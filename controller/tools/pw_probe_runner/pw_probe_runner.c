/*
 * pw_probe_runner.c — sandboxed C worker that owns the post-apply
 * syscall surface.
 *
 * Flow:
 *   1. Parse argv: --shm-fd <N> --ready-fd <N> --step-count <N>
 *                  [--policy-fd <N>] (defaults to stdin).
 *   2. mmap the host's pre-populated PW_SHM_REGION_BYTES region from
 *      --shm-fd. Verify ABI identity and prepared sentinel. Initialize the
 *      Mach timebase and every configured allowance in continuous ticks; a
 *      refusal publishes its failure and exits 12 before any policy byte.
 *   3. Read SBPL policy text from --policy-fd (or stdin) until EOF
 *      into a fixed static buffer. Native parameter creation and
 *      compilation follow. The pipe carries no framing, so
 *      the header's policy_bytes_expected (checked against the buffer
 *      capacity in step 2) is what tells a prefix cut at EOF apart from
 *      a complete shorter submission: the count read at EOF is
 *      published to the header, then a count that differs from the
 *      expectation is refused, then an embedded NUL is refused. Only a
 *      source equal in length to the submission reaches libsandbox.
 *   4. sandbox_compile_string(). On failure: write apply_rc and
 *      done sentinel after token erasure, then exit cleanly.
 *   5. Write one byte to --ready-fd. Pre-apply readiness signal.
 *   6. sandbox_apply(). Write apply_rc to header.
 *   7. Write applied sentinel (release ordering).
 *   8. For each populated slot: run the requested attempt. An exec
 *      attempt creates its pipes and spawn handles here, after apply,
 *      and releases them before its slot completes. Setup failures
 *      retain their own call boundary (see below). Exec
 *      children are bounded per step by the exec deadline and per plan
 *      by the exec attempt budget (see PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT).
 *      Slot output writes use regular stores; the slot's `completed`
 *      flag is written with release ordering so the host's acquire-load
 *      of completed pairs with all preceding writes.
 *   9. Erase accepted token storage and publish the done sentinel.
 *  10. _exit(0) without waiting for host permission. The host independently
 *      observes reap and retains its grace/termination fallback.
 *
 * PW-owned extension reporting uses preallocated storage after sandbox_apply;
 * private native libraries may allocate. The result region is the only
 * post-apply output channel; stdout/stderr writes may be denied by
 * a (deny default) policy and must not be relied on for results.
 */

#include <dlfcn.h>
#include <sys/resource.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <mach/mach.h>
#include <sandbox.h>
#include <servers/bootstrap.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#include "pw_probe_runner_abi.h"
#include "pw_worker_evidence.h"
#include "pw_profile_capture.h"
#include "pw_extension_channel.h"

#include "pw_worker_timing.h"

/* SPI symbols from libsandbox. The public sandbox.h does not declare
 * them; they live in /usr/lib/libsandbox.dylib (link via -lsandbox).
 * The C worker dynamically links these entry points; optional extension
 * entry points are resolved separately with dlsym before application.
 *
 * The second arg of sandbox_compile_string is an OPAQUE SandboxParams
 * pointer (from sandbox_create_params), NOT a string — passing a
 * string literal here segfaults inside libsandbox. The params object
 * is built pre-apply from the host-populated shm params region and
 * freed after compile.
 */
extern int sandbox_apply(void *profile);
extern void *sandbox_compile_string(const char *str, void *params, char **error);
extern void *sandbox_create_params(void);
extern int sandbox_set_param(void *params, const char *key, const char *value);
extern void sandbox_free_params(void *params);
/* sandbox_free_error is deprecated in modern SDKs. The libsandbox
 * implementation is a thin wrapper around free(); we call free()
 * directly to avoid the deprecation warning without changing
 * behaviour. The errbuf returned by sandbox_compile_string is
 * documented as plain-malloc'd. */

/* ---- argv parsing -------------------------------------------------------- */

typedef struct {
    int extension_fd;
    int shm_fd;
    int ready_fd;
    int policy_fd;
    uint32_t step_count;
    /* Post-apply hang gate (_test_overrides.worker_post_apply_hang_ms).
     * When > 0, the worker calls nanosleep(N ms) AFTER every slot's
     * `completed` flag is written but BEFORE the `done` sentinel
     * flips. Pushes the host past its sentinel deadline so the
     * runner_timeout outcome is reachable from a real test specimen.
     * Defaults to 0 (no hang). Safe to leave 0 in production. */
    long post_apply_hang_ms;
    /* Post-apply fatal-signal gate (_test_overrides.worker_post_apply_kill_signal).
     * Raises signal N after applied and completed slots, before done. This
     * establishes abnormal process disposition, never a kernel sandbox cause.
     * Defaults to 0 (no signal). */
    int post_apply_kill_signal;
    /* Pre-publication fatal-signal gate (_test_overrides.worker_kill_before_publish_slot).
     * When >= 0, run_attempt() raises SIGKILL on this process for that slot
     * index after the native attempt returned and its result fields were
     * written, but BEFORE the slot's `completed` flag is stored. The host then
     * holds the slot's started progress word and no published result: the
     * control for a native return without publication. Defaults to -1 (off). */
    long kill_before_publish_slot;
    /* Pre-ready hang gate (_test_overrides.worker_pre_ready_hang_ms).
     * When > 0, the worker calls nanosleep(N ms) BEFORE writing the
     * pre-apply ready byte. Delays after compilation and optional capture, before readiness. It
     * overruns the host's readyByteTimeout: the host closes the ready
     * pipe first, so the subsequent ready-byte write hits a closed read
     * end. With SIGPIPE ignored (see main) the worker survives that and
     * still reaches sandbox_apply; this seam lets a test pin that
     * survival. Defaults to 0 (no hang). Safe to leave 0 in production. */
    long pre_ready_hang_ms;
    /* Per-exec wall-clock budget. Test seam — production callers
     * leave this at 0 to use PW_EXEC_CHILD_DEADLINE_MS_DEFAULT. */
    long exec_child_deadline_ms;
    long proceed_wait_ms;
    /* Harness-only shortening of the exec attempt budget. 0 keeps the
     * production default; the flag can never extend the budget. */
    long exec_attempt_budget_ms;
} pw_args_t;

static void print_usage(FILE *to) {
    fprintf(to,
        "usage: pw-probe-runner --shm-fd <N> --ready-fd <N> --step-count <N>\n"
        "                       [--policy-fd <N>] [--post-apply-hang-ms <N>]\n"
        "\n"
        "  --shm-fd N             FD of the host's pw_shm_region mapping.\n"
        "  --ready-fd N           FD the worker writes one byte to just\n"
        "                         before sandbox_apply(). Pre-apply only;\n"
        "                         post-apply readiness is the `applied`\n"
        "                         sentinel in shm.\n"
        "  --step-count N         Number of populated slots, 0..%u.\n"
        "  --policy-fd N          Optional FD with the SBPL policy text.\n"
        "                         Defaults to stdin (FD 0).\n"
        "  --post-apply-hang-ms N Optional test-seam. Sleep N ms AFTER\n"
        "                         all slot results are durable but BEFORE\n"
        "                         flipping the `done` sentinel. Drives the\n"
        "                         host's runner_timeout outcome from a\n"
        "                         real specimen.\n"
        "  --post-apply-kill-signal N  Optional test-seam. Raise signal N on\n"
        "                         self AFTER slot results are durable but\n"
        "                         BEFORE flipping `done`, so the host sees\n"
        "                         applied=1/done=0 and a self-signal.\n"
        "  --pre-ready-hang-ms N  Optional test-seam. Sleep N ms BEFORE\n"
        "                         the ready byte, delaying after compilation\n"
        "                         that overruns the host's readyByteTimeout\n"
        "                         (the ready write then lands on a closed\n"
        "                         pipe; SIGPIPE is ignored).\n"
        "  --exec-child-deadline-ms N  Optional test-seam. Per-exec\n"
        "                         attempt wall-clock cap; default %ld ms.\n"
        "                         Helpers exceeding the deadline are\n"
        "                         SIGKILL'd (process group) and the slot\n"
        "                         reports the deadline in error.\n"
        "\n"
        "  --proceed-wait-ms N     Harness-only release deadline (1..60000 ms).\n"
        "  --exec-attempt-budget-ms N  Harness-only exec attempt budget\n"
        "                         (1..%ld ms). Exec children spawn only while\n"
        "                         the worker's local active time is\n"
        "                         below it; later exec steps are refused.\n"
        "  --version              Print ABI identity and exit.\n",
        PW_SHM_MAX_STEPS, PW_EXEC_CHILD_DEADLINE_MS_DEFAULT,
        PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT);
}

static int parse_int_arg(const char *value, long *out) {
    if (!value || !*value) return -1;
    errno = 0;
    char *end = NULL;
    long v = strtol(value, &end, 10);
    if (errno == ERANGE || !end || *end) return -1;
    *out = v;
    return 0;
}

static int parse_args(int argc, char **argv, pw_args_t *args) {
    args->extension_fd = -1;
    args->shm_fd                 = -1;
    args->ready_fd               = -1;
    args->policy_fd              = STDIN_FILENO;
    args->step_count             = 0;
    args->post_apply_hang_ms     = 0;
    args->post_apply_kill_signal = 0;
    args->kill_before_publish_slot = -1;
    args->pre_ready_hang_ms      = 0;
    args->exec_child_deadline_ms = 0;
    args->proceed_wait_ms = PW_PROCEED_WAIT_MS_DEFAULT;
    args->exec_attempt_budget_ms = 0;

    int i = 1;
    while (i < argc) {
        const char *flag = argv[i];
        if (strcmp(flag, "--shm-fd") == 0 || strcmp(flag, "--ready-fd") == 0 || strcmp(flag, "--extension-fd") == 0 ||
            strcmp(flag, "--step-count") == 0 || strcmp(flag, "--policy-fd") == 0 ||
            strcmp(flag, "--post-apply-hang-ms") == 0 ||
            strcmp(flag, "--post-apply-kill-signal") == 0 ||
            strcmp(flag, "--kill-before-publish-slot") == 0 ||
            strcmp(flag, "--pre-ready-hang-ms") == 0 ||
            strcmp(flag, "--exec-child-deadline-ms") == 0 ||
            strcmp(flag, "--exec-attempt-budget-ms") == 0 ||
            strcmp(flag, "--proceed-wait-ms") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "pw-probe-runner: %s requires a value\n", flag);
                return -1;
            }
            long v;
            if (parse_int_arg(argv[i + 1], &v) != 0) {
                fprintf(stderr, "pw-probe-runner: %s: invalid integer %s\n", flag, argv[i + 1]);
                return -1;
            }
            if (strcmp(flag, "--extension-fd") == 0) {
                if (v < 0 || v > INT_MAX) return -1;
                args->extension_fd = (int)v;
            } else if (strcmp(flag, "--shm-fd") == 0) {
                if (v < 0 || v > INT_MAX) {
                    fprintf(stderr, "pw-probe-runner: %s: fd out of range %ld\n", flag, v);
                    return -1;
                }
                args->shm_fd = (int)v;
            } else if (strcmp(flag, "--ready-fd") == 0) {
                if (v < 0 || v > INT_MAX) {
                    fprintf(stderr, "pw-probe-runner: %s: fd out of range %ld\n", flag, v);
                    return -1;
                }
                args->ready_fd = (int)v;
            } else if (strcmp(flag, "--policy-fd") == 0) {
                if (v < 0 || v > INT_MAX) {
                    fprintf(stderr, "pw-probe-runner: %s: fd out of range %ld\n", flag, v);
                    return -1;
                }
                args->policy_fd = (int)v;
            } else if (strcmp(flag, "--post-apply-hang-ms") == 0) {
                /* Cap at one minute. The host's runner_timeout deadline is
                 * its own setting; the hang just has to exceed it. A bogus
                 * multi-day value would burn CPU + clog the test process. */
                if (v < 0 || v > 60 * 1000) {
                    fprintf(stderr, "pw-probe-runner: --post-apply-hang-ms %ld out of range (0..60000)\n", v);
                    return -1;
                }
                args->post_apply_hang_ms = v;
            } else if (strcmp(flag, "--post-apply-kill-signal") == 0) {
                /* 0 disables; otherwise a signal number (1..31) the worker
                 * raises on itself post-apply / pre-done so the host's
                 * self-signal classification (runner_failed with the signal
                 * preserved) is reached deterministically. */
                if (v < 0 || v > 31) {
                    fprintf(stderr, "pw-probe-runner: --post-apply-kill-signal %ld out of range (0..31)\n", v);
                    return -1;
                }
                args->post_apply_kill_signal = (int)v;
            } else if (strcmp(flag, "--kill-before-publish-slot") == 0) {
                /* A slot index. The seam fires only when the loop reaches
                 * that slot; an index beyond the plan never fires. */
                if (v < 0 || v >= (long)PW_SHM_MAX_STEPS) {
                    fprintf(stderr, "pw-probe-runner: --kill-before-publish-slot %ld out of range (0..%u)\n",
                            v, PW_SHM_MAX_STEPS - 1u);
                    return -1;
                }
                args->kill_before_publish_slot = v;
            } else if (strcmp(flag, "--pre-ready-hang-ms") == 0) {
                /* Same one-minute cap as the post-apply hang: the seam
                 * only has to exceed the host's readyByteTimeout. */
                if (v < 0 || v > 60 * 1000) {
                    fprintf(stderr, "pw-probe-runner: --pre-ready-hang-ms %ld out of range (0..60000)\n", v);
                    return -1;
                }
                args->pre_ready_hang_ms = v;
            } else if (strcmp(flag, "--proceed-wait-ms") == 0) {
                if (v <= 0 || v > 60000) {
                    fprintf(stderr, "pw-probe-runner: --proceed-wait-ms %ld out of range (1..60000)\n", v);
                    return -1;
                }
                args->proceed_wait_ms = v;
            } else if (strcmp(flag, "--exec-child-deadline-ms") == 0) {
                if (v <= 0 || v > PW_EXEC_CHILD_DEADLINE_MS_MAX) {
                    fprintf(stderr,
                            "pw-probe-runner: --exec-child-deadline-ms %ld out of range (1..%ld)\n",
                            v, PW_EXEC_CHILD_DEADLINE_MS_MAX);
                    return -1;
                }
                args->exec_child_deadline_ms = v;
            } else if (strcmp(flag, "--exec-attempt-budget-ms") == 0) {
                /* Shorten only: a harness proves the budget with seconds of
                 * helpers, never by granting more than production allows. */
                if (v <= 0 || v > PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT) {
                    fprintf(stderr,
                            "pw-probe-runner: --exec-attempt-budget-ms %ld out of range (1..%ld)\n",
                            v, PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT);
                    return -1;
                }
                args->exec_attempt_budget_ms = v;
            } else {
                if (v < 0 || (unsigned long)v > (unsigned long)PW_SHM_MAX_STEPS) {
                    fprintf(stderr, "pw-probe-runner: --step-count %ld out of range\n", v);
                    return -1;
                }
                args->step_count = (uint32_t)v;
            }
            i += 2;
        } else {
            fprintf(stderr, "pw-probe-runner: unknown argument %s\n", flag);
            return -1;
        }
    }

    if (args->shm_fd < 0) {
        fprintf(stderr, "pw-probe-runner: --shm-fd is required\n");
        return -1;
    }
    if (args->ready_fd < 0) {
        fprintf(stderr, "pw-probe-runner: --ready-fd is required\n");
        return -1;
    }
    return 0;
}

/* ---- shm + policy + sandbox --------------------------------------------- */

/* mmap the host's region. The caller checks the fixed bootstrap identity
 * before accessing layout-dependent fields or the prepared sentinel.
 * Returns the base pointer on success, NULL on failure (caller logs +
 * exits; no further shm communication is possible). */
static void *map_region(int shm_fd) {
    struct stat st;
    if (fstat(shm_fd, &st) != 0) {
        fprintf(stderr, "pw-probe-runner: fstat(shm_fd=%d): %s\n", shm_fd, strerror(errno));
        return NULL;
    }
    if ((size_t)st.st_size < PW_SHM_REGION_BYTES) {
        fprintf(stderr,
                "pw-probe-runner: shm_fd region too small: got %lld bytes, need %zu\n",
                (long long)st.st_size, (size_t)PW_SHM_REGION_BYTES);
        return NULL;
    }
    void *base = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE,
                      MAP_SHARED, shm_fd, 0);
    if (base == MAP_FAILED) {
        fprintf(stderr, "pw-probe-runner: mmap: %s\n", strerror(errno));
        return NULL;
    }
    return base;
}

/* Read up to max_len-1 bytes from fd into buf, NUL-terminating.
 * Returns the number of bytes read on success, -1 on read error, and
 * -2 if the input exceeds the fixed buffer. */
static ssize_t read_all_from_fd(int fd, char *buf, size_t max_len) {
    if (max_len == 0) return -1;
    size_t total = 0;
    while (total < max_len - 1) {
        ssize_t n = read(fd, buf + total, (max_len - 1) - total);
        if (n < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        if (n == 0) break;
        total += (size_t)n;
    }
    buf[total] = '\0';
    if (total == max_len - 1) {
        char extra;
        for (;;) {
            ssize_t n = read(fd, &extra, 1);
            if (n < 0 && errno == EINTR) continue;
            if (n < 0) return -1;
            if (n > 0) return -2;
            break;
        }
    }
    return (ssize_t)total;
}

/* Write one byte to the ready FD. Restart on EINTR. Returns 0 on
 * success, -1 on persistent failure. */
static int write_ready_byte(int fd) {
    static const uint8_t byte = 1;
    for (;;) {
        ssize_t n = write(fd, &byte, 1);
        if (n == 1) return 0;
        if (n < 0 && errno == EINTR) continue;
        return -1;
    }
}

/* ---- attempt implementations -------------------------------------------- */

/*
 * Attempts acquire their own resources after apply, including exec pipes
 * and native spawn-handle storage. Diagnostic and other native-library
 * internals are not constrained to stack storage. Outputs reach slot fields
 * before run_attempt() releases the slot's `completed` flag.
 *
 * observed_path uses fcntl(F_GETPATH) on the file FD while it is
 * still open — this is the kernel's authoritative answer to "what
 * path did this open() actually resolve to", and survives the
 * common difference between requested vs realpath form. Populated
 * for file attempts only; mach_lookup leaves it empty.
 */

/* Helper: set rc/errno/error from a failed POSIX call. */
static void fail_from_errno(pw_shm_slot_t *slot, const char *what) {
    int saved = errno;
    slot->rc = 1;
    slot->errno_val = saved;
    snprintf(slot->error, sizeof(slot->error), "%s: %s", what, strerror(saved));
}

/* Helper: capture observed_path from a still-open FD. Leaves the
 * field empty on failure rather than reporting it as a slot error —
 * the diagnostic is best-effort. */
static void capture_observed_path(int fd, pw_shm_slot_t *slot) {
    char buf[PW_SHM_OBSERVED_PATH_MAX];
    if (fcntl(fd, F_GETPATH, buf) == 0) {
        size_t n = strnlen(buf, sizeof(buf));
        if (n >= sizeof(slot->observed_path)) n = sizeof(slot->observed_path) - 1;
        memcpy(slot->observed_path, buf, n);
        slot->observed_path[n] = '\0';
    }
}

static void attempt_file_open_read(pw_shm_slot_t *slot) {
    int fd = open(slot->target, O_RDONLY);
    if (fd < 0) {
        fail_from_errno(slot, "open(O_RDONLY)");
        return;
    }
    capture_observed_path(fd, slot);
    /* Touch one byte so the kernel observes the read, then close. */
    char b;
    (void)read(fd, &b, 1);
    close(fd);
    slot->rc = 0;
    slot->errno_val = 0;
}

static void attempt_file_open_write(pw_shm_slot_t *slot) {
    int fd = open(slot->target, O_WRONLY | O_TRUNC);
    if (fd < 0) {
        fail_from_errno(slot, "open(O_WRONLY|O_TRUNC)");
        return;
    }
    capture_observed_path(fd, slot);
    char b = 'x';
    (void)write(fd, &b, 1);
    close(fd);
    slot->rc = 0;
    slot->errno_val = 0;
}

static void attempt_file_create(pw_shm_slot_t *slot) {
    /* O_WRONLY | O_CREAT without O_EXCL,
     * mode 0600. A pre-existing file is opened for write but not
     * truncated; semantics callers depend on. */
    int fd = open(slot->target, O_WRONLY | O_CREAT, 0600);
    if (fd < 0) {
        fail_from_errno(slot, "open(O_WRONLY|O_CREAT)");
        return;
    }
    capture_observed_path(fd, slot);
    close(fd);
    slot->rc = 0;
    slot->errno_val = 0;
}

static void attempt_file_unlink(pw_shm_slot_t *slot) {
    if (unlink(slot->target) != 0) {
        fail_from_errno(slot, "unlink");
        return;
    }
    slot->rc = 0;
    slot->errno_val = 0;
}

static void attempt_file_access(pw_shm_slot_t *slot) {
    /* R_OK requests an access check; it does not open or read the target. */
    if (access(slot->target, R_OK) != 0) {
        fail_from_errno(slot, "access(R_OK)");
        return;
    }
    slot->rc = 0;
    slot->errno_val = 0;
}

static void attempt_mach_lookup(pw_shm_slot_t *slot) {
    mach_port_t bootstrap = MACH_PORT_NULL;
    kern_return_t kr = task_get_special_port(mach_task_self(),
                                             TASK_BOOTSTRAP_PORT,
                                             &bootstrap);
    if (kr != KERN_SUCCESS) {
        slot->rc = 1;
        slot->errno_val = 0;
        snprintf(slot->error, sizeof(slot->error),
                 "task_get_special_port: kr=%d", kr);
        return;
    }
    mach_port_t svc = MACH_PORT_NULL;
    kr = bootstrap_look_up(bootstrap, slot->target, &svc);
    if (kr != KERN_SUCCESS) {
        slot->rc = 1;
        slot->errno_val = 0;
        snprintf(slot->error, sizeof(slot->error),
                 "bootstrap_look_up: kr=%d", kr);
        return;
    }
    mach_port_deallocate(mach_task_self(), svc);
    slot->rc = 0;
    slot->errno_val = 0;
}

/* One bounded value read; value bytes and post-call length are discarded. */
#define PW_SYSCTL_READ_BYTES 4096

static void attempt_sysctl_read(pw_shm_slot_t *slot) {
    char buf[PW_SYSCTL_READ_BYTES];
    size_t len = sizeof(buf);
    if (sysctlbyname(slot->target, buf, &len, NULL, 0) != 0) {
        fail_from_errno(slot, "sysctlbyname");
        return;
    }
    slot->rc = 0;
    slot->errno_val = 0;
}

#include "pw_worker_exec.h"

/* Native extension entry points are resolved before application; none is called
 * to warm it up. PW owns fixed storage; private-library allocation is unspecified. */
typedef int64_t (*pw_consume_fn)(const char *);
typedef int (*pw_release_fn)(int64_t);
static pw_consume_fn extension_consume;
static pw_release_fn extension_release;
static pw_extension_channel_t *extension_channel;
static int64_t extension_handle = -1;
static int consume_decided, release_decided;

/* Ordinary cleanup erases the whole accepted channel, including unused bytes.
 * This neither consumes nor releases native extension authority. */
static void erase_accepted_token(void) {
    if (extension_channel) pw_extension_erase(extension_channel->token, PW_EXTENSION_TOKEN_BYTES);
}

/* Test-only observation at the actual release-store boundary. Production has
 * no callback or request knob; the observer cannot run before publication. */
#ifndef PW_TERMINAL_PUBLISHED
#define PW_TERMINAL_PUBLISHED(hdr) ((void)0)
#endif

static _Noreturn void publish_done_and_exit(pw_shm_header_t *hdr) {
    erase_accepted_token();
    atomic_store_explicit(&hdr->done, 1u, memory_order_release);
    PW_TERMINAL_PUBLISHED(hdr);
    _exit(0);
}

/* Compile-time observation seam for controlled interruption tests. The shipped
 * worker has no callback or request knob. 1 is after the pre-call publication;
 * 2 is after native return and before any result payload/publication. */
#ifndef PW_EXTENSION_OBSERVE
#define PW_EXTENSION_OBSERVE(stage, release, result) ((void)0)
#endif

/* Delivery status codes the worker publishes in hdr->extension_delivery_status.
 * The host maps them to delivery_status strings; see PWExtensionDelivery. */
enum {
    PW_DELIVERY_DELIVERED = 1,          /* channel accepted; delivered_bytes is the token length */
    PW_DELIVERY_TOKEN_UNAVAILABLE = 2,  /* no token descriptor was supplied */
    PW_DELIVERY_CHANNEL_REJECTED = 3,   /* the channel was inspected and its contents or size rejected */
    PW_DELIVERY_API_UNAVAILABLE = 4,    /* consume or release symbol unavailable */
    PW_DELIVERY_LOCAL_SETUP_FAILED = 5  /* a local native call before validation failed */
};
/* Preparation stages. The first failing stage names the status; a cleanup
 * failure after it is published separately and never changes the status. */
enum {
    PW_DELIVERY_STAGE_NONE = 0,
    PW_DELIVERY_STAGE_CORE_LIMIT = 1,          /* setrlimit(RLIMIT_CORE) */
    PW_DELIVERY_STAGE_DESCRIPTOR_METADATA = 2, /* fstat(fd) */
    PW_DELIVERY_STAGE_CHANNEL_SIZE = 3,        /* fstat succeeded; st_size below the channel size */
    PW_DELIVERY_STAGE_MAPPING = 4,             /* mmap */
    PW_DELIVERY_STAGE_DESCRIPTOR_CLOSE = 5,    /* close(fd) */
    PW_DELIVERY_STAGE_CHANNEL_HEADER = 6,      /* magic, completed or status */
    PW_DELIVERY_STAGE_CHANNEL_TOKEN = 7,       /* token length or bytes */
    PW_DELIVERY_STAGE_UNMAP = 8                /* munmap during cleanup */
};

/* Compile-time native-call seams for controlled local failures. Production
 * compiles each to the real call; the shipped worker has no request knob. */
#ifndef PW_EXTENSION_SETRLIMIT
#define PW_EXTENSION_SETRLIMIT(resource, limit) setrlimit((resource), (limit))
#endif
#ifndef PW_EXTENSION_FSTAT
#define PW_EXTENSION_FSTAT(fd, metadata) fstat((fd), (metadata))
#endif
#ifndef PW_EXTENSION_MMAP
#define PW_EXTENSION_MMAP(length, fd) mmap(NULL, (length), PROT_READ | PROT_WRITE, MAP_SHARED, (fd), 0)
#endif
#ifndef PW_EXTENSION_CLOSE
#define PW_EXTENSION_CLOSE(fd) close(fd)
#endif

static void prepare_extension(pw_shm_header_t *hdr, int fd) {
    if (!hdr->extension_requested) { if (fd >= 0) close(fd); return; }
    uint32_t status = PW_DELIVERY_TOKEN_UNAVAILABLE, stage = PW_DELIVERY_STAGE_NONE, cleanup_stage = PW_DELIVERY_STAGE_NONE;
    int32_t native_rc = 0, saved_errno = 0, cleanup_errno = 0;
    int rc;
    /* The descriptor is closed exactly once: either as the inspected call
     * (after mapping) or as cleanup after an earlier failure. */
    int fd_open = fd >= 0;
#define PW_DELIVERY_CLEANUP_CLOSE() do { \
        if (fd_open) { errno = 0; if (PW_EXTENSION_CLOSE(fd)) { cleanup_stage = PW_DELIVERY_STAGE_DESCRIPTOR_CLOSE; cleanup_errno = errno; } fd_open = 0; } \
    } while (0)
    /* Resolve the native entry points first, so a later local failure leaves
     * the API question answered and the actions unavailable for want of a
     * delivered token, not for an API absence that was never observed. */
    extension_consume = (pw_consume_fn)dlsym(RTLD_DEFAULT, "sandbox_extension_consume");
    extension_release = (pw_release_fn)dlsym(RTLD_DEFAULT, "sandbox_extension_release");
    if (!extension_consume || !extension_release) {
        status = PW_DELIVERY_API_UNAVAILABLE; PW_DELIVERY_CLEANUP_CLOSE(); goto publish;
    }
    /* Core dumps are disabled before any token byte can be mapped. */
    struct rlimit core = {0, 0};
    errno = 0;
    rc = PW_EXTENSION_SETRLIMIT(RLIMIT_CORE, &core);
    if (rc) {
        status = PW_DELIVERY_LOCAL_SETUP_FAILED; stage = PW_DELIVERY_STAGE_CORE_LIMIT; native_rc = rc; saved_errno = errno;
        PW_DELIVERY_CLEANUP_CLOSE(); goto publish;
    }
    if (fd_open) {
        struct stat metadata;
        errno = 0;
        rc = PW_EXTENSION_FSTAT(fd, &metadata);
        if (rc) {
            status = PW_DELIVERY_LOCAL_SETUP_FAILED; stage = PW_DELIVERY_STAGE_DESCRIPTOR_METADATA; native_rc = rc; saved_errno = errno;
            PW_DELIVERY_CLEANUP_CLOSE(); goto publish;
        }
        if (metadata.st_size < (off_t)PW_EXTENSION_CHANNEL_BYTES) {
            /* The inspection call succeeded; the object is too small to be the channel. */
            status = PW_DELIVERY_CHANNEL_REJECTED; stage = PW_DELIVERY_STAGE_CHANNEL_SIZE; native_rc = rc;
            PW_DELIVERY_CLEANUP_CLOSE(); goto publish;
        }
        errno = 0;
        void *p = PW_EXTENSION_MMAP(PW_EXTENSION_CHANNEL_BYTES, fd);
        int map_errno = errno;
        errno = 0;
        int closed = PW_EXTENSION_CLOSE(fd);
        int close_errno = errno;
        fd_open = 0;
        if (p == MAP_FAILED) {
            status = PW_DELIVERY_LOCAL_SETUP_FAILED; stage = PW_DELIVERY_STAGE_MAPPING; native_rc = -1; saved_errno = map_errno;
            if (closed) { cleanup_stage = PW_DELIVERY_STAGE_DESCRIPTOR_CLOSE; cleanup_errno = close_errno; }
            goto publish;
        }
        extension_channel = p;
        if (closed) {
            status = PW_DELIVERY_LOCAL_SETUP_FAILED; stage = PW_DELIVERY_STAGE_DESCRIPTOR_CLOSE; native_rc = closed; saved_errno = close_errno;
            goto reject_mapping;
        }
        uint32_t published = atomic_load_explicit(&extension_channel->completed, memory_order_acquire);
        if (extension_channel->magic != PW_EXTENSION_MAGIC || published != 1 || extension_channel->status != 1) {
            status = PW_DELIVERY_CHANNEL_REJECTED; stage = PW_DELIVERY_STAGE_CHANNEL_HEADER; goto reject_mapping;
        }
        uint32_t n = extension_channel->token_length;
        if (n == 0 || n >= PW_EXTENSION_TOKEN_BYTES || extension_channel->token[n] != 0 ||
            memchr(extension_channel->token, 0, n) != NULL) {
            status = PW_DELIVERY_CHANNEL_REJECTED; stage = PW_DELIVERY_STAGE_CHANNEL_TOKEN; goto reject_mapping;
        }
        hdr->extension_delivered_bytes = n;
        status = PW_DELIVERY_DELIVERED;
        goto publish;
    reject_mapping:
        pw_extension_erase(extension_channel->token, PW_EXTENSION_TOKEN_BYTES);
        errno = 0;
        if (munmap(extension_channel, PW_EXTENSION_CHANNEL_BYTES)) { cleanup_stage = PW_DELIVERY_STAGE_UNMAP; cleanup_errno = errno; }
        extension_channel = NULL;
    }
publish:
#undef PW_DELIVERY_CLEANUP_CLOSE
    hdr->extension_delivery_status = status;
    hdr->extension_delivery_stage = stage;
    hdr->extension_delivery_native_rc = native_rc;
    hdr->extension_delivery_errno = saved_errno;
    hdr->extension_delivery_cleanup_stage = cleanup_stage;
    hdr->extension_delivery_cleanup_errno = cleanup_errno;
    atomic_store_explicit(&hdr->extension_delivery_published, 1, memory_order_release);
}

static void attempt_extension(pw_shm_slot_t *slot, int release) {
    if ((release && release_decided) || (!release && consume_decided)) {
        slot->unavailable_code = 4; return;
    }
    if (release) release_decided = 1; else consume_decided = 1;
    if (!extension_consume || !extension_release) slot->unavailable_code = 3;
    else if (release && extension_handle == -1) slot->unavailable_code = 2;
    else if (!release && !extension_channel) slot->unavailable_code = 1;
    else {
        atomic_store_explicit(&slot->call_boundary, 1, memory_order_release);
        PW_EXTENSION_OBSERVE(1, release, 0);
        errno = 0;
        int64_t result = release ? (int64_t)extension_release(extension_handle)
                                 : extension_consume(extension_channel->token);
        int saved = errno;
        PW_EXTENSION_OBSERVE(2, release, result);
        slot->native_result = result;
        slot->native_errno = saved;
        slot->native_result_valid = 1;
        if (!release && result != -1) extension_handle = result;
    }
    if (!release) erase_accepted_token();
}

/* A single bounded read on a fresh descriptor, with its own identity and close
 * observations. This does not change open_read's historical open-only meaning. */
static void attempt_file_read_fresh(pw_shm_slot_t *slot) {
    slot->access_read_rc = -2; slot->access_stat_rc = -2; slot->access_close_rc = -2;
    errno = 0;
    int fd = open(slot->target, O_RDONLY | O_CLOEXEC);
    slot->access_open_rc = fd;
    slot->access_open_errno = fd < 0 ? errno : 0;
    if (fd < 0) { slot->rc = -1; slot->errno_val = slot->access_open_errno; return; }
    struct stat metadata;
    errno = 0;
    int stat_rc = fstat(fd, &metadata);
    slot->access_stat_rc = stat_rc;
    slot->access_stat_errno = stat_rc ? errno : 0;
    if (!stat_rc) {
        slot->access_device = (uint32_t)metadata.st_dev; slot->access_inode = metadata.st_ino;
        slot->access_mode = metadata.st_mode; slot->access_uid = metadata.st_uid; slot->access_gid = metadata.st_gid;
    }
    errno = 0;
    ssize_t n = read(fd, slot->access_bytes, PW_SHM_FRESH_READ_BYTES);
    slot->access_read_rc = n; slot->access_read_errno = n < 0 ? errno : 0;
    errno = 0;
    int close_rc = close(fd);
    slot->access_close_rc = close_rc; slot->access_close_errno = close_rc ? errno : 0;
    if (stat_rc || n < 0 || close_rc) {
        slot->rc = -1;
        slot->errno_val = stat_rc ? slot->access_stat_errno : n < 0 ? slot->access_read_errno : slot->access_close_errno;
    }
}

static void record_file_stat(pw_file_stat_t *out, int result, int saved_errno, const struct stat *metadata) {
    out->rc = result; out->errno_val = result ? saved_errno : 0;
    if (!result) {
        out->device = (uint32_t)metadata->st_dev; out->inode = metadata->st_ino;
        out->mode = metadata->st_mode; out->uid = metadata->st_uid; out->gid = metadata->st_gid;
        out->size = metadata->st_size;
    }
}
static void fresh_write_stat(int fd, pw_file_stat_t *out) {
    struct stat metadata;
    errno = 0;
    int result = fstat(fd, &metadata), saved_errno = errno;
    record_file_stat(out, result, saved_errno, &metadata);
}
static void fresh_write_failure(pw_shm_slot_t *slot, int failed, int saved_errno) {
    if (failed && slot->rc == 0) { slot->rc = -1; slot->errno_val = saved_errno; }
}
/* Distinct actions preserve the legacy open_write/create meanings. No target
 * descriptor is acquired before application or retained after this attempt.
 * A short transfer is a failed attempt with no fabricated native errno. */
static void attempt_file_write_fresh(pw_shm_slot_t *slot, int create) {
    pw_fresh_write_t *out = &slot->fresh_write;
    out->open_rc = out->truncate_rc = out->close_rc = -2; out->write_rc = -2;
    out->preopen_stat.rc = out->opened_stat.rc = out->truncated_stat.rc = out->written_stat.rc = -2;
    if (create) {
        struct stat metadata;
        errno = 0;
        int result = lstat(slot->target, &metadata), saved_errno = errno;
        record_file_stat(&out->preopen_stat, result, saved_errno, &metadata);
    }
    errno = 0;
    int fd = open(slot->target, O_WRONLY | O_CLOEXEC | (create ? O_CREAT | O_EXCL : 0), 0600);
    out->open_rc = fd; out->open_errno = fd < 0 ? errno : 0;
    if (fd < 0) { slot->rc = -1; slot->errno_val = out->open_errno; return; }
    fresh_write_stat(fd, &out->opened_stat);
    fresh_write_failure(slot, out->opened_stat.rc != 0, out->opened_stat.errno_val);
    if (!create) {
        errno = 0;
        out->truncate_rc = ftruncate(fd, 0); out->truncate_errno = out->truncate_rc ? errno : 0;
        fresh_write_failure(slot, out->truncate_rc != 0, out->truncate_errno);
        fresh_write_stat(fd, &out->truncated_stat);
        fresh_write_failure(slot, out->truncated_stat.rc != 0, out->truncated_stat.errno_val);
    }
    if (create || out->truncate_rc == 0) {
        const char byte = 'x';
        errno = 0;
        out->write_rc = write(fd, &byte, 1); out->write_errno = out->write_rc < 0 ? errno : 0;
        fresh_write_failure(slot, out->write_rc != 1, out->write_errno);
        fresh_write_stat(fd, &out->written_stat);
        fresh_write_failure(slot, out->written_stat.rc != 0, out->written_stat.errno_val);
    }
    errno = 0;
    out->close_rc = close(fd); out->close_errno = out->close_rc ? errno : 0;
    fresh_write_failure(slot, out->close_rc != 0, out->close_errno);
}

/* Dispatch on attempt_kind. Initializes slot outputs to "ok defaults"
 * before the per-kind helper runs so a kind that leaves a field
 * untouched lands at a known state. `completed` is the LAST write
 * (release ordering) so the host's acquire-load of completed
 * synchronizes with every other slot write. */
static void run_attempt(pw_shm_slot_t *slot, pw_timing_t *timing, uint32_t phase, uint32_t index,
                        int kill_before_publish) {
    slot->rc = 0;
    slot->errno_val = 0;
    slot->observed_path[0] = '\0';
    slot->error[0] = '\0';

    switch (slot->attempt_kind) {
    case PW_ATTEMPT_NONE:                                                 break;
    case PW_ATTEMPT_EXTENSION_CONSUME: attempt_extension(slot, 0); break;
    case PW_ATTEMPT_EXTENSION_RELEASE: attempt_extension(slot, 1); break;
    case PW_ATTEMPT_FILE_READ_FRESH: attempt_file_read_fresh(slot); break;
    case PW_ATTEMPT_FILE_WRITE_FRESH: attempt_file_write_fresh(slot, 0); break;
    case PW_ATTEMPT_FILE_CREATE_FRESH: attempt_file_write_fresh(slot, 1); break;
    case PW_ATTEMPT_FILE_OPEN_READ:   attempt_file_open_read(slot);       break;
    case PW_ATTEMPT_FILE_OPEN_WRITE:  attempt_file_open_write(slot);      break;
    case PW_ATTEMPT_FILE_CREATE:      attempt_file_create(slot);          break;
    case PW_ATTEMPT_FILE_UNLINK:      attempt_file_unlink(slot);          break;
    case PW_ATTEMPT_FILE_ACCESS:      attempt_file_access(slot);          break;
    case PW_ATTEMPT_MACH_LOOKUP:      attempt_mach_lookup(slot);          break;
    case PW_ATTEMPT_SYSCTL_READ:      attempt_sysctl_read(slot);          break;
    case PW_ATTEMPT_EXEC_SPAWN:
        attempt_exec_spawn(slot, timing, phase, index);
        break;
    default:
        slot->rc = -1;
        slot->errno_val = ENOSYS;
        snprintf(slot->error, sizeof(slot->error),
                 "unsupported attempt_kind=%u", slot->attempt_kind);
        break;
    }

    /* Test seam: die after the native return, before publication. The result
     * fields above are written but never released, so the host must withhold
     * them. SIGKILL cannot be caught; a return from kill() means delivery
     * failed, and the slot then publishes normally. */
    if (kill_before_publish) kill(getpid(), SIGKILL);

    atomic_store_explicit(&slot->completed, 1u, memory_order_release);
}

/* ---- phase release wait ------------------------------------------------- */

static inline void cpu_relax(void) {
    __asm__ volatile("yield" ::: "memory");
}

/* Test-only gates around the sampled decision; the shipped worker compiles
 * them away and no request can enable them. */
#ifndef PW_PROCEED_DECIDED
#define PW_PROCEED_DECIDED(phase) ((void)0)
#endif
#ifndef PW_PROCEED_CANCEL_LOADED
#define PW_PROCEED_CANCEL_LOADED(phase) ((void)0)
#endif

static _Noreturn void proceed_refused(pw_shm_header_t *hdr, pw_shm_evidence_t *e, uint32_t phase_index,
                                      uint32_t reason, const char *diagnostic) {
    pw_failure(e, PW_OP_PROCEED, PW_FAILURE_TIME_INVALID, PW_NATIVE_NONE, 0, 0, 0, phase_index, reason);
    pw_diagnostic(e, diagnostic);
    publish_done_and_exit(hdr);
}

/* No allocation, sleep or I/O after apply. Expiry is decided by sampled
 * continuous time: an unusable sample, an expired sample, a future release
 * and cancellation each end the phase before any acknowledgement, even with
 * release already visible. A late host release cannot revive a refusal. The
 * phase's wait is excluded from the exec plan once, at acknowledgement. */
static void wait_for_proceed(pw_shm_header_t *hdr, pw_shm_evidence_t *e,
                             uint32_t phase_index, pw_timing_t *timing) {
    pw_shm_phase_t *phase = &hdr->phases[phase_index];
    pw_progress(e, PW_OP_PROCEED, PW_PROGRESS_STARTED, phase->first_slot);
    atomic_store_explicit(&phase->arrived, 1u, memory_order_release);
    if (timing->clock.fault.reason) {
        /* An earlier exec rejected a sample: refuse without another read. */
        char text[PW_SHM_ERROR_MAX];
        pw_text_t out = {text, 0, sizeof(text)};
        pw_text_add(&out, "proceed refused: worker clock already invalid; first rejected sample: ");
        pw_text_add_fault(&out, &timing->clock.fault);
        proceed_refused(hdr, e, phase_index, PW_TIME_REASON_PRIOR_CLOCK_FAULT, text);
    }
    uint64_t start = 0, now = 0, extended = 0;
    if (pw_clock_sample(&timing->clock, PW_CLOCK_PROCEED_START, phase_index, PW_CLOCK_NO_SCOPE, &start))
        proceed_refused(hdr, e, phase_index, PW_TIME_REASON_BACKWARDS_COUNTER,
                        "proceed wait: worker clock went backwards at proceed start (reason in detail)");
    for (;;) {
        if (pw_clock_sample(&timing->clock, PW_CLOCK_PROCEED_OBSERVE, phase_index, PW_CLOCK_NO_SCOPE, &now))
            proceed_refused(hdr, e, phase_index, PW_TIME_REASON_BACKWARDS_COUNTER,
                            "proceed wait: worker clock went backwards while observing release (reason in detail)");
        uint64_t waited = now - start;
        if (waited >= timing->proceed_ticks) {
            pw_failure(e, PW_OP_PROCEED, PW_FAILURE_PROCEED_TIMEOUT, PW_NATIVE_NONE,
                       0, 0, 0, phase_index, (uint32_t)timing->proceed_ms);
            pw_diagnostic(e, "proceed wait: worker_proceed_wait budget expired (milliseconds in detail)");
            break;
        }
        if (pw_ticks_add(timing->plan_deadline, waited, &extended))
            proceed_refused(hdr, e, phase_index, PW_TIME_REASON_DEADLINE_OVERFLOW,
                            "proceed wait: exec plan deadline cannot exclude this wait (reason in detail)");
        PW_PROCEED_DECIDED(phase_index);
        uint32_t ordinal = atomic_load_explicit(&hdr->proceed, memory_order_acquire);
        if (ordinal > phase_index + 1u) {
            pw_failure(e, PW_OP_PROCEED, PW_FAILURE_PHASE_RELEASE, PW_NATIVE_NONE,
                       0, 0, 0, phase_index, ordinal);
            pw_diagnostic(e, "release names a future phase");
            break;
        }
        uint32_t cancelled = atomic_load_explicit(&hdr->exit_requested, memory_order_acquire);
        PW_PROCEED_CANCEL_LOADED(phase_index);
        if (cancelled != 0u) { erase_accepted_token(); _exit(0); }
        if (ordinal == phase_index + 1u) {
            timing->plan_deadline = extended;
            atomic_store_explicit(&phase->acknowledged, 1u, memory_order_release);
            atomic_store_explicit(&hdr->proceed_observed, ordinal, memory_order_release);
            pw_progress(e, PW_OP_PROCEED, PW_PROGRESS_RETURNED, phase->first_slot);
            return;
        }
        for (uint32_t i = 0; i < 1000u; i++) cpu_relax();
    }
    publish_done_and_exit(hdr);
}

/* ---- main ---------------------------------------------------------------- */

int main(int argc, char **argv) {
    /* Ignore SIGPIPE so a closed host pipe can produce EPIPE instead of
     * terminating the worker before shared-memory publication. In particular,
     * write_ready_byte records its return and lets application proceed when
     * the host has closed --ready-fd. A fatal signal is a termination
     * observation, not proof of sandbox denial. Return handling is local to
     * each call; open_write discards its one-byte write result. */
    signal(SIGPIPE, SIG_IGN);

    if (argc >= 2 && strcmp(argv[1], "--version") == 0) {
        printf("pw-probe-runner abi_identity=%s region_bytes=%zu max_steps=%u slot_bytes=%u\n",
               PW_WORKER_ABI_IDENTITY_HEX,
               (size_t)PW_SHM_REGION_BYTES,
               PW_SHM_MAX_STEPS,
               PW_SHM_SLOT_BYTES);
        return 0;
    }

    pw_args_t args;
    if (parse_args(argc, argv, &args) != 0) {
        print_usage(stderr);
        return 2;
    }

    /* The worker origin: setup after this sample is charged to the exec budget. */
    pw_timing_t timing = {
        .proceed_ms = args.proceed_wait_ms,
        .budget_ms = args.exec_attempt_budget_ms > 0 ? args.exec_attempt_budget_ms : PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT,
        .child_ms = args.exec_child_deadline_ms > 0 ? args.exec_child_deadline_ms : PW_EXEC_CHILD_DEADLINE_MS_DEFAULT,
    };
    pw_clock_start(&timing.clock);

    void *base = map_region(args.shm_fd);
    if (!base) return 3;

    pw_shm_header_t *hdr = (pw_shm_header_t *)base;
    if (hdr->abi_magic != PW_SHM_ABI_MAGIC ||
        memcmp(hdr->abi_identity, PW_WORKER_ABI_IDENTITY, PW_SHM_ABI_IDENTITY_BYTES) != 0) {
        fprintf(stderr,
                "pw-probe-runner: ABI identity mismatch (worker %s); refusing shared interface\n",
                PW_WORKER_ABI_IDENTITY_HEX);
        return 4;
    }
    pw_shm_slot_t   *slots = (pw_shm_slot_t *)((char *)base + PW_SHM_HEADER_BYTES);
    pw_shm_param_t  *params = (pw_shm_param_t *)((char *)slots
                              + ((size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES));
    pw_shm_evidence_t *evidence = pw_evidence(base);
    pw_progress(evidence, PW_OP_HEADER, PW_PROGRESS_STARTED, UINT32_MAX);
    if (atomic_load_explicit(&hdr->prepared, memory_order_acquire) != 1u) {
        fprintf(stderr,
                "pw-probe-runner: host did not set prepared=1; refusing to proceed\n");
        pw_failure(evidence, PW_OP_HEADER, PW_FAILURE_UNPREPARED, PW_NATIVE_NONE, 0, 0, 0, UINT32_MAX, 0);
        pw_diagnostic(evidence, "host did not set prepared=1");
        return 5;
    }

    /* Honour the host's step_count over argv. argv is advisory; the
     * shm is the source of truth so a host that wrote step_count=N
     * cannot have a worker overrun by being passed --step-count=M>N
     * on the command line. */
    if (hdr->step_count > PW_SHM_MAX_STEPS) {
        fprintf(stderr,
                "pw-probe-runner: header step_count=%u exceeds PW_SHM_MAX_STEPS=%u\n",
                hdr->step_count, PW_SHM_MAX_STEPS);
        pw_failure(evidence, PW_OP_HEADER, PW_FAILURE_STEP_LIMIT, PW_NATIVE_NONE, 0, 0, 0, UINT32_MAX, PW_SHM_MAX_STEPS);
        pw_diagnostic(evidence, "step count exceeds shared-memory capacity");
        return 6;
    }
    if (args.step_count != 0 && args.step_count != hdr->step_count) {
        fprintf(stderr,
                "pw-probe-runner: argv --step-count=%u disagrees with header=%u; using header\n",
                args.step_count, hdr->step_count);
    }
    uint32_t step_count = hdr->step_count;
    uint32_t end_slot = 0;
    int phases_valid = hdr->phase_count > 0 && hdr->phase_count <= PW_SHM_MAX_PHASES;
    if (phases_valid) {
        for (uint32_t i = 0; i < hdr->phase_count; i++) {
            pw_shm_phase_t *phase = &hdr->phases[i];
            if (phase->first_slot != end_slot || phase->end_slot < end_slot || phase->end_slot > step_count
                || atomic_load_explicit(&phase->arrived, memory_order_acquire) != 0u
                || atomic_load_explicit(&phase->acknowledged, memory_order_acquire) != 0u
                || atomic_load_explicit(&phase->completed, memory_order_acquire) != 0u) phases_valid = 0;
            end_slot = phase->end_slot;
        }
    }
    if (!phases_valid || end_slot != step_count) {
        pw_failure(evidence, PW_OP_HEADER, PW_FAILURE_PHASE_LAYOUT, PW_NATIVE_NONE,
                   0, 0, 0, UINT32_MAX, PW_SHM_MAX_PHASES);
        pw_diagnostic(evidence, "invalid phase partition or publication input");
        return 9;
    }


    prepare_extension(hdr, args.extension_fd);

    /* Ensure host-populated strings are bounded before the sandbox is
     * applied. The worker is intentionally defensive here because a
     * missing NUL would otherwise let open/bootstrap_look_up read past
     * the slot's fixed field after apply. */
    for (uint32_t i = 0; i < step_count; i++) {
        slots[i].step_id[PW_SHM_STEP_ID_MAX - 1u] = '\0';
        slots[i].target[PW_SHM_TARGET_MAX - 1u] = '\0';
        atomic_store_explicit(&slots[i].completed, 0u, memory_order_release);
    }

    if (hdr->param_count > PW_SHM_MAX_PARAMS) {
        fprintf(stderr,
                "pw-probe-runner: header param_count=%u exceeds PW_SHM_MAX_PARAMS=%u\n",
                hdr->param_count, PW_SHM_MAX_PARAMS);
        pw_failure(evidence, PW_OP_HEADER, PW_FAILURE_PARAM_LIMIT, PW_NATIVE_NONE, 0, 0, 0, UINT32_MAX, PW_SHM_MAX_PARAMS);
        pw_diagnostic(evidence, "parameter count exceeds shared-memory capacity");
        erase_accepted_token();
        return 8;
    }
    /* Snapshot the host's expected policy length once; the comparison after
     * EOF uses this copy even if shared input changes. The buffer's final byte
     * is the terminating NUL, so an expectation of the whole buffer can never
     * be met and is refused as invalid host input before any policy byte is
     * consumed. Zero is a valid expectation (an admitted empty source). */
    const uint32_t policy_bytes_expected = hdr->policy_bytes_expected;
    if (policy_bytes_expected > PW_SHM_POLICY_BYTES - 1u) {
        fprintf(stderr,
                "pw-probe-runner: header policy_bytes_expected=%u exceeds the %u-byte source capacity\n",
                policy_bytes_expected, PW_SHM_POLICY_BYTES - 1u);
        pw_failure(evidence, PW_OP_HEADER, PW_FAILURE_LENGTH_EXPECTATION, PW_NATIVE_NONE, 0, 0, 0, UINT32_MAX,
                   policy_bytes_expected);
        pw_diagnostic(evidence, "expected policy length exceeds the source capacity (expectation in detail)");
        erase_accepted_token();
        return 10;
    }
    pw_progress(evidence, PW_OP_HEADER, PW_PROGRESS_RETURNED, UINT32_MAX);

    /* Clock setup follows the adjacent header/policy-read refusal convention:
     * a published failure and a distinct exit, with applied, done and apply_rc
     * untouched. It precedes every policy byte and the application. */
    if (pw_timing_setup(&timing, evidence) != 0) { erase_accepted_token(); return 12; }

    uint32_t param_count = hdr->param_count;
    for (uint32_t i = 0; i < param_count; i++) {
        params[i].key[PW_SHM_PARAM_KEY_MAX - 1u] = '\0';
        params[i].value[PW_SHM_PARAM_VALUE_MAX - 1u] = '\0';
    }

    /* Read policy text into a fixed buffer. SBPL policies are
     * typically small (KiB); cap at 256 KiB so a runaway producer
     * fails loudly rather than allocating unboundedly or silently
     * truncating. */
    static char policy_buf[PW_SHM_POLICY_BYTES];
    pw_progress(evidence, PW_OP_POLICY_READ, PW_PROGRESS_STARTED, UINT32_MAX);
    ssize_t plen = read_all_from_fd(args.policy_fd, policy_buf, sizeof(policy_buf));
    int policy_errno = errno;
    pw_progress(evidence, PW_OP_POLICY_READ, PW_PROGRESS_RETURNED, UINT32_MAX);
    if (plen < 0) {
        pw_failure(evidence, PW_OP_POLICY_READ, plen == -2 ? PW_FAILURE_SOURCE_LIMIT : PW_FAILURE_POLICY_READ,
                   plen == -2 ? PW_NATIVE_NONE : PW_NATIVE_INTEGER,
                   plen == -2 ? 0 : -1, plen != -2, policy_errno, UINT32_MAX, PW_SHM_POLICY_BYTES - 1);
        pw_diagnostic(evidence, plen == -2 ? "policy exceeds fixed source buffer" : "failed reading policy input");
        if (plen == -2) {
            fprintf(stderr,
                    "pw-probe-runner: policy exceeds fixed buffer (%zu bytes max)\n",
                    sizeof(policy_buf) - 1u);
        } else {
            fprintf(stderr, "pw-probe-runner: failed reading policy: %s\n", strerror(errno));
        }
        erase_accepted_token();
        return 7;
    }
    /* EOF receipt: publish the count actually read before judging it, so the
     * host can set it beside its own write progress on every path that reached
     * EOF, refusals included. The payload is immutable after the flag. Read
     * errors and overflow returned above and publish nothing here. */
    hdr->policy_bytes_received = (uint32_t)plen;
    atomic_store_explicit(&hdr->policy_read_published, 1u, memory_order_release);
    /* One rule for the two guards below: a prefix of the source the reply's
     * policy_sha256 describes is never compiled. The pipe carries no framing,
     * so a submission cut at EOF after a complete form would otherwise arrive
     * as a shorter valid policy; the host's expected length is the only thing
     * that distinguishes it. Any difference, short or long, is refused before
     * the NUL scan and before any libsandbox call. */
    if ((uint32_t)plen != policy_bytes_expected) {
        pw_failure(evidence, PW_OP_POLICY_READ, PW_FAILURE_SOURCE_LENGTH, PW_NATIVE_NONE,
                   0, 0, 0, UINT32_MAX, (uint32_t)plen);
        pw_diagnostic(evidence, "policy length at EOF differs from the host's expectation (received count in detail)");
        fprintf(stderr, "pw-probe-runner: policy delivered %zd bytes, host expected %u; refusing to compile\n",
                plen, policy_bytes_expected);
        erase_accepted_token();
        return 11;
    }
    /* The reader's own guard for the one native string that arrives with an
     * explicit length. sandbox_compile_string takes a C string, so an embedded
     * NUL would silently compile a prefix of the source while the reply's
     * policy_sha256 described the whole submission. The host refuses NUL at
     * admission; this refusal does not depend on it. */
    {
        size_t visible = strnlen(policy_buf, (size_t)plen);
        if (visible != (size_t)plen) {
            pw_failure(evidence, PW_OP_POLICY_READ, PW_FAILURE_SOURCE_NUL, PW_NATIVE_NONE,
                       0, 0, 0, UINT32_MAX, (uint32_t)visible);
            pw_diagnostic(evidence, "policy contains an embedded NUL (byte offset in detail)");
            fprintf(stderr, "pw-probe-runner: policy contains an embedded NUL at byte %zu\n", visible);
            erase_accepted_token();
            return 9;
        }
    }

    /* Build SandboxParams from the host-populated params region. The
     * worker only allocates a params object when param_count > 0; an
     * empty params region keeps the v1 behaviour of passing NULL,
     * which sandbox_compile_string accepts. Any sandbox_set_param
     * failure is fatal — silently dropping a param could change
     * which subpath/value the policy denies. */
    /* Snapshot once: these exact C strings feed both sandbox_set_param and the
     * capture identity, even if a buggy host subsequently changes shared input. */
    static pw_shm_param_t consumed_params[PW_SHM_MAX_PARAMS];
    unsigned char capture_nonce[PW_SHM_CAPTURE_NONCE_BYTES];
    memcpy(capture_nonce, hdr->capture_nonce, sizeof(capture_nonce));
    memcpy(consumed_params, params, param_count * sizeof(*params));
    params = consumed_params;
    void *params_obj = NULL;
    if (param_count > 0) {
        pw_progress(evidence, PW_OP_PARAMS_CREATE, PW_PROGRESS_STARTED, UINT32_MAX);
        params_obj = sandbox_create_params();
        pw_progress(evidence, PW_OP_PARAMS_CREATE, PW_PROGRESS_RETURNED, UINT32_MAX);
        if (!params_obj) {
            pw_failure(evidence, PW_OP_PARAMS_CREATE, PW_FAILURE_NATIVE, PW_NATIVE_NULL, 0, 0, 0, UINT32_MAX, 0);
            pw_diagnostic(evidence, "sandbox_create_params returned NULL");
            fprintf(stderr,
                    "pw-probe-runner: sandbox_create_params returned NULL\n");
            hdr->apply_rc = -1;
            publish_done_and_exit(hdr);
        }
        for (uint32_t i = 0; i < param_count; i++) {
            if (!memchr(params[i].key, 0, sizeof(params[i].key))
                    || !memchr(params[i].value, 0, sizeof(params[i].value))) {
                pw_failure(evidence, PW_OP_PARAM_SET, PW_FAILURE_PARAM_ENCODING, PW_NATIVE_NONE, 0, 0, 0, i, 0);
                pw_diagnostic(evidence, "parameter is not NUL terminated");
                sandbox_free_params(params_obj);
                hdr->apply_rc = -1;
                publish_done_and_exit(hdr);
            }
            pw_progress(evidence, PW_OP_PARAM_SET, PW_PROGRESS_STARTED, i);
            int srv = sandbox_set_param(params_obj, params[i].key, params[i].value);
            pw_progress(evidence, PW_OP_PARAM_SET, PW_PROGRESS_RETURNED, i);
            if (srv != 0) {
                pw_failure(evidence, PW_OP_PARAM_SET, PW_FAILURE_NATIVE, PW_NATIVE_INTEGER, srv, 0, 0, i, 0);
                pw_diagnostic(evidence, "sandbox_set_param returned failure");
                fprintf(stderr,
                        "pw-probe-runner: sandbox_set_param[%u] (key=%s) failed rc=%d\n",
                        i, params[i].key, srv);
                sandbox_free_params(params_obj);
                hdr->apply_rc = -1;
                publish_done_and_exit(hdr);
            }
        }
    }

    /* Compile. sandbox_compile_string allocates internally; that's
     * before sandbox_apply so it's safe. */
    char *compile_err = NULL;
    pw_progress(evidence, PW_OP_COMPILE, PW_PROGRESS_STARTED, UINT32_MAX);
    void *profile = sandbox_compile_string(policy_buf, params_obj, &compile_err);
    pw_progress(evidence, PW_OP_COMPILE, PW_PROGRESS_RETURNED, UINT32_MAX);
    if (!profile) {
        pw_failure(evidence, PW_OP_COMPILE, PW_FAILURE_NATIVE, PW_NATIVE_NULL, 0, 0, 0, UINT32_MAX, 0);
    }
    /* Whether compile succeeded or not, the params object is no longer
     * needed (libsandbox copies what it needs into the profile). */
    if (params_obj) sandbox_free_params(params_obj);
    if (!profile) {
        pw_diagnostic(evidence, compile_err);
        fprintf(stderr,
                "pw-probe-runner: sandbox_compile_string failed: %s\n",
                compile_err ? compile_err : "(no error string)");
        if (compile_err) free(compile_err);
        hdr->apply_rc = -1;
        publish_done_and_exit(hdr);
    }

    /* Capture the same object we are about to apply, before policy restrictions.
     * Output has no pipe backpressure and is published independently of apply.
     * A failed capture leaves policy execution unchanged and reports unavailable. */
    if (hdr->capture_requested == 1u) {
        pw_progress(evidence, PW_OP_CAPTURE, PW_PROGRESS_STARTED, UINT32_MAX);
        unsigned char *capture_base = (unsigned char *)hdr + PW_SHM_HEADER_BYTES
            + PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES + PW_SHM_MAX_PARAMS * PW_SHM_PARAM_BYTES;
        pw_capture_profile((pw_shm_capture_t *)capture_base,
            capture_base + PW_SHM_CAPTURE_HEADER_BYTES, profile,
            policy_buf, strlen(policy_buf), params, param_count, capture_nonce);
        pw_progress(evidence, PW_OP_CAPTURE, PW_PROGRESS_RETURNED, UINT32_MAX);
    }

    /* Pre-ready hang test seam: delay after compilation can overrun the
     * host's readyByteTimeout (so the ready byte below lands on a
     * host-closed pipe). nanosleep is a pre-apply syscall — safe here,
     * before any policy is applied. */
    if (args.pre_ready_hang_ms > 0) {
        long ns = args.pre_ready_hang_ms * 1000000L;
        struct timespec ts = {
            .tv_sec  = ns / 1000000000L,
            .tv_nsec = ns % 1000000000L,
        };
        nanosleep(&ts, NULL);
    }

    /* Pre-apply ready byte. Tells the host the worker has parsed,
     * mmap'd, and is about to apply. Best-effort: if the host already
     * closed --ready-fd (e.g. a slow compile overran its readyByteTimeout)
     * the write returns EPIPE rather than killing us (SIGPIPE is ignored
     * in main), and we continue to apply + the shm sentinel path. */
    pw_progress(evidence, PW_OP_READY, PW_PROGRESS_STARTED, UINT32_MAX);
    int ready_rc = write_ready_byte(args.ready_fd);
    int ready_errno = errno;
    evidence->ready_rc = ready_rc;
    evidence->ready_errno = ready_rc ? ready_errno : 0;
    atomic_store_explicit(&evidence->ready_published, 1, memory_order_release);
    pw_progress(evidence, PW_OP_READY, PW_PROGRESS_RETURNED, UINT32_MAX);
    if (ready_rc != 0) {
        fprintf(stderr,
                "pw-probe-runner: write(ready_fd=%d): %s\n",
                args.ready_fd, strerror(errno));
        /* Continue anyway — the apply + sentinel path still gives
         * the host visibility via shm. */
    }

    /* Apply. After this point: PW extension reporting uses fixed storage;
     * native libraries may allocate. No stdout writes
     * that the policy hasn't been authored to permit. */
    pw_progress(evidence, PW_OP_APPLY, PW_PROGRESS_STARTED, UINT32_MAX);
    int apply_rc = sandbox_apply(profile);
    int apply_errno = errno;   /* capture immediately; only meaningful on failure */
    pw_progress(evidence, PW_OP_APPLY, PW_PROGRESS_RETURNED, UINT32_MAX);
    hdr->apply_rc = apply_rc;
    if (apply_rc != 0) {
        pw_failure(evidence, PW_OP_APPLY, PW_FAILURE_NATIVE, PW_NATIVE_INTEGER, apply_rc, 1, apply_errno, UINT32_MAX, 0);
        pw_diagnostic(evidence, "sandbox_apply returned failure");
        /* Surface WHY apply failed (e.g. EPERM: the witness worker lacks
         * the entitlements this profile requires) so the host can report
         * it instead of a bare -1. */
        hdr->apply_errno = apply_errno;
        /* apply_rc carries the cause; publish it before exiting. */
        publish_done_and_exit(hdr);
    }
    atomic_store_explicit(&hdr->applied, 1u, memory_order_release);

    for (uint32_t phase_index = 0; phase_index < hdr->phase_count; phase_index++) {
        pw_shm_phase_t *phase = &hdr->phases[phase_index];
        wait_for_proceed(hdr, evidence, phase_index, &timing);
        for (uint32_t i = phase->first_slot; i < phase->end_slot; i++) {
            pw_progress(evidence, PW_OP_ATTEMPT, PW_PROGRESS_STARTED, i);
            run_attempt(&slots[i], &timing, phase_index, i,
                        args.kill_before_publish_slot == (long)i);
            pw_progress(evidence, PW_OP_ATTEMPT, PW_PROGRESS_RETURNED, i);
        }
        atomic_store_explicit(&phase->completed, 1u, memory_order_release);
    }

    erase_accepted_token();

    /* Test-seam hang. nanosleep IS a syscall and could be denied by a
     * maximally hostile policy — but the post-apply-hang test seam
     * is for tests running under cooperative policies (typically
     * allow-default with a long-enough host deadline that the hang
     * exceeds it). On an apply-default policy that survives slot
     * execution at all, nanosleep will too. This fires before done
     * flips, so the host
     * observes applied=1, done=0 — exactly the runner_timeout shape. */
    if (args.post_apply_hang_ms > 0) {
        long ns = args.post_apply_hang_ms * 1000000L;
        struct timespec ts = {
            .tv_sec  = ns / 1000000000L,
            .tv_nsec = ns % 1000000000L,
        };
        nanosleep(&ts, NULL);
    }

    /* Test-seam signal after applied and completed slots, before done. A fatal
     * delivery yields abnormal disposition without establishing a policy cause.
     * The host interprets the real publication and reaped status independently. */
    if (args.post_apply_kill_signal > 0) {
        kill(getpid(), args.post_apply_kill_signal);
        /* A failed request or nonfatal/ignored signal can return. The worker
         * then publishes done below; the request alone proves no termination. */
    }

    pw_progress(evidence, PW_OP_FINISHED, PW_PROGRESS_RETURNED, UINT32_MAX);
    publish_done_and_exit(hdr);
}

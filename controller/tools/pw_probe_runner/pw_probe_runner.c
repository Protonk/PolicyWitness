/*
 * pw_probe_runner.c — sandboxed C worker that owns the post-apply
 * syscall surface.
 *
 * Flow:
 *   1. Parse argv: --shm-fd <N> --ready-fd <N> --step-count <N>
 *                  [--policy-fd <N>] (defaults to stdin).
 *   2. mmap the host's pre-populated PW_SHM_REGION_BYTES region from
 *      --shm-fd. Verify abi_version and prepared sentinel.
 *   3. Read SBPL policy text from --policy-fd (or stdin) until EOF
 *      into a stack-fixed buffer. This is the LAST allocation
 *      attempt before sandbox_apply().
 *   4. sandbox_compile_string(). On failure: write apply_rc and
 *      done sentinel, then enter the spin loop (still report the
 *      failure cleanly).
 *   5. Write one byte to --ready-fd. Pre-apply readiness signal.
 *   6. sandbox_apply(). Write apply_rc to header.
 *   7. Write applied sentinel (release ordering).
 *   8. For each populated slot: run the requested attempt. Slot
 *      output writes use regular stores; the slot's `completed` flag
 *      is written with release ordering so the host's acquire-load of
 *      completed pairs with all preceding writes.
 *   9. Write done sentinel.
 *  10. Spin loop: poll exit_requested with acquire ordering, _exit(0)
 *      when set. The spin is bounded by
 *      the host's grace timer (SIGKILL fallback if _exit is denied).
 *
 * No allocations after sandbox_apply. The result region is the only
 * post-apply output channel; stdout/stderr writes may be denied by
 * a (deny default) policy and must not be relied on for results.
 */

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <mach/mach.h>
#include <poll.h>
#include <sandbox.h>
#include <servers/bootstrap.h>
#include <signal.h>
#include <spawn.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "pw_probe_runner_abi.h"

/*
 * Bounded child deadline for exec attempts. The worker enforces a
 * per-attempt wall-clock cap so a hung helper can't escalate into
 * the host's worker-level sentinel timeout (which would also lose
 * the per-step error attribution). When the deadline fires the
 * worker SIGKILLs the child's process group and records
 * "child exceeded N-second deadline" as the slot error. Capped
 * well under the host's default sentinelTimeoutMs (60s) so the
 * per-attempt failure has time to drain and surface before the
 * host gives up on the whole worker. Overridable per-run via the
 * `--exec-child-deadline-ms` test seam. */
#define PW_EXEC_CHILD_DEADLINE_MS_DEFAULT 10000L
#define PW_EXEC_CHILD_DEADLINE_MS_MAX     60000L

static long g_exec_child_deadline_ms = PW_EXEC_CHILD_DEADLINE_MS_DEFAULT;

/* SPI symbols from libsandbox. The public sandbox.h does not declare
 * them; they live in /usr/lib/libsandbox.dylib (link via -lsandbox).
 * Same approach the existing Swift loader uses via dlsym; the C
 * worker links dynamically per R5 ("no static-link gymnastics").
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
     * When > 0, the worker raises signal N on itself AFTER the `applied`
     * sentinel + slot results are durable but BEFORE the `done` sentinel
     * flips. The host then observes applied=1, done=0, and a worker that died
     * from a signal it did NOT send — exactly the runner_sandbox_denied shape
     * (a real kernel sandbox kill produces the same observable state). Makes
     * runner_sandbox_denied reachable from a deterministic specimen.
     * Defaults to 0 (no kill). Safe to leave 0 in production. */
    int post_apply_kill_signal;
    /* Pre-ready hang gate (_test_overrides.worker_pre_ready_hang_ms).
     * When > 0, the worker calls nanosleep(N ms) BEFORE writing the
     * pre-apply ready byte. Models a slow sandbox_compile_string that
     * overruns the host's readyByteTimeout: the host closes the ready
     * pipe first, so the subsequent ready-byte write hits a closed read
     * end. With SIGPIPE ignored (see main) the worker survives that and
     * still reaches sandbox_apply; this seam lets a test pin that
     * survival. Defaults to 0 (no hang). Safe to leave 0 in production. */
    long pre_ready_hang_ms;
    /* Per-exec wall-clock budget. Test seam — production callers
     * leave this at 0 to use PW_EXEC_CHILD_DEADLINE_MS_DEFAULT. */
    long exec_child_deadline_ms;
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
        "                         applied=1/done=0 and a foreign signal —\n"
        "                         the runner_sandbox_denied shape.\n"
        "  --pre-ready-hang-ms N  Optional test-seam. Sleep N ms BEFORE\n"
        "                         the ready byte, modelling a slow compile\n"
        "                         that overruns the host's readyByteTimeout\n"
        "                         (the ready write then lands on a closed\n"
        "                         pipe; SIGPIPE is ignored).\n"
        "  --exec-child-deadline-ms N  Optional test-seam. Per-exec\n"
        "                         attempt wall-clock cap; default %ld ms.\n"
        "                         Helpers exceeding the deadline are\n"
        "                         SIGKILL'd (process group) and the slot\n"
        "                         reports the deadline in error.\n"
        "\n"
        "  --version              Print ABI version and exit.\n",
        PW_SHM_MAX_STEPS, PW_EXEC_CHILD_DEADLINE_MS_DEFAULT);
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
    args->shm_fd                 = -1;
    args->ready_fd               = -1;
    args->policy_fd              = STDIN_FILENO;
    args->step_count             = 0;
    args->post_apply_hang_ms     = 0;
    args->post_apply_kill_signal = 0;
    args->pre_ready_hang_ms      = 0;
    args->exec_child_deadline_ms = 0;

    int i = 1;
    while (i < argc) {
        const char *flag = argv[i];
        if (strcmp(flag, "--shm-fd") == 0 || strcmp(flag, "--ready-fd") == 0 ||
            strcmp(flag, "--step-count") == 0 || strcmp(flag, "--policy-fd") == 0 ||
            strcmp(flag, "--post-apply-hang-ms") == 0 ||
            strcmp(flag, "--post-apply-kill-signal") == 0 ||
            strcmp(flag, "--pre-ready-hang-ms") == 0 ||
            strcmp(flag, "--exec-child-deadline-ms") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "pw-probe-runner: %s requires a value\n", flag);
                return -1;
            }
            long v;
            if (parse_int_arg(argv[i + 1], &v) != 0) {
                fprintf(stderr, "pw-probe-runner: %s: invalid integer %s\n", flag, argv[i + 1]);
                return -1;
            }
            if (strcmp(flag, "--shm-fd") == 0) {
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
                 * raises on itself post-apply / pre-done to reach the
                 * runner_sandbox_denied classifier path deterministically. */
                if (v < 0 || v > 31) {
                    fprintf(stderr, "pw-probe-runner: --post-apply-kill-signal %ld out of range (0..31)\n", v);
                    return -1;
                }
                args->post_apply_kill_signal = (int)v;
            } else if (strcmp(flag, "--pre-ready-hang-ms") == 0) {
                /* Same one-minute cap as the post-apply hang: the seam
                 * only has to exceed the host's readyByteTimeout. */
                if (v < 0 || v > 60 * 1000) {
                    fprintf(stderr, "pw-probe-runner: --pre-ready-hang-ms %ld out of range (0..60000)\n", v);
                    return -1;
                }
                args->pre_ready_hang_ms = v;
            } else if (strcmp(flag, "--exec-child-deadline-ms") == 0) {
                if (v <= 0 || v > PW_EXEC_CHILD_DEADLINE_MS_MAX) {
                    fprintf(stderr,
                            "pw-probe-runner: --exec-child-deadline-ms %ld out of range (1..%ld)\n",
                            v, PW_EXEC_CHILD_DEADLINE_MS_MAX);
                    return -1;
                }
                args->exec_child_deadline_ms = v;
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

/* mmap the host's region. Verifies abi_version and prepared sentinel.
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

/* ---- attempt implementations (R6) --------------------------------------- */

/*
 * Per R6: each attempt is stack-only POSIX (or mach) code, ~25 LOC.
 * No allocations post-apply. Outputs are written to the slot fields
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
    /* Matches the Swift worker: O_WRONLY | O_CREAT without O_EXCL,
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
    /* R_OK: check the kernel would permit a read open without
     * actually opening. New to the C worker — the Swift worker
     * doesn't ship this kind. */
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

static void attempt_sysctl_read(pw_shm_slot_t *slot) {
    char buf[4096];
    size_t len = sizeof(buf);
    if (sysctlbyname(slot->target, buf, &len, NULL, 0) != 0) {
        fail_from_errno(slot, "sysctlbyname");
        return;
    }
    slot->rc = 0;
    slot->errno_val = 0;
}

/* ---- exec attempt machinery (ABI v4) ------------------------------------ */

/*
 * Exec attempts need pipes + posix_spawn_file_actions to capture
 * stdout/stderr. Both of those are syscalls/allocations that we MUST
 * perform pre-apply so the witness honestly reports "the sandbox
 * blocked posix_spawn", not "the worker couldn't even set up the
 * observation frame."
 *
 * Why this matters: the rest of the worker is intentionally simple
 * after sandbox_apply — fixed inputs, no hidden resource
 * acquisition, shared-memory writes as the durable output channel.
 * The exec attempt is the one place that needs pipe creation, a
 * posix_spawn_file_actions handle, an interleaved poll/read drain,
 * and waitpid. If any of those pre-spawn setup syscalls happen
 * AFTER sandbox_apply, an unaugmented (deny default) policy can
 * fail the setup syscall before posix_spawn is reached. The
 * attempt would surface as exec_failed but the per-attempt error
 * attribution would point at pipe()/file_actions_init() — not at
 * the process execution the caller actually wanted to probe.
 * That blurs the witness in exactly the case we exist to surface.
 *
 * The contract this enforces, tested by
 * `tests/suites/runner_use_c_worker/exec_attempt_without_baseline_fails_cleanly`:
 * under (deny default), the failure attribution MUST be
 * posix_spawn itself (child_pid == 0 + errno ∈ {EPERM, EACCES} +
 * error contains "posix_spawn"). Any other failure source means
 * the post-apply syscall surface has grown and the witness is
 * unreliable.
 *
 * Three deliberate fallbacks exist if the preferred model fails
 * empirically on a future macOS revision (do NOT silently degrade
 * to whichever failure happens first):
 *
 *   1. Move pipe/file-action setup into the augment surface and
 *      document that unaugmented exec can fail during setup, not
 *      just at spawn (loses witness purity but preserves observability).
 *   2. Drop stdout/stderr capture from the worker and report only
 *      child_pid/status/spawn errno (smaller post-apply surface).
 *   3. Pre-create only pipes and keep file-action setup post-apply
 *      iff empirically proven allocation-free and not sandbox-gated.
 *
 * Resources are parallel to the slot array (index-aligned). Slots
 * whose kind is not PW_ATTEMPT_EXEC_SPAWN leave their resource entry
 * at its default zero state and never visit attempt_exec_spawn.
 */
typedef struct {
    int stdout_rfd;                 /* parent's read end; -1 when unused */
    int stdout_wfd;                 /* parent's copy of child's stdout; closed post-spawn */
    int stderr_rfd;
    int stderr_wfd;
    posix_spawn_file_actions_t actions;
    posix_spawnattr_t           attr;
    int actions_initialized;        /* 1 if posix_spawn_file_actions_init was called */
    int attr_initialized;           /* 1 if posix_spawnattr_init was called */
    int setup_failed;               /* 1 if pre-apply setup failed for this slot */
    int setup_errno;
    char setup_error[PW_SHM_ERROR_MAX];
} pw_exec_resources_t;

static pw_exec_resources_t exec_resources[PW_SHM_MAX_STEPS];

static void exec_resources_reset_all(void) {
    for (uint32_t i = 0; i < PW_SHM_MAX_STEPS; i++) {
        exec_resources[i].stdout_rfd          = -1;
        exec_resources[i].stdout_wfd          = -1;
        exec_resources[i].stderr_rfd          = -1;
        exec_resources[i].stderr_wfd          = -1;
        exec_resources[i].actions_initialized = 0;
        exec_resources[i].attr_initialized    = 0;
        exec_resources[i].setup_failed        = 0;
        exec_resources[i].setup_errno         = 0;
        exec_resources[i].setup_error[0]      = '\0';
    }
}

/* Pre-apply: walk every slot, and for each exec slot create both pipes
 * and build the posix_spawn_file_actions handle that wires them to the
 * child's STDOUT/STDERR. Per-slot failures are recorded into the
 * resource entry (and surfaced by attempt_exec_spawn at execution
 * time) so a transient resource shortage on one exec slot doesn't kill
 * the whole run.
 *
 * IMPORTANT: this MUST be called before sandbox_apply. After
 * sandbox_apply the worker should only call posix_spawn + close/poll/
 * read/waitpid; opening new pipes post-apply would muddy the
 * "sandbox blocked spawn" reading. */
static void setup_exec_resources(pw_shm_slot_t *slots, uint32_t step_count) {
    for (uint32_t i = 0; i < step_count; i++) {
        if (slots[i].attempt_kind != PW_ATTEMPT_EXEC_SPAWN) continue;
        pw_exec_resources_t *r = &exec_resources[i];

        int out_pipe[2] = {-1, -1};
        int err_pipe[2] = {-1, -1};
        if (pipe(out_pipe) != 0) {
            r->setup_failed = 1;
            r->setup_errno = errno;
            snprintf(r->setup_error, sizeof(r->setup_error),
                     "pipe(stdout): %s", strerror(errno));
            continue;
        }
        if (pipe(err_pipe) != 0) {
            r->setup_failed = 1;
            r->setup_errno = errno;
            snprintf(r->setup_error, sizeof(r->setup_error),
                     "pipe(stderr): %s", strerror(errno));
            close(out_pipe[0]); close(out_pipe[1]);
            continue;
        }

        r->stdout_rfd = out_pipe[0];
        r->stdout_wfd = out_pipe[1];
        r->stderr_rfd = err_pipe[0];
        r->stderr_wfd = err_pipe[1];

        if (posix_spawn_file_actions_init(&r->actions) != 0) {
            r->setup_failed = 1;
            r->setup_errno = errno;
            snprintf(r->setup_error, sizeof(r->setup_error),
                     "posix_spawn_file_actions_init: %s", strerror(errno));
            close(out_pipe[0]); close(out_pipe[1]);
            close(err_pipe[0]); close(err_pipe[1]);
            r->stdout_rfd = r->stdout_wfd = r->stderr_rfd = r->stderr_wfd = -1;
            continue;
        }
        r->actions_initialized = 1;

        if (posix_spawnattr_init(&r->attr) != 0) {
            r->setup_failed = 1;
            r->setup_errno = errno;
            snprintf(r->setup_error, sizeof(r->setup_error),
                     "posix_spawnattr_init: %s", strerror(errno));
            continue;
        }
        r->attr_initialized = 1;

        /*
         * Two attr flags carry the witness-honesty guarantees:
         *
         *   POSIX_SPAWN_CLOEXEC_DEFAULT — Darwin extension. Closes
         *     every inherited FD in the child EXCEPT those mentioned
         *     in this file_actions handle. Without this, the helper
         *     would inherit the worker's shm fd (FD 3 carries the
         *     result region), the policy-pipe read end (would expose
         *     the SBPL source), and every OTHER exec slot's pipe ends.
         *     With it, the child sees exactly the FDs we explicitly
         *     dup/open below — nothing more.
         *
         *   POSIX_SPAWN_SETPGROUP + setpgroup(0) — puts the child in
         *     its own process group with pgid == child_pid. Lets the
         *     deadline path kill(-pgid, SIGKILL) the whole helper
         *     tree (any sub-children the helper spawns) rather than
         *     leaking grandchildren.
         */
        short flags = (short)(POSIX_SPAWN_CLOEXEC_DEFAULT | POSIX_SPAWN_SETPGROUP);
        if (posix_spawnattr_setflags(&r->attr, flags) != 0 ||
            posix_spawnattr_setpgroup(&r->attr, 0) != 0) {
            r->setup_failed = 1;
            r->setup_errno = errno ? errno : EINVAL;
            snprintf(r->setup_error, sizeof(r->setup_error),
                     "posix_spawnattr_set*: %s", strerror(errno));
            continue;
        }

        /* File actions: child gets stdin from /dev/null (so a helper
         * that read(STDIN) gets EOF rather than blocking on an
         * inherited fd that doesn't exist under CLOEXEC_DEFAULT),
         * stdout/stderr dup'd from our pipes. addopen runs in the
         * child after fork, so the FD it produces is one of the
         * CLOEXEC_DEFAULT exceptions. */
        int rc = 0;
        rc |= posix_spawn_file_actions_addopen(&r->actions, STDIN_FILENO,
                                                "/dev/null", O_RDONLY, 0);
        rc |= posix_spawn_file_actions_adddup2(&r->actions, out_pipe[1], STDOUT_FILENO);
        rc |= posix_spawn_file_actions_adddup2(&r->actions, err_pipe[1], STDERR_FILENO);
        /* Close the originals after the adddup2 so the child doesn't
         * carry the pipe-source fds redundantly. CLOEXEC_DEFAULT would
         * close them anyway but we're explicit so future readers see
         * the intent. */
        rc |= posix_spawn_file_actions_addclose(&r->actions, out_pipe[1]);
        rc |= posix_spawn_file_actions_addclose(&r->actions, err_pipe[1]);
        rc |= posix_spawn_file_actions_addclose(&r->actions, out_pipe[0]);
        rc |= posix_spawn_file_actions_addclose(&r->actions, err_pipe[0]);
        if (rc != 0) {
            r->setup_failed = 1;
            r->setup_errno = errno ? errno : EINVAL;
            snprintf(r->setup_error, sizeof(r->setup_error),
                     "posix_spawn_file_actions_add*: rc=%d", rc);
            /* Leave actions_initialized=1 so the destroy in cleanup
             * still runs and frees any partial state. */
        }
    }
}

/* Drain a single stream into the slot buffer. Returns updated `*used`
 * via the in/out parameter, and sets *overflow when content exceeded
 * the buffer. Reads up to one buffered chunk per call so the caller's
 * poll loop can interleave both streams. */
static int drain_one(int fd, char *dst, size_t cap, size_t *used, int *overflow) {
    char buf[256];
    ssize_t n;
    for (;;) {
        n = read(fd, buf, sizeof(buf));
        if (n < 0 && errno == EINTR) continue;
        break;
    }
    if (n <= 0) return (int)n;            /* 0 = EOF; <0 = error */
    size_t room = (cap > *used + 1u) ? (cap - 1u - *used) : 0u;
    size_t to_copy = ((size_t)n < room) ? (size_t)n : room;
    if (to_copy > 0) memcpy(dst + *used, buf, to_copy);
    *used += to_copy;
    if ((size_t)n > to_copy) *overflow = 1;
    return (int)n;
}

static void attempt_exec_spawn(pw_shm_slot_t *slot, pw_exec_resources_t *r) {
    /* Sentinel conventions when no child runs (header documents these). */
    slot->child_pid          = 0;
    slot->child_exit_code    = -1;
    slot->child_term_signal  = 0;
    slot->child_stdout[0]    = '\0';
    slot->child_stderr[0]    = '\0';

    if (r->setup_failed) {
        slot->rc = -1;
        slot->errno_val = r->setup_errno;
        size_t n = strnlen(r->setup_error, sizeof(r->setup_error));
        if (n >= sizeof(slot->error)) n = sizeof(slot->error) - 1u;
        memcpy(slot->error, r->setup_error, n);
        slot->error[n] = '\0';
        return;
    }
    if (!r->actions_initialized) {
        slot->rc = -1;
        slot->errno_val = EINVAL;
        snprintf(slot->error, sizeof(slot->error),
                 "exec slot: file_actions not prepared");
        return;
    }

    /* Build argv from slot->target + slot->argv[1..argv_count-1].
     * The host always writes argv[0] = target plus the caller's args,
     * so argv_count is at least 1 when the host populated the slot;
     * be defensive (use slot->target as the sole entry) if a slot
     * somehow arrives with argv_count == 0. */
    uint32_t total = slot->argv_count;
    if (total == 0u) total = 1u;
    if (total > PW_SHM_MAX_ARGV) total = PW_SHM_MAX_ARGV;

    char *argv_local[PW_SHM_MAX_ARGV + 1];
    /* Defensive NUL-terminate every populated argv entry; the host
     * bounds these but a stray missing NUL would let posix_spawn
     * read past the slot field. */
    argv_local[0] = slot->target;
    for (uint32_t i = 1u; i < total; i++) {
        slot->argv[i][PW_SHM_ARGV_BYTES - 1u] = '\0';
        argv_local[i] = slot->argv[i];
    }
    argv_local[total] = NULL;

    /* Pass an EMPTY environment per the plan: the exec attempt is a
     * witness for the kernel's sandbox enforcement against
     * posix_spawn, not for environment-variable behavior. Inheriting
     * the worker's environ would leak dyld/DYLD_* settings and TMPDIR
     * into the helper. macOS dyld uses the shared cache without env
     * for system binaries; helpers that rely on PATH or HOME must
     * pass absolute paths via target/args anyway. */
    static char *empty_envp[] = { NULL };

    pid_t child = 0;
    int spawn_rc = posix_spawn(&child, slot->target, &r->actions, &r->attr,
                               argv_local, empty_envp);
    if (spawn_rc != 0) {
        /* posix_spawn returns an errno-style value rather than -1+errno. */
        slot->rc = -1;
        slot->errno_val = spawn_rc;
        snprintf(slot->error, sizeof(slot->error),
                 "posix_spawn: %s", strerror(spawn_rc));
        return;
    }

    slot->child_pid = (int32_t)child;
    /* The child is now its own process-group leader (pgid == child)
     * thanks to POSIX_SPAWN_SETPGROUP. Stash the pgid so the deadline
     * path can SIGKILL the whole tree. */
    pid_t child_pgid = child;

    /* Close the parent's copy of the write ends. The child holds them
     * (via the dup2'd STDOUT/STDERR), and once the child exits the
     * kernel closes its references; the read end then sees EOF. If we
     * leave the parent's write ends open here, the read end would
     * never see EOF and the poll loop would spin until the bounded
     * deadline. */
    if (r->stdout_wfd >= 0) { close(r->stdout_wfd); r->stdout_wfd = -1; }
    if (r->stderr_wfd >= 0) { close(r->stderr_wfd); r->stderr_wfd = -1; }

    /* Compute a monotonic deadline. A hung helper would otherwise
     * escalate into a worker-level sentinel timeout (host SIGKILLs
     * the worker, error attribution lost). The deadline gives us a
     * chance to surface "child exceeded deadline" cleanly while
     * still under the host's larger budget. */
    struct timespec deadline_ts;
    if (clock_gettime(CLOCK_MONOTONIC, &deadline_ts) != 0) {
        /* Should not happen on any supported macOS. Fall back to a
         * permissive deadline so we still bound the run rather than
         * blocking forever. */
        deadline_ts.tv_sec = 0; deadline_ts.tv_nsec = 0;
    }
    long deadline_ms_total = g_exec_child_deadline_ms;
    deadline_ts.tv_sec  += deadline_ms_total / 1000L;
    deadline_ts.tv_nsec += (deadline_ms_total % 1000L) * 1000000L;
    if (deadline_ts.tv_nsec >= 1000000000L) {
        deadline_ts.tv_sec += 1;
        deadline_ts.tv_nsec -= 1000000000L;
    }

    /* Drain stdout + stderr interleaved, bounded by the deadline. */
    size_t stdout_n = 0, stderr_n = 0;
    int stdout_overflow = 0, stderr_overflow = 0;
    int stdout_open = 1, stderr_open = 1;
    int deadline_expired = 0;

    while (stdout_open || stderr_open) {
        struct timespec now_ts;
        clock_gettime(CLOCK_MONOTONIC, &now_ts);
        long remaining_ms =
            (long)(deadline_ts.tv_sec  - now_ts.tv_sec)  * 1000L +
            (long)(deadline_ts.tv_nsec - now_ts.tv_nsec) / 1000000L;
        if (remaining_ms <= 0) { deadline_expired = 1; break; }

        struct pollfd pfds[2];
        nfds_t npfds = 0;
        int stdout_idx = -1, stderr_idx = -1;
        if (stdout_open) {
            pfds[npfds].fd = r->stdout_rfd;
            pfds[npfds].events = POLLIN;
            pfds[npfds].revents = 0;
            stdout_idx = (int)npfds; npfds++;
        }
        if (stderr_open) {
            pfds[npfds].fd = r->stderr_rfd;
            pfds[npfds].events = POLLIN;
            pfds[npfds].revents = 0;
            stderr_idx = (int)npfds; npfds++;
        }
        /* Cap each poll() at the remaining budget so we revisit the
         * deadline check at least once per second. */
        int poll_ms = (remaining_ms > 1000L) ? 1000 : (int)remaining_ms;
        int pr = poll(pfds, npfds, poll_ms);
        if (pr < 0 && errno == EINTR) continue;
        if (pr < 0) break;                /* poll error — abandon drain */
        if (pr == 0) continue;            /* short poll, retry under deadline */

        if (stdout_idx >= 0 && (pfds[stdout_idx].revents & (POLLIN | POLLHUP))) {
            int n = drain_one(r->stdout_rfd, slot->child_stdout,
                              sizeof(slot->child_stdout), &stdout_n, &stdout_overflow);
            if (n <= 0) stdout_open = 0;
        } else if (stdout_idx >= 0 &&
                   (pfds[stdout_idx].revents & (POLLERR | POLLNVAL))) {
            stdout_open = 0;
        }
        if (stderr_idx >= 0 && (pfds[stderr_idx].revents & (POLLIN | POLLHUP))) {
            int n = drain_one(r->stderr_rfd, slot->child_stderr,
                              sizeof(slot->child_stderr), &stderr_n, &stderr_overflow);
            if (n <= 0) stderr_open = 0;
        } else if (stderr_idx >= 0 &&
                   (pfds[stderr_idx].revents & (POLLERR | POLLNVAL))) {
            stderr_open = 0;
        }
    }

    /* Append truncation marker when content overflowed the buffer.
     * The marker eats the tail of the buffer so the resulting string
     * stays NUL-terminated within PW_SHM_CHILD_OUTPUT_BYTES. */
    static const char marker[] = "\n... [truncated]";
    const size_t mlen = sizeof(marker) - 1u;
    if (stdout_overflow) {
        size_t start = (stdout_n + mlen + 1u > sizeof(slot->child_stdout))
            ? sizeof(slot->child_stdout) - 1u - mlen
            : stdout_n;
        memcpy(slot->child_stdout + start, marker, mlen);
        stdout_n = start + mlen;
    }
    if (stdout_n >= sizeof(slot->child_stdout)) stdout_n = sizeof(slot->child_stdout) - 1u;
    slot->child_stdout[stdout_n] = '\0';

    if (stderr_overflow) {
        size_t start = (stderr_n + mlen + 1u > sizeof(slot->child_stderr))
            ? sizeof(slot->child_stderr) - 1u - mlen
            : stderr_n;
        memcpy(slot->child_stderr + start, marker, mlen);
        stderr_n = start + mlen;
    }
    if (stderr_n >= sizeof(slot->child_stderr)) stderr_n = sizeof(slot->child_stderr) - 1u;
    slot->child_stderr[stderr_n] = '\0';

    /* Reap. WNOHANG first to find out whether the drain loop exited
     * because the child finished or because the deadline fired with
     * the child still alive. */
    int status = 0;
    pid_t reaped = waitpid(child, &status, WNOHANG);
    if (reaped == 0) {
        /* Still alive — either deadline_expired is set, or the drain
         * loop saw an error. In either case the child has to go now;
         * a runaway helper must not be allowed to outlive its
         * attempt slot. SIGKILL the whole process group to take down
         * any sub-children too. */
        if (kill(-child_pgid, SIGKILL) != 0 && errno != ESRCH) {
            /* Fall back to killing just the leader. ESRCH means the
             * pgroup was already empty (e.g., the leader raced with
             * us into exit) — harmless. */
            (void)kill(child, SIGKILL);
        }
        /* Block until the kernel reports the signaled child. SIGKILL
         * is uncatchable, so this completes promptly. */
        do {
            reaped = waitpid(child, &status, 0);
        } while (reaped < 0 && errno == EINTR);
    } else if (reaped < 0) {
        if (errno == EINTR) {
            /* Retry blocking, since WNOHANG retries on EINTR are
             * unusual and most callers expect a final answer. */
            do {
                reaped = waitpid(child, &status, 0);
            } while (reaped < 0 && errno == EINTR);
        }
    }

    /* Read ends are no longer needed; close before recording the
     * result. */
    if (r->stdout_rfd >= 0) { close(r->stdout_rfd); r->stdout_rfd = -1; }
    if (r->stderr_rfd >= 0) { close(r->stderr_rfd); r->stderr_rfd = -1; }

    if (reaped < 0) {
        slot->rc = -1;
        slot->errno_val = errno;
        snprintf(slot->error, sizeof(slot->error),
                 "waitpid: %s", strerror(errno));
        return;
    }

    if (WIFEXITED(status)) {
        slot->child_exit_code   = WEXITSTATUS(status);
        slot->child_term_signal = 0;
        slot->rc                = slot->child_exit_code;
        slot->errno_val         = 0;
        if (deadline_expired) {
            /* Edge case: the helper happened to finish between the
             * deadline-expired check and the WNOHANG waitpid. Surface
             * the natural exit code but still mark the deadline in
             * the error string so a downstream consumer can see that
             * the run was bounded. */
            snprintf(slot->error, sizeof(slot->error),
                     "child completed at the %ld-second deadline boundary",
                     deadline_ms_total / 1000L);
        }
    } else if (WIFSIGNALED(status)) {
        slot->child_exit_code   = -1;
        slot->child_term_signal = WTERMSIG(status);
        slot->rc                = -1;
        slot->errno_val         = 0;
        if (deadline_expired && slot->child_term_signal == SIGKILL) {
            snprintf(slot->error, sizeof(slot->error),
                     "child exceeded %ld-second deadline; SIGKILL'd",
                     deadline_ms_total / 1000L);
        } else {
            snprintf(slot->error, sizeof(slot->error),
                     "child signaled: signal=%d", slot->child_term_signal);
        }
    } else {
        slot->rc                = -1;
        slot->errno_val         = 0;
        snprintf(slot->error, sizeof(slot->error),
                 "child did not exit or signal: status=%d", status);
    }
}

/* Dispatch on attempt_kind. Initializes slot outputs to "ok defaults"
 * before the per-kind helper runs so a kind that leaves a field
 * untouched lands at a known state. `completed` is the LAST write
 * (release ordering) so the host's acquire-load of completed
 * synchronizes with every other slot write.
 *
 * The slot_idx parameter is required by PW_ATTEMPT_EXEC_SPAWN to find
 * its pre-apply-prepared pipe/file_actions resources; other kinds
 * ignore it. */
static void run_attempt(pw_shm_slot_t *slot, uint32_t slot_idx) {
    slot->rc = 0;
    slot->errno_val = 0;
    slot->observed_path[0] = '\0';
    slot->error[0] = '\0';

    switch (slot->attempt_kind) {
    case PW_ATTEMPT_NONE:                                                 break;
    case PW_ATTEMPT_FILE_OPEN_READ:   attempt_file_open_read(slot);       break;
    case PW_ATTEMPT_FILE_OPEN_WRITE:  attempt_file_open_write(slot);      break;
    case PW_ATTEMPT_FILE_CREATE:      attempt_file_create(slot);          break;
    case PW_ATTEMPT_FILE_UNLINK:      attempt_file_unlink(slot);          break;
    case PW_ATTEMPT_FILE_ACCESS:      attempt_file_access(slot);          break;
    case PW_ATTEMPT_MACH_LOOKUP:      attempt_mach_lookup(slot);          break;
    case PW_ATTEMPT_SYSCTL_READ:      attempt_sysctl_read(slot);          break;
    case PW_ATTEMPT_EXEC_SPAWN:
        attempt_exec_spawn(slot, &exec_resources[slot_idx]);
        break;
    default:
        slot->rc = -1;
        slot->errno_val = ENOSYS;
        snprintf(slot->error, sizeof(slot->error),
                 "unsupported attempt_kind=%u", slot->attempt_kind);
        break;
    }

    atomic_store_explicit(&slot->completed, 1u, memory_order_release);
}

/* ---- post-done spin loop ------------------------------------------------- */

static inline void cpu_relax(void) {
#if defined(__aarch64__) || defined(__arm64__)
    __asm__ volatile("yield" ::: "memory");
#elif defined(__x86_64__)
    __asm__ volatile("pause" ::: "memory");
#else
    atomic_signal_fence(memory_order_seq_cst);
#endif
}

/* Post-apply teardown cannot rely on sleep/yield syscalls surviving
 * hostile profiles. Keep this loop CPU-only: an atomic load, a small
 * processor-relax backoff, and _exit(0) once the host flips the byte. */
static void spin_for_exit(pw_shm_header_t *hdr) {
    for (;;) {
        if (atomic_load_explicit(&hdr->exit_requested, memory_order_acquire) != 0u) {
            _exit(0);
        }
        for (uint32_t i = 0; i < 100000u; i++) {
            cpu_relax();
        }
    }
}

/* ---- main ---------------------------------------------------------------- */

int main(int argc, char **argv) {
    /* Ignore SIGPIPE process-wide. The witness worker must never be
     * killed by a write to a pipe the host has closed — its fate is the
     * policy-under-test's to decide, and a host-side pipe teardown must
     * not forge a fatal-signal exit (which the host reads as the source
     * of truth for sandbox denial). In particular the pre-apply
     * `write_ready_byte` is best-effort: if the host has already closed
     * --ready-fd (e.g. a slow `sandbox_compile_string` overran the
     * host's ready-byte deadline), the write must return EPIPE and let
     * the worker proceed to sandbox_apply + the shm sentinel path,
     * rather than dying of SIGPIPE before apply ever runs. Every write()
     * in this worker already checks its return value. */
    signal(SIGPIPE, SIG_IGN);

    if (argc >= 2 && strcmp(argv[1], "--version") == 0) {
        printf("pw-probe-runner abi=%u region_bytes=%zu max_steps=%u slot_bytes=%u\n",
               PW_PROBE_RUNNER_ABI_VERSION,
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

    void *base = map_region(args.shm_fd);
    if (!base) return 3;

    pw_shm_header_t *hdr = (pw_shm_header_t *)base;
    pw_shm_slot_t   *slots = (pw_shm_slot_t *)((char *)base + PW_SHM_HEADER_BYTES);
    pw_shm_param_t  *params = (pw_shm_param_t *)((char *)slots
                              + ((size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES));

    if (hdr->abi_version != PW_PROBE_RUNNER_ABI_VERSION) {
        fprintf(stderr,
                "pw-probe-runner: ABI mismatch — header says %u, worker built for %u\n",
                hdr->abi_version, PW_PROBE_RUNNER_ABI_VERSION);
        return 4;
    }
    if (atomic_load_explicit(&hdr->prepared, memory_order_acquire) != 1u) {
        fprintf(stderr,
                "pw-probe-runner: host did not set prepared=1; refusing to proceed\n");
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
        return 6;
    }
    if (args.step_count != 0 && args.step_count != hdr->step_count) {
        fprintf(stderr,
                "pw-probe-runner: argv --step-count=%u disagrees with header=%u; using header\n",
                args.step_count, hdr->step_count);
    }
    uint32_t step_count = hdr->step_count;

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
        return 8;
    }
    uint32_t param_count = hdr->param_count;
    for (uint32_t i = 0; i < param_count; i++) {
        params[i].key[PW_SHM_PARAM_KEY_MAX - 1u] = '\0';
        params[i].value[PW_SHM_PARAM_VALUE_MAX - 1u] = '\0';
    }

    /* Pre-apply: for every exec slot, create stdout/stderr pipes and
     * build the posix_spawn_file_actions handle that wires them to the
     * child. Doing this before sandbox_apply is load-bearing: the
     * post-apply worker should only call posix_spawn + close/poll/
     * read/waitpid so a sandbox-denied spawn surfaces cleanly rather
     * than being masked by a denied pipe() or denied
     * posix_spawn_file_actions_init(). */
    if (args.exec_child_deadline_ms > 0) {
        g_exec_child_deadline_ms = args.exec_child_deadline_ms;
    }
    exec_resources_reset_all();
    setup_exec_resources(slots, step_count);

    /* Read policy text into a fixed buffer. SBPL policies are
     * typically small (KiB); cap at 256 KiB so a runaway producer
     * fails loudly rather than allocating unboundedly or silently
     * truncating. */
    enum { POLICY_MAX = 256 * 1024 };
    static char policy_buf[POLICY_MAX];
    ssize_t plen = read_all_from_fd(args.policy_fd, policy_buf, sizeof(policy_buf));
    if (plen < 0) {
        if (plen == -2) {
            fprintf(stderr,
                    "pw-probe-runner: policy exceeds fixed buffer (%zu bytes max)\n",
                    sizeof(policy_buf) - 1u);
        } else {
            fprintf(stderr, "pw-probe-runner: failed reading policy: %s\n", strerror(errno));
        }
        return 7;
    }

    /* Build SandboxParams from the host-populated params region. The
     * worker only allocates a params object when param_count > 0; an
     * empty params region keeps the v1 behaviour of passing NULL,
     * which sandbox_compile_string accepts. Any sandbox_set_param
     * failure is fatal — silently dropping a param could change
     * which subpath/value the policy denies. */
    void *params_obj = NULL;
    if (param_count > 0) {
        params_obj = sandbox_create_params();
        if (!params_obj) {
            fprintf(stderr,
                    "pw-probe-runner: sandbox_create_params returned NULL\n");
            hdr->apply_rc = -1;
            atomic_store_explicit(&hdr->done, 1u, memory_order_release);
            spin_for_exit(hdr);
        }
        for (uint32_t i = 0; i < param_count; i++) {
            int srv = sandbox_set_param(params_obj, params[i].key, params[i].value);
            if (srv != 0) {
                fprintf(stderr,
                        "pw-probe-runner: sandbox_set_param[%u] (key=%s) failed rc=%d\n",
                        i, params[i].key, srv);
                sandbox_free_params(params_obj);
                hdr->apply_rc = -1;
                atomic_store_explicit(&hdr->done, 1u, memory_order_release);
                spin_for_exit(hdr);
            }
        }
    }

    /* Compile. sandbox_compile_string allocates internally; that's
     * before sandbox_apply so it's safe. */
    char *compile_err = NULL;
    void *profile = sandbox_compile_string(policy_buf, params_obj, &compile_err);
    /* Whether compile succeeded or not, the params object is no longer
     * needed (libsandbox copies what it needs into the profile). */
    if (params_obj) sandbox_free_params(params_obj);
    if (!profile) {
        fprintf(stderr,
                "pw-probe-runner: sandbox_compile_string failed: %s\n",
                compile_err ? compile_err : "(no error string)");
        if (compile_err) free(compile_err);
        hdr->apply_rc = -1;
        atomic_store_explicit(&hdr->done, 1u, memory_order_release);
        spin_for_exit(hdr);
    }

    /* Pre-ready hang test seam: model a slow compile that overruns the
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
    if (write_ready_byte(args.ready_fd) != 0) {
        fprintf(stderr,
                "pw-probe-runner: write(ready_fd=%d): %s\n",
                args.ready_fd, strerror(errno));
        /* Continue anyway — the apply + sentinel path still gives
         * the host visibility via shm. */
    }

    /* Apply. After this point: no allocations, no stdout writes
     * that the policy hasn't been authored to permit. */
    int apply_rc = sandbox_apply(profile);
    int apply_errno = errno;   /* capture immediately; only meaningful on failure */
    hdr->apply_rc = apply_rc;
    if (apply_rc != 0) {
        /* Surface WHY apply failed (e.g. EPERM: the witness worker lacks
         * the entitlements this profile requires) so the host can report
         * it instead of a bare -1. */
        hdr->apply_errno = apply_errno;
        /* apply failed — write done so the host stops polling, then
         * spin until exit. apply_rc carries the cause. */
        atomic_store_explicit(&hdr->done, 1u, memory_order_release);
        spin_for_exit(hdr);
    }
    atomic_store_explicit(&hdr->applied, 1u, memory_order_release);

    /* Run attempts. Dispatch by attempt_kind; each helper writes
     * outputs before the slot's `completed` flag is released. */
    for (uint32_t i = 0; i < step_count; i++) {
        run_attempt(&slots[i], i);
    }

    /* Test-seam hang. nanosleep IS a syscall and could be denied by a
     * maximally hostile policy — but the post-apply-hang test seam
     * is for tests running under cooperative policies (typically
     * allow-default with a long-enough host deadline that the hang
     * exceeds it). On an apply-default policy that survives slot
     * execution at all, nanosleep will too. The post-done spin loop
     * is unaffected; this fires before done flips, so a hung host
     * observes applied=1, done=0 — exactly the runner_timeout shape. */
    if (args.post_apply_hang_ms > 0) {
        long ns = args.post_apply_hang_ms * 1000000L;
        struct timespec ts = {
            .tv_sec  = ns / 1000000000L,
            .tv_nsec = ns % 1000000000L,
        };
        nanosleep(&ts, NULL);
    }

    /* Test-seam fatal signal. Fires AFTER the `applied` sentinel + slot
     * results are durable but BEFORE `done` flips, so the host observes
     * applied=1, done=0, and a worker that died from a signal it did NOT send
     * — exactly the runner_sandbox_denied shape (a real kernel sandbox kill
     * produces the same observable state). This re-routes a *condition* (the
     * worker takes a fatal signal mid-run); the host classifier runs for real
     * on it. */
    if (args.post_apply_kill_signal > 0) {
        kill(getpid(), args.post_apply_kill_signal);
        /* SIGKILL never returns. A catchable/ignored signal falls through;
         * the host still sees done=0 and times out — never a false "ok". */
    }

    atomic_store_explicit(&hdr->done, 1u, memory_order_release);
    spin_for_exit(hdr);
}

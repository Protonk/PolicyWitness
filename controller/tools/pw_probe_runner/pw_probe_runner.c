/*
 * pw_probe_runner.c — sandboxed C worker that owns the post-apply
 * syscall surface. Per RUNNER-RESHAPE-PLAN.md Step 5 (R5/R6/R7/R8).
 *
 * Flow (Chunk 2):
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
 *   8. For each populated slot: run the attempt (stub today; Chunk
 *      3 wires real implementations). Slot output writes use
 *      regular stores; the slot's `completed` flag is written with
 *      release ordering so the host's acquire-load of completed
 *      pairs with all preceding writes.
 *   9. Write done sentinel.
 *  10. Spin loop: poll exit_requested with acquire ordering, sleep
 *      between polls, _exit(0) when set. The spin is bounded by
 *      the host's grace timer (SIGKILL fallback if _exit is denied).
 *
 * No allocations after sandbox_apply. The result region is the only
 * post-apply output channel; stdout/stderr writes may be denied by
 * a (deny default) policy and must not be relied on for results.
 */

#include <errno.h>
#include <fcntl.h>
#include <mach/mach.h>
#include <sandbox.h>
#include <servers/bootstrap.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#include "pw_probe_runner_abi.h"

/* SPI symbols from libsandbox. The public sandbox.h does not declare
 * them; they live in /usr/lib/libsandbox.dylib (link via -lsandbox).
 * Same approach the existing Swift loader uses via dlsym; the C
 * worker links statically per R5 ("no static-link gymnastics").
 *
 * The second arg of sandbox_compile_string is an OPAQUE SandboxParams
 * pointer (from sandbox_create_params), NOT a string — passing a
 * string literal here segfaults inside libsandbox. The worker doesn't
 * exercise SBPL params today; pass NULL until the host plumbs them
 * through the request.
 */
extern int sandbox_apply(void *profile);
extern void *sandbox_compile_string(const char *str, void *params, char **error);
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
} pw_args_t;

static void print_usage(FILE *to) {
    fprintf(to,
        "usage: pw-probe-runner --shm-fd <N> --ready-fd <N> --step-count <N>\n"
        "                       [--policy-fd <N>]\n"
        "\n"
        "  --shm-fd N        FD of the host's pw_shm_region mapping.\n"
        "  --ready-fd N      FD the worker writes one byte to just\n"
        "                    before sandbox_apply(). Pre-apply only;\n"
        "                    post-apply readiness is the `applied`\n"
        "                    sentinel in shm.\n"
        "  --step-count N    Number of populated slots, 0..%u.\n"
        "  --policy-fd N     Optional FD with the SBPL policy text.\n"
        "                    Defaults to stdin (FD 0).\n"
        "\n"
        "  --version         Print ABI version and exit.\n",
        PW_SHM_MAX_STEPS);
}

static int parse_int_arg(const char *value, long *out) {
    if (!value || !*value) return -1;
    char *end = NULL;
    long v = strtol(value, &end, 10);
    if (!end || *end) return -1;
    *out = v;
    return 0;
}

static int parse_args(int argc, char **argv, pw_args_t *args) {
    args->shm_fd     = -1;
    args->ready_fd   = -1;
    args->policy_fd  = STDIN_FILENO;
    args->step_count = 0;

    int i = 1;
    while (i < argc) {
        const char *flag = argv[i];
        if (strcmp(flag, "--shm-fd") == 0 || strcmp(flag, "--ready-fd") == 0 ||
            strcmp(flag, "--step-count") == 0 || strcmp(flag, "--policy-fd") == 0) {
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
                args->shm_fd = (int)v;
            } else if (strcmp(flag, "--ready-fd") == 0) {
                args->ready_fd = (int)v;
            } else if (strcmp(flag, "--policy-fd") == 0) {
                args->policy_fd = (int)v;
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
 * Returns the number of bytes read on success, -1 on read error. */
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

/* Dispatch on attempt_kind. Initializes slot outputs to "ok defaults"
 * before the per-kind helper runs so a kind that leaves a field
 * untouched lands at a known state. `completed` is the LAST write
 * (release ordering) so the host's acquire-load of completed
 * synchronizes with every other slot write. */
static void run_attempt(pw_shm_slot_t *slot) {
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

/* Bounded sleep between exit-byte polls. 2 ms matches the host poll
 * cadence documented in R8 so the host's exit-byte write is observed
 * within one cycle in the common case. */
static void spin_for_exit(pw_shm_header_t *hdr) {
    struct timespec ts = { .tv_sec = 0, .tv_nsec = 2 * 1000 * 1000 };
    for (;;) {
        if (atomic_load_explicit(&hdr->exit_requested, memory_order_acquire) != 0u) {
            _exit(0);
        }
        nanosleep(&ts, NULL);
    }
}

/* ---- main ---------------------------------------------------------------- */

int main(int argc, char **argv) {
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

    /* Read policy text into a stack-bounded buffer. SBPL policies are
     * typically small (KiB); cap at 256 KiB so a runaway producer
     * fails loudly rather than allocating unboundedly. The buffer
     * lives on the stack so there is no malloc to worry about. */
    enum { POLICY_MAX = 256 * 1024 };
    static char policy_buf[POLICY_MAX];
    ssize_t plen = read_all_from_fd(args.policy_fd, policy_buf, sizeof(policy_buf));
    if (plen < 0) {
        fprintf(stderr, "pw-probe-runner: failed reading policy: %s\n", strerror(errno));
        return 7;
    }

    /* Compile. sandbox_compile_string allocates internally; that's
     * before sandbox_apply so it's safe. */
    char *compile_err = NULL;
    void *profile = sandbox_compile_string(policy_buf, NULL, &compile_err);
    if (!profile) {
        fprintf(stderr,
                "pw-probe-runner: sandbox_compile_string failed: %s\n",
                compile_err ? compile_err : "(no error string)");
        if (compile_err) free(compile_err);
        hdr->apply_rc = -1;
        atomic_store_explicit(&hdr->done, 1u, memory_order_release);
        spin_for_exit(hdr);
    }

    /* Pre-apply ready byte. Tells the host the worker has parsed,
     * mmap'd, and is about to apply. */
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
    hdr->apply_rc = apply_rc;
    if (apply_rc != 0) {
        /* apply failed — write done so the host stops polling, then
         * spin until exit. apply_rc carries the cause. */
        atomic_store_explicit(&hdr->done, 1u, memory_order_release);
        spin_for_exit(hdr);
    }
    atomic_store_explicit(&hdr->applied, 1u, memory_order_release);

    /* Run attempts. Dispatch by attempt_kind; each helper writes
     * outputs before the slot's `completed` flag is released. */
    for (uint32_t i = 0; i < step_count; i++) {
        run_attempt(&slots[i]);
    }

    atomic_store_explicit(&hdr->done, 1u, memory_order_release);
    spin_for_exit(hdr);
}

/*
 * tests/suites/runner_c_worker_harness/harness.c — drives
 * pw-probe-runner in isolation and reports the result envelope to
 * stdout as a single JSON object. Built and run by the suite's
 * run.sh; not meant to be invoked by hand outside of that path.
 *
 * Usage:
 *   harness <worker_path> <scenario>
 *     scenario: happy_default_allow | bare_deny_default | exit_byte_clean |
 *               max_slots_deny_default | sigkill_fallback
 *
 * The harness:
 *  1. Builds the host side: shm_open + ftruncate + mmap, populate
 *     header + per-scenario slots, set prepared=1.
 *  2. posix_spawn pw-probe-runner with --shm-fd=3, --ready-fd=4,
 *     stdin = pipe carrying the per-scenario policy.
 *  3. Reads the pre-apply ready byte.
 *  4. Polls applied + done sentinels with a bounded deadline.
 *  5. Sets exit_requested and waits for the worker to _exit(0)
 *     (or times out — that's a fail).
 *  6. Prints one JSON object: { ready_byte_received, applied,
 *     apply_rc, done, exit_status, term_signal, slots: [...] }.
 *     The bash driver asserts shape from there.
 *
 * Exit codes:
 *   0 — scenario ran to completion; JSON on stdout is the result.
 *       Per-scenario success criteria are evaluated by the bash
 *       driver, not here.
 *   1 — host-side setup failure (shm_open, posix_spawn, etc).
 *       JSON may be partial or absent; diagnostic on stderr.
 *   2 — usage error.
 */

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <spawn.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "pw_probe_runner_abi.h"

extern char **environ;

/* ---- scenarios ----------------------------------------------------------- */

/* Temp-target lifecycle for the file attempt scenarios. The harness
 * owns the on-disk file (it is unsandboxed); the worker is what runs
 * the unlink/create under the scenario's policy. */
typedef enum {
    TEMP_NONE = 0,        /* scenario uses a fixed target (or none) */
    TEMP_PRECREATE,       /* harness creates the file; expect unlink (or deny) */
    TEMP_ENSURE_ABSENT,   /* harness removes the file; expect the worker to create it */
} temp_target_mode_t;

typedef struct {
    const char *name;
    const char *policy;
    uint32_t step_count;
    int request_exit;
    /* Populates the slots according to scenario semantics. */
    void (*populate_slots)(pw_shm_slot_t *slots);
    /* Optional: populates params + returns the populated count
     * (0..PW_SHM_MAX_PARAMS). NULL means "no params, leave region zero". */
    uint32_t (*populate_params)(pw_shm_param_t *params);

    /* ---- negative / corruption knobs (all default 0 = off) ----
     * These drive the worker's pre-apply self-defense branches over a
     * corrupted shm header. E2e the host always populates that header
     * correctly, so the harness — which pipes policy straight to the
     * worker — is the only vehicle that can reach them. */
    int corrupt_abi;               /* set hdr->abi_version = ABI+1 → worker exits 4 */
    int skip_prepared;             /* leave hdr->prepared = 0     → worker exits 5 */
    uint32_t override_step_count;  /* if !=0, force hdr->step_count after populate (overflow → exit 6) */
    uint32_t override_param_count; /* if !=0, force hdr->param_count after populate (overflow → exit 8) */
    int oversize_policy;           /* pipe > POLICY_MAX bytes      → worker exits 7 */

    /* On-disk target lifecycle for the file unlink/create scenarios. */
    temp_target_mode_t temp_target;
} scenario_t;

static void populate_happy(pw_shm_slot_t *slots) {
    /* One slot: read /etc/hosts. Under (allow default) this succeeds
     * and the slot reports observed_path == /private/etc/hosts. */
    snprintf(slots[0].step_id, sizeof(slots[0].step_id), "read_etc_hosts");
    slots[0].attempt_kind = PW_ATTEMPT_FILE_OPEN_READ;
    snprintf(slots[0].target, sizeof(slots[0].target), "/etc/hosts");
}

static void populate_deny_default(pw_shm_slot_t *slots) {
    /* One slot: read /etc/hosts under bare (deny default). The
     * worker still completes; the slot reports rc=1 with errno
     * = EACCES/EPERM because the kernel denied the open. */
    snprintf(slots[0].step_id, sizeof(slots[0].step_id), "read_etc_hosts_denied");
    slots[0].attempt_kind = PW_ATTEMPT_FILE_OPEN_READ;
    snprintf(slots[0].target, sizeof(slots[0].target), "/etc/hosts");
}

static void populate_max_slots(pw_shm_slot_t *slots) {
    for (uint32_t i = 0; i < PW_SHM_MAX_STEPS; i++) {
        snprintf(slots[i].step_id, sizeof(slots[i].step_id), "none_%03u", i);
        slots[i].attempt_kind = PW_ATTEMPT_NONE;
        slots[i].target[0] = '\0';
    }
}

/* Populate one slot that reads /etc/hosts and one param TARGET=/etc.
 * Paired with SCEN_PARAMS_ROUND_TRIP_POLICY below. */
static void populate_params_slot(pw_shm_slot_t *slots) {
    snprintf(slots[0].step_id, sizeof(slots[0].step_id), "read_etc_hosts_param_target");
    slots[0].attempt_kind = PW_ATTEMPT_FILE_OPEN_READ;
    snprintf(slots[0].target, sizeof(slots[0].target), "/etc/hosts");
}

static uint32_t populate_params_target(pw_shm_param_t *params) {
    snprintf(params[0].key, sizeof(params[0].key), "TARGET");
    /* Subpath match in SBPL is against the kernel-canonical form, not
     * userspace aliases — /etc/hosts realpaths to /private/etc/hosts,
     * so TARGET must be /private/etc for the deny rule to fire. This
     * is an SBPL semantic detail, not a worker concern; the test
     * documents it inline so a future reader doesn't waste time
     * debugging it again. */
    snprintf(params[0].value, sizeof(params[0].value), "/private/etc");
    return 1u;
}

/* Unlink + create slots. step_id + attempt_kind only; the harness fills
 * slots[0].target with the temp path it owns (see temp_target handling in
 * run_scenario), so these leave target empty. */
static void populate_unlink(pw_shm_slot_t *slots) {
    snprintf(slots[0].step_id, sizeof(slots[0].step_id), "unlink_temp_target");
    slots[0].attempt_kind = PW_ATTEMPT_FILE_UNLINK;
    slots[0].target[0] = '\0';
}

static void populate_create(pw_shm_slot_t *slots) {
    snprintf(slots[0].step_id, sizeof(slots[0].step_id), "create_temp_target");
    slots[0].attempt_kind = PW_ATTEMPT_FILE_CREATE;
    slots[0].target[0] = '\0';
}

/* Allow file-read but (deny default) — the worker can read /etc/hosts
 * but everything else is denied. Lets the happy_default_allow case run
 * under a maximally-restrictive policy that still permits the probe;
 * exercises the post-apply minimal syscall surface. */
static const char SCEN_ALLOW_DEFAULT_POLICY[] =
    "(version 1)\n"
    "(allow default)\n";

/* The downstream bug-report shape: (deny default) with nothing else.
 * The C worker must keep its shared-memory writes + spin loop alive
 * under this profile. */
static const char SCEN_DENY_DEFAULT_POLICY[] =
    "(version 1)\n"
    "(deny default)\n";

/* Default-allow with one deny rule whose subpath is taken from the
 * TARGET param. Without sandbox_set_param + a compatible params
 * object, sandbox_compile_string fails because (param "TARGET")
 * resolves to nothing. With it, the policy denies file-read-data
 * under /etc — so the /etc/hosts open fails with EPERM. Either
 * outcome proves the param round-tripped:
 *   - compile failure ⇒ params object wasn't built correctly,
 *   - kernel allow on /etc/hosts ⇒ param value didn't reach the
 *     compiled profile,
 *   - kernel deny on /etc/hosts ⇒ params are live.
 */
static const char SCEN_PARAMS_ROUND_TRIP_POLICY[] =
    "(version 1)\n"
    "(allow default)\n"
    "(deny file-read-data (subpath (param \"TARGET\")))\n";

/* Deliberately malformed: a missing close paren makes
 * sandbox_compile_string fail. Exercises the worker's compile-failure
 * branch — apply_rc=-1, done flips, applied stays 0, and the worker
 * still clean-exits on the exit byte rather than dying. This is the same
 * worker branch a real `sandbox_apply_failed` run takes (the controller no
 * longer runs sbpl-check on the happy path, so malformed SBPL reaches the worker,
 * where compile failure and apply failure are indistinguishable); the harness
 * exercises it in isolation without the host/XPC path. */
static const char SCEN_COMPILE_FAILURE_POLICY[] =
    "(version 1)\n"
    "(allow default";

/* Valid placeholder; the oversize_policy flag makes run_scenario pipe a
 * >POLICY_MAX buffer instead, so this text is never what the worker reads. */
static const char SCEN_POLICY_OVERFLOW_PLACEHOLDER[] =
    "(version 1)\n(allow default)\n";

static scenario_t SCENARIOS[] = {
    /* name, policy, step_count, request_exit, populate_slots, populate_params,
     * corrupt_abi, skip_prepared, override_step_count, override_param_count,
     * oversize_policy, temp_target */
    { "happy_default_allow",    SCEN_ALLOW_DEFAULT_POLICY, 1,                1, populate_happy,        NULL,                   0, 0, 0, 0, 0, TEMP_NONE },
    { "bare_deny_default",      SCEN_DENY_DEFAULT_POLICY,  1,                1, populate_deny_default, NULL,                   0, 0, 0, 0, 0, TEMP_NONE },
    { "exit_byte_clean",        SCEN_ALLOW_DEFAULT_POLICY, 1,                1, populate_happy,        NULL,                   0, 0, 0, 0, 0, TEMP_NONE },
    { "max_slots_deny_default", SCEN_DENY_DEFAULT_POLICY,  PW_SHM_MAX_STEPS, 1, populate_max_slots,    NULL,                   0, 0, 0, 0, 0, TEMP_NONE },
    { "sigkill_fallback",       SCEN_ALLOW_DEFAULT_POLICY, 1,                0, populate_happy,        NULL,                   0, 0, 0, 0, 0, TEMP_NONE },
    { "params_round_trip",      SCEN_PARAMS_ROUND_TRIP_POLICY, 1,            1, populate_params_slot,  populate_params_target, 0, 0, 0, 0, 0, TEMP_NONE },

    /* #1 — file attempt kinds with no other execution coverage. */
    { "unlink_allow",           SCEN_ALLOW_DEFAULT_POLICY, 1,                1, populate_unlink,       NULL,                   0, 0, 0, 0, 0, TEMP_PRECREATE },
    { "unlink_deny",            SCEN_DENY_DEFAULT_POLICY,  1,                1, populate_unlink,       NULL,                   0, 0, 0, 0, 0, TEMP_PRECREATE },
    { "create_allow",           SCEN_ALLOW_DEFAULT_POLICY, 1,                1, populate_create,       NULL,                   0, 0, 0, 0, 0, TEMP_ENSURE_ABSENT },

    /* #2 — pre-apply self-defense / refusal branches. */
    { "compile_failure",        SCEN_COMPILE_FAILURE_POLICY,   1,            1, populate_happy,        NULL,                   0, 0, 0, 0, 0, TEMP_NONE },
    { "abi_mismatch",           SCEN_ALLOW_DEFAULT_POLICY, 1,                1, populate_happy,        NULL,                   1, 0, 0, 0, 0, TEMP_NONE },
    { "prepared_unset",         SCEN_ALLOW_DEFAULT_POLICY, 1,                1, populate_happy,        NULL,                   0, 1, 0, 0, 0, TEMP_NONE },
    { "step_count_overflow",    SCEN_ALLOW_DEFAULT_POLICY, 1,                1, populate_happy,        NULL,                   0, 0, PW_SHM_MAX_STEPS + 1u, 0, 0, TEMP_NONE },
    { "param_count_overflow",   SCEN_ALLOW_DEFAULT_POLICY, 1,                1, populate_happy,        NULL,                   0, 0, 0, PW_SHM_MAX_PARAMS + 1u, 0, TEMP_NONE },
    { "policy_overflow",        SCEN_POLICY_OVERFLOW_PLACEHOLDER, 1,         1, populate_happy,        NULL,                   0, 0, 0, 0, 1, TEMP_NONE },
};
static const size_t SCENARIO_COUNT = sizeof(SCENARIOS) / sizeof(SCENARIOS[0]);

/* ---- JSON helpers -------------------------------------------------------- */

static void emit_json_string(FILE *to, const char *s) {
    putc('"', to);
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        switch (*p) {
        case '"':  fputs("\\\"", to); break;
        case '\\': fputs("\\\\", to); break;
        case '\n': fputs("\\n", to);  break;
        case '\r': fputs("\\r", to);  break;
        case '\t': fputs("\\t", to);  break;
        default:   putc(*p, to);      break;
        }
    }
    putc('"', to);
}

/* ---- helpers ------------------------------------------------------------- */

/* Write the whole buffer, restarting on EINTR. EPIPE is success-ish: the
 * reader (worker) closed early, which is exactly what the policy_overflow
 * scenario expects once the worker hits its cap and exits. */
static int write_all_tolerant(int fd, const char *buf, size_t len) {
    size_t off = 0;
    while (off < len) {
        ssize_t n = write(fd, buf + off, len - off);
        if (n < 0) {
            if (errno == EINTR) continue;
            if (errno == EPIPE) return 0;
            return -1;
        }
        off += (size_t)n;
    }
    return 0;
}

/* Build the harness-owned temp path for the file unlink/create scenarios
 * under $TMPDIR (falling back to /tmp). Fits PW_SHM_TARGET_MAX easily. */
static void build_temp_path(const scenario_t *scen, char *out, size_t cap) {
    const char *tmp = getenv("TMPDIR");
    if (!tmp || !*tmp) tmp = "/tmp";
    snprintf(out, cap, "%spw_c_harness_%d_%s.tmp",
             tmp, (int)getpid(), scen->name);
    /* TMPDIR may or may not have a trailing slash; normalize by only
     * adding one when absent. */
    if (tmp[strlen(tmp) - 1] != '/') {
        snprintf(out, cap, "%s/pw_c_harness_%d_%s.tmp",
                 tmp, (int)getpid(), scen->name);
    }
}

/* ---- main ---------------------------------------------------------------- */

static int run_scenario(const char *worker_path, const scenario_t *scen);

int main(int argc, char **argv) {
    /* The policy_overflow scenario stops reading after the worker hits
     * its cap and exits; the remaining pipe write would otherwise raise
     * SIGPIPE and kill the harness. Tolerate it as EPIPE instead. */
    signal(SIGPIPE, SIG_IGN);

    if (argc != 3) {
        fprintf(stderr, "usage: %s <worker_path> <scenario>\n", argv[0]);
        fprintf(stderr, "scenarios:");
        for (size_t i = 0; i < SCENARIO_COUNT; i++) {
            fprintf(stderr, " %s", SCENARIOS[i].name);
        }
        fputc('\n', stderr);
        return 2;
    }
    for (size_t i = 0; i < SCENARIO_COUNT; i++) {
        if (strcmp(argv[2], SCENARIOS[i].name) == 0) {
            return run_scenario(argv[1], &SCENARIOS[i]);
        }
    }
    fprintf(stderr, "unknown scenario: %s\n", argv[2]);
    return 2;
}

static int run_scenario(const char *worker_path, const scenario_t *scen) {
    /* Anonymous-ish shm region. shm_open returns FDs with FD_CLOEXEC
     * set on macOS; clear it so the dup2 in the child's file actions
     * can land on FD 3. */
    char shm_name[64];
    snprintf(shm_name, sizeof(shm_name), "/pw_c_harness_%d_%s", getpid(), scen->name);
    /* Names cap at 32 chars on macOS; truncate. */
    shm_name[31] = '\0';
    int shm_fd = shm_open(shm_name, O_CREAT | O_RDWR | O_EXCL, 0600);
    if (shm_fd < 0) {
        fprintf(stderr, "harness: shm_open: %s\n", strerror(errno));
        return 1;
    }
    shm_unlink(shm_name);
    fcntl(shm_fd, F_SETFD, 0);
    if (ftruncate(shm_fd, PW_SHM_REGION_BYTES) != 0) {
        fprintf(stderr, "harness: ftruncate: %s\n", strerror(errno));
        return 1;
    }
    void *base = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE,
                      MAP_SHARED, shm_fd, 0);
    if (base == MAP_FAILED) {
        fprintf(stderr, "harness: mmap: %s\n", strerror(errno));
        return 1;
    }
    pw_shm_header_t *hdr = (pw_shm_header_t *)base;
    pw_shm_slot_t *slots = (pw_shm_slot_t *)((char *)base + PW_SHM_HEADER_BYTES);
    pw_shm_param_t *params = (pw_shm_param_t *)((char *)slots
                              + ((size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES));
    memset(hdr, 0, sizeof(*hdr));
    hdr->abi_version = PW_PROBE_RUNNER_ABI_VERSION;
    hdr->step_count = scen->step_count;
    if (scen->populate_slots) scen->populate_slots(slots);
    if (scen->populate_params) {
        hdr->param_count = scen->populate_params(params);
    }

    /* File unlink/create scenarios: the harness owns the on-disk file
     * and writes its path into slot 0's target. PRECREATE makes the file
     * (so the worker's unlink has something to remove, or be denied
     * removing); ENSURE_ABSENT removes it (so the worker's create is the
     * thing that brings it into existence). */
    char temp_path[PW_SHM_TARGET_MAX];
    temp_path[0] = '\0';
    if (scen->temp_target != TEMP_NONE) {
        build_temp_path(scen, temp_path, sizeof(temp_path));
        if (scen->temp_target == TEMP_PRECREATE) {
            int tfd = open(temp_path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
            if (tfd < 0) {
                fprintf(stderr, "harness: precreate temp target %s: %s\n",
                        temp_path, strerror(errno));
                return 1;
            }
            (void)write(tfd, "seed\n", 5);
            close(tfd);
        } else { /* TEMP_ENSURE_ABSENT */
            if (unlink(temp_path) != 0 && errno != ENOENT) {
                fprintf(stderr, "harness: ensure-absent temp target %s: %s\n",
                        temp_path, strerror(errno));
                return 1;
            }
        }
        snprintf(slots[0].target, sizeof(slots[0].target), "%s", temp_path);
    }

    /* Corruption knobs — applied after normal population so they
     * overwrite a valid header field with the value the worker must
     * reject (drives the pre-apply self-defense branches). */
    if (scen->corrupt_abi) {
        hdr->abi_version = PW_PROBE_RUNNER_ABI_VERSION + 1u;
    }
    if (scen->override_step_count != 0u) {
        hdr->step_count = scen->override_step_count;
    }
    if (scen->override_param_count != 0u) {
        hdr->param_count = scen->override_param_count;
    }

    /* The host pre-touches every page it expects the worker to write
     * after apply, so the post-apply path never depends on lazy
     * allocation (which a strict sandbox would block). */
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) page_size = 4096;
    volatile unsigned char *touch = (volatile unsigned char *)base;
    for (size_t off = 0; off < PW_SHM_REGION_BYTES; off += (size_t)page_size) {
        touch[off] = touch[off];
    }
    touch[PW_SHM_REGION_BYTES - 1u] = touch[PW_SHM_REGION_BYTES - 1u];

    /* prepared_unset scenario leaves this at 0 so the worker refuses. */
    if (!scen->skip_prepared) {
        atomic_store_explicit(&hdr->prepared, 1u, memory_order_release);
    }

    /* Ready pipe + policy pipe. Parent-side ends get FD_CLOEXEC so
     * the addclose dance from earlier broken harness designs isn't
     * needed. */
    int ready_pipe[2], policy_pipe[2];
    if (pipe(ready_pipe) != 0 || pipe(policy_pipe) != 0) {
        fprintf(stderr, "harness: pipe: %s\n", strerror(errno));
        return 1;
    }
    fcntl(ready_pipe[0], F_SETFD, FD_CLOEXEC);
    int ready_flags = fcntl(ready_pipe[0], F_GETFL, 0);
    if (ready_flags >= 0) {
        fcntl(ready_pipe[0], F_SETFL, ready_flags | O_NONBLOCK);
    }
    fcntl(policy_pipe[1], F_SETFD, FD_CLOEXEC);

    posix_spawn_file_actions_t fa;
    posix_spawn_file_actions_init(&fa);
    posix_spawn_file_actions_adddup2(&fa, policy_pipe[0], 0);
    posix_spawn_file_actions_adddup2(&fa, shm_fd, 3);
    posix_spawn_file_actions_adddup2(&fa, ready_pipe[1], 4);

    char step_count_str[16];
    snprintf(step_count_str, sizeof(step_count_str), "%u", scen->step_count);
    char *worker_argv[] = {
        (char *)"pw-probe-runner",
        (char *)"--shm-fd",     (char *)"3",
        (char *)"--ready-fd",   (char *)"4",
        (char *)"--step-count", step_count_str,
        NULL,
    };
    pid_t pid;
    int spawn_rc = posix_spawn(&pid, worker_path, &fa, NULL, worker_argv, environ);
    posix_spawn_file_actions_destroy(&fa);
    if (spawn_rc != 0) {
        fprintf(stderr, "harness: posix_spawn: %s\n", strerror(spawn_rc));
        return 1;
    }
    close(policy_pipe[0]);
    close(ready_pipe[1]);

    /* Write policy + close so the worker sees EOF. The policy_overflow
     * scenario synthesizes a > POLICY_MAX buffer here instead of the
     * placeholder text so the worker's overflow check fires. */
    {
        const char *policy_data = scen->policy;
        size_t policy_len = strlen(scen->policy);
        char *big = NULL;
        if (scen->oversize_policy) {
            size_t n = 300u * 1024u;   /* worker caps at 256 KiB */
            big = (char *)malloc(n);
            if (!big) {
                fprintf(stderr, "harness: malloc oversize policy: %s\n", strerror(errno));
                close(policy_pipe[1]);
                return 1;
            }
            memset(big, ' ', n);
            memcpy(big, "(version 1)\n", 12);   /* harmless prefix; never compiles */
            policy_data = big;
            policy_len = n;
        }
        if (write_all_tolerant(policy_pipe[1], policy_data, policy_len) != 0) {
            fprintf(stderr, "harness: write policy: %s\n", strerror(errno));
        }
        free(big);
    }
    close(policy_pipe[1]);

    /* Pre-apply ready byte. 1 s deadline; the worker's pre-apply
     * work is bounded. */
    uint8_t ready_byte = 0;
    int ready_received = 0;
    {
        struct timespec ts = { .tv_sec = 0, .tv_nsec = 10 * 1000 * 1000 };
        for (int i = 0; i < 100; i++) {
            ssize_t n = read(ready_pipe[0], &ready_byte, 1);
            if (n == 1) { ready_received = 1; break; }
            if (n == 0) break;  /* EOF — worker exited without writing */
            if (n < 0 && errno != EINTR && errno != EAGAIN) break;
            nanosleep(&ts, NULL);
        }
    }
    close(ready_pipe[0]);

    /* Poll applied + done. Deadline 2 s — generous for any slow
     * compile/apply on first run after rebuild. A worker that refuses
     * pre-apply (abi / prepared / step_count / param_count / policy
     * overflow) exits immediately without flipping either sentinel, so
     * we also watch for an early worker exit and capture its status here
     * rather than polling the full 2 s. */
    int saw_applied = 0;
    int saw_done = 0;
    int status = 0;
    pid_t reaped = 0;
    int worker_reaped = 0;
    {
        struct timespec ts = { .tv_sec = 0, .tv_nsec = 2 * 1000 * 1000 };
        for (int i = 0; i < 1000; i++) {
            uint32_t applied = atomic_load_explicit(&hdr->applied, memory_order_acquire);
            uint32_t done = atomic_load_explicit(&hdr->done, memory_order_acquire);
            if (applied) saw_applied = 1;
            if (done) { saw_done = 1; break; }
            pid_t w = waitpid(pid, &status, WNOHANG);
            if (w == pid) { worker_reaped = 1; reaped = pid; break; }
            nanosleep(&ts, NULL);
        }
    }

    /* Request exit unless the worker already self-exited (refusal path),
     * or this scenario intentionally withholds the exit byte to exercise
     * the host-side SIGKILL fallback. */
    if (scen->request_exit && !worker_reaped) {
        atomic_store_explicit(&hdr->exit_requested, 1u, memory_order_release);
    }

    /* Wait for the worker to clean-exit (unless already reaped above).
     * 1 s deadline — if it hasn't exited by then, SIGKILL so the test
     * doesn't hang. */
    int sent_sigkill = 0;
    if (!worker_reaped) {
        struct timespec ts = { .tv_sec = 0, .tv_nsec = 10 * 1000 * 1000 };
        for (int i = 0; i < 100; i++) {
            reaped = waitpid(pid, &status, WNOHANG);
            if (reaped == pid) break;
            nanosleep(&ts, NULL);
        }
        if (reaped != pid) {
            kill(pid, SIGKILL);
            sent_sigkill = 1;
            waitpid(pid, &status, 0);
        }
    }

    /* Emit result envelope. */
    printf("{");
    printf("\"scenario\":"); emit_json_string(stdout, scen->name);
    printf(",\"ready_byte_received\":%s", ready_received ? "true" : "false");
    printf(",\"applied\":%s", saw_applied ? "true" : "false");
    printf(",\"apply_rc\":%d", hdr->apply_rc);
    printf(",\"done\":%s", saw_done ? "true" : "false");
    printf(",\"sent_sigkill\":%s", sent_sigkill ? "true" : "false");
    if (WIFEXITED(status)) {
        printf(",\"exit_code\":%d,\"term_signal\":null", WEXITSTATUS(status));
    } else if (WIFSIGNALED(status)) {
        printf(",\"exit_code\":null,\"term_signal\":%d", WTERMSIG(status));
    } else {
        printf(",\"exit_code\":null,\"term_signal\":null");
    }
    printf(",\"slots\":[");
    for (uint32_t i = 0; i < scen->step_count; i++) {
        if (i) putc(',', stdout);
        uint32_t completed = atomic_load_explicit(&slots[i].completed, memory_order_acquire);
        printf("{");
        printf("\"step_id\":"); emit_json_string(stdout, slots[i].step_id);
        printf(",\"completed\":%u", completed);
        printf(",\"rc\":%d", slots[i].rc);
        printf(",\"errno\":%d", slots[i].errno_val);
        printf(",\"observed_path\":"); emit_json_string(stdout, slots[i].observed_path);
        printf(",\"error\":"); emit_json_string(stdout, slots[i].error);
        printf("}");
    }
    printf("]");
    /* For the file unlink/create scenarios, report whether the
     * harness-owned target exists after the worker ran — the durable
     * proof that the unlink removed it (or the create made it). null for
     * scenarios that don't use a temp target. */
    if (scen->temp_target != TEMP_NONE) {
        int exists_after = (access(temp_path, F_OK) == 0) ? 1 : 0;
        printf(",\"target_exists_after\":%s", exists_after ? "true" : "false");
        unlink(temp_path);   /* best-effort cleanup */
    } else {
        printf(",\"target_exists_after\":null");
    }
    printf("}\n");
    fflush(stdout);

    munmap(base, PW_SHM_REGION_BYTES);
    close(shm_fd);
    return 0;
}

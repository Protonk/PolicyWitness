/*
 * tests/suites/runner_c_worker_harness/harness.c — drives
 * pw-probe-runner in isolation and reports the result envelope to
 * stdout as a single JSON object. Built and run by the suite's
 * run.sh; not meant to be invoked by hand outside of that path.
 *
 * Usage:
 *   harness <worker_path> <scenario>
 *     scenario: happy_default_allow | bare_deny_default | exit_byte_clean
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

typedef struct {
    const char *name;
    const char *policy;
    uint32_t step_count;
    /* Populates the slots according to scenario semantics. */
    void (*populate_slots)(pw_shm_slot_t *slots);
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

/* Allow file-read but (deny default) — the worker can read /etc/hosts
 * but everything else is denied. Lets the happy_default_allow case run
 * under a maximally-restrictive policy that still permits the probe;
 * exercises the post-apply minimal syscall surface. */
static const char SCEN_ALLOW_DEFAULT_POLICY[] =
    "(version 1)\n"
    "(allow default)\n";

/* The downstream bug-report shape: (deny default) with nothing else.
 * The pre-Step-5 Swift worker died here. The C worker must keep its
 * shared-memory writes + spin loop alive under this profile. */
static const char SCEN_DENY_DEFAULT_POLICY[] =
    "(version 1)\n"
    "(deny default)\n";

static scenario_t SCENARIOS[] = {
    { "happy_default_allow", SCEN_ALLOW_DEFAULT_POLICY, 1, populate_happy },
    { "bare_deny_default",   SCEN_DENY_DEFAULT_POLICY,  1, populate_deny_default },
    { "exit_byte_clean",     SCEN_ALLOW_DEFAULT_POLICY, 1, populate_happy },
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

/* ---- main ---------------------------------------------------------------- */

static int run_scenario(const char *worker_path, const scenario_t *scen);

int main(int argc, char **argv) {
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
    memset(hdr, 0, sizeof(*hdr));
    hdr->abi_version = PW_PROBE_RUNNER_ABI_VERSION;
    hdr->step_count = scen->step_count;
    if (scen->populate_slots) scen->populate_slots(slots);
    atomic_store_explicit(&hdr->prepared, 1u, memory_order_release);

    /* Ready pipe + policy pipe. Parent-side ends get FD_CLOEXEC so
     * the addclose dance from earlier broken harness designs isn't
     * needed. */
    int ready_pipe[2], policy_pipe[2];
    if (pipe(ready_pipe) != 0 || pipe(policy_pipe) != 0) {
        fprintf(stderr, "harness: pipe: %s\n", strerror(errno));
        return 1;
    }
    fcntl(ready_pipe[0], F_SETFD, FD_CLOEXEC);
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

    /* Write policy + close so the worker sees EOF. */
    if (write(policy_pipe[1], scen->policy, strlen(scen->policy)) < 0) {
        fprintf(stderr, "harness: write policy: %s\n", strerror(errno));
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
     * compile/apply on first run after rebuild. */
    int saw_applied = 0;
    int saw_done = 0;
    {
        struct timespec ts = { .tv_sec = 0, .tv_nsec = 2 * 1000 * 1000 };
        for (int i = 0; i < 1000; i++) {
            uint32_t applied = atomic_load_explicit(&hdr->applied, memory_order_acquire);
            uint32_t done = atomic_load_explicit(&hdr->done, memory_order_acquire);
            if (applied) saw_applied = 1;
            if (done) { saw_done = 1; break; }
            nanosleep(&ts, NULL);
        }
    }

    /* Request exit. */
    atomic_store_explicit(&hdr->exit_requested, 1u, memory_order_release);

    /* Wait for the worker to clean-exit. 1 s deadline — if it hasn't
     * exited by then, send SIGKILL so the test doesn't hang. */
    int status = 0;
    pid_t reaped = 0;
    int sent_sigkill = 0;
    {
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
    printf("]}\n");
    fflush(stdout);

    munmap(base, PW_SHM_REGION_BYTES);
    close(shm_fd);
    return 0;
}

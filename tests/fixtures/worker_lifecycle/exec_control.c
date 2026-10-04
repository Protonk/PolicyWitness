/* Production exec control flow with independent, deterministic native-call
 * equipment. No child or sandbox is created; each attempt's pipes and spawn
 * handles are real and released through the close stub. Real process/pipe
 * controls live in runner_exec_lifecycle. These tests pin observations, not
 * error wording. */
#include <assert.h>
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <spawn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static int64_t now_ms, spawn_ms, child_exit_ms, eof_ms, kill_ms;
static int spawn_count, group_kills, leader_kills, failed_phase, kill_error;
static int waitid_error, waitpid_error, poll_error, signal_sent, reaped_count;
static int controlled_clock(int, struct timespec *);
static int controlled_spawn(pid_t *pid, const char *path,
    const posix_spawn_file_actions_t *fa, const posix_spawnattr_t *attr,
    char *const argv[], char *const env[]) {
    (void)path; (void)fa; (void)attr; (void)argv; (void)env;
    spawn_count++; now_ms += spawn_ms; *pid = 12345; return 0;
}
static int controlled_poll(struct pollfd *fds, nfds_t count, int timeout) {
    if (poll_error) { errno = poll_error; return -1; }
    if (count && now_ms >= eof_ms) {
        for (nfds_t i = 0; i < count; i++) fds[i].revents = POLLHUP;
        return (int)count;
    }
    now_ms += timeout; return 0;
}
static ssize_t controlled_read(int fd, void *buf, size_t bytes) {
    (void)fd; (void)buf; (void)bytes; return 0;
}
/* The attempt acquires real pipes after admission; release them so repeated
 * attempts cannot exhaust the descriptor table. */
static int controlled_close(int fd) { return close(fd); }
static int controlled_waitid(idtype_t type, id_t id, siginfo_t *info, int options) {
    (void)type;
    assert(options == (WEXITED | WNOHANG | WNOWAIT));
    if (waitid_error) { now_ms++; errno = waitid_error; return -1; }
    if (now_ms >= child_exit_ms) info->si_pid = (pid_t)id;
    return 0;
}
static int controlled_kill(pid_t pid, int sig) {
    assert(sig == SIGKILL);
    if (pid < 0) group_kills++; else leader_kills++;
    kill_ms = now_ms;
    if (kill_error) { errno = kill_error; return -1; }
    signal_sent = 1; return 0;
}
static pid_t controlled_waitpid(pid_t pid, int *status, int options) {
    assert(options == WNOHANG); /* a regression must fail instead of hang */
    if (waitpid_error) { errno = waitpid_error; return -1; }
    if (now_ms < child_exit_ms && !signal_sent) return 0;
    *status = now_ms >= child_exit_ms ? 0 : SIGKILL;
    reaped_count++; return pid;
}
#define PW_MONOTONIC_READ controlled_clock
#define posix_spawn controlled_spawn
#define poll controlled_poll
#define read controlled_read
#define close controlled_close
#define waitid controlled_waitid
#define waitpid controlled_waitpid
#define kill controlled_kill
#define main worker_main
#include "pw_probe_runner.c"
#undef main

static int controlled_clock(int phase, struct timespec *out) {
    if (phase == failed_phase) { errno = EIO; return -1; }
    out->tv_sec = 100 + now_ms / 1000;
    out->tv_nsec = (now_ms % 1000) * 1000000LL;
    return 0;
}
static void reset(void) {
    now_ms = spawn_ms = spawn_count = group_kills = leader_kills = 0;
    waitid_error = waitpid_error = poll_error = kill_error = signal_sent = reaped_count = 0;
    kill_ms = -1; failed_phase = -1;
    child_exit_ms = eof_ms = INT64_MAX;
}
static pw_shm_slot_t attempt(const pw_attempt_budget_t *budget, long child_limit) {
    pw_shm_slot_t slot = {0};
    strcpy(slot.target, "/controlled");
    attempt_exec_spawn(&slot, budget, child_limit);
    assert(slot.child_pid == (spawn_count ? 12345 : 0));
    return slot;
}
int main(void) {
    pw_shm_slot_t slot;
    pw_attempt_budget_t budget;
    /* Absolute plan cutoff survives spawn delay, including a delay that uses
     * the entire budget and one that changes which deadline wins. */
    for (int delay = 0; delay <= 1100; delay += 100) {
        reset(); budget = attempt_budget_start(1000); spawn_ms = delay;
        slot = attempt(&budget, 10000);
        assert(kill_ms == (delay > 1000 ? delay : 1000));
        assert(group_kills == 1 && reaped_count == 1);
        assert(slot.child_term_signal == SIGKILL && slot.rc == -1);
    }
    reset(); budget = attempt_budget_start(1000); spawn_ms = 900;
    (void)attempt(&budget, 500); assert(kill_ms == 1000);
    /* Excluded release time shifts the cutoff once; unrelated work spends it. */
    reset(); budget = attempt_budget_start(1000); now_ms = 5000;
    attempt_budget_exclude(&budget, 5000LL * 1000000); now_ms += 200;
    (void)attempt(&budget, 10000); assert(kill_ms == 6000);
    reset(); budget = attempt_budget_start(1000); now_ms = 1000;
    slot = attempt(&budget, 10000);
    assert(!spawn_count && slot.errno_val == ETIMEDOUT && !group_kills);
    /* Pipe EOF never implies leader exit. Conversely, leader exit never
     * implies that pipe-owning group members have stopped. */
    reset(); budget = attempt_budget_start(1000); eof_ms = 0; child_exit_ms = 300;
    slot = attempt(&budget, 10000);
    assert(now_ms == 300 && !group_kills && slot.child_exit_code == 0 && slot.rc == 0);
    reset(); budget = attempt_budget_start(1000); child_exit_ms = 100;
    slot = attempt(&budget, 10000);
    assert(kill_ms == 1000 && group_kills == 1 && slot.child_exit_code == 0 && slot.rc == -1);
    /* Every semantic clock boundary fails closed, independently of call count. */
    for (int phase = PW_CLOCK_WORKER_START; phase <= PW_CLOCK_EXEC_REAP; phase++) {
        if (phase == PW_CLOCK_PROCEED_START || phase == PW_CLOCK_PROCEED_OBSERVE) continue;
        reset(); failed_phase = phase; budget = attempt_budget_start(1000);
        if (phase == PW_CLOCK_EXEC_REAP) waitpid_error = EINTR;
        slot = attempt(&budget, 10000);
        assert(slot.rc == -1 && slot.errno_val == EIO);
        if (phase <= PW_CLOCK_EXEC_ADMIT) assert(!spawn_count);
        else assert(group_kills == 1);
    }
    reset(); budget = attempt_budget_start(1000); waitid_error = EINTR;
    slot = attempt(&budget, 10000); assert(kill_ms == 1000 && slot.child_term_signal == SIGKILL);
    reset(); budget = attempt_budget_start(1000); poll_error = EIO;
    slot = attempt(&budget, 10000); assert(group_kills == 1 && slot.errno_val == EIO);
    reset(); budget = attempt_budget_start(1000); kill_error = EPERM;
    slot = attempt(&budget, 10000);
    assert(group_kills == 1 && leader_kills == 1 && !reaped_count);
    assert(slot.errno_val == EPERM && slot.child_exit_code == -1 && slot.child_term_signal == 0);
    reset(); budget = attempt_budget_start(1000); waitid_error = ECHILD;
    slot = attempt(&budget, 10000); assert(!group_kills && !leader_kills && slot.errno_val == ECHILD);
    reset(); budget = attempt_budget_start(1000); waitpid_error = EIO;
    slot = attempt(&budget, 10000); assert(slot.errno_val == EIO && slot.child_exit_code == -1);
    reset(); budget = attempt_budget_start(1000); waitpid_error = EINTR;
    slot = attempt(&budget, 10000);
    assert(now_ms == 1000 + PW_EXEC_REAP_GRACE_MS && slot.errno_val == ETIMEDOUT);
    assert(slot.child_exit_code == -1 && slot.child_term_signal == 0);
    puts("ok: absolute budgets, independent EOF/exit, clock phases, cleanup and missing-status evidence");
    return 0;
}

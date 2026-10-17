/* Production exec control flow with independent, deterministic native-call
 * equipment. No child or sandbox is created; each attempt's pipes and spawn
 * handles are real and released through the close stub. Real process/pipe
 * controls live in runner_exec_lifecycle. These tests pin observations, not
 * error wording. Time is a controlled continuous counter at the 125/3
 * timebase unless a case selects another ratio. */
#include <assert.h>
#include <errno.h>
#include <mach/mach_time.h>
#include <poll.h>
#include <signal.h>
#include <spawn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

static int64_t now_ms, spawn_ms, child_exit_ms, eof_ms, kill_ms;
static int spawn_count, group_kills, leader_kills, failed_phase, kill_error;
static int waitid_error, waitpid_error, poll_error, signal_sent, reaped_count;
static uint32_t tb_numer, tb_denom;
static kern_return_t controlled_timebase(mach_timebase_info_t info) {
    info->numer = tb_numer; info->denom = tb_denom; return KERN_SUCCESS;
}
/* Ticks for the controlled millisecond clock; a failed stage reports a value
 * below the origin. Each read leaves a stale permission errno. */
static uint64_t controlled_read(int phase) {
    errno = EPERM;
    if (phase == failed_phase) return 0;
    return 1000 + (uint64_t)((__uint128_t)now_ms * 1000000u * tb_denom / tb_numer);
}
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
static ssize_t controlled_read_fd(int fd, void *buf, size_t bytes) {
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
#define PW_TIMEBASE_INFO controlled_timebase
#define PW_CONTINUOUS_READ controlled_read
#define posix_spawn controlled_spawn
#define poll controlled_poll
#define read controlled_read_fd
#define close controlled_close
#define waitid controlled_waitid
#define waitpid controlled_waitpid
#define kill controlled_kill
#define main worker_main
#include "pw_probe_runner.c"
#undef main

static pw_shm_evidence_t *evidence;
static pw_timing_t timing;

static void reset(void) {
    now_ms = spawn_ms = spawn_count = group_kills = leader_kills = 0;
    waitid_error = waitpid_error = poll_error = kill_error = signal_sent = reaped_count = 0;
    kill_ms = -1; failed_phase = -1;
    child_exit_ms = eof_ms = INT64_MAX;
    tb_numer = 125; tb_denom = 3;
}
/* Worker origin at the current controlled time, then setup as in main. */
static void start(long budget_ms) {
    timing = (pw_timing_t){.proceed_ms = 60000, .budget_ms = budget_ms, .child_ms = 10000};
    pw_clock_start(&timing.clock);
    assert(pw_timing_setup(&timing, evidence) == 0);
}
static uint64_t ticks(long ms) {
    uint64_t value = 0;
    assert(pw_ticks_for_ms(&timing.clock, ms, &value) == 0);
    return value;
}
static pw_shm_slot_t attempt(long child_limit, uint32_t index) {
    pw_shm_slot_t slot = {0};
    strcpy(slot.target, "/controlled");
    timing.child_ms = child_limit;
    timing.child_ticks = ticks(child_limit);
    attempt_exec_spawn(&slot, &timing, 0, index);
    assert(slot.child_pid == (spawn_count ? 12345 : 0));
    return slot;
}
int main(void) {
    void *base = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    assert(base != MAP_FAILED);
    evidence = pw_evidence(base);
    pw_shm_slot_t slot;
    /* Absolute plan cutoff survives spawn delay, including a delay that uses
     * the entire budget and one that changes which deadline wins. */
    for (int delay = 0; delay <= 1100; delay += 100) {
        reset(); start(1000); spawn_ms = delay;
        slot = attempt(10000, 0);
        assert(kill_ms == (delay > 1000 ? delay : 1000));
        assert(group_kills == 1 && reaped_count == 1);
        assert(slot.child_term_signal == SIGKILL && slot.rc == -1 && slot.errno_val == 0);
    }
    reset(); start(1000); spawn_ms = 900;
    (void)attempt(500, 0); assert(kill_ms == 1000);
    reset(); start(1000); spawn_ms = 100;
    (void)attempt(500, 0); assert(kill_ms == 600);  /* the child deadline is smaller */
    /* Excluded release time shifts the cutoff once per exclusion; unrelated
     * work spends it. Setup time after the origin is charged. */
    reset(); start(1000); now_ms = 5000;
    assert(pw_ticks_add(timing.plan_deadline, ticks(3000), &timing.plan_deadline) == 0);
    assert(pw_ticks_add(timing.plan_deadline, ticks(2000), &timing.plan_deadline) == 0);
    now_ms += 200;
    (void)attempt(10000, 0); assert(kill_ms == 6000);
    reset(); start(1000); now_ms = 1000;
    slot = attempt(10000, 0);
    assert(!spawn_count && slot.errno_val == ETIMEDOUT && !group_kills);
    reset(); start(1000); now_ms = 999;
    slot = attempt(10000, 0);
    assert(spawn_count == 1 && kill_ms == 1000);  /* one millisecond below the cutoff spawns */
    /* Pipe EOF never implies leader exit. Conversely, leader exit never
     * implies that pipe-owning group members have stopped. */
    reset(); start(1000); eof_ms = 0; child_exit_ms = 300;
    slot = attempt(10000, 0);
    assert(now_ms == 300 && !group_kills && slot.child_exit_code == 0 && slot.rc == 0);
    reset(); start(1000); child_exit_ms = 100;
    slot = attempt(10000, 0);
    assert(kill_ms == 1000 && group_kills == 1 && slot.child_exit_code == 0 && slot.rc == -1);

    /* Every exec timing stage fails closed as a local fault: no errno, the
     * stage named, the first rejected sample retained with its slot. */
    reset(); start(1000); failed_phase = PW_CLOCK_EXEC_ADMIT;
    slot = attempt(10000, 3);
    assert(!spawn_count && slot.rc == -1 && slot.errno_val == 0);
    assert(strstr(slot.error, "local_timing=backwards_counter stage=exec_admit"));
    assert(strstr(slot.error, "phase=0 slot=3"));
    reset(); start(1000); failed_phase = PW_CLOCK_EXEC_OBSERVE;
    slot = attempt(10000, 4);
    assert(spawn_count == 1 && group_kills == 1 && reaped_count == 1);
    assert(slot.rc == -1 && slot.errno_val == 0 && slot.child_term_signal == SIGKILL);
    assert(strstr(slot.error, "exec observation=local timing") && strstr(slot.error, "stage=exec_observe"));
    assert(timing.clock.fault.reason == PW_TIME_REASON_BACKWARDS_COUNTER && timing.clock.fault.slot == 4);
    /* A later attempt refuses before spawn because of that rejection. */
    failed_phase = -1; spawn_count = 0;
    slot = attempt(10000, 5);
    assert(!spawn_count && slot.rc == -1 && slot.errno_val == 0);
    assert(strstr(slot.error, "local_timing=prior_clock_fault stage=exec_admit"));
    assert(strstr(slot.error, "stage=exec_observe phase=0 slot=4"));
    /* Unusable reap time permits the immediate observation, keeping its status. */
    reset(); start(1000); failed_phase = PW_CLOCK_EXEC_REAP; eof_ms = 0; child_exit_ms = 200;
    slot = attempt(10000, 0);
    assert(reaped_count == 1 && slot.child_exit_code == 0 && slot.rc == -1 && slot.errno_val == 0);
    assert(strstr(slot.error, "reaped=1") && strstr(slot.error, "stage=exec_reap"));
    /* Otherwise timed reaping stops with the local fault and no status. */
    reset(); start(1000); failed_phase = PW_CLOCK_EXEC_REAP; waitpid_error = EINTR;
    slot = attempt(10000, 0);
    assert(group_kills == 1 && !reaped_count && slot.rc == -1 && slot.errno_val == 0);
    assert(slot.child_exit_code == -1 && slot.child_term_signal == 0 && strstr(slot.error, "reaped=0"));
    assert(strstr(slot.error, "local_timing=backwards_counter stage=exec_reap"));  /* no second read */
    /* A local fault beside a native cleanup failure keeps the native errno. */
    reset(); start(1000); failed_phase = PW_CLOCK_EXEC_OBSERVE; kill_error = EPERM;
    slot = attempt(10000, 0);
    assert(group_kills == 1 && leader_kills == 1 && !reaped_count);
    assert(slot.errno_val == EPERM && strstr(slot.error, "group_cleanup_errno=1"));
    assert(strstr(slot.error, "local_timing=backwards_counter"));

    /* An arithmetic refusal stays local: near the cutoff, adding the child
     * allowance to a valid sample overflows; the clock stays usable. */
    reset(); tb_numer = 1; tb_denom = 150000000;
    start(115000); now_ms = 114999;
    slot = attempt(10000, 2);
    assert(spawn_count == 1 && group_kills == 1 && slot.rc == -1 && slot.errno_val == 0);
    assert(strstr(slot.error, "local_timing=deadline_overflow stage=exec_observe"));
    assert(!strstr(slot.error, "first rejected sample"));
    assert(timing.clock.fault.reason == 0);
    assert(timing.clock.last == controlled_read(PW_CLOCK_EXEC_REAP));
    uint64_t elapsed = 0;
    assert(pw_clock_sample(&timing.clock, PW_CLOCK_EXEC_ADMIT, 0, 0, &elapsed) == 0);

    /* A later rejected sample owns the first sticky origin; the earlier
     * arithmetic refusal must neither replace that origin nor suppress it. */
    uint64_t last_accepted = timing.clock.last;
    int prior_spawns = spawn_count;
    failed_phase = PW_CLOCK_EXEC_ADMIT;
    pw_shm_slot_t later = {0};
    strcpy(later.target, "/controlled");
    attempt_exec_spawn(&later, &timing, 1, 7);
    assert(spawn_count == prior_spawns && later.child_pid == 0);
    assert(later.rc == -1 && later.errno_val == 0 && timing.clock.last == last_accepted);
    assert(timing.clock.fault.reason == PW_TIME_REASON_BACKWARDS_COUNTER);
    assert(timing.clock.fault.stage == PW_CLOCK_EXEC_ADMIT);
    assert(timing.clock.fault.phase == 1 && timing.clock.fault.slot == 7);
    assert(strstr(later.error, "local_timing=backwards_counter stage=exec_admit"));
    assert(strstr(later.error, "first rejected sample: reason=backwards_counter stage=exec_admit phase=1 slot=7"));
    /* Forward-looking time cannot clear it or move its origin to this refusal. */
    failed_phase = -1;
    attempt_exec_spawn(&later, &timing, 2, 8);
    assert(spawn_count == prior_spawns && later.child_pid == 0 && later.rc == -1 && later.errno_val == 0);
    assert(timing.clock.last == last_accepted && timing.clock.fault.reason == PW_TIME_REASON_BACKWARDS_COUNTER);
    assert(timing.clock.fault.stage == PW_CLOCK_EXEC_ADMIT && timing.clock.fault.phase == 1 && timing.clock.fault.slot == 7);
    assert(strstr(later.error, "local_timing=prior_clock_fault stage=exec_admit"));
    assert(strstr(later.error, "first rejected sample: reason=backwards_counter stage=exec_admit phase=1 slot=7"));

    /* Native observation failures keep their own errno and cleanup paths. */
    reset(); start(1000); waitid_error = EINTR;
    slot = attempt(10000, 0); assert(kill_ms == 1000 && slot.child_term_signal == SIGKILL);
    reset(); start(1000); poll_error = EIO;
    slot = attempt(10000, 0); assert(group_kills == 1 && slot.errno_val == EIO);
    reset(); start(1000); kill_error = EPERM;
    slot = attempt(10000, 0);
    assert(group_kills == 1 && leader_kills == 1 && !reaped_count);
    assert(slot.errno_val == EPERM && slot.child_exit_code == -1 && slot.child_term_signal == 0);
    reset(); start(1000); waitid_error = ECHILD;
    slot = attempt(10000, 0); assert(!group_kills && !leader_kills && slot.errno_val == ECHILD);
    reset(); start(1000); waitpid_error = EIO;
    slot = attempt(10000, 0); assert(slot.errno_val == EIO && slot.child_exit_code == -1);
    reset(); start(1000); waitpid_error = EINTR;
    slot = attempt(10000, 0);
    assert(now_ms == 1000 + PW_EXEC_REAP_GRACE_MS && slot.errno_val == ETIMEDOUT);
    assert(slot.child_exit_code == -1 && slot.child_term_signal == 0);
    puts("ok: absolute tick budgets, independent EOF/exit, local timing stages, cleanup and missing-status evidence");
    return 0;
}

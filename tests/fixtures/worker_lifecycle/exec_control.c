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

/* The ledger is written only by the substituted native boundaries, before any
 * production payload is inspected. It captures calls (including retries),
 * arguments, returns, meaningful errno/status, stream identity and clock order.
 * Expected control facts below are supplied independently by the equipment. */
typedef struct {
    const char *call;
    int64_t a, b, rc;
    int error, status_present, status;
    uint64_t counter;
} call_record_t;
static call_record_t ledger[20000];
static size_t ledger_n;
static unsigned attempt_number;
static const char *case_name = "timing_regression";
static void record(const char *call, int64_t a, int64_t b, int64_t rc,
                   int error, int status_present, int status, uint64_t counter) {
    assert(ledger_n < sizeof(ledger) / sizeof(ledger[0]));
    ledger[ledger_n++] = (call_record_t){call, a, b, rc, error, status_present, status, counter};
}
static int64_t now_ms, spawn_ms, child_exit_ms, eof_ms, kill_ms;
static int spawn_count, group_kills, leader_kills, failed_phase, kill_error;
static int waitid_error, waitpid_error, poll_error, signal_sent, reaped_count;
static int fallback_error, wait_pending, ignore_signal, spawn_error;
static int stream_fds[2], pipe_count, stream_errors[2], stream_retries[2];
static short stream_revents[2];
static int waitid_interrupts, poll_interrupts, waitpid_interrupts;
static uint32_t tb_numer, tb_denom;
static kern_return_t controlled_timebase(mach_timebase_info_t info) {
    info->numer = tb_numer; info->denom = tb_denom;
    record("timebase", tb_numer, tb_denom, KERN_SUCCESS, 0, 0, 0, 0);
    return KERN_SUCCESS;
}
/* Each read leaves stale permission errno, intentionally unrelated to success. */
static uint64_t controlled_read(int phase) {
    errno = EPERM;
    uint64_t value = phase == failed_phase ? 0 :
        1000 + (uint64_t)((__uint128_t)now_ms * 1000000u * tb_denom / tb_numer);
    record("clock", phase, now_ms, 0, 0, 0, 0, value);
    return value;
}
static int controlled_pipe(int fds[2]) {
    int rc = pipe(fds), saved = rc < 0 ? errno : 0;
    if (rc == 0) { assert(pipe_count < 2); stream_fds[pipe_count++] = fds[0]; }
    record("pipe", rc == 0 ? fds[0] : -1, rc == 0 ? fds[1] : -1, rc, saved, 0, 0, 0);
    return rc;
}
static int controlled_spawn(pid_t *pid, const char *path,
    const posix_spawn_file_actions_t *fa, const posix_spawnattr_t *attr,
    char *const argv[], char *const env[]) {
    (void)path; (void)fa; (void)attr; (void)argv; (void)env;
    spawn_count++; now_ms += spawn_ms;
    if (!spawn_error) *pid = 12345;
    record("spawn", spawn_error ? 0 : *pid, spawn_ms, spawn_error, 0, 0, 0, 0);
    return spawn_error;
}
static int stream_for(int fd) {
    for (int i = 0; i < 2; i++) if (stream_fds[i] == fd) return i;
    assert(!"unexpected stream descriptor"); return -1;
}
static int controlled_poll(struct pollfd *fds, nfds_t count, int timeout) {
    int error = poll_interrupts ? (poll_interrupts--, EINTR) : poll_error;
    int rc = 0;
    if (error) { errno = error; rc = -1; }
    else if (count && now_ms >= eof_ms) {
        for (nfds_t i = 0; i < count; i++)
            fds[i].revents = stream_revents[stream_for(fds[i].fd)];
        rc = (int)count;
    } else now_ms += timeout;
    record("poll", count, timeout, rc, error, 0, 0, 0);
    if (rc > 0) for (nfds_t i = 0; i < count; i++)
        record("revents", stream_for(fds[i].fd), fds[i].fd, fds[i].revents, 0, 0, 0, 0);
    return rc;
}
static ssize_t controlled_read_fd(int fd, void *buf, size_t bytes) {
    (void)buf;
    int stream = stream_for(fd);
    int error = stream_errors[stream];
    if (stream_retries[stream]) { stream_retries[stream]--; error = stream ? EAGAIN : EINTR; }
    ssize_t rc = error ? -1 : 0;
    if (error) errno = error;
    record("read", stream, bytes, rc, error, 0, 0, 0);
    return rc;
}
static int controlled_close(int fd) {
    int rc = close(fd), saved = rc < 0 ? errno : 0;
    record("close", fd, 0, rc, saved, 0, 0, 0); return rc;
}
static int controlled_waitid(idtype_t type, id_t id, siginfo_t *info, int options) {
    assert(type == P_PID && options == (WEXITED | WNOHANG | WNOWAIT));
    int error = waitid_interrupts ? (waitid_interrupts--, EINTR) : waitid_error;
    if (error) { now_ms++; errno = error; }
    else if (now_ms >= child_exit_ms) info->si_pid = (pid_t)id;
    record("waitid", id, options, error ? -1 : 0, error, 0, info->si_pid, 0);
    return error ? -1 : 0;
}
static int controlled_kill(pid_t pid, int sig) {
    assert(sig == SIGKILL);
    if (pid < 0) group_kills++; else leader_kills++;
    kill_ms = now_ms;
    int error = pid < 0 ? kill_error : fallback_error;
    if (error) errno = error;
    else if (!ignore_signal) signal_sent = 1;
    record("kill", pid, sig, error ? -1 : 0, error, 0, 0, 0);
    return error ? -1 : 0;
}
static pid_t controlled_waitpid(pid_t pid, int *status, int options) {
    assert(options == WNOHANG);
    int error = waitpid_interrupts ? (waitpid_interrupts--, EINTR) : waitpid_error;
    pid_t rc = 0;
    if (error) { errno = error; rc = -1; }
    else if (!wait_pending && (now_ms >= child_exit_ms || signal_sent)) {
        *status = now_ms >= child_exit_ms ? 0 : SIGKILL;
        reaped_count++; rc = pid;
    }
    record("waitpid", pid, options, rc, error, rc == pid, rc == pid ? *status : 0, 0);
    return rc;
}
#define pipe controlled_pipe
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
#ifndef PW_EXEC_SOURCE
#define PW_EXEC_SOURCE "pw_probe_runner.c"
#endif
#include PW_EXEC_SOURCE
#undef main

static pw_shm_evidence_t *evidence;
static pw_timing_t timing;

static void reset(void) {
    now_ms = spawn_ms = spawn_count = group_kills = leader_kills = 0;
    waitid_error = waitpid_error = poll_error = kill_error = signal_sent = reaped_count = 0;
    kill_ms = -1; failed_phase = -1;
    fallback_error = wait_pending = ignore_signal = spawn_error = 0;
    waitid_interrupts = poll_interrupts = waitpid_interrupts = pipe_count = 0;
    stream_fds[0] = stream_fds[1] = -1;
    stream_errors[0] = stream_errors[1] = stream_retries[0] = stream_retries[1] = 0;
    stream_revents[0] = stream_revents[1] = POLLHUP;
    ledger_n = 0; case_name = "timing_regression";
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
/* Compare every published raw return with the independent boundary ledger.
 * This checks actual calls, not selected test knobs or diagnostic prose. */
static void verify_ledger(const pw_shm_slot_t *slot) {
#ifndef PW_EXEC_LEDGER_BASELINE
    if (!slot->child_pid) { assert(slot->exec_valid == 0); return; }
    assert(slot->exec_valid == 1);
    const call_record_t *group = NULL, *fallback = NULL, *wait = NULL;
    uint32_t eof[2] = {0}, leader = 0;
    int read_errors[2] = {0}, revents[2] = {0};
    int wait_error = 0, poll_failure = 0, cleanup_seen = 0, reap_seen = 0;
    for (size_t i = 0; i < ledger_n; i++) {
        const call_record_t *c = &ledger[i];
        if (!strcmp(c->call, "kill")) {
            assert(!reap_seen); cleanup_seen = 1;
            if (c->a < 0) { assert(!group && !fallback); group = c; }
            else { assert(group && !fallback); fallback = c; }
        } else if (!strcmp(c->call, "waitpid")) { reap_seen = 1; wait = c; }
        else if (!strcmp(c->call, "waitid")) {
            assert(!cleanup_seen && !reap_seen);
            if (c->rc == 0 && c->status == slot->child_pid) leader = 1;
            if (c->rc < 0 && c->error != EINTR) wait_error = c->error;
        } else if (!strcmp(c->call, "poll") && !cleanup_seen && !reap_seen) {
            if (c->rc < 0 && c->error != EINTR) poll_failure = c->error;
        } else if (!strcmp(c->call, "read")) {
            assert(!cleanup_seen && !reap_seen && (c->a == 0 || c->a == 1));
            if (c->rc == 0) eof[c->a] = 1;
            if (c->rc < 0 && c->error != EINTR && c->error != EAGAIN) read_errors[c->a] = c->error;
        } else if (!strcmp(c->call, "revents")) {
            if (!(c->rc & (POLLIN | POLLHUP)) && (c->rc & (POLLERR | POLLNVAL))) revents[c->a] = (int)c->rc;
        }
    }
    assert(slot->exec_leader_exit_observed == leader);
    assert(slot->exec_stdout_eof == eof[0] && slot->exec_stderr_eof == eof[1]);
    assert(slot->exec_waitid_errno == wait_error && slot->exec_poll_errno == poll_failure);
    assert(slot->exec_stdout_read_errno == read_errors[0] && slot->exec_stderr_read_errno == read_errors[1]);
    assert(slot->exec_stdout_poll_revents == revents[0] && slot->exec_stderr_poll_revents == revents[1]);
    assert((slot->exec_cleanup_state == 3) == (group != NULL));
    assert(slot->exec_fallback_present == (fallback != NULL));
    if (group) {
        assert(slot->exec_group_target == group->a && slot->exec_group_signal == group->b);
        assert(slot->exec_group_rc == group->rc && slot->exec_group_errno == group->error);
    }
    if (fallback) {
        assert(slot->exec_fallback_target == fallback->a && slot->exec_fallback_signal == fallback->b);
        assert(slot->exec_fallback_rc == fallback->rc && slot->exec_fallback_errno == fallback->error);
    }
    assert(wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error);
    assert(slot->exec_reap_status == (wait->status_present ? wait->status : 0));
    if (wait->status_present) {
        assert(slot->exec_reap_stop == 1);
        assert(slot->child_exit_code == (WIFEXITED(wait->status) ? WEXITSTATUS(wait->status) : -1));
        assert(slot->child_term_signal == (WIFSIGNALED(wait->status) ? WTERMSIG(wait->status) : 0));
    } else assert(slot->child_exit_code == -1 && slot->child_term_signal == 0);
#else
    (void)slot;
#endif
}
static void emit_ledger(void) {
    printf("{\"case\":\"%s\",\"attempt\":%u,\"calls\":[", case_name, attempt_number++);
    for (size_t i = 0; i < ledger_n; i++) {
        const call_record_t *c = &ledger[i];
        printf("%s[\"%s\",%lld,%lld,%lld,%d,%d,%d,%llu]", i ? "," : "", c->call,
               (long long)c->a, (long long)c->b, (long long)c->rc, c->error,
               c->status_present, c->status, (unsigned long long)c->counter);
    }
    puts("]}");
}
static void facts(const pw_shm_slot_t *s, uint32_t stop, uint32_t cleanup, uint32_t reap) {
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(s->exec_collection_stop == stop && s->exec_cleanup_state == cleanup && s->exec_reap_stop == reap);
#else
    (void)s; (void)stop; (void)cleanup; (void)reap;
#endif
}
static pw_shm_slot_t attempt(long child_limit, uint32_t index) {
    pw_shm_slot_t slot = {0};
    strcpy(slot.target, "/controlled");
    timing.child_ms = child_limit;
    timing.child_ticks = ticks(child_limit);
    attempt_exec_spawn(&slot, &timing, 0, index);
    assert(slot.child_pid == (spawn_count && !spawn_error ? 12345 : 0));
    verify_ledger(&slot);
    emit_ledger();
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
    reset(); start(1000); failed_phase = PW_CLOCK_EXEC_OBSERVE; kill_error = fallback_error = EPERM;
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
    reset(); start(1000); kill_error = fallback_error = EPERM;
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
    /* Independent branch expectations. Numeric codes deliberately do not use
     * producer enum constants: a changed encoding must fail the contract. */
    reset(); start(40); case_name = "ordinary"; eof_ms = child_exit_ms = 0;
    slot = attempt(100, 0); facts(&slot, 1, 1, 1);
    assert(!group_kills && !leader_kills && slot.rc == 0);

    reset(); start(40); case_name = "eof_live_leader"; eof_ms = 0;
    slot = attempt(100, 0); facts(&slot, 2, 3, 1);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(slot.exec_leader_exit_observed == 0 && slot.exec_stdout_eof == 1 && slot.exec_stderr_eof == 1);
    assert(slot.exec_deadline_kind == 2);
#endif
    reset(); start(40); case_name = "exited_leader_open_stream"; child_exit_ms = 0;
    slot = attempt(100, 0); facts(&slot, 2, 3, 1);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(slot.exec_leader_exit_observed == 1 && !slot.exec_stdout_eof && !slot.exec_stderr_eof);
#endif
    reset(); start(100); case_name = "child_deadline";
    slot = attempt(20, 0); facts(&slot, 2, 3, 1);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(slot.exec_deadline_kind == 1);
#endif
    reset(); start(40); case_name = "exit_between_collection_and_reap"; child_exit_ms = 40;
    slot = attempt(100, 0); facts(&slot, 2, 3, 1);
    assert(slot.child_exit_code == 0 && slot.rc == -1);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(!slot.exec_leader_exit_observed && !slot.exec_stdout_eof && !slot.exec_stderr_eof);
#endif
    reset(); start(40); case_name = "group_esrch"; child_exit_ms = 0; kill_error = ESRCH;
    slot = attempt(100, 0); facts(&slot, 2, 3, 1);
    assert(group_kills == 1 && !leader_kills && slot.child_exit_code == 0 && slot.errno_val == 0);
    reset(); start(40); case_name = "group_failure_fallback_success_clean_leader";
    child_exit_ms = 0; kill_error = EPERM;
    slot = attempt(100, 0); facts(&slot, 2, 3, 1);
    assert(group_kills == 1 && leader_kills == 1 && slot.child_exit_code == 0 && slot.errno_val == EPERM);
    reset(); start(40); case_name = "group_failure_fallback_failure_clean_leader";
    child_exit_ms = 0; kill_error = EPERM; fallback_error = EACCES;
    slot = attempt(100, 0); facts(&slot, 2, 3, 1);
    assert(slot.child_exit_code == 0 && slot.errno_val == EPERM);
    reset(); start(40); case_name = "group_failure_pending_reap";
    kill_error = EPERM; fallback_error = EACCES;
    slot = attempt(100, 0); facts(&slot, 2, 3, 4);
    assert(!reaped_count && slot.errno_val == EPERM);
    reset(); start(40); case_name = "ownership_unconfirmed";
    waitid_error = ECHILD; wait_pending = 1;
    slot = attempt(100, 0); facts(&slot, 3, 2, 3);
    assert(!group_kills && !leader_kills && slot.errno_val == ECHILD);
    reset(); start(40); case_name = "signal_success_pending_reap"; wait_pending = 1;
    slot = attempt(100, 0); facts(&slot, 2, 3, 6);
    assert(group_kills == 1 && !reaped_count && slot.errno_val == ETIMEDOUT);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(slot.exec_reap_wait_rc == 0 && slot.exec_reap_wait_errno == 0);
#endif
    int wait_errors[] = {EIO, ETIMEDOUT, EINTR};
    const char *wait_names[] = {"native_wait_error", "native_wait_etimedout", "final_eintr_local_deadline"};
    for (int i = 0; i < 3; i++) {
        reset(); start(40); case_name = wait_names[i]; waitpid_error = wait_errors[i];
        slot = attempt(100, 0); facts(&slot, 2, 3, i == 2 ? 6 : 2);
        assert(!reaped_count && slot.errno_val == (i == 2 ? ETIMEDOUT : wait_errors[i]));
    }
    reset(); start(40); case_name = "reap_clock_fault_with_status";
    eof_ms = child_exit_ms = 0; failed_phase = PW_CLOCK_EXEC_REAP;
    slot = attempt(100, 0); facts(&slot, 1, 1, 1);
    assert(slot.rc == -1 && slot.errno_val == 0 && slot.child_exit_code == 0);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(slot.exec_reap_clock_fault == PW_TIME_REASON_BACKWARDS_COUNTER);
#endif
    reset(); start(40); case_name = "reap_clock_fault_pending";
    failed_phase = PW_CLOCK_EXEC_REAP; wait_pending = 1;
    slot = attempt(100, 0); facts(&slot, 2, 3, 5);
    reset(); start(40); case_name = "reap_clock_fault_native_error";
    failed_phase = PW_CLOCK_EXEC_REAP; waitpid_error = EIO;
    slot = attempt(100, 0); facts(&slot, 2, 3, 2);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(slot.exec_reap_clock_fault == PW_TIME_REASON_BACKWARDS_COUNTER && slot.exec_reap_wait_errno == EIO);
#endif
    reset(); start(40); case_name = "collection_clock_fault"; failed_phase = PW_CLOCK_EXEC_OBSERVE;
    slot = attempt(100, 0); facts(&slot, 4, 3, 1);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(slot.exec_collection_clock_fault == PW_TIME_REASON_BACKWARDS_COUNTER && !slot.exec_deadline_kind);
#endif
    reset(); tb_numer = 1; tb_denom = 150000000; start(115000); now_ms = 114999;
    case_name = "collection_arithmetic_fault";
    slot = attempt(10000, 0); facts(&slot, 4, 3, 1);
#ifndef PW_EXEC_LEDGER_BASELINE
    assert(slot.exec_collection_clock_fault == PW_TIME_REASON_DEADLINE_OVERFLOW);
#endif
    reset(); start(40); case_name = "terminal_poll_error"; poll_error = ENOMEM;
    slot = attempt(100, 0); facts(&slot, 3, 3, 1);
    assert(slot.errno_val == ENOMEM);
    reset(); start(40); case_name = "both_stream_reads_fail";
    eof_ms = 0; stream_errors[0] = EIO; stream_errors[1] = ENXIO;
    slot = attempt(100, 0); facts(&slot, 3, 3, 1);
    assert(slot.errno_val == ENXIO); /* the existing aggregate selects the second stream */
    reset(); start(40); case_name = "both_stream_revents_fail"; eof_ms = 0;
    stream_revents[0] = POLLERR | POLLNVAL; stream_revents[1] = POLLNVAL;
    slot = attempt(100, 0); facts(&slot, 3, 3, 1);
    assert(slot.errno_val == EIO);
    reset(); start(40); case_name = "read_and_revents_fail"; eof_ms = 0;
    stream_errors[0] = ENXIO; stream_revents[1] = POLLERR;
    slot = attempt(100, 0); facts(&slot, 3, 3, 1);
    assert(slot.errno_val == EIO);
    reset(); start(40); case_name = "read_priority_over_error_revents"; eof_ms = child_exit_ms = 0;
    stream_revents[0] = POLLIN | POLLERR; stream_revents[1] = POLLHUP | POLLNVAL;
    slot = attempt(100, 0); facts(&slot, 1, 1, 1);
    assert(slot.rc == 0);
    reset(); start(40); case_name = "recovered_interruptions"; eof_ms = child_exit_ms = 0;
    waitid_interrupts = poll_interrupts = waitpid_interrupts = 2;
    stream_retries[0] = stream_retries[1] = 1;
    slot = attempt(100, 0); facts(&slot, 1, 1, 1);
    assert(slot.rc == 0);
    reset(); start(40); case_name = "spawn_failure"; spawn_error = ENOENT;
    slot = attempt(100, 0);
    assert(!slot.child_pid && slot.errno_val == ENOENT && !group_kills && !reaped_count);
    puts("ok: independent call ledger; collection, signal requests and reap facts; preserved timing and aggregate precedence");
    return 0;
}

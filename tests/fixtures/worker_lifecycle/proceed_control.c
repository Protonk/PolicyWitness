/* The production proceed wait with a controlled continuous counter and the
 * test-only gates after its time decision and cancellation load. Each mode
 * forks a fresh child that waits on real shared-memory atomics, then publishes
 * action start, performs a real /etc/hosts open under ordinary authority and
 * publishes completion. The parent observes acknowledgement, action start and
 * the native result independently. No sandbox, host or validator is involved;
 * these are boundary observations, not policy or query-order claims. */
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <mach/mach_time.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static kern_return_t controlled_timebase(mach_timebase_info_t info);
static uint64_t controlled_read(int stage);
static void decided_gate(uint32_t phase);
static void cancel_gate(uint32_t phase);
#define PW_TIMEBASE_INFO controlled_timebase
#define PW_CONTINUOUS_READ controlled_read
#define PW_PROCEED_DECIDED decided_gate
#define PW_PROCEED_CANCEL_LOADED cancel_gate
#define main worker_main
#include "pw_probe_runner.c"
#undef main

#define PHASES 8
/* Child-written receipts, shared with the parent. */
typedef struct {
    uint32_t reads[PHASES][6];
    uint32_t returned[PHASES], action_started[PHASES], action_completed[PHASES];
    int32_t action_rc[PHASES];
    uint64_t plan_before[PHASES], plan_after[PHASES];
} receipts_t;

static pw_shm_header_t *control;
static receipts_t *rx;
static int mode, active_phase;
static uint64_t cur, phase_start;
static uint32_t gate_calls;

static kern_return_t controlled_timebase(mach_timebase_info_t info) {
    info->numer = 125; info->denom = 3; errno = EPERM; return KERN_SUCCESS;
}
static void release(uint32_t ordinal) {
    atomic_store_explicit(&control->proceed, ordinal, memory_order_release);
}
static void cancel(void) {
    atomic_store_explicit(&control->exit_requested, 1u, memory_order_release);
}
static void pause_ms(long ms) {
    struct timespec delay = {.tv_sec = 0, .tv_nsec = ms * 1000000L};
    nanosleep(&delay, NULL);
}
/* At 125/3 the 1 ms allowance is 24000 ticks. Control stores happen inside
 * the read, before the sample is returned to the wait. */
static uint64_t observe(uint32_t observation) {
    uint32_t current = (uint32_t)active_phase + 1u;
    switch (mode) {
    case 1: return 1;                                         /* below the origin */
    case 2: release(current); return phase_start + 24000;     /* exact edge */
    case 3: release(current); return phase_start + 23999;     /* one tick below */
    case 4: release(current); cancel(); return phase_start + 23999;
    case 5: release(current); cancel(); return phase_start + 24000;
    case 6: { uint64_t v = phase_start + 23999; pause_ms(10); release(current); return v; }
    case 7: release(2); cancel(); return phase_start + 23999;
    case 8:
        /* Phase 2 first sees the stale phase-1 ordinal, then its own. */
        if (active_phase == 1 && observation == 1) return phase_start + 1;
        release(current); return phase_start + 2;
    case 9: return phase_start - 1;                           /* above the origin, below the last */
    case 10: release(current); return phase_start + 1;        /* one fractional-ns tick per phase */
    case 12: release(current); return phase_start + 23999;
    case 13: return phase_start + 23999;                      /* release arrives at the gate */
    case 14: return phase_start + 24005;                      /* release stored before the sample */
    case 15: case 16: release(current); return phase_start + 23999;
    default: release(current); return phase_start + 1;
    }
}
static uint64_t controlled_read(int stage) {
    errno = EPERM;
    if (stage == PW_CLOCK_WORKER_START) return cur = 1000000;
    rx->reads[active_phase][stage]++;
    if (stage == PW_CLOCK_PROCEED_START) {
        if (mode == 0) { release(1); return 1; }
        if (mode == 14) release(1);
        return phase_start = cur += 100;
    }
    uint64_t value = observe(rx->reads[active_phase][stage]);
    if (value > cur) cur = value;
    return value;
}
static void decided_gate(uint32_t phase) {
    (void)phase;
    gate_calls++;
    if (mode == 13 && gate_calls == 1) {
        /* Held beyond the allowance after a pre-expiry decision. */
        cur += 1000000000ull; pause_ms(20); release(1);
    }
    if (mode == 16) cancel();
}
static void cancel_gate(uint32_t phase) {
    (void)phase;
    if (mode == 15) cancel();  /* stored after the load: too late for this decision */
}

static void child(pw_shm_evidence_t *e, pw_shm_slot_t *slots) {
    pw_timing_t timing = {.proceed_ms = 1, .budget_ms = 115000, .child_ms = 10000};
    pw_clock_start(&timing.clock);
    if (pw_timing_setup(&timing, e) != 0) _exit(70);
    if (mode == 11) timing.clock.fault = (pw_clock_fault_t){PW_TIME_REASON_BACKWARDS_COUNTER, PW_CLOCK_EXEC_OBSERVE, 0, 2};
    if (mode == 12) timing.plan_deadline = UINT64_MAX - 10;
    for (active_phase = 0; active_phase < (int)control->phase_count; active_phase++) {
        rx->plan_before[active_phase] = timing.plan_deadline;
        wait_for_proceed(control, e, (uint32_t)active_phase, &timing);
        rx->plan_after[active_phase] = timing.plan_deadline;
        rx->returned[active_phase] = 1;
        pw_progress(e, PW_OP_ATTEMPT, PW_PROGRESS_STARTED, (uint32_t)active_phase);
        rx->action_started[active_phase] = 1;
        int fd = open("/etc/hosts", O_RDONLY);
        rx->action_rc[active_phase] = fd < 0 ? -errno : 0;
        if (fd >= 0) close(fd);
        atomic_store_explicit(&slots[active_phase].completed, 1u, memory_order_release);
        rx->action_completed[active_phase] = 1;
        atomic_store_explicit(&control->phases[active_phase].completed, 1u, memory_order_release);
    }
    _exit(0);
}

typedef struct { int status; uint32_t failure, op, code, detail, index, kind, errno_present, done; } outcome_t;

static outcome_t run(int selected, unsigned phases, void *memory, pw_shm_evidence_t *e) {
    memset(memory, 0, PW_SHM_REGION_BYTES);
    memset(rx, 0, sizeof(*rx));
    control = memory;
    mode = selected; gate_calls = 0;
    control->phase_count = phases;
    for (unsigned i = 0; i < phases; i++) { control->phases[i].first_slot = i; control->phases[i].end_slot = i + 1; }
    if (mode == 1 || mode == 9) release(1);
    pw_shm_slot_t *slots = (void *)((char *)memory + PW_SHM_HEADER_BYTES);
    pid_t pid = fork();
    assert(pid >= 0);
    if (!pid) child(e, slots);
    int status = 0;
    pid_t reaped = 0;
    for (int i = 0; i < 5000 && reaped == 0; i++) {
        reaped = waitpid(pid, &status, WNOHANG);
        if (!reaped && atomic_load_explicit(&control->done, memory_order_acquire)) cancel();
        if (!reaped) usleep(1000);
    }
    if (!reaped) { kill(pid, SIGKILL); waitpid(pid, &status, 0); fprintf(stderr, "mode %d hung\n", mode); assert(0); }
    outcome_t o = {status, atomic_load(&e->failure_published), e->operation, e->code, e->detail,
                   e->item_index, e->native_kind, e->errno_present, atomic_load(&control->done)};
    printf("{\"mode\":%d,\"status\":%d,\"failure\":%u,\"operation\":%u,\"code\":%u,\"detail\":%u,"
           "\"done\":%u,\"ack\":[%u,%u],\"action_started\":[%u,%u],\"action_rc\":[%d,%d],"
           "\"observe_reads\":[%u,%u],\"exclusion\":[%llu,%llu]}\n",
           mode, status, o.failure, o.op, o.code, o.detail, o.done,
           atomic_load(&control->phases[0].acknowledged), atomic_load(&control->phases[1].acknowledged),
           rx->action_started[0], rx->action_started[1], rx->action_rc[0], rx->action_rc[1],
           rx->reads[0][PW_CLOCK_PROCEED_OBSERVE], rx->reads[1][PW_CLOCK_PROCEED_OBSERVE],
           rx->returned[0] ? (unsigned long long)(rx->plan_after[0] - rx->plan_before[0]) : 0ull,
           rx->returned[1] ? (unsigned long long)(rx->plan_after[1] - rx->plan_before[1]) : 0ull);
    return o;
}
static int acked(unsigned phase) { return (int)atomic_load(&control->phases[phase].acknowledged); }
/* Refused before acknowledgement: no action start, no native action. */
static void refused(const outcome_t *o, uint32_t code, uint32_t detail) {
    assert(WIFEXITED(o->status) && WEXITSTATUS(o->status) == 0 && o->done);
    assert(o->failure == 1 && o->op == PW_OP_PROCEED && o->code == code && o->detail == detail);
    assert(o->index == 0 && o->kind == PW_NATIVE_NONE && o->errno_present == 0);
    assert(!acked(0) && !rx->returned[0] && !rx->action_started[0] && !rx->action_completed[0]);
    assert(atomic_load(&control->proceed_observed) == 0);
}
static void completed(const outcome_t *o, unsigned phases) {
    assert(WIFEXITED(o->status) && WEXITSTATUS(o->status) == 0 && o->failure == 0 && !o->done);
    for (unsigned i = 0; i < phases; i++)
        assert(acked(i) && rx->action_started[i] && rx->action_completed[i] && rx->action_rc[i] == 0);
}

int main(void) {
    void *memory = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    rx = mmap(NULL, sizeof(*rx), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    assert(memory != MAP_FAILED && rx != MAP_FAILED);
    pw_shm_evidence_t *e = pw_evidence(memory);
    outcome_t o;

    /* Unusable start or observation with release already visible: a local
     * refusal (no native result or errno) before acknowledgement. */
    o = run(0, 1, memory, e); refused(&o, PW_FAILURE_TIME_INVALID, PW_TIME_REASON_BACKWARDS_COUNTER);
    assert(rx->reads[0][PW_CLOCK_PROCEED_OBSERVE] == 0);
    o = run(1, 1, memory, e); refused(&o, PW_FAILURE_TIME_INVALID, PW_TIME_REASON_BACKWARDS_COUNTER);
    /* The exact edge expires even with release made visible; one tick below acknowledges. */
    o = run(2, 1, memory, e); refused(&o, PW_FAILURE_PROCEED_TIMEOUT, 1);
    o = run(3, 1, memory, e); completed(&o, 1);
    assert(rx->plan_after[0] - rx->plan_before[0] == 23999);
    /* Cancellation observed by its load wins without a fabricated clock failure. */
    o = run(4, 1, memory, e);
    assert(WIFEXITED(o.status) && WEXITSTATUS(o.status) == 0 && o.failure == 0 && !o.done);
    assert(!acked(0) && !rx->action_started[0]);
    /* An expired sample precedes cancellation handling. */
    o = run(5, 1, memory, e); refused(&o, PW_FAILURE_PROCEED_TIMEOUT, 1);
    /* A delay after a pre-expiry sample still acknowledges; the exclusion is
     * the sampled interval, not the delay. */
    o = run(6, 1, memory, e); completed(&o, 1);
    assert(rx->plan_after[0] - rx->plan_before[0] == 23999);
    /* A future release fails before cancellation is consulted. */
    o = run(7, 1, memory, e); refused(&o, PW_FAILURE_PHASE_RELEASE, 2);
    /* A stale phase-1 release cannot release phase 2; repeated polls exclude once. */
    o = run(8, 2, memory, e); completed(&o, 2);
    assert(rx->reads[1][PW_CLOCK_PROCEED_OBSERVE] == 2 && rx->plan_after[1] - rx->plan_before[1] == 2);
    /* A successful but backwards sample now fails closed instead of excluding
     * a negative interval. */
    o = run(9, 1, memory, e); refused(&o, PW_FAILURE_TIME_INVALID, PW_TIME_REASON_BACKWARDS_COUNTER);
    /* Fractional-nanosecond waits extend the plan by their exact tick sum once. */
    o = run(10, 3, memory, e); completed(&o, 3);
    uint64_t total = 0;
    for (int i = 0; i < 3; i++) total += rx->plan_after[i] - rx->plan_before[i];
    assert(total == 3 && total * 125 / 3 == 125);
    /* An earlier rejected exec sample refuses without another read, naming its origin. */
    o = run(11, 1, memory, e); refused(&o, PW_FAILURE_TIME_INVALID, PW_TIME_REASON_PRIOR_CLOCK_FAULT);
    assert(rx->reads[0][PW_CLOCK_PROCEED_START] == 0 && rx->reads[0][PW_CLOCK_PROCEED_OBSERVE] == 0);
    char *text = (char *)e + PW_SHM_EVIDENCE_HEADER_BYTES;
    assert(strstr(text, "first rejected sample: reason=backwards_counter stage=exec_observe phase=0 slot=2"));
    /* An unrepresentable exclusion refuses before acknowledgement. */
    o = run(12, 1, memory, e); refused(&o, PW_FAILURE_TIME_INVALID, PW_TIME_REASON_DEADLINE_OVERFLOW);

    /* Scheduled races. A pre-expiry decision held beyond the allowance can
     * still acknowledge; the complement expires when the sample is late. */
    o = run(13, 1, memory, e); completed(&o, 1);
    assert(rx->reads[0][PW_CLOCK_PROCEED_OBSERVE] == 1);
    o = run(14, 1, memory, e); refused(&o, PW_FAILURE_PROCEED_TIMEOUT, 1);
    /* Cancellation stored after its load is too late for that decision;
     * stored before the load, it wins. */
    o = run(15, 1, memory, e); completed(&o, 1);
    assert(atomic_load(&control->exit_requested) == 1);
    o = run(16, 1, memory, e);
    assert(WIFEXITED(o.status) && WEXITSTATUS(o.status) == 0 && o.failure == 0 && !acked(0) && !rx->action_started[0]);

    puts("ok: proceed precedence, fail-closed samples, exact exclusions and scheduled race limits");
    return 0;
}

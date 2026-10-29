#ifndef PW_WORKER_TIMING_H
#define PW_WORKER_TIMING_H

/* Private timing implementation for the worker's single translation unit.
 * Main owns the timing instance and calls origin/setup at their visible sites.
 * Sampling alone mutates clock history and its sticky fault. Phase waiting
 * commits a checked plan-deadline exclusion immediately before acknowledgement;
 * exec only reads that deadline. No resource is acquired by inclusion. */
#include <mach/mach_time.h>
#include <stdint.h>
#include <stdio.h>
#include "pw_worker_evidence.h"

/*
 * Bounded child deadline for exec attempts. The worker enforces a
 * per-attempt wall-clock cap so a hung helper can't escalate into
 * the host's worker-level sentinel timeout (which would also lose
 * the per-step error attribution). When the deadline fires the
 * worker SIGKILLs the child's process group and records
 * "child exceeded N ms deadline" as the slot error. The cap protects
 * one step; the exec attempt budget below protects the plan, because
 * a plan may hold 256 exec steps and each could spend a full deadline.
 * Overridable per-run via the `--exec-child-deadline-ms` test seam. */
#define PW_EXEC_CHILD_DEADLINE_MS_DEFAULT 10000L
#define PW_EXEC_CHILD_DEADLINE_MS_MAX     60000L

/* Local active-time budget in continuous ticks, including system sleep: it
 * starts at the worker origin before setup and excludes only each phase's
 * acknowledged release wait. It does not reconstruct the host's polling clock. The production default leaves room for cleanup/publication
 * inside the nominal host window; blocking native calls and host scheduling
 * are not made preemptible by this allowance. */
#define PW_WORKER_WINDOW_MS               120000L
#define PW_EXEC_ATTEMPT_BUDGET_MARGIN_MS  5000L
#define PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT (PW_WORKER_WINDOW_MS - PW_EXEC_ATTEMPT_BUDGET_MARGIN_MS)
#define PW_EXEC_REAP_GRACE_MS              1000L

/* Semantic clock stages. Compile-time seams select a raw value or fault by
 * stage, never by the ordinal of a clock call. No request can select one. */
enum pw_clock_phase {
    PW_CLOCK_WORKER_START, PW_CLOCK_PROCEED_START, PW_CLOCK_PROCEED_OBSERVE,
    PW_CLOCK_EXEC_ADMIT, PW_CLOCK_EXEC_OBSERVE, PW_CLOCK_EXEC_REAP
};

/* Continuous Mach time in relative ticks. It advances during system sleep
 * and avoids the libc CLOCK_MONOTONIC path, whose gettimeofday fallback a
 * deny-default profile refused. It has no native error return, so samples are
 * validated instead. Native controls exercise it under deny-default profiles
 * on the recorded Apple Silicon configuration; an implementation may read a
 * user-space counter or enter the kernel, and this comment promises neither.
 * Compile-time seams select a raw value or timebase result by semantic stage;
 * no request selects one. */
#ifndef PW_TIMEBASE_INFO
#define PW_TIMEBASE_INFO(info) mach_timebase_info(info)
#endif
#ifndef PW_CONTINUOUS_READ
#define PW_CONTINUOUS_READ(phase) ((void)(phase), mach_continuous_time())
#endif

#define PW_CLOCK_NO_SCOPE UINT32_MAX

/* The first rejected raw sample (the sticky clock fault). Only sample
 * validation writes it; reason 0 means no sample has been rejected. */
typedef struct {
    uint32_t reason, stage, phase, slot;
} pw_clock_fault_t;

typedef struct {
    uint32_t numer, denom;
    uint64_t origin, last;
    pw_clock_fault_t fault;
} pw_clock_t;

/* Worker timing in one tick domain: the plan cutoff is the exec allowance
 * plus committed release exclusions, all relative to the worker origin. */
typedef struct {
    pw_clock_t clock;
    uint64_t proceed_ticks, budget_ticks, child_ticks, reap_ticks;
    uint64_t plan_deadline;
    long proceed_ms, budget_ms, child_ms;
} pw_timing_t;

static const char *const pw_clock_stage_names[] = {
    "worker_start", "proceed_start", "proceed_observe", "exec_admit", "exec_observe", "exec_reap"
};
static const char *const pw_time_reason_names[] = {
    "none", "invalid_timebase", "invalid_duration", "backwards_counter",
    "unrepresentable_delta", "deadline_overflow", "prior_clock_fault"
};

static void pw_clock_start(pw_clock_t *clock) {
    clock->origin = clock->last = PW_CONTINUOUS_READ(PW_CLOCK_WORKER_START);
}

/* A usable sample is at least the origin and the last accepted sample;
 * equality and zero are valid. A rejection is recorded once, with its
 * scope, and every later sample is refused without another read. */
static uint32_t pw_clock_sample(pw_clock_t *clock, enum pw_clock_phase stage,
                                uint32_t phase, uint32_t slot, uint64_t *elapsed) {
    if (clock->fault.reason) return PW_TIME_REASON_PRIOR_CLOCK_FAULT;
    uint64_t raw = PW_CONTINUOUS_READ(stage);
    if (raw < clock->origin || raw < clock->last) {
        clock->fault = (pw_clock_fault_t){PW_TIME_REASON_BACKWARDS_COUNTER, (uint32_t)stage, phase, slot};
        return PW_TIME_REASON_BACKWARDS_COUNTER;
    }
    clock->last = raw;
    *elapsed = raw - clock->origin;
    return 0;
}

/* Ceiling allowance: at `ticks` the duration has expired, at `ticks - 1` it
 * has not. Nothing saturates; an unrepresentable allowance is refused. */
static uint32_t pw_ticks_for_ms(const pw_clock_t *clock, long ms, uint64_t *ticks) {
    if (!clock->numer || !clock->denom) return PW_TIME_REASON_INVALID_TIMEBASE;
    if (ms <= 0 || (unsigned long)ms > UINT64_MAX / 1000000u) return PW_TIME_REASON_INVALID_DURATION;
    __uint128_t product = (__uint128_t)((uint64_t)ms * 1000000u) * clock->denom;
    __uint128_t whole = product / clock->numer + (product % clock->numer != 0);
    if (whole > UINT64_MAX) return PW_TIME_REASON_INVALID_DURATION;
    *ticks = (uint64_t)whole;
    return 0;
}

/* Ceiling milliseconds for a bounded tick delta. Callers cap the result
 * before narrowing it to a poll timeout. */
static uint32_t pw_ms_for_ticks(const pw_clock_t *clock, uint64_t ticks, uint64_t *ms) {
    __uint128_t scaled = (__uint128_t)ticks * clock->numer;
    __uint128_t divisor = (__uint128_t)clock->denom * 1000000u;
    __uint128_t whole = scaled / divisor + (scaled % divisor != 0);
    if (whole > UINT64_MAX) return PW_TIME_REASON_UNREPRESENTABLE_DELTA;
    *ms = (uint64_t)whole;
    return 0;
}

static uint32_t pw_ticks_add(uint64_t a, uint64_t b, uint64_t *sum) {
    uint64_t result;
    if (__builtin_add_overflow(a, b, &result)) return PW_TIME_REASON_DEADLINE_OVERFLOW;
    *sum = result;
    return 0;
}

/* Bounded text assembly without allocation or libc formatting, usable after
 * application for evidence diagnostics. */
typedef struct { char *text; size_t used, capacity; } pw_text_t;

static void pw_text_add(pw_text_t *out, const char *text) {
    while (*text && out->used + 1 < out->capacity) out->text[out->used++] = *text++;
    out->text[out->used] = 0;
}

static void pw_text_add_u32(pw_text_t *out, uint32_t value) {
    char digits[11];
    int count = 0;
    do { digits[count++] = (char)('0' + value % 10u); value /= 10u; } while (value);
    while (count) { char one[2] = {digits[--count], 0}; pw_text_add(out, one); }
}

static void pw_text_add_scope(pw_text_t *out, const char *name, uint32_t value) {
    pw_text_add(out, name);
    if (value == PW_CLOCK_NO_SCOPE) pw_text_add(out, "none");
    else pw_text_add_u32(out, value);
}

static const char *pw_time_reason_name(uint32_t reason) {
    return reason < sizeof(pw_time_reason_names) / sizeof(*pw_time_reason_names)
        ? pw_time_reason_names[reason] : "unknown";
}

static const char *pw_clock_stage_name(uint32_t stage) {
    return stage < sizeof(pw_clock_stage_names) / sizeof(*pw_clock_stage_names)
        ? pw_clock_stage_names[stage] : "unknown";
}

/* "reason=backwards_counter stage=exec_observe phase=0 slot=2" */
static void pw_text_add_fault(pw_text_t *out, const pw_clock_fault_t *fault) {
    pw_text_add(out, "reason=");
    pw_text_add(out, pw_time_reason_name(fault->reason));
    pw_text_add(out, " stage=");
    pw_text_add(out, pw_clock_stage_name(fault->stage));
    pw_text_add_scope(out, " phase=", fault->phase);
    pw_text_add_scope(out, " slot=", fault->slot);
}

/* "local_timing=<reason> stage=<stage>", plus the first rejected sample when
 * the refusal is or follows one. Arithmetic refusals name only themselves. */
static void pw_text_add_local(pw_text_t *out, uint32_t reason, enum pw_clock_phase stage,
                              const pw_clock_fault_t *first) {
    pw_text_add(out, "local_timing=");
    pw_text_add(out, pw_time_reason_name(reason));
    pw_text_add(out, " stage=");
    pw_text_add(out, pw_clock_stage_name((uint32_t)stage));
    if (first->reason) {
        pw_text_add(out, " (first rejected sample: ");
        pw_text_add_fault(out, first);
        pw_text_add(out, ")");
    }
}

/* Pre-apply setup: one timebase query, then every configured allowance. It
 * obtains conversion metadata only; nothing here is retained for an attempt. */
static int pw_timing_setup(pw_timing_t *timing, pw_shm_evidence_t *e) {
    mach_timebase_info_data_t info = {0, 0};
    pw_progress(e, PW_OP_CLOCK_SETUP, PW_PROGRESS_STARTED, UINT32_MAX);
    kern_return_t kr = PW_TIMEBASE_INFO(&info);
    pw_progress(e, PW_OP_CLOCK_SETUP, PW_PROGRESS_RETURNED, UINT32_MAX);
    if (kr != KERN_SUCCESS) {
        pw_failure(e, PW_OP_CLOCK_SETUP, PW_FAILURE_NATIVE, PW_NATIVE_INTEGER, kr, 0, 0, UINT32_MAX, 0);
        pw_diagnostic(e, "clock setup: mach_timebase_info failed");
        fprintf(stderr, "pw-probe-runner: mach_timebase_info returned %d\n", kr);
        return -1;
    }
    timing->clock.numer = info.numer;
    timing->clock.denom = info.denom;
    uint32_t reason = pw_ticks_for_ms(&timing->clock, timing->proceed_ms, &timing->proceed_ticks);
    if (!reason) reason = pw_ticks_for_ms(&timing->clock, timing->budget_ms, &timing->budget_ticks);
    if (!reason) reason = pw_ticks_for_ms(&timing->clock, timing->child_ms, &timing->child_ticks);
    if (!reason) reason = pw_ticks_for_ms(&timing->clock, PW_EXEC_REAP_GRACE_MS, &timing->reap_ticks);
    if (reason) {
        pw_failure(e, PW_OP_CLOCK_SETUP, PW_FAILURE_TIME_INVALID, PW_NATIVE_NONE, 0, 0, 0, UINT32_MAX, reason);
        pw_diagnostic(e, reason == PW_TIME_REASON_INVALID_TIMEBASE
            ? "clock setup: Mach timebase has a zero factor (reason in detail)"
            : "clock setup: a configured duration has no representable tick allowance (reason in detail)");
        fprintf(stderr, "pw-probe-runner: clock setup refused: %s (numer=%u denom=%u)\n",
                pw_time_reason_name(reason), info.numer, info.denom);
        return -1;
    }
    timing->plan_deadline = timing->budget_ticks;
    return 0;
}

/* 30s validator I/O + 1s exit grace + 5s release margin < 60s.
 * This is a worker observation deadline, not a bound on host scheduling/reap. */
#define PW_PROCEED_WAIT_MS_DEFAULT 60000L

#endif

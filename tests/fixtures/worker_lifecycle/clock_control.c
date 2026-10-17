/* Production worker clock helpers with a controlled timebase and raw counter.
 * Expected answers are literals or the defining ceiling inequality checked in
 * 128-bit multiplication, never a call back into the helper under test. No
 * sandbox, child or host is involved. */
#include <assert.h>
#include <errno.h>
#include <mach/mach_time.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>

static uint32_t tb_numer = 125, tb_denom = 3;
static kern_return_t tb_kr = KERN_SUCCESS;
static uint64_t raws[16];
static int raw_next, raw_reads;

/* Each seam leaves a stale permission errno: no timing record may report it. */
static kern_return_t controlled_timebase(mach_timebase_info_t info) {
    info->numer = tb_numer; info->denom = tb_denom; errno = EPERM; return tb_kr;
}
static uint64_t controlled_read(int stage) {
    (void)stage; raw_reads++; errno = EPERM; return raws[raw_next++];
}
#define PW_TIMEBASE_INFO controlled_timebase
#define PW_CONTINUOUS_READ controlled_read
#define main worker_main
#include "pw_probe_runner.c"
#undef main

static pw_clock_t ratio(uint32_t numer, uint32_t denom) {
    return (pw_clock_t){.numer = numer, .denom = denom};
}
/* t is the ceiling allowance exactly when t*numer >= ns*denom > (t-1)*numer. */
static void ceiling_holds(uint32_t numer, uint32_t denom, long ms) {
    pw_clock_t clock = ratio(numer, denom);
    uint64_t ticks = 0;
    assert(pw_ticks_for_ms(&clock, ms, &ticks) == 0);
    __uint128_t need = (__uint128_t)ms * 1000000u * denom;
    assert((__uint128_t)ticks * numer >= need);
    assert(ticks > 0 && (__uint128_t)(ticks - 1) * numer < need);
}
static void start_at(pw_clock_t *clock, uint64_t origin) {
    *clock = ratio(clock->numer, clock->denom);
    memset(raws, 0, sizeof(raws)); raw_next = raw_reads = 0;
    raws[0] = origin; pw_clock_start(clock);
}

int main(void) {
    uint64_t ticks = 0, ms = 0, sum = 0;
    pw_clock_t clock;

    /* Literal allowances: 125/3 is the observed Apple Silicon timebase. */
    clock = ratio(125, 3);
    assert(pw_ticks_for_ms(&clock, 1, &ticks) == 0 && ticks == 24000);
    assert(pw_ticks_for_ms(&clock, 60000, &ticks) == 0 && ticks == 1440000000ull);
    clock = ratio(1, 1);
    assert(pw_ticks_for_ms(&clock, 1, &ticks) == 0 && ticks == 1000000);
    clock = ratio(3, 125);  /* reciprocal: 1e6 * 125 / 3 rounds up */
    assert(pw_ticks_for_ms(&clock, 1, &ticks) == 0 && ticks == 41666667);
    /* A 64-bit product of 120000 ms and a 32-bit denominator overflows; the
     * allowance itself is representable and exact. */
    clock = ratio(UINT32_MAX, UINT32_MAX);
    assert(pw_ticks_for_ms(&clock, 120000, &ticks) == 0 && ticks == 120000000000ull);
    clock = ratio(UINT32_MAX - 1, UINT32_MAX);
    assert(pw_ticks_for_ms(&clock, 120000, &ticks) == 0 && ticks == 120000000028ull);
    uint32_t ratios[][2] = {{1, 1}, {125, 3}, {3, 125}, {1, UINT32_MAX}, {UINT32_MAX, 1},
                            {UINT32_MAX, UINT32_MAX - 1}, {7, 1000003}, {1000003, 7}};
    long durations[] = {1, 2, 999, 1000, 10000, 60000, 115000, 120000};
    for (size_t r = 0; r < sizeof(ratios) / sizeof(*ratios); r++)
        for (size_t d = 0; d < sizeof(durations) / sizeof(*durations); d++) {
            clock = ratio(ratios[r][0], ratios[r][1]);
            __uint128_t need = (__uint128_t)durations[d] * 1000000u * ratios[r][1];
            if (need / ratios[r][0] + 1 > UINT64_MAX) continue;  /* refused below */
            ceiling_holds(ratios[r][0], ratios[r][1], durations[d]);
        }

    /* Expiry edge: at the allowance the budget has expired; one tick below has not. */
    clock = ratio(125, 3);
    assert(pw_ticks_for_ms(&clock, 1, &ticks) == 0);
    assert((__uint128_t)ticks * 125 >= (__uint128_t)1000000 * 3);
    assert((__uint128_t)(ticks - 1) * 125 < (__uint128_t)1000000 * 3);

    /* Refusals: factors, positivity, unit multiplication and narrowing. */
    clock = ratio(0, 3);
    assert(pw_ticks_for_ms(&clock, 1, &ticks) == PW_TIME_REASON_INVALID_TIMEBASE);
    clock = ratio(125, 0);
    assert(pw_ticks_for_ms(&clock, 1, &ticks) == PW_TIME_REASON_INVALID_TIMEBASE);
    clock = ratio(125, 3);
    assert(pw_ticks_for_ms(&clock, 0, &ticks) == PW_TIME_REASON_INVALID_DURATION);
    assert(pw_ticks_for_ms(&clock, -1, &ticks) == PW_TIME_REASON_INVALID_DURATION);
    assert(pw_ticks_for_ms(&clock, (long)(UINT64_MAX / 1000000u) + 1, &ticks) == PW_TIME_REASON_INVALID_DURATION);
    clock = ratio(1, UINT32_MAX);
    assert(pw_ticks_for_ms(&clock, 60000, &ticks) == PW_TIME_REASON_INVALID_DURATION);
    ticks = 77;
    assert(pw_ticks_for_ms(&clock, 60000, &ticks) && ticks == 77);  /* nothing narrowed out */

    /* Bounded delta to milliseconds rounds up and refuses an unrepresentable result. */
    clock = ratio(125, 3);
    assert(pw_ms_for_ticks(&clock, 0, &ms) == 0 && ms == 0);
    assert(pw_ms_for_ticks(&clock, 1, &ms) == 0 && ms == 1);
    assert(pw_ms_for_ticks(&clock, 24000, &ms) == 0 && ms == 1);
    assert(pw_ms_for_ticks(&clock, 24001, &ms) == 0 && ms == 2);
    clock = ratio(UINT32_MAX, 1);
    assert(pw_ms_for_ticks(&clock, UINT64_MAX, &ms) == PW_TIME_REASON_UNREPRESENTABLE_DELTA);

    /* Checked addition never saturates. */
    assert(pw_ticks_add(UINT64_MAX - 1, 1, &sum) == 0 && sum == UINT64_MAX);
    sum = 5;
    assert(pw_ticks_add(UINT64_MAX, 1, &sum) == PW_TIME_REASON_DEADLINE_OVERFLOW && sum == 5);
    /* Three one-tick exclusions at 125/3 are 3 ticks (125 ns) together;
     * three floored 41 ns intervals would exclude only 123 ns. */
    uint64_t deadline = 24000;
    for (int i = 0; i < 3; i++) assert(pw_ticks_add(deadline, 1, &deadline) == 0);
    assert(deadline == 24003 && (deadline - 24000) * 125 / 3 == 125);

    /* Samples: equality and zero are valid; regression against the last
     * accepted sample is rejected even above the origin. */
    clock = ratio(125, 3);
    start_at(&clock, 1000);
    raws[1] = 1000; raws[2] = 5000; raws[3] = 3000; raws[4] = 9000;
    uint64_t elapsed = 99;
    assert(pw_clock_sample(&clock, PW_CLOCK_PROCEED_START, 0, PW_CLOCK_NO_SCOPE, &elapsed) == 0 && elapsed == 0);
    assert(pw_clock_sample(&clock, PW_CLOCK_EXEC_ADMIT, 1, 4, &elapsed) == 0 && elapsed == 4000);
    elapsed = 99;
    assert(pw_clock_sample(&clock, PW_CLOCK_EXEC_OBSERVE, 1, 4, &elapsed) == PW_TIME_REASON_BACKWARDS_COUNTER);
    assert(elapsed == 99 && clock.last == 5000);
    assert(clock.fault.reason == PW_TIME_REASON_BACKWARDS_COUNTER && clock.fault.stage == PW_CLOCK_EXEC_OBSERVE);
    assert(clock.fault.phase == 1 && clock.fault.slot == 4);
    /* A later forward-looking value is never read, and the origin stays. */
    assert(pw_clock_sample(&clock, PW_CLOCK_PROCEED_START, 2, PW_CLOCK_NO_SCOPE, &elapsed) == PW_TIME_REASON_PRIOR_CLOCK_FAULT);
    assert(raw_reads == 4 && clock.fault.stage == PW_CLOCK_EXEC_OBSERVE && clock.fault.phase == 1);
    start_at(&clock, 0);
    raws[1] = 0;
    assert(pw_clock_sample(&clock, PW_CLOCK_PROCEED_START, 0, PW_CLOCK_NO_SCOPE, &elapsed) == 0 && elapsed == 0);
    /* An observed wrap is a regression; nothing converts the absolute counter. */
    start_at(&clock, UINT64_MAX - 2);
    raws[1] = UINT64_MAX; raws[2] = 4;
    assert(pw_clock_sample(&clock, PW_CLOCK_EXEC_REAP, 0, 0, &elapsed) == 0 && elapsed == 2);
    assert(pw_clock_sample(&clock, PW_CLOCK_EXEC_REAP, 0, 0, &elapsed) == PW_TIME_REASON_BACKWARDS_COUNTER);
    /* A sample below the origin is rejected even before any other sample. */
    start_at(&clock, 500);
    raws[1] = 499;
    assert(pw_clock_sample(&clock, PW_CLOCK_EXEC_ADMIT, 0, 0, &elapsed) == PW_TIME_REASON_BACKWARDS_COUNTER);

    /* Setup publications through the production evidence protocol. */
    void *base = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    assert(base != MAP_FAILED);
    pw_shm_evidence_t *e = pw_evidence(base);
    struct { kern_return_t kr; uint32_t numer, denom; long budget; uint32_t code, kind, detail; int32_t result; } setups[] = {
        {KERN_INVALID_ARGUMENT, 125, 3, 115000, PW_FAILURE_NATIVE, PW_NATIVE_INTEGER, 0, KERN_INVALID_ARGUMENT},
        {KERN_SUCCESS, 0, 3, 115000, PW_FAILURE_TIME_INVALID, PW_NATIVE_NONE, PW_TIME_REASON_INVALID_TIMEBASE, 0},
        {KERN_SUCCESS, 125, 0, 115000, PW_FAILURE_TIME_INVALID, PW_NATIVE_NONE, PW_TIME_REASON_INVALID_TIMEBASE, 0},
        {KERN_SUCCESS, 1, UINT32_MAX, 115000, PW_FAILURE_TIME_INVALID, PW_NATIVE_NONE, PW_TIME_REASON_INVALID_DURATION, 0},
        {KERN_SUCCESS, 125, 3, 0, PW_FAILURE_TIME_INVALID, PW_NATIVE_NONE, PW_TIME_REASON_INVALID_DURATION, 0},
    };
    for (size_t i = 0; i < sizeof(setups) / sizeof(*setups); i++) {
        memset(base, 0, PW_SHM_REGION_BYTES);
        tb_kr = setups[i].kr; tb_numer = setups[i].numer; tb_denom = setups[i].denom;
        pw_timing_t timing = {.proceed_ms = 60000, .budget_ms = setups[i].budget, .child_ms = 10000};
        assert(pw_timing_setup(&timing, e) == -1);
        assert(atomic_load(&e->progress) == ((PW_OP_CLOCK_SETUP << 24) | (PW_PROGRESS_RETURNED << 20)));
        assert(atomic_load(&e->failure_published) == 1 && e->operation == PW_OP_CLOCK_SETUP);
        assert(e->code == setups[i].code && e->native_kind == setups[i].kind && e->native_result == setups[i].result);
        assert(e->errno_present == 0 && e->item_index == UINT32_MAX && e->detail == setups[i].detail);
        assert(atomic_load(&e->diagnostic_state) == 1);
    }
    memset(base, 0, PW_SHM_REGION_BYTES);
    tb_kr = KERN_SUCCESS; tb_numer = 125; tb_denom = 3;
    pw_timing_t timing = {.proceed_ms = 60000, .budget_ms = 115000, .child_ms = 10000};
    assert(pw_timing_setup(&timing, e) == 0 && atomic_load(&e->failure_published) == 0);
    assert(timing.proceed_ticks == 1440000000ull && timing.budget_ticks == 2760000000ull);
    assert(timing.child_ticks == 240000000ull && timing.reap_ticks == 24000000ull);
    assert(timing.plan_deadline == timing.budget_ticks);

    /* Fault text is assembled without libc formatting and names absent scope. */
    char text[96];
    pw_text_t out = {text, 0, sizeof(text)};
    pw_clock_fault_t fault = {PW_TIME_REASON_BACKWARDS_COUNTER, PW_CLOCK_EXEC_REAP, 0, PW_CLOCK_NO_SCOPE};
    pw_text_add_fault(&out, &fault);
    assert(!strcmp(text, "reason=backwards_counter stage=exec_reap phase=0 slot=none"));
    char small[8];
    out = (pw_text_t){small, 0, sizeof(small)};
    pw_text_add_fault(&out, &fault);
    assert(strlen(small) == 7);

    puts("ok: ceiling allowances, refusals, sample validation, sticky fault, setup publications");
    return 0;
}

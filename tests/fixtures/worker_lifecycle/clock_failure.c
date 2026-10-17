/* Production worker main with one clock boundary substituted at compile time.
 * Setup companions change only the timebase query; sample companions return
 * the real continuous counter except at one semantic stage and read ordinal.
 * Every seam leaves a stale permission errno that no timing record may report.
 *
 *   PW_CLOCK_SETUP_FAILURE      mach_timebase_info returns KERN_INVALID_ARGUMENT
 *   PW_CLOCK_ZERO_FACTOR        the timebase numerator is zero
 *   PW_CLOCK_UNREPRESENTABLE    1/UINT32_MAX: no 60 s allowance fits 64 bits
 *   PW_CLOCK_BACKWARDS_STAGE/READ  that read of that stage is below the origin;
 *                               PW_CLOCK_FAILURE_DELAY_MS first holds it, so a
 *                               host collection of the arrived phase begins
 *   PW_CLOCK_EXPIRE_SECOND_PHASE   200 ms of real time into phase 2's wait, its
 *                               observation jumps 2^62 ticks: a valid expiry
 *   PW_CLOCK_EXEC_NEAR_CUTOFF   1/150000000, and the first exec observation
 *                               jumps to one millisecond before the default
 *                               115 s plan cutoff, so adding the 10 s child
 *                               allowance overflows while the sample is valid
 * Jumps are forward and persist, so every later sample stays ordered. */
#include <errno.h>
#include <mach/mach_time.h>
#include <time.h>
static uint64_t pw_controlled_read(int stage);
static kern_return_t pw_controlled_timebase(mach_timebase_info_t info);
#define PW_CONTINUOUS_READ pw_controlled_read
#define PW_TIMEBASE_INFO pw_controlled_timebase
#include "pw_probe_runner.c"

static uint64_t origin_raw, offset, phase2_start;
static unsigned reads[PW_CLOCK_EXEC_REAP + 1];

static uint64_t real_ms(uint64_t ticks) {
    mach_timebase_info_data_t info;
    mach_timebase_info(&info);
    return (uint64_t)((__uint128_t)ticks * info.numer / info.denom / 1000000u);
}

static uint64_t pw_controlled_read(int stage) {
    uint64_t raw = mach_continuous_time() + offset;
    reads[stage]++;
    errno = EPERM;
    if (stage == PW_CLOCK_WORKER_START) return origin_raw = raw;
#if defined(PW_CLOCK_BACKWARDS_STAGE)
    if (stage == PW_CLOCK_BACKWARDS_STAGE && reads[stage] == PW_CLOCK_BACKWARDS_READ) {
#ifdef PW_CLOCK_FAILURE_DELAY_MS
        struct timespec delay = {.tv_sec = 0, .tv_nsec = PW_CLOCK_FAILURE_DELAY_MS * 1000000L};
        nanosleep(&delay, NULL);
        errno = EPERM;
#endif
        return origin_raw - 1;
    }
#elif defined(PW_CLOCK_EXPIRE_SECOND_PHASE)
    if (stage == PW_CLOCK_PROCEED_START && reads[stage] == 2) phase2_start = raw;
    if (stage == PW_CLOCK_PROCEED_OBSERVE && phase2_start && !offset && real_ms(raw - phase2_start) >= 200) {
        offset = 1ull << 62;
        return raw + offset;
    }
#elif defined(PW_CLOCK_EXEC_NEAR_CUTOFF)
    if (stage == PW_CLOCK_EXEC_OBSERVE && !offset) {
        /* 115000 ms less 1 ms, at 150000000 ticks per nanosecond. */
        const uint64_t elapsed = 17250000000000000000ull - 150000000000000ull;
        offset = origin_raw + elapsed - raw;
        return raw + offset;
    }
#endif
    return raw;
}

static kern_return_t pw_controlled_timebase(mach_timebase_info_t info) {
    kern_return_t kr = mach_timebase_info(info);
#if defined(PW_CLOCK_SETUP_FAILURE)
    kr = KERN_INVALID_ARGUMENT;
#elif defined(PW_CLOCK_ZERO_FACTOR)
    info->numer = 0;
#elif defined(PW_CLOCK_UNREPRESENTABLE)
    info->numer = 1; info->denom = UINT32_MAX;
#elif defined(PW_CLOCK_EXEC_NEAR_CUTOFF)
    info->numer = 1; info->denom = 150000000;
#endif
    errno = EPERM;
    return kr;
}

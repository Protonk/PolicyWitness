/* Production worker main with one clock boundary substituted at compile time.
 * Setup companions change only the timebase query; sample companions return
 * the real continuous counter except at one semantic stage and read ordinal.
 * Every seam leaves a stale permission errno that no timing record may report.
 *
 *   PW_CLOCK_SETUP_FAILURE      mach_timebase_info returns KERN_INVALID_ARGUMENT
 *   PW_CLOCK_ZERO_FACTOR        the timebase numerator is zero
 *   PW_CLOCK_UNREPRESENTABLE    1/UINT32_MAX: no 60 s allowance fits 64 bits
 *   PW_CLOCK_BACKWARDS_STAGE/READ  that read of that stage is below the origin;
 *                               PW_CLOCK_PHASE_GATE holds it until collection
 *                               explicitly authorizes the injected sample
 *   PW_CLOCK_EXPIRE_SECOND_PHASE   the first phase-2 observation waits on the
 *                               same gate, then jumps 2^62 ticks: a valid expiry
 *   PW_CLOCK_EXEC_NEAR_CUTOFF   1/150000000, and the first exec observation
 *                               jumps to one millisecond before the default
 *                               115 s plan cutoff, so adding the 10 s child
 *                               allowance overflows while the sample is valid
 * Jumps are forward and persist, so every later sample stays ordered. */
#include <errno.h>
#include <mach/mach_time.h>
#include <mach-o/dyld.h>
#include <time.h>
static uint64_t pw_controlled_read(int stage);
static kern_return_t pw_controlled_timebase(mach_timebase_info_t info);
#define PW_CONTINUOUS_READ pw_controlled_read
#define PW_TIMEBASE_INFO pw_controlled_timebase
#ifdef PW_CLOCK_PHASE_GATE
#define main pw_clock_worker_main
#endif
#include "pw_probe_runner.c"
#ifdef PW_CLOCK_PHASE_GATE
#undef main
#endif

static uint64_t origin_raw, offset;
static unsigned reads[PW_CLOCK_EXEC_REAP + 1];

#ifdef PW_CLOCK_PHASE_GATE
/* The test owns <companion executable>.gate, created fresh for each run.
 * File receipts coordinate only this allow-default fixture. Production reads,
 * publication and driver release checks are unchanged. No fixed delay decides
 * whether collection has begun. This clock is independent of the injected one. */
static char gate_directory[PATH_MAX];
static mach_timebase_info_data_t gate_timebase;

static void gate_path(char *path, const char *name) {
    int n = snprintf(path, PATH_MAX, "%s/%s", gate_directory, name);
    if (n < 0 || n >= PATH_MAX) _exit(71);
}

static void gate_mark(const char *name) {
    char path[PATH_MAX]; gate_path(path, name);
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
    if (fd < 0) _exit(71);
    /* Existence is the signal; the close completes before the next stage. */
    if (close(fd) != 0) _exit(71);
}

static void await_collection(void) {
    char trigger[PATH_MAX]; gate_path(trigger, "collection-open");
    gate_mark("ready");
    uint64_t start = mach_continuous_time();
    for (;;) {
        if (access(trigger, F_OK) == 0) break;
        if (errno != ENOENT) _exit(71);
        uint64_t now = mach_continuous_time();
        if (now < start || (__uint128_t)(now - start) * gate_timebase.numer
                >= (__uint128_t)5000000000ull * gate_timebase.denom) {
            gate_mark("timed-out");
            _exit(71); /* fixture failure, never a fabricated worker clock fault */
        }
        usleep(1000);
    }
    gate_mark("injected");
    errno = EPERM;
}

int main(int argc, char **argv) {
    if (argc > 1) {
        uint32_t size = sizeof(gate_directory);
        if (_NSGetExecutablePath(gate_directory, &size) != 0
                || strlcat(gate_directory, ".gate", sizeof(gate_directory)) >= sizeof(gate_directory)
                || mach_timebase_info(&gate_timebase) != KERN_SUCCESS
                || !gate_timebase.numer || !gate_timebase.denom) return 71;
    }
    return pw_clock_worker_main(argc, argv);
}
#endif

static uint64_t pw_controlled_read(int stage) {
    uint64_t raw = mach_continuous_time() + offset;
    reads[stage]++;
    errno = EPERM;
    if (stage == PW_CLOCK_WORKER_START) return origin_raw = raw;
#if defined(PW_CLOCK_BACKWARDS_STAGE)
    if (stage == PW_CLOCK_BACKWARDS_STAGE && reads[stage] == PW_CLOCK_BACKWARDS_READ) {
#ifdef PW_CLOCK_PHASE_GATE
        await_collection();
#endif
        return origin_raw - 1;
    }
#elif defined(PW_CLOCK_EXPIRE_SECOND_PHASE)
    static uint64_t phase2_start;
    if (stage == PW_CLOCK_PROCEED_START && reads[stage] == 2) phase2_start = raw;
    if (stage == PW_CLOCK_PROCEED_OBSERVE && phase2_start && !offset) {
        await_collection();
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

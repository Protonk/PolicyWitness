#include <time.h>
#include <errno.h>
static int pw_controlled_clock(int phase, struct timespec *value);
#define PW_MONOTONIC_READ pw_controlled_clock
#include "pw_probe_runner.c"

static int pw_controlled_clock(int phase, struct timespec *value) {
#ifdef PW_CLOCK_FAIL_LATER
    const int failed_phase = PW_CLOCK_PROCEED_OBSERVE;
#else
    const int failed_phase = PW_CLOCK_PROCEED_START;
#endif
    if (phase != failed_phase) return clock_gettime(CLOCK_MONOTONIC, value);
    errno = EIO;
    return -1;
}

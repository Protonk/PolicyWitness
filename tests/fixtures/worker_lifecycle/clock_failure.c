#include <time.h>
#include <errno.h>
static int pw_controlled_clock(clockid_t clock, struct timespec *value) {
#ifdef PW_CLOCK_FAIL_LATER
    static int calls;
    if (++calls == 1) return clock_gettime(clock, value);
#else
    (void)clock; (void)value;
#endif
    errno = EIO;
    return -1;
}
#define clock_gettime pw_controlled_clock
#include "pw_probe_runner.c"

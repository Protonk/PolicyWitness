#include <time.h>
#include <errno.h>
static int pw_controlled_clock(clockid_t clock, struct timespec *value) {
#ifdef PW_CLOCK_FAIL_LATER
    /* The worker reads its start time for the exec attempt budget, then the
     * release wait's start. Both succeed; the wait's next read fails. */
    static int calls;
    if (++calls <= 2) return clock_gettime(clock, value);
#else
    (void)clock; (void)value;
#endif
    errno = EIO;
    return -1;
}
#define clock_gettime pw_controlled_clock
#include "pw_probe_runner.c"

/* Investigation equipment, not a shipped worker. One fresh process per run.
 * The child makes no explicit clock read before apply unless warm=1. All
 * post-apply observations go to inherited shared memory, not a permitted fd.
 * Library/loader-internal initialization is outside this first-explicit-use claim.
 */
#include <errno.h>
#include <inttypes.h>
#include <mach/mach_time.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

extern void *sandbox_compile_string(const char *, void *, char **);
extern int sandbox_apply(void *);

typedef struct {
    int apply_rc, apply_errno, compile_ok, warm_rc, warm_errno;
    int first_rc, first_errno, first_failure_rc, first_failure_errno;
    uint64_t first, last, failures, regressions, zeros, first_failure_index;
    uint64_t samples[8];
    _Atomic unsigned finished;
} report;

static int read_clock(int kind, uint64_t *value) {
    struct timespec ts = {0};
    if (kind < 2) {
        int rc = clock_gettime(kind == 0 ? CLOCK_MONOTONIC : CLOCK_MONOTONIC_RAW, &ts);
        if (!rc) *value = (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
        return rc;
    }
    *value = kind == 2 ? mach_absolute_time() : mach_continuous_time();
    return 0; /* These APIs have no native error return. */
}

int main(int argc, char **argv) {
    if (argc != 5) return 64;
    int kind = atoi(argv[1]), warm = atoi(argv[2]), policy = atoi(argv[3]);
    uint64_t count = strtoull(argv[4], NULL, 10);
    if (kind < 0 || kind > 3 || warm < 0 || warm > 1 || policy < 0 || policy > 2 || !count) return 64;
    const char *policies[] = {"(version 2)(deny default)(allow file-read-data)",
                             "(version 2)(deny default)", "(version 2)(allow default)"};
    report *r = mmap(NULL, sizeof(*r), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    if (r == MAP_FAILED) return 65;
    memset(r, 0, sizeof(*r));
    pid_t pid = fork();
    if (pid == -1) return 66;
    if (!pid) {
        if (warm) { uint64_t v = 0; errno = 0; r->warm_rc = read_clock(kind, &v); r->warm_errno = errno; }
        char *error = NULL;
        void *profile = sandbox_compile_string(policies[policy], NULL, &error);
        r->compile_ok = profile != NULL;
        if (!profile) _exit(67);
        r->apply_rc = sandbox_apply(profile); r->apply_errno = errno;
        if (r->apply_rc) _exit(68);
        uint64_t previous = 0;
        int have_previous = 0;
        for (uint64_t i = 0; i < count; ++i) {
            uint64_t value = 0;
            errno = 0;
            int rc = read_clock(kind, &value), error_number = errno;
            if (!i) { r->first_rc = rc; r->first_errno = error_number; r->first = value; }
            if (i < 8) r->samples[i] = value;
            if (rc) {
                if (!r->failures) { r->first_failure_index = i; r->first_failure_rc = rc; r->first_failure_errno = error_number; }
                ++r->failures;
            } else {
                if (!value) ++r->zeros;
                if (have_previous && value < previous) ++r->regressions;
                previous = value; have_previous = 1; r->last = value;
            }
        }
        atomic_store_explicit(&r->finished, 1, memory_order_release);
        _exit(0);
    }
    int status = 0;
    pid_t reaped;
    do { reaped = waitpid(pid, &status, 0); } while (reaped == -1 && errno == EINTR);
    mach_timebase_info_data_t tb = {0};
    int tb_rc = mach_timebase_info(&tb); /* Parent only, after child has exited. */
    printf("{\"pid\":%d,\"reaped\":%s,\"wait_status\":%d,\"kind\":%d,\"warm\":%d,\"policy\":%d,\"count\":%" PRIu64 ","
           "\"compile_ok\":%d,\"apply_rc\":%d,\"apply_errno\":%d,\"warm_rc\":%d,\"warm_errno\":%d,"
           "\"first_rc\":%d,\"first_errno\":%d,\"first\":%" PRIu64 ",\"last\":%" PRIu64 ","
           "\"failures\":%" PRIu64 ",\"first_failure_index\":%" PRIu64 ",\"first_failure_rc\":%d,\"first_failure_errno\":%d,"
           "\"regressions\":%" PRIu64 ",\"zeros\":%" PRIu64 ",\"finished\":%u,\"timebase_rc\":%d,\"numer\":%u,\"denom\":%u,\"samples\":[",
           pid, reaped == pid ? "true" : "false", status, kind, warm, policy, count,
           r->compile_ok, r->apply_rc, r->apply_errno, r->warm_rc, r->warm_errno,
           r->first_rc, r->first_errno, r->first, r->last, r->failures, r->first_failure_index,
           r->first_failure_rc, r->first_failure_errno, r->regressions, r->zeros,
           atomic_load_explicit(&r->finished, memory_order_acquire), tb_rc, tb.numer, tb.denom);
    for (unsigned i = 0; i < 8; ++i) printf("%s%" PRIu64, i ? "," : "", r->samples[i]);
    puts("]}");
    return reaped == pid && WIFEXITED(status) && WEXITSTATUS(status) == 0 ? 0 : 69;
}

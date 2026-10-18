/* Production sysctl/read with only the native call substituted. The receipt
 * is independent of the source capacity constant; no sandbox is applied. */
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/sysctl.h>

static int controlled_sysctlbyname(const char *, void *, size_t *, void *, size_t);
#define sysctlbyname controlled_sysctlbyname
#define main worker_main
#ifndef PW_SYSCTL_WORKER_SOURCE
#define PW_SYSCTL_WORKER_SOURCE "pw_probe_runner.c"
#endif
#include PW_SYSCTL_WORKER_SOURCE
#undef main
#undef sysctlbyname

static unsigned calls;
static int failure, target_matches, destination_nonnull, new_value_null;
static size_t incoming_length, new_value_length;

static int controlled_sysctlbyname(const char *name, void *oldp, size_t *oldlenp,
                                 void *newp, size_t newlen) {
    calls++;
    target_matches = strcmp(name, "pw.sysctl.boundary-control") == 0;
    destination_nonnull = oldp != NULL;
    incoming_length = oldlenp ? *oldlenp : 0;
    new_value_null = newp == NULL;
    new_value_length = newlen;
    if (oldlenp) *oldlenp = failure ? 0 : 7;
    errno = failure ? ENOMEM : EBUSY;
    return failure ? -1 : 0;
}

int main(void) {
    for (failure = 0; failure <= 1; failure++) {
        pw_shm_slot_t slot = {0};
        strcpy(slot.target, "pw.sysctl.boundary-control");
        calls = 0;
        attempt_sysctl_read(&slot);
        printf("{\"failure\":%d,\"calls\":%u,\"target_matches\":%d,"
               "\"destination_nonnull\":%d,\"incoming_length\":%zu,"
               "\"new_value_null\":%d,\"new_value_length\":%zu,"
               "\"rc\":%d,\"errno\":%d,\"error_label\":%d}\n",
               failure, calls, target_matches, destination_nonnull,
               incoming_length, new_value_null, new_value_length,
               slot.rc, slot.errno_val,
               strncmp(slot.error, "sysctlbyname:", 13) == 0);
    }
    return 0;
}

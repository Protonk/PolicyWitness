#include <errno.h>
#include <sys/types.h>

int sandbox_check(pid_t pid, const char *operation, int type, ...);

int pw_sandbox_check(pid_t pid, const char *operation, int type, const char *arg, int *out_errno) {
    errno = 0;
    int rc = sandbox_check(pid, operation, type, arg);
    if (out_errno) {
        *out_errno = errno;
    }
    return rc;
}

int pw_sandbox_check_noarg(pid_t pid, const char *operation, int *out_errno) {
    errno = 0;
    int rc = sandbox_check(pid, operation, 0);
    if (out_errno) {
        *out_errno = errno;
    }
    return rc;
}

/* Investigative host fixture only; use the SDK's proc_bsdinfo layout. */
#include <errno.h>
#include <libproc.h>
#include <stdint.h>
#include <sys/proc_info.h>

int pw_f2_process_identity(int pid, uint64_t *seconds, uint64_t *microseconds,
                           int *parent, int *error) {
    struct proc_bsdinfo info = {0};
    errno = 0;
    int count = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, sizeof(info));
    *error = errno;
    if (count != (int)sizeof(info)) return count;
    *seconds = info.pbi_start_tvsec;
    *microseconds = info.pbi_start_tvusec;
    *parent = info.pbi_ppid;
    return 0;
}

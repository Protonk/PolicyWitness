/* Independent descriptor observer and pre-worker adapter. No PW ABI headers.
 * The existing direct harness invokes --then-exec before the real worker and
 * --inspect in its three exec slots. Only the adapter's closed-* invocation
 * closes fd 2; child observations occur before any socket or file is opened.
 */
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/un.h>
#include <unistd.h>

#include "closed_worker_stderr_config.h"

static int write_all(int fd, const char *data, size_t length) {
    while (length) {
        ssize_t n = write(fd, data, length);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        data += n;
        length -= (size_t)n;
    }
    return 0;
}

/* The parent observes LOCAL_PEERPID and registers an OS exit event before
 * acknowledging. Always close this socket before returning to the adapter.
 */
static int rendezvous(const char *record) {
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return -1;
    struct timeval timeout = {2, 0};
    struct sockaddr_un address = {0};
    address.sun_family = AF_UNIX;
    size_t length = strlen(PW_CLOSED_STDERR_SOCKET);
    if (length >= sizeof(address.sun_path)) { close(fd); return -1; }
    memcpy(address.sun_path, PW_CLOSED_STDERR_SOCKET, length + 1);
    int rc = setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    if (!rc) rc = setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
    if (!rc) rc = connect(fd, (struct sockaddr *)&address, sizeof(address));
    if (!rc) rc = write_all(fd, record, strlen(record));
    char reply = 0;
    if (!rc) {
        ssize_t n;
        do { n = read(fd, &reply, 1); } while (n < 0 && errno == EINTR);
        if (n != 1 || reply != 'g') rc = -1;
    }
    if (close(fd) != 0) rc = -1;
    return rc;
}

typedef struct {
    int fd, flags, flags_errno, stat_rc, stat_errno;
    unsigned long long device, inode, size;
    unsigned mode;
} fd_state;

static fd_state inspect_fd(int fd) {
    fd_state state = {.fd = fd};
    errno = 0;
    state.flags = fcntl(fd, F_GETFD);
    state.flags_errno = state.flags < 0 ? errno : 0;
    struct stat metadata;
    errno = 0;
    state.stat_rc = fstat(fd, &metadata);
    state.stat_errno = state.stat_rc ? errno : 0;
    if (!state.stat_rc) {
        state.device = (unsigned long long)(uint32_t)metadata.st_dev;
        state.inode = (unsigned long long)metadata.st_ino;
        state.size = (unsigned long long)metadata.st_size;
        state.mode = metadata.st_mode;
    }
    return state;
}

static void emit_states(const fd_state states[5]) {
    putchar('[');
    for (int i = 0; i < 5; i++) {
        const fd_state *s = &states[i];
        printf("%s{\"fd\":%d,\"flags\":%d,\"flags_errno\":%d,\"stat_rc\":%d,"
               "\"stat_errno\":%d,\"device\":%llu,\"inode\":%llu,\"size\":%llu,\"mode\":%u}",
               i ? "," : "", s->fd, s->flags, s->flags_errno, s->stat_rc,
               s->stat_errno, s->device, s->inode, s->size, s->mode);
    }
    putchar(']');
}

static int adapter(const char *nonce, char **forward_argv) {
    char hello[256];
    int length = snprintf(hello, sizeof(hello),
        "{\"role\":\"adapter\",\"nonce\":\"%s\",\"pid\":%d,\"ppid\":%d}\n",
        nonce, getpid(), getppid());
    if (length < 0 || (size_t)length >= sizeof(hello) || rendezvous(hello)) return 120;

    /* The rendezvous descriptor is gone. No open/socket call follows before
     * execv. The final snapshot independently checks the supplied fd-2 state.
     */
    fd_state before[5], after[5];
    for (int fd = 0; fd < 5; fd++) before[fd] = inspect_fd(fd);
    int close_rc = 0, close_errno = 0;
    int requested = strncmp(nonce, "closed-", 7) == 0;
    if (requested) {
        errno = 0;
        close_rc = close(STDERR_FILENO);
        close_errno = close_rc ? errno : 0;
    }
    for (int fd = 0; fd < 5; fd++) after[fd] = inspect_fd(fd);
    printf("{\"role\":\"worker_entry\",\"nonce\":\"%s\",\"pid\":%d,"
           "\"ppid\":%d,\"close_requested\":%s,\"close_rc\":%d,\"close_errno\":%d,\"before\":",
           nonce, getpid(), getppid(), requested ? "true" : "false", close_rc, close_errno);
    emit_states(before);
    printf(",\"after\":");
    emit_states(after);
    printf("}\n");
    if (fflush(stdout) != 0) return 121;
    if (close_rc || (requested && (after[2].flags != -1 || after[2].flags_errno != EBADF))) return 122;
    /* Recheck after formatting/flush as well. No formatting, socket or open
     * call lies between this final descriptor observation and execv.
     */
    errno = 0;
    int final_flags = fcntl(STDERR_FILENO, F_GETFD);
    int final_errno = final_flags < 0 ? errno : 0;
    if (requested ? (final_flags != -1 || final_errno != EBADF) : final_flags < 0) return 122;
    execv(forward_argv[0], forward_argv);
    return 123;
}

static void alarm_exit(int signum) { (void)signum; _exit(124); }

static int child(const char *nonce) {
    /* This deadline belongs only to the observer, never the worker. It also
     * bounds an observer that cannot reach the parent after a harness failure.
     */
    signal(SIGALRM, alarm_exit);
    alarm(10);
    fd_state stderr_state = inspect_fd(STDERR_FILENO);
    char marker[96];
    int marker_length = snprintf(marker, sizeof(marker), "stderr:%s\n", nonce);
    if (marker_length < 0 || (size_t)marker_length >= sizeof(marker)) return 125;
    errno = 0;
    ssize_t written = write(STDERR_FILENO, marker, (size_t)marker_length);
    int write_errno = written < 0 ? errno : 0;
    char record[768];
    int length = snprintf(record, sizeof(record),
        "{\"role\":\"child\",\"nonce\":\"%s\",\"pid\":%d,\"ppid\":%d,"
        "\"fd2_flags\":%d,\"fd2_errno\":%d,\"fd2_stat_rc\":%d,\"fd2_stat_errno\":%d,"
        "\"fd2_mode\":%u,\"write_rc\":%zd,\"write_errno\":%d,\"write_expected\":%d}\n",
        nonce, getpid(), getppid(), stderr_state.flags, stderr_state.flags_errno,
        stderr_state.stat_rc, stderr_state.stat_errno, stderr_state.mode,
        written, write_errno, marker_length);
    if (length < 0 || (size_t)length >= sizeof(record)) return 126;
    /* Native observations above precede this socket. Its receipt is independent
     * of PW. Closing it precedes publishing the same receipt through stdout.
     */
    if (rendezvous(record)) return 127;
    if (write_all(STDOUT_FILENO, record, (size_t)length)) return 128;
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 5 || strcmp(argv[1], "--inspect") || strcmp(argv[3], "--read-fd") || strcmp(argv[4], "200")) return 2;
    const char *nonce = argv[2];
    size_t length = strlen(nonce);
    if (!length || length > 64 || strspn(nonce, "abcdefghijklmnopqrstuvwxyz0123456789-") != length) return 2;
    if (argc >= 7 && strcmp(argv[5], "--then-exec") == 0) return adapter(nonce, argv + 6);
    if (argc != 5) return 2;
    return child(nonce);
}

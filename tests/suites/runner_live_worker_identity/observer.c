/* Test-owned observer and rendezvous helper. No PW headers or validator code.
 * The observer gets the connecting helper's PID from LOCAL_PEERPID, follows
 * libproc ancestry, and queries libsandbox itself while the helper is blocked.
 */
#include <errno.h>
#include <libproc.h>
#include <limits.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

extern int sandbox_check(pid_t, const char *, int, ...);

static void fail(const char *message) {
    fprintf(stderr, "%s (errno=%d: %s)\n", message, errno, strerror(errno));
    exit(2);
}

static void readable(int fd) {
    struct pollfd p = {.fd = fd, .events = POLLIN};
    int rc;
    do { rc = poll(&p, 1, 7000); } while (rc < 0 && errno == EINTR);
    if (rc != 1 || !(p.revents & POLLIN)) fail("rendezvous timed out or closed");
}

static struct proc_bsdinfo process(pid_t pid, const char *expected_name) {
    struct proc_bsdinfo info = {0};
    char path[PROC_PIDPATHINFO_MAXSIZE];
    if (proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, sizeof(info)) != sizeof(info)
        || info.pbi_pid != (unsigned)pid) fail("proc_pidinfo");
    if (proc_pidpath(pid, path, sizeof(path)) <= 0) fail("proc_pidpath");
    const char *name = strrchr(path, '/');
    if (!name || strcmp(name + 1, expected_name) != 0) {
        fprintf(stderr, "pid %d: expected executable %s, got %s\n", pid, expected_name, path);
        exit(2);
    }
    return info;
}

static void print_process(const char *role, struct proc_bsdinfo p) {
    printf("\"%s\":{\"pid\":%u,\"ppid\":%u,\"start_sec\":%llu,\"start_usec\":%llu}",
           role, p.pbi_pid, p.pbi_ppid,
           (unsigned long long)p.pbi_start_tvsec, (unsigned long long)p.pbi_start_tvusec);
}

static void print_checks(const char *role, pid_t pid, const char *allowed, const char *denied) {
    /* PATH=1 is a test-owned constant, independently pinned by the allow/deny
     * controls below. Importing PW's filter mapping would share its mistakes. */
    errno = 0;
    int allow_rc = sandbox_check(pid, "file-read-data", 1, allowed);
    int allow_errno = errno;
    errno = 0;
    int deny_rc = sandbox_check(pid, "file-read-data", 1, denied);
    int deny_errno = errno;
    printf(",\"%s_checks\":{\"allowed_rc\":%d,\"allowed_errno\":%d,"
           "\"denied_rc\":%d,\"denied_errno\":%d}",
           role, allow_rc, allow_errno, deny_rc, deny_errno);
}

int main(int argc, char **argv) {
    if (argc != 3 && argc != 5) return 2;
    int hold = strcmp(argv[1], "--hold") == 0;
    if ((hold && argc != 3) || (!hold && (argc != 5 || strcmp(argv[1], "--observe")))) return 2;
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    if (strlen(argv[2]) >= sizeof(address.sun_path)) fail("socket path too long");
    strcpy(address.sun_path, argv[2]);
    address.sun_len = sizeof(address);
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) fail("socket");
    if (hold) {
        if (connect(fd, (struct sockaddr *)&address, sizeof(address))) fail("connect");
        readable(fd);
        char release = 0;
        if (read(fd, &release, 1) != 1 || release != 'G') fail("missing release byte");
        close(fd);
        puts("released");
        return 0;
    }

    if (bind(fd, (struct sockaddr *)&address, sizeof(address)) || listen(fd, 1)) fail("listen");
    puts("ready");
    fflush(stdout);
    readable(fd);
    int peer = accept(fd, NULL, NULL);
    if (peer < 0) fail("accept");
    pid_t helper_pid = 0;
    socklen_t size = sizeof(helper_pid);
    if (getsockopt(peer, SOL_LOCAL, LOCAL_PEERPID, &helper_pid, &size)
        || size != sizeof(helper_pid) || helper_pid <= 0) fail("LOCAL_PEERPID");
    const char *own_name = strrchr(argv[0], '/');
    struct proc_bsdinfo helper = process(helper_pid, own_name ? own_name + 1 : argv[0]);
    struct proc_bsdinfo worker = process(helper.pbi_ppid, "pw-probe-runner");
    struct proc_bsdinfo host = process(worker.pbi_ppid, "PWRunner");
    putchar('{');
    print_process("helper", helper);
    putchar(',');
    print_process("worker", worker);
    putchar(',');
    print_process("host", host);
    print_checks("worker", worker.pbi_pid, argv[3], argv[4]);
    print_checks("host", host.pbi_pid, argv[3], argv[4]);
    puts("}");
    fflush(stdout);
    if (write(peer, "G", 1) != 1) fail("release helper");
    close(peer);
    close(fd);
    unlink(argv[2]);
    return 0;
}

/*
 * Shared libSystem-dynamic exec fixture. No PW headers or implementation
 * dependencies. Also runnable directly to check the test equipment.
 *
 * Built on demand by build.sh via `xcrun clang` under tests/out/.
 * Not signed, not notarized,
 * not in the app bundle — purely a test fixture.
 *
 * Default behavior: print a fixed marker line to stdout and exit 0.
 * Optional flags exercise the failure shapes the worker has to
 * surface:
 *   --exit N      exit with code N (cap at 255 for portability).
 *   --stdout-bytes N
 *                 write N bytes (deterministic 'A' fill) to stdout
 *                 before exiting. Used to exercise the worker's
 *                 truncation marker when N exceeds the slot budget.
 *   --stderr S    write S plus a newline to stderr.
 *   --tree SOCKET connect a leader and forked child to a test-owned Unix
 *                 socket, then wait for commands. Both keep the inherited
 *                 process group; the fixture does not set up isolation.
 *   --process PID report libproc identity/ancestry for a live process.
 *   --inspect NONCE [--env-key NAME] [--read-fd N]
 *                 emit a complete JSON process-state observation instead
 *                 of the default marker. See README.md for the protocol.
 *   --then-exec PATH ARGS...
 *                 after inspection, exec PATH preserving PID/env/FDs;
 *                 skip reading stdin so a worker's policy pipe is preserved.
 *
 * Dynamic linkage against libSystem is intentional: it exercises
 * dyld + shared-cache resolution at exec time, which is what
 * `exec_baseline` has to allow. A statically-linked helper would
 * skip that surface entirely and produce a misleadingly small
 * baseline.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <libproc.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;

static void json_string(FILE *out, const char *value) {
    if (!value) { fputs("null", out); return; }
    fputc('"', out);
    for (const unsigned char *p = (const unsigned char *)value; *p; p++) {
        if (*p == '"' || *p == '\\') fprintf(out, "\\%c", *p);
        else if (*p < 32 || *p >= 127) fprintf(out, "\\u%04x", *p);
        else fputc(*p, out);
    }
    fputc('"', out);
}

/* Snapshot before opening, closing, or duplicating any descriptors. The
 * kernel inventory does not open a directory/reporting socket of its own.
 * A full buffer is an error, never an apparently complete short inventory.
 * Only the explicitly requested canary FD is read, with pread so its offset
 * survives a subsequent exec. No arbitrary worker resources are read.
 */
static int inspect(const char *nonce, const char *key, int canary_fd, int forwarding) {
    struct proc_fdinfo fds[4096];
    int bytes = proc_pidinfo(getpid(), PROC_PIDLISTFDS, 0, fds, sizeof(fds));
    if (bytes <= 0 || bytes >= (int)sizeof(fds) || bytes % sizeof(fds[0])) {
        fprintf(stderr, "exec_fixture: incomplete fd inventory (%d bytes, errno=%d)\n", bytes, errno);
        return 2;
    }
    size_t env_count = 0;
    while (environ && environ[env_count]) env_count++;
    unsigned char canary[32];
    errno = 0;
    ssize_t canary_rc = pread(canary_fd, canary, sizeof(canary), 0);
    int canary_errno = canary_rc < 0 ? errno : 0;
    int stdin_rc = -2, stdin_errno = 0;
    if (!forwarding) {
        struct pollfd input = {.fd = STDIN_FILENO, .events = POLLIN};
        int ready = poll(&input, 1, 100);
        if (ready > 0) {
            unsigned char c;
            stdin_rc = (int)read(STDIN_FILENO, &c, 1);
            if (stdin_rc < 0) stdin_errno = errno;
        } else if (ready < 0) { stdin_rc = -1; stdin_errno = errno; }
    }
    printf("{\"version\":1,\"nonce\":"); json_string(stdout, nonce);
    printf(",\"pid\":%d,\"env_count\":%zu,\"env_key\":", getpid(), env_count);
    json_string(stdout, key);
    fputs(",\"env_value\":", stdout); json_string(stdout, getenv(key));
    fputs(",\"fds\":[", stdout);
    for (size_t i = 0; i < (size_t)bytes / sizeof(fds[0]); i++) {
        if (i) putchar(',');
        printf("[%d,%u]", fds[i].proc_fd, fds[i].proc_fdtype);
    }
    printf("],\"stdin_rc\":%d,\"stdin_errno\":%d,\"stdin_skipped\":%s",
           stdin_rc, stdin_errno, forwarding ? "true" : "false");
    printf(",\"canary_fd\":%d,\"canary_rc\":%zd,\"canary_errno\":%d,\"canary_hex\":\"",
           canary_fd, canary_rc, canary_errno);
    for (ssize_t i = 0; i < canary_rc; i++) printf("%02x", canary[i]);
    fputs("\",\"complete\":true}\n", stdout);
    fprintf(stderr, "inspect:%s\n", nonce);
    return fflush(stdout) == 0 && fflush(stderr) == 0 ? 0 : 2;
}

/* Each process announces its role. The observer obtains its PID from the
 * socket's kernel credentials. 'p' -> 'a' proves the process can still run;
 * 'q' asks it to exit. EOF/errors fail, and an alarm bounds even broken tests.
 * These processes retain stdout/stderr so leaking a child also leaks pipes.
 */
static int controlled_process(const char *path, char role) {
    alarm(45);
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    if (strlen(path) >= sizeof(address.sun_path)) return 2;
    strcpy(address.sun_path, path);
    address.sun_len = sizeof(address);
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return 2;
    if (connect(fd, (struct sockaddr *)&address, sizeof(address)) != 0
        || write(fd, &role, 1) != 1) {
        close(fd);
        return 2;
    }
    int result = 2;
    char command;
    for (;;) {
        ssize_t n = read(fd, &command, 1);
        if (n < 0 && errno == EINTR) continue;
        if (n != 1) break;
        if (command == 'q') { result = 0; break; }
        if (command != 'p' || write(fd, "a", 1) != 1) break;
    }
    close(fd);
    return result;
}

static int run_tree(const char *path) {
    /* Flush before fork so buffered output cannot be duplicated by the child. */
    fflush(NULL);
    signal(SIGPIPE, SIG_IGN);
    alarm(45);
    pid_t child = fork();
    if (child < 0) return 2;
    if (child == 0) _exit(controlled_process(path, 'C'));
    int result = controlled_process(path, 'P');
    if (result != 0) kill(child, SIGKILL);
    int status = 0;
    pid_t waited;
    do { waited = waitpid(child, &status, 0); } while (waited < 0 && errno == EINTR);
    if (waited != child || !WIFEXITED(status) || WEXITSTATUS(status) != 0) return 2;
    return result;
}

static void write_stdout_fill(long count) {
    /* Stream in chunks so a million-byte request doesn't allocate a
     * million-byte buffer. */
    char chunk[4096];
    memset(chunk, 'A', sizeof(chunk));
    while (count > 0) {
        size_t n = (count > (long)sizeof(chunk)) ? sizeof(chunk) : (size_t)count;
        if (fwrite(chunk, 1, n, stdout) != n) break;
        count -= (long)n;
    }
    fflush(stdout);
}

/* Run by the unsandboxed observer, not by the process being identified. */
static int describe_process(const char *text) {
    char *end = NULL;
    errno = 0;
    long pid = strtol(text, &end, 10);
    if (errno || end == text || *end || pid <= 0 || pid > INT_MAX) return 2;
    struct proc_bsdinfo info = {0};
    char path[PROC_PIDPATHINFO_MAXSIZE];
    if (proc_pidinfo((pid_t)pid, PROC_PIDTBSDINFO, 0, &info, sizeof(info)) != sizeof(info)
        || info.pbi_pid != (unsigned)pid
        || proc_pidpath((pid_t)pid, path, sizeof(path)) <= 0) {
        fprintf(stderr, "exec_fixture: process %ld unavailable (errno=%d)\n", pid, errno);
        return 2;
    }
    printf("{\"version\":1,\"pid\":%u,\"ppid\":%u,\"start_sec\":%llu,\"start_usec\":%llu,\"path\":",
           info.pbi_pid, info.pbi_ppid, (unsigned long long)info.pbi_start_tvsec,
           (unsigned long long)info.pbi_start_tvusec);
    json_string(stdout, path);
    puts(",\"complete\":true}");
    return fflush(stdout) == 0 ? 0 : 2;
}

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[1], "--process") == 0) return describe_process(argv[2]);
    int    exit_code      = 0;
    long   stdout_bytes   = -1;          /* -1 → emit the default marker */
    const char *stderr_msg = NULL;
    const char *tree_socket = NULL;
    const char *inspect_nonce = NULL;
    const char *env_key = "PW_FIXTURE_CANARY";
    int canary_fd = -1;
    char **forward_argv = NULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--exit") == 0 && i + 1 < argc) {
            exit_code = atoi(argv[++i]) & 0xff;
        } else if (strcmp(argv[i], "--stdout-bytes") == 0 && i + 1 < argc) {
            stdout_bytes = strtol(argv[++i], NULL, 10);
        } else if (strcmp(argv[i], "--stderr") == 0 && i + 1 < argc) {
            stderr_msg = argv[++i];
        } else if (strcmp(argv[i], "--tree") == 0 && i + 1 < argc) {
            tree_socket = argv[++i];
        } else if (strcmp(argv[i], "--inspect") == 0 && i + 1 < argc) {
            inspect_nonce = argv[++i];
        } else if (strcmp(argv[i], "--env-key") == 0 && i + 1 < argc) {
            env_key = argv[++i];
        } else if (strcmp(argv[i], "--read-fd") == 0 && i + 1 < argc) {
            canary_fd = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--then-exec") == 0 && i + 1 < argc) {
            forward_argv = &argv[i + 1];
            break;
        } else {
            fprintf(stderr, "exec_fixture: unknown arg %s\n", argv[i]);
            return 2;
        }
    }

    if (inspect_nonce) {
        if (tree_socket || stderr_msg || stdout_bytes >= 0 || exit_code) return 2;
        int result = inspect(inspect_nonce, env_key, canary_fd, forward_argv != NULL);
        if (result != 0 || !forward_argv) return result;
        /* The harness uses this to establish the real worker's launch state.
         * Preserve PID, environment, descriptors, and the unread policy pipe. */
        execv(forward_argv[0], forward_argv);
        perror("exec_fixture: execv");
        return 2;
    }
    if (forward_argv) return 2;

    if (stdout_bytes >= 0) {
        write_stdout_fill(stdout_bytes);
    } else {
        fputs("exec_fixture: hello from helper\n", stdout);
        fflush(stdout);
    }
    if (stderr_msg) {
        fputs(stderr_msg, stderr);
        fputc('\n', stderr);
        fflush(stderr);
    }
    if (tree_socket) {
        int result = run_tree(tree_socket);
        if (result != 0) return result;
    }
    return exit_code;
}

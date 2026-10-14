/* Independent native target, not the PW worker or its evidence protocol.
 * One exec, one sandbox application. The parent queries this PID with the
 * shipped validator, then sends an operation over an inherited pipe. All
 * policies allow default and add only path-specific file denials, so the
 * coordination pipes do not need extra policy rules. */
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>

extern void *sandbox_compile_string(const char *, void *, char **);
extern int sandbox_apply(void *);
extern void sandbox_free_profile(void *);

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    struct rlimit core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &core)) return 3;
    setbuf(stdout, NULL);
    char *error = NULL;
    void *profile = sandbox_compile_string(argv[1], NULL, &error);
    if (!profile) { fprintf(stderr, "compile: %s\n", error ? error : "unknown"); return 4; }
    errno = 0;
    int applied = sandbox_apply(profile), apply_errno = errno;
    if (applied) { fprintf(stderr, "apply: %d errno %d\n", applied, apply_errno); return 5; }
    sandbox_free_profile(profile);
    printf("{\"ready\":true,\"pid\":%d,\"apply_rc\":%d,\"apply_errno\":%d}\n", getpid(), applied, apply_errno);
    char line[8192];
    while (fgets(line, sizeof(line), stdin)) {
        char *newline = strchr(line, '\n');
        if (!newline) return 6;
        *newline = 0;
        if (!strcmp(line, "exit")) return 0;
        char *path = strchr(line, '\t');
        if (!path) return 7;
        *path++ = 0;
        int rc, saved, fd = -1, stat_rc = -2, stat_errno = 0, close_rc = -2, close_errno = 0;
        ssize_t io_rc = -2;
        int io_errno = 0;
        struct stat metadata = {0};
        unsigned char data[64] = {0};
        errno = 0;
        if (!strcmp(line, "read")) rc = fd = open(path, O_RDONLY | O_CLOEXEC);
        else if (!strcmp(line, "create")) rc = fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
        else if (!strcmp(line, "unlink")) rc = unlink(path);
        else if (!strcmp(line, "stat")) rc = stat(path, &metadata);
        else return 8;
        saved = errno;
        if (fd >= 0) {
            errno = 0; stat_rc = fstat(fd, &metadata); stat_errno = errno;
            errno = 0;
            if (!strcmp(line, "read")) io_rc = read(fd, data, sizeof(data));
            else io_rc = write(fd, "P", 1);
            io_errno = errno;
            errno = 0; close_rc = close(fd); close_errno = errno;
        }
        printf("{\"operation\":\"%s\",\"rc\":%d,\"errno\":%d,\"io_rc\":%zd,\"io_errno\":%d,\"stat_rc\":%d,\"stat_errno\":%d,\"device\":%u,\"inode\":%" PRIu64 ",\"close_rc\":%d,\"close_errno\":%d,\"content_hex\":\"", line, rc, saved, io_rc, io_errno, stat_rc, stat_errno, (unsigned)metadata.st_dev, (uint64_t)metadata.st_ino, close_rc, close_errno);
        if (!strcmp(line, "read") && io_rc > 0)
            for (ssize_t i = 0; i < io_rc; i++) printf("%02x", data[i]);
        puts("\"}");
    }
    return 0;
}

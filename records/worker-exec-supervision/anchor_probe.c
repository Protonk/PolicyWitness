/* Investigation equipment, not a production worker or proposed implementation.
 * A controller owns an anchor in a fresh process group. This separate spawner
 * applies an allow-default sandbox, then creates pipes and posix_spawns into
 * that already-known group. It withholds child identity and waits to be killed.
 * Only A/S marker bytes are reported; helper identity comes from kernel peers.
 */
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

extern void *sandbox_compile_string(const char *, void *, char **);
extern int sandbox_apply(void *);

static int marker(char value) { return write(STDOUT_FILENO, &value, 1) == 1 ? 0 : 2; }
static int command(char expected) {
    char value = 0;
    return read(STDIN_FILENO, &value, 1) == 1 && value == expected ? 0 : 2;
}
static int failure(const char *where, int error) {
    fprintf(stderr, "%s: %d\n", where, error);
    return 2;
}

int main(int argc, char **argv) {
    alarm(30);
    if (argc == 2 && strcmp(argv[1], "anchor") == 0) {
        if (setpgid(0, 0) != 0) return failure("anchor setpgid", errno);
        if (marker('A') != 0) return 2;
        return command('q');
    }
    if (argc != 5 || strcmp(argv[1], "spawn") != 0) return 2;
    char *end = NULL;
    long requested = strtol(argv[2], &end, 10);
    if (!end || *end || requested <= 1 || requested > 2147483647L) return 2;
    char *compile_error = NULL;
    void *profile = sandbox_compile_string("(version 1)(allow default)", NULL, &compile_error);
    if (!profile) return failure("sandbox_compile_string", errno);
    if (sandbox_apply(profile) != 0) return failure("sandbox_apply", errno);
    if (marker('A') != 0 || command('g') != 0) return 2;

    /* Attempt resources are created after application. The control stdin and
     * stdout are pre-existing experiment equipment, unlike the real shared
     * memory result channel. Their usability here proves no deny-profile fact. */
    int out[2], err[2];
    if (pipe(out) != 0 || pipe(err) != 0) return failure("pipe", errno);
    posix_spawnattr_t attr;
    posix_spawn_file_actions_t actions;
    int rc = posix_spawnattr_init(&attr);
    if (rc) return failure("attr_init", rc);
    rc = posix_spawn_file_actions_init(&actions);
    if (rc) return failure("actions_init", rc);
    rc = posix_spawnattr_setflags(&attr, POSIX_SPAWN_CLOEXEC_DEFAULT | POSIX_SPAWN_SETPGROUP);
    if (!rc) rc = posix_spawnattr_setpgroup(&attr, (pid_t)requested);
    if (!rc) rc = posix_spawn_file_actions_addopen(&actions, 0, "/dev/null", O_RDONLY, 0);
    if (!rc) rc = posix_spawn_file_actions_adddup2(&actions, out[1], 1);
    if (!rc) rc = posix_spawn_file_actions_adddup2(&actions, err[1], 2);
    for (int i = 0; !rc && i < 2; i++) {
        rc = posix_spawn_file_actions_addclose(&actions, out[i]);
        if (!rc) rc = posix_spawn_file_actions_addclose(&actions, err[i]);
    }
    if (rc) return failure("spawn_setup", rc);
    char *child_argv[] = {argv[3], "--tree", argv[4], NULL};
    char *empty_env[] = {NULL};
    pid_t child = 0;
    rc = posix_spawn(&child, argv[3], &actions, &attr, child_argv, empty_env);
    if (rc) return failure("posix_spawn", rc);
    close(out[1]); close(err[1]);
    /* Deliberately do not publish child. S proves the successful native return,
     * not the identity of the created process. Controller kills this process. */
    if (marker('S') != 0) return 2;
    return command('q');
}

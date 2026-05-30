/*
 * sentinel_harness — verify the post-apply shared-memory mechanics
 * the runner depends on, using the same primitive shapes
 * pw-probe-runner uses.
 *
 * The runner host posix_spawns pw-probe-runner, passes a
 * shared-memory FD across the exec boundary via
 * posix_spawn_file_actions_adddup2, and the spawned worker
 * (a) mmaps that inherited FD shared, (b) applies the specimen
 * policy, (c) writes attempt results into the mmap'd region via
 * memory stores after apply, and (d) spins until the host signals
 * exit. This harness replicates that exact shape:
 *
 *   parent role  → posix_spawn child (re-exec of self with argv[1] sentinel),
 *                  passing a file-backed shared FD as FD 3
 *   child role   → mmap FD 3 shared, sandbox_apply bare (deny default),
 *                  store sentinel byte to shm, perform one attempt
 *                  (access("/etc/hosts", F_OK)), store rc + errno to
 *                  shm, spin until SIGKILLed
 *   parent again → poll shm header for sentinel; on success read the
 *                  recorded attempt result; SIGKILL the child; print
 *                  one line each for sentinel and attempt
 *
 * What this proves vs the future architecture:
 *   ✓ posix_spawn + inherited FD + mmap on the inherited FD works
 *     post-apply under bare (deny default).
 *   ✓ Memory stores into the shared region are observable to the
 *     parent without the worker invoking any syscall.
 *   ✓ An attempt (a single open/access-class syscall) records its
 *     result via memory store — the same recording mechanism the C
 *     probe-runner will use for each step.
 *   ✗ Does not exercise sandbox_compile_string + sandbox_apply via
 *     dlopen libsandbox (uses the deprecated sandbox_init for code
 *     economy). That distinction is orthogonal: the policy-apply
 *     mechanics differ between the two API forms, but the
 *     post-apply syscall surface and memory-store visibility do not.
 *
 * Output on success:
 *   sentinel_observed=1 (elapsed=<n>ms)
 *   attempt_rc=<n> attempt_errno=<n>
 *
 * On timeout (child failed to apply or store):
 *   sentinel_observed=0 (timeout=<n>ms, child status=0x<n>)
 */

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include <mach-o/dyld.h>
#include <sandbox.h>

extern char **environ;

#define CHILD_ARG "--child-apply-and-store"
#define INHERITED_FD 3
#define SHM_SIZE 4096
#define SENTINEL_VALUE 0xa1u
#define POLL_USLEEP_US 2000
#define TIMEOUT_MS 5000

/* Shared-memory layout. Pre-touched by parent before spawn so post-apply
 * writes never trip a page-in syscall. The header carries the sentinel
 * + attempt-result fields; the rest of the page is reserved/unused. */
struct shm_region {
    volatile unsigned char sentinel;
    /* padding to align attempt fields at a stable offset */
    unsigned char _pad[7];
    volatile int attempt_rc;
    volatile int attempt_errno;
    volatile unsigned char attempt_completed;
};

static const char POLICY[] = "(version 2)\n(deny default)\n";

static long elapsed_ms(struct timespec *start) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return (now.tv_sec - start->tv_sec) * 1000
         + (now.tv_nsec - start->tv_nsec) / 1000000;
}

static int child_main(void) {
    /* FD INHERITED_FD is the shared backing file passed by the parent. */
    void *shm = mmap(NULL, SHM_SIZE, PROT_READ | PROT_WRITE,
                     MAP_SHARED, INHERITED_FD, 0);
    if (shm == MAP_FAILED) {
        /* stderr may itself be denied post-apply; best-effort. */
        fprintf(stderr, "child mmap failed: %s\n", strerror(errno));
        return 3;
    }
    struct shm_region *r = (struct shm_region *)shm;

    /* Apply the bare deny-default policy. sandbox_init compiles +
     * applies internally; semantically equivalent to
     * sandbox_compile_string + sandbox_apply for our purposes. */
    char *errbuf = NULL;
    #pragma clang diagnostic push
    #pragma clang diagnostic ignored "-Wdeprecated-declarations"
    int rc = sandbox_init(POLICY, 0, &errbuf);
    if (rc != 0) {
        if (errbuf) {
            fprintf(stderr, "sandbox_init failed: %s\n", errbuf);
            sandbox_free_error(errbuf);
        }
        _exit(2);
    }
    #pragma clang diagnostic pop

    /* Memory store of the sentinel — not a syscall. Visible to parent. */
    r->sentinel = (unsigned char)SENTINEL_VALUE;

    /* Perform one attempt — the same shape the C probe-runner will use
     * for each step. access(2) is the cheapest call we can make that
     * the kernel sandbox mediates; under (deny default) it returns -1
     * with errno set to a deny indication. We capture both via stack
     * locals (no allocation) and store into the pre-allocated region. */
    errno = 0;
    int a_rc = access("/etc/hosts", F_OK);
    int a_errno = errno;
    r->attempt_rc = a_rc;
    r->attempt_errno = a_errno;
    r->attempt_completed = 1;

    /* Spin with no further syscalls until SIGKILLed by parent. */
    while (1) {
        __asm__ __volatile__("" ::: "memory");
    }
    /* unreachable */
}

static int parent_main(const char *self_path) {
    /* Create an anonymous-ish backing file: open then immediately unlink
     * so the inode lives only as long as the open FDs reference it. */
    char path[] = "/tmp/pw-sentinel-XXXXXX";
    int fd = mkstemp(path);
    if (fd < 0) {
        fprintf(stderr, "mkstemp failed: %s\n", strerror(errno));
        return 1;
    }
    unlink(path);
    if (ftruncate(fd, SHM_SIZE) != 0) {
        fprintf(stderr, "ftruncate failed: %s\n", strerror(errno));
        close(fd);
        return 1;
    }

    void *shm = mmap(NULL, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (shm == MAP_FAILED) {
        fprintf(stderr, "parent mmap failed: %s\n", strerror(errno));
        close(fd);
        return 1;
    }
    struct shm_region *r = (struct shm_region *)shm;

    /* Pre-touch the page so the child's writes hit a resident page. */
    r->sentinel = 0;
    r->attempt_rc = 0;
    r->attempt_errno = 0;
    r->attempt_completed = 0;

    /* posix_spawn the child (re-exec of self) with the shm FD plumbed
     * to INHERITED_FD. POSIX_SPAWN_CLOEXEC_DEFAULT keeps stray FDs out. */
    posix_spawn_file_actions_t actions;
    posix_spawnattr_t attrs;
    if (posix_spawn_file_actions_init(&actions) != 0) {
        fprintf(stderr, "posix_spawn_file_actions_init failed\n");
        close(fd);
        return 1;
    }
    if (posix_spawnattr_init(&attrs) != 0) {
        fprintf(stderr, "posix_spawnattr_init failed\n");
        posix_spawn_file_actions_destroy(&actions);
        close(fd);
        return 1;
    }
    short flags = POSIX_SPAWN_CLOEXEC_DEFAULT;
    posix_spawnattr_setflags(&attrs, flags);
    posix_spawn_file_actions_adddup2(&actions, fd, INHERITED_FD);
    if (fd != INHERITED_FD) {
        posix_spawn_file_actions_addclose(&actions, fd);
    }

    char *child_argv[] = {
        (char *)self_path,
        (char *)CHILD_ARG,
        NULL,
    };
    pid_t pid = 0;
    int spawn_rc = posix_spawn(&pid, self_path, &actions, &attrs,
                               child_argv, environ);
    posix_spawn_file_actions_destroy(&actions);
    posix_spawnattr_destroy(&attrs);
    close(fd); /* parent no longer needs the FD; child has its dup. */

    if (spawn_rc != 0) {
        fprintf(stderr, "posix_spawn failed: %s\n", strerror(spawn_rc));
        return 1;
    }

    /* Poll for sentinel. */
    struct timespec start;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int observed = 0;
    while (1) {
        if (r->sentinel == SENTINEL_VALUE) {
            observed = 1;
            break;
        }
        if (elapsed_ms(&start) > TIMEOUT_MS) {
            break;
        }
        usleep(POLL_USLEEP_US);
    }

    /* Give the child a tiny grace window for the attempt store to land
     * after the sentinel (the writes are sequential and usually
     * complete in microseconds). */
    if (observed) {
        for (int i = 0; i < 50; i++) {
            if (r->attempt_completed == 1) {
                break;
            }
            usleep(POLL_USLEEP_US);
        }
    }

    /* Clean up child unconditionally. */
    kill(pid, SIGKILL);
    int status = 0;
    waitpid(pid, &status, 0);

    long elapsed = elapsed_ms(&start);
    if (observed) {
        printf("sentinel_observed=1 (elapsed=%ldms)\n", elapsed);
        if (r->attempt_completed == 1) {
            printf("attempt_rc=%d attempt_errno=%d\n",
                   r->attempt_rc, r->attempt_errno);
        } else {
            printf("attempt_rc=- attempt_errno=- (not recorded before SIGKILL)\n");
        }
        return 0;
    }
    printf("sentinel_observed=0 (timeout=%dms, child status=0x%x)\n",
           TIMEOUT_MS, status);
    return 1;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], CHILD_ARG) == 0) {
        return child_main();
    }
    /* Resolve our own executable path for the re-exec. */
    char self[PATH_MAX];
    uint32_t size = sizeof(self);
    if (_NSGetExecutablePath(self, &size) != 0) {
        fprintf(stderr, "_NSGetExecutablePath buffer too small\n");
        return 1;
    }
    return parent_main(self);
}

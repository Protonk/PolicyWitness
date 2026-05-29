/*
 * sentinel_harness — verify the post-apply shared-memory sentinel pattern
 * R8 from RUNNER-RESHAPE-PLAN.md depends on.
 *
 * The C probe-runner this plan introduces will apply the specimen policy
 * to itself and then communicate results to its parent via stores into a
 * pre-mapped shared-memory region (no further syscalls). This harness
 * verifies the load-bearing assumption: a process can apply a bare
 * `(deny default)` policy and then make memory stores observable to its
 * parent without invoking syscalls that the policy would deny.
 *
 * The harness is single-binary. It mmaps an anonymous shared region,
 * forks, has the child apply the policy and write a sentinel byte via a
 * memory store while spinning, and has the parent poll the shared region
 * for the sentinel value with usleep(2000). On success it prints
 * `sentinel_observed=1`; on timeout, `sentinel_observed=0 (timeout)`.
 *
 * Built on demand by tests/suites/witness_contract/shm_sentinel_under_deny_default.sh.
 */

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <signal.h>
#include <time.h>
#include <sandbox.h>

/* Bare `(deny default)` at SBPL v2 — the canonical worst case from the
 * downstream bug report. */
static const char POLICY[] = "(version 2)\n(deny default)\n";

#define SENTINEL_VALUE 0xa1u
#define SHM_SIZE 4096
#define POLL_USLEEP_US 2000
#define TIMEOUT_MS 5000

static long elapsed_ms(struct timespec *start) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return (now.tv_sec - start->tv_sec) * 1000
         + (now.tv_nsec - start->tv_nsec) / 1000000;
}

int main(void) {
    /* Anonymous shared mapping inherited across fork. */
    void *shm = mmap(NULL, SHM_SIZE, PROT_READ | PROT_WRITE,
                     MAP_SHARED | MAP_ANON, -1, 0);
    if (shm == MAP_FAILED) {
        fprintf(stderr, "mmap failed: %s\n", strerror(errno));
        return 1;
    }

    /* Pre-touch the page so the worker writes hit a resident page and
     * never trip a syscall-mediated page-in post-apply. */
    volatile unsigned char *p = (volatile unsigned char *)shm;
    p[0] = 0;

    pid_t pid = fork();
    if (pid < 0) {
        fprintf(stderr, "fork failed: %s\n", strerror(errno));
        return 1;
    }

    if (pid == 0) {
        /* Child: apply policy, store sentinel via memory write, spin. */
        char *errbuf = NULL;
        /* sandbox_init is marked deprecated but the public alternative
         * (sandbox_compile_string + sandbox_apply) requires libsandbox
         * via dlopen. For a verification harness, the deprecated API
         * keeps the code minimal and still proves the same point. */
        #pragma clang diagnostic push
        #pragma clang diagnostic ignored "-Wdeprecated-declarations"
        int rc = sandbox_init(POLICY, 0, &errbuf);
        if (rc != 0) {
            /* Best-effort error report; stderr may itself be denied. */
            if (errbuf) {
                fprintf(stderr, "sandbox_init failed: %s\n", errbuf);
                sandbox_free_error(errbuf);
            }
            _exit(2);
        }
        #pragma clang diagnostic pop

        /* Memory store — not a syscall. Should succeed even under
         * (deny default). The volatile ensures the compiler doesn't
         * elide the store. */
        p[0] = (unsigned char)SENTINEL_VALUE;

        /* Spin with no syscalls until SIGKILLed by parent. */
        while (1) {
            __asm__ __volatile__("" ::: "memory");
        }
        /* unreachable */
    }

    /* Parent: poll for the sentinel. */
    struct timespec start;
    clock_gettime(CLOCK_MONOTONIC, &start);

    int observed = 0;
    while (1) {
        if (p[0] == SENTINEL_VALUE) {
            observed = 1;
            break;
        }
        if (elapsed_ms(&start) > TIMEOUT_MS) {
            break;
        }
        usleep(POLL_USLEEP_US);
    }

    /* Clean up child unconditionally. */
    kill(pid, SIGKILL);
    int status = 0;
    waitpid(pid, &status, 0);

    if (observed) {
        printf("sentinel_observed=1 (elapsed=%ldms)\n", elapsed_ms(&start));
        return 0;
    }
    printf("sentinel_observed=0 (timeout=%dms, child status=0x%x)\n",
           TIMEOUT_MS, status);
    return 1;
}

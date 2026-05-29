/*
 * discovery_target — companion harness for empirical sandbox-filter-id
 * discovery.
 *
 * Applies a policy that uses one named filter kind on a known
 * discriminator value, then spins until SIGKILLed. A separate harness
 * (discover_filter_id.sh + sb_api_validator's RAW:<n> mode) queries this
 * process with candidate numeric filter type IDs against:
 *
 *   value_A = "PWDiscoveryTestValue"   — explicitly mentioned in the policy
 *   value_B = "PWUnusedDiscoveryValue" — not mentioned anywhere
 *
 * The pattern that identifies the correct filter ID for the named kind:
 *
 *   correct filter ID:  rc(value_A) == 1 (deny — policy matched and denied)
 *                       rc(value_B) == 0 (allow — policy default-allow)
 *   wrong filter ID:    either rc=-1/errno=EINVAL, or both queries return
 *                       the same value (the kernel ignored the filter and
 *                       fell through to default rules), or both deny.
 *
 * The discriminator pattern (deny, allow) is unique to the matching ID
 * unless the kernel has multiple equivalent IDs (we have not observed
 * this; report if you do).
 *
 * Invocation:
 *   ./discovery_target <sbpl_policy_string>
 *
 * The caller passes the policy as a single argv string so the harness
 * stays generic across filter discoveries. The policy is expected to
 * default-allow with one deny rule using the filter kind under test.
 *
 * Output:
 *   ready_pid=<pid>\n
 *   (then spins forever; caller SIGKILLs when done)
 *
 * The ready line lets the caller learn the pid without a separate
 * `ps` invocation and ensures the policy has been applied before any
 * sandbox_check is issued from the outside.
 */

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <sandbox.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr,
                "usage: %s <sbpl-policy-string>\n"
                "  applies the policy to self, prints ready_pid=<pid>, "
                "spins until SIGKILL\n",
                argv[0]);
        return 2;
    }
    const char *policy = argv[1];

    char *errbuf = NULL;
    #pragma clang diagnostic push
    #pragma clang diagnostic ignored "-Wdeprecated-declarations"
    int rc = sandbox_init(policy, 0, &errbuf);
    if (rc != 0) {
        fprintf(stderr, "sandbox_init failed: %s\n",
                errbuf ? errbuf : "(no message)");
        if (errbuf) sandbox_free_error(errbuf);
        return 3;
    }
    #pragma clang diagnostic pop

    /* Print ready line — this happens post-apply via stdout. The host's
     * pipe FD is inherited and stdout writes are typically allowed by
     * default-allow policies (we always pair this harness with default-
     * allow policies). */
    pid_t pid = getpid();
    printf("ready_pid=%d\n", pid);
    fflush(stdout);

    /* Spin without syscalls until killed. */
    while (1) {
        __asm__ __volatile__("" ::: "memory");
    }
    /* unreachable */
}

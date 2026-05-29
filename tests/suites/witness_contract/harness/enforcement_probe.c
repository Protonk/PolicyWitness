/*
 * enforcement_probe — discover sandbox filter IDs by comparing
 * sandbox_check verdicts against the kernel's actual enforcement.
 *
 * The premise of empirical filter-ID discovery via sandbox_check alone
 * is broken: the userland predicate is known to drift from actual
 * kernel enforcement for at least some op+filter combinations (BBX-001
 * is one documented case; we found another for path filters during the
 * Step 2 investigation). To recover a reliable methodology, we ask the
 * kernel directly:
 *
 *   1. Apply a policy that denies one specific value of one specific
 *      operation under one specific filter kind (named, not numeric).
 *   2. Perform the actual operation — a real bootstrap_look_up for
 *      mach-lookup, a real open(2) for file ops, etc. — and capture
 *      the kernel's verdict (kr / errno).
 *   3. Stay alive so a parent can query sandbox_check with candidate
 *      filter_type_ids against the same value and compare the userland
 *      predicate's verdicts to the kernel's actual answer.
 *
 * The "correct" filter ID is the one whose sandbox_check verdict
 * agrees with the kernel's actual enforcement. If no candidate agrees,
 * either sandbox_check is broken for that op+filter combination (the
 * BBX-001 class of anomaly) or the runner can't use sandbox_check as
 * the verdict source for this filter kind.
 *
 * Invocation:
 *   enforcement_probe mach_lookup <policy> <service-name>
 *
 * (We accept the operation kind on the command line so the same binary
 *  can grow more probe types — file ops, iokit ops — in the same
 *  shape.)
 *
 * Output (stdout, lines):
 *   ready_pid=<n>
 *   op=<probe>
 *   value=<value>
 *   attempt_rc=<n>          (0 success, anything else failure)
 *   attempt_errno=<n>       (errno after the call; 0 if not applicable)
 *   attempt_kr=<n>          (kern_return_t for mach probes; 0 otherwise)
 *   attempt_outcome=allow|deny
 *
 * Then spins until SIGKILLed.
 */

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <mach/mach.h>
#include <servers/bootstrap.h>
#include <sandbox.h>

extern mach_port_t bootstrap_port;

static int probe_mach_lookup(const char *service) {
    mach_port_t port = MACH_PORT_NULL;
    kern_return_t kr = bootstrap_look_up(bootstrap_port, (char *)service, &port);
    int allow = (kr == KERN_SUCCESS);
    /* For mach probes we report kr; errno isn't meaningful here. */
    printf("attempt_rc=%d\n", kr == KERN_SUCCESS ? 0 : 1);
    printf("attempt_errno=0\n");
    printf("attempt_kr=%d\n", (int)kr);
    printf("attempt_outcome=%s\n", allow ? "allow" : "deny");
    if (port != MACH_PORT_NULL) {
        mach_port_deallocate(mach_task_self(), port);
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr,
                "usage: %s <probe> <policy-sbpl-string> <value>\n"
                "  probe: mach_lookup\n"
                "  policy: SBPL source applied to self before the probe\n"
                "  value: target of the probe (mach service name, etc.)\n",
                argv[0]);
        return 2;
    }
    const char *probe = argv[1];
    const char *policy = argv[2];
    const char *value = argv[3];

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

    printf("ready_pid=%d\n", getpid());
    printf("op=%s\n", probe);
    printf("value=%s\n", value);

    if (strcmp(probe, "mach_lookup") == 0) {
        probe_mach_lookup(value);
    } else {
        fprintf(stderr, "unknown probe kind: %s\n", probe);
        return 2;
    }

    fflush(stdout);

    /* Spin until SIGKILLed. */
    while (1) {
        __asm__ __volatile__("" ::: "memory");
    }
    return 0;
}

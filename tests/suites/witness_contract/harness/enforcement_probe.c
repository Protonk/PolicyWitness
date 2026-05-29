/*
 * enforcement_probe — discover sandbox filter IDs by comparing
 * sandbox_check verdicts against the kernel's actual enforcement.
 *
 * The premise of empirical filter-ID discovery via sandbox_check alone
 * is broken: the userland predicate is known to drift from actual
 * kernel enforcement for at least some op+filter combinations (BBX-001
 * was one documented case; we corrected GLOBAL_NAME=16 → 2 by this
 * methodology). To recover a reliable methodology, we ask the kernel
 * directly:
 *
 *   1. Optional pre-apply baseline (probe-specific). For mach-lookup
 *      we don't need one — well-known services like cfprefsd always
 *      exist. For iokit_open we do — class presence varies across
 *      hardware (Apple Silicon vs Intel) and macOS versions, and
 *      "lookup returned null" post-apply is ambiguous between
 *      "policy denied" and "class doesn't exist on this host."
 *   2. Apply the policy that denies one specific value of one specific
 *      operation under one specific filter kind (named, not numeric).
 *   3. Perform the actual operation — real bootstrap_look_up for
 *      mach-lookup, real IOServiceOpen for iokit — and capture the
 *      kernel's verdict (kr / errno).
 *   4. Stay alive so a parent can query sandbox_check with candidate
 *      filter_type_ids against the same value and compare the userland
 *      predicate's verdicts to the kernel's actual answer.
 *
 * The "correct" filter ID is the one whose sandbox_check verdict
 * agrees with the kernel's actual enforcement.
 *
 * Invocation:
 *   enforcement_probe mach_lookup <policy> <service-name>
 *   enforcement_probe iokit_open <policy> <iokit-class-name>
 *   enforcement_probe sysctl_read <policy> <sysctl-name>
 *
 * Output (stdout, lines):
 *   ready_pid=<n>
 *   op=<probe>
 *   value=<value>
 *   baseline_outcome=allow|deny|missing      (probes that need it)
 *   baseline_kr=<n>                          (probes that need it)
 *   attempt_rc=<n>          (0 success, anything else failure)
 *   attempt_errno=<n>       (errno after the call; 0 if not applicable)
 *   attempt_kr=<n>          (kern_return_t for mach/iokit probes)
 *   attempt_outcome=allow|deny|missing
 *
 * Then spins until SIGKILLed.
 */

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/sysctl.h>
#include <unistd.h>
#include <mach/mach.h>
#include <servers/bootstrap.h>
#include <sandbox.h>
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>

extern mach_port_t bootstrap_port;

/* ---- mach_lookup ------------------------------------------------------- */

static int probe_mach_lookup(const char *service) {
    mach_port_t port = MACH_PORT_NULL;
    kern_return_t kr = bootstrap_look_up(bootstrap_port, (char *)service, &port);
    int allow = (kr == KERN_SUCCESS);
    printf("attempt_rc=%d\n", kr == KERN_SUCCESS ? 0 : 1);
    printf("attempt_errno=0\n");
    printf("attempt_kr=%d\n", (int)kr);
    printf("attempt_outcome=%s\n", allow ? "allow" : "deny");
    if (port != MACH_PORT_NULL) {
        mach_port_deallocate(mach_task_self(), port);
    }
    return 0;
}

/* ---- iokit_open -------------------------------------------------------- */

/* Returns 0 if the class is present on this host (baseline ok); non-zero
 * if it's missing — in which case we can't meaningfully probe enforcement.
 * Prints baseline_outcome/baseline_kr lines.
 *
 * "Baseline" here means: with no policy applied, can we look up and open
 * a service of this class? If lookup returns IO_OBJECT_NULL there's
 * nothing to probe (class genuinely absent). If lookup succeeds but the
 * open returns a non-success kr, the class exists but isn't openable by
 * us unsandboxed — we record baseline_outcome=deny and still proceed,
 * since the same observation post-apply will tell us whether the policy
 * changes that. */
static int probe_iokit_setup(const char *class_name) {
    CFDictionaryRef matching = IOServiceMatching(class_name);
    if (!matching) {
        printf("baseline_outcome=missing\n");
        printf("baseline_kr=0\n");
        return 1;
    }
    /* IOServiceGetMatchingService consumes the matching dict. */
    io_service_t svc = IOServiceGetMatchingService(kIOMainPortDefault, matching);
    if (svc == IO_OBJECT_NULL) {
        printf("baseline_outcome=missing\n");
        printf("baseline_kr=0\n");
        return 1;
    }
    io_connect_t conn = MACH_PORT_NULL;
    kern_return_t kr = IOServiceOpen(svc, mach_task_self(), 0, &conn);
    int allow = (kr == KERN_SUCCESS);
    printf("baseline_outcome=%s\n", allow ? "allow" : "deny");
    printf("baseline_kr=%d\n", (int)kr);
    if (conn != MACH_PORT_NULL) IOServiceClose(conn);
    IOObjectRelease(svc);
    return 0;
}

static int probe_iokit_open(const char *class_name) {
    CFDictionaryRef matching = IOServiceMatching(class_name);
    if (!matching) {
        printf("attempt_rc=1\n");
        printf("attempt_errno=0\n");
        printf("attempt_kr=0\n");
        printf("attempt_outcome=missing\n");
        return 0;
    }
    io_service_t svc = IOServiceGetMatchingService(kIOMainPortDefault, matching);
    if (svc == IO_OBJECT_NULL) {
        /* Lookup itself was denied (or class disappeared). Treat as deny
         * — the kernel's verdict on this op is "you can't reach this
         * service." */
        printf("attempt_rc=1\n");
        printf("attempt_errno=0\n");
        printf("attempt_kr=0\n");
        printf("attempt_outcome=deny\n");
        return 0;
    }

    io_connect_t conn = MACH_PORT_NULL;
    kern_return_t kr = IOServiceOpen(svc, mach_task_self(), 0, &conn);
    int allow = (kr == KERN_SUCCESS);
    printf("attempt_rc=%d\n", allow ? 0 : 1);
    printf("attempt_errno=0\n");
    printf("attempt_kr=%d\n", (int)kr);
    printf("attempt_outcome=%s\n", allow ? "allow" : "deny");

    if (conn != MACH_PORT_NULL) IOServiceClose(conn);
    IOObjectRelease(svc);
    return 0;
}

/* ---- sysctl_read ------------------------------------------------------- */

/* Pre-apply baseline: the sysctl exists if sysctlbyname returns 0 (we
 * pass a tiny buffer and don't actually care about the data). If the
 * call fails with ENOENT the sysctl isn't on this host. */
static int probe_sysctl_setup(const char *name) {
    char buf[256];
    size_t len = sizeof(buf);
    errno = 0;
    int rc = sysctlbyname(name, buf, &len, NULL, 0);
    int err = errno;
    if (rc != 0) {
        if (err == ENOENT) {
            printf("baseline_outcome=missing\n");
        } else {
            printf("baseline_outcome=deny\n");
        }
        printf("baseline_kr=0\n");
        return 1;
    }
    printf("baseline_outcome=allow\n");
    printf("baseline_kr=0\n");
    return 0;
}

static int probe_sysctl_read(const char *name) {
    char buf[256];
    size_t len = sizeof(buf);
    errno = 0;
    int rc = sysctlbyname(name, buf, &len, NULL, 0);
    int err = errno;
    int allow = (rc == 0);
    printf("attempt_rc=%d\n", rc);
    printf("attempt_errno=%d\n", err);
    printf("attempt_kr=0\n");
    printf("attempt_outcome=%s\n", allow ? "allow" : "deny");
    return 0;
}

/* ---- preferences_read -------------------------------------------------- */

/* Pre-apply baseline: a preference domain is "usable" iff it has at
 * least one key visible via CFPreferencesCopyKeyList. We don't care
 * which key — only that the domain isn't empty (would make post-apply
 * deny vs missing indistinguishable). */
static int probe_preferences_setup(const char *domain) {
    CFStringRef cfDomain = CFStringCreateWithCString(NULL, domain, kCFStringEncodingUTF8);
    if (!cfDomain) {
        printf("baseline_outcome=missing\n");
        printf("baseline_kr=0\n");
        return 1;
    }
    CFArrayRef keys = CFPreferencesCopyKeyList(cfDomain,
                                                kCFPreferencesCurrentUser,
                                                kCFPreferencesAnyHost);
    int has_keys = (keys != NULL && CFArrayGetCount(keys) > 0);
    if (keys) CFRelease(keys);
    CFRelease(cfDomain);
    if (!has_keys) {
        printf("baseline_outcome=missing\n");
        printf("baseline_kr=0\n");
        return 1;
    }
    printf("baseline_outcome=allow\n");
    printf("baseline_kr=0\n");
    return 0;
}

static int probe_preferences_read(const char *domain) {
    CFStringRef cfDomain = CFStringCreateWithCString(NULL, domain, kCFStringEncodingUTF8);
    if (!cfDomain) {
        printf("attempt_rc=1\n");
        printf("attempt_errno=0\n");
        printf("attempt_kr=0\n");
        printf("attempt_outcome=missing\n");
        return 0;
    }
    CFArrayRef keys = CFPreferencesCopyKeyList(cfDomain,
                                                kCFPreferencesCurrentUser,
                                                kCFPreferencesAnyHost);
    int allow = (keys != NULL && CFArrayGetCount(keys) > 0);
    if (keys) CFRelease(keys);
    CFRelease(cfDomain);
    printf("attempt_rc=%d\n", allow ? 0 : 1);
    printf("attempt_errno=0\n");
    printf("attempt_kr=0\n");
    printf("attempt_outcome=%s\n", allow ? "allow" : "deny");
    return 0;
}

/* ---- main -------------------------------------------------------------- */

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr,
                "usage: %s <probe> <policy-sbpl-string> <value>\n"
                "  probe: mach_lookup | iokit_open\n"
                "  policy: SBPL source applied to self before the probe\n"
                "  value: target of the probe (mach service name or\n"
                "         iokit class name)\n",
                argv[0]);
        return 2;
    }
    const char *probe = argv[1];
    const char *policy = argv[2];
    const char *value = argv[3];

    /* Pre-apply setup, if the probe needs it. We print baseline_*
     * lines BEFORE applying the policy so the parent can correlate
     * even if the probe later misbehaves. */
    int setup_failed = 0;
    if (strcmp(probe, "iokit_open") == 0) {
        setup_failed = (probe_iokit_setup(value) != 0);
    } else if (strcmp(probe, "sysctl_read") == 0) {
        setup_failed = (probe_sysctl_setup(value) != 0);
    } else if (strcmp(probe, "preferences_read") == 0) {
        setup_failed = (probe_preferences_setup(value) != 0);
    }
    if (setup_failed) {
        /* Target isn't usable on this host — can't probe meaningfully.
         * Still print ready/op/value so the caller can detect the
         * bailout gracefully. */
        printf("ready_pid=%d\n", getpid());
        printf("op=%s\n", probe);
        printf("value=%s\n", value);
        printf("attempt_outcome=missing\n");
        fflush(stdout);
        while (1) { __asm__ __volatile__("" ::: "memory"); }
    }

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
    } else if (strcmp(probe, "iokit_open") == 0) {
        probe_iokit_open(value);
    } else if (strcmp(probe, "sysctl_read") == 0) {
        probe_sysctl_read(value);
    } else if (strcmp(probe, "preferences_read") == 0) {
        probe_preferences_read(value);
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

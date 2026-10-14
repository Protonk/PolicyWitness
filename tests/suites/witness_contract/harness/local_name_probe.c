/*
 * local_name_probe — observe which SBPL mach-lookup filter governs the Mach
 * namespaces a user process can actually reach, for a target and an
 * independently exercised sibling, under a controlled policy.
 *
 * Modes:
 *   registered       <policy>   register target and sibling with bootstrap_register,
 *                               then apply the policy and look both up
 *   registered-after <policy>   apply the policy, then register both and look both up
 *   bundle           <policy>   run from inside an app bundle whose Contents/XPCServices
 *                               holds a copy of PWRunner.xpc; look the service up by
 *                               bootstrap_look_up and by xpc_connection_create
 *   subset                      try to create a bootstrap subset (report the result)
 *
 * A trailing "hold" argument keeps the process alive after the observations so
 * a parent can scan sandbox_check filter IDs against it (see verify_local_name.sh).
 * Lines: register <name>: kr=…, <label> lookup <name>: kr=… (allow|deny|…),
 * <label> xpc: …, sandbox_init: rc=…, pid=…. Nothing here is a PolicyWitness
 * result; it is the independent native observation the filter decision rests on.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <mach/mach.h>
#include <servers/bootstrap.h>
#include <sandbox.h>
#include <xpc/xpc.h>
#include <dispatch/dispatch.h>

extern mach_port_t bootstrap_port;

static const char *TARGET = "com.policywitness.probe.local-target";
static const char *SIBLING = "com.policywitness.probe.local-sibling";
static const char *SERVICE = "com.policywitness.policy-witness.PWRunner";

static const char *verdict(kern_return_t kr) {
    if (kr == KERN_SUCCESS) return "allow";
    if (kr == BOOTSTRAP_NOT_PRIVILEGED) return "deny";
    return bootstrap_strerror(kr);
}

static void look(const char *label, const char *name) {
    mach_port_t port = MACH_PORT_NULL;
    kern_return_t kr = bootstrap_look_up(bootstrap_port, (char *)name, &port);
    printf("%s lookup %s: kr=%d (%s)\n", label, name, (int)kr, verdict(kr));
    if (port != MACH_PORT_NULL) mach_port_deallocate(mach_task_self(), port);
}

static int reg(const char *name) {
    mach_port_t recv = MACH_PORT_NULL;
    if (mach_port_allocate(mach_task_self(), MACH_PORT_RIGHT_RECEIVE, &recv) != KERN_SUCCESS) return 1;
    if (mach_port_insert_right(mach_task_self(), recv, recv, MACH_MSG_TYPE_MAKE_SEND) != KERN_SUCCESS) return 1;
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    kern_return_t kr = bootstrap_register(bootstrap_port, (char *)name, recv);
#pragma clang diagnostic pop
    printf("register %s: kr=%d (%s)\n", name, (int)kr, kr == KERN_SUCCESS ? "ok" : verdict(kr));
    return kr == KERN_SUCCESS ? 0 : 1;
}

static void xpc_probe(const char *label) {
    xpc_connection_t connection = xpc_connection_create(SERVICE, NULL);
    xpc_connection_set_event_handler(connection, ^(xpc_object_t event) {
        if (xpc_get_type(event) == XPC_TYPE_ERROR)
            printf("%s xpc event: %s\n", label, xpc_dictionary_get_string(event, XPC_ERROR_KEY_DESCRIPTION));
    });
    xpc_connection_resume(connection);
    xpc_object_t message = xpc_dictionary_create(NULL, NULL, 0);
    xpc_dictionary_set_string(message, "probe", "local-name");
    xpc_object_t reply = xpc_connection_send_message_with_reply_sync(connection, message);
    if (xpc_get_type(reply) == XPC_TYPE_ERROR) {
        const char *text = xpc_dictionary_get_string(reply, XPC_ERROR_KEY_DESCRIPTION);
        /* Transport error text is an observation, not proof of service receipt
         * or of the boundary that refused the operation. */
        printf("%s xpc error: %s\n", label, text ? text : "no description");
    } else {
        printf("%s xpc: reply\n", label);
    }
    xpc_connection_cancel(connection);
}

static int apply(const char *policy) {
    char *error = NULL;
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    int rc = sandbox_init(policy, 0, &error);
#pragma clang diagnostic pop
    printf("sandbox_init: rc=%d%s%s\n", rc, error ? " " : "", error ? error : "");
    return rc;
}

static void hold_if_requested(int argc, char **argv) {
    printf("pid=%d\n", getpid());
    fflush(stdout);
    if (argc > 3 && strcmp(argv[3], "hold") == 0) for (;;) pause();
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: local_name_probe <mode> [policy] [hold]\n"); return 2; }
    const char *mode = argv[1];
    if (strcmp(mode, "subset") == 0) {
        mach_port_t subset = MACH_PORT_NULL;
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
        kern_return_t kr = bootstrap_subset(bootstrap_port, mach_task_self(), &subset);
#pragma clang diagnostic pop
        printf("bootstrap_subset: kr=%d (%s)\n", (int)kr, kr == KERN_SUCCESS ? "created" : mach_error_string(kr));
        return 0;
    }
    if (argc < 3) { fprintf(stderr, "usage: local_name_probe <mode> <policy> [hold]\n"); return 2; }
    const char *policy = argv[2];
    if (strcmp(mode, "registered") == 0) {
        if (reg(TARGET) || reg(SIBLING)) return 5;
        look("baseline", TARGET); look("baseline", SIBLING);
        if (apply(policy)) return 6;
        look("sandboxed", TARGET); look("sandboxed", SIBLING);
    } else if (strcmp(mode, "registered-after") == 0) {
        if (apply(policy)) return 6;
        int target_failed = reg(TARGET), sibling_failed = reg(SIBLING);
        if (target_failed || sibling_failed) printf("registration incomplete; lookups do not prove lookup-policy enforcement\n");
        look("sandboxed", TARGET); look("sandboxed", SIBLING);
    } else if (strcmp(mode, "bundle") == 0) {
        look("baseline", SERVICE); xpc_probe("baseline");
        if (apply(policy)) return 6;
        look("sandboxed", SERVICE); xpc_probe("sandboxed");
    } else {
        fprintf(stderr, "unknown mode %s\n", mode);
        return 2;
    }
    hold_if_requested(argc, argv);
    return 0;
}

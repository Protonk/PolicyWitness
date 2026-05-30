import Foundation
@testable import PWRunnerCore

// validateSandboxChecks treats filter.kind as a tristate:
//   - known kinds that need a value (path, global_name, local_name,
//     iokit_*, sysctl_name)         → require value
//   - known kind that takes no value (none)
//                                    → reject if value is supplied
//                                       (handled downstream; this layer
//                                       just leaves the value alone)
//   - unknown kinds (preference_domain, mach_port, etc.)
//                                    → accept silently; downstream
//                                       synthesizes prediction_unavailable
//
// The accept-and-skip rule for unknown kinds bounds the blast radius
// when a specimen mixes a recognized probe with one whose filter
// kind hasn't been verified yet: the unrecognized step doesn't kill
// the rest of the plan with bad_request.

private func mkStep(stepId: String,
                    operation: String,
                    filterKind: String,
                    filterValue: String?) -> PWRunnerProbeStep {
    return PWRunnerProbeStep(
        step_id: stepId,
        sandbox_check: PWRunnerSandboxCheck(
            operation: operation,
            filter: PWRunnerSandboxFilter(kind: filterKind, value: filterValue)
        ),
        attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts")
    )
}

func runFilterKindValidationTests(_ tk: TestKit) {
    tk.group("validateSandboxChecks") {

        tk.run("known kind with value passes") {
            let steps = [mkStep(stepId: "p1",
                                operation: "file-read-data",
                                filterKind: "path",
                                filterValue: "/etc/hosts")]
            try validateSandboxChecks(steps)
        }

        tk.run("known kind without value is rejected") {
            let steps = [mkStep(stepId: "p1",
                                operation: "file-read-data",
                                filterKind: "path",
                                filterValue: "")]
            try expectThrows({
                try validateSandboxChecks(steps)
            })
        }

        tk.run("none kind without value passes") {
            let steps = [mkStep(stepId: "p1",
                                operation: "network-outbound",
                                filterKind: "none",
                                filterValue: nil)]
            try validateSandboxChecks(steps)
        }

        tk.run("none kind with empty value passes (downstream coerces to nil)") {
            // Consumers commonly pass value:"" for kind=none. The
            // validator's wire requires no filter_value for NONE, so
            // CWorkerOrchestrator nils it before sending. The
            // request-shape layer accepts the empty string rather
            // than rejecting up front.
            let steps = [mkStep(stepId: "p1",
                                operation: "network-outbound",
                                filterKind: "none",
                                filterValue: "")]
            try validateSandboxChecks(steps)
        }

        tk.run("unknown filter kind is accepted (per-step skip downstream)") {
            // preference_domain isn't in knownFilterKinds; the step
            // builder synthesizes prediction_unavailable for it
            // rather than killing the whole plan with bad_request.
            let steps = [mkStep(stepId: "p1",
                                operation: "user-preference-read",
                                filterKind: "preference_domain",
                                filterValue: "com.apple.Finder")]
            try validateSandboxChecks(steps)
        }

        tk.run("unknown kind without value is also accepted") {
            // We don't apply the value-required rule to kinds we
            // don't know — we wouldn't know what to require.
            let steps = [mkStep(stepId: "p1",
                                operation: "mach-lookup",
                                filterKind: "mach_port",
                                filterValue: nil)]
            try validateSandboxChecks(steps)
        }

        tk.run("empty operation still kills the plan") {
            // Operation is required regardless of filter kind.
            let steps = [mkStep(stepId: "p1",
                                operation: "",
                                filterKind: "path",
                                filterValue: "/etc/hosts")]
            try expectThrows({
                try validateSandboxChecks(steps)
            })
        }
    }

    tk.group("validateProbePlanForCWorker") {

        tk.run("duplicate step_id is still a plan-killer") {
            // Joining outputs back to steps by step_id requires
            // unique ids; the orchestrator's Dictionary construction
            // would crash otherwise.
            let steps = [
                PWRunnerProbeStep(
                    step_id: "dup",
                    sandbox_check: PWRunnerSandboxCheck(
                        operation: "file-read-data",
                        filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")
                    ),
                    attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts")
                ),
                PWRunnerProbeStep(
                    step_id: "dup",
                    sandbox_check: PWRunnerSandboxCheck(
                        operation: "file-read-data",
                        filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")
                    ),
                    attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts")
                ),
            ]
            let err = CWorkerOrchestrator.validateProbePlanForCWorker(steps)
            try expectNotNil(err, "duplicate step_id must be rejected")
            if let err = err {
                try expectContains(err, "duplicate step_id")
            }
        }

        tk.run("unknown attempt kind is NOT a plan-killer") {
            // Symmetric to the unknown-filter-kind behavior: the
            // unrecognized step downgrades to per-step skip in the
            // step builder rather than killing sibling steps.
            let steps = [
                PWRunnerProbeStep(
                    step_id: "good",
                    sandbox_check: PWRunnerSandboxCheck(
                        operation: "file-read-data",
                        filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")
                    ),
                    attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts")
                ),
                PWRunnerProbeStep(
                    step_id: "unknown_attempt",
                    sandbox_check: PWRunnerSandboxCheck(
                        operation: "iokit-open-user-client",
                        filter: PWRunnerSandboxFilter(kind: "none", value: nil)
                    ),
                    attempt: PWRunnerAttempt(kind: "iokit", action: "open", target: "irrelevant")
                ),
            ]
            try expectNil(CWorkerOrchestrator.validateProbePlanForCWorker(steps))
        }
    }
}

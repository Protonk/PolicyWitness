import Foundation
@testable import PWRunnerCore

// Request meaning checks reject unknown vocabulary and ineffective fields.

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

        tk.run("none kind with even an empty value is rejected") {
            let steps = [mkStep(stepId: "p1",
                                operation: "network-outbound",
                                filterKind: "none",
                                filterValue: "")]
            try expectThrows { try validateSandboxChecks(steps) }
        }

        tk.run("unknown filter kind refuses the request") {
            let steps = [mkStep(stepId: "p1",
                                operation: "user-preference-read",
                                filterKind: "preference_domain",
                                filterValue: "com.apple.Finder")]
            try expectThrows { try validateSandboxChecks(steps) }
        }

        tk.run("unknown kind without value is rejected") {
            let steps = [mkStep(stepId: "p1",
                                operation: "mach-lookup",
                                filterKind: "mach_port",
                                filterValue: nil)]
            try expectThrows { try validateSandboxChecks(steps) }
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

    tk.group("requestMeaningFailure") {

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
            let err = requestMeaningFailure(PWRunnerRunSpec(specimen_id: "meaning", policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)"), probe_plan: steps))
            try expectNotNil(err, "duplicate step_id must be rejected")
            if let err = err {
                try expectEqual(err.code, "duplicate_step_id")
            }
        }

        tk.run("unknown attempt refuses the whole plan") {
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
            try expectNotNil(requestMeaningFailure(PWRunnerRunSpec(specimen_id: "meaning", policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)"), probe_plan: steps)))
        }
    }
}

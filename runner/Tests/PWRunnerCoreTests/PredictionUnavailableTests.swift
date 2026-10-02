import Foundation
@testable import PWRunnerCore

// Covers the host's query planning: the shared (operation, filter_kind)
// exclusion set in ProbeRunner.swift and the unrecognized-filter exclusion,
// with literal expectations independent of the production set. An excluded
// step receives no validator probe and records the exclusion code the step
// builder renders as its `query_plan:*` limitation.

private func makeCheck(operation: String,
                       filterKind: String,
                       filterValue: String) -> PWRunnerSandboxCheck {
    return PWRunnerSandboxCheck(
        operation: operation,
        filter: PWRunnerSandboxFilter(kind: filterKind, value: filterValue)
    )
}

func runPredictionUnavailableTests(_ tk: TestKit) {
    tk.group("predictionUnavailableQueryPlanning") {
        // Literal expectations are independent of the shared production set.
        let exclusions = [
            ("iokit-open-service", "iokit_registry_entry_class", "prediction_unavailable_pair",
             "prediction unavailable for this operation and filter"),
            ("iokit-open-user-client", "iokit_user_client_class", "prediction_unavailable_pair",
             "prediction unavailable for this operation and filter"),
            ("sysctl-read", "sysctl_name", "prediction_unavailable_pair",
             "prediction unavailable for this operation and filter"),
            ("file-read-data", "future_filter", "unrecognized_filter_kind",
             "prediction unavailable for unrecognized filter kind"),
        ]
        for (operation, kind, code, reason) in exclusions {
            tk.run("excludes \(operation) + \(kind)") {
                let step = PWRunnerProbeStep(step_id: "excluded", sandbox_check:
                    makeCheck(operation: operation, filterKind: kind, filterValue: "value"),
                    attempt: PWRunnerAttempt(kind: "sysctl", action: "read", target: "kern.osrelease"))
                let decisions = planValidatorQueries([step])
                try expectEqual(decisions.count, 1)
                try expectEqual(decisions[0].stepId, "excluded")
                try expectNil(decisions[0].probe)
                try expectEqual(decisions[0].exclusionCode, code)
                try expectEqual(decisions[0].exclusionReason, reason)
            }
        }
        tk.run("known filter with another operation retains ordinary query") {
            let step = PWRunnerProbeStep(step_id: "query", sandbox_check:
                makeCheck(operation: "sysctl-write", filterKind: "sysctl_name", filterValue: "kern.hostname"),
                attempt: PWRunnerAttempt(kind: "sysctl", action: "read", target: "kern.osrelease"))
            let decisions = planValidatorQueries([step])
            try expectEqual(decisions.count, 1)
            try expectNil(decisions[0].exclusionReason)
            try expectNil(decisions[0].exclusionCode)
            guard let probe = decisions[0].probe else { throw TestFailure(message: "ordinary query missing") }
            try expectEqual(probe.stepId, "query")
            try expectEqual(probe.operation, "sysctl-write")
            try expectEqual(probe.filterType, "SYSCTL_NAME")
            try expectEqual(probe.filterValue, "kern.hostname")
        }
    }
}

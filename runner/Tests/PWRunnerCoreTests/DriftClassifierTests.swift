import Darwin
import Foundation
@testable import PWRunnerCore

// Constructed interpretation controls. These inputs and expectations are chosen
// from the public scope/attribution promises; they do not establish native causes.
private func comparisonCheck(_ prediction: String = "allow", operation: String = "file-read-data",
                             target: String = "/private/tmp/comparison", filter: String = "path") -> PWRunnerSandboxCheckResult {
    var result = PWRunnerSandboxCheckResult(rc: prediction == "allow" ? 0 : 1,
        outcome: prediction, pid: 42, operation: operation, scope: "post_sandbox",
        filter_kind: filter, filter_value: target)
    result.result_source = "validator"
    result.native_rc = result.rc
    return result
}

private func comparisonAttempt(kind: String = "file", action: String = "open_read",
                               target: String = "/private/tmp/comparison", outcome: String = "ok",
                               errno: Int? = nil, error: String? = nil,
                               child: Int? = nil) -> PWRunnerAttemptResult {
    var result = PWRunnerAttemptResult(rc: outcome == "ok" ? 0 : 1, errno: errno,
        outcome: outcome, error: error, requested_path: target, child_pid: child)
    result.requested_kind = kind
    result.requested_action = action
    result.result_source = "worker"
    return result
}

func runDriftClassifierTests(_ tk: TestKit) {
    tk.group("comparison: supported conclusions and independent limits") {
        for (prediction, conclusion, drift) in [("allow", "agreement", false), ("deny", "disagreement", true)] {
            tk.run("matched read success under \(prediction) retains a limited \(conclusion)") {
                let result = computeComparison(sandboxCheck: comparisonCheck(prediction), attempt: comparisonAttempt())
                try expectEqual(result.scope, "submitted_operation_and_target")
                try expectEqual(result.conclusion, conclusion)
                try expectEqual(result.drift, drift)
                try expectEqual(result.operation_relation, "matched")
                try expectEqual(result.target_relation, "same_submitted")
                try expectEqual(result.observation, "succeeded")
                try expectEqual(result.observation_basis, "completed_worker_status")
                try expectEqual(Set(result.limitations), Set(["query_attempt_order_unestablished",
                    "state_stability_unestablished", "runtime_target_identity_unestablished"]))
            }
        }
        for prediction in ["allow", "deny"] {
            for number in [Int(EPERM), Int(EACCES)] {
                tk.run("\(prediction) plus permission errno \(number) cannot establish enforcement agreement") {
                    let result = computeComparison(sandboxCheck: comparisonCheck(prediction),
                        attempt: comparisonAttempt(outcome: "open_failed", errno: number))
                    try expectNil(result.drift)
                    try expectEqual(result.conclusion, prediction == "deny" ? "directional_consistency" : "unavailable")
                    try expectEqual(result.observation, "permission_failure")
                    try expectEqual(result.observation_basis, "permission_errno")
                    try expectTrue(result.limitations.contains("sandbox_attribution_unestablished"))
                }
            }
        }
        tk.run("deny for A and successful B cannot establish disagreement") {
            let result = computeComparison(sandboxCheck: comparisonCheck("deny", target: "/A"),
                attempt: comparisonAttempt(target: "/B"))
            try expectNil(result.drift)
            try expectEqual(result.prediction, "deny")
            try expectEqual(result.observation, "succeeded")
            try expectEqual(result.target_relation, "different_submitted")
        }
        tk.run("same target with a different queried operation cannot establish disagreement") {
            let result = computeComparison(sandboxCheck: comparisonCheck("deny", operation: "file-write-data"),
                attempt: comparisonAttempt())
            try expectNil(result.drift)
            try expectEqual(result.operation_relation, "different")
            try expectEqual(result.target_relation, "same_submitted")
        }
        tk.run("missing channels and mismatched scope retain all known reasons") {
            var query = comparisonCheck("deny", operation: "file-write-data", target: "/A")
            query.result_source = "synthetic"
            query.missing_reason = "validator_no_verdict"
            var attempt = comparisonAttempt(target: "/B")
            attempt.result_source = "synthetic"
            attempt.missing_reason = "slot_incomplete"
            let result = computeComparison(sandboxCheck: query, attempt: attempt)
            try expectNil(result.drift)
            try expectEqual(result.prediction, "unavailable")
            try expectEqual(result.observation, "unavailable")
            for reason in ["prediction:validator_no_verdict", "attempt:slot_incomplete",
                           "operation:different", "target:different_submitted"] {
                try expectTrue(result.limitations.contains(reason), reason)
            }
        }
        tk.run("a validator error preserves a completed success without inventing a prediction") {
            let result = computeComparison(sandboxCheck: comparisonCheck("error"), attempt: comparisonAttempt())
            try expectNil(result.drift)
            try expectEqual(result.observation, "succeeded")
            try expectTrue(result.limitations.contains("prediction:no_usable_verdict"))
        }
        tk.run("old records cannot acquire a derivation from matching outcome labels") {
            var query = comparisonCheck()
            query.result_source = nil
            var attempt = comparisonAttempt()
            attempt.result_source = nil
            attempt.requested_kind = nil
            attempt.requested_action = nil
            let result = computeComparison(sandboxCheck: query, attempt: attempt)
            try expectNil(result.drift)
            try expectEqual(result.operation_relation, "unresolved")
            try expectEqual(result.observation, "unavailable")
        }
        tk.run("compound create does not claim a complete single-operation comparison") {
            let result = computeComparison(sandboxCheck: comparisonCheck(operation: "file-write-data"),
                attempt: comparisonAttempt(action: "create"))
            try expectNil(result.drift)
            try expectEqual(result.observation, "succeeded")
            try expectTrue(result.limitations.contains("compound_attempt"))
        }
        tk.run("broad exec queries retain unresolved operation scope") {
            let result = computeComparison(sandboxCheck: comparisonCheck(operation: "process-exec*"),
                attempt: comparisonAttempt(kind: "exec", action: "spawn", child: 123))
            try expectNil(result.drift)
            try expectEqual(result.operation_relation, "unresolved")
            try expectEqual(result.observation_basis, "spawned_child")
        }
        tk.run("a spawned child supplies spawn success beside a failed exec result") {
            let result = computeComparison(sandboxCheck: comparisonCheck(operation: "process-exec"),
                attempt: comparisonAttempt(kind: "exec", action: "spawn", outcome: "exec_failed", child: 123))
            try expectEqual(result.drift, false)
            try expectEqual(result.observation_basis, "spawned_child")
            try expectTrue(result.limitations.contains("exec_result_failed_after_spawn"))
            try expectTrue(result.limitations.contains("sandbox_attribution_unestablished"))
        }
        for filter in ["none", "local_name"] {
            tk.run("\(filter) does not certify a lookup target's namespace") {
                let result = computeComparison(sandboxCheck: comparisonCheck("deny", operation: "mach-lookup", filter: filter),
                    attempt: comparisonAttempt(kind: "mach_lookup", action: "bootstrap_look_up"))
                try expectNil(result.drift)
                try expectEqual(result.target_relation, "unresolved")
            }
        }
        for (message, observation) in [("bootstrap_look_up: kr=1100", "permission_failure"),
                                       ("bootstrap_look_up: kr=11000", "other_failure"),
                                       ("task_get_special_port: kr=1100", "other_failure")] {
            tk.run("native message \(message) retains its limited meaning") {
                let result = computeComparison(sandboxCheck: comparisonCheck("deny", operation: "mach-lookup", filter: "global_name"),
                    attempt: comparisonAttempt(kind: "mach_lookup", action: "bootstrap_look_up", outcome: "lookup_failed", error: message))
                try expectNil(result.drift)
                try expectEqual(result.observation, observation)
                try expectTrue(result.limitations.contains("sandbox_attribution_unestablished"))
            }
        }
        for number in [Int(ENOENT), Int(EINVAL), 123456] {
            tk.run("sysctl errno \(number) cannot become a strong sandbox denial") {
                let result = computeComparison(sandboxCheck: comparisonCheck(operation: "sysctl-read", filter: "sysctl_name"),
                    attempt: comparisonAttempt(kind: "sysctl", action: "read", outcome: "sysctl_failed", errno: number))
                try expectNil(result.drift)
                try expectEqual(result.observation, "other_failure")
            }
        }
        tk.run("new comparison and submitted provenance survive Codable without changing native fields") {
            let query = comparisonCheck("deny")
            let attempt = comparisonAttempt(outcome: "open_failed", errno: Int(EACCES))
            let comparison = computeComparison(sandboxCheck: query, attempt: attempt)
            let step = PWRunnerStepResult(step_id: "s", sandbox_check: query, attempt: attempt,
                drift: comparison.drift, comparison: comparison)
            let data = try pwRunnerEncodeJSON(step)
            let decoded = try pwRunnerDecodeJSON(PWRunnerStepResult.self, from: data)
            try expectEqual(decoded.comparison?.conclusion, "directional_consistency")
            try expectEqual(decoded.comparison?.limitations, comparison.limitations)
            try expectEqual(decoded.attempt.requested_kind, "file")
            try expectEqual(decoded.attempt.errno, Int(EACCES))
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            try expectTrue(json?["drift"] is NSNull)
        }
    }
    tk.group("host path provenance") {
        tk.run("later host disappearance is distinct from an earlier supplied validator record") {
            let path = "/private/tmp/pw-path-phase-" + UUID().uuidString
            FileManager.default.createFile(atPath: path, contents: Data("before".utf8))
            defer { try? FileManager.default.removeItem(atPath: path) }
            let step = PWRunnerStepResult(step_id: "s", sandbox_check: comparisonCheck(target: path),
                attempt: comparisonAttempt(target: path))
            let before = enrichPathDiagnostics(steps: [step])[0]
            try expectNotNil(before.sandbox_check.path_diagnostics?.realpath_resolved)
            try FileManager.default.removeItem(atPath: path)
            let after = enrichPathDiagnostics(steps: [step])[0]
            try expectEqual(after.sandbox_check.outcome, "allow")
            try expectNil(after.sandbox_check.path_diagnostics?.realpath_resolved)
            try expectEqual(after.sandbox_check.path_diagnostics?.observer, "runner_host")
            try expectEqual(after.sandbox_check.path_diagnostics?.phase, "after_orchestration")
            try expectNil(after.comparison) // enrichment cannot invent comparison evidence
        }
    }
}

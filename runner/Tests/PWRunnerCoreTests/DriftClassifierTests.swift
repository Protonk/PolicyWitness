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
    tk.group("typed comparison obligations") {
        tk.run("ordered_difference_does_not_imply_drift even with empty rendered labels") {
            let evidence = comparisonEvidence(sandboxCheck: comparisonCheck("deny"), attempt: comparisonAttempt(), order: .queryFirst)
            var wire = evidence.comparison
            wire.limitations = []
            try expectEqual(evidence.conclusion, "unavailable")
            try expectEqual(wire.conclusion, "unavailable")
            try expectNil(wire.drift)
        }
        tk.run("same_target_unlink_allow_ordered_is_agreement and renderer follows evidence") {
            for order: ComparisonOrder in [.unestablished, .queryFirst] {
                for verdict in ["allow", "deny"] {
                    let evidence = comparisonEvidence(sandboxCheck: comparisonCheck(verdict, operation: "file-write-unlink"),
                        attempt: comparisonAttempt(action: "unlink"), order: order)
                    let wire = evidence.comparison
                    try expectEqual(wire.limitations, evidence.renderLimitations())
                    try expectEqual(wire.conclusion, order == .queryFirst && verdict == "allow" ? "agreement" : "unavailable")
                    try expectEqual(wire.limitations.contains("attempt_mutation_order_unestablished"), order == .unestablished)
                }
            }
        }
    }
    tk.group("comparison: supported conclusions and independent limits") {
        for (prediction, conclusion, drift): (String, String, Bool?) in [("allow", "agreement", false), ("deny", "unavailable", nil)] {
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
        tk.run("native exec query compares target admission with observed spawn") {
            let result = computeComparison(sandboxCheck: comparisonCheck(operation: "process-exec*"),
                attempt: comparisonAttempt(kind: "exec", action: "spawn", child: 123))
            try expectEqual(result.drift, false)
            try expectEqual(result.operation_relation, "matched")
            try expectEqual(result.observation_basis, "spawned_child")
            try expectTrue(result.limitations.contains("exec_query_not_full_spawn_prediction"))
        }
        tk.run("other wildcard exec queries remain unresolved") {
            let result = computeComparison(sandboxCheck: comparisonCheck(operation: "process*"),
                attempt: comparisonAttempt(kind: "exec", action: "spawn", child: 123))
            try expectNil(result.drift)
            try expectEqual(result.operation_relation, "unresolved")
            try expectTrue(result.limitations.contains("broad_query_operation"))
        }
        tk.run("an accepted interpreter query cannot substitute for target admission") {
            let result = computeComparison(sandboxCheck: comparisonCheck("deny", operation: "process-exec-interpreter"),
                attempt: comparisonAttempt(kind: "exec", action: "spawn", child: 123))
            try expectNil(result.drift)
            try expectEqual(result.operation_relation, "different")
            try expectEqual(result.observation_basis, "spawned_child")
        }
        tk.run("a rejected bare exec query preserves spawn without a comparison") {
            let result = computeComparison(sandboxCheck: comparisonCheck("unsupported_operation", operation: "process-exec"),
                attempt: comparisonAttempt(kind: "exec", action: "spawn", child: 123))
            try expectNil(result.drift)
            try expectEqual(result.prediction, "unavailable")
            try expectEqual(result.observation, "succeeded")
        }
        tk.run("a spawned child supplies spawn success beside a failed exec result") {
            let result = computeComparison(sandboxCheck: comparisonCheck(operation: "process-exec*"),
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
    tk.group("unordered target mutation") {
        for prediction in ["allow", "deny"] {
            tk.run("same_target_unlink_\(prediction)_unordered_is_unavailable") {
                let result = computeComparison(sandboxCheck: comparisonCheck(prediction, operation: "file-write-unlink"),
                    attempt: comparisonAttempt(action: "unlink"))
                try expectEqual(result.prediction, prediction)
                try expectEqual(result.observation, "succeeded")
                try expectEqual(result.conclusion, "unavailable")
                try expectNil(result.drift)
                try expectTrue(result.limitations.contains("attempt_mutation_order_unestablished"))
                try expectFalse(result.limitations.contains("host_path_resolution_changed"))
            }
        }
        tk.run("open_write_allow_unordered_keeps_agreement") {
            let result = computeComparison(sandboxCheck: comparisonCheck(operation: "file-write-data"),
                attempt: comparisonAttempt(action: "open_write"))
            try expectEqual(result.conclusion, "agreement")
            try expectEqual(result.drift, false)
            try expectFalse(result.limitations.contains("attempt_mutation_order_unestablished"))
        }
        tk.run("mutation limitation requires a planned path query and a successful worker unlink of that target") {
            var synthetic = comparisonAttempt(action: "unlink")
            synthetic.result_source = "synthetic"
            let rows: [(PWRunnerSandboxCheckResult, PWRunnerAttemptResult, String?)] = [
                (comparisonCheck(target: "/A"), comparisonAttempt(action: "unlink", target: "/B"), nil),
                (comparisonCheck(), comparisonAttempt(action: "unlink", outcome: "unlink_failed", errno: Int(EPERM)), nil),
                (comparisonCheck(), synthetic, nil),
                (comparisonCheck(filter: "global_name"), comparisonAttempt(action: "unlink"), nil),
                (comparisonCheck(), comparisonAttempt(action: "unlink"), "path_unresolved_at_planning"),
            ]
            for (query, attempt, exclusion) in rows {
                let result = computeComparison(sandboxCheck: query, attempt: attempt, queryExclusionReason: exclusion)
                try expectFalse(result.limitations.contains("attempt_mutation_order_unestablished"))
            }
        }
        tk.run("earlier unlink remains relevant after recreation and affects only its submitted target") {
            // Constructed slots pin the join in plan order, independently of
            // the order in which slot records arrive. No native claim here.
            let path = "/etc/hosts"
            let rows = [("remove", "unlink", path), ("recreate", "create", path),
                        ("read", "open_read", path), ("other", "open_read", "/etc/passwd")]
            let steps = rows.map { id, action, target in
                PWRunnerProbeStep(step_id: id, sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                    filter: PWRunnerSandboxFilter(kind: "path", value: target)),
                    attempt: PWRunnerAttempt(kind: "file", action: action, target: target))
            }
            let slots = rows.reversed().map { id, _, target in
                CWorkerSlotResult(stepId: id, rc: 0, errnoVal: 0, observedPath: target, error: nil,
                    completed: true, childPid: nil, childExitCode: nil, childTermSignal: nil,
                    childStdout: nil, childStderr: nil)
            }
            let worker = CWorkerOutput(workerPid: 42, readyByteReceived: true, applied: true,
                applyRC: 0, applyErrno: 0, done: true, exitCode: 0, slots: slots)
            let verdicts = rows.map { id, _, target in
                ValidatorVerdict(stepId: id, operation: "file-read-data", filterType: "PATH",
                    filterValue: target, rc: 0, errnoVal: 0, outcome: "allow", rawLine: "constructed verdict")
            }
            let results = buildStepResults(probePlan: steps, queryPlan: planValidatorQueries(steps),
                workerOutput: worker, validatorOutput: ValidatorOutput(validatorPid: 43, verdicts: verdicts))
            try expectEqual(results[2].comparison?.conclusion, "unavailable")
            try expectNil(results[2].drift)
            try expectTrue(results[2].comparison!.limitations.contains("attempt_mutation_order_unestablished"))
            try expectEqual(results[3].comparison?.conclusion, "agreement")
            try expectEqual(results[3].drift, false)
            try expectFalse(results[3].comparison!.limitations.contains("attempt_mutation_order_unestablished"))
        }
        tk.run("another step's unlink of the queried target supplies the limitation regardless of position") {
            let removal = comparisonAttempt(action: "unlink")
            for attempts in [[removal], [comparisonAttempt(), removal], [removal, comparisonAttempt(action: "open_write")]] {
                let result = computeComparison(sandboxCheck: comparisonCheck(), attempt: comparisonAttempt(),
                    runAttempts: attempts)
                try expectEqual(result.conclusion, "unavailable")
                try expectNil(result.drift)
                try expectTrue(result.limitations.contains("attempt_mutation_order_unestablished"))
            }
            let other = computeComparison(sandboxCheck: comparisonCheck(), attempt: comparisonAttempt(),
                runAttempts: [comparisonAttempt(action: "unlink", target: "/B")])
            try expectEqual(other.conclusion, "agreement")
            try expectFalse(other.limitations.contains("attempt_mutation_order_unestablished"))
        }
        // Constructed slots and verdicts joined through the production builder.
        // No native claim: the rows pin the join, not sandbox behavior.
        func joinedRun(_ rows: [(id: String, action: String, target: String)],
                       verdict: String = "allow") -> [PWRunnerStepResult] {
            let operations = ["open_read": "file-read-data", "unlink": "file-write-unlink",
                              "create": "file-write-data"]
            let steps = rows.map { row in
                PWRunnerProbeStep(step_id: row.id, sandbox_check: PWRunnerSandboxCheck(operation: operations[row.action]!,
                    filter: PWRunnerSandboxFilter(kind: "path", value: row.target)),
                    attempt: PWRunnerAttempt(kind: "file", action: row.action, target: row.target))
            }
            let slots = rows.map { row in
                CWorkerSlotResult(stepId: row.id, rc: 0, errnoVal: 0, observedPath: row.target, error: nil,
                    completed: true, childPid: nil, childExitCode: nil, childTermSignal: nil,
                    childStdout: nil, childStderr: nil)
            }
            let worker = CWorkerOutput(workerPid: 42, readyByteReceived: true, applied: true,
                applyRC: 0, applyErrno: 0, done: true, exitCode: 0, slots: slots)
            let verdicts = rows.map { row in
                ValidatorVerdict(stepId: row.id, operation: operations[row.action]!, filterType: "PATH",
                    filterValue: row.target, rc: verdict == "allow" ? 0 : 1, errnoVal: 0,
                    outcome: verdict, rawLine: "constructed verdict")
            }
            return buildStepResults(probePlan: steps, queryPlan: planValidatorQueries(steps),
                workerOutput: worker, validatorOutput: ValidatorOutput(validatorPid: 43, verdicts: verdicts))
        }
        tk.run("later unlink in the run is a confound for earlier rows naming its target") {
            // With unestablished order the worker can finish every attempt before
            // the validator's first query; step position does not bound the confound.
            let results = joinedRun([("read", "open_read", "/etc/hosts"), ("other", "open_read", "/etc/passwd"),
                                     ("remove", "unlink", "/etc/hosts")])
            try expectEqual(results[0].comparison?.conclusion, "unavailable")
            try expectNil(results[0].drift)
            try expectTrue(results[0].comparison!.limitations.contains("attempt_mutation_order_unestablished"))
            try expectEqual(results[1].comparison?.conclusion, "agreement")
            try expectEqual(results[1].drift, false)
            try expectFalse(results[1].comparison!.limitations.contains("attempt_mutation_order_unestablished"))
            try expectEqual(results[2].comparison?.conclusion, "unavailable")
            try expectTrue(results[2].comparison!.limitations.contains("attempt_mutation_order_unestablished"))
        }
        tk.run("buildStepResults never establishes order: deny beside a successful read stays unavailable") {
            let results = joinedRun([("read", "open_read", "/etc/hosts")], verdict: "deny")
            try expectEqual(results[0].comparison?.prediction, "deny")
            try expectEqual(results[0].comparison?.observation, "succeeded")
            try expectEqual(results[0].comparison?.conclusion, "unavailable")
            try expectNil(results[0].drift)
            try expectFalse(results[0].comparison!.limitations.contains("attempt_mutation_order_unestablished"))
        }
    }
    tk.group("host path provenance") {
        for state in ["absent", "present", "recreated", "excluded"] {
            tk.run("later \(state) resolution appends only supported observations without reclassification") {
                let path = "/private/tmp/pw-path-enrichment-" + UUID().uuidString
                FileManager.default.createFile(atPath: path, contents: Data("before".utf8))
                defer { try? FileManager.default.removeItem(atPath: path) }
                var query = comparisonCheck(target: path)
                if state == "excluded" {
                    // The planner records an exclusion as its own outcome sentinel.
                    query.outcome = SandboxCheckOutcome.predictionUnavailable
                    query.rc = -1
                    query.native_rc = nil
                    query.result_source = "synthetic"
                    query.missing_reason = "query_not_requested"
                }
                let attempt = comparisonAttempt(target: path)
                let comparison = computeComparison(sandboxCheck: query, attempt: attempt,
                    queryExclusionReason: state == "excluded" ? "path_unresolved_at_planning" : nil)
                let step = PWRunnerStepResult(step_id: "s", sandbox_check: query, attempt: attempt,
                    drift: comparison.drift, comparison: comparison)
                if state != "present" { try FileManager.default.removeItem(atPath: path) }
                if state == "recreated" { FileManager.default.createFile(atPath: path, contents: Data("new".utf8)) }
                let enriched = enrichPathDiagnostics(steps: [step])[0]
                try expectEqual(enriched.comparison?.conclusion, comparison.conclusion)
                try expectEqual(enriched.drift, step.drift)
                try expectEqual(enriched.comparison?.limitations,
                    comparison.limitations + (state == "absent" ? ["host_path_resolution_changed"] : []))
                try expectFalse(enriched.comparison!.limitations.contains("attempt_mutation_order_unestablished"))
            }
        }
        tk.run("enrichment reads the planner's outcome sentinel, not a limitation label") {
            let path = "/private/tmp/pw-path-sentinel-" + UUID().uuidString
            var query = comparisonCheck(target: path)
            query.outcome = SandboxCheckOutcome.predictionUnavailable
            query.rc = -1
            query.native_rc = nil
            query.result_source = "synthetic"
            query.missing_reason = "query_not_requested"
            let attempt = comparisonAttempt(target: path)
            // No exclusion label reaches this comparison; the sentinel alone must gate.
            let comparison = computeComparison(sandboxCheck: query, attempt: attempt)
            try expectFalse(comparison.limitations.contains(where: { $0.hasPrefix("query_plan:") }))
            let step = PWRunnerStepResult(step_id: "s", sandbox_check: query, attempt: attempt,
                drift: comparison.drift, comparison: comparison)
            let enriched = enrichPathDiagnostics(steps: [step])[0]
            try expectNil(enriched.sandbox_check.path_diagnostics?.realpath_resolved)
            try expectEqual(enriched.comparison?.limitations, comparison.limitations)
            try expectFalse(enriched.comparison!.limitations.contains("host_path_resolution_changed"))
        }
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

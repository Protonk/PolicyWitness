import Darwin
import Foundation
@testable import PWRunnerCore

// The comparison record producer, table-driven over the shared scenario matrix
// (tests/fixtures/comparison/matrix.json) through `comparisonEvidence(...)`.
// Each row's `unit` inputs are constructed channel results; the expectations
// were reviewed against the matrix and its independent controls, not taken
// from this producer. The live reader (`witness_contract/comparison_matrix`)
// runs the same rows through the CLI.

private struct MatrixRow {
    let id: String
    let scenario: String
    let unit: [String: Any]
    let comparison: [String: Any]
}

private func matrixRows() throws -> [MatrixRow] {
    let url = repositoryRoot().appendingPathComponent("tests/fixtures/comparison/matrix.json")
    let fixture = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [String: Any]
    return (fixture["rows"] as! [[String: Any]]).map { row in
        MatrixRow(id: row["id"] as! String, scenario: row["scenario"] as! String,
                  unit: row["unit"] as! [String: Any], comparison: row["comparison"] as! [String: Any])
    }
}

private func matrixVocabulary() throws -> Set<String> {
    let url = repositoryRoot().appendingPathComponent("tests/fixtures/comparison/matrix.json")
    let fixture = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [String: Any]
    return Set(fixture["limitations_vocabulary"] as! [String])
}

// Placeholders stand for absolute paths the live reader creates; the producer
// compares submitted strings only, so any fixed expansion is equivalent.
private func expand(_ value: Any?) -> String? {
    guard let text = value as? String else { return nil }
    return text.replacingOccurrences(of: "{{SCEN_ROOT}}", with: "/private/tmp/pw-matrix-unit")
        .replacingOccurrences(of: "{{FIFO}}", with: "/private/tmp/pw-matrix-unit/blocker.fifo")
}

private func integer(_ value: Any?) -> Int? {
    guard let number = value as? NSNumber, CFGetTypeID(number) != CFBooleanGetTypeID() else { return nil }
    return number.intValue
}

private func unitSandboxCheck(_ raw: [String: Any]) -> PWRunnerSandboxCheckResult {
    var result = PWRunnerSandboxCheckResult(rc: integer(raw["rc"]) ?? 0, outcome: raw["outcome"] as! String, pid: 42,
        operation: raw["operation"] as! String, filter_kind: raw["filter_kind"] as! String,
        filter_value: expand(raw["filter_value"]), error: raw["error"] as? String)
    result.result_source = raw["result_source"] as? String
    result.native_rc = integer(raw["native_rc"])
    result.missing_reason = raw["missing_reason"] as? String
    return result
}

private func unitAttempt(_ raw: [String: Any]) -> PWRunnerAttemptResult {
    var result = PWRunnerAttemptResult(rc: integer(raw["rc"]) ?? 0, errno: integer(raw["errno"]),
        outcome: raw["outcome"] as! String, error: raw["error"] as? String,
        requested_path: expand(raw["requested_path"]), child_pid: integer(raw["child_pid"]),
        child_exit_code: integer(raw["child_exit_code"]))
    result.requested_kind = raw["requested_kind"] as? String
    result.requested_action = raw["requested_action"] as? String
    result.result_source = raw["result_source"] as? String
    result.missing_reason = raw["missing_reason"] as? String
    return result
}

/// The producer's record for one row, with the lifecycle limitation appended
/// exactly as the step builder appends it from the attempt's lifecycle summary.
private func produce(_ row: MatrixRow) -> PWRunnerComparison {
    let order: ComparisonOrder = (row.unit["order"] as? String) == "query_first" ? .queryFirst : .unestablished
    var comparison = comparisonEvidence(sandboxCheck: unitSandboxCheck(row.unit["sandbox_check"] as! [String: Any]),
        attempt: unitAttempt(row.unit["attempt"] as! [String: Any]),
        queryExclusionReason: row.unit["query_exclusion_reason"] as? String, order: order).comparison
    if let summary = row.unit["lifecycle_summary"] as? String,
       let limitation = PWDisposition.limitationForSummary[summary] {
        comparison.limitations.append(limitation)
    }
    return comparison
}

private func comparisonCheck(_ outcome: String = "allow", operation: String = "file-read-data",
                             target: String = "/private/tmp/comparison", filter: String = "path") -> PWRunnerSandboxCheckResult {
    var result = PWRunnerSandboxCheckResult(rc: outcome == "allow" ? 0 : 1, outcome: outcome, pid: 42,
        operation: operation, filter_kind: filter, filter_value: target)
    result.result_source = "validator"
    result.native_rc = result.rc
    return result
}

private func comparisonAttempt(kind: String = "file", action: String = "open_read",
                               target: String = "/private/tmp/comparison", outcome: String = "ok",
                               errno: Int? = nil) -> PWRunnerAttemptResult {
    var result = PWRunnerAttemptResult(rc: outcome == "ok" ? 0 : 1, errno: errno, outcome: outcome, requested_path: target)
    result.requested_kind = kind
    result.requested_action = action
    result.result_source = "worker"
    return result
}

func runComparisonEvidenceTests(_ tk: TestKit) {
    tk.group("comparison matrix rows through comparisonEvidence") {
        var rows: [MatrixRow] = []
        var vocabulary: Set<String> = []
        tk.run("the fixture carries every S, B, C and T row with a vocabulary-bound record") {
            rows = try matrixRows()
            vocabulary = try matrixVocabulary()
            let ids = Set(rows.map { $0.id })
            let expected = Set((1...25).filter { $0 != 4 }.map { String(format: "S%02d", $0) }
                + (1...7).map { "B\($0)" } + ["C1", "T"])
            try expectEqual(ids, expected, "matrix rows")
            try expectEqual(rows.count, 33)
            for row in rows {
                let limits = row.comparison["limitations"] as! [String]
                try expectTrue(Set(limits).isSubset(of: vocabulary), "\(row.id): \(limits)")
            }
        }
        for row in try! matrixRows() {
            tk.run("\(row.id): \(row.scenario)") {
                let produced = produce(row)
                let want = row.comparison
                try expectEqual(produced.observation, want["observation"] as? String, "\(row.id) observation")
                try expectEqual(produced.observation_basis, want["observation_basis"] as? String, "\(row.id) basis")
                try expectEqual(produced.operation_relation, want["operation_relation"] as? String, "\(row.id) operation")
                try expectEqual(produced.target_relation, want["target_relation"] as? String, "\(row.id) target")
                try expectEqual(produced.order, want["order"] as? String, "\(row.id) order")
                try expectEqual(produced.limitations, want["limitations"] as? [String], "\(row.id) limitations")
                // Every produced record stays inside the vocabulary and the wire
                // shape carries exactly the six record keys.
                try expectTrue(Set(produced.limitations).isSubset(of: try matrixVocabulary()))
                let wire = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(produced)) as! [String: Any]
                try expectEqual(Set(wire.keys), ["observation", "observation_basis", "operation_relation",
                                                 "target_relation", "order", "limitations"])
            }
        }
    }
    tk.group("limitations vocabulary at the producer") {
        tk.run("each planner exclusion code renders as its query_plan entry and nothing else") {
            for code in ["path_unresolved_at_planning", "prediction_unavailable_pair", "unrecognized_filter_kind"] {
                var query = comparisonCheck()
                query.outcome = SandboxCheckOutcome.predictionUnavailable
                query.rc = -1
                query.native_rc = nil
                query.result_source = "synthetic"
                query.missing_reason = "query_not_requested"
                let record = comparisonEvidence(sandboxCheck: query, attempt: comparisonAttempt(),
                                                queryExclusionReason: code, order: .unestablished).comparison
                try expectEqual(record.limitations, ["query_plan:" + code])
                try expectEqual(record.order, "unestablished")
            }
        }
        tk.run("missing channels, scope differences and failures render no limitation of their own") {
            var query = comparisonCheck("deny", operation: "file-write-data", target: "/A")
            query.result_source = "synthetic"
            query.outcome = SandboxCheckOutcome.error
            query.native_rc = nil
            query.missing_reason = "validator_no_verdict"
            var attempt = comparisonAttempt(target: "/B")
            attempt.result_source = "synthetic"
            attempt.missing_reason = "slot_incomplete"
            attempt.outcome = AttemptOutcome.notRunWorkerDied
            attempt.rc = -1
            let missing = comparisonEvidence(sandboxCheck: query, attempt: attempt).comparison
            try expectEqual(missing.observation, "unavailable")
            try expectEqual(missing.operation_relation, "different")
            try expectEqual(missing.target_relation, "different_submitted")
            try expectEqual(missing.limitations, [])
            let failed = comparisonEvidence(sandboxCheck: comparisonCheck(),
                attempt: comparisonAttempt(outcome: "open_failed", errno: Int(EACCES))).comparison
            try expectEqual(failed.observation, "permission_failure")
            try expectEqual(failed.limitations, [])
            let spawned = comparisonEvidence(sandboxCheck: comparisonCheck(operation: "process-exec*"),
                attempt: {
                    var a = comparisonAttempt(kind: "exec", action: "spawn", outcome: "exec_failed")
                    a.child_pid = 123; a.child_exit_code = 37; a.rc = 37
                    return a
                }()).comparison
            try expectEqual(spawned.observation_basis, "spawned_child")
            try expectEqual(spawned.limitations, [])
        }
        tk.run("the record carries no prediction, conclusion or scope") {
            let record = comparisonEvidence(sandboxCheck: comparisonCheck("deny"), attempt: comparisonAttempt(),
                                            order: .queryFirst).comparison
            let wire = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(record)) as! [String: Any]
            for key in ["prediction", "conclusion", "scope", "obligations", "drift"] {
                try expectNil(wire[key], key)
            }
            try expectEqual(record.observation, "succeeded")
            try expectEqual(record.order, "query_first")
        }
    }
    tk.group("host path provenance") {
        for state in ["absent", "present", "recreated", "excluded"] {
            tk.run("later \(state) resolution appends only path observations without touching the record") {
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
                let step = PWRunnerStepResult(step_id: "s", sandbox_check: query, attempt: attempt, comparison: comparison)
                if state != "present" { try FileManager.default.removeItem(atPath: path) }
                if state == "recreated" { FileManager.default.createFile(atPath: path, contents: Data("new".utf8)) }
                let enriched = enrichPathDiagnostics(steps: [step])[0]
                try expectEqual(enriched.comparison?.limitations, comparison.limitations)
                try expectEqual(enriched.comparison?.observation, comparison.observation)
                try expectEqual(enriched.comparison?.order, comparison.order)
                try expectEqual(enriched.sandbox_check.path_diagnostics?.observer, "runner_host")
                try expectEqual(enriched.sandbox_check.path_diagnostics?.phase, "after_orchestration")
                try expectEqual(enriched.sandbox_check.path_diagnostics?.realpath_resolved == nil, state == "absent" || state == "excluded")
            }
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
            try expectNil(after.comparison) // enrichment cannot invent comparison evidence
        }
    }
}

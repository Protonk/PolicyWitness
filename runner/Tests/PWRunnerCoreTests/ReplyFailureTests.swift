import Foundation
@testable import PWRunnerCore

// Field-complete constructed encoding input, not a claim that an admitted run
// also has an admission failure. Keep every top-level optional populated here.
private func replyFixture() throws -> PWRunnerRunResult {
    let json = #"""
    {
      "schema_version":8,"specimen_id":"reply-\"é\"","run_kind":"unit",
      "rc":1,"normalized_outcome":"runner_failed","error":"original cleanup fault",
      "pid":42,"bundle_id":"test.bundle","policy_format":"sbpl","policy_sha256":"hash",
      "applied_profile":{"schema_version":1,"status":"unavailable","reason":"constructed","worker_pid":42},
      "sandboxed_after_apply":true,
      "deny_signal_total":{"signal":"legacy","count_before":1,"count_after":2,"delta":1},
      "steps":[{
        "step_id":"s","deny_signal":null,"drift":false,
        "sandbox_check":{"rc":0,"native_rc":0,"errno":0,"outcome":"allow","pid":42,
          "operation":"file-read-data","scope":"post_sandbox","filter_kind":"path",
          "filter_value":"/owned","result_source":"validator",
          "path_diagnostics":{"input":"/owned","realpath_resolved":"/owned",
            "observer":"runner_host","phase":"after_orchestration"}},
        "attempt":{"rc":0,"outcome":"ok","requested_kind":"file","requested_action":"open_read",
          "requested_path":"/owned","result_source":"worker","native_rc":null},
        "comparison":{"scope":"submitted_operation_and_target","prediction":"allow",
          "observation":"succeeded","observation_basis":"completed_worker_status",
          "operation_relation":"matched","target_relation":"same_submitted",
          "conclusion":"agreement","order":"query_first","limitations":["state_stability_unestablished"]}
      }],
      "runner_subprocess":{"pid":42,"partial_steps":false,"reaped":false,
        "ready_byte_received":true,"done_observed":true,"poll_stop_reason":"done","exit_requested":true,
        "termination_request":{"signal":9,"rc":-1,"errno":1},
        "wait_errors":[{"phase":"exit_grace","rc":-1,"errno":10}],
        "ordering":{"collection_closed_before_proceed":true,"proceed_set":true,"proceed_observed":true,
          "validator_disposition":"reaped","worker_lifetime_established":true,"protocol_violations":[]},
        "worker_evidence":{"abi_version":7,"failure_publication":0,"failure_state":"absent",
          "diagnostic":{"state":0,"status":"absent"}}},
      "admission_failure":{"origin":"runner_host","field":"constructed","actual":2,"maximum":1,"unit":"items"},
      "validator_subprocess":{"pid":43,"exit_code":0,"reaped":true,"stdout_collection_stop":"eof",
        "records":[{"step_id":"s","operation":"file-read-data","filter_type":"PATH","filter_value":"/owned",
          "rc":0,"errno":0,"outcome":"allow","raw_line":"native record bytes"}]},
      "test_overrides":{"validator_io_timeout_ms":50}
    }
    """#
    return try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: Data(json.utf8))
}

private func replyObject(_ data: Data) throws -> [String: Any] {
    try JSONSerialization.jsonObject(with: data) as! [String: Any]
}

func runReplyFailureTests(_ tk: TestKit) {
    tk.group("host reply failure contract") {
        tk.run("valid and legacy replies use the normal encoder unchanged") {
            for version in [4, 7, 8] {
                var result = try replyFixture(); result.schema_version = version
                try expectEqual(pwRunnerReplyData(result), try pwRunnerEncodeJSON(result))
            }
        }
        for defect in ["ordering", "comparison", "order", "disagreement", "lifetime", "association", "pid", "none"] {
            tk.run("reply preserves evidence while withholding claims after \(defect) rejection") {
                var result = try replyFixture()
                switch defect {
                case "ordering": result.runner_subprocess?.ordering = nil
                case "comparison": result.steps[0].comparison = nil
                case "order": result.steps[0].comparison?.order = nil
                case "disagreement":
                    result.steps[0].comparison?.conclusion = "disagreement"
                    result.steps[0].comparison?.limitations = []; result.steps[0].drift = true
                case "lifetime": result.runner_subprocess?.ordering?.worker_lifetime_established = false
                case "association":
                    let duplicate = result.validator_subprocess!.records![0]
                    result.validator_subprocess?.records?.append(duplicate)
                case "pid": result.steps[0].sandbox_check.pid = 99
                default:
                    result.steps[0].sandbox_check.filter_kind = "none"
                    result.steps[0].sandbox_check.filter_value = "ignored"
                    result.validator_subprocess?.records?[0].filterType = "NONE"
                    // A NONE native record must omit its value, unlike the request.
                    result.validator_subprocess?.records?[0].filterValue = "not-native"
                }
                do { _ = try pwRunnerEncodeJSON(result); throw TestFailure(message: "invalid ordinary reply accepted") }
                catch is EncodingError { }
                let bytes = pwRunnerReplyData(result)
                let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
                try expectEqual(decoded.schema_version, 8)
                try expectEqual(decoded.normalized_outcome, NormalizedOutcome.runnerReportingFailed)
                try expectEqual(decoded.rc, 1)
                try expectContains(decoded.error ?? "", "runner host could not encode")
                try expectEqual(decoded.reporting_failure?.evidence_retained, true)
                try expectEqual(decoded.reporting_failure?.original_normalized_outcome, result.normalized_outcome)
                try expectEqual(decoded.reporting_failure?.original_rc, result.rc)
                try expectEqual(decoded.reporting_failure?.original_error, result.error)
                try expectNil(decoded.steps[0].comparison)
                try expectNil(decoded.steps[0].drift)
                // Compare every other field against an unvalidated diagnostic
                // reference, encoded as legacy only inside this test. Production
                // never downgrades a response to evade its invariants.
                var reference = result; reference.schema_version = 7
                var expected = try replyObject(pwRunnerEncodeJSON(reference))
                let actual = try replyObject(bytes)
                for key in ["schema_version", "rc", "normalized_outcome", "error", "reporting_failure"] {
                    expected[key] = actual[key]
                }
                var steps = expected["steps"] as! [[String: Any]]
                steps[0].removeValue(forKey: "comparison"); steps[0]["drift"] = NSNull()
                expected["steps"] = steps
                try expectTrue(NSDictionary(dictionary: expected).isEqual(to: actual), "raw evidence or identity changed")
                try expectEqual(try pwRunnerEncodeJSON(decoded), bytes)
            }
        }
        tk.run("failure marker cannot excuse surviving comparison claims or successful summary") {
            var result = try replyFixture()
            result.steps[0].comparison?.conclusion = "disagreement"
            let failure = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerReplyData(result))
            for defect in ["comparison", "false_drift", "true_drift", "outcome", "rc", "diagnostic", "missing_marker"] {
                var bad = failure
                switch defect {
                case "comparison": bad.steps[0].comparison = try replyFixture().steps[0].comparison
                case "false_drift": bad.steps[0].drift = false
                case "true_drift": bad.steps[0].drift = true
                case "outcome": bad.normalized_outcome = "ok"
                case "rc": bad.rc = 0
                case "diagnostic": bad.reporting_failure?.diagnostic = ""
                default: bad.reporting_failure = nil
                }
                do { _ = try pwRunnerEncodeJSON(bad); throw TestFailure(message: "invalid failure exception accepted: \(defect)") }
                catch is EncodingError { }
            }
        }
        tk.run("repeated encoder failure is explicit, preserves identity and does not claim evidence retention") {
            let result = try replyFixture()
            var calls = 0
            let bytes = pwRunnerReplyData(result) { _ in
                calls += 1; throw TestFailure(message: "injected encoder failure")
            }
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
            try expectEqual(calls, 2)
            try expectEqual(decoded.specimen_id, result.specimen_id)
            try expectEqual(decoded.policy_sha256, result.policy_sha256)
            try expectEqual(decoded.normalized_outcome, NormalizedOutcome.runnerReportingFailed)
            try expectContains(decoded.error ?? "", "evidence-preserving encoding also failed")
            try expectEqual(decoded.reporting_failure?.evidence_retained, false)
            try expectEqual(decoded.reporting_failure?.original_error, result.error)
            try expectTrue(decoded.steps.isEmpty)
            try expectNil(decoded.runner_subprocess)
            try expectNil(decoded.validator_subprocess)
            _ = try pwRunnerEncodeJSON(decoded)
        }
        tk.run("every stored result field has a coding key and survives a populated round trip") {
            var result = try replyFixture()
            result.steps[0].comparison = nil
            result = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerReplyData(result))
            let labels = Set(Mirror(reflecting: result).children.compactMap { $0.label })
            let keys = Set(PWRunnerRunResult.CodingKeys.allCases.map { $0.rawValue })
            try expectEqual(labels, keys, "add new fields to CodingKeys")
            let bytes = try pwRunnerEncodeJSON(result)
            try expectEqual(Set(try replyObject(bytes).keys), labels, "populate and encode every field")
            try expectEqual(try pwRunnerEncodeJSON(pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)), bytes)
        }
    }
}

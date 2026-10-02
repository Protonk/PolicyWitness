import Foundation
@testable import PWRunnerCore

// Structural invariants of PWRunnerRunResult that the audit signal depends on.
// The mirror-back story (`test_overrides` reflects what was honored;
// `runner_subprocess` is present iff the worker was observed) only works if
// these hold for every emit site. None of the existing e2e suites assert the
// relationships themselves — they assert the behavior. These tests pin the
// shape, the exact response-version gate and the absence of removed keys.
//
// Swift's synthesized Codable omits nil optional fields rather than encoding
// explicit JSON null. The tests assert the semantic contract ("absent or null
// means no value") rather than the literal byte form.

private func hostShortCircuitResult(outcome: String) -> PWRunnerRunResult {
    // Host-side outcomes are emitted before posix_spawn returns a worker
    // PID. No runner_subprocess, no steps.
    PWRunnerRunResult(
        specimen_id: "envelope_invariant_host_shortcircuit",
        rc: 1,
        normalized_outcome: outcome,
        error: "synthesized for envelope-shape test",
        pid: 1,
        policy_format: "sbpl",
        steps: []
    )
}

private func wireObject(_ data: Data) throws -> [String: Any] {
    try JSONSerialization.jsonObject(with: data) as! [String: Any]
}

func runEnvelopeInvariantTests(_ tk: TestKit) {
    tk.group("consumer evidence survives encoding without reclassification") {
        for state in ["absent", "present", "recreated"] {
            tk.run("a fixed comparison survives \(state) path enrichment and encoding") {
                let path = "/private/tmp/pw-mutation-wire-" + UUID().uuidString
                FileManager.default.createFile(atPath: path, contents: Data("old".utf8))
                defer { try? FileManager.default.removeItem(atPath: path) }
                var result = try replyFixture()
                var step = result.steps[0]
                step.sandbox_check.filter_value = path
                step.sandbox_check.operation = "file-write-unlink"
                step.attempt.requested_action = "unlink"
                step.attempt.requested_path = path
                step.attempt.path_diagnostics = nil
                step.comparison = PWRunnerComparison(observation: "succeeded", observation_basis: "completed_worker_status",
                    operation_relation: "matched", target_relation: "same_submitted", order: "unestablished", limitations: [])
                result.validator_subprocess?.records?[0].operation = "file-write-unlink"
                result.validator_subprocess?.records?[0].filterValue = path
                if state != "present" { try FileManager.default.removeItem(atPath: path) }
                if state == "recreated" { FileManager.default.createFile(atPath: path, contents: Data("new".utf8)) }
                result.steps = enrichPathDiagnostics(steps: [step])
                let data = try pwRunnerEncodeJSON(result)
                let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data).steps[0]
                try expectEqual(decoded.comparison?.observation, "succeeded")
                try expectEqual(decoded.comparison?.order, "unestablished")
                try expectEqual(decoded.comparison?.limitations, [])
                try expectEqual(decoded.sandbox_check.outcome, "allow")
                try expectEqual(decoded.sandbox_check.path_diagnostics?.phase, "after_orchestration")
                // Later host nonresolution is visible only in the path block.
                try expectEqual(decoded.sandbox_check.path_diagnostics?.realpath_resolved == nil, state == "absent")
                let wire = try wireObject(data)
                let step0 = (wire["steps"] as! [[String: Any]])[0]
                try expectNil(step0["drift"])
                try expectNil(step0["deny_signal"])
            }
        }
        tk.run("a spawned child's failed result survives beside its spawn observation") {
            var result = try replyFixture()
            var step = result.steps[0]
            step.comparison = PWRunnerComparison(observation: "succeeded", observation_basis: "spawned_child",
                operation_relation: "matched", target_relation: "same_submitted", order: "query_first", limitations: [])
            step.sandbox_check.operation = "process-exec*"
            step.attempt.requested_kind = "exec"
            step.attempt.requested_action = "spawn"
            step.attempt.outcome = "exec_failed"
            step.attempt.rc = 37
            step.attempt.child_pid = 123
            step.attempt.child_exit_code = 37
            step.attempt.stdout = "controlled marker"
            result.steps = [step]
            result.validator_subprocess?.records?[0].operation = "process-exec*"
            let encoded = try pwRunnerEncodeJSON(result)
            let raw = try wireObject(encoded)
            let wire = (raw["steps"] as! [[String: Any]])[0]
            let comparison = wire["comparison"] as! [String: Any]
            let attempt = wire["attempt"] as! [String: Any]
            try expectEqual(comparison["observation_basis"] as? String, "spawned_child")
            try expectEqual(comparison["limitations"] as? [String], [])
            try expectEqual(attempt["requested_kind"] as? String, "exec")
            try expectEqual(attempt["outcome"] as? String, "exec_failed")
            try expectEqual(attempt["rc"] as? Int, 37)
            try expectEqual(attempt["child_exit_code"] as? Int, 37)
            try expectEqual(attempt["child_pid"] as? Int, 123)
            try expectEqual(attempt["stdout"] as? String, "controlled marker")
            try expectNil(attempt["exit_code"])
            try expectNil(attempt["syscall_errno"])
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: encoded)
            try expectEqual(decoded.steps[0].attempt.child_exit_code, 37)
        }
        tk.run("a missing query keeps its missing reason and an empty limitations list") {
            // The attempt channel stays completed (the record beside it says so);
            // only the query channel is missing, so the order is unestablished.
            var result = try replyFixture()
            result.steps[0].comparison = PWRunnerComparison(observation: "succeeded",
                observation_basis: "completed_worker_status", operation_relation: "matched",
                target_relation: "same_submitted", order: "unestablished", limitations: [])
            result.steps[0].sandbox_check.outcome = SandboxCheckOutcome.error
            result.steps[0].sandbox_check.result_source = "synthetic"
            result.steps[0].sandbox_check.native_rc = nil
            result.steps[0].sandbox_check.missing_reason = "validator_no_verdict"
            let data = try pwRunnerEncodeJSON(result)
            let wire = (try wireObject(data)["steps"] as! [[String: Any]])[0]
            try expectEqual((wire["comparison"] as? [String: Any])?["limitations"] as? [String], [])
            try expectEqual((wire["sandbox_check"] as? [String: Any])?["missing_reason"] as? String, "validator_no_verdict")
            try expectTrue((wire["sandbox_check"] as? [String: Any])?["native_rc"] is NSNull)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectEqual(decoded.steps[0].comparison?.order, "unestablished")
            try expectEqual(decoded.steps[0].sandbox_check.missing_reason, "validator_no_verdict")
        }
    }
    tk.group("exact response version") {
        tk.run("the producer's default is the manifest version and nothing else decodes") {
            let fresh = PWRunnerRunResult(specimen_id: "s", rc: 1, normalized_outcome: NormalizedOutcome.badRequest,
                error: "constructed", pid: 1, policy_format: "sbpl", steps: [])
            try expectEqual(fresh.schema_version, PWContract.responseSchema)
            let bytes = try pwRunnerEncodeJSON(fresh)
            try expectEqual(try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes).schema_version, PWContract.responseSchema)
            for version in [1, 7, 12, PWContract.responseSchema + 1] {
                var raw = try wireObject(bytes)
                raw["schema_version"] = version
                do {
                    _ = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: raw))
                    throw TestFailure(message: "response \(version) decoded")
                } catch is DecodingError { }
            }
        }
    }
    tk.group("PWRunnerSubprocess: additive host observations") {
        tk.run("absent or null observations remain unknown") {
            for suffix in ["", ",\"ready_byte_received\":null,\"done_observed\":null,\"poll_stop_reason\":null,\"exit_requested\":null,\"termination_request\":null,\"reaped\":null,\"wait_errors\":null"] {
                let data = Data("{\"pid\":42,\"exit_code\":0,\"partial_steps\":false\(suffix)}".utf8)
                let decoded = try pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: data)
                try expectEqual(decoded.exit_code, 0)
                try expectNil(decoded.ready_byte_received)
                try expectNil(decoded.done_observed)
                try expectNil(decoded.poll_stop_reason)
                try expectNil(decoded.exit_requested)
                try expectNil(decoded.termination_request)
                try expectNil(decoded.reaped)
                try expectNil(decoded.wait_errors)
            }
        }
        tk.run("observed false and empty errors survive encoding without inventing status") {
            let record = PWRunnerSubprocess(pid: 42, term_signal: nil, exit_code: nil,
                partial_steps: true, ready_byte_received: false, done_observed: false,
                poll_stop_reason: "wait_error", exit_requested: true, reaped: false, wait_errors: [])
            let data = try pwRunnerEncodeJSON(record)
            let raw = try wireObject(data)
            try expectEqual(raw["ready_byte_received"] as? Bool, false)
            try expectEqual(raw["done_observed"] as? Bool, false)
            try expectEqual(raw["reaped"] as? Bool, false)
            try expectEqual((raw["wait_errors"] as? [Any])?.count, 0)
            let decoded = try pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: data)
            try expectNil(decoded.exit_code)
            try expectNil(decoded.term_signal)
            try expectNil(decoded.termination_request)
        }
        tk.run("unfamiliar host observation strings and errno values survive encoding") {
            let record = PWRunnerSubprocess(pid: 42, term_signal: nil, exit_code: nil,
                partial_steps: false, poll_stop_reason: "future_stop",
                termination_request: PWRunnerTerminationRequest(signal: 31, rc: -1, errno: 123456),
                reaped: false, wait_errors: [PWRunnerWaitError(phase: "future_phase", rc: -1, errno: 654321)])
            let data = try pwRunnerEncodeJSON(record)
            let decoded = try pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: data)
            try expectEqual(decoded.poll_stop_reason, "future_stop")
            try expectEqual(decoded.termination_request?.signal, 31)
            try expectEqual(decoded.termination_request?.rc, -1)
            try expectEqual(decoded.termination_request?.errno, 123456)
            try expectEqual(decoded.wait_errors?.first?.phase, "future_phase")
            try expectEqual(decoded.wait_errors?.first?.rc, -1)
            try expectEqual(decoded.wait_errors?.first?.errno, 654321)
        }
    }

    tk.group("PWRunnerRunResult: Codable round-trip preserves semantic absence") {
        tk.run("nil test_overrides survives encode → decode as nil") {
            var original = try replyFixture()
            original.test_overrides = nil
            let data = try pwRunnerEncodeJSON(original)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectNil(decoded.test_overrides)
        }
        tk.run("nil test_overrides survives a JSON producer that emits explicit null") {
            // A peer producer outside this codebase may emit `"test_overrides": null`
            // explicitly rather than omitting the key. The decoder must treat
            // both as "no value." This pins the semantic contract.
            var original = try replyFixture()
            original.test_overrides = nil
            var obj = try wireObject(pwRunnerEncodeJSON(original))
            obj["test_overrides"] = NSNull()
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: obj))
            try expectNil(decoded.test_overrides)
        }
    }

    tk.group("PWRunnerRunResult: production-shaped result") {
        tk.run("top-level pid agrees with runner_subprocess.pid") {
            // The mirror-back contract: top-level pid names the sandboxed
            // worker process when runner_subprocess is present, so consumers
            // using pid for unified-log correlation reach the worker.
            let result = try replyFixture()
            try expectEqual(result.pid, result.runner_subprocess?.pid)
        }
        tk.run("validator_subprocess and every step survive a round trip") {
            let original = try replyFixture()
            let data = try pwRunnerEncodeJSON(original)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectEqual(decoded.steps.count, original.steps.count)
            try expectEqual(decoded.validator_subprocess?.pid, original.validator_subprocess?.pid)
            try expectEqual(decoded.validator_subprocess?.exit_code, original.validator_subprocess?.exit_code)
            try expectNil(decoded.validator_subprocess?.term_signal)
        }
        tk.run("no worker PID encodes an explicit null query PID") {
            var result = try replyFixture()
            result.steps[0].sandbox_check.pid = nil
            result.steps[0].comparison?.order = "unestablished"
            let bytes = try pwRunnerEncodeJSON(result)
            let step = (try wireObject(bytes)["steps"] as! [[String: Any]])[0]
            try expectTrue((step["sandbox_check"] as! [String: Any])["pid"] is NSNull)
            try expectNil(try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes).steps[0].sandbox_check.pid)
        }
        tk.run("client XPC failure emitters share the current response default") {
            for outcome in [NormalizedOutcome.xpcError, NormalizedOutcome.xpcTimeout,
                            NormalizedOutcome.xpcProxyTypeMismatch, NormalizedOutcome.xpcNoReply] {
                let result = hostShortCircuitResult(outcome: outcome)
                let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(result))
                try expectEqual(decoded.schema_version, PWContract.responseSchema)
                try expectNil(decoded.runner_subprocess)
                try expectTrue(decoded.steps.isEmpty)
            }
        }
    }

    tk.group("PWRunnerRunResult: host short-circuit result") {
        tk.run("runner_subprocess is nil when no worker was spawned") {
            for outcome in [
                NormalizedOutcome.workerSpawnFailed,
                NormalizedOutcome.badRequest,
                NormalizedOutcome.badPolicy,
                NormalizedOutcome.alreadyRan,
            ] {
                let result = hostShortCircuitResult(outcome: outcome)
                try expectNil(result.runner_subprocess, "outcome=\(outcome)")
                try expectTrue(result.steps.isEmpty, "outcome=\(outcome) has steps=\(result.steps)")
                _ = try pwRunnerEncodeJSON(result)
            }
        }
    }

    tk.group("PWRunnerRunResult: post-spawn failure result") {
        tk.run("runner_subprocess is present even when no worker report arrived") {
            // runner_timeout: host SIGKILLed the worker after the deadline. The
            // field-complete fixture carries a worker subprocess with the record
            // the encoder requires beside it.
            var timeout = try replyFixture()
            timeout.normalized_outcome = NormalizedOutcome.runnerTimeout
            try expectNotNil(timeout.runner_subprocess)
            try expectEqual(timeout.pid, timeout.runner_subprocess?.pid)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(timeout))
            try expectNotNil(decoded.runner_subprocess?.disposition)
            try expectNotNil(decoded.runner_subprocess?.ordering)
        }
    }
}

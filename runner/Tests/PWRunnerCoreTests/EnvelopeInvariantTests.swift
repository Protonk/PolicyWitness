import Foundation
@testable import PWRunnerCore

// Structural invariants of PWRunnerRunResult that the audit signal
// depends on. The mirror-back story (`test_overrides` reflects what was
// honored; `runner_subprocess` is present iff the worker was observed)
// only works if these hold for every emit site. None of the existing
// e2e suites assert the relationships themselves — they assert the
// behavior. These tests pin the shape.
//
// Swift's synthesized Codable omits nil optional fields rather than
// encoding explicit JSON null. The tests assert the semantic contract
// ("absent or null means no value") rather than the literal byte form,
// so a future custom encoder that emits explicit nulls would not break
// them.

private func okResult(pid: Int = 4242, stepCount: Int = 0) -> PWRunnerRunResult {
    let sub = PWRunnerSubprocess(
        pid: pid,
        term_signal: nil,
        exit_code: 0,
        partial_steps: false
    )
    let steps = (0..<stepCount).map { idx in
        PWRunnerStepResult(
            step_id: "p\(idx)",
            sandbox_check: PWRunnerSandboxCheckResult(
                rc: 0, outcome: "allow", pid: pid,
                operation: "file-read-data", scope: "post_sandbox",
                filter_kind: "none"
            ),
            attempt: PWRunnerAttemptResult(rc: 0, outcome: "ok"),
            deny_signal: nil
        )
    }
    return PWRunnerRunResult(
        specimen_id: "envelope_invariant_ok",
        rc: 0,
        normalized_outcome: NormalizedOutcome.ok,
        pid: pid,
        policy_format: "sbpl",
        sandboxed_after_apply: true,
        steps: steps,
        runner_subprocess: sub
    )
}

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

private func postSpawnFailureResult(outcome: String, signal: Int?) -> PWRunnerRunResult {
    // Worker spawned but died before writing a report (runner_timeout,
    // runner_sandbox_denied, runner_failed). runner_subprocess must be
    // present even though no report arrived, so callers can see the
    // observed exit status.
    let sub = PWRunnerSubprocess(
        pid: 5555,
        term_signal: signal,
        exit_code: signal == nil ? 1 : nil,
        partial_steps: false
    )
    return PWRunnerRunResult(
        specimen_id: "envelope_invariant_post_spawn",
        rc: 1,
        normalized_outcome: outcome,
        error: "synthesized for envelope-shape test",
        pid: sub.pid,
        policy_format: "sbpl",
        steps: [],
        runner_subprocess: sub
    )
}

func runEnvelopeInvariantTests(_ tk: TestKit) {
    tk.group("consumer evidence survives encoding without reclassification") {
        tk.run("spawn agreement retains failed child result and every independent limit") {
            var result = okResult(stepCount: 1)
            var step = result.steps[0]
            let limits = ["query_attempt_order_unestablished", "state_stability_unestablished",
                "runtime_target_identity_unestablished", "exec_query_not_full_spawn_prediction",
                "exec_result_failed_after_spawn", "sandbox_attribution_unestablished"]
            step.comparison = PWRunnerComparison(scope: "submitted_operation_and_target",
                prediction: "allow", observation: "succeeded", observation_basis: "spawned_child",
                operation_relation: "matched", target_relation: "same_submitted",
                conclusion: "agreement", limitations: limits)
            step.drift = false
            step.attempt.requested_kind = "exec"
            step.attempt.requested_action = "spawn"
            step.attempt.requested_path = "/submitted"
            step.attempt.outcome = "exec_failed"
            step.attempt.rc = 37
            step.attempt.child_pid = 123
            step.attempt.child_exit_code = 37
            step.attempt.stdout = "controlled marker"
            var path = PWRunnerPathDiagnostics(input: "/submitted", realpath_resolved: "/host-later")
            path.observer = "runner_host"
            path.phase = "after_orchestration"
            step.sandbox_check.path_diagnostics = path
            result.steps = [step]
            let encoded = try pwRunnerEncodeJSON(result)
            let raw = try JSONSerialization.jsonObject(with: encoded) as! [String: Any]
            let wire = (raw["steps"] as! [[String: Any]])[0]
            let comparison = wire["comparison"] as! [String: Any]
            let attempt = wire["attempt"] as! [String: Any]
            let query = wire["sandbox_check"] as! [String: Any]
            let provenance = query["path_diagnostics"] as! [String: Any]
            try expectEqual(wire["drift"] as? Bool, false)
            try expectEqual(comparison["conclusion"] as? String, "agreement")
            try expectEqual(comparison["observation_basis"] as? String, "spawned_child")
            try expectEqual(comparison["limitations"] as? [String], limits)
            try expectEqual(attempt["requested_kind"] as? String, "exec")
            try expectEqual(attempt["requested_action"] as? String, "spawn")
            try expectEqual(attempt["requested_path"] as? String, "/submitted")
            try expectEqual(attempt["outcome"] as? String, "exec_failed")
            try expectEqual(attempt["rc"] as? Int, 37)
            try expectEqual(attempt["child_exit_code"] as? Int, 37)
            try expectEqual(attempt["child_pid"] as? Int, 123)
            try expectEqual(attempt["stdout"] as? String, "controlled marker")
            try expectEqual(provenance["observer"] as? String, "runner_host")
            try expectEqual(provenance["phase"] as? String, "after_orchestration")
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: encoded)
            try expectEqual(decoded.steps[0].comparison?.limitations, limits)
            try expectEqual(decoded.steps[0].attempt.child_exit_code, 37)
        }
        tk.run("missing channels and scope differences survive together including unfamiliar limits") {
            var result = okResult(stepCount: 1)
            let limits = ["prediction:validator_no_verdict", "attempt:slot_incomplete",
                "operation:different", "target:different_submitted", "future_evidence_limit"]
            result.steps[0].comparison = PWRunnerComparison(scope: "submitted_operation_and_target",
                prediction: "unavailable", observation: "unavailable", observation_basis: "no_completed_worker_result",
                operation_relation: "different", target_relation: "different_submitted",
                conclusion: "unavailable", limitations: limits)
            result.steps[0].sandbox_check.missing_reason = "validator_no_verdict"
            result.steps[0].attempt.missing_reason = "slot_incomplete"
            let data = try pwRunnerEncodeJSON(result)
            let raw = try JSONSerialization.jsonObject(with: data) as! [String: Any]
            let wire = (raw["steps"] as! [[String: Any]])[0]
            try expectTrue(wire["drift"] is NSNull)
            try expectEqual((wire["comparison"] as? [String: Any])?["limitations"] as? [String], limits)
            try expectEqual((wire["sandbox_check"] as? [String: Any])?["missing_reason"] as? String, "validator_no_verdict")
            try expectEqual((wire["attempt"] as? [String: Any])?["missing_reason"] as? String, "slot_incomplete")
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectEqual(decoded.steps[0].comparison?.limitations, limits)
        }
    }
    tk.group("response 7 preserves legacy uncertainty") {
        tk.run("stored versions 4 through 6 retain drift without invented comparison or intent") {
            for version in 4...6 {
                for value: Bool? in [true, false, nil] {
                    var old = okResult(stepCount: 1)
                    old.schema_version = version
                    old.steps[0].drift = value
                    let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(old))
                    try expectEqual(decoded.schema_version, version)
                    try expectEqual(decoded.steps[0].drift, value)
                    try expectNil(decoded.steps[0].comparison)
                    try expectNil(decoded.steps[0].attempt.requested_kind)
                    try expectNil(decoded.steps[0].attempt.requested_action)
                    let raw = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(decoded)) as! [String: Any]
                    let step = (raw["steps"] as! [[String: Any]])[0]
                    try expectNil(step["comparison"])
                    try expectNil((step["attempt"] as? [String: Any])?["requested_kind"])
                    try expectNil((step["attempt"] as? [String: Any])?["requested_action"])
                }
            }
        }
        tk.run("stored path forms do not acquire a host observation phase") {
            let bytes = Data("{\"input\":\"/tmp/old\",\"realpath_resolved\":\"/private/tmp/old\"}".utf8)
            let decoded = try pwRunnerDecodeJSON(PWRunnerPathDiagnostics.self, from: bytes)
            try expectEqual(decoded.realpath_resolved, "/private/tmp/old")
            try expectNil(decoded.observer)
            try expectNil(decoded.phase)
            let raw = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(decoded)) as! [String: Any]
            try expectNil(raw["observer"])
            try expectNil(raw["phase"])
        }
    }
    tk.group("PWRunnerSubprocess: additive host observations") {
        tk.run("legacy absent or null observations remain unknown") {
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
            let raw = try JSONSerialization.jsonObject(with: data) as! [String: Any]
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
            let original = okResult()
            try expectNil(original.test_overrides)

            let data = try pwRunnerEncodeJSON(original)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectNil(decoded.test_overrides)
        }

        tk.run("nil test_overrides survives a JSON producer that emits explicit null") {
            // A peer producer outside this codebase may emit `"test_overrides": null`
            // explicitly rather than omitting the key. The decoder must treat
            // both as "no value." This pins the semantic contract.
            let original = okResult()
            var data = try pwRunnerEncodeJSON(original)
            // Convert to a mutable dict, inject explicit null, re-encode.
            if var obj = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                obj["test_overrides"] = NSNull()
                data = try JSONSerialization.data(withJSONObject: obj, options: [])
            } else {
                throw TestFailure(message: "encoded result was not a JSON object")
            }
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectNil(decoded.test_overrides)
        }
    }

    tk.group("PWRunnerRunResult: production-shaped success result") {

        tk.run("schema_version is 7, test_overrides is nil, runner_subprocess is present") {
            let result = okResult(pid: 7777, stepCount: 2)
            try expectEqual(result.schema_version, 7)
            try expectNil(result.test_overrides)
            try expectNotNil(result.runner_subprocess)
            // validator_subprocess is nil when the host didn't spawn
            // a validator child for this run (e.g. okResult fixture
            // here, or every probe was in the prediction-unavailable
            // set in a real run).
            try expectNil(result.validator_subprocess)
        }

        tk.run("top-level pid agrees with runner_subprocess.pid") {
            // The mirror-back contract: top-level pid names the sandboxed
            // worker process when runner_subprocess is present, so consumers
            // using pid for unified-log correlation reach the worker.
            let result = okResult(pid: 12345)
            try expectEqual(result.pid, result.runner_subprocess?.pid)
        }

        tk.run("steps array is preserved through round-trip") {
            let original = okResult(stepCount: 3)
            try expectEqual(original.steps.count, 3)
            let data = try pwRunnerEncodeJSON(original)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectEqual(decoded.steps.count, 3)
        }

        tk.run("v4: validator_subprocess + steps[].drift round-trip via Codable") {
            // Production-shaped result with the v4 fields populated.
            var result = okResult(pid: 9001, stepCount: 2)
            result.validator_subprocess = PWRunnerValidatorSubprocess(
                pid: 9002, term_signal: nil, exit_code: 0
            )
            // Per-step drift values: one true, one false. Both must
            // round-trip identically. The third (default-nil) case
            // is covered separately below.
            result.steps[0].drift = true
            result.steps[1].drift = false

            let data = try pwRunnerEncodeJSON(result)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectEqual(decoded.schema_version, 7)
            try expectNotNil(decoded.validator_subprocess)
            try expectEqual(decoded.validator_subprocess?.pid, 9002)
            try expectEqual(decoded.validator_subprocess?.exit_code, 0)
            try expectNil(decoded.validator_subprocess?.term_signal)
            try expectEqual(decoded.steps[0].drift, true)
            try expectEqual(decoded.steps[1].drift, false)
        }

        tk.run("v4: steps[].drift=nil encodes as explicit JSON null and decodes back to nil") {
            // Distinguishing "v4 producer chose not to populate" from
            // "v3 producer never wrote the key" requires the encoder to
            // emit explicit null. The decoder still gives back nil
            // either way, but a consumer that introspects the raw JSON
            // sees the key.
            let result = okResult(pid: 9100, stepCount: 1)
            try expectNil(result.steps[0].drift)
            let data = try pwRunnerEncodeJSON(result)
            let raw = String(data: data, encoding: .utf8) ?? ""
            try expectTrue(raw.contains("\"drift\":null"),
                           "expected explicit \"drift\":null in v4 envelope; raw=\(raw)")
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectNil(decoded.steps[0].drift)
        }
    }

    tk.group("nullable query PID") {
        tk.run("no worker PID encodes null; legacy integer PID remains readable") {
            var result = okResult(stepCount: 1)
            result.steps[0].sandbox_check.pid = nil
            let bytes = try pwRunnerEncodeJSON(result)
            let raw = try JSONSerialization.jsonObject(with: bytes) as! [String: Any]
            let step = (raw["steps"] as! [[String: Any]])[0]
            try expectTrue((step["sandbox_check"] as! [String: Any])["pid"] is NSNull)
            try expectNil(try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes).steps[0].sandbox_check.pid)
            result.schema_version = 5
            result.steps[0].sandbox_check.pid = 123
            let old = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(result))
            try expectEqual(old.schema_version, 5)
            try expectEqual(old.steps[0].sandbox_check.pid, 123)
        }
    }

    tk.group("response 6: signal absence and legacy compatibility") {
        tk.run("new success and failure steps encode literal signal null") {
            for outcome in [NormalizedOutcome.ok, NormalizedOutcome.runnerFailed, NormalizedOutcome.runnerTimeout] {
                var result = okResult(stepCount: 1)
                result.normalized_outcome = outcome
                result.rc = outcome == NormalizedOutcome.ok ? 0 : 1
                let bytes = try pwRunnerEncodeJSON(result)
                let raw = try JSONSerialization.jsonObject(with: bytes) as! [String: Any]
                try expectEqual(raw["schema_version"] as? Int, 7)
                let step = (raw["steps"] as! [[String: Any]])[0]
                try expectTrue(step["deny_signal"] is NSNull)
                try expectTrue(step["drift"] is NSNull)
                try expectNil(try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes).steps[0].deny_signal)
            }
        }
        tk.run("stored response 4 signal object remains decodable without upgrading its version") {
            var old = okResult(stepCount: 1)
            old.schema_version = 4
            old.steps[0].deny_signal = PWRunnerSignalResult(signal: "SIGUSR1", count_before: 0, count_after: 0)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(old))
            try expectEqual(decoded.schema_version, 4)
            try expectEqual(decoded.steps[0].deny_signal?.delta, 0)
            try expectEqual(decoded.steps[0].deny_signal?.signal, "SIGUSR1")
        }
        tk.run("client XPC failure emitters share response 7 default") {
            for outcome in [NormalizedOutcome.xpcError, NormalizedOutcome.xpcTimeout,
                            NormalizedOutcome.xpcProxyTypeMismatch, NormalizedOutcome.xpcNoReply] {
                let result = hostShortCircuitResult(outcome: outcome)
                let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(result))
                try expectEqual(decoded.schema_version, 7)
                try expectNil(decoded.runner_subprocess)
                try expectTrue(decoded.steps.isEmpty)
            }
        }
    }

    tk.group("PWRunnerRunResult: host short-circuit result") {

        tk.run("runner_subprocess is nil when no worker was spawned") {
            for outcome in [
                NormalizedOutcome.workerSpawnFailed,
                NormalizedOutcome.libsandboxUnavailable,
                NormalizedOutcome.badRequest,
                NormalizedOutcome.badPolicy,
                NormalizedOutcome.alreadyRan,
            ] {
                let result = hostShortCircuitResult(outcome: outcome)
                try expectNil(result.runner_subprocess, "outcome=\(outcome)")
                try expectTrue(result.steps.isEmpty, "outcome=\(outcome) has steps=\(result.steps)")
            }
        }
    }

    tk.group("PWRunnerRunResult: post-spawn failure result") {

        tk.run("runner_subprocess is present even when no worker report arrived") {
            // runner_timeout: host SIGKILLed the worker after the deadline.
            let timeout = postSpawnFailureResult(
                outcome: NormalizedOutcome.runnerTimeout,
                signal: 9
            )
            try expectNotNil(timeout.runner_subprocess)
            try expectEqual(timeout.runner_subprocess?.term_signal, 9)
            try expectNil(timeout.runner_subprocess?.exit_code)

            // Stored legacy outcome spelling; a signal does not establish cause.
            let denied = postSpawnFailureResult(
                outcome: NormalizedOutcome.runnerSandboxDenied,
                signal: 5
            )
            try expectNotNil(denied.runner_subprocess)
            try expectEqual(denied.runner_subprocess?.term_signal, 5)

            // runner_failed: worker exited non-zero before writing a report.
            let failed = postSpawnFailureResult(
                outcome: NormalizedOutcome.runnerFailed,
                signal: nil
            )
            try expectNotNil(failed.runner_subprocess)
            try expectEqual(failed.runner_subprocess?.exit_code, 1)
            try expectNil(failed.runner_subprocess?.term_signal)
        }

        tk.run("top-level pid agrees with worker pid even without a report") {
            let result = postSpawnFailureResult(
                outcome: NormalizedOutcome.runnerTimeout,
                signal: 9
            )
            try expectEqual(result.pid, result.runner_subprocess?.pid)
        }
    }
}

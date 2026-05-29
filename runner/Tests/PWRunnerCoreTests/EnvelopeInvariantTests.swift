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
            deny_signal: PWRunnerSignalResult(signal: "SIGUSR1", count_before: 0, count_after: 0)
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

        tk.run("schema_version is 4, test_overrides is nil, runner_subprocess is present") {
            let result = okResult(pid: 7777, stepCount: 2)
            try expectEqual(result.schema_version, 4)
            try expectNil(result.test_overrides)
            try expectNotNil(result.runner_subprocess)
            // validator_subprocess defaults to nil on the legacy path.
            // Production wiring (Step 6.8) populates it when the host
            // takes the C-worker code path. v4 consumers branching on
            // `validator_subprocess != nil` see the right value.
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
            try expectEqual(decoded.schema_version, 4)
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

            // runner_sandbox_denied: kernel sandbox terminated the worker.
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

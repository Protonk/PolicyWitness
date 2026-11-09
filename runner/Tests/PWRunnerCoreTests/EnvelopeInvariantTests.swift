import Foundation
@testable import PWRunnerCore

// Typed host reporting invariants. The registered independent receipt readers
// check public projection and JSON absence/null spelling.

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
                result.phases[0].validator_subprocess?.records?[0].operation = "file-write-unlink"
                result.phases[0].validator_subprocess?.records?[0].filterValue = path
                if state != "present" { try FileManager.default.removeItem(atPath: path) }
                if state == "recreated" { FileManager.default.createFile(atPath: path, contents: Data("new".utf8)) }
                result.steps = enrichPathDiagnostics(steps: [step])
                let data = try admittedReplyData(result)
                let decoded = try reportedReply(result).steps[0]
                try expectEqual(decoded.comparison?.observation, "succeeded")
                try expectEqual(decoded.comparison?.order, "unestablished")
                try expectEqual(decoded.comparison?.limitations, [])
                try expectEqual(decoded.sandbox_check.outcome, "allow")
                try expectEqual(decoded.sandbox_check.path_diagnostics?.stage, "after_orchestration")
                // Later host nonresolution is visible only in the path block.
                try expectEqual(decoded.sandbox_check.path_diagnostics?.realpath_resolved == nil, state == "absent")

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
            result.phases[0].validator_subprocess?.records?[0].operation = "process-exec*"
            let encoded = try admittedReplyData(result)
            let decoded = try reportedReply(result)
            try expectEqual(decoded.steps[0].comparison?.observation_basis, "spawned_child")
            try expectEqual(decoded.steps[0].comparison?.limitations, [])
            try expectEqual(decoded.steps[0].attempt.requested_kind, "exec")
            try expectEqual(decoded.steps[0].attempt.outcome, "exec_failed")
            try expectEqual(decoded.steps[0].attempt.rc, 37)
            try expectEqual(decoded.steps[0].attempt.child_pid, 123)
            try expectEqual(decoded.steps[0].attempt.stdout, "controlled marker")
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
            let data = try admittedReplyData(result)
            let decoded = try reportedReply(result)
            try expectEqual(decoded.steps[0].comparison?.limitations, [])
            try expectNil(decoded.steps[0].sandbox_check.native_rc)
            try expectEqual(decoded.steps[0].comparison?.order, "unestablished")
            try expectEqual(decoded.steps[0].sandbox_check.missing_reason, "validator_no_verdict")
        }
    }
    tk.group("exact response version") {
        tk.run("the producer default is the manifest version and other versions fail admission") {
            let fresh = PWRunnerRunResult(specimen_id: "s", rc: 1, normalized_outcome: NormalizedOutcome.badRequest,
                error: "constructed", pid: 1, policy_format: "sbpl", steps: [])
            try expectEqual(fresh.schema_version, PWContract.responseSchema)
            try fresh.validateForReporting()
            for version in [1, 7, 12, PWContract.responseSchema + 1] {
                var invalid = fresh; invalid.schema_version = version
                try expectThrows { try invalid.validateForReporting() }
            }
        }
    }
    tk.group("PWRunnerSubprocess: additive host observations") {
        tk.run("absent typed observations remain unknown") {
            let decoded = PWRunnerSubprocess(pid: 42, exit_code: 0, partial_steps: false)
            _ = try pwPorcelainEncode(decoded)
            try expectEqual(decoded.exit_code, 0)
            try expectNil(decoded.ready_byte_received)
            try expectNil(decoded.done_observed)
            try expectNil(decoded.poll_stop_reason)
            try expectNil(decoded.exit_requested)
            try expectNil(decoded.termination_request)
            try expectNil(decoded.reaped)
            try expectNil(decoded.wait_errors)
        }
        tk.run("observed false and empty errors survive encoding without inventing status") {
            let record = PWRunnerSubprocess(pid: 42, term_signal: nil, exit_code: nil,
                partial_steps: true, ready_byte_received: false, done_observed: false,
                poll_stop_reason: "wait_error", exit_requested: true, reaped: false, wait_errors: [])
            _ = try pwPorcelainEncode(record)
            let decoded = record
            try expectEqual(decoded.ready_byte_received, false)
            try expectEqual(decoded.done_observed, false)
            try expectEqual(decoded.reaped, false)
            try expectEqual(decoded.wait_errors?.count, 0)
            try expectNil(decoded.exit_code)
            try expectNil(decoded.term_signal)
            try expectNil(decoded.termination_request)
        }
        tk.run("unfamiliar host observation strings and errno values survive encoding") {
            let record = PWRunnerSubprocess(pid: 42, term_signal: nil, exit_code: nil,
                partial_steps: false, poll_stop_reason: "future_stop",
                termination_request: PWRunnerTerminationRequest(signal: 31, rc: -1, errno: 123456),
                reaped: false, wait_errors: [PWRunnerWaitError(stage: "future_phase", rc: -1, errno: 654321)])
            _ = try pwPorcelainEncode(record)
            let decoded = record
            try expectEqual(decoded.poll_stop_reason, "future_stop")
            try expectEqual(decoded.termination_request?.signal, 31)
            try expectEqual(decoded.termination_request?.rc, -1)
            try expectEqual(decoded.termination_request?.errno, 123456)
            try expectEqual(decoded.wait_errors?.first?.stage, "future_phase")
            try expectEqual(decoded.wait_errors?.first?.rc, -1)
            try expectEqual(decoded.wait_errors?.first?.errno, 654321)
        }
    }

    tk.group("PWRunnerRunResult: typed reporting preserves semantic absence") {
        tk.run("nil test_overrides survives reporting as nil") {
            var original = try replyFixture()
            original.test_overrides = nil
            let data = try admittedReplyData(original)
            let decoded = try reportedReply(original)
            try expectNil(decoded.test_overrides)
        }

    }

    tk.group("PWRunnerRunResult: production-shaped result") {
        tk.run("top-level pid agrees with runner_subprocess.pid") {
            // The mirror-back contract: top-level pid names the sandboxed
            // worker process when runner_subprocess is present, so consumers
            // using pid for execution diagnostics reach the worker.
            let result = try replyFixture()
            try expectEqual(result.pid, result.runner_subprocess?.pid)
        }
        tk.run("validator_subprocess and every step survive reporting") {
            let original = try replyFixture()
            let data = try admittedReplyData(original)
            let decoded = try reportedReply(original)
            try expectEqual(decoded.steps.count, original.steps.count)
            try expectEqual(decoded.phases[0].validator_subprocess?.pid, original.phases[0].validator_subprocess?.pid)
            try expectEqual(decoded.phases[0].validator_subprocess?.exit_code, original.phases[0].validator_subprocess?.exit_code)
            try expectNil(decoded.phases.first?.validator_subprocess?.term_signal)
        }
        tk.run("no worker PID encodes an explicit null query PID") {
            var result = try replyFixture()
            result.steps[0].sandbox_check.pid = nil
            result.steps[0].comparison?.order = "unestablished"
            let bytes = try admittedReplyData(result)
            try expectNil(try reportedReply(result).steps[0].sandbox_check.pid)
            guard let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"] else {
                throw TestFailure(message: "PW_TEST_ARTIFACTS is required")
            }
            let directory = URL(fileURLWithPath: artifacts).appendingPathComponent("porcelain-replies", isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            try bytes.write(to: directory.appendingPathComponent("null-query-pid.pwp"))
        }

    }

    tk.group("PWRunnerRunResult: host short-circuit result") {
        tk.run("runner_subprocess is nil when no worker was spawned") {
            for outcome in [
                NormalizedOutcome.workerSpawnFailed,
                NormalizedOutcome.badRequest,
                NormalizedOutcome.badPolicy,
            ] {
                let result = hostShortCircuitResult(outcome: outcome)
                try expectNil(result.runner_subprocess, "outcome=\(outcome)")
                try expectTrue(result.steps.isEmpty, "outcome=\(outcome) has steps=\(result.steps)")
                _ = try admittedReplyData(result)
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
            let decoded = try reportedReply(timeout)
            try expectNotNil(decoded.runner_subprocess?.disposition)
            try expectNotNil(decoded.phases.first?.ordering)
        }
    }
}

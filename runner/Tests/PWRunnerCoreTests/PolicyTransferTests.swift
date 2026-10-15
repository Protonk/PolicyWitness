import Foundation
import Darwin
@testable import PWRunnerCore

func runPolicyTransferTests(_ tk: TestKit) {
    tk.group("policy delivery") {
        tk.run("stalled reader reaches host cleanup before fixture watchdog") {
            guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
                throw TestFailure(message: "required lifecycle fixture missing")
            }
            let start = Date()
            var input = CWorkerInput(workerExecutablePath: path,
                policy: "hold_input\n" + String(repeating: "x", count: 200_000), slots: [], exitGraceMs: 20)
            input.policyTransferTimeoutMs = 100
            var hookCalls = 0
            let result = runCWorker(input, postApplied: { _ in hookCalls += 1 })
            try expectTrue(Date().timeIntervalSince(start) < 3, "stalled policy input reached fixture watchdog instead of host cleanup")
            guard case .failure(_, let partial) = result, let out = partial else {
                throw TestFailure(message: "stalled input must fail with partial output")
            }
            try expectEqual(out.pollStopReason, "policy_transfer_deadline")
            try expectEqual(out.termSignal, SIGKILL)
            try expectEqual(hookCalls, 0)
            try expectNil(out.policyTransferError)
            try expectEqual(out.policyTransferTimeout?.budget_ms, 100)
            try expectTrue(out.policyTransferTimeout!.elapsed_ms >= 100)
            try expectEqual(out.policyTransferTimeout?.bytes_expected, input.policy.utf8.count)
            try expectTrue(out.policyTransferTimeout!.bytes_written > 0 && out.policyTransferTimeout!.bytes_written < input.policy.utf8.count)
            try expectEqual(out.cleanupTrigger, "policy_transfer_timeout")
            try expectEqual(out.collectionBasis, "after_confirmed_reap")
            try expectFalse(out.applied)
            try expectFalse(out.hookInvoked)
            // Timeout and kill before any receipt: the fixture publishes none, and
            // the account carries none. Absence establishes nothing about delivery.
            try expectNil(out.workerEvidence?.policy_read)
            try expectEqual(classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0).outcome, NormalizedOutcome.runnerTimeout)
            _ = try retainTransferReply(out, result: result, name: "timeout", fixture: path)
        }
        tk.run("draining fixture receives complete unmodified policy") {
            guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else { throw TestFailure(message: "fixture missing") }
            let result = runCWorker(CWorkerInput(workerExecutablePath: path,
                policy: "drain_bytes\n" + String(repeating: "x", count: 200_000), slots: []))
            guard case .success(let out) = result else { throw TestFailure(message: "drain failed: \(result)") }
            try expectEqual(out.exitCode, 24, "fixture independently checks every input byte and EOF")
            try expectNil(out.policyTransferTimeout)
            try expectNil(out.policyTransferError)
        }
        tk.run("timeout survives failed kill and unconfirmed reap") {
            guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else { throw TestFailure(message: "fixture missing") }
            var input = CWorkerInput(workerExecutablePath: path,
                policy: "hold_input\n" + String(repeating: "x", count: 200_000), slots: [], exitGraceMs: 10)
            input.policyTransferTimeoutMs = 100
            var calls = ChildProcessCalls()
            calls.kill = { _, _ in errno = EPERM; return -1 }
            let result = runCWorker(input, processCalls: calls)
            guard case .failure(.policyTransferTimedOut, let partial) = result, let out = partial else {
                throw TestFailure(message: "missing timeout output")
            }
            defer { _ = Darwin.kill(out.workerPid, SIGKILL); var status: Int32 = 0
                while Darwin.waitpid(out.workerPid, &status, 0) < 0 && errno == EINTR {} }
            try expectEqual(out.reaped, false)
            try expectNil(out.exitCode); try expectNil(out.termSignal)
            try expectEqual(out.terminationRequest?.errno, EPERM)
            try expectEqual(out.collectionBasis, "execution_may_continue")
            try expectEqual(out.policyTransferTimeout?.budget_ms, 100)
            try expectNil(out.workerEvidence?.policy_read)
            _ = try retainTransferReply(out, result: result, name: "unconfirmed", fixture: path)
        }
        tk.run("truncated delivery joins the host timeout with the shipped worker's length refusal") {
            // The shipped worker, not the fixture: the EOF receipt and the refusal are
            // its own publications. The injected writer uses native writes to deliver
            // exactly the first 28 of 43 bytes, accounting for actual write results,
            // then reports no progress (EAGAIN) while the poll sleeps for its allowance
            // until the short transfer deadline expires. Returning zero would be an
            // immediate host diagnostic, not a timeout. The exit grace is generous so
            // the worker's own exit, not a scheduling race, ends the account.
            guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
                throw TestFailure(message: "required lifecycle fixture missing")
            }
            let worker = shippedWorkerPath()
            guard FileManager.default.isExecutableFile(atPath: worker) else {
                throw TestFailure(message: "required equipment: pw-probe-runner missing; run ./build.sh")
            }
            let submission = "(version 1)\n(allow default)\n(deny default)\n"
            try expectEqual(submission.utf8.count, 43)
            try expectEqual(policyReceiptCapacityBytes, PWShmLayout.policyBytes - 1, "receipt bound mirrors the layout")
            // A sysctl attempt: the reply is assembled by the step builder alone, and
            // file attempts also carry host path diagnostics the full orchestration adds.
            let step = PWRunnerProbeStep(step_id: "sysctl_ostype",
                sandbox_check: PWRunnerSandboxCheck(operation: "sysctl-read",
                    filter: PWRunnerSandboxFilter(kind: "sysctl_name", value: "kern.ostype")),
                attempt: PWRunnerAttempt(kind: "sysctl", action: "read", target: "kern.ostype"))
            var input = CWorkerInput(workerExecutablePath: worker, policy: submission,
                slots: [CWorkerSlotInput(stepId: "sysctl_ostype", attemptKind: .sysctlRead, target: "kern.ostype")],
                exitGraceMs: 3_000)
            input.policyTransferTimeoutMs = 100
            var delivered = 0
            var calls = PolicyTransferCalls()
            calls.write = { fd, bytes, count in
                if delivered >= 28 { errno = EAGAIN; return -1 }
                let n = Darwin.write(fd, bytes, min(count, 28 - delivered))
                if n > 0 { delivered += n }
                return n
            }
            calls.poll = { _, ms in usleep(useconds_t(max(ms, 1)) * 1_000); return 0 }
            let result = runCWorker(input, processCalls: ChildProcessCalls(), transferCalls: calls)
            guard case .failure(.policyTransferTimedOut, let partial) = result, let out = partial else {
                throw TestFailure(message: "the truncated transfer must time out with partial output: \(result)")
            }
            try expectEqual(delivered, 28)
            // Host half: the timeout with its counts, stop reason and cleanup trigger.
            try expectEqual(out.policyTransferTimeout?.bytes_written, 28)
            try expectEqual(out.policyTransferTimeout?.bytes_expected, 43)
            try expectNil(out.policyTransferError)
            try expectEqual(out.pollStopReason, "policy_transfer_deadline")
            try expectEqual(out.cleanupTrigger, "policy_transfer_timeout")
            // Worker half: the receipt of what it read, and the refusal naming that count.
            try expectEqual(out.workerEvidence?.policy_read, PWWorkerPolicyRead(bytes_expected: 43, bytes_received: 28))
            try expectEqual(out.workerEvidence?.failure?.operation, 2)
            try expectEqual(out.workerEvidence?.failure?.code, 13)
            try expectEqual(out.workerEvidence?.failure?.detail, 28)
            try expectNil(out.workerEvidence?.readiness, "no readiness publication precedes the refusal")
            try expectFalse(out.readyByteReceived); try expectFalse(out.applied); try expectFalse(out.done)
            try expectTrue(out.slots.allSatisfy { !$0.completed }, "no attempt runs under a refused policy")
            // The worker exited on its own refusal code during grace; nothing was killed.
            try expectEqual(out.exitCode, 11); try expectNil(out.termSignal)
            try expectEqual(out.reaped, true); try expectEqual(out.graceEnd, "reaped_during_grace")
            try expectNil(out.terminationRequest); try expectEqual(out.collectionBasis, "after_confirmed_reap")
            // Precedence: the observed worker failure classifies the run; the host
            // timeout remains in the diagnostic and on the record.
            let summary = classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 1)
            try expectEqual(summary.outcome, NormalizedOutcome.runnerFailed)
            try expectContains(summary.error ?? "", "code=13")
            try expectContains(summary.error ?? "", "received=28")
            try expectContains(summary.error ?? "", "wrote 28 of 43")
            let bytes = try retainTransferReply(out, result: result, name: "refused", fixture: fixture,
                                                plan: [step], expectedVerdictCount: 1)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
            try expectEqual(decoded.runner_subprocess?.worker_evidence?.policy_read,
                            PWWorkerPolicyRead(bytes_expected: 43, bytes_received: 28))
            try expectEqual(decoded.steps.count, 1)
            try expectEqual(decoded.steps[0].attempt.result_source, "synthetic")
            // Rejected variants: a fabricated kill or exit contradicts the disposition
            // record; a receipt that disagrees with the refusal's detail, the host's
            // expectation or the capacity contradicts the receipt rules. Both the
            // encoder and the decoder refuse them.
            func rejected(_ reason: String, _ mutate: (inout PWRunnerSubprocess) -> Void) throws {
                var variant = decoded
                mutate(&variant.runner_subprocess!)
                try expectThrows({ _ = try pwRunnerEncodeJSON(variant) }, { error in
                    try expectContains("\(error)", reason)
                })
            }
            try rejected("contradicts its basis") { sub in
                sub.termination_request = PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil)
                sub.term_signal = 9; sub.exit_code = nil
            }
            try rejected("contradicts its basis") { sub in sub.exit_code = 0 }
            try rejected("policy read receipt") { sub in sub.worker_evidence?.policy_read?.bytes_received = 29 }
            try rejected("policy read receipt") { sub in sub.worker_evidence?.policy_read?.bytes_expected = 44 }
            try rejected("policy read receipt") { sub in sub.worker_evidence?.policy_read?.bytes_received = -1 }
            try rejected("policy read receipt") { sub in
                sub.worker_evidence?.policy_read = PWWorkerPolicyRead(bytes_expected: PWShmLayout.policyBytes, bytes_received: 28)
            }
            var document = try JSONSerialization.jsonObject(with: bytes) as! [String: Any]
            var sub = document["runner_subprocess"] as! [String: Any]
            var evidence = sub["worker_evidence"] as! [String: Any]
            evidence["policy_read"] = ["bytes_expected": 43, "bytes_received": 43]
            sub["worker_evidence"] = evidence; document["runner_subprocess"] = sub
            let mutated = try JSONSerialization.data(withJSONObject: document)
            try expectThrows({ _ = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: mutated) }, { error in
                try expectContains("\(error)", "policy read receipt")
            })
        }
        tk.run("interruption backpressure and slow progress share one absolute deadline") {
            for mode in ["interrupted", "backpressure", "slow"] {
                var now: UInt64 = 0
                var calls = PolicyTransferCalls()
                calls.clock = { now += 1_000_000; return now }
                calls.write = { _, _, _ in
                    if mode == "slow" { return 1 }
                    errno = mode == "interrupted" ? EINTR : EAGAIN; return -1
                }
                var allowances: [Int32] = []
                calls.poll = { _, ms in allowances.append(ms); errno = EINTR; return -1 }
                let deadline = MonotonicDeadline(milliseconds: 10, clock: calls.clock)
                let result = writePolicy(Array(repeating: 120, count: 100), fd: -1, deadline: deadline, calls: calls)
                guard case .timeout(let elapsed) = result.stop else { throw TestFailure(message: "deadline restarted: \(mode)") }
                try expectEqual(elapsed, 10)
                try expectTrue(result.written < 100)
                try expectTrue(allowances.allSatisfy { $0 > 0 && $0 <= 8 })
            }
        }
        tk.run("partial writes preserve offsets and zero progress and clock loss fail closed") {
            var accepted: [UInt8] = []
            var calls = PolicyTransferCalls(); calls.clock = { 1 }
            calls.write = { _, bytes, count in let n = min(3, count)
                accepted += Array(UnsafeBufferPointer(start: bytes.assumingMemoryBound(to: UInt8.self), count: n)); return n }
            let bytes = Array("unmodified-UTF8-é".utf8)
            let deadline = MonotonicDeadline(milliseconds: 10, clock: calls.clock)
            let result = writePolicy(bytes, fd: -1, deadline: deadline, calls: calls)
            guard case .complete = result.stop else { throw TestFailure(message: "partial writes failed") }
            try expectEqual(accepted, bytes)
            calls.write = { _, _, _ in 0 }
            guard case .failed(let diagnostic) = writePolicy(bytes, fd: -1, deadline: deadline, calls: calls).stop else { throw TestFailure(message: "zero write accepted") }
            try expectContains(diagnostic, "zero")
            let noClock = MonotonicDeadline(milliseconds: 10, clock: { nil })
            guard case .failed = writePolicy(bytes, fd: -1, deadline: noClock, calls: calls).stop else { throw TestFailure(message: "missing clock accepted") }
            try expectEqual(MonotonicDeadline.pollMilliseconds(1), 1)
            try expectEqual(MonotonicDeadline.pollMilliseconds(1_000_001), 2)
        }
    }
}

private func shippedWorkerPath() -> String {
    if let app = ProcessInfo.processInfo.environment["PW_APP_DIR"] {
        return app + "/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner"
    }
    return repositoryRoot()
        .appendingPathComponent("dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner").path
}

/// Assemble the actual driver account with the production builders and retain
/// it beside the fixture for the controller's replay test. One resolved
/// disposition record serves the subprocess and the step projections.
@discardableResult
private func retainTransferReply(_ out: CWorkerOutput, result: CWorkerRunResult, name: String, fixture: String,
                                 plan: [PWRunnerProbeStep] = [], expectedVerdictCount: Int = 0) throws -> Data {
    let summary = classify(workerResult: result, validatorResult: nil, expectedVerdictCount: expectedVerdictCount)
    let record = resolveDisposition(out, plan: plan)
    let sub = buildWorkerSubprocess(out, disposition: record)
    let steps = buildStepResults(probePlan: plan, queryPlan: planValidatorQueries(plan), workerOutput: out,
        validatorOutput: nil, ordering: buildOrdering(out, validatorOutput: nil, hasQueries: !plan.isEmpty),
        disposition: record)
    let reply = PWRunnerRunResult(specimen_id: name, rc: summary.rc, normalized_outcome: summary.outcome,
        error: summary.error, pid: Int(getpid()), policy_format: "sbpl", sandboxed_after_apply: out.applied,
        steps: steps, runner_subprocess: sub,
        phases: [constructedPhase(out, ids: plan.map { $0.step_id }, hasQueries: !plan.isEmpty)])
    let bytes = try pwRunnerEncodeJSON(reply)
    let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
    try expectEqual(decoded.runner_subprocess?.policy_transfer_timeout?.bytes_written, out.policyTransferTimeout?.bytes_written)
    try bytes.write(to: URL(fileURLWithPath: fixture).deletingLastPathComponent().appendingPathComponent("policy-transfer-\(name).json"))
    return bytes
}

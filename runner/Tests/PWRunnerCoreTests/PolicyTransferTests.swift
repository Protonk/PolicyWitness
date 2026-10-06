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
            try expectEqual(classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0).outcome, NormalizedOutcome.runnerTimeout)
            try retainTransferReply(out, result: result, name: "timeout", fixture: path)
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
            try retainTransferReply(out, result: result, name: "unconfirmed", fixture: path)
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

private func retainTransferReply(_ out: CWorkerOutput, result: CWorkerRunResult, name: String, fixture: String) throws {
    let summary = classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0)
    var sub = buildWorkerSubprocess(out)
    sub.ordering = buildOrdering(out, validatorOutput: nil, hasQueries: false)
    let reply = PWRunnerRunResult(specimen_id: name, rc: summary.rc, normalized_outcome: summary.outcome,
        error: summary.error, pid: Int(getpid()), policy_format: "sbpl", sandboxed_after_apply: out.applied,
        steps: [], runner_subprocess: sub)
    let bytes = try pwRunnerEncodeJSON(reply)
    let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
    try expectEqual(decoded.runner_subprocess?.policy_transfer_timeout?.bytes_written, out.policyTransferTimeout?.bytes_written)
    try bytes.write(to: URL(fileURLWithPath: fixture).deletingLastPathComponent().appendingPathComponent("policy-transfer-\(name).json"))
}

import Darwin
import Foundation
@testable import PWRunnerCore

/*
 * WorkerClockTests — the C worker's continuous-time setup and timing refusals
 * through the real host driver. Companion executables compile the production
 * C main with one clock boundary substituted (tests/fixtures/worker_lifecycle/
 * clock_failure.c); each seam leaves a stale EPERM that must not be reported.
 * These establish publication, transport and interpretation, not platform
 * clock behavior or a sandbox cause.
 */

private func clockCompanion(_ suffix: String) throws -> String {
    guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
        throw TestFailure(message: "required lifecycle equipment missing; run runner_unit")
    }
    let companion = path + suffix
    guard FileManager.default.isExecutableFile(atPath: companion) else {
        throw TestFailure(message: "required companion missing: \(companion)")
    }
    return companion
}

/// A sysctl step: the step builder alone assembles its reply, while file
/// attempts also carry path diagnostics that only full orchestration adds.
private func clockStep() -> PWRunnerProbeStep {
    PWRunnerProbeStep(step_id: "s", sandbox_check: PWRunnerSandboxCheck(operation: "sysctl-read",
        filter: PWRunnerSandboxFilter(kind: "sysctl_name", value: "kern.ostype")),
        attempt: PWRunnerAttempt(kind: "sysctl", action: "read", target: "kern.ostype"))
}

/// Encode the reply the host would assemble, round-trip it, and leave it beside
/// the fixture for the Rust assembly and independent-consumer replay.
private func retainClockReply(_ out: CWorkerOutput, result: CWorkerRunResult, name: String,
                              plan: [PWRunnerProbeStep]) throws -> PWRunnerRunResult {
    let summary = classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0)
    let record = resolveDisposition(out, plan: plan)
    let reply = PWRunnerRunResult(specimen_id: name, rc: summary.rc, normalized_outcome: summary.outcome,
        error: summary.error, pid: Int(getpid()), policy_format: "sbpl", sandboxed_after_apply: out.applied,
        steps: buildStepResults(probePlan: plan, queryPlan: planValidatorQueries(plan), workerOutput: out,
            validatorOutput: nil, ordering: buildOrdering(out, validatorOutput: nil, hasQueries: false),
            disposition: record),
        runner_subprocess: buildWorkerSubprocess(out, disposition: record),
        phases: [constructedPhase(out, ids: plan.map { $0.step_id }, hasQueries: false)])
    let bytes = try pwRunnerEncodeJSON(reply)
    let directory = URL(fileURLWithPath: try clockCompanion("")).deletingLastPathComponent()
    try bytes.write(to: directory.appendingPathComponent("worker-clock-\(name).json"))
    return try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
}

private func expectSameFailure(_ a: PWWorkerFailure?, _ b: PWWorkerFailure?) throws {
    try expectEqual(a?.operation, b?.operation); try expectEqual(a?.code, b?.code)
    try expectEqual(a?.native_kind, b?.native_kind); try expectEqual(a?.native_result, b?.native_result)
    try expectEqual(a?.errno, b?.errno); try expectEqual(a?.index, b?.index); try expectEqual(a?.detail, b?.detail)
}

private func appEquipment(_ name: String) -> String {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent()
    let app = ProcessInfo.processInfo.environment["PW_APP_DIR"] ?? root.appendingPathComponent("dist/PolicyWitness.app").path
    return app + "/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/" + name
}

private func accessProbe(_ id: String) -> PWRunnerProbeStep {
    PWRunnerProbeStep(step_id: id, sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
        filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
        attempt: PWRunnerAttempt(kind: "file", action: "access", target: "/etc/hosts"))
}

private func sleepProbe(_ id: String) -> PWRunnerProbeStep {
    PWRunnerProbeStep(step_id: id, sandbox_check: PWRunnerSandboxCheck(operation: "process-exec*",
        filter: PWRunnerSandboxFilter(kind: "path", value: "/bin/sleep")),
        attempt: PWRunnerAttempt(kind: "exec", action: "spawn", target: "/bin/sleep", args: ["5"]))
}

/// Full production orchestration with a companion worker and the shipped
/// validator. `collectionDelayMs` holds the second phase's validator launch,
/// so a worker refusal or expiry occurs while that collection is open.
private func clockPhases(_ suffix: String, first: PWRunnerProbeStep, collectionDelayMs: UInt32 = 0,
                         name: String) throws -> PWRunnerRunResult {
    var launches = 0
    var reply = CWorkerOrchestrator.run(parsed: PWRunnerRunSpec(specimen_id: name,
        policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)(allow default)"),
        phases: [PWRunnerPhase(phase_id: "first", actions: [.probe(first)]),
                 PWRunnerPhase(phase_id: "second", actions: [.probe(accessProbe("later"))])]),
        policyHash: "test", bundleId: nil, workerExecutablePath: try clockCompanion(suffix),
        validatorExecutablePath: appEquipment("sb_api_validator"),
        validatorSpawn: { pid, path, actions, argv in
            launches += 1
            if launches == 2 && collectionDelayMs > 0 { usleep(collectionDelayMs * 1_000) }
            return nativeValidatorSpawn(pid, path, actions, argv)
        })
    // The service adds host path diagnostics after orchestration.
    reply.steps = enrichPathDiagnostics(steps: reply.steps)
    let bytes = try pwRunnerEncodeJSON(reply)
    let directory = URL(fileURLWithPath: try clockCompanion("")).deletingLastPathComponent()
    try bytes.write(to: directory.appendingPathComponent("worker-clock-\(name).json"))
    return try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
}

/// The second phase never acknowledged: its prediction may survive, but its
/// attempt is unavailable and no query order is established.
private func expectSecondPhaseUnreleased(_ reply: PWRunnerRunResult, collected: Bool) throws {
    try expectTrue(reply.phases[1].arrival_observed)
    try expectFalse(reply.phases[1].completion_observed)
    try expectEqual(reply.phases[1].ordering?.proceed_observed, false)
    try expectFalse(reply.steps[1].attempt.result_source == "worker")
    try expectEqual(reply.steps[1].comparison?.order, "unestablished")
    if collected {
        try expectEqual(reply.phases[1].collection_status, "collected")
        try expectEqual(reply.phases[1].validator_subprocess?.records?.map { $0.stepId }, ["later"])
        try expectEqual(reply.steps[1].sandbox_check.outcome, "allow")
    }
}

/// A spawned child the worker killed but could not confirm is reparented when
/// the worker exits; confirm its absence independently, killing it if needed.
private func expectChildGone(_ pid: Int?) throws {
    guard let pid, pid > 0 else { throw TestFailure(message: "no spawned child recorded") }
    for _ in 0..<500 {
        if Darwin.kill(pid_t(pid), 0) != 0 && errno == ESRCH { return }
        usleep(10_000)
    }
    _ = Darwin.kill(pid_t(pid), SIGKILL)
    throw TestFailure(message: "spawned child \(pid) survived the worker's group cleanup")
}

func runWorkerClockTests(_ tk: TestKit) {
    tk.group("worker clock setup refusal: production main through the real host driver") {
        // (name, companion, code, native kind, native result, detail)
        let setups: [(String, String, UInt32, UInt32, Int32?, UInt32)] = [
            ("native", ".clock-setup-failure", 1, 1, KERN_INVALID_ARGUMENT, 0),
            ("zero_factor", ".clock-zero-factor", 14, 0, nil, 1),
            ("unrepresentable", ".clock-unrepresentable", 14, 0, nil, 2),
        ]
        for (name, suffix, code, kind, native, detail) in setups {
            for blocked in [false, true] {
                let label = "\(name) \(blocked ? "blocks policy delivery" : "follows buffered delivery")"
                tk.run("\(label): published refusal, exit 12, no receipt, application or action") {
                    // A source larger than the pipe buffer is still being written when the
                    // worker refuses; a short one is fully buffered before the refusal.
                    let filler = blocked ? "\n;" + String(repeating: "x", count: 200_000) : ""
                    let input = CWorkerInput(workerExecutablePath: try clockCompanion(suffix),
                        policy: "(version 1)(allow default)" + filler,
                        slots: [CWorkerSlotInput(stepId: "s", attemptKind: .sysctlRead, target: "kern.ostype")],
                        sentinelTimeoutMs: 5_000, exitGraceMs: 2_000)
                    var hookCalls = 0
                    let result = runCWorker(input, postApplied: { _ in hookCalls += 1 })
                    let out: CWorkerOutput
                    switch (blocked, result) {
                    case (false, .success(let observed)):
                        out = observed
                        try expectNil(out.policyTransferError)
                    case (true, .failure(.policyWriteFailed, let partial?)):
                        out = partial
                        try expectEqual(out.policyTransferError?.errno, EPIPE)
                        try expectTrue(out.policyTransferError!.bytes_written < input.policy.utf8.count)
                        try expectEqual(out.pollStopReason, "policy_write_error")
                    default:
                        throw TestFailure(message: "unexpected driver result: \(result)")
                    }
                    let failure = out.workerEvidence?.failure
                    try expectEqual(out.workerEvidence?.failure_state, "published")
                    try expectEqual(failure?.operation, 12)
                    try expectEqual(failure?.code, code)
                    try expectEqual(failure?.native_kind, kind)
                    try expectEqual(failure?.native_result, native)
                    try expectNil(failure?.errno, "a stale permission errno is never a timing result")
                    try expectNil(failure?.index)
                    try expectEqual(failure?.detail, detail)
                    try expectEqual(out.workerEvidence?.progress?.operation, 12)
                    try expectEqual(out.workerEvidence?.progress?.stage, 2)
                    try expectNil(out.workerEvidence?.policy_read, "no policy byte was read")
                    try expectNil(out.workerEvidence?.readiness)
                    try expectFalse(out.readyByteReceived || out.applied || out.done)
                    try expectEqual(out.applyRC, 0, "no status-word failure is claimed")
                    try expectEqual(hookCalls, 0)
                    try expectFalse(out.proceedObserved || out.phases.contains { $0.arrived || $0.acknowledged })
                    try expectTrue(out.slots.allSatisfy { !$0.completed })
                    try expectEqual(out.reaped, true)
                    try expectEqual(out.exitCode, 12); try expectNil(out.termSignal)
                    let summary = classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0)
                    try expectEqual(summary.outcome, NormalizedOutcome.runnerFailed)
                    try expectContains(summary.error ?? "", "clock setup failure (code=\(code))")
                    if code == 14 { try expectContains(summary.error ?? "", "no policy byte read") }
                    if blocked { try expectContains(summary.error ?? "", "host write(policy_pipe)") }
                    let record = resolveDisposition(out, plan: [clockStep()])
                    try expectEqual(record.questions["progress_association"]?.answer, "none")
                    try expectEqual(record.steps[0].questions["step_result_published"]?.answer, "unpublished")
                    let decoded = try retainClockReply(out, result: result,
                        name: "setup-\(name)-\(blocked ? "blocked" : "buffered")", plan: [clockStep()])
                    let sub = decoded.runner_subprocess
                    try expectSameFailure(sub?.worker_evidence?.failure, failure)
                    try expectEqual(sub?.exit_code, 12)
                    try expectEqual(sub?.done_observed, false)
                    try expectEqual(decoded.sandboxed_after_apply, false)
                    try expectEqual(decoded.steps[0].attempt.result_source, "synthetic")
                }
            }
        }
    }
    tk.group("worker timing faults across phases: production orchestration and shipped validator") {
        tk.run("phase 2's own backwards sample refuses after phase 1 completes and keeps its prediction") {
            let reply = try clockPhases(".clock-phase2", first: accessProbe("first"), collectionDelayMs: 400, name: "phase2-own-sample")
            let failure = reply.runner_subprocess?.worker_evidence?.failure
            try expectEqual(reply.normalized_outcome, NormalizedOutcome.runnerFailed)
            try expectEqual(failure?.operation, 11); try expectEqual(failure?.code, 14)
            try expectEqual(failure?.detail, 3); try expectEqual(failure?.index, 1)
            try expectNil(failure?.native_result); try expectNil(failure?.errno)
            try expectContains(reply.runner_subprocess?.worker_evidence?.diagnostic.text ?? "", "proceed start")
            try expectContains(reply.error ?? "", "local timing refusal reason=backwards_counter")
            // Phase 1's chain, prediction and native result are untouched.
            try expectEqual(reply.phases[0].ordering?.chainEstablished, true)
            try expectEqual(reply.steps[0].attempt.result_source, "worker")
            try expectEqual(reply.steps[0].attempt.rc, 0)
            try expectEqual(reply.steps[0].comparison?.order, "query_first")
            try expectSecondPhaseUnreleased(reply, collected: true)
        }
        tk.run("phase 2 expiry from a valid forward jump retains its open collection") {
            let reply = try clockPhases(".clock-expire2", first: accessProbe("first"), collectionDelayMs: 600, name: "phase2-expiry")
            let failure = reply.runner_subprocess?.worker_evidence?.failure
            try expectEqual(failure?.operation, 11); try expectEqual(failure?.code, 8)
            try expectEqual(failure?.detail, 60_000); try expectEqual(failure?.index, 1)
            try expectContains(reply.error ?? "", "budget=60000 ms")
            try expectEqual(reply.steps[0].comparison?.order, "query_first")
            try expectSecondPhaseUnreleased(reply, collected: true)
        }
        tk.run("a rejected exec sample in phase 1 refuses phase 2 by provenance, without a new sample") {
            let reply = try clockPhases(".clock-sticky", first: sleepProbe("first"), name: "sticky-provenance")
            let attempt = reply.steps[0].attempt
            try expectEqual(attempt.rc, -1); try expectNil(attempt.errno, "a local timing fault carries no errno")
            try expectContains(attempt.error ?? "", "local_timing=backwards_counter stage=exec_observe")
            try expectContains(attempt.error ?? "", "phase=0 slot=0")
            if attempt.child_term_signal != Int(SIGKILL) {
                // Reaping stopped under the unusable clock: status stays missing.
                try expectEqual(attempt.child_exit_code, -1); try expectContains(attempt.error ?? "", "reaped=0")
            }
            try expectChildGone(attempt.child_pid)
            let failure = reply.runner_subprocess?.worker_evidence?.failure
            try expectEqual(failure?.operation, 11); try expectEqual(failure?.code, 14)
            try expectEqual(failure?.detail, 6); try expectEqual(failure?.index, 1)
            try expectContains(reply.runner_subprocess?.worker_evidence?.diagnostic.text ?? "",
                               "first rejected sample: reason=backwards_counter stage=exec_observe phase=0 slot=0")
            try expectContains(reply.error ?? "", "proceed refused: worker clock already invalid")
            try expectFalse((reply.error ?? "").contains("local timing refusal reason=backwards_counter"),
                            "the later refusal is not a new regression")
            try expectEqual(reply.phases[0].ordering?.chainEstablished, true)
            try expectSecondPhaseUnreleased(reply, collected: reply.phases[1].collection_status == "collected")
        }
        tk.run("an exec arithmetic refusal stays local; phase 2 releases, acknowledges and acts") {
            let reply = try clockPhases(".clock-arith", first: sleepProbe("first"), name: "arithmetic-local")
            let attempt = reply.steps[0].attempt
            try expectEqual(attempt.rc, -1); try expectNil(attempt.errno)
            try expectContains(attempt.error ?? "", "local_timing=deadline_overflow stage=exec_observe")
            try expectFalse((attempt.error ?? "").contains("first rejected sample"))
            try expectEqual(attempt.child_term_signal, Int(SIGKILL), "the valid clock confirms the group cleanup")
            try expectChildGone(attempt.child_pid)
            try expectNil(reply.runner_subprocess?.worker_evidence?.failure)
            try expectTrue(reply.phases.allSatisfy { $0.completion_observed && $0.ordering?.chainEstablished == true })
            try expectEqual(reply.steps[1].attempt.result_source, "worker")
            try expectEqual(reply.steps[1].attempt.rc, 0)
            try expectEqual(reply.steps[1].comparison?.order, "query_first")
        }
    }
}

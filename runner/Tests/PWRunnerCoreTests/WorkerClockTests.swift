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

/// A test-owned handshake with the clock companion. The driver reaches phase-2
/// collection before authorizing the injected sample. The receipt establishes
/// that the fixture selected that sample; the final reply independently proves
/// failure publication and absent acknowledgement/actions, even after release.
private final class WorkerClockGate {
    let directory: URL
    private var events: [String] = []
    private var ownsDirectory = false

    init(_ suffix: String) throws {
        directory = URL(fileURLWithPath: try clockCompanion(suffix) + ".gate")
        // Refuse stale gates instead of allowing an earlier trigger to release.
        guard Darwin.mkdir(directory.path, 0o700) == 0 else {
            throw TestFailure(message: "cannot create fresh clock gate (errno=\(errno)): \(directory.path)")
        }
        ownsDirectory = true
    }

    deinit { if ownsDirectory { try? FileManager.default.removeItem(at: directory) } }

    func has(_ marker: String) -> Bool {
        FileManager.default.fileExists(atPath: directory.appendingPathComponent(marker).path)
    }

    func wait(_ marker: String, timeoutMs: UInt64 = 6_000) throws {
        let deadline = DispatchTime.now().uptimeNanoseconds + timeoutMs * 1_000_000
        while !has(marker) {
            if DispatchTime.now().uptimeNanoseconds >= deadline {
                events.append("timeout:\(marker)")
                throw TestFailure(message: "clock fixture did not publish \(marker)")
            }
            usleep(1_000)
        }
        events.append("observed:\(marker)")
    }

    func releaseFromCollection(delayMs: UInt32) throws {
        events.append("collection-entered")
        try wait("ready")
        try expectFalse(has("injected"), "the fixture injected before collection authorized it")
        // Deliberate host descheduling stress while authorization is withheld.
        // The marker handshake, not this delay, establishes the ordering.
        if delayMs > 0 { usleep(delayMs * 1_000) }
        try expectFalse(has("injected"), "the fixture injected while the host withheld its trigger")
        try expectFalse(has("timed-out"), "fixture gate timed out before authorization")
        try Data().write(to: directory.appendingPathComponent("collection-open"), options: .withoutOverwriting)
        events.append("collection-authorized")
        try wait("injected")
        try expectFalse(has("timed-out"))
    }

    func retain(_ name: String) throws {
        let receipt: [String: Any] = ["host_events": events,
            "worker_ready": has("ready"), "collection_authorized": has("collection-open"),
            "sample_injected": has("injected"), "fixture_timed_out": has("timed-out")]
        let bytes = try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
        try bytes.write(to: directory.deletingLastPathComponent().appendingPathComponent("worker-clock-\(name)-gate.json"))
    }
}

/// Full production orchestration with a companion worker and the shipped
/// validator. A non-nil gate delay enables explicit phase-2 synchronization;
/// zero exercises prompt authorization and a positive value stresses a late host.
private func clockPhases(_ suffix: String, first: PWRunnerProbeStep, gateDelayMs: UInt32? = nil,
                         name: String) throws -> PWRunnerRunResult {
    let gate = try gateDelayMs.map { _ in try WorkerClockGate(suffix) }
    var gateFailure: Error?
    var launches = 0
    var reply = CWorkerOrchestrator.run(parsed: PWRunnerRunSpec(specimen_id: name,
        policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)(allow default)"),
        phases: [PWRunnerPhase(phase_id: "first", actions: [.probe(first)]),
                 PWRunnerPhase(phase_id: "second", actions: [.probe(accessProbe("later"))])]),
        policyHash: "test", bundleId: nil, workerExecutablePath: try clockCompanion(suffix),
        validatorExecutablePath: appEquipment("sb_api_validator"),
        validatorSpawn: { pid, path, actions, argv in
            launches += 1
            if launches == 2, let gate {
                do { try gate.releaseFromCollection(delayMs: gateDelayMs ?? 0) }
                catch { gateFailure = error; return EIO }
            }
            return nativeValidatorSpawn(pid, path, actions, argv)
        })
    // The driver still owns worker cleanup when a handshake fails. Only throw
    // after orchestration has returned; retain failed coordination receipts too.
    try gate?.retain(name)
    if let gateFailure { throw gateFailure }
    if gate != nil { try expectEqual(launches, 2, "phase-2 collection was not reached") }
    // The service adds host path diagnostics after orchestration.
    reply.steps = enrichPathDiagnostics(steps: reply.steps)
    let bytes = try pwRunnerEncodeJSON(reply)
    let directory = URL(fileURLWithPath: try clockCompanion("")).deletingLastPathComponent()
    try bytes.write(to: directory.appendingPathComponent("worker-clock-\(name).json"))
    return try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
}

/// The second phase never acknowledged: retain any native query observation,
/// but its attempt is unavailable and no query order is established.
private func expectSecondPhaseUnreleased(_ reply: PWRunnerRunResult, collected: Bool) throws {
    try expectTrue(reply.phases[1].arrival_observed)
    try expectFalse(reply.phases[1].completion_observed)
    try expectEqual(reply.phases[1].ordering?.proceed_observed, false)
    try expectFalse(reply.steps[1].attempt.result_source == "worker")
    try expectEqual(reply.steps[1].comparison?.order, "unestablished")
    if collected {
        try expectEqual(reply.phases[1].collection_status, "collected")
        let records = reply.phases[1].validator_subprocess?.records ?? []
        try expectEqual(records.map { $0.stepId }, ["later"])
        guard let record = records.first, let nativeRC = record.rc else {
            throw TestFailure(message: "collected native query record missing its return value")
        }
        // Refusal can exit the target before the shipped validator queries it.
        // Preserve its actual native answer without choosing a live-target label.
        try expectTrue(["allow", "deny", "error"].contains(record.outcome))
        let query = reply.steps[1].sandbox_check
        try expectEqual(query.result_source, "validator")
        try expectEqual(query.outcome, record.outcome)
        try expectEqual(query.rc, nativeRC)
        try expectEqual(query.native_rc, nativeRC)
        try expectEqual(query.errno, record.errnoVal)
        try expectEqual(query.error, record.error)
        try expectEqual(query.operation, record.operation)
        try expectEqual(query.filter_value, record.filterValue)
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
        for delay in [UInt32(0), 350] {
            let schedule = delay == 0 ? "prompt host" : "delayed host"
            let suffix = delay == 0 ? "" : "-delayed-host"
            tk.run("phase 2's own backwards sample retains its native query observation (\(schedule))") {
                let reply = try clockPhases(".clock-phase2", first: accessProbe("first"), gateDelayMs: delay,
                                            name: "phase2-own-sample" + suffix)
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
            tk.run("phase 2 expiry retains its open collection (\(schedule))") {
                let reply = try clockPhases(".clock-expire2", first: accessProbe("first"), gateDelayMs: delay,
                                            name: "phase2-expiry" + suffix)
                let failure = reply.runner_subprocess?.worker_evidence?.failure
                try expectEqual(failure?.operation, 11); try expectEqual(failure?.code, 8)
                try expectEqual(failure?.detail, 60_000); try expectEqual(failure?.index, 1)
                try expectContains(reply.error ?? "", "budget=60000 ms")
                try expectEqual(reply.steps[0].comparison?.order, "query_first")
                try expectSecondPhaseUnreleased(reply, collected: true)
            }
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
    tk.group("clock fixture handshake failure and cleanup") {
        tk.run("missing fixture receipt fails within the host's gate allowance") {
            let gate = try WorkerClockGate(".clock-phase2")
            var refused = false
            do { try gate.wait("ready", timeoutMs: 20) }
            catch is TestFailure { refused = true }
            try gate.retain("missing-receipt")
            try expectTrue(refused)
            try expectFalse(gate.has("collection-open") || gate.has("injected"))
        }
        tk.run("a stale gate is refused and its existing trigger is preserved") {
            let owned = try WorkerClockGate(".clock-phase2")
            let trigger = owned.directory.appendingPathComponent("collection-open")
            try Data("stale trigger".utf8).write(to: trigger)
            var refused = false
            do { _ = try WorkerClockGate(".clock-phase2") }
            catch is TestFailure { refused = true }
            try expectTrue(refused)
            try expectEqual(try String(contentsOf: trigger), "stale trigger")
        }
        tk.run("withheld authorization times out the fixture and the driver reaps it") {
            let gate = try WorkerClockGate(".clock-phase2")
            var gateFailure: Error?
            var collections: [Int] = []
            let input = CWorkerInput(workerExecutablePath: try clockCompanion(".clock-phase2"),
                policy: "(version 1)(allow default)",
                slots: [CWorkerSlotInput(stepId: "first", attemptKind: .sysctlRead, target: "kern.ostype"),
                        CWorkerSlotInput(stepId: "later", attemptKind: .sysctlRead, target: "kern.ostype")],
                phases: [CWorkerPhaseInput(firstSlot: 0, endSlot: 1), CWorkerPhaseInput(firstSlot: 1, endSlot: 2)],
                sentinelTimeoutMs: 1_000, exitGraceMs: 1_000)
            let result = runCWorker(input, phaseBoundary: { _, index in
                collections.append(index)
                if index == 1 {
                    do { try gate.wait("ready"); try gate.wait("timed-out") }
                    catch { gateFailure = error }
                }
            })
            try gate.retain("withheld-authorization")
            if let gateFailure { throw gateFailure }
            guard case .success(let out) = result else {
                throw TestFailure(message: "fixture driver failed: \(result)")
            }
            try expectEqual(collections, [0, 1])
            try expectEqual(out.reaped, true)
            try expectTrue(out.applied && out.phases[0].completed)
            try expectEqual(out.exitCode, 71); try expectNil(out.termSignal)
            try expectFalse(out.done || out.phases[1].acknowledged || out.slots[1].completed)
            try expectNil(out.workerEvidence?.failure, "fixture timeout must not fabricate a production timing failure")
            try expectFalse(gate.has("collection-open") || gate.has("injected"))
        }
    }
}

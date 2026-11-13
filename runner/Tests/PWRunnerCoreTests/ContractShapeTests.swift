import Foundation
@testable import PWRunnerCore

func repositoryRoot() -> URL {
    URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
}

// Shape fixtures are typed producer evidence. Public object shape is checked
// by the independent Python binary reader after this executable writes receipts.
private func shapeSlot(_ id: String, completed: Bool) -> CWorkerSlotResult {
    CWorkerSlotResult(stepId: id, rc: 0, errnoVal: 0, observedPath: completed ? "/private/owned" : nil,
                      error: nil, completed: completed)
}

private func shapeProgress(_ op: UInt32, _ stage: UInt32, index: UInt32? = nil) -> PWWorkerProgress {
    let item: UInt32 = index.map { $0 + 1 } ?? 0
    return PWWorkerProgress(raw: (op << 24) | (stage << 20) | item, operation: op, stage: stage, index: index)
}

private func shapeProbe(_ id: String, kind: String = "file", action: String = "open_read") -> PWRunnerProbeStep {
    PWRunnerProbeStep(step_id: id,
        sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                                            filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
        attempt: PWRunnerAttempt(kind: kind, action: action, target: "/etc/hosts"))
}

private func shapeDiagnostic() -> PWWorkerDiagnostic {
    PWWorkerDiagnostic(state: 2, status: "truncated", length: 4, text: "text")
}

/// Worker accounts the field-complete fixture cannot carry at once, resolved
/// and assembled by the production builders so the encoder accepts them:
/// a confirmed exit whose progress word says the second attempt returned while
/// its slot stayed incomplete (the D5 conflict, with its issue and the
/// synthetic attempt's missing reason); a signalled worker with a termination
/// request, a published failure and a policy transfer error; a confirmed exit
/// whose progress word is unusable (unresolved step claims with reasons); a
/// plan whose attempt kind the worker does not support (inapplicable claims);
/// and a worker reaped before any exit was requested (inapplicable cleanup
/// claims with reasons). Each returns the output and the plan it answers.
private func shapeWorkerOutputs() -> [(CWorkerOutput, [PWRunnerProbeStep])] {
    var conflict = CWorkerOutput(
        workerPid: 42, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0, done: true,
        exitCode: 0, termSignal: nil, slots: [shapeSlot("first", completed: true), shapeSlot("second", completed: false)],
        pollStopReason: "done", exitRequested: true, terminationRequest: nil, reaped: true, waitErrors: [],
        workerEvidence: PWWorkerEvidence(abi_identity: Data(PWShmLayout.abiIdentity), progress: shapeProgress(9, 2, index: 1),
            failure_publication: 0, failure_state: "absent", failure: nil,
            readiness: PWWorkerReadiness(rc: 1, errno: 0), diagnostic: shapeDiagnostic()))
    conflict.cleanupTrigger = "completion"
    conflict.graceEnd = "reaped_during_grace"
    conflict.collectionBasis = "after_confirmed_reap"
    var signalled = CWorkerOutput(
        workerPid: 42, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0, done: false,
        exitCode: nil, termSignal: 9, slots: [shapeSlot("first", completed: true)],
        pollStopReason: "sentinel_deadline", exitRequested: true,
        terminationRequest: PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil), reaped: true,
        waitErrors: [PWRunnerWaitError(stage: "exit_grace", rc: -1, errno: 10)],
        workerEvidence: PWWorkerEvidence(abi_identity: Data(PWShmLayout.abiIdentity), progress: shapeProgress(10, 2),
            failure_publication: 1, failure_state: "published",
            failure: PWWorkerFailure(operation: 10, code: 1, native_kind: 1, native_result: -1, errno: 22, index: 0, detail: 0),
            readiness: PWWorkerReadiness(rc: 1, errno: 0), diagnostic: shapeDiagnostic()))
    signalled.policyTransferError = PWWorkerPolicyTransferError(errno: 32, bytes_written: 10, bytes_expected: 100)
    signalled.cleanupTrigger = "deadline_expiry"
    signalled.graceEnd = "exhausted"
    signalled.collectionBasis = "after_confirmed_reap"
    var unusable = conflict
    unusable.slots = [shapeSlot("first", completed: false)]
    var word = shapeProgress(9, 1, index: 0)
    word.raw = shapeProgress(9, 1, index: 1).raw
    unusable.workerEvidence?.progress = word
    var unsupported = conflict
    unsupported.slots = [shapeSlot("first", completed: true)]
    unsupported.workerEvidence?.progress = nil
    var crashed = conflict
    crashed.done = false
    crashed.exitCode = nil
    crashed.termSignal = 11
    crashed.slots = [shapeSlot("first", completed: false)]
    crashed.pollStopReason = "child_reaped"
    crashed.exitRequested = false
    crashed.cleanupTrigger = "child_reaped"
    crashed.graceEnd = "not_entered"
    crashed.workerEvidence?.progress = shapeProgress(9, 1, index: 0)
    var transferTimedOut = signalled
    transferTimedOut.policyTransferError = nil
    transferTimedOut.policyTransferTimeout = PWWorkerPolicyTransferTimeout(budget_ms: 5000, elapsed_ms: 5001, bytes_written: 8192, bytes_expected: 200000)
    transferTimedOut.pollStopReason = "policy_transfer_deadline"
    transferTimedOut.cleanupTrigger = "policy_transfer_timeout"
    // The worker's EOF receipt beside the host's write progress: a valid partial
    // observation (unequal counts, no length refusal) that agrees with the host's
    // own expectation on the timeout record.
    transferTimedOut.applied = false
    transferTimedOut.readyByteReceived = false
    transferTimedOut.slots = [shapeSlot("first", completed: false)]
    transferTimedOut.workerEvidence?.readiness = nil
    transferTimedOut.workerEvidence?.progress = shapeProgress(2, 2)
    transferTimedOut.workerEvidence?.failure_publication = 0
    transferTimedOut.workerEvidence?.failure_state = "absent"
    transferTimedOut.workerEvidence?.failure = nil
    transferTimedOut.workerEvidence?.policy_read = PWWorkerPolicyRead(bytes_expected: 200000, bytes_received: 8192)
    // The resolver supports absent host observations even though the current
    // live driver supplies both. Exercise that documented fallback through
    // typed reporting and encoding, not by adding allowlist keys by hand.
    var unrecorded = conflict
    unrecorded.slots = [shapeSlot("first", completed: true)]
    unrecorded.workerEvidence?.progress = nil
    unrecorded.pollStopReason = nil
    unrecorded.collectionBasis = nil
    return [
        (transferTimedOut, [shapeProbe("first")]),
        (conflict, [shapeProbe("first"), shapeProbe("second")]),
        (signalled, [shapeProbe("first")]),
        (unusable, [shapeProbe("first")]),
        (unsupported, [shapeProbe("first", kind: "future", action: "future")]),
        (crashed, [shapeProbe("first")]),
        (unrecorded, [shapeProbe("first")]),
    ]
}

/// Every encoded document whose keys the reply golden records: the
/// field-complete fixture, its degraded reply (`reporting_failure` beside the
/// retained evidence), the fixture with a signalled validator, and the
/// production-shaped worker accounts above. Only the encoder's output counts:
/// a key appears in the golden because the producer emitted it.
func replyShapeDocuments() throws -> [PWRunnerRunResult] {
    var documents: [PWRunnerRunResult] = []
    let base = try replyFixture()
    documents.append(base)
    var defective = base
    defective.steps[0].comparison?.order = "future_order"
    documents.append(try reportedReply(defective))
    var signalledValidator = base
    signalledValidator.phases[0].validator_subprocess?.term_signal = 9
    signalledValidator.phases[0].validator_subprocess?.exit_code = nil
    try signalledValidator.validateForReporting()
        documents.append(signalledValidator)
    var spawnFailed = base
    spawnFailed.phases[0].validator_subprocess = nil
    spawnFailed.phases[0].validator_spawn_failure = validatorSpawnFailureFixture()
    spawnFailed.phases[0].ordering?.validator_disposition = "not_spawned"
    spawnFailed.steps[0].comparison?.order = "unestablished"
    try spawnFailed.validateForReporting()
        documents.append(spawnFailed)
    for (out, plan) in shapeWorkerOutputs() {
        let record = resolveDisposition(out, plan: plan)
        let sub = buildWorkerSubprocess(out, disposition: record)
        let ordering = buildOrdering(out, validatorOutput: nil, hasQueries: true)
        let reply = PWRunnerRunResult(specimen_id: "shape", rc: 0, normalized_outcome: NormalizedOutcome.finished,
            pid: Int(out.workerPid), policy_format: "sbpl", sandboxed_after_apply: out.applied,
            steps: buildStepResults(probePlan: plan, queryPlan: planValidatorQueries(plan), workerOutput: out,
                                    validatorOutput: nil, ordering: ordering, disposition: record),
            runner_subprocess: sub, phases: [constructedPhase(out, ids: plan.map { $0.step_id })])
        try reply.validateForReporting()
        documents.append(reply)
    }
    documents += try ordinaryReadShapeDocuments()
    documents += try freshWriteShapeDocuments()
    documents += try execObservationShapeDocuments()
    documents += try actorShapeDocuments()
    return documents
}

func runContractShapeTests(_ tk: TestKit) {
    let root = repositoryRoot()
    tk.group("Worker identity and reply shapes") {
        tk.run("worker identity bytes agree with their hex presentation") {
            try expectEqual(PWShmLayout.abiIdentity.count, PWShmLayout.abiIdentityBytes)
            try expectEqual(PWShmLayout.abiIdentity.map { String(format: "%02x", $0) }.joined(),
                            PWShmLayout.abiIdentityHex)
        }
        tk.run("retain admitted typed shape companions for independent presentation checks") {
            guard let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"] else {
                throw TestFailure(message: "PW_TEST_ARTIFACTS is required for shape receipts")
            }
            let directory = URL(fileURLWithPath: artifacts).appendingPathComponent("porcelain-shapes", isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            for (index, reply) in try replyShapeDocuments().enumerated() {
                try reply.validateForReporting()
                try pwPorcelainEncode(reply).write(to: directory.appendingPathComponent(String(format: "%03d.pwp", index)))
            }
        }
        tk.run("actor capture companions retain per-process success and unavailable contexts") {
            var captured = 0, unavailable = 0
            for document in try actorShapeDocuments() {
                try expectNil(document.compiled_profile)
                for actor in document.actors ?? [] {
                    guard let receipt = actor.compiled_profile else { continue }
                    try expectEqual(receipt.worker_pid, actor.subprocess?.pid)
                    if receipt.status == "captured" {
                        captured += 1
                        try expectEqual(receipt.producer, "worker")
                        try expectEqual(receipt.capture_stage, "before_apply")
                        try expectEqual(receipt.bytecode, Data([10, 20, 30]))
                        try expectNil(receipt.reason)
                    } else {
                        unavailable += 1
                        try expectEqual(receipt.status, "unavailable")
                        try expectEqual(receipt.reason, "successful_application_unconfirmed")
                        try expectNil(receipt.producer)
                        try expectNil(receipt.capture_stage)
                        try expectNil(receipt.bytecode)
                    }
                }
            }
            try expectTrue(captured >= 2 && unavailable >= 1)
        }
    }
}

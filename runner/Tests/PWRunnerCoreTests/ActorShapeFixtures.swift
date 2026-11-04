import Foundation
@testable import PWRunnerCore

/*
 * Constructed actor-form replies for the reply shape golden and the maximal
 * reply model. The production translation and assembly run over constructed
 * scheduler outcomes (no process is launched), so every key the actor form
 * emits appears because the producer emitted it: a completed three-actor
 * re-delegation, and a run with a refused launch, a failed setup, an
 * unavailable consume and a refused transfer.
 */

private func actorRequest(withOpenReads: Bool = true) -> String {
    let probe = { (id: String) in
        "{\"step_id\": \"\(id)\", \"sandbox_check\": {\"operation\": \"file-read-data\", \"filter\": {\"kind\": \"path\", \"value\": \"/private/etc/hosts\"}}, \"attempt\": {\"kind\": \"file\", \"action\": \"open_read\", \"target\": \"/private/etc/hosts\"}}"
    }
    return """
    {"schema_version": \(PWContract.requestSchema), "specimen_id": "shape", "run_kind": "shape",
     "actors": [{"actor_id": "A", "sandbox": {"mode": "unapplied"}},
                {"actor_id": "B", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"}}},
                {"actor_id": "C", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"}}}],
     "phases": [
       {"phase_id": "b_before", "actor_id": "B", "actions": [\(probe("b_read_before"))]},
       {"phase_id": "c_before", "actor_id": "C", "actions": [\(probe("c_read_before"))]},
       {"phase_id": "initial_supply", "actor_id": "A", "actions": [
         {"step_id": "a_issue", "extension": {"operation": "issue", "family": "file", "authority": "read", "target": "/private/shape/effect", "token_ref": "ta"}},
         {"step_id": "a_to_b", "extension": {"operation": "transfer", "token_ref": "ta", "recipient": "B", "delivery_ref": "db"}}]},
       {"phase_id": "b_consume", "actor_id": "B", "actions": [{"step_id": "b_consume_first", "extension": {"operation": "consume", "delivery_ref": "db", "handle_ref": "hb"}}]},
       {"phase_id": "b_redelegate", "actor_id": "B", "actions": [\(probe("b_read_after")),
         {"step_id": "b_issue", "extension": {"operation": "issue", "family": "file", "authority": "read_write", "target": "/private/shape/effect", "token_ref": "tb"}},
         {"step_id": "b_to_c", "extension": {"operation": "transfer", "token_ref": "tb", "recipient": "C", "delivery_ref": "dc"}}]},
       {"phase_id": "c_consume", "actor_id": "C", "actions": [{"step_id": "c_consume_second", "extension": {"operation": "consume", "delivery_ref": "dc", "handle_ref": "hc"}}]},
       {"phase_id": "c_effect", "actor_id": "C", "actions": [\(probe("c_read_after")), {"step_id": "c_release", "extension": {"operation": "release", "handle_ref": "hc"}}]},
       {"phase_id": "b_cleanup", "actor_id": "B", "actions": [{"step_id": "b_release", "extension": {"operation": "release", "handle_ref": "hb"}}]}]}
    """
}

private func shapeProgress(_ op: UInt32, _ stage: UInt32, index: UInt32? = nil) -> PWWorkerProgress {
    let item: UInt32 = index.map { $0 + 1 } ?? 0
    return PWWorkerProgress(raw: (op << 24) | (stage << 20) | item, operation: op, stage: stage, index: index)
}

/// One actor's constructed output: every slot published, every visit
/// completed, a clean reaped exit. `failures` names slots to publish as
/// unavailable (code 6) and `refusedTransfers` the transfers acknowledged as
/// custody unavailable.
private func actorOutput(_ input: CWorkerInput, index: Int, applies: Bool, failures: Set<String> = [],
                         refusedTransfers: Set<String> = []) -> CWorkerOutput {
    let slots = input.slots.map { slot -> CWorkerSlotResult in
        var result = CWorkerSlotResult(stepId: slot.stepId, rc: 0, errnoVal: 0, observedPath: "/private/shape/effect", error: nil, completed: true)
        guard slot.extensionOperands != nil else { return result }
        result.observedPath = nil
        if failures.contains(slot.stepId) {
            // A consume whose delivery never arrived, and the release of the
            // handle that consume never produced.
            result.unavailableCode = slot.attemptKind == .extensionRelease ? 2 : 6
            result.extensionPublication = CWorkerExtensionPublication(tokenLength: 0, custodyStatus: 0, transferStatus: 0)
            return result
        }
        result.unavailableCode = 0
        switch slot.attemptKind {
        case .extensionIssue:
            result.callBoundary = true; result.nativeResult = 1; result.nativeErrno = 0
            result.extensionPublication = CWorkerExtensionPublication(tokenLength: 40, custodyStatus: 1, transferStatus: 0)
        case .extensionTransfer:
            result.extensionPublication = CWorkerExtensionPublication(tokenLength: 0, custodyStatus: 0,
                transferStatus: refusedTransfers.contains(slot.stepId) ? PWTransferAck.custodyUnavailable : PWTransferAck.delivered)
        case .extensionConsume:
            result.callBoundary = true; result.nativeResult = 7; result.nativeErrno = 0
            result.extensionPublication = CWorkerExtensionPublication(tokenLength: 0, custodyStatus: 0, transferStatus: 0)
        default:
            result.callBoundary = true; result.nativeResult = 0; result.nativeErrno = 0
            result.extensionPublication = CWorkerExtensionPublication(tokenLength: 0, custodyStatus: 0, transferStatus: 0)
        }
        return result
    }
    var output = CWorkerOutput(workerPid: pid_t(100 + index), readyByteReceived: true, applied: applies, applyRC: 0, applyErrno: 0,
        done: true, exitCode: 0, termSignal: nil, slots: slots, pollStopReason: "done", exitRequested: true,
        terminationRequest: nil, reaped: true, waitErrors: [],
        workerEvidence: PWWorkerEvidence(abi_identity: PWShmLayout.abiIdentityHex, progress: shapeProgress(10, 2),
            failure_publication: 0, failure_state: "absent", failure: nil,
            readiness: PWWorkerReadiness(rc: 1, errno: 0),
            diagnostic: PWWorkerDiagnostic(state: 0, status: "absent", length: 0, text: nil),
            policy_read: PWWorkerPolicyRead(bytes_expected: input.policy.utf8.count, bytes_received: input.policy.utf8.count)))
    output.phases = input.phases.map { _ in
        CWorkerPhaseOutput(arrived: true, collectionClosed: true, releaseSet: true, acknowledged: true, completed: true,
                           ownershipEstablished: true, violations: [])
    }
    output.proceedSet = true; output.proceedObserved = true; output.proceedOwnershipEstablished = true; output.hookInvoked = true
    output.cleanupTrigger = "completion"; output.graceEnd = "reaped_during_grace"; output.collectionBasis = "after_confirmed_reap"
    output.actorSetup = applies ? 1 : 2
    output.activationObserved = UInt32(input.phases.last?.globalPhase ?? 0)
    output.policyReceivedSha256 = String(repeating: "f", count: 64)
    output.authorityStatus = 1; output.authorityDetail = 0; output.nativeSymbols = 7
    output.readyWait = PWHostWait(budget_ms: 1000, elapsed_ms: 1, stop: "received", native_errno: nil, clock_fault: false)
    output.graceWait = PWHostWait(budget_ms: 1000, elapsed_ms: 1, stop: "reaped_during_grace", native_errno: nil, clock_fault: false)
    return output
}

private func failedSetupOutput(_ input: CWorkerInput, index: Int) -> CWorkerOutput {
    var output = actorOutput(input, index: index, applies: true)
    output.applied = false; output.applyRC = -1; output.actorSetup = 0; output.activationObserved = 0
    output.slots = input.slots.map { CWorkerSlotResult(stepId: $0.stepId, rc: 0, errnoVal: 0, completed: false) }
    output.phases = input.phases.map { _ in CWorkerPhaseOutput() }
    output.proceedSet = false; output.proceedObserved = false; output.proceedOwnershipEstablished = false; output.hookInvoked = false
    output.workerEvidence?.progress = shapeProgress(5, 2)
    output.workerEvidence?.failure_publication = 1
    output.workerEvidence?.failure_state = "published"
    output.workerEvidence?.failure = PWWorkerFailure(operation: 5, code: 1, native_kind: 2, native_result: nil, errno: nil, index: nil, detail: 0)
    output.workerEvidence?.diagnostic = PWWorkerDiagnostic(state: 1, status: "complete", length: 12, text: "syntax error")
    return output
}

/// The constructed documents: a completed re-delegation and a run with a
/// refused launch (A), a failed setup (C) and an unavailable consume (B).
func actorShapeDocuments() throws -> [[String: Any]] {
    let parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: Data(actorRequest().utf8))
    guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "shape request refused") }
    let translation = ActorTranslation(plan: plan, parsed: parsed, workerExecutablePath: "/constructed/pw-probe-runner")
    func visits(_ reasons: [String]) -> [ActorVisitRecord] {
        plan.phases.map { phase in
            var visit = ActorVisitRecord(phaseIndex: phase.index, actorIndex: phase.actorIndex, visit: phase.visit - 1)
            let reason = reasons[phase.index]
            visit.endReason = reason
            if reason == "completed" {
                visit.activationStored = true; visit.arrivalObserved = true; visit.collectionInvoked = true
                visit.collectionClosed = true; visit.releaseStored = true; visit.acknowledgementObserved = true
                visit.completionObserved = true
                visit.activationToArrivalMs = 1; visit.collectionMs = 2; visit.arrivalToReleaseMs = 3; visit.releaseToCompletionMs = 1
            }
            return visit
        }
    }
    func record(_ index: Int, status: ActorSetupStatus, output: CWorkerOutput?, failure: CWorkerRunError? = nil) -> ActorSessionRecord {
        var record = ActorSessionRecord(index: index)
        record.setupStatus = status
        record.applicationCount = status == .applied ? 1 : 0
        record.pid = output.map { $0.workerPid }
        // A fixed widest parent PID keeps the derived reply maximum independent
        // of the test process's own PID.
        record.parentPid = pid_t.max
        record.output = output
        record.launchFailure = failure
        record.quiescence = output == nil ? "never_launched" : "reaped"
        record.authorityRegion = "mapped"
        record.stopReason = status.usable ? nil : status.rawValue
        return record
    }
    let local = { (step: String) -> Int in translation.local[plan.slotOfStep[step]!]!.slot }
    let assemble = { (outcome: ActorScheduleOutcome) throws -> [String: Any] in
        // The hook runs only for visits the schedule reached, and plans queries
        // the way the live host does.
        let queryPlans = plan.phases.map { planValidatorQueries($0.actions.compactMap { $0.probe }) }
        let statuses = plan.phases.map { phase -> String in
            guard outcome.visits.first(where: { $0.phaseIndex == phase.index })?.collectionInvoked == true else { return "not_reached" }
            return queryPlans[phase.index].contains { $0.probe != nil } ? "collected" : "not_needed"
        }
        let reply = assembleActorReply(parsed: parsed, plan: plan, translation: translation, outcome: outcome,
            queryPlans: queryPlans,
            validatorResults: plan.phases.map { _ in nil }, collectionStatuses: statuses, bundleId: "shape")
        return try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(reply)) as! [String: Any]
    }

    // ---- The completed re-delegation.
    let outputs = plan.actors.map { actorOutput(translation.inputs[$0.index], index: $0.index, applies: $0.applies) }
    var complete = ActorScheduleOutcome(
        actors: plan.actors.map { record($0.index, status: $0.applies ? .applied : .unappliedDeclared, output: outputs[$0.index]) },
        visits: visits(Array(repeating: "completed", count: plan.phases.count)), lifetimeCutoffTicks: 1,
        setupWait: PWHostWait(budget_ms: 10_000, elapsed_ms: 20, stop: "all_resolved", native_errno: nil, clock_fault: false),
        executionWait: PWHostWait(budget_ms: 120_000, elapsed_ms: 50, stop: "schedule_complete", excluded_ms: 16, native_errno: nil, clock_fault: false),
        cancelled: nil)
    complete.custody = [
        CustodyObservation(tokenIndex: 0, actorIndex: 0, slot: local("a_issue"), phaseIndex: 2, status: "accepted", rejectDetail: nil, length: 40, erased: true),
        CustodyObservation(tokenIndex: 1, actorIndex: 1, slot: local("b_issue"), phaseIndex: 4, status: "accepted", rejectDetail: nil, length: 40, erased: true),
    ]
    var first = TransferObservation(deliveryIndex: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 1, slot: local("a_to_b"),
        phaseIndex: 2, custodyStatus: "held", copyStatus: "copied", equality: "equal", acknowledgement: PWTransferAck.delivered)
    first.recipientAcknowledged = true; first.sourceAcknowledged = true
    first.recipientWait = PWHostWait(budget_ms: 5000, elapsed_ms: 1, stop: "acknowledged", native_errno: nil, clock_fault: false)
    var second = first
    second = TransferObservation(deliveryIndex: 1, tokenIndex: 1, sourceActorIndex: 1, recipientActorIndex: 2, slot: local("b_to_c"),
        phaseIndex: 4, custodyStatus: "held", copyStatus: "copied", equality: "equal", acknowledgement: PWTransferAck.delivered)
    second.recipientAcknowledged = true; second.sourceAcknowledged = true
    complete.transfers = [first, second]
    var documents = [try assemble(complete)]

    // ---- A refused launch, a failed setup, an unavailable consume and a
    // refused transfer; the schedule still visits B.
    let bOutput = actorOutput(translation.inputs[1], index: 1, applies: true, failures: ["b_consume_first", "b_release"], refusedTransfers: ["b_to_c"])
    var faulted = ActorScheduleOutcome(
        actors: [record(0, status: .launchRefused, output: nil, failure: .spawnFailed("constructed")),
                 record(1, status: .applied, output: bOutput),
                 record(2, status: .setupFailed, output: failedSetupOutput(translation.inputs[2], index: 2))],
        visits: visits(["completed", "actor_unavailable", "actor_unavailable", "completed", "completed", "actor_unavailable", "actor_unavailable", "completed"]),
        lifetimeCutoffTicks: 1, setupWait: nil, executionWait: nil, cancelled: nil)
    faulted.custody = [CustodyObservation(tokenIndex: 1, actorIndex: 1, slot: local("b_issue"), phaseIndex: 4, status: "rejected:length", rejectDetail: 5, length: nil)]
    faulted.transfers = [TransferObservation(deliveryIndex: 1, tokenIndex: 1, sourceActorIndex: 1, recipientActorIndex: 2, slot: local("b_to_c"),
        phaseIndex: 4, custodyStatus: "unavailable", copyStatus: "not_copied", equality: "not_compared", acknowledgement: PWTransferAck.custodyUnavailable)]
    documents.append(try assemble(faulted))
    return documents
}

import Darwin
import Foundation

/*
 * ActorOrchestration — the actor form's host path from an admitted,
 * normalized plan to one reply: per-actor driver inputs and the authority
 * plan, the serial schedule with fresh validator collection per phase against
 * the active actor, and the actor-indexed reply assembly.
 *
 * Every record is read from one owner: the actor's own slot and header
 * publications, the host's custody and transfer observations, the validator's
 * verdicts and the scheduler's visit records. No singular worker or policy
 * projection is designated for this form.
 */

extension CWorkerOrchestrator {
    static func runActors(
        parsed: PWRunnerRunSpec,
        plan: ActorPlan,
        bundleId: String?,
        workerExecutablePath: String,
        validatorExecutablePath: String,
        validatorSpawn: @escaping ValidatorSpawnCall,
        validatorProcessCalls: @escaping (Int) -> ChildProcessCalls
    ) -> PWRunnerRunResult {
        let translation = ActorTranslation(plan: plan, parsed: parsed, workerExecutablePath: workerExecutablePath)
        var input = ActorScheduleInput(actors: translation.inputs, applies: plan.actors.map { $0.applies },
                                       schedule: translation.schedule)
        input.authority = translation.authority

        // Fresh planning after each arrival; every collection closes before the
        // scheduler's guarded release. One aggregate allowance across actors.
        let phases = plan.phases
        var queryPlans = phases.map { _ in [ValidatorQueryDecision]() }
        var validatorResults = phases.map { _ -> ValidatorClientResult? in nil }
        var collectionStatuses = phases.map { _ in "not_reached" }
        var collectionRemainingNs = UInt64(max(1, min(PWActorLimits.collectionMs, parsed._test_overrides?.validator_total_timeout_ms ?? PWActorLimits.collectionMs))) * 1_000_000
        let outcome = ActorScheduler.run(input) { index, _, workerPid in
            guard let start = MonotonicDeadline.now() else {
                collectionStatuses[index] = "clock_unavailable"; collectionRemainingNs = 0; return
            }
            defer {
                if let end = MonotonicDeadline.now(), end >= start {
                    collectionRemainingNs -= min(collectionRemainingNs, end - start)
                } else { collectionRemainingNs = 0 }
            }
            queryPlans[index] = planValidatorQueries(phases[index].actions.compactMap { $0.probe })
            let probes = queryPlans[index].compactMap { $0.probe }
            if probes.isEmpty { collectionStatuses[index] = "not_needed"; return }
            guard let now = MonotonicDeadline.now(), now >= start else {
                collectionStatuses[index] = "clock_unavailable"; collectionRemainingNs = 0; return
            }
            let planningNs = now - start
            guard collectionRemainingNs > planningNs + 1_000_000 else {
                collectionStatuses[index] = "budget_exhausted"; return
            }
            let timeout = min(timeoutMsForValidator(override: parsed._test_overrides?.validator_io_timeout_ms),
                              Int((collectionRemainingNs - planningNs) / 1_000_000))
            let clientInput = ValidatorClientInput(executablePath: validatorExecutablePath, targetPid: workerPid,
                                                   probes: probes, verdictReadTimeoutMs: timeout)
            validatorResults[index] = runValidator(clientInput, processCalls: validatorProcessCalls(index), spawn: validatorSpawn)
            collectionStatuses[index] = "collected"
        }

        return assembleActorReply(parsed: parsed, plan: plan, translation: translation, outcome: outcome,
                                  queryPlans: queryPlans, validatorResults: validatorResults,
                                  collectionStatuses: collectionStatuses, bundleId: bundleId)
    }
}

// MARK: - Translation

/// Per-actor driver inputs, the schedule and the authority plan derived from
/// the normalized plan. Slot indexes inside each actor are that actor's own.
struct ActorTranslation {
    let inputs: [CWorkerInput]
    let schedule: [ActorScheduleEntry]
    let authority: AuthorityPlan?
    /// Global slot → (actor index, actor-local slot index).
    let local: [Int: (actor: Int, slot: Int)]
    /// Actor-local phase input per global phase.
    let phaseInputs: [CWorkerPhaseInput]

    init(plan: ActorPlan, parsed: PWRunnerRunSpec, workerExecutablePath: String) {
        var local: [Int: (actor: Int, slot: Int)] = [:]
        for actor in plan.actors {
            for (position, globalSlot) in actor.slots.enumerated() { local[globalSlot] = (actor.index, position) }
        }
        self.local = local
        let actionsBySlot: [Int: PWRunnerPhaseAction] = Dictionary(uniqueKeysWithValues:
            plan.phases.flatMap { phase in phase.actions.enumerated().map { (phase.firstSlot + $0.offset, $0.element) } })
        var phaseInputs: [CWorkerPhaseInput] = []
        var inputs: [CWorkerInput] = []
        for actor in plan.actors {
            var slots: [CWorkerSlotInput] = []
            for globalSlot in actor.slots {
                guard let action = actionsBySlot[globalSlot] else { continue }
                switch action {
                case .probe(let probe):
                    slots.append(makeWorkerSlot(stepID: probe.step_id, attempt: probe.attempt))
                case .extensionAction(let value):
                    slots.append(ActorTranslation.extensionSlot(value, plan: plan, globalSlot: globalSlot))
                }
            }
            var phases: [CWorkerPhaseInput] = []
            for phaseIndex in actor.visits {
                let phase = plan.phases[phaseIndex]
                // Empty visits have no global action of their own: firstSlot
                // can name the next actor's action. Partition this actor's
                // slots using its accumulated offset instead.
                let first = phases.last?.endSlot ?? 0
                let input = CWorkerPhaseInput(firstSlot: first, endSlot: first + phase.actions.count, globalPhase: phaseIndex + 1)
                phases.append(input)
            }
            let policy = actor.policy
            var input = CWorkerInput(workerExecutablePath: workerExecutablePath,
                                     policy: policy?.sbpl_source ?? "",
                                     params: policy.map(workerParamsFromPolicy) ?? [],
                                     slots: slots, phases: phases,
                                     sentinelTimeoutMs: PWActorLimits.executionMs,
                                     captureCompiledProfile: policy?.capture_compiled_profile == true,
                                     captureNonce: policy?.capture_nonce)
            input.proceedWaitMs = PWActorLimits.releaseWaitMs
            inputs.append(input)
        }
        for phase in plan.phases {
            let actor = plan.actors[phase.actorIndex]
            let position = actor.visits.firstIndex(of: phase.index) ?? 0
            phaseInputs.append(inputs[phase.actorIndex].phases[position])
        }
        self.phaseInputs = phaseInputs
        self.inputs = inputs
        schedule = plan.phases.map { ActorScheduleEntry(phaseIndex: $0.index, actorIndex: $0.actorIndex, visit: $0.visit - 1) }
        if plan.tokens.isEmpty && plan.deliveries.isEmpty {
            authority = nil
        } else {
            authority = AuthorityPlan(
                tokens: plan.tokens.enumerated().map { index, token in
                    AuthorityPlanToken(index: index, actorIndex: token.actorIndex, slot: local[token.slot]?.slot ?? 0,
                                       lastUseSlot: local[token.lastUseSlot]?.slot ?? 0)
                },
                deliveries: plan.deliveries.enumerated().map { index, delivery in
                    AuthorityPlanDelivery(index: index, tokenIndex: plan.tokens.firstIndex { $0.ref == delivery.tokenRef } ?? 0,
                                          sourceActorIndex: delivery.sourceActorIndex, recipientActorIndex: delivery.recipientActorIndex,
                                          slot: local[delivery.slot]?.slot ?? 0)
                })
        }
    }

    static func extensionSlot(_ action: PWRunnerExtensionAction, plan: ActorPlan, globalSlot: Int) -> CWorkerSlotInput {
        let op = action.intervention
        var operands = CWorkerExtensionOperands()
        let kind: PWAttemptKind
        switch op.operation {
        case "issue":
            kind = .extensionIssue
            let token = plan.token(op.token_ref ?? "")
            operands.tokenIndex = UInt32(plan.tokens.firstIndex { $0.ref == op.token_ref } ?? 0)
            operands.authority = token?.authority == "read_write" ? 1 : 0
            operands.target = token?.target ?? op.target ?? ""
        case "transfer":
            kind = .extensionTransfer
            operands.tokenIndex = UInt32(plan.tokens.firstIndex { $0.ref == op.token_ref } ?? 0)
            operands.deliveryIndex = UInt32(plan.deliveries.firstIndex { $0.ref == op.delivery_ref } ?? 0)
            operands.recipientIndex = UInt32(plan.delivery(op.delivery_ref ?? "")?.recipientActorIndex ?? 0)
        case "consume":
            kind = .extensionConsume
            let delivery = plan.delivery(op.delivery_ref ?? "")
            operands.deliveryIndex = UInt32(plan.deliveries.firstIndex { $0.ref == op.delivery_ref } ?? 0)
            operands.handleIndex = UInt32(plan.handles.firstIndex { $0.ref == op.handle_ref } ?? 0)
            operands.lastUse = delivery?.lastUseSlot == globalSlot
        default:
            kind = .extensionRelease
            operands.handleIndex = UInt32(plan.handles.firstIndex { $0.ref == op.handle_ref } ?? 0)
        }
        return CWorkerSlotInput(stepId: action.step_id, attemptKind: kind, target: "", extensionOperands: operands)
    }
}

// MARK: - Classification

/// One actor's summary from its own record: launch, setup, publication and
/// disposition. The legacy classifier judges an apply actor's output; an
/// unapplied actor's declared setup stands in for application.
func classifyActor(_ record: ActorSessionRecord, applies: Bool) -> ClassifiedRun {
    if let failure = record.launchFailure {
        return classify(workerResult: .failure(failure, record.output), validatorResult: nil, expectedVerdictCount: 0)
    }
    guard let output = record.output else {
        return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1, error: "actor never launched: \(record.setupStatus.rawValue)")
    }
    if !applies && output.actorSetup == 2 {
        // Declared setup replaces the apply prerequisite for the classifier's
        // view; the reply's own fields keep applied unset for this actor.
        var view = output
        view.applied = true
        view.applyRC = 0
        return classify(workerResult: .success(view), validatorResult: nil, expectedVerdictCount: 0)
    }
    let classified = classify(workerResult: .success(output), validatorResult: nil, expectedVerdictCount: 0)
    if classified.rc != 0 || record.setupStatus.usable { return classified }
    return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1, error: "actor setup ended: \(record.setupStatus.rawValue)")
}

// MARK: - Reply assembly

private let unavailableReasons: [UInt32: String] = [1: "token_unavailable", 2: "handle_unavailable", 3: "native_api_unavailable",
    4: "repeated_action", 5: "authority_channel_unavailable", 6: "delivery_unavailable"]
private let custodyNames: [UInt32: String] = [0: "none", 1: "accepted", 2: "rejected", 3: "timeout", 4: "not_published", 5: "clock_fault"]

private func unpublishedResourceStatus(_ step: PWDispositionStep?) -> String {
    guard let boundary = step?.questions["step_boundary_reached"],
          boundary.state == "supported", boundary.answer == "not_reached" else { return "unresolved" }
    return "not_reached"
}

func assembleActorReply(parsed: PWRunnerRunSpec, plan: ActorPlan, translation: ActorTranslation, outcome: ActorScheduleOutcome,
                        queryPlans: [[ValidatorQueryDecision]], validatorResults: [ValidatorClientResult?],
                        collectionStatuses: [String], bundleId: String?) -> PWRunnerRunResult {
    let outputs = outcome.actors.map { $0.output }
    let dispositions = outputs.map { $0.map { resolveDisposition($0, plan: nil) } }
    func stepID(ofGlobalSlot slot: Int) -> String? { plan.slotOfStep.first { $0.value == slot }?.key }
    func slotResult(actor: Int, step: String) -> CWorkerSlotResult? { outputs[actor]?.slots.first { $0.stepId == step } }
    func dispositionStep(actor: Int, step: String) -> PWDispositionStep? { dispositions[actor]?.steps.first { $0.step_id == step } }

    // ---- Aggregate outcome: actor failures in actor order, then validator
    // failures and collection exhaustion in schedule order, then cancellation.
    var runOutcome = ClassifiedRun(outcome: NormalizedOutcome.ok, rc: 0, error: nil)
    for (index, record) in outcome.actors.enumerated() where runOutcome.rc == 0 {
        let classified = classifyActor(record, applies: plan.actors[index].applies)
        if classified.rc != 0 {
            runOutcome = ClassifiedRun(outcome: classified.outcome, rc: classified.rc,
                                       error: "actor \(plan.actors[index].id): " + (classified.error ?? "failed"))
        }
    }

    var phaseResults: [PWRunnerPhaseResult] = []
    var stepResults: [PWRunnerStepResult] = []
    var events: [PWRunnerExtensionEvent] = []
    for phase in plan.phases {
        let actorIndex = phase.actorIndex
        let actor = plan.actors[actorIndex]
        let visitIndex = phase.visit - 1
        let visit = outcome.visits.first { $0.phaseIndex == phase.index }
        let output = outputs[actorIndex]
        let validatorOutput = unwrapValidatorOutput(validatorResults[phase.index])
        let hasQueries = !queryPlans[phase.index].compactMap { $0.probe }.isEmpty
        let setupEstablished = actor.applies ? nil : Optional(outcome.actors[actorIndex].setupStatus == .unappliedDeclared)
        let ordering = output.flatMap { out -> PWRunnerOrdering? in
            guard out.phases.indices.contains(visitIndex) else { return nil }
            return buildPhaseOrdering(out, index: visitIndex, input: translation.phaseInputs[phase.index],
                                      validatorOutput: validatorOutput, hasQueries: hasQueries, setupEstablished: setupEstablished)
        }
        let probes = phase.actions.compactMap { $0.probe }
        var steps = buildStepResults(probePlan: probes, queryPlan: queryPlans[phase.index], workerOutput: output,
                                     validatorOutput: validatorOutput, ordering: ordering, disposition: dispositions[actorIndex],
                                     stepOffset: translation.phaseInputs[phase.index].firstSlot, setupEstablished: setupEstablished)
        for i in steps.indices { steps[i].phase_id = phase.id; steps[i].actor_id = actor.id }
        stepResults += steps
        var spawnFailure: PWRunnerSpawnFailure?
        if case .failure(.spawnFailed(let failure), _) = validatorResults[phase.index] { spawnFailure = failure }
        var result = PWRunnerPhaseResult(phase_id: phase.id, ordinal: phase.index + 1,
            action_ids: phase.actions.map { $0.stepID },
            arrival_observed: visit?.arrivalObserved ?? false,
            completion_observed: visit?.completionObserved ?? false,
            collection_status: collectionStatuses[phase.index], ordering: ordering,
            validator_subprocess: validatorOutput.map { buildValidatorSubprocess($0, phaseId: phase.id, ordinal: phase.index + 1) },
            validator_spawn_failure: spawnFailure)
        result.actor_id = actor.id
        result.actor_visit = phase.visit
        if let visit, visit.activationStored {
            result.visit_timing = PWRunnerVisitTiming(activation_to_arrival_ms: visit.activationToArrivalMs, collection_ms: visit.collectionMs,
                                                      arrival_to_release_ms: visit.arrivalToReleaseMs, release_to_completion_ms: visit.releaseToCompletionMs)
        }
        phaseResults.append(result)
        if runOutcome.rc == 0 {
            let validatorRun = classify(workerResult: .success(output ?? CWorkerOutput(workerPid: 0, readyByteReceived: false, applied: true, applyRC: 0, applyErrno: 0, done: true, slots: [])),
                validatorResult: validatorResults[phase.index],
                expectedVerdictCount: queryPlans[phase.index].compactMap { $0.probe }.count, disposition: dispositions[actorIndex])
            if validatorRun.rc != 0 && validatorRun.outcome.hasPrefix("validator") { runOutcome = validatorRun }
            if runOutcome.rc == 0 && ["budget_exhausted", "clock_unavailable"].contains(collectionStatuses[phase.index]) {
                runOutcome = ClassifiedRun(outcome: NormalizedOutcome.validatorUnavailable, rc: 1,
                    error: "phase collection unavailable: " + collectionStatuses[phase.index])
            }
        }
        // ---- Extension events for this phase's actions.
        for action in phase.actions {
            guard case .extensionAction(let value) = action else { continue }
            let op = value.intervention
            let slot = slotResult(actor: actorIndex, step: value.step_id)
            let published = slot?.completed == true
            let native = published ? slot?.nativeResult : nil
            let reason = published ? unavailableReasons[slot?.unavailableCode ?? 0] : nil
            let publication = published ? slot?.extensionPublication : nil
            var status: String
            if !published { status = "unresolved" }
            else if op.operation == "transfer" { status = PWTransferAck.names[publication?.transferStatus ?? 0] ?? "invalid" }
            else if native != nil { status = "returned" }
            else if reason != nil { status = "unavailable" }
            else { status = "invalid" }
            let token = op.token_ref.flatMap { plan.token($0) }
            var event = PWRunnerExtensionEvent(phase_id: phase.id, step_id: value.step_id, operation: op.operation,
                token_ref: op.token_ref, handle_ref: op.handle_ref, call_boundary_observed: slot?.callBoundary ?? false,
                result_published: published, status: status, native_result: native,
                errno: native != nil ? slot?.nativeErrno : nil, unavailable_reason: reason,
                lifecycle: dispositionStep(actor: actorIndex, step: value.step_id).flatMap(attemptLifecycle))
            event.actor_id = actor.id
            event.family = "file"
            if op.operation == "issue" {
                event.target = token?.target
                event.extension_class = token?.authority == "read_write" ? "com.apple.app-sandbox.read-write" : "com.apple.app-sandbox.read"
                event.flags = 0
                event.native_nonnull = native.map { $0 == 1 }
                event.token_length = publication.map { Int($0.tokenLength) }
            }
            if op.operation == "transfer" || op.operation == "consume" { event.delivery_ref = op.delivery_ref }
            events.append(event)
        }
    }
    if runOutcome.rc == 0, let cancelled = outcome.cancelled {
        runOutcome = ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1, error: "schedule cancelled: " + cancelled)
    }

    // ---- Actors.
    let actors: [PWRunnerActorResult] = plan.actors.map { actor in
        let record = outcome.actors[actor.index]
        let output = outputs[actor.index]
        let hash = actor.policy.flatMap { try? computePolicyHash($0) }
        return PWRunnerActorResult(actor_id: actor.id, index: actor.index, mode: actor.applies ? "apply" : "unapplied",
            policy_format: actor.policy?.format, policy_sha256: hash,
            policy_received_sha256: output?.policyReceivedSha256,
            setup_status: record.setupStatus.rawValue,
            applied: actor.applies ? output?.applied : nil,
            application_count: record.applicationCount,
            launch: record.pid.map { PWRunnerActorLaunch(pid: Int($0), parent_pid: Int(record.parentPid),
                inherited_descriptors: record.authorityRegion == "mapped" ? [0, 3, 4, 5] : [0, 3, 4]) },
            subprocess: output.map { buildWorkerSubprocess($0, disposition: dispositions[actor.index]) },
            compiled_profile: output?.profileCapture,
            visits: actor.visits.map { $0 + 1 })
    }

    // ---- Transfers and resources.
    let transfers: [PWRunnerTransferRecord] = outcome.transfers.compactMap { observation in
        guard plan.deliveries.indices.contains(observation.deliveryIndex) else { return nil }
        let delivery = plan.deliveries[observation.deliveryIndex]
        return PWRunnerTransferRecord(phase_id: plan.phases[delivery.phaseIndex].id, step_id: delivery.stepID,
            source_actor_id: plan.actors[delivery.sourceActorIndex].id, recipient_actor_id: plan.actors[delivery.recipientActorIndex].id,
            token_ref: delivery.tokenRef, delivery_ref: delivery.ref, request_published: observation.requestObserved,
            custody_status: observation.custodyStatus, copy_status: observation.copyStatus, equality: observation.equality,
            recipient_acknowledged: observation.recipientAcknowledged, source_acknowledged: observation.sourceAcknowledged,
            status: PWTransferAck.names[observation.acknowledgement] ?? String(observation.acknowledgement),
            lifecycle: dispositionStep(actor: delivery.sourceActorIndex, step: delivery.stepID).flatMap(attemptLifecycle),
            recipient_wait: observation.recipientWait)
    }
    let tokenRecords: [PWRunnerTokenRecord] = plan.tokens.enumerated().map { index, token in
        let slot = slotResult(actor: token.actorIndex, step: token.stepID)
        let custody = outcome.custody.first { $0.tokenIndex == index }
        let status: String
        if slot?.completed != true { status = unpublishedResourceStatus(dispositionStep(actor: token.actorIndex, step: token.stepID)) }
        else if let code = slot?.unavailableCode, code != 0 { status = "unavailable" }
        else if slot?.nativeResult == 1 { status = custody?.status == "accepted" ? "issued" : "issued_uncustodied" }
        else if slot?.nativeResult == 0 { status = "null" }
        else { status = "invalid" }
        return PWRunnerTokenRecord(token_ref: token.ref, actor_id: plan.actors[token.actorIndex].id, step_id: token.stepID,
            family: token.family, status: status, token_length: slot?.extensionPublication.map { Int($0.tokenLength) },
            last_use_step_id: stepID(ofGlobalSlot: token.lastUseSlot))
    }
    let deliveryRecords: [PWRunnerDeliveryRecord] = plan.deliveries.enumerated().map { index, delivery in
        let observation = outcome.transfers.first { $0.deliveryIndex == index }
        let slot = slotResult(actor: delivery.sourceActorIndex, step: delivery.stepID)
        let status: String
        if let observation { status = PWTransferAck.names[observation.acknowledgement] ?? "invalid" }
        else if slot?.completed == true { status = unavailableReasons[slot?.unavailableCode ?? 0] ?? "unrequested" }
        else { status = unpublishedResourceStatus(dispositionStep(actor: delivery.sourceActorIndex, step: delivery.stepID)) }
        let token = plan.tokens.firstIndex { $0.ref == delivery.tokenRef }
        return PWRunnerDeliveryRecord(delivery_ref: delivery.ref, token_ref: delivery.tokenRef,
            source_actor_id: plan.actors[delivery.sourceActorIndex].id, recipient_actor_id: plan.actors[delivery.recipientActorIndex].id,
            step_id: delivery.stepID, status: status,
            delivered_length: observation?.acknowledgement == PWTransferAck.delivered ? token.flatMap { t in outcome.custody.first { $0.tokenIndex == t }?.length } : nil,
            equality: observation?.equality, last_use_step_id: stepID(ofGlobalSlot: delivery.lastUseSlot))
    }
    let handleRecords: [PWRunnerHandleRecord] = plan.handles.map { handle in
        let slot = slotResult(actor: handle.actorIndex, step: handle.stepID)
        let status: String
        if slot?.completed != true { status = unpublishedResourceStatus(dispositionStep(actor: handle.actorIndex, step: handle.stepID)) }
        else if let code = slot?.unavailableCode, code != 0 { status = "unavailable" }
        else if slot?.nativeResult == -1 { status = "consume_failed" }
        else if slot?.nativeResult != nil { status = "produced" }
        else { status = "invalid" }
        let raw = status == "produced" ? slot?.nativeResult : nil
        let equal = plan.handles.filter { other in
            other.ref != handle.ref && other.actorIndex == handle.actorIndex && raw != nil
                && slotResult(actor: other.actorIndex, step: other.stepID)?.nativeResult == raw
        }.map { $0.ref }
        let releaseSlot = handle.releaseStepID.flatMap { slotResult(actor: handle.actorIndex, step: $0) }
        return PWRunnerHandleRecord(handle_ref: handle.ref, delivery_ref: handle.deliveryRef, actor_id: plan.actors[handle.actorIndex].id,
            step_id: handle.stepID, status: status, native_handle: raw, raw_equal_handles: equal,
            release_step_id: handle.releaseStepID, release_attempted: releaseSlot?.callBoundary == true)
    }

    var reply = PWRunnerRunResult(specimen_id: parsed.specimen_id, run_kind: parsed.run_kind,
        rc: runOutcome.rc, normalized_outcome: runOutcome.outcome, error: runOutcome.error,
        pid: Int(getpid()), bundle_id: bundleId, policy_format: nil, policy_sha256: nil,
        sandboxed_after_apply: nil, steps: stepResults, runner_subprocess: nil, phases: phaseResults,
        extensions: nil, extension_events: events, test_overrides: parsed._test_overrides)
    reply.execution_form = "actors"
    reply.actors = actors
    reply.transfers = transfers
    reply.resources = PWRunnerResourceTables(tokens: tokenRecords, deliveries: deliveryRecords, handles: handleRecords)
    reply.schedule = PWRunnerScheduleRecord(setup_wait: outcome.setupWait, execution_wait: outcome.executionWait,
                                            lifetime_budget_ms: PWActorLimits.lifetimeMs, collection_budget_ms: PWActorLimits.collectionMs,
                                            cancelled: outcome.cancelled)
    return reply
}

private func unwrapValidatorOutput(_ result: ValidatorClientResult?) -> ValidatorOutput? {
    guard let result else { return nil }
    switch result {
    case .success(let out): return out
    case .failure(_, let partial): return partial
    }
}

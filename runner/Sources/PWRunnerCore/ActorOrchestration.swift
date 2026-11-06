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
        validatorProcessCalls: @escaping (Int) -> ChildProcessCalls,
        equipmentBundleURL: URL = Bundle.main.bundleURL
    ) -> PWRunnerRunResult {
        let assignmentsConsistent = actorPlanAssignmentsConsistent(plan)
        let equipmentRequests = assignmentsConsistent ? plan.actors.map {
            ActorEquipmentRequest(actorID: $0.id, index: $0.index, requested: $0.equipment, requiredEntitlements: $0.requiredEntitlements)
        } : (parsed.actors ?? []).enumerated().map { index, actor in
            // Refusal metadata comes from the admitted request, never the
            // invalid indices. This path cannot proceed to translation.
            ActorEquipmentRequest(actorID: actor.actor_id, index: index, requested: actor.equipment,
                requiredEntitlements: actor.required_entitlements)
        }
        let equipment = ActorEquipmentPreparation.bind(bundleURL: equipmentBundleURL, actors: equipmentRequests,
            overrides: parsed._test_overrides?.actor_equipment_executable_paths ?? [:])
        guard assignmentsConsistent else {
            return actorPreparationRefusal(parsed: parsed, equipment: equipment, bundleId: bundleId,
                failure: PWRunnerPreparationFailure(stage: "resolved_plan", code: "inconsistent_assignment"))
        }
        guard let paths = equipment.executablePaths else {
            return actorPreparationRefusal(parsed: parsed, equipment: equipment, bundleId: bundleId,
                failure: PWRunnerPreparationFailure(stage: "equipment", code: "equipment_binding_refused",
                    actor_id: equipment.failure?.actor_id, binding_ref: equipment.failure?.binding_ref, reason: equipment.failure?.reason))
        }
        let translation: ActorTranslation
        do { translation = try ActorTranslation(plan: plan, parsed: parsed, workerExecutablePaths: paths) }
        catch {
            return actorPreparationRefusal(parsed: parsed, equipment: equipment, bundleId: bundleId,
                failure: PWRunnerPreparationFailure(stage: "resolved_plan", code: "inconsistent_assignment"))
        }
        var input = ActorScheduleInput(actors: translation.inputs, applies: plan.actors.map { $0.applies },
                                       schedule: translation.schedule)
        input.authority = translation.authority
        let inspectionDeadline = MonotonicDeadline.now().map { $0 + UInt64(PWActorLimits.lifetimeMs) * 1_000_000 }
        input.didSetUp = { index, pid in
            equipment.inspect(actorIndex: index, pid: pid, ownershipConfirmed: true, deadlineNs: inspectionDeadline)
        }

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

        var reply = assembleActorReply(parsed: parsed, plan: plan, translation: translation, outcome: outcome,
            queryPlans: queryPlans, validatorResults: validatorResults,
            collectionStatuses: collectionStatuses, bundleId: bundleId)
        for index in outcome.actors.indices {
            if let failure = outcome.actors[index].equipmentFailure, equipment.actors[index].execution.status == "matched" {
                equipment.actors[index].execution.status = "inspection_failed"
                equipment.actors[index].execution.reason = failure
                equipment.actors[index].execution.eligible = false
            }
            if equipment.actors[index].execution.status == "unobserved", outcome.actors[index].pid != nil {
                equipment.actors[index].execution.reason = outcome.actors[index].equipmentFailure ?? "setup_unavailable"
                if outcome.actors[index].equipmentFailure != nil {
                    equipment.actors[index].execution.pid = outcome.actors[index].pid.map(Int.init)
                }
            }
            reply.actors?[index].equipment = equipment.actors[index]
            reply.actors?[index].application = actorApplicationAssessment(mode: plan.actors[index].applies ? "apply" : "unapplied",
                launched: outcome.actors[index].pid != nil, applied: outcome.actors[index].output?.applied == true,
                evidence: outcome.actors[index].output?.workerEvidence, authority: outcome.actors[index].output?.authoritySetup)
        }
        reply.equipment_inventory = equipment.inventory
        reply.equipment_bindings = equipment.bindings
        reply.equipment_entitlements = equipment.entitlements
        reply.authority_setup = outcome.authoritySetup
        reply.authority_setup?.bind(actorIDs: plan.actors.map { $0.id }, tokenRefs: plan.tokens.map { $0.ref })
        return reply
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

    init(plan: ActorPlan, parsed: PWRunnerRunSpec, workerExecutablePaths: [String]) throws {
        func require(_ condition: Bool) throws {
            if !condition { throw PWRunnerPreparationFailureError.inconsistentAssignment }
        }
        try require(actorPlanAssignmentsConsistent(plan))
        let actions = plan.phases.flatMap { $0.actions }
        try require(workerExecutablePaths.count == plan.actors.count && actions.count == plan.actionCount
            && plan.localSlotOfGlobal.count == actions.count && plan.inboundCounts.count == plan.actors.count
            && plan.outboundCounts.count == plan.actors.count)
        var local: [Int: (actor: Int, slot: Int)] = [:]
        for actor in plan.actors {
            try require(plan.actors.indices.contains(actor.index))
            for (position, global) in actor.slots.enumerated() {
                try require(actions.indices.contains(global) && actions[global].globalSlot == global
                    && actions[global].actorLocalSlot == position && plan.localSlotOfGlobal[global] == position
                    && local[global] == nil)
                local[global] = (actor.index, position)
            }
        }
        try require(local.count == actions.count)
        self.local = local
        var inputs: [CWorkerInput] = []
        for actor in plan.actors {
            var slots: [CWorkerSlotInput] = []
            for global in actor.slots {
                let action = actions[global]
                switch action.body {
                case .probe(let probe, let kind):
                    var slot = makeWorkerSlot(stepID: probe.step_id, attempt: probe.attempt)
                    slot.attemptKind = kind
                    slots.append(slot)
                case .authority(let operation):
                    slots.append(try Self.extensionSlot(operation, stepID: action.stepID, plan: plan))
                }
            }
            var phases: [CWorkerPhaseInput] = []
            for phaseIndex in actor.visits {
                try require(plan.phases.indices.contains(phaseIndex))
                let phase = plan.phases[phaseIndex]
                try require(phase.actorIndex == actor.index && phase.visit == phases.count + 1)
                let first = phases.last?.endSlot ?? 0
                phases.append(CWorkerPhaseInput(firstSlot: first, endSlot: first + phase.actions.count, globalPhase: phaseIndex + 1))
            }
            try require(phases.last?.endSlot == slots.count)
            let policy = actor.policy
            var input = CWorkerInput(workerExecutablePath: workerExecutablePaths[actor.index],
                policy: policy?.sbpl_source ?? "", params: policy.map(workerParamsFromPolicy) ?? [], slots: slots, phases: phases,
                sentinelTimeoutMs: PWActorLimits.executionMs,
                postApplyHangMs: parsed._test_overrides?.worker_post_apply_hang_ms,
                postApplyKillSignal: parsed._test_overrides?.worker_post_apply_kill_signal,
                preReadyHangMs: parsed._test_overrides?.worker_pre_ready_hang_ms,
                killBeforePublishSlot: parsed._test_overrides?.worker_kill_before_publish_slot,
                captureCompiledProfile: policy?.capture_compiled_profile == true, captureNonce: policy?.capture_nonce)
            input.proceedWaitMs = PWActorLimits.releaseWaitMs
            input.authorityRequired = plan.authorityRequired
            inputs.append(input)
        }
        var phaseInputs: [CWorkerPhaseInput] = []
        var schedule: [ActorScheduleEntry] = []
        for phase in plan.phases {
            try require(inputs.indices.contains(phase.actorIndex) && inputs[phase.actorIndex].phases.indices.contains(phase.visit - 1))
            phaseInputs.append(inputs[phase.actorIndex].phases[phase.visit - 1])
            var entry = ActorScheduleEntry(phaseIndex: phase.index, actorIndex: phase.actorIndex, visit: phase.visit - 1)
            if let source = phase.afterTermination {
                try require(plan.actors.indices.contains(source))
                guard let final = plan.actors[source].visits.last, final < phase.index else {
                    throw PWRunnerPreparationFailureError.inconsistentAssignment
                }
                entry.terminationDependency = ActorTerminationDependency(sourceActorIndex: source, sourceFinalPhaseIndex: final)
            }
            schedule.append(entry)
        }
        self.phaseInputs = phaseInputs; self.inputs = inputs; self.schedule = schedule
        if !plan.authorityRequired { authority = nil; return }
        for token in plan.tokens {
            try require(plan.actors.indices.contains(token.actorIndex) && local[token.slot]?.actor == token.actorIndex
                && local[token.lastUseSlot]?.actor == token.actorIndex && token.outboundPosition >= 0
                && token.outboundPosition < plan.outboundCounts[token.actorIndex])
        }
        for delivery in plan.deliveries {
            try require(plan.tokens.indices.contains(delivery.tokenIndex.rawValue)
                && plan.actors.indices.contains(delivery.recipientActorIndex)
                && local[delivery.slot]?.actor == delivery.sourceActorIndex && delivery.inboundPosition >= 0
                && delivery.inboundPosition < plan.inboundCounts[delivery.recipientActorIndex])
        }
        authority = AuthorityPlan(
            tokens: plan.tokens.enumerated().map { index, token in
                AuthorityPlanToken(index: index, actorIndex: token.actorIndex, slot: plan.localSlotOfGlobal[token.slot],
                    lastUseSlot: plan.localSlotOfGlobal[token.lastUseSlot], outboundPosition: token.outboundPosition)
            }, deliveries: plan.deliveries.enumerated().map { index, delivery in
                AuthorityPlanDelivery(index: index, tokenIndex: delivery.tokenIndex.rawValue,
                    sourceActorIndex: delivery.sourceActorIndex, recipientActorIndex: delivery.recipientActorIndex,
                    slot: plan.localSlotOfGlobal[delivery.slot], inboundPosition: delivery.inboundPosition)
            }, inboundCounts: plan.inboundCounts, outboundCounts: plan.outboundCounts)
    }

    private static func extensionSlot(_ operation: ResolvedExtensionOperation, stepID: String, plan: ActorPlan) throws -> CWorkerSlotInput {
        var operands = CWorkerExtensionOperands()
        let kind: PWAttemptKind
        switch operation {
        case .issue(let index):
            guard plan.tokens.indices.contains(index.rawValue) else { throw PWRunnerPreparationFailureError.inconsistentAssignment }
            let token = plan.tokens[index.rawValue]
            kind = .extensionIssue; operands.tokenIndex = UInt32(index.rawValue)
            operands.authority = token.authority == "read_write" ? 1 : 0; operands.target = token.target
        case .transfer(let token, let delivery, let recipient):
            guard plan.tokens.indices.contains(token.rawValue), plan.deliveries.indices.contains(delivery.rawValue),
                  plan.actors.indices.contains(recipient.rawValue), plan.deliveries[delivery.rawValue].tokenIndex == token,
                  plan.deliveries[delivery.rawValue].recipientActorIndex == recipient.rawValue else {
                throw PWRunnerPreparationFailureError.inconsistentAssignment
            }
            kind = .extensionTransfer; operands.tokenIndex = UInt32(token.rawValue)
            operands.deliveryIndex = UInt32(delivery.rawValue); operands.recipientIndex = UInt32(recipient.rawValue)
        case .consume(let delivery, let handle, let lastUse):
            guard plan.deliveries.indices.contains(delivery.rawValue), plan.handles.indices.contains(handle.rawValue),
                  plan.handles[handle.rawValue].deliveryIndex == delivery else { throw PWRunnerPreparationFailureError.inconsistentAssignment }
            kind = .extensionConsume; operands.deliveryIndex = UInt32(delivery.rawValue)
            operands.handleIndex = UInt32(handle.rawValue); operands.lastUse = lastUse
        case .release(let handle):
            guard plan.handles.indices.contains(handle.rawValue) else { throw PWRunnerPreparationFailureError.inconsistentAssignment }
            kind = .extensionRelease; operands.handleIndex = UInt32(handle.rawValue)
        }
        return CWorkerSlotInput(stepId: stepID, attemptKind: kind, target: "", extensionOperands: operands)
    }
}

enum PWRunnerPreparationFailureError: Error { case inconsistentAssignment }

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
    let actionNames = plan.phases.flatMap { $0.actions.map { $0.stepID } }
    func stepID(ofGlobalSlot slot: Int) -> String? { actionNames.indices.contains(slot) ? actionNames[slot] : nil }
    func slotResult(actor: Int, step: String) -> CWorkerSlotResult? { outputs[actor]?.slots.first { $0.stepId == step } }
    func dispositionStep(actor: Int, step: String) -> PWDispositionStep? { dispositions[actor]?.steps.first { $0.step_id == step } }

    // ---- Aggregate outcome: actor failures in actor order, then validator
    // failures and collection exhaustion in schedule order, then cancellation.
    var runOutcome = ClassifiedRun(outcome: NormalizedOutcome.finished, rc: 0, error: nil)
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
        result.activation_observation = visit?.activationObservation
        if let visit, visit.activationStored {
            result.visit_timing = PWRunnerVisitTiming(activation_to_arrival_ms: visit.activationToArrivalMs, collection_ms: visit.collectionMs,
                                                      arrival_to_release_ms: visit.arrivalToReleaseMs, release_to_completion_ms: visit.releaseToCompletionMs)
        }
        if let gate = visit?.terminationGate {
            result.termination_gate = PWRunnerTerminationGate(source_actor_id: plan.actors[gate.sourceActorIndex].id,
                source_final_phase_id: plan.phases[gate.sourceFinalPhaseIndex].id, outcome: gate.outcome,
                wait: gate.wait, observation: gate.observation.map { PWOwnedReapReference(capture_ordinal: $0.capture_ordinal) },
                activation_eligible: gate.activationEligible, capture_ordinal: gate.captureOrdinal)
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
            guard case .authority(let operation) = action.body else { continue }
            let name: String
            var token: ActorPlanToken?
            var deliveryRef: String?
            var handleRef: String?
            switch operation {
            case .issue(let index): name = "issue"; token = plan.tokens[index.rawValue]
            case .transfer(let index, let delivery, _):
                name = "transfer"; token = plan.tokens[index.rawValue]; deliveryRef = plan.deliveries[delivery.rawValue].ref
            case .consume(let delivery, let handle, _):
                name = "consume"; deliveryRef = plan.deliveries[delivery.rawValue].ref; handleRef = plan.handles[handle.rawValue].ref
            case .release(let handle): name = "release"; handleRef = plan.handles[handle.rawValue].ref
            }
            let slot = slotResult(actor: actorIndex, step: action.stepID)
            let published = slot?.completed == true
            let native = published ? slot?.nativeResult : nil
            let reason = published ? unavailableReasons[slot?.unavailableCode ?? 0] : nil
            let publication = published ? slot?.extensionPublication : nil
            var status: String
            if !published { status = "unresolved" }
            else if name == "transfer" { status = PWTransferAck.names[publication?.transferStatus ?? 0] ?? "invalid" }
            else if native != nil { status = "returned" }
            else if reason != nil { status = "unavailable" }
            else { status = "invalid" }
            var event = PWRunnerExtensionEvent(phase_id: phase.id, step_id: action.stepID, operation: name,
                token_ref: token?.ref, handle_ref: handleRef, call_boundary_observed: slot?.callBoundary ?? false,
                result_published: published, status: status, native_result: native,
                errno: native != nil ? slot?.nativeErrno : nil, unavailable_reason: reason,
                lifecycle: dispositionStep(actor: actorIndex, step: action.stepID).flatMap(attemptLifecycle))
            event.actor_id = actor.id
            event.family = "file"
            if name == "issue" {
                event.target = token?.target
                event.extension_class = token?.authority == "read_write" ? "com.apple.app-sandbox.read-write" : "com.apple.app-sandbox.read"
                event.flags = 0
                event.native_nonnull = native.map { $0 == 1 }
                event.token_length = publication.map { Int($0.tokenLength) }
            }
            if name == "transfer" || name == "consume" { event.delivery_ref = deliveryRef }
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
            visits: actor.visits.map { $0 + 1 },
            application: actorApplicationAssessment(mode: actor.applies ? "apply" : "unapplied", launched: record.pid != nil,
                applied: output?.applied == true, evidence: output?.workerEvidence, authority: output?.authoritySetup),
            owned_reap: output?.ownedReap)
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
        let token = delivery.tokenIndex.rawValue
        return PWRunnerDeliveryRecord(delivery_ref: delivery.ref, token_ref: delivery.tokenRef,
            source_actor_id: plan.actors[delivery.sourceActorIndex].id, recipient_actor_id: plan.actors[delivery.recipientActorIndex].id,
            step_id: delivery.stepID, status: status,
            delivered_length: observation?.acknowledgement == PWTransferAck.delivered ? outcome.custody.first { $0.tokenIndex == token }?.length : nil,
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
        extension_events: events, test_overrides: parsed._test_overrides)
    reply.execution_form = "actors"
    reply.actors = actors
    reply.authority_setup = outcome.authoritySetup
    reply.authority_setup?.bind(actorIDs: plan.actors.map { $0.id }, tokenRefs: plan.tokens.map { $0.ref })
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

private func actorPreparationRefusal(parsed: PWRunnerRunSpec, equipment: ActorEquipmentPreparation,
                                     bundleId: String?, failure: PWRunnerPreparationFailure) -> PWRunnerRunResult {
    var reply = PWRunnerRunResult(specimen_id: parsed.specimen_id, run_kind: parsed.run_kind,
        rc: 1, normalized_outcome: NormalizedOutcome.runnerFailed, error: "actor preparation refused: " + failure.code,
        pid: Int(getpid()), bundle_id: bundleId, policy_format: nil, steps: [], extension_events: [], test_overrides: parsed._test_overrides)
    reply.execution_form = "actors"
    reply.preparation_failure = failure
    // The execution assignments may be exactly what failed. Project only
    // identity/policy metadata from the already-admitted request for this
    // before-launch account; do not normalize or reconstruct an execution plan.
    let actors = parsed.actors ?? []
    let phases = parsed.phases ?? []
    reply.actors = actors.enumerated().map { index, actor in
        PWRunnerActorResult(actor_id: actor.actor_id, index: index, mode: actor.applies ? "apply" : "unapplied",
            policy_format: actor.sandbox.policy?.format, policy_sha256: actor.sandbox.policy.flatMap { try? computePolicyHash($0) },
            setup_status: "launch_refused", application_count: 0,
            visits: phases.enumerated().compactMap { $0.element.actor_id == actor.actor_id ? $0.offset + 1 : nil },
            equipment: equipment.actors.indices.contains(index) ? equipment.actors[index] : nil,
            application: actorApplicationAssessment(mode: actor.applies ? "apply" : "unapplied", launched: false,
                applied: false, evidence: nil, authority: nil))
    }
    reply.phases = phases.enumerated().map { index, phase in
        var row = PWRunnerPhaseResult(phase_id: phase.phase_id, ordinal: index + 1,
            action_ids: phase.actions.map { $0.stepID }, arrival_observed: false, completion_observed: false, collection_status: "not_reached")
        row.actor_id = phase.actor_id
        row.actor_visit = phases.prefix(index + 1).filter { $0.actor_id == phase.actor_id }.count
        return row
    }
    reply.transfers = []
    reply.resources = PWRunnerResourceTables(tokens: [], deliveries: [], handles: [])
    reply.schedule = PWRunnerScheduleRecord(lifetime_budget_ms: PWActorLimits.lifetimeMs,
        collection_budget_ms: PWActorLimits.collectionMs, cancelled: "preparation_refused")
    reply.equipment_inventory = equipment.inventory; reply.equipment_bindings = equipment.bindings
    reply.equipment_entitlements = equipment.entitlements
    let authorityRequired = phases.contains { phase in
        phase.actions.contains { if case .extensionAction = $0 { return true }; return false }
    }
    reply.authority_setup = PWRunnerAuthoritySetup(host: PWRunnerAuthorityHost(run: PWRunnerAuthorityScope(disposition: "not_attempted")),
        workers: actors.enumerated().map { PWRunnerAuthorityScope(actor_id: $0.element.actor_id,
            actor_index: $0.offset, required: authorityRequired, publication: "not_observed") })
    return reply
}

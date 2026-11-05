import Darwin
import Foundation

// The actor form's normalized plan: typed single-assignment reference tables
// built from the whole request before any process work. Public admission,
// direct XPC admission and the scheduler use the same tables. Every refusal
// carries a bounded field path; a runtime failure of a producer never makes an
// admitted request malformed.

struct ActorPlanActor {
    let id: String
    let index: Int
    let applies: Bool
    let policy: PWRunnerPolicySpec?
    /// Issues, sends, receives, consumes or releases extensions: such an actor
    /// cannot exec in this delivery.
    var participates = false
    /// Global slot indexes of this actor's actions, in schedule order.
    var slots: [Int] = []
    /// Global phase indexes this actor is activated in, in schedule order.
    var visits: [Int] = []
}

struct ActorPlanPhase {
    let id: String
    let index: Int
    let actorIndex: Int
    /// 1-based ordinal among this actor's activations.
    let visit: Int
    let firstSlot: Int
    let endSlot: Int
    let actions: [PWRunnerPhaseAction]
}

struct ActorPlanToken {
    let ref: String
    let actorIndex: Int
    let stepID: String
    let slot: Int
    let phaseIndex: Int
    let family: String
    let target: String
    let authority: String
    var deliveries: [String] = []
    /// The last step that reads the token: its final transfer, or the issue itself.
    var lastUseSlot: Int
}

struct ActorPlanDelivery {
    let ref: String
    let tokenRef: String
    let sourceActorIndex: Int
    let recipientActorIndex: Int
    let stepID: String
    let slot: Int
    let phaseIndex: Int
    var handles: [String] = []
    /// The last step that reads the delivered bytes: its final consume, or the transfer.
    var lastUseSlot: Int
}

struct ActorPlanHandle {
    let ref: String
    let deliveryRef: String
    let actorIndex: Int
    let stepID: String
    let slot: Int
    let phaseIndex: Int
    var releaseStepID: String? = nil
    var releaseSlot: Int? = nil
}

struct ActorPlan {
    var actors: [ActorPlanActor]
    var phases: [ActorPlanPhase]
    var tokens: [ActorPlanToken]
    var deliveries: [ActorPlanDelivery]
    var handles: [ActorPlanHandle]
    /// Global slot index for every step, ordinary or extension.
    var slotOfStep: [String: Int]
    var issueCount: Int { tokens.count }
    var transferCount: Int { deliveries.count }
    var consumeCount: Int { handles.count }
    var releaseCount: Int { handles.filter { $0.releaseSlot != nil }.count }
    var actionCount: Int { slotOfStep.count }

    func token(_ ref: String) -> ActorPlanToken? { tokens.first { $0.ref == ref } }
    func delivery(_ ref: String) -> ActorPlanDelivery? { deliveries.first { $0.ref == ref } }
    func handle(_ ref: String) -> ActorPlanHandle? { handles.first { $0.ref == ref } }
    func actor(named id: String) -> ActorPlanActor? { actors.first { $0.id == id } }
}

enum ActorPlanResult {
    case success(ActorPlan)
    case failure(PWRunnerRequestFailure)
}

/// Normalize the actor form. Order: actor objects, phase identities and
/// owners, action structure and ordinary meaning, reference lifecycle in
/// global order, then the per-actor exec exclusion.
func normalizeActorPlan(_ spec: PWRunnerRunSpec) -> ActorPlanResult {
    func fail(_ code: String, _ path: [String]) -> ActorPlanResult { .failure(PWRunnerRequestFailure(code: code, path: path)) }
    guard let submittedActors = spec.actors else { return fail("missing_field", ["actors"]) }
    if submittedActors.isEmpty { return fail("empty_actors", ["actors"]) }
    var actors: [ActorPlanActor] = []
    for (i, actor) in submittedActors.enumerated() {
        let path = ["actors", String(i)]
        if actor.actor_id.isEmpty { return fail("empty_actor_id", path + ["actor_id"]) }
        if actors.contains(where: { $0.id == actor.actor_id }) { return fail("duplicate_actor_id", path + ["actor_id"]) }
        switch actor.sandbox.mode {
        case PWRunnerActorSandbox.modeApply:
            guard let policy = actor.sandbox.policy else { return fail("missing_field", path + ["sandbox", "policy"]) }
            if let failure = policyMeaningFailure(policy, path: path + ["sandbox", "policy"]) { return .failure(failure) }
        case PWRunnerActorSandbox.modeUnapplied:
            if actor.sandbox.policy != nil { return fail("inapplicable_field", path + ["sandbox", "policy"]) }
        default:
            return fail("unsupported_sandbox_mode", path + ["sandbox", "mode"])
        }
        actors.append(ActorPlanActor(id: actor.actor_id, index: i, applies: actor.applies, policy: actor.sandbox.policy))
    }

    guard let submittedPhases = spec.phases else { return fail("actors_require_phases", ["phases"]) }
    if submittedPhases.isEmpty { return fail("empty_phases", ["phases"]) }
    var phases: [ActorPlanPhase] = []
    var phaseIDs = Set<String>()
    var slot = 0
    for (pi, phase) in submittedPhases.enumerated() {
        let path = ["phases", String(pi)]
        if phase.phase_id.isEmpty { return fail("empty_phase_id", path + ["phase_id"]) }
        if !phaseIDs.insert(phase.phase_id).inserted { return fail("duplicate_phase_id", path + ["phase_id"]) }
        guard let actorID = phase.actor_id else { return fail("missing_field", path + ["actor_id"]) }
        guard let actor = actors.firstIndex(where: { $0.id == actorID }) else { return fail("unknown_actor", path + ["actor_id"]) }
        actors[actor].visits.append(pi)
        let first = slot
        slot += phase.actions.count
        phases.append(ActorPlanPhase(id: phase.phase_id, index: pi, actorIndex: actor, visit: actors[actor].visits.count,
                                     firstSlot: first, endSlot: slot, actions: phase.actions))
    }
    // A declared actor is a fresh process that is visited; one that owns no
    // phase would be launched for nothing and its worker has no partition.
    if let idle = actors.firstIndex(where: { $0.visits.isEmpty }) {
        return fail("actor_without_phases", ["actors", String(idle)])
    }

    // Action structure and ordinary meaning, in global order.
    var slotOfStep: [String: Int] = [:]
    var probes: [PWRunnerProbeStep] = []
    var probePaths: [[String]] = []
    for phase in phases {
        for (ai, action) in phase.actions.enumerated() {
            let path = ["phases", String(phase.index), "actions", String(ai)]
            if action.stepID.isEmpty { return fail("empty_step_id", path + ["step_id"]) }
            if slotOfStep[action.stepID] != nil { return fail("duplicate_step_id", path + ["step_id"]) }
            slotOfStep[action.stepID] = phase.firstSlot + ai
            actors[phase.actorIndex].slots.append(phase.firstSlot + ai)
            switch action {
            case .probe(let step):
                probes.append(step); probePaths.append(path)
            case .extensionAction(let value):
                let op = value.intervention
                guard let operands = PWRunnerExtensionOperation.actorOperands[op.operation] else {
                    return fail("unsupported_extension_action", path + ["extension", "operation"])
                }
                for key in PWRunnerExtensionOperation.CodingKeys.allCases where key != .operation {
                    let present = op.operand(key) != nil
                    if operands.contains(key) && !present { return fail("missing_field", path + ["extension", key.rawValue]) }
                    if !operands.contains(key) && present { return fail("inapplicable_field", path + ["extension", key.rawValue]) }
                }
                for key in operands where key == .token_ref || key == .delivery_ref || key == .handle_ref {
                    if op.operand(key)?.isEmpty == true { return fail("empty_reference", path + ["extension", key.rawValue]) }
                }
                if op.operation == "issue" {
                    if op.family != "file" { return fail("unsupported_extension_family", path + ["extension", "family"]) }
                    if !["read", "read_write"].contains(op.authority ?? "") {
                        return fail("unsupported_extension_authority", path + ["extension", "authority"])
                    }
                    if op.target?.hasPrefix("/") != true { return fail("relative_extension_target", path + ["extension", "target"]) }
                }
                if op.operation == "transfer", actors.contains(where: { $0.id == op.recipient }) == false {
                    return fail("unknown_actor", path + ["extension", "recipient"])
                }
            }
        }
    }
    if var failure = sandboxCheckFailure(probes) {
        if let path = failure.path, path.count >= 2, let index = Int(path[1]) {
            failure.path = probePaths[index] + path.dropFirst(2)
        }
        return .failure(failure)
    }
    for (index, step) in probes.enumerated() {
        let path = probePaths[index]
        guard let kind = mapAttemptKindOrNil(step.attempt) else { return fail("unsupported_attempt", path + ["attempt"]) }
        if kind != .execSpawn && step.attempt.args != nil { return fail("inapplicable_field", path + ["attempt", "args"]) }
        if kind == .execSpawn && !step.attempt.target.hasPrefix("/") { return fail("relative_exec_target", path + ["attempt", "target"]) }
    }

    // Reference lifecycle: every use follows its syntactic producer, each
    // reference is assigned once across tokens, deliveries and handles, and
    // ownership is the producing/receiving/consuming actor's.
    var tokens: [ActorPlanToken] = []
    var deliveries: [ActorPlanDelivery] = []
    var handles: [ActorPlanHandle] = []
    var assigned = Set<String>()
    for phase in phases {
        for (ai, action) in phase.actions.enumerated() {
            guard case .extensionAction(let value) = action else { continue }
            let op = value.intervention
            let path = ["phases", String(phase.index), "actions", String(ai), "extension"]
            let slot = phase.firstSlot + ai
            actors[phase.actorIndex].participates = true
            switch op.operation {
            case "issue":
                let ref = op.token_ref!
                if !assigned.insert(ref).inserted { return fail("duplicate_reference", path + ["token_ref"]) }
                tokens.append(ActorPlanToken(ref: ref, actorIndex: phase.actorIndex, stepID: value.step_id, slot: slot,
                    phaseIndex: phase.index, family: op.family!, target: op.target!, authority: op.authority!, lastUseSlot: slot))
            case "transfer":
                guard let tokenIndex = tokens.firstIndex(where: { $0.ref == op.token_ref! }) else {
                    return fail("unknown_token_reference", path + ["token_ref"])
                }
                if tokens[tokenIndex].actorIndex != phase.actorIndex { return fail("wrong_owner_reference", path + ["token_ref"]) }
                let ref = op.delivery_ref!
                if !assigned.insert(ref).inserted { return fail("duplicate_reference", path + ["delivery_ref"]) }
                let recipient = actors.firstIndex { $0.id == op.recipient! }!
                actors[recipient].participates = true
                tokens[tokenIndex].deliveries.append(ref)
                tokens[tokenIndex].lastUseSlot = slot
                deliveries.append(ActorPlanDelivery(ref: ref, tokenRef: op.token_ref!, sourceActorIndex: phase.actorIndex,
                    recipientActorIndex: recipient, stepID: value.step_id, slot: slot, phaseIndex: phase.index, lastUseSlot: slot))
            case "consume":
                guard let deliveryIndex = deliveries.firstIndex(where: { $0.ref == op.delivery_ref! }) else {
                    return fail("unknown_delivery_reference", path + ["delivery_ref"])
                }
                if deliveries[deliveryIndex].recipientActorIndex != phase.actorIndex { return fail("wrong_owner_reference", path + ["delivery_ref"]) }
                let ref = op.handle_ref!
                if !assigned.insert(ref).inserted { return fail("duplicate_reference", path + ["handle_ref"]) }
                deliveries[deliveryIndex].handles.append(ref)
                deliveries[deliveryIndex].lastUseSlot = slot
                handles.append(ActorPlanHandle(ref: ref, deliveryRef: op.delivery_ref!, actorIndex: phase.actorIndex,
                    stepID: value.step_id, slot: slot, phaseIndex: phase.index))
            case "release":
                guard let handleIndex = handles.firstIndex(where: { $0.ref == op.handle_ref! }) else {
                    return fail("unknown_handle_reference", path + ["handle_ref"])
                }
                if handles[handleIndex].actorIndex != phase.actorIndex { return fail("wrong_owner_reference", path + ["handle_ref"]) }
                if handles[handleIndex].releaseSlot != nil { return fail("repeated_release", path) }
                handles[handleIndex].releaseStepID = value.step_id
                handles[handleIndex].releaseSlot = slot
            default:
                return fail("unsupported_extension_action", path + ["operation"])
            }
        }
    }

    // Per-actor exec exclusion: participation anywhere in the plan excludes
    // exec anywhere in that actor's plan.
    for phase in phases where actors[phase.actorIndex].participates {
        for (ai, action) in phase.actions.enumerated() {
            if case .probe(let step) = action, step.attempt.kind == PWRunnerWire.attemptKindExec {
                return fail("extension_exec_unsupported", ["phases", String(phase.index), "actions", String(ai), "attempt"])
            }
        }
    }
    return .success(ActorPlan(actors: actors, phases: phases, tokens: tokens, deliveries: deliveries,
                              handles: handles, slotOfStep: slotOfStep))
}

/// Capacity refusals for the actor form, after the shared string admission
/// and before meaning. Counts first, then per-actor policy bounds, then the
/// worker's per-slot string bounds and the host-only query bounds.
func actorAdmissionFailure(_ parsed: PWRunnerRunSpec) -> PWRunnerAdmissionFailure? {
    let actors = parsed.actors ?? []
    let phases = parsed.phases ?? []
    func count(_ field: String, _ actual: Int, _ maximum: Int) -> PWRunnerAdmissionFailure? {
        actual > maximum ? PWRunnerAdmissionFailure(field: field, actual: actual, maximum: maximum, unit: "items") : nil
    }
    if let r = count("actors", actors.count, PWActorLimits.actors) { return r }
    if let r = count("phases", phases.count, PWActorLimits.phases) { return r }
    let actions = phases.flatMap { $0.actions }
    if let r = count("phases.actions", actions.count, PWActorLimits.actions) { return r }
    for (index, phase) in phases.enumerated() {
        if var failure = AdmissionStringRule(field: "phase_id", maximum: requestLabelMaxBytes, requiresCString: true).failure(phase.phase_id) {
            failure.index = index
            return failure
        }
    }
    var operations: [String: Int] = [:]
    for action in actions {
        if case .extensionAction(let value) = action { operations[value.intervention.operation, default: 0] += 1 }
    }
    for (operation, maximum) in [("issue", PWActorLimits.issues), ("transfer", PWActorLimits.deliveries),
                                 ("consume", PWActorLimits.handles), ("release", PWActorLimits.releases)] {
        if let r = count("extension." + operation, operations[operation] ?? 0, maximum) { return r }
    }
    for (i, actor) in actors.enumerated() {
        guard let policy = actor.sandbox.policy else { continue }
        let prefix = "actors.\(i).sandbox.policy."
        if let r = AdmissionStringRule(field: prefix + "sbpl_source", maximum: PWShmLayout.policyBytes - 1, requiresCString: true).failure(policy.sbpl_source) { return r }
        if let n = policy.params?.count, let r = count(prefix + "params", n, PWShmLayout.maxParams) { return r }
        for param in workerParamsFromPolicy(policy) {
            if var r = AdmissionStringRule(field: "key", maximum: parameterKeyAdmission.maximum, requiresCString: true).failure(param.key) {
                r.parameter_key = nil; return r
            }
            if var r = AdmissionStringRule(field: prefix + "value", maximum: PWShmLayout.paramValueMax - 1, requiresCString: true).failure(param.value) {
                r.parameter_key = parameterKeyAdmission.safeEcho(param.key); return r
            }
        }
    }
    let probes = actions.compactMap { $0.probe }
    let capacity = CWorkerInput(workerExecutablePath: "", policy: "", params: [], slots: workerSlotsFromProbePlan(probes))
    if let refused = workerAdmissionFailure(capacity) { return refused }
    return queryAdmissionFailure(probes)
}

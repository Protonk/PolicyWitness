import Darwin
import Foundation

// The actor form's normalized plan: typed single-assignment reference tables
// built from the whole request before any process work. Public admission,
// direct XPC admission and the scheduler use the same tables. Every refusal
// carries a bounded field path; a runtime failure of a producer never makes an
// admitted request malformed.

struct TokenIndex: Equatable { let rawValue: Int }
struct DeliveryIndex: Equatable { let rawValue: Int }
struct HandleIndex: Equatable { let rawValue: Int }
struct ActorIndex: Equatable { let rawValue: Int }

enum ResolvedExtensionOperation {
    case issue(token: TokenIndex)
    case transfer(token: TokenIndex, delivery: DeliveryIndex, recipient: ActorIndex)
    case consume(delivery: DeliveryIndex, handle: HandleIndex, lastDeliveryUse: Bool)
    case release(handle: HandleIndex)
}
enum ResolvedActionBody {
    case probe(PWRunnerProbeStep, PWAttemptKind)
    case authority(ResolvedExtensionOperation)
}
struct ResolvedAction {
    let stepID: String
    let globalSlot: Int
    let actorLocalSlot: Int
    let body: ResolvedActionBody
    var probe: PWRunnerProbeStep? { if case .probe(let probe, _) = body { return probe }; return nil }
}
struct ActorPlanActor {
    let id: String
    let index: Int
    let applies: Bool
    let policy: PWRunnerPolicySpec?
    let equipment: String?
    let requiredEntitlements: [String]
    /// Issues, sends, receives, consumes or releases extensions: such an actor
    /// cannot exec in this delivery.
    let participates: Bool
    /// Global slot indexes of this actor's actions, in schedule order.
    let slots: [Int]
    /// Global phase indexes this actor is activated in, in schedule order.
    let visits: [Int]
}

struct ActorPlanPhase {
    let id: String
    let index: Int
    let actorIndex: Int
    /// 1-based ordinal among this actor's activations.
    let visit: Int
    let firstSlot: Int
    let endSlot: Int
    let actions: [ResolvedAction]
    let afterTermination: Int?
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
    let outboundPosition: Int
    let deliveries: [String]
    /// The last step that reads the token: its final transfer, or the issue itself.
    let lastUseSlot: Int
}

struct ActorPlanDelivery {
    let ref: String
    let tokenRef: String
    let tokenIndex: TokenIndex
    let inboundPosition: Int
    let sourceActorIndex: Int
    let recipientActorIndex: Int
    let stepID: String
    let slot: Int
    let phaseIndex: Int
    let handles: [String]
    /// The last step that reads the delivered bytes: its final consume, or the transfer.
    let lastUseSlot: Int
}

struct ActorPlanHandle {
    let ref: String
    let deliveryRef: String
    let deliveryIndex: DeliveryIndex
    let actorIndex: Int
    let stepID: String
    let slot: Int
    let phaseIndex: Int
    let releaseStepID: String?
    let releaseSlot: Int?
}

struct ActorPlan {
    let actors: [ActorPlanActor]
    let phases: [ActorPlanPhase]
    let tokens: [ActorPlanToken]
    let deliveries: [ActorPlanDelivery]
    let handles: [ActorPlanHandle]
    let slotOfStep: [String: Int]
    let inboundCounts: [Int]
    let outboundCounts: [Int]
    let localSlotOfGlobal: [Int]
    var issueCount: Int { tokens.count }
    var transferCount: Int { deliveries.count }
    var consumeCount: Int { handles.count }
    var releaseCount: Int { handles.filter { $0.releaseSlot != nil }.count }
    var actionCount: Int { slotOfStep.count }
    var authorityRequired: Bool { !tokens.isEmpty || !deliveries.isEmpty }
    func token(_ ref: String) -> ActorPlanToken? { tokens.first { $0.ref == ref } }
    func delivery(_ ref: String) -> ActorPlanDelivery? { deliveries.first { $0.ref == ref } }
    func handle(_ ref: String) -> ActorPlanHandle? { handles.first { $0.ref == ref } }
    func actor(named id: String) -> ActorPlanActor? { actors.first { $0.id == id } }
}

/// Defensive checks at the fallible encoding boundary. These compare the
/// resolved assignments; no submitted reference is interpreted a second time.
func actorPlanAssignmentsConsistent(_ plan: ActorPlan) -> Bool {
    let actions = plan.phases.flatMap { $0.actions }
    guard plan.actors.count <= PWActorLimits.actors, plan.phases.count <= PWActorLimits.phases,
          actions.count == plan.actionCount, actions.count <= PWActorLimits.actions,
          plan.tokens.count <= PWActorLimits.issues, plan.deliveries.count <= PWActorLimits.deliveries,
          plan.handles.count <= PWActorLimits.handles,
          plan.localSlotOfGlobal.count == actions.count,
          plan.inboundCounts.count == plan.actors.count, plan.outboundCounts.count == plan.actors.count else { return false }
    var offset = 0
    for (index, phase) in plan.phases.enumerated() {
        guard phase.index == index, plan.actors.indices.contains(phase.actorIndex), phase.firstSlot == offset,
              phase.endSlot == offset + phase.actions.count else { return false }
        for (position, action) in phase.actions.enumerated() {
            guard action.globalSlot == offset + position, plan.slotOfStep[action.stepID] == action.globalSlot else { return false }
        }
        offset = phase.endSlot
    }
    for (index, actor) in plan.actors.enumerated() {
        let visits = plan.phases.filter { $0.actorIndex == index }
        guard actor.index == index, actor.visits == visits.map({ $0.index }), !actor.visits.isEmpty,
              actor.slots == visits.flatMap({ $0.actions.map { $0.globalSlot } }),
              visits.enumerated().allSatisfy({ $0.element.visit == $0.offset + 1 }),
              plan.inboundCounts[index] >= 0, plan.inboundCounts[index] <= PWActorLimits.deliveries,
              plan.outboundCounts[index] >= 0, plan.outboundCounts[index] <= PWActorLimits.issues else { return false }
        for (slot, global) in actor.slots.enumerated() {
            guard actions.indices.contains(global), actions[global].actorLocalSlot == slot,
                  plan.localSlotOfGlobal[global] == slot else { return false }
        }
        guard plan.tokens.filter({ $0.actorIndex == index }).map({ $0.outboundPosition }) == Array(0..<plan.outboundCounts[index]),
              plan.deliveries.filter({ $0.recipientActorIndex == index }).map({ $0.inboundPosition }) == Array(0..<plan.inboundCounts[index]) else { return false }
    }
    for (index, token) in plan.tokens.enumerated() {
        guard plan.phases.indices.contains(token.phaseIndex), plan.phases[token.phaseIndex].actorIndex == token.actorIndex,
              actions.indices.contains(token.slot), actions.indices.contains(token.lastUseSlot), token.lastUseSlot >= token.slot,
              actions[token.slot].stepID == token.stepID,
              case .authority(.issue(let actual)) = actions[token.slot].body, actual.rawValue == index else { return false }
        if token.lastUseSlot != token.slot {
            guard case .authority(.transfer(let last, _, _)) = actions[token.lastUseSlot].body, last.rawValue == index else { return false }
        }
    }
    for (index, delivery) in plan.deliveries.enumerated() {
        guard plan.tokens.indices.contains(delivery.tokenIndex.rawValue), plan.actors.indices.contains(delivery.recipientActorIndex),
              plan.tokens[delivery.tokenIndex.rawValue].actorIndex == delivery.sourceActorIndex,
              plan.tokens[delivery.tokenIndex.rawValue].slot < delivery.slot,
              actions.indices.contains(delivery.slot), actions.indices.contains(delivery.lastUseSlot), delivery.lastUseSlot >= delivery.slot,
              actions[delivery.slot].stepID == delivery.stepID,
              case .authority(.transfer(let token, let actual, let recipient)) = actions[delivery.slot].body,
              token == delivery.tokenIndex, actual.rawValue == index, recipient.rawValue == delivery.recipientActorIndex else { return false }
        if delivery.lastUseSlot != delivery.slot {
            guard case .authority(.consume(let last, _, let final)) = actions[delivery.lastUseSlot].body,
                  last.rawValue == index, final else { return false }
        }
    }
    for (index, handle) in plan.handles.enumerated() {
        guard plan.deliveries.indices.contains(handle.deliveryIndex.rawValue),
              plan.deliveries[handle.deliveryIndex.rawValue].recipientActorIndex == handle.actorIndex,
              plan.deliveries[handle.deliveryIndex.rawValue].slot < handle.slot,
              actions.indices.contains(handle.slot), actions[handle.slot].stepID == handle.stepID,
              case .authority(.consume(let delivery, let actual, let final)) = actions[handle.slot].body,
              delivery == handle.deliveryIndex, actual.rawValue == index,
              final == (plan.deliveries[delivery.rawValue].lastUseSlot == handle.slot) else { return false }
        if let release = handle.releaseSlot {
            guard actions.indices.contains(release), release > handle.slot, actions[release].stepID == handle.releaseStepID,
                  case .authority(.release(let actual)) = actions[release].body, actual.rawValue == index else { return false }
        }
    }
    // Check the reverse association too: every resolved action has exactly
    // one defining table entry, and a nominated last use cannot precede a
    // later action. These observations only validate the admitted assignments;
    // they never replace or repair them for execution.
    var issues = Array(repeating: 0, count: plan.tokens.count)
    var transfers = Array(repeating: 0, count: plan.deliveries.count)
    var consumes = Array(repeating: 0, count: plan.handles.count)
    var releases = Array(repeating: 0, count: plan.handles.count)
    var tokenLastUses = plan.tokens.map { $0.slot }
    var deliveryLastUses = plan.deliveries.map { $0.slot }
    for phase in plan.phases {
        for action in phase.actions {
            guard case .authority(let operation) = action.body else { continue }
            switch operation {
            case .issue(let index):
                guard plan.tokens.indices.contains(index.rawValue) else { return false }
                let token = plan.tokens[index.rawValue]
                guard token.slot == action.globalSlot, token.phaseIndex == phase.index,
                      token.actorIndex == phase.actorIndex else { return false }
                issues[index.rawValue] += 1
            case .transfer(let token, let index, let recipient):
                guard plan.tokens.indices.contains(token.rawValue),
                      plan.deliveries.indices.contains(index.rawValue) else { return false }
                let delivery = plan.deliveries[index.rawValue]
                guard delivery.slot == action.globalSlot, delivery.phaseIndex == phase.index,
                      delivery.sourceActorIndex == phase.actorIndex, delivery.tokenIndex == token,
                      delivery.recipientActorIndex == recipient.rawValue else { return false }
                transfers[index.rawValue] += 1
                tokenLastUses[token.rawValue] = action.globalSlot
            case .consume(let delivery, let index, let lastUse):
                guard plan.deliveries.indices.contains(delivery.rawValue),
                      plan.handles.indices.contains(index.rawValue) else { return false }
                let handle = plan.handles[index.rawValue]
                guard handle.slot == action.globalSlot, handle.phaseIndex == phase.index,
                      handle.actorIndex == phase.actorIndex, handle.deliveryIndex == delivery,
                      lastUse == (plan.deliveries[delivery.rawValue].lastUseSlot == action.globalSlot) else { return false }
                consumes[index.rawValue] += 1
                deliveryLastUses[delivery.rawValue] = action.globalSlot
            case .release(let index):
                guard plan.handles.indices.contains(index.rawValue) else { return false }
                let handle = plan.handles[index.rawValue]
                guard handle.releaseSlot == action.globalSlot, handle.releaseStepID == action.stepID,
                      handle.actorIndex == phase.actorIndex else { return false }
                releases[index.rawValue] += 1
            }
        }
    }
    guard issues.allSatisfy({ $0 == 1 }), transfers.allSatisfy({ $0 == 1 }),
          consumes.allSatisfy({ $0 == 1 }),
          releases == plan.handles.map({ $0.releaseSlot == nil ? 0 : 1 }),
          tokenLastUses == plan.tokens.map({ $0.lastUseSlot }),
          deliveryLastUses == plan.deliveries.map({ $0.lastUseSlot }) else { return false }
    return true
}

private struct BuilderActor {
    let id: String
    let index: Int
    let applies: Bool
    let policy: PWRunnerPolicySpec?
    let equipment: String?
    let requiredEntitlements: [String]
    /// Issues, sends, receives, consumes or releases extensions: such an actor
    /// cannot exec in this delivery.
    var participates = false
    /// Global slot indexes of this actor's actions, in schedule order.
    var slots: [Int] = []
    /// Global phase indexes this actor is activated in, in schedule order.
    var visits: [Int] = []
}

private struct BuilderPhase {
    let id: String
    let index: Int
    let actorIndex: Int
    /// 1-based ordinal among this actor's activations.
    let visit: Int
    let firstSlot: Int
    let endSlot: Int
    let actions: [PWRunnerPhaseAction]
    let afterTermination: Int?
}

private struct BuilderToken {
    let ref: String
    let actorIndex: Int
    let stepID: String
    let slot: Int
    let phaseIndex: Int
    let family: String
    let target: String
    let authority: String
    let outboundPosition: Int
    var deliveries: [String] = []
    /// The last step that reads the token: its final transfer, or the issue itself.
    var lastUseSlot: Int
}

private struct BuilderDelivery {
    let ref: String
    let tokenRef: String
    let tokenIndex: TokenIndex
    let inboundPosition: Int
    let sourceActorIndex: Int
    let recipientActorIndex: Int
    let stepID: String
    let slot: Int
    let phaseIndex: Int
    var handles: [String] = []
    /// The last step that reads the delivered bytes: its final consume, or the transfer.
    var lastUseSlot: Int
}

private struct BuilderHandle {
    let ref: String
    let deliveryRef: String
    let deliveryIndex: DeliveryIndex
    let actorIndex: Int
    let stepID: String
    let slot: Int
    let phaseIndex: Int
    var releaseStepID: String? = nil
    var releaseSlot: Int? = nil
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
    var actors: [BuilderActor] = []
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
        if let equipment = actor.equipment, !["selected", "unentitled"].contains(equipment) {
            return fail("unsupported_equipment", path + ["equipment"])
        }
        var requirements = Set<String>()
        for (ri, key) in actor.required_entitlements.enumerated() {
            if key.isEmpty { return fail("empty_entitlement", path + ["required_entitlements", String(ri)]) }
            if !requirements.insert(key).inserted { return fail("duplicate_entitlement", path + ["required_entitlements", String(ri)]) }
        }
        actors.append(BuilderActor(id: actor.actor_id, index: i, applies: actor.applies, policy: actor.sandbox.policy,
                                   equipment: actor.equipment, requiredEntitlements: actor.required_entitlements))
    }

    guard let submittedPhases = spec.phases else { return fail("actors_require_phases", ["phases"]) }
    if submittedPhases.isEmpty { return fail("empty_phases", ["phases"]) }
    var phases: [BuilderPhase] = []
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
        var dependency: Int?
        if let gate = phase.after_termination {
            guard let source = actors.firstIndex(where: { $0.id == gate.actor_id }) else {
                return fail("invalid_termination_dependency", path + ["after_termination", "actor_id"])
            }
            if source == actor { return fail("invalid_termination_dependency", path + ["after_termination", "actor_id"]) }
            guard let final = submittedPhases.lastIndex(where: { $0.actor_id == gate.actor_id }), final < pi else {
                return fail("invalid_termination_dependency", path + ["after_termination", "actor_id"])
            }
            dependency = source
        }
        phases.append(BuilderPhase(id: phase.phase_id, index: pi, actorIndex: actor, visit: actors[actor].visits.count,
                                     firstSlot: first, endSlot: slot, actions: phase.actions, afterTermination: dependency))
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
                    let present = op.contains(key)
                    if operands.contains(key) && op.operand(key) == nil { return fail("missing_field", path + ["extension", key.rawValue]) }
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
    var tokens: [BuilderToken] = []
    var deliveries: [BuilderDelivery] = []
    var handles: [BuilderHandle] = []
    var assigned = Set<String>()
    var outboundCounts = Array(repeating: 0, count: actors.count)
    var inboundCounts = Array(repeating: 0, count: actors.count)
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
                tokens.append(BuilderToken(ref: ref, actorIndex: phase.actorIndex, stepID: value.step_id, slot: slot,
                    phaseIndex: phase.index, family: op.family!, target: op.target!, authority: op.authority!, outboundPosition: outboundCounts[phase.actorIndex], lastUseSlot: slot))
                outboundCounts[phase.actorIndex] += 1
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
                deliveries.append(BuilderDelivery(ref: ref, tokenRef: op.token_ref!, tokenIndex: TokenIndex(rawValue: tokenIndex), inboundPosition: inboundCounts[recipient], sourceActorIndex: phase.actorIndex,
                    recipientActorIndex: recipient, stepID: value.step_id, slot: slot, phaseIndex: phase.index, lastUseSlot: slot))
                inboundCounts[recipient] += 1
            case "consume":
                guard let deliveryIndex = deliveries.firstIndex(where: { $0.ref == op.delivery_ref! }) else {
                    return fail("unknown_delivery_reference", path + ["delivery_ref"])
                }
                if deliveries[deliveryIndex].recipientActorIndex != phase.actorIndex { return fail("wrong_owner_reference", path + ["delivery_ref"]) }
                let ref = op.handle_ref!
                if !assigned.insert(ref).inserted { return fail("duplicate_reference", path + ["handle_ref"]) }
                deliveries[deliveryIndex].handles.append(ref)
                deliveries[deliveryIndex].lastUseSlot = slot
                handles.append(BuilderHandle(ref: ref, deliveryRef: op.delivery_ref!, deliveryIndex: DeliveryIndex(rawValue: deliveryIndex), actorIndex: phase.actorIndex,
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
    let tokenIndices = Dictionary(uniqueKeysWithValues: tokens.enumerated().map { ($0.element.ref, TokenIndex(rawValue: $0.offset)) })
    let deliveryIndices = Dictionary(uniqueKeysWithValues: deliveries.enumerated().map { ($0.element.ref, DeliveryIndex(rawValue: $0.offset)) })
    let handleIndices = Dictionary(uniqueKeysWithValues: handles.enumerated().map { ($0.element.ref, HandleIndex(rawValue: $0.offset)) })
    var localSlots = Array(repeating: 0, count: slot)
    for actor in actors { for (local, global) in actor.slots.enumerated() { localSlots[global] = local } }
    let resolvedPhases = phases.map { phase in
        let actions = phase.actions.enumerated().map { ai, action -> ResolvedAction in
            let global = phase.firstSlot + ai
            let body: ResolvedActionBody
            switch action {
            case .probe(let probe): body = .probe(probe, mapAttemptKindOrNil(probe.attempt)!)
            case .extensionAction(let value):
                let op = value.intervention
                // All names and operation cases were checked in the single builder above.
                switch op.operation {
                case "issue": body = .authority(.issue(token: tokenIndices[op.token_ref!]!))
                case "transfer":
                    let delivery = deliveryIndices[op.delivery_ref!]!
                    body = .authority(.transfer(token: tokenIndices[op.token_ref!]!, delivery: delivery,
                        recipient: ActorIndex(rawValue: deliveries[delivery.rawValue].recipientActorIndex)))
                case "consume":
                    let delivery = deliveryIndices[op.delivery_ref!]!
                    body = .authority(.consume(delivery: delivery, handle: handleIndices[op.handle_ref!]!,
                        lastDeliveryUse: deliveries[delivery.rawValue].lastUseSlot == global))
                case "release": body = .authority(.release(handle: handleIndices[op.handle_ref!]!))
                default: preconditionFailure("validated authority operation")
                }
            }
            return ResolvedAction(stepID: action.stepID, globalSlot: global, actorLocalSlot: localSlots[global], body: body)
        }
        return ActorPlanPhase(id: phase.id, index: phase.index, actorIndex: phase.actorIndex, visit: phase.visit,
                              firstSlot: phase.firstSlot, endSlot: phase.endSlot, actions: actions, afterTermination: phase.afterTermination)
    }
    return .success(ActorPlan(
        actors: actors.map { ActorPlanActor(id: $0.id, index: $0.index, applies: $0.applies, policy: $0.policy,
            equipment: $0.equipment, requiredEntitlements: $0.requiredEntitlements,
            participates: $0.participates, slots: $0.slots, visits: $0.visits) },
        phases: resolvedPhases,
        tokens: tokens.map { ActorPlanToken(ref: $0.ref, actorIndex: $0.actorIndex, stepID: $0.stepID, slot: $0.slot,
            phaseIndex: $0.phaseIndex, family: $0.family, target: $0.target, authority: $0.authority,
            outboundPosition: $0.outboundPosition, deliveries: $0.deliveries, lastUseSlot: $0.lastUseSlot) },
        deliveries: deliveries.map { ActorPlanDelivery(ref: $0.ref, tokenRef: $0.tokenRef, tokenIndex: $0.tokenIndex,
            inboundPosition: $0.inboundPosition, sourceActorIndex: $0.sourceActorIndex,
            recipientActorIndex: $0.recipientActorIndex, stepID: $0.stepID, slot: $0.slot, phaseIndex: $0.phaseIndex,
            handles: $0.handles, lastUseSlot: $0.lastUseSlot) },
        handles: handles.map { ActorPlanHandle(ref: $0.ref, deliveryRef: $0.deliveryRef, deliveryIndex: $0.deliveryIndex,
            actorIndex: $0.actorIndex, stepID: $0.stepID, slot: $0.slot, phaseIndex: $0.phaseIndex,
            releaseStepID: $0.releaseStepID, releaseSlot: $0.releaseSlot) },
        slotOfStep: slotOfStep, inboundCounts: inboundCounts, outboundCounts: outboundCounts, localSlotOfGlobal: localSlots))
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
        let requirements = "actors.\(i).required_entitlements"
        if let r = count(requirements, actor.required_entitlements.count, PWActorLimits.requiredEntitlements) { return r }
        for (j, key) in actor.required_entitlements.enumerated() {
            if let r = AdmissionStringRule(field: requirements + ".\(j)", maximum: PWActorLimits.entitlementKeyBytes, requiresCString: true).failure(key) { return r }
        }
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

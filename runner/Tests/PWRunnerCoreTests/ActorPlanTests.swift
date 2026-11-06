import Foundation
@testable import PWRunnerCore

// The actor form's contract: the public decoder admits it, the normalizer
// builds owned reference tables, and the shared corpus's actor refusals match.
// Nothing here launches a process.

/// The shared corpus's actor-form examples: every request that names actors.
private func actorCorpus() throws -> [[String: Any]] {
    let url = repositoryRoot().appendingPathComponent("tests/fixtures/request_contract/examples.json")
    let corpus = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [[String: Any]]
    return corpus.filter { ($0["request"] as? [String: Any])?["actors"] != nil }
}

private func corpusText(_ example: [String: Any]) throws -> String {
    let encoded = try JSONSerialization.data(withJSONObject: example["request"]!)
    return String(decoding: encoded, as: UTF8.self)
        .replacingOccurrences(of: "$EFFECT", with: "/private/tmp/request-grammar-effect")
}

private func decodeActorForm(_ text: String) throws -> PWRunnerRunSpec {
    try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: Data(text.utf8))
}

/// The same gate the live host applies: capacity, then meaning.
private func draftRefusal(_ text: String) -> PWRunnerRequestFailure? {
    do {
        let parsed = try decodeActorForm(text)
        switch admitSpecimen(parsed) {
        case .accepted: return nil
        case .capacity(let capacity): return requestCapacityFailure(capacity, parsed: parsed)
        case .refused(let failure): return failure
        }
    } catch { return requestDecodeFailure(error) }
}

private func replacingAssignments(_ plan: ActorPlan, actors: [ActorPlanActor]? = nil, tokens: [ActorPlanToken]? = nil,
                                  phases: [ActorPlanPhase]? = nil) -> ActorPlan {
    ActorPlan(actors: actors ?? plan.actors, phases: phases ?? plan.phases, tokens: tokens ?? plan.tokens,
        deliveries: plan.deliveries, handles: plan.handles, slotOfStep: plan.slotOfStep,
        inboundCounts: plan.inboundCounts, outboundCounts: plan.outboundCounts,
        localSlotOfGlobal: plan.localSlotOfGlobal)
}

private func expectAssignmentRefusal(_ plan: ActorPlan, parsed: PWRunnerRunSpec) throws {
    try expectTrue(!actorPlanAssignmentsConsistent(plan))
    do {
        _ = try ActorTranslation(plan: plan, parsed: parsed,
            workerExecutablePaths: Array(repeating: "/unused", count: plan.actors.count))
        throw TestFailure(message: "inconsistent admitted assignments reached translation")
    } catch PWRunnerPreparationFailureError.inconsistentAssignment {}
}

func runActorPlanTests(_ tk: TestKit) {
    tk.group("actor form entry points") {
        tk.run("the public decoder admits the actor form and names it") {
            let example = try actorCorpus().first { $0["id"] as! String == "actors_redelegation" }!
            let parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: Data(try corpusText(example).utf8))
            try expectTrue(parsed.isActorForm)
            try expectNil(parsed.policy)
            try expectEqual(parsed.actors?.map { $0.actor_id }, ["A", "B", "C"])
        }
        tk.run("ordinary requests remain valid and declaration fields are unknown even when null") {
            let ordinary = """
            {"schema_version": \(PWContract.requestSchema), "specimen_id": "ordinary",
             "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)"}, "probe_plan": []}
            """
            try expectNil(requestMeaningFailure(try decodeActorForm(ordinary)))
            for field in ["null", "[]"] {
                let removed = ordinary.dropLast() + ", \"extensions\": " + field + "}"
                try expectEqual(draftRefusal(removed)?.code, "unknown_field")
                try expectEqual(draftRefusal(removed)?.path, ["extensions"])
            }
        }
        tk.run("actor requirement limits count UTF8 bytes and permit exact capacities") {
            let base = try actorCorpus().first { $0["id"] as! String == "actors_redelegation" }!
            var parsed = try decodeActorForm(corpusText(base))
            for key in [String(repeating: "a", count: 255), String(repeating: "é", count: 127) + "a"] {
                parsed.actors![0].required_entitlements = [key] + (1..<64).map { "key-\($0)" }
                if case .accepted = admitSpecimen(parsed) {} else { throw TestFailure(message: "exact requirement capacity refused") }
                parsed.actors![0].required_entitlements[0] += "a"
                guard case .capacity(let refused) = admitSpecimen(parsed) else { throw TestFailure(message: "excess bytes admitted") }
                try expectEqual(refused.maximum, 255)
            }
            parsed.actors![0].required_entitlements = (0..<65).map { "key-\($0)" }
            guard case .capacity(let refused) = admitSpecimen(parsed) else { throw TestFailure(message: "excess requirements admitted") }
            try expectEqual(refused.maximum, 64)
        }
    }
    tk.group("actor form corpus") {
        tk.run("every example normalizes or refuses as recorded") {
            for example in try actorCorpus() {
                let name = example["id"] as! String
                let expected = (example["expected"] as! [String: Any])["xpc"]!
                let failure = draftRefusal(try corpusText(example))
                if expected is NSNull { try expectNil(failure, name) }
                else {
                    guard let failure else { throw TestFailure(message: "\(name): expected refusal") }
                    let actual = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(failure)) as! NSDictionary
                    try expectTrue(actual.isEqual(to: expected as! [String: Any]), "\(name): \(actual) != \(expected)")
                }
            }
        }
        tk.run("the principal specimen's tables name their owners, producers and last uses") {
            let example = try actorCorpus().first { $0["id"] as! String == "actors_redelegation" }!
            let parsed = try decodeActorForm(try corpusText(example))
            guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "principal specimen refused") }
            try expectEqual(plan.actors.map { $0.id }, ["A", "B", "C"])
            try expectEqual(plan.actors.map { $0.applies }, [false, true, true])
            try expectEqual(plan.actors.map { $0.participates }, [true, true, true])
            // The corpus copy ends with A's effect phase, the file creation
            // that witnesses acceptance through the CLI and direct XPC.
            try expectEqual(plan.phases.map { $0.actorIndex }, [1, 2, 0, 1, 1, 2, 2, 1, 0])
            try expectEqual(plan.phases.map { $0.visit }, [1, 1, 1, 2, 3, 2, 3, 4, 2])
            try expectEqual(plan.actors[1].visits, [0, 3, 4, 7])
            try expectEqual(plan.phases.map { $0.firstSlot }, [0, 1, 2, 4, 5, 8, 9, 11, 12])
            try expectEqual(plan.actionCount, 13)
            try expectEqual(plan.tokens.map { $0.ref }, ["ta", "tb"])
            try expectEqual(plan.tokens.map { $0.actorIndex }, [0, 1])
            try expectEqual(plan.tokens.map { $0.deliveries }, [["db"], ["dc"]])
            try expectEqual(plan.tokens.map { $0.lastUseSlot }, [plan.slotOfStep["a_to_b"]!, plan.slotOfStep["b_to_c"]!])
            try expectEqual(plan.deliveries.map { ($0.ref, $0.recipientActorIndex, $0.sourceActorIndex) }.map { "\($0.0):\($0.1):\($0.2)" }, ["db:1:0", "dc:2:1"])
            try expectEqual(plan.deliveries.map { $0.lastUseSlot }, [plan.slotOfStep["b_consume_first"]!, plan.slotOfStep["c_consume_second"]!])
            try expectEqual(plan.handles.map { $0.ref }, ["hb", "hc"])
            try expectEqual(plan.handles.map { $0.actorIndex }, [1, 2])
            try expectEqual(plan.handles.map { $0.releaseStepID }, ["b_release", "c_release"])
            try expectEqual(plan.releaseCount, 2)
            try expectEqual(plan.token("ta")?.target, "/private/tmp/request-grammar-effect")
            try expectEqual(plan.token("ta")?.authority, "read")
        }
        tk.run("repeated consumes and self-transfers keep distinct references") {
            let corpus = try actorCorpus()
            let repeated = try decodeActorForm(try corpusText(corpus.first { $0["id"] as! String == "repeated_consume" }!))
            guard case .success(let plan) = normalizeActorPlan(repeated) else { throw TestFailure(message: "refused") }
            try expectEqual(plan.delivery("db")?.handles, ["hb", "hb2"])
            try expectEqual(plan.delivery("db")?.lastUseSlot, plan.slotOfStep["b_consume_again"])
            let selfTransfer = try decodeActorForm(try corpusText(corpus.first { $0["id"] as! String == "self_transfer" }!))
            guard case .success(let selfPlan) = normalizeActorPlan(selfTransfer) else { throw TestFailure(message: "refused") }
            try expectEqual(selfPlan.delivery("da")?.recipientActorIndex, 0)
            try expectEqual(selfPlan.token("ta")?.deliveries, ["db", "da"])
        }
        tk.run("translation refuses a token last use shortened before remaining transfers") {
            let example = try actorCorpus().first { $0["id"] as! String == "self_transfer" }!
            let parsed = try decodeActorForm(corpusText(example))
            guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "refused") }
            try expectTrue(actorPlanAssignmentsConsistent(plan))
            _ = try ActorTranslation(plan: plan, parsed: parsed,
                workerExecutablePaths: Array(repeating: "/unused", count: plan.actors.count))
            let index = plan.tokens.firstIndex { $0.ref == "ta" }!
            let token = plan.tokens[index]
            let transfers = plan.deliveries.filter { $0.tokenIndex.rawValue == index }
            try expectTrue(transfers.count > 1)
            for shortened in [token.slot, transfers.first!.slot] {
                try expectTrue(shortened < token.lastUseSlot)
                var tokens = plan.tokens
                tokens[index] = ActorPlanToken(ref: token.ref, actorIndex: token.actorIndex, stepID: token.stepID,
                    slot: token.slot, phaseIndex: token.phaseIndex, family: token.family, target: token.target,
                    authority: token.authority, outboundPosition: token.outboundPosition,
                    deliveries: token.deliveries, lastUseSlot: shortened)
                try expectAssignmentRefusal(replacingAssignments(plan, tokens: tokens), parsed: parsed)
            }
        }
        tk.run("translation refuses extra authority actions using existing definitions") {
            let example = try actorCorpus().first { $0["id"] as! String == "actors_redelegation" }!
            let parsed = try decodeActorForm(corpusText(example))
            guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "refused") }
            try expectTrue(actorPlanAssignmentsConsistent(plan))
            let phaseIndex = plan.phases.lastIndex { $0.actions.contains { $0.probe != nil } }!
            let phase = plan.phases[phaseIndex]
            let actionIndex = phase.actions.firstIndex { $0.probe != nil }!
            let original = phase.actions[actionIndex]
            let operations: [ResolvedExtensionOperation] = [
                .issue(token: TokenIndex(rawValue: 0)),
                .transfer(token: TokenIndex(rawValue: 0), delivery: DeliveryIndex(rawValue: 0),
                    recipient: ActorIndex(rawValue: plan.deliveries[0].recipientActorIndex)),
                .consume(delivery: plan.handles[0].deliveryIndex, handle: HandleIndex(rawValue: 0), lastDeliveryUse: false),
                .release(handle: HandleIndex(rawValue: 0))
            ]
            for operation in operations {
                var actions = phase.actions
                actions[actionIndex] = ResolvedAction(stepID: original.stepID, globalSlot: original.globalSlot,
                    actorLocalSlot: original.actorLocalSlot, body: .authority(operation))
                var phases = plan.phases
                phases[phaseIndex] = ActorPlanPhase(id: phase.id, index: phase.index, actorIndex: phase.actorIndex,
                    visit: phase.visit, firstSlot: phase.firstSlot, endSlot: phase.endSlot, actions: actions,
                    afterTermination: phase.afterTermination)
                try expectAssignmentRefusal(replacingAssignments(plan, phases: phases), parsed: parsed)
            }
        }
        tk.run("orchestration preserves inconsistent index refusal even when equipment is unavailable") {
            let example = try actorCorpus().first { $0["id"] as! String == "actors_redelegation" }!
            let parsed = try decodeActorForm(corpusText(example))
            guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "refused") }
            var malformed: [ActorPlan] = []
            for invalidIndex in [-1, plan.actors.count] {
                var actors = plan.actors
                let actor = actors[0]
                actors[0] = ActorPlanActor(id: actor.id, index: invalidIndex, applies: actor.applies,
                    policy: actor.policy, equipment: actor.equipment, requiredEntitlements: actor.requiredEntitlements,
                    participates: actor.participates, slots: actor.slots, visits: actor.visits)
                malformed.append(replacingAssignments(plan, actors: actors))
                var phases = plan.phases
                let phase = phases[0]
                phases[0] = ActorPlanPhase(id: phase.id, index: phase.index, actorIndex: invalidIndex,
                    visit: phase.visit, firstSlot: phase.firstSlot, endSlot: phase.endSlot,
                    actions: phase.actions, afterTermination: phase.afterTermination)
                malformed.append(replacingAssignments(plan, phases: phases))
            }
            let absentBundle = FileManager.default.temporaryDirectory.appendingPathComponent("pw-no-equipment-" + UUID().uuidString)
            for invalid in malformed {
                let reply = CWorkerOrchestrator.run(admitted: AdmittedSpecimen(request: parsed, actorPlan: invalid),
                    policyHash: "", bundleId: "test", workerExecutablePath: "/unused-worker",
                    validatorExecutablePath: "/unused-validator", equipmentBundleURL: absentBundle)
                try expectEqual(reply.preparation_failure?.stage, "resolved_plan")
                try expectEqual(reply.preparation_failure?.code, "inconsistent_assignment")
                try expectEqual(reply.equipment_inventory?.status, "refused")
                try expectEqual(reply.actors?.map { $0.actor_id }, parsed.actors?.map { $0.actor_id })
                try expectEqual(reply.actors?.map { $0.index }, Array(plan.actors.indices))
                try expectTrue(reply.actors!.allSatisfy { $0.launch == nil && $0.subprocess == nil && $0.setup_status == "launch_refused" })
                try expectEqual(reply.phases.map { $0.actor_id }, parsed.phases!.map { $0.actor_id })
                try expectEqual(reply.phases.map { $0.action_ids }, parsed.phases!.map { $0.actions.map { $0.stepID } })
                try expectTrue(reply.phases.allSatisfy { $0.collection_status == "not_reached" && $0.activation_observation == nil })
                try expectTrue(reply.steps.isEmpty && reply.extension_events!.isEmpty && reply.resources!.tokens.isEmpty)
                let encoded = try pwRunnerEncodeJSON(reply)
                let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: encoded)
                try expectEqual(decoded.preparation_failure?.code, "inconsistent_assignment")
            }
        }
        tk.run("empty visits retain their actor-local position before another actor's action") {
            let text = """
            {"schema_version": \(PWContract.requestSchema), "specimen_id": "empty_visits",
             "actors": [{"actor_id":"A","sandbox":{"mode":"unapplied"}},
                        {"actor_id":"B","sandbox":{"mode":"unapplied"}}],
             "phases": [
               {"phase_id":"a_first","actor_id":"A","actions":[
                 {"step_id":"a1","extension":{"operation":"issue","family":"file","authority":"read","target":"/etc/hosts","token_ref":"t1"}}]},
               {"phase_id":"a_empty","actor_id":"A","actions":[]},
               {"phase_id":"b_first","actor_id":"B","actions":[
                 {"step_id":"b1","extension":{"operation":"issue","family":"file","authority":"read","target":"/etc/hosts","token_ref":"t2"}}]},
               {"phase_id":"a_last","actor_id":"A","actions":[
                 {"step_id":"a2","extension":{"operation":"issue","family":"file","authority":"read","target":"/etc/hosts","token_ref":"t3"}}]},
               {"phase_id":"b_empty","actor_id":"B","actions":[]}]}
            """
            let parsed = try decodeActorForm(text)
            try expectNil(requestMeaningFailure(parsed))
            guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "empty visits refused") }
            let translated = try ActorTranslation(plan: plan, parsed: parsed, workerExecutablePaths: Array(repeating: "/unused", count: plan.actors.count))
            try expectEqual(translated.inputs[0].phases.map { $0.firstSlot }, [0, 1, 1])
            try expectEqual(translated.inputs[0].phases.map { $0.endSlot }, [1, 1, 2])
            try expectEqual(translated.inputs[1].phases.map { $0.firstSlot }, [0, 1])
            try expectEqual(translated.inputs[1].phases.map { $0.endSlot }, [1, 1])
            try expectEqual(translated.phaseInputs.map { $0.firstSlot }, [0, 1, 0, 1, 1])
        }
        tk.run("actor-form capacities are the declared limits") {
            try expectEqual(PWActorLimits.actions, PWShmLayout.maxSteps)
            try expectEqual(PWActorLimits.identifierBytes, PWExtensionLimits.referenceBytes)
            try expectEqual(PWActorLimits.targetBytes, PWShmLayout.extTargetBytes - 1)
            try expectTrue(PWActorLimits.phases > PWRunnerPhase.maximumCount)
        }
    }
}

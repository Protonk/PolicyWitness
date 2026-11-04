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
        if let capacity = CWorkerOrchestrator.admissionFailure(for: parsed) {
            return requestCapacityFailure(capacity, parsed: parsed)
        }
        return requestMeaningFailure(parsed)
    } catch { return requestDecodeFailure(error) }
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
        tk.run("legacy requests decode unchanged beside the actor form") {
            let legacy = """
            {"schema_version": \(PWContract.requestSchema), "specimen_id": "legacy",
             "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)"},
             "phases": [{"phase_id": "p", "actions": [{"step_id": "c", "extension": {"operation": "consume", "token_ref": "t", "handle_ref": "h"}}]}],
             "extensions": [{"token_ref": "t", "target": "/etc/hosts"}]}
            """
            let parsed = try decodeActorForm(legacy)
            try expectFalse(parsed.isActorForm)
            try expectNil(requestMeaningFailure(parsed))
            // A legacy phase naming an actor is inapplicable; an actor-only operand too.
            let withActor = legacy.replacingOccurrences(of: "\"phase_id\": \"p\",", with: "\"phase_id\": \"p\", \"actor_id\": \"A\",")
            try expectEqual(requestMeaningFailure(try decodeActorForm(withActor))?.code, "inapplicable_field")
            try expectEqual(requestMeaningFailure(try decodeActorForm(withActor))?.path, ["phases", "0", "actor_id"])
            let withDelivery = legacy.replacingOccurrences(of: "\"handle_ref\": \"h\"}", with: "\"handle_ref\": \"h\", \"delivery_ref\": \"d\"}")
            try expectEqual(requestMeaningFailure(try decodeActorForm(withDelivery))?.code, "inapplicable_field")
            // A missing legacy handle still fails at decode time.
            let noHandle = legacy.replacingOccurrences(of: ", \"handle_ref\": \"h\"", with: "")
            do { _ = try decodeActorForm(noHandle); throw TestFailure(message: "missing handle admitted") }
            catch let failure as PWRunnerRequestFailure {
                try expectEqual(failure.code, "missing_field")
                try expectEqual(failure.path, ["phases", "0", "actions", "0", "extension", "handle_ref"])
            }
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
            let translated = ActorTranslation(plan: plan, parsed: parsed, workerExecutablePath: "/unused")
            try expectEqual(translated.inputs[0].phases.map { $0.firstSlot }, [0, 1, 1])
            try expectEqual(translated.inputs[0].phases.map { $0.endSlot }, [1, 1, 2])
            try expectEqual(translated.inputs[1].phases.map { $0.firstSlot }, [0, 1])
            try expectEqual(translated.inputs[1].phases.map { $0.endSlot }, [1, 1])
            try expectEqual(translated.phaseInputs.map { $0.firstSlot }, [0, 1, 0, 1, 1])
        }
        tk.run("actor-form capacities are the declared limits") {
            try expectEqual(PWActorLimits.actions, PWShmLayout.maxSteps)
            try expectEqual(PWActorLimits.identifierBytes, PWExtensionLimits.referenceBytes)
            try expectEqual(PWActorLimits.targetBytes, PWExtensionLimits.targetBytes)
            try expectTrue(PWActorLimits.phases > PWRunnerPhase.maximumCount)
        }
    }
}

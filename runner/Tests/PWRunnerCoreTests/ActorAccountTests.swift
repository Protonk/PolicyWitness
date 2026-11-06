import Foundation
@testable import PWRunnerCore

func runActorAccountTests(_ tk: TestKit) {
    tk.group("authority account: publication, ownership and application") {
        tk.run("primary setup failure and independent cleanup stay separate without an application claim") {
            let primary = PWRunnerAuthorityOperation(slot: 5, operation: "fstat", role: "setup", state: "failed",
                native_kind: "integer", native_rc: -1, errno: 9)
            let cleanup = PWRunnerAuthorityOperation(slot: 9, operation: "descriptor_close", role: "cleanup", state: "failed",
                native_kind: "integer", native_rc: -1, errno: 4)
            let scope = PWRunnerAuthorityScope(actor_id: "subject", actor_index: 0, required: true, publication: "observed",
                disposition: "terminal_required_failure", primary_operation: 5, operations: [primary, cleanup], ownership: ["descriptor": "unresolved"])
            var setup = PWRunnerAuthoritySetup(host: PWRunnerAuthorityHost(run: PWRunnerAuthorityScope(disposition: "ready")), workers: [scope])
            try expectEqual(authoritySetupIntegrityErrors(setup, actorIDs: ["subject"], tokenRefs: []), [])
            let application = actorApplicationAssessment(mode: "apply", launched: true, applied: false, evidence: nil, authority: scope)
            try expectEqual(application, PWRunnerActorApplication(state: "not_attempted", basis: "terminal_authority_setup_refusal"))
            setup.workers[0].publication = "not_observed"; setup.workers[0].disposition = nil; setup.workers[0].primary_operation = nil
            try expectEqual(authoritySetupIntegrityErrors(setup, actorIDs: ["subject"], tokenRefs: []), [])
            try expectEqual(setup.workers[0].operations, [primary, cleanup])
            try expectEqual(actorApplicationAssessment(mode: "apply", launched: true, applied: false, evidence: nil, authority: setup.workers[0]).state, "unobserved")
            setup.workers[0].actor_id = "another"
            try expectTrue(authoritySetupIntegrityErrors(setup, actorIDs: ["subject"], tokenRefs: []).contains("authority_actor_association"))
        }
        tk.run("mapping and validation observations cannot manufacture integer returns or errno") {
            for kind in ["mapping", "validation", "symbol", "memory"] {
                let operation = PWRunnerAuthorityOperation(slot: 8, operation: "mmap", role: "setup", state: "failed",
                    native_kind: kind, native_rc: 0, errno: 13)
                let scope = PWRunnerAuthorityScope(actor_id: "subject", actor_index: 0, required: true, publication: "not_observed", operations: [operation])
                let setup = PWRunnerAuthoritySetup(host: PWRunnerAuthorityHost(run: PWRunnerAuthorityScope()), workers: [scope])
                try expectFalse(authoritySetupIntegrityErrors(setup, actorIDs: ["subject"], tokenRefs: []).isEmpty)
            }
        }
        tk.run("unapplied declaration and an unlaunched apply actor retain distinct meanings") {
            try expectEqual(actorApplicationAssessment(mode: "unapplied", launched: false, applied: false, evidence: nil, authority: nil),
                PWRunnerActorApplication(state: "not_requested", basis: "unapplied_declaration"))
            try expectEqual(actorApplicationAssessment(mode: "apply", launched: false, applied: false, evidence: nil, authority: nil),
                PWRunnerActorApplication(state: "not_attempted", basis: "worker_not_launched"))
            try expectFalse(actorApplicationIntegrityErrors(PWRunnerActorApplication(state: "not_attempted", basis: "terminal_compile_refusal"),
                mode: "apply", launched: true, applied: false, evidence: nil, authority: nil).isEmpty)
        }
    }
    tk.group("termination dependency evidence") {
        tk.run("satisfied gate requires an earlier reap reference and a timely charged wait") {
            let observation = PWOwnedReapReference(capture_ordinal: 2)
            var gate = PWRunnerTerminationGate(source_actor_id: "source", source_final_phase_id: "supply", outcome: "satisfied",
                wait: PWHostWait(budget_ms: 5000, elapsed_ms: 2, stop: "satisfied", clock_fault: false),
                observation: observation, activation_eligible: true, capture_ordinal: 3)
            try expectEqual(terminationGateIntegrityErrors(gate, activationStored: true, collectionInvoked: true, releaseStored: true), [])
            gate.observation?.capture_ordinal = 3
            try expectTrue(terminationGateIntegrityErrors(gate, activationStored: true, collectionInvoked: true, releaseStored: true).contains("termination_gate_reap"))
            gate.observation = nil
            try expectTrue(terminationGateIntegrityErrors(gate, activationStored: true, collectionInvoked: false, releaseStored: false).contains("termination_gate_reap"))
            gate.outcome = "timed_out"; gate.activation_eligible = false
            try expectTrue(terminationGateIntegrityErrors(gate, activationStored: true, collectionInvoked: true, releaseStored: false).contains("activation_before_termination_gate"))
        }
    }
    tk.group("complete actor reply account controls") {
        tk.run("gate references must agree with the source child and final activation") {
            let documents = try actorShapeDocuments()
            guard let document = documents.first(where: { doc in
                (doc["phases"] as? [[String: Any]])?.contains { $0["termination_gate"] != nil } == true
            }) else { throw TestFailure(message: "constructed gate companion missing") }
            let baseline = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: document))
            let gateIndex = baseline.phases.firstIndex { $0.termination_gate != nil }!
            let sourceID = baseline.phases[gateIndex].termination_gate!.source_actor_id
            let sourceIndex = baseline.actors!.firstIndex { $0.actor_id == sourceID }!
            let finalIndex = baseline.phases.lastIndex { $0.actor_id == sourceID }!
            // The gate's source observations remain clocked. A failed clock
            // read after the dependent store cannot erase that activation.
            var unclockedDependent = baseline
            unclockedDependent.phases[gateIndex].activation_observation = PWRunnerActorActivation(
                capture_ordinal: 1, observed_ns: nil)
            try expectNil(unclockedDependent.actorExtensionEvidenceProblem())
            let encoded = try pwRunnerEncodeJSON(unclockedDependent)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: encoded)
            try expectEqual(decoded.phases[gateIndex].activation_observation?.capture_ordinal, 1)
            try expectNil(decoded.phases[gateIndex].activation_observation?.observed_ns)
            let mutations: [(inout PWRunnerRunResult) -> Void] = [
                { $0.actors![sourceIndex].owned_reap!.native_rc = 1 },
                { $0.actors![sourceIndex].owned_reap!.departure_requested = true },
                { $0.actors![sourceIndex].owned_reap!.raw_status = 9 },
                { $0.phases[finalIndex].activation_observation!.capture_ordinal = UInt64.max },
                { $0.phases[finalIndex].activation_observation!.observed_ns = nil },
                { $0.phases[gateIndex].activation_observation = PWRunnerActorActivation(capture_ordinal: 1, observed_ns: 0) },
                { $0.phases[gateIndex].termination_gate!.observation!.capture_ordinal = UInt64.max },
                { $0.phases[gateIndex].termination_gate!.wait!.elapsed_ms = 5001 },
                { $0.phases[gateIndex].termination_gate!.wait!.clock_fault = true },
            ]
            for mutate in mutations {
                var invalid = baseline; mutate(&invalid)
                try expectTrue(invalid.actorExtensionEvidenceProblem() != nil)
                try expectThrows { _ = try pwRunnerEncodeJSON(invalid) }
            }
        }
        tk.run("equipment failure cannot coexist with scheduled collections and a preparation refusal cannot follow launch") {
            let document = try actorShapeDocuments()[0]
            let baseline = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: document))
            var bad = baseline
            bad.actors![0].equipment!.execution.status = "inspection_failed"
            bad.actors![0].equipment!.execution.reason = "inspection_deadline"
            bad.actors![0].equipment!.execution.eligible = false
            try expectTrue(bad.actorExtensionEvidenceProblem() != nil)
            try expectThrows { _ = try pwRunnerEncodeJSON(bad) }
            bad = baseline
            bad.preparation_failure = PWRunnerPreparationFailure(stage: "equipment", code: "equipment_binding_refused")
            try expectTrue(bad.actorExtensionEvidenceProblem() != nil)
            try expectThrows { _ = try pwRunnerEncodeJSON(bad) }
        }
    }
}

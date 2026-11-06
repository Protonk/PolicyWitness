import Darwin
import Foundation
@testable import PWRunnerCore

/*
 * ActorReplyTests — the actor form through the production orchestrator with
 * the shipped worker and validator: the principal request from the shared
 * corpus runs against a test-owned file, and the reply is assembled, encoded
 * under the reply invariants and decoded again. Records are checked against
 * their owners: each actor's own process and publications, the host's
 * custody and transfer observations, the validator's verdicts per phase.
 */

private func repoRoot() -> URL {
    URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent()
}
private func equipment(_ name: String) -> String {
    let app = ProcessInfo.processInfo.environment["PW_APP_DIR"] ?? repoRoot().appendingPathComponent("dist/PolicyWitness.app").path
    return app + "/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/" + name
}

private func actorServiceBundle() -> URL {
    URL(fileURLWithPath: equipment("pw-probe-runner")).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
}

private func checkedActorSchedule(_ source: ActorScheduleInput, plan: ActorPlan) throws -> (ActorScheduleOutcome, ActorEquipmentPreparation) {
    let equipment = ActorEquipmentPreparation.bind(bundleURL: actorServiceBundle(), actors: plan.actors.map {
        ActorEquipmentRequest(actorID: $0.id, index: $0.index, requested: $0.equipment, requiredEntitlements: $0.requiredEntitlements)
    })
    try expectNil(equipment.failure, "signed equipment refused")
    var input = source
    input.didSetUp = { index, pid in equipment.inspect(actorIndex: index, pid: pid, ownershipConfirmed: true) }
    return (ActorScheduler.run(input) { _, _, _ in }, equipment)
}
private func attachObservedEquipment(_ reply: inout PWRunnerRunResult, _ equipment: ActorEquipmentPreparation, _ outcome: ActorScheduleOutcome) {
    reply.equipment_inventory = equipment.inventory; reply.equipment_bindings = equipment.bindings
    reply.equipment_entitlements = equipment.entitlements
    for index in outcome.actors.indices {
        if let failure = outcome.actors[index].equipmentFailure, equipment.actors[index].execution.status == "matched" {
            equipment.actors[index].execution.status = "inspection_failed"
            equipment.actors[index].execution.reason = failure; equipment.actors[index].execution.eligible = false
        }
        if equipment.actors[index].execution.status == "unobserved", outcome.actors[index].pid != nil {
            equipment.actors[index].execution.reason = outcome.actors[index].equipmentFailure ?? "setup_unavailable"
        }
        reply.actors?[index].equipment = equipment.actors[index]
    }
}

private func corpusRequest(_ id: String, effect: String) throws -> PWRunnerRunSpec {
    let url = repoRoot().appendingPathComponent("tests/fixtures/request_contract/examples.json")
    let corpus = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [[String: Any]]
    let example = corpus.first { $0["id"] as! String == id }!
    let encoded = try JSONSerialization.data(withJSONObject: example["request"]!)
    let text = String(decoding: encoded, as: UTF8.self).replacingOccurrences(of: "$EFFECT", with: effect)
    return try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: Data(text.utf8))
}

private func freshEffect() throws -> String {
    let dir = FileManager.default.temporaryDirectory.appendingPathComponent("pw-actor-reply-\(getpid())", isDirectory: true)
    try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    let file = dir.appendingPathComponent("effect")
    try Data("reply witness bytes\n".utf8).write(to: file)
    var resolved = [CChar](repeating: 0, count: Int(PATH_MAX))
    guard realpath(file.path, &resolved) != nil else { throw TestFailure(message: "realpath failed") }
    return String(cString: resolved)
}

private func retainActorReply(_ reply: PWRunnerRunResult, _ name: String) throws {
    guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
        throw TestFailure(message: "runner_unit receipt directory required")
    }
    // These tests enter below PWRunnerService. Apply its real post-orchestration
    // enrichment before retaining a public reply for the complete readers.
    var enriched = reply
    enriched.steps = enrichPathDiagnostics(steps: reply.steps)
    try pwRunnerEncodeJSON(enriched).write(to: URL(fileURLWithPath: fixture).deletingLastPathComponent()
        .appendingPathComponent("actor-review-\(name).json"))
}

func runActorReplyTests(_ tk: TestKit) {
    let workerPresent = FileManager.default.isExecutableFile(atPath: equipment("pw-probe-runner"))
    tk.group("actor reply: the principal request through the production orchestrator") {
        tk.run("authority setup failure refuses launch and remains an apparatus failure in the encoded reply") {
            // Occupy the exact authority name with a test-owned empty object.
            // O_EXCL at the real allocation boundary must fail before any actor
            // launches; the scheduler must not unlink this unrelated object.
            let name = "/pw_au_\(getpid())_0"
            let fd = name.withCString { pw_cworker_shm_open_create($0, 0o600) }
            try expectTrue(fd >= 0, "could not create owned collision")
            defer { close(fd); name.withCString { _ = shm_unlink($0) } }
            let parsed = try corpusRequest("actors_redelegation", effect: freshEffect())
            let reply = CWorkerOrchestrator.run(parsed: parsed, policyHash: "", bundleId: "test",
                workerExecutablePath: equipment("pw-probe-runner"), validatorExecutablePath: equipment("sb_api_validator"), equipmentBundleURL: actorServiceBundle())
            try expectTrue(reply.rc != 0)
            try expectTrue(reply.error?.contains("authority setup") == true, reply.error ?? "")
            try expectTrue(reply.actors!.allSatisfy { $0.launch == nil && $0.subprocess == nil && $0.setup_status == "launch_refused" })
            try expectTrue(reply.extension_events!.allSatisfy { !$0.result_published && !$0.call_boundary_observed })
            try expectTrue(reply.resources!.tokens.allSatisfy { $0.status == "unresolved" })
            _ = try pwRunnerEncodeJSON(reply)
            try retainActorReply(reply, "setup")
        }
        tk.run("native issue interrupted before result publication leaves the token unresolved") {
            let parsed = try corpusRequest("actors_redelegation", effect: freshEffect())
            guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "request refused") }
            let translation = try ActorTranslation(plan: plan, parsed: parsed, workerExecutablePaths: Array(repeating: equipment("pw-probe-runner"), count: plan.actors.count))
            var inputs = translation.inputs
            inputs[0].killBeforePublishSlot = 0
            let input = ActorScheduleInput(actors: inputs, applies: plan.actors.map { $0.applies },
                schedule: plan.phases.map { ActorScheduleEntry(phaseIndex: $0.index, actorIndex: $0.actorIndex, visit: $0.visit - 1) },
                authority: translation.authority)
            let (outcome, boundEquipment) = try checkedActorSchedule(input, plan: plan)
            var reply = assembleActorReply(parsed: parsed, plan: plan, translation: translation, outcome: outcome,
                queryPlans: plan.phases.map { _ in [] }, validatorResults: plan.phases.map { _ in nil },
                collectionStatuses: outcome.visits.map { $0.collectionInvoked ? "not_needed" : "not_reached" }, bundleId: "test")
            attachObservedEquipment(&reply, boundEquipment, outcome)
            let event = reply.extension_events!.first { $0.step_id == "a_issue" }!
            try expectTrue(event.call_boundary_observed)
            try expectFalse(event.result_published)
            try expectNil(event.native_result)
            try expectEqual(reply.resources!.tokens[0].status, "unresolved")
            try expectEqual(reply.actors![0].subprocess?.term_signal, Int(SIGKILL))
            _ = try pwRunnerEncodeJSON(reply)
            try retainActorReply(reply, "interrupted")
        }
        tk.run("host delivery survives source death before its transfer result publication") {
            let parsed = try corpusRequest("actors_redelegation", effect: freshEffect())
            guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "request refused") }
            let translation = try ActorTranslation(plan: plan, parsed: parsed, workerExecutablePaths: Array(repeating: equipment("pw-probe-runner"), count: plan.actors.count))
            var inputs = translation.inputs
            inputs[0].killBeforePublishSlot = 1
            let input = ActorScheduleInput(actors: inputs, applies: plan.actors.map { $0.applies },
                schedule: translation.schedule, authority: translation.authority)
            let (outcome, boundEquipment) = try checkedActorSchedule(input, plan: plan)
            var reply = assembleActorReply(parsed: parsed, plan: plan, translation: translation, outcome: outcome,
                queryPlans: plan.phases.map { _ in [] }, validatorResults: plan.phases.map { _ in nil },
                collectionStatuses: outcome.visits.map { $0.collectionInvoked ? "not_needed" : "not_reached" }, bundleId: "test")
            attachObservedEquipment(&reply, boundEquipment, outcome)
            let source = reply.extension_events!.first { $0.step_id == "a_to_b" }!
            try expectFalse(source.result_published)
            try expectEqual(source.status, "unresolved")
            try expectEqual(reply.transfers![0].status, "delivered")
            try expectFalse(reply.transfers![0].source_acknowledged)
            try expectEqual(reply.resources!.deliveries[0].status, "delivered")
            try expectEqual(reply.actors![0].subprocess?.term_signal, Int(SIGKILL))
            try retainActorReply(reply, "transfer-interrupted")
        }
        tk.run("late application remains observed after setup timed out without permitting its phases") {
            let parsed = try corpusRequest("actors_redelegation", effect: freshEffect())
            guard case .success(let plan) = normalizeActorPlan(parsed) else { throw TestFailure(message: "request refused") }
            let translation = try ActorTranslation(plan: plan, parsed: parsed, workerExecutablePaths: Array(repeating: equipment("pw-probe-runner"), count: plan.actors.count))
            var inputs = translation.inputs
            inputs[1].preReadyHangMs = 150
            inputs[1].exitGraceMs = 1000
            var input = ActorScheduleInput(actors: inputs, applies: plan.actors.map { $0.applies },
                schedule: translation.schedule, authority: translation.authority)
            input.setupAllowanceMs = 40
            let (outcome, boundEquipment) = try checkedActorSchedule(input, plan: plan)
            var reply = assembleActorReply(parsed: parsed, plan: plan, translation: translation, outcome: outcome,
                queryPlans: plan.phases.map { _ in [] }, validatorResults: plan.phases.map { _ in nil },
                collectionStatuses: outcome.visits.map { $0.collectionInvoked ? "not_needed" : "not_reached" }, bundleId: "test")
            attachObservedEquipment(&reply, boundEquipment, outcome)
            try expectEqual(reply.actors![1].setup_status, "setup_timeout")
            try expectEqual(reply.actors![1].applied, true)
            try expectEqual(reply.actors![1].application_count, 1)
            try expectTrue(reply.phases.filter { $0.actor_id == "B" }.allSatisfy { !$0.arrival_observed })
            try retainActorReply(reply, "late-setup")
        }
        tk.run("the corpus's principal request runs, assembles, encodes and decodes") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let effect = try freshEffect()
            let parsed = try corpusRequest("actors_redelegation", effect: effect)
            try expectTrue(parsed.isActorForm)
            try expectNil(CWorkerOrchestrator.admissionFailure(for: parsed))
            try expectNil(requestMeaningFailure(parsed))
            let reply = CWorkerOrchestrator.run(parsed: parsed, policyHash: "", bundleId: "test",
                workerExecutablePath: equipment("pw-probe-runner"), validatorExecutablePath: equipment("sb_api_validator"), equipmentBundleURL: actorServiceBundle())
            try expectEqual(reply.execution_form, "actors")
            try expectNil(reply.policy_sha256)
            try expectNil(reply.policy_format)
            try expectNil(reply.runner_subprocess)
            // Actors: three distinct processes, the apply actors applied once with
            // their own hashes, the unapplied actor without an application claim.
            guard let actors = reply.actors, actors.count == 3 else { throw TestFailure(message: "expected three actor records") }
            try expectEqual(actors.map { $0.actor_id }, ["A", "B", "C"])
            try expectEqual(actors.map { $0.mode }, ["unapplied", "apply", "apply"])
            try expectEqual(actors.map { $0.setup_status }, ["unapplied_declared", "applied", "applied"])
            try expectEqual(actors.map { $0.application_count }, [0, 1, 1])
            try expectEqual(actors.map { $0.applied }, [nil, true, true])
            try expectEqual(Set(actors.compactMap { $0.launch?.pid }).count, 3)
            try expectTrue(actors.allSatisfy { $0.launch?.parent_pid == Int(getpid()) })
            try expectTrue(actors.allSatisfy { $0.launch?.inherited_descriptors == [0, 3, 4, 5] })
            for actor in actors.dropFirst() {
                try expectEqual(actor.policy_sha256, try computePolicyHash(parsed.actors![actor.index].sandbox.policy!))
                try expectEqual(actor.policy_received_sha256, actor.policy_sha256)
            }
            try expectEqual(actors[0].policy_received_sha256, sha256Hex(Data()))
            try expectTrue(actors.allSatisfy { $0.subprocess?.disposition != nil && $0.subprocess?.reaped == true })
            try expectEqual(actors.map { $0.visits }, [[3, 9], [1, 4, 5, 8], [2, 6, 7]])
            // Phases carry their actor and visit; every phase completed.
            try expectEqual(reply.phases.map { $0.phase_id }, ["b_before", "c_before", "initial_supply", "b_consume", "b_redelegate", "c_consume", "c_effect", "b_cleanup", "effect"])
            try expectEqual(reply.phases.map { $0.actor_id }, ["B", "C", "A", "B", "B", "C", "C", "B", "A"])
            try expectEqual(reply.phases.map { $0.actor_visit }, [1, 1, 1, 2, 3, 2, 3, 4, 2])
            try expectTrue(reply.phases.allSatisfy { $0.arrival_observed && $0.completion_observed })
            try expectEqual(reply.phases.map { $0.collection_status }, ["collected", "collected", "not_needed", "not_needed", "collected", "not_needed", "collected", "not_needed", "collected"])
            try expectTrue(reply.phases.allSatisfy { ($0.ordering?.protocol_violations ?? ["missing"]).isEmpty })
            // Ordinary steps name their actor and their verdicts came from the live actor.
            try expectEqual(reply.steps.map { $0.step_id }, ["b_read_before", "c_read_before", "b_read_after", "c_read_after", "effect"])
            try expectEqual(reply.steps.map { $0.actor_id }, ["B", "C", "B", "C", "A"])
            for step in reply.steps {
                let actor = actors.first { $0.actor_id == step.actor_id }!
                try expectEqual(step.sandbox_check.pid, actor.launch?.pid, step.step_id)
                try expectEqual(step.sandbox_check.result_source, "validator", step.step_id)
                try expectEqual(step.comparison?.order, "query_first", step.step_id)
            }
            try expectEqual(reply.steps[0].sandbox_check.outcome, "deny")
            try expectEqual(reply.steps[1].sandbox_check.outcome, "deny")
            try expectEqual(reply.steps[0].attempt.outcome, AttemptOutcome.readFailed)
            // Events for every extension action, with the acting actor and family.
            let events = reply.extension_events ?? []
            try expectEqual(events.map { $0.step_id }, ["a_issue", "a_to_b", "b_consume_first", "b_issue", "b_to_c", "c_consume_second", "c_release", "b_release"])
            try expectEqual(events.map { $0.actor_id }, ["A", "A", "B", "B", "B", "C", "C", "B"])
            try expectTrue(events.allSatisfy { $0.family == "file" && $0.result_published })
            let aIssue = events[0]
            try expectEqual(aIssue.status, "returned")
            try expectEqual(aIssue.native_nonnull, true)
            try expectEqual(aIssue.target, effect)
            try expectEqual(aIssue.extension_class, "com.apple.app-sandbox.read")
            try expectTrue((aIssue.token_length ?? 0) > 0)
            try expectEqual(events[1].status, "delivered")
            try expectEqual(events[1].delivery_ref, "db")
            try expectFalse(events[1].call_boundary_observed)
            try expectEqual(events[2].status, "returned")
            try expectEqual(events[2].delivery_ref, "db")
            // Transfers and resources join the request's references to the
            // host's observations.
            guard let transfers = reply.transfers, let resources = reply.resources else { throw TestFailure(message: "missing transfer or resource tables") }
            try expectEqual(transfers.map { $0.delivery_ref }, ["db", "dc"])
            try expectEqual(transfers.map { $0.token_ref }, ["ta", "tb"])
            try expectEqual(transfers[0].status, "delivered")
            try expectTrue(transfers[0].recipient_acknowledged && transfers[0].source_acknowledged && transfers[0].equality == "equal")
            try expectEqual(resources.tokens.map { $0.token_ref }, ["ta", "tb"])
            try expectEqual(resources.tokens[0].status, "issued")
            try expectEqual(resources.tokens.map { $0.last_use_step_id }, ["a_to_b", "b_to_c"])
            try expectEqual(resources.deliveries.map { $0.delivery_ref }, ["db", "dc"])
            try expectEqual(resources.deliveries[0].status, "delivered")
            try expectEqual(resources.deliveries[0].delivered_length, resources.tokens[0].token_length)
            try expectEqual(resources.handles.map { $0.handle_ref }, ["hb", "hc"])
            try expectEqual(resources.handles.map { $0.release_step_id }, ["b_release", "c_release"])
            try expectTrue(resources.handles.allSatisfy { $0.release_attempted || $0.status != "produced" })
            // The chain's kernel answers are read, not assumed: a usable chain makes
            // B's and C's later reads succeed; any refusal is recorded as such.
            let bIssued = events[3].native_nonnull == true
            try expectEqual(resources.tokens[1].status, bIssued ? "issued" : "null")
            try expectEqual(transfers[1].status, bIssued ? "delivered" : "custody_unavailable")
            try expectEqual(reply.normalized_outcome, NormalizedOutcome.finished, reply.error ?? "")
            try expectEqual(reply.rc, 0)
            // Encode under the reply invariants and decode again.
            let data = try pwRunnerEncodeJSON(reply)
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
            try expectEqual(decoded.actors?.map { $0.actor_id }, ["A", "B", "C"])
            try expectEqual(decoded.phases.map { $0.actor_visit }, reply.phases.map { $0.actor_visit })
            try expectEqual(decoded.transfers?.count, 2)
            let object = try JSONSerialization.jsonObject(with: data) as! [String: Any]
            try expectNil(object["policy_sha256"])
            try expectNil(object["runner_subprocess"])
            try expectEqual(object["execution_form"] as? String, "actors")
            try retainActorReply(reply, "complete")
            var bad = reply
            bad.extension_events![0].native_nonnull = false
            try expectEqual(bad.actorExtensionEvidenceProblem(), "issue nonnull disagrees with native result")
            bad = reply
            bad.resources!.tokens[0].status = "null"
            try expectEqual(bad.actorExtensionEvidenceProblem(), "token status contradicts issue")
            bad = reply
            bad.resources!.handles[0].native_handle = 999_999
            try expectEqual(bad.actorExtensionEvidenceProblem(), "handle status or value contradicts consume")
            bad = reply
            bad.transfers![0].recipient_acknowledged = false
            try expectEqual(bad.actorExtensionEvidenceProblem(), "delivered transfer lacks custody, copy or recipient acknowledgement")
            bad = reply
            bad.transfers = []
            try expectEqual(bad.actorExtensionEvidenceProblem(), "delivery claims host observation without transfer")
            bad = reply
            bad.resources!.deliveries[0].status = "not_reached"
            try expectEqual(bad.actorExtensionEvidenceProblem(), "delivery projection contradicts host transfer")
            bad = reply
            bad.resources!.deliveries[0].equality = "unequal"
            try expectEqual(bad.actorExtensionEvidenceProblem(), "delivery projection contradicts host transfer")
            bad = reply
            bad.extension_events![2].delivery_ref = "dc"
            bad.resources!.handles[0].delivery_ref = "dc"
            try expectEqual(bad.actorExtensionEvidenceProblem(), "consume delivery recipient/order")
            bad = reply
            bad.extension_events![1].token_ref = "absent"
            bad.resources!.deliveries[0].token_ref = "absent"
            bad.transfers![0].token_ref = "absent"
            try expectEqual(bad.actorExtensionEvidenceProblem(), "transfer token owner/order")
            bad = reply
            bad.resources!.tokens.append(resources.tokens[0])
            try expectEqual(bad.actorExtensionEvidenceProblem(), "resource and transfer references must be unique")
            bad = reply
            bad.transfers!.append(transfers[0])
            try expectEqual(bad.actorExtensionEvidenceProblem(), "resource and transfer references must be unique")
            bad = reply
            bad.resources!.handles[0].release_attempted = false
            try expectEqual(bad.actorExtensionEvidenceProblem(), "handle release projection contradicts event")
            bad = reply
            bad.resources!.handles[0].raw_equal_handles = ["hc"]
            try expectEqual(bad.actorExtensionEvidenceProblem(), "handle equality projection contradicts native handles")
        }
        tk.run("a bare deny-default actor and a failed setup are reported per actor without a singular projection") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let effect = try freshEffect()
            let text = """
            {"schema_version": \(PWContract.requestSchema), "specimen_id": "actors-failure",
             "actors": [{"actor_id": "good", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1)(deny default)"}}},
                        {"actor_id": "broken", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1)(bogus"}}}],
             "phases": [{"phase_id": "g", "actor_id": "good", "actions": [{"step_id": "read", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "\(effect)"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "\(effect)"}}]},
                        {"phase_id": "b", "actor_id": "broken", "actions": [{"step_id": "never", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "\(effect)"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "\(effect)"}}]}]}
            """
            let parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: Data(text.utf8))
            let reply = CWorkerOrchestrator.run(parsed: parsed, policyHash: "", bundleId: nil,
                workerExecutablePath: equipment("pw-probe-runner"), validatorExecutablePath: equipment("sb_api_validator"), equipmentBundleURL: actorServiceBundle())
            try expectEqual(reply.normalized_outcome, NormalizedOutcome.runnerFailed)
            try expectTrue(reply.error?.hasPrefix("actor broken:") == true, reply.error ?? "")
            let actors = reply.actors ?? []
            try expectEqual(actors.map { $0.setup_status }, ["applied", "setup_failed"])
            try expectEqual(actors[1].applied, false)
            try expectEqual(actors[1].subprocess?.worker_evidence?.failure?.operation, 5)
            try expectEqual(reply.phases.map { $0.completion_observed }, [true, false])
            try expectEqual(reply.steps.map { $0.attempt.result_source }, ["worker", "synthetic"])
            try expectEqual(reply.steps[0].attempt.outcome, AttemptOutcome.readFailed)
            try expectEqual(reply.steps[0].sandbox_check.outcome, "deny")
            _ = try pwRunnerEncodeJSON(reply)
            try retainActorReply(reply, "failed-setup")
        }
    }
}

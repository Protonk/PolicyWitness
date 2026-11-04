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

func runActorReplyTests(_ tk: TestKit) {
    let workerPresent = FileManager.default.isExecutableFile(atPath: equipment("pw-probe-runner"))
    tk.group("actor reply: the principal request through the production orchestrator") {
        tk.run("the corpus's principal request runs, assembles, encodes and decodes") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let effect = try freshEffect()
            let parsed = try corpusRequest("actors_redelegation", effect: effect)
            try expectTrue(parsed.isActorForm)
            try expectNil(CWorkerOrchestrator.admissionFailure(for: parsed))
            try expectNil(requestMeaningFailure(parsed))
            let reply = CWorkerOrchestrator.run(parsed: parsed, policyHash: "", bundleId: "test",
                workerExecutablePath: equipment("pw-probe-runner"), validatorExecutablePath: equipment("sb_api_validator"))
            try expectEqual(reply.execution_form, "actors")
            try expectNil(reply.policy_sha256)
            try expectNil(reply.policy_format)
            try expectNil(reply.runner_subprocess)
            try expectNil(reply.extensions)
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
            try expectEqual(reply.normalized_outcome, NormalizedOutcome.ok, reply.error ?? "")
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
                workerExecutablePath: equipment("pw-probe-runner"), validatorExecutablePath: equipment("sb_api_validator"))
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
        }
    }
}

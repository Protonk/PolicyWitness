import Darwin
import Foundation
@testable import PWRunnerCore

private func execReaderCases(_ section: String) throws -> [[String: Any]] {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let document = try JSONSerialization.jsonObject(with: Data(contentsOf:
        root.appendingPathComponent("tests/fixtures/contract/exec_observation.json"))) as! [String: Any]
    return document[section] as! [[String: Any]]
}

func execObservationShapeDocuments() throws -> [[String: Any]] {
    try execReaderCases("valid").map { item in
        var reply = try replyFixture()
        reply.steps[0].attempt = try pwRunnerDecodeJSON(PWRunnerAttemptResult.self,
            from: JSONSerialization.data(withJSONObject: item["attempt"]!))
        return try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(reply)) as! [String: Any]
    }
}

func runExecObservationTests(_ tk: TestKit) {
    tk.group("exec observation readers and publication") {
        tk.run("independent native combinations retain cleanup separate from leader status") {
            for item in try execReaderCases("valid") {
                let data = try JSONSerialization.data(withJSONObject: item["attempt"]!)
                let attempt = try pwRunnerDecodeJSON(PWRunnerAttemptResult.self, from: data)
                try expectNil(attempt.execObservationEvidenceProblem(), item["name"] as! String)
                var reply = try replyFixture()
                reply.steps[0].attempt = attempt
                let comparison = computeComparison(sandboxCheck: reply.steps[0].sandbox_check, attempt: attempt)
                try expectEqual(comparison.observation, "succeeded", item["name"] as! String)
                try expectEqual(comparison.observation_basis, "spawned_child", item["name"] as! String)
                let encoded = try pwRunnerEncodeJSON(reply)
                let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: encoded)
                try expectEqual(decoded.steps[0].attempt.child_exit_code, attempt.child_exit_code)
                try expectEqual(decoded.steps[0].attempt.exec_observation?.cleanup.state,
                                attempt.exec_observation?.cleanup.state)
                let submitted = item["attempt"] as! [String: Any]
                if submitted["exec_observation"] == nil || submitted["exec_observation"] is NSNull {
                    try expectNil(decoded.steps[0].attempt.exec_observation, "absence cannot become not_requested")
                    let raw = try JSONSerialization.jsonObject(with: encoded) as! [String: Any]
                    let steps = raw["steps"] as! [[String: Any]]
                    try expectNil((steps[0]["attempt"] as! [String: Any])["exec_observation"],
                                  "absence cannot become not_requested")
                }
            }
        }
        tk.run("malformed present facts fail typed decode or ordinary reply integrity") {
            for item in try execReaderCases("invalid") {
                var raw = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(try replyFixture())) as! [String: Any]
                var steps = raw["steps"] as! [[String: Any]]
                steps[0]["attempt"] = item["attempt"]
                raw["steps"] = steps
                var refused = false
                do { _ = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: raw)) }
                catch { refused = true }
                try expectTrue(refused, item["name"] as! String)
                if let attempt = try? pwRunnerDecodeJSON(PWRunnerAttemptResult.self,
                    from: JSONSerialization.data(withJSONObject: item["attempt"]!)) {
                    var reply = try replyFixture(); reply.steps[0].attempt = attempt
                    let degraded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerReplyData(reply))
                    try expectEqual(degraded.normalized_outcome, "runner_reporting_failed", item["name"] as! String)
                    try expectTrue(degraded.steps.allSatisfy { $0.comparison == nil })
                }
            }
        }
        tk.run("C slot completion gates payload and malformed publication degrades") {
            guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
                throw TestFailure(message: "missing worker lifecycle fixture")
            }
            for mode in ["exec_payload_valid", "exec_payload_unpublished", "exec_payload_bad_marker", "exec_payload_bad_enum"] {
                let input = CWorkerInput(workerExecutablePath: path, policy: mode,
                    slots: [CWorkerSlotInput(stepId: "s", attemptKind: .execSpawn, target: "/usr/bin/true")],
                    sentinelTimeoutMs: 500, exitGraceMs: 500)
                guard case .success(let out) = runCWorker(input), let slot = out.slots.first else {
                    throw TestFailure(message: "fixture driver failed for \(mode)")
                }
                if mode == "exec_payload_unpublished" {
                    try expectFalse(slot.completed)
                    try expectNil(slot.execObservation)
                    try expectNil(slot.execObservationProblem)
                    try expectNil(slot.childPid)
                    try expectNil(slot.childStdout)
                    try expectEqual(out.termSignal, SIGKILL)
                } else {
                    try expectTrue(slot.completed)
                    let probe = PWRunnerProbeStep(step_id: "s", sandbox_check: PWRunnerSandboxCheck(operation: "process-exec",
                        filter: PWRunnerSandboxFilter(kind: "path", value: "/usr/bin/true")),
                        attempt: PWRunnerAttempt(kind: "exec", action: "spawn", target: "/usr/bin/true"))
                    let disposition = resolveDisposition(out, plan: [probe])
                    let phase = constructedPhase(out, ids: ["s"])
                    let reply = PWRunnerRunResult(specimen_id: mode, rc: 0, normalized_outcome: "ok", pid: Int(out.workerPid),
                        policy_format: "sbpl", sandboxed_after_apply: true,
                        steps: buildStepResults(probePlan: [probe], queryPlan: planValidatorQueries([probe]), workerOutput: out,
                            validatorOutput: nil, ordering: phase.ordering, disposition: disposition),
                        runner_subprocess: buildWorkerSubprocess(out, disposition: disposition), phases: [phase])
                    let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerReplyData(reply))
                    if mode == "exec_payload_valid" {
                        try expectEqual(decoded.steps[0].attempt.exec_observation?.reap.last_wait.rc, 4242)
                        try expectEqual(decoded.steps[0].attempt.exec_observation?.cleanup.state, "not_requested")
                    } else {
                        try expectEqual(decoded.normalized_outcome, "runner_reporting_failed")
                        try expectContains(decoded.reporting_failure?.diagnostic ?? "", "malformed completed exec payload")
                        try expectNil(decoded.steps[0].comparison)
                    }
                }
            }
        }
    }
}

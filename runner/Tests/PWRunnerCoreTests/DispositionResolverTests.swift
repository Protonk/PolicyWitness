import Darwin
import Foundation
@testable import PWRunnerCore

// Disposition record (controller/DISPOSITION-RECORD-PLAN.md, areas B, C and D;
// contract in tests/FAILURE-PROPAGATION-CONTRACT.md, "Worker disposition record").
//
// Three kinds of control. Fixture observations drive the production driver
// against the ABI fixture (no sandbox is applied, so no policy cause is
// claimed) and check the account the resolver derives from real publications:
// C2 (started attempt, two slots) and C5 (skip_publication's real D5 conflict).
// Constructed cases feed the resolver directly (B2, B3, B5, B6, C3, C4). The
// mirror group compares the Swift spellings with tests/lib/lifecycle_contract.py
// and requires the resolver to reproduce every hand-reviewed example row of that
// module, independently of the Python oracle that also evaluates them.

private func slot(_ id: String, completed: Bool, rc: Int32 = 0) -> CWorkerSlotResult {
    CWorkerSlotResult(stepId: id, rc: rc, errnoVal: 0, observedPath: completed ? "fixture-observation" : nil,
                      error: nil, completed: completed)
}

private func progressWord(_ op: UInt32, _ phase: UInt32, index: UInt32? = nil) -> PWWorkerProgress {
    let item: UInt32 = index.map { $0 + 1 } ?? 0
    return PWWorkerProgress(raw: (op << 24) | (phase << 20) | item, operation: op, phase: phase, index: index)
}

private func evidence(progress: PWWorkerProgress?) -> PWWorkerEvidence {
    PWWorkerEvidence(abi_identity: PWShmLayout.abiIdentityHex, progress: progress, failure_publication: 0,
                     failure_state: "absent", failure: nil, readiness: nil,
                     diagnostic: PWWorkerDiagnostic(state: 0, status: "absent", length: nil, text: nil))
}

// Constructed output in the style of HostOutcomeClassifierTests.workerOut, extended
// with slots, a progress word and the three collection facts.
private func constructed(slots: [CWorkerSlotResult], progress: PWWorkerProgress?,
                         stop: String = "done", exitCode: Int32? = 0, termSignal: Int32? = nil,
                         request: PWRunnerTerminationRequest? = nil, reaped: Bool = true,
                         basis: String = "after_confirmed_reap") -> CWorkerOutput {
    var out = CWorkerOutput(
        workerPid: 4242, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0,
        done: stop == "done", exitCode: exitCode, termSignal: termSignal, slots: slots,
        pollStopReason: stop, exitRequested: true, terminationRequest: request, reaped: reaped,
        waitErrors: [], workerEvidence: evidence(progress: progress))
    out.cleanupTrigger = PWDisposition.triggerForStop[stop] ?? stop
    out.graceEnd = request != nil ? "exhausted" : (stop == "child_reaped" ? "not_entered" : "reaped_during_grace")
    out.collectionBasis = basis
    return out
}

private func probe(_ id: String, kind: String = "file", action: String = "open_read") -> PWRunnerProbeStep {
    PWRunnerProbeStep(
        step_id: id,
        sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                                            filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
        attempt: PWRunnerAttempt(kind: kind, action: action, target: "/etc/hosts"))
}

// Real driver against the ABI fixture with a multi-slot plan. Cleanup follows
// CWorkerLifecycleTests: the test owns any child the driver left unreaped and
// never rewrites the driver's observations.
private func dispositionFixture(_ mode: String, stepIds: [String]) throws -> CWorkerOutput {
    guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
          FileManager.default.isExecutableFile(atPath: path) else {
        throw TestFailure(message: "required PW_LIFECYCLE_WORKER_FIXTURE missing; run tests/run.sh --suite runner_unit")
    }
    let result = runCWorker(CWorkerInput(
        workerExecutablePath: path, policy: mode,
        slots: stepIds.map { CWorkerSlotInput(stepId: $0, attemptKind: .fileOpenRead, target: "/fixture") },
        sentinelTimeoutMs: 100, exitGraceMs: 500))
    guard case .success(let out) = result else {
        throw TestFailure(message: "fixture driver failed: \(result)")
    }
    var status: Int32 = 0
    let first = Darwin.waitpid(out.workerPid, &status, WNOHANG)
    if first != out.workerPid && !(first == -1 && errno == ECHILD) {
        guard first == 0 || (first == -1 && errno == EINTR) else {
            throw TestFailure(message: "fixture cleanup wait failed: \(errno)")
        }
        let rc = Darwin.kill(out.workerPid, SIGKILL)
        guard rc == 0 || errno == ESRCH else {
            throw TestFailure(message: "fixture cleanup kill failed: \(errno)")
        }
        var cleaned = false
        for _ in 0..<100 {
            let result = Darwin.waitpid(out.workerPid, &status, WNOHANG)
            if result == out.workerPid || (result == -1 && errno == ECHILD) {
                cleaned = true
                break
            }
            usleep(10_000)
        }
        try expectTrue(cleaned, "test-owned fixture was not reaped")
    }
    return out
}

private func encodedObject<T: Encodable>(_ value: T) throws -> [String: Any] {
    let bytes = try pwRunnerEncodeJSON(value)
    guard let object = try JSONSerialization.jsonObject(with: bytes) as? [String: Any] else {
        throw TestFailure(message: "encoded value is not a JSON object")
    }
    return object
}

private func claim(_ record: PWDispositionRecord, _ name: String) -> PWDispositionClaim? { record.questions[name] }
private func stepClaim(_ record: PWDispositionRecord, _ index: Int, _ name: String) -> PWDispositionClaim? {
    record.steps.indices.contains(index) ? record.steps[index].questions[name] : nil
}

// MARK: - Python mirror

private func pythonExport(_ root: URL, model: Bool = false) throws -> [String: Any] {
    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
    process.arguments = [root.appendingPathComponent(model ? "tests/lib/lifecycle_oracle.py" : "tests/lib/lifecycle_contract.py").path,
                         model ? "--model-json" : "--json"]
    let pipe = Pipe()
    process.standardOutput = pipe
    process.standardError = pipe
    try process.run()
    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    process.waitUntilExit()
    guard process.terminationStatus == 0,
          let object = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
        throw TestFailure(message: "lifecycle_contract.py --json failed: \(String(decoding: data, as: UTF8.self).prefix(400))")
    }
    return object
}

private func strings(_ any: Any?) -> [String] { (any as? [String]) ?? [] }
private func mapping(_ any: Any?) -> [String: String] { (any as? [String: String]) ?? [:] }

/// A CWorkerOutput and plan from an example row's normalized observations.
private func inputs(from observations: [String: Any]) -> (CWorkerOutput, [PWRunnerProbeStep]) {
    func string(_ key: String) -> String? {
        guard let value = observations[key] as? String, value != "<missing>" else { return nil }
        return value
    }
    func int32(_ key: String) -> Int32? { (observations[key] as? NSNumber).map { Int32(truncating: $0) } }
    let reaped = observations["reaped"] as? Bool
    let exitRequested = observations["exit_requested"] as? Bool
    var request: PWRunnerTerminationRequest? = nil
    if let object = observations["termination_request"] as? [String: Any] {
        request = PWRunnerTerminationRequest(signal: Int32(truncating: object["signal"] as! NSNumber),
                                             rc: Int32(truncating: object["rc"] as! NSNumber),
                                             errno: (object["errno"] as? NSNumber).map { Int32(truncating: $0) })
    }
    var progress: PWWorkerProgress? = nil
    if let word = observations["progress"] as? [String: Any] {
        progress = PWWorkerProgress(raw: UInt32(truncating: word["raw"] as! NSNumber),
                                    operation: UInt32(truncating: word["operation"] as! NSNumber),
                                    phase: UInt32(truncating: word["phase"] as! NSNumber),
                                    index: (word["index"] as? NSNumber).map { UInt32(truncating: $0) })
    }
    let steps = (observations["steps"] as? [[String: Any]]) ?? []
    var plan: [PWRunnerProbeStep] = []
    var slots: [CWorkerSlotResult] = []
    for (i, step) in steps.enumerated() {
        let supported = step["supported"] as? Bool ?? true
        plan.append(probe("step\(i)", kind: supported ? "file" : "bogus", action: supported ? "open_read" : "nope"))
        switch step["slot"] as? String {
        case "completed"?: slots.append(slot("step\(i)", completed: true))
        case "incomplete"?: slots.append(slot("step\(i)", completed: false))
        default: break
        }
    }
    var out = CWorkerOutput(
        workerPid: 4242, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0,
        done: string("poll_stop_reason") == "done", exitCode: int32("exit_code"), termSignal: int32("term_signal"),
        slots: slots, pollStopReason: string("poll_stop_reason"), exitRequested: exitRequested,
        terminationRequest: request, reaped: reaped, waitErrors: [], workerEvidence: evidence(progress: progress))
    out.cleanupTrigger = string("cleanup_trigger")
    out.graceEnd = string("grace_end")
    out.collectionBasis = string("collection_basis")
    return (out, plan)
}

/// The comparable part of a claim: state, answer, value and reason (not the basis
/// or the issue index, which the oracle checks separately).
private func comparable(_ claim: PWDispositionClaim) throws -> [String: Any] {
    var object = try encodedObject(claim)
    object.removeValue(forKey: "basis")
    object.removeValue(forKey: "issue")
    return object
}

func runDispositionResolverTests(_ tk: TestKit) {
    tk.group("disposition observations (fixture, no sandbox)") {
        tk.run("C2: started attempt with two slots claims started_without_result then not_reached") {
            let out = try dispositionFixture("started_attempt", stepIds: ["first", "second"])
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            try expectEqual(out.exitCode, 0)
            try expectNil(out.terminationRequest, "a voluntary exit during grace needs no kill")
            try expectEqual(out.reaped, true)
            try expectEqual(out.cleanupTrigger, "deadline_expiry")
            try expectEqual(out.graceEnd, "reaped_during_grace")
            try expectEqual(out.collectionBasis, "after_confirmed_reap")
            try expectFalse(out.slots[0].completed)
            try expectEqual(out.slots[0].rc, Int32(0), "placeholder rc; the poison 12345 is never read")
            let plan = [probe("first"), probe("second")]
            let record = resolveDisposition(out, plan: plan)
            try expectEqual(claim(record, "final_status")?.answer, "exit_code")
            try expectEqual(claim(record, "progress_association")?.answer, "step_index")
            try expectEqual(stepClaim(record, 0, "step_boundary_reached")?.answer, "reached")
            try expectEqual(stepClaim(record, 0, "step_result_published")?.answer, "unpublished")
            try expectEqual(stepClaim(record, 1, "step_boundary_reached")?.answer, "not_reached")
            try expectEqual(stepClaim(record, 1, "step_result_published")?.answer, "unpublished")
            try expectEqual(record.issues.count, 0)
            try expectEqual(record.steps.map(lifecycleSummary), ["started_without_result", "not_reached"])
            let steps = buildStepResults(probePlan: plan, queryPlan: planValidatorQueries(plan), workerOutput: out,
                                         validatorOutput: nil, ordering: nil, disposition: record)
            try expectEqual(steps.map { $0.attempt.lifecycle?.summary }, ["started_without_result", "not_reached"])
            try expectEqual(steps.map { $0.attempt.outcome }, [AttemptOutcome.notRunWorkerDied, AttemptOutcome.notRunWorkerDied])
            try expectEqual(steps.map { $0.attempt.missing_reason }, ["slot_incomplete", "slot_incomplete"])
            try expectTrue(steps[0].comparison?.limitations.contains("attempt:started_without_result") == true)
            try expectTrue(steps[1].comparison?.limitations.contains("attempt:not_reached") == true)
            let sub = buildWorkerSubprocess(out, disposition: record)
            try expectEqual(sub.partial_steps, true)
            try expectEqual(sub.disposition, record)
        }
        tk.run("C5: skip_publication's real publication conflict is a scoped D5 issue") {
            let out = try dispositionFixture("skip_publication", stepIds: ["first", "second"])
            try expectTrue(out.done)
            try expectEqual(out.exitCode, 0)
            try expectEqual(out.collectionBasis, "after_confirmed_reap")
            try expectTrue(out.slots[0].completed)
            try expectFalse(out.slots[1].completed)
            try expectEqual(out.slots[1].rc, Int32(0), "the poison is never read without completed publication")
            let record = resolveDisposition(out, plan: [probe("first"), probe("second")])
            try expectEqual(stepClaim(record, 0, "step_result_published")?.answer, "published")
            try expectEqual(stepClaim(record, 1, "step_boundary_reached")?.answer, "reached")
            try expectEqual(stepClaim(record, 1, "step_result_published")?.state, "conflicting")
            try expectEqual(record.issues.count, 1)
            try expectEqual(record.issues[0].rule, "D5")
            try expectEqual(record.issues[0].step_index, 1)
            try expectEqual(record.issues[0].observations, ["progress", "slot", "collection_basis"])
            try expectEqual(claim(record, "final_status")?.answer, "exit_code", "the conflict is local to slot 1")
            try expectEqual(record.steps.map(lifecycleSummary), ["completed", "conflicting"])
            // The account encodes normally: a reported conflict is representable evidence.
            let reply = PWRunnerRunResult(specimen_id: "c5", rc: 0, normalized_outcome: NormalizedOutcome.ok, pid: 4242,
                policy_format: "sbpl", sandboxed_after_apply: true,
                steps: buildStepResults(probePlan: [probe("first"), probe("second")],
                                        queryPlan: planValidatorQueries([probe("first"), probe("second")]),
                                        workerOutput: out, validatorOutput: nil,
                                        ordering: buildOrdering(out, validatorOutput: nil, hasQueries: true),
                                        disposition: record),
                runner_subprocess: { var sub = buildWorkerSubprocess(out, disposition: record)
                                     sub.ordering = buildOrdering(out, validatorOutput: nil, hasQueries: true); return sub }())
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(reply))
            try expectEqual(decoded.runner_subprocess?.disposition?.issues.first?.rule, "D5")
        }
    }

    tk.group("disposition interpretation (constructed)") {
        tk.run("ambiguous slot identity cannot select a result or crash the reply join") {
            let out = constructed(slots: [slot("a", completed: true), slot("a", completed: false)], progress: nil)
            let plan = [probe("a")]
            let record = resolveDisposition(out, plan: plan)
            try expectEqual(record.steps[0].slot, "absent")
            try expectEqual(record.steps[0].questions["step_result_published"]?.reason, "slot_unavailable")
            let steps = buildStepResults(probePlan: plan, queryPlan: planValidatorQueries(plan), workerOutput: out,
                validatorOutput: nil, ordering: nil, disposition: record)
            try expectEqual(steps[0].attempt.result_source, "synthetic")
            try expectEqual(steps[0].attempt.missing_reason, "slot_absent")
        }
        tk.run("progress association checks the encoded word and non-indexed operation identity") {
            var mismatched = progressWord(9, 1, index: 0)
            mismatched.raw = progressWord(9, 1, index: 1).raw
            for word in [mismatched, progressWord(8, 2, index: 0)] {
                let out = constructed(slots: [slot("a", completed: false)], progress: word)
                let record = resolveDisposition(out, plan: [probe("a")])
                try expectEqual(record.questions["progress_association"]?.answer, "invalid")
                try expectEqual(record.steps[0].questions["step_boundary_reached"]?.reason, "no_usable_progress")
            }
        }
        tk.run("integrity: claims must cite sufficient observations and retain their values") {
            let out = constructed(slots: [slot("a", completed: true)], progress: progressWord(10, 2),
                                  stop: "sentinel_deadline", exitCode: nil, termSignal: 9,
                                  request: PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil))
            let base = resolveDisposition(out, plan: [probe("a")])
            let mutations: [(String, (inout PWDispositionRecord, inout PWRunnerSubprocess) -> Void)] = [
                ("second status", { _, sub in sub.exit_code = 0 }),
                ("kill return", { _, sub in sub.termination_request = PWRunnerTerminationRequest(signal: 9, rc: -1, errno: nil) }),
                ("kill signal", { _, sub in sub.termination_request = PWRunnerTerminationRequest(signal: 15, rc: 0, errno: nil) }),
                ("kill errno", { _, sub in sub.termination_request = PWRunnerTerminationRequest(signal: 9, rc: 0, errno: EPERM) }),
                ("irrelevant basis", { record, _ in record.questions["final_status"]?.basis = ["exit_requested"] }),
                ("missing reap basis", { record, _ in record.questions["final_status"]?.basis = ["term_signal"] }),
                ("cited progress does not prove the completed slot's boundary", { record, sub in
                    sub.worker_evidence?.progress = progressWord(200, 1)
                    record.questions["progress_association"] = PWDispositionClaim(
                        state: "unresolved", reason: "progress_unrecognized", basis: ["progress"])
                    record.steps[0].questions["step_boundary_reached"]?.basis = ["progress"]
                }),
                ("unobserved basis", { record, sub in
                    sub.worker_evidence = nil
                    record.questions["final_status"]?.basis = ["reaped", "term_signal", "worker_failure"]
                }),
                ("terminal collection without reap", { record, sub in
                    sub.reaped = false; sub.term_signal = nil
                    record.questions["final_status"] = PWDispositionClaim(state: "unresolved", reason: "no_successful_reap")
                }),
                ("invented boundary", { record, sub in
                    sub.worker_evidence?.progress = nil
                    record.steps[0].slot = "incomplete"
                    record.steps[0].questions["step_result_published"] = PWDispositionClaim(
                        state: "supported", answer: "unpublished", basis: ["slot", "collection_basis"])
                }),
                ("invented issue", { record, _ in
                    record.issues = [PWDispositionIssue(kind: "conflict", rule: "D5", question: "step_boundary_reached",
                        step_index: 0, observations: ["progress", "slot", "collection_basis"], detail: "fabricated")]
                    record.steps[0].questions["step_boundary_reached"] = PWDispositionClaim(state: "conflicting", issue: 0)
                }),
            ]
            for (name, mutate) in mutations {
                var record = base
                var sub = buildWorkerSubprocess(out, disposition: base)
                mutate(&record, &sub)
                try expectFalse(dispositionIntegrityProblems(record, subprocess: sub, stepCount: 1).isEmpty, name)
            }
        }
        tk.run("B2: missing progress beside an incomplete slot is unresolved, not not_reached") {
            let out = constructed(slots: [slot("a", completed: false)], progress: nil, stop: "sentinel_deadline",
                                  exitCode: nil, termSignal: 9, request: PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil))
            let record = resolveDisposition(out, plan: [probe("a")])
            try expectEqual(claim(record, "progress_association")?.state, "inapplicable")
            try expectEqual(stepClaim(record, 0, "step_boundary_reached")?.state, "unresolved")
            try expectEqual(stepClaim(record, 0, "step_boundary_reached")?.reason, "no_usable_progress")
            try expectEqual(stepClaim(record, 0, "step_result_published")?.answer, "unpublished")
            try expectEqual(lifecycleSummary(record.steps[0]), "unresolved")
            try expectEqual(buildAttemptResult(step: probe("a"), slot: out.slots[0]).outcome, AttemptOutcome.notRunWorkerDied)
        }
        tk.run("B3: unrecognized progress operation leaves completed results and their boundaries known") {
            let out = constructed(slots: [slot("a", completed: true), slot("b", completed: true)],
                                  progress: progressWord(200, 1, index: 0))
            let record = resolveDisposition(out, plan: [probe("a"), probe("b")])
            try expectEqual(claim(record, "progress_association")?.reason, "progress_unrecognized")
            try expectEqual(record.steps.map(lifecycleSummary), ["completed", "completed"])
            try expectEqual(classify(workerResult: .success(out), validatorResult: nil,
                                     expectedVerdictCount: 0).outcome, NormalizedOutcome.ok)
            let decoded = try pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: pwRunnerEncodeJSON(buildWorkerSubprocess(out)))
            try expectEqual(decoded.worker_evidence?.progress?.operation, 200, "the raw word survives")
            try expectEqual(decoded.partial_steps, false)
        }
        tk.run("B4: a successful kill without a reap leaves final status unresolved") {
            let out = constructed(slots: [slot("a", completed: false)], progress: progressWord(9, 1, index: 0),
                                  stop: "sentinel_deadline", exitCode: nil, termSignal: nil,
                                  request: PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil), reaped: false,
                                  basis: "execution_may_continue")
            let record = resolveDisposition(out, plan: [probe("a")])
            try expectEqual(claim(record, "final_status")?.reason, "no_successful_reap")
            try expectEqual(claim(record, "kill_request_and_result")?.answer, "requested")
            try expectEqual(stepClaim(record, 0, "step_boundary_reached")?.answer, "reached")
            try expectEqual(stepClaim(record, 0, "step_result_published")?.reason, "basis_not_terminal")
        }
        tk.run("B5: an out-of-range progress index invalidates association, not the run") {
            for index: UInt32 in [2, (1 << 20) - 2] {
                let out = constructed(slots: [slot("a", completed: true), slot("b", completed: false)],
                                      progress: progressWord(9, 1, index: index), stop: "sentinel_deadline",
                                      exitCode: nil, termSignal: 9, request: PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil))
                let record = resolveDisposition(out, plan: [probe("a"), probe("b")])
                try expectEqual(claim(record, "progress_association")?.answer, "invalid")
                try expectEqual(stepClaim(record, 0, "step_boundary_reached")?.answer, "reached", "completed slot keeps its boundary")
                try expectEqual(stepClaim(record, 0, "step_result_published")?.answer, "published")
                try expectEqual(stepClaim(record, 1, "step_boundary_reached")?.reason, "no_usable_progress")
                try expectEqual(stepClaim(record, 1, "step_result_published")?.answer, "unpublished")
            }
            let empty = resolveDisposition(constructed(slots: [], progress: progressWord(9, 1, index: 0)), plan: [])
            try expectEqual(claim(empty, "progress_association")?.answer, "invalid")
            try expectEqual(empty.steps.count, 0)
        }
        tk.run("B6: a completed no-op slot for an unsupported attempt is not a completed requested operation") {
            let out = constructed(slots: [slot("u", completed: true)], progress: progressWord(10, 2))
            let step = probe("u", kind: "bogus", action: "nope")
            let record = resolveDisposition(out, plan: [step])
            try expectEqual(stepClaim(record, 0, "step_requested_operation_applicability")?.answer, "unsupported")
            try expectEqual(stepClaim(record, 0, "step_result_published")?.state, "inapplicable")
            try expectEqual(lifecycleSummary(record.steps[0]), "unsupported")
            try expectEqual(buildAttemptResult(step: step, slot: out.slots[0]).outcome, AttemptOutcome.unsupported)
            try expectEqual(buildWorkerSubprocess(out, disposition: record).partial_steps, false)
        }
        tk.run("C3: reads that can describe different moments do not establish a conflict") {
            let out = constructed(slots: [slot("a", completed: false)], progress: progressWord(9, 2, index: 0),
                                  stop: "sentinel_deadline", exitCode: nil, termSignal: nil,
                                  request: PWRunnerTerminationRequest(signal: 9, rc: -1, errno: EPERM), reaped: false,
                                  basis: "execution_may_continue")
            let record = resolveDisposition(out, plan: [probe("a")])
            try expectEqual(stepClaim(record, 0, "step_result_published")?.reason, "basis_not_terminal")
            try expectEqual(record.issues.count, 0)
            var unavailable = out; unavailable.collectionBasis = "unavailable"
            try expectEqual(resolveDisposition(unavailable, plan: [probe("a")]).issues.count, 0)
        }
        tk.run("C4: a stable snapshot with incompatible publications is a scoped conflict") {
            let out = constructed(slots: [slot("a", completed: true), slot("b", completed: false)],
                                  progress: progressWord(9, 2, index: 1))
            let record = resolveDisposition(out, plan: [probe("a"), probe("b")])
            try expectEqual(stepClaim(record, 1, "step_result_published")?.state, "conflicting")
            try expectEqual(record.issues.map { $0.rule }, ["D5"])
            try expectEqual(stepClaim(record, 0, "step_result_published")?.answer, "published")
            try expectEqual(claim(record, "final_status")?.answer, "exit_code")
        }
        tk.run("D1: a reap represented as both exit and signal is a reported conflict, encoded normally") {
            var out = constructed(slots: [slot("a", completed: true)], progress: progressWord(10, 2), stop: "child_reaped",
                                  exitCode: 0, termSignal: 9)
            out.graceEnd = "not_entered"
            let record = resolveDisposition(out, plan: [probe("a")])
            try expectEqual(claim(record, "final_status")?.state, "conflicting")
            try expectEqual(record.issues.map { $0.rule }, ["D1"])
            try expectEqual(stepClaim(record, 0, "step_result_published")?.answer, "published", "the conflict is local")
            try expectEqual(dispositionIntegrityProblems(record, subprocess: buildWorkerSubprocess(out, disposition: record),
                                                         stepCount: 1), [])
            try expectContains(classify(workerResult: .success(out), validatorResult: nil, expectedVerdictCount: 0).error ?? "",
                               "conflicting status representation")
        }
        tk.run("integrity: an assembled claim that contradicts its basis is rejected by the encoder, kept by the degraded reply") {
            let out = constructed(slots: [slot("a", completed: true)], progress: progressWord(10, 2))
            var record = resolveDisposition(out, plan: [probe("a")])
            record.questions["final_status"] = PWDispositionClaim(state: "supported", answer: "signal",
                                                                  value: .integer(9), basis: ["reaped", "term_signal"])
            var sub = buildWorkerSubprocess(out, disposition: record)
            sub.ordering = buildOrdering(out, validatorOutput: nil, hasQueries: true)
            try expectFalse(dispositionIntegrityProblems(record, subprocess: sub, stepCount: 1).isEmpty)
            let reply = PWRunnerRunResult(specimen_id: "invalid", rc: 0, normalized_outcome: NormalizedOutcome.ok, pid: 4242,
                policy_format: "sbpl", sandboxed_after_apply: true,
                steps: buildStepResults(probePlan: [probe("a")], queryPlan: planValidatorQueries([probe("a")]),
                                        workerOutput: out, validatorOutput: nil,
                                        ordering: sub.ordering, disposition: record),
                runner_subprocess: sub)
            do { _ = try pwRunnerEncodeJSON(reply); throw TestFailure(message: "contradicting record accepted") }
            catch is EncodingError { }
            let degraded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerReplyData(reply))
            try expectEqual(degraded.normalized_outcome, NormalizedOutcome.runnerReportingFailed)
            try expectContains(degraded.reporting_failure?.diagnostic ?? "", "contradicts its basis")
            try expectEqual(degraded.runner_subprocess?.disposition?.questions["final_status"]?.answer, "signal",
                            "the degraded reply retains the record as assembled")
            var missing = reply; missing.runner_subprocess?.disposition = nil
            do { _ = try pwRunnerEncodeJSON(missing); throw TestFailure(message: "record omitted at the record version accepted") }
            catch is EncodingError { }
        }
    }

    tk.group("disposition contract mirror (tests/lib/lifecycle_contract.py)") {
        let root = repositoryRoot()
        var export: [String: Any] = [:]
        tk.run("Swift spellings agree with the Python contract module") {
            export = try pythonExport(root)
            try expectEqual(strings(export["claim_states"]), PWDisposition.claimStates)
            try expectEqual(strings(export["run_questions"]), PWDisposition.runQuestions)
            try expectEqual(strings(export["step_questions"]), PWDisposition.stepQuestions)
            try expectEqual(strings(export["cleanup_triggers"]), PWDisposition.cleanupTriggers)
            try expectEqual(strings(export["grace_ends"]), PWDisposition.graceEnds)
            try expectEqual(strings(export["collection_bases"]), PWDisposition.collectionBases)
            try expectEqual(mapping(export["trigger_for_stop"]), PWDisposition.triggerForStop)
            try expectEqual(strings(export["slot_states"]), PWDisposition.slotStates)
            try expectEqual(strings(export["attempt_support"]), PWDisposition.attemptSupport)
            try expectEqual(strings(export["summaries"]), PWDisposition.summaries)
            try expectEqual(mapping(export["limitation_for_summary"]), PWDisposition.limitationForSummary)
            try expectEqual(mapping(export["cause_for_trigger"]), PWDisposition.causeForTrigger)
            try expectEqual(export["not_recorded"] as? String, PWDisposition.notRecorded)
            try expectEqual((export["protocol_order"] as? [Int])?.map(UInt32.init), PWDisposition.protocolOrder)
            try expectEqual(strings(export["run_references"]), PWDisposition.runReferences)
            try expectEqual(strings(export["step_references"]), PWDisposition.stepReferences)
        }
        for model in [false, true] {
        tk.run(model ? "the production resolver satisfies all 2880 finite-model rows" : "the resolver reproduces every hand-reviewed example row") {
            if export.isEmpty { export = try pythonExport(root) }
            let rows = model ? try pythonExport(root, model: true) : export
            let examples = rows["examples"] as? [[String: Any]] ?? []
            try expectTrue(model ? examples.count == 2880 : examples.count >= 20, "rows missing from the export")
            for example in examples {
                let name = example["name"] as? String ?? "?"
                let (out, plan) = inputs(from: example["observations"] as! [String: Any])
                let record = resolveDisposition(out, plan: plan)
                let expectedClaims = example["claims"] as! [String: Any]
                for (question, expected) in expectedClaims {
                    guard let actual = record.questions[question] else { throw TestFailure(message: "\(name): missing \(question)") }
                    let got = try comparable(actual)
                    try expectTrue(NSDictionary(dictionary: got).isEqual(to: expected as! [String: Any]),
                                   "\(name) \(question): \(got) vs \(expected)")
                }
                let expectedSteps = example["steps"] as! [[String: Any]]
                try expectEqual(record.steps.count, expectedSteps.count, name)
                for (i, expectedStep) in expectedSteps.enumerated() {
                    for (question, expected) in expectedStep {
                        guard let actual = record.steps[i].questions[question] else {
                            throw TestFailure(message: "\(name) step \(i): missing \(question)")
                        }
                        let got = try comparable(actual)
                        try expectTrue(NSDictionary(dictionary: got).isEqual(to: expected as! [String: Any]),
                                       "\(name) step \(i) \(question): \(got) vs \(expected)")
                    }
                }
                let expectedIssues = example["issues"] as! [[String: Any]]
                try expectEqual(record.issues.count, expectedIssues.count, "\(name) issues")
                for (issue, expected) in zip(record.issues, expectedIssues) {
                    try expectEqual(issue.rule, expected["rule"] as? String, name)
                    try expectEqual(issue.question, expected["question"] as? String, name)
                    try expectEqual(issue.step_index, expected["step_index"] as? Int, name)
                    try expectEqual(issue.observations, strings(expected["observations"]), name)
                }
                let projections = example["projections"] as! [String: Any]
                try expectEqual(record.steps.map(lifecycleSummary), strings(projections["summaries"]), name)
                try expectEqual(buildWorkerSubprocess(out, disposition: record).partial_steps,
                                projections["partial_steps"] as? Bool, name)
                let sub = buildWorkerSubprocess(out, disposition: record)
                let problems = dispositionIntegrityProblems(record, subprocess: sub, stepCount: plan.count)
                try expectEqual(!problems.isEmpty, example["invalid_basis"] as? Bool ?? false,
                                "\(name): integrity \(problems)")
            }
        }
        }
    }
}

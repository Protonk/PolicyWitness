import Darwin
import Foundation
@testable import PWRunnerCore

// Disposition record (controller/DISPOSITION-RECORD-PLAN.md, areas B and C).
//
// Today this file establishes what the resolver will interpret: constructed
// CWorkerOutput values carrying slots and a progress word, and the publication
// patterns the ABI fixture can produce through the real primitives. The
// preservation controls pass on the current step builder and classifier. The
// integration-gap blocks are registered only when PW_DISPOSITION_REDS=1 (the
// non-default case runner_unit/disposition_reds); they fail until the resolver
// and the record exist and name that gap, never a policy cause. The fixture
// never applies a sandbox. The independent expectations live in
// tests/lib/lifecycle_contract.py and tests/lib/lifecycle_oracle.py; the Swift
// mirror of those tables lands with the resolver.

private let dispositionRedsGated = ProcessInfo.processInfo.environment["PW_DISPOSITION_REDS"] == "1"

private func slot(_ id: String, completed: Bool, rc: Int32 = 0) -> CWorkerSlotResult {
    CWorkerSlotResult(stepId: id, rc: rc, errnoVal: 0, observedPath: completed ? "fixture-observation" : nil,
                      error: nil, completed: completed)
}

private func progressWord(_ op: UInt32, _ phase: UInt32, index: UInt32? = nil) -> PWWorkerProgress {
    let item: UInt32 = index.map { $0 + 1 } ?? 0
    return PWWorkerProgress(raw: (op << 24) | (phase << 20) | item, operation: op, phase: phase, index: index)
}

private func evidence(progress: PWWorkerProgress?) -> PWWorkerEvidence {
    PWWorkerEvidence(abi_version: PWShmLayout.abiVersion, progress: progress, failure_publication: 0,
                     failure_state: "absent", failure: nil, readiness: nil,
                     diagnostic: PWWorkerDiagnostic(state: 0, status: "absent", length: nil, text: nil))
}

// Constructed output in the style of HostOutcomeClassifierTests.workerOut, extended
// with slots and a worker evidence value carrying a progress word.
private func constructed(slots: [CWorkerSlotResult], progress: PWWorkerProgress?,
                         stop: String = "done", exitCode: Int32? = 0, termSignal: Int32? = nil,
                         request: PWRunnerTerminationRequest? = nil, reaped: Bool = true) -> CWorkerOutput {
    CWorkerOutput(
        workerPid: 4242, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0,
        done: stop == "done", exitCode: exitCode, termSignal: termSignal, slots: slots,
        pollStopReason: stop, exitRequested: true, terminationRequest: request, reaped: reaped,
        waitErrors: [], workerEvidence: evidence(progress: progress))
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

func runDispositionResolverTests(_ tk: TestKit) {
    tk.group("disposition observations (fixture, no sandbox)") {
        tk.run("C2: started attempt with two slots leaves the poison unread and the second slot untouched") {
            let out = try dispositionFixture("started_attempt", stepIds: ["first", "second"])
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            try expectEqual(out.exitCode, 0)
            try expectNil(out.termSignal)
            try expectNil(out.terminationRequest, "a voluntary exit during grace needs no kill")
            try expectEqual(out.reaped, true)
            try expectEqual(out.slots.count, 2)
            try expectFalse(out.slots[0].completed)
            try expectEqual(out.slots[0].rc, Int32(0), "placeholder rc; the poison 12345 is never read")
            try expectFalse(out.slots[1].completed)
            try expectEqual(out.workerEvidence?.progress?.operation, 9)
            try expectEqual(out.workerEvidence?.progress?.phase, 1)
            try expectEqual(out.workerEvidence?.progress?.index, 0)
            for (index, id) in ["first", "second"].enumerated() {
                let attempt = buildAttemptResult(step: probe(id), slot: out.slots[index])
                try expectEqual(attempt.outcome, AttemptOutcome.notRunWorkerDied)
                try expectEqual(attempt.rc, -1, "projected missing rc is not an observed native return")
            }
            let sub = try encodedObject(buildWorkerSubprocess(out))
            try expectEqual(sub["partial_steps"] as? Bool, true)
        }
        tk.run("C5: skip_publication completes slot 0 and returns slot 1 without completing it") {
            let out = try dispositionFixture("skip_publication", stepIds: ["first", "second"])
            try expectTrue(out.done)
            try expectEqual(out.pollStopReason, "done")
            try expectEqual(out.exitCode, 0)
            try expectEqual(out.reaped, true)
            try expectNil(out.terminationRequest)
            try expectTrue(out.slots[0].completed)
            try expectEqual(out.slots[0].rc, Int32(0))
            try expectFalse(out.slots[1].completed)
            try expectEqual(out.slots[1].rc, Int32(0), "the poison is never read without completed publication")
            try expectEqual(out.workerEvidence?.progress?.operation, 9)
            try expectEqual(out.workerEvidence?.progress?.phase, 2)
            try expectEqual(out.workerEvidence?.progress?.index, 1)
            try expectEqual(buildAttemptResult(step: probe("first"), slot: out.slots[0]).outcome, AttemptOutcome.ok)
            try expectEqual(buildAttemptResult(step: probe("second"), slot: out.slots[1]).outcome,
                            AttemptOutcome.notRunWorkerDied)
        }
    }

    tk.group("disposition preservation (constructed)") {
        tk.run("B3: unrecognized progress operation does not disturb completed results") {
            let out = constructed(slots: [slot("a", completed: true), slot("b", completed: true)],
                                  progress: progressWord(200, 1, index: 0))
            try expectEqual(classify(workerResult: .success(out), validatorResult: nil,
                                     expectedVerdictCount: 0).outcome, NormalizedOutcome.ok)
            for (index, id) in ["a", "b"].enumerated() {
                try expectEqual(buildAttemptResult(step: probe(id), slot: out.slots[index]).outcome, AttemptOutcome.ok)
            }
            let bytes = try pwRunnerEncodeJSON(buildWorkerSubprocess(out))
            let decoded = try pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: bytes)
            try expectEqual(decoded.worker_evidence?.progress?.operation, 200, "the raw word survives")
            try expectEqual(decoded.partial_steps, false)
        }
        tk.run("B6: a completed no-op slot for an unsupported attempt is not a completed requested operation") {
            let attempt = buildAttemptResult(step: probe("u", kind: "bogus", action: "nope"),
                                             slot: slot("u", completed: true, rc: 0))
            try expectEqual(attempt.outcome, AttemptOutcome.unsupported)
            try expectContains(attempt.error ?? "", "not implemented")
        }
        tk.run("B2: missing progress beside an incomplete slot keeps the compatibility spelling") {
            let out = constructed(slots: [slot("a", completed: false)], progress: nil,
                                  stop: "sentinel_deadline", exitCode: nil, termSignal: 9,
                                  request: PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil))
            let attempt = buildAttemptResult(step: probe("a"), slot: out.slots[0])
            try expectEqual(attempt.outcome, AttemptOutcome.notRunWorkerDied)
            try expectEqual(classify(workerResult: .success(out), validatorResult: nil,
                                     expectedVerdictCount: 0).outcome, NormalizedOutcome.runnerTimeout)
        }
    }

    guard dispositionRedsGated else { return }
    tk.group("disposition integration gaps (PW_DISPOSITION_REDS)") {
        tk.run("disposition gap: runner_subprocess carries the record and the three host facts") {
            let out = constructed(slots: [slot("a", completed: false), slot("b", completed: false)],
                                  progress: progressWord(9, 1, index: 0), stop: "sentinel_deadline",
                                  exitCode: nil, termSignal: 9,
                                  request: PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil))
            let sub = try encodedObject(buildWorkerSubprocess(out))
            for key in ["cleanup_trigger", "grace_end", "collection_basis", "disposition"] {
                try expectNotNil(sub[key], "runner_subprocess.\(key) is not produced yet")
            }
        }
        tk.run("disposition gap: attempt results carry a lifecycle object") {
            let attempt = try encodedObject(buildAttemptResult(step: probe("a"), slot: slot("a", completed: false)))
            try expectNotNil(attempt["lifecycle"], "attempt.lifecycle is not produced yet")
        }
        tk.run("disposition gap: C5's real publication conflict is reported as a D5 issue") {
            let out = try dispositionFixture("skip_publication", stepIds: ["first", "second"])
            let sub = try encodedObject(buildWorkerSubprocess(out))
            let record = sub["disposition"] as? [String: Any]
            let issues = record?["issues"] as? [[String: Any]] ?? []
            try expectTrue(issues.contains { ($0["rule"] as? String) == "D5" },
                           "no D5 publication conflict reported for the incomplete returned slot")
        }
        tk.run("disposition gap: C2's started attempt claims started_without_result then not_reached") {
            let out = try dispositionFixture("started_attempt", stepIds: ["first", "second"])
            let sub = try encodedObject(buildWorkerSubprocess(out))
            let record = sub["disposition"] as? [String: Any]
            try expectNotNil(record, "no disposition record produced for the started attempt")
        }
    }
}

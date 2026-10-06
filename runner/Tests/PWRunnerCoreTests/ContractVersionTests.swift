import Foundation
@testable import PWRunnerCore

// docs/contract.json is the only hand-edited copy of the wire contract
// versions. The generated Swift copies are text; this compares the compiled
// values against the manifest so a stale or hand-edited region cannot ship.
private struct ContractManifest: Decodable {
    struct Versions: Decodable {
        let request_schema: Int
        let response_schema: Int
        let controller_envelope: Int
    }
    let versions: Versions
}

func repositoryRoot() -> URL {
    URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
}

// Reply shape golden: tests/fixtures/contract/response_shape.json records, per
// object path, every key the producer emits across the documents of
// replyShapeDocuments() and its JSON type.
// Any change fails until the golden is replaced. A number moves when the rules
// for reading change: a removed key, a changed type or meaning, or a new
// requirement on readers; an added field alone does not require a bump, and
// an absent field means unknown, never false.
private func jsonType(_ value: Any) -> String {
    if value is NSNull { return "null" }
    if let number = value as? NSNumber {
        return CFGetTypeID(number) == CFBooleanGetTypeID() ? "boolean" : "number"
    }
    if value is String { return "string" }
    if value is [Any] { return "array" }
    if value is [String: Any] { return "object" }
    return "unknown"
}

/// Record `object`'s keys under `path`; every object element of an array
/// contributes to the `path[]` entry. A key seen as null in one place and
/// typed in another records the type; two different types are a conflict.
private func collectShape(_ object: [String: Any], path: String, into shape: inout [String: [String: String]]) throws {
    var keys = shape[path] ?? [:]
    for (key, value) in object {
        let type = jsonType(value)
        if let current = keys[key], current != "null", current != type, type != "null" {
            throw TestFailure(message: "shape conflict at \(path).\(key): \(current) and \(type)")
        }
        if keys[key] == nil || keys[key] == "null" { keys[key] = type }
        let child = path + "." + key
        if let nested = value as? [String: Any] {
            try collectShape(nested, path: child, into: &shape)
        } else if let array = value as? [Any] {
            for element in array.compactMap({ $0 as? [String: Any] }) {
                try collectShape(element, path: child + "[]", into: &shape)
            }
        }
    }
    shape[path] = keys
}

private func shapeObject(_ data: Data) throws -> [String: Any] {
    try JSONSerialization.jsonObject(with: data) as! [String: Any]
}

private func shapeSlot(_ id: String, completed: Bool) -> CWorkerSlotResult {
    CWorkerSlotResult(stepId: id, rc: 0, errnoVal: 0, observedPath: completed ? "/private/owned" : nil,
                      error: nil, completed: completed)
}

private func shapeProgress(_ op: UInt32, _ phase: UInt32, index: UInt32? = nil) -> PWWorkerProgress {
    let item: UInt32 = index.map { $0 + 1 } ?? 0
    return PWWorkerProgress(raw: (op << 24) | (phase << 20) | item, operation: op, phase: phase, index: index)
}

private func shapeProbe(_ id: String, kind: String = "file", action: String = "open_read") -> PWRunnerProbeStep {
    PWRunnerProbeStep(step_id: id,
        sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                                            filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
        attempt: PWRunnerAttempt(kind: kind, action: action, target: "/etc/hosts"))
}

private func shapeDiagnostic() -> PWWorkerDiagnostic {
    PWWorkerDiagnostic(state: 2, status: "truncated", length: 4, text: "text")
}

/// Worker accounts the field-complete fixture cannot carry at once, resolved
/// and assembled by the production builders so the encoder accepts them:
/// a confirmed exit whose progress word says the second attempt returned while
/// its slot stayed incomplete (the D5 conflict, with its issue and the
/// synthetic attempt's missing reason); a signalled worker with a termination
/// request, a published failure and a policy transfer error; a confirmed exit
/// whose progress word is unusable (unresolved step claims with reasons); a
/// plan whose attempt kind the worker does not support (inapplicable claims);
/// and a worker reaped before any exit was requested (inapplicable cleanup
/// claims with reasons). Each returns the output and the plan it answers.
private func shapeWorkerOutputs() -> [(CWorkerOutput, [PWRunnerProbeStep])] {
    var conflict = CWorkerOutput(
        workerPid: 42, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0, done: true,
        exitCode: 0, termSignal: nil, slots: [shapeSlot("first", completed: true), shapeSlot("second", completed: false)],
        pollStopReason: "done", exitRequested: true, terminationRequest: nil, reaped: true, waitErrors: [],
        workerEvidence: PWWorkerEvidence(abi_identity: PWShmLayout.abiIdentityHex, progress: shapeProgress(9, 2, index: 1),
            failure_publication: 0, failure_state: "absent", failure: nil,
            readiness: PWWorkerReadiness(rc: 1, errno: 0), diagnostic: shapeDiagnostic()))
    conflict.cleanupTrigger = "completion"
    conflict.graceEnd = "reaped_during_grace"
    conflict.collectionBasis = "after_confirmed_reap"
    var signalled = CWorkerOutput(
        workerPid: 42, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0, done: false,
        exitCode: nil, termSignal: 9, slots: [shapeSlot("first", completed: true)],
        pollStopReason: "sentinel_deadline", exitRequested: true,
        terminationRequest: PWRunnerTerminationRequest(signal: 9, rc: 0, errno: nil), reaped: true,
        waitErrors: [PWRunnerWaitError(phase: "exit_grace", rc: -1, errno: 10)],
        workerEvidence: PWWorkerEvidence(abi_identity: PWShmLayout.abiIdentityHex, progress: shapeProgress(10, 2),
            failure_publication: 1, failure_state: "published",
            failure: PWWorkerFailure(operation: 10, code: 1, native_kind: 1, native_result: -1, errno: 22, index: 0, detail: 0),
            readiness: PWWorkerReadiness(rc: 1, errno: 0), diagnostic: shapeDiagnostic()))
    signalled.policyTransferError = PWWorkerPolicyTransferError(errno: 32, bytes_written: 10, bytes_expected: 100)
    signalled.cleanupTrigger = "deadline_expiry"
    signalled.graceEnd = "exhausted"
    signalled.collectionBasis = "after_confirmed_reap"
    var unusable = conflict
    unusable.slots = [shapeSlot("first", completed: false)]
    var word = shapeProgress(9, 1, index: 0)
    word.raw = shapeProgress(9, 1, index: 1).raw
    unusable.workerEvidence?.progress = word
    var unsupported = conflict
    unsupported.slots = [shapeSlot("first", completed: true)]
    unsupported.workerEvidence?.progress = nil
    var crashed = conflict
    crashed.done = false
    crashed.exitCode = nil
    crashed.termSignal = 11
    crashed.slots = [shapeSlot("first", completed: false)]
    crashed.pollStopReason = "child_reaped"
    crashed.exitRequested = false
    crashed.cleanupTrigger = "child_reaped"
    crashed.graceEnd = "not_entered"
    crashed.workerEvidence?.progress = shapeProgress(9, 1, index: 0)
    var transferTimedOut = signalled
    transferTimedOut.policyTransferError = nil
    transferTimedOut.policyTransferTimeout = PWWorkerPolicyTransferTimeout(budget_ms: 5000, elapsed_ms: 5001, bytes_written: 8192, bytes_expected: 200000)
    transferTimedOut.pollStopReason = "policy_transfer_deadline"
    transferTimedOut.cleanupTrigger = "policy_transfer_timeout"
    return [
        (transferTimedOut, [shapeProbe("first")]),
        (conflict, [shapeProbe("first"), shapeProbe("second")]),
        (signalled, [shapeProbe("first")]),
        (unusable, [shapeProbe("first")]),
        (unsupported, [shapeProbe("first", kind: "future", action: "future")]),
        (crashed, [shapeProbe("first")]),
    ]
}

/// Every encoded document whose keys the reply golden records: the
/// field-complete fixture, its degraded reply (`reporting_failure` beside the
/// retained evidence), the fixture with a signalled validator, and the
/// production-shaped worker accounts above. Only the encoder's output counts:
/// a key appears in the golden because the producer emitted it.
func replyShapeDocuments() throws -> [[String: Any]] {
    var documents: [[String: Any]] = []
    let base = try replyFixture()
    documents.append(try shapeObject(pwRunnerEncodeJSON(base)))
    var defective = base
    defective.steps[0].comparison?.order = "future_order"
    documents.append(try shapeObject(pwRunnerReplyData(defective)))
    var signalledValidator = base
    signalledValidator.validator_subprocess?.term_signal = 9
    signalledValidator.validator_subprocess?.exit_code = nil
    documents.append(try shapeObject(pwRunnerEncodeJSON(signalledValidator)))
    for (out, plan) in shapeWorkerOutputs() {
        let record = resolveDisposition(out, plan: plan)
        var sub = buildWorkerSubprocess(out, disposition: record)
        sub.ordering = buildOrdering(out, validatorOutput: nil, hasQueries: true)
        let reply = PWRunnerRunResult(specimen_id: "shape", rc: 0, normalized_outcome: NormalizedOutcome.ok,
            pid: Int(out.workerPid), policy_format: "sbpl", sandboxed_after_apply: true,
            steps: buildStepResults(probePlan: plan, queryPlan: planValidatorQueries(plan), workerOutput: out,
                                    validatorOutput: nil, ordering: sub.ordering, disposition: record),
            runner_subprocess: sub)
        documents.append(try shapeObject(pwRunnerEncodeJSON(reply)))
    }
    return documents
}

/// The merged shape of every document, collected the same way for each.
func replyShape() throws -> [String: [String: String]] {
    var merged: [String: [String: String]] = [:]
    for document in try replyShapeDocuments() {
        try collectShape(document, path: "reply", into: &merged)
    }
    return merged
}

struct ShapeVerdict: Equatable {
    let status: String   // ok, missing_golden, needs_bump, update
    let detail: String
}

func classifyShapeChange(golden: [String: Any]?, current: [String: [String: String]],
                         manifestVersion: Int) -> ShapeVerdict {
    let goldenShape = golden?["shape"] as? [String: [String: String]] ?? [:]
    guard let recorded = golden?["response_schema"] as? Int else {
        return ShapeVerdict(status: "missing_golden", detail: "no reply shape golden")
    }
    if goldenShape == current && recorded == manifestVersion { return ShapeVerdict(status: "ok", detail: "") }
    var removed: [String] = [], changed: [String] = [], added: [String] = []
    for (path, keys) in goldenShape {
        for (key, type) in keys {
            guard let now = current[path]?[key] else { removed.append(path + "." + key); continue }
            if now != type && now != "null" && type != "null" { changed.append("\(path).\(key): \(type) -> \(now)") }
        }
    }
    for (path, keys) in current {
        for key in keys.keys where goldenShape[path]?[key] == nil { added.append(path + "." + key) }
    }
    if !removed.isEmpty || !changed.isEmpty {
        let detail = "reply reading rules changed (removed: \(removed.sorted()); changed: \(changed.sorted()))"
        return manifestVersion <= recorded
            ? ShapeVerdict(status: "needs_bump", detail: detail)
            : ShapeVerdict(status: "update", detail: detail + "; the manifest already moved")
    }
    if recorded != manifestVersion {
        return ShapeVerdict(status: "update", detail: "golden records response \(recorded); manifest says \(manifestVersion)")
    }
    if !added.isEmpty {
        return ShapeVerdict(status: "update", detail: "reply shape gained fields \(added.sorted()); additive, no bump needed")
    }
    return ShapeVerdict(status: "update", detail: "nullable fields changed their recorded type; no bump needed")
}

func runContractVersionTests(_ tk: TestKit) {
    let root = repositoryRoot()
    tk.group("Wire contract versions") {
        tk.run("compiled Swift constants agree with docs/contract.json") {
            let manifest = try JSONDecoder().decode(ContractManifest.self,
                from: Data(contentsOf: root.appendingPathComponent("docs/contract.json")))
            try expectEqual(PWContract.requestSchema, manifest.versions.request_schema)
            try expectEqual(PWContract.responseSchema, manifest.versions.response_schema)
            try expectEqual(PWShmLayout.abiIdentity.count, PWShmLayout.abiIdentityBytes)
            try expectEqual(PWShmLayout.abiIdentity.map { String(format: "%02x", $0) }.joined(),
                            PWShmLayout.abiIdentityHex)
        }
        tk.run("shape classification separates additive, breaking and unacknowledged changes") {
            let base: [String: [String: String]] = ["reply": ["a": "number", "b": "null"], "reply.o": ["k": "string"]]
            func golden(_ shape: [String: [String: String]], _ version: Int) -> [String: Any] {
                ["shape": shape, "response_schema": version]
            }
            try expectEqual(classifyShapeChange(golden: nil, current: base, manifestVersion: 8).status, "missing_golden")
            try expectEqual(classifyShapeChange(golden: golden(base, 8), current: base, manifestVersion: 8).status, "ok")
            var added = base; added["reply"]?["c"] = "string"
            let additive = classifyShapeChange(golden: golden(base, 8), current: added, manifestVersion: 8)
            try expectEqual(additive.status, "update"); try expectContains(additive.detail, "no bump needed")
            var removed = base; removed["reply"]?.removeValue(forKey: "a")
            try expectEqual(classifyShapeChange(golden: golden(base, 8), current: removed, manifestVersion: 8).status, "needs_bump")
            try expectEqual(classifyShapeChange(golden: golden(base, 8), current: removed, manifestVersion: 9).status, "update")
            var retyped = base; retyped["reply"]?["a"] = "string"
            try expectEqual(classifyShapeChange(golden: golden(base, 8), current: retyped, manifestVersion: 8).status, "needs_bump")
            var nullable = base; nullable["reply"]?["b"] = "object"
            let refined = classifyShapeChange(golden: golden(base, 8), current: nullable, manifestVersion: 8)
            try expectEqual(refined.status, "update"); try expectContains(refined.detail, "nullable")
            try expectEqual(classifyShapeChange(golden: golden(base, 7), current: base, manifestVersion: 8).status, "update")
        }
        tk.run("shape documents cover the keys an ordinary fixture cannot carry at once") {
            let shape = try replyShape()
            for (path, key) in [("reply", "reporting_failure"), ("reply.steps[].attempt", "missing_reason"),
                                ("reply.validator_subprocess", "term_signal"), ("reply.runner_subprocess", "exit_code"),
                                ("reply.runner_subprocess", "term_signal"), ("reply.runner_subprocess", "policy_transfer_error"),
                                ("reply.runner_subprocess", "policy_transfer_timeout"),
                                ("reply.runner_subprocess.worker_evidence", "failure"),
                                ("reply.runner_subprocess.disposition.issues[]", "rule"),
                                ("reply.runner_subprocess.disposition.steps[].questions.step_result_published", "issue"),
                                ("reply.runner_subprocess.disposition.steps[].questions.step_result_published", "reason"),
                                ("reply.runner_subprocess.disposition.steps[].questions.step_boundary_reached", "reason"),
                                ("reply.steps[].attempt.lifecycle.boundary", "reason"),
                                ("reply.steps[].attempt.lifecycle.result", "reason"),
                                ("reply.runner_subprocess.disposition.questions.cleanup_trigger", "reason"),
                                ("reply.runner_subprocess.disposition.questions.grace_end", "reason"),
                                ("reply.runner_subprocess.disposition.questions.kill_request_and_result", "reason")] {
                try expectTrue(shape[path]?[key] != nil && shape[path]?[key] != "null", "\(path).\(key) is not typed")
            }
        }
        tk.run("reply shape golden agrees with the manifest") {
            let goldenURL = root.appendingPathComponent("tests/fixtures/contract/response_shape.json")
            let current = try replyShape()
            let golden = (try? JSONSerialization.jsonObject(with: Data(contentsOf: goldenURL))) as? [String: Any]
            let verdict = classifyShapeChange(golden: golden, current: current, manifestVersion: PWContract.responseSchema)
            if verdict.status == "ok" { return }
            let candidate: [String: Any] = ["response_schema": PWContract.responseSchema, "shape": current]
            let candidateData = try JSONSerialization.data(withJSONObject: candidate, options: [.prettyPrinted, .sortedKeys])
            let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"].map { URL(fileURLWithPath: $0) }
                ?? FileManager.default.temporaryDirectory
            let candidateURL = artifacts.appendingPathComponent("response_shape.candidate.json")
            try (candidateData + Data("\n".utf8)).write(to: candidateURL)
            var advice = "review the diff, then replace tests/fixtures/contract/response_shape.json with \(candidateURL.path)"
            if verdict.status == "needs_bump" {
                advice = "bump response_schema in docs/contract.json, regenerate, then " + advice
            }
            throw TestFailure(message: "\(verdict.detail); \(advice)")
        }
    }
}

import Foundation
@testable import PWRunnerCore

// A conservative bound on replies for admitted specimens: the ordinary fixture with
// 256 steps, 256 validator records and disposition entries, every request- or
// host-derived string at its documented limit and made of U+0001 (six JSON bytes
// per byte), the largest worker diagnostic, and the largest slash-heavy
// compiled-profile receipt. The runner client's retention budget is derived from
// this number, and the live max-target workload must stay under it. Separately
// encoded spawn-failure, extension and fresh-read components are added without subtracting
// ordinary fields they replace. This union is deliberately not a reachable reply.
//
// Every string key the fixture carries must be classified below as fixed
// vocabulary (kept) or bounded (replaced by a maximal string). An unclassified
// key fails the test, so adding a reply field forces a decision about its size.

private let maximalUnit = "\u{01}"

// A parent realpath is followed by a slash and an admitted literal leaf; the
// resulting diagnostic string can exceed realpath's own 1,023-byte buffer.
let maximalParentPathBytes = 1023 + 1 + (PWShmLayout.targetMax - 1)
// Supported system firmlinks prepend /System/Volumes/Data to a realpath.
let maximalFirmlinkPathBytes = 1023 + "/System/Volumes/Data".utf8.count

private func maximal(_ bytes: Int) -> String { String(repeating: maximalUnit, count: bytes) }

/// Documented UTF-8 byte limits for echoed strings; nil keeps a fixed value.
private let stringPolicy: [String: Int?] = [
    // Fixed vocabulary or host constants.
    "normalized_outcome": nil, "bundle_id": nil, "policy_format": nil, "policy_sha256": nil,
    "status": nil, "reason": nil, "outcome": nil, "result_source": nil,
    "missing_reason": nil, "observer": nil, "stage": nil, "same_as_input": nil, "summary": nil,
    "state": nil, "answer": nil, "basis": nil, "observation": nil,
    "observation_basis": nil, "operation_relation": nil, "target_relation": nil,
    "order": nil, "limitations": nil, "poll_stop_reason": nil,
    "cleanup_trigger": nil, "grace_end": nil, "collection_basis": nil, "slot": nil,
    "attempt_support": nil, "validator_disposition": nil, "protocol_violations": nil,
    "failure_state": nil, "origin": nil, "field": nil, "unit": nil, "kind": nil,
    "filter_type": 63, "signal": nil, "stdout_collection_stop": nil, "question": nil,
    "request_nonce": nil, "bytecode_sha256": nil, "source_sha256": nil, "params_sha256": nil,
    "abi_identity": nil, "code": nil, "collection_status": nil,
    "original_normalized_outcome": nil, "unavailable_reason": nil,
    "detail": nil, "observations": nil, "rule": nil, "original_error": 8191,
    "extension_class": nil, "preparation_status": nil, "issuance_status": nil, "delivery_status": nil,
    // Bounded echoes of request strings.
    "specimen_id": specimenIdMaxBytes, "run_kind": requestLabelMaxBytes, "path": 63,
    "phase_id": requestLabelMaxBytes, "action_ids": PWShmLayout.stepIdMax - 1,
    "step_id": PWShmLayout.stepIdMax - 1, "operation": sandboxCheckOperationMaxBytes,
    "filter_kind": probePlanLabelMaxBytes, "filter_value": sandboxCheckFilterValueMaxBytes,
    "input": sandboxCheckFilterValueMaxBytes, "requested_kind": probePlanLabelMaxBytes,
    "requested_action": probePlanLabelMaxBytes, "requested_path": PWShmLayout.targetMax - 1,
    "parameter_key": PWShmLayout.paramKeyMax - 1, "expected_step_ids": PWShmLayout.stepIdMax - 1,
    "worker_executable_path": testOverridePathMaxBytes,
    "issuer_executable_path": testOverridePathMaxBytes,
    "validator_executable_path": testOverridePathMaxBytes, "executable_path": testOverridePathMaxBytes,
    "token_ref": PWExtensionLimits.referenceBytes, "handle_ref": PWExtensionLimits.referenceBytes,
    "submitted_target": PWExtensionLimits.targetBytes, "resolved_target": PWExtensionLimits.targetBytes,
    // Bounded host-derived strings.
    "error": 8191, "diagnostic": 1023, "message": 1023, "read_error": 1023, "io_error": 1023,
    "realpath_resolved": 1023, "firmlink_resolved": maximalFirmlinkPathBytes,
    "parent_realpath_resolved": maximalParentPathBytes,
    "observed_path": PWShmLayout.observedPathMax - 1, "stdout": PWShmLayout.childOutputBytes - 1,
    "stderr": PWShmLayout.childOutputBytes - 1, "text": PWShmLayout.diagnosticBytes - 1,
    // Generated below rather than filled: valid base64 and the validator's own line.
    "bytecode_b64": nil, "context_b64": nil, "raw_line": nil, "content_hex": nil,
]

private struct Unclassified: Error, CustomStringConvertible {
    let keys: Set<String>
    var description: String { "unclassified reply string keys: \(keys.sorted())" }
}

/// Replace every bounded string leaf with its maximal value; collect unknown keys.
private func maximize(_ value: Any, key: String?, unknown: inout Set<String>) -> Any {
    if value is String {
        guard let key else { return value }
        guard let policy = stringPolicy[key] else { unknown.insert(key); return value }
        if let bytes = policy { return maximal(bytes) }
        return value
    }
    if let array = value as? [Any] { return array.map { maximize($0, key: key, unknown: &unknown) } }
    if let object = value as? [String: Any] {
        var out: [String: Any] = [:]
        for (k, v) in object { out[k] = maximize(v, key: k, unknown: &unknown) }
        return out
    }
    return value
}

/// The maximal per-step attempt error text is the worker's bounded buffer; the
/// sandbox_check error is the validator's bounded diagnostic (its buffer is 512).
private func addAbsentOptionalFields(_ reply: inout [String: Any]) {
    var requestFailure = reply["request_failure"] as! [String: Any]
    requestFailure["path"] = Array(repeating: maximal(63), count: 8)
    reply["request_failure"] = requestFailure
    var steps = reply["steps"] as! [[String: Any]]
    var step = steps[0]
    var check = step["sandbox_check"] as! [String: Any]
    check["error"] = maximal(511)
    check["missing_reason"] = "validator_no_verdict"
    var diagnostics = check["path_diagnostics"] as! [String: Any]
    diagnostics["same_as_input"] = [String]()
    diagnostics["realpath_resolved"] = maximal(1023)
    diagnostics["firmlink_resolved"] = maximal(maximalFirmlinkPathBytes)
    check["path_diagnostics"] = diagnostics
    step["sandbox_check"] = check
    var attempt = step["attempt"] as! [String: Any]
    var attemptPaths = attempt["path_diagnostics"] as! [String: Any]
    attemptPaths["same_as_input"] = [String]()
    attemptPaths["realpath_resolved"] = maximal(1023)
    attemptPaths["parent_realpath_resolved"] = maximal(maximalParentPathBytes)
    attempt["path_diagnostics"] = attemptPaths
    attempt["observed_path"] = maximal(PWShmLayout.observedPathMax - 1)
    attempt["error"] = maximal(PWShmLayout.errorMax - 1)
    attempt["stdout"] = maximal(PWShmLayout.childOutputBytes - 1)
    attempt["stderr"] = maximal(PWShmLayout.childOutputBytes - 1)
    attempt["child_pid"] = 4_294_967_295; attempt["child_exit_code"] = 255; attempt["child_term_signal"] = 31
    attempt["errno"] = 2_147_483_647
    step["attempt"] = attempt
    // The maximal validator records do not describe this step's query, so the
    // comparison cannot claim query_first. The record beside the step says the
    // attempt completed, so the one limitation a completed step can carry is
    // the planner's exclusion code (the longest of the three).
    var comparison = step["comparison"] as! [String: Any]
    comparison["order"] = "unestablished"
    comparison["limitations"] = ["query_plan:path_unresolved_at_planning"]
    step["comparison"] = comparison
    steps[0] = step
    reply["steps"] = steps

    var subprocess = reply["runner_subprocess"] as! [String: Any]
    var evidence = subprocess["worker_evidence"] as! [String: Any]
    evidence["diagnostic"] = ["state": 2, "status": "truncated", "length": PWShmLayout.diagnosticBytes - 1,
                              "text": maximal(PWShmLayout.diagnosticBytes - 1)]
    subprocess["worker_evidence"] = evidence
    subprocess["policy_transfer_timeout"] = ["budget_ms": 5000, "elapsed_ms": UInt64.max,
        "bytes_written": 262143, "bytes_expected": 262143] as [String: Any]
    reply["runner_subprocess"] = subprocess

    var phases = reply["phases"] as! [[String: Any]]
    var validator = phases[0]["validator_subprocess"] as! [String: Any]
    validator["read_error"] = maximal(1023)
    validator["io_error"] = maximal(1023)
    validator["decode_fault"] = ["origin": "runner_host", "kind": "structure", "message": maximal(1023),
                                 "byte_offset": 2_147_483_647, "frame_bytes": 2_147_483_647, "retained_bytes": 256,
                                 "context_b64": Data(repeating: 0xff, count: 256).base64EncodedString(),
                                 "context_truncated": true]
    phases[0]["validator_subprocess"] = validator
    reply["phases"] = phases

    reply["applied_profile"] = ["schema_version": 1, "status": "captured", "worker_pid": 4_294_967_295,
        "request_nonce": String(repeating: "f", count: 32), "profile_type": 0,
        "bytecode_length": PWShmLayout.captureBytes, "bytecode_sha256": String(repeating: "f", count: 64),
        "bytecode_b64": Data(repeating: 0xff, count: PWShmLayout.captureBytes).base64EncodedString(),
        "source_sha256": String(repeating: "f", count: 64), "source_length": PWShmLayout.policyBytes - 1,
        "params_sha256": String(repeating: "f", count: 64), "parameter_count": PWShmLayout.maxParams]
}

/// One maximal validator record and the line the validator would have emitted for it.
private func maximalRecord() throws -> [String: Any] {
    var record: [String: Any] = ["step_id": maximal(PWShmLayout.stepIdMax - 1), "operation": maximal(sandboxCheckOperationMaxBytes),
        "filter_type": "IOKIT_REGISTRY_ENTRY_CLASS", "filter_type_id": 2_147_483_647,
        "filter_value": maximal(sandboxCheckFilterValueMaxBytes), "rc": -1, "errno": 2_147_483_647,
        "outcome": "unsupported_operation", "error": maximal(511)]
    var line = record
    line["kind"] = "sb_api_validator_verdict"; line["schema_version"] = 1
    record["raw_line"] = String(decoding: try JSONSerialization.data(withJSONObject: line, options: [.sortedKeys]), as: UTF8.self)
    return record
}

/// Additional JSON members, including punctuation, encoded with the production
/// encoder. Optional failure/success fields coexist here solely to upper-bound
/// size; these components do not claim to satisfy full-reply evidence guards.
/// Count two events in addition to all 256 ordinary slots, and a fresh-read
/// payload beside every ordinary attempt, without reclaiming replaced fields.
private func extensionReplyAllowance() throws -> Int {
    let identity = PWFileIdentity(device: UInt64.max, inode: UInt64.max,
        mode: UInt32.max, uid: UInt32.max, gid: UInt32.max)
    var issuer = PWRunnerIssuer(executable_path: maximal(testOverridePathMaxBytes), pid: Int32.max,
        uid: UInt32.max, euid: UInt32.max, gid: UInt32.max, egid: UInt32.max,
        call_boundary_observed: false, result_published: false, native_nonnull: false,
        errno: Int32.max, token_length: UInt32.max, reaped: false, exit_code: Int32.max, term_signal: Int32.max)
    // Two lifetime EINTR retries plus a final failed wait at each boundary.
    issuer.wait_errors = Array(repeating: "after_termination", count: 4).map {
        PWRunnerWaitError(stage: $0, rc: -1, errno: Int32.max)
    }
    issuer.termination_request = PWRunnerTerminationRequest(signal: Int32.max, rc: -1, errno: Int32.max)
    issuer.spawn_failure = PWRunnerSpawnFailure(executable_path: maximal(testOverridePathMaxBytes),
        return_code: Int32.max, diagnostic: maximal(1023))
    let declaration = PWRunnerExtensionRecord(token_ref: maximal(PWExtensionLimits.referenceBytes),
        submitted_target: maximal(PWExtensionLimits.targetBytes), resolved_target: maximal(PWExtensionLimits.targetBytes),
        preparation_status: "resolution_failed", preparation_errno: Int32.max, identity: identity,
        issuance_status: "native_api_unavailable", issuer: issuer, delivery_status: "token_unavailable",
        delivered_bytes: UInt32.max, host_buffer_erased: false)
    let claim = PWDispositionClaim(state: "inapplicable", answer: "unpublished",
        value: .integer(Int.min), reason: "unsupported_attempt", issue: Int.max,
        basis: PWDisposition.runReferences + PWDisposition.stepReferences)
    let lifecycle = PWAttemptLifecycle(summary: "started_without_result", boundary: claim, result: claim)
    let events = ["consume", "release"].map { operation -> PWRunnerExtensionEvent in
        return PWRunnerExtensionEvent(phase_id: maximal(requestLabelMaxBytes), step_id: maximal(PWShmLayout.stepIdMax - 1),
            operation: operation, token_ref: maximal(PWExtensionLimits.referenceBytes),
            handle_ref: maximal(PWExtensionLimits.referenceBytes), call_boundary_observed: false, result_published: false,
            status: "unavailable", native_result: operation == "consume" ? Int64.min : Int64(Int32.min),
            errno: Int32.max, unavailable_reason: "native_api_unavailable", lifecycle: lifecycle)
    }
    struct NativeFields: Encodable {
        let extensions: [PWRunnerExtensionRecord]
        let extension_events: [PWRunnerExtensionEvent]
    }
    let native = try pwRunnerEncodeJSON(NativeFields(extensions: [declaration], extension_events: events))
    let fresh = PWRunnerFreshRead(open_rc: Int32.max, open_errno: Int32.max,
        read_rc: Int64(PWExtensionLimits.freshReadBytes), read_errno: Int32.max,
        stat_rc: -1, stat_errno: Int32.max, identity: identity, close_rc: -1, close_errno: Int32.max,
        content_hex: String(repeating: "f", count: PWExtensionLimits.freshReadBytes * 2))
    // Object braces overcount the actual comma joining these members, safely.
    let freshMember = try pwRunnerEncodeJSON(["fresh_read": fresh])
    let overrideMember = try pwRunnerEncodeJSON(["issuer_executable_path": maximal(testOverridePathMaxBytes)])
    return native.count + PWShmLayout.maxSteps * freshMember.count + overrideMember.count
}

/// Ordinary full-reply encoding plus conservative, separately encoded additions.
func maximalReplyEncodedSize() throws -> Int {
    let fixture = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(try replyFixture())) as! [String: Any]
    var unknown = Set<String>()
    var reply = maximize(fixture, key: nil, unknown: &unknown) as! [String: Any]
    if !unknown.isEmpty { throw Unclassified(keys: unknown) }
    addAbsentOptionalFields(&reply)
    reply["error"] = maximal(8191)

    let count = PWShmLayout.maxSteps
    func identity(_ index: Int) -> String {
        maximal(61) + String(UnicodeScalar(index / 31 + 1)!) + String(UnicodeScalar(index % 31 + 1)!)
    }
    let step = (reply["steps"] as! [[String: Any]])[0]
    reply["steps"] = (0..<count).map { index -> [String: Any] in
        var copy = step
        copy["step_id"] = identity(index)
        copy["phase_id"] = identity(index / (count / PWRunnerPhase.maximumCount))
        return copy
    }
    var subprocess = reply["runner_subprocess"] as! [String: Any]
    var disposition = subprocess["disposition"] as! [String: Any]
    let entry = (disposition["steps"] as! [[String: Any]])[0]
    disposition["steps"] = (0..<count).map { index -> [String: Any] in
        var copy = entry; copy["index"] = index; copy["step_id"] = identity(index); return copy
    }
    subprocess["disposition"] = disposition
    reply["runner_subprocess"] = subprocess
    var phases = reply["phases"] as! [[String: Any]]
    var validator = phases[0]["validator_subprocess"] as! [String: Any]
    var record = try maximalRecord()
    for (field, bound) in ValidatorReplyLimits.stringBytes { record[field] = maximal(bound) }
    record["raw_line"] = maximal(ValidatorReplyLimits.frameBytes)
    let perPhase = count / PWRunnerPhase.maximumCount
    reply["phases"] = (0..<PWRunnerPhase.maximumCount).map { index -> [String: Any] in
        var phase = phases[0], collection = validator
        let ids = (index * perPhase..<(index + 1) * perPhase).map(identity)
        phase["phase_id"] = identity(index); phase["ordinal"] = index + 1; phase["action_ids"] = ids
        collection["records"] = (0..<(ids.count * ValidatorReplyLimits.recordsPerProbe)).map { position -> [String: Any] in
            let id = identity(index * ids.count * ValidatorReplyLimits.recordsPerProbe + position)
            var copy = record; copy["step_id"] = id; return copy
        }
        collection["expected_step_ids"] = ids
        collection["association_issues"] = (0..<(ids.count * (ValidatorReplyLimits.recordsPerProbe + 1))).map { identity(index * ids.count * ValidatorReplyLimits.recordsPerProbe + $0) }.map { ["origin": "runner_host", "kind": "query_mismatch", "step_id": $0, "count": 1] as [String: Any] }
        collection["probe_bytes_written"] = 2_147_483_647; collection["probe_bytes_expected"] = 2_147_483_647
        collection["stdout_bytes_received"] = 2_147_483_647
        phase["validator_subprocess"] = collection
        return phase
    }

    let data = try JSONSerialization.data(withJSONObject: reply)
    let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
    try expectEqual(decoded.steps.count, count)
    // A failed spawn cannot coexist with a validator in an ordinary phase.
    // Encode its maximal member separately, preserving the conservative union
    // without asking the full-reply encoder to accept contradictory evidence.
    let spawnMember = try JSONSerialization.jsonObject(with:
        pwRunnerEncodeJSON(["validator_spawn_failure": validatorSpawnFailureFixture()]))
    let maximalSpawn = maximize(spawnMember, key: nil, unknown: &unknown)
    if !unknown.isEmpty { throw Unclassified(keys: unknown) }
    let spawn = try pwRunnerDecodeJSON([String: PWRunnerSpawnFailure].self,
        from: JSONSerialization.data(withJSONObject: maximalSpawn))
    // Remove one of the member object's two braces: inserting the member in
    // a nonempty phase adds one comma instead. All key/value bytes stay counted.
    let spawnAllowance = PWRunnerPhase.maximumCount * (try pwRunnerEncodeJSON(spawn).count - 1)
    return try pwRunnerEncodeJSON(decoded).count + extensionReplyAllowance() + spawnAllowance
}

private struct Manifest: Decodable {
    struct Limit: Decodable { let id: String; let value: Int }
    let limits: [Limit]
    func value(_ id: String) throws -> Int {
        guard let row = limits.first(where: { $0.id == id }) else { throw TestFailure(message: "limits.json lacks \(id)") }
        return row.value
    }
}

func runReplyMaximumTests(_ tk: TestKit) {
    tk.group("maximal reply and receiver budget") {
        tk.run("the runner client budget is three times the synthesized maximal reply, rounded up") {
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let manifest = try JSONDecoder().decode(Manifest.self,
                from: Data(contentsOf: root.appendingPathComponent("docs/limits.json")))
            let size = try maximalReplyEncodedSize()
            let budget = try manifest.value("controller_output")
            let rounding = 4 * 1024 * 1024
            FileHandle.standardOutput.write(Data("  maximal reply: \(size) bytes; budget \(budget)\n".utf8))
            try expectEqual(size, try manifest.value("runner_reply_maximum"), "limits.json records the synthesized maximum")
            try expectTrue(3 * size <= budget, "budget \(budget) below three times the maximal reply \(size)")
            try expectTrue(budget - 3 * size < rounding, "budget \(budget) is not three times \(size) rounded up to 4 MiB")
            try expectEqual(budget % rounding, 0, "budget is a whole number of 4 MiB")
        }
        tk.run("every reply string key is classified before it can grow the maximum") {
            // Inspect every shape document, including native/failure variants.
            var unknown = Set<String>()
            let fixtures = try replyShapeDocuments()
            for fixture in fixtures { _ = maximize(fixture, key: nil, unknown: &unknown) }
            try expectTrue(unknown.isEmpty, Unclassified(keys: unknown).description)
            var probe = fixtures[0]
            probe["future_reply_string"] = "unclassified"
            _ = maximize(probe, key: nil, unknown: &unknown)
            try expectEqual(unknown, ["future_reply_string"])
        }
    }
}

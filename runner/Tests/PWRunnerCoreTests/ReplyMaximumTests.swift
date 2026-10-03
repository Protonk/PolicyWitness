import Foundation
@testable import PWRunnerCore

// The largest reply the current response schema can encode for an admitted
// specimen, synthesized rather than measured: the field-complete fixture with
// 256 steps, 256 validator records and disposition entries, every request- or
// host-derived string at its documented limit and made of U+0001 (six JSON bytes
// per byte), the largest worker diagnostic, and the largest slash-heavy
// compiled-profile receipt. The runner client's retention budget is derived from
// this number, and the live max-target workload must stay under it.
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
    "missing_reason": nil, "observer": nil, "phase": nil, "same_as_input": nil, "summary": nil,
    "state": nil, "answer": nil, "basis": nil, "observation": nil,
    "observation_basis": nil, "operation_relation": nil, "target_relation": nil,
    "order": nil, "limitations": nil, "poll_stop_reason": nil,
    "cleanup_trigger": nil, "grace_end": nil, "collection_basis": nil, "slot": nil,
    "attempt_support": nil, "validator_disposition": nil, "protocol_violations": nil,
    "failure_state": nil, "origin": nil, "field": nil, "unit": nil, "kind": nil,
    "filter_type": nil, "signal": nil, "stdout_collection_stop": nil, "question": nil,
    "request_nonce": nil, "bytecode_sha256": nil, "source_sha256": nil, "params_sha256": nil,
    "abi_identity": nil, "code": nil,
    // Bounded echoes of request strings.
    "specimen_id": specimenIdMaxBytes, "run_kind": requestLabelMaxBytes, "path": 63,
    "step_id": PWShmLayout.stepIdMax - 1, "operation": sandboxCheckOperationMaxBytes,
    "filter_kind": probePlanLabelMaxBytes, "filter_value": sandboxCheckFilterValueMaxBytes,
    "input": sandboxCheckFilterValueMaxBytes, "requested_kind": probePlanLabelMaxBytes,
    "requested_action": probePlanLabelMaxBytes, "requested_path": PWShmLayout.targetMax - 1,
    "parameter_key": PWShmLayout.paramKeyMax - 1, "expected_step_ids": PWShmLayout.stepIdMax - 1,
    "worker_executable_path": testOverridePathMaxBytes,
    "validator_executable_path": testOverridePathMaxBytes, "executable_path": testOverridePathMaxBytes,
    // Bounded host-derived strings.
    "error": 8191, "diagnostic": 1023, "message": 1023, "read_error": 1023, "io_error": 1023,
    "realpath_resolved": 1023, "firmlink_resolved": maximalFirmlinkPathBytes,
    "parent_realpath_resolved": maximalParentPathBytes,
    "observed_path": PWShmLayout.observedPathMax - 1, "stdout": PWShmLayout.childOutputBytes - 1,
    "stderr": PWShmLayout.childOutputBytes - 1, "text": PWShmLayout.diagnosticBytes - 1,
    // Generated below rather than filled: valid base64 and the validator's own line.
    "bytecode_b64": nil, "context_b64": nil, "raw_line": nil,
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
    reply["runner_subprocess"] = subprocess

    var validator = reply["validator_subprocess"] as! [String: Any]
    validator["read_error"] = maximal(1023)
    validator["io_error"] = maximal(1023)
    validator["decode_fault"] = ["origin": "runner_host", "kind": "structure", "message": maximal(1023),
                                 "byte_offset": 2_147_483_647, "frame_bytes": 2_147_483_647, "retained_bytes": 256,
                                 "context_b64": Data(repeating: 0xff, count: 256).base64EncodedString(),
                                 "context_truncated": true]
    reply["validator_subprocess"] = validator

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

/// Encoded size of the synthesized maximal reply through the production encoder.
func maximalReplyEncodedSize() throws -> Int {
    let fixture = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(try replyFixture())) as! [String: Any]
    var unknown = Set<String>()
    var reply = maximize(fixture, key: nil, unknown: &unknown) as! [String: Any]
    if !unknown.isEmpty { throw Unclassified(keys: unknown) }
    addAbsentOptionalFields(&reply)
    reply["error"] = maximal(8191)

    let count = PWShmLayout.maxSteps
    let step = (reply["steps"] as! [[String: Any]])[0]
    reply["steps"] = Array(repeating: step, count: count)
    var subprocess = reply["runner_subprocess"] as! [String: Any]
    var disposition = subprocess["disposition"] as! [String: Any]
    let entry = (disposition["steps"] as! [[String: Any]])[0]
    disposition["steps"] = (0..<count).map { index -> [String: Any] in
        var copy = entry; copy["index"] = index; return copy
    }
    subprocess["disposition"] = disposition
    reply["runner_subprocess"] = subprocess
    var validator = reply["validator_subprocess"] as! [String: Any]
    validator["records"] = Array(repeating: try maximalRecord(), count: count)
    validator["expected_step_ids"] = Array(repeating: maximal(PWShmLayout.stepIdMax - 1), count: count)
    validator["association_issues"] = Array(repeating: ["origin": "runner_host", "kind": "query_mismatch",
                                                         "step_id": maximal(PWShmLayout.stepIdMax - 1), "count": 1] as [String: Any], count: count)
    validator["probe_bytes_written"] = 2_147_483_647; validator["probe_bytes_expected"] = 2_147_483_647
    validator["stdout_bytes_received"] = 2_147_483_647
    reply["validator_subprocess"] = validator

    let data = try JSONSerialization.data(withJSONObject: reply)
    let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)
    try expectEqual(decoded.steps.count, count)
    return try pwRunnerEncodeJSON(decoded).count
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
            // A key added to the field-complete fixture without a policy fails
            // maximalReplyEncodedSize with the unclassified key names.
            var unknown = Set<String>()
            let fixture = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(try replyFixture())) as! [String: Any]
            _ = maximize(fixture, key: nil, unknown: &unknown)
            try expectTrue(unknown.isEmpty, Unclassified(keys: unknown).description)
            var probe = fixture
            probe["future_reply_string"] = "unclassified"
            _ = maximize(probe, key: nil, unknown: &unknown)
            try expectEqual(unknown, ["future_reply_string"])
        }
    }
}

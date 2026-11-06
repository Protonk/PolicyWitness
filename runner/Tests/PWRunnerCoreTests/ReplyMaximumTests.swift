import Foundation
@testable import PWRunnerCore

// A conservative bound on replies for admitted specimens: the ordinary fixture with
// 256 steps, 256 validator records and disposition entries, every request- or
// host-derived string at its documented limit and made of U+0001 (six JSON bytes
// per byte), the largest worker diagnostic, and the largest slash-heavy
// compiled-profile receipt. The runner client's retention budget is derived from
// this number, and the live max-target workload must stay under it. Separately
// encoded spawn-failure, extension, fresh-read, fresh-write and exec-observation components are added without subtracting
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
    "producer": nil, "capture_stage": nil,
    "abi_identity": nil, "code": nil, "collection_status": nil,
    "original_normalized_outcome": nil, "unavailable_reason": nil,
    "detail": nil, "observations": nil, "rule": nil, "original_error": 8191,
    "extension_class": nil, "stop": nil, "stop_reason": nil, "deadline_kind": nil,
    // Actor form: fixed vocabulary and hashes.
    "execution_form": nil, "mode": nil, "setup_status": nil, "policy_received_sha256": nil, "family": nil,
    "custody_status": nil, "copy_status": nil, "equality": nil, "environment": nil, "standard_streams": nil,
    "cancelled": nil,
    "requested": nil, "resolved": nil, "binding_ref": nil, "binding_id": nil, "role": nil, "source": nil,
    "implementation_identity": nil, "relative_path": 1023, "sha256": nil, "expected_sha256": nil,
    "cdhash": nil, "expected_cdhash": nil, "identifier": 1023, "team_id": 255,
    "entitlements_id": nil, "entitlements_ref": nil, "requirements_status": nil,
    "required_entitlements": 255, "missing_requirements": 255, "raw_plist": 65536,
    "worker_identity": nil, "unsigned_worker_sha256": nil, "publication": nil, "disposition": nil,
    "native_kind": nil, "descriptor": nil, "mapping": nil, "object_name": nil,
    "shared_erasure": nil, "private_erasure": nil, "recovery_state": nil, "name": 31,
    "integrity_errors": nil, "domain": 255, "condition": nil, "source_final_phase_id": 63,
    // Bounded echoes of request strings.
    "specimen_id": specimenIdMaxBytes, "run_kind": requestLabelMaxBytes, "path": 1023,
    "phase_id": requestLabelMaxBytes, "action_ids": PWShmLayout.stepIdMax - 1,
    "step_id": PWShmLayout.stepIdMax - 1, "operation": sandboxCheckOperationMaxBytes,
    "filter_kind": probePlanLabelMaxBytes, "filter_value": sandboxCheckFilterValueMaxBytes,
    "input": sandboxCheckFilterValueMaxBytes, "requested_kind": probePlanLabelMaxBytes,
    "requested_action": probePlanLabelMaxBytes, "requested_path": PWShmLayout.targetMax - 1,
    "parameter_key": PWShmLayout.paramKeyMax - 1, "expected_step_ids": PWShmLayout.stepIdMax - 1,
    "selected": testOverridePathMaxBytes, "unentitled": testOverridePathMaxBytes,
    "worker_executable_path": testOverridePathMaxBytes,
    "validator_executable_path": testOverridePathMaxBytes, "executable_path": testOverridePathMaxBytes,
    "token_ref": PWExtensionLimits.referenceBytes, "handle_ref": PWExtensionLimits.referenceBytes,
    "delivery_ref": PWExtensionLimits.referenceBytes, "actor_id": PWActorLimits.identifierBytes,
    "source_actor_id": PWActorLimits.identifierBytes, "recipient_actor_id": PWActorLimits.identifierBytes,
    "last_use_step_id": PWShmLayout.stepIdMax - 1, "release_step_id": PWShmLayout.stepIdMax - 1,
    "raw_equal_handles": PWExtensionLimits.referenceBytes, "target": PWActorLimits.targetBytes,
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
    // The EOF receipt's counts are bounded by the source capacity and agree with
    // the transfer record's expectation below.
    evidence["policy_read"] = ["bytes_expected": PWShmLayout.policyBytes - 1, "bytes_received": PWShmLayout.policyBytes - 1]
    subprocess["worker_evidence"] = evidence
    subprocess["policy_transfer_timeout"] = ["budget_ms": 5000, "elapsed_ms": UInt64.max,
        "bytes_written": 262143, "bytes_expected": 262143] as [String: Any]
    let maximalWait: [String: Any] = ["budget_ms": Int32.max, "elapsed_ms": UInt64.max, "stop": "sentinel_deadline",
                                      "excluded_ms": UInt64.max, "native_errno": Int32.max, "clock_fault": true]
    for name in ["ready_wait", "sentinel_wait", "exit_grace_wait"] { subprocess[name] = maximalWait }
    reply["runner_subprocess"] = subprocess

    var phases = reply["phases"] as! [[String: Any]]
    var validator = phases[0]["validator_subprocess"] as! [String: Any]
    validator["exit_grace_wait"] = maximalWait
    validator["read_error"] = maximal(1023)
    validator["io_error"] = maximal(1023)
    validator["decode_fault"] = ["origin": "runner_host", "kind": "structure", "message": maximal(1023),
                                 "byte_offset": 2_147_483_647, "frame_bytes": 2_147_483_647, "retained_bytes": 256,
                                 "context_b64": Data(repeating: 0xff, count: 256).base64EncodedString(),
                                 "context_truncated": true]
    phases[0]["validator_subprocess"] = validator
    reply["phases"] = phases

    reply["compiled_profile"] = ["schema_version": 2, "status": "captured", "producer": "worker", "capture_stage": "before_apply", "worker_pid": 4_294_967_295,
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
/// A fresh-read payload beside every ordinary attempt remains bounded after
/// declaration removal. Actor authority records have their separate allowance.
private func extensionReplyAllowance() throws -> Int {
    let identity = PWFileIdentity(device: UInt64.max, inode: UInt64.max,
        mode: UInt32.max, uid: UInt32.max, gid: UInt32.max)
    let fresh = PWRunnerFreshRead(open_rc: Int32.max, open_errno: Int32.max,
        read_rc: Int64(PWExtensionLimits.freshReadBytes), read_errno: Int32.max,
        stat_rc: -1, stat_errno: Int32.max, identity: identity, close_rc: -1, close_errno: Int32.max,
        content_hex: String(repeating: "f", count: PWExtensionLimits.freshReadBytes * 2))
    // Object braces overcount the actual comma joining these members, safely.
    let freshMember = try pwRunnerEncodeJSON(["fresh_read": fresh])
    return PWShmLayout.maxSteps * freshMember.count
}

private func freshWriteReplyAllowance() throws -> Int {
    let identity = PWFileIdentity(device: UInt64.max, inode: UInt64.max,
        mode: UInt32.max, uid: UInt32.max, gid: UInt32.max)
    // Optional success and failure members coexist only in this conservative
    // size account. Int64.min is the widest signed decimal metadata size.
    let metadata = PWRunnerFileStat(rc: -1, errno: Int32.max, identity: identity, size: Int64.min)
    let write = PWRunnerFreshWrite(open_rc: Int32.max, open_errno: Int32.max,
        truncate_rc: -1, truncate_errno: Int32.max, write_rc: -1, write_errno: Int32.max,
        close_rc: -1, close_errno: Int32.max, preopen_stat: metadata,
        opened_stat: metadata, truncated_stat: metadata, written_stat: metadata)
    return PWShmLayout.maxSteps * (try pwRunnerEncodeJSON(["fresh_write": write])).count
}

/// Every optional exec member and widest native scalars, with the longest
/// permitted vocabulary values. Mutually exclusive observations intentionally
/// coexist to upper-bound representation; this is not a reachable transcript.
/// Object braces overcount the comma joining the member into an attempt.
private func execReplyAllowance() throws -> Int {
    let stream = PWExecStreamObservation(eof: false, read_errno: Int32.max, poll_revents: Int32.max)
    let value = PWExecObservation(
        collection: PWExecCollectionObservation(stop_reason: "leader_exit_and_eof", leader_exit_observed: false,
            stdout: stream, stderr: stream, deadline_kind: "child", waitid_errno: Int32.max,
            poll_errno: Int32.max, clock_fault: UInt32.max),
        cleanup: PWExecCleanupObservation(state: "ownership_unconfirmed",
            group_request: PWExecSignalRequest(target: Int32.min, signal: 9, rc: -1, errno: Int32.max),
            leader_fallback: PWExecSignalRequest(target: Int32.max, signal: 9, rc: -1, errno: Int32.max)),
        reap: PWExecReapObservation(stop_reason: "ownership_unconfirmed",
            last_wait: PWExecWaitObservation(rc: Int32.max, errno: Int32.max, status: Int32.min),
            clock_fault: UInt32.max))
    return PWShmLayout.maxSteps * (try pwRunnerEncodeJSON(["exec_observation": value])).count
}

/// Valid evidence on all 256 exec slots goes through the full ordinary reply
/// decoder and encoder as well as the union size account above. No native
/// transcript can contain every optional branch at once; this variant retains
/// two collection errors, failed group/fallback calls and wait/clock faults.
private func encodeAllExecReply(_ original: PWRunnerRunResult) throws -> Data {
    var reply = original
    for index in reply.steps.indices {
        var attempt = reply.steps[index].attempt
        attempt.requested_kind = "exec"; attempt.requested_action = "spawn"
        attempt.child_pid = Int(Int32.max); attempt.child_exit_code = -1; attempt.child_term_signal = 0
        attempt.rc = -1; attempt.errno = Int(Int32.max); attempt.outcome = "exec_failed"
        attempt.exec_observation = PWExecObservation(
            collection: PWExecCollectionObservation(stop_reason: "observation_error", leader_exit_observed: false,
                stdout: PWExecStreamObservation(eof: false, read_errno: Int32.max),
                stderr: PWExecStreamObservation(eof: false, read_errno: Int32.max)),
            cleanup: PWExecCleanupObservation(state: "requested",
                group_request: PWExecSignalRequest(target: -Int32.max, signal: 9, rc: -1, errno: Int32.max),
                leader_fallback: PWExecSignalRequest(target: Int32.max, signal: 9, rc: -1, errno: Int32.max)),
            reap: PWExecReapObservation(stop_reason: "wait_error",
                last_wait: PWExecWaitObservation(rc: -1, errno: Int32.max), clock_fault: UInt32.max))
        try expectTrue(attempt.execObservationEvidenceProblem() == nil)
        reply.steps[index].attempt = attempt
        reply.steps[index].comparison?.observation_basis = "spawned_child"
        reply.steps[index].comparison?.operation_relation = "different"
    }
    let encoded = try pwRunnerEncodeJSON(reply)
    let roundTrip = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: encoded)
    try expectEqual(roundTrip.steps.filter { $0.attempt.exec_observation != nil }.count, PWShmLayout.maxSteps)
    return encoded
}

private func encodeAllFreshWriteReply(_ original: PWRunnerRunResult) throws -> Data {
    var reply = original
    for index in reply.steps.indices {
        var attempt = reply.steps[index].attempt
        let creating = index % 2 == 0
        attempt.requested_kind = "file"; attempt.requested_action = creating ? "create_fresh" : "write_fresh"
        attempt.rc = 0; attempt.errno = nil; attempt.outcome = "ok"
        attempt.child_pid = nil; attempt.child_exit_code = nil; attempt.child_term_signal = nil
        attempt.stdout = nil; attempt.stderr = nil; attempt.exec_observation = nil
        attempt.fresh_read = nil; attempt.fresh_write = freshWriteFixture(creating: creating)
        try expectNil(attempt.freshWriteEvidenceProblem())
        reply.steps[index].attempt = attempt
        reply.steps[index].comparison?.observation = "succeeded"
        reply.steps[index].comparison?.observation_basis = "completed_worker_status"
        reply.steps[index].comparison?.operation_relation = creating ? "unresolved" : "different"
    }
    let encoded = try pwRunnerEncodeJSON(reply)
    let roundTrip = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: encoded)
    try expectEqual(roundTrip.steps.filter { $0.attempt.fresh_write != nil }.count, PWShmLayout.maxSteps)
    return encoded
}

/// Actor components are measured separately: their optional branches may coexist
/// for this representation bound without claiming to form a valid native reply.
/// Every fixture contributes fields, including failure and capture companions.
/// Numeric leaves use 20 decimal bytes (the widest 64-bit native representation),
/// booleans use false, and bounded strings retain the ordinary string policy.
/// Fixed ASCII vocabulary is padded to 128 bytes so an unexercised spelling does
/// not make a shorter successful fixture the bound. The current vocabulary fits
/// this ceiling; a longer fixture spelling requires a deliberate review.
private func actorComponentUnion(_ values: [Any], path: String) throws -> Any {
    let present = values.filter { !($0 is NSNull) }
    guard !present.isEmpty else { return NSNull() }
    let objects = present.compactMap { $0 as? [String: Any] }
    if !objects.isEmpty {
        var result: [String: Any] = [:]
        for key in Set(objects.flatMap { $0.keys }) {
            result[key] = try actorComponentUnion(objects.compactMap { $0[key] }, path: path + "." + key)
        }
        // A disposition value can be an integer or an object. The object union
        // is larger than a 20-byte integer; keep both alternatives accounted for.
        if objects.count != present.count {
            try expectTrue(try JSONSerialization.data(withJSONObject: result).count >= 20,
                           "actor component object must cover its scalar alternative: \(path)")
        }
        return result
    }
    let arrays = present.compactMap { $0 as? [Any] }
    if !arrays.isEmpty {
        let count: Int
        switch path {
        // These arrays are counted once at aggregate capacities below, rather
        // than multiplying a 256-action population by eight actors or phases.
        case "actor.subprocess.disposition.steps", "actor.subprocess.disposition.issues",
             "phase.action_ids", "phase.validator_subprocess.records",
             "phase.validator_subprocess.expected_step_ids", "phase.validator_subprocess.association_issues":
            count = 0
        case "actor.visits": count = PWActorLimits.phases
        case "actor.launch.inherited_descriptors": count = 4
        // ChildProcessState permits two lifetime EINTR retries and at most one
        // terminal failed wait in polling, grace and final reap.
        case "actor.subprocess.wait_errors", "phase.validator_subprocess.wait_errors": count = 5
        case "handle.raw_equal_handles": count = PWActorLimits.handles
        // The current phase and common ordering builders append at most ten
        // distinct protocol violations. Sixteen safely covers their union.
        case "phase.ordering.protocol_violations": count = 16
        case _ where path.hasSuffix(".basis") || path.hasSuffix(".observations"):
            count = PWDisposition.runReferences.count + PWDisposition.stepReferences.count
        default: throw TestFailure(message: "unclassified actor reply array capacity: \(path)")
        }
        if count == 0 { return [Any]() }
        try expectTrue(arrays.allSatisfy { $0.count <= count }, "actor array fixture exceeds its accounted capacity: \(path)")
        var elements = arrays.flatMap { $0 }
        if elements.isEmpty {
            // Success fixtures have no ordering violations or equal handles.
            switch path {
            case "phase.ordering.protocol_violations": elements = ["attempt_or_acknowledgement_after_proceed_failure"]
            case "handle.raw_equal_handles": elements = [maximal(PWExtensionLimits.referenceBytes)]
            default: throw TestFailure(message: "actor reply array has no populated fixture: \(path)")
            }
        }
        let element = try actorComponentUnion(elements, path: path + "[]")
        return Array(repeating: element, count: count)
    }
    if let number = present.first as? NSNumber {
        return CFGetTypeID(number) == CFBooleanGetTypeID() ? (false as Any) : (Int64.min as Any)
    }
    if present.first is String {
        let key = path.split(separator: ".").last!.replacingOccurrences(of: "[]", with: "")
        guard let policy = stringPolicy[key] else { throw Unclassified(keys: [key]) }
        if let bytes = policy { return maximal(bytes) }
        if key == "bytecode_b64" { return Data(repeating: 0xff, count: PWShmLayout.captureBytes).base64EncodedString() }
        if key == "context_b64" { return Data(repeating: 0xff, count: 256).base64EncodedString() }
        for value in present.compactMap({ $0 as? String }) {
            try expectTrue(value.utf8.count <= 128 && value.utf8.allSatisfy { $0 >= 0x20 && $0 < 0x7f },
                           "review actor fixed vocabulary ceiling: \(path)")
        }
        return String(repeating: "v", count: 128)
    }
    throw TestFailure(message: "unclassified actor reply value: \(path)")
}

private func actorReplyComponents(_ documents: [[String: Any]]) throws -> [String: Any] {
    func rows(_ key: String, in objects: [[String: Any]]) -> [[String: Any]] {
        objects.flatMap { ($0[key] as? [[String: Any]]) ?? [] }
    }
    // Equipment/application and gate/setup tables are charged by the bounded
    // consolidation allowance below. Keep ordinary actor payload accounting independent.
    let actors = rows("actors", in: documents).map { row -> [String: Any] in
        var value = row; value.removeValue(forKey: "equipment"); value.removeValue(forKey: "application"); return value
    }
    let subprocesses = actors.compactMap { $0["subprocess"] as? [String: Any] }
    let dispositions = subprocesses.compactMap { $0["disposition"] as? [String: Any] }
    let resources = documents.compactMap { $0["resources"] as? [String: Any] }
    // Ordinary phase companions supply validator and spawn-failure members that
    // actor-shaped no-validator fixtures do not reach. Their variable record
    // arrays remain charged at the aggregate limits in the ordinary base.
    var ordinary = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(try replyFixture())) as! [String: Any]
    addAbsentOptionalFields(&ordinary)
    let phaseDocuments = documents + (try replyShapeDocuments()) + [ordinary]
    let candidates: [String: [Any]] = [
        "actor": actors, "phase": rows("phases", in: phaseDocuments).map { row -> [String: Any] in
            var value = row; value.removeValue(forKey: "termination_gate"); return value
        },
        "event": rows("extension_events", in: documents), "transfer": rows("transfers", in: documents),
        "token": rows("tokens", in: resources), "delivery": rows("deliveries", in: resources),
        "handle": rows("handles", in: resources), "disposition_step": rows("steps", in: dispositions),
        "disposition_issue": rows("issues", in: dispositions),
        "schedule": documents.compactMap { $0["schedule"] }
    ]
    var components: [String: Any] = [:]
    for (name, values) in candidates {
        try expectFalse(values.isEmpty, "actor size component lacks an encoder fixture: \(name)")
        components[name] = try actorComponentUnion(values, path: name)
    }
    guard let actor = components["actor"] as? [String: Any],
          let profile = actor["compiled_profile"] as? [String: Any], profile["bytecode_b64"] is String else {
        throw TestFailure(message: "actor size account requires an encoded captured-profile fixture")
    }
    return components
}

/// The ordinary base already covers 256 attempts, 512 validator records, 768
/// association issues and their identity arrays. Add every actor-specific member
/// without reclaiming any ordinary fields. Disposition entries/issues are also
/// charged here at aggregate capacities to include every actor-only branch.
private func actorReplyAllowance() throws -> Int {
    let components = try actorReplyComponents(actorShapeDocuments())
    func bytes(_ name: String) throws -> Int {
        try JSONSerialization.data(withJSONObject: components[name]!).count + 1
    }
    var total = try JSONSerialization.data(withJSONObject: ["execution_form": "actors", "actors": [],
        "resources": ["tokens": [], "deliveries": [], "handles": []], "transfers": [],
        "extension_events": [], "schedule": [:]] as [String: Any]).count
    total += PWActorLimits.actors * (try bytes("actor"))
    // Count all sixteen phase overhead records, safely retaining the eight in
    // the ordinary base. Heavy validator arrays are counted only there.
    total += PWActorLimits.phases * (try bytes("phase"))
    total += (PWActorLimits.issues + PWActorLimits.deliveries + PWActorLimits.handles + PWActorLimits.releases) * (try bytes("event"))
    total += PWActorLimits.deliveries * (try bytes("transfer"))
    total += PWActorLimits.issues * (try bytes("token"))
    total += PWActorLimits.deliveries * (try bytes("delivery"))
    total += PWActorLimits.handles * (try bytes("handle"))
    total += PWActorLimits.actions * (try bytes("disposition_step"))
    // resolveDisposition has at most one final-status issue per actor and two
    // issue-producing questions per action; count both even when incompatible.
    total += (PWActorLimits.actors + 2 * PWActorLimits.actions) * (try bytes("disposition_issue"))
    total += try bytes("schedule")
    // Count the actor phase action-id population again rather than depending
    // on the ordinary base's eight-phase placement of the same 256 identities.
    total += PWActorLimits.actions * (6 * (PWShmLayout.stepIdMax - 1) + 3)
    // Each ordinary probe result also carries its actor_id in the actor form.
    // The ordinary base's steps lack this member. One removed object brace is
    // replaced by the comma joining the member to the existing step object.
    let actorStepMember = try JSONSerialization.data(withJSONObject:
        ["actor_id": maximal(PWActorLimits.identifierBytes)]).count - 1
    total += PWActorLimits.actions * actorStepMember
    return total
}

/// Independent complete population budget for added setup/equipment/application
/// and termination evidence, including JSON escaping. This is conservative,
/// not a claim that these incompatible outcomes occur in one execution.
private func consolidationReplyAllowance() throws -> Int {
    let setup = 524_288 // at most 388 operation cells plus owner/cleanup metadata
    let readbacks = PWEquipmentLimits.entitlementRecords * PWEquipmentLimits.entitlementBytes * 6
    let requirements = PWActorLimits.actors * 2 * PWActorLimits.requiredEntitlements * (PWActorLimits.entitlementKeyBytes * 6 + 3)
    let identityMetadata = PWEquipmentLimits.entitlementRecords * PWEquipmentLimits.metadataBytes
    let gates = PWActorLimits.phases * 4_096
    let preparation = 4_096
    let envelopeAndApplication = 32_768
    let sum = setup + readbacks + requirements + identityMetadata + gates + preparation + envelopeAndApplication
    let allowance = 8 * 1024 * 1024
    try expectTrue(sum <= allowance, "consolidation populations exceed reserved encoded allowance")
    return allowance
}

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
    let phases = reply["phases"] as! [[String: Any]]
    let validator = phases[0]["validator_subprocess"] as! [String: Any]
    var record = try maximalRecord()
    for (field, bound) in ValidatorReplyLimits.stringBytes { record[field] = maximal(bound) }
    record["raw_line"] = maximal(ValidatorReplyLimits.frameBytes)
    let perPhase = count / PWRunnerPhase.maximumCount
    reply["phases"] = (0..<PWRunnerPhase.maximumCount).map { index -> [String: Any] in
        var phase = phases[0], collection = validator
        let ids = (index * perPhase..<(index + 1) * perPhase).map(identity)
        phase["phase_id"] = identity(index); phase["ordinal"] = index + 1; phase["action_ids"] = ids
        // The largest consistent collection: every record names an action outside
        // the plan, so each expected ID is missing and each record is unexpected.
        let foreign = (0..<(ids.count * ValidatorReplyLimits.recordsPerProbe)).map {
            identity(count + index * ids.count * ValidatorReplyLimits.recordsPerProbe + $0)
        }
        collection["records"] = foreign.map { id -> [String: Any] in var copy = record; copy["step_id"] = id; return copy }
        collection["expected_step_ids"] = ids
        collection["phase_id"] = identity(index); collection["ordinal"] = index + 1
        collection["association_issues"] = ids.map { ["origin": "runner_host", "kind": "missing_id", "step_id": $0, "count": 0] as [String: Any] }
            + foreign.map { ["origin": "runner_host", "kind": "unexpected_id", "step_id": $0, "count": 1] as [String: Any] }
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
    let bound = try pwRunnerEncodeJSON(decoded).count + extensionReplyAllowance() + freshWriteReplyAllowance() + spawnAllowance + execReplyAllowance()
        + actorReplyAllowance() + consolidationReplyAllowance()
    let execBytes = try encodeAllExecReply(decoded)
    try expectTrue(execBytes.count <= bound, "every-slot valid exec reply exceeds conservative representation bound")
    let writeBytes = try encodeAllFreshWriteReply(decoded)
    try expectTrue(writeBytes.count <= bound, "every-slot valid fresh-write reply exceeds conservative representation bound")
    return bound
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
        tk.run("actor size account includes optional companions and requires array capacities") {
            let documents = try actorShapeDocuments()
            let components = try actorReplyComponents(documents)
            let actor = components["actor"] as! [String: Any]
            let process = actor["subprocess"] as! [String: Any]
            let reap = actor["owned_reap"] as! [String: Any]
            for field in ["pid", "native_rc", "raw_status", "stage", "observed_ns", "ownership_unbroken", "departure_requested", "capture_ordinal"] {
                try expectNotNil(reap[field], "owned reap companion escaped actor size account: \(field)")
            }
            let phase = components["phase"] as! [String: Any]
            let activation = phase["activation_observation"] as! [String: Any]
            try expectNotNil(activation["capture_ordinal"])
            try expectNotNil(activation["observed_ns"])
            // Gate/setup/equipment payloads retain the explicit bounded 8 MiB
            // allowance; owned reap and activation are additionally unioned.
            let gates = documents.flatMap { ($0["phases"] as? [[String: Any]]) ?? [] }
                .compactMap { $0["termination_gate"] as? [String: Any] }
            try expectFalse(gates.isEmpty, "termination gate lacks an encoded fixture")
            let references = gates.compactMap { $0["observation"] as? [String: Any] }
            try expectTrue(references.allSatisfy { Set($0.keys) == Set(["capture_ordinal"]) },
                "gate must reference the actor-owned reap instead of duplicating it")
            try expectEqual(try consolidationReplyAllowance(), 8 * 1024 * 1024)
            for field in ["term_signal", "termination_request", "policy_transfer_error", "policy_transfer_timeout"] {
                try expectNotNil(process[field], "failure companion escaped actor size account: \(field)")
            }
            let capture = actor["compiled_profile"] as! [String: Any]
            let bytecode = Data(repeating: 0xff, count: PWShmLayout.captureBytes)
            try expectEqual(capture["bytecode_b64"] as? String, bytecode.base64EncodedString())
            let nativeCapture = CompiledProfileCapture(status: "captured", reason: nil, worker_pid: Int(Int32.max),
                producer: "worker", capture_stage: "before_apply", request_nonce: String(repeating: "f", count: 32),
                profile_type: Int(Int32.max), bytecode_length: bytecode.count,
                bytecode_sha256: String(repeating: "f", count: 64), bytecode_b64: bytecode.base64EncodedString(),
                source_sha256: String(repeating: "f", count: 64), source_length: PWShmLayout.policyBytes - 1,
                params_sha256: String(repeating: "f", count: 64), parameter_count: PWShmLayout.maxParams)
            let actualCaptureBytes = try pwRunnerEncodeJSON(nativeCapture).count
            try expectTrue(try JSONSerialization.data(withJSONObject: capture).count >= actualCaptureBytes,
                           "actor union must cover production encoding of one maximum capture")
            let withoutCaptures = documents.map { document -> [String: Any] in
                var copy = document
                copy["actors"] = (document["actors"] as! [[String: Any]]).map { actor -> [String: Any] in
                    var value = actor; value.removeValue(forKey: "compiled_profile"); return value
                }
                return copy
            }
            try expectThrows({ _ = try actorReplyComponents(withoutCaptures) }, { error in
                try expectContains((error as? TestFailure)?.message ?? "", "requires an encoded captured-profile fixture")
            })
            try expectThrows({ _ = try actorComponentUnion([["future_array": []]] as [Any], path: "actor") }, { error in
                try expectContains((error as? TestFailure)?.message ?? "", "unclassified actor reply array capacity")
            })
            try expectThrows({ _ = try actorComponentUnion([Array(repeating: 0, count: 5)], path: "actor.launch.inherited_descriptors") }, { error in
                try expectContains((error as? TestFailure)?.message ?? "", "exceeds its accounted capacity")
            })
        }
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

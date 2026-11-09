import Foundation
@testable import PWRunnerCore

// Typed dense writer controls and presentation accounting are separate. These
// fixtures exercise the current binary path; they are not a maximum proof for
// every possible evidence graph. Python independently projects their JSON and
// accounts conservative incompatible component unions from all shape receipts.
let maximalParentPathBytes = 1023 + 1 + (PWShmLayout.targetMax - 1)
let maximalFirmlinkPathBytes = 1023 + "/System/Volumes/Data".utf8.count

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
    "contract": nil, "expected_contract": nil, "describe": nil, "commit": nil,
    "abi_identity": nil, "code": nil, "collection_status": nil,
    "original_normalized_outcome": nil, "unavailable_reason": nil,
    "detail": nil, "observations": nil, "rule": nil, "original_error": 8191,
    "extension_class": nil, "stop": nil, "stop_reason": nil, "deadline_kind": nil,
    // Actor form: fixed vocabulary and hashes.
    "execution_form": nil, "mode": nil, "setup_status": nil, "policy_received_sha256": nil, "family": nil,
    "custody_status": nil, "copy_status": nil, "equality": nil, "environment": nil, "standard_streams": nil,
    "cancelled": nil,
    "requested": nil, "resolved": nil, "role": nil, "source": nil,
    "implementation_identity": nil, "relative_path": 1023, "sha256": nil, "expected_sha256": nil,
    "cdhash": nil, "expected_cdhash": nil, "identifier": 1023, "team_id": 255,
    "requirements_status": nil,
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
    let encoded = try admittedReplyData(reply)
    try expectEqual(reply.steps.filter { $0.attempt.exec_observation != nil }.count, PWShmLayout.maxSteps)
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
    let encoded = try admittedReplyData(reply)
    try expectEqual(reply.steps.filter { $0.attempt.fresh_write != nil }.count, PWShmLayout.maxSteps)
    return encoded
}


private func denseReply() throws -> PWRunnerRunResult {
    var reply = try replyFixture()
    let count = PWShmLayout.maxSteps
    let original = reply.steps[0]
    let originalDisposition = reply.runner_subprocess!.disposition!.steps[0]
    reply.steps = (0..<count).map { index in
        var step = original
        step.step_id = "dense-\(index)"
        step.phase_id = "dense-phase-\(index / (count / PWRunnerPhase.maximumCount))"
        step.comparison?.order = "unestablished"
        step.attempt.error = String(repeating: "\u{01}", count: PWShmLayout.errorMax - 1)
        step.attempt.observed_path = String(repeating: "\u{01}", count: PWShmLayout.observedPathMax - 1)
        step.attempt.stdout = String(repeating: "\u{01}", count: PWShmLayout.childOutputBytes - 1)
        step.attempt.stderr = String(repeating: "\u{01}", count: PWShmLayout.childOutputBytes - 1)
        return step
    }
    reply.runner_subprocess!.disposition!.steps = (0..<count).map { index in
        var step = originalDisposition; step.index = index; step.step_id = "dense-\(index)"; return step
    }
    let originalPhase = reply.phases[0]
    reply.phases = (0..<PWRunnerPhase.maximumCount).map { index in
        var phase = originalPhase
        phase.phase_id = "dense-phase-\(index)"; phase.ordinal = index + 1
        phase.action_ids = reply.steps.filter { $0.phase_id == phase.phase_id }.map { $0.step_id }
        phase.validator_subprocess = nil; phase.validator_spawn_failure = nil
        phase.ordering?.validator_disposition = "not_spawned"
        return phase
    }
    try reply.validateForReporting()
    return reply
}

func runReplyMaximumTests(_ tk: TestKit) {
    tk.group("typed dense replies and presentation accounting inputs") {
        tk.run("retain full-capacity ordinary exec and fresh-write binary fixtures") {
            guard let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"] else {
                throw TestFailure(message: "PW_TEST_ARTIFACTS is required for dense receipts")
            }
            let directory = URL(fileURLWithPath: artifacts).appendingPathComponent("porcelain-dense", isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            let reply = try denseReply()
            let receipts = [("ordinary", try admittedReplyData(reply)),
                            ("exec", try encodeAllExecReply(reply)),
                            ("fresh-write", try encodeAllFreshWriteReply(reply))]
            for (name, data) in receipts {
                try expectTrue(data.count < 96_468_992, "dense fixture exceeds host-reply retention")
                try expectTrue(data.count <= pwPorcelainByteLimit, "writer exceeded full frame cap")
                try data.write(to: directory.appendingPathComponent(name + ".pwp"))
            }
            // Only numeric capacities and an authored string classification are
            // exported here; the public evidence projection belongs to Python.
            let policy = stringPolicy.mapValues { $0 as Any? ?? NSNull() }
            let capacities: [String: Int] = [
                "steps": PWShmLayout.maxSteps, "ordinary_phases": PWRunnerPhase.maximumCount,
                "actors": PWActorLimits.actors, "phases": PWActorLimits.phases,
                "issues": PWActorLimits.issues, "deliveries": PWActorLimits.deliveries,
                "handles": PWActorLimits.handles, "releases": PWActorLimits.releases,
                "actions": PWActorLimits.actions, "references": PWDisposition.runReferences.count + PWDisposition.stepReferences.count,
                "capture_bytes": PWShmLayout.captureBytes, "fresh_read_bytes": PWExtensionLimits.freshReadBytes,
                "entitlement_records": PWEquipmentLimits.entitlementRecords,
                "entitlement_bytes": PWEquipmentLimits.entitlementBytes,
                "required_entitlements": PWActorLimits.requiredEntitlements,
                "entitlement_key_bytes": PWActorLimits.entitlementKeyBytes,
                "metadata_bytes": PWEquipmentLimits.metadataBytes,
                "validator_frame": ValidatorReplyLimits.frameBytes,
                "records_per_probe": ValidatorReplyLimits.recordsPerProbe]
            let account: [String: Any] = ["string_policy": policy, "capacities": capacities,
                "validator_strings": ValidatorReplyLimits.stringBytes]
            try JSONSerialization.data(withJSONObject: account, options: [.sortedKeys]).write(
                to: directory.appendingPathComponent("accounting-inputs.json"))
        }
    }
}

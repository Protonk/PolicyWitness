import Foundation
@testable import PWRunnerCore

// Field-complete constructed encoding input, not a claim that an admitted run
// also has an admission failure. Keep every optional the encoder accepts beside
// a completed, ordered step populated here; the keys an ordinary reply cannot
// carry at once (a degraded reply's `reporting_failure`, a synthetic attempt's
// `missing_reason`, a signalled worker's `term_signal`, a slot conflict's
// `issues`, a failed validator spawn) come from the production-shaped documents `replyShapeDocuments()`
// adds beside this one for the reply shape golden.
func replyFixture() throws -> PWRunnerRunResult {
    let value1 = PWRunnerPathDiagnostics(input: "/owned", realpath_resolved: "/private/owned", firmlink_resolved: "/System/Volumes/Data/private/owned", observer: "runner_host", stage: "after_orchestration")
    var value2 = PWRunnerSandboxCheckResult(rc: 0, outcome: "allow", pid: 42, operation: "file-read-data", filter_kind: "path", filter_value: "/owned", filter_type_id: 1, errno: 0, error: "constructed query diagnostic", path_diagnostics: value1)
    value2.result_source = "validator"
    value2.native_rc = 0
    value2.missing_reason = "constructed"
    let value3 = PWRunnerAttemptPathDiagnostics(input: "/owned", realpath_resolved: "/private/owned", parent_realpath_resolved: "/private/owned-parent", observer: "runner_host", stage: "after_orchestration")
    let value4 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value5 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value6 = PWAttemptLifecycle(summary: "completed", boundary: value4, result: value5)
    var value7 = PWRunnerAttemptResult(rc: 0, errno: 0, outcome: "ok", error: "constructed attempt diagnostic", requested_path: "/owned", path_diagnostics: value3, observed_path: "/private/owned", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, stdout: "constructed out", stderr: "constructed err")
    value7.requested_kind = "file"
    value7.requested_action = "open_read"
    value7.result_source = "worker"
    value7.lifecycle = value6
    let value8 = PWRunnerComparison(observation: "succeeded", observation_basis: "completed_worker_status", operation_relation: "matched", target_relation: "same_submitted", order: "query_first", limitations: [])
    let value9 = PWRunnerStepResult(step_id: "s", phase_id: "main", sandbox_check: value2, attempt: value7, comparison: value8)
    let value10 = PWRunnerTerminationRequest(signal: 9, rc: -1, errno: 1)
    let value11 = PWRunnerWaitError(stage: "exit_grace", rc: -1, errno: 10)
    let value12 = PWWorkerReadiness(rc: 1, errno: 0)
    let value13 = PWWorkerDiagnostic(state: 2, status: "truncated", length: 4, text: "text")
    let value14 = PWWorkerPolicyRead(bytes_expected: 1, bytes_received: 1)
    let value15 = PWWorkerEvidence(abi_identity: PWShmLayout.abiIdentityHex, failure_publication: 0, failure_state: "absent", readiness: value12, diagnostic: value13, policy_read: value14)
    let value16 = PWHostWait(budget_ms: 1000, elapsed_ms: 3, stop: "received", excluded_ms: 0, native_errno: 0, clock_fault: false)
    let value17 = PWHostWait(budget_ms: 120000, elapsed_ms: 250, stop: "done", excluded_ms: 40, native_errno: 0, clock_fault: false)
    let value18 = PWHostWait(budget_ms: 1000, elapsed_ms: 1000, stop: "exhausted", excluded_ms: 0, native_errno: 4, clock_fault: true)
    let value19 = PWDispositionClaim(state: "unresolved", reason: "no_successful_reap", basis: ["reaped"])
    let value20 = PWDispositionClaim(state: "supported", answer: "done", basis: ["poll_stop_reason"])
    let value21 = PWDispositionClaim(state: "supported", answer: "completion", basis: ["cleanup_trigger", "exit_requested"])
    let value22 = PWDispositionClaim(state: "supported", answer: "exhausted", basis: ["grace_end", "exit_requested"])
    let value23 = PWRunnerTerminationRequest(signal: 9, rc: -1, errno: 1)
    let value24 = PWDispositionClaim(state: "supported", answer: "requested", value: .request(value23), basis: ["termination_request"])
    let value25 = PWDispositionClaim(state: "supported", answer: "execution_may_continue", basis: ["collection_basis"])
    let value26 = PWDispositionClaim(state: "inapplicable", reason: "no_progress_word")
    let value27 = PWDispositionRunQuestions(final_status: value19, stop_reason: value20, cleanup_trigger: value21, grace_end: value22, kill_request_and_result: value24, collection_basis: value25, progress_association: value26)
    let value28 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value29 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value30 = PWDispositionClaim(state: "supported", answer: "supported", basis: ["attempt_support"])
    let value31 = PWDispositionStepQuestions(step_boundary_reached: value28, step_result_published: value29, step_requested_operation_applicability: value30)
    let value32 = PWDispositionStep(index: 0, step_id: "s", slot: "completed", attempt_support: "supported", questions: value31)
    let value33 = PWDispositionRecord(questions: value27, steps: [value32], issues: [])
    var value34 = PWRunnerSubprocess(pid: 42, partial_steps: false, ready_byte_received: true, done_observed: true, poll_stop_reason: "done", exit_requested: true, termination_request: value10, reaped: false, wait_errors: [value11])
    value34.worker_evidence = value15
    value34.cleanup_trigger = "completion"
    value34.grace_end = "exhausted"
    value34.collection_basis = "execution_may_continue"
    value34.ready_wait = value16
    value34.sentinel_wait = value17
    value34.exit_grace_wait = value18
    value34.disposition = value33
    let value35 = PWRunnerOrdering(collection_closed_before_proceed: true, proceed_set: true, proceed_observed: true, validator_disposition: "reaped", worker_lifetime_established: true, protocol_violations: [])
    let value36 = PWRunnerTerminationRequest(signal: 9, rc: 0, errno: 1)
    let value37 = PWRunnerWaitError(stage: "exit_grace", rc: -1, errno: 10)
    let value38 = PWValidatorDecodeFault(origin: "runner_host", kind: "structure", message: "constructed", byte_offset: 1, frame_bytes: 2, retained_bytes: 2, context_b64: "AA==", context_truncated: false)
    let value39 = ValidatorVerdict(stepId: "s", operation: "file-read-data", filterType: "PATH", filterTypeId: 1, filterValue: "/owned", rc: 0, errnoVal: 0, outcome: "allow", error: "constructed", rawLine: "native record bytes")
    let value40 = ValidatorVerdict(stepId: "extra", operation: "file-read-data", filterType: "PATH", filterTypeId: 1, filterValue: "/elsewhere", rc: 0, errnoVal: 0, outcome: "allow", error: nil, rawLine: "unexpected native record")
    let value41 = PWValidatorAssociationIssue(origin: "runner_host", kind: "unexpected_id", step_id: "extra", count: 1)
    let value42 = PWHostWait(budget_ms: 1000, elapsed_ms: 2, stop: "reaped", excluded_ms: 0, native_errno: 0, clock_fault: false)
    var value43 = PWRunnerValidatorSubprocess(pid: 43, exit_code: 0)
    value43.phase_id = "main"
    value43.ordinal = 1
    value43.reaped = true
    value43.termination_request = value36
    value43.wait_errors = [value37]
    value43.read_error = "constructed read error"
    value43.stdout_collection_stop = "eof"
    value43.stdout_bytes_received = 64
    value43.probe_bytes_written = 32
    value43.probe_bytes_expected = 32
    value43.io_error = "constructed io error"
    value43.decode_fault = value38
    value43.records = [value39, value40]
    value43.expected_step_ids = ["s"]
    value43.association_issues = [value41]
    value43.exit_grace_wait = value42
    let value44 = PWRunnerPhaseResult(phase_id: "main", ordinal: 1, action_ids: ["s"], arrival_observed: true, completion_observed: true, collection_status: "collected", ordering: value35, validator_subprocess: value43)
    let value45 = PWRunnerTestOverrides(worker_executable_path: "/constructed/worker", worker_timeout_ms: 1000, validator_executable_path: "/constructed/validator", validator_io_timeout_ms: 50, validator_total_timeout_ms: 100, worker_post_apply_hang_ms: 0, worker_post_apply_kill_signal: 9, worker_pre_ready_hang_ms: 0, worker_kill_before_publish_slot: 1)
    let value46 = CompiledProfileCapture(schema_version: 2, status: "captured", reason: "constructed", worker_pid: 42, producer: "worker", capture_stage: "before_apply", request_nonce: "ffffffffffffffffffffffffffffffff", profile_type: 0, bytecode_length: 3, bytecode_sha256: "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", bytecode_b64: "AAAA", source_sha256: "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", source_length: 11, params_sha256: "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", parameter_count: 1)
    let value47 = PWRunnerAdmissionFailure(origin: "runner_host", field: "constructed", actual: 2, maximum: 1, unit: "items", step_id: "s", step_index: 0, parameter_key: "K", index: 0)
    let value48 = PWRunnerRequestFailure(code: "unsupported_policy_format", path: ["policy", "format"], expected_schema: 4)
    let value49 = PWRunnerRunResult(schema_version: PWContract.responseSchema, specimen_id: "reply-\"é\"", run_kind: "unit", rc: 1, normalized_outcome: "runner_failed", error: "original cleanup fault", pid: 42, bundle_id: "test.bundle", policy_format: "sbpl", policy_sha256: "hash", sandboxed_after_apply: true, steps: [value9], runner_subprocess: value34, phases: [value44], test_overrides: value45, compiled_profile: value46, admission_failure: value47, request_failure: value48)
    return value49
}

func validatorSpawnFailureFixture() -> PWRunnerSpawnFailure {
    PWRunnerSpawnFailure(executable_path: "/constructed/validator", return_code: 123456,
        diagnostic: "unfamiliar native failure")
}

// Observe the actual reporting boundary before serialization. Binary projection
// is checked independently by the registered Python/Rust receipt readers.
func reportedReply(_ result: PWRunnerRunResult) throws -> PWRunnerRunResult {
    var retained: PWRunnerRunResult?
    _ = pwRunnerPorcelainReplyData(result, encode: { retained = $0; return Data([1]) },
        minimal: { _, _ in throw TestFailure(message: "unexpected minimal fallback") })
    guard let retained else { throw TestFailure(message: "rich reporting did not retain a typed reply") }
    return retained
}

func admittedReplyData(_ result: PWRunnerRunResult) throws -> Data {
    try result.validateForReporting()
    return try pwPorcelainEncode(result)
}

func runReplyFailureTests(_ tk: TestKit) {
    tk.group("typed reply admission and binary failure boundary") {
        tk.run("retain normal rich and minimal binary receipts for independent readers") {
            guard let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"] else {
                throw TestFailure(message: "PW_TEST_ARTIFACTS is required for porcelain receipts")
            }
            let root = URL(fileURLWithPath: artifacts).appendingPathComponent("porcelain-replies", isDirectory: true)
            try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
            let normal = try replyFixture()
            try pwRunnerPorcelainReplyData(normal).write(to: root.appendingPathComponent("normal.pwp"))
            var invalid = normal
            invalid.steps[0].phase_id = "missing"
            try pwRunnerPorcelainReplyData(invalid).write(to: root.appendingPathComponent("rich-failure.pwp"))
            let fail: (PWRunnerRunResult) throws -> Data = { _ in
                throw TestFailure(message: "independent minimal receipt control")
            }
            try pwRunnerPorcelainReplyData(normal, encode: fail).write(to: root.appendingPathComponent("minimal-failure.pwp"))
        }
        tk.run("binary production writer receives an admitted typed reply") {
            let result = try replyFixture()
            try result.validateForReporting()
            try expectEqual(pwRunnerPorcelainReplyData(result), try pwPorcelainEncode(result))
        }
        for defect in ["missing_association", "future_ordinal", "missing_acknowledgement", "failed_reap"] {
            tk.run("typed admission rejects \(defect) before writing and preserves the observations") {
                var result = try replyFixture()
                switch defect {
                case "missing_association": result.steps[0].phase_id = "missing"
                case "future_ordinal": result.phases[0].ordinal = 99
                case "missing_acknowledgement": result.phases[0].ordering?.proceed_observed = false
                default:
                    // A requested signal cannot supply an observed final status.
                    result.runner_subprocess?.disposition?.questions.final_status = PWDispositionClaim(
                        state: "supported", answer: "exit_code", value: .integer(0),
                        basis: ["reaped", "exit_code"])
                }
                do { try result.validateForReporting(); throw TestFailure(message: "unsupported claim admitted") }
                catch is PWRunnerReportingValidationError { }
                var received: PWRunnerRunResult?
                var writerCalls = 0
                let marker = Data([0, 255, 0, 1])
                let emitted = pwRunnerPorcelainReplyData(result, encode: { value in
                    writerCalls += 1
                    received = value
                    return marker
                }, minimal: { _, _ in throw TestFailure(message: "rich evidence unexpectedly discarded") })
                try expectEqual(emitted, marker)
                try expectEqual(writerCalls, 1, "invalid ordinary evidence must not reach the writer")
                guard let degraded = received else { throw TestFailure(message: "missing degraded typed evidence") }
                try expectEqual(degraded.reporting_failure?.evidence_retained, true)
                try expectNil(degraded.steps[0].comparison)
                try expectEqual(degraded.runner_subprocess?.reaped, false)
                try expectNil(degraded.runner_subprocess?.exit_code)
                var expected = result
                expected.schema_version = degraded.schema_version
                expected.rc = degraded.rc
                expected.normalized_outcome = degraded.normalized_outcome
                expected.error = degraded.error
                expected.reporting_failure = degraded.reporting_failure
                for index in expected.steps.indices { expected.steps[index].comparison = nil }
                // Complete typed retention comparison includes every serialized field.
                try expectEqual(try pwPorcelainEncode(degraded), try pwPorcelainEncode(expected))
            }
        }
        tk.run("successful signal with unconfirmed reap stays unresolved") {
            var result = try replyFixture()
            let request = PWRunnerTerminationRequest(signal: 9, rc: 0, errno: 0)
            result.runner_subprocess?.termination_request = request
            result.runner_subprocess?.disposition?.questions.kill_request_and_result?.value = .request(request)
            try result.validateForReporting()
            try expectEqual(result.runner_subprocess?.reaped, false)
            try expectEqual(result.runner_subprocess?.disposition?.questions.final_status?.state, "unresolved")
            try expectNil(result.runner_subprocess?.exit_code)
            try expectNil(result.runner_subprocess?.term_signal)
        }
        for location in ["reply", "actor"] {
            tk.run("invalid \(location) compiled profile context cannot bypass typed admission through degradation") {
                var result = try replyFixture()
                var capture = result.compiled_profile!
                capture.capture_stage = nil
                if location == "reply" {
                    result.compiled_profile = capture
                } else {
                    result.actors = [PWRunnerActorResult(actor_id: "A", index: 0, mode: "apply",
                        policy_format: "sbpl", policy_sha256: nil, policy_received_sha256: nil,
                        setup_status: "applied", applied: true, application_count: 1,
                        launch: nil, subprocess: nil, compiled_profile: capture, visits: [])]
                }
                var writerCalls = 0
                var minimalCalls = 0
                let marker = Data([13, 0, 255])
                let data = pwRunnerPorcelainReplyData(result, encode: { _ in
                    writerCalls += 1
                    throw TestFailure(message: "invalid capture reached writer")
                }, minimal: { original, diagnostic in
                    minimalCalls += 1
                    try expectEqual(original.specimen_id, result.specimen_id)
                    try expectContains(diagnostic, "compiled_profile requires worker/before_apply context")
                    return marker
                })
                try expectEqual(data, marker)
                try expectEqual(writerCalls, 0)
                try expectEqual(minimalCalls, 1)
            }
        }
        tk.run("rich writer failure retains evidence on its second attempt") {
            let result = try replyFixture()
            var calls = 0
            let data = pwRunnerPorcelainReplyData(result, encode: { value in
                calls += 1
                if calls == 1 { throw TestFailure(message: "injected binary writer fault") }
                try expectEqual(value.reporting_failure?.evidence_retained, true)
                try expectEqual(value.reporting_failure?.original_error, result.error)
                try expectEqual(value.phases[0].validator_subprocess?.records?.count,
                    result.phases[0].validator_subprocess?.records?.count)
                try expectNil(value.steps[0].comparison)
                return Data([1, 0, 1])
            })
            try expectEqual(calls, 2)
            try expectEqual(data, Data([1, 0, 1]))
        }
        tk.run("independent minimal binary report survives repeated rich writer failure") {
            let result = try replyFixture()
            var calls = 0
            let bytes = pwRunnerPorcelainReplyData(result, encode: { _ in
                calls += 1
                throw TestFailure(message: "injected binary writer fault")
            })
            try expectEqual(calls, 2)
            try expectTrue(bytes.starts(with: Data("PWP1".utf8)))
            try expectTrue(bytes.count < (try pwPorcelainEncode(result)).count)
        }
        tk.run("minimal emission failure returns an undecodable empty receipt") {
            let result = try replyFixture()
            var richCalls = 0
            var minimalCalls = 0
            let data = pwRunnerPorcelainReplyData(result, encode: { _ in
                richCalls += 1
                throw TestFailure(message: "rich emission failed")
            }, minimal: { original, diagnostic in
                minimalCalls += 1
                try expectEqual(original.specimen_id, result.specimen_id)
                try expectContains(diagnostic, "evidence-preserving encoding also failed")
                throw TestFailure(message: "minimal emission failed")
            })
            try expectEqual(richCalls, 2)
            try expectEqual(minimalCalls, 1)
            try expectTrue(data.isEmpty)
        }
    }
    tk.group("host reply failure contract") {
        tk.run("malformed request diagnostics do not echo unbounded dictionary keys") {
            let key = String(repeating: "é", count: 32_768)
            let malformed: [String: Any] = ["schema_version": PWContract.requestSchema, "specimen_id": "decode",
                "policy": ["format": "sbpl", "sbpl_source": "(version 1)", "params": [key: [1, 2]]],
                "probe_plan": []]
            let data = try JSONSerialization.data(withJSONObject: malformed)
            do {
                _ = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: data)
                throw TestFailure(message: "malformed parameter value decoded")
            } catch let error as DecodingError {
                let diagnostic = requestDecodeDiagnostic(error)
                try expectContains(diagnostic, "type_mismatch")
                try expectContains(diagnostic, "<unreported_key>")
                try expectTrue(diagnostic.utf8.count < 512)
                try expectFalse(diagnostic.contains(key))
            }
        }
        tk.run("maximal slash-heavy profile capture fits the documented encoding allowance") {
            // Constructed bytes test serialization only, not a compiler result.
            // Base64 of 0xff maximizes '/' escaping in Foundation JSON.
            let bytes = Data(repeating: 0xff, count: PWShmLayout.captureBytes)
            let receipt = CompiledProfileCapture(status: "captured", worker_pid: 42,
                producer: "worker", capture_stage: "before_apply",
                request_nonce: String(repeating: "f", count: 32), profile_type: 0,
                bytecode_length: bytes.count, bytecode_sha256: String(repeating: "f", count: 64),
                bytecode_b64: bytes.base64EncodedString(), source_sha256: String(repeating: "f", count: 64),
                source_length: 262_143, params_sha256: String(repeating: "f", count: 64), parameter_count: 1024)
            let allowance = 2 * 4 * ((bytes.count + 2) / 3) + 4096
            let encoded = try pwPorcelainEncode(receipt)
            try expectTrue(encoded.count <= allowance)
            try receipt.validateForReporting()
            let decoded = receipt
            try expectEqual(Data(base64Encoded: decoded.bytecode_b64!), bytes)
            var result = try replyFixture()
            let baseline = try admittedReplyData(result).count
            result.compiled_profile = receipt
            try expectTrue(try admittedReplyData(result).count <= baseline + allowance)
        }
        tk.run("a valid current reply uses the normal encoder unchanged") {
            let result = try replyFixture()
            try expectEqual(pwRunnerPorcelainReplyData(result), try admittedReplyData(result))
        }
        for defect in ["ordering", "comparison", "order", "vocabulary", "lifetime", "association", "pid", "none"] {
            tk.run("reply preserves evidence while withholding claims after \(defect) rejection") {
                var result = try replyFixture()
                switch defect {
                case "ordering": result.phases[0].ordering = nil
                case "comparison": result.steps[0].comparison = nil
                case "order": result.steps[0].comparison?.order = "future_order"
                case "vocabulary":
                    result.steps[0].comparison?.limitations = ["state_stability_unestablished"]
                case "lifetime": result.phases[0].ordering?.worker_lifetime_established = false
                case "association":
                    let duplicate = result.phases[0].validator_subprocess!.records![0]
                    result.phases[0].validator_subprocess?.records?.append(duplicate)
                case "pid": result.steps[0].sandbox_check.pid = 99
                default:
                    result.steps[0].sandbox_check.filter_kind = "none"
                    result.steps[0].sandbox_check.filter_value = "ignored"
                    result.phases[0].validator_subprocess?.records?[0].filterType = "NONE"
                    // A NONE native record must omit its value, unlike the request.
                    result.phases[0].validator_subprocess?.records?[0].filterValue = "not-native"
                }
                do { _ = try admittedReplyData(result); throw TestFailure(message: "invalid ordinary reply accepted") }
                catch is PWRunnerReportingValidationError { }
                let bytes = pwRunnerPorcelainReplyData(result)
                let decoded = try reportedReply(result)
                try expectEqual(decoded.schema_version, PWContract.responseSchema)
                try expectEqual(decoded.normalized_outcome, NormalizedOutcome.runnerReportingFailed)
                try expectEqual(decoded.rc, 1)
                try expectContains(decoded.error ?? "", "runner host could not encode")
                try expectEqual(decoded.reporting_failure?.evidence_retained, true)
                try expectEqual(decoded.reporting_failure?.original_normalized_outcome, result.normalized_outcome)
                try expectEqual(decoded.reporting_failure?.original_rc, result.rc)
                try expectEqual(decoded.reporting_failure?.original_error, result.error)
                try expectNil(decoded.steps[0].comparison)
                // Compare every other field against the degraded reply's own
                // expected shape: the original result with the summary fields
                // and the comparison removed. Nothing else may change.
                var reference = result
                reference.normalized_outcome = NormalizedOutcome.runnerReportingFailed
                reference.rc = 1
                reference.error = decoded.error
                reference.reporting_failure = decoded.reporting_failure
                for index in reference.steps.indices { reference.steps[index].comparison = nil }
                try expectEqual(try pwPorcelainEncode(reference), try pwPorcelainEncode(decoded), "raw evidence or identity changed")
                try expectEqual(try admittedReplyData(decoded), bytes)
            }
        }
        tk.run("failure marker cannot excuse surviving comparison claims or successful summary") {
            var result = try replyFixture()
            result.steps[0].comparison?.limitations = ["state_stability_unestablished"]
            let failure = try reportedReply(result)
            for defect in ["comparison", "outcome", "rc", "diagnostic", "missing_marker"] {
                var bad = failure
                switch defect {
                case "comparison": bad.steps[0].comparison = try replyFixture().steps[0].comparison
                case "outcome": bad.normalized_outcome = "finished"
                case "rc": bad.rc = 0
                case "diagnostic": bad.reporting_failure?.diagnostic = ""
                default: bad.reporting_failure = nil
                }
                do { _ = try admittedReplyData(bad); throw TestFailure(message: "invalid failure exception accepted: \(defect)") }
                catch is PWRunnerReportingValidationError { }
            }
        }
        tk.run("another response number is rejected before binary writing") {
            for version in [PWContract.responseSchema - 1, PWContract.responseSchema + 1, 4] {
                var result = try replyFixture(); result.schema_version = version
                try expectThrows { try result.validateForReporting() }
                let degraded = try reportedReply(result)
                try expectEqual(degraded.schema_version, PWContract.responseSchema)
                try expectEqual(degraded.normalized_outcome, NormalizedOutcome.runnerReportingFailed)
            }
        }
        tk.run("every stored result field is retained in the binary projection receipt") {
            var result = try replyFixture()
            result.extension_events = []
            result.execution_form = "single_worker"
            result.actors = []
            result.transfers = []
            result.resources = PWRunnerResourceTables(tokens: [], deliveries: [], handles: [])
            result.schedule = PWRunnerScheduleRecord(setup_wait: nil, execution_wait: nil, lifetime_budget_ms: PWActorLimits.lifetimeMs,
                                                     collection_budget_ms: PWActorLimits.collectionMs, cancelled: nil)
            // The deliberately degraded broad fixture retains every stored
            // member. It makes no claim that actor apparatus belongs to an
            // ordinary execution or that a refusal coexists with effects.
            result.preparation_failure = PWRunnerPreparationFailure(stage: "equipment", code: "equipment_binding_refused",
                actor_id: "A", binding_ref: "selected", reason: "missing")
            result.equipment_inventory = PWRunnerEquipmentInventory(path: "/constructed/worker-equipment.json", status: "unobserved")
            result.equipment_bindings = []
            result.equipment_entitlements = []
            result.authority_setup = PWRunnerAuthoritySetup(host: PWRunnerAuthorityHost(
                run: PWRunnerAuthorityScope(disposition: "not_attempted")), workers: [])
            result.steps[0].comparison = nil
            let retained = try reportedReply(result)
            try expectEqual(retained.reporting_failure?.evidence_retained, true)
            guard let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"] else {
                throw TestFailure(message: "PW_TEST_ARTIFACTS is required")
            }
            try admittedReplyData(retained).write(to: URL(fileURLWithPath: artifacts)
                .appendingPathComponent("porcelain-replies/populated.pwp"))
        }
    }
}

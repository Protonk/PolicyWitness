import Foundation
@testable import PWRunnerCore

private let policy: [String: Any] = ["format": "sbpl", "sbpl_source": "(version 1)(allow default)"]

private func request(block: Any? = nil, contract: String = PWBuildContext.contract) -> Data {
    var value: [String: Any] = ["contract": contract, "specimen_id": "experimental", "policy": policy, "probe_plan": []]
    if let block { value["_test_overrides"] = block }
    return try! JSONSerialization.data(withJSONObject: value)
}

private func json(_ value: Any) -> Data { try! JSONSerialization.data(withJSONObject: value) }

private func refusal(_ request: Data, _ controls: Data) throws -> PWRunnerRequestFailure {
    do {
        _ = try decodeExperimentalSubmission(request, controls: controls)
    } catch let failure as PWRunnerRequestFailure {
        return failure
    } catch {
        return requestDecodeFailure(error)
    }
    throw TestFailure(message: "admitted: \(String(decoding: controls, as: UTF8.self))")
}

/// The refusal of one request through the ordinary call's decoder.
private func ordinaryRefusal(_ request: Data) throws -> PWRunnerRequestFailure {
    do {
        _ = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: request)
    } catch let failure as PWRunnerRequestFailure {
        return failure
    } catch {
        return requestDecodeFailure(error)
    }
    throw TestFailure(message: "admitted: \(String(decoding: request, as: UTF8.self))")
}

private let controlNames = ["worker_timeout_ms", "worker_pre_ready_hang_ms", "worker_post_apply_hang_ms",
                            "worker_post_apply_kill_signal", "worker_kill_before_publish_slot",
                            "validator_executable_path", "validator_io_timeout_ms", "validator_total_timeout_ms"]

private func reserve(_ service: PWRunnerService) -> String {
    var result: PWRunnerControlReply?
    let bytes = try! pwRunnerEncodeJSON(PWRunnerReservationRequest(attempt_id: UUID().uuidString, lease_ms: 5000))
    service.reserveRunner(bytes) { result = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: $0) }
    return result!.reservation_id!
}

/// One submission through the service with orchestration observed instead of run.
private struct Observed {
    var admitted: [PWRunnerRunSpec] = []
    var validators: [String] = []
    var replies: [PWRunnerRunResult] = []
    var exits = 0
}

private func submit(_ request: Data, controls: Data?) -> Observed {
    var observed = Observed()
    let service = PWRunnerService(admission: PWRunnerAdmission(), scheduleExit: { observed.exits += 1 },
        scheduleExpiry: { _, _ in }, report: { observed.replies.append($0); return pwRunnerPorcelainReplyData($0) },
        orchestrate: { admitted, _, _, _, validator in
            observed.admitted.append(admitted.request); observed.validators.append(validator)
            return PWRunnerRunResult(specimen_id: admitted.request.specimen_id, rc: 0,
                normalized_outcome: NormalizedOutcome.finished, pid: Int(getpid()), policy_format: "sbpl", steps: [],
                test_overrides: admitted.request._test_overrides)
        })
    let token = reserve(service)
    if let controls { service.runReservedExperiment(request, controls: controls, reservation: token) { _, _ in } }
    else { service.runReservedSpecimen(request, reservation: token) { _, _ in } }
    return observed
}

func runExperimentalSubmissionTests(_ tk: TestKit) {
    tk.group("experimental submission admission") {
        tk.run("the controls object yields the record its members name and changes nothing else in the request") {
            let blocks: [[String: Any]] = [
                [:],
                ["worker_timeout_ms": 7000], ["worker_pre_ready_hang_ms": 400], ["worker_post_apply_hang_ms": 60001],
                ["worker_post_apply_kill_signal": 32], ["worker_kill_before_publish_slot": 256],
                ["validator_executable_path": "/nonexistent/validator"], ["validator_executable_path": ""],
                ["validator_io_timeout_ms": 0], ["validator_total_timeout_ms": -1],
                ["worker_timeout_ms": Int.max, "worker_kill_before_publish_slot": Int.min],
                ["worker_timeout_ms": NSNull(), "validator_io_timeout_ms": 500],
                ["worker_timeout_ms": 200, "worker_pre_ready_hang_ms": 1, "worker_post_apply_hang_ms": 2,
                 "worker_post_apply_kill_signal": 9, "worker_kill_before_publish_slot": 0,
                 "validator_executable_path": "relative path \u{e9}", "validator_io_timeout_ms": 3,
                 "validator_total_timeout_ms": 4],
            ]
            let plain = try pwRunnerEncodeJSON(try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: request()))
            for block in blocks {
                // The record holds every member given a value; a null member is absent.
                let expected = block.filter { !($0.value is NSNull) }
                // The request's own block may be absent, null or empty beside the controls.
                for own in [nil, NSNull(), [String: Any]()] as [Any?] {
                    var experimental = try decodeExperimentalSubmission(request(block: own), controls: json(block))
                    guard let supplied = experimental._test_overrides else {
                        throw TestFailure(message: "an empty controls object is still a supplied record: \(block)")
                    }
                    let record = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(supplied)) as! NSDictionary
                    try expectTrue(record.isEqual(to: expected), "\(block)")
                    experimental._test_overrides = nil
                    try expectEqual(try pwRunnerEncodeJSON(experimental), plain, "\(block)")
                }
            }
            // The whole record, not only its encoding: each member the orchestrators read.
            let full = try decodeExperimentalSubmission(request(), controls: json(blocks.last!))._test_overrides!
            try expectEqual(full.worker_timeout_ms, 200); try expectEqual(full.worker_pre_ready_hang_ms, 1)
            try expectEqual(full.worker_post_apply_hang_ms, 2); try expectEqual(full.worker_post_apply_kill_signal, 9)
            try expectEqual(full.worker_kill_before_publish_slot, 0)
            try expectEqual(full.validator_executable_path, "relative path \u{e9}")
            try expectEqual(full.validator_io_timeout_ms, 3); try expectEqual(full.validator_total_timeout_ms, 4)
            try expectNil(full.worker_executable_path); try expectNil(full.actor_equipment_executable_paths)
        }
        tk.run("the controls object is closed and typed, and a refusal is located under the override block") {
            let longKey = String(repeating: "k", count: 64)
            let cases: [(String, String, [String]?)] = [
                (#"{"misspelled_control": 1}"#, "unknown_field", ["_test_overrides", "misspelled_control"]),
                (#"{"worker_timeout_ms": 5, "a_first_unknown": 1, "z_unknown": 2}"#, "unknown_field", ["_test_overrides", "a_first_unknown"]),
                ("{\"\(longKey)\": 1}", "unknown_field", nil),
                // The record's other two members belong to an ordinary request's block.
                (#"{"worker_executable_path": "/worker"}"#, "inapplicable_field", ["_test_overrides", "worker_executable_path"]),
                (#"{"worker_executable_path": null}"#, "inapplicable_field", ["_test_overrides", "worker_executable_path"]),
                (#"{"actor_equipment_executable_paths": {"selected": "/x"}, "worker_timeout_ms": 5}"#, "inapplicable_field",
                 ["_test_overrides", "actor_equipment_executable_paths"]),
                (#"{"worker_timeout_ms": "5"}"#, "type_mismatch", ["_test_overrides", "worker_timeout_ms"]),
                (#"{"worker_timeout_ms": 1.5}"#, "type_mismatch", ["_test_overrides", "worker_timeout_ms"]),
                (#"{"worker_timeout_ms": true}"#, "type_mismatch", ["_test_overrides", "worker_timeout_ms"]),
                (#"{"worker_timeout_ms": 9223372036854775808}"#, "type_mismatch", ["_test_overrides", "worker_timeout_ms"]),
                (#"{"worker_kill_before_publish_slot": -9223372036854775809}"#, "type_mismatch",
                 ["_test_overrides", "worker_kill_before_publish_slot"]),
                (#"{"validator_io_timeout_ms": []}"#, "type_mismatch", ["_test_overrides", "validator_io_timeout_ms"]),
                (#"{"validator_executable_path": 7}"#, "type_mismatch", ["_test_overrides", "validator_executable_path"]),
                (#"{"validator_executable_path": {"path": "/x"}}"#, "type_mismatch", ["_test_overrides", "validator_executable_path"]),
                ("[]", "type_mismatch", ["_test_overrides"]),
                (#""worker_timeout_ms""#, "type_mismatch", ["_test_overrides"]),
                ("7", "type_mismatch", ["_test_overrides"]),
                ("", "invalid_json", ["_test_overrides"]),
                (#"{"worker_timeout_ms": 5"#, "invalid_json", ["_test_overrides"]),
            ]
            for (controls, code, path) in cases {
                let failure = try refusal(request(), Data(controls.utf8))
                try expectEqual(failure.code, code, controls)
                try expectEqual(failure.path, path, controls)
                try expectNil(failure.expected_contract, controls)
                try expectTrue(failure.description.utf8.count < 256 && !failure.description.contains(longKey), controls)
                _ = try pwPorcelainEncode(failure)
            }
            // Null is not an object: the submission names its controls even when there are none.
            let null = try refusal(request(), Data("null".utf8))
            try expectEqual(null.code, "missing_value"); try expectEqual(null.path, ["_test_overrides"])
        }
        tk.run("a request block with any member is refused at the block, beside any controls") {
            let blocks: [[String: Any]] = [
                ["worker_timeout_ms": 5000], ["validator_executable_path": "/validator"],
                ["worker_executable_path": "/worker"], ["worker_timeout_ms": NSNull()],
                ["worker_executable_path": NSNull()],
                ["worker_executable_path": "/worker", "validator_executable_path": "/validator"],
            ]
            for block in blocks {
                for controls in [[:], ["worker_timeout_ms": 7000]] as [[String: Any]] {
                    let failure = try refusal(request(block: block), json(controls))
                    try expectEqual(failure.code, "inapplicable_field", "\(block)")
                    try expectEqual(failure.path, ["_test_overrides"], "\(block)")
                }
            }
            // The block's own closed-object and container rules are reached first.
            var failure = try refusal(request(block: ["misspelled_control": 1]), json([String: Any]()))
            try expectEqual(failure.code, "unknown_field"); try expectEqual(failure.path, ["_test_overrides", "misspelled_control"])
            failure = try refusal(request(block: "wrong type"), json([String: Any]()))
            try expectEqual(failure.code, "type_mismatch"); try expectEqual(failure.path, ["_test_overrides"])
        }
        tk.run("the contract and the request are decoded before the controls") {
            let badControls = Data(#"{"misspelled_control": 1}"#.utf8)
            var failure = try refusal(request(contract: "test:foreign"), badControls)
            try expectEqual(failure.code, "unsupported_contract"); try expectEqual(failure.path, ["contract"])
            try expectEqual(failure.expected_contract, PWBuildContext.contract)
            failure = try refusal(Data("{".utf8), badControls)
            try expectEqual(failure.code, "invalid_json"); try expectEqual(failure.path, [])
            var unknown = try JSONSerialization.jsonObject(with: request()) as! [String: Any]
            unknown["experimental_controls"] = ["worker_timeout_ms": 5]
            failure = try refusal(json(unknown), json([String: Any]()))
            try expectEqual(failure.code, "unknown_field"); try expectEqual(failure.path, ["experimental_controls"])
        }
    }
    tk.group("ordinary submission and the experimental controls") {
        tk.run("each control in an ordinary request's block is refused, whatever its value") {
            try expectEqual(PWRunnerTestOverrides.experimentalControls.map { $0.stringValue }, controlNames)
            // A value that would act, values the host would not forward, null, and values of another type.
            let values: [Any] = [5000, 0, -1, NSNull(), "/validator", "", 1.5, true, [1], ["nested": 1]]
            for name in controlNames {
                for value in values {
                    let failure = try ordinaryRefusal(request(block: [name: value]))
                    try expectEqual(failure.code, "inapplicable_field", "\(name): \(value)")
                    try expectEqual(failure.path, ["_test_overrides", name], "\(name): \(value)")
                    try expectNil(failure.expected_contract, name)
                    _ = try pwPorcelainEncode(failure)
                }
            }
        }
        tk.run("the refusal names the first control in the declared order, before any member's type") {
            var failure = try ordinaryRefusal(request(block: ["validator_total_timeout_ms": 1, "worker_post_apply_hang_ms": 2000]))
            try expectEqual(failure.code, "inapplicable_field")
            try expectEqual(failure.path, ["_test_overrides", "worker_post_apply_hang_ms"])
            // Beside a member the block keeps, and beside one of that member's type faults.
            failure = try ordinaryRefusal(request(block: ["worker_executable_path": "/worker", "worker_timeout_ms": 5000]))
            try expectEqual(failure.code, "inapplicable_field"); try expectEqual(failure.path, ["_test_overrides", "worker_timeout_ms"])
            failure = try ordinaryRefusal(request(block: ["worker_executable_path": 7, "validator_io_timeout_ms": NSNull()]))
            try expectEqual(failure.code, "inapplicable_field"); try expectEqual(failure.path, ["_test_overrides", "validator_io_timeout_ms"])
            // The block's closed-object rule and the request's earlier fields are reached first.
            failure = try ordinaryRefusal(request(block: ["misspelled_control": 1, "worker_timeout_ms": 5000]))
            try expectEqual(failure.code, "unknown_field"); try expectEqual(failure.path, ["_test_overrides", "misspelled_control"])
            failure = try ordinaryRefusal(request(block: ["worker_timeout_ms": 5000], contract: "test:foreign"))
            try expectEqual(failure.code, "unsupported_contract"); try expectEqual(failure.path, ["contract"])
            var early = try JSONSerialization.jsonObject(with: request(block: ["worker_timeout_ms": 5000])) as! [String: Any]
            early["policy"] = "not a policy"
            failure = try ordinaryRefusal(json(early))
            try expectEqual(failure.code, "type_mismatch"); try expectEqual(failure.path, ["policy"])
        }
        tk.run("the block's own two members, an empty block and no block are admitted") {
            let kept: [[String: Any]] = [
                [:], ["worker_executable_path": "/worker"], ["worker_executable_path": NSNull()],
                ["actor_equipment_executable_paths": ["selected": "/equipment"]],
                ["worker_executable_path": "/worker", "actor_equipment_executable_paths": ["unentitled": "/equipment"]],
            ]
            for block in kept {
                let parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: request(block: block))
                guard let record = parsed._test_overrides else { throw TestFailure(message: "block dropped: \(block)") }
                let encoded = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(record)) as! NSDictionary
                try expectTrue(encoded.isEqual(to: block.filter { !($0.value is NSNull) }), "\(block)")
            }
            try expectNil(try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: request(block: NSNull()))._test_overrides)
            try expectNil(try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: request())._test_overrides)
        }
    }
    tk.group("experimental submission through the service") {
        tk.run("the experimental call admits its controls and the ordinary call carries none") {
            let controls: [String: Any] = ["worker_timeout_ms": 200, "validator_executable_path": "/nonexistent/explicit-validator"]
            let experimental = submit(request(), controls: json(controls))
            try expectEqual(experimental.admitted.count, 1); try expectEqual(experimental.exits, 1)
            try expectEqual(experimental.admitted[0]._test_overrides?.worker_timeout_ms, 200)
            try expectEqual(experimental.validators, ["/nonexistent/explicit-validator"])
            try expectEqual(experimental.replies[0].test_overrides?.worker_timeout_ms, 200)
            try expectEqual(experimental.replies[0].test_overrides?.validator_executable_path, "/nonexistent/explicit-validator")
            // No controls: an empty record is echoed, where an ordinary call without a block echoes none.
            let empty = submit(request(), controls: Data("{}".utf8))
            try expectNotNil(empty.admitted[0]._test_overrides); try expectNotNil(empty.replies[0].test_overrides)
            try expectEqual(empty.validators, [CWorkerOrchestrator.defaultValidatorExecutablePath()])
            let plain = submit(request(), controls: nil)
            try expectNil(plain.admitted[0]._test_overrides); try expectNil(plain.replies[0].test_overrides)
            try expectEqual(plain.validators, empty.validators)
        }
        tk.run("a refused block or controls object consumes the host before admission or orchestration") {
            let refused: [(Data, Data, String, [String]?)] = [
                (request(block: ["worker_timeout_ms": 5000]), Data("{}".utf8), "inapplicable_field", ["_test_overrides"]),
                (request(), Data(#"{"worker_timeout_ms": 1.5}"#.utf8), "type_mismatch", ["_test_overrides", "worker_timeout_ms"]),
                (request(), Data(#"{"worker_executable_path": "/worker"}"#.utf8), "inapplicable_field",
                 ["_test_overrides", "worker_executable_path"]),
                (request(), Data(), "invalid_json", ["_test_overrides"]),
            ]
            for (bytes, controls, code, path) in refused {
                let observed = submit(bytes, controls: controls)
                try expectTrue(observed.admitted.isEmpty, code); try expectEqual(observed.exits, 1)
                let reply = observed.replies[0]
                try expectEqual(reply.normalized_outcome, NormalizedOutcome.badRequest)
                try expectEqual(reply.request_failure?.code, code); try expectEqual(reply.request_failure?.path, path)
                try expectEqual(reply.specimen_id, "<decode_failed>"); try expectNil(reply.test_overrides)
                try expectTrue(reply.steps.isEmpty && reply.phases.isEmpty && reply.runner_subprocess == nil)
            }
        }
        tk.run("an ordinary call whose block holds a control consumes the host before admission or orchestration") {
            for name in controlNames {
                for value in [1, NSNull()] as [Any] {
                    let observed = submit(request(block: [name: value]), controls: nil)
                    try expectTrue(observed.admitted.isEmpty && observed.validators.isEmpty, name)
                    try expectEqual(observed.exits, 1, name)
                    let reply = observed.replies[0]
                    try expectEqual(reply.normalized_outcome, NormalizedOutcome.badRequest, name)
                    try expectEqual(reply.request_failure?.code, "inapplicable_field", name)
                    try expectEqual(reply.request_failure?.path, ["_test_overrides", name], name)
                    try expectEqual(reply.specimen_id, "<decode_failed>"); try expectNil(reply.test_overrides, name)
                    try expectTrue(reply.steps.isEmpty && reply.phases.isEmpty && reply.runner_subprocess == nil, name)
                }
            }
            // The worker substitution alone still reaches orchestration through the ordinary call.
            let kept = submit(request(block: ["worker_executable_path": "/nonexistent/worker"]), controls: nil)
            try expectEqual(kept.admitted.count, 1)
            try expectEqual(kept.admitted[0]._test_overrides?.worker_executable_path, "/nonexistent/worker")
            try expectEqual(kept.validators, [CWorkerOrchestrator.defaultValidatorExecutablePath()])
            try expectEqual(kept.replies[0].test_overrides?.worker_executable_path, "/nonexistent/worker")
        }
        tk.run("the validator control keeps the path bound, the C-string rule and the withheld echo") {
            let atBound = "/" + String(repeating: "v", count: testOverridePathMaxBytes - 1)
            let admitted = submit(request(), controls: json(["validator_executable_path": atBound]))
            try expectEqual(admitted.validators, [atBound])
            for (value, unit) in [(atBound + "v", "utf8_bytes"), ("/tmp/v\u{0}x", "nul_bytes")] {
                let observed = submit(request(), controls: json(["validator_executable_path": value, "worker_timeout_ms": 200]))
                try expectTrue(observed.admitted.isEmpty, unit)
                let reply = observed.replies[0]
                try expectEqual(reply.normalized_outcome, NormalizedOutcome.badRequest)
                try expectEqual(reply.admission_failure?.field, "_test_overrides.validator_executable_path")
                try expectEqual(reply.admission_failure?.unit, unit)
                try expectEqual(reply.request_failure?.code, "admission_refused")
                try expectEqual(reply.request_failure?.path, ["_test_overrides", "validator_executable_path"])
                // The refused string is not echoed; the control beside it is.
                try expectNil(reply.test_overrides?.validator_executable_path)
                try expectEqual(reply.test_overrides?.worker_timeout_ms, 200)
                try expectFalse((reply.error ?? "").contains(value))
            }
        }
    }
}

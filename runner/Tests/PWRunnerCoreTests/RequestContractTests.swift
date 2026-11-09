import Foundation
@testable import PWRunnerCore

private func requestFixture() -> [String: Any] {
    ["contract": testRequestContract, "specimen_id": "request-contract", "run_kind": "experiment",
     "policy": ["format": "sbpl", "sbpl_source": "(version 1) (allow default)",
                "params": ["arbitrary_parameter": "value"], "capture_compiled_profile": true,
                "capture_nonce": "0123456789abcdef0123456789abcdef"],
     "probe_plan": [["step_id": "s", "sandbox_check": ["operation": "process-exec",
                       "filter": ["kind": "path", "value": "/bin/echo"]],
                      "attempt": ["kind": "exec", "action": "spawn", "target": "/bin/echo", "args": ["hello"]]]],
     "_test_overrides": ["worker_executable_path": "/worker", "worker_timeout_ms": 1000,
                         "validator_executable_path": "/validator", "validator_io_timeout_ms": 500,
                         "worker_post_apply_hang_ms": 0, "worker_post_apply_kill_signal": 0,
                         "worker_pre_ready_hang_ms": 0, "worker_kill_before_publish_slot": 1]]
}

private func replacing(_ node: Any, at path: [String], with value: Any) -> Any {
    guard let head = path.first else { return value }
    if var array = node as? [Any], let index = Int(head) {
        array[index] = replacing(array[index], at: Array(path.dropFirst()), with: value)
        return array
    }
    var object = node as! [String: Any]
    object[head] = replacing(object[head] ?? NSNull(), at: Array(path.dropFirst()), with: value)
    return object
}

private func decodeRequest(_ object: Any) throws -> PWRunnerRunSpec {
    try testDecodeJSON(PWRunnerRunSpec.self, from: JSONSerialization.data(withJSONObject: object))
}

func runRequestContractTests(_ tk: TestKit) {
    tk.group("developer request examples through the runner boundary") {
        tk.run("shared executable teaching corpus") {
            let url = repositoryRoot().appendingPathComponent("tests/fixtures/request_contract/examples.json")
            let examples = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [[String: Any]]
            for example in examples {
                var request = example["request"] as! [String: Any]
                assertExampleContract(example, request: &request)
                if let count = example["repeat_steps"] as? Int {
                    let step = (request["probe_plan"] as! [[String: Any]])[0]
                    request["probe_plan"] = (0..<count).map { index -> [String: Any] in
                        var copy = step; copy["step_id"] = "s\(index)"; return copy
                    }
                }
                if let count = example["repeat_phase_actions"] as? Int {
                    let phases = request["phases"] as! [[String: Any]]
                    let step = (phases[0]["actions"] as! [[String: Any]])[0]
                    let actions = (0..<count).map { index -> [String: Any] in
                        var copy = step; copy["step_id"] = "s\(index)"; return copy
                    } + Array((phases[0]["actions"] as! [[String: Any]]).dropFirst())
                    request["phases"] = (0..<8).map { index -> [String: Any] in
                        ["phase_id": "p\(index)", "actions": Array(actions[(index * 32)..<(index == 7 ? actions.count : (index + 1) * 32)])]
                    }
                }
                let encoded = try JSONSerialization.data(withJSONObject: request)
                let text = (example["raw_request"] as? String ?? String(decoding: encoded, as: UTF8.self))
                    .replacingOccurrences(of: "$EFFECT", with: "/private/tmp/request-grammar-effect")
                    .replacingOccurrences(of: "$NONCE", with: "0123456789abcdef0123456789abcdef")
                let failure: PWRunnerRequestFailure?
                do {
                    let parsed = try testDecodeJSON(PWRunnerRunSpec.self, from: Data(text.utf8))
                    switch admitSpecimen(parsed) {
                    case .accepted: failure = nil
                    case .capacity(let capacity): failure = requestCapacityFailure(capacity, parsed: parsed)
                    case .refused(let refusal): failure = refusal
                    }
                } catch { failure = requestDecodeFailure(error) }
                let expectations = example["expected"] as! [String: Any]
                // Capability refusals occur after admission in the live host.
                let expected = expectations["admission"] ?? expectations["xpc"]!
                let name = example["id"] as! String
                if expected is NSNull { try expectNil(failure, name) }
                else {
                    guard let failure else { throw TestFailure(message: "\(name): expected refusal") }
                    let want = expected as! [String: Any]
                    try expectEqual(failure.code, want["code"] as? String, name)
                    try expectEqual(failure.path, want["path"] as? [String], name)
                    try expectEqual(failure.expected_contract, want["expected_contract"] == nil ? nil : testRequestContract, name)
                    _ = try pwPorcelainEncode(failure)
                }
            }
        }
    }
    tk.group("accepted request contract") {
        tk.run("actor parameter refusals retain policy ownership and safe keys") {
            func request(_ params: [[String: String]]) throws -> PWRunnerRunSpec {
                try decodeRequest([
                    "contract": testRequestContract, "specimen_id": "actor-parameters",
                    "actors": params.enumerated().map { index, values -> [String: Any] in
                        ["actor_id": "a\(index)", "sandbox": ["mode": "apply", "policy": [
                            "format": "sbpl", "sbpl_source": "(version 1) (allow default)", "params": values]]]
                    },
                    "phases": params.indices.map { ["phase_id": "p\($0)", "actor_id": "a\($0)", "actions": []] as [String: Any] }
                ])
            }
            let exactKey = String(repeating: "é", count: 63) + "x" // 127 UTF-8 bytes.
            let exactValue = String(repeating: "é", count: 191) + "x" // 383 bytes.
            try expectNil(CWorkerOrchestrator.admissionFailure(for: request([[exactKey: exactValue], ["K": "ok"]])))
            for (value, actual, maximum, unit) in [(exactValue + "x", 384, 383, "utf8_bytes"), ("bad\0value", 1, 0, "nul_bytes")] {
                // The same key in multiple policies cannot identify its owner;
                // actor order wins before sorted keys in a later policy.
                let parsed = try request([[exactKey: "ok"], ["z": value, exactKey: value], ["a": value]])
                guard let refused = CWorkerOrchestrator.admissionFailure(for: parsed) else { throw TestFailure(message: "value admitted") }
                try expectEqual(refused.field, "actors.1.sandbox.policy.value")
                try expectEqual(refused.actual, actual); try expectEqual(refused.maximum, maximum)
                try expectEqual(refused.unit, unit)
                // ASCII z sorts before é, independently of insertion order.
                try expectEqual(refused.parameter_key, "z")
                let reply = admissionRefusalReply(parsed: parsed, refused: refused, bundleId: nil)
                try expectEqual(reply.request_failure?.path, ["actors", "1", "sandbox", "policy", "params", "z"])
                try expectEqual(reply.steps.count, 0)
                let safe = try request([["K": "ok"], [exactKey: value]])
                let safeRecord = CWorkerOrchestrator.admissionFailure(for: safe)!
                let safeReply = admissionRefusalReply(parsed: safe, refused: safeRecord, bundleId: nil)
                try expectEqual(safeReply.admission_failure?.parameter_key, exactKey)
                try expectNil(safeReply.request_failure?.path) // Path components have a separate 63-byte cap.
                for keyBytes in [63, 64] {
                    let key = String(repeating: "k", count: keyBytes)
                    let bounded = try request([["K": "ok"], [key: value]])
                    let record = CWorkerOrchestrator.admissionFailure(for: bounded)!
                    let path = admissionRefusalReply(parsed: bounded, refused: record, bundleId: nil).request_failure?.path
                    if keyBytes == 63 { try expectEqual(path, ["actors", "1", "sandbox", "policy", "params", key]) }
                    else { try expectNil(path) }
                }
            }
            for key in [exactKey + "x", "bad\0key"] {
                let parsed = try request([["K": "ok"], [key: "bad\0value"]])
                let refused = CWorkerOrchestrator.admissionFailure(for: parsed)!
                try expectEqual(refused.field, "key")
                try expectNil(refused.parameter_key)
                try expectNil(admissionRefusalReply(parsed: parsed, refused: refused, bundleId: nil).request_failure?.path)
            }
            let counted = try request([["K": "ok"], Dictionary(uniqueKeysWithValues:
                (0..<1025).map { ("K\($0)", "bad\0value") })])
            let countRecord = CWorkerOrchestrator.admissionFailure(for: counted)!
            try expectEqual(countRecord.field, "actors.1.sandbox.policy.params")
            try expectEqual(countRecord.actual, 1025); try expectEqual(countRecord.maximum, 1024)
            try expectNil(countRecord.parameter_key)
            try expectEqual(requestCapacityFailure(countRecord, parsed: counted).path, ["actors", "1", "sandbox", "policy", "params"])
            let legacy = try decodeRequest(replacing(requestFixture(), at: ["policy", "params"], with: ["K": "bad\0value"]))
            let legacyRecord = CWorkerOrchestrator.admissionFailure(for: legacy)!
            try expectEqual(legacyRecord.field, "value")
            try expectEqual(requestCapacityFailure(legacyRecord, parsed: legacy).path, ["policy", "params", "K"])
        }
        tk.run("all declared input fields round-trip without losing supplied intent") {
            let input = requestFixture()
            let decoded = try decodeRequest(input)
            let encoded = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(decoded)) as! NSDictionary
            try expectTrue(encoded.isEqual(to: input))
        }
        tk.run("versions are gated before interpreting unknown fields") {
            for version in ["test:foreign", "", "unbound"] {
                var input = requestFixture()
                input["contract"] = version
                input["future_field"] = true
                do {
                    _ = try decodeRequest(input)
                    throw TestFailure(message: "unsupported version accepted: \(version)")
                } catch let failure as PWRunnerRequestFailure {
                    try expectEqual(failure.code, "unsupported_contract")
                    try expectEqual(failure.expected_contract, testRequestContract)
                }
            }
        }
        tk.run("wrong version types and missing required fields are explicit errors") {
            for value in ["3", true, NSNull(), 3.5] as [Any] {
                try expectThrows { _ = try decodeRequest(replacing(requestFixture(), at: ["contract"], with: value)) }
            }
            var input = requestFixture(); input.removeValue(forKey: "contract")
            try expectThrows { _ = try decodeRequest(input) }
            input = requestFixture(); input.removeValue(forKey: "probe_plan")
            try expectThrows { _ = try decodeRequest(input) }
        }
        tk.run("unknown fields fail at every request object including test overrides") {
            let paths = [[], ["policy"], ["probe_plan", "0"], ["probe_plan", "0", "sandbox_check"],
                         ["probe_plan", "0", "sandbox_check", "filter"], ["probe_plan", "0", "attempt"],
                         ["_test_overrides"]]
            for path in paths {
                let input = replacing(requestFixture(), at: path + ["misspelled_intent"], with: true)
                do {
                    _ = try decodeRequest(input)
                    throw TestFailure(message: "unknown field accepted at \(path)")
                } catch let error as RequestContractError {
                    let diagnostic = requestDecodeDiagnostic(error)
                    try expectContains(diagnostic, "unknown_field")
                    try expectContains(diagnostic, "misspelled_intent")
                    if path.contains("0") { try expectContains(diagnostic, "[0]") }
                    let failure = requestDecodeFailure(error)
                    try expectEqual(failure.code, "unknown_field")
                    try expectEqual(failure.path, path + ["misspelled_intent"])
                }
            }
        }
        tk.run("parameter names remain open data and unknown names have bounded diagnostics") {
            let key = String(repeating: "é", count: 32_768)
            let parameter = replacing(requestFixture(), at: ["policy", "params"], with: ["future_field": "value"])
            try expectEqual(try decodeRequest(parameter).policy?.params?["future_field"], "value")
            do {
                _ = try decodeRequest(replacing(requestFixture(), at: ["policy", key], with: true))
                throw TestFailure(message: "unknown field accepted")
            } catch let error as RequestContractError {
                let diagnostic = requestDecodeDiagnostic(error)
                try expectContains(diagnostic, "<unreported_key>")
                try expectTrue(diagnostic.utf8.count < 512)
                try expectNil(requestDecodeFailure(error).path)
            }
        }
        tk.run("optional nulls preserve defaults and wrong optional types cannot disappear") {
            var input = requestFixture()
            input["run_kind"] = NSNull(); input["_test_overrides"] = NSNull()
            input["policy"] = ["format": "sbpl", "sbpl_source": "(version 1)", "params": NSNull()]
            let decoded = try decodeRequest(input)
            try expectNil(decoded.run_kind); try expectNil(decoded._test_overrides)
            try expectNil(decoded.policy?.params)
            for path in [["policy", "params"], ["probe_plan", "0", "attempt", "args"], ["_test_overrides"]] {
                try expectThrows { _ = try decodeRequest(replacing(requestFixture(), at: path, with: "wrong type")) }
            }
        }
        tk.run("resource limits remain admission rules separate from structural decoding") {
            var input = requestFixture()
            let step = (input["probe_plan"] as! [[String: Any]])[0]
            for count in [PWShmLayout.maxSteps, PWShmLayout.maxSteps + 1] {
                input["probe_plan"] = (0..<count).map { i -> [String: Any] in
                    var item = step; item["step_id"] = "s\(i)"; return item
                }
                let decoded = try decodeRequest(input)
                let refusal = CWorkerOrchestrator.admissionFailure(for: decoded)
                if count == PWShmLayout.maxSteps { try expectNil(refusal) }
                else { try expectEqual(refusal?.field, "probe_plan") }
            }
        }
        tk.run("controller-only selection is rejected by direct XPC decoding") {
            for name in ["runner", "runner_id", "runner_service", "required_entitlements", "runner_mode"] {
                do {
                    _ = try decodeRequest(replacing(requestFixture(), at: [name], with: NSNull()))
                    throw TestFailure(message: "controller field accepted: \(name)")
                } catch let error as RequestContractError {
                    try expectContains(requestDecodeDiagnostic(error), name)
                }
            }
        }
    }
}

let testRequestContract = "test:request"
func testDecodeJSON<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
    let decoder = JSONDecoder()
    decoder.userInfo[.expectedContract] = testRequestContract
    return try decoder.decode(type, from: data)
}

func assertExampleContract(_ example: [String: Any], request: inout [String: Any]) {
    switch example["assertion"] as? String {
    case "foreign": request["contract"] = "test:foreign"
    case "number": request["contract"] = 6
    case "fraction": request["contract"] = 6.5
    case "null": request["contract"] = NSNull()
    case "missing": request.removeValue(forKey: "contract")
    default: request["contract"] = testRequestContract
    }
}

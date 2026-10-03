import Foundation
@testable import PWRunnerCore

private func requestFixture() -> [String: Any] {
    ["schema_version": PWContract.requestSchema, "specimen_id": "request-contract", "run_kind": "experiment",
     "policy": ["format": "sbpl", "sbpl_source": "(version 1) (allow default)",
                "params": ["arbitrary_parameter": "value"], "capture_applied_profile": true,
                "capture_nonce": "0123456789abcdef0123456789abcdef"],
     "probe_plan": [["step_id": "s", "sandbox_check": ["operation": "process-exec",
                       "filter": ["kind": "path", "value": "/bin/echo"]],
                      "attempt": ["kind": "exec", "action": "spawn", "target": "/bin/echo", "args": ["hello"]]]],
     "_test_overrides": ["worker_executable_path": "/worker", "worker_timeout_ms": 1000,
                         "validator_executable_path": "/validator", "validator_io_timeout_ms": 500,
                         "worker_post_apply_hang_ms": 0, "worker_post_apply_kill_signal": 0,
                         "worker_pre_ready_hang_ms": 0]]
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
    try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: JSONSerialization.data(withJSONObject: object))
}

func runRequestContractTests(_ tk: TestKit) {
    tk.group("developer request examples through the runner boundary") {
        tk.run("shared executable teaching corpus") {
            let url = repositoryRoot().appendingPathComponent("tests/fixtures/request_contract/examples.json")
            let examples = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [[String: Any]]
            for example in examples {
                var request = example["request"] as! [String: Any]
                if let count = example["repeat_steps"] as? Int {
                    let step = (request["probe_plan"] as! [[String: Any]])[0]
                    request["probe_plan"] = (0..<count).map { index -> [String: Any] in
                        var copy = step; copy["step_id"] = "s\(index)"; return copy
                    }
                }
                let encoded = try JSONSerialization.data(withJSONObject: request)
                let text = (example["raw_request"] as? String ?? String(decoding: encoded, as: UTF8.self))
                    .replacingOccurrences(of: "$EFFECT", with: "/private/tmp/request-grammar-effect")
                    .replacingOccurrences(of: "$NONCE", with: "0123456789abcdef0123456789abcdef")
                let failure: PWRunnerRequestFailure?
                do {
                    let parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: Data(text.utf8))
                    if let capacity = CWorkerOrchestrator.admissionFailure(for: parsed) {
                        failure = requestCapacityFailure(capacity)
                    } else { failure = requestMeaningFailure(parsed) }
                } catch { failure = requestDecodeFailure(error) }
                let expected = (example["expected"] as! [String: Any])["xpc"]!
                let name = example["id"] as! String
                if expected is NSNull { try expectNil(failure, name) }
                else {
                    guard let failure else { throw TestFailure(message: "\(name): expected refusal") }
                    let actual = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(failure)) as! NSDictionary
                    try expectTrue(actual.isEqual(to: expected as! [String: Any]), "\(name): \(actual) != \(expected)")
                }
            }
        }
    }
    tk.group("accepted request contract") {
        tk.run("all declared input fields round-trip without losing supplied intent") {
            let input = requestFixture()
            let decoded = try decodeRequest(input)
            let encoded = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(decoded)) as! NSDictionary
            try expectTrue(encoded.isEqual(to: input))
        }
        tk.run("versions are gated before interpreting unknown fields") {
            for version in Array(-1..<PWContract.requestSchema) + [PWContract.requestSchema + 1, Int.max] {
                var input = requestFixture()
                input["schema_version"] = version
                input["future_field"] = true
                do {
                    _ = try decodeRequest(input)
                    throw TestFailure(message: "unsupported version accepted: \(version)")
                } catch RequestContractError.unsupportedSchema(let actual) {
                    try expectEqual(actual, version)
                    try expectContains(requestDecodeDiagnostic(RequestContractError.unsupportedSchema(actual)),
                                       "expected \(PWContract.requestSchema)")
                }
            }
        }
        tk.run("wrong version types and missing required fields are explicit errors") {
            for value in ["3", true, NSNull(), 3.5] as [Any] {
                try expectThrows { _ = try decodeRequest(replacing(requestFixture(), at: ["schema_version"], with: value)) }
            }
            var input = requestFixture(); input.removeValue(forKey: "schema_version")
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
            try expectEqual(try decodeRequest(parameter).policy.params?["future_field"], "value")
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
            try expectNil(decoded.policy.params)
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

import Foundation
@testable import PWRunnerCore

// docs/contract.json is the only hand-edited copy of the wire contract
// versions. The generated Swift copies are text; this compares the compiled
// values against the manifest so a stale or hand-edited region cannot ship.
private struct ContractManifest: Decodable {
    struct Versions: Decodable {
        let request_schema: Int
        let response_schema: Int
        let worker_abi: Int
        let controller_envelope: Int
    }
    let versions: Versions
}

func repositoryRoot() -> URL {
    URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
}

// Reply shape golden: tests/fixtures/contract/response_shape.json records, per
// object path, every key of the field-complete reply fixture and its JSON type.
// Any change fails until the golden is replaced; a removed key or a changed
// type also requires a response bump, because readers of the previous number
// would misread the reply. Added keys need no bump: absent means unknown.
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

private func collectShape(_ object: [String: Any], path: String, into shape: inout [String: [String: String]]) {
    var keys: [String: String] = [:]
    for (key, value) in object {
        keys[key] = jsonType(value)
        let child = path + "." + key
        if let nested = value as? [String: Any] {
            collectShape(nested, path: child, into: &shape)
        } else if let array = value as? [Any], let first = array.first as? [String: Any] {
            collectShape(first, path: child + "[]", into: &shape)
        }
    }
    shape[path] = keys
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
            try expectEqual(Int(PWShmLayout.abiVersion), manifest.versions.worker_abi)
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
        tk.run("reply shape golden agrees with the manifest") {
            let goldenURL = root.appendingPathComponent("tests/fixtures/contract/response_shape.json")
            let encoded = try pwRunnerEncodeJSON(try replyFixture())
            let object = try JSONSerialization.jsonObject(with: encoded) as! [String: Any]
            var current: [String: [String: String]] = [:]
            collectShape(object, path: "reply", into: &current)
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

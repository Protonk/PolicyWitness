import Foundation
@testable import PWRunnerCore

func runPathDiagnosticsTests(_ tk: TestKit) {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    tk.group("path diagnostics wire states and byte identity") {
        tk.run("shared valid and malformed fixtures decode and re-encode without evidence loss") {
            let data = try Data(contentsOf: root.appendingPathComponent("tests/fixtures/contract/path_diagnostics.json"))
            let rows = try JSONSerialization.jsonObject(with: data) as! [[String: Any]]
            for row in rows {
                let name = row["name"] as! String
                let path = row["path"] as! [String: Any]
                let bytes = try JSONSerialization.data(withJSONObject: path)
                if row["valid"] as! Bool {
                    let decoded = try pwRunnerDecodeJSON(PWRunnerPathDiagnostics.self, from: bytes)
                    let expected = row["values"] as! [String: Any]
                    // Swift String equality normalizes Unicode; compare bytes here.
                    for (key, actual) in [("realpath_resolved", decoded.realpath_resolved),
                                          ("firmlink_resolved", decoded.firmlink_resolved)] {
                        try expectEqual(actual.map { Array($0.utf8) },
                            (expected[key] as? String).map { Array($0.utf8) }, name + ": " + key)
                    }
                    let wire = try pwRunnerEncodeJSON(decoded)
                    let raw = try JSONSerialization.jsonObject(with: wire) as! [String: Any]
                    try expectEqual(Set(raw.keys), Set(path.keys), name)
                    // JSONSerialization dictionary equality also normalizes strings.
                    // A sorted reserialization compares the actual encoded bytes.
                    try expectEqual(try JSONSerialization.data(withJSONObject: raw, options: [.sortedKeys]),
                        try JSONSerialization.data(withJSONObject: path, options: [.sortedKeys]), name)
                } else {
                    do {
                        _ = try pwRunnerDecodeJSON(PWRunnerPathDiagnostics.self, from: bytes)
                        throw TestFailure(message: name + ": malformed diagnostics accepted")
                    } catch is DecodingError { }
                }
            }
        }
        tk.run("new observations compact only byte-identical forms in all nine states") {
            let input = "/caf\u{e9}"
            let values: [String?] = [input, "/cafe\u{301}", nil]
            for real in values {
                for firmlink in values {
                    let original = PWRunnerPathDiagnostics(input: input,
                        realpath_resolved: real, firmlink_resolved: firmlink)
                    let data = try pwRunnerEncodeJSON(original)
                    let raw = try JSONSerialization.jsonObject(with: data) as! [String: Any]
                    let same = raw["same_as_input"] as! [String]
                    let decoded = try pwRunnerDecodeJSON(PWRunnerPathDiagnostics.self, from: data)
                    for (name, value, recovered) in [("realpath_resolved", real, decoded.realpath_resolved),
                                                    ("firmlink_resolved", firmlink, decoded.firmlink_resolved)] {
                        let identical = value.map { Array($0.utf8) == Array(input.utf8) } ?? false
                        try expectEqual(same.contains(name), identical)
                        try expectEqual(raw[name] == nil, identical)
                        try expectEqual(recovered.map { Array($0.utf8) }, value.map { Array($0.utf8) })
                    }
                }
            }
        }
        tk.run("response version prevents a missing compact marker from posing as legacy") {
            var raw = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(try replyFixture())) as! [String: Any]
            var steps = raw["steps"] as! [[String: Any]]
            var query = steps[0]["sandbox_check"] as! [String: Any]
            query["path_diagnostics"] = ["input": "/old"]
            steps[0]["sandbox_check"] = query; raw["steps"] = steps
            for version in [8, 9] {
                raw["schema_version"] = version
                let bytes = try JSONSerialization.data(withJSONObject: raw)
                if version == 8 {
                    let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
                    let encoded = try pwRunnerEncodeJSON(decoded)
                    let recovered = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: encoded)
                    try expectNil(recovered.steps[0].sandbox_check.path_diagnostics?.realpath_resolved)
                    var upgraded = decoded; upgraded.schema_version = 9
                    do {
                        _ = try pwRunnerEncodeJSON(upgraded)
                        throw TestFailure(message: "legacy omission emitted as response 9")
                    } catch is EncodingError { }
                } else {
                    do {
                        _ = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
                        throw TestFailure(message: "missing response-9 marker accepted")
                    } catch is DecodingError { }
                }
            }
        }
    }
}

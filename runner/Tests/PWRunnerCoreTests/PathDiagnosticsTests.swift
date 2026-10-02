import Foundation
@testable import PWRunnerCore

func runPathDiagnosticsTests(_ tk: TestKit) {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    tk.group("path diagnostics wire states and byte identity") {
        tk.run("composed host paths can exceed the realpath buffer without escaping the reply bound") {
            let fm = FileManager.default
            let root = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("pw-long-parent-\(UUID().uuidString)")
            try fm.createDirectory(at: root, withIntermediateDirectories: true)
            defer { try? fm.removeItem(at: root) }
            var parent = root
            while parent.path.utf8.count < 850 {
                parent.appendPathComponent(String(repeating: "d", count: 100))
            }
            try fm.createDirectory(at: parent, withIntermediateDirectories: true)
            let link = root.appendingPathComponent("link")
            try fm.createSymbolicLink(at: link, withDestinationURL: parent)
            let leaf = String(repeating: "x", count: 240)
            let input = link.path + "/" + leaf
            try expectTrue(input.utf8.count < PWShmLayout.targetMax, "target must pass admission")
            guard let resolved = parentRealpathResolved(input),
                  let realParent = canonicalizePath(parent.path).resolved else {
                throw TestFailure(message: "long parent must resolve")
            }
            try expectEqual(resolved, realParent + "/" + leaf)
            try expectTrue(resolved.utf8.count > 1023, "composition exceeds realpath's limit")
            try expectTrue(resolved.utf8.count <= maximalParentPathBytes, "maximal reply covers the composed path")
            // Firmlink substitution also adds bytes after realpath has finished.
            let basis = "/private/" + String(repeating: "x", count: 1023 - "/private/".utf8.count)
            guard let mapped = firmlinkResolved(basis) else { throw TestFailure(message: "standard firmlink missing") }
            try expectTrue(mapped.utf8.count > 1023)
            try expectTrue(mapped.utf8.count <= maximalFirmlinkPathBytes)
            // Fail visibly if this host's system mappings need a larger bound.
            if let table = try? String(contentsOfFile: "/usr/share/firmlinks", encoding: .utf8) {
                for row in table.split(separator: "\n") {
                    guard let source = row.split(separator: "\t").first,
                          let mapped = firmlinkResolved(String(source)) else { continue }
                    try expectTrue(mapped.utf8.count - source.utf8.count <= maximalFirmlinkPathBytes - 1023,
                                   "system firmlink expansion exceeds the synthesized allowance")
                }
            }
            let forms = PWRunnerAttemptPathDiagnostics(input: input, realpath_resolved: nil,
                parent_realpath_resolved: resolved, observer: "runner_host", phase: "after_orchestration")
            let decoded = try pwRunnerDecodeJSON(PWRunnerAttemptPathDiagnostics.self, from: pwRunnerEncodeJSON(forms))
            try expectEqual(decoded.parent_realpath_resolved, .some(resolved))
        }
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
        tk.run("a query block without the compact marker is rejected at the reply") {
            var raw = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(try replyFixture())) as! [String: Any]
            var steps = raw["steps"] as! [[String: Any]]
            var query = steps[0]["sandbox_check"] as! [String: Any]
            query["path_diagnostics"] = ["input": "/old", "realpath_resolved": "/private/old"]
            steps[0]["sandbox_check"] = query; raw["steps"] = steps
            do {
                _ = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: raw))
                throw TestFailure(message: "missing compact marker accepted")
            } catch is DecodingError { }
        }
    }

    tk.group("attempt path diagnostics: shared wire rule and host resolution") {
        tk.run("attempt forms compact only byte-identical forms and require the marker") {
            let input = "/caf\u{e9}"
            let values: [String?] = [input, "/cafe\u{301}", nil]
            for real in values {
                for parent in values {
                    let original = PWRunnerAttemptPathDiagnostics(input: input, realpath_resolved: real,
                        parent_realpath_resolved: parent, observer: "runner_host", phase: "after_orchestration")
                    let data = try pwRunnerEncodeJSON(original)
                    let raw = try JSONSerialization.jsonObject(with: data) as! [String: Any]
                    let same = raw["same_as_input"] as! [String]
                    let decoded = try pwRunnerDecodeJSON(PWRunnerAttemptPathDiagnostics.self, from: data)
                    for (name, value, recovered) in [("realpath_resolved", real, decoded.realpath_resolved),
                                                    ("parent_realpath_resolved", parent, decoded.parent_realpath_resolved)] {
                        let identical = value.map { Array($0.utf8) == Array(input.utf8) } ?? false
                        try expectEqual(same.contains(name), identical)
                        try expectEqual(raw[name] == nil, identical)
                        try expectEqual(recovered.map { Array($0.utf8) }, value.map { Array($0.utf8) })
                    }
                    try expectTrue(Set(raw.keys).isSubset(of: ["observer", "phase", "input", "same_as_input",
                        "realpath_resolved", "parent_realpath_resolved"]), "unexpected attempt form keys")
                }
            }
            let malformed: [[String: Any]] = [
                ["input": "/x"],
                ["input": "/x", "same_as_input": ["firmlink_resolved"]],
                ["input": "/x", "same_as_input": ["realpath_resolved"], "realpath_resolved": "/x", "parent_realpath_resolved": NSNull()],
            ]
            for row in malformed {
                do {
                    _ = try pwRunnerDecodeJSON(PWRunnerAttemptPathDiagnostics.self, from: try JSONSerialization.data(withJSONObject: row))
                    throw TestFailure(message: "malformed attempt diagnostics accepted: \(row)")
                } catch is DecodingError { }
            }
        }
        tk.run("host resolution follows the leaf, resolves the parent and skips non-path attempts") {
            let fm = FileManager.default
            let root = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("pw-attempt-paths-\(getpid())")
            try? fm.removeItem(at: root)
            try fm.createDirectory(at: root.appendingPathComponent("real"), withIntermediateDirectories: true)
            defer { try? fm.removeItem(at: root) }
            try fm.createSymbolicLink(at: root.appendingPathComponent("link"), withDestinationURL: root.appendingPathComponent("real"))
            try Data("x".utf8).write(to: root.appendingPathComponent("real/file"))
            try fm.createSymbolicLink(at: root.appendingPathComponent("real/leaf"), withDestinationURL: root.appendingPathComponent("real/file"))
            guard let realRoot = canonicalizePath(root.path).resolved else { throw TestFailure(message: "temp root unresolvable") }
            func step(_ kind: String, _ action: String, _ target: String, query: String? = nil) -> PWRunnerStepResult {
                var attempt = PWRunnerAttemptResult(rc: 1, errno: 1, outcome: AttemptOutcome.openFailed,
                    error: "constructed", requested_path: target)
                attempt.requested_kind = kind
                attempt.requested_action = action
                let check = PWRunnerSandboxCheckResult(rc: 0, outcome: "allow", pid: 42, operation: "file-read-data",
                    filter_kind: query == nil ? "global-name" : PWRunnerWire.sandboxFilterPath,
                    filter_value: query ?? "com.example.svc", filter_type_id: nil, errno: nil, error: nil, path_diagnostics: nil)
                return PWRunnerStepResult(step_id: target, sandbox_check: check, attempt: attempt)
            }
            let link = root.path + "/link"
            let enriched = enrichPathDiagnostics(steps: [
                step("file", "open_read", link + "/file", query: link + "/file"),
                step("file", "create", link + "/new"),
                step("file", "unlink", link + "/leaf"),
                step("exec", "spawn", link + "/file"),
                step("mach_lookup", "bootstrap_look_up", "com.example.svc"),
                step("file", "open_read", "relative/file"),
            ])
            let forms = enriched.map { $0.attempt.path_diagnostics }
            try expectEqual(forms[0]?.realpath_resolved, .some(realRoot + "/real/file"))
            try expectEqual(forms[0]?.parent_realpath_resolved, .some(realRoot + "/real/file"))
            try expectEqual(forms[0]?.observer, .some("runner_host"))
            try expectEqual(forms[0]?.phase, .some("after_orchestration"))
            // A missing leaf has no leaf-followed form; the parent form names what a create would touch.
            try expectNil(forms[1]?.realpath_resolved)
            try expectEqual(forms[1]?.parent_realpath_resolved, .some(realRoot + "/real/new"))
            // A symlink leaf: realpath follows it, the parent form names the link itself.
            try expectEqual(forms[2]?.realpath_resolved, .some(realRoot + "/real/file"))
            try expectEqual(forms[2]?.parent_realpath_resolved, .some(realRoot + "/real/leaf"))
            try expectEqual(forms[3]?.realpath_resolved, .some(realRoot + "/real/file"))
            try expectNil(forms[4])
            try expectNotNil(forms[5])
            try expectNil(forms[5]?.realpath_resolved)
            try expectNil(forms[5]?.parent_realpath_resolved)
            // The query block keeps its own observation beside the attempt block.
            try expectEqual(enriched[0].sandbox_check.path_diagnostics?.realpath_resolved, .some(realRoot + "/real/file"))
            try expectNil(enriched[1].sandbox_check.path_diagnostics)
            let wire = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(enriched[4])) as! [String: Any]
            try expectNil((wire["attempt"] as! [String: Any])["path_diagnostics"])
            try expectNil((wire["attempt"] as! [String: Any])["normalized_path"])
        }
    }
}

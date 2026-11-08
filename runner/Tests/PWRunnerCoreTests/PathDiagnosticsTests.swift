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
                parent_realpath_resolved: resolved, observer: "runner_host", stage: "after_orchestration")
            _ = try pwPorcelainEncode(forms)
            let decoded = forms
            try expectEqual(decoded.parent_realpath_resolved, .some(resolved))
        }
        tk.run("all nine query and attempt path states retain exact UTF-8 in binary receipts") {
            guard let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"] else {
                throw TestFailure(message: "PW_TEST_ARTIFACTS is required")
            }
            let directory = URL(fileURLWithPath: artifacts).appendingPathComponent("porcelain-paths", isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            let input = "/caf\u{e9}"
            let values: [String?] = [input, "/cafe\u{301}", nil]
            for (i, first) in values.enumerated() {
                for (j, second) in values.enumerated() {
                    var reply = try replyFixture()
                    reply.steps[0].sandbox_check.path_diagnostics = PWRunnerPathDiagnostics(input: input,
                        realpath_resolved: first, firmlink_resolved: second, observer: "runner_host", stage: "after_orchestration")
                    reply.steps[0].attempt.path_diagnostics = PWRunnerAttemptPathDiagnostics(input: input,
                        realpath_resolved: first, parent_realpath_resolved: second, observer: "runner_host", stage: "after_orchestration")
                    try expectEqual(reply.steps[0].sandbox_check.path_diagnostics?.realpath_resolved.map { Array($0.utf8) }, first.map { Array($0.utf8) })
                    try expectEqual(reply.steps[0].attempt.path_diagnostics?.parent_realpath_resolved.map { Array($0.utf8) }, second.map { Array($0.utf8) })
                    // This is a codec fixture, not a claim that these constructed
                    // diagnostics describe the native targets in replyFixture.
                    try pwPorcelainEncode(reply).write(to: directory.appendingPathComponent("\(i)-\(j).pwp"))
                }
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
            try expectEqual(forms[0]?.stage, .some("after_orchestration"))
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
            _ = try pwPorcelainEncode(enriched[4])
            try expectNil(enriched[4].attempt.path_diagnostics)
        }
    }
}

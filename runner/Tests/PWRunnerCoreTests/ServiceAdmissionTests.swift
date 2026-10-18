import Foundation
@testable import PWRunnerCore

private final class AdmissionObservations {
    let lock = NSLock()
    var entries = 0
    var exits = 0
    var replies: [PWRunnerRunResult] = []
    func entry() { lock.lock(); entries += 1; lock.unlock() }
    func exit() { lock.lock(); exits += 1; lock.unlock() }
    func reply(_ data: Data) { lock.lock(); defer { lock.unlock() }
        replies.append(try! pwRunnerDecodeJSON(PWRunnerRunResult.self, from: data)) }
}

func runServiceAdmissionTests(_ tk: TestKit) {
    tk.group("host single use admission") {
        let request = try! pwRunnerEncodeJSON(PWRunnerRunSpec(specimen_id: "admission",
            policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)(allow default)"), probe_plan: []))
        func service(_ state: PWRunnerAdmission, _ observations: AdmissionObservations,
                     entered: DispatchSemaphore? = nil, release: DispatchSemaphore? = nil) -> PWRunnerService {
            PWRunnerService(admission: state, scheduleExit: { observations.exit() }, orchestrate: { parsed, hash, bundle, _, validator in
                observations.entry(); entered?.signal()
                if let release { _ = release.wait(timeout: .now() + 5) }
                return CWorkerOrchestrator.run(parsed: parsed, policyHash: hash, bundleId: bundle,
                    workerExecutablePath: "/nonexistent/pw-admission-control", validatorExecutablePath: validator)
            })
        }
        tk.run("distinct services refuse while owner is held and after reply without scheduling exit") {
            let state = PWRunnerAdmission(), observed = AdmissionObservations()
            let entered = DispatchSemaphore(value: 0), release = DispatchSemaphore(value: 0)
            let finished = DispatchSemaphore(value: 0)
            let owner = service(state, observed, entered: entered, release: release)
            let other = service(state, observed) // Opening an idle connection claims nothing.
            DispatchQueue.global().async { owner.runSpecimen(request, withReply: observed.reply); finished.signal() }
            defer { release.signal() }
            try expectEqual(entered.wait(timeout: .now() + 5), .success)
            other.runSpecimen(request, withReply: observed.reply)
            try expectEqual(observed.entries, 1)
            try expectEqual(observed.exits, 0, "refusal must not retire the active owner")
            try expectEqual(observed.replies.first?.normalized_outcome, NormalizedOutcome.alreadyRan)
            release.signal()
            try expectEqual(finished.wait(timeout: .now() + 5), .success)
            other.runSpecimen(request, withReply: observed.reply)
            try expectEqual(observed.entries, 1)
            try expectEqual(observed.exits, 1)
            try expectEqual(observed.replies.filter { $0.normalized_outcome == NormalizedOutcome.alreadyRan }.count, 2)
            try expectTrue(observed.replies.filter { $0.normalized_outcome == NormalizedOutcome.alreadyRan }.allSatisfy { $0.steps.isEmpty && $0.runner_subprocess == nil })
            service(PWRunnerAdmission(), observed).runSpecimen(request, withReply: observed.reply)
            try expectEqual(observed.entries, 2)
        }
        tk.run("simultaneous service requests admit exactly one execution") {
            let state = PWRunnerAdmission(), observed = AdmissionObservations()
            let start = DispatchSemaphore(value: 0), group = DispatchGroup()
            let services = (0..<8).map { _ in service(state, observed) }
            for s in services { group.enter(); DispatchQueue.global().async {
                start.wait(); s.runSpecimen(request, withReply: observed.reply); group.leave()
            } }
            for _ in services { start.signal() }
            try expectEqual(group.wait(timeout: .now() + 10), .success)
            try expectEqual(observed.entries, 1)
            try expectEqual(observed.exits, 1)
            try expectEqual(observed.replies.filter { $0.normalized_outcome == NormalizedOutcome.alreadyRan }.count, 7)
        }
        tk.run("decode and admission failures consume the host") {
            let oversized = try pwRunnerEncodeJSON(PWRunnerRunSpec(specimen_id: String(repeating: "x", count: 1024),
                policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)"), probe_plan: []))
            for invalid in [Data("{".utf8), oversized] {
                let state = PWRunnerAdmission(), observed = AdmissionObservations()
                service(state, observed).runSpecimen(invalid, withReply: observed.reply)
                service(state, observed).runSpecimen(request, withReply: observed.reply)
                try expectEqual(observed.entries, 0)
                try expectEqual(observed.exits, 1)
                try expectEqual(observed.replies.last?.normalized_outcome, NormalizedOutcome.alreadyRan)
            }
        }
    }
}

// Kept separate from the three admission cases used by their disposable
// mutation control; these tests observe selection, not helper execution.
func runValidatorSelectionTests(_ tk: TestKit) {
    tk.group("service validator selection") {
        tk.run("nested and standalone defaults stay local despite helper availability and app-level decoys") {
            let fm = FileManager.default
            let root = fm.temporaryDirectory.appendingPathComponent("pw-validator-selection-" + UUID().uuidString)
            defer { try? fm.removeItem(at: root) }
            let layouts = [
                ("PolicyWitness.app/Contents/XPCServices/PWRunner.xpc", "PolicyWitness.app/Contents/MacOS/sb_api_validator"),
                ("External/Services/PWRunner.xpc", "Contents/MacOS/sb_api_validator")
            ]
            for (serviceRelative, decoyRelative) in layouts {
                let bundle = root.appendingPathComponent(serviceRelative)
                let expected = root.path + "/" + serviceRelative + "/Contents/MacOS/sb_api_validator"
                let decoy = root.appendingPathComponent(decoyRelative)
                try fm.createDirectory(at: bundle.appendingPathComponent("Contents/MacOS"), withIntermediateDirectories: true)
                try fm.createDirectory(at: decoy.deletingLastPathComponent(), withIntermediateDirectories: true)
                try Data("#!/bin/sh\nexit 77\n".utf8).write(to: decoy)
                try fm.setAttributes([.posixPermissions: 0o755], ofItemAtPath: decoy.path)
                try expectTrue(fm.isExecutableFile(atPath: decoy.path), "positive executable app-level decoy")
                for mode: Int? in [nil, 0o600, 0o755] {
                    if let mode {
                        try Data("#!/bin/sh\nexit 0\n".utf8).write(to: URL(fileURLWithPath: expected))
                        try fm.setAttributes([.posixPermissions: mode], ofItemAtPath: expected)
                    }
                    try expectEqual(fm.fileExists(atPath: expected), mode != nil)
                    try expectEqual(fm.isExecutableFile(atPath: expected), mode == 0o755)
                    try expectEqual(CWorkerOrchestrator.defaultValidatorExecutablePath(bundleURL: bundle), expected)
                }
            }
        }
        tk.run("service uses its actual bundle default unless an explicit override is supplied") {
            let expectedDefault = Bundle.main.bundleURL.path + "/Contents/MacOS/sb_api_validator"
            for override: String? in [nil, "/nonexistent/explicit-validator", ""] {
                let parsed = PWRunnerRunSpec(specimen_id: "validator-selection",
                    policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)(allow default)"),
                    probe_plan: [], _test_overrides: override.map { PWRunnerTestOverrides(validator_executable_path: $0) })
                var selected = [String](), replies = [Data](), exits = 0
                let service = PWRunnerService(admission: PWRunnerAdmission(), scheduleExit: { exits += 1 },
                    orchestrate: { request, hash, bundle, _, validator in
                        selected.append(validator)
                        return CWorkerOrchestrator.run(parsed: request, policyHash: hash, bundleId: bundle,
                            workerExecutablePath: "/nonexistent/validator-selection-worker", validatorExecutablePath: validator)
                    })
                service.runSpecimen(try pwRunnerEncodeJSON(parsed), withReply: { replies.append($0) })
                try expectEqual(selected, [override ?? expectedDefault])
                try expectEqual(replies.count, 1)
                try expectEqual(exits, 1)
                let reply = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: replies[0])
                try expectEqual(reply.normalized_outcome, NormalizedOutcome.workerSpawnFailed)
                try expectTrue(reply.phases.allSatisfy { $0.validator_subprocess == nil && $0.validator_spawn_failure == nil })
                try expectEqual(reply.test_overrides?.validator_executable_path, override)
            }
        }
    }
}

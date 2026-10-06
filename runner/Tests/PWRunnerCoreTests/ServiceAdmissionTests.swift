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

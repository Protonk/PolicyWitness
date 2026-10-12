import Darwin
import Foundation
@testable import PWRunnerCore

private func phaseEquipment(_ name: String) -> String {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent()
    let app = ProcessInfo.processInfo.environment["PW_APP_DIR"] ?? root.appendingPathComponent("dist/PolicyWitness.app").path
    return app + "/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/" + name
}
private func phaseProbe(_ id: String, _ target: String, action: String = "access", operation: String = "file-read-data") -> PWRunnerProbeStep {
    PWRunnerProbeStep(step_id: id, sandbox_check: PWRunnerSandboxCheck(operation: operation,
        filter: PWRunnerSandboxFilter(kind: "path", value: target)),
        attempt: PWRunnerAttempt(kind: "file", action: action, target: target))
}
private func phaseRun(_ phases: [PWRunnerPhase], overrides: PWRunnerTestOverrides? = nil,
                      validator: String? = nil, spawn: @escaping ValidatorSpawnCall = nativeValidatorSpawn) -> PWRunnerRunResult {
    CWorkerOrchestrator.run(parsed: PWRunnerRunSpec(specimen_id: "phases",
        policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)(allow default)"),
        phases: phases, _test_overrides: overrides), policyHash: "test", bundleId: nil,
        workerExecutablePath: phaseEquipment("pw-probe-runner"),
        validatorExecutablePath: validator ?? phaseEquipment("sb_api_validator"), validatorSpawn: spawn)
}

func runPhaseProtocolTests(_ tk: TestKit) {
    tk.group("ordered phases: production C/Swift and independent file effects") {
        tk.run("each of eight held arrivals precedes its own unlink and follows earlier effects") {
            let directory = FileManager.default.temporaryDirectory.appendingPathComponent("pw-phases-" + UUID().uuidString)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
            defer { try? FileManager.default.removeItem(at: directory) }
            let files = (0..<8).map { directory.appendingPathComponent(String($0)).path }
            for path in files { try Data("phase-control".utf8).write(to: URL(fileURLWithPath: path)) }
            let input = CWorkerInput(workerExecutablePath: phaseEquipment("pw-probe-runner"),
                policy: "(version 1)(allow default)",
                slots: files.enumerated().map { CWorkerSlotInput(stepId: String($0.offset), attemptKind: .fileUnlink, target: $0.element) },
                phases: files.indices.map { CWorkerPhaseInput(firstSlot: $0, endSlot: $0 + 1) })
            var arrivals: [Int] = [], samples: [[Bool]] = []
            let result = runCWorker(input, phaseBoundary: { _, index in
                arrivals.append(index)
                for _ in 0..<5 {
                    samples.append(files.enumerated().map { FileManager.default.fileExists(atPath: $0.element) == ($0.offset >= index) })
                    usleep(20_000)
                }
            })
            guard case .success(let out) = result else { throw TestFailure(message: "phase worker did not run") }
            try expectEqual(arrivals, Array(0..<8)); try expectTrue(samples.flatMap { $0 }.allSatisfy { $0 })
            try expectTrue(files.allSatisfy { !FileManager.default.fileExists(atPath: $0) })
            try expectTrue(out.phases.allSatisfy { $0.arrived && $0.collectionClosed && $0.releaseSet && $0.acknowledged && $0.completed && $0.ownershipEstablished && $0.violations.isEmpty })
            try expectTrue(out.slots.allSatisfy { $0.completed && $0.rc == 0 }); try expectEqual(out.exitCode, 0)
        }
        tk.run("later realpath eligibility is unavailable after independently observed unlink") {
            let target = FileManager.default.temporaryDirectory.appendingPathComponent("pw-phase-unlink-" + UUID().uuidString)
            try Data("owned".utf8).write(to: target); defer { try? FileManager.default.removeItem(at: target) }
            let reply = phaseRun([
                PWRunnerPhase(phase_id: "remove", actions: [.probe(phaseProbe("unlink", target.path, action: "unlink", operation: "file-write-unlink"))]),
                PWRunnerPhase(phase_id: "missing", actions: [.probe(phaseProbe("access", target.path))])])
            try expectFalse(FileManager.default.fileExists(atPath: target.path))
            try expectEqual(reply.steps[0].attempt.rc, 0)
            try expectEqual(reply.steps[1].sandbox_check.outcome, "prediction_unavailable")
            try expectEqual(reply.steps[1].comparison?.order, "unestablished")
            try expectEqual(reply.steps[1].attempt.errno, Int(ENOENT))
            try expectTrue(reply.phases.allSatisfy { $0.completion_observed && $0.ordering?.chainEstablished == true })
            try expectEqual(reply.phases[1].collection_status, "not_needed")
            try expectNil(reply.phases[1].validator_subprocess)
            _ = try pwRunnerEncodeJSON(reply)
        }
        tk.run("resolvable phases use separate actual validators and retain phase association") {
            let phases = (0..<3).map { PWRunnerPhase(phase_id: "p\($0)", actions: [.probe(phaseProbe("s\($0)", "/etc/hosts"))]) }
            var launches = 0
            let reply = phaseRun(phases, spawn: { pid, path, actions, argv in
                launches += 1; usleep(50_000)
                return nativeValidatorSpawn(pid, path, actions, argv)
            })
            try expectEqual(launches, 3); try expectEqual(reply.rc, 0)
            try expectTrue(reply.steps.allSatisfy { $0.comparison?.order == "query_first" })
            try expectEqual(reply.steps.map { $0.phase_id }, ["p0", "p1", "p2"])
            try expectEqual(Set(reply.phases.compactMap { $0.validator_subprocess?.pid }).count, 3)
            for (index, phase) in reply.phases.enumerated() {
                try expectEqual(phase.validator_subprocess?.records?.map { $0.stepId }, ["s\(index)"])
            }
            _ = try pwRunnerEncodeJSON(reply)
        }
        for ordinal: UInt32 in [1, 3] {
            tk.run("stale or future second release ordinal \(ordinal) cannot execute later actions") {
                var input = CWorkerInput(workerExecutablePath: phaseEquipment("pw-probe-runner"),
                    policy: "(version 1)(allow default)",
                    slots: (0..<2).map { CWorkerSlotInput(stepId: "s\($0)", attemptKind: .fileAccess, target: "/etc/hosts") },
                    phases: [CWorkerPhaseInput(firstSlot: 0, endSlot: 1), CWorkerPhaseInput(firstSlot: 1, endSlot: 2)])
                input.proceedWaitMs = 80
                input.phaseReleaseOrdinal = { $0 == 0 ? 1 : ordinal }
                guard case .success(let out) = runCWorker(input) else { throw TestFailure(message: "missing worker output") }
                try expectTrue(out.phases[0].completed && out.slots[0].completed)
                try expectTrue(out.phases[1].arrived)
                try expectFalse(out.phases[1].acknowledged || out.phases[1].completed || out.slots[1].completed)
                try expectEqual(out.workerEvidence?.failure?.operation, 11)
                try expectEqual(out.workerEvidence?.failure?.index, 1)
                try expectEqual(out.workerEvidence?.failure?.code, ordinal == 1 ? 8 : 11)
                try expectEqual(out.exitCode, 0)
            }
        }
        tk.run("death during second collection retains first phase without later completion") {
            let input = CWorkerInput(workerExecutablePath: phaseEquipment("pw-probe-runner"), policy: "(version 1)(allow default)",
                slots: (0..<3).map { CWorkerSlotInput(stepId: "s\($0)", attemptKind: .fileAccess, target: "/etc/hosts") },
                phases: (0..<3).map { CWorkerPhaseInput(firstSlot: $0, endSlot: $0 + 1) })
            var called: [Int] = []
            let result = runCWorker(input, phaseBoundary: { pid, index in
                called.append(index)
                if index == 1 { _ = Darwin.kill(pid, SIGKILL); usleep(20_000) }
            })
            guard case .success(let out) = result else { throw TestFailure(message: "missing killed worker") }
            try expectEqual(called, [0, 1]); try expectEqual(out.termSignal, SIGKILL)
            try expectTrue(out.phases[0].completed && out.phases[0].ownershipEstablished)
            try expectTrue(out.phases[1].arrived && out.phases[1].collectionClosed)
            try expectFalse(out.phases[1].releaseSet || out.phases[1].acknowledged || out.phases[1].completed || out.phases[2].arrived)
            try expectEqual(out.slots.map { $0.completed }, [true, false, false])
        }
        tk.run("arrival without prior completion cannot start another collection") {
            guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else { throw TestFailure(message: "missing worker fixture") }
            let input = CWorkerInput(workerExecutablePath: fixture, policy: "phase_invalid_previous",
                slots: [], phases: [CWorkerPhaseInput(firstSlot: 0, endSlot: 0), CWorkerPhaseInput(firstSlot: 0, endSlot: 0)],
                sentinelTimeoutMs: 100)
            var collected: [Int] = []
            let result = runCWorker(input, phaseBoundary: { _, index in collected.append(index) })
            guard let out = unwrapWorkerOutput(result) else { throw TestFailure(message: "fixture did not spawn") }
            try expectEqual(collected, [0])
            try expectTrue(out.phases[1].arrived)
            try expectFalse(out.phases[1].collectionClosed || out.phases[1].releaseSet || out.phases[1].completed)
            try expectTrue(out.phases[1].violations.contains("arrival_without_previous_completion"))
        }
        tk.run("aggregate collection exhaustion permits attempts without borrowing an earlier record") {
            guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else { throw TestFailure(message: "missing validator fixture") }
            let reply = phaseRun((0..<3).map { PWRunnerPhase(phase_id: "p\($0)", actions: [.probe(phaseProbe("s\($0)", "/etc/hosts", operation: "io_hang"))]) },
                overrides: PWRunnerTestOverrides(validator_io_timeout_ms: 100, validator_total_timeout_ms: 30), validator: fixture + ".validator")
            try expectEqual(reply.test_overrides?.validator_total_timeout_ms, 30)
            try expectEqual(reply.phases[0].validator_subprocess?.stdout_collection_stop, "deadline")
            try expectEqual(reply.phases[1].collection_status, "budget_exhausted")
            try expectNil(reply.phases[1].validator_subprocess)
            try expectTrue(reply.steps.allSatisfy { $0.attempt.result_source == "worker" })
            try expectEqual(reply.steps[1].comparison?.order, "unestablished")
            _ = try pwRunnerEncodeJSON(reply)
        }
    }
}

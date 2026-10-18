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
        tk.run("shared evidence type corpus is rejected or preserved by the actual decoder and encoder") {
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent()
            let fixtures = root.appendingPathComponent("tests/fixtures")
            let envelope = try JSONSerialization.jsonObject(with: Data(contentsOf: fixtures.appendingPathComponent(
                "blackbox_e2e/checker/response23/issuer_abnormal_run.json"))) as! [String: Any]
            let baseline = (envelope["data"] as! [String: Any])["runner_result"]!
            let cases = try JSONSerialization.jsonObject(with: Data(contentsOf: fixtures.appendingPathComponent(
                "contract/evidence_types.json"))) as! [[String: Any]]
            func replace(_ value: Any, path: ArraySlice<String>, with replacement: Any) -> Any {
                guard let key = path.first else { return replacement }
                if var array = value as? [Any] {
                    let index = Int(key)!
                    array[index] = replace(array[index], path: path.dropFirst(), with: replacement)
                    return array
                }
                var object = value as! [String: Any]
                object[key] = replace(object[key] ?? NSNull(), path: path.dropFirst(), with: replacement)
                return object
            }
            for row in cases {
                var raw = baseline
                for patch in row["patches"] as! [[String: Any]] {
                    raw = replace(raw, path: (patch["path"] as! String).split(separator: "/").map(String.init)[...], with: patch["value"]!)
                }
                var accepted = false
                do {
                    let reply = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: raw))
                    _ = try pwRunnerEncodeJSON(reply)
                    accepted = true
                } catch {}
                try expectEqual(accepted, row["accepted"] as! Bool, row["name"] as! String)
            }
        }
        tk.run("collection states reject contradictions and retain failed driver evidence") {
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent()
            let fixtures = root.appendingPathComponent("tests/fixtures")
            let envelope = try JSONSerialization.jsonObject(with: Data(contentsOf:
                fixtures.appendingPathComponent("blackbox_e2e/checker/response23/extension_run.json"))) as! [String: Any]
            let raw = (envelope["data"] as! [String: Any])["runner_result"] as! [String: Any]
            let baseline = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: raw))
            let cases = try JSONSerialization.jsonObject(with: Data(contentsOf:
                fixtures.appendingPathComponent("contract/phase_collection.json"))) as! [[String: Any]]
            for row in cases {
                var reply = baseline
                var phase = reply.phases.last!
                phase.phase_id = "collection_control"; phase.ordinal = reply.phases.count + 1; phase.action_ids = []
                phase.collection_status = row["status"] as! String
                phase.arrival_observed = phase.collection_status != "not_reached"; phase.completion_observed = false
                phase.ordering?.validator_disposition = row["disposition"] as! String
                phase.ordering?.collection_closed_before_proceed = (row["disposition"] as! String) != "not_invoked"
                phase.ordering?.proceed_set = false; phase.ordering?.proceed_observed = false
                phase.ordering?.worker_lifetime_established = false
                if let reaped = row["reaped"] as? Bool {
                    // The carrier phase has no actions: its collection is its own,
                    // with an empty plan and no records.
                    phase.validator_subprocess?.phase_id = phase.phase_id; phase.validator_subprocess?.ordinal = phase.ordinal
                    phase.validator_subprocess?.expected_step_ids = []; phase.validator_subprocess?.records = []
                    phase.validator_subprocess?.association_issues = []
                    phase.validator_subprocess?.reaped = reaped
                    phase.validator_subprocess?.exit_code = nil; phase.validator_subprocess?.term_signal = nil
                } else { phase.validator_subprocess = nil }
                phase.validator_spawn_failure = (row["spawn_failure"] as! Bool) ? PWRunnerSpawnFailure(
                    executable_path: "/controlled/validator", return_code: 2, diagnostic: "controlled spawn failure") : nil
                reply.phases.append(phase)
                var rejected = false
                do { _ = try pwRunnerEncodeJSON(reply) }
                catch EncodingError.invalidValue(_, let context) {
                    rejected = true
                    try expectTrue(context.debugDescription.contains("phase collection status contradicts validator evidence"))
                }
                try expectEqual(rejected, !(row["accepted"] as! Bool), row["name"] as! String)
            }
        }
        tk.run("a validator collection must belong to the phase that holds it") {
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent()
            let envelope = try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent(
                "tests/fixtures/blackbox_e2e/checker/response23/extension_run.json"))) as! [String: Any]
            let raw = (envelope["data"] as! [String: Any])["runner_result"] as! [String: Any]
            let baseline = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: raw))
            try expectEqual(baseline.phases.count, 3)
            // Every phase queries the same path under a different action ID.
            try expectEqual(Set(baseline.steps.map { $0.sandbox_check.filter_value }).count, 1)
            _ = try pwRunnerEncodeJSON(baseline)
            let transplants: [(String, (inout PWRunnerRunResult) -> Void, String)] = [
                ("whole block", { r in let a = r.phases[0].validator_subprocess; r.phases[0].validator_subprocess = r.phases[1].validator_subprocess; r.phases[1].validator_subprocess = a }, "names another phase"),
                ("identity only", { r in let id = r.phases[0].phase_id; r.phases[1].validator_subprocess?.phase_id = id }, "names another phase"),
                ("ordinal only", { r in r.phases[1].validator_subprocess?.ordinal = 1 }, "names another phase"),
                ("expected IDs only", { r in let ids = r.phases[0].validator_subprocess?.expected_step_ids; r.phases[1].validator_subprocess?.expected_step_ids = ids }, "eligible query plan"),
                ("records only", { r in let records = r.phases[0].validator_subprocess?.records; r.phases[1].validator_subprocess?.records = records }, "association issues disagree"),
                ("missing identity", { r in r.phases[1].validator_subprocess?.phase_id = nil }, "lacks phase ownership"),
                ("missing plan", { r in r.phases[1].validator_subprocess?.expected_step_ids = nil }, "lacks its expected plan"),
                ("issues erased", { r in r.phases[1].validator_subprocess?.records = []; }, "association issues disagree"),
            ]
            for (name, change, reason) in transplants {
                var reply = baseline; change(&reply)
                var rejected: String? = nil
                do { _ = try pwRunnerEncodeJSON(reply) }
                catch EncodingError.invalidValue(_, let context) { rejected = context.debugDescription }
                try expectTrue(rejected?.contains(reason) == true, "\(name): expected rejection for \(reason), got \(rejected ?? "acceptance")")
            }
            // Sequential children may reuse a numeric PID; ownership does not read PIDs.
            var reused = baseline
            let firstPid = reused.phases[0].validator_subprocess!.pid
            reused.phases[1].validator_subprocess?.pid = firstPid
            _ = try pwRunnerEncodeJSON(reused)
        }
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
                let summary = classify(workerResult: .success(out), validatorResult: nil, expectedVerdictCount: 0)
                try expectEqual(summary.outcome, NormalizedOutcome.runnerFailed)
                if ordinal == 1 {
                    try expectEqual(out.workerEvidence?.failure?.detail, 80)
                    try expectContains(summary.error ?? "", "budget=80 ms; release not observed")
                } else {
                    try expectEqual(out.workerEvidence?.failure?.detail, ordinal)
                    try expectContains(summary.error ?? "", "observed_release_ordinal=3; phase release rejected")
                    try expectFalse((summary.error ?? "").contains("budget="))
                }
                // Constructed future codes retain the raw detail without a
                // known code's budget or release-ordinal interpretation.
                var unfamiliar = out
                unfamiliar.workerEvidence?.failure?.code = 4_000_000_001
                let unknown = classify(workerResult: .success(unfamiliar), validatorResult: nil, expectedVerdictCount: 0)
                try expectContains(unknown.error ?? "", "code=4000000001")
                try expectFalse((unknown.error ?? "").contains("budget="))
                try expectFalse((unknown.error ?? "").contains("observed_release_ordinal="))
                try expectEqual(unfamiliar.workerEvidence?.failure?.detail, out.workerEvidence?.failure?.detail)
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
        tk.run("second-phase ownership loss preserves the first phase's established ordering") {
            let input = CWorkerInput(workerExecutablePath: phaseEquipment("pw-probe-runner"), policy: "(version 1)(allow default)",
                slots: (0..<2).map { CWorkerSlotInput(stepId: "s\($0)", attemptKind: .fileAccess, target: "/etc/hosts") },
                phases: (0..<2).map { CWorkerPhaseInput(firstSlot: $0, endSlot: $0 + 1) })
            var secondCollectionClosed = false, faultInjected = false
            var calls = ChildProcessCalls()
            calls.wait = { pid, status, options in
                if secondCollectionClosed && !faultInjected {
                    faultInjected = true; errno = EIO; return -1
                }
                return Darwin.waitpid(pid, status, options)
            }
            let result = runCWorker(input, processCalls: calls, phaseBoundary: { _, index in
                if index == 1 { secondCollectionClosed = true }
            })
            guard case .success(let out) = result else { throw TestFailure(message: "missing worker output") }
            defer {
                var status: Int32 = 0
                var rc: pid_t
                repeat { rc = Darwin.waitpid(out.workerPid, &status, WNOHANG) } while rc < 0 && errno == EINTR
                if rc == 0 {
                    _ = Darwin.kill(out.workerPid, SIGKILL)
                    repeat { rc = Darwin.waitpid(out.workerPid, &status, 0) } while rc < 0 && errno == EINTR
                }
            }
            try expectTrue(faultInjected && out.phases[0].ownershipEstablished)
            try expectEqual(out.pollStopReason, "wait_error")
            try expectEqual(out.waitErrors?.map { $0.errno }, [EIO])
            try expectEqual(out.reaped, true)
            try expectTrue(out.phases[0].completed && out.slots[0].completed)
            try expectTrue(out.phases[1].arrived && out.phases[1].collectionClosed)
            try expectFalse(out.phases[1].releaseSet || out.phases[1].acknowledged || out.phases[1].completed || out.phases[1].ownershipEstablished)
            try expectFalse(out.slots[1].completed)
            for index in 0..<2 {
                let ordering = buildPhaseOrdering(out, index: index, input: input.phases[index], validatorOutput: nil, hasQueries: false)
                try expectEqual(ordering.chainEstablished, index == 0)
            }
            try expectEqual(classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0).outcome,
                            NormalizedOutcome.runnerFailed)
        }
        tk.run("arrival without prior completion cannot start another collection") {
            guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else { throw TestFailure(message: "missing worker fixture") }
            let input = CWorkerInput(workerExecutablePath: fixture, policy: "phase_invalid_previous",
                slots: [], phases: [CWorkerPhaseInput(firstSlot: 0, endSlot: 0), CWorkerPhaseInput(firstSlot: 0, endSlot: 0)],
                sentinelTimeoutMs: 100)
            var collected: [Int] = []
            let result = runCWorker(input, phaseBoundary: { _, index in collected.append(index) })
            let out: CWorkerOutput
            switch result {
            case .success(let observed): out = observed
            case .failure(_, let observed?): out = observed
            default: throw TestFailure(message: "fixture did not spawn")
            }
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
        tk.run("M08: timeout, failed cleanup and late output cannot enter the next phase") {
            guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
                  let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"] else {
                throw TestFailure(message: "required fixture and receipt directory missing")
            }
            let id = UUID().uuidString
            let gate = "/tmp/pw-order-late-" + id
            let target = URL(fileURLWithPath: "/private/tmp/pw-phase-combined-" + id)
            try Data("combined phase witness".utf8).write(to: target)
            defer { try? FileManager.default.removeItem(at: target); try? FileManager.default.removeItem(atPath: gate) }
            var spawned: [pid_t] = []
            defer {
                for pid in spawned {
                    // Reap first: never signal a PID the production driver already reaped.
                    var status: Int32 = 0
                    let rc = Darwin.waitpid(pid, &status, WNOHANG)
                    if rc == 0 {
                        _ = Darwin.kill(pid, SIGKILL)
                        while Darwin.waitpid(pid, &status, 0) < 0 && errno == EINTR {}
                    }
                }
            }
            let request = PWRunnerRunSpec(specimen_id: "M08",
                policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)(allow default)"),
                phases: [PWRunnerPhase(phase_id: "timed", actions: [.probe(phaseProbe("early", target.path, operation: "io_hang_late:" + id))]),
                         PWRunnerPhase(phase_id: "later", actions: [.probe(phaseProbe("later", target.path, action: "read_fresh"))])],
                _test_overrides: PWRunnerTestOverrides(validator_io_timeout_ms: 100))
            var reply = CWorkerOrchestrator.run(parsed: request, policyHash: "controlled-validator", bundleId: nil,
                workerExecutablePath: phaseEquipment("pw-probe-runner"), validatorExecutablePath: fixture + ".validator",
                validatorSpawn: { pid, path, actions, argv in
                    if !spawned.isEmpty { FileManager.default.createFile(atPath: gate, contents: Data()) }
                    let rc = nativeValidatorSpawn(pid, path, actions, argv)
                    if rc == 0 { spawned.append(pid.pointee) }
                    return rc
                }, validatorProcessCalls: { index in
                    var calls = ChildProcessCalls()
                    if index == 0 { calls.kill = { _, _ in errno = EPERM; return -1 } }
                    return calls
                })
            // Use the service's production post-orchestration enrichment before
            // handing this driver reply to complete-document readers.
            reply.steps = enrichPathDiagnostics(steps: reply.steps)
            try expectEqual(spawned.count, 2)
            try expectTrue(spawned[0] != spawned[1])
            let deadline = Date().addingTimeInterval(2)
            while Date() < deadline && !((try? String(contentsOfFile: gate))?.contains("late_write=-1 errno=\(EPIPE)") ?? false) { usleep(1000) }
            let receipt = try String(contentsOfFile: gate)
            try expectContains(receipt, "late_write=-1 errno=\(EPIPE)")
            try expectEqual(reply.phases[0].validator_subprocess?.stdout_collection_stop, "deadline")
            try expectEqual(reply.phases[0].validator_subprocess?.reaped, false)
            try expectEqual(reply.phases[0].validator_subprocess?.termination_request?.errno, EPERM)
            try expectEqual(reply.phases[0].ordering?.validator_disposition, "unconfirmed")
            try expectEqual(reply.phases[0].validator_subprocess?.records?.map { $0.stepId }, ["early"])
            try expectEqual(reply.phases[1].validator_subprocess?.records?.map { $0.stepId }, ["later"])
            try expectTrue(reply.phases.allSatisfy { $0.completion_observed })
            try expectEqual(try Data(contentsOf: target), Data("combined phase witness".utf8))
            let matrix = try JSONSerialization.jsonObject(with: Data(contentsOf: repositoryRoot()
                .appendingPathComponent("tests/fixtures/comparison/matrix.json"))) as! [String: Any]
            let row = (matrix["rows"] as! [[String: Any]]).first { $0["id"] as? String == "M08" }!
            let actual = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(reply.steps[1].comparison!)) as! NSDictionary
            try expectTrue(actual.isEqual(to: row["comparison"] as! [String: Any]))
            let raw = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(reply.steps[1]))
            func mismatches(_ expected: [String: Any]) -> [String] {
                expected.keys.sorted().filter { path in
                    let observed = path.split(separator: ".").reduce(raw as Any?) { value, key in
                        (value as? [String: Any])?[String(key)]
                    } ?? NSNull()
                    if expected[path] as? String == ">0" {
                        guard let number = observed as? NSNumber,
                              CFGetTypeID(number) != CFBooleanGetTypeID() else { return true }
                        return number.intValue <= 0
                    }
                    return !(observed as! NSObject).isEqual(expected[path]!)
                }
            }
            let expectations = row["assert"] as! [String: Any]
            try expectEqual(mismatches(expectations), [], "M08 shared raw assertions")
            // A wrong fixture expectation must fail this same live reader.
            var wrong = expectations
            wrong["attempt.fresh_read.read_rc"] = 20
            try expectEqual(mismatches(wrong), ["attempt.fresh_read.read_rc"])
            let output = URL(fileURLWithPath: artifacts)
            try pwRunnerEncodeJSON(reply).write(to: output.appendingPathComponent("combined-phases.json"))
            try Data(receipt.utf8).write(to: output.appendingPathComponent("combined-phases-late-write.txt"))
            // This cleanup belongs to the test, after the host's recorded
            // unconfirmed disposition. It cannot upgrade the retained reply.
            let killRC = Darwin.kill(spawned[0], SIGKILL)
            var status: Int32 = 0
            var reaped: pid_t
            repeat { reaped = Darwin.waitpid(spawned[0], &status, 0) } while reaped < 0 && errno == EINTR
            try JSONSerialization.data(withJSONObject: ["pid": spawned[0], "kill_rc": killRC,
                "wait_rc": reaped, "wait_status": status], options: [.sortedKeys]).write(
                    to: output.appendingPathComponent("combined-phases-test-cleanup.json"))
            try expectEqual(reaped, spawned[0])
        }
    }
}

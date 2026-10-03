import Darwin
import Foundation
@testable import PWRunnerCore

private func orderingFixturePath() throws -> String {
    guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
        throw TestFailure(message: "required lifecycle equipment missing; run runner_unit")
    }
    return path
}
private func cleanupOrderingChild(_ pid: pid_t) {
    var status: Int32 = 0
    let rc = Darwin.waitpid(pid, &status, WNOHANG)
    if rc == 0 { _ = Darwin.kill(pid, SIGKILL); _ = Darwin.waitpid(pid, &status, 0) }
}
private func orderingWorker(_ mode: String, suffix: String = "",
                            kind: PWAttemptKind = .fileOpenRead, target: String = "/etc/hosts",
                            calls: ChildProcessCalls = ChildProcessCalls(),
                            hook: CWorkerPostAppliedHook? = nil) throws -> CWorkerOutput {
    let result = runCWorker(CWorkerInput(workerExecutablePath: try orderingFixturePath() + suffix,
        policy: mode, slots: [CWorkerSlotInput(stepId: "s", attemptKind: kind, target: target)],
        sentinelTimeoutMs: 200, exitGraceMs: 30), processCalls: calls, postApplied: hook)
    guard case .success(let out) = result else { throw TestFailure(message: "worker setup failed: \(result)") }
    cleanupOrderingChild(out.workerPid)
    return out
}
private func orderingStep(operation: String = "file-read-data") -> PWRunnerProbeStep {
    PWRunnerProbeStep(step_id: "s", sandbox_check: PWRunnerSandboxCheck(operation: operation,
        filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
        attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts"))
}
private func orderingVerdict(_ operation: String = "file-read-data") -> ValidatorVerdict {
    ValidatorVerdict(stepId: "s", operation: operation, filterType: "PATH", filterTypeId: 1,
        filterValue: "/etc/hosts", rc: 0, errnoVal: 0, outcome: "allow", rawLine: "constructed control")
}
private func orderedSteps(_ worker: CWorkerOutput?, _ validator: ValidatorOutput?,
                          step: PWRunnerProbeStep = orderingStep()) -> [PWRunnerStepResult] {
    buildStepResults(probePlan: [step], queryPlan: planValidatorQueries([step]), workerOutput: worker,
        validatorOutput: validator, ordering: worker.map { buildOrdering($0, validatorOutput: validator, hasQueries: true) })
}
private func orderingEnvelope(_ worker: CWorkerOutput?, _ validator: ValidatorOutput?) -> PWRunnerRunResult {
    var sub = worker.map(buildWorkerSubprocess)
    sub?.ordering = worker.map { buildOrdering($0, validatorOutput: validator, hasQueries: true) }
    return PWRunnerRunResult(specimen_id: "ordering", rc: 0, normalized_outcome: "ok", pid: 42,
        policy_format: "sbpl", sandboxed_after_apply: worker?.applied,
        steps: orderedSteps(worker, validator), runner_subprocess: sub,
        validator_subprocess: validator.map(buildValidatorSubprocess))
}
private func waitForReceipt(_ path: String, _ text: String) -> Bool {
    for _ in 0..<2000 {
        if (try? String(contentsOfFile: path))?.contains(text) == true { return true }
        usleep(1000)
    }
    return false
}

// Shared by runner_unit and the disposable host mutation control.
func runOrderingGateControl(_ tk: TestKit) {
    tk.run("proceed_wait_then_report: hook gate forbids acknowledgement and attempts") {
        let receipt = "/tmp/pw-order-" + UUID().uuidString
        defer { try? FileManager.default.removeItem(atPath: receipt) }
        var heldReceipt = ""
        var ready = false
        let out = try orderingWorker("proceed_wait|" + receipt) { _ in
            ready = waitForReceipt(receipt, "waiting")
            let gate = DispatchSemaphore(value: 0)
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(100)) { gate.signal() }
            gate.wait()
            heldReceipt = (try? String(contentsOfFile: receipt)) ?? ""
        }
        try expectTrue(ready)
        try expectEqual(heldReceipt, "waiting\n", "early worker publication while hook held")
        try expectTrue(out.hookInvoked && out.proceedSet && out.proceedObserved && out.proceedOwnershipEstablished)
        try expectTrue(out.done && out.slots[0].completed)
        try expectEqual(try String(contentsOfFile: receipt), "waiting\nack\nattempt\n")
        try expectTrue(out.orderingProtocolViolations.isEmpty)
    }
}

func runOrderingTests(_ tk: TestKit) {
    tk.group("release barrier: real host driver and independent lifecycle fixture") {
        runOrderingGateControl(tk)
        tk.run("proceed_wait_expire: collection held beyond expiry, late release retains verdict and cannot revive") {
            let receipt = "/tmp/pw-order-" + UUID().uuidString
            defer { try? FileManager.default.removeItem(atPath: receipt) }
            var expired = false
            let validator = ValidatorOutput(validatorPid: 7, verdicts: [orderingVerdict()], reaped: true)
            let out = try orderingWorker("proceed_expire:50|" + receipt) { _ in
                expired = waitForReceipt(receipt, "expired") // test-owned collection gate
            }
            try expectTrue(expired)
            try expectTrue(out.hookInvoked && out.proceedSet && out.done)
            try expectFalse(out.proceedObserved || out.slots[0].completed)
            try expectEqual(out.workerEvidence?.failure?.operation, 11)
            try expectEqual(out.workerEvidence?.failure?.code, 8)
            let summary = classify(workerResult: .success(out), validatorResult: .success(validator), expectedVerdictCount: 1)
            try expectEqual(summary.outcome, NormalizedOutcome.runnerFailed)
            try expectContains(summary.error ?? "", "proceed wait")
            let step = orderedSteps(out, validator)[0]
            try expectEqual(step.sandbox_check.outcome, "allow")
            try expectEqual(step.comparison?.order, "unestablished")
            try expectEqual(step.comparison?.observation, "unavailable")
        }
        tk.run("hook_spawn_failure_before_release: attempts survive failed validator spawn") {
            var result: ValidatorClientResult?
            let out = try orderingWorker("proceed_wait") { pid in
                result = runValidator(ValidatorClientInput(executablePath: "/nonexistent-validator", targetPid: pid,
                    probes: [ValidatorProbe(stepId: "s", operation: "file-read-data", filterType: "PATH", filterValue: "/etc/hosts")]))
            }
            guard case .failure(.spawnFailed, nil) = result else { throw TestFailure(message: "expected real spawn failure") }
            try expectTrue(out.proceedObserved && out.slots[0].completed)
            try expectEqual(buildOrdering(out, validatorOutput: nil, hasQueries: true).validator_disposition, "not_spawned")
            try expectEqual(orderedSteps(out, nil)[0].comparison?.order, "unestablished")
            try expectEqual(classify(workerResult: .success(out), validatorResult: result, expectedVerdictCount: 1).outcome,
                            NormalizedOutcome.validatorSpawnFailed)
        }
        tk.run("unfamiliar native spawn errors survive orchestration and reply encoding") {
            // Controlled native returns, not sandbox evidence. The real driver
            // still owns its pipes, release, worker observation and assembly.
            for (code, mode): (Int32, String) in [(123456, "proceed_wait"), (Int32.max, "proceed_wait"),
                                                (123456, "signal_after_ack")] {
                let workerFailed = mode == "signal_after_ack"
                let receipt = "/tmp/pw-spawn-" + UUID().uuidString
                defer { try? FileManager.default.removeItem(atPath: receipt) }
                let path = "/unfamiliar/validator-\"é\""
                let diagnostic = String(cString: strerror(code))
                let parsed = PWRunnerRunSpec(specimen_id: "unfamiliar-spawn",
                    policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: mode + "|" + receipt),
                    probe_plan: [orderingStep()])
                var calls = 0
                var receivedPath = ""
                var receivedArgv = [String]()
                let result = CWorkerOrchestrator.run(parsed: parsed, policyHash: "fixture", bundleId: nil,
                    workerExecutablePath: try orderingFixturePath(), validatorExecutablePath: path,
                    validatorSpawn: { _, executable, _, argv in
                        calls += 1
                        receivedPath = executable
                        receivedArgv = (0..<3).map { String(cString: argv[$0]!) }
                        errno = EACCES // posix_spawn's return, not errno, owns this evidence.
                        return code
                    })
                try expectEqual(calls, 1)
                try expectEqual(receivedPath, path)
                try expectEqual(receivedArgv, ["sb_api_validator", "--batch", String(result.pid)])
                try expectEqual(try String(contentsOfFile: receipt), workerFailed ? "waiting\nack\n" : "waiting\nack\nattempt\n")
                let bytes = pwRunnerReplyData(result)
                let reply = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
                try expectEqual(reply.normalized_outcome, workerFailed ? NormalizedOutcome.runnerFailed : NormalizedOutcome.validatorSpawnFailed)
                try expectEqual(reply.rc, 1)
                try expectNil(reply.reporting_failure)
                try expectNil(reply.validator_subprocess)
                try expectEqual(reply.validator_spawn_failure?.origin, "runner_host")
                try expectEqual(reply.validator_spawn_failure?.operation, "posix_spawn")
                try expectEqual(reply.validator_spawn_failure?.executable_path, path)
                try expectEqual(reply.validator_spawn_failure?.return_code, code)
                try expectEqual(reply.validator_spawn_failure?.diagnostic, diagnostic)
                if !workerFailed {
                    try expectContains(reply.error ?? "", path)
                    try expectContains(reply.error ?? "", String(code))
                    try expectContains(reply.error ?? "", diagnostic)
                }
                try expectEqual(reply.runner_subprocess?.ordering?.validator_disposition, "not_spawned")
                try expectEqual(reply.runner_subprocess?.ordering?.proceed_observed, true)
                try expectEqual(reply.steps[0].attempt.outcome, workerFailed ? AttemptOutcome.notRunWorkerDied : AttemptOutcome.ok)
                try expectEqual(reply.steps[0].sandbox_check.outcome, SandboxCheckOutcome.error)
                try expectEqual(reply.steps[0].sandbox_check.missing_reason, "validator_not_invoked")
                try expectEqual(reply.steps[0].comparison?.order, "unestablished")
                // A later reply-invariant failure must retain the same native
                // record, even though the summary becomes reporting_failed.
                var invalid = result
                invalid.steps[0].comparison = nil
                let degraded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerReplyData(invalid))
                try expectEqual(degraded.normalized_outcome, NormalizedOutcome.runnerReportingFailed)
                try expectEqual(degraded.reporting_failure?.evidence_retained, true)
                try expectEqual(try pwRunnerEncodeJSON(degraded.validator_spawn_failure),
                                try pwRunnerEncodeJSON(reply.validator_spawn_failure))
                // An absent optional record stays unknown.
                var without = try JSONSerialization.jsonObject(with: bytes) as! [String: Any]
                without.removeValue(forKey: "validator_spawn_failure")
                let absent = try pwRunnerDecodeJSON(PWRunnerRunResult.self,
                    from: JSONSerialization.data(withJSONObject: without))
                try expectNil(absent.validator_spawn_failure)
            }
        }
        tk.run("signal_while_waiting: records before and after death never acquire policy lifetime") {
            let receipt = "/tmp/pw-order-" + UUID().uuidString
            defer { try? FileManager.default.removeItem(atPath: receipt); try? FileManager.default.removeItem(atPath: receipt + ".die") }
            var records = [ValidatorVerdict]()
            // Actual native records on either side of observed death; no
            // particular native answer for a dead PID is assumed.
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let validatorPath = root.appendingPathComponent("dist/PolicyWitness.app/Contents/MacOS/sb_api_validator").path
            var childDied = false
            let out = try orderingWorker("signal_awaiting_proceed|" + receipt) { pid in
                _ = waitForReceipt(receipt, "waiting")
                for index in 0..<2 {
                    if index == 1 {
                        FileManager.default.createFile(atPath: receipt + ".die", contents: Data())
                        // waitid WNOWAIT observes death without reaping/losing PID ownership.
                        var info = siginfo_t()
                        childDied = waitid(P_PID, id_t(pid), &info, WEXITED | WNOWAIT) == 0
                    }
                    let v = runValidator(ValidatorClientInput(executablePath: validatorPath, targetPid: pid,
                        probes: [ValidatorProbe(stepId: "s", operation: "file-read-data", filterType: "PATH", filterValue: "/etc/hosts")]))
                    if case .success(let output) = v { records += output.verdicts }
                }
            }
            try expectTrue(childDied)
            try expectEqual(records.count, 2)
            try expectEqual(out.termSignal, SIGTERM)
            try expectFalse(out.proceedObserved || out.slots[0].completed)
            for record in records {
                let step = orderedSteps(out, ValidatorOutput(validatorPid: 7, verdicts: [record], reaped: true))[0]
                try expectEqual(step.comparison?.order, "unestablished")
            }
        }
        tk.run("hang_while_waiting: host deadline says release not observed") {
            let out = try orderingWorker("ignore_proceed")
            try expectTrue(out.proceedSet && !out.proceedObserved)
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            try expectEqual(out.termSignal, SIGKILL)
            let summary = classify(workerResult: .success(out), validatorResult: nil, expectedVerdictCount: 0)
            try expectEqual(summary.outcome, NormalizedOutcome.runnerTimeout)
            try expectContains(summary.error ?? "", "release not observed")
        }
        tk.run("signal_after_release_before_attempt: eligible prediction retains query_first") {
            let out = try orderingWorker("signal_after_ack")
            try expectTrue(out.proceedObserved && out.proceedOwnershipEstablished)
            try expectEqual(out.termSignal, SIGTERM)
            try expectFalse(out.slots[0].completed)
            let step = orderedSteps(out, ValidatorOutput(validatorPid: 7, verdicts: [orderingVerdict()], reaped: true))[0]
            try expectEqual(step.comparison?.order, "query_first")
            try expectEqual(step.comparison?.observation, "unavailable")
        }
        tk.run("later cleanup ownership fault preserves already acknowledged order") {
            let receipt = "/tmp/pw-order-" + UUID().uuidString
            defer { try? FileManager.default.removeItem(atPath: receipt) }
            var calls = ChildProcessCalls()
            var interceptedReap = false
            calls.wait = { pid, status, options in
                let rc = Darwin.waitpid(pid, status, options)
                // This fixture exits only after exit_requested. Intercepting
                // its reap places the fault after the host's acknowledgement
                // observation; an attempt receipt alone can race that load.
                if rc == pid { interceptedReap = true; errno = ECHILD; return -1 }
                return rc
            }
            let out = try orderingWorker("proceed_wait|" + receipt, calls: calls)
            try expectTrue(interceptedReap)
            try expectEqual(out.waitErrors?.first?.phase, "exit_grace")
            try expectTrue(out.proceedObserved && out.proceedOwnershipEstablished)
            try expectEqual(out.reaped, false)
            let validator = ValidatorOutput(validatorPid: 7, verdicts: [orderingVerdict()], reaped: true)
            try expectEqual(orderedSteps(out, validator)[0].comparison?.order, "query_first")
        }
        tk.run("a worker with a different identity refuses the header without application or hook") {
            var invoked = false
            let out = try orderingWorker("proceed_wait", suffix: ".identity-mismatch") { _ in invoked = true }
            try expectEqual(out.exitCode, 92)
            try expectFalse(out.applied || invoked || out.proceedSet || out.proceedObserved)
        }
        tk.run("ownership loss before acknowledgement cannot certify later raw publication") {
            let receipt = "/tmp/pw-order-" + UUID().uuidString
            defer {
                try? FileManager.default.removeItem(atPath: receipt)
                try? FileManager.default.removeItem(atPath: receipt + ".ackgate")
            }
            var hookFinished = false, ownershipLost = false, sawLateAck = false
            var calls = ChildProcessCalls()
            calls.wait = { pid, status, options in
                if !hookFinished { return Darwin.waitpid(pid, status, options) }
                if !ownershipLost {
                    ownershipLost = true
                    errno = EIO; return -1
                }
                // The driver has processed EIO and broken ownership before
                // entering cleanup. Only now permit the fixture to acknowledge.
                // ECHILD then ends cleanup; the final acquire snapshot must retain
                // this raw publication without certifying its earlier lifetime.
                FileManager.default.createFile(atPath: receipt + ".ackgate", contents: Data())
                sawLateAck = waitForReceipt(receipt, "ack")
                errno = ECHILD; return -1
            }
            let out = try orderingWorker("proceed_ack_gate|" + receipt, calls: calls) { _ in hookFinished = true }
            try expectTrue(ownershipLost && sawLateAck && out.proceedObserved)
            try expectFalse(out.proceedOwnershipEstablished)
            try expectEqual(out.waitErrors?.map { $0.errno }, [EIO, ECHILD])
            let validator = ValidatorOutput(validatorPid: 7, verdicts: [orderingVerdict()], reaped: true)
            let ordering = buildOrdering(out, validatorOutput: validator, hasQueries: true)
            try expectTrue(ordering.proceed_observed)
            try expectFalse(ordering.worker_lifetime_established || ordering.chainEstablished)
            try expectEqual(orderedSteps(out, validator)[0].comparison?.order, "unestablished")
        }
        for suffix in [".clock-failure", ".clock-failure-later"] {
            tk.run("proceed_clock_failure \(suffix) fails closed at native boundary") {
                let out = try orderingWorker("(version 1)(allow default)", suffix: suffix)
                try expectEqual(out.workerEvidence?.failure?.operation, 11)
                try expectEqual(out.workerEvidence?.failure?.native_kind, 3)
                try expectEqual(out.workerEvidence?.failure?.native_result, -1)
                try expectEqual(out.workerEvidence?.failure?.errno, EIO)
                try expectTrue(out.done)
                try expectFalse(out.proceedObserved || out.slots[0].completed)
            }
        }
    }
    tk.group("ordering eligibility and response-8 encoding") {
        let validator = ValidatorOutput(validatorPid: 7, verdicts: [orderingVerdict()], reaped: true)
        let worker = CWorkerOutput(workerPid: 42, readyByteReceived: true, applied: true, applyRC: 0,
            applyErrno: 0, done: true, exitCode: 0, slots: [CWorkerSlotResult(stepId: "s", rc: 0, errnoVal: 0, completed: true)],
            reaped: true, waitErrors: [], hookInvoked: true, proceedSet: true, proceedObserved: true,
            proceedOwnershipEstablished: true)
        tk.run("eligible record requires complete chain; no worker and each missing link remain explicit") {
            for missing in ["none", "worker", "applied", "apply_rc", "collection", "release", "ack", "ownership", "fault"] {
                var w = worker
                if missing == "applied" { w.applied = false }
                if missing == "apply_rc" { w.applyRC = -1 }
                if missing == "collection" { w.hookInvoked = false }
                if missing == "release" { w.proceedSet = false }
                if missing == "ack" { w.proceedObserved = false }
                if missing == "ownership" { w.proceedOwnershipEstablished = false }
                if missing == "fault" { w.orderingProtocolViolations = ["attempt_before_release"] }
                let envelope = orderingEnvelope(missing == "worker" ? nil : w, validator)
                let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(envelope))
                try expectEqual(decoded.schema_version, PWContract.responseSchema)
                try expectEqual(decoded.steps[0].comparison?.order, missing == "none" ? "query_first" : "unestablished", missing)
                try expectEqual(decoded.runner_subprocess?.ordering != nil, missing != "worker")
            }
        }
        tk.run("NONE queries ignore the submitted unused value when matching native records") {
            var step = orderingStep(); step.sandbox_check.filter = PWRunnerSandboxFilter(kind: "none", value: "")
            var v = orderingVerdict(); v.filterType = "NONE"; v.filterValue = nil
            let validator = ValidatorOutput(validatorPid: 7, verdicts: [v], reaped: true)
            var envelope = orderingEnvelope(worker, validator)
            envelope.steps = orderedSteps(worker, validator, step: step)
            try expectEqual(envelope.steps[0].comparison?.order, "query_first")
            _ = try pwRunnerEncodeJSON(envelope)
        }
        tk.run("no queries, spawn failure and failed apply have distinct terminal decisions") {
            try expectEqual(buildOrdering(worker, validatorOutput: nil, hasQueries: false).validator_disposition, "not_needed")
            try expectEqual(buildOrdering(worker, validatorOutput: nil, hasQueries: true).validator_disposition, "not_spawned")
            var unapplied = worker; unapplied.applied = false; unapplied.applyRC = -1
            unapplied.hookInvoked = false; unapplied.proceedSet = false; unapplied.proceedObserved = false
            unapplied.slots = []; unapplied.proceedOwnershipEstablished = false
            let ordering = buildOrdering(unapplied, validatorOutput: nil, hasQueries: true)
            try expectEqual(ordering.validator_disposition, "not_invoked")
            try expectFalse(ordering.collection_closed_before_proceed || ordering.proceed_set || ordering.proceed_observed)
            var step = orderingStep(); step.sandbox_check.filter.value = "/nonexistent-ordering-path"
            let excluded = orderedSteps(worker, validator, step: step)[0]
            try expectEqual(excluded.sandbox_check.outcome, "prediction_unavailable")
            try expectEqual(excluded.comparison?.order, "unestablished")
        }
        for defect in ["missing", "duplicate", "operation", "filter", "value", "error", "unsupported_operation", "future", "rc", "errno"] {
            tk.run("record eligibility rejects \(defect)") {
                var v = orderingVerdict()
                if defect == "operation" { v.operation = "wrong" }
                if defect == "filter" { v.filterType = "NONE" }
                if defect == "value" { v.filterValue = "/other" }
                if ["error", "unsupported_operation", "future"].contains(defect) { v.outcome = defect }
                if defect == "rc" { v.rc = 1 }
                if defect == "errno" { v.errnoVal = nil }
                let records = defect == "missing" ? [] : defect == "duplicate" ? [v, v] : [v]
                let step = orderedSteps(worker, ValidatorOutput(validatorPid: 7, verdicts: records, reaped: true))[0]
                try expectEqual(step.comparison?.order, "unestablished")
                try expectEqual(step.comparison?.limitations, [])
            }
        }
        tk.run("encoder rejects an order or limitation string outside the vocabulary") {
            for change in ["order", "limitation", "removed_limitation"] {
                var envelope = orderingEnvelope(worker, validator)
                switch change {
                case "order": envelope.steps[0].comparison?.order = "future_order"
                case "limitation": envelope.steps[0].comparison?.limitations = ["future_limit"]
                default: envelope.steps[0].comparison?.limitations = ["query_attempt_order_unestablished"]
                }
                do { _ = try pwRunnerEncodeJSON(envelope); throw TestFailure(message: "\(change) encoded") }
                catch is EncodingError { }
            }
            // The decoder retains unfamiliar strings as transport; it is the
            // encoder and the consumer that refuse them.
            var raw = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(orderingEnvelope(worker, validator))) as! [String: Any]
            var steps = raw["steps"] as! [[String: Any]]
            var comparison = steps[0]["comparison"] as! [String: Any]
            comparison["limitations"] = ["future_limit"]
            steps[0]["comparison"] = comparison; raw["steps"] = steps
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: raw))
            try expectEqual(decoded.steps[0].comparison?.limitations, ["future_limit"])
        }
    }
    tk.group("validator deadline override at the production boundary") {
        tk.run("validator collection may outlast the worker budget without reviving attempts") {
            let path = try orderingFixturePath()
            let parsed = PWRunnerRunSpec(specimen_id: "over-budget",
                policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "proceed_expire:50"),
                probe_plan: [orderingStep(operation: "io_hang")],
                _test_overrides: PWRunnerTestOverrides(validator_io_timeout_ms: 150))
            let result = CWorkerOrchestrator.run(parsed: parsed, policyHash: "fixture", bundleId: nil,
                workerExecutablePath: path, validatorExecutablePath: path + ".validator")
            try expectEqual(result.normalized_outcome, NormalizedOutcome.runnerFailed)
            try expectEqual(result.test_overrides?.validator_io_timeout_ms, 150)
            try expectEqual(result.validator_subprocess?.stdout_collection_stop, "deadline")
            try expectEqual(result.validator_subprocess?.records?.count, 1)
            try expectEqual(result.runner_subprocess?.worker_evidence?.failure?.operation, 11)
            try expectEqual(result.runner_subprocess?.worker_evidence?.failure?.detail, 50)
            try expectEqual(result.runner_subprocess?.ordering?.proceed_set, true)
            try expectEqual(result.runner_subprocess?.ordering?.proceed_observed, false)
            try expectEqual(result.steps[0].sandbox_check.outcome, "allow")
            try expectEqual(result.steps[0].attempt.result_source, "synthetic")
            try expectEqual(result.steps[0].comparison?.order, "unestablished")
            _ = try pwRunnerEncodeJSON(result)
        }
        tk.run("validator_io_timeout_ms returns partial prediction, mirrors request and releases worker") {
            let path = try orderingFixturePath()
            let parsed = PWRunnerRunSpec(specimen_id: "deadline", policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "proceed_wait"),
                probe_plan: [orderingStep(operation: "io_hang")],
                _test_overrides: PWRunnerTestOverrides(validator_io_timeout_ms: 50))
            let result = CWorkerOrchestrator.run(parsed: parsed, policyHash: "fixture", bundleId: nil,
                workerExecutablePath: path, validatorExecutablePath: path + ".validator")
            try expectEqual(result.normalized_outcome, NormalizedOutcome.validatorNoReply)
            try expectContains(result.error ?? "", "50 ms I/O deadline")
            try expectEqual(result.test_overrides?.validator_io_timeout_ms, 50)
            try expectEqual(result.runner_subprocess?.exit_code, 0)
            try expectEqual(result.validator_subprocess?.stdout_collection_stop, "deadline")
            try expectEqual(result.runner_subprocess?.ordering?.proceed_observed, true)
            try expectEqual(result.steps[0].comparison?.order, "query_first")
            try expectEqual(result.steps[0].attempt.outcome, "ok")
            _ = try pwRunnerEncodeJSON(result)
        }
    }
    tk.group("collection closure independent of validator cleanup") {
        tk.run("surviving validator cannot publish after collection closes and worker proceeds") {
            let gateID = UUID().uuidString
            let gate = "/tmp/pw-order-late-" + gateID
            let effect = gate + ".effect"
            defer { try? FileManager.default.removeItem(atPath: gate); try? FileManager.default.removeItem(atPath: effect) }
            var calls = ChildProcessCalls()
            calls.kill = { _, _ in errno = EPERM; return -1 }
            var validator: ValidatorOutput?
            let path = try orderingFixturePath() + ".validator"
            let operation = "io_hang_late:" + gateID
            let out = try orderingWorker("proceed_wait", kind: .fileCreate, target: effect) { pid in
                let result = runValidator(ValidatorClientInput(executablePath: path, targetPid: pid,
                    probes: [ValidatorProbe(stepId: "s", operation: operation, filterType: "PATH", filterValue: "/etc/hosts")],
                    verdictReadTimeoutMs: 100, exitGraceMs: 30), processCalls: calls)
                switch result { case .success(let v): validator = v; case .failure(_, let v): validator = v }
            }
            guard let v = validator else { throw TestFailure(message: "expected partial validator output") }
            defer { cleanupOrderingChild(v.validatorPid) }
            try expectEqual(v.stdoutCollectionStop, "deadline")
            try expectEqual(v.reaped, false)
            try expectEqual(v.terminationRequest?.errno, EPERM)
            try expectTrue(out.proceedObserved && out.slots[0].completed)
            try expectEqual(try String(contentsOfFile: effect), "fixture-effect")
            FileManager.default.createFile(atPath: gate, contents: Data())
            try expectTrue(waitForReceipt(gate, "late_write=-1 errno=\(EPIPE)"))
            try expectEqual(v.verdicts.count, 1)
            try expectEqual(orderedSteps(out, v, step: orderingStep(operation: operation))[0].comparison?.order, "query_first")
        }
        for fault in ["kill", "reap", "ownership"] {
            tk.run("validator_cleanup_unconfirmed_releases_worker: \(fault), EOF while child alive") {
                var calls = ChildProcessCalls()
                if fault == "kill" { calls.kill = { _, _ in errno = EPERM; return -1 } }
                calls.wait = { pid, status, options in
                    if fault == "ownership" || (fault == "reap" && options == 0) { errno = ECHILD; return -1 }
                    return Darwin.waitpid(pid, status, options)
                }
                var validator: ValidatorOutput?
                let path = try orderingFixturePath() + ".validator"
                let effect = "/tmp/pw-order-effect-" + UUID().uuidString
                defer { try? FileManager.default.removeItem(atPath: effect) }
                let out = try orderingWorker("proceed_wait", kind: .fileCreate, target: effect) { pid in
                    let result = runValidator(ValidatorClientInput(executablePath: path, targetPid: pid,
                        probes: [ValidatorProbe(stepId: "s", operation: "hang", filterType: "PATH", filterValue: "/etc/hosts")],
                        verdictReadTimeoutMs: 100, exitGraceMs: 30), processCalls: calls)
                    switch result { case .success(let v): validator = v; case .failure(_, let v): validator = v }
                }
                guard let v = validator else { throw TestFailure(message: "expected partial validator output") }
                defer { cleanupOrderingChild(v.validatorPid) }
                try expectEqual(v.stdoutCollectionStop, "eof")
                try expectEqual(v.reaped, false)
                try expectEqual(v.verdicts.count, 1)
                try expectTrue(out.proceedObserved && out.slots[0].completed)
                try expectEqual(try String(contentsOfFile: effect), "fixture-effect")
                try expectEqual(buildOrdering(out, validatorOutput: v, hasQueries: true).validator_disposition, "unconfirmed")
                var step = orderingStep(operation: "hang")
                step.attempt = PWRunnerAttempt(kind: "file", action: "create", target: effect)
                try expectEqual(orderedSteps(out, v, step: step)[0].comparison?.order, "query_first")
            }
        }
    }
}

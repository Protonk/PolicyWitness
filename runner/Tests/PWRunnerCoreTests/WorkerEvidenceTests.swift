import Darwin
import Foundation
@testable import PWRunnerCore

private func evidenceFixture(_ mode: String, suffix: String = "", params: [CWorkerParam] = []) throws -> CWorkerOutput {
    guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
          FileManager.default.isExecutableFile(atPath: path + suffix) else {
        throw TestFailure(message: "required evidence producer missing")
    }
    let result = runCWorker(CWorkerInput(workerExecutablePath: path + suffix, policy: mode, params: params,
        slots: [CWorkerSlotInput(stepId: "s", attemptKind: .fileOpenRead, target: "/etc/hosts")],
        sentinelTimeoutMs: 100, exitGraceMs: 500))
    switch result {
    case .success(let out): return out
    case .failure(.policyWriteFailed, let partial) where suffix == ".map-failure":
        if let partial { return partial }
        fallthrough
    default: throw TestFailure(message: "driver: \(result)")
    }
}

func runWorkerEvidenceTests(_ tk: TestKit) {
    tk.group("worker evidence publication") {
        tk.run("production C apply failure preserves actual return and errno") {
            let out = try evidenceFixture("(version 1)(allow default)", suffix: ".apply-failure")
            let f = out.workerEvidence?.failure
            try expectEqual(f?.operation, 8)
            try expectEqual(f?.native_kind, 1)
            try expectEqual(f?.native_result, -37)
            try expectEqual(f?.errno, EACCES)
            try expectFalse(out.applied)
            try expectTrue(out.done)
            try expectEqual(out.exitCode, 0)
            try expectContains(classify(workerResult: .success(out), validatorResult: nil,
                expectedVerdictCount: 0).error ?? "", "sandbox_apply")
        }
        tk.run("parameter allocation and repeated assignment failures identify the native call") {
            for (suffix, op): (String, UInt32) in [(".params-CREATE", 3), (".params-SET", 4)] {
                let out = try evidenceFixture("(version 1)(allow default)", suffix: suffix,
                    params: [CWorkerParam(key: "one", value: "1"), CWorkerParam(key: "two", value: "2")])
                let f = out.workerEvidence?.failure
                try expectEqual(f?.operation, op)
                try expectEqual(f?.native_result, op == 3 ? 0 : -23)
                try expectEqual(f?.index, op == 3 ? nil : 1)
                try expectNil(f?.errno, "stale errno from APIs without an errno contract")
                try expectEqual(out.workerEvidence?.progress?.phase, 2)
                try expectFalse(out.applied)
            }
        }
        tk.run("unfamiliar operation code and kind retain signed result and zero errno") {
            let out = try evidenceFixture("unfamiliar")
            let bytes = try pwRunnerEncodeJSON(buildWorkerSubprocess(out))
            let decoded = try pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: bytes)
            try expectEqual(decoded.worker_evidence?.failure?.operation, 239)
            try expectEqual(decoded.worker_evidence?.failure?.code, 4_000_000_001)
            try expectEqual(decoded.worker_evidence?.failure?.native_kind, 77)
            try expectEqual(decoded.worker_evidence?.failure?.native_result, -123)
            try expectEqual(decoded.worker_evidence?.failure?.errno, 0)
            try expectEqual(decoded.worker_evidence?.progress?.index, 17)
            try expectEqual(classify(workerResult: .success(out), validatorResult: nil,
                expectedVerdictCount: 0).outcome, NormalizedOutcome.runnerFailed)
        }
        tk.run("zero operation and code are published evidence not absence") {
            let out = try evidenceFixture("zero_report")
            try expectEqual(out.workerEvidence?.failure_state, "published")
            try expectEqual(out.workerEvidence?.failure?.code, 0)
            try expectNil(out.workerEvidence?.failure?.native_result)
        }
        tk.run("cleanup publication preserves completed slot without erasing deadline") {
            let out = try evidenceFixture("late_publication")
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            try expectTrue(out.done)
            try expectTrue(out.slots[0].completed)
            try expectEqual(out.slots[0].rc, 0)
            try expectEqual(out.workerEvidence?.progress?.phase, 2)
            try expectEqual(classify(workerResult: .success(out), validatorResult: nil,
                expectedVerdictCount: 0).outcome, NormalizedOutcome.runnerTimeout)
        }
        tk.run("started attempt with unpublished poison has no completed result") {
            let out = try evidenceFixture("started_attempt")
            try expectFalse(out.slots[0].completed)
            try expectEqual(out.slots[0].rc, 0, "unpublished poison was read")
            try expectEqual(out.workerEvidence?.progress?.operation, 9)
            try expectEqual(out.workerEvidence?.progress?.phase, 1)
        }
        tk.run("rich missing empty and truncated text keep identical failure classification") {
            for (mode, status) in [("rich", "complete"), ("missing", "absent"),
                                   ("empty", "complete"), ("truncated", "truncated"),
                                   ("after_apply", "complete")] {
                let out = try evidenceFixture("diagnostic_" + mode)
                let evidence = out.workerEvidence!
                try expectEqual(evidence.diagnostic.status, status)
                try expectEqual(evidence.failure?.operation, 5)
                try expectEqual(evidence.failure?.native_result, 0)
                try expectEqual(classify(workerResult: .success(out), validatorResult: nil,
                    expectedVerdictCount: 0).outcome, NormalizedOutcome.runnerFailed)
                if mode == "truncated" { try expectEqual(evidence.diagnostic.length, 4095) }
                if mode == "missing" { try expectNil(evidence.diagnostic.text) }
                if mode == "empty" { try expectEqual(evidence.diagnostic.text, "") }
                if mode == "after_apply" { try expectTrue(out.applied) }
            }
        }
        tk.run("mapping failure exposes exit status without invented worker cause") {
            let out = try evidenceFixture("(version 1)(allow default)", suffix: ".map-failure")
            try expectEqual(out.exitCode, 3)
            try expectNil(out.workerEvidence?.progress)
            try expectNil(out.workerEvidence?.failure)
            try expectEqual(out.workerEvidence?.diagnostic.status, "absent")
            let classified = classify(workerResult: .success(out), validatorResult: nil, expectedVerdictCount: 0)
            try expectEqual(classified.outcome, NormalizedOutcome.runnerFailed)
            try expectContains(classified.error ?? "", "exit code 3")
            try expectFalse((classified.error ?? "").contains("errno"))
        }
        tk.run("closed policy input preserves report-present and report-absent child evidence") {
            guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
                  FileManager.default.isExecutableFile(atPath: path) else {
                throw TestFailure(message: "required worker lifecycle fixture missing; use runner_unit")
            }
            let old = signal(SIGPIPE, SIG_DFL)
            defer { signal(SIGPIPE, old) }
            for report in [false, true] {
                let policy = (report ? "close_report\n" : "close_absent\n") + String(repeating: "x", count: 200_000)
                let result = runCWorker(CWorkerInput(workerExecutablePath: path, policy: policy, slots: []))
                guard case .failure(.policyWriteFailed, let partial) = result, let out = partial else {
                    throw TestFailure(message: "missing policy failure/partial output: \(result)")
                }
                try expectEqual(out.exitCode, 23)
                try expectEqual(out.reaped, true)
                try expectEqual(out.pollStopReason, "policy_write_error")
                try expectEqual(out.policyTransferError?.errno, EPIPE)
                try expectEqual(out.policyTransferError?.bytes_expected, policy.utf8.count)
                try expectTrue(out.policyTransferError!.bytes_written < policy.utf8.count)
                try expectEqual(out.workerEvidence?.failure_state, report ? "published" : "absent")
                try expectEqual(out.workerEvidence?.failure?.code, report ? 987654 : nil)
                try expectEqual(classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0).outcome,
                                NormalizedOutcome.runnerFailed)
                let encoded = try pwRunnerEncodeJSON(buildWorkerSubprocess(out))
                let decoded = try pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: encoded)
                try expectEqual(decoded.policy_transfer_error?.errno, EPIPE)
                try expectEqual(decoded.worker_evidence?.failure_state, report ? "published" : "absent")
            }
        }
        tk.run("early exit with no publication retains unexplained status") {
            let out = try evidenceFixture("early_exit")
            try expectEqual(out.exitCode, 17)
            try expectEqual(out.workerEvidence?.failure_state, "absent")
            try expectNil(out.workerEvidence?.progress)
            try expectEqual(classify(workerResult: .success(out), validatorResult: nil,
                expectedVerdictCount: 0).outcome, NormalizedOutcome.runnerFailed)
        }
        tk.run("pipe failure retains report even when termination fails") {
            guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
                  FileManager.default.isExecutableFile(atPath: path) else {
                throw TestFailure(message: "required worker lifecycle fixture missing; use runner_unit")
            }
            var calls = ChildProcessCalls()
            calls.kill = { _, _ in errno = EPERM; return -1 }
            let result = runCWorker(CWorkerInput(workerExecutablePath: path,
                policy: "close_hang_report\n" + String(repeating: "x", count: 200_000), slots: [],
                exitGraceMs: 50), processCalls: calls)
            guard case .failure(.policyWriteFailed, let partial) = result, let out = partial else {
                throw TestFailure(message: "expected failed transfer with partial report")
            }
            // Independent cleanup of the child intentionally left alive by this control.
            _ = Darwin.kill(out.workerPid, SIGKILL)
            var status: Int32 = 0
            var cleaned = false
            for _ in 0..<100 {
                let rc = Darwin.waitpid(out.workerPid, &status, WNOHANG)
                if rc == out.workerPid || (rc == -1 && errno == ECHILD) { cleaned = true; break }
                usleep(10_000)
            }
            try expectTrue(cleaned, "test-owned fixture must be independently reaped")
            try expectEqual(out.workerEvidence?.failure?.code, 987654)
            try expectEqual(out.policyTransferError?.errno, EPIPE)
            try expectEqual(classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0).outcome, NormalizedOutcome.runnerFailed)
            try expectEqual(out.pollStopReason, "policy_write_error")
            try expectEqual(out.terminationRequest?.rc, -1)
            try expectEqual(out.terminationRequest?.errno, EPERM)
            try expectEqual(out.reaped, false)
            try expectNil(out.exitCode)
            try expectNil(out.termSignal)
        }
        tk.run("publication gates reject incomplete malformed and incompatible payloads") {
            let raw = UnsafeMutableRawPointer.allocate(byteCount: PWShmLayout.regionBytes, alignment: 8)
            defer { raw.deallocate() }
            raw.initializeMemory(as: UInt8.self, repeating: 0, count: PWShmLayout.regionBytes)
            func word(_ offset: Int, _ value: UInt32) { raw.storeBytes(of: value, toByteOffset: offset, as: UInt32.self) }
            let base = raw.assumingMemoryBound(to: UInt8.self)
            let e = PWShmLayout.evidenceOffset
            word(0, 6)
            word(e + PWShmLayout.evidenceOperationOffset, 8)
            word(e + PWShmLayout.evidenceCodeOffset, 123)
            for (pub, state): (UInt32, String) in [(0,"absent"), (2,"incomplete"), (9,"invalid")] {
                word(e + PWShmLayout.evidenceFailurePublishedOffset, pub)
                let got = decodeWorkerEvidence(base)
                try expectEqual(got?.failure_state, state)
                try expectNil(got?.failure)
            }
            word(e + PWShmLayout.evidenceFailurePublishedOffset, 1)
            word(e + PWShmLayout.evidenceErrnoPresentOffset, 2)
            try expectEqual(decodeWorkerEvidence(base)?.failure_state, "invalid")
            word(e + PWShmLayout.evidenceErrnoPresentOffset, 0)
            word(e + PWShmLayout.evidenceNativeKindOffset, 2)
            word(e + PWShmLayout.evidenceNativeResultOffset, 123)
            try expectEqual(decodeWorkerEvidence(base)?.failure_state, "invalid")
            word(e + PWShmLayout.evidenceNativeResultOffset, 0)
            try expectEqual(decodeWorkerEvidence(base)?.failure_state, "published")
            word(e + PWShmLayout.evidenceDiagnosticStateOffset, 1)
            word(e + PWShmLayout.evidenceDiagnosticLengthOffset, 0)
            word(e + PWShmLayout.evidenceHeaderBytes, 65)
            try expectEqual(decodeWorkerEvidence(base)?.diagnostic.status, "invalid")
            word(e + PWShmLayout.evidenceHeaderBytes, 0)
            try expectEqual(decodeWorkerEvidence(base)?.diagnostic.text, "")
            for (state, status): (UInt32, String) in [(0,"absent"),(3,"incomplete"),(27,"unknown"),(1,"invalid")] {
                word(e + PWShmLayout.evidenceDiagnosticStateOffset, state)
                word(e + PWShmLayout.evidenceDiagnosticLengthOffset, UInt32.max)
                let got = decodeWorkerEvidence(base)
                try expectEqual(got?.diagnostic.status, status)
                try expectNil(got?.diagnostic.text)
                try expectEqual(got?.failure?.code, 123)
            }
            word(0, 5)
            try expectNil(decodeWorkerEvidence(base))
        }
        tk.run("excluded query keeps synthetic provenance despite an unexpected verdict") {
            let step = PWRunnerProbeStep(step_id: "s", sandbox_check: PWRunnerSandboxCheck(
                operation: "sysctl-read", filter: PWRunnerSandboxFilter(kind: "sysctl_name", value: "kern.ostype")),
                attempt: PWRunnerAttempt(kind: "sysctl", action: "read", target: "kern.ostype"))
            let verdict = ValidatorVerdict(stepId: "s", operation: "sysctl-read", rc: 0,
                outcome: "allow", rawLine: "controlled unexpected verdict")
            let result = buildStepResults(probePlan: [step], queryPlan: planValidatorQueries([step]), workerOutput: nil,
                validatorOutput: ValidatorOutput(validatorPid: 123, verdicts: [verdict]))[0]
            try expectEqual(result.sandbox_check.outcome, SandboxCheckOutcome.predictionUnavailable)
            try expectEqual(result.sandbox_check.result_source, "synthetic")
            try expectEqual(result.sandbox_check.missing_reason, "query_not_requested")
            try expectNil(result.sandbox_check.native_rc)
        }
        tk.run("never-invoked and short-reply validators expose distinct synthetic results") {
            let step = PWRunnerProbeStep(step_id: "s", sandbox_check: PWRunnerSandboxCheck(
                operation: "file-read-data", filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
                attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts"))
            let worker = try evidenceFixture("started_attempt")
            for invoked in [false, true] {
                let validator = invoked ? ValidatorOutput(validatorPid: 123, verdicts: [], exitCode: 0) : nil
                let got = buildStepResults(probePlan: [step], queryPlan: planValidatorQueries([step]), workerOutput: worker, validatorOutput: validator)[0]
                try expectEqual(got.sandbox_check.result_source, "synthetic")
                try expectEqual(got.sandbox_check.missing_reason, invoked ? "validator_no_verdict" : "validator_not_invoked")
                try expectNil(got.sandbox_check.native_rc)
                try expectEqual(got.attempt.missing_reason, "slot_incomplete")
                try expectNil(got.attempt.native_rc)
                try expectNil(got.drift)
                let json = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(got)) as! [String: Any]
                try expectTrue((json["sandbox_check"] as! [String: Any])["native_rc"] is NSNull)
                try expectTrue((json["attempt"] as! [String: Any])["native_rc"] is NSNull)
            }
        }
    }
}

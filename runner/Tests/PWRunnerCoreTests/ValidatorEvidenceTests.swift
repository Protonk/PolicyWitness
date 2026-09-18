import Darwin
import Foundation
@testable import PWRunnerCore

private let validValidatorLine = "{\"kind\":\"sb_api_validator_verdict\",\"schema_version\":1,\"step_id\":\"s\",\"operation\":\"file-read-data\",\"filter_type\":\"PATH\",\"outcome\":\"allow\",\"rc\":0,\"errno\":0}"

private func validatorFixture(_ mode: String, calls: ChildProcessCalls = ChildProcessCalls()) throws -> ValidatorOutput {
    guard let root = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
          FileManager.default.isExecutableFile(atPath: root + ".validator") else {
        throw TestFailure(message: "required validator fixture missing; use runner_unit")
    }
    var probes = [ValidatorProbe(stepId: "s", operation: mode, filterType: "NONE")]
    if mode == "multibyte" { probes.append(ValidatorProbe(stepId: "tail", operation: "query", filterType: "NONE")) }
    if mode.hasPrefix("close_input") {
        probes.append(ValidatorProbe(stepId: "tail", operation: String(repeating: "x", count: 200000), filterType: "NONE"))
    }
    let result = runValidator(ValidatorClientInput(executablePath: root + ".validator", targetPid: getpid(),
        probes: probes, verdictReadTimeoutMs: 1000, exitGraceMs: 30), processCalls: calls)
    let out: ValidatorOutput
    switch result {
    case .success(let value): out = value
    case .failure(_, let partial):
        guard let partial else { throw TestFailure(message: "fixture failed pre-spawn: \(result)") }
        out = partial
    }
    // Independent cleanup owns any child deliberately left by failed OS calls.
    var status: Int32 = 0
    let first = Darwin.waitpid(out.validatorPid, &status, WNOHANG)
    if first != out.validatorPid && !(first == -1 && errno == ECHILD) {
        _ = Darwin.kill(out.validatorPid, SIGKILL)
        var cleaned = false
        for _ in 0..<100 {
            let rc = Darwin.waitpid(out.validatorPid, &status, WNOHANG)
            if rc == out.validatorPid || (rc == -1 && errno == ECHILD) { cleaned = true; break }
            usleep(10000)
        }
        try expectTrue(cleaned, "validator fixture independent cleanup")
    }
    return out
}

private func assertValidatorDisposition(_ out: ValidatorOutput, expected: String) throws {
    let worker = CWorkerOutput(workerPid: 1, readyByteReceived: true, applied: true,
        applyRC: 0, applyErrno: 0, done: true, exitCode: 0, slots: [], pollStopReason: "done", reaped: true, waitErrors: [])
    let summary = classify(workerResult: .success(worker), validatorResult: .success(out), expectedVerdictCount: 1)
    try expectEqual(summary.outcome, expected)
    try expectEqual(out.verdicts.count, 1, "actual verdict survives cleanup")
    let bytes = try pwRunnerEncodeJSON(buildValidatorSubprocess(out))
    let wire = try pwRunnerDecodeJSON(PWRunnerValidatorSubprocess.self, from: bytes)
    try expectEqual(wire.records?.first?.stepId, "s")
    try expectEqual(wire.reaped, out.reaped)
    try expectEqual(wire.exit_code, out.exitCode.map(Int.init))
    try expectEqual(wire.term_signal, out.termSignal.map(Int.init))
    try expectEqual(wire.termination_request?.rc, out.terminationRequest?.rc)
    try expectEqual(wire.termination_request?.errno, out.terminationRequest?.errno)
    try expectEqual(wire.wait_errors?.map { $0.errno }, out.waitErrors?.map { $0.errno })
    FileHandle.standardOutput.write(Data("  validator JSON: ".utf8) + bytes + Data("\n".utf8))
}

func runValidatorEvidenceTests(_ tk: TestKit) {
    tk.group("validator byte frames and structural contract") {
        tk.run("valid prefix survives invalid UTF-8; empty and malformed are distinct") {
            let prefix = Data((validValidatorLine + "\n").utf8)
            let bad = decodeValidatorFrames(prefix + Data([0xff, 0x0a]))
            try expectEqual(bad.verdicts.map { $0.stepId }, ["s"])
            try expectEqual(bad.fault?.kind, "utf8")
            try expectEqual(bad.fault?.byte_offset, prefix.count)
            try expectEqual(bad.fault?.frame_bytes, 1)
            try expectEqual(bad.fault?.context_b64, Data([0xff]).base64EncodedString())
            try expectEqual(decodeValidatorFrames(Data("not-json\n".utf8)).fault?.kind, "json")
            let empty = decodeValidatorFrames(Data())
            try expectNil(empty.fault)
            try expectEqual(empty.verdicts.count, 0)
        }
        tk.run("multibyte text across read chunks remains intact; incomplete tail rejected") {
            let diagnostic = "{\"kind\":\"sb_api_validator_verdict\",\"schema_version\":1,\"step_id\":null,\"outcome\":\"future_937\",\"error\":\"café €\"}\n"
            let data = Data(diagnostic.utf8)
            for split in 0...data.count {
                var received = Data(data.prefix(split)); received.append(data.suffix(data.count - split))
                let result = decodeValidatorFrames(received)
                try expectNil(result.fault)
                try expectEqual(result.verdicts.first?.error, "café €")
            }
            let tail = decodeValidatorFrames(Data((validValidatorLine + "\n").utf8) + Data([0xe2, 0x82]))
            try expectEqual(tail.verdicts.count, 1)
            try expectEqual(tail.fault?.kind, "utf8")
            try expectEqual(tail.fault?.frame_bytes, 2)
        }
        for outcome in ["allow", "deny"] {
            for key in ["kind", "schema_version", "step_id", "outcome", "operation", "filter_type", "rc", "errno"] {
                for mutation in ["missing", "null", "wrong"] {
                    tk.run("\(outcome) rejects \(mutation) \(key)") {
                        var obj = try JSONSerialization.jsonObject(with: Data(validValidatorLine.utf8)) as! [String: Any]
                        obj["outcome"] = outcome
                        if mutation == "missing" { obj.removeValue(forKey: key) }
                        else if mutation == "null" { obj[key] = NSNull() }
                        else { obj[key] = ["not": "a scalar"] }
                        let received = Data((validValidatorLine + "\n").utf8) + (try JSONSerialization.data(withJSONObject: obj))
                        let result = decodeValidatorFrames(received)
                        try expectEqual(result.verdicts.count, 1)
                        try expectEqual(result.fault?.kind, "structure")
                    }
                }
            }
        }
        tk.run("Boolean and fractional native returns are not integers; rejection context bounded") {
            for value: Any in [true, 0.5, "0"] {
                var obj = try JSONSerialization.jsonObject(with: Data(validValidatorLine.utf8)) as! [String: Any]
                obj["rc"] = value; obj["context"] = String(repeating: "x", count: 900)
                let result = decodeValidatorFrames(try JSONSerialization.data(withJSONObject: obj))
                try expectEqual(result.fault?.kind, "structure")
                try expectEqual(result.fault?.retained_bytes, 256)
                try expectEqual(result.fault?.context_truncated, true)
                try expectEqual(result.verdicts.count, 0)
            }
        }
        tk.run("legitimate no-native and unfamiliar diagnostics retain structure and codes") {
            for outcome in ["parse_error", "bad_filter", "future_937", "unsupported_operation", "error"] {
                let obj: [String: Any] = ["kind": "sb_api_validator_verdict", "schema_version": 1,
                    "step_id": NSNull(), "outcome": outcome, "error": "diagnostic", "future_code": 97319]
                let result = decodeValidatorFrames(try JSONSerialization.data(withJSONObject: obj))
                try expectNil(result.fault)
                try expectEqual(result.verdicts.first?.outcome, outcome)
                try expectNil(result.verdicts.first?.rc)
                try expectContains(result.verdicts.first?.rawLine ?? "", "97319")
            }
        }
        tk.run("duplicate and unexpected records never provide a guessed step join") {
            let v = decodeValidatorFrames(Data(validValidatorLine.utf8)).verdicts[0]
            var unexpected = v; unexpected.stepId = "unexpected"
            var unassociated = v; unassociated.stepId = nil
            let join = associateValidatorVerdicts([v, v, unexpected, unassociated], expected: ["s", "missing"].map { ValidatorProbe(stepId: $0, operation: "file-read-data", filterType: "PATH") })
            try expectEqual(join.byStep.count, 0)
            try expectEqual(Set(join.issues.map { $0.kind }), Set(["duplicate_id", "missing_id", "unexpected_id", "unassociated"]))
        }
    }
    tk.group("validator driver lifecycle and competing observations") {
        for mode in ["clean", "nonzero", "signal", "hang"] {
            tk.run("verdict then \(mode) retains actual disposition") {
                let out = try validatorFixture(mode)
                try assertValidatorDisposition(out, expected: mode == "clean" ? NormalizedOutcome.ok : NormalizedOutcome.validatorUnavailable)
                try expectEqual(out.reaped, true)
                try expectEqual(out.exitCode, mode == "clean" ? 0 : mode == "nonzero" ? 23 : nil)
                try expectEqual(out.termSignal, mode == "hang" ? SIGKILL : mode == "signal" ? SIGTERM : nil)
                try expectEqual(out.terminationRequest?.rc, mode == "hang" ? 0 : nil)
            }
        }
        tk.run("failed kill uses nonblocking final wait and preserves verdict without exit status") {
            var calls = ChildProcessCalls()
            var killed = false
            var finalOptions: [Int32] = []
            calls.kill = { _, _ in killed = true; errno = EPERM; return -1 }
            calls.wait = { pid, status, options in
                if killed { finalOptions.append(options); return 0 }
                return Darwin.waitpid(pid, status, options)
            }
            let out = try validatorFixture("hang", calls: calls)
            try assertValidatorDisposition(out, expected: NormalizedOutcome.validatorUnavailable)
            try expectEqual(finalOptions, [WNOHANG])
            try expectEqual(out.terminationRequest?.errno, EPERM)
            try expectEqual(out.reaped, false)
            try expectNil(out.exitCode)
            try expectNil(out.termSignal)
        }
        tk.run("wait failure and poisoned storage cannot fabricate successful exit") {
            for fault in [ECHILD, EIO, EINTR] {
                var calls = ChildProcessCalls()
                var waits = 0; var kills = 0
                calls.wait = { _, status, _ in waits += 1; status.pointee = 0; errno = fault; return -1 }
                calls.kill = { pid, signal in kills += 1; return Darwin.kill(pid, signal) }
                let out = try validatorFixture("hang", calls: calls)
                try assertValidatorDisposition(out, expected: NormalizedOutcome.validatorUnavailable)
                try expectEqual(out.reaped, false)
                try expectNil(out.exitCode)
                try expectNil(out.termSignal)
                try expectEqual(out.waitErrors?.count, waits)
                try expectTrue(waits <= 4)
                try expectEqual(kills, fault == ECHILD ? 0 : 1)
            }
        }
        tk.run("recovered interruption preserves real clean disposition") {
            var calls = ChildProcessCalls(); var first = true
            calls.wait = { pid, status, options in
                if first { first = false; errno = EINTR; return -1 }
                return Darwin.waitpid(pid, status, options)
            }
            let out = try validatorFixture("clean", calls: calls)
            try assertValidatorDisposition(out, expected: NormalizedOutcome.ok)
            try expectEqual(out.waitErrors?.map { $0.errno }, [EINTR])
        }
        tk.run("I/O deadline retains the received verdict and cleanup observations") {
            let out = try validatorFixture("io_hang")
            try expectContains(out.ioError ?? "", "1000 ms I/O deadline")
            try expectEqual(out.verdicts.first?.stepId, "s")
            try expectTrue(out.rawStdoutBytes > 0)
            try expectNil(out.decodeFault)
            try expectEqual(out.reaped, true)
            try expectEqual(out.termSignal, SIGKILL)
            try expectEqual(out.terminationRequest?.rc, 0)
            let wire = try pwRunnerDecodeJSON(PWRunnerValidatorSubprocess.self,
                from: pwRunnerEncodeJSON(buildValidatorSubprocess(out)))
            try expectEqual(wire.io_error, out.ioError)
            try expectEqual(wire.records?.count, 1)
        }
        tk.run("driver joins multibyte UTF-8 split across delayed pipe writes") {
            let out = try validatorFixture("multibyte")
            try expectNil(out.decodeFault)
            try expectNil(out.ioError)
            try expectEqual(out.exitCode, 0)
            try expectEqual(out.verdicts.map { $0.stepId }, ["s", "tail"])
            try expectEqual(out.verdicts.last?.error, "€")
        }
        tk.run("closed input preserves write failure while the original read deadline expires") {
            let started = Date()
            let out = try validatorFixture("close_input_io_hang")
            try expectTrue(Date().timeIntervalSince(started) < 3, "drain budget was reset or unbounded")
            try expectContains(out.ioError ?? "", "write(probes)")
            try expectContains(out.readError ?? "", "1000 ms I/O deadline")
            try expectEqual(out.stdoutCollectionStop, "deadline")
            try expectEqual(out.decodeFault?.kind, "utf8")
            try expectTrue(out.rawStdoutBytes > 32768)
            try expectEqual(out.verdicts.first?.stepId, "s")
            let wire = try pwRunnerDecodeJSON(PWRunnerValidatorSubprocess.self,
                from: pwRunnerEncodeJSON(buildValidatorSubprocess(out)))
            try expectEqual(wire.stdout_collection_stop, "deadline")
            try expectEqual(wire.read_error, out.readError)
            try expectEqual(wire.io_error, out.ioError)
        }
        tk.run("closed input retains independent I/O and UTF-8 faults plus preceding verdict") {
            let out = try validatorFixture("close_input")
            try expectNotNil(out.ioError)
            try expectEqual(out.stdoutCollectionStop, "eof")
            try expectTrue(out.rawStdoutBytes > 32768)
            try expectNil(out.readError)
            try expectEqual(out.decodeFault?.kind, "utf8")
            try expectEqual(out.verdicts.first?.stepId, "s")
            try expectTrue((out.probeBytesWritten ?? 0) < (out.probeBytesExpected ?? 0))
            let wire = buildValidatorSubprocess(out)
            try expectEqual(wire.io_error, out.ioError)
            try expectEqual(wire.stdout_collection_stop, "eof")
            try expectEqual(wire.decode_fault?.kind, "utf8")
        }
    }
}

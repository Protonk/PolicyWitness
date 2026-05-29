import Darwin
import Foundation

/*
 * ValidatorClient — Swift driver for `sb_api_validator --batch <pid>`.
 * Per RUNNER-RESHAPE-PLAN Step 6.3 (R9 part 2). Mirrors the protocol
 * pinned by tests/suites/validator_batch_mode: NDJSON probes in on
 * stdin, NDJSON verdicts out on stdout, exit 0 on clean EOF, per-probe
 * failures surface as verdicts with outcome ∈ {parse_error, bad_filter}
 * rather than aborting the run.
 *
 * Like CWorker.swift, this module is self-contained — it doesn't depend
 * on PWRunnerService and produces its own typed output. The integration
 * into the runner host happens in Step 6.3c when PWRunnerService gains
 * the use_c_worker flag and starts driving both children together.
 *
 * Flow:
 *   1. Create stdin + stdout pipes.
 *   2. posix_spawn the validator with FDs dup'd to 0 (probes-in) and
 *      1 (verdicts-out). Argv: ["sb_api_validator", "--batch", "<pid>"].
 *   3. Write all probe lines to stdin in one pass; close stdin to
 *      signal EOF to the validator's fgets loop.
 *   4. Read stdout to EOF (the validator exits when stdin EOFs, which
 *      flushes stdout); parse each non-blank line as a JSON verdict.
 *   5. waitpid the validator with a bounded grace; SIGKILL fallback if
 *      it hangs (it shouldn't — the validator is one fgets loop).
 *
 * The probe-write happens BEFORE any reads so a sudden surge of
 * verdicts doesn't block on a still-unsent probe; the validator's
 * batch is small enough (< ~64 KiB) that the kernel pipe buffer
 * absorbs the whole batch in one write call.
 */

// MARK: - Public input/output types

public struct ValidatorProbe {
    public var stepId: String
    public var operation: String
    public var filterType: String          // "NONE" | "PATH" | "GLOBAL_NAME" | ...
    public var filterValue: String?        // required for non-NONE

    public init(stepId: String, operation: String,
                filterType: String, filterValue: String? = nil) {
        self.stepId = stepId
        self.operation = operation
        self.filterType = filterType
        self.filterValue = filterValue
    }
}

public struct ValidatorVerdict {
    public var stepId: String?
    public var operation: String?
    public var filterType: String?
    public var filterTypeId: Int?
    public var filterValue: String?
    public var rc: Int?
    public var errnoVal: Int?
    public var outcome: String             // "allow"|"deny"|"error"|"parse_error"|"bad_filter"
    public var error: String?
    public var rawLine: String             // for debugging
}

public struct ValidatorOutput {
    public var validatorPid: pid_t
    public var verdicts: [ValidatorVerdict]
    public var exitCode: Int32?            // nil if signaled
    public var termSignal: Int32?
    public var sentSigkill: Bool
}

public enum ValidatorClientError: Error, CustomStringConvertible {
    case pipeFailed(String)
    case spawnFailed(String)
    case probeWriteFailed(String)
    case probeSerializationFailed(String)
    case verdictReadFailed(String)
    case verdictParseFailed(line: String, why: String)

    public var description: String {
        switch self {
        case .pipeFailed(let why):                return "pipe: \(why)"
        case .spawnFailed(let why):               return "posix_spawn(sb_api_validator): \(why)"
        case .probeWriteFailed(let why):          return "write(probes): \(why)"
        case .probeSerializationFailed(let why):  return "serialize probes: \(why)"
        case .verdictReadFailed(let why):         return "read(verdicts): \(why)"
        case .verdictParseFailed(let line, let why):
            return "verdict parse failed: \(why); line=\(line)"
        }
    }
}

public enum ValidatorClientResult {
    case success(ValidatorOutput)
    case failure(ValidatorClientError)
}

// MARK: - Driver

public struct ValidatorClientInput {
    public var executablePath: String      // path to sb_api_validator
    public var targetPid: pid_t            // the worker_pid to query
    public var probes: [ValidatorProbe]
    public var verdictReadTimeoutMs: Int   // read deadline
    public var exitGraceMs: Int            // wait deadline before SIGKILL

    public init(executablePath: String,
                targetPid: pid_t,
                probes: [ValidatorProbe],
                verdictReadTimeoutMs: Int = 30_000,
                exitGraceMs: Int = 1_000) {
        self.executablePath = executablePath
        self.targetPid = targetPid
        self.probes = probes
        self.verdictReadTimeoutMs = verdictReadTimeoutMs
        self.exitGraceMs = exitGraceMs
    }
}

public func runValidator(_ input: ValidatorClientInput) -> ValidatorClientResult {
    // Build the NDJSON probe payload up-front so a serialization failure
    // is caught before any FD or child-process state exists.
    let payload: Data
    do {
        payload = try serializeProbes(input.probes)
    } catch let e as ValidatorClientError {
        return .failure(e)
    } catch {
        return .failure(.probeSerializationFailed(String(describing: error)))
    }

    // Pipes.
    var stdinPipe = [Int32](repeating: -1, count: 2)
    var stdoutPipe = [Int32](repeating: -1, count: 2)
    if pipe(&stdinPipe) != 0 {
        return .failure(.pipeFailed("stdin: \(String(cString: strerror(errno)))"))
    }
    if pipe(&stdoutPipe) != 0 {
        close(stdinPipe[0]); close(stdinPipe[1])
        return .failure(.pipeFailed("stdout: \(String(cString: strerror(errno)))"))
    }
    _ = fcntl(stdinPipe[1], F_SETFD, FD_CLOEXEC)
    _ = fcntl(stdoutPipe[0], F_SETFD, FD_CLOEXEC)

    // posix_spawn.
    var fa: posix_spawn_file_actions_t? = nil
    posix_spawn_file_actions_init(&fa)
    defer { posix_spawn_file_actions_destroy(&fa) }
    posix_spawn_file_actions_adddup2(&fa, stdinPipe[0], 0)
    posix_spawn_file_actions_adddup2(&fa, stdoutPipe[1], 1)

    let argv: [String] = [
        "sb_api_validator",
        "--batch",
        String(input.targetPid),
    ]

    var pid: pid_t = 0
    let spawnRC = withCStringArrayCopy(argv) { argvPtr in
        posix_spawn(&pid, input.executablePath, &fa, nil, argvPtr, nil)
    }
    if spawnRC != 0 {
        close(stdinPipe[0]); close(stdinPipe[1])
        close(stdoutPipe[0]); close(stdoutPipe[1])
        return .failure(.spawnFailed(String(cString: strerror(spawnRC))))
    }
    // Close child-owned ends.
    close(stdinPipe[0])
    close(stdoutPipe[1])

    // Write probes to stdin and close. The validator's fgets loop sees
    // EOF and exits after emitting its last verdict.
    let writeRC: Int = payload.withUnsafeBytes { raw -> Int in
        guard let base = raw.baseAddress else { return 0 }
        var written = 0
        while written < raw.count {
            let n = Darwin.write(stdinPipe[1], base.advanced(by: written), raw.count - written)
            if n < 0 {
                if errno == EINTR { continue }
                return -1
            }
            written += n
        }
        return written
    }
    close(stdinPipe[1])
    if writeRC < 0 {
        let why = String(cString: strerror(errno))
        _ = kill(pid, SIGKILL)
        var st: Int32 = 0
        _ = waitpid(pid, &st, 0)
        close(stdoutPipe[0])
        return .failure(.probeWriteFailed(why))
    }

    // Drain stdout to EOF. The validator buffers nothing meaningful in
    // practice — a small probe count produces a small response.
    let stdoutData: Data
    do {
        stdoutData = try readToEOF(fd: stdoutPipe[0],
                                   deadlineMs: input.verdictReadTimeoutMs)
    } catch let e as ValidatorClientError {
        close(stdoutPipe[0])
        _ = kill(pid, SIGKILL)
        var st: Int32 = 0
        _ = waitpid(pid, &st, 0)
        return .failure(e)
    } catch {
        close(stdoutPipe[0])
        _ = kill(pid, SIGKILL)
        var st: Int32 = 0
        _ = waitpid(pid, &st, 0)
        return .failure(.verdictReadFailed(String(describing: error)))
    }
    close(stdoutPipe[0])

    // Parse verdicts. A malformed line is a hard fail — every line the
    // validator emits is a JSON object by contract.
    var verdicts: [ValidatorVerdict] = []
    let raw = String(data: stdoutData, encoding: .utf8) ?? ""
    for line in raw.split(separator: "\n", omittingEmptySubsequences: true) {
        let lineStr = String(line)
        guard let lineData = lineStr.data(using: .utf8) else { continue }
        let parsed: Any
        do {
            parsed = try JSONSerialization.jsonObject(with: lineData, options: [])
        } catch {
            return .failure(.verdictParseFailed(line: lineStr,
                                                 why: String(describing: error)))
        }
        guard let obj = parsed as? [String: Any] else {
            return .failure(.verdictParseFailed(line: lineStr,
                                                 why: "verdict line is not a JSON object"))
        }
        verdicts.append(verdictFromJSONObject(obj, rawLine: lineStr))
    }

    // Reap.
    var status: Int32 = 0
    var reaped: pid_t = 0
    var sentSigkill = false
    let pollNs: UInt64 = 10_000_000
    let iters = max(1, input.exitGraceMs * 1_000_000 / Int(pollNs))
    for _ in 0..<iters {
        let r = waitpid(pid, &status, WNOHANG)
        if r == pid { reaped = r; break }
        sleepNs(pollNs)
    }
    if reaped != pid {
        _ = kill(pid, SIGKILL)
        sentSigkill = true
        _ = waitpid(pid, &status, 0)
    }

    let exitCode: Int32?
    let termSignal: Int32?
    let wifexited = (status & 0x7f) == 0
    if wifexited {
        exitCode = (status >> 8) & 0xff
        termSignal = nil
    } else {
        exitCode = nil
        termSignal = status & 0x7f
    }

    return .success(ValidatorOutput(
        validatorPid: pid,
        verdicts: verdicts,
        exitCode: exitCode,
        termSignal: termSignal,
        sentSigkill: sentSigkill
    ))
}

// MARK: - Probe serialization

private func serializeProbes(_ probes: [ValidatorProbe]) throws -> Data {
    var out = Data()
    for probe in probes {
        var dict: [String: Any] = [
            "step_id":     probe.stepId,
            "operation":   probe.operation,
            "filter_type": probe.filterType,
        ]
        if let v = probe.filterValue {
            dict["filter_value"] = v
        }
        let line: Data
        do {
            line = try JSONSerialization.data(withJSONObject: dict,
                                              options: [.sortedKeys])
        } catch {
            throw ValidatorClientError.probeSerializationFailed(String(describing: error))
        }
        out.append(line)
        out.append(0x0A)  // '\n'
    }
    return out
}

private func verdictFromJSONObject(_ obj: [String: Any], rawLine: String) -> ValidatorVerdict {
    return ValidatorVerdict(
        stepId:        obj["step_id"] as? String,
        operation:     obj["operation"] as? String,
        filterType:    obj["filter_type"] as? String,
        filterTypeId:  obj["filter_type_id"] as? Int,
        filterValue:   obj["filter_value"] as? String,
        rc:            obj["rc"] as? Int,
        errnoVal:      obj["errno"] as? Int,
        outcome:       (obj["outcome"] as? String) ?? "missing_outcome",
        error:         obj["error"] as? String,
        rawLine:       rawLine
    )
}

// MARK: - Helpers

private func readToEOF(fd: Int32, deadlineMs: Int) throws -> Data {
    // Set nonblocking so the loop can yield rather than blocking
    // forever on a hung validator (which shouldn't happen, but the
    // deadline is cheap insurance).
    let flags = fcntl(fd, F_GETFL, 0)
    if flags >= 0 { _ = fcntl(fd, F_SETFL, flags | O_NONBLOCK) }

    var out = Data()
    var buf = [UInt8](repeating: 0, count: 8192)
    let pollNs: UInt64 = 5_000_000
    let iters = max(1, deadlineMs * 1_000_000 / Int(pollNs))
    for _ in 0..<iters {
        let n = buf.withUnsafeMutableBufferPointer { bp -> Int in
            guard let base = bp.baseAddress else { return 0 }
            return Darwin.read(fd, base, bp.count)
        }
        if n > 0 {
            out.append(contentsOf: buf.prefix(n))
            continue                       // keep reading until EOF
        }
        if n == 0 { return out }            // EOF — validator exited
        if errno == EINTR { continue }
        if errno == EAGAIN { sleepNs(pollNs); continue }
        throw ValidatorClientError.verdictReadFailed(
            "read: \(String(cString: strerror(errno)))"
        )
    }
    throw ValidatorClientError.verdictReadFailed(
        "exceeded \(deadlineMs) ms deadline draining validator stdout"
    )
}

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
    public var exitCode: Int32?            // nil if signaled or still alive
    public var termSignal: Int32?
    public var sentSigkill: Bool
    /// Total bytes drained from the validator's stdout. Equal to the
    /// concatenated verdict-line byte length on a clean run; useful on
    /// partial-failure returns to distinguish "validator never wrote
    /// anything" (0) from "validator wrote a partial stream that
    /// failed to parse mid-line" (> 0 with verdicts.count smaller
    /// than expected).
    public var rawStdoutBytes: Int

    public init(validatorPid: pid_t,
                verdicts: [ValidatorVerdict],
                exitCode: Int32? = nil,
                termSignal: Int32? = nil,
                sentSigkill: Bool = false,
                rawStdoutBytes: Int = 0) {
        self.validatorPid = validatorPid
        self.verdicts = verdicts
        self.exitCode = exitCode
        self.termSignal = termSignal
        self.sentSigkill = sentSigkill
        self.rawStdoutBytes = rawStdoutBytes
    }
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
    /// On failure, the driver returns whatever partial state it captured
    /// before the error fired: the validator PID if posix_spawn
    /// succeeded, exit/signal status if the child was reaped, raw byte
    /// count read from stdout, and any verdict lines parsed cleanly
    /// before the failure. Step 6.5's degraded validator_* outcomes
    /// will surface this evidence so a consumer can see "validator
    /// died mid-stream after 3 of 256 verdicts" rather than just
    /// "validator failed."
    ///
    /// `partial` is nil only when the failure happened before any
    /// process state existed (probe serialization, pipe creation,
    /// posix_spawn itself).
    case failure(error: ValidatorClientError, partial: ValidatorOutput?)
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
    // ===== Phase 1: pre-spawn. Any failure here returns .failure with
    // partial=nil because no process or pipe state exists yet. =====

    let payload: Data
    do {
        payload = try serializeProbes(input.probes)
    } catch let e as ValidatorClientError {
        return .failure(error: e, partial: nil)
    } catch {
        return .failure(error: .probeSerializationFailed(String(describing: error)),
                        partial: nil)
    }

    var stdinPipe = [Int32](repeating: -1, count: 2)
    var stdoutPipe = [Int32](repeating: -1, count: 2)
    if pipe(&stdinPipe) != 0 {
        return .failure(
            error: .pipeFailed("stdin: \(String(cString: strerror(errno)))"),
            partial: nil
        )
    }
    if pipe(&stdoutPipe) != 0 {
        close(stdinPipe[0]); close(stdinPipe[1])
        return .failure(
            error: .pipeFailed("stdout: \(String(cString: strerror(errno)))"),
            partial: nil
        )
    }
    _ = fcntl(stdinPipe[1], F_SETFD, FD_CLOEXEC)
    _ = fcntl(stdoutPipe[0], F_SETFD, FD_CLOEXEC)
    // Both parent-side pipe ends must be nonblocking so the I/O loop
    // can drive them interleaved via poll(). Without this, the writer
    // blocks once the kernel pipe buffer (64 KiB on macOS) is full,
    // and a validator that emits verdicts faster than we drain them
    // would deadlock against us. This is the post-Step-6.4 audit
    // BLOCKER fix.
    let stdinFlags = fcntl(stdinPipe[1], F_GETFL, 0)
    if stdinFlags >= 0 { _ = fcntl(stdinPipe[1], F_SETFL, stdinFlags | O_NONBLOCK) }
    let stdoutFlags = fcntl(stdoutPipe[0], F_GETFL, 0)
    if stdoutFlags >= 0 { _ = fcntl(stdoutPipe[0], F_SETFL, stdoutFlags | O_NONBLOCK) }

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
        return .failure(
            error: .spawnFailed(String(cString: strerror(spawnRC))),
            partial: nil
        )
    }
    // Close child-owned ends in the parent.
    close(stdinPipe[0])
    close(stdoutPipe[1])

    // ===== Phase 2: post-spawn. From here on, every failure path
    // captures partial state — parsed verdicts, raw byte count, exit
    // disposition — so the caller can surface degraded evidence. =====

    var stdoutBytes = Data()
    var writeOffset = 0
    var stdinOpen = true
    var stdoutOpen = true
    var ioError: ValidatorClientError? = nil
    let deadline = Date().addingTimeInterval(TimeInterval(input.verdictReadTimeoutMs) / 1000.0)

    // Interleave writes (payload → validator stdin) with reads
    // (validator stdout → stdoutBytes). poll() returns when either FD
    // is ready or the 100 ms tick fires (whichever first) so the
    // deadline check stays sharp.
    while stdinOpen || stdoutOpen {
        if Date() > deadline {
            ioError = .verdictReadFailed(
                "exceeded \(input.verdictReadTimeoutMs) ms I/O deadline; "
                + "wrote \(writeOffset) of \(payload.count) probe bytes; "
                + "drained \(stdoutBytes.count) stdout bytes"
            )
            break
        }

        var pfds: [pollfd] = []
        if stdinOpen {
            pfds.append(pollfd(fd: stdinPipe[1],
                               events: Int16(POLLOUT),
                               revents: 0))
        }
        if stdoutOpen {
            pfds.append(pollfd(fd: stdoutPipe[0],
                               events: Int16(POLLIN),
                               revents: 0))
        }

        let pollRC = pfds.withUnsafeMutableBufferPointer { buf -> Int32 in
            guard let base = buf.baseAddress else { return 0 }
            return poll(base, nfds_t(buf.count), 100)
        }
        if pollRC < 0 {
            if errno == EINTR { continue }
            ioError = .verdictReadFailed("poll: \(String(cString: strerror(errno)))")
            break
        }
        if pollRC == 0 { continue }  // tick, recheck deadline

        for pfd in pfds {
            // Writer side: drain payload bytes into stdin as the kernel
            // buffer drains. When all bytes are out, close stdin to
            // signal EOF to the validator's fgets loop.
            if pfd.fd == stdinPipe[1] && stdinOpen {
                if (pfd.revents & Int16(POLLOUT)) != 0 {
                    let remaining = payload.count - writeOffset
                    if remaining > 0 {
                        let n = payload.withUnsafeBytes { raw -> Int in
                            guard let base = raw.baseAddress else { return 0 }
                            return Darwin.write(stdinPipe[1],
                                                base.advanced(by: writeOffset),
                                                remaining)
                        }
                        if n > 0 {
                            writeOffset += n
                        } else if n < 0 && errno != EAGAIN && errno != EINTR {
                            ioError = .probeWriteFailed(
                                "write after \(writeOffset)/\(payload.count) bytes: "
                                + String(cString: strerror(errno))
                            )
                            close(stdinPipe[1])
                            stdinOpen = false
                        }
                    }
                    if writeOffset >= payload.count {
                        close(stdinPipe[1])
                        stdinOpen = false
                    }
                }
                if (pfd.revents & (Int16(POLLERR) | Int16(POLLHUP) | Int16(POLLNVAL))) != 0 {
                    if writeOffset < payload.count {
                        ioError = .probeWriteFailed(
                            "stdin closed by peer after \(writeOffset)/\(payload.count) bytes"
                        )
                    }
                    close(stdinPipe[1])
                    stdinOpen = false
                }
            }
            // Reader side: append every available byte until EOF.
            if pfd.fd == stdoutPipe[0] && stdoutOpen {
                if (pfd.revents & Int16(POLLIN)) != 0 {
                    var buf = [UInt8](repeating: 0, count: 8192)
                    let n = buf.withUnsafeMutableBufferPointer { bp -> Int in
                        guard let base = bp.baseAddress else { return 0 }
                        return Darwin.read(stdoutPipe[0], base, bp.count)
                    }
                    if n > 0 {
                        stdoutBytes.append(contentsOf: buf.prefix(n))
                    } else if n == 0 {
                        stdoutOpen = false  // validator EOF'd stdout
                    } else if errno != EAGAIN && errno != EINTR {
                        ioError = .verdictReadFailed(
                            "read after \(stdoutBytes.count) bytes: "
                            + String(cString: strerror(errno))
                        )
                        stdoutOpen = false
                    }
                }
                if (pfd.revents & (Int16(POLLERR) | Int16(POLLHUP) | Int16(POLLNVAL))) != 0 {
                    // Drain whatever the kernel still has buffered.
                    var buf = [UInt8](repeating: 0, count: 8192)
                    let n = buf.withUnsafeMutableBufferPointer { bp -> Int in
                        guard let base = bp.baseAddress else { return 0 }
                        return Darwin.read(stdoutPipe[0], base, bp.count)
                    }
                    if n > 0 {
                        stdoutBytes.append(contentsOf: buf.prefix(n))
                    } else {
                        stdoutOpen = false
                    }
                }
            }
        }

        if ioError != nil { break }
    }

    // Idempotent close — paths above may have already closed stdin.
    if stdinOpen { close(stdinPipe[1]) }
    close(stdoutPipe[0])

    // Parse verdicts up to the first malformed line. A parse failure
    // doesn't drop the prior verdicts — they're real evidence.
    var verdicts: [ValidatorVerdict] = []
    var parseError: ValidatorClientError? = nil
    let raw = String(data: stdoutBytes, encoding: .utf8) ?? ""
    for line in raw.split(separator: "\n", omittingEmptySubsequences: true) {
        let lineStr = String(line)
        guard let lineData = lineStr.data(using: .utf8) else { continue }
        do {
            let parsed = try JSONSerialization.jsonObject(with: lineData, options: [])
            guard let obj = parsed as? [String: Any] else {
                parseError = .verdictParseFailed(line: lineStr,
                                                 why: "verdict line is not a JSON object")
                break
            }
            verdicts.append(verdictFromJSONObject(obj, rawLine: lineStr))
        } catch {
            parseError = .verdictParseFailed(line: lineStr,
                                             why: String(describing: error))
            break
        }
    }

    // Reap with grace + SIGKILL fallback.
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

    let output = ValidatorOutput(
        validatorPid: pid,
        verdicts: verdicts,
        exitCode: exitCode,
        termSignal: termSignal,
        sentSigkill: sentSigkill,
        rawStdoutBytes: stdoutBytes.count
    )

    // ioError takes precedence over parseError — an I/O failure means
    // we have a possibly-truncated stdout that the parser may then
    // also have rejected, but the I/O failure is the root cause to
    // report. Either way, every parsed verdict is in `output.verdicts`.
    if let err = ioError ?? parseError {
        return .failure(error: err, partial: output)
    }
    return .success(output)
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

// (readToEOF helper removed in the post-Step-6.4 audit remediation;
// runValidator now drives both pipes via poll(), so the old
// write-then-drain path is gone.)

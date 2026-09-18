import Darwin
import Foundation
import CoreFoundation

/*
 * ValidatorClient — Swift driver for `sb_api_validator --batch <pid>`.
 * Mirrors the protocol pinned by tests/suites/validator_batch_mode:
 * NDJSON probes in on stdin, NDJSON verdicts out on stdout, exit 0
 * on clean EOF, per-probe failures surface as verdicts with outcome
 * ∈ {parse_error, bad_filter} rather than aborting the run.
 *
 * Like CWorker.swift, this module is self-contained — it doesn't depend
 * on PWRunnerService and produces its own typed output. Both children
 * are driven together by CWorkerOrchestrator.
 *
 * Flow:
 *   1. Create stdin + stdout pipes.
 *   2. posix_spawn the validator with FDs dup'd to 0 (probes-in) and
 *      1 (verdicts-out). Argv: ["sb_api_validator", "--batch", "<pid>"].
 *   3. Interleave nonblocking writes and reads under the I/O deadline.
 *   4. Frame received bytes, then strictly decode UTF-8, JSON and structure.
 *   5. Use the shared child observer for grace, termination and successful reap.
 * Transport, decoding, association and process disposition remain independent.
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
    public var reaped: Bool?
    public var terminationRequest: PWRunnerTerminationRequest?
    public var waitErrors: [PWRunnerWaitError]?
    public var ioError: String?
    public var decodeFault: PWValidatorDecodeFault?
    public var expectedProbes: [ValidatorProbe]?
    public var readError: String?
    public var stdoutCollectionStop: String?
    public var expectedStepIds: [String]? { expectedProbes?.map { $0.stepId } }
    public var probeBytesWritten: Int?
    public var probeBytesExpected: Int?

    public init(validatorPid: pid_t,
                verdicts: [ValidatorVerdict],
                exitCode: Int32? = nil,
                termSignal: Int32? = nil,
                sentSigkill: Bool = false,
                rawStdoutBytes: Int = 0,
                reaped: Bool? = nil,
                terminationRequest: PWRunnerTerminationRequest? = nil,
                waitErrors: [PWRunnerWaitError]? = nil,
                ioError: String? = nil,
                decodeFault: PWValidatorDecodeFault? = nil,
                expectedProbes: [ValidatorProbe]? = nil,
                readError: String? = nil,
                stdoutCollectionStop: String? = nil,
                probeBytesWritten: Int? = nil,
                probeBytesExpected: Int? = nil) {
        self.validatorPid = validatorPid
        self.verdicts = verdicts
        self.exitCode = exitCode
        self.termSignal = termSignal
        self.sentSigkill = sentSigkill
        self.reaped = reaped
        self.terminationRequest = terminationRequest
        self.waitErrors = waitErrors
        self.ioError = ioError
        self.decodeFault = decodeFault
        self.expectedProbes = expectedProbes
        self.readError = readError
        self.stdoutCollectionStop = stdoutCollectionStop
        self.probeBytesWritten = probeBytesWritten
        self.probeBytesExpected = probeBytesExpected
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
    case verdictDecodeFailed(PWValidatorDecodeFault)

    public var description: String {
        switch self {
        case .pipeFailed(let why):                return "pipe: \(why)"
        case .spawnFailed(let why):               return "posix_spawn(sb_api_validator): \(why)"
        case .probeWriteFailed(let why):          return "write(probes): \(why)"
        case .probeSerializationFailed(let why):  return "serialize probes: \(why)"
        case .verdictReadFailed(let why):         return "read(verdicts): \(why)"
        case .verdictDecodeFailed(let fault):
            return "validator \(fault.kind) failure at byte \(fault.byte_offset): \(fault.message)"
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
    /// before the failure. The degraded validator_* outcomes surface
    /// this evidence so a consumer can see "validator died mid-stream
    /// after 3 of 256 verdicts" rather than just "validator failed."
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
    runValidator(input, processCalls: ChildProcessCalls())
}

func runValidator(_ input: ValidatorClientInput, processCalls: ChildProcessCalls) -> ValidatorClientResult {
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
    // Close all original descriptors across exec; only explicit dup2 targets
    // belong in the child. Suppress SIGPIPE on this writer, not process-wide.
    func pipeSetupFailure(_ operation: String) -> ValidatorClientResult {
        let detail = "\(operation): errno=\(errno) \(String(cString: strerror(errno)))"
        for fd in stdinPipe + stdoutPipe { close(fd) }
        return .failure(error: .pipeFailed(detail), partial: nil)
    }
    for fd in stdinPipe + stdoutPipe {
        if fcntl(fd, F_SETFD, FD_CLOEXEC) == -1 { return pipeSetupFailure("F_SETFD") }
    }
    if fcntl(stdinPipe[1], F_SETNOSIGPIPE, 1) == -1 { return pipeSetupFailure("F_SETNOSIGPIPE") }
    for fd in [stdinPipe[1], stdoutPipe[0]] {
        let flags = fcntl(fd, F_GETFL, 0)
        if flags == -1 || fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1 { return pipeSetupFailure("O_NONBLOCK") }
    }

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
    var readError: ValidatorClientError? = nil
    var collectionStop = "eof"
    let deadline = Date().addingTimeInterval(TimeInterval(input.verdictReadTimeoutMs) / 1000.0)

    // Interleave writes (payload → validator stdin) with reads
    // (validator stdout → stdoutBytes). poll() returns when either FD
    // is ready or the 100 ms tick fires (whichever first) so the
    // deadline check stays sharp.
    while stdinOpen || stdoutOpen {
        if Date() > deadline {
            collectionStop = stdoutOpen ? "deadline" : "eof"
            readError = .verdictReadFailed(
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
            collectionStop = "poll_error"
            readError = .verdictReadFailed("poll: \(String(cString: strerror(errno)))")
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
                    if stdinOpen && writeOffset >= payload.count {
                        close(stdinPipe[1])
                        stdinOpen = false
                    }
                }
                if stdinOpen && (pfd.revents & (Int16(POLLERR) | Int16(POLLHUP) | Int16(POLLNVAL))) != 0 {
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
                if (pfd.revents & (Int16(POLLIN) | Int16(POLLHUP) | Int16(POLLERR) | Int16(POLLNVAL))) != 0 {
                    var buf = [UInt8](repeating: 0, count: 8192)
                    let n = buf.withUnsafeMutableBytes { Darwin.read(stdoutPipe[0], $0.baseAddress!, $0.count) }
                    if n > 0 { stdoutBytes.append(contentsOf: buf.prefix(n)) }
                    else if n == 0 { stdoutOpen = false }
                    else if errno != EAGAIN && errno != EINTR {
                        collectionStop = "read_error"
                        readError = .verdictReadFailed("read after \(stdoutBytes.count) bytes: errno=\(errno) \(String(cString: strerror(errno)))")
                        stdoutOpen = false
                    }
                }
            }
        }

        if readError != nil { break }
        // A failed input write does not end independent stdout collection.
        // Continue under the original deadline until EOF or a read failure.
    }

    // Idempotent close — paths above may have already closed stdin.
    if stdinOpen { close(stdinPipe[1]) }
    close(stdoutPipe[0])

    let decoded = decodeValidatorFrames(stdoutBytes)

    // Status is usable only when the shared observer actually reaped this PID.
    var process = ChildProcessState(pid: pid, calls: processCalls)
    let pollNs: UInt64 = 10_000_000
    let iters = max(1, input.exitGraceMs * 1_000_000 / Int(pollNs))
    for _ in 0..<iters {
        let observation = process.wait(options: WNOHANG, phase: "exit_grace")
        if observation != .pending { break }
        sleepNs(pollNs)
    }
    process.terminate()
    var exitCode: Int32? = nil
    var termSignal: Int32? = nil
    if let status = process.status, (status & 0x7f) == 0 {
        exitCode = (status >> 8) & 0xff
    } else if let status = process.status, (((status & 0x7f) + 1) >> 1 > 0) {
        termSignal = status & 0x7f
    }
    let output = ValidatorOutput(
        validatorPid: pid, verdicts: decoded.verdicts,
        exitCode: exitCode, termSignal: termSignal,
        sentSigkill: process.terminationRequest != nil, rawStdoutBytes: stdoutBytes.count,
        reaped: process.status != nil, terminationRequest: process.terminationRequest,
        waitErrors: process.waitErrors, ioError: (ioError ?? readError)?.description,
        decodeFault: decoded.fault, expectedProbes: input.probes,
        readError: readError?.description, stdoutCollectionStop: collectionStop,
        probeBytesWritten: writeOffset, probeBytesExpected: payload.count
    )
    // Preserve both independent faults; precedence only selects the summary.
    if let error = ioError ?? readError { return .failure(error: error, partial: output) }
    if let fault = decoded.fault { return .failure(error: .verdictDecodeFailed(fault), partial: output) }
    return .success(output)
}

// MARK: - Probe serialization

func serializeProbes(_ probes: [ValidatorProbe]) throws -> Data {
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

// MARK: - Receiver contract

/// NDJSON is framed on byte LF before strict UTF-8 decoding. Empty frames are
/// ignored; a final nonempty fragment is decoded too. Stop on the first fault.
/// All records require kind=sb_api_validator_verdict, integer schema_version=1,
/// present string-or-null step_id and nonempty string outcome. Known optional
/// fields must have their declared type or null (Bool is not an integer).
/// Allow/deny require nonempty step_id, operation, filter_type and integer rc,
/// errno. Diagnostic outcomes require string error, but may omit native results.
/// Unfamiliar diagnostic outcomes and extra JSON fields are retained. Rejected
/// bytes are context only, never accepted evidence. See the routing inventory.
struct ValidatorDecodedFrames {
    var verdicts: [ValidatorVerdict] = []
    var fault: PWValidatorDecodeFault? = nil
}

func decodeValidatorFrames(_ bytes: Data) -> ValidatorDecodedFrames {
    var result = ValidatorDecodedFrames()
    var offset = 0
    for frame in bytes.split(separator: 0x0a, omittingEmptySubsequences: false) {
        defer { offset += frame.count + 1 }
        if frame.isEmpty { continue }
        func reject(_ kind: String, _ message: String) -> ValidatorDecodedFrames {
            let prefix = Data(frame.prefix(256))
            result.fault = PWValidatorDecodeFault(kind: kind, message: message,
                byte_offset: offset, frame_bytes: frame.count, retained_bytes: prefix.count,
                context_b64: prefix.base64EncodedString(), context_truncated: frame.count > prefix.count)
            return result
        }
        guard let line = String(data: frame, encoding: .utf8) else {
            return reject("utf8", "invalid UTF-8 in validator reply")
        }
        let json: Any
        do { json = try JSONSerialization.jsonObject(with: Data(frame), options: [.fragmentsAllowed]) }
        catch { return reject("json", "verdict parse failed: " + String(describing: error)) }
        guard let obj = json as? [String: Any] else { return reject("structure", "verdict must be an object") }
        if let why = validatorStructureError(obj) { return reject("structure", why) }
        result.verdicts.append(ValidatorVerdict(
            stepId: obj["step_id"] as? String, operation: obj["operation"] as? String,
            filterType: obj["filter_type"] as? String, filterTypeId: validatorInteger(obj["filter_type_id"]),
            filterValue: obj["filter_value"] as? String, rc: validatorInteger(obj["rc"]),
            errnoVal: validatorInteger(obj["errno"]), outcome: obj["outcome"] as! String,
            error: obj["error"] as? String, rawLine: line))
    }
    return result
}

private func validatorInteger(_ value: Any?) -> Int? {
    guard let n = value as? NSNumber, CFGetTypeID(n) != CFBooleanGetTypeID(),
          String(cString: n.objCType) != "d", String(cString: n.objCType) != "f" else { return nil }
    return Int(n.stringValue)
}

private func validatorStructureError(_ obj: [String: Any]) -> String? {
    guard obj["kind"] as? String == "sb_api_validator_verdict" else { return "missing or invalid kind" }
    guard validatorInteger(obj["schema_version"]) == 1 else { return "missing or invalid schema_version" }
    guard obj.keys.contains("step_id") else { return "missing step_id (string or null required)" }
    guard let outcome = obj["outcome"] as? String, !outcome.isEmpty else { return "missing or invalid outcome" }
    for key in ["step_id", "operation", "filter_type", "filter_value", "error"] {
        if let value = obj[key], !(value is NSNull), !(value is String) { return "invalid string field \(key)" }
    }
    for key in ["rc", "errno", "filter_type_id"] {
        if let value = obj[key], !(value is NSNull), validatorInteger(value) == nil { return "invalid integer field \(key)" }
    }
    if outcome == "allow" || outcome == "deny" {
        for key in ["step_id", "operation", "filter_type"] {
            guard let value = obj[key] as? String, !value.isEmpty else { return "\(outcome) requires \(key)" }
        }
        for key in ["rc", "errno"] {
            if validatorInteger(obj[key]) == nil { return "\(outcome) requires integer \(key)" }
        }
    } else if !(obj["error"] is String) { return "diagnostic outcome requires string error" }
    return nil
}

/// Duplicate IDs are ambiguous, so none of their records enters the step join.
/// All accepted records remain at run scope, including unknown and null IDs.
func associateValidatorVerdicts(_ verdicts: [ValidatorVerdict], expected: [ValidatorProbe]) -> (byStep: [String: ValidatorVerdict], issues: [PWValidatorAssociationIssue]) {
    let wanted = Set(expected.map { $0.stepId })
    let groups = Dictionary(grouping: verdicts.compactMap { v in v.stepId.map { ($0, v) } }, by: { $0.0 })
    var byStep: [String: ValidatorVerdict] = [:]
    var issues: [PWValidatorAssociationIssue] = []
    for probe in expected {
        let id = probe.stepId
        let matches = groups[id] ?? []
        if matches.count == 1 {
            let v = matches[0].1
            // Diagnostics may omit query metadata. Any supplied metadata must
            // agree; predictions must describe exactly the submitted query.
            let prediction = v.outcome == "allow" || v.outcome == "deny"
            let mismatch = (prediction || v.operation != nil) && v.operation != probe.operation
                || (prediction || v.filterType != nil) && v.filterType != probe.filterType
                || (prediction || v.filterValue != nil) && v.filterValue != probe.filterValue
            if mismatch { issues.append(PWValidatorAssociationIssue(kind: "query_mismatch", step_id: id, count: 1)) }
            else { byStep[id] = v }
        }
        else { issues.append(PWValidatorAssociationIssue(kind: matches.isEmpty ? "missing_id" : "duplicate_id", step_id: id, count: matches.count)) }
    }
    for id in groups.keys.sorted() where !wanted.contains(id) {
        issues.append(PWValidatorAssociationIssue(kind: "unexpected_id", step_id: id, count: groups[id]!.count))
    }
    let unassociated = verdicts.filter { $0.stepId == nil }.count
    if unassociated > 0 { issues.append(PWValidatorAssociationIssue(kind: "unassociated", count: unassociated)) }
    return (byStep, issues)
}

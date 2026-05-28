import Foundation
import Darwin

private let defaultWorkerTimeoutSeconds: TimeInterval = 90
private let workerExitGraceSeconds: TimeInterval = 1

struct WorkerSpawnError: Error, CustomStringConvertible {
    var message: String

    var description: String { message }
}

struct WorkerProcessResult {
    var report: PWRunnerWorkerReport?
    var subprocess: PWRunnerSubprocess
    var rc: Int
    var normalized_outcome: String
    var error: String?
}

private enum WorkerReadOutcome {
    case frame(Data)
    case eof
    case timeout
    case failure(String)
}

private struct WorkerWaitObservation {
    var exitCode: Int?
    var termSignal: Int?
    var timedOut: Bool
    var error: String?
}

enum WorkerProcess {
    static func run(
        requestData: Data,
        expectedStepCount: Int,
        executablePathOverride: String? = nil,
        timeoutMsOverride: Int? = nil
    ) -> Result<WorkerProcessResult, WorkerSpawnError> {
        var sockets = [Int32](repeating: -1, count: 2)
        if socketpair(AF_UNIX, SOCK_STREAM, 0, &sockets) != 0 {
            return .failure(WorkerSpawnError(message: "socketpair failed: \(String(cString: strerror(errno)))"))
        }
        let hostFD = sockets[0]
        let workerFD = sockets[1]
        disableSigpipe(hostFD)
        disableSigpipe(workerFD)

        // The override path is consumed at the posix_spawn boundary so a
        // hostile value produces a real ENOENT/ENOEXEC, not a stubbed
        // failure inside our wrapper.
        let spawnResult = spawnWorker(
            workerFD: workerFD,
            hostFD: hostFD,
            executablePathOverride: executablePathOverride
        )
        close(workerFD)

        let workerTimeoutSeconds = effectiveWorkerTimeoutSeconds(override: timeoutMsOverride)

        switch spawnResult {
        case .failure(let err):
            close(hostFD)
            return .failure(err)
        case .success(let pid):
            defer { close(hostFD) }
            do {
                try writeWorkerFrame(fd: hostFD, data: requestData)
                shutdown(hostFD, SHUT_WR)
            } catch {
                kill(pid, SIGKILL)
                let wait = waitForWorkerExit(pid: pid, deadline: Date().addingTimeInterval(workerExitGraceSeconds), killOnTimeout: true)
                let subprocess = PWRunnerSubprocess(
                    pid: Int(pid),
                    term_signal: wait.termSignal,
                    exit_code: wait.exitCode,
                    partial_steps: false
                )
                return .success(
                    WorkerProcessResult(
                        report: nil,
                        subprocess: subprocess,
                        rc: 1,
                        normalized_outcome: "runner_failed",
                        error: "failed to send request to worker: \(error)"
                    )
                )
            }

            let deadline = Date().addingTimeInterval(workerTimeoutSeconds)
            let readOutcome = readWorkerFrameWithDeadline(fd: hostFD, deadline: deadline)
            var report: PWRunnerWorkerReport? = nil
            var readError: String? = nil
            var timedOut = false

            switch readOutcome {
            case .frame(let data):
                do {
                    report = try pwRunnerDecodeJSON(PWRunnerWorkerReport.self, from: data)
                } catch {
                    readError = "worker report decode failed: \(error)"
                }
            case .eof:
                readError = "worker exited without writing a report"
            case .timeout:
                timedOut = true
                readError = "worker timed out before writing a report"
            case .failure(let message):
                readError = message
            }

            let waitDeadline = report == nil
                ? deadline
                : Date().addingTimeInterval(workerExitGraceSeconds)
            let wait = waitForWorkerExit(
                pid: pid,
                deadline: waitDeadline,
                killOnTimeout: true
            )
            if wait.timedOut {
                timedOut = true
            }

            let partialSteps = report.map { partialStepOutput($0.steps.count, expectedStepCount: expectedStepCount) } ?? false
            let subprocess = PWRunnerSubprocess(
                pid: Int(pid),
                term_signal: wait.termSignal,
                exit_code: wait.exitCode,
                partial_steps: partialSteps
            )

            let classification = classifyWorkerResult(
                report: report,
                subprocess: subprocess,
                timedOut: timedOut,
                transportError: readError,
                waitError: wait.error
            )
            return .success(
                WorkerProcessResult(
                    report: report,
                    subprocess: subprocess,
                    rc: classification.rc,
                    normalized_outcome: classification.outcome,
                    error: classification.error
                )
            )
        }
    }
}

private func disableSigpipe(_ fd: Int32) {
    var one: Int32 = 1
    setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &one, socklen_t(MemoryLayout<Int32>.size))
}

private func spawnWorker(
    workerFD: Int32,
    hostFD: Int32,
    executablePathOverride: String?
) -> Result<pid_t, WorkerSpawnError> {
    let executable: String
    if let override = executablePathOverride, !override.isEmpty {
        executable = override
    } else {
        do {
            executable = try currentExecutablePath()
        } catch {
            return .failure(WorkerSpawnError(message: "failed to resolve worker executable: \(error)"))
        }
    }

    var actions: posix_spawn_file_actions_t? = nil
    var attrs: posix_spawnattr_t? = nil
    if posix_spawn_file_actions_init(&actions) != 0 {
        return .failure(WorkerSpawnError(message: "posix_spawn_file_actions_init failed"))
    }
    defer { posix_spawn_file_actions_destroy(&actions) }
    if posix_spawnattr_init(&attrs) != 0 {
        return .failure(WorkerSpawnError(message: "posix_spawnattr_init failed"))
    }
    defer { posix_spawnattr_destroy(&attrs) }

    let flags = Int16(POSIX_SPAWN_CLOEXEC_DEFAULT)
    let flagsRC = posix_spawnattr_setflags(&attrs, flags)
    if flagsRC != 0 {
        return .failure(WorkerSpawnError(message: "posix_spawnattr_setflags failed: \(String(cString: strerror(flagsRC)))"))
    }

    let dupRC = posix_spawn_file_actions_adddup2(&actions, workerFD, pwRunnerWorkerRequestFD)
    if dupRC != 0 {
        return .failure(WorkerSpawnError(message: "posix_spawn_file_actions_adddup2 failed: \(String(cString: strerror(dupRC)))"))
    }
    if workerFD != pwRunnerWorkerRequestFD {
        _ = posix_spawn_file_actions_addclose(&actions, workerFD)
    }
    if hostFD != pwRunnerWorkerRequestFD {
        _ = posix_spawn_file_actions_addclose(&actions, hostFD)
    }

    let argvStrings = [executable, pwRunnerWorkerModeArgument]
    let envStrings = ProcessInfo.processInfo.environment
        .map { "\($0.key)=\($0.value)" }
        .sorted()

    return withCStringArray(argvStrings) { argv in
        withCStringArray(envStrings) { envp in
            var pid: pid_t = 0
            let rc = executable.withCString { path in
                posix_spawn(&pid, path, &actions, &attrs, argv, envp)
            }
            if rc != 0 {
                return .failure(WorkerSpawnError(message: "posix_spawn failed: \(String(cString: strerror(rc)))"))
            }
            return .success(pid)
        }
    }
}

private func currentExecutablePath() throws -> String {
    var size = UInt32(PATH_MAX)
    var buffer = [CChar](repeating: 0, count: Int(size))
    var rc = buffer.withUnsafeMutableBufferPointer { ptr in
        _NSGetExecutablePath(ptr.baseAddress, &size)
    }
    if rc != 0 {
        buffer = [CChar](repeating: 0, count: Int(size) + 1)
        rc = buffer.withUnsafeMutableBufferPointer { ptr in
            _NSGetExecutablePath(ptr.baseAddress, &size)
        }
    }
    guard rc == 0 else {
        throw WorkerSpawnError(message: "_NSGetExecutablePath failed")
    }
    let unresolved = String(cString: buffer)
    var resolved = [CChar](repeating: 0, count: Int(PATH_MAX))
    if unresolved.withCString({ realpath($0, &resolved) }) != nil {
        return String(cString: resolved)
    }
    return unresolved
}

private func withCStringArray<T>(
    _ strings: [String],
    _ body: (UnsafeMutablePointer<UnsafeMutablePointer<CChar>?>?) -> T
) -> T {
    var pointers: [UnsafeMutablePointer<CChar>?] = strings.map { strdup($0) }
    pointers.append(nil)
    defer {
        for ptr in pointers {
            if let ptr {
                free(ptr)
            }
        }
    }
    return pointers.withUnsafeMutableBufferPointer { buffer in
        body(buffer.baseAddress)
    }
}

private func readWorkerFrameWithDeadline(fd: Int32, deadline: Date) -> WorkerReadOutcome {
    var bytes: [UInt8] = []
    bytes.reserveCapacity(4096)
    while true {
        if bytes.count >= 4 {
            let length = bytes[0..<4].reduce(UInt32(0)) { ($0 << 8) | UInt32($1) }
            let count = Int(length)
            if count > maxWorkerFrameBytes {
                return .failure("worker report too large: \(count) bytes")
            }
            if bytes.count >= 4 + count {
                return .frame(Data(bytes[4..<(4 + count)]))
            }
        }

        let remainingMs = millisecondsUntil(deadline)
        if remainingMs <= 0 {
            return .timeout
        }

        var pollFD = pollfd(fd: fd, events: Int16(POLLIN | POLLHUP | POLLERR), revents: 0)
        let pollRC = poll(&pollFD, 1, min(remainingMs, 1000))
        if pollRC < 0 {
            if errno == EINTR {
                continue
            }
            return .failure("poll failed while reading worker report: \(String(cString: strerror(errno)))")
        }
        if pollRC == 0 {
            continue
        }

        var chunk = [UInt8](repeating: 0, count: 8192)
        let got = chunk.withUnsafeMutableBytes { raw -> Int in
            guard let base = raw.baseAddress else { return -1 }
            return Darwin.read(fd, base, raw.count)
        }
        if got > 0 {
            bytes.append(contentsOf: chunk.prefix(got))
            continue
        }
        if got == 0 {
            return bytes.isEmpty ? .eof : .failure("worker report truncated before EOF")
        }
        if errno == EINTR {
            continue
        }
        return .failure("read failed while reading worker report: \(String(cString: strerror(errno)))")
    }
}

private func waitForWorkerExit(
    pid: pid_t,
    deadline: Date,
    killOnTimeout: Bool
) -> WorkerWaitObservation {
    var status: Int32 = 0
    while true {
        let rc = waitpid(pid, &status, WNOHANG)
        if rc == pid {
            return WorkerWaitObservation(
                exitCode: waitExitCode(status),
                termSignal: waitTermSignal(status),
                timedOut: false,
                error: nil
            )
        }
        if rc < 0 {
            if errno == EINTR {
                continue
            }
            return WorkerWaitObservation(
                exitCode: nil,
                termSignal: nil,
                timedOut: false,
                error: "waitpid failed: \(String(cString: strerror(errno)))"
            )
        }
        if millisecondsUntil(deadline) <= 0 {
            if killOnTimeout {
                kill(pid, SIGKILL)
                while true {
                    let killedRC = waitpid(pid, &status, 0)
                    if killedRC == pid {
                        return WorkerWaitObservation(
                            exitCode: waitExitCode(status),
                            termSignal: waitTermSignal(status),
                            timedOut: true,
                            error: nil
                        )
                    }
                    if killedRC < 0 && errno != EINTR {
                        return WorkerWaitObservation(
                            exitCode: nil,
                            termSignal: nil,
                            timedOut: true,
                            error: "waitpid after SIGKILL failed: \(String(cString: strerror(errno)))"
                        )
                    }
                }
            }
            return WorkerWaitObservation(exitCode: nil, termSignal: nil, timedOut: true, error: nil)
        }
        usleep(10_000)
    }
}

private func effectiveWorkerTimeoutSeconds(override: Int?) -> TimeInterval {
    guard let override, override > 0 else {
        return defaultWorkerTimeoutSeconds
    }
    // The override is in milliseconds; the host uses TimeInterval seconds.
    // Floor at 50ms — anything shorter is racy against posix_spawn + first
    // worker syscall on a modern Mac and produces non-deterministic results.
    let ms = max(override, 50)
    return TimeInterval(ms) / 1000.0
}

private func millisecondsUntil(_ deadline: Date) -> Int32 {
    let ms = Int(deadline.timeIntervalSinceNow * 1000)
    if ms <= 0 {
        return 0
    }
    return Int32(min(ms, Int(Int32.max)))
}

private func waitExitCode(_ status: Int32) -> Int? {
    if (status & 0x7f) == 0 {
        return Int((status >> 8) & 0xff)
    }
    return nil
}

private func waitTermSignal(_ status: Int32) -> Int? {
    let sig = status & 0x7f
    if sig != 0 && sig != 0x7f {
        return Int(sig)
    }
    return nil
}

private func partialStepOutput(_ count: Int, expectedStepCount: Int) -> Bool {
    count > 0 && count < expectedStepCount
}

private func classifyWorkerResult(
    report: PWRunnerWorkerReport?,
    subprocess: PWRunnerSubprocess,
    timedOut: Bool,
    transportError: String?,
    waitError: String?
) -> (rc: Int, outcome: String, error: String?) {
    if timedOut {
        return (1, "runner_timeout", transportError ?? waitError ?? "worker timed out")
    }
    if let report {
        return (report.rc, report.normalized_outcome, report.error ?? waitError)
    }
    if let sig = subprocess.term_signal {
        // No worker report + fatal signal is the bug-report signature: the worker
        // spawned, applied the policy, and was terminated before it could write a
        // report. On macOS this happens through two paths under (deny default):
        //   - SIGKILL when the kernel sandbox terminates the process directly.
        //   - EXC_BREAKPOINT/SIGTRAP (or SIGABRT) when an essential allocation
        //     fails inside libSystem/libswiftCore because (allow syscall-mach)
        //     is missing for vm_allocate-class traps, and the Swift runtime
        //     traps with "Could not allocate memory".
        // Both surfaces are sandbox-driven; the precise signal is preserved in
        // runner_subprocess.term_signal for forensics.
        let message = transportError
            ?? waitError
            ?? "worker terminated by signal \(sig) before writing a report"
        return (1, "runner_sandbox_denied", message)
    }
    if let code = subprocess.exit_code, code != 0 {
        return (1, "runner_failed", transportError ?? waitError ?? "worker exited with status \(code)")
    }
    return (1, "runner_failed", transportError ?? waitError ?? "worker exited without a complete report")
}

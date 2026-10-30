import Foundation

// Reservation and submission transport. The output is a client-owned capture;
// exact host reply bytes remain separate from locally observed failures.
private func die(_ message: String, code: Int32) -> Never {
    fputs(message + "\n", stderr)
    exit(code)
}

private func usage() -> String {
    """
    usage:
      pw-runner-client run [--timeout-ms <n>] [--deadline-ticks <n>] [--mach-service] [--privileged] <xpc-service-name> <request.json>
      pw-runner-client run [--timeout-ms <n>] [--deadline-ticks <n>] [--mach-service] [--privileged] --request - <xpc-service-name>

    notes:
      - the first form reads the request from the named file; the second reads it from stdin to EOF.
      - the whole request is read before the connection is opened or any output is written.
      - prints one protocol-versioned transport capture, including exact host reply bytes.
      - acquisition may retry within the allowance; submission is never replayed.
      - --deadline-ticks is an absolute mach_continuous_time deadline from the caller.
      - use --mach-service for Mach services; add --privileged for system scope.
    """
}

private func emit(_ capture: PWRunnerClientCapture) -> Never {
    do {
        let bytes = try pwRunnerEncodeClientCapture(capture)
        FileHandle.standardOutput.write(bytes)
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(capture.terminal == "runner_reply" ? 0 : 1)
    } catch {
        // A missing capture leaves submission unknown to the caller.
        die("could not encode client transport capture: \(error)", code: 1)
    }
}

private func readFailure(_ error: Error, timeoutMs: UInt64, deadlineNs: UInt64?) -> Never {
    let now = PWContinuousClock.now()
    let start: UInt64? = now == UInt64.max ? nil : now
    let end = deadlineNs ?? start.map { PWContinuousClock.adding(milliseconds: timeoutMs, to: $0) }
    let deadline = end == UInt64.max ? nil : end
    let available = start != nil && deadline != nil
    var capture = PWRunnerClientCapture(clock_available: available, started_continuous_ns: start,
        deadline_continuous_ns: deadline, ended_continuous_ns: available ? start : nil, timeout_ms: timeoutMs)
    capture.error = PWRunnerTransportError(stage: "local", reason: available ? "input_read_failed" : "clock_error",
        message: available ? "could not read request" : "continuous clock unavailable", error: available ? error : nil)
    emit(capture)
}

private func run(args: [String]) -> Never {
    var timeoutMs = PWRunnerWire.defaultClientTimeoutMs
    var deadlineTicks: UInt64?
    var useMachService = false
    var privileged = false
    var requestFromStdin = false

    var idx = 0
    while idx < args.count {
        let arg = args[idx]
        if arg == "--" {
            idx += 1
            break
        }
        if !arg.hasPrefix("-") {
            break
        }
        switch arg {
        case "-h", "--help":
            die(usage(), code: 0)
        case "--timeout-ms":
            guard idx + 1 < args.count else { die("missing value for --timeout-ms", code: 2) }
            guard let v = Int(args[idx + 1]) else { die("invalid --timeout-ms", code: 2) }
            timeoutMs = max(1, v)
            idx += 2
        case "--deadline-ticks":
            guard idx + 1 < args.count, let value = UInt64(args[idx + 1]) else { die("invalid --deadline-ticks", code: 2) }
            guard deadlineTicks == nil else { die("duplicate --deadline-ticks", code: 2) }
            deadlineTicks = value
            idx += 2
        case "--mach-service":
            useMachService = true
            idx += 1
        case "--privileged":
            privileged = true
            idx += 1
        case "--request":
            // Only `-` is accepted here: the positional request argument remains
            // the literal file path form, and the two forms never mix.
            guard idx + 1 < args.count else { die("missing value for --request", code: 2) }
            guard args[idx + 1] == "-" else { die("invalid --request value (only - is accepted)\n\n\(usage())", code: 2) }
            guard !requestFromStdin else { die("duplicate --request -", code: 2) }
            requestFromStdin = true
            idx += 2
        default:
            die("unknown argument: \(arg)\n\n\(usage())", code: 2)
        }
    }

    guard idx < args.count else { die("missing <xpc-service-name>\n\n\(usage())", code: 2) }
    let serviceName = args[idx]
    idx += 1

    let requestBytes: Data
    if requestFromStdin {
        guard idx == args.count else { die("unexpected argument after <xpc-service-name> with --request -\n\n\(usage())", code: 2) }
        // Read the whole request to EOF before connecting or writing anything.
        do { requestBytes = try FileHandle.standardInput.readToEnd() ?? Data() }
        catch { readFailure(error, timeoutMs: UInt64(timeoutMs), deadlineNs: deadlineTicks.map(PWContinuousClock.nanoseconds)) }
    } else {
        guard idx < args.count else { die("missing <request.json>\n\n\(usage())", code: 2) }
        let requestPath = args[idx]
        idx += 1
        guard idx == args.count else { die("unexpected argument after <request.json>\n\n\(usage())", code: 2) }
        do {
            requestBytes = try Data(contentsOf: URL(fileURLWithPath: requestPath))
        } catch {
            readFailure(error, timeoutMs: UInt64(timeoutMs), deadlineNs: deadlineTicks.map(PWContinuousClock.nanoseconds))
        }
    }

    let queue = DispatchQueue(label: "PolicyWitness.runner-client-session")
    let finished = DispatchSemaphore(value: 0)
    var result: PWRunnerClientCapture?
    let session = PWRunnerClientSession(request: requestBytes, timeoutMs: UInt64(timeoutMs),
        deadlineNs: deadlineTicks.map(PWContinuousClock.nanoseconds),
        enqueue: { work in queue.async(execute: work) },
        schedule: { milliseconds, work in queue.asyncAfter(deadline: .now() + .milliseconds(milliseconds), execute: work) },
        connect: { failure in PWRunnerXPCConnection(service: serviceName, machService: useMachService,
            privileged: privileged, failure: failure) },
        finish: { capture in result = capture; finished.signal() })
    session.start()
    finished.wait()
    emit(result!)
}

let argv = Array(CommandLine.arguments.dropFirst())
if argv.isEmpty {
    die(usage(), code: 2)
}
if argv[0] == "run" {
    run(args: Array(argv.dropFirst()))
}
die("unknown command: \(argv[0])\n\n\(usage())", code: 2)

import Foundation

// Thin NSXPC wrapper. On XPC failure it emits a synthetic RunResult JSON; it
// never interprets sandbox behavior or probe outcomes.
private func die(_ message: String, code: Int32) -> Never {
    fputs(message + "\n", stderr)
    exit(code)
}

private func usage() -> String {
    """
    usage:
      pw-runner-client run [--timeout-ms <n>] [--mach-service] [--privileged] <xpc-service-name> <request.json>

    notes:
      - prints the raw RunResult JSON returned by the runner (JSON-over-Data).
      - on open/call failure, prints a synthetic RunResult with normalized_outcome set.
      - use --mach-service for Mach services; add --privileged for system scope.
    """
}

private struct XpcErrorDetails: Codable {
    var domain: String?
    var code: Int?
    var message: String
    var user_info: [String: String]?
}

private func nsErrorDetails(_ error: Error) -> XpcErrorDetails {
    let ns = error as NSError
    var ui: [String: String] = [:]
    for (k, v) in ns.userInfo {
        ui[String(describing: k)] = String(describing: v)
    }
    return XpcErrorDetails(domain: ns.domain, code: ns.code, message: String(describing: error), user_info: ui.isEmpty ? nil : ui)
}

private func run(args: [String]) -> Never {
    var timeoutMs = 240_000
    var useMachService = false
    var privileged = false

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
        case "--mach-service":
            useMachService = true
            idx += 1
        case "--privileged":
            privileged = true
            idx += 1
        default:
            die("unknown argument: \(arg)\n\n\(usage())", code: 2)
        }
    }

    guard idx < args.count else { die("missing <xpc-service-name>\n\n\(usage())", code: 2) }
    let serviceName = args[idx]
    idx += 1

    guard idx < args.count else { die("missing <request.json>\n\n\(usage())", code: 2) }
    let requestPath = args[idx]

    let requestBytes: Data
    do {
        requestBytes = try Data(contentsOf: URL(fileURLWithPath: requestPath))
    } catch {
        die("failed to read request.json: \(error)", code: 2)
    }

    let conn: NSXPCConnection
    if useMachService {
        let opts: NSXPCConnection.Options = privileged ? [.privileged] : []
        conn = NSXPCConnection(machServiceName: serviceName, options: opts)
    } else {
        conn = NSXPCConnection(serviceName: serviceName)
    }
    conn.remoteObjectInterface = NSXPCInterface(with: PWRunnerProtocol.self)
    conn.resume()

    let sema = DispatchSemaphore(value: 0)
    let lock = NSLock()
    var done = false
    var replyData: Data?
    var replyError: Error?

    guard let proxy = conn.remoteObjectProxyWithErrorHandler({ error in
        lock.lock()
        defer { lock.unlock() }
        if done { return }
        done = true
        replyError = error
        sema.signal()
    }) as? PWRunnerProtocol else {
        let resp = PWRunnerRunResult(
            specimen_id: "<unknown>",
            run_kind: nil,
            rc: 1,
            normalized_outcome: NormalizedOutcome.xpcProxyTypeMismatch,
            error: "remote proxy type mismatch",
            pid: Int(getpid()),
            bundle_id: nil,
            policy_format: "unknown",
            steps: []
        )
        let out = (try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8)
        FileHandle.standardOutput.write(out)
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(1)
    }

    proxy.runSpecimen(requestBytes) { data in
        lock.lock()
        defer { lock.unlock() }
        if done { return }
        done = true
        replyData = data
        sema.signal()
    }

    let deadline = DispatchTime.now() + .milliseconds(timeoutMs)
    if sema.wait(timeout: deadline) == .timedOut {
        let resp = PWRunnerRunResult(
            specimen_id: "<unknown>",
            run_kind: nil,
            rc: 1,
            normalized_outcome: NormalizedOutcome.xpcTimeout,
            error: "xpc call timeout after \(timeoutMs)ms",
            pid: Int(getpid()),
            bundle_id: nil,
            policy_format: "unknown",
            steps: []
        )
        let out = (try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8)
        FileHandle.standardOutput.write(out)
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(1)
    }

    lock.lock()
    let data = replyData
    let err = replyError
    lock.unlock()

    if let err {
        let details = nsErrorDetails(err)
        let resp = PWRunnerRunResult(
            specimen_id: "<unknown>",
            run_kind: nil,
            rc: 1,
            normalized_outcome: NormalizedOutcome.xpcError,
            error: "\(details.domain ?? "unknown"):\(details.code ?? -1) \(details.message)",
            pid: Int(getpid()),
            bundle_id: nil,
            policy_format: "unknown",
            steps: []
        )
        let out = (try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8)
        FileHandle.standardOutput.write(out)
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(1)
    }

    if let data {
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    }

    let resp = PWRunnerRunResult(
        specimen_id: "<unknown>",
        run_kind: nil,
        rc: 1,
        normalized_outcome: NormalizedOutcome.xpcNoReply,
        error: "xpc call failed (no reply and no error)",
        pid: Int(getpid()),
        bundle_id: nil,
        policy_format: "unknown",
        steps: []
    )
    let out = (try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8)
    FileHandle.standardOutput.write(out)
    FileHandle.standardOutput.write(Data("\n".utf8))
    exit(1)
}

let argv = Array(CommandLine.arguments.dropFirst())
if argv.isEmpty {
    die(usage(), code: 2)
}
if argv[0] == "run" {
    run(args: Array(argv.dropFirst()))
}
die("unknown command: \(argv[0])\n\n\(usage())", code: 2)

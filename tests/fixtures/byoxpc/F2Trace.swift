// Investigative fixture, compiled only with copied production host sources.
// Every request is traced; bundle configuration alone enables named gates.
// Trace writes and generation reads perturb timing. Reply invocation/return
// are host observations, not confirmation that the client received the reply.
import Foundation
import Darwin
import CryptoKit

@_silgen_name("pw_f2_process_identity")
private func f2ProcessIdentity(_ pid: Int32, _ seconds: UnsafeMutablePointer<UInt64>,
    _ microseconds: UnsafeMutablePointer<UInt64>, _ parent: UnsafeMutablePointer<Int32>,
    _ error: UnsafeMutablePointer<Int32>) -> Int32

struct F2Request {
    let invocation: String
    let specimen: String
    let requestHash: String
    let requestBytes: Int
    let clientPID: Int32?
}

enum F2Trace {
    private static let lock = NSLock()
    private static var sequence: UInt64 = 0
    private static var owner: F2Request?
    private static var retiring: F2Request?
    private static let configuration = Bundle.main.object(forInfoDictionaryKey: "PWF2Trace") as? [String: Any]
    private static let directory = configuration?["directory"] as? String
    private static let gates = configuration?["gates"] as? [String: [String]] ?? [:]

    static func identity(_ pid: Int32) -> [String: Any] {
        var seconds: UInt64 = 0, microseconds: UInt64 = 0
        var parent: Int32 = 0, error: Int32 = 0
        let rc = f2ProcessIdentity(pid, &seconds, &microseconds, &parent, &error)
        // A successful query always has a nonzero process start time. A short
        // zero-byte failure must not be confused with the helper's success rc.
        let observed = rc == 0 && seconds > 0
        var result: [String: Any] = ["pid": Int(pid), "observed": observed,
            "absent": !observed && error == ESRCH, "errno": Int(error), "query_rc": Int(rc)]
        if observed {
            result["start_sec"] = seconds
            result["start_usec"] = microseconds
            result["ppid"] = Int(parent)
        }
        return result
    }

    static func event(_ request: F2Request?, _ kind: String, _ fields: [String: Any] = [:]) {
        guard let directory else { return }
        lock.lock()
        defer { lock.unlock() }
        sequence += 1
        var value = fields
        value["event"] = kind
        value["sequence"] = sequence
        value["uptime_ns"] = DispatchTime.now().uptimeNanoseconds
        value["host"] = identity(getpid())
        if let request {
            value["invocation"] = request.invocation
            value["specimen_id"] = request.specimen
            value["request_sha256"] = request.requestHash
            value["request_bytes"] = request.requestBytes
            value["client_pid"] = request.clientPID.map(Int.init) as Any? ?? NSNull()
        }
        do {
            let bytes = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
            let name = "\(getpid())-\(String(format: "%012llu", sequence))-\(UUID().uuidString).json"
            try bytes.write(to: URL(fileURLWithPath: directory).appendingPathComponent(name), options: .atomic)
        } catch {
            // Missing trace evidence fails the experiment; it must never be
            // silently credited as absence of an event.
            fputs("F2 trace write failed: \(error)\n", stderr)
            _exit(92)
        }
    }

    static func receive(_ bytes: Data, clientPID: Int32?) -> F2Request {
        let object = (try? JSONSerialization.jsonObject(with: bytes)) as? [String: Any]
        let candidate = object?["specimen_id"] as? String ?? "<unreported>"
        let safe = candidate.utf8.count <= 128 && candidate.unicodeScalars.allSatisfy {
            CharacterSet(charactersIn: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_<>.").contains($0)
        }
        let request = F2Request(invocation: "\(getpid())-\(UUID().uuidString)",
            specimen: safe ? candidate : "<unreported>",
            requestHash: SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined(),
            requestBytes: bytes.count, clientPID: clientPID)
        event(request, "request_received")
        return request
    }

    static func admitted(_ request: F2Request) {
        lock.lock(); owner = request; lock.unlock()
        event(request, "admission_claimed")
    }

    static func workerSpawned(_ pid: Int32) {
        lock.lock(); let request = owner; lock.unlock()
        event(request, "worker_spawned", ["worker": identity(pid)])
    }

    static func orchestrationReturned(_ request: F2Request, _ result: PWRunnerRunResult) {
        var fields: [String: Any] = ["outcome": result.normalized_outcome, "rc": result.rc]
        if let child = result.runner_subprocess {
            fields["worker_pid"] = child.pid
            fields["worker_reaped"] = child.reaped as Any? ?? NSNull()
            fields["worker_exit_code"] = child.exit_code as Any? ?? NSNull()
            fields["worker_term_signal"] = child.term_signal as Any? ?? NSNull()
        }
        event(request, "orchestration_returned", fields)
    }

    static func encoded(_ request: F2Request, _ result: PWRunnerRunResult, _ bytes: Data) {
        // Only scalar reply metadata; no request policy, extension token, error
        // prose, or reply body is copied into the trace.
        let body = (try? JSONSerialization.jsonObject(with: bytes)) as? [String: Any]
        event(request, "reply_encoded", ["result_outcome": result.normalized_outcome,
            "encoded_outcome": body?["normalized_outcome"] as Any? ?? NSNull(),
            "reply_bytes": bytes.count,
            "reply_sha256": SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined()])
        gate(request, "reply")
    }

    private static func gate(_ request: F2Request, _ boundary: String) {
        guard request.specimen.hasPrefix("f2-control-"),
              gates[request.specimen]?.contains(boundary) == true, let directory else { return }
        let path = URL(fileURLWithPath: directory).appendingPathComponent("\(request.invocation).\(boundary).allow").path
        event(request, "gate_wait", ["boundary": boundary, "gate_path": path])
        let start = DispatchTime.now().uptimeNanoseconds
        while access(path, F_OK) != 0 {
            if DispatchTime.now().uptimeNanoseconds - start >= 20_000_000_000 {
                event(request, "gate_watchdog", ["boundary": boundary])
                _exit(93)
            }
            usleep(1000)
        }
        event(request, "gate_released", ["boundary": boundary])
    }

    static func willScheduleExit(_ request: F2Request) {
        lock.lock(); retiring = request; lock.unlock()
        event(request, "exit_scheduled", ["delay_ms": hostExitDelayMs])
    }

    static func beforeExit() {
        lock.lock(); let request = retiring; lock.unlock()
        event(request, "exit_timer_fired")
        if let request { gate(request, "exit") }
        event(request, "exit_invocation", ["status": 0])
    }
}

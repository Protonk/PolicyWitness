// Compiled only with copied production host sources by reservation_controls.
// Gates are outside admission locks and arm only after installation verification.
// Credentials, policy source and execution reply bodies are never traced.
import Foundation
import Darwin
import CryptoKit

enum ReservationTrace {
    private static let configuration = Bundle.main.object(forInfoDictionaryKey: "PWF2Trace") as? [String: Any]
    private static let directory = configuration?["directory"] as? String
    private static let gates = configuration?["gates"] as? [String: [String]] ?? [:]
    private static var armed: Bool {
        guard let directory else { return false }
        return access(directory + "/armed", F_OK) == 0
    }
    static func reservation(_ data: Data, clientPID: Int32?) -> F2Request {
        let value = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
        let attempt = value?["attempt_id"] as? String
        let context = F2Request(invocation: "\(getpid())-\(UUID().uuidString)", specimen: "<reservation>",
            requestHash: SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined(),
            requestBytes: data.count, clientPID: clientPID)
        F2Trace.event(context, "reservation_received", ["attempt_id": attempt as Any? ?? NSNull()])
        return context
    }
    static func control(_ context: F2Request, _ data: Data) {
        let value = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
        let status = value?["status"] as? String ?? "<unreadable>"
        F2Trace.event(context, "control_reply_encoded", ["status": status,
            "attempt_id": value?["attempt_id"] as Any? ?? NSNull(),
            "control_bytes": data.count,
            "control_sha256": SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()])
        gate(context, status)
        F2Trace.event(context, "control_reply_invocation", ["status": status])
    }
    static func legacyControl() -> Data? {
        guard armed, gates["reservation"]?.contains("legacy_control") == true else { return nil }
        F2Trace.event(nil, "legacy_protocol_control_substituted")
        // A protocol-1 control peer, not a synthetic execution result. The
        // installed marker remains current so this reaches the RPC boundary.
        return try! JSONSerialization.data(withJSONObject: ["protocol_version": 1, "legacy": true])
    }
    static func gate(_ request: F2Request, _ boundary: String) {
        guard armed, gates["reservation"]?.contains(boundary) == true, let directory else { return }
        // One claim across host generations prevents the recovering client
        // encountering the same intervention on its next fresh acquisition.
        let claim = directory + "/once-" + boundary
        let fd = open(claim, O_WRONLY | O_CREAT | O_EXCL, 0o600)
        guard fd >= 0 else { return }
        close(fd)
        let path = directory + "/" + request.invocation + "." + boundary + ".allow"
        F2Trace.event(request, "gate_wait", ["boundary": boundary, "gate_path": path])
        let start = DispatchTime.now().uptimeNanoseconds
        while access(path, F_OK) != 0 {
            if DispatchTime.now().uptimeNanoseconds - start >= 20_000_000_000 {
                F2Trace.event(request, "gate_watchdog", ["boundary": boundary]); _exit(93)
            }
            usleep(1000)
        }
        F2Trace.event(request, "gate_released", ["boundary": boundary])
    }
    static func beforeExit() {
        let context = F2Request(invocation: "\(getpid())-\(UUID().uuidString)", specimen: "<retirement>",
            requestHash: "", requestBytes: 0, clientPID: nil)
        F2Trace.event(context, "retirement_timer_fired")
        gate(context, "exit")
        F2Trace.event(context, "exit_invocation")
    }
}

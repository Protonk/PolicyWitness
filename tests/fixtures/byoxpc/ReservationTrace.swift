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
    private static func sha(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
    /// After one real execution, alter only the top-level response-schema
    /// marker of the encoded reply, once. The bytes are otherwise unchanged:
    /// the altered body parses to the original object once the marker is
    /// restored, or nothing is altered and the reason is traced.
    static func outgoingReply(_ request: F2Request, _ data: Data) -> Data {
        guard armed, gates["reservation"]?.contains("old_response") == true, let directory else { return data }
        let fd = open(directory + "/once-old_response", O_WRONLY | O_CREAT | O_EXCL, 0o600)
        guard fd >= 0 else { return data }
        close(fd)
        guard let original = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
              let marker = original["schema_version"] as? Int else {
            F2Trace.event(request, "outgoing_marker_unaltered", ["reason": "unreadable reply"]); return data
        }
        let needle = Data("\"schema_version\":\(marker)".utf8)
        let replacement = Data("\"schema_version\":\(marker - 1)".utf8)
        var search = data.startIndex..<data.endIndex
        while let range = data.range(of: needle, in: search) {
            var candidate = data
            candidate.replaceSubrange(range, with: replacement)
            if var parsed = (try? JSONSerialization.jsonObject(with: candidate)) as? [String: Any],
               parsed["schema_version"] as? Int == marker - 1 {
                parsed["schema_version"] = marker
                if NSDictionary(dictionary: parsed).isEqual(to: original) {
                    F2Trace.event(request, "outgoing_marker_altered", ["original_marker": marker,
                        "altered_marker": marker - 1, "original_bytes": data.count, "altered_bytes": candidate.count,
                        "original_sha256": sha(data), "altered_sha256": sha(candidate),
                        "byte_offset": range.lowerBound, "equal_after_restoring_marker": true])
                    return candidate
                }
            }
            search = range.upperBound..<data.endIndex
        }
        F2Trace.event(request, "outgoing_marker_unaltered", ["reason": "no top-level marker occurrence"])
        return data
    }
    static func beforeExit() {
        let context = F2Request(invocation: "\(getpid())-\(UUID().uuidString)", specimen: "<retirement>",
            requestHash: "", requestBytes: 0, clientPID: nil)
        F2Trace.event(context, "retirement_timer_fired")
        gate(context, "exit")
        F2Trace.event(context, "exit_invocation")
    }
}

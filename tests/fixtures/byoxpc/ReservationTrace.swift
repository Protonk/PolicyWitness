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
        F2Trace.event(nil, "foreign_contract_control_substituted")
        // A foreign build contract in a reservation reply. The installed
        // contract remains current so this reaches the live RPC boundary.
        return try! JSONSerialization.data(withJSONObject: ["contract": "test:foreign", "legacy": true])
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
    /// Change only the contract UTF-8 bytes in a real binary reply.
    /// This narrow wire-fault fixture does not decode or rebuild the reply.
    static func outgoingReply(_ request: F2Request, _ data: Data) -> Data {
        guard armed, gates["reservation"]?.contains("old_response") == true, let directory else { return data }
        let fd = open(directory + "/once-old_response", O_WRONLY | O_CREAT | O_EXCL, 0o600)
        guard fd >= 0 else { return data }
        close(fd)
        let bytes = [UInt8](data)
        func unsigned(_ offset: Int, _ width: Int) -> UInt64? {
            guard offset >= 0, width <= 8, offset <= bytes.count, width <= bytes.count - offset else { return nil }
            return (0..<width).reduce(UInt64(0)) { $0 | (UInt64(bytes[offset + $1]) << (8 * $1)) }
        }
        // PWP1, reply record, producer field, producer record, contract field.
        let offset = 59
        let marker = PWBuildContext.contract
        let length = marker.utf8.count
        guard length > 0, bytes.count >= offset + length,
              Array(bytes.prefix(4)) == [0x50, 0x57, 0x50, 0x31],
              Array(bytes[4..<36]) == PWPorcelainSchema.fingerprint,
              bytes[36] == 6, unsigned(37, 4) == UInt64(bytes.count - 41),
              unsigned(41, 2) == UInt64(PWRunnerRunResult.porcelainRecordID),
              unsigned(43, 2) == UInt64(PWRunnerRunResult.PorcelainTag.producer),
              bytes[45] == 6, unsigned(50, 2) == UInt64(PWProducer.porcelainRecordID),
              unsigned(52, 2) == UInt64(PWProducer.PorcelainTag.contract),
              bytes[54] == 4, unsigned(55, 4) == UInt64(length),
              Array(bytes[offset..<(offset + length)]) == Array(marker.utf8) else {
            F2Trace.event(request, "outgoing_marker_unaltered", ["reason": "unexpected producer contract field"]); return data
        }
        var candidate = data
        candidate[offset] = candidate[offset] == 120 ? 121 : 120
        let foreign = String(decoding: candidate[offset..<(offset + length)], as: UTF8.self)
        var restored = candidate
        restored.replaceSubrange(offset..<(offset + length), with: data[offset..<(offset + length)])
        guard restored == data, candidate != data else {
            F2Trace.event(request, "outgoing_marker_unaltered", ["reason": "byte restoration failed"]); return data
        }
        F2Trace.event(request, "outgoing_marker_altered", ["original_marker": marker,
            "altered_marker": foreign, "original_bytes": data.count, "altered_bytes": candidate.count,
            "original_sha256": sha(data), "altered_sha256": sha(candidate),
            "byte_offset": offset, "byte_length": length, "equal_after_restoring_marker": true])
        return candidate
    }
    static func beforeExit() {
        let context = F2Request(invocation: "\(getpid())-\(UUID().uuidString)", specimen: "<retirement>",
            requestHash: "", requestBytes: 0, clientPID: nil)
        F2Trace.event(context, "retirement_timer_fired")
        gate(context, "exit")
        F2Trace.event(context, "exit_invocation")
    }
}

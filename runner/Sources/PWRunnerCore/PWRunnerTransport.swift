import Foundation
import Darwin
import CryptoKit

/// Protocol controls have no specimen or worker fields. Their identity is
/// reported by the peer; it is not an independent process-generation receipt.
enum PWRunnerTransportLimits {
    static let reservationLeaseMs = 5_000
    static let reservationRPCMs = 5_000
    static let acquisitionAttempts = 256
    static let retryDelayMs = 100
    static let controlBytes = 64 * 1024
    static let errorMessageBytes = 1024
    static let errorDomainBytes = 128
    static let runnerReplyBytes = 64 * 1024 * 1024
}

enum PWContinuousClock {
    static func now() -> UInt64 {
        nanoseconds(ticks: mach_continuous_time())
    }
    static func nanoseconds(ticks: UInt64) -> UInt64 {
        var info = mach_timebase_info_data_t()
        guard mach_timebase_info(&info) == KERN_SUCCESS, info.denom != 0, info.numer != 0 else { return UInt64.max }
        let numerator = UInt64(info.numer), denominator = UInt64(info.denom)
        let whole = ticks / denominator
        let (base, overflow) = whole.multipliedReportingOverflow(by: numerator)
        if overflow { return UInt64.max }
        let fraction = (ticks % denominator) * numerator / denominator
        return base > UInt64.max - fraction ? UInt64.max : base + fraction
    }
    static func adding(milliseconds: UInt64, to start: UInt64) -> UInt64 {
        let (span, overflow) = milliseconds.multipliedReportingOverflow(by: 1_000_000)
        return overflow || start > UInt64.max - span ? UInt64.max : start + span
    }
    static func elapsedMs(from start: UInt64, to end: UInt64) -> UInt64 {
        end >= start ? (end - start) / 1_000_000 : 0
    }
}

struct PWRunnerReservationRequest: Codable {
    var protocol_version: Int = PWContract.runnerProtocol
    var attempt_id: String
    var lease_ms: Int
    enum CodingKeys: String, CodingKey, CaseIterable { case protocol_version, attempt_id, lease_ms }
    init(attempt_id: String, lease_ms: Int) { self.attempt_id = attempt_id; self.lease_ms = lease_ms }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        protocol_version = try c.decode(Int.self, forKey: .protocol_version)
        attempt_id = try c.decode(String.self, forKey: .attempt_id)
        lease_ms = try c.decode(Int.self, forKey: .lease_ms)
    }
}

struct PWRunnerControlReply: Codable {
    var protocol_version: Int = PWContract.runnerProtocol
    var status: String
    var attempt_id: String?
    var host_pid: Int
    var host_instance: String
    var reservation_id: String?
    var lease_ms: Int?
    var reason: String?
    enum CodingKeys: String, CodingKey, CaseIterable {
        case protocol_version, status, attempt_id, host_pid, host_instance, reservation_id, lease_ms, reason
    }
    init(status: String, attempt_id: String? = nil, host_pid: Int = Int(getpid()), host_instance: String,
         reservation_id: String? = nil, lease_ms: Int? = nil, reason: String? = nil) {
        self.status = status; self.attempt_id = attempt_id; self.host_pid = host_pid
        self.host_instance = host_instance; self.reservation_id = reservation_id
        self.lease_ms = lease_ms; self.reason = reason
    }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        protocol_version = try c.decode(Int.self, forKey: .protocol_version)
        status = try c.decode(String.self, forKey: .status)
        attempt_id = try c.decodeIfPresent(String.self, forKey: .attempt_id)
        host_pid = try c.decode(Int.self, forKey: .host_pid)
        host_instance = try c.decode(String.self, forKey: .host_instance)
        reservation_id = try c.decodeIfPresent(String.self, forKey: .reservation_id)
        lease_ms = try c.decodeIfPresent(Int.self, forKey: .lease_ms)
        reason = try c.decodeIfPresent(String.self, forKey: .reason)
    }
}

func pwTransportBoundedString(_ text: String, bytes: Int) -> (String, Bool) {
    guard text.utf8.count > bytes else { return (text, false) }
    var value = Array(text.utf8.prefix(bytes))
    while String(bytes: value, encoding: .utf8) == nil { value.removeLast() }
    return (String(bytes: value, encoding: .utf8)!, true)
}

struct PWRunnerTransportError: Codable {
    var stage: String
    var reason: String
    var domain: String?
    var code: Int?
    var message: String
    var domain_truncated: Bool
    var message_truncated: Bool
    init(stage: String, reason: String, message: String, error: Error? = nil) {
        self.stage = stage; self.reason = reason
        let ns = error.map { $0 as NSError }
        let domain = ns.map { pwTransportBoundedString($0.domain, bytes: PWRunnerTransportLimits.errorDomainBytes) }
        self.domain = domain?.0; self.domain_truncated = domain?.1 ?? false; self.code = ns?.code
        // XPC's localized summary omits the service/route diagnostic. Retain
        // this one native diagnostic string, never the arbitrary userInfo map.
        let diagnostic = ns?.userInfo[NSDebugDescriptionErrorKey] as? String
        let bounded = pwTransportBoundedString(diagnostic ?? ns?.localizedDescription ?? message,
            bytes: PWRunnerTransportLimits.errorMessageBytes)
        self.message = bounded.0; self.message_truncated = bounded.1
    }
}

struct PWRunnerControlObservation: Codable {
    var bytes_received: Int
    var sha256: String
    var status: String?
    var host_pid: Int?
    var host_instance: String?
    var lease_ms: Int?
    var reason: String?
    init(_ data: Data, admitted: PWRunnerControlReply? = nil) {
        bytes_received = data.count
        sha256 = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        status = admitted?.status; host_pid = admitted?.host_pid; host_instance = admitted?.host_instance
        lease_ms = admitted?.lease_ms; reason = admitted?.reason
    }
}

struct PWRunnerAcquisitionAttempt: Codable {
    var ordinal: Int
    var attempt_id: String
    var started_elapsed_ms: UInt64?
    var ended_elapsed_ms: UInt64?
    var outcome: String
    var control: PWRunnerControlObservation?
    var error: PWRunnerTransportError?
}

struct PWRunnerSubmission: Codable {
    var state: String = "not_invoked"
    var invoked_elapsed_ms: UInt64?
}

struct PWRunnerReplyCapture: Codable {
    var bytes_received: Int
    var bytes_retained: Int
    var truncated: Bool
    var data_base64: String
    init(_ data: Data) {
        bytes_received = data.count
        let held = data.prefix(PWRunnerTransportLimits.runnerReplyBytes)
        bytes_retained = held.count; truncated = held.count != data.count
        data_base64 = held.base64EncodedString()
    }
}

/// Optional fields are omitted when absent; absence never implies an event.
struct PWRunnerClientCapture: Codable {
    var kind: String = "runner_client_capture"
    var protocol_version: Int = PWContract.runnerProtocol
    var client_pid: Int = Int(getpid())
    var clock: String = "mach_continuous_time_ns"
    var clock_available: Bool = true
    var started_continuous_ns: UInt64?
    var deadline_continuous_ns: UInt64?
    var ended_continuous_ns: UInt64?
    var timeout_ms: UInt64
    var attempts: [PWRunnerAcquisitionAttempt] = []
    var acquisition_stop: String = "local_error"
    var submission = PWRunnerSubmission()
    var terminal: String = "local_error"
    var error: PWRunnerTransportError?
    var runner_reply: PWRunnerReplyCapture?
    var submission_refusal: PWRunnerControlObservation?
}

/// Base64 can contain a slash in every position. Escaping those slashes would
/// double the retained-byte expansion; this encoder owns only the new capture,
/// leaving the host RunResult encoder and its exact bytes unchanged.
func pwRunnerEncodeClientCapture(_ capture: PWRunnerClientCapture) throws -> Data {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
    return try encoder.encode(capture)
}

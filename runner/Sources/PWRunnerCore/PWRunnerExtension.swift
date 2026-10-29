import Foundation
import Darwin

// Wire-side bounds also compile into the client, without the worker driver.
enum PWExtensionLimits {
    static let declarations = 1
    static let consumes = 1
    static let releases = 1
    static let referenceBytes = 63
    static let targetBytes = 1023
    static let tokenBytes = 16384
    static let freshReadBytes = 64
}

struct PWRunnerExtensionDeclaration: Codable {
    var token_ref: String
    var target: String
    var authority: String?
    var effectiveAuthority: String { authority ?? "read" }
    var nativeClass: String { effectiveAuthority == "read_write" ? "com.apple.app-sandbox.read-write" : "com.apple.app-sandbox.read" }
    init(token_ref: String, target: String, authority: String? = nil) {
        self.token_ref = token_ref; self.target = target; self.authority = authority
    }
    enum CodingKeys: String, CodingKey, CaseIterable { case token_ref, target, authority }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        token_ref = try c.decode(String.self, forKey: .token_ref)
        target = try c.decode(String.self, forKey: .target)
        authority = try c.decodeIfPresent(String.self, forKey: .authority)
    }
}
struct PWRunnerExtensionOperation: Codable {
    var operation: String
    var token_ref: String?
    var handle_ref: String
    enum CodingKeys: String, CodingKey, CaseIterable { case operation, token_ref, handle_ref }
    init(operation: String, token_ref: String? = nil, handle_ref: String) {
        self.operation = operation; self.token_ref = token_ref; self.handle_ref = handle_ref
    }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        operation = try c.decode(String.self, forKey: .operation)
        token_ref = try c.decodeIfPresent(String.self, forKey: .token_ref)
        handle_ref = try c.decode(String.self, forKey: .handle_ref)
    }
}
struct PWRunnerExtensionAction: Codable {
    var step_id: String
    var intervention: PWRunnerExtensionOperation
    enum CodingKeys: String, CodingKey, CaseIterable { case step_id; case intervention = "extension" }
    init(step_id: String, intervention: PWRunnerExtensionOperation) { self.step_id = step_id; self.intervention = intervention }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        step_id = try c.decode(String.self, forKey: .step_id)
        intervention = try c.decode(PWRunnerExtensionOperation.self, forKey: .intervention)
    }
}

/// The native handle is signed 64-bit; -1 does not provide a handle.
/// Missing publication withholds every native result, regardless of progress.
struct PWRunnerExtensionEvent: Codable {
    var phase_id: String
    var step_id: String
    var operation: String
    var token_ref: String?
    var handle_ref: String
    var call_boundary_observed: Bool
    var result_published: Bool
    var status: String
    var native_result: Int64?
    var errno: Int32?
    var unavailable_reason: String?
    var lifecycle: PWAttemptLifecycle?
}
struct PWRunnerIssuer: Codable {
    var executable_path: String
    var pid: Int32?
    var uid: UInt32?
    var euid: UInt32?
    var gid: UInt32?
    var egid: UInt32?
    var call_boundary_observed = false
    var result_published = false
    var native_nonnull: Bool?
    var errno: Int32?
    var token_length: UInt32?
    var reaped: Bool?
    var exit_code: Int32?
    var term_signal: Int32?
    var wait_errors: [PWRunnerWaitError] = []
    var termination_request: PWRunnerTerminationRequest?
    var spawn_failure: PWRunnerSpawnFailure?
}
struct PWRunnerExtensionRecord: Codable {
    var token_ref: String
    var extension_class = "com.apple.app-sandbox.read"
    var submitted_target: String
    var resolved_target: String?
    var preparation_status = "not_started"
    var preparation_errno: Int32?
    var identity: PWFileIdentity?
    var issuance_status = "not_started"
    var issuer: PWRunnerIssuer?
    var delivery_status = "not_observed"
    var delivered_bytes: UInt32?
    /// Present exactly when the worker published `channel_rejected` or
    /// `local_setup_failed`.
    var delivery_failure: PWRunnerExtensionDeliveryFailure?
    /// Cleanup after unavailable native APIs is independent of channel setup.
    /// Absence means no cleanup failure was reported, not proof of cleanup.
    var delivery_cleanup_failure: PWRunnerExtensionDeliveryCleanupFailure?
    var host_buffer_erased = false
}

struct PWRunnerExtensionDeliveryCleanupFailure: Codable, Equatable {
    var stage: String
    var errno: Int32

    func problem(status: String) -> String? {
        guard status == "native_api_unavailable", stage == "descriptor_close", errno >= 0 else {
            return "invalid independent delivery cleanup failure"
        }
        return nil
    }
}

/// The worker's delivery publication vocabulary. Codes and stage numbers are
/// the PW_DELIVERY_* enums in pw_probe_runner.c; an unrecognized value becomes
/// the record status `invalid`.
enum PWExtensionDelivery {
    static let statuses: [UInt32: String] = [1: "delivered", 2: "token_unavailable", 3: "channel_rejected",
                                             4: "native_api_unavailable", 5: "local_setup_failed"]
    static let stages: [UInt32: String] = [1: "core_limit", 2: "descriptor_metadata", 3: "channel_size", 4: "mapping",
                                           5: "descriptor_close", 6: "channel_header", 7: "channel_token", 8: "unmap"]
    /// Stages whose failure is a native call result.
    static let localStages: Set<String> = ["core_limit", "descriptor_metadata", "mapping", "descriptor_close"]
    /// Stages that judged the channel itself; `channel_size` keeps the successful fstat return.
    static let channelStages: Set<String> = ["channel_size", "channel_header", "channel_token"]
    static let cleanupStages: Set<String> = ["descriptor_close", "unmap"]
    static let failureStatuses: Set<String> = ["channel_rejected", "local_setup_failed"]
    static let recordStatuses: Set<String> = ["not_observed", "delivered", "token_unavailable", "channel_rejected",
                                              "native_api_unavailable", "local_setup_failed"]
}

/// The worker's account of a failed channel preparation: the first failing
/// stage, that call's native return and the errno saved immediately after it
/// when the stage made a native call, and a cleanup failure observed while
/// undoing earlier setup. A format rejection carries no native result.
struct PWRunnerExtensionDeliveryFailure: Codable, Equatable {
    var stage: String
    var native_rc: Int32?
    var errno: Int32?
    var cleanup_stage: String?
    var cleanup_errno: Int32?

    /// Structural rules every reader applies: the stage class agrees with the
    /// status, native fields are present exactly for native stages, and
    /// cleanup fields are paired.
    func problem(status: String) -> String? {
        let local = PWExtensionDelivery.localStages.contains(stage)
        guard local || PWExtensionDelivery.channelStages.contains(stage) else { return "unknown delivery failure stage" }
        if (status == "local_setup_failed") != local { return "delivery failure stage disagrees with status" }
        if local {
            guard let rc = native_rc, rc != 0, let value = errno, value >= 0 else { return "local setup failure lacks its native result" }
        } else if stage == "channel_size" {
            guard native_rc == 0, errno == nil else { return "undersized channel misreports its inspection result" }
        } else if native_rc != nil || errno != nil { return "channel rejection invents a native result" }
        if let cleanup = cleanup_stage {
            guard PWExtensionDelivery.cleanupStages.contains(cleanup), let value = cleanup_errno, value >= 0 else { return "delivery cleanup failure lacks its errno" }
            if cleanup == "descriptor_close" && stage == "descriptor_close" { return "descriptor closed twice" }
        } else if cleanup_errno != nil { return "delivery cleanup errno without a stage" }
        return nil
    }
}

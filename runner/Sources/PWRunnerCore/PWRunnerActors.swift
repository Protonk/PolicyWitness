import Foundation
import Darwin

// The actor form of the request and the actor-indexed reply records. Shared
// contract sources: these compile in the host and the client. Normalization,
// scheduling and evidence assembly live beside the orchestrator.

/// Actor-form capacities and qualified budgets. Distinct from the legacy
/// single-worker settings even where the numbers agree.
enum PWActorLimits {
    static let actors = 8
    static let phases = 16
    static let issues = 32
    static let deliveries = 64
    static let handles = 64
    static let releases = 64
    /// Shared with ordinary actions: PWShmLayout.maxSteps.
    static let actions = 256
    static let identifierBytes = 63
    static let targetBytes = 1023
    static let setupMs = 10_000
    static let executionMs = 120_000
    static let collectionMs = 30_000
    static let releaseWaitMs = 60_000
    static let exchangeMs = 5_000
    static let lifetimeMs = 180_000
    static let requiredEntitlements = 64
    static let entitlementKeyBytes = 255
    static let terminationMs = 5_000
}

struct PWRunnerActorSandbox: Codable {
    static let modeApply = "apply"
    static let modeUnapplied = "unapplied"
    var mode: String
    var policy: PWRunnerPolicySpec?
    init(mode: String, policy: PWRunnerPolicySpec? = nil) { self.mode = mode; self.policy = policy }
    enum CodingKeys: String, CodingKey, CaseIterable { case mode, policy }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        mode = try c.decode(String.self, forKey: .mode)
        policy = try c.decodeIfPresent(PWRunnerPolicySpec.self, forKey: .policy)
    }
}

struct PWRunnerActor: Codable {
    var actor_id: String
    var sandbox: PWRunnerActorSandbox
    var equipment: String?
    var required_entitlements: [String]
    init(actor_id: String, sandbox: PWRunnerActorSandbox, equipment: String? = nil, required_entitlements: [String] = []) {
        self.actor_id = actor_id; self.sandbox = sandbox; self.equipment = equipment
        self.required_entitlements = required_entitlements
    }
    enum CodingKeys: String, CodingKey, CaseIterable { case actor_id, sandbox, equipment, required_entitlements }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        actor_id = try c.decode(String.self, forKey: .actor_id)
        sandbox = try c.decode(PWRunnerActorSandbox.self, forKey: .sandbox)
        equipment = c.contains(.equipment) ? try c.decode(String.self, forKey: .equipment) : nil
        required_entitlements = c.contains(.required_entitlements) ? try c.decode([String].self, forKey: .required_entitlements) : []
    }
    var applies: Bool { sandbox.mode == PWRunnerActorSandbox.modeApply }
}

struct PWRunnerAfterTermination: Codable {
    let actor_id: String
    enum CodingKeys: String, CodingKey, CaseIterable { case actor_id }
    init(actor_id: String) { self.actor_id = actor_id }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        actor_id = try c.decode(String.self, forKey: .actor_id)
    }
}

struct PWRunnerPreparationFailure: Codable {
    var stage: String
    var code: String
    var actor_id: String?
    var binding_ref: String?
    var reason: String?
}

// MARK: - Authority exchange vocabulary (shared with the reply's readers)

/// Slot acknowledgement values and rejection reasons (pw_authority_region.h).
enum PWAuthorityAck {
    static let none: UInt32 = 0, accepted: UInt32 = 1, rejected: UInt32 = 2
    static let rejectNames: [UInt32: String] = [1: "magic", 2: "family", 3: "owner", 4: "ordinal", 5: "length",
                                                 6: "terminator", 7: "interior_nul", 8: "resource"]
}

/// The host's transfer acknowledgements (pw_authority_region.h).
enum PWTransferAck {
    static let none: UInt32 = 0, delivered: UInt32 = 1, custodyUnavailable: UInt32 = 2, recipientRejected: UInt32 = 3
    static let recipientTimeout: UInt32 = 4, recipientUnavailable: UInt32 = 5, requestInvalid: UInt32 = 6
    static let hostTimeout: UInt32 = 7, clockFault: UInt32 = 8, copyMismatch: UInt32 = 9
    static let names: [UInt32: String] = [0: "none", 1: "delivered", 2: "custody_unavailable", 3: "recipient_rejected",
                                          4: "recipient_timeout", 5: "recipient_unavailable", 6: "request_invalid",
                                          7: "host_timeout", 8: "clock_fault", 9: "copy_mismatch"]
}

// MARK: - Reply records (emitted from the integrated actor contract)

/// Launch context the host arranged for one actor process.
struct PWRunnerActorLaunch: Codable, Equatable {
    var pid: Int
    var parent_pid: Int
    var environment: String = "empty"
    var standard_streams: String = "stdin_policy_pipe_stdout_stderr_null_device"
    var inherited_descriptors: [Int] = [0, 3, 4]
}

/// One actor's process, policy and application account. The subprocess record
/// is the same record a single-worker reply carries, with its disposition.
struct PWRunnerActorResult: Codable {
    var actor_id: String
    var index: Int
    var mode: String
    var policy_format: String?
    /// Host hash of the submitted (controller-resolved) source bytes.
    var policy_sha256: String?
    /// The worker's own hash of the bytes it read before compiling, when published.
    var policy_received_sha256: String?
    var setup_status: String
    var applied: Bool?
    var application_count: Int
    var launch: PWRunnerActorLaunch?
    var subprocess: PWRunnerSubprocess?
    var compiled_profile: CompiledProfileCapture?
    var visits: [Int]
    var equipment: PWRunnerActorEquipment? = nil
    var application: PWRunnerActorApplication? = nil
    var owned_reap: PWOwnedReapObservation? = nil
}

/// Token, delivery and handle tables, keyed by the request's references.
struct PWRunnerTokenRecord: Codable {
    var token_ref: String
    var actor_id: String
    var step_id: String
    var family: String
    var status: String
    var token_length: Int?
    var last_use_step_id: String?
}
struct PWRunnerDeliveryRecord: Codable {
    var delivery_ref: String
    var token_ref: String
    var source_actor_id: String
    var recipient_actor_id: String
    var step_id: String
    var status: String
    var delivered_length: Int?
    var equality: String?
    var last_use_step_id: String?
}
struct PWRunnerHandleRecord: Codable {
    var handle_ref: String
    var delivery_ref: String
    var actor_id: String
    var step_id: String
    var status: String
    var native_handle: Int64?
    var raw_equal_handles: [String]
    var release_step_id: String?
    var release_attempted: Bool
}
struct PWRunnerResourceTables: Codable {
    var tokens: [PWRunnerTokenRecord]
    var deliveries: [PWRunnerDeliveryRecord]
    var handles: [PWRunnerHandleRecord]
}

/// Host-measured intervals of one actor-form visit, in milliseconds on the
/// host's monotonic clock. Each is absent when its boundary was not reached.
/// Collection time is excluded from the schedule allowance; the others are
/// charged to it. These are scheduling and publication intervals, not native
/// call latencies.
struct PWRunnerVisitTiming: Codable, Equatable {
    var activation_to_arrival_ms: UInt64?
    var collection_ms: UInt64?
    var arrival_to_release_ms: UInt64?
    var release_to_completion_ms: UInt64?
}

/// The actor form's schedule account: the measured setup and execution waits
/// with their allowances, the shared lifetime budget, and whether the schedule
/// was cancelled.
struct PWRunnerScheduleRecord: Codable {
    var setup_wait: PWHostWait?
    var execution_wait: PWHostWait?
    var lifetime_budget_ms: Int
    var collection_budget_ms: Int
    var cancelled: String?
}

/// One explicit transfer: an apparatus action with host and actor provenance,
/// never a native sandbox call. No native return or errno is attached.
struct PWRunnerTransferRecord: Codable {
    var phase_id: String
    var step_id: String
    var source_actor_id: String
    var recipient_actor_id: String
    var token_ref: String
    var delivery_ref: String
    var request_published: Bool
    var custody_status: String
    var copy_status: String
    var equality: String
    var recipient_acknowledged: Bool
    var source_acknowledged: Bool
    var status: String
    var lifecycle: PWAttemptLifecycle?
    /// The host's wait for the recipient's acknowledgement, when a copy was made.
    var recipient_wait: PWHostWait?
}

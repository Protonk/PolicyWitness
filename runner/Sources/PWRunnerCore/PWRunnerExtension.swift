import Foundation
import Darwin

// Wire-side bounds also compile into the client, without the worker driver.
enum PWExtensionLimits {
    static let referenceBytes = 63
    static let tokenBytes = 16384
    static let freshReadBytes = 64
}

/// Closed actor authority operation. Presence is retained separately so an
/// extraneous operand with a null value is still rejected by admission.
struct PWRunnerExtensionOperation: Codable {
    static let actorOperations = ["issue", "transfer", "consume", "release"]
    var operation: String
    var token_ref: String?
    var handle_ref: String?
    var family: String?
    var target: String?
    var authority: String?
    var recipient: String?
    var delivery_ref: String?
    private var presentOperands: Set<CodingKeys> = []
    func contains(_ key: CodingKeys) -> Bool { presentOperands.contains(key) || operand(key) != nil }
    enum CodingKeys: String, CodingKey, CaseIterable {
        case operation, token_ref, handle_ref, family, target, authority, recipient, delivery_ref
    }
    init(operation: String, token_ref: String? = nil, handle_ref: String? = nil, family: String? = nil,
         target: String? = nil, authority: String? = nil, recipient: String? = nil, delivery_ref: String? = nil) {
        self.operation = operation; self.token_ref = token_ref; self.handle_ref = handle_ref
        self.family = family; self.target = target; self.authority = authority
        self.recipient = recipient; self.delivery_ref = delivery_ref
    }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        operation = try c.decode(String.self, forKey: .operation)
        presentOperands = Set(CodingKeys.allCases.filter { $0 != .operation && c.contains($0) })
        token_ref = try c.decodeIfPresent(String.self, forKey: .token_ref)
        handle_ref = try c.decodeIfPresent(String.self, forKey: .handle_ref)
        family = try c.decodeIfPresent(String.self, forKey: .family)
        target = try c.decodeIfPresent(String.self, forKey: .target)
        authority = try c.decodeIfPresent(String.self, forKey: .authority)
        recipient = try c.decodeIfPresent(String.self, forKey: .recipient)
        delivery_ref = try c.decodeIfPresent(String.self, forKey: .delivery_ref)
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(operation, forKey: .operation)
        if presentOperands.contains(.token_ref) { try c.encode(token_ref, forKey: .token_ref) }
        else { try c.encodeIfPresent(token_ref, forKey: .token_ref) }
        if presentOperands.contains(.handle_ref) { try c.encode(handle_ref, forKey: .handle_ref) }
        else { try c.encodeIfPresent(handle_ref, forKey: .handle_ref) }
        if presentOperands.contains(.family) { try c.encode(family, forKey: .family) }
        else { try c.encodeIfPresent(family, forKey: .family) }
        if presentOperands.contains(.target) { try c.encode(target, forKey: .target) }
        else { try c.encodeIfPresent(target, forKey: .target) }
        if presentOperands.contains(.authority) { try c.encode(authority, forKey: .authority) }
        else { try c.encodeIfPresent(authority, forKey: .authority) }
        if presentOperands.contains(.recipient) { try c.encode(recipient, forKey: .recipient) }
        else { try c.encodeIfPresent(recipient, forKey: .recipient) }
        if presentOperands.contains(.delivery_ref) { try c.encode(delivery_ref, forKey: .delivery_ref) }
        else { try c.encodeIfPresent(delivery_ref, forKey: .delivery_ref) }
    }
    /// Required operands of the closed actor operation.
    static let actorOperands: [String: [CodingKeys]] = [
        "issue": [.family, .target, .authority, .token_ref],
        "transfer": [.token_ref, .recipient, .delivery_ref],
        "consume": [.delivery_ref, .handle_ref],
        "release": [.handle_ref],
    ]
    func operand(_ key: CodingKeys) -> String? {
        switch key {
        case .operation: return operation
        case .token_ref: return token_ref
        case .handle_ref: return handle_ref
        case .family: return family
        case .target: return target
        case .authority: return authority
        case .recipient: return recipient
        case .delivery_ref: return delivery_ref
        }
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
    /// Present for consume/release; absent on issue and transfer.
    var handle_ref: String?
    var call_boundary_observed: Bool
    var result_published: Bool
    var status: String
    var native_result: Int64?
    var errno: Int32?
    var unavailable_reason: String?
    var lifecycle: PWAttemptLifecycle?
    // Actor form: the acting actor, the family operands and references.
    var actor_id: String?
    var family: String?
    var target: String?
    var extension_class: String?
    var flags: Int?
    var delivery_ref: String?
    var native_nonnull: Bool?
    var token_length: Int?
}

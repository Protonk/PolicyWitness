import Foundation
import CoreFoundation

enum PWEquipmentLimits {
    static let inventoryBytes = 1_048_576
    static let entitlementBytes = 65_536
    static let staticBindings = 4
    static let liveInspections = 8
    static let entitlementRecords = 12
    static let requirementCount = 64
    static let requirementKeyBytes = 255
    static let diagnosticBytes = 1024
    static let metadataBytes = 32_768
}

// Equipment observations are shared wire types. The host implementation lives
// in ActorEquipment.swift; clients need no Security APIs or worker driver.
struct PWRunnerEquipmentError: Codable, Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentError
    var operation: String
    var domain: String?
    var code: Int?
    var message: String?
    // END GENERATED PORCELAIN PWRunnerEquipmentError
}

struct PWRunnerEquipmentInventory: Codable, Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentInventory
    var path: String
    var status: String = "unobserved"
    var sha256: String?
    var schema_version: Int?
    var worker_identity: String?
    var unsigned_worker_sha256: String?
    var seal_osstatus: Int?
    var reason: String?
    var error: PWRunnerEquipmentError?
    // END GENERATED PORCELAIN PWRunnerEquipmentInventory
}

struct PWRunnerEquipmentBinding: Codable, Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentBinding
    var binding_id: String
    var role: String
    var source: String
    var implementation_identity: String
    var relative_path: String?
    var path: String
    var status: String = "refused"
    var reason: String?
    var expected_sha256: String?
    var expected_cdhash: String?
    var sha256: String?
    var cdhash: String?
    var identifier: String?
    var team_id: String?
    var entitlements_ref: String?
    var signature_osstatus: Int?
    var entitlements_match: Bool?
    var error: PWRunnerEquipmentError?
    // END GENERATED PORCELAIN PWRunnerEquipmentBinding

    enum CodingKeys: String, CodingKey, CaseIterable {
        case binding_id, role, source, implementation_identity, relative_path, path, status, reason
        case expected_sha256, expected_cdhash, sha256, cdhash, identifier, team_id
        case entitlements_ref, signature_osstatus, entitlements_match, error
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(binding_id, forKey: .binding_id); try c.encode(role, forKey: .role)
        try c.encode(source, forKey: .source); try c.encode(implementation_identity, forKey: .implementation_identity)
        try c.encodeIfPresent(relative_path, forKey: .relative_path); try c.encode(path, forKey: .path)
        try c.encode(status, forKey: .status); try c.encodeIfPresent(reason, forKey: .reason)
        try c.encodeIfPresent(expected_sha256, forKey: .expected_sha256); try c.encodeIfPresent(expected_cdhash, forKey: .expected_cdhash)
        try c.encodeIfPresent(sha256, forKey: .sha256); try c.encodeIfPresent(cdhash, forKey: .cdhash)
        try c.encodeIfPresent(identifier, forKey: .identifier)
        if identifier != nil { try c.encode(team_id, forKey: .team_id) }
        try c.encodeIfPresent(entitlements_ref, forKey: .entitlements_ref)
        try c.encodeIfPresent(signature_osstatus, forKey: .signature_osstatus)
        try c.encodeIfPresent(entitlements_match, forKey: .entitlements_match); try c.encodeIfPresent(error, forKey: .error)
    }
}

struct PWRunnerEquipmentEntitlements: Codable, Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentEntitlements
    var entitlements_id: String
    var source: String
    var binding_ref: String
    var actor_id: String?
    var status: String
    var raw_plist: String?
    var error: PWRunnerEquipmentError?
    // END GENERATED PORCELAIN PWRunnerEquipmentEntitlements
}

struct PWRunnerEquipmentNativeObservation: Codable, Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentNativeObservation
    var operation: String
    var attempted: Bool
    var osstatus: Int?
    // END GENERATED PORCELAIN PWRunnerEquipmentNativeObservation
}

struct PWRunnerEquipmentExecution: Codable, Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentExecution
    var status: String = "unobserved"
    var pid: Int?
    var parent_pid: Int?
    var observed_at_monotonic_ns: UInt64?
    var path: String?
    var cdhash: String?
    var identifier: String?
    var team_id: String?
    var entitlements_ref: String?
    var native_observations: [PWRunnerEquipmentNativeObservation] = []
    var reason: String? = "not_launched"
    var eligible: Bool = false
    // END GENERATED PORCELAIN PWRunnerEquipmentExecution

    enum CodingKeys: String, CodingKey, CaseIterable {
        case status, pid, parent_pid, observed_at_monotonic_ns, path, cdhash, identifier, team_id
        case entitlements_ref, native_observations, reason, eligible
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(status, forKey: .status); try c.encodeIfPresent(pid, forKey: .pid)
        try c.encodeIfPresent(parent_pid, forKey: .parent_pid)
        try c.encodeIfPresent(observed_at_monotonic_ns, forKey: .observed_at_monotonic_ns)
        try c.encodeIfPresent(path, forKey: .path); try c.encodeIfPresent(cdhash, forKey: .cdhash)
        try c.encodeIfPresent(identifier, forKey: .identifier)
        if identifier != nil { try c.encode(team_id, forKey: .team_id) }
        try c.encodeIfPresent(entitlements_ref, forKey: .entitlements_ref)
        try c.encode(native_observations, forKey: .native_observations)
        try c.encodeIfPresent(reason, forKey: .reason); try c.encode(eligible, forKey: .eligible)
    }
}

struct PWRunnerActorEquipment: Codable, Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerActorEquipment
    var requested: String?
    var resolved: String
    var binding_ref: String
    var required_entitlements: [String]
    var requirements_status: String = "unobserved"
    var missing_requirements: [String]?
    var execution: PWRunnerEquipmentExecution = PWRunnerEquipmentExecution()
    // END GENERATED PORCELAIN PWRunnerActorEquipment

    enum CodingKeys: String, CodingKey, CaseIterable {
        case requested, resolved, binding_ref, required_entitlements, requirements_status, missing_requirements, execution
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(requested, forKey: .requested); try c.encode(resolved, forKey: .resolved)
        try c.encode(binding_ref, forKey: .binding_ref); try c.encode(required_entitlements, forKey: .required_entitlements)
        try c.encode(requirements_status, forKey: .requirements_status)
        try c.encodeIfPresent(missing_requirements, forKey: .missing_requirements); try c.encode(execution, forKey: .execution)
    }
}

/// Pure reply checks, independent of the host's inspection/selection code.
/// Caller supplies actor associations from the surrounding reply. No filesystem,
/// code-signing query or registry lookup can repair malformed evidence here.
func pwRunnerEquipmentProblems(inventory: PWRunnerEquipmentInventory?,
                              bindings: [PWRunnerEquipmentBinding],
                              entitlements: [PWRunnerEquipmentEntitlements],
                              actors: [PWRunnerActorEquipment], actorIDs: [String],
                              actorPIDs: [Int?]) -> [String] {
    var problems: [String] = []
    func require(_ value: Bool, _ message: String) { if !value { problems.append(message) } }
    func hex(_ value: String?, _ count: Int) -> Bool {
        guard let value else { return false }
        return value.utf8.count == count && value.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) }
    }
    func checkError(_ error: PWRunnerEquipmentError?) {
        guard let error else { return }
        let operations: Set<String> = ["service_seal", "inventory_read", "inventory_decode", "worker_path", "worker_hash",
            "worker_signature", "worker_entitlements", "guest_code", "dynamic_validity", "associated_static_code", "signing_information"]
        require(operations.contains(error.operation), "equipment error operation")
        require(error.domain.map { $0.utf8.count <= 128 } ?? true, "equipment error domain bound")
        require(error.message.map { $0.utf8.count <= 1024 } ?? true, "equipment error message bound")
        require((error.domain == nil) == (error.code == nil), "equipment error domain/code association")
    }
    let bindingReasons: Set<String> = ["missing", "not_regular", "not_executable", "outside_bundle", "signature_invalid",
        "signature_unreadable", "entitlements_unreadable", "worker_identity_mismatch", "inspection_failed"]
    let executionReasons: Set<String> = ["not_launched", "setup_unavailable", "process_unavailable", "ownership_unresolved",
        "code_lookup_failed", "dynamic_validation_failed", "signing_readback_failed", "executable_mismatch",
        "signature_identity_mismatch", "entitlement_mismatch", "requirements_unsatisfied", "inspection_deadline"]
    let roles: Set<String> = ["selected", "unentitled"]
    let bindingIDs: Set<String> = ["selected", "unentitled", "override-selected", "override-unentitled"]
    require(actors.count <= PWEquipmentLimits.liveInspections && actors.count == actorIDs.count && actors.count == actorPIDs.count, "equipment actor associations")
    require(bindings.count <= PWEquipmentLimits.staticBindings && entitlements.count <= PWEquipmentLimits.entitlementRecords, "equipment table capacity")
    require(Set(bindings.map { $0.binding_id }).count == bindings.count, "equipment duplicate binding")
    require(Set(entitlements.map { $0.entitlements_id }).count == entitlements.count, "equipment duplicate read-back")
    var dictionaries: [String: [String: Any]] = [:]
    for row in entitlements {
        checkError(row.error)
        require(bindingIDs.contains(row.binding_ref), "equipment read-back binding")
        require(row.source == "binding" || row.source == "execution", "equipment read-back source")
        require(row.status == "observed" || row.status == "failed", "equipment read-back status")
        if row.source == "binding" {
            require(row.entitlements_id == "binding-" + row.binding_ref && row.actor_id == nil, "equipment static read-back identity")
        } else {
            require(row.actor_id.map { actorIDs.contains($0) } == true, "equipment live read-back actor")
        }
        if row.status == "observed" {
            if let raw = row.raw_plist, raw.utf8.count <= PWEquipmentLimits.entitlementBytes,
               let dictionary = try? PropertyListSerialization.propertyList(from: Data(raw.utf8), options: [], format: nil) as? [String: Any] {
                dictionaries[row.entitlements_id] = dictionary
            } else { problems.append("equipment invalid entitlement observation") }
            require(row.error == nil, "equipment observed read-back error")
        } else {
            require(row.raw_plist == nil && row.error != nil, "equipment failed read-back contents")
        }
    }
    if let inventory {
        checkError(inventory.error)
        require(inventory.path.hasPrefix("/") && inventory.path.utf8.count <= 1023 && !inventory.path.contains("\0"), "equipment inventory path")
        require(["verified", "refused", "unobserved"].contains(inventory.status), "equipment inventory status")
        if inventory.status == "verified" {
            require(inventory.seal_osstatus == 0 && inventory.schema_version == 1 && hex(inventory.sha256, 64)
                    && hex(inventory.worker_identity, 64) && hex(inventory.unsigned_worker_sha256, 64), "equipment verified inventory facts")
            require(inventory.reason == nil && inventory.error == nil, "equipment verified inventory refusal")
            require(Set(bindings.filter { $0.source == "packaged" }.map { $0.binding_id }) == roles, "equipment complete packaged pair")
        }
    } else { problems.append("equipment inventory absent") }
    for row in bindings {
        checkError(row.error)
        require((try? pwRunnerEncodeJSON(row).count).map { $0 <= PWEquipmentLimits.metadataBytes } == true, "equipment binding metadata bound")
        require(bindingIDs.contains(row.binding_id) && roles.contains(row.role), "equipment binding identity")
        require(["bound", "refused"].contains(row.status), "equipment binding status")
        require(row.path.hasPrefix("/") && row.path.utf8.count <= 1023 && !row.path.contains("\0"), "equipment binding path")
        require(row.sha256.map { hex($0, 64) } ?? true, "equipment observed hash")
        require(row.cdhash.map { hex($0, 40) } ?? true, "equipment observed CDHash")
        require(row.identifier.map { !$0.isEmpty && $0.utf8.count <= 255 && !$0.contains("\0") } ?? true, "equipment signature identifier bound")
        require(row.team_id.map { !$0.isEmpty && $0.utf8.count <= 255 && !$0.contains("\0") } ?? true, "equipment signature team bound")
        if row.source == "packaged" {
            let expected = "Contents/MacOS/" + (row.role == "selected" ? "pw-probe-runner" : "pw-probe-runner-unentitled")
            require(row.binding_id == row.role && row.relative_path == expected
                    && row.implementation_identity == "inventory_verified", "equipment packaged binding association")
        } else if row.source == "test_override" {
            require(row.binding_id == "override-" + row.role && row.relative_path == nil
                    && row.expected_sha256 == nil && row.expected_cdhash == nil
                    && row.implementation_identity == "unverified_fixture", "equipment override binding association")
        } else { problems.append("equipment binding source") }
        if row.status == "bound" {
            require(row.reason == nil && row.error == nil && row.signature_osstatus == 0
                    && hex(row.sha256, 64) && hex(row.cdhash, 40) && row.identifier?.isEmpty == false,
                    "equipment bound observations")
            require(row.entitlements_ref == "binding-" + row.binding_id && dictionaries[row.entitlements_ref ?? ""] != nil,
                    "equipment bound read-back")
            if row.source == "packaged" {
                require(inventory?.status == "verified" && row.expected_sha256 == row.sha256
                        && row.expected_cdhash == row.cdhash && row.entitlements_match == true,
                        "equipment packaged identity match")
                if row.role == "unentitled" { require(dictionaries[row.entitlements_ref ?? ""]?.isEmpty == true, "equipment unentitled signature") }
            }
        } else { require(row.reason.map { bindingReasons.contains($0) } == true, "equipment refusal reason") }
    }
    for (index, actor) in actors.enumerated() {
        require(roles.contains(actor.resolved) && (actor.requested == nil || actor.requested == actor.resolved), "equipment actor selector")
        require(actor.required_entitlements.count <= 64 && Set(actor.required_entitlements).count == actor.required_entitlements.count
                && actor.required_entitlements.allSatisfy { !$0.isEmpty && !$0.contains("\0") && $0.utf8.count <= 255 }, "equipment requirements bounds")
        let binding = bindings.first { $0.binding_id == actor.binding_ref }
        if let binding { require(binding.role == actor.resolved, "equipment actor role association") }
        func missing(_ dictionary: [String: Any]) -> [String] {
            actor.required_entitlements.filter { key in
                guard let value = dictionary[key] as? NSNumber else { return true }
                return CFGetTypeID(value) != CFBooleanGetTypeID() || !value.boolValue
            }
        }
        if actor.requirements_status == "unobserved" {
            require(actor.missing_requirements == nil, "equipment unobserved requirements")
        } else if let dictionary = dictionaries[binding?.entitlements_ref ?? ""] {
            let absent = missing(dictionary)
            require(actor.requirements_status == (absent.isEmpty ? "satisfied" : "unsatisfied")
                    && actor.missing_requirements == absent, "equipment requirement decision")
        } else { problems.append("equipment requirements without read-back") }
        let execution = actor.execution
        require((try? pwRunnerEncodeJSON(execution).count).map { $0 <= PWEquipmentLimits.metadataBytes } == true, "equipment execution metadata bound")
        require(execution.path.map { $0.hasPrefix("/") && $0.utf8.count <= 1023 && !$0.contains("\0") } ?? true, "equipment execution path")
        require(execution.cdhash.map { hex($0, 40) } ?? true, "equipment execution CDHash")
        require(execution.identifier.map { !$0.isEmpty && $0.utf8.count <= 255 && !$0.contains("\0") } ?? true, "equipment execution identifier bound")
        require(execution.team_id.map { !$0.isEmpty && $0.utf8.count <= 255 && !$0.contains("\0") } ?? true, "equipment execution team bound")
        require(["matched", "mismatched", "inspection_failed", "unobserved"].contains(execution.status), "equipment execution status")
        require(execution.native_observations.count <= 4, "equipment live observation capacity")
        let operations = ["guest_code", "dynamic_validity", "associated_static_code", "signing_information"]
        for (offset, observation) in execution.native_observations.enumerated() {
            require(offset < operations.count && observation.operation == operations[min(offset, 3)]
                    && observation.attempted && observation.osstatus != nil, "equipment native observation order/result")
        }
        if let pid = execution.pid, index < actorPIDs.count {
            require(pid > 0 && actorPIDs[index] == pid, "equipment execution PID association")
        }
        if execution.status == "matched" {
            require(execution.eligible && execution.reason == nil && execution.observed_at_monotonic_ns != nil
                    && execution.pid != nil && execution.native_observations.count == 4
                    && execution.native_observations.allSatisfy { $0.osstatus == 0 }, "equipment matched live observations")
            require(binding?.status == "bound" && execution.path == binding?.path && execution.cdhash == binding?.cdhash
                    && execution.identifier == binding?.identifier && execution.team_id == binding?.team_id,
                    "equipment matched signed identity")
            let live = entitlements.first { $0.entitlements_id == execution.entitlements_ref }
            require(live?.source == "execution" && live?.binding_ref == actor.binding_ref
                    && index < actorIDs.count && live?.actor_id == actorIDs[index]
                    && live?.entitlements_id == "execution-\(index)", "equipment live read-back association")
            if let actual = dictionaries[execution.entitlements_ref ?? ""], let expected = dictionaries[binding?.entitlements_ref ?? ""] {
                require(NSDictionary(dictionary: actual).isEqual(to: expected) && missing(actual).isEmpty, "equipment live entitlement identity")
            } else { problems.append("equipment matched without entitlement observation") }
        } else {
            require(!execution.eligible && execution.reason.map { executionReasons.contains($0) } == true, "equipment ineligible execution")
        }
    }
    return problems
}

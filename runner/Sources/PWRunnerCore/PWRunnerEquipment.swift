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
struct PWRunnerEquipmentError: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentError
    var operation: String
    var domain: String?
    var code: Int?
    var message: String?
    // END GENERATED PORCELAIN PWRunnerEquipmentError
}

struct PWRunnerEquipmentInventory: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentInventory
    var path: String
    var status: String = "unobserved"
    var sha256: Data?
    var schema_version: Int?
    var worker_identity: Data?
    var unsigned_worker_sha256: Data?
    var seal_osstatus: Int?
    var reason: String?
    var error: PWRunnerEquipmentError?
    // END GENERATED PORCELAIN PWRunnerEquipmentInventory
}

struct PWRunnerEquipmentBinding: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentBinding
    var role: String
    var source: String
    var implementation_identity: String
    var relative_path: String?
    var path: String
    var status: String = "refused"
    var reason: String?
    var expected_sha256: Data?
    var expected_cdhash: Data?
    var sha256: Data?
    var cdhash: Data?
    var identifier: String?
    var team_id: String?
    var entitlements_ref: UInt32?
    var signature_osstatus: Int?
    var entitlements_match: Bool?
    var error: PWRunnerEquipmentError?
    // END GENERATED PORCELAIN PWRunnerEquipmentBinding

}

struct PWRunnerEquipmentEntitlements: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentEntitlements
    var source: String
    var binding_ref: UInt32
    var actor_id: String?
    var status: String
    var raw_plist: String?
    var error: PWRunnerEquipmentError?
    // END GENERATED PORCELAIN PWRunnerEquipmentEntitlements
}

struct PWRunnerEquipmentNativeObservation: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentNativeObservation
    var operation: String
    var attempted: Bool
    var osstatus: Int?
    // END GENERATED PORCELAIN PWRunnerEquipmentNativeObservation
}

struct PWRunnerEquipmentExecution: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerEquipmentExecution
    var status: String = "unobserved"
    var pid: Int?
    var parent_pid: Int?
    var observed_at_monotonic_ns: UInt64?
    var path: String?
    var cdhash: Data?
    var identifier: String?
    var team_id: String?
    var entitlements_ref: UInt32?
    var native_observations: [PWRunnerEquipmentNativeObservation] = []
    var reason: String? = "not_launched"
    var eligible: Bool = false
    // END GENERATED PORCELAIN PWRunnerEquipmentExecution

}

struct PWRunnerActorEquipment: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerActorEquipment
    var requested: String?
    var resolved: String
    var binding_ref: UInt32?
    var required_entitlements: [String]
    var requirements_status: String = "unobserved"
    var missing_requirements: [String]?
    var execution: PWRunnerEquipmentExecution = PWRunnerEquipmentExecution()
    // END GENERATED PORCELAIN PWRunnerActorEquipment

}

// Bound retained text directly, independent of a later JSON spelling or escaping
// policy. Numeric, Boolean, digest and table-index fields have fixed width;
// table and observation counts are admitted separately below. Subtracting avoids an aggregate-size overflow.
private func equipmentMetadataFits(_ fields: [String?]) -> Bool {
    var remaining = PWEquipmentLimits.metadataBytes
    for field in fields {
        guard let field else { continue }
        let count = field.utf8.count
        guard count <= remaining else { return false }
        remaining -= count
    }
    return true
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
    // Digests are bytes of a fixed length; rows are named by table index.
    func digest(_ value: Data?, _ count: Int) -> Bool { value?.count == count }
    func bindingRow(_ reference: UInt32?) -> PWRunnerEquipmentBinding? {
        reference.flatMap { Int($0) < bindings.count ? bindings[Int($0)] : nil }
    }
    func readback(_ reference: UInt32?) -> PWRunnerEquipmentEntitlements? {
        reference.flatMap { Int($0) < entitlements.count ? entitlements[Int($0)] : nil }
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
    require(actors.count <= PWEquipmentLimits.liveInspections && actors.count == actorIDs.count && actors.count == actorPIDs.count, "equipment actor associations")
    require(bindings.count <= PWEquipmentLimits.staticBindings && entitlements.count <= PWEquipmentLimits.entitlementRecords, "equipment table capacity")
    require(bindings.indices.allSatisfy { index in
        !bindings[..<index].contains { $0.role == bindings[index].role && $0.source == bindings[index].source }
    }, "equipment duplicate binding")
    require(entitlements.indices.allSatisfy { index in
        let row = entitlements[index]
        return !entitlements[..<index].contains {
            $0.source == row.source && (row.source == "binding" ? $0.binding_ref == row.binding_ref : $0.actor_id == row.actor_id)
        }
    }, "equipment duplicate read-back")
    var dictionaries: [Int: [String: Any]] = [:]
    for (position, row) in entitlements.enumerated() {
        checkError(row.error)
        require(bindingRow(row.binding_ref) != nil, "equipment read-back binding")
        require(row.source == "binding" || row.source == "execution", "equipment read-back source")
        require(row.status == "observed" || row.status == "failed", "equipment read-back status")
        if row.source == "binding" {
            require(bindingRow(row.binding_ref)?.entitlements_ref.map { Int($0) } == position && row.actor_id == nil,
                    "equipment static read-back identity")
        } else {
            require(row.actor_id.map { actorIDs.contains($0) } == true, "equipment live read-back actor")
        }
        if row.status == "observed" {
            if let raw = row.raw_plist, raw.utf8.count <= PWEquipmentLimits.entitlementBytes,
               let dictionary = try? PropertyListSerialization.propertyList(from: Data(raw.utf8), options: [], format: nil) as? [String: Any] {
                dictionaries[position] = dictionary
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
            require(inventory.seal_osstatus == 0 && inventory.schema_version == 1 && digest(inventory.sha256, 32)
                    && digest(inventory.worker_identity, 32) && digest(inventory.unsigned_worker_sha256, 32), "equipment verified inventory facts")
            require(inventory.reason == nil && inventory.error == nil, "equipment verified inventory refusal")
            require(Set(bindings.filter { $0.source == "packaged" }.map { $0.role }) == roles, "equipment complete packaged pair")
        }
    } else { problems.append("equipment inventory absent") }
    for (position, row) in bindings.enumerated() {
        checkError(row.error)
        require(equipmentMetadataFits([row.role, row.source, row.implementation_identity,
            row.relative_path, row.path, row.status, row.reason, row.identifier, row.team_id,
            row.error?.operation, row.error?.domain, row.error?.message]), "equipment binding metadata bound")
        require(roles.contains(row.role), "equipment binding identity")
        require(row.expected_sha256.map { digest($0, 32) } ?? true && row.expected_cdhash.map { digest($0, 20) } ?? true,
                "equipment expected identity")
        require(["bound", "refused"].contains(row.status), "equipment binding status")
        require(row.path.hasPrefix("/") && row.path.utf8.count <= 1023 && !row.path.contains("\0"), "equipment binding path")
        require(row.sha256.map { digest($0, 32) } ?? true, "equipment observed hash")
        require(row.cdhash.map { digest($0, 20) } ?? true, "equipment observed CDHash")
        require(row.identifier.map { !$0.isEmpty && $0.utf8.count <= 255 && !$0.contains("\0") } ?? true, "equipment signature identifier bound")
        require(row.team_id.map { !$0.isEmpty && $0.utf8.count <= 255 && !$0.contains("\0") } ?? true, "equipment signature team bound")
        if row.source == "packaged" {
            let expected = "Contents/MacOS/" + (row.role == "selected" ? "pw-probe-runner" : "pw-probe-runner-unentitled")
            require(row.relative_path == expected
                    && row.implementation_identity == "inventory_verified", "equipment packaged binding association")
        } else if row.source == "test_override" {
            require(row.relative_path == nil
                    && row.expected_sha256 == nil && row.expected_cdhash == nil
                    && row.implementation_identity == "unverified_fixture", "equipment override binding association")
        } else { problems.append("equipment binding source") }
        if row.status == "bound" {
            require(row.reason == nil && row.error == nil && row.signature_osstatus == 0
                    && digest(row.sha256, 32) && digest(row.cdhash, 20) && row.identifier?.isEmpty == false,
                    "equipment bound observations")
            let own = readback(row.entitlements_ref)
            require(own?.source == "binding" && own.map { Int($0.binding_ref) } == position
                    && row.entitlements_ref.flatMap { dictionaries[Int($0)] } != nil, "equipment bound read-back")
            if row.source == "packaged" {
                require(inventory?.status == "verified" && row.expected_sha256 == row.sha256
                        && row.expected_cdhash == row.cdhash && row.entitlements_match == true,
                        "equipment packaged identity match")
                if row.role == "unentitled" {
                    require(row.entitlements_ref.flatMap { dictionaries[Int($0)] }?.isEmpty == true, "equipment unentitled signature")
                }
            }
        } else { require(row.reason.map { bindingReasons.contains($0) } == true, "equipment refusal reason") }
    }
    for (index, actor) in actors.enumerated() {
        require(roles.contains(actor.resolved) && (actor.requested == nil || actor.requested == actor.resolved), "equipment actor selector")
        require(actor.required_entitlements.count <= 64 && Set(actor.required_entitlements).count == actor.required_entitlements.count
                && actor.required_entitlements.allSatisfy { !$0.isEmpty && !$0.contains("\0") && $0.utf8.count <= 255 }, "equipment requirements bounds")
        let binding = bindingRow(actor.binding_ref)
        require(actor.binding_ref == nil || binding?.role == actor.resolved, "equipment actor role association")
        func missing(_ dictionary: [String: Any]) -> [String] {
            actor.required_entitlements.filter { key in
                guard let value = dictionary[key] as? NSNumber else { return true }
                return CFGetTypeID(value) != CFBooleanGetTypeID() || !value.boolValue
            }
        }
        if actor.requirements_status == "unobserved" {
            require(actor.missing_requirements == nil, "equipment unobserved requirements")
        } else if let dictionary = binding?.entitlements_ref.flatMap({ dictionaries[Int($0)] }) {
            let absent = missing(dictionary)
            require(actor.requirements_status == (absent.isEmpty ? "satisfied" : "unsatisfied")
                    && actor.missing_requirements == absent, "equipment requirement decision")
        } else { problems.append("equipment requirements without read-back") }
        let execution = actor.execution
        require(equipmentMetadataFits([execution.status, execution.path, execution.identifier,
            execution.team_id, execution.reason]
            + execution.native_observations.map { Optional($0.operation) }), "equipment execution metadata bound")
        require(execution.path.map { $0.hasPrefix("/") && $0.utf8.count <= 1023 && !$0.contains("\0") } ?? true, "equipment execution path")
        require(execution.cdhash.map { digest($0, 20) } ?? true, "equipment execution CDHash")
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
            let live = readback(execution.entitlements_ref)
            require(live?.source == "execution" && live?.binding_ref == actor.binding_ref
                    && index < actorIDs.count && live?.actor_id == actorIDs[index], "equipment live read-back association")
            if let actual = execution.entitlements_ref.flatMap({ dictionaries[Int($0)] }),
               let expected = binding?.entitlements_ref.flatMap({ dictionaries[Int($0)] }) {
                require(NSDictionary(dictionary: actual).isEqual(to: expected) && missing(actual).isEmpty, "equipment live entitlement identity")
            } else { problems.append("equipment matched without entitlement observation") }
        } else {
            require(!execution.eligible && execution.reason.map { executionReasons.contains($0) } == true, "equipment ineligible execution")
        }
    }
    return problems
}

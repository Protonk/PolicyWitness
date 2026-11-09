import Foundation
import Darwin
import Security
import CryptoKit
import CoreFoundation

typealias ActorEquipmentLimits = PWEquipmentLimits

struct ActorEquipmentRequest {
    var actorID: String
    var index: Int
    var requested: String?
    var requiredEntitlements: [String]
}

struct ActorEquipmentBindingFailure {
    var stage = "equipment"
    var code = "equipment_binding_refused"
    var actor_id: String?
    /// Index of the refused row in the binding table, when one was produced.
    var binding_ref: UInt32?
    var reason: String
}

struct ActorSignedCode {
    var path: String
    var cdhash: Data
    var identifier: String
    var teamID: String?
    var entitlements: [String: Any]
    var entitlementsXML: String
}

struct ActorCodeInspection {
    var code: ActorSignedCode?
    var verificationStatus: Int?
    var reason: String?
    var error: PWRunnerEquipmentError?
    var observations: [PWRunnerEquipmentNativeObservation] = []
}

struct ActorEquipmentCalls {
    var inspectStatic: (URL) -> ActorCodeInspection = ActorEquipmentSystem.inspectStatic
    var inspectLive: (Int32) -> ActorCodeInspection = ActorEquipmentSystem.inspectLive
    var clock: () -> UInt64? = MonotonicDeadline.now
}

/// Internal native-call boundaries for branch controls. Production uses these
/// exact Security calls; no request or test override selects their results.
struct ActorEquipmentSecurityCalls {
    var guestCode: (Int32) -> (OSStatus, SecCode?) = { pid in
        var code: SecCode?
        let rc = SecCodeCopyGuestWithAttributes(nil,
            [kSecGuestAttributePid as String: NSNumber(value: pid)] as CFDictionary, SecCSFlags(), &code)
        return (rc, code)
    }
    var dynamicValidity: (SecCode) -> OSStatus = { code in
        SecCodeCheckValidity(code, SecCSFlags(), nil)
    }
    var associatedStaticCode: (SecCode) -> (OSStatus, SecStaticCode?) = { code in
        var associated: SecStaticCode?
        let rc = SecCodeCopyStaticCode(code, SecCSFlags(), &associated)
        return (rc, associated)
    }
    var signingInformation: (SecStaticCode) -> (OSStatus, CFDictionary?) = { code in
        var information: CFDictionary?
        let rc = SecCodeCopySigningInformation(code, SecCSFlags(rawValue: kSecCSSigningInformation), &information)
        return (rc, information)
    }
}

// The service-local manifest is sealed after both workers have been signed.
// It supplies expected signed hashes, not authority inferred from a filename.
struct ActorEquipmentManifest: Decodable {
    var schema_version: Int
    var runner_protocol: Int
    // The inventory file spells digests as lowercase hexadecimal; they are held
    // and reported as bytes.
    var worker_identity: Data
    var unsigned_worker_sha256: Data
    var workers: [Worker]
    struct Worker: Decodable {
        var role: String
        var relative_path: String
        var sha256: Data
        var cdhash: Data
        var identifier: String
        var team_id: String?
        var entitlements_xml: String
        enum CodingKeys: String, CodingKey, CaseIterable {
            case role, relative_path, sha256, cdhash, identifier, team_id, entitlements_xml
        }
        init(from decoder: Decoder) throws {
            try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
            let c = try decoder.container(keyedBy: CodingKeys.self)
            role = try c.decode(String.self, forKey: .role)
            relative_path = try c.decode(String.self, forKey: .relative_path)
            guard let hash = ActorEquipmentSystem.digest(try c.decode(String.self, forKey: .sha256), bytes: 32),
                  let code = ActorEquipmentSystem.digest(try c.decode(String.self, forKey: .cdhash), bytes: 20) else {
                throw ActorEquipmentProblem("invalid equipment inventory row")
            }
            sha256 = hash; cdhash = code
            identifier = try c.decode(String.self, forKey: .identifier)
            guard c.contains(.team_id) else { throw ActorEquipmentProblem("missing team_id") }
            team_id = try c.decodeIfPresent(String.self, forKey: .team_id)
            entitlements_xml = try c.decode(String.self, forKey: .entitlements_xml)
        }
    }
    enum CodingKeys: String, CodingKey, CaseIterable {
        case schema_version, runner_protocol, worker_identity, unsigned_worker_sha256, workers
    }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        schema_version = try c.decode(Int.self, forKey: .schema_version)
        runner_protocol = try c.decode(Int.self, forKey: .runner_protocol)
        guard let identity = ActorEquipmentSystem.digest(try c.decode(String.self, forKey: .worker_identity), bytes: 32),
              let unsigned = ActorEquipmentSystem.digest(try c.decode(String.self, forKey: .unsigned_worker_sha256), bytes: 32) else {
            throw ActorEquipmentProblem("incompatible equipment inventory")
        }
        worker_identity = identity; unsigned_worker_sha256 = unsigned
        workers = try c.decode([Worker].self, forKey: .workers)
    }
    static func decode(_ data: Data, expectedIdentity: Data) throws -> ActorEquipmentManifest {
        guard data.count <= ActorEquipmentLimits.inventoryBytes else { throw ActorEquipmentProblem("inventory limit") }
        let value = try pwRunnerDecodeJSON(Self.self, from: data)
        guard value.schema_version == 1, value.runner_protocol == PWContract.runnerProtocol,
              value.worker_identity == expectedIdentity,
              value.workers.count == 2, Set(value.workers.map { $0.role }) == Set(ActorEquipmentPreparation.roles) else {
            throw ActorEquipmentProblem("incompatible equipment inventory")
        }
        for row in value.workers {
            guard row.relative_path == ActorEquipmentPreparation.relativePath(row.role),
                  !row.identifier.isEmpty, row.identifier.utf8.count <= 255,
                  row.team_id.map({ !$0.isEmpty && $0.utf8.count <= 255 }) ?? true else {
                throw ActorEquipmentProblem("invalid equipment inventory row")
            }
            let entitlements = try ActorEquipmentSystem.parseEntitlements(row.entitlements_xml)
            if row.role == "unentitled" && !entitlements.isEmpty { throw ActorEquipmentProblem("unentitled worker has entitlements") }
        }
        return value
    }
}

private struct ActorEquipmentProblem: Error, CustomStringConvertible {
    var description: String
    init(_ value: String) { description = value }
}

enum ActorEquipmentSystem {
    /// The bytes of a lowercase hexadecimal digest of exactly `bytes` bytes.
    static func digest(_ text: String, bytes: Int) -> Data? {
        let digits = Array(text.utf8)
        guard digits.count == bytes * 2 else { return nil }
        func nibble(_ c: UInt8) -> UInt8? {
            (48...57).contains(c) ? c - 48 : (97...102).contains(c) ? c - 87 : nil
        }
        var out = Data(capacity: bytes)
        for index in stride(from: 0, to: digits.count, by: 2) {
            guard let high = nibble(digits[index]), let low = nibble(digits[index + 1]) else { return nil }
            out.append(high << 4 | low)
        }
        return out
    }
    static func bounded(_ value: String, limit: Int = ActorEquipmentLimits.diagnosticBytes) -> String {
        var result = "", count = 0
        for character in value {
            let width = String(character).utf8.count
            if count + width > limit { break }; result.append(character); count += width
        }
        return result
    }
    static func error(_ operation: String, _ error: Error) -> PWRunnerEquipmentError {
        if error is ActorEquipmentProblem || error is DecodingError || operation == "inventory_decode" {
            return PWRunnerEquipmentError(operation: operation, message: bounded(String(describing: error)))
        }
        let value = error as NSError
        return PWRunnerEquipmentError(operation: operation, domain: bounded(value.domain, limit: 128),
                                      code: value.code, message: bounded(value.localizedDescription))
    }
    static func nativeError(_ operation: String, _ status: OSStatus) -> PWRunnerEquipmentError {
        PWRunnerEquipmentError(operation: operation, domain: NSOSStatusErrorDomain, code: Int(status), message: nil)
    }
    static func parseEntitlements(_ text: String) throws -> [String: Any] {
        guard text.utf8.count <= ActorEquipmentLimits.entitlementBytes,
              let data = text.data(using: .utf8),
              let dictionary = try PropertyListSerialization.propertyList(from: data, options: [], format: nil) as? [String: Any] else {
            throw ActorEquipmentProblem("invalid or overlong entitlement plist")
        }
        return dictionary
    }
    static func xml(_ value: [String: Any]) throws -> String {
        let data = try PropertyListSerialization.data(fromPropertyList: value, format: .xml, options: 0)
        guard data.count <= ActorEquipmentLimits.entitlementBytes, let text = String(data: data, encoding: .utf8) else {
            throw ActorEquipmentProblem("observation_limit")
        }
        return text
    }
    static func granted(_ value: Any?) -> Bool {
        guard let number = value as? NSNumber else { return false }
        return CFGetTypeID(number) == CFBooleanGetTypeID() && number.boolValue
    }
    static func hash(_ url: URL) throws -> Data {
        let file = try FileHandle(forReadingFrom: url); defer { try? file.close() }
        var digest = SHA256()
        while let bytes = try file.read(upToCount: 1_048_576), !bytes.isEmpty { digest.update(data: bytes) }
        return Data(digest.finalize())
    }
    static func readInventory(_ url: URL) throws -> Data {
        let file = try FileHandle(forReadingFrom: url); defer { try? file.close() }
        let bytes = try file.read(upToCount: ActorEquipmentLimits.inventoryBytes + 1) ?? Data()
        guard bytes.count <= ActorEquipmentLimits.inventoryBytes else { throw ActorEquipmentProblem("inventory limit") }
        return bytes
    }
    private static func signingInfo(_ code: SecStaticCode,
                                    calls: ActorEquipmentSecurityCalls = ActorEquipmentSecurityCalls()) -> ActorCodeInspection {
        let (rc, information) = calls.signingInformation(code)
        guard rc == errSecSuccess else {
            return ActorCodeInspection(reason: "signing_readback_failed", error: nativeError("signing_information", rc))
        }
        guard let info = information as? [String: Any],
              let path = info[kSecCodeInfoMainExecutable as String] as? URL,
              let cdhash = info[kSecCodeInfoUnique as String] as? Data,
              let identifier = info[kSecCodeInfoIdentifier as String] as? String else {
            return ActorCodeInspection(reason: "signing_readback_failed",
                error: PWRunnerEquipmentError(operation: "signing_information", message: "required signature metadata absent"))
        }
        let team = info[kSecCodeInfoTeamIdentifier as String] as? String
        guard cdhash.count == 20, !identifier.isEmpty, identifier.utf8.count <= 255, !identifier.contains("\0"),
              path.path.utf8.count <= 1023,
              team.map({ !$0.isEmpty && $0.utf8.count <= 255 && !$0.contains("\0") }) ?? true else {
            return ActorCodeInspection(reason: "signing_readback_failed",
                error: PWRunnerEquipmentError(operation: "signing_information", message: "observation_limit or invalid signature metadata"))
        }
        let entitlements = info[kSecCodeInfoEntitlementsDict as String] as? [String: Any] ?? [:]
        do {
            return ActorCodeInspection(code: ActorSignedCode(path: path.resolvingSymlinksInPath().path,
                cdhash: cdhash, identifier: identifier, teamID: team, entitlements: entitlements,
                entitlementsXML: try xml(entitlements)), verificationStatus: 0)
        } catch {
            return ActorCodeInspection(reason: "signing_readback_failed", error: self.error("signing_information", error))
        }
    }
    static func inspectStatic(_ url: URL) -> ActorCodeInspection {
        var code: SecStaticCode?
        let created = SecStaticCodeCreateWithPath(url as CFURL, SecCSFlags(), &code)
        guard created == errSecSuccess, let code else {
            return ActorCodeInspection(reason: "signature_unreadable", error: nativeError("worker_signature", created))
        }
        let checked = SecStaticCodeCheckValidity(code, SecCSFlags(rawValue: kSecCSStrictValidate | kSecCSCheckNestedCode), nil)
        guard checked == errSecSuccess else {
            return ActorCodeInspection(verificationStatus: Int(checked), reason: "signature_invalid", error: nativeError("worker_signature", checked))
        }
        var result = signingInfo(code); result.verificationStatus = Int(checked)
        if result.reason != nil { result.reason = "entitlements_unreadable" }
        return result
    }
    static func inspectLive(_ pid: Int32) -> ActorCodeInspection {
        inspectLive(pid, calls: ActorEquipmentSecurityCalls())
    }
    static func inspectLive(_ pid: Int32, calls: ActorEquipmentSecurityCalls) -> ActorCodeInspection {
        var result = ActorCodeInspection()
        func observed(_ operation: String, _ rc: OSStatus) {
            result.observations.append(PWRunnerEquipmentNativeObservation(operation: operation, attempted: true, osstatus: Int(rc)))
        }
        let (rc, dynamic) = calls.guestCode(pid)
        observed("guest_code", rc)
        guard rc == errSecSuccess, let dynamic else { result.reason = "code_lookup_failed"; return result }
        let validity = calls.dynamicValidity(dynamic)
        observed("dynamic_validity", validity)
        guard validity == errSecSuccess else { result.reason = "dynamic_validation_failed"; return result }
        let (staticRC, staticCode) = calls.associatedStaticCode(dynamic)
        observed("associated_static_code", staticRC)
        guard staticRC == errSecSuccess, let staticCode else { result.reason = "signing_readback_failed"; return result }
        let signed = signingInfo(staticCode, calls: calls)
        // Signing info supplies its own native return separately from decoding.
        let signingRC = signed.error?.domain == NSOSStatusErrorDomain ? signed.error?.code ?? 0 : 0
        observed("signing_information", OSStatus(signingRC))
        result.code = signed.code; result.reason = signed.reason; result.error = signed.error
        result.verificationStatus = Int(validity)
        return result
    }
}

final class ActorEquipmentPreparation {
    static let roles = ["selected", "unentitled"]
    static let inventoryRelativePath = "Contents/Resources/worker-equipment.json"
    static func relativePath(_ role: String) -> String {
        "Contents/MacOS/" + (role == "selected" ? "pw-probe-runner" : "pw-probe-runner-unentitled")
    }
    private(set) var inventory: PWRunnerEquipmentInventory
    private(set) var bindings: [PWRunnerEquipmentBinding] = []
    private(set) var entitlements: [PWRunnerEquipmentEntitlements] = []
    var actors: [PWRunnerActorEquipment]
    private(set) var executablePaths: [String]?
    private(set) var failure: ActorEquipmentBindingFailure?
    private let requests: [ActorEquipmentRequest]
    private let calls: ActorEquipmentCalls
    /// Inspected code by binding-table index.
    private var signedBindings: [UInt32: ActorSignedCode] = [:]
    private let overridden: Set<String>

    private init(bundleURL: URL, actors: [ActorEquipmentRequest], overrides: [String: String], calls: ActorEquipmentCalls) {
        inventory = PWRunnerEquipmentInventory(path: bundleURL.appendingPathComponent(Self.inventoryRelativePath).path)
        requests = actors; self.calls = calls; overridden = Set(overrides.keys)
        // An actor's binding is named by table index once its row exists.
        self.actors = actors.map {
            PWRunnerActorEquipment(requested: $0.requested, resolved: $0.requested ?? "selected",
                required_entitlements: $0.requiredEntitlements)
        }
    }
    static func bind(bundleURL: URL = Bundle.main.bundleURL, actors: [ActorEquipmentRequest],
                     overrides: [String: String] = [:], calls: ActorEquipmentCalls = ActorEquipmentCalls()) -> ActorEquipmentPreparation {
        let result = ActorEquipmentPreparation(bundleURL: bundleURL, actors: actors, overrides: overrides, calls: calls)
        result.prepare(bundleURL: bundleURL, overrides: overrides)
        return result
    }
    private func refuse(_ reason: String, actor: String? = nil, binding: UInt32? = nil) {
        if failure == nil { failure = ActorEquipmentBindingFailure(actor_id: actor, binding_ref: binding, reason: reason) }
    }
    private func prepare(bundleURL: URL, overrides: [String: String]) {
        let service = calls.inspectStatic(bundleURL)
        inventory.seal_osstatus = service.verificationStatus
        guard let host = service.code, service.reason == nil else {
            inventory.status = "refused"; inventory.reason = service.reason ?? "signature_unreadable"
            inventory.error = service.error; refuse(inventory.reason!); return
        }
        let manifestURL = URL(fileURLWithPath: inventory.path)
        var inventoryStat = stat()
        guard lstat(inventory.path, &inventoryStat) == 0 else {
            let saved = errno; inventory.status = "refused"; inventory.reason = saved == ENOENT ? "missing" : "inspection_failed"
            inventory.error = PWRunnerEquipmentError(operation: "inventory_read", domain: NSPOSIXErrorDomain, code: Int(saved))
            refuse(inventory.reason!); return
        }
        guard (inventoryStat.st_mode & S_IFMT) == S_IFREG else {
            inventory.status = "refused"; inventory.reason = "not_regular"; refuse("not_regular"); return
        }
        guard manifestURL.resolvingSymlinksInPath().path.hasPrefix(bundleURL.resolvingSymlinksInPath().path + "/") else {
            inventory.status = "refused"; inventory.reason = "outside_bundle"; refuse("outside_bundle"); return
        }
        let bytes: Data
        do { bytes = try ActorEquipmentSystem.readInventory(manifestURL) }
        catch {
            inventory.status = "refused"; inventory.reason = "inspection_failed"
            inventory.error = ActorEquipmentSystem.error("inventory_read", error); refuse("inspection_failed"); return
        }
        let manifest: ActorEquipmentManifest
        do {
            inventory.sha256 = Data(SHA256.hash(data: bytes))
            manifest = try ActorEquipmentManifest.decode(bytes, expectedIdentity: Data(PWShmLayout.abiIdentity))
            inventory.schema_version = manifest.schema_version; inventory.worker_identity = manifest.worker_identity
            inventory.unsigned_worker_sha256 = manifest.unsigned_worker_sha256; inventory.status = "verified"
        } catch {
            inventory.status = "refused"; inventory.reason = "worker_identity_mismatch"
            inventory.error = ActorEquipmentSystem.error("inventory_decode", error); refuse("worker_identity_mismatch"); return
        }
        for role in Self.roles {
            let expected = manifest.workers.first { $0.role == role }!
            bindOne(role: role, path: bundleURL.appendingPathComponent(expected.relative_path).path,
                    expected: expected, bundleURL: bundleURL, hostTeam: host.teamID)
        }
        // Explicit fixture bindings never hide failed packaged role observations.
        for role in Self.roles {
            if let path = overrides[role] { bindOne(role: role, path: path, expected: nil, bundleURL: bundleURL, hostTeam: host.teamID) }
        }
        for index in requests.indices {
            let role = actors[index].resolved, source = overridden.contains(role) ? "test_override" : "packaged"
            actors[index].binding_ref = bindings.firstIndex { $0.role == role && $0.source == source }.map { UInt32($0) }
            guard let reference = actors[index].binding_ref, let signed = signedBindings[reference] else { continue }
            let missing = requests[index].requiredEntitlements.filter { !ActorEquipmentSystem.granted(signed.entitlements[$0]) }
            actors[index].missing_requirements = missing
            actors[index].requirements_status = missing.isEmpty ? "satisfied" : "unsatisfied"
            if !missing.isEmpty { refuse("requirements_unsatisfied", actor: requests[index].actorID, binding: reference) }
        }
        if failure == nil { executablePaths = actors.map { signedBindings[$0.binding_ref!]!.path } }
    }
    private func bindOne(role: String, path: String, expected: ActorEquipmentManifest.Worker?, bundleURL: URL, hostTeam: String?) {
        // The row is appended on every exit, so this is its table index.
        let id = UInt32(bindings.count)
        var row = PWRunnerEquipmentBinding(role: role, source: expected == nil ? "test_override" : "packaged",
            implementation_identity: expected == nil ? "unverified_fixture" : "inventory_verified",
            relative_path: expected?.relative_path, path: path, expected_sha256: expected?.sha256, expected_cdhash: expected?.cdhash)
        defer { bindings.append(row); if let reason = row.reason { refuse(reason, binding: id) } }
        var st = stat()
        guard lstat(path, &st) == 0 else {
            let saved = errno; row.reason = saved == ENOENT ? "missing" : "inspection_failed"
            row.error = PWRunnerEquipmentError(operation: "worker_path", domain: NSPOSIXErrorDomain, code: Int(saved)); return
        }
        guard (st.st_mode & S_IFMT) == S_IFREG else { row.reason = "not_regular"; return }
        guard access(path, X_OK) == 0 else { row.reason = "not_executable"; return }
        let url = URL(fileURLWithPath: path).resolvingSymlinksInPath()
        row.path = url.path
        if expected != nil && !url.path.hasPrefix(bundleURL.resolvingSymlinksInPath().path + "/") {
            row.reason = "outside_bundle"; return
        }
        do { row.sha256 = try ActorEquipmentSystem.hash(url) }
        catch { row.reason = "inspection_failed"; row.error = ActorEquipmentSystem.error("worker_hash", error); return }
        let inspected = calls.inspectStatic(url)
        row.signature_osstatus = inspected.verificationStatus
        guard let signed = inspected.code, inspected.reason == nil else {
            if inspected.reason == "entitlements_unreadable" {
                row.entitlements_ref = UInt32(entitlements.count)
                entitlements.append(PWRunnerEquipmentEntitlements(source: "binding", binding_ref: id,
                    status: "failed", error: inspected.error ?? PWRunnerEquipmentError(operation: "worker_entitlements", message: "read-back unavailable")))
            }
            row.reason = inspected.reason ?? "signature_unreadable"; row.error = inspected.error; return
        }
        row.cdhash = signed.cdhash; row.identifier = signed.identifier; row.team_id = signed.teamID
        row.entitlements_ref = UInt32(entitlements.count)
        entitlements.append(PWRunnerEquipmentEntitlements(source: "binding", binding_ref: id,
            status: "observed", raw_plist: signed.entitlementsXML))
        if let expected {
            let expectedEntitlements = try? ActorEquipmentSystem.parseEntitlements(expected.entitlements_xml)
            row.entitlements_match = expectedEntitlements.map { NSDictionary(dictionary: $0).isEqual(to: signed.entitlements) } ?? false
            guard row.sha256 == expected.sha256, signed.cdhash == expected.cdhash,
                  signed.identifier == expected.identifier, signed.teamID == expected.team_id,
                  signed.teamID == hostTeam, row.entitlements_match == true,
                  role != "unentitled" || signed.entitlements.isEmpty else {
                row.reason = "worker_identity_mismatch"; return
            }
        }
        guard signed.path == url.path else { row.reason = "worker_identity_mismatch"; return }
        row.status = "bound"; signedBindings[id] = signed
    }
    /// Called only for a setup-usable child whose ownership the scheduler holds.
    /// A returned suffix cancels activation; existing setup facts are untouched.
    func inspect(actorIndex: Int, pid: Int32, ownershipConfirmed: Bool, deadlineNs: UInt64? = nil) -> String? {
        guard actors.indices.contains(actorIndex) else { return "ownership_unresolved" }
        var execution = PWRunnerEquipmentExecution(pid: Int(pid), parent_pid: Int(getpid()))
        defer { actors[actorIndex].execution = execution }
        func failed(_ reason: String, mismatch: Bool = false) -> String {
            execution.reason = reason; execution.status = mismatch ? "mismatched" : "inspection_failed"; return reason
        }
        guard ownershipConfirmed else { return failed("ownership_unresolved") }
        guard let now = calls.clock(), deadlineNs.map({ now < $0 }) ?? true else { return failed("inspection_deadline") }
        let observed = calls.inspectLive(pid); execution.native_observations = observed.observations
        execution.observed_at_monotonic_ns = calls.clock()
        // A launched actor has a bound row; without one nothing can be associated.
        guard let binding = actors[actorIndex].binding_ref else { return failed("ownership_unresolved") }
        guard let actual = observed.code, observed.reason == nil else {
            if observed.observations.contains(where: { $0.operation == "signing_information" && $0.attempted }) {
                execution.entitlements_ref = UInt32(entitlements.count)
                entitlements.append(PWRunnerEquipmentEntitlements(source: "execution",
                    binding_ref: binding, actor_id: requests[actorIndex].actorID,
                    status: "failed", error: observed.error ?? PWRunnerEquipmentError(operation: "signing_information", message: "read-back unavailable")))
            }
            return failed(observed.reason ?? "signing_readback_failed")
        }
        execution.path = actual.path; execution.cdhash = actual.cdhash
        execution.identifier = actual.identifier; execution.team_id = actual.teamID
        execution.entitlements_ref = UInt32(entitlements.count)
        entitlements.append(PWRunnerEquipmentEntitlements(source: "execution", binding_ref: binding,
            actor_id: requests[actorIndex].actorID, status: "observed", raw_plist: actual.entitlementsXML))
        guard let expected = signedBindings[binding] else { return failed("ownership_unresolved") }
        guard actual.path == expected.path else { return failed("executable_mismatch", mismatch: true) }
        guard actual.cdhash == expected.cdhash, actual.identifier == expected.identifier, actual.teamID == expected.teamID else {
            return failed("signature_identity_mismatch", mismatch: true)
        }
        guard NSDictionary(dictionary: actual.entitlements).isEqual(to: expected.entitlements) else { return failed("entitlement_mismatch", mismatch: true) }
        guard requests[actorIndex].requiredEntitlements.allSatisfy({ ActorEquipmentSystem.granted(actual.entitlements[$0]) }) else {
            return failed("requirements_unsatisfied", mismatch: true)
        }
        guard let end = calls.clock(), end >= now, deadlineNs.map({ end < $0 }) ?? true else { return failed("inspection_deadline") }
        execution.observed_at_monotonic_ns = end
        execution.status = "matched"; execution.reason = nil; execution.eligible = true; return nil
    }
}

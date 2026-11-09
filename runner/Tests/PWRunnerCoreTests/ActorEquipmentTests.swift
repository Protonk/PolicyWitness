import Foundation
import Darwin
import CryptoKit
import Security
@testable import PWRunnerCore

private let equipmentEmptyXML = "<?xml version=\"1.0\"?><plist version=\"1.0\"><dict/></plist>"

private func equipmentFixture(_ body: (URL, ActorEquipmentCalls) throws -> Void) throws {
    let root = FileManager.default.temporaryDirectory.appendingPathComponent("pw-equipment-unit-\(UUID().uuidString).xpc")
    let macos = root.appendingPathComponent("Contents/MacOS")
    let resources = root.appendingPathComponent("Contents/Resources")
    try FileManager.default.createDirectory(at: macos, withIntermediateDirectories: true)
    try FileManager.default.createDirectory(at: resources, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: root) }
    var rows: [[String: Any]] = []
    for (role, name) in [("selected", "pw-probe-runner"), ("unentitled", "pw-probe-runner-unentitled")] {
        let bytes = Data(name.utf8), file = macos.appendingPathComponent(name)
        try bytes.write(to: file)
        try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: file.path)
        rows.append(["role": role, "relative_path": "Contents/MacOS/" + name,
            "sha256": SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined(),
            "cdhash": String(repeating: "a", count: 40), "identifier": "controlled-worker", "team_id": "TEAM",
            "entitlements_xml": equipmentEmptyXML])
    }
    let inventory: [String: Any] = ["schema_version": 1, "runner_protocol": PWContract.runnerProtocol,
        "worker_identity": PWShmLayout.abiIdentityHex, "unsigned_worker_sha256": String(repeating: "b", count: 64), "workers": rows]
    try JSONSerialization.data(withJSONObject: inventory).write(to: resources.appendingPathComponent("worker-equipment.json"))
    // Constructed signature observations exercise interpretation and refusal.
    // They supply no live or packaged-signature acceptance credit.
    let code: (URL) -> ActorCodeInspection = { url in
        ActorCodeInspection(code: ActorSignedCode(path: url.resolvingSymlinksInPath().path,
            cdhash: Data(repeating: 0xaa, count: 20), identifier: "controlled-worker", teamID: "TEAM",
            entitlements: [:], entitlementsXML: equipmentEmptyXML), verificationStatus: 0)
    }
    try body(root, ActorEquipmentCalls(inspectStatic: code, inspectLive: { _ in
        var value = code(macos.appendingPathComponent("pw-probe-runner"))
        value.observations = ["guest_code", "dynamic_validity", "associated_static_code", "signing_information"].map {
            PWRunnerEquipmentNativeObservation(operation: $0, attempted: true, osstatus: 0)
        }
        return value
    }, clock: { 100 }))
}

func runActorEquipmentTests(_ tk: TestKit) {
    tk.group("equipment retained metadata text budget") {
        tk.run("binding text uses UTF-8 bytes without JSON escape overhead") {
            // Isolate the aggregate resource bound. Other semantic diagnostics
            // are expected for these deliberately non-identity records.
            for unit in ["x", "\"", "\\", "\n", "é"] {
                let text = String(repeating: unit, count: 32_768 / unit.utf8.count)
                var binding = PWRunnerEquipmentBinding(role: "", source: "",
                    implementation_identity: text, path: "", status: "")
                func bounded(_ value: PWRunnerEquipmentBinding) -> Bool {
                    !pwRunnerEquipmentProblems(inventory: nil, bindings: [value], entitlements: [],
                        actors: [], actorIDs: [], actorPIDs: []).contains("equipment binding metadata bound")
                }
                try expectTrue(bounded(binding))
                binding.error = PWRunnerEquipmentError(operation: "x")
                try expectFalse(bounded(binding), "nested error text participates")
            }
        }
        tk.run("execution includes observation operation text and keeps a separate count bound") {
            var execution = PWRunnerEquipmentExecution(status: "", identifier: String(repeating: "é", count: 16_383),
                native_observations: [PWRunnerEquipmentNativeObservation(operation: "é", attempted: false)], reason: nil)
            func problems(_ value: PWRunnerEquipmentExecution) -> [String] {
                let actor = PWRunnerActorEquipment(requested: nil, resolved: "selected",
                    required_entitlements: [], execution: value)
                return pwRunnerEquipmentProblems(inventory: nil, bindings: [], entitlements: [],
                    actors: [actor], actorIDs: ["A"], actorPIDs: [nil])
            }
            try expectFalse(problems(execution).contains("equipment execution metadata bound"))
            execution.reason = "x"
            try expectTrue(problems(execution).contains("equipment execution metadata bound"))
            execution.identifier = nil; execution.reason = nil
            execution.native_observations = Array(repeating: PWRunnerEquipmentNativeObservation(operation: "", attempted: false), count: 5)
            try expectFalse(problems(execution).contains("equipment execution metadata bound"))
            try expectTrue(problems(execution).contains("equipment live observation capacity"))
        }
    }

    tk.group("actor equipment: binding, requirements and observed execution") {
        tk.run("unused packaged role is required and no alternate worker is substituted") {
            try equipmentFixture { root, calls in
                let request = [ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])]
                let complete = ActorEquipmentPreparation.bind(bundleURL: root, actors: request, calls: calls)
                try expectNil(complete.failure)
                try expectEqual(complete.bindings.map { $0.role }, ["selected", "unentitled"])
                try expectEqual(complete.bindings.map { $0.source }, ["packaged", "packaged"])
                try expectEqual(complete.actors[0].binding_ref, 0)
                try FileManager.default.removeItem(at: root.appendingPathComponent("Contents/MacOS/pw-probe-runner-unentitled"))
                let missing = ActorEquipmentPreparation.bind(bundleURL: root, actors: request, calls: calls)
                try expectEqual(missing.failure?.reason, "missing")
                try expectEqual(missing.failure?.binding_ref, 1)
                try expectNil(missing.executablePaths)
                try expectEqual(missing.bindings.first?.status, "bound")
            }
        }
        tk.run("requirements are per actor and only boolean true satisfies a key") {
            try expectTrue(ActorEquipmentSystem.granted(NSNumber(value: true)))
            try expectFalse(ActorEquipmentSystem.granted(NSNumber(value: 1)))
            try expectFalse(ActorEquipmentSystem.granted("true"))
            try equipmentFixture { root, calls in
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                    ActorEquipmentRequest(actorID: "A", index: 0, requested: "selected", requiredEntitlements: []),
                    ActorEquipmentRequest(actorID: "B", index: 1, requested: "selected", requiredEntitlements: ["required"])
                ], calls: calls)
                try expectEqual(result.actors[0].requirements_status, "satisfied")
                try expectEqual(result.actors[1].requirements_status, "unsatisfied")
                try expectEqual(result.failure?.actor_id, "B")
                try expectTrue(result.bindings.allSatisfy { $0.status == "bound" })
            }
        }
        tk.run("live mismatch cannot become a matched equipment record or eligible actor") {
            try equipmentFixture { root, calls in
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                    ActorEquipmentRequest(actorID: "issuer", index: 0, requested: "unentitled", requiredEntitlements: [])
                ], calls: calls)
                try expectEqual(result.inspect(actorIndex: 0, pid: 123, ownershipConfirmed: true), "executable_mismatch")
                try expectEqual(result.actors[0].execution.status, "mismatched")
                try expectFalse(result.actors[0].execution.eligible)
                try expectEqual(result.actors[0].execution.path, root.appendingPathComponent("Contents/MacOS/pw-probe-runner").resolvingSymlinksInPath().path)
                try expectEqual(result.entitlements.last?.actor_id, "issuer")
            }
        }
        tk.run("reader rejects a changed process association and an invented requirement decision") {
            try equipmentFixture { root, calls in
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                    ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                ], calls: calls)
                try expectNil(result.inspect(actorIndex: 0, pid: 123, ownershipConfirmed: true))
                func problems(_ actors: [PWRunnerActorEquipment]) -> [String] {
                    pwRunnerEquipmentProblems(inventory: result.inventory, bindings: result.bindings,
                        entitlements: result.entitlements, actors: actors, actorIDs: ["A"], actorPIDs: [123])
                }
                try expectEqual(problems(result.actors), [])
                var wrongPID = result.actors; wrongPID[0].execution.pid = 124
                try expectTrue(problems(wrongPID).contains("equipment execution PID association"))
                var wrongRequirement = result.actors; wrongRequirement[0].required_entitlements = ["absent"]
                try expectTrue(problems(wrongRequirement).contains("equipment requirement decision"))
            }
        }
        tk.run("fixture overrides preserve packaged rows and remain explicitly unverified") {
            try equipmentFixture { root, calls in
                let fixture = root.appendingPathComponent("fixture")
                try Data("fixture bytes".utf8).write(to: fixture)
                try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: fixture.path)
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                    ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                ], overrides: ["selected": fixture.path], calls: calls)
                try expectNil(result.failure)
                try expectEqual(result.bindings.count, 3)
                // The override row follows the two packaged rows; the actor names it by index.
                try expectEqual(result.actors[0].binding_ref, 2)
                try expectEqual(result.bindings.map { $0.role }, ["selected", "unentitled", "selected"])
                try expectEqual(result.bindings.last?.source, "test_override")
                try expectEqual(result.bindings.last?.implementation_identity, "unverified_fixture")
                try expectNil(result.bindings.last?.expected_sha256)
            }
        }
        tk.run("expired inspection and lost ownership do not query a new process") {
            try equipmentFixture { root, original in
                var calls = original, inspected = false
                calls.inspectLive = { _ in inspected = true; return ActorCodeInspection() }
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                    ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                ], calls: calls)
                try expectEqual(result.inspect(actorIndex: 0, pid: 123, ownershipConfirmed: false), "ownership_unresolved")
                try expectFalse(inspected)
                try expectEqual(result.inspect(actorIndex: 0, pid: 123, ownershipConfirmed: true, deadlineNs: 100), "inspection_deadline")
                try expectFalse(inspected)
            }
        }
        tk.run("all four live inspection failure prefixes retain only reached observations") {
            let operations = ["guest_code", "dynamic_validity", "associated_static_code", "signing_information"]
            let reasons = ["code_lookup_failed", "dynamic_validation_failed", "signing_readback_failed", "signing_readback_failed"]
            for failedIndex in 0..<4 {
                try equipmentFixture { root, original in
                    var calls = original
                    let prefix = (0...failedIndex).map { index in
                        PWRunnerEquipmentNativeObservation(operation: operations[index], attempted: true,
                            osstatus: index == failedIndex ? -67000 - index : 0)
                    }
                    // The seam supplies constructed native observations. This
                    // tests retention/eligibility, not Security.framework calls.
                    calls.inspectLive = { _ in ActorCodeInspection(reason: reasons[failedIndex],
                        error: PWRunnerEquipmentError(operation: operations[failedIndex], domain: NSOSStatusErrorDomain,
                            code: -67000 - failedIndex), observations: prefix) }
                    let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                        ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                    ], calls: calls)
                    try expectNil(result.failure)
                    try expectEqual(result.inspect(actorIndex: 0, pid: 123, ownershipConfirmed: true), reasons[failedIndex])
                    let execution = result.actors[0].execution
                    try expectEqual(execution.native_observations, prefix)
                    try expectEqual(execution.status, "inspection_failed")
                    try expectFalse(execution.eligible)
                    try expectNil(execution.path)
                    try expectEqual(result.entitlements.count, failedIndex == 3 ? 3 : 2)
                    if failedIndex == 3 {
                        try expectEqual(result.entitlements.last?.status, "failed")
                        try expectEqual(result.entitlements.last?.error?.code, -67003)
                        try expectNil(result.entitlements.last?.raw_plist)
                    } else { try expectNil(execution.entitlements_ref) }
                    try expectEqual(pwRunnerEquipmentProblems(inventory: result.inventory, bindings: result.bindings,
                        entitlements: result.entitlements, actors: result.actors, actorIDs: ["A"], actorPIDs: [123]), [])
                    var wrongOrder = result.actors
                    wrongOrder[0].execution.native_observations[0].operation = "signing_information"
                    try expectTrue(pwRunnerEquipmentProblems(inventory: result.inventory, bindings: result.bindings,
                        entitlements: result.entitlements, actors: wrongOrder, actorIDs: ["A"], actorPIDs: [123])
                        .contains("equipment native observation order/result"))
                }
            }
        }
        tk.run("each native Security failure stops the production live inspection branch") {
            // Real reference-counted Security objects keep these controls safe.
            // The call returns below are constructed; this is branch/retention
            // evidence, not an observation of a Security.framework outage.
            var current: SecCode?
            let selfRC = SecCodeCopySelf(SecCSFlags(), &current)
            try expectEqual(selfRC, errSecSuccess)
            guard let current else { throw TestFailure(message: "self code object unavailable") }
            var associated: SecStaticCode?
            let staticRC = SecCodeCopyStaticCode(current, SecCSFlags(), &associated)
            try expectEqual(staticRC, errSecSuccess)
            guard let associated else { throw TestFailure(message: "self static code object unavailable") }
            var information: CFDictionary?
            let infoRC = SecCodeCopySigningInformation(associated,
                SecCSFlags(rawValue: kSecCSSigningInformation), &information)
            try expectEqual(infoRC, errSecSuccess)
            guard let information, let dictionary = information as? [String: Any],
                  let executable = dictionary[kSecCodeInfoMainExecutable as String] as? URL else {
                throw TestFailure(message: "self signing information unavailable")
            }
            let operations = ["guest_code", "dynamic_validity", "associated_static_code", "signing_information"]
            let reasons = ["code_lookup_failed", "dynamic_validation_failed", "signing_readback_failed", "signing_readback_failed"]
            for failedIndex in -1..<4 {
                let failure = OSStatus(-67010 - failedIndex)
                var reached: [String] = []
                var correctInputs = true
                let calls = ActorEquipmentSecurityCalls(
                    guestCode: { pid in
                        reached.append("guest_code")
                        correctInputs = correctInputs && pid == getpid()
                        return failedIndex == 0 ? (failure, nil) : (errSecSuccess, current)
                    },
                    dynamicValidity: { code in
                        reached.append("dynamic_validity")
                        correctInputs = correctInputs && CFEqual(code, current)
                        return failedIndex == 1 ? failure : errSecSuccess
                    },
                    associatedStaticCode: { code in
                        reached.append("associated_static_code")
                        correctInputs = correctInputs && CFEqual(code, current)
                        return failedIndex == 2 ? (failure, nil) : (errSecSuccess, associated)
                    },
                    signingInformation: { code in
                        reached.append("signing_information")
                        correctInputs = correctInputs && CFEqual(code, associated)
                        return failedIndex == 3 ? (failure, nil) : (errSecSuccess, information)
                    })
                let result = ActorEquipmentSystem.inspectLive(getpid(), calls: calls)
                let count = failedIndex < 0 ? 4 : failedIndex + 1
                try expectEqual(reached, Array(operations.prefix(count)), "later native calls must remain unreached")
                try expectTrue(correctInputs)
                let expected = (0..<count).map { index in
                    PWRunnerEquipmentNativeObservation(operation: operations[index], attempted: true,
                        osstatus: index == failedIndex ? Int(failure) : Int(errSecSuccess))
                }
                try expectEqual(result.observations, expected)
                if failedIndex < 0 {
                    try expectNil(result.reason)
                    try expectNil(result.error)
                    try expectEqual(result.verificationStatus, 0)
                    try expectEqual(result.code?.path, executable.resolvingSymlinksInPath().path)
                    try expectTrue(result.code?.cdhash.isEmpty == false)
                } else {
                    try expectEqual(result.reason, reasons[failedIndex])
                    try expectNil(result.code)
                    if failedIndex == 3 {
                        try expectEqual(result.verificationStatus, 0)
                        try expectEqual(result.error?.operation, "signing_information")
                        try expectEqual(result.error?.domain, NSOSStatusErrorDomain)
                        try expectEqual(result.error?.code, Int(failure))
                        try expectNil(result.error?.message)
                    } else {
                        // These branches retain the OSStatus in their native
                        // observation, without inventing a signing read-back.
                        try expectNil(result.verificationStatus)
                        try expectNil(result.error)
                    }
                }
            }
        }
        tk.run("late or unavailable completion clock withholds matched live evidence") {
            let clockSamples: [[UInt64?]] = [[100, 101, 200], [100, 101, nil], [100, 101, 99], [nil]]
            for samples in clockSamples {
                try equipmentFixture { root, original in
                    var calls = original, index = 0, inspected = 0
                    calls.clock = { defer { index += 1 }; return samples[min(index, samples.count - 1)] }
                    calls.inspectLive = { pid in inspected += 1; return original.inspectLive(pid) }
                    let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                        ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                    ], calls: calls)
                    try expectEqual(result.inspect(actorIndex: 0, pid: 123, ownershipConfirmed: true, deadlineNs: 200), "inspection_deadline")
                    try expectFalse(result.actors[0].execution.eligible)
                    try expectEqual(result.actors[0].execution.status, "inspection_failed")
                    try expectEqual(inspected, samples.count == 1 ? 0 : 1)
                    try expectEqual(result.entitlements.count, samples.count == 1 ? 2 : 3,
                        "late completion retains reached signing readback")
                }
            }
        }
        tk.run("missing live code is an inspection failure even when static binding succeeded") {
            try equipmentFixture { root, original in
                var calls = original
                calls.inspectLive = { _ in ActorCodeInspection(reason: "code_lookup_failed", observations: [
                    PWRunnerEquipmentNativeObservation(operation: "guest_code", attempted: true, osstatus: -67062)]) }
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                    ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                ], calls: calls)
                try expectNil(result.failure)
                try expectEqual(result.inspect(actorIndex: 0, pid: 123, ownershipConfirmed: true), "code_lookup_failed")
                try expectFalse(result.actors[0].execution.eligible)
                try expectEqual(result.bindings.map { $0.status }, ["bound", "bound"])
                // No exit/reap is inferred from a code lookup failure.
                try expectNil(result.actors[0].execution.entitlements_ref)
            }
        }
        tk.run("closed inventory refuses missing duplicate escaping stale and entitled roles") {
            let mutations: [(String, (inout [String: Any]) -> Void)] = [
                ("missing", { $0["workers"] = Array(($0["workers"] as! [[String: Any]]).prefix(1)) }),
                ("duplicate", { value in var rows = value["workers"] as! [[String: Any]]; rows[1] = rows[0]; value["workers"] = rows }),
                ("escaping", { value in var rows = value["workers"] as! [[String: Any]]; rows[0]["relative_path"] = "../worker"; value["workers"] = rows }),
                ("build_identity", { $0["worker_identity"] = String(repeating: "f", count: 64) }),
                ("protocol", { $0["runner_protocol"] = -1 }),
                ("entitled_unentitled", { value in var rows = value["workers"] as! [[String: Any]];
                    rows[1]["entitlements_xml"] = "<plist version=\"1.0\"><dict><key>permission</key><true/></dict></plist>"; value["workers"] = rows }),
                ("unknown_field", { $0["future"] = true })]
            for (name, mutate) in mutations {
                try equipmentFixture { root, calls in
                    let path = root.appendingPathComponent("Contents/Resources/worker-equipment.json")
                    var manifest = try JSONSerialization.jsonObject(with: Data(contentsOf: path)) as! [String: Any]
                    mutate(&manifest)
                    try JSONSerialization.data(withJSONObject: manifest).write(to: path)
                    let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                        ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                    ], calls: calls)
                    try expectEqual(result.failure?.reason, "worker_identity_mismatch", name)
                    try expectEqual(result.inventory.status, "refused", name)
                    try expectTrue(result.bindings.isEmpty, name)
                    try expectNil(result.executablePaths, name)
                }
            }
            try equipmentFixture { root, calls in
                // Artifact changed while the signed-role manifest remains old.
                try Data("different worker bytes".utf8).write(to: root.appendingPathComponent("Contents/MacOS/pw-probe-runner"))
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                    ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                ], calls: calls)
                try expectEqual(result.failure?.reason, "worker_identity_mismatch")
                try expectEqual(result.failure?.binding_ref, 0)
                try expectEqual(result.bindings.map { $0.status }, ["refused", "bound"])
                try expectNil(result.executablePaths)
            }
        }
        tk.run("static inspection cannot substitute paths or add unentitled signing authority") {
            for fault in ["path", "entitlements"] {
                try equipmentFixture { root, original in
                    var calls = original
                    calls.inspectStatic = { path in
                        var value = original.inspectStatic(path)
                        if path.lastPathComponent == "pw-probe-runner-unentitled" {
                            if fault == "path" { value.code!.path = root.appendingPathComponent("Contents/MacOS/pw-probe-runner").resolvingSymlinksInPath().path }
                            else { value.code!.entitlements = ["permission": true]
                                value.code!.entitlementsXML = "<plist version=\"1.0\"><dict><key>permission</key><true/></dict></plist>" }
                        }
                        return value
                    }
                    let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                        ActorEquipmentRequest(actorID: "A", index: 0, requested: "unentitled", requiredEntitlements: [])
                    ], calls: calls)
                    try expectEqual(result.failure?.reason, "worker_identity_mismatch", fault)
                    try expectEqual(result.failure?.binding_ref, 1, fault)
                    try expectNil(result.executablePaths, fault)
                    try expectEqual(result.bindings.map { $0.status }, ["bound", "refused"])
                }
            }
        }
        tk.run("worker filesystem refusals precede injected signature inspection") {
            // Actual filesystem shapes; enclosing signature remains a constructed
            // valid observation so this isolates the host path branch only.
            for fault in ["symlink", "directory", "nonexecutable"] {
                try equipmentFixture { root, original in
                    let worker = root.appendingPathComponent("Contents/MacOS/pw-probe-runner")
                    if fault == "nonexecutable" {
                        try FileManager.default.setAttributes([.posixPermissions: 0o644], ofItemAtPath: worker.path)
                    } else {
                        try FileManager.default.removeItem(at: worker)
                        if fault == "directory" {
                            try FileManager.default.createDirectory(at: worker, withIntermediateDirectories: false)
                        } else {
                            try FileManager.default.createSymbolicLink(at: worker,
                                withDestinationURL: root.appendingPathComponent("Contents/MacOS/pw-probe-runner-unentitled"))
                        }
                    }
                    var calls = original, selectedInspections = 0
                    calls.inspectStatic = { path in
                        if path == worker { selectedInspections += 1 }
                        return original.inspectStatic(path)
                    }
                    let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                        ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: [])
                    ], calls: calls)
                    try expectEqual(result.failure?.reason, fault == "nonexecutable" ? "not_executable" : "not_regular", fault)
                    try expectEqual(result.failure?.binding_ref, 0, fault)
                    try expectEqual(selectedInspections, 0, fault)
                    try expectEqual(result.bindings.map { $0.status }, ["refused", "bound"], fault)
                    try expectNil(result.executablePaths, fault)
                }
            }
        }
        tk.run("bound false requirements and unreadable signing readback never grant authority") {
            for fault in ["false", "unreadable"] {
                try equipmentFixture { root, original in
                    let xml = "<plist version=\"1.0\"><dict><key>required</key><false/></dict></plist>"
                    let inventory = root.appendingPathComponent("Contents/Resources/worker-equipment.json")
                    var manifest = try JSONSerialization.jsonObject(with: Data(contentsOf: inventory)) as! [String: Any]
                    var rows = manifest["workers"] as! [[String: Any]]
                    rows[0]["entitlements_xml"] = xml; manifest["workers"] = rows
                    try JSONSerialization.data(withJSONObject: manifest).write(to: inventory)
                    var calls = original
                    calls.inspectStatic = { path in
                        var value = original.inspectStatic(path)
                        if path.lastPathComponent == "pw-probe-runner" {
                            if fault == "false" {
                                value.code!.entitlements = ["required": false]
                                value.code!.entitlementsXML = xml
                            } else {
                                value.code = nil; value.reason = "entitlements_unreadable"
                                value.error = PWRunnerEquipmentError(operation: "signing_information", domain: NSOSStatusErrorDomain, code: -67062)
                            }
                        }
                        return value
                    }
                    let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                        ActorEquipmentRequest(actorID: "A", index: 0, requested: "selected", requiredEntitlements: []),
                        ActorEquipmentRequest(actorID: "B", index: 1, requested: "selected", requiredEntitlements: ["required"])
                    ], calls: calls)
                    try expectNil(result.executablePaths, fault)
                    if fault == "false" {
                        try expectEqual(result.failure?.reason, "requirements_unsatisfied")
                        try expectEqual(result.failure?.actor_id, "B")
                        try expectEqual(result.actors.map { $0.requirements_status }, ["satisfied", "unsatisfied"])
                        try expectEqual(result.actors[1].missing_requirements, ["required"])
                        try expectTrue(result.bindings.allSatisfy { $0.status == "bound" })
                        try expectEqual(result.entitlements.first?.raw_plist, xml)
                    } else {
                        try expectEqual(result.failure?.reason, "entitlements_unreadable")
                        try expectTrue(result.actors.allSatisfy { $0.requirements_status == "unobserved" })
                        try expectEqual(result.entitlements.first?.status, "failed")
                        try expectNil(result.entitlements.first?.raw_plist)
                    }
                }
            }
        }
        tk.run("live required keys cannot borrow a successful static requirement decision") {
            for fault in ["matched", "false", "absent", "unreadable"] {
                try equipmentFixture { root, original in
                    let xml = "<plist version=\"1.0\"><dict><key>required</key><true/></dict></plist>"
                    let inventory = root.appendingPathComponent("Contents/Resources/worker-equipment.json")
                    var manifest = try JSONSerialization.jsonObject(with: Data(contentsOf: inventory)) as! [String: Any]
                    var rows = manifest["workers"] as! [[String: Any]]
                    rows[0]["entitlements_xml"] = xml; manifest["workers"] = rows
                    try JSONSerialization.data(withJSONObject: manifest).write(to: inventory)
                    var calls = original
                    calls.inspectStatic = { path in
                        var value = original.inspectStatic(path)
                        if path.lastPathComponent == "pw-probe-runner" {
                            value.code!.entitlements = ["required": true]; value.code!.entitlementsXML = xml
                        }
                        return value
                    }
                    calls.inspectLive = { pid in
                        var value = original.inspectLive(pid)
                        value.code!.entitlements = ["required": true]; value.code!.entitlementsXML = xml
                        if fault == "false" {
                            value.code!.entitlements = ["required": false]
                            value.code!.entitlementsXML = xml.replacingOccurrences(of: "<true/>", with: "<false/>")
                        } else if fault == "absent" {
                            value.code!.entitlements = [:]; value.code!.entitlementsXML = equipmentEmptyXML
                        } else if fault == "unreadable" {
                            value.code = nil; value.reason = "signing_readback_failed"
                            value.error = PWRunnerEquipmentError(operation: "signing_information", domain: NSOSStatusErrorDomain, code: -67062)
                            value.observations[value.observations.count - 1].osstatus = -67062
                        }
                        return value
                    }
                    let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                        ActorEquipmentRequest(actorID: "A", index: 0, requested: "selected", requiredEntitlements: ["required"])
                    ], calls: calls)
                    try expectNil(result.failure)
                    try expectEqual(result.actors[0].requirements_status, "satisfied")
                    let reason = result.inspect(actorIndex: 0, pid: 123, ownershipConfirmed: true)
                    if fault == "matched" {
                        try expectNil(reason); try expectTrue(result.actors[0].execution.eligible)
                    } else {
                        try expectEqual(reason, fault == "unreadable" ? "signing_readback_failed" : "entitlement_mismatch")
                        try expectFalse(result.actors[0].execution.eligible)
                    }
                    try expectNil(result.failure, "a live failure must not invent a preparation refusal")
                    try expectEqual(result.entitlements.last?.status, fault == "unreadable" ? "failed" : "observed")
                    if fault == "unreadable" { try expectNil(result.entitlements.last?.raw_plist) }
                }
            }
        }
        tk.run("entitlement XML accepts exactly 65536 UTF8 bytes and refuses one more") {
            let exact = equipmentEmptyXML + String(repeating: " ", count: 65_536 - equipmentEmptyXML.utf8.count)
            try expectEqual(exact.utf8.count, 65_536)
            try expectTrue(try ActorEquipmentSystem.parseEntitlements(exact).isEmpty)
            try expectThrows({ _ = try ActorEquipmentSystem.parseEntitlements(exact + " ") })
            let overhead = try PropertyListSerialization.data(fromPropertyList: ["payload": "a"], format: .xml, options: 0).count - 1
            let serialized = try ActorEquipmentSystem.xml(["payload": String(repeating: "a", count: 65_536 - overhead)])
            try expectEqual(serialized.utf8.count, 65_536)
            try expectThrows({ _ = try ActorEquipmentSystem.xml(["payload": String(repeating: "a", count: 65_537 - overhead)]) })
            try equipmentFixture { root, calls in
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [], calls: calls)
                var records = result.entitlements
                records[0].raw_plist = exact
                try expectEqual(pwRunnerEquipmentProblems(inventory: result.inventory, bindings: result.bindings,
                    entitlements: records, actors: [], actorIDs: [], actorPIDs: []), [])
                records[0].raw_plist = exact + " "
                try expectTrue(pwRunnerEquipmentProblems(inventory: result.inventory, bindings: result.bindings,
                    entitlements: records, actors: [], actorIDs: [], actorPIDs: []).contains("equipment invalid entitlement observation"))
            }
        }
        tk.run("sealed inventory reader accepts exactly one MiB and refuses one more before binding") {
            try equipmentFixture { root, calls in
                let path = root.appendingPathComponent("Contents/Resources/worker-equipment.json")
                let original = try Data(contentsOf: path)
                var exact = original
                exact.append(Data(repeating: 0x20, count: 1_048_576 - original.count))
                try exact.write(to: path)
                try expectEqual(try ActorEquipmentSystem.readInventory(path).count, 1_048_576)
                let good = ActorEquipmentPreparation.bind(bundleURL: root, actors: [], calls: calls)
                try expectNil(good.failure)
                exact.append(0x20); try exact.write(to: path)
                try expectThrows({ _ = try ActorEquipmentSystem.readInventory(path) })
                try expectThrows({ _ = try ActorEquipmentManifest.decode(exact, expectedIdentity: Data(PWShmLayout.abiIdentity)) })
                let refused = ActorEquipmentPreparation.bind(bundleURL: root, actors: [], calls: calls)
                try expectEqual(refused.failure?.reason, "inspection_failed")
                try expectTrue(refused.bindings.isEmpty)
                try expectNil(refused.executablePaths)
            }
        }
        tk.run("equipment reader independently enforces key count bytes and diagnostic bounds") {
            try equipmentFixture { root, calls in
                let keys = [String(repeating: "é", count: 127) + "a"] + (1..<64).map { "key-\($0)" }
                let result = ActorEquipmentPreparation.bind(bundleURL: root, actors: [
                    ActorEquipmentRequest(actorID: "A", index: 0, requested: nil, requiredEntitlements: keys)
                ], calls: calls)
                func problems(_ actors: [PWRunnerActorEquipment]) -> [String] {
                    pwRunnerEquipmentProblems(inventory: result.inventory, bindings: result.bindings,
                        entitlements: result.entitlements, actors: actors, actorIDs: ["A"], actorPIDs: [nil])
                }
                try expectEqual(keys.count, 64); try expectEqual(keys[0].utf8.count, 255)
                try expectEqual(problems(result.actors), [])
                for invalid in [keys + ["one-more"], [keys[0] + "a"], ["duplicate", "duplicate"], ["embedded\0nul"]] {
                    var actors = result.actors; actors[0].required_entitlements = invalid
                    actors[0].missing_requirements = invalid
                    try expectTrue(problems(actors).contains("equipment requirements bounds"))
                }
                let message = String(repeating: "é", count: 512)
                try expectEqual(ActorEquipmentSystem.bounded(message + "x"), message)
                let detail = ActorEquipmentSystem.error("worker_path", NSError(domain: String(repeating: "d", count: 129),
                    code: 17, userInfo: [NSLocalizedDescriptionKey: message + "x"]))
                try expectEqual(detail.domain?.utf8.count, 128)
                try expectEqual(detail.message?.utf8.count, 1024)
                try expectEqual(detail.code, 17)
                var inventory = PWRunnerEquipmentInventory(path: "/constructed/inventory", status: "refused", error: detail)
                try expectEqual(pwRunnerEquipmentProblems(inventory: inventory, bindings: [], entitlements: [],
                    actors: [], actorIDs: [], actorPIDs: []), [])
                inventory.error!.message = message + "x"
                try expectTrue(pwRunnerEquipmentProblems(inventory: inventory, bindings: [], entitlements: [],
                    actors: [], actorIDs: [], actorPIDs: []).contains("equipment error message bound"))
            }
        }
    }
}

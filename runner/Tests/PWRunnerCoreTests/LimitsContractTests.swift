import Foundation
@testable import PWRunnerCore

private struct DocumentedLimit: Decodable {
    struct Check: Decodable { let path: String; let kind: String }
    let id: String
    let value: Int
    let checks: [Check]
}
private struct LimitsManifest: Decodable { let limits: [DocumentedLimit] }

// These calibrations call the admitting implementation; their search bounds
// only bracket the result. The literal boundary assertions below are separate
// from limits.json. Constructed reader records isolate the named predicate.
private func largestAcceptedCount(upper: Int, accepts: (Int) throws -> Bool) throws -> Int {
    try expectTrue(try accepts(1))
    try expectFalse(try accepts(upper))
    var low = 1, high = upper
    while high - low > 1 {
        let middle = low + (high - low) / 2
        if try accepts(middle) { low = middle } else { high = middle }
    }
    return low
}

private func manifestAcceptsSigningText(_ text: String, field: String) throws -> Bool {
    let workers: [[String: Any]] = ActorEquipmentPreparation.roles.map { role in
        var row: [String: Any] = ["role": role,
            "relative_path": ActorEquipmentPreparation.relativePath(role),
            "sha256": String(repeating: "0", count: 64), "cdhash": String(repeating: "0", count: 40),
            "identifier": "worker", "team_id": NSNull(),
            "entitlements_xml": "<plist version=\"1.0\"><dict/></plist>"]
        row[field] = text
        return row
    }
    let manifest: [String: Any] = ["schema_version": 1, "contract": "test:limit-manifest",
        "worker_identity": String(repeating: "0", count: 64),
        "unsigned_worker_sha256": String(repeating: "0", count: 64), "workers": workers]
    let data = try JSONSerialization.data(withJSONObject: manifest)
    do {
        _ = try ActorEquipmentManifest.decode(data, expectedIdentity: Data(repeating: 0, count: 32),
            expectedContract: "test:limit-manifest")
        return true
    } catch { return false }
}

private func equipmentTextProblems(path: String = "/constructed", identifier: String? = nil,
                                  team: String? = nil) -> [String] {
    let row = PWRunnerEquipmentBinding(role: "selected", source: "test_override",
        implementation_identity: "unverified_fixture", path: path, identifier: identifier, team_id: team)
    return pwRunnerEquipmentProblems(inventory: nil, bindings: [row], entitlements: [],
        actors: [], actorIDs: [], actorPIDs: [])
}

private func cleanupReferenceProblems(name: String) -> [String] {
    let region = PWRunnerAuthorityScope(actor_id: "A", actor_index: 0, operations: [
        PWRunnerAuthorityOperation(slot: 0, operation: "shm_open", role: "setup", state: "succeeded",
            native_kind: "integer", native_rc: 3),
        PWRunnerAuthorityOperation(slot: 1, operation: "shm_unlink", role: "setup", state: "failed",
            native_kind: "integer", native_rc: -1, errno: 1)],
        ownership: ["object_name": "unresolved"],
        cleanup_reference: PWAuthorityCleanupReference(name: name, host_pid: 1, session_nonce: 1))
    let setup = PWRunnerAuthoritySetup(host: PWRunnerAuthorityHost(run: PWRunnerAuthorityScope(), regions: [region]),
        workers: [PWRunnerAuthorityScope(actor_id: "A", actor_index: 0, publication: "not_observed")])
    return authoritySetupIntegrityErrors(setup, actorIDs: ["A"], tokenRefs: [])
}

func runLimitsContractTests(_ tk: TestKit) {
    tk.group("Documented limits") {
        tk.run("compiled layout and production defaults agree with inventory") {
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let manifest = try JSONDecoder().decode(LimitsManifest.self,
                from: Data(contentsOf: root.appendingPathComponent("docs/limits.json")))
            let worker = CWorkerInput(workerExecutablePath: "unused", policy: "", slots: [])
            let validator = ValidatorClientInput(executablePath: "unused", targetPid: 1, probes: [])
            guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
                throw TestFailure(message: "compiled C limit probe missing; run runner_unit")
            }
            let probe = Process(), pipe = Pipe()
            probe.executableURL = URL(fileURLWithPath: fixture + ".worker-limits")
            probe.standardOutput = pipe
            try probe.run()
            let output = pipe.fileHandleForReading.readDataToEndOfFile()
            probe.waitUntilExit()
            try expectEqual(probe.terminationStatus, 0)
            let native = Dictionary(uniqueKeysWithValues: String(decoding: output, as: UTF8.self)
                .split(separator: "\n").compactMap { line -> (String, Int)? in
                    let pair = line.split(separator: "=", maxSplits: 1)
                    guard pair.count == 2, let value = Int(pair[1]) else { return nil }
                    return (String(pair[0]), value)
                })
            guard let proceedWait = native["worker_proceed_wait"], let attemptBudget = native["exec_attempt_budget"] else {
                throw TestFailure(message: "compiled C probe omitted worker_proceed_wait or exec_attempt_budget")
            }
            let rejected = decodeValidatorFrames(Data(repeating: 0xff, count: 1024))
            guard let fault = rejected.fault else { throw TestFailure(message: "invalid frame accepted") }
            // Observe returned paths rather than restating the manifest's maxima.
            let retainedDepths = (0...32).compactMap { count in
                PWRunnerRequestFailure(code: "invalid_request", path: Array(repeating: "x", count: count)).path?.count
            }
            let retainedComponents = (0...256).compactMap { count in
                PWRunnerRequestFailure(code: "invalid_request", path: [String(repeating: "x", count: count)]).path?.first?.utf8.count
            }
            guard let retainedDepth = retainedDepths.max(), let retainedComponentBytes = retainedComponents.max() else {
                throw TestFailure(message: "request failure constructor retained no diagnostic paths")
            }
            let signingTextBytes = try largestAcceptedCount(upper: 1024) { count in
                try manifestAcceptsSigningText(String(repeating: "x", count: count), field: "identifier")
            }
            let equipmentPathBytes = try largestAcceptedCount(upper: 4096) { count in
                !equipmentTextProblems(path: "/" + String(repeating: "x", count: count - 1))
                    .contains("equipment binding path")
            }
            let cleanupNameBytes = try largestAcceptedCount(upper: 128) { count in
                cleanupReferenceProblems(name: "/" + String(repeating: "x", count: count - 1)).isEmpty
            }
            let equipmentDomainBytes = ActorEquipmentSystem.error("worker_path",
                NSError(domain: String(repeating: "d", count: 2048), code: 1)).domain!.utf8.count
            guard let fixtureDelay = native["worker_fixture_delay"] else {
                throw TestFailure(message: "compiled C probe omitted fixture delay parser capacity")
            }
            let observed: [String: Int] = [
                "request_failure_path_components": retainedDepth,
                "request_failure_path_component": retainedComponentBytes,
                "policy_source": PWShmLayout.policyBytes - 1,
                "probe_steps": PWShmLayout.maxSteps,
                "phase_count": PWRunnerPhase.maximumCount,
                "phase_records": PWShmLayout.maxPhases,
                "actors": PWActorLimits.actors,
                "actor_phases": PWActorLimits.phases,
                "actor_issues": PWActorLimits.issues,
                "actor_deliveries": PWActorLimits.deliveries,
                "actor_handles": PWActorLimits.handles,
                "actor_releases": PWActorLimits.releases,
                "actor_id": PWActorLimits.identifierBytes,
                "extension_issue_target": PWActorLimits.targetBytes,
                "actor_setup_allowance": PWActorLimits.setupMs,
                "actor_execution_allowance": PWActorLimits.executionMs,
                "actor_collection_allowance": PWActorLimits.collectionMs,
                "actor_release_wait": PWActorLimits.releaseWaitMs,
                "actor_exchange_allowance": PWActorLimits.exchangeMs,
                "actor_lifetime_cutoff": PWActorLimits.lifetimeMs,
                "actor_required_entitlements": PWActorLimits.requiredEntitlements,
                "actor_entitlement_key": PWActorLimits.entitlementKeyBytes,
                "actor_termination_wait": PWActorLimits.terminationMs,
                "authority_setup_trailer": PWAuthoritySetupLayout.bytes,
                "authority_setup_cells": PWAuthoritySetupLayout.capacity,
                "equipment_entitlement_bytes": PWEquipmentLimits.entitlementBytes,
                "equipment_inventory_bytes": PWEquipmentLimits.inventoryBytes,
                "equipment_diagnostic_bytes": PWEquipmentLimits.diagnosticBytes,
                "equipment_metadata_bytes": PWEquipmentLimits.metadataBytes,
                "equipment_signing_text": signingTextBytes,
                "equipment_path": equipmentPathBytes,
                "equipment_error_domain": equipmentDomainBytes,
                "authority_cleanup_name": cleanupNameBytes,
                "equipment_static_bindings": PWEquipmentLimits.staticBindings,
                "equipment_live_inspections": PWEquipmentLimits.liveInspections,
                "equipment_entitlement_records": PWEquipmentLimits.entitlementRecords,
                "authority_slot_bytes": PWAuthorityLayout.slotBytes,
                "phase_id": requestLabelMaxBytes,
                "phase_publications": PWShmLayout.maxPhases * PWShmLayout.phaseBytes,
                "phase_collection_wait": phaseCollectionBudgetMs,
                "extension_reference": PWExtensionLimits.referenceBytes,
                "extension_token_storage": PWExtensionLimits.tokenBytes,
                "extension_token_payload": PWExtensionLimits.tokenBytes - 1,
                "fresh_read_bytes": PWExtensionLimits.freshReadBytes,
                "validator_reply_frame": ValidatorReplyLimits.frameBytes,
                "validator_records_per_query": ValidatorReplyLimits.recordsPerProbe,
                "validator_reply_bytes_per_query": ValidatorReplyLimits.frameBytes * ValidatorReplyLimits.recordsPerProbe,
                "validator_reply_step_id": ValidatorReplyLimits.stringBytes["step_id"]!,
                "validator_reply_operation": ValidatorReplyLimits.stringBytes["operation"]!,
                "validator_reply_filter_type": ValidatorReplyLimits.stringBytes["filter_type"]!,
                "validator_reply_filter_value": ValidatorReplyLimits.stringBytes["filter_value"]!,
                "validator_reply_outcome": ValidatorReplyLimits.stringBytes["outcome"]!,
                "validator_reply_error": ValidatorReplyLimits.stringBytes["error"]!,
                "policy_parameters": PWShmLayout.maxParams,
                "step_id": PWShmLayout.stepIdMax - 1,
                "attempt_target": PWShmLayout.targetMax - 1,
                "exec_arguments": PWShmLayout.maxArgv - 1,
                "exec_argument": PWShmLayout.argvBytes - 1,
                "parameter_key": PWShmLayout.paramKeyMax - 1,
                "parameter_value": PWShmLayout.paramValueMax - 1,
                "query_operation": sandboxCheckOperationMaxBytes,
                "query_filter_value": sandboxCheckFilterValueMaxBytes,
                "specimen_id": specimenIdMaxBytes,
                "request_label": requestLabelMaxBytes,
                "test_override_path": testOverridePathMaxBytes,
                "probe_plan_label": probePlanLabelMaxBytes,
                "host_exit_delay": hostExitDelayMs,
                "worker_policy_transfer": worker.policyTransferTimeoutMs,
                "worker_ready_wait": worker.readyByteTimeoutMs,
                "worker_sentinel_wait": worker.sentinelTimeoutMs,
                "worker_timeout_override_floor": timeoutMsForCWorker(override: 0),
                "validator_collection_override_floor": collectionBudgetMs(override: 0, maximum: phaseCollectionBudgetMs),
                "worker_fixture_delay": fixtureDelay,
                "worker_exit_grace": worker.exitGraceMs,
                "validator_io_wait": validator.verdictReadTimeoutMs,
                "worker_proceed_wait": proceedWait,
                "exec_attempt_budget": attemptBudget,
                "validator_release_margin": validatorReleaseMarginMs,
                "validator_io_override_floor": timeoutMsForValidator(override: 0),
                "validator_exit_grace": validator.exitGraceMs,
                "client_rpc_wait": PWRunnerWire.defaultClientTimeoutMs,
                "validator_fault_context": fault.retained_bytes,
                "exec_stream": PWShmLayout.childOutputBytes - 1,
                "worker_diagnostic": PWShmLayout.diagnosticBytes - 1,
                "compiled_profile": PWShmLayout.captureBytes,
                "observed_path": PWShmLayout.observedPathMax - 1,
                "attempt_error": PWShmLayout.errorMax - 1,
            ]
            try expectTrue(observed["worker_proceed_wait"]! > validator.verdictReadTimeoutMs
                + validator.exitGraceMs + validatorReleaseMarginMs)
            try expectTrue(PWRunnerPhase.maximumCount <= PWShmLayout.maxPhases)
            try expectEqual(PWActorLimits.phases, PWShmLayout.maxPhases)
            try expectEqual(PWExtensionLimits.tokenBytes, PWAuthorityLayout.tokenBytes)
            try expectEqual(PWShmLayout.extTargetBytes - 1, PWActorLimits.targetBytes)
            try expectEqual(PWExtensionLimits.freshReadBytes, PWShmLayout.freshReadBytes)
            try expectEqual(timeoutMsForValidator(override: nil), validator.verdictReadTimeoutMs)
            for maximum in [phaseCollectionBudgetMs, PWActorLimits.collectionMs] {
                for input in [Int.min, -1, 0, 1] {
                    try expectEqual(collectionBudgetMs(override: input, maximum: maximum), 1)
                }
                try expectEqual(collectionBudgetMs(override: 2, maximum: maximum), 2)
                try expectEqual(collectionBudgetMs(override: maximum - 1, maximum: maximum), maximum - 1)
                try expectEqual(collectionBudgetMs(override: maximum, maximum: maximum), maximum)
                try expectEqual(collectionBudgetMs(override: maximum + 1, maximum: maximum), maximum)
                try expectEqual(collectionBudgetMs(override: Int.max, maximum: maximum), maximum)
                try expectEqual(collectionBudgetMs(override: nil, maximum: maximum), maximum)
            }
            try expectEqual(timeoutMsForValidator(override: -100), 50)
            try expectEqual(timeoutMsForValidator(override: 70), 70)
            try expectEqual(timeoutMsForValidator(override: Int.max), Int.max, "fault-injection override has no ceiling")
            let owned = manifest.limits.filter { row in
                row.checks.contains { $0.kind == "value" && $0.path.hasSuffix("/LimitsContractTests.swift") }
            }
            try expectEqual(Set(owned.map { $0.id }), Set(observed.keys), "every declared Swift owner is exercised")
            for row in owned {
                try expectEqual(observed[row.id], Optional(row.value), row.id)
            }
            try expectEqual(timeoutMsForCWorker(override: nil), worker.sentinelTimeoutMs,
                            "orchestrator and driver defaults agree")
            for value in [-1, 0, 49, 50] {
                try expectEqual(timeoutMsForCWorker(override: value), 50,
                                "ordinary worker override retains its minimum")
            }
            try expectEqual(timeoutMsForCWorker(override: 51), 51)
            try expectEqual(timeoutMsForCWorker(override: Int.max), Int.max,
                            "ordinary worker override has no ceiling")
            // Configuration allowance only: the C active-time budget and host polling
            // budget have different epochs and accounting, not one shared clock.
            try expectEqual(worker.sentinelTimeoutMs - attemptBudget, 5_000,
                            "exec attempt budget leaves the publication margin inside the worker window")
        }
        tk.run("equipment text boundaries use UTF-8 bytes at their own admission predicates") {
            let exactSigning = String(repeating: "é", count: 127) + "x"
            for field in ["identifier", "team_id"] {
                try expectTrue(try manifestAcceptsSigningText(exactSigning, field: field))
                try expectFalse(try manifestAcceptsSigningText(exactSigning + "x", field: field))
            }
            try expectFalse(equipmentTextProblems(identifier: exactSigning).contains("equipment signature identifier bound"))
            try expectTrue(equipmentTextProblems(identifier: exactSigning + "x").contains("equipment signature identifier bound"))
            try expectFalse(equipmentTextProblems(team: exactSigning).contains("equipment signature team bound"))
            try expectTrue(equipmentTextProblems(team: exactSigning + "x").contains("equipment signature team bound"))
            let exactPath = "/" + String(repeating: "é", count: 511)
            try expectEqual(exactPath.utf8.count, 1023)
            try expectFalse(equipmentTextProblems(path: exactPath).contains("equipment binding path"))
            try expectTrue(equipmentTextProblems(path: exactPath + "x").contains("equipment binding path"))
            let exactName = "/" + String(repeating: "é", count: 15)
            try expectEqual(exactName.utf8.count, 31)
            try expectEqual(cleanupReferenceProblems(name: exactName), [])
            try expectTrue(cleanupReferenceProblems(name: exactName + "x").contains("authority_cleanup_reference"))
            let exactDomain = String(repeating: "é", count: 64)
            for domain in [exactDomain, exactDomain + "x"] {
                let observed = ActorEquipmentSystem.error("worker_path", NSError(domain: domain, code: 17))
                try expectEqual(observed.domain, exactDomain)
                try expectEqual(observed.code, 17)
            }
            let overlong = PWRunnerEquipmentError(operation: "worker_path", domain: exactDomain + "x", code: 17)
            let inventory = PWRunnerEquipmentInventory(path: "/constructed", status: "refused", error: overlong)
            try expectTrue(pwRunnerEquipmentProblems(inventory: inventory, bindings: [], entitlements: [],
                actors: [], actorIDs: [], actorPIDs: []).contains("equipment error domain bound"))
        }
        tk.run("request failure paths retain whole locations or withhold them") {
            // Literal behavioral oracles remain independent of limits.json.
            let eight = Array(repeating: "x", count: 8)
            try expectEqual(PWRunnerRequestFailure(code: "invalid_request", path: eight).path, Optional(eight))
            try expectTrue(PWRunnerRequestFailure(code: "invalid_request", path: eight + ["x"]).path == nil)
            for component in [String(repeating: "x", count: 63), String(repeating: "é", count: 31) + "x"] {
                let path = ["policy", "params", component]
                try expectEqual(component.utf8.count, 63)
                try expectEqual(PWRunnerRequestFailure(code: "invalid_request", path: path).path, Optional(path))
                try expectTrue(PWRunnerRequestFailure(code: "invalid_request", path: ["policy", "params", component + "x"]).path == nil)
            }
            try expectTrue(PWRunnerRequestFailure(code: "invalid_request", path: nil).path == nil)
        }
        tk.run("rejected-frame context boundary retains raw prefix and loss metadata") {
            // Independent of limits.json: changing the inventory cannot change this oracle.
            for count in [255, 256, 257] {
                let decoded = decodeValidatorFrames(Data(repeating: 0xff, count: count))
                guard let fault = decoded.fault else { throw TestFailure(message: "invalid frame accepted") }
                try expectTrue(decoded.verdicts.isEmpty)
                try expectEqual(fault.frame_bytes, count)
                try expectEqual(fault.retained_bytes, min(count, 256))
                try expectEqual(fault.context_truncated, count > 256)
                try expectEqual(fault.context, Data(repeating: 0xff, count: min(count, 256)))
            }
        }
    }
}

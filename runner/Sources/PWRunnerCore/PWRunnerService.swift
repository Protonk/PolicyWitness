import Foundation
import Darwin
import Security

// PWRunnerService is the unsandboxed half of the runner: the XPC service
// host that authenticates the caller, validates the request, drives the
// C worker plus batch validator through CWorkerOrchestrator, and
// translates their joined output into the public PWRunnerRunResult
// shape before replying via XPC.
//
// The companion files are CWorker.swift (host-side launcher for
// pw-probe-runner), ValidatorClient.swift (host-side launcher for
// sb_api_validator --batch), and CWorkerOrchestrator.swift (joins
// their outputs). Anything that must observe the applied sandbox
// belongs in those sandboxed children, not here.
//
// Host invariance rule: the XPC host remains unsandboxed and does not link,
// load or call libsandbox. The worker applies the specimen policy to itself
// and the validator queries it; the host only reads what they publish, so
// the XPC reply path survives a (deny default) specimen. The live
// runner_apply_isolation_v3/deny_default_v3_worker_reply case covers the
// host/worker split end to end; runner_c_worker_harness/bare_deny_default
// covers the worker alone. The source_drift suite rejects native sandbox
// API use under runner/Sources, and preflight rejects a shipped host
// executable with an undefined _sandbox_* symbol.

// Delay scheduled by the terminal request owner so its XPC reply can flush.
let hostExitDelayMs = 50

private func bundleString(_ key: String) -> String? {
    Bundle.main.object(forInfoDictionaryKey: key) as? String
}

private struct PWRunnerSigningInfo {
    let teamID: String?
    let identifier: String?
}

private func signingInfo(for code: SecStaticCode) -> PWRunnerSigningInfo {
    var infoRef: CFDictionary?
    let flags = SecCSFlags(rawValue: kSecCSSigningInformation)
    let status = SecCodeCopySigningInformation(code, flags, &infoRef)
    guard status == errSecSuccess, let info = infoRef as? [String: Any] else {
        return PWRunnerSigningInfo(teamID: nil, identifier: nil)
    }
    let teamID = info[kSecCodeInfoTeamIdentifier as String] as? String
    let identifier = info[kSecCodeInfoIdentifier as String] as? String
    return PWRunnerSigningInfo(teamID: teamID, identifier: identifier)
}

private func staticCode(from code: SecCode) -> SecStaticCode? {
    var staticCode: SecStaticCode?
    guard SecCodeCopyStaticCode(code, [], &staticCode) == errSecSuccess else {
        return nil
    }
    return staticCode
}

private func requireSignedCaller() -> Bool {
    (Bundle.main.object(forInfoDictionaryKey: "PWRunnerRequireSignedCaller") as? Bool) ?? false
}

private func allowedCallerIdentifiers() -> Set<String>? {
    guard let list = Bundle.main.object(forInfoDictionaryKey: "PWRunnerAllowedIdentifiers") as? [String] else {
        return nil
    }
    let trimmed = list
        .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
        .filter { !$0.isEmpty }
    return trimmed.isEmpty ? nil : Set(trimmed)
}

private func authorizedCaller(_ connection: NSXPCConnection) -> Bool {
    if !requireSignedCaller() {
        return true
    }

    let pid = connection.processIdentifier
    let attrs = [kSecGuestAttributePid as String: NSNumber(value: pid)] as CFDictionary

    var callerCode: SecCode?
    guard SecCodeCopyGuestWithAttributes(nil, attrs, [], &callerCode) == errSecSuccess,
          let caller = callerCode,
          let callerStatic = staticCode(from: caller) else {
        return false
    }

    var selfCode: SecCode?
    guard SecCodeCopySelf([], &selfCode) == errSecSuccess,
          let selfCode,
          let selfStatic = staticCode(from: selfCode) else {
        return false
    }

    let callerInfo = signingInfo(for: callerStatic)
    let selfInfo = signingInfo(for: selfStatic)
    guard let callerTeam = callerInfo.teamID,
          let selfTeam = selfInfo.teamID,
          callerTeam == selfTeam else {
        return false
    }

    if let allowlist = allowedCallerIdentifiers() {
        guard let identifier = callerInfo.identifier,
              allowlist.contains(identifier) else {
            return false
        }
    }

    return true
}

/// The transport boundary admits typed evidence before choosing a writer.
/// The closures are internal failure controls; requests cannot select them.
func pwRunnerPorcelainReplyData(_ result: PWRunnerRunResult,
    encode: (PWRunnerRunResult) throws -> Data = { try pwPorcelainEncode($0) },
    minimal: (PWRunnerRunResult, String) throws -> Data = { result, diagnostic in
        try pwPorcelainEncode(PWMinimalPorcelainReply(original: result, diagnostic: diagnostic))
    }) -> Data {
    pwRunnerReportData(result, encode: encode, minimal: minimal)
}

private func pwRunnerReportData(_ result: PWRunnerRunResult,
    encode: (PWRunnerRunResult) throws -> Data,
    minimal: (PWRunnerRunResult, String) throws -> Data) -> Data {
    do {
        try result.validateForReporting()
        return try encode(result)
    } catch {
        let diagnostic: String
        if let failure = error as? PWRunnerReportingValidationError {
            diagnostic = failure.message
        } else {
            diagnostic = String(describing: error)
        }
        var failed = result
        failed.schema_version = PWContract.responseSchema
        failed.rc = 1
        failed.normalized_outcome = NormalizedOutcome.runnerReportingFailed
        failed.error = "runner host could not encode its result: \(diagnostic)"
        failed.reporting_failure = PWRunnerReportingFailure(diagnostic: diagnostic,
            original_rc: result.rc, original_normalized_outcome: result.normalized_outcome,
            original_error: result.error, evidence_retained: true)
        for index in failed.steps.indices { failed.steps[index].comparison = nil }
        do {
            try failed.validateForReporting()
            return try encode(failed)
        } catch {
            let finalDiagnostic = "\(diagnostic); evidence-preserving encoding also failed: \(error)"
            // If even the independent scalar report fails, an empty receipt is
            // explicitly undecodable by the client/controller. It cannot claim
            // a successful result or evidence retention. Keep that outer failure
            // observable instead of crashing or trying the failed rich writer again.
            return (try? minimal(result, finalDiagnostic)) ?? Data()
        }
    }
}

/// These backstops deliberately avoid the generated full-result writers and all
/// rich evidence. The schema still owns their record identities and field tags.
private struct PWMinimalPorcelainFailure: PWPorcelainWritable {
    static var porcelainRecordID: UInt16 { PWRunnerReportingFailure.porcelainRecordID }
    let original: PWRunnerRunResult
    let diagnostic: String
    func porcelainWrite() throws -> Data {
        typealias Tag = PWRunnerReportingFailure.PorcelainTag
        var w = PWPorcelainRecordWriter(Self.porcelainRecordID)
        try w.field(Tag.origin, "runner_host")
        try w.field(Tag.diagnostic, diagnostic)
        try w.field(Tag.original_rc, original.rc)
        try w.field(Tag.original_normalized_outcome, original.normalized_outcome)
        try w.field(Tag.original_error, original.error)
        try w.field(Tag.evidence_retained, false)
        return try w.finish()
    }
}

private struct PWMinimalPorcelainReply: PWPorcelainWritable {
    static var porcelainRecordID: UInt16 { PWRunnerRunResult.porcelainRecordID }
    let original: PWRunnerRunResult
    let diagnostic: String
    func porcelainWrite() throws -> Data {
        typealias Tag = PWRunnerRunResult.PorcelainTag
        var w = PWPorcelainRecordWriter(Self.porcelainRecordID)
        try w.field(Tag.schema_version, PWContract.responseSchema)
        try w.field(Tag.specimen_id, original.specimen_id)
        try w.field(Tag.run_kind, original.run_kind)
        try w.field(Tag.rc, 1)
        try w.field(Tag.normalized_outcome, NormalizedOutcome.runnerReportingFailed)
        try w.field(Tag.error, diagnostic)
        try w.field(Tag.pid, original.pid)
        try w.field(Tag.bundle_id, original.bundle_id)
        try w.field(Tag.policy_format, original.policy_format)
        try w.field(Tag.policy_sha256, original.policy_sha256)
        try w.field(Tag.steps, [PWRunnerStepResult]())
        try w.field(Tag.phases, [PWRunnerPhaseResult]())
        try w.field(Tag.reporting_failure, PWMinimalPorcelainFailure(original: original, diagnostic: diagnostic))
        return try w.finish()
    }
}

/// A decoder error can contain an unbounded dictionary key in its coding path.
func requestDecodeFailure(_ error: Error) -> PWRunnerRequestFailure {
    let code: String
    let path: [String]
    switch error {
    case let failure as PWRunnerRequestFailure: return failure
    case RequestContractError.unsupportedSchema:
        return PWRunnerRequestFailure(code: "unsupported_schema", path: ["schema_version"],
            expected_schema: PWContract.requestSchema)
    case RequestContractError.unresolvedAugments(let keys):
        let location = keys.isEmpty ? ["policy"] : keys.map { $0.intValue.map(String.init) ?? $0.stringValue }
        return PWRunnerRequestFailure(code: "unresolved_augments", path: location + ["augments"])
    case RequestContractError.unknownField(let keys):
        code = "unknown_field"; path = keys.map { $0.intValue.map(String.init) ?? $0.stringValue }
    case DecodingError.typeMismatch(_, let c): code = "type_mismatch"; path = c.codingPath.map { $0.intValue.map(String.init) ?? $0.stringValue }
    case DecodingError.valueNotFound(_, let c): code = "missing_value"; path = c.codingPath.map { $0.intValue.map(String.init) ?? $0.stringValue }
    case DecodingError.keyNotFound(let key, let c): code = "missing_field"; path = (c.codingPath + [key]).map { $0.intValue.map(String.init) ?? $0.stringValue }
    case DecodingError.dataCorrupted(let c):
        code = c.codingPath.isEmpty ? "invalid_json" : "invalid_value"; path = c.codingPath.map { $0.intValue.map(String.init) ?? $0.stringValue }
    default: return PWRunnerRequestFailure(code: "invalid_json", path: nil)
    }
    return PWRunnerRequestFailure(code: code, path: path,
        expected_schema: path == ["schema_version"] ? PWContract.requestSchema : nil)
}

/// Report the category and bounded path, never arbitrary decoder prose/input.
func requestDecodeDiagnostic(_ error: Error) -> String {
    let kind: String
    let path: [CodingKey]
    switch error {
    case let failure as PWRunnerRequestFailure: return failure.description
    case RequestContractError.unsupportedSchema(let version):
        return "request decode failed: unsupported request schema \(version) (expected \(PWContract.requestSchema))"
    case RequestContractError.unresolvedAugments(let keys):
        let location = keys.isEmpty ? "policy" : keys.map { $0.intValue.map { "[\($0)]" } ?? $0.stringValue }.joined(separator: ".")
        return "request decode failed: \(location).augments must be resolved by the controller before XPC delivery"
    case RequestContractError.unknownField(let keys): kind = "unknown_field"; path = keys
    case DecodingError.typeMismatch(_, let context): kind = "type_mismatch"; path = context.codingPath
    case DecodingError.valueNotFound(_, let context): kind = "value_missing"; path = context.codingPath
    case DecodingError.keyNotFound(let key, let context): kind = "key_missing"; path = context.codingPath + [key]
    case DecodingError.dataCorrupted(let context): kind = "data_corrupted"; path = context.codingPath
    default: return "request decode failed"
    }
    let rule = AdmissionStringRule(field: "coding_path", maximum: 63)
    var parts = path.prefix(8).map { key in
        key.intValue.map { "[\($0)]" } ?? rule.safeEcho(key.stringValue) ?? "<unreported_key>"
    }
    if path.count > 8 { parts.append("<remaining_path_omitted>") }
    return "request decode failed: \(kind) at \(parts.isEmpty ? "<root>" : parts.joined(separator: "."))"
}

final class PWRunnerService: NSObject, PWRunnerProtocol {
    private let admission: PWRunnerAdmission
    private let connectionID = PWRunnerAdmission.Connection()
    private let scheduleExit: () -> Void
    private let scheduleExpiry: (Int, @escaping () -> Void) -> Void
    private let admit: (PWRunnerRunSpec) -> SpecimenAdmission
    private let orchestrate: (AdmittedSpecimen, Data, String?, String, String) -> PWRunnerRunResult
    private let report: (PWRunnerRunResult) -> Data

    // These boundaries let tests observe entry and retirement without exiting
    // the test host. No request selects them; test orchestration still executes
    // the real driver against a controlled, nonexistent executable.
    init(admission: PWRunnerAdmission,
         scheduleExit: @escaping () -> Void = {
             DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(hostExitDelayMs)) { exit(0) }
         },
         scheduleExpiry: @escaping (Int, @escaping () -> Void) -> Void = { delay, action in
             DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(delay), execute: action)
         },
         admit: @escaping (PWRunnerRunSpec) -> SpecimenAdmission = admitSpecimen,
         report: @escaping (PWRunnerRunResult) -> Data = { pwRunnerPorcelainReplyData($0) },
         orchestrate: @escaping (AdmittedSpecimen, Data, String?, String, String) -> PWRunnerRunResult = {
             CWorkerOrchestrator.run(admitted: $0, policyHash: $1, bundleId: $2,
                 workerExecutablePath: $3, validatorExecutablePath: $4)
         }) {
        self.admission = admission
        self.scheduleExit = scheduleExit
        self.scheduleExpiry = scheduleExpiry
        self.admit = admit
        self.report = report
        self.orchestrate = orchestrate
        super.init()
    }

    private func control(_ status: String, attempt: String? = nil, token: String? = nil,
                         lease: Int? = nil, reason: String? = nil) -> Data {
        // This fixed, bounded representation has no specimen-derived strings.
        try! pwRunnerEncodeJSON(PWRunnerControlReply(status: status, attempt_id: attempt,
            host_instance: admission.instance, reservation_id: token, lease_ms: lease, reason: reason))
    }

    func reserveRunner(_ request: Data, withReply reply: @escaping (Data) -> Void) {
        guard request.count <= PWRunnerTransportLimits.controlBytes else {
            reply(control("invalid_request", reason: "control_too_large")); return
        }
        struct Version: Decodable { var protocol_version: Int }
        guard let version = try? pwRunnerDecodeJSON(Version.self, from: request) else {
            reply(control("invalid_request", reason: "malformed_control")); return
        }
        guard version.protocol_version == PWContract.runnerProtocol else {
            reply(control("unsupported_protocol", reason: "unsupported_protocol")); return
        }
        guard let parsed = try? pwRunnerDecodeJSON(PWRunnerReservationRequest.self, from: request),
              parsed.attempt_id.utf8.count == 36, UUID(uuidString: parsed.attempt_id) != nil, parsed.lease_ms > 0 else {
            reply(control("invalid_request", reason: "malformed_control")); return
        }
        let decision = admission.reserve(owner: connectionID, leaseMs: parsed.lease_ms)
        if decision.retire { scheduleExit() }
        guard let held = decision.reservation else {
            reply(control(decision.reason == "clock_error" ? "invalid_request" : "occupied",
                attempt: parsed.attempt_id, reason: decision.reason == "clock_error" ? "clock_error" : nil))
            return
        }
        let state = admission, exit = scheduleExit, schedule = scheduleExpiry
        func checkExpiry() {
            if state.expire(owner: held.owner, token: held.token) { exit(); return }
            if let delay = state.expiryDelay(owner: held.owner, token: held.token) {
                schedule(delay, checkExpiry)
            }
        }
        // Short ticks recheck continuous time after system sleep. An early
        // callback rearms only while the same unused reservation still exists.
        schedule(min(100, held.leaseMs), checkExpiry)
        reply(control("granted", attempt: parsed.attempt_id, token: held.token, lease: held.leaseMs))
    }

    func connectionInvalidated() {
        if admission.disconnected(owner: connectionID) { scheduleExit() }
    }

    func runReservedSpecimen(_ request: Data, reservation: String,
                             withReply reply: @escaping (Bool, Data) -> Void) {
        let decision = admission.submit(owner: connectionID, token: reservation)
        guard decision.accepted else {
            reply(false, control("reservation_refused", reason: decision.reason))
            if decision.retire { scheduleExit() }
            return
        }
        func replyAndExit(_ result: PWRunnerRunResult) {
            let data = report(result)
            let retire = admission.complete(owner: connectionID, token: reservation)
            reply(true, data)
            // Allow the XPC reply to flush before exiting the process.
            if retire { scheduleExit() }
        }

        let parsed: PWRunnerRunSpec
        do {
            parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: request)
        } catch {
            let resp = PWRunnerRunResult(
                specimen_id: "<decode_failed>",
                run_kind: nil,
                rc: 1,
                normalized_outcome: NormalizedOutcome.badRequest,
                error: requestDecodeDiagnostic(error),
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: "unknown",
                steps: [],
                request_failure: requestDecodeFailure(error)
            )
            replyAndExit(resp)
            return
        }

        let admitted: AdmittedSpecimen
        switch admit(parsed) {
        case .accepted(let value): admitted = value
        case .capacity(let refused):
            replyAndExit(admissionRefusalReply(parsed: parsed, refused: refused, bundleId: bundleString("CFBundleIdentifier")))
            return
        case .refused(let failure):
            replyAndExit(requestRefusalReply(parsed: parsed, failure: failure, bundleId: bundleString("CFBundleIdentifier")))
            return
        }

        // The actor form hashes each apply actor's policy in its own driver.
        let policyHash: Data
        do {
            if parsed.isActorForm { policyHash = Data() }
            else {
                guard let policy = parsed.policy else { throw PolicyHashError.missingField("policy") }
                policyHash = try computePolicyHash(policy)
            }
        } catch {
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: 1,
                normalized_outcome: NormalizedOutcome.badPolicy,
                error: "\(error)",
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy?.format,
                steps: []
            )
            replyAndExit(resp)
            return
        }

        let workerPath = parsed._test_overrides?.worker_executable_path
            ?? CWorkerOrchestrator.defaultWorkerExecutablePath()
        let validatorPath = parsed._test_overrides?.validator_executable_path
            ?? CWorkerOrchestrator.defaultValidatorExecutablePath()
        let cResp = orchestrate(admitted, policyHash, bundleString("CFBundleIdentifier"), workerPath, validatorPath)
        // path_diagnostics enrichment is host-side; the host's
        // realpath(3) is not blocked by the worker's (deny default)
        // policy.
        var enrichedResp = cResp
        enrichedResp.steps = enrichPathDiagnostics(steps: cResp.steps)
        replyAndExit(enrichedResp)
    }
}

// path_diagnostics is computed here in the unsandboxed host rather
// than in the worker. The host's realpath(3) is not blocked by a
// worker (deny default) policy, so realpath_resolved is reliably
// populated. The fallback chain (wellKnownSymlinksResolved when
// realpath is unavailable) is retained for hosts that for any
// reason can't stat the path.
//
// path_diagnostics appears on path-filter sandbox_check results and,
// as attempt.path_diagnostics, on file and exec attempts.
func enrichPathDiagnostics(steps: [PWRunnerStepResult]) -> [PWRunnerStepResult] {
    return steps.map { step in
        var updated = step
        // The attempt target gets the same later host observation: the
        // leaf-followed realpath and the parent-resolved literal-leaf form.
        // Neither reclassifies the attempt or its comparison.
        if let kind = step.attempt.requested_kind,
           kind == PWRunnerWire.attemptKindFile || kind == PWRunnerWire.attemptKindExec,
           let target = step.attempt.requested_path, !target.isEmpty {
            updated.attempt.path_diagnostics = PWRunnerAttemptPathDiagnostics(
                input: target,
                realpath_resolved: canonicalizePath(target).resolved,
                parent_realpath_resolved: parentRealpathResolved(target),
                observer: "runner_host",
                stage: "after_orchestration"
            )
        }
        guard step.sandbox_check.filter_kind == PWRunnerWire.sandboxFilterPath,
              let value = step.sandbox_check.filter_value,
              !value.isEmpty
        else {
            return updated
        }
        let canonical = canonicalizePath(value)
        let basis = canonical.resolved ?? wellKnownSymlinksResolved(value)
        updated.sandbox_check.path_diagnostics = PWRunnerPathDiagnostics(
            input: value,
            realpath_resolved: canonical.resolved,
            firmlink_resolved: firmlinkResolved(basis),
            observer: "runner_host",
            stage: "after_orchestration"
        )
        // This later host observation never touches the comparison record:
        // a null realpath_resolved on a query the planner did not exclude is
        // the reader's evidence that the host could not resolve the submitted
        // path after the run.
        return updated
    }
}

final class PWRunnerSessionDelegate: NSObject, NSXPCListenerDelegate {
    private let admission = PWRunnerAdmission()
    func listener(_ listener: NSXPCListener, shouldAcceptNewConnection newConnection: NSXPCConnection) -> Bool {
        if !authorizedCaller(newConnection) {
            return false
        }
        let exported = PWRunnerService(admission: admission)
        newConnection.exportedInterface = NSXPCInterface(with: PWRunnerProtocol.self)
        newConnection.exportedObject = exported
        newConnection.invalidationHandler = { exported.connectionInvalidated() }
        newConnection.interruptionHandler = { exported.connectionInvalidated() }
        newConnection.resume()
        return true
    }
}

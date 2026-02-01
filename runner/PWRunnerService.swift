import Foundation
import Darwin
import Security

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

// PWRunnerService executes one specimen per process. The flow is intentionally
// linear and explicit:
// 1) Decode and validate the run spec.
// 2) Run pre-sandbox instrumentation (if requested).
// 3) Load libsandbox and apply the policy.
// 4) Run post-sandbox instrumentation (if requested).
// 5) Execute probe steps and reply with a JSON result, then exit.
public final class PWRunnerService: NSObject, PWRunnerProtocol {
    private var didRun = false

    public func runSpecimen(_ request: Data, withReply reply: @escaping (Data) -> Void) {
        func replyAndExit(_ result: PWRunnerRunResult) {
            reply((try? pwRunnerEncodeJSON(result)) ?? Data("{}".utf8))
            // Allow the XPC reply to flush before exiting the process.
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(50)) { exit(0) }
        }

        if didRun {
            let resp = PWRunnerRunResult(
                specimen_id: "<unknown>",
                run_kind: nil,
                rc: 1,
                normalized_outcome: "already_ran",
                error: "runner instance only supports one RunSpecimen request",
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: "unknown",
                steps: []
            )
            replyAndExit(resp)
            return
        }
        didRun = true

        installDenySignalHandler()

        let parsed: PWRunnerRunSpec
        do {
            parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: request)
        } catch {
            let resp = PWRunnerRunResult(
                specimen_id: "<decode_failed>",
                run_kind: nil,
                rc: 1,
                normalized_outcome: "bad_request",
                error: "request decode failed: \(error)",
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: "unknown",
                steps: []
            )
            replyAndExit(resp)
            return
        }

        do {
            try validateSandboxChecks(parsed.probe_plan)
        } catch {
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: 1,
                normalized_outcome: "bad_request",
                error: String(describing: error),
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                steps: []
            )
            replyAndExit(resp)
            return
        }

        var instrumentationState = InstrumentationState(spec: parsed.instrumentation)
        instrumentationState?.runPhase(PWRunnerWire.instrumentationPhasePre)

        let sandboxLib: SandboxLib
        switch SandboxLib.load() {
        case .success(let lib):
            sandboxLib = lib
        case .failure(let err):
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: 1,
                normalized_outcome: "libsandbox_unavailable",
                error: err.description,
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                steps: [],
                instrumentation: instrumentationState?.finalize(reason: "runner exited before sandbox setup")
            )
            replyAndExit(resp)
            return
        }

        let policyHash: String
        do {
            policyHash = try computePolicyHash(parsed.policy)
        } catch {
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: 1,
                normalized_outcome: "bad_policy",
                error: "\(error)",
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                steps: [],
                instrumentation: instrumentationState?.finalize(reason: "runner exited before sandbox apply")
            )
            replyAndExit(resp)
            return
        }

        let applyResult = applySandboxPolicy(parsed.policy, sandboxLib: sandboxLib)
        if case .failure(let err) = applyResult {
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: 1,
                normalized_outcome: "sandbox_apply_failed",
                error: err.description,
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                policy_sha256: policyHash,
                steps: [],
                instrumentation: instrumentationState?.finalize(reason: "runner exited before sandbox apply")
            )
            replyAndExit(resp)
            return
        }

        instrumentationState?.runPhase(PWRunnerWire.instrumentationPhasePost)

        let sandboxedAfterApply: Bool? = currentProcessIsSandboxed()

        var stepResults: [PWRunnerStepResult] = []
        for step in parsed.probe_plan {
            let beforeSig = denySignalCount()
            let sb = runSandboxCheck(step.sandbox_check)
            let attempt = runAttempt(step.attempt)
            let afterSig = denySignalCount()
            let sig = PWRunnerSignalResult(signal: "SIGUSR1", count_before: beforeSig, count_after: afterSig)
            stepResults.append(
                PWRunnerStepResult(
                    step_id: step.step_id,
                    sandbox_check: sb,
                    attempt: attempt,
                    deny_signal: sig
                )
            )
        }

        let totalSig = PWRunnerSignalResult(signal: "SIGUSR1", count_before: 0, count_after: denySignalCount())
        let resp = PWRunnerRunResult(
            specimen_id: parsed.specimen_id,
            run_kind: parsed.run_kind,
            rc: 0,
            normalized_outcome: "ok",
            error: nil,
            pid: Int(getpid()),
            bundle_id: bundleString("CFBundleIdentifier"),
            policy_format: parsed.policy.format,
            policy_sha256: policyHash,
            sandboxed_after_apply: sandboxedAfterApply,
            deny_signal_total: totalSig,
            steps: stepResults,
            instrumentation: instrumentationState?.finalize(reason: nil)
        )
        replyAndExit(resp)
    }
}

public final class PWRunnerSessionDelegate: NSObject, NSXPCListenerDelegate {
    public func listener(_ listener: NSXPCListener, shouldAcceptNewConnection newConnection: NSXPCConnection) -> Bool {
        if !authorizedCaller(newConnection) {
            return false
        }
        let exported = PWRunnerService()
        newConnection.exportedInterface = NSXPCInterface(with: PWRunnerProtocol.self)
        newConnection.exportedObject = exported
        newConnection.resume()
        return true
    }
}

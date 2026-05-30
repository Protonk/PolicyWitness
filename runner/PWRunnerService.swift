import Foundation
import Darwin
import Security

// PWRunnerService is the unsandboxed half of the runner: the XPC service
// host that authenticates the caller, validates the request, spawns a
// short-lived worker through WorkerProcess, and translates the worker's
// report into the public PWRunnerRunResult shape before replying via XPC.
//
// The companion file is WorkerEntry.swift, which is the sandboxed half
// — it runs inside the worker process, applies the policy to itself,
// and executes the probe plan. Anything that must observe the applied
// sandbox belongs there, not here.
//
// What does NOT belong in this file: calls to applySandboxPolicy,
// libsandbox state that survives past the load check, runSandboxCheck
// or runAttempt. The host must stay invariant under the policy under
// test so the XPC reply path is never disrupted by a (deny default)
// specimen.

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
                normalized_outcome: NormalizedOutcome.alreadyRan,
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

        let parsed: PWRunnerRunSpec
        do {
            parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: request)
        } catch {
            let resp = PWRunnerRunResult(
                specimen_id: "<decode_failed>",
                run_kind: nil,
                rc: 1,
                normalized_outcome: NormalizedOutcome.badRequest,
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
                normalized_outcome: NormalizedOutcome.badRequest,
                error: String(describing: error),
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                steps: []
            )
            replyAndExit(resp)
            return
        }

        let libsandboxPath = parsed._test_overrides?.libsandbox_path ?? SandboxLib.defaultLibraryPath
        switch SandboxLib.load(path: libsandboxPath) {
        case .success:
            break
        case .failure(let err):
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: 1,
                normalized_outcome: NormalizedOutcome.libsandboxUnavailable,
                error: err.description,
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                steps: [],
                test_overrides: parsed._test_overrides
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
                normalized_outcome: NormalizedOutcome.badPolicy,
                error: "\(error)",
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                steps: []
            )
            replyAndExit(resp)
            return
        }

        // ---- C-worker code path (gated by _test_overrides.use_c_worker).
        // Per RUNNER-RESHAPE-PLAN Step 6.8a. Default-false during the
        // transition: production traffic continues through the Swift
        // worker below. Step 6.8b flips the default once the gated
        // path has been broadly exercised.
        if parsed._test_overrides?.use_c_worker == true {
            let workerPath = parsed._test_overrides?.worker_executable_path
                ?? CWorkerOrchestrator.defaultWorkerExecutablePath()
            let validatorPath = parsed._test_overrides?.validator_executable_path
                ?? CWorkerOrchestrator.defaultValidatorExecutablePath()
            let cResp = CWorkerOrchestrator.run(
                parsed: parsed,
                policyHash: policyHash,
                bundleId: bundleString("CFBundleIdentifier"),
                workerExecutablePath: workerPath,
                validatorExecutablePath: validatorPath
            )
            // path_diagnostics enrichment runs on both paths so the
            // wire shape stays consistent regardless of which worker
            // produced the attempts.
            var enrichedResp = cResp
            enrichedResp.steps = enrichPathDiagnostics(steps: cResp.steps)
            replyAndExit(enrichedResp)
            return
        }

        let workerRun = WorkerProcess.run(
            requestData: request,
            expectedStepCount: parsed.probe_plan.count,
            executablePathOverride: parsed._test_overrides?.worker_executable_path,
            timeoutMsOverride: parsed._test_overrides?.worker_timeout_ms,
            specimenId: parsed.specimen_id
        )

        switch workerRun {
        case .failure(let err):
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: 1,
                normalized_outcome: NormalizedOutcome.workerSpawnFailed,
                error: err.description,
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                policy_sha256: policyHash,
                steps: [],
                test_overrides: parsed._test_overrides
            )
            replyAndExit(resp)

        case .success(let worker):
            let report = worker.report
            let enrichedSteps = enrichPathDiagnostics(steps: report?.steps ?? [])
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: worker.rc,
                normalized_outcome: worker.normalized_outcome,
                error: worker.error,
                pid: report?.worker_pid ?? worker.subprocess.pid,
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                policy_sha256: report?.policy_sha256 ?? policyHash,
                sandboxed_after_apply: report?.sandboxed_after_apply,
                deny_signal_total: report?.deny_signal_total,
                steps: enrichedSteps,
                instrumentation: report?.instrumentation,
                runner_subprocess: worker.subprocess,
                test_overrides: parsed._test_overrides
            )
            replyAndExit(resp)
        }
    }
}

// path_diagnostics is computed here in the unsandboxed host rather
// than in the worker (per RUNNER-RESHAPE-PLAN.md Step 3 / R4). The
// host's realpath(3) is not blocked by a worker (deny default)
// policy, so realpath_resolved is populated more reliably than the
// pre-Step-3 producer could manage. The fallback chain
// (wellKnownSymlinksResolved when realpath is unavailable) is
// retained for hosts that for any reason can't stat the path.
//
// The schema/wire shape is unchanged: path_diagnostics still appears
// on path-filter sandbox_check results and only on those. Consumers
// that branched on `path_diagnostics != nil` behave identically; the
// only observable difference is that realpath_resolved is less often
// null. The producer change is documented in PolicyWitness.md.
func enrichPathDiagnostics(steps: [PWRunnerStepResult]) -> [PWRunnerStepResult] {
    return steps.map { step in
        guard step.sandbox_check.filter_kind == PWRunnerWire.sandboxFilterPath,
              let value = step.sandbox_check.filter_value,
              !value.isEmpty
        else {
            return step
        }
        var updated = step
        let canonical = canonicalizePath(value)
        let basis = canonical.resolved ?? wellKnownSymlinksResolved(value)
        updated.sandbox_check.path_diagnostics = PWRunnerPathDiagnostics(
            input: value,
            realpath_resolved: canonical.resolved,
            firmlink_resolved: firmlinkResolved(basis),
            data_volume_form: dataVolumeForm(basis)
        )
        return updated
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

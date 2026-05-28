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

// PWRunnerService is the unsandboxed XPC host. It validates the request,
// starts a short-lived worker process that applies the specimen policy, then
// translates the worker report back into the public RunResult shape.
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
                steps: report?.steps ?? [],
                instrumentation: report?.instrumentation,
                runner_subprocess: worker.subprocess,
                test_overrides: parsed._test_overrides
            )
            replyAndExit(resp)
        }
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

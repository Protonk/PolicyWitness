import Foundation
import CryptoKit
import Darwin

private let PW_RUNNER_DENY_SIGNAL: Int32 = SIGUSR1

// Empirical sandbox_check filter kind values that are stable on current macOS:
// - PATH filter: 1 (already used elsewhere in this repo)
// - mach-lookup global name filter: 16 (used for "mach-lookup" + service name)
private let PW_SANDBOX_FILTER_PATH: Int32 = 1
private let PW_SANDBOX_FILTER_GLOBAL_NAME: Int32 = 16

private let PW_INSTRUMENTATION_PHASE_PRE: String = "pre_sandbox"
private let PW_INSTRUMENTATION_PHASE_POST: String = "post_sandbox"
private let PW_SANDBOX_CHECK_SCOPE_POST: String = "post_sandbox"

private func nowUnixMs() -> UInt64 {
    UInt64(Date().timeIntervalSince1970 * 1000.0)
}

private func bundleString(_ key: String) -> String? {
    Bundle.main.object(forInfoDictionaryKey: key) as? String
}

private func sha256Hex(_ data: Data) -> String {
    let digest = SHA256.hash(data: data)
    return digest.map { String(format: "%02x", $0) }.joined()
}

// MARK: - libsandbox bindings (dlopen/dlsym)

private struct SandboxLib {
    typealias SandboxParams = UnsafeMutableRawPointer
    typealias SandboxProfile = UnsafeMutableRawPointer

    typealias CreateParamsFn = @convention(c) () -> SandboxParams?
    typealias FreeParamsFn = @convention(c) (SandboxParams?) -> Void
    typealias SetParamFn = @convention(c) (SandboxParams?, UnsafePointer<CChar>?, UnsafePointer<CChar>?) -> Int32

    typealias CompileStringFn = @convention(c) (UnsafePointer<CChar>?, SandboxParams?, UnsafeMutablePointer<UnsafeMutablePointer<CChar>?>?) -> SandboxProfile?
    typealias CompileNamedFn = @convention(c) (UnsafePointer<CChar>?, SandboxParams?, UnsafeMutablePointer<UnsafeMutablePointer<CChar>?>?) -> SandboxProfile?
    typealias FreeProfileFn = @convention(c) (SandboxProfile?) -> Void
    typealias FreeErrorFn = @convention(c) (UnsafeMutablePointer<CChar>?) -> Void

    typealias ApplyFn = @convention(c) (SandboxProfile?) -> Int32
    typealias RegisterProfileFn = @convention(c) (UnsafePointer<CChar>?, UnsafeRawPointer?, size_t) -> Int32
    typealias UnregisterProfileFn = @convention(c) (UnsafePointer<CChar>?) -> Int32

    let createParams: CreateParamsFn
    let freeParams: FreeParamsFn
    let setParam: SetParamFn
    let compileString: CompileStringFn
    let compileNamed: CompileNamedFn
    let freeProfile: FreeProfileFn
    let freeError: FreeErrorFn
    let apply: ApplyFn
    let registerProfile: RegisterProfileFn
    let unregisterProfile: UnregisterProfileFn?

    struct LoadError: Error, CustomStringConvertible {
        var message: String

        var description: String { message }
    }

    static func load() -> Result<SandboxLib, LoadError> {
        guard let handle = dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW) else {
            return .failure(LoadError(message: "dlopen(/usr/lib/libsandbox.dylib) failed"))
        }
        func sym<T>(_ name: String, _ type: T.Type) -> Result<T, LoadError> {
            let ptr = name.withCString { dlsym(handle, $0) }
            guard let ptr else { return .failure(LoadError(message: "dlsym(\(name)) failed")) }
            return .success(unsafeBitCast(ptr, to: T.self))
        }

        let createParams: CreateParamsFn
        let freeParams: FreeParamsFn
        let setParam: SetParamFn
        let compileString: CompileStringFn
        let compileNamed: CompileNamedFn
        let freeProfile: FreeProfileFn
        let freeError: FreeErrorFn
        let apply: ApplyFn
        let registerProfile: RegisterProfileFn

        switch sym("sandbox_create_params", CreateParamsFn.self) {
        case .success(let v): createParams = v
        case .failure(let err): return .failure(err)
        }
        switch sym("sandbox_free_params", FreeParamsFn.self) {
        case .success(let v): freeParams = v
        case .failure(let err): return .failure(err)
        }
        switch sym("sandbox_set_param", SetParamFn.self) {
        case .success(let v): setParam = v
        case .failure(let err): return .failure(err)
        }
        switch sym("sandbox_compile_string", CompileStringFn.self) {
        case .success(let v): compileString = v
        case .failure(let err): return .failure(err)
        }
        switch sym("sandbox_compile_named", CompileNamedFn.self) {
        case .success(let v): compileNamed = v
        case .failure(let err): return .failure(err)
        }
        switch sym("sandbox_free_profile", FreeProfileFn.self) {
        case .success(let v): freeProfile = v
        case .failure(let err): return .failure(err)
        }
        switch sym("sandbox_free_error", FreeErrorFn.self) {
        case .success(let v): freeError = v
        case .failure(let err): return .failure(err)
        }
        switch sym("sandbox_apply", ApplyFn.self) {
        case .success(let v): apply = v
        case .failure(let err): return .failure(err)
        }
        switch sym("sandbox_register_profile", RegisterProfileFn.self) {
        case .success(let v): registerProfile = v
        case .failure(let err): return .failure(err)
        }
        let unregisterProfile: UnregisterProfileFn? = {
            let ptr = "sandbox_unregister_profile".withCString { dlsym(handle, $0) }
            guard let ptr else { return nil }
            return unsafeBitCast(ptr, to: UnregisterProfileFn.self)
        }()

        return .success(
            SandboxLib(
                createParams: createParams,
                freeParams: freeParams,
                setParam: setParam,
                compileString: compileString,
                compileNamed: compileNamed,
                freeProfile: freeProfile,
                freeError: freeError,
                apply: apply,
                registerProfile: registerProfile,
                unregisterProfile: unregisterProfile
            )
        )
    }
}

// MARK: - sandbox_check binding

private typealias SandboxCheckNoArgFn = @convention(c) (pid_t, UnsafePointer<CChar>?, Int32) -> Int32
private typealias SandboxCheckOneArgFn = @convention(c) (pid_t, UnsafePointer<CChar>?, Int32, UnsafePointer<CChar>?) -> Int32

private func resolveSandboxCheckSymbol() -> UnsafeMutableRawPointer? {
    let rtldDefault = UnsafeMutableRawPointer(bitPattern: -2)
    return "sandbox_check".withCString { sym in dlsym(rtldDefault, sym) }
}

// MARK: - Mach bootstrap lookup (for mach-lookup probes)

@_silgen_name("bootstrap_look_up")
private func bootstrap_look_up(_ bp: mach_port_t, _ service_name: UnsafePointer<CChar>, _ sp: UnsafeMutablePointer<mach_port_t>) -> kern_return_t

@_silgen_name("fcntl")
private func fcntl_getpath(_ fd: Int32, _ cmd: Int32, _ value: UnsafeMutablePointer<CChar>?) -> Int32

// MARK: - deny-signal counter (Channel B)

private var pwRunnerDenySignalCount: sig_atomic_t = 0

@_cdecl("pw_runner_deny_signal_handler")
private func pw_runner_deny_signal_handler(_ signo: Int32) {
    if signo == PW_RUNNER_DENY_SIGNAL {
        pwRunnerDenySignalCount += 1
    }
}

private func installDenySignalHandler() {
    _ = signal(PW_RUNNER_DENY_SIGNAL, pw_runner_deny_signal_handler)
    // In some XPC/libdispatch contexts, signals can be blocked on the current
    // thread. Unblock our deny signal so a sandbox-side-effect (if supported by
    // the active profile) can be observed deterministically.
    var set = sigset_t()
    sigemptyset(&set)
    sigaddset(&set, PW_RUNNER_DENY_SIGNAL)
    _ = pthread_sigmask(SIG_UNBLOCK, &set, nil)
}

private func denySignalCount() -> Int {
    Int(pwRunnerDenySignalCount)
}

// MARK: - Instrumentation ports (opt-in)

private func instrumentationDefaultPhase(kind: String) -> String {
    switch kind {
    case "dylib_load", "debug_wait", "execmem_probe", "dyld_env":
        return PW_INSTRUMENTATION_PHASE_PRE
    default:
        return PW_INSTRUMENTATION_PHASE_PRE
    }
}

private func instrumentationPhaseIsValid(_ phase: String) -> Bool {
    phase == PW_INSTRUMENTATION_PHASE_PRE || phase == PW_INSTRUMENTATION_PHASE_POST
}

private func instrumentationErrorReport(
    port: PWRunnerInstrumentationPort,
    phase: String?,
    status: String = "error",
    message: String
) -> PWRunnerInstrumentationPortReport {
    PWRunnerInstrumentationPortReport(
        kind: port.kind,
        phase: phase,
        label: port.label,
        status: status,
        error: message
    )
}

private func runInstrumentationPort(
    _ port: PWRunnerInstrumentationPort,
    phase: String
) -> PWRunnerInstrumentationPortReport {
    switch port.kind {
    case "dylib_load":
        guard let path = port.path, !path.isEmpty else {
            return instrumentationErrorReport(port: port, phase: phase, message: "missing dylib path")
        }
        let handle = path.withCString { dlopen($0, RTLD_NOW) }
        guard let handle else {
            let err = dlerror().map { String(cString: $0) } ?? "dlopen failed"
            return instrumentationErrorReport(port: port, phase: phase, message: err)
        }
        var symbolFound: Bool? = nil
        if let symbol = port.symbol, !symbol.isEmpty {
            _ = dlerror()
            let sym = symbol.withCString { dlsym(handle, $0) }
            if let sym {
                typealias DylibEntryFn = @convention(c) () -> Void
                let fn = unsafeBitCast(sym, to: DylibEntryFn.self)
                fn()
                symbolFound = true
            } else {
                let err = dlerror().map { String(cString: $0) } ?? "dlsym failed"
                return PWRunnerInstrumentationPortReport(
                    kind: port.kind,
                    phase: phase,
                    label: port.label,
                    status: "error",
                    error: err,
                    dylib: PWRunnerInstrumentationDylibReport(path: path, symbol: symbol, symbol_found: false)
                )
            }
        }
        let dylibReport = PWRunnerInstrumentationDylibReport(path: path, symbol: port.symbol, symbol_found: symbolFound)
        return PWRunnerInstrumentationPortReport(
            kind: port.kind,
            phase: phase,
            label: port.label,
            status: "ok",
            error: nil,
            dylib: dylibReport
        )

    case "debug_wait":
        guard let sleepMs = port.sleep_ms, sleepMs > 0 else {
            return instrumentationErrorReport(port: port, phase: phase, message: "missing sleep_ms")
        }
        Thread.sleep(forTimeInterval: Double(sleepMs) / 1000.0)
        return PWRunnerInstrumentationPortReport(
            kind: port.kind,
            phase: phase,
            label: port.label,
            status: "ok",
            error: nil,
            debug_wait: PWRunnerInstrumentationDebugWaitReport(sleep_ms: sleepMs)
        )

    case "execmem_probe":
        let requested = port.size_bytes ?? 4096
        let size = max(1, min(requested, 1024 * 1024))
        let ptr = mmap(nil, size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANON, -1, 0)
        if ptr == MAP_FAILED {
            let err = errno
            return PWRunnerInstrumentationPortReport(
                kind: port.kind,
                phase: phase,
                label: port.label,
                status: "error",
                error: String(cString: strerror(err)),
                execmem_probe: PWRunnerInstrumentationExecmemReport(
                    size_bytes: size,
                    mmap_succeeded: false,
                    errno: Int(err)
                )
            )
        }
        _ = munmap(ptr, size)
        return PWRunnerInstrumentationPortReport(
            kind: port.kind,
            phase: phase,
            label: port.label,
            status: "ok",
            error: nil,
            execmem_probe: PWRunnerInstrumentationExecmemReport(
                size_bytes: size,
                mmap_succeeded: true,
                errno: nil
            )
        )

    case "dyld_env":
        let keys = port.keys ?? []
        let expected = port.expected ?? [:]
        if keys.isEmpty && expected.isEmpty {
            return instrumentationErrorReport(port: port, phase: phase, message: "missing keys or expected map")
        }
        let env = ProcessInfo.processInfo.environment
        var present: Set<String> = []
        var missing: Set<String> = []
        var mismatched: Set<String> = []

        let keySet = Set(keys).union(expected.keys)
        for key in keySet {
            if let value = env[key] {
                present.insert(key)
                if let expectedValue = expected[key], expectedValue != value {
                    mismatched.insert(key)
                }
            } else {
                missing.insert(key)
                if expected.keys.contains(key) {
                    mismatched.insert(key)
                }
            }
        }

        let reveal = port.reveal_values ?? false
        var values: [String: String]? = nil
        if reveal {
            var out: [String: String] = [:]
            for key in keySet.sorted() {
                if let value = env[key] {
                    out[key] = value
                }
            }
            values = out.isEmpty ? nil : out
        }

        let keysPresent = present.sorted()
        let keysMissing = missing.sorted()
        let keysMismatch = mismatched.sorted()
        let status = (keysMissing.isEmpty && keysMismatch.isEmpty) ? "ok" : "error"
        let report = PWRunnerInstrumentationDyldEnvReport(
            keys_present: keysPresent,
            keys_missing: keysMissing,
            expected_mismatch: keysMismatch,
            values: values
        )
        return PWRunnerInstrumentationPortReport(
            kind: port.kind,
            phase: phase,
            label: port.label,
            status: status,
            error: status == "ok" ? nil : "dyld env check failed",
            dyld_env: report
        )

    default:
        return instrumentationErrorReport(
            port: port,
            phase: phase,
            status: "unsupported",
            message: "unsupported instrumentation port"
        )
    }
}

private func applyInstrumentationPhase(
    _ phase: String,
    ports: [PWRunnerInstrumentationPort],
    reports: inout [PWRunnerInstrumentationPortReport?]
) {
    for (idx, port) in ports.enumerated() {
        if reports[idx] != nil {
            continue
        }
        if let requestedPhase = port.phase, !instrumentationPhaseIsValid(requestedPhase) {
            reports[idx] = instrumentationErrorReport(
                port: port,
                phase: requestedPhase,
                message: "unknown phase (expected pre_sandbox|post_sandbox)"
            )
            continue
        }
        let effectivePhase = port.phase ?? instrumentationDefaultPhase(kind: port.kind)
        if effectivePhase != phase {
            continue
        }
        reports[idx] = runInstrumentationPort(port, phase: effectivePhase)
    }
}

private func finalizeInstrumentationReport(
    version: Int,
    ports: [PWRunnerInstrumentationPort],
    reports: [PWRunnerInstrumentationPortReport?],
    earlyReason: String?
) -> PWRunnerInstrumentationReport {
    var out: [PWRunnerInstrumentationPortReport] = []
    out.reserveCapacity(ports.count)
    for (idx, port) in ports.enumerated() {
        if let report = reports[idx] {
            out.append(report)
            continue
        }
        let phase = port.phase ?? instrumentationDefaultPhase(kind: port.kind)
        let message = earlyReason ?? "instrumentation port did not run"
        out.append(
            PWRunnerInstrumentationPortReport(
                kind: port.kind,
                phase: phase,
                label: port.label,
                status: "skipped",
                error: message
            )
        )
    }
    return PWRunnerInstrumentationReport(version: version, ports: out)
}

// MARK: - Runner implementation

public final class PWRunnerService: NSObject, PWRunnerProtocol {
    private var didRun = false

    public func runSpecimen(_ request: Data, withReply reply: @escaping (Data) -> Void) {
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
            reply((try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8))
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(50)) { exit(0) }
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
            reply((try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8))
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(50)) { exit(0) }
            return
        }

        var instrumentationVersion: Int? = nil
        var instrumentationPorts: [PWRunnerInstrumentationPort] = []
        var instrumentationReports: [PWRunnerInstrumentationPortReport?] = []
        var instrumentationReport: PWRunnerInstrumentationReport? = nil

        if let instrumentation = parsed.instrumentation {
            instrumentationVersion = instrumentation.version
            instrumentationPorts = instrumentation.ports
            if instrumentation.version != 1 {
                let reports = instrumentationPorts.map { port in
                    instrumentationErrorReport(
                        port: port,
                        phase: port.phase ?? instrumentationDefaultPhase(kind: port.kind),
                        message: "unsupported instrumentation version \(instrumentation.version)"
                    )
                }
                instrumentationReport = PWRunnerInstrumentationReport(version: instrumentation.version, ports: reports)
            } else {
                instrumentationReports = Array(repeating: nil, count: instrumentationPorts.count)
                applyInstrumentationPhase(
                    PW_INSTRUMENTATION_PHASE_PRE,
                    ports: instrumentationPorts,
                    reports: &instrumentationReports
                )
            }
        }

        let finalizeInstrumentation = { (reason: String?) -> PWRunnerInstrumentationReport? in
            guard let version = instrumentationVersion else { return nil }
            if let report = instrumentationReport {
                return report
            }
            return finalizeInstrumentationReport(
                version: version,
                ports: instrumentationPorts,
                reports: instrumentationReports,
                earlyReason: reason
            )
        }

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
                instrumentation: finalizeInstrumentation("runner exited before sandbox setup")
            )
            reply((try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8))
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(50)) { exit(0) }
            return
        }

        let sandboxCheckSymbol = resolveSandboxCheckSymbol()
        if sandboxCheckSymbol == nil {
            let resp = PWRunnerRunResult(
                specimen_id: parsed.specimen_id,
                run_kind: parsed.run_kind,
                rc: 1,
                normalized_outcome: "sandbox_check_missing",
                error: "sandbox_check symbol not found via dlsym(RTLD_DEFAULT, \"sandbox_check\")",
                pid: Int(getpid()),
                bundle_id: bundleString("CFBundleIdentifier"),
                policy_format: parsed.policy.format,
                steps: [],
                instrumentation: finalizeInstrumentation("runner exited before sandbox setup")
            )
            reply((try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8))
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(50)) { exit(0) }
            return
        }

        let policyHash: String?
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
                instrumentation: finalizeInstrumentation("runner exited before sandbox apply")
            )
            reply((try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8))
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(50)) { exit(0) }
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
                instrumentation: finalizeInstrumentation("runner exited before sandbox apply")
            )
            reply((try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8))
            DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(50)) { exit(0) }
            return
        }

        if instrumentationVersion == 1 && instrumentationReport == nil {
            applyInstrumentationPhase(
                PW_INSTRUMENTATION_PHASE_POST,
                ports: instrumentationPorts,
                reports: &instrumentationReports
            )
        }

        let sandboxedAfterApply: Bool? = {
            guard let symbol = sandboxCheckSymbol else { return nil }
            let fn = unsafeBitCast(symbol, to: SandboxCheckNoArgFn.self)
            let rc = fn(getpid(), nil, 0)
            return rc == 1
        }()

        var stepResults: [PWRunnerStepResult] = []
        for step in parsed.probe_plan {
            let beforeSig = denySignalCount()
            let sb = runSandboxCheck(step.sandbox_check, symbol: sandboxCheckSymbol!)
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
            instrumentation: finalizeInstrumentation(nil)
        )
        reply((try? pwRunnerEncodeJSON(resp)) ?? Data("{}".utf8))
        DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(50)) { exit(0) }
    }

    private enum PolicyHashError: Error, CustomStringConvertible {
        case missingField(String)

        var description: String {
            switch self {
            case .missingField(let f):
                return "missing policy field: \(f)"
            }
        }
    }

    private func computePolicyHash(_ policy: PWRunnerPolicySpec) throws -> String {
        switch policy.format {
        case "sbpl":
            guard let src = policy.sbpl_source else { throw PolicyHashError.missingField("sbpl_source") }
            return sha256Hex(Data(src.utf8))
        case "compiled_bytes":
            guard let b64 = policy.compiled_profile_b64 else {
                throw PolicyHashError.missingField("compiled_profile_b64")
            }
            guard let data = Data(base64Encoded: b64) else {
                throw PolicyHashError.missingField("compiled_profile_b64 (invalid base64)")
            }
            return sha256Hex(data)
        default:
            throw PolicyHashError.missingField("format (expected sbpl|compiled_bytes)")
        }
    }

    private struct ApplyError: Error, CustomStringConvertible {
        var message: String

        var description: String { message }
    }

    private func applySandboxPolicy(_ policy: PWRunnerPolicySpec, sandboxLib: SandboxLib) -> Result<Void, ApplyError> {
        // `sandbox_set_param` is an underspecified private API. Keep the key/value C strings alive
        // until compilation completes to avoid relying on whether libsandbox copies the strings.
        var paramCStringAllocs: [UnsafeMutablePointer<CChar>] = []
        defer {
            for ptr in paramCStringAllocs {
                free(ptr)
            }
        }

        // Create params if present.
        let paramsObj: SandboxLib.SandboxParams?
        if let params = policy.params, !params.isEmpty {
            guard let obj = sandboxLib.createParams() else {
                return .failure(ApplyError(message: "sandbox_create_params failed (returned NULL)"))
            }
            for (key, value) in params.sorted(by: { $0.key < $1.key }) {
                guard let keyDup = strdup(key) else {
                    sandboxLib.freeParams(obj)
                    return .failure(ApplyError(message: "strdup failed for param key"))
                }
                guard let valueDup = strdup(value) else {
                    free(keyDup)
                    sandboxLib.freeParams(obj)
                    return .failure(ApplyError(message: "strdup failed for param value"))
                }
                paramCStringAllocs.append(keyDup)
                paramCStringAllocs.append(valueDup)

                let rc: Int32 = sandboxLib.setParam(obj, keyDup, valueDup)
                if rc != 0 {
                    sandboxLib.freeParams(obj)
                    return .failure(
                        ApplyError(
                            message: "sandbox_set_param failed for key \(key): rc=\(rc)"
                        )
                    )
                }
            }
            paramsObj = obj
        } else {
            paramsObj = nil
        }
        defer { sandboxLib.freeParams(paramsObj) }

        switch policy.format {
        case "sbpl":
            guard let src = policy.sbpl_source else { return .failure(ApplyError(message: "missing policy.sbpl_source")) }
            var errBuf: UnsafeMutablePointer<CChar>?
            let profile: SandboxLib.SandboxProfile? = src.withCString { cStr in
                sandboxLib.compileString(cStr, paramsObj, &errBuf)
            }
            if let errBuf {
                let message = String(cString: errBuf)
                sandboxLib.freeError(errBuf)
                return .failure(ApplyError(message: "sandbox_compile_string failed: \(message)"))
            }
            guard let profile else { return .failure(ApplyError(message: "sandbox_compile_string failed (no profile and no error)")) }
            defer { sandboxLib.freeProfile(profile) }
            let rc = sandboxLib.apply(profile)
            if rc != 0 {
                return .failure(ApplyError(message: "sandbox_apply failed: \(String(cString: strerror(errno)))"))
            }
            return .success(())

        case "compiled_bytes":
            guard let b64 = policy.compiled_profile_b64 else { return .failure(ApplyError(message: "missing policy.compiled_profile_b64")) }
            guard let bytes = Data(base64Encoded: b64) else { return .failure(ApplyError(message: "compiled_profile_b64 invalid base64")) }
            let name = "pw.runner.\(UUID().uuidString)"
            let regRc: Int32 = name.withCString { namePtr in
                bytes.withUnsafeBytes { buf in
                    let base = buf.baseAddress
                    return sandboxLib.registerProfile(namePtr, base, buf.count)
                }
            }
            if regRc != 0 {
                return .failure(ApplyError(message: "sandbox_register_profile failed: \(String(cString: strerror(errno)))"))
            }
            defer {
                if let unregister = sandboxLib.unregisterProfile {
                    _ = name.withCString { ptr in unregister(ptr) }
                }
            }

            var errBuf: UnsafeMutablePointer<CChar>?
            let profile: SandboxLib.SandboxProfile? = name.withCString { namePtr in
                sandboxLib.compileNamed(namePtr, paramsObj, &errBuf)
            }
            if let errBuf {
                let message = String(cString: errBuf)
                sandboxLib.freeError(errBuf)
                return .failure(ApplyError(message: "sandbox_compile_named failed: \(message)"))
            }
            guard let profile else { return .failure(ApplyError(message: "sandbox_compile_named failed (no profile and no error)")) }
            defer { sandboxLib.freeProfile(profile) }
            let rc = sandboxLib.apply(profile)
            if rc != 0 {
                return .failure(ApplyError(message: "sandbox_apply failed: \(String(cString: strerror(errno)))"))
            }
            return .success(())

        default:
            return .failure(ApplyError(message: "unknown policy.format (expected sbpl|compiled_bytes)"))
        }
    }

    private func runSandboxCheck(_ check: PWRunnerSandboxCheck, symbol: UnsafeMutableRawPointer) -> PWRunnerSandboxCheckResult {
        let op = check.operation
        let filterKind = check.filter.kind
        let filterValue = check.filter.value
        var effectiveFilterValue = filterValue

        if filterKind == "path", let value = filterValue, !value.isEmpty {
            let canonical = canonicalizePath(value)
            effectiveFilterValue = canonical.normalized
        }

        let rc: Int32 = op.withCString { opPtr in
            switch filterKind {
            case "none":
                let fn = unsafeBitCast(symbol, to: SandboxCheckNoArgFn.self)
                return fn(getpid(), opPtr, 0)
            case "path":
                let fn = unsafeBitCast(symbol, to: SandboxCheckOneArgFn.self)
                return (effectiveFilterValue ?? "").withCString { pathPtr in
                    fn(getpid(), opPtr, PW_SANDBOX_FILTER_PATH, pathPtr)
                }
            case "global_name":
                let fn = unsafeBitCast(symbol, to: SandboxCheckOneArgFn.self)
                return (filterValue ?? "").withCString { namePtr in
                    fn(getpid(), opPtr, PW_SANDBOX_FILTER_GLOBAL_NAME, namePtr)
                }
            default:
                let fn = unsafeBitCast(symbol, to: SandboxCheckNoArgFn.self)
                return fn(getpid(), opPtr, 0)
            }
        }

        let outcome: String
        if rc == 0 {
            outcome = "allow"
        } else if rc == 1 {
            outcome = "deny"
        } else {
            outcome = "rc_nonstandard"
        }

        return PWRunnerSandboxCheckResult(
            rc: Int(rc),
            outcome: outcome,
            scope: PW_SANDBOX_CHECK_SCOPE_POST,
            filter_kind: filterKind,
            filter_value: filterValue,
            effective_filter_value: effectiveFilterValue
        )
    }

    private func runAttempt(_ attempt: PWRunnerAttempt) -> PWRunnerAttemptResult {
        switch attempt.kind {
        case "file":
            return runFileAttempt(action: attempt.action, path: attempt.target)
        case "mach_lookup":
            return runMachLookupAttempt(action: attempt.action, name: attempt.target)
        default:
            return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: "unsupported", error: "unsupported attempt.kind")
        }
    }

    private func runFileAttempt(action: String, path: String) -> PWRunnerAttemptResult {
        let resolved = canonicalizePath(path)
        let target = resolved.resolved ?? resolved.normalized
        let requestedPath = resolved.input
        let normalizedPath = resolved.normalized

        switch action {
        case "open_read":
            var buf: UInt8 = 0
            let fd = target.withCString { open($0, O_RDONLY, 0) }
            if fd < 0 {
                return PWRunnerAttemptResult(
                    rc: 1,
                    errno: Int(errno),
                    outcome: "open_failed",
                    error: String(cString: strerror(errno)),
                    requested_path: requestedPath,
                    normalized_path: normalizedPath,
                    observed_path: nil
                )
            }
            defer { close(fd) }
            _ = Darwin.read(fd, &buf, 1)
            let observed = observedPathForFd(fd)
            return PWRunnerAttemptResult(
                rc: 0,
                errno: nil,
                outcome: "ok",
                error: nil,
                requested_path: requestedPath,
                normalized_path: normalizedPath,
                observed_path: observed
            )

        case "open_write":
            let fd = target.withCString { open($0, O_WRONLY | O_TRUNC, 0) }
            if fd < 0 {
                return PWRunnerAttemptResult(
                    rc: 1,
                    errno: Int(errno),
                    outcome: "open_failed",
                    error: String(cString: strerror(errno)),
                    requested_path: requestedPath,
                    normalized_path: normalizedPath,
                    observed_path: nil
                )
            }
            defer { close(fd) }
            var b: UInt8 = UInt8(ascii: "x")
            _ = Darwin.write(fd, &b, 1)
            let observed = observedPathForFd(fd)
            return PWRunnerAttemptResult(
                rc: 0,
                errno: nil,
                outcome: "ok",
                error: nil,
                requested_path: requestedPath,
                normalized_path: normalizedPath,
                observed_path: observed
            )

        case "create":
            let fd = target.withCString { open($0, O_WRONLY | O_CREAT, 0o600) }
            if fd < 0 {
                return PWRunnerAttemptResult(
                    rc: 1,
                    errno: Int(errno),
                    outcome: "open_failed",
                    error: String(cString: strerror(errno)),
                    requested_path: requestedPath,
                    normalized_path: normalizedPath,
                    observed_path: nil
                )
            }
            let observed = observedPathForFd(fd)
            close(fd)
            return PWRunnerAttemptResult(
                rc: 0,
                errno: nil,
                outcome: "ok",
                error: nil,
                requested_path: requestedPath,
                normalized_path: normalizedPath,
                observed_path: observed
            )

        case "unlink":
            let rc = target.withCString { unlink($0) }
            if rc != 0 {
                return PWRunnerAttemptResult(
                    rc: 1,
                    errno: Int(errno),
                    outcome: "unlink_failed",
                    error: String(cString: strerror(errno)),
                    requested_path: requestedPath,
                    normalized_path: normalizedPath,
                    observed_path: nil
                )
            }
            return PWRunnerAttemptResult(
                rc: 0,
                errno: nil,
                outcome: "ok",
                error: nil,
                requested_path: requestedPath,
                normalized_path: normalizedPath,
                observed_path: nil
            )

        default:
            return PWRunnerAttemptResult(
                rc: 1,
                errno: nil,
                outcome: "unsupported",
                error: "unsupported file action",
                requested_path: requestedPath,
                normalized_path: normalizedPath,
                observed_path: nil
            )
        }
    }

    private func runMachLookupAttempt(action: String, name: String) -> PWRunnerAttemptResult {
        guard action == "bootstrap_look_up" else {
            return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: "unsupported", error: "unsupported mach_lookup action")
        }

        var bootstrap: mach_port_t = 0
        let kr = task_get_special_port(mach_task_self_, task_special_port_t(TASK_BOOTSTRAP_PORT), &bootstrap)
        if kr != KERN_SUCCESS {
            return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: "bootstrap_port_failed", error: "task_get_special_port failed kr=\(kr)")
        }

        var servicePort: mach_port_t = 0
        let kr2: kern_return_t = name.withCString { ptr in
            bootstrap_look_up(bootstrap, ptr, &servicePort)
        }
        if kr2 != KERN_SUCCESS {
            return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: "lookup_failed", error: "bootstrap_look_up failed kr=\(kr2)")
        }
        mach_port_deallocate(mach_task_self_, servicePort)
        return PWRunnerAttemptResult(rc: 0, errno: nil, outcome: "ok", error: nil)
    }

    private struct CanonicalPath {
        var input: String
        var normalized: String
        var resolved: String?
    }

    private func canonicalizePath(_ input: String) -> CanonicalPath {
        var buf = [CChar](repeating: 0, count: Int(PATH_MAX))
        let rc = input.withCString { ptr in
            realpath(ptr, &buf)
        }
        if rc != nil {
            let resolved = String(cString: buf)
            return CanonicalPath(input: input, normalized: resolved, resolved: resolved)
        }
        let normalized: String
        if input.hasPrefix("/") {
            normalized = URL(fileURLWithPath: input).standardizedFileURL.path
        } else {
            normalized = input
        }
        return CanonicalPath(input: input, normalized: normalized, resolved: nil)
    }

    private func observedPathForFd(_ fd: Int32) -> String? {
        var buf = [CChar](repeating: 0, count: Int(PATH_MAX))
        let rc: Int32 = buf.withUnsafeMutableBufferPointer { ptr in
            guard let base = ptr.baseAddress else {
                return -1
            }
            return fcntl_getpath(fd, F_GETPATH, base)
        }
        if rc == 0 {
            return String(cString: buf)
        }
        return nil
    }
}

public final class PWRunnerSessionDelegate: NSObject, NSXPCListenerDelegate {
    public func listener(_ listener: NSXPCListener, shouldAcceptNewConnection newConnection: NSXPCConnection) -> Bool {
        let exported = PWRunnerService()
        newConnection.exportedInterface = NSXPCInterface(with: PWRunnerProtocol.self)
        newConnection.exportedObject = exported
        newConnection.resume()
        return true
    }
}

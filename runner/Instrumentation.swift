import Foundation
import Darwin

// Instrumentation ports are opt-in and executed only when requested in the spec.
private func instrumentationDefaultPhase(kind: String) -> String {
    switch kind {
    case PWRunnerWire.instrumentationKindDylibLoad,
         PWRunnerWire.instrumentationKindDebugWait,
         PWRunnerWire.instrumentationKindExecmemProbe,
         PWRunnerWire.instrumentationKindDyldEnv:
        return PWRunnerWire.instrumentationPhasePre
    default:
        return PWRunnerWire.instrumentationPhasePre
    }
}

private func instrumentationPhaseIsValid(_ phase: String) -> Bool {
    phase == PWRunnerWire.instrumentationPhasePre || phase == PWRunnerWire.instrumentationPhasePost
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
    case PWRunnerWire.instrumentationKindDylibLoad:
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

    case PWRunnerWire.instrumentationKindDebugWait:
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

    case PWRunnerWire.instrumentationKindExecmemProbe:
        let requested = port.size_bytes ?? 4096
        let size = max(1, min(requested, 1024 * 1024))
        // Prefer MAP_JIT when allowed; fall back to legacy RWX mapping if needed.
        let flagsJit = MAP_PRIVATE | MAP_ANON | MAP_JIT
        let protJit = PROT_READ | PROT_WRITE  // MAP_JIT provides an exec alias.
        var primaryErr: Int32? = nil

        let ptrJit = mmap(nil, size, protJit, flagsJit, -1, 0)
        if ptrJit != MAP_FAILED {
            _ = munmap(ptrJit, size)
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
        }
        primaryErr = errno

        // Legacy fallback: RWX anonymous mapping (may still fail under hardened runtime).
        let ptrLegacy = mmap(nil, size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANON, -1, 0)
        if ptrLegacy != MAP_FAILED {
            _ = munmap(ptrLegacy, size)
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
        }
        let err = errno
        let combinedError: String
        if let primaryErr {
            combinedError = "MAP_JIT failed: \(String(cString: strerror(primaryErr))); RWX mmap failed: \(String(cString: strerror(err)))"
        } else {
            combinedError = String(cString: strerror(err))
        }
        return PWRunnerInstrumentationPortReport(
            kind: port.kind,
            phase: phase,
            label: port.label,
            status: "error",
            error: combinedError,
            execmem_probe: PWRunnerInstrumentationExecmemReport(
                size_bytes: size,
                mmap_succeeded: false,
                errno: Int(err)
            )
        )

    case PWRunnerWire.instrumentationKindDyldEnv:
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

struct InstrumentationState {
    // Tracks instrumentation ports across pre/post phases.
    let version: Int
    let ports: [PWRunnerInstrumentationPort]
    private var reports: [PWRunnerInstrumentationPortReport?]
    private let precomputedReport: PWRunnerInstrumentationReport?

    init?(spec: PWRunnerInstrumentation?) {
        guard let spec else { return nil }
        version = spec.version
        ports = spec.ports
        reports = Array(repeating: nil, count: ports.count)

        if spec.version != 1 {
            let errorReports = ports.map { port in
                instrumentationErrorReport(
                    port: port,
                    phase: port.phase ?? instrumentationDefaultPhase(kind: port.kind),
                    message: "unsupported instrumentation version \(spec.version)"
                )
            }
            precomputedReport = PWRunnerInstrumentationReport(version: spec.version, ports: errorReports)
        } else {
            precomputedReport = nil
        }
    }

    mutating func runPhase(_ phase: String) {
        if precomputedReport != nil || version != 1 {
            return
        }
        applyInstrumentationPhase(phase, ports: ports, reports: &reports)
    }

    func finalize(reason: String?) -> PWRunnerInstrumentationReport {
        if let precomputedReport {
            return precomputedReport
        }
        return finalizeInstrumentationReport(
            version: version,
            ports: ports,
            reports: reports,
            earlyReason: reason
        )
    }
}

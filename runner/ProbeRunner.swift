import Foundation
import Darwin

// Probe execution helpers: sandbox_check plus file and mach-lookup attempts.
// Empirical sandbox_check filter kind values that are stable on current macOS:
// - PATH filter: 1
// - mach-lookup global name filter: 16
// - mach-lookup local name filter: 17
private let PW_SANDBOX_FILTER_PATH: Int32 = 1
private let PW_SANDBOX_FILTER_GLOBAL_NAME: Int32 = 16
private let PW_SANDBOX_FILTER_LOCAL_NAME: Int32 = 17

// sandbox_check binding (C shim)
@_silgen_name("pw_sandbox_check")
private func pw_sandbox_check(
    _ pid: pid_t,
    _ operation: UnsafePointer<CChar>?,
    _ filter: Int32,
    _ arg: UnsafePointer<CChar>?,
    _ out_errno: UnsafeMutablePointer<Int32>?
) -> Int32

@_silgen_name("pw_sandbox_check_noarg")
private func pw_sandbox_check_noarg(
    _ pid: pid_t,
    _ operation: UnsafePointer<CChar>?,
    _ out_errno: UnsafeMutablePointer<Int32>?
) -> Int32

// Mach bootstrap lookup (for mach-lookup probes).
@_silgen_name("bootstrap_look_up")
private func bootstrap_look_up(
    _ bp: mach_port_t,
    _ service_name: UnsafePointer<CChar>,
    _ sp: UnsafeMutablePointer<mach_port_t>
) -> kern_return_t

private enum SpecValidationError: Error, CustomStringConvertible {
    case invalidSandboxCheck(stepId: String, message: String)

    var description: String {
        switch self {
        case .invalidSandboxCheck(let stepId, let message):
            return "invalid sandbox_check for step \(stepId): \(message)"
        }
    }
}

func validateSandboxChecks(_ steps: [PWRunnerProbeStep]) throws {
    let allowedKinds: Set<String> = [
        PWRunnerWire.sandboxFilterNone,
        PWRunnerWire.sandboxFilterPath,
        PWRunnerWire.sandboxFilterGlobalName,
        PWRunnerWire.sandboxFilterLocalName,
    ]
    for step in steps {
        let op = step.sandbox_check.operation.trimmingCharacters(in: .whitespacesAndNewlines)
        if op.isEmpty {
            throw SpecValidationError.invalidSandboxCheck(stepId: step.step_id, message: "operation is empty")
        }
        let kind = step.sandbox_check.filter.kind
        if !allowedKinds.contains(kind) {
            throw SpecValidationError.invalidSandboxCheck(
                stepId: step.step_id,
                message: "unsupported filter.kind \(kind)"
            )
        }
        if kind != PWRunnerWire.sandboxFilterNone {
            let value = step.sandbox_check.filter.value?.trimmingCharacters(in: .whitespacesAndNewlines)
            if value == nil || value == "" {
                throw SpecValidationError.invalidSandboxCheck(
                    stepId: step.step_id,
                    message: "filter.value required for kind \(kind)"
                )
            }
        }
    }
}

func runSandboxCheck(_ check: PWRunnerSandboxCheck) -> PWRunnerSandboxCheckResult {
    let op = check.operation
    let filterKind = check.filter.kind
    let filterValue = check.filter.value
    let pid = Int(getpid())
    var effectiveFilterValue = filterValue

    if filterKind == PWRunnerWire.sandboxFilterPath, let value = filterValue, !value.isEmpty {
        let canonical = canonicalizePath(value)
        effectiveFilterValue = canonical.normalized
    }

    let (filterTypeId, argValue): (Int32, String?) = {
        switch filterKind {
        case PWRunnerWire.sandboxFilterNone:
            return (0, nil)
        case PWRunnerWire.sandboxFilterPath:
            return (PW_SANDBOX_FILTER_PATH, filterValue)
        case PWRunnerWire.sandboxFilterGlobalName:
            return (PW_SANDBOX_FILTER_GLOBAL_NAME, filterValue)
        case PWRunnerWire.sandboxFilterLocalName:
            return (PW_SANDBOX_FILTER_LOCAL_NAME, filterValue)
        default:
            return (0, nil)
        }
    }()

    var errNo: Int32 = 0
    let rc: Int32 = op.withCString { opPtr in
        if filterTypeId == 0 {
            return pw_sandbox_check_noarg(getpid(), opPtr, &errNo)
        }
        return (argValue ?? "").withCString { argPtr in
            pw_sandbox_check(getpid(), opPtr, filterTypeId, argPtr, &errNo)
        }
    }

    var outcome: String
    var errNoOut: Int? = nil
    var errMsg: String? = nil
    if errNo != 0 {
        errNoOut = Int(errNo)
        errMsg = String(cString: strerror(errNo))
    }
    if rc == 0 {
        outcome = "allow"
    } else if rc == 1 && errNo == 0 {
        outcome = "deny"
    } else {
        outcome = "error"
    }

    return PWRunnerSandboxCheckResult(
        rc: Int(rc),
        outcome: outcome,
        pid: pid,
        operation: op,
        scope: PWRunnerWire.sandboxCheckScopePost,
        filter_kind: filterKind,
        filter_value: filterValue,
        effective_filter_value: effectiveFilterValue,
        filter_type_id: Int(filterTypeId),
        errno: errNoOut,
        error: errMsg
    )
}

func runAttempt(_ attempt: PWRunnerAttempt) -> PWRunnerAttemptResult {
    switch attempt.kind {
    case PWRunnerWire.attemptKindFile:
        return runFileAttempt(action: attempt.action, path: attempt.target)
    case PWRunnerWire.attemptKindMachLookup:
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
    case PWRunnerWire.attemptActionOpenRead:
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

    case PWRunnerWire.attemptActionOpenWrite:
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

    case PWRunnerWire.attemptActionCreate:
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

    case PWRunnerWire.attemptActionUnlink:
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
    guard action == PWRunnerWire.attemptActionMachLookup else {
        return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: "unsupported", error: "unsupported mach_lookup action")
    }

    // Use the task bootstrap port to mirror how launchd resolves Mach services.
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

// Best-effort "am I sandboxed" check for reporting purposes.
// Returns false on unexpected sandbox_check errors.
func currentProcessIsSandboxed() -> Bool {
    var err: Int32 = 0
    let rc = pw_sandbox_check_noarg(getpid(), nil, &err)
    return rc == 1
}

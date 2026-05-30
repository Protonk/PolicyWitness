import Foundation
import Darwin

// Probe execution helpers: sandbox_check plus file and mach-lookup attempts.
// Filter type IDs for sandbox_check. The public sandbox.h doesn't export
// these; the values are determined empirically by comparing sandbox_check
// verdicts against actual kernel enforcement (see
// tests/suites/witness_contract/harness/verify_filter_id.sh).
// - PATH filter: 1                       (long-stable; widely documented)
// - mach-lookup global name filter: 2    (selected working ID. Strict
//                                         verification — both denied
//                                         and allowed sibling — passes
//                                         for IDs 2 AND 12 across the
//                                         scan to 200; uniqueness is
//                                         NOT proven. ID 2 was chosen
//                                         because it is the lower of
//                                         the two and conventional;
//                                         ID 12 is presumably an alias
//                                         or aliased predicate path.
//                                         The previously-documented 16
//                                         was empirically wrong — the
//                                         original cause of BBX-001.)
// - mach-lookup local name filter: 17    (NOT YET re-verified by the same
//                                         methodology; may also be wrong.
//                                         No in-tree test exercises local-name
//                                         today. Recheck before relying on
//                                         this constant for any new fixture.)
private let PW_SANDBOX_FILTER_PATH: Int32 = 1
private let PW_SANDBOX_FILTER_GLOBAL_NAME: Int32 = 2
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
        PWRunnerWire.sandboxFilterIokitRegistryEntryClass,
        PWRunnerWire.sandboxFilterIokitUserClientClass,
        PWRunnerWire.sandboxFilterSysctlName,
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

// (operation, filter_kind) pairs for which the runner deliberately
// does NOT call sandbox_check, because empirical verification against
// actual kernel enforcement (verify_filter_id.sh) has shown the
// userland predicate returns wrong answers for these specific
// combinations regardless of numeric filter ID. Channel A (the
// attempt result) remains the reliable evidence; the prediction is
// honestly absent rather than silently wrong.
//
// Keyed by (operation, filter_kind), not by filter_kind alone — a
// filter kind might be reliable for one op and unreliable for
// another, and the verification is op+filter-specific. A specimen
// pairing one of these filter kinds with a DIFFERENT operation gets
// the normal sandbox_check call; the prediction may still be wrong,
// but we haven't proven it and we don't override the prediction we
// haven't verified to be wrong.
//
// Entries here must be paired with an enforcement_probe verification
// commit naming the op+filter pair and the empirical evidence.
struct PredictionUnavailablePair: Hashable {
    let operation: String
    let filterKind: String
}

private let predictionUnavailableOpFilters: Set<PredictionUnavailablePair> = [
    // iokit-open-service + iokit-registry-entry-class: verified
    // 2026-05-29 against IOSurfaceRoot; no filter ID in 1..200
    // produced a sandbox_check verdict matching kernel enforcement.
    .init(operation: "iokit-open-service",
          filterKind: PWRunnerWire.sandboxFilterIokitRegistryEntryClass),
    // iokit-open-user-client + iokit-user-client-class: verified
    // 2026-05-29 with policy filter value IOSurfaceRootUserClient
    // and probe target IOSurfaceRoot. The earlier "verification"
    // (pre-audit) used operation iokit-open-service, which is the
    // wrong SBPL operation for this filter — both operations fire
    // when IOServiceOpen is called, but iokit-user-client-class
    // matches against the open-user-client operation. With the
    // corrected pairing the kernel enforces the deny (kr=
    // kIOReturnNotPermitted) and no sandbox_check filter ID in
    // 1..200 produces a verdict that agrees with the kernel.
    .init(operation: "iokit-open-user-client",
          filterKind: PWRunnerWire.sandboxFilterIokitUserClientClass),
    // sysctl-read + sysctl-name: verified 2026-05-29 against
    // kern.osrelease; same pattern as iokit. Confirms the
    // userland-vs-kernel drift is broader than iokit.
    .init(operation: "sysctl-read",
          filterKind: PWRunnerWire.sandboxFilterSysctlName),
]

// Sentinel rc value emitted alongside outcome=prediction_unavailable.
// A non-zero value so any consumer that keys on rc==0 (the long-standing
// "allow" convention) doesn't misread the absent prediction as allow.
// Consumers should treat rc with outcome==prediction_unavailable as
// "no sandbox_check return value to interpret."
private let predictionUnavailableRC: Int = -1

func runSandboxCheck(_ check: PWRunnerSandboxCheck) -> PWRunnerSandboxCheckResult {
    let op = check.operation
    let filterKind = check.filter.kind
    let filterValue = check.filter.value
    let pid = Int(getpid())
    var effectiveFilterValue = filterValue

    let opFilterPair = PredictionUnavailablePair(operation: op, filterKind: filterKind)
    if predictionUnavailableOpFilters.contains(opFilterPair) {
        // Skip sandbox_check entirely — its verdict for this op+filter
        // pair is known unreliable. Emit prediction_unavailable so
        // consumers can tell "we deliberately didn't predict" apart
        // from "we predicted and got allow/deny/error". The attempt
        // (channel A) still runs.
        //
        // rc is the sentinel predictionUnavailableRC (-1) so any
        // consumer that keys on rc==0 ("allow" by long-standing
        // convention) doesn't misread the absent prediction as allow.
        // The (rc=-1, outcome=prediction_unavailable, errno=nil)
        // triple is unambiguous and documented in PolicyWitness.md.
        return PWRunnerSandboxCheckResult(
            rc: predictionUnavailableRC,
            outcome: SandboxCheckOutcome.predictionUnavailable,
            pid: pid,
            operation: op,
            scope: PWRunnerWire.sandboxCheckScopePost,
            filter_kind: filterKind,
            filter_value: filterValue,
            effective_filter_value: filterValue,
            filter_type_id: nil,
            errno: nil,
            error: nil,
            path_diagnostics: nil
        )
    }

    if filterKind == PWRunnerWire.sandboxFilterPath, let value = filterValue, !value.isEmpty {
        // effective_filter_value is the worker's canonicalized form of
        // the filter value; sandbox_check still gets the raw filterValue
        // below (the worker passes the user-authored string through to
        // libsandbox so policy matching matches whatever the user
        // wrote).
        let canonical = canonicalizePath(value)
        effectiveFilterValue = canonical.normalized
        // path_diagnostics was previously computed here. It now lands
        // on the response via host-side enrichment in
        // PWRunnerService.runSpecimen — the host is unsandboxed, so
        // realpath(3) is reliable there even under a worker (deny
        // default) policy that would block the stat. See
        // PolicyWitness.md "path_diagnostics" for the producer change
        // and the more-reliable realpath_resolved semantics.
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
        error: errMsg,
        path_diagnostics: nil
    )
}

func runAttempt(_ attempt: PWRunnerAttempt) -> PWRunnerAttemptResult {
    switch attempt.kind {
    case PWRunnerWire.attemptKindFile:
        return runFileAttempt(action: attempt.action, path: attempt.target)
    case PWRunnerWire.attemptKindMachLookup:
        return runMachLookupAttempt(action: attempt.action, name: attempt.target)
    default:
        return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: AttemptOutcome.unsupported, error: "unsupported attempt.kind")
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
                outcome: AttemptOutcome.openFailed,
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
            outcome: AttemptOutcome.ok,
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
                outcome: AttemptOutcome.openFailed,
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
            outcome: AttemptOutcome.ok,
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
                outcome: AttemptOutcome.openFailed,
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
            outcome: AttemptOutcome.ok,
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
                outcome: AttemptOutcome.unlinkFailed,
                error: String(cString: strerror(errno)),
                requested_path: requestedPath,
                normalized_path: normalizedPath,
                observed_path: nil
            )
        }
        return PWRunnerAttemptResult(
            rc: 0,
            errno: nil,
            outcome: AttemptOutcome.ok,
            error: nil,
            requested_path: requestedPath,
            normalized_path: normalizedPath,
            observed_path: nil
        )

    default:
        return PWRunnerAttemptResult(
            rc: 1,
            errno: nil,
            outcome: AttemptOutcome.unsupported,
            error: "unsupported file action",
            requested_path: requestedPath,
            normalized_path: normalizedPath,
            observed_path: nil
        )
    }
}

private func runMachLookupAttempt(action: String, name: String) -> PWRunnerAttemptResult {
    guard action == PWRunnerWire.attemptActionMachLookup else {
        return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: AttemptOutcome.unsupported, error: "unsupported mach_lookup action")
    }

    // Use the task bootstrap port to mirror how launchd resolves Mach services.
    var bootstrap: mach_port_t = 0
    let kr = task_get_special_port(mach_task_self_, task_special_port_t(TASK_BOOTSTRAP_PORT), &bootstrap)
    if kr != KERN_SUCCESS {
        return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: AttemptOutcome.bootstrapPortFailed, error: "task_get_special_port failed kr=\(kr)")
    }

    var servicePort: mach_port_t = 0
    let kr2: kern_return_t = name.withCString { ptr in
        bootstrap_look_up(bootstrap, ptr, &servicePort)
    }
    if kr2 != KERN_SUCCESS {
        return PWRunnerAttemptResult(rc: 1, errno: nil, outcome: AttemptOutcome.lookupFailed, error: "bootstrap_look_up failed kr=\(kr2)")
    }
    mach_port_deallocate(mach_task_self_, servicePort)
    return PWRunnerAttemptResult(rc: 0, errno: nil, outcome: AttemptOutcome.ok, error: nil)
}

// Best-effort "am I sandboxed" check for reporting purposes.
// Returns false on unexpected sandbox_check errors.
func currentProcessIsSandboxed() -> Bool {
    var err: Int32 = 0
    let rc = pw_sandbox_check_noarg(getpid(), nil, &err)
    return rc == 1
}

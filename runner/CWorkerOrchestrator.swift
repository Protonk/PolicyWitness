import Darwin
import Foundation

/*
 * CWorkerOrchestrator — host-side wiring that runs a single specimen
 * through the runner's C code path: pw-probe-runner for attempts +
 * sb_api_validator --batch for sandbox_check verdicts, joined into
 * one PWRunnerRunResult envelope.
 *
 * The orchestrator owns:
 *   1. Request → driver inputs translation:
 *        - probe_plan → [CWorkerSlotInput] (worker attempts)
 *        - probe_plan → [ValidatorProbe] (validator queries),
 *          skipping (op, filter) pairs in
 *          ProbeRunner.predictionUnavailableOpFilters
 *        - policy.params → [CWorkerParam]
 *   2. Driver invocation:
 *        - runCWorker(...) with a postApplied hook that runs
 *          runValidator against the sandboxed worker_pid
 *   3. Driver outputs → per-step PWRunnerStepResult:
 *        - sandbox_check from validator verdict OR synthesized
 *          prediction_unavailable result for skipped pairs
 *        - attempt from CWorker slot result
 *        - drift = boolean comparison or nil (see drift helper for
 *          the asymmetry rule)
 *   4. Classifier:
 *        - normalized_outcome from C-worker disposition +
 *          validator disposition + per-slot completed/done state
 *
 * Validation, libsandbox-availability checks, and policy-hash
 * computation are PWRunnerService.runSpecimen's responsibility.
 * The orchestrator only sees a request that has already passed
 * those gates.
 */

public enum CWorkerOrchestrator {

    // ---- entry point -----------------------------------------------------

    public static func run(
        parsed: PWRunnerRunSpec,
        policyHash: String,
        bundleId: String?,
        workerExecutablePath: String,
        validatorExecutablePath: String
    ) -> PWRunnerRunResult {
        let stepCount = parsed.probe_plan.count

        // ---- translation: request → driver inputs ------------------------
        let workerSlots = workerSlotsFromProbePlan(parsed.probe_plan)
        let workerParams = workerParamsFromPolicy(parsed.policy)
        let validatorProbes = validatorProbesFromProbePlan(parsed.probe_plan)

        // _test_overrides.worker_timeout_ms drives the sentinel
        // deadline on the C-worker path. Floored at 50 ms because a
        // smaller deadline fires before any real worker can complete
        // its post-apply work and would just generate spurious
        // runner_timeouts.
        let workerInput = CWorkerInput(
            workerExecutablePath: workerExecutablePath,
            policy: parsed.policy.sbpl_source ?? "",
            params: workerParams,
            slots: workerSlots,
            sentinelTimeoutMs: timeoutMsForCWorker(
                override: parsed._test_overrides?.worker_timeout_ms
            ),
            postApplyHangMs: parsed._test_overrides?.worker_post_apply_hang_ms
        )

        // ---- run worker + validator together via postApplied hook --------
        var validatorResult: ValidatorClientResult? = nil
        let workerResult = runCWorker(workerInput) { workerPid in
            // Skip validator entirely when every step's (op, filter) is
            // in the prediction_unavailable set: no probes to send means
            // no useful validator work. Avoids spawning a child only to
            // immediately reap it.
            if validatorProbes.isEmpty { return }
            let vInput = ValidatorClientInput(
                executablePath: validatorExecutablePath,
                targetPid: workerPid,
                probes: validatorProbes
            )
            validatorResult = runValidator(vInput)
        }

        // ---- assemble + classify -----------------------------------------
        let runOutcome = classify(
            workerResult: workerResult,
            validatorResult: validatorResult,
            expectedVerdictCount: validatorProbes.count
        )

        let workerOutput = unwrapWorkerOutput(workerResult)
        let validatorOutput = unwrapValidatorOutput(validatorResult)

        let stepResults = buildStepResults(
            probePlan: parsed.probe_plan,
            workerOutput: workerOutput,
            validatorOutput: validatorOutput
        )

        let topPid: Int = workerOutput.map { Int($0.workerPid) } ?? Int(getpid())
        let runnerSubprocess = workerOutput.map { out in
            PWRunnerSubprocess(
                pid: Int(out.workerPid),
                term_signal: out.termSignal.map { Int($0) },
                exit_code: out.exitCode.map { Int($0) },
                partial_steps: anySlotNotCompleted(out.slots)
            )
        }
        let validatorSubprocess = validatorOutput.map {
            PWRunnerValidatorSubprocess(
                pid: Int($0.validatorPid),
                term_signal: $0.termSignal.map { Int($0) },
                exit_code: $0.exitCode.map { Int($0) }
            )
        }

        _ = stepCount  // referenced for future partial-step logic; silence unused warning

        return PWRunnerRunResult(
            specimen_id: parsed.specimen_id,
            run_kind: parsed.run_kind,
            rc: runOutcome.rc,
            normalized_outcome: runOutcome.outcome,
            error: runOutcome.error,
            pid: topPid,
            bundle_id: bundleId,
            policy_format: parsed.policy.format,
            policy_sha256: policyHash,
            sandboxed_after_apply: workerOutput?.applied,
            deny_signal_total: nil,
            steps: stepResults,
            runner_subprocess: runnerSubprocess,
            validator_subprocess: validatorSubprocess,
            test_overrides: parsed._test_overrides
        )
    }

    // ---- bundle path resolution -----------------------------------------

    /// pw-probe-runner lives at `<this xpc service>/Contents/MacOS/pw-probe-runner`.
    /// The XPC service binary itself lives at
    /// `<this xpc service>/Contents/MacOS/<service-name>` — Bundle.main
    /// resolves to the service bundle. Sibling resolution.
    public static func defaultWorkerExecutablePath() -> String {
        let bundleURL = Bundle.main.bundleURL
        return bundleURL
            .appendingPathComponent("Contents/MacOS/pw-probe-runner")
            .path
    }

    /// sb_api_validator is embedded both bundle-local (alongside
    /// pw-probe-runner inside each XPC service) AND at the app's
    /// top-level. The bundle-local copy is preferred so BYOXPC
    /// runners — which live outside any app bundle — still find a
    /// validator. The app-level path is the fallback for older
    /// layouts where the bundle-local copy may be missing.
    public static func defaultValidatorExecutablePath() -> String {
        let bundleURL = Bundle.main.bundleURL
        let bundleLocal = bundleURL
            .appendingPathComponent("Contents/MacOS/sb_api_validator")
            .path
        if FileManager.default.isExecutableFile(atPath: bundleLocal) {
            return bundleLocal
        }
        let appURL = bundleURL
            .deletingLastPathComponent()   // XPCServices/
            .deletingLastPathComponent()   // Contents/
            .deletingLastPathComponent()   // <app>.app/
        return appURL
            .appendingPathComponent("Contents/MacOS/sb_api_validator")
            .path
    }

    // ---- validation -----------------------------------------------------

    /// Pre-spawn validation specific to the C-worker code path.
    /// Returns a human-readable error string when the plan is
    /// malformed; nil when it's safe to orchestrate. Callers map a
    /// non-nil return to bad_request.
    ///
    /// Only one plan-killing check today: step_ids must be unique.
    /// The orchestrator joins the worker's per-slot outputs and the
    /// validator's verdicts back to steps by step_id; a duplicate
    /// would crash the Dictionary(uniqueKeysWithValues:) constructor
    /// and kill the XPC service.
    ///
    /// Unsupported (attempt.kind, attempt.action) combos are NOT
    /// plan-killers — they downgrade to per-step
    /// `attempt.outcome = "unsupported"` in the step builder,
    /// mirroring the per-step skip behavior for unknown filter
    /// kinds. The slot is mapped to PW_ATTEMPT_NONE so the C worker
    /// no-ops it; the validator's sandbox_check verdict for that
    /// step still runs.
    public static func validateProbePlanForCWorker(_ plan: [PWRunnerProbeStep]) -> String? {
        var seenStepIds: Set<String> = []
        seenStepIds.reserveCapacity(plan.count)
        for step in plan {
            if !seenStepIds.insert(step.step_id).inserted {
                return "duplicate step_id '\(step.step_id)' in probe_plan"
            }
        }
        return nil
    }
}

// MARK: - Helpers

/// Resolve the sentinel-timeout for the C worker from the request's
/// `_test_overrides.worker_timeout_ms`. Floor at 50 ms because a
/// smaller deadline fires before any real worker can complete its
/// post-apply work. nil/absent → CWorkerInput default (60s — long
/// enough for any real specimen).
private func timeoutMsForCWorker(override: Int?) -> Int {
    let cWorkerDefault = 60_000
    guard let v = override else { return cWorkerDefault }
    return max(50, v)
}

// MARK: - Translation: request → driver inputs

private func workerSlotsFromProbePlan(_ plan: [PWRunnerProbeStep]) -> [CWorkerSlotInput] {
    return plan.map { step in
        // Exec attempts pass argv[1..N] via attempt.args; other kinds
        // ignore the field. Defensive: only thread the args when the
        // resolved attempt kind is .execSpawn so a caller that
        // mistakenly populates args on a file probe doesn't pay the
        // shm-write cost for ignored bytes.
        let kind = mapAttemptKind(step.attempt)
        let args: [String] = (kind == .execSpawn) ? (step.attempt.args ?? []) : []
        return CWorkerSlotInput(
            stepId: step.step_id,
            attemptKind: kind,
            target: step.attempt.target,
            args: args
        )
    }
}

/// (kind, action) → C-worker PWAttemptKind. Returns nil for any
/// combo the C worker can't execute. The orchestrator falls back
/// to PW_ATTEMPT_NONE (worker no-ops the slot) and the step builder
/// then emits `attempt.outcome = "unsupported"` so the rc=0 slot
/// isn't misread as a successful observation.
private func mapAttemptKindOrNil(_ attempt: PWRunnerAttempt) -> PWAttemptKind? {
    switch (attempt.kind, attempt.action) {
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionOpenRead):
        return .fileOpenRead
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionOpenWrite):
        return .fileOpenWrite
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionCreate):
        return .fileCreate
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionUnlink):
        return .fileUnlink
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionAccess):
        return .fileAccess
    case (PWRunnerWire.attemptKindMachLookup, PWRunnerWire.attemptActionMachLookup):
        return .machLookup
    case (PWRunnerWire.attemptKindSysctl, PWRunnerWire.attemptActionRead):
        return .sysctlRead
    case (PWRunnerWire.attemptKindExec, PWRunnerWire.attemptActionSpawn):
        return .execSpawn
    default:
        return nil
    }
}

/// Fallback variant used for the shm slot. Unsupported attempts map to
/// PW_ATTEMPT_NONE so the worker no-ops the slot; buildAttemptResult
/// later surfaces the per-step `unsupported` outcome.
private func mapAttemptKind(_ attempt: PWRunnerAttempt) -> PWAttemptKind {
    return mapAttemptKindOrNil(attempt) ?? .none
}

private func workerParamsFromPolicy(_ policy: PWRunnerPolicySpec) -> [CWorkerParam] {
    guard let dict = policy.params, !dict.isEmpty else { return [] }
    // Sort by key for a stable order — easier to debug, and the
    // C worker iterates the array in order so deterministic param
    // ordering helps when comparing runs.
    return dict.keys.sorted().map { CWorkerParam(key: $0, value: dict[$0] ?? "") }
}

private func validatorProbesFromProbePlan(_ plan: [PWRunnerProbeStep]) -> [ValidatorProbe] {
    var probes: [ValidatorProbe] = []
    probes.reserveCapacity(plan.count)
    for step in plan {
        let kind = step.sandbox_check.filter.kind
        let opFilterPair = PredictionUnavailablePair(
            operation: step.sandbox_check.operation,
            filterKind: kind
        )
        if predictionUnavailableOpFiltersHostMirror.contains(opFilterPair) {
            // Don't ask the validator about this pair. The verdict is
            // synthesized as prediction_unavailable in the step builder.
            continue
        }
        if !knownFilterKinds.contains(kind) {
            // Unknown filter kind: skip the validator probe and let the
            // step builder synthesize prediction_unavailable. Avoids
            // killing the whole plan when a specimen mixes a recognized
            // probe with one whose filter kind hasn't been verified.
            continue
        }
        // Per-step path-resolution gate: when the path filter doesn't
        // resolve via realpath, the kernel won't reach a sandbox
        // decision (file ops ENOENT first), so any libsandbox verdict
        // for the path is a userland canonicalization artifact rather
        // than a kernel prediction. Skip the validator probe; the
        // step builder synthesizes prediction_unavailable so consumers
        // see the prediction was honestly absent rather than wrong.
        if pathFilterIsUnresolvable(kind, step.sandbox_check.filter.value) {
            continue
        }
        // NONE-filter probes must not carry a filter_value in the
        // validator wire (the validator rejects it as bad_filter).
        // Callers commonly pass "" for kind=none — coerce that to nil.
        let filterValue: String? = (kind == PWRunnerWire.sandboxFilterNone)
            ? nil
            : step.sandbox_check.filter.value
        probes.append(ValidatorProbe(
            stepId: step.step_id,
            operation: step.sandbox_check.operation,
            filterType: mapFilterKindToValidator(kind),
            filterValue: filterValue
        ))
    }
    return probes
}

/// True when the step's filter is a path whose value does not
/// resolve on the host via realpath. The kernel's file-op vectors
/// (open, access, …) ENOENT before they reach the sandbox layer for
/// absent paths, so a libsandbox verdict for such a path is a
/// userland artifact, not a kernel prediction. We skip the
/// validator probe and synthesize prediction_unavailable for these
/// steps; the attempt channel still runs and carries the real
/// observation. NONE-filter and resolvable paths are unaffected.
private func pathFilterIsUnresolvable(_ kind: String, _ value: String?) -> Bool {
    guard kind == PWRunnerWire.sandboxFilterPath else { return false }
    guard let v = value, !v.isEmpty else { return false }
    return canonicalizePath(v).resolved == nil
}

/// Host-side mirror of ProbeRunner's predictionUnavailableOpFilters.
/// The orchestrator skips validator probes for these pairs and
/// synthesizes prediction_unavailable verdicts directly. source_drift
/// already enforces three-way agreement on the underlying pair set.
private let predictionUnavailableOpFiltersHostMirror: Set<PredictionUnavailablePair> = [
    .init(operation: "iokit-open-service",
          filterKind: PWRunnerWire.sandboxFilterIokitRegistryEntryClass),
    .init(operation: "iokit-open-user-client",
          filterKind: PWRunnerWire.sandboxFilterIokitUserClientClass),
    .init(operation: "sysctl-read",
          filterKind: PWRunnerWire.sandboxFilterSysctlName),
]

private func mapFilterKindToValidator(_ wireKind: String) -> String {
    switch wireKind {
    case PWRunnerWire.sandboxFilterNone:                     return "NONE"
    case PWRunnerWire.sandboxFilterPath:                     return "PATH"
    case PWRunnerWire.sandboxFilterGlobalName:               return "GLOBAL_NAME"
    case PWRunnerWire.sandboxFilterLocalName:                return "LOCAL_NAME"
    case PWRunnerWire.sandboxFilterIokitRegistryEntryClass:  return "IOKIT_REGISTRY_ENTRY_CLASS"
    case PWRunnerWire.sandboxFilterIokitUserClientClass:     return "IOKIT_USER_CLIENT_CLASS"
    case PWRunnerWire.sandboxFilterSysctlName:               return "SYSCTL_NAME"
    default:
        // validateSandboxChecks already rejected unknown kinds; this
        // branch shouldn't fire. Emit the literal so a future extension
        // pre-validateSandboxChecks fails loudly via the validator's
        // bad_filter response.
        return wireKind.uppercased()
    }
}

// MARK: - Driver-result unwrapping

private func unwrapWorkerOutput(_ result: CWorkerRunResult) -> CWorkerOutput? {
    switch result {
    case .success(let out): return out
    case .failure:          return nil
    }
}

private func unwrapValidatorOutput(_ result: ValidatorClientResult?) -> ValidatorOutput? {
    guard let result else { return nil }
    switch result {
    case .success(let out):       return out
    case .failure(_, let partial): return partial   // degraded evidence is still evidence
    }
}

// MARK: - Step builder

private func buildStepResults(
    probePlan: [PWRunnerProbeStep],
    workerOutput: CWorkerOutput?,
    validatorOutput: ValidatorOutput?
) -> [PWRunnerStepResult] {
    // Index outputs by step_id for the join.
    let workerSlotsByStep: [String: CWorkerSlotResult] = Dictionary(
        uniqueKeysWithValues: (workerOutput?.slots ?? []).map { ($0.stepId, $0) }
    )
    let verdictsByStep: [String: ValidatorVerdict] = Dictionary(
        uniqueKeysWithValues: (validatorOutput?.verdicts ?? []).compactMap { v in
            v.stepId.map { ($0, v) }
        }
    )

    // sandbox_check.pid is consistently the sandboxed worker PID so
    // unified-log correlation can use a single PID per run, and so
    // validator-backed AND synthesized verdicts carry the same per-step
    // pid. Falls back to the host PID only when no worker exists (spawn
    // failed before pid was known).
    let sbCheckPid = Int(workerOutput?.workerPid ?? pid_t(getpid()))

    var results: [PWRunnerStepResult] = []
    results.reserveCapacity(probePlan.count)
    for step in probePlan {
        let sandboxCheck = buildSandboxCheckResult(
            step: step,
            verdict: verdictsByStep[step.step_id],
            sandboxCheckPid: sbCheckPid
        )
        let attempt = buildAttemptResult(
            step: step,
            slot: workerSlotsByStep[step.step_id]
        )
        let drift = computeDrift(sandboxCheck: sandboxCheck, attempt: attempt)
        let stepResult = PWRunnerStepResult(
            step_id: step.step_id,
            sandbox_check: sandboxCheck,
            attempt: attempt,
            deny_signal: zeroSignalResult(),
            drift: drift
        )
        results.append(stepResult)
    }
    return results
}

private func buildSandboxCheckResult(
    step: PWRunnerProbeStep,
    verdict: ValidatorVerdict?,
    sandboxCheckPid: Int
) -> PWRunnerSandboxCheckResult {
    let opFilterPair = PredictionUnavailablePair(
        operation: step.sandbox_check.operation,
        filterKind: step.sandbox_check.filter.kind
    )
    let scope = PWRunnerWire.sandboxCheckScopePost
    let kind = step.sandbox_check.filter.kind
    let value = step.sandbox_check.filter.value

    // Synthesize prediction_unavailable in three cases that share
    // the wire shape:
    //
    //   (a) a known op+filter pair that empirically drifts from
    //       kernel enforcement (iokit/sysctl families);
    //   (b) a filter kind the runner doesn't know how to validate
    //       (e.g. preference_domain, mach_port);
    //   (c) per-step host condition: a path-filter value that
    //       doesn't resolve via realpath. For absent paths the
    //       kernel never reaches a sandbox decision (file-* ops
    //       ENOENT first), so whatever verdict libsandbox returns
    //       is a userland-side canonicalization artifact, not a
    //       prediction the kernel would produce. We surface the
    //       gate's reason in `error` so a consumer can see which
    //       branch fired without having to inspect path_diagnostics.
    //
    // In all three cases the validator wasn't asked, the attempt
    // is the reliable evidence, and the consumer-visible shape is
    // identical (rc=-1, drift=null).
    if predictionUnavailableOpFiltersHostMirror.contains(opFilterPair)
        || !knownFilterKinds.contains(kind) {
        return PWRunnerSandboxCheckResult(
            rc: -1,
            outcome: SandboxCheckOutcome.predictionUnavailable,
            pid: sandboxCheckPid,
            operation: step.sandbox_check.operation,
            scope: scope,
            filter_kind: kind,
            filter_value: value,
            effective_filter_value: value,
            filter_type_id: nil,
            errno: nil,
            error: nil,
            path_diagnostics: nil
        )
    }
    if pathFilterIsUnresolvable(kind, value) {
        // path_diagnostics is added later by PWRunnerService's
        // enrichPathDiagnostics pass (which always runs for
        // path-kind results), so a consumer can still see
        // realpath_resolved=null alongside this outcome.
        let target = value ?? ""
        return PWRunnerSandboxCheckResult(
            rc: -1,
            outcome: SandboxCheckOutcome.predictionUnavailable,
            pid: sandboxCheckPid,
            operation: step.sandbox_check.operation,
            scope: scope,
            filter_kind: kind,
            filter_value: value,
            effective_filter_value: value,
            filter_type_id: nil,
            errno: nil,
            error: "target path \(target.debugDescription) did not resolve on the host; "
                + "the kernel ENOENTs file-* access before reaching the sandbox check, "
                + "so libsandbox's verdict for this path is not a kernel prediction",
            path_diagnostics: nil
        )
    }

    // Validator didn't return a verdict for this step (validator never
    // ran, or it died mid-stream and this step was past the partial
    // cutoff). Surface as outcome=error so consumers see the gap.
    guard let v = verdict else {
        return PWRunnerSandboxCheckResult(
            rc: 0,
            outcome: SandboxCheckOutcome.error,
            pid: sandboxCheckPid,
            operation: step.sandbox_check.operation,
            scope: scope,
            filter_kind: kind,
            filter_value: value,
            effective_filter_value: value,
            filter_type_id: nil,
            errno: nil,
            error: "no validator verdict for this step",
            path_diagnostics: nil
        )
    }

    return PWRunnerSandboxCheckResult(
        rc: v.rc ?? -1,
        outcome: mapValidatorOutcomeToSandboxCheckOutcome(v.outcome),
        pid: sandboxCheckPid,
        operation: v.operation ?? step.sandbox_check.operation,
        scope: scope,
        filter_kind: kind,
        filter_value: value,
        effective_filter_value: value,
        filter_type_id: v.filterTypeId,
        errno: v.errnoVal,
        error: v.error,
        path_diagnostics: nil
    )
}

/// The validator emits its own outcome vocabulary (allow / deny /
/// error / unsupported_operation / parse_error / bad_filter). Map
/// to the host's SandboxCheckOutcome catalog:
///   - allow / deny → same
///   - unsupported_operation → same (distinct outcome so consumers
///     can route bare-op-name failures as per-step skips rather
///     than runtime errors; the validator's error string is
///     threaded through PWRunnerSandboxCheckResult.error)
///   - everything else (error / parse_error / bad_filter / unknown)
///     folds into SandboxCheckOutcome.error with the validator's
///     own error string in the error field via the verdict itself
///     (set upstream)
private func mapValidatorOutcomeToSandboxCheckOutcome(_ vOutcome: String) -> String {
    switch vOutcome {
    case "allow":                  return SandboxCheckOutcome.allow
    case "deny":                   return SandboxCheckOutcome.deny
    case "unsupported_operation":  return SandboxCheckOutcome.unsupportedOperation
    default:                       return SandboxCheckOutcome.error
    }
}

private func buildAttemptResult(
    step: PWRunnerProbeStep,
    slot: CWorkerSlotResult?
) -> PWRunnerAttemptResult {
    // Unsupported attempt (kind, action): the orchestrator routed
    // the slot to PW_ATTEMPT_NONE so the worker no-ops it; surface
    // that here as outcome="unsupported" rather than letting the
    // rc=0 no-op masquerade as a successful "ok" observation. The
    // sandbox_check verdict for this step still runs and gets
    // attached normally; drift falls out as null because the
    // attempt didn't produce an allow/deny verdict.
    if mapAttemptKindOrNil(step.attempt) == nil {
        return PWRunnerAttemptResult(
            rc: -1,
            errno: nil,
            outcome: AttemptOutcome.unsupported,
            error: "kind='\(step.attempt.kind)', action='\(step.attempt.action)' not implemented",
            requested_path: step.attempt.target,
            normalized_path: nil,
            observed_path: nil
        )
    }
    // Slot missing → worker never reached the step. Surface as
    // not_run_worker_died so consumers can tell "the attempt failed"
    // (slot present, rc non-zero) from "the attempt never ran"
    // (slot missing).
    guard let s = slot else {
        return PWRunnerAttemptResult(
            rc: -1,
            errno: nil,
            outcome: AttemptOutcome.notRunWorkerDied,
            error: "worker exited before reaching this slot",
            requested_path: step.attempt.target,
            normalized_path: nil,
            observed_path: nil
        )
    }
    if !s.completed {
        return PWRunnerAttemptResult(
            rc: -1,
            errno: nil,
            outcome: AttemptOutcome.notRunWorkerDied,
            error: "worker exited before this slot completed",
            requested_path: step.attempt.target,
            normalized_path: nil,
            observed_path: nil
        )
    }

    // Slot completed. Map the C-worker rc/errno into the host's
    // attempt outcome vocabulary. The error string the worker wrote
    // already names which call failed (open / unlink / etc).
    //
    // Exec attempts are special: rc != 0 may mean either spawn-failed
    // (child_pid == 0) or child-exited-non-zero (child_pid > 0). Both
    // map to outcome=exec_failed, but the drift classifier uses
    // child_pid downstream to distinguish them.
    let outcome: String = {
        if s.rc == 0 {
            return AttemptOutcome.ok
        }
        // Dispatch on the attempt action rather than parsing the worker's
        // error string — the requested action is authoritative.
        switch step.attempt.action {
        case PWRunnerWire.attemptActionOpenRead,
             PWRunnerWire.attemptActionOpenWrite,
             PWRunnerWire.attemptActionCreate:
            return AttemptOutcome.openFailed
        case PWRunnerWire.attemptActionUnlink:
            return AttemptOutcome.unlinkFailed
        case PWRunnerWire.attemptActionAccess:
            return AttemptOutcome.accessFailed
        case PWRunnerWire.attemptActionMachLookup:
            return AttemptOutcome.lookupFailed
        case PWRunnerWire.attemptActionRead:
            return AttemptOutcome.sysctlFailed
        case PWRunnerWire.attemptActionSpawn:
            return AttemptOutcome.execFailed
        default:
            return AttemptOutcome.unsupported
        }
    }()

    return PWRunnerAttemptResult(
        rc: Int(s.rc),
        errno: s.errnoVal == 0 ? nil : Int(s.errnoVal),
        outcome: outcome,
        error: s.error,
        requested_path: step.attempt.target,
        normalized_path: nil,        // path canonicalization for file
                                     // attempts is left to host-side
                                     // enrichment (see enrichPathDiagnostics)
        observed_path: s.observedPath,
        child_pid: s.childPid.map { Int($0) },
        child_exit_code: s.childExitCode.map { Int($0) },
        child_term_signal: s.childTermSignal.map { Int($0) },
        stdout: s.childStdout,
        stderr: s.childStderr
    )
}

// `internal` (not `private`) so DriftClassifierTests can drive the
// validator-vs-kernel truth table directly. This is the conceptual
// core of PolicyWitness — the test pins the *semantics* of every
// (predicted, observed) cell so the classifier can be reorganized,
// split, or moved without silently changing what "drift" means.
func computeDrift(
    sandboxCheck: PWRunnerSandboxCheckResult,
    attempt: PWRunnerAttemptResult
) -> Bool? {
    // drift is the validator-vs-attempt disagreement about *sandbox
    // enforcement* — not just any allow/deny disagreement.
    //
    // An ENOENT file open or a BOOTSTRAP_UNKNOWN_SERVICE mach lookup
    // is a failure but NOT a sandbox denial — the file doesn't exist,
    // the service doesn't exist. Treating those as "kernel denied" when
    // the validator predicted allow would flood the envelope with
    // false libsandbox-drift signals.
    //
    // Asymmetric: EPERM/EACCES on a file op is AMBIGUOUS — the kernel
    // sandbox produces those errnos, but so does ordinary Unix DAC
    // (chmod 000, owner mismatch, etc). Without a deny-event-log
    // cross-reference we can't tell the two apart from rc/errno alone.
    // So:
    //   - (validator=allow, observation=ambiguous-deny) → nil
    //     ("we observed a failure but can't attribute it to libsandbox")
    //   - (validator=deny,  observation=ambiguous-deny) → false
    //     ("agreement on direction — small risk of crediting libsandbox
    //      for a DAC denial, accepted because the signal is mostly right")
    // Mach kr=1100 is unambiguous (no DAC analogue) so it always
    // counts as strong sandbox evidence.
    let observation = observationFromAttempt(attempt)
    switch (sandboxCheck.outcome, observation) {
    case (SandboxCheckOutcome.allow, .allowed):                return false
    case (SandboxCheckOutcome.allow, .deniedStrongEvidence):   return true   // libsandbox drift
    case (SandboxCheckOutcome.allow, .deniedAmbiguous):        return nil    // could be DAC, not sandbox
    case (SandboxCheckOutcome.deny,  .allowed):                return true   // libsandbox drift
    case (SandboxCheckOutcome.deny,  .deniedStrongEvidence):   return false
    case (SandboxCheckOutcome.deny,  .deniedAmbiguous):        return false  // directional agreement
    default:                                                    return nil
    }
}

private enum AttemptObservation {
    case allowed                 // attempt.outcome == ok
    case deniedStrongEvidence    // mach kr=1100 or sysctl errno that has no
                                 //   known non-policy analogue here
    case deniedAmbiguous         // file EPERM/EACCES (sandbox OR DAC; can't
                                 //   tell from rc/errno alone)
    case undefined               // ENOENT, missing service, unsupported,
                                 //   worker died — failures that aren't
                                 //   themselves sandbox verdicts
}

private func observationFromAttempt(_ attempt: PWRunnerAttemptResult) -> AttemptObservation {
    if attempt.outcome == AttemptOutcome.ok {
        return .allowed
    }
    switch attempt.outcome {
    case AttemptOutcome.openFailed,
         AttemptOutcome.unlinkFailed,
         AttemptOutcome.accessFailed:
        // POSIX file ops: EPERM (1) and EACCES (13) are the kernel's
        // sandbox-deny signals — but they're also ordinary Unix DAC
        // signals (mode bits, owner mismatch, immutable flag, etc.).
        // Classify as deniedAmbiguous so the drift logic above can
        // suppress false libsandbox-drift attribution when the
        // validator's prediction is allow.
        switch attempt.errno {
        case Int(EPERM), Int(EACCES): return .deniedAmbiguous
        default:                       return .undefined
        }
    case AttemptOutcome.lookupFailed:
        // bootstrap_look_up returns BOOTSTRAP_NOT_PRIVILEGED (1100)
        // when the kernel sandbox denies the lookup, and
        // BOOTSTRAP_UNKNOWN_SERVICE (1102) when the service simply
        // isn't registered. Only the former is a sandbox verdict.
        // The worker writes the kr verbatim into attempt.error as
        // "bootstrap_look_up: kr=<N>"; parse that substring.
        if let msg = attempt.error, msg.contains("kr=1100") {
            return .deniedStrongEvidence
        }
        return .undefined
    case AttemptOutcome.sysctlFailed:
        switch attempt.errno {
        case Int(EPERM), Int(EACCES):
            return .deniedAmbiguous
        case Int(ENOENT), Int(ENOMEM):
            return .undefined
        case .some(_):
            return .deniedStrongEvidence
        case .none:
            return .undefined
        }
    case AttemptOutcome.execFailed:
        // Exec drift attribution keys on child_pid:
        //   child_pid > 0  → spawn succeeded; rc carries the helper's
        //                    own exit code, which is not a sandbox
        //                    verdict. Treat as non-policy failure.
        //   child_pid == 0 → spawn never produced a child. errno carries
        //                    the posix_spawn errno. EPERM / EACCES are
        //                    the kernel sandbox's spawn deny signals
        //                    (no DAC analogue for spawn itself —
        //                    unlike file ops, posix_spawn's deny is a
        //                    clean sandbox tell). ENOENT means the
        //                    target binary doesn't exist; other errnos
        //                    are non-policy reasons (out of fds, etc).
        let childPid = attempt.child_pid ?? 0
        if childPid > 0 {
            return .undefined
        }
        switch attempt.errno {
        case Int(EPERM), Int(EACCES):
            return .deniedStrongEvidence
        default:
            return .undefined
        }
    case AttemptOutcome.bootstrapPortFailed,
         AttemptOutcome.unsupported,
         AttemptOutcome.notRunWorkerDied:
        // Setup or shape failures — the syscall the policy would
        // gate never ran. No verdict to surface.
        return .undefined
    default:
        return .undefined
    }
}

private func zeroSignalResult() -> PWRunnerSignalResult {
    // PWRunnerSignalResult: signal name + before/after counts + delta.
    // The C worker doesn't yet observe per-step deny signals — the
    // host doesn't share a signal handler with it. The field is
    // zeroed for now; a future chunk can wire in a per-slot signal
    // counter if the data turns out to matter.
    return PWRunnerSignalResult(signal: "SIGUSR1", count_before: 0, count_after: 0)
}

private func anySlotNotCompleted(_ slots: [CWorkerSlotResult]) -> Bool {
    return slots.contains { !$0.completed }
}

// MARK: - Classifier

private struct ClassifiedRun {
    let outcome: String
    let rc: Int
    let error: String?
}

private func classify(
    workerResult: CWorkerRunResult,
    validatorResult: ValidatorClientResult?,
    expectedVerdictCount: Int
) -> ClassifiedRun {
    // Worker side first — its failure modes are more severe (the
    // attempt channel is the load-bearing observation; without it the
    // validator's predictions have nothing to compare against).
    switch workerResult {
    case .failure(let err):
        switch err {
        case .slotCountExceeded, .paramCountExceeded,
             .slotInputTooLong, .paramInputTooLong,
             .argvCountExceeded, .argvEntryTooLong,
             .execTargetNotAbsolute:
            return ClassifiedRun(outcome: NormalizedOutcome.badRequest,
                                 rc: 1, error: err.description)
        case .shmSetupFailed, .pipeFailed, .policyWriteFailed:
            return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed,
                                 rc: 1, error: err.description)
        case .spawnFailed:
            return ClassifiedRun(outcome: NormalizedOutcome.workerSpawnFailed,
                                 rc: 1, error: err.description)
        }
    case .success(let out):
        if !out.applied {
            // sandbox_apply failed inside the worker. apply_rc carries
            // the cause (the worker writes it to shm before flipping
            // done and entering the spin loop). Compile failure follows
            // the same path.
            return ClassifiedRun(
                outcome: NormalizedOutcome.sandboxApplyFailed,
                rc: 1,
                error: "sandbox_apply returned \(out.applyRC) inside pw-probe-runner"
            )
        }
        // sentSigkill means the HOST sent SIGKILL after its grace
        // timer expired. The worker's termSignal=9 is then evidence
        // of the host's kill, NOT of a sandbox denial. Always classify
        // as runner_timeout in that case. Only consider termSignal as
        // sandbox-denial evidence when the worker died from a signal
        // we did NOT send.
        if out.sentSigkill {
            return ClassifiedRun(
                outcome: NormalizedOutcome.runnerTimeout,
                rc: 1,
                error: "pw-probe-runner did not flip done within sentinel deadline; host SIGKILL grace fired"
            )
        }
        if !out.done {
            // done sentinel never flipped AND host didn't SIGKILL — the
            // worker exited on its own without writing done. If it
            // exited from a signal, attribute that to the sandbox
            // (the worker's post-apply syscall surface is tiny; the
            // most likely external cause is a sandbox kill). Otherwise
            // surface as runner_timeout — the worker exited cleanly
            // but failed to write done within the sentinel window.
            if let sig = out.termSignal, sig != 0 {
                return ClassifiedRun(
                    outcome: NormalizedOutcome.runnerSandboxDenied,
                    rc: 1,
                    error: "pw-probe-runner exited with signal \(sig) before flipping done"
                )
            }
            return ClassifiedRun(
                outcome: NormalizedOutcome.runnerTimeout,
                rc: 1,
                error: "pw-probe-runner did not flip done within sentinel deadline"
            )
        }
    }

    // Worker completed cleanly. Now classify the validator side.
    switch validatorResult {
    case nil:
        // No probes were sent (every step's (op, filter) was in
        // prediction_unavailable). That's a valid happy-path shape —
        // every step has a synthesized prediction_unavailable
        // verdict, attempts ran cleanly.
        return ClassifiedRun(outcome: NormalizedOutcome.ok, rc: 0, error: nil)

    case .failure(let err, _):
        switch err {
        case .spawnFailed:
            return ClassifiedRun(
                outcome: NormalizedOutcome.validatorSpawnFailed,
                rc: 1, error: err.description
            )
        case .verdictParseFailed:
            return ClassifiedRun(
                outcome: NormalizedOutcome.validatorDecodeFailure,
                rc: 1, error: err.description
            )
        case .verdictReadFailed, .probeWriteFailed:
            return ClassifiedRun(
                outcome: NormalizedOutcome.validatorNoReply,
                rc: 1, error: err.description
            )
        case .pipeFailed, .probeSerializationFailed:
            return ClassifiedRun(
                outcome: NormalizedOutcome.runnerFailed,
                rc: 1, error: err.description
            )
        }

    case .success(let vOut):
        // Validator clean-exited. Verify it produced the expected
        // verdict count; a short count means it walked off the end
        // of stdin early and we have attempts-only evidence for the
        // missing tail.
        if vOut.verdicts.count < expectedVerdictCount {
            return ClassifiedRun(
                outcome: NormalizedOutcome.validatorUnavailable,
                rc: 1,
                error: "validator returned \(vOut.verdicts.count) verdicts; expected \(expectedVerdictCount)"
            )
        }
        return ClassifiedRun(outcome: NormalizedOutcome.ok, rc: 0, error: nil)
    }
}

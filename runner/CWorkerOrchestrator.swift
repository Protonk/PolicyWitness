import Darwin
import Foundation

/*
 * CWorkerOrchestrator — host-side wiring that runs a single specimen
 * through the C-worker code path: pw-probe-runner for attempts +
 * sb_api_validator --batch for sandbox_check verdicts, joined into
 * one PWRunnerRunResult envelope. Per RUNNER-RESHAPE-PLAN Step 6.8
 * (R9). Gated by `_test_overrides.use_c_worker` during 6.8a;
 * default-on after 6.8b.
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
 *        - drift = boolean comparison or nil per Step 6.4 contract
 *   4. Classifier:
 *        - normalized_outcome from C-worker disposition +
 *          validator disposition + per-slot completed/done state
 *
 * Validation, libsandbox-availability checks, and policy-hash
 * computation are PWRunnerService.runSpecimen's responsibility —
 * they happen identically on both code paths. The orchestrator
 * only sees a request that has already passed those gates.
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

        let workerInput = CWorkerInput(
            workerExecutablePath: workerExecutablePath,
            policy: parsed.policy.sbpl_source ?? "",
            params: workerParams,
            slots: workerSlots,
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

    /// pw-probe-runner lives at `<this xpc service>/Contents/MacOS/pw-probe-runner`
    /// per RUNNER-RESHAPE-PLAN R5. The XPC service binary itself lives at
    /// `<this xpc service>/Contents/MacOS/<service-name>` — Bundle.main
    /// resolves to the service bundle. Sibling resolution.
    public static func defaultWorkerExecutablePath() -> String {
        let bundleURL = Bundle.main.bundleURL
        return bundleURL
            .appendingPathComponent("Contents/MacOS/pw-probe-runner")
            .path
    }

    /// sb_api_validator lives at the app's top-level
    /// `Contents/MacOS/sb_api_validator`. The XPC service bundle is
    /// nested at `<app>/Contents/XPCServices/<service>.xpc`, so we
    /// walk up three levels to the app bundle and into its MacOS dir.
    public static func defaultValidatorExecutablePath() -> String {
        let serviceURL = Bundle.main.bundleURL
        let appURL = serviceURL
            .deletingLastPathComponent()   // XPCServices/
            .deletingLastPathComponent()   // Contents/
            .deletingLastPathComponent()   // <app>.app/
        return appURL
            .appendingPathComponent("Contents/MacOS/sb_api_validator")
            .path
    }
}

// MARK: - Translation: request → driver inputs

private func workerSlotsFromProbePlan(_ plan: [PWRunnerProbeStep]) -> [CWorkerSlotInput] {
    return plan.map { step in
        CWorkerSlotInput(
            stepId: step.step_id,
            attemptKind: mapAttemptKind(step.attempt),
            target: step.attempt.target
        )
    }
}

private func mapAttemptKind(_ attempt: PWRunnerAttempt) -> PWAttemptKind {
    switch (attempt.kind, attempt.action) {
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionOpenRead):
        return .fileOpenRead
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionOpenWrite):
        return .fileOpenWrite
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionCreate):
        return .fileCreate
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionUnlink):
        return .fileUnlink
    case (PWRunnerWire.attemptKindMachLookup, PWRunnerWire.attemptActionMachLookup):
        return .machLookup
    default:
        // The Swift wire vocabulary includes (kind, action) combos the
        // C worker doesn't implement (e.g. file/access). For those the
        // slot is filled but `attempt_kind` is NONE; the worker will
        // mark completed=1 with rc=0 and no observation. The step's
        // attempt outcome then surfaces as "unsupported" through the
        // builder so consumers see why the attempt didn't fire.
        return .none
    }
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
        let opFilterPair = PredictionUnavailablePair(
            operation: step.sandbox_check.operation,
            filterKind: step.sandbox_check.filter.kind
        )
        if predictionUnavailableOpFiltersHostMirror.contains(opFilterPair) {
            // Don't ask the validator about this pair. The verdict is
            // synthesized as prediction_unavailable in the step builder.
            continue
        }
        probes.append(ValidatorProbe(
            stepId: step.step_id,
            operation: step.sandbox_check.operation,
            filterType: mapFilterKindToValidator(step.sandbox_check.filter.kind),
            filterValue: step.sandbox_check.filter.value
        ))
    }
    return probes
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

    var results: [PWRunnerStepResult] = []
    results.reserveCapacity(probePlan.count)
    for step in probePlan {
        let sandboxCheck = buildSandboxCheckResult(
            step: step,
            verdict: verdictsByStep[step.step_id]
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
    verdict: ValidatorVerdict?
) -> PWRunnerSandboxCheckResult {
    let opFilterPair = PredictionUnavailablePair(
        operation: step.sandbox_check.operation,
        filterKind: step.sandbox_check.filter.kind
    )
    let scope = PWRunnerWire.sandboxCheckScopePost
    let kind = step.sandbox_check.filter.kind
    let value = step.sandbox_check.filter.value

    // Skipped pair: synthesize prediction_unavailable per the existing
    // contract (same shape ProbeRunner's short-circuit emits).
    if predictionUnavailableOpFiltersHostMirror.contains(opFilterPair) {
        return PWRunnerSandboxCheckResult(
            rc: -1,
            outcome: SandboxCheckOutcome.predictionUnavailable,
            pid: Int(getpid()),
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

    // Validator didn't return a verdict for this step (validator never
    // ran, or it died mid-stream and this step was past the partial
    // cutoff). Surface as outcome=error so consumers see the gap.
    guard let v = verdict else {
        return PWRunnerSandboxCheckResult(
            rc: 0,
            outcome: SandboxCheckOutcome.error,
            pid: Int(getpid()),
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
        pid: 0,
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
/// error / parse_error / bad_filter). Map to the host's
/// SandboxCheckOutcome catalog: allow/deny/error pass through;
/// parse_error and bad_filter both surface as `error` with the
/// validator's outcome string in the error field via the verdict
/// itself (set upstream).
private func mapValidatorOutcomeToSandboxCheckOutcome(_ vOutcome: String) -> String {
    switch vOutcome {
    case "allow": return SandboxCheckOutcome.allow
    case "deny":  return SandboxCheckOutcome.deny
    default:      return SandboxCheckOutcome.error
    }
}

private func buildAttemptResult(
    step: PWRunnerProbeStep,
    slot: CWorkerSlotResult?
) -> PWRunnerAttemptResult {
    // Slot missing → worker never reached the step. Surface as
    // not_run_worker_died so consumers can tell "the attempt failed"
    // (slot present, rc non-zero) from "the attempt never ran"
    // (slot missing). Step 6.7 / AttemptOutcome.
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
    let outcome: String = {
        if s.rc == 0 {
            return AttemptOutcome.ok
        }
        // The C worker uses the error-message convention "open(...): X"
        // for file failures and "bootstrap_look_up: kr=N" for mach
        // failures. We dispatch on the attempt kind instead of parsing
        // the message — kind is authoritative.
        switch step.attempt.action {
        case PWRunnerWire.attemptActionOpenRead,
             PWRunnerWire.attemptActionOpenWrite,
             PWRunnerWire.attemptActionCreate:
            return AttemptOutcome.openFailed
        case PWRunnerWire.attemptActionUnlink:
            return AttemptOutcome.unlinkFailed
        case PWRunnerWire.attemptActionMachLookup:
            return AttemptOutcome.lookupFailed
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
        observed_path: s.observedPath
    )
}

private func computeDrift(
    sandboxCheck: PWRunnerSandboxCheckResult,
    attempt: PWRunnerAttemptResult
) -> Bool? {
    // Per the Step 6.4 schema doc: drift is the validator-vs-attempt
    // disagreement about allow/deny. nil when no comparison possible.
    switch sandboxCheck.outcome {
    case SandboxCheckOutcome.allow:
        if attempt.outcome == AttemptOutcome.ok { return false }
        // Any non-ok attempt outcome that isn't a worker-died-class
        // signal is observable disagreement (allow predicted, deny
        // observed).
        if attempt.outcome == AttemptOutcome.notRunWorkerDied { return nil }
        return true
    case SandboxCheckOutcome.deny:
        if attempt.outcome == AttemptOutcome.ok { return true }
        if attempt.outcome == AttemptOutcome.notRunWorkerDied { return nil }
        return false
    default:
        return nil   // prediction_unavailable, error, missing → no comparison
    }
}

private func zeroSignalResult() -> PWRunnerSignalResult {
    // PWRunnerSignalResult: signal name + before/after counts + delta.
    // The C-worker path doesn't yet observe per-step deny signals
    // (the Swift worker collected those via signal handlers inside
    // its own process). 6.8a leaves the field zeroed; a future
    // chunk can wire in a per-slot signal counter if the data turns
    // out to matter.
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
             .slotInputTooLong, .paramInputTooLong:
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
            // done and entering the spin loop). The Step 5 contract
            // says compile failure follows the same path.
            return ClassifiedRun(
                outcome: NormalizedOutcome.sandboxApplyFailed,
                rc: 1,
                error: "sandbox_apply returned \(out.applyRC) inside pw-probe-runner"
            )
        }
        if out.sentSigkill || !out.done {
            // Host couldn't observe `done` within the sentinel
            // deadline. The bug-report shape: worker died from a
            // post-apply signal (sandbox kill) is indistinguishable
            // here from runner_timeout from this side; the term_signal
            // on runner_subprocess lets a consumer tell them apart.
            // For 6.8a we lean toward runner_timeout — the worker's
            // sandbox-kill exit path is rare under the C worker
            // because its post-apply syscall surface is so small.
            // A future refinement could inspect out.termSignal to
            // distinguish.
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

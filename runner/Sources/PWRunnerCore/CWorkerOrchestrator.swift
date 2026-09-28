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
 *        - comparison records submitted scope, derivation and known limits;
 *          drift projects supported agreement to false; current evidence
 *          cannot establish disagreement even when query order is known
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
        run(parsed: parsed, policyHash: policyHash, bundleId: bundleId,
            workerExecutablePath: workerExecutablePath, validatorExecutablePath: validatorExecutablePath,
            validatorSpawn: nativeValidatorSpawn)
    }

    // Tests substitute only the native validator launch; worker orchestration,
    // classification, evidence assembly and reply encoding remain production.
    static func run(
        parsed: PWRunnerRunSpec,
        policyHash: String,
        bundleId: String?,
        workerExecutablePath: String,
        validatorExecutablePath: String,
        validatorSpawn: @escaping ValidatorSpawnCall
    ) -> PWRunnerRunResult {
        let stepCount = parsed.probe_plan.count

        // ---- translation: request → driver inputs ------------------------
        let workerSlots = workerSlotsFromProbePlan(parsed.probe_plan)
        let workerParams = workerParamsFromPolicy(parsed.policy)
        let queryRefusal = queryAdmissionFailure(parsed.probe_plan)
        // Admission precedes path resolution and query construction as well as
        // child launch; rejected strings need no derived host observations.
        let queryPlan = queryRefusal == nil ? planValidatorQueries(parsed.probe_plan) : []
        let validatorProbes = queryPlan.compactMap { $0.probe }

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
            postApplyHangMs: parsed._test_overrides?.worker_post_apply_hang_ms,
            postApplyKillSignal: parsed._test_overrides?.worker_post_apply_kill_signal,
            preReadyHangMs: parsed._test_overrides?.worker_pre_ready_hang_ms,
            captureAppliedProfile: parsed.policy.capture_applied_profile == true,
            captureNonce: parsed.policy.capture_nonce
        )

        // ---- run worker + validator together via postApplied hook --------
        var validatorResult: ValidatorClientResult? = nil
        let workerResult: CWorkerRunResult
        if let refused = queryRefusal {
            // These host-only plan strings never reach shared memory, so the
            // driver's capacity checks cannot see them. Refuse here with the
            // same host-owned record and the same downstream classification,
            // before any shm, pipe or process work.
            workerResult = .failure(.admissionFailed(refused))
        } else {
            workerResult = runCWorker(workerInput) { workerPid in
                // Skip validator entirely when every step's (op, filter) is
                // in the prediction_unavailable set: no probes to send means
                // no useful validator work. Avoids spawning a child only to
                // immediately reap it.
                if validatorProbes.isEmpty { return }
                let vInput = ValidatorClientInput(
                    executablePath: validatorExecutablePath,
                    targetPid: workerPid,
                    probes: validatorProbes,
                    verdictReadTimeoutMs: timeoutMsForValidator(override: parsed._test_overrides?.validator_io_timeout_ms)
                )
                validatorResult = runValidator(vInput, processCalls: ChildProcessCalls(), spawn: validatorSpawn)
            }
        }

        // ---- assemble + classify -----------------------------------------
        let workerOutput = unwrapWorkerOutput(workerResult)
        let disposition = workerOutput.map { resolveDisposition($0, plan: parsed.probe_plan) }
        let runOutcome = classify(
            workerResult: workerResult,
            validatorResult: validatorResult,
            expectedVerdictCount: validatorProbes.count,
            disposition: disposition
        )

        let validatorOutput = unwrapValidatorOutput(validatorResult)

        let ordering = workerOutput.map {
            buildOrdering($0, validatorOutput: validatorOutput, hasQueries: !validatorProbes.isEmpty)
        }
        // A pre-spawn refusal is a bad_request like the service's own: the
        // reply carries the refusal record and no steps (see isPreSpawnRefusal).
        let stepResults: [PWRunnerStepResult]
        if case .failure(let error, nil) = workerResult, error.isPreSpawnRefusal {
            stepResults = []
        } else {
            stepResults = buildStepResults(
                probePlan: parsed.probe_plan,
                queryPlan: queryPlan,
                workerOutput: workerOutput,
                validatorOutput: validatorOutput, ordering: ordering,
                disposition: disposition
            )
        }

        let admissionFailure: PWRunnerAdmissionFailure?
        if case .failure(.admissionFailed(let record), _) = workerResult { admissionFailure = record }
        else { admissionFailure = nil }
        let topPid: Int = workerOutput.map { Int($0.workerPid) } ?? Int(getpid())
        var runnerSubprocess = workerOutput.map { buildWorkerSubprocess($0, disposition: disposition) }
        runnerSubprocess?.ordering = ordering
        let validatorSubprocess = validatorOutput.map(buildValidatorSubprocess)
        let validatorSpawnFailure: PWRunnerSpawnFailure?
        if case .failure(.spawnFailed(let failure), _) = validatorResult { validatorSpawnFailure = failure }
        else { validatorSpawnFailure = nil }

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
            test_overrides: parsed._test_overrides,
            applied_profile: workerOutput?.profileCapture,
            admission_failure: admissionFailure,
            validator_spawn_failure: validatorSpawnFailure
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

    /// Every capacity refusal, decided from the decoded request alone. The
    /// service runs this before any other validation so that no later
    /// diagnostic can echo an unbounded string: top-level strings first, then
    /// the worker's shared-memory bounds in plan order, then the host-only
    /// query strings and labels. The driver keeps its own check as the guard
    /// local to the ABI writer, and `run` keeps the query gate for callers
    /// that bypass the service.
    public static func admissionFailure(for parsed: PWRunnerRunSpec) -> PWRunnerAdmissionFailure? {
        if let refused = requestAdmissionFailure(parsed) { return refused }
        let capacity = CWorkerInput(workerExecutablePath: "", policy: parsed.policy.sbpl_source ?? "",
            params: workerParamsFromPolicy(parsed.policy), slots: workerSlotsFromProbePlan(parsed.probe_plan))
        if let refused = workerAdmissionFailure(capacity) { return refused }
        return queryAdmissionFailure(parsed.probe_plan)
    }

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
func timeoutMsForCWorker(override: Int?) -> Int {
    let cWorkerDefault = 60_000
    guard let v = override else { return cWorkerDefault }
    return max(50, v)
}

// Configuration allowance for observation, setup, decode and scheduling;
// the nominal relation covers defaults, not fault-injection overrides. It is
// not an enforced bound on final reap or host descheduling.
let validatorReleaseMarginMs = 5_000
func timeoutMsForValidator(override: Int?) -> Int {
    // Intentionally uncapped: tests may hold collection beyond worker expiry.
    override.map { max(50, $0) } ?? 30_000
}

// MARK: - Translation: request → driver inputs

private func workerSlotsFromProbePlan(_ plan: [PWRunnerProbeStep]) -> [CWorkerSlotInput] {
    var slots: [CWorkerSlotInput] = []
    slots.reserveCapacity(plan.count)
    for step in plan {
        let slot = makeWorkerSlot(stepID: step.step_id, attempt: step.attempt)
        slots.append(slot)
    }
    return slots
}

private func makeWorkerSlot(stepID: String, attempt: PWRunnerAttempt) -> CWorkerSlotInput {
    // Exec attempts pass argv[1..N] via attempt.args; other kinds
    // ignore the field. Defensive: only thread the args when the
    // resolved attempt kind is .execSpawn so a caller that
    // mistakenly populates args on a file probe doesn't pay the
    // shm-write cost for ignored bytes.
    let kind = mapAttemptKind(attempt)
    let args: [String] = (kind == .execSpawn) ? (attempt.args ?? []) : []
    return CWorkerSlotInput(
        stepId: stepID,
        attemptKind: kind,
        target: attempt.target,
        args: args
    )
}

/// (kind, action) → C-worker PWAttemptKind. Returns nil for any
/// combo the C worker can't execute. The orchestrator falls back
/// to PW_ATTEMPT_NONE (worker no-ops the slot) and the step builder
/// then emits `attempt.outcome = "unsupported"` so the rc=0 slot
/// isn't misread as a successful observation.
// `internal` (not `private`) so AttemptOutcomeMappingTests can assert the
// Layer-1 routing table agrees with buildAttemptResult's outcome switch.
func mapAttemptKindOrNil(_ attempt: PWRunnerAttempt) -> PWAttemptKind? {
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

/// Snapshot the host's query decision before any worker attempt can change paths.
struct ValidatorQueryDecision {
    let stepId: String
    let probe: ValidatorProbe?
    let exclusionReason: String?
    var exclusionCode: String? = nil
}

/// Admission bounds for request strings the worker never carries.
/// `sandbox_check.operation` and `sandbox_check.filter.value` go to the
/// validator as one JSON line per probe and come back echoed in every step of
/// the reply; neither enters shared memory, so `workerAdmissionFailure` cannot
/// bound them. Left unbounded, an admitted 256-step plan can outgrow the
/// controller's reply capture after every attempt has already run, and one
/// probe can exceed the validator's line buffer and lose its prediction while
/// its attempt still runs. Bounded, a fully escaped probe line stays a few KiB
/// and the per-step reply overhead is a sum of documented limits. The values
/// match the attempt target (511) and the parameter key (127); no libsandbox
/// operation name approaches 127 bytes and filter values are paths or names.
/// Units are UTF-8 bytes excluding any terminating NUL, like the worker bounds.
let sandboxCheckOperationMaxBytes = 127
let sandboxCheckFilterValueMaxBytes = 511
// Unknown labels remain supported as per-step unavailable/unsupported results
// within this bound. They are echoed verbatim, sometimes in several fields.
let probePlanLabelMaxBytes = 127

/// Host-only capacity check for the sandbox_check strings, using the same
/// record as the driver's shared-memory bounds. The value is bounded for every
/// filter kind, including `none` and unrecognized kinds, because the reply
/// echoes whatever was supplied. Filter kind and attempt labels also stay on
/// the host and are echoed even when unrecognized. Checks run in plan order,
/// operation then value then labels within a step, and report the first excess.
func queryAdmissionFailure(_ plan: [PWRunnerProbeStep]) -> PWRunnerAdmissionFailure? {
    for (position, step) in plan.enumerated() {
        let operation = step.sandbox_check.operation.utf8.count
        if operation > sandboxCheckOperationMaxBytes {
            return PWRunnerAdmissionFailure(field: "sandbox_check.operation", actual: operation,
                maximum: sandboxCheckOperationMaxBytes, unit: "utf8_bytes", step_id: step.step_id, step_index: position)
        }
        if let value = step.sandbox_check.filter.value, value.utf8.count > sandboxCheckFilterValueMaxBytes {
            return PWRunnerAdmissionFailure(field: "sandbox_check.filter.value", actual: value.utf8.count,
                maximum: sandboxCheckFilterValueMaxBytes, unit: "utf8_bytes", step_id: step.step_id, step_index: position)
        }
        for (field, value) in [("sandbox_check.filter.kind", step.sandbox_check.filter.kind),
                               ("attempt.kind", step.attempt.kind), ("attempt.action", step.attempt.action)] {
            if value.utf8.count > probePlanLabelMaxBytes {
                return PWRunnerAdmissionFailure(field: field, actual: value.utf8.count,
                    maximum: probePlanLabelMaxBytes, unit: "utf8_bytes", step_id: step.step_id, step_index: position)
            }
        }
    }
    return nil
}

/// Bounds for the request strings echoed once per reply rather than per step:
/// the specimen ID, the run kind and policy format labels, and the test-seam
/// executable paths mirrored back in `test_overrides` and named in dlopen and
/// spawn diagnostics. Amplification is one, so these matter only for a request
/// about as large as the reply cap; they complete the rule that every echoed
/// request string is admission-bounded. PATH_MAX is 1024 including the NUL.
let specimenIdMaxBytes = 255
let requestLabelMaxBytes = 63
let testOverridePathMaxBytes = 1023

/// Capacity check for the top-level request strings, using the same record.
/// No step or parameter identity applies; the field name is the identity.
func requestAdmissionFailure(_ parsed: PWRunnerRunSpec) -> PWRunnerAdmissionFailure? {
    func check(_ field: String, _ value: String?, _ maximum: Int) -> PWRunnerAdmissionFailure? {
        guard let value, value.utf8.count > maximum else { return nil }
        return PWRunnerAdmissionFailure(field: field, actual: value.utf8.count, maximum: maximum, unit: "utf8_bytes")
    }
    if let r = check("specimen_id", parsed.specimen_id, specimenIdMaxBytes) { return r }
    if let r = check("run_kind", parsed.run_kind, requestLabelMaxBytes) { return r }
    if let r = check("policy.format", parsed.policy.format, requestLabelMaxBytes) { return r }
    let overrides = parsed._test_overrides
    for (field, value) in [("_test_overrides.libsandbox_path", overrides?.libsandbox_path),
                           ("_test_overrides.worker_executable_path", overrides?.worker_executable_path),
                           ("_test_overrides.validator_executable_path", overrides?.validator_executable_path)] {
        if let r = check(field, value, testOverridePathMaxBytes) { return r }
    }
    return nil
}

func planValidatorQueries(_ plan: [PWRunnerProbeStep]) -> [ValidatorQueryDecision] {
    plan.map { step in
        let check = step.sandbox_check
        let kind = check.filter.kind
        let reason: String?
        let code: String?
        if predictionUnavailableOpFilters.contains(PredictionUnavailablePair(operation: check.operation, filterKind: kind)) {
            reason = "prediction unavailable for this operation and filter"
            code = "prediction_unavailable_pair"
        } else if !knownFilterKinds.contains(kind) {
            reason = "prediction unavailable for unrecognized filter kind"
            code = "unrecognized_filter_kind"
        } else if pathFilterIsUnresolvable(kind, check.filter.value) {
            reason = "target path \(check.filter.value ?? "") did not resolve on the host when the query was planned"
            code = "path_unresolved_at_planning"
        } else { reason = nil; code = nil }
        return ValidatorQueryDecision(stepId: step.step_id,
            probe: reason == nil ? ValidatorProbe(stepId: step.step_id, operation: check.operation,
                filterType: mapFilterKindToValidator(kind),
                filterValue: kind == PWRunnerWire.sandboxFilterNone ? nil : check.filter.value) : nil,
            exclusionReason: reason, exclusionCode: code)
    }
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
    case .failure(_, let partial): return partial
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

func buildStepResults(
    probePlan: [PWRunnerProbeStep],
    queryPlan: [ValidatorQueryDecision],
    workerOutput: CWorkerOutput?,
    validatorOutput: ValidatorOutput?,
    ordering: PWRunnerOrdering? = nil,
    disposition: PWDispositionRecord? = nil
) -> [PWRunnerStepResult] {
    // One resolved account for every lifecycle projection below.
    let account = disposition ?? workerOutput.map { resolveDisposition($0, plan: probePlan) }
    // Index outputs by step_id for the join.
    let workerSlotsByStep = uniquelyAssociatedWorkerSlots(workerOutput?.slots ?? [])
    let probes = queryPlan.compactMap { $0.probe }
    let decisions = Dictionary(uniqueKeysWithValues: queryPlan.map { ($0.stepId, $0) })
    let verdictsByStep = associateValidatorVerdicts(validatorOutput?.verdicts ?? [], expected: probes).byStep
    // No worker means no PID for a worker-targeted sandbox query.
    let sbCheckPid = workerOutput.map { Int($0.workerPid) }

    // Join both channels for every step before any comparison. With order
    // unestablished, any attempt in the run may precede any query, so the
    // classifier must see the whole run's attempts, not a prefix of them.
    var channels: [(step: PWRunnerProbeStep, sandboxCheck: PWRunnerSandboxCheckResult,
                    attempt: PWRunnerAttemptResult)] = []
    channels.reserveCapacity(probePlan.count)
    for (index, step) in probePlan.enumerated() {
        var sandboxCheck = buildSandboxCheckResult(
            step: step,
            verdict: verdictsByStep[step.step_id],
            sandboxCheckPid: sbCheckPid,
            exclusionReason: decisions[step.step_id]?.exclusionReason
        )
        var attempt = buildAttemptResult(
            step: step,
            slot: workerSlotsByStep[step.step_id]
        )
        // Excluded queries are synthesized even if an unexpected validator
        // record names their step. Do not attribute the synthesized result to it.
        let verdict = sandboxCheck.outcome == SandboxCheckOutcome.predictionUnavailable
            ? nil : verdictsByStep[step.step_id]
        sandboxCheck.result_source = verdict == nil ? "synthetic" : "validator"
        sandboxCheck.native_rc = verdict.flatMap {
            ["allow", "deny", "error"].contains($0.outcome) ? $0.rc : nil
        }
        if verdict == nil {
            sandboxCheck.missing_reason = sandboxCheck.outcome == SandboxCheckOutcome.predictionUnavailable
                ? "query_not_requested" : validatorOutput == nil ? "validator_not_invoked" : "validator_no_verdict"
        }
        let slot = workerSlotsByStep[step.step_id]
        let recordStep = account?.steps.indices.contains(index) == true ? account?.steps[index] : nil
        let supported = recordStep.map { $0.attempt_support == "supported" } ?? (mapAttemptKindOrNil(step.attempt) != nil)
        let slotState = recordStep?.slot ?? (slot == nil ? "absent" : slot!.completed ? "completed" : "incomplete")
        attempt.requested_kind = step.attempt.kind
        attempt.requested_action = step.attempt.action
        attempt.result_source = slotState == "completed" && supported ? "worker" : "synthetic"
        // Slot rc is PW's attempt status (often 0/1), not the raw syscall
        // return (e.g. an open FD). ABI 7 does not carry that native return.
        attempt.native_rc = nil
        if attempt.result_source == "synthetic" {
            attempt.missing_reason = !supported ? "attempt_not_supported" : slotState == "absent" ? "slot_absent" : "slot_incomplete"
        }
        // The lifecycle object projects this step's two claims; the compatibility
        // triple above is unchanged.
        if let account, account.steps.indices.contains(index) {
            attempt.lifecycle = attemptLifecycle(account.steps[index])
        }
        channels.append((step: step, sandboxCheck: sandboxCheck, attempt: attempt))
    }
    let runAttempts = channels.map { $0.attempt }
    return channels.map { channel in
        var comparison = computeComparison(sandboxCheck: channel.sandboxCheck, attempt: channel.attempt,
            queryExclusionReason: decisions[channel.step.step_id]?.exclusionCode,
            order: eligibleOrderedStep(stepId: channel.step.step_id, query: channel.sandboxCheck,
                records: validatorOutput?.verdicts ?? [], ordering: ordering,
                sandboxedAfterApply: workerOutput?.applied == true && workerOutput?.applyRC == 0,
                workerPid: workerOutput.map { Int($0.workerPid) })
                ? .queryFirst : .unestablished, runAttempts: runAttempts)
        // Exactly one lifecycle limitation for a summary other than completed. It
        // never changes agreement, order, drift or sandbox attribution.
        if let summary = channel.attempt.lifecycle?.summary,
           let limitation = PWDisposition.limitationForSummary[summary] {
            comparison.limitations.append(limitation)
        }
        return PWRunnerStepResult(
            step_id: channel.step.step_id,
            sandbox_check: channel.sandboxCheck,
            attempt: channel.attempt,
            deny_signal: nil,
            drift: comparison.drift,
            comparison: comparison
        )
    }
}

private func buildSandboxCheckResult(
    step: PWRunnerProbeStep,
    verdict: ValidatorVerdict?,
    sandboxCheckPid: Int?,
    exclusionReason: String?
) -> PWRunnerSandboxCheckResult {
    let scope = PWRunnerWire.sandboxCheckScopePost
    let kind = step.sandbox_check.filter.kind
    let value = step.sandbox_check.filter.value
    if let reason = exclusionReason {
        return PWRunnerSandboxCheckResult(rc: -1, outcome: SandboxCheckOutcome.predictionUnavailable,
            pid: sandboxCheckPid, operation: step.sandbox_check.operation, scope: scope,
            filter_kind: kind, filter_value: value, error: reason)
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

// `internal` (not `private`) so AttemptOutcomeMappingTests can drive the
// (kind, action, slot) → AttemptOutcome mapping directly. This is the
// third host classifier alongside computeComparison/classify; the test pins
// each cell so the two stacked tables (kind routing + the rc!=0 action
// switch) can't silently drift apart.
func buildAttemptResult(
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
    // Missing or incomplete slots establish no completed attempt result.
    // The compatibility spelling does not prove the operation never started.
    guard let s = slot else {
        return PWRunnerAttemptResult(
            rc: -1,
            errno: nil,
            outcome: AttemptOutcome.notRunWorkerDied,
            error: "no completed attempt result: slot unavailable",
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
            error: "no completed attempt result: slot publication incomplete",
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

// Only a completed worker observation supports mutation of the submitted object.
// Content writes and create-if-absent do not establish object removal/replacement.
private func reportsTargetRemoval(_ attempt: PWRunnerAttemptResult) -> Bool {
    guard attempt.result_source == "worker", attempt.rc == 0 else { return false }
    switch (attempt.requested_kind, attempt.requested_action, attempt.outcome) {
    case ("file", "unlink", AttemptOutcome.ok): return true
    default: return false
    }
}

enum ComparisonOrder: String { case queryFirst = "query_first", unestablished }
enum ComparisonState { case unestablished }
enum ComparisonIdentity { case unestablished, notApplicable }
enum ComparisonAttribution { case unestablished, notRequired }
enum ComparisonMutation { case none, sameTargetUnordered, sameTargetAfterQuery }

struct ComparisonEvidence {
    var order: ComparisonOrder
    var state: ComparisonState = .unestablished
    var identity: ComparisonIdentity
    var attribution: ComparisonAttribution
    var mutation: ComparisonMutation
    var prediction: String
    var observation: String
    var basis: String
    var operationRelation: String
    var targetRelation: String
    var otherLimitations: [String]

    // No evidence for established state or runtime identity is expressible in
    // response 8. In particular there is no constructible disagreement branch.
    var conclusion: String {
        guard operationRelation == "matched", targetRelation == "same_submitted" else { return "unavailable" }
        if mutation == .sameTargetUnordered { return "unavailable" }
        if observation == "succeeded", prediction == "allow" { return "agreement" }
        if observation == "permission_failure", prediction == "deny" { return "directional_consistency" }
        return "unavailable"
    }
    func renderLimitations() -> [String] {
        var result: [String] = []
        if order == .unestablished { result.append("query_attempt_order_unestablished") }
        switch state { case .unestablished: result.append("state_stability_unestablished") }
        if identity == .unestablished { result.append("runtime_target_identity_unestablished") }
        if attribution == .unestablished { result.append("sandbox_attribution_unestablished") }
        if mutation == .sameTargetUnordered { result.append("attempt_mutation_order_unestablished") }
        return result + otherLimitations
    }
    var comparison: PWRunnerComparison {
        PWRunnerComparison(scope: "submitted_operation_and_target", prediction: prediction,
            observation: observation, observation_basis: basis, operation_relation: operationRelation,
            target_relation: targetRelation, conclusion: conclusion, limitations: renderLimitations(), order: order.rawValue)
    }
}

func buildOrdering(_ worker: CWorkerOutput, validatorOutput: ValidatorOutput?, hasQueries: Bool) -> PWRunnerOrdering {
    let disposition = !worker.hookInvoked ? "not_invoked" : !hasQueries ? "not_needed"
        : validatorOutput == nil ? "not_spawned" : validatorOutput?.reaped == true ? "reaped" : "unconfirmed"
    var violations = worker.orderingProtocolViolations
    if worker.proceedObserved && !worker.proceedSet { violations.append("acknowledgement_without_release") }
    if worker.proceedSet && !worker.hookInvoked { violations.append("release_without_collection_closure") }
    if (worker.proceedSet || worker.proceedObserved) && (!worker.applied || worker.applyRC != 0) {
        violations.append("release_without_successful_application")
    }
    if worker.slots.contains(where: { $0.completed }) && !worker.proceedObserved {
        violations.append("attempt_without_acknowledgement")
    }
    if worker.workerEvidence?.failure?.operation == 11 &&
        (worker.proceedObserved || worker.slots.contains(where: { $0.completed })) {
        violations.append("attempt_or_acknowledgement_after_proceed_failure")
    }
    return PWRunnerOrdering(collection_closed_before_proceed: worker.hookInvoked,
        proceed_set: worker.proceedSet, proceed_observed: worker.proceedObserved,
        validator_disposition: disposition, worker_lifetime_established: worker.proceedOwnershipEstablished,
        protocol_violations: Array(Set(violations)).sorted())
}

func computeComparison(sandboxCheck: PWRunnerSandboxCheckResult, attempt: PWRunnerAttemptResult,
                       queryExclusionReason: String? = nil, order: ComparisonOrder = .unestablished,
                       runAttempts: [PWRunnerAttemptResult] = []) -> PWRunnerComparison {
    comparisonEvidence(sandboxCheck: sandboxCheck, attempt: attempt, queryExclusionReason: queryExclusionReason,
                       order: order, runAttempts: runAttempts).comparison
}

// Internal for independent scenario controls. Query order alone cannot
// discharge state/identity obligations or establish drift.
// `runAttempts` is every worker-reported attempt in the run, in plan order.
// While order is unestablished the worker's attempt loop can finish before the
// validator's first query, so a same-target unlink in any step, earlier or
// later, may precede this query. The current attempt is always considered.
func comparisonEvidence(
    sandboxCheck: PWRunnerSandboxCheckResult,
    attempt: PWRunnerAttemptResult,
    queryExclusionReason: String? = nil,
    order: ComparisonOrder = .unestablished,
    runAttempts: [PWRunnerAttemptResult] = []
) -> ComparisonEvidence {
    var limits: [String] = []
    var attribution: ComparisonAttribution = .notRequired
    if let reason = queryExclusionReason { limits.append("query_plan:" + reason) }
    let prediction = sandboxCheck.result_source == "validator"
        && [SandboxCheckOutcome.allow, SandboxCheckOutcome.deny].contains(sandboxCheck.outcome)
        ? sandboxCheck.outcome : "unavailable"
    if prediction == "unavailable" {
        limits.append("prediction:" + (sandboxCheck.missing_reason ?? "no_usable_verdict"))
    }

    var observation = "unavailable"
    var basis = "no_completed_worker_result"
    if attempt.result_source == "worker" {
        if attempt.requested_kind == "exec", (attempt.child_pid ?? 0) > 0 {
            observation = "succeeded"
            basis = "spawned_child"
            if attempt.rc != 0 {
                limits.append("exec_result_failed_after_spawn")
                attribution = .unestablished
            }
        } else if attempt.outcome == AttemptOutcome.ok && attempt.rc == 0 {
            observation = "succeeded"
            basis = "completed_worker_status"
        } else if attempt.rc != 0 {
            observation = "other_failure"
            basis = "completed_worker_status"
            if [AttemptOutcome.openFailed, AttemptOutcome.unlinkFailed,
                AttemptOutcome.accessFailed, AttemptOutcome.sysctlFailed,
                AttemptOutcome.execFailed].contains(attempt.outcome),
               [Int(EPERM), Int(EACCES)].contains(attempt.errno ?? -1) {
                observation = "permission_failure"
                basis = "permission_errno"
            } else if attempt.outcome == AttemptOutcome.lookupFailed,
                      attempt.error == "bootstrap_look_up: kr=1100" {
                observation = "permission_failure"
                basis = "bootstrap_permission_result"
            }
        }
    }
    if observation == "unavailable" {
        limits.append("attempt:" + (attempt.missing_reason ?? "no_completed_worker_result"))
    } else if observation != "succeeded" {
        attribution = .unestablished
    }

    let operation: String?
    let filter: String?
    switch (attempt.requested_kind, attempt.requested_action) {
    case ("file", "open_read"), ("file", "access"):
        operation = "file-read-data"; filter = "path"
    case ("file", "open_write"):
        operation = "file-write-data"; filter = "path"
    case ("file", "unlink"):
        operation = "file-write-unlink"; filter = "path"
    case ("mach_lookup", "bootstrap_look_up"):
        operation = "mach-lookup"; filter = "global_name"
    case ("sysctl", "read"):
        operation = "sysctl-read"; filter = "sysctl_name"
    case ("exec", "spawn"):
        // The native query accepts this spelling, not bare process-exec.
        // Native exec-scope controls isolate this target-admission query from
        // fork/interpreter conditions. Matching it does not predict all spawn
        // prerequisites; success supplies the execution observation separately.
        operation = "process-exec*"; filter = "path"
        limits.append("exec_query_not_full_spawn_prediction")
    case ("file", "create"):
        operation = nil; filter = "path"
        limits.append("compound_attempt")
    default:
        operation = nil; filter = nil
        limits.append("attempt_operation_unestablished")
    }
    let operationRelation: String
    let matchedExecQuery = operation == "process-exec*" && sandboxCheck.operation == operation
    let unresolvedBroadQuery = sandboxCheck.operation.contains("*") && !matchedExecQuery
    if unresolvedBroadQuery { limits.append("broad_query_operation") }
    if operation == nil || unresolvedBroadQuery {
        operationRelation = "unresolved"
    } else {
        operationRelation = operation == sandboxCheck.operation ? "matched" : "different"
    }
    if operationRelation != "matched" { limits.append("operation:" + operationRelation) }

    let targetRelation: String
    if filter != nil && sandboxCheck.filter_kind != filter {
        limits.append("query_filter_scope_unestablished")
    }
    if sandboxCheck.filter_value == nil || attempt.requested_path == nil {
        limits.append("submitted_target_unavailable")
    }
    if filter == nil || sandboxCheck.filter_kind != filter
        || sandboxCheck.filter_value == nil || attempt.requested_path == nil {
        targetRelation = "unresolved"
    } else {
        targetRelation = sandboxCheck.filter_value == attempt.requested_path
            ? "same_submitted" : "different_submitted"
    }
    if targetRelation != "same_submitted" { limits.append("target:" + targetRelation) }
    let identity: ComparisonIdentity = sandboxCheck.filter_kind == "path" || filter == "path"
        ? .unestablished : .notApplicable

    // Compare submitted paths only. Host resolution happens later and cannot
    // establish which object a query saw. Recreation does not erase a removal,
    // and step position does not bound the confound while order is unknown.
    let sameTargetMutation = queryExclusionReason == nil
        && sandboxCheck.filter_kind == "path" && sandboxCheck.filter_value != nil
        && ([attempt] + runAttempts).contains {
            reportsTargetRemoval($0) && $0.requested_path == sandboxCheck.filter_value
        }
    let mutation: ComparisonMutation = !sameTargetMutation ? .none
        : order == .queryFirst ? .sameTargetAfterQuery : .sameTargetUnordered
    return ComparisonEvidence(order: order, identity: identity, attribution: attribution, mutation: mutation,
        prediction: prediction, observation: observation, basis: basis, operationRelation: operationRelation,
        targetRelation: targetRelation, otherLimitations: limits)
}

// Internal for driver-to-JSON controls. Preserve the host's observations in the
// authoritative subprocess object; classification does not rewrite them.
func buildWorkerSubprocess(_ out: CWorkerOutput) -> PWRunnerSubprocess {
    buildWorkerSubprocess(out, disposition: nil)
}

/// `partial_steps` and the record project from one resolved account; callers
/// without a plan get the account resolved from the slots.
func buildWorkerSubprocess(_ out: CWorkerOutput, disposition: PWDispositionRecord?) -> PWRunnerSubprocess {
    let record = disposition ?? resolveDisposition(out, plan: nil)
    var result = PWRunnerSubprocess(
        pid: Int(out.workerPid),
        term_signal: out.termSignal.map { Int($0) },
        exit_code: out.exitCode.map { Int($0) },
        partial_steps: record.steps.contains { $0.slot != "completed" },
        ready_byte_received: out.readyByteReceived,
        done_observed: out.done,
        poll_stop_reason: out.pollStopReason,
        exit_requested: out.exitRequested,
        termination_request: out.terminationRequest,
        reaped: out.reaped,
        wait_errors: out.waitErrors
    )
    result.worker_evidence = out.workerEvidence
    result.policy_transfer_error = out.policyTransferError
    result.cleanup_trigger = out.cleanupTrigger
    result.grace_end = out.graceEnd
    result.collection_basis = out.collectionBasis
    result.disposition = record
    return result
}

func buildValidatorSubprocess(_ out: ValidatorOutput) -> PWRunnerValidatorSubprocess {
    var result = PWRunnerValidatorSubprocess(pid: Int(out.validatorPid),
        term_signal: out.termSignal.map(Int.init), exit_code: out.exitCode.map(Int.init))
    result.reaped = out.reaped
    result.termination_request = out.terminationRequest
    result.wait_errors = out.waitErrors
    result.stdout_bytes_received = out.rawStdoutBytes
    result.probe_bytes_written = out.probeBytesWritten
    result.probe_bytes_expected = out.probeBytesExpected
    result.io_error = out.ioError
    result.read_error = out.readError
    result.stdout_collection_stop = out.stdoutCollectionStop
    result.decode_fault = out.decodeFault
    result.records = out.verdicts
    result.expected_step_ids = out.expectedStepIds
    result.association_issues = out.expectedProbes.map { associateValidatorVerdicts(out.verdicts, expected: $0).issues }
    return result
}

private func anySlotNotCompleted(_ slots: [CWorkerSlotResult]) -> Bool {
    return slots.contains { !$0.completed }
}

// MARK: - Worker disposition record
//
// One canonical lifecycle account, resolved once from the driver's output and
// the submitted plan (tests/FAILURE-PROPAGATION-CONTRACT.md, "Worker
// disposition record"). Every lifecycle conclusion below projects from it.

private func uniquelyAssociatedWorkerSlots(_ slots: [CWorkerSlotResult]) -> [String: CWorkerSlotResult] {
    Dictionary(grouping: slots, by: { $0.stepId }).compactMapValues { $0.count == 1 ? $0[0] : nil }
}

/// Resolve the account. Without a plan (constructed inputs) the steps come from
/// the slots and every attempt counts as supported; production passes the plan.
func resolveDisposition(_ out: CWorkerOutput, plan: [PWRunnerProbeStep]?) -> PWDispositionRecord {
    var issues: [PWDispositionIssue] = []
    func supported(_ answer: String, value: PWDispositionValue? = nil, basis: [String]) -> PWDispositionClaim {
        PWDispositionClaim(state: "supported", answer: answer, value: value, basis: basis)
    }
    func unresolved(_ reason: String, basis: [String] = []) -> PWDispositionClaim {
        PWDispositionClaim(state: "unresolved", reason: reason, basis: basis.isEmpty ? nil : basis)
    }
    func inapplicable(_ reason: String) -> PWDispositionClaim {
        PWDispositionClaim(state: "inapplicable", reason: reason)
    }
    func conflict(_ rule: String, question: String, stepIndex: Int?, observations: [String],
                  detail: String) -> PWDispositionClaim {
        issues.append(PWDispositionIssue(kind: "conflict", rule: rule, question: question, step_index: stepIndex,
                                         observations: observations, detail: detail))
        return PWDispositionClaim(state: "conflicting", issue: issues.count - 1)
    }
    let hasProgress = out.workerEvidence?.progress != nil
    func present(_ tokens: [String]) -> [String] { tokens.filter { $0 != "progress" || hasProgress } }

    var questions: [String: PWDispositionClaim] = [:]
    if out.reaped != true {
        questions["final_status"] = unresolved("no_successful_reap", basis: ["reaped"])
    } else if out.exitCode != nil && out.termSignal != nil {
        questions["final_status"] = conflict("D1", question: "final_status", stepIndex: nil,
            observations: ["exit_code", "term_signal"],
            detail: "one successful reap represented as both an exit status and a signal")
    } else if let signal = out.termSignal {
        questions["final_status"] = supported("signal", value: .integer(Int(signal)), basis: ["reaped", "term_signal"])
    } else if let code = out.exitCode {
        questions["final_status"] = supported("exit_code", value: .integer(Int(code)), basis: ["reaped", "exit_code"])
    } else {
        questions["final_status"] = unresolved("status_unusable", basis: ["reaped"])
    }
    if let stop = out.pollStopReason {
        questions["stop_reason"] = supported(stop, basis: ["poll_stop_reason"])
    } else {
        questions["stop_reason"] = unresolved(PWDisposition.notRecorded)
    }
    for (name, raw) in [("cleanup_trigger", out.cleanupTrigger), ("grace_end", out.graceEnd)] {
        if out.exitRequested == false {
            questions[name] = inapplicable("exit_not_requested")
        } else if let raw {
            questions[name] = supported(raw, basis: [name, "exit_requested"])
        } else {
            questions[name] = unresolved(PWDisposition.notRecorded)
        }
    }
    // A recorded request is a direct observation; only the absence of a request
    // needs the recorded cleanup phase (exit_requested) to count as observed.
    if out.exitRequested == false {
        questions["kill_request_and_result"] = inapplicable("exit_not_requested")
    } else if let request = out.terminationRequest {
        questions["kill_request_and_result"] = supported("requested", value: .request(request), basis: ["termination_request"])
    } else if out.exitRequested == nil {
        questions["kill_request_and_result"] = unresolved(PWDisposition.notRecorded)
    } else {
        questions["kill_request_and_result"] = supported("none", basis: ["termination_request", "exit_requested"])
    }
    if let basis = out.collectionBasis {
        questions["collection_basis"] = supported(basis, basis: ["collection_basis"])
    } else {
        questions["collection_basis"] = unresolved(PWDisposition.notRecorded)
    }

    let planSteps: [(id: String, supported: Bool)] = plan?.map { ($0.step_id, mapAttemptKindOrNil($0.attempt) != nil) }
        ?? out.slots.map { ($0.stepId, true) }
    var position: ProtocolPosition? = nil
    switch associateProgress(out.workerEvidence?.progress, planCount: planSteps.count) {
    case nil:
        questions["progress_association"] = inapplicable("no_progress_word")
    case .unrecognized?:
        questions["progress_association"] = unresolved("progress_unrecognized", basis: ["progress"])
    case .invalid?:
        questions["progress_association"] = supported("invalid", basis: ["progress", "plan"])
    case .stepIndex(let index, let at)?:
        questions["progress_association"] = supported("step_index", value: .integer(index), basis: ["progress", "plan"])
        position = at
    case .parameterIndex(let index, let at)?:
        questions["progress_association"] = supported("parameter_index", value: .integer(index), basis: ["progress"])
        position = at
    case .none(let at)?:
        questions["progress_association"] = supported("none", basis: ["progress"])
        position = at
    }

    let terminal = out.collectionBasis == "after_confirmed_reap" && out.reaped == true
    let attemptOrder = PWDisposition.protocolOrder.firstIndex(of: 9)!
    let slotsById = uniquelyAssociatedWorkerSlots(out.slots)
    var steps: [PWDispositionStep] = []
    for (i, step) in planSteps.enumerated() {
        let slot = slotsById[step.id]
        let slotState = slot == nil ? "absent" : (slot!.completed ? "completed" : "incomplete")
        let completed = slotState == "completed"
        let boundary = ProtocolPosition(order: attemptOrder, index: i, phase: 1)
        let afterSlot = ProtocolPosition(order: attemptOrder, index: i, phase: 2)
        var claims: [String: PWDispositionClaim] = [:]
        claims["step_requested_operation_applicability"] =
            supported(step.supported ? "supported" : "unsupported", basis: ["attempt_support"])
        if let at = position, at < boundary && completed && terminal {
            claims["step_boundary_reached"] = conflict("D5", question: "step_boundary_reached", stepIndex: i,
                observations: ["progress", "slot", "collection_basis"],
                detail: "a completed slot beside valid terminal progress that never reached it")
        } else if let at = position, at >= boundary {
            claims["step_boundary_reached"] = supported("reached", basis: present(["progress", "slot", "attempt_support"]))
        } else if completed && step.supported {
            claims["step_boundary_reached"] = supported("reached", basis: present(["progress", "slot", "attempt_support"]))
        } else if position != nil && !completed && terminal {
            claims["step_boundary_reached"] = supported("not_reached", basis: ["progress", "slot", "collection_basis"])
        } else if position != nil && !completed {
            claims["step_boundary_reached"] = unresolved("basis_not_terminal", basis: ["progress", "slot", "collection_basis"])
        } else {
            claims["step_boundary_reached"] = unresolved("no_usable_progress", basis: present(["progress", "slot"]))
        }
        if !step.supported {
            claims["step_result_published"] = inapplicable("unsupported_attempt")
        } else if slotState == "absent" {
            claims["step_result_published"] = unresolved("slot_unavailable", basis: ["slot"])
        } else if completed {
            claims["step_result_published"] = supported("published", basis: ["slot", "attempt_support"])
        } else if !terminal {
            claims["step_result_published"] = unresolved("basis_not_terminal", basis: ["slot", "collection_basis"])
        } else if let at = position, at >= afterSlot {
            claims["step_result_published"] = conflict("D5", question: "step_result_published", stepIndex: i,
                observations: ["progress", "slot", "collection_basis"],
                detail: "valid returned progress for this step or a later position beside an incomplete slot")
        } else {
            claims["step_result_published"] = supported("unpublished", basis: present(["slot", "collection_basis", "progress"]))
        }
        steps.append(PWDispositionStep(index: i, step_id: step.id, slot: slotState,
                                       attempt_support: step.supported ? "supported" : "unsupported", questions: claims))
    }
    return PWDispositionRecord(questions: questions, steps: steps, issues: issues)
}

func attemptLifecycle(_ step: PWDispositionStep) -> PWAttemptLifecycle? {
    guard let boundary = step.questions["step_boundary_reached"],
          let result = step.questions["step_result_published"] else { return nil }
    return PWAttemptLifecycle(summary: lifecycleSummary(step), boundary: boundary, result: result)
}

// MARK: - Classifier

// `internal` (not `private`) so HostOutcomeClassifierTests can read the
// classified outcome. Pairs with the `classify` visibility note below.
struct ClassifiedRun {
    let outcome: String
    let rc: Int
    let error: String?
}

// `internal` (not `private`) so HostOutcomeClassifierTests can drive the
// worker/validator → NormalizedOutcome decision directly. This is the
// host's counterpart to computeComparison — the test pins each run shape to
// its outcome so the branch ladder can be reorganized without silently
// changing what the controller reports (and reaches outcomes no e2e
// specimen can reliably produce, including validator_no_reply).
func classify(
    workerResult: CWorkerRunResult,
    validatorResult: ValidatorClientResult?,
    expectedVerdictCount: Int,
    disposition: PWDispositionRecord? = nil
) -> ClassifiedRun {
    // Worker side first — its failure modes are more severe (the
    // attempt channel is the load-bearing observation; without it the
    // validator's predictions have nothing to compare against).
    switch workerResult {
    case .failure(let err, let partial):
        if let partial, partial.workerEvidence?.failure != nil {
            let reported = classify(workerResult: .success(partial), validatorResult: validatorResult,
                                    expectedVerdictCount: expectedVerdictCount, disposition: disposition)
            return ClassifiedRun(outcome: reported.outcome, rc: 1,
                error: (reported.error ?? "worker failure") + "; host " + err.description)
        }
        switch err {
        case .captureNonceInvalid, .admissionFailed, .execTargetNotAbsolute:
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
        // Precedence is specified in tests/FAILURE-PROPAGATION-CONTRACT.md.
        // Publication, deadline, cleanup and disposition remain independent;
        // this summary never rewrites their evidence or assigns a policy cause.
        if let evidence = out.workerEvidence {
            if let failure = evidence.failure {
                let names: [UInt32: String] = [1: "header validation", 2: "policy read", 3: "sandbox_create_params",
                    4: "sandbox_set_param", 5: "sandbox_compile_string", 8: "sandbox_apply", 11: "proceed wait"]
                let operation = names[failure.operation] ?? "operation \(failure.operation)"
                var detail = "pw-probe-runner reported \(operation) failure (code=\(failure.code))"
                if failure.operation == 11 { detail += "; budget=\(failure.detail) ms; release not observed" }
                if let rc = failure.native_result { detail += "; native_kind=\(failure.native_kind), result=\(rc)" }
                if let error = failure.errno { detail += "; errno=\(error)" }
                if let text = evidence.diagnostic.text, !text.isEmpty { detail += ": " + text }
                return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1, error: detail)
            }
            if evidence.failure_state != "absent" {
                return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1,
                    error: "pw-probe-runner failure publication \(evidence.failure_state)")
            }
        }
        if (out.applied && out.applyRC != 0) || (out.done && !out.applied && out.applyRC == 0) {
            return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1,
                error: "pw-probe-runner published inconsistent application/completion state")
        }
        if !out.applied && out.done {
            let detail = out.applyErrno != 0 ? "; legacy errno=\(out.applyErrno)" : ""
            return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1,
                error: "pw-probe-runner published a legacy preparation/application failure "
                    + "(status=\(out.applyRC)\(detail)); failed operation and native return unavailable")
        }
        // Lifecycle clauses render from the resolved account (the same account
        // the reply carries); worker, validator and setup diagnostics keep their
        // own owners and are composed with these clauses, not generated from them.
        let account = disposition ?? resolveDisposition(out, plan: nil)
        let killRequested = account.questions["kill_request_and_result"]?.answer == "requested"
        if account.questions["stop_reason"]?.answer == "sentinel_deadline" {
            return ClassifiedRun(outcome: NormalizedOutcome.runnerTimeout, rc: 1,
                error: "pw-probe-runner sentinel deadline expired; "
                    + (out.proceedSet && !out.proceedObserved ? "release not observed; " : "")
                    + (killRequested ? "host requested SIGKILL during cleanup" : "no termination requested"))
        }
        var problems: [String] = []
        if out.proceedSet && !out.proceedObserved { problems.append("release not observed") }
        if !out.applied { problems.append("no published application") }
        if !out.done { problems.append("no completed report") }
        if out.done && anySlotNotCompleted(out.slots) { problems.append("incomplete slot publication") }
        if let status = account.questions["final_status"] {
            switch (status.state, status.answer, status.value) {
            case ("unresolved", _, _):
                problems.append(status.reason == "no_successful_reap" ? "process disposition unconfirmed"
                                                                     : "reaped without usable exit status")
            case ("conflicting", _, _):
                problems.append("reaped with conflicting status representation")
            case ("supported", "signal"?, .integer(let signal)?):
                problems.append("reaped with signal \(signal)")
            case ("supported", "exit_code"?, .integer(let code)?):
                if code != 0 { problems.append("reaped with exit code \(code)") }
            default: break
            }
        }
        if killRequested { problems.append("host requested termination during cleanup") }
        // Recovered EINTR is retained evidence, not a run failure. A poll error
        // or any other wait error remains a host fault even if later reaped.
        if out.pollStopReason == "wait_error" || out.waitErrors == nil
            || out.waitErrors?.contains(where: { $0.errno != EINTR }) == true {
            problems.append("unresolved or unavailable host wait observations")
        }
        if !problems.isEmpty {
            return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1,
                error: "pw-probe-runner: " + problems.joined(separator: "; "))
        }
    }

    // Worker completed cleanly. Now classify the validator side.
    switch validatorResult {
    case nil:
        if expectedVerdictCount > 0 {
            return ClassifiedRun(outcome: NormalizedOutcome.validatorUnavailable, rc: 1,
                                 error: "validator not invoked; expected \(expectedVerdictCount) query results")
        }
        return ClassifiedRun(outcome: NormalizedOutcome.ok, rc: 0, error: nil)

    case .failure(let err, _):
        switch err {
        case .spawnFailed:
            return ClassifiedRun(
                outcome: NormalizedOutcome.validatorSpawnFailed,
                rc: 1, error: err.description
            )
        case .verdictParseFailed, .verdictDecodeFailed:
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
        var problems: [String] = []
        if vOut.reaped != true { problems.append("process disposition unconfirmed") }
        else if let signal = vOut.termSignal { problems.append("reaped with signal \(signal)") }
        else if vOut.exitCode != 0 { problems.append("nonzero or unavailable exit status \(String(describing: vOut.exitCode))") }
        if vOut.terminationRequest != nil { problems.append("host requested termination during cleanup") }
        if vOut.waitErrors == nil || vOut.waitErrors?.contains(where: { $0.errno != EINTR }) == true {
            problems.append("unresolved or unavailable host wait observations")
        }
        if let error = vOut.ioError { problems.append(error) }
        if let fault = vOut.decodeFault { problems.append("\(fault.kind): \(fault.message)") }
        if let expected = vOut.expectedProbes {
            let association = associateValidatorVerdicts(vOut.verdicts, expected: expected)
            if !association.issues.isEmpty || expected.count != expectedVerdictCount {
                problems.append("returned \(association.byStep.count) uniquely associated records; expected \(expectedVerdictCount); "
                    + association.issues.map { "\($0.kind):\($0.step_id ?? "null")" }.joined(separator: ", "))
            }
        } else { problems.append("submitted queries unavailable") }
        if !problems.isEmpty {
            return ClassifiedRun(outcome: NormalizedOutcome.validatorUnavailable, rc: 1,
                                 error: "validator: " + problems.joined(separator: "; "))
        }
        return ClassifiedRun(outcome: NormalizedOutcome.ok, rc: 0, error: nil)
    }
}

import Darwin
import Foundation

extension CWorkerOrchestrator {
    // ---- validation -----------------------------------------------------

    /// Every capacity refusal, decided from the decoded request alone. The
    /// service runs this before semantic validation so that no later
    /// diagnostic can echo an unbounded string: top-level strings first, then
    /// the worker's shared-memory bounds in plan order, then the host-only
    /// query strings and labels. Both service and direct orchestration use this
    /// gate; the driver also retains its checks local to the ABI writer.
    static func admissionFailure(for parsed: PWRunnerRunSpec) -> PWRunnerAdmissionFailure? {
        if let refused = requestAdmissionFailure(parsed) { return refused }
        // Count checks precede translating an unbounded plan or sorting params.
        if let phases = parsed.phases {
            if phases.count > PWShmLayout.maxPhases {
                return PWRunnerAdmissionFailure(field: "phases", actual: phases.count, maximum: PWShmLayout.maxPhases, unit: "items")
            }
            let count = phases.reduce(0) { $0 + $1.actions.count }
            if count > PWShmLayout.maxSteps {
                return PWRunnerAdmissionFailure(field: "phases.actions", actual: count, maximum: PWShmLayout.maxSteps, unit: "items")
            }
            for (index, phase) in phases.enumerated() {
                if var failure = AdmissionStringRule(field: "phase_id", maximum: requestLabelMaxBytes, requiresCString: true).failure(phase.phase_id) {
                    failure.index = index
                    return failure
                }
            }
        }
        if parsed.probe_plan.count > PWShmLayout.maxSteps {
            return PWRunnerAdmissionFailure(field: "probe_plan", actual: parsed.probe_plan.count,
                maximum: PWShmLayout.maxSteps, unit: "items")
        }
        if let count = parsed.policy.params?.count, count > PWShmLayout.maxParams {
            return PWRunnerAdmissionFailure(field: "policy.params", actual: count,
                maximum: PWShmLayout.maxParams, unit: "items")
        }
        let capacity = CWorkerInput(workerExecutablePath: "", policy: parsed.policy.sbpl_source ?? "",
            params: workerParamsFromPolicy(parsed.policy), slots: workerSlotsFromProbePlan(parsed.probe_plan))
        if let refused = workerAdmissionFailure(capacity) { return refused }
        return queryAdmissionFailure(parsed.probe_plan)
    }
}

// MARK: - Helpers

let phaseCollectionBudgetMs = 30_000

/// Resolve the sentinel-timeout for the C worker from the request's
/// `_test_overrides.worker_timeout_ms`. Floor at 50 ms because a
/// smaller deadline fires before any real worker can complete its
/// post-apply work. nil/absent → CWorkerInput default (120s, the worker
/// window; the separate C exec budget leaves a nominal publication margin,
/// not a guarantee against blocking native calls; see docs/LIMITS.md).
func timeoutMsForCWorker(override: Int?) -> Int {
    let cWorkerDefault = CWorkerInput.defaultSentinelTimeoutMs
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

func makeWorkerSlot(stepID: String, attempt: PWRunnerAttempt) -> CWorkerSlotInput {
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
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionReadFresh):
        return .fileReadFresh
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionWriteFresh):
        return .fileWriteFresh
    case (PWRunnerWire.attemptKindFile, PWRunnerWire.attemptActionCreateFresh):
        return .fileCreateFresh
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

func workerParamsFromPolicy(_ policy: PWRunnerPolicySpec) -> [CWorkerParam] {
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
// Bound submitted labels before meaning validation. Unknown labels within the
// bound are refused; recognized labels may be echoed in several evidence fields.
let probePlanLabelMaxBytes = 127

/// Host-only capacity check for the sandbox_check strings, using the same
/// record as the driver's shared-memory bounds. The value is bounded for every
/// filter kind, including `none` and unrecognized kinds, because the reply
/// echoes whatever was supplied. Filter kind and attempt labels also stay on
/// the host and are echoed even when unrecognized. Checks run in plan order,
/// operation then value then labels within a step, and report the first excess.
func queryAdmissionFailure(_ plan: [PWRunnerProbeStep]) -> PWRunnerAdmissionFailure? {
    for (position, step) in plan.enumerated() {
        let fields: [(AdmissionStringRule, String?)] = [
            (AdmissionStringRule(field: "sandbox_check.operation", maximum: sandboxCheckOperationMaxBytes, requiresCString: true), step.sandbox_check.operation),
            (AdmissionStringRule(field: "sandbox_check.filter.value", maximum: sandboxCheckFilterValueMaxBytes, requiresCString: true), step.sandbox_check.filter.value),
            (AdmissionStringRule(field: "sandbox_check.filter.kind", maximum: probePlanLabelMaxBytes), step.sandbox_check.filter.kind),
            (AdmissionStringRule(field: "attempt.kind", maximum: probePlanLabelMaxBytes), step.attempt.kind),
            (AdmissionStringRule(field: "attempt.action", maximum: probePlanLabelMaxBytes), step.attempt.action),
        ]
        for (rule, value) in fields {
            if var refused = rule.failure(value) {
                refused.step_id = stepIdAdmission.safeEcho(step.step_id)
                refused.step_index = position
                return refused
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

// The same rules select refusals and decide which metadata may be echoed.
// Adding a field requires an entry here and an explicit projection below.
let specimenIdAdmission = AdmissionStringRule(field: "specimen_id", maximum: specimenIdMaxBytes)
let runKindAdmission = AdmissionStringRule(field: "run_kind", maximum: requestLabelMaxBytes)
let policyFormatAdmission = AdmissionStringRule(field: "policy.format", maximum: requestLabelMaxBytes)
let overridePathAdmissions: [(key: WritableKeyPath<PWRunnerTestOverrides, String?>, rule: AdmissionStringRule)] = [
    (\.worker_executable_path, AdmissionStringRule(field: "_test_overrides.worker_executable_path", maximum: testOverridePathMaxBytes, requiresCString: true)),
    (\.issuer_executable_path, AdmissionStringRule(field: "_test_overrides.issuer_executable_path", maximum: testOverridePathMaxBytes, requiresCString: true)),
    (\.validator_executable_path, AdmissionStringRule(field: "_test_overrides.validator_executable_path", maximum: testOverridePathMaxBytes, requiresCString: true)),
]

func requestAdmissionFailure(_ parsed: PWRunnerRunSpec) -> PWRunnerAdmissionFailure? {
    for (rule, value) in [(specimenIdAdmission, parsed.specimen_id),
                           (runKindAdmission, parsed.run_kind), (policyFormatAdmission, parsed.policy.format)] {
        if let refused = rule.failure(value) { return refused }
    }
    if let declarations = parsed.extensions {
        if declarations.count > PWExtensionLimits.declarations { return PWRunnerAdmissionFailure(field: "extensions", actual: declarations.count, maximum: PWExtensionLimits.declarations, unit: "items") }
        for (i, declaration) in declarations.enumerated() {
            for (key, value, cap) in [("token_ref", declaration.token_ref, PWExtensionLimits.referenceBytes), ("target", declaration.target, PWExtensionLimits.targetBytes)] {
                if let failure = AdmissionStringRule(field: "extensions.\(i).\(key)", maximum: cap, requiresCString: true).failure(value) { return failure }
            }
        }
    }
    for (pi, phase) in (parsed.phases ?? []).enumerated() {
        for (ai, action) in phase.actions.enumerated() {
            guard case .extensionAction(let value) = action else { continue }
            for (key, text) in [("step_id", value.step_id), ("extension.operation", value.intervention.operation),
                                ("extension.token_ref", value.intervention.token_ref), ("extension.handle_ref", value.intervention.handle_ref)] {
                let cap = key.hasSuffix("_ref") ? PWExtensionLimits.referenceBytes : requestLabelMaxBytes
                if let failure = AdmissionStringRule(field: "phases.\(pi).actions.\(ai).\(key)", maximum: cap, requiresCString: true).failure(text) { return failure }
            }
        }
    }
    if let overrides = parsed._test_overrides {
        for (key, rule) in overridePathAdmissions {
            if let refused = rule.failure(overrides[keyPath: key]) { return refused }
        }
    }
    return nil
}

/// Failure selection and safe echo are independent: every metadata field is
/// checked even when a different field won admission precedence. No rejected
/// value is shortened into an apparent submitted identity.
func admissionRefusalReply(parsed: PWRunnerRunSpec, refused: PWRunnerAdmissionFailure,
                           bundleId: String?, policyHash: String? = nil) -> PWRunnerRunResult {
    var mirrored = parsed._test_overrides
    if var overrides = mirrored {
        for (key, rule) in overridePathAdmissions {
            overrides[keyPath: key] = rule.safeEcho(overrides[keyPath: key])
        }
        mirrored = overrides
    }
    var record = refused
    record.step_id = stepIdAdmission.safeEcho(record.step_id)
    record.parameter_key = parameterKeyAdmission.safeEcho(record.parameter_key)
    return PWRunnerRunResult(
        specimen_id: specimenIdAdmission.safeEcho(parsed.specimen_id) ?? "<admission_refused>",
        run_kind: runKindAdmission.safeEcho(parsed.run_kind), rc: 1,
        normalized_outcome: NormalizedOutcome.badRequest,
        error: CWorkerRunError.admissionFailed(record).description, pid: Int(getpid()),
        bundle_id: bundleId, policy_format: policyFormatAdmission.safeEcho(parsed.policy.format) ?? "unknown",
        policy_sha256: policyHash, steps: [], test_overrides: mirrored, admission_failure: record,
        request_failure: requestCapacityFailure(record, parsed: parsed))
}

func requestCapacityFailure(_ record: PWRunnerAdmissionFailure, parsed: PWRunnerRunSpec? = nil) -> PWRunnerRequestFailure {
    var path = record.field == "phases.actions" ? ["phases"] : record.field.split(separator: ".").map(String.init)
    if let index = record.step_index {
        if record.field == "target" || record.field == "args" { path.insert("attempt", at: 0) }
        path = (parsed?.probePath(index) ?? ["probe_plan", String(index)]) + path
    }
    if let index = record.index {
        if record.field == "phase_id" { path = ["phases", String(index), "phase_id"] }
        else { path.append(String(index)) }
    }
    // Parameter-key refusals deliberately withhold the key. The existing
    // admission record remains authoritative for exact counts and positions.
    if record.field == "key" {
        return PWRunnerRequestFailure(code: "admission_refused", path: nil)
    }
    if record.field == "value" {
        guard let key = record.parameter_key else { return PWRunnerRequestFailure(code: "admission_refused", path: nil) }
        path = ["policy", "params", key]
    }
    return PWRunnerRequestFailure(code: "admission_refused", path: path)
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

/// True when the step's path filter cannot resolve via realpath on the host
/// at query planning time. The planner excludes that validator query and
/// synthesizes prediction_unavailable; the attempt channel still runs.
/// Later host path diagnostics are a separate observation and can resolve
/// a target created by the attempt. Non-path filters and resolvable paths
/// are unaffected.
private func pathFilterIsUnresolvable(_ kind: String, _ value: String?) -> Bool {
    guard kind == PWRunnerWire.sandboxFilterPath else { return false }
    guard let v = value, !v.isEmpty else { return false }
    return canonicalizePath(v).resolved == nil
}

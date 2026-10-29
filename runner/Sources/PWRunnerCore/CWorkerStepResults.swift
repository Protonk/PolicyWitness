import Darwin
import Foundation

// MARK: - Step builder

func buildStepResults(
    probePlan: [PWRunnerProbeStep],
    queryPlan: [ValidatorQueryDecision],
    workerOutput: CWorkerOutput?,
    validatorOutput: ValidatorOutput?,
    ordering: PWRunnerOrdering? = nil,
    disposition: PWDispositionRecord? = nil,
    stepOffset: Int = 0
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

    // Join both channels for every step before any comparison.
    var channels: [(step: PWRunnerProbeStep, sandboxCheck: PWRunnerSandboxCheckResult,
                    attempt: PWRunnerAttemptResult)] = []
    channels.reserveCapacity(probePlan.count)
    for (localIndex, step) in probePlan.enumerated() {
        _ = localIndex + stepOffset
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
        let recordStep = account?.steps.first { $0.step_id == step.step_id }
        let supported = recordStep.map { $0.attempt_support == "supported" } ?? (mapAttemptKindOrNil(step.attempt) != nil)
        let slotState = recordStep?.slot ?? (slot == nil ? "absent" : slot!.completed ? "completed" : "incomplete")
        attempt.requested_kind = step.attempt.kind
        attempt.requested_action = step.attempt.action
        attempt.result_source = slotState == "completed" && supported ? "worker" : "synthetic"
        if attempt.result_source == "synthetic" {
            attempt.missing_reason = !supported ? "attempt_not_supported" : slotState == "absent" ? "slot_absent" : "slot_incomplete"
        }
        // The lifecycle object projects this step's two claims; the compatibility
        // triple above is unchanged.
        if let recordStep {
            attempt.lifecycle = attemptLifecycle(recordStep)
        }
        channels.append((step: step, sandboxCheck: sandboxCheck, attempt: attempt))
    }
    return channels.map { channel in
        var comparison = computeComparison(sandboxCheck: channel.sandboxCheck, attempt: channel.attempt,
            queryExclusionReason: decisions[channel.step.step_id]?.exclusionCode,
            order: eligibleOrderedStep(stepId: channel.step.step_id, query: channel.sandboxCheck,
                records: validatorOutput?.verdicts ?? [], ordering: ordering,
                sandboxedAfterApply: workerOutput?.applied == true && workerOutput?.applyRC == 0,
                workerPid: workerOutput.map { Int($0.workerPid) })
                ? .queryFirst : .unestablished)
        // Exactly one lifecycle limitation for a summary other than completed. It
        // never changes the observation, the relations or the order.
        if let summary = channel.attempt.lifecycle?.summary,
           let limitation = PWDisposition.limitationForSummary[summary] {
            comparison.limitations.append(limitation)
        }
        return PWRunnerStepResult(
            step_id: channel.step.step_id,
            sandbox_check: channel.sandboxCheck,
            attempt: channel.attempt,
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
    let kind = step.sandbox_check.filter.kind
    let value = step.sandbox_check.filter.value
    if let reason = exclusionReason {
        return PWRunnerSandboxCheckResult(rc: -1, outcome: SandboxCheckOutcome.predictionUnavailable,
            pid: sandboxCheckPid, operation: step.sandbox_check.operation,
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
// third host classification table alongside comparisonEvidence/classify; the
// test pins each cell so the two stacked tables (kind routing + the rc!=0
// action switch) can't silently diverge.
func buildAttemptResult(
    step: PWRunnerProbeStep,
    slot: CWorkerSlotResult?
) -> PWRunnerAttemptResult {
    // Unsupported attempt (kind, action): the orchestrator routed
    // the slot to PW_ATTEMPT_NONE so the worker no-ops it; surface
    // that here as outcome="unsupported" rather than letting the
    // rc=0 no-op masquerade as a successful "ok" observation. The
    // sandbox_check verdict for this step still runs and gets
    // attached normally; the comparison records an unavailable
    // observation with both relations unresolved.
    if mapAttemptKindOrNil(step.attempt) == nil {
        return PWRunnerAttemptResult(
            rc: -1,
            errno: nil,
            outcome: AttemptOutcome.unsupported,
            error: "kind='\(step.attempt.kind)', action='\(step.attempt.action)' not implemented",
            requested_path: step.attempt.target,
            observed_path: nil
        )
    }
    // Missing or incomplete slots establish no completed attempt result. The
    // outcome names that absence; the lifecycle evidence, not this builder,
    // says whether the operation started. Nothing below reads the slot's
    // unpublished fields: a result that was never released is withheld.
    guard let s = slot else {
        return PWRunnerAttemptResult(
            rc: -1,
            errno: nil,
            outcome: AttemptOutcome.noCompletedResult,
            error: "no completed attempt result: slot unavailable",
            requested_path: step.attempt.target,
            observed_path: nil
        )
    }
    if !s.completed {
        return PWRunnerAttemptResult(
            rc: -1,
            errno: nil,
            outcome: AttemptOutcome.noCompletedResult,
            error: "no completed attempt result: slot publication incomplete",
            requested_path: step.attempt.target,
            observed_path: nil
        )
    }

    // Slot completed. Map the C-worker rc/errno into the host's
    // attempt outcome vocabulary. The error string the worker wrote
    // already names which call failed (open / unlink / etc).
    //
    // Exec attempts are special: rc != 0 may mean either spawn-failed
    // (child_pid == 0) or child-exited-non-zero (child_pid > 0). Both
    // map to outcome=exec_failed; comparisonEvidence reads child_pid
    // downstream to distinguish them.
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
        case PWRunnerWire.attemptActionReadFresh:
            return AttemptOutcome.readFailed
        case PWRunnerWire.attemptActionWriteFresh, PWRunnerWire.attemptActionCreateFresh:
            return AttemptOutcome.writeFailed
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

    var result = PWRunnerAttemptResult(
        rc: Int(s.rc),
        errno: s.errnoVal == 0 ? nil : Int(s.errnoVal),
        outcome: outcome,
        error: s.error,
        requested_path: step.attempt.target,
        observed_path: s.observedPath,
        child_pid: s.childPid.map { Int($0) },
        child_exit_code: s.childExitCode.map { Int($0) },
        child_term_signal: s.childTermSignal.map { Int($0) },
        stdout: s.childStdout,
        stderr: s.childStderr
    )
    result.fresh_read = s.freshRead
    result.fresh_write = s.freshWrite
    result.exec_observation = s.execObservation
    result.execObservationDecodeProblem = s.execObservationProblem
    return result
}

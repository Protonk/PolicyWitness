import Darwin
import Foundation

// Shared association for step assembly and the worker disposition account.
// A duplicate identifier cannot choose an arbitrary slot as its evidence.
func uniquelyAssociatedWorkerSlots(_ slots: [CWorkerSlotResult]) -> [String: CWorkerSlotResult] {
    Dictionary(grouping: slots, by: { $0.stepId }).compactMapValues { $0.count == 1 ? $0[0] : nil }
}

// Internal for driver-to-reporting controls. Preserve the host's observations in the
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
    result.policy_transfer_timeout = out.policyTransferTimeout
    result.cleanup_trigger = out.cleanupTrigger
    result.grace_end = out.graceEnd
    result.collection_basis = out.collectionBasis
    result.ready_wait = out.readyWait
    result.sentinel_wait = out.sentinelWait
    result.exit_grace_wait = out.graceWait
    result.disposition = record
    return result
}

func buildValidatorSubprocess(_ out: ValidatorOutput, phaseId: String, ordinal: Int) -> PWRunnerValidatorSubprocess {
    var result = PWRunnerValidatorSubprocess(pid: Int(out.validatorPid),
        term_signal: out.termSignal.map(Int.init), exit_code: out.exitCode.map(Int.init))
    // The collection is bound to the phase whose plan it served; the record
    // carries that identity rather than leaving readers to infer it from PIDs.
    result.phase_id = phaseId
    result.ordinal = ordinal
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
    result.exit_grace_wait = out.exitGraceWait
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

    let finalStatus: PWDispositionClaim
    if out.reaped != true {
        finalStatus = unresolved("no_successful_reap", basis: ["reaped"])
    } else if out.exitCode != nil && out.termSignal != nil {
        finalStatus = conflict("D1", question: "final_status", stepIndex: nil,
            observations: ["exit_code", "term_signal"],
            detail: "one successful reap represented as both an exit status and a signal")
    } else if let signal = out.termSignal {
        finalStatus = supported("signal", value: .integer(Int(signal)), basis: ["reaped", "term_signal"])
    } else if let code = out.exitCode {
        finalStatus = supported("exit_code", value: .integer(Int(code)), basis: ["reaped", "exit_code"])
    } else {
        finalStatus = unresolved("status_unusable", basis: ["reaped"])
    }
    let stopReason: PWDispositionClaim
    if let stop = out.pollStopReason {
        stopReason = supported(stop, basis: ["poll_stop_reason"])
    } else {
        stopReason = unresolved(PWDisposition.notRecorded)
    }
    func cleanupClaim(_ raw: String?, reference: String) -> PWDispositionClaim {
        if out.exitRequested == false { return inapplicable("exit_not_requested") }
        if let raw { return supported(raw, basis: [reference, "exit_requested"]) }
        return unresolved(PWDisposition.notRecorded)
    }
    let cleanupTrigger = cleanupClaim(out.cleanupTrigger, reference: "cleanup_trigger")
    let graceEnd = cleanupClaim(out.graceEnd, reference: "grace_end")
    // A recorded request is a direct observation; only the absence of a request
    // needs the recorded cleanup stage (exit_requested) to count as observed.
    let killRequestAndResult: PWDispositionClaim
    if out.exitRequested == false {
        killRequestAndResult = inapplicable("exit_not_requested")
    } else if let request = out.terminationRequest {
        killRequestAndResult = supported("requested", value: .request(request), basis: ["termination_request"])
    } else if out.exitRequested == nil {
        killRequestAndResult = unresolved(PWDisposition.notRecorded)
    } else {
        killRequestAndResult = supported("none", basis: ["termination_request", "exit_requested"])
    }
    let collectionBasis: PWDispositionClaim
    if let basis = out.collectionBasis {
        collectionBasis = supported(basis, basis: ["collection_basis"])
    } else {
        collectionBasis = unresolved(PWDisposition.notRecorded)
    }

    let planSteps: [(id: String, supported: Bool)] = plan?.map { ($0.step_id, mapAttemptKindOrNil($0.attempt) != nil) }
        ?? out.slots.map { ($0.stepId, true) }
    var position: ProtocolPosition? = nil
    let progressAssociation: PWDispositionClaim
    switch associateProgress(out.workerEvidence?.progress, planCount: planSteps.count) {
    case nil:
        progressAssociation = inapplicable("no_progress_word")
    case .unrecognized?:
        progressAssociation = unresolved("progress_unrecognized", basis: ["progress"])
    case .invalid?:
        progressAssociation = supported("invalid", basis: ["progress", "plan"])
    case .stepIndex(let index, let at)?:
        progressAssociation = supported("step_index", value: .integer(index), basis: ["progress", "plan"])
        position = at
    case .parameterIndex(let index, let at)?:
        progressAssociation = supported("parameter_index", value: .integer(index), basis: ["progress"])
        position = at
    case .none(let at)?:
        progressAssociation = supported("none", basis: ["progress"])
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
        let boundary = ProtocolPosition(order: attemptOrder, index: i, stage: 1)
        let afterSlot = ProtocolPosition(order: attemptOrder, index: i, stage: 2)
        let applicability =
            supported(step.supported ? "supported" : "unsupported", basis: ["attempt_support"])
        let boundaryClaim: PWDispositionClaim
        if let at = position, at < boundary && completed && terminal {
            boundaryClaim = conflict("D5", question: "step_boundary_reached", stepIndex: i,
                observations: ["progress", "slot", "collection_basis"],
                detail: "a completed slot beside valid terminal progress that never reached it")
        } else if let at = position, at >= boundary {
            boundaryClaim = supported("reached", basis: present(["progress", "slot", "attempt_support"]))
        } else if completed && step.supported {
            boundaryClaim = supported("reached", basis: present(["progress", "slot", "attempt_support"]))
        } else if position != nil && !completed && terminal {
            boundaryClaim = supported("not_reached", basis: ["progress", "slot", "collection_basis"])
        } else if position != nil && !completed {
            boundaryClaim = unresolved("basis_not_terminal", basis: ["progress", "slot", "collection_basis"])
        } else {
            boundaryClaim = unresolved("no_usable_progress", basis: present(["progress", "slot"]))
        }
        let resultClaim: PWDispositionClaim
        if !step.supported {
            resultClaim = inapplicable("unsupported_attempt")
        } else if slotState == "absent" {
            resultClaim = unresolved("slot_unavailable", basis: ["slot"])
        } else if completed {
            resultClaim = supported("published", basis: ["slot", "attempt_support"])
        } else if !terminal {
            resultClaim = unresolved("basis_not_terminal", basis: ["slot", "collection_basis"])
        } else if let at = position, at >= afterSlot {
            resultClaim = conflict("D5", question: "step_result_published", stepIndex: i,
                observations: ["progress", "slot", "collection_basis"],
                detail: "valid returned progress for this step or a later position beside an incomplete slot")
        } else {
            resultClaim = supported("unpublished", basis: present(["slot", "collection_basis", "progress"]))
        }
        steps.append(PWDispositionStep(index: i, step_id: step.id, slot: slotState,
                                       attempt_support: step.supported ? "supported" : "unsupported", questions: PWDispositionStepQuestions(
                                           step_boundary_reached: boundaryClaim, step_result_published: resultClaim,
                                           step_requested_operation_applicability: applicability)))
    }
    return PWDispositionRecord(questions: PWDispositionRunQuestions(
        final_status: finalStatus, stop_reason: stopReason, cleanup_trigger: cleanupTrigger,
        grace_end: graceEnd, kill_request_and_result: killRequestAndResult,
        collection_basis: collectionBasis, progress_association: progressAssociation), steps: steps, issues: issues)
}

func attemptLifecycle(_ step: PWDispositionStep) -> PWAttemptLifecycle? {
    guard let boundary = step.questions.step_boundary_reached,
          let result = step.questions.step_result_published else { return nil }
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

/// Names for PW_TIME_REASON_* (pw_probe_runner_abi.h), the detail of a local
/// timing refusal (code 14). Unknown values stay numeric, never milliseconds.
func workerTimeReason(_ detail: UInt32) -> String {
    let names: [UInt32: String] = [1: "invalid_timebase", 2: "invalid_duration", 3: "backwards_counter",
                                   4: "unrepresentable_delta", 5: "deadline_overflow", 6: "prior_clock_fault"]
    return names[detail] ?? "unknown(\(detail))"
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
        case .policyTransferTimedOut:
            return ClassifiedRun(outcome: NormalizedOutcome.runnerTimeout, rc: 1, error: err.description)
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
                    4: "sandbox_set_param", 5: "sandbox_compile_string", 8: "sandbox_apply", 11: "proceed wait",
                    12: "clock setup", 13: "activation wait"]
                let operation = names[failure.operation] ?? "operation \(failure.operation)"
                var detail = "pw-probe-runner reported \(operation) failure (code=\(failure.code))"
                if failure.code == 15 && failure.native_kind == 0 {
                    detail += failure.operation == 12 ? "; actor lifetime cutoff already past at clock setup; no policy byte read"
                                                       : "; actor lifetime cutoff expired while waiting"
                }
                if failure.operation == 13 && failure.code == 16 && failure.native_kind == 0 {
                    detail += "; activation ordinal \(failure.detail) names a later visit; actor never arrived"
                }
                if failure.operation == 11 {
                    switch (failure.code, failure.native_kind) {
                    case (8, 0), (1, 3):
                        detail += "; budget=\(failure.detail) ms; release not observed"
                    case (11, 0):
                        detail += "; observed_release_ordinal=\(failure.detail); phase release rejected"
                    case (14, 0) where failure.detail == 6:
                        // A refusal caused by an earlier rejected sample, not a new one.
                        detail += "; proceed refused: worker clock already invalid"
                    case (14, 0):
                        detail += "; local timing refusal reason=\(workerTimeReason(failure.detail))"
                    default: break // Unknown detail units remain uninterpreted.
                    }
                }
                if failure.operation == 12 && failure.code == 14 && failure.native_kind == 0 {
                    detail += "; local timing refusal reason=\(workerTimeReason(failure.detail)); no policy byte read"
                }
                // Policy delivery refusals name their byte counts: the host's
                // expectation that exceeded the source capacity, or the count
                // read at EOF that differed from the expectation. Neither says
                // what the pipe carried beyond those counts.
                if failure.operation == 1 && failure.code == 12 && failure.native_kind == 0 {
                    detail += "; expected=\(failure.detail) bytes exceeds the source capacity; no policy byte read"
                }
                if failure.operation == 2 && failure.code == 13 && failure.native_kind == 0 {
                    detail += "; received=\(failure.detail) bytes at EOF differs from the submission; source not compiled"
                }
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
        if out.authoritySetup?.disposition == "terminal_required_failure" {
            return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1,
                error: "pw-probe-runner refused required authority setup before policy processing")
        }
        if out.authoritySetup?.integrity_errors != nil {
            return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1,
                error: "pw-probe-runner authority setup evidence failed integrity validation")
        }
        if out.applied && out.applyRC != 0 {
            return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1,
                error: "pw-probe-runner published inconsistent application state")
        }
        if !out.applied && out.done {
            return ClassifiedRun(outcome: NormalizedOutcome.runnerFailed, rc: 1,
                error: "pw-probe-runner completed without an observed application; no native apply return is inferred")
        }
        // Lifecycle clauses render from the resolved account (the same account
        // the reply carries); worker, validator and setup diagnostics keep their
        // own owners and are composed with these clauses, not generated from them.
        let account = disposition ?? resolveDisposition(out, plan: nil)
        let killRequested = account.questions.kill_request_and_result?.answer == "requested"
        if account.questions.stop_reason?.answer == "sentinel_deadline" {
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
        if let status = account.questions.final_status {
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
        return ClassifiedRun(outcome: NormalizedOutcome.finished, rc: 0, error: nil)

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
        return ClassifiedRun(outcome: NormalizedOutcome.finished, rc: 0, error: nil)
    }
}

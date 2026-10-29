import Darwin
import Foundation

enum ComparisonOrder: String { case queryFirst = "query_first", unestablished }

/// The per-step comparison record: the attempt channel classified by the
/// errno set, the `kr=1100` result and the spawned-child rule; the attempt
/// mapped through PW's operation and filter table against the submitted query;
/// the order PW established; and the planner's exclusion code. Lifecycle
/// entries are appended by the step builder. Nothing here asserts agreement
/// or disagreement between the two channels.
struct ComparisonEvidence {
    var order: ComparisonOrder
    var observation: String
    var basis: String
    var operationRelation: String
    var targetRelation: String
    var limitations: [String]

    var comparison: PWRunnerComparison {
        PWRunnerComparison(observation: observation, observation_basis: basis, operation_relation: operationRelation,
            target_relation: targetRelation, order: order.rawValue, limitations: limitations)
    }
}

func buildPhaseOrdering(_ worker: CWorkerOutput, index: Int, input: CWorkerPhaseInput,
                        validatorOutput: ValidatorOutput?, hasQueries: Bool) -> PWRunnerOrdering {
    let phase = worker.phases[index]
    // Reuse the single collection's claim rules on this phase's observations.
    var view = worker
    view.hookInvoked = phase.collectionClosed
    view.proceedSet = phase.releaseSet
    view.proceedObserved = phase.acknowledged
    view.proceedOwnershipEstablished = phase.ownershipEstablished
    view.orderingProtocolViolations = phase.violations
    view.slots = Array(worker.slots[input.firstSlot..<input.endSlot])
    if view.workerEvidence?.failure?.operation == 11 && view.workerEvidence?.failure?.index != UInt32(index) {
        view.workerEvidence?.failure = nil
    }
    return buildOrdering(view, validatorOutput: validatorOutput, hasQueries: hasQueries)
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
                       queryExclusionReason: String? = nil, order: ComparisonOrder = .unestablished) -> PWRunnerComparison {
    comparisonEvidence(sandboxCheck: sandboxCheck, attempt: attempt, queryExclusionReason: queryExclusionReason,
                       order: order).comparison
}

// Internal for independent scenario controls. Query order alone establishes
// an interval before the attempt batch, never equal state or runtime identity.
func comparisonEvidence(
    sandboxCheck: PWRunnerSandboxCheckResult,
    attempt: PWRunnerAttemptResult,
    queryExclusionReason: String? = nil,
    order: ComparisonOrder = .unestablished
) -> ComparisonEvidence {
    var limits: [String] = []
    if let reason = queryExclusionReason { limits.append("query_plan:" + reason) }

    var observation = "unavailable"
    var basis = "no_completed_worker_result"
    if attempt.result_source == "worker" {
        if attempt.requested_kind == "exec", (attempt.child_pid ?? 0) > 0 {
            // A positive child PID establishes spawning independently of the
            // child's later result, which attempt.rc and child_exit_code carry.
            observation = "succeeded"
            basis = "spawned_child"
        } else if attempt.outcome == AttemptOutcome.ok && attempt.rc == 0 {
            observation = "succeeded"
            basis = "completed_worker_status"
        } else if attempt.rc != 0 {
            observation = "other_failure"
            basis = "completed_worker_status"
            if [AttemptOutcome.openFailed, AttemptOutcome.readFailed, AttemptOutcome.writeFailed, AttemptOutcome.unlinkFailed,
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

    // The submitted attempt mapped to the query operation and filter kind it
    // corresponds to. A compound create has no single query operation.
    let operation: String?
    let filter: String?
    switch (attempt.requested_kind, attempt.requested_action) {
    case ("file", "open_read"), ("file", "access"), ("file", "read_fresh"):
        operation = "file-read-data"; filter = "path"
    case ("file", "open_write"), ("file", "write_fresh"):
        operation = "file-write-data"; filter = "path"
    case ("file", "unlink"):
        operation = "file-write-unlink"; filter = "path"
    case ("mach_lookup", "bootstrap_look_up"):
        operation = "mach-lookup"; filter = "global_name"
    case ("sysctl", "read"):
        operation = "sysctl-read"; filter = "sysctl_name"
    case ("exec", "spawn"):
        // The native query accepts this spelling, not bare process-exec. It
        // predicts target admission only, not every spawn prerequisite.
        operation = "process-exec*"; filter = "path"
    case ("file", "create"), ("file", "create_fresh"):
        operation = nil; filter = "path"
    default:
        operation = nil; filter = nil
    }
    let operationRelation: String
    let matchedExecQuery = operation == "process-exec*" && sandboxCheck.operation == operation
    let unresolvedBroadQuery = sandboxCheck.operation.contains("*") && !matchedExecQuery
    if operation == nil || unresolvedBroadQuery {
        operationRelation = "unresolved"
    } else {
        operationRelation = operation == sandboxCheck.operation ? "matched" : "different"
    }

    // Submitted strings only. Host resolution happens later and cannot
    // establish which object a query saw.
    let targetRelation: String
    if filter == nil || sandboxCheck.filter_kind != filter
        || sandboxCheck.filter_value == nil || attempt.requested_path == nil {
        targetRelation = "unresolved"
    } else {
        targetRelation = sandboxCheck.filter_value == attempt.requested_path
            ? "same_submitted" : "different_submitted"
    }
    return ComparisonEvidence(order: order, observation: observation, basis: basis,
        operationRelation: operationRelation, targetRelation: targetRelation, limitations: limits)
}

import Foundation
import Darwin

/// Eligibility of a native record for `order: query_first`.
func eligibleOrderedPrediction(_ query: PWRunnerSandboxCheckResult) -> Bool {
    guard query.result_source == "validator", let rc = query.native_rc,
          let err = query.errno, query.rc == rc else { return false }
    return (query.outcome == "allow" && rc == 0) || (query.outcome == "deny" && rc == 1 && err == 0)
}

// Shared by construction and reporting validation: a native record must be uniquely
// associated with this query and target the worker whose lifetime was observed.
// NONE has no native filter value, even if the request supplies an unused value.
func eligibleOrderedStep(stepId: String, query: PWRunnerSandboxCheckResult,
                         records: [ValidatorVerdict], ordering: PWRunnerOrdering?,
                         sandboxedAfterApply: Bool?, workerPid: Int?) -> Bool {
    guard ordering?.chainEstablished == true, sandboxedAfterApply == true,
          let workerPid, query.pid == workerPid, eligibleOrderedPrediction(query) else { return false }
    let matches = records.filter { $0.stepId == stepId }
    guard matches.count == 1, let record = matches.first else { return false }
    return record.operation == query.operation && record.filterType == query.filter_kind.uppercased()
        && record.filterValue == (query.filter_kind == "none" ? nil : query.filter_value) && record.outcome == query.outcome
        && record.rc == query.native_rc && record.errnoVal == query.errno
}

/// The per-step comparison record: the attempt channel's classified
/// observation, the submitted-scope relations, the order PW established and
/// the planner's exclusion or lifecycle limitations. It asserts nothing about
/// agreement or disagreement between prediction and enforcement.
struct PWRunnerComparison {
    // BEGIN GENERATED PORCELAIN PWRunnerComparison
    var observation: String
    var observation_basis: String
    var operation_relation: String
    var target_relation: String
    var order: String
    var limitations: [String]
    // END GENERATED PORCELAIN PWRunnerComparison

    /// The `limitations` vocabulary: the planner's exclusion codes and the
    /// lifecycle entries. Reporting validation rejects any other string.
    static let limitationVocabulary: Set<String> = Set([
        "query_plan:path_unresolved_at_planning", "query_plan:prediction_unavailable_pair",
        "query_plan:unrecognized_filter_kind",
    ]).union(PWDisposition.limitationForSummary.values)

    init(observation: String, observation_basis: String, operation_relation: String,
                target_relation: String, order: String, limitations: [String]) {
        self.observation = observation
        self.observation_basis = observation_basis
        self.operation_relation = operation_relation
        self.target_relation = target_relation
        self.order = order
        self.limitations = limitations
    }
}

struct PWRunnerStepResult {
    // BEGIN GENERATED PORCELAIN PWRunnerStepResult
    var phase_id: String
    var step_id: String
    var sandbox_check: PWRunnerSandboxCheckResult
    var attempt: PWRunnerAttemptResult
    /// Present on every step of an ordinary reply; withheld by a
    /// `runner_reporting_failed` reply.
    var comparison: PWRunnerComparison?
    /// Actor form: the actor whose process ran this step.
    var actor_id: String?
    // END GENERATED PORCELAIN PWRunnerStepResult

    init(
        step_id: String,
        phase_id: String = "main",
        sandbox_check: PWRunnerSandboxCheckResult,
        attempt: PWRunnerAttemptResult,
        comparison: PWRunnerComparison? = nil,
        actor_id: String? = nil
    ) {
        self.phase_id = phase_id
        self.step_id = step_id
        self.sandbox_check = sandbox_check
        self.attempt = attempt
        self.comparison = comparison
        self.actor_id = actor_id
    }



}

/// Authoritative worker process metadata, produced by the unsandboxed host.
/// Lifecycle observations are host-owned; worker_evidence uses the exact host/worker identity.
/// All live CWorkerOutput paths populate the optional observation fields below;
/// an absent observation is unknown, not false. Policy-write failures retain
/// partial child observations.
struct PWRunnerOrdering {
    // BEGIN GENERATED PORCELAIN PWRunnerOrdering
    var collection_closed_before_proceed: Bool
    var proceed_set: Bool
    var proceed_observed: Bool
    var validator_disposition: String
    /// Ownership through acknowledgement, not the eventual cleanup outcome.
    var worker_lifetime_established: Bool
    var protocol_violations: [String]
    // END GENERATED PORCELAIN PWRunnerOrdering

    var chainEstablished: Bool {
        collection_closed_before_proceed && proceed_set && proceed_observed
            && worker_lifetime_established && protocol_violations.isEmpty
    }
}

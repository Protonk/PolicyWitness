import Foundation

/// Evidence cannot support an ordinary report. This error carries a diagnostic,
/// not a copy of the full observation graph.
struct PWRunnerReportingValidationError: Error, CustomStringConvertible {
    let message: String
    var description: String { message }
}

import Darwin

/// Reading rules for the EOF receipt (tests/FAILURE-PROPAGATION-CONTRACT.md,
/// "Policy-transfer failure"): both counts lie within the source capacity, the
/// host's own `bytes_expected` on any transfer record agrees with the receipt's,
/// and a length refusal (operation 2, code 13) names the received count while the
/// counts differ. Unequal counts can precede termination without a refusal, but
/// cannot coexist with observations of compilation or later worker execution.
func policyReadProblem(_ result: PWRunnerRunResult) -> String? {
    guard let sub = result.runner_subprocess, let evidence = sub.worker_evidence,
          let read = evidence.policy_read else { return nil }
    let capacity = policyReceiptCapacityBytes
    guard (0...capacity).contains(read.bytes_expected), (0...capacity).contains(read.bytes_received) else {
        return "policy_read counts must lie within the source capacity"
    }
    if let timeout = sub.policy_transfer_timeout, timeout.bytes_expected != read.bytes_expected {
        return "policy_transfer_timeout.bytes_expected disagrees with policy_read.bytes_expected"
    }
    if let error = sub.policy_transfer_error, error.bytes_expected != read.bytes_expected {
        return "policy_transfer_error.bytes_expected disagrees with policy_read.bytes_expected"
    }
    if let failure = sub.worker_evidence?.failure, failure.operation == 2, failure.code == 13,
       read.bytes_received == read.bytes_expected || Int(failure.detail) != read.bytes_received {
        return "a length refusal must name the received count while the counts differ"
    }
    if read.bytes_received != read.bytes_expected {
        // Only known operations imply passage beyond the length guard. Open
        // numeric codes must not acquire a temporal meaning from their magnitude.
        let afterPolicyRead: Set<UInt32> = [3, 4, 5, 6, 7, 8, 9, 10, 11]
        if result.sandboxed_after_apply == true || sub.ready_byte_received == true || sub.done_observed == true
            || evidence.readiness != nil
            || evidence.progress.map({ afterPolicyRead.contains($0.operation) }) == true
            || evidence.failure.map({ afterPolicyRead.contains($0.operation) }) == true
            || result.phases.contains(where: { $0.arrival_observed || $0.completion_observed || $0.ordering?.proceed_observed == true })
            || result.steps.contains(where: { $0.attempt.result_source == "worker" }) {
            return "unequal policy_read counts contradict observations after the policy length check"
        }
    }
    return nil
}

/// Ownership of a phase's validator collection, applied by every reader: the
/// block names its phase, its expected IDs are exactly this phase's eligible
/// query plan in action order, and its association issues are the ones its
/// records and that plan imply. The plan is read from the retained per-step
/// query decisions, never by resolving paths again. Numeric PID uniqueness is
/// not a rule: sequential children may reuse a PID. The identity does not
/// authenticate the validator executable or prove a native call.
func validatorOwnershipProblem(phase: PWRunnerPhaseResult, steps: [PWRunnerStepResult]) -> String? {
    guard let block = phase.validator_subprocess else { return nil }
    guard let owner = block.phase_id, let ordinal = block.ordinal else { return "validator collection lacks phase ownership" }
    if owner != phase.phase_id || ordinal != phase.ordinal { return "validator collection names another phase" }
    // Order is the step-order and partition checks' question; ownership asks
    // whether the plan names exactly this phase's eligible queries.
    let eligible = steps.filter { $0.phase_id == phase.phase_id && $0.sandbox_check.missing_reason != "query_not_requested" }
    guard let expected = block.expected_step_ids else { return "validator collection lacks its expected plan" }
    if Set(expected).count != expected.count || Set(expected) != Set(eligible.map { $0.step_id }) {
        return "validator expected IDs disagree with the phase's eligible query plan"
    }
    let probes = eligible.map { step in
        ValidatorQueryIdentity(stepId: step.step_id, operation: step.sandbox_check.operation,
                               filterType: mapFilterKindToValidator(step.sandbox_check.filter_kind),
                               filterValue: step.sandbox_check.filter_kind == PWRunnerWire.sandboxFilterNone ? nil : step.sandbox_check.filter_value)
    }
    guard let records = block.records, let issues = block.association_issues else {
        return "validator collection lacks records or association issues"
    }
    let recomputed = validatorAssociationIssues(records, expected: probes).issues
    func key(_ issue: PWValidatorAssociationIssue) -> String { "\(issue.kind)|\(issue.step_id ?? "")|\(issue.count)" }
    if issues.map(key).sorted() != recomputed.map(key).sorted() {
        return "validator association issues disagree with its records"
    }
    return nil
}

/// Host reply failure, separate from execution classification. Retained evidence
/// has no per-step comparison claims; original_* fields are diagnostic only.
struct PWRunnerReportingFailure {
    // BEGIN GENERATED PORCELAIN PWRunnerReportingFailure
    var origin: String = "runner_host"
    var diagnostic: String
    var original_rc: Int
    var original_normalized_outcome: String
    var original_error: String?
    var evidence_retained: Bool
    // END GENERATED PORCELAIN PWRunnerReportingFailure
}

/// Host observation of a failed validator launch; no child PID is implied.
/// posix_spawn returns the error code directly, independently of ambient errno.
/// Keep unfamiliar codes intact; diagnostic is descriptive, not a classifier.
struct PWRunnerSpawnFailure {
    // BEGIN GENERATED PORCELAIN PWRunnerSpawnFailure
    var origin: String = "runner_host"
    var operation: String = "posix_spawn"
    var executable_path: String
    var return_code: Int32
    var diagnostic: String
    // END GENERATED PORCELAIN PWRunnerSpawnFailure
}

// Reporting admission is explicit; the schema owns stored fields and binary writing.
/// One phase's immutable publications and its own collection. Unobserved
/// arrival/completion stay false; later progress never manufactures them.
struct PWRunnerPhaseResult {
    // BEGIN GENERATED PORCELAIN PWRunnerPhaseResult
    var phase_id: String
    var ordinal: Int
    var action_ids: [String]
    var arrival_observed: Bool
    var completion_observed: Bool
    var collection_status: String
    var ordering: PWRunnerOrdering?
    var validator_subprocess: PWRunnerValidatorSubprocess?
    var validator_spawn_failure: PWRunnerSpawnFailure?
    /// Actor form: the activated actor and its 1-based visit ordinal, and the
    /// host-measured intervals of the visit.
    var actor_id: String? = nil
    var actor_visit: Int? = nil
    var visit_timing: PWRunnerVisitTiming? = nil
    var termination_gate: PWRunnerTerminationGate? = nil
    var activation_observation: PWRunnerActorActivation? = nil
    // END GENERATED PORCELAIN PWRunnerPhaseResult

    var collectionEvidenceConsistent: Bool {
        let disposition = ordering?.validator_disposition
        let allowed: Bool
        switch collection_status {
        case "not_reached": allowed = disposition == nil || disposition == "not_invoked"
        case "not_needed": allowed = disposition == "not_needed"
        case "collected": allowed = ["not_spawned", "reaped", "unconfirmed"].contains(disposition ?? "")
        case "budget_exhausted": allowed = disposition == "not_spawned"
        case "clock_unavailable": allowed = disposition == "not_needed" || disposition == "not_spawned"
        default: allowed = false
        }
        guard allowed else { return false }
        if collection_status != "collected" {
            return validator_subprocess == nil && validator_spawn_failure == nil
        }
        if disposition == "not_spawned" {
            // Driver setup can fail before there is a native spawn observation.
            return validator_subprocess == nil
        }
        return validator_spawn_failure == nil && validator_subprocess?.reaped == (disposition == "reaped")
    }
}


struct PWRunnerRunResult {
    // BEGIN GENERATED PORCELAIN PWRunnerRunResult
    // Response wire version. Reporting admission accepts exactly
    // PWContract.responseSchema; docs/CONTRACT.md, "Supported versions".
    var schema_version: Int
    var specimen_id: String
    var run_kind: String?
    var rc: Int
    var normalized_outcome: String
    var error: String?
    var pid: Int
    var bundle_id: String?
    /// The legacy form's policy format and hash; absent for the actor form,
    /// whose actors carry their own.
    var policy_format: String?
    var policy_sha256: String?
    var compiled_profile: CompiledProfileCapture?
    var sandboxed_after_apply: Bool?
    var steps: [PWRunnerStepResult]
    var runner_subprocess: PWRunnerSubprocess?
    var admission_failure: PWRunnerAdmissionFailure?
    var request_failure: PWRunnerRequestFailure?
    var phases: [PWRunnerPhaseResult]
    var extension_events: [PWRunnerExtensionEvent]?
    var test_overrides: PWRunnerTestOverrides?
    var reporting_failure: PWRunnerReportingFailure?
    /// `single_worker` or `actors`; emitted from the integrated actor contract.
    var execution_form: String?
    var actors: [PWRunnerActorResult]?
    var transfers: [PWRunnerTransferRecord]?
    var resources: PWRunnerResourceTables?
    var schedule: PWRunnerScheduleRecord?
    var preparation_failure: PWRunnerPreparationFailure?
    var equipment_inventory: PWRunnerEquipmentInventory?
    var equipment_bindings: [PWRunnerEquipmentBinding]?
    var equipment_entitlements: [PWRunnerEquipmentEntitlements]?
    var authority_setup: PWRunnerAuthoritySetup?
    // END GENERATED PORCELAIN PWRunnerRunResult

    init(
        schema_version: Int = PWContract.responseSchema,
        specimen_id: String,
        run_kind: String? = nil,
        rc: Int,
        normalized_outcome: String,
        error: String? = nil,
        pid: Int,
        bundle_id: String? = nil,
        policy_format: String?,
        policy_sha256: String? = nil,
        sandboxed_after_apply: Bool? = nil,
        steps: [PWRunnerStepResult],
        runner_subprocess: PWRunnerSubprocess? = nil,
        phases: [PWRunnerPhaseResult] = [],
        extension_events: [PWRunnerExtensionEvent]? = nil,
        test_overrides: PWRunnerTestOverrides? = nil,
        compiled_profile: CompiledProfileCapture? = nil,
        admission_failure: PWRunnerAdmissionFailure? = nil,
        reporting_failure: PWRunnerReportingFailure? = nil,
        request_failure: PWRunnerRequestFailure? = nil
    ) {
        self.schema_version = schema_version
        self.specimen_id = specimen_id
        self.run_kind = run_kind
        self.rc = rc
        self.normalized_outcome = normalized_outcome
        self.error = error
        self.pid = pid
        self.bundle_id = bundle_id
        self.policy_format = policy_format
        self.policy_sha256 = policy_sha256
        self.compiled_profile = compiled_profile
        self.admission_failure = admission_failure
        self.request_failure = request_failure
        self.sandboxed_after_apply = sandboxed_after_apply
        self.steps = steps
        self.runner_subprocess = runner_subprocess
        self.extension_events = extension_events
        self.phases = phases
        self.test_overrides = test_overrides
        self.reporting_failure = reporting_failure
    }

    /// Admission for reporting is independent of the selected output codec.
    /// Degraded replies retain contradictory observations but cannot retain claims.
    func validateForReporting() throws {
        // Only the current response is reported; these are its evidence rules.
        guard schema_version == PWContract.responseSchema else {
            throw PWRunnerReportingValidationError(message: "unsupported response schema \(schema_version) (this reporter emits \(PWContract.responseSchema))")
        }
        if let failure = reporting_failure {
            // The degraded reply retains observations and withholds every comparison.
            guard normalized_outcome == NormalizedOutcome.runnerReportingFailed,
                  rc == 1, error?.isEmpty == false, failure.origin == "runner_host",
                  !failure.diagnostic.isEmpty, !failure.original_normalized_outcome.isEmpty,
                  steps.allSatisfy({ $0.comparison == nil }),
                  failure.evidence_retained || (steps.isEmpty && runner_subprocess == nil && phases.isEmpty &&
                    (extension_events ?? []).isEmpty) else {
                throw PWRunnerReportingValidationError(message: "reporting failure requires a failed summary and no comparison claims")
            }
        } else {
            if normalized_outcome == NormalizedOutcome.runnerReportingFailed {
                throw PWRunnerReportingValidationError(message: "runner_reporting_failed requires reporting_failure diagnostics")
            }
            // The disposition record is mandatory beside a worker subprocess and
            // must agree with the raw facts it cites. The degraded reply above
            // skips this so a reported conflict is never lost.
            if let sub = runner_subprocess {
                guard let record = sub.disposition else {
                    throw PWRunnerReportingValidationError(message: "a worker subprocess requires the worker disposition record")
                }
                let problems = dispositionIntegrityProblems(record, subprocess: sub, stepCount: phases.reduce(0) { $0 + $1.action_ids.count }, steps: steps)
                if let first = problems.first {
                    throw PWRunnerReportingValidationError(message: "disposition record contradicts its basis: \(first)")
                }
                if let problem = policyReadProblem(self) {
                    throw PWRunnerReportingValidationError(message: "policy read receipt contradicts its basis: \(problem)")
                }
            }
            let phaseIDs = phases.map { $0.phase_id }
            let actionIDs = phases.flatMap { $0.action_ids }
            let eventIDs = (extension_events ?? []).map { $0.step_id }
            let stepIDs = steps.map { $0.step_id }
            let allIDs = stepIDs + eventIDs
            // Per-actor subprocesses carry their own disposition records, checked
            // against that actor's action count.
            for actor in actors ?? [] {
                guard let sub = actor.subprocess else { continue }
                guard let record = sub.disposition else {
                    throw PWRunnerReportingValidationError(message: "actor \(actor.actor_id): a worker subprocess requires the worker disposition record")
                }
                let actorPhases = phases.filter { $0.actor_id == actor.actor_id }
                let actorSteps = steps.filter { $0.actor_id == actor.actor_id }
                let problems = dispositionIntegrityProblems(record, subprocess: sub,
                    stepCount: actorPhases.reduce(0) { $0 + $1.action_ids.count }, steps: actorSteps)
                if let first = problems.first {
                    throw PWRunnerReportingValidationError(message: "actor \(actor.actor_id): disposition record contradicts its basis: \(first)")
                }
            }
            let phaseCap = execution_form == "actors" ? PWActorLimits.phases : PWRunnerPhase.maximumCount
            guard phases.count <= phaseCap, Set(phaseIDs).count == phases.count,
                  Set(actionIDs).count == actionIDs.count, actionIDs.count <= 256,
                  Set(allIDs).count == allIDs.count, (preparation_failure != nil || Set(actionIDs) == Set(allIDs)),
                  actionIDs.filter({ stepIDs.contains($0) }) == stepIDs,
                  actionIDs.filter({ eventIDs.contains($0) }) == eventIDs,
                  (runner_subprocess == nil || !phases.isEmpty) else {
                throw PWRunnerReportingValidationError(message: "phase identities and ordered actions must partition the reply")
            }
            for (index, phase) in phases.enumerated() {
                guard phase.collectionEvidenceConsistent else {
                    throw PWRunnerReportingValidationError(message: "phase collection status contradicts validator evidence")
                }
                if let issue = validatorOwnershipProblem(phase: phase, steps: steps) {
                    throw PWRunnerReportingValidationError(message: issue)
                }
                guard phase.ordinal == index + 1,
                      ["not_reached", "not_needed", "collected", "budget_exhausted", "clock_unavailable"].contains(phase.collection_status),
                      (runner_subprocess == nil || phase.ordering != nil),
                      (!phase.completion_observed || (phase.arrival_observed && phase.ordering?.proceed_observed == true)),
                      // Another actor's phase may arrive after an unfinished phase; the
                      // missing completion stays visible on the earlier phase. The same
                      // actor's next visit requires its previous completion.
                      (!phase.arrival_observed || index == 0 || phases[index - 1].completion_observed
                       || (execution_form == "actors" && phases[index - 1].actor_id != phase.actor_id)) else {
                    throw PWRunnerReportingValidationError(message: "invalid phase boundary account")
                }
            }
            if let issue = extensionEvidenceProblem() {
                throw PWRunnerReportingValidationError(message: issue)
            }
            for step in steps {
                if let issue = step.attempt.execObservationEvidenceProblem() {
                    throw PWRunnerReportingValidationError(message: issue)
                }
                if let issue = step.attempt.freshReadEvidenceProblem() {
                    throw PWRunnerReportingValidationError(message: issue)
                }
                if let issue = step.attempt.freshWriteEvidenceProblem() {
                    throw PWRunnerReportingValidationError(message: issue)
                }
                guard let phase = phases.first(where: { $0.phase_id == step.phase_id }), phase.action_ids.contains(step.step_id) else {
                    throw PWRunnerReportingValidationError(message: "step requires unique phase association")
                }
                guard let comparison = step.comparison else {
                    throw PWRunnerReportingValidationError(message: "every step of an ordinary reply carries a comparison record")
                }
                guard ["query_first", "unestablished"].contains(comparison.order) else {
                    throw PWRunnerReportingValidationError(message: "comparison.order must be query_first or unestablished")
                }
                if let outside = comparison.limitations.first(where: { !PWRunnerComparison.limitationVocabulary.contains($0) }) {
                    throw PWRunnerReportingValidationError(message: "limitation outside the vocabulary: \(outside)")
                }
                // The actor form's prerequisite and PID are the step's actor's own:
                // its declared or applied setup and its launched process.
                let actorRecord = execution_form == "actors" ? actors?.first(where: { $0.actor_id == step.actor_id }) : nil
                if execution_form == "actors" && (actorRecord == nil || phase.actor_id != step.actor_id) {
                    throw PWRunnerReportingValidationError(message: "step requires its phase's actor")
                }
                let established = actorRecord.map { ["applied", "unapplied_declared"].contains($0.setup_status) } ?? sandboxed_after_apply
                let workerPid = actorRecord != nil ? actorRecord!.launch?.pid : runner_subprocess?.pid
                if comparison.order == "query_first" && !eligibleOrderedStep(stepId: step.step_id, query: step.sandbox_check,
                    records: phase.validator_subprocess?.records ?? [], ordering: phase.ordering,
                    sandboxedAfterApply: established, workerPid: workerPid) {
                    throw PWRunnerReportingValidationError(message: "query_first requires eligible prediction and complete ordering chain")
                }
            }
        }
        // Receipt context applies to both ordinary and degraded reporting.
        // Keep it explicit, including the evidence-preserving degraded path.
        try compiled_profile?.validateForReporting()
        for actor in actors ?? [] {
            try actor.compiled_profile?.validateForReporting()
        }
    }


}

extension PWRunnerRunResult {
    /// The actor form's extension evidence rules: every event names a live
    /// actor and a phase of that actor, references resolve in the resource
    /// tables to their owners, transfers carry no native result, and each
    /// native status is published only by the shape it claims.
    func actorExtensionEvidenceProblem() -> String? {
        let events = extension_events ?? []
        guard let actors, !actors.isEmpty, actors.count <= PWActorLimits.actors,
              runner_subprocess == nil, policy_sha256 == nil, sandboxed_after_apply == nil else { return "actor form carries singular projections" }
        guard let resources, let transfers else { return "actor form lacks resource or transfer tables" }
        guard let equipment_inventory, let equipment_bindings, let equipment_entitlements, let authority_setup,
              actors.allSatisfy({ $0.equipment != nil && $0.application != nil }) else { return "actor form lacks setup/equipment/application account" }
        if let problem = pwRunnerEquipmentProblems(inventory: equipment_inventory, bindings: equipment_bindings,
            entitlements: equipment_entitlements, actors: actors.compactMap { $0.equipment },
            actorIDs: actors.map { $0.actor_id }, actorPIDs: actors.map { $0.launch?.pid }).first { return problem }
        if let problem = authoritySetupIntegrityErrors(authority_setup, actorIDs: actors.map { $0.actor_id },
            tokenRefs: resources.tokens.map { $0.token_ref }).first { return problem }
        for (index, actor) in actors.enumerated() {
            if let problem = actorApplicationIntegrityErrors(actor.application!, mode: actor.mode, launched: actor.launch != nil,
                applied: actor.applied == true, evidence: actor.subprocess?.worker_evidence,
                authority: authority_setup.workers.indices.contains(index) ? authority_setup.workers[index] : nil).first { return problem }
            if let reap = actor.owned_reap {
                guard reap.pid > 0, reap.native_rc == reap.pid, reap.capture_ordinal > 0,
                      reap.raw_status >= 0, reap.pid == actor.launch?.pid,
                      reap.pid == actor.subprocess?.pid, actor.subprocess?.reaped == true,
                      !reap.stage.isEmpty, reap.stage.utf8.count <= 64 else { return "owned reap process association" }
                let signal = Int(reap.raw_status & 0x7f)
                if signal == 0 {
                    guard actor.subprocess?.exit_code == Int((reap.raw_status >> 8) & 0xff),
                          actor.subprocess?.term_signal == nil else { return "owned reap exit status" }
                } else {
                    guard signal != 0x7f, actor.subprocess?.term_signal == signal,
                          actor.subprocess?.exit_code == nil else { return "owned reap signal status" }
                }
            }
        }
        if let failure = preparation_failure {
            guard ((failure.stage == "resolved_plan" && failure.code == "inconsistent_assignment")
                || (failure.stage == "equipment" && failure.code == "equipment_binding_refused")),
                normalized_outcome == NormalizedOutcome.runnerFailed, rc == 1, request_failure == nil,
                actors.allSatisfy({ $0.launch == nil && $0.subprocess == nil && $0.setup_status == "launch_refused" }),
                steps.isEmpty, events.isEmpty, transfers.isEmpty, resources.tokens.isEmpty,
                resources.deliveries.isEmpty, resources.handles.isEmpty,
                authority_setup.host.run.disposition == "not_attempted",
                authority_setup.host.regions.isEmpty, authority_setup.host.custody.isEmpty,
                phases.allSatisfy({ !$0.arrival_observed && !$0.completion_observed && $0.collection_status == "not_reached" })
                else { return "preparation refusal contains execution evidence" }
        }
        let failedInspection = actors.contains { actor in
            guard let equipment = actor.equipment else { return false }
            return ["mismatched", "inspection_failed"].contains(equipment.execution.status)
                || (equipment.execution.status == "unobserved" && !["not_launched", "setup_unavailable"].contains(equipment.execution.reason ?? ""))
        }
        if failedInspection {
            // An earlier setup/quiescence cancellation remains the first cause;
            // a later inspection failure is retained without replacing it.
            guard schedule?.cancelled?.isEmpty == false,
                phases.allSatisfy({ !$0.arrival_observed && !$0.completion_observed && $0.visit_timing == nil
                    && $0.activation_observation == nil && $0.collection_status == "not_reached"
                    && $0.ordering?.proceed_set != true && $0.ordering?.proceed_observed != true })
                else { return "equipment execution failure did not cancel all activation" }
        }
        for (index, phase) in phases.enumerated() {
            if let activation = phase.activation_observation, activation.capture_ordinal == 0 { return "invalid phase activation observation" }
            guard let gate = phase.termination_gate else { continue }
            guard let source = actors.first(where: { $0.actor_id == gate.source_actor_id }), source.actor_id != phase.actor_id,
                  let final = phases.lastIndex(where: { $0.actor_id == source.actor_id }), final < index,
                  phases[final].phase_id == gate.source_final_phase_id else { return "termination gate source association" }
            if let reference = gate.observation {
                guard let reap = source.owned_reap, let capture = gate.capture_ordinal,
                      reference.capture_ordinal > 0, reference.capture_ordinal == reap.capture_ordinal,
                      reference.capture_ordinal < capture else { return "termination gate reap reference" }
            }
            if let problem = terminationGateIntegrityErrors(gate,
                activationStored: phase.activation_observation != nil || phase.visit_timing != nil || phase.arrival_observed,
                collectionInvoked: phase.collection_status != "not_reached",
                releaseStored: phase.ordering?.proceed_set == true || phase.ordering?.proceed_observed == true).first { return problem }
            if gate.outcome == "satisfied" {
                guard let reap = source.owned_reap, let activation = phases[final].activation_observation,
                      let capture = gate.capture_ordinal, gate.observation?.capture_ordinal == reap.capture_ordinal,
                      activation.capture_ordinal < reap.capture_ordinal, reap.capture_ordinal < capture,
                      reap.ownership_unbroken, !reap.departure_requested,
                      ["schedule", "termination_gate"].contains(reap.stage),
                      let activatedAt = activation.observed_ns, let reapedAt = reap.observed_ns,
                      activatedAt <= reapedAt else { return "termination gate lacks natural owned reap after final activation" }
                if let dependentAt = phase.activation_observation?.observed_ns, dependentAt < reapedAt {
                    return "dependent activation precedes owned termination"
                }
            }
            if gate.activation_eligible {
                guard let dependent = actors.first(where: { $0.actor_id == phase.actor_id }),
                      ["applied", "unapplied_declared"].contains(dependent.setup_status),
                      dependent.equipment?.execution.eligible == true else { return "termination gate eligibility lacks independent setup" }
            }
        }
        guard resources.tokens.count <= PWActorLimits.issues, resources.deliveries.count <= PWActorLimits.deliveries,
              resources.handles.count <= PWActorLimits.handles, transfers.count <= PWActorLimits.deliveries,
              events.count <= PWActorLimits.issues + 2 * PWActorLimits.deliveries + PWActorLimits.handles + PWActorLimits.releases
        else { return "actor extension record capacity" }
        func validReference(_ value: String) -> Bool { !value.isEmpty && value.utf8.count <= PWExtensionLimits.referenceBytes && !value.utf8.contains(0) }
        let actorIDs = Set(actors.map { $0.actor_id })
        guard actorIDs.count == actors.count, phases.allSatisfy({ $0.actor_id.map(actorIDs.contains) == true && ($0.actor_visit ?? 0) >= 1 }),
              steps.allSatisfy({ $0.actor_id.map(actorIDs.contains) == true }) else { return "actor association on phases or steps" }
        for actor in actors {
            guard [0, 1].contains(actor.application_count), (actor.application_count == 1) == (actor.applied == true),
                  actor.setup_status != "applied" || actor.applied == true else { return "application count contradicts application publication" }
        }
        let ids = phases.flatMap { $0.action_ids }
        for references in [resources.tokens.map { $0.token_ref }, resources.deliveries.map { $0.delivery_ref },
                           resources.handles.map { $0.handle_ref }, transfers.map { $0.delivery_ref }] {
            guard references.allSatisfy(validReference), Set(references).count == references.count else {
                return "resource and transfer references must be unique"
            }
        }
        func before(_ first: String, _ second: String) -> Bool {
            guard let a = ids.firstIndex(of: first), let b = ids.firstIndex(of: second) else { return false }
            return a < b
        }
        var consumed: [String: PWRunnerExtensionEvent] = [:]
        var released = Set<String>()
        for event in events {
            guard let actorID = event.actor_id, let actor = actors.first(where: { $0.actor_id == actorID }) else { return "extension event actor" }
            guard let phase = phases.first(where: { $0.phase_id == event.phase_id }), phase.action_ids.contains(event.step_id),
                  phase.actor_id == actorID else { return "extension event phase association" }
            guard event.family == "file" else { return "extension event family" }
            switch event.operation {
            case "issue":
                guard let token = event.token_ref, validReference(token),
                      let record = resources.tokens.first(where: { $0.token_ref == token }), record.actor_id == actorID, record.step_id == event.step_id,
                      event.handle_ref == nil, event.delivery_ref == nil else { return "issue reference" }
                if event.status == "returned" && (event.native_result != 0 && event.native_result != 1
                    || event.native_nonnull != (event.native_result == 1)) { return "issue nonnull disagrees with native result" }
            case "transfer":
                guard let token = event.token_ref, let delivery = event.delivery_ref, validReference(token), validReference(delivery),
                      let record = resources.deliveries.first(where: { $0.delivery_ref == delivery }), record.token_ref == token,
                      record.source_actor_id == actorID, record.step_id == event.step_id, event.handle_ref == nil else { return "transfer reference" }
                guard let source = resources.tokens.first(where: { $0.token_ref == token }),
                      source.actor_id == actorID, before(source.step_id, event.step_id) else { return "transfer token owner/order" }
                guard !event.call_boundary_observed, event.native_result == nil, event.errno == nil else { return "transfer carries a native result" }
                guard event.status == "unresolved" ? !event.result_published
                      : event.result_published && PWTransferAck.names.values.contains(event.status) else { return "transfer status" }
            case "consume":
                guard let delivery = event.delivery_ref, let handle = event.handle_ref, validReference(delivery), validReference(handle),
                      let record = resources.handles.first(where: { $0.handle_ref == handle }), record.delivery_ref == delivery,
                      record.actor_id == actorID, record.step_id == event.step_id, event.token_ref == nil else { return "consume reference" }
                guard let source = resources.deliveries.first(where: { $0.delivery_ref == delivery }),
                      source.recipient_actor_id == actorID, before(source.step_id, event.step_id) else { return "consume delivery recipient/order" }
                if consumed[handle] != nil { return "repeated consume handle" }
                consumed[handle] = event
            case "release":
                guard let handle = event.handle_ref, validReference(handle), event.token_ref == nil, event.delivery_ref == nil,
                      let record = resources.handles.first(where: { $0.handle_ref == handle }), record.actor_id == actorID,
                      record.release_step_id == event.step_id, !released.contains(handle),
                      let prior = consumed[handle], let first = ids.firstIndex(of: prior.step_id), let second = ids.firstIndex(of: event.step_id), first < second
                else { return "release reference/order" }
                released.insert(handle)
                if event.status == "returned" && (prior.status != "returned" || prior.native_result == nil || prior.native_result == -1) { return "release lacks an observed consume handle" }
            default: return "unknown extension operation"
            }
            if let disposition = actor.subprocess?.disposition?.steps.first(where: { $0.step_id == event.step_id }) {
                if event.result_published != (disposition.slot == "completed") || event.lifecycle?.boundary != disposition.questions.step_boundary_reached || event.lifecycle?.result != disposition.questions.step_result_published {
                    return "extension publication disagrees with disposition"
                }
            } else if actor.subprocess != nil || event.call_boundary_observed || event.result_published || event.lifecycle != nil { return "extension event lacks disposition" }
            if event.operation != "transfer" {
                switch event.status {
                case "returned":
                    if !event.result_published || !event.call_boundary_observed || event.native_result == nil || event.errno == nil || (event.errno ?? 0) < 0 || event.unavailable_reason != nil { return "native extension result lacks publication" }
                case "unavailable":
                    if !event.result_published || event.call_boundary_observed || event.native_result != nil || event.errno != nil
                        || !["token_unavailable", "handle_unavailable", "native_api_unavailable", "repeated_action",
                             "authority_channel_unavailable", "delivery_unavailable"].contains(event.unavailable_reason ?? "") { return "unavailable extension action fabricates a call" }
                case "unresolved":
                    if event.result_published || event.native_result != nil || event.errno != nil || event.unavailable_reason != nil { return "unpublished extension result must stay unresolved" }
                default: return "invalid extension event status"
                }
            }
            let setupEstablished = actor.setup_status == "applied" || actor.setup_status == "unapplied_declared"
            if (event.result_published || event.call_boundary_observed) && (phase.ordering?.proceed_observed != true || !setupEstablished) {
                return "extension publication lacks setup and phase acknowledgement"
            }
        }
        for transfer in transfers {
            guard let delivery = resources.deliveries.first(where: { $0.delivery_ref == transfer.delivery_ref }),
                  delivery.token_ref == transfer.token_ref, delivery.source_actor_id == transfer.source_actor_id,
                  delivery.recipient_actor_id == transfer.recipient_actor_id, delivery.step_id == transfer.step_id,
                  PWTransferAck.names.values.contains(transfer.status) else { return "transfer record association" }
            guard let source = events.first(where: { $0.operation == "transfer" && $0.delivery_ref == transfer.delivery_ref }),
                  transfer.phase_id == source.phase_id, transfer.lifecycle == source.lifecycle else { return "transfer source phase/lifecycle association" }
            if transfer.status == "delivered" && (!transfer.request_published || transfer.custody_status != "held"
                || transfer.copy_status != "copied" || transfer.equality != "equal" || !transfer.recipient_acknowledged) {
                return "delivered transfer lacks custody, copy or recipient acknowledgement"
            }
            if transfer.source_acknowledged && !events.contains(where: { $0.operation == "transfer" && $0.step_id == transfer.step_id
                && $0.actor_id == transfer.source_actor_id && $0.result_published && $0.status == transfer.status }) {
                return "source acknowledgement lacks matching publication"
            }
        }
        for token in resources.tokens {
            guard let event = events.first(where: { $0.operation == "issue" && $0.token_ref == token.token_ref }) else { return "token lacks issue event" }
            if !event.result_published {
                let status = event.lifecycle?.boundary.state == "supported" && event.lifecycle?.boundary.answer == "not_reached"
                    && !event.call_boundary_observed ? "not_reached" : "unresolved"
                if token.status != status { return "unpublished resource status contradicts lifecycle" }
            } else if event.status == "unavailable" {
                if token.status != "unavailable" { return "token status contradicts issue" }
            } else if event.native_result == 0 {
                if token.status != "null" { return "token status contradicts issue" }
            } else if event.native_result == 1 {
                if !["issued", "issued_uncustodied"].contains(token.status) { return "token status contradicts issue" }
            }
            if token.family != "file" || token.token_length != event.token_length
                || (token.status == "issued" && !(1..<PWExtensionLimits.tokenBytes).contains(token.token_length ?? 0)) {
                return "token metadata contradicts issue"
            }
        }
        for handle in resources.handles {
            guard let event = events.first(where: { $0.operation == "consume" && $0.handle_ref == handle.handle_ref }) else { return "handle lacks consume event" }
            let status: String
            if !event.result_published {
                status = event.lifecycle?.boundary.state == "supported" && event.lifecycle?.boundary.answer == "not_reached"
                    && !event.call_boundary_observed ? "not_reached" : "unresolved"
            } else { status = event.status == "unavailable" ? "unavailable" : event.native_result == -1 ? "consume_failed" : "produced" }
            if handle.status != status || handle.native_handle != (status == "produced" ? event.native_result : nil) {
                return "handle status or value contradicts consume"
            }
            let release = events.first { $0.operation == "release" && $0.handle_ref == handle.handle_ref }
            if handle.release_step_id != release?.step_id || handle.release_attempted != (release?.call_boundary_observed == true) {
                return "handle release projection contradicts event"
            }
            let equal = resources.handles.filter { $0.handle_ref != handle.handle_ref && $0.actor_id == handle.actor_id
                && handle.native_handle != nil && $0.native_handle == handle.native_handle }.map { $0.handle_ref }
            if Set(handle.raw_equal_handles).count != handle.raw_equal_handles.count || Set(handle.raw_equal_handles) != Set(equal) {
                return "handle equality projection contradicts native handles"
            }
        }
        for delivery in resources.deliveries {
            guard let event = events.first(where: { $0.operation == "transfer" && $0.delivery_ref == delivery.delivery_ref }) else { return "delivery lacks transfer event" }
            guard actorIDs.contains(delivery.recipient_actor_id) else { return "delivery recipient does not exist" }
            if let host = transfers.first(where: { $0.delivery_ref == delivery.delivery_ref }) {
                // A host observation can survive missing source publication.
                if delivery.status != host.status || delivery.equality != host.equality {
                    return "delivery projection contradicts host transfer"
                }
                if host.status == "delivered" {
                    guard let length = delivery.delivered_length, (1..<PWExtensionLimits.tokenBytes).contains(length) else {
                        return "delivered length contradicts custody"
                    }
                    if let lengthFromIssue = resources.tokens.first(where: { $0.token_ref == delivery.token_ref })?.token_length,
                       lengthFromIssue != length { return "delivered length contradicts custody" }
                } else if delivery.delivered_length != nil { return "undelivered resource carries delivered length" }
                continue
            }
            if delivery.equality != nil || delivery.delivered_length != nil
                || !["none", "host_timeout", "clock_fault", "unresolved"].contains(event.status) {
                return "delivery claims host observation without transfer"
            }
            if event.result_published && delivery.status != (event.unavailable_reason ?? "unrequested") {
                return "unobserved delivery status contradicts source"
            }
            if !event.result_published {
                let status = event.lifecycle?.boundary.state == "supported" && event.lifecycle?.boundary.answer == "not_reached"
                    && !event.call_boundary_observed ? "not_reached" : "unresolved"
                if delivery.status != status { return "unpublished resource status contradicts lifecycle" }
            }
        }
        return nil
    }

    func extensionEvidenceProblem() -> String? {
        if execution_form == "actors" { return actorExtensionEvidenceProblem() }
        if !(extension_events ?? []).isEmpty { return "authority events require actor form" }
        if equipment_inventory != nil || equipment_bindings != nil || equipment_entitlements != nil || authority_setup != nil || preparation_failure != nil {
            return "actor evidence in ordinary reply"
        }
        return nil
    }
}

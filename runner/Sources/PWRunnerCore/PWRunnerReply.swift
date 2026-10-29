import Foundation
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
struct PWRunnerReportingFailure: Codable {
    var origin: String = "runner_host"
    var diagnostic: String
    var original_rc: Int
    var original_normalized_outcome: String
    var original_error: String?
    var evidence_retained: Bool
}

/// Host observation of a failed validator launch; no child PID is implied.
/// posix_spawn returns the error code directly, independently of ambient errno.
/// Keep unfamiliar codes intact; diagnostic is descriptive, not a classifier.
struct PWRunnerSpawnFailure: Codable {
    var origin: String = "runner_host"
    var operation: String = "posix_spawn"
    var executable_path: String
    var return_code: Int32
    var diagnostic: String
}

// Encoding is explicit to enforce response invariants. When adding a stored
// field, update CodingKeys and encode(to:), and populate the field-coverage
// round-trip fixture in ReplyFailureTests. Reflection stays in that test.
/// One phase's immutable publications and its own collection. Unobserved
/// arrival/completion stay false; later progress never manufactures them.
struct PWRunnerPhaseResult: Codable {
    var phase_id: String
    var ordinal: Int
    var action_ids: [String]
    var arrival_observed: Bool
    var completion_observed: Bool
    var collection_status: String
    var ordering: PWRunnerOrdering?
    var validator_subprocess: PWRunnerValidatorSubprocess?
    var validator_spawn_failure: PWRunnerSpawnFailure?

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

private enum RetiredProfileKey: String, CodingKey { case applied_profile }

struct PWRunnerRunResult: Codable {
    // Response wire version. Semantic decoding and encoding accept exactly
    // PWContract.responseSchema; docs/CONTRACT.md, "Supported versions".
    var schema_version: Int
    var specimen_id: String
    var run_kind: String?
    var rc: Int
    var normalized_outcome: String
    var error: String?
    var pid: Int
    var bundle_id: String?
    var policy_format: String
    var policy_sha256: String?
    var compiled_profile: CompiledProfileCapture?
    var sandboxed_after_apply: Bool?
    var steps: [PWRunnerStepResult]
    var runner_subprocess: PWRunnerSubprocess?
    var admission_failure: PWRunnerAdmissionFailure?
    var request_failure: PWRunnerRequestFailure?
    var phases: [PWRunnerPhaseResult]
    var extensions: [PWRunnerExtensionRecord]?
    var extension_events: [PWRunnerExtensionEvent]?
    var test_overrides: PWRunnerTestOverrides?
    var reporting_failure: PWRunnerReportingFailure?

    init(
        schema_version: Int = PWContract.responseSchema,
        specimen_id: String,
        run_kind: String? = nil,
        rc: Int,
        normalized_outcome: String,
        error: String? = nil,
        pid: Int,
        bundle_id: String? = nil,
        policy_format: String,
        policy_sha256: String? = nil,
        sandboxed_after_apply: Bool? = nil,
        steps: [PWRunnerStepResult],
        runner_subprocess: PWRunnerSubprocess? = nil,
        phases: [PWRunnerPhaseResult] = [],
        extensions: [PWRunnerExtensionRecord]? = nil,
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
        self.extensions = extensions
        self.extension_events = extension_events
        self.phases = phases
        self.test_overrides = test_overrides
        self.reporting_failure = reporting_failure
    }

    enum CodingKeys: String, CodingKey, CaseIterable {
        case schema_version, specimen_id, run_kind, rc, normalized_outcome, error, pid, bundle_id, policy_format, policy_sha256, compiled_profile, sandboxed_after_apply, steps, runner_subprocess, admission_failure, request_failure, phases, extensions, extension_events, test_overrides, reporting_failure
    }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        schema_version = try c.decode(Int.self, forKey: .schema_version)
        // Exactly the current response is decoded semantically; another number
        // is unsupported, never read under a previous version's rules.
        guard schema_version == PWContract.responseSchema else {
            throw DecodingError.dataCorruptedError(forKey: .schema_version, in: c,
                debugDescription: "unsupported response schema \(schema_version) (this reader accepts \(PWContract.responseSchema))")
        }
        let retired = try decoder.container(keyedBy: RetiredProfileKey.self)
        if retired.contains(.applied_profile) {
            throw DecodingError.dataCorruptedError(forKey: .applied_profile, in: retired,
                debugDescription: "retired applied_profile field in current runner reply")
        }
        specimen_id = try c.decode(String.self, forKey: .specimen_id)
        run_kind = try c.decodeIfPresent(String.self, forKey: .run_kind)
        rc = try c.decode(Int.self, forKey: .rc)
        normalized_outcome = try c.decode(String.self, forKey: .normalized_outcome)
        error = try c.decodeIfPresent(String.self, forKey: .error)
        pid = try c.decode(Int.self, forKey: .pid)
        bundle_id = try c.decodeIfPresent(String.self, forKey: .bundle_id)
        policy_format = try c.decode(String.self, forKey: .policy_format)
        policy_sha256 = try c.decodeIfPresent(String.self, forKey: .policy_sha256)
        compiled_profile = try c.decodeIfPresent(CompiledProfileCapture.self, forKey: .compiled_profile)
        sandboxed_after_apply = try c.decodeIfPresent(Bool.self, forKey: .sandboxed_after_apply)
        steps = try c.decode([PWRunnerStepResult].self, forKey: .steps)
        runner_subprocess = try c.decodeIfPresent(PWRunnerSubprocess.self, forKey: .runner_subprocess)
        admission_failure = try c.decodeIfPresent(PWRunnerAdmissionFailure.self, forKey: .admission_failure)
        request_failure = try c.decodeIfPresent(PWRunnerRequestFailure.self, forKey: .request_failure)
        extensions = try c.decodeIfPresent([PWRunnerExtensionRecord].self, forKey: .extensions)
        extension_events = try c.decodeIfPresent([PWRunnerExtensionEvent].self, forKey: .extension_events)
        phases = try c.decode([PWRunnerPhaseResult].self, forKey: .phases)
        test_overrides = try c.decodeIfPresent(PWRunnerTestOverrides.self, forKey: .test_overrides)
        reporting_failure = try c.decodeIfPresent(PWRunnerReportingFailure.self, forKey: .reporting_failure)
        if reporting_failure == nil {
            for step in steps {
                if let problem = step.attempt.execObservationEvidenceProblem() {
                    throw DecodingError.dataCorruptedError(forKey: .steps, in: c, debugDescription: problem)
                }
                if let problem = step.attempt.freshWriteEvidenceProblem() {
                    throw DecodingError.dataCorruptedError(forKey: .steps, in: c, debugDescription: problem)
                }
            }
        }
        if reporting_failure == nil, let problem = policyReadProblem(self) {
            throw DecodingError.dataCorruptedError(forKey: .runner_subprocess, in: c,
                debugDescription: "policy read receipt contradicts its basis: \(problem)")
        }
        if reporting_failure == nil, let sub = runner_subprocess, sub.disposition == nil {
            throw DecodingError.dataCorruptedError(forKey: .runner_subprocess, in: c,
                debugDescription: "a worker subprocess requires the worker disposition record")
        }
    }
    func encode(to encoder: Encoder) throws {
        // Only the current response is encoded; the invariants below are its rules.
        guard schema_version == PWContract.responseSchema else {
            throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                debugDescription: "unsupported response schema \(schema_version) (this encoder emits \(PWContract.responseSchema))"))
        }
        if let failure = reporting_failure {
            // The degraded reply retains observations and withholds every comparison.
            guard normalized_outcome == NormalizedOutcome.runnerReportingFailed,
                  rc == 1, error?.isEmpty == false, failure.origin == "runner_host",
                  !failure.diagnostic.isEmpty, !failure.original_normalized_outcome.isEmpty,
                  steps.allSatisfy({ $0.comparison == nil }),
                  failure.evidence_retained || (steps.isEmpty && runner_subprocess == nil && phases.isEmpty &&
                    (extensions ?? []).isEmpty && (extension_events ?? []).isEmpty) else {
                throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                    debugDescription: "reporting failure requires a failed summary and no comparison claims"))
            }
        } else {
            if normalized_outcome == NormalizedOutcome.runnerReportingFailed {
                throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                    debugDescription: "runner_reporting_failed requires reporting_failure diagnostics"))
            }
            // The disposition record is mandatory beside a worker subprocess and
            // must agree with the raw facts it cites. The degraded reply above
            // skips this so a reported conflict is never lost.
            if let sub = runner_subprocess {
                guard let record = sub.disposition else {
                    throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                        debugDescription: "a worker subprocess requires the worker disposition record"))
                }
                let problems = dispositionIntegrityProblems(record, subprocess: sub, stepCount: phases.reduce(0) { $0 + $1.action_ids.count }, steps: steps)
                if let first = problems.first {
                    throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                        debugDescription: "disposition record contradicts its basis: \(first)"))
                }
                if let problem = policyReadProblem(self) {
                    throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                        debugDescription: "policy read receipt contradicts its basis: \(problem)"))
                }
            }
            let phaseIDs = phases.map { $0.phase_id }
            let actionIDs = phases.flatMap { $0.action_ids }
            let eventIDs = (extension_events ?? []).map { $0.step_id }
            let stepIDs = steps.map { $0.step_id }
            let allIDs = stepIDs + eventIDs
            guard phases.count <= PWRunnerPhase.maximumCount, Set(phaseIDs).count == phases.count,
                  Set(actionIDs).count == actionIDs.count, actionIDs.count <= 256,
                  Set(allIDs).count == allIDs.count, Set(actionIDs) == Set(allIDs),
                  actionIDs.filter({ stepIDs.contains($0) }) == stepIDs,
                  actionIDs.filter({ eventIDs.contains($0) }) == eventIDs,
                  (runner_subprocess == nil || !phases.isEmpty) else {
                throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                    debugDescription: "phase identities and ordered actions must partition the reply"))
            }
            for (index, phase) in phases.enumerated() {
                guard phase.collectionEvidenceConsistent else {
                    throw EncodingError.invalidValue(phase, .init(codingPath: encoder.codingPath,
                        debugDescription: "phase collection status contradicts validator evidence"))
                }
                if let issue = validatorOwnershipProblem(phase: phase, steps: steps) {
                    throw EncodingError.invalidValue(phase, .init(codingPath: encoder.codingPath, debugDescription: issue))
                }
                guard phase.ordinal == index + 1,
                      ["not_reached", "not_needed", "collected", "budget_exhausted", "clock_unavailable"].contains(phase.collection_status),
                      (runner_subprocess == nil || phase.ordering != nil),
                      (!phase.completion_observed || (phase.arrival_observed && phase.ordering?.proceed_observed == true)),
                      (!phase.arrival_observed || index == 0 || phases[index - 1].completion_observed) else {
                    throw EncodingError.invalidValue(phase, .init(codingPath: encoder.codingPath,
                        debugDescription: "invalid phase boundary account"))
                }
            }
            if let issue = extensionEvidenceProblem() {
                throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath, debugDescription: issue))
            }
            for step in steps {
                if let issue = step.attempt.execObservationEvidenceProblem() {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath, debugDescription: issue))
                }
                if let issue = step.attempt.freshReadEvidenceProblem() {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath, debugDescription: issue))
                }
                if let issue = step.attempt.freshWriteEvidenceProblem() {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath, debugDescription: issue))
                }
                guard let phase = phases.first(where: { $0.phase_id == step.phase_id }), phase.action_ids.contains(step.step_id) else {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath,
                        debugDescription: "step requires unique phase association"))
                }
                guard let comparison = step.comparison else {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath,
                        debugDescription: "every step of an ordinary reply carries a comparison record"))
                }
                guard ["query_first", "unestablished"].contains(comparison.order) else {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath,
                        debugDescription: "comparison.order must be query_first or unestablished"))
                }
                if let outside = comparison.limitations.first(where: { !PWRunnerComparison.limitationVocabulary.contains($0) }) {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath,
                        debugDescription: "limitation outside the vocabulary: \(outside)"))
                }
                if comparison.order == "query_first" && !eligibleOrderedStep(stepId: step.step_id, query: step.sandbox_check,
                    records: phase.validator_subprocess?.records ?? [], ordering: phase.ordering,
                    sandboxedAfterApply: sandboxed_after_apply, workerPid: runner_subprocess?.pid) {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath,
                        debugDescription: "query_first requires eligible prediction and complete ordering chain"))
                }
            }
        }
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(schema_version, forKey: .schema_version)
        try c.encode(specimen_id, forKey: .specimen_id)
        try c.encodeIfPresent(run_kind, forKey: .run_kind)
        try c.encode(rc, forKey: .rc)
        try c.encode(normalized_outcome, forKey: .normalized_outcome)
        try c.encodeIfPresent(error, forKey: .error)
        try c.encode(pid, forKey: .pid)
        try c.encodeIfPresent(bundle_id, forKey: .bundle_id)
        try c.encode(policy_format, forKey: .policy_format)
        try c.encodeIfPresent(policy_sha256, forKey: .policy_sha256)
        try c.encodeIfPresent(compiled_profile, forKey: .compiled_profile)
        try c.encodeIfPresent(sandboxed_after_apply, forKey: .sandboxed_after_apply)
        try c.encode(steps, forKey: .steps)
        try c.encodeIfPresent(runner_subprocess, forKey: .runner_subprocess)
        try c.encodeIfPresent(admission_failure, forKey: .admission_failure)
        try c.encodeIfPresent(request_failure, forKey: .request_failure)
        try c.encode(phases, forKey: .phases)
        try c.encodeIfPresent(extensions, forKey: .extensions)
        try c.encodeIfPresent(extension_events, forKey: .extension_events)
        try c.encodeIfPresent(test_overrides, forKey: .test_overrides)
        try c.encodeIfPresent(reporting_failure, forKey: .reporting_failure)
    }

}

extension PWRunnerRunResult {
    func extensionEvidenceProblem() -> String? {
        let events = extension_events ?? []
        let declarations = extensions ?? []
        if declarations.count > PWExtensionLimits.declarations || events.count > PWExtensionLimits.consumes + PWExtensionLimits.releases || (!events.isEmpty && declarations.count != 1) { return "extension record capacity or association" }
        let ids = phases.flatMap { $0.action_ids }
        var consume: PWRunnerExtensionEvent?
        var released = false
        for event in events {
            func validReference(_ value: String) -> Bool { !value.isEmpty && value.utf8.count <= PWExtensionLimits.referenceBytes && !value.utf8.contains(0) }
            if !validReference(event.handle_ref) || event.handle_ref == declarations.first?.token_ref { return "extension handle reference" }
            guard let phase = phases.first(where: { $0.phase_id == event.phase_id }), phase.action_ids.contains(event.step_id) else { return "extension event phase association" }
            if event.operation == "consume" {
                if consume != nil || event.token_ref != declarations.first?.token_ref { return "extension consume reference" }
                consume = event
            } else if event.operation == "release" {
                guard !released, let prior = consume, prior.handle_ref == event.handle_ref, event.token_ref == nil,
                      let first = ids.firstIndex(of: prior.step_id), let second = ids.firstIndex(of: event.step_id), first < second else { return "extension release reference/order" }
                released = true
                if event.status == "returned" && (prior.status != "returned" || prior.native_result == nil || prior.native_result == -1) { return "release lacks an observed consume handle" }
                if let value = event.native_result, value < Int64(Int32.min) || value > Int64(Int32.max) { return "release result is not native int" }
            } else { return "unknown extension operation" }
            if let disposition = runner_subprocess?.disposition?.steps.first(where: { $0.step_id == event.step_id }) {
                if event.result_published != (disposition.slot == "completed") || event.lifecycle?.boundary != disposition.questions["step_boundary_reached"] || event.lifecycle?.result != disposition.questions["step_result_published"] {
                    return "extension publication disagrees with disposition"
                }
            } else if runner_subprocess != nil || event.call_boundary_observed || event.result_published || event.lifecycle != nil { return "extension event lacks disposition" }
            switch event.status {
            case "returned":
                if !event.result_published || !event.call_boundary_observed || event.native_result == nil || event.errno == nil || (event.errno ?? 0) < 0 || event.unavailable_reason != nil { return "native extension result lacks publication" }
                if event.operation == "consume" && declarations.first?.delivery_status != "delivered" { return "consumption lacks delivery" }
            case "unavailable":
                if !event.result_published || event.call_boundary_observed || event.native_result != nil || event.errno != nil || !["token_unavailable", "handle_unavailable", "native_api_unavailable", "repeated_action"].contains(event.unavailable_reason ?? "") { return "unavailable extension action fabricates a call" }
            case "unresolved":
                if event.result_published || event.native_result != nil || event.errno != nil || event.unavailable_reason != nil { return "unpublished extension result must stay unresolved" }
            default: return "invalid extension event status"
            }
            if (event.result_published || event.call_boundary_observed) && (phase.ordering?.proceed_observed != true || sandboxed_after_apply != true) { return "extension publication lacks application and phase acknowledgement" }
        }
        for declaration in declarations {
            guard ["com.apple.app-sandbox.read", "com.apple.app-sandbox.read-write"].contains(declaration.extension_class) else {
                return "invalid extension declaration class"
            }
            if declaration.issuance_status == "issuer_result_missing" {
                guard let issuer = declaration.issuer, !issuer.result_published,
                      issuer.native_nonnull == nil, issuer.errno == nil, issuer.token_length == nil,
                      issuer.uid == nil, issuer.euid == nil, issuer.gid == nil, issuer.egid == nil else {
                    return "missing issuer result carries publication or payload"
                }
            }
            if declaration.issuance_status == "issuer_abnormal_exit" {
                guard let issuer = declaration.issuer, issuer.result_published,
                      issuer.call_boundary_observed, issuer.native_nonnull == true,
                      issuer.reaped == true, let length = issuer.token_length,
                      length > 0 && length < PWExtensionLimits.tokenBytes,
                      (issuer.term_signal != nil || (issuer.exit_code != nil && issuer.exit_code != 0)),
                      declaration.delivery_status != "delivered" else { return "abnormal issuer exit lacks publication and reap" }
            }
            if declaration.issuance_status == "issued" {
                guard declaration.preparation_status == "prepared", declaration.resolved_target != nil,
                      declaration.identity != nil, declaration.issuer?.call_boundary_observed == true,
                      declaration.issuer?.native_nonnull == true, declaration.issuer?.result_published == true,
                      declaration.issuer?.reaped == true, declaration.issuer?.exit_code == 0,
                      declaration.issuer?.term_signal == nil, let length = declaration.issuer?.token_length,
                      length > 0 && length < PWExtensionLimits.tokenBytes else { return "issuance lacks bounded native result and issuer reap" }
            }
            guard PWExtensionDelivery.recordStatuses.contains(declaration.delivery_status) else { return "unknown delivery status" }
            if PWExtensionDelivery.failureStatuses.contains(declaration.delivery_status) {
                guard let failure = declaration.delivery_failure else { return "delivery failure lacks its account" }
                if let issue = failure.problem(status: declaration.delivery_status) { return issue }
                if declaration.delivery_status == "channel_rejected" && declaration.issuance_status != "issued" { return "channel rejection without an issued token" }
            } else if declaration.delivery_failure != nil { return "delivery failure account without a failure status" }
            if let cleanup = declaration.delivery_cleanup_failure,
               let issue = cleanup.problem(status: declaration.delivery_status) { return issue }
            if declaration.delivery_status != "delivered" && declaration.delivered_bytes != nil { return "undelivered extension carries delivered byte count" }
            if declaration.delivery_status == "delivered" {
                guard declaration.issuance_status == "issued", let bytes = declaration.delivered_bytes,
                      bytes > 0 && bytes < PWExtensionLimits.tokenBytes, bytes == declaration.issuer?.token_length,
                      declaration.issuer?.native_nonnull == true, declaration.issuer?.result_published == true,
                      declaration.issuer?.reaped == true, declaration.issuer?.exit_code == 0 else { return "delivery lacks bounded issuance and issuer reap" }
            }
        }
        return nil
    }
}

import Foundation
import Darwin

// MARK: - Worker disposition record
//
// Wire spellings shared with tests/lib/lifecycle_contract.py; DispositionContractTests
// compares them. The contract is tests/FAILURE-PROPAGATION-CONTRACT.md,
// "Worker disposition record". Every claim carries a state; a supported claim
// names its answer and the raw observations that support it; unresolved and
// inapplicable claims name a reason; a conflicting claim points at an issue.
enum PWDisposition {
    static let claimStates = ["supported", "unresolved", "conflicting", "inapplicable"]
    static let runQuestions = ["final_status", "stop_reason", "cleanup_trigger", "grace_end",
                                      "kill_request_and_result", "collection_basis", "progress_association"]
    static let stepQuestions = ["step_boundary_reached", "step_result_published",
                                       "step_requested_operation_applicability"]
    static let cleanupTriggers = ["deadline_expiry", "completion", "child_reaped", "poll_wait_error",
                                         "policy_transfer_error", "policy_transfer_timeout"]
    static let graceEnds = ["not_entered", "reaped_during_grace", "exhausted", "wait_error"]
    static let collectionBases = ["after_confirmed_reap", "execution_may_continue", "unavailable"]
    static let triggerForStop: [String: String] = [
        "sentinel_deadline": "deadline_expiry", "done": "completion", "child_reaped": "child_reaped",
        "wait_error": "poll_wait_error", "policy_write_error": "policy_transfer_error", "policy_transfer_deadline": "policy_transfer_timeout"]
    static let slotStates = ["completed", "incomplete", "absent"]
    static let attemptSupport = ["supported", "unsupported"]
    static let summaries = ["completed", "started_without_result", "not_reached", "unsupported",
                                   "unresolved", "conflicting"]
    static let limitationForSummary: [String: String] = [
        "started_without_result": "attempt:started_without_result", "not_reached": "attempt:not_reached",
        "unsupported": "attempt:unsupported", "unresolved": "attempt:lifecycle_unresolved",
        "conflicting": "attempt:lifecycle_conflicting"]
    static let causeForTrigger: [String: String] = [
        "deadline_expiry": "host_sentinel_deadline", "completion": "host_exit_grace_exhausted",
        "poll_wait_error": "host_cleanup_after_wait_error", "policy_transfer_error": "host_cleanup_after_transfer_error", "policy_transfer_timeout": "host_cleanup_after_transfer_timeout"]
    static let notRecorded = "not_recorded"
    /// Temporal order of worker operations (pw_probe_runner_abi.h): clock setup
    /// (12) follows header validation (1) and precedes the policy read (2);
    /// proceed (11) precedes the indexed attempts (9); completion (10) follows them.
    static let protocolOrder: [UInt32] = [1, 12, 2, 3, 4, 5, 6, 7, 8, 11, 9, 10]
    static let runReferences = ["reaped", "exit_code", "term_signal", "poll_stop_reason", "exit_requested",
                                       "termination_request", "wait_errors", "cleanup_trigger", "grace_end",
                                       "collection_basis", "done_observed", "progress", "worker_failure", "plan"]
    static let stepReferences = ["slot", "attempt_support"]
}

/// A claim value: an exit code, signal or index, or the termination request.
enum PWDispositionValue: Codable, Equatable {
    case integer(Int)
    case request(PWRunnerTerminationRequest)
    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if let integer = try? c.decode(Int.self) { self = .integer(integer); return }
        self = .request(try c.decode(PWRunnerTerminationRequest.self))
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer()
        switch self {
        case .integer(let integer): try c.encode(integer)
        case .request(let request): try c.encode(request)
        }
    }
}

struct PWDispositionClaim: Codable, Equatable {
    var state: String
    var answer: String? = nil
    var value: PWDispositionValue? = nil
    var reason: String? = nil
    var issue: Int? = nil
    var basis: [String]? = nil
}

struct PWDispositionIssue: Codable, Equatable {
    var kind: String
    var rule: String
    var question: String
    var step_index: Int? = nil
    var observations: [String]
    var detail: String
}

struct PWDispositionStep: Codable, Equatable {
    var index: Int
    var step_id: String
    var slot: String
    var attempt_support: String
    var questions: [String: PWDispositionClaim]
}

struct PWDispositionRecord: Codable, Equatable {
    var questions: [String: PWDispositionClaim]
    var steps: [PWDispositionStep]
    var issues: [PWDispositionIssue]
}

struct PWAttemptLifecycle: Codable, Equatable {
    var summary: String
    var boundary: PWDispositionClaim
    var result: PWDispositionClaim
}

// Shared wire interpretation: the API also builds in the standalone runner client.
struct ProtocolPosition: Comparable {
    let order: Int
    let index: Int
    let stage: Int
    static func < (a: ProtocolPosition, b: ProtocolPosition) -> Bool {
        (a.order, a.index, a.stage) < (b.order, b.index, b.stage)
    }
}

enum ProgressAssociation {
    case none(ProtocolPosition)
    case stepIndex(Int, ProtocolPosition)
    case parameterIndex(Int, ProtocolPosition)
    case invalid
    case unrecognized

    var position: ProtocolPosition? {
        switch self {
        case .none(let p), .stepIndex(_, let p), .parameterIndex(_, let p): return p
        default: return nil
        }
    }
    var answer: String? {
        switch self {
        case .none: return "none"
        case .stepIndex: return "step_index"
        case .parameterIndex: return "parameter_index"
        case .invalid: return "invalid"
        case .unrecognized: return nil
        }
    }
    var value: PWDispositionValue? {
        switch self {
        case .stepIndex(let i, _), .parameterIndex(let i, _): return .integer(i)
        default: return nil
        }
    }
}

func associateProgress(_ progress: PWWorkerProgress?, planCount: Int) -> ProgressAssociation? {
    guard let progress else { return nil }
    guard let order = PWDisposition.protocolOrder.firstIndex(of: progress.operation),
          (1...2).contains(progress.stage) else { return .unrecognized }
    if let index = progress.index, index >= 0xfffff { return .invalid }
    let item = progress.index.map { $0 + 1 } ?? 0
    guard progress.raw == ((progress.operation << 24) | (progress.stage << 20) | item) else { return .invalid }
    let stage = Int(progress.stage)
    switch progress.operation {
    case 9:
        guard let index = progress.index, Int(index) < planCount else { return .invalid }
        return .stepIndex(Int(index), ProtocolPosition(order: order, index: Int(index), stage: stage))
    case 11 where progress.index != nil:
        guard let index = progress.index, Int(index) <= planCount,
              let attemptOrder = PWDisposition.protocolOrder.firstIndex(of: 9) else { return .invalid }
        // Waiting is before the first action of this phase, even after a prior
        // phase's completed actions. Neither wait marker establishes entry.
        return .none(ProtocolPosition(order: attemptOrder, index: Int(index), stage: 0))
    case 4:
        guard let index = progress.index else { return .invalid }
        return .parameterIndex(Int(index), ProtocolPosition(order: order, index: Int(index), stage: stage))
    default:
        guard progress.index == nil else { return .invalid }
        return .none(ProtocolPosition(order: order, index: 0, stage: stage))
    }
}

/// The compact per-step summary: a registered projection of the two step claims.
func lifecycleSummary(_ step: PWDispositionStep) -> String {
    let boundary = step.questions["step_boundary_reached"]
    let result = step.questions["step_result_published"]
    if step.attempt_support == "unsupported" { return "unsupported" }
    if result?.state == "supported" && result?.answer == "published" { return "completed" }
    if boundary?.state == "conflicting" || result?.state == "conflicting" { return "conflicting" }
    if result?.state == "supported" && boundary?.state == "supported" {
        return boundary?.answer == "reached" ? "started_without_result" : "not_reached"
    }
    return "unresolved"
}

private func dispositionBasisSufficient(_ name: String, _ claim: PWDispositionClaim) -> Bool {
    let tokens = Set(claim.basis ?? [])
    func has(_ required: [String]) -> Bool { Set(required).isSubset(of: tokens) }
    switch (name, claim.answer) {
    case ("final_status", "signal"?): return has(["reaped", "term_signal"])
    case ("final_status", "exit_code"?): return has(["reaped", "exit_code"])
    case ("stop_reason", _): return has(["poll_stop_reason"])
    case ("cleanup_trigger", _), ("grace_end", _): return has([name, "exit_requested"])
    case ("collection_basis", _): return has(["collection_basis"])
    case ("kill_request_and_result", "requested"?): return has(["termination_request"])
    case ("kill_request_and_result", "none"?): return has(["termination_request", "exit_requested"])
    case ("progress_association", "step_index"?), ("progress_association", "invalid"?): return has(["progress", "plan"])
    case ("progress_association", "none"?), ("progress_association", "parameter_index"?): return has(["progress"])
    case ("step_requested_operation_applicability", _): return has(["attempt_support"])
    case ("step_boundary_reached", "reached"?): return has(["progress"]) || has(["slot", "attempt_support"])
    case ("step_boundary_reached", "not_reached"?): return has(["progress", "slot", "collection_basis"])
    case ("step_result_published", "published"?): return has(["slot", "attempt_support"])
    case ("step_result_published", "unpublished"?): return has(["slot", "collection_basis"])
    default: return true // Future answers retain their wire values.
    }
}

/// Integrity of an assembled record against the raw facts it cites. The
/// encoder rejects a record that fails this; the degraded reply retains it
/// unchecked so the conflict being reported is never lost. A record that
/// reports an observed conflict through `issues` passes.
func dispositionIntegrityProblems(_ record: PWDispositionRecord, subprocess sub: PWRunnerSubprocess,
                                  stepCount: Int, steps replySteps: [PWRunnerStepResult]? = nil) -> [String] {
    var problems: [String] = []
    func resolves(_ token: String, step: PWDispositionStep? = nil) -> Bool {
        switch token {
        case "plan": return true // Count and order checked against the reply below.
        case "slot", "attempt_support": return step != nil
        case "reaped": return sub.reaped != nil
        case "exit_code": return sub.exit_code != nil
        case "term_signal": return sub.term_signal != nil
        case "poll_stop_reason": return sub.poll_stop_reason != nil
        case "exit_requested": return sub.exit_requested != nil
        case "termination_request": return sub.termination_request != nil || sub.exit_requested != nil
        case "wait_errors": return sub.wait_errors != nil
        case "done_observed": return sub.done_observed != nil
        case "cleanup_trigger": return sub.cleanup_trigger != nil
        case "grace_end": return sub.grace_end != nil
        case "collection_basis": return sub.collection_basis != nil
        case "progress": return sub.worker_evidence?.progress != nil
        case "worker_failure": return sub.worker_evidence?.failure != nil
        default: return false
        }
    }
    for name in PWDisposition.runQuestions where record.questions[name] == nil {
        problems.append("disposition lacks question \(name)")
    }
    for (name, claim) in record.questions {
        guard PWDisposition.claimStates.contains(claim.state) else {
            problems.append("\(name): unknown claim state \(claim.state)"); continue
        }
        if claim.state == "supported" {
            guard let basis = claim.basis, !basis.isEmpty, claim.answer != nil else {
                problems.append("\(name): supported claim without answer or basis"); continue
            }
            for token in basis where !resolves(token) {
                problems.append("\(name): unresolved reference \(token)")
            }
            if !dispositionBasisSufficient(name, claim) { problems.append("\(name): insufficient witness references") }
        }
        if claim.state == "conflicting" {
            guard let issue = claim.issue, record.issues.indices.contains(issue),
                  record.issues[issue].question == name, record.issues[issue].step_index == nil else {
                problems.append("\(name): conflicting claim without a matching issue"); continue
            }
        }
        if claim.state == "unresolved" || claim.state == "inapplicable", claim.reason == nil {
            problems.append("\(name): \(claim.state) claim without a reason")
        }
    }
    if let final = record.questions["final_status"] {
        switch (final.state, final.answer) {
        case ("supported", "signal"?):
            if sub.reaped != true || sub.term_signal == nil || sub.exit_code != nil || final.value != sub.term_signal.map({ .integer($0) }) {
                problems.append("final_status: signal claim contradicts reaped/term_signal")
            }
        case ("supported", "exit_code"?):
            if sub.reaped != true || sub.exit_code == nil || sub.term_signal != nil || final.value != sub.exit_code.map({ .integer($0) }) {
                problems.append("final_status: exit_code claim contradicts reaped/exit_code")
            }
        case ("supported", _): break
        case ("conflicting", _):
            if sub.reaped != true || sub.exit_code == nil || sub.term_signal == nil {
                problems.append("final_status: conflict claimed without both status representations")
            }
        default: break
        }
    }
    if let stop = record.questions["stop_reason"], stop.state == "supported", stop.answer != sub.poll_stop_reason {
        problems.append("stop_reason: claim contradicts poll_stop_reason")
    }
    for (name, raw) in [("cleanup_trigger", sub.cleanup_trigger), ("grace_end", sub.grace_end),
                        ("collection_basis", sub.collection_basis)] {
        if let claim = record.questions[name], claim.state == "supported", claim.answer != raw {
            problems.append("\(name): claim contradicts the recorded host fact")
        }
    }
    if let kill = record.questions["kill_request_and_result"], kill.state == "supported" {
        if kill.answer == "requested", sub.termination_request == nil || kill.value != sub.termination_request.map({ .request($0) }) {
            problems.append("kill_request_and_result: value differs from termination_request")
        }
        if kill.answer == "none", sub.termination_request != nil {
            problems.append("kill_request_and_result: no-request claim beside a termination_request")
        }
    }
    if sub.collection_basis == "after_confirmed_reap" && sub.reaped != true {
        problems.append("collection_basis: terminal collection without a confirmed reap")
    }
    for name in ["cleanup_trigger", "grace_end", "kill_request_and_result"] {
        if record.questions[name]?.state == "supported" && sub.exit_requested == false {
            problems.append("\(name): supported cleanup claim when exit was not requested")
        }
    }
    let association = associateProgress(sub.worker_evidence?.progress, planCount: stepCount)
    let position = association?.position
    if let claim = record.questions["progress_association"], claim.state == "supported",
       ["none", "step_index", "parameter_index", "invalid"].contains(claim.answer ?? ""),
       claim.answer != association?.answer || claim.value != association?.value {
        problems.append("progress_association: claim disagrees with progress identity")
    }
    if record.steps.count != stepCount {
        problems.append("disposition steps (\(record.steps.count)) disagree with reply steps (\(stepCount))")
    }
    for (position, step) in record.steps.enumerated() {
        if step.index != position { problems.append("disposition step \(position) carries index \(step.index)") }
        if !PWDisposition.slotStates.contains(step.slot) { problems.append("step \(position): unknown slot state") }
        if !PWDisposition.attemptSupport.contains(step.attempt_support) {
            problems.append("step \(position): unknown attempt support")
        }
        for name in PWDisposition.stepQuestions where step.questions[name] == nil {
            problems.append("step \(position) lacks question \(name)")
        }
        for (name, claim) in step.questions {
            if !PWDisposition.claimStates.contains(claim.state) {
                problems.append("step \(position) \(name): unknown claim state")
            }
            if ["unresolved", "inapplicable"].contains(claim.state), claim.reason == nil {
                problems.append("step \(position) \(name): missing reason")
            }
            if claim.state == "supported" {
                guard let basis = claim.basis, !basis.isEmpty, claim.answer != nil else {
                    problems.append("step \(position) \(name): supported claim without answer or basis"); continue
                }
                for token in basis where !resolves(token, step: step) {
                    problems.append("step \(position) \(name): unresolved reference \(token)")
                }
                if !dispositionBasisSufficient(name, claim) { problems.append("step \(position) \(name): insufficient witness references") }
            }
            if claim.state == "conflicting" {
                guard let issue = claim.issue, record.issues.indices.contains(issue),
                      record.issues[issue].question == name, record.issues[issue].step_index == position else {
                    problems.append("step \(position) \(name): conflicting claim without a matching issue"); continue
                }
            }
        }
        if let applicability = step.questions["step_requested_operation_applicability"], applicability.state == "supported",
           ["supported", "unsupported"].contains(applicability.answer ?? ""), applicability.answer != step.attempt_support {
            problems.append("step \(position): applicability disagrees with attempt support")
        }
        if let result = step.questions["step_result_published"], result.state == "supported" {
            if result.answer == "published", step.slot != "completed" || step.attempt_support != "supported" {
                problems.append("step \(position): published claim on a slot that is not completed")
            }
            if result.answer == "unpublished", step.slot != "incomplete" || sub.collection_basis != "after_confirmed_reap" || step.attempt_support != "supported" {
                problems.append("step \(position): unpublished claim needs an incomplete slot under terminal collection")
            }
        }
        if let boundary = step.questions["step_boundary_reached"], boundary.state == "supported",
           boundary.answer == "not_reached", sub.collection_basis != "after_confirmed_reap" || step.slot == "completed" {
            problems.append("step \(position): not_reached claim needs terminal collection and no completed slot")
        }
    }
    // Validate the temporal proof and conflict scope independently of rendering.
    let terminal = sub.collection_basis == "after_confirmed_reap" && sub.reaped == true
    let attemptOrder = PWDisposition.protocolOrder.firstIndex(of: 9)!
    var referencedIssues = Set<Int>()
    for (i, step) in record.steps.enumerated() {
        let reached = position.map { $0 >= ProtocolPosition(order: attemptOrder, index: i, stage: 1) } ?? false
        let returned = position.map { $0 >= ProtocolPosition(order: attemptOrder, index: i, stage: 2) } ?? false
        let boundaryConflict = terminal && position != nil && !reached && step.slot == "completed"
        let resultConflict = terminal && returned && step.slot == "incomplete" && step.attempt_support == "supported"
        if let claim = step.questions["step_boundary_reached"], claim.state == "supported" {
            let basis = Set(claim.basis ?? [])
            let progressWitness = reached && basis.contains("progress")
            let slotWitness = step.slot == "completed" && step.attempt_support == "supported"
                && Set(["slot", "attempt_support"]).isSubset(of: basis)
            if claim.answer == "reached", boundaryConflict || !(progressWitness || slotWitness) {
                problems.append("step \(i): reached claim lacks an unopposed boundary witness")
            }
            if claim.answer == "not_reached", !terminal || position == nil || reached || step.slot == "completed" {
                problems.append("step \(i): not_reached claim lacks a terminal earlier position")
            }
        }
        if let claim = step.questions["step_result_published"], claim.state == "supported", claim.answer == "unpublished", resultConflict {
            problems.append("step \(i): unpublished answer suppresses a publication conflict")
        }
        for (name, isConflict) in [("step_boundary_reached", boundaryConflict), ("step_result_published", resultConflict)] {
            if let claim = step.questions[name], claim.state == "conflicting" {
                if !isConflict { problems.append("step \(i) \(name): conflict without incompatible observations") }
            }
        }
        if let reply = replySteps?.first(where: { $0.step_id == step.step_id }) {
            let completed = step.slot == "completed" && step.attempt_support == "supported"
            let reason: String? = completed ? nil : step.attempt_support == "unsupported" ? "attempt_not_supported"
                : step.slot == "absent" ? "slot_absent" : "slot_incomplete"
            if reply.step_id != step.step_id || reply.attempt.result_source != (completed ? "worker" : "synthetic") || reply.attempt.missing_reason != reason {
                problems.append("step \(i): identity or compatibility projections disagree with record")
            }
            if reply.attempt.lifecycle?.boundary != step.questions["step_boundary_reached"] || reply.attempt.lifecycle?.result != step.questions["step_result_published"] {
                problems.append("step \(i): lifecycle copies disagree with record")
            }
            if let summary = reply.attempt.lifecycle?.summary, PWDisposition.summaries.contains(summary), summary != lifecycleSummary(step) {
                problems.append("step \(i): lifecycle summary disagrees with record")
            }
            let limits = reply.comparison?.limitations.filter { PWDisposition.limitationForSummary.values.contains($0) } ?? []
            let expected = PWDisposition.limitationForSummary[lifecycleSummary(step)].map { [$0] } ?? []
            if limits != expected { problems.append("step \(i): lifecycle limitations disagree with record") }
        }
    }
    for (name, claim, index) in record.questions.map({ ($0.key, $0.value, Int?.none) })
        + record.steps.flatMap({ step in step.questions.map { ($0.key, $0.value, Optional(step.index)) } }) {
        guard claim.state == "conflicting", let pointer = claim.issue, record.issues.indices.contains(pointer) else { continue }
        referencedIssues.insert(pointer)
        let issue = record.issues[pointer]
        let observations = name == "final_status" ? ["exit_code", "term_signal"] : ["progress", "slot", "collection_basis"]
        if issue.kind != "conflict" || issue.rule != (name == "final_status" ? "D1" : "D5")
            || !(["final_status", "step_boundary_reached", "step_result_published"].contains(name))
            || !Set(observations).isSubset(of: Set(issue.observations))
            || issue.observations.contains(where: { !resolves($0, step: index.flatMap { record.steps.indices.contains($0) ? record.steps[$0] : nil }) }) {
            problems.append("\(name): malformed conflict issue")
        }
    }
    if referencedIssues.count != record.issues.count { problems.append("unreferenced disposition issue") }
    if sub.partial_steps != record.steps.contains(where: { $0.slot != "completed" }) {
        problems.append("partial_steps disagrees with record slots")
    }
    return problems
}

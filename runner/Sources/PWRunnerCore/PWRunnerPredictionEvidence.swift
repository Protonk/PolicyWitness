import Foundation
import Darwin

struct PWRunnerSandboxCheckResult {
    // BEGIN GENERATED PORCELAIN PWRunnerSandboxCheckResult
    /// Result provenance. See the "Worker evidence contract" in
    /// tests/FAILURE-PROPAGATION-CONTRACT.md for native returns versus PW
    /// status and missing reasons.
    var result_source: String? = nil
    var native_rc: Int? = nil
    var missing_reason: String? = nil
    var rc: Int
    var outcome: String
    var pid: Int?
    var operation: String
    var filter_kind: String
    var filter_value: String?
    var filter_type_id: Int?
    var errno: Int?
    var error: String?
    var path_diagnostics: PWRunnerPathDiagnostics?
    // END GENERATED PORCELAIN PWRunnerSandboxCheckResult

    init(
        rc: Int,
        outcome: String,
        pid: Int?,
        operation: String,
        filter_kind: String,
        filter_value: String? = nil,
        filter_type_id: Int? = nil,
        errno: Int? = nil,
        error: String? = nil,
        path_diagnostics: PWRunnerPathDiagnostics? = nil
    ) {
        self.rc = rc
        self.outcome = outcome
        self.pid = pid
        self.operation = operation
        self.filter_kind = filter_kind
        self.filter_value = filter_value
        self.filter_type_id = filter_type_id
        self.errno = errno
        self.error = error
        self.path_diagnostics = path_diagnostics
    }



}

struct ValidatorVerdict {
    // BEGIN GENERATED PORCELAIN ValidatorVerdict
    var stepId: String?
    var operation: String?
    var filterType: String?
    var filterTypeId: Int?
    var filterValue: String?
    var rc: Int?
    var errnoVal: Int?
    var outcome: String
    var error: String?
    var rawLine: String
    // END GENERATED PORCELAIN ValidatorVerdict
}

/// Receiver-owned rejected frame context. The prefix is bytes, not repaired
/// JSON. Offsets/lengths are exact received byte counts; at most 256 context
/// bytes are retained. Unknown diagnostic outcome names are not decode faults.
struct PWValidatorDecodeFault {
    // BEGIN GENERATED PORCELAIN PWValidatorDecodeFault
    var origin: String = "runner_host"
    var kind: String
    var message: String
    var byte_offset: Int
    var frame_bytes: Int
    var retained_bytes: Int
    var context_b64: String
    var context_truncated: Bool
    // END GENERATED PORCELAIN PWValidatorDecodeFault
}

struct PWValidatorAssociationIssue {
    // BEGIN GENERATED PORCELAIN PWValidatorAssociationIssue
    var origin: String = "runner_host"
    var kind: String
    var step_id: String? = nil
    var count: Int
    // END GENERATED PORCELAIN PWValidatorAssociationIssue
}

/// Validator child observations. Missing host fields remain unknown.
/// Only successful reaping supplies exit/signal. Records are accepted validator
/// evidence, independently retained even when association/transport/cleanup fails.
/// A null-ID record is never assigned an invented step identity.
struct PWRunnerValidatorSubprocess {
    // BEGIN GENERATED PORCELAIN PWRunnerValidatorSubprocess
    /// The phase this collection served, stamped by the host from the
    /// collection it ran. Readers require agreement with the containing phase.
    var phase_id: String?
    var ordinal: Int?
    var pid: Int
    var term_signal: Int?
    var exit_code: Int?
    var reaped: Bool?
    var termination_request: PWRunnerTerminationRequest?
    var wait_errors: [PWRunnerWaitError]?
    var read_error: String?
    var stdout_collection_stop: String?
    var stdout_bytes_received: Int?
    var probe_bytes_written: Int?
    var probe_bytes_expected: Int?
    var io_error: String?
    var decode_fault: PWValidatorDecodeFault?
    var records: [ValidatorVerdict]?
    var expected_step_ids: [String]?
    var association_issues: [PWValidatorAssociationIssue]?
    /// The measured exit-grace wait after collection closed.
    var exit_grace_wait: PWHostWait? = nil
    // END GENERATED PORCELAIN PWRunnerValidatorSubprocess

    init(pid: Int, term_signal: Int? = nil, exit_code: Int? = nil) {
        self.pid = pid
        self.term_signal = term_signal
        self.exit_code = exit_code
    }
}

/// The validator's filter type name for a wire filter kind. Shared by the
/// host's query planner and by readers that rebuild a phase's query plan.
func mapFilterKindToValidator(_ wireKind: String) -> String {
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

/// The submitted query a validator record must describe.
struct ValidatorQueryIdentity {
    var stepId: String
    var operation: String
    var filterType: String
    var filterValue: String?
}

/// The host's step/record join, shared with every reader that recomputes it.
/// Duplicate IDs are ambiguous, so none of their records enters the step join.
/// All accepted records remain at run scope, including unknown and null IDs.
func validatorAssociationIssues(_ verdicts: [ValidatorVerdict], expected: [ValidatorQueryIdentity]) -> (byStep: [String: ValidatorVerdict], issues: [PWValidatorAssociationIssue]) {
    let wanted = Set(expected.map { $0.stepId })
    let groups = Dictionary(grouping: verdicts.compactMap { v in v.stepId.map { ($0, v) } }, by: { $0.0 })
    var byStep: [String: ValidatorVerdict] = [:]
    var issues: [PWValidatorAssociationIssue] = []
    for probe in expected {
        let id = probe.stepId
        let matches = groups[id] ?? []
        if matches.count == 1 {
            let v = matches[0].1
            // Diagnostics may omit query metadata. Any supplied metadata must
            // agree; predictions must describe exactly the submitted query.
            let prediction = v.outcome == "allow" || v.outcome == "deny"
            let mismatch = (prediction || v.operation != nil) && v.operation != probe.operation
                || (prediction || v.filterType != nil) && v.filterType != probe.filterType
                || (prediction || v.filterValue != nil) && v.filterValue != probe.filterValue
            if mismatch { issues.append(PWValidatorAssociationIssue(kind: "query_mismatch", step_id: id, count: 1)) }
            else { byStep[id] = v }
        }
        else { issues.append(PWValidatorAssociationIssue(kind: matches.isEmpty ? "missing_id" : "duplicate_id", step_id: id, count: matches.count)) }
    }
    for id in groups.keys.sorted() where !wanted.contains(id) {
        issues.append(PWValidatorAssociationIssue(kind: "unexpected_id", step_id: id, count: groups[id]!.count))
    }
    let unassociated = verdicts.filter { $0.stepId == nil }.count
    if unassociated > 0 { issues.append(PWValidatorAssociationIssue(kind: "unassociated", count: unassociated)) }
    return (byStep, issues)
}

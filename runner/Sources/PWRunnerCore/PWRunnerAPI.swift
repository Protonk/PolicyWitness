import Foundation
import Darwin

// PWRunner is a single-purpose, ephemeral XPC runner. The XPC service host
// stays unsandboxed; a short-lived worker self-applies a seatbelt profile,
// executes the probe plan, returns a report to the host, and exits.
//
// This file intentionally defines a small JSON-over-Data protocol surface so the
// runner can be driven by multiple controllers (CLI, lab tools) without NSXPC
// object graphs.

@objc protocol PWRunnerProtocol {
    func reserveRunner(_ request: Data, withReply reply: @escaping (Data) -> Void)
    func runReservedSpecimen(_ request: Data, reservation: String,
        withReply reply: @escaping (Bool, Data) -> Void)
}

// Wire string constants used across runner/client code. Keep these stable.
enum PWRunnerWire {
    static let defaultClientTimeoutMs = 240_000
    static let policyFormatSbpl = "sbpl"

    static let attemptKindFile = "file"
    static let attemptKindMachLookup = "mach_lookup"
    static let attemptKindSysctl = "sysctl"
    static let attemptKindExec = "exec"

    static let attemptActionOpenRead = "open_read"
    static let attemptActionReadFresh = "read_fresh"
    static let attemptActionWriteFresh = "write_fresh"
    static let attemptActionCreateFresh = "create_fresh"
    static let attemptActionOpenWrite = "open_write"
    static let attemptActionCreate = "create"
    static let attemptActionUnlink = "unlink"
    static let attemptActionAccess = "access"
    static let attemptActionMachLookup = "bootstrap_look_up"
    static let attemptActionRead = "read"
    static let attemptActionSpawn = "spawn"

    static let sandboxFilterNone = "none"
    static let sandboxFilterPath = "path"
    static let sandboxFilterGlobalName = "global_name"
    static let sandboxFilterLocalName = "local_name"
    static let sandboxFilterIokitRegistryEntryClass = "iokit_registry_entry_class"
    static let sandboxFilterIokitUserClientClass = "iokit_user_client_class"
    static let sandboxFilterSysctlName = "sysctl_name"
}

// Canonical normalized_outcome values. Every emit site in the runner stack
// references these constants instead of writing a literal string, so a typo
// becomes a compile error rather than a silent new outcome that no test
// asserts on and no doc covers. The wire type stays `String` (Codable
// unchanged); these are just the typo-proof spellings.
//
// Adding an outcome: declare it here, then teach the matching test suite
// (tests/suites/runner_outcome_*/ or witness_contract/) to assert
// against it. docs/PolicyWitness.md should also list it in the "Run output"
// section so callers can recognize it.
enum NormalizedOutcome {
    // Successful execution. The worker's status word cannot identify a failed
    // native operation; published preparation/application failures map to
    // runner_failed, and no precise apply-failure spelling exists.
    static let ok = "ok"

    // ----- emitted by the host short-circuit (PWRunnerService.swift).
    // `bad_policy` is the host's pre-spawn structural check (computePolicyHash:
    // missing sbpl_source / non-sbpl format), NOT a compile-error signal — SBPL
    // that fails to compile reaches the worker and surfaces as
    // runner_failed with the published status word or failure record.
    static let badPolicy = "bad_policy"
    static let badRequest = "bad_request"
    static let workerSpawnFailed = "worker_spawn_failed"

    // ----- emitted by the host classifier (CWorker.swift sentinel
    // observation + CWorkerOrchestrator classification). Signals and
    // PID-matched denials do not establish a sandbox cause, so no
    // sandbox-denied spelling exists; such terminations are runner_failed.
    static let runnerTimeout = "runner_timeout"
    static let runnerFailed = "runner_failed"
    // Host reply construction failed; the original execution summary is retained
    // in reporting_failure, independently of child or policy observations.
    static let runnerReportingFailed = "runner_reporting_failed"

    // ----- emitted by the host classifier on the validator child
    // failure modes. Default top-level semantics: any validator_*
    // outcome makes `result.ok=false`, `rc=1`. The attempt channel
    // is still populated and machine-readable, but a missing
    // prediction channel is a runner evidence failure even when the
    // observation channel completed. Consumers can opt to consume
    // the partial envelope as degraded evidence; the runner does not
    // silently upgrade an attempts-only run to `ok`.
    static let validatorSpawnFailed = "validator_spawn_failed"
    static let validatorNoReply = "validator_no_reply"
    static let validatorDecodeFailure = "validator_decode_failure"
    static let validatorUnavailable = "validator_unavailable"
}

/// Canonical step.attempt.outcome values. Parallels NormalizedOutcome
/// and SandboxCheckOutcome: new constants are added here (with the
/// matching wire string) before any emit site uses them, and
/// source_drift enforces that every constant has a row in
/// tests/COVERAGE.md's attempt-outcome matrix.
///
/// `no_completed_result` names the absence of a completed attempt result. It
/// says nothing about whether the operation started: `attempt.lifecycle` and
/// the worker's progress word carry that evidence. Treat it as missing
/// evidence, never as an access verdict.
enum AttemptOutcome {
    static let ok = "ok"
    static let openFailed = "open_failed"
    static let readFailed = "read_failed"
    static let writeFailed = "write_failed"
    static let unlinkFailed = "unlink_failed"
    static let accessFailed = "access_failed"
    static let lookupFailed = "lookup_failed"
    static let sysctlFailed = "sysctl_failed"
    static let execFailed = "exec_failed"
    static let unsupported = "unsupported"
    static let noCompletedResult = "no_completed_result"
}

// Canonical step.sandbox_check.outcome values. New constants should be
// added here (with the matching wire string) before any emit site uses
// them, by the same convention as NormalizedOutcome.
//
// `prediction_unavailable` is emitted when the planner excludes a step's
// query: for the (operation, filter) pairs in the shared exclusion set no
// filter ID produced a sandbox_check verdict matching kernel enforcement
// (verified via tests/suites/witness_contract/harness/verify_filter_id.sh),
// and for a path the host could not resolve at planning time. The attempt
// channel still runs; the query channel records why it was not asked.
//
// When emitted, the result's `rc` field is the sentinel -1 (NOT 0) so
// any consumer that keys on `rc == 0` for "allow" cannot misread the
// absent prediction as an allow verdict. See docs/PolicyWitness.md
// "Filter kinds where prediction is unavailable" for the full
// contract.
enum SandboxCheckOutcome {
    static let allow = "allow"
    static let deny = "deny"
    static let error = "error"
    static let predictionUnavailable = "prediction_unavailable"
    /// libsandbox doesn't recognize the operation name (sandbox_check
    /// returned rc=-1 + errno=EINVAL). Most commonly a caller passing
    /// the unstar'd form of an SBPL family operation
    /// (e.g. "process-exec" instead of the canonical "process-exec*").
    /// Surfaced as a distinct outcome so consumers can treat it as a
    /// per-step unavailable observation. `error` is always
    /// populated with the rejected operation name + the wildcard-form
    /// hint. The query channel's answer is unavailable for these steps.
    static let unsupportedOperation = "unsupported_operation"
}

// BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
/// Wire contract versions. Edit docs/contract.json and regenerate; never edit here.
enum PWContract {
    static let requestSchema: Int = 5
    static let responseSchema: Int = 24
    static let runnerProtocol: Int = 2
}
// END GENERATED CONTRACT VERSIONS

import Foundation

// PWRunner is a single-purpose, ephemeral XPC runner. The XPC service host
// stays unsandboxed; a short-lived worker self-applies a seatbelt profile,
// executes the probe plan, returns a report to the host, and exits.
//
// This file intentionally defines a small JSON-over-Data protocol surface so the
// runner can be driven by multiple controllers (CLI, lab tools) without NSXPC
// object graphs.

@objc protocol PWRunnerProtocol {
    func runSpecimen(_ request: Data, withReply reply: @escaping (Data) -> Void)
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
    static let alreadyRan = "already_ran"
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

    // ----- synthesized by pw-runner-client when the XPC peer is unreachable
    static let xpcError = "xpc_error"
    static let xpcTimeout = "xpc_timeout"
    static let xpcProxyTypeMismatch = "xpc_proxy_type_mismatch"
    static let xpcNoReply = "xpc_no_reply"
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
    static let responseSchema: Int = 22
}
// END GENERATED CONTRACT VERSIONS

// Request objects are closed; dictionary keys inside policy.params are data.
// CodingKeys owns both encoding and acceptance, so there is no second schema.
private struct RequestKey: CodingKey {
    let stringValue: String
    let intValue: Int? = nil
    init(stringValue: String) { self.stringValue = stringValue }
    init?(intValue: Int) { return nil }
}

enum RequestContractError: Error {
    case unsupportedSchema(Int)
    case unknownField([CodingKey])
    case unresolvedAugments
}

/// A request refusal before execution. Path components are object keys or
/// decimal array positions. A null path withholds an overlong location; it
/// never substitutes a shortened key that could name a different field.
struct PWRunnerRequestFailure: Codable, Error, CustomStringConvertible {
    var code: String
    var path: [String]?
    var expected_schema: Int?

    init(code: String, path: [String]?, expected_schema: Int? = nil) {
        self.code = code
        self.path = path.flatMap { parts in
            parts.count <= 8 && parts.allSatisfy({ $0.utf8.count <= 63 }) ? parts : nil
        }
        self.expected_schema = expected_schema
    }

    enum CodingKeys: String, CodingKey { case code, path, expected_schema }
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(code, forKey: .code)
        try c.encode(path, forKey: .path)
        try c.encodeIfPresent(expected_schema, forKey: .expected_schema)
    }

    var description: String {
        let location = path.map { $0.isEmpty ? "<root>" : $0.joined(separator: ".") } ?? "<unreported_path>"
        let explanations = [
            "duplicate_step_id": "duplicate step_id in probe_plan",
            "missing_filter_value": "filter.value required for this kind",
            "empty_operation": "sandbox_check.operation is empty",
            "unsupported_attempt": "unsupported attempt kind/action",
            "unknown_filter_kind": "unknown filter kind",
            "inapplicable_field": "field has no effect in this request",
            "unsupported_policy_format": "policy.format must be sbpl",
            "missing_policy_source": "policy.sbpl_source is required",
            "invalid_capture_nonce": "capture_compiled_profile requires a fresh 32-character lowercase hex capture_nonce",
            "relative_exec_target": "exec target must be absolute",
        ]
        let detail = expected_schema.map { " (expected \($0))" }
            ?? explanations[code].map { ": \($0)" } ?? ""
        return "request refused: \(code) at \(location)\(detail)"
    }
}

func rejectUnknownRequestKeys<K: CodingKey & CaseIterable>(_ type: K.Type, from decoder: Decoder) throws {
    let container = try decoder.container(keyedBy: RequestKey.self)
    let accepted = Set(K.allCases.map { $0.stringValue })
    if let key = container.allKeys.sorted(by: { $0.stringValue < $1.stringValue })
        .first(where: { !accepted.contains($0.stringValue) }) {
        throw RequestContractError.unknownField(decoder.codingPath + [key])
    }
}

struct PWRunnerRunSpec: Codable {
    // The request contract and its admission rules: docs/CONTRACT.md.
    var schema_version: Int
    var specimen_id: String
    var run_kind: String?
    var policy: PWRunnerPolicySpec
    private var ordinaryPlan: [PWRunnerProbeStep]?
    var phases: [PWRunnerPhase]?
    var extensions: [PWRunnerExtensionDeclaration]?
    var probe_plan: [PWRunnerProbeStep] {
        get { phases?.flatMap { $0.actions.compactMap { $0.probe } } ?? ordinaryPlan ?? [] }
        set { ordinaryPlan = newValue; phases = nil }
    }
    var executionPhases: [PWRunnerPhase] {
        phases ?? [PWRunnerPhase(phase_id: "main", actions: (ordinaryPlan ?? []).map(PWRunnerPhaseAction.probe))]
    }
    func probePath(_ index: Int) -> [String] {
        guard let phases else { return ["probe_plan", String(index)] }
        var offset = 0
        for (phaseIndex, phase) in phases.enumerated() {
            for (actionIndex, action) in phase.actions.enumerated() where action.probe != nil {
                if offset == index { return ["phases", String(phaseIndex), "actions", String(actionIndex)] }
                offset += 1
            }
        }
        return ["phases"]
    }
    var _test_overrides: PWRunnerTestOverrides?

    init(
        schema_version: Int = PWContract.requestSchema,
        specimen_id: String,
        run_kind: String? = nil,
        policy: PWRunnerPolicySpec,
        probe_plan: [PWRunnerProbeStep] = [],
        phases: [PWRunnerPhase]? = nil,
        extensions: [PWRunnerExtensionDeclaration]? = nil,
        _test_overrides: PWRunnerTestOverrides? = nil
    ) {
        self.schema_version = schema_version
        self.specimen_id = specimen_id
        self.run_kind = run_kind
        self.policy = policy
        self.ordinaryPlan = phases == nil ? probe_plan : nil
        self.phases = phases
        self.extensions = extensions
        self._test_overrides = _test_overrides
    }

    enum CodingKeys: String, CodingKey, CaseIterable {
        case schema_version, specimen_id, run_kind, policy, probe_plan, phases, extensions, _test_overrides
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        do { schema_version = try c.decode(Int.self, forKey: .schema_version) }
        catch {
            // Foundation wraps its private integer-conversion error as a root
            // JSON error outside this initializer. Identify numeric values here
            // so a fractional/oversized marker keeps its actual field location.
            guard let number = try? c.decode(Double.self, forKey: .schema_version), number.isFinite else { throw error }
            if number == Double(PWContract.requestSchema) {
                schema_version = PWContract.requestSchema
            } else {
                throw PWRunnerRequestFailure(code: number.rounded(.towardZero) == number ? "unsupported_schema" : "type_mismatch",
                    path: ["schema_version"], expected_schema: PWContract.requestSchema)
            }
        }
        guard schema_version == PWContract.requestSchema else {
            throw RequestContractError.unsupportedSchema(schema_version)
        }
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        specimen_id = try c.decode(String.self, forKey: .specimen_id)
        run_kind = try c.decodeIfPresent(String.self, forKey: .run_kind)
        policy = try c.decode(PWRunnerPolicySpec.self, forKey: .policy)
        extensions = try c.decodeIfPresent([PWRunnerExtensionDeclaration].self, forKey: .extensions)
        phases = try c.decodeIfPresent([PWRunnerPhase].self, forKey: .phases)
        ordinaryPlan = try c.decodeIfPresent([PWRunnerProbeStep].self, forKey: .probe_plan)
        guard (phases == nil) != (ordinaryPlan == nil) else {
            throw PWRunnerRequestFailure(code: "exclusive_plan_forms", path: ["phases"])
        }
        _test_overrides = try c.decodeIfPresent(PWRunnerTestOverrides.self, forKey: ._test_overrides)
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(schema_version, forKey: .schema_version)
        try c.encode(specimen_id, forKey: .specimen_id)
        try c.encodeIfPresent(run_kind, forKey: .run_kind)
        try c.encode(policy, forKey: .policy)
        try c.encodeIfPresent(ordinaryPlan, forKey: .probe_plan)
        try c.encodeIfPresent(phases, forKey: .phases)
        try c.encodeIfPresent(extensions, forKey: .extensions)
        try c.encodeIfPresent(_test_overrides, forKey: ._test_overrides)
    }
}

/// Ordinary phase actions retain the required prediction/attempt pair.
/// Lifecycle actions have a separate representation and never relax that pair.
enum PWRunnerPhaseAction: Codable {
    case probe(PWRunnerProbeStep)
    case extensionAction(PWRunnerExtensionAction)
    var probe: PWRunnerProbeStep? { if case .probe(let value) = self { return value }; return nil }
    var stepID: String { switch self { case .probe(let value): return value.step_id; case .extensionAction(let value): return value.step_id } }
    init(from decoder: Decoder) throws {
        let keys = try decoder.container(keyedBy: RequestKey.self)
        if keys.contains(RequestKey(stringValue: "extension")) {
            self = .extensionAction(try PWRunnerExtensionAction(from: decoder))
        } else { self = .probe(try PWRunnerProbeStep(from: decoder)) }
    }
    func encode(to encoder: Encoder) throws {
        switch self { case .probe(let value): try value.encode(to: encoder)
        case .extensionAction(let value): try value.encode(to: encoder) }
    }
}

// Wire-side bounds also compile into the client, without the worker driver.
enum PWExtensionLimits {
    static let declarations = 1
    static let consumes = 1
    static let releases = 1
    static let referenceBytes = 63
    static let targetBytes = 1023
    static let tokenBytes = 16384
    static let freshReadBytes = 64
}

struct PWRunnerExtensionDeclaration: Codable {
    var token_ref: String
    var target: String
    init(token_ref: String, target: String) { self.token_ref = token_ref; self.target = target }
    enum CodingKeys: String, CodingKey, CaseIterable { case token_ref, target }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        token_ref = try c.decode(String.self, forKey: .token_ref)
        target = try c.decode(String.self, forKey: .target)
    }
}
struct PWRunnerExtensionOperation: Codable {
    var operation: String
    var token_ref: String?
    var handle_ref: String
    enum CodingKeys: String, CodingKey, CaseIterable { case operation, token_ref, handle_ref }
    init(operation: String, token_ref: String? = nil, handle_ref: String) {
        self.operation = operation; self.token_ref = token_ref; self.handle_ref = handle_ref
    }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        operation = try c.decode(String.self, forKey: .operation)
        token_ref = try c.decodeIfPresent(String.self, forKey: .token_ref)
        handle_ref = try c.decode(String.self, forKey: .handle_ref)
    }
}
struct PWRunnerExtensionAction: Codable {
    var step_id: String
    var intervention: PWRunnerExtensionOperation
    enum CodingKeys: String, CodingKey, CaseIterable { case step_id; case intervention = "extension" }
    init(step_id: String, intervention: PWRunnerExtensionOperation) { self.step_id = step_id; self.intervention = intervention }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        step_id = try c.decode(String.self, forKey: .step_id)
        intervention = try c.decode(PWRunnerExtensionOperation.self, forKey: .intervention)
    }
}

/// The native handle is signed 64-bit; -1 does not provide a handle.
/// Missing publication withholds every native result, regardless of progress.
struct PWRunnerExtensionEvent: Codable {
    var phase_id: String
    var step_id: String
    var operation: String
    var token_ref: String?
    var handle_ref: String
    var call_boundary_observed: Bool
    var result_published: Bool
    var status: String
    var native_result: Int64?
    var errno: Int32?
    var unavailable_reason: String?
    var lifecycle: PWAttemptLifecycle?
}
struct PWFileIdentity: Codable {
    var device: UInt64
    var inode: UInt64
    var mode: UInt32
    var uid: UInt32
    var gid: UInt32
}
struct PWRunnerFreshRead: Codable {
    var open_rc: Int32
    var open_errno: Int32?
    var read_rc: Int64?
    var read_errno: Int32?
    var stat_rc: Int32?
    var stat_errno: Int32?
    var identity: PWFileIdentity?
    var close_rc: Int32?
    var close_errno: Int32?
    var content_hex: String?
}
struct PWRunnerIssuer: Codable {
    var executable_path: String
    var pid: Int32?
    var uid: UInt32?
    var euid: UInt32?
    var gid: UInt32?
    var egid: UInt32?
    var call_boundary_observed = false
    var result_published = false
    var native_nonnull: Bool?
    var errno: Int32?
    var token_length: UInt32?
    var reaped: Bool?
    var exit_code: Int32?
    var term_signal: Int32?
    var wait_errors: [PWRunnerWaitError] = []
    var termination_request: PWRunnerTerminationRequest?
    var spawn_failure: PWRunnerSpawnFailure?
}
struct PWRunnerExtensionRecord: Codable {
    var token_ref: String
    var extension_class = "com.apple.app-sandbox.read"
    var submitted_target: String
    var resolved_target: String?
    var preparation_status = "not_started"
    var preparation_errno: Int32?
    var identity: PWFileIdentity?
    var issuance_status = "not_started"
    var issuer: PWRunnerIssuer?
    var delivery_status = "not_observed"
    var delivered_bytes: UInt32?
    /// Present exactly when the worker published `channel_rejected` or
    /// `local_setup_failed`.
    var delivery_failure: PWRunnerExtensionDeliveryFailure?
    /// Cleanup after unavailable native APIs is independent of channel setup.
    /// Absence means no cleanup failure was reported, not proof of cleanup.
    var delivery_cleanup_failure: PWRunnerExtensionDeliveryCleanupFailure?
    var host_buffer_erased = false
}

struct PWRunnerExtensionDeliveryCleanupFailure: Codable, Equatable {
    var stage: String
    var errno: Int32

    func problem(status: String) -> String? {
        guard status == "native_api_unavailable", stage == "descriptor_close", errno >= 0 else {
            return "invalid independent delivery cleanup failure"
        }
        return nil
    }
}

/// The worker's delivery publication vocabulary. Codes and stage numbers are
/// the PW_DELIVERY_* enums in pw_probe_runner.c; an unrecognized value becomes
/// the record status `invalid`.
enum PWExtensionDelivery {
    static let statuses: [UInt32: String] = [1: "delivered", 2: "token_unavailable", 3: "channel_rejected",
                                             4: "native_api_unavailable", 5: "local_setup_failed"]
    static let stages: [UInt32: String] = [1: "core_limit", 2: "descriptor_metadata", 3: "channel_size", 4: "mapping",
                                           5: "descriptor_close", 6: "channel_header", 7: "channel_token", 8: "unmap"]
    /// Stages whose failure is a native call result.
    static let localStages: Set<String> = ["core_limit", "descriptor_metadata", "mapping", "descriptor_close"]
    /// Stages that judged the channel itself; `channel_size` keeps the successful fstat return.
    static let channelStages: Set<String> = ["channel_size", "channel_header", "channel_token"]
    static let cleanupStages: Set<String> = ["descriptor_close", "unmap"]
    static let failureStatuses: Set<String> = ["channel_rejected", "local_setup_failed"]
    static let recordStatuses: Set<String> = ["not_observed", "delivered", "token_unavailable", "channel_rejected",
                                              "native_api_unavailable", "local_setup_failed"]
}

/// The worker's account of a failed channel preparation: the first failing
/// stage, that call's native return and the errno saved immediately after it
/// when the stage made a native call, and a cleanup failure observed while
/// undoing earlier setup. A format rejection carries no native result.
struct PWRunnerExtensionDeliveryFailure: Codable, Equatable {
    var stage: String
    var native_rc: Int32?
    var errno: Int32?
    var cleanup_stage: String?
    var cleanup_errno: Int32?

    /// Structural rules every reader applies: the stage class agrees with the
    /// status, native fields are present exactly for native stages, and
    /// cleanup fields are paired.
    func problem(status: String) -> String? {
        let local = PWExtensionDelivery.localStages.contains(stage)
        guard local || PWExtensionDelivery.channelStages.contains(stage) else { return "unknown delivery failure stage" }
        if (status == "local_setup_failed") != local { return "delivery failure stage disagrees with status" }
        if local {
            guard let rc = native_rc, rc != 0, let value = errno, value >= 0 else { return "local setup failure lacks its native result" }
        } else if stage == "channel_size" {
            guard native_rc == 0, errno == nil else { return "undersized channel misreports its inspection result" }
        } else if native_rc != nil || errno != nil { return "channel rejection invents a native result" }
        if let cleanup = cleanup_stage {
            guard PWExtensionDelivery.cleanupStages.contains(cleanup), let value = cleanup_errno, value >= 0 else { return "delivery cleanup failure lacks its errno" }
            if cleanup == "descriptor_close" && stage == "descriptor_close" { return "descriptor closed twice" }
        } else if cleanup_errno != nil { return "delivery cleanup errno without a stage" }
        return nil
    }
}

struct PWRunnerPhase: Codable {
    static let maximumCount = 8
    var phase_id: String
    var actions: [PWRunnerPhaseAction]
    init(phase_id: String, actions: [PWRunnerPhaseAction]) {
        self.phase_id = phase_id; self.actions = actions
    }
    enum CodingKeys: String, CodingKey, CaseIterable { case phase_id, actions }
    init(from decoder: Decoder) throws {
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        let c = try decoder.container(keyedBy: CodingKeys.self)
        phase_id = try c.decode(String.self, forKey: .phase_id)
        actions = try c.decode([PWRunnerPhaseAction].self, forKey: .actions)
    }
}

// Test-only knobs that re-route narrow boundaries through real production
// code so the test suite can reach failure outcomes without stubbing return
// values. The underscore prefix on the wire field
// (`PWRunnerRunSpec._test_overrides`) signals "not part of the public
// contract"; readers can branch on its presence to flag a non-production
// run. Any override consumed is mirrored back into
// `PWRunnerRunResult.test_overrides` so the resulting envelope is
// self-describing — a production run leaves `test_overrides` null.
//
// Design rule for new keys: re-route a *condition* (a path, a deadline,
// a hostile value), never fake a *result*. The classifier and the JSON
// envelope assembly must still run for real; only their input is steered.
//
// Currently supported keys and the boundaries they re-route:
//
// | key                         | consumed at                                                   | drives outcome              |
// | --------------------------- | ------------------------------------------------------------- | --------------------------- |
// | `worker_executable_path`    | `posix_spawn` path in CWorker.spawn (pw-probe-runner)         | `worker_spawn_failed`       |
// | `worker_timeout_ms`         | host-side deadline in CWorker.run (floored at 50ms)           | `runner_timeout`            |
// | `validator_executable_path` | `posix_spawn` path in ValidatorClient.runValidator. Parallel  | `validator_spawn_failed`    |
// |                             | to `worker_executable_path` for the validator child.          |                             |
// | `worker_post_apply_hang_ms` | passed to pw-probe-runner as `--post-apply-hang-ms <N>`;      | `runner_timeout`            |
// |                             | the C worker nanosleeps for N ms AFTER all slot results       |                             |
// |                             | are durable but BEFORE writing the `done` sentinel, pushing   |                             |
// |                             | host past its sentinel_timeout. Drives the runner_timeout     |                             |
// |                             | suite.                                                        |                             |
// | `worker_pre_ready_hang_ms` | sleep after compile/capture, before ready byte                 | ok with sufficient budget; |
// |                             | (not evidence of a native compilation failure)                | runner_timeout if expired  |
// | `worker_post_apply_kill_signal` | self-signal after applied/slots, before done               | runner_failed              |
// |                             | Signal establishes disposition, not a sandbox cause.          |                            |
// | `worker_kill_before_publish_slot` | SIGKILL on itself inside run_attempt() for that slot,   | runner_failed              |
// |                             | after the native attempt returned and before the slot's       |                            |
// |                             | `completed` store. The host holds a started progress word     |                            |
// |                             | and no published result for that slot.                        |                            |
//
// See runner/AGENTS.md → "Testing `normalized_outcome` failure paths via
// `_test_overrides`" for the full contract, the four-assertion test
// recipe, and the rules for adding a new key.
struct PWRunnerTestOverrides: Codable {
    var worker_executable_path: String?
    var worker_timeout_ms: Int?
    var issuer_executable_path: String?
    var validator_executable_path: String?
    var validator_total_timeout_ms: Int?
    var validator_io_timeout_ms: Int?
    var worker_post_apply_hang_ms: Int?
    var worker_post_apply_kill_signal: Int?
    var worker_pre_ready_hang_ms: Int?
    var worker_kill_before_publish_slot: Int?

    init(
        worker_executable_path: String? = nil,
        worker_timeout_ms: Int? = nil,
        issuer_executable_path: String? = nil,
        validator_executable_path: String? = nil,
        validator_io_timeout_ms: Int? = nil,
        validator_total_timeout_ms: Int? = nil,
        worker_post_apply_hang_ms: Int? = nil,
        worker_post_apply_kill_signal: Int? = nil,
        worker_pre_ready_hang_ms: Int? = nil,
        worker_kill_before_publish_slot: Int? = nil
    ) {
        self.worker_executable_path = worker_executable_path
        self.worker_timeout_ms = worker_timeout_ms
        self.issuer_executable_path = issuer_executable_path
        self.validator_executable_path = validator_executable_path
        self.validator_total_timeout_ms = validator_total_timeout_ms
        self.validator_io_timeout_ms = validator_io_timeout_ms
        self.worker_post_apply_hang_ms = worker_post_apply_hang_ms
        self.worker_post_apply_kill_signal = worker_post_apply_kill_signal
        self.worker_pre_ready_hang_ms = worker_pre_ready_hang_ms
        self.worker_kill_before_publish_slot = worker_kill_before_publish_slot
    }

    enum CodingKeys: String, CodingKey, CaseIterable {
        case worker_executable_path, worker_timeout_ms, issuer_executable_path, validator_executable_path, validator_io_timeout_ms, validator_total_timeout_ms
        case worker_post_apply_hang_ms, worker_post_apply_kill_signal, worker_pre_ready_hang_ms, worker_kill_before_publish_slot
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        func optionalInteger(_ key: CodingKeys) throws -> Int? {
            do { return try c.decodeIfPresent(Int.self, forKey: key) }
            catch {
                // Keep Foundation's private numeric-conversion errors at the
                // supplied field instead of letting them become root errors.
                throw DecodingError.typeMismatch(Int.self, .init(
                    codingPath: c.codingPath + [key], debugDescription: "expected a representable integer"))
            }
        }
        worker_executable_path = try c.decodeIfPresent(String.self, forKey: .worker_executable_path)
        worker_timeout_ms = try optionalInteger(.worker_timeout_ms)
        issuer_executable_path = try c.decodeIfPresent(String.self, forKey: .issuer_executable_path)
        validator_executable_path = try c.decodeIfPresent(String.self, forKey: .validator_executable_path)
        validator_total_timeout_ms = try optionalInteger(.validator_total_timeout_ms)
        validator_io_timeout_ms = try optionalInteger(.validator_io_timeout_ms)
        worker_post_apply_hang_ms = try optionalInteger(.worker_post_apply_hang_ms)
        worker_post_apply_kill_signal = try optionalInteger(.worker_post_apply_kill_signal)
        worker_pre_ready_hang_ms = try optionalInteger(.worker_pre_ready_hang_ms)
        worker_kill_before_publish_slot = try optionalInteger(.worker_kill_before_publish_slot)
    }

}

/// Versioned optional receipt for the exact compiler result supplied to apply.
/// `captured` requires a complete, checksum-verified worker capture and successful
/// application/process completion. This is not a readback of kernel state.
struct CompiledProfileCapture: Codable {
    var schema_version: Int = 2
    var status: String
    var reason: String?
    var worker_pid: Int
    var producer: String? = nil
    var capture_stage: String? = nil
    var request_nonce: String?
    var profile_type: Int?
    var bytecode_length: Int?
    var bytecode_sha256: String?
    var bytecode_b64: String?
    var source_sha256: String?
    var source_length: Int?
    var params_sha256: String?
    var parameter_count: Int?
}


// Keep context validation at the receipt boundary, including direct decoding
// and evidence-preserving reply encoding. No absent context implies a stage.
extension CompiledProfileCapture {
    var contextProblem: String? {
        guard schema_version == 2 else { return "unsupported compiled_profile schema_version" }
        switch status {
        case "captured":
            guard producer == "worker", capture_stage == "before_apply" else {
                return "compiled_profile requires worker/before_apply context"
            }
        case "unavailable":
            guard producer == nil, capture_stage == nil else {
                return "unavailable compiled_profile cannot claim capture context"
            }
        default: return "invalid compiled_profile status"
        }
        return nil
    }
    enum CodingKeys: String, CodingKey {
        case schema_version, status, reason, worker_pid, producer, capture_stage, request_nonce, profile_type, bytecode_length, bytecode_sha256, bytecode_b64, source_sha256, source_length, params_sha256, parameter_count
    }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        schema_version = try c.decode(Int.self, forKey: .schema_version)
        status = try c.decode(String.self, forKey: .status)
        reason = try c.decodeIfPresent(String.self, forKey: .reason)
        worker_pid = try c.decode(Int.self, forKey: .worker_pid)
        producer = try c.decodeIfPresent(String.self, forKey: .producer)
        capture_stage = try c.decodeIfPresent(String.self, forKey: .capture_stage)
        request_nonce = try c.decodeIfPresent(String.self, forKey: .request_nonce)
        profile_type = try c.decodeIfPresent(Int.self, forKey: .profile_type)
        bytecode_length = try c.decodeIfPresent(Int.self, forKey: .bytecode_length)
        bytecode_sha256 = try c.decodeIfPresent(String.self, forKey: .bytecode_sha256)
        bytecode_b64 = try c.decodeIfPresent(String.self, forKey: .bytecode_b64)
        source_sha256 = try c.decodeIfPresent(String.self, forKey: .source_sha256)
        source_length = try c.decodeIfPresent(Int.self, forKey: .source_length)
        params_sha256 = try c.decodeIfPresent(String.self, forKey: .params_sha256)
        parameter_count = try c.decodeIfPresent(Int.self, forKey: .parameter_count)
        if let problem = contextProblem {
            throw DecodingError.dataCorrupted(.init(codingPath: decoder.codingPath, debugDescription: problem))
        }
    }
    func encode(to encoder: Encoder) throws {
        if let problem = contextProblem {
            throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath, debugDescription: problem))
        }
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(schema_version, forKey: .schema_version)
        try c.encode(status, forKey: .status)
        try c.encodeIfPresent(reason, forKey: .reason)
        try c.encode(worker_pid, forKey: .worker_pid)
        try c.encodeIfPresent(producer, forKey: .producer)
        try c.encodeIfPresent(capture_stage, forKey: .capture_stage)
        try c.encodeIfPresent(request_nonce, forKey: .request_nonce)
        try c.encodeIfPresent(profile_type, forKey: .profile_type)
        try c.encodeIfPresent(bytecode_length, forKey: .bytecode_length)
        try c.encodeIfPresent(bytecode_sha256, forKey: .bytecode_sha256)
        try c.encodeIfPresent(bytecode_b64, forKey: .bytecode_b64)
        try c.encodeIfPresent(source_sha256, forKey: .source_sha256)
        try c.encodeIfPresent(source_length, forKey: .source_length)
        try c.encodeIfPresent(params_sha256, forKey: .params_sha256)
        try c.encodeIfPresent(parameter_count, forKey: .parameter_count)
    }
}

struct PWRunnerPolicySpec: Codable {
    // Policy format, e.g. PWRunnerWire.policyFormatSbpl.
    var format: String
    var sbpl_source: String?
    var params: [String: String]?
    /// Opt into sensitive worker-side bytecode/input identity capture.
    var capture_compiled_profile: Bool?
    /// Fresh 128-bit lowercase hex identity, echoed by the worker capture.
    var capture_nonce: String?
    // Named augments the caller opts into (e.g. "exec_baseline"). The
    // controller resolves each name to a file under
    // Contents/Resources/Augments/<name>.sb, appends the contents to
    // sbpl_source before the runner compiles, and strips this field from the
    // request forwarded to the runner. The runner is augment-agnostic;
    // this field exists on the wire so callers can author their request
    // without controller-private knowledge.
    var augments: [String]?

    init(
        format: String,
        sbpl_source: String? = nil,
        params: [String: String]? = nil,
        augments: [String]? = nil,
        capture_compiled_profile: Bool? = nil,
        capture_nonce: String? = nil
    ) {
        self.format = format
        self.sbpl_source = sbpl_source
        self.params = params
        self.augments = augments
        self.capture_compiled_profile = capture_compiled_profile
        self.capture_nonce = capture_nonce
    }

    enum CodingKeys: String, CodingKey, CaseIterable {
        case format, sbpl_source, params, capture_compiled_profile, capture_nonce, augments
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        format = try c.decode(String.self, forKey: .format)
        sbpl_source = try c.decodeIfPresent(String.self, forKey: .sbpl_source)
        params = try c.decodeIfPresent([String: String].self, forKey: .params)
        capture_compiled_profile = try c.decodeIfPresent(Bool.self, forKey: .capture_compiled_profile)
        capture_nonce = try c.decodeIfPresent(String.self, forKey: .capture_nonce)
        augments = try c.decodeIfPresent([String].self, forKey: .augments)
        // Only the controller resolves named augments. Direct XPC must not
        // accept a request whose policy fragments would silently disappear.
        if let augments, !augments.isEmpty { throw RequestContractError.unresolvedAugments }
    }

}

struct PWRunnerSandboxCheck: Codable {
    var operation: String
    var filter: PWRunnerSandboxFilter

    init(operation: String, filter: PWRunnerSandboxFilter) {
        self.operation = operation
        self.filter = filter
    }

    enum CodingKeys: String, CodingKey, CaseIterable {
        case operation, filter
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        operation = try c.decode(String.self, forKey: .operation)
        filter = try c.decode(PWRunnerSandboxFilter.self, forKey: .filter)
    }

}

struct PWRunnerSandboxFilter: Codable {
    // "none" | "path" | "global_name" | "local_name"
    var kind: String
    var value: String?

    init(kind: String, value: String? = nil) {
        self.kind = kind
        self.value = value
    }

    enum CodingKeys: String, CodingKey, CaseIterable {
        case kind, value
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        kind = try c.decode(String.self, forKey: .kind)
        value = try c.decodeIfPresent(String.self, forKey: .value)
    }

}

struct PWRunnerAttempt: Codable {
    // "file" | "mach_lookup" | "sysctl" | "exec"
    var kind: String
    // For kind=file:
    //   action: open_read | open_write | create | unlink | access
    //   target: path
    // For kind=mach_lookup:
    //   action: bootstrap_look_up
    //   target: mach service name
    // For kind=sysctl:
    //   action: read
    //   target: sysctl name
    // For kind=exec:
    //   action: spawn
    //   target: absolute path to a helper binary (becomes argv[0])
    //   args:   optional argv[1..N]; caps from PWShmLayout.maxArgv-1
    //           and PWShmLayout.argvBytes apply (per-arg byte cap
    //           includes the trailing NUL). Absent / nil treated as
    //           an empty list.
    var action: String
    var target: String
    var args: [String]?

    init(kind: String, action: String, target: String, args: [String]? = nil) {
        self.kind = kind
        self.action = action
        self.target = target
        self.args = args
    }

    enum CodingKeys: String, CodingKey, CaseIterable {
        case kind, action, target, args
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        kind = try c.decode(String.self, forKey: .kind)
        action = try c.decode(String.self, forKey: .action)
        target = try c.decode(String.self, forKey: .target)
        args = try c.decodeIfPresent([String].self, forKey: .args)
    }

}

struct PWRunnerProbeStep: Codable {
    var step_id: String
    var sandbox_check: PWRunnerSandboxCheck
    var attempt: PWRunnerAttempt

    init(step_id: String, sandbox_check: PWRunnerSandboxCheck, attempt: PWRunnerAttempt) {
        self.step_id = step_id
        self.sandbox_check = sandbox_check
        self.attempt = attempt
    }

    enum CodingKeys: String, CodingKey, CaseIterable {
        case step_id, sandbox_check, attempt
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        try rejectUnknownRequestKeys(CodingKeys.self, from: decoder)
        step_id = try c.decode(String.self, forKey: .step_id)
        sandbox_check = try c.decode(PWRunnerSandboxCheck.self, forKey: .sandbox_check)
        attempt = try c.decode(PWRunnerAttempt.self, forKey: .attempt)
    }

}

// Path forms observed by the unsandboxed runner host after orchestration.
// They are not validator/worker resolutions or comparison inputs.
//
// Wire form: `input` plus the two forms named in `formNames`. A form with the
// same UTF-8 bytes as `input` is listed in `same_as_input` and its key omitted; a form
// that differs is a string; a form the host could not derive is an explicit
// null. Each form is therefore in exactly one of those three states.
struct PWRunnerPathDiagnostics: Codable {
    static let formNames = ["realpath_resolved", "firmlink_resolved"]

    var observer: String?
    var stage: String?
    var input: String
    var realpath_resolved: String?
    var firmlink_resolved: String?

    init(
        input: String,
        realpath_resolved: String? = nil,
        firmlink_resolved: String? = nil,
        observer: String? = nil,
        stage: String? = nil
    ) {
        self.observer = observer
        self.stage = stage
        self.input = input
        self.realpath_resolved = realpath_resolved
        self.firmlink_resolved = firmlink_resolved
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: PathFormKey.self)
        try container.encodeIfPresent(observer, forKey: .observer)
        try container.encodeIfPresent(stage, forKey: .stage)
        try container.encode(input, forKey: .input)
        try encodePathForms(&container, input: input,
            forms: [("realpath_resolved", realpath_resolved), ("firmlink_resolved", firmlink_resolved)])
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: PathFormKey.self)
        observer = try container.decodeIfPresent(String.self, forKey: .observer)
        stage = try container.decodeIfPresent(String.self, forKey: .stage)
        input = try container.decode(String.self, forKey: .input)
        let decoded = try decodePathForms(container, input: input, formNames: Self.formNames)
        realpath_resolved = decoded["realpath_resolved"] ?? nil
        firmlink_resolved = decoded["firmlink_resolved"] ?? nil
    }
}

/// Dynamic key for the shared three-state path-form wire rule, so the query
/// and attempt blocks differ only in their form-name lists.
struct PathFormKey: CodingKey {
    var stringValue: String
    var intValue: Int? { nil }
    init(stringValue: String) { self.stringValue = stringValue }
    init?(intValue: Int) { nil }
    static let observer = PathFormKey(stringValue: "observer")
    static let stage = PathFormKey(stringValue: "stage")
    static let input = PathFormKey(stringValue: "input")
    static let sameAsInput = PathFormKey(stringValue: "same_as_input")
}

/// Encode `forms` beside `input`: a form with the same UTF-8 bytes as `input`
/// is listed in `same_as_input` and omitted, a different form is a string, an
/// underivable form is an explicit null.
func encodePathForms(_ container: inout KeyedEncodingContainer<PathFormKey>, input: String,
                     forms: [(String, String?)]) throws {
    var sameAsInput: [String] = []
    for (name, value) in forms {
        let key = PathFormKey(stringValue: name)
        if let value, value.utf8.elementsEqual(input.utf8) {
            sameAsInput.append(name)
        } else if let value {
            try container.encode(value, forKey: key)
        } else {
            // Explicit null: the host computed this form and got nothing.
            try container.encodeNil(forKey: key)
        }
    }
    try container.encode(sameAsInput, forKey: .sameAsInput)
}

/// Decode the forms in `formNames` under the same rule. The compact marker is
/// required: each form is listed, a string or an explicit null, exclusively.
func decodePathForms(_ container: KeyedDecodingContainer<PathFormKey>, input: String,
                     formNames: [String]) throws -> [String: String?] {
    guard container.contains(.sameAsInput) else {
        throw DecodingError.dataCorruptedError(forKey: .sameAsInput, in: container,
            debugDescription: "path diagnostics require same_as_input")
    }
    let sameAsInput = try container.decode([String].self, forKey: .sameAsInput)
    if Set(sameAsInput).count != sameAsInput.count || !Set(sameAsInput).isSubset(of: Set(formNames)) {
        throw DecodingError.dataCorruptedError(forKey: .sameAsInput, in: container,
            debugDescription: "same_as_input must contain unique supported form names")
    }
    var values: [String: String?] = [:]
    for name in formNames {
        let key = PathFormKey(stringValue: name)
        let listed = sameAsInput.contains(name)
        if listed == container.contains(key) {
            throw DecodingError.dataCorruptedError(forKey: key, in: container,
                debugDescription: "form must be either listed in same_as_input or present, exclusively")
        }
        if listed {
            values[name] = .some(input)
            continue
        }
        let value = try container.decodeIfPresent(String.self, forKey: key)
        if let value, value.utf8.elementsEqual(input.utf8) {
            throw DecodingError.dataCorruptedError(forKey: key, in: container,
                debugDescription: "a form with identical UTF-8 bytes must be listed in same_as_input")
        }
        values[name] = .some(value)
    }
    return values
}

// The unsandboxed host's after-orchestration resolution of a file or exec
// attempt target. `realpath_resolved` follows the leaf; `parent_realpath_resolved`
// resolves the parent and keeps the leaf literal, the form the kernel names for
// a created or unlinked path. Neither establishes what the worker's own syscall
// resolved: they are candidate evidence for deny-log correlation only.
struct PWRunnerAttemptPathDiagnostics: Codable {
    static let formNames = ["realpath_resolved", "parent_realpath_resolved"]

    var observer: String?
    var stage: String?
    var input: String
    var realpath_resolved: String?
    var parent_realpath_resolved: String?

    init(
        input: String,
        realpath_resolved: String? = nil,
        parent_realpath_resolved: String? = nil,
        observer: String? = nil,
        stage: String? = nil
    ) {
        self.observer = observer
        self.stage = stage
        self.input = input
        self.realpath_resolved = realpath_resolved
        self.parent_realpath_resolved = parent_realpath_resolved
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: PathFormKey.self)
        try container.encodeIfPresent(observer, forKey: .observer)
        try container.encodeIfPresent(stage, forKey: .stage)
        try container.encode(input, forKey: .input)
        try encodePathForms(&container, input: input,
            forms: [("realpath_resolved", realpath_resolved), ("parent_realpath_resolved", parent_realpath_resolved)])
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: PathFormKey.self)
        observer = try container.decodeIfPresent(String.self, forKey: .observer)
        stage = try container.decodeIfPresent(String.self, forKey: .stage)
        input = try container.decode(String.self, forKey: .input)
        let decoded = try decodePathForms(container, input: input, formNames: Self.formNames)
        realpath_resolved = decoded["realpath_resolved"] ?? nil
        parent_realpath_resolved = decoded["parent_realpath_resolved"] ?? nil
    }
}

struct PWRunnerSandboxCheckResult: Codable {
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

    enum CodingKeys: String, CodingKey {
        case result_source, native_rc, missing_reason
        case rc
        case outcome
        case pid
        case operation
        case filter_kind
        case filter_value
        case filter_type_id
        case errno
        case error
        case path_diagnostics
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(result_source, forKey: .result_source)
        if result_source != nil { try container.encode(native_rc, forKey: .native_rc) }
        try container.encodeIfPresent(missing_reason, forKey: .missing_reason)
        try container.encode(rc, forKey: .rc)
        try container.encode(outcome, forKey: .outcome)
        try container.encode(pid, forKey: .pid)
        try container.encode(operation, forKey: .operation)
        try container.encode(filter_kind, forKey: .filter_kind)
        if let filter_value {
            try container.encode(filter_value, forKey: .filter_value)
        } else {
            try container.encodeNil(forKey: .filter_value)
        }
        if let filter_type_id {
            try container.encode(filter_type_id, forKey: .filter_type_id)
        } else {
            try container.encodeNil(forKey: .filter_type_id)
        }
        if let errno {
            try container.encode(errno, forKey: .errno)
        } else {
            try container.encodeNil(forKey: .errno)
        }
        if let error {
            try container.encode(error, forKey: .error)
        } else {
            try container.encodeNil(forKey: .error)
        }
        // Omit the key entirely on non-path filters so the output stays minimal
        // and consumers can branch on `path_diagnostics != nil` rather than
        // inspecting a null payload.
        if let path_diagnostics {
            try container.encode(path_diagnostics, forKey: .path_diagnostics)
        }
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        result_source = try container.decodeIfPresent(String.self, forKey: .result_source)
        native_rc = try container.decodeIfPresent(Int.self, forKey: .native_rc)
        missing_reason = try container.decodeIfPresent(String.self, forKey: .missing_reason)
        rc = try container.decode(Int.self, forKey: .rc)
        outcome = try container.decode(String.self, forKey: .outcome)
        pid = try container.decodeIfPresent(Int.self, forKey: .pid)
        operation = try container.decode(String.self, forKey: .operation)
        filter_kind = try container.decode(String.self, forKey: .filter_kind)
        filter_value = try container.decodeIfPresent(String.self, forKey: .filter_value)
        filter_type_id = try container.decodeIfPresent(Int.self, forKey: .filter_type_id)
        errno = try container.decodeIfPresent(Int.self, forKey: .errno)
        error = try container.decodeIfPresent(String.self, forKey: .error)
        path_diagnostics = try container.decodeIfPresent(PWRunnerPathDiagnostics.self, forKey: .path_diagnostics)
    }
}

struct PWRunnerAttemptResult: Codable {
    /// Submitted intent, not proof that the named native operation ran. See
    /// the "Worker evidence contract" in tests/FAILURE-PROPAGATION-CONTRACT.md
    /// for PW status versus missing reasons.
    var requested_kind: String? = nil
    var requested_action: String? = nil
    var result_source: String? = nil
    var missing_reason: String? = nil
    /// Projection of this step's disposition claims. It is the evidence for
    /// whether a `no_completed_result`/`slot_incomplete` step started.
    var lifecycle: PWAttemptLifecycle? = nil
    /// PW's attempt status, not a raw syscall return.
    var fresh_read: PWRunnerFreshRead? = nil
    var rc: Int
    var errno: Int?
    var outcome: String
    var error: String?
    var requested_path: String?
    /// Host-resolved forms of the attempt target; absent for non-path attempts.
    var path_diagnostics: PWRunnerAttemptPathDiagnostics?
    var observed_path: String?

    /// Exec-attempt outputs. All five are nil for non-exec attempts and
    /// are emitted as explicit JSON null (when populated) or omitted
    /// entirely (when nil) so a sysctl/file/mach result envelope does
    /// not grow five new null fields it has no use for.
    ///
    /// `child_pid > 0` means `posix_spawn` produced a child; it does not
    /// establish reaping. Unconfirmed status keeps exit -1 / signal 0.
    /// Attempt rc may fail independently of a natural leader exit.
    /// `child_pid == 0` means
    /// spawn failed before producing a child (sandbox blocked spawn,
    /// target missing, etc.) — `errno` carries the spawn errno in
    /// that case. comparisonEvidence reads `child_pid` to distinguish
    /// spawn failure from a child non-zero exit. EPERM/EACCES without
    /// a child remain ambiguous: execute permissions can also prevent
    /// spawning.
    var child_pid: Int?
    var child_exit_code: Int?
    var child_term_signal: Int?
    var stdout: String?
    var stderr: String?

    init(
        rc: Int,
        errno: Int? = nil,
        outcome: String,
        error: String? = nil,
        requested_path: String? = nil,
        path_diagnostics: PWRunnerAttemptPathDiagnostics? = nil,
        observed_path: String? = nil,
        child_pid: Int? = nil,
        child_exit_code: Int? = nil,
        child_term_signal: Int? = nil,
        stdout: String? = nil,
        stderr: String? = nil
    ) {
        self.rc = rc
        self.errno = errno
        self.outcome = outcome
        self.error = error
        self.requested_path = requested_path
        self.path_diagnostics = path_diagnostics
        self.observed_path = observed_path
        self.child_pid = child_pid
        self.child_exit_code = child_exit_code
        self.child_term_signal = child_term_signal
        self.stdout = stdout
        self.stderr = stderr
    }

    enum CodingKeys: String, CodingKey {
        case requested_kind, requested_action
        case result_source, missing_reason, lifecycle
        case rc, fresh_read
        case errno
        case outcome
        case error
        case requested_path
        case path_diagnostics
        case observed_path
        case child_pid
        case child_exit_code
        case child_term_signal
        case stdout
        case stderr
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(requested_kind, forKey: .requested_kind)
        try container.encodeIfPresent(requested_action, forKey: .requested_action)
        try container.encodeIfPresent(result_source, forKey: .result_source)
        try container.encodeIfPresent(missing_reason, forKey: .missing_reason)
        try container.encodeIfPresent(lifecycle, forKey: .lifecycle)
        try container.encodeIfPresent(fresh_read, forKey: .fresh_read)
        try container.encode(rc, forKey: .rc)
        if let errno {
            try container.encode(errno, forKey: .errno)
        } else {
            try container.encodeNil(forKey: .errno)
        }
        try container.encode(outcome, forKey: .outcome)
        try container.encodeIfPresent(error, forKey: .error)
        if let requested_path {
            try container.encode(requested_path, forKey: .requested_path)
        } else {
            try container.encodeNil(forKey: .requested_path)
        }
        try container.encodeIfPresent(path_diagnostics, forKey: .path_diagnostics)
        if let observed_path {
            try container.encode(observed_path, forKey: .observed_path)
        } else {
            try container.encodeNil(forKey: .observed_path)
        }
        // Exec output fields: emit when non-nil, omit the key when nil.
        // A completed exec slot supplies the three child fields, including
        // child_pid == 0 / child_exit_code == -1 / child_term_signal == 0
        // when spawn failed. stdout/stderr are included only when that
        // stream produced bytes. Non-exec attempts omit all five fields.
        try container.encodeIfPresent(child_pid, forKey: .child_pid)
        try container.encodeIfPresent(child_exit_code, forKey: .child_exit_code)
        try container.encodeIfPresent(child_term_signal, forKey: .child_term_signal)
        try container.encodeIfPresent(stdout, forKey: .stdout)
        try container.encodeIfPresent(stderr, forKey: .stderr)
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        requested_kind = try container.decodeIfPresent(String.self, forKey: .requested_kind)
        requested_action = try container.decodeIfPresent(String.self, forKey: .requested_action)
        result_source = try container.decodeIfPresent(String.self, forKey: .result_source)
        missing_reason = try container.decodeIfPresent(String.self, forKey: .missing_reason)
        lifecycle = try container.decodeIfPresent(PWAttemptLifecycle.self, forKey: .lifecycle)
        fresh_read = try container.decodeIfPresent(PWRunnerFreshRead.self, forKey: .fresh_read)
        rc = try container.decode(Int.self, forKey: .rc)
        errno = try container.decodeIfPresent(Int.self, forKey: .errno)
        outcome = try container.decode(String.self, forKey: .outcome)
        error = try container.decodeIfPresent(String.self, forKey: .error)
        requested_path = try container.decodeIfPresent(String.self, forKey: .requested_path)
        path_diagnostics = try container.decodeIfPresent(PWRunnerAttemptPathDiagnostics.self, forKey: .path_diagnostics)
        observed_path = try container.decodeIfPresent(String.self, forKey: .observed_path)
        child_pid = try container.decodeIfPresent(Int.self, forKey: .child_pid)
        child_exit_code = try container.decodeIfPresent(Int.self, forKey: .child_exit_code)
        child_term_signal = try container.decodeIfPresent(Int.self, forKey: .child_term_signal)
        stdout = try container.decodeIfPresent(String.self, forKey: .stdout)
        stderr = try container.decodeIfPresent(String.self, forKey: .stderr)
    }
}

/// Eligibility of a native record for `order: query_first`.
func eligibleOrderedPrediction(_ query: PWRunnerSandboxCheckResult) -> Bool {
    guard query.result_source == "validator", let rc = query.native_rc,
          let err = query.errno, query.rc == rc else { return false }
    return (query.outcome == "allow" && rc == 0) || (query.outcome == "deny" && rc == 1 && err == 0)
}

// Shared by construction and encoding: a native record must be uniquely
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
struct PWRunnerComparison: Codable {
    var observation: String
    var observation_basis: String
    var operation_relation: String
    var target_relation: String
    var order: String
    var limitations: [String]

    /// The `limitations` vocabulary: the planner's exclusion codes and the
    /// lifecycle entries. The encoder rejects any other string.
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

struct PWRunnerStepResult: Codable {
    var phase_id: String
    var step_id: String
    var sandbox_check: PWRunnerSandboxCheckResult
    var attempt: PWRunnerAttemptResult
    /// Present on every step of an ordinary reply; withheld by a
    /// `runner_reporting_failed` reply.
    var comparison: PWRunnerComparison?

    init(
        step_id: String,
        phase_id: String = "main",
        sandbox_check: PWRunnerSandboxCheckResult,
        attempt: PWRunnerAttemptResult,
        comparison: PWRunnerComparison? = nil
    ) {
        self.phase_id = phase_id
        self.step_id = step_id
        self.sandbox_check = sandbox_check
        self.attempt = attempt
        self.comparison = comparison
    }

    enum CodingKeys: String, CodingKey {
        case phase_id, step_id
        case sandbox_check
        case attempt
        case comparison
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(comparison, forKey: .comparison)
        try container.encode(phase_id, forKey: .phase_id)
        try container.encode(step_id, forKey: .step_id)
        try container.encode(sandbox_check, forKey: .sandbox_check)
        try container.encode(attempt, forKey: .attempt)
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        phase_id = try container.decode(String.self, forKey: .phase_id)
        step_id = try container.decode(String.self, forKey: .step_id)
        sandbox_check = try container.decode(PWRunnerSandboxCheckResult.self, forKey: .sandbox_check)
        attempt = try container.decode(PWRunnerAttemptResult.self, forKey: .attempt)
        comparison = try container.decodeIfPresent(PWRunnerComparison.self, forKey: .comparison)
    }
}

/// Host observation of one kill(2) request, not evidence of its delivery or cause.
/// JSON: runner_subprocess.termination_request.{signal,rc,errno}. All numbers
/// are signed 32-bit syscall values encoded as JSON integers (no units).
/// errno is captured immediately only when rc == -1; otherwise it is absent/null.
/// An absent/null request means no request. Structurally valid values are decoded
/// without a signal/errno allowlist. The client/controller forward this object.
struct PWRunnerTerminationRequest: Codable {
    let signal: Int32
    let rc: Int32
    let errno: Int32?

    init(signal: Int32, rc: Int32, errno: Int32?) {
        self.signal = signal
        self.rc = rc
        self.errno = errno
    }
}

/// One host-observed failed waitpid(2) call, including recovered interruptions.
/// JSON: runner_subprocess.wait_errors[].{stage,rc,errno}. stage is a string
/// (poll, exit_grace, after_termination); rc/errno are signed 32-bit integers.
/// Only rc == -1 produces a record, with errno captured before another call.
/// Unknown stage/errno values remain transportable. Empty array means no errors
/// observed; absent/null array means unavailable.
struct PWRunnerWaitError: Codable {
    let stage: String
    let rc: Int32
    let errno: Int32

    init(stage: String, rc: Int32, errno: Int32) {
        self.stage = stage
        self.rc = rc
        self.errno = errno
    }
}

/// Host-observed UTF-8 policy transfer failure; counts are writes, not child reads.
/// See tests/FAILURE-PROPAGATION-CONTRACT.md for field validity and JSON semantics.
/// Timer observation; byte counts are writes accepted, not child reads.
struct PWWorkerPolicyTransferTimeout: Codable {
    var budget_ms: Int
    var elapsed_ms: UInt64
    var bytes_written: Int
    var bytes_expected: Int
}
struct PWWorkerPolicyTransferError: Codable {
    var errno: Int32
    var bytes_written: Int
    var bytes_expected: Int
}
/// Worker publications. Numeric codes are open, never Codable enums.
struct PWWorkerProgress: Codable {
    var raw: UInt32
    var operation: UInt32
    var stage: UInt32
    var index: UInt32?
}
struct PWWorkerFailure: Codable {
    var operation: UInt32
    var code: UInt32
    var native_kind: UInt32
    var native_result: Int32?
    var errno: Int32?
    var index: UInt32?
    var detail: UInt32
}
struct PWWorkerReadiness: Codable {
    var rc: Int32
    var errno: Int32?
}
struct PWWorkerDiagnostic: Codable {
    var state: UInt32
    var status: String
    var length: UInt32?
    var text: String?
}
/// The worker's EOF receipt for the policy pipe: the host's expected byte count
/// (its immutable header input) beside the count the worker read at EOF. Present
/// only when the worker published it, which happens before the length comparison;
/// a header refusal, read error or overflow publishes none. Equal counts establish
/// length agreement with the submission, not content identity, compilation,
/// application or kernel effect. Absence establishes nothing about delivery.
struct PWWorkerPolicyRead: Codable, Equatable {
    var bytes_expected: Int
    var bytes_received: Int
}
/// The worker's fixed source buffer less its terminating NUL (PW_SHM_POLICY_BYTES - 1),
/// the bound on both receipt counts. Stated here because the client target compiles
/// this file without the layout mirror; `PolicyTransferTests` pins agreement with
/// `PWShmLayout.policyBytes`.
let policyReceiptCapacityBytes = 262_143
struct PWWorkerEvidence: Codable {
    /// Host-selected source identity, not proof that a child reached ABI validation.
    var abi_identity: String
    var progress: PWWorkerProgress?
    var failure_publication: UInt32
    var failure_state: String
    var failure: PWWorkerFailure?
    var readiness: PWWorkerReadiness?
    var diagnostic: PWWorkerDiagnostic
    var policy_read: PWWorkerPolicyRead? = nil
}

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

/// Authoritative worker process metadata, produced by the unsandboxed host.
/// Lifecycle observations are host-owned; worker_evidence uses the exact host/worker identity.
/// All live CWorkerOutput paths populate the optional observation fields below;
/// an absent observation is unknown, not false. Policy-write failures retain
/// partial child observations.
struct PWRunnerOrdering: Codable {
    var collection_closed_before_proceed: Bool
    var proceed_set: Bool
    var proceed_observed: Bool
    var validator_disposition: String
    /// Ownership through acknowledgement, not the eventual cleanup outcome.
    var worker_lifetime_established: Bool
    var protocol_violations: [String]

    var chainEstablished: Bool {
        collection_closed_before_proceed && proceed_set && proceed_observed
            && worker_lifetime_established && protocol_violations.isEmpty
    }
}

/// One host wait measured on CLOCK_MONOTONIC: its allowance, the elapsed time
/// when it stopped and why it stopped. `excluded_ms` is time the wait does not
/// charge (synchronous phase collection inside the sentinel wait); the
/// allowance consumed is `elapsed_ms - excluded_ms`. `clock_unavailable` means
/// the clock failed or ran backwards and the wait fell back to a bounded number
/// of fixed sleeps; `setup_failed` means the nonblocking prerequisite could not
/// be established and no wait was attempted. Elapsed time is absent when the
/// clock could not supply it, and `clock_fault` says the clock failed or ran
/// backwards during the wait. A stop names when the host moved on, not when a
/// child ended.
struct PWHostWait: Codable, Equatable {
    var budget_ms: Int
    var elapsed_ms: UInt64?
    var stop: String
    var excluded_ms: UInt64?
    var native_errno: Int32?
    var clock_fault: Bool
}

struct PWRunnerSubprocess: Codable {
    var pid: Int
    /// JSON integers, meaningful only after waitpid returned this child's PID.
    /// Both may be absent/null when status was not obtained; zero is a real exit.
    var term_signal: Int?
    var exit_code: Int?
    var partial_steps: Bool
    /// Worker publication snapshot; absent before spawn.
    var worker_evidence: PWWorkerEvidence? = nil
    /// Host transfer observation independent of any child publication.
    var policy_transfer_timeout: PWWorkerPolicyTransferTimeout? = nil
    var policy_transfer_error: PWWorkerPolicyTransferError? = nil
    /// Host read of the ready byte; false does not prove compilation failed.
    var ready_byte_received: Bool?
    /// Final acquire observation of done after cleanup, not successful application.
    /// poll_stop_reason separately retains the reason the polling stage ended.
    var done_observed: Bool?
    /// Host string: done, child_reaped, sentinel_deadline, wait_error, policy_write_error, or policy_transfer_deadline.
    /// Identifies why polling stopped; later cleanup must not rewrite it.
    /// Only sentinel_deadline establishes exhaustion of the polling budget.
    /// Unknown strings survive decoding; they do not imply a known condition.
    var poll_stop_reason: String?
    /// Host performed the release-store of exit_requested; not worker receipt.
    var exit_requested: Bool?
    var termination_request: PWRunnerTerminationRequest?
    /// True only when waitpid actually returned this PID. False is explicitly
    /// unconfirmed disposition, distinct from an absent/null observation.
    var reaped: Bool?
    var wait_errors: [PWRunnerWaitError]?
    /// Host facts recorded where the host acts (tests/FAILURE-PROPAGATION-CONTRACT.md,
    /// "Worker disposition record"): why exit was requested, how the exit-grace
    /// wait ended, and whether the final reads followed a confirmed reap.
    /// Absence is unreported, not observed false.
    var cleanup_trigger: String? = nil
    var grace_end: String? = nil
    var collection_basis: String? = nil
    /// Measured host waits: readiness hint, publication (sentinel) and exit grace.
    /// Absent when the stage did not run.
    var ready_wait: PWHostWait? = nil
    var sentinel_wait: PWHostWait? = nil
    var exit_grace_wait: PWHostWait? = nil
    /// The canonical lifecycle account, resolved once by the host. Mandatory
    /// whenever this object is present.
    var disposition: PWDispositionRecord? = nil

    init(
        pid: Int,
        term_signal: Int? = nil,
        exit_code: Int? = nil,
        partial_steps: Bool,
        ready_byte_received: Bool? = nil,
        done_observed: Bool? = nil,
        poll_stop_reason: String? = nil,
        exit_requested: Bool? = nil,
        termination_request: PWRunnerTerminationRequest? = nil,
        reaped: Bool? = nil,
        wait_errors: [PWRunnerWaitError]? = nil
    ) {
        self.pid = pid
        self.term_signal = term_signal
        self.exit_code = exit_code
        self.partial_steps = partial_steps
        self.ready_byte_received = ready_byte_received
        self.done_observed = done_observed
        self.poll_stop_reason = poll_stop_reason
        self.exit_requested = exit_requested
        self.termination_request = termination_request
        self.reaped = reaped
        self.wait_errors = wait_errors
    }
}

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
    /// Temporal order of worker operations (pw_probe_runner_abi.h): proceed (11)
    /// precedes the indexed attempts (9); completion (10) follows them.
    static let protocolOrder: [UInt32] = [1, 2, 3, 4, 5, 6, 7, 8, 11, 9, 10]
    static let runReferences = ["reaped", "exit_code", "term_signal", "poll_stop_reason", "exit_requested",
                                       "termination_request", "wait_errors", "cleanup_trigger", "grace_end",
                                       "collection_basis", "done_observed", "progress", "worker_failure", "plan"]
    static let stepReferences = ["slot", "attempt_support"]
}

extension PWRunnerTerminationRequest: Equatable {}

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
            if sub.reaped != true || sub.term_signal == nil || sub.exit_code != nil || final.value != sub.term_signal.map { .integer($0) } {
                problems.append("final_status: signal claim contradicts reaped/term_signal")
            }
        case ("supported", "exit_code"?):
            if sub.reaped != true || sub.exit_code == nil || sub.term_signal != nil || final.value != sub.exit_code.map { .integer($0) } {
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

struct ValidatorVerdict: Codable {
    enum CodingKeys: String, CodingKey {
        case stepId = "step_id", operation, filterType = "filter_type"
        case filterTypeId = "filter_type_id", filterValue = "filter_value"
        case rc, errnoVal = "errno", outcome, error, rawLine = "raw_line"
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(stepId, forKey: .stepId)
        try c.encodeIfPresent(operation, forKey: .operation)
        try c.encodeIfPresent(filterType, forKey: .filterType)
        try c.encodeIfPresent(filterTypeId, forKey: .filterTypeId)
        try c.encodeIfPresent(filterValue, forKey: .filterValue)
        try c.encodeIfPresent(rc, forKey: .rc)
        try c.encodeIfPresent(errnoVal, forKey: .errnoVal)
        try c.encode(outcome, forKey: .outcome)
        try c.encodeIfPresent(error, forKey: .error)
        try c.encode(rawLine, forKey: .rawLine)
    }
    var stepId: String?
    var operation: String?
    var filterType: String?
    var filterTypeId: Int?
    var filterValue: String?
    var rc: Int?
    var errnoVal: Int?
    var outcome: String             // "allow"|"deny"|"error"|"parse_error"|"bad_filter"
    var error: String?
    var rawLine: String             // for debugging
}

/// Receiver-owned rejected frame context. The prefix is bytes, not repaired
/// JSON. Offsets/lengths are exact received byte counts; at most 256 context
/// bytes are retained. Unknown diagnostic outcome names are not decode faults.
struct PWValidatorDecodeFault: Codable {
    var origin: String = "runner_host"
    var kind: String // utf8, json, structure
    var message: String
    var byte_offset: Int
    var frame_bytes: Int
    var retained_bytes: Int
    var context_b64: String
    var context_truncated: Bool
}

struct PWValidatorAssociationIssue: Codable {
    var origin: String = "runner_host"
    var kind: String // missing_id, duplicate_id, unexpected_id, unassociated
    var step_id: String? = nil
    var count: Int
}

/// Validator child observations. Missing host fields remain unknown.
/// Only successful reaping supplies exit/signal. Records are accepted validator
/// evidence, independently retained even when association/transport/cleanup fails.
/// A null-ID record is never assigned an invented step identity.
struct PWRunnerValidatorSubprocess: Codable {
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

/// Host admission: no worker publication or child process is implied.
/// UTF-8 lengths count payload bytes; item counts use `items`. `nul_bytes`
/// counts embedded NULs in native C strings, whose maximum is zero.
struct PWRunnerAdmissionFailure: Codable {
    var origin: String = "runner_host"
    var field: String
    var actual: Int
    var maximum: Int
    var unit: String
    /// The offending step's ID, omitted when the step ID itself is the refused
    /// field: a refusal never echoes the string it refused. `step_index` is the
    /// step's position in `probe_plan` and accompanies every per-step refusal.
    var step_id: String?
    var step_index: Int?
    /// The offending parameter's key, omitted when the key itself is refused;
    /// the field name and byte count identify it.
    var parameter_key: String?
    /// The offending argv position for exec argument refusals.
    var index: Int?
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
                if let issue = step.attempt.freshReadEvidenceProblem() {
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

func pwRunnerEncodeJSON<T: Encodable>(_ value: T) throws -> Data {
    let enc = JSONEncoder()
    enc.outputFormatting = [.sortedKeys]
    return try enc.encode(value)
}

func pwRunnerDecodeJSON<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
    let dec = JSONDecoder()
    return try dec.decode(type, from: data)
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

extension PWRunnerAttemptResult {
    func freshReadEvidenceProblem() -> String? {
        let expected = requested_kind == "file" && requested_action == "read_fresh" && result_source == "worker"
        guard let read = fresh_read else { return expected ? "completed fresh read lacks syscall observations" : nil }
        guard expected, read.open_rc >= -1 else { return "fresh read requires a completed read_fresh attempt" }
        if read.open_rc == -1 {
            guard let error = read.open_errno, error >= 0, read.read_rc == nil, read.read_errno == nil,
                  read.stat_rc == nil, read.stat_errno == nil, read.identity == nil,
                  read.close_rc == nil, read.close_errno == nil, read.content_hex == nil,
                  rc == -1, errno == (error == 0 ? nil : Int(error)), outcome == AttemptOutcome.readFailed else {
                return "failed fresh open cannot supply read/stat/close evidence"
            }
            return nil
        }
        guard read.open_errno == nil, let count = read.read_rc, count >= -1 && count <= PWExtensionLimits.freshReadBytes,
              let stat = read.stat_rc, [-1, 0].contains(stat), let close = read.close_rc, [-1, 0].contains(close) else { return "invalid fresh syscall results" }
        func validErrno(_ result: Int64, _ error: Int32?) -> Bool { result < 0 ? error != nil && error! >= 0 : error == nil }
        guard validErrno(count, read.read_errno), validErrno(Int64(stat), read.stat_errno), validErrno(Int64(close), read.close_errno),
              (stat == 0) == (read.identity != nil) else { return "fresh syscall failure evidence disagrees" }
        if count >= 0 {
            guard let content = read.content_hex, content.utf8.count == Int(count) * 2,
                  content.utf8.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }) else { return "fresh read bytes disagree with native count" }
        } else if read.content_hex != nil { return "failed fresh read cannot supply content" }
        let failed = stat < 0 || count < 0 || close < 0
        let error = stat < 0 ? read.stat_errno : count < 0 ? read.read_errno : close < 0 ? read.close_errno : nil
        guard rc == (failed ? -1 : 0), errno == error.flatMap({ $0 == 0 ? nil : Int($0) }),
              outcome == (failed ? AttemptOutcome.readFailed : AttemptOutcome.ok) else { return "fresh syscall results disagree with attempt" }
        return nil
    }
}

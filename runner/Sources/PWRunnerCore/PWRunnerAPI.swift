import Foundation

// PWRunner is a single-purpose, ephemeral XPC runner. The XPC service host
// stays unsandboxed; a short-lived worker self-applies a seatbelt profile,
// executes the probe plan, returns a report to the host, and exits.
//
// This file intentionally defines a small JSON-over-Data protocol surface so the
// runner can be driven by multiple controllers (CLI, lab tools) without NSXPC
// object graphs.

@objc public protocol PWRunnerProtocol {
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
    static let sandboxCheckScopePost = "post_sandbox"
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
public enum NormalizedOutcome {
    // Successful execution and a reserved precise apply-failure spelling.
    // Legacy ABI status cannot identify a failed native operation; current
    // published preparation/application failures map to runner_failed.
    public static let ok = "ok"
    public static let sandboxApplyFailed = "sandbox_apply_failed"

    // ----- emitted by the host short-circuit (pre-spawn libsandbox check)
    public static let libsandboxUnavailable = "libsandbox_unavailable"

    // ----- emitted by the host short-circuit (PWRunnerService.swift).
    // `bad_policy` is the host's pre-spawn structural check (computePolicyHash:
    // missing sbpl_source / non-sbpl format), NOT a compile-error signal — SBPL
    // that fails to compile reaches the worker and surfaces as
    // runner_failed with an ambiguous published legacy status.
    public static let badPolicy = "bad_policy"
    public static let badRequest = "bad_request"
    public static let alreadyRan = "already_ran"
    public static let workerSpawnFailed = "worker_spawn_failed"

    // ----- emitted by the host classifier (CWorker.swift sentinel
    // observation + CWorkerOrchestrator classification)
    // Recognized legacy string only; signals and PID-matched denials do not
    // establish a sandbox cause, so current producers never emit this label.
    public static let runnerSandboxDenied = "runner_sandbox_denied"
    public static let runnerTimeout = "runner_timeout"
    public static let runnerFailed = "runner_failed"
    // Host reply construction failed; the original execution summary is retained
    // in reporting_failure, independently of child or policy observations.
    public static let runnerReportingFailed = "runner_reporting_failed"

    // ----- emitted by the host classifier on the validator child
    // failure modes. Default top-level semantics: any validator_*
    // outcome makes `result.ok=false`, `rc=1`. The attempt channel
    // is still populated and machine-readable, but a missing
    // prediction channel is a runner evidence failure even when the
    // observation channel completed. Consumers can opt to consume
    // the partial envelope as degraded evidence; the runner does not
    // silently upgrade an attempts-only run to `ok`.
    public static let validatorSpawnFailed = "validator_spawn_failed"
    public static let validatorNoReply = "validator_no_reply"
    public static let validatorDecodeFailure = "validator_decode_failure"
    public static let validatorUnavailable = "validator_unavailable"

    // ----- synthesized by pw-runner-client when the XPC peer is unreachable
    public static let xpcError = "xpc_error"
    public static let xpcTimeout = "xpc_timeout"
    public static let xpcProxyTypeMismatch = "xpc_proxy_type_mismatch"
    public static let xpcNoReply = "xpc_no_reply"
}

/// Canonical step.attempt.outcome values. Parallels NormalizedOutcome
/// and SandboxCheckOutcome: new constants are added here (with the
/// matching wire string) before any emit site uses them, and
/// source_drift enforces that every constant has a row in
/// tests/COVERAGE.md's attempt-outcome matrix.
///
/// `not_run_worker_died` is a compatibility spelling for no completed attempt
/// result. Missing publication does not prove the operation never started.
/// Treat it as missing evidence, never as an access verdict.
public enum AttemptOutcome {
    public static let ok = "ok"
    public static let openFailed = "open_failed"
    public static let unlinkFailed = "unlink_failed"
    public static let accessFailed = "access_failed"
    public static let lookupFailed = "lookup_failed"
    public static let sysctlFailed = "sysctl_failed"
    public static let execFailed = "exec_failed"
    public static let bootstrapPortFailed = "bootstrap_port_failed"
    public static let unsupported = "unsupported"
    public static let notRunWorkerDied = "not_run_worker_died"
}

// Canonical step.sandbox_check.outcome values. New constants should be
// added here (with the matching wire string) before any emit site uses
// them, by the same convention as NormalizedOutcome.
//
// `prediction_unavailable` is emitted when the runner deliberately
// declines to call sandbox_check because the userland predicate is
// known to drift from kernel enforcement for the (operation, filter)
// pair (verified via
// tests/suites/witness_contract/harness/verify_filter_id.sh). Channel
// A (the attempt result) remains the reliable evidence for those
// probes; the prediction is honestly absent rather than wrong.
//
// When emitted, the result's `rc` field is the sentinel -1 (NOT 0) so
// any consumer that keys on `rc == 0` for "allow" cannot misread the
// absent prediction as an allow verdict. See docs/PolicyWitness.md
// "Filter kinds where prediction is unavailable" for the full
// contract.
public enum SandboxCheckOutcome {
    public static let allow = "allow"
    public static let deny = "deny"
    public static let error = "error"
    public static let predictionUnavailable = "prediction_unavailable"
    /// libsandbox doesn't recognize the operation name (sandbox_check
    /// returned rc=-1 + errno=EINVAL). Most commonly a caller passing
    /// the unstar'd form of an SBPL family operation
    /// (e.g. "process-exec" instead of the canonical "process-exec*").
    /// Surfaced as a distinct outcome so consumers can treat it as a
    /// per-step skip rather than a runtime failure — parallel to how
    /// unsupported attempt kinds are handled. `error` is always
    /// populated with the rejected operation name + the wildcard-form
    /// hint. `drift` is null for these steps because there's no
    /// allow/deny verdict to compare against.
    public static let unsupportedOperation = "unsupported_operation"
}

// BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
/// Wire contract versions. Edit docs/contract.json and regenerate; never edit here.
public enum PWContract {
    public static let requestSchema: Int = 1
    public static let responseSchema: Int = 10
}
// END GENERATED CONTRACT VERSIONS

public struct PWRunnerRunSpec: Codable {
    // Version meanings: docs/CONTRACT.md, "Reading older replies".
    public var schema_version: Int
    public var specimen_id: String
    public var run_kind: String?
    public var policy: PWRunnerPolicySpec
    public var probe_plan: [PWRunnerProbeStep]
    public var _test_overrides: PWRunnerTestOverrides?

    public init(
        schema_version: Int = PWContract.requestSchema,
        specimen_id: String,
        run_kind: String? = nil,
        policy: PWRunnerPolicySpec,
        probe_plan: [PWRunnerProbeStep],
        _test_overrides: PWRunnerTestOverrides? = nil
    ) {
        self.schema_version = schema_version
        self.specimen_id = specimen_id
        self.run_kind = run_kind
        self.policy = policy
        self.probe_plan = probe_plan
        self._test_overrides = _test_overrides
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
// | `libsandbox_path`           | `SandboxLib.load(path:)` via PWRunnerService.swift (host-     | `libsandbox_unavailable`    |
// |                             | side pre-spawn check)                                         |                             |
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
//
// See runner/AGENTS.md → "Testing `normalized_outcome` failure paths via
// `_test_overrides`" for the full contract, the four-assertion test
// recipe, and the rules for adding a new key.
public struct PWRunnerTestOverrides: Codable {
    public var libsandbox_path: String?
    public var worker_executable_path: String?
    public var worker_timeout_ms: Int?
    public var validator_executable_path: String?
    public var validator_io_timeout_ms: Int?
    public var worker_post_apply_hang_ms: Int?
    public var worker_post_apply_kill_signal: Int?
    public var worker_pre_ready_hang_ms: Int?

    public init(
        libsandbox_path: String? = nil,
        worker_executable_path: String? = nil,
        worker_timeout_ms: Int? = nil,
        validator_executable_path: String? = nil,
        validator_io_timeout_ms: Int? = nil,
        worker_post_apply_hang_ms: Int? = nil,
        worker_post_apply_kill_signal: Int? = nil,
        worker_pre_ready_hang_ms: Int? = nil
    ) {
        self.libsandbox_path = libsandbox_path
        self.worker_executable_path = worker_executable_path
        self.worker_timeout_ms = worker_timeout_ms
        self.validator_executable_path = validator_executable_path
        self.validator_io_timeout_ms = validator_io_timeout_ms
        self.worker_post_apply_hang_ms = worker_post_apply_hang_ms
        self.worker_post_apply_kill_signal = worker_post_apply_kill_signal
        self.worker_pre_ready_hang_ms = worker_pre_ready_hang_ms
    }
}

/// Versioned optional receipt for the exact compiler result supplied to apply.
/// `captured` requires a complete, checksum-verified worker capture and successful
/// application/process completion. This is not a readback of kernel state.
public struct AppliedProfileCapture: Codable {
    public var schema_version: Int = 1
    public var status: String
    public var reason: String?
    public var worker_pid: Int
    public var request_nonce: String?
    public var profile_type: Int?
    public var bytecode_length: Int?
    public var bytecode_sha256: String?
    public var bytecode_b64: String?
    public var source_sha256: String?
    public var source_length: Int?
    public var params_sha256: String?
    public var parameter_count: Int?
}

public struct PWRunnerPolicySpec: Codable {
    // Policy format, e.g. PWRunnerWire.policyFormatSbpl.
    public var format: String
    public var sbpl_source: String?
    public var params: [String: String]?
    /// Opt into sensitive worker-side bytecode/input identity capture.
    public var capture_applied_profile: Bool?
    /// Fresh 128-bit lowercase hex identity, echoed by the worker capture.
    public var capture_nonce: String?
    // Named augments the caller opts into (e.g. "exec_baseline"). The
    // controller resolves each name to a file under
    // Contents/Resources/Augments/<name>.sb, appends the contents to
    // sbpl_source before the runner compiles, and strips this field from the
    // request forwarded to the runner. The runner is augment-agnostic;
    // this field exists on the wire so callers can author their request
    // without controller-private knowledge.
    public var augments: [String]?

    public init(
        format: String,
        sbpl_source: String? = nil,
        params: [String: String]? = nil,
        augments: [String]? = nil,
        capture_applied_profile: Bool? = nil,
        capture_nonce: String? = nil
    ) {
        self.format = format
        self.sbpl_source = sbpl_source
        self.params = params
        self.augments = augments
        self.capture_applied_profile = capture_applied_profile
        self.capture_nonce = capture_nonce
    }
}

public struct PWRunnerSandboxCheck: Codable {
    public var operation: String
    public var filter: PWRunnerSandboxFilter

    public init(operation: String, filter: PWRunnerSandboxFilter) {
        self.operation = operation
        self.filter = filter
    }
}

public struct PWRunnerSandboxFilter: Codable {
    // "none" | "path" | "global_name" | "local_name"
    public var kind: String
    public var value: String?

    public init(kind: String, value: String? = nil) {
        self.kind = kind
        self.value = value
    }
}

public struct PWRunnerAttempt: Codable {
    // "file" | "mach_lookup" | "sysctl" | "exec"
    public var kind: String
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
    public var action: String
    public var target: String
    public var args: [String]?

    public init(kind: String, action: String, target: String, args: [String]? = nil) {
        self.kind = kind
        self.action = action
        self.target = target
        self.args = args
    }
}

public struct PWRunnerProbeStep: Codable {
    public var step_id: String
    public var sandbox_check: PWRunnerSandboxCheck
    public var attempt: PWRunnerAttempt

    public init(step_id: String, sandbox_check: PWRunnerSandboxCheck, attempt: PWRunnerAttempt) {
        self.step_id = step_id
        self.sandbox_check = sandbox_check
        self.attempt = attempt
    }
}

// Path forms observed by the unsandboxed runner host after orchestration.
// They are not historical validator/worker resolutions or comparison inputs.
// Legacy decoding preserves absent provenance as unknown.
//
// Wire form: `input` plus the two forms named in `formNames`. A form with the
// same UTF-8 bytes as `input` is listed in `same_as_input` and its key omitted; a form
// that differs is a string; a form the host could not derive is an explicit
// null. Each form is therefore in exactly one of those three states. Replies
// before response 9 carried every form as a string or null, never listed
// equality, and also carried a `data_volume_form` heuristic that duplicated
// `firmlink_resolved`; decoding reads either shape into the same values.
public struct PWRunnerPathDiagnostics: Codable {
    public static let formNames = ["realpath_resolved", "firmlink_resolved"]

    public var observer: String?
    public var phase: String?
    public var input: String
    public var realpath_resolved: String?
    public var firmlink_resolved: String?

    // A legacy omission is unknown, not an observed resolution failure. Keep
    // the old shape when re-encoding it instead of inventing explicit nulls.
    fileprivate var legacyAbsentForms: Set<String>? = nil

    public init(
        input: String,
        realpath_resolved: String? = nil,
        firmlink_resolved: String? = nil,
        observer: String? = nil,
        phase: String? = nil
    ) {
        self.observer = observer
        self.phase = phase
        self.input = input
        self.realpath_resolved = realpath_resolved
        self.firmlink_resolved = firmlink_resolved
    }

    enum CodingKeys: String, CodingKey {
        case observer, phase
        case input
        case same_as_input
        case realpath_resolved
        case firmlink_resolved
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(observer, forKey: .observer)
        try container.encodeIfPresent(phase, forKey: .phase)
        try container.encode(input, forKey: .input)
        var sameAsInput: [String] = []
        let forms: [(String, CodingKeys, String?)] = [
            ("realpath_resolved", .realpath_resolved, realpath_resolved),
            ("firmlink_resolved", .firmlink_resolved, firmlink_resolved),
        ]
        for (name, key, value) in forms {
            if let absent = legacyAbsentForms {
                if let value {
                    try container.encode(value, forKey: key)
                } else if !absent.contains(name) {
                    try container.encodeNil(forKey: key)
                }
            } else if let value, value.utf8.elementsEqual(input.utf8) {
                sameAsInput.append(name)
            } else if let value {
                try container.encode(value, forKey: key)
            } else {
                // Explicit null: the host computed this form and got nothing.
                try container.encodeNil(forKey: key)
            }
        }
        if legacyAbsentForms == nil {
            try container.encode(sameAsInput, forKey: .same_as_input)
        }
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        observer = try container.decodeIfPresent(String.self, forKey: .observer)
        phase = try container.decodeIfPresent(String.self, forKey: .phase)
        input = try container.decode(String.self, forKey: .input)
        let compact = container.contains(.same_as_input)
        let sameAsInput = compact ? try container.decode([String].self, forKey: .same_as_input) : []
        if Set(sameAsInput).count != sameAsInput.count || !Set(sameAsInput).isSubset(of: Set(Self.formNames)) {
            throw DecodingError.dataCorruptedError(forKey: .same_as_input, in: container,
                debugDescription: "same_as_input must contain unique supported form names")
        }
        let submitted = input
        func form(_ key: CodingKeys) throws -> String? {
            let listed = sameAsInput.contains(key.rawValue)
            if compact && listed == container.contains(key) {
                throw DecodingError.dataCorruptedError(forKey: key, in: container,
                    debugDescription: "form must be either listed in same_as_input or present, exclusively")
            }
            if listed { return submitted }
            let value = try container.decodeIfPresent(String.self, forKey: key)
            if compact, let value, value.utf8.elementsEqual(submitted.utf8) {
                throw DecodingError.dataCorruptedError(forKey: key, in: container,
                    debugDescription: "a form with identical UTF-8 bytes must be listed in same_as_input")
            }
            return value
        }
        realpath_resolved = try form(.realpath_resolved)
        firmlink_resolved = try form(.firmlink_resolved)
        if !compact {
            legacyAbsentForms = Set([CodingKeys.realpath_resolved, .firmlink_resolved]
                .filter { !container.contains($0) }.map { $0.rawValue })
        }
    }
}

public struct PWRunnerSandboxCheckResult: Codable {
    /// Additive provenance; absence in stored replies means unknown. See the
    /// "Worker evidence contract" in tests/FAILURE-PROPAGATION-CONTRACT.md
    /// for native returns versus PW status and missing reasons.
    public var result_source: String? = nil
    public var native_rc: Int? = nil
    public var missing_reason: String? = nil
    public var rc: Int
    public var outcome: String
    public var pid: Int?
    public var operation: String
    public var scope: String
    public var filter_kind: String
    public var filter_value: String?
    public var filter_type_id: Int?
    public var errno: Int?
    public var error: String?
    public var path_diagnostics: PWRunnerPathDiagnostics?

    public init(
        rc: Int,
        outcome: String,
        pid: Int?,
        operation: String,
        scope: String,
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
        self.scope = scope
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
        case scope
        case filter_kind
        case filter_value
        case filter_type_id
        case errno
        case error
        case path_diagnostics
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(result_source, forKey: .result_source)
        if result_source != nil { try container.encode(native_rc, forKey: .native_rc) }
        try container.encodeIfPresent(missing_reason, forKey: .missing_reason)
        try container.encode(rc, forKey: .rc)
        try container.encode(outcome, forKey: .outcome)
        try container.encode(pid, forKey: .pid)
        try container.encode(operation, forKey: .operation)
        try container.encode(scope, forKey: .scope)
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

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        result_source = try container.decodeIfPresent(String.self, forKey: .result_source)
        native_rc = try container.decodeIfPresent(Int.self, forKey: .native_rc)
        missing_reason = try container.decodeIfPresent(String.self, forKey: .missing_reason)
        rc = try container.decode(Int.self, forKey: .rc)
        outcome = try container.decode(String.self, forKey: .outcome)
        pid = try container.decodeIfPresent(Int.self, forKey: .pid)
        operation = try container.decodeIfPresent(String.self, forKey: .operation) ?? ""
        scope = try container.decode(String.self, forKey: .scope)
        filter_kind = try container.decode(String.self, forKey: .filter_kind)
        filter_value = try container.decodeIfPresent(String.self, forKey: .filter_value)
        filter_type_id = try container.decodeIfPresent(Int.self, forKey: .filter_type_id)
        errno = try container.decodeIfPresent(Int.self, forKey: .errno)
        error = try container.decodeIfPresent(String.self, forKey: .error)
        path_diagnostics = try container.decodeIfPresent(PWRunnerPathDiagnostics.self, forKey: .path_diagnostics)
    }
}

public struct PWRunnerAttemptResult: Codable {
    /// Additive provenance; absence in stored replies means unknown. See the
    /// "Worker evidence contract" in tests/FAILURE-PROPAGATION-CONTRACT.md
    /// for native returns versus PW status and missing reasons.
    /// Submitted intent, not proof that the named native operation ran.
    public var requested_kind: String? = nil
    public var requested_action: String? = nil
    public var result_source: String? = nil
    public var native_rc: Int? = nil
    public var missing_reason: String? = nil
    /// Projection of this step's disposition claims; absent in replies before
    /// the record. `not_run_worker_died`/`slot_incomplete` stay as they are.
    public var lifecycle: PWAttemptLifecycle? = nil
    public var rc: Int
    public var exit_code: Int
    public var errno: Int?
    public var syscall_errno: Int?
    public var outcome: String
    public var error: String?
    public var requested_path: String?
    public var normalized_path: String?
    public var observed_path: String?

    /// Exec-attempt outputs. All five are nil for non-exec attempts and
    /// are emitted as explicit JSON null (when populated) or omitted
    /// entirely (when nil) so a sysctl/file/mach result envelope does
    /// not grow five new null fields it has no use for.
    ///
    /// `child_pid > 0` means `posix_spawn` succeeded and a child was
    /// reaped (even if it exited non-zero). `child_pid == 0` means
    /// spawn failed before producing a child (sandbox blocked spawn,
    /// target missing, etc.) — `errno` carries the spawn errno in
    /// that case. The orchestrator's drift classifier reads
    /// `child_pid` to distinguish spawn failure from a child non-zero
    /// exit (non-policy failure). EPERM/EACCES without a child remain
    /// ambiguous: execute permissions can also prevent spawning.
    public var child_pid: Int?
    public var child_exit_code: Int?
    public var child_term_signal: Int?
    public var stdout: String?
    public var stderr: String?

    public init(
        rc: Int,
        errno: Int? = nil,
        outcome: String,
        error: String? = nil,
        requested_path: String? = nil,
        normalized_path: String? = nil,
        observed_path: String? = nil,
        child_pid: Int? = nil,
        child_exit_code: Int? = nil,
        child_term_signal: Int? = nil,
        stdout: String? = nil,
        stderr: String? = nil
    ) {
        self.rc = rc
        self.exit_code = rc
        self.errno = errno
        self.syscall_errno = errno
        self.outcome = outcome
        self.error = error
        self.requested_path = requested_path
        self.normalized_path = normalized_path
        self.observed_path = observed_path
        self.child_pid = child_pid
        self.child_exit_code = child_exit_code
        self.child_term_signal = child_term_signal
        self.stdout = stdout
        self.stderr = stderr
    }

    enum CodingKeys: String, CodingKey {
        case requested_kind, requested_action
        case result_source, native_rc, missing_reason, lifecycle
        case rc
        case exit_code
        case errno
        case syscall_errno
        case outcome
        case error
        case requested_path
        case normalized_path
        case observed_path
        case child_pid
        case child_exit_code
        case child_term_signal
        case stdout
        case stderr
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(requested_kind, forKey: .requested_kind)
        try container.encodeIfPresent(requested_action, forKey: .requested_action)
        try container.encodeIfPresent(result_source, forKey: .result_source)
        if result_source != nil { try container.encode(native_rc, forKey: .native_rc) }
        try container.encodeIfPresent(missing_reason, forKey: .missing_reason)
        try container.encodeIfPresent(lifecycle, forKey: .lifecycle)
        try container.encode(rc, forKey: .rc)
        try container.encode(exit_code, forKey: .exit_code)
        if let errno {
            try container.encode(errno, forKey: .errno)
        } else {
            try container.encodeNil(forKey: .errno)
        }
        if let syscall_errno {
            try container.encode(syscall_errno, forKey: .syscall_errno)
        } else {
            try container.encodeNil(forKey: .syscall_errno)
        }
        try container.encode(outcome, forKey: .outcome)
        try container.encodeIfPresent(error, forKey: .error)
        if let requested_path {
            try container.encode(requested_path, forKey: .requested_path)
        } else {
            try container.encodeNil(forKey: .requested_path)
        }
        if let normalized_path {
            try container.encode(normalized_path, forKey: .normalized_path)
        } else {
            try container.encodeNil(forKey: .normalized_path)
        }
        if let observed_path {
            try container.encode(observed_path, forKey: .observed_path)
        } else {
            try container.encodeNil(forKey: .observed_path)
        }
        // Exec output fields: emit when non-nil (as explicit JSON
        // value), omit the key entirely when nil. A non-exec
        // attempt's envelope therefore does not grow five new null
        // keys; an exec attempt's envelope always carries all five
        // (the orchestrator populates them from the shm slot,
        // including child_pid == 0 / child_exit_code == -1 when
        // spawn failed).
        try container.encodeIfPresent(child_pid, forKey: .child_pid)
        try container.encodeIfPresent(child_exit_code, forKey: .child_exit_code)
        try container.encodeIfPresent(child_term_signal, forKey: .child_term_signal)
        try container.encodeIfPresent(stdout, forKey: .stdout)
        try container.encodeIfPresent(stderr, forKey: .stderr)
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        requested_kind = try container.decodeIfPresent(String.self, forKey: .requested_kind)
        requested_action = try container.decodeIfPresent(String.self, forKey: .requested_action)
        result_source = try container.decodeIfPresent(String.self, forKey: .result_source)
        native_rc = try container.decodeIfPresent(Int.self, forKey: .native_rc)
        missing_reason = try container.decodeIfPresent(String.self, forKey: .missing_reason)
        lifecycle = try container.decodeIfPresent(PWAttemptLifecycle.self, forKey: .lifecycle)
        rc = try container.decode(Int.self, forKey: .rc)
        exit_code = try container.decodeIfPresent(Int.self, forKey: .exit_code) ?? rc
        errno = try container.decodeIfPresent(Int.self, forKey: .errno)
        syscall_errno = try container.decodeIfPresent(Int.self, forKey: .syscall_errno)
        outcome = try container.decode(String.self, forKey: .outcome)
        error = try container.decodeIfPresent(String.self, forKey: .error)
        requested_path = try container.decodeIfPresent(String.self, forKey: .requested_path)
        normalized_path = try container.decodeIfPresent(String.self, forKey: .normalized_path)
        observed_path = try container.decodeIfPresent(String.self, forKey: .observed_path)
        child_pid = try container.decodeIfPresent(Int.self, forKey: .child_pid)
        child_exit_code = try container.decodeIfPresent(Int.self, forKey: .child_exit_code)
        child_term_signal = try container.decodeIfPresent(Int.self, forKey: .child_term_signal)
        stdout = try container.decodeIfPresent(String.self, forKey: .stdout)
        stderr = try container.decodeIfPresent(String.self, forKey: .stderr)
    }
}

public struct PWRunnerSignalResult: Codable {
    public var signal: String
    public var count_before: Int
    public var count_after: Int
    public var delta: Int

    public init(signal: String, count_before: Int, count_after: Int) {
        self.signal = signal
        self.count_before = count_before
        self.count_after = count_after
        self.delta = max(0, count_after - count_before)
    }
}

/// A bounded comparison of recorded outcomes, with independently reported limits.
/// Unknown future strings remain decodable; no field implies synchronized state.
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

public struct PWRunnerComparison: Codable {
    public var scope: String
    public var prediction: String
    public var observation: String
    public var observation_basis: String
    public var operation_relation: String
    public var target_relation: String
    public var conclusion: String
    public var limitations: [String]
    /// Absent in legacy replies; every response-8 producer supplies a value.
    public var order: String? = nil

    public var drift: Bool? {
        switch conclusion {
        case "agreement": return false
        case "disagreement": return true
        default: return nil
        }
    }
}

public struct PWRunnerStepResult: Codable {
    public var step_id: String
    public var sandbox_check: PWRunnerSandboxCheckResult
    public var attempt: PWRunnerAttemptResult
    /// Unobserved by the C worker: new responses encode explicit null.
    /// Legacy objects remain decodable; their counts are not new observations.
    public var deny_signal: PWRunnerSignalResult?

    /// Current evidence cannot establish state stability/runtime identity,
    /// so no response-8 producer supplies disagreement. Agreement is limited to supported observations
    /// within matched submitted scope, without an unordered target mutation.
    /// Directional consistency and unavailable comparisons project to null.
    /// Older decoded values retain their original version's meaning.
    public var comparison: PWRunnerComparison?
    public var drift: Bool?

    public init(
        step_id: String,
        sandbox_check: PWRunnerSandboxCheckResult,
        attempt: PWRunnerAttemptResult,
        deny_signal: PWRunnerSignalResult? = nil,
        drift: Bool? = nil,
        comparison: PWRunnerComparison? = nil
    ) {
        self.step_id = step_id
        self.sandbox_check = sandbox_check
        self.attempt = attempt
        self.deny_signal = deny_signal
        self.drift = drift
        self.comparison = comparison
    }

    enum CodingKeys: String, CodingKey {
        case step_id
        case sandbox_check
        case attempt
        case deny_signal
        case drift
        case comparison
    }

    // Custom encode so `drift` is emitted as explicit JSON null when
    // nil. Consumers at schema_version >= 4 can rely on the key being
    // present (bool or null); v3 producers never write the key at all.
    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(comparison, forKey: .comparison)
        try container.encode(step_id, forKey: .step_id)
        try container.encode(sandbox_check, forKey: .sandbox_check)
        try container.encode(attempt, forKey: .attempt)
        if let deny_signal {
            try container.encode(deny_signal, forKey: .deny_signal)
        } else {
            try container.encodeNil(forKey: .deny_signal)
        }
        if let drift {
            try container.encode(drift, forKey: .drift)
        } else {
            try container.encodeNil(forKey: .drift)
        }
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        step_id = try container.decode(String.self, forKey: .step_id)
        sandbox_check = try container.decode(PWRunnerSandboxCheckResult.self, forKey: .sandbox_check)
        attempt = try container.decode(PWRunnerAttemptResult.self, forKey: .attempt)
        deny_signal = try container.decodeIfPresent(PWRunnerSignalResult.self, forKey: .deny_signal)
        // decodeIfPresent handles both "key absent" (v3 producer) and
        // "key present but null" (v4 producer with no comparison) →
        // both land as Bool? = nil on the reader side. That's the
        // intended behaviour.
        drift = try container.decodeIfPresent(Bool.self, forKey: .drift)
        comparison = try container.decodeIfPresent(PWRunnerComparison.self, forKey: .comparison)
    }
}

/// Host observation of one kill(2) request, not evidence of its delivery or cause.
/// JSON: runner_subprocess.termination_request.{signal,rc,errno}. All numbers
/// are signed 32-bit syscall values encoded as JSON integers (no units).
/// errno is captured immediately only when rc == -1; otherwise it is absent/null.
/// An absent/null request means no request when the new host fields are present;
/// old stored replies have no observation. Structurally valid values are decoded
/// without a signal/errno allowlist. The client/controller forward this object.
public struct PWRunnerTerminationRequest: Codable {
    public let signal: Int32
    public let rc: Int32
    public let errno: Int32?

    public init(signal: Int32, rc: Int32, errno: Int32?) {
        self.signal = signal
        self.rc = rc
        self.errno = errno
    }
}

/// One host-observed failed waitpid(2) call, including recovered interruptions.
/// JSON: runner_subprocess.wait_errors[].{phase,rc,errno}. phase is a string
/// (poll, exit_grace, after_termination); rc/errno are signed 32-bit integers.
/// Only rc == -1 produces a record, with errno captured before another call.
/// Unknown phase/errno values remain transportable. Empty array means no errors
/// observed; absent/null array means unavailable (e.g. an older stored reply).
public struct PWRunnerWaitError: Codable {
    public let phase: String
    public let rc: Int32
    public let errno: Int32

    public init(phase: String, rc: Int32, errno: Int32) {
        self.phase = phase
        self.rc = rc
        self.errno = errno
    }
}

/// Host-observed UTF-8 policy transfer failure; counts are writes, not child reads.
/// See tests/FAILURE-PROPAGATION-CONTRACT.md for field validity and JSON semantics.
public struct PWWorkerPolicyTransferError: Codable {
    public var errno: Int32
    public var bytes_written: Int
    public var bytes_expected: Int
}
/// ABI 7 worker publications. Numeric codes are open, never Codable enums.
public struct PWWorkerProgress: Codable {
    public var raw: UInt32
    public var operation: UInt32
    public var phase: UInt32
    public var index: UInt32?
}
public struct PWWorkerFailure: Codable {
    public var operation: UInt32
    public var code: UInt32
    public var native_kind: UInt32
    public var native_result: Int32?
    public var errno: Int32?
    public var index: UInt32?
    public var detail: UInt32
}
public struct PWWorkerReadiness: Codable {
    public var rc: Int32
    public var errno: Int32?
}
public struct PWWorkerDiagnostic: Codable {
    public var state: UInt32
    public var status: String
    public var length: UInt32?
    public var text: String?
}
public struct PWWorkerEvidence: Codable {
    /// Host-selected layout, not proof that a child reached ABI validation.
    public var abi_version: UInt32
    public var progress: PWWorkerProgress?
    public var failure_publication: UInt32
    public var failure_state: String
    public var failure: PWWorkerFailure?
    public var readiness: PWWorkerReadiness?
    public var diagnostic: PWWorkerDiagnostic
}

/// Authoritative worker process metadata, produced by the unsandboxed host.
/// Lifecycle observations are host-owned; worker_evidence uses worker ABI 7.
/// All live CWorkerOutput paths populate the optional observation fields below;
/// optionality preserves decoding of older stored replies as unknown, not false.
/// Policy-write failures retain partial child observations.
public struct PWRunnerOrdering: Codable {
    public var collection_closed_before_proceed: Bool
    public var proceed_set: Bool
    public var proceed_observed: Bool
    public var validator_disposition: String
    /// Ownership through acknowledgement, not the eventual cleanup outcome.
    public var worker_lifetime_established: Bool
    public var protocol_violations: [String]

    var chainEstablished: Bool {
        collection_closed_before_proceed && proceed_set && proceed_observed
            && worker_lifetime_established && protocol_violations.isEmpty
    }
}

public struct PWRunnerSubprocess: Codable {
    public var ordering: PWRunnerOrdering? = nil
    public var pid: Int
    /// JSON integers, meaningful only after waitpid returned this child's PID.
    /// Both may be absent/null when status was not obtained; zero is a real exit.
    public var term_signal: Int?
    public var exit_code: Int?
    public var partial_steps: Bool
    /// Worker publication snapshot; absent in legacy replies and before spawn.
    public var worker_evidence: PWWorkerEvidence? = nil
    /// Host transfer observation independent of any child publication.
    public var policy_transfer_error: PWWorkerPolicyTransferError? = nil
    /// Host read of the ready byte; false does not prove compilation failed.
    public var ready_byte_received: Bool?
    /// Final acquire observation of done after cleanup, not successful application.
    /// poll_stop_reason separately retains the reason the polling phase ended.
    public var done_observed: Bool?
    /// Host string: done, child_reaped, sentinel_deadline, wait_error, or policy_write_error.
    /// Identifies why polling stopped; later cleanup must not rewrite it.
    /// Only sentinel_deadline establishes exhaustion of the polling budget.
    /// Unknown strings survive decoding; they do not imply a known condition.
    public var poll_stop_reason: String?
    /// Host performed the release-store of exit_requested; not worker receipt.
    public var exit_requested: Bool?
    public var termination_request: PWRunnerTerminationRequest?
    /// True only when waitpid actually returned this PID. False is explicitly
    /// unconfirmed disposition, distinct from absent/null legacy observation.
    public var reaped: Bool?
    public var wait_errors: [PWRunnerWaitError]?
    /// Host facts recorded where the host acts (tests/FAILURE-PROPAGATION-CONTRACT.md,
    /// "Worker disposition record"): why exit was requested, how the exit-grace
    /// wait ended, and whether the final reads followed a confirmed reap. Absent
    /// in replies before the record; absence is unreported, not observed false.
    public var cleanup_trigger: String? = nil
    public var grace_end: String? = nil
    public var collection_basis: String? = nil
    /// The canonical lifecycle account, resolved once by the host. Mandatory
    /// whenever this object is present from the response that introduced it.
    public var disposition: PWDispositionRecord? = nil

    public init(
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
public enum PWDisposition {
    public static let claimStates = ["supported", "unresolved", "conflicting", "inapplicable"]
    public static let runQuestions = ["final_status", "stop_reason", "cleanup_trigger", "grace_end",
                                      "kill_request_and_result", "collection_basis", "progress_association"]
    public static let stepQuestions = ["step_boundary_reached", "step_result_published",
                                       "step_requested_operation_applicability"]
    public static let cleanupTriggers = ["deadline_expiry", "completion", "child_reaped", "poll_wait_error",
                                         "policy_transfer_error"]
    public static let graceEnds = ["not_entered", "reaped_during_grace", "exhausted", "wait_error"]
    public static let collectionBases = ["after_confirmed_reap", "execution_may_continue", "unavailable"]
    public static let triggerForStop: [String: String] = [
        "sentinel_deadline": "deadline_expiry", "done": "completion", "child_reaped": "child_reaped",
        "wait_error": "poll_wait_error", "policy_write_error": "policy_transfer_error"]
    public static let slotStates = ["completed", "incomplete", "absent"]
    public static let attemptSupport = ["supported", "unsupported"]
    public static let summaries = ["completed", "started_without_result", "not_reached", "unsupported",
                                   "unresolved", "conflicting"]
    public static let limitationForSummary: [String: String] = [
        "started_without_result": "attempt:started_without_result", "not_reached": "attempt:not_reached",
        "unsupported": "attempt:unsupported", "unresolved": "attempt:lifecycle_unresolved",
        "conflicting": "attempt:lifecycle_conflicting"]
    public static let causeForTrigger: [String: String] = [
        "deadline_expiry": "host_sentinel_deadline", "completion": "host_exit_grace_exhausted",
        "poll_wait_error": "host_cleanup_after_wait_error", "policy_transfer_error": "host_cleanup_after_transfer_error"]
    public static let notRecorded = "not_recorded"
    /// Temporal order of worker operations (pw_probe_runner_abi.h): proceed (11)
    /// precedes the indexed attempts (9); completion (10) follows them.
    public static let protocolOrder: [UInt32] = [1, 2, 3, 4, 5, 6, 7, 8, 11, 9, 10]
    public static let runReferences = ["reaped", "exit_code", "term_signal", "poll_stop_reason", "exit_requested",
                                       "termination_request", "wait_errors", "cleanup_trigger", "grace_end",
                                       "collection_basis", "done_observed", "progress", "worker_failure", "plan"]
    public static let stepReferences = ["slot", "attempt_support"]
}

extension PWRunnerTerminationRequest: Equatable {}

/// A claim value: an exit code, signal or index, or the termination request.
public enum PWDispositionValue: Codable, Equatable {
    case integer(Int)
    case request(PWRunnerTerminationRequest)
    public init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if let integer = try? c.decode(Int.self) { self = .integer(integer); return }
        self = .request(try c.decode(PWRunnerTerminationRequest.self))
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer()
        switch self {
        case .integer(let integer): try c.encode(integer)
        case .request(let request): try c.encode(request)
        }
    }
}

public struct PWDispositionClaim: Codable, Equatable {
    public var state: String
    public var answer: String? = nil
    public var value: PWDispositionValue? = nil
    public var reason: String? = nil
    public var issue: Int? = nil
    public var basis: [String]? = nil
}

public struct PWDispositionIssue: Codable, Equatable {
    public var kind: String
    public var rule: String
    public var question: String
    public var step_index: Int? = nil
    public var observations: [String]
    public var detail: String
}

public struct PWDispositionStep: Codable, Equatable {
    public var index: Int
    public var step_id: String
    public var slot: String
    public var attempt_support: String
    public var questions: [String: PWDispositionClaim]
}

public struct PWDispositionRecord: Codable, Equatable {
    public var questions: [String: PWDispositionClaim]
    public var steps: [PWDispositionStep]
    public var issues: [PWDispositionIssue]
}

public struct PWAttemptLifecycle: Codable, Equatable {
    public var summary: String
    public var boundary: PWDispositionClaim
    public var result: PWDispositionClaim
}

/// Integrity of an assembled record against the raw facts it cites. The
/// encoder rejects a record that fails this; the degraded reply retains it
/// unchecked so the conflict being reported is never lost. A record that
/// reports an observed conflict through `issues` passes.
func dispositionIntegrityProblems(_ record: PWDispositionRecord, subprocess sub: PWRunnerSubprocess,
                                  stepCount: Int) -> [String] {
    var problems: [String] = []
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
            for token in basis where !PWDisposition.runReferences.contains(token) {
                problems.append("\(name): unknown reference \(token)")
            }
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
            if sub.reaped != true || sub.term_signal == nil || final.value != sub.term_signal.map { .integer($0) } {
                problems.append("final_status: signal claim contradicts reaped/term_signal")
            }
        case ("supported", "exit_code"?):
            if sub.reaped != true || sub.exit_code == nil || final.value != sub.exit_code.map { .integer($0) } {
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
        if kill.answer == "requested", sub.termination_request == nil {
            problems.append("kill_request_and_result: request claimed without termination_request")
        }
        if kill.answer == "none", sub.termination_request != nil {
            problems.append("kill_request_and_result: no-request claim beside a termination_request")
        }
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
            if claim.state == "supported" {
                guard let basis = claim.basis, !basis.isEmpty, claim.answer != nil else {
                    problems.append("step \(position) \(name): supported claim without answer or basis"); continue
                }
                for token in basis where !(PWDisposition.runReferences + PWDisposition.stepReferences).contains(token) {
                    problems.append("step \(position) \(name): unknown reference \(token)")
                }
            }
            if claim.state == "conflicting" {
                guard let issue = claim.issue, record.issues.indices.contains(issue),
                      record.issues[issue].question == name, record.issues[issue].step_index == position else {
                    problems.append("step \(position) \(name): conflicting claim without a matching issue"); continue
                }
            }
        }
        if let result = step.questions["step_result_published"], result.state == "supported" {
            if result.answer == "published", step.slot != "completed" {
                problems.append("step \(position): published claim on a slot that is not completed")
            }
            if result.answer == "unpublished", step.slot != "incomplete" || sub.collection_basis != "after_confirmed_reap" {
                problems.append("step \(position): unpublished claim needs an incomplete slot under terminal collection")
            }
        }
        if let boundary = step.questions["step_boundary_reached"], boundary.state == "supported",
           boundary.answer == "not_reached", sub.collection_basis != "after_confirmed_reap" || step.slot == "completed" {
            problems.append("step \(position): not_reached claim needs terminal collection and no completed slot")
        }
    }
    return problems
}

public struct ValidatorVerdict: Codable {
    enum CodingKeys: String, CodingKey {
        case stepId = "step_id", operation, filterType = "filter_type"
        case filterTypeId = "filter_type_id", filterValue = "filter_value"
        case rc, errnoVal = "errno", outcome, error, rawLine = "raw_line"
    }
    public func encode(to encoder: Encoder) throws {
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
    public var stepId: String?
    public var operation: String?
    public var filterType: String?
    public var filterTypeId: Int?
    public var filterValue: String?
    public var rc: Int?
    public var errnoVal: Int?
    public var outcome: String             // "allow"|"deny"|"error"|"parse_error"|"bad_filter"
    public var error: String?
    public var rawLine: String             // for debugging
}

/// Receiver-owned rejected frame context. The prefix is bytes, not repaired
/// JSON. Offsets/lengths are exact received byte counts; at most 256 context
/// bytes are retained. Unknown diagnostic outcome names are not decode faults.
public struct PWValidatorDecodeFault: Codable {
    public var origin: String = "runner_host"
    public var kind: String // utf8, json, structure
    public var message: String
    public var byte_offset: Int
    public var frame_bytes: Int
    public var retained_bytes: Int
    public var context_b64: String
    public var context_truncated: Bool
}

public struct PWValidatorAssociationIssue: Codable {
    public var origin: String = "runner_host"
    public var kind: String // missing_id, duplicate_id, unexpected_id, unassociated
    public var step_id: String? = nil
    public var count: Int
}

/// Validator child observations. Legacy missing host fields remain unknown.
/// Only successful reaping supplies exit/signal. Records are accepted validator
/// evidence, independently retained even when association/transport/cleanup fails.
/// A null-ID record is never assigned an invented step identity.
public struct PWRunnerValidatorSubprocess: Codable {
    public var pid: Int
    public var term_signal: Int?
    public var exit_code: Int?
    public var reaped: Bool?
    public var termination_request: PWRunnerTerminationRequest?
    public var wait_errors: [PWRunnerWaitError]?
    public var read_error: String?
    public var stdout_collection_stop: String?
    public var stdout_bytes_received: Int?
    public var probe_bytes_written: Int?
    public var probe_bytes_expected: Int?
    public var io_error: String?
    public var decode_fault: PWValidatorDecodeFault?
    public var records: [ValidatorVerdict]?
    public var expected_step_ids: [String]?
    public var association_issues: [PWValidatorAssociationIssue]?

    public init(pid: Int, term_signal: Int? = nil, exit_code: Int? = nil) {
        self.pid = pid
        self.term_signal = term_signal
        self.exit_code = exit_code
    }
}

/// Host admission: no worker publication or child process is implied.
/// UTF-8 lengths are payload bytes excluding NUL; item counts use `items`.
public struct PWRunnerAdmissionFailure: Codable {
    public var origin: String = "runner_host"
    public var field: String
    public var actual: Int
    public var maximum: Int
    public var unit: String
    public var step_id: String?
    public var parameter_key: String?
    public var index: Int?
}

/// Host reply failure, separate from execution classification. Retained evidence
/// has no per-step comparison claims; original_* fields are diagnostic only.
public struct PWRunnerReportingFailure: Codable {
    public var origin: String = "runner_host"
    public var diagnostic: String
    public var original_rc: Int
    public var original_normalized_outcome: String
    public var original_error: String?
    public var evidence_retained: Bool
}

/// Host observation of a failed validator launch; no child PID is implied.
/// posix_spawn returns the error code directly, independently of ambient errno.
/// Keep unfamiliar codes intact; diagnostic is descriptive, not a classifier.
public struct PWRunnerSpawnFailure: Codable {
    public var origin: String = "runner_host"
    public var operation: String = "posix_spawn"
    public var executable_path: String
    public var return_code: Int32
    public var diagnostic: String
}

// Encoding is explicit to enforce response invariants. When adding a stored
// field, update CodingKeys and encode(to:), and populate the field-coverage
// round-trip fixture in ReplyFailureTests. Reflection stays in that test.
public struct PWRunnerRunResult: Codable {
    // Response wire version. What each older number lacked is tabulated in
    // docs/CONTRACT.md, "Reading older replies".
    public var schema_version: Int
    public var specimen_id: String
    public var run_kind: String?
    public var rc: Int
    public var normalized_outcome: String
    public var error: String?
    public var pid: Int
    public var bundle_id: String?
    public var policy_format: String
    public var policy_sha256: String?
    public var applied_profile: AppliedProfileCapture?
    public var sandboxed_after_apply: Bool?
    public var deny_signal_total: PWRunnerSignalResult?
    public var steps: [PWRunnerStepResult]
    public var runner_subprocess: PWRunnerSubprocess?
    public var admission_failure: PWRunnerAdmissionFailure?
    public var validator_subprocess: PWRunnerValidatorSubprocess?
    public var validator_spawn_failure: PWRunnerSpawnFailure?
    public var test_overrides: PWRunnerTestOverrides?
    public var reporting_failure: PWRunnerReportingFailure?

    public init(
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
        deny_signal_total: PWRunnerSignalResult? = nil,
        steps: [PWRunnerStepResult],
        runner_subprocess: PWRunnerSubprocess? = nil,
        validator_subprocess: PWRunnerValidatorSubprocess? = nil,
        test_overrides: PWRunnerTestOverrides? = nil,
        applied_profile: AppliedProfileCapture? = nil,
        admission_failure: PWRunnerAdmissionFailure? = nil,
        reporting_failure: PWRunnerReportingFailure? = nil,
        validator_spawn_failure: PWRunnerSpawnFailure? = nil
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
        self.applied_profile = applied_profile
        self.admission_failure = admission_failure
        self.sandboxed_after_apply = sandboxed_after_apply
        self.deny_signal_total = deny_signal_total
        self.steps = steps
        self.runner_subprocess = runner_subprocess
        self.validator_subprocess = validator_subprocess
        self.test_overrides = test_overrides
        self.reporting_failure = reporting_failure
        self.validator_spawn_failure = validator_spawn_failure
    }
    enum CodingKeys: String, CodingKey, CaseIterable {
        case schema_version, specimen_id, run_kind, rc, normalized_outcome, error, pid, bundle_id, policy_format, policy_sha256, applied_profile, sandboxed_after_apply, deny_signal_total, steps, runner_subprocess, admission_failure, validator_subprocess, validator_spawn_failure, test_overrides, reporting_failure
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        schema_version = try c.decode(Int.self, forKey: .schema_version)
        specimen_id = try c.decode(String.self, forKey: .specimen_id)
        run_kind = try c.decodeIfPresent(String.self, forKey: .run_kind)
        rc = try c.decode(Int.self, forKey: .rc)
        normalized_outcome = try c.decode(String.self, forKey: .normalized_outcome)
        error = try c.decodeIfPresent(String.self, forKey: .error)
        pid = try c.decode(Int.self, forKey: .pid)
        bundle_id = try c.decodeIfPresent(String.self, forKey: .bundle_id)
        policy_format = try c.decode(String.self, forKey: .policy_format)
        policy_sha256 = try c.decodeIfPresent(String.self, forKey: .policy_sha256)
        applied_profile = try c.decodeIfPresent(AppliedProfileCapture.self, forKey: .applied_profile)
        sandboxed_after_apply = try c.decodeIfPresent(Bool.self, forKey: .sandboxed_after_apply)
        deny_signal_total = try c.decodeIfPresent(PWRunnerSignalResult.self, forKey: .deny_signal_total)
        steps = try c.decode([PWRunnerStepResult].self, forKey: .steps)
        runner_subprocess = try c.decodeIfPresent(PWRunnerSubprocess.self, forKey: .runner_subprocess)
        admission_failure = try c.decodeIfPresent(PWRunnerAdmissionFailure.self, forKey: .admission_failure)
        validator_subprocess = try c.decodeIfPresent(PWRunnerValidatorSubprocess.self, forKey: .validator_subprocess)
        validator_spawn_failure = try c.decodeIfPresent(PWRunnerSpawnFailure.self, forKey: .validator_spawn_failure)
        test_overrides = try c.decodeIfPresent(PWRunnerTestOverrides.self, forKey: .test_overrides)
        reporting_failure = try c.decodeIfPresent(PWRunnerReportingFailure.self, forKey: .reporting_failure)
        if schema_version >= 9 && steps.contains(where: { $0.sandbox_check.path_diagnostics?.legacyAbsentForms != nil }) {
            throw DecodingError.dataCorruptedError(forKey: .steps, in: c,
                debugDescription: "response 9 path diagnostics require same_as_input")
        }
        if schema_version >= 10, reporting_failure == nil, let sub = runner_subprocess, sub.disposition == nil {
            throw DecodingError.dataCorruptedError(forKey: .runner_subprocess, in: c,
                debugDescription: "response 10 requires the worker disposition record")
        }
    }
    public func encode(to encoder: Encoder) throws {
        if schema_version >= 9 && steps.contains(where: { $0.sandbox_check.path_diagnostics?.legacyAbsentForms != nil }) {
            throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                debugDescription: "response 9 path diagnostics require same_as_input"))
        }
        // Reporting-failure diagnostics and ordered comparisons are required from
        // response 8 onward; a stored older reply re-encodes without them.
        if let failure = reporting_failure {
            guard schema_version >= 8, normalized_outcome == NormalizedOutcome.runnerReportingFailed,
                  rc == 1, error?.isEmpty == false, failure.origin == "runner_host",
                  !failure.diagnostic.isEmpty, !failure.original_normalized_outcome.isEmpty,
                  steps.allSatisfy({ $0.comparison == nil && $0.drift == nil }),
                  failure.evidence_retained || (steps.isEmpty && runner_subprocess == nil && validator_subprocess == nil && validator_spawn_failure == nil) else {
                throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                    debugDescription: "reporting failure requires a failed summary and no comparison claims"))
            }
        } else if schema_version >= 8 {
            if normalized_outcome == NormalizedOutcome.runnerReportingFailed {
                throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                    debugDescription: "runner_reporting_failed requires reporting_failure diagnostics"))
            }
            // The disposition record is mandatory beside a worker subprocess from
            // response 10 and must agree with the raw facts it cites. The degraded
            // reply above skips this so a reported conflict is never lost.
            if schema_version >= 10, let sub = runner_subprocess {
                guard let record = sub.disposition else {
                    throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                        debugDescription: "response 10 requires the worker disposition record"))
                }
                let problems = dispositionIntegrityProblems(record, subprocess: sub, stepCount: steps.count)
                if let first = problems.first {
                    throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                        debugDescription: "disposition record contradicts its basis: \(first)"))
                }
            }
            if runner_subprocess != nil && runner_subprocess?.ordering == nil {
                throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath,
                    debugDescription: "response 8 requires runner ordering"))
            }
            for step in steps {
                guard let comparison = step.comparison, let order = comparison.order,
                      comparison.conclusion != "disagreement", step.drift != true,
                      comparison.limitations.contains("query_attempt_order_unestablished") == (order != "query_first") else {
                    throw EncodingError.invalidValue(step, .init(codingPath: encoder.codingPath,
                        debugDescription: "response 8 requires order and cannot establish disagreement"))
                }
                if order == "query_first" && !eligibleOrderedStep(stepId: step.step_id, query: step.sandbox_check,
                    records: validator_subprocess?.records ?? [], ordering: runner_subprocess?.ordering,
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
        try c.encodeIfPresent(applied_profile, forKey: .applied_profile)
        try c.encodeIfPresent(sandboxed_after_apply, forKey: .sandboxed_after_apply)
        try c.encodeIfPresent(deny_signal_total, forKey: .deny_signal_total)
        try c.encode(steps, forKey: .steps)
        try c.encodeIfPresent(runner_subprocess, forKey: .runner_subprocess)
        try c.encodeIfPresent(admission_failure, forKey: .admission_failure)
        try c.encodeIfPresent(validator_subprocess, forKey: .validator_subprocess)
        try c.encodeIfPresent(validator_spawn_failure, forKey: .validator_spawn_failure)
        try c.encodeIfPresent(test_overrides, forKey: .test_overrides)
        try c.encodeIfPresent(reporting_failure, forKey: .reporting_failure)
    }

}

public func pwRunnerEncodeJSON<T: Encodable>(_ value: T) throws -> Data {
    let enc = JSONEncoder()
    enc.outputFormatting = [.sortedKeys]
    return try enc.encode(value)
}

public func pwRunnerDecodeJSON<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
    let dec = JSONDecoder()
    return try dec.decode(type, from: data)
}

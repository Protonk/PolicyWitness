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
// (tests/suites/runner_outcome_*/ or runner_sandbox_denied/) to assert
// against it. PolicyWitness.md should also list it in the "Run output"
// section so callers can recognize it.
public enum NormalizedOutcome {
    // ----- emitted by the C worker (pw-probe-runner), forwarded by host
    public static let ok = "ok"
    public static let badPolicy = "bad_policy"
    public static let sandboxApplyFailed = "sandbox_apply_failed"

    // ----- emitted by the host short-circuit (pre-spawn libsandbox check)
    public static let libsandboxUnavailable = "libsandbox_unavailable"

    // ----- emitted by the host short-circuit (PWRunnerService.swift)
    public static let badRequest = "bad_request"
    public static let alreadyRan = "already_ran"
    public static let workerSpawnFailed = "worker_spawn_failed"

    // ----- emitted by the host classifier (CWorker.swift sentinel
    // observation + CWorkerOrchestrator classification)
    public static let runnerSandboxDenied = "runner_sandbox_denied"
    public static let runnerTimeout = "runner_timeout"
    public static let runnerFailed = "runner_failed"

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
/// tests/INDEX.md's attempt-outcome matrix.
///
/// `not_run_worker_died` signals that the host saw a slot with
/// completed=0 because the C worker exited before reaching it.
/// Distinct from the per-attempt failure outcomes (`open_failed`,
/// etc.) — those mean "the attempt itself ran and produced a
/// failure"; `not_run_worker_died` means "the attempt never had a
/// chance." Consumers should treat the latter as missing evidence,
/// not as a verdict.
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
// absent prediction as an allow verdict. See PolicyWitness.md
// "Filter kinds where prediction is unavailable" for the full
// contract.
public enum SandboxCheckOutcome {
    public static let allow = "allow"
    public static let deny = "deny"
    public static let error = "error"
    public static let predictionUnavailable = "prediction_unavailable"
}

public struct PWRunnerRunSpec: Codable {
    public var schema_version: Int
    public var specimen_id: String
    public var run_kind: String?
    public var policy: PWRunnerPolicySpec
    public var probe_plan: [PWRunnerProbeStep]
    public var _test_overrides: PWRunnerTestOverrides?

    public init(
        schema_version: Int = 1,
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
//
// See AGENTS.md → "Testing `normalized_outcome` failure paths via
// `_test_overrides`" for the full contract, the four-assertion test
// recipe, and the rules for adding a new key.
public struct PWRunnerTestOverrides: Codable {
    public var libsandbox_path: String?
    public var worker_executable_path: String?
    public var worker_timeout_ms: Int?
    public var validator_executable_path: String?
    public var worker_post_apply_hang_ms: Int?

    public init(
        libsandbox_path: String? = nil,
        worker_executable_path: String? = nil,
        worker_timeout_ms: Int? = nil,
        validator_executable_path: String? = nil,
        worker_post_apply_hang_ms: Int? = nil
    ) {
        self.libsandbox_path = libsandbox_path
        self.worker_executable_path = worker_executable_path
        self.worker_timeout_ms = worker_timeout_ms
        self.validator_executable_path = validator_executable_path
        self.worker_post_apply_hang_ms = worker_post_apply_hang_ms
    }
}

public struct PWRunnerPolicySpec: Codable {
    // Policy format, e.g. PWRunnerWire.policyFormatSbpl.
    public var format: String
    public var sbpl_source: String?
    public var params: [String: String]?
    // Named augments the caller opts into (e.g. "exec_baseline"). The
    // controller resolves each name to a file under
    // Contents/Resources/Augments/<name>.sb, appends the contents to
    // sbpl_source before preflight, and strips this field from the
    // request forwarded to the runner. The runner is augment-agnostic;
    // this field exists on the wire so callers can author their request
    // without controller-private knowledge.
    public var augments: [String]?

    public init(
        format: String,
        sbpl_source: String? = nil,
        params: [String: String]? = nil,
        augments: [String]? = nil
    ) {
        self.format = format
        self.sbpl_source = sbpl_source
        self.params = params
        self.augments = augments
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

// Candidate kernel-side forms of a path-filter argument. Diagnostic only —
// the runner passes the raw filter_value to sandbox_check; this block lets a
// caller see which other forms of the same path libsandbox could have been
// comparing against when matching a `(subpath ...)` rule.
//
// Introduced in PWRunnerRunResult.schema_version = 2. Old controllers reading
// new runner output ignore this field gracefully; new controllers reading old
// runner output see nil and should branch on schema_version to know whether
// the absence is "unsupported" or "no path-filter steps".
public struct PWRunnerPathDiagnostics: Codable {
    public var input: String
    public var realpath_resolved: String?
    public var firmlink_resolved: String?
    public var data_volume_form: String?

    public init(
        input: String,
        realpath_resolved: String? = nil,
        firmlink_resolved: String? = nil,
        data_volume_form: String? = nil
    ) {
        self.input = input
        self.realpath_resolved = realpath_resolved
        self.firmlink_resolved = firmlink_resolved
        self.data_volume_form = data_volume_form
    }

    enum CodingKeys: String, CodingKey {
        case input
        case realpath_resolved
        case firmlink_resolved
        case data_volume_form
    }

    // Always emit all four keys at schema_version >= 2 so a consumer can
    // distinguish "computed and the result was null" from "not emitted at
    // all". The default Swift Codable behavior would omit keys whose values
    // are nil, conflating both states.
    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(input, forKey: .input)
        if let realpath_resolved {
            try container.encode(realpath_resolved, forKey: .realpath_resolved)
        } else {
            try container.encodeNil(forKey: .realpath_resolved)
        }
        if let firmlink_resolved {
            try container.encode(firmlink_resolved, forKey: .firmlink_resolved)
        } else {
            try container.encodeNil(forKey: .firmlink_resolved)
        }
        if let data_volume_form {
            try container.encode(data_volume_form, forKey: .data_volume_form)
        } else {
            try container.encodeNil(forKey: .data_volume_form)
        }
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        input = try container.decode(String.self, forKey: .input)
        realpath_resolved = try container.decodeIfPresent(String.self, forKey: .realpath_resolved)
        firmlink_resolved = try container.decodeIfPresent(String.self, forKey: .firmlink_resolved)
        data_volume_form = try container.decodeIfPresent(String.self, forKey: .data_volume_form)
    }
}

public struct PWRunnerSandboxCheckResult: Codable {
    public var rc: Int
    public var outcome: String
    public var pid: Int
    public var operation: String
    public var scope: String
    public var filter_kind: String
    public var filter_value: String?
    public var effective_filter_value: String?
    public var filter_type_id: Int?
    public var errno: Int?
    public var error: String?
    public var path_diagnostics: PWRunnerPathDiagnostics?

    public init(
        rc: Int,
        outcome: String,
        pid: Int,
        operation: String,
        scope: String,
        filter_kind: String,
        filter_value: String? = nil,
        effective_filter_value: String? = nil,
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
        self.effective_filter_value = effective_filter_value
        self.filter_type_id = filter_type_id
        self.errno = errno
        self.error = error
        self.path_diagnostics = path_diagnostics
    }

    enum CodingKeys: String, CodingKey {
        case rc
        case outcome
        case pid
        case operation
        case scope
        case filter_kind
        case filter_value
        case effective_filter_value
        case filter_type_id
        case errno
        case error
        case path_diagnostics
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
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
        if let effective_filter_value {
            try container.encode(effective_filter_value, forKey: .effective_filter_value)
        } else {
            try container.encodeNil(forKey: .effective_filter_value)
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
        rc = try container.decode(Int.self, forKey: .rc)
        outcome = try container.decode(String.self, forKey: .outcome)
        pid = try container.decodeIfPresent(Int.self, forKey: .pid) ?? -1
        operation = try container.decodeIfPresent(String.self, forKey: .operation) ?? ""
        scope = try container.decode(String.self, forKey: .scope)
        filter_kind = try container.decode(String.self, forKey: .filter_kind)
        filter_value = try container.decodeIfPresent(String.self, forKey: .filter_value)
        effective_filter_value = try container.decodeIfPresent(String.self, forKey: .effective_filter_value)
        filter_type_id = try container.decodeIfPresent(Int.self, forKey: .filter_type_id)
        errno = try container.decodeIfPresent(Int.self, forKey: .errno)
        error = try container.decodeIfPresent(String.self, forKey: .error)
        path_diagnostics = try container.decodeIfPresent(PWRunnerPathDiagnostics.self, forKey: .path_diagnostics)
    }
}

public struct PWRunnerAttemptResult: Codable {
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
    /// `child_pid` to distinguish a sandbox-blocked spawn (strong
    /// deny evidence) from a child non-zero exit (non-policy
    /// failure).
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

public struct PWRunnerStepResult: Codable {
    public var step_id: String
    public var sandbox_check: PWRunnerSandboxCheckResult
    public var attempt: PWRunnerAttemptResult
    public var deny_signal: PWRunnerSignalResult

    /// Drift between the validator's predicted verdict and the attempt's
    /// observed verdict. Introduced in PWRunnerRunResult.schema_version=4.
    ///
    /// Semantics:
    ///   - `true`  — validator predicted allow but attempt observed deny
    ///               (or vice versa). The libsandbox-drift design property
    ///               PolicyWitness exists to surface.
    ///   - `false` — validator predicted X and attempt observed X.
    ///   - `nil`   — no comparison possible: validator was skipped
    ///               (e.g. `prediction_unavailable` filter pair), validator
    ///               wasn't run (Swift-worker code path), validator failed
    ///               to produce a verdict for this step, or the attempt
    ///               didn't run.
    ///
    /// `nil` is the default and is encoded as explicit JSON null so
    /// consumers can distinguish "field absent on v3" from "field present
    /// but no comparison possible on v4".
    public var drift: Bool?

    public init(
        step_id: String,
        sandbox_check: PWRunnerSandboxCheckResult,
        attempt: PWRunnerAttemptResult,
        deny_signal: PWRunnerSignalResult,
        drift: Bool? = nil
    ) {
        self.step_id = step_id
        self.sandbox_check = sandbox_check
        self.attempt = attempt
        self.deny_signal = deny_signal
        self.drift = drift
    }

    enum CodingKeys: String, CodingKey {
        case step_id
        case sandbox_check
        case attempt
        case deny_signal
        case drift
    }

    // Custom encode so `drift` is emitted as explicit JSON null when
    // nil. Consumers at schema_version >= 4 can rely on the key being
    // present (bool or null); v3 producers never write the key at all.
    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(step_id, forKey: .step_id)
        try container.encode(sandbox_check, forKey: .sandbox_check)
        try container.encode(attempt, forKey: .attempt)
        try container.encode(deny_signal, forKey: .deny_signal)
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
        deny_signal = try container.decode(PWRunnerSignalResult.self, forKey: .deny_signal)
        // decodeIfPresent handles both "key absent" (v3 producer) and
        // "key present but null" (v4 producer with no comparison) →
        // both land as Bool? = nil on the reader side. That's the
        // intended behaviour.
        drift = try container.decodeIfPresent(Bool.self, forKey: .drift)
    }
}

public struct PWRunnerSubprocess: Codable {
    public var pid: Int
    public var term_signal: Int?
    public var exit_code: Int?
    public var partial_steps: Bool

    public init(
        pid: Int,
        term_signal: Int? = nil,
        exit_code: Int? = nil,
        partial_steps: Bool
    ) {
        self.pid = pid
        self.term_signal = term_signal
        self.exit_code = exit_code
        self.partial_steps = partial_steps
    }
}

/// Validator child process metadata. Introduced in
/// PWRunnerRunResult.schema_version=4 to mirror `runner_subprocess` for
/// the `sb_api_validator --batch` child the runner host spawns
/// alongside the C worker. `pid` is the validator's PID; `exit_code`
/// is its waitpid status when the validator clean-exited; `term_signal`
/// is set when the validator was signaled (typically only the host's
/// SIGKILL grace fallback). Exactly one of `exit_code` or `term_signal`
/// is non-nil for a completed run.
///
/// `validator_subprocess` is nil on the runner response when the
/// validator child didn't run. Two cases reach this: every probe in
/// the plan had an (operation, filter) pair in the
/// `prediction_unavailable` set (the orchestrator skipped the
/// validator and synthesized verdicts locally), or the validator
/// child failed to spawn before any metadata could be captured.
/// In the latter case `normalized_outcome` is set to
/// `validator_spawn_failed`.
public struct PWRunnerValidatorSubprocess: Codable {
    public var pid: Int
    public var term_signal: Int?
    public var exit_code: Int?

    public init(pid: Int, term_signal: Int? = nil, exit_code: Int? = nil) {
        self.pid = pid
        self.term_signal = term_signal
        self.exit_code = exit_code
    }
}

public struct PWRunnerRunResult: Codable {
    // Response wire version.
    //   1 — initial shape.
    //   2 — adds optional `steps[].sandbox_check.path_diagnostics` block
    //       (kernel-side path candidate forms). Consumers that branch on
    //       schema_version can rely on path_diagnostics being available on
    //       any path-filter check when schema_version >= 2. The field is
    //       additive: clients pinned to v1 ignore it transparently.
    //   3 — splits the XPC service host from the sandboxed worker process.
    //       `pid` is the sandboxed worker PID when `runner_subprocess` is
    //       present, so unified-log correlation should continue to use this
    //       top-level field. `runner_subprocess` carries the worker exit
    //       status observed by the unsandboxed host.
    //   4 — adds `validator_subprocess` (alongside `runner_subprocess`)
    //       describing the sb_api_validator --batch child the host spawns
    //       against the sandboxed worker_pid, and adds `steps[].drift`
    //       (nullable bool) capturing validator-prediction vs
    //       attempt-observation disagreement per step.
    //       `validator_subprocess` is nil when no validator child ran
    //       (every probe was in the prediction-unavailable set, or the
    //       child failed to spawn). `drift` is nil when no comparison
    //       is possible (validator wasn't run for the step, or the
    //       (validator-allow, ambiguous-deny) asymmetry applies).
    //       Top-level `pid` semantics from v3 are preserved.
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
    public var sandboxed_after_apply: Bool?
    public var deny_signal_total: PWRunnerSignalResult?
    public var steps: [PWRunnerStepResult]
    public var runner_subprocess: PWRunnerSubprocess?
    public var validator_subprocess: PWRunnerValidatorSubprocess?
    public var test_overrides: PWRunnerTestOverrides?

    public init(
        schema_version: Int = 4,
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
        test_overrides: PWRunnerTestOverrides? = nil
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
        self.sandboxed_after_apply = sandboxed_after_apply
        self.deny_signal_total = deny_signal_total
        self.steps = steps
        self.runner_subprocess = runner_subprocess
        self.validator_subprocess = validator_subprocess
        self.test_overrides = test_overrides
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

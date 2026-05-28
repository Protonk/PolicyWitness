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

    static let attemptActionOpenRead = "open_read"
    static let attemptActionOpenWrite = "open_write"
    static let attemptActionCreate = "create"
    static let attemptActionUnlink = "unlink"
    static let attemptActionMachLookup = "bootstrap_look_up"

    static let sandboxFilterNone = "none"
    static let sandboxFilterPath = "path"
    static let sandboxFilterGlobalName = "global_name"
    static let sandboxFilterLocalName = "local_name"
    static let sandboxCheckScopePost = "post_sandbox"

    static let instrumentationPhasePre = "pre_sandbox"
    static let instrumentationPhasePost = "post_sandbox"

    static let instrumentationKindDylibLoad = "dylib_load"
    static let instrumentationKindDebugWait = "debug_wait"
    static let instrumentationKindExecmemProbe = "execmem_probe"
    static let instrumentationKindDyldEnv = "dyld_env"
}

public struct PWRunnerRunSpec: Codable {
    public var schema_version: Int
    public var specimen_id: String
    public var run_kind: String?
    public var policy: PWRunnerPolicySpec
    public var probe_plan: [PWRunnerProbeStep]
    public var instrumentation: PWRunnerInstrumentation?

    public init(
        schema_version: Int = 1,
        specimen_id: String,
        run_kind: String? = nil,
        policy: PWRunnerPolicySpec,
        probe_plan: [PWRunnerProbeStep],
        instrumentation: PWRunnerInstrumentation? = nil
    ) {
        self.schema_version = schema_version
        self.specimen_id = specimen_id
        self.run_kind = run_kind
        self.policy = policy
        self.probe_plan = probe_plan
        self.instrumentation = instrumentation
    }
}

public struct PWRunnerPolicySpec: Codable {
    // Policy format, e.g. PWRunnerWire.policyFormatSbpl.
    public var format: String
    public var sbpl_source: String?
    public var params: [String: String]?

    public init(
        format: String,
        sbpl_source: String? = nil,
        params: [String: String]? = nil
    ) {
        self.format = format
        self.sbpl_source = sbpl_source
        self.params = params
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
    // "file" | "mach_lookup"
    public var kind: String
    // For kind=file:
    //   action: open_read | open_write | create | unlink
    //   target: path
    // For kind=mach_lookup:
    //   action: bootstrap_look_up
    //   target: mach service name
    public var action: String
    public var target: String

    public init(kind: String, action: String, target: String) {
        self.kind = kind
        self.action = action
        self.target = target
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

public struct PWRunnerInstrumentation: Codable {
    public var version: Int
    public var ports: [PWRunnerInstrumentationPort]

    public init(version: Int = 1, ports: [PWRunnerInstrumentationPort]) {
        self.version = version
        self.ports = ports
    }
}

public struct PWRunnerInstrumentationPort: Codable {
    public var kind: String
    public var phase: String?
    public var label: String?
    public var path: String?
    public var symbol: String?
    public var sleep_ms: Int?
    public var size_bytes: Int?
    public var keys: [String]?
    public var expected: [String: String]?
    public var reveal_values: Bool?

    public init(
        kind: String,
        phase: String? = nil,
        label: String? = nil,
        path: String? = nil,
        symbol: String? = nil,
        sleep_ms: Int? = nil,
        size_bytes: Int? = nil,
        keys: [String]? = nil,
        expected: [String: String]? = nil,
        reveal_values: Bool? = nil
    ) {
        self.kind = kind
        self.phase = phase
        self.label = label
        self.path = path
        self.symbol = symbol
        self.sleep_ms = sleep_ms
        self.size_bytes = size_bytes
        self.keys = keys
        self.expected = expected
        self.reveal_values = reveal_values
    }
}

public struct PWRunnerInstrumentationReport: Codable {
    public var version: Int
    public var ports: [PWRunnerInstrumentationPortReport]

    public init(version: Int, ports: [PWRunnerInstrumentationPortReport]) {
        self.version = version
        self.ports = ports
    }
}

public struct PWRunnerInstrumentationPortReport: Codable {
    public var kind: String
    public var phase: String?
    public var label: String?
    public var status: String
    public var error: String?
    public var dylib: PWRunnerInstrumentationDylibReport?
    public var debug_wait: PWRunnerInstrumentationDebugWaitReport?
    public var execmem_probe: PWRunnerInstrumentationExecmemReport?
    public var dyld_env: PWRunnerInstrumentationDyldEnvReport?

    public init(
        kind: String,
        phase: String? = nil,
        label: String? = nil,
        status: String,
        error: String? = nil,
        dylib: PWRunnerInstrumentationDylibReport? = nil,
        debug_wait: PWRunnerInstrumentationDebugWaitReport? = nil,
        execmem_probe: PWRunnerInstrumentationExecmemReport? = nil,
        dyld_env: PWRunnerInstrumentationDyldEnvReport? = nil
    ) {
        self.kind = kind
        self.phase = phase
        self.label = label
        self.status = status
        self.error = error
        self.dylib = dylib
        self.debug_wait = debug_wait
        self.execmem_probe = execmem_probe
        self.dyld_env = dyld_env
    }
}

public struct PWRunnerInstrumentationDylibReport: Codable {
    public var path: String
    public var symbol: String?
    public var symbol_found: Bool?

    public init(path: String, symbol: String? = nil, symbol_found: Bool? = nil) {
        self.path = path
        self.symbol = symbol
        self.symbol_found = symbol_found
    }
}

public struct PWRunnerInstrumentationDebugWaitReport: Codable {
    public var sleep_ms: Int

    public init(sleep_ms: Int) {
        self.sleep_ms = sleep_ms
    }
}

public struct PWRunnerInstrumentationExecmemReport: Codable {
    public var size_bytes: Int
    public var mmap_succeeded: Bool
    public var errno: Int?

    public init(size_bytes: Int, mmap_succeeded: Bool, errno: Int? = nil) {
        self.size_bytes = size_bytes
        self.mmap_succeeded = mmap_succeeded
        self.errno = errno
    }
}

public struct PWRunnerInstrumentationDyldEnvReport: Codable {
    public var keys_present: [String]
    public var keys_missing: [String]
    public var expected_mismatch: [String]
    public var values: [String: String]?

    public init(
        keys_present: [String],
        keys_missing: [String],
        expected_mismatch: [String],
        values: [String: String]? = nil
    ) {
        self.keys_present = keys_present
        self.keys_missing = keys_missing
        self.expected_mismatch = expected_mismatch
        self.values = values
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

    public init(
        rc: Int,
        errno: Int? = nil,
        outcome: String,
        error: String? = nil,
        requested_path: String? = nil,
        normalized_path: String? = nil,
        observed_path: String? = nil
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

    public init(
        step_id: String,
        sandbox_check: PWRunnerSandboxCheckResult,
        attempt: PWRunnerAttemptResult,
        deny_signal: PWRunnerSignalResult
    ) {
        self.step_id = step_id
        self.sandbox_check = sandbox_check
        self.attempt = attempt
        self.deny_signal = deny_signal
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
    public var instrumentation: PWRunnerInstrumentationReport?
    public var runner_subprocess: PWRunnerSubprocess?

    public init(
        schema_version: Int = 3,
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
        instrumentation: PWRunnerInstrumentationReport? = nil,
        runner_subprocess: PWRunnerSubprocess? = nil
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
        self.instrumentation = instrumentation
        self.runner_subprocess = runner_subprocess
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

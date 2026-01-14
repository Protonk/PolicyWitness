import Foundation

// PWRunner is a single-purpose, ephemeral XPC runner that starts unsandboxed and
// self-applies a seatbelt profile exactly once, then executes a probe plan and exits.
//
// This file intentionally defines a small JSON-over-Data protocol surface so the
// runner can be driven by multiple controllers (CLI, lab tools) without NSXPC
// object graphs.

@objc public protocol PWRunnerProtocol {
    func runSpecimen(_ request: Data, withReply reply: @escaping (Data) -> Void)
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
    // "sbpl" or "compiled_bytes"
    public var format: String
    public var sbpl_source: String?
    public var params: [String: String]?
    public var compiled_profile_b64: String?

    public init(
        format: String,
        sbpl_source: String? = nil,
        params: [String: String]? = nil,
        compiled_profile_b64: String? = nil
    ) {
        self.format = format
        self.sbpl_source = sbpl_source
        self.params = params
        self.compiled_profile_b64 = compiled_profile_b64
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

public struct PWRunnerSandboxCheckResult: Codable {
    public var rc: Int
    public var outcome: String
    public var filter_kind: String
    public var filter_value: String?

    public init(rc: Int, outcome: String, filter_kind: String, filter_value: String? = nil) {
        self.rc = rc
        self.outcome = outcome
        self.filter_kind = filter_kind
        self.filter_value = filter_value
    }
}

public struct PWRunnerAttemptResult: Codable {
    public var rc: Int
    public var errno: Int?
    public var outcome: String
    public var error: String?

    public init(rc: Int, errno: Int? = nil, outcome: String, error: String? = nil) {
        self.rc = rc
        self.errno = errno
        self.outcome = outcome
        self.error = error
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

public struct PWRunnerRunResult: Codable {
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

    public init(
        schema_version: Int = 1,
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
        instrumentation: PWRunnerInstrumentationReport? = nil
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

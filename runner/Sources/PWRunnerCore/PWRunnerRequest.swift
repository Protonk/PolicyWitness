import Foundation
import Darwin

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
            "unsupported_extension_authority": "extension authority must be read or read_write",
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
// values. `PWRunnerRunResult.test_overrides` mirrors supplied controls when
// available, subject to refusal sanitization. Values can be inert or their
// boundaries unreached; presence does not establish an effective intervention.
// Early replies can omit the echo, so absence does not establish that the
// request supplied no controls. Retain the request for that fact.
//
// Design rule for new keys: re-route a *condition* (a path, a deadline,
// a hostile value), never fake a *result*. The classifier and the JSON
// envelope assembly must still run for real; only their input is steered.
//
// runner/README.md's "Test seam: `_test_overrides`" is the key/boundary
// reference, including host resolution and native argument admission. The
// adjacent AGENTS.md gives the assertion recipe and rules for new controls.
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
    //   action: open_read | read_fresh | open_write | write_fresh | create | create_fresh | unlink | access
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

import Foundation
import Darwin

// Query admission and the shared planner exclusion set. The host validates
// the submitted queries and decides which of them the validator child asks
// about; it performs no sandbox query or attempt of its own.

// Filter kinds the runner knows how to validate, predict, and route to
// the sb_api_validator. Unknown names refuse the whole request before attempts.
let knownFilterKinds: Set<String> = [
    PWRunnerWire.sandboxFilterNone,
    PWRunnerWire.sandboxFilterPath,
    PWRunnerWire.sandboxFilterGlobalName,
    PWRunnerWire.sandboxFilterLocalName,
    PWRunnerWire.sandboxFilterIokitRegistryEntryClass,
    PWRunnerWire.sandboxFilterIokitUserClientClass,
    PWRunnerWire.sandboxFilterSysctlName,
]

func sandboxCheckFailure(_ steps: [PWRunnerProbeStep]) -> PWRunnerRequestFailure? {
    for (index, step) in steps.enumerated() {
        let path = ["probe_plan", String(index), "sandbox_check"]
        let op = step.sandbox_check.operation.trimmingCharacters(in: .whitespacesAndNewlines)
        if op.isEmpty {
            return PWRunnerRequestFailure(code: "empty_operation", path: path + ["operation"])
        }
        let kind = step.sandbox_check.filter.kind
        guard knownFilterKinds.contains(kind) else {
            return PWRunnerRequestFailure(code: "unknown_filter_kind", path: path + ["filter", "kind"])
        }
        let needsValue = kind != PWRunnerWire.sandboxFilterNone
        if needsValue {
            let value = step.sandbox_check.filter.value?.trimmingCharacters(in: .whitespacesAndNewlines)
            if value == nil || value == "" {
                return PWRunnerRequestFailure(code: "missing_filter_value", path: path + ["filter", "value"])
            }
        } else if step.sandbox_check.filter.value != nil {
            return PWRunnerRequestFailure(code: "inapplicable_field", path: path + ["filter", "value"])
        }
    }
    return nil
}

func validateSandboxChecks(_ steps: [PWRunnerProbeStep]) throws {
    if let failure = sandboxCheckFailure(steps) { throw failure }
}

/// Meanings that structural decoding cannot express. Run after capacity checks
/// and before either child is created, at both host orchestration entry points.
/// Query and attempt scopes need not match; a known but unavailable prediction
/// still permits a supported attempt and an honest unavailable observation.
func requestMeaningFailure(_ spec: PWRunnerRunSpec) -> PWRunnerRequestFailure? {
    if let augments = spec.policy.augments, !augments.isEmpty {
        return PWRunnerRequestFailure(code: "unresolved_augments", path: ["policy", "augments"])
    }
    if spec.policy.format != PWRunnerWire.policyFormatSbpl {
        return PWRunnerRequestFailure(code: "unsupported_policy_format", path: ["policy", "format"])
    }
    if spec.policy.sbpl_source == nil {
        return PWRunnerRequestFailure(code: "missing_policy_source", path: ["policy", "sbpl_source"])
    }
    if spec.policy.capture_applied_profile == true {
        if captureNonceBytes(spec.policy.capture_nonce) == nil {
            return PWRunnerRequestFailure(code: "invalid_capture_nonce", path: ["policy", "capture_nonce"])
        }
    } else if spec.policy.capture_nonce != nil {
        return PWRunnerRequestFailure(code: "inapplicable_field", path: ["policy", "capture_nonce"])
    }
    if let failure = sandboxCheckFailure(spec.probe_plan) { return failure }
    var ids = Set<String>()
    for (index, step) in spec.probe_plan.enumerated() {
        let path = ["probe_plan", String(index)]
        if !ids.insert(step.step_id).inserted {
            return PWRunnerRequestFailure(code: "duplicate_step_id", path: path + ["step_id"])
        }
        guard let kind = mapAttemptKindOrNil(step.attempt) else {
            return PWRunnerRequestFailure(code: "unsupported_attempt", path: path + ["attempt"])
        }
        if kind != .execSpawn && step.attempt.args != nil {
            return PWRunnerRequestFailure(code: "inapplicable_field", path: path + ["attempt", "args"])
        }
        if kind == .execSpawn && !step.attempt.target.hasPrefix("/") {
            return PWRunnerRequestFailure(code: "relative_exec_target", path: path + ["attempt", "target"])
        }
    }
    return nil
}

func requestRefusalReply(parsed: PWRunnerRunSpec, failure: PWRunnerRequestFailure,
                         bundleId: String?, policyHash: String? = nil) -> PWRunnerRunResult {
    PWRunnerRunResult(specimen_id: parsed.specimen_id, run_kind: parsed.run_kind,
        rc: 1, normalized_outcome: NormalizedOutcome.badRequest, error: failure.description,
        pid: Int(getpid()), bundle_id: bundleId, policy_format: parsed.policy.format,
        policy_sha256: policyHash, steps: [], test_overrides: parsed._test_overrides,
        request_failure: failure)
}

// (operation, filter_kind) pairs the planner excludes from the validator
// batch: for each, no filter ID in 1..200 produced a sandbox_check verdict
// matching kernel enforcement under verify_filter_id.sh, so no prediction is
// requested and the step records `query_plan:prediction_unavailable_pair`.
// The attempt channel still runs.
//
// Keyed by (operation, filter_kind), not by filter_kind alone: the
// verification is op+filter-specific. A specimen pairing one of these filter
// kinds with a different operation gets the normal query.
//
// Entries here must be paired with an enforcement_probe verification
// commit naming the op+filter pair and the empirical evidence.
struct PredictionUnavailablePair: Hashable {
    let operation: String
    let filterKind: String
}

let predictionUnavailableOpFilters: Set<PredictionUnavailablePair> = [
    // iokit-open-service + iokit-registry-entry-class: verified
    // 2026-05-29 against IOSurfaceRoot; no filter ID in 1..200
    // produced a sandbox_check verdict matching kernel enforcement.
    .init(operation: "iokit-open-service",
          filterKind: PWRunnerWire.sandboxFilterIokitRegistryEntryClass),
    // iokit-open-user-client + iokit-user-client-class: verified
    // 2026-05-29 with policy filter value IOSurfaceRootUserClient
    // and probe target IOSurfaceRoot. The earlier "verification"
    // (pre-audit) used operation iokit-open-service, which is the
    // wrong SBPL operation for this filter — both operations fire
    // when IOServiceOpen is called, but iokit-user-client-class
    // matches against the open-user-client operation. With the
    // corrected pairing the kernel enforces the deny (kr=
    // kIOReturnNotPermitted) and no sandbox_check filter ID in
    // 1..200 produces a verdict that agrees with the kernel.
    .init(operation: "iokit-open-user-client",
          filterKind: PWRunnerWire.sandboxFilterIokitUserClientClass),
    // sysctl-read + sysctl-name: verified 2026-05-29 against
    // kern.osrelease; same pattern as iokit, so the mismatch is not
    // iokit-specific.
    .init(operation: "sysctl-read",
          filterKind: PWRunnerWire.sandboxFilterSysctlName),
]

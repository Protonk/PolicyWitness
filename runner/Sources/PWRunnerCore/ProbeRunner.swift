import Foundation
import Darwin

// Query admission and the shared planner exclusion set. The host validates
// the submitted queries and decides which of them the validator child asks
// about; it performs no sandbox query or attempt of its own.

private enum SpecValidationError: Error, CustomStringConvertible {
    case invalidSandboxCheck(stepId: String, message: String)

    var description: String {
        switch self {
        case .invalidSandboxCheck(let stepId, let message):
            return "invalid sandbox_check for step \(stepId): \(message)"
        }
    }
}

// Filter kinds the runner knows how to validate, predict, and route to
// the sb_api_validator. Unknown kinds are still accepted in the
// probe_plan — they fall through to per-step prediction_unavailable
// in the step builder instead of killing the whole plan with
// bad_request. This bounds the blast radius when a specimen mixes a
// recognized probe with one whose filter kind hasn't been verified.
let knownFilterKinds: Set<String> = [
    PWRunnerWire.sandboxFilterNone,
    PWRunnerWire.sandboxFilterPath,
    PWRunnerWire.sandboxFilterGlobalName,
    PWRunnerWire.sandboxFilterLocalName,
    PWRunnerWire.sandboxFilterIokitRegistryEntryClass,
    PWRunnerWire.sandboxFilterIokitUserClientClass,
    PWRunnerWire.sandboxFilterSysctlName,
]

func validateSandboxChecks(_ steps: [PWRunnerProbeStep]) throws {
    for step in steps {
        let op = step.sandbox_check.operation.trimmingCharacters(in: .whitespacesAndNewlines)
        if op.isEmpty {
            throw SpecValidationError.invalidSandboxCheck(stepId: step.step_id, message: "operation is empty")
        }
        let kind = step.sandbox_check.filter.kind
        // Value-required check applies only to known kinds that take
        // a value. Unknown kinds skip both predictions and validator
        // probes, so their value isn't consulted.
        let needsValue = knownFilterKinds.contains(kind)
            && kind != PWRunnerWire.sandboxFilterNone
        if needsValue {
            let value = step.sandbox_check.filter.value?.trimmingCharacters(in: .whitespacesAndNewlines)
            if value == nil || value == "" {
                throw SpecValidationError.invalidSandboxCheck(
                    stepId: step.step_id,
                    message: "filter.value required for kind \(kind)"
                )
            }
        }
    }
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

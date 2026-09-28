import Foundation
@testable import PWRunnerCore

// Query strings and filter/attempt labels are host-only: they reach the reply
// (and queries the validator), never shared memory, so the driver cannot refuse them. The
// orchestrator bounds them with the same host-owned record before any process
// work. Every oracle here is a constructed string; nothing about sandbox
// behavior is claimed.

private func queryStep(_ id: String, operation: String = "file-read-data",
                       kind: String = "path", value: String? = "/etc/hosts") -> PWRunnerProbeStep {
    PWRunnerProbeStep(step_id: id,
        sandbox_check: PWRunnerSandboxCheck(operation: operation,
            filter: PWRunnerSandboxFilter(kind: kind, value: value)),
        attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts"))
}

func runQueryAdmissionTests(_ tk: TestKit) {
    tk.group("sandbox_check query admission") {
        tk.run("echoed filter and attempt labels cannot bypass admission") {
            for field in ["sandbox_check.filter.kind", "attempt.kind", "attempt.action"] {
                for multibyte in [false, true] {
                    for count in [127, 128, 32_768] {
                        let text = multibyte
                            ? String(repeating: "é", count: count / 2) + String(repeating: "x", count: count % 2)
                            : String(repeating: "x", count: count)
                        var step = queryStep("label")
                        switch field {
                        case "sandbox_check.filter.kind": step.sandbox_check.filter.kind = text
                        case "attempt.kind": step.attempt.kind = text
                        default: step.attempt.action = text
                        }
                        let refused = queryAdmissionFailure([step])
                        if count == 127 {
                            try expectNil(refused, field)
                        } else {
                            try expectEqual(refused?.field, field)
                            try expectEqual(refused?.actual, count)
                            try expectEqual(refused?.maximum, 127)
                            try expectEqual(refused?.unit, "utf8_bytes")
                            try expectEqual(refused?.step_id, "label")
                        }
                    }
                }
            }
        }

        tk.run("oversized labels produce a small refusal instead of a lost reply") {
            for field in ["sandbox_check.filter.kind", "attempt.kind", "attempt.action"] {
                let text = String(repeating: "x", count: 32_768)
                let plan = (0..<256).map { index -> PWRunnerProbeStep in
                    var step = queryStep("s\(index)")
                    switch field {
                    case "sandbox_check.filter.kind": step.sandbox_check.filter.kind = text
                    case "attempt.kind": step.attempt.kind = text
                    default: step.attempt.action = text
                    }
                    return step
                }
                let parsed = PWRunnerRunSpec(specimen_id: "label-admission",
                    policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)(allow default)"),
                    probe_plan: plan)
                let result = CWorkerOrchestrator.run(parsed: parsed, policyHash: "fixture", bundleId: nil,
                    workerExecutablePath: "/nonexistent-worker", validatorExecutablePath: "/nonexistent-validator")
                try expectEqual(result.normalized_outcome, NormalizedOutcome.badRequest, field)
                try expectEqual(result.admission_failure?.field, field)
                try expectNil(result.runner_subprocess)
                try expectNil(result.validator_subprocess)
                try expectTrue(result.steps.isEmpty)
                try expectTrue(pwRunnerReplyData(result).count < 4096)
            }
        }

        tk.run("at-limit ASCII and multibyte strings are admitted") {
            let operation = String(repeating: "o", count: sandboxCheckOperationMaxBytes)
            let value = String(repeating: "v", count: sandboxCheckFilterValueMaxBytes)
            // Bytes, not characters: 'é' is two UTF-8 bytes.
            let multibyteOperation = String(repeating: "é", count: sandboxCheckOperationMaxBytes / 2) + "x"
            let multibyteValue = String(repeating: "é", count: sandboxCheckFilterValueMaxBytes / 2) + "x"
            try expectEqual(multibyteOperation.utf8.count, sandboxCheckOperationMaxBytes)
            try expectEqual(multibyteValue.utf8.count, sandboxCheckFilterValueMaxBytes)
            try expectNil(queryAdmissionFailure([
                queryStep("ascii", operation: operation, value: value),
                queryStep("multibyte", operation: multibyteOperation, value: multibyteValue),
                queryStep("no-value", kind: "none", value: nil),
            ]))
        }

        tk.run("one byte over refuses with the host-owned record") {
            let operation = String(repeating: "o", count: sandboxCheckOperationMaxBytes + 1)
            guard let refusedOperation = queryAdmissionFailure([queryStep("ok"), queryStep("long-op", operation: operation)]) else {
                throw TestFailure(message: "over-limit operation admitted")
            }
            try expectEqual(refusedOperation.origin, "runner_host")
            try expectEqual(refusedOperation.field, "sandbox_check.operation")
            try expectEqual(refusedOperation.actual, sandboxCheckOperationMaxBytes + 1)
            try expectEqual(refusedOperation.maximum, sandboxCheckOperationMaxBytes)
            try expectEqual(refusedOperation.unit, "utf8_bytes")
            try expectEqual(refusedOperation.step_id, "long-op")
            try expectNil(refusedOperation.parameter_key)
            try expectNil(refusedOperation.index)

            let value = String(repeating: "é", count: (sandboxCheckFilterValueMaxBytes + 1) / 2)
            try expectEqual(value.utf8.count, sandboxCheckFilterValueMaxBytes + 1)
            guard let refusedValue = queryAdmissionFailure([queryStep("long-value", value: value)]) else {
                throw TestFailure(message: "over-limit multibyte value admitted")
            }
            try expectEqual(refusedValue.field, "sandbox_check.filter.value")
            try expectEqual(refusedValue.actual, sandboxCheckFilterValueMaxBytes + 1)
            try expectEqual(refusedValue.maximum, sandboxCheckFilterValueMaxBytes)
            try expectEqual(refusedValue.unit, "utf8_bytes")
            try expectEqual(refusedValue.step_id, "long-value")
        }

        tk.run("operation precedes value within a step; plan order across steps") {
            let operation = String(repeating: "o", count: sandboxCheckOperationMaxBytes + 1)
            let value = String(repeating: "v", count: sandboxCheckFilterValueMaxBytes + 1)
            let both = queryAdmissionFailure([queryStep("both", operation: operation, value: value)])
            try expectEqual(both?.field, "sandbox_check.operation")
            let ordered = queryAdmissionFailure([queryStep("first", value: value), queryStep("second", operation: operation)])
            try expectEqual(ordered?.step_id, "first")
            try expectEqual(ordered?.field, "sandbox_check.filter.value")
        }

        tk.run("the value is bounded for every filter kind, including unrecognized ones") {
            // Unknown kinds downgrade to prediction_unavailable, and `none`
            // sends no value to the validator, but the reply echoes whatever
            // was supplied in both cases.
            let value = String(repeating: "v", count: sandboxCheckFilterValueMaxBytes + 1)
            for kind in ["none", "path", "global_name", "sysctl_name", "unrecognized_kind"] {
                guard let refused = queryAdmissionFailure([queryStep("s", kind: kind, value: value)]) else {
                    throw TestFailure(message: "over-limit value admitted for kind \(kind)")
                }
                try expectEqual(refused.field, "sandbox_check.filter.value", kind)
            }
        }

        tk.run("orchestrator refuses before any process work") {
            // Nonexistent worker and validator paths: had admission not fired,
            // the driver would report a spawn failure instead of bad_request.
            let value = String(repeating: "q", count: 32_768)
            let parsed = PWRunnerRunSpec(specimen_id: "query-admission",
                policy: PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)(allow default)"),
                probe_plan: [queryStep("s000", operation: "sysctl-read", kind: "sysctl_name", value: value),
                             queryStep("s001")])
            var spawns = 0
            let result = CWorkerOrchestrator.run(parsed: parsed, policyHash: "fixture", bundleId: nil,
                workerExecutablePath: "/nonexistent-worker", validatorExecutablePath: "/nonexistent-validator",
                validatorSpawn: { _, _, _, _ in spawns += 1; return 0 })
            try expectEqual(spawns, 0)
            try expectEqual(result.normalized_outcome, NormalizedOutcome.badRequest)
            try expectEqual(result.rc, 1)
            try expectNil(result.runner_subprocess)
            try expectNil(result.validator_subprocess)
            try expectNil(result.validator_spawn_failure)
            guard let refused = result.admission_failure else { throw TestFailure(message: "no admission record") }
            try expectEqual(refused.origin, "runner_host")
            try expectEqual(refused.field, "sandbox_check.filter.value")
            try expectEqual(refused.actual, 32_768)
            try expectEqual(refused.maximum, sandboxCheckFilterValueMaxBytes)
            try expectEqual(refused.unit, "utf8_bytes")
            try expectEqual(refused.step_id, "s000")
            // Nothing ran, so no steps: echoing the plan would repeat the refused
            // 32 KiB strings, and 256 of them outgrow the reply cap on their own.
            try expectTrue(result.steps.isEmpty)
            // Encodes like every other admission refusal, and the reply stays small.
            let bytes = pwRunnerReplyData(result)
            try expectTrue(bytes.count < 4096, "refusal reply is \(bytes.count) bytes")
            let reply = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: bytes)
            try expectEqual(reply.normalized_outcome, NormalizedOutcome.badRequest)
            try expectEqual(reply.admission_failure?.field, "sandbox_check.filter.value")
            try expectEqual(reply.admission_failure?.actual, 32_768)
            try expectTrue(reply.steps.isEmpty)
        }
    }
}

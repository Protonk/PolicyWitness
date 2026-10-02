import Foundation
@testable import PWRunnerCore

// Query strings, filter/attempt labels and the top-level request strings are host-only: they reach the reply
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

/// Every string leaf and dictionary key of a decoded JSON value.
func stringLeaves(_ value: Any) -> [String] {
    if let text = value as? String { return [text] }
    if let array = value as? [Any] { return array.flatMap(stringLeaves) }
    if let object = value as? [String: Any] {
        return object.flatMap { [$0.key] + stringLeaves($0.value) }
    }
    return []
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
            try expectEqual(refusedOperation.step_index, 1)
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
            try expectEqual(refusedValue.step_index, 0)
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
            try expectEqual(refused.step_index, 0)
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

    tk.group("request-level admission") {
        func spec(specimenId: String = "s", runKind: String? = nil, format: String = "sbpl",
                  overrides: PWRunnerTestOverrides? = nil, plan: [PWRunnerProbeStep] = [queryStep("s")],
                  params: [String: String]? = nil) -> PWRunnerRunSpec {
            PWRunnerRunSpec(specimen_id: specimenId, run_kind: runKind,
                policy: PWRunnerPolicySpec(format: format, sbpl_source: "(version 1)(allow default)", params: params),
                probe_plan: plan, _test_overrides: overrides)
        }
        tk.run("every pair of oversized metadata fields has a bounded shared refusal") {
            let fields: [(String, (inout PWRunnerRunSpec, String) -> Void)] = [
                ("specimen_id", { $0.specimen_id = $1 }),
                ("run_kind", { $0.run_kind = $1 }),
                ("policy.format", { $0.policy.format = $1 }),
                ("_test_overrides.worker_executable_path", { $0._test_overrides!.worker_executable_path = $1 }),
                ("_test_overrides.validator_executable_path", { $0._test_overrides!.validator_executable_path = $1 }),
            ]
            for size in [2048, 32_768, 131_072] {
                let rejected = String(repeating: "é", count: size / 2)
                for i in fields.indices {
                    for j in fields.indices where j > i {
                        var parsed = spec(overrides: PWRunnerTestOverrides(worker_timeout_ms: 73))
                        fields[i].1(&parsed, rejected); fields[j].1(&parsed, rejected)
                        let result = CWorkerOrchestrator.run(parsed: parsed, policyHash: "fixture", bundleId: nil,
                            workerExecutablePath: "/nonexistent-worker", validatorExecutablePath: "/nonexistent-validator")
                        try expectEqual(result.normalized_outcome, NormalizedOutcome.badRequest)
                        try expectEqual(result.admission_failure?.field, fields[i].0)
                        try expectNil(result.runner_subprocess); try expectNil(result.validator_subprocess)
                        try expectTrue(result.steps.isEmpty)
                        try expectEqual(result.test_overrides?.worker_timeout_ms, 73)
                        let data = pwRunnerReplyData(result)
                        try expectTrue(data.count < 4096, "refusal grew with rejected values: \(data.count)")
                        // Containment over every decoded string leaf, not equality on
                        // named fields: prose diagnostics embed values too.
                        let leaves = stringLeaves(try JSONSerialization.jsonObject(with: data))
                        try expectFalse(leaves.contains { $0.contains(rejected) }, "\(fields[i].0)+\(fields[j].0)")
                        let serviceResult = admissionRefusalReply(parsed: parsed,
                            refused: CWorkerOrchestrator.admissionFailure(for: parsed)!, bundleId: nil, policyHash: "fixture")
                        try expectEqual(pwRunnerReplyData(serviceResult), data, "service and direct orchestration share refusal projection")
                    }
                }
            }
        }
        tk.run("direct orchestration checks worker identity before query diagnostics") {
            var step = queryStep(String(repeating: "i", count: 32_768), operation: String(repeating: "o", count: 128))
            let result = CWorkerOrchestrator.run(parsed: spec(plan: [step]), policyHash: "fixture", bundleId: nil,
                workerExecutablePath: "/nonexistent-worker", validatorExecutablePath: "/nonexistent-validator")
            try expectEqual(result.admission_failure?.field, "step_id")
            try expectNil(result.admission_failure?.step_id)
            try expectEqual(result.admission_failure?.step_index, 0)
            try expectTrue(pwRunnerReplyData(result).count < 4096)
            try expectNil(queryAdmissionFailure([step])?.step_id)
            step.step_id = "nul\0id"
            let failure = CWorkerOrchestrator.admissionFailure(for: spec(plan: [step]))
            try expectEqual(failure?.field, "step_id")
            try expectEqual(failure?.unit, "nul_bytes")
            try expectEqual(failure?.actual, 1); try expectEqual(failure?.maximum, 0)
        }
        tk.run("native strings reject NUL while host-only metadata preserves it") {
            var step = queryStep("s", operation: "file-read-data\0suffix")
            try expectEqual(queryAdmissionFailure([step])?.unit, "nul_bytes")
            step = queryStep("s", value: "/etc/hosts\0suffix")
            try expectEqual(queryAdmissionFailure([step])?.unit, "nul_bytes")
            let worker = CWorkerInput(workerExecutablePath: "unused", policy: "(version 1)\0", slots: [])
            try expectEqual(workerAdmissionFailure(worker)?.unit, "nul_bytes")
            let parsed = spec(specimenId: "s\0id", runKind: "run\0kind")
            try expectNil(CWorkerOrchestrator.admissionFailure(for: parsed))
            let rule = AdmissionStringRule(field: "example", maximum: 63, requiresCString: true)
            try expectNil(rule.safeEcho("native\0suffix"))
            try expectEqual(rule.safeEcho("é😀"), "é😀")
        }
        tk.run("top-level strings are bounded once, without step or parameter identity") {
            let cases: [(String, Int, (String) -> PWRunnerRunSpec)] = [
                ("specimen_id", specimenIdMaxBytes, { spec(specimenId: $0) }),
                ("run_kind", requestLabelMaxBytes, { spec(runKind: $0) }),
                ("policy.format", requestLabelMaxBytes, { spec(format: $0) }),
                ("_test_overrides.worker_executable_path", testOverridePathMaxBytes,
                 { spec(overrides: PWRunnerTestOverrides(worker_executable_path: $0)) }),
                ("_test_overrides.validator_executable_path", testOverridePathMaxBytes,
                 { spec(overrides: PWRunnerTestOverrides(validator_executable_path: $0)) }),
            ]
            for (field, maximum, make) in cases {
                let exact = String(repeating: "é", count: maximum / 2) + String(repeating: "x", count: maximum % 2)
                try expectEqual(exact.utf8.count, maximum, field)
                try expectNil(requestAdmissionFailure(make(exact)), field)
                try expectNil(CWorkerOrchestrator.admissionFailure(for: make(exact)), field)
                guard let refused = requestAdmissionFailure(make(exact + "x")) else {
                    throw TestFailure(message: "over-limit \(field) admitted")
                }
                try expectEqual(refused.origin, "runner_host")
                try expectEqual(refused.field, field)
                try expectEqual(refused.actual, maximum + 1)
                try expectEqual(refused.maximum, maximum)
                try expectEqual(refused.unit, "utf8_bytes")
                try expectNil(refused.step_id); try expectNil(refused.step_index)
                try expectNil(refused.parameter_key); try expectNil(refused.index)
            }
            try expectNil(requestAdmissionFailure(spec()))
        }
        tk.run("a refused step ID or parameter key is identified, never echoed") {
            let longId = String(repeating: "i", count: PWShmLayout.stepIdMax + 16)
            let plan = [queryStep("first"), PWRunnerProbeStep(step_id: longId,
                sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                    filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
                attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts"))]
            guard let refusedId = CWorkerOrchestrator.admissionFailure(for: spec(plan: plan)) else {
                throw TestFailure(message: "oversized step_id admitted")
            }
            try expectEqual(refusedId.field, "step_id")
            try expectEqual(refusedId.actual, longId.utf8.count)
            try expectNil(refusedId.step_id, "the refused string is not echoed")
            try expectEqual(refusedId.step_index, 1)
            let longKey = String(repeating: "k", count: PWShmLayout.paramKeyMax + 4)
            guard let refusedKey = CWorkerOrchestrator.admissionFailure(for: spec(params: [longKey: "v"])) else {
                throw TestFailure(message: "oversized parameter key admitted")
            }
            try expectEqual(refusedKey.field, "key")
            try expectNil(refusedKey.parameter_key, "the refused string is not echoed")
            let longValue = String(repeating: "v", count: PWShmLayout.paramValueMax + 4)
            let refusedValue = CWorkerOrchestrator.admissionFailure(for: spec(params: ["K": longValue]))
            try expectEqual(refusedValue?.field, "value")
            try expectEqual(refusedValue?.parameter_key, "K")
            // Every other per-step refusal names the step both ways.
            let longTarget = String(repeating: "t", count: PWShmLayout.targetMax + 4)
            let targetPlan = [queryStep("a"), PWRunnerProbeStep(step_id: "b",
                sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                    filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
                attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: longTarget))]
            let refusedTarget = CWorkerOrchestrator.admissionFailure(for: spec(plan: targetPlan))
            try expectEqual(refusedTarget?.field, "target")
            try expectEqual(refusedTarget?.step_id, "b")
            try expectEqual(refusedTarget?.step_index, 1)
        }
        tk.run("the service entry point orders top-level, worker and query bounds") {
            let longValue = String(repeating: "q", count: sandboxCheckFilterValueMaxBytes + 1)
            let longTarget = String(repeating: "t", count: PWShmLayout.targetMax + 4)
            let step = PWRunnerProbeStep(step_id: "s",
                sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                    filter: PWRunnerSandboxFilter(kind: "path", value: longValue)),
                attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: longTarget))
            let all = spec(specimenId: String(repeating: "s", count: specimenIdMaxBytes + 1), plan: [step])
            try expectEqual(CWorkerOrchestrator.admissionFailure(for: all)?.field, "specimen_id")
            try expectEqual(CWorkerOrchestrator.admissionFailure(for: spec(plan: [step]))?.field, "target")
            var queryOnly = step; queryOnly.attempt.target = "/etc/hosts"
            try expectEqual(CWorkerOrchestrator.admissionFailure(for: spec(plan: [queryOnly]))?.field,
                            "sandbox_check.filter.value")
            try expectNil(CWorkerOrchestrator.admissionFailure(for: spec()))
        }
    }
}

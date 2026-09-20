import Foundation
@testable import PWRunnerCore

private struct DocumentedLimit: Decodable {
    struct Check: Decodable { let path: String; let kind: String }
    let id: String
    let value: Int
    let checks: [Check]
}
private struct LimitsManifest: Decodable { let limits: [DocumentedLimit] }

func runLimitsContractTests(_ tk: TestKit) {
    tk.group("Documented limits") {
        tk.run("compiled layout and production defaults agree with inventory") {
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let manifest = try JSONDecoder().decode(LimitsManifest.self,
                from: Data(contentsOf: root.appendingPathComponent("docs/limits.json")))
            let worker = CWorkerInput(workerExecutablePath: "unused", policy: "", slots: [])
            let validator = ValidatorClientInput(executablePath: "unused", targetPid: 1, probes: [])
            let rejected = decodeValidatorFrames(Data(repeating: 0xff, count: 1024))
            guard let fault = rejected.fault else { throw TestFailure(message: "invalid frame accepted") }
            let observed: [String: Int] = [
                "policy_source": PWShmLayout.policyBytes - 1,
                "probe_steps": PWShmLayout.maxSteps,
                "policy_parameters": PWShmLayout.maxParams,
                "step_id": PWShmLayout.stepIdMax - 1,
                "attempt_target": PWShmLayout.targetMax - 1,
                "exec_arguments": PWShmLayout.maxArgv - 1,
                "exec_argument": PWShmLayout.argvBytes - 1,
                "parameter_key": PWShmLayout.paramKeyMax - 1,
                "parameter_value": PWShmLayout.paramValueMax - 1,
                "worker_ready_wait": worker.readyByteTimeoutMs,
                "worker_sentinel_wait": worker.sentinelTimeoutMs,
                "worker_exit_grace": worker.exitGraceMs,
                "validator_io_wait": validator.verdictReadTimeoutMs,
                "validator_exit_grace": validator.exitGraceMs,
                "client_rpc_wait": PWRunnerWire.defaultClientTimeoutMs,
                "validator_fault_context": fault.retained_bytes,
                "exec_stream": PWShmLayout.childOutputBytes - 1,
                "worker_diagnostic": PWShmLayout.diagnosticBytes - 1,
                "applied_profile": PWShmLayout.captureBytes,
                "observed_path": PWShmLayout.observedPathMax - 1,
                "attempt_error": PWShmLayout.errorMax - 1,
            ]
            let owned = manifest.limits.filter { row in
                row.checks.contains { $0.kind == "value" && $0.path.hasSuffix("/LimitsContractTests.swift") }
            }
            try expectEqual(Set(owned.map { $0.id }), Set(observed.keys), "every declared Swift owner is exercised")
            for row in owned {
                try expectEqual(observed[row.id], Optional(row.value), row.id)
            }
            try expectEqual(timeoutMsForCWorker(override: nil), worker.sentinelTimeoutMs,
                            "orchestrator and driver defaults agree")
        }
        tk.run("rejected-frame context boundary retains raw prefix and loss metadata") {
            // Independent of limits.json: changing the inventory cannot change this oracle.
            for count in [255, 256, 257] {
                let decoded = decodeValidatorFrames(Data(repeating: 0xff, count: count))
                guard let fault = decoded.fault else { throw TestFailure(message: "invalid frame accepted") }
                try expectTrue(decoded.verdicts.isEmpty)
                try expectEqual(fault.frame_bytes, count)
                try expectEqual(fault.retained_bytes, min(count, 256))
                try expectEqual(fault.context_truncated, count > 256)
                try expectEqual(Data(base64Encoded: fault.context_b64), Data(repeating: 0xff, count: min(count, 256)))
            }
        }
    }
}

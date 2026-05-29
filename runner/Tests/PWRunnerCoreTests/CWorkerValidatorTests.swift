import Foundation
@testable import PWRunnerCore

/*
 * CWorkerValidatorTests — drives runCWorker + runValidator together
 * via CWorker's postApplied hook, the way the Step 6.3c integration
 * in PWRunnerService will. Proves the host-side orchestration shape:
 * worker applies the policy, validator queries the worker_pid while
 * the worker is sandboxed, both children's outputs flow back to the
 * host as a single coherent envelope (attempts + verdicts indexed by
 * step_id).
 *
 * The combined-test bar is intentionally low for this chunk: a single
 * scenario that exercises every wire. Scenario coverage breadth lives
 * in CWorkerTests + validator_batch_mode + runner_c_worker_harness;
 * this file pins the integration handshake itself.
 *
 * Skips cleanly when either binary is missing.
 */

private func repoRootForCV() -> URL {
    return URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
}

private func workerPathForCV() -> String {
    return repoRootForCV()
        .appendingPathComponent("dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner")
        .path
}

private func validatorPathForCV() -> String {
    return repoRootForCV()
        .appendingPathComponent("dist/PolicyWitness.app/Contents/MacOS/sb_api_validator")
        .path
}

private func bothBinariesExist() -> Bool {
    let fm = FileManager.default
    return fm.isExecutableFile(atPath: workerPathForCV())
        && fm.isExecutableFile(atPath: validatorPathForCV())
}

func runCWorkerValidatorTests(_ tk: TestKit) {
    tk.group("CWorker + ValidatorClient orchestration") {
        tk.run("postApplied hook spawns validator against worker_pid; both outputs round-trip") {
            guard bothBinariesExist() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner or sb_api_validator missing; run ./build.sh\n".utf8))
                return
            }

            // Specimen-shaped input. Two steps so the per-step index
            // is exercised; each step pairs an attempt the worker
            // will run with a sandbox_check probe the validator
            // will run.
            let workerInput = CWorkerInput(
                workerExecutablePath: workerPathForCV(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "s_read_etc_hosts",
                                     attemptKind: .fileOpenRead,
                                     target: "/etc/hosts"),
                    CWorkerSlotInput(stepId: "s_net_outbound",
                                     attemptKind: .none,
                                     target: ""),
                ]
            )

            // Validator probes correspond one-to-one with the
            // worker's slots by step_id. PWRunnerService will build
            // these from PWRunnerProbeStep.sandbox_check in Step 6.3c.
            let validatorProbes: [ValidatorProbe] = [
                ValidatorProbe(stepId: "s_read_etc_hosts",
                               operation: "file-read-data",
                               filterType: "PATH",
                               filterValue: "/etc/hosts"),
                ValidatorProbe(stepId: "s_net_outbound",
                               operation: "network-outbound",
                               filterType: "NONE",
                               filterValue: nil),
            ]

            // Captured by the postApplied hook so we can assert on the
            // validator result after runCWorker returns.
            var validatorResult: ValidatorClientResult? = nil

            let workerResult = runCWorker(workerInput) { workerPid in
                // The worker is sandboxed at this point; the validator
                // queries the worker's per-task state via
                // sandbox_check(pid, op, ...). Production code will
                // wrap this in a real test_overrides plumb; the test
                // just inlines it.
                let vIn = ValidatorClientInput(
                    executablePath: validatorPathForCV(),
                    targetPid: workerPid,
                    probes: validatorProbes
                )
                validatorResult = runValidator(vIn)
            }

            // Worker side.
            guard case .success(let workerOut) = workerResult else {
                throw TestFailure(message: "runCWorker failed: \(workerResult)")
            }
            try expectTrue(workerOut.applied, "applied sentinel — hook should have fired")
            try expectTrue(workerOut.done, "done sentinel")
            try expectFalse(workerOut.sentSigkill, "worker should clean-exit")
            try expectEqual(workerOut.slots.count, 2, "slot count")
            // The /etc/hosts read should succeed under (allow default).
            let etcSlot = workerOut.slots.first { $0.stepId == "s_read_etc_hosts" }
            try expectNotNil(etcSlot, "s_read_etc_hosts slot")
            try expectEqual(etcSlot!.rc, Int32(0), "/etc/hosts open succeeded")

            // Validator side.
            guard let vResult = validatorResult else {
                throw TestFailure(message: "validator hook never fired — postApplied not called")
            }
            guard case .success(let vOut) = vResult else {
                throw TestFailure(message: "runValidator failed: \(vResult)")
            }
            try expectEqual(vOut.exitCode, Int32(0), "validator exited cleanly")
            try expectFalse(vOut.sentSigkill, "validator didn't need SIGKILL")
            try expectEqual(vOut.verdicts.count, 2, "one verdict per probe")

            // Verdicts indexed by step_id so the integration code can
            // join attempts + sandbox_checks per step. This is the
            // shape PWRunnerService will assemble into
            // PWRunnerStepResult in Step 6.3c.
            var byStep = [String: ValidatorVerdict]()
            for v in vOut.verdicts {
                if let sid = v.stepId { byStep[sid] = v }
            }
            let etcVerdict = byStep["s_read_etc_hosts"]
            try expectNotNil(etcVerdict, "missing verdict for s_read_etc_hosts")
            try expectEqual(etcVerdict!.outcome, "allow",
                            "(allow default) policy + /etc/hosts read should validate as allow")

            let netVerdict = byStep["s_net_outbound"]
            try expectNotNil(netVerdict, "missing verdict for s_net_outbound")
            try expectEqual(netVerdict!.outcome, "allow",
                            "NONE-filter network-outbound under (allow default) → allow")
        }

        // Smaller assertion: postApplied isn't called when applied
        // never fires (e.g. sandbox_apply fails). The driver's
        // contract says the hook fires the first iteration after we
        // observe applied; if we never observe applied, the hook
        // should never fire.
        tk.run("postApplied hook does not fire when sandbox_apply fails") {
            guard bothBinariesExist() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            // Malformed SBPL — compile fails inside the worker.
            let input = CWorkerInput(
                workerExecutablePath: workerPathForCV(),
                policy: "(garbage not-valid-sbpl",
                slots: [
                    CWorkerSlotInput(stepId: "x", attemptKind: .none, target: "")
                ],
                sentinelTimeoutMs: 1_000
            )
            var hookFiredCount = 0
            let result = runCWorker(input) { _ in hookFiredCount += 1 }

            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker reported setup failure: \(result)")
            }
            try expectFalse(out.applied, "applied should never fire for malformed policy")
            try expectEqual(hookFiredCount, 0,
                            "hook fired \(hookFiredCount) times when applied was never observed")
        }
    }
}

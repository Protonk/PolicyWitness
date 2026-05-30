import Foundation
@testable import PWRunnerCore

/*
 * CWorkerValidatorTests — drives runCWorker + runValidator together
 * via CWorker's postApplied hook, the way CWorkerOrchestrator
 * drives them in production. Proves the host-side orchestration
 * shape: worker applies the policy, validator queries the
 * worker_pid while the worker is sandboxed, both children's outputs
 * flow back to the host as a single coherent envelope (attempts +
 * verdicts indexed by step_id).
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
            // worker's slots by step_id. CWorkerOrchestrator builds
            // these from PWRunnerProbeStep.sandbox_check in production.
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

            // Verdicts indexed by step_id so the orchestrator can
            // join attempts + sandbox_checks per step into the
            // PWRunnerStepResult envelope.
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

        // Driver-contract pin: the hook fires the first iteration
        // AFTER we observe `applied`. This fixture uses malformed
        // SBPL so sandbox_compile_string fails inside the worker;
        // `applied` is never written, so the hook must not run.
        // (We can't easily produce a real sandbox_apply failure from
        // a unit test — apply almost always succeeds when compile
        // does — but the same gating semantics cover that path:
        // applied=0 ⇒ hook never fires.)
        tk.run("postApplied hook does not fire when compile fails") {
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

        // Validator spawn failure: nonexistent binary. Partial should
        // be nil because the failure happens before any FD or process
        // state exists. Post-Step-6.4 audit (PR G #2).
        tk.run("validator spawn failure returns partial=nil") {
            let result = runValidator(ValidatorClientInput(
                executablePath: "/usr/local/no-such-validator-\(getpid())",
                targetPid: getpid(),
                probes: [
                    ValidatorProbe(stepId: "x",
                                   operation: "network-outbound",
                                   filterType: "NONE",
                                   filterValue: nil)
                ]
            ))
            switch result {
            case .failure(let err, let partial):
                guard case .spawnFailed = err else {
                    throw TestFailure(message: "expected spawnFailed, got \(err)")
                }
                try expectNil(partial,
                              "partial should be nil — no process state existed")
            case .success:
                throw TestFailure(message: "expected spawn failure for nonexistent path")
            }
        }

        // Deadlock regression: 256 probes with long path values force
        // > 64 KiB of NDJSON onto stdin while the validator is
        // concurrently emitting verdicts to stdout. Pre-fix, this
        // deadlocked because runValidator wrote-then-read; the
        // validator's stdout filled before stdin drained. The new
        // poll() loop interleaves both directions. The assertion is
        // structural ("everything completed") rather than verdict
        // count because the test target is the I/O harness, not the
        // validator's filter coverage.
        tk.run("256 probes with long paths drive both pipes without deadlock") {
            guard bothBinariesExist() else {
                FileHandle.standardOutput.write(Data("  SKIP  sb_api_validator missing\n".utf8))
                return
            }
            // Padding to push each probe line near 1 KiB → 256 lines ≈ 250 KiB total.
            let longPath = "/etc/" + String(repeating: "x", count: 900)
            var probes: [ValidatorProbe] = []
            for i in 0..<256 {
                probes.append(ValidatorProbe(
                    stepId: "deadlock_\(i)",
                    operation: "file-read-data",
                    filterType: "PATH",
                    filterValue: longPath
                ))
            }
            let result = runValidator(ValidatorClientInput(
                executablePath: validatorPathForCV(),
                targetPid: getpid(),    // unsandboxed → predictable verdict shape
                probes: probes,
                verdictReadTimeoutMs: 10_000,
                exitGraceMs: 2_000
            ))
            switch result {
            case .success(let out):
                try expectEqual(out.verdicts.count, 256,
                                "expected one verdict per probe; pipe interleave didn't drop any")
                try expectEqual(out.exitCode, Int32(0), "validator clean-exited")
                try expectFalse(out.sentSigkill, "no SIGKILL needed")
                try expectTrue(out.rawStdoutBytes > 0, "stdout was drained")
            case .failure(let err, let partial):
                let drained = partial?.rawStdoutBytes ?? 0
                let parsed = partial?.verdicts.count ?? 0
                throw TestFailure(
                    message: "deadlock-regression run failed: \(err); drained=\(drained) parsed=\(parsed)"
                )
            }
        }
    }
}

import Foundation
@testable import PWRunnerCore

/*
 * CWorkerTests — exercises the Swift CWorker driver against the
 * bundled pw-probe-runner binary. Mirrors the scenarios in the C
 * harness suite (tests/suites/runner_c_worker_harness/) but from
 * Swift, so the integration paths the Step 6.3 host wiring will
 * depend on are exercised inside the same process the host runs.
 *
 * Skips cleanly when pw-probe-runner isn't built (e.g. fresh
 * checkout without `./build.sh`). Pin: the worker path resolves
 * relative to the repo root so the test doesn't need an env var.
 */

private func repoRoot() -> URL {
    // This file lives at runner/Tests/PWRunnerCoreTests/CWorkerTests.swift,
    // so the repo root is three levels up.
    return URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()  // PWRunnerCoreTests/
        .deletingLastPathComponent()  // Tests/
        .deletingLastPathComponent()  // runner/
        .deletingLastPathComponent()  // repo root
}

private func workerPath() -> String {
    return repoRoot()
        .appendingPathComponent("dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner")
        .path
}

private func workerExists() -> Bool {
    return FileManager.default.isExecutableFile(atPath: workerPath())
}

func runCWorkerTests(_ tk: TestKit) {
    tk.group("CWorker driver") {
        // ---- happy default-allow: file_open_read /etc/hosts ----------------
        tk.run("happy default-allow: /etc/hosts read succeeds with observed_path") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing; run ./build.sh\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "etc_hosts",
                                     attemptKind: .fileOpenRead,
                                     target: "/etc/hosts")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            try expectTrue(out.readyByteReceived, "pre-apply ready byte not received")
            try expectTrue(out.applied, "applied sentinel never flipped")
            try expectEqual(out.applyRC, Int32(0), "sandbox_apply return code")
            try expectTrue(out.done, "done sentinel never flipped")
            try expectFalse(out.sentSigkill, "harness had to SIGKILL — exit byte didn't work")
            try expectEqual(out.exitCode, Int32(0), "worker exit_code")
            try expectEqual(out.slots.count, 1, "slot count")
            let s = out.slots[0]
            try expectTrue(s.completed, "slot not marked completed")
            try expectEqual(s.rc, Int32(0), "/etc/hosts open should succeed")
            try expectEqual(s.observedPath, "/private/etc/hosts",
                            "F_GETPATH-canonical observed_path")
        }

        // ---- bare (deny default): the bug-report regression ----------------
        tk.run("bare deny-default: worker survives + reports kernel deny") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(deny default)",
                slots: [
                    CWorkerSlotInput(stepId: "denied_read",
                                     attemptKind: .fileOpenRead,
                                     target: "/etc/hosts")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            try expectTrue(out.applied, "applied sentinel never flipped under (deny default)")
            try expectTrue(out.done, "done sentinel never flipped — bug-report regression")
            try expectFalse(out.sentSigkill, "worker should clean-exit under (deny default)")
            try expectEqual(out.exitCode, Int32(0), "clean exit code")
            try expectEqual(out.slots.count, 1)
            let s = out.slots[0]
            try expectTrue(s.completed, "slot not completed")
            try expectEqual(s.rc, Int32(1), "kernel should deny /etc/hosts read")
            // EPERM=1 or EACCES=13 depending on the macOS revision.
            try expectTrue(s.errnoVal == 1 || s.errnoVal == 13,
                           "expected EPERM (1) or EACCES (13), got \(s.errnoVal)")
        }

        // ---- params round-trip: TARGET=/private/etc fires the deny rule -----
        tk.run("params round-trip: TARGET=/private/etc denies /etc/hosts") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)(deny file-read-data (subpath (param \"TARGET\")))",
                params: [
                    CWorkerParam(key: "TARGET", value: "/private/etc")
                ],
                slots: [
                    CWorkerSlotInput(stepId: "etc_hosts_param_target",
                                     attemptKind: .fileOpenRead,
                                     target: "/etc/hosts")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            try expectEqual(out.applyRC, Int32(0),
                            "compile + apply should succeed; if not, sandbox_create_params or " +
                            "sandbox_set_param failed silently")
            try expectTrue(out.applied, "applied sentinel")
            try expectTrue(out.done, "done sentinel")
            try expectEqual(out.slots.count, 1)
            let s = out.slots[0]
            try expectTrue(s.completed, "slot completed")
            try expectEqual(s.rc, Int32(1),
                            "TARGET=/private/etc should make /etc/hosts open fail; " +
                            "rc=0 means the param didn't reach the kernel")
            try expectTrue(s.errnoVal == 1 || s.errnoVal == 13,
                           "expected EPERM/EACCES for param-driven kernel deny, got \(s.errnoVal)")
        }

        // ---- input validation: every bounded field rejects pre-spawn -------
        // Table-driven so a regression in any single field (target,
        // param key, param value) doesn't silently slip through. The
        // worker path is "/nonexistent" because validation has to fire
        // before any FD or process work happens.
        tk.run("oversized step_id rejected pre-spawn") {
            let big = String(repeating: "x", count: PWShmLayout.stepIdMax + 16)
            let result = runCWorker(CWorkerInput(
                workerExecutablePath: "/nonexistent",
                policy: "(version 1)(allow default)",
                slots: [CWorkerSlotInput(stepId: big,
                                         attemptKind: .none,
                                         target: "/tmp")]
            ))
            switch result {
            case .failure(.slotInputTooLong(let field, _, _)):
                try expectEqual(field, "step_id", "wrong field reported for oversized step_id")
            default:
                throw TestFailure(message: "expected slotInputTooLong(step_id), got \(result)")
            }
        }

        tk.run("oversized target rejected pre-spawn") {
            let big = String(repeating: "x", count: PWShmLayout.targetMax + 16)
            let result = runCWorker(CWorkerInput(
                workerExecutablePath: "/nonexistent",
                policy: "(version 1)(allow default)",
                slots: [CWorkerSlotInput(stepId: "ok",
                                         attemptKind: .fileOpenRead,
                                         target: big)]
            ))
            switch result {
            case .failure(.slotInputTooLong(let field, _, _)):
                try expectEqual(field, "target", "wrong field reported for oversized target")
            default:
                throw TestFailure(message: "expected slotInputTooLong(target), got \(result)")
            }
        }

        tk.run("oversized param key rejected pre-spawn") {
            let big = String(repeating: "k", count: PWShmLayout.paramKeyMax + 4)
            let result = runCWorker(CWorkerInput(
                workerExecutablePath: "/nonexistent",
                policy: "(version 1)(allow default)",
                params: [CWorkerParam(key: big, value: "v")],
                slots: [CWorkerSlotInput(stepId: "ok",
                                         attemptKind: .none,
                                         target: "")]
            ))
            switch result {
            case .failure(.paramInputTooLong(let field, _, _)):
                try expectEqual(field, "key", "wrong field reported for oversized param key")
            default:
                throw TestFailure(message: "expected paramInputTooLong(key), got \(result)")
            }
        }

        tk.run("oversized param value rejected pre-spawn") {
            let big = String(repeating: "v", count: PWShmLayout.paramValueMax + 4)
            let result = runCWorker(CWorkerInput(
                workerExecutablePath: "/nonexistent",
                policy: "(version 1)(allow default)",
                params: [CWorkerParam(key: "TARGET", value: big)],
                slots: [CWorkerSlotInput(stepId: "ok",
                                         attemptKind: .none,
                                         target: "")]
            ))
            switch result {
            case .failure(.paramInputTooLong(let field, _, _)):
                try expectEqual(field, "value", "wrong field reported for oversized param value")
            default:
                throw TestFailure(message: "expected paramInputTooLong(value), got \(result)")
            }
        }

        // ---- postApplyHangMs test seam (Step 6.6 / R12b) -------------------
        // Drives the sentinel-timeout window from a real specimen.
        // The host's sentinelTimeoutMs (300 ms here) is shorter than
        // the worker's post-apply hang (800 ms), so `done` never
        // flips inside the deadline. The host then signals
        // exit_requested in spite of done=0; the worker's spin loop
        // observes it AFTER the hang completes and clean-exits.
        // The success criterion is the saw_done=false shape — not a
        // SIGKILL — proving the runner_timeout-class condition is
        // observable on the C-worker path.
        tk.run("postApplyHangMs > sentinelTimeoutMs produces done=false") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "hang_seam",
                                     attemptKind: .fileOpenRead,
                                     target: "/etc/hosts")
                ],
                sentinelTimeoutMs: 300,
                exitGraceMs: 2_000,
                postApplyHangMs: 800
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker reported setup failure: \(result)")
            }
            try expectTrue(out.applied, "applied should still flip — hang is post-apply")
            try expectFalse(out.done,
                            "done should not flip inside 300ms when worker hangs 800ms post-apply")
            // The worker eventually completes — slot was filled — but the
            // host gave up polling and went to exit_requested. The
            // exitGraceMs (2s) is wide enough for the worker to wake
            // from nanosleep, observe exit_requested, and _exit(0).
            try expectFalse(out.sentSigkill,
                            "host should not need SIGKILL — worker exits cleanly post-hang")
            try expectEqual(out.exitCode, Int32(0))
        }
    }
}

import Foundation
@testable import PWRunnerCore

/*
 * CWorkerTests — exercises the Swift CWorker driver against the
 * bundled pw-probe-runner binary. Mirrors the scenarios in the C
 * harness suite (tests/suites/runner_c_worker_harness/) but from
 * Swift, so the integration paths the host depends on are exercised
 * inside the same process the host runs.
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

        // ---- sysctl_read: third curated attempt family -----------------------
        tk.run("sysctl_read under allow-default succeeds") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "sysctl_osrelease",
                                     attemptKind: .sysctlRead,
                                     target: "kern.osrelease")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            try expectTrue(out.applied, "applied sentinel")
            try expectTrue(out.done, "done sentinel")
            try expectFalse(out.sentSigkill, "worker should clean-exit")
            try expectEqual(out.slots.count, 1)
            let s = out.slots[0]
            try expectTrue(s.completed, "slot completed")
            try expectEqual(s.rc, Int32(0), "kern.osrelease sysctl read should succeed")
            try expectEqual(s.errnoVal, Int32(0), "successful sysctl read should not set errno")
        }

        tk.run("sysctl_read under mismatched allow is denied") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(deny default)(allow sysctl-read (sysctl-name \"kern.osversion\"))",
                slots: [
                    CWorkerSlotInput(stepId: "sysctl_osrelease_denied",
                                     attemptKind: .sysctlRead,
                                     target: "kern.osrelease")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            try expectTrue(out.applied, "applied sentinel")
            try expectTrue(out.done, "done sentinel")
            try expectFalse(out.sentSigkill, "worker should clean-exit")
            try expectEqual(out.slots.count, 1)
            let s = out.slots[0]
            try expectTrue(s.completed, "slot completed")
            try expectEqual(s.rc, Int32(1), "kern.osrelease should be denied by the sysctl-name policy")
            try expectTrue(s.errnoVal == 1 || s.errnoVal == 13,
                           "expected EPERM (1) or EACCES (13), got \(s.errnoVal)")
        }

        // ---- many params: ABI cap accommodates real-world profile closures -
        // Real SBPL profile closures bind 100+ derived params once
        // (import "system.sb") and friends are resolved. This test
        // proves the host-side param array writer and the C worker's
        // param-table reader both handle a count well above 16 (the
        // previous cap). The policy doesn't reference all the params
        // — `sandbox_compile_string` accepts unreferenced params
        // silently — so we're testing the wire/abi machinery, not
        // SBPL macro expansion.
        tk.run("many params (128) round-trip through the shm region") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let n = 128
            var params: [CWorkerParam] = []
            params.reserveCapacity(n)
            for i in 0..<n {
                // Distinct keys; values are short so we don't pressure
                // the per-param byte budget. The point is the array
                // length, not the per-entry size.
                params.append(CWorkerParam(key: "PARAM_\(i)", value: "v\(i)"))
            }
            // Policy uses one of the params to also exercise the apply
            // path; the rest are bound but unreferenced. TARGET_0 is
            // /private/etc so /etc/hosts is denied (same shape as the
            // round-trip test above, just buried inside a 128-param
            // dict).
            params[0] = CWorkerParam(key: "TARGET_0", value: "/private/etc")
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)(deny file-read-data (subpath (param \"TARGET_0\")))",
                params: params,
                slots: [
                    CWorkerSlotInput(stepId: "many_params_probe",
                                     attemptKind: .fileOpenRead,
                                     target: "/etc/hosts")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed with \(n) params: \(result)")
            }
            try expectEqual(out.applyRC, Int32(0),
                            "sandbox_apply must succeed with \(n) params; if not, " +
                            "host wrote past the region or worker rejected the count")
            try expectTrue(out.applied, "applied sentinel with \(n) params")
            try expectTrue(out.done, "done sentinel with \(n) params")
            try expectFalse(out.sentSigkill, "worker should clean-exit with \(n) params")
            try expectEqual(out.slots.count, 1)
            let s = out.slots[0]
            try expectTrue(s.completed, "slot completed with \(n) params")
            try expectEqual(s.rc, Int32(1),
                            "TARGET_0=/private/etc inside a \(n)-param dict should still " +
                            "make /etc/hosts open fail; rc=0 means the param wasn't found " +
                            "by the kernel")
        }

        tk.run("over-cap params rejected pre-spawn") {
            // Symmetric guard: exceeding PWShmLayout.maxParams must
            // fail validation, not silently truncate or corrupt the
            // region.
            var params: [CWorkerParam] = []
            for i in 0..<(PWShmLayout.maxParams + 1) {
                params.append(CWorkerParam(key: "K\(i)", value: "v"))
            }
            let result = runCWorker(CWorkerInput(
                workerExecutablePath: "/nonexistent",
                policy: "(version 1)(allow default)",
                params: params,
                slots: [
                    CWorkerSlotInput(stepId: "x",
                                     attemptKind: .fileOpenRead,
                                     target: "/etc/hosts")
                ]
            ))
            guard case .failure(let err) = result else {
                throw TestFailure(message: "expected pre-spawn rejection for over-cap params")
            }
            let msg = String(describing: err)
            try expectContains(msg, "policy params")
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

        // ---- postApplyHangMs test seam -------------------
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

        // ---- exec attempt: happy path (/usr/bin/true) ---------------------------
        // Spawn succeeds, child clean-exits 0, sentinels look exactly
        // like the "no child output" success state.
        tk.run("exec /usr/bin/true under (allow default) → ok, child_pid>0, child_exit_code=0") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_true",
                                     attemptKind: .execSpawn,
                                     target: "/usr/bin/true")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            try expectTrue(out.applied)
            try expectTrue(out.done)
            try expectEqual(out.slots.count, 1)
            let s = out.slots[0]
            try expectTrue(s.completed)
            try expectEqual(s.rc, Int32(0), "/usr/bin/true returns 0")
            try expectEqual(s.errnoVal, Int32(0))
            try expectNotNil(s.childPid)
            try expectTrue((s.childPid ?? 0) > 0, "child_pid should be > 0 on successful spawn")
            try expectEqual(s.childExitCode, Int32(0))
            try expectEqual(s.childTermSignal, Int32(0))
        }

        // ---- exec attempt: non-zero exit (/usr/bin/false) -----------------------
        // Spawn succeeds, child exits 1. Witness honesty: rc reflects
        // the helper's verdict, NOT a sandbox event.
        tk.run("exec /usr/bin/false → exec_failed semantics with child_pid>0, child_exit_code=1") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_false",
                                     attemptKind: .execSpawn,
                                     target: "/usr/bin/false")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            let s = out.slots[0]
            try expectTrue(s.completed)
            try expectEqual(s.rc, Int32(1), "/usr/bin/false exits 1")
            try expectTrue((s.childPid ?? 0) > 0, "spawn should succeed; only the child exited non-zero")
            try expectEqual(s.childExitCode, Int32(1))
            try expectEqual(s.childTermSignal, Int32(0))
        }

        // ---- exec attempt: target missing -----------------------------------
        // posix_spawn returns ENOENT (errno-style return value). The
        // worker never produces a child, so child_pid stays 0 (the
        // sentinel that lets the drift classifier distinguish "sandbox
        // blocked spawn" from "child exited non-zero").
        tk.run("exec /nonexistent → exec_failed with child_pid=0, errno=ENOENT") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_missing",
                                     attemptKind: .execSpawn,
                                     target: "/var/empty/pw_does_not_exist")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            let s = out.slots[0]
            try expectTrue(s.completed)
            try expectEqual(s.rc, Int32(-1), "spawn failure: rc=-1 sentinel")
            try expectEqual(s.errnoVal, Int32(ENOENT))
            try expectEqual(s.childPid, Int32(0),
                            "child_pid must be 0 when spawn failed — drift classifier keys on this")
            try expectEqual(s.childExitCode, Int32(-1),
                            "child_exit_code stays at -1 sentinel when no child ran")
        }

        // ---- exec attempt: spawn blocked by sandbox -------------------------
        // THE LOAD-BEARING PIN. The failure must come from posix_spawn
        // (child_pid==0 + EPERM/EACCES), NOT from pipe()/file_actions
        // setup. If this flips to a different errno or to child_pid>0,
        // the worker is no longer honoring "post-apply syscall surface
        // is minimal" and the witness is unreliable.
        tk.run("exec /usr/bin/true under (deny default) → spawn EPERM/EACCES, child_pid=0") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(deny default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_deny",
                                     attemptKind: .execSpawn,
                                     target: "/usr/bin/true")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            try expectTrue(out.applied,
                "worker must reach sandbox_apply — pre-apply setup must not fail")
            let s = out.slots[0]
            try expectTrue(s.completed)
            try expectEqual(s.childPid, Int32(0),
                "child_pid==0 pins the failure attribution to posix_spawn (not setup)")
            try expectEqual(s.rc, Int32(-1))
            // EPERM (1) or EACCES (13). The kernel doesn't promise
            // which one for sandbox-denied spawn; both are valid.
            let errnoVal = s.errnoVal
            try expectTrue(errnoVal == Int32(EPERM) || errnoVal == Int32(EACCES),
                "expected EPERM or EACCES from sandbox-denied posix_spawn; got errno=\(errnoVal)")
            // The error string should mention posix_spawn so a reader can
            // tell at a glance what was blocked.
            try expectNotNil(s.error)
            try expectTrue((s.error ?? "").contains("posix_spawn"),
                "error string should identify posix_spawn as the failure source")
        }

        // ---- exec argv bounds: count over the cap ---------------------------
        // 16-entry argv table includes argv[0] (target), so up to 15
        // caller-supplied args fit. The 16th args entry must be
        // rejected pre-spawn so an over-long argv never reaches the
        // worker.
        tk.run("exec args count exceeding maxArgv-1 rejected pre-spawn") {
            // Don't need the worker; this rejection happens before spawn.
            let tooManyArgs = (0..<(PWShmLayout.maxArgv)).map { "arg\($0)" }
            try expectEqual(tooManyArgs.count, PWShmLayout.maxArgv,
                            "test setup: should generate exactly maxArgv args (= argsMax + 1)")
            let input = CWorkerInput(
                workerExecutablePath: "/usr/usr/bin/false",  // unused; rejected before spawn
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_too_many_args",
                                     attemptKind: .execSpawn,
                                     target: "/usr/bin/true",
                                     args: tooManyArgs)
                ]
            )
            let result = runCWorker(input)
            guard case .failure(let err) = result else {
                throw TestFailure(message: "expected argv-count rejection; got \(result)")
            }
            guard case .argvCountExceeded = err else {
                throw TestFailure(message: "expected argvCountExceeded; got \(err)")
            }
        }

        // ---- exec argv bounds: per-entry byte length ------------------------
        tk.run("exec args entry exceeding argvBytes rejected pre-spawn") {
            let bigArg = String(repeating: "x", count: PWShmLayout.argvBytes)
            let input = CWorkerInput(
                workerExecutablePath: "/usr/usr/bin/false",
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_arg_too_long",
                                     attemptKind: .execSpawn,
                                     target: "/usr/bin/true",
                                     args: [bigArg])
                ]
            )
            let result = runCWorker(input)
            guard case .failure(let err) = result else {
                throw TestFailure(message: "expected argv-entry rejection; got \(result)")
            }
            guard case .argvEntryTooLong = err else {
                throw TestFailure(message: "expected argvEntryTooLong; got \(err)")
            }
        }

        // ---- exec absolute-path enforcement ---------------------------------
        // Non-absolute exec targets are rejected pre-spawn (bad_request
        // path). Worker is never invoked; the test doesn't need the
        // bundle.
        tk.run("exec target without leading slash rejected pre-spawn") {
            let input = CWorkerInput(
                workerExecutablePath: "/usr/bin/false",
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_relative",
                                     attemptKind: .execSpawn,
                                     target: "usr/bin/true")  // relative
                ]
            )
            let result = runCWorker(input)
            guard case .failure(let err) = result else {
                throw TestFailure(message: "expected absolute-path rejection; got \(result)")
            }
            guard case .execTargetNotAbsolute = err else {
                throw TestFailure(message: "expected execTargetNotAbsolute; got \(err)")
            }
        }

        // ---- exec deadline-fired SIGKILL ------------------------------------
        // A hung helper would otherwise escalate into the host's
        // worker-level sentinel timeout. With a short
        // execChildDeadlineMs the worker bounds the per-exec wait,
        // SIGKILLs the child's process group, and surfaces the
        // deadline-kill cleanly. Pin: outcome=exec_failed,
        // child_term_signal=SIGKILL (9), error mentions deadline.
        tk.run("exec helper hung past deadline → SIGKILL + exec_failed with deadline error") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            guard FileManager.default.isExecutableFile(atPath: "/bin/sleep") else {
                FileHandle.standardOutput.write(Data("  SKIP  /bin/sleep missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_hang",
                                     attemptKind: .execSpawn,
                                     target: "/bin/sleep",
                                     args: ["10"])
                ],
                // Plenty of host budget so the deadline path runs to
                // completion rather than being preempted by the host.
                sentinelTimeoutMs: 30_000,
                exitGraceMs: 5_000,
                execChildDeadlineMs: 500
            )
            let start = Date()
            let result = runCWorker(input)
            let elapsed = Date().timeIntervalSince(start)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            // The whole run must finish well under the host's sentinel
            // budget — proving the deadline + SIGKILL path actually
            // cut the wait, rather than the host SIGKILL'ing the
            // worker.
            try expectTrue(elapsed < 10.0,
                "deadline should fire ~500ms in; total elapsed=\(elapsed)s should be << helper sleep (10s)")
            let s = out.slots[0]
            try expectTrue(s.completed)
            try expectEqual(s.rc, Int32(-1))
            try expectTrue((s.childPid ?? 0) > 0, "spawn succeeded; deadline applies post-spawn")
            try expectEqual(s.childTermSignal, Int32(SIGKILL),
                "deadline kill should arrive as SIGKILL on the child")
            try expectEqual(s.childExitCode, Int32(-1),
                "child_exit_code sentinel when signaled")
            try expectNotNil(s.error)
            try expectTrue((s.error ?? "").contains("deadline"),
                "error should mention the deadline; got \(s.error ?? "nil")")
        }

        // ---- exec deadline kills the whole process group --------------------
        // The worker spawns each exec child as its own process-group leader
        // (POSIX_SPAWN_SETPGROUP) so the deadline path can kill(-pgid) the
        // ENTIRE tree, not just the leader. The sibling test above uses a
        // childless /bin/sleep, so "the grandchild dies too" is asserted
        // nowhere else.
        //
        // Mechanism: the child is a /bin/sh that forks a backgrounded
        // grandchild and then sleeps past the deadline. The grandchild
        // touches a `.gc_started` marker immediately (proving it launched),
        // sleeps past the deadline, then would touch `.survived`. When the
        // worker's deadline fires it kill(-pgid)s the group; a correctly
        // reaped grandchild dies mid-sleep and never writes `.survived`. A
        // leaked grandchild (pgroup kill that only hit the leader) writes
        // `.survived` after its sleep — which this test waits long enough to
        // observe.
        tk.run("exec deadline SIGKILLs the child's whole process group (grandchild reaped)") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            for bin in ["/bin/sh", "/bin/sleep", "/usr/bin/touch"] {
                guard FileManager.default.isExecutableFile(atPath: bin) else {
                    FileHandle.standardOutput.write(Data("  SKIP  \(bin) missing\n".utf8))
                    return
                }
            }

            // Short /tmp paths on purpose: the whole script is one argv
            // entry, capped at PW_SHM_ARGV_BYTES (128 incl. NUL), so a
            // /var/folders temp path would overflow it.
            let pid = ProcessInfo.processInfo.processIdentifier
            let base = "/tmp/pwgc\(pid)"
            let gcStarted = base + "s"   // grandchild launched
            let survived  = base + "v"   // grandchild outlived the deadline (a leak)
            // Empty envp under our spawn means PATH is unset, so every
            // command in the script is an absolute path (paths are clean, so
            // no quoting is needed). The grandchild is the backgrounded
            // subshell; non-interactive sh keeps it in the leader's process
            // group (no job control), which is what makes it a target of
            // kill(-pgid).
            let gcSleepSec = 2
            let leaderSleepSec = 6
            let script =
                "( /usr/bin/touch \(gcStarted); /bin/sleep \(gcSleepSec); /usr/bin/touch \(survived) ) &"
                + " /bin/sleep \(leaderSleepSec)"
            defer {
                try? FileManager.default.removeItem(atPath: gcStarted)
                try? FileManager.default.removeItem(atPath: survived)
            }

            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_pgroup",
                                     attemptKind: .execSpawn,
                                     target: "/bin/sh",
                                     args: ["-c", script])
                ],
                sentinelTimeoutMs: 30_000,
                exitGraceMs: 5_000,
                execChildDeadlineMs: 700
            )
            let start = Date()
            let result = runCWorker(input)
            // Wait until a *leaked* grandchild would have had time to write
            // `.survived` (its sleep + a margin), so an absent marker is a
            // real reap rather than us checking too early.
            let safetyWaitSec = Double(gcSleepSec) + 2.5
            let elapsed = Date().timeIntervalSince(start)
            if elapsed < safetyWaitSec {
                Thread.sleep(forTimeInterval: safetyWaitSec - elapsed)
            }

            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            let s = out.slots[0]
            try expectEqual(s.childTermSignal, Int32(SIGKILL),
                "the leader should be SIGKILL'd at the deadline")
            try expectTrue((s.error ?? "").contains("deadline"),
                "error should mention the deadline; got \(s.error ?? "nil")")
            // Guard against a vacuous pass: the grandchild must actually have
            // launched, or `.survived` being absent proves nothing.
            try expectTrue(FileManager.default.fileExists(atPath: gcStarted),
                "grandchild never launched (.gc_started absent) — test is vacuous, not a real reap")
            // The load-bearing assertion: the grandchild was killed mid-sleep
            // by the process-group SIGKILL, so it never wrote `.survived`.
            try expectTrue(!FileManager.default.fileExists(atPath: survived),
                "grandchild survived the deadline kill — kill(-pgid) leaked a grandchild")
        }

        // ---- exec hermetic environment --------------------------------------
        // The worker passes an empty envp. /usr/bin/env prints the
        // environment one variable per line. Under our spawn the
        // helper sees an empty environment, so stdout is empty.
        tk.run("exec child receives empty environment (envp = {NULL})") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            guard FileManager.default.isExecutableFile(atPath: "/usr/bin/env") else {
                FileHandle.standardOutput.write(Data("  SKIP  /usr/bin/env missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_env",
                                     attemptKind: .execSpawn,
                                     target: "/usr/bin/env")
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            let s = out.slots[0]
            try expectEqual(s.rc, Int32(0))
            // /usr/bin/env with no inherited env should produce no
            // stdout. childStdout reader normalizes empty → nil.
            try expectNil(s.childStdout,
                "exec child should receive empty env; got stdout=\(s.childStdout ?? "nil")")
        }

        // ---- exec stdout/stderr round-trip via /bin/echo --------------------
        // Use /bin/echo as a portable fixture that doesn't require
        // building our own helper for the unit suite. Echo writes its
        // args to stdout followed by a newline; nothing to stderr.
        tk.run("exec /bin/echo round-trips stdout into the slot") {
            guard workerExists() else {
                FileHandle.standardOutput.write(Data("  SKIP  pw-probe-runner missing\n".utf8))
                return
            }
            let input = CWorkerInput(
                workerExecutablePath: workerPath(),
                policy: "(version 1)(allow default)",
                slots: [
                    CWorkerSlotInput(stepId: "exec_echo",
                                     attemptKind: .execSpawn,
                                     target: "/bin/echo",
                                     args: ["hello", "world"])
                ]
            )
            let result = runCWorker(input)
            guard case .success(let out) = result else {
                throw TestFailure(message: "runCWorker failed: \(result)")
            }
            let s = out.slots[0]
            try expectEqual(s.rc, Int32(0))
            try expectEqual(s.childExitCode, Int32(0))
            try expectNotNil(s.childStdout)
            // /bin/echo's exact output is "hello world\n".
            try expectEqual(s.childStdout, "hello world\n")
            // stderr is empty; reader normalizes empty to nil.
            try expectNil(s.childStderr)
        }
    }
}

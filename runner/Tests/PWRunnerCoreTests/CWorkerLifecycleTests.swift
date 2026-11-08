import Darwin
import Foundation
@testable import PWRunnerCore

// Real driver, separately built ABI producer, and narrowly controlled OS calls.
// The fixture never applies a sandbox. These tests establish host observations,
// not policy causes. Required equipment must fail clearly instead of SKIP+pass.
private func lifecycleFixture(_ mode: String, readyMs: Int = 1_000, graceMs: Int = 50,
                              calls: ChildProcessCalls = ChildProcessCalls()) throws -> CWorkerOutput {
    guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
          FileManager.default.isExecutableFile(atPath: path) else {
        throw TestFailure(message: "required PW_LIFECYCLE_WORKER_FIXTURE missing; run tests/run.sh --suite runner_unit")
    }
    let result = runCWorker(CWorkerInput(
        workerExecutablePath: path, policy: mode,
        slots: [CWorkerSlotInput(stepId: "lifecycle", attemptKind: .fileOpenRead, target: "/fixture")],
        readyByteTimeoutMs: readyMs, sentinelTimeoutMs: 100, exitGraceMs: graceMs
    ), processCalls: calls)
    guard case .success(let out) = result else {
        throw TestFailure(message: "fixture driver failed: \(result)")
    }
    // Fault controls may deliberately leave disposition unconfirmed. This
    // independent test-owned cleanup never rewrites the driver's observations.
    var status: Int32 = 0
    let first = Darwin.waitpid(out.workerPid, &status, WNOHANG)
    if first != out.workerPid && !(first == -1 && errno == ECHILD) {
        guard first == 0 || (first == -1 && errno == EINTR) else {
            throw TestFailure(message: "fixture cleanup wait failed: \(errno)")
        }
        let rc = Darwin.kill(out.workerPid, SIGKILL)
        guard rc == 0 || errno == ESRCH else {
            throw TestFailure(message: "fixture cleanup kill failed: \(errno)")
        }
        var cleaned = false
        for _ in 0..<100 {
            let result = Darwin.waitpid(out.workerPid, &status, WNOHANG)
            if result == out.workerPid || (result == -1 && errno == ECHILD) {
                cleaned = true
                break
            }
            usleep(10_000)
        }
        try expectTrue(cleaned, "test-owned fixture was not reaped")
    }
    return out
}

private func checkLifecycleEvidence(_ out: CWorkerOutput, stop: String,
                                reaped: Bool, exit: Int32? = nil, signal: Int32? = nil) throws {
    let classified = classify(workerResult: .success(out), validatorResult: nil, expectedVerdictCount: 0)
    try expectEqual(classified.outcome, NormalizedOutcome.runnerFailed,
                    "completed or incomplete fixture reports with abnormal/unconfirmed disposition must fail without a policy cause")
    try expectEqual(out.pollStopReason, stop)
    try expectEqual(out.reaped, reaped)
    try expectEqual(out.exitCode, exit)
    try expectEqual(out.termSignal, signal)
    try expectEqual(out.exitRequested, true)
    // Exercise the actual production assembler followed by binary writing.
    let decoded = buildWorkerSubprocess(out)
    let bytes = try pwPorcelainEncode(decoded)
    try expectEqual(decoded.poll_stop_reason, stop)
    try expectEqual(decoded.reaped, reaped)
    try expectEqual(decoded.exit_code, exit.map(Int.init))
    try expectEqual(decoded.term_signal, signal.map(Int.init))
    try expectEqual(decoded.exit_requested, true)
    try expectEqual(decoded.ready_byte_received, out.readyByteReceived)
    try expectEqual(decoded.done_observed, out.done)
    try expectEqual(decoded.termination_request?.signal, out.terminationRequest?.signal)
    try expectEqual(decoded.termination_request?.rc, out.terminationRequest?.rc)
    try expectEqual(decoded.termination_request?.errno, out.terminationRequest?.errno)
    try expectEqual(decoded.wait_errors?.map { $0.stage }, out.waitErrors?.map { $0.stage })
    try expectEqual(decoded.wait_errors?.map { $0.rc }, out.waitErrors?.map { $0.rc })
    try expectEqual(decoded.wait_errors?.map { $0.errno }, out.waitErrors?.map { $0.errno })
    if !reaped {
        try expectNil(decoded.exit_code)
        try expectNil(decoded.term_signal)
    }
    try expectTrue(bytes.starts(with: Data("PWP1".utf8)))
}

private func checkCompletedReport(_ out: CWorkerOutput) throws {
    try expectTrue(out.applied)
    try expectTrue(out.done)
    try expectEqual(out.applyRC, Int32(0))
    try expectEqual(out.slots.count, 1)
    try expectTrue(out.slots[0].completed)
    try expectEqual(out.slots[0].stepId, "lifecycle")
    try expectEqual(out.slots[0].rc, Int32(0))
    try expectEqual(out.slots[0].observedPath, "fixture-observation")
    try expectFalse(buildWorkerSubprocess(out).partial_steps)
}

// Also invoked in a disposable host copy with final acknowledgement
// reconciliation removed. Neither positive case may pass that mutation.
func runCWorkerReapedAcknowledgementControls(_ tk: TestKit) {
    for scenario in ["clean", "signal", "ownership_lost"] {
        tk.run("unseen acknowledgement at confirmed reap: \(scenario)") {
            guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
                throw TestFailure(message: "required lifecycle fixture missing; run runner_unit")
            }
            let gate = "/tmp/pw-reap-ack-" + UUID().uuidString
            try expectFalse(FileManager.default.fileExists(atPath: gate))
            var knownPID: pid_t = 0
            defer {
                try? FileManager.default.removeItem(atPath: gate)
                // Independent cleanup never uses the injected wait boundary.
                if knownPID > 0 {
                    var status: Int32 = 0
                    var rc: pid_t
                    repeat { rc = Darwin.waitpid(knownPID, &status, WNOHANG) } while rc < 0 && errno == EINTR
                    if rc == 0 {
                        _ = Darwin.kill(knownPID, SIGKILL)
                        repeat { rc = Darwin.waitpid(knownPID, &status, 0) } while rc < 0 && errno == EINTR
                    }
                }
            }
            var hookFinished = false, postHookChecked = false, faultInjected = false
            var gatedWait = false, gateFailed = false, watchdogExpired = false
            var calls = ChildProcessCalls()
            calls.wait = { pid, status, options in
                knownPID = pid
                if !hookFinished { return Darwin.waitpid(pid, status, options) }
                if !postHookChecked {
                    postHookChecked = true
                    return Darwin.waitpid(pid, status, options)
                }
                if scenario == "ownership_lost" && !faultInjected {
                    faultInjected = true
                    errno = EIO
                    return -1
                }
                // The release and the host's last ack/done samples precede
                // this wait. Only now let the fixture acknowledge and exit.
                // In the negative ownership case this is the cleanup wait,
                // after the driver has consumed the poll EIO.
                gatedWait = true
                guard FileManager.default.createFile(atPath: gate, contents: Data()) else {
                    gateFailed = true; errno = EIO; return -1
                }
                let deadline = DispatchTime.now().uptimeNanoseconds + 2_000_000_000
                repeat {
                    let rc = Darwin.waitpid(pid, status, WNOHANG)
                    if rc == pid || (rc < 0 && errno != EINTR) { return rc }
                    usleep(1000)
                } while DispatchTime.now().uptimeNanoseconds < deadline
                watchdogExpired = true
                errno = ETIMEDOUT
                return -1
            }
            let fatal = scenario == "signal"
            let result = runCWorker(CWorkerInput(workerExecutablePath: fixture,
                policy: (fatal ? "reap_ack_signal|" : "reap_ack_clean|") + gate,
                slots: [CWorkerSlotInput(stepId: "s", attemptKind: .fileOpenRead, target: "/etc/hosts")],
                sentinelTimeoutMs: 1_000, exitGraceMs: 100), processCalls: calls,
                postApplied: { _ in hookFinished = true })
            guard case .success(let out) = result else { throw TestFailure(message: "fixture driver failed: \(result)") }
            try expectTrue(hookFinished && postHookChecked && gatedWait && !gateFailed && !watchdogExpired,
                           "acknowledgement must be gated inside the final native wait")
            try expectEqual(faultInjected, scenario == "ownership_lost")
            try expectEqual(out.pollStopReason, faultInjected ? "wait_error" : "child_reaped")
            try expectEqual(out.reaped, true)
            try expectEqual(out.exitCode, fatal ? nil : 0)
            try expectEqual(out.termSignal, fatal ? SIGTERM : nil)
            try expectNil(out.terminationRequest)
            try expectEqual(out.collectionBasis, "after_confirmed_reap")
            try expectEqual(out.waitErrors?.map { $0.errno }, faultInjected ? [EIO] : [])
            try expectTrue(out.applied && out.proceedSet && out.proceedObserved)
            try expectEqual(out.done, !fatal)
            try expectEqual(out.phases[0].completed, !fatal)
            try expectEqual(out.slots[0].completed, !fatal)

            // Constructed native query data isolates phase qualification;
            // this fixture does not apply a sandbox or perform the attempt.
            let query = PWRunnerProbeStep(step_id: "s", sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
                attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts"))
            let validator = ValidatorOutput(validatorPid: 7, verdicts: [ValidatorVerdict(stepId: "s",
                operation: "file-read-data", filterType: "PATH", filterTypeId: 1, filterValue: "/etc/hosts",
                rc: 0, errnoVal: 0, outcome: "allow", rawLine: "constructed lifecycle control")],
                exitCode: 0, reaped: true, waitErrors: [], expectedProbes: [ValidatorProbe(stepId: "s",
                    operation: "file-read-data", filterType: "PATH", filterValue: "/etc/hosts")])
            let ordering = buildOrdering(out, validatorOutput: validator, hasQueries: true)
            let steps = buildStepResults(probePlan: [query], queryPlan: planValidatorQueries([query]),
                workerOutput: out, validatorOutput: validator, ordering: ordering)
            try expectEqual(out.proceedOwnershipEstablished, !faultInjected,
                           "confirmed reap must recover unseen acknowledgement only with intact ownership")
            try expectEqual(ordering.chainEstablished, !faultInjected)
            try expectEqual(steps[0].comparison?.order, faultInjected ? "unestablished" : "query_first")
            try expectEqual(steps[0].comparison?.observation, fatal ? "unavailable" : "succeeded")
            let classification = classify(workerResult: result, validatorResult: .success(validator), expectedVerdictCount: 1)
            try expectEqual(classification.outcome, (fatal || faultInjected) ? NormalizedOutcome.runnerFailed : NormalizedOutcome.finished)
            let subprocess = buildWorkerSubprocess(out)
    let encoded = try pwPorcelainEncode(subprocess)
            try expectEqual(subprocess.term_signal, fatal ? Int(SIGTERM) : nil)
            try expectEqual(subprocess.done_observed, !fatal)
            var status: Int32 = 0
            try expectEqual(Darwin.waitpid(out.workerPid, &status, WNOHANG), -1)
            try expectEqual(errno, ECHILD, "the driver must have independently reaped its child")
        }
    }
}

/// Records the bound and measured duration of each production readability wait.
private final class ReadinessWaits {
    private(set) var bounds: [UInt64] = []
    private(set) var durations: [UInt64] = []
    var calls: ChildProcessCalls {
        var calls = ChildProcessCalls()
        calls.waitReadable = { [unowned self] fd, ns in
            let start = clock_gettime_nsec_np(CLOCK_UPTIME_RAW)
            waitReadableNs(fd, ns)
            self.durations.append(clock_gettime_nsec_np(CLOCK_UPTIME_RAW) - start)
            self.bounds.append(ns)
        }
        return calls
    }
}

/// The fixture's input exceeds the pipe buffer, so policy delivery, and with it
/// the start of the readiness wait, completes only while the fixture is
/// reading; its ready-byte delay starts at its EOF.
private func runReadinessWaitControls(_ tk: TestKit) {
    let padding = String(repeating: "x", count: 200_000)
    tk.run("a ready byte written 3 ms after delivery is received within a 6 ms tolerance, before the 10 ms poll period ends") {
        // Delay plus tolerance stays below one 10 ms poll period, which a wait
        // that slept through the period could not record.
        let delayMs: UInt64 = 3, toleranceMs: UInt64 = 6
        let waits = ReadinessWaits()
        let out = try lifecycleFixture("ready_after_\(delayMs)\n" + padding, calls: waits.calls)
        guard let ready = out.readyWait, let elapsed = ready.elapsed_ms else {
            throw TestFailure(message: "missing ready_wait elapsed time: \(String(describing: out.readyWait))")
        }
        try expectEqual(ready.stop, "received"); try expectTrue(out.readyByteReceived)
        try expectEqual(ready.budget_ms, 1_000); try expectEqual(ready.clock_fault, false)
        try expectTrue(elapsed <= delayMs + toleranceMs,
                       "elapsed \(elapsed) ms for a \(delayMs) ms delay; waits \(waits.bounds) ns lasted \(waits.durations) ns")
        try expectEqual(waits.bounds.first, UInt64(10_000_000), "the byte must arrive during a wait: \(waits.bounds)")
        try expectTrue(waits.durations.last! < waits.bounds.last!,
                       "the receiving read must follow a wait that returned on readability: \(waits.durations) ns")
    }
    tk.run("a ready byte that never arrives ends the wait at its allowance") {
        let budgetMs = 60, toleranceMs: UInt64 = 12
        let waits = ReadinessWaits()
        let out = try lifecycleFixture("ready_never\n" + padding, readyMs: budgetMs, calls: waits.calls)
        guard let ready = out.readyWait, let elapsed = ready.elapsed_ms else {
            throw TestFailure(message: "missing ready_wait elapsed time: \(String(describing: out.readyWait))")
        }
        try expectEqual(ready.stop, "deadline"); try expectFalse(out.readyByteReceived)
        try expectEqual(ready.budget_ms, budgetMs); try expectEqual(ready.clock_fault, false)
        try expectTrue(elapsed >= UInt64(budgetMs) && elapsed <= UInt64(budgetMs) + toleranceMs,
                       "elapsed \(elapsed) ms must sit on the \(budgetMs) ms allowance")
        // An open, silent pipe never makes a wait return early, so the passes are
        // bounded by allowance / period, not by how often a wait can return.
        try expectTrue(waits.bounds.count <= budgetMs / 10 + 2 && waits.bounds.allSatisfy { $0 <= 10_000_000 },
                       "waits \(waits.bounds) ns lasted \(waits.durations) ns")
    }
}

private func unwrap<T>(_ value: T?, _ what: String = "value", file: StaticString = #file, line: UInt = #line) throws -> T {
    guard let value else { throw TestFailure(message: "missing \(what) (at \(file):\(line))") }
    return value
}

/// Records each production exit wait's outcome and every sleep requested after
/// the first exit wait, which in these single-worker runs are the grace sleeps.
private final class GraceRecorder {
    private(set) var outcomes: [ExitWatchOutcome] = []
    private(set) var watchedFDs: Set<Int32> = []
    private(set) var graceSleeps: [UInt64] = []
    var calls: ChildProcessCalls {
        var calls = ChildProcessCalls()
        calls.sleep = { [unowned self] ns in
            if !self.outcomes.isEmpty { self.graceSleeps.append(ns) }
            sleepNs(ns)
        }
        calls.waitExit = { [unowned self] watch, ns in
            self.watchedFDs.insert(watch.fd)
            let outcome = waitExitNs(watch, ns)
            self.outcomes.append(outcome)
            return outcome
        }
        return calls
    }
}

/// Virtual time for the injected exit-wait controls: the clock advances only by
/// the requested length of each sleep, readability wait and timed-out exit
/// wait, so pass counts follow allowance / period exactly. Each call also takes
/// real time (at most 1 ms, or until the pipe is readable) so the child makes
/// progress. `outcome` chooses each exit wait's result by call index.
private final class InjectedExitWaits {
    var now: UInt64 = 1_000_000_000_000
    let outcome: (Int) -> ExitWatchOutcome
    private(set) var exitWaits: [UInt64] = []
    private(set) var graceSleeps: [UInt64] = []
    init(_ outcome: @escaping (Int) -> ExitWatchOutcome) { self.outcome = outcome }
    var calls: ChildProcessCalls {
        var calls = ChildProcessCalls()
        calls.clock = { [unowned self] in self.now }
        calls.sleep = { [unowned self] ns in
            if !self.exitWaits.isEmpty { self.graceSleeps.append(ns) }
            self.now += ns
            sleepNs(min(ns, 1_000_000))
        }
        calls.waitReadable = { [unowned self] fd, ns in
            self.now += ns
            waitReadableNs(fd, ns)
        }
        calls.waitExit = { [unowned self] _, ns in
            let result = self.outcome(self.exitWaits.count)
            self.exitWaits.append(ns)
            if result == .timedOut {
                self.now += ns
                sleepNs(1_000_000)
            }
            return result
        }
        return calls
    }
}

/// The grace wait between waitpid samples waits for the ready pipe's hangup.
private func runExitWaitControls(_ tk: TestKit) {
    tk.run("a worker that exits on the exit request is reaped by the sample after its hangup, within 3 ms") {
        let recorder = GraceRecorder()
        let out = try lifecycleFixture("complete_exit_0", calls: recorder.calls)
        try checkCompletedReport(out)
        try expectEqual(out.pollStopReason, "done"); try expectEqual(out.reaped, true)
        try expectEqual(out.exitCode, Int32(0)); try expectNil(out.termSignal)
        try expectNil(out.terminationRequest)
        let grace = try unwrap(out.graceWait)
        try expectEqual(grace.stop, "reaped_during_grace"); try expectEqual(out.graceEnd, "reaped_during_grace")
        try expectEqual(grace.clock_fault, false)
        let elapsed = try unwrap(grace.elapsed_ms)
        try expectTrue(elapsed <= 3, "elapsed \(elapsed) ms; exit waits \(recorder.outcomes), grace sleeps \(recorder.graceSleeps) ns")
        try expectEqual(recorder.outcomes, [.notified], "one exit wait, ended by the hangup")
        try expectEqual(recorder.watchedFDs.count, 1); try expectTrue(recorder.watchedFDs.allSatisfy { $0 >= 0 })
        try expectTrue(recorder.graceSleeps.allSatisfy { $0 == HostWaitClock.exitSettleNs },
                       "only settle sleeps may follow the hangup: \(recorder.graceSleeps)")
    }
    tk.run("a hangup before exit is followed by ten 100 µs settle sleeps, then 10 ms sleeps, then the reap") {
        let recorder = GraceRecorder()
        let out = try lifecycleFixture("complete_linger", graceMs: 1_000, calls: recorder.calls)
        try checkCompletedReport(out)
        try expectEqual(out.pollStopReason, "done"); try expectEqual(out.reaped, true)
        try expectEqual(out.exitCode, Int32(0)); try expectNil(out.termSignal)
        try expectNil(out.terminationRequest)
        let grace = try unwrap(out.graceWait)
        try expectEqual(grace.stop, "reaped_during_grace")
        let elapsed = try unwrap(grace.elapsed_ms)
        try expectTrue(elapsed >= 29, "the fixture lingers 30 ms after its hangup: elapsed \(elapsed) ms")
        try expectEqual(recorder.outcomes, [.notified], "no exit wait follows a notification")
        let sleeps = recorder.graceSleeps
        try expectEqual(Array(sleeps.prefix(HostWaitClock.exitSettleSleeps)),
                        Array(repeating: HostWaitClock.exitSettleNs, count: HostWaitClock.exitSettleSleeps), "\(sleeps)")
        let polls = sleeps.dropFirst(HostWaitClock.exitSettleSleeps)
        try expectTrue(!polls.isEmpty && polls.allSatisfy { $0 == 10_000_000 }, "then the 10 ms poll until the reap: \(sleeps)")
    }
    tk.run("exit waits that always time out end the grace by exhaustion and SIGKILL at the allowance") {
        let control = InjectedExitWaits { _ in .timedOut }
        let out = try lifecycleFixture("complete_hang", calls: control.calls)
        try checkCompletedReport(out)
        try checkLifecycleEvidence(out, stop: "done", reaped: true, signal: SIGKILL)
        let grace = try unwrap(out.graceWait)
        try expectEqual(grace.stop, "exhausted"); try expectEqual(grace.elapsed_ms, UInt64(50))
        try expectEqual(control.exitWaits, Array(repeating: UInt64(10_000_000), count: 50 / 10), "allowance / poll period")
        try expectEqual(control.graceSleeps, [], "a timed-out exit wait is the pass; no sleep follows it")
        try expectEqual(out.terminationRequest?.signal, SIGKILL); try expectEqual(out.terminationRequest?.rc, 0)
        try expectEqual(out.waitErrors?.count, 0)
    }
    tk.run("an unusable exit wait falls back to the 10 ms sleeping poll for the rest of the grace") {
        let control = InjectedExitWaits { _ in .unusable }
        let out = try lifecycleFixture("complete_hang", calls: control.calls)
        try checkCompletedReport(out)
        try checkLifecycleEvidence(out, stop: "done", reaped: true, signal: SIGKILL)
        let grace = try unwrap(out.graceWait)
        try expectEqual(grace.stop, "exhausted"); try expectEqual(grace.elapsed_ms, UInt64(50))
        try expectEqual(control.exitWaits.count, 1, "the watch is abandoned after the first unusable wait")
        try expectEqual(control.graceSleeps, Array(repeating: UInt64(10_000_000), count: 50 / 10), "allowance / poll period")
        try expectEqual(out.terminationRequest?.signal, SIGKILL); try expectEqual(out.terminationRequest?.rc, 0)
    }
}

func runCWorkerLifecycleTests(_ tk: TestKit) {
    tk.group("CWorker exit grace waits for the worker's exit") {
        runExitWaitControls(tk)
    }
    tk.group("CWorker readiness wait on the ready pipe") {
        runReadinessWaitControls(tk)
    }
    tk.group("CWorker host lifecycle observations") {
        runCWorkerReapedAcknowledgementControls(tk)
        tk.run("completed report followed by cleanup kill is not sentinel expiry") {
            let out = try lifecycleFixture("complete_hang")
            try checkCompletedReport(out)
            try checkLifecycleEvidence(out, stop: "done", reaped: true, signal: SIGKILL)
            try expectEqual(out.terminationRequest?.signal, SIGKILL)
            try expectEqual(out.terminationRequest?.rc, 0)
            try expectNil(out.terminationRequest?.errno)
            try expectEqual(out.waitErrors?.count, 0)
        }
        tk.run("completed report survives independent nonzero exit") {
            let out = try lifecycleFixture("complete_exit_17")
            try checkCompletedReport(out)
            try checkLifecycleEvidence(out, stop: "done", reaped: true, exit: 17)
            try expectNil(out.terminationRequest)
        }
        tk.run("completed report survives independent signal") {
            let out = try lifecycleFixture("complete_signal")
            try checkCompletedReport(out)
            try checkLifecycleEvidence(out, stop: "done", reaped: true, signal: SIGTERM)
            try expectNil(out.terminationRequest)
        }
        tk.run("done and cleanup termination cannot publish a coarse apply-failure scalar") {
            let out = try lifecycleFixture("reported_failure_hang")
            try expectFalse(out.applied)
            try expectTrue(out.done)
            // This ABI fixture writes apply_rc=-1 and done, but publishes no
            // native failure cell. Preserve done/cleanup; withhold attribution.
            try expectEqual(out.applyRC,Int32(0))
            try expectEqual(out.applyErrno,Int32(0))
            try expectEqual(out.workerEvidence?.failure_state,"absent")
            try expectNil(out.workerEvidence?.failure)
            let application=actorApplicationAssessment(mode:"apply",launched:true,applied:false,
                evidence:out.workerEvidence,authority:out.authoritySetup)
            try expectEqual(application.state,"unobserved")
            try expectEqual(application.basis,"no_eligible_apply_publication")
            let classified=classify(workerResult:.success(out),validatorResult:nil,expectedVerdictCount:0)
            try expectEqual(classified.outcome,NormalizedOutcome.runnerFailed)
            try expectContains(classified.error ?? "","without an observed application")
            try expectFalse(out.slots[0].completed)
            try checkLifecycleEvidence(out, stop: "done", reaped: true, signal: SIGKILL)
            try expectEqual(out.terminationRequest?.rc, 0)
        }
        tk.run("failed kill permits only nonblocking reap and no invented status") {
            var calls = ChildProcessCalls()
            var killRequested = false
            var finalOptions: [Int32] = []
            calls.kill = { _, _ in killRequested = true; errno = EPERM; return -1 }
            calls.wait = { pid, status, options in
                if killRequested {
                    finalOptions.append(options)
                    // Avoid hanging even under a regression to blocking wait.
                    if options == 0 { status.pointee = 0; errno = EINTR; return -1 }
                }
                return Darwin.waitpid(pid, status, options)
            }
            let start = Date()
            let out = try lifecycleFixture("complete_hang", calls: calls)
            try expectTrue(Date().timeIntervalSince(start) < 3, "failed kill did not return promptly")
            try checkCompletedReport(out)
            try checkLifecycleEvidence(out, stop: "done", reaped: false)
            try expectEqual(out.terminationRequest?.rc, -1)
            try expectEqual(out.terminationRequest?.errno, EPERM)
            try expectEqual(finalOptions, [WNOHANG])
            try expectEqual(out.waitErrors?.count, 0)
        }
        tk.run("successful kill followed by failed reap does not decode wait storage") {
            var calls = ChildProcessCalls()
            calls.wait = { pid, status, options in
                if options == 0 { status.pointee = 0; errno = ECHILD; return -1 }
                return Darwin.waitpid(pid, status, options)
            }
            let out = try lifecycleFixture("complete_hang", calls: calls)
            try checkCompletedReport(out)
            try checkLifecycleEvidence(out, stop: "done", reaped: false)
            try expectEqual(out.terminationRequest?.rc, 0)
            try expectEqual(out.waitErrors?.map { $0.stage }, ["after_termination"])
            try expectEqual(out.waitErrors?.map { $0.errno }, [ECHILD])
        }
        tk.run("interrupted grace reap recovers and retains the interruption") {
            var calls = ChildProcessCalls()
            var interrupted = false
            calls.wait = { pid, status, options in
                if !interrupted { interrupted = true; status.pointee = 0; errno = EINTR; return -1 }
                return Darwin.waitpid(pid, status, options)
            }
            let out = try lifecycleFixture("complete_exit_17", calls: calls)
            try checkCompletedReport(out)
            try checkLifecycleEvidence(out, stop: "done", reaped: true, exit: 17)
            try expectNil(out.terminationRequest)
            try expectEqual(out.waitErrors?.map { $0.stage }, ["exit_grace"])
            try expectEqual(out.waitErrors?.map { $0.errno }, [EINTR])
        }
        tk.run("repeated EINTR returns with finite attempts and unconfirmed status") {
            var calls = ChildProcessCalls()
            var waitCalls = 0
            calls.wait = { _, status, _ in
                waitCalls += 1
                status.pointee = 0
                errno = EINTR
                return -1
            }
            let out = try lifecycleFixture("complete_hang", calls: calls)
            try checkCompletedReport(out)
            try checkLifecycleEvidence(out, stop: "done", reaped: false)
            try expectEqual(waitCalls, 4, "three grace attempts, then one final attempt")
            try expectEqual(out.waitErrors?.map { $0.stage },
                            ["exit_grace", "exit_grace", "exit_grace", "after_termination"])
            try expectEqual(out.waitErrors?.map { $0.errno }, [EINTR, EINTR, EINTR, EINTR])
            try expectEqual(out.terminationRequest?.rc, 0)
        }
        for mode in ["complete_hang", "no_report_hang"] {
            tk.run("ECHILD stops \(mode) waits without signaling an unowned PID") {
                var calls = ChildProcessCalls()
                var killCalls = 0
                calls.wait = { _, status, _ in status.pointee = 0; errno = ECHILD; return -1 }
                calls.kill = { _, _ in killCalls += 1; errno = EPERM; return -1 }
                let out = try lifecycleFixture(mode, calls: calls)
                let completed = mode == "complete_hang"
                if completed { try checkCompletedReport(out) }
                try expectEqual(out.done, completed)
                try checkLifecycleEvidence(out, stop: completed ? "done" : "wait_error", reaped: false)
                try expectNil(out.terminationRequest)
                try expectEqual(killCalls, 0)
                try expectEqual(out.waitErrors?.map { $0.stage }, [completed ? "exit_grace" : "poll"])
                try expectEqual(out.waitErrors?.map { $0.errno }, [ECHILD])
            }
        }
        tk.run("poll failure survives successful cleanup without claiming deadline expiry") {
            var calls = ChildProcessCalls()
            var failed = false
            calls.wait = { pid, status, options in
                if !failed { failed = true; errno = EIO; return -1 }
                return Darwin.waitpid(pid, status, options)
            }
            let out = try lifecycleFixture("no_report_hang", calls: calls)
            try checkLifecycleEvidence(out, stop: "wait_error", reaped: true, signal: SIGKILL)
            try expectFalse(out.done)
            try expectEqual(out.terminationRequest?.rc, 0)
            try expectEqual(out.waitErrors?.map { $0.stage }, ["poll"])
            try expectEqual(out.waitErrors?.map { $0.errno }, [EIO])
        }
    }
}

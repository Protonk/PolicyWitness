import Darwin
import Foundation
@testable import PWRunnerCore

// The ABI fixture applies no sandbox. A gate lets the test release its final
// publication inside the host's actual wait/sleep boundary. These controls
// establish decisions and ownership, not native performance or policy causes.
private final class FinalWaitControl {
    let gate = "/tmp/pw-final-" + UUID().uuidString
    let scenario: String
    let phaseCount: Int
    var collections = 0
    var pid: pid_t = 0
    var waits: [UInt64] = []
    var sleeps: [UInt64] = []
    var outcomes: [ExitWatchOutcome] = []
    var waitBeforeFinalCollection = false
    var gateFailed = false
    var gateOpened = false
    var notified = false
    var ownedChecksAfterNotification = 0
    var now: UInt64 = 1_000_000_000_000
    var clockFailed = false

    init(_ scenario: String, phases: Int = 1) {
        self.scenario = scenario
        phaseCount = phases
    }

    var controlledTime: Bool { scenario == "deadline" || scenario == "clock_failure" }

    func openGate() {
        guard !gateOpened else { return }
        gateOpened = true
        if !FileManager.default.createFile(atPath: gate, contents: Data()) { gateFailed = true; return }
        let until = DispatchTime.now().uptimeNanoseconds + 2_000_000_000
        while !FileManager.default.fileExists(atPath: gate + ".settled") {
            if DispatchTime.now().uptimeNanoseconds >= until { gateFailed = true; return }
            usleep(1000)
        }
    }

    var calls: ChildProcessCalls {
        var calls = ChildProcessCalls()
        if controlledTime {
            calls.clock = { [unowned self] in self.clockFailed ? nil : self.now }
        }
        calls.waitReadable = { [unowned self] fd, ns in
            waitReadableNs(fd, ns)
            if self.controlledTime { self.now += ns }
        }
        calls.wait = { [unowned self] pid, status, options in
            self.pid = pid
            if self.notified { self.ownedChecksAfterNotification += 1 }
            return Darwin.waitpid(pid, status, options)
        }
        calls.waitExit = { [unowned self] watch, ns in
            // Grace waits request 10 ms; the sentinel requests at most 2 ms.
            // These fixtures finish well before the grace's last partial wait.
            guard ns <= 2_000_000 else { return waitExitNs(watch, ns) }
            self.waitBeforeFinalCollection = self.waitBeforeFinalCollection || self.collections != self.phaseCount
            self.waits.append(ns)
            let outcome: ExitWatchOutcome
            if self.controlledTime {
                self.now += ns
                if self.scenario == "clock_failure" { self.clockFailed = true }
                outcome = .timedOut
            } else if self.scenario == "unusable" {
                outcome = .unusable
            } else if self.scenario == "interrupted" && self.waits.count == 1 {
                // waitExitNs maps EINTR to an early timed-out pass. No fixture
                // event or extra allowance is supplied by that return.
                outcome = .timedOut
            } else {
                if self.scenario != "early_hangup" { self.openGate() }
                if ["exit", "no_done", "interrupted"].contains(self.scenario) {
                    // Establish an already-readable pipe independently. This
                    // is a decision control, not a timed exit-latency claim.
                    waitReadableNs(watch.fd, 1_000_000_000)
                }
                outcome = waitExitNs(watch, ns)
            }
            self.outcomes.append(outcome)
            if outcome == .notified { self.notified = true }
            return outcome
        }
        calls.sleep = { [unowned self] ns in
            if self.collections == self.phaseCount && ns <= 2_000_000 {
                self.sleeps.append(ns)
                if self.scenario == "unusable" || self.scenario == "missing_pipe" ||
                    (self.scenario == "early_hangup" && self.notified) { self.openGate() }
            }
            if self.controlledTime { self.now += ns }
            sleepNs(self.controlledTime ? min(ns, 1_000_000) : ns)
        }
        return calls
    }

    func run() throws -> CWorkerOutput {
        guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
              FileManager.default.isExecutableFile(atPath: path) else {
            throw TestFailure(message: "required lifecycle fixture missing; run tests/run.sh --suite runner_unit")
        }
        defer {
            try? FileManager.default.removeItem(atPath: gate)
            try? FileManager.default.removeItem(atPath: gate + ".settled")
            // Independent cleanup owns the child if a faulty driver leaves it.
            if pid > 0 {
                var status: Int32 = 0
                var rc: pid_t
                repeat { rc = Darwin.waitpid(pid, &status, WNOHANG) } while rc < 0 && errno == EINTR
                if rc == 0 {
                    _ = Darwin.kill(pid, SIGKILL)
                    repeat { rc = Darwin.waitpid(pid, &status, 0) } while rc < 0 && errno == EINTR
                }
            }
        }
        let mode: String
        switch scenario {
        case "no_done": mode = "final_wait_no_done"
        case "early_hangup": mode = "final_wait_early_hangup"
        case "missing_pipe": mode = "final_wait_late_ready"
        case "linger", "unusable": mode = "final_wait_linger"
        default: mode = "final_wait_exit"
        }
        let slots = (0..<phaseCount).map {
            CWorkerSlotInput(stepId: "final-\($0)", attemptKind: .fileOpenRead, target: "/fixture")
        }
        let phases = (0..<phaseCount).map { CWorkerPhaseInput(firstSlot: $0, endSlot: $0 + 1) }
        let result = runCWorker(CWorkerInput(workerExecutablePath: path, policy: mode + "|" + gate,
            slots: slots, phases: phases, readyByteTimeoutMs: scenario == "missing_pipe" ? 0 : 1_000,
            sentinelTimeoutMs: controlledTime ? 50 : 1_000, exitGraceMs: 100), processCalls: calls,
            phaseBoundary: { [unowned self] _, _ in self.collections += 1 })
        guard case .success(let out) = result else { throw TestFailure(message: "fixture driver failed: \(result)") }
        try expectEqual(collections, phaseCount, "all declared collections must be reached")
        try expectFalse(waitBeforeFinalCollection, "exit notifications cannot replace an intermediate arrival wait")
        try expectFalse(gateFailed, "the test gate and its independent receipt must complete")
        try expectTrue(out.reaped == true, "the driver's own observation must establish reap")
        try expectTrue(out.proceedSet, "the final phase must be released before final waiting")
        return out
    }
}

func runCWorkerFinalWaitTests(_ tk: TestKit) {
    tk.group("ordinary final completion uses the retained pipe") {
        for phases in [1, 2] {
            tk.run("exit wakes the final wait after \(phases) collections without a timer sleep") {
                let control = FinalWaitControl("exit", phases: phases)
                let out = try control.run()
                try expectTrue(!control.waits.isEmpty && control.notified)
                try expectEqual(control.sleeps, [])
                try expectEqual(out.pollStopReason, "done")
                try expectTrue(out.done && out.proceedObserved)
                try expectTrue(out.slots.allSatisfy { $0.completed })
                try expectEqual(out.exitCode, 0)
                try expectNil(out.terminationRequest)
            }
        }
        tk.run("publication ends a bounded wait while exit still depends on the host request") {
            let control = FinalWaitControl("linger")
            let out = try control.run()
            try expectEqual(control.outcomes, [.timedOut])
            try expectTrue(control.waits.allSatisfy { $0 <= 2_000_000 })
            try expectEqual(out.pollStopReason, "done")
            try expectTrue(out.done && out.exitRequested == true)
            try expectNil(out.terminationRequest)
        }
        tk.run("an early hangup is consumed once and falls back to bounded publication checks") {
            let control = FinalWaitControl("early_hangup")
            let out = try control.run()
            try expectEqual(control.outcomes.filter { $0 == .notified }.count, 1)
            try expectTrue(control.ownedChecksAfterNotification > 0)
            try expectTrue(!control.sleeps.isEmpty && control.sleeps.allSatisfy { $0 <= 2_000_000 })
            try expectEqual(out.pollStopReason, "done")
            try expectTrue(out.done && out.proceedObserved)
        }
        tk.run("a notification without done prompts owned reap and does not invent publication") {
            let control = FinalWaitControl("no_done")
            let out = try control.run()
            try expectTrue(control.notified && control.ownedChecksAfterNotification > 0)
            try expectEqual(out.pollStopReason, "child_reaped")
            try expectFalse(out.done)
            try expectEqual(out.exitCode, 17)
            try expectTrue(out.proceedObserved)
            try expectNil(out.terminationRequest)
        }
        tk.run("an unusable pipe abandons the notification wait and preserves publication") {
            let control = FinalWaitControl("unusable")
            let out = try control.run()
            try expectEqual(control.outcomes, [.unusable])
            try expectTrue(!control.sleeps.isEmpty)
            try expectEqual(out.pollStopReason, "done")
            try expectTrue(out.done && out.proceedObserved)
        }
        tk.run("an interrupted wait returns to the decision before another bounded wait") {
            let control = FinalWaitControl("interrupted")
            let out = try control.run()
            try expectEqual(control.outcomes, [.timedOut, .notified])
            try expectTrue(control.waits.allSatisfy { $0 <= 2_000_000 })
            try expectEqual(out.pollStopReason, "done")
            try expectTrue(out.done && out.proceedObserved)
        }
        tk.run("readiness failure retains no pipe and a late ready write still meets EPIPE") {
            let control = FinalWaitControl("missing_pipe")
            let out = try control.run()
            try expectFalse(out.readyByteReceived)
            try expectEqual(control.waits, [])
            try expectTrue(!control.sleeps.isEmpty)
            try expectEqual(out.pollStopReason, "done")
            try expectTrue(out.done)
            try expectEqual(out.slots[0].rc, 1)
            try expectEqual(out.slots[0].errnoVal, EPIPE)
        }
        for scenario in ["deadline", "clock_failure"] {
            tk.run("final waits preserve the remaining allowance under \(scenario)") {
                let control = FinalWaitControl(scenario)
                let out = try control.run()
                try expectTrue(!control.waits.isEmpty && control.waits.reduce(0, +) <= 50_000_000)
                try expectFalse(control.gateOpened)
                try expectEqual(out.pollStopReason, "sentinel_deadline")
                try expectEqual(out.sentinelWait?.clock_fault, scenario == "clock_failure")
                try expectFalse(out.done)
                try expectTrue(out.exitRequested == true)
            }
        }
    }
}

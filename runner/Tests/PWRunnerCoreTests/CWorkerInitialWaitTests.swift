import Darwin
import Foundation
@testable import PWRunnerCore

// The child applies no sandbox. Controlled clocks open an independently
// acknowledged publication gate inside the initial wait; no timing claim.
private final class InitialWaitControl {
    let gate = "/tmp/pw-initial-" + UUID().uuidString
    let scenario: String
    var now: UInt64 = 1_000_000_000_000
    var readyReads = 0
    var readsAtSleep: [Int] = []
    var collections = 0
    var pid: pid_t = 0
    var gateOpened = false
    var gateFailed = false
    init(_ scenario: String) { self.scenario = scenario }

    func openGate() {
        guard !gateOpened else { return }
        gateOpened = true
        guard FileManager.default.createFile(atPath: gate, contents: Data()) else { gateFailed = true; return }
        let until = DispatchTime.now().uptimeNanoseconds + 2_000_000_000
        while !FileManager.default.fileExists(atPath: gate + ".settled") {
            if DispatchTime.now().uptimeNanoseconds >= until { gateFailed = true; return }
            usleep(1000)
        }
    }

    func run() throws -> CWorkerOutput {
        guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
            throw TestFailure(message: "required lifecycle fixture missing")
        }
        defer {
            if pid > 0 {
                var status: Int32 = 0
                var rc: pid_t
                repeat { rc = Darwin.waitpid(pid, &status, WNOHANG) } while rc < 0 && errno == EINTR
                if rc == 0 {
                    _ = Darwin.kill(pid, SIGKILL)
                    repeat { rc = Darwin.waitpid(pid, &status, 0) } while rc < 0 && errno == EINTR
                }
            }
            for suffix in ["", ".ready", ".settled"] { try? FileManager.default.removeItem(atPath: gate + suffix) }
        }
        var calls = ChildProcessCalls()
        calls.clock = { [unowned self] in
            if FileManager.default.fileExists(atPath: self.gate + ".ready") {
                self.readyReads += 1
                if ["arrival", "failure", "exit"].contains(self.scenario) && self.readyReads == 4 { self.openGate() }
                if self.scenario == "clock_failure" && self.readyReads >= 3 { return nil }
                if self.scenario == "frozen" && !self.gateOpened { return self.now }
            }
            self.now += 10_000
            return self.now
        }
        calls.waitReadable = { [unowned self] fd, ns in
            waitReadableNs(fd, ns)
            self.now += ns
        }
        calls.wait = { [unowned self] pid, status, options in
            self.pid = pid
            return Darwin.waitpid(pid, status, options)
        }
        calls.sleep = { [unowned self] ns in
            if self.collections == 0 {
                self.readsAtSleep.append(self.readyReads)
                if self.scenario == "delayed" && self.readsAtSleep.count == 2 { self.openGate() }
                if ["missing", "clock_failure", "frozen"].contains(self.scenario) { self.openGate() }
            }
            self.now += ns
            sleepNs(min(ns, 1_000_000))
        }
        calls.waitExit = { [unowned self] watch, ns in
            let outcome = waitExitNs(watch, ns)
            self.now += ns
            return outcome
        }
        let mode = ["failure", "exit", "missing"].contains(scenario) ? scenario : "arrival"
        let result = runCWorker(CWorkerInput(workerExecutablePath: path, policy: "initial_wait_" + mode + "|" + gate,
            slots: [CWorkerSlotInput(stepId: "initial", attemptKind: .fileOpenRead, target: "/fixture")],
            readyByteTimeoutMs: scenario == "missing" ? 0 : 1000,
            sentinelTimeoutMs: scenario == "deadline" ? 1 : 100,
            exitGraceMs: 100), processCalls: calls, phaseBoundary: { [unowned self] _, _ in self.collections += 1 })
        let out: CWorkerOutput
        switch result {
        case .success(let value): out = value
        case .failure(_, let partial):
            guard let partial else { throw TestFailure(message: "no fixture observations: \(result)") }
            out = partial
        }
        try expectFalse(gateFailed, "independent fixture gate must settle")
        try expectTrue(out.reaped, "driver must establish owned reap")
        return out
    }
}

func runCWorkerInitialWaitTests(_ tk: TestKit) {
    tk.group("ordinary initial resampling") {
        tk.run("arrival during initial resampling collects before a sleep") {
            let c = InitialWaitControl("arrival"); let out = try c.run()
            try expectEqual(c.collections, 1); try expectEqual(c.readsAtSleep, [])
            try expectTrue(out.done && out.proceedObserved && out.slots[0].completed)
        }
        tk.run("delayed application gets one opportunity then bounded ordinary sleeps") {
            let c = InitialWaitControl("delayed"); let out = try c.run()
            try expectEqual(c.collections, 1); try expectTrue(out.done)
            try expectEqual(c.readsAtSleep.count, 2)
            try expectTrue(c.readsAtSleep[0] >= 10)
            try expectTrue(c.readsAtSleep[1] - c.readsAtSleep[0] < 10, "second wait must not restart resampling")
        }
        for scenario in ["failure", "exit", "deadline"] {
            tk.run("\(scenario) cannot authorize collection") {
                let c = InitialWaitControl(scenario); let out = try c.run()
                try expectEqual(c.collections, 0); try expectFalse(out.proceedObserved)
                if scenario == "failure" { try expectEqual(out.applyRC, -1); try expectTrue(out.done) }
                if scenario == "exit" { try expectEqual(out.exitCode, 17); try expectFalse(out.done) }
                if scenario == "deadline" { try expectFalse(c.gateOpened); try expectFalse(out.done) }
            }
        }
        tk.run("missing readiness uses the ordinary fallback without initial resampling") {
            let c = InitialWaitControl("missing"); let out = try c.run()
            try expectFalse(out.readyByteReceived); try expectEqual(c.collections, 1)
            try expectEqual(c.readsAtSleep.count, 1); try expectTrue(c.readsAtSleep[0] < 10)
        }
        for scenario in ["clock_failure", "frozen"] {
            tk.run("\(scenario) ends initial resampling with a bounded fallback") {
                let c = InitialWaitControl(scenario); let out = try c.run()
                try expectEqual(c.collections, 1); try expectTrue(out.done)
                try expectEqual(c.readsAtSleep.count, 1)
                if scenario == "clock_failure" { try expectEqual(out.sentinelWait?.clock_fault, true) }
                else { try expectTrue(c.readsAtSleep[0] >= 16_384 && c.readsAtSleep[0] < 16_400) }
            }
        }
    }
}

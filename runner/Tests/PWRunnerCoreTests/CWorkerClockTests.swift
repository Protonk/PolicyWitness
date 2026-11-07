import Darwin
import Foundation
@testable import PWRunnerCore

/*
 * CWorkerClockTests — the host's ready, sentinel and exit-grace waits are
 * elapsed monotonic allowances, not iteration counts.
 *
 * The real driver runs the ABI fixture worker while the clock, the sleep and
 * the readability wait the driver consults are controlled: a sleep may
 * overrun or cost nothing, a wait may return early, the clock may jump, fail
 * or run backwards, and a phase hook may consume time the sentinel wait must
 * not charge. Every assertion reads the wait records the host publishes
 * beside the disposition it already recorded. These are host observations
 * under controlled time, never policy evidence.
 */

/// A controlled monotonic clock. `sleep` advances it by the requested interval
/// times `overrun`, plus any fixed `cost` per call, and may really sleep so a
/// child can make progress; `failAfter` turns the clock unusable after that
/// many readings. A readability wait advances it like a sleep, or by
/// `waitReturnsAfterNs` when set (an early return), after `onWait` runs; its
/// real part polls the descriptor.
private final class ControlledClock {
    var now: UInt64 = 1_000_000_000_000
    var overrun: UInt64 = 1
    var costNs: UInt64 = 0
    var realSleepNs: UInt64 = 1_000_000   // children still need real time to make progress
    var failAfter: Int? = nil
    var regressAt: Int? = nil
    private(set) var readings = 0
    private(set) var sleeps: [UInt64] = []
    var waitReturnsAfterNs: UInt64? = nil
    var onWait: ((Int32) -> Void)? = nil
    private(set) var waits: [UInt64] = []
    private(set) var waitedFDs: Set<Int32> = []
    func read() -> UInt64? {
        readings += 1
        if let limit = failAfter, readings > limit { return nil }
        if let at = regressAt, readings >= at { now -= 1_000_000; return now }   // runs backwards from here on
        now += costNs
        return now
    }
    func sleep(_ ns: UInt64) {
        sleeps.append(ns)
        now += ns * overrun
        if realSleepNs > 0 { sleepNs(realSleepNs) }
    }
    func wait(_ fd: Int32, _ ns: UInt64) {
        waits.append(ns)
        waitedFDs.insert(fd)
        onWait?(fd)
        now += waitReturnsAfterNs ?? ns * overrun
        if realSleepNs > 0 { waitReadableNs(fd, realSleepNs) }
    }
    var calls: ChildProcessCalls {
        var calls = ChildProcessCalls()
        calls.clock = { [unowned self] in self.read() }
        calls.sleep = { [unowned self] ns in self.sleep(ns) }
        calls.waitReadable = { [unowned self] fd, ns in self.wait(fd, ns) }
        return calls
    }
}

/// The readiness loop's shape over a test pipe: a nonblocking read first, then
/// the clock's readability wait. Returns the stop reason.
private func readUntilReady(_ fd: Int32, _ wait: inout HostWaitClock) -> String {
    var byte: UInt8 = 0
    while true {
        let n = Darwin.read(fd, &byte, 1)
        if n == 1 { return "received" }
        if n == 0 { return "eof" }
        if n < 0 && errno != EAGAIN && errno != EINTR { return "read_error" }
        if wait.expiredAfterWaiting(readable: fd) { return "deadline" }
    }
}

private func nonblockingPipe() throws -> [Int32] {
    var fds: [Int32] = [-1, -1]
    guard pipe(&fds) == 0 else { throw TestFailure(message: "pipe failed: \(errno)") }
    guard fcntl(fds[0], F_SETFL, fcntl(fds[0], F_GETFL, 0) | O_NONBLOCK) == 0 else {
        close(fds[0]); close(fds[1])
        throw TestFailure(message: "fcntl failed: \(errno)")
    }
    return fds
}


private func unwrap<T>(_ value: T?, _ what: String = "value", file: StaticString = #file, line: UInt = #line) throws -> T {
    guard let value else { throw TestFailure(message: "missing \(what) (at \(file):\(line))") }
    return value
}

private func fixturePath() throws -> String {
    guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
          FileManager.default.isExecutableFile(atPath: path) else {
        throw TestFailure(message: "required PW_LIFECYCLE_WORKER_FIXTURE missing; run tests/run.sh --suite runner_unit")
    }
    return path
}

private func cleanup(_ pid: pid_t) throws {
    var status: Int32 = 0
    let first = Darwin.waitpid(pid, &status, WNOHANG)
    if first == pid || (first == -1 && errno == ECHILD) { return }
    _ = Darwin.kill(pid, SIGKILL)
    for _ in 0..<200 {
        let rc = Darwin.waitpid(pid, &status, WNOHANG)
        if rc == pid || (rc == -1 && errno == ECHILD) { return }
        usleep(10_000)
    }
    throw TestFailure(message: "test-owned fixture was not reaped")
}

/// Drive the fixture in `mode` under a controlled clock; the fixture never applies a sandbox.
private func drive(_ mode: String, clock: ControlledClock, sentinelMs: Int, graceMs: Int = 50,
                   readyMs: Int = 1_000, phases: Int = 1, hook: CWorkerPhaseHook? = nil) throws -> CWorkerOutput {
    let slots = (0..<phases).map { CWorkerSlotInput(stepId: "s\($0)", attemptKind: .fileOpenRead, target: "/fixture") }
    var input = CWorkerInput(workerExecutablePath: try fixturePath(), policy: mode, slots: slots,
                             phases: (0..<phases).map { CWorkerPhaseInput(firstSlot: $0, endSlot: $0 + 1) },
                             readyByteTimeoutMs: readyMs, sentinelTimeoutMs: sentinelMs, exitGraceMs: graceMs)
    input.proceedWaitMs = 2_000
    let result = runCWorker(input, processCalls: clock.calls, phaseBoundary: hook ?? { _, _ in })
    guard case .success(let out) = result else { throw TestFailure(message: "fixture driver failed: \(result)") }
    try cleanup(out.workerPid)
    return out
}

func runCWorkerClockTests(_ tk: TestKit) {
    tk.group("host waits are elapsed monotonic allowances") {
        tk.run("small regression above the starting time faults without restoring spent time") {
            let clock = ControlledClock(); clock.realSleepNs = 0
            var wait = HostWaitClock(milliseconds: 100, pollNs: 7_000_000, calls: clock.calls)
            clock.now += 90_000_000
            try expectEqual(wait.remainingNs(), UInt64(10_000_000))
            clock.now -= 40_000_000
            try expectNil(wait.remainingNs())
            try expectTrue(wait.clockFault)
            while !wait.expiredAfterSleeping() {}
            try expectEqual(clock.sleeps, [UInt64(7_000_000), UInt64(3_000_000)])
        }
        tk.run("a clock failure after a requested sleep does not spend that sleep twice") {
            let clock = ControlledClock(); clock.realSleepNs = 0
            var wait = HostWaitClock(milliseconds: 100, pollNs: 7_000_000, calls: clock.calls)
            clock.now += 90_000_000
            try expectFalse(wait.expiredAfterSleeping())
            clock.failAfter = clock.readings
            while !wait.expiredAfterSleeping() {}
            try expectEqual(clock.sleeps.reduce(0, +), UInt64(10_000_000))
        }
        tk.run("both exclusion boundaries check the previous reading and retain remaining fallback") {
            for atEnd in [false, true] {
                let clock = ControlledClock(); clock.realSleepNs = 0
                var wait = HostWaitClock(milliseconds: 100, pollNs: 7_000_000, calls: clock.calls)
                clock.now += 90_000_000
                _ = wait.remainingNs()
                if !atEnd { clock.now -= 40_000_000 }
                let mark = wait.mark()
                if atEnd { clock.now -= 40_000_000 }
                wait.excludeSince(mark)
                try expectTrue(wait.clockFault)
                while !wait.expiredAfterSleeping() {}
                try expectEqual(clock.sleeps.reduce(0, +), UInt64(10_000_000))
                try expectEqual(wait.excludedNs, UInt64(0))
            }
        }
        tk.run("a wait that returns as the pipe becomes readable continues to the read that receives") {
            let clock = ControlledClock(); clock.realSleepNs = 0; clock.waitReturnsAfterNs = 0
            let fds = try nonblockingPipe()
            defer { close(fds[0]); close(fds[1]) }
            clock.onWait = { _ in _ = Darwin.write(fds[1], "R", 1) }   // the byte arrives during the first wait
            var wait = HostWaitClock(milliseconds: 1_000, pollNs: 10_000_000, calls: clock.calls)
            try expectEqual(readUntilReady(fds[0], &wait), "received")
            try expectEqual(clock.waits, [UInt64(10_000_000)])
            try expectEqual(clock.waitedFDs, [fds[0]])
            try expectEqual(clock.sleeps, [])
            let record = wait.record(stop: "received")
            try expectEqual(record.elapsed_ms, UInt64(0)); try expectEqual(record.clock_fault, false)
        }
        tk.run("zero allowance expires before any readability wait") {
            let clock = ControlledClock(); clock.realSleepNs = 0
            var wait = HostWaitClock(milliseconds: 0, pollNs: 10_000_000, calls: clock.calls)
            try expectTrue(wait.expiredAfterWaiting(readable: 0))
            try expectEqual(clock.waits, [])
        }
        tk.run("a remaining allowance below the poll period bounds the readability wait") {
            let clock = ControlledClock(); clock.realSleepNs = 0
            var wait = HostWaitClock(milliseconds: 100, pollNs: 7_000_000, calls: clock.calls)
            clock.now += 97_000_000
            try expectFalse(wait.expiredAfterWaiting(readable: 0))
            try expectTrue(wait.expiredAfterWaiting(readable: 0))
            try expectEqual(clock.waits, [UInt64(3_000_000)])
        }
        tk.run("early returns are passes charged their measured time, never progress") {
            let clock = ControlledClock(); clock.realSleepNs = 0
            clock.waitReturnsAfterNs = 1_000_000   // every wait returns after 1 ms, before its bound
            var wait = HostWaitClock(milliseconds: 100, pollNs: 10_000_000, calls: clock.calls)
            while !wait.expiredAfterWaiting(readable: 0) {}
            try expectEqual(clock.waits.count, 100)
            try expectTrue(clock.waits.prefix(91).allSatisfy { $0 == 10_000_000 }, "\(clock.waits)")
            try expectEqual(Array(clock.waits.suffix(9)), (1...9).reversed().map { UInt64($0) * 1_000_000 })
            let record = wait.record(stop: "deadline")
            try expectEqual(record.elapsed_ms, UInt64(100)); try expectEqual(record.clock_fault, false)
        }
        tk.run("a regressing clock spends only the remaining allowance in nominal readability waits") {
            let clock = ControlledClock(); clock.realSleepNs = 0
            var wait = HostWaitClock(milliseconds: 100, pollNs: 7_000_000, calls: clock.calls)
            clock.now += 90_000_000
            try expectEqual(wait.remainingNs(), UInt64(10_000_000))
            clock.now -= 40_000_000
            try expectNil(wait.remainingNs())
            try expectTrue(wait.clockFault)
            while !wait.expiredAfterWaiting(readable: 0) {}
            try expectEqual(clock.waits, [UInt64(7_000_000), UInt64(3_000_000)])
        }
        tk.run("a clock failure after a requested readability wait does not spend that wait twice") {
            for early in [false, true] {
                let clock = ControlledClock(); clock.realSleepNs = 0
                if early { clock.waitReturnsAfterNs = 0 }   // returns at once; the fallback still charges the bound
                var wait = HostWaitClock(milliseconds: 100, pollNs: 7_000_000, calls: clock.calls)
                clock.now += 90_000_000
                try expectFalse(wait.expiredAfterWaiting(readable: 0))
                clock.failAfter = clock.readings
                while !wait.expiredAfterWaiting(readable: 0) {}
                try expectEqual(clock.waits.reduce(0, +), UInt64(10_000_000), "early=\(early)")
                try expectEqual(wait.record(stop: "deadline").clock_fault, true)
            }
        }
        tk.run("oversleeping polls end the sentinel wait at the allowance, not after a fixed number of passes") {
            let clock = ControlledClock(); clock.overrun = 5   // every 2 ms sleep costs 10 ms of clock
            let out = try drive("no_report_hang", clock: clock, sentinelMs: 100)
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            let wait = try unwrap(out.sentinelWait)
            try expectEqual(wait.stop, "sentinel_deadline"); try expectEqual(wait.budget_ms, 100)
            try expectEqual(wait.clock_fault, false)
            let elapsed = try unwrap(wait.elapsed_ms)
            try expectTrue(elapsed >= 100 && elapsed <= 112, "elapsed \(elapsed) ms must sit on the allowance, not on a pass count")
            try expectTrue(clock.sleeps.count < 50, "an iteration-counted wait would take 50 passes; the clock ended it after \(clock.sleeps.count)")
            // The grace wait sleeps at most 10 ms, the sentinel 2 ms; the readiness wait polls the pipe for at most 10 ms.
            try expectTrue(clock.sleeps.allSatisfy { $0 <= 10_000_000 }, "each sleep is bounded by its poll interval and the remaining allowance")
            try expectTrue(clock.waits.allSatisfy { $0 <= 10_000_000 }, "each readability wait is bounded by its poll interval and the remaining allowance")
        }
        tk.run("irregular polling costs consume the allowance") {
            let clock = ControlledClock(); clock.costNs = 7_000_000   // each clock reading costs 7 ms of scheduler time
            let out = try drive("no_report_hang", clock: clock, sentinelMs: 100)
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            let elapsed = try unwrap(try unwrap(out.sentinelWait).elapsed_ms)
            try expectTrue(elapsed >= 100 && elapsed <= 130, "elapsed \(elapsed) ms")
        }
        tk.run("the last sleep is bounded by the remaining allowance") {
            let clock = ControlledClock()
            _ = try drive("no_report_hang", clock: clock, sentinelMs: 7)   // 7 ms is not a multiple of the 2 ms poll
            let sentinelSleeps = clock.sleeps.filter { $0 <= 2_000_000 }
            try expectTrue(sentinelSleeps.contains { $0 < 2_000_000 }, "a final sleep shorter than the poll interval: \(clock.sleeps)")
        }
        tk.run("zero allowance expires on the first pass without inventing publication") {
            let clock = ControlledClock()
            let out = try drive("no_report_hang", clock: clock, sentinelMs: 0)
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            try expectEqual(try unwrap(out.sentinelWait).elapsed_ms, UInt64(0))
            try expectFalse(out.done)
        }
        tk.run("interrupted waits do not renew the allowance") {
            let clock = ControlledClock()
            var calls = clock.calls
            var interruptions = 0
            let native = calls.wait
            calls.wait = { pid, status, options in
                if interruptions < 2 { interruptions += 1; errno = EINTR; return -1 }
                return native(pid, status, options)
            }
            var input = CWorkerInput(workerExecutablePath: try fixturePath(), policy: "no_report_hang",
                slots: [CWorkerSlotInput(stepId: "s0", attemptKind: .fileOpenRead, target: "/fixture")],
                sentinelTimeoutMs: 100, exitGraceMs: 50)
            input.proceedWaitMs = 2_000
            let result = runCWorker(input, processCalls: calls, phaseBoundary: { _, _ in })
            guard case .success(let out) = result else { throw TestFailure(message: "fixture driver failed: \(result)") }
            try cleanup(out.workerPid)
            try expectEqual(interruptions, 2)
            let elapsed = try unwrap(try unwrap(out.sentinelWait).elapsed_ms)
            try expectTrue(elapsed >= 100 && elapsed <= 112, "elapsed \(elapsed) ms: EINTR must not restart the allowance")
        }
        tk.run("a failed clock falls back to a bounded number of nominal sleeps and says so") {
            // The clock dies during the readiness wait, so every later wait runs on its
            // bounded fallback: 1000/10 readiness waits, 100/2 sentinel passes and 50/10
            // grace passes at most, each recorded as a clock fault.
            let clock = ControlledClock(); clock.failAfter = 6; clock.realSleepNs = 0
            let out = try drive("no_report_hang", clock: clock, sentinelMs: 100)
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            let wait = try unwrap(out.sentinelWait)
            try expectEqual(wait.clock_fault, true)
            try expectNil(wait.elapsed_ms)
            try expectEqual(try unwrap(out.readyWait).clock_fault, true)
            try expectTrue(clock.sleeps.count + clock.waits.count <= 100 + 50 + 5 + 10,
                           "the fallback is bounded by budget / poll: \(clock.sleeps.count) sleeps, \(clock.waits.count) waits")
        }
        tk.run("a clock that runs backwards is a fault, not extra allowance") {
            let clock = ControlledClock(); clock.regressAt = 5
            let out = try drive("no_report_hang", clock: clock, sentinelMs: 100)
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            // From the fifth reading the clock runs backwards: whichever wait is
            // active records the fault, and no wait is extended by it.
            let faulted = [out.readyWait, out.sentinelWait, out.graceWait].compactMap { $0 }.filter { $0.clock_fault }
            try expectTrue(!faulted.isEmpty, "a regressing clock must be recorded as a fault")
            try expectTrue(clock.sleeps.count + clock.waits.count <= 100 + 50 + 5 + 10,
                           "a regression never extends a wait: \(clock.sleeps.count) sleeps, \(clock.waits.count) waits")
        }
        tk.run("synchronous collection intervals extend the allowance by exactly their measured length") {
            let clock = ControlledClock()
            var hooks = 0
            // ignore_proceed arrives at its phase (so the collection hook runs) and
            // then never acknowledges or publishes, so the sentinel allowance expires.
            let out = try drive("ignore_proceed", clock: clock, sentinelMs: 100, phases: 1, hook: { _, _ in
                hooks += 1; clock.now += 300_000_000   // 300 ms of collection the sentinel must not charge
            })
            try expectEqual(hooks, 1)
            try expectEqual(out.pollStopReason, "sentinel_deadline")
            let wait = try unwrap(out.sentinelWait)
            try expectEqual(wait.excluded_ms, UInt64(300))
            let elapsed = try unwrap(wait.elapsed_ms)
            try expectTrue(elapsed >= 400 && elapsed <= 412, "elapsed \(elapsed) ms = 100 ms allowance + 300 ms excluded")
        }
        tk.run("completion observed as the allowance runs out is done, not a deadline") {
            let clock = ControlledClock(); clock.realSleepNs = 50_000_000; clock.overrun = 1_000   // one sleep spends the whole allowance
            let out = try drive("complete_hang", clock: clock, sentinelMs: 100)
            try expectEqual(out.pollStopReason, "done")
            try expectTrue(out.done)
            let wait = try unwrap(out.sentinelWait)
            try expectEqual(wait.stop, "done")
        }
        tk.run("the readiness wait and exit grace publish their allowances") {
            let clock = ControlledClock()
            let out = try drive("complete_exit_0", clock: clock, sentinelMs: 500, graceMs: 50)
            let ready = try unwrap(out.readyWait)
            try expectEqual(ready.budget_ms, 1_000)
            try expectTrue(["received", "eof"].contains(ready.stop), ready.stop)
            try expectEqual(try unwrap(out.graceWait).budget_ms, 50)
            let encoded = try pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: pwRunnerEncodeJSON(buildWorkerSubprocess(out)))
            try expectEqual(encoded.sentinel_wait, out.sentinelWait)
            try expectEqual(encoded.ready_wait, out.readyWait)
            try expectEqual(encoded.exit_grace_wait, out.graceWait)
        }
    }
}

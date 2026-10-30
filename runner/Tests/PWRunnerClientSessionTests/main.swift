import Foundation

private struct ControlFailure: Error { var message: String }
private func check(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    if !condition() { throw ControlFailure(message: message) }
}

private final class ControlledConnection: PWRunnerClientConnection {
    let failure: (PWRunnerConnectionFailure) -> Void
    var onReserve: ((ControlledConnection) -> Void)?
    var onSubmit: ((ControlledConnection) -> Void)?
    var reservationRequest: PWRunnerReservationRequest?
    var reservedReply: ((Data) -> Void)?
    var submissionReply: ((Bool, Data) -> Void)?
    var submissions = 0
    var invalidations = 0
    init(_ failure: @escaping (PWRunnerConnectionFailure) -> Void) { self.failure = failure }
    func reserve(_ data: Data, reply: @escaping (Data) -> Void) {
        reservationRequest = try! pwRunnerDecodeJSON(PWRunnerReservationRequest.self, from: data)
        reservedReply = reply; onReserve?(self)
    }
    func submit(_ data: Data, reservation: String, reply: @escaping (Bool, Data) -> Void) {
        submissions += 1; submissionReply = reply; onSubmit?(self)
    }
    func invalidate() { invalidations += 1 }
    func respond(_ status: String, paddedTo: Int? = nil) {
        let request = reservationRequest!
        let control = PWRunnerControlReply(status: status, attempt_id: request.attempt_id,
            host_pid: 123, host_instance: "12345678-1234-1234-1234-123456789abc",
            reservation_id: status == "granted" ? "12345678-1234-1234-1234-123456789def" : nil,
            lease_ms: status == "granted" ? request.lease_ms : nil)
        var bytes = try! pwRunnerEncodeJSON(control)
        if let paddedTo { bytes += Data(repeating: 32, count: max(0, paddedTo - bytes.count)) }
        reservedReply?(bytes)
    }
    func fail(_ reason: String = "xpc_error") {
        failure(.init(reason: reason, message: "controlled connection failure", error: nil))
    }
}

private final class SessionFixture {
    var now: UInt64 = 1_000_000_000
    var clockReads: [UInt64] = []
    var jobs: [(UInt64, Int, () -> Void)] = []
    var serial = 0
    var connections: [ControlledConnection] = []
    var frames: [PWRunnerClientCapture] = []
    var session: PWRunnerClientSession?
    var onReserve: ((ControlledConnection) -> Void)?
    var connectionTimes: [UInt64] = []
    func start(timeout: UInt64 = 30_000, deadline: UInt64? = nil) {
        session = PWRunnerClientSession(request: Data("specimen bytes".utf8), timeoutMs: timeout, deadlineNs: deadline,
            clock: { self.clockReads.isEmpty ? self.now : self.clockReads.removeFirst() }, enqueue: { $0() },
            schedule: { delay, body in
                self.serial += 1; self.jobs.append((self.now + UInt64(delay) * 1_000_000, self.serial, body))
            }, connect: { failure in
                let connection = ControlledConnection(failure)
                connection.onReserve = self.onReserve
                self.connections.append(connection); self.connectionTimes.append(self.now)
                return connection
            }, finish: { self.frames.append($0) })
        session!.start()
    }
    func advance(_ milliseconds: UInt64) {
        let target = now + milliseconds * 1_000_000
        var steps = 0
        while let index = jobs.indices.min(by: {
            jobs[$0].0 == jobs[$1].0 ? jobs[$0].1 < jobs[$1].1 : jobs[$0].0 < jobs[$1].0
        }), jobs[index].0 <= target {
            let job = jobs.remove(at: index); now = max(now, job.0); job.2()
            steps += 1; precondition(steps < 100_000, "bounded scheduler")
        }
        now = max(now, target)
    }
    var frame: PWRunnerClientCapture { frames.last! }
}

func runClientSessionControls() throws -> Int {
    var count = 0
    func test(_ name: String, _ body: () throws -> Void) throws {
        try body(); count += 1; print("ok \(name)")
    }
    try test("occupied acquisition retries on a new connection and submits once") {
        let f = SessionFixture(); f.start()
        let old = f.connections[0]; old.respond("occupied")
        try check(old.invalidations == 1, "abandon before retry")
        f.advance(99); try check(f.connections.count == 1, "cadence not shortened")
        f.advance(1); try check(f.connections.count == 2, "100ms retry")
        old.respond("granted"); try check(old.submissions == 0, "late grant ignored")
        let current = f.connections[1]; current.respond("granted")
        try check(current.submissions == 1, "one invocation")
        let bytes = Data([0, 255, 10, 13])
        current.submissionReply?(true, bytes)
        try check(f.frame.terminal == "runner_reply", "result admitted as bytes")
        try check(Data(base64Encoded: f.frame.runner_reply!.data_base64) == bytes, "exact original host bytes")
        current.fail(); old.fail(); f.advance(30_000)
        try check(f.frames.count == 1 && f.connections.count == 2, "no later replay")
    }
    try test("reservation RPC timeout abandons only acquisition") {
        let f = SessionFixture(); f.start()
        let old = f.connections[0]
        f.advance(4999); try check(old.invalidations == 0, "RPC allowance remains")
        f.advance(1); try check(old.invalidations == 1, "5000ms timeout cancels")
        f.advance(100); try check(f.connections.count == 2, "reacquire after cadence")
        old.respond("granted"); try check(old.submissions == 0, "timed-out grant cannot execute")
        f.connections[1].respond("granted"); f.connections[1].submissionReply?(true, Data())
        try check(f.frame.attempts[0].error?.reason == "rpc_timeout", "retain RPC timeout")
    }
    try test("attempt ceiling and absolute deadline independently bound acquisition") {
        let f = SessionFixture(); f.onReserve = { $0.respond("occupied") }; f.start(timeout: 60_000)
        f.advance(60_000)
        try check(f.connections.count == 256, "literal attempt bound")
        try check(f.frame.acquisition_stop == "attempt_limit" && f.frame.terminal == "acquisition_failed", "attempt exhaustion terminal")
        try check(f.connectionTimes.enumerated().allSatisfy { $0.element == 1_000_000_000 + UInt64($0.offset) * 100_000_000 }, "cadence observed for every attempt")
        let short = SessionFixture(); short.onReserve = { $0.respond("occupied") }; short.start(timeout: 250)
        short.advance(250)
        try check(short.connections.count == 3, "deadline stops fourth connection")
        try check(short.frame.acquisition_stop == "overall_deadline" && short.frame.submission.state == "not_invoked", "deadline before invocation")
    }
    try test("grant after original deadline remains not invoked") {
        let f = SessionFixture(); f.start(timeout: 10)
        f.now += 10_000_000 // Deliberately leave the scheduled timer pending.
        f.connections[0].respond("granted")
        try check(f.connections[0].submissions == 0, "late grant cannot submit")
        try check(f.frame.acquisition_stop == "granted" && f.frame.submission.state == "not_invoked", "positive grant retained")
        try check(f.frame.attempts.last?.outcome == "granted", "completed grant receipt survives subsequent timeout")
        try check(f.frame.terminal == "xpc_timeout", "overall allowance not reset")
    }
    try test("late host result and error cannot beat an overdue timer") {
        for error in [false, true] {
            let f = SessionFixture(); f.start(timeout: 10); f.connections[0].respond("granted")
            f.now += 10_000_000
            if error { f.connections[0].fail() } else { f.connections[0].submissionReply?(true, Data("late result".utf8)) }
            try check(f.frame.terminal == "xpc_timeout" && f.frame.submission.state == "invoked", "late callback is timeout with invocation retained")
            try check(f.frame.runner_reply == nil && f.connections.count == 1, "no timely result claim or replay")
        }
    }
    try test("submission error timeout and control refusal never replay") {
        for event in ["error", "timeout", "refusal", "malformed", "host_clock"] {
            let f = SessionFixture(); f.start(timeout: 20); let c = f.connections[0]; c.respond("granted")
            switch event {
            case "error": c.fail()
            case "timeout": f.advance(20)
            case "malformed": c.submissionReply?(false, Data("{".utf8))
            default:
                let refusal = PWRunnerControlReply(status: "reservation_refused", host_instance: UUID().uuidString,
                    reason: event == "host_clock" ? "clock_error" : "expired")
                c.submissionReply?(false, try pwRunnerEncodeJSON(refusal))
            }
            try check(f.frame.submission.state == "invoked", "invocation is irreversible")
            if event == "malformed" {
                try check(f.frame.terminal == "protocol_error" && f.frame.submission_refusal?.status == nil, "malformed refusal retains count/hash only")
            }
            c.respond("granted"); c.fail(); f.advance(30_000)
            try check(c.submissions == 1 && f.connections.count == 1 && f.frames.count == 1, "no replay after submission terminal")
        }
    }
    try test("proxy failure during submission retains invocation and never retries") {
        let f = SessionFixture(); f.start(); let c = f.connections[0]
        c.onSubmit = { $0.fail("proxy_type_mismatch") }
        c.respond("granted")
        try check(f.frame.submission.state == "invoked" && f.frame.submission.invoked_elapsed_ms != nil, "submission boundary precedes proxy acquisition")
        try check(f.frame.terminal == "xpc_error" && f.frame.error?.stage == "submission", "submission transport terminal")
        try check(f.frame.error?.reason == "proxy_type_mismatch", "specific proxy observation retained")
        f.advance(30_000)
        try check(f.connections.count == 1 && c.submissions == 1 && f.frames.count == 1, "proxy failure cannot replay")
    }
    try test("control byte bound and protocol gate refuse before submission") {
        for size in [65535, 65536, 65537] {
            let f = SessionFixture(); f.start(); let c = f.connections[0]; c.respond("granted", paddedTo: size)
            if size <= 65536 {
                try check(c.submissions == 1, "at-bound control admitted")
                c.submissionReply?(true, Data())
            } else {
                try check(c.submissions == 0 && f.frame.error?.reason == "control_too_large", "over-bound control refused")
                try check(f.frame.attempts[0].control?.bytes_received == size && f.frame.attempts[0].control?.status == nil, "rejected count/hash no recovered fields")
            }
        }
        let f = SessionFixture(); f.start()
        f.connections[0].reservedReply?(Data("{\"protocol_version\":1,\"unknown_future_payload\":true}".utf8))
        try check(f.frame.error?.reason == "unsupported_protocol" && f.connections[0].submissions == 0, "version admitted before inner shape")
        let bad = SessionFixture(); bad.start()
        bad.connections[0].reservedReply?(Data("{\"protocol_version\":2,\"unknown_future_payload\":true}".utf8))
        try check(bad.frame.error?.reason == "invalid_control", "known version requires valid body")
        let pid = SessionFixture(); pid.start()
        let overRange = PWRunnerControlReply(status: "granted", attempt_id: pid.connections[0].reservationRequest!.attempt_id,
            host_pid: 2_147_483_648, host_instance: UUID().uuidString, reservation_id: UUID().uuidString, lease_ms: 5000)
        pid.connections[0].reservedReply?(try pwRunnerEncodeJSON(overRange))
        try check(pid.connections[0].submissions == 0 && pid.frame.error?.reason == "invalid_control", "over-range PID refused before submission")
    }
    try test("clock failure preserves partial readings and positive invocation") {
        let initial = SessionFixture(); initial.clockReads = [UInt64.max]; initial.start()
        try check(!initial.frame.clock_available && initial.frame.started_continuous_ns == nil, "missing initial clock is not zero")
        try check(initial.frame.attempts.isEmpty && initial.frame.submission.state == "not_invoked", "initial failure cannot connect")
        let grant = SessionFixture(); grant.start(); grant.clockReads = [grant.now, UInt64.max]
        grant.connections[0].respond("granted")
        try check(grant.frame.acquisition_stop == "granted" && grant.frame.attempts.last?.outcome == "granted", "completed grant retained after next clock failure")
        try check(grant.frame.submission.state == "not_invoked", "failed pre-invocation clock cannot submit")
        for invoked in [false, true] {
            let f = SessionFixture(); f.start()
            if invoked { f.connections[0].respond("granted") }
            f.clockReads = [UInt64.max]; f.connections[0].fail()
            try check(!f.frame.clock_available && f.frame.ended_continuous_ns == nil, "unknown end stays unknown")
            try check(f.frame.started_continuous_ns != nil && f.frame.deadline_continuous_ns != nil, "valid earlier readings retained")
            try check(f.frame.submission.state == (invoked ? "invoked" : "not_invoked"), "positive invocation retained")
            try check(f.frame.error?.reason == "clock_error" && f.frame.terminal == "local_error", "clock attribution")
            if !invoked { try check(f.frame.attempts[0].ended_elapsed_ms == nil, "unknown attempt end not fabricated") }
        }
    }
    try test("external expired deadline and reduced lease precede connection") {
        let expired = SessionFixture(); expired.start(deadline: expired.now)
        try check(expired.connections.isEmpty && expired.frame.terminal == "xpc_timeout", "caller deadline covers startup")
        let f = SessionFixture(); f.start(timeout: 999)
        try check(f.connections[0].reservationRequest?.lease_ms == 999, "lease no longer than remaining allowance")
    }
    return count
}

do { let count = try runClientSessionControls(); print("\(count)/\(count) client session controls passed") }
catch { fputs("client session control failed: \(error)\n", stderr); exit(1) }

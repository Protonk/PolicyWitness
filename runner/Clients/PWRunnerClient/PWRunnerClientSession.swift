import Foundation

struct PWRunnerConnectionFailure {
    var reason: String
    var message: String
    var error: Error?
}

protocol PWRunnerClientConnection: AnyObject {
    func reserve(_ request: Data, reply: @escaping (Data) -> Void)
    func submit(_ request: Data, reservation: String, reply: @escaping (Bool, Data) -> Void)
    func invalidate()
}

final class PWRunnerXPCConnection: PWRunnerClientConnection {
    private let connection: NSXPCConnection
    private let failure: (PWRunnerConnectionFailure) -> Void
    init(service: String, machService: Bool, privileged: Bool, failure: @escaping (PWRunnerConnectionFailure) -> Void) {
        self.failure = failure
        connection = machService ? NSXPCConnection(machServiceName: service, options: privileged ? [.privileged] : [])
            : NSXPCConnection(serviceName: service)
        connection.remoteObjectInterface = NSXPCInterface(with: PWRunnerProtocol.self)
        connection.interruptionHandler = { failure(.init(reason: "interrupted", message: "XPC connection interrupted", error: nil)) }
        connection.invalidationHandler = { failure(.init(reason: "invalidated", message: "XPC connection invalidated", error: nil)) }
        connection.resume()
    }
    private func proxy() -> PWRunnerProtocol? {
        let failed = failure
        let object = connection.remoteObjectProxyWithErrorHandler {
            failed(.init(reason: "xpc_error", message: "XPC call failed", error: $0))
        }
        guard let proxy = object as? PWRunnerProtocol else {
            failure(.init(reason: "proxy_type_mismatch", message: "remote proxy type mismatch", error: nil))
            return nil
        }
        return proxy
    }
    func reserve(_ request: Data, reply: @escaping (Data) -> Void) { proxy()?.reserveRunner(request, withReply: reply) }
    func submit(_ request: Data, reservation: String, reply: @escaping (Bool, Data) -> Void) {
        proxy()?.runReservedSpecimen(request, reservation: reservation, withReply: reply)
    }
    func invalidate() { connection.invalidate() }
}

/// One serial owner decides every callback, cancellation and invocation. Tests
/// supply the queue, clock, scheduler and connection at these actual boundaries.
final class PWRunnerClientSession {
    typealias Enqueue = (@escaping () -> Void) -> Void
    typealias Schedule = (Int, @escaping () -> Void) -> Void
    typealias Connect = (@escaping (PWRunnerConnectionFailure) -> Void) -> PWRunnerClientConnection
    private enum Phase { case initial, acquiring, waiting, reserved, submitted, done }
    private var phase = Phase.initial
    private let request: Data
    private let clock: () -> UInt64
    private let enqueue: Enqueue
    private let schedule: Schedule
    private let connect: Connect
    private let finish: (PWRunnerClientCapture) -> Void
    private var capture: PWRunnerClientCapture
    private var connection: PWRunnerClientConnection?
    private var attemptID = ""
    private var lastNow: UInt64?
    private let deadline: UInt64?

    init(request: Data, timeoutMs: UInt64, deadlineNs: UInt64?, clock: @escaping () -> UInt64 = PWContinuousClock.now,
         enqueue: @escaping Enqueue, schedule: @escaping Schedule, connect: @escaping Connect,
         finish: @escaping (PWRunnerClientCapture) -> Void) {
        self.request = request; self.clock = clock; self.enqueue = enqueue
        self.schedule = schedule; self.connect = connect; self.finish = finish
        let now = clock()
        let validNow = now == UInt64.max ? nil : now
        lastNow = validNow
        let candidateDeadline = deadlineNs ?? validNow.map { PWContinuousClock.adding(milliseconds: max(1, timeoutMs), to: $0) }
        deadline = candidateDeadline == UInt64.max ? nil : candidateDeadline
        capture = PWRunnerClientCapture(clock_available: validNow != nil && deadline != nil,
            started_continuous_ns: validNow, deadline_continuous_ns: deadline,
            ended_continuous_ns: nil, timeout_ms: max(1, timeoutMs))
    }

    func start() { enqueue { self.begin() } }
    private func begin() {
        guard phase == .initial else { return }
        guard capture.clock_available else { clockFailure(); return }
        armDeadline()
        beginAttempt()
    }
    private func sample() -> UInt64? {
        let now = clock()
        guard now != UInt64.max, let previous = lastNow, now >= previous else { clockFailure(); return nil }
        lastNow = now
        return now
    }
    private func elapsed(_ now: UInt64?) -> UInt64? {
        guard let now, let start = capture.started_continuous_ns, now >= start else { return nil }
        return PWContinuousClock.elapsedMs(from: start, to: now)
    }
    private func remainingMs(_ now: UInt64) -> Int {
        guard let deadline, now < deadline else { return 0 }
        let ns = deadline - now
        return Int(min(UInt64(Int.max), ns / 1_000_000 + (ns % 1_000_000 == 0 ? 0 : 1)))
    }
    private func armDeadline() {
        guard phase != .done, let now = sample() else { return }
        if remainingMs(now) == 0 { overallTimeout(); return }
        // A short scheduling tick notices continuous-time expiry after sleep;
        // the absolute clock, not a callback count, owns the allowance.
        schedule(min(100, remainingMs(now))) { self.enqueue { self.armDeadline() } }
    }
    private func overallTimeout() {
        guard phase != .done else { return }
        if phase == .acquiring {
            endAttempt("timeout", error: .init(stage: "acquisition", reason: "overall_deadline", message: "overall deadline expired"))
        }
        if capture.acquisition_stop != "granted" { capture.acquisition_stop = "overall_deadline" }
        complete("xpc_timeout", error: .init(stage: phase == .submitted ? "submission" : "acquisition",
                                             reason: "overall_deadline", message: "overall deadline expired"))
    }
    private func clockFailure() {
        guard phase != .done else { return }
        capture.clock_available = false
        lastNow = nil
        let error = PWRunnerTransportError(stage: "local", reason: "clock_error", message: "continuous clock unavailable or moved backward")
        if phase == .acquiring { endAttempt("local_error", error: error) }
        if capture.acquisition_stop != "granted" { capture.acquisition_stop = "local_error" }
        complete("local_error", error: error)
    }
    private func beginAttempt() {
        guard phase == .initial || phase == .waiting, let now = sample() else { return }
        guard remainingMs(now) > 0 else { overallTimeout(); return }
        guard capture.attempts.count < PWRunnerTransportLimits.acquisitionAttempts else {
            capture.acquisition_stop = "attempt_limit"
            complete("acquisition_failed", error: .init(stage: "acquisition", reason: "attempt_limit", message: "acquisition attempt limit reached"))
            return
        }
        phase = .acquiring
        attemptID = UUID().uuidString
        let id = attemptID
        capture.attempts.append(PWRunnerAcquisitionAttempt(ordinal: capture.attempts.count + 1, attempt_id: id,
            started_elapsed_ms: elapsed(now), ended_elapsed_ms: elapsed(now), outcome: "local_error"))
        let lease = min(PWRunnerTransportLimits.reservationLeaseMs, remainingMs(now))
        let bytes: Data
        do { bytes = try pwRunnerEncodeJSON(PWRunnerReservationRequest(attempt_id: id, lease_ms: lease)) }
        catch {
            let failure = PWRunnerTransportError(stage: "local", reason: "encoding_failed", message: "reservation encoding failed")
            endAttempt("local_error", error: failure); capture.acquisition_stop = "local_error"
            complete("local_error", error: failure); return
        }
        connection = connect { failure in self.enqueue { self.connectionFailed(id, failure) } }
        // The factory can report a synchronous failure under a test queue.
        guard phase == .acquiring, attemptID == id else { connection?.invalidate(); connection = nil; return }
        let rpcDeadline = min(deadline!,
            PWContinuousClock.adding(milliseconds: UInt64(PWRunnerTransportLimits.reservationRPCMs), to: now))
        schedule(min(PWRunnerTransportLimits.reservationRPCMs, remainingMs(now))) {
            self.enqueue { self.reservationTimeout(id, deadline: rpcDeadline) }
        }
        connection?.reserve(bytes) { data in self.enqueue { self.reservationReply(id, data: data, requestedLease: lease) } }
    }
    private func endAttempt(_ outcome: String, control: PWRunnerControlObservation? = nil, error: PWRunnerTransportError? = nil) {
        guard !capture.attempts.isEmpty else { return }
        let i = capture.attempts.count - 1
        capture.attempts[i].ended_elapsed_ms = elapsed(lastNow)
        capture.attempts[i].outcome = outcome
        capture.attempts[i].control = control
        capture.attempts[i].error = error
    }
    private func retry() {
        guard phase == .acquiring else { return }
        phase = .waiting
        let old = connection; connection = nil
        old?.invalidate()
        guard let now = sample() else { return }
        guard remainingMs(now) > 0 else { overallTimeout(); return }
        if capture.attempts.count >= PWRunnerTransportLimits.acquisitionAttempts { beginAttempt(); return }
        schedule(min(PWRunnerTransportLimits.retryDelayMs, remainingMs(now))) {
            self.enqueue { if self.phase == .waiting { self.beginAttempt() } }
        }
    }
    private func reservationTimeout(_ id: String, deadline: UInt64) {
        guard phase == .acquiring, attemptID == id, let now = sample() else { return }
        guard now >= deadline else {
            schedule(Int(min(UInt64(100), (deadline - now) / 1_000_000 + 1))) {
                self.enqueue { self.reservationTimeout(id, deadline: deadline) }
            }
            return
        }
        if now >= self.deadline! { overallTimeout(); return }
        endAttempt("timeout", error: .init(stage: "acquisition", reason: "rpc_timeout", message: "reservation RPC deadline expired"))
        retry()
    }
    private func connectionFailed(_ id: String, _ failure: PWRunnerConnectionFailure) {
        guard attemptID == id, phase == .acquiring || phase == .submitted, let now = sample() else { return }
        guard now < deadline! else { overallTimeout(); return }
        let stage = phase == .submitted ? "submission" : "acquisition"
        let error = PWRunnerTransportError(stage: stage, reason: failure.reason, message: failure.message, error: failure.error)
        if phase == .submitted { complete("xpc_error", error: error); return }
        if failure.reason == "proxy_type_mismatch" {
            endAttempt("local_error", error: error); capture.acquisition_stop = "local_error"
            complete("local_error", error: error); return
        }
        endAttempt("transport_error", error: error)
        retry()
    }
    private func decodeControl(_ data: Data) throws -> PWRunnerControlReply {
        guard data.count <= PWRunnerTransportLimits.controlBytes else { throw ControlFailure.tooLarge }
        struct Version: Decodable { var protocol_version: Int }
        let version = try pwRunnerDecodeJSON(Version.self, from: data)
        guard version.protocol_version == PWContract.runnerProtocol else { throw ControlFailure.unsupported }
        let reply = try pwRunnerDecodeJSON(PWRunnerControlReply.self, from: data)
        guard reply.host_pid > 0, reply.host_pid <= Int(Int32.max),
              reply.host_instance.utf8.count == 36, UUID(uuidString: reply.host_instance) != nil else {
            throw ControlFailure.invalid
        }
        return reply
    }
    private enum ControlFailure: Error, Equatable { case tooLarge, unsupported, invalid }
    private func controlError(_ error: Error, stage: String) -> PWRunnerTransportError {
        let reason = (error as? ControlFailure) == .tooLarge ? "control_too_large"
            : (error as? ControlFailure) == .unsupported ? "unsupported_protocol" : "invalid_control"
        return .init(stage: stage, reason: reason, message: "invalid or unsupported runner control response")
    }
    private func reservationReply(_ id: String, data: Data, requestedLease: Int) {
        guard phase == .acquiring, attemptID == id, let now = sample() else { return }
        let reply: PWRunnerControlReply
        do {
            reply = try decodeControl(data)
            guard reply.attempt_id == id, reply.reason == nil else { throw ControlFailure.invalid }
            switch reply.status {
            case "granted":
                guard let token = reply.reservation_id, token.utf8.count == 36, UUID(uuidString: token) != nil,
                      let lease = reply.lease_ms, lease > 0, lease <= requestedLease else { throw ControlFailure.invalid }
            case "occupied":
                guard reply.reservation_id == nil, reply.lease_ms == nil else { throw ControlFailure.invalid }
            default: throw ControlFailure.invalid
            }
        } catch {
            let error = controlError(error, stage: "acquisition")
            endAttempt("protocol_error", control: PWRunnerControlObservation(data), error: error)
            capture.acquisition_stop = "protocol_error"; complete("protocol_error", error: error); return
        }
        endAttempt(reply.status, control: PWRunnerControlObservation(data, admitted: reply))
        if reply.status == "occupied" { retry(); return }
        phase = .reserved
        capture.acquisition_stop = "granted"
        // Do not reset the allowance when a grant arrives. A grant processed
        // after the original deadline must remain explicitly not_invoked.
        guard let at = sample(), phase != .done else { return }
        guard at < deadline! else { overallTimeout(); return }
        phase = .submitted
        capture.submission = PWRunnerSubmission(state: "invoked", invoked_elapsed_ms: elapsed(at))
        connection?.submit(request, reservation: reply.reservation_id!) { isResult, bytes in
            self.enqueue { self.submissionReply(id, isResult: isResult, data: bytes) }
        }
        _ = now // The receipt's end sample was taken before control admission.
    }
    private func submissionReply(_ id: String, isResult: Bool, data: Data) {
        guard phase == .submitted, attemptID == id, let now = sample() else { return }
        guard now < deadline! else { overallTimeout(); return }
        if isResult {
            capture.runner_reply = PWRunnerReplyCapture(data)
            complete("runner_reply"); return
        }
        do {
            let reply = try decodeControl(data)
            guard reply.status == "reservation_refused", reply.attempt_id == nil, reply.reservation_id == nil,
                  reply.lease_ms == nil, let reason = reply.reason,
                  ["wrong", "expired", "absent", "consumed", "clock_error"].contains(reason) else { throw ControlFailure.invalid }
            capture.submission_refusal = PWRunnerControlObservation(data, admitted: reply)
            complete("submission_refused")
        } catch {
            capture.submission_refusal = PWRunnerControlObservation(data)
            complete("protocol_error", error: controlError(error, stage: "submission"))
        }
    }
    private func complete(_ terminal: String, error: PWRunnerTransportError? = nil) {
        guard phase != .done else { return }
        phase = .done
        capture.terminal = terminal; capture.error = error; capture.ended_continuous_ns = lastNow
        let old = connection; connection = nil
        old?.invalidate()
        finish(capture)
    }
}

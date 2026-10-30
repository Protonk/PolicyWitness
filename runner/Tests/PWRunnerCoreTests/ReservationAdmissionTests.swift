import Foundation
@testable import PWRunnerCore

func runReservationAdmissionTests(_ tk: TestKit) {
    tk.group("reservation lifecycle and transport limits") {
        tk.run("compiled transport constants agree with the inventory") {
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let manifest = try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent("docs/limits.json"))) as! [String: Any]
            let rows = manifest["limits"] as! [[String: Any]]
            let values = Dictionary(uniqueKeysWithValues: rows.map { ($0["id"] as! String, $0["value"] as! Int) })
            let observed = [
                "reservation_lease": PWRunnerTransportLimits.reservationLeaseMs,
                "reservation_rpc_wait": PWRunnerTransportLimits.reservationRPCMs,
                "reservation_attempts": PWRunnerTransportLimits.acquisitionAttempts,
                "reservation_retry_delay": PWRunnerTransportLimits.retryDelayMs,
                "reservation_control_bytes": PWRunnerTransportLimits.controlBytes,
                "client_error_message": PWRunnerTransportLimits.errorMessageBytes,
                "client_error_domain": PWRunnerTransportLimits.errorDomainBytes,
                "client_reply_retention": PWRunnerTransportLimits.runnerReplyBytes,
            ]
            let owned = rows.filter { row in (row["checks"] as! [[String: Any]]).contains {
                ($0["kind"] as? String) == "value" && ($0["path"] as? String)?.hasSuffix("/ReservationAdmissionTests.swift") == true
            } }
            try expectEqual(Set(owned.map { $0["id"] as! String }), Set(observed.keys))
            for (name, value) in observed { try expectEqual(value, values[name]!, name) }
        }
        tk.run("lease limits, connection binding and terminal owner actions") {
            var now: UInt64 = 1_000_000_000
            let owner = PWRunnerAdmission.Connection(), foreign = PWRunnerAdmission.Connection(), state = PWRunnerAdmission(clock: { now })
            try expectFalse(state.reserve(owner: owner, leaseMs: 0).accepted)
            let held = state.reserve(owner: owner, leaseMs: 5001).reservation!
            try expectEqual(held.leaseMs, 5000)
            try expectEqual(held.expiry - now, 5_000_000_000)
            try expectEqual(state.reserve(owner: foreign, leaseMs: 1).reason, "occupied")
            try expectEqual(state.submit(owner: foreign, token: held.token).reason, "wrong")
            try expectEqual(state.submit(owner: owner, token: UUID().uuidString).reason, "wrong")
            try expectFalse(state.disconnected(owner: foreign))
            now = held.expiry - 1
            try expectFalse(state.expire(owner: owner, token: held.token))
            try expectTrue(state.submit(owner: owner, token: held.token).accepted)
            now = held.expiry + 1
            try expectFalse(state.expire(owner: owner, token: held.token), "late timer cannot retire an executing owner")
            try expectFalse(state.disconnected(owner: owner), "execution retains its worker ownership")
            try expectFalse(state.complete(owner: foreign, token: held.token))
            try expectTrue(state.complete(owner: owner, token: held.token))
            try expectFalse(state.complete(owner: owner, token: held.token), "retire exactly once")
            try expectEqual(state.reserve(owner: owner, leaseMs: 1).reason, "occupied")
        }
        tk.run("expiry and disconnect never release a slot for reuse") {
            for event in ["timer", "submit", "reserve", "disconnect"] {
                var now: UInt64 = 100
                let owner = PWRunnerAdmission.Connection(), state = PWRunnerAdmission(clock: { now })
                let held = state.reserve(owner: owner, leaseMs: 1).reservation!
                now = held.expiry
                switch event {
                case "timer": try expectTrue(state.expire(owner: owner, token: held.token))
                case "submit":
                    let refusal = state.submit(owner: owner, token: held.token)
                    try expectFalse(refusal.accepted); try expectTrue(refusal.retire)
                    try expectEqual(refusal.reason, "expired")
                case "reserve": try expectTrue(state.reserve(owner: PWRunnerAdmission.Connection(), leaseMs: 1).retire)
                default: try expectTrue(state.disconnected(owner: owner))
                }
                try expectFalse(state.expire(owner: owner, token: held.token))
                try expectFalse(state.disconnected(owner: owner))
                try expectFalse(state.submit(owner: owner, token: held.token).accepted)
                try expectEqual(state.reserve(owner: PWRunnerAdmission.Connection(), leaseMs: 1).reason, "occupied")
            }
        }
        tk.run("invalidation before reservation refuses a queued call without claiming a slot") {
            let state = PWRunnerAdmission()
            var exits = 0, timers = 0
            let stale = PWRunnerService(admission: state, scheduleExit: { exits += 1 },
                scheduleExpiry: { _, _ in timers += 1 })
            let fresh = PWRunnerService(admission: state, scheduleExit: { exits += 1 },
                scheduleExpiry: { _, _ in timers += 1 })
            stale.connectionInvalidated()
            stale.connectionInvalidated()
            let request = try pwRunnerEncodeJSON(PWRunnerReservationRequest(attempt_id: UUID().uuidString, lease_ms: 5000))
            var refused: PWRunnerControlReply?, grant: PWRunnerControlReply?
            stale.reserveRunner(request) { refused = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: $0) }
            try expectEqual(refused?.status, "occupied")
            try expectNil(refused?.reservation_id)
            try expectEqual(timers, 0); try expectEqual(exits, 0)
            fresh.reserveRunner(request) { grant = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: $0) }
            try expectEqual(grant?.status, "granted", "idle invalidation cannot consume a different connection's fresh slot")
            try expectEqual(timers, 1)
            stale.runReservedSpecimen(Data("{".utf8), reservation: grant!.reservation_id!) { isResult, data in
                if !isResult { refused = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: data) }
            }
            try expectEqual(refused?.reason, "wrong", "invalidated connection cannot submit the new owner's token")
            try expectEqual(exits, 0)
            fresh.connectionInvalidated()
            try expectEqual(exits, 1, "unused owner disconnect retires exactly once")
            fresh.connectionInvalidated()
            fresh.reserveRunner(request) { refused = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: $0) }
            try expectEqual(refused?.status, "occupied"); try expectEqual(exits, 1)
        }
        tk.run("reservation control bound and protocol gate precede specimen work") {
            for size in [65535, 65536, 65537] {
                let state = PWRunnerAdmission(), owner = PWRunnerService(admission: state, scheduleExit: {}, scheduleExpiry: { _, _ in })
                let raw = try pwRunnerEncodeJSON(PWRunnerReservationRequest(attempt_id: UUID().uuidString, lease_ms: 1))
                let padded = raw + Data(repeating: 32, count: size - raw.count)
                var control: PWRunnerControlReply?
                owner.reserveRunner(padded) { control = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: $0) }
                try expectEqual(control?.status, size <= 65536 ? "granted" : "invalid_request")
                try expectEqual(control?.reason, size <= 65536 ? nil : "control_too_large")
            }
            let owner = PWRunnerService(admission: PWRunnerAdmission(), scheduleExit: {}, scheduleExpiry: { _, _ in })
            var control: PWRunnerControlReply?
            owner.reserveRunner(Data("{\"protocol_version\":1,\"future_body\":true}".utf8)) {
                control = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: $0)
            }
            try expectEqual(control?.status, "unsupported_protocol")
            try expectNil(control?.reservation_id)
        }
        tk.run("clock failure cannot mint a reservation") {
            let state = PWRunnerAdmission(clock: { UInt64.max })
            let failed = state.reserve(owner: PWRunnerAdmission.Connection(), leaseMs: 1)
            try expectFalse(failed.accepted); try expectNil(failed.reservation)
            try expectEqual(failed.reason, "clock_error")
            try expectEqual(PWContinuousClock.adding(milliseconds: UInt64.max, to: 100), UInt64.max)
            var now: UInt64 = 10
            let heldState = PWRunnerAdmission(clock: { now }), owner = PWRunnerAdmission.Connection()
            let held = heldState.reserve(owner: owner, leaseMs: 1).reservation!
            now = UInt64.max
            let refusal = heldState.submit(owner: owner, token: held.token)
            try expectEqual(refusal.reason, "clock_error", "unavailable time is not observed expiry")
            try expectTrue(refusal.retire)
            try expectEqual(heldState.submit(owner: owner, token: held.token).reason, "clock_error")
        }
        tk.run("service expiry rearms early callbacks and cannot retire execution") {
            var now: UInt64 = 1_000_000_000
            var pending: [(Int, () -> Void)] = [], exits = 0
            let state = PWRunnerAdmission(clock: { now })
            let service = PWRunnerService(admission: state, scheduleExit: { exits += 1 },
                scheduleExpiry: { pending.append(($0, $1)) })
            let request = try pwRunnerEncodeJSON(PWRunnerReservationRequest(attempt_id: UUID().uuidString, lease_ms: 5000))
            var grant: PWRunnerControlReply?
            service.reserveRunner(request) { grant = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: $0) }
            try expectEqual(pending[0].0, 100, "short tick bounds post-sleep observation delay")
            pending.removeFirst().1()
            try expectEqual(exits, 0); try expectEqual(pending.count, 1, "early callback rearmed")
            now += 5_000_000_000
            pending.removeFirst().1()
            try expectEqual(exits, 1); try expectTrue(pending.isEmpty)
            var refused: PWRunnerControlReply?
            service.runReservedSpecimen(Data(), reservation: grant!.reservation_id!) { isResult, bytes in
                if !isResult { refused = try! pwRunnerDecodeJSON(PWRunnerControlReply.self, from: bytes) }
            }
            try expectEqual(refused?.reason, "expired"); try expectEqual(exits, 1)
        }
        tk.run("native error bytes are bounded without splitting UTF8 scalars") {
            for n in [127, 128, 129] {
                let native = NSError(domain: String(repeating: "d", count: n), code: 4097,
                    userInfo: [NSLocalizedDescriptionKey: String(repeating: "m", count: 1024)])
                let captured = PWRunnerTransportError(stage: "acquisition", reason: "xpc_error", message: "unused", error: native)
                try expectEqual(captured.domain?.utf8.count, min(n, 128))
                try expectEqual(captured.domain_truncated, n > 128)
                try expectFalse(captured.message_truncated)
                try expectEqual(captured.code, 4097)
            }
            for n in [1023, 1024, 1025] {
                let captured = PWRunnerTransportError(stage: "local", reason: "input_read_failed", message: String(repeating: "m", count: n))
                try expectEqual(captured.message.utf8.count, min(n, 1024))
                try expectEqual(captured.message_truncated, n > 1024)
                try expectNil(captured.domain); try expectNil(captured.code)
            }
            let scalar = pwTransportBoundedString(String(repeating: "é", count: 513), bytes: 1023)
            try expectEqual(scalar.0.utf8.count, 1022); try expectTrue(scalar.1)
        }
        tk.run("retained reply boundary and maximal encoded capture fit controller stdout") {
            for n in [67_108_863, 67_108_864, 67_108_865] {
                let captured = PWRunnerReplyCapture(Data(repeating: 0xff, count: n))
                try expectEqual(captured.bytes_received, n)
                try expectEqual(captured.bytes_retained, min(n, 67_108_864))
                try expectEqual(captured.truncated, n > 67_108_864)
                try expectEqual(Data(base64Encoded: captured.data_base64)?.count, min(n, 67_108_864))
            }
            try expectTrue(try maximalReplyEncodedSize() < 67_108_864, "normal maximum must fit retained reply bytes")
            // Escapable ASCII uses six JSON bytes per retained UTF8 byte. This
            // field superset deliberately overcounts combinations a session emits.
            var error = PWRunnerTransportError(stage: "acquisition", reason: "xpc_error", message: "")
            error.domain = String(repeating: "\0", count: 128); error.code = Int.min
            error.message = String(repeating: "\0", count: 1024)
            error.domain_truncated = true; error.message_truncated = true
            var frame = PWRunnerClientCapture(started_continuous_ns: UInt64.max - 1,
                deadline_continuous_ns: UInt64.max - 1, ended_continuous_ns: UInt64.max - 1, timeout_ms: UInt64.max)
            frame.attempts = (1...256).map { PWRunnerAcquisitionAttempt(ordinal: $0,
                attempt_id: UUID().uuidString, started_elapsed_ms: UInt64.max, ended_elapsed_ms: UInt64.max,
                outcome: "transport_error", error: error) }
            var control = PWRunnerControlObservation(Data(repeating: 0, count: 65536),
                admitted: PWRunnerControlReply(status: "reservation_refused", host_pid: Int.max,
                    host_instance: UUID().uuidString, lease_ms: 5000, reason: "clock_error"))
            control.bytes_received = Int.max
            for i in frame.attempts.indices { frame.attempts[i].control = control }
            frame.submission_refusal = control
            frame.error = error
            frame.runner_reply = PWRunnerReplyCapture(Data(repeating: 0xff, count: 67_108_864))
            frame.submission = PWRunnerSubmission(state: "invoked", invoked_elapsed_ms: UInt64.max)
            let encoded = try pwRunnerEncodeClientCapture(frame)
            try expectTrue(encoded.count + 1 < 152 * 1024 * 1024, "max capture plus newline fits public stdout frame")
        }
    }
}

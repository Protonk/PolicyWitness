import Darwin
import Foundation
@testable import PWRunnerCore

private func metadata(_ size: Int64) -> PWRunnerFileStat {
    PWRunnerFileStat(rc: 0, identity: PWFileIdentity(device: 1, inode: 2, mode: 33152, uid: 501, gid: 20), size: size)
}

func freshWriteFixture(creating: Bool = false) -> PWRunnerFreshWrite {
    PWRunnerFreshWrite(open_rc: 5, truncate_rc: creating ? nil : 0, write_rc: 1, close_rc: 0,
        preopen_stat: creating ? PWRunnerFileStat(rc: -1, errno: ENOENT) : nil,
        opened_stat: metadata(creating ? 0 : 19), truncated_stat: creating ? nil : metadata(0), written_stat: metadata(1))
}

func freshWriteReplyFixture(_ write: PWRunnerFreshWrite, creating: Bool = false,
                            rc: Int = 0, errno: Int? = nil) -> PWRunnerRunResult {
    var reply = extensionReplyFixture()
    reply.extensions?[0].extension_class = "com.apple.app-sandbox.read-write"
    reply.steps[0].attempt.requested_action = creating ? "create_fresh" : "write_fresh"
    reply.steps[0].attempt.fresh_read = nil
    reply.steps[0].attempt.fresh_write = write
    reply.steps[0].attempt.rc = rc
    reply.steps[0].attempt.errno = errno
    reply.steps[0].attempt.outcome = rc == 0 ? AttemptOutcome.ok : AttemptOutcome.writeFailed
    reply.steps[0].comparison?.operation_relation = creating ? "unresolved" : "different"
    reply.steps[0].comparison?.observation = rc == 0 ? "succeeded" : [1, 13].contains(errno ?? 0) ? "permission_failure" : "other_failure"
    reply.steps[0].comparison?.observation_basis = rc != 0 && [1, 13].contains(errno ?? 0) ? "permission_errno" : "completed_worker_status"
    return reply
}

func freshWriteShapeDocuments() throws -> [[String: Any]] {
    var replies = [freshWriteReplyFixture(freshWriteFixture()),
                   freshWriteReplyFixture(freshWriteFixture(creating: true), creating: true)]
    replies.append(freshWriteReplyFixture(PWRunnerFreshWrite(open_rc: -1, open_errno: 17,
        preopen_stat: metadata(19)), creating: true, rc: -1, errno: 17))
    let metadataFailure = PWRunnerFileStat(rc: -1, errno: 9)
    replies.append(freshWriteReplyFixture(PWRunnerFreshWrite(open_rc: 5, write_rc: -1, write_errno: 5,
        close_rc: -1, close_errno: 4, preopen_stat: PWRunnerFileStat(rc: -1, errno: 13),
        opened_stat: metadataFailure, written_stat: metadataFailure), creating: true, rc: -1, errno: 9))
    replies.append(freshWriteReplyFixture(PWRunnerFreshWrite(open_rc: 5, truncate_rc: -1, truncate_errno: 1,
        close_rc: -1, close_errno: 9, opened_stat: metadata(19), truncated_stat: metadataFailure), rc: -1, errno: 1))
    return try replies.map { try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON($0)) as! [String: Any] }
}

func runFreshWriteEvidenceTests(_ tk: TestKit) {
    tk.group("bounded extension authority admission") {
        func request(_ authority: Any?) -> [String: Any] {
            var declaration: [String: Any] = ["token_ref": "token", "target": "/private/tmp"]
            if let authority { declaration["authority"] = authority }
            return ["schema_version": PWContract.requestSchema, "specimen_id": "authority",
                "policy": ["format": "sbpl", "sbpl_source": "(version 1)(allow default)"],
                "extensions": [declaration], "phases": [["phase_id": "p", "actions": []]]]
        }
        func decode(_ value: [String: Any]) throws -> PWRunnerRunSpec {
            try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: JSONSerialization.data(withJSONObject: value))
        }
        tk.run("absent and null preserve read while explicit authorities remain distinct") {
            for value in [nil, NSNull(), "read", "read_write"] as [Any?] {
                let parsed = try decode(request(value))
                try expectNil(requestMeaningFailure(parsed))
                let declaration = parsed.extensions![0]
                let rw = (value as? String) == "read_write"
                try expectEqual(declaration.effectiveAuthority, rw ? "read_write" : "read")
                try expectEqual(declaration.nativeClass, rw ? "com.apple.app-sandbox.read-write" : "com.apple.app-sandbox.read")
                let roundTrip = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: pwRunnerEncodeJSON(parsed))
                try expectEqual(roundTrip.extensions?[0].authority, declaration.authority)
            }
        }
        tk.run("unknown authority is a bounded semantic refusal; wrong types and raw class/token stay closed") {
            for authority in ["", "write", "READ", "com.apple.app-sandbox.read-write", "read\0"] {
                let failure = requestMeaningFailure(try decode(request(authority)))
                try expectEqual(failure?.code, "unsupported_extension_authority")
                try expectEqual(failure?.path, ["extensions", "0", "authority"])
            }
            for value in [1, true, ["read"], ["authority": "read"]] as [Any] {
                try expectThrows { _ = try decode(request(value)) }
            }
            for key in ["extension_class", "token"] {
                var input = request("read_write")
                var declarations = input["extensions"] as! [[String: Any]]
                declarations[0][key] = "not accepted"
                input["extensions"] = declarations
                do { _ = try decode(input); throw TestFailure(message: "raw authority field accepted") }
                catch let error as RequestContractError {
                    try expectEqual(requestDecodeFailure(error).code, "unknown_field")
                    try expectEqual(requestDecodeFailure(error).path, ["extensions", "0", key])
                }
            }
        }
        tk.run("native class output accepts exactly the two supported classes") {
            for value in ["com.apple.app-sandbox.read", "com.apple.app-sandbox.read-write"] {
                var reply = extensionReplyFixture(); reply.extensions?[0].extension_class = value
                try expectNil(reply.extensionEvidenceProblem())
            }
            var reply = extensionReplyFixture(); reply.extensions?[0].extension_class = "write"
            try expectTrue(reply.extensionEvidenceProblem() != nil)
        }
    }
    tk.group("fresh write evidence and failure ordering") {
        tk.run("the step builder exposes completed write payloads and withholds unpublished storage") {
            let step = PWRunnerProbeStep(step_id: "write",
                sandbox_check: PWRunnerSandboxCheck(operation: "file-write-data", filter: PWRunnerSandboxFilter(kind: "path", value: "/target")),
                attempt: PWRunnerAttempt(kind: "file", action: "write_fresh", target: "/target"))
            for completed in [false, true] {
                let slot = CWorkerSlotResult(freshWrite: freshWriteFixture(), stepId: "write", rc: 0, errnoVal: 0, completed: completed)
                let result = buildAttemptResult(step: step, slot: slot)
                try expectEqual(result.outcome, completed ? "ok" : "no_completed_result")
                try expectEqual(result.fresh_write != nil, completed)
            }
        }
        tk.run("valid writes, creation, open refusal and multiple syscall failures survive encoding") {
            for document in try freshWriteShapeDocuments() {
                let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: document))
                try expectNil(decoded.steps[0].attempt.freshWriteEvidenceProblem())
                _ = try pwRunnerEncodeJSON(decoded)
            }
        }
        tk.run("pre-open metadata is diagnostic and short writes do not invent errno") {
            var created = freshWriteFixture(creating: true)
            created.preopen_stat = PWRunnerFileStat(rc: -1, errno: EACCES)
            _ = try pwRunnerEncodeJSON(freshWriteReplyFixture(created, creating: true))
            var short = freshWriteFixture()
            short.write_rc = 0; short.written_stat = metadata(0)
            short.close_rc = -1; short.close_errno = 9
            let reply = freshWriteReplyFixture(short, rc: -1)
            try expectNil(reply.steps[0].attempt.freshWriteEvidenceProblem())
            _ = try pwRunnerEncodeJSON(reply)
            var replaced = reply; replaced.steps[0].attempt.errno = 9
            try expectTrue(replaced.steps[0].attempt.freshWriteEvidenceProblem() != nil)
        }
        tk.run("the first descriptor metadata failure survives later syscall failures") {
            var write = freshWriteFixture()
            write.opened_stat = PWRunnerFileStat(rc: -1, errno: 9)
            write.truncate_rc = -1; write.truncate_errno = 1
            write.truncated_stat = PWRunnerFileStat(rc: -1, errno: 5)
            write.write_rc = nil; write.written_stat = nil
            write.close_rc = -1; write.close_errno = 4
            let reply = freshWriteReplyFixture(write, rc: -1, errno: 9)
            try expectNil(reply.steps[0].attempt.freshWriteEvidenceProblem())
            _ = try pwRunnerEncodeJSON(reply)
        }
        tk.run("missing or impossible syscall records are rejected by encoding and reading") {
            let changes: [(inout PWRunnerAttemptResult) -> Void] = [
                { $0.fresh_write = nil },
                { $0.fresh_write?.open_rc = -2 },
                { $0.fresh_write?.open_rc = -1; $0.fresh_write?.open_errno = 1 },
                { $0.fresh_write?.open_errno = 1 },
                { $0.fresh_write?.opened_stat = nil },
                { $0.fresh_write?.opened_stat?.identity = nil },
                { $0.fresh_write?.opened_stat?.size = nil },
                { $0.fresh_write?.opened_stat?.errno = 5 },
                { $0.fresh_write?.opened_stat?.rc = -1 },
                { $0.fresh_write?.truncate_rc = nil },
                { $0.fresh_write?.truncate_errno = 5 },
                { $0.fresh_write?.truncated_stat = nil },
                { $0.fresh_write?.truncate_rc = -1; $0.fresh_write?.truncate_errno = 1 },
                { $0.fresh_write?.write_rc = 2 },
                { $0.fresh_write?.write_rc = 0 },
                { $0.fresh_write?.write_rc = -1 },
                { $0.fresh_write?.write_errno = 5 },
                { $0.fresh_write?.written_stat = nil },
                { $0.fresh_write?.close_rc = nil },
                { $0.fresh_write?.close_rc = -1 },
                { $0.fresh_write?.preopen_stat = PWRunnerFileStat(rc: -1, errno: 2) },
                { $0.result_source = "synthetic" },
                { $0.requested_action = "open_write" },
                { $0.rc = -1; $0.errno = 1; $0.outcome = "write_failed" },
            ]
            for (index, change) in changes.enumerated() {
                var reply = freshWriteReplyFixture(freshWriteFixture())
                change(&reply.steps[0].attempt)
                try expectTrue(reply.steps[0].attempt.freshWriteEvidenceProblem() != nil, "mutation \(index) admitted")
                try expectThrows { _ = try pwRunnerEncodeJSON(reply) }
                // Encoding the isolated attempt preserves the corrupt input for
                // an independent full-reply decoder check.
                var document = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(freshWriteReplyFixture(freshWriteFixture()))) as! [String: Any]
                var steps = document["steps"] as! [[String: Any]]
                steps[0]["attempt"] = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(reply.steps[0].attempt))
                document["steps"] = steps
                try expectThrows { _ = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: document)) }
            }
            let createChanges: [(inout PWRunnerFreshWrite) -> Void] = [
                { $0.preopen_stat = nil },
                { $0.truncate_rc = 0; $0.truncated_stat = metadata(0) },
            ]
            for change in createChanges {
                var value = freshWriteFixture(creating: true); change(&value)
                try expectThrows { _ = try pwRunnerEncodeJSON(freshWriteReplyFixture(value, creating: true)) }
            }
        }
        tk.run("raw ABI decoding preserves widths and omits only unattempted operations") {
            let memory = UnsafeMutableRawPointer.allocate(byteCount: PWShmLayout.slotBytes, alignment: 8)
            defer { memory.deallocate() }
            memory.initializeMemory(as: UInt8.self, repeating: 0, count: PWShmLayout.slotBytes)
            let base = PWShmLayout.slotFreshWriteOffset
            func word(_ offset: Int, _ value: Int32) { memory.storeBytes(of: value, toByteOffset: base + offset, as: Int32.self) }
            for offset in [PWShmLayout.freshWriteTruncateRcOffset, PWShmLayout.freshWriteCloseRcOffset,
                           PWShmLayout.freshWritePreopenStatOffset, PWShmLayout.freshWriteOpenedStatOffset,
                           PWShmLayout.freshWriteTruncatedStatOffset, PWShmLayout.freshWriteWrittenStatOffset] { word(offset, -2) }
            memory.storeBytes(of: Int64(-2), toByteOffset: base + PWShmLayout.freshWriteWriteRcOffset, as: Int64.self)
            word(PWShmLayout.freshWriteOpenRcOffset, -1); word(PWShmLayout.freshWriteOpenErrnoOffset, 13)
            let failed = decodeFreshWrite(memory.assumingMemoryBound(to: UInt8.self))
            try expectEqual(failed.open_rc, -1); try expectEqual(failed.open_errno, 13)
            try expectNil(failed.write_rc); try expectNil(failed.truncate_rc); try expectNil(failed.close_rc)
            try expectNil(failed.opened_stat); try expectNil(failed.preopen_stat)
            let stat = PWShmLayout.freshWriteOpenedStatOffset
            word(stat + PWShmLayout.fileStatRcOffset, 0)
            memory.storeBytes(of: UInt64.max, toByteOffset: base + stat + PWShmLayout.fileStatDeviceOffset, as: UInt64.self)
            memory.storeBytes(of: UInt64.max - 1, toByteOffset: base + stat + PWShmLayout.fileStatInodeOffset, as: UInt64.self)
            memory.storeBytes(of: Int64.max, toByteOffset: base + stat + PWShmLayout.fileStatSizeOffset, as: Int64.self)
            let observed = decodeFreshWrite(memory.assumingMemoryBound(to: UInt8.self))
            try expectEqual(observed.opened_stat?.identity?.device, UInt64.max)
            try expectEqual(observed.opened_stat?.identity?.inode, UInt64.max - 1)
            try expectEqual(observed.opened_stat?.size, Int64.max)
        }
    }
}

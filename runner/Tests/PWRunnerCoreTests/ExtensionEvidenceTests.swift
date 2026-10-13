import Darwin
import Foundation
@testable import PWRunnerCore

// Constructed observations establish encoding/reading rules, not native effects.
func extensionReplyFixture(published: Bool = true, available: Bool = true) -> PWRunnerRunResult {
    let ids = ["consume", "read", "release"]
    let identity = PWFileIdentity(device: 1, inode: 2, mode: 33188, uid: 501, gid: 20)
    let read = PWRunnerFreshRead(open_rc: 5, read_rc: 2, stat_rc: 0, identity: identity,
                                close_rc: 0, content_hex: "5057")
    var out = CWorkerOutput(workerPid: 42, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0,
        done: published, exitCode: 0, termSignal: nil,
        slots: ids.map { CWorkerSlotResult(freshRead: $0 == "read" && published ? read : nil,
            stepId: $0, rc: 0, errnoVal: 0, completed: published) },
        pollStopReason: "child_reaped", reaped: true, waitErrors: [], proceedObserved: true)
    out.collectionBasis = "after_confirmed_reap"
    let disposition = resolveDisposition(out, plan: nil)
    let probe = PWRunnerProbeStep(step_id: "read",
        sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data", filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
        attempt: PWRunnerAttempt(kind: "file", action: "read_fresh", target: "/etc/hosts"))
    let phase = constructedPhase(out, ids: ids)
    let ordinary = buildStepResults(probePlan: [probe], queryPlan: planValidatorQueries([probe]), workerOutput: out,
        validatorOutput: nil, ordering: phase.ordering, disposition: disposition)
    var issuer = PWRunnerIssuer(executable_path: "/constructed/pw-extension-issuer", pid: 43,
        uid: 501, euid: 501, gid: 20, egid: 20, call_boundary_observed: true, result_published: true,
        native_nonnull: available, errno: 0, token_length: available ? 12 : nil, reaped: true, exit_code: 0)
    issuer.wait_errors = [PWRunnerWaitError(stage: "issuer_wait", rc: -1, errno: 4)]
    let declaration = PWRunnerExtensionRecord(token_ref: "token", submitted_target: "/etc/hosts",
        resolved_target: "/private/etc/hosts", preparation_status: "prepared", identity: identity,
        issuance_status: available ? "issued" : "native_refusal", issuer: issuer,
        delivery_status: available ? "delivered" : "token_unavailable", delivered_bytes: available ? 12 : nil,
        host_buffer_erased: true)
    let events = [0, 2].map { index in
        PWRunnerExtensionEvent(phase_id: "main", step_id: ids[index], operation: ids[index],
            token_ref: index == 0 ? "token" : nil, handle_ref: "handle",
            call_boundary_observed: available && (published || index == 0), result_published: published,
            status: !published ? "unresolved" : available ? "returned" : "unavailable",
            native_result: published && available ? (index == 0 ? Int64.max : 0) : nil,
            errno: published && available ? 0 : nil,
            unavailable_reason: published && !available ? (index == 0 ? "token_unavailable" : "handle_unavailable") : nil,
            lifecycle: attemptLifecycle(disposition.steps[index]))
    }
    return PWRunnerRunResult(specimen_id: "constructed-extension", rc: 0, normalized_outcome: "ok", pid: 42,
        policy_format: "sbpl", sandboxed_after_apply: true, steps: ordinary,
        runner_subprocess: buildWorkerSubprocess(out, disposition: disposition), phases: [phase],
        extensions: [declaration], extension_events: events,
        test_overrides: PWRunnerTestOverrides(issuer_executable_path: "/constructed/issuer"))
}

func extensionShapeDocuments() throws -> [[String: Any]] {
    var replies = [extensionReplyFixture(), extensionReplyFixture(published: false), extensionReplyFixture(available: false)]
    var failed = extensionReplyFixture(available: false)
    failed.extensions?[0].issuance_status = "issuer_timeout"
    failed.extensions?[0].issuer?.termination_request = PWRunnerTerminationRequest(signal: 9, rc: -1, errno: 1)
    failed.extensions?[0].issuer?.term_signal = 9
    failed.extensions?[0].issuer?.exit_code = nil
    failed.steps[0].attempt.fresh_read = PWRunnerFreshRead(open_rc: -1, open_errno: 13)
    failed.steps[0].attempt.rc = -1
    failed.steps[0].attempt.errno = 13
    failed.steps[0].attempt.outcome = AttemptOutcome.readFailed
    replies.append(failed)
    var preparation = extensionReplyFixture(available: false)
    preparation.extensions?[0].preparation_status = "metadata_failed"
    preparation.extensions?[0].preparation_errno = 13
    preparation.extensions?[0].identity = nil
    preparation.extensions?[0].issuance_status = "not_started"
    preparation.extensions?[0].issuer = nil
    replies.append(preparation)
    var spawn = extensionReplyFixture(available: false)
    spawn.extensions?[0].issuance_status = "spawn_failed"
    spawn.extensions?[0].issuer = PWRunnerIssuer(executable_path: "/constructed/issuer",
        spawn_failure: PWRunnerSpawnFailure(executable_path: "/constructed/issuer", return_code: 2, diagnostic: "constructed"))
    replies.append(spawn)
    var syscallFailure = extensionReplyFixture()
    syscallFailure.steps[0].attempt.fresh_read = PWRunnerFreshRead(open_rc: 5, read_rc: -1, read_errno: 5,
        stat_rc: -1, stat_errno: 9, close_rc: -1, close_errno: 4)
    syscallFailure.steps[0].attempt.rc = -1
    syscallFailure.steps[0].attempt.errno = 9
    syscallFailure.steps[0].attempt.outcome = AttemptOutcome.readFailed
    replies.append(syscallFailure)
    return try replies.map { try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON($0)) as! [String: Any] }
}

func runExtensionEvidenceTests(_ tk: TestKit) {
    tk.group("issuer cleanup and physical channel erasure") {
        func withIssuer(_ body: (String, PWRunnerExtensionDeclaration) throws -> Void) throws {
            guard let fixture = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"],
                  FileManager.default.isExecutableFile(atPath: fixture + ".issuer") else {
                throw TestFailure(message: "required native issuer fixture missing; use tests/run.sh")
            }
            let target = FileManager.default.temporaryDirectory.appendingPathComponent("pw-issuer-" + UUID().uuidString)
            try Data("independent issuer target".utf8).write(to: target)
            defer { try? FileManager.default.removeItem(at: target) }
            try body(fixture + ".issuer", PWRunnerExtensionDeclaration(token_ref: "token", target: target.path))
        }
        tk.run("host erases the actual mapping and closes its owned descriptor") {
            try withIssuer { executable, declaration in
                var session: ExtensionSession? = ExtensionSession(declaration: declaration, executable: executable)
                try expectEqual(session!.record.issuance_status, "issued")
                let fd = session!.descriptor
                let base = mmap(nil, ExtensionSession.channelBytes, PROT_READ, MAP_SHARED, fd, 0)!
                try expectTrue(base != MAP_FAILED)
                defer { munmap(base, ExtensionSession.channelBytes) }
                let bytes = UnsafeRawBufferPointer(start: base, count: ExtensionSession.channelBytes)
                try expectTrue(bytes[ExtensionSession.tokenOffset...].contains { $0 != 0 })
                session!.erase()
                try expectTrue(bytes.allSatisfy { $0 == 0 }, "host's mapped bytes were not erased")
                try expectTrue(session!.record.host_buffer_erased)
                session = nil
                try expectEqual(fcntl(fd, F_GETFD), -1)
                try expectEqual(errno, EBADF)
            }
        }
        tk.run("published issuance cannot deliver after an unconfirmed host reap") {
            try withIssuer { executable, declaration in
                var independentlyReaped = false
                var independentStatus: Int32 = -1
                var calls = ChildProcessCalls()
                calls.wait = { pid, _, _ in
                    // The test observes and owns real cleanup, while refusing
                    // that observation at the host's OS-call boundary.
                    if !independentlyReaped {
                        independentlyReaped = Darwin.waitpid(pid, &independentStatus, 0) == pid
                    }
                    errno = EIO; return -1
                }
                calls.kill = { _, _ in errno = EPERM; return -1 }
                let session = ExtensionSession(declaration: declaration, executable: executable, processCalls: calls)
                try expectTrue(independentlyReaped && independentStatus == 0)
                try expectEqual(session.record.issuance_status, "issuer_wait_error")
                try expectEqual(session.record.issuer?.result_published, true)
                try expectEqual(session.record.issuer?.native_nonnull, true)
                try expectEqual(session.record.issuer?.reaped, false)
                try expectNil(session.record.issuer?.exit_code)
                try expectEqual(session.record.issuer?.wait_errors.map { $0.errno }, [EIO, EIO])
                try expectEqual(session.record.issuer?.termination_request?.errno, EPERM)
                try expectNil(session.deliveryDescriptor)
                session.erase()
                try expectTrue(session.record.host_buffer_erased)
            }
        }
    }
    tk.group("extension publication and reference evidence") {
        tk.run("published abnormal issuer exit retains both observations and rejects invented claims") {
            let raw = try JSONSerialization.jsonObject(with: Data(contentsOf: repositoryRoot().appendingPathComponent(
                "tests/fixtures/blackbox_e2e/checker/response18/issuer_abnormal_run.json"))) as! [String: Any]
            let data = (raw["data"] as! [String: Any])["runner_result"]!
            let baseline = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: JSONSerialization.data(withJSONObject: data))
            _ = try pwRunnerEncodeJSON(baseline)
            let changes: [(inout PWRunnerRunResult) -> Void] = [
                { $0.extensions?[0].issuer?.exit_code = 0 },
                { $0.extensions?[0].issuer?.result_published = false },
                { $0.extensions?[0].issuer?.reaped = false },
                { $0.extensions?[0].issuer?.token_length = 0 },
            ]
            for change in changes {
                var reply = baseline; change(&reply)
                var refused = false
                do { _ = try pwRunnerEncodeJSON(reply) } catch { refused = true }
                try expectTrue(refused)
            }
        }
        tk.run("native int64 handles and all-action disposition round trip") {
            let source = extensionReplyFixture()
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(source))
            try expectEqual(decoded.extension_events?[0].native_result, Int64.max)
            try expectEqual(decoded.runner_subprocess?.disposition?.steps.map { $0.step_id }, ["consume", "read", "release"])
            try expectEqual(decoded.steps[0].attempt.fresh_read?.content_hex, "5057")
        }
        tk.run("unpublished call boundary preserves an unresolved native result") {
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(extensionReplyFixture(published: false)))
            try expectEqual(decoded.extension_events?[0].call_boundary_observed, true)
            try expectEqual(decoded.extension_events?[0].status, "unresolved")
            try expectNil(decoded.extension_events?[0].native_result)
        }
        tk.run("unavailable dependent release does not invent a native call") {
            let decoded = try pwRunnerDecodeJSON(PWRunnerRunResult.self, from: pwRunnerEncodeJSON(extensionReplyFixture(available: false)))
            try expectEqual(decoded.extension_events?[1].unavailable_reason, "handle_unavailable")
            try expectEqual(decoded.extension_events?[1].call_boundary_observed, false)
        }
        tk.run("encoder rejects invented publication and mismatched references") {
            let changes: [(inout PWRunnerRunResult) -> Void] = [
                { $0.extension_events?[0].call_boundary_observed = false },
                { $0.extension_events?[0].handle_ref = "token" },
                { $0.extension_events?[0].errno = -1 },
                { $0.extension_events?[0].result_published = false },
                { $0.extension_events?[0].native_result = -1 },
                { $0.extension_events?[1].handle_ref = "other" },
                { $0.extension_events?[1].native_result = Int64.max },
                { $0.extension_events?[1].phase_id = "other" },
                { $0.extensions?[0].delivered_bytes = 16384 },
                { $0.extensions?[0].issuer?.reaped = false },
                { $0.extension_events?.reverse() },
            ]
            for change in changes {
                var reply = extensionReplyFixture(); change(&reply)
                var refused = false
                do { _ = try pwRunnerEncodeJSON(reply) } catch { refused = true }
                try expectTrue(refused, "encoder accepted unsupported native lifecycle evidence")
            }
        }
        tk.run("fresh syscall payloads cannot invent bytes or follow an unsuccessful open") {
            let changes: [(inout PWRunnerAttemptResult) -> Void] = [
                { $0.fresh_read = nil },
                { $0.fresh_read?.open_rc = -1 },
                { $0.fresh_read?.read_rc = 65 },
                { $0.fresh_read?.read_rc = -1 },
                { $0.fresh_read?.identity = nil },
                { $0.fresh_read?.content_hex = "ff" },
                { $0.fresh_read?.close_rc = nil },
                { $0.fresh_read?.open_errno = 13 },
                { $0.result_source = "synthetic" },
            ]
            for change in changes {
                var reply = extensionReplyFixture(); change(&reply.steps[0].attempt)
                var refused = false
                do { _ = try pwRunnerEncodeJSON(reply) } catch { refused = true }
                try expectTrue(refused, "encoder accepted unsupported fresh-read observations")
            }
        }
    }
}

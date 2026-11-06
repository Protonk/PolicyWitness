import Darwin
import Foundation
@testable import PWRunnerCore

// Constructed ordinary observations preserve fresh-read and validator evidence
// independently of the removed declaration workflow.
func ordinaryReadReplyFixture(published: Bool = true) -> PWRunnerRunResult {
    let identity = PWFileIdentity(device: 1, inode: 2, mode: 33188, uid: 501, gid: 20)
    let read = PWRunnerFreshRead(open_rc: 5, read_rc: 2, stat_rc: 0, identity: identity,
                                close_rc: 0, content_hex: "5057")
    var out = CWorkerOutput(workerPid: 42, readyByteReceived: true, applied: true, applyRC: 0, applyErrno: 0,
        done: published, exitCode: 0, termSignal: nil,
        slots: [CWorkerSlotResult(freshRead: published ? read : nil, stepId: "read", rc: 0, errnoVal: 0, completed: published)],
        pollStopReason: "child_reaped", reaped: true, waitErrors: [], proceedObserved: true)
    out.collectionBasis = "after_confirmed_reap"
    let disposition = resolveDisposition(out, plan: nil)
    let probe = PWRunnerProbeStep(step_id: "read",
        sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data", filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
        attempt: PWRunnerAttempt(kind: "file", action: "read_fresh", target: "/etc/hosts"))
    let phase = constructedPhase(out, ids: ["read"])
    let ordinary = buildStepResults(probePlan: [probe], queryPlan: planValidatorQueries([probe]), workerOutput: out,
        validatorOutput: nil, ordering: phase.ordering, disposition: disposition)
    return PWRunnerRunResult(specimen_id: "constructed-ordinary-read", rc: 0, normalized_outcome: "ok", pid: 42,
        policy_format: "sbpl", sandboxed_after_apply: true, steps: ordinary,
        runner_subprocess: buildWorkerSubprocess(out, disposition: disposition), phases: [phase])
}

func ordinaryReadShapeDocuments() throws -> [[String: Any]] {
    var replies = [ordinaryReadReplyFixture(), ordinaryReadReplyFixture(published: false)]
    var failure = ordinaryReadReplyFixture()
    failure.steps[0].attempt.fresh_read = PWRunnerFreshRead(open_rc: 5, read_rc: -1, read_errno: 5,
        stat_rc: -1, stat_errno: 9, close_rc: -1, close_errno: 4)
    failure.steps[0].attempt.rc = -1; failure.steps[0].attempt.errno = 9
    failure.steps[0].attempt.outcome = AttemptOutcome.readFailed
    replies.append(failure)
    var openFailure = ordinaryReadReplyFixture()
    openFailure.steps[0].attempt.fresh_read = PWRunnerFreshRead(open_rc: -1, open_errno: 2)
    openFailure.steps[0].attempt.rc = -1
    openFailure.steps[0].attempt.errno = 2
    openFailure.steps[0].attempt.outcome = AttemptOutcome.readFailed
    openFailure.steps[0].attempt.observed_path = nil
    openFailure.steps[0].comparison?.observation = "other_failure"
    openFailure.steps[0].comparison?.observation_basis = "completed_worker_status"
    try expectNil(openFailure.steps[0].attempt.freshReadEvidenceProblem())
    replies.append(openFailure)
    return try replies.map { try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON($0)) as! [String: Any] }
}

func runExtensionEvidenceTests(_ tk: TestKit) {
    tk.group("ordinary fresh read evidence") {
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
                var reply = ordinaryReadReplyFixture(); change(&reply.steps[0].attempt)
                var refused = false
                do { _ = try pwRunnerEncodeJSON(reply) } catch { refused = true }
                try expectTrue(refused, "encoder accepted unsupported fresh-read observations")
            }
        }
    }
}

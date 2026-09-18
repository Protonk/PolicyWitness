import Darwin
import Foundation
@testable import PWRunnerCore

// Constructed interpretation controls pin the interim evidence table.
// Real driver/publication controls live separately in CWorkerLifecycleTests.
private func workerOut(
    applied: Bool = true,
    applyRC: Int32 = 0,
    applyErrno: Int32 = 0,
    done: Bool = true,
    sentSigkill: Bool = false,
    termSignal: Int32? = nil,
    exitCode: Int32? = 0,
    stop: String? = "done",
    reaped: Bool? = true,
    waitErrors: [PWRunnerWaitError]? = [],
    killRC: Int32 = 0
) -> CWorkerOutput {
    return CWorkerOutput(
        workerPid: 0,
        readyByteReceived: true,
        applied: applied,
        applyRC: applyRC,
        applyErrno: applyErrno,
        done: done,
        exitCode: exitCode,
        termSignal: termSignal,
        slots: [],
        pollStopReason: stop,
        terminationRequest: sentSigkill ? PWRunnerTerminationRequest(signal: 9, rc: killRC, errno: killRC == -1 ? EPERM : nil) : nil,
        reaped: reaped,
        waitErrors: waitErrors
    )
}

private struct ClassifyRow {
    let label: String
    let worker: CWorkerRunResult
    let validator: ValidatorClientResult?
    let expectedVerdictCount: Int
    let expected: String
}

func runHostOutcomeClassifierTests(_ tk: TestKit) {
    let rows: [ClassifyRow] = [
        // ---- worker side: shape/setup/spawn failures (validator not reached) ----
        ClassifyRow(label: "worker rejects oversized plan → bad_request",
                    worker: .failure(.slotCountExceeded(999)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.badRequest),
        ClassifyRow(label: "worker posix_spawn fails → worker_spawn_failed",
                    worker: .failure(.spawnFailed("posix_spawn: 2")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.workerSpawnFailed),
        ClassifyRow(label: "worker shm setup fails → runner_failed",
                    worker: .failure(.shmSetupFailed("shm_open")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),

        // Worker publication, deadline, cleanup and disposition rows.
        ClassifyRow(label: "published legacy failure",
                    worker: .success(workerOut(applied: false, applyRC: -1)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "inconsistent done without application or failure",
                    worker: .success(workerOut(applied: false, applyRC: 0)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "inconsistent applied with failure status",
                    worker: .success(workerOut(applyRC: -1)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "inconsistent publication outranks deadline",
                    worker: .success(workerOut(applied: false, done: true, stop: "sentinel_deadline")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "published failure outranks cleanup and deadline",
                    worker: .success(workerOut(applied: false, applyRC: -1, sentSigkill: true, termSignal: 9, exitCode: nil, stop: "sentinel_deadline")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "published failure survives failed kill and reap",
                    worker: .success(workerOut(applied: false, applyRC: -1, sentSigkill: true, exitCode: nil, reaped: false, killRC: -1)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "unpublished zeros and pre-apply clean exit",
                    worker: .success(workerOut(applied: false, done: false, stop: "child_reaped")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "unpublished arbitrary storage and pre-apply nonzero exit",
                    worker: .success(workerOut(applied: false, applyRC: -83, applyErrno: 97, done: false, exitCode: 17, stop: "child_reaped")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "pre-apply signal",
                    worker: .success(workerOut(applied: false, done: false, termSignal: 9, exitCode: nil, stop: "child_reaped")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "pre-apply deadline and host termination",
                    worker: .success(workerOut(applied: false, done: false, sentSigkill: true, termSignal: 9, exitCode: nil, stop: "sentinel_deadline")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerTimeout),
        ClassifyRow(label: "pre-apply deadline survives unconfirmed disposition",
                    worker: .success(workerOut(applied: false, done: false, sentSigkill: true, exitCode: nil, stop: "sentinel_deadline", reaped: false, killRC: -1)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerTimeout),
        ClassifyRow(label: "incomplete post-apply signal has no sandbox cause",
                    worker: .success(workerOut(done: false, termSignal: 9, exitCode: nil, stop: "child_reaped")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "incomplete clean exit is not a deadline",
                    worker: .success(workerOut(done: false, stop: "child_reaped")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "deadline survives voluntary grace exit",
                    worker: .success(workerOut(done: false, stop: "sentinel_deadline")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerTimeout),
        ClassifyRow(label: "deadline survives host cleanup termination",
                    worker: .success(workerOut(done: false, sentSigkill: true, termSignal: 9, exitCode: nil, stop: "sentinel_deadline")),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerTimeout),
        ClassifyRow(label: "completed report and cleanup kill is not a deadline",
                    worker: .success(workerOut(sentSigkill: true, termSignal: 9, exitCode: nil)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "completed report and cleanup request followed by exit zero",
                    worker: .success(workerOut(sentSigkill: true)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "completed report and nonzero exit",
                    worker: .success(workerOut(exitCode: 17)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "completed report and independent signal",
                    worker: .success(workerOut(termSignal: 15, exitCode: nil)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "completed report and failed reap",
                    worker: .success(workerOut(exitCode: nil, reaped: false)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "status storage cannot override unconfirmed reap",
                    worker: .success(workerOut(exitCode: 0, reaped: false)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "unavailable host observations cannot prove completion",
                    worker: .success(workerOut(reaped: nil, waitErrors: nil)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "incomplete wait error without deadline",
                    worker: .success(workerOut(applied: false, done: false, exitCode: nil, stop: "wait_error", reaped: false)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "wait error survives later clean reap",
                    worker: .success(workerOut(waitErrors: [PWRunnerWaitError(phase: "poll", rc: -1, errno: EIO)])),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        ClassifyRow(label: "recovered EINTR does not fail a clean report",
                    worker: .success(workerOut(waitErrors: [PWRunnerWaitError(phase: "exit_grace", rc: -1, errno: EINTR)])),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.ok),

        // ---- worker clean: validator-side classification ----
        ClassifyRow(label: "worker ok, no probes sent (validator nil) → ok",
                    worker: .success(workerOut(done: true)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.ok),
        ClassifyRow(label: "validator read/write I/O fault → validator_no_reply",
                    worker: .success(workerOut(done: true)),
                    validator: .failure(error: .verdictReadFailed("read(verdicts): EIO"), partial: nil),
                    expectedVerdictCount: 0,
                    expected: NormalizedOutcome.validatorNoReply),
        ClassifyRow(label: "validator emits non-NDJSON → validator_decode_failure",
                    worker: .success(workerOut(done: true)),
                    validator: .failure(error: .verdictParseFailed(line: "garbage", why: "not json"), partial: nil),
                    expectedVerdictCount: 0,
                    expected: NormalizedOutcome.validatorDecodeFailure),
        ClassifyRow(label: "validator posix_spawn fails → validator_spawn_failed",
                    worker: .success(workerOut(done: true)),
                    validator: .failure(error: .spawnFailed("posix_spawn(sb_api_validator)"), partial: nil),
                    expectedVerdictCount: 0,
                    expected: NormalizedOutcome.validatorSpawnFailed),
        ClassifyRow(label: "validator probe serialization fails → runner_failed",
                    worker: .success(workerOut(done: true)),
                    validator: .failure(error: .probeSerializationFailed("encode"), partial: nil),
                    expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerFailed),
        // Clean exit but fewer verdicts than expected → attempts-only mode.
        ClassifyRow(label: "validator clean exit, short verdict count → validator_unavailable",
                    worker: .success(workerOut(done: true)),
                    validator: .success(ValidatorOutput(validatorPid: 0, verdicts: [])),
                    expectedVerdictCount: 1,
                    expected: NormalizedOutcome.validatorUnavailable),
        // Clean exit, verdict count meets expectation (0 of 0) → ok.
        ClassifyRow(label: "validator clean exit, full verdict count → ok",
                    worker: .success(workerOut(done: true)),
                    validator: .success(ValidatorOutput(validatorPid: 0, verdicts: [])),
                    expectedVerdictCount: 0,
                    expected: NormalizedOutcome.ok),
    ]

    tk.group("classify: worker/validator → normalized outcome") {
        for row in rows {
            tk.run(row.label) {
                let got = classify(
                    workerResult: row.worker,
                    validatorResult: row.validator,
                    expectedVerdictCount: row.expectedVerdictCount
                )
                if got.outcome != row.expected {
                    throw TestFailure(message:
                        "outcome contract for [\(row.label)]: expected "
                        + "\(row.expected), got \(got.outcome) (error: \(got.error ?? "nil"))")
                }
            }
        }
    }

    tk.group("classify: publication validity and independent diagnostics") {
        tk.run("legacy failure retains status and meaningful legacy errno without native attribution") {
            for legacyErrno: Int32 in [0, 1, 4567] {
                let got = classify(workerResult: .success(workerOut(applied: false, applyRC: -1, applyErrno: legacyErrno)),
                                   validatorResult: nil, expectedVerdictCount: 0)
                try expectEqual(got.outcome, NormalizedOutcome.runnerFailed)
                try expectContains(got.error ?? "", "status=-1")
                if legacyErrno != 0 { try expectContains(got.error ?? "", "legacy errno=\(legacyErrno)") }
                else { try expectFalse((got.error ?? "").contains("errno")) }
                try expectFalse((got.error ?? "").contains("sandbox_apply"))
                try expectFalse((got.error ?? "").contains("returned"))
            }
        }
        tk.run("unpublished storage is ignored including arbitrary nonzero values") {
            let clean = classify(workerResult: .success(workerOut(applied: false, done: false, stop: "child_reaped")),
                                 validatorResult: nil, expectedVerdictCount: 0)
            let garbage = classify(workerResult: .success(workerOut(applied: false, applyRC: -83, applyErrno: 97,
                                                                     done: false, stop: "child_reaped")),
                                   validatorResult: nil, expectedVerdictCount: 0)
            try expectEqual(garbage.outcome, clean.outcome)
            try expectEqual(garbage.error, clean.error)
        }
        tk.run("worker failure precedence retains validator failure independently") {
            let worker = workerOut(applied: false, applyRC: -1, sentSigkill: true, exitCode: nil, reaped: false)
            let validator = ValidatorClientResult.failure(error: .spawnFailed("fixture validator"), partial: nil)
            let got = classify(workerResult: .success(worker), validatorResult: validator, expectedVerdictCount: 1)
            try expectEqual(got.outcome, NormalizedOutcome.runnerFailed)
            try expectContains(got.error ?? "", "status=-1")
            try expectEqual(buildWorkerSubprocess(worker).termination_request?.rc, 0)
            try expectEqual(buildWorkerSubprocess(worker).reaped, false)
        }
    }
}

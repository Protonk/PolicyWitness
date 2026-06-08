import Foundation
@testable import PWRunnerCore

/*
 * HostOutcomeClassifierTests — the worker/validator → NormalizedOutcome
 * decision table.
 *
 * `classify(workerResult:validatorResult:expectedVerdictCount:)` is the
 * host's counterpart to computeDrift: it folds a run's shape (worker
 * setup error, apply failure, host SIGKILL, foreign signal, clean exit;
 * then validator spawn/read/parse failure or short verdict count) onto
 * the single NormalizedOutcome the controller reports. The branch
 * structure is a nested switch ladder — exactly the kind of code a
 * refactor reshuffles.
 *
 * This is a behavior test: it drives the public boundary `classify`
 * with concrete inputs and asserts the resulting outcome, never naming
 * the internal ordering. Reorganize the ladder however you like; only a
 * change in MEANING fails a row.
 *
 * It also reaches three outcomes COVERAGE.md marks e2e-unreachable —
 * validator_no_reply (not seam-reachable through _test_overrides),
 * runner_failed, and runner_sandbox_denied — because at this altitude
 * they are just input shapes, not pipeline accidents.
 */

// A clean worker run with overridable failure knobs. classify never
// reads `slots`, so an empty slot list is fine.
private func workerOut(
    applied: Bool = true,
    applyRC: Int32 = 0,
    applyErrno: Int32 = 0,
    done: Bool = true,
    sentSigkill: Bool = false,
    termSignal: Int32? = nil,
    exitCode: Int32? = 0
) -> CWorkerOutput {
    return CWorkerOutput(
        workerPid: 0,
        readyByteReceived: true,
        applied: applied,
        applyRC: applyRC,
        applyErrno: applyErrno,
        done: done,
        sentSigkill: sentSigkill,
        exitCode: exitCode,
        termSignal: termSignal,
        slots: []
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

        // ---- worker side: ran, but apply / done / signal outcomes ----
        ClassifyRow(label: "sandbox_apply failed inside worker → sandbox_apply_failed",
                    worker: .success(workerOut(applied: false, applyRC: 2)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.sandboxApplyFailed),
        // The load-bearing asymmetry, part 1: the HOST sent SIGKILL after
        // its grace timer — the worker's death is the host's doing, NOT a
        // sandbox denial. Must read as runner_timeout.
        ClassifyRow(label: "host SIGKILL after grace timer → runner_timeout (not sandbox)",
                    worker: .success(workerOut(done: false, sentSigkill: true, termSignal: 9)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerTimeout),
        // Part 2: a FOREIGN signal (host did not SIGKILL) on a worker that
        // never flipped done IS sandbox-denial evidence.
        ClassifyRow(label: "foreign signal before done → runner_sandbox_denied",
                    worker: .success(workerOut(done: false, sentSigkill: false, termSignal: 9)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerSandboxDenied),
        // No signal, just failed to flip done in time → timeout, not denial.
        ClassifyRow(label: "clean exit without done → runner_timeout",
                    worker: .success(workerOut(done: false, sentSigkill: false, termSignal: nil)),
                    validator: nil, expectedVerdictCount: 0,
                    expected: NormalizedOutcome.runnerTimeout),

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

    // The apply-failed error string must surface the worker's apply_errno
    // so a reader can tell WHY apply failed (e.g. EPERM = the unentitled
    // witness worker isn't permitted to apply the profile) rather than
    // seeing a bare rc.
    tk.group("classify: sandbox_apply_failed surfaces apply errno") {
        tk.run("non-zero errno appears in the error string") {
            let got = classify(
                workerResult: .success(workerOut(applied: false, applyRC: -1, applyErrno: 1)),
                validatorResult: nil,
                expectedVerdictCount: 0
            )
            try expectEqual(got.outcome, NormalizedOutcome.sandboxApplyFailed)
            try expectContains(got.error ?? "", "returned -1")
            try expectContains(got.error ?? "", "errno 1")
        }
        tk.run("zero errno omits the errno clause") {
            let got = classify(
                workerResult: .success(workerOut(applied: false, applyRC: 2, applyErrno: 0)),
                validatorResult: nil,
                expectedVerdictCount: 0
            )
            try expectEqual(got.outcome, NormalizedOutcome.sandboxApplyFailed)
            try expectContains(got.error ?? "", "returned 2")
            if (got.error ?? "").contains("errno") {
                throw TestFailure(message: "expected no errno clause when applyErrno==0, got: \(got.error ?? "")")
            }
        }
    }
}

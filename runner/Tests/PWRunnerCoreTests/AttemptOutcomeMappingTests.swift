import Foundation
@testable import PWRunnerCore

/*
 * AttemptOutcomeMappingTests — the (kind, action, slot) → AttemptOutcome
 * table.
 *
 * buildAttemptResult is the third host classifier (with computeDrift and
 * classify). It folds a probe step plus the worker's per-slot result
 * into an attempt outcome, and it's built from TWO stacked tables that
 * must agree:
 *
 *   Layer 1  mapAttemptKindOrNil — which (kind, action) pairs are
 *            implemented; anything else routes to PW_ATTEMPT_NONE.
 *   Layer 2  buildAttemptResult — the disposition ladder
 *            (unsupported / not_run_worker_died / ok) plus, on a
 *            completed slot with rc != 0, an action switch that names
 *            the specific *_failed outcome.
 *
 * The outcomes here are individually reachable e2e, but only one cell at
 * a time, scattered across ~6 suites. This test pins the mapping AS A
 * TABLE so a refactor that reshuffles either layer — or makes the two
 * disagree — fails a row instead of slipping through. Behavior test:
 * drives the public boundary, never the branch ordering.
 */

private func step(kind: String, action: String, target: String = "/tmp/probe") -> PWRunnerProbeStep {
    return PWRunnerProbeStep(
        step_id: "s1",
        sandbox_check: PWRunnerSandboxCheck(
            operation: "file-read-data",
            filter: PWRunnerSandboxFilter(kind: "path", value: target)
        ),
        attempt: PWRunnerAttempt(kind: kind, action: action, target: target)
    )
}

// A completed worker slot with an overridable rc. buildAttemptResult
// reads rc/errnoVal/completed/childPid; the rest is filler.
private func slot(
    rc: Int32,
    completed: Bool = true,
    errnoVal: Int32 = 0,
    childPid: Int32? = nil
) -> CWorkerSlotResult {
    return CWorkerSlotResult(
        stepId: "s1",
        rc: rc,
        errnoVal: errnoVal,
        observedPath: nil,
        error: nil,
        completed: completed,
        childPid: childPid,
        childExitCode: nil,
        childTermSignal: nil,
        childStdout: nil,
        childStderr: nil
    )
}

private let W = PWRunnerWire.self

// The eight supported (kind, action) pairs paired with the failure
// outcome buildAttemptResult must emit when the slot completed rc != 0.
// This list IS the Layer-1/Layer-2 agreement contract.
private let SUPPORTED: [(kind: String, action: String, failOutcome: String)] = [
    (W.attemptKindFile,       W.attemptActionOpenRead,   AttemptOutcome.openFailed),
    (W.attemptKindFile,       W.attemptActionOpenWrite,  AttemptOutcome.openFailed),
    (W.attemptKindFile,       W.attemptActionCreate,     AttemptOutcome.openFailed),
    (W.attemptKindFile,       W.attemptActionUnlink,     AttemptOutcome.unlinkFailed),
    (W.attemptKindFile,       W.attemptActionAccess,     AttemptOutcome.accessFailed),
    (W.attemptKindMachLookup, W.attemptActionMachLookup, AttemptOutcome.lookupFailed),
    (W.attemptKindSysctl,     W.attemptActionRead,       AttemptOutcome.sysctlFailed),
    (W.attemptKindExec,       W.attemptActionSpawn,      AttemptOutcome.execFailed),
]

func runAttemptOutcomeMappingTests(_ tk: TestKit) {
    tk.group("buildAttemptResult: (kind, action, slot) → attempt outcome") {

        // ---- the rc != 0 action switch: each supported pair → its outcome ----
        for pair in SUPPORTED {
            tk.run("\(pair.kind)/\(pair.action) rc!=0 → \(pair.failOutcome)") {
                let at = buildAttemptResult(
                    step: step(kind: pair.kind, action: pair.action),
                    slot: slot(rc: 1, errnoVal: Int32(EPERM))
                )
                if at.outcome != pair.failOutcome {
                    throw TestFailure(message:
                        "\(pair.kind)/\(pair.action): expected \(pair.failOutcome), got \(at.outcome)")
                }
            }
        }

        // ---- table-agreement guard: every pair Layer 1 accepts must map to a
        //      NON-unsupported failure outcome in Layer 2. If the two tables
        //      drift apart (a new action routed but not switched, or vice
        //      versa), this row catches it. ----
        tk.run("every Layer-1-supported pair yields a non-unsupported failure outcome") {
            for pair in SUPPORTED {
                let attempt = PWRunnerAttempt(kind: pair.kind, action: pair.action, target: "/tmp/probe")
                if mapAttemptKindOrNil(attempt) == nil {
                    throw TestFailure(message:
                        "Layer 1 unexpectedly rejects supported pair \(pair.kind)/\(pair.action)")
                }
                let at = buildAttemptResult(
                    step: step(kind: pair.kind, action: pair.action),
                    slot: slot(rc: 1, errnoVal: Int32(EPERM))
                )
                if at.outcome == AttemptOutcome.unsupported {
                    throw TestFailure(message:
                        "Layer 2 emits 'unsupported' for a Layer-1-supported pair "
                        + "\(pair.kind)/\(pair.action) — the two tables disagree")
                }
            }
        }

        // ---- rc == 0 on a completed slot → ok ----
        tk.run("supported pair, slot completed rc==0 → ok") {
            let at = buildAttemptResult(
                step: step(kind: W.attemptKindFile, action: W.attemptActionOpenRead),
                slot: slot(rc: 0)
            )
            if at.outcome != AttemptOutcome.ok {
                throw TestFailure(message: "expected ok, got \(at.outcome)")
            }
        }

        // ---- slot missing → not_run_worker_died (worker never reached it) ----
        tk.run("supported pair, slot missing → not_run_worker_died") {
            let at = buildAttemptResult(
                step: step(kind: W.attemptKindFile, action: W.attemptActionOpenRead),
                slot: nil
            )
            if at.outcome != AttemptOutcome.notRunWorkerDied {
                throw TestFailure(message: "expected not_run_worker_died, got \(at.outcome)")
            }
        }

        // ---- slot present but not completed → not_run_worker_died ----
        // Distinct from "missing": the worker reached the slot but exited
        // before finishing it.
        tk.run("supported pair, slot present but !completed → not_run_worker_died") {
            let at = buildAttemptResult(
                step: step(kind: W.attemptKindFile, action: W.attemptActionOpenRead),
                slot: slot(rc: 0, completed: false)
            )
            if at.outcome != AttemptOutcome.notRunWorkerDied {
                throw TestFailure(message: "expected not_run_worker_died, got \(at.outcome)")
            }
        }

        // ---- unsupported (kind, action) combos → unsupported, BEFORE the
        //      slot is even consulted (a completed rc==0 slot must not
        //      masquerade as ok). ----
        let unsupportedCombos: [(String, String)] = [
            (W.attemptKindFile, W.attemptActionSpawn),       // right kind, wrong action
            (W.attemptKindMachLookup, W.attemptActionOpenRead),
            (W.attemptKindSysctl, W.attemptActionSpawn),
            ("totally-bogus", "nonsense"),
        ]
        for (kind, action) in unsupportedCombos {
            tk.run("unsupported combo \(kind)/\(action) → unsupported (slot ignored)") {
                // Pass a completed rc==0 slot: if the unsupported check were
                // ordered after the rc==0 branch, this would wrongly be ok.
                let at = buildAttemptResult(
                    step: step(kind: kind, action: action),
                    slot: slot(rc: 0)
                )
                if at.outcome != AttemptOutcome.unsupported {
                    throw TestFailure(message:
                        "expected unsupported for \(kind)/\(action), got \(at.outcome)")
                }
            }
        }

        // ---- exec child_pid passthrough: the drift classifier downstream
        //      keys on it, so buildAttemptResult must carry it through. ----
        tk.run("exec rc!=0 preserves child_pid for downstream drift attribution") {
            let at = buildAttemptResult(
                step: step(kind: W.attemptKindExec, action: W.attemptActionSpawn, target: "/usr/bin/true"),
                slot: slot(rc: 1, errnoVal: Int32(EPERM), childPid: 0)
            )
            if at.outcome != AttemptOutcome.execFailed {
                throw TestFailure(message: "expected exec_failed, got \(at.outcome)")
            }
            if at.child_pid != 0 {
                throw TestFailure(message: "expected child_pid=0 preserved, got \(String(describing: at.child_pid))")
            }
        }
    }
}

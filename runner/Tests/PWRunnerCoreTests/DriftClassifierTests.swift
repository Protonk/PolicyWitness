import Foundation
@testable import PWRunnerCore

/*
 * DriftClassifierTests — the validator-vs-kernel drift truth table.
 *
 * `computeDrift(sandboxCheck:attempt:)` is the reason PolicyWitness
 * exists: it decides, for each step, whether the userland
 * sandbox_check prediction disagrees with what the kernel actually
 * did. The answer is a tri-state — true (libsandbox drift), false
 * (agreement), or nil (no attributable verdict) — and the rules are
 * deliberately ASYMMETRIC (an ambiguous file EPERM means different
 * things under a predicted allow vs a predicted deny).
 *
 * This is a behavior test, not a structure test. It drives the public
 * boundary `computeDrift` with concrete (PWRunnerSandboxCheckResult,
 * PWRunnerAttemptResult) pairs and asserts the resulting Bool?. It
 * never names the private helpers behind it (observationFromAttempt,
 * the AttemptObservation enum), so the classifier can be re-split,
 * renamed, or relocated freely — only a change in MEANING fails a row,
 * and the row's label says which invariant broke.
 *
 * Each row exercises both the 6-cell (predicted × observation) truth
 * table AND the observation classifier that maps an attempt's
 * outcome/errno/child_pid/error into one of {allowed, strongEvidence,
 * ambiguous, undefined}.
 */

// A sandbox_check result carrying only the field the classifier reads
// (outcome); the rest are plausible filler.
private func check(_ outcome: String) -> PWRunnerSandboxCheckResult {
    return PWRunnerSandboxCheckResult(
        rc: outcome == SandboxCheckOutcome.allow ? 0 : 1,
        outcome: outcome,
        pid: 0,
        operation: "file-read-data",
        scope: "",
        filter_kind: "path",
        filter_value: "/etc/hosts"
    )
}

// An attempt result. Only outcome/errno/child_pid/error feed the
// classifier; rc is filler (nonzero for any failure shape).
private func attempt(
    _ outcome: String,
    errno: Int? = nil,
    child_pid: Int? = nil,
    error: String? = nil
) -> PWRunnerAttemptResult {
    return PWRunnerAttemptResult(
        rc: outcome == AttemptOutcome.ok ? 0 : 1,
        errno: errno,
        outcome: outcome,
        error: error,
        child_pid: child_pid
    )
}

private func fmtDrift(_ value: Bool?) -> String {
    switch value {
    case .some(true): return "true (drift)"
    case .some(false): return "false (agreement)"
    case .none: return "nil (no verdict)"
    }
}

private struct DriftRow {
    let label: String
    let predicted: String
    let attempt: PWRunnerAttemptResult
    let expected: Bool?
}

func runDriftClassifierTests(_ tk: TestKit) {
    // errno constants the classifier branches on, named for clarity.
    let eperm = Int(EPERM)     // 1  — sandbox deny OR Unix DAC (ambiguous on files)
    let eacces = Int(EACCES)   // 13 — same ambiguity
    let enoent = Int(ENOENT)   // 2  — target missing; never a sandbox verdict
    let einval = Int(EINVAL)   // 22 — a sysctl errno with no non-policy analogue here

    let rows: [DriftRow] = [
        // ---- happy path: prediction and observation agree on allow ----
        DriftRow(label: "allow predicted + attempt ok",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.ok),
                 expected: false),
        // ---- deny predicted but the op went through → libsandbox drift ----
        DriftRow(label: "deny predicted + attempt ok",
                 predicted: SandboxCheckOutcome.deny,
                 attempt: attempt(AttemptOutcome.ok),
                 expected: true),

        // ---- mach kr=1100 is UNAMBIGUOUS strong sandbox evidence ----
        DriftRow(label: "allow predicted + mach kr=1100 (strong deny)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.lookupFailed,
                                  error: "bootstrap_look_up: kr=1100"),
                 expected: true),   // libsandbox drift
        DriftRow(label: "deny predicted + mach kr=1100 (strong deny)",
                 predicted: SandboxCheckOutcome.deny,
                 attempt: attempt(AttemptOutcome.lookupFailed,
                                  error: "bootstrap_look_up: kr=1100"),
                 expected: false),  // directional agreement
        // ---- mach kr=1102 is "service not registered" — NOT a verdict ----
        DriftRow(label: "allow predicted + mach kr=1102 (unknown service)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.lookupFailed,
                                  error: "bootstrap_look_up: kr=1102"),
                 expected: nil),
        DriftRow(label: "deny predicted + mach kr=1102 (unknown service)",
                 predicted: SandboxCheckOutcome.deny,
                 attempt: attempt(AttemptOutcome.lookupFailed,
                                  error: "bootstrap_look_up: kr=1102"),
                 expected: nil),    // no evidence to confirm the deny

        // ---- file EPERM/EACCES is AMBIGUOUS (sandbox OR Unix DAC) ----
        // The asymmetry: allow+ambiguous must be nil (don't blame
        // libsandbox for what could be a chmod), deny+ambiguous is
        // false (directional agreement, accepted small risk).
        DriftRow(label: "allow predicted + file open EPERM (ambiguous)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.openFailed, errno: eperm),
                 expected: nil),
        DriftRow(label: "deny predicted + file open EPERM (ambiguous)",
                 predicted: SandboxCheckOutcome.deny,
                 attempt: attempt(AttemptOutcome.openFailed, errno: eperm),
                 expected: false),
        DriftRow(label: "allow predicted + access() EACCES (ambiguous)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.accessFailed, errno: eacces),
                 expected: nil),
        DriftRow(label: "deny predicted + unlink EACCES (ambiguous)",
                 predicted: SandboxCheckOutcome.deny,
                 attempt: attempt(AttemptOutcome.unlinkFailed, errno: eacces),
                 expected: false),
        // ---- file ENOENT is the file missing — NOT a sandbox verdict ----
        DriftRow(label: "allow predicted + file open ENOENT (missing, not deny)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.openFailed, errno: enoent),
                 expected: nil),

        // ---- exec drift keys on child_pid, not just errno ----
        // child_pid == 0 + EPERM → spawn denied (strong, no DAC analogue).
        DriftRow(label: "allow predicted + exec spawn-denied (child_pid=0, EPERM)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.execFailed, errno: eperm, child_pid: 0),
                 expected: true),
        DriftRow(label: "deny predicted + exec spawn-denied (child_pid=0, EPERM)",
                 predicted: SandboxCheckOutcome.deny,
                 attempt: attempt(AttemptOutcome.execFailed, errno: eperm, child_pid: 0),
                 expected: false),
        // child_pid > 0 → spawn SUCCEEDED; the helper merely exited
        // nonzero. Not a sandbox verdict no matter the errno.
        DriftRow(label: "allow predicted + exec child ran then exited nonzero (child_pid>0)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.execFailed, errno: eperm, child_pid: 4242),
                 expected: nil),

        // ---- sysctl: EPERM/EACCES ambiguous, ENOENT/ENOMEM undefined,
        //      any other errno is strong (no non-policy analogue here) ----
        DriftRow(label: "allow predicted + sysctl EPERM (ambiguous)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.sysctlFailed, errno: eperm),
                 expected: nil),
        DriftRow(label: "allow predicted + sysctl ENOENT (undefined)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.sysctlFailed, errno: enoent),
                 expected: nil),
        DriftRow(label: "allow predicted + sysctl EINVAL (strong)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.sysctlFailed, errno: einval),
                 expected: true),

        // ---- setup/shape failures: the gated syscall never ran ----
        DriftRow(label: "allow predicted + worker died before slot (not_run_worker_died)",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.notRunWorkerDied),
                 expected: nil),
        DriftRow(label: "allow predicted + unsupported attempt kind",
                 predicted: SandboxCheckOutcome.allow,
                 attempt: attempt(AttemptOutcome.unsupported),
                 expected: nil),

        // ---- a non-allow/deny prediction never yields a verdict ----
        DriftRow(label: "prediction_unavailable + attempt ok",
                 predicted: SandboxCheckOutcome.predictionUnavailable,
                 attempt: attempt(AttemptOutcome.ok),
                 expected: nil),
    ]

    tk.group("computeDrift: validator-vs-kernel truth table") {
        for row in rows {
            tk.run(row.label) {
                let got = computeDrift(
                    sandboxCheck: check(row.predicted),
                    attempt: row.attempt
                )
                if got != row.expected {
                    throw TestFailure(message:
                        "drift contract for [\(row.label)]: expected "
                        + "\(fmtDrift(row.expected)), got \(fmtDrift(got))")
                }
            }
        }
    }
}

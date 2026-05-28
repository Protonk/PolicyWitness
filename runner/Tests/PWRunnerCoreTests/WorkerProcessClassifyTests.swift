import Foundation
import Darwin
@testable import PWRunnerCore

// classifyWorkerResult is the host-side function that turns "what waitpid
// observed and what bytes (if any) the worker wrote" into a normalized_outcome
// string. The end-to-end suites cover the main paths (ok, runner_timeout,
// runner_sandbox_denied, worker_spawn_failed); this table walks the precedence
// rules and the edge cases that aren't reachable from a real specimen.

private func sub(pid: Int = 4242, term: Int? = nil, exit: Int? = nil, partial: Bool = false) -> PWRunnerSubprocess {
    PWRunnerSubprocess(pid: pid, term_signal: term, exit_code: exit, partial_steps: partial)
}

private func okReport(pid: Int = 4242) -> PWRunnerWorkerReport {
    PWRunnerWorkerReport(
        worker_pid: pid,
        rc: 0,
        normalized_outcome: "ok",
        error: nil,
        policy_sha256: "deadbeef",
        sandboxed_after_apply: true,
        deny_signal_total: nil,
        steps: [],
        instrumentation: nil
    )
}

func runWorkerClassifyTests(_ tk: TestKit) {
    tk.group("WorkerProcess.classifyWorkerResult") {

        tk.run("timedOut beats everything including a present report and a signal") {
            // Even if the worker also somehow produced a report and got a
            // signal, timedOut wins because the host SIGKILLed an
            // unresponsive worker and any report would be from a torn-down
            // code path.
            let result = classifyWorkerResult(
                report: okReport(),
                subprocess: sub(term: Int(SIGKILL)),
                timedOut: true,
                transportError: "timed out reading frame",
                waitError: nil
            )
            try expectEqual(result.outcome, "runner_timeout")
            try expectEqual(result.rc, 1)
            try expectEqual(result.error, "timed out reading frame")
        }

        tk.run("report present beats signal observed after worker wrote it") {
            // The worker survived long enough to write a complete report;
            // the signal observed after the write is a teardown artifact,
            // not a probe failure.
            let result = classifyWorkerResult(
                report: okReport(),
                subprocess: sub(term: Int(SIGKILL)),
                timedOut: false,
                transportError: nil,
                waitError: nil
            )
            try expectEqual(result.outcome, "ok")
            try expectEqual(result.rc, 0)
        }

        tk.run("no report + SIGKILL surfaces as runner_sandbox_denied") {
            let result = classifyWorkerResult(
                report: nil,
                subprocess: sub(term: Int(SIGKILL)),
                timedOut: false,
                transportError: "worker exited without writing a report",
                waitError: nil
            )
            try expectEqual(result.outcome, "runner_sandbox_denied")
            try expectEqual(result.rc, 1)
            try expectEqual(result.error, "worker exited without writing a report")
        }

        tk.run("no report + SIGTRAP surfaces as runner_sandbox_denied") {
            // The bug-report Swift-runtime trap: under (deny default) a
            // denied mach_vm_allocate makes libSwift's protocol-conformance
            // cache trap with EXC_BREAKPOINT/SIGTRAP. Same root cause as
            // SIGKILL — classify the same way.
            let result = classifyWorkerResult(
                report: nil,
                subprocess: sub(term: Int(SIGTRAP)),
                timedOut: false,
                transportError: nil,
                waitError: nil
            )
            try expectEqual(result.outcome, "runner_sandbox_denied")
        }

        tk.run("no report + SIGABRT surfaces as runner_sandbox_denied") {
            // SIGABRT can surface from libSwift assertion failures under
            // very restrictive sandboxes; treat it the same way.
            let result = classifyWorkerResult(
                report: nil,
                subprocess: sub(term: Int(SIGABRT)),
                timedOut: false,
                transportError: nil,
                waitError: nil
            )
            try expectEqual(result.outcome, "runner_sandbox_denied")
        }

        tk.run("no report + non-zero exit without signal surfaces as runner_failed") {
            let result = classifyWorkerResult(
                report: nil,
                subprocess: sub(exit: 2),
                timedOut: false,
                transportError: nil,
                waitError: nil
            )
            try expectEqual(result.outcome, "runner_failed")
            try expectEqual(result.rc, 1)
            try expectNotNil(result.error)
        }

        tk.run("no report + clean exit without signal surfaces as runner_failed") {
            // Worker exited 0 but produced no readable frame — the host
            // can't distinguish this from a stripped reply, so it's a
            // structural failure rather than ok.
            let result = classifyWorkerResult(
                report: nil,
                subprocess: sub(exit: 0),
                timedOut: false,
                transportError: nil,
                waitError: nil
            )
            try expectEqual(result.outcome, "runner_failed")
            try expectEqual(result.rc, 1)
        }

        tk.run("timeout falls back to waitError when no transport error is available") {
            let result = classifyWorkerResult(
                report: nil,
                subprocess: sub(term: Int(SIGKILL)),
                timedOut: true,
                transportError: nil,
                waitError: "waitpid stalled"
            )
            try expectEqual(result.outcome, "runner_timeout")
            try expectEqual(result.error, "waitpid stalled")
        }
    }
}

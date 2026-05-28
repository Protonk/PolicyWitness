import Foundation
import Darwin
@testable import PWRunnerCore

// Small pure helpers inside WorkerProcess. They back outcome decisions, so a
// wrong branch here would quietly produce the wrong normalized_outcome
// downstream rather than fail loudly.

func runWorkerHelperTests(_ tk: TestKit) {
    tk.group("WorkerProcess.effectiveWorkerTimeoutSeconds") {

        tk.run("defaults to 90 seconds when override is nil") {
            try expectClose(effectiveWorkerTimeoutSeconds(override: nil), 90, accuracy: 1e-9)
        }

        tk.run("ignores non-positive override and uses default") {
            try expectClose(effectiveWorkerTimeoutSeconds(override: 0), 90, accuracy: 1e-9)
            try expectClose(effectiveWorkerTimeoutSeconds(override: -10), 90, accuracy: 1e-9)
        }

        tk.run("honors positive override in milliseconds") {
            try expectClose(effectiveWorkerTimeoutSeconds(override: 5_000), 5.0, accuracy: 1e-9)
            try expectClose(effectiveWorkerTimeoutSeconds(override: 100), 0.1, accuracy: 1e-6)
        }

        tk.run("floors values below 50ms to 50ms") {
            // The floor exists because anything tighter races posix_spawn
            // plus the first worker syscall on a modern Mac, producing
            // non-deterministic outcomes that look like sandbox kills
            // rather than timeouts.
            try expectClose(effectiveWorkerTimeoutSeconds(override: 25), 0.05, accuracy: 1e-9)
            try expectClose(effectiveWorkerTimeoutSeconds(override: 1), 0.05, accuracy: 1e-9)
        }
    }

    tk.group("WorkerProcess.sanitizedSpecimenLabel") {

        tk.run("nil and empty input produce nil") {
            try expectNil(sanitizedSpecimenLabel(nil))
            try expectNil(sanitizedSpecimenLabel(""))
        }

        tk.run("safe characters pass through unchanged") {
            try expectEqual(sanitizedSpecimenLabel("file_read_deny"), "file_read_deny")
            try expectEqual(sanitizedSpecimenLabel("BBX-001"), "BBX-001")
            try expectEqual(sanitizedSpecimenLabel("v2.foo:bar"), "v2.foo:bar")
        }

        tk.run("unsafe characters are stripped") {
            // Spaces, shell metacharacters, control chars — all gone. The
            // remaining characters survive in order so pgrep output stays
            // human-readable.
            try expectEqual(sanitizedSpecimenLabel("hi there"), "hithere")
            try expectEqual(sanitizedSpecimenLabel("$(rm -rf /)"), "rm-rf")
            try expectEqual(sanitizedSpecimenLabel("a/b\\c"), "abc")
        }

        tk.run("input is capped at 64 characters before filtering") {
            let long = String(repeating: "a", count: 100)
            try expectEqual(sanitizedSpecimenLabel(long)?.count, 64)
        }

        tk.run("input that filters to nothing yields nil") {
            try expectNil(sanitizedSpecimenLabel("///"))
            try expectNil(sanitizedSpecimenLabel("    "))
        }
    }

    tk.group("WorkerProcess.partialStepOutput") {

        tk.run("reports partial only when worker produced some but not all steps") {
            try expectFalse(partialStepOutput(0, expectedStepCount: 0), "no probe plan, no steps")
            try expectFalse(partialStepOutput(0, expectedStepCount: 5), "worker never produced a step")
            try expectTrue(partialStepOutput(3, expectedStepCount: 5), "worker stopped mid-plan")
            try expectFalse(partialStepOutput(5, expectedStepCount: 5), "complete plan is not partial")
            try expectFalse(partialStepOutput(5, expectedStepCount: 0), "defensive: more than expected")
        }
    }

    // BSD wait-status encoding:
    //   low 7 bits == 0       -> WIFEXITED, exit code in next 8 bits
    //   low 7 bits in [1,126] -> WIFSIGNALED with that signal
    //   low 7 bits == 0x7f    -> WIFSTOPPED (worker is never SIGSTOPped)
    tk.group("WorkerProcess.waitExitCode / waitTermSignal") {

        tk.run("waitExitCode decodes clean exits") {
            try expectEqual(waitExitCode(0x0000), 0)
            try expectEqual(waitExitCode(0x0100), 1)
            try expectEqual(waitExitCode(0xff00), 255)
        }

        tk.run("waitExitCode is nil when terminated by signal") {
            try expectNil(waitExitCode(Int32(SIGKILL)))
            try expectNil(waitExitCode(Int32(SIGTRAP)))
        }

        tk.run("waitTermSignal decodes signaled exits") {
            try expectEqual(waitTermSignal(Int32(SIGKILL)), Int(SIGKILL))
            try expectEqual(waitTermSignal(Int32(SIGTRAP)), Int(SIGTRAP))
            try expectEqual(waitTermSignal(Int32(SIGABRT)), Int(SIGABRT))
        }

        tk.run("waitTermSignal is nil for clean exits") {
            try expectNil(waitTermSignal(0x0000))
            try expectNil(waitTermSignal(0x0100))
        }

        tk.run("waitTermSignal ignores the WIFSTOPPED sentinel") {
            // 0x7f means WIFSTOPPED. The worker shouldn't ever be in this
            // state (we never SIGSTOP it), but the helper must not misread
            // it as a terminating signal.
            try expectNil(waitTermSignal(0x007f))
        }
    }
}

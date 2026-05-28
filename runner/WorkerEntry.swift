import Foundation
import Darwin

private func failureWorkerReport(
    normalizedOutcome: String,
    error: String,
    policySHA256: String? = nil,
    instrumentation: PWRunnerInstrumentationReport? = nil
) -> PWRunnerWorkerReport {
    PWRunnerWorkerReport(
        worker_pid: Int(getpid()),
        rc: 1,
        normalized_outcome: normalizedOutcome,
        error: error,
        policy_sha256: policySHA256,
        sandboxed_after_apply: nil,
        deny_signal_total: nil,
        steps: [],
        instrumentation: instrumentation
    )
}

func runWorkerBody(_ parsed: PWRunnerRunSpec) -> PWRunnerWorkerReport {
    installDenySignalHandler()

    var instrumentationState = InstrumentationState(spec: parsed.instrumentation)
    instrumentationState?.runPhase(PWRunnerWire.instrumentationPhasePre)

    let sandboxLib: SandboxLib
    switch SandboxLib.load() {
    case .success(let lib):
        sandboxLib = lib
    case .failure(let err):
        return failureWorkerReport(
            normalizedOutcome: "libsandbox_unavailable",
            error: err.description,
            instrumentation: instrumentationState?.finalize(reason: "worker exited before sandbox setup")
        )
    }

    let policyHash: String
    do {
        policyHash = try computePolicyHash(parsed.policy)
    } catch {
        return failureWorkerReport(
            normalizedOutcome: "bad_policy",
            error: "\(error)",
            instrumentation: instrumentationState?.finalize(reason: "worker exited before sandbox apply")
        )
    }

    // Warm path-resolution caches before the sandbox locks down file reads.
    warmFirmlinkMap()

    let applyResult = applySandboxPolicy(parsed.policy, sandboxLib: sandboxLib)
    if case .failure(let err) = applyResult {
        return failureWorkerReport(
            normalizedOutcome: "sandbox_apply_failed",
            error: err.description,
            policySHA256: policyHash,
            instrumentation: instrumentationState?.finalize(reason: "worker exited before sandbox apply")
        )
    }

    instrumentationState?.runPhase(PWRunnerWire.instrumentationPhasePost)

    let sandboxedAfterApply: Bool? = currentProcessIsSandboxed()

    var stepResults: [PWRunnerStepResult] = []
    for step in parsed.probe_plan {
        let beforeSig = denySignalCount()
        let sb = runSandboxCheck(step.sandbox_check)
        let attempt = runAttempt(step.attempt)
        let afterSig = denySignalCount()
        let sig = PWRunnerSignalResult(signal: "SIGUSR1", count_before: beforeSig, count_after: afterSig)
        stepResults.append(
            PWRunnerStepResult(
                step_id: step.step_id,
                sandbox_check: sb,
                attempt: attempt,
                deny_signal: sig
            )
        )
    }

    let totalSig = PWRunnerSignalResult(signal: "SIGUSR1", count_before: 0, count_after: denySignalCount())
    return PWRunnerWorkerReport(
        worker_pid: Int(getpid()),
        rc: 0,
        normalized_outcome: "ok",
        error: nil,
        policy_sha256: policyHash,
        sandboxed_after_apply: sandboxedAfterApply,
        deny_signal_total: totalSig,
        steps: stepResults,
        instrumentation: instrumentationState?.finalize(reason: nil)
    )
}

func runApplyAndProbeWorker(requestFD: Int32 = pwRunnerWorkerRequestFD) -> Never {
    let exitCode: Int32
    do {
        let requestData = try readWorkerFrame(fd: requestFD)
        let parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: requestData)
        let report = runWorkerBody(parsed)
        let responseData = try pwRunnerEncodeJSON(report)
        try writeWorkerFrame(fd: requestFD, data: responseData)
        exitCode = 0
    } catch {
        let report = failureWorkerReport(
            normalizedOutcome: "runner_failed",
            error: "worker failed before completing report: \(error)"
        )
        if let responseData = try? pwRunnerEncodeJSON(report) {
            try? writeWorkerFrame(fd: requestFD, data: responseData)
        }
        exitCode = 1
    }
    close(requestFD)
    exit(exitCode)
}

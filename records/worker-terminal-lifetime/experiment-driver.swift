import Darwin
import Foundation
@testable import PWRunnerCore

func require(_ value: Bool, _ message: String) {
    if !value { fatalError(message) }
}

let fixture = CommandLine.arguments[1]
let variant = CommandLine.arguments[2]
let directory = CommandLine.arguments[3]

for negative in [false, true] {
    let mode = negative ? "lost_ownership" : "publication_before_reap"
    let gate = directory + "/" + variant + "-" + mode + ".gate"
    require(!FileManager.default.fileExists(atPath: gate), "gate must be fresh")
    var hookFinished = false, postHookChecked = false, faultInjected = false
    var gatedWait = false, watchdogExpired = false
    var knownPID: pid_t = 0
    var calls = ChildProcessCalls()
    calls.wait = { pid, status, options in
        knownPID = pid
        if !hookFinished { return Darwin.waitpid(pid, status, options) }
        if !postHookChecked {
            postHookChecked = true
            return Darwin.waitpid(pid, status, options)
        }
        if negative && !faultInjected {
            faultInjected = true
            errno = EIO
            return -1
        }
        gatedWait = true
        require(FileManager.default.createFile(atPath: gate, contents: Data()), "gate creation failed")
        let deadline = DispatchTime.now().uptimeNanoseconds + 2_000_000_000
        repeat {
            let rc = Darwin.waitpid(pid, status, WNOHANG)
            if rc == pid || (rc < 0 && errno != EINTR) { return rc }
            usleep(1000)
        } while DispatchTime.now().uptimeNanoseconds < deadline
        watchdogExpired = true
        errno = ETIMEDOUT
        return -1
    }
    let result = runCWorker(CWorkerInput(workerExecutablePath: fixture, policy: gate,
        slots: [CWorkerSlotInput(stepId: "s", attemptKind: .fileOpenRead, target: "/etc/hosts")],
        sentinelTimeoutMs: 1_000, exitGraceMs: 100), processCalls: calls,
        postApplied: { _ in hookFinished = true })
    // Independent cleanup uses native waits, never the fault-controlled calls.
    var status: Int32 = 0
    var cleanupRC: pid_t = knownPID > 0 ? Darwin.waitpid(knownPID, &status, WNOHANG) : -1
    let cleanupErrno: Int32? = cleanupRC == -1 ? errno : nil
    if cleanupRC == 0 {
        _ = Darwin.kill(knownPID, SIGKILL)
        let deadline = DispatchTime.now().uptimeNanoseconds + 2_000_000_000
        repeat {
            cleanupRC = Darwin.waitpid(knownPID, &status, WNOHANG)
            if cleanupRC == knownPID || (cleanupRC == -1 && errno == ECHILD) { break }
            usleep(1000)
        } while DispatchTime.now().uptimeNanoseconds < deadline
    }
    guard case .success(let out) = result else { fatalError("driver setup failed: \(result)") }
    let query = PWRunnerProbeStep(step_id: "s", sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
        filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
        attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts"))
    let verdict = ValidatorVerdict(stepId: "s", operation: "file-read-data", filterType: "PATH", filterTypeId: 1,
        filterValue: "/etc/hosts", rc: 0, errnoVal: 0, outcome: "allow", rawLine: "constructed investigation control")
    let validator = ValidatorOutput(validatorPid: 7, verdicts: [verdict], reaped: true)
    let ordering = buildOrdering(out, validatorOutput: validator, hasQueries: true)
    let steps = buildStepResults(probePlan: [query], queryPlan: planValidatorQueries([query]), workerOutput: out,
        validatorOutput: validator, ordering: ordering)
    var subprocess = buildWorkerSubprocess(out)
    subprocess.disposition = resolveDisposition(out, plan: [query])
    let classification = classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0)
    var row: [String: Any] = ["variant": variant, "mode": mode,
        "fixture_applies_sandbox": false, "validator_record_is_constructed": true,
        "gated_wait": gatedWait, "watchdog_expired": watchdogExpired,
        "fault_injected": faultInjected, "independent_wait_rc": cleanupRC,
        "runner_subprocess": try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(subprocess)),
        "ordering": try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(ordering)),
        "comparison_order": steps[0].comparison!.order,
        "normalized_outcome_without_validator": classification.outcome]
    if let cleanupErrno { row["independent_wait_errno"] = cleanupErrno }
    let bytes = try JSONSerialization.data(withJSONObject: row, options: [.sortedKeys])
    FileHandle.standardOutput.write(bytes + Data("\n".utf8))
    require(hookFinished && postHookChecked && gatedWait && !watchdogExpired, "race gate not observed")
    require(out.done && out.applied && out.proceedObserved && out.slots[0].completed, "publication lost")
    require(out.reaped == true && out.exitCode == 0 && out.termSignal == nil && out.terminationRequest == nil, "clean reap missing")
    require(out.collectionBasis == "after_confirmed_reap", "snapshot basis lost")
    require(out.pollStopReason == (negative ? "wait_error" : "child_reaped"), "stop rewritten")
    let expectedOwnership = variant == "candidate" && !negative
    require(out.proceedOwnershipEstablished == expectedOwnership, "unexpected lifetime credit")
    require(steps[0].comparison?.order == (expectedOwnership ? "query_first" : "unestablished"), "unexpected order")
    require(classification.outcome == (negative ? "runner_failed" : "ok"), "classification changed")
    require(cleanupRC == -1 && cleanupErrno == ECHILD, "driver failed to reap owned child")
}

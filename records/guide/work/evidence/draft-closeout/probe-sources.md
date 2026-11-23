# Two disposable diagnostics used for draft 0

These source snapshots identify where the two prototypes stopped or paused. Both used the runner core from the source reviewed through `2bc70a43`. The unmodified signed app in `dist/` supplied the execution comparisons. Neither prototype was built into that app.

## Admission

A copy of the app kept its controller and replaced its client executable with an adapter. The adapter captured the held request from stdin. It invoked the diagnostic below under `sandbox-exec` with `(version 1)(allow default)(deny process-fork)`. A shell under the same policy failed to fork a child. The diagnostic's stdout went to a separate observation file. The comparison used that proposed outcome and exit when the adapter ran, and the copied controller's actual failure when it refused before client invocation.

For each `corpus-cli-*` refusal under the saved build 1666 default run, the operator compared outcome, exit and the complete structured failure with the signed CLI envelope. The resulting TSV stores their common value. Five admitted checks left the target absent. The operator then used the original signed app on the identical input and observed the newly created file. This exercises host decoding and admission without XPC. The host reservation, restart timing and external equipment path still need a production trial.

```swift
import Foundation
import Darwin

let input = FileHandle.standardInput.readDataToEndOfFile()
var answer: [String: Any] = [:]
func refused(_ f: PWRunnerRequestFailure) -> [String: Any] {
    var failure: [String: Any] = ["code": f.code, "path": f.path as Any]
    if let contract = f.expected_contract { failure["expected_contract"] = contract }
    return ["outcome": "bad_request", "request_failure": failure, "exit": 1]
}
do {
    let parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: input)
    switch admitSpecimen(parsed) {
    case .capacity(let f): answer = refused(requestCapacityFailure(f, parsed: parsed))
    case .refused(let f): answer = refused(f)
    case .accepted:
        if let policy = parsed.policy { _ = try computePolicyHash(policy) }
        answer = ["outcome": "admitted", "exit": 0]
    }
} catch is PolicyHashError {
    answer = ["outcome":"bad_policy","exit":1]
} catch {
    answer = refused(requestDecodeFailure(error))
}
let json = try JSONSerialization.data(withJSONObject: answer, options: [.sortedKeys])
FileHandle.standardOutput.write(json)
exit(Int32(answer["exit"] as! Int))
```

## Phase checkpoint

The host copy added the following line at the entry to `CWorkerOrchestrator`'s existing `phaseBoundary` closure, before the second phase's planning clock read. This is the entire difference in that source file.

```diff
@@ -136,0 +137 @@
+            if index == 1 { checkpoint(parsed.specimen_id, phases[index].phase_id, workerPid) }
```

The driver below ran the host locally using the signed candidate's worker and validator executables. Its private output and acknowledgement pipes belonged to one observer. A caller could sample the target before acknowledging, delay, close the pipe or leave it idle past the deadline. The existing worker performed the actions and produced its own phase observations. The prototype changed when the second phase proceeded, which affects what an experiment can conclude about timing.

```swift
import Darwin
import Foundation

func checkpoint(_ id: String, _ phase: String, _ pid: Int32) {
    print("READY \(id) \(phase) \(pid)")
    fflush(stdout)
    var pollfd = pollfd(fd: STDIN_FILENO,events: Int16(POLLIN),revents: 0)
    let status = poll(&pollfd,1,300)
    var byte: UInt8 = 0
    let acknowledged = status > 0 && read(STDIN_FILENO,&byte,1) == 1 && byte == 97
    print("RESUME \(acknowledged ? "ack" : (status == 0 ? "timeout" : "disconnected"))")
    fflush(stdout)
}
let args = CommandLine.arguments
let raw = try Data(contentsOf: URL(fileURLWithPath: args[1]))
let spec = try pwRunnerDecodeJSON(PWRunnerRunSpec.self,from:raw)
guard case .accepted(let admitted) = admitSpecimen(spec) else { exit(2) }
let r = CWorkerOrchestrator.run(admitted: admitted,policyHash:try computePolicyHash(spec.policy!),bundleId:nil,workerExecutablePath: args[2],validatorExecutablePath:args[3])
print("RESULT", r.normalized_outcome, r.phases.map { "\($0.phase_id)=\($0.arrival_observed)/\($0.completion_observed)" }, r.steps.map { "\($0.step_id)=\($0.attempt.outcome)" })
```

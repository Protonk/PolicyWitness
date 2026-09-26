import Foundation

let tk = TestKit()

FileHandle.standardOutput.write(Data("PWRunnerCore unit tests\n".utf8))

// This registry is the inventory of what each test file pins. Add a call and a
// one-line comment together; see runner/AGENTS.md → "Adding a new unit test file".

// Stubbed SandboxLib calls against the Swift apply helper, which has no
// production callers; the worked example for stubbing @convention(c) pointers.
runSandboxApplyTests(tk)
// Structural invariants of PWRunnerRunResult that the mirror-back audit signal
// depends on (test_overrides echo, runner_subprocess present iff observed).
runEnvelopeInvariantTests(tk)
// runSandboxCheck short-circuit for (operation, filter_kind) pairs that skip
// libsandbox; wire envelope of the synthesized prediction_unavailable verdict.
runPredictionUnavailableTests(tk)
// validateSandboxChecks tristate: value-required kinds, the no-value kind, and
// unknown kinds that downgrade rather than reject.
runFilterKindValidationTests(tk)
// Constructed drift/comparison interpretation controls from the public scope
// and attribution promises; they establish no native causes.
runDriftClassifierTests(tk)
// Release barrier, eligible-record lifetime, native spawn failures through replies,
// and response-8 encoding controls.
runOrderingTests(tk)
// Service reply degradation preserves observations, withholds claims and covers every wire field.
runReplyFailureTests(tk)
// Production host classifier fed constructed worker/validator results; the
// evidence → normalized_outcome table. Real driver controls live below.
runHostOutcomeClassifierTests(tk)
// buildAttemptResult: (kind, action, slot) → attempt outcome table.
runAttemptOutcomeMappingTests(tk)
// Documented limits in docs/limits.json against the Swift constants.
runLimitsContractTests(tk)
// CWorker driver with a real worker: shm setup, sentinel polling, publication.
runCWorkerTests(tk)
// Production host driver against the separately built ABI fixture with
// controlled kill/waitpid faults; host lifecycle observations only. The fixture
// never applies a sandbox, so no policy cause can be claimed here.
runCWorkerLifecycleTests(tk)
// Production C main with isolated native-call substitutions: ABI 6 progress and
// failure publication, missing step evidence, policy-write partial results,
// EPIPE partial output. Controlled call failures are not kernel attribution.
runWorkerEvidenceTests(tk)
// CWorker + ValidatorClient orchestration with real children: the join of
// worker slots and validator verdicts into one result.
runCWorkerValidatorTests(tk)
// Validator child through the shared lifecycle observer: byte-frame and record
// structure acceptance, competing observations, cleanup after controlled
// kill/wait failures.
runValidatorEvidenceTests(tk)
// Unfamiliar diagnostic codes and payloads survive worker and validator
// forwarding; inputs are independent of the receiver's enums.
runDiagnosticTransportTests(tk)
// Codable round-trip of the already-resolved `augments` field on the runner's
// parsed view of a request.
runAugmentTests(tk)
// pwListenerConfig argv → listener selection table (service vs --mach-service).
runListenerConfigTests(tk)
// Compiled-object receipt wire bytes: selected-byte changes versus ignored
// padding/order changes have different effects.
runAppliedProfileCaptureTests(tk)

FileHandle.standardOutput.write(Data("\n\(tk.summary())\n".utf8))
exit(tk.exitCode())

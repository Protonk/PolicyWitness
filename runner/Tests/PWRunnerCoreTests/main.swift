import Foundation

let tk = TestKit()

FileHandle.standardOutput.write(Data("PWRunnerCore unit tests\n".utf8))

// This registry is the inventory of what each test file pins. Add a call and a
// one-line comment together; see runner/AGENTS.md → "Adding a new unit test file".

// Structural invariants of PWRunnerRunResult that the mirror-back audit signal
// depends on (test_overrides echo, runner_subprocess present iff observed),
// the exact response-version gate and the removed wire keys.
runEnvelopeInvariantTests(tk)
// Host query planning: the shared (operation, filter_kind) exclusion set and the
// unrecognized-filter exclusion, with literal expectations.
runPredictionUnavailableTests(tk)
// validateSandboxChecks tristate: value-required kinds, the no-value kind, and
// unknown kinds and ineffective combinations rejected before execution.
runFilterKindValidationTests(tk)
// The comparison record producer, table-driven over the shared scenario matrix
// (tests/fixtures/comparison/matrix.json), the limitations vocabulary and host
// path provenance; it establishes no native causes.
runComparisonEvidenceTests(tk)
// Release barrier, eligible-record lifetime, native spawn failures through replies,
// and ordering encoding controls.
runOrderingTests(tk)
// Service reply degradation preserves observations, withholds claims and covers every wire field.
runReplyFailureTests(tk)
// Shared host admission, concurrent exported objects and owner-only exit scheduling.
runServiceAdmissionTests(tk)
// Production host classifier fed constructed worker/validator results; the
// evidence → normalized_outcome table. Real driver controls live below.
runHostOutcomeClassifierTests(tk)
// buildAttemptResult: (kind, action, slot) → attempt outcome table.
runAttemptOutcomeMappingTests(tk)
// Documented limits in docs/limits.json against the Swift constants.
runLimitsContractTests(tk)
// Host-only query and attempt-label bounds: constructed at-limit/over-limit strings
// and the orchestrator's refusal before any process work.
runQueryAdmissionTests(tk)
// Wire contract versions in docs/contract.json against the generated Swift copies.
runContractVersionTests(tk)
// Closed request objects, exact input version, lossless fields and separate admission limits.
runRequestContractTests(tk)
// Synthesized maximal reply (256 steps, every string at its limit) and the
// runner client budget derived from it; unclassified reply keys fail here.
runReplyMaximumTests(tk)
// Shared path-wire fixtures, strict compact states, rejected omissions and UTF-8 identity.
runPathDiagnosticsTests(tk)
// CWorker driver with a real worker: shm setup, sentinel polling, publication.
runCWorkerTests(tk)
// Production host driver against the separately built ABI fixture with
// controlled kill/waitpid faults; host lifecycle observations only. The fixture
// never applies a sandbox, so no policy cause can be claimed here.
runCWorkerLifecycleTests(tk)
// Production C main with isolated native-call substitutions: worker progress and
// failure publication, missing step evidence, policy-write partial results,
// EPIPE partial output. Controlled call failures are not kernel attribution.
runWorkerEvidenceTests(tk)
// Policy pipe deadline and independently observed transfer/cleanup evidence.
runPolicyTransferTests(tk)
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
// Optional augment shape and refusal of unresolved fragments in direct runner requests.
runAugmentTests(tk)
// pwListenerConfig argv → listener selection table (service vs --mach-service).
runListenerConfigTests(tk)
// Compiled-object receipt wire bytes: selected-byte changes versus ignored
// padding/order changes have different effects.
runAppliedProfileCaptureTests(tk)
// Worker disposition record: the resolver against fixture publications (C2, C5),
// constructed interpretation cases (B2 to B6, C3, C4, D1), encoder integrity, and
// the mirror of tests/lib/lifecycle_contract.py's spellings and example rows.
runDispositionResolverTests(tk)

FileHandle.standardOutput.write(Data("\n\(tk.summary())\n".utf8))
exit(tk.exitCode())

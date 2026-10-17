# runner_unit

Swift unit tests for the `PWRunnerCore` library — small helpers and
classifier branches, live worker/validator drivers, and host lifecycle observations.

`PhaseProtocolTests` checks eight held arrivals against independently observed
unlink effects, fresh planning and fresh validator processes, stale/future
release refusal, interrupted later collection and aggregate exhaustion.
It also runs the phase collection fixture through the full reply encoder,
rejecting contradictory evidence while preserving failed collection states.
`ValidatorEvidenceTests` checks exact/over frame, record and UTF-8 scalar bounds,
and real stream cutoff with retained complete evidence. The maximal reply
fixture accounts for all phases and bounded validator records through the
production encoder; it is a conservative constructed bound, not a reachable
native transcript.

## Invariants

- Runs the `PWRunnerCoreTests` executable target defined in
  `runner/Package.swift` via `swift run --package-path runner`.
- Uses a hand-rolled TestKit (no XCTest), so the suite works under
  Command Line Tools without full Xcode.
- `PWRunnerCore` is built with `-enable-testing` so tests can
  `@testable import` it; production builds via `build.sh` are unaffected.
- `HostOutcomeClassifierTests` covers the host's interpretation of
  constructed worker results; `runner_c_worker_harness` owns the real-worker
  `compile_failure` case. `ComparisonEvidenceTests` reads every row of
  `tests/fixtures/comparison/matrix.json` through `comparisonEvidence(...)`
  and pins the limitations vocabulary and host path provenance at the
  producer. The host never touches libsandbox, so no Swift test stubs it.
- The fast CWorker per-exec deadline diagnostic remains here; process-group
  cleanup, output retention, and plan continuation are covered through the
  public CLI by `runner_exec_lifecycle`.
- Exec-child environment and descriptor isolation are covered by
  `runner_exec_inheritance`, with explicit child observations and controlled
  worker launch resources.
- `DispositionResolverTests` drives the disposition resolver against fixture
  publications (`started_attempt` with two slots, `skip_publication`'s real D5
  conflict) and constructed outputs (B2 to B6, C3, C4, D1), checks encoder
  integrity and degradation of a record that contradicts its basis, and
  compares the Swift spellings and the resolver's answers with
  `tests/lib/lifecycle_contract.py` (every hand-reviewed example row).
- `PathDiagnosticsTests` pins all nine combinations of compact path states,
  UTF-8 identity, and rejection of conflicting/missing representations. `tests/fixtures/contract/path_diagnostics.json` supplies
  shared cases to Swift decoding/encoding, Rust receiver forwarding and Python
  consumer checks. CLI integration separately checks native Unicode realpath
  spelling through the signed app.

## Success criteria

- The test executable exits 0 and its final stdout line matches
  `^\d+/\d+ tests passed$`.

## Fixtures

- `tests/fixtures/worker_lifecycle/worker.c` is built by the wrapper with clang.
  It publishes controlled ABI payloads without applying a sandbox. The real
  host driver records completion followed by abnormal exit, cleanup kill, and
  failed/interrupted OS calls. Tests encode the assembled subprocess fields and
  independently clean up children left by fault controls. This is host coverage,
  not sandbox attribution or real C-worker publication coverage.
- Required real-worker deadline/grace and polling-reap controls use the signed
  app selected by `PW_APP_DIR` (default `dist/PolicyWitness.app`). Missing required
  equipment fails. The wrapper also rejects internal `SKIP` or `FAIL` lines
  before crediting the summary.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/runner_unit/<test_id>/artifacts/pwrunner_core_tests.log`

- The same artifact directory retains `worker-lifecycle-fixture` and
  `lifecycle-fixture-build.log`; subprocess JSON is printed in the Swift log.

## Run

```
./tests/run.sh --suite runner_unit --suite runner_c_worker_harness
```

Requires Swift, clang, Cargo and a signed app. The catalog declares the app
requirement for `runner_unit` itself, so the dispatcher records its integrity.
The wrapper builds and warms the lifecycle fixture and exports its path.
For direct SwiftPM execution, first run
`tests/fixtures/worker_lifecycle/build.sh <output>` outside the inspected app
and export that executable path as `PW_LIFECYCLE_WORKER_FIXTURE`. Direct
execution omits the wrapper's result checks and Rust reader replay below.

`WorkerEvidenceTests` requires the lifecycle builder's companion producers. It
checks actual C-main publication for controlled parameter/apply failures, open
numeric codes, publication validity, late completed slots, missing predictions,
memory-only text under deny-default, mapping failure and broken-policy-pipe
partial output. Failed-kill controls independently reap their owned fixtures.

`ValidatorEvidenceTests` checks strict byte-frame/record decoding and actual
validator driver cleanup. The shared `ChildProcessCalls` test boundary changes
only kill/wait observations. The `.validator` fixture is built beside the worker
fixture, outside the app; tests fail when it is absent and own independent cleanup.

Required worker/validator equipment failures throw `TestFailure`; they do not
return as passing cases. The wrapper also rejects any internal `SKIP` or `FAIL`
line before crediting the summary. Missing fixture environment is a normal
reported failure, not a force-unwrap crash.

`DiagnosticTransportTests` compares direct ABI decoding and Codable forwarding
against independent JSON inputs for two unfamiliar codes, then checks structural
publication gates. Its validator control preserves both unfamiliar diagnostics
and a known UTF-8 decoder fault through the actual subprocess encoder. The CLI
transport witness separately exercises C publication and client/controller
forwarding; these unit inputs do not establish native failure attribution.

`ServiceAdmissionTests` checks host-wide admission and owner-only retirement.
`service_admission_controls` restores per-connection claims and refusal exits
separately in a disposable source copy; each must restore its specific failure.
`PolicyTransferTests` checks real stalled/draining pipes, partial and interrupted
writes, zero progress, clock loss and failed cleanup, and joins the host's
transfer timeout to the shipped worker's length refusal of a truncated delivery
(the EOF receipt beside the write counts, `runner_failed` by precedence, reaped
by its own exit), rejecting fabricated kill, exit and receipt variants. Its
actual encoded replies are replayed through Rust assembly and the Python
consumer by the wrapper, including an evidence-preserving reporting failure
with a contradictory receipt. Constructed controls accept a receipt interrupted
before comparison and reject unequal counts beside later worker execution.
`WorkerEvidenceTests` also drives the production read-error branch with a closed
policy descriptor, requiring native failure evidence and no EOF receipt.
The exact Rust replay is ignored in standalone Cargo runs because it requires
those fresh driver receipts; it is mandatory in the default `runner_unit` case.

`CompiledProfileCaptureTests` constructs receipt bytes independently of the
reader. The shared `contract/compiled_profile.json` cases check schema and
producer/stage admission in Swift, Rust and Python; encoding also refuses
context on unavailable receipts. Changed selected bytes or consumed inputs must change their digests;
padding, unselected bytes and parameter-pair order must not. Corrupt identity,
extent or integrity fields, failed application and incomplete/abnormal worker
completion withhold the bytecode. The
[ABI suite](../runner_abi_layout/README.md#compiled-object-capture) separately
checks the C capture helper against constructed objects.

`ExtensionEvidenceTests` also run the native issuer with the host-owned channel.
They inspect physical zeroization and descriptor closure, and substitute failed
wait/kill observations after independent test cleanup to verify that published
issuance cannot supply a delivery descriptor without confirmed host reaping.

The combined-phase driver control (`PhaseProtocolTests`, matrix M08) retains a
validator deadline, failed termination and unconfirmed reap while its late write
independently observes EPIPE. A fresh validator supplies only the next phase’s
record. The registered reader replay checks the encoded reply through Rust
assembly and the Python consumer and lifecycle oracle; fixture query answers
are controlled data, and the test independently cleans up the surviving child.

The live stale/future phase-release controls also check failure-detail units:
wait expiry reports its millisecond budget, while a rejected future release
reports the observed ordinal. Constructed unknown failure codes retain raw
detail without acquiring either interpretation.

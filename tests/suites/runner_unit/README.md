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
native transcript. A separately encoded allowance counts every exec-observation
optional member at its maximum representation on every slot; a second full
ordinary encode/roundtrip carries valid collection/request/reap evidence on all
256 exec slots. The retained client output budget is unchanged.

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
- `ExecObservationTests` uses the shared constructed
  `tests/fixtures/contract/exec_observation.json` cases for typed decoding,
  ordinary-reply refusal and degraded evidence retention. The same cases run
  through Rust disposition admission and the independent Python consumer.
  Missing metadata stays unknown; successful signalling with unconfirmed reap
  remains valid. ABI fixture modes separately pin publication gating and
  reporting failure for malformed present payloads. `CWorkerTests` checks the
  signed producer's ordinary, nonzero, deadline and pre-spawn results.
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
- `ServiceAdmissionTests` separately checks validator selection inside nested
  and standalone bundles, including absent/non-executable local files and
  executable app-level decoys, then observes service default/override precedence.
  `OrderingTests` retains actual selected-path/return-code spawn receipts and
  encoded replies for missing and non-executable local defaults. Excluded-query
  controls independently observe an attempted file creation with zero validator
  launches; an earlier worker spawn refusal likewise creates no validator fact.
  These controls use the existing lifecycle worker, not a sandboxed specimen.

## Success criteria

- The test executable exits 0 and its final stdout line matches
  `^\d+/\d+ tests passed$`.

## System sleep

Host and worker allowances count system sleep. TestKit reads
`CLOCK_MONOTONIC_RAW`, which counts sleep, and `CLOCK_UPTIME_RAW`, which does
not, around every case. A case during which the system slept at least 1 ms
gets a separate line after its `ok` or `FAIL` line,
`system slept N ms during this case`; its outcome is unchanged. When a failure
overlapped sleep, the executable prints `K of N failures overlapped system sleep`
before its summary, and the wrapper adds that count to its failure message.
Such a failure is not product evidence.

`sleep_record_controls` builds a disposable package containing only
`TestKit.swift` and drives it with substituted readings: awake, slept,
sub-millisecond and uptime-ahead cases, passing and failing, then the real
clocks. The `ok` and `FAIL` lines stay exact, sleep lines and the count appear
only where the readings show sleep, and the patterns the wrapper and the
mutation controls read keep their meaning. It requires Swift and does not use
the signed app; its package, output and results remain under
`artifacts/controls/`.

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
The wrapper builds the lifecycle fixture, whose builder fails unless every
output's first exec exits with its recorded status, and exports its path.
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
`WorkerClockTests` runs the lifecycle fixture's clock companions (production C
main with one substituted continuous-clock boundary) through the real driver:
clock-setup refusals during and after policy delivery (published operation 12,
exit 12, no receipt, application or `done`), and, through production
orchestration with the shipped validator, a phase-2 sample refusal and a
phase-2 expiry that keep phase 1's chain and phase 2's open collection, a
rejected exec sample that refuses phase 2 by provenance with independent
confirmation that the killed child is gone, and an exec arithmetic refusal
after which phase 2 releases and acts. Phase-2 injection uses a bounded fixture
handshake with the validator-launch hook, exercised with prompt and delayed
authorization; fixed sleeps do not establish collection order. Missing receipts
and stale gates fail explicitly, and withholding authorization confirms fixture
timeout and driver reap without a fabricated timing failure. Gate receipts are
retained beside the replies. Both authorization schedules' encoded replies are replayed
through Rust assembly, the Python consumer and the lifecycle oracle by the
wrapper's `clock_readers` step. These replays are ignored in standalone Cargo
runs because they require those fresh driver receipts; they are mandatory in
the default `runner_unit` case.

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

## Host setup failures and descriptor collisions

`host_setup_controls` compiles disposable copies of the host sources with
selected native boundaries replaced by test adapters. It retains ordinary and
injected-failure runs, actual low-descriptor collisions, independent child
receipts and cleanup observations. Passing controls characterize both checked
refusals and paths that still spawn after setup failure; they do not certify
universal setup refusal. Rejected checker controls require the intervention,
child effect and cleanup evidence separately. The
[fixture contract](../../fixtures/host_setup/README.md) describes invalid-handle
containment and the limits of descriptor metadata. This case requires Swift and
clang and does not use the signed app; its sources, build log and receipts are
retained under `artifacts/controls/`.

## Host launch descriptor ownership

`launch_descriptor_controls` runs copied current host/validator drivers against
the selected signed worker. An independent observer challenges unused cells
through inherited writable mappings; host readback distinguishes the actual
evidence object from an identical writable decoy. Exact descriptor-number reuse
must survive driver teardown. Native spawn refusal and substituted earlier
setup failures retain one close and independent complete-range unmap observations.
High descriptors, self-duplication at fd 3 and separate fd 5 delivery preserve
worker entry endpoints, publications, release acknowledgement and confirmed reap.

Disposable source controls restore the old descriptor lifetime, retain a stale
deferred owner or omit the pre-spawn close-on-exec clear. The fixed candidate
assertions must reject each at its designated observation. Altered receipts
separately pin checker sensitivity. The [fixture contract](../../fixtures/launch_descriptor/README.md)
describes source transformations, object identity, cleanup and claim limits.
The case requires Swift, clang and a signed app; exact source copies, command
logs, receipts and rejected controls remain under `artifacts/controls/`.

## Host setup oracle sensitivity (opt-in)

`host_setup_oracle_sensitivity` preserves and runs the unchanged setup recipe and
checker against a baseline and three disposable host variants: the readiness
pipe's read end replaces its write end, the worker's shared-memory argument names
the ready descriptor, or evidence cleanup unmaps only one page. Every legacy
receipt and checker result remains available. Supplemental copied-fixture
instrumentation records the child's actual argv and `F_GETFL` access modes,
and scans exact native `mach_vm_region` ranges before and after the owner's
unmap. Each query retains its native result, returned range and object-name
right deallocation. The complete acquisition supplies the positive control;
full unmapping must leave no overlap with that range. A surviving owned suffix
is re-confirmed across its complete extent and independently unmapped, with its
cleanup return and subsequent absence retained before fixture exit. The legacy
map counter is recorded before that fixture cleanup and is never repaired.

The case requires the baseline to agree with those independent observations and
the controlled counterexamples to survive the old oracle. A pass characterizes
oracle blind spots; it does not establish product safety or fix those checks.
Sources, exact substitutions, hashes, build logs, original receipts and separate
observations are retained under `artifacts/controls/`. The additional observer
calls and cleanup exist only in these copied fixtures; this case requires Swift
and clang and does not use the signed app.


## Confirmed-reap acknowledgement

`CWorkerLifecycleTests` holds an ABI fixture until the host's native polling
wait, after the last acknowledgement/done samples. Clean completion and fatal
SIGTERM without `done` must both recover the previously unseen acknowledgement
at confirmed reap, qualifying the collected query while preserving each run's
actual disposition. An injected ownership error before acknowledgement keeps
order unestablished even when later reap is confirmed. `PhaseProtocolTests`
also checks that a later phase's ownership error leaves earlier established
phase credit intact.

The opt-in `reaped_ack_mutation` case copies the host and this bounded group,
then removes only final reconciliation. Both clean and fatal controls must fail
specifically at missing ownership credit; the broken-ownership control must
still pass. It retains exact copied sources/hashes, build/run commands and logs,
fixed/mutated host source and structured results. It requires Swift and clang,
uses isolated build output and does not modify or use the inspected app.

## Exec reader mutations

The opt-in `exec_reader_mutations` case copies the Swift package and runs only
`ExecObservationTests`. The baseline must pass all three controls. One source
variant bypasses the actual completed-slot gate: the self-killed ABI fixture's
fully written exec metadata must trip the existing absence assertion. Another
variant supplies a fabricated ordinary exec account when metadata is missing;
the assertion uses the original wire fixture to establish absence and rejects
the invented `not_requested` record. The copied package retains the source
identity solely to reach these oracles; the inspected app is unchanged.

The controls retain copied sources and hashes, actual compiler/run commands,
logs and exact designated failures. The native fixture is compiled against the
same copied ABI identity and owns no exec descendants. These controls establish
host interpretation, not sandbox behavior or successful process cleanup.

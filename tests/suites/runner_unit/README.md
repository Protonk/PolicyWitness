# runner_unit

Swift unit tests for the `PWRunnerCore` library — small helpers and
classifier branches, live worker/validator drivers, and host lifecycle observations.

## Invariants

- Runs the `PWRunnerCoreTests` executable target defined in
  `runner/Package.swift` via `swift run --package-path runner`.
- Uses a hand-rolled TestKit (no XCTest), so the suite works under
  Command Line Tools without full Xcode.
- `PWRunnerCore` is built with `-enable-testing` so tests can
  `@testable import` it; production builds via `build.sh` are unaffected.
- `SandboxApplyTests` exercises the unused Swift `applySandboxPolicy` helper
  with stubbed library calls. It provides no coverage of production C-worker
  failures or their forwarding. `HostOutcomeClassifierTests` covers the host's
  interpretation of constructed worker results; `runner_c_worker_harness` owns
  the real-worker `compile_failure` case.
- The fast CWorker per-exec deadline diagnostic remains here; process-group
  cleanup, output retention, and plan continuation are covered through the
  public CLI by `runner_exec_lifecycle`.
- Exec-child environment and descriptor isolation are covered by
  `runner_exec_inheritance`, with explicit child observations and controlled
  worker launch resources.

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
  equipment fails. Other live tests can print internal `SKIP`; inspect the log
  before crediting them, regardless of the summary.

## Artifacts

- `tests/out/suites/runner_unit/<test_id>/artifacts/pwrunner_core_tests.log`
- The same artifact directory retains `worker-lifecycle-fixture` and
  `lifecycle-fixture-build.log`; subprocess JSON is printed in the Swift log.

## Run

```
./tests/run.sh --suite runner_unit --suite runner_c_worker_harness
```

Requires Swift and clang. Selecting an app-dependent suite alongside it records
the signed app's integrity. Direct SwiftPM execution requires first building the
fixture and exporting its path as `PW_LIFECYCLE_WORKER_FIXTURE`.

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

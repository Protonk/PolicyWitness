# runner_unit

Swift unit tests for the `PWRunnerCore` library — small helpers and
classifier branches that no real specimen can exercise.

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

- None on disk. Tests construct fixtures inline.

## Artifacts

- `tests/out/suites/runner_unit/<test_id>/artifacts/pwrunner_core_tests.log`

## Run

```
./tests/run.sh --suite runner_unit
```

Skips when `swift` is not on `PATH` or `runner/Package.swift` is absent.

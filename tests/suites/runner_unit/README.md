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

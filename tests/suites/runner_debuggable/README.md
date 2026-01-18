# runner_debuggable

Runner suite for the built-in debuggable runner. It drives the
shared smoke and blackbox tests through `runner.mode=debuggable` and asserts the
reported `runner_kind`.

## Invariants

- Uses the embedded runner (no external install).
- Shared smoke and blackbox scripts receive `PW_TEST_RUNNER_MODE=debuggable`.

## Artifacts

- `tests/out/suites/runner_debuggable/<test_id>/artifacts/*`

Run:

```
./tests/run.sh --suite runner_debuggable
```

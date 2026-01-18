# runner_machme

Runner suite for MachMe services. It installs a Mach service runner from the
PWRunner binary, runs the shared smoke and blackbox scripts through
`runner.mode=machme`, and validates `runner_kind` in the output.

## Invariants

- Requires launchd bootstrap from a logged-in GUI session.
- Installs a MachMe runner under the user scope and removes it after the suite.
- Shared smoke and blackbox scripts receive `PW_TEST_RUNNER_MODE=machme` and the
  installed service name.

## Artifacts

- `tests/out/suites/runner_machme/<test_id>/artifacts/*`

Run:

```
./tests/run.sh --suite runner_machme
```

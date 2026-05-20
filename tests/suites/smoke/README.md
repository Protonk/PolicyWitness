# smoke

Quick end-to-end checks against a built app bundle. These scripts are shared
and invoked by the runner suites (debuggable/BYOXPC).

## Invariants

- Runs the CLI against small fixtures using the runner selected by the suite.
- Validates basic instrumentation behavior (success and validation paths).

## Success criteria

- Each smoke script exits 0 and produces `result.ok=true`.

## Fixtures

- `tests/fixtures/pw_runner/specimen_file_read_deny.json`
- `tests/fixtures/pw_runner/specimen_instrumentation_execmem.json`
- `tests/fixtures/pw_runner/specimen_instrumentation_invalid_phase.json`

## Artifacts

- `tests/out/suites/<suite>/<test_id>/artifacts/*` (suite is `smoke` when run directly).

Run:

```
./tests/run.sh --suite smoke
```

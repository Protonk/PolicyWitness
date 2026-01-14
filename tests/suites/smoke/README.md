# smoke

Quick end-to-end checks against a built app bundle.

## Invariants

- Runs the CLI against small fixtures using the embedded runner.
- Validates basic instrumentation behavior (success and validation paths).

## Success criteria

- Each smoke script exits 0 and produces `result.ok=true`.

## Fixtures

- `tests/fixtures/pw_runner/specimen_file_read_deny.json`
- `tests/fixtures/pw_runner/specimen_instrumentation_execmem.json`
- `tests/fixtures/pw_runner/specimen_instrumentation_invalid_phase.json`

## Artifacts

- `tests/out/suites/smoke/<test_id>/artifacts/*`

Run:

```
./tests/run.sh --suite smoke
```

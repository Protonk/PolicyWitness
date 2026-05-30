# smoke

Quick end-to-end checks against a built app bundle. These scripts are shared
and invoked by the BYOXPC runner suite.

## Invariants

- Runs the CLI against small fixtures using the runner selected by the suite.

## Success criteria

- Each smoke script exits 0 and produces `result.ok=true`.

## Fixtures

- `tests/fixtures/pw_runner/specimen_file_read_deny.json`

## Artifacts

- `tests/out/suites/<suite>/<test_id>/artifacts/*` (suite is `smoke` when run directly).

Run:

```
./tests/run.sh --suite smoke
```

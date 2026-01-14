# anomalies

Diagnostic reproductions of known or suspected sandbox anomalies.

## Invariants

- Tests are inverted: they pass only when the anomaly is observed.
- `PW_TEST_QUIET=1` so only the final anomaly note is emitted.

## Success criteria

- Each test prints an `Anomaly: ...` message and exits 0 when the behavior is reproduced.

## Fixtures

- `tests/fixtures/runner_smoke/v1/profile.sbpl`
- `tests/fixtures/runner_smoke/v1/specimen.template.json`

## Artifacts

- `tests/out/suites/anomalies/<test_id>/artifacts/*`

Run:

```
./tests/run.sh --suite anomalies
```

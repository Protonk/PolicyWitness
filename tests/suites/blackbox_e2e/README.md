# blackbox_e2e

End-to-end tests that treat the runner as a black box. Each case feeds a specimen
into the controller, runs a fresh runner instance, and validates the returned
JSON as a complete, correlated bundle. These scripts are shared and invoked by
the runner suites (debuggable/BYOXPC).

## Invariants

- One specimen launches one runner process and exits after reply.
- Every probe step has sandbox_check and attempt results.
- Probe actions are idempotent and scoped under a per-run test root.
- Denial classification is based on D (sandbox_check) plus the attempt outcome;
  we do not rely on deny-signal alone.

## How to run

```
./tests/run.sh --suite blackbox_e2e
```

## Pass/fail

A test passes only when the controller output matches the expected evidence
bundle for every step. Failures include mismatched sandbox_check outcomes,
attempt results, or denial classification.

## Fixtures

- Case directories: `tests/fixtures/blackbox_e2e/BBX-001/`, `BBX-002/`

The suite will also skip a case if `sandbox_check` returns outcomes that
contradict the expected policy (see the `anomalies` suite for known host bugs).

## Artifacts

- `tests/out/suites/<suite>/<case>/artifacts/*` (suite is `blackbox_e2e` when run directly).

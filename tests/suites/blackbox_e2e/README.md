# blackbox_e2e

End-to-end tests that treat the runner as a black box. Each case feeds a specimen
into the controller, runs a fresh runner instance, and validates the returned
JSON as a complete, correlated bundle. These scripts are shared and invoked by
the BYOXPC runner suite.

## Invariants

- One specimen launches one runner process and exits after reply.
- Every probe step has sandbox_check and attempt results; step IDs are unique
  and retain their expected order.
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

The checker collects errors across both evidence channels and all returned
steps. An unexpected prediction is a failure and cannot suppress validation
of an attempt or a later step. The shell wrappers treat every nonzero checker
exit as a failure.

Missing builds may skip the live cases. Prediction disagreements are never
inferred to be host limitations. Any supported host variation must be
expressed as a specific per-step expectation with supporting evidence, and
must preserve the remaining attempt and correlation assertions.

BBX-002's missing-file step explicitly expects `prediction_unavailable` and
an attempted read that fails with ENOENT. As specified in `PolicyWitness.md`,
an unavailable prediction requires `rc=-1`, null `errno` and `filter_type_id`,
and an explicit `drift:null`. Real allow/deny verdicts still require an integer
filter type. This step is validated normally and does not skip the case.

## Fixtures

- Case directories: `tests/fixtures/blackbox_e2e/BBX-001/`, `BBX-002/`
- Checker control envelopes: `tests/fixtures/blackbox_e2e/checker/valid_run.json`
  and `missing_path_run.json`

`checker_controls` runs without the app, before the live cases. Its checked-in
synthetic envelope passes BBX-001's expectations. Controlled changes must fail:
an incorrect later attempt, a prediction mismatch, both together, both on the
same step, malformed evidence channels, duplicate IDs, and reordered steps.
Combined failures must report each independent problem, so changing a skip
to an early failure is insufficient. These controls exercise the checker CLI
without importing its implementation or any production code.

The missing-file control also verifies the unavailable-result contract,
rejects an invented prediction, and proves that an expected unavailable
prediction cannot hide a later attempt failure.

## Artifacts

- `tests/out/suites/<suite>/<case>/artifacts/*` (suite is `blackbox_e2e` when run directly).
- Checker artifacts retain each synthetic envelope, exit status, and diagnostics.

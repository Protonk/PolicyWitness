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
- Denial classification uses the prediction plus attempt evidence. Response 5
  requires explicit `deny_signal: null`; the channel is unobserved. The checker
  retains support for legacy signal expectations on stored pre-5 replies.

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

`validate_run.py` uses `tests/lib/blackbox.py` for envelope, step identity/order,
required evidence fields, scalar types, and explicit prediction/attempt/errno/
drift expectations. The case files choose the expectations; denial and signal
checks stay in this suite. The helper performs no setup and makes no skip
decisions. The menagerie uses the same checks with its own policy requirements.
The required attempt aliases `rc`/`exit_code` and `errno`/`syscall_errno` must
agree in type and value. Nullable evidence keys remain present; optional attempt
`error` text can be omitted or null.

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

The menagerie's `validation_controls` also drives this checker CLI. It covers
shared nullable fields, integer/boolean distinctions, malformed envelopes,
step correlation, alias presence/agreement, and combined failures, alongside
each suite's own rules. Valid fixtures contain explicit compatibility aliases;
optional diagnostic text and expected null errno values have positive controls.
Paired responses with reordered steps must retain exactly the same step
diagnostics and add only one order error. These controls cover valid evidence
and a moved faulty attempt, comparing diagnostic multisets without pinning a
full transcript or its line order.

## Artifacts

- `tests/out/suites/<suite>/<case>/artifacts/*` (suite is `blackbox_e2e` when run directly).
- Checker artifacts retain each synthetic envelope, exit status, and diagnostics.

BBX file targets live in unique owned `/private/tmp/pw-bbx.*` directories,
including when the shared scripts run under BYOXPC. The rendered specimen and
`workspace.before`/`workspace.after` copies remain in artifacts; exit cleanup
removes scratch on success or failure. Test correctness does not depend on
Desktop/Documents privacy consent.

The shared checker requires response-7 comparison, submitted attempt kind/action
and host path provenance. Checker controls include a constructed response-7
positive case, missing comparison and independently malformed channels; the
stored response-5 fixtures continue to exercise legacy contracts.

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
- Query answers and attempt observations are checked separately; the checker
  rejects a `deny_signal` or `drift` key.

## How to run

```
./tests/run.sh --suite blackbox_e2e
```

## Pass/fail

A test passes only when the controller output matches the expected evidence
bundle for every step. Failures include mismatched sandbox_check outcomes,
attempt results, or comparison fields.

The checker collects errors across both evidence channels and all returned
steps. An unexpected answer is a failure and cannot suppress validation
of an attempt or a later step. The shell wrappers treat every nonzero checker
exit as a failure.

`validate_run.py` uses `tests/lib/blackbox.py` for envelope, step identity/order,
required evidence fields, scalar types, and explicit prediction/attempt/errno
expectations; `tests/lib/consumer.py` validates the envelope and every
comparison record first. The case files choose the query and attempt
expectations. The helper performs no setup and makes no skip
decisions. The menagerie uses the same checks with its own policy requirements.
Nullable evidence keys remain present; optional attempt `error` text can be
omitted or null.

Missing builds may skip the live cases. Unexpected answers are never
inferred to be host limitations. Any supported host variation must be
expressed as a specific per-step expectation with supporting evidence, and
must preserve the remaining attempt and correlation assertions.

BBX-002's missing-file step explicitly expects `prediction_unavailable` and
an attempted read that fails with ENOENT. As specified in `docs/PolicyWitness.md`,
an unavailable prediction requires `rc=-1`, null `errno` and `filter_type_id`,
and the `query_plan:path_unresolved_at_planning` limitation. Real allow/deny
answers still require an integer filter type. This step is validated normally
and does not skip the case.

## Fixtures

- Case directories: `tests/fixtures/blackbox_e2e/BBX-001/`, `BBX-002/`
- Checker control envelopes: `tests/fixtures/blackbox_e2e/checker/response15/valid_run.json`
  and `response15/missing_path_run.json`

The `response15/` envelopes are unmodified captures from the corresponding
current-producer cases; each carries its own build stamp, binary hashes and
worker source identity. Their sibling `valid_specimen.json` and
`missing_path_specimen.json` files are the exact submitted requests. Refresh
each envelope and specimen together from a passing live case. Superseded
acceptance captures remain available in Git; previous-envelope rejection uses
constructed controls.

`checker_controls` runs without the app, before the live cases. Its checked-in
live envelope passes BBX-001's expectations. Controlled changes must fail:
an incorrect later attempt, a prediction mismatch, both together, both on the
same step, malformed evidence channels, duplicate IDs, and reordered steps.
Combined failures must report each independent problem, so changing a skip
to an early failure is insufficient. These controls exercise the checker CLI
without importing its implementation or any production code.

The missing-file control also verifies the unavailable-result contract,
rejects an invented prediction, and proves that an expected unavailable
prediction cannot hide a later attempt failure.

Disposition controls reject missing or malformed worker-exit witnesses and
exercise the actual FIFO case's cleanup with controlled capture outcomes. They
check staging retention, setup failure before launch, metadata and removal
failures, preservation of the primary exception, and refusal of reused evidence.
No worker launches in these controls. The real Rust-red wrapper runs against
controlled Cargo output to distinguish the intended assertion from build and
unrelated failures, reject zero/wrong-test runs, and accept the exact passing test.
Artifacts retain cleanup receipts, recovery records, wrapper reports and arguments.
The disposition contract's structural self-check and the independent oracle's
self-check also run here: every hand-reviewed example row is reproduced by the
claim tables, a record built from it is accepted, its mutations are rejected with
the expected rule, and the core D-model evaluates totally. These are constructed
controls; they establish interpretation, not live reachability.
The expected-fixture controls accept `tests/fixtures/disposition/response15/a1_expected.json`
(a live envelope of the a1 specimen at the current contract), refuse the
captured `a1_known_loss.json` as the unsupported version it is before any
claim is read, and reject named mutations of the accepted baseline (missing
disposition record, request
removed while the cause is kept, exit code beside signal without a conflict,
supported cause replaced by unknown, identical unresolved or swapped step
answers, with or without differing debug indices), each with its expected rule.
The consumer library reports an envelope of another version as `unsupported`
and requires the record beside every worker subprocess.

The menagerie's `validation_controls` also drives this checker CLI. It covers
shared nullable fields, integer/boolean distinctions, malformed envelopes,
step correlation, one shape-allowlist mutation, and combined failures, alongside
each suite's own rules. Optional diagnostic text and expected null errno
values have positive controls.
Paired responses with reordered steps must retain exactly the same step
diagnostics and add only one order error. These controls cover valid evidence
and a moved faulty attempt, comparing diagnostic multisets without pinning a
full transcript or its line order.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/<suite>/<case>/artifacts/*` (suite is `blackbox_e2e` when run directly).
- Checker artifacts retain each synthetic envelope, exit status, and diagnostics.

BBX file targets live in unique owned `/private/tmp/pw-bbx.*` directories,
including when the shared scripts run under BYOXPC. The rendered specimen and
`workspace.before`/`workspace.after` copies remain in artifacts; exit cleanup
removes scratch on success or failure. Test correctness does not depend on
Desktop/Documents privacy consent.

The shared checker requires the six-field comparison record, submitted attempt
kind/action and host path provenance on every step at the current response
schema. `checker_controls` exercises the consumer directly: a synthetic
current-version envelope passes; another or malformed version is reported as
`unsupported` with no downstream errors; an unknown key at a recorded path and
a present key of another type are rejected under each shape golden
(`tests/fixtures/contract/envelope_shape.json`, `response_shape.json`);
each limitation outside the vocabulary, a record that contradicts its raw
fields and a `query_first` claim without its chain are rejected; the client's
own failure replies validate; and the ordering of a successful unlink against
its query is read from `order` alone.

Constructed policy-check captures cover the same current helper admission gate
as the controller. Rejected parsed payloads remain unchanged and opaque under
`invalid_reply`; wrapper fields still receive shape checks. Admitted helper
envelopes receive current-shape checks and must agree with the capture's copied
outcome, including unfamiliar outcomes. Previous versions and malformed replies
are constructed inputs, without historical helper fixtures or schema readers.

Observer controls admit both version markers before nested shape validation,
retain rejected JSON unchanged, reject recovered log claims and malformed
wrappers, and continue validating admitted report bodies.

`comparison_controls` exercises `tests/lib/envelope_compare.py` through its CLI
using the checked-in live envelope and constructed mutations. It runs offline
without a built app or migration output. Changed commands, flags, timeouts,
request arguments, argument order and list lengths must fail. Only executable
relocation and service renaming corroborated by each envelope's provenance may
pass. Predicate changes must retain the same filter apart from the recorded
worker PID. Structural controls reject missing empty containers, added fields,
container and scalar type changes, and missing or null volatile values. Each
control retains its inputs, report and diagnostics; negative controls must
reach comparison and name the expected difference, rather than merely fail
schema validation.

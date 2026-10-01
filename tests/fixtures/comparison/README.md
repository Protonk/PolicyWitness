# Comparison matrix fixture

`matrix.json` is the single source of comparison-record expectations: one row
per scenario in the drift removal plan's D1 matrix (S01–S25 with S04 unused,
B1–B7, C1 and T), each with the inputs that produce it, the raw channel values
a unit reader feeds to the producer, the raw fields a live reader asserts
beside the record, and the expected response 13 `comparison` object.
Expectations were reviewed against the D1 matrix and the independent
controls named per row; they were not generated from the producer under test.

Two readers share the file:

- `witness_contract/comparison_matrix` runs the S, B and C specimens through
  the CLI and checks every step against its row with the consumer's `validate`
  and `select`, keeping the independent controls (a direct EACCES open, file
  bytes before and after, direct spawn results). The existing
  `worker_attempt_in_flight_at_deadline` case reads row T after establishing
  its FIFO boundary; it owns FIFO cleanup.
- `runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift` is
  table-driven over the same file through `comparisonEvidence(...)`, appending
  the lifecycle limitation for `unit.lifecycle_summary` exactly as the step
  builder does.

## Placeholders

Absolute paths use the fixtures' `{{NAME}}` convention and are expanded by
both readers before use:

| Placeholder | Live reader | Unit reader |
| --- | --- | --- |
| `{{SCEN_ROOT}}` | a fresh directory it creates under `/private/tmp` | any fixed absolute string; only submitted-string equality matters |
| `{{STUB_VALIDATOR}}` | the absolute path of `stub_validator.py` beside this file | unused |
| `{{FIFO}}` | the FIFO the deadline case creates | any fixed absolute string |

## Files each specimen needs

`files` in the fixture lists every path under `{{SCEN_ROOT}}` with its
required state before a run: regular files with content and mode, copies of
`/usr/bin/true` and `/usr/bin/false`, paths that must be absent, and the
expected state after the run (`effect`). Specimen B is not idempotent: it
unlinks the paths it queries, and a run that fails after release still
performs its attempts, so the live reader recreates every file before every
run, including after a failed one.

## Specimen B is steered

Specimen B uses `_test_overrides.validator_executable_path` pointing at
`stub_validator.py` and `validator_io_timeout_ms: 500`. The stub answers deny
for b1, allow for b6 and b7, a diagnostic error record for b4, omits b2, b3
and b5, flushes, then holds stdout open until the host's validator I/O
deadline expires. The host retains and associates the emitted records,
releases the worker and builds all seven step results; the run ends in
`normalized_outcome: validator_no_reply` while b1, b6 and b7 keep
`order: query_first`. The transcript is stub output, not a native
`sandbox_check` result: B's expectations come from the submitted scopes and
the independent file controls. This is input-steering through a documented
override, not result-faking; the real worker performs the attempts and the
real host joins the channels, and the run is self-describing because
`test_overrides` is echoed in the reply.

A steered validator cannot omit a verdict by skipping a line and then exiting
cleanly: the host counts uniquely associated records and refuses the run with
`validator_unavailable` before any comparison exists. The I/O-deadline seam
is what makes partial records observable with every step result present.

## Specimen mechanics the rows depend on

- An `unlink` attempt reaches `operation_relation: matched` only against a
  `file-write-unlink` query (S19, S25, B3, B5, B6).
- The validator answers every query before the worker is released, so S25's
  query of the path S19 unlinks sees the file and answers allow; the read
  then fails with ENOENT. B5 reads the path B6 unlinks; both queries are
  omitted by the stub.
- `process-exec*` is the query spelling the native API accepts for exec
  admission; the bare `process-exec` spelling (S11) is rejected by the
  validator as `unsupported_operation`, so its query column is `unavailable`
  and its order `unestablished`.
- The planner excludes queries whose submitted path does not resolve on the
  host at planning time (S07, S08, S18) and the `(sysctl-read, sysctl_name)`
  pair (S10); excluded steps carry the `query_plan:*` limitation and
  `order: unestablished`.

## Row provenance

`baseline_response12/` holds the response 12 verification of these rows
against the shipped `ff2b192` producer: retained run output supplied
twenty-five rows and two live specimens supplied the rest. The response 13
rows keep the five comparison values and prune each `limitations` list to the
D1 vocabulary. C1's raw shape (`runner_failed`, validator not invoked, worker
slot incomplete with lifecycle `not_reached`) and T's (`runner_timeout`,
attempt 0 in flight at the sentinel deadline, lifecycle
`started_without_result`) were taken from captured replies of the same
producer; T's retained baseline is the
`release-0.2.4-default` run of `worker_attempt_in_flight_at_deadline`.
Response 13 acceptance receipts are linked here once captured.

The `query` column in each row is a test column, not a record field: it is
`sandbox_check.outcome` when `result_source` is `validator` and the outcome
is `allow` or `deny`, otherwise `unavailable`.

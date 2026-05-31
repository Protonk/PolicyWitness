# runner_outcome_bad_request

Drives `normalized_outcome = "bad_request"` end-to-end through both
emit sites in `PWRunnerService.runSpecimen`. No `_test_overrides` needed
— `bad_request` is the only runner-side outcome reachable through normal
e2e.

## Invariants

- The Rust controller forwards both fixtures to the runner; the Swift
  side is responsible for the rejection.
- The host short-circuits before posix_spawning a worker, so
  `runner_subprocess` is absent and `steps` is empty.

## Success criteria

Two cases, each `result.ok == false` and `runner_subprocess == null`:

- **`swift_decode_failure`** — request JSON is missing required Swift
  fields (`schema_version`, `specimen_id`) but has enough policy
  structure to pass the Rust preflight. Asserts
  `normalized_outcome == "bad_request"` and the error mentions
  "request decode failed".
- **`missing_required_filter_value`** — Swift-decodable spec whose probe
  step has `sandbox_check.filter.kind == "path"` with an empty
  `value`. Asserts `normalized_outcome == "bad_request"` and the error
  mentions "filter.value required". Exercises the
  `validateSandboxChecks` value-required branch.
  (Was `unknown_filter_kind`; unknown kinds now downgrade to per-step
  `prediction_unavailable` rather than killing the plan, so the
  remaining filter-side `bad_request` trigger is the
  missing-required-value check.)

## Fixtures

- Both specimens generated inline by `run.sh`.

## Artifacts

- `tests/out/suites/runner_outcome_bad_request/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_outcome_bad_request
```

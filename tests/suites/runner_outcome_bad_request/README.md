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
- **`unknown_filter_kind`** — Swift-decodable spec whose probe step has
  `sandbox_check.filter.kind == "not-a-real-kind"`. Asserts
  `normalized_outcome == "bad_request"` and the error identifies the
  bad kind. Exercises the `validateSandboxChecks` branch.

## Fixtures

- Both specimens generated inline by `run.sh`.

## Artifacts

- `tests/out/suites/runner_outcome_bad_request/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_outcome_bad_request
```

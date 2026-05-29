# validator_batch_mode

Pins the contract for `sb_api_validator --batch <pid>`: reads NDJSON
probe lines from stdin, writes NDJSON verdict lines to stdout (one
verdict per probe, in input order), exits 0 on clean EOF.

This is the per-run validator invocation shape the C probe-runner will
use in RUNNER-RESHAPE-PLAN Step 5 — one validator process for all
probes in a run instead of spawning one per probe. The per-probe CLI
mode (used by `controller/src/sonoma_cross_check.rs` today) is
preserved unchanged.

## Invariants

- Each probe input line is a flat JSON object with string-only values.
  Required keys: `step_id`, `operation`, `filter_type`. Optional:
  `filter_value` (required when `filter_type != "NONE"`).
- Each output line is a JSON object with
  `kind=sb_api_validator_verdict`, `schema_version=1`, and (on success)
  `step_id`, `operation`, `filter_type`, `filter_type_id`,
  `filter_value`, `rc`, `errno`, `outcome ∈ {allow, deny, error}`,
  `error: null`.
- Per-probe failures (parse error, unsupported filter) surface as
  verdicts with `outcome ∈ {parse_error, bad_filter}` and a non-null
  `error` string. They do NOT abort the run — subsequent probes are
  still processed.
- `step_id` is preserved in error verdicts when it was already parsed
  before the failure (so the host can correlate the error back to its
  probe plan). `step_id` is `null` only when the parser couldn't
  recover it (e.g., malformed JSON before the field was reached).
- Blank lines in input are silently skipped.
- The validator exits 0 on clean EOF regardless of per-probe failures.

## Success criteria

A mixed-filter request with 3 happy-path probes (PATH, GLOBAL_NAME,
NONE) and 3 error probes (unknown filter, missing filter_value,
malformed JSON) produces exactly 6 verdict lines with the
classifications above.

## Fixtures

- Request specimen built inline as a heredoc in `run.sh`. The probe
  target is the test script's own PID — unsandboxed, so sandbox_check
  returns allow for the happy-path probes.

## Run

```
./tests/run.sh --suite validator_batch_mode
```

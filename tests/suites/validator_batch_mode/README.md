# validator_batch_mode

Pins the contract for `sb_api_validator --batch <pid>`: reads NDJSON
probe lines from stdin, writes NDJSON verdict lines to stdout (one
verdict per probe, in input order), exits 0 on clean EOF.

This is the per-run validator invocation shape the runner uses —
one validator process for all probes in a run instead of spawning
one per probe. The per-probe CLI mode is preserved for diagnostic
tooling.

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

A mixed-filter request produces exactly 10 verdict lines covering all
four sandbox_check outcomes plus all parser failure modes:

- 3 allow (`s_mach_allow`, `s_net_allow`, `after_overlong`)
- 1 deny (`s_path_deny` — path-filter probe against the sandboxed
  child, classifier branch `rc=1 && errno=0 → deny`)
- 1 error (`s_op_error` — unknown operation, classifier branch `else
  → error`, errno != 0)
- 1 bad_filter (`e1` — filter_type=BAD with filter_value present)
- 4 parse_error: `e2` (missing required field, step_id preserved),
  malformed JSON line (null step_id), `e_trail` (trailing garbage
  after `}`, audit-finding-1 regression), and the 80 KiB overlong
  line (audit-finding-2 regression).

## Fixtures

- Request specimen built inline in `run.sh`.
- Target PID is a `/usr/bin/sandbox-exec` child running `/bin/sleep
  30` with a profile that defaults allow but denies file-read-data
  under `/etc`. Targeting an unsandboxed PID (e.g. `$$`) would return
  allow for everything and leave the deny + error verdict-classifier
  branches uncovered.

## Run

```
./tests/run.sh --suite validator_batch_mode
```

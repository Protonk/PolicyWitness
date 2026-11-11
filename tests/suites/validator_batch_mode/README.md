# validator_batch_mode

Pins the contract for `sb_api_validator --batch <pid>`: reads NDJSON
probe lines from stdin, writes NDJSON verdict lines to stdout (one
verdict per probe, in input order), exits 0 on clean EOF.

The runner uses one validator process for the eligible probes in each
collected phase. The per-probe CLI mode is preserved for diagnostic
tooling.

## Invariants

- Each probe input line is a flat JSON object with string-only values.
  Required keys: `step_id`, `operation`, `filter_type`. Optional:
  `filter_value` (required when `filter_type != "NONE"`).
- Each output line is a JSON object with
  `kind=sb_api_validator_verdict`, `schema_version=1`, and (after a native call)
  `step_id`, `operation`, `filter_type`, `filter_type_id`,
  `filter_value`, `rc`, `errno`, `outcome ∈ {allow, deny, unsupported_operation, error}`
  and `error`. Allow/deny carry null error; unsupported-operation and error
  outcomes carry a diagnostic string.
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

A mixed-filter request produces exactly 10 verdict lines covering the native and grammar outcomes selected below:

- 3 allow (`s_mach_allow`, `s_net_allow`, `after_overlong`)
- 1 deny (`s_path_deny` — path-filter probe against the sandboxed
  child, classifier branch `rc=1 && errno=0 → deny`)
- 1 unsupported operation (`s_op_error` — unknown operation, native
  rc -1 and errno EINVAL)
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

The same target also serves direct-mode queries through the shipped helper.
Both duplicate-member orders preserve the final strings for all four recognized
query keys. `RAW:` and `RAW:0` select numeric filter zero: direct mode accepts
no value and rejects an extra value; batch mode requires a string value, retains
it in the verdict and invokes the no-value native filter. Direct calls repeat
the batch case's native deny and unsupported-operation queries. Both produce
`denied: true` in direct JSON, whose process exit is zero; plain output exits
one. The batch records distinguish `deny` with null error from
`unsupported_operation` with its diagnostic. Raw requests, outputs, commands
and returns are retained under `direct-batch`.

## predictions_do_not_report

`tests/fixtures/validator/no_report.c` compiles the production validator
source with a recording `sandbox_check` and drives the initial three batch probes
(PATH, GLOBAL_NAME, NONE), two per-probe invocations and the boundary controls
described below. Every recorded
`type` argument must carry `SANDBOX_CHECK_NO_REPORT` (0x40000000) with the
filter id intact. Without the flag the kernel reports a denied prediction as
`Sandbox: pw-probe-runner(PID) deny(1) <op> <path>`, indistinguishable from
the attempt's own line; the attempt's line then
arrives only as a coalesced "duplicate report". No kernel query, sandbox or
child is involved, so the control is deterministic.

The source control additionally exercises each recognized duplicate key alone
in both orders, both zero spellings, and six supplied native rc/errno pairs
across direct JSON, direct plain and batch modes. Its recorded-call arguments
and emitted records establish parser, dispatch and projection behavior. The
native results in this control are constructed: allow, deny, EINVAL and other
error pairs are supplied by the recording function. Every resulting native call
must retain the no-report flag. The live helper case provides separate evidence
for its particular native deny and unsupported-operation queries.

# SBPL helper implementation plan

Remove the literal parameter scan from `sbpl-check`. Native compilation decides
the helper's verdict, and the controller repeats it. Do not replace the scan
with advisory fields, missing-name hints or an opt-in mode. Passing
`policy.params` to libsandbox remains supported; only the scan and its findings
are removed.

Input refusal, parameter setup, compilation and import inventory must describe
the work actually performed. Keep input facts and import provenance. This
changes the helper's output contract and its capture, not specimen admission
or worker execution.

## Output contract

### Helper verdict and compile record

Keep `kind: "sbpl_check"` and the common envelope. Remove `missing_params` as an
outcome. Fold missing source and unsupported format into `bad_request`; keep
`policy_too_large`. Use `setup_error` for failed native parameter setup.

| Boundary or result | `result.normalized_outcome` | Exit / `result.ok` | `data.compile` |
| --- | --- | --- | --- |
| Unsupported format, missing source, or NUL in source/parameter key/value | `bad_request` | 1 / false | null |
| Source exceeds the existing helper byte cap | `policy_too_large` | 1 / false | null |
| `sandbox_create_params` returns NULL | `setup_error` | 1 / false | stage `params_create`, `ok: false` |
| `sandbox_set_param` returns nonzero | `setup_error` | 1 / false | stage `param_set`, `ok: false` |
| Compiler returns an error buffer, or no profile | `compile_error` | 1 / false | stage `compile`, `ok: false` |
| Compiler returns a profile and no error buffer | `ok` | 0 / true | stage `compile`, `ok: true` |

`data.compile` is an explicit null or `{stage, ok, error}`. It records the last
native stage attempted, not a history of all calls. Stage names align with
`PW_OP_PARAMS_CREATE`, `PW_OP_PARAM_SET` and `PW_OP_COMPILE` without importing
the worker ABI into the helper. An absent or empty params map goes directly to
`compile`; do not invent successful setup calls.

Error rules:

- Input refusals put helper validation text in `result.error`.
- Setup failures put helper text naming the failed call in `compile.error` and
  `result.error`. A failed parameter set retains its direct return code and
  parameter name in that text; do not substitute ambient errno or echo the value.
- When the compiler supplies an error buffer, copy its decoded text unchanged
  into both error fields: no prefix, trimming, missing-name hint or replacement.
  Keep the existing C-string decoding convention; this is text, not a raw-byte
  receipt. An empty native string remains an empty string, distinct from null.
- A NULL profile without an error buffer is a completed compiler call with no
  diagnostic: `compile.error` is null and `result.error` is the helper summary
  `sandbox_compile_string returned NULL without a diagnostic`.
- A profile and error buffer returned together remain a failure, retaining the
  native text. Release both allocations. Success has both error fields null.

Preserve the direct helper's argument, request-read and JSON-decode failures:
exit 2 with stderr and no JSON envelope. Do not replace its small request reader
with the specimen decoder or make it require a specimen `schema_version`.

### Import inventory and input facts

Replace the flat helper result fields with these groups:

| Field under `data` | Shape and meaning |
| --- | --- |
| `compile` | Null or the stage record above; replaces `compiled` and `compile_error`. |
| `import_inventory` | Null or `{records, truncated, cycle, policy_closure_sha256}`. Each record keeps the existing `ImportRecord` fields. Replaces `imports`, `imports_truncated`, `imports_cycle` and the top-level closure hash. |

Remove `params_referenced`, `params_supplied`, `params_missing`, `params_unused`
and `params_scan_complete` entirely. They are absent, not null or empty. Do not
introduce a `param_scan` group or another representation of those findings.

Keep `policy_format`, `policy_sha256`, `params_present`, `params_count` and
`macos_build_version` as input/host facts. Missing or null params means
`params_present: false`; an empty map means true; both have count 0.
`policy_sha256` is null on input refusal and populated after validation.

Order the work explicitly: decode; validate format, source presence, source byte
cap and every native C string; collect the import inventory; perform native
setup and compilation; construct the verdict. Convert source, keys and values
to C strings before allocating native params. No import walk or libsandbox call
occurs on an input refusal; `compile` and `import_inventory` are explicitly null.
No stage scans for literal parameter references.

On admitted input, the import inventory remains available even when setup or
compilation fails. A performed walk with no imports has an object with empty
`records`, not null. Import resolution errors, truncation and cycles stay in
the inventory and never veto or replace native compilation. Preserve the
existing closure hash algorithm and its treatment of unresolved imports.

### Controller capture

In [src/policy_check.rs](src/policy_check.rs), keep `status`, `tool_exit_code`,
the flattened transport fields and the complete nested `envelope`. Remove the
projected `compiled`, `compile_error`, `normalized_outcome`, `policy_format` and
`policy_sha256` fields. Readers use the nested envelope for those observations.

Apply capture status precedence in this order:

| Observation | Capture `status` and retention |
| --- | --- |
| Helper cannot launch or request delivery fails | `unavailable`, following the existing unavailable-capture path |
| Stdout capture is truncated | `capture_error`; no parsed envelope, even if the retained prefix is JSON |
| Untruncated stdout fails UTF-8/JSON decoding | `parse_error`; no parsed envelope |
| No parsed output (including empty stdout) | `tool_error` |
| Parsed output lacks the helper kind, current integer envelope version, or nonempty string `result.normalized_outcome` | `invalid_reply`; retain parsed output unchanged |
| Supported helper envelope with an outcome | Copy that outcome exactly into `status`; retain the envelope unchanged |

Check the version before interpreting its outcome. A different integer version
also uses `invalid_reply` with its bytes/parsed object retained; do not introduce
another transport vocabulary or translate old fields. Do not infer success from
`data.compile`, `result.ok` or the process exit code. Preserve an unfamiliar
outcome string and independent `tool_exit_code`; producer tests enforce normal
agreement, while the capture reader does not manufacture a second verdict.

The helper is still invoked only after an admitted `xpc_error` reply. Neither
helper success, failure nor capture loss replaces the runner reply or changes
the controller's original run outcome.

## Implementation order and owners

1. In [src/bin/sbpl-check.rs](src/bin/sbpl-check.rs), remove `ParamDiff`,
   `compute_param_diff`, `empty_param_diff`, `missing_param_error`, the scan
   invocation, its output fields and the missing-name precedence branch.
   Remove scan-only imports and comments. In
   [src/sbpl_lex.rs](src/sbpl_lex.rs), retire the unused `param_scan` entry point
   and parameter-only tests. Rename the shared `ParamScanResult` type to
   `ImportScanResult` and update its comments. Preserve `import_scan` and the
   underlying lexer behavior, moving reusable lexer controls to import cases
   as described below.
2. In [src/bin/sbpl-check.rs](src/bin/sbpl-check.rs), introduce the typed nullable
   groups, centralize validation, and replace `Result<(), String>` with the
   stage result. Keep native resources and their C strings alive through the
   call, then free every acquired resource on every return. Add narrow
   injectable native-call and import-walk boundaries for unit
   controls; no public flags, environment overrides or runner test seams.
3. Update the capture reader and every `PolicyCheckCapture` construction in
   [src/run_flow.rs](src/run_flow.rs). Keep `fallback_policy_check`'s invocation
   gate. Implement the acceptance controls below alongside these changes.
4. Batch the incompatible output changes into one `controller_envelope` bump,
   currently 6 to 7, in [docs/contract.json](../docs/contract.json). Run
   `python3 docs/generate_contract.py`; never edit generated numbers. If the
   manifest has moved before implementation, rebase this change on its current
   value. Request/response contracts and worker source identity do not change.
5. Update `sbpl_check_envelope()` and the capture fixture in `run_flow.rs`, plus
   `check_shape_agrees_with_the_envelope_golden` in `sbpl-check.rs`. Populate all
   new optional object/string fields in the field-complete fixtures. Run the
   golden test, inspect `envelope_shape.candidate.json`, and replace
   [envelope_shape.json](../tests/fixtures/contract/envelope_shape.json) with
   the reviewed candidate as prescribed by
   [Shape goldens](../docs/CONTRACT.md#shape-goldens). Explicit null/absence
   tests below remain necessary; the golden is not a required-field validator.
6. Update the [guide's helper section](../docs/PolicyWitness.md#sbpl-check-sbpl-check)
   and outcome-catalog reference, the `data.policy_check` account in
   [README.md](README.md#output-contract), and the helper coverage sentence in
   [tests/COVERAGE.md](../tests/COVERAGE.md). Review `helper_source` wording in
   [limits.json](../docs/limits.json) without changing its value or counting;
   run `python3 docs/generate_limits.py` for owned copies. Document the native
   verdict, stage record and retained import inventory; remove scan-field
   instructions and suggestions to consult missing-name findings.

Keep [src/sbpl_imports.rs](src/sbpl_imports.rs)'s resolver/hash logic, the shared
import lexer and the controller dossier unchanged in behavior. Retiring the
parameter scanner must not remove import scanning or its completeness signal.
No runner/worker source edits, new helper executable, capacity change or CLI
surface change belongs in this implementation.

## Acceptance tests

Add these to the existing test owners; this section specifies tests to implement,
not tests already run. Use controlled native-call results for unreliable failure
paths and real helper invocations for compiler behavior. Do not assert an exact
macOS diagnostic sentence in native integration tests.

### Helper controls without native compilation

Owner: the `sbpl-check.rs` unit module, under `unit/rust.unit`. Drive the real
admission/setup/compile routine with controlled native calls and import-walk
spies; assert call counts and resource release as well as JSON. Pure serializer
rows alone cannot prove that admission prevented a compiler call.

For every newly emitted helper envelope, assert that the five retired scan
fields and `param_scan` are absent by key membership, rather than comparing
lookups with null. No producer outcome is `missing_params`.

| Case | Required assertions |
| --- | --- |
| Unsupported format, missing source, over-cap source, NUL in source/key/value (separate inputs) | Exact refusal outcome/exit/ok from the contract; `compile` and `import_inventory` explicitly null; no import-walk/create/set/compile call. Params presence/count still describe the decoded map. |
| Source at the byte cap and one byte over, including multibyte UTF-8 | At-cap input reaches the controlled compiler; over-cap input is refused before the import walk or native calls. Counting remains UTF-8 bytes, not characters. |
| Absent, null and empty params | Correct presence/count; successful compilation reaches `compile` directly; no create/set call. An inventory object with empty records distinguishes a performed walk with no imports from refusal. |
| Create returns NULL | `setup_error`, stage `params_create`; no set/compile call and no free of an unallocated params object. |
| A later set returns an unfamiliar nonzero code after an earlier successful set | `setup_error`, stage `param_set`; error retains call/name/code; no compiler call; params freed once and no value echoed. |
| Compiler returns NULL plus a distinctive diagnostic (also test an empty string) | `compile_error`, stage `compile`; both error strings equal the supplied diagnostic exactly; error buffer and any params freed once. |
| Compiler returns NULL with no diagnostic | `compile_error`, stage `compile`, `compile.error: null`; exact helper summary in `result.error`. No setup-failure classification. |
| Compiler returns a profile without error; separately, a profile with an error buffer | First is `ok`/0 with null errors; second is `compile_error`/1 with the native error. Free every profile, params object and error buffer acquired, once each. |
| Inventory contains import errors, truncation or a cycle | The same controlled native result produces the same verdict/error/exit for every inventory variant; inventory findings survive in their group. |

Retain the import-resolver controls for cycles, diamond imports, limits and
closure hashes. Before deleting parameter-scanner tests, express reusable lexer
coverage with import forms: comments, quoted strings, escapes, whitespace,
lookalike keywords, sorting/deduplication, empty or unterminated input, and
literal/nonliteral mixtures. Keep the assertion that `import_scan` ignores
`(param ...)`; remove the reverse assertion that calls the retired scanner.
Test the new groups' serialization, including inventory with no imports and
inventory with partial records; do not reimplement those algorithms in the
helper tests.

### Native helper acceptance matrix

Owner: [integration/cli_contract.rs](integration/cli_contract.rs), under
`integration/cli.integration`. Replace
`sbpl_check_missing_params_returns_clean_outcome` with table-driven cases.
Each source below is complete; params are absent unless listed. Every row also
checks the actual process exit against `result.exit_code`, `result.ok`, the
`compile` stage/boolean, params presence/count, and absence of all retired flat
fields and `param_scan`.

| Case | SBPL source / params | Outcome / exit |
| --- | --- | --- |
| Plain success | `(version 1) (allow default)` | `ok` / 0 |
| Unused definition | `(version 1) (allow default) (define unused (param "OPTIONAL"))` | `ok` / 0 |
| Optional guard | `(version 1) (deny default) (if (param "DEBUG") (allow file-read* (subpath "/tmp")))` | `ok` / 0 |
| Required path parameter absent | `(version 1) (deny default) (allow file-read* (subpath (param "ROOT")))` | `compile_error` / 1 |
| Required path parameter supplied | Same source; `{"ROOT":"/private/tmp"}` | `ok` / 0 |
| Other compiler error beside missing name | `(version 1) (deny default) (allow bogus-op) (allow file-read* (subpath (param "ROOT")))` | `compile_error` / 1 |
| String composition needs a value | `(version 1) (deny default) (allow file-read* (subpath (string-append (param "HOME") "/x")))` | `compile_error` / 1 |
| Nonliteral parameter name | `(version 1) (deny default) (define (h pn) (allow file-read* (subpath (param pn)))) (h "FOO")` | `compile_error` / 1 |
| Supplied value unusable | Path-parameter source above; `{"ROOT":""}` | `compile_error` / 1 |
| Parameter text in a comment and an unused supplied value | `(version 1) (allow default)` followed by a newline and `; (param "GHOST")`; `{"UNUSED":"value"}` | `ok` / 0 |

On native errors, require the diagnostic in `compile.error` to be present and
identical to `result.error`; deterministic controls above establish the exact
copying rule independently of OS wording. Success retains null errors even
when source references an unsupplied parameter. These cases protect compiler
authority and parameter transfer without preserving scan-specific assertions.
Exercise both file and stdin helper input without requiring a full specimen.
Also pin exit 2, stderr and no JSON envelope for invalid arguments, an unreadable
request path and malformed request JSON.

Adapt `sbpl_check_records_import_provenance_for_system_sb` to
`import_inventory.records` and its nested closure hash, preserving its existing
provenance assertions. Adapt `failure_boundaries/fallback_helper` in
[check.py](../tests/suites/failure_boundaries/check.py) to require exit 1,
`policy_too_large` and explicit null groups instead of `compiled: false`.
That case is a direct helper size refusal, not a live fallback/XPC experiment.

### Capture, fallback and contract acceptance

Owners: `policy_check.rs` and `run_flow.rs` unit tests, the existing envelope
shape tests, and `blackbox_e2e/checker_controls`.

- Supported envelopes for `ok`, `compile_error`, `setup_error`, `bad_request`,
  `policy_too_large` and an unfamiliar nonempty outcome: `status` equals the
  nested outcome. Include a contradictory process exit and compile record to
  prove the capture does not derive another verdict; preserve both as received.
- Wrong kind; missing, noninteger or old version; missing, null, empty or
  non-string outcome: `invalid_reply`, with parsed JSON retained unchanged.
  An old-version envelope with `compiled: true` earns no recovered success.
- Retain the oversized-valid-JSON, invalid UTF-8, malformed JSON, empty-output
  and unfamiliar-diagnostic controls. Assert transport-status precedence,
  exact byte counts/retention and nested-envelope presence independently.
  Assert removed capture projections are absent, not present as null.
- Extend `fallback_compilation_is_requested_only_for_an_admitted_xpc_error`:
  helper success, rejection and unavailable capture leave the original runner
  reply and controller outcome unchanged. No helper invocation for `ok`,
  `runner_failed`, `xpc_timeout` or no reply. Exercise refused response versions
  through the existing run-flow admission controls, requiring a null
  `policy_check`; do not bypass admission by handing them directly to the
  fallback helper function.
- The new helper shape and capture agree with the new envelope golden. Current
  envelopes pass the independent consumer; old envelopes are rejected at the
  version boundary. Runner response shape and worker identity remain unchanged.

## Implementation validation and completion

After implementation and reviewed golden replacement, run the limits, contract
and worker-identity generators with `--check`, plus `git diff --check`.
Use the public dispatcher with fresh managed output names:

```sh
PW_TEST_OUT_DIR=tests/out/runs/sbpl-check-source-01 tests/run.sh \
  --suite source_drift --case unit/rust.fmt --case unit/rust.unit \
  --case blackbox_e2e/checker_controls
```

When libsandbox is available, build/sign through `make build`, then run the
native acceptance cases against that unchanged build. Serialize this work with
other libsandbox use. `RUST_TEST_THREADS=1` also serializes the integration
binary's helper and live PW cases, which otherwise run concurrently.

```sh
RUST_TEST_THREADS=1 PW_TEST_OUT_DIR=tests/out/runs/sbpl-check-native-01 \
  tests/run.sh --case integration/cli.integration \
  --case failure_boundaries/fallback_helper --case smoke/specimen_file_read_deny
```

Completion requires every acceptance case to pass, the one reviewed envelope
bump and golden, current generated documentation, and removal of the literal
parameter scanner and all its output fields. Parameter transfer, import
scanning/resolution and runner behavior remain intact. Preserve original
captures and run evidence; do not rewrite historical envelopes.

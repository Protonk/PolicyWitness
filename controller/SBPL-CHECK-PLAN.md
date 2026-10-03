# SBPL helper change sketch

This is a problem sketch for a later design discussion, not an implementation
specification. It concerns the standalone `sbpl-check` helper, its captured
result in the controller, and the readers of both. The direction is settled
enough to state: native compilation decides the helper's outcome, exit code
and error; the literal parameter scan and the import inventory are recorded
as findings beside that verdict; a check that stopped before a stage says so
instead of publishing empty results; and the controller's capture reader
repeats the helper's verdict rather than deriving a second one. Field names,
grouping and the exact stage vocabulary remain open.

The source question is “Missing parameters and compiler diagnostic provenance”
in [the user report](../pw-user-guide-report.md). The
[user guide](../docs/PolicyWitness.md#sbpl-check-sbpl-check) describes current
helper behavior independently of this design sketch.

## Problem

The current helper attempts compilation after its literal parameter scan; a
nonempty missing-name list then takes precedence in `result.normalized_outcome`,
`result.error` and the exit code.

That precedence rejects successful compilations and misattributes failed ones.
A literal reference can appear in an unused definition, or in an `if` guard an
author uses as an optional feature flag; both compile without the parameter.
The helper reports `compiled: true`, `compile_error: null`,
`normalized_outcome: "missing_params"` and exit 1 together. When compilation
fails for an unrelated reason, `result.error` names the missing parameter while
the compiler's actual complaint sits only in `data.compile_error`. The
controller's capture reader then derives its own `status` from `compiled`
first, so one helper result is labeled `compiled` in the run envelope and
`missing_params` in the nested envelope. These are two competing summaries of
one check.

The scan is load-bearing nowhere the product routes users. The controller runs
the helper only after an admitted `xpc_error`, to learn whether the policy
compiles on this host independently of the missing runner reply; it reads five
fields and none of them is a scan list. In a normal run a missing parameter
reaches the C worker and surfaces as `runner_failed` with the native compiler
text. The scan therefore serves direct invocation only. Its original aim, naming
unsupplied parameters beside a cryptic native message, is served by adjacency
in the data block, not by precedence over the compiler. The native message is
also not one message: the same unsupplied parameter produces different wording
in a path filter and in `string-append`.

Diagnostic provenance has related problems. `compile_error` carries native
compiler text behind a helper-added prefix, and also carries host validation
and setup prose from paths on which `sandbox_compile_string` was never called:
NUL in a key, a value or the source, `sandbox_create_params` returning NULL,
`sandbox_set_param` failing, and a NULL profile with no error buffer. Early
refusals manufacture empty scan lists with `params_scan_complete: true` and an
empty import inventory with `imports_truncated: false` and no cycle, including
when there was no source to scan or walk. The helper's missing-source refusal
is called `bad_policy`, a token the runner reserves for its defensive
policy-hash failure, while the controller refuses the identical request shape
in a run as `bad_request`.

## Steps to reproduce

Use a helper built from the source being reviewed. From the repository root,
set its path; an isolated app's corresponding path works too:

```sh
PW_SBPL_CHECK=dist/PolicyWitness.app/Contents/MacOS/sbpl-check
```

These are helper requests. They only need the `policy` object and do not launch
a sandboxed worker. The observations below were reproduced on macOS Sonoma
14.8.3; native diagnostic wording can vary by OS.

First, omit a parameter used by a path filter:

```sh
"$PW_SBPL_CHECK" --request - <<'JSON'
{"policy":{"format":"sbpl","sbpl_source":"(version 1) (deny default) (allow file-read* (subpath (param \"ROOT\")))"}}
JSON
```

Observed: exit 1, `result.normalized_outcome: "missing_params"`,
`data.compiled: false`, and `data.params_missing: ["ROOT"]`.
`data.compile_error` contains
`sandbox_compile_string failed: invalid data type of path filter; expected pattern, got boolean`.
Adding `"params": {"ROOT": "/private/tmp"}` to `policy` is the positive
control: exit 0, outcome `ok`, `compiled: true`, and no compile error.

Next, reference an unsupplied parameter in an unused definition:

```sh
"$PW_SBPL_CHECK" --request - <<'JSON'
{"policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default) (define unused (param \"OPTIONAL\"))"}}
JSON
```

Observed: exit 1 and outcome `missing_params`, despite `data.compiled: true`
and `data.compile_error: null`. `data.params_missing` is `["OPTIONAL"]`.

The same precedence rejects an idiom an author writes on purpose, an optional
feature flag:

```sh
"$PW_SBPL_CHECK" --request - <<'JSON'
{"policy":{"format":"sbpl","sbpl_source":"(version 1) (deny default) (if (param \"DEBUG\") (allow file-read* (subpath \"/tmp\")))"}}
JSON
```

Observed: exit 1 and outcome `missing_params`, with `data.compiled: true` and
`data.compile_error: null`. The policy is well formed and compiles to the
intended profile without `DEBUG`.

Precedence also misattributes a genuine compiler failure. Place an unbound
operation before the unbound parameter:

```sh
"$PW_SBPL_CHECK" --request - <<'JSON'
{"policy":{"format":"sbpl","sbpl_source":"(version 1) (deny default) (allow bogus-op) (allow file-read* (subpath (param \"ROOT\")))"}}
JSON
```

Observed: exit 1, outcome `missing_params`, and `result.error` reading
`policy references params not supplied: ROOT`, while `data.compile_error`
begins `sandbox_compile_string failed: unbound variable: bogus-op`. The summary
blames a parameter; the compiler rejected an operation name.

Additional controls isolate the provenance and authority problems:

| Helper input | Current observation |
| --- | --- |
| `{"policy":{"format":"sbpl"}}` | `bad_policy`; `compile_error` says `missing policy.sbpl_source`; `params_scan_complete` is true and `imports_truncated` is false although neither ran. |
| Source `(version 1) (allow certainly-not-a-sandbox-operation)` | `compile_error`, with a native unbound-variable diagnostic. |
| Otherwise valid source followed by a JSON `\u0000` escape | `compile_error` says `sbpl_source contains NUL`; conversion to a C string fails before compilation. |
| Unsupplied `HOME` inside `(string-append (param "HOME") "/x")` | `missing_params`; `compile_error` says `string-append: argument 1 must be: string`, not the path-filter wording. |
| `(define (h pn) (allow file-read* (subpath (param pn)))) (h "FOO")`, nothing supplied | `compile_error` with the path-filter wording; `params_missing` is empty and `params_scan_complete` is false. The native text already serves as the summary on this path. |
| `ROOT` supplied as the empty string, used in `subpath` | `compile_error` saying `empty subpath pattern`; `params_missing` is empty. Supplied is not usable; only the compiler knows. |
| `(param "GHOST")` spelled only inside a `;` comment | `ok`; the scanner skips comments as documented. |

## Readers of the helper output

Check these before preserving or removing any property; nothing else in the
repository reads the scan lists or the capture's projected fields.

- `parse_policy_check_output` in [src/policy_check.rs](src/policy_check.rs)
  reads `data.compiled`, `data.policy_format`, `data.policy_sha256`,
  `data.compile_error` and `result.normalized_outcome`, projects them to the
  capture's top level beside the complete nested `envelope`, and derives
  `status` from `compiled` before consulting the helper's outcome.
- `fallback_policy_check` in [src/run_flow.rs](src/run_flow.rs) only gates the
  invocation on `xpc_error` and treats the capture as opaque.
- Tests: `sbpl_check_missing_params_returns_clean_outcome` and
  `sbpl_check_records_import_provenance_for_system_sb` in
  [integration/cli_contract.rs](integration/cli_contract.rs); the
  `fallback_helper` case of `tests/suites/failure_boundaries/check.py`, which
  pins `policy_too_large`, a nonzero exit and `compiled: false`; the two unit
  tests in `policy_check.rs`, whose fabricated envelopes drive `status`
  through `data.compiled`; and `check_shape_agrees_with_the_envelope_golden` in
  `sbpl-check.rs`, which compares the helper's emitted shape with the
  `sbpl_check_envelope()` fixture in `run_flow.rs` and the
  `tests/fixtures/contract/envelope_shape.json` golden.
- Documentation: the guide's SBPL check section and its cross-reference in the
  `normalized_outcome` catalog; the `data.policy_check` bullets in
  [README.md](README.md); the `helper_source` counting text in
  `docs/limits.json` (“policy_too_large without a compile verdict”); the
  `failure_boundaries` sentence in `tests/COVERAGE.md`.

## Scope

Most work stays in [src/bin/sbpl-check.rs](src/bin/sbpl-check.rs): `CheckData`,
`empty_param_diff`, the three early refusal paths, `compile_sbpl`, and the
outcome selection in `main`. The capture reader in
[src/policy_check.rs](src/policy_check.rs) is in scope: its `status`
derivation and its projected fields are where the second summary is made.

The scan implementation in [src/sbpl_lex.rs](src/sbpl_lex.rs) and the import
inventory in [src/sbpl_imports.rs](src/sbpl_imports.rs) are shared with the
controller's dossier and do not change in logic; only the helper's
representation of their results changes. The problem does not call for macro
expansion or another SBPL interpreter.

Keep the helper independent of specimen admission and worker execution. The
controller keeps invoking it only after an admitted `xpc_error` reply, and its
report never replaces the original runner result. No runner or worker source
changes; the worker source identity is untouched.

## Direction

1. **The outcome follows the compile attempt.** `result.normalized_outcome`,
   `result.ok`, the exit code and `result.error` are functions of how far the
   helper got and what the compiler said. `ok` with exit 0 means the compiler
   returned a profile. A compiler rejection is `compile_error`, exit 1, with
   `result.error` carrying the native text verbatim. Input refusals keep their
   own tokens, and a failure in parameter setup gets its own token because the
   compiler was never invoked. `missing_params` is removed as an outcome, and
   with it the `result.error` text that listed names.

2. **One staged compile record replaces the boolean and the string.** The
   record is null when the helper refused the input before any compile-related
   work. Otherwise it names the stage reached, whether that stage succeeded,
   and the error text of that stage. The stage names mirror the worker's
   operations `PW_OP_PARAMS_CREATE`, `PW_OP_PARAM_SET` and `PW_OP_COMPILE`, so
   a reader can line up the helper's failure point against a worker failure
   record using the same words. Native text is stored without the helper's
   `sandbox_compile_string failed:` prefix; the stage field is the provenance.
   The NUL-in-source conversion failure moves up to the input refusals, so the
   setup stages only begin on admitted input.

3. **The scan and the inventory become nullable groups.** The parameter scan
   is null when it did not run, otherwise a group holding the referenced,
   supplied, missing and unused names and the completeness flag. The import
   inventory is null when it was not walked, otherwise a group holding the
   records, the truncation flag and the cycle. The closure hash travels with
   the inventory because it is derived from the walk. Request facts stay at the
   top level because they describe input rather than findings: `policy_format`,
   `policy_sha256`, `params_present`, `params_count` and
   `macos_build_version`.

4. **The capture reader repeats the helper's verdict.** When the nested
   envelope parsed, `data.policy_check.status` is the helper's own outcome.
   The transport vocabulary, `unavailable`, `capture_error`, `parse_error`,
   `tool_error` and `invalid_reply`, remains for everything else. The projected
   copies of `compiled`, `compile_error`, `normalized_outcome`,
   `policy_format` and `policy_sha256` are dropped; the complete envelope is
   already nested beside `status`.

5. **The refusal tokens stop colliding.** The missing-source refusal is renamed
   from `bad_policy` to the token the controller uses for the same request
   shape, `bad_request`. `policy_too_large` stays as it is: a documented limit
   with its own test. `unsupported_format` is a candidate to fold into
   `bad_request` as well, since the controller refuses both conditions with one
   token; see the remaining decisions.

6. **This is one `controller_envelope` bump.** Every honest representation of a
   skipped scan changes a field's type, and dropping the projections removes
   fields; [the contract](../docs/CONTRACT.md) requires a bump for either. The
   helper's envelope shares the controller's frame number, so the shape changes
   above are batched into a single bump from 6 to 7, edited in
   `docs/contract.json` and regenerated with `docs/generate_contract.py`.

7. **The original goal survives by adjacency.** On `compile_error`, the native
   text is the error and the missing literal names sit in the scan group beside
   it. The guide teaches readers to consult those names when the native wording
   is the path-filter type mismatch or the `string-append` argument error. The
   helper does not append a hint to the native text, because a missing literal
   name beside a compiler error does not prove causation.

## Remaining decisions

- The stage vocabulary: whether the record's stage values are spelled after
  the worker operations (`params_create`, `param_set`, `compile`) or after the
  libsandbox calls, and the token for a setup failure.
- Whether `unsupported_format` survives as its own token or folds into
  `bad_request`.
- Whether a refused input leaves the compile record null, as proposed, or
  carries a `refused` stage; null keeps it parallel with the scan and the
  inventory.
- The direct-use exit code for a policy that compiles while referencing an
  unsupplied literal name is 0 under this direction. Confirm that is the
  intended direct-use experience before removing the current test's claim.
- Whether any reader of the dropped capture projections exists outside this
  repository; the survey above found none inside it.

## Verification for the implementation plan

- Replace `sbpl_check_missing_params_returns_clean_outcome` with a table-driven
  integration test over the reproductions above, one row per case, asserting
  the outcome, the exit code, the provenance of `result.error`, the scan
  group and the compile record's stage.
- Move the `policy_check.rs` unit fixtures from `data.compiled` to the new
  deciding field, and add a parsed-envelope case whose helper outcome is
  `compile_error` to assert that `status` equals it.
- Keep `policy_too_large` in the `fallback_helper` case and replace its
  `compiled: false` assertion with the null compile record.
- Regenerate the field-complete fixtures and the envelope shape golden; the
  bump is acknowledged by replacing the golden with the reviewed candidate.
- Update the guide's SBPL check section and catalog cross-reference, the
  controller README's `policy_check` bullets, the `helper_source` counting text
  if the “compile verdict” wording changes, and the `failure_boundaries`
  sentence in `tests/COVERAGE.md`.

A later implementation plan turns the direction and the remaining decisions
into exact expectations for every reproduction, for genuine compiler failure,
for incomplete scans and for controller capture. This sketch stops there.

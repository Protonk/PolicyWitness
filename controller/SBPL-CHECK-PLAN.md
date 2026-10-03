# SBPL helper change sketch

This is a problem sketch for a later design discussion, not an implementation
specification. It concerns the standalone `sbpl-check` helper and its captured
result in the controller. The preferred direction is to let compilation decide
compiler success and keep the literal parameter scan advisory. The exact output
contract, failure classifications and implementation remain open.

The source question is “Missing parameters and compiler diagnostic provenance”
in [the user report](../pw-user-guide-report.md). The separate
[documentation plan](../docs/USER-GUIDE-PLAN.md) can correct the guide's description
of current behavior before this design is settled.

## Problem

The guide says both that missing literal parameters stop a policy before
libsandbox and that the resulting `compile_error` preserves libsandbox's
diagnostic. The current helper actually attempts compilation after its scan;
missing names then take precedence in the final outcome.

That precedence also rejects a successful compilation. A literal reference can
appear in an unused definition, so finding an unsupplied name does not establish
that compilation needs its value. The helper can report `compiled: true`,
`compile_error: null`, `normalized_outcome: "missing_params"`, and exit 1 together.
The controller's capture reader then labels that same helper result `compiled`.
These are two competing summaries of one check.

Diagnostic provenance has related problems. `compile_error` can contain host
validation or setup prose even when `sandbox_compile_string` was never called.
Early refusals manufacture empty scan results with `params_scan_complete: true`,
including when there was no source to scan. Ordinary compiler rejection uses
`compile_error`, although the guide currently promises `bad_policy`.

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
This is the clearest case for reconsidering the scanner's authority; it does
not establish that every unsupplied parameter is harmless.

Additional controls isolate the provenance problem:

| Helper input | Current observation |
| --- | --- |
| `{"policy":{"format":"sbpl"}}` | `bad_policy`; `compile_error` says `missing policy.sbpl_source`; `params_scan_complete` is true although no scan ran. |
| Source `(version 1) (allow certainly-not-a-sandbox-operation)` | `compile_error`, with a native unbound-variable diagnostic. |
| Otherwise valid source followed by a JSON `\u0000` escape | `compile_error` says `sbpl_source contains NUL`; conversion to a C string fails before compilation. |

## Likely scope

Most work should stay in [src/bin/sbpl-check.rs](src/bin/sbpl-check.rs):
`CheckData`, `empty_param_diff`, `compile_sbpl`, and the outcome selection in
`main`. Inspect [src/policy_check.rs](src/policy_check.rs), especially
`parse_policy_check_output`, as its immediate consumer. Relevant existing tests
live beside that code and in
[integration/cli_contract.rs](integration/cli_contract.rs), including
`sbpl_check_missing_params_returns_clean_outcome`.

The scan implementation is in [src/sbpl_lex.rs](src/sbpl_lex.rs); import inventory
is in [src/sbpl_imports.rs](src/sbpl_imports.rs). Their shared uses matter before
changing or deleting fields. The problem does not call for macro expansion or
another SBPL interpreter.

Keep the helper independent of specimen admission and worker execution. The
controller currently invokes it only after an admitted `xpc_error` reply; its
report does not replace the original runner result. Any chosen output change
will also need the appropriate consumer, fixture, contract and guide follow-up,
but this sketch does not prescribe those changes.

## Candidate direction

- Give native compilation the deciding role in compiler success. Consider
  removing `missing_params` as a separate failure classification while retaining
  useful literal-name findings as diagnostic context.
- Make it possible to distinguish input/setup refusal from an actual compiler
  failure. Prefer removing misleading claims and redundant fields over adding
  a general provenance framework.
- Represent an unperformed scan honestly. Consider omitting its results instead
  of publishing empty lists and a fabricated completeness claim.

These are design preferences, not a settled replacement schema. In particular,
a missing literal name alongside a compiler error does not prove causation.

## Decisions for the next design pass

1. Which scan findings earn a place in the helper output, and how should a
   skipped or incomplete scan be represented? Check actual consumers before
   preserving every existing property.
2. What should remain of `compiled`, `compile_error`, the normalized outcome and
   the controller's capture status? Decide their meanings together, including
   input refusal and parameter-setup failure.
3. Which reading rules change, and therefore which version, fixtures and
   documentation updates are required under [the contract](../docs/CONTRACT.md)?

A later implementation plan should turn those decisions into exact expectations
for the reproductions above, genuine compiler failure, incomplete scans and
controller capture. This sketch deliberately stops before that specification.

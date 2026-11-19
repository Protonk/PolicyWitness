# unit

Rust unit tests and formatting for the controller crate.

## Invariants

- `rust.unit` runs `cargo test --bins`. Controlled orchestration checks count
  manifest loads and client calls through the real `run` path. The field-complete
  envelope is compared with `tests/fixtures/contract/envelope_shape.json`;
  helper binaries check their nested subtrees.
- `rust.fmt` runs `cargo fmt -- --check` and fails on any difference; fix with
  `cargo fmt` in `controller/`.
- `rust.disposition_reds` selects the four disposition record controller tests by
  their full names with `cargo test --bin policy-witness -- --include-ignored --exact`
  (status conflict, projection and withholding of the carried record).
- `rust.byoxpc_reds` selects the two BYOXPC selection tests the same way: a required
  entitlement key present with value `false` is refused, naming the worker and key.
- Both selections also run inside `rust.unit`. Each wrapper requires all named
  tests to report success, the exact test count, and a zero Cargo exit status.
  Missing/ignored results, wrong selections, test failures and build/equipment
  failures fail the case. Raw Cargo diagnostics are retained without classifying
  assertion messages.
- The registry loader returns the empty registry only for a path where
  inspection finds no entry. A directory that cannot be searched, an ancestor
  that is a file, an unreadable file, a symlink to a missing target, a
  directory at the path, unparseable text and another schema version each
  refuse, the first five with the path and the system error; external
  selection reports that refusal and never "not found".
- Plist ownership is `owned` only for a present, regular, converted and
  matching observation: an object that is not a regular file and a differing
  `XPC_SERVICE_PATH` are `unowned`, an unconverted file and unknown presence
  are `unknown`, absence is `ambiguous`. A listed service with two `program`
  lines is `ambiguous`. These are constructed observations.
- The envelope writer writes the text and one newline and then flushes. A
  write that fails before the first byte, inside the text or at the newline,
  and a failed flush, are each an error; this is a constructed writer.
- `runner install` accepts as `XPC_SERVICE_PATH` only the bundle path as text,
  and each value it refuses is one for which the ownership classifier reports
  the resulting plist `unowned`.
- The fallback controls run the real `run` path with recording client and
  helper callbacks and replace the request file inside the client callback.
  For an ordinary request the helper's input equals the client's input byte
  for byte. For a request with an `actors` array each helper input is one
  independently authored policy object, never the held request; each actor's
  capture, read from the envelope in request order, is the one returned for
  that actor's object, and the `policy_check` key is present with null. The
  array may stand beside a top-level policy or be empty; a non-array `actors`
  member leaves the ordinary rule in force.
  A delivered host reply, a refused capture and a failed delivery give the
  helper no input. The callbacks are not the shipped client or helper; the
  opt-in `runner_byoxpc/reservation_controls` case observes a shipped client's
  `xpc_error` and the ordinary fallback capture beside it.
- The capture parser types a reply exactly when the client run reports no
  failure, over constructed client stdout; a fallback-eligible client run is
  refused by reply admission for every value of the members those two
  functions read.
- A typed reply with nine phases is refused on `run` as
  `malformed_runner_response` with exit 1, the decoded reply retained and a
  present, null diagnostics value.
- The import scanner follows a list holding `import` and one string through
  whitespace, comments and square brackets, and after a character literal, a
  quote inside a symbol or a `#!` comment. It reports every other list headed
  by `import`, including one with an escape other than `\"` or `\\`, an
  unterminated one and a parameter list spelled `(import)`, and keeps scanning
  inside it. A renamed or applied `import`, `eval` and `load` leave no form to
  report. The spellings are text; no compiler runs in this suite.
- The import walk gives a scanned file that holds an unfollowed form a record
  error beside its hash and names that file in the first problem; such a form
  in the submitted source is the first problem before any import is visited.
  The closure digest equals a digest of literal bytes that include the line of
  a hashed record carrying an error. The helper projects the flag for both
  constructed values with the verdict unchanged, and the dossier reports
  `incomplete` for an unfollowed form written with or without a space after
  `import`.
- No case requires a built `.app` bundle.

`execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields`
in [run_flow.rs](../../../controller/src/run_flow.rs) exercises completion,
assembly and serialization for successful, signaled, degraded and absent-worker
replies, including ordered phases and fresh reads. It checks the exact public
field sets, that the projected `runner_result` reads back as the same typed
record, the client observations, exit status and execution diagnostics. Real Swift policy-transfer and worker-clock replies
also cross this assembly boundary and independent consumers in `runner_unit`.

`compiled_profile_status_and_labels_alone_decide_run_admission` runs the
compiled-profile fixture corpus through production controller orchestration
with a supplied client result: two admitted rows and seventeen refused. Nine
refusals are status or label refusals by reply admission, with
`malformed_runner_response`, exit 1, the admission diagnostic and the decoded
reply retained. The other eight rows carry a non-string or absent status or
label and are refused by the test's typed JSON reader, with a null
`runner_result`. Every refused row has the diagnostics key present with null
and no fallback compilation. The two accepted rows retain `finished` and exit
0. The accepted captured row's nonce, source and parameter fields are
unrelated to the request, which asks for no capture: the test establishes
nothing about a receipt's association with a request. These are constructed
replies, with no worker capture or sandbox application.

## Success criteria

`finished_run_preserves_successful_and_failed_attempts` pins the run summary
independently of successful, permission-failed and other-failed attempts. Only
`finished` yields command success; the retired run spelling and failure summaries
retain their evidence without yielding exit 0.

- All unit tests pass (exit code 0) and the crate is rustfmt-clean.

## Fixtures

Current response captures and constructed reply helpers support disposition and
assembly tests. Authored fixture deserialization and binary admission reject
wrong types and missing required fields. Phase collection controls withhold
unsupported projections while preserving observations through assembly; the
independent consumer separately validates the public projection.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`.

- `<run>/suites/unit/rust.unit/artifacts/cargo-test-bins.log`
- `<run>/suites/unit/rust.fmt/artifacts/cargo-fmt-check.log`
- `<run>/suites/unit/rust.disposition_reds/artifacts/cargo-test-ignored.log`
- `<run>/suites/unit/rust.byoxpc_reds/artifacts/cargo-test-ignored.log`

Run:

```
./tests/run.sh --suite unit
```

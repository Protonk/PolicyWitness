# P2 answer key: spec-only oracle

Readers get the text of one contract subject and nothing else. For each
input, they predict the outcome and quote the sentence they relied on. The
coordinator took each expected outcome from an existing, independently
authored test row, named beside it, before any reader ran. A prediction is
graded right, wrong, or "the text does not decide". A "not decided" answer
that the key's row shows the text should have decided counts as a lead.

## S1 Validator association (R9)

The text given is the association rules in `31-steps.surface.md` ("Unique
association" and order eligibility) and in the lifecycle association
subject. Setup: an ordinary request has one step whose `step_id` is `café`,
spelled with U+00E9. It queries `file-read-data` on a path. Each input is
the validator record that comes back.

- **I1.** The record's `step_id` has the same bytes.
  Expected: the record associates with the step, there is no association
  issue, and the order can be `query_first`.
  Rows: `OrderingTests` and reader-corpus byte-identical neighbours (`cb00a2bd`).
- **I2.** The record's `step_id` is `cafe` followed by U+0301: canonically
  equivalent, different bytes.
  Expected: no association. Issues `missing_id` for the step and
  `unexpected_id` for the record. The step gets a synthetic query, its order
  is `unestablished`, and the outcome is `validator_unavailable`, exit 1.
  Rows: reader-corpus byte-different rows; `cb00a2bd`'s message.
- **I3.** The `step_id` bytes are identical, but the filter value is a
  canonically equivalent path with different bytes.
  Expected: `query_mismatch`, a synthetic query, order `unestablished`, and
  `validator_unavailable`, exit 1.
  Row: `cb00a2bd`'s message.
- **I4.** The request itself has two steps, `café` with U+00E9 and `café`
  with U+0301.
  Expected: request admission refuses them as duplicate names under
  canonical equivalence, so the outcome is `bad_request`.
  Row: the request uniqueness rule, unchanged by R9.

## S2 Import inventory (R12)

The text given is the `sbpl-check` import-inventory subject in
`11-policy.surface.md`. Each input is a policy fragment. `/d/marker.sb` is a
readable file holding one rule. Predict three things: whether the inventory
records `/d/marker.sb`, the value of `unfollowed_imports`, and whether the
compiler evaluated the import. All rows come from `cli_contract.rs`
`sbpl_check_inventory_reports_each_import_form_beside_the_compiler_result`.

- **I1.** `(import ; note` newline `"/d/marker.sb")`: recorded,
  `unfollowed_imports` false, the compiler evaluated the import.
- **I2.** `[import "/d/marker.sb"]`: recorded, false, evaluated.
- **I3.** `(import (string-append "/d" "/marker.sb"))`: not recorded, true,
  evaluated.
- **I4.** `(if #f (import "/d/marker.sb"))`: recorded, false, not evaluated.
  A record does not mean the compiler evaluated the form.
- **I5.** `(define pw-alias import)` newline `(pw-alias "/d/marker.sb")`: not
  recorded, false, evaluated. The scan cannot report a renamed `import`.

## S3 Registry loading (R2)

The text given is "Read and select records" in `50-installation.surface.md`.
`PW_RUNNER_REGISTRY` names the registry path. Rows: `321bb6c5`'s unit and
integration controls, and the surface's pins.

- **I1.** No entry at the path, whose parent directory exists, then
  `runner list`.
  Expected: a `runner_registry` envelope with empty `runners` and
  `pending_cleanup`, exit 0.
- **I2.** The path is a symlink to a missing target, then `runner list`.
  Expected: refusal, with one line on standard error, no envelope, exit 2.
- **I3.** A directory is at the path, then `runner status --id x`.
  Expected: refusal, with one stderr line, no envelope, exit 2.
- **I4.** The path's parent cannot be searched, and a `run` selects an
  external runner.
  Expected: a `tool_error` envelope carrying the inspection error, exit 2,
  and no runner client started.
- **I5.** `PW_RUNNER_REGISTRY` is set to the empty string, then
  `runner list`.
  Expected: the default path under `HOME` is used. This rests on source reading
  (`runner_manager.rs:514-520`), not on a test row.

## S4 Exec stream text and counts (R1)

The text given is the exec stream observation subject in
`32-lifecycle.surface.md` and the `stdout` field in `31-steps.surface.md`.
Each input is the child's whole stdout, written before it exits. Predict
`bytes_received`, `bytes_retained`, `truncated`, `text_exact`, and how the
text ends. Rows: `tests/suites/runner_use_c_worker/check_exec_stream.py`
expectations, observed equal in `product-group-default`.

- **I1.** `x` followed by 2,000 copies of `é` (4,001 bytes).
  Expected: received 4,001, retained 1,007, truncated, exact; the text ends
  with a newline and `... [truncated]`.
- **I2.** `xx` followed by 2,000 copies of `é` (4,002 bytes).
  Expected: received 4,002 and retained 1,006, because the cut backs up to
  the scalar boundary. Truncated, exact, and the text ends with the marker.
- **I3.** `HEAD`, a NUL, then 2,048 zeros (2,053 bytes).
  Expected: received 2,053, retained 1,007, truncated, exact; the NUL
  appears as U+0000 and the text ends with the marker.
- **I4.** 17 bytes that are not valid UTF-8.
  Expected: received 17, retained 17, not truncated, not exact; the text is
  17 replacement characters.

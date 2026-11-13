# C — bounded X07 oracle review

Reviewed the uncommitted diff to `tests/suites/blackbox_e2e/checker_controls.py::result_consistency_controls` after the maintainer accepted M01–M05. This is a source review before consolidated execution, not a test pass. Initial and cross-examination reports remain unchanged. No tests, builds, production/consumer edits, worktrees or helper agents were used; only this review note is written.

**Disposition: no blocking mistake or missing required scope found.** The change implements the bounded correction proposed in C07/X07. It does not change the consumer's admission or result semantics. Execution and inspection of the new receipts remain necessary before crediting the corrected predicate.

## Complete expected multisets

`control()` now compares `Counter(wanted)` against `Counter(errors)` in both directions before the result-category assertion. This detects unexpected, missing and duplicate messages; it does not discard unrecognized errors or infer expectations from actual output. It retains all actual errors and the independently expected strings, plus missing/unexpected differences, in the in-memory receipt. Successful case completion writes the two receipt files.

The result helper formats supplied values only. Four explicit baseline rows independently state finished → true/0 and each of the three other outcomes → false/1. Neither `_admitted_outcome` nor the production result classifier supplies expected semantics. Using the deliberately changed value to spell that value in an expected diagnostic is appropriate and does not make the oracle circular.

I checked these mutation families against the previously inspected fresh raw diagnostic sets and their source/fixture meanings:

| Family | Review |
| --- | --- |
| Single result fields, absent/null/type faults | The expected result diagnostic names the changed field and original admitted outcome. The four structural companions cover numeric outcome, integer Boolean field, Boolean numeric field and string numeric field. Absent/null cases correctly retain semantic-only expectations for this existing shape reader. |
| All three result fields | Three independently specified result diagnostics; no unrequested structural companion. |
| Removed or array result | Missing object produces the result-object error; array adds exactly its structural type error. |
| Missing comparison, alone and with exit fault | Exact step-labelled companion, plus only the independently expected exit diagnostic in the combined case. Taking the step label from the input identifies the affected record; it does not derive the semantic expectation from the consumer. |
| Profile contexts | Explicit captured/unavailable empty-error rows; status versus producer/stage semantic messages remain distinct. Boolean/number variants add their exact type errors, while null/absent/future-string variants do not. Fixture-name inventory and the `valid` Boolean are checked against the authored expectation table rather than used to invent its expected outcome. Valid contexts bind all three result fields; invalid contexts bind none, including the controller-shaped refused-result neighbors. |
| Rejected capture/delivery | Foreign capture, inconsistent truncation marker and failed delivery each name the admission diagnostic plus all three consequences caused by retaining accepted-looking projection fields. Reply-diagnostic-only has its separate single error. No result mapping is recovered from these refused captures. |
| Absent reply/assessment and projection discrepancy | No reply leaves mapping inapplicable; absent assessment does not disable an admitted mapping. Projection discrepancy expects both the exact byte/projection error and all three mismatches against captured finished. |
| Foreign host version | Now uses the same complete matcher and requires exactly the one version diagnostic; no descendant errors are admitted. |

The profile table covers the current checked-in `compiled_profile.json` cases. The capture consequence table matches the known consequences of these specific one-field mutations; it is deliberately not a general catalog of all possible capture failures. That boundedness is correct.

## Matcher sensitivity and reachability

The five sensitivity calls run through the same nested `control()` used by the ordinary mutation cases, with only its error source and receipt destination substituted. They use a literal expected exit error plus literal missing-comparison error:

1. Baseline: both expected messages, accepted.
2. Extra: append the unrelated sentinel, require rejection and exactly that unexpected message.
3. Missing: remove the comparison error, require rejection and exactly that missing message.
4. Duplicate: add a second comparison error, require rejection and exactly one unexpected copy.
5. Restored: original multiset, accepted.

The supplied lambda is consumed synchronously by each `control()` invocation, so loop-variable capture does not defer the selected list. The surrounding try/except requires a rejection for damaged cases and acceptance for baseline/restoration. Subsequent exact checks of the appended receipt's differences identify the intended reason; an unrelated failure before receipt append cannot earn the stated sensitivity. The separate `result-oracle-controls.json` preserves deliberately rejected matcher inputs without inflating the 134 consumer-input controls.

This is actual control-route sensitivity by source inspection, not merely a pure helper whose caller might ignore its result. The substituted diagnostics establish the test comparator's behavior; the normal 134 calls still exercise the real validator. Their evidence scopes should stay separate in the final receipt summary.

## Limits and follow-through

The old fresh evaluation remains evidence only for the earlier narrower predicate. After consolidated execution, inspect that all 134 consumer controls have empty missing/unexpected lists and retain their full expected/actual errors, and that the five oracle controls have exactly the intended baseline/extra/missing/duplicate/restored differences. No broad native rerun follows from this test-only matcher change by itself, and no new consumer interpreter is warranted.

No source changes were requested by this review. If execution reveals an unexpected companion, determine its necessity from the mutation and reader contract before editing the expected table; do not update expectations solely to reproduce actual output.

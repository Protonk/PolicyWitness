# Independent renderer review

Verdict: the submitted local-context/arithmetic correction faithfully renders the current model and should remain. A separate narrow implication-grouping correction is warranted before settling the readable account; that is a scope-clarity issue rather than a preference for more punctuation.

Reviewed patch SHA256: `64ba61679b3fb3b30370850f20e006a0af5f85dc0816247a0bc0a9aec736ff39`.
Manifest SHA256: `c06bc493921c04935726e214ebb85b7bc6deba3d26318b0012181dd59040df16`.
Both shared source files match the manifest's after hashes at review time:

- `docs/contract/tree.py`: `5e632b0d2fa16505c9416bf564f2664977bc51c97b4d41de76aa6bb402c05fb9`.
- `tests/suites/source_drift/contract_tree_controls.py`: `3984589264c6960360fe39a8346e14d0babb60949a3d40c3be7a2688a2c9252b`.

## Local context

The validator inherits context, restricts entry/recipient/report overrides to subsets, and treats an authored actor as a replacement. The new non-rule branch displays only locally authored who/where/entry/recipient/report. That matches compact child rows: the surrounding rule carries inherited context, while the local entry distinguishes the two refusal effects. The displayed labels use the existing context conventions and resolved component links.

`render.table()` calls `_facts_text` for the compact condition/effect/outcome rows; `_finding_consequence()` also calls it for effect/outcome rows in the findings index. I inspected the current generated response-geometry rows and the corresponding index row. Both now label the run consequence `Entry: cli run` and the verify consequence `Entry: runner verify`. The common outcome remains separate. No changed parser/context behavior is present in this patch.

The constructed context control widens the fixture parent within its already allowed root entries, locally narrows the failure effect to direct, and checks both body and findings output. This exercises the reported omission through the actual rendering path. Inherited applicability continues to be supplied by the surrounding or linked rule; the correction specifically retains local refinements.

## Arithmetic

The checker accepts precisely Add, Sub, Mult, FloorDiv and Mod for numeric operands; the renderer's operator map covers those five. Recursive operands now reach the existing `limit`/count/matches rendering, and parentheses at every BinOp preserve AST grouping. Current nested examples display `1 + (2 × 256 items)` and `(matching count + record count) + 1` explicitly. Subtraction bounds show their actual limit quantity and unit instead of a raw `limit(...)` expression. No arithmetic evaluation or public model change occurs.

The new constructed arithmetic control exercises an actual collection count against a limit-minus-one expression and requires the rendered value/unit/limit identity. It would detect the original raw-expression fallback. I read the source and generated examples; I did not execute the control or generator.

## Implication grouping follow-up

`_expression_text` currently emits `implies(A, B)` as `if A, then B` without delimiters. In the generated ordinary/actor run-reference geometry rows, the AST is a conjunction of several independent guarded obligations, including nested implications for an optional claim and its optional basis. The readable result has this form:

`(if A is present, then if A.basis is present, then bound_A and if C is present, then ... )`

A reader can reasonably take the later conjunction under A's antecedent. The AST instead requires the later C obligation independently of A. This matters when the first optional claim is absent and a later claim exists.

Wrap each implication rendering as `(if ..., then ...)`. The existing recursive renderer will then also delimit nested implications, preserving the antecedent/consequent relation without changing syntax, validation, stamps' authored meaning, or product behavior. Add a constructed renderer control containing independent conjunctive implications and a nested implication, checking the distinct closing scopes. Review the resulting generated reference rows after the active frozen suite finishes. The current submitted patch need not be reverted for this follow-up.

## Review scope

Opened the entire 61-line patch and manifest; expression inference for numeric operators, calls and comparisons; context inheritance/narrowing; RULE_KINDS/CONTEXT/fact grammar; `_expression_text`, `_context_text`, `_facts_text`, `_finding_consequence`, compact tables, field meanings, renderer traversal and findings-index callers; both new controls and their minimal fixture. Read current generated geometry body rows (including arithmetic and per-entry refusal effects) and its controller-findings row. A focused authored-source search showed the current sum/count/limit arithmetic uses.

This delegated review covers rendering and the stated constructed controls. The separate geometry authoring/product predicate audit belongs to its author and root; I did not independently re-prove those bounds here. No tests, model load, product import, generator, build, app command or shared edit was performed. Standard-library hashing only establishes the reviewed byte identities.

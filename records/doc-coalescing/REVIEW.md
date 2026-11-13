# Ownership review

Pass 1 review against `9eb81540`, limited to the proposed result-reading and
request-lesson ownership moves. Actual model: `gpt-6-astra` (parent-confirmed).
Source inspection only; no experiments, tests or builds and no execution credit.

## Verdict

Accept the allocation, with the qualifications below. First make the guide's
two factual corrections and local cross-references; then remove the genuinely
duplicated contract attribution paragraph and redundant tour conclusion.
Do not introduce an explanation manifest or a general excerpt renderer in this
cycle without identifying the authored paragraphs it actually replaces.
The app lesson move is useful only when it removes both the corpus input copy
and the guide's corresponding input construction. Its exposure remains an
explicit design decision; ownership mapping alone does not settle that interface.

## Minimum meanings and concrete edits

1. In [the guide](../../docs/PolicyWitness.md), change the reply-wide table's
   “remain available independently” to retained projections of the carried rows,
   immediately qualified by identity, launch-association and action-membership
   findings. Keep worker-local withholding, aggregate withholding and assertion
   location distinct. A distant contract link cannot replace this local caveat.
2. Change “If host encoding fails” and the `runner_reporting_failed` catalog
   description to validation **or** encoding. Link that catalog entry to the
   existing reporting-failure subsection. Preserve rich/minimal retention, removed
   comparisons, remaining lifecycle checks and the ordinary-check applicability
   limit locally. In `PWRunnerService.swift::pwRunnerReportData`, both operations
   are inside the same catch; rich validation/encoding can fall back to minimal
   or empty bytes. Do not imply that every failed writer yields an admitted
   `runner_reporting_failed` report. The existing no-admitted-report section
   supplies the adjacent reading path; a local link is sufficient.
3. In [41-diagnostics](../../docs/contract/41-diagnostics.surface.md), retain
   `diagnostics.issue.subject.withholding_scope` as the full attribution limit.
   Replace only the repeated actor-row attribution paragraph under
   `diagnostics.execution.reply_checks` with a reference to that definition.
   Preserve the action's inherited context, trigger, effect operands, ordering,
   stop-reason retention and untouched host fields. References must preserve
   the effective public dependency; review the resulting public snapshot.
4. In [CONTROLLER](../../docs/CONTROLLER.md), remove the closing restatement
   after the completion controls (“success reports host completion…”), retaining
   its contract link alongside the mechanism paragraph. That paragraph still
   needs exact-`finished` selection and independent diagnostic computation to
   explain the code. Preserve the constructed-control limit and independent
   Python reader's capacity gap. The actor join sequence and degraded branching
   are mechanism, not redundant normative prose; blanket shortening loses value.
5. Keep the guide's failed-attempt example and instruction to inspect integrity
   beside success. Its first paragraph repeats host completion conditions, but
   supplies necessary standalone meaning. Do not replace it with a repository
   link or import the classifier ladder. The envelope's selection effects,
   reply's producer commitments and diagnostics' recipient checks have different
   jobs; calling any one their sole owner would collapse those boundaries.

## Projection and input-migration decisions

- [runtime.py](../../docs/contract/runtime.py)::render exports a guide stamp
  table, not node excerpts. [tree.py](../../docs/contract/tree.py)::_example_document
  extracts one Rust raw JSON object, optionally one object member. Neither is
  generic lesson metadata or guide-rendering infrastructure. A new canonical
  summary above existing normative prose would add an alignment obligation.
  If future projection replaces necessary guide prose, explicitly design inherited
  applicability, standalone link rebasing and freshness checks; otherwise retain
  the small local explanation and count no authoring reduction for adding links.
- The actual removable request duplication is corpus `create`/`capture_typo`
  definitions versus guide heredoc/typo construction, not REQUEST-GRAMMAR's
  renderer invocation. `request_examples.py::materialize` also handles unrelated
  assertion mutations and repetition cases: moving that machinery is unnecessary.
- Choose a separately specified temporary lesson exposure or defer migration.
  Set identity injection, caller-supplied target/materialization, specimen IDs,
  output/refusal behavior and invalid-input emission deliberately. The existing
  `example` rejects all arguments, emits a fixed read-hosts request and applies
  run's parser/identity gate. Do not silently repurpose its admitted-example
  promise to emit a deliberately refused request. Future `policywitness help`
  remains a separate interface design.
- Preserve `create.json`, IDs/format assumptions used by BYOXPC's sed transform,
  compile-check consumption, saved results and absent-target guards, or update
  those downstream consumers together. Keep nonce generation, missing-nonce
  refusal and repair as explicit remaining lesson work. Moving two inputs does
  not eliminate their separately authored recipe or its maintenance.
- [guide_workflows.py](../../tests/suites/witness_contract/opt_in/guide_workflows.py)
  selects actual fences and hardcodes refusal expectations; it also checks
  existing-target preservation. Adapt acquisition selectors, not these oracles.
  Corpus diagnostic expectations and external effect observations must remain
  independent of the app renderer. A shipped guide cannot require checkout Python.

## Support presentation

No specific shared assertion/scope has been established for merging support.
Keep production, constructed-input, recipient-reading and native evidence distinct.
A generated appendix could reduce reading volume while preserving local scope and
limits, but does not reduce maintained records. Defer compaction until a precise
duplicate record or a concrete presentation problem has been identified.

## Integrated disposition

Reviewed PASS-1: accepted. Steps 2–3 retain guide-local meanings and tour
mechanisms; extraction remains conditional on actual copy removal. Steps 4–5
preserve downstream recipes, independent expectations and the explicit interface
decision. No further correction or broader audit is needed for this pass.

# A — returning contract and integration review

## Initial review status

Reviewed the maintainer's explicit acceptance of M01–M05 in `DECISIONS.md`, the four authored-surface diffs, their current normalized public snapshot, the generated contract diff and the controller tour draft. The original A inventory and cross-examination remain unchanged. This review is exposed to the integration work and is not an independent initial inventory.

Initial disposition: the authored meanings implement the accepted decisions without a runtime, shape or obligation-owner change. No substantive contract blocker found. Final integration crosswalk and verification receipts remain pending review; this is not final acceptance of the complete change.

## Accepted meanings and node realization

| Decision | Realized node | Review |
| --- | --- | --- |
| M01 completion-only success | `envelope.data.success_findings`, formerly `envelope.data.select.success_findings` | Definition explicitly limits itself to an admitted reply and references `envelope.data.select`. Finished remains true/0 beside failed attempts or integrity findings. Existing selection outcomes/effects are unchanged. |
| M02 actor-row retention | `diagnostics.issue.subject.withholding_scope` | Converted in place from gap to definition. Carried subprocess/action operands and copied labels are explicit; retention does not establish requested-actor attribution. Related reply-check and scope-example prose carries the same limit. |
| M03 degraded associations | `reply.failure.associations`, formerly `reply.failure.publish.associations` | Definition references publishing and actor-reader scope; it accepts degraded-form admission without ordinary association certification. Worker-local checks remain applicable; no comparison/query-order conclusion is recovered. |
| M04 merged vocabulary | `diagnostics.execution.vocabulary.vocabulary_choice` | Converted in place. Unresolved/inapplicable remain merged only in the controller projection; retained host state/reason preserve the distinction. |
| M05 separate classifiers | `diagnostics.execution.reader_evidence.classifier_generation` | Converted in place. Agreement remains checked within reader scopes; neither shared generation nor universal equivalence is promised. |

The two relocations are a valid realization within the current authoring grammar: a definition cannot be nested below a reporting rule. They do not move the reporting rules themselves or change their conditions/effects. The new `uses` edges preserve navigation to those operative rules.

The exact context consequence should be recorded accurately. M01's old gap inherited the selection rule's `when: present(envelope.data.runner_result)`, successful-admission `free_when`, and `where: run completion after admission`; its new definition inherits the payload subject's `where: run payload assembly` without those rule conditions. M03 changes inherited `where` from `host response encoding` to `host reply assembly`. Both retain their original who/entry/recipient/report context. Their own prose and references explicitly preserve the admitted-reply/degraded-form meaning. This is acceptable for descriptive definitions, but a claim that *all node contexts* are unchanged would be false. The accurate claim is that all executable/reporting-rule applicability, effects and ownership are unchanged.

I compared all normalized nodes in `docs/contract/public.json` against HEAD using a nonmutating in-memory script. Exactly the two old IDs are removed and the two replacement IDs added. The only non-prose changes among retained nodes are the three accepted gap-to-definition kind changes and removal of their gap-kind facts. All retained node contexts are identical. Surface-level fields outside the public node content are unchanged. This is a read comparison, not a generator execution or an independent proof of every runtime shape.

## Other scoped clarification and support metadata

`actor_evidence.actor.reader_scope` now distinguishes receiver comparisons of carried declarations from host request-to-reply assembly. This implements X02 without inventing an original-request operand or transferring host producer obligations. `diagnostics.execution.reader_evidence` explicitly preserves the Python consumer's collection-capacity-domain limitation. It does not weaken the controller geometry rule or promise identical reader admission.

The fallback support's old “association commitment remains open” limit is correctly replaced with the accepted degraded-form limit. The diagnostic-subject support's old “reserved withholding policy” limit correctly refers to the new withholding definition. Neither change adds execution credit. Existing run IDs, source snapshots, checks and assertion scopes stay historical and bounded. The added reader-domain prose is not evidence of a new execution or universal classifier agreement. No other stale support assertion referring to these five choices as undecided was found in the changed authored surfaces.

Unchanged historical plan references to the former open questions are planning history, not current normative definitions. They should not be used to reopen the maintainer's accepted scope or silently be represented as current public rules. The integration record must preserve both old-to-new ID mappings so the frozen original inventory remains traceable.

## Controller draft review

The draft separates origin/example emission, preparation/selection, invocation uncertainty, receiver admission, local/reply-wide projections, completion mapping, output, and administration. It preserves the consequential distinctions from A's inventory: held serialization versus import reads; host grammar versus controller identity; pipe acceptance versus receipt; original-request versus carried operands; selected metadata versus live equipment; missing publication versus no effect; ordinary output versus the example's explicit flush protocol; successful administrative command versus verified cleanup/validity. No new reader, owner transfer or stronger attribution guarantee is asserted.

The actor and degradation discussion matches M02/M03. Its constructed-control descriptions state what the named tests actually check without claiming every association failure or native reachability. Completion and consumer discussion retain M01 and the geometry-domain caveat. The diagram's “admitted xpc_error only” fallback arrow is read with the text's successful-delivery requirement, not as permission to use rejected captures.

Two moved-node anchors were stale in the first draft: `contract-reply-failure-publish-associations` and `contract-envelope-data-select-success_findings`. I notified the coordinator; D is correcting these to `contract-reply-failure-associations` and `contract-envelope-data-success_findings`. These are concrete link defects pending final draft confirmation, not substantive policy disagreements.

The tour's known-gap index includes accepted information limits (actor attribution, completion versus integrity, merged vocabulary and classifier scopes). That index need not imply those policies remain undecided: the body expressly identifies retained definitions. No requirement to redesign an accepted limit follows from cataloguing it there.

## Exposure and pending completion

No tests/builds/generators, native operations, worktrees or production edits were performed by A for this review. Only this review record was written. The shared baseline eight-case receipt does not automatically credit newly edited tests or documentation checks. I have not independently inspected new raw execution evidence.

Pending: D's stable final tour/crosswalk, confirmation of both moved anchors and exact mappings, and coordinator verification receipts for authored-tree/public-history/shape/prose/link/known-gap checks and the corrected oracle. The final crosswalk must preserve all 56 A families and distinguish the initial open-question wording from the now accepted disposition. Final acceptance will be appended after these inputs arrive.

## Stable integration review at `424f3c73`

D's stable tour corrects both moved anchors. Its accepted-node realization explicitly maps the two relocated IDs and retains the other three IDs. I checked the exhaustive crosswalk against the original inventory with an in-memory read comparison: all 56 family IDs occur exactly once, and every original node, promise, prerequisite/beneficiary and failure/dependency cell is preserved literally in its corresponding family. Thus no original contractual scope was silently omitted or replaced by a source-derived outline. I also read the crosswalk's distinct assertion/evidence, independent rejection and disposition entries and its declared scopes. Their grouped implementation routes remain attributed to A/B/C and do not claim D independently re-audited every native predicate.

The crosswalk explicitly labels preserved open-choice wording as the initial reading and supplies the accepted M01–M05 disposition and current ID mapping separately. In particular, A55's preserved “open choice” sentence is historical inventory content under this express convention, not a new unresolved decision. Native, source, constructed and execution support remain separate. I find no missing obligation family or unsupported owner transfer in this integration.

B has separately identified a minor tour precision correction: actor projection selects actions through the actor label and matching phase action IDs, not an additional phase-ID join. The existing authored rules already preserve the exact relation; the coordinator will make the narrow explanatory correction after the active verification run. This does not reopen M02 or require runtime changes.

A's contract/content disposition is accept, subject to that narrow wording correction and review of the consolidated verification receipt. The earlier normalized snapshot comparison was against the pre-integration committed snapshot at the time of inspection, not a comparison of `424f3c73` with itself. No new execution credit is claimed here.

## Final receipt review and acceptance

I inspected the raw summary, case reports and selected structural logs/receipts in `tests/out/runs/controller-authority-verification` before pruning. Run `20261113T155111Z_8ba29955` selected `source_drift` plus `blackbox_e2e/checker_controls` at `424f3c73`: 11 selected/completed/passing, no skipped or unrun cases, zero recorded sleep per case, and artifact-integrity reporting valid-before, unchanged, and no harness errors. This is verification of the changed documentation/controls, not a new native failure-path evaluation.

Relevant raw evidence read:

- `suites/source_drift/build_contracts/artifacts/build-contracts-receipts.json` is complete/ok with 91 passing controls. The current resolved-actor/controller-row control, complete stamp derivation, conjoined-context/field/effect controls and history/released-input controls passed. `contract.log` reports 91 tests and OK. These support authored tree/history/stamp/shape mechanics; they do not establish desired product policy or native production of constructed replies.
- `suites/source_drift/runner_source_manifests_agree/artifacts/check.log` reports 19 evaluated rules, zero input/gate-blocked, explicitly including `known_gap_index`, CLI surface agreement, guidance routes and evidence-channel paths; its case passed.
- `suites/source_drift/generator_contract/artifacts/generators-receipts.json` is complete/ok with 29 controls. In particular, line-level prose reading, prose baseline, local-link destination inclusion, anchor/symbol-link resolution and authored-surface prose scope passed. The generator log's intentional nested receipt-probe failures are part of a passing failure-reporting control, not unexplained suite failures.
- The consolidated summary also reports architecture/build/limits/footprint documentation, Markdown reader, direct Python, porcelain codec and corrected checker-controls cases passing. Detailed oracle assertion review remains C's owner; I do not substitute the aggregate pass for that review.

I inspected the exact post-run diff. BR01 changes only “carried actor labels, phase IDs and action IDs” to “carried actor labels and each matching phase's action IDs” in two prose lines of `docs/CONTROLLER.md`. It now matches the selected-action construction inspected in A-CROSS. No heading, link, anchor, code span, fence, generated region, literal control input, test, generator or authored contract changes accompany this correction.

Under `tests/AGENTS.md`'s Evaluate and reuse evidence rule, I accept retaining the structural results as a **reviewed applicability exception** for this exact prose delta. The document's bytes are changed, so this is not file-identity evidence for the final text. The relevant structural inputs—link/heading/fence/region structure, known-gap index and generator-owned material—are unchanged; the revised ordinary sentence introduces none of the checked structural constructs or new prose-rule exceptions. Runtime and oracle execution inputs are unchanged. Human source/contract review, rather than the structural run, establishes the corrected sentence's meaning. No third execution is needed for this delta; a broader subsequent edit would require a new applicability judgment.

**Final A disposition: accept.** The five approved meanings, effective-context accounting, complete family crosswalk, current links, evidence limits and corrected actor-action account have no remaining A finding. Raw receipts may be pruned through the repository's existing ownership/retention tools after the coordinator completes the other returning reviews. This acceptance adds structural/constructed receipt credit only at the scopes above and does not promote the original historical or native evidence.

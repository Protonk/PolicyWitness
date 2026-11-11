# Private authored reply-reference repair

Accept the proposed narrow fix. In diagnostics.execution.families, add `uses: ["identity.definitions.reply"]` to the existing definition facts and remove the prose sentence containing the generated fragment link. The dependency already exists in that sentence and in the table's ordinary-semantic-reply terminology. The shared Reply definition explicitly explains that ordinary semantic replies have no reporting_failure and include both single-worker and actor forms. This patch preserves that meaning and leaves all applicability/table rows intact.

## Original failure

The active workflow's completed source_drift/generator_contract case at tests/out/runs/contract-stage-four-workflows-20261111/suites/source_drift/generator_contract records fail. Its generators.log has 28 tests and one failure: test_prose_links_resolve_anchors_and_symbol_links, generators.py:733. The sole broken link is docs/contract/41-diagnostics.surface.md: missing heading #contract-identity-definitions-reply. The original failure remains a failed receipt.

`broken_links` (generators.py:168–190) correctly resolves a fragment-only link against the authored Markdown file containing it. That file does not own the generated cross-surface anchor. The fragment is valid in the generated CONTRACT.md, but that does not make the original source link valid. The patch neither weakens this checker nor introduces a renderer link special case.

## Source support and expected rendering

The existing identity surface owns Shared definitions → Reply (00-identity.surface.md:335,455–467), giving the exact ID identity.definitions.reply. The tree validator resolves uses through the indexed nodes (_validate around tree.py:952–960). Existing diagnostics.issue.subject is another definition using this same structured relation form.

The existing renderer visits definitions through `_facts_text` (visit around tree.py:1366–1373); that function emits Uses plus `_link(tree.index[x])` for uses (1203–1205), without restricting it to rule nodes. `_link` and `_anchor` (1059–1064) derive `Uses [Reply](#contract-identity-definitions-reply).` in the generated document. That sentence is the expected output based on source reading; this agent has not regenerated or executed the renderer. The definition and table retain the exact operational meaning; the existing reference is represented as a resolved authoring dependency.

## Follow-up reading and validation limits

This is a source-level repair review after the final stage-three presentation change, not a new isolated reader pass. Freshly read: the failing receipt/log excerpt; authored families definition/table; shared Reply definition; current generated families passage; validator reference handling; `_facts_text` uses emission; visit/_link/_anchor; and the cross-document checker plus its owning test entry. The already supplied reader/journal/follow-up artifacts were not revised or treated as verification of this new postimage. No isolated reader was contacted.

Only private before/after files and this patch/report/manifest are written. No shared edits, generator/model imports, generation, tests, builds or product execution. Static checks establish exact preimage identity, one intended source replacement, valid literal reference syntax and unchanged neighboring text. Private patch applicability is checked separately. The earlier limits-control patch/report/manifest remain byte-for-byte frozen and their hashes are included here.

Adoption is parent-owned after the frozen sequence ends: verify the preimage hash, apply this authored patch, regenerate through the owner, review that the generated families section contains Uses Reply and no stale source-fragment sentence, then run the full source_drift selection. The earlier build_contracts pass did not establish the failed cross-document link property. No fresh pass or overall workflow acceptance is claimed by this candidate.

# Replay register — B1

Predictions in this first version precede execution. Exact git object IDs,
input hashes and verdicts are retained in later results. All open cases and
their expectations are known to the designer from the owning plan and the
51487f7 audit. These are development cases, not independent validation.
Historical facts are `git show REV:PATH` / `git log` over committed trees.

| ID / class | Claim sites and finder | Revisions / predicted result and reason | Supplied annotation |
| --- | --- | --- | --- |
| A-missing / identifying evidence absent | WORKER L; WA-05, 51487f7 initial-report | 51487f7: evidence-missing; WORKER credits L but receipt path absent | Register L as current-support-requested, with named expected receipt; no nonexistent provenance supplied. |
| A-current / negative for A-missing and A-change | WORKER L and receipt, correction69c7dfe | 69c7dfe: represented-inputs-current; seven file hashes and worker identity equal | Hypothetical adoption review at this tree; grant is an explicit assumption. |
| A-change / mode2 represented changes | Same claim/receipt; owning plan's later review | f468200: review-required; same receipt, different worker identity and3 file hashes | Same adopted relationship; no later review supplied. Does not say L is false. |
| P-change / mode3 represented claim changes | WORKER whole-document claim input; D1 designer selecting known rewrite | 69c7dfe vs11fddc4: review-required for changed claim input; baseline69c7dfe is paired negative | Hypothetical registration hashes the whole claim document; conservative scope deliberately includes generated text. No allegation rewrite is wrong. |
| B / out-of-scope unconnected contradiction | Makefile header vs BUILD/lock helpers; owning plan's fixed history | 46fe43e,b410ac3,d46ccd6,99cf137: excluded at all4. Interior trees contain contradiction, endpoints lack it; no universal truth pass | None. No subject registry, semantic opposition annotation, or future Apple facts. |
| S2 / mode5 nonasserting check | architecture worker row s2 and bare_deny_default/harness; audit WA-02 | 51487f7: unreviewed semantic support, not behavioral agreement. Paired repaired attribution69c7dfe remains pointer presence absent review | No assertion classification manufactured by checker. Audit supplies evaluation target only. |
| S9 / modes2/4 wrong existing source | architecture W24 ExtensionSession, W30 issuer main; audit WA-09 | 51487f7: pointer presence passes despite wrong source;69c7dfe repaired citation also passes. Semantic mismatch excluded | None; auditor's attribution is not retroactively a recorded review. |
| S6 / wrong source rendered faithfully | architecture worker s9/s29/s31a/s32/s36b; audit WA-06 | 51487f7 and69c7dfe: excluded semantic correctness; manifest-to-render identity can hold on both wrong and corrected content | None. No correction semantics inferred from generation. |
| S11 / omitted fact | WORKER sysctl_read and worker C buffer; audit WA-11 | 51487f7: omitted4096-byte bound outside registration; f699758 correction: still outside B1 until explicitly registered | None. Omission cannot be found by an index of existing citations alone. |

The explicit tree predicates/output snippets are extracted by
`replay/open.py`; output lives in `replay/open-results.json`. The script models
the proposed decisions using tree inputs, not a production implementation.
It never executes historical build/test commands or writes historical trees.
For source citation examples it reports actual cited symbols and existence;
semantic classification remains attributed to the historical audit.

Churn prediction: e04ec96,2b0be8e,16e2f83,146e7d2,cb8a110 each changes worker
identity relative to parent, so five review events. No automatic native rerun.
Compare launch-path differences outside generated identity regions/comments;
only cb8a110 removes a non-arm64 spin branch. Build changes still need review
even when launch-file source lines are unchanged. Cost disposition follows
evaluation and will distinguish review from fresh observation.

Open results and their self-review are in `replay/open-results.json` and
`open-review.md`, frozen with B1 at `db75edf`. The sealed concrete held-back
register is `replay/heldback-cases.json`, committed before evaluation at
`152f984`; `heldback-predictions.md` records post-reveal exposure and B1-specific
predictions. Results and coverage are in `replay/heldback-results.json` and
`heldback-review.md`. H06 is explicitly delayed; no excluded semantic class
is counted as a clean evidence pass.

# B1 open replay review

Predictions: commit `689cb49`. Evaluation: `replay/open.py`, run with the
repository Python wrapper; 19 revision/case results in `replay/open-results.json`.
Reviewer: D1 executor, self-review. No design changes were needed or silently
made after evaluation. Results are conditional paper-contract exercises,
not evidence of a deployed detector.

| Case | Observed tree fact | B1 result / prediction assessment |
| --- | --- | --- |
| A-missing | 51487f7 has no receipt; worker identity e1c88f81… | evidence-missing, as predicted. No original app or raw-run inference. |
| A-current | 69c7dfe receipt identity4cb19db0… and all7 source hashes match | represented-inputs-current, conditional on explicit supplied adoption review. Paired negative works; it is not proof of current conditions. |
| A-change | f468200 retains identical receipt; worker identity0da3a70a… and3 source hashes differ | review-required for the stated represented changes, as predicted. |
| P-change | whole registered WORKER input changes from69c7dfe to11fddc4 | review-required; baseline negative unchanged. Conservatism visible: a beneficial rewrite triggers review too. |
| B | Same Makefile interpreter claim in first3 trees; BUILD/helpers describe shim in interior trees; final Makefile corrected | excluded at all4, as predicted. This neither calls endpoints true nor pretends to detect interior contradiction. |
| S9 | W24/W30 wrong citations exist in51487f7; corrected69c7dfe citations also exist | Pointer presence cannot choose correct attribution. Exclusion predicts both; no false semantic credit. |
| S2 | s2 cites substitute harness in51487f7;69c7dfe names lifecycle and descriptor controls with scope | Definitions alone remain unreviewed for claimed support. Auditor's classification is attributed, not reproduced by an existence test. |
| S6 | Historical rows contain audit-pass history; corrected rows change source data | Semantic source-data correctness excluded even when rendering is faithful. |
| S11 | Historical source has buffer while account omits bound; f699758 introduces disclosure and limit | Excluded until a relationship is deliberately selected. A reverse index cannot discover an absent statement. |

Historical finder for S2/S6/S9/S11 and missing-provenance A is the auditor
whose first-person record is committed at51487f7; no personal identity is
inferred from that artifact. The B and later-A targets were supplied by the
owning plan; P-change is a D1-authored change-detection contrast. These cases
were all exposed before design and provide no independent validation.

## Churn and disposition work

All5 named commits change the worker identity relative to their parent.
Predicted/replayed review count is5/5. The cumulative diff69c7dfe..cb8a110
over the four launch-path files contains only generated identities and the
six removed non-arm64 cpu_relax lines. Exact identities and changed-path
lists are in the result JSON. This supports conservative identity use with
human dispositions; it does not support ignoring all build changes.

| Event | Review facts and proposed resolution for current reuse | Further observation cost |
| --- | --- | --- |
| e04ec96 | Adds explicit thin-arm64 output targeting/flags and build provenance. Launch-file text unchanged; compiled target may change. Review build/app conditions, not merely source paths. | If current reuse is required with only tree evidence, new launch observation or matching build/condition evidence is needed. Historical census remains intact. |
| 2b0be8e | Parenthesizes two Swift map closures in dispositionIntegrityProblems. Launch paths and receipt observer unchanged. | A reviewer may grant source-scoped reuse with unchanged native conditions; no new observation caused by this delta alone. |
| 16e2f83 | Direct Python start and caller environment preservation replace shim/restoration in build helpers. Compiler/SDK environment can differ without launch-source change. | Review actual build context; if unavailable and current reuse required, obtain new observation. Source diff alone does not grant current native applicability. |
| 146e7d2 | build.sh change is explanatory lock comment; identity changes anyway. | Record comment-only review; no new native observation for this delta. |
| cb8a110 | Native-builder admission, Meson diagnostic and removal of non-arm64 cpu_relax branches; supported arm64 instruction unchanged. | Review supported-target restriction and conditions; code-scoped reuse is reasonable without new observation for this delta. |

Thus there are five initial review actions, three source-scoped no-new-observation
dispositions, and two needing build/condition evidence before current reuse.
There are zero automatic reruns and no event that can silently take "no action"
while counting current support. With only the replay's trees, at most two new
native observations would settle those two outstanding current-reuse requests;
not doing current reuse requires neither. This is a design cost estimate, not
observed human effort or a historical claim that those reviews happened.
Previously reviewed unchanged inputs incur no repeated review; any new source
or condition delta requires another attributable decision.

B1 is ready to freeze for the withheld cases. New registration/control machinery
is still only proposed. F1 remains outside this design's semantic detection
claim and pending user disposition; it is not repaired by calling a census a check.

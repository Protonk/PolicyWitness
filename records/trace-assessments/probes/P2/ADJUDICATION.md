# P2 adjudication: spec-only oracle

**Run.** Workflow `wf_6cabb03c-a2f`, 2026-11-20, at `2bcdfeb8`. Four readers
ran as `Explore` agents: three Sonnet and one Opus control. Every reader
reported opening only `inputs/`. One Sonnet reader also listed the harness's
saved copy of its own large read, which is not another source. Raw answers
are in `answers.json`. Expectations are in `KEY.md`.

## Agreement with the key

| Input | Result |
| --- | --- |
| S1-I1 | 4/4 associate with no issue. Order is left open because the setup gives no chain facts, which is fair. |
| S1-I2 | 4/4: `missing_id` (count 0), `unexpected_id` (count 1), order `unestablished`. |
| S1-I3 | 4/4 infer `query_mismatch` and `unestablished`. 4/4 note that the excerpt never says when `query_mismatch` is emitted. |
| S1-I4 | 4/4 "not decided": the excerpt holds association rules only, and request-name uniqueness is stated in the request surface. The excerpt boundary explains it; no action. |
| S1 outcome and exit | 4/4 "not decided": the `validator_unavailable` consequence lies outside the association subject. Excerpt boundary; no action. |
| S2-I1, I3, I4, I5 | 4/4 correct on record and flag. All say correctly that the excerpt does not decide compiler evaluation. |
| S2-I2 (`[import …]`) | 4/4 "not decided": the excerpt speaks of lists and never says square brackets form one. |
| S3-I1, I2, I3, I5 | 4/4 correct. |
| S3-I4 | 4/4 identify the tool error. 4/4 say the excerpt does not decide whether a runner client starts. |
| S4-I4 | 4/4 correct. |
| S4-I1 to I3 | Opus and one Sonnet reader derived 1,007 and 1,006 exactly. The other two hedged on whether the marker's room counts inside the 1,023-byte allowance. |

## Leads and verdicts

**L1, Pass 4 entry.** `query_mismatch` has no stated condition. The
lifecycle surface names it only in the value list and the count rule.
`validatorAssociationIssues` (`PWRunnerPredictionEvidence.swift:182-191`)
emits it, with count 1, for the uniquely associated record when:

- a prediction record (`allow` or `deny`) does not carry the submitted
  operation, filter type and filter value with identical bytes; or
- a diagnostic record carries any of those fields with different bytes. A
  diagnostic record may omit them.

The record is then not associated. A reader who sees this issue in output
cannot tell what it means. Correct the owner: the `association_issues` or
validator query association subject in `32-lifecycle.surface.md`.

**L2, Pass 4 entry.** List delimiters are unstated. The scanner treats `(`
`)` and `[` `]` as list delimiters (`sbpl_lex.rs:93`, `:125-126`), so
`[import "…"]` is recorded and followed. The policy surface's import
inventory says only "lists". A policy author cannot tell whether bracketed
forms are covered. Correct the owner: the literal import inventory subject in
`11-policy.surface.md`. The `cli_contract.rs` rows ("square brackets",
"braces") give the evidence.

**L3, Pass 4 entry.** A registry refusal in `run` happens before any client
starts. `run_flow.rs` resolves the runner (`:694`) and returns `tool_error`
on a selection error (`~:772`) before the client call (`:790`). The read rule
says only that the refusal is "that run's tool error". Readers could not
tell whether an external runner was contacted. Correct the owner: "Read and
select records" in `50-installation.surface.md`. CONTROLLER-A executed this
path.

**W1, weak, no action.** The 1,023-byte allowance with the reserved marker
room. Two of three Sonnet readers hedged on whether the marker's room lies
inside the allowance; the Opus control and the third Sonnet reader derived
1,007 from the text. A single-model hesitation that the control did not
share counts as weak under the plan.

## Destinations

- Pass 4 entries: L1, L2 and L3.
- User-duty draft: none.
- Guide-rewrite note: none.

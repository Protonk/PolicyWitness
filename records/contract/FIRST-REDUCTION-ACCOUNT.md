# First contract reduction

The prepared `v0.3.8` contract at `b83b2e2e` had 5,831 lines and 77,418
words. This intervention at the pre-tag review boundary leaves 5,482 lines
and 73,314 words: 349 lines and 4,104 words fewer. It changes the generator's
presentation and the authored account. Product source, shape goldens, the
guide body and the free-relationship counts are unchanged. The stage accounts
and their rehearsals describe the document as it stood before this change.

Exact repeated sentences accounted for about 1,500 words of the baseline and
near-repeats for about 2,000; the three derived views held under two percent.
The reduction therefore came from restated propositions found by reading. Six
delegated readings of the whole generated document supplied candidates and
the coordinator decided each one.

## Cuts

| Cut | Class | Generated effect | Where the meaning remains |
| --- | --- | --- | --- |
| Derived views identify a rule and its reach | Presentation only | 190 lines, 950 words | The findings index names the record members each check reads and links each consequence with its entry, trigger or case and the targets it sets, withholds, retains or prevents. Applicability lists rules under each acting-component set. A subordinate row follows its parent row. Operand paths, values and consequence prose stay at the linked rule. |
| Stage-two evidence definitions folded into support | Authored | 11 definition nodes | Each restated a neighboring rule or field and described its evidence. Its owner now supports the rule, field, example or subject concerned, and each sentence or clause stated nowhere else moved there. The seven accepted-limit definitions and the definitions carrying their own behavior stay. |
| One home for a restated proposition | Authored | 147 entries, about 2,370 words | A subject paragraph, field cell or row sentence repeated its governing rule, structured row or definition. The rule or row keeps the statement. |
| Two variant stubs and one duplicate structured row | Authored | 3 nodes | The generated alternatives table links both variant records. `request.specimen.capacity.phase_actions` states the whole-specimen action bound for every phased request. |
| Generic context on source-read support | Evidence metadata | 14 owners, about 110 words | The source-read grade definition. Every specific context and every evidence limit stays. |

`evidence/first-reduction/` lists each removed sentence with its node and
retained statement, each removed node with its former text and the present
home of its support, and the six readings.

## Canonical content and stamps

The presentation step left all nineteen surface hashes identical. The
authored steps changed 148 nodes in prose only, removed 14 nodes and added
none; 2,926 words left canonical public prose. Eighteen surfaces changed
through their own content and `envelope` through incorporated shared content.
Every surface already carried the prospective `v0.3.8` stamp, so both stamp
tables read as before. All 145 support paragraphs remain. Each field meaning,
obligation, applicability, refusal order, effect, evidence limit and Known
gap can still be established from the same or a linked node.

## Verification

Checks ran on the reduced tree with stamps regenerated as `unreleased`, so
ordinary history checking applied.

- Strict tree loading and `--check --require-history` pass.
- Canonical payloads and surface hashes were compared at the baseline, after
  the presentation step and at the result. No node changed outside the cut
  list, and no surviving node changed in anything except prose.
- Each listed removal is absent from its node and each retained statement is
  present at its named node. All 386 internal link targets resolve. The 14
  removed anchors have no live inbound link.
- Six presentation controls now assert the reduced views: record members
  read, linked consequences with entry, trigger or case, their reach, and that
  operand paths, values and consequence prose remain at the linked rows.
- `source_drift`, run `20261112T002531Z_b89d61d1`: 10 of 10 cases passed on
  the first reduced source.
- Two reviewers who had not seen the cut list compared `d18d4925` with
  `b83b2e2e` sentence by sentence against the reduced document. They found no
  lost proposition and seven weakened or dangling statements. All seven were
  corrected: two sentences and one definition with its owner were restored,
  the request introduction and the empty-plan sentence were restored, one
  moved sentence regained its subject, one paragraph regained its antecedent,
  and the legacy-registry owner moved to the field naming the retired aliases.
- `source_drift` on the corrected source, run `20261112T010714Z_59d45ccf`:
  10 of 10 cases passed.

Signed development build 1341 came from clean commit `d18d4925`, with the
unchanged development contract `84448fb4…` and worker identity `52bbda61…`,
and its staged guide equal to the source guide. Default battery
`20261112T003820Z_c2a4ab04` on that build completed all 229 cases with zero
recorded sleep and a valid, unchanged app: 228 passed and
`witness_contract/response_footprint` failed. Its retained
`terminal-inspection.json` shows a final process sample that straddled the
controller's exit: the identity read succeeded and the re-read 14 µs later
returned ESRCH. The measurement harness accepts only a fully absent sample
as terminal, and its controls reject the mixed form, so it refused the
sample. The cause is that harness boundary; no product observation or
contract text is involved. The whole run remains failed. The rehearsal of the
corrected source follows this commit and is recorded at preparation.

Corrections made while working: the first application of the sentence
removals split paragraphs where a removal emptied whole lines, so the sources
were restored and the removals reapplied with paragraph-preserving joins; two
retained-statement locations in the working list named field nodes that do
not exist and now name `steps.attempt_paths.realpath_resolved` and
`parent_realpath_resolved`, where the statements were already present.

Limits. Each cut rests on the contract's own retained statement; no product
source was read to decide one. The readings were single delegated passes with
mechanically checked quotes. No isolated reader has read the reduced
document. Some hard-wrapped paragraphs now have uneven line lengths; their
rendered text is unaffected.

## Declined, with what each needs

| Candidate | Size | Why it stays |
| --- | --- | --- |
| Ordinary and per-actor projection families; ordinary and actor disposition bounds | about 1,350 words | Reply-wide findings overwrite the ordinary outputs and leave actor outputs; assigned actions differ. One statement needs a scope parameter. |
| Paired with-errno and without-errno aggregate cases | about 350 words | Needs a conditional value. |
| Variant and reference identity row families; repeated helper-admission effects | about 500 words | Needs an expression over the selected variant, or a rule-level effect beside first-match cases. |
| Generic pins and check-read context | about 620 words | The owner schema requires both. |
| Pins and context in rendered support | about 3,400 words | Presentation only, but pins state which assertions a check supports. |
| Per-rule entry, recipient and report | about 370 words | The readable rule keeps its complete context by an earlier decision. |
| Admission-order rule in diagnostics; request-side termination stub; success-with-findings statements | about 280 words | They carry refusal precedence or touch the reserved R-20 and R-37 choices. |
| Value lists repeated by the vocabulary tail; one unfamiliar-value sentence on eight fields | about 370 words | Field meanings and per-field `unknown` are required; the edits are clause rewrites. |
| Helper and dossier import walks | about 110 words | Two producers with different bounds, status and record shapes. |

## Noticed and left unchanged

- `refusals.controller.code` displays `admission_refused`; a source search
  found no controller capacity refusal. Not verified further.
- The validator support limit calls duplicate-key behavior source-read while
  `wire.validator.duplicate_keys` carries a check-read owner.
- `transport.delivery.acquire` and `transport.acquisition.outcome` list
  different retry causes: only the second names an RPC timeout.
- The lifecycle projection rules cover steps; `lifecycle.attempt` says a
  step or extension event carries the projection.
- The removed `termination_cause` sentence was inexact for `no_worker`; the
  rules and the retained field text are exact.

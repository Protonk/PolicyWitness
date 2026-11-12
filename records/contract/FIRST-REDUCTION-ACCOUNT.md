# First contract reduction

The prepared `v0.3.8` contract at `b83b2e2e` had 5,831 lines and 77,418
words. This intervention at the pre-tag review boundary leaves 5,472 lines
and 73,178 words: 359 lines and 4,240 words fewer. It changes the generator's
presentation and the authored account. Product source, shape goldens, the
guide body and the free-relationship counts are unchanged. The stage accounts
and their rehearsals describe the document as it stood before this change.

## Where the size was

Exact repeated sentences accounted for about 1,500 words and near-repeats for
about 2,000. Field rows hold a third of the document, rule paragraphs and
condition rows half, support paragraphs a tenth and the three derived views
under two percent. The reduction therefore came from restated propositions
found by reading, with six delegated readings of the whole generated document
supplying candidates and the coordinator deciding each one.

## Cuts

| Cut | Class | Effect on the generated document | Where the meaning remains |
| --- | --- | --- | --- |
| Derived views identify a rule and its reach | Presentation only | 190 lines, 950 words | The findings index names the record members each check reads and links each consequence with its entry, trigger or case and the targets it sets, withholds, retains or prevents. Applicability lists rules under each acting-component set. A subordinate row follows its parent row. Operand paths, values and consequence prose stay at the linked rule. |
| Stage-two evidence definitions folded into support | Authored | 12 definition nodes | Each restated a neighboring rule or field and described its evidence. Its owner now supports the rule, field, example or subject concerned. Each sentence or clause stated nowhere else moved to that home. The seven accepted-limit (L) definitions and the definitions carrying their own behavior stay. |
| One home for a restated proposition | Authored | 148 entries, about 2,450 words | A subject paragraph, field cell or row sentence that repeated its governing rule, structured row or definition. The rule or row keeps the statement. |
| Two variant stubs and one duplicate structured row | Authored | 3 nodes | The generated alternatives table links both variant records. `request.specimen.capacity.phase_actions` states the whole-specimen action bound for every phased request. |
| Generic context on source-read support | Evidence metadata | 14 owners, about 110 words | The source-read grade definition. Every specific context and every evidence limit stays. |

The package under `evidence/first-reduction/` lists each removed sentence
with its node and the retained statement, each removed node with its former
text and the present home of its support, and the six readings with the
candidates they marked distinct.

## Canonical content and stamps

The presentation step left all nineteen surface hashes identical. The
authored steps changed 149 nodes in prose only, removed 15 nodes and added
none; 3,057 words left canonical public prose. Eighteen surfaces changed
through their own content and `envelope` through incorporated shared content.
Every surface already carried the prospective `v0.3.8` stamp, so both stamp
tables are unchanged. All 145 support paragraphs remain. A reader can still
establish each field meaning, obligation, applicability, refusal order,
effect, evidence limit and Known gap from the same or a linked node.

## Verification

Checks ran on the reduced tree with stamps regenerated as `unreleased`, so
ordinary history checking applied. The prepared `v0.3.8` tables follow the
rehearsal.

- Strict tree loading and `--check --require-history` pass.
- Canonical payloads and surface hashes were compared at the baseline, after
  the presentation step and at the result. No node changed outside the cut
  list, and no surviving node changed in anything except prose.
- Each listed removal is absent from its node and each retained statement is
  present at its named node. All 386 internal link targets resolve. The 15
  removed anchors have no inbound link in the repository.
- Seven presentation controls now assert the reduced views: record members
  read, linked consequences with entry, trigger or case, their reach, and that
  operand paths, values and consequence prose remain at the linked rows. The
  40 tree controls pass in a local run.
- `source_drift`, run `20261112T002531Z_b89d61d1`: 10 of 10 cases passed with
  no skipped or unrun case, no harness error and zero recorded sleep. It is an
  offline selection; its artifact-integrity field is null.

Two corrections were made while working. The first application of the
sentence removals split paragraphs where a removal emptied whole lines; the
sources were restored and the removals reapplied with paragraph-preserving
joins. Two retained-statement locations in the working list named field nodes
that do not exist; they now name `steps.attempt_paths.realpath_resolved` and
`parent_realpath_resolved`, where the statements were already present.

The signed development build and pre-tag rehearsal of this reduced source
follow its commit and are recorded here when complete.

Limits. Each cut rests on the contract's own retained statement; no product
source was read to decide one. The readings were single delegated passes over
the generated text, with quotes checked mechanically. No isolated reader has
read the reduced document. Some hard-wrapped paragraphs now have uneven line
lengths; their rendered text is unaffected.

## Declined, with what each needs

| Candidate | Size | Why it stays |
| --- | --- | --- |
| Ordinary and per-actor projection families; ordinary and actor disposition bounds | about 1,350 words | Reply-wide findings overwrite the ordinary outputs and leave actor outputs; assigned actions differ. One statement needs a scope parameter the tree lacks. |
| Paired with-errno and without-errno aggregate cases | about 350 words | Needs a conditional value. |
| Variant and reference identity row families; repeated helper-admission effects | about 500 words | Needs an expression over the selected variant or a rule-level effect with first-match cases. |
| Generic pins and check-read context | about 620 words | The owner schema requires both. An authoring-rule decision. |
| Pins and context in rendered support | about 3,400 words | Presentation only, but pins state which assertions a check supports. A decision about public evidence presentation. |
| Per-rule entry, recipient and report | about 370 words | The readable rule keeps its complete context by an earlier decision. |
| Admission-order rule in diagnostics; request-side termination stub; success-with-findings statements | about 280 words | They touch refusal precedence or the reserved R-20 and R-37 choices. |
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

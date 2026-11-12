# Second contract reduction

Baseline: clean, prepared but untagged `6f65612b`. The first reduction's
corrected development battery and refusal rehearsal had passed; the ordinary
stamp check refused exactly the absent `v0.3.8` tag. This work keeps that
pre-tag boundary and the same prospective release.

## Result and accounting

| Material | Before | After |
| --- | ---: | ---: |
| Main contract, whitespace-counted Markdown words | 73,314 | 63,816 |
| Main contract, visible words through the repository CommonMark reader | 61,976 | 57,175 |
| Main contract, lines | 5,482 | 5,227 |
| Main contract, UTF-8 bytes | 725,572 | 706,584 |
| Authored surface files, words / bytes | 63,146 / 629,372 | unchanged |
| Authored non-field prose / field meanings, words | 13,323 / 14,397 | unchanged |
| Additional generated references | none | none |

The Markdown contraction is 9,498 words (13.0%), over twice the first pass's
4,104. That is not 9,498 words of removed contractual prose: visible words
fall by 4,801 (7.7%), and bytes by 18,988 (2.6%). Long exact paths, anchors,
citations and necessary meanings still dominate byte size. Counts use `split()`;
visible counts concatenate the reader's inline text and code blocks without
Markdown scaffolding or link destinations. `evidence/second-reduction/measurements.json`
records the baseline, intermediate renderings and final hashes.

Two transformations account for the change:

- The 1,004 fields become record-local list entries with bold names, compact
  type/presence signatures and full-width meanings. Removing 158 repeated
  field-table headers eliminates 948 visible heading words. The remaining
  4,750-word saving in this step is Markdown scaffolding. Every field anchor,
  meaning, vocabulary, special omission rule and subordinate obligation stays.
- Existing checked expressions retain their function names, full operands,
  grouping and lists instead of expanding into English phrases. Field
  signatures distinguish required keys, omission and null; unusual input and
  serialization rules stay explicit. These changes compact 4,400 counted
  words. The reading key and its entrance add 600 Markdown words, 547 visible.

No contractual proposition was eliminated and no information moved to another
artifact. Neither transformation changes the authoring language. A field's
suffix applies to its whole value, including a collection. Binding domains,
association restrictions, quantifiers, first-match order, refusal policy,
effect triggers and scopes remain explicit. Rule tables remain tables.

## Preservation and review

The initial notation trial compared the actor termination gate with compiled
profile receipts. The gate retained positional association, quantified phases,
prepared-reply applicability, prerequisite and scheduling order, unreached versus
failed evaluation, and later cleanup observations. Receipts retained decoded
byte extents, host capture conditions, controller label admission, the absent
controller request-nonce operand, and separate run/verification consequences.
The field-list trial also examined run-envelope null/omission and completion
behavior. Fields remain beside the rules to which their prose refers.

Independent review is retained in `evidence/second-reduction/REVIEW.md`. It
compared the baseline and result, including ordinary versus actor projection,
reply-wide withholding, helper refusal order and all exceptional presence
families. A new legend phrase, “when available,” could have implied emission
of a known but withheld value; its corrected wording describes representation
only. Exhaustive mechanical comparisons preserve all 1,004 field meanings,
145 byte-identical support paragraphs, original anchor ordering, 20 first-match
tables, 64 condition/effect tables, four variant tables, 16 examples and seven
gaps. The parser recognizes 1,004 separate field list items. Direct semantic
reading was selected, not a new uninterrupted reading of every unchanged
paragraph, and supplies no new native execution credit.

All nineteen canonical public payloads and surface hashes are identical to
`6f65612b`. Authored surfaces, `public.json`, shape goldens, free-relationship
counts, history readers, guide and both stamp tables are byte-identical.
The generator's presentation and controls change; product source does not.
The existing unresolved behavioral choices remain unresolved.

## Declined representations

A companion field reference shortened the main preview to about 40,500 words
by moving about 31,300 words. Combined size fell only modestly in words and
grew in bytes. It improved the behavior sequence but introduced cross-page
lookup and left “below” references requiring authored repair. That benefit did
not justify the overhead for this reduction. Local path abbreviations saved
only about 9 KB for 34 new mappings across 19 rules; full operand paths remain.

Rule contexts and evidence were inspected as possible contributors. The 127
rules contain about 2,500 context words but 110 distinct component, boundary,
entry, recipient and report combinations;
sharing them risks hiding different recipients or entry points. The 145 support
blocks contain about 8,200 words, chiefly distinct assertions and limitations.
They remain adjacent to their owners. Field vocabularies retain openness,
exhaustiveness and unfamiliar-value meaning separately. No generic grade label
replaces a supported assertion or limitation.

## Verification and pre-tag boundary

The selection was `tests/run.sh --suite source_drift --case
preflight/build_entry_controls --case preflight/release_publish_controls`,
with a fresh `PW_TEST_OUT_DIR` for each run.

| Run | Result |
| --- | --- |
| `20261112T145451Z_9099fa62` | 11 of 12 passed. Build-entry controls failed when sandboxed `sysctl` queries refused the native-builder observations before the intended guards. This remains a failed whole run, with its `suite_exit` harness error. |
| `20261112T150401Z_58ea9f44` | The unchanged selection passed all 12 outside the automation sandbox, including all ten source-drift cases. No harness errors. |

Both runs are terminal with zero skips, unrun cases or recorded sleep. These
are offline selections and inspected no app. The source-drift cases include
generator ownership/idempotence, links, shape joins, authoring/rejection controls,
retained history readers, Markdown parsing and unchanged build/worker identities.
`evidence/second-reduction/verification.json` retains the commands, source hashes,
case accounting and applicability checks. Raw development evidence is local and
gitignored under `/private/tmp/pw-contract-second-verification-20261112/tests/out/runs/`;
it remains subject to ordinary retention, without a pin.

The isolated worktree
uses `8435e5d3`'s pre-preparation history and the exact revised generator,
documentation and controls. Every contract-generator input matches this
checkout except the three prospective stamp artifacts: contract, guide and
public snapshot. This lets ordinary strict history checks run without creating
a `v0.3.8` tag or altering this checkout's prepared state. Prospective rendering
in this checkout separately verifies those artifacts.

Prospective rendering is exact and shape recollection agrees. The ordinary
strict check gives precisely `release history unavailable; restore annotated
release tags: v0.3.8`, the expected pre-tag refusal. No baseline exception was
added. The prepared contract's SHA-256 is
`4d8e40e1d7a4fba1df60b8f12a7d28fdebd1bd80ad08564af83db2eca6e304d7`.

The earlier native battery and extracted-ZIP rehearsal remain observations of
their recorded sources and builds. This change affects documentation rendering
and its checks; it changes no product, wire shape, build identity input, worker
identity input, wait/release/eligibility path or guide workflow. The affected
source-drift and build/release-document controls are rerun. It does not require
another native battery or order-barrier mutation run. These are reviewed
applicability judgments, not claims that earlier runs executed the new renderer.
All 105 selected build inputs and 56 worker-identity inputs were compared with
`8435e5d3` and are byte-identical. The entry point, history/runtime, copier,
build gates and shipped guide are unchanged; the changed renderer path has new
generator and early-gate credit. The earlier full signed/refusal/ZIP rehearsals
retain their unchanged orchestration, artifact and native-behavior scope, not
current-tree whole-rehearsal credit.

The final checkout remains prepared for `v0.3.8`. Maintainer review, the existing
tagged rehearsal, real Apple submission and publication remain ahead. The
prospective release has not been tagged, submitted or published.

# Second coalescing cycle: the comparison record

This cycle follows [DOC-COALESCING-PLAN](../../docs/DOC-COALESCING-PLAN.md)
through passes 1 to 4 for one topic, starting from `bfa65341`.

## Topic, scope and reader questions

The topic is the per-step comparison record, `steps[].comparison`: its six
fields, the phase ordering observations that `order` rests on and the reading
rules. Extension lifecycle actions, path diagnostics, the attempt-outcome
catalog and reporting degradation stay outside it.

1. A step shows a `deny` query answer beside a successful attempt. What does
   the record establish, and what else is needed before claiming that
   prediction and enforcement disagree?
2. A step has `comparison.order: unestablished`. Which requirement was missing,
   and what can still be used from that step?
3. An attempt is classified `permission_failure`. What does the classification
   rest on, and can the failure be attributed to the sandbox?

## Pass 1 — Ownership

The guide is staged with the app and cannot link into the developer contract,
so an envelope reader answers these questions from the guide alone. The
contract and the test contract serve developers and test authors.

| Question | Concept | Authoritative account | Other presentations | Checks | Reading problem | Treatment |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | The record relates two channels and states no agreement verdict | `steps.comparison` fields, `steps.assessment.relations`, `identity` prediction definition | Test contract "The record"; two FAQ answers; guide field entry; reading rules 4 to 10 | `ComparisonEvidenceTests` over the scenario matrix; `witness_contract/comparison_matrix` live | The guide's reading section opens on fourteen flat rules and never says that no field states agreement. The FAQ answer that poses the question has no link. A reader must assemble the qualifying fields from six rules. | Open the guide section with the record's claim limit and a reading path for this case. Link the FAQ answer. Keep the rules as the complete account. |
| 2 | Requirements for `query_first` | `steps.assessment.order`: collection chain, setup, native answer, unique association | Guide `comparison.order` and `phases[].ordering` entries, rule 1, ordered phases; test contract record table and ordering-states table; ARCHITECTURE; WORKER | `OrderingTests`; `witness_contract/order_barrier_mutations` | The guide says "eligible native records" without defining eligibility or naming the fields that show which requirement failed. The test contract's `order` row says "after successful application", omitting an unapplied actor's declared setup that the contract and source accept. The contract's field entry says nothing that leads to its rule. | Add a guide account of the four requirements with the fields to inspect and what an unestablished step still supplies. Correct the test contract's row and point it to the contract rule. Reference the rule from the contract field. |
| 3 | `observation` and `observation_basis` classify the native result's shape | `steps.assessment.observe`, a first-match rule | Guide field entry, per-step outcome notes, rule 3, FAQ answer; test contract record table | `ComparisonEvidenceTests`; matrix rows S02, S03, S13, S14, S16, S17 | The guide names the basis values without the fields each rests on, and does not show that one classification arises from different causes. The FAQ answer has no link. The contract's field entry says "the rule below", about 150 lines away, without a reference. | Add a guide account of each basis and of the evidence attribution needs. Link the FAQ answer. Reference the rule from the contract field. |
| 1, 2, 3 | Reading rules | Shared block in the test contract, copied into the guide | Matrix controls cite rules 3, 6, 7 and 10 by number | `source_drift/limits_documentation` | The list serves as a complete reference; it is hard to enter from one observed step. | Retain the text and its owner. Guide-authored orientation precedes it without citing rule numbers. |
| 1, 2, 3 | Worked scenarios | `tests/fixtures/comparison/matrix.json`, rendered in the test contract | None in the guide | Unit reader over every row; live reader for specimen S rows | The guide has no concrete record. Rows S02 and S03 carry identical comparison values under a policy denial and a mode-0000 file; S05 shows a `deny` beside a success for a different target. | Pass 3: extract a few rows from the fixture into the guide through the existing generator. |
| 2, 3 | Support for the order and classification rules | Owners in the `steps` surface | Evidence support appendix | Contract tree checks | The order rule shows only source-read support; its check-read owner sits under the following definition. The classification rule shows no local support; the owner whose assertion includes classification is attached to the relations definition. | Pass 4: place each owner beside the claim its assertion covers. |

The requirements were read in `eligibleOrderedStep`, `eligibleOrderedPrediction`,
`PWRunnerOrdering.chainEstablished`, `buildStepResults` and
`validateForReporting`; classification and relations in `comparisonEvidence`.
The contract's rules match that source. No behavioral evidence is claimed.

### Ownership questions retained

- The reading rules are an interpretation aid that the plan's allocation places
  with the guide, yet their one text lives in the test contract and matrix
  controls cite them by number. This cycle leaves that owner in place.
- The test contract's record table restates the contract's field meanings in
  its own words. This cycle corrects and links its `order` row. The other rows
  remain a second maintained description.

### Adjacent opportunities for a later cycle

- ARCHITECTURE, WORKER and the runner README send readers to the test contract
  for order eligibility; the contract rule is the owner.
- The `limitations` vocabulary is listed in the contract, the test contract,
  the guide and the fixture.
- The guide's `steps[].comparison` field entry repeats the contract's
  attempt-to-operation map in prose.
- The contract's temporal-meaning definition omits the interval statement that
  the identity surface and the guide carry.
- The attempt-outcome catalog, path diagnostics and extension rules 13 and 14.

## Pass 2 — Consolidated explanations

The guide's reading section now opens by stating what the record relates and
that no reply field states agreement. Three subsections start from an observed
step: an answer that differs from the attempt, an unestablished order and a
permission failure. Each names the fields to read and what a conclusion still
needs. The copied rules follow under their own heading as the complete account,
and the `jq` recipes keep their commands under a heading of their own. The
`comparison.order` field entry names the four requirements in place of
"eligible native records", and three FAQ answers link to the subsection that
answers them.

The test contract's `order` row now includes an unapplied actor's declared
setup, the absence of protocol violations and the reported worker, and links to
the contract rule. Its introduction names the contract as the owner of the
field meanings.

In the `steps` surface, five comparison fields gain a `uses` reference to the
rule or definition that sets them, so the rendered field list links to
"Classify an observation", "Submitted operation and target" and "Establish
query order". No prose, field shape, support owner or free-text relationship
changed.

Public snapshot review: the five field nodes each gain one `uses` fact. The
`reply`, `envelope` and `installation` surfaces, which already inherit those
fields, each gain the same 18 shared nodes: the `steps.assessment` subject and
its order, classification and relations nodes. A later change to one of those
rules will therefore also mark these three surfaces changed, which matches the
fields' dependence on them. History and the free-text baseline are unchanged,
and every surface is currently unreleased.

The guide's new subsections restate the contract's order and classification
rules for a reader who cannot follow a link into the contract. That adds one
alignment duty between the guide and `steps.assessment`; no check binds them.

## Pass 3 — Examples from their owner

The guide had no concrete comparison record, and the scenario fixture already
owns reviewed expectations with independent controls. `docs/generate_limits.py`
now copies six fixture rows into the guide under "Recorded scenarios": S02 and
S03 for a permission failure under two causes, S05 and S06 for an answer and an
attempt that concern different things, and S07 and S11 for an unestablished
order. The rows use the renderer that produces the test contract's table,
without the specimen column. The guide authors only the short description of
the fixture's files and three notes on what the rows show.

The expectations and controls stay separately authored in the fixture. The unit
reader checks every row through the producer and the live matrix case checks
the specimen S rows against the app; this pass ran neither and credits no
execution. No guide command changed, and the pass adds no app interface.

New machinery: one marker pair in the guide, a row selection constant, a
shared table renderer, guide validation of the copied rows, a region
registration and drift controls for a stale copy, a missing marker, a hidden
block and a selected row absent from the fixture. New duty: the three authored
notes must keep describing the selected rows. No maintained copy was removed;
the pass avoided adding hand-written example records to the guide.

The test contract's literal example record remains hand-written and equals
row S01's expectation. Rendering it from the fixture is left for later.

## Pass 4 — Support beside its claim

Two owners in the `steps` surface now sit beside the claims their assertions
cover. Support metadata is outside the public snapshot, which this pass leaves
unchanged.

- The check-read ordering owner moved from the temporal-meaning definition to
  "Establish query order". Its assertion concerns the rule's requirements:
  `OrderingTests` removes each chain link and applies each record defect in
  turn. The rule now shows its source-read association owner and this
  check-read owner together. The definition states evidentiary limits and
  keeps the surface's source-read owner.
- "Classify an observation" gains a check-read owner citing `comparisonEvidence`
  and `ComparisonEvidenceTests`. The producer's branch order was read against
  the rule's six cases, and the table-driven reader asserts observation and
  basis for every matrix row. The relations owner's assertion no longer lists
  classification, which its attached scope never covered.

Both owners keep their limits: source and check reading, constructed inputs
and no execution credit. No owners were merged; the classification and
relations owners cite the same source and check for different assertions and
scopes. The rendered anchor `contract-steps-assessment-meaning-support` is
replaced by `contract-steps-assessment-order-support`; nothing in the
repository linked to the old one.

## Consultation

One Opus consultation, read-only and without further delegation, answered one
question: does the guide's new comparison text claim more than the contract
rules and producer source establish? It read the guide subsections, the FAQ
changes, the `steps` surface, the producer, validator and worker sources and
the fixture with its live reader. It found no explicit sandbox-cause or
agreement claim and reported ten imprecise or overreaching statements and four
doubts. All were applied. The consequential ones: a `deny` answer had been
called a prediction without the `query_first` condition; the scenarios' last
column had been called an independent observation although some entries state
policy text; `different_submitted` and `matched` had been glossed as facts
about targets and operations when they compare submitted strings and
PolicyWitness's own mapping; and an `open_read` success had been described as
a read. The consultation is source inspection and supplies no execution
evidence.

## Verification

Generator regeneration, `generate_contract_stamps.py --tree-check` and
`--check --require-history`, and `generate_limits.py --check` passed after each
pass. One suite run then covered the whole cycle from clean `1f5e358c`:

```sh
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 \
  PW_TEST_OUT_DIR=tests/out/runs/doc-coalescing-comparison PW_TEST_QUIET=1 \
  tests/run.sh --suite source_drift
```

Run `20261113T181345Z_0be84511` completed in 398,792 ms in an unsandboxed
shell with Python 3.14.9. All ten cases passed, with no skips, unrun cases,
harness errors or recorded system sleep. `limits_documentation` ran 24 tests,
including the new scenario-copy test and the extended stale-copy control.
These are generator and documentation observations. No runtime code, request
or guide command changed, so no build, native case or guide-workflow case was
added, and no support grade rose.

One disposable run and no worktree were created. After receipt review,
`make prune` preview and `make prune APPLY=1` removed that run without
blockers and kept the four release archives and protected acceptance. Its raw
output is no longer available locally. The staged `dist/PolicyWitness.md`
still equals the guide at `bfa65341`; the next signed build restages it.

## Completion

1. **A `deny` beside a success.** The FAQ answer now begins "No" and links to
   "When the answer and the attempt differ". That subsection lists five fields
   to check, states what the record establishes when all five permit the
   comparison, and names what a conclusion still needs: runtime object
   identity, unchanged state, the attempt's effect and a failure's cause.
   Rows S05 and S06 show the relation fields ruling a comparison out. Before,
   the reader assembled this from rules 1, 4 to 10 and a field entry. Still
   difficult: no published row shows a real `deny` beside a success with every
   field permitting the comparison, because the fixture's only such row uses
   the test validator; and the guide cannot say how to establish runtime
   identity for the query, since no reply field records it.
2. **`order: unestablished`.** The field entry and FAQ link to a table of the
   four requirements, the fields that show each and why each can be unmet,
   followed by what the step still supplies. Rows S07 and S11 show two
   reasons. Before, the guide said "eligible native records" and left the
   requirements to the developer contract. Still difficult: the setup and
   record requirements span three parts of the reply, and the guide's table
   restates a contract rule without a check binding the two.
3. **`permission_failure`.** The FAQ answer links to a table of each
   observation and basis with the fields it rests on, the statement that
   neither the classification nor a `deny` beside it identifies the cause,
   and examples of separating evidence. Rows S02 and S03 carry identical
   records under different conditions. Still difficult: attribution remains
   the reader's experiment; the guide offers examples and no procedure.

Contract readers reach the three rules from the comparison field list, and the
order and classification rules show their check-read support locally.

Removed: the test contract's incorrect setup wording, and the misattached
support scope for classification. No maintained copy was deleted this cycle.
Added duties: the guide's order and classification tables against
`steps.assessment`, and the three scenario notes against the selected rows.
Added machinery: the scenario copy and its controls, and one support owner.
Preserved distinctions: prediction versus raw native return, submitted
strings versus runtime objects, order versus state, classification versus
cause, and source inspection versus constructed checks versus native evidence.

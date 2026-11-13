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

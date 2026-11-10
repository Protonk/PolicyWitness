# Contract staging plan

This outline fixes the boundaries between four stages of work on the public
contract, [CONTRACT.md](CONTRACT.md), and on the implementation and guide it
describes. It says what belongs in each stage and what does not. It is not
the plan for any one stage; a stage may get its own plan or may not.

The examination that led here is in `records/contract/`. Its
[plan](../records/contract/CONTRACT-CONTACT-PLAN.md) describes the reading
and inventory work, and its
[ledger](../records/contract/CONTRACT-LEDGER.md) holds the strain register
this outline draws on. Register rows are cited below as `R-nn`.

## The stages

| Stage | What it does | Changes product behavior | Ends with |
| --- | --- | --- | --- |
| One | Restructures the contract so that it is a complete and truthful account of the implementation as it is, including the parts we do not want | No | A release |
| Two | Changes the implementation where the stage one contract could not state a rule simply | Yes | Every known gap removed or confirmed as intended |
| Three | Settles the contract on the changed implementation | No | A release |
| Four | Edits the user guide heavily, without restructuring it, to agree with the settled contract | No | A guide that explains the contract it ships beside |

The order carries the method. Writing the contract truthfully against the
current implementation is what finds the places worth changing: wherever the
true sentence needs a case split or an awkward qualification. Stage two then
has a list made by stage one, and stage three is a revision of a sound
structure, not a second rewrite.

## Terms

- **Rule.** One requirement the contract states: something a component
  checks, produces or refuses.
- **Particulars.** The four things a rule owes its reader: who acts, what is
  compared with what, at which boundary, and with what consequence. A rule
  whose particulars cannot be given is not yet stated.
- **Known gap.** A paragraph that says what is true now about behavior that
  is expected to change. The architecture, build and worker documents
  already use this form, with an index.
- **Surface.** A named part of the contract with its own stamp in the
  surface table.
- **Claim row.** A record tying one rule in the contract to the source that
  implements it and the check that would fail if it were false.

## Rules that hold across all stages

- **The contract is true at every commit.** It describes the implementation
  at that commit. Where the truth is awkward, it is stated in a Known gap
  paragraph, not left out.
- **Surface names are fixed at the end of stage one.** A surface that
  existed at a release and later disappears keeps a removal row in the
  surface table permanently. Stage one ends in a release, so later stages
  change what a surface contains and leave its name alone.
- **The guide stays out of the surfaces' definitions** from stage one on.
- **A disagreement between contract and implementation is never settled by
  assumption.** Which side changes is decided by the maintainer, on the
  evidence for each side.
- **A definition settles a family of cases.** Disputes about validity are
  resolved by stating what a record means and where the rule applies, not
  case by case and not by picking the strictest implementation.
- **Evidence is graded.** A claim rests on a run, a check that was read, or
  source that was read, and its row says which. Agreement among generated
  artifacts, or among implementations, is not correctness.

## Stage one: restructure against the current implementation

**Aim.** A developer can establish which contract applies and find what it
commits to, from this document alone, and every rule in it is true of the
implementation as it stands.

**Belongs in this stage.**

- *Shape.* The document opens with the reader's route: how a specimen or a
  received artifact identifies its contract, and where that contract's
  commitments are. Its body is organized as definitions of what the records
  mean, applicability of each rule to the kinds of reply (ordinary,
  preparation failure, reporting failure), and obligations: what each
  component checks and what it does on failure.
- *Surfaces.* The surfaces are redrawn to fit that shape. This is required,
  not permitted: fitting the new document into the old surfaces would turn
  the stage into a puzzle. The names chosen here are final.
- *Self-containment.* The guide's regions leave the surfaces' definitions.
  What each surface contains is rendered in the contract; reading the
  manifest is not a prerequisite for knowing what the document covers.
- *Particulars, in prose.* Every rule states its four particulars in
  sentences. Structured forms wait for stage three.
- *Removals.* Sentences that deny or recall a former mechanism, and
  instructions addressed to maintainers inside normative text, are removed
  or moved. The maintainer has already directed three removals (`R-23`,
  `R-30`, `R-31`).
- *Known gaps.* Each behavior stage two is expected to change is stated as
  it is now, in a Known gap paragraph. The candidates are listed under
  stage two.
- *Machinery, by reuse only.* One new section in the existing surface
  manifest holding claim rows at the level of the rule: an identifier, the
  rule's kind, the reply kinds it applies to, its sources, its checks, and
  a known-gap flag. The existing citation checks applied to those rows.
  Markers in the prose tying each passage to its row, with a check that
  markers and rows correspond one to one. A named owning check for each
  example. The existing Known gap index check extended to this document.
  The stamp generator following the new surfaces.
- *Owners.* A row's source and check are read by whoever records them. A
  rule with no check either gets one or is carried as a known gap. Adding
  a test that gives a true rule an owner belongs here; `R-06` is one.
- *Text-only strains.* Register rows whose strain sits in the text are
  resolved by the restructure.
- *Minimal guide corrections.* A guide sentence that contradicts the
  contract is corrected when found. Nothing else in the guide changes.

**Does not belong in this stage.**

- Any change to what the product does: validation, outcomes, field names or
  values. Comment corrections and added tests are allowed; behavior is not.
- Rules encoded as data, a corpus run across the validators, or rendering of
  definitions from rows. These would encode the implementation we intend to
  change.
- New generators, new output formats or new kinds of check.
- Careful prose for a passage that stands under a Known gap. It gets the
  minimal true statement.

**Guard against overbuilding.** If the new manifest section, the markers and
their checks were deleted, the contract's prose would be unchanged.

**Hands to stage two.** The list of Known gaps, and the list of rules whose
particulars needed a case split to state.

**Exit.** Every passage has a row; every row is owned or is a known gap;
the generators' checks and the drift suite pass; the change has been
reviewed against the register; an isolated reader has read the new document
and the result has been compared with the baseline reading; a release has
been cut, with the Known gap paragraphs in it.

## Stage two: change what is hard to state

**Aim.** Remove the reasons the stage one contract needed a Known gap or a
case split.

**Gate.** Each change names the contract rule it makes simpler and says
what that rule will read afterward. A change that serves no rule does not
belong to this stage.

**Belongs in this stage.**

- *Decisions first.* For each candidate the maintainer decides whether the
  implementation changes or the behavior is intended and stays. Where
  validators disagree, the definitions and scopes are settled before any
  implementation is chosen (`R-36`, and the draft of
  [disputed meanings and scopes](../records/contract/validators/DEFINITIONS-AND-SCOPES.md)).
- *Changes to shipped source*, each made and verified under the
  repository's ordinary rules and able to land on its own.
- *Checks for the rules as decided*, including, once the definitions exist,
  a corpus of constructed replies run through every validator.
- *The contract kept true.* A change replaces its own Known gap paragraph
  with a plain statement of the new behavior, in the same commit. Nothing
  else in the contract moves.

**Candidates known now.** Each is a candidate, not a commitment to change.

- Whether success reflects the controller's findings about the evidence
  (`R-20`).
- What a reporting-failure reply promises and which requirements still
  apply to it (`R-36`).
- The definitions the validators disagree on: what a preparation failure
  is, which replies may carry one, what an identifier is, absent against
  empty, and an actor's visits (`R-14`, `R-36`).
- The words for withheld conclusions and the scope of withholding (`R-07`,
  `R-34`).
- What the stamp check certifies without release history, and regeneration
  for a release without it (`R-29`).
- Rules implemented by hand more than once (`R-15`).
- Rules with no owning check that stage one could only carry as gaps.

**Does not belong in this stage.**

- Reorganizing the contract.
- Editing the guide, beyond correcting a sentence a change has made false.
- Renaming a surface.

**Exit.** Every Known gap from stage one has been removed by a change or
confirmed by the maintainer as intended, and each decision is recorded.

## Stage three: settle the contract

**Aim.** The contract reads as an account of this implementation, with no
trace of having first been written for another.

**Belongs in this stage.**

- *Revision.* Passages that carried a Known gap or a case split are
  rewritten with care. A gap confirmed as intended becomes an ordinary
  statement.
- *Structure for the particulars.* The four particulars move from prose
  into tables, trees or another structure, wherever that makes a rule
  easier to find and compare.
- *Rules as data, where it earns its place.* Applicability and obligations
  may move into the manifest, and parts of the document may be rendered
  from rows. Each such step is weighed as new machinery.
- *Checks that depend on settled rules*, such as naming the cross-validator
  corpus as an owner.
- *Reading.* An isolated reader reads the settled document, and the result
  is compared with the stage one reading.

**Does not belong in this stage.**

- Changes to product behavior. A strain found while settling goes back to
  stage two as a named item and is decided there.
- New surface names.
- The guide.

**Exit.** No Known gap remains that the maintainer has not confirmed as
intended; every row is owned; the checks pass; a release has been cut.

## Stage four: edit the guide

**Aim.** The guide agrees with the settled contract and explains it in
terms of public fields and observable behavior.

**Why last.** The guide explains the contract. Edited earlier, it would be
edited again after each of the stages before it.

**Belongs in this stage.**

- A heavy edit of the guide's text against the settled contract, section by
  section, including its field vocabularies (`R-35`) and its account of a
  run's result (`R-33`).
- The guide's shared content, edited at its sources and regenerated as the
  [documentation guidance](AGENTS.md) requires.

**Does not belong in this stage.**

- Restructuring the guide. Its sections stay where they are.
- Changes to the contract or the product. A disagreement found here goes
  back to the stage that owns it.

**Exit.** Each guide section has been read against the contract; the
checks pass.

## Decisions still open

- **The new surfaces and their names.** Needed at the start of stage one.
- **Whether the consolidation drafted for `R-33` is within a heavy edit.**
  The [draft](../records/contract/GUIDE-RESULT-ACCOUNT-DRAFT.md) moves
  three passages of the guide next to one another. That may count as
  restructuring.
- **Whether stage four ends in a release.** The guide ships beside the
  release.
- **For each stage two candidate, whether the implementation changes.**
  Made within stage two, definitions first.

## What the examination supplies, and its limits

- A claim inventory covering every line of the present contract, with a
  literal account of the mechanism behind each sentence. It follows the old
  sentences, so stage one regroups it into rule-level rows. Its rows are
  readings by delegated passes; nothing in it was run, and a share of its
  rows have a source but no check, more than one answer, or no owner.
- A strain register with the maintainer's close readings and decisions.
- A baseline reading of the present contract by a reader given nothing
  else, for comparison with later readings.
- An observed account of where the three validators' judgments differ, with
  the test code that produced it.

Stage one has to raise the grade of what it restates. A contract bound to
the current implementation is only as good as what is known of that
implementation.

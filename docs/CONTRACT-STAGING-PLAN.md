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
- **Node.** One item of the contract's source: a surface, a subject, a
  definition, a field, a rule, a condition, an outcome, an effect, a known
  gap or an example. The contract is a tree of nodes.
- **Owner.** The source that implements a rule and the check that would
  fail if the rule were false, recorded beneath the node they support.
- **Free-text item.** A condition, dependency or effect written as a
  sentence and not yet as an expression.

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
- **The contract binds PolicyWitness.** Every rule's subject is one of its
  components. Accepted input is stated as what PolicyWitness accepts and
  what it refuses, and a limit on what an output establishes is stated as a
  limit on its commitment, not as a duty of the person reading the output.
- **Meaning lives in the contract.** A field's meaning, the significance of
  its absence and what its values support are in the contract. The guide
  explains how to use those commitments.
- **Production and interpretation are stated apart.** Where PolicyWitness
  produces a record is one commitment. What it checks whenever that record
  is present is another, and does not depend on what the current producer
  emits.
- **Evidence is graded.** A claim rests on a run, a check that was read, or
  source that was read, and its owner says which. Agreement among generated
  artifacts, or among implementations, is not correctness.

## The contract's source and generator

`docs/CONTRACT.md` is generated. Its source lives in `docs/contract/`,
which also holds the generator and the guidance for maintaining both. The
model is built in stage one and firmed up in stage three.

**One hierarchy.** The contract is a tree, authored as Markdown, one file
for each surface. A heading is a node, with a type and an identifier taken
from its path. There is no separate manifest whose structure has to be
kept in step with the document's.

**The tree's shape carries the relationships.** A relationship that is
subsidiary to another is written beneath it, not added as one more
attribute on every item.

| A node of type | Holds |
| --- | --- |
| surface | subjects: a record, an input, or a part of an operation |
| subject | definitions, fields and rules |
| rule | its conditions, its outcomes and its effect |
| effect | what it prevents or withholds, and what it leaves standing |
| any of these | a known gap, an example, or an owner |

What is stated on a node holds for the nodes beneath it unless they say
otherwise. Who acts, at which boundary, and which kinds of report a rule
applies to are each stated once, at the level they belong to.

A rule is one of three kinds: a component acts, reports or checks. The
kinds and the node types are a working set, adjusted as drafting gives
reason.

**Structured facts sit under their node, beside its prose.** They are a few
keyed lines in a constrained form. A sketch, not a syntax:

```
### The host activates only through a satisfied gate   {gate.activation: acts}
who: runner host        where: execution
requires: report.phases[p].termination_gate.outcome = satisfied

When a gate is not satisfied the host does not activate the phase...

#### Otherwise   {effect}
cancels: every later phase in the schedule
leaves: records reported before the gate
```

**Four relationships have a defined expression**, written the same way
wherever they occur: a reference to an object, as a path into a defined
record; a condition, as an object, a relation from a closed list, and an
object or a literal; a dependency, as an assertion or action and the
conditions it requires; and an effect, as a component, a verb from a closed
list, an object, and what the effect prevents and leaves.

**The generator assembles the document.** It parses the source with the
repository's Markdown reader, passes prose through, and renders each node's
structured facts in one uniform form. It builds field tables by joining the
record definitions with each field node's authored meaning. It derives the
views that would otherwise be written by hand: the surface table, which
rules apply to which kind of report, an index of the controller's findings
with what each reads and leaves, and the index of known gaps. It computes a
surface's stamp from that surface's source and its goldens.

**Sanding down is a ratchet.** Any item may begin as free text and later
become an expression. The generator counts free-text items by kind in a
baseline that may shrink and may not grow, as the prose baseline already
does for other documents. As items firm up, derived views take the place of
prose summaries, and prose that only restated them is removed.

**Checks the tree makes cheap.** Nodes nest legally. Identifiers are
unique and references resolve. An object path written as an expression
exists in the record definitions. Every public field has a field node.
Every owner's source and check exist. Every example has an owner. The
generated document is current.

**What the generator does not do.** It evaluates no condition, compares no
implementations and decides no validity. It parses, assembles, derives
views and checks references. There is one generator, built on the
repository's shared generator code.

## Stage one: restructure against the current implementation

**Aim.** A developer can establish which contract applies and find what it
commits to, from this document alone, and every rule in it is true of the
implementation as it stands.

**Belongs in this stage.**

- *Shape.* The document opens with the contract identity: how a specimen or
  a received artifact identifies its contract. Definitions of the
  components, boundaries, artifacts and kinds of report follow, and do the
  orienting; nothing explains how to read the document. The body is
  organized by public operation, including runner management, and within
  an operation by accepted input, the acting component's account, and the
  controller's assessment. The controller's findings name the host
  assertions they bear on.
- *Surfaces.* The surfaces are redrawn to fit that shape. This is required,
  not permitted: fitting the new document into the old surfaces would turn
  the stage into a puzzle. The names chosen here are final.
- *Self-containment.* The guide's regions leave the surfaces' definitions.
  What each surface contains is rendered in the contract; nobody has to
  open its source to know what the document covers.
- *Particulars, in sentences, as separate parts.* Every rule states who
  acts, where, when it applies, each condition as its own identified item,
  and the consequence. The parts are fixed in stage one so that stage three
  can hold the same content as data without rewriting it. A rule is not
  written as one paragraph that runs its conditions together.
- *Maintenance leaves the document.* The contract has no section on its own
  upkeep. `docs/contract/` gets a description of its contents and working
  rules for changing and regenerating them.
- *Removals.* Sentences that deny or recall a former mechanism, and
  instructions addressed to maintainers inside normative text, are removed
  or moved. The maintainer has already directed three removals (`R-23`,
  `R-30`, `R-31`).
- *Known gaps.* Each behavior stage two is expected to change is stated as
  it is now, in a Known gap paragraph. The candidates are listed under
  stage two.
- *The source tree and its generator*, as described above: the tree, the
  node types and their nesting, structured facts beside prose, the
  generator with its derived views and its checks, and the first baseline
  of free-text items. The existing stamp generator and surface manifest
  are replaced or moved as the tree requires; the build's accounts of them
  change with them.
- *Owners.* An owner's source and check are read by whoever records them.
  A rule with no check either gets one or carries a known gap. Adding a
  test that gives a true rule an owner belongs here; `R-06` is one.
- *Text-only strains.* Register rows whose strain sits in the text are
  resolved by the restructure.
- *Minimal guide corrections.* A guide sentence that contradicts the
  contract is corrected when found. Nothing else in the guide changes.

**Does not belong in this stage.**

- Any change to what the product does: validation, outcomes, field names or
  values. Comment corrections and added tests are allowed; behavior is not.
- Rule semantics in the generator, or a corpus run across the validators.
  These would encode the implementation we intend to change.
- Turning every item into an expression. An item may stay free text and be
  counted; the baseline is driven down in stage three.
- A second generator, or a second hierarchy beside the tree.
- Careful prose for a passage that stands under a Known gap. It gets the
  minimal true statement.

**Guard against overbuilding.** The structure has to do work. A structured
fact is added to a node only when it feeds a check or a derived view, or
replaces a sentence. An attribute that would be filled in on every node
for uniformity's sake is a sign that it belongs on a parent, or nowhere.

**First steps, in order.**

1. A spike, outside the repository's tracked files, on the two sections
   already worked through in the
   [structure proposal](../records/contract/CONTRACT-STRUCTURE-PROPOSAL.md):
   the compiled-profile receipt and the termination gate. It settles
   whether the source reads well to an author, whether the output reads
   like the worked sections, and how much of a constrained form the parser
   needs.
2. The list of what the generator must guarantee by the end of this stage,
   each written as a check that fails.
3. An inventory of everything that refers to the present stamp generator,
   surface manifest and region markers: the build script, the build and
   architecture accounts, the drift suite, release preflight and the build
   identity's scope.
4. The generator and the tree's skeleton, with every surface present and
   empty.
5. The surfaces, drafted one at a time against the claim inventory and the
   register.

**Hands to stage two.** The list of Known gaps, and the list of rules whose
particulars needed a case split to state.

**Exit.** Every rule has an owner or carries a known gap; every public
field has a field node; the baseline of free-text items is recorded; the
generator's checks and the drift suite pass; the change has been
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
- How far a failed termination dependency reaches: the dependent phase, or
  the rest of the schedule (`R-37`).
- Whether a finding of the controller's names the assertion it concerns
  (`R-38`).
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
- *Firming up.* Free-text items become expressions until the definitions,
  applicability and obligations are held as structured facts in the tree.
  That is the machine-readable representation of the finished contract.
  Derived views take over from the prose summaries they make redundant.
- *More from the generator, where it earns its place.* A further derived
  view or check is weighed as new machinery.
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
intended; every rule is owned; the definitions, applicability and
obligations are structured facts, with any free-text item that remains
accepted by the maintainer; the checks pass; a release has been cut.

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

- **The surface names, before the stage one release.** The structure
  proposal's surfaces are the working set. The names become permanent at
  that release, so they are confirmed then.
- **What the surface table means once a surface is stamped from its source
  in the tree.**
- **What an ordinary build requires of the contract's check** (`R-29`).
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
  sentences, so stage one regroups it under the tree's rules. Its rows are
  readings by delegated passes; nothing in it was run, and a share of its
  rows have a source but no check, more than one answer, or no owner.
- A strain register with the maintainer's close readings and decisions.
- A [structure proposal](../records/contract/CONTRACT-STRUCTURE-PROPOSAL.md)
  with the document's table of contents, its surfaces, the model of a rule,
  and two sections worked through in that model.
- A baseline reading of the present contract by a reader given nothing
  else, for comparison with later readings.
- An observed account of where the three validators' judgments differ, with
  the test code that produced it.

Stage one has to raise the grade of what it restates. A contract bound to
the current implementation is only as good as what is known of that
implementation.

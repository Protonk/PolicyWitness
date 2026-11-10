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
| Two | Resolves behavioral gaps against the intended public commitments | Where a change is decided | Every known gap resolved, including evidence gaps |
| Three | Settles the contract on the changed implementation | No | A release |
| Four | Edits and locally consolidates the guide to agree with the settled contract | No | A guide that explains the contract it ships beside |

The order carries the method. Writing the contract truthfully against the
current implementation exposes commitments that need review. An awkward
qualification is a reason to investigate, not proof of a defect: a case split
may express a necessary distinction. Stage two draws on those findings and
the intended public meanings. Stage three settles the account of the resulting
behavior.

## Terms

- **Rule.** One public commitment about an action, a produced record or an
  assessment. Its responsible component, applicability and consequences
  are explicit.
- **Particulars.** Who owes the behavior, when and where it applies, what
  operation or relationship is required, and the scope of its effects.
  Comparisons identify their operands. A rule whose particulars cannot be
  given is not yet stated.
- **Known gap.** A labelled unresolved item. A behavioral gap states current
  behavior whose intended commitment needs a decision. An evidence gap
  states what has not been established or tested. Missing evidence does not
  itself imply that the product should change; an unverified behavior is
  not presented as an established commitment. Each gap identifies its kind.
- **Surface.** A named part of the contract with its own stamp in the
  surface table.
- **Node.** One item of the contract's source: a surface, a subject, a
  definition, a field, a rule, a condition, an outcome, an effect, a known
  gap or an example. The contract is a tree of nodes.
- **Owner.** Supporting source and a named check, with the assertion that
  check makes, its limits and its evidence grade, recorded beneath the
  supported node. A cited check need not cover every part of the rule.
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
- **The contract binds PolicyWitness.** Every rule has a responsible
  component and identifies the records or actions it governs. Accepted input
  is stated as what PolicyWitness accepts and refuses, and a limit on what
  an output establishes is stated as a
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

Stage one will make `docs/CONTRACT.md` a generated document, authored under
`docs/contract/` beside its generator and maintenance guidance. Currently
only the stamp table is generated; the directory and full-document generator
have not been built. The model is built in stage one and firmed up in stage
three.

**One hierarchy.** The contract is a tree, authored as Markdown, one file
for each surface. A heading is a node, with a type and an identifier taken
from its path. There is no separate manifest whose structure has to be
kept in step with the document's.

**The tree's shape carries the relationships.** A relationship that is
subsidiary to another is written beneath it, not added as one more
attribute on every item. Nesting expresses ownership. Dependencies across
subjects or surfaces use explicit references, without duplicating the
referenced definition under each dependent rule.

| A node of type | Holds |
| --- | --- |
| surface | subjects: a record, an input, or a part of an operation |
| subject | definitions, fields and rules |
| rule | its conditions, its outcomes and its effect |
| effect | what it prevents or withholds, and what it leaves standing |
| any of these | a known gap, an example, or an owner |

Shared context may be stated on a parent. The spike defines which properties
inherit, how an override works and how the effective value is rendered. An
example or evidence citation does not become an obligation through nesting.
Applicability combines run state, admission state and record presence as the
rule requires; a parent default must not silently widen a child's reach.

A rule is one of three kinds: a component acts, reports or checks. The
kinds and the node types are a working set, adjusted as drafting gives
reason.

**Structured facts sit under their node, beside its prose.** They are a few
keyed lines in a constrained form. A sketch, not a syntax:

```
### The host activates only through a satisfied gate   {gate.activation: acts}
who: runner host        where: execution
when: a reached gate has been evaluated
requires: report.phases[p].termination_gate.outcome = satisfied

When a gate is not satisfied the host does not activate the phase...

#### Otherwise   {effect}
cancels: every later phase in the schedule
leaves: records reported before the gate
```

**Four relationships need defined expressions:** references to defined
records, fields, actions and events; conditions on them; dependencies; and
effects with their scope. The proposal's relations and verbs are a working
vocabulary. The spike must express presence tests, comparisons, conjunctions
and conditional requirements, including bound actor and phase references.
Failure effects distinguish retained records from assessments that remain
supported. Unsupported expressions stay explicitly free text; placing prose
under a key does not make its relationships machine-readable.

**The generator assembles the document.** It parses the source with the
repository's Markdown reader, passes prose through, and renders each node's
structured facts in one uniform form. It builds field tables by joining the
record definitions with each field node's authored meaning. It derives the
views that would otherwise be written by hand: the surface table, which
rules apply to which kind of report, an index of the controller's findings
with what each reads and leaves, and the index of known gaps.

**Stamps track public content and shapes.** A surface's hash covers its
public content, including definitions, commitments, examples and shared
public content it incorporates, and its canonical shape goldens. Source/test citations,
evidence grades and maintenance-only metadata are checked separately and do
not change a public stamp on their own. The tree identifies which content
belongs to each surface; hashing the whole authoring file would violate this
boundary. Migration preserves the existing release-history and removal-row
account rather than silently treating old surfaces as newly introduced.

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
  and the consequence. Representative relationships are structured in stage
  one; the model remains revisable when another commitment exposes a missing
  distinction. Stage three need not preserve an inadequate template.
- *Maintenance leaves the document.* The contract has no section on its own
  upkeep. `docs/contract/` gets a description of its contents and working
  rules for changing and regenerating them.
- *Removals.* Sentences that deny or recall a former mechanism, and
  instructions addressed to maintainers inside normative text, are removed
  or moved. The maintainer has already directed three removals (`R-23`,
  `R-30`, `R-31`).
- *Known gaps.* Current behavior under review and limits of the supporting
  evidence are recorded with their respective gap kinds. The behavioral
  candidates are listed under stage two.
- *The source tree and its generator*, as described above: the tree, the
  node types and their nesting, structured facts beside prose, the
  generator with its derived views and its checks, and the first baseline
  of free-text items. The existing stamp generator and surface manifest
  are replaced or moved as the tree requires; the build's accounts of them
  change with them.
- *Owners.* An owner's source and check are read by whoever records them.
  An untested part of a rule gets a meaningful check or an evidence gap.
  Adding a test that gives a true rule an owner belongs here; `R-06` is one.
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

**Hands to stage two.** The known gaps with their kinds and supporting
evidence, and the definitions or commitments each proposed change affects.

**Exit.** Every rule has an owner or carries a known gap; every public
field has a field node; the baseline of free-text items is recorded; the
generator's checks and the drift suite pass; the change has been
reviewed against the register; an isolated reader has read the new document
and the result has been compared with the baseline reading; a release has
been cut, with the Known gap paragraphs in it.

## Stage two: resolve the gaps

**Aim.** Resolve the behavioral decisions and establish missing evidence.
Necessary distinctions remain explicit even when they require case splits.

**Gate.** Each change names the public commitment it establishes or repairs,
explains why that behavior is intended, and states the resulting rule.
Simpler prose alone does not justify changing behavior.

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

**Exit.** Behavioral gaps have been resolved by a change or a decision to
retain the behavior. Evidence gaps have the missing support or an explicit
maintainer decision accepting the stated limitation. Calling behavior intended
does not supply missing evidence. Each disposition is recorded.

## Stage three: settle the contract

**Aim.** The contract reads as an account of this implementation, with no
trace of having first been written for another.

**Belongs in this stage.**

- *Revision.* Passages that carried a Known gap or a case split are
  rewritten with care. Behavior confirmed as intended becomes an ordinary
  statement; an accepted evidence limitation remains identified as such.
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

**Exit.** Every behavioral gap has a recorded disposition and every evidence
gap is closed or has an explicitly accepted limitation; every rule has
graded support or that evidence limitation; the definitions, applicability and
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
- Local consolidation to make related explanations contiguous, including
  the result account already requested for `R-33` and drafted in
  [the result-account proposal](../records/contract/GUIDE-RESULT-ACCOUNT-DRAFT.md).
  Existing anchors are preserved or their callers updated.
- The guide's shared content, edited at its sources and regenerated as the
  [documentation guidance](AGENTS.md) requires.

**Does not belong in this stage.**

- A wholesale redesign of the guide's organization. Local moves needed for
  a complete explanation belong in this stage.
- Changes to the contract or the product. A disagreement found here goes
  back to the stage that owns it.

**Exit.** Each guide section has been read against the contract; the
checks pass.

## Decisions still open

- **The surface names, before the stage one release.** The structure
  proposal's surfaces are the working set. The names become permanent at
  that release, so they are confirmed then.
- **What an ordinary build requires of the contract's check** (`R-29`).
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

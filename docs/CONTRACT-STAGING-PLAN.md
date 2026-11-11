# Contract staging plan

This outline fixes the boundaries between four stages of work on the public
contract, [CONTRACT.md](CONTRACT.md), and on the implementation and guide it
describes. It says what belongs in each stage and what does not, who carries
the stages out and who decides what. It is not the plan for any one stage; a
stage may get its own plan or may not.

The examination that led here is in `records/contract/`. Its
[plan](../records/contract/CONTRACT-CONTACT-PLAN.md) describes the reading
and inventory work, and its
[ledger](../records/contract/CONTRACT-LEDGER.md) holds the strain register
this outline draws on. Register rows are cited below as `R-nn`. The ledger
is also the working record of the stages: where the work stands, what has
been decided and what waits for the maintainer.

Stage-one execution records: the
[coverage map](../records/contract/CONTRACT-COVERAGE-MAP.md),
[authoring trial](../records/contract/CONTRACT-SPIKE-RESULT.md),
[migration inventory](../records/contract/CONTRACT-MIGRATION-INVENTORY.md) and
[generator guarantees](../records/contract/CONTRACT-GENERATOR-GUARANTEES.md).
The [stage-one reading journal](../records/contract/readings/stage-one/JOURNAL.md),
[unprompted adjudication](../records/contract/readings/stage-one/UNPROMPTED-ADJUDICATION.md),
[prompted adjudication](../records/contract/readings/stage-one/PROMPTED-ADJUDICATION.md)
and [targeted revision reading](../records/contract/readings/stage-one/REVISION-READING.md)
retain the frozen-input reading separately from subsequent truth corrections.

Stage-two records: the [decisions](../records/contract/STAGE-TWO-DECISIONS.md)
and [scoped evidence](../records/contract/evidence/stage-two/README.md) retain
the implementation dispositions, observed controls and remaining choices.

Stage-three records: the [settled account](../records/contract/STAGE-THREE-ACCOUNT.md),
[frozen readings](../records/contract/readings/stage-three/README.md) and
[verification receipts](../records/contract/evidence/stage-three/README.md) retain
the final representation, truth corrections and scoped checks.

## The stages

| Stage | What it does | Changes product behavior | Ends with |
| --- | --- | --- | --- |
| One | Restructures the contract so that it is a complete and truthful account of the implementation as it is, including the parts we do not want | No | An unpublished `v0.3.7` release |
| Two | Resolves behavioral gaps against the intended public commitments | Where a change is decided | Every known gap resolved, including evidence gaps |
| Three | Settles the contract on the changed implementation | No | A settled contract ready for the guide work |
| Four | Settles the guide's explanations and user workflows against the contract | No | The complete `v0.3.8` release, ready for publication after the full plan |

The order carries the method. Writing the contract truthfully against the
current implementation exposes commitments that need review. An awkward
qualification is a reason to investigate, not proof of a defect: a case split
may express a necessary distinction. Stage two draws on those findings and
the intended public meanings. Stage three settles the account of the resulting
behavior.

**Release checkpoints and publication.** The releases deliberately exercise
the complete build, acceptance, packaging, guide staging and version-locking
arrangement, so disagreements between those parts are found in practice.
Follow the [release procedure](SIGNING.md#release-procedure) through tagging
and archival at the end of stage one and again at the end of stage four.
Keep the tags and release assets unpublished until all four stages are complete;
publication is a separate step from creating these releases.
[The release checkpoints](#the-release-checkpoints) says who runs them and
what a failed attempt is for.

The sequence is the existing `v0.3.6`, the stage-one `v0.3.7`, and the completed
`v0.3.8`. Preserve each version's contract and shape snapshot in release history.
The next published contract is the completed `v0.3.8`, with that three-version
history available, including the intermediate tag. Each checkpoint stages the
guide belonging to its own build; the final release includes the settled guide.
A change the maintainer directs after the final archive exists reopens the
stage that owns it, and the completed release takes the next number.

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
  not presented as an established commitment. An unresolved meaning records
  a promise whose scope cannot yet be stated. Preserve that question until
  its meaning is established or its removal is decided; ambiguity alone is
  not a reason to delete a commitment. These labels are not an exhaustive
  taxonomy.
- **Surface.** A named part of the contract with its own stamp in the
  surface table.
- **Node.** One item of the contract's source: a surface, a subject, a
  definition, a field, a rule, a condition, an outcome, an effect, a known
  gap or an example. The contract is a tree of nodes.
- **Owner.** Supporting source and a named check, with the assertion that
  check makes, its execution context, limits and evidence grade, recorded
  beneath the supported node. Constructed records, injected dependencies,
  fixture processes and integrated product runs establish different things.
  A cited check need not cover every part of the rule. Crediting execution
  also names the run and source/build it exercised; release credit identifies
  the case in that release's acceptance, not merely its suite in the catalog.
- **Free-text item.** A condition, dependency or effect written as a
  sentence and not yet as an expression.
- **Executor.** Whoever is carrying out a stage, and anyone they hand part
  of it to. This outline is addressed to the executor.
- **The maintainer's list.** The part of the ledger holding what only the
  maintainer can settle, each item with what proceeds meanwhile.

## Rules that hold across all stages

- **The contract is true at every commit.** It describes the implementation
  at that commit. Where the truth is awkward, it is stated in a Known gap
  paragraph, not left out.
- **Surface names are fixed at the end of stage one.** A surface that
  existed at a release and later disappears keeps a removal row in the
  surface table permanently. The unpublished stage-one release enters this
  history, so later stages change what a surface contains and leave its name
  alone.
- **The guide stays out of the surfaces' definitions** from stage one on.
- **A disagreement between contract and implementation is never settled by
  assumption.** Which side changes is decided on the evidence for each
  side, by whoever [Who decides what](#who-decides-what) names, and the
  decision is recorded.
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
  explains how to use those commitments. Definitions also state the limits
  of a successful value's meaning, beside that value. Those limits are not
  failure effects or dispensable descriptions of negative space.
- **Production and interpretation are stated apart.** Where PolicyWitness
  produces a record is one commitment. What it checks whenever that record
  is present is another, and does not depend on what the current producer
  emits.
- **Evidence is graded.** A claim rests on a run, a check that was read, or
  source that was read, and its owner says which. Agreement among generated
  artifacts, or among implementations, is not correctness.

## Carrying out the stages

An executor carries the stages out from this outline and hands parts of the
work to others where that helps. The maintainer looks in from time to time
and does not approve ordinary steps, so work does not wait for a check-in.
Commit each unit of work to `main` when its checks pass. Push nothing.

### Who decides what

**The executor decides, and records the reason:**

- the working taxonomy, the node types, the wording, and the arrangement of
  the document within the structure proposal's outline;
- the meaning of an existing record, field or value, read from the source
  that produces it and stated with its limits;
- owners and their grades, which items stay free text, and the disposition
  of a strain that sits in the text;
- a test that gives a true rule an owner, and a correction to a test or
  harness reader that a definition shows to be wrong;
- keeping present behavior and stating it plainly, which never needs the
  maintainer;
- a change to behavior that passes
  [stage two's gate](#stage-two-resolve-the-gaps) and either repairs a
  defect against a rule the repository already states, or adds to an output
  without altering what an existing field, value or exit status means.

**The maintainer decides** every other change to what PolicyWitness does:
one that alters what an existing output means, what a caller has to do, or
how far an action reaches. Until the maintainer rules, the behavior stays,
the contract states it under a Known gap, and the item waits on the
maintainer's list as the distinction, why it matters and the commitment
that would change. Stage two names the items known now. Publication is the
maintainer's as well.

The maintainer reads the settled contract and the decision record before
the final checkpoint and may reverse anything in them. Nothing is published
before all four stages are complete, so a reversal costs rework and little
else. Two things cost more: a surface name, which keeps a removal row once
a release has carried it, and a change to shipped source after the final
archive exists, which needs another release.

### The working record

The [ledger](../records/contract/CONTRACT-LEDGER.md) is what a check-in
reads. Keep three parts at its head current, each updated in the commit
that changes it:

- **Standing.** The stage and step, what last passed and where its output
  is, what is under way and what comes next.
- **Decisions.** One entry for each decision that could reasonably have
  gone the other way: the distinction, what was chosen and the commitment
  it makes, the evidence with its grade, and what a reversal would undo.
  The costliest to reverse come first.
- **For the maintainer.** What only the maintainer can settle, each item
  with what proceeds meanwhile, and anything else worth a look.

If a question at a check-in cannot be answered from those three parts, the
ledger is behind: bring it up to date before going on.

### Handing work out

Reading, inventory, drafting a surface, reviewing one and running a suite
can each be handed to someone else. Three conditions keep what comes back
usable:

- **A brief stands alone.** It states the question, the sources to read and
  what is already known, and asks for what was opened, what was not, and
  the grade of each claim.
- **A combined claim belongs to its author.** A row returned by a delegated
  reading is that reader's reading and is recorded as one. A statement that
  joins several returns is a new claim, and whoever writes it reads enough
  of the source to hold it.
- **Review comes from someone else.** A surface is reviewed against the
  register and the coverage map by someone who did not draft it. An
  isolated reading is made by a reader started outside the repository with
  the rendered contract and the
  [task text](../records/contract/CONTRACT-CONTACT-PLAN.md#task-text-for-an-isolated-reader)
  alone; the ledger records how the isolation was arranged and where it
  fell short.

Builds and test runs in one checkout take turns, so concurrent runs need
separate worktrees ([root guidance](../AGENTS.md#testing)).

## The release checkpoints

The executor runs both checkpoints: the release commit, the local annotated
tag, and `make release`, which builds afresh, submits the build to Apple
for notarization, runs acceptance against the extracted app and archives
the result. The executor does not run `make publish` and pushes no tag. The
version is the tag; no file carries a number to bump.

For the final checkpoint, complete the changes, commits and pre-tag checks,
then pause before creating `v0.3.8`. The maintainer will arrange another
agent's review and read the contract line by line at that boundary. Tagged
rehearsal and Apple submission follow that review and the instruction to
continue.

**A failed attempt is the checkpoint doing its work.** The checkpoints
exist to find disagreements between the parts, and the acceptance battery
is demanding. Expect refusals and failing cases, most of all at the first
checkpoint: it is the first release run of tooling changed since `v0.3.6`,
and the first time the replaced stamp generator meets a tagged commit. For
each failure:

1. Read the retained receipts and diagnostics first, and say whether the
   cause lies in the environment, the release tooling, a test or the
   product. A rerun that passes is not a diagnosis; the
   [test guidance](../tests/AGENTS.md#evaluate-and-reuse-evidence) says
   when a rerun can be credited.
2. Fix the cause where it lives. Change a test or control that encoded the
   old arrangement, and say why. Repair a product defect as its own change
   under the repository's ordinary rules, with the contract stating what
   the product then does. Stage one's rule against behavior changes governs
   the restructure; it does not leave a failing case standing. A repair
   that would change what a public rule says is decided as stage two
   decides it.
3. Record the stumble in the ledger before retrying: the attempt directory,
   the commit, the failing step or case, the cause and the change. The
   cleanup after a passing attempt removes the failed acceptance output,
   and the archive describes only the attempt that passed.
4. Retry under the same number. Commit the correction on top of the tagged
   commit, delete the local tag, recreate it as an annotated tag on the new
   commit, repeat the stamp check and run `make release` again. This is
   sound because the tag has not left this repository and no archive bears
   its name. Do not amend the tagged commit, and do not take the next
   number to get past a refusal. Once `dist/archive/<tag>/` exists the
   number is spent.

If a failure survives a fix believed to address its cause, the diagnosis
was wrong: establish the cause again before another submission.

**Rehearse, so that a submission is spent only on what a rehearsal cannot
show.** Before the stamp step, build and run the default battery on the
release tree, and run the opt-in controls that exercise the stamp
generator, which acceptance does not select. That is the last development
build: between the stamp step and the tag the stamp check fails by design.
After the tag and before `make release`, run the strict preflight, then a
fresh build and the battery on the tagged tree, which exercises the release
identity and fresh caches without a submission. What is left to
`make release` alone is notarization and stapling, the app as extracted
from the final ZIP, test output nested one directory deeper, the archive's
inventory checks and the real prune.

**Keep the tree still while it runs.** From the tag until
`dist/archive/<tag>/release.json` exists, write nothing into the working
tree and run no other build or battery in the checkout. The strict
preflight runs again after acceptance and refuses an untracked note or a
new commit. Bring the ledger up to date before the release commit and again
after the archive exists.

**Do not buy a green drift suite with a baseline entry.** The drift suite
accepts a new prose or build baseline entry. Release preflight refuses any
growth against the preceding tag, and it can say so only once the tag
exists. Rewording a guide line that the baseline lists counts as growth.
Convert the site.

**Stop for the maintainer** when the signing identity or the notary profile
is absent, as distinct from unreachable inside a sandboxed harness, and
when Apple asks for a policy agreement. A pending reply, or one with no
submission identifier, is handled as the
[release procedure](SIGNING.md#apple-replies-now-later-or-never) describes
and never by submitting again to see. A case is never passed by removing it
from the default battery, adding a skip or editing evidence.

**What the first checkpoint sets in motion.** Archiving `v0.3.7` expires
the oldest local archive, the last in the older storage format, so the
release procedure's removal of its inspector falls due as a change of its
own. From the release commit on, `main` carries stamp tables naming
`v0.3.7`, and a clone that holds the earlier tags without that one fails
the stamp check and cannot build. Publication therefore needs both tags on
the remote, and `make publish` pushes only the tag it publishes. Whether
`v0.3.7` is published as a release or only its tag is pushed is the
maintainer's choice at publication. Draft release notes for both versions
so either is possible; they also carry the account of which surfaces
changed in presentation only and which in behavior.

## The contract's source and generator

Stage one will make `docs/CONTRACT.md` a generated document, authored under
`docs/contract/` beside its generator and maintenance guidance. Currently
only the stamp table is generated; the directory and full-document generator
have not been built. The model is built in stage one and firmed up in stage
three.

The test harness finds a generator at `docs/generate_<name>.py`, release
preflight imports the stamp generator by name, and `build.sh` names its
check. Every byte of `build.sh` is inside both the build identity and the
worker identity. An entry point kept at the present path and interface,
reading `docs/contract/`, leaves those alone. Moving it is the executor's
choice and brings the regeneration the
[maintenance checklist](../AGENTS.md#maintenance-checklist-when-changing-things)
names.

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
Applicability combines entry path, recipient, run state, admission state
and record presence as the rule requires; a parent default must not silently
widen a child's reach. A direct host caller does not receive the controller's
assessment. The inventory establishes which entry paths and shipped helpers
the contract covers and what each promises.

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
It must also express check order and refusal precedence across surfaces;
neither follows from nesting or a list of prerequisites. Value sets state
whether admitted values are closed or open; displayed lists separately state
whether they are exhaustive or illustrative. The relevant boundary defines
what unfamiliar values establish or cause.
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

The present generator stores nothing: it derives each stamp by hashing every
release tag's tree with today's code, reading that tag's own manifest. A
generator that reads the tree cannot hash `v0.3.6` that way, and a later
change to the source syntax would stop it reading `v0.3.7`. History
therefore needs either a retained reader for each released layout or
recorded digests for each release, and the choice decides what the check
certifies (`R-29`). Digests are not comparable across layouts, so every
carried surface is recorded as changed at `v0.3.7`.

**Sanding down is a ratchet.** Any item may begin as free text and later
become an expression. The generator counts free-text items by kind in a
baseline that may shrink and may not grow. The prose baseline for other
documents ratchets by exact entry, so rewording a listed item counts as
growth; a count by kind is a different comparison and needs its own check.
As items firm up, derived views take the place of prose summaries, and
prose that only restated them is removed.

**Checks the tree makes cheap.** Nodes nest legally. Identifiers are
unique and references resolve. An object path written as an expression
exists in the record definitions. Every public field has a field node.
Every owner's source and check exist. Every example has graded support or
an explicit evidence gap; lack of an integrated test does not by itself
justify dropping a useful example. The generated document is current.
These checks establish consistency and reference integrity, not that a
cited check exercises the claim or passed in a release.

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
  controller's assessment. The account of controller findings distinguishes
  the records inspected from the conclusions affected.
- *Surfaces.* The surfaces are redrawn to fit that shape. This is required,
  not permitted: fitting the new document into the old surfaces would turn
  the stage into a puzzle. The names chosen here are final.
- *Self-containment.* The guide's regions leave the surfaces' definitions.
  First account for every commitment in those regions, including rules,
  value sets, defaults, interpretation limits and examples. Map each to its
  destination or an explicit disposition, with unresolved claims retained
  as gaps. Removing a region from the hash inputs must not silently retire
  its commitments. What each surface contains is rendered in the contract;
  nobody has to open its source to know what the document covers.
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
  evidence, together with unresolved meanings, are recorded explicitly.
  The behavioral candidates are listed under stage two.
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

**Size.** The rendered contract is expected to reach roughly 1,700 to 2,200
lines, most of them generated field and value rows: the record definitions
and shape goldens hold several hundred public fields. If the whole document
passes 2,200 lines, put the figure on the maintainer's list before the
final checkpoint and keep working. The generator chooses the wrapping and
gives a table row one line whatever its length, so report words beside
lines, and report the authored body (definitions, rules, known gaps and
examples) apart from the generated tables. The first count is available
when the skeleton exists, before any surface is drafted.

**First steps, in order.** Steps one, two and four do not depend on one
another and can be handed out together.

1. Reconcile the drafting inputs before drafting surfaces or removing guide
   regions. Inventory the guide regions named by `docs/contract_surfaces.json`
   alongside `CONTRACT.md`. Three passages inside those regions are copied
   from `docs/EXTENSIONS.md` and `tests/FAILURE-PROPAGATION-CONTRACT.md`;
   follow them to those sources. Complete the ledger's coverage record from the
   report's findings and line-by-line verdicts, the adjudication's unresolved
   items, corrections and silences, and the reader's answers. Each concern
   has a register reference or an explicit disposition; "not examined" is
   distinct from "examined, no strain". Preserve sound meanings as well as
   defects. The resulting map records old location, meaning, evidence grade
   and destination or unresolved question; a field inventory alone does not
   establish coverage.
2. A spike, outside the repository's tracked files, on the two sections
   already worked through in the
   [structure proposal](../records/contract/CONTRACT-STRUCTURE-PROPOSAL.md):
   the compiled-profile receipt and the termination gate. It settles
   whether the source reads well to an author, whether the output reads
   like the worked sections, and how much of a constrained form the parser
   needs. Exercise recipient-specific reach, a successful value's limits,
   an open vocabulary and cross-surface refusal precedence as well. It
   also settles how the rendered document shows evidence grades and limits,
   and gives the first measurement of size.
3. The list of what the generator must guarantee by the end of this stage,
   each written as a check that fails. It includes the history guarantees:
   `v0.3.6` is read from its own manifest and never skipped; a name present
   there and absent from the tree gets a removal row; the table written
   before the tag equals the table derived once the tag exists;
   regeneration for a release refuses when the history it would overwrite
   is unavailable (`R-29`); and a later change of source syntax leaves an
   earlier release readable. It also covers the prose scan, which treats a
   generated document as authored text unless it sits in a generated
   region, so that a literal duration or size in the rendered contract
   becomes a baseline site.
4. An inventory of everything that refers to the present stamp generator,
   surface manifest, surface names and region markers: the build script,
   the surface names written into the generator's shape collection, the
   tests and mutation controls bound to the generator's interface, the
   opt-in controls that acceptance does not run, release preflight, the
   build and architecture accounts, the build identity's scope, and the
   links into `CONTRACT.md`, including those the link check does not scan.
   The ledger holds a first pass from a delegated reading; verify it
   before relying on it.
5. The generator and the tree's skeleton, with every surface present and
   empty, built beside the present contract. Nothing in the build reads the
   tree yet and the generator does not write `docs/CONTRACT.md`. An empty
   or half-drafted tree is not the contract; the present document remains
   the contract until the switch.
6. The surfaces, drafted against the reconciled inputs and the register.
   The definitions and `identity` come first. After that, surfaces can be
   drafted side by side, each landing when its references resolve and it
   has been reviewed.
7. The switch, in one commit. The generated `docs/CONTRACT.md` replaces the
   present one and everything in step four's inventory moves with it: both
   stamp tables, the surface goldens, the tests and controls bound to the
   old generator, release preflight, the build and architecture accounts,
   and the links into the contract. The guide's markers are inert once
   nothing reads them and can go later.
8. The reading and truth checks below, then the release checkpoint.

**Drafting tests.** Apply these while writing the related surfaces. The
behavioral decisions belong to stage two; stage one supplies the surrounding
definitions and dependencies needed to judge them. State current behavior
and the unresolved commitment in each Known gap. Recording that account
in the stage-one release does not approve the behavior as the intended
guarantee.

- *Failed termination dependencies (`R-37`).* Read the accounts of
  dependencies, scheduling and cleanup together. They must explain what
  stops after a failed evaluated gate, what observations can still be
  collected, and what cleanup still does. Use that account to identify
  what continued execution of other phases would need to preserve or
  promise. Keep the choice between global cancellation and continued
  execution open while drafting.
- *Reliance after a controller finding (`R-38`).* Trace the relationships
  from evidence to host assertions to controller conclusions. The account
  must make clear what a finding means for reliance on the output, including
  where the current output cannot identify the affected assertion or the
  scope of withholding. A phase or actor identifier alone does not settle
  those dependencies. Establish them before choosing a diagnostic shape
  or changing which conclusions a finding withholds.
- *Entry paths and boundary order (`F-08`, `F-09`, `A-D04`).* Account for
  command-line parsing, controller admission and direct XPC separately;
  distinguish selector errors from request refusals and decode-time rules
  from later capacity checks. Locate `sbpl-check --request` and
  `_test_overrides` in the coverage map, with their actual admission and
  instrumentation limits. Removing the "no bypass" sentence does not
  dispose of these questions.

**Reading and truth checks.** Read the rendered document as well as its
source. The isolated reading is arranged as
[Handing work out](#handing-work-out) says; one reader is one sample.
Reuse the adjudication's fourteen silences and the situation questions
in the journal addenda as prompts after an unprompted reading, recording the
two separately. Compare the answers with the implementation evidence and its
limits, not just with the intended reading. A faithful restatement of a false
sentence is a truth failure. Source reads, executed checks and untested
consequences keep their grades; reader confidence supplies no execution evidence.

**Hands to stage two.** The known gaps with their kinds and supporting
evidence, and the definitions or commitments each proposed change affects.
The contract as released at `v0.3.7`, its index of known gaps, the decision
record and the maintainer's list are what the maintainer reads to direct
stage two. Stage two starts without waiting for that reading.

**Exit.** The coverage map accounts for the contract and all incorporated
guide regions, including rules and value sets; report and adjudication items
have dispositions. Every rule and example has graded support or a known gap;
every public field has a field node; the baseline of free-text items is
recorded; the generator's checks and the drift suite pass; each surface has
been reviewed against the register by someone who did not draft it; the
surface names have been confirmed and the size reported; an isolated reader
has read the new document and the prompted answers have been checked against
evidence as well as the baseline reading; `v0.3.7` has been built, accepted
and archived with its guide and Known gap paragraphs, and remains unpublished.

## Stage two: resolve the gaps

**Aim.** Settle unresolved meanings, resolve the behavioral decisions and
establish missing evidence.
Necessary distinctions remain explicit even when they require case splits.

**Gate.** Each change names the public commitment it establishes or repairs,
explains why that behavior is intended, and states the resulting rule.
Simpler prose alone does not justify changing behavior.

**Belongs in this stage.**

- *Decisions first.* Each candidate is settled by whoever
  [Who decides what](#who-decides-what) names: the implementation changes,
  or the behavior stays and is stated. First establish from source, tests
  and history whether the present behavior was argued for, merely present,
  or contrary to a rule stated elsewhere; that grades the decision. Where
  validators disagree, the definitions and scopes are settled before any
  implementation is chosen (`R-36`, and the draft of
  [disputed meanings and scopes](../records/contract/validators/DEFINITIONS-AND-SCOPES.md)).
  A definition of what the host assembles is a reading of existing
  behavior. What each reader must check when handed such a record is a
  separate commitment.
- *Changes to shipped source*, each made and verified under the
  repository's ordinary rules and able to land on its own.
- *Checks for the rules as decided*, including, once the definitions exist,
  a corpus of constructed replies run through every validator.
- *The contract kept true.* A change replaces its own Known gap paragraph
  with a plain statement of the new behavior, in the same commit. Nothing
  else in the contract moves.

**Candidates known now.** Each is a candidate, not a commitment to change.
The ledger's sorting of open rows gives the evidence behind each placement.

*The executor settles these.*

- The definitions the validators disagree on: what a preparation failure
  is, which replies may carry one, what an identifier is, absent against
  empty, and an actor's visits (`R-14`, `R-36`). Each is written from what
  the host assembles. A reader that departs from a definition is brought
  to it, or the difference is given a reason the contract states.
- What a reporting-failure reply promises as it stands (`R-36`).
- The words for withheld conclusions and the scope of withholding as
  implemented (`R-07`, `R-34`).
- Regeneration for a release without history (`R-29`): a defect against
  the stated refusal, repaired with stage one's generator.
- A check that holds the hand-written copies of a rule together (`R-15`).
- A reference from a controller finding to the phase or actor it concerns,
  added beside the existing fields (`R-38`).
- Rules with no owning check that stage one could only carry as gaps.

*The maintainer settles these. Until then the behavior named is kept.*

- Whether success reflects the controller's findings about the evidence
  (`R-20`). Kept: success follows the host's outcome alone.
- How far a failed termination dependency reaches (`R-37`). Kept: a failed
  evaluated gate cancels the rest of the schedule.
- Whether a reporting-failure reply must keep the association of its
  retained records with their actors and phases (`R-36`). Kept: only the
  form of the degradation is checked.
- Whether `unconfirmed` remains beside the host's states (`R-07`), and
  whether a reply-level finding withholds the per-actor conclusions
  (`R-34`). Kept: both as they are.
- What an ordinary build requires of the stamp check without release
  history (`R-29`). Kept: the narrower check passes.
- Whether rules now written by hand in three places are generated from one
  (`R-15`). Kept: three copies.

**Does not belong in this stage.**

- Reorganizing the contract.
- Editing the guide, beyond correcting a sentence a change has made false.
- Renaming a surface.

**Exit.** Behavioral gaps have been resolved by a change or a decision to
retain the behavior, or wait on the maintainer's list with the behavior
kept. Unresolved meanings have a stated scope or an explicit decision
retiring the commitment. Evidence gaps have the missing support or a
recorded decision accepting the stated limitation, with its reason. Calling
behavior intended does not supply missing evidence, and behavior kept while
an item waits has not been approved. Each disposition is recorded.

## Stage three: settle the contract

**Aim.** The contract reads as an account of this implementation, with no
trace of having first been written for another.

**Belongs in this stage.**

- *Revision.* Passages that carried a Known gap or a case split are
  rewritten with care. Behavior confirmed as intended becomes an ordinary
  statement; an accepted evidence limitation remains identified as such.
  An item still on the maintainer's list keeps its Known gap paragraph and
  the minimal true statement.
- *Firming up.* Free-text items become expressions until the definitions,
  applicability and obligations are held as structured facts in the tree.
  That is the machine-readable representation of the finished contract.
  Derived views take over from the prose summaries they make redundant.
  A change to the source syntax keeps `v0.3.7` readable to the stamp
  history, as stage one's guarantees require.
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

**Exit.** Every behavioral gap and unresolved meaning has a recorded
disposition or waits on the maintainer's list, and every evidence gap is
closed or has an explicitly accepted limitation; every rule has
graded support or that evidence limitation; the definitions, applicability and
obligations are structured facts, with a recorded reason for any free-text
item that remains; the size has been reported; the checks pass. The settled
contract proceeds to stage four; no release is cut at this boundary. This is
the point at which the maintainer's reading is asked for: say so at the head
of the ledger, with the settled contract, the decision record and the
maintainer's list as what there is to read. Stage four does not wait for it.

## Stage four: settle the guide

**Aim.** The guide agrees with the settled contract and explains it in
terms of public fields and observable behavior. Settle whether a user can
prepare a specimen, select a runner, interpret the output and recover from
refusals using the guide, with the supporting contract definitions available.

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
- Walkthroughs of those tasks against the shipped interface, recording what
  was executed and what was only read. Use available repository scenarios;
  the unavailable consumer repository's profile collection is a validation
  limit, not evidence of compatibility and not a prerequisite to this stage.
- The final release checkpoint: prepare `v0.3.8` with the settled contract
  and guide, run release acceptance and archive them together. It is cut
  once the maintainer has read the settled contract and ruled on the list,
  or has said to cut without that. Verify the
  identities and guide in the packaged artifacts and the contract's history
  against the `v0.3.6`, `v0.3.7` and `v0.3.8` snapshots. Preserve the intermediate
  tag when making that history available at publication.

**Does not belong in this stage.**

- A wholesale redesign of the guide's organization. Local moves needed for
  a complete explanation belong in this stage.
- Changes to public rules or product behavior. A disagreement found here
  goes back to the stage that owns it. Release stamping and packaging belong
  to the final checkpoint.

**Exit.** Each guide section has been read against the contract; the user
tasks have recorded outcomes and validation limits; the checks pass; the
maintainer's reading has happened or been waived;
`v0.3.8` has been accepted and archived with the settled guide. The full plan
is complete before publication proceeds.

## Decisions still open

Each item says who settles it. The executor's are recorded as decisions
when made.

- **The surface names, before the stage one release.** The executor. The
  structure proposal's surfaces are the working set. The names become
  permanent at that release, so they are confirmed then. Review the
  boundaries of `reply`, `actor_evidence` and `diagnostics` against the
  unresolved stage-two definitions before confirming them; the present
  outline does not settle those boundaries. Put the confirmed names on the
  maintainer's list before tagging and do not wait on them: a name changed
  afterwards costs a removal row.
- **What an ordinary build requires of the contract's check** (`R-29`).
  The maintainer. The replacement generator keeps the present behavior
  until then: a source copy without release history passes a narrower
  check and says so.
- **What ships.** The maintainer. A release archives the guide and not the
  contract, and after stage one the guide's surface table names surfaces
  defined only in the contract. The working arrangement keeps the generated
  table in the guide and the archive's contents as they are.
- **Review across the migration releases.** The executor. Rewriting all
  surface inputs can move every stamp even without behavior changes. Say in
  the release notes, surface by surface, which changed in presentation only
  and which in behavior, drawing on the decision record. This does not
  change what a stamp hashes.
- **Public presentation of evidence.** The executor, in the spike. Decide
  how the rendered document exposes evidence grades and execution scope.
  Public limits on a commitment and gaps in its support must remain
  visible; detailed evidence metadata remains separate from the stamped
  public content.
- **For each stage two candidate, whether the implementation changes.**
  Made within stage two, definitions first, by whoever that stage names.

## What the examination supplies, and its limits

- The [technical report](../records/contract/CONTRACT-FIRST-READER-REPORT.md),
  including its line-by-line verdicts, findings, sound statements and unrun
  experiments, and the
  [adjudication](../records/contract/CONTRACT-ADJUDICATION.md), including
  corrections to the report and consequential questions neither reader raised.
  These remain drafting inputs until their contents are reconciled with the
  register; the maintainer's selected close reads do not replace them.
- A claim inventory covering every line of the present contract, with a
  literal account of the mechanism behind each sentence. It follows the old
  sentences, so stage one regroups it under the tree's rules. Its rows are
  readings by delegated passes; nothing in it was run, and a share of its
  rows have a source but no check, more than one answer, or no owner.
  It does not inventory the incorporated guide regions; stage one's first
  step closes that coverage gap.
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

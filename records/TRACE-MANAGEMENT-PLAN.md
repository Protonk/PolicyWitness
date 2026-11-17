# Trace review management plan

## Purpose and scope

[DOCUMENTATION-TRACE-REVIEW.md](DOCUMENTATION-TRACE-REVIEW.md) is a deliberately
broad investigation record. Its investigators were encouraged to find problems
that would not look like problems from every perspective. The overlapping
entries, differing interpretations and appended qualifications preserve that
search. They are useful inputs to assessment, including when an apparent
implementation defect becomes a question about a specification, a test's
assertion scope, or the inference a reader can draw.

This plan makes those findings usable for careful remediation while preserving
their ability to challenge the existing arrangement. It establishes a route
from observations to bounded decisions and verifiable changes. It does not
select the implementation, the specifications or the tests as automatically
correct when they disagree. Agreement among all three can also rest on an
undesirable rule or a shared assumption.

A finding can disappear under one interpretation while leaving a consequential
problem under another. Record what the explanation settles and what remains.
For example, deliberate delegation can explain why one reader accepts a record;
it does not establish that callers run the reader responsible for the remaining
checks, or that coverage claims accurately describe that arrangement.

The initial groupings and examples below are assessments of the recorded
investigations. Preparing this plan supplies no fresh execution evidence or
independent confirmation of their findings. The review currently contains
DT-01 through DT-135 and two unnumbered import/receipt investigations. Its
source snapshots, builds and evidence limits remain attached to their claims.

## Working materials

Keep the review intact as the evidence record. Develop the coverage map and
working assessments in this associated plan. A targeted remediation plan can
become a separate `TRACE-<topic>-PLAN.md` when it has a concrete decision,
approach and verification. Follow the repository's
[planning guidance](../CONTRIBUTING.md#planning-a-change).

Begin with Markdown tables and short assessments. The work needs a way to find
every observation and understand its disposition; it does not yet need a new
schema, generator or issue-management system. Split the working material only
when its size or execution boundaries make that useful.

Under the [record rules](AGENTS.md), links into investigation records belong
in their associated plans. Put resulting statements of current behavior in
their existing documentation owners within the freeze boundary below, without
links back to this investigation from permanent documentation, source, tests
or indexes.

## Guide freeze and public commitments

The freeze covers the explanatory content of `docs/PolicyWitness.md` and its
distributed copies, including generated or shared content copied into them.
Changing an owning input and postponing regeneration still crosses that
boundary. The narrow exception is generator-required identity and stamp-table
updates that record another authorized change without revising explanatory
content or silently changing a public meaning. Review those outputs explicitly;
do not bypass freshness checks or hand-edit generated copies to preserve the
appearance of a freeze.

The freeze constrains publication and the remedies available now. It does not
establish that the guide is correct or that behavior it describes is desirable.
An assessment may conclude that the guide is wrong without amending it. Keep
that judgment distinct from authorization to change the product's commitments.

### Handling changes during the transition

Treat this work as a developer-facing change that a radical rewrite of the
guide will follow. Do not shape it around the guide's eventual structure or
content. The maintainer's judgments are collected at the end of the work, not
sought during it.

What counts as a public commitment is itself changing. It was the app's bytes
and the guide. The app now also speaks for itself through `help`, `example`
and `test-input`, and the contract documents carry a detailed description
that was never settled as commitments and is meant to shrink. The definition
is constructed after this work, from the user-responsibility outflow and the
collected judgments. Until then, do not gate a change on whether it touches a
public meaning. Classify it by what it does, not by where it appears:

| Change | Handling |
| --- | --- |
| Alters what the app does or prints: behavior, the envelope, exit status, or the text of `help`, `example` and `test-input` | Judge it and do not make it; it goes to the [collection for the maintainer](#judgments-for-the-maintainer). Exceptions are behavior corrected to match a meaning that is already settled and the bounded test-seam migration below. |
| Implements the [bounded test-seam migration](#bounded-test-seam-migration) | Make the selected command, admission, experiment-output and caller changes under that thread's scope and verification. This is an authorized observable change, not a correction presumed to preserve current admission. |
| Adds or strengthens a statement a user could rely on, in any projection | Do not make it, except for the developer-command definitions, help and support statements necessary to specify the selected seam migration. The guide freeze still applies. |
| Corrects, narrows or removes a description in the contract documents or surfaces | Make it when it describes established behavior, state its practical consequence, and collect it. An edit that chooses between consequential readings is a judgment for the maintainer instead. |
| Corrects a mechanism account, citation, test description or support claim | Proceed when it describes established behavior. |
| Relinquishes or narrows test authority | Make it as the overhaul plan authorizes, and collect it. |
| Alters explanatory content copied into the guide, or supplies replacement workflows or instructions for reinterpreting frozen passages | Outside the freeze boundary. The second would create a shadow user guide. |

Reductions proceed and are collected. Outside the bounded seam migration,
growth and observable change wait. Everything made under this table can be
undone before the next release. Two
existing checks enforce part of it: contract generation permits reductions in
free-text relationships and refuses increases, and release preflight refuses
added or rewritten prose sites.

The contract documents cannot provide an indirect route for amending the
guide. Where the evidence and guide disagree, retain the disagreement in the
assessment instead of silently publishing a replacement normative
interpretation elsewhere.

### Judge the product before selecting the available remedy

For each affected statement, first establish the behavior and evidential
meaning worth choosing on their merits. Then assess the existing user reliance
that choice would disrupt. Apply this locally to candidate changes; a complete
new inventory of guide commitments is not a prerequisite.

| Kind of statement | Consequence for the decision |
| --- | --- |
| Explicit commitment | Concrete conditions promise behavior or meaning. Removing it can break compatibility even if it was a poor choice. |
| Consequential ambiguity | Reasonable readings produce different expectations. Choosing one requires a decision rather than an editorial clarification. |
| Unsupported inference | A stronger conclusion exceeds what the stated observations establish. The product need not acquire machinery solely to make that inference true. |
| Inaccurate mechanism account | The prose describes an internal operation incorrectly. Correcting the account need not preserve that mechanism, unless it also expresses a user commitment. |

Use the passages and their context to justify the classification. An
unimplemented promise can still be a promise; mention in the guide does not
make every implied interpretation a commitment. Likewise, evidence that a
current rule is faithfully implemented does not settle whether to retain it.

Outside the authorized seam migration, if truthful publication of the chosen
remedy requires revising the frozen guide, that remedy is unavailable. Lifting
the freeze for a passage is not an available answer: record the present behavior
as retained, with its stated cost. The seam migration changes its selected
developer interface while recording the cost of any frozen account it leaves
inaccurate; it does not amend that account. Additional architecture intended to
vindicate existing prose needs its own substantive justification.

## Units of assessment and relationships

Use a claim with a particular boundary and consequence as the assessment unit.
An original DT identifier remains its source reference. Several entries can
support one problem, and one entry can supply several problems. DT-34, for
example, contains ownership classification, recovery wording and signing
observations that need separate dispositions. References such as
“DT-34, recovery bullet” are sufficient; renumbering the original review would
discard useful continuity.

Each working assessment should answer these questions:

| Question | What to retain |
| --- | --- |
| What is observed, and what is inferred? | The narrow observation, the interpretation being considered, and competing readings where consequential. |
| Where does it apply? | Input form, observer, representation, execution path and observation time. |
| What supports it? | DT references and follow-ups; inspected snapshot and build; native, controlled, constructed, source-read or historical evidence; artifact availability. |
| What remains problematic? | The practical consequence for behavior, evidence, interpretation, verification or maintenance after qualifications are applied. |
| What decision is needed? | Candidate implementation, specification or test changes; deliberate retention; or the particular uncertainty preventing a decision. |
| What does the freeze constrain? | The affected passage, actual commitment or inference, available corrections, and any remedy that requires a guide change. |
| What is the present disposition? | What is established, what is acceptable or defective, the treatment chosen now, and the consequences accepted or found unacceptable. |
| What would settle a remaining uncertainty? | The discriminating evidence or decision needed, without automatically creating a future work obligation. |

Keep evidence, interpretation and work status separate. A constructed frame can
establish a reader gap without establishing that the shipped producer emits
that frame. A native execution can establish behavior that is already stated
accurately. Neither category determines priority by itself. A source-supported
claim does not become executed because another entry in its group was run.

Record relationships explicitly: confirms, extends, narrows, corrects, shares
a mechanism, depends on, or remains in tension. “Related” by topic is useful
navigation but insufficient grounds for combining decisions. Use “duplicate”
only where the claim, boundary and relevant limits coincide. Even then, retain
the additional evidence rather than counting it as another independent defect.

Later text supplies evidence for a revised assessment, not an automatic
last-writer decision. Resolve apparent disagreement by checking inputs,
snapshots, observers, representations and times. Keep unresolved disagreement
visible when those distinctions do not explain it.

These examples seed the relationship map:

| Sources | Working relationship | Question that survives consolidation |
| --- | --- | --- |
| DT-08 and DT-91 | One omitted discovery root; the later entry adds executed contrasts and history. | How should the stated selection stay aligned with the generator's selection? |
| DT-23 and DT-51 | One classification asymmetry exercised through spawn and decode failures. | What outcome should validator failures produce for a declared-unapplied actor? Preserve both paths in verification. |
| DT-46 and DT-120 | The later trace qualifies the recording history and the independence concern. | Correct the recording-time account; assess actor trigger projection separately under DT-121. The follow-up found no reader treating the copies as independent corroboration. |
| DT-53 and DT-132 | The later frame exercise strengthens the scope result and explains deliberate reader responsibilities. | Which callers omit the responsible oracle or equivalent assertions, and what coverage do their passes actually establish? |
| DT-63 and DT-124/125 | Later observations distinguish last-use clearing from teardown and identify an additional worker-side control. | Can the credited test distinguish the particular clearing boundary it claims to establish? Eventual clearing does not settle that question. |
| DT-31/32/42 and DT-113–119 | One admission gate explains several observations, with separate foreign-decoding and actor-helper boundaries. | Which public states and fixtures remain useful, and which accounts describe unreachable combinations? |

## Initial families

These families are starting navigation, not a complete allocation or a set of
preselected changes. Cross-reference a finding into more than one family when
it answers different questions. Mark temporarily unallocated observations so
an unusual or isolated finding is not excluded by the taxonomy. Assignment is
an intermediate coverage step; it is not a completed disposition.

| Family | Representative findings | Organizing question |
| --- | --- | --- |
| Documentation generation and reading paths | DT-01–07, DT-13–21, DT-39–41 | What must generation preserve, and what relationships must a reader be able to follow? |
| Result selection and transport | DT-23/51, DT-31/32/42, DT-113–119 | Which states are reachable, what selects the result, and what does fallback establish? |
| Reader responsibilities and identity relations | DT-22/57, DT-25, DT-48/50/52/53/60/61, DT-130–135 | Which proposition does each reader check, under which equality rule, with what consequence? |
| Observation ownership and time | DT-46, DT-59–68, DT-120–129 | Who observes a value, when, and which observations survive independently into the reply? |
| Import inventories and compiled receipts | DT-29, DT-81–87, DT-95–104, the two unnumbered follow-ups | What is established about submitted source, imported files, captured bytes and application? |
| Runner reconciliation | DT-34/35, DT-69–80 | How are absence, failed inspection, ownership, candidate discovery and recovery distinguished? |
| Development identity | DT-08, DT-88–94 | Which paths and bytes are selected, and what constitutes failed discovery? |
| Wire identity and public projection | DT-105–112 | What requires producer/reader agreement, and what information survives projection? |
| Exec output retention | DT-55/56 | What representation makes truncation and decoding loss visible? |

Evidence-support findings also belong beside the behavior they concern.
DT-11/12, DT-38/47, DT-67/79/86/93/101/111/135 illustrate recurring questions
about availability, assertion scope, shared expectations and independent
judgment. Use those as a second view across families, without removing their
specific claims from the owning assessments. A general observation that “tests
are incomplete” would lose the distinctions needed to repair them.

## Assessment sequence

### 1. Establish coverage without filtering on severity

Inventory every numbered entry, compound subfinding and unnumbered follow-up.
Give each an assessment destination, keeping any temporary allocation gaps
visible. Include qualifications, affirmative observations and unresolved leads.
DT-44's reported but unverified items need their own treatment; absence of a new
reproduction does not turn them into resolved items.

Record links between earlier and later accounts before shortening their
conclusions. Keep the question that motivated an entry available even when its
first interpretation is withdrawn. Count coverage of observations, not a target
number of surviving defects.

The complete map is a management deliverable. Once a bounded assessment is
ready, it can proceed toward remediation while the remainder is still being
mapped. Coverage work should not become a prerequisite for every small fix.

### 2. Examine each concern from its relevant perspectives

For a selected problem, put the stated obligation, producer behavior, retained
evidence, reader checks and test assertions beside one another. Identify the
user or developer inference at stake. Use the existing
[acceptance boundary map](DOCUMENTATION-TRACE-REVIEW.md#acceptance-boundary-map-what-each-accepting-boundary-checks-and-over-which-representation)
and [observation-time account](DOCUMENTATION-TRACE-REVIEW.md#observation-time-cross-anchor-account)
where they already supply this work.

Ask both what explains the current arrangement and what that explanation leaves
unanswered. “By design,” “the producer cannot emit it,” “another reader checks
it,” and “the suite passes” can each be relevant evidence. None alone settles
a specification's meaning, the scope credited to a test, or whether the chosen
design serves its purpose.

Likewise, a suspicious combination is not automatically a runtime defect.
Preserve distinctions between a false claim, an accurately described limit,
an unspecified relation, lost evidence, an unchecked producer obligation and
an awkward but intentional design. An assessment can retain several of these
at different boundaries.

### 3. Resolve only uncertainty that changes the decision

Check current applicability against the files and dependencies behind a claim
before implementing its remedy. Reuse recorded observations with their stated
limits where applicable. If evidence is missing or a dependency changed, name
the question a new check must settle before running it.

Prefer a small contrast that distinguishes competing explanations. Avoid a
fresh broad audit simply to replace the review with a uniform report. When an
uncertainty cannot yet be settled, retain the competing accounts and judge what
the evidence presently supports, what it leaves unknown, and whether accepting
that uncertainty is justified. Identify further evidence only when it would
change the decision; its absence need not generate a task. A decision that
cannot responsibly be made remains pending, rather than being counted as a
completed assessment through assignment to future documentation work.

### 4. Choose and verify a bounded response

Evaluate candidate remedies on their merits, then select the treatment
available within the guide freeze and existing commitments. Responses include
correcting behavior to match a settled meaning, correcting a test or its
coverage claim, improving the reading path, or retaining the arrangement with
an explicit rationale. A change to what the app does or prints is judged here
and left to the maintainer, as the
[transition handling](#handling-changes-during-the-transition) sets out. More than one response may be necessary. Narrower
prose is sufficient only when the narrower promise is justified and its
practical consequence has been assessed; it cannot silently withdraw a
commitment or substitute for a frozen guide amendment.

When the preferred remedy is unavailable, complete the present product
judgment. State the remaining defect or limitation and whether its consequences
are accepted. “Update the guide later” is neither that judgment nor a chosen
remedy. If the cost seems unacceptable, say so in the judgment. That is a
matter for the maintainer, and the closing collection carries it.

Group changes when they share a decision and verification boundary. Keep
separate changes for separate mechanisms even when their symptoms resemble
one another. Priority should consider consequence, reachability, uncertainty,
dependencies and decision readiness. Popularity across reports and ease of
reproduction are not measures of importance.

## First applications of the method

### Transport pilot

Start with DT-31/32/42 and DT-113–119. The
[existing synthesis](DOCUMENTATION-TRACE-REVIEW.md#how-dt-31-dt-32-and-dt-42-relate)
already separates a shared gate from adjacent mechanisms. Answer three reader
questions through one short assessment:

1. Which combinations of submission, capture and host reply can reach the
   shipped result path?
2. What does the first failed boundary leave in the envelope?
3. What purpose and meaning should ordinary and actor fallback have?

Produce separate candidate decisions for unreachable result states and their
fixtures, foreign-producer decoding, and actor-form helper invocation. Do not
infer that every defensive branch should be removed. Establish whether its
purpose is defensive handling, component testing, or an advertised public
possibility, and evaluate the tests on that basis.

Separate availability of fallback output from its explanatory power.
Independent compilation does not establish worker progress or explain a lost
reply; do not expand transport machinery merely to support that inference.
Removing an invocation or changing the presence or status of `policy_check`
can nevertheless alter an observable commitment. Assess that compatibility
question and the actor-form whole-request failure independently. The pilot's
disposition must judge their present utility and cost, even if a preferred
change cannot be published during the freeze.

### Test and specification challenge

Use DT-53/132 and DT-63/124/125 to check that the method preserves findings
whose apparent defect changes with perspective.

For DT-53/132, delegation explains the general consumer's scope. The assessment
still needs to address the callers that do not run the lifecycle oracle and
the claims made about their coverage. Possible responses include changing
which checks run, changing credited scope, or accepting a stated gap. A unified
validator is not implied.

For DT-63/124/125, observed clearing and source order can support the behavior
while a final-state assertion still fails to establish its claimed timing.
Assess host and worker controls separately. The remedy may be a discriminating
observation or a corrected support claim, with no change to erasure behavior.
If the behavior is sufficiently supported and the test's credited scope is
corrected, that narrower assessment can finish without a guide rewrite or an
automatic obligation to add implementation work.

### Import and receipt distinctions

Use this family as a check against excessive merging:

- DT-82 concerns a scanner distinction dropped by the helper's projection.
- DT-84 concerns a literal import form missed by the scanner.
- DT-85 bounds a deliberate walk that includes unevaluated forms.
- DT-98 concerns the receipt's input coverage.
- DT-103 concerns the private object view and the inference about application.

The [final qualifications](DOCUMENTATION-TRACE-REVIEW.md#passages-in-the-appended-account-that-need-narrower-wording)
correct a consequential earlier emphasis: source association holds by
construction; the missing association concerns the compiler's file inputs.
Adding a source-digest comparison would not supply that missing observation.
Preserve the distinction between documented separation, unverified association,
observed divergence and signaled incompleteness. Fixing a scanner miss would
not identify the file bytes consumed by a separate compilation.

Judge whether the lack of compiler-file observations is an accepted limit of
the instrument, and whether its public account overstates the evidence.
Preserving the receipt does not require making the literal inventory identify
those inputs. Conversely, accepting that limit does not dispose of the scanner
miss or the helper's dropped incompleteness signal. A retained documentation
defect must state the mistaken inference readers remain exposed to; an internal
assessment does not repair that user-facing defect.

### Early remediation candidates

These are bounded starting points for assessment, not predetermined solutions
or a final priority order:

| Sources | Candidate decision | Discriminating verification |
| --- | --- | --- |
| DT-55/56 | Decide what exec output promises and how its representation exposes NUL, truncation and decoding loss. | Preserve both the embedded-NUL and split-UTF-8 contrasts; inspect retained content and loss indicators, not only child success. |
| DT-74 | Distinguish an absent registry from failure to inspect its path. | Contrast absent path, inaccessible ancestor and unreadable file; inspect the resulting classification and candidate report. |
| DT-89 | Decide how failed source-directory enumeration affects identity derivation. | Contrast readable and unreadable directories containing selected files; check that omission cannot silently masquerade as complete discovery. |
| DT-23/51 | Decide how declared-unapplied actor classification handles validator failures. | Exercise spawn and decode failures beside their applied counterparts, retaining independent worker observations. |
| DT-09, DT-26, DT-54, DT-58, DT-69, DT-91 | Assess specific inaccuracies and correct accounts within the freeze boundary; give remaining inaccuracies a present disposition. | Check ownership, generated destinations and user commitments, then verify that corrected support establishes the stated scope. |

Broader questions about integrity findings and exit status, receipt validation,
or wire projection need their own decisions. The current separation of result
selection and diagnostics is documented; changing it would require an account
of the desired public meaning and affected consumers.

## Remediation handoff and verification

A remediation proposal should carry the bounded problem, relevant competing
interpretations, chosen behavior or meaning, affected owners and readers,
verification, and explicit exclusions. Include the freeze's effect on the
selected remedy and any residual cost. Explain why the chosen layer changes;
existing agreement with that layer is insufficient justification by itself.
Public-meaning and interface decisions follow
[CONTRIBUTING](../CONTRIBUTING.md#improving-documentation-in-four-passes).

For each proposed check, state the plausible incorrect behavior that could
previously pass and how the new observation distinguishes it. Match the tested
representation to the claim: a pre-encoding object does not establish byte
preservation, a body helper does not establish whole-envelope acceptance, and
captured-byte equality does not establish semantic truth. Shared predicates
and generated definitions should receive credit for consistency without being
counted as independent judgments.

Follow [test guidance](../tests/AGENTS.md) and
[change verification](../tests/CHANGE-VERIFICATION.md) for case selection,
evidence reuse and required controls. In particular, changes to the worker
wait, release store or eligibility rule require
`witness_contract/order_barrier_mutations`. Run registered selections through
the dispatcher with a fresh `PW_TEST_OUT_DIR`, and respect the shared checkout
lock. Direct investigations retain their own evidence class.

The review's development runs and scratch artifacts are local, generally
gitignored or temporary, and have no retention guarantee. Check availability
before crediting them. Preserve decisive observations and provenance in the
assessment, without adding retention exceptions or treating missing artifacts
as either proof or disproof of the recorded result.

For permitted documentation and contract changes, edit the owning inputs and
regenerate through the [documented generators](../docs/AGENTS.md). Inspect all
destinations for guide content changes, including copies from shared inputs;
separate any allowed identity/stamp updates from explanatory changes. Update
affected admission, transport, readers, fixtures and public meanings together
when the decision crosses those boundaries. Mechanical freshness establishes
agreement of copies; review and selected behavioral checks establish the
changed claim.

## Working the three plans together

[TRACE-ACCEPTANCE-PLAN.md](TRACE-ACCEPTANCE-PLAN.md) and
[TEST-OUTCOME-OVERHAUL-PLAN.md](TEST-OUTCOME-OVERHAUL-PLAN.md) reach some of
the passages, tests and decisions assessed here. This section owns the order in
which shared work settles and the selection of its broad verification; the
companions refer to it instead of restating it.

The sequencing rests on source and catalog inspection at `a9de3ccf`; the seam
migration also uses inspection at `ebc18543`. Nothing was executed for these
readings. The durations below are approximate figures from earlier development
runs on the maintainer's machine, not retained evidence; `run.json` records
the actual ones.

### Shared threads

Six threads need more than one plan. Elsewhere each plan proceeds alone.

| Thread | This plan | Acceptance plan | Overhaul plan |
| --- | --- | --- | --- |
| Actor fallback and transport result paths | Transport pilot | Fallback-compilation rehearsal | Run-flow fallback tests and the fallback-removal observation |
| Compiled-profile receipts | Import and receipt distinctions | Rehearsal of a capture reported despite unsuccessful application | Label-admission test and its credited claim |
| Association and reader responsibilities | DT-53/132 with the identity-relation findings | Association-equality rehearsal | Consumer and oracle callers and their credited coverage |
| Exec descendant lifetime | Commitment assessment the overhaul requests | None planned | Survivor conversion and the aftermath dependency |
| Authority erasure timing | DT-63/124/125 | None planned | Credited last-use claim and any observation before teardown |
| Executable test seams | Selected admission changes, scope and transition costs | Change or remove one migrated seam; compare maintained decisions | Command implementation, caller migration and preservation of experimental evidence |

Take a shared thread in this order:

1. **Read once.** Where a rehearsal is planned, make its trace and this plan's
   comparison of perspectives one reading. Both inspect the same statements,
   producers, readers and assertions. Include the tests that enforce the
   rehearsed subject, so the overhaul's local rehearsal is not a second pass.
2. **Decide once.** Record the disposition here, with the freeze's effect. The
   rehearsal is evidence for it and not a gate: a thread without a planned
   rehearsal does not wait for one.
3. **Change once.** The overhaul applies the authorized test response. Permitted
   account corrections land with it, so each destination is edited one time.
   An arrangement change the rehearsal justified lands with them when it stays
   within developer-facing accounts and moves no ownership. The seam migration
   additionally carries the implementation and ownership changes authorized
   below. Other changes go to the collection for the maintainer.

A disposition recorded before its rehearsal can correct a passage that the
arrangement judgment then moves or removes. A test response chosen before the
disposition selects authority after seeing the result, which the overhaul
rules out.

Where a thread produces both a test response and a product change, land the
test response first and exercise it against the existing behavior. A test and
a product changed in one step cannot show that the revised test still
distinguishes the old behavior from the new.

For the seam migration, establish the existing experiment's observations and
checks before changing its entry point. The new command and its callers may
then land together, with old/new evidence compared. Keep any change to judgment
or enforcement separate from that interface migration.

The exec-descendant commitment is not the subject of a DT entry. Assess it with
the [same method](#judge-the-product-before-selecting-the-available-remedy),
and early: the overhaul's acceptance argument depends on that conversion.
Handle other commitment questions the overhaul hands in the same way. They do
not join the DT coverage map.

### Bounded test-seam migration

Move a selected set of executable test seams into an explicit experimental
execution route under `test-input`, completing that work before final integrated
verification. This is part of the combined implementation, not a recommendation
to develop in the closing outflow. This plan owns selection and admission
decisions; the [overhaul](TEST-OUTCOME-OVERHAUL-PLAN.md#migrating-executable-test-seams)
owns implementation, caller migration and experimental equivalence. The
[acceptance companion](TRACE-ACCEPTANCE-PLAN.md#rehearsing-a-migrated-test-seam)
examines whether the arrangement reduces independently maintained decisions.

Begin by accounting for the ten fields in the existing
[override reference](../runner/README.md#test-seam-_test_overrides): three
component substitutions and seven timing/fault controls. Trace each to its
admission, effective intervention, callers and retained evidence. Select the
coherent subset to migrate before implementation; give fields left outside it
a present treatment and reason. This is a bounded inventory of the existing
seam, not an audit of every test hook or a mandate to move all ten.

Use `validator_executable_path` and the paired `worker_pre_ready_hang_ms` /
`worker_timeout_ms` as the initial design contrasts. They exercise replacement
equipment and intervention in shipped components. Confirm or revise that subset
from its actual callers; do not satisfy the work with a new unused command.
Record the selection here once, with the overhaul's case/evidence mapping
linked from it. No separate finding inventory or permanent seam registry is
needed.

Settle the boundary early. Current `test-input read` publishes a request and
launches nothing. Flags that merely publish `_test_overrides` do not remove the
ordinary execution seam. The intended change is explicit experimental
execution, with selected controls supplied separately from the ordinary request
and unavailable through ordinary `run`. Preserve `read` as publication-only and
reuse existing execution machinery. The exact subcommand and flag design must
account for controller and host admission, internal transport, early refusals,
and the released-app battery before coding begins.

The authorization covers only that selected route, retirement of its old
ordinary-request entry points, the evidence needed to identify experiments,
and the corresponding definitions, help, tests and developer accounts. It does
not authorize new fault mechanisms, fabricated outcomes, weaker cleanup or a
separate test-only build as a substitute for testing the released executable.
Controls left outside the subset keep their explicit disposition; the migration
must not accidentally remove their coverage.

The frozen guide already names override paths and deadline controls. Identify
which descriptions the selected migration leaves inaccurate and record their
reader consequence as a transition cost. Do not preserve the old admission path
solely to vindicate those passages. Do not change the guide or shared explanatory
inputs copied into it, or create a replacement guide. Determine how the necessary
developer definitions fit the owning generators and release checks during design;
this authorization is not a waiver of freshness checks or unrelated growth guards.

Investigate and specify the migration from the start. Supply any shared reporting
requirements to the overhaul's capability stage before the instrument checkpoint.
Land the executable and caller changes after that checkpoint, on an identified
rebuilt app, with their routed evidence. Complete the selected migration before
the final integrated run. The closing records receive its implemented boundary,
accepted costs and specifically retained limitations; they do not initiate another
engineering investigation.

### What proceeds independently

- From the start, with no result needed from another plan: this plan's
  coverage map and assessments; the rehearsals; the overhaul's reporting
  comparison, its capability and the cohort equivalence mapping; the bounded
  seam inventory and design.
- A conversion or correction on a shared thread waits for that thread's
  disposition. Conversions and pure-computation cohort items also wait for the
  reporting capability.
- A product change that restores an already-settled meaning waits for its own
  disposition, and for the instrument checkpoint while one is open. The selected
  seam migration lands after that checkpoint and its own scope decision. Other
  changes to what the app does or prints are not made in this work.
- A remedy that adds controls to a population being migrated to pytest lands
  after that cohort's equivalence is established, so the mapping does not
  follow a moving population.

### Selecting verification by consequence

Use the existing routes. [Change verification](../tests/CHANGE-VERIFICATION.md)
maps a changed boundary to its selections, and `tests/run.sh --list` shows a
selection's prerequisites and dependencies. No further classification is
needed. What the combined work adds is a judgment about where breadth belongs.

An incremental signed build takes a few minutes and one case can be selected
alone. A product failure found late can therefore be located by rebuilding at
an intermediate commit and running that case. Breadth is the expensive part:
the default battery, 233 cases of which 165 need the app or worker, takes
roughly thirty to forty minutes. `preflight/build_refusal_controls`, with its
fresh builds, real acceptance and nested battery, takes about two hours. Each
holds the checkout lock, and tracked files stay unedited while it runs; a
second worktree is the existing way to keep working.

Settle at the start how many executors will work in this checkout at once.
With more than one, run the broad selections from a worktree pinned to a
commit, and name quiet windows for the live worker-wait pilot, which a
concurrent build or battery disturbs. With one, neither is needed.

Run the routed selection with each change, at the commit that carries it. Run
the default battery at the boundaries below. Keep one reason per commit; one
verification run may cover several commits.

Four kinds of change cannot rely on late localization. Give them their broader
evidence when they land:

| Change | Why it cannot wait | Evidence when it lands |
| --- | --- | --- |
| Outcome reporting and release readers, the overhaul's second stage | Every later result is read through them. | The constructed controls the overhaul names, then the instrument checkpoint below. |
| Runner installation, registry, reconciliation or cleanup (DT-34/35, DT-69–80) | A failed removal leaves launchd services and registry records that obstruct later selections and pruning. | The applicable `runner_byoxpc` opt-ins in a logged-in GUI session, with owned resources verified absent before other work continues. |
| Worker wait, release store, query eligibility or observers | The mutation anchors are exact; two accumulated changes make a failed anchor ambiguous. | `witness_contract/order_barrier_mutations` with each change. |
| Wire, layout, schema or identity derivation (DT-105–112, DT-88–94, DT-08/91) | Generated identities, goldens and every later build depend on them. | Regenerate through the owner; run `source_drift`, `runner_abi_layout` and the default build controls; rebuild before the next change. |

A document-only change needs its generator and `source_drift`, and no app.
Check [the build contract inputs](../docs/build_contract.py) before assuming a
change is document-only or test-only. `controller/src` holds the Rust unit
tests, so correcting a test's message there changes the development contract,
and the app must be rebuilt for the tree and the app to agree. `runner/Tests`
and most of `tests/` are outside those inputs.

### Three boundaries for broad runs

**Instrument checkpoint.** The overhaul's reporting capability changes the
path every result passes through. A defect in it can touch any case and cannot
be located by running one. Product remediation changes what is read. Keep the
two apart with one rule: a change to the shared reading path and a change to a
build-contract input never fall between the same two default batteries.
[The build contract](../docs/build_contract.py) prints one digest over those
inputs, and an unchanged digest shows that nothing held has moved.

For the capability, take a default battery immediately before it lands, land
it with no conversion in it, and run the default battery again against the
same app. Case statuses must equal the baseline. Other authorized product work
that is ready sooner lands before the baseline is taken; the seam migration
lands after this checkpoint as specified above.

The hold ends there. Conversions and cohorts then proceed alongside product
changes. The two migrated families need no app, and each conversion changes
one named case whose expected difference is stated in advance and checked by
running it. A change to the shared reading path that turns up later needs its
own before-and-after battery on an unchanged app, so finish in the capability
whatever the cohorts and selected seam reporting will need from the engine.
The seam's executable changes are outside this unchanged-app comparison.

Read a completed battery with the revised release battery validator as a
direct investigation that credits no case: once at the checkpoint, and again
at the first battery that contains a converted case and the migrated
families. These are the least expensive places for that reader to meet real
output.

**Signed-app checkpoints.** After that, group product changes whose routed
selections do not overlap, and run one default battery for the group instead
of one per change. Locate a failure outside every routed selection with an
intermediate build.

**Final integrated verification.** Run it once, when the selected changes from
all three plans are in. Order it by cost, so an inexpensive failure does not
consume the long run: `source_drift` and the offline controls, a build, the
default battery with the relevant opt-ins, then
`preflight/build_refusal_controls`. That last case is change-triggered here.
The overhaul revises release-acceptance orchestration, and the case's
release-battery sequence is the one catalog path in which real acceptance
reads a real battery. Its per-control records and nested output keep a failure
attributable to a build refusal, the acceptance reader or a battery case. An
actual release follows the [release procedure](../docs/SIGNING.md#release-procedure)
and remains a maintainer action.

Deferring that case to the end is sound because every unit reaches it with
its own evidence: the reading path against an unchanged app, each conversion
and product change through its own case or routed selection, each group
through a default battery.

No tagged release falls inside this work. The next release is intended after
the guide rewrite. Two consequences follow. The release-battery sequence in the
final verification is the only real acceptance the revised release reader
meets before that release, so read its nested output closely. And the retained
archives keep their earlier evidence format throughout, while every executing
run reads their identities for retention protection and pruning verifies them
in full. At the instrument checkpoint, run the read-only prune preview against
them. A revised reader that no longer accepts a retained archive is then found
before it obstructs execution or cleanup.

## Completion and disposition

Complete each assessment with a present-tense judgment:

> We establish X within these limits. We judge Y acceptable or defective
> because Z. We choose this present treatment. It leaves this consequence,
> which we accept or find unacceptable under the freeze.

When the accepted consequence falls on a user, say so in the judgment: what
they must do, avoid, arrange, check or refrain from concluding. The
[closing collection](#user-responsibility-outflow) reads these statements.

The judgment may conclude that an alleged defect is not established and a
narrower problem is resolved; that behavior is an accepted limitation with no
additional work warranted; or that a known defect remains deliberately retained.
In the last case, name the affected cases and costs. Assessment completed and
defect repaired are different states. A known defect can remain without an
automatic promise to repair it when the guide changes.

If the residual cost seems unacceptable, say so. The decision about the
product's behavior is the maintainer's, and the
[closing collection](#judgments-for-the-maintainer) carries it. The assessment
is complete once the judgment, the cost and that referral are recorded;
assigning a future documentation task cannot substitute for the judgment.

A disposition that accepts a limitation lasts only where an owner states it.
When a developer-facing owner exists, a test account or a support record,
state the limit there beside the claim it limits. When the only truthful home
is a public statement or the guide, the limit belongs to that collection.

An unresolved evidence question can receive a completed, bounded judgment when
the present uncertainty and its consequences are explicitly accepted. Do not
claim the underlying behavior was established in that case.

Record which original claims were resolved, narrowed, withdrawn or deliberately
retained, what evidence supports each disposition, and what remains defective
elsewhere. A correction to one passage does not close every concern in its
family. An implementation that meets its current specification does not by
itself close a challenge to that specification or its credited tests. Correcting
internal accounts while freezing misleading guide prose leaves a documentation
defect whose reader impact must be judged explicitly.

The management pass is complete when every observation has a traceable present
assessment, follow-up qualifications are represented, selected changes have
usable proposals, and the [reserved material](#material-reserved-beyond-this-work)
is recorded. The combined work also requires completion of the selected seam
migration under the overhaul's verification, not merely its assignment to a
closing record. No observation is complete merely because it has a family, a
future task or an instruction to revisit the guide. Completion requires
accountable judgments, not a target number of defects or future obligations.

Before accepting the synthesis, check it in both directions: every original
observation has a disposition, and every proposed change rests on identified
claims and decisions. Resolve temporary allocation gaps and inspect cases that
seem harmless from one perspective. Further work follows from a chosen product
objective or new evidence; the accounting exercise creates no standing backlog
or requirements for the eventual guide rewrite.

## User-responsibility outflow

Near the end of the combined work, collect the responsibilities that the three
plans' judgments leave with users, considered together. Record them in
`records/USER-RESPONSIBILITY-OUTFLOW.md`, following the existing outflow
records: a date, the source revision and a status line. This plan owns the
activity because a responsibility follows from the dispositions, compatibility
decisions and freeze it owns. The companions contribute what their own work
established.

### What belongs

An entry is a consequential condition under which someone who submits
requests, reads results, or installs and operates runners must do more than
follow the declared schemas. They must act, refrain, arrange their
environment, run a particular command or check, keep a conclusion within a
stated scope, or take responsibility for something PolicyWitness does not
establish for them.

Test each candidate by naming the action or restraint and what goes wrong for
that user without it. A candidate that supplies neither is one of these, and
stays in its assessment without being listed:

- **Implementation assumption.** The product's own producer, reader or
  maintainer upholds the condition. The user can neither meet nor violate it.
- **Optional practice.** It helps, but nothing false or harmful follows from
  omitting it.
- **Limitation without a user consequence.** It narrows what the instrument
  observes without changing an action or conclusion open to the user. A
  limitation becomes an entry when a user must restrict a conclusion because
  of it.

Duties of people building, testing or releasing PolicyWitness belong to the
working guidance, not here.

### Execution overrides

Someone using `_test_overrides` is not a user in this sense. The fields are an
instrument seam: a run through them is an experiment on PolicyWitness, not an
observation by it. For external runners, an intact copy of the app's service
is the supported use, and supplying one is a candidate responsibility.

The [bounded seam migration](#bounded-test-seam-migration) resolves the selected
interface and engineering work before this collection. Read its established
boundary and retained limitations here. Experimental operators' duties belong
to developer and test guidance; include an outflow entry only when there is a
consequence for an ordinary user's action or conclusion. A state that only a
substituted executable can produce does not become an ordinary caller's duty
merely because the experiment can produce it. Keep the shipped component's
obligations distinct from the experiment's evidence.

### Sources

Use the accumulated judgments of all three plans, including dispositions that
changed no code or test:

- This plan's completed assessments, particularly accepted limitations,
  deliberately retained defects and checks delegated to another party.
- The rehearsal assessments, for obligations the current arrangement places on
  a caller that surfaced only by reconstruction across documents. An
  obligation that exists only in a rehearsed hypothetical establishes nothing.
- The overhaul's preservation and reduction account, for what stops being
  established on a user's behalf when enforcement is withdrawn or a credited
  claim is narrowed.

Read them together. One responsibility can rest on several findings. Some
appear only in combination: an accepted limitation here and a relinquished
assertion there can bear on the same conclusion.

### Entries

Write one entry per responsibility, not per finding:

- the condition and the responsibility, stated for the role that carries it;
- the consequence of not meeting it;
- what in the product's own output indicates that the condition applies, or
  that nothing does;
- its standing, established or unsettled, with the reason;
- its provenance: the assessments, rehearsal or conversion it rests on, and
  their evidence class. Give enough to show why it belongs without restating
  the findings.

A responsibility is **established** when the evidence supports the condition
within stated limits and a completed disposition leaves it with the user. It
is **unsettled** when the condition rests on an observation that was not
traced or reproduced, when it lasts only until a product decision that is the
maintainer's to make, or when it arises only under a hypothetical arrangement.
For such a decision, name it and what each outcome does to the responsibility.
Do not promote an unsettled candidate because listing it as an obligation
seems the cautious choice.

### Guide freeze

The outflow states what users are responsible for. It does not compare those
responsibilities with guide passages, record where the guide omits or
misstates one, propose wording, or carry requirements to the guide rewrite.
Include or exclude a responsibility on the product's behavior and the
dispositions alone.

### Timing

Draft it once the last disposition, rehearsal assessment and reduction account
are recorded. It depends on judgments, not on the final runs. Finalize it
after the [final integrated verification](#three-boundaries-for-broad-runs):
restate an entry, or move it to unsettled, when that run did not bear out the
change or observation it rests on.

## Material reserved beyond this work

The work ends with material for two later events and nothing kept for its own
sake.

| Reserved for | Material | Until |
| --- | --- | --- |
| The guide rewrite | The [user-responsibility outflow](#user-responsibility-outflow) and the judgments for the maintainer, including the completed seam migration's boundary and retained costs | The rewrite has read them |
| The versioned release | The release account | The release is cut |
| After the release | Nothing in `records/` | |

None of it concerns the guide's structure, passages or wording.

### Judgments for the maintainer

The maintainer's judgments are collected here at the end of the work, not
sought during it. The maintainer intends to express them during the guide
rewrite, as statements that can be traced to code, tests and documents. Record
the collection in `records/MAINTAINER-JUDGMENT-OUTFLOW.md`, drafted and
finalized with the user-responsibility outflow.

Collect the following judgments. These have already been acted on and can be
undone before release:

- a consequence left with a user: refer to the outflow's entry;
- a description corrected, narrowed or removed in the contract documents,
  with its practical consequence;
- test authority relinquished or narrowed, with its reason;
- the authorized seam migration's admission changes, experimental boundary and
  retained costs, including any inaccurate frozen account.

Two have not been acted on:

- a remedy judged preferable but unavailable, because it alters what the app
  does or prints outside the seam authorization, adds an unauthorized promise
  or requires revising the guide, with the cost of the behavior retained in its
  place;
- a documentation arrangement that would move ownership outside the seam
  authorization.

For each, give the distinction at stake, why it matters, what would change,
and its anchors. Anchor by symbol, catalog case and statement identifier at a
stated revision, not by line number, so that a later statement can still be
traced after the files have moved.

Also name the projections that carry the matter today: the app does it, the
app says it through `help`, `example` or `test-input`, or a contract statement
says it. Leave the guide out. For each projection, say whether it is derived
from one definition or separately authored. A contradiction can arise only
between separately authored projections, so this record is what a later
choice of commitments and their projections is built from. The rehearsal
traces supply it for their threads.

### Release account

Record briefly what a release after this work will meet because of it: the
changes a reader of test results or release evidence encounters, such as
outcome semantics, the evidence-format boundary, the converted cases and the
new experimental execution route with its retired ordinary-request controls.
Include anything the release procedure must do differently. It supplies the
release notes.

### What outlasts the release

Nothing from this work needs to remain in `records/` after the release. The
plans, assessments, rehearsals and reserved material have each been read by
then, and git history keeps them.

What should last is placed in permanent owners while the work is under way,
because the judgment behind it is no longer at hand afterward:

- an accepted limit, beside the claim it limits, as
  [completion](#completion-and-disposition) requires;
- the reason a test observes a behavior instead of requiring it, in the
  suite's own account and in the commit that changed it;
- a verification rule that proved its worth in execution, in the test working
  guidance.

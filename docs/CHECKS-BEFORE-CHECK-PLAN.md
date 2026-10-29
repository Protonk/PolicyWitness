# Checks before CHECK — amended D2 investigation

## Purpose and boundary

Establish how this repository's documentation is authored, generated, copied
and checked, localize established complications, and make bounded corrections
supported by the investigation. WORKSET-PLAN.md supersedes the original
future-CHECK preparation boundary: this work does not write or outline CHECK,
allocate its ownership, register hypothetical content or prepare a special
handoff for its future writer. Acceptance and disposition finish in this workset.

Supported changes may include generators, checks, ownership arrangements and
tests, with independent accepted/rejected controls. A change to a checker's
promised guarantee still requires the workset's behavioral-defect discussion.
F1 from D1 remains unresolved by explicit user decision. Initial investigation
source is7562d24; initial writes are limited to this plan and its records while
E2 changes shared implementation and documentation. Coordinate and refresh
source before any permanent or executable correction.

The [intake](../records/checks-before-check/intake.md) establishes D1 completion,
absorption and source differences. The [package account](../records/checks-before-check/README.md)
indexes the owned artifacts. D1 retirement remains coordinated separately.
The [ownership account](../records/checks-before-check/ownership.md) reconciles
document populations, source authority and output ownership; its supporting
[facts](../records/checks-before-check/ownership-facts.json) and
[historical control evidence](../records/checks-before-check/trace-evidence.json)
retain the examined source and limits of reuse.

Follow [planning guidance](../CONTRIBUTING.md#planning-a-change),
[documentation guidance](AGENTS.md) and [test working guidance](../tests/AGENTS.md).
The principal addition to the prerequisite is a view starting from documents
and author actions. Reuse its rule inventory, evidence distinctions and design
findings rather than commissioning another general audit of tests or bindings.

## Prerequisite and intake

Execution requires the
[Binding through replay plan](../tests/suites/source_drift/BINDING-THRU-REPLAY-PLAN.md)
to be complete through its investigation, design/replay evaluation, package and
acceptance review. Its handoff must contain the inventory and L trace, versioned
design, replay predictions and results, assumptions, exclusions, cost account
and unresolved questions required by that plan. An inventory alone, or the
existence of a design file, does not satisfy this prerequisite. If completion
cannot be established, record what is missing and leave this plan unexecuted.

This plan is the immediate successor consuming that handoff. Completion of the
prerequisite means its investigation and review are finished; it does not mean
its proposed machinery has been implemented. Its retirement follows acceptance
and absorption at intake, so retirement is not a circular prerequisite to intake.

At intake, record the prerequisite's completion and review commits, inventory
revision, design version and evidence locations. Choose a revision for the new
account and compare relevant changes since the prerequisite's inventory. Refresh
affected facts and evidence applicability at that revision; preserve historical
replays and their original assumptions. Classify each inherited recommendation
as proposed, implemented with identified evidence, declined, or still undecided.
A replay result never establishes that a mechanism is present in the live tree.

Absorb the material still needed into this plan's records, preserving its
provenance and the facts needed to assess its conclusions without unavailable
local output. After absorption is reviewed and coordinated with the primary
executor, retire the predecessor plan and its package together under its
retirement rule. In that change, replace this plan's prerequisite
link with the original pathname and completion commit as text, plus a link to
the incorporated intake record. Keep the completed prerequisite identifiable
without leaving a link to a removed file. Until absorption, reach the old
package through its owning plan; do not add another inbound link to it.

## Records, scope and evidence

Create `records/checks-before-check/` when execution begins. Its README states
the purpose, the consumer (this workset's correction and acceptance process), the
examined revision and the retirement condition below. Use these artifacts:

| Artifact | Contents |
| --- | --- |
| `intake.md` | Accepted prerequisite, incorporated evidence, revision differences and disposition of inherited proposals. |
| `ownership.md` | Document and region ownership, transformations, checking scopes and evidence responsibilities. |
| `traces.md` | Complete representative edit paths, checkpoint behavior, supporting source and credited observations. |
| `reconciliation.md` | Conflicting accounts, unresolved facts, established complexity, corrections and remaining work. |
| `acceptance.md` | Disposition of findings/corrections, credited verification, review and remaining decision boundaries. |

The README indexes the artifacts. Follow [records guidance](../records/AGENTS.md):
this plan carries the repository links into its package once those files exist.
Permanent documentation absorbs useful findings into its own account. Commit
the intake and subsequent reviewed outputs so the handoff can survive a change
of executor; do not leave essential reasoning only in conversation or scratch.

Start with the permanent `docs/` accounts and the documentation index in the
[root README](../README.md#documentation). Follow their authored inputs,
generated regions and spans, shared text, figures, code outputs and staged guide
where those relationships cross directory boundaries. Include the root and
directory READMEs, working guidance and test contracts that participate in these
paths. Record plans and other transient documents where the actual checking
scope includes them, while distinguishing their role from permanent accounts.

Reconcile that population against generator declarations and the prerequisite's
checking inventory. Enumerate each discovery scope separately, including
exclusions and explicitly registered documents. The command-document walk,
prose/link scan and generator ownership declarations need not select the same
files. Follow helpers and external checkpoints far enough to explain these
relationships; a newly discovered boundary needs a recorded scope decision,
not an unbounded inventory of every suite or every prose claim.

Stamp accounts of current behavior with the examined commit and any working
changes. Distinguish source inspection, declared inputs, observed execution and
review judgments. For reused runs, follow the
[evidence applicability rules](../tests/AGENTS.md#evaluate-and-reuse-evidence).
Keep compact supporting facts in the package and label raw `tests/out/` evidence
as local and gitignored. A receipt describes its registered inputs and explicit
command wrappers; it is not an audit of all reads or descendant processes.

## Work sequence

### Establish content ownership and authority

For each in-scope document, separate authored content from generated regions,
inline spans, copied sections and whole-file outputs. Group ordinary authored
prose where it has the same handling, but identify exceptions and boundaries
precisely enough that an author can find the place to edit. Record:

- the editable input and its owner, the transformation and all destinations;
- the rule or generator selecting that content, including explicit registration
  and discovery policy, and the checkpoints that invoke it;
- the fact each comparison or assertion establishes, its evidence and what
  remains a human judgment;
- unsupported content and exclusions, including content that is scanned for
  structure or links without having its meaning checked.

Use distinct relationships for authorship, copying, generation, comparison,
citation and behavioral evidence. A generated copy can agree with an incorrect
input; a link can resolve without supporting a claim. Apply the prerequisite's
binding distinctions to relationships rather than assigning a strength to an
entire document.

Determine which facts define implementation inputs and which describe or compare
with implementation elsewhere. The [contract generator](generate_contract.py)
and [limits generator](generate_limits.py) are starting examples of different
directions of authority. Identify the independent expectations behind a claimed
implementation comparison; shared input does not supply independent support.
Do not infer authority merely from a file being a manifest or living in `docs/`.

This stage is ready when the document population and generator/checker inventory
reconcile, every owned output has an editable source, and unmatched content or
ambiguous ownership has an explicit entry for reconciliation. A reciprocal map
should expose both an output without an owner and an input whose effects were
omitted from the document view.

### Trace representative changes end to end

Select concrete examples at the examined revision that cover these distinct
paths. Combine examples where they actually traverse the same mechanism; add a
path when an uncovered mechanism could change the explanation.

| Path | Question the trace must answer |
| --- | --- |
| Shared authored prose into the standalone guide | Where is the edit made, what is copied or transformed, and what checks generation and staging? |
| A limit value or generated scalar | How do input, rendered prose and implementation comparison differ, and where are independent expectations maintained? |
| A graph, its table and a supporting citation | How are destinations and references admitted, how are figures published, and which meanings remain unverified? |
| A contract value propagated into code and prose | Which outputs define implementation inputs, and which checks establish their agreement? |
| An independently authored claim and a new ordinary document | What is discovered automatically, what needs registration, and which edits can pass every applicable mechanical check? |

Each trace starts with the exact editable input and ends at its relevant
checked-in or distributed outputs. Record the commands, readers, generators,
write boundaries, ordering dependencies and checkpoints along that path. Separate
generation, freshness comparison, structural checking and behavioral testing.
Explain local repair, default-battery coverage, build admission and release
refusal where they apply; absence from a checkpoint is also a result.

For mechanisms claiming to reject a defect, locate an applicable accepted case,
a deliberately invalid case and a restoration, with the actual assertion and
diagnostic that distinguish them. Existing controls and applicable receipts can
supply this evidence. Source inspection can establish routing but cannot be
reported as a fresh execution. Use a focused experiment only when the available
evidence leaves a consequential behavior unresolved. For semantic edits outside
a check's contract, record the expected lack of detection rather than inventing
a rejection requirement.

Inspect cross-generator dependencies and partial-failure behavior explicitly.
Per-generator idempotence or transactional publication does not establish that
an arbitrary sequence of generators is order-independent or transactional as a
whole. Record the actual refresh order and recovery boundaries. A complete
trace should let a reader predict which files change, which checkpoint can
object, and what passing that checkpoint would still leave unsettled.

### Reconcile the account and locate complexity

Compare the map and traces with the
[document-graph account](ARCHITECTURE.md#how-the-system-verifies-itself),
[generator contracts](../tests/suites/source_drift/README.md#generator-contracts),
the [build tour](BUILD.md), [release procedure](SIGNING.md#release-procedure),
working guidance and other accounts reached by the traces. Record each material
disagreement or explanation difficulty, its sites, evidence and consequences.

Distinguish these outcomes:

- **Incorrect or stale account:** a specific statement conflicts with established
  current behavior. Correct its owning input and affected copies, with the
  applicable checks. A disputed normative contract is not a prose correction.
- **Established complexity:** the account accurately describes multiple scopes,
  owners, checkpoints or dependencies. State where the complication lives and
  what purpose or constraint is established; mark an unknown rationale as unknown.
  A hard-to-write paragraph alone does not justify a refactor.
- **Unresolved fact:** identify what inspection or observation would settle it
  and which planning decision depends on the answer. Resolve it here when it
  prevents identifying an edit owner, an output path, a checkpoint's guarantee
  or the supported correction scope. Otherwise retain a bounded question with its settling action.

Generated corrections go through owning inputs and generators. Do not loosen
baselines, restamp evidence or weaken a promised guarantee to make prose agree.
Supported executable corrections require a concrete scope, source coordination,
and independent accepted/rejected controls. Record decisions and evidence;
refresh the map and traces after corrections, keeping change history in this
record rather than permanent prose. A reasoned no-change disposition is valid.

### Dispose findings and supported corrections

For each localized complication, record retaining the arrangement, correcting
its account, implementing a bounded simplification, or leaving an explicit
unresolved decision. Explain the consequence and verification. No future CHECK
scope, narrative, outline, navigation, ownership or integration handoff is a
deliverable. The inherited proposal is evidence for a decision, not proof that
machinery has been implemented or that implementing it is necessary.

## Verification and readiness review

Use the public dispatcher and a fresh managed output directory for new test
evidence. Select cases from changed boundaries and unresolved observations under
[test guidance](../tests/AGENTS.md). For authored documentation and links, inspect
and run the relevant `source_drift/generator_contract` and
`source_drift/runner_source_manifests_agree` cases. Run owning generator freshness
checks after corrections and add their suite cases when generated inputs or
outputs change. Follow docs guidance for the limits freshness check. Full builds,
live witnesses and a full battery need a specific unresolved claim or changed
dependency; they are not default requirements of this investigation.

Mechanical success establishes only the checks' contracts. Review the package
using these acceptance criteria:

| Proxy | Inspectable evidence |
| --- | --- |
| The account has a bounded, reconciled population | Document and region inventory agrees with declared outputs and actual discovery scopes; exclusions and unmatched items have dispositions. |
| An author can locate edits and follow their effects | Each selected trace identifies its editable source, transformations, outputs, checkpoints, repair and limits without an unexplained transition. |
| Guarantees have support at the claimed strength | Assertions and applicable evidence support claimed refusals; source-only conclusions and semantic blind spots remain labeled. |
| Material disagreements have been settled | Factual corrections are verified; no open fact prevents identifying ownership, central paths, checkpoint guarantees or the supported correction scope. |
| Findings and proposals have dispositions | Remaining questions name what would answer them, affected decisions and whether current behavior can be described while they remain open. |

Conduct a read-through from another executor's position using the committed package
and its cited sources, without relying on this conversation. Starting with a
representative document edit and then an input change, use the package to locate
the authoritative edit, affected outputs, relevant checkpoint and the strongest
supported conclusion from a pass. Record the chosen examples, answers and any
missing connections. Inspect every materially distinct trace; a polished example
must not conceal an unresolved path elsewhere. State who reviewed the package
and whether the review was by its author; do not describe self-review as
independent acceptance.

The package ends with a reasoned acceptance judgment, the examined revision,
credited verification and limitations. These proxies support that judgment;
they do not mechanically establish semantic adequacy or complete dependency coverage.
If a central question remains unresolved, state the settling work and do not
declare the affected work complete. An understood limitation or an optional
improvement can remain with an explicit disposition.

## Acceptance and retirement

Completion requires accepted findings, their dispositions and any implemented
corrections with applicable verification. No future writing/planning handoff is
required. Coordinate retirement with workset reconciliation; transfer still-needed
material to its remaining owned records, preserve provenance, update links and
retire this plan and package together. Permanent documentation retains useful
current behavior in its own text, without linking to retired investigation records.

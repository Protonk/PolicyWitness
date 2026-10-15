# Plan for planning guidance

Write `docs/PLANNING.md` to help agents make the first draft their best
executable proposal: sufficient for a fresh agent to execute, and disposable
once the work is complete. Human contributors should be able to use the same
guidance. Its job is to elicit the effort and judgment that produce such a
proposal, with believable explanations and useful examples.

This file plans that documentation work. The current request ends with rewriting
and committing this plan; writing the guide and integrating it remain future
work. Preparation includes review of the current repository and all 27 deleted
plans in the historical set. This revision is based on
`189e850a52ad23892ca22027665483c6a7910454`, with a clean worktree at the start.
Historical acceptance records were read, not rerun.

## The agreed goal

The guide should make a first draft a considered proposal its author can stand
behind. Being open to correction does not reduce the thinking owed before
handoff. An executable proposal chooses a course, explains consequential
decisions, and gives a successor enough context, actions and acceptance criteria
to carry it out within its scope.

Executable does not mean pretending to know an experimental result or specifying
every implementation detail. Where a necessary result can only come from later
work, the proposal must make that work executable and explain what depends on
the result. The author remains responsible for decisions that available evidence
already permits.

The short statement of the effort we want is:

> Make the first draft your best executable proposal. Investigate, choose, and
> justify a coherent path. Resolve what you can now; give the next agent
> instructions, uncertainties, and success tests.

The local handoff and retirement requirement is:

> Make the plan sufficient for a fresh agent to execute, and disposable once the
> work is complete.

These are the brief for the guide, not a substitute for developing its
explanations. The six authoring tasks below supply that development.

## Audience, deliverables and boundaries

Assume a reader who understands the relevant parts of the repository, or knows
how to find them through [README.md](README.md) and [AGENTS.md](AGENTS.md), but
has no memory of past changes or planning conversations. Help that reader turn
their understanding into a concrete proposal. Do not repeat the architecture,
build system, evidence philosophy or maintenance checklist as planning advice.

Deliver `docs/PLANNING.md` and concise discovery links from the root README's
contributing index, CONTRIBUTING's working-guidance section, and AGENTS' quick
router. Detailed working rules retain their current owners. The guide explains
how to prepare a plan using those rules; it introduces no required plan format,
commit cadence, review ceremony, plan generator or requirement to create a plan
file for every edit.

Organize the guide around the author's work, using connected explanations and
short plan fragments. Do not turn the six ideas into six mandatory headings in
every resulting plan. The chosen format must accommodate a small settled repair
without inflating it to resemble a large investigation.

This task changes documentation only. A product defect encountered while checking
an example should be recorded with its consequence for that example; repairing
it requires separately authorized scope. Do not execute other active plans.

## Develop guidance around the six ways of eliciting effort

For each item, work out what the author should do, why it improves the proposal,
and how a reader can recognize that the work has been done. Use the historical
examples to make these explanations credible. A repeated historical practice
does not by itself establish a rule.

### 1. Ask the author to choose

Develop guidance that calls for one coherent recommended course and reasons for
consequential choices. Explain how to use alternatives to support a decision
without handing the executor a menu of unresolved designs. Leave routine
implementation choices at the appropriate level of detail.

Use the SBPL helper's move from a problem sketch to a selected replacement
contract, and the Makefile plan's two already-selected changes, to work out how
much reasoning each needs. Neither example should imply that the writer can
skip diagnosis or must enumerate every rejected option.

The explanation succeeds when a reader can identify the author's recommendation,
its scope and its basis, and can tell which decisions remain the executor's.

### 2. Separate preparation from the work being proposed

Explain how to decide which inspection, reproduction or source tracing the
author must perform to make the proposal defensible now. A future first step
should not simply assign the successor research the author needed in order to
choose that step. Give a concrete example of preparation changing the proposed
work, using the policy-transfer reproduction or the disposition reproduction
chain.

Also show a genuine later dependency: an experiment whose result cannot be
assumed before choosing the dependent implementation. Explain why that experiment
belongs in the plan and what the author can still settle before handing it off.
This distinction must not become a requirement to implement the feature during
planning or to perform an exhaustive repository survey for each change.

The repository review already performed for this task is preparation for the
writer. Its architecture and build pointers are not a syllabus to reproduce in
the planning guide or assign wholesale to its readers.

### 3. Make handoff the practical standard

Develop a way for an author to check whether a capable successor can recover the
problem, intended behavior, consequential decisions, affected owners, dependency
order and evidence of completion without the originating conversation. Explain
when a source pointer is sufficient and when the plan must state the decision
itself. A link to private scratch or a previous conversation cannot carry the
only copy of an instruction needed to execute.

Use the compact Makefile plan and the more involved policy-transfer plan to
demonstrate different amounts of necessary detail. Include how to keep an
interrupted plan usable: distinguish completed work from instructions, record
the current decision and next action, and identify applicable evidence without
turning the file into a duplicate git log.

Connect handoff to disposal. The plan should identify the permanent homes for
new contracts, operating guidance and required evidence. Completion should leave
those materials usable without the plan, and maintained documents should not
depend on a temporary plan link. Do not prescribe deletion of test evidence;
its retention and cleanup remain governed by [tests/AGENTS.md](tests/AGENTS.md).

### 4. Give unresolved questions a demanding admission rule

Work out how to express an unknown in terms of the missing fact or decision,
why it cannot responsibly be settled now, the work that will settle it, and the
implementation that depends on it. Explain what an inconclusive result means
for continuation. The plan should bound the investigation and preserve useful
independent work without inventing the missing answer.

Use the BYOXPC investigation's corrected environment probe to show why an
experiment must be capable of answering its question. Use the native-feasibility
portion of the extensions plan to examine a legitimate dependency before
integration. Keep their larger audit and review arrangements out of the example.

This guidance must distinguish an empirical unknown from a design choice the
author can make and justify. A heading saying "open questions" or a promise to
revisit something during review is not enough to make a dependency executable.

### 5. Require stronger self-review

Turn the value seen in historical reviews into work the author does before
handoff: challenge the weakest premise, trace a consequential claim, and inspect
whether the proposed acceptance evidence distinguishes success from a plausible
failure. Choose a small example where this changes the plan, rather than adding
an unbounded instruction to audit everything.

The policy-transfer revision is useful here: an EOF receipt adds an observation,
but does not make host write counts prove receipt or make length agreement prove
content identity. The test-equipment proposal distinguishes valid references from
a complete dependency inventory. The generator plan distinguishes an existing
test definition from a test that establishes the cited behavior.

Explain how to select checks by the uncertainty they resolve. More tests or a
larger matrix are not inherently stronger acceptance. The guide should help the
author recognize a control that fails at the wrong prerequisite, depends on the
implementation for its expected answer, or cannot discriminate the proposed fix.

### 6. Keep review out of the default dependency chain

Explain the responsibility to present a proposal ready to act on within the
task's authorization. Historical human and agent reviews were valuable and
changed plans; describing those events as a standard sequence could instead
teach an author to stop and wait for someone else to finish the design.

Make review a challenge to the author's considered recommendation. Where a
decision genuinely belongs to the user or needs unavailable authority, explain
how to identify that specific decision and present a recommendation with its
consequences. Preserve explicit user instructions and applicable approval
requirements. Routine drafting choices and an anticipated review are not new
reasons to stop.

Check the wording especially carefully here. Statements that planning can change
later stages, or that review can change the system or question, are useful to
the guide's writer. Prominent instructions built from them could undermine the
finality and effort expected of a first draft. The guide must not reward
tentativeness, decision deferral or ceremonial approval gates.

## Historical material for this writing task

The review covered all 27 deleted plans, comparing available early and late
states, substantive revisions and associated implementation or retirement.
The useful variation includes prospective designs, investigations, compact
instructions, documentation assessments and execution records. Some first
committed copies accompanied implementation. The test-equipment proposal has no
located committed implementation of its specified deliverables. Deletion alone
does not establish completion.

Use the following references for targeted rereading when constructing examples.
They are evidence for the writer, not required reading for the guide's audience.

| Historical path | Versions to compare | Use in this task |
| --- | --- | --- |
| `controller/SBPL-CHECK-PLAN.md` | `c729128` to `a580b1f` | Distinguish identifying a problem from choosing and specifying a remedy. |
| `docs/MAKEFILE-PLAN.md` | `1c3ec36` | A small executable proposal whose investigation and selection happened earlier. |
| `POLICY-TRANSFER-ACKNOWLEDGEMENT-PLAN.md` | `9505f9f` to `dc7d090`; completion in `7ad4c96` | Preparation, a discriminating control, precise unknowns and correction of overclaims. |
| `controller/DISPOSITION-RECORD-PLAN.md` | `8cd7f3f` to `0b6e191`; completion record in `288c2c5` | Connect reproduction, selected behavior and independent acceptance. |
| `tests/TEST-EQUIPMENT-PLAN.md` | `8d192ed` to `92dfd1d` | Distinguish the proposed check's guarantee from a larger manual-review claim; do not present this as a completed success. |
| `docs/BYOXPC-INVESTIGATION-PLAN.md` | `e2115cf` to `ecbd962` | A proposed probe proves unable to answer its original question. |
| `SANDBOX-EXTENSIONS-PLAN.md` | `8d6f8fe` to `fb2750d`; completion record in `2582f1e` | Feasibility before dependent design; separate executable investigation from later results. |
| `docs/GENERATOR-HARDENING-PLAN.md` | `942a68e` to `72501b7` | Clarify guarantees and condense instructions without losing their substance. |
| `docs/BUILD-DOC-PLAN.md` | `382ba2c` to `209e11c`; later record in `1c3ec36` | An assessment distinguishes promises, assertions and observed behavior; its review process is not a universal workflow. |
| `USER-GUIDE-REFACTOR-PLAN.md` | `26a6183`; retirement in `71d3753` | A plan can omit conversation changes and overstate its fidelity checks. |

Recover snapshots without restoring them into the worktree:

```sh
git show c729128:controller/SBPL-CHECK-PLAN.md
git diff c729128 a580b1f -- controller/SBPL-CHECK-PLAN.md
git show --stat 7a0dcba
git log --all --diff-filter=D --format='%h %s' --name-only -- '*-PLAN.md'
```

No repeated census is required. Reopen history only to answer a named writing
question or verify an example. Commit boundaries do not establish working-session
cadence or whose judgment initiated a revision. Historical status and test
receipts do not establish present behavior. Avoid importing old field layouts,
schema values, authorization instructions or acceptance claims as current rules.

## Work sequence

The goal and six directions above are settled inputs. The work is to make their
explanations convincing and useful, then assess the guidance through the plans
it helps produce. These stages are for writing this document; they are not a
process to impose on every plan. Each stage produces reviewable work. Its end
does not create an approval pause or require a separate reviewer.

### P1. Work out the explanations and examples

Record the execution revision and relevant local changes. Read the goal and six
authoring tasks above. Refresh only repository instructions or source details
needed for the examples; preparation has already supplied the general orientation.

Develop short working fragments for each of the six ideas. Each fragment should
explain an author action, the planning problem it solves, and an observable
difference it makes to the proposal. Start with a small repair and a repair
whose acceptance needs a discriminating observation. Add an uncertain-feasibility
fragment to establish the limit of what must be decided before handoff. Reuse a
fragment across ideas when that avoids repetition.

Adapt the cited histories into self-contained examples. State the necessary
scenario facts and distinguish them from facts an author still needs to inspect.
Show the reasoning that earns a recommendation; do not present the final
historical plan as a pristine first draft or a universal template. Use only the
technical detail needed to understand the planning choice.

Keep a compact working note here mapping the six ideas to their explanation,
example and likely misreading. Resolve weaknesses in those explanations before
building the guide around them. This note is drafting material and is retired
with this plan.

Exit: every idea has a concrete treatment; the examples demonstrate choice,
preparation, handoff, bounded uncertainty and self-review without making external
review a prerequisite. The small repair remains small. No required content rests
solely on a historical practice or on the originating conversation.

### P2. Write the guide

Write `docs/PLANNING.md` from P1's treatments. Open with the expected quality of
the first proposal, then explain the author actions in an order a reader can use.
Integrate the fragments where they clarify a decision. Finish with a concise
self-review of readiness for a successor and eventual retirement. Use the six
ideas as coverage obligations, not a required six-section document structure.

Keep the guide focused on planning effort. Link existing instructions when a
reader needs their details; do not reproduce the repository survey or enumerate
every possible affected subsystem. Omit a mandatory template and historical
narrative. A reader should not need any of the deleted plans or this plan to
understand or follow the guide.

Review every imperative for what it would cause an agent to do. Remove advice
that rewards long inventories, repeated research, unspecified future decisions,
unnecessary tests, premature certainty or waiting for routine review. Preserve
genuine prerequisites and the authority of explicit task instructions. Explain
how effort is scaled by the decisions and uncertainties in the change, rather
than the length or number of sections in the resulting plan.

Exit: a complete guide gives a reader a practical way to produce the agreed kind
of proposal. All six ideas are developed, handoff and disposal are explicit, and
the writing does not substitute a workflow ritual for judgment.

### P3. Exercise the guidance by producing plans

Use the draft to prepare short first proposals for the scenarios below. Supply
enough repository context or source access to avoid testing orientation instead
of planning. These are writing exercises: do not implement their proposed changes
or run product experiments just to demonstrate the guide. Where needed, give the
exercise an explicit observation as part of its premise.

Vary the concrete problem from the guide's worked fragments so that copying an
example cannot satisfy the exercise. If a fresh reader is available, give them
the guide and scenario facts, keeping the assessment criteria below separate.

| Scenario | What to inspect in the resulting proposal |
| --- | --- |
| A small operator-interface repair with a known defect and an available remedy. | Does it choose a bounded change, account for affected callers and select adequate verification without inventing a large process? |
| A child can act on incomplete input, and an existing control distinguishes that behavior from receiving the complete submission. | Does it use the available evidence now, choose the repair, cover partial results and affected readers, and explain acceptance without delegating the design to review? |
| A proposed native capability has one unresolved feasibility premise. | Does it make the investigation executable, specify a discriminating observation and consequences of each result, and settle the independent decisions without inventing feasibility? |

For each proposal, inspect whether a successor can identify the recommendation,
why it was chosen, the next actions, genuine dependencies and completion evidence.
Point to the actual passages supplying those answers. Check what durable material
the work will leave so that deleting the plan loses no operating instruction or
contract. Then identify where the guide encouraged an omission, excess or deferral,
revise it, and repeat the affected exercise.

An available fresh reader can expose problems the author misses; do not make
obtaining one a dependency of this work. Record who performed each exercise and
what context they had. An author rehearsal is not independent review or proof
of how another agent will behave. Keep its results and limitations here; if a
review is supplied, record its findings and their disposition in the same place.

Exit: the actual proposals support the goal across the three scenarios, and
identified guidance defects are corrected. Coverage of the six ideas alone is
insufficient. The assessment must account for execution readiness, decision
ownership, appropriate scale and retirement, including any remaining limitation
of the exercise.

### P4. Integrate, verify and retire

Add the discovery links named under Audience, deliverables and boundaries. Keep
routers short and preserve the distinction in [CONTRIBUTING.md](CONTRIBUTING.md)
between working guidance and implementation descriptions. No maintained document
should link this plan or rely on its historical examples for instructions.

Inspect the current documentation checks before running them. At this plan's
baseline, `scanned_documents` in
[generators.py](tests/suites/source_drift/generators.py) includes `docs/*.md`, so
the new guide enters local-link, anchor, symbol-link and prose-baseline checks.
CONTRIBUTING needs a direct link check because it is outside that explicit scan.
Do not expand a baseline or edit generated output to accommodate ordinary prose.

Follow [tests/AGENTS.md](tests/AGENTS.md), inspect the selection, and choose a
fresh managed output name for the documentation checks:

```sh
tests/run.sh --suite source_drift --list
PW_TEST_OUT_DIR=tests/out/runs/planning-doc-01 tests/run.sh --suite source_drift
git diff --check
```

Use a different output name if that one exists. The suite includes tool-dependent
controls; follow the existing harness escalation procedure for an environmental
refusal and retain the actual results. No signed app rebuild or live battery is
required solely for this documentation change. Mechanical checks establish their
bounded properties, not whether the guidance elicits the intended effort.

Inspect the rendered Markdown, including examples and navigation. Re-read the
guide as an agent familiar with the repository but with no memory of this work.
Confirm it asks for a considered executable proposal, supplies useful ways to
produce one, and does not make review the place where ordinary design is finished.

Closeout requires the guide, discovery links, assessed example proposals, the
disposition of material findings and applicable check results. Summarize the
exercise results and their limits in the completion record here, commit that
record so it is recoverable, and retire this plan with no dangling references.
Retain required test evidence under its existing owners. The completed guide
must stand alone; no permanent registry of planning exercises is needed.

## Execution checkpoint

| Stage | State | Next action or completion record |
| --- | --- | --- |
| Preparation and goal | Complete | Repository orientation, all 27 historical plans and the agreed six directions inform this plan. No runtime verification claimed. |
| P1 | Not started | Develop the explanations, short examples and their likely misreadings. |
| P2 | Not started | Write the guide from those treatments. |
| P3 | Not started | Produce and assess example proposals; revise the guidance where it fails its purpose. |
| P4 | Not started | Integrate, check, record completion and retire this plan. |

During execution, keep this checkpoint useful to a successor: record current
decisions, applicable evidence, unresolved dependencies and the next action.

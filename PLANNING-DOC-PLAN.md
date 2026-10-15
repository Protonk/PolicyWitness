# Planning guidance plan

Write `docs/PLANNING.md` to help a contributor turn a proposed change or repair
into work another person or agent can carry out and evaluate. The missing piece
is the connection between the repository's experimental method, its working
rules and a concrete plan: what to investigate, what to decide, how to bound the
work, and what evidence would establish completion.

This is a first draft of the work plan, not the planning guide. The present
request ends with this file. The stages below are future work; neither the
guide nor its integration edits have been made.

Prepared against `6a2cc762323ff8cb871e1ba2aee2cf3971e7fb2e`, with a clean
worktree at the start of the review. Preparation consisted of git archaeology,
documentation reading and selected implementation/assertion traces. No app was
built or run, and no historical acceptance result is credited as current
verification.

## Intended result and boundaries

The guide should serve both humans and agents, especially someone preparing a
medium change across implementation, evidence, tests and documentation. It
should also explain how to keep a small repair small and how to plan an
investigation when the remedy is not yet known. Its usefulness is measured by
the decisions and next actions a reader can recover, not by whether a plan
contains a prescribed number of sections.

Expected deliverables are the guide and short discovery links from the root
README, CONTRIBUTING and AGENTS files. Detailed rules stay with their existing
owners. The guide explains how to use them while planning; it must not become
a second wire contract, test manual, architecture inventory or build guide.

This work does not implement the active build-provenance plan, redesign the
app, introduce a plan linter or generator, require plans for every edit, or
establish a commit/review cadence. A repository defect discovered while writing
needs a concrete finding and a separate scope decision; it must not quietly
turn this documentation task into a product repair.

## Historical evidence available to the next writer

The deletion search found 27 distinct `*-PLAN.md` paths in reachable history.
Six were selected for detailed reading: controller repair, external-runner
repair, native transport, generator maintenance, documentation assessment, and
a smaller operator-interface change. The first five provide substantive
planning examples; the last checks whether advice drawn from them would impose
unnecessary ceremony on smaller work. This is a purposive sample, not a survey
of the relative frequency or success of planning styles.

| Historical path | Early committed version | Later planning version or boundary | What to examine |
| --- | --- | --- | --- |
| `controller/SBPL-CHECK-PLAN.md` | `c729128` | `a580b1f`, before helper implementation in `7a0dcba`; deleted in `4e02cf5` | A problem sketch with reproductions and open contract questions becomes an implementation plan with exact output meanings, reader changes and native/controlled acceptance cases. The early advisory-scan preference is replaced by scan removal. The text establishes that decision changed, not who originated it or why. |
| `docs/BYOXPC-REMEDIATION-PLAN.md` | `2b9a207` | `5240a6a` adds baseline results; first repair group follows in `7421101`; deleted in `2f153d0` | Starts with investigation records, bounded repair groups, contract reasoning and retained limits. The later snapshot has already executed baseline controls, so it is not a wholly unexecuted plan. Observe the distinction between a measured wait and an asserted behavior, and the ownership needed to remove installed services. |
| `POLICY-TRANSFER-ACKNOWLEDGEMENT-PLAN.md` | `9505f9f` | `dc7d090`, before implementation in `7ad4c96`; deleted in `c07911a` | The introducing commit also adds a failing control. The revision narrows what that control establishes, defines EOF publication and partial observations, joins producers/readers, and includes documentation in the implementation increment. |
| `docs/GENERATOR-HARDENING-PLAN.md` | `942a68e` | `72501b7`, before implementation begins in `9d3e2b9`; deleted in `79a5d5f` | Measured weaknesses become invariants, changes and controls. Intermediate `9561de3` distinguishes citation form from existing kinds and baseline consistency from non-growth; the later plan consolidates repeated material. |
| `docs/BUILD-DOC-PLAN.md` | `382ba2c` | `209e11c`, before the assessment results recorded in `47fe553`; deleted in `b133cee` | A document buildout becomes an assessment of promises, implementation and evidence. Read its working method and review/closeout instructions, not just the proposed table of contents. `ca8b4d1` was also inspected as an execution-stage contrast; its register contains observations and recommendations awaiting adjudication. |
| `docs/MAKEFILE-PLAN.md` | `1c3ec36` | Same available planning snapshot; implementation and deletion in `b133cee` | A short plan states two decisions, their affected callers, controls and exclusions. There is no separate committed maturation sequence to reconstruct. |

Recover these files without restoring them into the worktree:

```sh
git log --all --diff-filter=D --format='%h %s' --name-only -- '*-PLAN.md'
git log --reverse --format='%h %s' -- controller/SBPL-CHECK-PLAN.md
git show c729128:controller/SBPL-CHECK-PLAN.md
git show a580b1f:controller/SBPL-CHECK-PLAN.md
git diff c729128 a580b1f -- controller/SBPL-CHECK-PLAN.md
git show --stat 7a0dcba
```

Use the same commands with the other table entries. Commit contents and stated
status support the boundaries above. They cannot reveal uncommitted evolution,
the start of all experimental work, or conversations that prompted revisions.
An earliest committed version is not necessarily the first draft. A deletion
or completion note does not itself prove successful implementation. Author and
committer metadata do not identify whose judgment caused a change. Do not
infer preferred cadence, mandatory approval rituals or agent/user intent from
this history.

### Questions suggested by the sample

These are candidates to evaluate in the guide work, not lessons already adopted:

| Candidate | Historical basis | Question still to settle |
| --- | --- | --- |
| Distinguish a problem sketch from a plan ready for implementation. | SBPL's early explicit uncertainty and later settled contract. | What must be settled for the next action, and what can appropriately remain an investigation? Avoid demanding implementation detail before feasibility is known. |
| Tie the remedy to a bounded observation and an intended behavior. | Policy-transfer revision separates the harness-released attempt from the production host's withheld release, and length agreement from content identity. | How can a short plan state its premise and the observation that would overturn it without becoming an incident report? |
| Plan changes through their readers and supporting apparatus. | SBPL capture and shape changes; transfer receipt producers, publications and semantic readers; BYOXPC read-backs and selection. | Which affected surfaces belong together, and which do not change? A universal file checklist would obscure this reasoning. |
| Name what acceptance establishes and what it cannot establish. | Native versus controlled SBPL cases, BYOXPC timing, generator citation guarantees, build assessment's three evidence categories. | What minimum description lets an executor recognize a failure at the wrong prerequisite or an inadequate test? |
| Sequence by dependency and coherent behavior. | Transfer's later combined increment, BYOXPC's repair groups, generator prerequisites. | How should plans keep contracts and documentation coherent without prescribing commit size or one fixed staging scheme? |
| Let documentation work expose unsettled claims. | BUILD's assessment loop explicitly separates the current implementation from authority for intended behavior. | How should a writer route a contradiction into investigation or a scope decision instead of documenting a defect as intended? |
| Keep the plan useful for handoff and eventual retirement. | Generator consolidation, explicit temporary status in BUILD and BYOXPC, compact Makefile steps. | Which decisions, evidence references and next actions must survive interruption, and which repeated prose or historical narration can go? |

The sample contains different approaches to documentation timing and human
review. Those differences are evidence to inspect, not a vote to select one
universal workflow. Historical instructions about versions, ABI ordinals,
test selection and cleanup must be checked against today's owners before reuse.

## Current repository grounding

The repository already has substantial working guidance. The gap is synthesis
at the planning stage, not an absence of rules. [CONTRIBUTING.md](CONTRIBUTING.md)
frames the product as inspectable behavior and asks contributors to state an
expectation, change a condition and retain observations. [AGENTS.md](AGENTS.md)
and its directory counterparts establish the boundaries changes must preserve.
The guide should connect that material to the work a plan prepares.

The review followed the README's documentation index, the architecture's
process/timeline/evidence account, controller and runner references, wire and
request contracts, build guidance, and test/evidence/generator guidance. The
following distinctions should drive the next writer's choices:

| Repository characteristic | Consequence to address when planning | Current starting points |
| --- | --- | --- |
| Applying a sandbox is one-way; a fresh worker applies it while an unsandboxed host preserves the reply path. Explicit phases share that worker and policy. | Identify whose state changes, when resources are acquired, and whether an experiment has changed along with its implementation. Splitting or retrying work can change the specimen's meaning. | [Architecture](docs/ARCHITECTURE.md), [runner reference](runner/README.md), [runner guidance](runner/AGENTS.md). |
| Collection closure, host release, worker acknowledgement and eligible query evidence have distinct jobs. | An ordering change needs a specific invariant and its required controls; paired fields do not establish order or state stability. | The phase polling/release path in [CWorker.swift](runner/Sources/PWRunnerCore/CWorker.swift), `wait_for_proceed` in [the worker](controller/tools/pw_probe_runner/pw_probe_runner.c), [ordering contract](tests/FAILURE-PROPAGATION-CONTRACT.md#ordering-evidence-states). |
| Native results, publication, transport, lifecycle observations and interpretation are separate evidence. Optional logs cannot change execution. | State the observation a proposed field or behavior adds, who can observe it, and what remains unknown. Account for partial failure and independent readers. | `complete_execution` and `attach_sandbox_logs` in [run_flow.rs](controller/src/run_flow.rs), [controller ownership table](controller/README.md#execution-and-log-evidence-ownership), [failure evidence contract](tests/FAILURE-PROPAGATION-CONTRACT.md). |
| JSON reading rules, accepted input, exact worker source identity and compiled layout are different contracts. | Make a reasoned version/identity/layout decision, including a justified no-change decision. Update owning inputs, producers, transport, readers and fixtures together where affected. | [Wire contract](docs/CONTRACT.md), [request grammar](docs/REQUEST-GRAMMAR.md), [controller guidance](controller/AGENTS.md). |
| Generated accounts and shape goldens check bounded properties. They do not replace semantic review. | Identify the owner to edit and what its check actually proves. Review generated changes and the authored explanation as one account. | [Generator contracts](tests/suites/source_drift/README.md#generator-contracts), [shape goldens](docs/CONTRACT.md#shape-goldens), [build guide](docs/BUILD.md). |
| Verification depends on the exercised boundary and equipment, and retained evidence has ownership and provenance. | Select checks by claim; distinguish constructed inputs from live XPC/kernel effects; plan applicable signed artifacts, evidence retention and cleanup. An automation refusal needs diagnosis and the prescribed unchanged-artifact retry. | [Test guidance](tests/AGENTS.md), [harness reference](tests/README.md), [opt-in controls](tests/OPT_IN_TESTS.md), root external-runner workflow. |

One concrete trace went from the worker's EOF count and publication flag, through
the host's acquire-gated read, to the joined timeout/refusal assertions in
[PolicyTransferTests.swift](runner/Tests/PWRunnerCoreTests/PolicyTransferTests.swift)
and count/consistency checks in [consumer.py](tests/lib/consumer.py). The tests
assert receipt, refusal, absent application and independently observed cleanup;
the shape golden alone does not express those requirements. This is a useful
example of the planning problem, not a claim that these checks were run during
this review.

[BUILD-PROVENANCE-PLAN.md](BUILD-PROVENANCE-PLAN.md) is active working material
at this baseline. Its proposed build behavior must not be described as current.
Refresh the build-related references if that work lands before this plan is
executed. Do not make the future guide depend on the active plan remaining in
the tree.

## Work sequence

### P1. Refresh the evidence and make the proposed guidance reviewable

Record the execution revision and worktree state. Re-read the current routers
and refresh the affected entries above; do not repeat the entire survey by
default. Recover the paired historical snapshots and inspect the specific
sections supporting each candidate. Use the commit's broader diff to distinguish
plan revision from recorded investigation or implementation.

Keep a compact working table in this plan with one row per proposed piece of
advice: the planning problem it solves, historical example and counterexample,
current repository basis, proposed wording or disposition, and uncertainty.
Classify each as an existing requirement, a recommendation to explain, a local
choice from one plan, or an unsupported inference to discard. Historical
repetition alone cannot create a requirement.

Expand the sample only to answer a named gap. For example, an uncertain native
feature may need a feasibility-plan example beyond these mostly bounded repairs;
retrieve early and later planning sections of `SANDBOX-EXTENSIONS-PLAN.md` if
that distinction cannot otherwise be explained. Do not import that larger
effort's audit structure as the default for a medium repair.

Exit: each retained candidate has a concrete purpose, recoverable support and
its limits; unresolved substantive questions have a next action. The table is
working evidence for this task, not a new permanent planning registry.

### P2. Settle the guide's scope, ownership and readiness criteria

Use P1 to settle the following design choices before writing the guide. The
defaults here are proposals for review, not inferred repository mandates:

- Organize the guide around moving from a question to an executable plan,
  then maintaining it through findings and handoff. Do not organize it as a
  retrospective of the deleted plans.
- Treat a plan as warranted by uncertainty, interacting boundaries or handoff
  needs. A local edit with an obvious remedy can use a short account. Avoid
  thresholds based on line count or a requirement that every repair have a file.
- Distinguish readiness to investigate from readiness to implement. An open
  question is useful when it names how to resolve it and what depends on the
  answer. It is a handoff defect when the next executor must silently choose a
  material contract or product behavior.
- Explain the relationship between existing authorization and decisions still
  needed. Do not copy historical human-review gates into a blanket requirement
  to stop after each stage. Routine work within settled scope can proceed;
  material new behavior or expanded scope needs an explicit decision.
- Keep hard working rules in AGENTS files and specialized contracts. PLANNING
  explains the method and links to those owners. Any genuinely new mandatory
  rule must be identified and reviewed as such, not smuggled in as a historical
  convention.
- Offer an optional compact plan outline only if the examples show it helps.
  The outline should prompt reasoning, not demand empty headings or a duplicate
  architecture tour. Large verification matrices and audit stages are optional
  responses to particular risks.

Produce an outline that answers: what is wrong or wanted; what is known and
unknown; what the proposed change means; which boundaries/readers it affects;
what must happen in what order; what would demonstrate success or disprove the
premise; and what another executor needs at the next checkpoint. Include how a
repair differs from a new feature or a documentation assessment where relevant.

Exit: each proposed section has a reader decision to support, an example or
source basis, and an owner for detailed rules it delegates. Settle material
disagreements with the user using the concrete alternatives and evidence; do not
use this stage to request approval for routine drafting choices.

### P3. Draft the guide and exercise its examples

Write `docs/PLANNING.md` from P2's decisions. Keep the historical comparison and
its git coordinates in this temporary plan. The permanent document should
describe the adopted method and current obligations, with examples that stand
on their own after the old plans and this one disappear.

Develop two bounded examples before expanding explanatory prose:

1. A repair that crosses an evidence boundary, such as policy-pipe receipt.
   Show what changes between an initial reproduction/question and a plan
   another executor can implement. Make clear which details are illustrative
   and which current contracts the reader must consult. Do not repeat obsolete
   field layouts, version values or historical assumptions as live instructions.
2. A documentation discrepancy where inspection cannot yet establish whether
   prose, code or verification is wrong. Show the investigation and decision
   needed before either correcting prose or proposing a product change.

Use the Makefile example as a size check: the same method should permit a short
decision/scope/control account. Do not grow it to match the larger example's
sections. Select example details that expose a real planning decision; copying
an entire historical acceptance matrix would obscure the method.

Address plan maintenance: record the current decision and next action, attach
results only after execution, reopen dependent work when assumptions change,
retain failed evidence, and distinguish an unresolved question from accepted
scope. Describe handoff and retirement without turning the plan into a second
git log or imposing a commit frequency.

Exit: the draft and examples are readable as one account, all consequential
advice traces to P1/P2, and intended behavior is not presented as already
implemented or verified.

### P4. Challenge the draft through planning exercises

Evaluate the guide from the position of a contributor who has not read this
conversation. Prefer a fresh reader when available; otherwise record that the
author performed the exercise and do not call that independent review. Give
the reader the draft and each short scenario, not this plan's expected answers.
Ask for the first investigation, decisions needed, affected owners, acceptance
evidence and handoff state. Record omissions and revise the guide where they
reveal a real gap. These are document-use exercises, not product test results.

| Scenario | What the exercise should reveal |
| --- | --- |
| Add an observation of what a child received over an existing channel. | Distinguish write, receipt, publication and interpretation; find producer and reader obligations, partial states, contract decision and a discriminating control. |
| Repair a phase release or query-eligibility condition. | Find the ordering invariant, current coordinated checks and required mutation control; do not equate `query_first` with stable targets or permission agreement. |
| A failing run reports an XPC lookup error under automation. | Separate product diagnosis from harness restrictions, preserve the artifact and use the existing rerun procedure before selecting a repair. |
| A build document says a check proves more than its assertions show. | Distinguish textual agreement, assertion coverage and observed behavior; investigate or narrow the supported claim without silently blessing a defect. |
| A BYOXPC regression needs installation and can fail during removal. | Account for GUI/signing equipment, service ownership, durable cleanup state and verified absence before discarding staging. |
| Rename a local operator verb, or correct one documentation link. | Scale down to affected callers and appropriate verification; avoid an automatic signed rebuild, native experiment or elaborate plan template for a link correction. |

Also review the draft for advice that could come from any repository with the
name changed. Generic advice should earn its space by explaining a decision
here. Remove unsupported universals, duplicated rule tables and repetition
between the examples, outline and explanatory prose.

Exit: the exercises recover the material decisions and obligations without
inventing unnecessary work. Remaining limitations are explicit; no claim of
independent validation is based only on the author rereading their draft.

### P5. Integrate, verify and prepare closeout

Add concise links in the README's contributing index, CONTRIBUTING's working
guidance and the root AGENTS router. Link to the finished guide, never this
temporary plan. Preserve the existing division between descriptions, working
rules and detailed contract ownership; avoid copying the guide into routers.

Inspect the documentation scan before choosing checks. At the preparation
baseline, `scanned_documents` in
[generators.py](tests/suites/source_drift/generators.py) includes `docs/*.md`,
so PLANNING will enter local-link, anchor, symbol-link and prose-baseline
checks automatically. CONTRIBUTING is not in that explicit scan set and needs
a direct link check as part of review. Prefer links to current owners over
restated numeric facts. Do not add a prose-baseline exception just to silence
a failure or edit a generated region by hand.

For the documentation change, inspect the selection, then use fresh managed
output for the applicable documentation suite:

```sh
tests/run.sh --suite source_drift --list
PW_TEST_OUT_DIR=tests/out/runs/planning-doc-01 tests/run.sh --suite source_drift
git diff --check
```

Choose a fresh output name if that one exists. Follow the current test guidance
for equipment, harness escalation, retention and applicability of earlier
evidence. Some source-drift cases exercise tooling, including Swift discovery;
an environmental refusal is not a document defect or a passing check. Do not
build/sign the app or run the live battery solely because this is a planning
document. If the agreed scope expands to executable behavior or test machinery,
revise verification according to those changes before proceeding.

Review the rendered Markdown in the normal repository viewer: examples,
tables, headings and links must be usable. Check both directions between the
guide and its owners for contradictory instructions. Confirm that no permanent
page links this plan, deleted plans, or investigation records. Follow
[records guidance](records/AGENTS.md) if a separate associated record actually
becomes necessary; ordinary drafting notes can remain here.

Closeout requires the completed guide, working discovery links, the P4 exercise
record, actual check results with their scope, and disposition of every material
open question. Preserve any required evidence and give deferred work a named
destination before retiring the plan. Do not mark this work complete merely
because a prose draft exists or mechanical checks pass.

## Execution checkpoint

| Stage | State | Evidence or next action |
| --- | --- | --- |
| Preparation | Complete for this first draft | Historical sample and current-source reading recorded above; no runtime verification claimed. |
| P1 | Not started | Refresh at the execution revision; evaluate the candidate advice. |
| P2 | Not started | Resolve scope, ownership and readiness criteria from P1. |
| P3 | Not started | Draft the guide and bounded examples after P2. |
| P4 | Not started | Record planning exercises, review findings and revisions. |
| P5 | Not started | Integrate, run applicable checks and review completion evidence. |

During execution, keep this checkpoint current with decisions, source revision,
changed assumptions, evidence references, unresolved work and the next action.
Keep enough context here for a successor to proceed without this conversation.

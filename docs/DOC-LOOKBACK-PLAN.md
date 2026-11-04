# Documentation lookback: sandbox extensions

## Purpose and endpoint

Review the current [ARCHITECTURE](../docs/ARCHITECTURE.md),
[WORKER](../docs/WORKER.md) and [LIMITS](../docs/LIMITS.md) after the
sandbox-extension update. Use Astra subagents for scoping, independent reading
and evidence gathering, with the coordinating agent reviewing each handoff.

ARCHITECTURE and WORKER should give the shortest clear, cogent account that
still serves their readers. LIMITS should accurately describe current limits
and include any limits the update has introduced or exposed. Shortening must
preserve necessary explanations, qualifications and evidence distinctions;
there is no word-count target.

The working bias is that ARCHITECTURE and WORKER may carry too much explanatory
weight, while LIMITS may have undiscovered or under-articulated constraints.
Use that bias to direct attention, not to predetermine findings. Assess authored
and script-generated prose as one account: a resolving citation may establish
that a source exists without establishing the claim, and generated text still
has to cohere for its reader.

The initial review ends with an evidence-backed discussion between the user
and the coordinator about whether fixes are needed and where they belong.
Possible outcomes include documentation changes, implementation changes, coordinated
simplification, retaining the current material, or further investigation.
An unclear or inaccurate passage does not establish which of those is right.
Do not implement proposed fixes during the initial review. After any agreed
documentation changes, a final reading pass assesses every candidate document,
including unchanged ones, using a fresh reader followed by a skeptical assessor.
The required outflow is one `READER-OUTFLOW-PLAN.md` at the repository root,
recording decisions and separately assigned implementation work. Completing the
lookback does not require completing every remedy it uncovers.

This file is the execution plan. Writing it does not start the review.

## Roles and working rules

Use `gpt-6-astra` for every specialist subagent. Start each new role with a
fresh context (`fork_turns="none"`) and an explicit task packet, so readers do
not inherit the coordinator's conclusions or another agent's investigation.
Scoper, consistency and investigator packets include the applicable repository
guidance, baseline, assigned scope, allowed sources, questions and return format.
Stage 2 document readers and the first reader in each stage 5 pair instead
receive materials and tasks in the sequence below. Keep the same agent and its
task history throughout that sequence; a fresh context is required at the start
of the role, not between its onramp, document use and questioning. The second
stage 5 reader receives the first reader's report and the document as specified
there; its assessment is deliberately informed by that report.

The coordinator owns scope decisions, handoff review, onramp preparation, work
tasks, prodding questions, finding consolidation, investigation assignments and
the final presentation. An Astra supervisor handling dispatch may also assess
claims, inspect evidence, question findings and raise issues with the user. If
dispatch is delegated, the main session relays that supervisor's substantive
questions and judgments. Keep the user involved in consequential uncertainty,
verification tradeoffs and decisions to stop unproductive lines of inquiry;
routine choices remain with the supervisor.

Agents return findings to the coordinator; they do not edit the reviewed
documents or shared source files. Region markers are references in a report,
not inserted annotations.

Use the available concurrency without weakening the handoff gates. Start the
ARCHITECTURE scoper, WORKER scoper and LIMITS reader as capacity permits. As
reviewed scopes become ready, start fresh ARCHITECTURE and WORKER readers.
Batch independent investigations within the available slots, accounting for
any slot occupied by a separate supervisor.

Read [README](../README.md), [root guidance](../AGENTS.md),
[planning guidance](../CONTRIBUTING.md#planning-a-change) and
[documentation guidance](../docs/AGENTS.md) before execution. This preparation
applies to the coordinator, scopers, consistency reader and investigators.
For staged document readers, the coordinator handles repository preparation and
supplies the applicable working constraints without a broad orientation packet.
Record any guidance or surrounding context the reader actually receives; do not
describe a reader exposed to it as uninformed. Investigators also read the
guidance for the component or tests they inspect. Preserve the repository's
distinctions between observations, predictions, effects and
attribution throughout the review.

## Reader audience and staging

Assume ordinary familiarity with processes, file descriptors, IPC and sandbox
policies. Do not assume knowledge of PW terminology, internal protocols,
lifecycle states or particular native sandbox APIs. Use these primary jobs as
the standard for relevance and necessary explanation:

| Document | Primary reader | Job the document should enable |
| --- | --- | --- |
| ARCHITECTURE | A contributor or technical reviewer orienting to PW | Trace a specimen through processes and channels, understand responsibilities and ordering, and locate boundaries a proposed change would affect. |
| WORKER | A contributor implementing or reviewing a native operation | Trace resources and authority through acquisition, use and release, and assess what the resulting observations establish. |
| LIMITS | A specimen author or someone interpreting results | Determine whether a specimen fits supported bounds, understand how counts and budgets apply, and interpret refusal, exhaustion, truncation and unavailable evidence. |

LIMITS also serves maintainers through its implementation and evidence grounding;
source inspection should not be necessary to understand its operational account.
Give readers the general role and background. Keep specific expected takeaways
in the coordinator's assessment notes rather than in their task prompts.

Use a short work history to acclimate readers to PW's setting and vocabulary.
This is practical preparation, not a controlled experiment in comprehension.
The coordinator chooses the tasks, questions and amount of assistance; no fixed
question bank, scoring rubric or prompt-count threshold is required. Use
read-only tasks and existing examples or observations. Onboarding does not
authorize native trials, implementation changes or additional equipment.

### Prepare the reader's work

Prepare a small onramp packet and a consequential work task for each document.
They may be two steps of one problem, provided the need checkpoint precedes
access to the target document.
Record the materials, their source state, the intended familiarity and which
facts the target document is expected to supply. Keep the target document,
pre-marked regions, scoper judgments, change brief and expected answers out of
the onramp. Avoid using implementation or test source to supply the explanation
being reviewed. If the onramp necessarily teaches part of it, record that overlap
and limit the conclusions drawn about the document's contribution.

For example, an ARCHITECTURE reader might inspect an ordinary specimen and reply
before helping a teammate trace responsibility for a partly reported run. A
WORKER reader might inspect an operation's request and observations before
reviewing a proposed resource-use sequence. A LIMITS reader might assemble a
small specimen from an example before assessing an expansion near several bounds.
These are task shapes, not prescribed prompts or instructions to implement them.

### Stage the interaction and intervene deliberately

1. **Onramp.** Let the fresh reader complete the small orientation task using
   only its packet. Clarify the assignment or missing materials as needed without
   teaching the target explanation. Discard its output as a product deliverable,
   but retain it and the interaction as review evidence. Continue with that agent.
2. **Need checkpoint.** Give the consequential work task and ask for its tentative
   approach and missing information before supplying the document. Permit an
   explicit inability to answer. If the onramp already supplied the whole answer,
   record that overlap and adjust the task if useful. Do not build a succession
   of onboarding exercises merely to isolate the document's contribution.
3. **Document use.** Supply the target document and let the agent use it to do the
   work. Initially withhold the scope map and location-specific questions. Capture
   its work result and initial understanding before directing attention to the
   pre-marked areas. Stage 2 permits reader-facing documentation links with their
   use recorded; stage 5 uses the restricted artifact described below.
4. **Supervisor questioning.** After that checkpoint, introduce questions about
   the accepted scope and pre-marked regions where applicable. The supervisor
   chooses content and follow-ups from the task result, scope map and unanswered
   questions. Ask for the reader's understanding and its basis before supplying
   a correction. A nearby variation of the task may help test whether that
   understanding supports another decision. LIMITS has no preliminary exclusion
   map; its entries, omissions and the reader's work supply the question targets.
5. **Assessment.** Complete the stage-specific ledger or reader report, separating
   the initial work from understanding reached after prompts or explanations.
   Stage 2's full coverage obligations remain; success on one task does not
   establish that every selected unit communicates successfully.

Usually capture the first work result before prodding, but assist during document
use when useful. Keep the same agent and preserve enough of the initial answer
and consequential interventions to distinguish initial, prompted and taught
understanding. The interaction history is the record; summarize only what bears
on a finding rather than maintaining a separate entry for every ordinary cue.

Understanding reached with assistance is acceptable review evidence, and needing
a prompt is not itself a documentation defect. The supervisor judges whether the
reader needed ordinary orientation or a reference detail, or whether the document
obscured a distinction essential to its job. An explicit correction cannot show
that the document communicated the point unaided. Use that distinction to assess
material confusion, without making unassisted performance a pass/fail gate.

## 0. Establish a shared baseline

The coordinator prepares a short, neutral change brief before dispatch:

- Identify the pre-update comparison point and the current revision. Include
  relevant committed, staged and unstaged work; `git diff HEAD` alone may omit
  much of the update. Resolve the boundary from history and the update's
  existing planning or acceptance records. If plausible boundaries materially
  change the review scope, ask the user to resolve that ambiguity.
- Record the exact reviewed state, including file hashes for the three
  documents and relevant uncommitted inputs. Do not reset, stage or otherwise
  alter existing work to obtain a baseline. If files change during the review,
  identify affected findings and refresh their review before accepting them.
- Describe the changed mechanisms and affected paths without evaluating their
  quality. Include indirect effects on authority, resource lifetime,
  orchestration, ordering, transport and evidence where the update touches them.
- Compare each document's introduction and documentation-index description with
  the primary reader and job above. Record a consequential mismatch as a review
  question rather than silently changing the audience to fit the existing prose.

Record source ownership for later investigations. Both ARCHITECTURE and WORKER
mix authored content with regions and scalar spans maintained by
[generate_architecture.py](../docs/generate_architecture.py), using
[architecture.json](../docs/architecture.json) and related inputs. LIMITS mixes
authored prose with records rendered from [limits.json](../docs/limits.json)
by [generate_limits.py](../docs/generate_limits.py); shared material is copied
into [PolicyWitness.md](../docs/PolicyWitness.md). Review the rendered account,
but identify the owning input before proposing any edit. Generated status is
not a reason to exempt content from scrutiny.

Gate: both scopers receive the same change brief and baseline. Staged readers
receive baseline identifiers and a general work role, without speculative
findings or the change brief before their initial document-use result.

## 1. Establish and review scope

### A. ARCHITECTURE scoper

One Astra agent reads the whole document and identifies the regions relevant
to the sandbox-extension changes. Include unchanged passages whose claims may
have become affected, along with context needed to understand selected material.

Return an inclusion map. Each entry has a heading or anchor, baseline line
range, short opening and closing text, and a reason for inclusion. Identify
relevant figures, captions, table rows and generated region or node/edge IDs.
Distinguish substantive review regions from surrounding reading context.
Explain any consequential decision to leave related material outside scope.
The map may nominate questions to probe later, but does not prescribe answers
or an editorial verdict for the eventual reader.

### B. WORKER scoper

One Astra agent reads all of WORKER and returns a small, conservative exclusion
list. Every exclusion identifies its boundaries in the same format and explains
why the update cannot materially affect its claims or their explanation.
Cross-cutting uncertainty is a reason to retain a region. An empty exclusion
list is acceptable. Everything not excluded remains in substantive scope.

### Coordinator gate

Review both maps for missing dependencies, overbroad inclusions, unsafe
exclusions and sufficient context. Revise or request clarification before using
the accepted map to prepare the fresh reader's assignment. Keep the map with
the supervisor through onboarding and the first document-use result. At the
questioning stage, pass its boundaries and scope rationale, not an editorial
verdict from the scoper.

Boundaries remain provisional: readers can challenge an exclusion or nominate
adjacent material. The coordinator resolves those requests and records the
result rather than silently widening or narrowing the assignment.

LIMITS has no exclusion pass. Its reader covers the whole document and can
begin its staged onramp while the other scopes are being established.

## 2. Read the documents independently

### A. ARCHITECTURE and WORKER: defend every substantive unit

Assign one fresh Astra reader to each accepted scope and use the staged onramp
above. Supply the complete target document for its work task; the accepted map
governs the later substantive audit, not what it may read for context. Its first
work result establishes what it could understand and do before location-specific
prodding. It may follow reader-facing documentation links, recording when an
explanation depends on another document, but must not use implementation or test
source to repair an explanation in its head. Factual uncertainty becomes a
verification question for stage 3.

After capturing that result, the supervisor probes pre-marked regions and gaps
revealed by the task, then has the same reader complete the coverage ledger.
The criteria below govern that audit; do not front-load them as a documentation
critique assignment during onboarding or the initial work task.

Account for every line in scope, but evaluate sentences, claims, paragraphs,
table rows and diagram elements as meaningful units. Physical Markdown wrapping
does not define a claim. Evaluate structural markup through its role in the
rendered document rather than demanding prose justifications for blank lines.

For each unit, determine:

1. What does it help the intended reader understand or do?
2. Is it clear and cogent, with intelligible terms, referents and connections?
3. Is its factual claim or qualification sufficiently explicit to be checked?
4. Is it useful here, and does this document own that explanation?
5. Even if clear and useful, is it needed? Could removal, combination, a shorter
   formulation or a precise link preserve everything necessary?
6. Does it duplicate, obscure or contradict nearby prose, a figure or a table?

Assess paragraphs in context: a sentence may supply a premise or transition
whose value appears in the next paragraph. Flag essential missing explanation
as well as unnecessary text. Do not reward terseness that forces the reader to
reconstruct an invariant or loses an important qualification.

Return a coverage ledger covering every selected region. Consecutive units may
share a retention rationale only when they serve the same identifiable purpose.
For questioned units, provide precise locations, the reader's problem, why it
matters and the question that would resolve it. Keep a proposed edit distinct
from the finding; drafting replacements is optional at this stage. Associate
findings with the initial task result or later prompt/response where applicable.
A ledger judgment is not itself evidence that the initial task encountered that
passage or misunderstanding.

### B. LIMITS: accuracy and missing coverage

The LIMITS reader uses the same onramp, initial work result and questioning
sequence, followed by a different audit remit. Inventory every current entry
and the shared explanations, interactions, premises and coverage claims around
the tables. Record the meaning of each limit: value or derivation, unit,
counting rule, scope, enforcement point, control, boundary consequence and
stated evidence. Mark inapplicable fields explicitly rather than inventing them.

Identify suspected stale values, ambiguous counts, obsolete entries, missing
qualifications and gaps in the account. Classify constraints where useful as
platform constraints, implementation restrictions or boundaries of available
evidence; a single entry can involve more than one category.

Perform a separate coverage pass using the change brief, supplied after the
initial work result, and documented request and execution paths. Ask what could
now refuse a request, constrain a resource
or lifetime, exhaust a budget, truncate transport or evidence, or leave an
observation unavailable. Treat proposed missing limits as hypotheses to check,
not as new documented guarantees. Preserve existing questions about unaffected
entries too: the entire current LIMITS document is in scope.

This initial pass uses the documents and their citations as a map, not as proof
of current behavior. Apparently correct entries still need grounding in stage
3. Return an entry ledger and a separate list of possible omissions, with the
implementation or observation needed to settle each question.

### C. Cross-document consistency

After reviewing the individual reports, assign a fresh Astra reader a consistency
pass across all three documents. This is a check of their relationships, not a
second line-by-line review of excluded material. Check terminology, ownership
of explanations, contradictory claims, unhelpful duplication, link dependencies
and gaps created by proposed shortening or relocation.

Have this reader form an initial view from the documents before consulting the
other reports. Return linked findings and any justified request to reopen scope.

### Coordinator gate

Check that the ledgers cover their assigned scopes and that retention decisions
also address necessity. Separate findings about clarity, factual accuracy,
omission, redundancy and placement; one passage may raise several questions.
Keep editorial observations distinct from unverified claims about behavior.
Check the staging records as well: what the onramp supplied, what the reader
initially concluded, which regions were actually encountered, and what changed
after prodding or correction. Successful prompted answers do not erase earlier
confusion, and an unvisited region is not an observed reading failure.

Consolidate related findings into investigation questions while retaining the
original locations and minority views. Do not send several agents to investigate
the same mechanism independently unless an unresolved disagreement warrants it.
Include verification of every LIMITS entry and the search for missing limits,
even where the first reader reported no apparent problem.

## 3. Investigate with evidence

The supervisor chooses the depth of factual verification for ARCHITECTURE and
WORKER. There is no requirement to independently verify every factual claim or
to commission an investigation for every reader objection. Prioritize claims
whose uncertainty could change the reader's understanding, an experimental
conclusion or the remedy, including claims the readers accepted too readily.
The supervisor may inspect evidence directly, group related questions, dismiss
minor concerns with a reason, or dispatch Astra investigators for deeper work.

Keep a brief account of what was checked, what was relied on and what remains
uncertain; do not imply comprehensive verification where it was not performed.
Raise consequential gaps or expanding investigations with the user. The supervisor
and user may stop a blind alley or repeated reconsideration of a minor point
without forcing agent consensus. LIMITS retains comprehensive grounding of its
current entries and a separate search for missing limits. Assign that coverage
work to investigators even where the initial reader raised no objection.

Each task packet states the baseline, exact passages, open question, related
findings and what evidence would resolve the uncertainty. Avoid framing it as
an instruction to prove the reader right.

Investigators consult the relevant implementation, contracts, fixtures, tests
and reusable observations. For purely editorial problems, evidence can be the
document's stated audience, duplicated explanation or an actual reader dependency;
code inspection is only useful when it bears on the question. For behavioral
claims, a manifest, comment, resolving citation or passing generator check is
not sufficient evidence by itself.

For LIMITS, check values and units against their implementation owners, then
check counting, boundary behavior, controls and consequences separately. Trace
affected paths to discover restrictions missing from the document. A constant
comparison does not establish behavior at the boundary, and a shortened timeout
test does not establish the production duration. Reuse applicable evidence only
when its revision, artifact and conditions support the current claim. Describe
remaining uncertainty explicitly. Claims about macOS guarantees need suitable
primary sources or appropriately qualified observations, not generalization
from one successful run.

An investigation returns:

- Finding IDs and precise document locations, including affected generated IDs.
- The claim, observed or implemented behavior, and the relationship between them.
- Source paths and symbols; relevant test assertions, commands and evidence
  locations; and what each item does and does not establish.
- A disposition: confirmed problem, unsupported concern, or unresolved question,
  with the reason and any evidence that conflicts with the conclusion.
- Plausible remedies and their consequences: documentation, implementation,
  coordinated simplification, retaining the current state, or further evidence.
- The actual edit owner for each remedy, affected consumers and documentation,
  and the validation that a later change would require.

Do not let an investigator choose a remedy merely because it is the smallest
patch. In particular, distinguish a misleading statement from an implementation
that fails a useful intended contract, and consider whether both can be simplified.

### Verification and evidence handling

Choose focused checks that answer the investigation question. Read
[test guidance](../tests/AGENTS.md) and the owning suite reference before running
them. Use `tests/run.sh`, fresh managed `tests/out/runs/<name>` evidence, and the
repository's evidence-reuse and cleanup rules. Keep builds and tests serialized
within a checkout; never unlink `tests/.checkout.lock`. Source-reading agents
can continue concurrently. Preserve investigated artifacts when retrying an
environmental failure under the documented automation-sandbox guidance.

New checks or fixtures needed to resolve a question belong in an isolated
investigative workspace; do not fold speculative fixes into the reviewed state.
Record evidence gaps when a check cannot yet be performed.

For eventual fixes, identify the appropriate generator and semantic checks.
The [generator contracts](../tests/suites/source_drift/README.md#generator-contracts)
explain mechanical ownership and freshness checks. Limit changes additionally
follow [limit verification](../tests/AGENTS.md#verify-a-limit-change), including
implementation-value checks and honest behavior coverage. Changes to the worker
wait, release store or query eligibility require
`witness_contract/order_barrier_mutations`. These are validation obligations for
the relevant remedy, not a reason to run the whole battery for this plan.

## 4. Reconcile and decide with the user

The coordinator reviews the investigations, resolves duplicate or conflicting
claims, and asks focused Astra follow-ups where evidence remains insufficient.
Recheck cross-document consistency in light of the established facts and remedy
options. If a proposed deletion or relocation removes an explanation another
document needs, bring that dependency into the same decision.

Start the root `READER-OUTFLOW-PLAN.md` as the single decision and follow-up
plan, then update it with the final reader pass. Present a concise account, with
supporting review records and evidence referenced where needed:

- Accepted scopes, baseline and any scope changes made during review.
- Findings grouped by the decision needed, with exact locations and evidence.
- The reader tasks, onboarding exposure and interventions supporting those
  findings, distinguishing initial understanding from prompted or taught answers.
- For LIMITS, the outcome for each existing entry and each proposed addition,
  separating verified facts from remaining uncertainty.
- Remedy options, the coordinator's recommendation and its rationale, the
  owning inputs or code, and consequential validation requirements.
- Dismissed concerns and unresolved questions, so absence from the proposed
  fixes cannot be mistaken for lack of review.

The user and coordinator decide together whether fixes are warranted and where
they belong, including which documentation changes to make before stage 5.
Keep implementation repairs as separately assigned work in the outflow plan,
including consequential defects. Review closure does not depend on completing
that work. Record the user's accepted deferral, the current behavior and its
effect on the documentation, the owner, the proposed work and its acceptance
checks. Do not silently turn an implementation defect into a documentation fix
or imply that closing the review validates defective behavior.

Accepted documentation must accurately and usefully describe the current system,
including relevant limitations. If an unresolved defect prevents that, keep the
affected document's acceptance open and state what must be resolved. Distinguish
the completion of the review from document acceptance and implementation follow-up.

The initial review is ready for that discussion when every selected ARCHITECTURE
and WORKER unit has a recorded disposition, every LIMITS entry has an evidence
assessment, the missing-limit search and consistency pass are complete, and
every investigation is either resolved or explicitly bounded by what remains
unknown. Do not present an unresolved item as a verified claim or a required fix.

## 5. Read the candidate documents with paired readers

Run this pass for all three documents, even if the initial review recommends
no documentation changes. Run it after stage 4 and any agreed documentation
changes and validation; if none are needed, proceed directly from stage 4.
It covers whole documents, including material excluded from the detailed review.

Allocate two Astra readers per document. The first starts fresh from earlier
review conclusions and uses the staged onramp and work task. The second starts
in a separate context, reads the same document and the first reader's report,
and assesses that report skeptically in either direction. Neither participates
in the earlier review. These are whole-document readings, not line-by-line
audits or assignments to rewrite the prose. Run each pair sequentially; different
documents' pairs may progress concurrently as slots permit.

### Prepare a faithful, isolated artifact

The coordinator records the candidate source state and prepares one complete
artifact for each document, after any required regeneration. Use flat Markdown
when it preserves the reading experience; use a self-contained rendered PDF
when figures or layout are needed to understand the account. Preserve headings,
tables, examples, figures, captions, qualifications and their order. Verify
that conversion has not omitted content, clipped tables or lost diagrams.

Remove non-visible generation comments from a Markdown reading copy while
retaining their rendered content, including scalar values. Do not simplify or
annotate the prose, add explanations, or identify which passages were generated
beyond what the document itself already tells its readers. Keep visible links,
but readers may not follow them outside the artifact. Internal navigation is
allowed. Record the artifact's format and hash alongside the source state.

After its recorded onramp and need checkpoint, give the first reader its artifact
and work task. Beyond the bounded onboarding packet, do not supply the repository,
other documents, scope maps, change brief, prior findings, generator inputs or
intended answers. The first reader may inspect its artifact and retained task
history but may not consult external sources. Isolation here means controlled
materials and no inherited investigation conclusions, not an absence of prior
task context.
The coordinator keeps a short account of the essential takeaways established by
the earlier review, written before seeing these reports and withheld from readers.

### First reader: use the document and explain its account

Use the primary role, background and task history defined above. Ask for a
natural reading with limited attention, without reconstructing missing premises
or studying every citation. Do not ask the agent to pretend to be unintelligent,
manufacture mistakes, or find a quota of defects. Assess how well the document
supports its reader's work and where it might invite a plausible misunderstanding,
especially a confident one.

Within the staged sequence, separate these document-use checkpoints:

1. **First impression.** Ask for a skim of the title, opening, headings and
   prominent summaries or figures. Have the reader explain in at most 150 words
   what the document is for, its central account, and what they would expect to
   understand or do after reading it. Capture that response before the next prompt.
2. **Work result.** Let the reader use the artifact to complete its work task.
   Capture the answer before directing it to particular passages or correcting
   the first impression.
3. **Whole-document account.** Ask for one ordinary read of the whole artifact
   and an account in its own words, including what changed from its first
   impression. This supplies the whole-document assessment even when the work
   task needed only part of the document. Capture it before targeted questioning.

The supervisor then asks prodding questions about relevant pre-marked or revised
areas and uncertainties in these answers. Choose the questions in light of the
reader's work; no prescribed question content is required. Use passage references
without revealing the earlier reader's diagnosis or the coordinator's expected
answer. Record any earlier intervention and its checkpoint as in stage 2.

Keep the prompts neutral about the content. Let readers identify the document's
main distinctions rather than coaching them to repeat the project's intended
invariants. Evaluate coherence, progression, emphasis and the visibility of
qualifications. A linked reference can appropriately supply detail; flag a
dependency when it prevents understanding the document's central account.

### First reader's report

The first reader returns a short report containing:

- Their initial and settled understanding, with uncertainty stated explicitly.
- Their work result, the onramp's contribution and changes following specific
  prompts or corrections, with references to the recorded interaction.
- Whether the document forms a coherent whole and where its main thread is lost.
- The few most consequential plausible misunderstandings, if any. For each,
  state the interpretation, the heading or short passage that invites it, and
  whether the correction is absent, buried, encountered too late or difficult
  to connect to the original claim. Distinguish an actual first impression from
  a hypothetical misunderstanding noticed during the fuller read.
- Any essential outside knowledge they needed but the isolated document did
  not provide. Separate this from optional detail they would seek elsewhere.

### Second reader: assess the first report skeptically

Give a separate Astra reader the same artifact, the first report, and enough of
the original task and intervention history to assess its claims fairly. Keep
earlier investigation conclusions and the supervisor's intended answers out of
this packet. The second reader may inspect those supplied materials, with the
same restriction on outside sources. It does not repeat the onramp or represent
an independent fresh-reader result; exposure to the first report is deliberate.

Ask whether the first reader's account and concerns are supported by the document.
Skepticism works in both directions: it may reject an alleged ambiguity, confirm
that a problem matters, expose an overlooked limitation, or challenge an
unwarranted assurance that the document is clear. Look for charitable readings
and contrary passages as well as evidence of real confusion. Do not require
disagreement, a quota of findings, or defense of the existing prose.

Return a short assessment of the material claims, with document locations,
reasons for agreement or disagreement, and the likely consequence for the
reader's job. Identify minor or unsupported concerns that merit no further work.

### Supervisor assessment

The supervisor compares both reports with the task history and available evidence,
and may question either reader. It can resolve or dismiss points directly, ask
for a focused investigation, or discuss consequential uncertainty with the user.
Agreement between readers is not proof; disagreement does not require repeated
rounds until they converge. Stop unproductive or disproportionate follow-ups with
a brief reason. Distinguish document problems from task design, artifact conversion,
ordinary prerequisites and unsupported reader inferences.

Treat the pair as evidence about possible confusion and the strength of the first
report, not a measured rate of human misunderstanding or comprehensive factual
verification. Keep question content and the depth of follow-up with the supervisor.

Bring consequential findings to the user with evidence and remedy options, then
decide together which warrant changes. The supervisor chooses whether a material
change needs another reading; minor edits do not automatically restart the pair.
When a fresh first impression is needed, use a new reader and a recorded onramp.
Keep any assessment by an already informed reader labeled as such. Reuse the
unaffected documents' results and record remaining uncertainty in the outflow plan.

## 6. Finish the single outflow plan

Complete `READER-OUTFLOW-PLAN.md` at the repository root. It is the review's
required handoff, even if no documentation changes are recommended. Incorporate
the stage 4 decisions and both readers' material findings rather than creating
separate action plans for individual agents or documents.

Keep it usable by someone who did not take part in the review. Include the
reviewed baseline and scope, documentation changes made or still proposed,
the rationale and evidence for accepted decisions, dismissed concerns that
matter to those decisions, and unresolved questions. Summarize the actual
verification coverage for ARCHITECTURE and WORKER and the comprehensive LIMITS
assessment without implying that citation checks established behavior.

For each accepted implementation follow-up, name the owner, current defect,
affected documentation or observations, proposed approach, dependencies and
acceptance checks. Record the user's agreement to defer it. Distinguish review
completion, each document's acceptance and outstanding implementation work.
Supporting reader records and managed test evidence remain evidence referenced
by this one plan. The review may close with accurately documented limitations
and assigned implementation work; it must not silently discard consequential
findings or describe deferred repairs as complete.

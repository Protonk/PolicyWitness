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

The initial review ends with an evidence-backed discussion between the user
and the coordinator about whether fixes are needed and where they belong.
Possible outcomes include documentation changes, implementation changes, coordinated
simplification, retaining the current material, or further investigation.
An unclear or inaccurate passage does not establish which of those is right.
Do not implement proposed fixes during the initial review. After agreed changes
have been implemented, a final isolated reading pass assesses whether each
revised document communicates a coherent account to a hurried reader.

This file is the execution plan. Writing it does not start the review.

## Roles and working rules

Use `gpt-6-astra` for every specialist subagent. Start each new role with a
fresh context (`fork_turns="none"`) and an explicit task packet, so readers do
not inherit the coordinator's conclusions or another agent's investigation.
For stages 0–4, packets include the applicable repository guidance, baseline,
assigned scope, allowed sources, review questions and required return format.
Stage 5 readers receive only their isolated document and a neutral reading task;
the coordinator handles repository guidance and artifact preparation for them.

The coordinator owns scope decisions, handoff review, finding consolidation,
investigation assignments and the final presentation. Agents return findings
to the coordinator; they do not edit the reviewed documents or shared source
files. Region markers are references in a report, not inserted annotations.

Use the available concurrency without weakening the handoff gates. With three
subagent slots, start the ARCHITECTURE scoper, WORKER scoper and LIMITS reader
together. As reviewed scopes become ready, start fresh ARCHITECTURE and WORKER
readers. Run later investigations in batches of up to three independent tasks.
Do not hold an unused slot while an unrelated task can proceed.

Read [README](../README.md), [root guidance](../AGENTS.md),
[planning guidance](../CONTRIBUTING.md#planning-a-change) and
[documentation guidance](../docs/AGENTS.md) before execution. This preparation
applies to the coordinator and stages 0–4 agents, not the isolated readers.
Investigators also read the guidance for the component or tests they inspect. Preserve the
repository's distinctions between observations, predictions, effects and
attribution throughout the review.

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
- Establish each document's purpose from its introduction and the documentation
  index: ARCHITECTURE explains a run and its boundaries; WORKER explains the
  worker's resources, authority and experimental constraints; LIMITS explains
  capacities, budgets, boundary behavior and their grounding.

Record source ownership for later investigations. Both ARCHITECTURE and WORKER
mix authored content with regions and scalar spans maintained by
[generate_architecture.py](../docs/generate_architecture.py), using
[architecture.json](../docs/architecture.json) and related inputs. LIMITS mixes
authored prose with records rendered from [limits.json](../docs/limits.json)
by [generate_limits.py](../docs/generate_limits.py); shared material is copied
into [PolicyWitness.md](../docs/PolicyWitness.md). Review the rendered account,
but identify the owning input before proposing any edit. Generated status is
not a reason to exempt content from scrutiny.

Gate: both scopers receive the same change brief and baseline. Readers receive
the baseline and document purpose, without speculative findings from the brief.

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

### B. WORKER scoper

One Astra agent reads all of WORKER and returns a small, conservative exclusion
list. Every exclusion identifies its boundaries in the same format and explains
why the update cannot materially affect its claims or their explanation.
Cross-cutting uncertainty is a reason to retain a region. An empty exclusion
list is acceptable. Everything not excluded remains in substantive scope.

### Coordinator gate

Review both maps for missing dependencies, overbroad inclusions, unsafe
exclusions and sufficient context. Revise or request clarification before
handing the accepted map to a fresh reader. Pass the scope rationale, not an
editorial verdict from the scoper.

Boundaries remain provisional: readers can challenge an exclusion or nominate
adjacent material. The coordinator resolves those requests and records the
result rather than silently widening or narrowing the assignment.

LIMITS has no exclusion pass. Its reader covers the whole document and can
begin while the other scopes are being established.

## 2. Read the documents independently

### A. ARCHITECTURE and WORKER: defend every substantive unit

Assign one fresh Astra reader to each accepted scope. Their first judgment is
whether the documentation communicates successfully on its own. They may follow
reader-facing documentation links, recording when an explanation depends on
another document, but must not use implementation or test source to repair an
explanation in their heads. Factual uncertainty becomes a verification question
for stage 3.

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
from the finding; drafting replacements is optional at this stage.

### B. LIMITS: accuracy and missing coverage

The LIMITS reader has a different remit. First inventory every current entry
and the shared explanations, interactions, premises and coverage claims around
the tables. Record the meaning of each limit: value or derivation, unit,
counting rule, scope, enforcement point, control, boundary consequence and
stated evidence. Mark inapplicable fields explicitly rather than inventing them.

Identify suspected stale values, ambiguous counts, obsolete entries, missing
qualifications and gaps in the account. Classify constraints where useful as
platform constraints, implementation restrictions or boundaries of available
evidence; a single entry can involve more than one category.

Perform a separate coverage pass using the change brief and documented request
and execution paths. Ask what could now refuse a request, constrain a resource
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

Consolidate related findings into investigation questions while retaining the
original locations and minority views. Do not send several agents to investigate
the same mechanism independently unless an unresolved disagreement warrants it.
Include verification of every LIMITS entry and the search for missing limits,
even where the first reader reported no apparent problem.

## 3. Investigate with evidence

Assign Astra investigators by consolidated question or closely related group
of questions. Every problem receives an investigation; grouping reduces
duplicate work without dropping findings. Assign a separate coverage task for
potential undocumented limits if it does not fit the existing groups.

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

Present a concise decision packet, with detailed ledgers available behind it:

- Accepted scopes, baseline and any scope changes made during review.
- Findings grouped by the decision needed, with exact locations and evidence.
- For LIMITS, the outcome for each existing entry and each proposed addition,
  separating verified facts from remaining uncertainty.
- Remedy options, the coordinator's recommendation and its rationale, the
  owning inputs or code, and consequential validation requirements.
- Dismissed concerns and unresolved questions, so absence from the proposed
  fixes cannot be mistaken for lack of review.

The user and coordinator decide together whether fixes are warranted and where
they belong. Implementation follows as separately agreed work.

The initial review is ready for that discussion when every selected ARCHITECTURE
and WORKER unit has a recorded disposition, every LIMITS entry has an evidence
assessment, the missing-limit search and consistency pass are complete, and
every investigation is either resolved or explicitly bounded by what remains
unknown. Do not present an unresolved item as a verified claim or a required fix.

## 5. Read the revised documents in isolation

Run this pass near the end, after the substantial agreed changes and their
validation, before accepting the revised documentation. It evaluates whole
documents, including material excluded from the earlier detailed review.
Assign one fresh Astra agent per document; none may have participated in the
earlier review. These agents act as readers, not editors or implementation
auditors. They do not produce line-by-line judgments or replacement prose.

### Prepare a faithful, isolated artifact

The coordinator records the revised source state and prepares one complete
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

Give each agent only its artifact and the reading task below. Do not supply
the repository, other documents, scope maps, change brief, prior findings,
generator inputs or intended answers. Readers may inspect their assigned
artifact but may not consult external sources. The coordinator keeps a short
account of the essential takeaways established by the earlier review, written
before seeing these reports and withheld from the readers.

### Calibrate the reading task

Use a technically competent reader who is new to PolicyWitness, has ordinary
background knowledge appropriate to the document's audience, and has limited
attention. Ask for a natural reading, without reconstructing missing premises
or studying every citation. Do not ask the agent to pretend to be unintelligent,
manufacture mistakes, or find a quota of defects. The question is whether the
document makes a plausible misunderstanding easy, especially a confident one.

Use two sequential prompts with each reader:

1. **First impression.** Ask for a skim of the title, opening, headings and
   prominent summaries or figures. Have the reader explain in at most 150 words
   what the document is for, its central account, and what they would expect to
   understand or do after reading it. Capture that response before the next prompt.
2. **One ordinary read.** Ask the reader to read the whole artifact once and
   explain its account in their own words. Ask what changed from the first
   impression, where the explanation became hard to follow, and which important
   conclusions a hurried reader might draw incorrectly. Do not reveal the
   coordinator's expected takeaways or correct the first impression first.

Keep the prompts neutral about the content. Let readers identify the document's
main distinctions rather than coaching them to repeat the project's intended
invariants. Evaluate coherence, progression, emphasis and the visibility of
qualifications. A linked reference can appropriately supply detail; flag a
dependency when it prevents understanding the document's central account.

### Return and assess the reader's model

Each reader returns a short report containing:

- Their initial and settled understanding, with uncertainty stated explicitly.
- Whether the document forms a coherent whole and where its main thread is lost.
- The few most consequential plausible misunderstandings, if any. For each,
  state the interpretation, the heading or short passage that invites it, and
  whether the correction is absent, buried, encountered too late or difficult
  to connect to the original claim. Distinguish an actual first impression from
  a hypothetical misunderstanding noticed during the fuller read.
- Any essential outside knowledge they needed but the isolated document did
  not provide. Separate this from optional detail they would seek elsewhere.

The coordinator compares these reports with the withheld takeaways and the
verified behavior. Classify issues as document-level confusion, appropriate
prerequisites, artifact-conversion defects, or unsupported reader inferences;
cite the reason rather than treating every reader complaint as a required edit.
Treat these reads as evidence of possible confusion, not a measured rate of
human misunderstanding or another factual verification pass.

Bring consequential findings to the user with evidence and remedy options.
Decide together which warrant changes. If those changes materially alter a
document's explanation, repeat its cold read with a new agent; an agent already
taught the intended account cannot supply a fresh first impression. Reuse the
unaffected documents' results. The final review packet records each document's
reader outcome, any follow-up changes and the disposition of remaining issues.

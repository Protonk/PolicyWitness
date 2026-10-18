# Independent audit of the worker account

Audit the current worker documentation for supported claims and material
omissions. Form your assessment from the document, its machinery, implementation
and evidence. Produce an independent report before receiving earlier reviews or
the coordinator's assessment. This assignment ends at that report.

## Establish the reading context

The coordinator supplies an audit revision and a clean checkout, preferably a
dedicated worktree. Read the root [AGENTS.md](../AGENTS.md) and
[README.md](../README.md), and follow applicable directory guidance as you enter
source, tests or scratch. Confirm the supplied revision with `git rev-parse HEAD`
and inspect `git status --short`. Record the revision and starting status. Resolve
a revision mismatch or tracked changes with the coordinator before auditing;
preserve any existing work.

Use a fresh conversation that has not received the worker documentation plan,
previous reviews or coordination history. During this initial audit, leave
`*-PLAN.md` files, finding registers, previous audit reports, triage and
root-cause-analysis summaries, repair rationales, git history and diffs unread.
This includes interpretive review records under `records/` and `.tmp/audits/`.
Scope searches to the relevant documentation, implementation and checks so that
search results do not import those earlier conclusions.

Cited primary evidence remains available wherever it is stored: inputs, raw
observations, execution metadata, fixtures and assertions. If primary evidence
is bundled with an excluded review, request the underlying artifacts separately.
Record unavailable evidence and any accidental exposure to earlier conclusions,
including when it occurred and which parts of the audit it could affect. Ask
logistical questions as needed; defer comparison with earlier assessments until
your initial report is complete.

## Scope and reading route

Start with [WORKER.md](WORKER.md), including its generated inventory and the
rendered [capability map](worker-capabilities.svg). Inspect the map visually at a
legible scale as well as reading its labels and relationships. Its manifest is
[architecture.json](architecture.json), and its generated graph source is
[worker-capabilities.dot](worker-capabilities.dot). The owning generator is
[generate_architecture.py](generate_architecture.py), with shared helpers in
[generator_common.py](generator_common.py). Follow the worker graph's sources,
checks and relevant generation contracts.

Read the worker account as a whole before tracing individual claims. Then work
in both directions:

- From material statements, inventory facts and graph relationships to the
  implementation, assertions and observations supporting them.
- From worker preparation and launch through execution and exit to the account,
  looking for material operations, resources, branches and failure paths that
  it omits or represents inaccurately.

Follow callers, helpers, admission rules and evidence consumers wherever needed
to establish the worker's behavior and boundaries. Other documents can supply
context and contracts. Keep findings tied to the worker account or the machinery
supporting it; this assignment does not require a general repository audit.

## Assess support and omissions

Evaluate the actual proposition and its stated scope. Distinguish source-derived
facts, controlled observations, broader inferences and unresolved questions.
Inspect the exercised path and assertions behind a cited check, and examine the
conditions and provenance of a credited observation. Assess generator guarantees
from their implementation and controls. Record how far each kind of support
reaches.

Consider prose, inventory and map together. Check whether labels, arrows,
grouping, timing and ownership convey an account supported by the sources, and
whether important conditions remain visible when the parts are read together.
Use precise worker behavior to judge omissions. Explain how an omission would
change a reader's understanding of the instrument or its observations.

All material claims and qualifications are open to scrutiny. There is no target
finding count or expected conclusion. A documented limitation may be accurate
and sufficient. A missing artifact establishes a verification limit; explain
what additional evidence would settle it. Distinguish a demonstrated
contradiction from insufficient support, and substantive ambiguity from a style
preference. Keep optional editorial suggestions separate from material findings.

## Verification and working boundaries

Begin with source inspection and available primary evidence. Run relevant
existing checks when they would resolve uncertainty, following
[tests/AGENTS.md](../tests/AGENTS.md), the harness reference and the owning suite's
guidance. Use fresh managed output directories and record exact commands,
configuration, results and evidence locations. Explain evidence applicability
and any execution or equipment limits. Report additional experiments needed to
settle open questions, including the observation that would distinguish the
alternatives.

Keep the audited source, documentation, fixtures and generated artifacts
unchanged. Write only audit notes, the report and outputs belonging to the
selected checks. Propose repairs in the report; implementation and adjudication
belong to a later step. Preserve existing evidence and resource ownership under
repository rules. Do not commit, push or release during this assignment.

## Initial report and stop

Read [.tmp/AGENTS.md](../.tmp/AGENTS.md) before creating a fresh directory at
`.tmp/audits/<audit-id>/`. Save the initial report there as `report.md`. Keep
test evidence in its managed location and cite it from the report. Scratch is
disposable, so deliver the report text to the user as well as saving the file.

Include:

- The audited revision, starting and ending checkout status, reading coverage,
  methods, checks run and evidence used. Identify material areas left unread or
  unverified and any exposure to excluded material.
- Findings with your own stable identifiers. For each, give the document
  location or graph/inventory identifier, the claim or omission, the relevant
  source and evidence locations, your reasoning, the practical consequence for
  the account, confidence and remaining uncertainty. State any proposed
  correction or further verification separately from the demonstrated facts.
- Unresolved questions and missing evidence, with a concrete way to resolve
  each where possible. Keep these distinguishable from established findings.
- Your overall assessment of the account's support and completeness within the
  coverage you actually achieved.

Finish by delivering the report, its path and SHA-256 digest, and the audited
revision. Stop before opening earlier reviews or receiving their findings. Keep
this initial report unchanged once delivered. Any later comparison or revised
assessment belongs in a separate addendum after the user authorizes that stage.

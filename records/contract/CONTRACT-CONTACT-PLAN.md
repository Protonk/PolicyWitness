# CONTRACT.md examination plan

This plan organizes an examination of the public contract,
[docs/CONTRACT.md](../../docs/CONTRACT.md): what it communicates to a
technically competent reader, what its claims establish, how those claims rest
on generation machinery and working code, and whether complexity or misleading
statements can be reduced.

The objective is not a shorter contract or a quota of defects. "This passage is
necessary, correct and adequately supported" is a result, and the plan records
it as one.

Two independent readings supply the material, and both are complete. This plan
defines how they are compared, filtered, acted on and re-examined, and when the
work stops. It contains no finding from either reading.

**Where the work stands** is recorded in
[CONTRACT-LEDGER.md](CONTRACT-LEDGER.md), not here. A coordinator taking over
reads the ledger's stage log first, then the stage it names in this plan.

## Contents

- [Participants](#participants)
- [Subject and baseline](#subject-and-baseline)
- [Artifacts and references](#artifacts-and-references)
- [Stage 1: independent examination](#stage-1-independent-examination)
- [Stage 2: first adjudication](#stage-2-first-adjudication)
- [Stage 3: filter findings](#stage-3-filter-findings)
- [Stage 4: ground and revise](#stage-4-ground-and-revise)
- [Stage 5: second examinations](#stage-5-second-examinations)
- [Stage 6: completion](#stage-6-completion)
- [Decisions reserved for the maintainer](#decisions-reserved-for-the-maintainer)
- [When to reconsider this plan](#when-to-reconsider-this-plan)

## Participants

| Role | Responsibility | Does not |
| --- | --- | --- |
| Experienced reader | Wrote the technical examination. Next: adjudication (stage 2), later review of changes (stage 5). | Edit its report. Author the changes it later reviews. |
| Fresh reader | Wrote the interpretation journal. Next: close-out and answers (stage 2), later a targeted re-reading (stage 5). | Inspect implementation, evaluate the writing, or see the report, the adjudication, the ledger or this plan. |
| Second fresh reader | A reader with no exposure to the original contract or to any artifact of this examination. Used in stage 5 only where independence matters. | Exist before stage 5 decides it is needed. |
| Coordinator | Executes this plan: keeps the ledger, drafts the fresh reader's questions, proposes filter decisions, grounds findings, authors changes, runs verification. | Substitute its own reading for either reader's; its own observations enter the ledger marked as coordinator-origin. |
| Maintainer | Relays tasks to the readers and decides the items under [Decisions reserved for the maintainer](#decisions-reserved-for-the-maintainer). | |

The coordinator has no direct contact with the readers. The maintainer hands
each reader its task, and the reader's output arrives as a file in this
directory. The task sections in stage 2 are written to be handed over: the
experienced reader may be given this whole plan; the fresh reader is given
only the text of its own two task sections.

Independence is kept by discipline, not isolation: every artifact sits in this
directory and any participant could open it. Each task therefore says what its
reader may open, and each output says what its author did open.

## Subject and baseline

The subject is `docs/CONTRACT.md` as last changed by commit `cbf5f298`:
441 lines, blob `bfd2ededcfdeaf801b3f179e38886e9baa55fb7f`. Both readers read
these bytes. Before each stage, run

```sh
git rev-parse HEAD:docs/CONTRACT.md
git log --oneline cbf5f298..HEAD -- docs/CONTRACT.md docs/contract_surfaces.json docs/PolicyWitness.md
```

Other work lands in this repository while the examination runs. If the blob
differs or the log prints anything before stage 4 begins, identify the affected
units below and either have them re-examined or record in the ledger that the
artifacts describe the older text. From stage 4 on, the examination's own
commits appear there; anything else is treated the same way.

The coverage units follow the document's own structure. Line numbers are those
of the baseline; the heading or region marker is the durable name.

| Unit | Extent | Lines | Stamp-hashed |
| --- | --- | --- | --- |
| U01 | Preamble: identity, admission, reuse | 1–20 | no |
| U02 | Surface stamps: prose, generated table, history paragraph | 22–56 | no (table is generated) |
| U03 | `request` region, including "Accepted input contract" | 60–124 | `request` |
| U04 | `policy` region | 126–130 | `policy` |
| U05 | `probes` region | 132–136 | `probes` |
| U06 | `actors` region | 138–142 | `actors` |
| U07 | `envelope` region | 144–148 | `envelope` |
| U08 | `dossier` region | 150–154 | `dossier` |
| U09 | `steps` region | 156–160 | `steps` |
| U10 | `lifecycle` region | 162–166 | `lifecycle` |
| U11 | `equipment` region, including "Actor evidence ownership" | 168–238 | `equipment` |
| U12 | `profile` region | 240–244 | `profile` |
| U13 | `transport` region | 246–250 | `transport` |
| U14 | `refusals` region, including "Structured request refusals" | 252–291 | `refusals` |
| U15 | `installation` region | 293–298 | `installation` |
| U16 | `transport_encoding` region, "Typed response transport" | 300–358 | `transport` |
| U17 | Maintaining the contract | 360–377 | no |
| U18 | Internal host/worker identity | 379–425 | no |
| U19 | Shape goldens | 428–434 | no |
| U20 | Build stamp | 436–441 | no |

"Stamp-hashed" names the surface whose derived stamp depends on the unit's
text. [Stage 4](#what-an-edit-inside-a-region-does) explains why that column
matters for revisions. It also matters for reading: the manifest
[docs/contract_surfaces.json](../../docs/contract_surfaces.json) defines each
surface as its `docs/CONTRACT.md` region together with the
`<!-- BEGIN CONTRACT … -->` regions it names in
[docs/PolicyWitness.md](../../docs/PolicyWitness.md) and the listed goldens.
The examination's subject is the contract document; grounding a finding about
a surface reads the companion regions as part of that surface's definition.

## Artifacts and references

All artifacts live in `records/contract/`. Under the
[records link rule](../AGENTS.md), only this plan links to them; the other
artifacts name one another by path without a link.

| Artifact | Author | State | Changes after acceptance |
| --- | --- | --- | --- |
| [CONTRACT-FIRST-READER-REPORT.md](CONTRACT-FIRST-READER-REPORT.md), the **report** | Experienced reader | Accepted, `c87bfd80` | None |
| [FRESH-ENCOUNTER-JOURNAL.md](FRESH-ENCOUNTER-JOURNAL.md), the **journal** | Fresh reader | Accepted, `214dddd7` | None |
| [CONTRACT-LEDGER.md](CONTRACT-LEDGER.md): stage log, acceptance record, coverage record, findings ledger | Coordinator | Open | Rows gain decisions and status; reasons are never deleted |
| `FRESH-ENCOUNTER-ADDENDA.md` | Fresh reader | Stage 2 | Append-only: a committed section is not edited |
| `CONTRACT-ADJUDICATION.md` | Experienced reader | Stage 2 | Pending items are completed once; nothing else is rewritten |
| Second-examination notes | Each second examiner | Stage 5 | None |

The report's file name and title say "first reader". It is the experienced
reader's technical examination. The fresh reader's artifact is the journal.

Acceptance is a commit. An accepted artifact is not edited afterward: a
correction is recorded in the adjudication, the addenda or the ledger and
points at the passage it corrects. `git log -- <path>` then shows that the
original stands.

No other administrative artifacts are planned. If a need for one appears,
state the need in the ledger before creating it.

References used across the artifacts:

| Form | Refers to |
| --- | --- |
| `C:N`, `C:N-M` | Lines of `docs/CONTRACT.md` at the baseline |
| `U01`–`U20` | Coverage units, above |
| `L-01`–`L-48` | The report's line groups (its section 6) |
| `F-01`–`F-20` | The report's findings (its section 7) |
| `J-01`–`J-52` | Journal entries, by the journal's own section numbers |
| `A-01`–`A-52`, `A-S1`… | Adjudication entries; `A-nn` adjudicates `J-nn`, `A-Sn` a silence |
| `R-01`… | Ledger rows |

## Stage 1: independent examination

Complete. The ledger's acceptance record gives the result of each check below
for each artifact, and how each shortfall is handled. The criteria are kept
here because the same checks apply to anything later accepted from a reader.

A reader's artifact is usable when it names the contract revision it read;
covers every unit or says which it did not and why; can be cited entry by
entry; says what its conclusions rest on; says what its author opened; and
arrives in a commit that changes nothing else. The report additionally says
what it did not verify. The journal additionally runs in document order,
gives each belief with its supporting statement and remaining uncertainty,
and leaves an earlier entry in place when a later one revises it.

A shortfall is not repaired by hand. It is recorded against the affected
units. The same reader may fill it in an addendum, provided that happens
before that reader is exposed to anything further; after exposure, the gap is
filled in the next stage and labeled as post-exposure work.

## Stage 2: first adjudication

This stage is read-only with respect to the tree. Its commits add or complete
the adjudication, the addenda and the ledger, and nothing else.

Order of work:

1. The experienced reader's task and the fresh reader's close-out start
   together. Neither needs the other's output to begin.
2. The coordinator accepts the close-out and passes it to the experienced
   reader, who adjudicates the journal's uncertainties from it.
3. The experienced reader delivers the adjudication with its "pending reader
   response" items and its silences list.
4. The coordinator drafts questions from those two lists. The fresh reader
   answers.
5. The experienced reader completes the pending items and adds an entry for
   each silence.
6. The coordinator fills the coverage record.

### Experienced reader, first task: adjudicate the journal

**Purpose.** Examine each of the fresh reader's conclusions against the
contract text and against the technical findings the report already
establishes, and test the report's own expectations about readers against
what a reader actually recorded.

**May open.** The journal; the fresh reader's addenda as they arrive; the
report; the contract at the baseline; the repository, read-only; this plan
and the ledger.

**Begin with a declaration.** State whether the journal, or any account of
it, was seen before this task. The report lists what its author read and the
journal is not on the list; the declaration makes that explicit.

**What the journal contains.** Each of its 52 entries cites a line range and
answers three questions: what the reader now believes, what supports the
belief, and what remains uncertain. Within an entry there are three kinds of
item, and they are adjudicated differently:

| Kind | How to recognize it | How to adjudicate |
| --- | --- | --- |
| Restatement | The reader says what the passage states. Most of each entry. | Once per entry. Check for drift: a restatement that is stronger, weaker, broader or narrower than the text. List each drift as its own item; otherwise record "faithful". |
| Inference | The reader marks it: "I infer", "I expect", "I therefore", "I would not", "I do not take", and the like. | Individually. These are the reader's own conclusions and the main object of this task. |
| Uncertainty | The "What remains uncertain?" paragraph. | From the fresh reader's close-out, which gives the end-of-document status of each. Until it arrives, leave these items open. |

**For each restatement, drift and inference, answer two questions in this
order.**

1. *Reading: does the contract text support the belief?* Judge this from the
   text alone, before consulting implementation knowledge. Cite the passage
   the reader relied on and any other passage that bears on it.
2. *Grounding: where the belief tracks something the contract states, is that
   statement established?* Answer from the report by citing the `L-nn` verdict
   and any `F-nn` it names, and carry forward the report's evidence class and
   its † mark where the support rests on delegated tracing. If the report does
   not cover the point, either inspect now and label the result "new
   inspection, post-exposure", or leave the grounding undetermined and say
   what would determine it. Run no experiment in this stage; the report's
   section 9 lists experiments, and they belong to stage 4.

**Then assign one class.**

| Class | Meaning |
| --- | --- |
| Supported interpretation | The belief is what the text says, and the report found the statement established or had no reason to doubt it. |
| Mistaken reading | The text does not support the belief, the passage that settles it can be quoted, and nothing in the text leads toward the error. |
| Reasonably invited misunderstanding | The belief is not what the contract means or not what the implementation does, and a feature of the text leads toward it. Name the feature: a term used in two senses, a missing antecedent, ordering, an example, a heading, an omission, reliance on knowledge the document does not supply. |
| Unsupported claim | The belief is a faithful reading of a contract statement that the examined evidence neither establishes nor contradicts. The issue lies with the statement, not the reading. |
| Implementation discrepancy | The belief is a faithful reading of a contract statement that the examined source or observed behavior contradicts. |
| Unresolved question | The reading or the grounding cannot be settled with what is available. State what would settle it. |

**For each uncertainty still open at the end of the document** (from the
close-out), say which holds: the contract settles it and the reader missed
where; the contract defers it to a document it names; another repository
document settles it and the contract does not point there; or nothing in the
repository's documentation settles it.

**Separating "mistaken" from "invited".** The adjudicator knows the
implementation, and that knowledge makes text look clearer than it is. Class a
reading as mistaken only when the correcting text can be quoted and the reader
had already passed it, or it stands beside the passage in question. When the
correcting text arrives later, lives in another document, or depends on
repository knowledge, the reading was invited. When in doubt, class it as
invited and record the doubt; stage 3 can still dismiss it, but a finding
dismissed here is lost.

**Two cautions specific to this journal.**

- The fresh reader read the root, `docs/` and `.tmp/` guidance before the
  contract and says so. The root guidance states several of the project's
  principles about evidence. Where a journal belief matches one of them, the
  journal cannot show that the contract alone produced it; say so in the item.
- The fresh reader followed none of the contract's links. A belief the reader
  held back because a linked document was unread is an uncertainty, not a
  misreading.

**Closing sections of the adjudication.**

- *Expectations and reliance.* The report was written without the journal and
  says, in each finding's interpretation and in the "Consequence for a fresh
  reader" column of its section 2, what a reader will conclude. For each of
  `F-01` to `F-19`, state the expected belief in one sentence and what the
  journal shows: the reader **formed** it (cite `J-nn`), the reader
  **avoided** it (cite `J-nn`), or the journal is **silent**. Also cite any
  entry that shows the reader relying on the statement the finding concerns.
  Do not revise the report's rating; the comparison stands beside it.
- *Silences.* Beliefs that matter to what a reader would do and that the
  journal neither states nor rules out. Every "silent" expectation above
  belongs here; add any other the adjudicator judges a reader needs. For each,
  describe a situation in which the belief would show. A journal records the
  beliefs a reader formed; it cannot record the ones the reader failed to
  form, and this list is how they are reached.
- *Pending reader response.* Items that cannot be classed without knowing more
  precisely what the reader believed. Say what is needed.
- *Corrections.* Anything the adjudication shows to be wrong or missing in
  the report. The report is not edited.
- *Not adjudicated.* Journal content left out, with the reason.

**Output.** `CONTRACT-ADJUDICATION.md`. One entry per journal entry, `A-nn`
for `J-nn`, with lettered items inside it. Each item gives the belief in the
reader's words (quoted or closely paraphrased), the reading answer with its
text, the grounding answer with its source, and the class. An entry whose
restatement is faithful and fully grounded, with no inference or open
uncertainty, can be three lines.

**Done when** all 52 journal entries have an adjudication entry; every item
has a class or is marked pending; the declaration and the five closing
sections exist, and an empty section says it is empty.

**After the fresh reader's answers arrive.** Complete each pending item once.
Add an entry `A-Sn` for each silence, classed from the answer. Mark every
item that rests on an answer as "prompted"; see how answers are weighed,
below.

### Fresh reader, first task: close out the journal

This section is handed to the fresh reader as written.

**Purpose.** The journal records your understanding passage by passage. This
task records where that understanding stood when you finished the document.

**You may open** your journal and `docs/CONTRACT.md`. Do not open anything
else in the repository, any other file in `records/contract/`, or any
document the contract links to. Do not inspect implementation or tests, and
do not comment on the quality of the writing or suggest changes.

**Record three things.**

1. *Reading conditions.* The revision of the contract you read: the output of
   `git hash-object docs/CONTRACT.md` if the file is unchanged since, or else
   the commit you read it at. Whether you read the raw Markdown or a rendered
   view. Whether you read in one pass or returned to earlier passages, and
   which. Everything you opened besides the contract.
2. *Uncertainties.* Go through each entry's "What remains uncertain?"
   paragraph. For each distinct uncertainty, give its status at the end of
   the document:
   - **answered**: a later passage settled it. Cite the lines.
   - **deferred**: the contract points to a named document for it, which you
     did not open. Name the document.
   - **open**: the contract neither settles it nor says where to look.

   For each deferred or open item, say what you could not do with confidence
   because of it, if anything: for instance write or reuse a specimen, read
   a reply or envelope, install or remove a runner.
3. *Changes of mind.* Any belief recorded in the journal that you held
   differently by the end of the document. Give the entry, the earlier
   belief, the later one, and the passage that changed it. The journal itself
   stays as it is.

**Output.** A section titled "Close-out" in a new file,
`records/contract/FRESH-ENCOUNTER-ADDENDA.md`, citing journal entries by
their section numbers. Your commit changes nothing but that file.

**Done when** every "What remains uncertain?" paragraph in the journal has
been accounted for, including those that say nothing consequential remains.

### Fresh reader, second step: answer questions from the text

This section is handed to the fresh reader with the questions.

**Purpose.** These questions ask about situations your journal does not
cover, or about entries where what you believed is not clear to another
reader. They are not a test, and a question does not mean your journal was
wrong on the point.

**You may open** your journal, your close-out and `docs/CONTRACT.md`, under
the same limits as before.

**For each question, record** your answer; the contract statement it rests
on; whether the answer came from what you remembered of your first reading or
from re-reading now, and how much of the document you had to search; and how
sure you are. "The contract does not say" is an answer.

**Output.** A section titled "Answers" appended to
`records/contract/FRESH-ENCOUNTER-ADDENDA.md`. The "Close-out" section is not
edited.

### Coordinator: questions and how answers are weighed

Draft one question for each silence and each pending item. A question
describes a situation and asks what the reader believes, expects or would do.
It does not state or imply the adjudicator's answer, does not mention
implementation, and does not reveal how any journal entry was classed. Where
two readings are in play, describe the situation so that neither is
suggested. The maintainer sees the questions before they go. If both lists
are empty, record that in the ledger and skip the step.

Answers are prompted beliefs. A correct prompted answer shows that the text
can yield the belief when the reader is pointed at the topic; it does not
show that the text yields it unprompted. An answer that needed a search
through the document is itself an observation about interpretive burden.
Items that rest on answers are marked so later stages weigh them accordingly.

### Coverage record

The ledger's coverage table already maps each unit to the report's line
groups and the journal's entries. After adjudication the coordinator fills
its last two columns: the adjudication entries, and the result, which is
either "no finding: supported and established" or the ledger rows of the
findings. A row that reads "no finding" is a conclusion of the examination,
with references behind it, not an absence of work. The report's `F-20` and
its section 8 are sources for those rows.

**Exit:** the adjudication has no pending items; the coverage table is
filled; the report and journal are unchanged since acceptance.

## Stage 3: filter findings

The ledger receives one row per underlying issue, from four sources:

- adjudication items in any class other than "supported interpretation",
  and silences whose answers show a belief worth a row;
- the report's findings `F-01` to `F-19`;
- qualifications in the report's line-group verdicts (`L-nn`) that no `F-nn`
  carries. Sweep every verdict that is not plainly "Supported" for these;
- uncertainties the close-out leaves open or deferred that kept the reader
  from acting, and observations recorded by the coordinator.

Merge rows that describe the same issue and keep every source reference. Each
row carries: an ID (`R-01`, …); the units; the source references; the finding
in one sentence; its class; the filter decision and reason; and, as the row
advances, the candidate layer, grounding, change, second examinations and
status. An index table plus a short block per pursued finding is enough.

The report gives each finding a provisional "belongs to" layer and a
consequence rating made before the journal existed. Both are inputs to the
row. The decision is made here, with the adjudication's "formed, avoided or
silent" result beside the report's rating.

### Decision procedure

Ask three questions, in order, and write the answer to each in the row.

1. **Is it consequential?** Name the concrete wrong action or wrong conclusion
   that follows, and who makes it: a specimen author, a consumer of envelopes
   or replies, someone installing a runner, or a maintainer of the contract.
   A wrong conclusion about what an observation establishes weighs most; that
   is what the instrument exists to prevent. A slip that the tool refuses
   immediately with a diagnostic naming the problem weighs least. If no action
   or conclusion depends on the finding, dismiss it and say so.
2. **Is the distinction necessary?** Does some reader of the contract rely on
   the commitment or distinction involved, for admission, for interpreting
   evidence or for maintenance? If the distinction is needed and correctly
   stated, and the reading was simply mistaken, dismiss. If the material is
   not needed by any reader of this document, the candidate remedy is removal
   or relocation, not clarification.
3. **Could an intervention reduce interpretive burden without losing
   contractual meaning?** Name the least intervention that plausibly would,
   and its layer. If every candidate loses meaning, or costs more than the
   consequence named in question 1, defer or dismiss.

Outcomes:

- **Pursue**: goes to stage 4.
- **Dismiss**: the reason stays in the row.
- **Defer**: the reason and the condition that would reopen it stay in the row.
- **Open question**: evidence is needed before the three questions can be
  answered; the row says what evidence.

An implementation discrepancy or unsupported claim is pursued at least as far
as grounding, because the class itself may reflect incomplete inspection.
Dismissing one without grounding is a maintainer decision.

### Remedy layers

| Layer | The remedy changes | Constraint |
| --- | --- | --- |
| Document | The contract's wording, order, structure or placement, including removal of material that is duplicated or unneeded. Intended meaning is unchanged. | See [stage 4](#what-an-edit-inside-a-region-does) for what an edit inside a region does. |
| Interpretation | What the contract is taken to mean where its text admits more than one reading or leaves a question open. | A decision about meaning belongs to the maintainer. The examination can show which reading the implementation has; it cannot make that behavior a commitment. |
| Implementation | Code, where a contract statement is confirmed as the intended meaning and the code does otherwise. | Leaves this plan: record the hand-off and its destination in the row. Which side is wrong is a maintainer decision. |
| Evidence | Tests, controls or citations, where a statement may be true and nothing adequately establishes it. The alternative remedy is to qualify or withdraw the statement, which is a document-layer change. | Follows [tests/AGENTS.md](../../tests/AGENTS.md#add-or-change-tests). |

A row may name more than one candidate layer. The choice is made in stage 4,
after grounding.

**Exit:** every row has a decision and a reason. The maintainer has confirmed
the pursue set.

## Stage 4: ground and revise

Nothing in this stage is prescribed in advance of the filter. It defines how
a pursued finding is established and how an intervention is chosen and
checked.

### Ground

For each pursued row, write the claim at issue as one sentence that could be
false. Then establish it with evidence suited to the kind of claim, and record
the evidence and its grade in the row.

| Grade | Meaning | The report calls this |
| --- | --- | --- |
| Run | A command or case was run in this examination and the relevant observation was inspected. Record the command, source commit and output location. | (none; the report ran four read-only checks) |
| Retained run | A case's recorded result in a retained archive. It establishes what that build did under that commit's test sources. Say where the archive is and that it is local. | Runtime |
| Test read | A test's assertion was read and traced to the connection in question, without a run. Reuse of an earlier result follows [the evidence rules](../../tests/AGENTS.md#evaluate-and-reuse-evidence). | Observed |
| Source read | The mechanism was located and read in source. | Observed |
| Delegated read | Source or test text read by a delegated pass and not re-read by the report's author. | Observed, marked † |
| Generated agreement | Generated artifacts agree with one another or with their input. | |
| None | Nothing found, or a conjecture awaiting an experiment. | Hypothesis |

A row whose grounding rests on a delegated read is re-read by whoever grounds
it before a change is built on it. The report's section 9 lists experiments
its author identified and did not run; each is a candidate grounding step for
the row it concerns, and none is required unless the row is pursued.

Choose by claim:

- *What the generation machinery reads, hashes, checks or refuses*: read the
  generator and run it or the owning `source_drift` case.
- *What is admitted or refused, with what code, in what order*: source reading
  locates the mechanism; an integrated case establishes it. Read the case's
  assertion and say what input it submits, what it observes, and why it would
  fail if the behavior were otherwise.
- *That something does not happen* (no client starts, no child is created, a
  file is unchanged): requires an independent witness of the absence. An exit
  code or a refusal message is not that witness.
- *What runtime evidence means* (lifecycle, gates, ordering, attribution):
  live suites establish behavior; constructed inputs establish interpretation
  only.
- *Universal negatives* ("never", "no negotiation"): identify the paths that
  could do the thing and state the limit of what was checked. These usually
  end at "source read", and the row should say so rather than claim more.

Four things do not establish behavior and are graded "generated agreement" at
most:

- the stamp table, `--check`, or agreement between the tables in the contract
  and the guide;
- a shape golden matching the collected shape, since the generator collects
  both from the same declarations;
- a suite named in a manifest row's `checks`: these are validated as suite
  names, and the
  [drift suite's account](../../tests/suites/source_drift/README.md#invariants)
  says their presence does not establish a defined assertion or coverage;
- generated writers and readers agreeing with the schema they were generated
  from.

The existence of a test, or of an example sentence in the contract, likewise
establishes nothing until the assertion or observation behind it is identified
and shown to reach the connection in question.

Grounding does not change tracked files. Test output goes to a fresh
`PW_TEST_OUT_DIR=tests/out/runs/<name>`; cite it as local, disposable evidence
with that limit stated. If grounding needs a probe or control that does not
exist, that is an evidence-layer change and goes through the steps below.

Grounding can change a finding's class or dissolve it. Record the outcome in
the ledger row; the adjudication entry is not edited. A finding that grounding
does not bear out closes as "not reproduced", with the evidence.

### What an edit inside a region does

This is a mechanical fact of
[docs/generate_contract_stamps.py](../../docs/generate_contract_stamps.py)
(`surface_hash`), stated here because it bears on every document-layer choice.

A surface's stamp derives from a hash over the whitespace-normalized text of
its region in the contract, the companion regions its manifest row names, and
its goldens. Re-wrapping lines changes nothing. Any other net change to that
text, including a clarification that leaves meaning intact, makes the surface
`unreleased` and then stamps it with the next release. The contract tells
specimen authors to review surfaces changed since the release they assert. A
wording edit inside a region therefore reaches readers as a surface to
re-review. Units U01, U02 and U17–U20 are outside every region and carry no
such effect.

Three consequences for choosing an intervention:

- Whether a clarification justifies that signal is a maintainer decision, per
  finding or per surface. This plan sets no policy for it.
- The comparison is against the last release, not the last commit, so a
  surface with several accepted edits is signaled once.
- Moving text across a region boundary, or adding, removing or renaming a
  region or manifest row, changes what the surface's definition contains or
  which surfaces exist. That is a change of scope, not of wording.

### Choose

Before editing, write in the ledger row:

- the layer chosen and why the others were not;
- a *meaning statement*: the commitments the affected passage carries now, and
  the commitments it is to carry afterward. For a document-layer change the
  two lists are the same. The stage 5 review checks the change against this
  statement;
- the verification the change needs.

The examination does not add contract semantics, compatibility commitments or
release policy. A candidate change that would state something the contract
does not already commit to stops here and goes to the maintainer as an
interpretation-layer decision.

### Revise

- One finding, or one tightly coupled group, per commit. The commit message
  names the ledger rows.
- No incidental edits. Something noticed while editing becomes a new ledger
  row.
- Document edits follow the [root guidance](../../AGENTS.md#documentation) and
  [docs/AGENTS.md](../../docs/AGENTS.md): describe current behavior, edit
  generator inputs and regenerate, never edit a generated copy. The stamp
  table is generated into both the contract and the guide.
- Check inbound anchors before renaming or moving a heading
  (`git grep -n 'CONTRACT.md#'`). Other documents link to several of the
  contract's headings, and the drift suite resolves them.
- Two drift cases insert text after the `<!-- BEGIN CONTRACT request -->`
  marker. If an edit removes a control's target, follow the
  [mutation-control rule](../../docs/AGENTS.md#editing-limits-and-shared-guide-content):
  update the control and confirm its mutation still changes the input.
- Avoid adding literal counts, sizes or durations to prose. The drift suite's
  invariant for counts and values routes them through generator spans; sites
  outside a span are entries in the
  [prose baseline](../../tests/suites/source_drift/README.md#invariants), and
  release preflight refuses added or rewritten baseline entries.
- An evidence-layer change shows the new check failing when the connection is
  broken, as well as passing when it holds.
- An implementation-layer change is not made under this plan. Until it is
  decided, the contract text it concerns stays as it is and the row stays
  open as handed off.

### Verify

For a change to the contract or its companion regions, from the repository
root:

```sh
tests/lib/python.sh docs/generate_contract_stamps.py   # after an edit inside a region
tests/lib/python.sh docs/generate_contract_stamps.py --check --require-history
tests/lib/python.sh docs/generate_limits.py --check    # when the guide or its links are touched
tests/run.sh --suite source_drift
```

These establish mechanical agreement: fresh tables, resolvable links, intact
generators. They do not establish that meaning was preserved or that the text
now communicates; stage 5 examines those. A change to tests or code takes the
verification its own guidance requires
([tests/AGENTS.md](../../tests/AGENTS.md#choose-and-run-verification),
[tests/CHANGE-VERIFICATION.md](../../tests/CHANGE-VERIFICATION.md)).

**Exit:** each pursued row is grounded and is either closed without change
(supported, or not reproduced), changed with its commit and verification
recorded, handed off, or left as an open question.

## Stage 5: second examinations

Each reader has a reserved second task. Its purpose and entry conditions are
fixed here. The assignments themselves are written from the actual changes.

**Common entry conditions.** At least one change exists as a commit, with its
ledger row, meaning statement and evidence record; the mechanical checks above
pass on the tree being examined. Run the second examinations once over a batch
of changes, not per change: a fresh reader can be fresh only once.

### Experienced reader: review the changes

**Purpose.** For each change, determine whether it addresses the finding,
preserves the necessary contract meaning, and rests on adequate evidence.

**Inputs.** The change; its ledger row; the original text; the adjudication
and report.

**Questions the review answers.** Is the feature that invited the
misunderstanding gone, or the unsupported statement now supported or
qualified? Compared with the meaning statement and the original text, was
anything normative added, dropped, weakened or strengthened without a recorded
maintainer decision? Does the recorded evidence reach the connection it is
cited for, at a grade suited to the claim? Did the change disturb anything
adjacent: stamps, anchors, companion regions, other documents that restate the
passage?

**Output.** A review note per change: accept, revise or reject, with reasons.
The reviewer did not author the change.

### Fresh-reader role: read the revised text

**Purpose.** Determine whether the revised material communicates its intended
meaning without introducing consequential new misunderstandings.

The original fresh reader has read the original contract, kept a journal,
closed it out and answered questions. That reader is no longer fresh, and the
two available readings are used for different things:

| Reading | By | Establishes | Does not establish |
| --- | --- | --- | --- |
| Targeted re-reading of the revised passages in context, journaled as before, without being told how earlier entries were classed | Original fresh reader | Whether the specific confusion that reader recorded is resolved for that reader | That the text is clear to someone meeting it for the first time |
| Sequential reading of the whole revised contract, journaled as before | Second fresh reader, given nothing from this examination | What a new reader comes to believe from the revised text, including misunderstandings a change introduced elsewhere | That a misunderstanding absent from this journal would have appeared without the change; one reader is one sample |

A second fresh reader's reading conditions are set deliberately and recorded:
which guidance files it reads beforehand, and whether it reads raw or
rendered text. Matching the original reader's conditions makes the two
journals comparable.

**Entry conditions for the second fresh reader.** Use one when a pursued
finding was a reasonably invited misunderstanding with a consequence rated
serious in stage 3; when a change moved, removed or restructured material; or
when the accepted changes together alter how the document reads. For a few
local wording changes of low consequence, the targeted re-reading is enough.
Record the choice and its reason in the ledger.

**Use of the result.** The experienced reader or the coordinator compares the
new journal with the adjudicated beliefs for the changed units. A
misunderstanding attributable to a change is a regression and reopens the row.
A misunderstanding in unchanged text is a new finding about the original
contract: it enters the ledger and is filtered like any other, and does not by
itself hold up completion of rows already verified.

Take the absence of an old misunderstanding from a new journal together with
the review's judgment that the inviting feature is gone. Neither alone shows
the change worked.

A regression's correction is reviewed by the experienced reader. Whether it
also needs another fresh reading follows the same entry conditions; no number
of rounds is required or forbidden.

## Stage 6: completion

The examination is complete when all of these hold:

1. **Examination is complete.** Every unit's coverage row is filled, with any
   gap stated and accepted by the maintainer. The report and journal are
   unchanged since acceptance.
2. **Findings are adjudicated and decided.** The adjudication has no pending
   items. Every ledger row is in one of these states, with its reason:
   dismissed; deferred, with a reopening condition; closed without change;
   changed and verified; handed off, with its destination; open question, with
   what would settle it and why that is not available now.
3. **Interventions are adequately verified.** For each changed row: the
   mechanical checks pass on the final tree; the evidence grade is recorded
   and suits the claim; the experienced reader's review accepts the change;
   and the fresh reading its entry conditions called for has been done.
4. **No consequential regression is unresolved.** Each regression attributed
   to a change has been corrected and re-reviewed, or the change reverted, or
   the regression accepted by the maintainer with the reason recorded.

No number of iterations, findings or reductions is required. An examination
that changes nothing can be complete. Open questions and deferred rows do not
block completion; they remain visible.

At closeout the maintainer decides what becomes of this directory. Plans here
are retired when consumed, and [records/README.md](../README.md) keeps
deferred questions outside the archive, so rows left deferred or open need a
home that outlives this plan.

## Decisions reserved for the maintainer

- Accepting a coverage gap or an acceptance shortfall.
- The questions sent to the fresh reader.
- Confirming the set of findings to pursue; dismissing an implementation
  discrepancy or unsupported claim without grounding.
- Any interpretation-layer decision: which of two readings the contract means.
- Which side changes when contract and implementation disagree.
- Any edit inside a stamped region, given the re-review signal it sends.
- Any change to a region boundary, to the manifest's surfaces, or to the
  presence of a normative statement.
- Whether to use a second fresh reader, where the entry conditions leave it
  open.
- Accepting a regression instead of correcting it.
- Disposition of the artifacts at closeout.

## When to reconsider this plan

- An output from a reader cannot be cited item by item, so the next step
  cannot map onto it.
- The contract, the surface manifest or the guide's contract regions change
  on `main` during the examination in a way that affects more than a few
  units.
- Findings point at the surface structure itself (which surfaces exist, what
  their regions contain) and not at passages within it. That is a design
  question this procedure is too small to carry; take it to the maintainer
  before stage 4 rather than as a series of wording changes.
- The volume of pursued findings makes one ledger file and one batch of second
  examinations unworkable.

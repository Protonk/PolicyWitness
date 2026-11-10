# CONTRACT.md examination plan

This plan organizes an examination of the public contract,
[docs/CONTRACT.md](../../docs/CONTRACT.md): what it communicates to a
technically competent reader, what its claims establish, how those claims rest
on generation machinery and working code, and whether complexity or misleading
statements can be reduced.

The objective is not a shorter contract or a quota of defects. "This passage is
necessary, correct and adequately supported" is a result, and the plan records
it as one.

Two readings supply the material, and both are complete. This plan defines
how they are compared, filtered, acted on and re-examined, and when the work
stops. It contains no finding from either reading.

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

The two readers are distinguished by how they worked, and each is used for
what that way of working left it holding.

| Role | What it holds | Used for | Does not |
| --- | --- | --- | --- |
| Report writer | An integrated technical map of the contract, its machinery and its implementation. It directed five delegated tracing passes and combined what they returned; much of the map is second-hand, and part of it exists only in that session's context. | Depositing the delegated traces; adjudication (stage 2); review of changes (stage 5). | Edit its report. Author the changes it later reviews. |
| Journal writer | A first-person, chronological record of meeting the document, kept entry by entry with nothing but the text and repository guidance. | Close-out, answers and replies (stage 2); a targeted re-reading (stage 5). | Inspect implementation, evaluate the writing, or open the report, the adjudication, the ledger or this plan. |
| Isolated reader | Nothing. A new session started outside the repository and given only the contract file. | The baseline reading (stage 2) and each reading of revised text (stage 5). One session per reading. | Receive repository guidance, any artifact of this examination, or any other file. |
| Coordinator | Both artifacts and the ledger. | Executes this plan: keeps the ledger, compares journals, drafts questions, proposes filter decisions, grounds findings, authors changes, runs verification. | Substitute its own reading for a reader's; its own observations enter the ledger marked as coordinator-origin. |
| Maintainer | | Relays tasks to the readers, launches isolated readers, and decides the items under [Decisions reserved for the maintainer](#decisions-reserved-for-the-maintainer). | |

The coordinator has no direct contact with the readers. The maintainer hands
each reader its task, and the reader's output arrives as a file in this
directory. The report writer may be given this whole plan. The journal writer
and each isolated reader are given only the task text marked for them.

The journal writer read repository guidance before the contract, so its
journal is not a contract-only reading. Its record and context are used all
the same. Readings that must depend on the contract alone are done by
isolated readers. An isolated reader cannot be launched from inside this
checkout: a session started here receives the root guidance automatically.

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
| [CONTRACT-FIRST-READER-REPORT.md](CONTRACT-FIRST-READER-REPORT.md), the **report** | Report writer | Accepted, `c87bfd80` | None |
| [FRESH-ENCOUNTER-JOURNAL.md](FRESH-ENCOUNTER-JOURNAL.md), the **journal** | Journal writer | Accepted, `214dddd7` | None |
| [CONTRACT-LEDGER.md](CONTRACT-LEDGER.md): stage log, acceptance record, join table, coverage record, findings ledger | Coordinator | Open | Rows gain decisions and status; reasons are never deleted |
| `CONTRACT-REPORT-TRACES.md`, the **traces** | Report writer | Stage 2 | Append-only |
| `ISOLATED-BASELINE-JOURNAL.md`, the **baseline** | Isolated reader | Stage 2 | None |
| `FRESH-ENCOUNTER-ADDENDA.md`, the **addenda**: close-out, answers, replies | Journal writer | Stage 2 | Append-only: a committed section is not edited |
| `CONTRACT-ADJUDICATION.md` | Report writer | Stage 2 | Pending items are completed once; nothing else is rewritten |
| Second-examination notes and journals | Each second examiner | Stage 5 | None |

The report's file name and title say "first reader". It is the report
writer's technical examination, not a first reading.

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
| `B-01`… | Baseline journal entries, by its own section numbers |
| `A-01`–`A-52`, `A-Sn`, `A-Dn` | Adjudication entries: `A-nn` adjudicates `J-nn`, `A-Sn` a silence, `A-Dn` a divergence between the two journals |
| `R-01`… | Ledger rows |
| † | Rests on a delegated pass and was not re-read by the report writer |

## Stage 1: independent examination

Complete. The ledger's acceptance record gives the result of each check below
for each artifact, and how each shortfall was settled. The criteria are kept
here because the same checks apply to anything later accepted from a reader,
including an isolated reader's journal.

A reader's artifact is usable when it names the contract revision it read;
covers every unit or says which it did not and why; can be cited entry by
entry; says what its conclusions rest on; says what its author opened; and
arrives in a commit that changes nothing else. The report additionally says
what it did not verify. A journal additionally runs in document order, gives
each belief with its supporting statement and remaining uncertainty, and
leaves an earlier entry in place when a later one revises it.

A shortfall is not repaired by hand. It is recorded against the affected
units, and filled by the same reader in an addendum or settled by the
maintainer's statement, recorded as such.

## Stage 2: first adjudication

This stage is read-only with respect to the tree. Its commits add or complete
the traces, the baseline, the addenda, the adjudication and the ledger, and
nothing else.

Order of work:

1. The report writer deposits the delegated traces. This comes before
   anything else that reader does: the material is held only in its session.
2. Three things then run together, none needing another's output to begin:
   the report writer's adjudication, the journal writer's close-out, and the
   isolated baseline reading.
3. The coordinator accepts the close-out and the baseline, lists the
   divergences between the two journals in the ledger, and passes all three
   to the report writer.
4. The report writer delivers the adjudication with its silences and its
   "pending reader response" items.
5. The coordinator drafts questions from those two lists. The journal writer
   answers. The report writer completes the pending items and adds an entry
   for each silence.
6. The coordinator shows the journal writer the items classed as mistaken
   readings. The journal writer replies. The report writer settles each item
   once more.
7. The coordinator fills the coverage record.

### Report writer, first: deposit the delegated traces

**Purpose.** The report marks with † every citation that rests on a delegated
tracing pass, and refers in several places to tables "in the delegated
trace". Those returns are not on disk. Stage 4 grounding starts from them.

**Record**, for each of the five passes: the brief it was given; what it
returned, verbatim where the text is still available; and where only a
summary or recollection remains, say so and give that. Do not re-verify,
correct or tidy what a pass returned; note separately anything now known to
be wrong in it.

**Output.** `CONTRACT-REPORT-TRACES.md`, one section per pass, headed by a
statement that its content is second-hand and was not re-read by the report
writer except where the report cites it without a †. The report is not
edited.

### Report writer, second: adjudicate the journal

**Purpose.** Judge the journal writer's own conclusions against the contract
text and the report's findings, and test the report's expectations about
readers against what two readers actually recorded.

**May open.** The journal, the addenda and the baseline as they arrive; the
report and traces; the contract at the baseline; the repository, read-only;
this plan and the ledger.

**What is already done.** The ledger's join table pairs every journal entry
with the report's line groups for the same lines, the opening words of each
verdict, and the findings that cite those lines. Pairing is a lookup and is
not repeated in the adjudication. The task is the judgments below.

**What the journal contains.** Each of its 52 entries cites a line range and
answers three questions: what the reader now believes, what supports the
belief, and what remains uncertain. Within an entry there are three kinds of
item:

| Kind | How to recognize it | What to do |
| --- | --- | --- |
| Restatement | The reader says what the passage states. Most of each entry. | Once per entry, check for drift: a restatement stronger, weaker, broader or narrower than the text. Record "faithful", or list each drift as its own item. |
| Inference | The reader marks it: "I infer", "I expect", "I therefore", "I would not", "I do not take", and the like. | Judge each one. These are the reader's own conclusions and the main object of this task. |
| Uncertainty | The "What remains uncertain?" paragraph. | Judge from the journal writer's close-out, which gives the end-of-document status of each. Until it arrives, leave these open. |

**For each drift and inference, answer two questions in this order.**

1. *Reading: does the contract text support the belief?* Judge this from the
   text alone, before consulting implementation knowledge. Cite the passage
   the reader relied on and any other passage that bears on it.
2. *Grounding: where the belief tracks something the contract states, is that
   statement established?* Answer as reported: cite the `L-nn` verdict and
   any `F-nn` from the join table, with the report's evidence class and its †
   where the support is delegated. First-hand re-reading is not asked for
   here; it happens in stage 4 for the rows that are pursued. Where the
   report does not cover the point, say "not covered" and what would
   determine it. Run no experiment in this stage.

For a faithful restatement the reading answer is "faithful" and the grounding
answer is the join table's row. It needs an item of its own only when the
report's verdict for those lines is anything other than plainly supported;
the class then follows from that verdict.

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

**Separating "mistaken" from "invited".** The adjudicator holds a map of the
implementation, and that makes text look clearer than it is. Class a reading
as mistaken only when the correcting text can be quoted and the reader had
already passed it, or it stands beside the passage in question. When the
correcting text arrives later, lives in another document, or depends on
repository knowledge, the reading was invited. When in doubt, class it as
invited and record the doubt. Every "mistaken" item goes back to the journal
writer for a reply, so the call is checked by the person who made the
reading.

**Three cautions.**

- The journal writer read the root, `docs/` and `.tmp/` guidance before the
  contract. The root guidance states several of the project's principles
  about evidence. Where a journal belief matches one of them, the journal
  cannot show that the contract alone produced it. Say so in the item, and
  look at what the baseline reader, who had no guidance, recorded for the
  same lines.
- The journal writer followed none of the contract's links. A belief held
  back because a linked document was unread is an uncertainty, not a
  misreading.
- This task may itself be delegated in part. Mark any item judged by a
  delegated pass with †, and add what the pass returned to the traces. The
  call between "mistaken" and "invited" is not delegated.

**Divergences.** The ledger lists where the baseline and the journal differ
over the same lines. Judge each as an item `A-Dn`, with the same two
questions and classes, for whichever reader's belief is in question. Where
the two journals agree, the judgment of the journal entry stands for both.

**Closing sections of the adjudication.**

- *Expectations and reliance.* The report was written without either journal
  and says, in each finding's interpretation and in the "Consequence for a
  fresh reader" column of its section 2, what a reader will conclude. For
  each of `F-01` to `F-19`, state the expected belief in one sentence and
  what each journal shows: the reader **formed** it, the reader **avoided**
  it, or the journal is **silent**, with the entry cited. Also cite any entry
  that shows a reader relying on the statement the finding concerns. Do not
  revise the report's rating; the comparison stands beside it.
- *Silences.* Beliefs that matter to what a reader would do and that neither
  journal states or rules out. Every expectation on which both journals are
  silent belongs here; add any other the adjudicator judges a reader needs.
  For each, describe a situation in which the belief would show. A journal
  records the beliefs a reader formed; it cannot record the ones the reader
  failed to form, and this list is how they are reached.
- *Pending reader response.* Items that cannot be classed without knowing more
  precisely what the journal writer believed. Say what is needed.
- *Corrections.* Anything the adjudication shows to be wrong or missing in
  the report. The report is not edited.
- *Not adjudicated.* Journal content left out, with the reason.

**Output.** `CONTRACT-ADJUDICATION.md`. One entry per journal entry, `A-nn`
for `J-nn`, with lettered items inside it; then the `A-Dn` entries; then the
closing sections. Each item gives the belief in the reader's words (quoted or
closely paraphrased), the reading answer with its text, the grounding answer
with its source, and the class. An entry with a faithful restatement, a
plainly supported verdict and no inference or open uncertainty is one line.

**Done when** all 52 journal entries and every listed divergence have an
entry; every item has a class or is marked pending; the five closing sections
exist, and an empty section says it is empty.

**After the answers arrive.** Complete each pending item once. Add an entry
`A-Sn` for each silence, classed from the answer, and mark every item that
rests on an answer as "prompted".

**After the replies arrive.** For each contested item, either keep the class
or change it, once, and record the reply beside it. The earlier class stays
visible. An item still contested after that is filtered in stage 3 as though
it were invited.

### What a close-out records

This block is part of the task text for the journal writer and for every
isolated reader. "Your journal" is whichever journal that reader wrote.

1. *Reading conditions.* Whether you read the raw Markdown or a rendered
   view. Whether you read in one pass or returned to earlier passages.
   Everything you opened besides the contract.
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
3. *Carried terms.* Each term, name or reference you met before the document
   explained it, or that it never explained. Say where you first met it,
   where it was explained if it was, and what meaning you assumed in order to
   keep reading.
4. *Going back.* Each passage you returned to in order to understand a later
   one, and what sent you back.
5. *Changes of mind.* Any belief recorded in your journal that you held
   differently by the end of the document. Give the entry, the earlier
   belief, the later one, and the passage that changed it. The journal's
   entries stay as they are.

Report what happened as you read. Do not judge the quality of the writing or
suggest changes.

### Journal writer, first: close out the journal

Handed to the journal writer together with the block above.

**Purpose.** Your journal records your understanding passage by passage. This
task records where that understanding stood when you finished the document,
and what the reading cost you along the way.

**You may open** your journal and `docs/CONTRACT.md`. Do not open anything
else in the repository, any other file in `records/contract/`, or any
document the contract links to. Do not inspect implementation or tests.

**Output.** A section titled "Close-out" in a new file,
`records/contract/FRESH-ENCOUNTER-ADDENDA.md`, with the five parts of the
close-out block, citing journal entries by their section numbers. Your commit changes nothing
but that file.

**Done when** every "What remains uncertain?" paragraph in the journal has
been accounted for, including those that say nothing consequential remains.

### Isolated reader: baseline reading

Launched by the maintainer in a new session outside the repository, in a
directory that holds one file: a copy of `docs/CONTRACT.md` whose
`git hash-object` output is the baseline blob. No repository guidance, no
other file, no network. The text below this paragraph, to the end of this
section, and the close-out block are the whole of what the reader is told.

**Purpose.** Read this document as a technically competent person meeting it
for the first time, who needs to know what it commits to. Keep a journal of
what you come to believe as you go.

**You may open** only this file. Its links lead to documents you do not have;
do not look for them or for the project anywhere else. Do not judge the
quality of the writing or suggest changes.

**How to keep the journal.** Read the raw text in order, one portion at a
time: a paragraph, or a few that belong together. After each portion, and
before reading further, write a numbered entry with a short title, the line
range it covers, and three paragraphs:

- **What do I now believe?** What the passage tells you. Where you go beyond
  what it states, mark the step: "I infer", "I expect", "I would not".
- **What supports that belief?** The lines it rests on, here or earlier.
- **What remains uncertain?** What you would need to know and do not.

Do not go back to change an entry. If a later passage answers or overturns
an earlier one, say so in the later entry.

When you reach the end, add a final section titled "Close-out" with the five
parts of the close-out block.

**Output.** One file, `ISOLATED-BASELINE-JOURNAL.md`, in the working
directory. The maintainer places it in `records/contract/`.

### Coordinator: compare the two journals

When the baseline is accepted, compare it with the journal over the same
lines and list the divergences in the ledger: a belief or inference one
reader formed and the other did not; inferences that point opposite ways; an
uncertainty only one reader had; a term only one had to carry. This is a
comparison of two readings with each other, not a judgment of either against
the text. Agreement is recorded by absence from the list.

The two readers differ in more than guidance: they are different sessions,
and each is one sample. A divergence shows that the text permits both
readings. It does not show which condition produced the difference.

### Journal writer, second: answer questions from the text

Handed to the journal writer with the questions.

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
`records/contract/FRESH-ENCOUNTER-ADDENDA.md`. Earlier sections are not
edited.

### Journal writer, third: reply to contested readings

Handed to the journal writer with the items.

**Purpose.** Another reader has compared some of your beliefs with the
contract text and concluded that the text does not support them. For each,
you are shown your belief, their reasoning, and the passage they say settles
it. You were the one reading; say whether they are right.

**You may open** your journal, your earlier addenda and `docs/CONTRACT.md`.

**For each item, record** one of two replies. *Agreed*: you missed or
misread the passage; say which and, if you can, why. *Contested*: say what
in the text led you to your reading, citing lines, and why the passage
offered does not settle it for someone reading in order. Neither reply is
the better one. You are not defending the journal.

**Output.** A section titled "Replies" appended to
`records/contract/FRESH-ENCOUNTER-ADDENDA.md`. Earlier sections are not
edited.

### Coordinator: questions, contested items and how answers are weighed

*Questions.* Draft one for each silence and each pending item. A question
describes a situation and asks what the reader believes, expects or would do.
It does not state or imply the adjudicator's answer, does not mention
implementation, and does not reveal how any journal entry was classed. Where
two readings are in play, describe the situation so that neither is
suggested. The maintainer sees the questions before they go. If both lists
are empty, record that in the ledger and skip the step. If the baseline
reader's session is still open, the same questions may be put to it; its
answers are recorded in the ledger as prompted and coordinator-relayed.

*Contested items.* Give the journal writer every item classed as a mistaken
reading, with the belief, the reading answer and the quoted passage. Leave
out the grounding answer and anything else about implementation: the reply
is about the text. This step ends the journal writer's independence from the
adjudication, which is why it comes last.

*Weighing.* The journal and the baseline are unprompted. The close-outs are
unprompted but retrospective. Answers are prompted: a correct prompted answer
shows that the text can yield the belief when the reader is pointed at the
topic, not that it yields it unprompted, and an answer that needed a search
through the document is itself an observation about interpretive burden.
Replies are made with the adjudicator's reasoning in view. Each item in the
adjudication and each ledger row says which of these it rests on.

### Coverage record

The ledger's coverage table maps each unit to the report's line groups and
the journal's entries. After adjudication the coordinator adds the baseline's
entries and fills the last two columns: the adjudication entries, and the
result, which is either "no finding: supported and established" or the ledger
rows of the findings. A row that reads "no finding" is a conclusion of the
examination, with references behind it, not an absence of work. The report's
`F-20` and its section 8 are sources for those rows.

**Exit:** the adjudication has no pending items and every contested item is
settled or marked as still contested; the coverage table is filled; the
report and journal are unchanged since acceptance.

## Stage 3: filter findings

The ledger receives one row per underlying issue, from five sources:

- adjudication items in any class other than "supported interpretation",
  including divergences and contested items, and silences whose answers show
  a belief worth a row;
- the report's findings `F-01` to `F-19`;
- qualifications in the report's line-group verdicts (`L-nn`) that no `F-nn`
  carries. Sweep every verdict that is not plainly "Supported" for these;
- from either close-out: uncertainties left open or deferred that kept the
  reader from acting, and carried terms the document never explained;
- observations recorded by the coordinator.

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
| Delegated read | Source or test text read by a delegated pass and not re-read by the report writer. The traces hold what the pass returned. | Observed, marked † |
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
of changes, not per change.

### Report writer: review the changes

**Purpose.** For each change, determine whether it addresses the finding,
preserves the necessary contract meaning, and rests on adequate evidence.

**Inputs.** The change; its ledger row; the original text; the adjudication,
report and traces.

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

### Readings of the revised text

**Purpose.** Determine whether the revised material communicates its intended
meaning without introducing consequential new misunderstandings.

Two readings are available, and they establish different things:

| Reading | By | Establishes | Does not establish |
| --- | --- | --- | --- |
| Sequential reading of the whole revised contract, under the baseline reading's conditions and task text | A new isolated reader | What a reader with nothing but the document comes to believe from the revised text, including misunderstandings a change introduced elsewhere. Compared with the baseline journal, which was made the same way from the original text. | That a difference from the baseline was caused by the change; each reader is one sample |
| Targeted re-reading of the revised passages in context, journaled as before, without being told how earlier entries were classed | Journal writer | Whether the specific confusion that reader recorded is resolved for that reader | That the text is clear to someone meeting it for the first time |

**Entry conditions.** An isolated reading runs over every batch that changes
the contract's text. Skipping it for a batch is a maintainer decision with
the reason recorded. Where a difference from the baseline would decide
whether a change stands, run more than one isolated reading before relying on
it. The journal writer's re-reading is used when a change answers a belief,
uncertainty or carried term that reader recorded.

**Use of the result.** The report writer or the coordinator compares the new
journal with the baseline and with the adjudicated beliefs for the changed
units. A misunderstanding attributable to a change is a regression and
reopens the row. A misunderstanding in unchanged text is a new finding about
the original contract: it enters the ledger and is filtered like any other,
and does not by itself hold up completion of rows already verified.

Take the absence of an old misunderstanding from a new journal together with
the review's judgment that the inviting feature is gone. Neither alone shows
the change worked.

A regression's correction is reviewed by the report writer and read by a new
isolated reader under the same entry conditions; no number of rounds is
required or forbidden.

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
   and suits the claim; the report writer's review accepts the change;
   and the readings its entry conditions called for have been done.
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
- The questions sent to the journal writer.
- Launching each isolated reader, and skipping an isolated reading for a
  batch of changes.
- Confirming the set of findings to pursue; dismissing an implementation
  discrepancy or unsupported claim without grounding.
- Any interpretation-layer decision: which of two readings the contract means.
- Which side changes when contract and implementation disagree.
- Any edit inside a stamped region, given the re-review signal it sends.
- Any change to a region boundary, to the manifest's surfaces, or to the
  presence of a normative statement.
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

# CONTRACT.md examination plan

This plan organizes an examination of the public contract,
[docs/CONTRACT.md](../../docs/CONTRACT.md): what it communicates to a
technically competent reader, what its claims establish, how those claims rest
on generation machinery and working code, and whether complexity or misleading
statements can be reduced.

The objective is not a shorter contract or a quota of defects. "This passage is
necessary, correct and adequately supported" is a result, and the plan records
it as one.

Two independent readings supply the material. This plan does not perform
either reading and does not predict what they contain. It defines how their
artifacts are accepted, compared, filtered, acted on and re-examined, and when
the work stops.

## Contents

- [Participants](#participants)
- [Subject and baseline](#subject-and-baseline)
- [Artifacts](#artifacts)
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
| Experienced reader | Technical examination of the contract's structure, normative claims, generation machinery, implementation connections and verification evidence. Later: adjudication (stage 2) and review of changes (stage 5). | See the fresh reader's journal before its own report is accepted. Author the changes it later reviews. |
| Fresh reader | Sequential interpretation journal: what the reader comes to believe, which statements support each belief, what stays uncertain. Later: answers to questions (stage 2) and a targeted re-reading (stage 5). | Inspect implementation, evaluate the writing, or see the experienced reader's report, the adjudication or the ledger. |
| Second fresh reader | A reader with no exposure to the original contract or to any artifact of this examination. Used in stage 5 only where independence matters. | Exist before stage 5 decides it is needed. |
| Coordinator | Executes this plan: accepts artifacts, keeps the coverage record and findings ledger, proposes filter decisions, grounds findings, authors changes, runs verification. | Relay one reader's content to the other outside the defined steps. Substitute its own reading for either reader's; its own observations enter the ledger marked as coordinator-origin. |
| Maintainer | Decides the items listed under [Decisions reserved for the maintainer](#decisions-reserved-for-the-maintainer). | |

Independence here is kept by discipline, not isolation: the artifacts live in
this directory and any participant could open them. Each artifact therefore
states what its author read, and the coordinator records the order of
exposure.

## Subject and baseline

The subject is `docs/CONTRACT.md` as last changed by commit `cbf5f298`
(441 lines). Before stage 2 and again before any revision, run

```sh
git log --oneline cbf5f298..HEAD -- docs/CONTRACT.md docs/contract_surfaces.json
```

Other work lands in this repository while the examination runs. If the command
prints anything, identify the affected units below and either have them
re-examined or record that the artifacts describe the older text.

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

## Artifacts

All live in `records/contract/`. Under the
[records link rule](../AGENTS.md), only this plan links to them.

| Artifact | Author | Created | Changes after acceptance |
| --- | --- | --- | --- |
| Experienced reader report | Experienced reader | Stage 1 | None |
| Fresh reader journal | Fresh reader | Stage 1 | None |
| `CONTRACT-ADJUDICATION.md` | Experienced reader | Stage 2 | Pending entries are completed once; nothing else is rewritten |
| `CONTRACT-READER-RESPONSES.md` | Fresh reader | Stage 2 | None |
| `CONTRACT-LEDGER.md` (coverage record and findings ledger) | Coordinator | Stage 2, grows through stage 6 | Rows gain decisions and status; reasons are never deleted |
| Second-examination notes | Each second examiner | Stage 5 | None |

One report, `CONTRACT-FIRST-READER-REPORT.md`, was already committed
(`c87bfd80`) when this plan was written. It was not opened in preparing the
plan. Which role it fills, and the path of the other reader's artifact, are
bound when the reports are introduced; record both paths and their accepting
commits at the top of the ledger.

Acceptance is a commit. An accepted artifact is not edited afterward: a
correction is recorded in the adjudication or the ledger and points at the
passage it corrects. `git log -- <path>` then shows that the original stands.

No other administrative artifacts are planned. If a need for one appears,
state the need in the ledger before creating it.

## Stage 1: independent examination

The two readings are already assigned; this stage only defines what the
coordinator checks before accepting each artifact. The checks are about
usability, not about whether the conclusions are right.

**Experienced reader report** is complete and usable when:

- it names the contract revision it examined;
- every unit U01–U20 is addressed, or is listed as not examined with the
  reason;
- each assessment can be cited: it identifies the contract passage and has, or
  can be given without rewriting, a stable reference (section number, heading
  or identifier);
- for each claim it assesses, it says what the assessment rests on and of what
  kind: source read, test read, command run and observed, generated artifact
  compared, or inference;
- it states what it did not verify and why;
- it says what the author read besides the contract and the repository, and in
  particular that the journal was not among it;
- its commit changes nothing but the report.

**Fresh reader journal** is complete and usable when:

- it names the contract revision it read;
- its entries run in document order to the end of the contract, and any place
  the reader stopped, skipped or went back is visible;
- each entry gives the belief formed, the statement or statements that support
  it (quoted or located precisely enough to find), and the reader's
  uncertainty;
- a belief revised later appears as a later entry, with the earlier one left in
  place;
- it says what else the reader opened (a linked document, for instance), so a
  belief formed from another document can be told apart from one formed from
  the contract;
- its commit changes nothing but the journal.

If an artifact falls short, do not repair it by hand. Record the gap against
the affected units in the coverage record. The same reader may supply an
addendum as a separate dated section or file, provided that happens before
that reader is exposed to anything further. After exposure, a gap is filled in
the next stage and labeled as post-exposure work.

Journal content outside the fresh reader's role (remarks on implementation, or
on the quality of the writing) stays in the journal. It is listed in the
adjudication as out of role and is not adjudicated as an interpretation.

**Exit:** both artifacts accepted and committed; the experienced reader's
report was accepted before that reader received the journal; the ledger file
exists with the artifact paths, accepting commits and an empty coverage table
of twenty rows.

## Stage 2: first adjudication

This stage is read-only with respect to the tree. Its commits add or complete
the adjudication, the reader responses and the ledger, nothing else.

### The experienced reader's first subsequent task: adjudicate the journal

**Purpose.** Examine each of the fresh reader's conclusions against the
contract text and against the technical findings the experienced reader has
already established.

**Inputs.** The accepted journal; the reader's own accepted report; the
contract at the baseline; the repository, read-only.

**Unit of work.** One belief or recorded uncertainty in the journal. Entries
that state the same belief may be adjudicated once, citing every entry.

**For each belief, answer two questions in this order.**

1. *Reading: does the contract text support the belief?* Judge this from the
   text alone, before consulting implementation knowledge. Cite the passage the
   reader relied on and any other passage that bears on it.
2. *Grounding: where the belief tracks something the contract states, is that
   statement established?* Answer from the accepted report, citing it. If the
   report does not cover the point, either inspect now and label the result
   "new inspection, post-exposure", or leave the grounding undetermined and
   say what would determine it.

**Then assign one class.**

| Class | Meaning |
| --- | --- |
| Supported interpretation | The belief is what the text says, and the report found the statement established or had no reason to doubt it. |
| Mistaken reading | The text does not support the belief, the passage that settles it can be quoted, and nothing in the text leads toward the error. |
| Reasonably invited misunderstanding | The belief is not what the contract means or not what the implementation does, and a feature of the text leads toward it. Name the feature: a term used in two senses, a missing antecedent, ordering, an example, a heading, an omission, reliance on knowledge the document does not supply. |
| Unsupported claim | The belief is a faithful reading of a contract statement that the examined evidence neither establishes nor contradicts. The issue lies with the statement, not the reading. |
| Implementation discrepancy | The belief is a faithful reading of a contract statement that the examined source or observed behavior contradicts. |
| Unresolved question | The reading or the grounding cannot be settled with what is available. State what would settle it. |

For a recorded uncertainty, say whether the contract settles the question and
where, or whether the contract leaves it open.

**Separating "mistaken" from "invited".** The adjudicator knows the
implementation, and that knowledge makes text look clearer than it is. Class a
reading as mistaken only when the correcting text can be quoted and the reader
had already passed it, or it stands beside the passage in question. When the
correcting text arrives later, lives in another document, or depends on
repository knowledge, the reading was invited. When in doubt, class it as
invited and record the doubt; stage 3 can still dismiss it, but a finding
dismissed here is lost.

**Also record, in closing sections of the adjudication:**

- *Silences.* For each unit, any commitment in the contract that a reader
  needs to carry away and that no journal entry reflects. A journal shows the
  beliefs a reader formed; it cannot show the ones the reader failed to form.
  Keep this to commitments, in the adjudicator's judgment, not every sentence.
- *Pending reader input.* Entries that cannot be classed without knowing more
  precisely what the reader believed. Leave their class as "pending reader
  response" and say what is needed.
- *Reliance.* For each finding in the accepted report, the journal entries, if
  any, that show the reader relying on the affected statement.
- *Corrections.* Anything the adjudication shows to be wrong or missing in the
  accepted report. The report is not edited.
- *Not adjudicated.* Journal entries left out, with the reason (out of role,
  duplicate of another entry).

**Output.** `CONTRACT-ADJUDICATION.md`: one identified entry (`A-01`, …) per
belief or group, each with the journal references, the contract passage, the
belief in the reader's words, the reading answer with its text, the grounding
answer with its source, and the class.

**Done when** every journal entry maps to an adjudication entry or to the
not-adjudicated list, and the closing sections exist (empty ones say so).

### The fresh reader's first subsequent task: answer questions from the text

**Purpose.** Supply the two things adjudication cannot get from the journal:
what the reader meant where an entry is ambiguous, and what the reader
believes about commitments the journal passed over in silence.

**Entry.** The adjudication draft exists. The coordinator turns its "pending
reader input" and "silences" lists into questions. Each question asks what the
reader believes, or what the reader would expect or do in a described
situation. A question does not state or imply the adjudicator's answer, does
not mention implementation, and does not reveal how any journal entry was
classed. If both lists are empty, record that in the ledger and skip the task.

**Inputs.** The questions; the reader's own journal; the contract at the
baseline. Nothing else from this examination.

**Output.** `CONTRACT-READER-RESPONSES.md`: for each question, the answer, the
contract statement it rests on, whether the answer came from what the reader
remembered of the first reading or from re-reading now, and the reader's
uncertainty.

**How the answers are used.** The experienced reader completes the pending
entries, and adds an entry for each silence whose answer shows a belief worth
adjudicating. Answers are prompted beliefs. A correct prompted answer shows
that the text can yield the belief when the reader is pointed at the topic; it
does not show that the text yields it unprompted. Mark entries that rest on
responses so later stages weigh them accordingly. An answer that required a
search through the document is itself an observation about interpretive
burden.

### Coverage record

After adjudication, the coordinator fills the coverage table in the ledger,
one row per unit:

| Column | Content |
| --- | --- |
| Unit | U01–U20 |
| Experienced | Report reference, or "not examined: reason" |
| Fresh | Journal entry range, or "not reached" |
| Adjudicated | Adjudication entry IDs |
| Result | "No finding: supported and established", or the ledger IDs of findings |

A row that reads "no finding" is a conclusion of the examination, with
references behind it, not an absence of work.

**Exit:** adjudication complete with no pending entries; coverage table
filled; both original artifacts unchanged since acceptance.

## Stage 3: filter findings

The ledger receives one row per underlying issue, from three sources:
adjudication entries in any class other than "supported interpretation";
findings in the experienced reader's report, including observations about
unnecessary complexity, misleading statements and the generation machinery
that have no counterpart in the journal; and corrections or observations
recorded by the coordinator. Merge rows that describe the same issue and keep
every source reference.

Each row carries: an ID (`F-01`, …); the units; the source references; the
finding in one sentence; its class; the filter decision and reason; and, as
the row advances, the candidate layer, grounding, change, second examinations
and status. An index table plus a short block per pursued finding is enough.

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

Nothing in this stage is prescribed in advance of findings. It defines how a
pursued finding is established and how an intervention is chosen and checked.

### Ground

For each pursued row, write the claim at issue as one sentence that could be
false. Then establish it with evidence suited to the kind of claim, and record
the evidence and its grade in the row.

| Grade | Meaning |
| --- | --- |
| Observed | A command or case was run in this examination and the relevant observation was inspected. Record the command, source commit and output location. |
| Test read | A test's assertion was read and traced to the connection in question, without a run in this examination. Reuse of an earlier result follows [the evidence rules](../../tests/AGENTS.md#evaluate-and-reuse-evidence). |
| Source read | The mechanism was located and read in source. |
| Generated agreement | Generated artifacts agree with one another or with their input. |
| None | Nothing found. |

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
  names the ledger IDs.
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

The original fresh reader has read the original contract, kept a journal and
answered questions. That reader is no longer fresh, and the two available
readings are used for different things:

| Reading | By | Establishes | Does not establish |
| --- | --- | --- | --- |
| Targeted re-reading of the revised passages in context, journaled as before, without being told how earlier entries were classed | Original fresh reader | Whether the specific confusion that reader recorded is resolved for that reader | That the text is clear to someone meeting it for the first time |
| Sequential reading of the whole revised contract, journaled as before | Second fresh reader, given nothing from this examination | What a new reader comes to believe from the revised text, including misunderstandings a change introduced elsewhere | That a misunderstanding absent from this journal would have appeared without the change; one reader is one sample |

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
   gap stated and accepted by the maintainer. Both original artifacts are
   unchanged since acceptance.
2. **Findings are adjudicated and decided.** The adjudication has no pending
   entries. Every ledger row is in one of these states, with its reason:
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

- Accepting a coverage gap.
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

- An accepted artifact cannot be cited entry by entry, so adjudication cannot
  map onto it.
- The contract or the surface manifest changes on `main` during the
  examination in a way that affects more than a few units.
- Findings point at the surface structure itself (which surfaces exist, what
  their regions contain) and not at passages within it. That is a design
  question this procedure is too small to carry.
- The volume of pursued findings makes one ledger file and one batch of second
  examinations unworkable.

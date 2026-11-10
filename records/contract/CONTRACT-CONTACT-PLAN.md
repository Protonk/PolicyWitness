# CONTRACT.md examination plan

This plan runs on the public contract,
[docs/CONTRACT.md](../../docs/CONTRACT.md), the cycle this repository has
already run on its limits, footprint, architecture and build documents: read
the document closely, make each sentence account for itself against the
repository, straighten out whatever the honest account turns out to need,
write the document again, and read it again.

The objective is not a shorter contract or a quota of defects. "This sentence
is necessary, correct and owned" is a result, and the plan records it as one.

**This plan's later stages are superseded.** The examination ran through its
readings, its claim inventory and the opening of its strain register. The
maintainer then set a different course for acting on what it found, in
[docs/CONTRACT-STAGING-PLAN.md](../../docs/CONTRACT-STAGING-PLAN.md): four
stages, with the contract rewritten as a generated tree. Stages 5 to 8
below, and the dispositions listed under stage 4, describe the earlier
intention and are kept for the record. Two things in them are still used:
the register itself, which the staging plan draws its candidates from, and
the task text for an isolated reader under stage 7, which later readings
reuse.

**Where the work stands** is recorded in
[CONTRACT-LEDGER.md](CONTRACT-LEDGER.md), not here. A coordinator taking over
reads the ledger's stage log first, then the stage it names in this plan.

## Contents

- [How this document differs from the earlier ones](#how-this-document-differs-from-the-earlier-ones)
- [Participants](#participants)
- [Subject and baseline](#subject-and-baseline)
- [Artifacts and references](#artifacts-and-references)
- [Stages 1 and 2: the readings](#stages-1-and-2-the-readings)
- [Stage 3: claims and owners](#stage-3-claims-and-owners)
- [Stage 4: strain register](#stage-4-strain-register)
- [Stage 5: structure](#stage-5-structure)
- [Stage 6: fix and write](#stage-6-fix-and-write)
- [Stage 7: read again](#stage-7-read-again)
- [Stage 8: completion](#stage-8-completion)
- [Decisions reserved for the maintainer](#decisions-reserved-for-the-maintainer)
- [When to reconsider this plan](#when-to-reconsider-this-plan)

## How this document differs from the earlier ones

The cycle is the same. Four things about the starting position are not, and
the stages below are shaped by them.

- **Its sentences hang from nothing.** The limits, footprint, architecture
  and build documents were each created together with a manifest and a
  generator. A claim there is a row with a source and a check. The contract's
  unit of checking is the surface: thirteen hashes over region text and
  goldens, with nothing per sentence. Stage 3 gives each claim a row and looks
  for its owner.
- **Its prose is older than its machinery.** The text accumulated beside
  feature changes and has not had a close reading before. The surface
  machinery was placed around it at `v0.3.6`. Some sentences were written
  for a mechanism since replaced.
- **Its claims are not of one kind.** A limit is an integer with a compiled
  owner. The contract mixes admission rules, wire shapes, evidence rules,
  identity derivation, denials, examples and instructions. Stage 3 sorts
  them, because each kind has a different sort of owner.
- **Writing it is not free.** A net change inside a region restamps a
  surface, a code fix changes the build identity, and part of each surface's
  text lives in the guide. [Stage 6](#what-an-edit-inside-a-region-does)
  gives the mechanics. The maintainer has said that a restructured contract
  whose surfaces all carry the next release is an acceptable outcome, and
  that `v0.3.6` shapes may persist on other branches.

## Participants

| Role | What it holds | Used for |
| --- | --- | --- |
| Report writer | An integrated technical map of the contract, its machinery and its implementation, built from five delegated tracing passes. | The report, the traces, the adjudication; review of changes in stage 7. Does not review a change it authored. |
| Journal writer | A first-person record of meeting the document with the text and repository guidance only. | The journal and its close-out; questions; a targeted re-reading in stage 7. Does not inspect implementation. |
| Isolated reader | Nothing: a new session outside the repository, given the contract alone. | The baseline reading; each reading of revised text. One session per reading. |
| Delegated passes | A narrow brief and the repository, read-only. | Finding owners in stage 3; grounding in stage 4. |
| Coordinator | Every artifact and the ledger. | Executes this plan: keeps the ledger and the claim inventory, briefs passes, proposes dispositions, authors changes, runs verification. |
| Maintainer | | Relays tasks, launches isolated readers, and decides the items under [Decisions reserved for the maintainer](#decisions-reserved-for-the-maintainer). |

The coordinator has no direct contact with the two writers or with isolated
readers; the maintainer hands over each task and the output arrives as a
file here. Order of work is a default throughout, not a protocol. A step that
finds an input missing works from what exists and says so, and the ledger
records what happened.

## Subject and baseline

The subject is `docs/CONTRACT.md` as last changed by commit `cbf5f298`:
441 lines, blob `bfd2ededcfdeaf801b3f179e38886e9baa55fb7f`. Every reading so
far is of these bytes. Until stage 6 begins, check before each stage:

```sh
git rev-parse HEAD:docs/CONTRACT.md
git log --oneline cbf5f298..HEAD -- docs/CONTRACT.md docs/contract_surfaces.json docs/PolicyWitness.md
```

If the blob differs or the log prints anything, identify the affected units
and record in the ledger which artifacts describe the older text.

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

The manifest [docs/contract_surfaces.json](../../docs/contract_surfaces.json)
defines each surface as its `docs/CONTRACT.md` region together with the
`<!-- BEGIN CONTRACT … -->` regions it names in
[docs/PolicyWitness.md](../../docs/PolicyWitness.md) and the listed goldens.
Work on a surface reads those companion regions as part of its definition.

## Artifacts and references

All artifacts live in `records/contract/`. Under the
[records link rule](../AGENTS.md), only this plan links to them; the others
name one another by path.

| Artifact | Author | What it is |
| --- | --- | --- |
| [CONTRACT-FIRST-READER-REPORT.md](CONTRACT-FIRST-READER-REPORT.md), the **report** | Report writer | Technical examination: line groups `L-01`–`L-48`, findings `F-01`–`F-20`. Despite the file name it is not a first reading. |
| [CONTRACT-REPORT-TRACES.md](CONTRACT-REPORT-TRACES.md), the **traces** | Report writer | Verbatim briefs and returns of the five delegated passes behind the report. Second-hand throughout. |
| [FRESH-ENCOUNTER-JOURNAL.md](FRESH-ENCOUNTER-JOURNAL.md), the **journal** | Journal writer | Entries `J-01`–`J-52`. Read with repository guidance. |
| [FRESH-ENCOUNTER-ADDENDA.md](FRESH-ENCOUNTER-ADDENDA.md), the **addenda** | Journal writer | The journal's close-out; later, answers. Append-only. |
| [ISOLATED-BASELINE-JOURNAL.md](ISOLATED-BASELINE-JOURNAL.md), the **baseline** | Isolated reader | Entries `B-01`–`B-40` and a close-out with uncertainties `U1`–`U61`. Contract only; a reread. |
| [CONTRACT-ADJUDICATION.md](CONTRACT-ADJUDICATION.md) | Report writer | Entries `A-01`–`A-52` on the journal, `A-D01`–`A-D20` on the divergences, a table of findings against both journals, and four lists. |
| [CONTRACT-MAINTAINER-NOTES.md](CONTRACT-MAINTAINER-NOTES.md) | Maintainer | Close readings supplied in stage 4, verbatim. |
| [GUIDE-RESULT-ACCOUNT-DRAFT.md](GUIDE-RESULT-ACCOUNT-DRAFT.md) | Coordinator | A proposed consolidation of the guide's account of a run's result, for review. Changes nothing. |
| `validators/` | Delegated passes | For `R-14`: a comparison of the three hand-written validators on preparation-failure replies, the run of its candidates, and the temporary test code as a patch. |
| [CONTRACT-STRUCTURE-PROPOSAL.md](CONTRACT-STRUCTURE-PROPOSAL.md) | Coordinator | Proposed table of contents, surfaces and one worked section for the restructured contract, for the staging plan in `docs/CONTRACT-STAGING-PLAN.md`. |
| [CONTRACT-LEDGER.md](CONTRACT-LEDGER.md) | Coordinator | Stage log, acceptance record, join table, divergences, coverage, strain register. |
| [CONTRACT-CLAIMS.md](CONTRACT-CLAIMS.md) and `claims/`, the **inventory** | Coordinator, from delegated passes | Stage 3. One row per claim, with its kind, mechanism and owner. |
| Later readings and review notes | Their authors | Stage 7. |

A reader's artifact is accepted by a commit and not edited afterward; a
correction is recorded elsewhere and points at what it corrects. The ledger
and the inventory are working records and change as the work proceeds; a
recorded reason is never deleted. If another artifact seems needed, state the
need in the ledger first.

| Reference | Refers to |
| --- | --- |
| `C:N`, `C:N-M` | Lines of `docs/CONTRACT.md` at the baseline |
| `G:N` | Lines of `docs/PolicyWitness.md` at the same commit |
| `U01`–`U20` | Units, above |
| `K-<line>-<n>` | Claims in the inventory, by the first contract line of the claim |
| `R-01`… | Rows of the strain register |
| † | Rests on a delegated pass and was not re-read by whoever cites it |

## Stages 1 and 2: the readings

Done, apart from one optional step. The ledger holds the acceptance record
for each artifact, including the conditions each reader worked under. What
those readings established, and how to weigh them:

- The report examined every line and rated each line group. Most of its
  source citations are †. It ran four read-only checks and no test.
- The adjudication found no mistaken reading in the journal. Two of the
  journal's 69 marked inferences were invited by the text. Eighteen
  statements the journal restated faithfully take their class from the
  report: nine contradicted by the implementation as the report read it,
  five neither established nor contradicted, four unresolved. A careful
  reader mostly ends up believing what the contract says, so the strains in
  this document lie between the text and the repository far more than
  between the text and its reader.
- Both readers read raw Markdown and neither followed a link, so neither
  journal can show what a rendered page or the linked documents do to a
  reader. The baseline reader had no guidance and carried questions and
  undefined terms that the journal writer did not; the ledger's divergence
  table lists them.
- Each reader is one sample. The journal is unprompted; the close-outs are
  unprompted but retrospective; answers to questions are prompted.

**Remaining step: questions to the journal writer.** The adjudication lists
three unclear journal items and fourteen silences, which are conclusions
that would change what a reader does and that neither journal states or
rules out. The coordinator drafts one question for each unclear item and for
each silence a contract-only reader could answer. A question describes a
situation and asks what the reader believes, expects or would do; it does not
state or imply an answer and does not mention implementation. The maintainer
sees the questions before they go. The journal writer answers from the
journal, the addenda and the contract, giving for each the answer, the
contract statement it rests on, whether it came from memory or from
re-reading, and how sure it is, in a section titled "Answers" appended to
the addenda. The answers weigh as prompted beliefs and feed stage 4. No
journal item was classed as a mistaken reading, so there is nothing to send
back for reply.

This step does not block stage 3.

## Stage 3: claims and owners

**Purpose.** Give every claim in the contract a row, sort the rows by kind,
and find for each the source that implements it and the check that would
fail if it were false. This is the "spread to the repository" half of the
cycle, and it is where the ledger is put under load.

**Unit.** A claim is one assertion that could be false. A sentence may hold
several. A list whose members share one owner is one claim. Headings,
connectives and the generated table are not claims.

**Starting material.** The report's 48 line groups, and the traces, which
already break most passages into claim groups with source citations. Those
citations are leads. An owner is recorded only when the pass recording it
has read the source and the check itself.

**Kinds.** The list is closed; amend it by recording the reason in the
inventory's header.

| Kind | A claim that | Where owners have been found so far (leads, from the report and traces) |
| --- | --- | --- |
| `admission` | an input is accepted or refused, with what code, in what order | The request corpus `tests/fixtures/request_contract/examples.json` and the case that runs it through the signed CLI and direct XPC |
| `shape` | a record, frame or envelope has given keys, types, encoding or presentation | `docs/porcelain.json`, the shape goldens under `tests/fixtures/contract/`, the codec cases in `source_drift` |
| `evidence` | a reply field or state requires something, or does or does not establish something | The controller's reader checks and their constructed cases; `witness_contract` and `runner_unit` cases |
| `identity` | an identity is derived, compared or reported in a given way | `docs/build_contract.py`, `docs/generate_worker_identity.py`, `source_drift/build_contracts` |
| `denial` | something never happens or does not exist | None as a class; each needs the paths that could do the thing |
| `example` | an "Example:" sentence describes behavior | None as a class; the report traced each one separately |
| `procedure` | a specimen author, operator or maintainer is to do something | None |
| `machinery` | the document's own generation and checking works a given way | `docs/generate_contract_stamps.py`, `source_drift/build_contracts` |
| `referral` | another document supplies a value or definition | The target document |
| `residue` | a former mechanism is recalled or denied | None |

**Row.** Each row has: an ID; the unit and lines; the claim, quoted or
closely paraphrased; its kind; the *mechanism*; `sources` as path and
symbol; `checks` as
path, symbol and form (`test`, `rule` or `control`), with whether the check
runs in the default battery; an evidence grade from the table below; the
owner status; and the references that bear on it (`L`, `F`, `A`, `D`, `U`).
`sources` and `checks` follow the row schema of
[docs/limits.json](../../docs/limits.json) and
[docs/architecture.json](../../docs/architecture.json), so a row can be
promoted into a manifest if stage 5 decides on one.

**Mechanism.** What the repository does that makes the claim true, described
literally and in order: every component, file and process that takes part,
which of them decides, and whether the same rule is implemented in more than
one place. The account does not judge the machinery. It is written so that
someone who has not read the code can judge it.

A contract sentence that states a rule owes its reader four things, and the
account supplies each or says the sentence leaves it out: **who acts**;
**what is compared with what**; **at which boundary**, meaning where in a
run and on which side of which hand-over; and **with what consequence**,
meaning what is refused, withheld, flagged or published, and what a consumer
observes. Where a list of nouns stands in for several rules, the account
separates them. Where one name is used for two things, it says so.

**Owner status.**

- `owned`: a source implements the claim, and a check was read and its
  assertion reaches the claim: it would fail if the claim were false.
- `sourced`: a source implements the claim; no check reaches it.
- `unowned`: nothing found, or the claim has no observable consequence to
  own.
- `split`: the repository gives more than one answer, depending on path or
  state. Record each answer with its source.

**Evidence grades.**

| Grade | Meaning |
| --- | --- |
| Run | A command or case was run in this examination and the relevant observation inspected. Record the command, source commit and output location. |
| Retained run | A case's recorded result in a retained archive. Say where the archive is and that it is local. The report calls this "Runtime". |
| Test read | A check's assertion was read and traced to the claim, without a run. Reuse of an earlier result follows [the evidence rules](../../tests/AGENTS.md#evaluate-and-reuse-evidence). |
| Source read | The mechanism was located and read in source. |
| Delegated read | Read by a delegated pass and not re-read by whoever records it. The report's † citations are this grade until re-read. |
| Generated agreement | Generated artifacts agree with one another or with their input. |
| None | Nothing found, or a conjecture awaiting an experiment. |

Four things establish no more than "generated agreement": the stamp table
and `--check`; a shape golden matching the collected shape, since the
generator collects both from the same declarations; a suite named in a
manifest row's `checks`, which the
[drift suite's account](../../tests/suites/source_drift/README.md#invariants)
says is validated as a suite name only; and generated writers and readers
agreeing with their schema. The existence of a test establishes nothing
until its assertion is identified and shown to reach the claim.

**How.** The coordinator drafts the rows for a unit from the report and
traces, then briefs delegated passes to find and read owners. Briefs are
narrow: one kind or one unit, read-only, a fixed return format, a bound on
tool calls. A pass records what it read and what it did not find. The
coordinator integrates the returns and marks each row's grade. Nothing is
run in this stage unless a row's status turns on it.

**Output.** `CONTRACT-CLAIMS.md` is the index: how the rows were made,
coverage, counts by kind and status, and one table per unit. The rows
themselves are in `claims/`, one file per unit, because a mechanism account
runs to several hundred words. A pass writes its rows to a scratch file and
returns only a summary; the coordinator assembles the files without
rewriting the rows.

**Exit.** Every substantive sentence of every unit is covered by a row. The
inventory's header gives counts by kind and owner status for each unit.

## Stage 4: strain register

**Purpose.** List every place where a short, true account of the contract
needs a footnote, say whether the trouble sits in the text or in the
repository, and dispose of each. This is the register the architecture cycle
used, kept in the ledger.

**Where rows come from.** Merge rows that describe one strain and keep every
reference.

- Claims that are `unowned`, `sourced` or `split`.
- Claims of kind `residue`, `procedure`, `machinery` and `referral`, for the
  question whether they belong in this document.
- The report's findings `F-01`–`F-19`, and qualifications in its line-group
  verdicts that no finding carries.
- The adjudication: every item classed other than a supported
  interpretation, its divergences, its silences and its report corrections.
- The close-outs: uncertainties left open that kept a reader from acting,
  and terms the document never explains.
- Answers to questions, and observations recorded by the coordinator.

**Row.** An ID; the claims; the references; the strain in one sentence;
where it sits; the disposition; the reason; the status.

**Telling text from repository.** These are aids, used as far as a row
needs.

- *Four things owed.* Does the sentence say who acts, what is compared with
  what, at which boundary, and with what consequence? The maintainer's
  reading of C:243 in the notes is the worked case: verbs that sound like
  rules, a noun list covering five relations with two owners, one name for
  two things, and an example that does not demonstrate the distinction it is
  there for.
- *Outside knowledge.* Three readings exist at three levels: contract only,
  contract with guidance, contract with the implementation. A strain that
  disappears with guidance means the sentence leans on project knowledge. A
  strain that disappears only with the implementation means the repository
  is clear and the sentence hides it. A strain that survives all three
  points at the repository, or at a sentence with nothing behind it.
- *Probe.* State a situation with an observable answer: an exit code, a
  field, whether a process started. Ask it of the text and of the
  repository. If no probe can be formed, the sentence is not a behavioral
  claim.
- *Rewrite test.* Try to write the true replacement. If one short sentence
  does it, the strain was in the text. If the truth needs a case split, the
  seam is in the repository, and the question becomes whether it is
  intended.
- *History.* `git log -L` on the sentence shows what mechanism it was
  written for and how it was carried across later changes.
- *Run it.* A tracing pass can misread code as a reader can misread text. A
  row that places a strain in the repository on reading alone is confirmed
  by a run before anything is built on it. Test output goes to a fresh
  `PW_TEST_OUT_DIR=tests/out/runs/<name>` and is cited as local, disposable
  evidence. The report's section 9 lists experiments its author identified
  and did not run.

**Whose judgment.** Whether the machinery behind a sentence is necessary is
the maintainer's judgment, and what will look wrong to the maintainer cannot
be predicted from the coordinator's seat. The coordinator therefore does not
screen mechanisms for reasonableness. The register is reviewed with the
maintainer from the mechanism accounts themselves, including the rows the
coordinator would call "not a strain"; that disposition is proposed by the
coordinator and confirmed by the maintainer.

**Which side is right.** Never assumed. Where text and repository disagree,
the row records what the text says; what the repository does and at what
grade; what else depends on each side, including tests, the guide, other
documents and other code paths; and what the sentence's history shows about
intent. The coordinator proposes; the maintainer decides. These decisions
are collected and put to the maintainer together.

**Dispositions.**

| Disposition | Meaning |
| --- | --- |
| Not a strain | The sentence is short, true and owned, or the difficulty was a reader's. Give the reason. |
| Rewrite | The text changes and the repository does not: reword, define, link, move or remove. |
| Eliminate | Code, tests or machinery change so that the short sentence becomes true or owned. Giving a claim a check is an elimination. |
| Footnote | The seam is intended. The document states it. |
| Defer | Recorded with the condition that would reopen it. |

A strain disposed as "eliminate" whose fix is not yet made is carried in the
document as a **Known gap** paragraph that says what is true now. The
architecture, build and worker documents use this form and index it; the
drift suite checks their indexes, and would need to be extended to check
this document's.

Weigh rows by consequence: the concrete wrong action or wrong conclusion
that follows, and who makes it. A wrong conclusion about what an observation
establishes weighs most. A slip the tool refuses at once with a diagnostic
naming the problem weighs least.

**Exit.** Every row has a disposition and a reason, or is waiting on a named
maintainer decision.

## Stage 5: structure

**Purpose.** Decide what shape the contract takes before it is written
again.

This stage comes after the inventory and the register exist, because they
are the evidence for it. The sentence-level work is not lost whatever is
decided: rows move with their claims.

The questions, with what the inventory and register supply for each:

- *Definition or index.* For each surface, where its claims actually live
  now: in the contract's region, in the guide's regions, or split. Counts by
  kind and owner status on each side.
- *What belongs in the document.* Rows of kind `procedure`, `machinery`,
  `residue` and the internal identity section, with the readers who needed
  them.
- *Whether claims get durable owners.* Whether the inventory, or part of it
  such as the examples, is promoted into the surface manifest or a manifest
  of its own, with a generator check. This is new machinery and is weighed
  as such.
- *Regions and stamps.* Which regions exist and what each contains. The
  restamp consequences follow mechanically.

The coordinator writes the options with their costs into the ledger. The
maintainer decides.

## Stage 6: fix and write

### Fix

Each elimination is its own change, made under the repository's ordinary
rules: the [root guidance](../../AGENTS.md), the directory guidance for the
code touched, and the verification its kind requires
([tests/AGENTS.md](../../tests/AGENTS.md#choose-and-run-verification),
[tests/CHANGE-VERIFICATION.md](../../tests/CHANGE-VERIFICATION.md)). A new
check is shown failing when the claim is false as well as passing when it
holds. The commit names the register rows it serves. A change to shipped
source changes the development contract; that is the contract working as
written, not a cost to avoid.

### What an edit inside a region does

A mechanical fact of
[docs/generate_contract_stamps.py](../../docs/generate_contract_stamps.py)
(`surface_hash`). A surface's stamp derives from a hash over the
whitespace-normalized text of its region in the contract, the companion
regions its manifest row names, and its goldens. Re-wrapping lines changes
nothing. Any other net change makes the surface `unreleased` and then stamps
it with the next release. The comparison is against the last release, so
several edits to one surface are signaled once. Moving text across a region
boundary, or adding, removing or renaming a region or manifest row, changes
what a surface's definition contains or which surfaces exist. Units U01, U02
and U17–U20 are outside every region.

### Write

- The contract is written from the inventory, in the structure stage 5
  decided. Each sentence in the result traces to a claim row that is owned,
  footnoted or carried as a known gap. A sentence that traces to nothing is
  not written.
- Before changing a passage, write its *meaning statement* in the register
  row: what the passage commits to now, and what it is to commit to
  afterward. Where the two differ, the row names the maintainer decision
  that allows it.
- One strain, or one tightly coupled group, per commit. Something noticed
  while editing becomes a new row.
- Document edits follow the [root guidance](../../AGENTS.md#documentation)
  and [docs/AGENTS.md](../../docs/AGENTS.md): describe current behavior,
  edit generator inputs and regenerate, never edit a generated copy. The
  stamp table is generated into both the contract and the guide.
- Check inbound anchors before renaming or moving a heading
  (`git grep -n 'CONTRACT.md#'`).
- Two drift cases insert text after the `<!-- BEGIN CONTRACT request -->`
  marker. If an edit removes a control's target, follow the
  [mutation-control rule](../../docs/AGENTS.md#editing-limits-and-shared-guide-content).
- Avoid adding literal counts, sizes or durations to prose. The drift
  suite's invariant for counts and values routes them through generator
  spans; sites outside a span are entries in the
  [prose baseline](../../tests/suites/source_drift/README.md#invariants),
  and release preflight refuses added or rewritten baseline entries.

### Verify

For a change to the contract or its companion regions, from the repository
root:

```sh
tests/lib/python.sh docs/generate_contract_stamps.py   # after an edit inside a region
tests/lib/python.sh docs/generate_contract_stamps.py --check --require-history
tests/lib/python.sh docs/generate_limits.py --check    # when the guide or its links are touched
tests/run.sh --suite source_drift
```

These establish mechanical agreement. They do not establish that meaning was
preserved or that the text communicates; stage 7 examines those.

## Stage 7: read again

Run once over a batch of changes.

**Report writer: review.** For each change: does it remove the strain; does
the result match the row's meaning statement, with nothing normative added,
dropped, weakened or strengthened beyond it; does the recorded owner reach
the claim at the grade stated; did it disturb stamps, anchors, companion
regions or other documents that restate the passage. Output is a note per
change: accept, revise or reject, with reasons.

**Isolated reader: read the revised contract.** A new session outside the
repository, given the revised contract alone and the task text below. Its
journal is compared with the baseline, which was made the same way from the
original text. The hand-over order of document and task is not controlled;
the ledger records what happened. One reader is one sample: where a
difference from the baseline would decide whether a change stands, run more
than one.

**Journal writer: targeted re-reading.** Used when a change answers a
belief, uncertainty or carried term that reader recorded. It shows whether
that reader's difficulty is resolved, not whether a new reader would have
one.

A misunderstanding attributable to a change reopens its row. A new strain in
unchanged text enters the register like any other. The cycle then returns to
stage 4.

### Task text for an isolated reader

**Purpose.** Read the contract as a technically competent person meeting it
for the first time, who needs to know what it commits to. Keep a journal of
what you come to believe as you go.

**You may open** only the contract. Its links lead to documents you do not
have; do not look for them or for the project anywhere else. Do not judge the
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

When you reach the end, add a final section titled "Close-out" with these
five parts:

1. *Reading conditions.* Whether you read the raw Markdown or a rendered
   view. Whether you read in one pass or returned to earlier passages.
   Everything you opened besides the contract.
2. *Uncertainties.* For each distinct uncertainty in your entries, its
   status at the end of the document: **answered** by a later passage (cite
   the lines); **deferred** to a named document you did not open (name it);
   or **open**. For each deferred or open item, say what you could not do
   with confidence because of it, if anything.
3. *Carried terms.* Each term, name or reference you met before the document
   explained it, or that it never explained: where you first met it, where
   it was explained if it was, and what meaning you assumed in order to keep
   reading.
4. *Going back.* Each passage you returned to in order to understand a later
   one, and what sent you back.
5. *Changes of mind.* Any belief in your journal that you held differently
   by the end: the entry, the earlier belief, the later one, and the passage
   that changed it.

Report what happened as you read.

**Output.** One file in your working directory, named as the maintainer
directs.

## Stage 8: completion

The cycle is complete when all of these hold:

1. **Every claim is accounted for.** Each row of the inventory is owned,
   footnoted, carried as a known gap, or removed from the document with its
   reason.
2. **Every strain is disposed.** Each register row is not a strain,
   rewritten, eliminated, footnoted, or deferred with a reopening condition.
   No row waits on an undecided question of which side is right.
3. **The structure decision is recorded** and the written contract follows
   it.
4. **Changes are verified.** The mechanical checks pass on the final tree,
   each elimination has the verification its kind requires, and the report
   writer's review accepts each change.
5. **The result has been read.** At least one isolated reading of the final
   text exists, and no consequential misunderstanding attributable to a
   change is unresolved.

No number of rounds, findings or reductions is required. Known gaps and
deferred rows do not block completion; they remain visible, the first in
the document and the second in a record that outlives this plan. Plans here
are retired when consumed, and [records/README.md](../README.md) keeps
deferred questions outside the archive. At closeout the maintainer decides
what becomes of this directory.

## Decisions reserved for the maintainer

- The questions sent to the journal writer.
- Whether the machinery behind a claim is necessary.
- Which side changes when contract and repository disagree.
- Whether a seam in the repository is intended: footnote or eliminate.
- The structure of the rewritten contract, including any new manifest or
  generator check, and any change to regions or surfaces.
- Any change in what the contract commits to.
- Launching each isolated reader.
- Accepting a misunderstanding introduced by a change instead of correcting
  it.
- Disposition of the artifacts at closeout.

## When to reconsider this plan

- The inventory cannot be built at the claim level for some unit because its
  sentences do not separate into assertions that could be false.
- Owners turn out to be mostly absent for a whole kind, so that the register
  would be dominated by one structural strain and not by rows.
- The contract, the surface manifest or the guide's contract regions change
  on `main` for unrelated reasons in a way that affects more than a few
  units.
- The number of eliminations makes this a product change with a document
  attached. That work then needs its own plan, and this one keeps the
  document.

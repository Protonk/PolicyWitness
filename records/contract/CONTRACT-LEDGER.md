# CONTRACT.md examination ledger

The working record of the examination defined in
`records/contract/CONTRACT-CONTACT-PLAN.md`: where the work stands, what was
accepted from each reader, which parts of the contract have been covered, and
what became of each finding. The plan says how each part is filled. Sibling
artifacts are named by path without links, under the records link rule.

## Stage log

| Date | Stage | Event |
| --- | --- | --- |
| 2026-11-09 | 1 | Report accepted at `c87bfd80`, journal at `214dddd7`. Acceptance record below. Its shortfalls were settled by the maintainer's statements. |
| 2026-11-09 | 2 | Tasks reworked with the maintainer: trace deposit, narrowed adjudication, widened close-out, reply step, isolated baseline reading. Join table built. |
| 2026-11-09 | 2 | Baseline reading done by an isolated reader and accepted at `f6c2dda6`. Acceptance record, join table, divergences and coverage updated below. That reader has been dismissed, so no question can be put to it. |
| 2026-11-09 | 2 | Report writer's task (trace deposit, then adjudication) and journal writer's close-out handed over by the maintainer; both in progress. The report writer was told to judge uncertainties from what exists if the close-out has not arrived. |
| 2026-11-09 | 2 | Relayed from the report writer: the delegated passes' briefs and returns are still available verbatim in that session's subagent transcripts and are being extracted directly, not retyped. Check the traces file's own statement of this at acceptance. |
| 2026-11-09 | 2 | Traces accepted at `d1ca3cd9`. The first hand-over of the adjudication task did not complete; it was sent again in a shorter form: Part 1 entries, Part 2 divergences, Part 3 findings against both journals, Part 4 four lists. That form, not the earlier task text, is what the adjudication follows. |
| 2026-11-09 | 2 | Close-out and adjudication delivered and accepted; acceptance record below. The adjudication classes no journal item as a mistaken reading, so the reply step has nothing to send. Remaining in stage 2: the optional questions to the journal writer (three unclear items, fourteen silences). |
| 2026-11-09 | 3 | Plan rewritten around the cycle used for the limits, footprint, architecture and build documents: claim inventory with owners, strain register, structure decision, fix and write, read again. Two read-only history passes informed it; their returns are summarized in the plan's first section and are not deposited. Stage 3 has not started. |
| 2026-11-09 | 3 | Maintainer's direction for stages 3 and 4: whether machinery is necessary is the maintainer's judgment and cannot be predicted from the coordinator's seat, so mechanisms are described literally and not screened. The plan carries this. |
| 2026-11-09 | 3 | First four owner-finding passes returned: 94 rows covering the thirteen examples, C:168-236, C:165 and C:243. Assembled into `records/contract/CONTRACT-CLAIMS.md` and `records/contract/claims/`. 68 owned, 11 sourced, 11 split, 4 unowned, as the passes state them. Nothing was run. Not yet inventoried: U01, U02, U16 to U20, and the non-example text of U03 to U09 and U13 to U15. |
| 2026-11-09 | 2 | Question set of fifteen (three unclear journal items, twelve situations) handed to the journal writer by the maintainer. The journal writer is to be released after answering. The report writer is retained. |
| 2026-11-09 | 4 | Maintainer supplied a close reading of C:243, kept in `records/contract/CONTRACT-MAINTAINER-NOTES.md`. Coordinator read the cited source and opened register rows `R-01` to `R-05`. Stage 3 continues for the units not yet inventoried. |

## Artifacts

| Artifact | Path | Accepted at | Contract read |
| --- | --- | --- | --- |
| Report writer's report | `records/contract/CONTRACT-FIRST-READER-REPORT.md` | `c87bfd80` | Commit `298c1805`, blob `bfd2eded…` (stated in its section 1.1) |
| Journal writer's journal | `records/contract/FRESH-ENCOUNTER-JOURNAL.md` | `214dddd7` | Not stated in the journal. The maintainer states it is the version the report writer read. |
| Report writer's traces | `records/contract/CONTRACT-REPORT-TRACES.md` | `d1ca3cd9` | Cites the contract and guide at `298c1805`, as the report does |
| Isolated reader's baseline | `records/contract/ISOLATED-BASELINE-JOURNAL.md` | `f6c2dda6` | Not stated. Supplied by the maintainer as pasted raw Markdown; the reader counted 441 lines and its line references agree with the baseline. |
| Journal writer's addenda | `records/contract/FRESH-ENCOUNTER-ADDENDA.md` | committed by the coordinator with this ledger update | The baseline contract; the close-out says it reopened the journal and the contract only |
| Adjudication | `records/contract/CONTRACT-ADJUDICATION.md` | committed by the coordinator with this ledger update | The baseline contract |

`docs/CONTRACT.md`, `docs/contract_surfaces.json` and `docs/PolicyWitness.md`
have the same blobs at `v0.3.6`, `298c1805`, `c87bfd80`, `214dddd7` and at the
commit that created this ledger (checked with `git rev-parse <commit>:<path>`).
Both readers read the same contract.

## Acceptance record

Checked by the coordinator on 2026-11-09 against the plan's stage 1 criteria.
The checks concern usability, not whether the conclusions are right.

### Report

| Criterion | Result |
| --- | --- |
| Names the revision read | Yes: commit and blobs, section 1.1. |
| Covers every unit | Yes. Section 6 assigns every line to one of 48 groups, `L-01` to `L-48`. |
| Citable item by item | Yes: `L-nn` groups, `F-01` to `F-20` findings, numbered sections. |
| Says what conclusions rest on | Yes. Section 1.4 defines four evidence classes, and a † marks citations read by a delegated pass and not re-read by the author. |
| Says what was not verified | Yes: sections 9 and 10. |
| Says what the author opened | Partly. Section 1.2 lists what was read, and the journal is not on the list; there is no explicit statement that it was not seen. |
| Commit changes nothing else | Yes. |

**Shortfall.** Non-exposure to the journal is implicit in the report.
**Settled.** The maintainer states that the report writer did not see the
journal: it was kept in `.tmp/` and written to disk separately from the
report. Commit order is not evidence either way.

Limits the report states about itself, which later stages must carry:

- Most source tracing was done by five delegated passes that the report
  writer directed and combined. Those citations are marked †. What the
  passes returned is not on disk until the traces are deposited.
- The guide's contract regions were read in part; the report does not compare
  the guide with the contract systematically.
- Rule-level correctness of the semantic validators was examined only for the
  equipment region.
- No build, test or experiment was run. Four read-only generator checks were.
- Its runtime evidence is the retained v0.3.6 acceptance battery under
  `dist/archive/v0.3.6/`, which is gitignored and exists only in the local
  checkout, and which ran the test sources of its own commit.

### Journal

| Criterion | Result |
| --- | --- |
| Names the revision read | No. It says its line references "identify the document as read". |
| Covers every unit | Yes. 52 entries cite lines 1 to 441 in document order. |
| Citable item by item | Yes, by its section numbers (`J-01` to `J-52`). |
| Belief, support and uncertainty in each entry | Yes, as three labeled paragraphs. Inferences are marked as such within the belief paragraph. |
| Earlier entries left in place | Yes; the preamble says later entries answer earlier questions without revising them. |
| Says what the author opened | Yes: the contract and the root, `docs/` and `.tmp/` guidance. Its preamble says no implementation, test, verification artifact or other agent's finding was consulted, and its entries say where a linked document was left unopened. It does not say whether the text was read raw or rendered. |
| Commit changes nothing else | Yes. |

**Shortfalls.** The revision and the raw-or-rendered condition are not
stated. **Settled.** The maintainer states that the journal writer read the
same version as the report writer. The close-out records the reading
conditions.

Notes for later stages:

- The journal writer read repository guidance before the contract, so the
  journal is not a contract-only reading. The maintainer accepts this: the
  journal writer's record and context are used as they are, the adjudication
  task carries a caution, and an isolated reader supplies the contract-only
  baseline.
- The journal's source links are absolute paths into this checkout. They
  resolve only at this location. Not repaired.
- No out-of-role content was identified at acceptance. The adjudication's
  "not adjudicated" section is the place for any.

### Baseline

Checked by the coordinator on 2026-11-09.

| Criterion | Result |
| --- | --- |
| Names the revision read | No. The text was pasted into the session. It has 441 lines and the cited lines match the baseline wherever checked (63, 243, 296–297, 341–345, 406–414). |
| Covers every unit | Yes. 40 entries cite lines 1 to 441 in document order. |
| Citable item by item | Yes: entries by number (`B-01` to `B-40`), and uncertainties by the reader's own labels `U1` to `U61`. |
| Belief, support and uncertainty in each entry | Yes. Entries summarize more than the journal's do and mark few inferences. |
| Earlier entries left in place | Yes; the close-out says none was revised. |
| Says what the author opened | Yes: nothing besides the supplied contract. Raw Markdown, including comments. |
| Close-out, five parts | Yes. |
| Commit changes nothing else | Yes. |

**Deviation from the task's conditions.** The reader was given the document
before the instructions and had read all of it once before journaling. The
journal says so and calls itself a sequential rereading. The maintainer
confirms this was an ordering mistake in the hand-over. The session was
outside the repository with no PolicyWitness material.

What this changes:

- The baseline is contract-only and guidance-free, which is what it was
  wanted for.
- It is not a first-pass record. Its "going back" part is empty for that
  reason, and an early entry may carry hindsight from later passages. The
  per-entry uncertainties and the close-out's end-of-document statuses are
  usable; evidence about first-pass effort comes from the journal writer's
  close-out instead.
- Hand-over order is not controlled for later isolated readings either. The
  ledger records what happened for each.

### Traces

Checked for structure on 2026-11-09; not read through.

- One section for each of the five passes, each with the brief, the return,
  what the report writer read first-hand at the time, and what is now known
  to be wrong.
- The file states that every brief and return is verbatim, copied by script
  from the session's subagent transcripts, and that the transcripts
  themselves are not deposited.
- It states that it is second-hand throughout. A return's own labels
  (OBSERVED, INFERRED, HYPOTHESIS) are the pass's.

### Close-out (addenda)

Checked for structure on 2026-11-09; parts 1 and the opening of part 3 read.

- All five parts are present. Part 2 has a subsection for each of the 52
  journal sections.
- Reading conditions it adds to the journal's own account: raw Markdown in a
  terminal with line numbers, so region markers were visible; one forward
  pass in five windows (C:1-160, 161-245, 246-325, 326-385, 386-441), with
  entries written between windows, not after each passage; no earlier
  passage reopened during that pass.
- It says the root guidance "had already supplied a conceptual outline" of
  fresh processes, the host and worker split, the collection and release
  barrier, effects needing more than a return code, and limits on
  attributing sandbox cause; and that its part 3 marks where that mattered.

### Adjudication

Checked against the task's done criteria on 2026-11-09; conventions, Part 3
and Part 4 read, Parts 1 and 2 sampled.

- 52 entries on the journal, 20 on the divergences, 19 rows of findings
  against both journals, four lists. Complete.
- It opened no source and ran no test. Technical support is carried from the
  report with its † marks. Uncertainties were traced by a search of
  repository documentation only.
- Its own summary: no journal inference is a mistaken reading; of 69 marked
  inferences, 67 are supported and two were invited by the text (`A-21` (b),
  `A-29` (a)); one referral the reader relied on does not land (`A-23`);
  eighteen faithfully restated statements in fifteen entries take a class
  from the report's verdict (nine implementation discrepancies, five
  unsupported claims, four unresolved); one baseline reading is classed
  mistaken, with a caveat (`A-D04`).
- Part 4 lists fourteen silences, three unclear journal items and ten report
  corrections, and says nothing in its inputs shows a statement of fact in
  the report to be wrong.

## Join table

Pairs each journal entry with the report's material for the same lines, so
the adjudication does not repeat the lookup. Generated on 2026-11-09 by a
one-off script from the accepted artifacts; nothing in it is a judgment.

- *Baseline*: the `B-nn` entry covering the same lines. The baseline's
  portions are coarser, so several journal entries share one.
- *Report group*: every `L-nn` whose line range overlaps the entry's.
- *Report verdict, opening words*: the first sentence after "Verdict." in
  that group, verbatim. "(continues)" means the verdict says more; the
  further sentences often carry qualifications, and stage 3 sweeps them.
- *Findings cited in the group*: `F-nn` named anywhere in the group's text.
- *Findings citing these lines*: `F-nn` whose section 7 text cites a `C:`
  line or range overlapping the entry's. Some findings cite a whole region,
  so this column over-includes; it is an index, not a claim of relevance.

| Journal | Lines | Baseline | Report group | Report verdict, opening words | Findings cited in the group | Findings citing these lines |
| --- | --- | --- | --- | --- | --- | --- |
| `J-01` | 1–6 | `B-01` | `L-01` | `L-01`: Supported for `policy-witness run` and the XPC host. *(continues)* | F-09, F-10 | F-09, F-10, F-12, F-20 |
| `J-02` | 8–15 | `B-01` | `L-02`; `L-03` | `L-02`: Partly supported. *(continues)*<br>`L-03`: Supported. *(continues)* | F-09, F-11 | F-09, F-11, F-18 |
| `J-03` | 17–20 | `B-01` | `L-04` | `L-04`: The denial is supported. *(continues)* | F-03 | F-03 |
| `J-04` | 22–50 | `B-02` | `L-05`; `L-06` | `L-05`: Supported. *(continues)*<br>`L-06`: Supported as generated output. *(continues)* | F-01, F-03 | F-01, F-03, F-04, F-12 |
| `J-05` | 52–56 | `B-03` | `L-07` | `L-07`: Supported. *(continues)* | F-12 | F-12 |
| `J-06` | 58–63 | `B-04` | `L-08` | `L-08`: Supported. *(continues)* | none | F-05, F-20 |
| `J-07` | 65–75 | `B-05` | `L-09` | `L-09`: Partly supported. *(continues)* | F-08, F-09, F-12 | F-02, F-08, F-09, F-12 |
| `J-08` | 77–85 | `B-06` | `L-10` | `L-10`: Supported except "resolved meaning is recorded in runner provenance", which is partly supported *(continues)* | none | none |
| `J-09` | 87–98 | `B-07` | `L-11` | `L-11`: Supported. *(continues)* | none | F-08 |
| `J-10` | 100–106 | `B-08` | `L-12` | `L-12`: The first sentence is supported for tracked scoped sources and not for build variants (F-10, F-11). *(continues)* | F-03, F-05, F-10, F-11, F-12, F-13 | F-03, F-05, F-10, F-11, F-12, F-13 |
| `J-11` | 108–114 | `B-09` | `L-13` | `L-13`: Supported. *(continues)* | F-13 | F-13 |
| `J-12` | 116–124 | `B-09` | `L-14`; `L-15` | `L-14`: The disclaimer is a useful restriction and is consistent with the design. *(continues)*<br>`L-15`: Supported. *(continues)* | F-12, F-13 | F-01, F-12, F-13 |
| `J-13` | 126–130 | `B-10` | `L-16` | `L-16`: Supported in code. *(continues)* | F-05 | F-05 |
| `J-14` | 132–136 | `B-10` | `L-17` | `L-17`: Supported. *(continues)* | F-05 | F-05, F-12 |
| `J-15` | 138–142 | `B-11` | `L-18` | `L-18`: Supported. *(continues)* | F-08, F-12 | F-05, F-08 |
| `J-16` | 144–148 | `B-12` | `L-19` | `L-19`: Supported, with one precision. *(continues)* | F-05 | F-05, F-20 |
| `J-17` | 150–154 | `B-13` | `L-20` | `L-20`: Supported in code. *(continues)* | F-05 | F-05, F-18 |
| `J-18` | 156–160 | `B-14` | `L-21` | `L-21`: Supported. *(continues)* | F-07 | F-05, F-20 |
| `J-19` | 162–166 | `B-15` | `L-22` | `L-22`: Supported in producer and controller. *(continues)* | none | F-05, F-12 |
| `J-20` | 168–171 | `B-15` | `L-23` | `L-23`: Supported, with qualifications. *(continues)* | none | F-05, F-07, F-12 |
| `J-21` | 173–181 | `B-16` | `L-24` | `L-24`: The first three statements are supported in producer and reader (†). *(continues)* | F-12, F-15 | F-02, F-07, F-12, F-15 |
| `J-22` | 183–191 | `B-17` | `L-25` | `L-25`: Supported in producer and reader for the structural rules (†). *(continues)* | F-15 | F-07, F-12, F-15 |
| `J-23` | 191–196 | `B-17` | `L-25` | `L-25`: Supported in producer and reader for the structural rules (†). *(continues)* | F-15 | F-07, F-12, F-18 |
| `J-24` | 198–202 | `B-18` | `L-26` | `L-26`: Supported, read as "a reply violating this is flagged" (F-07). *(continues)* | F-07, F-15 | F-07, F-12, F-15 |
| `J-25` | 204–210 | `B-19` | `L-27` | `L-27`: Supported. *(continues)* | none | F-07, F-12, F-18 |
| `J-26` | 212–220 | `B-20` | `L-28` | `L-28`: Supported. *(continues)* | F-12, F-15 | F-07, F-12, F-15 |
| `J-27` | 220–228 | `B-20` | `L-28` | `L-28`: Supported. *(continues)* | F-12, F-15 | F-07, F-12 |
| `J-28` | 230–238 | `B-21` | `L-29` | `L-29`: Supported in reader and producer, with constructed negatives and a default signed assertion for the failed-gate case (†). | none | F-07, F-12 |
| `J-29` | 240–244 | `B-22` | `L-30` | `L-30`: Partly supported *(continues)* | F-06 | F-05, F-06, F-12, F-19 |
| `J-30` | 246–250 | `B-23` | `L-31` | `L-31`: Supported in code. *(continues)* | F-10 | F-05, F-12, F-19, F-20 |
| `J-31` | 252–255 | `B-24` | `L-32` | `L-32`: Supported. *(continues)* | F-12 | F-05, F-12, F-20 |
| `J-32` | 256–264 | `B-24` | `L-33` | `L-33`: Supported. *(continues)* | none | F-02 |
| `J-33` | 266–271 | `B-25` | `L-34` | `L-34`: Supported. | none | F-20 |
| `J-34` | 273–284 | `B-26` | `L-35` | `L-35`: Every listed code exists as a literal in controller or runner source (author's search) and has a reachable emit site (†). *(continues)* | F-08, F-12 | F-08, F-12 |
| `J-35` | 286–291 | `B-26` | `L-36` | `L-36`: Supported, except that "capacity checks precede meaning checks" is not true of rules enforced at decode time (F-08). *(continues)* | F-08 | F-08, F-20 |
| `J-36` | 293–296 | `B-27` | `L-37` | `L-37`: Supported in code, with three imprecise phrases (F-16). *(continues)* | F-04, F-16 | F-05, F-12, F-18 |
| `J-37` | 297–298 | `B-27` | `L-37` | `L-37`: Supported in code, with three imprecise phrases (F-16). *(continues)* | F-04, F-16 | F-12, F-16, F-18 |
| `J-38` | 300–311 | `B-28` | `L-38` | `L-38`: Supported, except that "cannot disagree" is stronger than the code (F-14). *(continues)* | F-14 | F-02, F-13, F-14 |
| `J-39` | 313–325 | `B-29` | `L-39` | `L-39`: Supported in full. | none | F-02 |
| `J-40` | 326–334 | `B-30` | `L-39`; `L-40` | `L-39`: Supported in full.<br>`L-40`: Supported in code for both readers. *(continues)* | F-18 | F-02, F-12, F-18 |
| `J-41` | 334–339 | `B-30` | `L-40` | `L-40`: Supported in code for both readers. *(continues)* | F-18 | F-02, F-18 |
| `J-42` | 341–345 | `B-31` | `L-41` | `L-41`: Supported. *(continues)* | none | F-02, F-12, F-19, F-20 |
| `J-43` | 347–358 | `B-32` | `L-42` | `L-42`: Supported. *(continues)* | F-07 | F-02, F-07 |
| `J-44` | 360–370 | `B-33` | `L-43` | `L-43`: The commands match the generator. *(continues)* | none | F-05, F-12 |
| `J-45` | 372–377 | `B-34` | `L-43` | `L-43`: The commands match the generator. *(continues)* | none | F-12 |
| `J-46` | 379–390 | `B-35` | `L-44` | `L-44`: Supported except the quoted sentence (F-17). | F-17 | F-12, F-13, F-17 |
| `J-47` | 392–404 | `B-36` | `L-45` | `L-45`: Supported. *(continues)* | none | F-13 |
| `J-48` | 406–414 | `B-37` | `L-46` | `L-46`: Supported, with three narrowings (F-17). *(continues)* | F-17 | F-12, F-13, F-17, F-20 |
| `J-49` | 416–420 | `B-38` | `L-47` | `L-47`: Supported and exemplary. *(continues)* | F-10 | F-10, F-12, F-13 |
| `J-50` | 422–427 | `B-38` | `L-47` | `L-47`: Supported and exemplary. *(continues)* | F-10 | F-13 |
| `J-51` | 428–434 | `B-39` | `L-48` | `L-48`: Supported. *(continues)* | F-09 | F-12 |
| `J-52` | 436–441 | `B-40` | `L-48` | `L-48`: Supported. *(continues)* | F-09 | none |

## Divergences between the journals

Compiled by the coordinator on 2026-11-09 from the journal and the baseline.
This compares two readings with each other. It does not say which is right.

What is and is not listed:

- The journal marks many inferences and the baseline few, because the
  baseline summarizes. A journal inference with no counterpart in the
  baseline is not listed; the report writer judges each journal inference
  anyway, and the join table gives the baseline entry to consult.
- Listed: an uncertainty or carried term only the baseline reader had; a
  point one reader settled at once and the other carried forward; and lines
  from which the two took different meanings.
- Agreement is recorded by absence. The journal writer's close-out has not
  arrived, so "uncertain" for the journal means its per-entry paragraph, not
  an end-of-document status. When the close-out is accepted, add here the
  uncertainties both readers left open at the end.

Each row is adjudicated as `A-Dn` with the same number.

| Divergence | Lines | Journal | Baseline | Difference |
| --- | --- | --- | --- | --- |
| D-01 | Title, C:113 | No question about what PolicyWitness is. The journal writer had read repository guidance. | Close-out, carried terms: "No standalone product definition"; treated as the system the contract governs. | A term only the baseline reader carried. |
| D-02 | C:3-6 | `J-01`: uncertain about the identity's representation and how a failure appears; no question about the artifacts named. | `B-01`, U3: what makes an artifact a saved specimen or a client capture, and how the producers relate. At the end: answered "at the relationship level", structures deferred. | An uncertainty only the baseline reader had. |
| D-03 | C:8-13 | `J-02`: the input inventory is not given; "I do not need the inventory to understand the stated distinction". | `B-01`, U1: which inputs and cleanliness rules determine the identity. Open at the end: "could not independently reproduce every public development digest or decide every release-tree edge case". | The same gap, weighed differently. |
| D-04 | C:82-85 | `J-08`: "A direct XPC caller must not supply those runner-selection fields." | `B-06`: "direct XPC rejects unresolved selection or augments". | Different restatements of the direct-XPC rule for selection fields. |
| D-05 | C:98 | `J-09`: draws a caution, "I cannot assume they describe identical operations or targets merely because they share a step". | `B-07`, U17: "What does a query/attempt comparison claim when their scopes differ?" Open at the end. | One reader settles on a caution; the other is left with a question. |
| D-06 | C:117-118 with C:304-306 | `J-12` and `J-38` record no tension between "no additional schema language or parser generator" and the generator met later. | `B-28`: "This confines entry 9's no-generator rule to requests." | A reconciliation only the baseline reader recorded. |
| D-07 | C:117 | `J-12`: "guide meanings", no question. | Close-out, carried terms: "Guide not uniquely identified". | A reference only the baseline reader could not place. |
| D-08 | C:135 | `J-14`: "I must not interpret a prediction as proof of what the attempted operation will do"; no question about what agreement would take. | `B-10`, U20: "What does enforcement agreement require beyond prediction?" Open at the end: "could not certify enforcement agreement from these observations alone". | An uncertainty only the baseline reader had. |
| D-09 | C:147 | `J-16`: uncertain "where unsupported bytes are exposed". | `B-12`, U24: whether "remain available" means retention without a size limit. Answered at `B-30` from C:328-339 and listed among its changes of mind. | A question only the baseline reader raised, settled much later in the document. |
| D-10 | C:153 | `J-17`: uncertain about the holding mechanism. | `B-13`, U25: "What triggers fallback compilation?" Open at the end. | An uncertainty only the baseline reader had. |
| D-11 | C:176 | `J-21` restates "neither a declaration reply nor a singular worker projection" without question. | `B-16`: the phrase "names something excluded without defining its former shape". U30, open at the end. | Terms only the baseline reader flagged. |
| D-12 | C:180-181 | `J-21`: "An acquired decision does not imply publication of another cell"; it "is not evidence of another cell's publication". | `B-16`: the text "explicitly prevent[s] one acquired decision from publishing another cell". | Different meanings from one sentence: what a decision shows, against what a decision may do. Both readers list "acquired decision" as not understood. |
| D-13 | C:263-264 | `J-32`: optional diagnostic presence "does not itself imply any compatibility exception", settled on the spot from C:100-106. | `B-24`, U42: "Does optional additive information imply any compatibility allowance, despite entry 8's rule?" Answered at `B-31` from C:341-345. | The baseline reader carried a question for about eighty lines that the journal writer settled at once. |
| D-14 | C:267-270 | `J-33`: the passage "does not specify every representation choice for parameter-key failures". | `B-25`, U43: the same, and also whether array positions are strings or numbers. At the end: element representation deferred to `porcelain.json`. | The array-position question is the baseline reader's alone. |
| D-15 | C:297 with C:5-6 | `J-37`: historical storage shapes do "not lead me to expect historical public-contract admission or translation, which lines 3–6 forbid", settled on the spot. | `B-27`, U46: "How do accepted historical registry forms fit the opening ban on historical translation?" Settled by inference at `B-34` from C:372-374. | Both noticed the tension. One resolved it at once, the other carried it. |
| D-16 | C:307-309 | `J-38`: shared derivation "does not check whether the schema itself is correct"; no further question. | `B-28`, U47: "What independently establishes that the schema itself is correct?" Open at the end. | An uncertainty only the baseline reader had. |
| D-17 | C:348-354 | `J-43` restates "fresh-read content", "rejected validator context" and "owned endings" without question. | `B-32`, U54: what these are. Open at the end. | Terms only the baseline reader flagged. |
| D-18 | C:375-377 | `J-45`: infers that a template "is not yet the identity-asserting submitted specimen". | `B-34`, U55: "when is a request treated as an authored template rather than a saved specimen?" Open at the end. | One reader settles by inference; the other is left with a question. |
| D-19 | C:389 | `J-46` restates "Direct source-test builds regenerate in the same way". | `B-35`, U56: which operations "regenerate rather than merely check, particularly for direct source tests". Deferred to `BUILD.md`. | An uncertainty only the baseline reader had. |
| D-20 | C:399-400 | `J-47` restates "the worker and shim" without question. | Close-out, carried terms: "shim not identified precisely". | A term only the baseline reader carried. |

Two differences in kind between the readings, noted so that no row is read
for more than it shows: the readers are different sessions under different
conditions (guidance or none; first pass or reread), and each is one sample.

## Coverage record

The first five columns were filled at acceptance from the line ranges each
artifact cites. Adjudication entries carry the journal's numbers. The last
column is filled in stage 4 with the register rows for the unit, or "none".

| Unit | Lines | Report | Journal | Baseline | Adjudicated | Strains |
| --- | --- | --- | --- | --- | --- | --- |
| U01 | 1–20 | `L-01`–`L-04` | `J-01`–`J-03` | `B-01` | `A-01`–`A-03` | |
| U02 | 22–56 | `L-05`–`L-07` | `J-04`–`J-05` | `B-02`–`B-03` | `A-04`–`A-05` | |
| U03 | 60–124 | `L-08`–`L-15` | `J-06`–`J-12` | `B-04`–`B-09` | `A-06`–`A-12` | |
| U04 | 126–130 | `L-16` | `J-13` | `B-10` | `A-13` | |
| U05 | 132–136 | `L-17` | `J-14` | `B-10` | `A-14` | |
| U06 | 138–142 | `L-18` | `J-15` | `B-11` | `A-15` | |
| U07 | 144–148 | `L-19` | `J-16` | `B-12` | `A-16` | |
| U08 | 150–154 | `L-20` | `J-17` | `B-13` | `A-17` | |
| U09 | 156–160 | `L-21` | `J-18` | `B-14` | `A-18` | |
| U10 | 162–166 | `L-22` | `J-19` | `B-15` | `A-19` | |
| U11 | 168–238 | `L-23`–`L-29` | `J-20`–`J-28` | `B-15`–`B-21` | `A-20`–`A-28` | |
| U12 | 240–244 | `L-30` | `J-29` | `B-22` | `A-29` | |
| U13 | 246–250 | `L-31` | `J-30` | `B-23` | `A-30` | |
| U14 | 252–291 | `L-32`–`L-36` | `J-31`–`J-35` | `B-24`–`B-26` | `A-31`–`A-35` | |
| U15 | 293–298 | `L-37` | `J-36`–`J-37` | `B-27` | `A-36`–`A-37` | |
| U16 | 300–358 | `L-38`–`L-42` | `J-38`–`J-43` | `B-28`–`B-32` | `A-38`–`A-43` | |
| U17 | 360–377 | `L-43` | `J-44`–`J-45` | `B-33`–`B-34` | `A-44`–`A-45` | |
| U18 | 379–425 | `L-44`–`L-47` | `J-46`–`J-50` | `B-35`–`B-38` | `A-46`–`A-50` | |
| U19 | 428–434 | `L-48` (first paragraph) | `J-51` | `B-39` | `A-51` | |
| U20 | 436–441 | `L-48` (second paragraph) | `J-52` | `B-40` | `A-52` | |

The report, the journal and the baseline each cover all twenty units. No
coverage gap is recorded.

## Strain register

Stage 4. The plan names the sources of rows and the dispositions. A
disposition marked "proposed" is the coordinator's and awaits the
maintainer.

### C:243, the compiled-profile paragraph

Opened by the maintainer's close reading, kept verbatim in
`records/contract/CONTRACT-MAINTAINER-NOTES.md`. The coordinator then read
the source the reading describes and found it accurate on every point
checked. Grade for the statements below: source read by the coordinator on
2026-11-09; nothing run.

What the repository does, from that reading:

- **Host, while collecting the worker's capture**
  (`runner/Sources/PWRunnerCore/CWorker.swift`, `decodeProfileCapture`,
  lines 678-716). In order: application succeeded; the worker completed with
  exit 0 and no signal; the capture-completed flag is set; the worker's
  capture status is 1; the recorded PID equals the PID being collected; the
  recorded nonce equals the requested nonce; the profile type is 0 and the
  length is positive and within capacity; the SHA-256 of the bytes read
  equals the recorded digest; the recorded source length, source digest,
  parameter count and parameter digest equal the host's own. The first
  failure returns a receipt with `status: "unavailable"` and a `reason`
  (for the nonce, `capture_nonce_mismatch`), with no bytecode, digest,
  producer or stage. That receipt is published. Only when all pass is the
  receipt `captured`, with `producer: "worker"` and
  `capture_stage: "before_apply"`. Its `request_nonce` is the request's own
  string, not the bytes read back.
- **Readers of a reply** (`controller/src/porcelain_admission.rs`,
  `admission_problem`, lines 1289-1312; the same rule in
  `runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift`,
  `contextProblem`). `status` must be `captured` or `unavailable`; a
  captured receipt must have `producer: "worker"` and
  `capture_stage: "before_apply"`; an unavailable one must have neither. A
  violation makes the whole reply `malformed_runner_response`
  (`controller/src/run_flow.rs`, lines 100-101 and 355-356). No reader
  compares a nonce, PID, length or digest.
- **Around it.** The guide, inside the hashed `profile` region, states the
  host's rule (G:649-652) and then says "Readers require the nested receipt
  version" (G:655). The type's source comment begins "Versioned optional
  receipt" (`PWRunnerProfileCapture.swift`, line 4). The decoder's source
  comment says a mismatch "refuses publication" (`CWorker.swift`, line 669),
  which is the contract example's verb and not what the function does.

| Row | Claims | References | Strain | Sits in | Disposition and reason | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | `K-243-1` | Maintainer's reading; `A-29`; `L-30` | "Inherits its admitted host reply context" names an interpretive relationship with verbs that suggest an operation. It gives no actor and no boundary, and "admitted" cannot mean the reply has passed every check, since the receipt check is part of admitting the reply. | Text | **Rewrite**, proposed. The defensible content, in the maintainer's words: the receipt carries no build identity of its own and is interpreted under the contract of its enclosing reply, whose identity is checked first. | Awaiting maintainer |
| R-02 | `K-243-2` | Maintainer's reading; `F-12`; `F-19` | "No independent schema marker" is true if it means no separate version or contract field. The guide's hashed text says readers require a "nested receipt version", and a source comment calls the receipt "Versioned". | Text, in three places: the contract, G:655, one source comment | **Rewrite**, proposed, in all three. The guide sentence is inside the `profile` region; the comment is in shipped source. | Awaiting maintainer |
| R-03 | `K-243-3` to `K-243-7` | Maintainer's reading; `F-06`; `A-29` | "Status, nonce, worker binding, stage, byte count and digest must be consistent" lists six nouns that stand in at least five different relations with two owners and two different consequences. The host's comparisons end in a published `unavailable` receipt; the reader's label check ends in a refused reply. The list omits the source and parameter comparisons and the conditions for `captured`. "Worker binding" is a PID comparison. | Text for the list. Repository for one question: no reader can repeat the host's comparisons, and the captured receipt's nonce is the request's own string. | **Rewrite**, proposed, stating each rule with its owner and consequence. **Maintainer decision:** whether the absence of any reader-side comparison is intended (then it is stated) or not (then it is an elimination). | Awaiting maintainer |
| R-04 | `K-243-8` | Maintainer's reading; `L-30` | "A detached receipt grants no producer context" changes subject without saying so, uses "grants" for something no code path does, and says "producer" where the reply and the receipt each have a different thing by that name. | Text. Repository for the naming: two fields named `producer` with different meanings. | **Rewrite**, proposed: an extracted receipt does not identify the build that produced it. The duplicate name is recorded for the maintainer; renaming a field is a shape change. | Awaiting maintainer |
| R-05 | `K-243-9` | Maintainer's reading; `F-05`; `F-06`; `A-29`; silence 4 | The example states a rule the implementation does not perform. "Wrong nonce" covers two different failures: a malformed nonce in the request, refused before any capture, and a capture nonce that differs from the requested one, which yields a published `unavailable` receipt. Neither is "refusing the receipt inside a current reply". The point the example is there to make, that a matching build identity does not excuse invalid contents, is made by a different case that does exist: a current reply whose receipt has inconsistent status, producer or stage is refused as malformed. | Text | **Which side is right**, for the maintainer: replace the example with a case that happens and has an owning check, or add the reader-side comparison the sentence describes. The coordinator proposes the first. | Awaiting maintainer |

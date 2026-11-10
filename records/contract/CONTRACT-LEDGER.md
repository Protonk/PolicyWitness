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
| 2026-11-09 | 2 | Ready to begin at step 1 of the plan's order of work. Nothing has been handed to a reader yet. To hand over: the trace deposit and adjudication tasks to the report writer; the close-out task to the journal writer; the baseline reading to an isolated reader launched outside the checkout. |

## Artifacts

| Artifact | Path | Accepted at | Contract read |
| --- | --- | --- | --- |
| Report writer's report | `records/contract/CONTRACT-FIRST-READER-REPORT.md` | `c87bfd80` | Commit `298c1805`, blob `bfd2eded…` (stated in its section 1.1) |
| Journal writer's journal | `records/contract/FRESH-ENCOUNTER-JOURNAL.md` | `214dddd7` | Not stated in the journal. The maintainer states it is the version the report writer read. |
| Report writer's traces | `records/contract/CONTRACT-REPORT-TRACES.md` | not yet delivered | |
| Isolated reader's baseline | `records/contract/ISOLATED-BASELINE-JOURNAL.md` | not yet delivered | |
| Journal writer's addenda | `records/contract/FRESH-ENCOUNTER-ADDENDA.md` | not yet delivered | |
| Adjudication | `records/contract/CONTRACT-ADJUDICATION.md` | not yet delivered | |

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

## Join table

Pairs each journal entry with the report's material for the same lines, so
the adjudication does not repeat the lookup. Generated on 2026-11-09 by a
one-off script from the two accepted artifacts; nothing in it is a judgment.

- *Report group*: every `L-nn` whose line range overlaps the entry's.
- *Report verdict, opening words*: the first sentence after "Verdict." in
  that group, verbatim. "(continues)" means the verdict says more; the
  further sentences often carry qualifications, and stage 3 sweeps them.
- *Findings cited in the group*: `F-nn` named anywhere in the group's text.
- *Findings citing these lines*: `F-nn` whose section 7 text cites a `C:`
  line or range overlapping the entry's. Some findings cite a whole region,
  so this column over-includes; it is an index, not a claim of relevance.

| Journal | Lines | Report group | Report verdict, opening words | Findings cited in the group | Findings citing these lines |
| --- | --- | --- | --- | --- | --- |
| `J-01` | 1–6 | `L-01` | `L-01`: Supported for `policy-witness run` and the XPC host. *(continues)* | F-09, F-10 | F-09, F-10, F-12, F-20 |
| `J-02` | 8–15 | `L-02`; `L-03` | `L-02`: Partly supported. *(continues)*<br>`L-03`: Supported. *(continues)* | F-09, F-11 | F-09, F-11, F-18 |
| `J-03` | 17–20 | `L-04` | `L-04`: The denial is supported. *(continues)* | F-03 | F-03 |
| `J-04` | 22–50 | `L-05`; `L-06` | `L-05`: Supported. *(continues)*<br>`L-06`: Supported as generated output. *(continues)* | F-01, F-03 | F-01, F-03, F-04, F-12 |
| `J-05` | 52–56 | `L-07` | `L-07`: Supported. *(continues)* | F-12 | F-12 |
| `J-06` | 58–63 | `L-08` | `L-08`: Supported. *(continues)* | none | F-05, F-20 |
| `J-07` | 65–75 | `L-09` | `L-09`: Partly supported. *(continues)* | F-08, F-09, F-12 | F-02, F-08, F-09, F-12 |
| `J-08` | 77–85 | `L-10` | `L-10`: Supported except "resolved meaning is recorded in runner provenance", which is partly supported *(continues)* | none | none |
| `J-09` | 87–98 | `L-11` | `L-11`: Supported. *(continues)* | none | F-08 |
| `J-10` | 100–106 | `L-12` | `L-12`: The first sentence is supported for tracked scoped sources and not for build variants (F-10, F-11). *(continues)* | F-03, F-05, F-10, F-11, F-12, F-13 | F-03, F-05, F-10, F-11, F-12, F-13 |
| `J-11` | 108–114 | `L-13` | `L-13`: Supported. *(continues)* | F-13 | F-13 |
| `J-12` | 116–124 | `L-14`; `L-15` | `L-14`: The disclaimer is a useful restriction and is consistent with the design. *(continues)*<br>`L-15`: Supported. *(continues)* | F-12, F-13 | F-01, F-12, F-13 |
| `J-13` | 126–130 | `L-16` | `L-16`: Supported in code. *(continues)* | F-05 | F-05 |
| `J-14` | 132–136 | `L-17` | `L-17`: Supported. *(continues)* | F-05 | F-05, F-12 |
| `J-15` | 138–142 | `L-18` | `L-18`: Supported. *(continues)* | F-08, F-12 | F-05, F-08 |
| `J-16` | 144–148 | `L-19` | `L-19`: Supported, with one precision. *(continues)* | F-05 | F-05, F-20 |
| `J-17` | 150–154 | `L-20` | `L-20`: Supported in code. *(continues)* | F-05 | F-05, F-18 |
| `J-18` | 156–160 | `L-21` | `L-21`: Supported. *(continues)* | F-07 | F-05, F-20 |
| `J-19` | 162–166 | `L-22` | `L-22`: Supported in producer and controller. *(continues)* | none | F-05, F-12 |
| `J-20` | 168–171 | `L-23` | `L-23`: Supported, with qualifications. *(continues)* | none | F-05, F-07, F-12 |
| `J-21` | 173–181 | `L-24` | `L-24`: The first three statements are supported in producer and reader (†). *(continues)* | F-12, F-15 | F-02, F-07, F-12, F-15 |
| `J-22` | 183–191 | `L-25` | `L-25`: Supported in producer and reader for the structural rules (†). *(continues)* | F-15 | F-07, F-12, F-15 |
| `J-23` | 191–196 | `L-25` | `L-25`: Supported in producer and reader for the structural rules (†). *(continues)* | F-15 | F-07, F-12, F-18 |
| `J-24` | 198–202 | `L-26` | `L-26`: Supported, read as "a reply violating this is flagged" (F-07). *(continues)* | F-07, F-15 | F-07, F-12, F-15 |
| `J-25` | 204–210 | `L-27` | `L-27`: Supported. *(continues)* | none | F-07, F-12, F-18 |
| `J-26` | 212–220 | `L-28` | `L-28`: Supported. *(continues)* | F-12, F-15 | F-07, F-12, F-15 |
| `J-27` | 220–228 | `L-28` | `L-28`: Supported. *(continues)* | F-12, F-15 | F-07, F-12 |
| `J-28` | 230–238 | `L-29` | `L-29`: Supported in reader and producer, with constructed negatives and a default signed assertion for the failed-gate case (†). | none | F-07, F-12 |
| `J-29` | 240–244 | `L-30` | `L-30`: Partly supported *(continues)* | F-06 | F-05, F-06, F-12, F-19 |
| `J-30` | 246–250 | `L-31` | `L-31`: Supported in code. *(continues)* | F-10 | F-05, F-12, F-19, F-20 |
| `J-31` | 252–255 | `L-32` | `L-32`: Supported. *(continues)* | F-12 | F-05, F-12, F-20 |
| `J-32` | 256–264 | `L-33` | `L-33`: Supported. *(continues)* | none | F-02 |
| `J-33` | 266–271 | `L-34` | `L-34`: Supported. | none | F-20 |
| `J-34` | 273–284 | `L-35` | `L-35`: Every listed code exists as a literal in controller or runner source (author's search) and has a reachable emit site (†). *(continues)* | F-08, F-12 | F-08, F-12 |
| `J-35` | 286–291 | `L-36` | `L-36`: Supported, except that "capacity checks precede meaning checks" is not true of rules enforced at decode time (F-08). *(continues)* | F-08 | F-08, F-20 |
| `J-36` | 293–296 | `L-37` | `L-37`: Supported in code, with three imprecise phrases (F-16). *(continues)* | F-04, F-16 | F-05, F-12, F-18 |
| `J-37` | 297–298 | `L-37` | `L-37`: Supported in code, with three imprecise phrases (F-16). *(continues)* | F-04, F-16 | F-12, F-16, F-18 |
| `J-38` | 300–311 | `L-38` | `L-38`: Supported, except that "cannot disagree" is stronger than the code (F-14). *(continues)* | F-14 | F-02, F-13, F-14 |
| `J-39` | 313–325 | `L-39` | `L-39`: Supported in full. | none | F-02 |
| `J-40` | 326–334 | `L-39`; `L-40` | `L-39`: Supported in full.<br>`L-40`: Supported in code for both readers. *(continues)* | F-18 | F-02, F-12, F-18 |
| `J-41` | 334–339 | `L-40` | `L-40`: Supported in code for both readers. *(continues)* | F-18 | F-02, F-18 |
| `J-42` | 341–345 | `L-41` | `L-41`: Supported. *(continues)* | none | F-02, F-12, F-19, F-20 |
| `J-43` | 347–358 | `L-42` | `L-42`: Supported. *(continues)* | F-07 | F-02, F-07 |
| `J-44` | 360–370 | `L-43` | `L-43`: The commands match the generator. *(continues)* | none | F-05, F-12 |
| `J-45` | 372–377 | `L-43` | `L-43`: The commands match the generator. *(continues)* | none | F-12 |
| `J-46` | 379–390 | `L-44` | `L-44`: Supported except the quoted sentence (F-17). | F-17 | F-12, F-13, F-17 |
| `J-47` | 392–404 | `L-45` | `L-45`: Supported. *(continues)* | none | F-13 |
| `J-48` | 406–414 | `L-46` | `L-46`: Supported, with three narrowings (F-17). *(continues)* | F-17 | F-12, F-13, F-17, F-20 |
| `J-49` | 416–420 | `L-47` | `L-47`: Supported and exemplary. *(continues)* | F-10 | F-10, F-12, F-13 |
| `J-50` | 422–427 | `L-47` | `L-47`: Supported and exemplary. *(continues)* | F-10 | F-13 |
| `J-51` | 428–434 | `L-48` | `L-48`: Supported. *(continues)* | F-09 | F-12 |
| `J-52` | 436–441 | `L-48` | `L-48`: Supported. *(continues)* | F-09 | none |

## Divergences between the journals

Not yet filled. When the baseline is accepted, the coordinator lists here
where it and the journal differ over the same lines, as the plan describes.

| Divergence | Lines | Journal | Baseline | Difference |
| --- | --- | --- | --- | --- |

## Coverage record

The first four columns were filled at acceptance from the line ranges each
artifact cites. The baseline's entries are added when it is accepted. The
last two columns are filled after adjudication.

| Unit | Lines | Report | Journal | Adjudicated | Result |
| --- | --- | --- | --- | --- | --- |
| U01 | 1–20 | `L-01`–`L-04` | `J-01`–`J-03` | | |
| U02 | 22–56 | `L-05`–`L-07` | `J-04`–`J-05` | | |
| U03 | 60–124 | `L-08`–`L-15` | `J-06`–`J-12` | | |
| U04 | 126–130 | `L-16` | `J-13` | | |
| U05 | 132–136 | `L-17` | `J-14` | | |
| U06 | 138–142 | `L-18` | `J-15` | | |
| U07 | 144–148 | `L-19` | `J-16` | | |
| U08 | 150–154 | `L-20` | `J-17` | | |
| U09 | 156–160 | `L-21` | `J-18` | | |
| U10 | 162–166 | `L-22` | `J-19` | | |
| U11 | 168–238 | `L-23`–`L-29` | `J-20`–`J-28` | | |
| U12 | 240–244 | `L-30` | `J-29` | | |
| U13 | 246–250 | `L-31` | `J-30` | | |
| U14 | 252–291 | `L-32`–`L-36` | `J-31`–`J-35` | | |
| U15 | 293–298 | `L-37` | `J-36`–`J-37` | | |
| U16 | 300–358 | `L-38`–`L-42` | `J-38`–`J-43` | | |
| U17 | 360–377 | `L-43` | `J-44`–`J-45` | | |
| U18 | 379–425 | `L-44`–`L-47` | `J-46`–`J-50` | | |
| U19 | 428–434 | `L-48` (first paragraph) | `J-51` | | |
| U20 | 436–441 | `L-48` (second paragraph) | `J-52` | | |

The report and the journal each cover all twenty units. No coverage gap is
recorded.

## Findings

No rows yet. Rows are created in stage 3, after adjudication, from the
sources the plan names.

| Row | Units | Sources | Finding | Class | Decision and reason | Status |
| --- | --- | --- | --- | --- | --- | --- |

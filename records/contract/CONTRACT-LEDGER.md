# CONTRACT.md examination ledger

The working record of the examination defined in
`records/contract/CONTRACT-CONTACT-PLAN.md`: where the work stands, what was
accepted from each reader, which parts of the contract have been covered, and
what became of each finding. The plan says how each part is filled. Sibling
artifacts are named by path without links, under the records link rule.

## Stage log

| Date | Stage | Event |
| --- | --- | --- |
| 2026-11-09 | 1 | Report accepted at `c87bfd80`, journal at `214dddd7`. Acceptance record below. Two shortfalls are handled in stage 2 and await the maintainer's confirmation. |
| 2026-11-09 | 2 | Ready to begin. Step 1: hand the experienced reader its first task and the fresh reader its close-out. Nothing has been handed over yet. |

## Artifacts

| Role | Path | Accepted at | Contract read |
| --- | --- | --- | --- |
| Experienced reader's report | `records/contract/CONTRACT-FIRST-READER-REPORT.md` | `c87bfd80` | Commit `298c1805`, blob `bfd2eded…` (stated in its section 1.1) |
| Fresh reader's journal | `records/contract/FRESH-ENCOUNTER-JOURNAL.md` | `214dddd7` | Not stated. The blob of `docs/CONTRACT.md` at `214dddd7` is `bfd2eded…` |

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
| Says what the author opened | Partly. Section 1.2 lists what was read, and the journal is not on the list; there is no explicit statement that it was not seen. The report's commit precedes the journal's. |
| Commit changes nothing else | Yes. |

**Shortfall.** Non-exposure to the journal is implicit. **Handling.** The
experienced reader's first task begins with a declaration.

Limits the report states about itself, which later stages must carry:

- Most source tracing was delegated and is marked †.
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
stated. **Handling.** The revision is established above from the commit. The
fresh reader's close-out records both.

Notes for later stages:

- The fresh reader read repository guidance before the contract. The plan's
  adjudication task carries a caution about beliefs that guidance could have
  supplied.
- The journal's source links are absolute paths into this checkout. They
  resolve only at this location. Not repaired.
- No out-of-role content was identified at acceptance. The adjudication's
  "not adjudicated" section is the place for any.

## Coverage record

The first four columns were filled at acceptance from the line ranges each
artifact cites. The last two are filled after adjudication.

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

Both readers covered all twenty units. No coverage gap is recorded.

## Findings

No rows yet. Rows are created in stage 3, after adjudication, from the four
sources the plan names.

| Row | Units | Sources | Finding | Class | Decision and reason | Status |
| --- | --- | --- | --- | --- | --- | --- |

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
| 2026-11-09 | 2 | Journal writer's fifteen answers accepted at `8323f54f`. Stage 2 is complete. The journal writer can be released. |
| 2026-11-09 | 6 | Maintainer decided `R-01` to `R-05`. Change made and committed at `a7d9b320`, ahead of the structure stage at the maintainer's direction; mechanically verified. Outstanding for it: stage 7 review and reading, `R-06`, and a rebuild before any app-dependent case. |
| 2026-11-09 | 3 | Six further owner-finding passes started, covering every unit not yet inventoried, with the four-slot brief. |
| 2026-11-09 | 3 | The six passes returned 238 rows. The inventory now has 332 rows over every unit: 240 owned, 45 sourced, 32 split, 15 unowned, as the passes state them. Of the 238 rows asked, the sentence does not state who acts in 159, the boundary in 165, or the consequence in 133. Stage 3's exit condition is met; nothing in it has been run. Stage 4 proceeds by the maintainer's focus items and by the sources the plan names. |
| 2026-11-10 | 4 | Maintainer supplied a second close reading, of C:165-236 and C:351-355. Coordinator read the source it turns on and opened register rows `R-07` to `R-20`, all proposals. `R-06` also still awaits the maintainer. |
| 2026-11-10 | 4 | Maintainer supplied a third close reading, of C:3-56, C:100-106 and C:430-434, with a direction for stage 5: the contract is to be generated and remain the public account. Coordinator ran the stamp generator in a tagless scratch clone and opened rows `R-21` to `R-32`. Finding from the run: regeneration with `--release` and no history rewrites every stamp. |
| 2026-11-10 | 4 | Maintainer asked for a consolidated account of a run's result in the guide, with `R-20` kept open. Drafted for review in `records/contract/GUIDE-RESULT-ACCOUNT-DRAFT.md` as `R-33`. The draft's placement would move text between the guide's `envelope`, `refusals` and `lifecycle` regions. |
| 2026-11-10 | 4 | Maintainer's comment on `R-14` recorded and the row corrected. A delegated read-only comparison of the three validators on preparation-failure and reporting-failure replies was started, to establish where their final judgments diverge. |
| 2026-11-10 | 4 | The validator comparison returned thirteen inferred candidates. A run of them through all three readers was started in a disposable worktree. |
| 2026-11-10 | 4 | Maintainer's comment on `R-07` recorded. Coordinator read the controller's projection and opened `R-34` (the scope of "dependent") and `R-35` (`per_actor` missing from the guide's vocabulary). |
| 2026-11-10 | 4 | The run of the validator candidates returned and is deposited under `records/contract/validators/`. Final judgments diverge on twelve of thirteen candidates. `R-36` opened. The experiment's worktree and branch were removed. |
| 2026-11-10 | 4 | Maintainer's position on `R-36` recorded, with a correction to the coordinator's "same bytes" wording. The disputed definitions and scopes are drafted for review in `records/contract/validators/DEFINITIONS-AND-SCOPES.md`. The position also adds to the stage 5 direction: definitions, applicability, obligations. |
| 2026-11-10 | — | The maintainer set a four-stage course: restructure the contract against the current implementation, change what is hard to state, settle the contract, edit the guide. Outlined in `docs/CONTRACT-STAGING-PLAN.md` (`d98303a9`). The examination's stage 4 register feeds it; no further close reading is planned. |
| 2026-11-10 | — | Proposed structure for the restructured contract, with a worked section, in `records/contract/CONTRACT-STRUCTURE-PROPOSAL.md`, for review before stage one is drafted. |
| 2026-11-10 | — | Maintainer reviewed the structure proposal in eight points, recorded in the notes. Second version written: no reading-instructions section, body by public operation with the trio inside each, no maintenance appendix, rules with separately identified conditions, production and interpretation stated apart, field meaning in the contract. The staging plan in `docs/` carries the same points. |
| 2026-11-10 | — | Maintainer's second review of the structure proposal recorded. Third version written: three kinds of rule (acts, reports, checks); the reach of a consequence as reads, decides, prevents or withholds, and leaves; four relationships with a defined expression; and a second worked example, a termination gate, read in source by the coordinator. Reading for it found that a failed gate cancels every later phase of every actor, which the contract does not say; and that a controller finding carries no reference to the gate it concerns. |
| 2026-11-10 | — | Maintainer's third review recorded. It sets what is brought to the maintainer: behavioral commitments, and a grouping only when it hides a distinction a consumer needs, presented as the distinction, why it matters and the commitment that would change. The working taxonomy and the meaning of an existing outcome are the coordinator's to settle from source. Outcome meanings for the gate are now stated in the proposal. `R-37` and `R-38` opened for the two commitments the gate reading found. |
| 2026-11-10 | — | Authoring model settled with the maintainer: the contract is a generated tree, authored as Markdown under `docs/contract/`, with structured facts beside prose, subordination carrying subsidiary relationships, derived views, and a baseline of free-text items that only shrinks. Written into `docs/CONTRACT-STAGING-PLAN.md`, with stage one's first steps. The examination plan's stages 5 to 8 are marked superseded. Standing by; nothing is in motion. |

### Review after the coordinator handoff

The maintainer authorized review and repairs after `4a3e5202`, while keeping
behavioral decisions open. The staging plan and structure proposal now:

- distinguish behavioral decisions from missing evidence, keep the rule
  model revisable, and allow the guide consolidation already requested for
  `R-33`;
- specify that public content and shape goldens affect surface stamps,
  while source/test citations and evidence grades are checked separately.
  This boundary was explicitly selected by the maintainer during the review;
- include both worked sections in full. Source reads establish receipt
  absence on preparation failure, the meaning of `profile_type`, the
  `done` prerequisite, and the reporting of skipped gates and later phases;
- correct the gate's budget wording and finding multiplicity, retain the
  distinction between a failed evaluated gate and an unevaluated gate, and
  narrow `R-38` to the missing subject in gate findings;
- do not use the `R-36` experiment as proof of a gate-specific validator
  disagreement. The original comparison, experiment report and patch are
  unchanged. `R-14` now points to the completed comparison.

The worked sections cite source and tests that were read; no new gate or
capture execution is claimed. Product behavior and the published contract
were not changed. The authoring generator has not been built. `R-06`,
`R-20`, `R-29`, `R-36`, `R-37` and `R-38` retain their outstanding work or
decisions.

Validation: `env -u PYTHONOPTIMIZE
PW_TEST_OUT_DIR=tests/out/runs/contract-review-repairs-20261110
tests/run.sh --suite source_drift` completed all ten selected cases, all
passing, without system sleep. This checks the documentation and existing
generator contracts; it is not execution evidence for the worked examples.
The run is disposable development evidence under the normal retention rules.

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
column indexes existing register rows by their cited contract lines. It is
partial: reconciliation of the report and adjudication remains pending for
every unit. "No row yet" is not a judgment that a unit has no strain. Record
"examined, no strain" only after the reconciliation required by stage one
of `docs/CONTRACT-STAGING-PLAN.md`.

| Unit | Lines | Report | Journal | Baseline | Adjudicated | Strains |
| --- | --- | --- | --- | --- | --- | --- |
| U01 | 1–20 | `L-01`–`L-04` | `J-01`–`J-03` | `B-01` | `A-01`–`A-03` | `R-21`–`R-25`, `R-32` |
| U02 | 22–56 | `L-05`–`L-07` | `J-04`–`J-05` | `B-02`–`B-03` | `A-04`–`A-05` | `R-26`–`R-29`, `R-32` |
| U03 | 60–124 | `L-08`–`L-15` | `J-06`–`J-12` | `B-04`–`B-09` | `A-06`–`A-12` | `R-30`, `R-32` |
| U04 | 126–130 | `L-16` | `J-13` | `B-10` | `A-13` | No row yet |
| U05 | 132–136 | `L-17` | `J-14` | `B-10` | `A-14` | No row yet |
| U06 | 138–142 | `L-18` | `J-15` | `B-11` | `A-15` | No row yet |
| U07 | 144–148 | `L-19` | `J-16` | `B-12` | `A-16` | No row yet |
| U08 | 150–154 | `L-20` | `J-17` | `B-13` | `A-17` | No row yet |
| U09 | 156–160 | `L-21` | `J-18` | `B-14` | `A-18` | No row yet |
| U10 | 162–166 | `L-22` | `J-19` | `B-15` | `A-19` | `R-07`, `R-20`, `R-34`, `R-35` |
| U11 | 168–238 | `L-23`–`L-29` | `J-20`–`J-28` | `B-15`–`B-21` | `A-20`–`A-28` | `R-08`–`R-19`, `R-36`, `R-37` |
| U12 | 240–244 | `L-30` | `J-29` | `B-22` | `A-29` | `R-01`–`R-06` |
| U13 | 246–250 | `L-31` | `J-30` | `B-23` | `A-30` | No row yet |
| U14 | 252–291 | `L-32`–`L-36` | `J-31`–`J-35` | `B-24`–`B-26` | `A-31`–`A-35` | No row yet |
| U15 | 293–298 | `L-37` | `J-36`–`J-37` | `B-27` | `A-36`–`A-37` | No row yet |
| U16 | 300–358 | `L-38`–`L-42` | `J-38`–`J-43` | `B-28`–`B-32` | `A-38`–`A-43` | `R-19`, `R-20`, `R-34`, `R-38` |
| U17 | 360–377 | `L-43` | `J-44`–`J-45` | `B-33`–`B-34` | `A-44`–`A-45` | No row yet |
| U18 | 379–425 | `L-44`–`L-47` | `J-46`–`J-50` | `B-35`–`B-38` | `A-46`–`A-50` | No row yet |
| U19 | 428–434 | `L-48` (first paragraph) | `J-51` | `B-39` | `A-51` | `R-31`, `R-32` |
| U20 | 436–441 | `L-48` (second paragraph) | `J-52` | `B-40` | `A-52` | No row yet |

The report, the journal and the baseline each cover all twenty units. No
unit is absent from those readings; that does not establish that every
finding has a disposition. The claim inventory covers `CONTRACT.md` only,
not the guide regions incorporated by the surface manifest. Those regions
need their own coverage and destination map before migration.

The reconciliation must carry `F-02` (rendered boundaries), `F-08` (open
vocabularies, ordering and nulls), `F-14` (limits of generated structural
agreement), `F-16` (registry preservation and read-back), and `F-17`
(internal identity and regeneration) into explicit dispositions. They have
no dedicated register disposition yet. Removing the denial in `R-23` also
does not settle `F-09`'s shipped-helper and instrumented-entry-path questions.
The adjudication's corrections, silences and unresolved meanings remain
inputs even where a related register row exists.

## Strain register

Stage 4. The plan names the sources of rows and the dispositions. A
disposition marked "proposed" is the coordinator's and awaits the
maintainer.

### C:243, the compiled-profile paragraph

Opened by the maintainer's close reading, kept verbatim in
`records/contract/CONTRACT-MAINTAINER-NOTES.md`. The coordinator then read
the source the reading describes and found it accurate on every point
checked.

**What the repository does.** Source read by the coordinator on 2026-11-09.

- **Host, while collecting the worker's capture**
  (`runner/Sources/PWRunnerCore/CWorker.swift`, `decodeProfileCapture`). In
  order: application succeeded; the worker exited with status 0 and no
  signal; the capture-completed flag is set; the worker's capture status is
  1; the recorded PID equals the PID being collected; the recorded nonce
  equals the requested nonce; the profile type is 0 and the length is
  positive and within capacity; the SHA-256 of the bytes read equals the
  recorded digest; the recorded source length, source digest, parameter
  count and parameter digest equal the host's own. The first failure
  returns a receipt with `status: "unavailable"` and a `reason` (for the
  nonce, `capture_nonce_mismatch`), with no bytecode, digest, producer or
  stage. That receipt is published; the reply is not refused. Only when all
  pass is the receipt `captured`, with `producer: "worker"` and
  `capture_stage: "before_apply"`. Its `request_nonce` is the request's
  string, published after the equality check.
- **Controller, reading a reply** (`controller/src/run_flow.rs`,
  `reply_contract`; `controller/src/porcelain_admission.rs`,
  `admission_problem`). It compares the reply's `producer.contract` first.
  Then, for each receipt: `status` must be `captured` or `unavailable`; a
  captured receipt must have `producer: "worker"` and
  `capture_stage: "before_apply"`; an unavailable one must have neither. A
  violation classifies the reply as `malformed_runner_response`. These are
  the controller's only uses of receipt fields outside the generated record
  code (checked by search).
- **Host, before encoding its own result**
  (`runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift`,
  `contextProblem`; `PWRunnerService.swift`, `pwRunnerReportData`). The same
  label rule, with a different consequence: the host re-issues its result
  as `runner_reporting_failed` with a `reporting_failure` record. This is
  not a refusal by a reader and is not `malformed_runner_response`.
- **What a reader could check and does not.** Maintainer's correction of
  2026-11-09 to the coordinator's first account, which wrongly said no
  reader could repeat the host's comparisons.
  - *Possible from the reply alone, not done by the current readers:*
    compare the receipt's byte count with its decoded bytecode, and recompute
    the bytecode digest.
  - *Possible for a consumer holding its own request, not done by the
    controller:* compare the request's nonce with the receipt's
    `request_nonce`. Equality associates the receipt with that request and
    would expose a wrong association or an altered receipt. It cannot
    establish that the host made its comparison against the worker's
    capture.
  - *Not possible for any reader:* the comparisons that need the worker's
    shared memory or the host's own observations, which are the recorded
    PID against the collected worker, the worker's recorded nonce, the
    completion flag and capture status, and the application and exit
    conditions.
  - *Not examined:* whether a consumer could recompute the source and
    parameter digests from its request.

**Decision.** Maintainer, 2026-11-09: correct the prose and comments;
preserve the current validation behavior, the division of responsibility
and both `producer` field names; keep the consumer's responsibility to
associate a receipt with its own request explicit; attribute each
consequence to its component.

**Meaning statement.** After the change the passage commits to these, each
describing existing behavior: the receipt has no contract or version field
and is read under the contract of the reply that carries it, which the
controller checks first; an extracted receipt does not identify its build;
the two `producer` fields mean different things; the host publishes
`captured` only when its listed conditions hold and otherwise withholds the
capture data and publishes an `unavailable` receipt with a reason, without
refusing the reply; the controller checks the labels only and classifies a
violating reply as `malformed_runner_response`; the controller does not
compare nonce, PID, byte count or digest; a consumer ties a receipt to its
request by the nonce, which does not show the host compared the capture; a
malformed `capture_nonce` is a request refusal. Withdrawn: the rule that a
wrong nonce refuses a receipt inside a current reply, which nothing
performed.

**Change.** `a7d9b320`: the contract's `profile` paragraph (kept on one
physical line, so the document's other line numbers are unchanged); two
sentences of the guide's `profile` region; the doc comments on
`CompiledProfileCapture` and above `captureNonceBytes`. Regenerated: the
stamp table, where `profile` now reads `unreleased`, and the worker
identity with its three copies, because the comments are in hashed Swift
files.

**Verification.** Generator checks for stamps (with history), worker
identity, limits, porcelain and architecture pass. Run
`tests/out/runs/contract-c243` at the tree committed as `a7d9b320`: the
`source_drift` suite and `unit/rust.unit` pass. That output is local and
disposable. The installed app under `dist/` predates the new worker
identity and has not been rebuilt, so no case that needs the app has been
run against this change.

**Owner of the new example.** `controller/src/run_flow.rs`,
`compiled_profile_context_is_gated_after_the_response_version`, in the
default case `unit/rust.unit`, over the fixture
`tests/fixtures/contract/compiled_profile.json`, whose `producer_future`
case is a `captured` receipt with a producer other than `worker`. Grade:
run, in the run above. It asserts that the reply is not admitted. It does
not assert the outcome string: the step from "not admitted" to
`malformed_runner_response` is the `Malformed` arm in `run_flow.rs`, source
read, with no test of that step for this cause. Recorded as `R-06`.

| Row | Claims | References | Strain | Sits in | Disposition and reason | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | `K-243-1` | Maintainer's reading; `A-29`; `L-30`; answer 2 | "Inherits its admitted host reply context" names an interpretive relationship with verbs that suggest an operation, with no actor and no boundary. | Text | **Rewrite.** Maintainer's decision. | Changed at `a7d9b320`; mechanically verified; stage 7 review and reading outstanding |
| R-02 | `K-243-2` | Maintainer's reading; `F-12`; `F-19` | "No independent schema marker" beside a guide sentence requiring a "nested receipt version" and a source comment calling the receipt "Versioned". | Text, in three places | **Rewrite** in all three. Maintainer's decision. | Changed at `a7d9b320`; as above |
| R-03 | `K-243-3` to `K-243-7` | Maintainer's reading; `F-06`; `A-29`; answers 2 and 8 | A list of six nouns standing for several relations with different owners and consequences, omitting the source and parameter comparisons and the conditions for `captured`. | Text | **Rewrite**, stating each rule with its owner and consequence, what the controller does not compare, and the consumer's own comparison. The existing division of responsibility is intended and preserved. Maintainer's decision. | Changed at `a7d9b320`; as above |
| R-04 | `K-243-8` | Maintainer's reading; `L-30` | "A detached receipt grants no producer context": a changed subject, a verb for something no code path does, and one name for two fields. | Text | **Rewrite**, explaining the two `producer` fields by their qualified locations. Both names stay. Maintainer's decision. | Changed at `a7d9b320`; as above |
| R-05 | `K-243-9` | Maintainer's reading; `F-05`; `F-06`; `A-29`; silence 4; answers 6 and 8 | The example stated a rule nothing performed and merged two different nonce failures. The journal writer, asked, expected "a request-aware acceptance step to refuse that receipt" and would rely on an example's behavior without checking it. | Text | **Rewrite**: replaced by a case the controller rejects, with its owning check. The source comment's "refuses publication" now names what is withheld and what is published. Maintainer's decision. | Changed at `a7d9b320`; as above |
| R-06 | New example at C:243 | Coordinator | No test asserts that a receipt-label violation yields the outcome `malformed_runner_response`; the owning test stops at "not admitted". | Repository: a missing check | **Proposed: eliminate**, by asserting the outcome in the existing test. Outside the scope the maintainer set for this change. | Awaiting maintainer |

### C:165-236 and C:351-355, lifecycle, equipment and the publication rule

Opened by the maintainer's close reading of 2026-11-10, kept verbatim in
`records/contract/CONTRACT-MAINTAINER-NOTES.md`. No disposition here is
decided. Each is the coordinator's proposal and awaits the maintainer.

**What the coordinator read first-hand on 2026-11-10** (source read; nothing
run), on the points the reading turns on:

- **Success does not follow integrity.** `controller/src/run_flow.rs`,
  `complete_execution`: `ok` is `runner_outcome == "finished"` and the exit
  code is 0 or 1 from that alone. The controller's diagnostics are computed
  just before and do not enter it. A controller test asserts exit code 0
  together with `disposition_integrity: "invalid"`,
  `process_disposition: "withheld"` and `termination_cause: "unknown"`, and
  that `data.runner_result` round-trips equal to the host's reply.
- **Where the controller's findings appear.**
  `controller/src/porcelain_admission.rs`, `execution_diagnostics`: any issue
  from the reply's validators sets `process_disposition: "withheld"`,
  `termination_cause: "unknown"` and `disposition_integrity: "invalid"` and
  appends the issues, in `data.runner_sandbox_diagnostics`. The host's
  records in `data.runner_result` are published as received, including a
  field the finding contradicts.
- **A refused reply keeps its decoded record.** `run_flow.rs`: "A decoded
  reply stays in the envelope on every refusal; nothing interprets it before
  admission."
- **A degraded reply is checked differently.** With `reporting_failure`
  present the controller checks the shape of the degradation itself, and the
  same test shows no `phase_collection` issue is raised for it.
- **Ordinals.** The counter is a field of the host's record for each child
  process (`runner/Sources/PWRunnerCore/CWorker.swift`,
  `nextCaptureOrdinal`). An actor's activation takes the next value of its
  own process's counter (`ActorSession.swift`, `activate`). A gate takes the
  next value of the source's counter (`ActorScheduler.swift`). The host
  keeps every counter; the worker does not.

**Taken from inventory rows, not re-read by the coordinator** (delegated
reads):

- "Withhold" is rendered three ways, by where the problem is found
  (`K-165-2`): the host emits a disposition `state` of `unresolved` or
  `conflicting`; the controller projects those to `process_disposition`
  `unconfirmed` or `conflicting`; and any validator issue overwrites the
  projection with `withheld`.
- The "partition" is the rule that the set of all phases' action
  identifiers equals the set of step identifiers plus extension-event
  identifiers (`K-202-1`). Three hand-written readers skip it under
  different conditions: the controller and the host's self-check when a
  `preparation_failure` is present, the Python reader only when it is valid.
  With `reporting_failure` present neither the host's self-check nor the
  controller evaluates it.
- For the first clause of C:180-181, the host loads the worker's decision
  word with an acquire load and reads operation cells separately; a decision
  without a failed or rejected primary cell is recorded as an integrity
  error and no cell is created (`K-180-1`). Nothing in source or
  documentation is called a "scheduling summary".
- Nothing prevents an actor bound to an override row from being matched,
  eligible and run (`K-188-1`; report `F-15`).
- The terminal-failure list behind `not_attempted` is hand-copied in Swift,
  Rust and Python, and the Python reader has no application precedence check
  (`K-205-1` and its neighbors).
- Whether a setup timeout can coexist with an observed application, both
  reported, has not been traced to a source or a check.

| Row | Claims | References | Strain | Sits in | Proposed disposition | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-07 | `K-165-2` | Reading; maintainer's comment of 2026-11-10 on this row; `F-07`; answer 7; the section "Withholding, as implemented" below | "Withhold dependent claims" has no referent, and the host's and the controller's words for the same missing evidence differ without a stated difference in meaning: the host's claim is `unresolved`, the controller's summary is `unconfirmed`. | Text, and repository vocabulary | **Rewrite**, proposed: one table giving each controller value and the host state it comes from. **Maintainer:** whether `unconfirmed` should exist beside `unresolved` and `inapplicable`, given that it renames and merges them; changing a public value is a change of shape. | Awaiting maintainer |
| R-08 | `K-171-2` | Reading; `L-23`; `F-10` | "The worker ABI identity remains independent of the public build identity" interrupts the equipment association and does not say independent in what respect. Their source scopes overlap. | Text, and placement | **Rewrite**: say what each identity governs and that neither substitutes for the other, at the place where the internal identity is described (C:379-425 already has most of it), and remove it here. | Awaiting maintainer |
| R-09 | `K-171-1` | Reading; `L-23` | "Binds observations to the named process and service-sealed equipment" covers three operations that establish different things: checking packaged equipment, inspecting a running process, validating reported associations. | Text | **Rewrite**: state what the association asserts, then how the inventory, binding and entitlement fields represent it. | Awaiting maintainer |
| R-10 | `K-176-1`, `K-176-2` | Reading; `F-12`; `A-D11` | The actor records are introduced by denying a "declaration reply" and a "singular worker projection", neither defined anywhere. | Text (residue) | **Rewrite**: remove the denial; keep the positive statement about `actors[]`. | Awaiting maintainer |
| R-11 | `K-180-1`, `K-181-1` | Reading; `F-15`; `A-21`; `A-D12` | "An acquired decision does not publish another cell, and a scheduling summary does not replace any actor's facts." The first clause has a mechanism the sentence does not give; the second names no field and no operation. Two readers took opposite meanings from it. | Text | **Rewrite**: remove the sentence once the records and their consequences are described. If a concrete case replaces it, the maintainer's candidate (a setup timeout beside an observed application, both reported) first needs a source and an owning check. | Awaiting maintainer |
| R-12 | `K-188-1` | Reading; `F-15` | Override rows "cannot establish packaged selection" limits what a row establishes, not whether the override runs, and the text does not let a reader tell which. | Text | **Rewrite**: tie the statement to the named fields and say plainly that it concerns what the row shows. | Awaiting maintainer |
| R-13 | `K-194-1`, `K-194-2` | Reading; `F-18` | Runtime inspection failure cancelling activation while keeping earlier observations is a behavior of its own, placed as a qualification to the entitlement fields. | Text, and placement | **Rewrite**: give it its own statement with actor, boundary and consequence. No signed-product check reaches it (`F-18`); recorded for the maintainer. | Awaiting maintainer |
| R-14 | `K-198-1` to `K-202-1` | Reading; maintainer's comment of 2026-11-10 on this row; `F-07`; `F-15`; `A-24` | The passage gives an exception to a rule it never states. The rule, positively: the actions declared in the phases correspond exactly to the step records and extension-event records, with uniqueness and ordering requirements. Stated that way it also separates having a record for an action from having evidence that the action ran. "Observation arrays are empty" is neither specific nor safe: a preparation-failure reply holds a mixture of declarations, evidence of the failure, and empty execution records, and the phrase does not let a reader tell them apart. "Sole exception" is inaccurate: a reporting-failure reply is not held to the partition either, and the two cases mean different things. After a preparation failure a declared plan has no execution records because nothing launched; after a reporting failure records may remain whose consistency was not established. | Text. Repository: three hand-written validators with different conditions. At the initial review, divergence in final judgments was not established. The subsequent comparison and experiment are recorded under R-36: the skip condition changes diagnostics, while other differences change judgments. The coordinator's earlier wording, that they "skip the rule under different conditions", claimed more than was known: the controller and the host's self-check flag an invalid preparation-failure record separately, so that difference may change only which diagnostic appears. The Python reader's lack of explicit checks on host regions, custody and phase arrival and completion is the more concrete difference. | **Rewrite**, proposed: state the partition rule positively where replies are explained; describe a preparation-failure reply by its three categories of record; state both cases in which the rule is not applied, with what each means. **Evidence now available:** the source comparison and candidate experiment are complete under R-36. Definitions and applicability still need to settle the intended common rules. | Comparison complete; wording and intended rules open with R-36 |
| R-15 | `K-204-1` to `K-210-*` | Reading; `L-27`; `F-18` | The application states are given through exclusions without positive meanings, and "closed state/basis pairs" restricts a set the reader is never shown. | Text. Repository: the list behind `not_attempted` is hand-copied in three languages. | **Rewrite**: define the four states positively, then the exclusions; give the pairs or say where they are. **Maintainer:** whether the pair set belongs in the contract, and whether three hand-written copies are necessary. | Awaiting maintainer |
| R-16 | `K-212-1` to `K-228-*` | Reading; `L-28`; answer 3 | The purpose of the termination dependency is implicit: the gate decides whether the dependent phase may activate, collect queries and release attempts, so "a satisfied gate additionally requires" reads as record consistency only. | Text | **Rewrite**: open with the decision the gate governs. | Awaiting maintainer |
| R-17 | `K-215-1` | Reading; `F-15`; `A-26`; answer 3 | "These ordinals are local to the source actor process" is too broad after the sentence on phase activation, and hides that the host keeps the counters. | Text | **Rewrite**: the host keeps one observation sequence per actor; an actor's activations, its reap and the gates that refer to it use that sequence; a dependent actor's activation uses its own. | Awaiting maintainer |
| R-18 | `K-230-*` to `K-236-*` | Reading; `L-29` | "Native facts may retain absent source timestamps" and the sentences after it present three consequences of failures at different moments as qualifications to "native facts". | Text | **Rewrite** in order of occurrence: missing source timestamps; a clock failure after the dependent activation is stored; a cleanup reap after a failed gate. | Awaiting maintainer |
| R-19 | `K-351-*` to `K-355-*`, and every "requires" in C:168-238 | Reading; `F-07`; silence 5; answer 7 | The rule that governs the equipment region's requirements is 115 lines later, under the transport heading. "Unsupported or malformed input cannot become a semantic claim" covers four different consequences: bytes and diagnostics kept when decoding fails; a decoded record kept when admission fails; observations kept with integrity issues when later checks find contradictions; and a host reporting failure handled on its own path. | Text, and placement | **Rewrite**: state the four cases by boundary and consequence, and put the publication rule where the requirements are read. Throughout, name the speaker: the host reports, the record carries, the controller checks, the consumer may conclude. | Awaiting maintainer |
| R-20 | `K-165-2`, `K-352-*` | Reading; `F-07`; coordinator's source reading above | `result.ok` and the exit code follow the host's `finished` outcome and nothing else. A consumer can see success, a host field asserting something, and a controller finding that withholds it, in one envelope. A default test asserts that combination. | Repository, and text that does not say so | **Which side is right**, for the maintainer: state the combination plainly and keep the behavior, or make success reflect the controller's findings. | Awaiting maintainer |

### C:3-56, C:100-106 and C:430-434, identity, stamps and shape goldens

Opened by the maintainer's close reading of 2026-11-10, kept verbatim in
`records/contract/CONTRACT-MAINTAINER-NOTES.md`. Three removals are the
maintainer's stated direction and are marked so. Every other disposition is
the coordinator's proposal.

**The reader's task these passages serve**, in the maintainer's words: to
let a developer establish which contract applies and find what that
contract commits to. The rows below are read against that.

**Direction for stage 5, stated in this reading.** `CONTRACT` is to be
generated and to remain the public account a developer engages with.
Generation changes where authors edit it and need not reduce the authority
or completeness of what readers receive. The manifest can own surface
membership and references as authoring inputs; their substance is rendered
so the document tells the developer what each surface contains. Reading
JSON is not to be a prerequisite for discovering what the document covers.

**Added by the maintainer's position on `R-36`, 2026-11-10.** The contract's
shape has three parts with a purpose each: named definitions establish what
the records mean; explicit applicability establishes which rules govern
ordinary, preparation-failure and reporting-failure replies; obligations
establish what each component checks and what it does on failure.

**Run by the coordinator on 2026-11-10**, in a scratch clone of `ec88e53f`
made with no tags, since deleted. Grade: run.

| Command | Result |
| --- | --- |
| `generate_contract_stamps.py --check` | Prints "ok: contract inputs current; stamp derivation not checked (release history unavailable)". Exit 0. |
| `--check --require-history` | Refuses. Exit 1. |
| Regeneration with no option | Refuses: "restore annotated release tags before regenerating stamps". Exit 1. |
| Regeneration with `--release v9.9.9` | Prints "ok: contract surface stamps current", exit 0, and rewrites both tables, replacing every `v0.3.6` stamp with `v9.9.9`. |

The last line contradicts C:54-55, "Regeneration refuses to erase existing
release stamps without history": the refusal is skipped whenever `--release`
is given. Release preflight separately requires history; that was not run.

**Read first-hand by the coordinator.** The build runs the plain `--check`
(`build.sh`). The two tables are the ones in `docs/CONTRACT.md` and
`docs/PolicyWitness.md` (`generate_contract_stamps.py`, `OUTPUTS`). A shape
difference raises an assertion failure after the candidate is written, so
the case fails (`tests/suites/runner_unit/porcelain_replies.py`,
`replay_shapes_and_sizes`). A surface's hash covers its region text and
goldens and nothing about behavior (`surface_hash`).

| Row | Claims | References | Strain | Sits in | Disposition | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-21 | `K-3-1` | Reading; `F-10`; `A-01` | "The public contract is the release" is definitive before either term is explained. Development builds have contracts too, and an identity names a contract without stating what it commits to. | Text | **Rewrite**, proposed: open with what the contract governs and how a specimen or a received artifact identifies it. | Awaiting maintainer |
| R-22 | `K-3-2`, `K-4-*`, `K-5-1` | Reading; `F-10`; `A-D02`; `R-04` | "Assert `contract`" and "names its producer" are different relationships put side by side. "Producer" suggests a process identity or an authenticated origin; the value compared is the reported build contract. "Admission is exact" does not say which values are compared. | Text | **Rewrite**, proposed: the specimen names the contract it requests; a received artifact reports the contract of the build that produced it; state the two values compared at each admission. | Awaiting maintainer |
| R-23 | `K-5-2` to `K-6-*` | Reading; `F-09`; `F-12`; `A-D15`; answer 15 | "There is no negotiation, implicit acceptance, historical translation or bypass." | Text | **Rewrite: remove.** Maintainer's direction. The positive rule states that a matching assertion is required and what a mismatch does; historical evidence handling is described where it happens. | Direction given; not yet changed |
| R-24 | `K-8-*` to `K-15-*` | Reading; `F-11`; `A-D03` | Forms of identity, their derivation and where they are reported are combined, and where the identity is reported comes after suffixes, index flags and incidental files. | Text, and placement | **Rewrite**, proposed: first the forms and where a person holding an application reads its identity; derivation separately, as what a builder needs. | Awaiting maintainer |
| R-25 | `K-17-1` to `K-19-*` | Reading; `F-03`; `F-01`; answers 5 and 12 | "Revisit the corresponding definitions" has no dependable destination. Changing the assertion is presented as the step, when it follows a decision the review may go against. The procedure has no baseline for a specimen asserting a development identity. | Text, and structure | **Rewrite**, proposed, once stage 5 settles where definitions are reached from: the review decides whether the selected contract suits the specimen; changing the string supplies the admission condition only. | Awaiting maintainer |
| R-26 | `K-24-1` | Reading; `F-01`; `F-04` | "The manifest defines the scope" delegates before saying which scope: the public commitments, each surface's membership, or the inputs whose change moves a stamp. | Text, and structure | **Structure**, per the direction above: the document renders what each surface contains; the manifest is an authoring input. | Stage 5 |
| R-27 | `K-25-1`, `K-26-1` | Reading | The sentences on transport and installation goldens name maintenance artifacts and what they contain, not the requirements a reader needs. | Text, and structure | **Rewrite**, proposed: give the definitions and their reach; move the account of the artifacts to where maintenance is described. | Awaiting maintainer |
| R-28 | `K-29-1` to `K-32-1`, the table | Reading; `F-03`; silence 2; answer 5 | "Last changed" has no precise object. The machinery records changes to the definition text and golden inputs and does not discover implementation changes, so the table depends on a maintenance responsibility the text does not state. | Text | **Rewrite**, proposed: say what the column records and state the responsibility plainly. | Awaiting maintainer |
| R-29 | `K-52-1` to `K-56-1` | Reading; `L-07`; `F-12`; the run above | Without history `--check` exits 0 on a narrower result, and "explicitly reports" is left to carry the difference. "The two tables" are not identified. Preserving stamps is not verifying them. And the stated protection does not hold when `--release` is given. | Text, and repository | **Rewrite**, proposed: state the exit status and the narrower result, name the tables, separate preservation from verification. **Maintainer:** what an ordinary build from a source copy requires of this check; and whether regeneration with `--release` and no history should refuse. | Awaiting maintainer |
| R-30 | `K-100-*` to `K-106-*` | Reading; `F-13`; `F-12`; `A-10` | "Review and assert" joins a human judgment to an enforced comparison. The next sentence turns to maintainers, and its "so" carries the dependency of the table on their upkeep. | Text | **Rewrite**, proposed: separate what the application establishes from what the review must; state the maintenance dependency as one. **Remove** "There is no separate request counter or compatibility exception for optional additions": maintainer's direction. | Partly direction given; not yet changed |
| R-31 | `K-430-1` to `K-433-2` | Reading; `L-48`; the source read above | Shape goldens record keys and JSON types; the text does not keep that apart from values, relationships and behavior. It omits that a difference fails the check. "Update the golden" assumes the review's outcome. "Still fail semantic admission" names a mechanism without identifying it. | Text | **Rewrite**, proposed: a shape difference fails a check and writes a candidate; the review decides which side is corrected; required fields are enforced by readers and decoders, separately. **Remove** "There is no separate version-bump classifier": maintainer's direction. | Partly direction given; not yet changed |
| R-32 | All of the above | Reading | The passages attend to maintaining contract artifacts and leave the reader's route, from the identity they observe to the commitments they act under, implicit. | Structure | **Stage 5**: the route is the organizing requirement for the opening of the rewritten document. | Stage 5 |

### The guide's account of a result

Opened by the maintainer's note of 2026-11-10 on `R-20`, kept in
`records/contract/CONTRACT-MAINTAINER-NOTES.md`.

| Row | Claims | References | Strain | Sits in | Disposition | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-33 | The guide's `envelope` and `refusals` regions, G:1207-1294 and G:2017-2109 | Maintainer's note; `R-20`; `R-07`; `R-19`; `F-07` | The guide explains one ordinary result in five places about 730 lines apart. It has no sentence saying which component supplies `data.runner_result`, `data.runner_sandbox_diagnostics` and `result`, though the controller README does. The definition tying `finished` to `result.ok` and exit 0 is far from the sentence saying the controller's findings do not change the outcome. | Text of the guide, and its placement | **Rewrite**: one contiguous account under the output-envelope introduction, with the outcome catalog adjacent, consolidating the existing passages and not adding a summary beside them. Maintainer's direction. Drafted in `records/contract/GUIDE-RESULT-ACCOUNT-DRAFT.md`; the guide is unchanged. `R-20` stays open: the draft describes the present behavior and marks the sentences that depend on it. | Draft awaiting maintainer's review |

### Withholding, as implemented

For `R-07`, `R-34` and `R-35`. Source read by the coordinator on 2026-11-10
(`controller/src/porcelain_admission.rs`, `project` and
`execution_diagnostics`; `runner/Sources/PWRunnerCore/CWorkerDisposition.swift`
for the host's states). Nothing run for this section; the test named below
passed in run `tests/out/runs/contract-c243`.

**Is `unconfirmed` another judgment or a rename?** A rename that also merges.
The host's `final_status` claim has one of four states. For a worker's
record that passed the controller's validation, the controller's
`process_disposition` is chosen from that state alone:

| Host's `final_status` claim | Controller's `process_disposition` |
| --- | --- |
| `supported`, answer `exit_code`, value 0 | `clean_exit` |
| `supported`, answer `exit_code`, other value | `nonzero_exit` |
| `supported`, answer `signal` | `signaled` |
| `conflicting` | `conflicting` |
| `unresolved` | `unconfirmed` |
| `inapplicable` | `unconfirmed` |
| anything else | `unrecognized` |

Three further values do not come from the host's claim: `withheld`, when
the controller's own validation of the record finds an issue; `no_worker`;
and `per_actor`, the top-level value in the actor form.

**What "withheld" covers.** Only the controller's own disposition fields,
at the level where the finding was made.

- A finding inside one worker's disposition record withholds that worker's
  `process_disposition`. In the actor form each actor is projected
  separately, from its own record and its own actions; the top-level
  `disposition_integrity` is `valid` only if every actor's is.
- A finding by the reply-level validators sets the top-level
  `process_disposition` to `withheld`. The per-actor entries are not
  changed by it. A default test,
  `typed_invalid_actor_account_keeps_independent_actor_endings`, asserts a
  top-level `withheld` with an `actor_evidence` issue beside an actor still
  projected as `clean_exit`.
- Nothing in the host's report is withheld or altered by the controller:
  not the host's claims, not a step's `comparison`, not the outcome.
  `result.ok` is unaffected (`R-20`).

There is no record of which conclusion depends on which observation. The
overall `withheld` does not govern the assessments beneath it.

| Row | Claims | References | Strain | Sits in | Disposition | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-34 | `K-165-2`, `K-352-*` to `K-355-*` | Maintainer's comment on `R-07`; the section above; `R-19`; `R-20` | "Dependent claims" promises that a missing or contradictory observation prevents the conclusions that require it. What is implemented is narrower and differently shaped: the controller withholds its own disposition at the level of the finding, leaves assessments beneath that level standing, and leaves the host's claims visible. A consumer cannot tell from the text which conclusions a finding invalidates, which stay independently supported, or whether a top-level `withheld` governs the per-actor ones. It does not. | Text. Repository for the question of intent. | **Rewrite**, proposed: say exactly which fields are withheld, at which level, by which kind of finding, and what stays. **Which side is right**, for the maintainer: whether a reply-level finding beside a standing per-actor `clean_exit` is the intended meaning of "dependent". The test's name suggests it is deliberate. | Awaiting maintainer |
| R-35 | Guide G:1276-1277; `K-165-2` | Coordinator, while reading for `R-07` | `process_disposition` can be `per_actor`. The guide's list of its values omits it, and so does the contract. Only the controller README mentions it. The coordinator's guide draft copied the incomplete list. | Text of the guide | **Rewrite**, proposed: add the value where the field's vocabulary is given, with the actor form's per-actor entries. The draft is corrected to say so. | Awaiting maintainer |

### R-14: where the three validators' judgments diverge

Established by a read-only comparison and then a run, both delegated, on
2026-11-10. Deposited as `records/contract/validators/COMPARISON.md`,
`RUN.md` and `RUN.patch`. The coordinator has read the run's method, its
table and its list of divergences, not all of its per-reply sections.

**Grade.** Run, as an experiment: in a disposable worktree at `35226316`
(product source as at `a7d9b320`), with temporary test code only. Each reply
was built once as a typed Swift record, which S judged; it was then encoded
to the binary reply format and decoded by the Rust reader, and R judged the
decoded record and P its JSON presentation. These were direct invocations, not runs of the catalog
cases, and establish nothing about the battery. The worktree has been
removed; the patch reproduces the test code.

**Readers.** S is the host's self-check (`validateForReporting`). R is the
controller (`execution_diagnostics`). P is the test harness's reader
(`consumer.validate_fixture`).

**Controls.** The three valid preparation-failure replies the Swift tests
construct were accepted by all three readers.

**From the reading.** The three implement the same partition rule. Of 41
conditions on a preparation-failure reply, 29 are applied by all three, 9
by two, 1 by one and 2 by none.

**Observed.** Each row is a valid preparation-failure reply with one
change, unless it says otherwise. Every clean observation matched the
comparison's prediction.

| Change | S | R | P |
| --- | --- | --- | --- |
| A well-formed host region row (D1) | objects | objects | **accepts** |
| A phase marked as arrived (D2) | objects | objects | **accepts** |
| An ordinary reply with a `preparation_failure` added (D11) | objects | objects | **accepts** |
| A phase given an ordering record with proceed set (D3) | **accepts** | objects | objects |
| A declared action identity that is empty or over the bound (D4) | **accepts** | objects | objects |
| `extension_events` absent (D5) | **accepts** | objects | objects |
| A phase's `actor_visit` wrong (D7) | **accepts** | objects | objects |
| An actor's `visits` empty (D8) | **accepts** | objects | objects |
| An actor's `index` not its position (D10) | **accepts** | objects | objects |
| An actor's `visits` with one extra entry (D9) | **accepts** | objects | **accepts** |
| A `phase_id` that is empty or over the bound (D6) | **accepts** | **accepts** | objects |
| A degraded reply with an actor-table defect (D12) | **accepts** | **accepts** | objects |
| JSON `"preparation_failure": null` on a valid actor reply (D13) | not asked | **accepts** | objects |

What the run settles:

- **Skipping the partition on presence or on validity changes the
  diagnostic only.** No reply was found on which that difference alone
  changes a final judgment, as the maintainer expected.
- **Final judgments do diverge**, in every direction. Twelve candidates
  were compared across all three readers and the judgments differed on
  each. The thirteenth, a JSON null, could not be put to S and differed
  between R and P. This shows that the three definitions of validity
  differ; it does not show how often production emits such replies.
  The directions: the harness reader accepts replies both product readers
  object to; the host's self-check accepts replies the controller and the
  harness reader object to; the controller alone objects to one; the
  harness reader alone objects to three.
- **The Python reader does not check host region rows or phase arrival** on
  a preparation-failure reply, confirming the maintainer's point. Its
  missing custody and completion checks are covered indirectly.
- **Every objection by the controller was a flag, not a refusal.** For all
  101 replies run, admission passed and `data.runner_result` would be
  published; the objection appeared as an `actor_evidence` issue.
- D6 to D10 do not depend on preparation failure. The same changes to any
  actor-form reply would read the same way. The general checks were not
  compared exhaustively, so these are examples, not a census.

Not observed: S could not be asked about a JSON null. The degraded reply
for D12 was built in test code, not by the host's own path.

Incidental: two unmodified Swift shape fixtures, which are built for shape
coverage, were accepted by S and objected to by P, and one of them by R.
Recorded here and not pursued.

| Row | Claims | References | Strain | Sits in | Disposition | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-36 | `K-198-1` to `K-202-1`; the general actor-table checks | `R-14`; the run above; maintainer's position of 2026-11-10 | Three hand-written validators reach different final judgments on the same reply, in every direction. The three roles are legitimate and may respond differently to a violation. The strain is that each defines validity on its own authority: where they assess the same requirement over equivalent information, a difference needs a reason grounded in the contract, and the contract supplies none. | Repository, and text that does not define the records | **Maintainer's position:** keep the finding; do not settle the architecture by counting validators; make the disputed meanings and scopes explicit before choosing which implementation to change. Not thirteen separate rulings: a definition should settle a family of cases and establish a public rule whose reach determines each reader's obligations. The reporting-failure reply is the most consequential: what it promises, which requirements still apply, and what a consumer may conclude from retained records. Generating the three from one implementation is set aside. A common corpus would test stated commitments across implementations, after the definitions. Drafted for review: `records/contract/validators/DEFINITIONS-AND-SCOPES.md`, with six definitions, an applicability table and the present obligations. | Draft awaiting maintainer's review |

### Two commitments found while working the termination gate

Source read by the coordinator on 2026-11-10
(`runner/Sources/PWRunnerCore/ActorScheduler.swift`, the schedule walk and
the gate evaluation; `controller/src/porcelain_admission.rs`, the issue
record). Nothing run.

| Row | Claims | References | Strain | Sits in | For the maintainer | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-37 | `K-234-*` to `K-236-*` | `records/contract/CONTRACT-STRUCTURE-PROPOSAL.md`, the gate example; `R-16`; `R-18` | When an evaluated gate fails, the host withholds the dependent phase and skips every later phase, whichever actor owns it. A gate left `not_reached` by an unavailable actor is not itself a failed evaluation that cancels the rest. C:234-236 does not state the global cancellation scope. | Text that understates, and the repository for whether this reach is intended | **The distinction:** stopping the dependent phase, against ending the run's remaining schedule. **Why it matters:** it decides which later observations a specimen can still produce after a dependency fails. **The commitment at stake:** retain and state global cancellation, or define which later phases remain eligible and change the scheduler accordingly. | Awaiting maintainer |
| R-38 | `K-352-*` to `K-355-*`; controller gate findings | The gate example; `R-20`; `R-34`; `R-36`; `porcelain_actor.rs::require`; `porcelain_admission.rs::IntegrityIssue` | Gate checks emit `actor_evidence` issues containing a kind and detail sentence without a structured phase or actor reference. The host's gate remains published unchanged. Other lifecycle issues can carry rule, question, step index and observation fields, so the absence of context is not universal. | Repository: the subject of a gate finding. Text that promises withholding of "dependent claims". | **The distinction:** an overall integrity finding, against one identifying the assertion and its dependencies. **Why it matters:** the gate finding has no machine-readable association to the affected gate. **The commitment at stake:** whether findings should identify their subjects, together with a defined scope for the conclusions affected. A subject reference alone would not settle which other conclusions remain supported. | Awaiting maintainer |


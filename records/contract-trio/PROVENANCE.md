# Contract trio passes: provenance and validation status

This note covers the three contract investigations of 2026-11-16.
It records who wrote and validated each report, the validation
status, what remains unresolved, and where the evidence is. It does not
summarize the findings. The reports themselves are in
`records/DOCUMENTATION-TRACE-REVIEW.md`, appended intact.

## Common facts

- Source snapshot: `main` at `cc55288d033023ce2f18e8c02cd51a400ef2b530`, clean.
  The tree stayed clean apart from the review record and this directory.
- App: `dist/PolicyWitness.app`, built from `8b5de2b2` (build 1482, contract
  `development:bdefcb44…fb18`). Product sources are unchanged from that commit
  to HEAD. The app was not rebuilt, re-signed or modified.
- Roles:
  - Manager: Claude Opus 5.5, in the main session.
  - Investigators: one Opus subagent per pass, told not to delegate.
  - Validators: one Sonnet subagent per pass, told not to rewrite the report.
  - Investigation, validation and revision ran in sequence within each pass.
    The passes ran concurrently in the main checkout. No worktree was used.
- Each investigator received its pass's plan text verbatim, with logistics
  added before and after it.
- No registered test case was executed in any pass. Acceptance ran
  `tests/run.sh --all --list` only. `tests/out/runs/` is empty.

## Reports in the record

| Pass | Record heading | Identifiers | `final.md` SHA-256 |
| --- | --- | --- | --- |
| Transport failure and helper fallback | `## Additional findings: transport failure and helper fallback` | DT-113 to DT-119 | `981695f3046618fc0c45a8227e0b9eb5791e6daf43630217e4c338df773e6050` |
| Observation ownership and time | `## Additional findings: observation ownership and time` | DT-120 to DT-129 | `3d53059cb0af1917dec1427a4e71e51428b36b9012b436c169147deaf90163f6` |
| What acceptance establishes | `## Additional findings: what acceptance establishes` | DT-130 to DT-135 | `dbbd838789f008d65135f33b937a2f9da6efed552f85d6e658f95847ccedcce3` |

How the reports were appended:
- In the order the passes finalized.
- The manager added only the `##` heading lines.
- Each `final.md` was copied with `cat`. The appended bytes were compared with
  the file using `cmp`, and every comparison was equal.
- The diff of `records/DOCUMENTATION-TRACE-REVIEW.md` contains only insertions.
- All 102 relative links in the appended text resolve to existing paths.
  Anchors were not checked.

## Files per pass

Each of `transport/`, `observation-time/` and `acceptance/` retains the
validation memos and author responses. The full set listed below, including
the two drafts and the separate final for each pass, is in commit `263c06c8`.
For example, use `git show 263c06c8:records/contract-trio/transport/final.md`
to recover the exact bytes for the transport hash above.

- `draft-1.md`: the first authored draft.
- `validation-1.md`: the validator's first memo, on draft-1.
- `response-1.md`: the author's disposition of each validation-1 concern and
  each manager question.
- `draft-2.md`: the revised draft.
- `validation-2.md`: the targeted revalidation of draft-2.
- `response-2.md`: the author's disposition of the validation-2 caveats.
- `final.md`: the author-approved text that was appended.

Observation-time has one more file:
- `validation-3.md`: a check of the correction made in its `final.md` after
  validation-2.

## Validation status

**Transport (DT-113 to DT-119).**
- Validation-1: five concerns.
  - One wrong citation.
  - One native run credited to the wrong row.
  - Aftermath observations that were not saved.
  - A precedence ordering between mutually exclusive steps.
  - One evidence-class wording.
- The author corrected all five.
- While re-checking, the author withdrew one claim, that no `pw-probe-runner`
  process existed after d2. The check pattern could not match a worker.
- Validation-2 found every concern resolved, with no new overstatement. It
  left one caveat: an unlabelled "only native route" sentence. The author
  qualified it in `final.md`.
- After validation-2, `final.md` also gained a table of controlled cases and a
  note on citation shorthand. The validator did not re-check these. The
  manager checked the table against `b/summary.json`, case by case.

**Observation-time (DT-120 to DT-129).**
- Validation-1: eight concerns. Three were incorrect statements:
  - the store-time copy of the stop reason in the actor form;
  - equipment binding in an in-process test;
  - the assignment sites of `sentinel_deadline`.

  The other five covered one overstatement about the driver baseline, two scope
  points and two caveats.
- The author corrected or qualified all eight.
- Two small CLI runs followed. They related token length to the target path
  length, which resolves the 208 versus 216 difference from DT-62.
- Validation-2 found every concern resolved, with two caveats. The author
  qualified one. While checking the other, the author found that "every other
  live actor is parked" was wrong for an actor past its final visit, and
  corrected it.
- Validation-3 confirmed both caveats were resolved. It recorded one limit:
  the full effect of `_exit` on the exiting actor's shared mappings was not
  read.
- `final.md` reorganizes draft-2 into numbered entries. That was the author's
  choice.

**Acceptance (DT-130 to DT-135).**
- Validation-1 recomputed all 25 seam rows and found them matching. It raised
  seven concerns:
  - three overstatements of the form "every reader" or "no reader";
  - an imprecise statement of the scheduler gate;
  - a count wording;
  - an unstated negative search;
  - a misattached cross-reference.
- The author corrected or qualified all seven. The author traced the gate
  expression and restated the gate finding (now DT-133). The ownership
  paragraph was reread more weakly, as stating a procedure with no equality
  relation (now DT-135).
- Validation-2 supported the gate trace and found two minor items. One was
  inconsistent use of the weaker reading; the other, one case counted as
  running the consumer when it does not. The author corrected both in
  `final.md`.
- After validation-2, `final.md` also gained three things the validator did
  not re-check:
  - a trace of the untraced regions branch;
  - a cross-reference to DT-120;
  - clarifications.

  The manager checked the regions claim against `AuthorityCustody.swift`
  359–362 and checked the DT-120 citation.

**Disputes.** No author disputed a validator concern, so no consequential
dispute remained for a further round.

## Unresolved

These are the limits the validators recorded. Each report's own coverage
section states its own limits.

- **Transport.**
  - Two post-run process checks were seen at the terminal and not saved: the
    check at 14:48:43 after the host kill, and the d2 PID check.
  - The NSXPC zero-length reply was inferred, not exercised.
  - The Cargo build, the controlled harness and the host-kill run were not
    re-executed by the validator.
- **Observation-time.**
  - Use of the checkout lock for live runs is recorded only in the author's
    command history.
  - The claim that the active actor is parked rests on the scheduler's design
    and comment, not on a traced path for each actor.
  - The `_exit` mapping effect was not read.
  - The actor timeout variants and a worker custody timeout were not executed.
- **Acceptance.**
  - No Swift reader was run on an edited frame. Every Swift judgment about
    those frames is source reading.
  - Every seam row carries a constructed `producer.contract` rebinding.
  - The reader-to-case map is a static text search.
  - Of the 30 consumer-only cases, the live status of 24 was not individually
    confirmed.

The manager found no direct contradiction between the three reports. Where
they overlap, each author's text is left as written. For example, DT-119 and
DT-134 both say that admission refusal follows only from geometry and from
compiled-profile labels.

## Evidence locations

All of these are local, gitignored or temporary, and have no retention
guarantee.
- `.tmp/contract-trio/transport/`: helper probes, shipped-controller runs,
  native captures `r1` and `r2`, controlled cases (`b/`), the host-kill run
  and `kill_log.json` (`c/`), tools, and an isolated Cargo build.
- `.tmp/contract-trio/observation-time/`: specimens, CLI captures (`runs/`),
  and the copied Swift package and driver.
- `/private/tmp/pw-trio-ot-xVGRMW/target`: the observation-time target file.
  It does not survive a reboot.
- `.tmp/contract-trio/acceptance/`: scripts, live captures, the frame corpus
  with `edits.json`, seam outputs `rust.json` and `python.json`, the reader
  map, and an isolated Cargo build.

## Process notes

**Reformatted write content.**
- Content that subagents passed to the Write tool sometimes reached disk in a
  restructured form; first noticed in observation-time's draft-1.
- No hook is configured in the project, the user settings or the installed
  plugins. The session transcript recorded the restructured content as the
  Write input.
- Every author therefore read back each draft and its `final.md` from disk,
  corrected any passage whose meaning had changed, and approved the on-disk
  text. Appends were byte copies of those approved files.

**Evidence relayed between passes.** The manager relayed three items. Each was
marked provisional, and the receiving author checked it before using it.
1. To acceptance, from observation-time: an in-process test computes its
   expected trigger with the production map, and claims are compared only
   with their own raw fields.
2. To transport, from acceptance: result selection ignores integrity issues.
3. To transport, from acceptance: the host's reporting fallback ends with
   empty bytes.

**Fault injection.**
- Transport sent one SIGKILL, to a single PWRunner host (PID 71748). It was
  identified by its parent and child chain, its start time and its
  `launchctl` per-client domain.
- The orphaned worker and its children exited on their own. No other process
  was signalled.

**Not done.**
- Nothing was committed.
- The plan file was not changed.

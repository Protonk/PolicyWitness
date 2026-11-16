# Response 1: dispositions for validation-1 and the coordinator's questions

Author: observation-time investigator. Revised report: `draft-2.md`. `draft-1.md`
is unchanged. I checked each item myself against source, history or the saved
captures. One new pair of public CLI runs (C7a/C7b, path-length checks) was made;
nothing else was executed.

## Validator concerns

- **C1 (OT-6, actor-form store-time copy): corrected.** The validator is right.
  `stopActor` writes `records[index].stopReason = reason` at
  `ActorScheduler.swift` 548, before `pollStopReason` and `requestExit`. The field
  is read only by tests (`ActorSchedulerTests.swift` 572 and 607), never by
  production code or the reply. `finish()` does not set it. OT-6 now says both forms
  keep a copy made before the store and only the single-worker copy is published.
- **C2 (OT-8, `checkedActorSchedule`): corrected.** `ActorReplyTests.swift`
  27–35 runs the production `ActorEquipmentPreparation.bind` and installs a
  `didSetUp` live inspection. The issue-interrupted test also runs
  `admittedReplyData` (`ReplyFailureTests.swift` 110–113: `validateForReporting`
  plus encoding). OT-8 now says it skips the XPC service entry, `runActors` and
  validator collection, and sets the seam on actor 0 only. On the E6 limit the
  validator could not check: the driver's `ActorScheduleInput` (driver
  `main.swift` line 40) sets no `didSetUp`, so binding and inspection do not run
  there. Draft-2 cites the driver lines.
- **C3 (mapping-change detection; wording sites): qualified.** "That fixture alone"
  now applies to `DispositionResolverTests.swift` 44. Line 527 is added: it
  compares the Python export with the Swift map, which detects disagreement
  between the two tables but checks no reply value. The validator's third wording
  site is added (`lifecycle_contract.py` 105–106, from `0b6e191e`). I also found a
  fourth: the doc comment on `CWorkerOutput.cleanupTrigger` (`CWorker.swift`
  559–562, from `0ed4ae7a`). The central point is unchanged.
- **C4 (`sentinel_deadline` assignment): corrected.** The sentence now cites both
  initializer assignments (`ActorSession.swift` 70 and 411). The inference is
  unchanged: both precede the loop.
- **C5 (OT-2 search scope): qualified.** Draft-2 states the first search's scope
  and adds the later search of `tests/suites` and `tests/fixtures`. That search
  found the raw C word in `authority_binding.c` 99/104 (a constructed control that
  drives the worker to `PW_CUSTODY_TIMEOUT`), in the `early_erase` mutation anchor
  (`actor_handoff_mutations.py` 140–141) and in the layout printer. None of these
  reads the decoded Swift field. The "not executed" limit is narrowed to an
  end-to-end timeout case.
- **C6 (E6 V2 "only at teardown"; counterexample strength): corrected.** V2 is now
  bounded the way the capture bounds it: still uncleared (208) at B's phase-4
  hook, cleared and unmapped by the time `run()` returned. The interval includes
  B's last visit, B's exit and `finish()`, and source attributes the clearing to
  `custody.finish()`. "Counterexample" is replaced. V2 shows with real workers
  that the final flag cannot tell the two sites apart when the last-transfer site
  never ran. It is not a case where the line-468 assertion fails for the input
  that test runs.
- **C7 (216 vs 208; consume 0 vs 1): resolved and disclosed.**
  - Length. A targeted check ran E1a's specimen with target paths of 45 and 55
    bytes (C7a and C7b, public CLI, under the lock). They gave `token_length` 216
    and 226. E1a's 37-byte path gives 208. In all three the length is 171 plus the
    path's byte length. DT-62's path `/private/tmp/pw-authority-trace-3QC3qQ/target`
    is 45 bytes, which accounts for its 216. This is a length correlation; no token
    content was inspected.
  - Consume return. E6's `consume_d1` returned 0 (B unapplied, selected worker),
    while E3's consumes returned 1 (B applied). DT-59 also recorded 0 for an
    unapplied actor. Both are candidate handles, and the last-use erase runs
    whatever the result (C 933–940). Draft-2 discloses this and makes no claim
    about handle numbering.
- **C8 (reader description): corrected.** The text now says the readers check that
  `released` and `performed` are backed by operation cells, and that the
  `performed` check does not constrain the value. OT-4 stands.
- **Vocabulary note: incorporated into OT-1.**
  - `cleanup_trigger` has no vocabulary block; its field statement lists six values
    while actor replies carry others as `supported` claims. DT-30 records this; it
    is not a new finding here.
  - OT-1 now says that both actor outcomes follow documented rules. The open
    `poll_stop_reason` vocabulary says an unfamiliar reason "gains no known timeout
    or cause meaning" (`32-lifecycle.surface.md` 64–70). The cause table and the
    recognized-stop rule each fall back for unrecognized values.
  - "No stated rationale" is narrowed. No statement says the actor scheduler's own
    routine reasons are meant to be "unfamiliar", or that the actor deadline row
    cannot be reached.

## Coordinator's questions

1. **Reformatting: acknowledged.** I read draft-2 back in full on disk after
   writing and corrected two passages whose meaning differed from what I intended:
   - the target-file sentence had become ambiguous across three targets;
   - the coverage note had to name the response file.
   I will do the same for `final.md`.
2. **`stop_reason: null` in E5: answered in OT-1.** It is a separate projection
   rule with the same root. The actor `stop_reason` projects only answers in the
   six-value recognized set (`41-diagnostics.surface.md` 803–806 definition,
   932–943 rule), so `schedule_complete` and E1b's `died_before_completion` project
   null, and E3's `done` projects `done`. The cause table is a different
   first-match rule ending in `unknown`. Both are documented. The undocumented part
   is that the actor producer's routine values fall outside both recognized sets.
3. **216 vs 208, and consume return: see C7.** The 8-byte difference matches the
   difference in path length, confirmed with two further path lengths.
4. **`worker_custody_status` vs `ext_custody_status`: same field.**
   `worker_custody_status` is the E6 driver's output label for
   `CWorkerExtensionPublication.custodyStatus`, the decoded `ext_custody_status`.
   Draft-2 uses `ext_custody_status` and explains the label once.
5. **"Which is correct": replaced with the basis.** Draft-2 cites three things:
   - `collectOutput` reads payloads only after the `completed` acquire
     (`ActorSession.swift` 645–655);
   - the `result_published` definition (`14-extensions.surface.md` 544);
   - the failure contract's `unresolved` row and its rule that an unpublished
     return stays unresolved even when a test intervention knows it returned
     (lines 315 and 317–319).
6. **"Host values true at reply time": made precise.** These values record the
   outcome of the host's own last call on each resource, made in `tearDown` or
   `finish` during `ActorScheduler.finish()`, before the outcome and assembly. PW
   makes no later call: the deinitializers return through the
   `tornDown`/`finished` guards (`AuthorityCustody.swift` 226, 312, 634).
   - `released` therefore stays accurate after the reply as far as PW is
     concerned.
   - `unresolved` records a failed call and leaves the resource with the host
     process. What happens to it when that process ends is outside the records.
   - `withheld_not_quiescent` says nothing about the object's later state.

## Disputes for revalidation

None. I accepted, corrected or qualified every validator concern. The coordinator
may want the following revalidated:

- the C7a/C7b length correlation (`runs/c7_len45` and `runs/c7_len55`);
- the revised OT-1 statement of what is documented;
- the E6 driver claims now tied to `main.swift` line numbers (40, 43–56, 88).

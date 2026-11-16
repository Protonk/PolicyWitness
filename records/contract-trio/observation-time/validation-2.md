# Validation memo 2: revision check of draft-2 (observation-time)

Validator: Sonnet 5.5, read-only. Compared `draft-2.md` with `draft-1.md` (full diff), `response-1.md`,
the saved captures under `.tmp/contract-trio/observation-time/runs/`, the driver source, and the cited source,
docs and tests. No build, no native run. `validation-1.md` is untouched.

## Concerns and caveats (2 supported with caveat, 0 incorrect, 0 overstated, 0 unsupported)

### V2-1. C7 length correlation (supported with caveat)
- Location: draft-2 "Rebuilt specimens", bullet "Token lengths depend on the target path".
- Checked: `runs/c7_len45` and `runs/c7_len55` (exit 0, empty stderr). Issue `token_length` and token record are
  216 and 226. Specimen JSON diffs against `e1a_issue_only` differ only in `target` and `specimen_id`. Path byte
  lengths computed from the specimens: 37 (E1a, 208), 45 (216), 55 (226). 171+37, 171+45 and 171+55 match. DT-62's
  path `/private/tmp/pw-authority-trace-3QC3qQ/target` is 45 bytes, so its 216 is accounted for.
- Finding: the numbers and the "length correlation only; no token content inspected" qualification are supported.
  The opening verb "depend" is slightly stronger than three points with a single changed input strictly show, but
  the same sentence limits the claim. The constant 171 is unexplained, which the draft does not claim. Not
  asserted: that the 216 in DT-62 came from the same mechanism beyond the matching length.
- Unresolved: I did not verify that the C7a/C7b runs went under the checkout lock (not recorded in the capture).

### V2-2. E6 hook description (supported with caveat)
- Location: E6 bullet "Each collection-hook row ... after the scheduler observed the active actor's arrival and
  before its release store (`ActorScheduler.swift` 405-415). Every other live actor is parked".
- Checked: `ActorScheduler.swift` 395-430: the collect call (411) follows the arrival/violation checks and
  `waitChild`, and precedes the visit's `releaseVisit` (429). The in-source comment says "live, parked-at-arrival
  actor". Driver `main.swift` 88-94 appends one row per hook call. V2's capture has no `a_last` hook, and A is
  reaped from phase 1 on, as stated.
- Finding: the claim for the active actor is supported. "Every other live actor is parked" rests on the scheduler's
  one-actor-at-a-time design and its comment; I did not trace each park path. Classification: supported with
  caveat (source-comment level for the other actors).

## Disposition of C1 to C8 and vocabulary note: change made, concern resolved

- C1 (OT-6): resolved. Draft-2 says both forms keep a pre-store copy and only the single-worker copy is published.
  The actor copy is `ActorSessionRecord.stopReason` (`ActorScheduler.swift` 59 and 548). Only
  `ActorSchedulerTests.swift` 572 and 607 read it. `finish()` does not set it (562). No new overstatement.
- C2 (OT-8): resolved. `ActorReplyTests.swift` 27-35 binds and inspects equipment. `admittedReplyData`
  (`ReplyFailureTests.swift` 110-113) runs `validateForReporting` and encoding. The skipped parts are now stated as
  XPC entry, `runActors` and validator collection. The kill seam is set on actor 0 only (`ActorReplyTests.swift` 117).
- C3: resolved. Line 527 is described as table-to-table agreement that checks no reply value. Line 44 is "that
  fixture alone". The lifecycle_contract.py comment and `CWorker.swift` 559-562 (verified text) are added as wording sites.
- C4: resolved. Both assignments (70, 411) are cited, and the inference is stated as "no loop exit replaced it".
- C5: resolved. The scope of the first search is stated and the later search and its three hits are added.
  `authority_binding.c` 99 and 104, `actor_handoff_mutations.py` 140-141 and the layout printer were confirmed
  earlier. The "not executed" limit is narrowed to end-to-end.
- C6: resolved. V2 is bounded at the phase-4 hook (208 nonzero in `issuer_killed.json`) and `run()` return. The
  "counterexample" wording is replaced by the relationship statement plus "not a case in which the line-468
  assertion would fail". No new overstatement.
- C7: resolved and disclosed (see V2-1). E6 consume 0 versus E3 consume 1 is disclosed. DT-59's recorded
  `consume returned/0` for an unapplied self-consumer was confirmed. C 933-940 erase runs for any result other than
  the guarded store, as stated.
- C8: resolved. Wording now covers `released` and `performed` backing, and that `performed` does not constrain the
  value (checked earlier in `actor_evidence.py` 100-114).
- Vocabulary note: incorporated, see item (b).

## Requested area checks

### (a) C7 length correlation: see V2-1. Supported, stated only as a correlation.

### (b) Narrowed OT-1 documentation claim: supported
- `41-diagnostics.surface.md` 801-807 define actor `stop_reason` as "supported stop reason from the recognized set
  ... Null when no supported recognized answer was projected". The recognized-stop rule is at 930-944 with a
  `test: True` fallback to null; the quoted phrases match. The cause table ends in "No eligible recognized cleanup
  cause" (unknown). `32-lifecycle.surface.md` 64-70: `vocabulary: "open"`, `listed: "illustrative"` and the
  quoted `unknown:` sentence match. DT-30 records the six-value listing and a retained `cleanup_trigger:
  "schedule_complete"` envelope, so the draft's "DT-30 recorded that difference" is accurate. The E5 and E1b nulls
  (`stop_reason` null for `schedule_complete` and `died_before_completion`, `done` for E3) match the captures.
- The narrowed "No stated rationale" claim is limited to two things the draft says it did not find (routine
  scheduler reasons classified as unfamiliar; deadline row unreachable). I did not find either statement in
  `docs/contract` (grep for `schedule_complete` returned nothing). Retitling to "following the documented
  recognized-value rules" is supported for `poll_stop_reason` and the two projections. For `cleanup_trigger` the
  support is the cause-table fallback, since it has no vocabulary block, as the draft states.

### (c) E6 driver claims tied to `main.swift`: supported
- SHA-256 prefix `7d88c93f364e` matches.
- Line 40: `ActorScheduleInput(actors:applies:schedule:authority:)` with no `didSetUp` (the field defaults to nil at
  `ActorScheduler.swift` 41). Equipment binding and live inspection therefore do not run, as stated.
- Lines 43-49 (`nonzero`) count nonzero bytes only; no byte is printed. Lines 51-56 reach the private `buffer`
  through `Mirror` with no access-control change. Line 88 is the collection-hook entry.
- Line 37: V2 sets `inputs[0].killBeforePublishSlot = 1` only (actor 0 is A), with a comment matching the report.
  Final snapshot reads flags and mapping only, as the "buffer unmapped" cells require.
- Not independently confirmable from source: that the built executable was this file (hash recorded by the author).

## Unresolved limits
- The checkout-lock use for C7a/C7b is not recorded in the saved captures.
- "Every other live actor is parked" is supported only at the design/comment level (V2-2).
- I did not re-verify the unchanged parts of draft-2 beyond those listed in `validation-1.md`.
- Native behavior behind the 171 constant, and handle numbering, remain unexplained and are not claimed.

Counts: 0 incorrect, 0 overstated, 0 unsupported, 0 scope-not-justified, 2 supported-with-caveat (V2-1, V2-2);
C1 to C8 and the vocabulary note all resolved.

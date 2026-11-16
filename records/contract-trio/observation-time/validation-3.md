# Validation memo 3: handling of the validation-2 caveats in final.md

Validator: Sonnet 5.5, read-only. `final.md` SHA-256 prefix `3d53059c` confirmed. Compared with `response-2.md`,
the saved captures under `.tmp/contract-trio/observation-time/runs/`, `pw_probe_runner.c`, `ActorScheduler.swift`
and the E6 outputs. Nothing was built or run. Only these two caveats were assessed.

## V2-1 (qualified): resolved
- Wording: `final.md` line 87 now reads "Token lengths varied with the target path's byte length in these runs".
  It keeps "length correlation only; no token content was inspected" and says "The constant is not explained here"
  (lines 93-96). The numbers are unchanged and still match the captures I checked in validation-2
  (208, 216, 226 for 37, 45, 55 byte paths; DT-62's path is 45 bytes).
- Lock statement: lines 60-63 give a single statement that all live runs (E1-E5, E7a/E7b, E6) used
  `tests/lib/checkout_lock.sh`, "recorded only in this pass's command history; the saved captures do not record it".
  That is accurate to what I found (the captures carry no lock record), and no other sentence in the file asserts the
  lock from a capture. I cannot confirm the command-history claim itself.
- Renaming: E7a/E7b is used in the evidence-kinds list, the artifacts bullet and the coverage list; the capture
  directories are named as `runs/c7_len45` and `runs/c7_len55`, and both exist. The only "C7"-style hits in
  `final.md` are in the checkout-name `c7_len*` directories, not a validation label. Line 29 says "made after the
  first validation", which is a process remark, not a finding label.
- Classification: resolved.

## V2-2 (corrected): resolved, with one caveat
- Source check of the correction: after the visits loop (`pw_probe_runner.c` 1659-1671), the worker runs
  `erase_accepted_token()` (1673), the optional hang and signal seams, then `publish_done_and_exit(hdr)` (1702). It
  does not park again. `wait_for_activation` (1148) is called only at the top of each visit (1662) and calls
  `service_inbound_once()` (confirmed inside the function), so "parked in `wait_for_activation`, which services
  inbound slots" before a later visit is supported. The statement in draft-2 was therefore wrong for an actor past
  its final visit, and the correction is right.
- E6 rows: V1 hooks show A's visits at phases 0 and 2 and B's at 1, 3, 4. So A is past its final visit at the
  phase-3 and phase-4 hooks, and B is parked before a later visit at phases 0 and 2, as the new bullets say.
  In V2, A died at its first visit and has no `a_last` hook, matching "reaped from phase 1 on". The scheduler
  one-actor-at-a-time basis is cited to `ActorScheduler.swift` 4-17 and 406-407, which match the header comment and
  the "parked-at-arrival actor" comment; the text correctly says this is design and comment, not a traced path.
- New claim, "A's exit path erases only A's own settled inbound slots (none) and touches neither host custody
  nor B's region": `erase_accepted_token` calls `erase_authority` (C 579-590), which iterates only the worker's own
  `authority->inbound_count` slots and erases those that are `settled`; A has no inbound slot (its cell 11 value is 0
  in E1a/E3). It does not reference host custody or any other actor's region. Supported for the measured quantities
  (host custody buffer, B's inbound slots).
- Caveat (unresolved, not an error): the claim covers `erase_accepted_token`. The same exit path also runs the seam
  branches and `publish_done_and_exit`, which stores `done` and calls `_exit`; neither touches the measured memory
  by source, but I did not read `_exit`-time effects on shared mappings beyond that. A's exit also changes A's own
  process state, which the hook rows do not measure. Classification: resolved, supported with that caveat.

## Counts by classification
- Resolved: 2 (V2-1, V2-2).
- New concerns: 0 incorrect, 0 overstated, 0 unsupported, 0 scope not justified.
- Supported with caveat: 1 (V2-2, exit-path coverage limited to the cited functions).

## Unresolved limits
- The command-history record of the lock use is not checkable by me.
- Restructuring and the renumbering to DT-120 through DT-129 were not assessed, per the instruction.

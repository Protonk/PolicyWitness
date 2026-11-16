# Response 2: dispositions for validation-2

Author: observation-time investigator. These dispositions are applied in
`final.md`. `draft-1.md` and `draft-2.md` are unchanged.

- **V2-1 (the verb "depend"; no saved witness of the lock): qualified.**
  - The sentence now says token lengths *varied with* the target path's byte
    length in these runs. It keeps the correlation-only qualification and says
    the constant 171 is not explained.
  - On the lock: every live run in this pass (E1–E5, the path-length checks and
    the E6 driver) was invoked through `tests/lib/checkout_lock.sh`. That is
    recorded only in this session's command history. No saved capture records it.
  - The final text says this in its evidence section, instead of stating the lock
    as if a capture showed it.
  - The path-length runs are renamed E7a/E7b in the final text (the run
    directories stay `runs/c7_len45` and `runs/c7_len55`), so the record does not
    carry a validation-memo label.
- **V2-2 ("every other live actor is parked"): corrected, not only qualified.** A
  narrow check of the worker's control flow (`pw_probe_runner.c` 1660–1702) shows
  the statement was wrong for actors past their final visit.
  - After its last visit a worker does not park. It runs `erase_accepted_token`
    (1673), then the optional hang and signal seams, then `publish_done_and_exit`
    (1702). So at E6 V1's phase-3 and phase-4 hooks, A (whose last visit was
    phase 2) was exiting or had exited, not parked.
  - Parking applies to actors waiting for a later visit (`wait_for_activation`,
    which services inbound slots).
  - The final text now gives each other actor's state per hook row: parked before
    a later visit, past its final visit, or (V2) reaped. It states that the
    one-active-actor property rests on the scheduler's design and its source
    comment (`ActorScheduler.swift` 4–17, 406–407), not on a traced path for each
    actor.
  - The measured quantities do not depend on A's state. A's exit path erases only
    A's own settled inbound slots, which do not exist, and touches neither host
    custody nor B's region (`erase_authority`, C 579–590).

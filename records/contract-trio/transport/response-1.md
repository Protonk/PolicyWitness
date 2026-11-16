# Response 1: transport pass, dispositions for validation-1 and the coordinator's questions

The revised text is in `draft-2.md`. `draft-1.md` is unchanged.

## Validator concerns

**C1: incorrect citation for the host's `exclusive_plan_forms` refusal. Corrected.**
- `PWRunnerRequest.swift` line 127 decodes `actors`. Line 132 throws
  `exclusive_plan_forms` at path `["policy"]`. The siblings are at 138 and 141.
- The wrong citation, 68–73, came from line numbers that were relative to a
  `sed` excerpt.
- draft-2 TR-5 now cites 127–132, 138 and 141.

**C2: TR-1 overstates which native run reached the admitted-other row. Corrected.**
- The native ordinary baseline is `finished`/0, the admitted-finished row.
- TR-1 now credits `c/baseline0_bad_request_envelope.json` for the
  admitted-other row (host reply `bad_request`, run `bad_request`/1) and d1
  for the admission-refusal row.

**C3: the post-run absence checks are not in any saved artifact. Corrected and qualified. Part of the earlier claim is withdrawn.**
- The (c) check at 14:48:43 and the d2 PID check were seen at the terminal
  and never saved. draft-2 now labels both that way and gives the method and
  time.
- While doing this I found a further problem with the d2 check at 14:43:16.
  Its pattern was `PWRunner\.xpc/Contents/MacOS/(pw-probe-runner|PWRunner)`.
  That pattern cannot match a worker, because a worker's argv[0] is the bare
  name `pw-probe-runner`, as shown in `c/kill_log.json`.
- So the earlier statement that no `pw-probe-runner` process existed at
  14:43:16 is withdrawn. The check shows only that no PWRunner host with
  that path in its argv remained.
- Nothing is established about the d2 worker.

**C4: steps 3 and 4 of the precedence list cannot co-occur. Corrected.**
- Answer 2 now presents host-frame refusal and the non-reply terminal as two
  alternatives under one step. An accepted capture has a host frame exactly
  when its terminal is `runner_reply` (runner_client.rs 478–481).
- The precedence table now has a note saying those four rows are
  alternatives.

**C5: B5a is a truncation, not a fixed-length edit. Corrected.**
- The C-class definition now lists the ways capture bytes were used:
  verbatim, same-length substitution, truncation (B5a only), or
  construction.
- The B5a table cell now says "r1 truncated by one byte".

## Coordinator questions

**Q1: platform. Corrected.**
- macOS 26.7.1, build 25G241 (`sw_vers`), Darwin 25.6.0, arm64.

**Q2: precedence between host frame and terminal. Corrected.**
- Covered by the C4 correction.

**Q3: empty host bytes. Qualified, with source and inference separated.**
- Swift client:
  - `submissionReply` checks no length when `isResult` is true. It stores
    `PWRunnerReplyCapture(data)` and completes `"runner_reply"`
    (`PWRunnerClientSession.swift` 260–262).
  - `PWRunnerReplyCapture.init` records 0, 0 and `false` for empty data
    (`PWRunnerTransport.swift` 163–168).
  - `emit` exits 0 for `runner_reply` (`main.swift` 30).
- Controller:
  - `validate_capture` tests presence through the `Option`, not by length
    (478–481), and its retention checks hold for zero (575–587).
  - `decode_bound` refuses a frame shorter than 36 bytes as `Malformed`
    (`porcelain.rs` 179–181).
- Still inference: that NSXPC delivers a zero-length `Data` to the reply
  block. draft-2 labels it as inference. No path reaching the empty writer
  was executed.

**Q4: source of the `ba483826` quotation. Corrected.**
- The quotation comes from the commit message.
- The same commit put the rationale in two other places, both now cited:
  - `PolicyWitness.md` line 110 at that commit;
  - the `run_flow.rs` module comment.

**Q5: "They depend on nothing else in common". Qualified.**
- This is a judgment from the paths I traced, not the result of a search.
  draft-2 now says so.

**Q6: aftermath observations. Corrected.**
- Covered by the C3 correction. Each statement now says whether it is saved
  in `kill_log.json` or was seen at the terminal, with time and command.

**Q7: reading back the file on disk. Done for draft-2.**
- The read-back found these problems, now corrected:
  - A sentence placement in TR-1 that ran the conclusion into the
    parenthetical.
  - "No file in X mentions": reworded.
  - The ARCHITECTURE 462–466 quotation was attributed the README's wording.
    They are now quoted separately.
  - "Exited 0.2 s later". `kill_log.json` gives the signal at 0.19 s after
    launch and the exit 19 ms after the signal.
  - The cost sentence on `policy_check`. Presence implies `invoked`, which
    the earlier wording denied.
  - "Executed in the cases cited" for the diagnostics key on rows whose
    evidence is source or a unit test.
  - "Fallback has never accompanied". Now scoped to production.

## Disputes

None. No item needs revalidation for a dispute.

The withdrawal in C3, about the d2 worker, and the timing correction in Q7
are factual corrections against the saved artifacts. A validator can check
both:
- `c/kill_log.json` event times;
- the worker argv in its `chain_found` event.

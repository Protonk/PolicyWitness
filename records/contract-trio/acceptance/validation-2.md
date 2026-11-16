# Validation memo 2: acceptance report (draft-2), targeted revalidation

Validator: Sonnet. Same boundaries as validation-1 (read-only; no Swift, seam or live reruns). I diffed `draft-1.md` against `draft-2.md` and read each changed passage against `response-1.md`, source and `reader-case-map.jsonl`. validation-1 is untouched.

## 1. Did draft-2 make the described changes, and do they resolve V-1 to V-7?

- **V-1 resolved.** DT-61 step 5, the AC-4 heading and the "cannot distinguish" paragraph now state both directions: applied implies not terminal (Rust `application`, porcelain_actor.rs 468-603; Python `_application`), and no reader relates `ready` to its cells or `required`. I rechecked the Rust/Python relation in validation-1; nothing new overstated.
- **V-2 resolved.** DT-48 "What this establishes" is split into claimed-order (Rust and consumer reject; oracle does not check `order`, `[]`; Swift by source, PWRunnerReply.swift 365-368) and no-claim (live, every boundary accepts). Matches `analysis.txt` and the live summary.
- **V-3 resolved.** Section 3 rows, the Section 4 bullet and AC-3 now name the readers run and mark Swift as by source. The reworded DT-61 row ("Shared assumption") is consistent with 34-equipment 912-917 and with the decoder argument check (AuthoritySetupRuntime.swift ~98). No new overstatement found; the author's own classification (not delegation, not questionable) is argued from absence of a delegating statement, which I did not find either.
- **V-4 resolved**, subject to section 2a below.
- **V-5 resolved with one residual (W-2 below).**
- **V-6 resolved.** The stated searches match what I found: `query_column` uses at consumer.py 1142 (inside `select`), check_query_scope.py 166, check_comparison_matrix.py 151 (beside `COMPARISON_KEYS`, six keys including `order`, consumer.py line 52), and one `select(... query=)` at check_query_scope.py 190.
- **V-7 resolved.** DT-38/47 stay with AC-1 for the JSON-fixture control; DT-101 moved to the DT-95 section and AC-5. The carried limits (eleven corruptions assert unavailability only, six of nine reasons in no test, no case combines two failures) match the DT-101 entry text.

## 2a. Scheduler-gate trace (supported)

Checked in source:
- ActorScheduler.swift 257-266: the gate is inside `if let status = setupDisposition(session)`, i.e. only after a published, non-failed, non-terminal decision; refusal condition is `actorSetup != 0 && (authorityStatus >= 3 || (authorityFD != nil && authorityStatus != 1))` as quoted.
- Status constants (abi.h 161-162): 0, 1 MAPPED, 2 DESCRIPTOR_MISSING, 3 REJECTED, 4 LOCAL_FAILED. Worker (pw_probe_runner.c 750): `authority ? MAPPED : (required ? LOCAL_FAILED : DESCRIPTOR_MISSING)`, so only 1, 4, 2 are written. 3 is never written but the gate refuses it; 0 with a descriptor refuses (`!= 1`); 0 without a descriptor passes (draft-2 says "Without a plan, status 0 or 2 passes and 3 or more refuses", correct). `authorityStatus` reads 0 unless the decoder observed the decision (ActorSession.swift 490).
- `authorityFD = custody?.descriptor(for:)` and `authorityRequired = input.authority != nil` (ActorScheduler.swift 231-232). `custody` exists only when a plan exists (210-211). `descriptor(for:)` returns nil only if `coreLimitFailure != nil`, the index is out of range, or the region has a failure (AuthorityCustody.swift 407-410). `setupFailure` returns non-nil for exactly the core-limit and region failure cases (390-398), and when non-nil the scheduler sets every actor `launchRefused` and returns before any session exists (ActorScheduler.swift 208-217). So for a launched actor in a plan run the descriptor is present and the gate reduces to `status == 1`. The trace holds by source. The `AuthorityCustody` descriptor is a non-optional `Int32` (default -1, closed only after session creation, line 207-213), so the nil test is not defeated by a closed descriptor at gate time.
- Not checked: that `regions` always has one entry per actor (the out-of-range branch). The draft's Section 7 correctly lists the reduction as source-only.

The wording in AC-4 and Section 4 ("for an actor in a run with an authority plan ... by source") is correctly conditioned. No new overstatement.

## 2b. AC-6 reading of FAILURE-PROPAGATION-CONTRACT.md 605-614

- Quotation: draft-2 AC-6's block quote matches lines 605-614 verbatim (I compared against the file). The label "lines 605-614 read in full" is literally true for those lines, but the paragraph runs to line 622. The omitted tail says a copied block "fails validation", that "unexpected, duplicate and null-ID validator records remain intentional diagnostic evidence, retained with their association issues", and that PID uniqueness is not an invariant. None of it states an equality relation, so the reading "procedure stated, relation not stated" is unaffected. But `response-1.md` Q5 says "the sentence and the rest of its paragraph (lines 605-614) are quoted in full", which overstates: the paragraph is not fully quoted.
- Consistency (see W-1): AC-6 now reads the paragraph as fixing a procedure, which AC-2's "Statements" paragraph matches ("matches the ownership paragraph quoted under AC-6"). Two places still read otherwise.

## New concerns

### W-1. The weaker line-605 reading is not applied uniformly (overstated / inconsistent, minor)

Located: DT-50 "Statements" bullet; AC-2 "Cost".

Checked: the DT-50 bullet opens "The rules write identity as an unqualified `==`" and lists line 605 as one of the three examples, then adds "That sentence fixes a procedure but states no equality relation". The list item and its qualification conflict. AC-2 Cost still says the host's decisions "follow a rule that the independent readers do not apply", whereas AC-6 now says readers apply the same procedure with different equality relations.

Finding: the claim a statement writes identity as `==` is not supported for line 605 under the author's own reading. To be consistent, the bullet should list line 605 separately (as procedure-only) and AC-2 Cost should say the readers apply the same procedure under a different equality relation.

### W-2. The "thirty ... run the consumer" headline includes a case that does not call the consumer in its mode (scope wording, minor)

Located: DT-53 "Thirty default cases run the consumer without the oracle" and AC-3 "Thirty default cases call the consumer without the oracle".

Checked: `runner_validator_failure/transcript_controls` runs `check.py fixture`, which calls `check_fixture` (check.py line 53); `consumer` is used only in `check_cli` (line 72 onward, uses at 107-114). The map attributes the consumer to the file, not to the invoked mode, so this case counts as consumer-bearing only by file. Draft-2 does classify it as offline, which removes it from the 28 and from the 26, so the 28/2/26 figures are unaffected.

Finding: the 28 / two-offline / two-asserting / 26 arithmetic is sound against `reader-case-map.jsonl` (30 consumer-only default cases by distinct case) and the named lines. I confirmed: example_round_trip_controls.py lines 4-12 say "No process is launched"; check_example_round_trip.py 1123-1124 and 1321 assert `disposition_integrity == 'valid'`; check_worker_termination.py line 93-94 asserts `process_disposition`; check_pre_apply_failure.py 67-80 admits `termination_cause` in `(None, 'unknown', labels)`. Wording would need "thirty by file attribution" or to exclude `transcript_controls` from "call the consumer". I verified only that comparison_matrix, test_input, example_round_trip_controls and transcript_controls are as classified; I did not verify each of the other 24 individually as live.

## Unresolved limits

- All Swift reasoning, including the gate trace, is source reading.
- Whether `regions` always has an entry for every actor index was not traced.
- The other 24 consumer-only cases' "runs the app" status was not individually confirmed.
- I did not re-verify hashes for draft-2 (the author lists draft-1's hash only).

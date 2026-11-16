# Response 1: acceptance pass, revision of draft-1 into draft-2

Author's dispositions of `validation-1.md` (V-1 to V-8) and of the
coordinator's six questions. `draft-1.md` is unchanged (SHA-256 `f77e436a…715c`).
All corrections are in `draft-2.md`. No new experiment was run. The additional
checks were source reading only.

## Validator concerns

- **V-1 (no reader relates `setup_status` to the scope): corrected.** Confirmed:
  - Rust `application` (porcelain_actor.rs lines 468–603) and Python
    `_application` (actor_evidence.py lines 162–225) reject an `applied` actor
    with an observed `terminal_required_failure` scope.
  - Both tie `terminal_authority_setup_refusal` to such a scope.

  In draft-2, DT-61 step 5, the AC-4 heading and AC-4's "cannot distinguish"
  paragraph now state the direction that exists (applied ⇒ not terminal). They
  also state the direction that is missing: no reader relates `ready` to its
  prerequisite cells or to `required`.
- **V-2 (no reader accepts an incoherent claimed order): corrected.** The DT-48
  "What this establishes" passage now says:
  - Rust (`withheld`/`invalid`) and the consumer reject the frame;
  - the oracle does not check `order` and returned `[]`;
  - Swift was not run on this frame, and by source it would reject the claim
    (PWRunnerReply.swift lines 365–368).

  The live statement for the record without an order claim keeps "every
  boundary", because the Swift host did process that live run.
- **V-3 ("all/every reader" for the f61 and f95 edits): corrected.** The
  Section 3 rows and the Section 4 bullet now name the readers that were run
  (Rust, the consumer, `actor_evidence`, `extension_evidence`, the oracle) and
  say Swift's agreement is by source. AC-3's "a frame read by every reader" now
  says "by the Rust and Python readers". The DT-61 baseline sentence names the
  Swift host and the Rust and Python readers.
- **V-4 (scheduler gate paraphrase): corrected; the open question is traced.**
  The gate's expression and status values are now stated in DT-61 step 3, in
  the Section 1 scheduler row and in AC-4. Q1 below gives the trace.
- **V-5 ("twenty-seven assert neither"): corrected.** See Q3. The figures are
  now 30 consumer-only default cases, of which 28 run the app. Two of those 28
  assert a Rust diagnostics value that a withheld projection changes, which
  leaves 26. The search patterns are stated. The text now notes that an
  `ok`/exit assertion cannot substitute, because Rust findings do not change
  the result.
- **V-6 (query-column search unstated): corrected.** The DT-48 paragraph now
  states both searches and their results:
  - `query_column` in `*.py` under `tests` (excluding `tests/out`): three uses,
    including `check_query_scope.py` line 166 and `check_comparison_matrix.py`
    line 151, which compares beside all six comparison keys including `order`
    (lines 148–152);
  - `select(` with `query=`: one use, line 190.
- **V-7 (DT-101 attachment and its limit): corrected.**
  - In Section 6, DT-38 and DT-47 stay with AC-1, for the JSON-fixture order
    control.
  - DT-101 moves to the DT-95 section and AC-5.
  - The DT-95 "Checked by the host decoder" list now says the nine conditions
    are source-read. Carried from DT-101: the unit check asserts unavailability
    for eleven corruptions but no reasons; six of nine reasons occur in no
    test; no case combines two failures.
- **V-8 (citations): no change needed.**

## Coordinator questions

1. **V-4 and AC-4: corrected; traced in source.** The gate is
   `actorSetup != 0 && (status >= 3 || (authorityFD != nil && status != 1))`
   (ActorScheduler.swift lines 257–266).
   - Status values (pw_probe_runner_abi.h lines 161–162): 0 none, 1 MAPPED,
     2 DESCRIPTOR_MISSING, 3 REJECTED, 4 LOCAL_FAILED.
   - The current worker writes only 1, 4 or 2 (pw_probe_runner.c line 751).
     REJECTED is not written. The host reads 0 until the decoder has observed
     the decision (ActorSession.swift line 490).
   - `authorityFD` comes from `custody?.descriptor(for:)` (ActorScheduler.swift
     line 231). With a plan, the descriptor is nil only after a core-limit or
     region failure (AuthorityCustody.swift lines 407–410). Either failure sets
     `setupFailure` (lines 390–398), and then every actor's launch is refused
     before any session exists (ActorScheduler.swift lines 208–217).
   - So, by source, every launched actor with required authority has a
     descriptor, and the gate cannot pass without status 1. Without a plan,
     status 0 or 2 passes and 3 or more refuses.

   AC-4 is restated as "gated on a header word", with this expression and its
   reduction. The reduction is listed as source-only in Section 7.
2. **V-2 readers: corrected.** Executed rejection: Rust and the consumer. The
   oracle does not check `order` (`[]`). Swift was not run (source: it would
   reject).
3. **`example_round_trip_controls`: qualified.** It reads authored envelopes
   "in place of the app's emission", and no process runs
   (example_round_trip_controls.py lines 4–12). It tests the round-trip checker
   on constructed envelopes, not a live run's diagnostics. It is now counted as
   offline, with `runner_validator_failure/transcript_controls`. The figures
   become 28 live consumer-only default cases. Two of them assert a
   diagnostics value a withheld projection changes (`example_round_trip`,
   `worker_termination`). Two more, `pre_apply_failure_reports_no_policy_verdict`
   and `dossier_witness`, mention diagnostics but would not detect one. That
   leaves 26.
4. **Section 3 DT-61 row: classified as a shared assumption.** The readers
   agree because they rely on the producer:
   - the decoder projects `ready` only when its required argument is true, and
     copies the argument into `required`;
   - the C worker writes READY only after every prerequisite.

   The conditions are stated as host or host/worker obligations
   (34-equipment lines 912–917 under a `who: host` report; 14-extensions
   lines 349–360). No recipient check is assigned. It is not deliberate
   delegation: no statement delegates it, unlike DT-95's line 309, and I found
   no rationale. It is not a questionable rule: the condition holds in
   production.
5. **AC-6 and FAILURE-PROPAGATION-CONTRACT.md line 605: qualified.**
   - The sentence and the rest of its paragraph (lines 605–614) are quoted in
     full in AC-6.
   - The paragraph promises one ownership procedure: stamp comparison, plan
     comparison, and recomputation of the issues the records and plan imply.
     It states no equality relation.
   - AC-6 no longer says the paragraph "promises" cross-language agreement. It
     now reads the divergence as an unstated relation that the implementations
     bind differently, rather than a contradicted promise.
   - AC-2's sentence on the PWRunnerPredictionEvidence.swift line 157 comment
     and the DT-50 "Statements" bullet are aligned with that reading.
6. **On-disk text: done.** I read draft-2 back in full after writing it. I
   corrected three formatting effects of the edit procedure:
   - a bullet whose continuation lines lost their indentation;
   - a sentence merged into the next paragraph;
   - one unqualified "exactly", now limited to launched actors.

   No other on-disk text differs in meaning from what I intended.

## Disputes

None. Every concern was confirmed and corrected or qualified.

## Suggested revalidation

Two changes are new reasoning rather than wording, and revalidation may
target them:

- the source trace in Q1 that reduces the scheduler gate to status 1 for
  launched required actors;
- the weakened AC-6 reading of line 605.

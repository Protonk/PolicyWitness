# SCAN acceptance: a completed-prefix cursor for the inbound scan

Branch 3 of the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md),
opened after branch 2 closed with HOST-01, HOST-02 and HOST-03 integrated.
Committed before any comparison measurement, after the candidate was
implemented, reviewed and verified; the protocol below is frozen before the
comparison, and later changes are recorded as revisions. Raw evidence under
`tests/out/` is gitignored and available only in the local checkout.

## Candidate

`service_inbound_once` runs between polls of the parked-activation wait and of
the authority exchange wait and visits every inbound slot from index 0, with an
acquire load of `committed` and, for a committed slot, of `acknowledged`,
acknowledging at most the lowest committed, unacknowledged slot per pass.
Each slot serves one delivery; after the host's commit its `acknowledged`
word is written only by the recipient, once, so every pass after a slot's
acknowledgement reloads words whose answer cannot change. In the HOST-03
comparison's A2 trials the candidate side, whose production source this
record's baseline carries, had the subject actor make 15,554 to 20,855 scan
passes per request, visiting both of its slots on every pass but the one that
acknowledged slot 0 (31,107 to 41,709 visits, 31,264 to 46,472 loads). Most of
those passes precede slot 0's commit, where no cursor can save anything; the
redundant work is the reloading of slot 0 on every pass after its
acknowledgement and of slot 1 after its own.

The candidate keeps one worker-local word, the count of leading inbound slots
this worker has itself acknowledged, and a local record of its own
acknowledgements; the scan starts at that prefix and the prefix advances only
after this worker's own acknowledgement store, across slots it acknowledged
itself. Both are reset when the authority region is prepared. Every visited
slot is checked exactly as before; lowest-index selection, one acknowledgement
per pass, settlement, consumption, erasure and cleanup are unchanged; a
committed lower slot this worker has not acknowledged is visited every pass,
and an uncommitted lower slot stops the prefix without blocking higher slots.
No shared word is added or written that was not before. The state is one
32-bit word and a fixed 64-byte array (`PW_AUTHORITY_MAX_INBOUND`), 68 bytes
per worker. Each pass loads the word once in place of the constant 0. Each
acknowledgement stores one local byte and runs the advance loop: every
iteration reads the shared `inbound_count`, compares the prefix against it and
the array bound, and, until the stopping iteration, reads one local byte and
stores the advanced prefix. The array write is bounded the same way.

## Identities

- Baseline source: `365260fb` on `main` (production source equal to
  `66430db5`; HOST-01, HOST-02 and HOST-03 integrated); worker identity
  `57dbfd28a58849ff7526aa79d21cfce87dd5b165b408746115268fb363c6d363`. Baseline
  app: the distribution build in the main checkout, provenance `66430db5`,
  dirty false (host `89cb0c09…`, worker `74d06c15…`); its verification is
  recorded in the HOST-03 record's outcome.
- Candidate source: commit `b93cb5c4` on branch `wait/scan` in the worktree
  `PolicyWitness-wait-scan`, clean (two commits: the cursor with its scenarios
  and documentation, then the registered cursor mutations); worker identity
  `564477bc0b94cbaf0d99ae4f3cd82f2cd2ec20298c60218e4542c551b68298ee`.
  Candidate app: its distribution build (provenance `b93cb5c4`, dirty false);
  host `9d589c8c…`, worker `8b3abdac…`.
- Readers and fixtures, main checkout at `04669583`, used for both sides:
  pilot reader version 9 `99026c6f…`, its controls `d29b5074…` and wrapper
  `8662d460…`, driver `2f29bf31…`, actor workloads `a26af28f…`, opt-in
  wrapper `1ca9458f…`, host patch set `9b1abd40…` (no patch is specific to
  either tree; the exit-wait patch applies to both), `HostStamps.swift`
  `df37674a…`, worker build `aab37da3…`, stamp worker `5bc7937e…`, stamp page
  header `a63b0f68…`, clock pair `19d8b521…`. The scan counters come from the
  existing seams, counted by the stamp worker built from each tree; no CPU
  reader, so total CPU and sampled memory are unobserved, not unchanged.

## Workloads and trials

The pilot cells plus `A2D`, the inbound-dense actor workload (the A2 actors;
the issuer's phase issues 32 file tokens and transfers each twice to the
subject, 64 deliveries filling the subject's inbound slots in index order; the
subject's phase consumes and releases two of them), in both regimes, five matched pairs per cell and regime, alternating order per
repetition, both apps staged as instrumented builds under one cleanup rule,
calibration first, pilot conditions and exclusions; one announced quiet
window of four minutes (the driver's planning estimate is 168 s for 140
trials: a flat allowance per trial that A2D's requests exceed, plus 60 s of
calibration, warm runs and the end reserve; HOST-03's 120 trials used 74 s).

## Claims and required observations

| Claim | Observation |
| --- | --- |
| Less repeated work in the inbound scan | A scan that starts at index 0 makes at least n·P − n(n−1)/2 visits, and as many loads, over P passes with n inbound slots (the full-scan floor), so visits per pass alone follow the pass count. In every matched pair of A2 and A2D in both regimes, the subject actor's visits and loads in the parked-activation scan (`w1.scan_visits_per_pass_activation`, `w1.scan_loads_per_pass_activation`) must be `lower_in_every_pair` as the reader defines it: the baseline's count at or above its own floor, the candidate's below its own floor, and the candidate's ratio strictly lower by exact arithmetic; and in every pair the candidate trial must record passes with zero visits (`w1.scan_zero_visit_passes`, the activation role since the subject makes no exchange pass; above 0 on the candidate side and 0 on the baseline side, read per pair). The exchange-wait series are reported and withheld where either side made no exchange pass. The ordinary cells have no scan; the issuer actor, with no inbound slots, is a no-benefit control whose series show zero visits and zero loads on both sides (`not_lower` with equal zero counts) and whose zero-visit passes are all of its passes on both sides. |
| Unchanged behavior | Decided by the verification runs below: the extended `authority_binding` scenarios (empty, single and maximum slot sets committed at once and one at a time, accepted and rejected prefix, early hole with late commit, later eligible slots, a foreign acknowledgement that must not advance the prefix, re-preparation) pass against the candidate with exact pass, visit, load, first-visit, acknowledgement and prefix counts; the four registered cursor mutations (scan from zero, advance past a hole, prefix from shared words, missing reset) fail their designated observations in `runner_unit/actor_handoff_mutations`; and `extension_boundaries`, `actor_compositions`, `order_barrier_mutations` and `actor_timing_qualification` pass. Decided by the comparison: every trial delivers every transfer (the driver refuses a trial otherwise, so an accepted run establishes it), and both sides' acknowledged slots equal the layout in every pair (the reader's `scan_inbound_acknowledgement_mismatch` refusal, which withholds the series, does not fire). |
| Response | The two wait roles the scan runs in are the parked activation wait and the exchange wait, so the bounds are `activation_response` (activation store to arrival) and, new in reader version 9 for this record, the custody rows' `inbound_response` (the host's transfer wait start, right after its commit, to the recipient's acknowledgement publication), each the candidate's upper bound against the baseline's lower bound within 2 ms and credited; `release_to_ack` is reported as before. |
| No resolved regression | No quantity, in any cell, worsens beyond spread in every pair, apart from one named in advance as changed by construction: the subject's parked-activation pass counts (`pN.activation_wait` passes for the subject's visits in A2 and A2D) rise because passes that skip the prefix are shorter while the parked time is set by the other actor's phases (the dry run showed 11 to 14 percent more passes in A2D); they are reported, not gated. Held intervals, whole request, response and every other quantity stay under the clause. A resolved increase in whole request needs a written tradeoff decision before acceptance; total CPU and sampled memory are unobserved. |
| State and bookkeeping | Reported, not gated: the cursor's bytes per worker, one comparison per pass and one advance loop per acknowledgement. No CPU or energy claim is made from the counts. |

Decision rule, frozen:

- Accept when the work claim's verdicts are true in every A2 and A2D group of
  both regimes, the zero-visit condition holds in every pair, the behavioral
  controls and live cases passed, every response bound is credited, and no
  quantity other than the named pass counts worsens beyond spread in every
  pair.
- If a work verdict is false (any established pair not lower, or a pair
  without zero-visit passes on the candidate), reject, whatever else holds.
- If a work verdict is withheld (a refused, absent or `no_passes` pair, or
  fewer than five established pairs), the run does not decide: the cause is
  recorded and the comparison is repeated after it is fixed, under a revision.
- If a trial is refused for undelivered transfers, the run does not decide and
  the refusal is investigated as a behavioral failure before any repeat.
- If the work claim holds but a response bound is not credited or a quantity
  other than the named pass counts worsens beyond spread in every pair, the
  candidate is not accepted; the decision is the owner's with the
  coordinator's recommendation.

## Verification before comparison

In the candidate worktree against its signed build: `runner_unit`,
`runner_abi_layout`, `source_drift`, `runner_c_worker_harness` including the
extended `authority_binding`, `failure_boundaries`, `runner_exec_inheritance`,
`witness_contract/phases`, `attempt_effects_wait_for_collection`,
`actor_compositions`, `extension_boundaries`, `order_barrier_mutations`,
`actor_timing_qualification` and the default battery. Regenerated worker
identity and architecture account are part of the candidate. On `main`:
`witness_contract/worker_wait_pilot_controls` with the reader's new controls,
a re-read of the HOST-03 comparison with the new reader showing every frozen
verdict unchanged, and a comparison dry run over A2 and A2D.

## Verification results

Candidate worktree, against its signed build, before the comparison:

- Cursor and scenarios (`e3fdaa3d`): `runner_unit`, `runner_abi_layout`,
  `source_drift` and `runner_c_worker_harness/authority_binding` failed one
  case in run `20261108T042036Z_f599d34d` (`scan-unit-01`), the drift suite's
  prose check refusing two numeric literals in the new `docs/WORKER.md`
  sentence, which was reworded; 22 of 22 pass in `20261108T042921Z_1be112fc`
  (`scan-unit-02`) against a build of the then-uncommitted tree later
  committed as `e3fdaa3d` (identical production source; that app's hashes
  were not recorded). The
  evidence review then found that the scenarios' sensitivity to a broken
  cursor existed only as unregistered scratch runs; `b93cb5c4` registers four
  cursor mutations in `runner_unit/actor_handoff_mutations`, each failing its
  designated observation while the unmodified copy passes.
- On the tree later committed as `b93cb5c4`: the same selection with the
  registered mutations, 22 of 22 pass in `20261108T044436Z_295527fe`
  (`scan-unit-fix-01`), against the app built from `e3fdaa3d` with the
  uncommitted test and documentation changes (provenance `e3fdaa3d`, dirty
  true; identical production source). The mutation case's source manifest
  equals `b93cb5c4`.
- On the candidate app rebuilt from the clean tree (provenance `b93cb5c4`,
  dirty false): the named selection of `witness_contract/order_barrier_mutations`, `phases`,
  `attempt_effects_wait_for_collection`, `actor_compositions`,
  `extension_boundaries`, `actor_timing_qualification`, the
  `failure_boundaries`, `runner_c_worker_harness` and `runner_exec_inheritance`
  suites: 77 pass plus the `native_pause` applicability gate in
  `20261108T045154Z_70e4ab14` (`scan-named-01`); default battery 222 of 222 in
  `20261108T045625Z_8f1fb9be` (`scan-default-01`). No case in any run
  overlapped system sleep.

Main checkout (readers):

- A2D cell and scan pairs (on the tree later committed as `565604c9`):
  `witness_contract/worker_wait_pilot_controls` pass in
  `20261108T041944Z_a4ec52f1`; comparison dry run with the main app on both
  sides over A2 and A2D, pass in `20261108T042007Z_d05e226d`, the A2D request
  admitted with all 64 deliveries delivered. Its review found that a
  strict ratio comparison is decided by the pass count alone (identical apps
  gave "lower" in single pairs), and that the inbound-count refusal read only
  the declared layout; `0a0a7013` adds the full-scan floor conditions and the
  observed-acknowledgement refusal, with controls for identical scans at
  different pass counts and a reader that ignores the floor. Controls pass in
  `20261108T043641Z_5600b199` (`scan-inst-controls-fix-01`, on the tree later
  committed as `0a0a7013`; 60 accepted receipts, 76 faults rejected). `source_drift` on `0a0a7013`: 9 of 9 in
  `20261108T051527Z_77cffb4c` (`scan-main-drift-01`).
- Re-read of the HOST-03 comparison with reader version 8: all 540 frozen
  series (component, wait and whole-request verdicts and response bounds)
  equal to the committed summary, only the scan fields added. Under the floor
  rule HOST-03's subject scan pairs, which the strict ratio had called lower,
  are not lower, as expected of a candidate that did not change the scan.
- Inbound-delivery response bound (`04669583`, reader version 9): the referee of
  this record found that it named a recipient-acknowledgement bound the reader
  did not compute; the custody rows now carry `inbound_response` and the
  response bounds include it. Controls pass in `20261108T054516Z_27698b67`
  (`scan-inbound-controls-01`, 60 accepted receipts, 76 faults rejected). The
  HOST-03 re-read with version 9 keeps all 540 series equal and adds eight
  (the A2 custody rows' `inbound_response` components and bounds, 166 to
  250 ns, credited); the scan dry run re-read gives 64 credited bounds per A2D
  group, the largest 13.2 µs, and 2 per A2 group.
- Comparison dry run, baseline app against the candidate app, one repetition
  of every cell and regime including A2D: pass in `20261108T051317Z_c1f60f1e`
  (`scan-compare-dryrun-01`), 28 trials accepted, reader version 8, no host
  patch skipped on either side, trees clean at `0a0a7013` and `b93cb5c4`, no
  scan refusal. The subject's parked-activation scan was `lower` in each of
  the four pairs. Idle: A2 38,485 visits over 19,243 passes against 35,324
  over 20,039 (loads 42,383 against 35,326); A2D 24.8 million visits over
  387,484 passes against 18.1 million over 430,630 (loads 32.5 million against
  18.1 million). Rapid: A2 42,487 over 21,244 against 37,349 over 21,237
  (loads 47,673 against 37,351); A2D 24.1 million over 376,426 against 17.8
  million over 427,812 (loads 31.4 million against 17.8 million). The A2
  saving is small because about three quarters of the subject's passes
  precede slot 0's commit and the second delivery commits only in the fourth
  phase; in A2D the prefix advances as the 64 deliveries commit in index order
  and the loads fall by about 44 percent. Zero-visit passes on the candidate:
  40 and 41 in A2, 123 and 67 in A2D; none on the baseline. The issuer's
  series showed zero counts on both sides. The subject's parked pass counts
  rose on the candidate (A2D 387,484 to 430,630 and 376,426 to 427,812),
  the by-construction effect the regression row names. Mechanics only; no
  trial of a dry run is evidence.

## Results

Pending the comparison window.

## Revisions

None yet.

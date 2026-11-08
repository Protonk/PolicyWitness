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
acknowledgement stores one local byte and runs the advance loop: each
iteration reads the shared `inbound_count` and compares the prefix against it,
then (short-circuiting) against the array bound and the local byte, storing
the advanced prefix once per slot advanced. The array write is bounded the
same way.

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
| Response | The two wait roles the scan runs in are the parked activation wait and the exchange wait, so the bounds are `activation_response` (the host's activation store to the worker's activation publication) and, the custody rows' `inbound_response` (commit publication to the recipient's acknowledgement), each the candidate's uncertainty-expanded upper bound against the baseline's uncertainty-expanded lower bound within 2 ms and credited, as is `release_to_ack`. The [acceptance review](WORKER-WAIT-REVIEW.md) corrects version 9's post-commit wait-start endpoint with a conservative commit bracket and requires complete response coverage. In every cell the subject acknowledges while parked, so `inbound_response` is observed in the parked-activation role; no comparison cell exercises the exchange call site with inbound slots (it calls the same function, which the scenarios exercise directly). |
| No resolved regression | No quantity, in any cell, worsens beyond spread in every pair, apart from one named in advance as changed by construction: the subject's parked-activation pass counts (`pN.activation_wait` passes for the subject's visits in A2 and A2D) rise because passes that skip the prefix are shorter while the parked time is set by the other actor's phases (the dry run showed 11 to 14 percent more passes in A2D); they are reported, not gated. Held intervals, whole request, response and every other quantity stay under the clause. A resolved increase in whole request needs a written tradeoff decision before acceptance; total CPU and sampled memory are unobserved. |
| State and bookkeeping | Reported, not gated: the cursor's bytes per worker, one local load per pass and one advance loop per acknowledgement. No CPU or energy claim is made from the counts. |

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
  (`scan-unit-fix-01`), against the app then in the worktree's `dist`, built
  from `e3fdaa3d` with the uncommitted test and documentation changes
  (identical production source; the run retains no provenance and the app
  was rebuilt after it). The mutation case's source manifest equals
  `b93cb5c4`.
- On the candidate app rebuilt from the clean tree (provenance `b93cb5c4`,
  dirty false): the named selection of `witness_contract/order_barrier_mutations`, `phases`,
  `attempt_effects_wait_for_collection`, `actor_compositions`,
  `extension_boundaries`, `actor_timing_qualification`, the
  `failure_boundaries`, `runner_c_worker_harness` and `runner_exec_inheritance`
  suites: 77 pass in `20261108T045154Z_70e4ab14` (`scan-named-01`), with
  `native_pause` failing as the intentionally failing applicability gate on
  this equipment; default battery 222 of 222 in
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
  response bounds include it. On the tree later committed as `04669583`:
  controls pass in `20261108T054516Z_27698b67` (`scan-inbound-controls-01`,
  60 accepted receipts, 76 faults rejected); the HOST-03 re-read with
  version 9 keeps all 540 series equal and adds eight (the A2 custody rows'
  `inbound_response` components and bounds, 166 to 250 ns, credited); the scan
  dry run re-read gives 64 credited bounds per A2D group, the largest 13.2 µs,
  and 2 per A2 group (outputs under `.tmp/worker-wait/reread-host03-v9/` and
  `.tmp/worker-wait/reread-scandry-v9/`, local checkout only).
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
  rose on the candidate (A2D `p1.activation_wait` 387,485 to 430,631 and
  376,427 to 427,813 passes), the by-construction effect the regression row
  names; with one pair per group every spread verdict is withheld, and the
  single-pair any-pair worsenings include many zero-spread count series in
  every cell, as a null comparison does. Mechanics only; no
  trial of a dry run is evidence.

## Results

Run `20261108T160221Z_850ecafb` in `tests/out/runs/worker-wait-scan-compare-01`
(gitignored, local checkout only). Announced quiet window of 240 s, of which
89.4 s were used; the machine reported AC power at 83 percent and charging
throughout (the owner had expected battery), low power mode off, load average
2.2 to 4.6 at trial starts, no system sleep, no observer overlap, no clock
inversion, no excluded or refused trial. 140 trials accepted, 70 matched
pairs, none unpaired; five pairs in each of the fourteen cell and regime
groups. Actual gaps: `rapid` 13.7 to 17.0 ms, `idle` 1005.2 to 1005.7 ms.
Calibration credited the instrument at a 458 ns endpoint term and 125 ns
alignment bound. The staged instrumented builds, not production bytes, were
host `347498da…` and worker `16f755bf…` for the baseline and host `8ca1c799…`
and worker `440f0686…` for the candidate; no host patch was skipped on either
side; trees clean at `2775c97d` (readers as frozen at `04669583`; the later
commits touched only this record) and `b93cb5c4`.

### Behavioral refusals (first in precedence)

None. Every trial delivered every transfer, and no pair was refused for an
acknowledgement mismatch or an inbound-count mismatch; the scan series carry
no problems in any group.

### Less repeated work in the inbound scan (the work claim)

`lower_in_every_pair` is true for the subject's visits and loads per pass in
the parked-activation scan in every A2 and A2D group of both regimes: all
twenty pairs lower, no condition unmet. Candidate zero-visit passes in every
pair, none on the baseline.

| Cell, regime | Visits per pass, baseline then candidate | Loads per pass, baseline then candidate | Load reduction per pair (percent) | Candidate zero-visit passes |
| --- | --- | --- | --- | --- |
| A2 idle | 2.00; 1.75, 1.75, 1.99, 1.76, 1.76 | 2.24; 1.75, 1.75, 1.99, 1.76, 1.76 | 23.0, 19.1, 33.3, 19.9, 22.5 | 44, 42, 40, 40, 41 |
| A2 rapid | 2.00; 1.75, 1.75, 1.99, 1.75, 1.99 | 2.24; 1.75, 1.75, 1.99, 1.75, 1.99 | 25.0, 22.8, 33.1, 19.1, 4.2 | 44, 41, 41, 44, 39 |
| A2D idle | 63.99; 41.13, 41.21, 41.74, 41.69, 41.45 | 83.9 to 84.6; 41.13, 41.21, 41.74, 41.69, 41.45 | 47.0, 45.2, 44.3, 44.1, 44.8 | 65, 71, 67, 65, 69 |
| A2D rapid | 63.99; 41.80, 41.79, 41.59, 41.39, 41.76 | 83.3 to 84.0; 41.80, 41.79, 41.59, 41.39, 41.76 | 41.4, 43.2, 46.3, 42.4, 43.1 | 66, 109, 123, 69, 75 |

In A2 the baseline's subject made 19,637 to 21,086 passes per request and
visited both slots on every pass but one (2.00 visits and 2.24 loads per
pass); the candidate's 1.75 to 1.99 visits and loads per pass reflect slot 0
skipped after its acknowledgement and slot 1 after its own, with about three
quarters of the passes preceding slot 0's commit, where nothing can be
skipped. In the fifth rapid pair the candidate made 8 percent more passes
(its parked wait was longer) so its total visits exceeded the baseline's;
its per-pass count was still below the full-scan floor, which is what the
rule asks. In A2D the baseline's subject made 371,000 to 390,000 passes and
visited all 64 slots on each (84 loads per pass, two for every committed
slot); the candidate visited 41 to 42 slots per pass on average, the prefix
advancing as the 64 deliveries committed in index order, and its loads fell
by 41 to 47 percent, 13.3 to 15.3 million per request. The exchange-wait
series were `no_passes` on both sides (the subject never waits in that role)
and the issuer's series showed zero visits and loads on both sides, as the
record said they would.

### Response, regression and the rest

- Response, superseding the original reader's nominal extrema and wait-start
  endpoint: the [version-10 reanalysis](WORKER-WAIT-REVIEW.md) expands bounds
  by uncertainty, checks complete coverage, and brackets legacy commits from
  custody-service start to wait start. All 172 bounds remain credited:
  `release_to_ack` 2.207 to 2.457 µs (26 bounds), `activation_response` 2.124
  to 9.082 µs (14), `inbound_response` 8.874 to 108.791 µs (132), against
  the 2 ms limit. The accepted scan-work claim is unchanged.
- `worsens_beyond_spread_in_every_pair` holds for exactly two series, the
  subject's `p1.activation_wait` pass count in A2D idle (389,174 to 420,976
  against 377,433 to 437,119) and rapid (374,755 to 438,191 against 371,255 to
  436,550): the exempt by-construction rise, 7 to 17 percent more passes in
  the same parked time. The other six exempt series moved both ways within
  spread. No other quantity worsened beyond spread in every pair, and no
  every-pair verdict was withheld. The any-pair spread verdict fired in
  isolated pairs as the null control predicts, including zero-spread count
  series.
- Held intervals and whole request: unchanged within spread in every group;
  A2 and A2D detection totals differ by a few microseconds except the
  bimodal 1.2 ms detections that fall on different sides in single pairs;
  whole request directions are 3 to 4 of 5 either way in every cell.
- State and bookkeeping: 68 bytes per worker, one local load per pass, one
  byte store and one advance loop per acknowledgement, as described. No CPU,
  memory or energy claim is made from the counts.

### Decision

Accepted. In the order the revised rule sets: no behavioral refusal; the
work claim's verdicts true in every A2 and A2D group of both regimes with
candidate zero-visit passes in every pair; the behavioral controls, the four
cursor mutations and the live actor cases passed in the verification runs;
every response bound credited; the only every-pair worsening is the exempt
parked pass count. The candidate is integrated into `main`; the integration
verification is recorded under Outcome.

Outcome: integrated into `main` as `d7d19a6b` and `d1821df6`, the candidate's
two commits cherry-picked with the session's trailer; main's production source
then equals `b93cb5c4` and its worker identity is `564477bc…`. Verification on
`main` against its rebuilt signed app (provenance `d1821df6`, dirty false):
`runner_unit` with its opt-in cases (the four cursor mutations among them),
`runner_abi_layout`, `source_drift` and `runner_exec_inheritance`, 26 of 26 in
`20261108T160653Z_473a7f18` (`main-scan-unit-01`); the named selection with
`order_barrier_mutations`, 72 pass in `20261108T161327Z_42310146`
(`main-scan-named-01`) with `native_pause` failing as the intentionally
failing applicability gate; default battery 222 of 222 in
`20261108T161704Z_e29fe638` (`main-scan-default-01`); no case overlapped
system sleep. The candidate worktree and its runs are retained until the
plan's closeout decides raw-evidence retention.

## Revisions

### Revision 1, before the comparison measurement

The second referee pass found no blocking defect but four points the decision
rule left open and one exemption to pin exactly. Frozen definitions stand;
these clarifications bind the comparison:

- Response bounds: `release_to_ack`, `activation_response` and
  `inbound_response` are all gated; "every response bound is credited" means
  every applicable bound across all declared trials and matched pairs. The
  [acceptance review](WORKER-WAIT-REVIEW.md) replaces the earlier "every bound
  emitted" interpretation: absent endpoints must withhold credit, and inbound
  publication must be bracketed at the commit, including the conservative
  legacy bracket used for this run.
- Precedence of the decision bullets: a trial refused for undelivered
  transfers, or a pair refused as `scan_inbound_acknowledgement_mismatch`, is
  a behavioral failure first: the run does not decide and the refusal is
  investigated before any repeat or rejection. Then a false work verdict or a
  pair without candidate zero-visit passes rejects, whatever else holds. Then a
  withheld work verdict for any other reason (absent pair, fewer than five
  established) means the run does not decide and is repeated under a revision.
  Then an uncredited bound or a resolved regression outside the exemption goes
  to the owner. Only a run that none of these catch accepts.
- A withheld `worsens_beyond_spread_in_every_pair` verdict (fewer than five
  established pairs for that quantity) leaves the regression clause undecided
  for that quantity; acceptance requires the clause established false for
  every gated quantity, and a withheld one is reported with its cause.
- The by-construction exemption names exactly the subject's parked-activation
  pass counts: `p1.activation_wait`, `p2.activation_wait` and
  `p4.activation_wait` in A2 and `p1.activation_wait` in A2D, in both regimes
  (eight series). The issuer's waits, the release waits and every other
  quantity stay under the clause.
- The baseline side's zero-visit passes above 0, or the issuer control's
  series not at zero on both sides, would show the instrument or the workload
  misbehaving and send the run to investigation like a behavioral refusal.

# HOST-02 acceptance: bounded re-sampling before the first sleep after a publication

Second candidate of branch 2 of the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md),
nominated by the [pilot](WORKER-WAIT-PILOT.md) and opened after HOST-01's
acceptance, which its baseline includes. Committed as the candidate opens; the
protocol below is frozen before any comparison measurement, and later changes
are recorded as revisions. Raw evidence under `tests/out/` is gitignored and
available only in the local checkout.

## Candidate

After the host publishes an activation, a release or an inbound delivery, the
worker answers within microseconds: the pilot measured activation to arrival
at 0.0 to 0.1 µs, release to acknowledgement at 0.1 to 0.3 µs and the parked
recipient's acknowledgement within 0.3 µs of its pass sample. The host samples
the answer once after the store, finds it absent, and sleeps a whole poll
period, so each detection cost the whole sleep: 1.25 ms for an actor's arrival
and completion and for the recipient acknowledgement, 2.4 ms for a later
ordinary phase's arrival.

The candidate re-samples the answer for at most 100 µs of clock time before
the first sleep that follows such a publication and then sleeps exactly as
today (`HostWaitClock.expiredAfterResampling`, used on the first pass after
the actor scheduler's activation store and release store, after the custody
code's inbound commit, and after the ordinary loop's release store). The
re-sampling is charged to the same allowance like any pass; no wake, thread,
descriptor or registration is added; every decision order, allowance and
ownership check is unchanged. The readiness byte is not re-sampled: the
worker's application takes up to milliseconds after it, so that detection
stays with the 2 ms sentinel poll and is recorded as a further delay.

## Identities

- Baseline source: `fc089ef7` on `main` (HOST-01 integrated); worker identity
  `a729571df02255983f5bf8e76883a7fb94166f6404cb869780e86997c4e57894`. Baseline
  app: the distribution build of that source in the main checkout, provenance
  commit `fc089ef7`, dirty false. Baseline verification: default battery 222 of
  222 pass in run `20261107T221005Z_e35b4797` (`main-host01-default-01`), during
  which one case, `preflight/build_provenance_controls`, overlapped a system
  sleep and was rerun without sleep in `20261107T231019Z_79b8e96c`
  (`main-host01-provenance-rerun-01`, pass); `order_barrier_mutations` pass in
  `20261107T230830Z_c4725a38`.
- Candidate source: commit `628a1ccc` on branch `wait/host-02` in the
  worktree `PolicyWitness-wait-host02`, clean; worker identity
  `69a3977788506b4f1dc818d5b1afcd8fad44994593737a6106871b1db1a719fb`. Candidate
  app: its distribution build (provenance commit `628a1ccc`, dirty false);
  host `2018ec11…`, worker `d8cb8f0b…`. The re-sampling window is bounded by
  the smaller of 100 µs and the remaining allowance, and by a sample cap of
  16,384 so a clock that stops advancing cannot hold the loop.
- Readers and fixtures, main checkout at `3c193f5e`, used for both sides:
  pilot reader version 5 with the detection total `e2cc5e07…`, driver
  `9027e742…`, host patch set `9645cdcd…`, worker build `aab37da3…`, stamp worker
  `5bc7937e…`; other fixture hashes as in the HOST-01 record. No CPU reader: the
  candidate changes no held-worker mechanism and claims no CPU benefit. It
  does add bounded host busy time, stated under claims.

## Workloads and trials

The six pilot cells in both regimes, five matched pairs per cell and regime,
alternating order per repetition, both apps staged as instrumented builds under
one cleanup rule, calibration first, pilot conditions and exclusions; one
announced quiet window of about four minutes.

## Claims and required observations

| Claim | Observation |
| --- | --- |
| Shorter held intervals in the actor form | Per trial, the sum of the host's post-publication detection latencies: arrival after activation for every visit, completion after release for every visit, and the recipient acknowledgement after each inbound commit (`detection_total`). Accepted only if the candidate's total is below the baseline's by more than the sum of both uncertainties in every pair of A2 in both regimes (`improves_beyond_uncertainty_in_every_pair`). Individual components are reported; they are bimodal on the baseline and are not gated singly. |
| Shorter held interval for a later ordinary phase | O2P phase 1 arrival to observation and held total: improvement beyond instrument uncertainty in every pair of both regimes. |
| No resolved regression | No quantity, in any cell, worsens beyond spread in every pair (`worsens_beyond_spread_in_every_pair`); a resolved increase needs a written tradeoff decision before acceptance. First-phase ordinary arrival, which the candidate does not change, is reported as unchanged. |
| Response | Release-to-acknowledgement and activation response, candidate upper bound against baseline lower bound, within 2 ms, credited. |
| Added host busy time | Re-sampling occurs at most once per publication and lasts at most 100 µs; the candidate's per-trial count of publications bounds it. Reported, not gated; no CPU claim is made either way. |
| Whole request | Per pair, reported with the spread verdicts. |

## Verification before comparison

In the candidate worktree against its signed build: `runner_unit` with the new
clock and scheduler controls, `runner_abi_layout`, `source_drift`,
`runner_c_worker_harness`, `failure_boundaries`, `witness_contract/phases`,
`attempt_effects_wait_for_collection`, `actor_compositions`,
`extension_boundaries`, `order_barrier_mutations`, `actor_timing_qualification`
(default) and the default battery. Regenerated worker identity and limits
account are part of the candidate.

## Verification results

Candidate worktree, against its signed build, before the comparison:

- `runner_unit` (11 cases, including the four opt-in mutation cases, with the
  new re-sampling clock controls and the live actor assertions),
  `runner_abi_layout/c_swift_layout_agreement` and `source_drift`: 21 of 21
  pass, run `20261107T234659Z_dc2cebb0` (`host02-unit-02`).
- `witness_contract/order_barrier_mutations`, `phases`,
  `attempt_effects_wait_for_collection`, `actor_compositions`,
  `extension_boundaries`, `actor_timing_qualification`, the
  `failure_boundaries` suite and the `runner_c_worker_harness` suite: 72 pass
  in run `20261107T235258Z_959443dc` (`host02-named-02`); `native_pause`
  failed as the intentionally failing applicability gate on this equipment.
- Default battery: 222 of 222 pass with no skips, harness errors or sleep
  overlap, run `20261107T235640Z_cc37a4a7` (`host02-default-02`).
- An earlier chain against the same production source (runs `host02-unit-01`,
  `host02-named-01`, `host02-default-01`) failed one new clock control whose
  expected sample count was off by one; the control was corrected, the
  candidate rebuilt clean, and every case rerun above.

## Results

Run `20261108T002327Z_715b1dc3` in `tests/out/runs/worker-wait-host02-compare-01`
(gitignored, local checkout only). Announced quiet window of 240 s, of which
75.3 s were used; AC power throughout, low power mode off, load average 2.9 to
3.8 at trial starts, no system sleep, no observer overlap, three counted clock
inversions of at most 2.2 µs, no excluded trials. 120 trials accepted, 60
matched pairs, none unpaired; five pairs in each of the twelve cell and regime
groups. Actual gaps: `rapid` 13.4 to 17.8 ms, `idle` 1000.4 to 1005.4 ms.
Calibration credited the instrument at a 1458 ns endpoint term and 166 ns
alignment bound. The staged instrumented builds, which are not production
bytes, were host `e9145c52…` and worker `aa754261…` for the baseline and host
`83be4c42…` and worker `109b3e5d…` for the candidate; no host patch was skipped
on either side.

### Shorter held intervals in the actor form (the gated claim)

Baseline minus candidate per pair, microseconds, with the frozen verdict
`improves_beyond_uncertainty_in_every_pair` and the stricter spread verdict.

| Regime | `detection_total`, five pairs | Verdicts | Baseline median (range) | Candidate median (range) |
| --- | --- | --- | --- | --- |
| idle | 8667, 7226, 9970, 6325, 6098 | yes / yes | 8436 (7338 to 11149) | 1210 (1090 to 1240) |
| rapid | 8679, 6168, 8662, 4914, 4898 | yes / yes | 7427 (4913 to 9922) | 1240 (−1 to 1259) |

The combined uncertainty per pair was 103 to 121 µs. On the baseline, every
arrival that the host's first sample after an activation missed, every
completion after a release and every recipient acknowledgement after an
inbound commit cost one 1.25 ms sleep: four to eight execution sleeps per
trial and, in six trials, one or two recipient sleeps. The candidate's host made two execution sleeps
per trial (one in one rapid trial) and no recipient sleep; 112 of its 120
post-publication detections in A2 ended 2.5 to 12.2 µs after the publication.
The eight exceptions are the completion of the second actor's second visit
(phase 2), whose attempts outlast the 100 µs budget in eight of ten trials:
there the host spent the budget and then slept as before, so that component
is 71 to 233 µs longer than the baseline's in seven pairs
(`worsens_beyond_spread_in_any_pair`, not every pair) and 1.1 ms shorter in
the two rapid pairs where the completion fell inside the budget. The final
visit's completion store has no stamp of its own; its proxy, the terminal
publication, follows the store, so the candidate's observation precedes the
proxy by 15 to 29 µs and that component is reported negative.

The two actors' wait passes per trial (activation, release and exchange) fell
from 101,468 to 145,530 on the baseline to 70,467 to 90,903 on the candidate,
23,568 to 59,493 fewer in every pair. An actor's release wait after an arrival
the candidate detected by re-sampling fell from about 4,800 to 5,300 passes
to 14 to 46.

### Later ordinary phase (O2P phase 1)

| Regime | Arrival to observation, five pairs | Verdicts | Held total, five pairs | Verdicts |
| --- | --- | --- | --- | --- |
| idle | −113, 2408, −76, 2410, 2409 | no / no | −500, 2196, −139, 2562, 2431 | no / no |
| rapid | 2387, 2436, 2247, 2434, 2424 | yes / yes | 2380, 2813, 1956, 2645, 2490 | yes / yes |

The claim holds in `rapid` and is not established in `idle`. After the phase 0
release the worker performs phase 0's attempts, publishes completion and
arrives at phase 1. In every rapid pair and in idle pairs 1, 3 and 4 this
happened inside the 100 µs budget and the candidate observed the arrival 3.1
to 4.3 µs after it, where the baseline's first sample missed it and one 2 ms
sleep followed (2250 to 2440 µs). In idle pairs 0 and 2 the arrival came after
the budget; the host spent it, slept as before, and observed the arrival 113
and 76 µs later than the baseline did. The worker's phase 1 release-wait
passes fell from 15,494 to 17,515 to 6,097 to 7,735 in every rapid pair and in
the three idle pairs the re-sample caught. Whether the budget covers a later
phase's arrival depends on how long the previous phase's attempts take, a
property of the specimen rather than of the host.

### No resolved regression, response and first-phase arrival

- No quantity in any cell or regime worsened beyond spread in every pair.
  `worsens_beyond_spread_in_any_pair` fired in isolated pairs: the A2 phase 2
  completion above in both regimes, O2P idle phase 1 arrival, first-phase
  arrival in O64 idle and O256 rapid where the bimodal 2.5 ms detection fell on
  different sides in one pair, and whole request in A2 idle and O0 rapid.
- First-phase ordinary arrival, which the candidate does not change, is
  unchanged: differences of about 0 or ±2.5 ms in every ordinary cell, the
  baseline's first-sample-or-one-sleep detection on both sides. Single-phase
  cells re-sample nothing, since their only release is the last.
- Response: release-to-acknowledgement and activation response, candidate
  upper bound minus baseline lower bound, 0.1 to 5.1 µs across every cell and
  phase against the 2 ms bound; all 32 bounds credited.

### Added host busy time

Reported, not gated. The host re-samples at most once per publication for at
most 100 µs. In A2, 112 of 120 re-samples ended within 12.2 µs and eight spent
the whole budget, at most about 0.26 ms of added busy time per trial by these
counts. In O2P the single re-sample per trial spent its whole budget in the
two idle pairs above, 100 µs each without benefit. Single-phase ordinary cells
added none.

### Whole request

Baseline minus candidate per pair, milliseconds.

| Cell | idle, five pairs | rapid, five pairs |
| --- | --- | --- |
| A2 | −3.1, −0.4, −4.2, −13.9, −5.9 | 2.2, −9.3, −2.4, −7.2, −0.1 |
| O2P | −0.9, 0.9, −1.9, 6.9, −0.8 | 4.1, 3.8, 2.5, 1.8, 6.0 |

The actor form is slower on the candidate in nine of ten pairs, by 0.1 to
13.9 ms, beyond spread in one idle pair and not in every pair, so the frozen
rule does not call it resolved. The cause is identified. After the last
completion the host stores the exit request and waits for the worker in
`finishCleanup` with a 10 ms poll, 12.5 ms as slept on this equipment. The
baseline reached that wait after its final 1.25 ms detection sleep, by which
time the worker had exited: no grace sleep in any of its ten trials, the worker
reaped on the first grace sample. The candidate reaches the wait within
microseconds of the completion, before the worker exits, and sleeps once in
every trial, 10.5 to 12.5 ms. Its 4.9 to 10.0 ms of shorter detection is thus
converted into one grace sleep. O2P rapid, the other group where the candidate
acts, is faster in all five pairs by 1.8 to 6.0 ms against a 5.7 ms
improvement threshold, so not beyond spread in every pair. Every other
ordinary pair lies within spread in both directions, including one O0 idle
pair 29 ms slower on the candidate against a 37 ms spread.

### Decision

Blocked on the tradeoff decision the plan requires before accepting a
candidate that increases whole-request latency. The gated claim holds in every
pair of both regimes; the later-ordinary-phase claim holds in `rapid` and is
not established in `idle`; no regression resolves under the frozen rule; every
response bound is credited. But on this equipment the candidate makes the
actor form slower end to end in nine of ten pairs, through the worker exit
grace poll that its prompt detection of the last completion now reaches before
the worker exits. The candidate is not integrated into `main`; the worktree,
its signed build and the run are retained. The owner's options, with the
coordinator's recommendation, are written into the plan's branch 2 as a
course of action and summarized here:

1. Recommended: evaluate the exposed grace poll as one further host candidate,
   `HOST-03`, beyond the plan's two-nomination cap, compared together with
   `HOST-02` against the HOST-01 baseline, and decide both on that evidence.
   The worker's readiness pipe stays open on its side until exit while the
   host closes its read end after the byte, so a hangup wait on that pipe
   under the same 1 s grace allowance is one mechanism to examine; attempt
   children must not inherit the descriptor. Cost: one more candidate cycle
   and one quiet window of about four minutes.
2. Accept `HOST-02` as it stands, with the tradeoff written: shorter held
   intervals and fewer host wakes in the actor form, actor-form requests 0.1 to
   13.9 ms slower until the grace wait changes.
3. Reject `HOST-02` and carry both the re-sample and the grace poll to the
   outflow for later work.

## Revisions

### Revision 1, before the comparison measurement

The frozen reader, `e2cc5e07…` at `3c193f5e`, raised an index error on the
comparison's `detection_total` series, whose name carries no phase prefix, in
its response-bound and wait filters. Commit `955c149d` changed the two splits
to `rpartition` so an unprefixed name passes through; no verdict, threshold,
exclusion or pairing rule changed. The comparison ran with that reader,
`ca106339…`; the driver, host patch set, worker build and stamp worker hashes
are as frozen.

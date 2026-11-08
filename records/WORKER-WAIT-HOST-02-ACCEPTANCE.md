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

Pending the comparison window.

## Revisions

None yet.

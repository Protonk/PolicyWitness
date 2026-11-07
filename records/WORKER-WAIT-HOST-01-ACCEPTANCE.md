# HOST-01 acceptance: readiness-driven ready-byte wait

Candidate of branch 2 of the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md),
nominated by the [pilot](WORKER-WAIT-PILOT.md). This record is committed as
the candidate opens; the comparison protocol below is frozen before any
comparison measurement, and later additions are recorded as revisions. Raw
evidence under `tests/out/` is gitignored and available only in the local
checkout.

## Candidate

The host waits for the worker's pre-apply ready byte by reading the ready
pipe without blocking and, when nothing has arrived, sleeping for the smaller
of 10 ms and the remaining allowance (`ActorSession.swift`, the readiness
loop over `HostWaitClock.expiredAfterSleeping`). The pilot found that in every
ordinary trial the worker became ready, applied its policy and arrived at its
first phase inside that one sleep, which lasted 12.5 ms for a requested 10 ms,
so the worker spun for 5.6 to 8.1 ms before the host first looked.

The candidate replaces the sleep with a bounded wait for readability of the
pipe: `HostWaitClock.expiredAfterWaiting(readable:)`, which charges the same
allowance, bounds each wait by the smaller of the poll period and the
remaining allowance, treats an interrupted or early return as one more pass,
and spends only the fallback allowance in nominal waits when the clock fails
or regresses. The nonblocking read stays first in every pass, so a byte that
arrives as the allowance runs out is still received. The `ready_wait` record
keeps its budget, elapsed time, stop reason and native errno. The wait call is
injectable through `ChildProcessCalls` like the sleep it replaces; production
uses `poll(2)` on the pipe. No worker wait, release store or eligibility rule
changes. No new descriptor, thread or registration is created: the pipe
already exists and the call blocks the same thread that slept before.

## Identities

- Baseline source: `6b5b2d40` on `main`; production sources unchanged since
  `ce6e35d2`; worker identity `160149e86953317fc6e4a24ce5ed79ab5ccd16311bb01da5a8ad76e5ccebc2cf`.
  Baseline app: the distribution build of that source in the main checkout.
- Candidate source: commit `df85ebef` on branch `wait/host-01` in the
  worktree `PolicyWitness-wait-host01`, clean; worker identity
  `a729571df02255983f5bf8e76883a7fb94166f6404cb869780e86997c4e57894`. Candidate
  app: its distribution build (provenance commit `df85ebef`, dirty false);
  host `4ef877ea…`, worker `fef3a811…`.
- Readers and fixtures, main checkout at `451e2124`, used for both sides:
  pilot reader version 5 `34071eb5…`, driver `9027e742…`, clock-pair reader
  `6bdf2567…`, host patch set `9645cdcd…`, recorder `6e9885e4…`, worker build
  `aab37da3…`, stamp worker `5bc7937e…`, page header `a63b0f68…`, clock pair
  `19d8b521…`. The candidate side's stamped host and worker are built from the
  candidate tree with this patch set; its optional readiness-wait patch applies
  on the candidate only (confirmed in the dry run `20261107T213500Z_887fdc65`,
  where the baseline side skipped it and the candidate side applied it). No
  CPU reader is used: the candidate changes no held-worker mechanism and makes
  no CPU claim.

## Workloads and trials

The six pilot cells (O1, O64, O256, O0, O2P, A2) in both pacing regimes. Five
matched baseline/candidate pairs per cell and regime, alternating order per
repetition, both apps staged as instrumented builds under one cleanup rule
(the generation-checked host exit event). Conditions, pacing ranges, exclusions,
watchdog and the resolution gate are the pilot's, with the pilot's
calibration pair run first inside the window. Planned window: one announced
quiet window of about four minutes.

## Claims and required observations

| Claim | Observation |
| --- | --- |
| Shorter held interval | Per pair: the arrival-to-first-sample component and the held total, both forms, plus worker release-wait passes; complete query and attempt evidence from the envelope validation of every trial. Accepted only if the candidate's value is below the baseline's by more than the sum of both uncertainties in every pair of every ordinary cell, and no actor-form pair worsens beyond uncertainty. |
| Fewer host wakes | Count and duration of readiness-wait sleeps or waits per trial from the host's sleep registers and events, both sides; reported, not required. |
| Response | Release-to-acknowledgement and activation response, candidate upper bound against baseline lower bound, at most 2 ms worse; expected unchanged since no worker wait changes. |
| Whole request | Per-pair whole-request latency, reported; a resolved increase beyond the trial spread requires a written tradeoff decision before acceptance. |
| Not claimed | CPU, energy, memory and scheduling. The readiness wait precedes the hold and the candidate changes no held mechanism. |

## Verification before comparison

In the candidate worktree against its signed build: `runner_unit` with the new
clock controls, `runner_abi_layout`, `source_drift`, `runner_c_worker_harness`,
`failure_boundaries`, `witness_contract/phases`,
`witness_contract/attempt_effects_wait_for_collection`, the actor cases,
`witness_contract/order_barrier_mutations`, and the default battery. The
held-footprint fixture is not applicable: it measures CPU during holds the
candidate does not change. Regenerated worker identity and limits account
(`worker_ready_wait` behavior) are part of the candidate.

## Verification results

Candidate worktree, against its signed build, before the comparison:

- `runner_unit` (11 cases, including the four opt-in mutation cases; 559 of
  559 core unit assertions), `runner_abi_layout/c_swift_layout_agreement` and
  `source_drift` (9 cases): 21 of 21 pass, runs `host01-unit-01` and
  `host01-unit-02`.
- `witness_contract/order_barrier_mutations`, `phases`,
  `attempt_effects_wait_for_collection`, `actor_compositions`,
  `extension_boundaries`, the `failure_boundaries` suite and the
  `runner_c_worker_harness` suite: 70 pass in run `20261107T212100Z_79d318f6`
  (`host01-mutations-01`); `native_pause` failed as the intentionally failing
  applicability gate on this equipment, and `exec_control_states` was unrun
  there because the pytest family was not yet provisioned in the worktree.
- Default battery in the candidate worktree against the candidate build: 222 of
  222 cases pass with no skips, harness errors or sleep overlap, run
  `20261107T212517Z_13c8c342` (`host01-default-01`); the pytest family ran
  after its target was provisioned from the main checkout's identical target.
  Verification before comparison is complete; the comparison window is the
  next step.

## Results

Run `20261107T220331Z_2be0f17e` in `tests/out/runs/worker-wait-host01-compare-01`
(gitignored, local checkout only). Announced quiet window, battery power at 82
percent throughout, low power mode off, no system sleep, no observer overlap,
one counted clock inversion of 0.9 µs. 120 trials accepted, 60 matched pairs,
none unpaired; five pairs in each of the twelve cell and regime groups. Actual
gaps: `rapid` 13.4 to 26.3 ms, `idle` 1000.3 to 1005.5 ms. Calibration
credited the instrument at 333 ns endpoint term and 83 ns alignment bound.

### Shorter held interval (the claim)

Baseline minus candidate per pair, microseconds, with the frozen verdict
`improves_beyond_uncertainty_in_every_pair` and the stricter spread verdict.

| Cell, regime | Arrival to first host sample, five pairs | Verdicts | Held total, five pairs | Verdicts |
| --- | --- | --- | --- | --- |
| O1 idle | 2696, 2966, 2240, 2862, 5147 | yes / no | 2479, 3079, 2872, 2843, 4610 | yes / yes |
| O1 rapid | 3209, 5179, 5243, 3266, 7601 | yes / yes | 3064, 5124, 5257, 3427, 8116 | yes / yes |
| O64 idle | 3066, 5116, 5418, 754, 5616 | yes / no | 3160, 5645, 5032, 408, 5424 | yes / no |
| O64 rapid | 5187, 5178, 2827, 7837, 5059 | yes / yes | 5672, 4472, 2878, 7793, 5175 | yes / no |
| O256 idle | 3602, 6174, 3112, 3076, 5668 | yes / yes | 3047, 3293, 3837, 3338, 5876 | yes / yes |
| O256 rapid | 4238, 7710, 7709, 5193, 2842 | yes / yes | 4346, 8274, 7567, 5175, 2795 | yes / no |
| O0 idle | 3086, 5531, 5488, 4123, 680 | yes / no | 3087, 5524, 5438, 4122, 681 | yes / no |
| O0 rapid | 5192, 3142, 7625, 6626, 5236 | yes / yes | 5194, 3207, 7594, 6599, 5244 | yes / yes |
| O2P idle, phase 0 | 5347, 3764, 2886, 2935, 4792 | yes / yes | 5062, 3903, 2475, 3056, 5046 | yes / no |
| O2P rapid, phase 0 | 7470, 5216, 3021, 4526, 2866 | yes / yes | 7504, 5245, 3011, 3296, 2787 | yes / no |

Every pair of every ordinary cell and regime improved beyond the instrument
uncertainty (1.3 to 1.8 µs) for both named components, and the worker made
fewer release-wait passes in every pair (7,663 to 13,807 fewer in O1 idle).
The improvement is smaller than the pilot's readiness share because the
candidate's first arrival is now detected by the 2 ms sentinel poll: its
arrival-to-observation values spread over about 2.5 ms (0 to 2.5 ms), which
is why the stricter spread verdict is mixed. The candidate's readiness wait
ended at the byte: one wait of 4.6 to 8.1 ms (shorter after a rapid launch,
longer after an idle gap, since the worker's compile and readiness take
longer there) against the baseline's one sleep of 12.5 ms (10.0 to 12.5 ms).

### Actor form, response and whole request

- A2: no quantity worsened beyond spread in every pair, in either regime. The
  any-pair spread verdict fired where a 1.25 ms polled detection fell on
  different sides of its bimodal distribution in one pair, as the null
  control predicted; those are not resolved regressions. The subject's parked
  activation wait made 19 to 81 fewer passes per pair in its first two visits.
  Whole request in A2 idle improved beyond spread in every pair, by 13.3 to
  19.8 ms, from the two actors' shorter readiness waits during setup; in A2
  rapid four pairs improved by 17 to 22 ms and one pair was 65 ms slower on
  the candidate, a single-trial excursion outside both spreads that does not
  resolve in every pair.
- Response: release-to-acknowledgement and activation response, candidate
  upper bound minus baseline lower bound, 0.04 to 1.4 µs across every cell and
  phase, against the 2 ms bound; all credited.
- Ordinary whole request: improved in most pairs by 1 to 9 ms; O256 idle had
  two pairs 13 to 14 ms slower on the candidate against spreads of 12 and
  24 ms; no cell worsened in every pair.
- Fewer host wakes: the readiness wait makes one wake on both sides, but the
  candidate's wake is the byte's arrival rather than a 10 ms timer.

### Decision

Accepted. The frozen improvement criterion holds in all sixty ordinary pairs,
no resolved regression appears in the actor form or in whole-request latency,
and every response bound is credited. The candidate is integrated into `main`
with its tests and documentation; the next baseline for any later candidate
includes it.

## Revisions

### Revision 1, before any comparison measurement

A null comparison of the baseline app against itself (run
`20261107T211415Z_022b0097`, `tests/out/runs/worker-wait-compare-null-01`,
two repetitions, dry run) showed that polled host detections vary between
trials by 5 µs to 1.26 ms while the instrument uncertainty is about 1.3 µs,
so the frozen regression clause "no actor-form pair worsens beyond
uncertainty" would fail for identical bytes. The clause is replaced; the
improvement claim is unchanged.

- Improvement, as frozen: `improves_beyond_uncertainty_in_every_pair` for the
  arrival-to-observation component and the held total in every ordinary cell
  and both regimes, with the stricter `improves_beyond_spread_in_every_pair`
  reported beside it.
- Resolved regression, actor form and whole request: a quantity worsens in a
  resolved way only when `worsens_beyond_spread_in_every_pair` holds, that is
  the candidate exceeds the baseline by more than the baseline group's
  trial spread plus both instrument uncertainties in every required pair.
  Such a result requires the written tradeoff decision the plan names before
  acceptance. `worsens_beyond_spread_in_any_pair` and the instrument-only
  verdict are reported, not gating, because the null control met them with
  identical bytes.
- Response bound: unchanged.
- Reader: the comparison mode's matched-pair reader, version 5 or later, with
  the five verdicts above; hashes recorded at freeze.

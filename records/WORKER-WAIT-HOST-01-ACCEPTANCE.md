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
- Candidate source: branch `wait/host-01` in the worktree
  `PolicyWitness-wait-host01`; commit, worker identity and build receipt are
  recorded under Revisions when the candidate is frozen.
- Readers and fixtures: the pilot's timestamp reader and fixtures at the main
  checkout's committed versions, used for both sides; their hashes are recorded
  at freeze. No CPU reader is used: the candidate changes no held-worker
  mechanism and makes no CPU claim.

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

## Results

Pending.

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

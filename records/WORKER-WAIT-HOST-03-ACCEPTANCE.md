# HOST-03 acceptance: the worker exit grace wait ends at the worker's exit

Third candidate of branch 2 of the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md),
admitted beyond the two-nomination cap by the owner on 2026-11-07 after the
[HOST-02 comparison](WORKER-WAIT-HOST-02-ACCEPTANCE.md) showed the delay it
addresses. Committed before any comparison measurement, after the candidate
was implemented, reviewed and verified; the protocol below is frozen before
the comparison, and later changes are recorded as revisions. Raw evidence under `tests/out/` is gitignored and available only in
the local checkout.

## Candidate

After the exit request, `ActorSession.finishCleanup` samples `waitpid` with
`WNOHANG` and, when the worker is still running, sleeps 10 ms (12.5 ms as slept
on this equipment) before the next sample, under the 1 s exit grace allowance.
HOST-02's prompt detection of the last completion reaches that wait before the
worker has exited: in HOST-02's A2 trials the worker was still running 26 to
54 µs after its terminal publication, and in the HOST-01 baseline's trials it
had exited by 1.28 to 2.60 ms (the exit itself has no stamp), so HOST-02 slept
once per actor-form request. The HOST-01 baseline sleeps there in three of
five O256 idle trials.

After a received readiness byte the candidate keeps the readiness pipe's read
end until cleanup and waits on it instead of sleeping: the worker never closes
its write end and its exec attempts spawn with every other descriptor closed,
so the pipe hangs up when the worker exits by any cause. Between `waitpid`
samples the host polls that descriptor for at most the smaller of 10 ms and
the remaining allowance, rounded up to whole milliseconds
(`HostWaitClock.expiredAfterWaiting(exit:)`, charged like a sleep). A hangup
is followed by the next sample; if the worker is not yet reapable, at most ten
settle sleeps of 100 µs precede a return to the 10 ms poll. When the readiness
byte was not received the read end is closed as before and the grace uses the
10 ms poll from its first wait; a descriptor that cannot inform the wait
(`POLLNVAL`, `POLLERR`, or a `poll` failure other than `EINTR`) does the same
after one extra sample pass, with up to one poll period of nominal fallback
allowance charged for the unusable wait. Decision order, allowance, reap,
termination, EINTR and ECHILD paths, the acknowledgement reconciliation and
every evidence field are unchanged; no thread, descriptor or registration is
added. The candidate includes HOST-02's two commits (`d9097c7a`, `628a1ccc`);
HOST-02 stays blocked on its own record until this comparison decides both.

On this machine a hangup wake and a kqueue `NOTE_EXIT` wake both arrive about
157 µs (median) after the child's pre-exit stamp; the hangup precedes
reapability in 3 to 7 percent of wakes by a median of 4 µs (worst 187 µs);
registering `EVFILT_PROC` on an exited, unreaped child fails with `ESRCH`
(`.tmp/worker-wait/reports/exit-notify/`, 3000 iterations per mode and 600
for the registration test, local checkout only). The pipe serves without a new descriptor, so the kqueue
variant was not built.

## Identities

- Baseline source: `fc089ef7` on `main` (HOST-01 integrated); production
  source unchanged through `000df771`, the main commit the readers come from;
  worker identity
  `a729571df02255983f5bf8e76883a7fb94166f6404cb869780e86997c4e57894`. Baseline
  app: the distribution build of that source in the main checkout, provenance
  commit `fc089ef7`, dirty false, the same app the HOST-02 comparison used
  (host `3ad59b9f…`, worker `972df0de…`); its verification is recorded in the
  HOST-02 record.
- Candidate source: commit `50cd7695` on branch `wait/host-03` in the
  worktree `PolicyWitness-wait-host03`, clean, including HOST-02's two
  commits; worker identity
  `57dbfd28a58849ff7526aa79d21cfce87dd5b165b408746115268fb363c6d363`. Candidate
  app: its distribution build (provenance commit `50cd7695`, dirty false);
  host `65e6e27e…`, worker `94f72970…`.
- Readers and fixtures, main checkout at `000df771`, used for both sides:
  pilot reader version 7 `480f865c…`, its controls `db22559a…` and wrapper
  `8662d460…`, driver `9027e742…` (unchanged since comparison mode was added, as in the
  HOST-02 record), opt-in wrapper
  `1ca9458f…`, host patch set `9b1abd40…` (its exit-wait patch applies to the
  candidate tree and is recorded as skipped on the baseline tree; the grace
  program points apply to both), `HostStamps.swift` `df37674a…`, worker build
  `aab37da3…`, stamp worker `5bc7937e…`, stamp page header `a63b0f68…`, clock
  pair `19d8b521…`. No CPU reader.

## Workloads and trials

The six pilot cells in both regimes, five matched pairs per cell and regime,
alternating order per repetition, both apps staged as instrumented builds under
one cleanup rule, calibration first, pilot conditions and exclusions; one
announced quiet window of about four minutes.

## Claims and required observations

| Claim | Observation |
| --- | --- |
| Shorter held intervals in the actor form (HOST-02's claim, re-established with HOST-03 included) | Per trial `detection_total`, below the baseline's by more than the sum of both uncertainties in every pair of A2 in both regimes (`improves_beyond_uncertainty_in_every_pair`); the spread verdict reported. |
| The exit grace wait ends at the worker's exit | In every accepted candidate trial of every cell: `grace_unusable` is 0 (the pipe informed every wait) and `grace_timeouts` is 0, where a timed-out exit wait, a plain key-5 sleep requested longer than 100 µs and any wait past the 64 recorded pairs each count as a timeout. One case is declared in advance: a trial with `grace_timeouts` of exactly 1 and `grace_notified` of at least 1 is a worker exit longer than one poll period, not a failure of the wait, and is reported with its `exit_request_to_reap`; a trial with a timeout and no notification fails the claim, and so does a trial whose grace counts are unavailable (the group aggregates' `unavailable` must be 0). The 100 µs settle sleeps that follow a notification before the child is reapable are counted apart (`grace_settle_sleeps`) and reported; the code bounds them at ten per notification, so per trial `grace_settle_sleeps` is at most ten times `grace_notified`, read in the decomposition rows. Every candidate actor's grace ends reaped: `grace_stop_code` 1 for every actor row. Per actor, `terminal_to_exit_request`, `exit_request_to_reap` and `grace_wait` are reported for both apps. |
| Whole request in the actor form | Baseline minus candidate per pair, per regime (five A2 pairs each), read from each pairs entry's `direction` counts (faster, slower, equal by the sign of the difference). Required in each regime: the candidate is not slower in four or more of the five pairs, the signature HOST-02 alone produced (five of five idle, four of five rapid); identical apps produce four or more slower with probability 18.75 percent per regime, so this is a guard against that regression returning, not a benefit claim. Reported per regime: faster in all five pairs is stated as the whole-request improvement in that regime (3.1 percent for identical apps); fewer leaves it unresolved; `improves_beyond_spread_in_every_pair` and `worsens_beyond_spread_in_every_pair` beside it. Whole request carries no instrument uncertainty, and its trial-to-trial spread in HOST-02's run (4.3 to 10.5 ms) is about the size of the expected gain, so the direction count is the rule here, a declared departure from the beyond-uncertainty standard that governs the stamped components. Fewer than five established pairs in a regime leaves the rule undecided and the candidate not accepted. |
| No resolved regression | No quantity, in any cell, worsens beyond spread in every pair (`worsens_beyond_spread_in_every_pair`); a resolved increase needs a written tradeoff decision before acceptance. First-phase ordinary arrival, which the candidate does not change, is reported. |
| Response | Release-to-acknowledgement and activation response, candidate upper bound against baseline lower bound, within 2 ms, credited. |
| Added host resources and busy time | No new descriptor, registration or thread; after a received readiness byte the pipe's read end lives until cleanup. HOST-03's own wake activity is charged: each grace wait adds one poll return per notification or timeout and at most ten settle sleeps per notification, reported per trial as `grace_notified`, `grace_timeouts` and `grace_settle_sleeps`. HOST-02's re-sampling busy time reported as in its record. O2P phase 1 carried as reported in the HOST-02 record, not gated. |

Decision rule, frozen:

- Accept HOST-02 and HOST-03 together, and integrate both, when the
  held-interval claim holds in every A2 pair of both regimes, the grace claim
  holds in every candidate trial, the whole-request guard holds in both
  regimes, no quantity worsens beyond spread in every pair, and every response
  bound is credited.
- If the grace claim fails, HOST-03 is rejected and HOST-02 returns to its
  blocked state with the two options the plan names for the owner.
- If the grace claim holds but the whole-request guard fails in either regime,
  the latency cost is not the grace poll: neither candidate is accepted, and
  the owner decides between rejecting both and a separate comparison of
  HOST-03 alone (which would also remove the baseline's O256 idle grace
  sleeps), with the coordinator's recommendation.
- If the held-interval claim fails, a quantity worsens beyond spread in every
  pair, or a response bound is not credited, neither candidate is accepted;
  the record states what failed, and the written tradeoff decision the plan
  requires for a resolved increase is the owner's.

## Verification before comparison

In the candidate worktree against its signed build: `runner_unit` with the new
grace-wait controls, `runner_abi_layout`, `source_drift`,
`runner_c_worker_harness`, `failure_boundaries`, `witness_contract/phases`,
`attempt_effects_wait_for_collection`, `actor_compositions`,
`extension_boundaries`, `order_barrier_mutations`, `actor_timing_qualification`
(default) and the default battery. Regenerated worker identity, limits account
and architecture account are part of the candidate. On `main`:
`witness_contract/worker_wait_pilot_controls` with the reader's new controls,
and a re-read of the HOST-02 comparison artifacts with the new reader showing
every frozen verdict unchanged.

## Verification results

Candidate worktree, against its signed build, before the comparison:

- First implementation (`ce80b019`): `runner_unit`, `runner_abi_layout` and
  `source_drift` failed three cases in run `20261108T011951Z_34cd0dc1`
  (`host03-unit-01`), all on one compile error in the implementer's new
  lifecycle tests, corrected before the commit; 21 of 21 pass in
  `20261108T012635Z_de9bfa96` (`host03-unit-02`). Two independent reviews then
  found, by reading the resilience case's expectation, that keeping the
  readiness pipe's read end open after a readiness deadline or transfer
  failure would let a late ready byte succeed instead of meeting `EPIPE`,
  changing the worker's published readiness evidence; the read end is now
  kept only after a received byte (`50cd7695`).
- On the fix's source before its commit, against a build of the
  then-uncommitted tree whose production source is identical to `50cd7695`
  (host `bdb96fbf…`, worker `91187af2…`): `runner_unit` (with the exit-wait,
  settle, timed-out, unusable, linger and two-actor controls),
  `runner_abi_layout` and `source_drift`: 21 of 21 pass, run
  `20261108T014239Z_b66dff48` (`host03-unit-fix-01`);
  `runner_ready_byte_resilience/slow_compile_ready_byte_survives_sigpipe`,
  `runner_exec_inheritance/launch_inventory`,
  `witness_contract/order_barrier_mutations`, `phases`,
  `attempt_effects_wait_for_collection`, `actor_compositions`,
  `extension_boundaries`, `actor_timing_qualification`, the
  `failure_boundaries` suite and the `runner_c_worker_harness` suite: 75 pass
  in `20261108T014920Z_cd9e1fe0` (`host03-named-fix-01`), `native_pause`
  failing as the intentionally failing applicability gate on this equipment.
- On the candidate app (provenance `50cd7695`, host `65e6e27e…`, worker
  `94f72970…`): default battery 222 of 222 in `20261108T015435Z_b0452eac`
  (`host03-default-fix-01`) and again 222 of 222 in
  `20261108T021449Z_87458c1f` (`host03-default-01`); the named selection
  without the resilience and inheritance cases, 72 pass plus the
  `native_pause` gate in `20261108T021105Z_65d6ce33` (`host03-named-01`);
  `runner_unit` with its opt-in mutation cases and the
  `runner_exec_inheritance` suite (`launch_inventory`, `contaminated_worker`,
  `cli`, `closed_worker_stderr`, `mutation_controls`): 16 of 16 pass in
  `20261108T025853Z_d048a539` (`host03-unit-final-01`). No case in any run
  overlapped system sleep.

Main checkout (readers):

- `witness_contract/worker_wait_pilot_controls`: pass in
  `20261108T012001Z_c117847c`, `20261108T012627Z_59113999` and
  `20261108T013258Z_24fdda9a` on the instrument commits. After the
  settle-sleep separation, `20261108T023654Z_2937d9b5`,
  `20261108T023715Z_7702a89d` and `20261108T023746Z_fc0697fe`
  (`host03-settle-controls-01` to `-03`) failed on the controls' stale
  expectations for the new count (a three-value tuple, a group expectation
  without it, the version pin), corrected in turn; `20261108T023800Z_e441ce70`
  (`-04`) passes with 74 constructed faults rejected after 51 accepted
  receipts. `source_drift`: 9 of 9 in `20261108T023143Z_5ace0a83` on the tree
  before that commit and 9 of 9 in `20261108T025853Z_b870d653`
  (`host03-main-drift-02`) on `000df771`. Comparison dry run with the
  baseline app on both sides, new patch set and reader: pass in
  `20261108T012026Z_0964f1e1`.
- Re-read of the HOST-02 comparison artifacts with reader version 7: all 466
  frozen pair-verdict series and 32 response bounds equal to the committed
  summary, 28 series added (the per-actor exit intervals), none missing.
- Comparison dry run, baseline app against the candidate app, one repetition
  of every cell and regime: pass in `20261108T023851Z_30e16f5e`
  (`host03-compare-dryrun-01`), 24 trials accepted, reader version 7, the
  exit-wait patch applied to the candidate tree and recorded as skipped on the
  baseline tree, both trees clean at the commits above. The candidate's three
  grace waits (A2 in both regimes and O0 idle) each ended by notification 195
  to 283 µs after the exit request and were each followed by one settle sleep
  of about 130 µs before the reap, so the production worker's hangup precedes
  its reapability more often than the microbenchmark's trivial child did; no
  wait timed out. The baseline made no grace wait in that run. Mechanics
  only; no trial of a dry run is evidence.

## Results

Run `20261108T033212Z_afb24188` in `tests/out/runs/worker-wait-host03-compare-01`
(gitignored, local checkout only). Announced quiet window of 240 s, of which
73.7 s were used; AC power at 86 to 87 percent and charging, low power mode
off, load average 2.7 to 5.2 at trial starts (the candidate's verification
reruns had finished minutes before), no system sleep, no observer overlap, one
counted clock inversion of 84 ns, no excluded trials. 120 trials accepted, 60
matched pairs, none unpaired; five pairs in each of the twelve cell and regime
groups. Actual gaps: `rapid` 12.8 to 20.9 ms, `idle` 1005.1 to 1005.5 ms.
Calibration credited the instrument at a 291 ns endpoint term and 83 ns
alignment bound. The staged instrumented builds, not production bytes, were
host `62e77e70…` and worker `868ce273…` for the baseline and host `c96c3d90…`
and worker `424030b4…` for the candidate; the exit-wait patch applied to the
candidate tree and was recorded as skipped on the baseline tree, both trees
clean at `b9add1fc` and `50cd7695`.

### Shorter held intervals in the actor form (claim 1)

Baseline minus candidate per pair, microseconds, with the frozen verdict and
the stricter spread verdict.

| Regime | `detection_total`, five pairs | Verdicts | Baseline median (range) | Candidate median (range) |
| --- | --- | --- | --- | --- |
| idle | 6187, 4909, 7464, 3694, 7447 | yes / yes | 6188 (4940 to 8693) | 1246 (1 to 1246) |
| rapid | 6210, 8695, 9929, 9922, 8757 | yes / yes | 9925 (6213 to 9970) | 3 (2 to 1213) |

The combined uncertainty per pair was 47 to 50 µs. Of the candidate's 112
post-publication detections in A2, 108 ended within 3.6 µs of the publication;
the other four, the phase 2 completion whose attempts outlast the re-sample
budget, in three idle trials and one rapid trial, cost the sleep as before.
The two actors made 16,156 to 67,112 fewer wait passes per pair. The host's
execution sleeps fell from four to eight per trial to one or two, and its
recipient sleeps from one or two to none. The claim holds.

### The exit grace wait ends at the worker's exit (claim 2)

In every candidate trial of every cell `grace_unusable` and `grace_timeouts`
are 0, and every actor's grace ended reaped (`grace_stop_code` 1 in all 70
candidate actor rows, as in all 70 baseline rows). In A2 the first actor's
grace made one notified wait per trial, ending 169 to 361 µs after the exit
request at the pipe's hangup, followed in two of the ten trials by one 100 µs
settle sleep before the reap; the second actor had already exited and was
reaped on its first sample on both apps. No other cell made a grace wait on
either app in this run; the baseline's O256 idle grace sleeps of the HOST-02
run did not recur. Per actor, terminal publication to reap: first actor,
baseline 1309 to 2578 µs, candidate 199 to 398 µs; second actor, baseline 1514
to 1563 µs, candidate 400 to 653 µs. The claim holds.

### Whole request in the actor form (claim 3)

Baseline minus candidate per pair, milliseconds.

| Regime | Five pairs | Direction | Baselines (ms) | Beyond spread in every pair |
| --- | --- | --- | --- | --- |
| idle | 7.0, 2.6, 1.5, 4.8, 5.6 | faster 5, slower 0 | 90.4 to 96.6 | no (threshold 3.3) |
| rapid | 4.2, 8.6, 8.9, 10.2, 7.8 | faster 5, slower 0 | 58.3 to 67.0 | no (threshold 6.3) |

The guard holds in both regimes, and the candidate is faster in every pair of
both regimes, which the frozen rule states as the whole-request improvement
in each regime. HOST-02 alone had been slower in nine of ten pairs. In the
ordinary cells, O2P rapid is faster in all five pairs by 1.9 to 3.1 ms
(threshold 5.4 ms); every other group lies within spread in both directions,
with single pairs beyond spread in O0 idle (9.8 ms slower), O0 rapid (11.5 ms
slower) and O64 idle, and none in every pair.

### Regression, response and carried observations

- `worsens_beyond_spread_in_every_pair` holds for exactly two quantities,
  `w0.exit_request_to_reap` and `w0.grace_wait` in A2, in both regimes:
  baseline 2 to 7 µs, candidate 169 to 362 µs. These are the intervals the
  candidate changes by construction. The baseline stored its exit request
  after its final 1.25 ms detection sleep (and a further sleep in nine of ten
  trials), by which time the worker had exited, so its first grace sample
  reaped; the candidate stores the request 26 to 36 µs after the terminal
  publication and waits for the exit itself. The enclosing interval, terminal
  publication to reap, fell in every pair (above), as did the whole request.
  No other quantity worsened beyond spread in every pair; the any-pair spread
  verdict fired in isolated pairs as the null control predicts.
- Response: 32 bounds, 0.08 to 0.33 µs against the 2 ms limit, all credited.
- O2P phase 1, carried from HOST-02 and not gated: arrival to observation
  and held total improved beyond uncertainty and beyond spread in every pair
  of both regimes in this run (idle 2021 to 2440 µs, rapid 2440 to 2445 µs).
  First-phase ordinary arrival is unchanged, bimodal at 0 or 2.5 ms on both
  sides.
- Added host activity: one poll return per grace wait, one settle sleep in
  two of 120 trials; HOST-02's re-sample spent its full budget in the four A2
  trials named above.

### Decision

Every gate holds except one clause as literally frozen: "no quantity, in any
cell, worsens beyond spread in every pair" fires for the two reported grace
intervals whose increase is the mechanism itself, since the host now waits for
the worker's actual exit instead of finding it already done after a longer
detection sleep. The frozen rule sends that case to the owner, so neither
candidate is integrated by this record. The coordinator's recommendation is to
accept HOST-02 and HOST-03 together: the plan's tradeoff clause names total
CPU, whole-request latency, sampled memory and peer interference, none of
which worsened; the whole request improved in every A2 pair of both regimes;
and the two flagged intervals lie inside an interval that shrank in every
pair. Pending the owner's decision.

## Revisions

None yet.

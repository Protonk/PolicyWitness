# HOST-06: first-arrival observation

This record belongs to the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md).
HOST-04 is accepted and HOST-05 closed without adoption. Production source
remains `1451c488`, native identity
`6e8e46469c1ebf0677b799ad63adac5af20be68b20902e18450c5b6e70a8a9ba`.
ARM and hint tuning remain deferred.

## Nomination and apparatus

Reader v12 separates spawn-to-ready observation, ready-observation-to-worker
post-application stamp, and that stamp to the first-arrival stamp. These are
program points, not the exact application/publication instants. Reanalysis of
`host05-inspection-diagnostic-01`, on unchanged accepted production source,
retains all 80 accepted trials: spawn-to-ready spans approximately 4.47–6.97 ms;
ready observation to the applied post-stamp spans 12.12–47.67 µs, above its
roughly 2 µs uncertainty; applied-to-arrival spans 0–0.625 µs, below its roughly
1.916 µs uncertainty. Do not call the latter fault-free or instantaneous.
The original v11 reports are preserved; this separate reanalysis is nomination,
not a comparison against a new candidate.

O0/O1 idle first-arrival observation was consistently about 3 ms after arrival.
These small/no-eligible-query workloads isolate the initial wait without a large
variable decoder interval. They are the selected performance workloads. Rapid
launches and query-dense/multiphase/actor workloads remain required controls.

Fixture events 183/184 bracket the resampling helper before fallback sleep.
An explicit export marker distinguishes no call from missing instrumentation;
missing pairs, dropped events or absent marker cannot establish zero work.
The measured span includes possible descheduling and is not process CPU.
Startup arithmetic, malformed pairs, missing-versus-zero and separation from
sleep have independent constructed controls. `host06-reader-controls-03`
passes them and all 589 runner assertions against unchanged production source.
The first two reader-control attempts failed stale expected field/version lists;
they preceded this passing run and are not credited. Old reports retain their
reader identity. Every new comparison uses v12 on both sides.

## Sole candidate and frozen decision

After a received readiness byte, before the first ordinary phase has collected,
allow one initial resampling opportunity. Use the existing 100,000 ns budget,
remaining-allowance cap, 16,384-sample cap and sticky clock-fault behavior. End
resampling on first arrival or done, then return through the ordinary checks;
resampling itself never collects, releases or attributes application. If the
window finds neither, sleep through the existing bounded fallback. Do not change
subsequent phase/actor waits, global poll periods, resources or worker IPC.
A missing readiness byte gets no new initial resampling opportunity.

Require controlled delayed application, failed application, pre-application
exit, missing/late readiness, one-use behavior, deadline, clock-fault and
sample-cap evidence, in addition to existing phase/ownership controls. The
unsandboxed lifecycle fixture establishes host decisions, not sandbox effects.
Run order-barrier mutations because this changes a wait. Native production
source changes require identity regeneration and a signed matching candidate.

Compare inspection builds of accepted source and candidate in O0, O1, O64,
O256, O2P and A2, rapid/idle, five alternating matched pairs per cell/regime:
120 trials, within an announced 240-second native window. Use 100 clock-pair
calibration trials, the 15-second watchdog and existing cleanup reserve. Freeze
exact staged identities while the gate is closed. Exclude exactly the first
execution of each staged executable; eligible actual gaps remain rapid
[0, 100 ms], idle [1000, 1250 ms]. Record AC/battery, low-power mode, competing
load and sleep without pooling changed conditions.

For **O0 idle and O1 idle**, every pair must shorten both first-arrival-to-host
observation and `p0.held_total` beyond combined uncertainty. Retain all other
pairs as controls, including contrary results. All common response obligations
must have complete evidence, bound at most 2 ms and combined uncertainty at most
0.5 ms. Report initial-resampling count and elapsed span in every ordinary
candidate trial, including zero when it did not enter; at most one initial call
is allowed. The added measured resampling span plus its uncertainty must be
smaller than the arrival-observation saving minus combined uncertainty in every
selected performance pair. This compares elapsed obligations, not total CPU.
A source time budget is not a real-time upper bound on a descheduled process.

An increase in initial resampling is expected and explicitly traded against the
larger removed initial wait under the preceding rule. Preserve any-pair spread
flags for investigation. Any other every-pair spread worsening in whole-request,
CPU, memory or peer-interference observations requires a separate written
tradeoff before adoption. No scheduling, energy or CPU benefit follows merely
from shorter elapsed holds. Missing required evidence withholds acceptance.
Do not extend samples to seek a preferred outcome. Failure closes this sole
candidate without production adoption.

Before adoption, complete the applicable signed default battery, source/ABI and
ordering checks, held-footprint checks and actor timing qualification. Larger
actor qualification gets its own announced bounded quiet window. Keep useful
negative findings and apparatus even if the candidate fails. Finalize retention
and pruning with the host round; this record is plan-specific, not permanent
behavior documentation.

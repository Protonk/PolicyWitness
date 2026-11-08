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

## Preparation and correctness evidence

The separate v12 nomination is attached under
`tests/out/runs/host06-reader-controls-03/host06-nomination/`; `source.json`
identifies the original inspection run `20261108T202647Z_be14bf79`, the attachment
run `20261108T205644Z_fafb53d6`, reader and original-report hashes. It does not
replace the original reports or relocate process ownership.

Candidate production source is `f341d37d`, native identity
`aaa8056c79c242fde5740449049246e3ed88facdc2c8efd143f6344c856da8e5`.
The signed candidate app was built there; subsequent `20acc233`, `6fd0394b`
and `101bdf70` change only fixture documentation/control code. The candidate
checkout is `/private/tmp/pw-wait-host06`.

`host06-correctness-01` failed to compile a test's optional-reap assertion;
its mutation build failure supplied no detection evidence.
`host06-correctness-02` passed ABI and ordering mutations but failed the new
apply-failure fixture assertion: it had not published the native failure record
that the production decoder requires. The corrected fixture publishes that
record before done. Its gate now advances only after the first owned polling
check, so startup scheduling cannot satisfy the no-sleep test accidentally.
`host06-correctness-03` passes all 597 runner assertions and both ordering
bypasses are detected. These controls are unsandboxed and establish decisions,
not native timing. The ABI case in `-02` remains applicable: its C header,
Swift layout, generated identity, implementation inputs and independent layout
fixtures are unchanged by the subsequent lifecycle fixture and Swift test edits.

## Prepared comparison

`host06-mechanics-01` accepted all 24 rehearsal trials, established calibration
and settled cleanup. Every ordinary trial had an observed initial-resampling
count: zero on the baseline and zero or one on the candidate. It supplies no
quantitative credit. The full comparison uses the same v12 apparatus, committed
at `273fabf9`, with candidate control source at `101bdf70`. It remains at its
gate while the following identities are committed.

| Receipt / input | SHA-256 |
| --- | --- |
| `tests/out/runs/host06-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/staged-identity-before.json` | `997d234b035e566f4b7f17e8ac5ac873502beec6cc612ad33621c615072bc7f0` |
| `tests/out/runs/host06-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/schedule.json` | `75e526659ffa8e944940c975362393e2ec3af9d853396f109250c605f6424243` |
| `tests/out/runs/host06-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/host-baseline/host-build.json` | `5687610cbeaab36915443a00b122aa8f7762828ccd5ddf01a4821d03c9bca14e` |
| `tests/out/runs/host06-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/host-candidate/host-build.json` | `bacfe3d827d9578b6852086a4aa38aacf1643be6d772c66af43456ae21b7e699` |
| `tests/suites/witness_contract/worker_wait_pilot_reader.py` | `7b4ca3fd7da794d5861cd5b877c2d400c6e64dbc552db3711d66f088d3b78635` |
| `tests/fixtures/worker_wait/host_stamps.py` | `62ddfad1902c2d7c63f48bacccdcde5e9e1bf9f436c5364b2e09f87c7efc5fe0` |
| `tests/fixtures/worker_wait/HostStamps.swift` | `243e1c92794ebef36db11f8131a1e10765d223e3a8f891d48bf5287ac3f35775` |

## Comparison result; integrated verification pending

`host06-comparison-01` accepted all 120 trials, formed all 60 pairs and credited
calibration, without exclusions, skipped/incomplete trials or unpaired members.
Cleanup settled with no staged process surviving. All 50 ordinary candidate
trials recorded exactly one initial-resampling call. All response obligations
were credited: largest finite-observation bound 2.954 µs, largest combined
uncertainty 2.662 µs.

In the ten selected O0/O1 idle pairs, first-arrival observation shortened by
2929.543–3009.666 µs and held time by 2827.042–3033.500 µs. Every pair exceeded
combined uncertainty. Added initial-resampling spans were 1.833–8.625 µs;
even their upper uncertainty bound was smaller than the corresponding saving's
lower bound in every pair. These are elapsed observations in fixture builds,
not process CPU or an energy measurement. The expected increase in initial
resampling is the predeclared tradeoff. It adds no mapping, descriptor, thread,
worker write or cross-process notification.

No other component or whole-request group worsened beyond spread in every pair.
No whole-request pair crossed its spread regression flag. Nevertheless O0 idle
repetition 4 was 1.9815 ms slower as a whole request despite a shorter held
interval; other contrary control pairs remain in the complete reader output.
Do not infer universal request speed or a cause for these differences.

Production source is integrated at `7f67e5cd`, with final fixture controls at
`952f30cf` and current-behavior documentation at `f6877809`. Acceptance remains
pending complete signed verification and the observer comparison. The signed
app's inventory and native identity, not a pristine whole-tree claim, identify
its source: the user's unrelated planning document remains modified.

Run an observer comparison of this integrated source with its unstamped
neighbor, using the same six cells, two regimes and five repetitions per side
(120 trials), inspection host flags, 100 calibration trials and an announced
240-second native window. Freeze its exact staged identities at the gate. This
adds observer-cost evidence, not more implementation pairs or another attempt
at the acceptance gate. Preserve signed app/source identity and inspect actual
capture markers, in-situ stamp costs, export spans, neighbor whole-request
observations and cleanup. Apply no fixed overhead subtraction.

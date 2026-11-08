# HOST-05: decoder work at collection

This record belongs to the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md).
HOST-04 is accepted. This investigation starts with a compiler-flavour diagnostic;
no production decoder candidate or change to shipped inspection policy is adopted.

## Foundation and first diagnostic

Accepted production source is HOST-04 (`1451c488`), with its current-behavior
account at `3d4e5f6a` and completed disposition at `9738ff41`. Native identity:
`6e8e46469c1ebf0677b799ad63adac5af20be68b20902e18450c5b6e70a8a9ba`.
The signed main app verified for HOST-04 remains the source app for both flavours.
No other production change enters this diagnostic.

The timestamp host builder now accepts the two settings supported by Meson:
inspection `-Onone -g` and optimized `-O`. It passes and records the selected
flags in the actual compiler command, generated recorder, build receipt and
trial export. The setting affects only the disposable Swift host. Worker,
validator, controller and C shim recipes remain fixed. Both instrumented and
unstamped neighbors in a run use that same host flavour; readers keep different
flavours separate. `host05-flavour-controls-01` passes the existing independent
reader/stager controls, including refusal to pool different host flavours.

First run an optimized mechanics rehearsal across O0, O1, O64 and O256 in both
rapid and idle regimes, one repetition. It is excluded from quantitative credit.
Then run the same four cells in each flavour, five repetitions per regime and
per instrumented/unstamped side: 80 scheduled trials per flavour. Each native
window is bounded at 180 seconds, with 100 clock-pair calibration trials,
a 15-second trial watchdog and the driver's cleanup reserve. The prepared gate
holds trials until exact identities are recorded and the window announced.
Compiler concurrency is at most two; no concurrent native work is scheduled.

Use the existing excluded first execution per exact staged executable and
rapid [0, 100 ms] / idle [1000, 1250 ms] actual-gap rules. Preserve every trial,
exclusion, contrary observation and power/load/sleep receipt. Require complete
declared coverage and the existing 0.5 ms instrument gate; missing information
withholds claims rather than relaxing these rules. The separate flavour blocks
are a diagnostic, not a matched implementation comparison or authority to change
the shipped build policy. Record decoder and held intervals, small/no-query
behavior, host stamp cost, export span and neighbor whole-request observations.

## Selection and acceptance of a source candidate

After the diagnostic, select at most one small source change or reject further
source work. An initial source-review possibility is repeated conversion of the
same native integer fields during structural checks and verdict construction.
That is a hypothesis, not measured savings. Freeze the selected source, artifacts,
workloads and claims before any implementation comparison.

Any candidate must preserve strict UTF-8, framing, integer/Boolean distinctions,
byte/count bounds, first-fault kind/message ordering and byte offset, step
association, unfamiliar fields/outcomes, partial results and raw lines. Decoding
and its charge remain at the current collection boundary. No preparation cache,
deferred charge, new public field or sandbox-side resource is in scope.

Adoption flavour is inspection. Compare identical compiler settings on accepted
source and candidate, five alternating matched pairs in each selected query-dense
workload/regime. Require shorter decoding and held intervals beyond uncertainty
in every named pair, with complete evidence and the common response bounds.
Small/no-eligible-query controls and whole-request costs remain required.
The reader's any-pair spread flag prompts investigation; an every-pair spread
worsening is a resolved increase requiring a written tradeoff decision. Retain
all flags and withhold universal speed, CPU, energy or coalescing claims unless
their independent observations support them.

Use existing validator framing, failure/no-reply, association, phase and runner
controls, adding only missing behavioral cases at the changed boundary. Regenerate
the worker identity for native source changes, build through the signed pipeline,
and run integrated verification under the plan's evidence-reuse rules. A negative
result closes HOST-05 without changing production source; useful apparatus and
negative findings remain available for HOST-06 and deferred work.

## Status

HOST-05 is closed without adoption. The sole source candidate failed the frozen
every-pair held-time requirement; production decoding and build policy remain
unchanged. Raw evidence stays in dispatcher-owned local output; retention is
finalized with the host round.

## Prepared inspection diagnostic

Apparatus commit `723a7d54` and reader version 11 are used on both sides.
`host05-optimized-mechanics-01` passed all 16 dry-run trials and verified actual
`-O` commands and matching optimized trial exports for both hosts; it supplies
no performance credit. The inspection diagnostic below remains at its gate
while these identities are committed.

| Receipt / input | SHA-256 |
| --- | --- |
| `tests/out/runs/host05-inspection-diagnostic-01/suites/witness_contract/worker_wait_pilot/artifacts/staged-identity-before.json` | `139ba64fc98871de4a2f0330253e9586776dcde2e0ca1a298d9d09355947c8f1` |
| `tests/out/runs/host05-inspection-diagnostic-01/suites/witness_contract/worker_wait_pilot/artifacts/schedule.json` | `05bb6c0c139be31696b23af5232aa0136d422984e76bfea3d67dd81f10cc8c14` |
| `tests/out/runs/host05-inspection-diagnostic-01/suites/witness_contract/worker_wait_pilot/artifacts/host-instrumented/host-build.json` | `73fcfde93edae8195b8eed3ec3226fa54be1a5a3a76c4a305485a4b233782b6a` |
| `tests/out/runs/host05-inspection-diagnostic-01/suites/witness_contract/worker_wait_pilot/artifacts/host-neighbor/host-build.json` | `a2469a2423dd4a538e2acc5cd537b4b3b8734f3222df45b7e27dd5f16b21cd50` |
| `tests/suites/witness_contract/worker_wait_pilot_reader.py` | `3615d6e6679d1b08d0f027c5afd7cd415dd87359ca939f695f776efe58de904c` |
| `tests/suites/witness_contract/check_worker_wait_pilot.py` | `1d52d5f6f729ea4f9e38f1799ec60d719d43eafcd7f60b0bc3f8c0c9a1d4d1e5` |
| `tests/fixtures/worker_wait/host_stamps.py` | `0cf559a72d2dde5c961c9ec9858250aa0331d02c061c7af62f1f46d250ac733e` |

Pacing prose correction: the frozen driver schedules use a rapid eligible gap
of [0, 100 ms], not the 250 ms initially transcribed here. The hashed schedules
and retained trial conditions already carry 100 ms; every credited trial met
that stricter range. No selection, exclusion or result was changed.

## Prepared optimized diagnostic

The optimized block uses the same source and reader as the inspection block.
Its exact staged identities are frozen while the measurement gate is closed.
Both host compiler receipts specify `-O`; production remains inspection.

| Receipt / input | SHA-256 |
| --- | --- |
| `tests/out/runs/host05-optimized-diagnostic-01/suites/witness_contract/worker_wait_pilot/artifacts/staged-identity-before.json` | `122040c52e0430a998142cbe5991a7102f2a411529ffb37a0bb8f8d946dab0a6` |
| `tests/out/runs/host05-optimized-diagnostic-01/suites/witness_contract/worker_wait_pilot/artifacts/schedule.json` | `caee7223532f747f7ab53580044c05b2896ed43e673d161ca78c940854626be1` |
| `tests/out/runs/host05-optimized-diagnostic-01/suites/witness_contract/worker_wait_pilot/artifacts/host-instrumented/host-build.json` | `db5dd838fd7a2dafc7f9ada9a12ca17b8640cf7debcd17341781c3d239c0653d` |
| `tests/out/runs/host05-optimized-diagnostic-01/suites/witness_contract/worker_wait_pilot/artifacts/host-neighbor/host-build.json` | `414b17b2aab6dc8f82719b9e0058f79cac082c12d7350e122f777478885292e0` |

## Diagnostic result and selected source comparison

Both diagnostic blocks accepted all 80 trials, with no exclusions, skipped or
incomplete trials, credited calibration and settled cleanup. All were on AC
power with low-power mode off. The inspection/optimized decoder medians were:

| Verdict count | Inspection rapid / idle (µs) | Optimized rapid / idle (µs) |
| --- | --- | --- |
| 1 | 96.0 / 102.9 | 62.7 / 67.3 |
| 64 | 1192.6 / 1296.0 | 821.8 / 886.3 |
| 256 | 4253.8 / 4515.9 | 2958.9 / 3136.8 |

These separately scheduled blocks establish remaining decoder cost in each
flavour, not a matched causal estimate of changing flags. The decoder interval
exceeds uncertainty in every query-bearing trial. O0 has no validator decode.
Production remains inspection. Reader v11's fixture-identity prose says
“disposable -Onone builds” even for the optimized block; the actual compiler
commands, build receipts and exported flavour establish `-O`. That prose is
not used to classify or pool trials; it will be corrected after these frozen runs.

Select one candidate: retain each native integer conversion during structural
validation and reuse it for required-field checks and verdict construction.
Keep validation order and the same `validatorInteger` conversion. A valid
allow/deny frame with all three native integer fields goes from nine conversions
(including schema) to four. This count is a source observation, not CPU savings.
The local value holds three optional integers for one frame, without a heap
cache or new cross-frame lifetime. Production adoption requires the measured
criteria below; reduced conversion count alone does not suffice.

Compare accepted HOST-04 with this candidate in inspection flavour, O0/O1/O64/
O256, rapid and idle, five alternating pairs per cell/regime (80 trials total).
The selected performance workloads are O64 and O256 in both regimes: **every
pair must shorten both `p0.decode` and `p0.held_total` beyond combined
uncertainty**. O0/O1 remain no-query/small controls. The common response and
regression rules above apply. Use a 180-second native window, the same 100-trial
calibration, pacing, warm exclusion and cleanup reserve. Do not extend sampling
or add a favorable workload after seeing the candidate comparison. A failure
of this gate rejects this sole decoder candidate and closes HOST-05.

Before comparison, build/sign the isolated candidate, run runner evidence,
ABI and affected validator/failure controls, and freeze exact staged identities.
Full default and remaining qualification checks are required before adoption;
if the measurement rejects it, production source remains HOST-04 and its
integrated verification remains applicable.

## Prepared source comparison

Candidate source is `b433da29` in `/private/tmp/pw-wait-host05`, native identity
`bab33b220f1ea50b50412a0d83b700b4a997e097c69d9ad974f3c5676da6af44`.
The signed candidate app was built from that committed source. Its separate
`host05-correctness-01` run (`20261108T204033Z_e650f582`) completed 91 of 92
selected cases: 90 passed, native-pause applicability failed as expected, and
`exec_control_states` was unrun because that checkout lacked its pinned pytest
installation. This is not a fully passing run. All 11 runner-unit cases (589
assertions), four validator-failure cases, seven failure-boundary cases, ABI
and nine source-drift cases passed; the signed app was valid and unchanged.
The broad suite selection brought in the two unrelated cases above. Their
outcomes remain explicit, and complete integrated verification remains required
before any adoption.

Comparison machinery, pacing and workloads reuse the completed HOST-04
comparison rehearsal and HOST-05 flavour rehearsal. The candidate changes no
stamp anchor, driver, worker behavior or staging recipe. Reader v11 and all
three apparatus hashes frozen above are unchanged. Both staged hosts use
inspection settings. The comparison is still at its gate while these exact
identities are committed.

| Receipt / input | SHA-256 |
| --- | --- |
| `tests/out/runs/host05-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/staged-identity-before.json` | `8688222087ce883e6cc448c9a752ff8f586fb9044912157d22c99fc855f80cc9` |
| `tests/out/runs/host05-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/schedule.json` | `9a1daf62bded23ad9aa64342f75f5582bdae832b9d0ee0504ab2bdf89f4ff52c` |
| `tests/out/runs/host05-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/host-baseline/host-build.json` | `89c0d3eafe2003391b423e7e8eddbedd92c5cff8fc9b5d597216798fd5b84707` |
| `tests/out/runs/host05-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/host-candidate/host-build.json` | `4734fc44706ee3a5d8d14d8e5feddd8e03454a3be906b736726d41b3f0b10248` |

Diagnostic observer limits: instrumented-minus-neighbor whole-request median
differences ranged from −0.647 to +11.307 ms in the inspection block and
−5.235 to +12.401 ms in the optimized block. Host export spans were
199.166–2410.041 µs and 160.291–572.208 µs respectively. No fixed observer
correction is applied. These differences do not isolate recorder overhead;
whole-request comparisons also include the independently staged executables.

## Disposition: rejected under the frozen held-time rule

`host05-comparison-01` accepted all 80 trials and formed all 40 pairs, with no
excluded, skipped, incomplete or unpaired trials. Calibration was credited,
all release response bounds passed (largest 4.954 µs), and cleanup settled.
Decode improved beyond uncertainty in every O64/O256 pair in both regimes:
135.208–919.042 µs saved. This establishes the local decoder improvement on
these fixture builds. It does not establish the required uniform shorter hold.

| Selected workload | Decode improves in every pair | Held total improves in every pair |
| --- | --- | --- |
| O64 rapid | yes | yes |
| O64 idle | yes | no: repetition 1 is 21.001 µs longer |
| O256 rapid | yes | no: repetition 3 is 1255.417 µs longer |
| O256 idle | yes | yes |

The O64 contrary pair decoded 135.208 µs faster, while planning and validator
spawn-to-EOF intervals grew by 41.4 and 103.1 µs. The O256 contrary pair
decoded 785.750 µs faster, while planning grew by 1449.6 µs and validator
spawn-to-EOF grew by 464.4 µs. These are observed locations of the added time,
not an established cause. No component or whole-request group worsened beyond
its spread in every pair; all individual flags remain in the reader output.
The no-query and small controls remain part of the retained comparison.

Do not relax the predeclared gate or collect more pairs. Candidate `b433da29`
is not integrated. Its correctness run is not a full acceptance battery, and
neither its incomplete exec-control case nor its known native-pause failure is
converted into a pass. The independent integer/offset controls and flavour
apparatus remain reusable. Reopening this source idea would require an explicit
new scope/acceptance decision (for example a claim based on less decoder work),
not treating this run as proof of uniform shorter holds. No total CPU, memory,
energy or scheduling benefit is established. HOST-06 starts from HOST-04.

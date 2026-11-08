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

Compiler-flavour apparatus is prepared. The diagnostic identities, observations
and source-candidate decision remain pending. Raw evidence stays in dispatcher-owned
local output; retention is finalized with the host round.

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

# Phase-barrier measurement fixture

Equipment for the phase-barrier investigation. It drives the shipped C worker
(`dist/PolicyWitness.app/.../pw-probe-runner`) through the runner's internal
driver, `runCWorker(_:phaseBoundary:)`, reached with `@testable import` as
`runner/Tests/PWRunnerCoreTests` does. The worker, its policy procedure, the
shared-memory protocol and public output are unchanged; the fixture is not
part of the app or the runner package.

## Build and run

From the repository root:

```sh
swift build --package-path records/performance/phase-barrier \
  --scratch-path .tmp/phase-barrier-build
tests/lib/python.sh records/performance/phase-barrier/measure.py --plan measure --label measure-b853
tests/lib/python.sh records/performance/phase-barrier/analyze.py \
  records/performance/runs/RUN-ID --out records/performance/evidence/RUN-ID
```

The fixture binary is `.tmp/phase-barrier-build/out/Products/Debug/PhaseBarrierProbe`.
Execute a new build once before measuring: the first exec of a new file is
delayed by Gatekeeper's scan. `measure.py` prints the new raw directory
(`records/performance/runs/<UTC stamp>-phasebarrier-<label>/`) first, refuses
an existing one, and holds `tests/.checkout.lock` for the schedule. Each unit
has a 20 s deadline (SIGTERM, then SIGKILL two seconds later); the schedule
has a 300 s ceiling; a first SIGINT stops before the next unit. Exit 0 means
the schedule completed.

| Plan | Units |
| --- | --- |
| `pilot` | one of each condition, shuffled |
| `measure` | five rounds of `hold0-boundary`, `hold200-boundary`, `hold800-boundary`; the dense, unsampled and deadline conditions in the first three rounds; each round shuffled with the recorded seed |

| Condition | Callback hold | Worker allowance | Worker CPU reads |
| --- | --- | --- | --- |
| `hold0-boundary` | 0 ms | default (60 s) | at callback entry and exit |
| `hold200-boundary`, `hold800-boundary` | 200, 800 ms | default | at callback entry and exit |
| `hold200-dense`, `hold800-dense` | 200, 800 ms | default | entry, exit and a thread reading every 1 ms until the worker exits |
| `hold200-none`, `hold800-none` | 200, 800 ms | default | none during the run |
| `deadline250-hold400-boundary` | 400 ms | 250 ms (`CWorkerInput.proceedWaitMs`) | at callback entry and exit |

## What one unit observes

The worker compiles and applies `(version 1)(allow default)(deny mach-lookup)`
and has one phase whose single action unlinks a file the fixture created. The
fixture holds the `phaseBoundary` callback, which the driver runs after it
observes arrival and before its release store. The hold is a controlled
substitute for collection time; no validator runs.

- Callback entry and exit, and the driver's `phaseReleaseOrdinal` call made
  immediately before the release store, on `CLOCK_MONOTONIC_RAW`.
- The file's existence at callback entry and exit and after the run, and a
  kqueue `NOTE_DELETE` for the unlink and `NOTE_EXIT` for the worker. The
  exit registration does not reap.
- Worker CPU from `proc_pid_rusage(RUSAGE_INFO_V6)`, each read bracketed by
  the fixture's clock, with the process start stamp checked for generation.
  The worker's lifetime CPU is the fixture's `RUSAGE_CHILDREN` difference,
  since the worker is its only child.
- The worker's PID, `p_uniqueid`, parent and creation time at callback entry;
  the driver's complete result, projected by reflection; clock readings that
  place kernel stamps on the monotonic axis; and a unit calibration of
  `rusage_info` time fields against `getrusage`.

`measure.py` checks after each unit that the identified worker generation no
longer exists and lists any process running the worker executable.

## Limits

- Arrival and acknowledgement times are not published by the worker. Callback
  entry is the host's recognition of arrival; the unlink event bounds
  acknowledgement from above.
- A running worker's CPU account advances in steps of up to about 10 ms
  here, so a read can lag by that much. Short-window CPU deltas are quantized;
  the lifetime total read after reap is not.
- `nanosleep` overshoots the requested hold by up to several milliseconds; the
  actual hold is recorded.
- Exit events are observed about 0.27 ms after the kernel's exit stamp.
- The dense reader's own CPU appears in the fixture's usage, not the worker's.

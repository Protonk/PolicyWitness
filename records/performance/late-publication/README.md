# Late-publication fixture

Equipment for the late-publication investigation. The fixture drives the
shipped C worker through the runner's internal driver,
`runCWorker(_:processCalls:phaseBoundary:)`, reached with `@testable import` as
`runner/Tests/PWRunnerCoreTests` does. `measure.py` also runs the public
`policy-witness run` with `_test_overrides`. Neither is part of the app or the
runner package.

## Build and run

From the repository root:

```sh
swift build --package-path records/performance/late-publication \
  --scratch-path .tmp/late-publication-build
tests/lib/python.sh records/performance/late-publication/measure.py --label series1-b853
tests/lib/python.sh records/performance/late-publication/analyze.py \
  records/performance/runs/RUN-ID --out records/performance/evidence/RUN-ID
```

The fixture binary is `.tmp/late-publication-build/out/Products/Debug/LatePublicationProbe`.
Execute a new build once before measuring; the first exec of a new file is
delayed by Gatekeeper's scan.

`measure.py`:

- prints the new raw directory
  (`records/performance/runs/<UTC stamp>-latepub-<label>/`) first and refuses
  an existing one;
- refuses while any process runs the worker executable;
- holds `tests/.checkout.lock` for the schedule;
- gives each unit a 15 s deadline (SIGTERM, then SIGKILL) and the schedule a
  240 s ceiling;
- stops at the first unit after which a worker process remains.

## Cases

The fixture always uses a 400 ms sentinel allowance (`CWorkerInput.sentinelTimeoutMs`;
production 120 s), the production 1,000 ms exit grace, the policy
`(version 1)(allow default)(deny mach-lookup)` and one file open-read attempt.
It holds the phase-boundary callback for 50 ms while sampling the spinning
worker, a control for the scheduler-state reading. The host excludes that
hold from its sentinel allowance.

| Case | Attempt target | Release of the attempt | Worker delay before `done` |
| --- | --- | --- | --- |
| `timely` | owned FIFO | 100 ms after the driver's release | none |
| `late-done` | owned regular file | immediate | `--post-apply-hang-ms 800` |
| `late-slot` | owned FIFO | 400 ms after the host's grace entry | none |
| `grace-exhausted` | owned FIFO | never | none |

The worker's open-read attempt calls `open(O_RDONLY)` and reads one byte. On
a FIFO both block until the fixture opens the write end with `O_NONBLOCK`,
which succeeds only while a reader is present, writes one byte and closes.

CLI units send the same attempt through `policy-witness run` with
`_test_overrides.worker_timeout_ms: 400` and, for `cli-late-done`,
`worker_post_apply_hang_ms: 800`. The harness releases the FIFO 150 ms
(`cli-timely`) or 950 ms (`cli-late-slot`) after the controller's spawn.

## What one fixture unit observes

On `CLOCK_MONOTONIC_RAW`:

- the driver's release call;
- every `waitpid`, `kill` and sleep call the driver makes, each wrapping the
  production function. The sentinel sleeps at most 2 ms and the readiness and
  grace waits 10 ms, so the last sentinel sleep and the first later wait
  bracket the exit-request store;
- the FIFO write end's open, write and close;
- the worker's `NOTE_EXIT`, which does not reap.

The fixture also records:

- the worker's CPU and per-thread scheduler state every 20 ms from the
  callback onward;
- the complete driver result;
- the orchestrator's `classify` and `resolveDisposition` readings of it.

`analyze.py` decides each unit's case from these observations, not its label.

## Limits

- The exit-request store, the slot's `completed` store and `done` are
  bracketed between observed calls and events, not timed directly.
- The worker publishes no attempt or acknowledgement times. Scheduler state
  and CPU show that it was blocked, not which call it was blocked in; the
  FIFO's reader presence and the worker's final progress word identify the
  attempt.
- Running CPU accounting advances in steps of up to about 10 ms. Flat CPU is
  judged over windows of at least 50 ms.

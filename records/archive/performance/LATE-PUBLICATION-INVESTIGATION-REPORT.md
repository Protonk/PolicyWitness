# Late publication during worker exit grace: build 853

> Archive availability: original raw runs are not retained. Reproduction
> procedures describe the original `records/performance/` layout and pinned
> environment; committed derived evidence remains available.

All four controlled cases were reached, through the driver seam (three runs
each) and through the public CLI (one run each). When the host's sentinel
deadline expired while the worker was blocked inside a released attempt, the
worker carried on regardless of the exit request. In the observed cases:

- **An attempt that finished during grace was retained.** The worker completed
  the attempt about 404 ms into grace, published its slot and `done`, and
  exited 0. The host reaped it without a kill, and the reply reports the
  attempt as an ordinary completed result.
- **An attempt already published before the deadline was also preserved.**
  `done` arrived during grace, and the earlier slot survived.
- **The two are indistinguishable in the public reply** except for wait
  durations. Both carry `runner_timeout`.
- **An attempt still unfinished when grace ran out** ended with the host's
  SIGKILL. Its only trace is the worker's "attempt 0 started" progress word.

## Evidence and conditions

The worker was the shipped `pw-probe-runner` of `dist/PolicyWitness.app`,
version 0.3.3, build 853, commit `1bf0341` (SHA-256 `c8ac685b…`). The runner
and worker sources are unchanged since that commit. The fixture
([`late-publication/`](late-publication/README.md)) was built by SwiftPM with
the Swift 6.4 toolchain (binary SHA-256 `49a740a3…`). It reached the driver
through `@testable import`.

The run was interactive, with this agent session active, on AC power at load
average 1.31. The machine was a Mac17,3 with macOS 26.7.1 (25G241). Event
margins were hundreds of milliseconds; no quiet-machine segment was needed.

The run is
[`20261024T143131685570Z-latepub-series1-b853`](evidence/20261024T143131685570Z-latepub-series1-b853/summary.json):
`measure.py` SHA-256 `42b6a174…`, analyzed by `analyze.py` SHA-256
`1bf9627a…`. It ran 16 units in a recorded shuffled order, seed 20261024:

- every unit completed within its deadline;
- all 65 raw checksums verified;
- no worker process remained after any unit or at the end;
- every owned FIFO was removed.

Original raw files are not retained; the committed derived evidence remains.

Differences from production:

- The sentinel allowance is 400 ms (`CWorkerInput.sentinelTimeoutMs` in the
  fixture, `_test_overrides.worker_timeout_ms` in the CLI). Production is
  120 s.
- The fixture holds the phase-boundary callback for 50 ms.
- The fixture wraps the driver's `waitpid`, `kill` and sleep calls only to
  timestamp them.
- The late-`done` case uses the worker's post-apply hang seam.

The exit grace stayed at the production 1,000 ms. No application code,
worker instruction, schema or production timeout was changed.

## The implementation as verified

Driver, [`CWorker.swift`](../../../runner/Sources/PWRunnerCore/CWorker.swift):

1. The sentinel loop polls at 2 ms (line 1283).
2. On its exit the driver stores `exit_requested` (line 1380) and records the
   cleanup trigger.
3. An unreaped worker gets a 10 ms-polled grace (line 1393). Exhaustion is
   followed by `terminate()`, which sends SIGKILL and makes a blocking wait
   (line 1413).
4. The collection basis is set from the reap (line 1423).
5. The final snapshot after cleanup reads every slot whose `completed` flag is
   set (lines 1440–1446). It has no record of when that flag was stored.

Orchestrator: any run whose disposition stop reason is `sentinel_deadline` is
classified `runner_timeout`
([`CWorkerOrchestrator.swift`](../../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift),
line 1407), whatever the final snapshot holds.

Worker, [`pw_probe_runner.c`](../../../controller/tools/pw_probe_runner/pw_probe_runner.c):

- `run_attempt` stores the slot's `completed` flag after the native work
  returns (line 1530).
- The open-read attempt (line 659) calls a blocking `open(O_RDONLY)`, then
  reads one byte.
- The post-apply hang (line 1983) sleeps after every slot and the phase
  complete, and before `done`.
- The worker reads `exit_requested` only inside its release wait (line 1599).

## Method

The fixture's worker applies `(version 1)(allow default)(deny mach-lookup)`
to itself, is released after the 50 ms callback, and performs one open-read
attempt on a target the fixture owns. A FIFO blocks the worker inside the
native `open` and `read` until the fixture releases it. That release opens the
write end with `O_NONBLOCK`, which succeeds only while a reader waits, then
writes one byte and closes.

Grace entry is identified from the driver's own calls: the first 10 ms sleep
request after a 2 ms sentinel sleep. The late-slot release is timed from that
moment. A thread records the worker's CPU and per-thread scheduler state every
20 ms. During each callback hold the spinning worker read `RUNNING` with CPU
rising, which validates the state reading in every unit. The CLI units send
the equivalent request through `policy-witness run`, and the harness releases
the FIFO at a fixed delay after the controller's spawn.

| Event | Observation | Observer |
| --- | --- | --- |
| release | the driver's `phaseReleaseOrdinal` call before its store | fixture |
| attempt in progress | `WAITING` with no CPU growth from release through expiry; the FIFO's reader present at release; final progress word | fixture sampler; FIFO open result; driver snapshot |
| sentinel expiry, `exit_requested` store | bracketed between the last sentinel sleep's return and the first following `waitpid` | wrapped driver calls |
| native attempt completion | bounded by the FIFO write's completion and the worker's exit | fixture; kqueue |
| slot `completed`, `done` | final flags; their stores are bracketed, not observed | driver snapshot |
| grace stop, kill, reap | grace record; the wrapped `kill` and the `waitpid` returning the worker | driver; wrapped calls |

## Cases reached

Times are milliseconds after the driver's release (n=3 each).

| Case | Stop / grace end | Exit request stored | Attempt released | Worker exit | Kill | Final slot / `done` | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| timely | `done` / reaped during grace (10–12 ms) | after `done` | 105.1–105.2 | 105.6–105.9 | none | completed rc 0 / true | `ok` |
| late `done` | `sentinel_deadline` / reaped during grace (407–417 ms) | 400.0–400.3 | immediately; hang began by 19–21 | 805.7–806.6 | none | completed rc 0 / true | `runner_timeout`, "no termination requested" |
| late slot | `sentinel_deadline` / reaped during grace (407–412 ms) | 400.0–400.4 | 803.6–805.8 | 804.4–807.1 | none | completed rc 0 / true | `runner_timeout`, "no termination requested" |
| grace exhausted | `sentinel_deadline` / exhausted (1,001 ms) | 400.2–400.5 | never | 1402.2–1403.8 | SIGKILL, rc 0, at 1401.2–1402.1 | not completed / false | `runner_timeout`, "host requested SIGKILL during cleanup" |

In each late-slot, late-`done` and grace-exhausted unit:

- the worker read `WAITING` in every sample from release to expiry (16–18
  samples), with no CPU growth over 338–361 ms;
- the collection basis was `after_confirmed_reap`;
- the reaped status was exit 0, or signal 9 after the kill.

**Late-slot bounds.** The exit request was stored within a window of about
0.1 ms near 400 ms. The worker's `open` and `read` could return only after
the FIFO write, which completed at 803.7–805.8 ms, and the worker exited
0.7–1.5 ms later. The slot's `completed` store and `done` lie in that window,
403–406 ms after the exit request.

**Late-`done` bounds.** The worker was in its post-slot hang by 19–21 ms
after release. By source order, its slot was therefore stored at least 379 ms
before the exit request; `done` came just before its exit, about 405 ms
after.

**Grace-exhausted partial evidence.** The final snapshot holds:

- `applied`, `arrived` and `acknowledged`;
- slot 0 not completed, with no call-boundary flag;
- the worker's progress word: operation 9 (attempt), stage 1 (started),
  index 0;
- no failure publication;
- `termSignal: 9`.

The CLI reply reports the attempt as `rc: -1`,
`missing_reason: slot_incomplete`, with `partial_steps: true`,
`progress_association: step_index`, a `signaled` disposition and
`termination_cause: host_sentinel_deadline`.

**CLI confirmation.** Each of the four CLI units reached its case:

- The late-slot unit's FIFO was released 951 ms after the controller's spawn.
  Grace lasted 491 ms, and the worker exited 0 with no termination request.
- The late-slot and late-`done` replies differ only in wait durations and the
  echoed hang override. Both report:
  - attempt `rc: 0` with `lifecycle.result: published` and
    `summary: completed`;
  - `partial_steps: false`, `done_observed: true` and `clean_exit`;
  - `runner_timeout`.

## What grace retains

In the observed cases, grace does both:

- **It recovers a newly completed attempt slot.** An attempt that was blocked
  at the deadline and finished inside grace was published and retained as an
  ordinary completed result.
- **It preserves an already published slot**, together with a `done`
  published during grace.

In both, the deadline survives in `poll_stop_reason` and the outcome is
`runner_timeout`. No field records when a slot was published, so a reader
cannot tell a slot completed before the deadline from one completed during
grace.

## What the cancellation flag can and cannot interrupt

The worker reads `exit_requested` only while waiting for release. In the
observed runs, storing it at about 400 ms interrupted neither a worker blocked
in a native `open`/`read` nor one sleeping in the post-apply hang. Both
continued, completed and published normally.

Only the host's SIGKILL at grace exhaustion ended a worker still inside its
attempt. A worker that exits by itself within grace is reaped without any
termination request. Cancellation of a worker still waiting for release was
not exercised here.

## Agreement with the documentation and existing controls

Observed behavior agrees with the user guide:

- "`done_observed` and completed slots reflect the final acquire snapshot
  after cleanup. `poll_stop_reason` retains an earlier deadline even if the
  worker finishes during grace."
- `runner_timeout` "remains a timeout if the child voluntarily exits during
  grace."

It agrees with [WORKER.md](../../../docs/WORKER.md): the exit request "still
cancels a worker waiting for release; grace and termination remain fallback
cleanup". It agrees with the failure-propagation contract's rows for a
voluntary exit during grace and for `done` published during grace.

No behavior was found that contradicts the lifecycle documentation, and no
application error was observed. Two documentation observations, neither a
fault in the application:

- **Grace-time slots are not called out.** The limits table says sentinel
  expiry "can yield `runner_timeout` with partial evidence." The late-slot
  case shows that it can also carry complete evidence, including an attempt
  finished after the deadline. The guide's final-snapshot sentence implies
  this; the outcome catalog does not say it.
- **A stale test comment.** The `check_attempt_in_flight.py` docstring says
  case `a1`'s termination cause "today ... reports 'unknown'". The README
  beside it says the check requires `host_sentinel_deadline`. This build
  reported `host_sentinel_deadline` for the comparable grace-exhausted CLI
  run, so the docstring describes an earlier state of the application.

The existing live control `witness_contract/worker_attempt_in_flight_at_deadline`
exercises a FIFO blocked through grace exhaustion (`a1`) and a late `done`
through the hang seam (`a4`). Neither releases a blocked attempt during
grace; the late-slot case here is not covered by it.

## Limitations

- The `exit_requested`, slot `completed` and `done` stores are bracketed by
  observed calls and events; their instants are not observed.
- Scheduler state shows that the worker was blocked, not in which call. The
  FIFO's reader presence and the final progress word identify the attempt.
- One attempt kind was exercised: a blocking file open-read on a FIFO.
  Attempts with their own internal deadlines, such as exec children, can end
  differently within grace.
- Multi-slot and multi-phase plans, a later slot in flight after an earlier
  one, and validator interaction during grace were not exercised by the
  fixture; the CLI units had one ordinary validator collection.
- The run was interactive; timings describe this machine and interval.

## Reproduction and cleanup

The [fixture README](late-publication/README.md) has the build, schedule and
reader commands. Each evidence directory holds `summary.json` and
`units.json` with each unit's event order, bounds and final fields, and
`run-record.json` with the process snapshot trimmed to CPU shares.

Cleanup:

- The fixture removed each FIFO or file after its run, and the harness
  removed each CLI FIFO.
- No worker process remained after any unit.
- The checkout lock was released.
- Build intermediates are in `.tmp/late-publication-build`.

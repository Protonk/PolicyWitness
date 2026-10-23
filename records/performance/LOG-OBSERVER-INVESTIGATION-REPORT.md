# Supplementary log collection: two build-841 pilots

Both pilots completed their 44 planned invocations with complete evidence and
cleanup: 65.950 s and 65.607 s against separate 180 s ceilings. Direct historical
`/usr/bin/log show` invocations took 649–695 ms across the tested conditions,
including 655–677 ms for deliberately no-match queries. This establishes a
substantial collection interval even when the existing observer is bypassed;
it does not isolate log-store opening, scanning or other internal OS work.

For four fresh executions queried repeatedly, the returned bytes were identical
at nominal delays of 0, 2 and 10 s. Twelve comparable fresh executions queried
only once, first at one of those delays, each returned a worker-matching denial
line. These small observations establish neither completeness nor an absence
of query effects. No application change or instrumentation followed.

## Runs, evidence and conditions

| Run | UTC interval, 2026-10-23 | Duration | Cleanup | Planned / completed |
| --- | --- | ---: | ---: | ---: |
| 1: `20261023T233408639400Z-log-pilot-b841` | 23:34:08.645–23:35:14.594 | 65.950 s | 0.066 s | 44 / 44 |
| 2: `20261023T233625785042Z-log-pilot-b841` | 23:36:25.791–23:37:31.397 | 65.607 s | 0.066 s | 44 / 44 |

Each run contains 24 historical cost queries, eight fresh specimen executions
and twelve fresh-event queries. Each has terminal exit 0, `manifest_exhausted`,
complete cleanup and 192/192 verified files with no uncovered files. All 88
invocations exited 0, finished both output streams, and had confirmed owned
process-group absence. All 24 observer reports also had `result.ok: true`,
successful inner log-child exit/reaping, matching query metadata, no cutoff
and no truncation. All captured stderr streams, including inner log stderr,
were empty. No observations were excluded. No sleep or clock fault was detected
during invocation spans; delayed waiting intervals are not separately classified
by the per-invocation clock check.

The unchanged app is PolicyWitness 0.3.2 build 841, source
`8b2e5c93b12e637e8f7d21d321efe81c7d76cf04`. The same 12 application identity
files matched the previous investigation and both run configurations. The
system log executable and relevant source/helper dependencies were also pinned.
Post-run verification matched those identities and retained script/specimen
snapshots. No application source, executable or build changed. The measurement
checkout was `a1b86bba1784c8462ccc6cc2a2a9fb510a376fe3` with investigation files
uncommitted; hashes and snapshots identify the actual procedure beyond that
commit.

The operator authorized one pilot and one further pilot if needed, reporting a
quiet machine. The agent remained active. Both endpoint snapshots in both runs
reported Mac17,3, arm64, ten logical CPUs, 16 GiB RAM, macOS 26.7.1 (25G241),
AC power and a charged battery. All condition probes succeeded. `pmset therm`
reported no recorded thermal/performance/CPU-power status; it did not measure
temperature or continuous thermal pressure. Background-server name observations
retain the earlier limitation that the custom server's exact name was not
supplied. Endpoints and the operator account do not establish constant background
activity. Each idle-sleep assertion remained active until cleanup and was
released; display lock/dimming remained allowed.

Run 2 used the same configuration and schedule to check whether run 1's slower
first observer invocation recurred. It is a separately identified follow-up,
not a replacement. No further live run was made. After both runs ended, the
operator was told normal program use could resume; subsequent work only reads
saved evidence and writes derived analysis/documentation.

Evidence:

- [Run 1 per-observation summary](evidence/20261023T233408639400Z-log-pilot-b841/summary.json).
- [Run 2 per-observation summary](evidence/20261023T233625785042Z-log-pilot-b841/summary.json).
- [Recomputed comparisons and checks](evidence/log-observer-pilot-analysis.json), produced by
  [analyze.py](log-observer/analyze.py).
- [Final preparation-control ledger](evidence/20261023T230543377500Z-log-preparation-controls/controls.json).

Complete raw output is under `records/performance/runs/<run-id>/`, gitignored
and available only in this checkout. New raw directories are mode 0700 and files
were created under a 077 umask. Raw logs are not copied into derived evidence:
content-level comparisons require those local files. Exported checksum lists
attest the named raw files, not a portable copy of them.

## Collection path and timing boundaries

The source-supported path is:

1. The controller completes native execution, selects the authoritative worker
   PID and constructs a query window from the runner-client wall-clock span.
   Bounds round outward to seconds and add two seconds of padding at each end.
2. It creates a shared monotonic budget before launching the observer: the start
   of the earlier investigation's L and L′.
3. The observer parses arguments, constructs the process/PID predicate and
   launches `/usr/bin/log show --style syslog --info --debug` with those bounds.
4. Inner supervision reads bounded pipes, observes child exit and reaps it.
   L′ is recorded here, before log-text decoding/parsing and report serialization.
   Its shared origin includes observer startup.
5. Outer supervision receives the observer's report and exit, completes group
   cleanup and records L. Controller reply parsing, admission, association and
   envelope assembly follow; their individual durations are not exposed by L.

These boundaries are implemented in [run_flow.rs](../../controller/src/run_flow.rs),
[sandbox_log.rs](../../controller/src/sandbox_log.rs),
[sandbox-log-observer.rs](../../controller/src/bin/sandbox-log-observer.rs),
[log_capture.rs](../../controller/src/log_capture.rs), and
[log_show.rs](../../controller/src/log_show.rs). Native execution evidence remains
separate from supplementary collection.

This pilot's `process_wall_ms` spans Popen entry through collected `wait4`,
including pipe handling and supervision. `wall_ms` additionally includes capture
setup and subsequent group probing; both are retained. They bracket subprocess
execution, not exact exec or kernel-exit instants. Standalone observer mode
starts its native budget after argument parsing, unlike the controller's shared
origin. Its native `collection.elapsed_ms` therefore is not the earlier
controller-driven L′ on an identical origin.

Direct queries use identical OS arguments/output mode per condition, but Python
consumes their output while the observer uses native supervision and emits JSON.
These differences prevent interpreting elapsed-time subtraction as pure wrapper
overhead. CPU observations account for the measured child and reaped descendants,
not shared logging services. Neither elapsed nor CPU observations separately
identify store opening, scanning, formatting, IPC or waiting.

Controller `captured` requires completed collection and processing. Standalone
observer success must be read from its report as well as process status: a
failed report can exit 0. Direct query exit 0 establishes neither retrieved
events nor completeness. Failed, empty and truncated outcomes remain distinct;
no failure or truncation occurred in these live pilots.

## Historical-query cost observations

The anchor was `mach_deny` invocation 00002 from the earlier run at 21:20:50 UTC,
with one parsed denial. Its original interval is five seconds wide. The wider
condition keeps the end and extends the start to make 60 seconds. Another
condition shifts the five-second interval 60 seconds earlier. Predicate
conditions add a literal prefilter, request no matches with `FALSEPREDICATE`, or
match all PW worker PIDs within the original small interval.

Each condition/method cell has **n=2 per run**. The table shows minimum–maximum
process spans in ms; all observations and conventional medians are retained in
the analysis. Block 1 runs observer then direct in the listed order; block 2
reverses both method and condition order. No warm-up is discarded and no query
is labeled a known cold-store measurement.

| Query condition | Run 1 observer | Run 1 direct | Run 2 observer | Run 2 direct |
| --- | ---: | ---: | ---: | ---: |
| Original interval/predicate | 686.031–751.001 | 657.501–685.430 | 680.429–681.851 | 663.632–677.708 |
| 60-second interval | 696.078–705.769 | 693.707–695.109 | 690.320–692.491 | 685.641–690.386 |
| Earlier interval, same width | 670.275–678.144 | 671.413–681.709 | 668.306–670.106 | 652.047–653.166 |
| Literal prefilter plus original regex | 676.805–683.064 | 649.571–678.710 | 670.936–675.537 | 658.816–670.248 |
| Deliberately no match | 675.742–678.431 | 655.134–677.141 | 673.152–675.746 | 655.890–658.819 |
| All PW worker PIDs, original interval | 676.396–682.673 | 675.224–689.727 | 671.640–680.109 | 649.261–657.751 |

All observer/direct pairs returned identical log bytes within each condition
and block. Original, wider, literal-prefilter and all-PW-worker queries returned
2,193 bytes with one worker-matching denial line. Earlier-window and no-match
queries returned 51 bytes with no matching denial line: an empty event result
is not empty stdout. Broadening the worker predicate did not increase returned
volume here, so it did not supply a high-volume comparison. Predicate complexity
and output quantity are not independently identified by these cells.

The eight original-condition results across methods, blocks and runs are also
byte-identical to the saved capture from more than two hours earlier. That
establishes retention and repeat retrieval of this particular content, with many
intervening queries, not general retention or completeness.

Direct 60-second queries exceeded corresponding original-width measurements
by 9.679 and 36.205 ms in run 1, and 26.755 and 7.933 ms in run 2, while returning
identical bytes. This is an observed width contrast for these windows, orders
and runs; two widths cannot establish a scaling law, and shared-state/time-order
effects remain possible. No-match queries still took roughly two-thirds of a
second, so low output did not imply a cheap invocation here. The measurements
do not identify why that interval exists.

Run 1's first observer invocation was 751.001 ms, with native inner elapsed
745 ms; its later original-condition observation was 686.031 ms. Run 2 began
at 681.851 ms, with inner elapsed 677 ms, and ended that condition at 680.429 ms.
The larger first observation did not recur in the second fresh harness process.
Warming, scheduling and other temporal conditions remain explanations; the
store was not reset or independently characterized. All four values remain.

Within-block observer-minus-direct differences span −13.331 to +65.570 ms in
run 1 and +2.105 to +30.848 ms in run 2. These changing differences, including
negative values, cannot supply a constant wrapper cost. They compare whole
invocations and do not estimate component costs or prospective speedup.

## Fixed fresh events queried at different delays

Each run executed four cohorts in each of two reversed-order blocks:
repeated queries at 0/2/10 s, and first-only queries at 0, 2 or 10 s. Across
both runs there are 16 distinct workers: four repeated events contributing
twelve queries, and twelve first-only events contributing twelve queries.
These are related observations, not 24 independent executions.

The existing `mach_deny` fixture ran with automatic collection disabled and a
declared 5 s runner timeout. All sixteen execution envelopes reported `ok`.
Each native attempt separately reported `lookup_failed`, rc 1,
`bootstrap_look_up: kr=1100`, with a completed attempt lifecycle. The validator
reported `deny`; comparisons reported `query_first` with target relation
`unresolved`. These facts do not declare agreement between prediction and
enforcement or attribute the failure solely to sandbox policy. No specimen
was regenerated to obtain another view of its original event interval.

All 24 direct queries returned 2,193 bytes including exactly one line matching
the complete original worker token and `deny(...) mach-lookup com.apple.logd`.
For each repeated event, full output was byte-identical across all three
queries: no added/removed/reordered lines, changed text or changed duplicate
counts appeared. The worker-line subset was also identical. Worker identity,
window, padding, predicate and syslog format were constant for each repetition.

| Cohort, per run | Executions | Queries per execution | Observed worker-matching denial retrieval |
| --- | ---: | ---: | --- |
| Repeated, 0/2/10 s | 2 | 3 | All six queries; bytes stable within each event |
| First query at 0 s | 2 | 1 | Both queries |
| First query at 2 s | 2 | 1 | Both queries |
| First query at 10 s | 2 | 1 | Both queries |

These outcomes held separately in both runs. Between fresh executions,
different PIDs, timestamps and events prevent treating equal counts as identical
content. The cohorts did not reveal an added record attributable to waiting or
prior querying; their small size cannot exclude either effect.

Actual timing across both runs follows. Each delay has eight queries: four
repeated-event observations and four first-only observations.

| Nominal delay | Actual Popen entry after controller reap | Actual query completion after controller reap | Query span |
| --- | ---: | ---: | ---: |
| 0 s | 0.624–0.762 ms | 0.605–0.635 s | 604.297–634.206 ms |
| 2 s | 2.002–2.007 s | 2.617–2.646 s | 614.323–640.135 ms |
| 10 s | 10.003–10.007 s | 10.625–10.658 s | 619.955–651.137 ms |

The nominal zero-delay query still takes about 0.6 s to finish. Retrieval in
that query does not prove the line was available at its sub-millisecond launch
time, nor locate when the OS emitted or stored it. Padding can extend past the
query start. First-only means no earlier query by this procedure for that
execution's interval; previous queries of other intervals and other processes
can affect shared state. Historical queries preceded these fresh-event queries,
so their different timing ranges do not isolate query age as a cause.

Exact byte matching detects content differences without inventing stable record
IDs. Had lines changed, additions/removals alone would not establish mutation of
one OS record. Full equality here needs no such guess. Stable results never
establish that every relevant record was available; no monotonic-superset
assumption was used.

## Controls and remaining questions

Thirteen final preparation controls passed, covering recording, ordinary/nonzero
and failed launch outcomes, byte limits, deadlines, interruption, inherited-writer
cleanup, content comparison, checksum refusal and whole-driver accounting. A
shortened ceiling retained one timed-out invocation and 43 never-started entries
with completed cleanup. The initial import collision and superseded attempts
remain preserved. Sandboxed condition-probe failures were retained and the same
stand-in command passed outside that sandbox. Both live pilots ran outside it;
no live failure was silently retried.

The pilots support substantial directly measured log-tool invocation cost and
stable retrieval for selected events over inspected times. They leave open:

- The division of direct-query time among startup, store access, scan, formatting,
  IPC and waiting; external spans do not separate these components.
- Behavior for other windows, larger outputs, other predicates and independently
  varied output quantities. These conditions did not generate a volume series.
- Rates of delayed availability, disappearance, modification or non-delivery.
  Four repeated events and twelve first-only events cannot establish them.
- Separation of delay from previous-query effects and shared logging state.
  Reversed-order cohorts do not give the investigator control of that state.
- The cause of the first longer query and differences between positions/series.
  Constant machine conditions and a cold/warm mechanism were not established.

No speedup, batching, streaming, caching or evidence-semantics proposal follows
from these observations. A later investigation may narrowly instrument a
consequential unresolved boundary; these results do not require that change.

Reproduce the checks/calculations from retained local raw files with:

```sh
tests/lib/python.sh records/performance/log-observer/analyze.py
```

This verifies raw checksums, reproduces saved summaries, checks source/specimen
and executable identities, recomputes spans from raw endpoints, compares raw
output bytes, and regenerates `evidence/log-observer-pilot-analysis.json`.

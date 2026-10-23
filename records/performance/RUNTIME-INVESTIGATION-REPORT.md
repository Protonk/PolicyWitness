# Runtime investigation, first cycle: build 841

The operator-run series completed 1,452 invocations in 473.357 s (7 min
53 s), with complete evidence and no detected system sleep. Each of the
11 cells has 132 observations. Capture-cell median wall spans were
671.707–673.896 ms; no-capture specimen medians were 37.269–41.024 ms.
The directly recorded log-supervision span was the largest named interval
inside capture runs. These results describe this executable, specimen set,
order and machine interval; they are not a throughput estimate or an
optimization recommendation.

## Evidence and conditions

The run is `20261023T212050Z-short-b841`, started at
2026-10-23 21:20:50 UTC and finished at 21:28:43 UTC. The saved terminal exit
status is 0 and `run.json` says `manifest_exhausted`. All 1,452 planned entries
have completed status records; there are no missing, extra, interrupted,
timed-out or never-started entries. All 5,824 listed checksums verify and
there are no unattested files. Cleanup took 0.255 s within the 10 s reserve;
the run ended before its 600 s ceiling. No invocation was excluded from
these summaries. Zero sleep detections uses the harness's 1 ms read-skew
threshold, not an assertion of infinitely precise clock equality.

The 1,320 specimen invocations all reported `normalized_outcome: ok` and
controller exit 0. All 660 enabled captures reported `captured`; 660 specimen
invocations disabled capture, making L/L′ inapplicable. The other 132 entries
were version controls. There were no absent or invalid applicable measures
and no negative residuals. A run-level `ok` is not a claim that all submitted
operations succeeded or that prediction and enforcement agreed.

The app was version 0.3.2, build 841, source
`8b2e5c93b12e637e8f7d21d321efe81c7d76cf04`, describe
`v0.3.2-50-g8b2e5c9`, using its existing default inspection compilation flavor.
The measurement checkout was `1fb5a52ecf3391b5f20c4f9472d00b629e42070c`;
the only reported working-tree entry at start and end was the newly created
terminal-record directory. The app identity hashes match both pilots.
Every output envelope carries the same build identity. Specimen copies and
invocation machinery match the retained source snapshots. No app source,
profile, timeout setting, schema or build changed during this investigation.

Conditions at both endpoints reported Mac17,3, 10 logical CPUs, 16 GiB memory,
arm64, macOS 26.7.1 (25G241), AC power and a charged battery. The thermal
probe reported that no warning/performance/CPU-power status had been recorded;
it did not measure temperature or thermal pressure. The same three executable
name matches for the Codex app-server package were present at both endpoints.
The custom server's exact executable name was unavailable; an empty broad
`app-server` match does not establish its absence. Endpoint observations do
not establish constant conditions throughout the interval.

The operator was away for most of the interval and returned when the run was
nearly finished. They report leaving the machine plugged in, waking it on
return, starting no applications, and having fewer than ten idle terminal
tabs with no other intentional application activity. This account does not
establish the absence of background work. Activity while they were away
remains unobserved. The idle-sleep assertion launched, was still running at
cleanup, and was released. Screen locking and display dimming were allowed.
No detected system sleep during invocations does not exclude display waking,
unlocking or other user interaction; the operator's waking description does
not identify which of those events occurred.

The complete raw directory is `records/performance/runs/20261023T212050Z-short-b841/`;
it is gitignored and available only in the producing checkout. Committed
[evidence and per-observation summaries](evidence/20261023T212050Z-short-b841/summary.json)
retain the manifest, conditions, status accounting and distributions.
[Analysis calculations](evidence/20261023T212050Z-short-b841/analysis.json) and their
[reproduction script](evidence/20261023T212050Z-short-b841/analyze.py) establish the checks
and comparisons below. Terminal outputs and the operator note are under
`evidence/20261023T212050Z-short-b841-terminal/`. Checksums in the exported metadata
refer to the raw directory, not to a complete portable copy of it.

## What was measured

Each round used the five capture cells, the same five no-capture cells and
one version control, in fixed order, for 132 rounds. The specimens were
single-step `file_read_deny`, `mach_deny`, `sysctl_read`, `exec_spawn` and
`path_diagnostics_strict`. Defaults retained the 240 s runner timeout and
10 s log allowance. The effective harness deadline was recorded separately.
There were no concurrent, external-runner, multi-step or multi-phase entries
in the operator manifest. There were no labeled warm-ups in this operator
run; the earlier pilots' warm-ups stay separate, and version preflight is
an unmeasured identity observation.

| Measure | Events and observer | Clock / interpretation limit |
| --- | --- | --- |
| W | Harness clock before controller spawn through collected `wait4` exit | Raw monotonic, paired with raw uptime for sleep detection; includes launch and exit-observation overhead. |
| C | Controller clock before Swift-client spawn through collected client exit | Unix wall clock, whole ms; combines startup/XPC work and does not prove clock continuity. |
| R | Host ready-pipe polling start after policy transfer through recognized stop | Monotonic, 10 ms polling quantum; not compile time or exact byte-arrival time. |
| S | Host sentinel polling interval minus recorded phase-hook exclusions | Monotonic, 2 ms polling quantum; not individual attempt duration. |
| X | Synchronous phase-hook intervals excluded from S | Host monotonic; planning, validator and collection combined. |
| G | Host grace polling after exit request through recognized reap/error/deadline | Monotonic, 10 ms quantum; not exact worker-exit time. |
| L | Shared log budget creation before observer launch through outer supervision finish | Controller monotonic; excludes subsequent controller reply parsing/correlation. |
| L′ | The same shared budget start through inner log-child supervision finish | Observer on shared monotonic origin; includes observer startup, so not standalone `log show` time. |
| E | Envelope value construction stamp | Unix wall-clock timestamp, retained per observation; not print completion. |
| U | `wait4` user+system accounting for the controller and reaped descendants | Kernel CPU accounting; excludes launchd's host/worker/validator tree. |

All 1,452 exits used the kqueue process-exit observation path; there was no
polling fallback. Durations below are milliseconds. Medians average the two
middle observations for even n; p90 uses nearest rank. The samples are
repeated observations in one ordered interval, not independent machine trials.
No confidence intervals or population-wide failure probabilities are inferred.

## Observed duration distributions

| Cell | n | Minimum | Median | p90 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| file_read_deny/capture | 132 | 664.811 | 671.707 | 682.212 | 716.195 |
| mach_deny/capture | 132 | 668.065 | 673.896 | 684.287 | 751.972 |
| sysctl_read/capture | 132 | 638.442 | 671.980 | 681.301 | 728.003 |
| exec_spawn/capture | 132 | 665.991 | 673.346 | 683.006 | 718.673 |
| path_diagnostics_strict/capture | 132 | 662.269 | 671.993 | 682.098 | 737.177 |
| file_read_deny/no-capture | 132 | 39.284 | 41.024 | 44.074 | 44.319 |
| mach_deny/no-capture | 132 | 36.736 | 38.401 | 41.473 | 44.456 |
| sysctl_read/no-capture | 132 | 34.974 | 37.269 | 40.356 | 40.698 |
| exec_spawn/no-capture | 132 | 36.569 | 39.244 | 42.231 | 42.528 |
| path_diagnostics_strict/no-capture | 132 | 36.253 | 38.753 | 41.884 | 42.447 |
| version | 132 | 1.975 | 2.098 | 2.169 | 3.264 |

The following table describes each stage without pooling unlike cells into
one median. The third column spans the separate cell medians, and the fourth
covers the minimum to maximum across the named cells. Each cell has n=132;
all per-cell minimum/median/p90/maximum values are in the committed summary.

| Measure / cells | n per cell | Range of cell medians | Full observed range |
| --- | ---: | ---: | ---: |
| C, capture | 132 | 37.000–38.000 | 35.000–60.000 |
| C, no-capture | 132 | 35.000–38.000 | 32.000–42.000 |
| R, all specimen cells | 132 | 12.000–12.000 | 10.000–15.000 |
| S, all specimen cells | 132 | 2.000–2.000 | 2.000–9.000 |
| X, all specimen cells | 132 | 0.000–1.000 | 0.000–1.000 |
| G, all specimen cells | 132 | 0.000–0.000 | 0.000–0.000 |
| L, capture | 132 | 630.000–632.000 | 599.000–708.000 |
| L′, capture | 132 | 629.000–630.000 | 596.000–706.000 |
| U, capture | 132 | 95.887–97.285 | 68.460–161.688 |
| U, no-capture | 132 | 4.390–5.175 | 4.202–5.353 |
| C−R−S−X−G | 132 | 20.000–23.000 | 19.000–35.000 |
| W−C−L, capture | 132 | 2.982–3.628 | 1.703–5.098 |
| W−C, no-capture | 132 | 2.363–2.928 | 1.495–3.836 |

All 1,320 ready waits ended `received`, sentinel waits `done`, and grace waits
`reaped_during_grace`. Every G was zero at whole-ms precision; that does not
mean no grace/reap work occurred. X was zero at whole-ms precision in both
sysctl cells and one millisecond in the other eight cells. The host timings
observe recognition boundaries, so the R/S values do not establish compile,
query or attempt execution costs.

C−R−S−X−G and W−C−L are derived residuals across clock domains, not directly
measured component costs. The summary also preserves C−R−S−G, which includes
X. None was negative. The residuals cannot decompose launchd, caller
authorization, Swift startup, host setup, dossier construction, parsing or
rendering. The version median of 2.098 ms contextualizes startup plus a small
response; it is not subtracted from run timings or treated as a universal floor.

The largest W was sequence 937, round 86, `mach_deny/capture`: 751.972 ms,
with C=40 ms, L=708 ms, L′=706 ms and U=161.688 ms. Its outcome and wait stop
words were the same as the other observations; it remains in the sample.
The available fields locate the longer interval at log supervision but cannot
identify which operation inside the observer or OS log tool caused it.

## Comparison with the interactive pilots

The two pilot series were `20261023T201755491161Z-pilot` and
`20261023T202250234510Z-pilot`, each with n=5 per non-warm-up cell and n=3
warm-ups per capture cell. Each app identity matches the operator run. All
pilot observations remain separate. The initial pilot's capture W medians
were 679.604–685.567 ms; the final pilot's were 675.582–680.394 ms, compared
with the operator run's 671.707–673.896 ms. The operator observations therefore
do not reproduce the pilot medians exactly.

Differences below are operator median minus final-pilot median, in ms;
pilot n=5 and operator n=132 for each entry. Both distributions, not only these
differences, are retained in `analysis.json`.

| Specimen | Capture Δ median W | No-capture Δ median W |
| --- | ---: | ---: |
| file_read_deny | -3.875 | -2.881 |
| mach_deny | -4.018 | -2.985 |
| sysctl_read | -5.275 | -2.521 |
| exec_spawn | -7.048 | -2.549 |
| path_diagnostics_strict | -7.990 | -2.836 |

For every specimen cell, final-pilot median R=15 ms and S=3 ms, while whole-run
operator medians were R=12 ms and S=2 ms. Operator C medians were 2–3 ms lower;
capture L medians were 1–5 ms lower. These observations do not isolate the
presence of an agent as a cause. The sample sizes, time interval and order
also differ, and the operator series itself changes over time.

Dividing the 132 rounds into four consecutive groups of 33 preserves n=33
for each cell in every quarter. First-to-last-quarter W medians were:

| Specimen | Capture W, first → last quarter | No-capture W, first → last quarter |
| --- | ---: | ---: |
| file_read_deny | 670.543 → 679.561 | 40.856 → 44.015 |
| mach_deny | 673.111 → 680.811 | 38.329 → 41.379 |
| sysctl_read | 671.555 → 679.585 | 37.194 → 40.204 |
| exec_spawn | 671.846 → 680.126 | 39.091 → 42.109 |
| path_diagnostics_strict | 670.564 → 679.390 | 38.661 → 41.744 |

In every specimen cell, quarter-median R was 12 ms in quarters 1–3 and 15 ms
in quarter 4; S was respectively 2 ms and 3 ms. Thus the late operator series
returns to the pilot's median host-wait values without changing outcome words.
The operator's reported return and waking interaction near the end is a
possible explanatory condition. No exact interaction timestamp is available,
so it cannot be aligned with the timing shift, and its causal contribution
is not established. The mechanism remains unresolved: scheduling, timer
behavior or other workload differences are also possible interpretations.
Starting no applications does not establish that system/session work was
unchanged. The fixed order and absence of continuous environment observations
prevent separating those explanations. All four quarter distributions remain
in the analysis; none is excluded on the basis of the retrospective account.

## Instancing observations and PID correction

No operator invocation reported `already_ran` or an XPC error, including the
660 no-capture specimen runs. There were 1,320 distinct recorded worker PIDs
across the 1,320 specimen runs. This establishes the observed workers and
outcomes, not an impossibility of meeting a retiring host.

The interactive overlap pilot contained ten pairs of `sysctl_read` runs,
20 completed `ok` observations and 20 distinct worker PIDs. Its W median was
43.911 ms and p90 44.632 ms; pair members were concurrent, not independent
repetitions. No overlap observations were added to the operator series.

The earlier pilot brief incorrectly called `runner_result.pid` a host PID.
`CWorkerOrchestrator.swift` selects the worker PID after launch and can select
the host PID before launch. Successful replies here therefore do not expose
an independent host identity. Summary format 2 calls the field
`runner_result_pid`, retains the explicit subprocess `worker_pid`, and makes
no distinct-host count. The reader correction and re-export check are recorded
in `reader-correction.json`: only the PID label, summary version and its
explanation changed; timing statistics, counts and exclusions are identical.
Original exports remain in commit `1fb5a52`; all raw files are unchanged.

## Interpretation and unresolved boundaries

The recorded L interval is much larger than C in these capture cells, and
capture/no-capture wall spans differ accordingly. This identifies a real,
measured supplementary-collection interval in the existing application. It
does not establish that its cost is unnecessary or recommend removing it.
L′ shares L's start; it does not isolate OS store-open or scan time, and
`captured` does not certify completeness of OS log delivery.

The ready and sentinel distributions show the host's recognition timing and
its variation during the interval. Existing fields do not locate compilation
completion, byte arrival within a polling quantum, individual query/attempt
costs or exact worker-exit time. Successful exit, a permission-shaped failure
or matching prediction does not supply those missing events or a sandbox-cause
claim. Controller CPU also cannot account for the full launchd-owned process tree.

This first cycle provides a reproducible account of ordinary built-in runs,
with pilot differences, time-order variation and outcome accounting intact.
External-runner throttling/re-acquisition, multi-phase behavior, constructed
log queries and instrumented stage timing remain outside its scope. No
application modification, optimization proposal or batch-throughput estimate
follows from these data. The completed report, procedure and evidence remain;
the execution plan is removed at closeout as it specified.

# Build 841: measurement brief and operator handoff

This brief records the pilot measurements and procedure used for the completed
first operator-run interval. PolicyWitness, its build and its five source
fixtures are unchanged. The first cycle's findings are in
`RUNTIME-INVESTIGATION-REPORT.md`; the pilot observations below remain distinct
from the operator-run measurements.

## Executable and conditions

The measured executable is
`dist/PolicyWitness.app/Contents/MacOS/policy-witness`, version 0.3.2, build
841, commit `8b2e5c93b12e637e8f7d21d321efe81c7d76cf04`, describe
`v0.3.2-50-g8b2e5c9`. The repository initially stood at
`6751cbb31fa50291081e4c57190383d72469b085` with a clean tree; its differences
from the app's source revision were the performance records and `.gitignore`.
The app's default inspection compilation flavor is the one specified in the
plan. Each manifest retains the executable's version response and SHA-256
observations for the controller, evidence manifest and every manifest entry.
The operator configurations pin those same bytes, beyond checking build 841.

The live pilots ran outside the automation sandbox. Conditions reported
macOS 26.7.1 (25G241), arm64, AC power and a charged battery. The start/end
`pmset -g therm` outputs said no thermal warning, performance warning or CPU
power status had been recorded; they do not supply a temperature or a numeric
thermal-pressure measurement. The Codex app-server daemon was present. No
other executable name matching `app-server` was observed; the custom server's
exact executable name has not been supplied, so its absence is not established
by that broad match alone.

The operator reported power connected, other applications mostly closed,
possible incoming calls, and expected screen locking/dimming. These are
conditions and possible interruptions, not proof of an otherwise quiet system.
The idle-sleep assertion launched and was still running when released in the
live pilots. No invocation's raw-clock pair detected system sleep. Screen
locking and display dimming remain allowed. No system setting was changed.

## Measures and interpretation

All duration summaries use milliseconds. Host wait records have whole-ms
resolution; the ready/grace polling quantum is 10 ms and sentinel polling is
2 ms. Their durations describe host recognition, not exact worker event times.

| Measure | Start and end | Observer / clock | Limit |
| --- | --- | --- | --- |
| W | Harness clock immediately before controller launch through `wait4` collection | Harness / `CLOCK_MONOTONIC_RAW`, paired with `CLOCK_UPTIME_RAW` | Includes launch and exit-observation overhead, all controller work and optional logs. |
| C | Controller clock before Swift-client spawn through collected client exit | Controller / Unix wall clock, ms | Includes client startup and XPC work; two readings cannot prove clock continuity. |
| R | Host ready-pipe polling begins after policy transfer through recognized stop | Host / `CLOCK_MONOTONIC` | Not sandbox compilation duration or byte-arrival time. |
| S | Sentinel polling interval minus the recorded synchronous phase-hook exclusions | Host / `CLOCK_MONOTONIC` | Recognition and polling work, not individual attempt durations. |
| X | Sum of the phase-hook intervals excluded from S | Host / `CLOCK_MONOTONIC` | Combines planning, validator and collection work; no spawn/query decomposition. |
| G | Host grace polling after the exit-request store through reap/error/deadline | Host / `CLOCK_MONOTONIC` | Does not show when the worker exited or whether it read the request. |
| L | Shared log budget creation before observer launch through outer supervisor finish | Controller / `CLOCK_MONOTONIC` | Excludes subsequent controller parsing/correlation and says nothing about OS log completeness. |
| L' | The same shared budget start through inner child-supervisor finish | Observer / shared `CLOCK_MONOTONIC` origin | Includes observer startup; not a standalone `log show` measurement. |
| E | Envelope construction stamp | Controller / Unix wall clock | A timestamp, not print completion or a duration. |
| U | Kernel user+system accounting returned by controller `wait4` | Harness / kernel rusage | Controller and reaped descendant accounting; excludes launchd's host/worker/validator tree. |

The definitions follow `controller/src/runner_client.rs`,
`controller/src/log_capture.rs::finish`, `controller/src/sandbox_log.rs`,
`controller/src/run_flow.rs`, and
`runner/Sources/PWRunnerCore/{CWorker,MonotonicDeadline}.swift`, unchanged from
the app's source revision. In particular, the two log elapsed fields share
their start; neither brackets controller parsing after supervision returns.

The summary retains C−R−S−G (which includes X), C−R−S−X−G, and W−C−L.
They are arithmetic residuals across clock domains, not measured component
costs. Rounding and wall-clock discontinuity can affect them. Negative values
are retained. Explicitly unentered grace contributes zero only to residual
arithmetic; disabled log capture likewise contributes zero there while L/L'
remain inapplicable. The version control contextualizes startup and its small
response; its wall time is not subtracted from runs.

Missing/null, wrong-type and clock-faulted fields are counted per observation;
valid observations of the same measure remain. Wide variability never causes
exclusion. Completed nonzero app exits remain observations in their own outcome
strata. Interrupted, timed-out, unresolved and sleep-affected invocations are
listed separately. An unavailable measure is not a zero. The p90 is nearest
rank, so with n=5 it equals the sample maximum.

## Pilot evidence

The initial full pilot was `20261023T201755491161Z-pilot`; the final harness
verification pilot was `20261023T202250234510Z-pilot`. Each contains 15 labeled
warm-ups (three for each capture cell) followed by five rounds of 11 cells,
55 ordinary observations. The controller's unmeasured version preflight is
recorded separately. Warm-ups do not prove that every possible first-execution
effect has vanished.

Both pilots completed all 70 entries, with complete checksum coverage, no
sleep exclusions, no absent/invalid applicable measures, and no negative
residuals. All 100 non-warm-up specimen runs across the two pilots reported
`ok`; none reported `already_ran` or an XPC error. All enabled log captures
reported `captured`. These are envelope observations, not claims that
predictions and enforcement agree.

Final pilot W, n=5 per cell, excluding warm-ups:

| Specimen | Capture median / range, ms | No-capture median / range, ms |
| --- | ---: | ---: |
| file_read_deny | 675.582 / 660.356–682.383 | 43.905 / 43.870–44.020 |
| mach_deny | 677.914 / 675.201–682.455 | 41.386 / 41.208–41.427 |
| sysctl_read | 677.255 / 676.023–680.336 | 39.790 / 39.662–39.926 |
| exec_spawn | 680.394 / 676.911–686.555 | 41.794 / 37.465–41.876 |
| path_diagnostics_strict | 679.983 / 676.537–691.118 | 41.589 / 41.487–41.840 |

The version cell median was 2.061 ms (n=5). The initial pilot's capture medians
were 679.604–685.567 ms across specimens; the final pilot's were
675.582–680.394 ms. These separate series are retained rather than pooled.
That difference is not attributed to a particular background activity.
The final pilot's ready-wait medians were 15 ms, S medians 3 ms, X medians
0–1 ms and G medians 0 ms. Ready waits ended `received`, sentinel waits `done`,
and grace waits `reaped_during_grace`. A zero whole-ms G or X is not proof of
zero work. The retained fields cannot decompose compilation, validator startup,
query execution or log-store opening.

Overlap pilot `20261023T201905645635Z-overlap` contains ten pairs of concurrent
no-capture `sysctl_read` invocations: 20 completed `ok` observations and 20
distinct worker PIDs, with no XPC error,
`already_ran`, missing applicable measure or sleep exclusion. Its W median was
43.911 ms and p90 44.632 ms. Pair members are concurrent observations, not
independent repetitions. This establishes only what these ten pairs did;
overlap remains interactive-only and is absent from operator manifests.

On this successful path `runner_result.pid` is the worker PID. It cannot
establish a separate count of host processes. Summary format 2 preserves that
field as `runner_result_pid` without assigning it a host role.

The original raw directories under `records/performance/runs/` were gitignored
and are not retained. The corresponding `evidence/<run-id>/`
directories hold manifests, conditions, checksums and summaries; the control
batch directories retain each run's external terminal records. Their checksum paths refer to the full raw directory; the exported
metadata directory is not a complete copy of the raw evidence.

## Verification and bounds

`20261023T202136980588Z-synthetic-controls` records successful identity refusal,
in-flight interruption, both timeout sources, cleanup exhaustion, checksum
mismatch rejection and telemetry interpretation controls. The deadline
stand-in ignored SIGTERM, so both actual signal attempts were observed. The
ceiling control ended before its shortened eight-second ceiling; the
cleanup-exhaustion control returned 3 and kept a valid partial attestation.

`20261023T202250234510Z-live-controls` records the clean-environment full
pilot, independently recomputed W medians, an identical fresh-shell summary,
a missing-request exit 2 followed by continued execution, an 11-invocation
short-configuration rehearsal, and Ctrl-C during a live pilot. The latter
retained one interrupted invocation and 69 never-started entries. The
controller was reaped; its status explicitly leaves XPC descendants to their
own budgets. Application failures never trigger silent retries.

The first synthetic attempt, `20261023T201617807617Z-synthetic-controls`,
failed because kqueue is not a Python context manager. Its run records a
harness error and three never-started entries; it is not runtime evidence.
The implementation uses `contextlib.closing` now. Later sandboxed controls
passed but recorded denied machine probes; the unsandboxed repetition
`20261023T201705144042Z-synthetic-controls` collected those probes. Every
attempt remains intact. The final synthetic credit precedes additions only
to the live-control branch and its live interrupt trigger; the synthetic
paths and the measured harness were unchanged by those additions.

The final 70-entry pilot's cleanup took 0.067 s against a 10 s reserve and
attested 296 files. That is measured small-run evidence, not a guarantee for
larger file sets. Cleanup has a bounded incomplete path: terminal facts first,
bounded probes, assertion release, incremental hashes, then the final
`run.json` bytes hashed last. The checksum control verifies that this final
record is actually attested. A partial list covers only its named files.

| Configuration | Rounds / invocations | Pilot-sized work | Hard-finish ceiling |
| --- | ---: | ---: | ---: |
| short | 132 / 1,452 | 478.9 s, about 8 min | 600 s |
| standard | 396 / 4,356 | 1,436.6 s, about 24 min | 1,800 s |

Sizing uses the initial pilot's median complete round span of 3.627728 s,
including inter-invocation bookkeeping. The final pilot remained in the same
range, so the configuration was not resized. The 5 s start margin exceeds
the largest initial-pilot W (0.906 s). No new invocation starts inside the
margin plus reserve. The effective deadline is the smaller of 300 s and the
time remaining before the reserve, and its source is recorded. The ceiling
governs harness decisions and supervised waits; an OS scheduling or filesystem
stall cannot be converted into a real-time guarantee. Control transcripts
retain actual outer elapsed times.

## Operator procedure

This is the historical build-841 procedure. It requires the original
application and inputs described in the harness README; its capture comparison
does not run against maintained PolicyWitness.

End active agent sessions, then use a normal Terminal in the repository root.
The first short interval is sufficient for the next analysis. Keep background
servers in their launch state and note any observed change or interruption.
The procedure needs no interaction. One Ctrl-C stops the series safely.

This block selects a fresh UTC run name and retains the exact terminal outputs
and observed exit status outside the immutable raw directory:

```sh
cd /Users/raccoon/Desktop/Security/PolicyWitness
pw_measure_id="$(date -u +%Y%m%dT%H%M%SZ)-short-b841"
pw_measure_terminal="records/performance/evidence/${pw_measure_id}-terminal"
mkdir "$pw_measure_terminal"
printf 'Raw output: records/performance/runs/%s\n' "$pw_measure_id"
tests/lib/python.sh records/performance/harness/measure.py \
  --config short --expect-build 841 --run-id "$pw_measure_id" \
  --out records/performance/runs \
  > "$pw_measure_terminal/stdout.txt" 2> "$pw_measure_terminal/stderr.txt"
pw_measure_status=$?
printf '%s\n' "$pw_measure_status" > "$pw_measure_terminal/exit-status.txt"
printf 'Exit status: %s\n' "$pw_measure_status"
```

Exit 0 means manifest exhaustion and complete cleanup, not that every app
invocation succeeded. Exit 1 means an early loop stop with cleanup complete;
2 is preflight refusal; 3 means incomplete cleanup or a later write failure.
Preserve all output in every case. Add a short operator note alongside the
terminal records, including “no events noticed” if appropriate. Do not edit
the raw directory to add it. Return the printed raw directory and terminal
record location for analysis after the procedure has exited. No agent should
remain attached to supervise the interval.

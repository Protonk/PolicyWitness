# Log observer investigation: pilot plan

Status: both authorized pilots are complete. The
[report](LOG-OBSERVER-INVESTIGATION-REPORT.md) retains their separate results,
evidence, controls and unresolved questions. No further live run is scheduled.
The procedure below is historical and requires the original build-841
environment. Source links use the pinned pre-retirement archive; the maintained
application has no collector. The harness README states the reproduction
requirements.

This implements the [investigation brief](PolicyWitness-Log-Observer-Investigation.md).
The [previous report](RUNTIME-INVESTIGATION-REPORT.md) and
[measurement brief](RUNTIME-MEASUREMENT-BRIEF.md) supply the comparison and
definitions, not an expected result or a performance target. The deliverable
after live observations is `LOG-OBSERVER-INVESTIGATION-REPORT.md`: collection
path, cost distributions, record-set comparisons, controls and open questions.
An optimization or redesign proposal is outside this investigation.

## Current artifacts and historical selection

Preparation rereads the version, verifies all 12 application identity files
against the earlier run's pinned bytes and the embedded manifest, checks that
controller/runner source matches the application's source revision, and hashes
the current `/usr/bin/log`. The current app is still 0.3.2 build 841, source
`8b2e5c93b12e637e8f7d21d321efe81c7d76cf04`. No application file was modified or
rebuilt. The [prepared configuration](log-observer/pilot-config.json) pins these
identities, the actual historical query and the harness/source dependencies.
Launch refuses changed dependencies or artifacts; changing the configuration
requires explicit preparation and review of the new identities.

The historical anchor is invocation 00002, `mach_deny`, of
`20261023T212050Z-short-b841`. Its original capture contains one parsed denial.
The selected envelope and the old manifest verify against their raw checksums.
Preparation also verifies all 660 capture envelopes before deriving this table:

| Existing specimen | Captures with no parsed denial | Captures with one parsed denial |
| --- | ---: | ---: |
| file_read_deny | 16 | 116 |
| mach_deny | 5 | 127 |
| sysctl_read | 132 | 0 |
| exec_spawn | 132 | 0 |
| path_diagnostics_strict | 20 | 112 |

These are parser observations from saved captures, not emission or completeness
claims. A counted output line can be a header: invocation 00001 has
`observed_lines: 1` but zero parsed denials. The choice of `mach_deny` uses
existing positive observations without promising a future record. Its existing
fixture attempts `bootstrap_look_up` of `com.apple.logd` under denied
`mach-lookup`; it is copied unchanged for each pilot run.

The old full raw run and all new raw runs are gitignored, local-only files under
`records/performance/runs/`. The checked-in metadata and checksums do not supply
portable copies of those files. Historical retention in the live log store
remains untested until the pilot.

## Collection path and timing boundaries

Source audit:

| Step | Existing source | Measurement consequence |
| --- | --- | --- |
| Complete execution, then select worker PID/client interval | [run_flow.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/run_flow.rs), `attach_sandbox_logs`, `collect_log_evidence` | Supplementary queries cannot change the native execution evidence. Successful replies expose the worker, not an independent host PID. |
| Round client milliseconds outward and pad two seconds on each side | [sandbox_log.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/sandbox_log.rs), `SandboxLogWindow::runner_client_span` | Query endpoints are wall-clock bounds; backwards spans are invalid. Padding may extend beyond the time an immediate query starts. |
| Create monotonic budget, launch observer in owned group | [sandbox_log.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/sandbox_log.rs), `capture_sandbox_logs_with_timeout` | L starts before observer launch. The controller passes a shared 10 s default budget. |
| Parse observer arguments, build predicate and `/usr/bin/log show` command | [sandbox-log-observer.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/bin/sandbox-log-observer.rs), `sandbox_predicate`, `log_show_command`, `main` | No separate observer-startup or log-spawn duration is exposed. Ordinary query uses syslog style, info/debug, exact bounds and a complete process-name/PID regex. |
| Spawn log child, read bounded pipes, observe exit and clean up | [log_capture.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/log_capture.rs), `capture_with_ops`, `finish` | Inner elapsed L′ ends here and shares the controller budget origin. It does not isolate log execution, store opening or scanning. Inner supervision reserves 1 s for reporting. |
| Decode and parse log output; serialize observer report | [log_show.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/log_show.rs), `capture_show`; observer `main` | This occurs after L′ is recorded. The observer retains raw text plus parsed events. A report with `result.ok: false` can still have process exit 0. |
| Finish outer supervision, parse/admit observer reply, correlate, assemble envelope | `log_capture.rs::finish`, `sandbox_log.rs::parse_supervised_observer`, `run_flow.rs::finish_sandbox_log_capture` | L ends before controller parsing/correlation. Those operations still consume the shared allowance, but their individual durations are not exposed. |

`captured` requires successful transport, admitted shape/window and completed
processing. Neither it, observer `result.ok`, nor direct log-tool exit 0 proves
complete OS delivery. No instrumentation is needed to begin the pilot; consider
it later only if an unresolved interval prevents a useful comparison.

## Pilot A: fixed historical cost comparisons

Six conditions use the pinned historical worker identity and syslog output:

1. The exact original padded interval and predicate.
2. A 60-second interval ending at the same endpoint, with the same predicate.
3. The original-width interval shifted 60 seconds earlier, with the same predicate.
4. Original interval, adding a literal `Sandbox:` prefilter to the original regex.
5. Original interval with `FALSEPREDICATE`, deliberately requesting no matches.
6. Original interval with a regex for all `pw-probe-runner` PIDs.

Each condition runs once through the existing observer and once through the
direct log tool in each of two blocks: 24 invocations. Block 1 uses the listed
condition order and observer/direct method order; block 2 reverses both. There
are no discarded warm-ups, and the first query is not assumed to be cold.
The broadened predicate remains restricted to PW workers in the small original
window. No unrestricted log extraction is planned.

The methods use identical OS query arguments per condition. Both are consumed
through bounded pipes, but the observer uses its native supervisor and emits
JSON, while direct output is consumed by the Python harness. Standalone observer
budget creation happens after its argument parsing, unlike the controller's
shared origin. Observer parsing/serialization and these supervision differences
mean a difference in whole invocation duration is not pure wrapper overhead.

Record output bytes and content separately from predicate/window changes.
These six cells can reveal useful contrasts; they cannot independently identify
the effect of output quantity if selectivity also changes. No linear scaling,
causal small-difference claim, or prospective speedup is inferred from n=2.

## Pilot B: fixed events inspected at different delays

Two blocks each contain four fresh `mach_deny` executions:

| Cohort | Queries after the same execution |
| --- | --- |
| repeated | nominal delays 0, 2 and 10 s |
| first_0 | first and only query at nominal delay 0 s |
| first_2 | first and only query at nominal delay 2 s |
| first_10 | first and only query at nominal delay 10 s |

The second block reverses cohort order: eight executions and twelve queries
total. All execute with `--no-log-capture`, preventing an unrecorded earlier
query, and `--timeout-ms 5000` to bound abnormal execution. The shorter execution
budget is an explicit departure from the earlier 240 s default. Fresh events
are comparable executions, not identical underlying events or independent
machine trials. Repetitions never rerun the specimen.
First-query means the first query this procedure makes for that execution's
fixed interval. Earlier queries of other intervals, including pilot A, may have
affected shared logging state; this does not establish an untouched store.

Direct `/usr/bin/log show` is used for these observations, with production
predicate, syslog/info/debug flags and reconstructed production padding held
constant for each original worker/client interval. A missing authoritative PID,
unsupported envelope or reversed span produces a named unqueried entry. An
execution failure with an otherwise usable identity remains an observation.
The specimen's result and collector result remain separate.

Delays originate at harness `wait4` collection of the controller's exit, not at
an assumed kernel-event emission time. Each query records Popen entry, spawn
return, exit observation, wait4, wall-clock timestamps and raw monotonic/uptime
readings. Actual launch/finish delays are derived from these observations;
overruns remain visible rather than being called on-time. These bracket
subprocess execution, not the exact exec or kernel exit instant. No queries run
concurrently; a long earlier query can delay a later nominal deadline.

Exact raw-byte line sequences, hashes, multisets and duplicate counts establish
what changed, including order. Whole output and the complete worker-token subset
are compared separately. Headers/footers stay in full comparisons. Syslog text
provides no stable record identity here: a changed line appears as a removal and
addition, not a proven mutation of the same OS record. Original text remains
available locally to inspect ambiguous pairs. Observer text may be lossy on
decode failure; such outcomes remain distinct. Empty or stable output never
establishes completeness, and later output need not contain all earlier output.

## Bounds, evidence and verification

The runnable procedure is [pilot.py](log-observer/pilot.py); commands and output
layout are in [the harness README](log-observer/README.md). It holds the existing
checkout lock, checks pinned identities, creates a fresh mode-0700 raw directory
under a 077 umask, copies its specimen and scripts, and records an explicit
execution-condition note. It uses an idle-sleep assertion while allowing display
lock/dimming. Agent activity is allowed and declared. Endpoint probes and query
sequence/elapsed times remain evidence, not a continuous quiet-machine claim.

The whole procedure has a 180 s ceiling including a 10 s cleanup reserve.
Nominal external allowances are 12 s for the standalone observer, 9 s for direct
queries, and 15 s for a controller invocation. Effective allowances shrink at
the ceiling and retain their source. Group cleanup has 1 s; no new work starts
inside the cleanup reserve plus 2 s admission margin. Pipe caps are 1 MiB direct
stdout, 32 MiB observer/controller stdout, and 128 KiB stderr. The native
observer's own limits and 10 s budget also apply. Conditions near a cutoff are
not equivalent between methods and are reported separately.

The harness keeps its child leader unreaped through its final group signal,
then records wait4 and probes for group absence. An exited leader with an
inherited pipe writer does not end capture. At cutoff the harness closes its
pipe readers and kills its owned group; a producer can observe pipe closure
before that signal. Unconfirmed cleanup stops the series. Launchd-owned XPC
processes are outside this group and retain their requested 5 s runner budget;
group absence does not claim those descendants were reaped by the harness.

Every invocation retains arguments, environment, metadata, stdout/stderr and
status immediately. Cleanup reuses the earlier verified finalizer: terminal
facts first, bounded end probes, assertion release, incremental checksums and
final `run.json` attested last. Partial coverage and incomplete cleanup survive.
Clock/deadline decisions do not guarantee real-time OS scheduling or filesystem
completion. Exit 0 means schedule exhaustion and complete cleanup, not that
every query succeeded; early stop is 1, pre-creation refusal 2, incomplete
cleanup or a post-creation write failure 3.

The reader verifies listed hashes before exporting. Uncovered files are named,
mismatches refused, and failure/sleep/clock/observer outcomes stratified. Each
query's raw wall span includes harness work; `process_wall_ms` spans Popen entry
through wait4, while `wall_ms` additionally includes setup and group probing.
Both include pipe handling and are distinct from native L′. Derived evidence
contains content hashes rather than raw log extracts; content-level claims
require the retained local raw files. Inspect the export before committing it.

Final stand-in verification is
`evidence/20261023T230543377500Z-log-preparation-controls/controls.json`.
It covers normal/nonzero output, timeout, overflow, inherited pipe writers,
actual SIGINT, failed launch, exact-content comparison, malformed identity,
checksum rejection, incomplete attestation, failed observer report with exit 0,
all 44 driver entries with shortened delays, and a shortened whole-run ceiling.
The full driver attested 192 files; the ceiling control retained one timed-out
invocation and 43 never-started entries, exited 1, and completed cleanup before
3.5 s. These are harness controls, not live OS log or event-availability evidence.
The initial failed control (an import collision with the old summarizer) and
superseded successful controls remain intact with their source hashes. The
final check repeated the same stand-in command outside the automation sandbox
after the sandbox denied machine-condition probes. No live
specimen or log query was executed during preparation.

## Decisions after the pilot

Inspect raw records and all outcomes before expanding the schedule. If the
historical query is now empty, retain that result and explicitly choose any new
anchor in a later series; do not silently replace windows. If fresh observations
are all empty, the pilot establishes a retrieval limit, not absence of events.
Any policy, window, predicate, format or delay refinement forms a separately
identified condition. Broaden only when the pilot makes the next comparison
interpretable. Instrument only a consequential unresolved boundary. A finished
report may conclude that available observations do not distinguish competing
explanations.

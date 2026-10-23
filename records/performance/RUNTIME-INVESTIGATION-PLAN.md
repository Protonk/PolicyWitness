# Runtime investigation, first cycle: the built-in runner under existing telemetry

Plan for the investigation that
[PolicyWitness-Runtime-Exploration-Guide.md](PolicyWitness-Runtime-Exploration-Guide.md)
calls for, scoped to one cycle. The questions come from
[PolicyWitness-Boundaries-Findings.md](PolicyWitness-Boundaries-Findings.md),
whose source text is the read-only report of 2026-10-23 at
`.tmp/READ-ONLY-PERF-REPORT.md`, a scratch file available only in the local
checkout. Prepared 2026-10-23 at `35a4987`.

## Problem

PolicyWitness has never been timed as a running program. The only numbers
about its runtime are the medians the read-only report mined from test-battery
envelopes: a client span near 49 ms, a unified-log scan near 800 ms, host waits
of 10 to 15 ms that end `received` on the first poll. Those numbers describe
battery runs of earlier builds, under the harness's own conditions, read out of
fields whose start and end events the report did not establish. The synthesis
shows that several events an envelope describes do not coincide: the host
replying, the controller receiving, log collection ending, the worker being
reaped, the envelope being printed. A credible account of runtime behavior has
to say which of those events each number sits between, who observed it and on
which clock, before any duration is read as the cost of the activity inside it.

## Intended result

The prepared handoff and pilot evidence are described in
[RUNTIME-MEASUREMENT-BRIEF.md](RUNTIME-MEASUREMENT-BRIEF.md).
The executable procedure is documented in [harness/README.md](harness/README.md).
All existing runs are interactive pilots or controls; operator measurements
and the final runtime report remain pending.

A reproducible account of one ordinary invocation of the built-in runner,
built from the telemetry the shipped envelope already carries plus one
harness-observed wall clock around the controller process, under conditions
the operator can hold constant and the record can describe. It consists of:

- A measurement brief naming each measure's start event, end event, observer,
  clock domain and what the duration does not establish.
- A standalone procedure the operator launches from a normal terminal, which
  runs a fixed manifest of invocations against a named executable, preserves
  every raw output and status, and stops on its own.
- Raw evidence for every invocation, kept locally, and committed manifests,
  conditions, terminal records, checksums and summaries per run.
- A runtime report separating observed facts, interpretations and unresolved
  questions, with sample sizes and variability for each claim.

PolicyWitness is not modified. No speedup is proposed. The report may conclude
that a cost is real and necessary, or that the retained fields cannot locate
an event the question needs.

## Decisions already taken

These were settled with the operator before this plan was written and are not
reopened by it.

- **Executable.** The app under `dist/` was rebuilt from clean `8b2e5c9` on
  2026-10-23 at 19:31:34Z: version 0.3.2, build 841, describe
  `v0.3.2-50-g8b2e5c9`, `dirty: false`, signed with the Developer ID. The
  earlier build 838 carried `586ddd4-dirty` and was replaced so that no
  measurement inherits an inferred source identity. The build is the default
  inspection flavour, Swift at `-Onone -g`, Rust at `opt-level=1` with debug
  info and frame pointers, C helpers at `-O2`; releases use the same default,
  so this flavour is the one users run. Its binaries are new files, and their
  first executions carry Gatekeeper's first-exec latency; the pilot's warm-up
  invocations exist for that reason and stay labelled as such.
- **Evidence home.** Everything about this investigation lives under
  `records/performance/`. The procedure and its summaries, each run's
  manifest, conditions, terminal record and checksums are committed. Raw
  per-invocation output goes under `records/performance/runs/`, which
  `.gitignore` excludes; the records that cite it state that it is local-only,
  as [records/AGENTS.md](../AGENTS.md) requires. The layout is in
  [README.md](README.md).
- **Scope.** Built-in runner only. No external (BYOXPC) runner is installed on
  this machine, and installing one would create a user-scope LaunchAgent, a
  registry entry and removal obligations that outlive the session. The
  throttle floor, re-acquisition and external caller authorization questions
  wait for a later cycle.
- **Operator time.** Unattended intervals of about 10 minutes are easy, about
  30 minutes sparingly available, and anything over an hour belongs to a later
  phase in which the operator runs a prepared procedure and returns with the
  results. The procedure therefore ships with configurations sized to those
  intervals and a hard wall-clock ceiling, cleanup included, that ends it
  inside them.
- **Background servers.** The two the guide mentions are the Codex app-server
  daemon, running from `~/.codex/packages/app-server-daemon/`, and a second
  custom app server that is now stopped. The procedure records the presence
  of both by process name at start and end and does not change them.

## Approach

### 1. What one invocation retains, and what the harness adds

The envelope's timing-bearing fields were confirmed in a battery envelope from
`tests/out/runs/release-0.3.2-default` and in source. Each measure below names
the events it sits between. "Host" means the XPC service process; its waits
are elapsed monotonic allowances from `HostWaitClock` in
[CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift).

| Measure | Starts | Ends | Observer and clock | Does not establish |
| --- | --- | --- | --- | --- |
| W, harness wall span | Harness reads its clock immediately before spawning `policy-witness` | Harness collects the controller's exit | Harness; `CLOCK_MONOTONIC_RAW` with a `CLOCK_UPTIME_RAW` pair for sleep detection, as the dispatcher does | Anything about stages inside; includes spawn cost, controller startup, dossier, render, and the whole log scan |
| C, client span | Controller reads wall clock before spawning the Swift client (`runner_client.started_at_unix_ms`) | Controller reads it after collecting the client's exit (`ended_at_unix_ms`) | Controller; Unix wall clock in ms | Host launch time separately from client startup; nothing about clock continuity in between |
| R, ready wait | Host finishes writing policy bytes and starts polling the ready pipe | Host recognizes a byte, EOF, error or deadline (`runner_subprocess.ready_wait`) | Host; monotonic, 10 ms sleep quantum | Compile duration; the byte's arrival time within the quantum |
| S, sentinel wait | Host starts polling shared memory after the ready wait | Host recognizes `done` or another stop (`sentinel_wait.elapsed_ms`, less `excluded_ms` of phase collection) | Host; monotonic, 2 ms quantum | When the worker published; attempt durations individually |
| X, phase collection | Host observes phase arrival and begins planning | Collection closes (`sentinel_wait.excluded_ms`, per-phase `validator_subprocess`) | Host; monotonic | Validator spawn versus query time; what `sandbox_check` itself cost |
| G, exit grace | Host stores `exit_requested` | Host recognizes the reap or exhausts the grace (`exit_grace_wait`) | Host; monotonic, 10 ms quantum | Worker exit time; whether the worker read the request |
| L, log supervision | Controller starts the shared collection budget before launching the observer (`sandbox_log_capture.supervision`) | Supervisor finishes collecting/reaping the observer (`supervision.elapsed_ms`), before controller reply parsing and correlation | Controller; `CLOCK_MONOTONIC` budget | Total log processing cost; OS delivery completeness; which records existed at the time |
| L', inner log collection endpoint | Same controller budget start as L, carried into the observer | Inner child supervision finishes (`observer.data.collection.elapsed_ms`) | Observer; shared `CLOCK_MONOTONIC` budget | A standalone `log show` duration: observer startup is included; store open versus scan cost |
| E, envelope stamp | Not a span: `generated_at_unix_ms` is read when the envelope value is built | | Controller; Unix wall clock | Print completion; the controller's exit |
| U, controller CPU | Spawn | Exit (`wait4` rusage) | Harness; kernel accounting for the controller and the children it reaped: client, observer, `log show` | Host, worker, validator and issuer CPU, which launchd's service tree owns |

Residuals are derived, never measured. C minus (R + S + G) includes X because
S has had the phase collection excluded; the summary labels that residual
`client_residual_including_X`. C minus (R + S + X + G), also retained, covers
the remaining client, launchd, host authorization, decode, region setup,
spawn, policy transfer, assembly and reply work. W minus C minus L includes
controller startup, dossier, log reply parsing and correlation, render and
exit, together with harness spawn and exit-observation cost. When grace was
explicitly not entered its contribution is zero; missing grace evidence is
not silently zero. Disabled log capture contributes zero L to the residual,
while L itself remains inapplicable.

`policy-witness --version` observes startup plus its small version response;
it is not a mathematical lower bound for every later sample. The residuals
combine durations from different clocks, with millisecond rounding and
unproven wall-clock continuity; they do not identify individual component
costs. Negative residuals remain visible and require interpretation, never
exclusion merely because of their sign. `log_capture.rs::finish` establishes
the shared origin of L and L'; neither includes controller parsing after
supervision returns.

### 2. Specimens and cells

The five single-step fixtures under `tests/fixtures/pw_runner/` are the
specimen set: `file_read_deny` (allow default, one denied read),
`mach_deny` (a denied bootstrap lookup), `sysctl_read` (allowed sysctl),
`exec_spawn` (allowed spawn of `/usr/bin/true`, the exec budgets and child
reap) and `path_diagnostics_strict` (deny default, the profile that can deny
the worker's own exit). They reach different attempt kinds and both policy
defaults with one step each, so phase and step counts do not vary across
cells. Multi-step and multi-phase plans are out of scope this cycle.

Each specimen runs in two modes, with log capture (the default) and with
`--no-log-capture`. With the `--version` control that is 11 cells. The
procedure copies each fixture into the run directory at start and runs the
copies, records their SHA-256 in the manifest, and passes only the request
path and the mode flag; every other setting is the CLI default, including the
240,000 ms runner timeout and the 10,000 ms log allowance.

Cells are interleaved in a fixed round-robin order, one invocation of each
cell per round, so that drift across the interval reaches every cell alike;
the manifest records each invocation's sequence number for order analysis.
Invocations start as soon as the previous one has exited and its files are
closed. In the no-capture cells the next client reaches launchd some tens of
milliseconds after the previous host replied, inside or near the 50 ms host
exit delay (`host_exit_delay` in [LIMITS.md](../../docs/LIMITS.md)), so this
series incidentally observes whether consecutive built-in runs ever meet a
retiring host: an `already_ran` refusal, an XPC error, or neither. That is the
synthesis's F3 instancing question, probed by ordinary sequential use rather
than by a constructed overlap.

### 3. Stage 2: interactive pilots

Pilots run from this session against build 841, each bounded to a few minutes
of machine time, each producing a complete run directory of its own so nothing
is re-run silently.

- **P1, warm-up.** Three invocations of each cell with capture, labelled
  `warmup: true` in the manifest. They absorb first-exec latency on the new
  binaries and establish that every field in the table is present.
- **P2, pilot series.** Five rounds of all 11 cells, 55 invocations, about one
  minute. Checks: every field present for every cell; residuals non-negative;
  W for `--version` against W for a run; sleep detection reading
  zero; the no-capture back-to-back series free of `already_ran` or XPC errors,
  or showing them, either way recorded.
- **P3, overlap.** Interactive only this cycle. Two no-capture invocations of
  `sysctl_read` started together, repeated ten times, to see which of the
  outcomes above a concurrent start produces. The user guide says relative
  scheduling between concurrent runs is not guaranteed; the pilot records what
  happened, not a rule, and the report carries its ten pairs as pilot
  observations with that n. No admission rule is needed now. A later cycle
  may add an overlap series to an unattended manifest only if every pilot
  pair terminated within the deadline, every outcome fell in a closed set the
  summarizer classifies (`ok`, `already_ran`, a named XPC error) and the
  sequential series showed no retirement encounter. That establishes only
  that those sampled sequential invocations did not encounter retirement.
- **P4, procedure controls.** The harness's own verification, listed under
  Verification below.

The pilots decide two things recorded in the brief. First, which measures are
defined for which cells: a measure is dropped for a cell only when its field
is absent, null, of another type or carries `clock_fault: true`, and the drop
is named. Variability never drops a measure; it is part of what the
investigation characterizes, and the summary reports it stratified by the
outcome words each record carries. Second, the per-invocation cost that sizes
the unattended configurations.

### 4. Stage 3: the procedure

`records/performance/harness/measure.py`, run on the pinned interpreter the
repository already requires:

```sh
tests/lib/python.sh records/performance/harness/measure.py \
  --config short --expect-build 841 --out records/performance/runs
```

`tests/lib/python.sh` resolves Homebrew's `python@3.14` at its keg path and
refuses otherwise; the harness imports only the standard library. It takes no
input from the environment beyond the working directory, which it records, and
asks no questions.

Behavior, in order:

1. Refuse before starting if the app at `dist/PolicyWitness.app` reports a
   build number other than `--expect-build`, if the output run directory
   exists, or if any fixture is missing. The app is never built or changed by
   the procedure.
2. Create `runs/<run-id>/` with `run-id` as `<UTC stamp>-<config>-b<build>`.
   Write `owner.json` (pid, start wall time, both monotonic readings), copy
   the specimens, write `manifest.json` listing every planned invocation with
   sequence number, cell, specimen hash, argv and the configuration's bounds,
   then `conditions-start.json`: `sw_vers`, `uname -m`, `hw.model`, `hw.ncpu`,
   `hw.memsize`, power source and thermal pressure from `pmset`, the app's
   `--version` envelope, `git rev-parse HEAD` and `git status --porcelain`
   when git is available, the presence of the two background servers by
   process name, and the idle-sleep assertion's launch record.
3. Hold a `caffeinate -i -w <pid>` assertion in its own session, as the test
   dispatcher does, and record whether it launched. This blocks idle sleep
   only; it changes no configuration.
4. For each planned invocation in sequence: write `argv.json`, read both
   monotonic clocks, spawn the controller with stdout and stderr to
   `stdout.json` and `stderr.txt` opened fresh, wait with `wait4` under the
   invocation's effective deadline (below), read both clocks, and write
   `status.json`: state, exit status or signal, both clock deltas, sleep
   detected, rusage, byte counts. States are `completed` (exited, any status),
   `harness_timeout` (the effective deadline reached; SIGTERM, then SIGKILL
   after two seconds if still unreaped, signal attempts recorded with the
   deadline and its source), `interrupted` (the operator's SIGINT or SIGTERM
   arrived while it ran; the controller is left to finish or is killed, and
   the record says which) and `spawn_failed`. Nothing is retried. A nonzero
   exit is a completed invocation whose envelope says what happened.
5. Stop when the manifest is exhausted or when less than the cleanup reserve
   plus the start margin remains before the ceiling, whichever is first.
   Unstarted entries are written as `never_started` with the reason. On
   SIGINT the loop finishes the current invocation's record and stops the
   same way.
6. Cleanup, inside the reserve and ordered by what cannot be reconstructed
   later. First `run.json`, written atomically with the loop's terminal facts
   (counts by state, start and end, stop reason) and `cleanup.state:
   "started"`, so the loop's outcome is on disk before anything else runs.
   Then `conditions-end.json`, each probe under a 2 s subprocess timeout and
   the set under 5 s, written with whatever was collected and a per-probe
   state (`ok`, `timed_out`, `failed`). Then the idle-sleep assertion is
   released and its state recorded. Then `SHA256SUMS`, appended and flushed
   one file at a time over every file in the run directory except itself and
   the still-provisional `run.json`,
   with the clock checked before each file. Finally `run.json` is rewritten
   atomically with `cleanup.state: "complete"` or `"incomplete"`, each step's
   outcome, and for checksums the counts hashed and total. Its final bytes are
   hashed and appended to `SHA256SUMS` last, avoiding a stale attestation of
   the provisional record. A 150 ms final-write allowance is held inside the
   cleanup budget. If the reserve
   runs out, the remaining steps are skipped, never hurried; nothing already
   written is removed; a partial `SHA256SUMS` attests exactly the files it
   lists; and the final `run.json` write, which is small and always
   performed, names what was skipped. Per-invocation records never depend on
   cleanup: each `status.json` is written when its invocation exits. The
   procedure exits 0 when the manifest was exhausted and cleanup completed,
   1 when the loop was ended by the ceiling or an interrupt with cleanup
   complete, 3 when cleanup is incomplete, and 2 when it refused before
   creating anything. The pilot records how long cleanup took, and the brief
   states it beside the reserve.

Each configuration has a ceiling, a hard finish time counted from the
procedure's start and including cleanup; a cleanup reserve of 10 s inside it;
and a manifest sized to end by exhaustion at about 80 percent of the ceiling
at the pilot's per-invocation cost. The ceiling is the backstop, not the
expected end. Exact counts are set from P2 and recorded in the brief.

| Config | Ceiling, hard finish | Shape |
| --- | --- | --- |
| `pilot` | 3 min | P1 then P2 as above |
| `short` | 10 min | Round-robin over the 11 cells, rounds sized to about 8 minutes |
| `standard` | 30 min | The same shape, rounds sized to about 24 minutes |

The nominal per-invocation deadline is 300 s: above the 240 s runner timeout
plus the 11 s log allowance and grace, so a timeout at the nominal deadline
means the controller itself failed to stop. An invocation's effective deadline
is the smaller of the nominal deadline and the time remaining before the
reserve begins, and `status.json` records the effective value with its source,
`nominal` or `ceiling`, so a kill at the ceiling is never read as a hung
controller. No invocation starts when less than the reserve plus a start
margin remains; the margin is 5 s, raised above the pilot's largest W if that
is higher. Cleanup runs inside the reserve. The procedure's last write
therefore lands before the ceiling, with one exception the record would show:
a controller that does not die on SIGKILL. The harness manages only the
controller; the XPC host and its worker belong to launchd's service tree, and
a kill at the ceiling leaves them to their own budgets, which the status
notes.

A companion `records/performance/harness/summarize.py` reads a run directory
and writes `summary.json` and `summary.md`: manifest reconciled against
`status.json` files, counts per state, and per cell and per outcome stratum (the record's `stop` words, capture
status and exit status) the n, minimum, median, p90 and maximum of each
measure. It computes from completed invocations only, reports every excluded
invocation by sequence number and state, and counts per cell the measures it
could not read as `absent`, `invalid` (wrong type or `clock_fault: true`) or
`inapplicable` (undefined for the cell, as L and L' are under
`--no-log-capture`). It never edits the
run directory. It verifies every entry `SHA256SUMS` lists and refuses on a
mismatch; files the list does not cover are reported as `unattested`, and a
run whose `cleanup.state` is `incomplete` is summarized with that state and
the skipped steps carried into the summary.

### 5. Stage 4: the operator interval

The brief handed over before the interval contains the exact command, the run
directory the procedure will create, the number of planned invocations, the
ceiling as the hard finish time, how to interrupt (one Ctrl-C), and the statement that no agent
session should be active while it runs. The operator keeps the Codex
app-server in whatever state it has at launch; the conditions files record
that state at both ends. The operator notes anything they observed during the
interval in a short text file beside the run directory, or notes that they
observed nothing.

### 6. Stage 5: analysis and the report

Analysis begins only on a run whose `run.json` exists and whose listed
checksums verify; an incomplete cleanup is carried into the report as a
condition of that run, not repaired. The report, a record under `records/performance/`, gives for each
claim the cells and n behind it, the measure by its letter and events, the
spread, and the states excluded. It compares the pilot series with the
unattended series and reports disagreement as such. Interpretations and open
questions are separated as the guide requires. It proposes no change; if an
event the synthesis asks about cannot be located in the retained fields, the
report names the missing event and stops there.

### Where this stops

- No change to PolicyWitness's source, profiles, limits, schemas or build.
- No instrumented variant. If the pilots show that a question needs one, the
  report says what existing fields cannot establish and leaves the decision.
- No external runner, no multi-step or multi-phase specimen, no concurrent
  series in the unattended run, no interval over 30 minutes.
- No throughput estimate for batches. Per-invocation medians under these
  conditions are what the data supports.

## Alternatives rejected

- **Reuse `tests/lib/run_capture.py` as the harness.** It captures one CLI
  invocation well, but it is test infrastructure with harness intervention
  semantics, and importing it would make the procedure depend on the test
  library's conventions and on `tests/out/` ownership rules it was written
  for. A small standalone script with the same artifact discipline is simpler
  for an operator to read and run.
- **Run under the test dispatcher.** The dispatcher owns `tests/out/runs/`,
  takes the checkout lock and reports pass or fail per case. The measurements
  have no pass criterion, and their evidence belongs beside the records that
  cite it.
- **Timing `log show` directly across window widths and predicates.** The
  report's F1 asks for it, but it measures the OS tool outside PolicyWitness's
  ordinary work. The observer's standalone mode would keep it inside the app,
  yet `run` does not use that mode. Deferred; L and L' from ordinary runs come
  first.
- **A tracing or sampling profiler on the host.** It would answer the residual
  questions, and it would also change the conditions it observes and need
  separate approval as instrumentation.

## Verification

Of the procedure, before handover, each as its own small run directory kept
under `runs/` and summarized in the brief:

1. The `pilot` configuration completes from a shell started with `env -i` plus
   `PATH` and `HOME` only, so nothing in this session's environment is a
   dependency.
2. Interrupt control: Ctrl-C during a pilot leaves `run.json` with one
   `interrupted` and the rest `never_started`, and `SHA256SUMS` verifies.
3. Failure control: a manifest entry whose specimen path is removed after
   copying yields exit 2 with its envelope and stderr retained, no retry, and
   the series continues.
4. Deadline controls: `--pw` pointed at a stand-in that sleeps past a
   shortened nominal deadline produces `harness_timeout` with source
   `nominal` and both signals recorded; the same stand-in under a ceiling
   shorter than the nominal deadline produces source `ceiling`, and the run's
   last write precedes the ceiling. The stand-in is a script in
   `harness/controls/`, never the app.
5. Identity control: `--expect-build` set to another number refuses before any
   directory is created.
6. `summarize.py` on the pilot directory reproduces the counts and medians the
   session read by hand, from a fresh shell.
7. Cleanup-exhaustion control: a control flag that delays the conditions
   probes, under a reserve shortened below that delay, leaves the first
   `run.json` facts intact, `cleanup.state: "incomplete"` with the skipped
   steps named, a `SHA256SUMS` that attests only the files it lists, exit
   status 3, and a last write before the ceiling.

Of the measurements themselves, inspect before sizing the unattended run:
every measure in every cell where it is defined, the `--version` distribution
alongside each run's W, the signs of the residuals, and sleep detection.
Undefined or unreadable measures and any negative residuals are named in the
brief; valid variability remains. Pilot observations that overlapped system
sleep cannot size the ordinary no-sleep configurations.

Passes that would mislead, and what guards each:

- Spawn cost counted as controller time. The `--version` cell contextualizes
  startup; the report does not subtract it from run timings.
- First-exec latency on the new binaries read as steady-state cost. Warm-up
  invocations are labelled and the summary reports them separately.
- A quiet interval assumed because no agent was attached. The conditions
  files and the background-server presence checks are the record; the report
  claims only what they show.
- Identical envelopes read as identical runs. Durations are compared per
  measure and per clock domain; equality of final JSON is not a claim of this
  investigation.
- An unattended series that silently measured a different app. The identity
  refusal and the `--version` envelope in `conditions-start.json` pin it.

## What would require reconsideration

- The app under `dist/` is rebuilt or replaced before the unattended run. The
  procedure refuses on build number; the brief is reissued for the new build
  or the run waits.
- P2 finds a field absent, null, of another type or clock-faulted for a cell
  in ways the field's contract does not predict. That is a finding to record,
  and the cell's measure is dropped from the summary rather than repaired.
  Wide variability is not such a finding; it stays in the summary.
- P2 shows the no-capture series meeting `already_ran` or XPC errors. The
  series stays, the outcomes are counted, and the report treats them as the
  first observation on the instancing question rather than as noise.
- The pilot's per-invocation cost is far from the report's medians, so the
  `short` and `standard` shapes no longer fit their intervals. Resize from the
  measurement and say so; do not trim the ceiling.
- System sleep is detected during a run. Affected invocations are flagged in
  the summary and excluded from medians by state, with the count reported.

## Closeout

When the report is committed, delete this plan. The two source documents, the
harness, the committed evidence per run and the report remain under
`records/performance/`; the `.gitignore` entry for `runs/` remains.

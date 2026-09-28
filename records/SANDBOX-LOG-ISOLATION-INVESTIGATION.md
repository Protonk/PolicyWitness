# Sandbox log isolation: problem and troubleshooting evidence

Investigation record, 2026-09-28, macOS 14.8.3 (23J220), arm64, two rounds the
same day. This is a temporary investigation record. No remediation has been selected or
implemented. Production code and registered tests remain unchanged.

## Problem

`witness_contract/deny_capture_covers_the_run` intermittently fails with:

```text
late denial unrecorded: the unified log holds no deny record for the worker's
final denied read inside the scanned span
```

The [case](../tests/suites/witness_contract/check_deny_capture_window.py) denies an
early read, holds two `/bin/sleep` children to their exec deadlines, then denies
a late read about twenty seconds later. It checks the complete runner-client
scan interval, associations and missing-record diagnostics. Its final assertion
also requires the late read's record to exist in the returned unified-log data.

The missing-record symptom is independently reproduced. It occurs with native
EPERM results, successful worker completion, a successful log query, and correct
missing-record diagnostics. Wider raw searches outside PolicyWitness also lack the selected records, in every
channel. The follow-up round localizes the omission to the Sandbox kernel
extension's violation reporting and reproduces it with an unconfined
`sandbox-exec` control, so process identity, signing, ancestry, policy rule count
and the worker's self-apply path are excluded as selectors, as is log transport.
The rule that drops a line is not identified.

The immediate production consequence observed here is incomplete supporting
log evidence. The worker's attempts and successful execution remain reported.
`capture_status: "captured"` means a successful observer response for the
requested interval, not complete delivery of all denials.
`permission_failures_without_record` identifies permission-shaped attempts with
no captured candidate association; it does not establish why their records are
absent. The default test adds a stronger availability requirement and can fail
even when those production distinctions are preserved.

The investigation separates three questions: whether PW handles available and
unavailable evidence correctly; whether a controlled worker workload produces
enough real records to test capture through the whole interval; and whether
every denied attempt produces a record. These are different claims. No
unconditional worker-log availability guarantee has been established.

## STR

Use the built app at `dist/PolicyWitness.app` from an unsandboxed session. In
the automation harness, `log show` returned `Cannot run while sandboxed`;
live investigation commands were rerun with escalation as described in
[tests/README.md](../tests/README.md#sandboxed-automation-harnesses). Missing
equipment or blocked capture is distinct from a successful query with no record.
Preserve each execution and scan; these steps do not retry a failure until green.

`log show` omits loss events unless `--loss` is passed. A
`--predicate 'eventType == lossEvent'` query without that flag returns nothing
however many losses the store holds, so every scan below passes `--loss`.
`log stats --overview` needs no root and prints the archive-wide loss count; run
it once to confirm loss events are visible at all. A loss event reads
`lost N unreliable messages from A-B`; `A-B` is a mach-continuous range, and every
record's `machTimestamp` is on the same clock (24 MHz here, `mach_timebase_info`
125/3), so any recorded event's `timestamp`/`machTimestamp` pair converts a range
to wall time. Kernel deny lines are `processID` 0 events from the `Sandbox`
sender; the worker PID exists only inside `eventMessage`, so PID selection must
match the message text, never `processID`. Displayed wall timestamps in the
archive carried a conversion offset of +10 to +36 ms relative to `CLOCK_REALTIME`
during this investigation; treat them as later than the attempt by that much.

1. **Original intermittent case.** Select a fresh output name:

   ```sh
   PW_TEST_OUT_DIR="tests/out/runs/deny-log-repro-$(date -u +%Y%m%dT%H%M%SZ)" \
     tests/run.sh --case witness_contract/deny_capture_covers_the_run
   ```

   Read `observations.json`, `retired-window.json`, and `run/run.json` under
   `suites/witness_contract/deny_capture_covers_the_run/artifacts/`.
   A pass on a fresh run does not invalidate an earlier missing-record result.

2. **Isolated worker STR.** Create five specimens with fresh readable temporary
   files. Each uses `(version 1)(allow default)` plus
   `(deny file-read-data (literal (param "P")))`. Its only probe predicts
   `file-read-metadata` on that path and attempts `file/open_read` on it. The
   allowed metadata prediction avoids intentionally generating read-denial
   records before the attempt. Run each with:

   ```sh
   dist/PolicyWitness.app/Contents/MacOS/policy-witness \
     run /absolute/path/to/specimen.json --no-log-capture
   ```

   Retain the envelope, worker PID, path and start/end times. Verify native EPERM
   and worker completion independently of logging. Search the enclosing interval
   using raw `/usr/bin/log show --loss --info --debug --style ndjson`, first by
   worker PID (`eventMessage CONTAINS "pw-probe-runner(<pid>)"`), then by the
   unique target directory without a process filter, then channel-agnostic by
   `eventMessage CONTAINS "(<pid>)"` with bounds widened by 60 seconds; the last
   also returns sandboxd's rate-limited `com.apple.sandbox.reporting` Violation
   reports and, for `sandbox-exec` controls, the kext's `Sandbox apply:` line.
   Use explicit whole-second UTC bounds. Missing records are intermittent; neither
   a fixed loss count nor an initial-burst pattern is an expected invariant.

3. **Lifetime and process controls.** Repeat the worker specimens with a trailing
   allowed `/bin/sleep 0.5` exec and verify that child actually exits successfully.
   For process controls, use fresh files under the same allow-default/literal-deny
   policy shape with `sandbox-exec`: `/bin/cat`, then an ad-hoc signed C program
   that calls `open(argv[1], O_RDONLY)` and reports its result and errno. Retain
   command receipts, not just files left in the temporary directory. These
   controls measure reporting differences; a child's record is not worker evidence.

4. **Burst/spacing and long-window experiments used below.** The retained driver
   uses one fixed policy shape with 64 literal denied targets per specimen and
   allowed metadata queries. It selects 1, 8 or 32 distinct read attempts, with
   either no added pause or a 0.5-second pause immediately before CLI launch.
   Four shuffled, balanced blocks give 20 fresh workers per cell. Short runs
   disable production capture and are scanned independently after each block.
   Long runs put equal-sized read groups before and after the original two held
   execs, enable production capture, and rotate sizes across three blocks.
   A separate experiment starts a live stream before twelve short runs with
   production capture enabled. The evidence routes below include the exact driver.

5. **Follow-up observations.** Preserve initial scans, then search the same
   targets with bounds widened by 60 seconds at both ends. The current driver
   performs a delayed scan at least 60 seconds after a cohort's last run; actual
   scan times are retained. Query loss events separately with `--loss --predicate 'eventType == lossEvent'`;
   without `--loss` that query returns nothing however many losses the store holds.
   Convert each `from A-B` range to wall time as described above and test it
   against the missing attempt's interval. Compare target membership, not just
   total line counts. NDJSON's final `count/finished` object is a footer, not an
   event. Zero loss events exclude a counted transport loss over the interval;
   they do not identify the stage that omitted an uncounted line.

6. **Kext-side localization.** For each missing record, scan `sender == "Sandbox"`
   within 3 seconds of the lost phase (client start for early or single-read
   losses, client end for late losses) and list every line with its time relative
   to the attempt. Other processes' deny lines show whether the kernel report path
   was delivering at that instant. A `N duplicate reports for Sandbox: …` flush
   line at the attempt's instant shows that the kext's duplicate tracking
   processed an arrival there; it names the coalesced neighbour, not the missing
   attempt. Retain the raw scans.

7. **Instrumented unconfined control.** Build and ad-hoc sign `probe_latency.c`
   (route below): it stamps `CLOCK_REALTIME`, `mach_absolute_time` and
   `mach_continuous_time` immediately before and after one `open(2)` and prints
   them with `getpid()` and `errno`. Run it under
   `sandbox-exec -p '(version 1)(allow default)(deny file-read-data (literal "<path>"))'`
   on a fresh file per run, in a back-to-back cell (0.25 s gaps) and an idle cell
   (20 s before each run). Append a receipt per run before scanning. Scan 5 seconds
   after the last run and again 60 seconds later with bounds widened by 60 seconds.
   Join records to runs by path, check the record's PID against the probe's, and
   compute `machTimestamp` minus the post-open `mach_continuous_time` (report
   latency, no wall conversion involved) and `timestamp` minus the post-open
   `CLOCK_REALTIME` (the archive's conversion offset). A child's record is not
   worker evidence; this control measures the OS reporting path.

## Troubleshooting results

### Environment and original failure

Measurements used checkout `c6ea6856d4e846cfe23e636c9237e09065cc5c62` and the
existing signed app, build 290, stamped
`v0.2.3-22-gb1f5ca4-dirty`. The entire recorded app inventory matches the original
failed `exec-budget-robust` run. The earlier registered reruns passed signature
and manifest inspection. Inventories before and after every new live experiment
also match that original inventory. No logging configuration was changed.

In the original failure, worker PID 91533 completed normally. Both reads returned
EPERM; both exec children were killed at their deadlines. The 20,096 ms client
span was scanned from `2026-09-28 15:36:30+0000` to `15:36:51+0000`. The early
record was present, the late record absent, and diagnostics named exactly the
late step. Production and retired-window queries succeeded; production reported
no truncation.

Over 31 minutes later, independent raw queries still found only the early
record. This held for the exact interval searched by worker PID and for a
path-only query widened by 60 seconds on each side. The loss-event query returned
nothing, but it lacked `--loss` and could not have returned a loss event; the
follow-up round below re-queried with the flag. The earlier notes' 357 ms and
631 ms figures are observer report generation minus client end; those fields do
not establish scan start times.

### Independent initial cross-check

Two fresh executions of the registered long-window case passed with both records.
An initial batch with 0.5-second pauses captured 5/5 isolated worker denials and
5/5 denials followed by a successful sleep. Eight cat controls, ten ad-hoc C
controls, and a 32-read C burst were fully recorded.

A tighter replay alternated the original isolated and trailing-sleep specimen
shapes without added pauses, using fresh paths. Each group recorded 3/5 denials:
its first two were absent and its last three present. Every read returned EPERM;
every trailing sleep exited 0. A wider path-only scan about 68 seconds later
returned the same six records. A query for the first missing worker PID returned
none. A wider loss-event query returned none, but lacked `--loss` (see the
follow-up round). All ten targets were readable
outside the specimen sandbox.

Historical path searches also recovered eight cat records, three C records, and
one matching record for each earlier five-worker specimen group. Those older
standalone artifacts lack sufficient execution receipts to independently verify
every claimed attempt. The fresh experiments retain those receipts. The earlier
Python control and claimed 514/s and 3,211/30-minute totals were not independently
re-measured; they do not establish a general platform or rate-limit rule.

### Balanced burst and spacing experiment

All 120 workers completed successfully and reported EPERM for every selected
read. Each table cell contains 20 runs. Policy shape was held constant; target
paths were fresh. Execution order was shuffled within four balanced blocks.
The pause is before CLI launch, not a pause between reads within a burst.

| Reads per worker | Added pause | Recorded / attempted reads | Runs with any record | Runs with all records |
| --- | --- | --- | --- | --- |
| 1 | 0 | 20/20 | 20/20 | 20/20 |
| 1 | 0.5 s | 19/20 | 19/20 | 19/20 |
| 8 | 0 | 160/160 | 20/20 | 20/20 |
| 8 | 0.5 s | 160/160 | 20/20 | 20/20 |
| 32 | 0 | 640/640 | 20/20 | 20/20 |
| 32 | 0.5 s | 637/640 | 20/20 | 19/20 |

The incomplete 32-read worker lost its first three records and retained the
remaining 29. This directly contradicts a general claim that dense worker
denials are recorded completely. A 0.5-second pause also did not ensure a single
record. The 40 complete eight-read runs supplied a candidate for the longer
experiment, not a guarantee. These samples do not establish a causal effect of
spacing, a stable loss probability, or independent losses between attempts.

### Bursts across the original twenty-second interval

Nine runs used 1, 8 or 32 reads in each phase, with three runs per size and
rotated execution order. Native reads, metadata predictions, worker completion
and both exec deadlines were checked. Production capture and independent raw
queries returned exactly the same target membership in every run.
All 227 captured event timestamps fit the requested bounds; recorded early
events were outside the trailing ten seconds and recorded late events inside it.

| Reads per phase | Early records / attempts | Late records / attempts | Runs with a record in both phases | Runs with every record |
| --- | --- | --- | --- | --- |
| 1 | 3/3 | 2/3 | 2/3 | 2/3 |
| 8 | 17/24 | 16/24 | 2/3 | 1/3 |
| 32 | 96/96 | 93/96 | 3/3 | 2/3 |

The eight-read candidate failed: `b0-n8` recorded all early reads and no late
reads. Another run, `b1-n8`, recorded only the last early read and all late reads.
For 32 reads, `b2-n32` lost the first three late records. The other two 32-read
runs were complete.

Thus 32 reads per phase retained some evidence in both phases in this small
sample, while complete logging already has counterexamples. This is a limited
candidate condition, not an established “PW always gets a log” contract.
All nine envelopes retained successful execution and named exactly the
permission-shaped attempts without captured records. No observer errors or
truncation explained the omissions.

### Live stream, archive and delayed observations

The separate stream experiment ran four workers at each size, 1/8/32. All 164
target denials appeared in the live stream, production capture, the immediate
raw archive query and the delayed query. Stream receipt times were approximately
0.24–2.42 ms after the displayed stream timestamps. This cohort did not reproduce
a missing record, so it cannot locate the omission before or after streaming or
persistence. The presence of an active stream is itself an experimental condition;
its effect on record availability was not isolated.

For these same 164 events, matching `machTimestamp` values accompanied archive
wall timestamps approximately 9.97–10.01 ms later than stream wall timestamps.
This is a measured representation difference, not evidence of denial timing or
the cause of the absent records. The production window already disclaims exact
event-time and attempt-time claims.

Delayed path-only queries used wider intervals and started approximately 370 s,
98 s and 60 s after the matrix, long and stream cohorts' respective final runs.
Their target membership exactly matched the initial queries. No missing record
appeared. Each cohort's loss-event query returned zero records, but those queries
lacked `--loss`; the follow-up round repeats them correctly. These observations
exclude a short delay as the explanation over the measured waits, but do not
prove that records were never emitted or rule out every suppression or loss path.

### Contract boundary exercised without depending on new OS records

The existing tests already distinguish much of the PW-controlled behavior:

| Claim | Existing controls / observed boundary |
| --- | --- |
| Full client bounds, whole-second widening, rollback refusal, and event selection inside/outside bounds | `sandbox_log::tests` uses the actual outgoing argv and a fixed independently timed event corpus; the live case checks real-tool acceptance. |
| PID, operation and path association; ambiguity and missing provenance | Matching controls require the correct candidate sets and preserve ambiguity. A unique fixture target permits one candidate, not a general causal attribution claim. |
| Partial/empty capture and explicit missing-record diagnostics | `no_match_is_distinguished_by_unrecorded_permission_failures` distinguishes an empty successful capture from unavailable, disabled or unclassifiable evidence. |
| Preserved execution status and termination evidence | Run-flow controls keep execution independent of capture conditions and carry valid or mismatched observer replies through serialization and consumer recovery. |
| Real final-denial record exists | The current live case's final assertion depends on external availability. The other checks cannot make the OS supply this record. |

Executed in a disposable source copy: 15 sandbox-log tests, 10 observer-binary
tests (including its JSON-envelope helper tests), and 25 run-flow tests. All
passed. Original source hashes and command receipts are retained.

An additional disposable replay supplied retained real early/late syslog lines
to the actual observer parser, then controlled observer responses to the actual
receiver, association, diagnostic and envelope functions and the independent
Python consumer. Ten states passed: both records, early only, late only, neither,
disabled, blocked, observer error, malformed JSON, wrong window, and no observer.
Each preserved the complete real runner result and successful execution, with
no invented termination cause. Successful partial/empty capture named exactly
the missing steps; unavailable/disabled capture kept that diagnostic null.

Three separate mutations of the disposable implementation were rejected at the
intended assertions: dropping all raw denial lines, dropping one supplied event
in the receiver, and inventing a candidate step ID. The restored copy passed
again. Compiler failures were not accepted as successful mutation controls.
No mutation touched the signed app or checkout source.

This establishes an enforceable boundary for **supplied-event fidelity** even
when an empty external result is admissible. It does not prove live retrieval
when there is no independently available record. Removing only the current
mandatory-late-record assertion would leave positive live capture coverage
conditional on record availability, although the deterministic fidelity checks
would still reject those tested regressions. The replay remains investigation
evidence, not a newly registered test or a selected implementation.

### Follow-up round: loss visibility, alternate channels, record timing and an unconfined control

Same machine, boot and app inventory as above; checkout `290ee71` (plan only).
Live commands ran unsandboxed. Nothing under `tests/out/` from the first round
was modified; the new output is a fresh unmanaged directory (routes below). A
read-only review of the first round's evidence preceded this round; its report
is retained beside the new output.

**Loss events were invisible to every earlier query.** `log show` returns no
loss event unless `--loss` is passed, and no earlier loss query passed it.
`log stats --overview` reports 257 loss events in the store; `log show --loss`
returns 123 over five days, all of the form `lost N unreliable messages from A-B`.
Re-queried with `--loss` over intervals widened by 60 seconds, the matrix, long,
stream, replay and initial-crosscheck cohorts hold zero loss events. The
registered interval holds 17, all between 15:37:52 and 15:38:04 UTC, 62 to 73
seconds after the original client end; converted through the recorded early
record's `machTimestamp`, none overlaps any missing attempt. The earlier
conclusion stands, but the method could not have shown otherwise.

**No channel holds the missing lines.** For all eleven missing workers (matrix
`b2-17-n1-p0.5` PID 10039 and `b3-08-n32-p0.5` PID 10387; long `b0-n8` 11014,
`b1-n1` 11054, `b1-n8` 11069, `b2-n32` 11099; replay 3503, 3510, 3518, 3525; the
original 91533) a channel-agnostic query for `(<pid>)` over the client span
widened by 60 seconds returned only the kernel lines already known, zero
`com.apple.sandbox.reporting` (sandboxd) reports, zero other lines and zero loss
events. Over five days the sandboxd channel carried 101 events for 50 worker
PIDs against 18,943 kernel lines for 805 PIDs; it is rate limited and cannot
serve as a fallback witness, though it must be checked.

**The kernel report path was delivering for other processes at every loss.**
Within 3 seconds of each lost phase, other processes' `Sandbox:` lines were
recorded: for the original, logd_helper denials displayed 62 ms after the client
end; for the replay, sixteen ContextStoreAgent lines within a second; for the
matrix losses, hundreds of lines from neighbouring workers.

**Records are stamped inside the syscall; displayed times run late.** The
instrumented control (23 runs, below) gives `machTimestamp` minus the probe's
post-open `mach_continuous_time` of −2 to −10 µs for every recorded run: the
kernel stamps the deny line during `open(2)`, with no report latency. The same
records' displayed `timestamp` ran +35.41 to +36.10 ms after the probe's
`CLOCK_REALTIME`, drifting about 0.7 ms over 160 s; the first round's
stream-versus-archive comparison implies about +10 ms at 16:34. Displayed times
therefore postdate attempts by a session-dependent conversion offset, not by
reporting delay. Against the client span, displayed last-step record times fall
7 to 55 ms before the client end for the 64-rule workers (138 records) and up to
21 ms after it for one-rule last-step workers (8 records); the registered
two-rule late read displayed 13.5 ms before, 1.9 ms after and 4.5 ms after the
client end in the three passing runs. The production window's ceiling leaves 0
to 1,000 ms of trailing slack, so a last-step denial is excluded from production
capture when the client end falls within the offset of the next whole second.
None of the observed omissions is such a case: the ±60 s scans lack them too.

**An unconfined control reproduces the omission.** The ad-hoc-signed
`probe_latency` ran 23 times under `sandbox-exec`, each denying one fresh
literal path; every run returned EPERM. Nine were recorded. The back-to-back
cell lost runs 0 to 7 and recorded 8 to 14; the idle cell recorded runs 0 and 1
and lost 2 to 7. The delayed scan returned the same nine. Zero loss events fell
in the window widened by 60 seconds. The same morning's controls (eight `cat`,
ten C, one 32-read C burst) had been complete, so the condition varies with
time or system state, not with process identity, signing, ancestry, rule count
or the worker's self-apply path.

**The omission sits inside the kext's violation reporting.** For all 23 control
PIDs, including the 14 without a deny line, the kext's own
`Sandbox apply: sandbox-exec[<pid>]` line was recorded 33 to 37 ms (displayed)
after the probe started. At five of the six lost idle-cell instants, a
`N duplicate reports for Sandbox: mediaanalysisd(…) deny(1) mach-lookup …` flush
line was recorded 36.4 to 38.1 ms after the probe's `open(2)` returned, i.e. at
the denial's displayed instant, with no mediaanalysisd line beside it; the same
flush accompanies recorded control lines (idle run 1, burst run 10). Among the
first round's losses, the same signature precedes three of the four long-run
late losses: `b0-n8` (flush 20.7 ms before client end, all eight late lines
missing), `b1-n1` (14.5 ms before, the single late line missing) and `b2-n32`
(flush at 16:33:08.373337, first recorded late line 254 µs later, three lines
missing in between). It is absent at the matrix, `b1-n8`, replay and original
losses, where no flush was pending. A flush is emitted when a different report
arrives, so the missing attempt reached the kext's duplicate tracking and was
then not logged, while a line from the same kext, the same instant and the same
PID was. Over five days no throttle, rate-limit or suppression notice exists
from the `Sandbox` sender; only `N duplicate reports for …` coalescing, which
keys on the identical message (1,064 such lines name pw-probe-runner, all for
repeated identical denials in other tests).

**Review of the first round's evidence.** Every numeric claim the reviewer
could locate matches its file. `experiment.py` was saved after its cohorts ran;
the bytecode compiled before the matrix differs from the retained source only
in the rescan wait loop. Four derived files (`cross-channel-checks.json`,
`long-timing-checks.json`, `stream/timestamp-comparison.json`,
`unconfined-read-controls.json`) have no retained generator; the first three
were recomputed and match. No envelope carries per-attempt timestamps. Every
receipted worker loss is a leading prefix of its phase (seven of seven), and the
replay lost its first four consecutive runs; both matrix losses were in the
0.5 s pause cells; three of four long-run losses and the original were the first
reads after the 20 s hold. The control adds a trailing run of losses (idle runs
2 to 7), so contiguity in time, not leading position, is the shared shape.

**Offset mechanism and a third measurement (18:27 UTC).** Six userland `os_log`
markers carrying their own `CLOCK_REALTIME` displayed +59.10 to +61.68 ms late,
against +35.41 to +36.10 ms on the kernel channel at 17:25 and about +10 ms at
16:34; six interleaved `sandbox-exec` denials recorded none, so the kext
omission was total in that run. `timed` logged a −68 ms residual slew in
progress at 18:29 and three clock steps of 63 to 73 ms over the day, each
accompanied within 10 ms by a logd `=== system wallclock time adjusted`
timesync event (35 timesync events in 24 h, roughly hourly otherwise). The
machine had been up 147 days, so the offset does not accumulate over uptime: it
is the wall-clock correction applied since logd's last re-map, and the scan
padding decision in the associated plan rests on that bound. `eventType ==
timesyncEvent` needs no extra flag.

## Open questions

Closed by the follow-up round:

- Displayed timestamp differences and report delays (former question 4). The
  record is stamped inside the denied syscall; displayed archive times ran +10 to
  +36 ms late in this session. That offset can push a last-step denial past the
  production ceiling when the client end lands within the offset of a whole
  second, and no observed omission was such a case.
- Transport loss. With `--loss`, no loss event overlaps any missing attempt.
- Alternate channels and formats. No sandboxd report, no other line and no
  differently formatted kernel line exists for any of the eleven missing workers.
- Process identity, signing, ancestry, rule count and the self-apply path as
  selectors. One-rule (replay, control), two-rule (original) and 64-rule (matrix,
  long) specimens all lose lines; an ad-hoc-signed `sandbox-exec` control loses
  them while the kext's apply line and other processes' deny lines from the same
  instants persist.

Open:

- Which rule inside the Sandbox kext's violation reporting drops a line after
  duplicate tracking has processed it? Candidates consistent with the data: a
  global or per-class budget consumed by other processes' arrivals, coalesced
  repeats included (mediaanalysisd's mach-lookup denials were the coalesced
  neighbour during the control's losses), or a suppression window keyed on the
  preceding report. A discriminating run: the control while a helper generates
  identical denials at a controlled rate (0, 1, 10, 100 per second), then the
  same with distinct-path denials, correlating loss episodes with the flushed
  duplicate counts.
- Does a lost line also fail to appear in `log stream` (former question 3)? The
  syscall-time stamp and the kext localization predict that it does; the control
  reproduces losses cheaply enough to test with a stream attached, and to test
  whether attaching the stream changes the loss rate.
- Does a fixed 32-read burst reliably provide at least one record per phase
  (former question 1)? Unchanged: three long runs, one incomplete. The control's
  loss episodes of 8 and 6 consecutive runs, lasting about 2 s and 120 s, bound
  how long a burst would have to span to guarantee one record; no fixed count
  does.
- Where does the worker's attempt sit relative to the client end? One-rule
  last-step lines display up to 21 ms after the client end and 64-rule lines 7 to
  55 ms before it; separating teardown duration from the conversion offset needs
  per-attempt `mach_continuous_time` in the worker's evidence, which no schema
  carries today.
- How large can the archive's conversion offset become (+10 ms at 16:34,
  +36 ms at 17:25, +62 ms at 18:27)? The mechanism bounds it by `timed`'s
  corrections between logd re-maps, measured on one machine over one day; the
  associated plan decides a symmetric two-second scan pad on that basis, and a
  machine with different time discipline could need re-measurement.
- What positive live guarantee can the default battery retain without treating
  external absence as a PW correctness failure (former question 5)? Unchanged,
  with the added fact that the omission is an OS-side kext behaviour
  reproducible without PolicyWitness.
- Do any production consumers treat `captured` as complete, or a null
  missing-record list as empty (former question 6)? Unchanged; consumers outside
  this checkout were not audited.
- Are the first round's regularities (leading-prefix losses within a phase, both
  matrix losses in the 0.5 s pause cells, losses after the 20 s hold) properties
  of the kext rule or artefacts of small samples? The control's trailing-run loss
  weakens the leading-prefix reading; the pause and idle readings are untested.

## Routes to existing gitignored evidence

These are repository-relative **local** routes. `tests/out/` is gitignored;
committing this plan does not commit its evidence, and a fresh clone will not
contain these directories. They were left intact. The new investigation output
is outside managed `tests/out/runs/`, so it is unmanaged retained scratch rather
than a dispatcher-owned completed run.

| Evidence | Route and contents |
| --- | --- |
| Original failed case and app inventory | [exec-budget-robust](../tests/out/runs/exec-budget-robust/): case artifacts under `suites/witness_contract/deny_capture_covers_the_run/artifacts/`; app inventory under `artifact-integrity/`. |
| Original immediate passing rerun | [exec-budget-robust-rerun](../tests/out/runs/exec-budget-robust-rerun/), same case artifact layout. |
| Independent registered reruns | [crosscheck A](../tests/out/runs/sandbox-log-crosscheck-20260928-a/) and [crosscheck B](../tests/out/runs/sandbox-log-crosscheck-20260928-b/), each with observations and artifact-integrity receipts. |
| Initial independent investigation | [INVESTIGATION.md](../tests/out/sandbox-log-crosscheck-20260928/INVESTIGATION.md) indexes the original-failure re-queries, platform/C controls, tighter worker replay, delayed scans, unconfined read controls, and their scripts. |
| New experiment driver and summarized results | [experiment.py](../tests/out/sandbox-log-troubleshooting-20260928/experiment.py), [analysis.json](../tests/out/sandbox-log-troubleshooting-20260928/analysis.json), [analyze.py](../tests/out/sandbox-log-troubleshooting-20260928/analyze.py). |
| Short matrix | [matrix/](../tests/out/sandbox-log-troubleshooting-20260928/matrix/): `rows.json`, `initial-summary.json`, `block-*-initial.json`, `loss.json`, and per-case `specimen.json`, `command.json`, `envelope.json`. Counterexamples: `b2-17-n1-p0.5` and `b3-08-n32-p0.5`. |
| Twenty-second runs | [long/](../tests/out/sandbox-log-troubleshooting-20260928/long/): the same per-case receipts, `*-initial.json` raw scans and `initial-summary.json`; [long-timing-checks.json](../tests/out/sandbox-log-troubleshooting-20260928/long-timing-checks.json) records interval/phase timestamp checks. Counterexamples include `b0-n8`, `b1-n1`, `b1-n8`, and `b2-n32`. |
| Stream comparison and receipt times | [stream/](../tests/out/sandbox-log-troubleshooting-20260928/stream/): `stream-receipts.jsonl`, `stream-command.json`, `stream-summary.json`, `initial-path.json`, per-case envelopes and `timestamp-comparison.json`; [stream-timing.json](../tests/out/sandbox-log-troubleshooting-20260928/stream-timing.json) gives parsed receipt timing. |
| Delayed wider queries and exact comparisons | [rescan/](../tests/out/sandbox-log-troubleshooting-20260928/rescan/): `*-path-wide.json` commands/results and `summaries.json`; [cross-channel-checks.json](../tests/out/sandbox-log-troubleshooting-20260928/cross-channel-checks.json) records exact target-membership and app-inventory equality checks. |
| Coverage audit and controlled replay | [COVERAGE-AUDIT.md](../tests/out/sandbox-log-troubleshooting-20260928/COVERAGE-AUDIT.md), [replay.py](../tests/out/sandbox-log-troubleshooting-20260928/replay.py), [replay_test.rs](../tests/out/sandbox-log-troubleshooting-20260928/replay_test.rs), and [replay/](../tests/out/sandbox-log-troubleshooting-20260928/replay/): input envelope/specimen, source hashes, receipts, baseline/restored consumer outputs and all three rejected-mutation logs. |
| Provenance and fixture locations | [provenance.json](../tests/out/sandbox-log-troubleshooting-20260928/provenance.json); each live cohort's `environment.json` names its retained `/private/tmp/pw-log-…` target tree, and its `app-before.json`, `app-after.json`, `completion.json` record integrity and timing. |
| Evidence review of the first round | [EVIDENCE-REVIEW.md](../tests/out/sandbox-log-troubleshooting-20260928-b/EVIDENCE-REVIEW.md): inventory, claim-to-file mapping, counterexample table, driver review, regularities and gaps. |
| Follow-up archive checks | [archive/](../tests/out/sandbox-log-troubleshooting-20260928-b/archive/): `archive_checks.py` and `summary.json`; per missing worker `pid-*.ndjson` (channel-agnostic PID query) and `kext-*-<phase>.ndjson` (`sender == "Sandbox"` within 3 s); per cohort `records-*.ndjson` and `loss-*.ndjson` (with `--loss`); every query's `*-command.json`; `flush-signature-check.json`. |
| Instrumented unconfined control | [latency/](../tests/out/sandbox-log-troubleshooting-20260928-b/latency/): `probe_latency.c`, `run_latency.py`, `receipts.jsonl` (23 runs), `environment.json` (codesign transcript, target tree `/private/tmp/pw-log-latency-ym2qqnyp`), `initial-*.ndjson` and `delayed-*.ndjson` scans with `*-command.json`, `analyze_latency.py`, `analysis.json`, `timeline.json`, `pid-keyed-all-controls*` (apply lines per PID), `duplicate-report-lines.json`. |
| Offset mechanism, third measurement | [sandbox-log-troubleshooting-20260928-c/](../tests/out/sandbox-log-troubleshooting-20260928-c/): `marker.c` (userland `os_log` marker printing `CLOCK_REALTIME` and `mach_continuous_time`), `offset_probe.py`, `receipts.json`, `scan.ndjson` with `scan-command.json`, `summary.json`; `timesync-24h.ndjson` and `timed-24h.ndjson` with `timed-summary.json` (logd timesync events and `timed` adjustments over 24 h). Target tree `/private/tmp/pw-log-offset-…` named in `receipts.json`. |

The new driver refuses to reuse an existing mode directory. To repeat it, copy
`experiment.py` and `analyze.py` into a fresh direct child of `tests/out/`, then
run modes `matrix`, `long`, `stream`, `rescan` in that order, followed by
`analyze.py`. It holds the existing checkout lock during each live mode and never
unlinks the lock. Keep the original evidence directories intact. The replay
driver likewise creates a fresh output directory and records its deliberate
test-only source changes; its input currently references crosscheck A above.
The follow-up round's `archive_checks.py`, `run_latency.py` and
`analyze_latency.py` take an output directory argument; copy them into a fresh
direct child of `tests/out/` before rerunning and leave the retained directory
untouched. `archive_checks.py` reads the first round's retained rows and
receipts by their current routes and requires the unified log store to still
hold those intervals.

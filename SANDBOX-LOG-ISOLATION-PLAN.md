# Sandbox log isolation: problem and troubleshooting evidence

Investigation completed 2026-09-28 on macOS 14.8.3 (23J220), arm64.
This is a temporary investigation record. No remediation has been selected or
implemented. Production code and registered tests remain unchanged.

## Problem

`witness_contract/deny_capture_covers_the_run` intermittently fails with:

```text
late denial unrecorded: the unified log holds no deny record for the worker's
final denied read inside the scanned span
```

The [case](tests/suites/witness_contract/check_deny_capture_window.py) denies an
early read, holds two `/bin/sleep` children to their exec deadlines, then denies
a late read about twenty seconds later. It checks the complete runner-client
scan interval, associations and missing-record diagnostics. Its final assertion
also requires the late read's record to exist in the returned unified-log data.

The missing-record symptom is independently reproduced. It occurs with native
EPERM results, successful worker completion, a successful log query, and correct
missing-record diagnostics. Wider raw searches outside PolicyWitness also lack
the selected records. The reporting stage responsible for the omission is not
established; neither platform status nor a particular rate limit is a proven
selector.

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
[tests/README.md](tests/README.md#sandboxed-automation-harnesses). Missing
equipment or blocked capture is distinct from a successful query with no record.
Preserve each execution and scan; these steps do not retry a failure until green.

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
   using raw `/usr/bin/log show --info --debug --style ndjson`, first by worker
   PID and then by the unique target directory without a process filter. Use
   explicit whole-second UTC bounds. Missing records are intermittent; neither
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
   scan times are retained. Query `eventType == lossEvent` separately. Compare
   target membership, not just total line counts. NDJSON's final `count/finished`
   object is a footer, not an event. Zero loss notices do not prove lossless
   delivery, and continued absence does not identify the responsible stage.

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
path-only query widened by 60 seconds on each side. No loss-event records were
returned. The earlier notes' 357 ms and 631 ms figures are observer report
generation minus client end; those fields do not establish scan start times.

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
none, and a wider loss-event query returned none. All ten targets were readable
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
appeared. Each cohort's loss-event query returned zero records. These observations
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

## Open questions

- Does a fixed 32-read burst reliably provide at least one record in each
  required phase across more blocks, sessions, system states and supported OS
  versions? Current evidence is three long runs, with incomplete logging in one.
  Per-attempt completeness and per-phase availability remain separate questions.
- Which property selects omissions: process identity or ancestry, signing,
  report cadence, time since previous activity, policy shape, or another state?
  Neither a platform/non-platform explanation nor a specific rate limit has
  been isolated. The new matrix holds 64 literal rules constant and therefore
  does not compare that shape against the original one- or two-rule specimens.
- When omissions occur with a live stream already active, are the same records
  absent from stream and archive? Does activating the stream affect the outcome?
  The current stream cohort was complete and does not resolve either question.
- Can displayed timestamp differences or longer report delays cross the
  whole-second scan slack? They did not explain the omissions found by wider
  searches here, but exact attempt-time inference is not established.
- What positive live guarantee can the default battery retain without treating
  external absence as a PW correctness failure? The supplied-event controls are
  strict, but do not alone establish a dependable source of real records.
- Do any production consumers treat `captured` as complete, or treat a null
  missing-record list as an empty list? The exercised controller and Python
  consumer preserve the distinction; consumers outside this checkout were not
  audited.

## Routes to existing gitignored evidence

These are repository-relative **local** routes. `tests/out/` is gitignored;
committing this plan does not commit its evidence, and a fresh clone will not
contain these directories. They were left intact. The new investigation output
is outside managed `tests/out/runs/`, so it is unmanaged retained scratch rather
than a dispatcher-owned completed run.

| Evidence | Route and contents |
| --- | --- |
| Original failed case and app inventory | [exec-budget-robust](tests/out/runs/exec-budget-robust/): case artifacts under `suites/witness_contract/deny_capture_covers_the_run/artifacts/`; app inventory under `artifact-integrity/`. |
| Original immediate passing rerun | [exec-budget-robust-rerun](tests/out/runs/exec-budget-robust-rerun/), same case artifact layout. |
| Independent registered reruns | [crosscheck A](tests/out/runs/sandbox-log-crosscheck-20260928-a/) and [crosscheck B](tests/out/runs/sandbox-log-crosscheck-20260928-b/), each with observations and artifact-integrity receipts. |
| Initial independent investigation | [INVESTIGATION.md](tests/out/sandbox-log-crosscheck-20260928/INVESTIGATION.md) indexes the original-failure re-queries, platform/C controls, tighter worker replay, delayed scans, unconfined read controls, and their scripts. |
| New experiment driver and summarized results | [experiment.py](tests/out/sandbox-log-troubleshooting-20260928/experiment.py), [analysis.json](tests/out/sandbox-log-troubleshooting-20260928/analysis.json), [analyze.py](tests/out/sandbox-log-troubleshooting-20260928/analyze.py). |
| Short matrix | [matrix/](tests/out/sandbox-log-troubleshooting-20260928/matrix/): `rows.json`, `initial-summary.json`, `block-*-initial.json`, `loss.json`, and per-case `specimen.json`, `command.json`, `envelope.json`. Counterexamples: `b2-17-n1-p0.5` and `b3-08-n32-p0.5`. |
| Twenty-second runs | [long/](tests/out/sandbox-log-troubleshooting-20260928/long/): the same per-case receipts, `*-initial.json` raw scans and `initial-summary.json`; [long-timing-checks.json](tests/out/sandbox-log-troubleshooting-20260928/long-timing-checks.json) records interval/phase timestamp checks. Counterexamples include `b0-n8`, `b1-n1`, `b1-n8`, and `b2-n32`. |
| Stream comparison and receipt times | [stream/](tests/out/sandbox-log-troubleshooting-20260928/stream/): `stream-receipts.jsonl`, `stream-command.json`, `stream-summary.json`, `initial-path.json`, per-case envelopes and `timestamp-comparison.json`; [stream-timing.json](tests/out/sandbox-log-troubleshooting-20260928/stream-timing.json) gives parsed receipt timing. |
| Delayed wider queries and exact comparisons | [rescan/](tests/out/sandbox-log-troubleshooting-20260928/rescan/): `*-path-wide.json` commands/results and `summaries.json`; [cross-channel-checks.json](tests/out/sandbox-log-troubleshooting-20260928/cross-channel-checks.json) records exact target-membership and app-inventory equality checks. |
| Coverage audit and controlled replay | [COVERAGE-AUDIT.md](tests/out/sandbox-log-troubleshooting-20260928/COVERAGE-AUDIT.md), [replay.py](tests/out/sandbox-log-troubleshooting-20260928/replay.py), [replay_test.rs](tests/out/sandbox-log-troubleshooting-20260928/replay_test.rs), and [replay/](tests/out/sandbox-log-troubleshooting-20260928/replay/): input envelope/specimen, source hashes, receipts, baseline/restored consumer outputs and all three rejected-mutation logs. |
| Provenance and fixture locations | [provenance.json](tests/out/sandbox-log-troubleshooting-20260928/provenance.json); each live cohort's `environment.json` names its retained `/private/tmp/pw-log-…` target tree, and its `app-before.json`, `app-after.json`, `completion.json` record integrity and timing. |

The new driver refuses to reuse an existing mode directory. To repeat it, copy
`experiment.py` and `analyze.py` into a fresh direct child of `tests/out/`, then
run modes `matrix`, `long`, `stream`, `rescan` in that order, followed by
`analyze.py`. It holds the existing checkout lock during each live mode and never
unlinks the lock. Keep the original evidence directories intact. The replay
driver likewise creates a fresh output directory and records its deliberate
test-only source changes; its input currently references crosscheck A above.

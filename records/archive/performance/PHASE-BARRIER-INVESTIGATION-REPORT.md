# Phase barrier under delayed collection: build 853

> Archive availability: original raw runs are not retained. Reproduction
> procedures describe the original `records/performance/` layout and pinned
> environment; committed derived evidence remains available.

While the host held the phase-boundary callback, the sandboxed worker ran on
one CPU for essentially the whole interval. Over 200 ms holds its CPU was
0.957–0.998 of the observed window, and over 800 ms holds 0.993–1.000, almost
all of it on performance cores. The worker's exact lifetime CPU was
0.992–0.999 of its lifetime in every held condition, against 0.907–0.914 in
ordinary unheld runs. The difference was a longer life, not a different
rate. Sampling density did not change these figures.

When the worker's own 250 ms proceed allowance expired during a 400 ms hold,
the worker published a proceed-timeout failure and exited, 248.9–249.7 ms
after the host's callback began. The host then found the child reaped and
never published a release; the attempt never ran. These observations describe
one fixture, policy, executable and machine interval. They are not an
optimization proposal.

## Evidence and conditions

The worker was the shipped `pw-probe-runner` from `dist/PolicyWitness.app`,
version 0.3.3, build 853, commit `1bf0341` (SHA-256 `c8ac685b…`). The runner
and worker sources are unchanged between that commit and this investigation's
commits. The fixture
([`phase-barrier/`](phase-barrier/README.md)) was built from this repository
by SwiftPM with the Swift 6.4 toolchain and deployment target 26.0 (binary
SHA-256 `50d2c4a2…`). It
reached the driver through `@testable import`, as the runner's own tests do.

The machine was a Mac17,3 (4 performance and 6 efficiency logical CPUs,
16 GiB) running macOS 26.7.1 (25G241). The measured series ran on AC power;
the pilots ran on battery. The operator launched the measured series from a
normal terminal with no agent session active, and reported no major system
events, only switching between windows.

At the series start, the load average was 3.04 and several macOS background
services showed recent high CPU shares: `duetexpertd`, a background Shortcuts
runner, Spotlight's `mds`, `siriactionsd` and `axassetsd`. All were quiet in
the end snapshot. `ps` shares are decayed averages, so activity during the
series is unobserved. `pmset` recorded no thermal or performance warning at
either end.

| Run | Plan | Units | Outcome |
| --- | --- | ---: | --- |
| [`20261024T134944618985Z-phasebarrier-measure-b853`](evidence/20261024T134944618985Z-phasebarrier-measure-b853/summary.json) | measured, operator-run | 30 | all completed; 0 unclean |
| [`20261024T134255988081Z-phasebarrier-pilot1-b853`](evidence/20261024T134255988081Z-phasebarrier-pilot1-b853/summary.json) | pilot, interactive | 8 | all completed |
| [`20261024T134557967888Z-phasebarrier-pilot2-b853`](evidence/20261024T134557967888Z-phasebarrier-pilot2-b853/summary.json) | pilot, interactive | 8 | all completed |
| [`20261024T134644215653Z-hostlife-phasebarrier-cli-control-b853`](evidence/20261024T134644215653Z-hostlife-phasebarrier-cli-control-b853/summary.json) | production-path control | 3 | 3 `ok` |

All raw checksums verified with no unattested files. The measured series ran
every planned unit; 30 distinct worker generations were identified, and none
survived its unit or the run. The `measure.py` that ran it has SHA-256
`f6f39c6b…`; the original raw directories are not retained. The
measured order, seed 20261024, is in that run's `summary.json`. In brief,
across sequences 0–29, the three hold-0, 200 and 800 boundary conditions
recur in all five rounds. The dense, unsampled and deadline conditions fall
in rounds one to three.

## The implementation as verified

Worker, [`pw_probe_runner.c`](../../../controller/tools/pw_probe_runner/pw_probe_runner.c),
`wait_for_proceed` (line 1560):

- It stores `arrived`, then samples continuous time to start its own
  allowance.
- Each pass samples the clock, checks the allowance, loads the release
  ordinal and `exit_requested`, and returns after storing `acknowledged` when
  the ordinal is its own.
- Otherwise it executes `cpu_relax`, the arm64 `yield` instruction
  (line 1535), 1000 times (line 1609).
- On expiry it publishes failure 8 (`PROCEED_TIMEOUT`, detail = allowance in
  ms) and calls `publish_done_and_exit`.
- The allowance defaults to 60,000 ms (line 292) and is set by
  `--proceed-wait-ms`.

Driver, [`CWorker.swift`](../../../runner/Sources/PWRunnerCore/CWorker.swift):

- After observing arrival, the driver calls the `phaseBoundary` callback
  between `clock.mark()` and `clock.excludeSince` (lines 1322–1325), so the
  callback's time is excluded from the host's sentinel allowance (recorded at
  line 1376).
- After the callback it marks collection closed and makes a nonblocking
  reap (line 1331). It releases only if the worker has not published `done`,
  the phase is arrived and neither acknowledged nor completed, and there is
  no violation. `phaseReleaseOrdinal` supplies the ordinal immediately before
  the store (line 1342).
- `CWorkerInput.proceedWaitMs` is internal and reaches the worker as
  `--proceed-wait-ms` (line 1159); no request sets it.

The worker's clock and the host's exclusion are separate. Nothing in the
worker pauses its allowance while the host collects.

## Method

The fixture spawns the shipped worker through `runCWorker`. The worker
applies `(version 1)(allow default)(deny mach-lookup)` to itself, arrives at
one phase whose action unlinks a file the fixture owns, and waits. The
fixture's callback sleeps for the requested hold, a controlled substitute for
collection time; no validator runs.

The four events and what observed them:

| Event | Observation | Observer and clock |
| --- | --- | --- |
| worker publishes **arrival** | not published by the worker; callback entry is the host's *recognition* of it | fixture, `CLOCK_MONOTONIC_RAW` |
| host finishes the **collection interval** | callback exit | fixture |
| host publishes **release** | driver's `phaseReleaseOrdinal` call immediately before the store; the store itself is untimed | fixture |
| worker **acknowledges** or **exits** | acknowledgement only as the final `acknowledged` flag, bounded above by the unlink's kqueue `NOTE_DELETE`; exit by kqueue `NOTE_EXIT` and the kernel's exit stamp | driver snapshot; fixture kqueue thread; `proc_pid_rusage` |

Worker CPU comes from `proc_pid_rusage(RUSAGE_INFO_V6)`, read by the fixture.
Every read is bracketed by its own clock and checked against the worker's
start stamp. The reads:

- **Boundary:** at callback entry and exit.
- **Dense:** a thread reading about every 1.26 ms until the worker exits.
- **None:** no reads during the run.

Every unit also records the worker's exact lifetime CPU from the fixture's
`RUSAGE_CHILDREN` after reap; the worker is its only child. CPU fields are
mach ticks. The fixture's calibration against `getrusage` gave 24.016–24.079
ticks per µs in all 30 units, consistent with the 125/3 ns timebase. Kernel
creation and exit stamps are placed on the monotonic axis through clock
readings taken at callback entry.

Two measurement properties bound what short intervals can show:

- **Accounting steps.** A running worker's CPU account advanced in steps of
  up to about 10 ms. In the measured dense units, 1,706 of 2,398 consecutive
  read pairs (0.71) showed no increment, and the largest increment was
  10.8 ms. A boundary delta can therefore be off by roughly that much; the
  lifetime total is not.
- **Sleep overshoot.** `nanosleep` overshot requested holds by 0.6–5.1 ms;
  actual holds are reported.

## Pilots and the production-path control

Three smoke runs in session scratch are not retained, and the two pilots are
retained. They established the following:

- The fixture's event ordering.
- The tick units of the CPU fields.
- The roughly 10 ms accounting step, which motivated adding exact lifetime
  CPU and the clock readings to the method.
- Behavior consistent with the measured series.

Pilot 2 is the first with the final fixture. No pilot failed or was
excluded.

The production-path control ran three ordinary `policy-witness run`
invocations of `specimen_mach_deny.json` under the host-lifetime observer.
Each had:

- a host generation linked to its worker and validator by `p_uniqueid`;
- a real validator collection lasting 1–9 ms (the sentinel's `excluded_ms`);
- a phase collected, closed before proceed, released and observed;
- `query_first` comparison;
- the worker and validator reaped, with nothing outliving the host.

Real collection intervals are shorter than the accounting step, so worker CPU
during them was not measured.

## Results

Values are minimum / median / p90 / maximum (ms unless noted). The
200-boundary and 800-boundary conditions have n=5; dense and unsampled have
n=3.

| Measure | 200 boundary | 800 boundary | 200 dense | 800 dense |
| --- | --- | --- | --- | --- |
| actual hold | 204.125 / 205.043 / 205.048 / 205.048 | 802.944 / 803.215 / 805.084 / 805.084 | 200.894 / 203.325 / 205.030 / 205.030 | 800.581 / 800.620 / 805.047 / 805.047 |
| worker CPU in read window | 196.050 / 203.534 / 204.651 / 204.651 | 799.101 / 800.915 / 804.820 / 804.820 | 200.315 / 202.464 / 204.312 / 204.312 | 795.342 / 797.002 / 804.850 / 804.850 |
| fraction of read window | 0.957 / 0.995 / 0.998 / 0.998 | 0.995 / 0.997 / 1.000 / 1.000 | 0.996 / 0.997 / 0.997 / 0.997 | 0.993 / 0.996 / 1.000 / 1.000 |
| of which performance-core | 196.050 / 203.516 / 204.651 / 204.651 | 799.101 / 800.905 / 804.820 / 804.820 | 200.315 / 202.464 / 204.303 / 204.303 | 795.253 / 796.997 / 804.850 / 804.850 |

The dense reader's span inside each hold gave 0.997–1.000 at 200 ms and
0.994–0.997 at 800 ms. During holds the worker's cycle counter advanced
4.02–4.39 cycles per ns of its CPU time, at 2.91–2.93 instructions per cycle.
These are observed counter ratios; the core frequency was not observed
directly.

Whole worker lives, from kernel creation to exit event, using exact lifetime
CPU:

| Condition | n | Lifetime | Lifetime CPU | Fraction |
| --- | ---: | --- | --- | --- |
| hold 0 | 5 | 13.534–13.879 | 12.359–12.594 | 0.907–0.914 |
| hold 200, boundary / dense / none | 5 / 3 / 3 | 213.602–218.564 | 212.777–217.510 | 0.992–0.996 |
| hold 800, boundary / dense / none | 5 / 3 / 3 | 814.201–830.287 | 812.925–828.894 | 0.998–0.999 |
| deadline (250 ms allowance, 400 ms hold) | 3 | 261.707–262.622 | 260.680–261.409 | 0.995–0.996 |

Before the callback began, the worker had existed 11.772–24.492 ms. That span
tracked the host's readiness wait (11–23 ms), and the worker's CPU read at
callback entry was 0.884–0.974 of it, a reading that can lag by one
accounting step. The span contains compilation, application and any wait
after arrival; the split is not observed in ordinary runs.

**Release and acknowledgement.** In all 27 non-deadline units:

- The phase arrived, its collection closed, and release was set,
  acknowledged and completed, with no violations.
- The unlink returned 0 and the file existed at callback entry and exit.
- The release call followed callback exit by 0.005–0.057 ms; the unlink
  event followed the release call by 0.060–0.266 ms.
- The worker exited 0, was reaped during grace, and
  `collection_basis = after_confirmed_reap`.

Neither the attempt's effect nor acknowledgement appeared before the release
call. The driver's own premature-publication checks recorded no
`acknowledgement_before_release` or `attempt_before_release`.

The host's sentinel record excluded the hold. A typical held unit recorded
`elapsed_ms 207, excluded_ms 205` at 200 ms and `807 / 805` at 800 ms, while
the worker's lifetime grew by the full hold.

**Deadline crossing (n=3).** In every unit the worker:

- published failure code 8, operation 11 (proceed), index 0, detail 250;
- exited 0;
- had its exit observed 248.876–249.721 ms after callback entry, and its
  kernel exit stamp 152.6–155.9 ms before the callback ended.

The worker spent 248.2–249.3 ms of CPU in a 401–405 ms window (0.615–0.619);
its CPU stopped at exit.

After the callback, the driver:

- marked collection closed;
- reaped the already-exited child (`pollStopReason child_reaped`);
- never called `phaseReleaseOrdinal`;
- recorded `releaseSet`, `acknowledged` and `completed` false, with no
  violations.

Grace was not entered, `collection_basis` was `after_confirmed_reap`, and the
sentinel recorded `elapsed_ms 405, excluded_ms 405`. The `arrived` flag and
the failure record survived. The slot did not complete, and the file still
existed after the run. This path never involved the client RPC timeout or
the host's sentinel deadline.

An estimate, not an observation: subtracting the 250 ms allowance from each
kernel exit stamp places the worker's arrival 11.4–12.3 ms after its creation,
and the host's callback 0.6–1.5 ms after that. It assumes negligible work
between expiry and exit.

**Measurement interference.** The fixture's own CPU during holds was:

- 1.54–1.76 ms (200) and 5.35–5.63 ms (800) with dense reads;
- 0.18–0.36 ms with boundary reads;
- 0.12–0.23 ms with none.

The worker's lifetime fractions agree across sampling modes, so no reading
density changed what the worker consumed. The dense reader's cost appears
only in the fixture's usage.

## Interpretation

Observed:

- A held collection interval appears almost entirely as worker CPU time, on
  one core and almost all on performance cores. It is consumed while the
  worker repeats its release check and `yield` loop.
- Holding changes how long that rate continues, not the rate. Short
  ordinary lives are about 0.91 on-CPU, perhaps because process startup is
  not all on-CPU; that cause is not established.
- The worker's allowance runs on its own clock, from before the host's
  recognition, while the host excludes the same interval from its sentinel.
  When the worker's clock wins, it fails and exits on its own. The host,
  observing the reaped child, withholds release.

Explanations not established by these data:

- why the spin occupied performance cores;
- what its cycle rate means for frequency;
- whether other processes ever displaced it (the runnable-time field
  advances in the same coarse steps);
- the background services active at the series start.

A production collection of 1–9 ms would by the same rate cost about that much
worker CPU, but that was not measured.

## Limitations and unresolved questions

- Arrival and acknowledgement times are not published by the worker. In
  ordinary runs the interval from arrival to the host's recognition is
  unobserved; only the deadline estimate bounds it.
- Worker CPU over windows shorter than about 10 ms, including real
  collections, cannot be resolved with these accounting reads.
- The fixture's sleep is not a validator: a real collection's I/O, spawn and
  reap load the machine differently.
- Multi-phase specimens, exec attempts, larger allowances and holds near the
  60 s default allowance were not exercised.
- The deadline case where the worker has published `done` but not yet
  exited when the callback returns was not separately produced.
- Release-store and acknowledgement-store times are bracketed, not observed.

## Reproduction

The [fixture README](phase-barrier/README.md) gives the build, schedule and
reader commands and their limits. The reader is `phase-barrier/analyze.py`
(SHA-256 `02f63060…`).
Each evidence directory holds the derived `summary.json` and `units.json`,
and a `run-record.json` with the process snapshot trimmed to CPU shares.
Cleanup:

- The schedule ran within its deadlines, and every identified worker
  generation was absent after its unit.
- No process running the worker executable remained when the run ended.
- The checkout lock was released.
- Fixture build intermediates are in `.tmp/phase-barrier-build`.

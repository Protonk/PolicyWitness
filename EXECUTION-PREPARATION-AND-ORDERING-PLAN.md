# Report system sleep, check fixture preparation and start short validator deadlines after the child runs

## Problem and intended result

On this machine, the first exec of a newly built executable file can take
several hundred milliseconds, while later execs of the same file are fast.
`runValidator` in
[ValidatorClient.swift](runner/Sources/PWRunnerCore/ValidatorClient.swift)
creates its I/O deadline immediately after a successful spawn. When the
deadline arrives, the loop stops without reading anything still waiting in the
pipe. When the over-budget case ran a cold validator, the startup cost was
charged to that window and the case saw no record (see Evidence). A short
window can therefore close before a newly built validator has produced its
record, and a case that needs that record fails without exercising its
intended condition.

The lifecycle fixture builder currently prevents this with a warm-up that
executes each output once before any test runs. The warm-up is advisory. It
prints statuses but does not fail on an unexpected status or a timeout, so a
broken preparation reaches the Swift tests. The short-deadline cases stay
correct only while the warm-up keeps working.

Every allowance these cases depend on also counts system sleep. Host waits
read `CLOCK_MONOTONIC` and the C worker reads continuous Mach time, and both
advance while the machine sleeps. This Mac is a laptop that idle-sleeps on
battery. After a sleep inside a case's window, the whole sleep appears to have
passed inside it, so allowances expire and records go missing. Nothing
prevents or records this today: `tests/AGENTS.md` asks whoever runs a battery
to use `caffeinate -i` and to check `pmset -g log` by hand. A failure caused
this way reads like a product failure, and during this plan's checkpoint it
could select the wrong design.

Intended result:

1. A system sleep during testing is reported. The dispatcher blocks idle sleep
   while it runs and records how long the system slept during each case. The
   Swift test library records the same for each Swift test. A failure that
   overlapped sleep still fails and says so. In the cases this plan converts,
   a sleep can cause a failure but cannot cause a pass.
2. Fixture preparation is checked. An unexpected status, a timeout or a launch
   failure stops the builder, and its callers stop before the tests that depend
   on it.
3. Cases that need a validator record before a short deadline start that
   deadline only after the fixture validator has reached `main`. A cold or
   delayed start can no longer consume the window.
4. Cases whose short allowance is incidental get a generous one. The
   aggregate-exhaustion case can no longer pass without the phase-0 record it
   claims to preserve.

Phase 1 reports sleep, Phase 2 checks the warm-up and Phase 3 gates the
deadlines. Phase 3's checkpoint relies on Phase 1's per-test sleep record, so
Phase 1 lands first. Phase 3 does not rely on Phase 2's warm-up. Phase 2 stays
useful without Phase 3 because of the worker readiness wait described under
Findings. Changes are confined to the test dispatcher, the Swift test library,
the lifecycle fixture, the Swift unit tests, their catalog entries and their
documentation. No production source, no worker-identity input
(`runner/Sources`, `controller/tools/pw_probe_runner`, the root `build.sh`,
Meson files, `runner/Package.swift`) and no signed build output changes. The
current signed app remains a valid test target.

The baseline is commit `9e49a0d`. The current signed app,
`dist/PolicyWitness.app`, is a clean build of `390f771` (build 772). Its
`Contents/Resources/Evidence/provenance.json` records worker identity
`bf9b04aefccf51568969e6914149c389d6c271da5033f65f39dc73cddaa3372e` as
`source.worker_identity`. The commits after `390f771` change no build input.

## Evidence

| Observation | Source |
| --- | --- |
| Before the warm-up, the over-budget case failed five runs out of five under the dispatcher, with first execs of 180–400 ms. It passed against an already-executed fixture. The message quotes AMFI's "no CMS blob" line followed by syspolicyd's first-launch evaluation. That the evaluation precedes `main` is the message's inference, not a measurement. | Message of commit `158a802`. The unified log no longer reaches that date. |
| Since the warm-up was added, every retained result of that case is `ok`: five, one from each pinned run in which the Swift tests compiled and ran. | `pwrunner_core_tests.log` under `suites/runner_unit/pwrunner_core_unit_executable/artifacts/` in the runs listed below |
| 13 fixture build logs record 247 warm-up execs: mean 224 ms, maximum 671 ms, 2 at or above 500 ms, and no timeouts. The `.validator` companion alone: mean 228 ms, maximum 368 ms. | `warm` lines in the fixture build logs of the runs listed below |
| Every warm-up status was identical across those logs. Base worker, `.identity-mismatch` and `.validator` exited 90. `.issuer` exited 92. `.worker-limits` exited 0. Every production-main companion exited 2 (usage refusal with no arguments). | Same logs |
| A default battery on 2026-10-17 overlapped a 232-second idle sleep on battery. The worker refused its second exec step after the shared budget was exhausted, and the host sentinel also expired. The rerun under `caffeinate -i` recorded no sleep. Sleep/wake behavior has not been tested in a controlled way. | [records/SLEEP-WAKE-VALIDATION.md](records/SLEEP-WAKE-VALIDATION.md). The runs it links are no longer retained. |
| Host waits read `CLOCK_MONOTONIC` through `MonotonicDeadline.now`, which is also the default `ChildProcessCalls.clock`. The C worker reads `mach_continuous_time`, which `docs/LIMITS.md` documents as including system sleep. | [MonotonicDeadline.swift](runner/Sources/PWRunnerCore/MonotonicDeadline.swift), [CWorker.swift](runner/Sources/PWRunnerCore/CWorker.swift), [pw_probe_runner.c](controller/tools/pw_probe_runner/pw_probe_runner.c), [LIMITS.md](docs/LIMITS.md#execution-budgets) |
| `CLOCK_MONOTONIC` "will continue to increment while the system is asleep". `CLOCK_UPTIME_RAW` increments "in the same manner as `CLOCK_MONOTONIC_RAW`, but … does not increment while the system is asleep". Only the raw clock is described as unaffected by frequency adjustments. Reading the two raw clocks together on this machine shows a gap of many hours, the same order as its accumulated sleep since boot. | `man clock_gettime`. Reproduce with `time.clock_gettime_ns`, `sysctl kern.boottime` and `pmset -g log`. |
| `/usr/bin/python3` implements `time.monotonic` with `mach_absolute_time()`, which does not advance during sleep. | `time.get_clock_info('monotonic')` |

The warm-up figures come from the runs under `tests/out/runs/` that
`tests/RETAINED.json` pins and that contain a fixture build:
`apple-silicon-repair-default-1`, `doc-rework-candidate-20261019`,
`doc-rework-test-build-fixes-20261019`,
`doc-rework-test-build-fixes-2-20261019`, `release-0.3.1-default`,
`release-0.3.1-optins` and `validator-selection-receipts-20261018`. Swift
compilation failed in `doc-rework-test-build-fixes-20261019`, so it
contributes a build log but no test result. Unpinned runs are not counted
because pruning can remove them. The runs are gitignored and local to this
checkout. Phase 2 keeps the `warm` lines, so every fixture build log will go
on recording the cold cost.
These costs are context, not acceptance thresholds. Nothing here should become
a fast-enough-to-be-warm assertion.

## Findings and scope

| Location | Finding and consequence |
| --- | --- |
| [Dispatcher](tests/lib/suite_run.py), `execute` and `finish` | Runs each invocation and records wall-clock start and finish times only. Nothing blocks or records system sleep. `finish(...)` is also called directly by `check_accounting.py`, so a new parameter needs a default. |
| [Swift test library](runner/Tests/PWRunnerCoreTests/TestKit.swift), `TestKit.run` | Prints `  ok   <name>` or `  FAIL <name>: <reason>`. The [runner_unit wrapper](tests/suites/runner_unit/run.sh) fails on any line starting with `SKIP` or `FAIL` and reads the last `N/M tests passed` line. `opt_in/reaped_ack_mutation.py` compares `ok` lines exactly, and `opt_in/exec_reader_mutations.py` collects `FAIL ` lines and rejects any `SKIP` in the log. A sleep note must therefore be a separate line that starts with neither and contains no `SKIP`. Scratch-package controls copy `TestKit.swift`, so it must stay Foundation-only. |
| [Lifecycle builder](tests/fixtures/worker_lifecycle/build.sh), final Python block | Executes `${OUTPUT}` and the glob `${OUTPUT}.*` with no arguments, stdin at EOF and a 30-second timeout. A launch failure raises and stops the script under `set -e`. An unexpected status or a timeout is printed and ignored. The glob would also execute an adjacent file the builder did not produce. The comment justifies the warm-up by the 150 ms case. The timeout and elapsed times use `time.monotonic`, so a system sleep cannot produce a warm-up timeout. |
| [Worker driver](runner/Sources/PWRunnerCore/CWorker.swift), `readyByteTimeoutMs` | The ready-byte wait is 1,000 ms for every worker, including the lifecycle fixtures. The slowest retained cold exec took 671 ms, two-thirds of that wait. This, not the 150 ms case, is why the warm-up stays mandatory after Phase 3. |
| [Fixture helper](tests/lib/case.sh), `test_build_fixture` | Fails the case when the builder exits nonzero. Callers: `runner_unit/run.sh` (before `swift run`), and in `witness_contract`, `unfamiliar_diagnostic_transport.sh`, `worker_sparse_failure.sh`, `worker_progress_and_failure.sh` and `opt_in/mutations.sh`. A nonzero builder already stops all of them, so they need no change. |
| [Validator driver](runner/Sources/PWRunnerCore/ValidatorClient.swift), `runValidator` | Creates its `MonotonicDeadline` after the spawn returns. Accepts `spawn: ValidatorSpawnCall`, which defaults to `nativeValidatorSpawn`: `posix_spawn` with the driver's file actions and argv `sb_api_validator --batch <pid>`. |
| [Orchestrator](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), internal `run` overload | Already passes `validatorSpawn` to every phase's `runValidator`. The aggregate start is sampled before the spawn and the end after collection, so time spent waiting inside the spawn is debited from the aggregate exactly as startup is now. The per-phase timeout is fixed before the spawn. |
| [Lifecycle validator](tests/fixtures/worker_lifecycle/validator.c) | `main(void)` ignores argv and arms `alarm(10)`. It reads stdin to EOF before writing its record (except in `close_input` mode). With `io_hang` it keeps stdout open, so collection ends at the deadline. |
| [OrderingTests](runner/Tests/PWRunnerCoreTests/OrderingTests.swift) | Three cases need a record before a deadline that starts at the spawn: `validator collection may outlast the worker budget...` (150 ms, public overload), `validator_io_timeout_ms returns partial prediction...` (50 ms, public overload) and `surviving validator cannot publish...` (100 ms, calls `runValidator` directly). The three `validator_cleanup_unconfirmed_releases_worker` variants end at EOF. Their 100 ms allowance is only a cap, but a cold start can reach it first. |
| [PhaseProtocolTests](runner/Tests/PWRunnerCoreTests/PhaseProtocolTests.swift) | `aggregate collection exhaustion...` gives phase 0 about 29 ms. It asserts the phase-0 `deadline` stop but not the phase-0 record, so after a slow start it passes with nothing tested. `M08` uses 100 ms and asserts the phase-0 record. It already passes a `validatorSpawn` closure that opens the late-write gate before the second spawn. `phaseRun` accepts `spawn:`. |

## Choices

### Report sleep instead of excluding it

Production allowances count sleep on purpose, and `docs/LIMITS.md` documents
that for the worker. Making them exclude sleep would change what a user's
timeouts mean and would change production sources and the worker identity.
That is a product decision, not a test fix, and this plan leaves it alone.

The dispatcher prevents the common case. It holds an idle-sleep assertion
(`/usr/bin/caffeinate -i`) for as long as it runs, which works on battery. That
covers idle sleep, the kind recorded on 2026-10-17. Closing the lid, choosing
Sleep from the Apple menu and low-battery sleep still happen.
`/usr/bin/caffeinate` is on the sealed system volume, like the other base tools
the harness already calls without declaring them as equipment, so this adds
nothing to install.

For every sleep that still happens, the harness records it. It reads two
clocks at the start and end of each invocation and each Swift test:
`CLOCK_MONOTONIC_RAW`, which counts sleep, and `CLOCK_UPTIME_RAW`, which does
not. If the first advanced further, the difference is how long the system
slept. The raw pair shares one timebase and neither is frequency-adjusted, so a
long awake interval cannot be mistaken for sleep. This is a reading inside the
test harness. No production timestamp is compared across clocks. The
dispatcher records each invocation, but `runner_unit` runs hundreds of Swift
tests inside one invocation, so the Swift test library records each test as
well.

No step puts the machine to sleep to test this. Inducing a sleep interrupts
every session on the Mac and needs someone to wake it, and no check in the
harness could confirm that the person using the Mac agreed to it. Controls
with substituted clock readings establish the reporting, and the man page
establishes which clock counts sleep. The first real sleep that overlaps a run
supplies a live observation.

The record states that a sleep overlapped a case, not that it caused the
outcome. A failing case that overlapped sleep still fails. The record marks the
failure as not creditable product evidence, and the case needs a run that did
not overlap sleep. A pass is unchanged.

If `caffeinate` cannot be launched or exits early, the dispatcher records that
and continues. The sleep record still makes any affected failure say why.
Refusing to run instead would stop every run in a harness that refuses the
assertion and would add nothing the record does not already provide. The
dispatcher records that `caffeinate` was launched and still running at the end
of the run, not that sleep was prevented. It cannot observe the assertion's
effect, and the sleep record observes the outcome.

### Start the deadline after the child runs instead of controlling the clock

A receipt the fixture validator writes as its first action in `main` marks the
point after which the deadline can safely start. If the test's spawn function
returns only after that receipt exists, `runValidator` starts its unchanged
deadline with the child already running. The receipt is written after dyld has
run, so this excludes any startup cost that lands before `main`, whatever its
cause.

That premise is tested directly. Before any other case is converted, the
checkpoint runs a cold copy of the validator with and without the gate. If the
gated cold run fails, the cost lands after `main`, and the clock-control
alternative described below becomes the path.

The spawn seam already exists at every level these cases use. Through it, they
keep the real collector, the real deadline, real pipes and the real fixture
processes. No production change is needed, and the cases keep exercising
production's real-time deadline, so no replacement deadline coverage is
needed.

The alternative was to add clock and read substitutions to `runValidator` and
the orchestrator's aggregate accounting, and to drive worker expiry and
validator output through test gates. That would make these orderings hold by
construction, independent of machine load. It would also change production
code paths, add fixture modes, and need new deadline-semantics tests to replace
what real clocks currently exercise.

What this plan gives up: once the child is running, it still has to read its
requests to EOF and write its record against a real deadline. That is a few
milliseconds of work in a 500 ms window. The margin is large but not
guaranteed under arbitrary load, which is the same standard every other short
real-time window in the suite accepts. If post-start races are observed later,
the clock and read substitutions can still be added on top of this change.

### Do not execute shipped executables during the build or at dispatch

No observed failure involves a cold shipped binary. `PWRunner` has no harmless
direct entry point: unrecognized arguments fall through to the XPC listener,
and adding an entry point changes production. A user's machine has never
executed these files, so their cold first exec is the real first-run behavior,
whatever this machine has cached.

Release acceptance (`tests/lib/release_accept.py`) extracts the ZIP and runs
`smoke/specimen_file_read_deny` and `witness_contract/happy_path_baseline`
against the extracted app. Executing the binaries first, during the build or
at dispatch, would make those runs less like a user's first run, not more.

The cold cost of a shipped worker relative to the 1,000 ms readiness wait is
unmeasured. A readiness timeout or XPC failure traced to a cold shipped binary
is a production finding about `readyByteTimeoutMs`, to be investigated as
such, not masked by preparation.

## Phase 1: block idle sleep and report the sleep that still happens

### 1. Hold an idle-sleep assertion and record sleep per invocation

In `tests/lib/suite_run.py`, at the start of `execute`:

- Launch `/usr/bin/caffeinate -i -w <dispatcher pid>` with `subprocess.Popen`,
  not `scope.popen`, with standard streams on `/dev/null`, descriptors closed
  so it never holds the checkout lock, and a new session so a terminal
  interrupt reaches the dispatcher's own handling instead of ending the
  assertion early. `-w` releases the assertion if the dispatcher dies.
- Stop and reap it in the existing `finally`, after the artifact inventory.
- Record `idle_sleep_assertion` in `run.json` as `launched`, `running_at_end`
  and `error`. A launch failure or early exit is recorded and printed once and
  does not change `ok`.

Around each command, next to `started_at_unix_ms` and `finished_at_unix_ms`,
read `CLOCK_MONOTONIC_RAW` and `CLOCK_UPTIME_RAW` with `time.clock_gettime_ns`.
Record `system_sleep_ms` on the invocation as the difference between the two
clocks' advances, in whole milliseconds. Copy the value to each of that
invocation's `case_results` entries. A blocked invocation records `null`. If a
reading fails or the difference is negative, record `null` with the reason,
never 0.

In `finish`, for each invocation whose `system_sleep_ms` is at least 1, print
one `SLEEP:` line to stderr beside the `HARNESS:` lines. It names the
invocation's cases with their statuses and the milliseconds slept. For a
failing case it adds that the failure is not creditable product evidence. Give
`finish` the assertion record as a keyword parameter with a default, so the
accounting controls' direct calls keep working. Sleep never changes a status or
`ok`.

### 2. Record sleep per Swift test

In `TestKit.swift`, read the same raw pair at the start and end of each
`tk.run`. When the system slept at least 1 ms, write a separate line directly
after the case's `ok` or `FAIL` line. For example:
`       system slept 2000 ms during this case`. That line must not start with
`ok`, `FAIL` or `SKIP` and must not contain `SKIP`. The case's outcome, its
`ok`/`FAIL` line and the summary line are unchanged. Take the clock pair from a
stored closure that defaults to the real clocks, so a control can substitute
readings. `TestKit.swift` stays Foundation-only.

In `tests/suites/runner_unit/run.sh`, when the log has internal `FAIL` lines,
extend the failure message with how many of them are followed by a sleep line,
for example `(2 of 3 failures overlapped system sleep)`.

### 3. Replace the operator instruction

Replace the `tests/AGENTS.md` paragraph that begins "Worker allowances count
system sleep". The new paragraph says that host and worker allowances count
system sleep, and that the dispatcher blocks idle sleep and records sleep per
case and per Swift test. It also says that a failure that overlapped sleep is
not creditable either way and needs a run that did not. Document
`idle_sleep_assertion`, `system_sleep_ms` and the `SLEEP:` line in the `run.json`
description in [tests/README.md](tests/README.md) and in the
[dispatcher README](tests/suites/dispatcher/README.md). Document the Swift
sleep line and the wrapper message in the
[runner_unit README](tests/suites/runner_unit/README.md).

### Phase-1 checks

- Dispatcher controls. In `check_accounting.py`, supply constructed clock
  pairs:
  - Equal advances and a sub-millisecond gap record 0.
  - A 1 ms gap records 1, and a 2,000 ms gap records 2,000.
  - A negative gap and a failed read record `null` with a reason.
  - A failing and a passing case with 2,000 ms of sleep keep their statuses
    and `ok`. Both appear in a `SLEEP:` line, and only the failure is marked
    not creditable.

  Substitute an unlaunchable `caffeinate` path at the module boundary. The run
  must complete with `launched: false`, an error and unchanged accounting. In
  the cancellation controls, no `caffeinate` may outlive the dispatcher after
  an interrupt, and the checkout lock must be free immediately.
- A Swift test-library control as a new `runner_unit` case, registered in
  `tests/catalog.json` and the runner_unit README following
  `service_admission_controls.py`'s scratch-package pattern. With substituted
  readings:
  - A passing case and a failing case that slept 2,000 ms keep their exact
    `ok`/`FAIL` lines, followed by the sleep line.
  - An awake case prints no sleep line.
  - The wrapper's `SKIP`/`FAIL` pattern and the summary line are unaffected.

  With the real clocks, an ordinary case prints no sleep line.
- Positive runs: `tests/run.sh --suite dispatcher` and
  `tests/run.sh --suite runner_unit` record `launched: true` and
  `running_at_end: true`. Every invocation records `system_sleep_ms: 0`, and
  the Swift log has no sleep line. The `runner_unit` suite selector includes
  the opt-in mutation controls that parse the Swift log, so they confirm the
  sleep line leaves their parsing intact. While one of these runs is in progress,
  `pmset -g assertions` lists the `caffeinate` assertion as
  `PreventUserIdleSystemSleep`.
- Do not put the machine to sleep to test this (see Choices). The first real
  sleep that overlaps a run after this change supplies a live observation:
  its `system_sleep_ms` can be compared with the duration on the `Sleep` line
  of `pmset -g log`, which has whole-second resolution. Phase 1 does not wait
  for it, and no step depends on it.

Phase 1 is complete when every control and positive run passes.

## Phase 2: check the lifecycle fixture warm-up

### 4. Make the builder's warm-up fail closed

In `tests/fixtures/worker_lifecycle/build.sh`, record each output and its
expected status where it is compiled. For example, a small shell function
could run the compile command and append the output path and status to two
arrays. A new companion then cannot be compiled without entering the
inventory. Pass the arrays to the Python block in place of the glob.

| Output | Expected exit with no arguments |
| --- | --- |
| `${OUTPUT}` and `.identity-mismatch` | 90 |
| `.validator` | 90 (stdin at EOF) |
| `.issuer` | 92 |
| `.worker-limits` | 0 |
| `.apply-failure`, `.params-CREATE`, `.params-SET`, `.map-failure`, `.read-failure` and every `.clock-*` companion | 2 (usage refusal) |

These are the statuses recorded in every retained log. Keep the invocation (no
arguments, stdin at EOF, output discarded, only the standard descriptors open)
and the 30-second timeout.

Execute every listed output and print each line as now. Treat an unexpected
status, a timeout or a launch error as a failure, but record it and continue,
so that a single log identifies every failure. After the last output, exit
nonzero if any execution failed. Do not retry. Elapsed time stays diagnostic.

Rewrite the block's comment to give the actual reason: the first exec of a
newly built fixture can take several hundred milliseconds, a substantial part
of the fixture workers' 1,000 ms readiness wait, so tests must not be the
first to execute a fixture. Update the warm-up paragraph in the
[fixture README](tests/fixtures/worker_lifecycle/README.md), removing "The
warm-up asserts nothing", and the corresponding sentence in the
[runner_unit README](tests/suites/runner_unit/README.md).

### Phase-2 checks

Run the default `runner_unit` cases, the three default `witness_contract`
cases that build the fixture, and `witness_contract/order_barrier_mutations`
explicitly. The last is the only caller the default battery does not exercise.
Each build log must list all nineteen outputs with their expected statuses.

In a second worktree with `PW_APP_DIR` set to the current signed app, make
these one-time controls and record them with the change. Do not add a
permanent case for them:

- Change one expected status. The builder must exit nonzero with that
  output's mismatch line. `runner_unit/pwrunner_core_unit_executable` must
  fail without starting `swift run`: no Swift test log may be produced.
- List an output that does not exist. The builder must still report every
  other output, then exit nonzero.
- Lower the timeout and list an output that sleeps past it. The builder must
  report `timeout` for it and exit nonzero, and no child may outlive the
  builder.

Phase 2 is complete when the builder fails closed on all three controls,
every caller stops on a builder failure, and the positive runs pass.

## Phase 3: start short validator deadlines after the fixture validator runs

### 5. Give the fixture validator an optional start receipt

Change `validator.c` to `main(int argc, char **argv)`. When `argc` is at least
4, `argv[3]` names a receipt path supplied by the test, and an optional
`argv[4]` gives a start delay in milliseconds (0–5,000). Immediately after
`alarm(10)`, the validator sleeps for the delay, then creates `argv[3]` with
`O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW`, writes
`started pid=<getpid()> delay_ms=<n>`, and closes it. On any failure it exits
95. In every other respect its behavior is unchanged.

The driver's argv has three elements, so the warm-up and every
production-shaped spawn are unaffected. The delay is a test perturbation
standing for time between spawn return and the child's query loop. It does not
emulate Gatekeeper.

### 6. Add a gated spawn function for the tests

Add one helper in the test target, shared by `OrderingTests` and
`PhaseProtocolTests`. It returns a `ValidatorSpawnCall` and keeps test-owned
state: receipt paths, spawned PIDs, elapsed times and equipment failures.

For each call, the helper:

1. Chooses an absent path `/tmp/pw-validator-started-<UUID>`.
2. Copies the driver's argv elements, appends the receipt path (and the delay,
   when the case configures one), and calls `nativeValidatorSpawn` with the
   driver's executable path and file actions unchanged.
3. Returns a nonzero result unchanged.
4. Otherwise, waits up to 5 seconds measured on `CLOCK_UPTIME_RAW` (below the
   fixture's 10-second alarm) until the receipt exists and names the spawned
   PID.
5. Records the time from spawn return to receipt on `CLOCK_UPTIME_RAW`, then
   returns 0.

Both measurements use a clock that stops during sleep. A sleep therefore cannot
expire the watchdog or make an ignored delay look like 1,000 ms.

If the watchdog expires, the helper records an equipment failure naming the
PID and returns 0, so the production collector keeps ownership of the child's
collection and cleanup. Each case checks the helper's failures first and
reports them as equipment failures, distinct from its behavioral assertions.

The helper never reaps or signals a child. Existing cleanup ownership is
unchanged: `cleanupOrderingChild`, the `ChildProcessCalls` substitutions and
M08's deferred reaping. Receipt paths are removed on exit. The helper is used
only with the lifecycle validator, never with the shipped `sb_api_validator`.

### 7. Apply it to the dependent cases

| Case | Change | Preserved |
| --- | --- | --- |
| `validator collection may outlast the worker budget...` | Internal `CWorkerOrchestrator.run` overload with the gated spawn. `validator_io_timeout_ms` 150 → 500. | `proceed_expire:50`. Worker failure (operation 11, detail 50), unset release, synthetic attempt, `unestablished` order, one retained record with a `deadline` stop, and reply encoding. The echo assertion is updated to 500. |
| Same case, delayed start (new) | Same arrangement with a 1,000 ms start delay. | Every assertion above, plus `delay_ms=1000` in the receipt and a spawn-to-receipt time of at least 1,000 ms on `CLOCK_UPTIME_RAW`, so neither an ignored delay nor a sleep can pass. |
| Same case, cold copy (new) | Copy `.validator` to a fresh path, `/tmp/pw-cold-validator-<UUID>`, and pass it as the validator. Gated spawn, 500 ms. Remove the copy afterwards. | Every assertion of the base case. Print the spawn-to-receipt time in the case log, but assert no bound on it: the OS may stop charging new files, and the delayed variant already guards the gate. |
| `validator_io_timeout_ms returns partial prediction...` | Internal overload with the gated spawn. Override 50 → 500. | The error text and echo follow the new value. Worker release, `query_first` and a successful attempt. |
| `surviving validator cannot publish...` | `runValidator(..., spawn:)` with the gated spawn. Allowance 100 → 500. | Failed termination, the native `EPIPE` receipt after return, one verdict, the worker's effect, `query_first`. |
| `validator_cleanup_unconfirmed_releases_worker` variants | No gate. Allowance 100 → 5,000. Collection ends at EOF, so only the cap changes. | `eof` stop, unreaped child, one verdict, `unconfirmed` disposition, effect, `query_first`. |
| `aggregate collection exhaustion...` | `phaseRun(spawn:)` with the gated spawn. `validator_total_timeout_ms` 30 → 500 and `validator_io_timeout_ms` 100 → 1,000, so the aggregate stays the binding limit. Add an assertion that phase 0's records are exactly `["s0"]`. | Phase-0 `deadline` stop, phase-1 `budget_exhausted` with no subprocess, worker-sourced attempts, and `unestablished` order for step 1. |
| `M08` | Its existing closure keeps opening the late-write gate before later spawns, then calls the gated spawn and records the PID. `validator_io_timeout_ms` 100 → 500. | Every current assertion, the matrix row and cross-reader replay. Its `later` phase still ends at EOF. |

Leave the other ordering cases unchanged.

In these cases, a sleep can only take away something an assertion requires: a
record missed at the deadline, an EOF cap reached first or a readiness wait
expired. It cannot supply one. With the delayed variant's bound measured on
`CLOCK_UPTIME_RAW`, a sleep can make a converted case fail but cannot make it
pass, and Phase 1's sleep line names the failure.

### Checkpoint before converting the remaining cases

Convert the over-budget case first, keeping its original 150 ms value for these
runs. Each cold run uses its own fresh copy of `.validator`, made as in the
cold-copy variant. "Ungated" means the spawn returns immediately while still
passing any delay argument.

1. Ungated, cold copy: fails for the missing record. This reproduces the
   failure recorded in `158a802` and shows that the cold cost reaches the
   collection window.
2. Gated, cold copy: passes with the record retained. Its spawn-to-receipt
   time shows the cost being absorbed before the receipt.
3. Gated, warm fixture, no delay: passes.
4. Gated, 1,000 ms delay: passes with the record retained.
5. Ungated, 1,000 ms delay: fails for the missing record.

Every checkpoint run carries Phase 1's sleep record. A run that overlapped
sleep is void whatever its outcome. Sleep can produce the expected failure of
runs 1 and 5 as easily as a false failure of runs 2–4. Each of the five runs
needs a result that did not overlap sleep. A void run is an unusable
observation, not a flaky one, and it is reported with the rest.

Run 2 answers whether the cost lands before `main`. If it fails, the cost lands
after the receipt and this design cannot remove the race. Stop Phase 3 and take
up the clock-control design described under Choices.

If run 1 passes, that copy's cold cost did not reach the window, and runs 1
and 2 establish nothing about the cost's location. Record the result, try
further fresh copies, and report every attempt. Do not proceed on a pair that
does not discriminate.

If run 5 passes, the delay is not landing inside the window and the gate's
effect is not demonstrated. Stop and reassess.

When log access works (it needs an unsandboxed shell), capture syspolicyd and
AMFI lines from the unified log covering runs 1 and 2. The timing result does
not depend on them.

Then widen to 500 ms and convert the remaining cases. Retain the checkpoint
runs, and put their outcomes, spawn-to-receipt times, void runs and any log
lines in the Phase 3 commit message. Runs 1 and 5 are checkpoint evidence
only. Do not add them as permanent cases, because they pin an incidental
property of production: that the deadline starts at spawn return.

### Phase-3 documentation

- Describe the start receipt and delay arguments in the validator section of
  the [fixture README](tests/fixtures/worker_lifecycle/README.md). The
  [fixture catalog](tests/fixtures/README.md) names the `.validator` companion
  without listing its modes, so it needs no change.
- Describe in the [runner_unit README](tests/suites/runner_unit/README.md)
  which cases start collection after the receipt, and that the receipt is
  equipment, not evidence of a PolicyWitness deadline. Note that the cold-copy
  variant prints its spawn-to-receipt time.
- `tests/FAILURE-PROPAGATION-CONTRACT.md` needs no change. Its M08 prose and
  scenario-matrix row describe controlled validator calls and their
  observations, not timing values, and it does not describe the aggregate
  case. If a later edit is needed there, M08's row lies in a block that
  `docs/generate_limits.py` generates from
  `tests/fixtures/comparison/matrix.json`, so edit that input and regenerate.

No request, reply or envelope meaning changes.

## Out of scope

- **Making production allowances exclude sleep, observing the worker's
  continuous clock across an actual sleep, and inducing a sleep to test the
  record.** See Choices.
- **`runOrderingGateControl`'s 100 ms sleep.** This is an absence-sensitivity
  weakness in the barrier mutation control, not a startup race: an early
  release can go unseen if the child has not run within the sleep. A child
  checkpoint reported before the callback returns would fix it. That change
  touches the mutation driver, its oracle and `tests/OPT_IN_TESTS.md`, and
  requires rerunning `witness_contract/order_barrier_mutations`, so it is a
  separate change.
- **The `orderingWorker` 200 ms sentinel.** The sentinel starts after
  readiness, with the worker already running, so no startup cost is charged to
  it.
- **Clock and read substitutions, production allowances, the shipped-binary
  first run, and preparation of shipped executables.** See Choices.
- **How macOS keys first-exec state, and whether copies, extractions,
  re-signing, network reachability or reboots change it.** No decision here
  depends on these.

## Verification and completion

| Checkpoint | Required checks |
| --- | --- |
| Phase 1 | The Phase-1 controls and positive runs above. |
| Phase 2 | The Phase-2 runs and controls above. |
| Phase-3 checkpoint | `runner_unit/pwrunner_core_unit_executable` with the five over-budget runs, each with a result that did not overlap sleep. |
| Phase-3 integrated | Default `runner_unit` cases and the three fixture-building `witness_contract` cases. `python3 docs/generate_worker_identity.py --check` must pass and print the signed app's worker identity, `bf9b04ae…` (see the baseline), showing that no identity input changed. |
| Final | Full `source_drift`, the full `dispatcher` suite and the default battery against the current signed app. |

Phase 3 is complete when all of these hold:

- The seven gated cases record a start receipt naming their spawned PID.
- The delayed variant passes with its delay observed, and the cold-copy
  variant passes and prints its spawn-to-receipt time.
- In the checkpoint, the gated cold run passed and both ungated runs failed
  for the missing record, none of them overlapping sleep. The Phase 3 commit
  message records those results and any void runs.
- The EOF variants and the aggregate case carry their new allowances and
  assertions.
- All selected checks pass.

Report builder failures, gated-spawn watchdog failures and behavioral failures
distinctly, and name any sleep that overlapped a failure.

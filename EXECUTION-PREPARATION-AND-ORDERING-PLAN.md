# Check fixture preparation and start short validator deadlines after the child runs

## Problem and intended result

On this machine, the first exec of a newly built executable file can take
several hundred milliseconds, while later execs of the same file are fast.
`runValidator` in
[ValidatorClient.swift](runner/Sources/PWRunnerCore/ValidatorClient.swift)
creates its I/O deadline immediately after a successful spawn. When the
over-budget case ran a cold validator, the startup cost was charged to that
window (see Evidence). When the deadline arrives, the loop stops without
reading anything still waiting in the pipe. A short window can therefore close
before a newly built validator has produced its record. A case that needs that
record then fails without exercising its intended condition.

The lifecycle fixture builder currently prevents this with a warm-up that
executes each output once before any test runs. The warm-up is advisory. It
prints statuses but does not fail on an unexpected status or a timeout, so a
broken preparation reaches the Swift tests. The short-deadline cases stay
correct only while the warm-up keeps working.

Intended result:

1. Fixture preparation is checked. An unexpected status, a timeout or a launch
   failure stops the builder, and its callers stop before the tests that depend
   on it.
2. Cases that need a validator record before a short deadline start that
   deadline only after the fixture validator has reached `main`. A cold or
   delayed start can no longer consume the window. This depends on the cost
   landing before `main`, which Phase 2's checkpoint establishes before any
   other case is converted.
3. Cases whose short allowance is incidental get a generous one. The
   aggregate-exhaustion case can no longer pass without the phase-0 record it
   claims to preserve.

Neither kind of failure is repaired by repeating a specimen or a suite.

The two phases are independent. Phase 2 does not rely on Phase 1's warm-up.
Phase 1 stays useful without Phase 2 because of the worker readiness wait
described under Findings. Changes are confined to the lifecycle fixture, the
Swift unit tests and their documentation. No production source, no
worker-identity input (`runner/Sources`, `controller/tools/pw_probe_runner`,
the root `build.sh`, Meson files, `runner/Package.swift`) and no signed build
output changes. The current signed app remains a valid test target.

The baseline is commit `242bb36`.

## Evidence

| Observation | Source |
| --- | --- |
| Before the warm-up, the over-budget case failed five runs out of five under the dispatcher, with first execs of 180–400 ms. It passed against an already-executed fixture. The message quotes AMFI's "no CMS blob" line followed by syspolicyd's first-launch evaluation. It infers that the evaluation happens before the process starts but does not measure this. | Message of commit `158a802`. The unified log no longer reaches that date, so the message is the only surviving record of those log lines. |
| Since the warm-up was added, all 72 retained results of that case are `ok`. | `pwrunner_core_tests.log` under `tests/out/runs/*/suites/runner_unit/pwrunner_core_unit_executable/artifacts/` |
| 206 retained fixture build logs record 2,812 warm-up execs: mean 232 ms, maximum 938 ms, 19 at or above 500 ms, and no timeouts. The `.validator` companion alone: mean 224 ms, maximum 781 ms. | `warm` lines in the build logs under `tests/out/runs/` |
| Every warm-up status was identical across those logs. Base worker, `.identity-mismatch` and `.validator` exited 90. `.issuer` exited 92. `.worker-limits` exited 0. Every production-main companion exited 2 (usage refusal with no arguments). | Same logs |

The retained runs are gitignored and local to this checkout. Phase 1 keeps the
`warm` lines, so every fixture build log will go on recording the cold cost.
These costs are context, not acceptance thresholds. Nothing here should become
a fast-enough-to-be-warm assertion.

Two questions have no retained evidence behind them:

- **Where the cost lands relative to `main`.** Phase 2 depends on the answer,
  and its checkpoint provides it.
- **Whether a copy, extraction or re-signing of a signed file starts cold.**
  No decision here depends on the answer.

## Findings and scope

| Location | Finding and consequence |
| --- | --- |
| [Lifecycle builder](tests/fixtures/worker_lifecycle/build.sh), final Python block | Executes `${OUTPUT}` and the glob `${OUTPUT}.*` with no arguments, stdin at EOF and a 30-second timeout. A launch failure raises and stops the script under `set -e`. An unexpected status or a timeout is printed and ignored. The glob would also execute an adjacent file the builder did not produce. The comment justifies the warm-up by the 150 ms case. |
| [Worker driver](runner/Sources/PWRunnerCore/CWorker.swift), `readyByteTimeoutMs` | The ready-byte wait is 1,000 ms for every worker, including the lifecycle fixtures. The 938 ms maximum cold start leaves little margin. This, not the 150 ms case, is why the warm-up stays mandatory after Phase 2. |
| [Fixture helper](tests/lib/case.sh), `test_build_fixture` | Fails the case when the builder exits nonzero. Callers: `runner_unit/run.sh` (before `swift run`), and in `witness_contract`, `unfamiliar_diagnostic_transport.sh`, `worker_sparse_failure.sh`, `worker_progress_and_failure.sh` and `opt_in/mutations.sh`. A nonzero builder already stops all of them, so they need no change. |
| [Validator driver](runner/Sources/PWRunnerCore/ValidatorClient.swift), `runValidator` | Creates its `MonotonicDeadline` after the spawn returns. Accepts `spawn: ValidatorSpawnCall`, which defaults to `nativeValidatorSpawn`: `posix_spawn` with the driver's file actions and argv `sb_api_validator --batch <pid>`. |
| [Orchestrator](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), internal `run` overload | Already passes `validatorSpawn` to every phase's `runValidator`. The aggregate start is sampled before the spawn and the end after collection, so time spent waiting inside the spawn is debited from the aggregate exactly as startup is now. The per-phase timeout is fixed before the spawn. |
| [Lifecycle validator](tests/fixtures/worker_lifecycle/validator.c) | `main(void)` ignores argv and arms `alarm(10)`. It reads stdin to EOF before writing its record (except in `close_input` mode). With `io_hang` it keeps stdout open, so collection ends at the deadline. |
| [OrderingTests](runner/Tests/PWRunnerCoreTests/OrderingTests.swift) | Three cases need a record before a deadline that starts at the spawn: `validator collection may outlast the worker budget...` (150 ms, public overload), `validator_io_timeout_ms returns partial prediction...` (50 ms, public overload) and `surviving validator cannot publish...` (100 ms, calls `runValidator` directly). The three `validator_cleanup_unconfirmed_releases_worker` variants end at EOF. Their 100 ms allowance is only a cap, but a cold start can reach it first. |
| [PhaseProtocolTests](runner/Tests/PWRunnerCoreTests/PhaseProtocolTests.swift) | `aggregate collection exhaustion...` gives phase 0 about 29 ms. It asserts the phase-0 `deadline` stop but not the phase-0 record, so after a slow start it passes with nothing tested. `M08` uses 100 ms and asserts the phase-0 record. It already passes a `validatorSpawn` closure that opens the late-write gate before the second spawn. `phaseRun` accepts `spawn:`. |

## Choices

### Start the deadline after the child runs instead of controlling the clock

If the startup cost lands between the spawn returning and `main`, a receipt
the fixture validator writes as its first action in `main` marks the point
after which the deadline can safely start. If the test's spawn function
returns only after that receipt exists, `runValidator` starts its unchanged
deadline with the child already running.

The receipt is written after dyld has run, so it excludes any cost before
`main`, whatever the cause. The design does not need to attribute the cost to
Gatekeeper. Its premise is tested directly: the checkpoint runs a cold copy of
the validator with and without the gate before any other case is converted.
If the gated cold run fails, the premise is wrong, and the clock-control
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

This decision does not depend on whether this machine treats a copied or
extracted signed file as cold. The cold cost of a shipped worker relative to
the 1,000 ms readiness wait is likewise unmeasured. A readiness timeout or XPC
failure traced to a cold shipped binary is a production finding about
`readyByteTimeoutMs`, to be investigated as such, not masked by preparation.

## Phase 1: check the lifecycle fixture warm-up

### 1. Make the builder's warm-up fail closed

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

Rewrite the block's comment to give the actual reason: first-exec cost lands
between spawn and `main`, and the fixture workers face the 1,000 ms readiness
wait, so tests must not be the first to execute a fixture. Update the warm-up
paragraph in the [fixture README](tests/fixtures/worker_lifecycle/README.md),
removing "The warm-up asserts nothing", and the corresponding sentence in the
[runner_unit README](tests/suites/runner_unit/README.md).

### Phase-1 checks

Run, with a fresh `PW_TEST_OUT_DIR`, the default `runner_unit` cases, the
three default `witness_contract` cases that build the fixture, and
`witness_contract/order_barrier_mutations` explicitly. The last is the only
caller the default battery does not exercise. Each build log must list all
nineteen outputs with their expected statuses.

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

Phase 1 is complete when the builder fails closed on all three controls,
every caller stops on a builder failure, and the positive runs pass.

## Phase 2: start short validator deadlines after the fixture validator runs

### 2. Give the fixture validator an optional start receipt

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

### 3. Add a gated spawn function for the tests

Add one helper in the test target, shared by `OrderingTests` and
`PhaseProtocolTests`. It returns a `ValidatorSpawnCall` and keeps test-owned
state: receipt paths, spawned PIDs, elapsed times and equipment failures.

For each call, the helper:

1. Chooses an absent path `/tmp/pw-validator-started-<UUID>`.
2. Copies the driver's argv elements, appends the receipt path (and the delay,
   when the case configures one), and calls `nativeValidatorSpawn` with the
   driver's executable path and file actions unchanged.
3. Returns a nonzero result unchanged.
4. Otherwise, waits under a real monotonic watchdog of 5 seconds (below the
   fixture's 10-second alarm) until the receipt exists and names the spawned
   PID.
5. Records the time from spawn return to receipt, then returns 0.

If the watchdog expires, the helper records an equipment failure naming the
PID and returns 0, so the production collector keeps ownership of the child's
collection and cleanup. Each case checks the helper's failures first and
reports them as equipment failures, distinct from its behavioral assertions.

The helper never reaps or signals a child. Existing cleanup ownership is
unchanged: `cleanupOrderingChild`, the `ChildProcessCalls` substitutions and
M08's deferred reaping. Receipt paths are removed on exit. The helper is used
only with the lifecycle validator, never with the shipped `sb_api_validator`.

### 4. Apply it to the dependent cases

| Case | Change | Preserved |
| --- | --- | --- |
| `validator collection may outlast the worker budget...` | Internal `CWorkerOrchestrator.run` overload with the gated spawn. `validator_io_timeout_ms` 150 → 500. | `proceed_expire:50`. Worker failure (operation 11, detail 50), unset release, synthetic attempt, `unestablished` order, one retained record with a `deadline` stop, and reply encoding. The echo assertion is updated to 500. |
| Same case, delayed start (new) | Same arrangement with a 1,000 ms start delay. | Every assertion above, plus `delay_ms=1000` in the receipt and a spawn-to-receipt time of at least 1,000 ms, so an ignored delay cannot pass. |
| Same case, cold copy (new) | Copy `.validator` to a fresh path, `/tmp/pw-cold-validator-<UUID>`, and pass it as the validator. Gated spawn, 500 ms. Remove the copy afterwards. | Every assertion of the base case. Print the spawn-to-receipt time in the case log, but assert no bound on it: the OS may stop charging new files, and the delayed variant already guards the gate. |
| `validator_io_timeout_ms returns partial prediction...` | Internal overload with the gated spawn. Override 50 → 500. | The error text and echo follow the new value. Worker release, `query_first` and a successful attempt. |
| `surviving validator cannot publish...` | `runValidator(..., spawn:)` with the gated spawn. Allowance 100 → 500. | Failed termination, the native `EPIPE` receipt after return, one verdict, the worker's effect, `query_first`. |
| `validator_cleanup_unconfirmed_releases_worker` variants | No gate. Allowance 100 → 5,000. Collection ends at EOF, so only the cap changes. | `eof` stop, unreaped child, one verdict, `unconfirmed` disposition, effect, `query_first`. |
| `aggregate collection exhaustion...` | `phaseRun(spawn:)` with the gated spawn. `validator_total_timeout_ms` 30 → 500 and `validator_io_timeout_ms` 100 → 1,000, so the aggregate stays the binding limit. Add an assertion that phase 0's records are exactly `["s0"]`. | Phase-0 `deadline` stop, phase-1 `budget_exhausted` with no subprocess, worker-sourced attempts, and `unestablished` order for step 1. |
| `M08` | Its existing closure keeps opening the late-write gate before later spawns, then calls the gated spawn and records the PID. `validator_io_timeout_ms` 100 → 500. | Every current assertion, the matrix row and cross-reader replay. Phase 1 still ends at EOF. |

Leave the other ordering cases unchanged.

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

Run 2 answers whether the cost lands before `main`. If it fails, the cost lands
after the receipt and this design cannot remove the race. Stop Phase 2 and take
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

Then widen to 500 ms and convert the remaining cases. Retain the runs, and put
their outcomes, spawn-to-receipt times and any log lines in the Phase 2 commit
message, so the evidence survives with the change. Runs 1 and 5 are checkpoint
evidence only. Do not add them as permanent cases, because they pin an
incidental property of production: that the deadline starts at spawn return.
Do not widen production allowances or replace replies with constructed
records.

### Phase-2 documentation

- Describe the start receipt and delay arguments in the validator section of
  the [fixture README](tests/fixtures/worker_lifecycle/README.md), with a
  one-line entry in the [fixture catalog](tests/fixtures/README.md) if it lists
  validator modes.
- Describe in the [runner_unit README](tests/suites/runner_unit/README.md)
  which cases start collection after the receipt, and that the receipt is
  equipment, not evidence of a PolicyWitness deadline. Note that the cold-copy
  variant prints its spawn-to-receipt time. READMEs describe current
  behavior; the checkpoint measurements belong in the commit message.
- Update `tests/FAILURE-PROPAGATION-CONTRACT.md` only where it describes how
  M08 or the aggregate case controls timing.

No request, reply or envelope meaning changes.

## Out of scope

- **`runOrderingGateControl`'s 100 ms sleep.** This is an absence-sensitivity
  weakness in the barrier mutation control, not a startup race: an early
  release can go unseen if the child has not run within the sleep. A child
  checkpoint reported before the callback returns would fix it. That change
  touches the mutation driver, its oracle and `tests/OPT_IN_TESTS.md`, and
  requires rerunning `witness_contract/order_barrier_mutations`, so it is a
  separate change.
- **`proceed_wait_expire`.** It already waits for the worker's `expired`
  receipt and has no startup race.
- **The `orderingWorker` 200 ms sentinel.** The sentinel starts after
  readiness, with the worker already running, so no startup cost is charged to
  it.
- **Collector and orchestrator clock or read substitutions, gate-driven worker
  expiry, and a validator emit gate.** These are not needed for this problem.
  They remain possible if post-start races are observed later.
- **Production allowances, the shipped-binary first run, and preparation of
  shipped executables.** See Choices.
- **How macOS keys first-exec state, and whether copies, extractions,
  re-signing, network reachability or reboots change it.** No decision here
  depends on these.
- **BYOXPC, installation, host retirement and retries.**

## Verification and completion

Use `tests/run.sh` with a fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>` for
each checkpoint, and inspect selections with `--list` first. Confirm canonical
case IDs in the catalog before running, and select opt-ins explicitly.

| Checkpoint | Required checks |
| --- | --- |
| Phase 1 | The Phase-1 runs and controls above. |
| Phase-2 checkpoint | `runner_unit/pwrunner_core_unit_executable` with the five over-budget runs. |
| Phase-2 integrated | Default `runner_unit` cases and the three fixture-building `witness_contract` cases. `python3 docs/generate_worker_identity.py --check` must show no identity input changed. |
| Final | Full `source_drift` and the default battery against the current signed app. |

If the automation sandbox blocks process observation or XPC, follow
`tests/AGENTS.md`'s same-command escalation rule and retain the original
result. That rule does not authorize rerunning specimens after behavioral
failures.

Phase 2 is complete when all of these hold:

- The seven gated cases record a start receipt naming their spawned PID.
- The delayed variant passes with its delay observed, and the cold-copy
  variant passes and prints its spawn-to-receipt time.
- In the checkpoint, the gated cold run passed and both ungated runs failed
  for the missing record. The Phase 2 commit message records those results.
- The EOF variants and the aggregate case carry their new allowances and
  assertions.
- All selected checks pass.

Report builder failures, gated-spawn watchdog failures and behavioral failures
distinctly. Leave unrelated working-tree changes and historical evidence
intact.

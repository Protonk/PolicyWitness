# `tests/` (test runner + suites)

This directory contains the repository test harness. The test suite is organized to answer three questions:

1. Does the built `dist/PolicyWitness.app` basically work end-to-end?
2. Did we break a contract (CLI shape, evidence artifacts, JSON output schema)?
3. Do `sandbox_check` verdicts stay consistent with kernel-observed attempt outcomes?

The harness is machine-readable: every test writes structured JSONL events and a per-run summary under `tests/out/`.

Related docs:

- CLI contract: `controller/README.md`
- Runner architecture: `runner/README.md`
- Signing/build: `SIGNING.md`
- Outcome coverage matrices: `tests/COVERAGE.md`
- Fixtures catalog: `tests/fixtures/README.md`
- Opt-in registry: `tests/OPT_IN_TESTS.md`

## How to run

Build first (signed pipeline):

```sh
make build
```

Then run tests:

```sh
make test
# or:
./tests/run.sh
./tests/run.sh --suite preflight
./tests/run.sh --suite unit
./tests/run.sh --suite integration
./tests/run.sh --suite runner_byoxpc
./tests/run.sh --suite sbpl_allowdeny_consistency
./tests/run.sh --all --list
./tests/run.sh --case blackbox_menagerie/validation_controls
```

`tests/run.sh` is the public selection and reporting interface. With no selectors
it runs the default battery. `--all` selects every registered case, including
opt-ins. Repeated `--suite NAME` and `--case SUITE/CASE` selectors form a union;
order and repetitions do not change the work. A suite selects all its members,
including any opt-in members. Case IDs are exact harness identifiers, not patterns. Rust and Swift unit
methods remain inside their respective batch cases.

`--list` prints the selected plan as JSON, including descriptions, default
membership, prerequisites, runner contexts, dependencies, and configuration.
`selection.suites` records the caller's suite selectors; `containing_suites`
maps selected cases to every suite containing them. Membership does not imply
that the caller selected that entire suite.
`--all --list` discovers the complete catalog. Help, inspection, invalid arguments,
invalid configuration, and missing entrypoint scripts leave existing evidence
untouched. `--describe` is not supported.

The catalog is `tests/catalog.json`. A case has one canonical ID; suites may
include the same ID, so shared validator-failure cases execute once even when
both suites are selected. BYOXPC cases have distinct IDs and runner contexts.
Selecting a BYOXPC specimen also selects its installation dependency, visible in
`--list`. Independent cases continue after failures. Required equipment missing
at execution is a failed run with an explicit unrun case, never an implicit skip.
For ordinary cases, Ctrl-C during command execution stops the active command's
process group and cancels queued work. Completed and partial evidence survives;
the failed summary accounts for unfinished selections with an interruption reason.

When a selection requires the app or embedded worker, the dispatcher first
requires the complete bundle layout, valid local codesign signatures, and
matching embedded manifest hashes. Invalid artifacts block those cases; offline
cases can still run. A shared read-only inspector also backs `preflight`.
The dispatcher inventories the selected app before testing and again during
finalization, including after case failures or Ctrl-C. Added, removed, or changed
files, modes, directories, and symlink targets fail the run with a retained diff.
Inspection never repairs the app. Rebuild through `build.sh` to replace a stale
artifact; regenerating evidence over a mutated app would hide the defect.
These checks do not certify notarization and cannot detect a transient mutation
restored before the final inventory. Direct suite scripts do not have this guard.

Opt-in cases are documented in `tests/OPT_IN_TESTS.md`; use an exact case, an
owning suite, `--suite opt_in`, or `--all` to select them. Direct suite scripts
remain developer entrypoints, but do not provide the public command's planning,
configuration validation, or completion guarantees.

Release ZIP acceptance is a separate explicit command:
`bash tests/accept-release.sh dist/PolicyWitness.zip`. It inspects a temporary
extraction, checks the staple and Gatekeeper assessment, runs the existing allow
and deny contracts through the extracted controller, and records the ZIP hash
and before/after integrity. It never builds or signs. See `SIGNING.md` for the
complete release procedure and the handling of delayed or uncertain Apple replies.

## Configuration

- `PW_APP_DIR`: app bundle to test; defaults to `dist/PolicyWitness.app`.
- `PW_BIN` and `PW_BIN_PATH`: compatibility aliases for the controller inside
  that bundle. Either can infer the app when `PW_APP_DIR` is absent. All supplied
  paths must agree after resolution; a standalone controller is rejected because
  tests also exercise its bundled helpers. Rust and shell tests receive the same
  resolved controller and app paths. Whole-app symlinks are supported; a
  controller symlink must stay inside its named bundle, including when a
  controller alias supplies the app path implicitly.
- `PW_TEST_OUT_DIR`: output directory, default `tests/out`. It must resolve inside
  `tests/out`, including through symlinks, and cannot overlap the tested app.
  Execution replaces this directory; inspection does not.
- `PW_TEST_RUN_ID`: evidence label; unset or empty generates one. It does not
  create a separate output directory. Labels start with a letter/digit and use
  at most 128 letters, digits, dots, underscores, or hyphens, because specimen
  fixtures embed them in paths and SBPL literals.
- `PW_TEST_QUIET=1`: suppress routine case messages. `0`, empty, or unset retains
  them. Selection, errors, and the summary remain visible.
- `PW_BYOXPC_IDENTITY`, then `IDENTITY`: signing identity override for signing
  tests; otherwise resolve an available Developer ID matching the app's team.

Relative paths resolve from the repository root regardless of the caller's
working directory. The effective paths are recorded in `plan.json` and
`run.json`. Runner-mode/service overrides, suite aliases, case selection state,
and event paths (`PW_TEST_RUNNER_*`, `PW_TEST_SUITE_OVERRIDE`, `PW_TEST_CASES`,
`PW_TEST_EVENTS`) belong to child execution and are rejected as public settings.
Select BYOXPC cases through the catalog instead.

## Tiers

- **Baseline**: ordinary default cases on supported hosts, including offline
  checker controls and live smoke, black-box, and witness contracts.
- **Opt-in**: resource-sensitive signing/launchd work or implementation mutation
  controls. Some otherwise Baseline suites also own opt-in cases; `--list` gives
  each case's exact default membership and requirements.

## Suite coverage

This is the canonical map of what each suite covers, what you can claim when it
passes, and when it legitimately skips. For exact invariants and fixtures, see
the per-suite README files under `tests/suites/<suite>/`. For the per-outcome
coverage matrices (which suite exercises each `NormalizedOutcome` /
`AttemptOutcome` value), see `tests/COVERAGE.md`.

A blank **Skips when** cell means the suite has no expected skips: missing
prerequisites should fail, not skip.

| Suite | Tier | Primary claim | Requires | Skips when | Notes / artifacts |
| --- | --- | --- | --- | --- | --- |
| `preflight` | Baseline + opt-in signing controls | Enforce bundle layout, signatures, and manifest hashes; release continuation and real deadline controls | Built app for inspection; signing controls also need matching Developer ID; release controls need no app, with macOS socket/process observation for deadlines | — | Read-only inspection; signing controls mutate disposable copies only. Select `preflight/codesign.preflight` for inspection alone. |
| `source_drift` | Baseline | The runner source manifest is consistent between the on-disk `runner/Sources/` tree and `build.sh`'s `XPC_RUNNER_*` set. (The SwiftPM package auto-discovers by convention, so its set equals disk; build.sh vs the tree is the comparison that can ship a broken `PWRunner.xpc`.) Catches a compiled file added to one but not the other before the drift ships. | Python 3 | — | `tests/out/suites/source_drift/.../check.log` |
| `shell_helpers` | Baseline | Case helpers retain arguments, logs and identity; failures stop case stages. Result helpers preserve matching terminal evidence and logging/exit behavior. Wrapper groups preserve child order, streams, and failure status while continuing later children | Bash + Python 3 | — | Independent receipts and subprocess observations; covers case/equipment failures, separate build logs, quiet output, result serialization, wrapper phase gates/cleanup, and explicit skips. No app or toolchain; BYOXPC ownership controls use fake OS/CLI commands; wrapper and worker-setup controls use simulated children. |
| `dispatcher` | Baseline | Requested suite execution, case reports, and lifecycle events determine the same shell exit status and `run.json.ok` | Bash + Python 3; cancellation also needs macOS local sockets and process observation | — | Separate reconciliation, accounting, cancellation, and selection controls. Includes kernel-observed cleanup of an interrupted ordinary case and its helper, plus executable receipts from two usable stub apps. No app or compiler. |
| `unit` | Baseline | Controller logic is correct at the unit level | Cargo toolchain | — | `tests/out/suites/unit/.../cargo-test-bins.log` |
| `runner_unit` | Baseline | Swift runner internals: `CWorkerOrchestrator` envelope invariants, `computeDrift` truth table, `classify` worker/validator→normalized-outcome table, `buildAttemptResult` (kind, action, slot)→attempt-outcome table, prediction_unavailable host-mirror, and CWorker + ValidatorClient drivers. Lifecycle controls retain independent polling, termination and confirmed-reap observations through the driver and JSON assembler. `HostOutcomeClassifierTests` exercises the production classifier with constructed results. Separate `SandboxApplyTests` checks exercise the unused Swift apply helper; they do not establish C-worker or CLI coverage. | Swift + clang; signed app for required live controls | — | `tests/out/suites/runner_unit/.../pwrunner_core_tests.log`. Wrapper builds `worker_lifecycle`; select with an app-dependent suite for integrity evidence and inspect the Swift log for internal SKIP. |
| `integration` | Baseline | CLI contract + runner envelope are stable end-to-end | Built app + XPC | — | Uses fixtures under `tests/fixtures/pw_runner/` |
| `runner_apply_isolation_v2` | Baseline | v2 deny-default specimens complete cleanly: the unsandboxed XPC host posix_spawns the C worker, the worker applies the policy and writes its slot results to shared memory, and the host replies with a full envelope | Built app + XPC | — | Asserts `runner_subprocess` and worker PID semantics |
| `runner_apply_isolation_v3` | Baseline | Same shape as `runner_apply_isolation_v2` but with SBPL v3 grammar, which has stricter validation | Built app + XPC | — | Asserts `runner_subprocess` and worker PID semantics |
| `runner_outcome_libsandbox_unavailable` | Baseline | `_test_overrides.libsandbox_path=/nonexistent` causes `SandboxLib.load(path:)` to fail with a real `dlopen` error and the host returns `normalized_outcome="libsandbox_unavailable"` without spawning a worker | Built app + XPC | — | Exercises the real loader; no stubbing. Asserts the failure message names the override path and that `test_overrides` is mirrored back |
| `runner_outcome_worker_spawn_failed` | Baseline | `_test_overrides.worker_executable_path=/nonexistent` makes `posix_spawn` return `ENOENT`; host returns `normalized_outcome="worker_spawn_failed"` | Built app + XPC | — | Asserts `runner_subprocess` is null (no worker observed) and override is mirrored back |
| `runner_outcome_runner_timeout` | Baseline | Deliberate empty-plan timeout control: host SIGKILL, failure diagnostic, honored overrides, explicit empty steps, and no validator metadata | Built app + XPC | — | Shares a focused checker with the single-write and mixed-outcome timeout cases; populated plans independently verify file effects and retained step evidence. Uses a 2s worker deadline and 8s hang; no log capture or tight wall-clock assertion. |
| `runner_outcome_bad_request` | Baseline | Two e2e cases that drive `normalized_outcome="bad_request"` through both emit sites in `PWRunnerService.runSpecimen` — Swift decode failure and `validateSandboxChecks` rejection. No `_test_overrides` needed. | Built app + XPC | — | Asserts `runner_subprocess` is null and that the error message identifies the rejected field |
| `runner_ready_byte_resilience` | Baseline | `_test_overrides.worker_pre_ready_hang_ms=2000` makes the C worker write its pre-apply ready byte after the host's 1000ms `readyByteTimeout` has closed `--ready-fd`. The worker must survive that SIGPIPE-prone write (SIGPIPE is ignored), still `sandbox_apply`, and score the probe — `normalized_outcome="ok"`. Regression guard for the `com.apple.WebProcess` slow-compile SIGPIPE bug. | Built app + XPC | — | Runs ~2-3s. Asserts `term_signal=null`, `exit_code=0`, validator ran, and the override is mirrored back. The seam delays after compilation/capture; this case has sufficient sentinel budget. The pre-apply witness uses a short budget and requires `runner_timeout`. |
| `runner_filter_iokit_registry_entry_class` | Baseline | The `(iokit-open-service, iokit_registry_entry_class)` pair returns `prediction_unavailable` with explicit sentinel/null evidence and the exact requested step. A supported file `open_read` placeholder retains attempt evidence; it does not establish IOKit enforcement. | Built app + XPC | — | Documents the "prediction-unavailable for known-drift op+filter pairs" contract |
| `runner_filter_sysctl_name` | Baseline | The `(sysctl-read, sysctl_name)` pair retains unavailable-prediction evidence and a real denied `sysctl` / `read` attempt against `kern.osrelease`. Independent checker controls exercise all three filter callers. | Built app + XPC; controls need only Python 3 | — | Shared envelope/step checks plus supported-file and sysctl-denial contracts |
| `runner_filter_iokit_user_client_class` | Baseline | `(iokit-open-user-client, iokit_user_client_class)` pair. Same `prediction_unavailable` contract; complements `runner_filter_iokit_registry_entry_class` to cover both registry-entry and user-client class matching modes. Same attempt placeholder caveat. | Built app + XPC | — | |
| `validator_batch_mode` | Baseline | Pins the `sb_api_validator --batch <pid>` NDJSON-over-stdin/stdout contract: 10 mixed-filter probes against a `sandbox-exec` child cover all four verdict outcomes (3 allow + 1 deny + 1 error + 1 bad_filter + 4 parse_error including trailing-garbage + overlong-line regressions). Per-probe failures don't abort the run; step_id is preserved when known. The production runner uses this shape per run. Per-probe CLI mode preserved unchanged for diagnostic tooling. | Built app | — | |
| `runner_validator_failure` | Baseline | Reversed partial validator replies survive clean shortfall or malformed JSON, attach to the correct step IDs, and preserve all completed attempts. The unanswered prediction has an explicit error and `drift:null`. | Built app + XPC + Python 3 | — | Checked-in validator transcripts have direct controls; CLI cases independently check file effects, degradation, honored overrides, and subprocess completion. Shared with the corresponding `witness_contract` entry points. |
| `runner_abi_layout` | Baseline | Layout-drift guard between the C ABI header and Swift `PWShmLayout`. Compiles a tiny `printer.c` against `pw_probe_runner_abi.h` at test time, harvests every `sizeof`/`offsetof`/macro value, parses the mirrored Swift enum, and asserts bidirectional agreement. Catches what parser-only `source_drift` can't model (compiler struct padding). | Toolchain only (no app) | — | Companion to `source_drift`'s enum-agreement check; both belong in the Baseline tier. |
| `runner_c_worker_harness` | Baseline | Proves `pw-probe-runner` (the C worker) in isolation across 15 hand-built-shm scenarios: `(allow default)` happy path, bare `(deny default)` isolation, clean exit-byte teardown, SIGKILL fallback, a 256-slot multi-page shared-memory run, an SBPL-params round-trip that proves `policy.params` reach the kernel (kernel-observed deny on `/etc/hosts` when `TARGET=/private/etc` is passed through `sandbox_create_params` + `sandbox_set_param`), the file unlink/create attempt kinds (allow + deny), and the worker's pre-apply self-defense exits (compile failure survives with `apply_rc=-1`; abi/prepared/step_count/param_count/policy-overflow refusals → exit 4/5/6/7/8). | Built app + harness | — | Compiles `harness.c` once per suite run into `tests/out/.../harness.runner_c_worker` |
| `runner_use_c_worker` | Baseline | End-to-end coverage of the runner's C code path. Drives real specimens through `controller → XPC service → CWorkerOrchestrator → pw-probe-runner + sb_api_validator --batch` normally without `_test_overrides` (the timeout case deliberately uses the deadline and hang seams). Covers: v4 envelope shape (validator_subprocess populated, drift computed, prediction_unavailable verdicts synthesized locally), bug-report `(deny default)` survival, and regression cases for duplicate step_ids (plan-killer), unsupported attempt combos (per-step skip), worker timeout with completed write evidence and independent file effects, ENOENT/BOOTSTRAP_UNKNOWN_SERVICE not counted as drift, sandbox_check.pid = worker PID, DAC EACCES not counted as drift, and the access_failed outcome. | Built app + XPC | — | |
| `runner_mach_service_liveness` | Baseline | The built `PWRunner` executable, launched directly with `--mach-service <name>` (the BYOXPC LaunchAgent launch shape), binds `NSXPCListener(machServiceName:)` and stays alive instead of aborting under `xpc_main`. Regression guard for the BYOXPC `xpc_timeout` crash: a host that calls `NSXPCListener.service()` for this launch aborts immediately (`"An XPC Service cannot be run directly."`), which is what made `runner verify` time out. Complements `runner_unit`'s `pwListenerConfig` table (which pins the argv→listener selection) by asserting the shipped binary itself does not abort. | Built app | — | Launches the host binary without launchd, so it never services a connection here — it only asserts the process does not abort. `tests/out/suites/runner_mach_service_liveness/.../artifacts/pwrunner.stderr.log` |
| `runner_byoxpc` | Opt-in | Smoke + blackbox coverage through a BYOXPC runner | Built app + launchd (GUI session) | Annotated mismatch condition in shared menagerie cases only | Uses an owned, uniquely named runner copy; signing preserves the selected app and cleanup verifies removal. Shared smoke/blackbox assertions include checker controls. BBX prediction disagreements fail and do not suppress attempt validation. |
| `smoke` | Baseline + opt-in caller-auth case | Quick end-to-end checks against a built app bundle | Built app + XPC; selecting the whole suite also requires a matching Developer ID | — | `--suite smoke` includes `runner_caller_auth`. For ordinary smoke without signing equipment, select `--case smoke/specimen_file_read_deny --case smoke/specimen_file_read_deny_standard`. Ordinary specimens also run under `runner_byoxpc`. Caller-auth checks use signed app copies, identical-client restricted/relaxed controls, independent file effects, and a missing-service control. |
| `blackbox_e2e` | Baseline | End-to-end black-box cases (BBX-*) validate the returned JSON envelope, attempts, and step identity/order. Prediction disagreements fail; independent checker controls ensure one failure cannot hide another. | Built app + XPC; checker controls need only Python 3 | — | Live cases also run under `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_e2e` |
| `blackbox_menagerie` | Baseline | Real SBPL fixtures exercising specimen ingestion and evidence correlation; controls drive both black-box checkers against independent envelopes and faults | Built app + XPC; validation controls need only Python 3 | Annotated mismatch is absent after all evidence checks pass | Live cases also run under `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_menagerie`. See `tests/suites/blackbox_menagerie/README.md` for invariants and fixtures. |
| `sbpl_allowdeny_consistency` | Baseline | Independently reads randomized file targets after writes, checks changed/nonempty bytes vs byte-for-byte preservation, restores seeds and reverses policy parameter bindings with the same probe plan, then cross-checks JSON verdicts. The fixture retains two Mach steps, checked for presence only. | Built app + XPC | — | Two specimens/envelopes plus external before/after byte snapshots; no log dependency or test overrides. |
| `runner_live_worker_identity` | Baseline | Test-owned observer obtains the exec helper PID from the kernel socket peer, follows OS ancestry to the worker and host, independently queries libsandbox while they live, and checks PW reports that worker and those verdicts. | Built app + XPC + macOS C toolchain | — | Bounded handshake; no PW source dependencies or test overrides. `observer.json` records independent PIDs, start times, and raw queries. |
| `runner_exec_dac` | Baseline | Direct execution and PW both reject a non-executable helper with EACCES and succeed after execute permission is restored; the failed attempt must retain its raw evidence and have `drift=null`. | Built app + XPC | — | Strict regression check against treating spawn EACCES as strong sandbox evidence. Both permission controls run before the drift assertion. |
| `exec_fixture` | Baseline | Independently verifies the shared helper's output/status, socket rendezvous, OS process identity/exit observation, environment/descriptor inspection, and state-preserving exec forwarding. A leader-only kill must be rejected while its child still answers; releasing one tree must leave another alive. | macOS C toolchain + Python 3 | — | Direct controls; no app dependency. Normal release and group kill must pass the same exit assertion. |
| `run_capture` | Baseline | Shared CLI capture preserves exact bytes, arguments and exit/signal status; distinguishes harness deadlines from PW results; keeps overlapping runs separate; and reaps the CLI after assertion failure | macOS + Python 3, Unix sockets and OS exit observation | — | No app or C compilation. Independent fixture, socket acknowledgements and exec fixture exit observer. Retains raw output and `capture.json`, including launch/JSON/cleanup errors. |
| `runner_specimen_isolation` | Baseline | Two bundled-runner specimens with identical step IDs overlap; B completes while A remains held. OS identities, independent file effects, and each run's output/attempt/prediction evidence stay separate. | Built app + XPC + macOS C toolchain + Python 3 | — | Shared envelope/step validation plus independent observations. Controls cover cross-run swaps, missing/invalid evidence, alias consistency, legitimate optional fields, and combined failures; direct release controls live in `exec_fixture`. |
| `runner_exec_lifecycle` | Baseline | A public CLI exec deadline stops both observed helper processes, preserves output, and permits a subsequent file write with independently checked effects. | Built app + XPC + macOS C toolchain + Python 3 | — | No test overrides or worker ABI dependency. Roughly 10 seconds; artifacts retain PID/group/exit observations and before/after bytes. |
| `runner_exec_inheritance` | Baseline | Exec children report empty environments, only standard descriptors, stdin EOF, and usable output. The CLI case uses ordinary specimens; a controlled worker launch proves random environment/descriptor resources existed to leak. | Built app + XPC + macOS C toolchain + Python 3 | — | Shared observer and assertions have direct contamination controls. The worker adapter owns the ABI dependency; opt-in mutation checks verify real leak detection. |
| `opt_in` | Opt-in | Select all non-default catalog cases | See registry | — | `tests/OPT_IN_TESTS.md` |
| `witness_contract` | Baseline | Pins verdicts, attempts, independent query/attempt routing, validator-failure attribution, completed observations after worker timeout, absence of policy claims before application, existing-file create semantics, rejected fields, test seams, and audit rules. | Built app + XPC | — | The routing case swaps real prediction targets while independently observed writes stay fixed; its intentional target mismatch tests drift reporting without claiming a compiler bug. The pre-apply case requires response 5, explicit signal null and no invented library/policy result, with a populated positive control. `worker_termination_and_log_correlation` combines denied writes with self-signal, capture disabled/enabled, successful-run capture, and ambiguous event references; Rust controls pin captured-event association independently of log availability. The steered-validator case separately tests classifier inputs end-to-end, and `runner_unit` pins the asymmetric truth table. `happy_path_baseline` is the regression sentinel. |

## Conventions

### Shell case setup and checking

Shared shell startup rejects Python with assertions disabled (for example,
`PYTHONOPTIMIZE=1`) with exit 2 before changing output or running cases. Unset
`PYTHONOPTIMIZE` to run tests. Direct Python helper invocations bypass shell
startup; invoke those with assertions enabled. Independent startup controls live
in `shell_helpers`.

`tests/lib/case.sh` provides baseline prerequisite checks, logged command
execution, fixture builds through their existing scripts, and Python checker
invocation. Cases retain their steps, argument lists, artifact paths, and final
pass statements. A failed stage writes a failed report and exits immediately;
it does not depend on the wrapper's `set -e`. Direct scripts retain the optional-app helpers in `testlib.sh`; the public
dispatcher enforces catalog prerequisites and rejects undeclared skips. Direct controls live
in `shell_helpers`; see `tests/suites/shell_helpers/README.md` for the API.

### CLI capture

`tests/lib/run_capture.py` prepares the supplied specimen and captures the public
CLI command, raw stdout/stderr, exit status, timing, and harness intervention.
Separate start/wait operations support overlapping runs. The caller supplies CLI
arguments and a test-side wait deadline, decides when to decode JSON, and owns
all outcome assertions and independent observations. Cleanup runs after those
observations. The initial users are `runner_validator_failure`,
`runner_exec_lifecycle`, and `runner_specimen_isolation`; independent controls
live in `run_capture`. See `tests/suites/run_capture/README.md` for the API and
artifact contract.

### Black-box validation

`blackbox_e2e`, `blackbox_menagerie`, `runner_specimen_isolation`, the
`witness_contract` prediction-target case, and the three `runner_filter_*` suites
share `tests/lib/blackbox.py` for envelope checks, step
identity/order, evidence fields and types, and explicit per-step expectations. Each suite owns its
policy, file-observation, denial, and skip rules. The helper only collects
errors; it neither runs PolicyWitness nor chooses expectations. Required attempt
aliases `rc`/`exit_code` and `errno`/`syscall_errno` agree in type and value;
nullable path fields remain present, while attempt `error` text is optional.
Black-box and filter controls exercise checker CLIs without importing the helper
or production code. Isolation controls call the suite adapter with separately
recorded witnesses. Both approaches require combined faults to remain visible.
Black-box and isolation controls also compare ordered/reordered response pairs:
only the order diagnostic may change, preserving actual step failures without
inventing others. Diagnostic order is unconstrained.
The filter suites use the `unavailable_prediction.py` CLI adapter, supplying
step identity, operation, filter value, and either a supported file-open or
denied-sysctl attempt contract. Their independent controls run through
`runner_filter_sysctl_name` before its optional app check; see its README.

The menagerie's end-to-end specimens come from local copies of PAWL evidence.
It covers SBPL ingestion, probe execution, and evidence correlation, including
negative controls and canonicalization-boundary cases where mismatches are
recorded as evidence. An absent annotated mismatch can skip only after all
evidence checks pass. See `tests/suites/blackbox_menagerie/README.md` for
suite invariants and fixtures.

### Harness note: sandboxed automation environments

Some automation harnesses run commands inside an OS sandbox. In that situation, specimen execution and unified-log based evidence capture can fail for reasons unrelated to PolicyWitness; re-run from a normal Terminal (or with escalation) before diagnosing PolicyWitness itself.

## Output contract (`tests/out/`)

An executing invocation of `tests/run.sh` replaces its output directory so tooling
can read stable paths. Help, `--list`, and rejected commands preserve it:

```text
tests/out/
  plan.json
  run.json
  dispatch.json
  events.jsonl
  artifact-integrity/  # when selected cases require app/worker
    inspection.json
    before.json
    after.json
    changes.json
  suites/<suite>/<test_id>/
    report.json
    events.jsonl
    artifacts/...
```

`plan.json` records the selection before execution. `dispatch.json` journals each
command invocation, expected cases, execution status, report snapshots, and
harness errors. Most cases execute in separate processes; BYOXPC leaves share
installation and cleanup. The installation case is also a selected dependency.

`run.json` retains reports/counts and includes the plan, effective configuration,
invocations, harness errors, and one `case_results` entry per selected case.
`artifact_integrity` records initial validity, final equality, evidence location,
and artifact errors, or is null for an entirely offline selection. Artifact errors
fail `ok` independently of case reports; incomplete inspections retain diagnostics
instead of claiming equality.
Distinct catalog cases must use distinct report paths; collisions are rejected
before output is replaced. The executor also refuses ambiguous report ownership
and checks complete, unique selection accounting before reporting success.
`completion` counts selected, completed (pass or fail reports), skipped, and
unrun cases. These are separate from readable-report counts: a missing report
cannot disappear merely because no report was available to count.

Started cases need one terminal event and a matching report. Unselected reports,
reused paths, malformed or contradictory evidence, silent commands, crashes,
unrun selections, and undeclared skips fail. A declared skip requires a matching
`skip_reason` in the report. Current live skips are limited to the menagerie's
absent annotated mismatch after evidence validation. There is no skip-policy flag.
`run.json.ok` and the shell exit agree: zero failed reports and zero harness
errors. Exit 2 means planning/configuration was rejected before execution.
See `tests/suites/dispatcher/README.md` for the independent controls.

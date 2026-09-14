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
./tests/run.sh --all
./tests/run.sh --suite preflight
./tests/run.sh --suite unit
./tests/run.sh --suite integration
./tests/run.sh --suite runner_byoxpc
./tests/run.sh --suite sbpl_allowdeny_consistency
./tests/run.sh --describe --all
```

Opt-in tests live under `tests/suites/runner_*/opt_in/` and are listed in `tests/OPT_IN_TESTS.md`.
Compatibility wrappers remain under `tests/suites/opt_in/`.
Runner suites that install launchd services (`runner_byoxpc`) require a logged-in GUI session.

## Tiers

- **Baseline**: expected on supported hosts; run by default in `tests/run.sh --all`.
- **Shared**: real suites with their own `run.sh`, but invoked transitively by the BYOXPC runner-mode wrapper rather than from `--all` defaults.
- **Contract**: pins load-bearing behaviors that the runner contracts to provide (includes regression guards for removed request fields and runner modes). Off the default battery because the suite is intentionally permissive about environment shape; promotable to Baseline if a case proves to be runnable everywhere.
- **Opt-in**: manual, resource-sensitive, or environment-specific tests. See `tests/OPT_IN_TESTS.md`.

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
| `preflight` | Baseline | Codesign + entitlements metadata matches the built app bundle | `dist/PolicyWitness.app` | — (missing app or codesign issues should fail) | `tests/out/suites/preflight/.../preflight.json` |
| `source_drift` | Baseline | The runner source manifest is consistent between the on-disk `runner/Sources/` tree and `build.sh`'s `XPC_RUNNER_*` set. (The SwiftPM package auto-discovers by convention, so its set equals disk; build.sh vs the tree is the comparison that can ship a broken `PWRunner.xpc`.) Catches a compiled file added to one but not the other before the drift ships. | Python 3 | — (manifest disagreement is always a fail) | `tests/out/suites/source_drift/.../check.log` |
| `shell_helpers` | Baseline | Case helpers retain arguments, logs and identity; failures stop case stages. Result helpers preserve matching terminal evidence and logging/exit behavior. Wrapper groups preserve child order, streams, and failure status while continuing later children | Bash + Python 3 | — | Independent receipts and subprocess observations; covers case/equipment failures, separate build logs, quiet output, result serialization, wrapper phase gates/cleanup, and explicit skips. No app or toolchain; BYOXPC and worker-setup controls use simulated children. |
| `dispatcher` | Baseline | Requested suite execution, case reports, and lifecycle events determine the same shell exit status and `run.json.ok` | Bash + Python 3 | — | Real dispatcher in fixture repositories; covers crashes, missing/invalid/contradictory evidence, explicit skips and wrapper aliases. No app or toolchain. |
| `unit` | Baseline | Controller logic is correct at the unit level | Cargo toolchain | — (missing toolchain should fail) | `tests/out/suites/unit/.../cargo-test-bins.log` |
| `runner_unit` | Baseline | Swift runner internals (`applySandboxPolicy`, the `CWorkerOrchestrator` envelope invariants, the `computeDrift` validator-vs-kernel truth table, the `classify` worker/validator→normalized-outcome table, the `buildAttemptResult` (kind, action, slot)→attempt-outcome table, prediction_unavailable host-mirror, CWorker + ValidatorClient drivers) are correct at the unit level. Covers paths that no real specimen can reach — including the `runner_failed`, `validator_no_reply`, and `runner_sandbox_denied` outcomes that have no e2e seam — and pins the attempt-outcome mapping as a table (so its two stacked layers can't silently disagree) rather than relying on the scattered per-outcome e2e suites. | `swift` on PATH | `swift` toolchain or `runner/Package.swift` missing | `tests/out/suites/runner_unit/.../pwrunner_core_tests.log`. Built via `runner/Package.swift`. |
| `integration` | Baseline | CLI contract + runner envelope are stable end-to-end | Built app + XPC | — (missing app should fail) | Uses fixtures under `tests/fixtures/pw_runner/` |
| `runner_apply_isolation_v2` | Baseline | v2 deny-default specimens complete cleanly: the unsandboxed XPC host posix_spawns the C worker, the worker applies the policy and writes its slot results to shared memory, and the host replies with a full envelope | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Asserts `runner_subprocess` and worker PID semantics |
| `runner_apply_isolation_v3` | Baseline | Same shape as `runner_apply_isolation_v2` but with SBPL v3 grammar, which has stricter validation | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Asserts `runner_subprocess` and worker PID semantics |
| `runner_outcome_libsandbox_unavailable` | Baseline | `_test_overrides.libsandbox_path=/nonexistent` causes `SandboxLib.load(path:)` to fail with a real `dlopen` error and the host returns `normalized_outcome="libsandbox_unavailable"` without spawning a worker | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Exercises the real loader; no stubbing. Asserts the failure message names the override path and that `test_overrides` is mirrored back |
| `runner_outcome_worker_spawn_failed` | Baseline | `_test_overrides.worker_executable_path=/nonexistent` makes `posix_spawn` return `ENOENT`; host returns `normalized_outcome="worker_spawn_failed"` | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Asserts `runner_subprocess` is null (no worker observed) and override is mirrored back |
| `runner_outcome_runner_timeout` | Baseline | `_test_overrides.worker_timeout_ms=2000` plus `_test_overrides.worker_post_apply_hang_ms=8000` makes the C worker hang past the host deadline; the host SIGKILLs it and reports `normalized_outcome="runner_timeout"` | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Runs ~2s wall-clock. Asserts `term_signal=9` (host-issued) and that wall-clock elapsed time matches the host deadline, not the worker's natural sleep |
| `runner_outcome_bad_request` | Baseline | Two e2e cases that drive `normalized_outcome="bad_request"` through both emit sites in `PWRunnerService.runSpecimen` — Swift decode failure and `validateSandboxChecks` rejection. No `_test_overrides` needed. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Asserts `runner_subprocess` is null and that the error message identifies the rejected field |
| `runner_ready_byte_resilience` | Baseline | `_test_overrides.worker_pre_ready_hang_ms=2000` makes the C worker write its pre-apply ready byte after the host's 1000ms `readyByteTimeout` has closed `--ready-fd`. The worker must survive that SIGPIPE-prone write (SIGPIPE is ignored), still `sandbox_apply`, and score the probe — `normalized_outcome="ok"`. Regression guard for the `com.apple.WebProcess` slow-compile SIGPIPE bug. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Runs ~2-3s. Asserts `term_signal=null`, `exit_code=0`, validator ran, and the override is mirrored back. Pre-fix worker fails here with `sandbox_apply_failed`/`term_signal=13` |
| `runner_filter_iokit_registry_entry_class` | Baseline | Pins the `(iokit-open-service, iokit_registry_entry_class)` pair: the runner accepts the filter, deliberately skips `sandbox_check` (empirically unreliable for this op+filter), and emits `step.sandbox_check.outcome="prediction_unavailable"` with `rc=-1` (sentinel). Attempt slot is a benign file `open_read` placeholder — the C worker doesn't implement iokit attempts. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Documents the "prediction-unavailable for known-drift op+filter pairs" contract |
| `runner_filter_sysctl_name` | Baseline | Same prediction-unavailable shape but for `(sysctl-read, sysctl_name)`, with real Channel A coverage via a `sysctl` / `read` attempt against `kern.osrelease`. Documents that the prediction-unavailable contract is not iokit-specific. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | |
| `runner_filter_iokit_user_client_class` | Baseline | `(iokit-open-user-client, iokit_user_client_class)` pair. Same `prediction_unavailable` contract; complements `runner_filter_iokit_registry_entry_class` to cover both registry-entry and user-client class matching modes. Same attempt placeholder caveat. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | |
| `validator_batch_mode` | Baseline | Pins the `sb_api_validator --batch <pid>` NDJSON-over-stdin/stdout contract: 10 mixed-filter probes against a `sandbox-exec` child cover all four verdict outcomes (3 allow + 1 deny + 1 error + 1 bad_filter + 4 parse_error including trailing-garbage + overlong-line regressions). Per-probe failures don't abort the run; step_id is preserved when known. The production runner uses this shape per run. Per-probe CLI mode preserved unchanged for diagnostic tooling. | Built app | `dist/PolicyWitness.app` missing or unbuilt | |
| `runner_validator_failure` | Baseline | Reversed partial validator replies survive clean shortfall or malformed JSON, attach to the correct step IDs, and preserve all completed attempts. The unanswered prediction has an explicit error and `drift:null`. | Built app + XPC + Python 3 | — | Checked-in validator transcripts have direct controls; CLI cases independently check file effects, degradation, honored overrides, and subprocess completion. Shared with the corresponding `witness_contract` entry points. |
| `runner_abi_layout` | Baseline | Layout-drift guard between the C ABI header and Swift `PWShmLayout`. Compiles a tiny `printer.c` against `pw_probe_runner_abi.h` at test time, harvests every `sizeof`/`offsetof`/macro value, parses the mirrored Swift enum, and asserts bidirectional agreement. Catches what parser-only `source_drift` can't model (compiler struct padding). | Toolchain only (no app) | `xcrun clang` or the macOS SDK unavailable. No app-bundle dependency. | Companion to `source_drift`'s enum-agreement check; both belong in the Baseline tier. |
| `runner_c_worker_harness` | Baseline | Proves `pw-probe-runner` (the C worker) in isolation across 15 hand-built-shm scenarios: `(allow default)` happy path, bare `(deny default)` isolation, clean exit-byte teardown, SIGKILL fallback, a 256-slot multi-page shared-memory run, an SBPL-params round-trip that proves `policy.params` reach the kernel (kernel-observed deny on `/etc/hosts` when `TARGET=/private/etc` is passed through `sandbox_create_params` + `sandbox_set_param`), the file unlink/create attempt kinds (allow + deny), and the worker's pre-apply self-defense exits (compile failure survives with `apply_rc=-1`; abi/prepared/step_count/param_count/policy-overflow refusals → exit 4/5/6/7/8). | Built app + harness | `dist/PolicyWitness.app` missing or unbuilt | Compiles `harness.c` once per suite run into `tests/out/.../harness.runner_c_worker` |
| `runner_use_c_worker` | Baseline | End-to-end coverage of the runner's C code path. Drives real specimens through `controller → XPC service → CWorkerOrchestrator → pw-probe-runner + sb_api_validator --batch` with NO `_test_overrides` (so each run also double-checks production-shape assembly). Covers: v4 envelope shape (validator_subprocess populated, drift computed, prediction_unavailable verdicts synthesized locally), bug-report `(deny default)` survival, and regression cases for duplicate step_ids (plan-killer), unsupported attempt combos (per-step skip), worker_timeout_ms wiring, ENOENT/BOOTSTRAP_UNKNOWN_SERVICE not counted as drift, sandbox_check.pid = worker PID, DAC EACCES not counted as drift, and the access_failed outcome. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | |
| `runner_mach_service_liveness` | Baseline | The built `PWRunner` executable, launched directly with `--mach-service <name>` (the BYOXPC LaunchAgent launch shape), binds `NSXPCListener(machServiceName:)` and stays alive instead of aborting under `xpc_main`. Regression guard for the BYOXPC `xpc_timeout` crash: a host that calls `NSXPCListener.service()` for this launch aborts immediately (`"An XPC Service cannot be run directly."`), which is what made `runner verify` time out. Complements `runner_unit`'s `pwListenerConfig` table (which pins the argv→listener selection) by asserting the shipped binary itself does not abort. | Built app | `dist/PolicyWitness.app` missing or unbuilt | Launches the host binary without launchd, so it never services a connection here — it only asserts the process does not abort. `tests/out/suites/runner_mach_service_liveness/.../artifacts/pwrunner.stderr.log` |
| `runner_byoxpc` | Opt-in | Smoke + blackbox coverage through a BYOXPC runner | Built app + launchd (GUI session) | launchd bootstrap unavailable or sandboxed | Uses the shared smoke and blackbox assertions, including checker controls. BBX prediction disagreements fail and do not suppress attempt validation. |
| `smoke` | Shared | Quick end-to-end checks against a built app bundle | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite smoke` |
| `blackbox_e2e` | Shared | End-to-end black-box cases (BBX-*) validate the returned JSON envelope, attempts, and step identity/order. Prediction disagreements fail; independent checker controls ensure one failure cannot hide another. | Built app + XPC; checker controls need only Python 3 | Live cases: `dist/PolicyWitness.app` missing or unbuilt; checker controls never skip | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_e2e` |
| `blackbox_menagerie` | Shared | Real SBPL fixtures exercising specimen ingestion and evidence correlation; controls drive both black-box checkers against independent envelopes and faults | Built app + XPC; validation controls need only Python 3 | Live cases: app missing, or an annotated mismatch is absent and all evidence checks pass; validation controls never skip | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_menagerie`. See `tests/suites/blackbox_menagerie/README.md` for invariants and fixtures. |
| `sbpl_allowdeny_consistency` | Baseline | Independently reads randomized file targets after writes, checks changed/nonempty bytes vs byte-for-byte preservation, restores seeds and reverses policy parameter bindings with the same probe plan, then cross-checks JSON verdicts. The fixture retains two Mach steps, checked for presence only. | Built app + XPC | — | Two specimens/envelopes plus external before/after byte snapshots; no log dependency or test overrides. |
| `runner_live_worker_identity` | Baseline | Test-owned observer obtains the exec helper PID from the kernel socket peer, follows OS ancestry to the worker and host, independently queries libsandbox while they live, and checks PW reports that worker and those verdicts. | Built app + XPC + macOS C toolchain | — | Bounded handshake; no PW source dependencies or test overrides. `observer.json` records independent PIDs, start times, and raw queries. |
| `runner_exec_dac` | Baseline | Direct execution and PW both reject a non-executable helper with EACCES and succeed after execute permission is restored; the failed attempt must retain its raw evidence and have `drift=null`. | Built app + XPC | — | Strict regression check against treating spawn EACCES as strong sandbox evidence. Both permission controls run before the drift assertion. |
| `exec_fixture` | Baseline | Independently verifies the shared helper's output/status, socket rendezvous, OS process identity/exit observation, environment/descriptor inspection, and state-preserving exec forwarding. A leader-only kill must be rejected while its child still answers; releasing one tree must leave another alive. | macOS C toolchain + Python 3 | — | Direct controls; no app dependency. Normal release and group kill must pass the same exit assertion. |
| `run_capture` | Baseline | Shared CLI capture preserves exact bytes, arguments and exit/signal status; distinguishes harness deadlines from PW results; keeps overlapping runs separate; and reaps the CLI after assertion failure | macOS + Python 3, Unix sockets and OS exit observation | — | No app or C compilation. Independent fixture, socket acknowledgements and exec fixture exit observer. Retains raw output and `capture.json`, including launch/JSON/cleanup errors. |
| `runner_specimen_isolation` | Baseline | Two bundled-runner specimens with identical step IDs overlap; B completes while A remains held. OS identities, independent file effects, and each run's output/attempt/prediction evidence stay separate. | Built app + XPC + macOS C toolchain + Python 3 | — | Socket barriers establish overlap. Twelve cross-run envelope/step/channel swaps must fail with attribution diagnostics; direct release controls live in `exec_fixture`. |
| `runner_exec_lifecycle` | Baseline | A public CLI exec deadline stops both observed helper processes, preserves output, and permits a subsequent file write with independently checked effects. | Built app + XPC + macOS C toolchain + Python 3 | — | No test overrides or worker ABI dependency. Roughly 10 seconds; artifacts retain PID/group/exit observations and before/after bytes. |
| `runner_exec_inheritance` | Baseline | Exec children report empty environments, only standard descriptors, stdin EOF, and usable output. The CLI case uses ordinary specimens; a controlled worker launch proves random environment/descriptor resources existed to leak. | Built app + XPC + macOS C toolchain + Python 3 | — | Shared observer and assertions have direct contamination controls. The worker adapter owns the ABI dependency; opt-in mutation checks verify real leak detection. |
| `opt_in` | Opt-in | Runner-mode opt-ins (logs, DYLD, launchd) | See registry | required resources unavailable (toolchain, GUI session for launchd bootstrap, sandboxed harness for XPC/log capture) | `tests/OPT_IN_TESTS.md` |
| `witness_contract` | Contract | Pins the load-bearing behaviors PolicyWitness contracts to provide: verdicts + attempts + validator failures attributed + removed fields rejected + test seam functioning + audit-rule enforcement. | Built app + XPC | off the default battery (suite is intentionally permissive about environment shape); run on demand | Most cases now pass post-reshape; `happy_path_baseline` is the regression sentinel and should always pass. End-to-end drift *surfacing* is still uncovered here — no current op+filter combination produces clean userland-vs-kernel disagreement through a real specimen (all known cases route to `prediction_unavailable`). The drift *classifier logic* itself (the asymmetric truth table) is unit-tested directly in `runner_unit`'s `computeDrift` table, which drives synthetic verdict/attempt pairs no specimen can currently produce. |

## Conventions

### Shell case setup and checking

`tests/lib/case.sh` provides baseline prerequisite checks, logged command
execution, fixture builds through their existing scripts, and Python checker
invocation. Cases retain their steps, argument lists, artifact paths, and final
pass statements. A failed stage writes a failed report and exits immediately;
it does not depend on the wrapper's `set -e`. Optional-app skips remain an
explicit choice through the existing `testlib.sh` helpers. Direct controls live
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

`blackbox_e2e` and `blackbox_menagerie` share `tests/lib/blackbox.py` for envelope
checks, step identity/order, evidence fields and types, and explicit per-step
expectations. Each suite owns its policy, file-observation, denial, and skip
rules. The helper only collects errors; it neither runs PolicyWitness nor
chooses expectations. Checker controls exercise the suite CLIs without importing
the helper or production code and require combined faults to remain visible.

The menagerie's end-to-end specimens come from local copies of PAWL evidence.
It covers SBPL ingestion, probe execution, and evidence correlation, including
negative controls and canonicalization-boundary cases where mismatches are
recorded as evidence. An absent annotated mismatch can skip only after all
evidence checks pass. See `tests/suites/blackbox_menagerie/README.md` for
suite invariants and fixtures.

### Harness note: sandboxed automation environments

Some automation harnesses run commands inside an OS sandbox. In that situation, specimen execution and unified-log based evidence capture can fail for reasons unrelated to PolicyWitness; re-run from a normal Terminal (or with escalation) before diagnosing PolicyWitness itself.

## Output contract (`tests/out/`)

Every invocation of `tests/run.sh` overwrites the prior run output so tooling can read stable paths:

```text
tests/out/
  run.json
  dispatch.json
  events.jsonl
  suites/<suite>/<test_id>/
    report.json
    events.jsonl
    artifacts/...
```

`dispatch.json` records each requested suite invocation and its execution status,
report snapshots, and harness errors. `run.json` retains case reports/counts and
adds `requested_suites`, `invocations`, and `harness_errors`. Its `ok` field and
the command's exit status use the same decision: no failed case reports and no
harness errors. A crash or absent report cannot disappear from the summary.
Case counts describe readable reports; harness failures are reported separately.

The dispatcher associates reports by invocation, including wrapper aliases.
Started cases must have one terminal event and a matching report. Reused case
paths, malformed or contradictory evidence, and silent suites fail. Explicit
reported skips remain valid. See `tests/suites/dispatcher/README.md` for the
contract and controls.

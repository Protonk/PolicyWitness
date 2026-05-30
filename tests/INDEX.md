# Test Coverage Index

This map summarizes what each suite covers and what you can claim when it
passes. For exact invariants and fixtures, see the per-suite README files under
`tests/suites/<suite>/`.

Tiers:
- **Baseline**: expected on supported hosts; run by default in `tests/run.sh --all`.
- **Diagnostic**: validates known OS anomalies; not a product guarantee.
- **Shared**: real suites with their own `run.sh`, but invoked transitively by the BYOXPC runner-mode wrapper rather than from `--all` defaults.
- **Contract**: pins load-bearing behaviors that the runner contracts to provide (includes regression guards for removed request fields and runner modes). Off the default battery because the suite is intentionally permissive about environment shape; promotable to Baseline if a case proves to be runnable everywhere.
- **Opt-in**: manual, resource-sensitive, or environment-specific tests.

| Suite | Tier | Primary claim | Requires | Notes / artifacts |
| --- | --- | --- | --- | --- |
| `preflight` | Baseline | Codesign + entitlements metadata matches the built app bundle | `dist/PolicyWitness.app` | `tests/out/suites/preflight/.../preflight.json` |
| `source_drift` | Baseline | The runner source manifest is consistent across all three sources of truth: `runner/*.swift` on disk, `build.sh`'s `XPC_RUNNER_*_FILE` set, and `runner/Package.swift`'s `sources:` array. Catches files added to one manifest but not the other before the drift ships. | Python 3 | `tests/out/suites/source_drift/.../check.log` |
| `unit` | Baseline | Controller logic is correct at the unit level | Cargo toolchain | `tests/out/suites/unit/.../cargo-test-bins.log` |
| `runner_unit` | Baseline | Swift runner internals (`applySandboxPolicy`, the `CWorkerOrchestrator` envelope invariants, prediction_unavailable host-mirror, CWorker + ValidatorClient drivers) are correct at the unit level. Covers paths that no real specimen can reach. | `swift` on PATH | `tests/out/suites/runner_unit/.../pwrunner_core_tests.log`. Built via `runner/Package.swift`. |
| `integration` | Baseline | CLI contract + runner envelope are stable end-to-end | Built app + XPC | Uses fixtures under `tests/fixtures/pw_runner/` |
| `runner_apply_isolation_v2` | Baseline | v2 deny-default specimens reply through the unsandboxed host/worker split (positive case: worker survives because the specimen pre-allows the syscalls its encode-and-write path needs) | Built app + XPC | Asserts `runner_subprocess` and worker PID semantics |
| `runner_apply_isolation_v3` | Baseline | v3 deny-default specimens reply through the unsandboxed host/worker split (positive case) | Built app + XPC | Asserts `runner_subprocess` and worker PID semantics |
| `runner_outcome_libsandbox_unavailable` | Baseline | `_test_overrides.libsandbox_path=/nonexistent` causes `SandboxLib.load(path:)` to fail with a real `dlopen` error and the host returns `normalized_outcome="libsandbox_unavailable"` without spawning a worker | Built app + XPC | Exercises the real loader; no stubbing. Asserts the failure message names the override path and that `test_overrides` is mirrored back |
| `runner_outcome_worker_spawn_failed` | Baseline | `_test_overrides.worker_executable_path=/nonexistent` makes `posix_spawn` return `ENOENT`; host returns `normalized_outcome="worker_spawn_failed"` | Built app + XPC | Asserts `runner_subprocess` is null (no worker observed) and override is mirrored back |
| `runner_outcome_runner_timeout` | Baseline | `_test_overrides.worker_timeout_ms=2000` plus `_test_overrides.worker_post_apply_hang_ms=8000` makes the C worker hang past the host deadline; the host SIGKILLs it and reports `normalized_outcome="runner_timeout"` | Built app + XPC | Asserts `term_signal=9` (host-issued) and that wall-clock elapsed time matches the host deadline, not the worker's natural sleep |
| `runner_outcome_bad_request` | Baseline | Two e2e cases that drive `normalized_outcome="bad_request"` through both emit sites in `PWRunnerService.runSpecimen` — Swift decode failure and `validateSandboxChecks` rejection. No `_test_overrides` needed. | Built app + XPC | Asserts `runner_subprocess` is null and that the error message identifies the rejected field |
| `runner_filter_iokit_registry_entry_class` | Baseline | Pins the `(iokit-open-service, iokit_registry_entry_class)` pair: the runner accepts the filter, deliberately skips `sandbox_check` (empirically unreliable for this op+filter), and emits `step.sandbox_check.outcome="prediction_unavailable"` with `rc=-1` (sentinel). The cross-check mirrors with `status="skipped"`. Attempt slot is a benign file `open_read` placeholder — no Channel A coverage of `iokit-open-service` yet (lands with the C probe-runner). | Built app + XPC | Documents the "prediction-unavailable for known-drift op+filter pairs" contract |
| `runner_filter_sysctl_name` | Baseline | Same shape but for `(sysctl-read, sysctl_name)`. Documents that the prediction-unavailable contract is not iokit-specific. Same attempt placeholder caveat. | Built app + XPC | |
| `runner_filter_iokit_user_client_class` | Baseline | `(iokit-open-user-client, iokit_user_client_class)` pair. Same `prediction_unavailable` contract; complements `runner_filter_iokit_registry_entry_class` to cover both registry-entry and user-client class matching modes. Same attempt placeholder caveat. | Built app + XPC | |
| `validator_batch_mode` | Baseline | Pins the `sb_api_validator --batch <pid>` NDJSON-over-stdin/stdout contract: 10 mixed-filter probes against a `sandbox-exec` child cover all four verdict outcomes (3 allow + 1 deny + 1 error + 1 bad_filter + 4 parse_error including trailing-garbage + overlong-line regressions). Per-probe failures don't abort the run; step_id is preserved when known. The production runner uses this shape per run. Per-probe CLI mode preserved unchanged for diagnostic tooling. | Built app | |
| `runner_c_worker_harness` | Baseline | Proves `pw-probe-runner` (the C worker) in isolation: a host-side C harness drives the worker through `(allow default)` happy path, bare `(deny default)` isolation, clean exit-byte teardown, SIGKILL fallback, a 256-slot multi-page shared-memory run, and an SBPL-params round-trip that proves `policy.params` reach the kernel (kernel-observed deny on `/etc/hosts` when `TARGET=/private/etc` is passed through `sandbox_create_params` + `sandbox_set_param`). | Built app + harness | Compiles `harness.c` once per suite run into `tests/out/.../harness.runner_c_worker` |
| `runner_use_c_worker` | Baseline | End-to-end coverage of the runner's C code path. Drives real specimens through `controller → XPC service → CWorkerOrchestrator → pw-probe-runner + sb_api_validator --batch` with NO `_test_overrides` (so each run also double-checks production-shape assembly). Covers: v4 envelope shape (validator_subprocess populated, drift computed, prediction_unavailable verdicts synthesized locally), bug-report `(deny default)` survival, and regression cases for duplicate step_ids, unsupported attempt combos, worker_timeout_ms wiring, ENOENT/BOOTSTRAP_UNKNOWN_SERVICE not counted as drift, sandbox_check.pid = worker PID, DAC EACCES not counted as drift, and the access_failed outcome. | Built app + XPC | |
| `runner_byoxpc` | Opt-in | Smoke + blackbox coverage through a BYOXPC runner | Built app + launchd (GUI session) | Skips when launchd bootstrap is unavailable |
| `smoke` | Shared | Quick end-to-end checks against a built app bundle | Built app + XPC | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite smoke` |
| `blackbox_e2e` | Shared | End-to-end black-box cases (BBX-*) that treat the runner as a sealed unit and validate the returned JSON envelope | Built app + XPC | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_e2e` |
| `blackbox_menagerie` | Shared | Real SBPL fixtures exercising specimen ingestion and evidence correlation | Built app + XPC | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_menagerie` |
| `anomalies` | Diagnostic | Known OS anomalies (SBPL `(allow ...) (deny ...)` ordering) | Host-dependent | |
| `opt_in` | Opt-in | Runner-mode opt-ins (logs, DYLD, launchd) | See registry | `tests/OPT_IN_TESTS.md` |
| `witness_contract` | Contract | Pins the load-bearing behaviors PolicyWitness contracts to provide: verdicts + attempts + validator failures attributed + removed fields rejected + test seam functioning + audit-rule enforcement. | Built app + XPC | Most cases now pass post-reshape; `happy_path_baseline` is the regression sentinel. Drift surfacing is currently uncovered — no current op+filter combination produces clean userland-vs-kernel disagreement (all known cases route to `prediction_unavailable`). |

## Expected skips by suite

- `preflight`: no expected skips; missing app or codesign issues should fail.
- `source_drift`: no expected skips; manifest disagreement is always a fail.
- `unit`: no expected skips; missing toolchain should fail.
- `runner_unit`: skip when the `swift` toolchain or `runner/Package.swift` is missing.
- `integration`: no expected skips; missing app should fail.
- `runner_apply_isolation_v2`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_apply_isolation_v3`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_outcome_libsandbox_unavailable`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_outcome_worker_spawn_failed`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_outcome_runner_timeout`: skip when `dist/PolicyWitness.app` is missing or unbuilt. Runs ~2s wall-clock time.
- `runner_outcome_bad_request`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_filter_iokit_registry_entry_class`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_filter_sysctl_name`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_filter_iokit_user_client_class`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_byoxpc`: skip when launchd bootstrap is unavailable or sandboxed. Blackbox cases historically reported a skip for a `mach-lookup global-name` sandbox_check anomaly (BBX-001); root-caused as a wrong filter type ID in the runner (corrected from 16 → 2 after empirical verification). Other `sandbox_check` divergences (especially for filter kinds whose IDs we have not yet re-verified) may still surface.
- `anomalies`: skip when `dist/PolicyWitness.app` is missing.
- `opt_in`: skip when required resources are unavailable (toolchain, GUI session for launchd bootstrap, sandboxed harness for XPC/log capture).
- `witness_contract`: tests are *expected to fail* during the reshape; see the suite README. The suite is not in `tests/run.sh --all` defaults until fully green. `happy_path_baseline` should always pass.

## Normalized outcome coverage matrix

Every value in `runner/PWRunnerAPI.swift::NormalizedOutcome` must appear
exactly once in this matrix. New outcomes are added here in the same
change that introduces the constant; `source_drift` enforces the rule
mechanically. "Untestable" rows are not unmaintained — the rationale
column says why, and the closest unit or harness coverage is named.

| outcome | emitted by | primary suite/case | notes |
| --- | --- | --- | --- |
| `ok` | C worker (pw-probe-runner) + validator (sb_api_validator) joined by `CWorkerOrchestrator` | `runner_apply_isolation_v2`, `runner_apply_isolation_v3`, `integration`, `runner_use_c_worker`, others | The happy path; covered everywhere. |
| `bad_policy` | host (PWRunnerService) pre-spawn hash failure | none (e2e unreachable) | The Rust controller's preflight short-circuits malformed SBPL as `bad_policy` before invoking the runner. `runner_unit` covers `computePolicyHash` failure indirectly through `applySandboxPolicy` shape tests. |
| `sandbox_apply_failed` | C worker apply path (surfaced via `CWorkerOrchestrator` when `apply_rc != 0`) | `runner_unit` / `SandboxApplyTests` | E2e unreachable because preflight catches the same input upstream as `bad_policy`. Unit tests stub `SandboxLib` to force compile/apply failure. |
| `libsandbox_unavailable` | host (PWRunnerService) pre-spawn check | `runner_outcome_libsandbox_unavailable` | Driven via `_test_overrides.libsandbox_path`. |
| `bad_request` | host (PWRunnerService) — Swift decode + `validateSandboxChecks` + `CWorkerOrchestrator.validateProbePlanForCWorker` | `runner_outcome_bad_request`, `runner_use_c_worker` (dup step_id, bogus attempt) | Multiple cases cover the emit sites. |
| `already_ran` | host (PWRunnerService) | none (out of scope) | The XPC service exits ~50ms after the first reply, so a second request from the same connection is racy. |
| `worker_spawn_failed` | host (PWRunnerService) | `runner_outcome_worker_spawn_failed` | Driven via `_test_overrides.worker_executable_path`. |
| `runner_sandbox_denied` | host classifier (CWorkerOrchestrator) when the C worker exits from a signal before flipping `done` | `runner_unit` / `EnvelopeInvariantTests` (wire-shape pin) | E2e unreachable from any deterministic specimen now that the C worker has a minimal post-apply syscall surface that the bug-report `(deny default)` policy can no longer kill (covered as a survival positive by `runner_use_c_worker.bare_deny_default`). |
| `runner_timeout` | host classifier | `runner_outcome_runner_timeout`, `witness_contract/worker_post_apply_hang_seam` | Driven via `_test_overrides.worker_timeout_ms` plus `_test_overrides.worker_post_apply_hang_ms`. |
| `runner_failed` | host classifier | none (e2e unreachable) | Reached when the C worker exits cleanly without flipping `done` or with a non-fatal failure mode. No deterministic specimen produces this. |
| `validator_spawn_failed` | host classifier (CWorkerOrchestrator) | `witness_contract/validator_spawn_failed_reports_degraded` | Driven via `_test_overrides.validator_executable_path`. `result.ok=false`, `rc=1`; attempts still surfaced as degraded evidence. |
| `validator_no_reply` | host classifier | none yet | Validator child started but exited without emitting the expected verdict count. `ValidatorClientResult.failure` carries the partial verdicts as degraded evidence. |
| `validator_decode_failure` | host classifier | none yet | Validator emitted bytes the host couldn't parse as NDJSON verdicts. Same partial-evidence treatment as `validator_no_reply`. |
| `validator_unavailable` | host classifier | none yet | Synthesized when the envelope has attempts but no verdicts. Distinct from the failure-mode-specific outcomes above so a consumer can recognize "PW ran in attempts-only degradation mode" as a known state. |
| `xpc_error` | client (`pw-runner-client`) synthetic reply | none (e2e requires renaming the `.xpc` bundle out from under launchd) | Reachable in practice when the bundle is missing or launchd refuses to spawn the host. Documented in `PolicyWitness.md` troubleshooting. |
| `xpc_timeout` | client synthetic reply | none (e2e requires a slow specimen plus tight `--timeout-ms`) | Trigger is real (`--timeout-ms 50` plus a long `_test_overrides.worker_post_apply_hang_ms`) but not currently scripted. |
| `xpc_proxy_type_mismatch` | client synthetic reply | none (no realistic trigger) | Fires only if the remote XPC proxy doesn't conform to `PWRunnerProtocol`. Defense-in-depth for a code path that should never run with our matched client/host. |
| `xpc_no_reply` | client synthetic reply | none (no realistic trigger) | Fires only if the XPC reply never arrives but no error fires either. Defense-in-depth. |

## Attempt outcome coverage matrix

Every value in `runner/PWRunnerAPI.swift::AttemptOutcome` must appear
exactly once in this matrix; `source_drift` enforces the rule
mechanically alongside the NormalizedOutcome matrix above.

| outcome | emitted by | primary coverage | notes |
| --- | --- | --- | --- |
| `ok` | C worker (pw-probe-runner) | every smoke / happy-path suite | The attempt ran and the kernel allowed the operation. |
| `open_failed` | C worker (file open_read / open_write / create) | `runner_use_c_worker.bare_deny_default`, blackbox file-deny cases | Covers both kernel deny (EPERM / EACCES) and ENOENT-class failures; the kernel verdict is in `attempt.errno`. |
| `unlink_failed` | C worker (file unlink) | `runner_unit` / unit coverage | E2e coverage requires a specimen that exercises unlink; the unit-level Codable shape is covered. |
| `access_failed` | C worker (file `access(R_OK)`) | `runner_use_c_worker.access_failure_classified` | Errno preserved in `attempt.errno` (typically EPERM/EACCES on a denied path). |
| `lookup_failed` | C worker (mach_lookup bootstrap_look_up) | `blackbox_e2e` / `core_mach_simple` | The kernel return code is preserved in the error message (e.g. `kr=1102` BOOTSTRAP_UNKNOWN_SERVICE). |
| `bootstrap_port_failed` | C worker (mach_lookup) | none (no realistic trigger) | Fires only if `task_get_special_port(TASK_BOOTSTRAP_PORT)` itself fails — defense-in-depth for an OS-level failure that shouldn't happen on a healthy macOS host. |
| `unsupported` | C worker (unknown attempt.kind or unknown action) | `runner_outcome_bad_request` (close) | The runner validates attempt shape before the worker runs; this branch fires only if a future caller adds a new attempt.kind to the schema before the worker learns to handle it. |
| `not_run_worker_died` | host classifier (CWorkerOrchestrator) | `witness_contract/shm_sentinel_under_deny_default` | Synthesized when a slot's `completed=0` after the worker exited — distinguishes "the attempt itself failed" from "the worker never reached this slot." Distinct from `unsupported`, which means the worker reached the slot but didn't know what to do. |

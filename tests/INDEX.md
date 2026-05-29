# Test Coverage Index

This map summarizes what each suite covers and what you can claim when it
passes. For exact invariants and fixtures, see the per-suite README files under
`tests/suites/<suite>/`.

Tiers:
- **Baseline**: expected on supported hosts; run by default in `tests/run.sh --all`.
- **Diagnostic**: validates known OS anomalies; not a product guarantee.
- **Shared**: real suites with their own `run.sh`, but invoked transitively by the runner-mode wrappers (debuggable / BYOXPC) rather than from `--all` defaults.
- **Contract**: pins target behaviors of an in-progress refactor. Off the default battery until fully green; once green, the suite is promoted to Baseline. Failures during the transition print a precise "PASSES WHEN: …" line naming the gating row in the relevant plan document.
- **Opt-in**: manual, resource-sensitive, or environment-specific tests.

| Suite | Tier | Primary claim | Requires | Notes / artifacts |
| --- | --- | --- | --- | --- |
| `preflight` | Baseline | Codesign + entitlements metadata matches the built app bundle | `dist/PolicyWitness.app` | `tests/out/suites/preflight/.../preflight.json` |
| `source_drift` | Baseline | The runner source manifest is consistent across all three sources of truth: `runner/*.swift` on disk, `build.sh`'s `XPC_RUNNER_*_FILE` set, and `runner/Package.swift`'s `sources:` array. Catches files added to one manifest but not the other before the drift ships. | Python 3 | `tests/out/suites/source_drift/.../check.log` |
| `unit` | Baseline | Controller logic is correct at the unit level | Cargo toolchain | `tests/out/suites/unit/.../cargo-test-bins.log` |
| `runner_unit` | Baseline | Swift runner internals (`applySandboxPolicy`, `classifyWorkerResult`, `effectiveWorkerTimeoutSeconds`, `partialStepOutput`, wait-status decoders, `PWRunnerWorkerWire` framing) are correct at the unit level. Covers paths that no real specimen can reach. | `swift` on PATH | `tests/out/suites/runner_unit/.../pwrunner_core_tests.log`. Built via `runner/Package.swift`. |
| `integration` | Baseline | CLI contract + runner envelope are stable end-to-end | Built app + XPC | Uses fixtures under `tests/fixtures/pw_runner/` |
| `runner_apply_isolation_v2` | Baseline | v2 deny-default specimens reply through the unsandboxed host/worker split (positive case: worker survives because the specimen pre-allows the syscalls its encode-and-write path needs) | Built app + XPC | Asserts `runner_subprocess` and worker PID semantics |
| `runner_apply_isolation_v3` | Baseline | v3 deny-default specimens reply through the unsandboxed host/worker split (positive case) | Built app + XPC | Asserts `runner_subprocess` and worker PID semantics |
| `runner_sandbox_denied` | Baseline | Bare `(deny default)` worker is sandbox-killed but the unsandboxed host still reports `normalized_outcome="runner_sandbox_denied"` with `runner_subprocess.term_signal` populated | Built app + XPC | Uses the bug-report specimen verbatim; covers both SIGKILL and SIGTRAP termination paths |
| `runner_outcome_libsandbox_unavailable` | Baseline | `_test_overrides.libsandbox_path=/nonexistent` causes `SandboxLib.load(path:)` to fail with a real `dlopen` error and the host returns `normalized_outcome="libsandbox_unavailable"` without spawning a worker | Built app + XPC | Exercises the real loader; no stubbing. Asserts the failure message names the override path and that `test_overrides` is mirrored back |
| `runner_outcome_worker_spawn_failed` | Baseline | `_test_overrides.worker_executable_path=/nonexistent` makes `posix_spawn` return `ENOENT`; host returns `normalized_outcome="worker_spawn_failed"` | Built app + XPC | Asserts `runner_subprocess` is null (no worker observed) and override is mirrored back |
| `runner_outcome_runner_timeout` | Baseline | `_test_overrides.worker_timeout_ms=2000` plus an 8s `debug_wait` instrumentation port makes the host SIGKILL the worker at its deadline; `normalized_outcome="runner_timeout"` | Built app + XPC | Asserts `term_signal=9` (host-issued) and that wall-clock elapsed time matches the host deadline, not the worker's natural sleep |
| `runner_outcome_bad_request` | Baseline | Two e2e cases that drive `normalized_outcome="bad_request"` through both emit sites in `PWRunnerService.runSpecimen` — Swift decode failure and `validateSandboxChecks` rejection. No `_test_overrides` needed. | Built app + XPC | Asserts `runner_subprocess` is null and that the error message identifies the rejected field |
| `runner_filter_iokit_registry_entry_class` | Baseline | The runner accepts `iokit_registry_entry_class` filter kind on `iokit-open-service`, deliberately skips `sandbox_check` (empirically unreliable for this op+filter), and emits `step.sandbox_check.outcome="prediction_unavailable"`. The cross-check mirrors with `status="skipped"`. The attempt (channel A) still runs as the reliable evidence. | Built app + XPC | Documents the "prediction-unavailable for known-drift op+filter pairs" contract |
| `runner_filter_sysctl_name` | Baseline | Same shape as `runner_filter_iokit_registry_entry_class` but for `sysctl_name` on `sysctl-read`. Documents that the prediction-unavailable contract is not iokit-specific — sandbox_check drift surfaces on syscall-level operations too. | Built app + XPC | |
| `runner_debuggable` | Baseline | Smoke + blackbox coverage through the built-in debuggable runner | Built app + XPC | Uses shared smoke/blackbox scripts |
| `runner_byoxpc` | Opt-in | Smoke + blackbox coverage through a BYOXPC runner | Built app + launchd (GUI session) | Skips when launchd bootstrap is unavailable |
| `smoke` | Shared | Quick end-to-end checks (specimen smoke + instrumentation paths) against a built app bundle | Built app + XPC | Invoked by `runner_debuggable` / `runner_byoxpc`; runs standalone via `tests/run.sh --suite smoke` |
| `blackbox_e2e` | Shared | End-to-end black-box cases (BBX-*) that treat the runner as a sealed unit and validate the returned JSON envelope | Built app + XPC | Invoked by `runner_debuggable` / `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_e2e` |
| `blackbox_menagerie` | Shared | Real SBPL fixtures exercising specimen ingestion and evidence correlation | Built app + XPC | Invoked by `runner_debuggable` / `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_menagerie` |
| `anomalies` | Diagnostic | Known OS anomalies + sandbox_check cross-check consistency | Host-dependent | Cross-check may skip if tooling is unavailable |
| `opt_in` | Opt-in | Runner-mode opt-ins (logs, DYLD, launchd) | See registry | `tests/OPT_IN_TESTS.md` |
| `witness_contract` | Contract | Pins the load-bearing behaviors PolicyWitness contracts to provide: verdicts + attempts + drift surfaced + validator failures attributed + removed fields rejected + test seam functioning + audit-rule enforcement. | Built app + XPC | Off the default battery during the runner reshape (`RUNNER-RESHAPE-PLAN.md`). Most tests fail today with PHASE 0 markers naming the gating plan row; `happy_path_baseline` passes today as a regression sentinel. |

## Expected skips by suite

- `preflight`: no expected skips; missing app or codesign issues should fail.
- `source_drift`: no expected skips; manifest disagreement is always a fail.
- `unit`: no expected skips; missing toolchain should fail.
- `runner_unit`: skip when the `swift` toolchain or `runner/Package.swift` is missing.
- `integration`: no expected skips; missing app should fail.
- `runner_apply_isolation_v2`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_apply_isolation_v3`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_sandbox_denied`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_outcome_libsandbox_unavailable`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_outcome_worker_spawn_failed`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_outcome_runner_timeout`: skip when `dist/PolicyWitness.app` is missing or unbuilt. Runs ~2s wall-clock time.
- `runner_outcome_bad_request`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_filter_iokit_registry_entry_class`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_filter_sysctl_name`: skip when `dist/PolicyWitness.app` is missing or unbuilt.
- `runner_debuggable`: skip when `dist/PolicyWitness.app` is missing or unbuilt. Blackbox cases historically reported a skip for a `mach-lookup global-name` sandbox_check anomaly (BBX-001); root-caused as a wrong filter type ID in the runner (corrected from 16 → 2 after empirical verification). Skips of that specific form should no longer fire. Other `sandbox_check` divergences (especially for filter kinds whose IDs we have not yet re-verified) may still surface.
- `runner_byoxpc`: skip when launchd bootstrap is unavailable or sandboxed. Same `sandbox_check`-divergence caveat as `runner_debuggable`.
- `anomalies`: skip when `dist/PolicyWitness.app` is missing; cross-check tooling unavailable.
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
| `ok` | worker (WorkerEntry) | `runner_apply_isolation_v2`, `runner_apply_isolation_v3`, `integration`, `runner_debuggable`, others | The happy path; covered everywhere. |
| `bad_policy` | worker (WorkerEntry); host (PWRunnerService) for pre-spawn hash failure | none (e2e unreachable) | The Rust controller's preflight short-circuits malformed SBPL as `bad_policy` before invoking the runner, so the runner-side branches are defense-in-depth. `runner_unit` covers `computePolicyHash` failure indirectly through `applySandboxPolicy` shape tests. |
| `sandbox_apply_failed` | worker (WorkerEntry) | `runner_unit` / `SandboxApplyTests` | E2e unreachable because preflight catches the same input upstream as `bad_policy`. Unit tests stub `SandboxLib` to force compile/apply failure. |
| `libsandbox_unavailable` | host (PWRunnerService) short-circuit; worker (WorkerEntry) defense-in-depth | `runner_outcome_libsandbox_unavailable` | Driven via `_test_overrides.libsandbox_path`. The worker-side path is unreachable today because the host short-circuits first; that's documented in `WorkerEntry.swift`. |
| `bad_request` | host (PWRunnerService) — Swift decode + `validateSandboxChecks` | `runner_outcome_bad_request` | Two cases cover both emit sites. No override needed. |
| `already_ran` | host (PWRunnerService) | none (out of scope) | The XPC service exits ~50ms after the first reply, so a second request from the same connection is racy. Unit-testing it would require refactoring `replyAndExit`'s `exit(0)` out, which `COMMITMENTS-PLAN.md` lists as out of scope. |
| `worker_spawn_failed` | host (PWRunnerService) | `runner_outcome_worker_spawn_failed` | Driven via `_test_overrides.worker_executable_path`. |
| `runner_sandbox_denied` | host classifier (WorkerProcess.classifyWorkerResult) | `runner_sandbox_denied`; unit-pinned by `runner_unit` / `WorkerProcessClassifyTests` | The bug-report specimen, verbatim. |
| `runner_timeout` | host classifier | `runner_outcome_runner_timeout`; unit-pinned by `runner_unit` | Driven via `_test_overrides.worker_timeout_ms` plus a long `debug_wait`. |
| `runner_failed` | host classifier; worker self-report on encode failure | `runner_unit` / `WorkerProcessClassifyTests` | E2e unreachable today because the failure modes that produce it (worker exits non-zero with no report; worker self-reports during a teardown error) don't surface from any deterministic specimen. Unit tests cover the classifier branch. |
| `xpc_error` | client (`pw-runner-client`) synthetic reply | none (e2e requires renaming the `.xpc` bundle out from under launchd) | Reachable in practice when the bundle is missing or launchd refuses to spawn the host. Documented in `PolicyWitness.md` troubleshooting. |
| `xpc_timeout` | client synthetic reply | none (e2e requires a slow specimen plus tight `--timeout-ms`) | Trigger is real (`--timeout-ms 50` plus a long `debug_wait`) but not currently scripted. |
| `xpc_proxy_type_mismatch` | client synthetic reply | none (no realistic trigger) | Fires only if the remote XPC proxy doesn't conform to `PWRunnerProtocol`. Defense-in-depth for a code path that should never run with our matched client/host. |
| `xpc_no_reply` | client synthetic reply | none (no realistic trigger) | Fires only if the XPC reply never arrives but no error fires either. Defense-in-depth. |

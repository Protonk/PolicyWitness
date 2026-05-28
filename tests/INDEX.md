# Test Coverage Index

This map summarizes what each suite covers and what you can claim when it
passes. For exact invariants and fixtures, see the per-suite README files under
`tests/suites/<suite>/`.

Tiers:
- **Baseline**: expected on supported hosts; run by default in `tests/run.sh --all`.
- **Extended**: broader coverage but host-dependent skips are normal.
- **Diagnostic**: validates known OS anomalies; not a product guarantee.
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
| `runner_debuggable` | Baseline | Smoke + blackbox coverage through the built-in debuggable runner | Built app + XPC | Uses shared smoke/blackbox scripts |
| `runner_byoxpc` | Opt-in | Smoke + blackbox coverage through a BYOXPC runner | Built app + launchd (GUI session) | Skips when launchd bootstrap is unavailable |
| `anomalies` | Diagnostic | Known OS anomalies + sandbox_check cross-check consistency | Host-dependent | Cross-check may skip if tooling is unavailable |
| `opt_in` | Opt-in | Runner-mode opt-ins (logs, DYLD, launchd) | See registry | `tests/OPT_IN_TESTS.md` |

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
- `runner_debuggable`: skip when `dist/PolicyWitness.app` is missing or unbuilt; blackbox cases may skip for host `sandbox_check` anomalies.
- `runner_byoxpc`: skip when launchd bootstrap is unavailable or sandboxed; blackbox cases may skip for host `sandbox_check` anomalies.
- `anomalies`: skip when `dist/PolicyWitness.app` is missing; cross-check tooling unavailable.
- `opt_in`: skip when required resources are unavailable (toolchain, GUI session for launchd bootstrap, sandboxed harness for XPC/log capture).

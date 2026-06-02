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
| `source_drift` | Baseline | The runner source manifest is consistent across all three sources of truth: `runner/*.swift` on disk, `build.sh`'s `XPC_RUNNER_*_FILE` set, and `runner/Package.swift`'s `sources:` array. Catches files added to one manifest but not the other before the drift ships. | Python 3 | — (manifest disagreement is always a fail) | `tests/out/suites/source_drift/.../check.log` |
| `unit` | Baseline | Controller logic is correct at the unit level | Cargo toolchain | — (missing toolchain should fail) | `tests/out/suites/unit/.../cargo-test-bins.log` |
| `runner_unit` | Baseline | Swift runner internals (`applySandboxPolicy`, the `CWorkerOrchestrator` envelope invariants, the `computeDrift` validator-vs-kernel truth table, prediction_unavailable host-mirror, CWorker + ValidatorClient drivers) are correct at the unit level. Covers paths that no real specimen can reach. | `swift` on PATH | `swift` toolchain or `runner/Package.swift` missing | `tests/out/suites/runner_unit/.../pwrunner_core_tests.log`. Built via `runner/Package.swift`. |
| `integration` | Baseline | CLI contract + runner envelope are stable end-to-end | Built app + XPC | — (missing app should fail) | Uses fixtures under `tests/fixtures/pw_runner/` |
| `runner_apply_isolation_v2` | Baseline | v2 deny-default specimens complete cleanly: the unsandboxed XPC host posix_spawns the C worker, the worker applies the policy and writes its slot results to shared memory, and the host replies with a full envelope | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Asserts `runner_subprocess` and worker PID semantics |
| `runner_apply_isolation_v3` | Baseline | Same shape as `runner_apply_isolation_v2` but with SBPL v3 grammar, which has stricter validation | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Asserts `runner_subprocess` and worker PID semantics |
| `runner_outcome_libsandbox_unavailable` | Baseline | `_test_overrides.libsandbox_path=/nonexistent` causes `SandboxLib.load(path:)` to fail with a real `dlopen` error and the host returns `normalized_outcome="libsandbox_unavailable"` without spawning a worker | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Exercises the real loader; no stubbing. Asserts the failure message names the override path and that `test_overrides` is mirrored back |
| `runner_outcome_worker_spawn_failed` | Baseline | `_test_overrides.worker_executable_path=/nonexistent` makes `posix_spawn` return `ENOENT`; host returns `normalized_outcome="worker_spawn_failed"` | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Asserts `runner_subprocess` is null (no worker observed) and override is mirrored back |
| `runner_outcome_runner_timeout` | Baseline | `_test_overrides.worker_timeout_ms=2000` plus `_test_overrides.worker_post_apply_hang_ms=8000` makes the C worker hang past the host deadline; the host SIGKILLs it and reports `normalized_outcome="runner_timeout"` | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Runs ~2s wall-clock. Asserts `term_signal=9` (host-issued) and that wall-clock elapsed time matches the host deadline, not the worker's natural sleep |
| `runner_outcome_bad_request` | Baseline | Two e2e cases that drive `normalized_outcome="bad_request"` through both emit sites in `PWRunnerService.runSpecimen` — Swift decode failure and `validateSandboxChecks` rejection. No `_test_overrides` needed. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Asserts `runner_subprocess` is null and that the error message identifies the rejected field |
| `runner_filter_iokit_registry_entry_class` | Baseline | Pins the `(iokit-open-service, iokit_registry_entry_class)` pair: the runner accepts the filter, deliberately skips `sandbox_check` (empirically unreliable for this op+filter), and emits `step.sandbox_check.outcome="prediction_unavailable"` with `rc=-1` (sentinel). Attempt slot is a benign file `open_read` placeholder — the C worker doesn't implement iokit attempts. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Documents the "prediction-unavailable for known-drift op+filter pairs" contract |
| `runner_filter_sysctl_name` | Baseline | Same prediction-unavailable shape but for `(sysctl-read, sysctl_name)`, with real Channel A coverage via a `sysctl` / `read` attempt against `kern.osrelease`. Documents that the prediction-unavailable contract is not iokit-specific. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | |
| `runner_filter_iokit_user_client_class` | Baseline | `(iokit-open-user-client, iokit_user_client_class)` pair. Same `prediction_unavailable` contract; complements `runner_filter_iokit_registry_entry_class` to cover both registry-entry and user-client class matching modes. Same attempt placeholder caveat. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | |
| `validator_batch_mode` | Baseline | Pins the `sb_api_validator --batch <pid>` NDJSON-over-stdin/stdout contract: 10 mixed-filter probes against a `sandbox-exec` child cover all four verdict outcomes (3 allow + 1 deny + 1 error + 1 bad_filter + 4 parse_error including trailing-garbage + overlong-line regressions). Per-probe failures don't abort the run; step_id is preserved when known. The production runner uses this shape per run. Per-probe CLI mode preserved unchanged for diagnostic tooling. | Built app | `dist/PolicyWitness.app` missing or unbuilt | |
| `runner_abi_layout` | Baseline | Layout-drift guard between the C ABI header and Swift `PWShmLayout`. Compiles a tiny `printer.c` against `pw_probe_runner_abi.h` at test time, harvests every `sizeof`/`offsetof`/macro value, parses the mirrored Swift enum, and asserts bidirectional agreement. Catches what parser-only `source_drift` can't model (compiler struct padding). | Toolchain only (no app) | `xcrun clang` or the macOS SDK unavailable. No app-bundle dependency. | Companion to `source_drift`'s enum-agreement check; both belong in the Baseline tier. |
| `runner_c_worker_harness` | Baseline | Proves `pw-probe-runner` (the C worker) in isolation across 15 hand-built-shm scenarios: `(allow default)` happy path, bare `(deny default)` isolation, clean exit-byte teardown, SIGKILL fallback, a 256-slot multi-page shared-memory run, an SBPL-params round-trip that proves `policy.params` reach the kernel (kernel-observed deny on `/etc/hosts` when `TARGET=/private/etc` is passed through `sandbox_create_params` + `sandbox_set_param`), the file unlink/create attempt kinds (allow + deny), and the worker's pre-apply self-defense exits (compile failure survives with `apply_rc=-1`; abi/prepared/step_count/param_count/policy-overflow refusals → exit 4/5/6/7/8). | Built app + harness | `dist/PolicyWitness.app` missing or unbuilt | Compiles `harness.c` once per suite run into `tests/out/.../harness.runner_c_worker` |
| `runner_use_c_worker` | Baseline | End-to-end coverage of the runner's C code path. Drives real specimens through `controller → XPC service → CWorkerOrchestrator → pw-probe-runner + sb_api_validator --batch` with NO `_test_overrides` (so each run also double-checks production-shape assembly). Covers: v4 envelope shape (validator_subprocess populated, drift computed, prediction_unavailable verdicts synthesized locally), bug-report `(deny default)` survival, and regression cases for duplicate step_ids (plan-killer), unsupported attempt combos (per-step skip), worker_timeout_ms wiring, ENOENT/BOOTSTRAP_UNKNOWN_SERVICE not counted as drift, sandbox_check.pid = worker PID, DAC EACCES not counted as drift, and the access_failed outcome. | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | |
| `runner_byoxpc` | Opt-in | Smoke + blackbox coverage through a BYOXPC runner | Built app + launchd (GUI session) | launchd bootstrap unavailable or sandboxed | Blackbox cases historically reported a skip for a `mach-lookup global-name` sandbox_check anomaly (BBX-001); root-caused as a wrong filter type ID in the runner (corrected from 16 → 2 after empirical verification). Other `sandbox_check` divergences (especially for filter kinds whose IDs we have not yet re-verified) may still surface. |
| `smoke` | Shared | Quick end-to-end checks against a built app bundle | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite smoke` |
| `blackbox_e2e` | Shared | End-to-end black-box cases (BBX-*) that treat the runner as a sealed unit and validate the returned JSON envelope | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_e2e` |
| `blackbox_menagerie` | Shared | Real SBPL fixtures exercising specimen ingestion and evidence correlation | Built app + XPC | `dist/PolicyWitness.app` missing; compiled-blob cases skip when profile registration is not permitted on the host | Invoked by `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_menagerie`. See `tests/suites/blackbox_menagerie/README.md` for invariants and fixtures. |
| `sbpl_allowdeny_consistency` | Baseline | SBPL `(allow ...)` / `(deny ...)` verdicts agree with kernel-observed attempt outcomes end-to-end: 4 steps (file write + `mach-lookup`, each allowed and denied) assert allow→exit 0 / `syscall_errno` null / `deny_signal.delta` 0 and deny→exit≠0 / `syscall_errno` populated | Built app + XPC | `dist/PolicyWitness.app` missing or unbuilt | Positive correctness check; `deny_signal` capture can be perturbed in sandboxed harnesses (rerun from a normal Terminal). |
| `opt_in` | Opt-in | Runner-mode opt-ins (logs, DYLD, launchd) | See registry | required resources unavailable (toolchain, GUI session for launchd bootstrap, sandboxed harness for XPC/log capture) | `tests/OPT_IN_TESTS.md` |
| `witness_contract` | Contract | Pins the load-bearing behaviors PolicyWitness contracts to provide: verdicts + attempts + validator failures attributed + removed fields rejected + test seam functioning + audit-rule enforcement. | Built app + XPC | off the default battery (suite is intentionally permissive about environment shape); run on demand | Most cases now pass post-reshape; `happy_path_baseline` is the regression sentinel and should always pass. End-to-end drift *surfacing* is still uncovered here — no current op+filter combination produces clean userland-vs-kernel disagreement through a real specimen (all known cases route to `prediction_unavailable`). The drift *classifier logic* itself (the asymmetric truth table) is unit-tested directly in `runner_unit`'s `computeDrift` table, which drives synthetic verdict/attempt pairs no specimen can currently produce. |

## Conventions

### Blackbox menagerie

End-to-end specimen runs sourced from local copies of PAWL evidence. The suite
covers SBPL ingestion, probe execution, and evidence correlation; it includes
negative controls and canonicalization-boundary cases where mismatches are
recorded as evidence. Compiled-blob cases may skip when profile registration is
not permitted on the host. See `tests/suites/blackbox_menagerie/README.md` for
suite invariants and fixtures.

### Harness note: sandboxed automation environments

Some automation harnesses run commands inside an OS sandbox. In that situation, specimen execution and unified-log based evidence capture can fail for reasons unrelated to PolicyWitness; re-run from a normal Terminal (or with escalation) before diagnosing PolicyWitness itself.

## Output contract (`tests/out/`)

Every invocation of `tests/run.sh` overwrites the prior run output so tooling can read stable paths:

```text
tests/out/
  run.json
  events.jsonl
  suites/<suite>/<test_id>/
    report.json
    events.jsonl
    artifacts/...
```

# Outcome coverage matrices

These two matrices pin which suite/case exercises every enumerated outcome value
the runner can emit. They are reference tables for `tests/README.md`'s suite
coverage map — start there for the per-suite view.

`source_drift` enforces both matrices mechanically: every value in
`runner/Sources/PWRunnerCore/PWRunnerAPI.swift::NormalizedOutcome` and `::AttemptOutcome` must appear
here exactly once. New outcomes are added here in the same change that
introduces the constant. "Untestable" rows are not unmaintained — the notes
column says why, and names the closest unit or harness coverage.

## Normalized outcome coverage matrix

| outcome | emitted by | primary suite/case | notes |
| --- | --- | --- | --- |
| `ok` | C worker (pw-probe-runner) + validator (sb_api_validator) joined by `CWorkerOrchestrator` | `runner_apply_isolation_v2`, `runner_apply_isolation_v3`, `integration`, `runner_use_c_worker`, others | The happy path; covered everywhere. |
| `bad_policy` | host (PWRunnerService) pre-spawn hash failure | none (e2e unreachable) | The Rust controller's preflight short-circuits malformed SBPL as `bad_policy` before invoking the runner. `runner_unit` covers `computePolicyHash` failure indirectly through `applySandboxPolicy` shape tests. |
| `sandbox_apply_failed` | C worker apply path (surfaced via `CWorkerOrchestrator` when `apply_rc != 0`) | `runner_unit` / `SandboxApplyTests` | E2e unreachable because preflight catches the same input upstream as `bad_policy`. Unit tests stub `SandboxLib` to force compile/apply failure. |
| `libsandbox_unavailable` | host (PWRunnerService) pre-spawn check | `runner_outcome_libsandbox_unavailable` | Driven via `_test_overrides.libsandbox_path`. |
| `bad_request` | host (PWRunnerService) — Swift decode + `validateSandboxChecks` + `CWorkerOrchestrator.validateProbePlanForCWorker` (duplicate step_id) | `runner_outcome_bad_request`, `runner_use_c_worker.duplicate_step_id_rejected` | Unknown filter kinds and unknown attempt combos do NOT produce `bad_request` — they downgrade to per-step `prediction_unavailable` / `unsupported` respectively. |
| `already_ran` | host (PWRunnerService) | none (out of scope) | The XPC service exits ~50ms after the first reply, so a second request from the same connection is racy. |
| `worker_spawn_failed` | host (PWRunnerService) | `runner_outcome_worker_spawn_failed` | Driven via `_test_overrides.worker_executable_path`. |
| `runner_sandbox_denied` | host classifier (CWorkerOrchestrator) when the C worker exits from a signal before flipping `done` | `runner_unit` / `HostOutcomeClassifierTests` (classifier logic) + `EnvelopeInvariantTests` (wire-shape pin) | E2e unreachable from any deterministic specimen now that the C worker has a minimal post-apply syscall surface that the bug-report `(deny default)` policy can no longer kill (covered as a survival positive by `runner_use_c_worker.bare_deny_default`). The classifier table pins the load-bearing asymmetry: a foreign signal before `done` → `runner_sandbox_denied`, but a host-sent SIGKILL (grace timer) → `runner_timeout`, not a denial. |
| `runner_timeout` | host classifier | `runner_outcome_runner_timeout`, `witness_contract/worker_post_apply_hang_seam` | Driven via `_test_overrides.worker_timeout_ms` plus `_test_overrides.worker_post_apply_hang_ms`. |
| `runner_failed` | host classifier | `runner_unit` / `HostOutcomeClassifierTests` | No deterministic e2e specimen produces this (it needs a worker shm/pipe/policy-write fault or a validator pipe/serialization fault). The classifier table drives those input shapes directly and asserts the outcome. |
| `validator_spawn_failed` | host classifier (CWorkerOrchestrator) | `witness_contract/validator_spawn_failed_reports_degraded` | Driven via `_test_overrides.validator_executable_path`. `result.ok=false`, `rc=1`; attempts still surfaced as degraded evidence. |
| `validator_no_reply` | host classifier (`verdictReadFailed` / `probeWriteFailed`) | `runner_unit` / `HostOutcomeClassifierTests` | Fires on a real I/O fault reading the validator's stdout or writing probes to its stdin (not a clean short exit — that routes to `validator_unavailable`). Not seam-reachable e2e: the `validator_executable_path` stub can only clean-exit (→ `validator_unavailable`) or genuinely fault, and the 30s read deadline has no `_test_overrides` seam. The classifier table reaches it directly by feeding `classify` a `ValidatorClientResult.failure(.verdictReadFailed)`, which is the exact host disposition that emits this outcome. |
| `validator_decode_failure` | host classifier (`verdictParseFailed`) | `witness_contract/validator_decode_failure_reports_degraded` | Driven via `_test_overrides.validator_executable_path` → a stub that drains the probes then emits a non-NDJSON line, so the host's verdict parse fails. Asserts the outcome and that attempts survive (degraded evidence). |
| `validator_unavailable` | host classifier (clean exit, `verdicts.count < expectedVerdictCount`) | `witness_contract/validator_unavailable_reports_degraded` | Synthesized when the validator clean-exits but returns fewer verdicts than expected (zero or partial) — "PW ran in attempts-only degradation mode." Driven by a stub emitting 1 of 2 expected verdicts; asserts both attempts are preserved. |
| `xpc_error` | client (`pw-runner-client`) synthetic reply | none (e2e requires renaming the `.xpc` bundle out from under launchd) | Reachable in practice when the bundle is missing or launchd refuses to spawn the host. Documented in `PolicyWitness.md` troubleshooting. |
| `xpc_timeout` | client synthetic reply | none (e2e requires a slow specimen plus tight `--timeout-ms`) | Trigger is real (`--timeout-ms 50` plus a long `_test_overrides.worker_post_apply_hang_ms`) but not currently scripted. |
| `xpc_proxy_type_mismatch` | client synthetic reply | none (no realistic trigger) | Fires only if the remote XPC proxy doesn't conform to `PWRunnerProtocol`. Defense-in-depth for a code path that should never run with our matched client/host. |
| `xpc_no_reply` | client synthetic reply | none (no realistic trigger) | Fires only if the XPC reply never arrives but no error fires either. Defense-in-depth. |

## Attempt outcome coverage matrix

| outcome | emitted by | primary coverage | notes |
| --- | --- | --- | --- |
| `ok` | C worker (pw-probe-runner) | every smoke / happy-path suite | The attempt ran and the kernel allowed the operation. |
| `open_failed` | C worker (file open_read / open_write / create) | `runner_use_c_worker.bare_deny_default`, blackbox file-deny cases | Covers both kernel deny (EPERM / EACCES) and ENOENT-class failures; the kernel verdict is in `attempt.errno`. |
| `unlink_failed` | C worker (file unlink) | `runner_c_worker_harness` / `unlink_deny` (+ `unlink_allow` for the success path) | Harness drives `PW_ATTEMPT_FILE_UNLINK` directly: deny-default yields `rc=1` + EPERM/EACCES and the target survives; allow-default removes it. `runner_unit` still covers the Codable shape. E2e-via-controller remains unexercised (no specimen plans an unlink). |
| `access_failed` | C worker (file `access(R_OK)`) | `runner_use_c_worker.access_failure_classified` | Errno preserved in `attempt.errno` (typically EPERM/EACCES on a denied path). |
| `lookup_failed` | C worker (mach_lookup bootstrap_look_up) | `blackbox_e2e` / `core_mach_simple` | The kernel return code is preserved in the error message (e.g. `kr=1102` BOOTSTRAP_UNKNOWN_SERVICE). |
| `sysctl_failed` | C worker (`sysctlbyname` read) | `runner_filter_sysctl_name`, `runner_unit` / `CWorkerTests` | EPERM/EACCES are ambiguous sandbox-vs-privilege failures for drift; ENOENT/ENOMEM are non-policy failures. |
| `exec_failed` | C worker (`posix_spawn` + waitpid) | `runner_use_c_worker.exec_attempt_without_baseline_fails_cleanly`, `runner_unit` / `CWorkerTests` exec cases | Two failure shapes share one outcome name. Drift classifier uses `attempt.child_pid` to distinguish them: `child_pid == 0` + `errno ∈ {EPERM, EACCES}` is a sandbox-denied spawn → strong deny evidence; `child_pid > 0` is a helper that simply exited non-zero → non-policy failure (drift always null). |
| `bootstrap_port_failed` | C worker (mach_lookup) | none (no realistic trigger) | Fires only if `task_get_special_port(TASK_BOOTSTRAP_PORT)` itself fails — defense-in-depth for an OS-level failure that shouldn't happen on a healthy macOS host. |
| `unsupported` | host orchestrator (CWorkerOrchestrator.buildAttemptResult) when (attempt.kind, attempt.action) doesn't map to an implemented C-worker slot | `runner_use_c_worker.unsupported_attempt_per_step_skip` | Per-step skip: the unrecognized step still gets its `sandbox_check` verdict, sibling steps run normally, and `drift` is null. |
| `not_run_worker_died` | host classifier (CWorkerOrchestrator) | `witness_contract/shm_sentinel_under_deny_default` | Synthesized when a slot's `completed=0` after the worker exited — distinguishes "the attempt itself failed" from "the worker never reached this slot." Distinct from `unsupported`, which means the worker reached the slot but didn't know what to do. |

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
| `bad_policy` | host structural-policy admission (`computePolicyHash`) | `runner_unit` (`EnvelopeInvariantTests`) | Missing source or wrong policy format. A published legacy compilation/setup/application failure instead maps to `runner_failed`. |
| `sandbox_apply_failed` | Legacy/reserved; current producers summarize operation failures as runner_failed | `runner_unit` / `HostOutcomeClassifierTests`; `runner_c_worker_harness/compile_failure` protects real publication separately | ABI 6 publishes precise operation/native-result evidence under `runner_failed`; legacy ambiguous status also remains `runner_failed`. Unpublished storage supplies no result. Unused `SandboxApplyTests` has no production attribution credit. |
| `libsandbox_unavailable` | host (PWRunnerService) pre-spawn check | `runner_outcome_libsandbox_unavailable` | Driven via `_test_overrides.libsandbox_path`. |
| `bad_request` | host (PWRunnerService) — Swift decode + `validateSandboxChecks` + `CWorkerOrchestrator.validateProbePlanForCWorker` (duplicate step_id) | `runner_outcome_bad_request`, `runner_use_c_worker.duplicate_step_id_rejected` | Unknown filter kinds and unknown attempt combos do NOT produce `bad_request` — they downgrade to per-step `prediction_unavailable` / `unsupported` respectively. |
| `already_ran` | host (PWRunnerService) | none (out of scope) | The XPC service exits ~50ms after the first reply, so a second request from the same connection is racy. |
| `worker_spawn_failed` | host (PWRunnerService) | `runner_outcome_worker_spawn_failed` | Driven via `_test_overrides.worker_executable_path`. |
| `runner_sandbox_denied` | Recognized legacy string; not currently emitted | `runner_unit` / classifier and legacy encoding controls; `witness_contract/worker_termination_and_log_correlation` | Signals and PID-matched denials do not establish a sandbox termination cause. The self-signal seam produces `runner_failed` and preserves independent denied-attempt evidence. |
| `runner_timeout` | host classifier | `runner_outcome_runner_timeout`, `runner_use_c_worker/worker_timeout_ms_honored`, `witness_contract/worker_post_apply_hang_seam` | Deliberate empty-plan control plus completed single-write and mixed allowed/denied-write plans. All assert host-kill timeout evidence and both overrides; populated plans independently check file effects and retained step evidence with limited agreement (`drift=false`) or unattributed failure (`drift=null`) and `partial_steps=false`. |
| `runner_failed` | host classifier | `runner_unit` / `HostOutcomeClassifierTests`, `CWorkerLifecycleTests`, `WorkerEvidenceTests`, `CWorkerTests`; `witness_contract/worker_termination_and_log_correlation`, `worker_progress_and_failure`, `worker_sparse_failure` | Published worker operation/native-result failure, legacy failure, inconsistent/incomplete report, abnormal or unconfirmed disposition, cleanup/wait fault, or host setup/transport failure. Source-cap rejection and simultaneous host EPIPE survive together. Completed slots survive; the underlying cause can remain unknown. |
| `validator_spawn_failed` | host classifier (CWorkerOrchestrator) | `witness_contract/validator_spawn_failed_reports_degraded` | Driven via `_test_overrides.validator_executable_path`. `result.ok=false`, `rc=1`; attempts still surfaced as degraded evidence. |
| `validator_no_reply` | host classifier (`verdictReadFailed` / `probeWriteFailed`) | `runner_unit` / `HostOutcomeClassifierTests` | Fires on a real I/O fault reading the validator's stdout or writing probes to its stdin (not a clean short exit — that routes to `validator_unavailable`). Not seam-reachable e2e: the `validator_executable_path` stub can only clean-exit (→ `validator_unavailable`) or genuinely fault, and the 30s read deadline has no `_test_overrides` seam. The classifier table reaches it directly by feeding `classify` a `ValidatorClientResult.failure(.verdictReadFailed)`, which is the exact host disposition that emits this outcome. |
| `validator_decode_failure` | host classifier (UTF-8/JSON/structure rejection) | `runner_validator_failure/validator_decode_failure_reports_degraded`, `witness_contract/validator_decode_failure_reports_degraded` | Two valid verdicts arrive in reverse step order before malformed JSON. Asserts partial verdict association, all three completed attempt outcomes and file effects, an explicit gap with drift=null, and the honored override. |
| `validator_unavailable` | host classifier (unique expected-ID coverage and confirmed clean disposition) | `runner_validator_failure/validator_unavailable_reports_degraded`, `witness_contract/validator_unavailable_reports_degraded` | Checked-in transcript returns 2 of 3 verdicts in reverse step order, then clean EOF. Asserts partial verdict association, all three completed attempt outcomes and file effects, the shortfall diagnostic, explicit drift=null for the gap, and the honored override. |
| `xpc_error` | client (`pw-runner-client`) synthetic reply | `smoke/runner_caller_auth` (real rejected and missing-service calls); `runner_unit` response-default controls | Actual client-generated errors and successful peer replies use response 7. The caller-auth suite preserves no-effect controls and verifies disposable app copies without altering the selected source app. |
| `xpc_timeout` | client synthetic reply | none (e2e requires a slow specimen plus tight `--timeout-ms`) | Trigger is real (`--timeout-ms 50` plus a long `_test_overrides.worker_post_apply_hang_ms`) but not currently scripted. |
| `xpc_proxy_type_mismatch` | client synthetic reply | none (no realistic trigger) | Fires only if the remote XPC proxy doesn't conform to `PWRunnerProtocol`. Defense-in-depth for a code path that should never run with our matched client/host. |
| `xpc_no_reply` | client synthetic reply | none (no realistic trigger) | Fires only if the XPC reply never arrives but no error fires either. Defense-in-depth. |

## Evidence contract coverage

The complementary evidence-focused case
`witness_contract/pre_apply_failure_reports_no_policy_verdict` exercises the
real CLI with a populated plan and pre-ready delay/deadline overrides, then
runs an un-overridden positive control. It excludes unsupported apply/compile
and sandbox-cause claims without fixing a replacement outcome name; classifier
tests own that mapping. Its grouped attribution and signal-null checks remain
independent. The [interim contract and coverage audit](FAILURE-PROPAGATION-CONTRACT.md)
assign publication, host-driver and CLI acceptance separately; the
[execution plan](FAILURE-PROPAGATION-PLAN.md#current-execution-state) records which
checks are accepted or still pending.

## Attempt outcome coverage matrix

Host lifecycle observations have separate driver/encoding coverage in
`runner_unit/pwrunner_core_unit_executable`: `CWorkerLifecycleTests` drives
completed reports followed by abnormal exits or cleanup failure using an ABI
fixture and internal OS-call controls; `CWorkerTests` uses the real worker for
deadline followed by voluntary exit and polling-time reaping. `EnvelopeInvariantTests`
protects absent legacy observations and additive encoding. The pre-apply CLI
witness checks forwarding on both failure and success. The classifier tests and live driver controls agree on the
response-6 mapping. Rust correlation tests and the signed CLI retain log
associations separately from execution status and cause.

| outcome | emitted by | primary coverage | notes |
| --- | --- | --- | --- |
| `ok` | C worker (pw-probe-runner) | every smoke / happy-path suite | The attempt ran and the kernel allowed the operation. |
| `open_failed` | C worker (file open_read / open_write / create) | `runner_use_c_worker.bare_deny_default`, blackbox file-deny cases, `witness_contract/create_existing_file_preserves_contents` | Covers permission failures (EPERM / EACCES) and ENOENT-class failures, with errno retained. The create CLI case checks a denied write-open alongside an allowed create on existing files, independently preserving bytes and identities. |
| `unlink_failed` | C worker (file unlink) | `runner_c_worker_harness` / `unlink_deny` (+ `unlink_allow` for the success path) | Harness drives `PW_ATTEMPT_FILE_UNLINK` directly: deny-default yields `rc=1` + EPERM/EACCES and the target survives; allow-default removes it. `runner_unit` still covers the Codable shape. E2e-via-controller remains unexercised (no specimen plans an unlink). |
| `access_failed` | C worker (file `access(R_OK)`) | `runner_use_c_worker.access_failure_classified` | Errno preserved in `attempt.errno` (typically EPERM/EACCES on a denied path). |
| `lookup_failed` | C worker (mach_lookup bootstrap_look_up) | `blackbox_e2e` / `core_mach_simple` | The kernel return code is preserved in the error message (e.g. `kr=1102` BOOTSTRAP_UNKNOWN_SERVICE). |
| `sysctl_failed` | C worker (`sysctlbyname` read) | `runner_filter_sysctl_name`, `runner_unit` / `CWorkerTests` | EPERM/EACCES are ambiguous sandbox-vs-privilege failures for drift; ENOENT/ENOMEM are non-policy failures. |
| `exec_failed` | C worker (`posix_spawn` + waitpid) | `runner_use_c_worker.exec_attempt_without_baseline_fails_cleanly`, `runner_exec_dac`, `runner_exec_lifecycle`, `runner_unit` / `CWorkerTests` exec cases | Spawn failure and helper nonzero exit share this outcome. With `child_pid == 0`, EPERM/EACCES are ambiguous permission failures: predicted allow yields `drift=null`, predicted deny can yield directional consistency with `drift=null` only when submitted scope matches. `runner_exec_dac` verifies ordinary execute-permission EACCES using direct OS controls. A spawned child establishes spawn success independently of its later nonzero exit; `runner_use_c_worker.exec_attempt_args_and_stderr_round_trip` verifies status/output retention and continuation. `runner_exec_lifecycle` verifies deadline cleanup against OS process observations, retained output, and a subsequent file write. |
| `bootstrap_port_failed` | C worker (mach_lookup) | none (no realistic trigger) | Fires only if `task_get_special_port(TASK_BOOTSTRAP_PORT)` itself fails — defense-in-depth for an OS-level failure that shouldn't happen on a healthy macOS host. |
| `unsupported` | host orchestrator (CWorkerOrchestrator.buildAttemptResult) when (attempt.kind, attempt.action) doesn't map to an implemented C-worker slot | `runner_use_c_worker.unsupported_attempt_per_step_skip` | Per-step skip: the unrecognized step still gets its `sandbox_check` verdict, sibling steps run normally, and `drift` is null. |
| `not_run_worker_died` | host step builder | `witness_contract/pre_apply_failure_reports_no_policy_verdict`; `runner_unit` / `AttemptOutcomeMappingTests` | Compatibility spelling for no completed attempt result. Missing/incomplete publication does not prove the operation never started; errno and drift remain null. `WorkerEvidenceTests` starts a slot without publishing its poisoned payload; source/reason/native-null fields identify the gap. |

## Worker publication and sparse evidence

`witness_contract/worker_progress_and_failure` separates real success/compilation
failure from fixture transport of unfamiliar codes and rich/missing/truncated
text. `worker_sparse_failure` proves real source-cap rejection alongside EPIPE,
closed-input fixture reports and absent reports, failed mapping, and completed
real file effects before self-signal. `runner_unit` / `WorkerEvidenceTests`
exercises C production parameter-allocation/assignment/apply call boundaries,
late publication, zero/unfamiliar records, malformed/unpublished payloads,
missing predictions, post-apply memory-only text, and failed cleanup after a
broken pipe. `runner_abi_layout` checks ABI 6 sizes/offsets; incompatible worker
rejection remains in `runner_c_worker_harness`. These controls do not establish
kernel policy attribution from a signal or synthesize a native call from text.

`failure_boundaries` checks every worker admission capacity (exact/over and UTF-8
multibyte boundaries), independent sbpl-check admission, actual C validator line
overflow between valid queries, and fixture reply UTF-8/structure/association.
`ValidatorEvidenceTests` covers actual driver kill/wait failures and abnormal exits
after verdicts, byte framing across delayed multibyte writes, bounded rejected
context, and independent I/O plus decode faults. Rust receiver tests use real
subprocess producers for valid oversized JSON, malformed within-cap output,
invalid UTF-8, and multibyte prefix boundaries. The C harness separately checks
the defensive source guard and published failure record; normal CLI oversized
source is rejected by the host before spawn.

## Unfamiliar diagnostic preservation

`witness_contract/unfamiliar_diagnostic_transport` exercises an ABI-compatible
test worker with two open codes, distinct operations/native results/errno/detail
and UTF-8 diagnostic text. It checks absent/unpublished/malformed/incompatible
records, text truncation independent of code recognition, and a real host EPIPE
beside the unfamiliar worker record. The same case checks two validator
diagnostics beside an observed UTF-8 receiver fault and a fixture-supplied allow
record. That record tests preservation of native-result fields; the transcript
producer does not call `sandbox_check`. The real worker's file change is checked
independently.
`DiagnosticTransportTests` supplies direct ABI/validator decoding and Codable
controls. Rust `unfamiliar_diagnostics_survive_*_capture` tests cover runner,
helper and observer JSON receivers. These are transport controls; real producer
attribution remains covered by the step 1–2 witnesses.

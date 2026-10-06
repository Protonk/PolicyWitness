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
| `bad_policy` | defensive host policy-hash failure (`computePolicyHash`) | `runner_unit` (`EnvelopeInvariantTests`) | Public admission refuses missing source or wrong format as `bad_request` before this boundary. A published compilation/setup/application failure maps to `runner_failed`. |
| `bad_request` | controller syntax/version/selector/augment checks + host closed request decode + `CWorkerOrchestrator.admissionFailure(for:)` (capacity first) + `requestMeaningFailure` | `runner_outcome_bad_request/accepted_input_contract`, `runner_unit`, `runner_use_c_worker.duplicate_step_id_rejected`, `failure_boundaries.admission` | Structured `request_failure` names the refusal and location. Unknown filters, unsupported attempt pairs, duplicate IDs and inapplicable fields refuse the whole specimen before children. Known unavailable predictions retain their per-step observations. |
| `already_ran` | host (PWRunnerService) | none (out of scope) | The XPC service exits ~50ms after the first reply, so a second request from the same connection is racy. |
| `worker_spawn_failed` | host (PWRunnerService) | `runner_outcome_worker_spawn_failed` | Driven via `_test_overrides.worker_executable_path`. |
| `runner_timeout` | host classifier | `runner_outcome_runner_timeout`, `runner_use_c_worker/worker_timeout_ms_honored`, `witness_contract/worker_post_apply_hang_seam` | Deliberate empty-plan control plus completed single-write and mixed allowed/denied-write plans. All assert host-kill timeout evidence and both overrides; populated plans independently check file effects and retained step evidence (allow/`succeeded` and deny/`permission_failure` records) and `partial_steps=false`. |
| `runner_failed` | host classifier | `runner_unit` / `HostOutcomeClassifierTests`, `CWorkerLifecycleTests`, `WorkerEvidenceTests`, `CWorkerTests`; `witness_contract/worker_termination_and_log_correlation`, `worker_progress_and_failure`, `worker_sparse_failure` | Published worker operation/native-result failure, imprecise published failure, inconsistent/incomplete report, abnormal or unconfirmed disposition, cleanup/wait fault, or host setup/transport failure. Source-cap rejection and simultaneous host EPIPE survive together. Completed slots survive; the underlying cause can remain unknown. |
| `runner_reporting_failed` | host reply boundary | `runner_unit` / `ReplyFailureTests`; `blackbox_e2e/checker_controls` | Constructed invariant rejection preserves original summary, queries, attempts and subprocess observations and withholds comparisons. Repeated encoder failure explicitly reports evidence loss. No result-forcing request override. |
| `validator_spawn_failed` | host classifier (CWorkerOrchestrator) | `witness_contract/validator_spawn_failed_reports_degraded` | Driven via `_test_overrides.validator_executable_path`. `result.ok=false`, `rc=1`; attempts still surfaced as degraded evidence. |
| `validator_no_reply` | host classifier (`verdictReadFailed` / `probeWriteFailed`) | `runner_outcome_validator_no_reply/validator_io_deadline_releases_worker`; `runner_unit` | Real monotonic I/O deadline after one of two verdicts; exact override echo and deadline diagnostic, retained eligible prediction, confirmed validator cleanup and both independently observed worker writes after release. |
| `validator_decode_failure` | host classifier (UTF-8/JSON/structure rejection) | `runner_validator_failure/validator_decode_failure_reports_degraded`, `witness_contract/validator_decode_failure_reports_degraded` | Two valid verdicts arrive in reverse step order before malformed JSON. Asserts partial verdict association, all three completed attempt outcomes and file effects, an explicit gap with its missing reason, and the honored override. |
| `validator_unavailable` | host classifier (unique expected-ID coverage and confirmed clean disposition) | `runner_validator_failure/validator_unavailable_reports_degraded`, `witness_contract/validator_unavailable_reports_degraded` | Checked-in transcript returns 2 of 3 verdicts in reverse step order, then clean EOF. Asserts partial verdict association, all three completed attempt outcomes and file effects, the shortfall diagnostic, the gap's missing reason, and the honored override. |
| `xpc_error` | client (`pw-runner-client`) synthetic reply | `smoke/runner_caller_auth` (real rejected and missing-service calls); `runner_unit` response-default controls | Client-generated failure replies carry the current response schema with empty steps. The caller-auth suite preserves no-effect controls and verifies disposable app copies without altering the selected source app. |
| `xpc_timeout` | client synthetic reply | none (e2e requires a slow specimen plus tight `--timeout-ms`) | Trigger is real (`--timeout-ms 50` plus a long `_test_overrides.worker_post_apply_hang_ms`) but not currently scripted. |
| `xpc_proxy_type_mismatch` | client synthetic reply | none (no realistic trigger) | Fires only if the remote XPC proxy doesn't conform to `PWRunnerProtocol`. Defense-in-depth for a code path that should never run with our matched client/host. |
| `xpc_no_reply` | client synthetic reply | none (no realistic trigger) | Fires only if the XPC reply never arrives but no error fires either. Defense-in-depth. |

## Evidence contract coverage

The complementary evidence-focused case
`witness_contract/pre_apply_failure_reports_no_policy_verdict` exercises the
real CLI with a populated plan and pre-ready delay/deadline overrides, then
runs an un-overridden positive control. It excludes unsupported apply/compile
and sandbox-cause claims without fixing a replacement outcome name; classifier
tests own that mapping. Its grouped attribution checks remain independent.
The [failure contract](FAILURE-PROPAGATION-CONTRACT.md) assigns publication,
host-driver and CLI coverage separately. Its
[comparison record ownership table](FAILURE-PROPAGATION-CONTRACT.md#comparison-record)
names which case owns which matrix rows and invariants. Consumer validation
uses only one envelope; tests keep their scenario expectations separate from
the reported records.

Log coverage separates three claims, all in the default selection:

| Claim | Required coverage | Limit of the claim |
| --- | --- | --- |
| OS query selection | `witness_contract/log_query_predicate_archive`: real `log show`, committed archive, independent positive/negative multisets before parsing | Fixture forms and verified readers; no claim about kernel emission |
| Record preservation and execution independence | `unit/rust.unit`: supplied-text parser/receiver/assembly/consumer replay, capacity, deadline/byte/cleanup faults; `blackbox_e2e/checker_controls`: consumer recovery across capture states | Exact controlled inputs and expected candidates; no live retrieval-completeness claim |
| Live collection evidence | `witness_contract/deny_capture_covers_the_run`, `worker_termination_and_log_correlation`, `max_targets_reply_survives`, with independent `log_capture_controls` | Native execution remains mandatory. Complete empty queries and evidenced budget exhaustion with confirmed cleanup are admissible; unsupported failures are not. |

The [witness suite](suites/witness_contract/README.md#deny-capture-covers-the-run)
defines these oracles and their equipment requirements. Missing log records do
not establish allowance or a cause for an attempted failure.

## Attempt outcome coverage matrix

Host lifecycle observations have separate driver/encoding coverage in
`runner_unit/pwrunner_core_unit_executable`: `CWorkerLifecycleTests` drives
completed reports followed by abnormal exits or cleanup failure using an ABI
fixture and internal OS-call controls; `CWorkerTests` uses the real worker for
deadline followed by voluntary exit and polling-time reaping. `EnvelopeInvariantTests`
protects the encoded reply shape and the absence of the removed wire keys (`drift`, `deny_signal`, the attempt aliases and the comparison's former fields). The pre-apply CLI
witness checks forwarding on both failure and success. The classifier tests and live driver controls agree on the
outcome mapping. Rust correlation tests and the signed CLI retain log
associations separately from execution status and cause.

| outcome | emitted by | primary coverage | notes |
| --- | --- | --- | --- |
| `ok` | C worker (pw-probe-runner) | every smoke / happy-path suite | The attempt ran and the kernel allowed the operation. |
| `open_failed` | C worker (file open_read / open_write / create) | `runner_use_c_worker.bare_deny_default`, blackbox file-deny cases, `witness_contract/create_existing_file_preserves_contents` | Covers permission failures (EPERM / EACCES) and ENOENT-class failures, with errno retained. The create CLI case checks a denied write-open alongside an allowed create on existing files, independently preserving bytes and identities. |
| `unlink_failed` | C worker (file unlink) | `runner_c_worker_harness` / `unlink_deny` (+ `unlink_allow` for the success path) | Harness drives `PW_ATTEMPT_FILE_UNLINK` directly: deny-default yields `rc=1` + EPERM/EACCES and the target survives; allow-default removes it. `runner_unit` covers the Codable shape; `witness_contract/comparison_matrix` (rows S19, B3 and B6 plan unlinks; S25 and B5 read the paths S19 and B6 remove) and `run_effects` plan unlinks through the controller. |
| `access_failed` | C worker (file `access(R_OK)`) | `runner_use_c_worker.access_failure_classified` | Errno preserved in `attempt.errno` (typically EPERM/EACCES on a denied path). |
| `lookup_failed` | C worker (mach_lookup bootstrap_look_up) | `blackbox_e2e` / `core_mach_simple` | The kernel return code is preserved in the error message (e.g. `kr=1102` BOOTSTRAP_UNKNOWN_SERVICE). |
| `sysctl_failed` | C worker (`sysctlbyname` read) | `runner_filter_sysctl_name`, `runner_unit` / `CWorkerTests` | EPERM/EACCES are permission-shaped failures without sandbox attribution; ENOENT/ENOMEM are non-policy failures. |
| `exec_failed` | C worker (`posix_spawn` + waitpid) | `runner_use_c_worker.exec_attempt_without_baseline_fails_cleanly`, `runner_exec_dac`, `runner_exec_lifecycle`, `runner_unit` / `CWorkerTests` exec cases | Spawn failure and helper nonzero exit share this outcome. With `child_pid == 0`, EPERM/EACCES are permission-shaped failures whose cause the record does not assign. `runner_exec_dac` verifies ordinary execute-permission EACCES using direct OS controls and exercises native exec-query mapping under independent exec/fork/interpreter policies. The query covers target admission, not every spawn prerequisite. A spawned child establishes spawn success independently of its later nonzero exit; `runner_use_c_worker.exec_attempt_args_and_stderr_round_trip` verifies status/output retention and continuation. `runner_exec_lifecycle` verifies deadline cleanup against OS process observations, retained output, and a subsequent file write. |
| `unsupported` | defensive host result construction for an unimplemented (attempt.kind, attempt.action) | `runner_unit` / `AttemptOutcomeMappingTests` and `DispositionResolverTests` | Constructed unsupported slots cannot claim successful execution. Public requests refuse these pairs before children; `runner_use_c_worker.unsupported_attempt_rejected` and the shared request corpus cover that refusal. |
| `not_run_worker_died` | host step builder | `witness_contract/pre_apply_failure_reports_no_policy_verdict`; `runner_unit` / `AttemptOutcomeMappingTests` | The spelling for no completed attempt result. Missing/incomplete publication does not prove the operation never started; errno remains null and the comparison carries the lifecycle limitation. `WorkerEvidenceTests` starts a slot without publishing its poisoned payload; source/reason/native-null fields identify the gap. |

## Worker publication and sparse evidence

`witness_contract/worker_progress_and_failure` separates real success/compilation
failure from fixture transport of unfamiliar codes and rich/missing/truncated
text. `worker_sparse_failure` proves real source-cap rejection alongside EPIPE,
closed-input fixture reports and absent reports, failed mapping, and completed
real file effects before self-signal. `runner_unit` / `WorkerEvidenceTests`
exercises C production parameter-allocation/assignment/apply call boundaries,
late publication, zero/unfamiliar records, malformed/unpublished payloads,
missing predictions, post-apply memory-only text, and failed cleanup after a
broken pipe. `runner_abi_layout` checks the worker ABI sizes/offsets; incompatible worker
rejection remains in `runner_c_worker_harness`. These controls do not establish
kernel policy attribution from a signal or synthesize a native call from text.

`failure_boundaries` checks every admission capacity, worker and host-only
(exact/over and UTF-8 multibyte boundaries, capacity before shape, no echo of the
refused string), independent sbpl-check admission (the shipped helper's size
refusal with null compile and import-inventory groups; the helper's native
verdict matrix, stage record and exit-2 paths are `integration/cli.integration`,
its controlled setup/compile/release paths and the capture's status precedence
are `unit/rust.unit`), admission refusal of an
overlong query with the largest admitted probe line measured against the native
cap, control-character round trip through the real validator, and fixture reply
UTF-8/structure/association.
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
attribution remains covered by `witness_contract/worker_progress_and_failure`,
`witness_contract/worker_sparse_failure`, and the `failure_boundaries` cases
listed in the [coverage ownership table](FAILURE-PROPAGATION-CONTRACT.md#coverage-audit-and-acceptance-ownership).

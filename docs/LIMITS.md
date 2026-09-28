# PolicyWitness limits

<!-- BEGIN SHARED LIMITS -->
A profile accepted by `libsandbox` can still exceed PolicyWitness's input
capacities, exhaust an execution budget, or produce more evidence than a reply
can carry. This inventory covers specimen admission, execution, comparison 
transport and retained evidence.

Counts of UTF-8 bytes are not counts of characters. Admission limits apply before
worker launch. Capture limits usually reduce evidence after work has happened.
The diagnostic `sbpl-check` helper has separate limits and is not the normal
worker admission path. Its import inventory does not control libsandbox's own
import resolution or compilation.

## Interactions that matter

- Raising `--timeout-ms` changes the client wait only. The worker and validator
  retain their own budgets. None of these numbers promises an end-to-end runtime:
  worker policy transfer precedes polling, synchronous validator work is outside
  the worker polling budget, and cleanup/reaping can take additional time.
- The controller's runner-client budget is derived, not tuned: three times the
  synthesized maximal reply (`runner_reply_maximum`, the field-complete reply
  fixture with 256 steps and records and every string at its limit, encoded by
  the production encoder), rounded up to a whole 4 MiB. Helper and log-observer
  streams keep an independent 8 MiB. Receivers report their budget in
  `capture_limit_bytes`; collection still buffers the whole stream first. The
  synthesized number is an upper bound for the schema, since it puts fields
  that cannot co-occur in one run side by side; the live 256-step corpus is
  evidence that real replies stay inside it. A reply string key added without a
  size classification fails runner_unit, so the bound follows the schema.
- Service and direct orchestration share admission. Top-level metadata comes
  first, then plan/parameter counts, worker strings and host query fields.
  Each string checks its UTF-8 capacity before its native-string constraint.
  Refusals select one diagnostic but independently sanitize every echoed
  metadata field. Oversized or invalid identities are omitted or replaced by
  explicit placeholders, never shortened into apparent submitted identities.
- Native C strings (source, parameters, step IDs, targets, exec arguments,
  query operations/values and override paths) reject embedded NUL before any
  process work. The admission record counts `nul_bytes` against maximum zero.
  The worker's reader refuses a NUL in the policy on its own (exit 9, failure
  code 9, offset in detail) rather than compile a prefix; the shared-memory
  string slots carry no length, so for them the host rule is the only guard.
  Other control characters and valid Unicode survive JSON transport exactly;
  host-only metadata and labels may also contain escaped NUL. The validator
  rejects raw controls, invalid UTF-8, malformed escapes and lone surrogates,
  while preserving the next physical probe line. Decoder failures report a
  bounded category/path instead of arbitrary input-derived exception prose.
- Exec attempts spend descriptors before the sandbox applies, four per step,
  so the worker counts free descriptor slots and raises its soft limit to fit
  the plan plus reserved headroom before opening any pipe. Inherited descriptors
  count against availability. If the hard limit prevents the plan from fitting,
  excess exec steps report a descriptor-budget refusal before opening pipes;
  compilation and other attempts keep their headroom. The refusal is per-step
  evidence and does not by itself fail the run.
- Deny-log capture has no fixed lookback limit. The requested interval is the
  runner client's wall-clock span, widened to whole seconds because `log show`
  accepts nothing finer. Reversed endpoints prevent the scan; ordered endpoints
  do not establish clock continuity or complete log delivery. Archive access has
  been observed to cost seconds even for short spans; scan cost is not guaranteed
  to be independent of span or log volume.

<!-- BEGIN GENERATED LIMITS -->

Values are maxima unless labelled as defaults.

## Specimen admission

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Policy source (`policy_source`) | 262,143 UTF-8 bytes | Final SBPL source after augments; excludes terminating NUL. Imported file contents are not added to this count. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Probe steps (`probe_steps`) | 256 items | Entries in probe_plan. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Policy parameters (`policy_parameters`) | 1,024 items | Entries in the policy parameter dictionary. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Step ID (`step_id`) | 63 UTF-8 bytes | Each step_id, excluding terminating NUL. A refused step ID is identified by step_index only, never echoed. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Attempt target (`attempt_target`) | 511 UTF-8 bytes | Each attempt target (path, service or sysctl name), excluding terminating NUL. Also the exec argv[0]. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Supplied exec arguments (`exec_arguments`) | 15 items | Arguments supplied in attempt.args; the target occupies the additional argv[0] slot. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Each supplied exec argument (`exec_argument`) | 127 UTF-8 bytes | Each supplied argument, excluding terminating NUL; the target has its own larger limit. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Parameter key (`parameter_key`) | 127 UTF-8 bytes | Each key, excluding terminating NUL. A refused key is identified by field and byte count only, never echoed. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Parameter value (`parameter_value`) | 383 UTF-8 bytes | Each value, excluding terminating NUL. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Query operation (`query_operation`) | 127 UTF-8 bytes | Each sandbox_check.operation, excluding terminating NUL. Host-only: the string goes to the validator line and is echoed per step in the reply; it never enters shared memory. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Query filter value (`query_filter_value`) | 511 UTF-8 bytes | Each sandbox_check.filter.value when present, for every filter kind including none and unrecognized kinds, excluding terminating NUL. Independent of the attempt target: a step may query one path and attempt another, and each string is bounded on its own. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Probe filter and attempt labels (`probe_plan_label`) | 127 UTF-8 bytes | Each sandbox_check.filter.kind, attempt.kind and attempt.action, excluding terminating NUL. Unknown labels within the bound retain their per-step prediction_unavailable or unsupported behavior. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Specimen ID (`specimen_id`) | 255 UTF-8 bytes | The specimen_id string, excluding terminating NUL. Echoed once per reply; a refused ID is replaced by the placeholder <admission_refused>. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Request labels (`request_label`) | 63 UTF-8 bytes | Each of run_kind and policy.format, excluding terminating NUL. Echoed once per reply; a refused run_kind is omitted and a refused format reads unknown. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Test-seam executable paths (`test_override_path`) | 1,023 UTF-8 bytes | Each of _test_overrides.libsandbox_path, worker_executable_path and validator_executable_path, excluding terminating NUL. Mirrored back in test_overrides and named in dlopen and spawn diagnostics; every invalid path is independently dropped from a refusal mirror, even if another field is reported first. Excess rejects the specimen after decoding and before semantic validation or process work: bad_request with host-owned admission_failure. | Fixed; no public override. |

## Execution budgets

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Worker readiness hint wait (`worker_ready_wait`) | 1,000 milliseconds | Initial ready-byte polling budget. Expiry alone does not abort: the host still checks shared-memory publication. | Production default; test-only controls are not a public tuning interface. |
| Worker publication wait (`worker_sentinel_wait`) | 60,000 milliseconds | Nominal polling budget for worker sentinels. Synchronous validator work is outside this budget. Expiry can trigger worker cleanup and runner_timeout with partial evidence. | Production default; test-only controls are not a public tuning interface. |
| Worker exit grace (`worker_exit_grace`) | 1,000 milliseconds | Polling grace after the host requests exit. Expiry triggers a SIGKILL attempt, then reaping. Kill/reap failures remain reported. | Production default; test-only controls are not a public tuning interface. |
| Worker release wait (`worker_proceed_wait`) | 60,000 milliseconds | Elapsed CLOCK_MONOTONIC time after successful apply, before host release acknowledgement. Expiry or clock failure publishes a proceed failure and done with no attempts. The existing exit-request spin can outlive a dead host. | Production default and internal test equipment; not a public CLI tuning interface. |
| Nominal release margin (`validator_release_margin`) | 5,000 milliseconds | Configuration allowance for host observation, setup, decoding and scheduling, not a separately enforced timer. Production defaults satisfy 60000 > 30000 + 1000 + 5000. This guard does not cover test overrides or bound final blocking reap, host descheduling, prompt replies or eventual orphan cleanup. | Production default and internal test equipment; not a public CLI tuning interface. |
| Validator I/O test override floor (`validator_io_override_floor`) | 50 milliseconds | Minimum effective _test_overrides.validator_io_timeout_ms; request schema remains 1. Changes only the real validator I/O deadline, with no ceiling. Over-budget values may intentionally outlast the worker release wait; expiry cannot revive attempts. The supplied value is mirrored in every reply. | Production default and internal test equipment; not a public CLI tuning interface. |
| Validator I/O deadline (`validator_io_wait`) | 30,000 milliseconds | Elapsed CLOCK_MONOTONIC deadline for nonblocking probe writes and verdict reads; wall-clock changes cannot extend it. Retains received verdicts and records an I/O timeout; cleanup follows. | Production default; _test_overrides.validator_io_timeout_ms replaces this deadline, floored at 50 ms without a ceiling and mirrored in results. |
| Validator exit grace (`validator_exit_grace`) | 1,000 milliseconds | Polling grace after closing validator pipes. Expiry triggers a SIGKILL attempt, then reaping; failures remain reported. | Production default; test-only controls are not a public tuning interface. |
| Exec child deadline (`exec_child_wait`) | 10,000 milliseconds | Per-exec child observation deadline after successful spawn. Worker attempts to kill/reap the child; the step records that the deadline fired. | Production default; test-only controls are not a public tuning interface. |
| Exec attempt descriptors (`exec_step_descriptors`) | 4 items | Descriptors opened before sandbox application per exec step: both ends of stdout and stderr pipes. Before opening any, the worker scans for free descriptor numbers, accounting for inherited descriptors, and raises its soft limit to fit the plan plus the descriptor reserve. Raises are capped at the hard limit and OPEN_MAX (10,240); an already higher soft limit is preserved. Only exec slots that fit without spending the reserve get pipes. Excess slots report exec_failed with errno 24 and an exec descriptor budget diagnostic naming the limit; no pipe syscall or child spawn is claimed. Actual pipe failures report their own syscall and errno. Budget refusal is per-step evidence, with sandbox attribution unestablished; imports and other attempts retain descriptor headroom. | Host-derived hard ceiling; no public override. The worker raises the soft limit and never lowers it. |
| Exec descriptor reserve (`exec_descriptor_reserve`) | 64 items | Free descriptor slots withheld from exec pipe setup, in addition to descriptors already open. The worker scans with fcntl(F_GETFD) to find room for this reserve plus four descriptors per exec step. Preserves headroom for policy compilation/imports, file probes, and spawn file actions. If the inherited/hard limit already leaves fewer free slots than the reserve, exec setup opens no pipes. This bounds exec pipe consumption; it does not guarantee that arbitrary imports or other resource users fit. | Fixed; no public override. |
| Runner RPC wait (`client_rpc_wait`) | 240,000 milliseconds | Client wait for the runner reply. An expired wait yields runner_timeout; it does not expand the inner worker or validator budgets. | Default; --timeout-ms changes only this wait and floors its value at 1 ms. |

## Queries and transport

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Validator query payload (`validator_query_payload`) | 65,534 bytes | Serialized JSON bytes for one probe, before the LF delimiter. Escaping counts. The fixed 65536-byte buffer retains the 65534-byte payload allowance; the reader counts physical bytes, including raw NUL, and drains the rest of an overlong line. An overlong line produces one parse_error with no step ID; that prediction is unavailable. Later lines can still be processed. Admitted specimens cannot reach it: with the operation and filter value admission-bounded, a fully escaped probe line stays a few KiB. | Fixed; no public override. |
| Synthesized maximal reply (`runner_reply_maximum`) | 21,660,314 bytes | Encoded size, through the production encoder, of the field-complete reply fixture with 256 steps, 256 validator records and disposition entries, every request- or host-derived string at its documented limit and made of U+0001 (six JSON bytes per byte), the largest worker diagnostic, and the largest slash-heavy compiled-profile receipt. An upper bound for the current response schema: fields that cannot co-occur in one run are all present. Not enforced anywhere; it derives the runner client budget. A reply string key added to the fixture without a size classification fails runner_unit, so the number cannot silently fall behind the schema. | Recomputed by runner_unit; edit the manifest when the synthesizer's number moves. |
| Runner client output (`controller_output`) | 67,108,864 bytes | Per stdout or stderr stream captured from the runner client. Byte prefix before lossy text decoding; not an envelope-wide cap. Output beyond the prefix is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Derived: three times runner_reply_maximum, rounded up to a whole 4 MiB. runner_unit asserts the relation against the compiled Rust constant's documented value; no public override. |
| Log observer output (`log_observer_output`) | 8,388,608 bytes | Per stdout or stderr stream captured from sandbox-log-observer. Byte prefix before lossy text decoding; independent of the runner reply budget. Output beyond the prefix is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Fixed; no public override. Unlike the runner reply, the observer's output is log volume over the client span, not admitted request strings, so no admission bound derives this budget. |
| Policy helper output (`policy_helper_output`) | 8,388,608 bytes | Per stdout or stderr stream captured from sbpl-check. Byte prefix before lossy text decoding; independent of the runner reply budget. Output beyond the prefix is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Fixed; no public override. |
| Rejected validator frame context (`validator_fault_context`) | 256 bytes | Raw prefix of the first rejected frame, before base64 encoding. The remaining frame is not retained as context; frame_bytes, retained_bytes and context_truncated describe the loss. | Fixed; no public override. |

## Evidence capture

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Exec child output per stream (`exec_stream`) | 1,023 bytes | Retained bytes in each stdout/stderr text buffer, excluding NUL. A truncation marker occupies part of this space on overflow. Additional output is drained but not retained. | Fixed; no public override. |
| Primary worker diagnostic (`worker_diagnostic`) | 4,095 bytes | Diagnostic payload bytes, excluding NUL. The primary diagnostic is bounded and reports retained length and truncation state; it is not a transcript. | Fixed; no public override. |
| Optional compiled-object capture (`applied_profile`) | 1,048,576 bytes | Raw bytecode bytes for a nonempty supported single-profile (type 0) object, before base64 encoding. Oversize or unsupported objects leave capture unavailable without preventing policy application. | Fixed; no public override. |
| Worker observed path (`observed_path`) | 1,023 bytes | Per-step C path-buffer payload bytes, excluding NUL. Path observation can be absent or bounded; a host-side path diagnostic is a separate observation. | Fixed; no public override. |
| Worker attempt error text (`attempt_error`) | 255 bytes | Per-step error-buffer payload bytes, excluding NUL. Error prose is bounded; structured result/status fields remain separate. | Fixed; no public override. |

## Diagnostic helpers

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| sbpl-check source admission (`helper_source`) | 4,194,304 bytes | Top-level source bytes read by the diagnostic helper; not the runner policy cap. policy_too_large without a compile verdict. | Fixed; no public override. |
| sbpl-check import inventory depth (`helper_import_depth`) | 8 levels | Top-level imports start at depth 0. At depth 8 the helper records a depth-limit diagnostic instead of reading/expanding that file. Stops inventory expansion on that branch and marks imports_truncated. Does not impose this depth on libsandbox compilation. | Fixed; no public override. |
| sbpl-check import inventory count (`helper_import_count`) | 64 records | Maximum records accumulated by the helper traversal, including unresolved/error records; visited files/names are deduplicated. Stops further inventory traversal and marks imports_truncated. Does not impose this count on libsandbox compilation. | Fixed; no public override. |
| Log observer stream text (`observer_stream_text`) | 1,048,576 bytes | Streaming helper mode only (--duration or --follow): retained nonempty, non-prelude log lines with one LF per line. Only whole lines that fit are retained. The first overflowing line sets log_truncated and stops text accumulation. Deny-event arrays and JSONL emission continue separately; this is not a memory or total-report cap. The normal CLI log-show path does not use this inner cap. | Fixed byte cap; --no-log-capture disables normal CLI log collection, not this helper capability. |

<!-- END GENERATED LIMITS -->
<!-- END SHARED LIMITS -->

See the [user guide](PolicyWitness.md) for the request and response contracts.
Tables are generated from [limits.json](limits.json).

<!-- BEGIN GENERATED LIMIT COVERAGE -->

## Grounding and coverage

Value checks compare the inventory with compiled constants, constructed defaults or actual returned bytes. Boundary checks exercise a limit and its consequence; path checks cover related behavior without proving the exact boundary. A source reference alone is not a value check. Coverage notes below identify where behavior remains source-inspected.

| Limit ID | Implementation | Permanent checks | Behavioral coverage |
| --- | --- | --- | --- |
| `policy_source` | [`PW_SHM_POLICY_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `probe_steps` | [`PW_SHM_MAX_STEPS`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `policy_parameters` | [`PW_SHM_MAX_PARAMS`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `step_id` | [`PW_SHM_STEP_ID_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `attempt_target` | [`PW_SHM_TARGET_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `exec_arguments` | [`PW_SHM_MAX_ARGV`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `exec_argument` | [`PW_SHM_ARGV_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `parameter_key` | [`PW_SHM_PARAM_KEY_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `parameter_value` | [`PW_SHM_PARAM_VALUE_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `query_operation` | [`sandboxCheckOperationMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`queryAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py); boundary: [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | At-limit, over-limit and multibyte admission controls through the CLI; constructed orchestrator controls refuse before any process work and cover every filter kind. |
| `query_filter_value` | [`sandboxCheckFilterValueMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`queryAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py); boundary: [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | At-limit, over-limit and multibyte admission controls through the CLI; constructed orchestrator controls refuse before any process work and cover every filter kind. |
| `probe_plan_label` | [`probePlanLabelMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`queryAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py); boundary: [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Exact, over-limit and multibyte boundaries through the CLI; 256-step oversized-label regressions require a small refusal and unchanged write targets. |
| `specimen_id` | [`specimenIdMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`requestAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py); boundary: [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; the refusal reply never contains the refused string. |
| `request_label` | [`requestLabelMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`requestAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py); boundary: [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; an at-limit format passes admission and fails as bad_policy. |
| `test_override_path` | [`testOverridePathMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`requestAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`admission`](../tests/suites/failure_boundaries/check.py); boundary: [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; at-limit nonexistent paths pass admission and reach their own seam failures. |
| `worker_ready_wait` | [`CWorkerInput`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | Normal readiness is tested; expiry without aborting is source-inspected. |
| `worker_sentinel_wait` | [`timeoutMsForCWorker`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | Deadline and partial-publication paths use shortened test budgets; the production duration is source-inspected. |
| `worker_exit_grace` | [`CWorkerInput`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) | Deadline/cleanup paths use controlled children; the production duration is source-inspected. |
| `worker_proceed_wait` | [`PW_PROCEED_WAIT_MS_DEFAULT`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value: [`NATIVE_LIMITS`](../tests/suites/runner_abi_layout/limits.py); path: [`proceed_wait_budget_short`](../tests/suites/runner_c_worker_harness/harness.c); path: [`runOrderingTests`](../runner/Tests/PWRunnerCoreTests/OrderingTests.swift) | Short-budget, delayed-release, clock-failure and delayed-cleanup controls establish fail-closed behavior; production duration is value-checked. |
| `validator_release_margin` | [`validatorReleaseMarginMs`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | Short-budget, delayed-release, clock-failure and delayed-cleanup controls establish fail-closed behavior; production duration is value-checked. |
| `validator_io_override_floor` | [`timeoutMsForValidator`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | Short-budget, delayed-release, clock-failure and delayed-cleanup controls establish fail-closed behavior; production duration is value-checked. |
| `validator_io_wait` | [`ValidatorClientInput`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runValidatorEvidenceTests`](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift) | I/O deadline and partial-evidence paths use shortened budgets; the production duration is source-inspected. |
| `validator_exit_grace` | [`ValidatorClientInput`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runValidatorEvidenceTests`](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift) | Cleanup paths use controlled children; the production duration is source-inspected. |
| `exec_child_wait` | [`PW_EXEC_CHILD_DEADLINE_MS_DEFAULT`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value: [`NATIVE_LIMITS`](../tests/suites/runner_abi_layout/limits.py); path: [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | Shortened deadline and cleanup controls; the production duration is source-inspected. |
| `exec_step_descriptors` | [`PW_EXEC_DESCRIPTORS_PER_STEP`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`setup_exec_resources`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value: [`NATIVE_LIMITS`](../tests/suites/runner_abi_layout/limits.py); boundary: [`main`](../tests/suites/witness_contract/check_max_exec_steps.py); path: [`run_exec_descriptor_limit`](../tests/suites/runner_c_worker_harness/run.sh); path: [`EXEC_STEPS`](../tests/suites/witness_contract/check_max_target_reply.py) | The per-step count is value-checked against the compiled worker. A 256-exec plan is pinned live through the CLI. Native harness cases cover a raised soft limit, 80 extra inherited descriptors, and hard caps 64 and 126 through 129 with policy imports and reads before/after execs. Every prepared child must exit cleanly and excess slots must report budget refusal. The OPEN_MAX clamp is source-inspected. |
| `exec_descriptor_reserve` | [`PW_EXEC_DESCRIPTOR_RESERVE`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`prepare_exec_descriptor_budget`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value: [`NATIVE_LIMITS`](../tests/suites/runner_abi_layout/limits.py); path: [`run_exec_descriptor_limit`](../tests/suites/runner_c_worker_harness/run.sh) | Value-checked against the compiled worker. Capped mixed plans require successful policy imports and file reads even when all exec slots are refused, and clean exits for every prepared exec. The inherited-descriptor case requires all 32 execs with ample hard-limit capacity. |
| `client_rpc_wait` | [`DEFAULT_TIMEOUT_MS`](../controller/src/run_flow.rs); [`defaultClientTimeoutMs`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`defaultClientTimeoutMs`](../runner/Clients/PWRunnerClient/main.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value: [`documented_controller_limits`](../controller/src/run_flow.rs) | The production wait and timeout response are source-inspected; compiled default agreement is tested. |
| `validator_query_payload` | [`LINE_MAX_BYTES`](../controller/tools/sb_api_validator/sb_api_validator.c); [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value: [`NATIVE_LIMITS`](../tests/suites/runner_abi_layout/limits.py); boundary: [`query_boundary`](../tests/suites/runner_abi_layout/limits.py); path: [`validator_overlong_request`](../tests/suites/failure_boundaries/check.py) | Exact payload boundary, over-limit drain/recovery, valid raw and escaped Unicode, malformed escapes/UTF-8/raw controls and raw-NUL physical framing. Every rejected probe is followed by a valid recovery probe. |
| `runner_reply_maximum` | [`maximalReplyEncodedSize`](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift); [`pwRunnerEncodeJSON`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`runReplyMaximumTests`](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift); path: [`main`](../tests/suites/witness_contract/check_max_target_reply.py) | The synthesizer's value is compared with the manifest; the budget relation is asserted; an injected unclassified key is detected. Live 256-step workloads are measured against this bound. |
| `controller_output` | [`RUNNER_CAPTURE_BYTES`](../controller/src/utils.rs) | value: [`documented_controller_limits`](../controller/src/run_flow.rs); path: [`mod tests`](../controller/src/runner_client.rs); path: [`main`](../tests/suites/witness_contract/check_max_target_reply.py) | Exact prefix and truncation-boundary controls, including small arbitrary budgets and every cut within multibyte scalars. Collection buffers the entire stream first; this is not a memory limit. Five admitted 256-step CLI workloads at the admitted maxima, including the control-character exec workload with 511-byte targets and queries, 63-byte step IDs, maximal metadata and live profile capture, must each stay under runner_reply_maximum; the budget then holds a complete reply with a threefold margin by construction. |
| `log_observer_output` | [`OBSERVER_CAPTURE_BYTES`](../controller/src/utils.rs) | value: [`documented_controller_limits`](../controller/src/run_flow.rs); boundary: [`arbitrary_budgets_preserve_counts_at_every_unicode_cut`](../controller/src/utils.rs) | The shared receiver accepts an explicit per-stream retention budget for this producer; exact byte counts, truncation and JSON parse suppression are tested independently of the runner budget. Exceeding it loses the whole deny-log channel for the run (capture_error), while worker attempts, predictions and attribution are unaffected; a per-event truncation that keeps the captured prefix usable would be the next step if that loss is observed in practice. |
| `policy_helper_output` | [`HELPER_CAPTURE_BYTES`](../controller/src/utils.rs) | value: [`documented_controller_limits`](../controller/src/run_flow.rs); boundary: [`arbitrary_budgets_preserve_counts_at_every_unicode_cut`](../controller/src/utils.rs) | The shared receiver accepts an explicit per-stream retention budget for this producer; exact byte counts, truncation and JSON parse suppression are tested independently of the runner budget. |
| `validator_fault_context` | [`decodeValidatorFrames`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | Exact and over-limit invalid-frame context controls; no rejected bytes become verdicts. |
| `exec_stream` | [`PW_SHM_CHILD_OUTPUT_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | Small stdout/stderr capture is tested. Overflow truncation and the exact retained-prefix/marker split are source-inspected. |
| `worker_diagnostic` | [`PW_SHM_DIAGNOSTIC_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runWorkerEvidenceTests`](../runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift) | Bounded diagnostic/truncation controls in the Swift worker evidence tests. |
| `applied_profile` | [`PW_SHM_CAPTURE_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary: [`main`](../tests/suites/runner_abi_layout/capture.c) | Independently constructed object controls cover exact, excessive and unsupported captures. |
| `observed_path` | [`PW_SHM_OBSERVED_PATH_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | Source-inspected buffer use; no exact path-length behavior claim is tested. |
| `attempt_error` | [`PW_SHM_ERROR_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value: [`ABI_LIMITS`](../tests/suites/runner_abi_layout/limits.py); value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | Source-inspected bounded formatting; no exact error-text boundary claim is tested. |
| `helper_source` | [`MAX_SBPL_SOURCE_BYTES`](../controller/src/bin/sbpl-check.rs) | value: [`documented_helper_limits`](../controller/src/bin/sbpl-check.rs); path: [`mod tests`](../controller/src/bin/sbpl-check.rs) | Oversized input is tested through the shipped helper and fallback CLI; exact boundary behavior is source-inspected. |
| `helper_import_depth` | [`IMPORT_MAX_DEPTH`](../controller/src/bin/sbpl-check.rs) | value: [`documented_helper_limits`](../controller/src/bin/sbpl-check.rs); path: [`mod tests`](../controller/src/bin/sbpl-check.rs) | Deep import-chain control in the helper unit tests. |
| `helper_import_count` | [`IMPORT_MAX_COUNT`](../controller/src/bin/sbpl-check.rs) | value: [`documented_helper_limits`](../controller/src/bin/sbpl-check.rs); path: [`mod tests`](../controller/src/bin/sbpl-check.rs) | Import-count exhaustion control in the helper unit tests. |
| `observer_stream_text` | [`MAX_CAPTURE_BYTES`](../controller/src/bin/sandbox-log-observer.rs) | value: [`documented_observer_limits`](../controller/src/bin/sandbox-log-observer.rs) | Compiled value agreement is tested. Streaming accumulation and overflow behavior are source-inspected. |

<!-- END GENERATED LIMIT COVERAGE -->

## Maintaining this document

Edit [limits.json](limits.json), then run `python3 docs/generate_limits.py` from
the repository root. The same command copies the marked shared section into
[PolicyWitness.md](PolicyWitness.md); edit its explanations here. Review the
handwritten explanations as well as the tables.
The JSON is a reviewed description; production code does not load it.

`python3 docs/generate_limits.py --check` verifies the manifest's shape, source
and check references, generated text in both documents, and the guide's internal
links. The copied section must contain every limit and require no companion
files or web pages. `--stage-guide PATH` performs the same checks before copying
the guide; it refuses stale documents without regenerating them. The build
checks freshness before compilation and stages the guide before packaging.

These checks cannot establish implementation agreement by themselves.
`source_drift` exercises invalid and stale inputs, copying and staging, a
standalone guide, and refusal to build with stale documentation.
`runner_abi_layout` compares
compiled C values and exercises native query boundaries; `runner_unit` checks
compiled Swift values/defaults and rejected-frame capture. Rust unit tests check
controller and helper constants. Existing behavioral suites remain independent
of the manifest, so changing a documented number cannot change their oracles.

For a limit change, run `cargo test --manifest-path controller/Cargo.toml` and
`tests/run.sh --suite source_drift --suite runner_abi_layout --suite runner_unit
--suite runner_c_worker_harness --suite failure_boundaries` against a normal
signed build, plus the affected behavior owners named above. New entries need
an implementation-value check and an honest coverage note; a link to source is
not enough. Do not label a shortened timeout control as a test of the production
duration, or a constant comparison as proof of its operational consequences.

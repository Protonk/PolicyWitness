# PolicyWitness limits

<!-- BEGIN SHARED LIMITS -->
A profile accepted by `libsandbox` can still exceed PolicyWitness's input
capacities, exhaust an execution budget, or produce more evidence than a reply
can carry. These are PolicyWitness limits, not claims about the sandbox language
or proof that the sandbox denied an operation. This inventory covers specimen
admission, execution, comparison transport and retained evidence; it does not
enumerate every input-format rule, OS resource limit, runner-management budget
or release-tool deadline.

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
- The controller collects subprocess output before retaining a bounded prefix.
  Its output cap does not bound peak memory. A valid raw compiled-object capture
  can exceed that cap after base64 encoding and envelope overhead, leaving the
  controller unable to parse the runner reply. Even smaller captures share the
  reply with all other evidence; there is no independently guaranteed safe size.
- Probe query JSON has a wire-size limit independent of attempt-target admission.
  A long operation or filter value can lose its prediction while the attempted
  operation still runs. JSON escaping contributes to the query size.
- Applying a policy does not establish that it permits the worker's reporting
  or probe operations. Unsupported attempt kinds, invalid request shapes, native
  library availability and OS failures can also prevent useful results.

<!-- BEGIN GENERATED LIMITS -->

Values are maxima unless labelled as defaults.

## Specimen admission

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Policy source (`policy_source`) | 262,143 UTF-8 bytes | Final SBPL source after augments; excludes terminating NUL. Imported file contents are not added to this count. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Probe steps (`probe_steps`) | 256 items | Entries in probe_plan. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Policy parameters (`policy_parameters`) | 1,024 items | Entries in the policy parameter dictionary. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Step ID (`step_id`) | 63 UTF-8 bytes | Each step_id, excluding terminating NUL. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Attempt target (`attempt_target`) | 511 UTF-8 bytes | Each attempt target (path, service or sysctl name), excluding terminating NUL. Also the exec argv[0]. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Supplied exec arguments (`exec_arguments`) | 15 items | Arguments supplied in attempt.args; the target occupies the additional argv[0] slot. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Each supplied exec argument (`exec_argument`) | 127 UTF-8 bytes | Each supplied argument, excluding terminating NUL; the target has its own larger limit. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Parameter key (`parameter_key`) | 127 UTF-8 bytes | Each key, excluding terminating NUL. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |
| Parameter value (`parameter_value`) | 383 UTF-8 bytes | Each value, excluding terminating NUL. Excess rejects the specimen before worker launch: bad_request with host-owned admission_failure. | Fixed; no public override. |

## Execution budgets

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Worker readiness hint wait (`worker_ready_wait`) | 1,000 milliseconds | Initial ready-byte polling budget. Expiry alone does not abort: the host still checks shared-memory publication. | Production default; test-only controls are not a public tuning interface. |
| Worker publication wait (`worker_sentinel_wait`) | 60,000 milliseconds | Nominal polling budget for worker sentinels. Synchronous validator work is outside this budget. Expiry can trigger worker cleanup and runner_timeout with partial evidence. | Production default; test-only controls are not a public tuning interface. |
| Worker exit grace (`worker_exit_grace`) | 1,000 milliseconds | Polling grace after the host requests exit. Expiry triggers a SIGKILL attempt, then reaping. Kill/reap failures remain reported. | Production default; test-only controls are not a public tuning interface. |
| Validator I/O deadline (`validator_io_wait`) | 30,000 milliseconds | Elapsed deadline for nonblocking probe writes and verdict reads. Retains received verdicts and records an I/O timeout; cleanup follows. | Production default; test-only controls are not a public tuning interface. |
| Validator exit grace (`validator_exit_grace`) | 1,000 milliseconds | Polling grace after closing validator pipes. Expiry triggers a SIGKILL attempt, then reaping; failures remain reported. | Production default; test-only controls are not a public tuning interface. |
| Exec child deadline (`exec_child_wait`) | 10,000 milliseconds | Per-exec child observation deadline after successful spawn. Worker attempts to kill/reap the child; the step records that the deadline fired. | Production default; test-only controls are not a public tuning interface. |
| Runner RPC wait (`client_rpc_wait`) | 240,000 milliseconds | Client wait for the runner reply. An expired wait yields runner_timeout; it does not expand the inner worker or validator budgets. | Default; --timeout-ms changes only this wait and floors its value at 1 ms. |

## Queries and transport

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Validator query payload (`validator_query_payload`) | 65,534 bytes | Serialized JSON bytes for one probe, before the LF delimiter. Escaping counts. The 65536-byte fgets buffer reserves space for LF and NUL. An overlong line produces one parse_error with no step ID; that prediction is unavailable. Later lines can still be processed. | Fixed; no public override. |
| Controller subprocess output (`controller_output`) | 1,048,576 bytes | Per stdout or stderr stream captured from the runner client, policy helper or log observer. Byte prefix before lossy text decoding; not an envelope-wide cap. Output beyond the prefix is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Fixed; no public override. |
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
| `worker_ready_wait` | [`CWorkerInput`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | Normal readiness is tested; expiry without aborting is source-inspected. |
| `worker_sentinel_wait` | [`timeoutMsForCWorker`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | Deadline and partial-publication paths use shortened test budgets; the production duration is source-inspected. |
| `worker_exit_grace` | [`CWorkerInput`](../runner/Sources/PWRunnerCore/CWorker.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) | Deadline/cleanup paths use controlled children; the production duration is source-inspected. |
| `validator_io_wait` | [`ValidatorClientInput`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runValidatorEvidenceTests`](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift) | I/O deadline and partial-evidence paths use shortened budgets; the production duration is source-inspected. |
| `validator_exit_grace` | [`ValidatorClientInput`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path: [`runValidatorEvidenceTests`](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift) | Cleanup paths use controlled children; the production duration is source-inspected. |
| `exec_child_wait` | [`PW_EXEC_CHILD_DEADLINE_MS_DEFAULT`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value: [`NATIVE_LIMITS`](../tests/suites/runner_abi_layout/limits.py); path: [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | Shortened deadline and cleanup controls; the production duration is source-inspected. |
| `client_rpc_wait` | [`DEFAULT_TIMEOUT_MS`](../controller/src/run_flow.rs); [`defaultClientTimeoutMs`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`defaultClientTimeoutMs`](../runner/Clients/PWRunnerClient/main.swift) | value: [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value: [`documented_controller_limits`](../controller/src/run_flow.rs) | The production wait and timeout response are source-inspected; compiled default agreement is tested. |
| `validator_query_payload` | [`LINE_MAX_BYTES`](../controller/tools/sb_api_validator/sb_api_validator.c); [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value: [`NATIVE_LIMITS`](../tests/suites/runner_abi_layout/limits.py); boundary: [`query_boundary`](../tests/suites/runner_abi_layout/limits.py); path: [`validator_overlong_request`](../tests/suites/failure_boundaries/check.py) | Exact payload boundary and over-limit drain/recovery controls in the native validator; overlong input also goes through the CLI. |
| `controller_output` | [`MAX_CAPTURE_BYTES`](../controller/src/utils.rs) | value: [`documented_controller_limits`](../controller/src/run_flow.rs); path: [`mod tests`](../controller/src/runner_client.rs) | Exact prefix and truncation-boundary controls. Collection buffers the entire stream first; this is not a memory limit. |
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

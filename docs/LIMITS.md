# PolicyWitness limits

<!-- BEGIN SHARED LIMITS -->
A specimen that `libsandbox` would compile can still be refused here, or run
with less evidence than it produced. This section lists every such limit with
its value, what it counts and what happens at the boundary.

Capacity refusals carry `data.runner_result.admission_failure`, which names the
`field`, the `actual` count, the `maximum` and the `unit`, with location details
where available and `origin: "runner_host"`. Find that field in the "Refusal
names" column of the Specimen admission table; the row says what was measured
and which location fields are reported. To check a specimen before submitting
it, compare it with the same rows.

Request files must be UTF-8 JSON. A file containing invalid UTF-8 yields exit
code 2 and `result.normalized_outcome: "tool_error"`, with an error beginning
`failed to read request.json` and `data.runner_result: null`. It has no
`admission_failure` to look up.

## How to read the tables

- Capacities are inclusive maxima unless the row says otherwise: a 63-byte
  step ID fits, a 64-byte one exceeds its limit. UTF-8 counts measure decoded
  strings rather than JSON escapes or characters. Rows labeled `bytes` specify
  whether they count raw output, bytecode or a calculated allowance. String
  capacities exclude any terminating NUL.
- Time rows distinguish defaults, elapsed monotonic deadlines, nominal waits
  and unenforced allowances. Monotonic deadlines are unaffected by wall-clock
  adjustments. Nominal waits can take longer than their listed duration; each
  row describes what expiry does.
- The Control column describes `policy-witness` flags using four words.
  "Fixed" means no flag changes the value in this build. "Flag" names the flag
  that does. "Derived" means the value follows from another row.
  "Not enforced" means the number is informative.
- Specimen admission answers whether a specimen fits this build's capacities
  and why one did not. A capacity refusal names one field, has empty `steps`
  and carries no worker or validator subprocess record. PolicyWitness never
  truncates a plan to fit.
- Execution budgets describe waits and deadlines within a run. Some expiries
  lead to cleanup or missing results; the readiness hint can expire while the
  run continues. The nominal release margin has no expiry of its own.
- Queries and transport describe query sizes and received output. The rows
  identify rejected queries, truncated output and unavailable parsing or
  correlation. Truncated JSON is not parsed as a complete reply.
- Evidence capture bounds optional evidence: deny-log records, child output and
  compiled-object receipts. Excess can retain a prefix with a truncation marker
  or make capture or correlation unavailable, as the row describes. Attempt
  status and `sandbox_check` verdicts are unchanged by these evidence limits.
- Diagnostic helpers lists the limits of `sbpl-check`, which runs only after an
  XPC error, and of the log observer's streaming mode. Neither is the normal
  admission path, and the helper's import inventory does not control how
  `libsandbox` resolves or compiles imports.

<!-- BEGIN GENERATED LIMITS -->

## Specimen admission

| Limit | Value | Refusal names | Counting and consequence | Control |
| --- | --- | --- | --- | --- |
| Policy source (`policy_source`) | 262,143 UTF-8 bytes | `policy.sbpl_source` | Final SBPL source after augments. Imported file contents are not added to this count. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Probe steps (`probe_steps`) | 256 items | `probe_plan` | Entries in `probe_plan`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Policy parameters (`policy_parameters`) | 1,024 items | `policy.params` | Entries in `policy.params`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Step ID (`step_id`) | 63 UTF-8 bytes | `step_id`, with `step_index` | Each `step_id`. A refused ID is identified by `step_index` and is never echoed. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Attempt target (`attempt_target`) | 511 UTF-8 bytes | `target`, with `step_id` and `step_index` | Each attempt target (path, service or sysctl name). For exec, this is also argument zero. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Supplied exec arguments (`exec_arguments`) | 15 items | `args` with unit `items`, with `step_id` and `step_index` | Arguments supplied in `attempt.args`; the exec target is the additional argument zero. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Each supplied exec argument (`exec_argument`) | 127 UTF-8 bytes | `args` with unit `utf8_bytes`, with `index`, `step_id` and `step_index` | Each supplied exec argument; the target has its own larger limit. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Parameter key (`parameter_key`) | 127 UTF-8 bytes | `key` | Each parameter key. A refused key is identified by field and byte count and is never echoed. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Parameter value (`parameter_value`) | 383 UTF-8 bytes | `value`, with `parameter_key` | Each parameter value. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Query operation (`query_operation`) | 127 UTF-8 bytes | `sandbox_check.operation`, with `step_id` and `step_index` | Each `sandbox_check.operation`, also echoed per step in the reply. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Query filter value (`query_filter_value`) | 511 UTF-8 bytes | `sandbox_check.filter.value`, with `step_id` and `step_index` | Each `sandbox_check.filter.value` when present, including for `none` and unrecognized filter kinds. The query value and attempt target are counted separately, even when they name different paths. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Probe filter and attempt labels (`probe_plan_label`) | 127 UTF-8 bytes | `sandbox_check.filter.kind`, `attempt.kind` or `attempt.action`, with `step_id` and `step_index` | Each `sandbox_check.filter.kind`, `attempt.kind` and `attempt.action`. Unknown labels within the capacity still receive a meaning refusal. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Specimen ID (`specimen_id`) | 255 UTF-8 bytes | `specimen_id` | The `specimen_id` string. Echoed once per reply; a refused ID is replaced by `<admission_refused>`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Request labels (`request_label`) | 63 UTF-8 bytes | `run_kind` or `policy.format` | Each of `run_kind` and `policy.format`. A refused `run_kind` is omitted and a refused format reads `unknown`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Test-seam executable paths (`test_override_path`) | 1,023 UTF-8 bytes | `_test_overrides.worker_executable_path` or `_test_overrides.validator_executable_path` | Each of `_test_overrides.worker_executable_path` and `_test_overrides.validator_executable_path`. Every path that fails byte or NUL admission is omitted from a refusal's `test_overrides`, even when another field is refused first. Excess returns `bad_request` with `admission_failure`. | Fixed. |

## Execution budgets

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Worker policy delivery (`worker_policy_transfer`) | 5,000 milliseconds | One absolute monotonic deadline starting immediately after spawn; partial writes and interrupted calls do not restart it. Expiry closes the input pipe and enters host cleanup with policy_transfer_timeout and policy_transfer_deadline; no write errno is invented. | Fixed; internal driver controls may shorten it. |
| Worker readiness hint wait (`worker_ready_wait`) | 1,000 milliseconds | Nominal wait for the worker readiness hint. Expiry can leave `runner_subprocess.ready_byte_received: false` while the run continues. | Fixed. |
| Worker publication wait (`worker_sentinel_wait`) | 120,000 milliseconds | Nominal wait for worker results after the readiness-hint wait. Validator collection is outside this allowance; the listed duration is not a total runtime limit. Expiry can yield `runner_timeout` with partial evidence and reported cleanup results. | Fixed. |
| Worker exit grace (`worker_exit_grace`) | 1,000 milliseconds | Nominal wait for worker exit after an exit request. Expiry requests `SIGKILL`. Termination and reap failures remain reported. | Fixed. |
| Worker release wait (`worker_proceed_wait`) | 60,000 milliseconds | Elapsed monotonic deadline for worker release after successful policy application. Expiry or clock failure records a proceed failure with no attempts. | Fixed. |
| Nominal release margin (`validator_release_margin`) | 5,000 milliseconds | Informative allowance between the validator budgets and worker release wait. No separate timeout or refusal occurs at this value. | Not enforced; no flag. |
| Validator I/O test override floor (`validator_io_override_floor`) | 50 milliseconds | Minimum effective `_test_overrides.validator_io_timeout_ms`. Smaller supplied values use 50 ms; there is no ceiling. The reply mirrors the supplied value. This changes only the validator I/O deadline; a longer value can outlast `worker_proceed_wait` without restoring expired attempts. | Fixed. |
| Validator I/O deadline (`validator_io_wait`) | 30,000 milliseconds | Default elapsed monotonic deadline for validator query delivery and verdict collection. Received verdicts survive an I/O timeout; cleanup results remain reported. | Fixed. |
| Validator exit grace (`validator_exit_grace`) | 1,000 milliseconds | Nominal wait for validator exit after collection closes. Expiry requests `SIGKILL`. Termination and reap failures remain reported. | Fixed. |
| Exec child deadline (`exec_child_wait`) | 10,000 milliseconds | Elapsed monotonic deadline after successful spawn, limited by the remaining `exec_attempt_budget`. Expiry fails the attempt while preserving any observed natural exit code. Cleanup results remain reported; an observed leader exit does not establish that every descendant stopped. | Fixed. |
| Exec attempt budget (`exec_attempt_budget`) | 115,000 milliseconds | Elapsed monotonic budget shared by exec steps, including worker setup and intervening work but excluding the worker release wait. Exhaustion refuses a later spawn with `exec_failed` and `ETIMEDOUT`, no `child_pid` and no sandbox attribution. A clock failure refuses spawn or leaves an observation error after spawn. Blocking spawn and non-exec operations may outlast this allowance. | Fixed. |
| Exec child reap grace (`exec_reap_grace`) | 1,000 milliseconds | Elapsed monotonic allowance to confirm an exec child's exit after observation ends. Expiry, clock failure or a wait error leaves reaping unconfirmed and supplies no invented exit status. Failed group termination leaves only an immediate exit check. This is not a total cleanup runtime limit. | Fixed. |
| Runner RPC wait (`client_rpc_wait`) | 240,000 milliseconds | Default wait for the runner reply. The reply records the actual span as `data.runner_client.started_at_unix_ms` and `ended_at_unix_ms`. An expired wait yields `xpc_timeout`; it does not expand the inner worker or validator budgets. | Flag `--timeout-ms`, floored at 1 ms; values above this default are permitted. |
| Runner removal teardown wait (`runner_remove_teardown_wait`) | 1,000 milliseconds | Nominal wait for a removed BYOXPC service to disappear from launchd. The cleanup observation records the service checks and the wait. A service still listed at expiry retains its cleanup record with a warning; a later `runner remove` or `runner reconcile` continues recovery. | Fixed. No wait when the removal issued no bootout. |
| External runner respawn throttle (`byoxpc_throttle_interval`) | 1 seconds | `ThrottleInterval` in every launchd plist that `runner install` generates. The host exits after each specimen and launchd starts the job at most once per interval; the wait is counted from the previous launch, not from the previous exit. A request to an installed external runner that arrives within the interval of the previous launch waits for the remainder before a host serves it. Without the key launchd applies its ten-second default. A request that reaches a host which is still retiring after its reply meets that host's `already_ran`; the interval does not change that. | Fixed in the generated plist. An installed plist can be edited by hand after `runner remove` and a fresh install; the registry's plist hash then differs and removal reports the ownership disagreement. |

## Queries and transport

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Validator query payload (`validator_query_payload`) | 65,534 bytes | Serialized JSON bytes for one validator probe, excluding the final LF. JSON escapes count toward this size. An overlong line produces one `parse_error` without a step ID; later lines remain usable. Admitted specimens stay below this limit. | Fixed. |
| Informative reply size bound (`runner_reply_maximum`) | 24,825,461 bytes | Upper bound on the encoded size of one runner JSON reply for this build. No reply is refused at this size; retained output is bounded by `controller_output`. | Not enforced; it sizes `controller_output`. |
| Runner client output (`controller_output`) | 75,497,472 bytes | Captured bytes per stdout or stderr stream from the runner client, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Derived: three times `runner_reply_maximum`, rounded up to a whole 4 MiB; no flag. |
| Log observer stdout (`log_observer_output`) | 33,554,432 bytes | Raw observer stdout bytes, including the JSON report and final newline. Stderr has a separate cap. Overflow retains a bounded raw prefix, with unavailable parsing and correlation. | Fixed. |
| Log show stdout (`log_show_stdout`) | 1,048,576 bytes | Raw bytes from `log show` stdout, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Log show stderr (`log_show_stderr`) | 131,072 bytes | Raw bytes from `log show` stderr, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Log observer stderr (`log_observer_stderr`) | 131,072 bytes | Raw bytes from observer stderr, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Observer JSON structure (`log_reply_structure`) | 262,144 items | Opening object/array delimiters, commas and colons outside quoted strings in the observer reply. Excess retains bounded raw diagnostic text with unavailable parsing and correlation. | Fixed. |
| Observer echoed metadata (`log_observer_metadata`) | 4,096 UTF-8 bytes | Each echoed show argument: predicate, process name, start, end, last, plan, row and correlation ID. Oversized arguments are rejected; oversized reply metadata leaves correlation unavailable. | Fixed. |
| Policy helper output (`policy_helper_output`) | 8,388,608 bytes | Captured bytes per stdout or stderr stream from `sbpl-check`, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Fixed. |
| Rejected validator frame context (`validator_fault_context`) | 256 bytes | Retained prefix of the first rejected validator frame, measured before base64 encoding. `frame_bytes`, `retained_bytes` and `context_truncated` describe how much context was retained. | Fixed. |

## Evidence capture

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Deny-log scan padding per endpoint (`log_window_pad`) | 2 seconds | Padding at each end of the runner client's span after rounding outward to whole seconds. The scan covers `floor(start) - 2 seconds` through `ceil(end) + 2 seconds`, including both pads. Raw client timestamps are unchanged; reversed endpoints prevent collection. | Fixed; `window.pad_seconds` records it. |
| Default log collection timeout (`log_collection_timeout`) | 10,000 milliseconds | Default elapsed monotonic allowance for log collection, including startup and processing. Actual costs appear in `data.sandbox_log_capture.supervision.elapsed_ms` and `observer.data.collection.elapsed_ms`. Expiry stops collection and starts the fixed cleanup grace; available diagnostics survive without associations. Standalone `show` uses the same default. | Flag `--log-timeout-ms`: a positive integer of milliseconds that fits a monotonic deadline plus the cleanup grace, validated before the runner starts even with `--no-log-capture`. |
| Log cleanup grace (`log_cleanup_grace`) | 1,000 milliseconds | Elapsed monotonic allowance for observing log-process cleanup after collection stops. Early failures start the grace immediately. The allowance expires no later than the original collection deadline plus this grace. Unconfirmed reaping or group absence is reported; retries never restart the allowance. | Fixed. |
| Log report reserve (`log_report_reserve`) | 1,000 milliseconds | Allowance withheld from the log query within `log_collection_timeout`. The observer's report can arrive after the query times out. Collection allowances at or below this reserve leave no query time. The reserve does not guarantee an intact report; interruption leaves bounded transport diagnostics. | Fixed; `supervision.reserve_ms` records 0 at the observer boundary and this value under `observer.data.collection`. |
| Parsed deny events (`log_deny_events`) | 8,192 records | Parsed deny events in show output and the derived controller array. An additional event makes capture incomplete and correlation unavailable; bounded raw output and available diagnostic events survive. | Fixed. |
| Candidate associations (`log_candidate_count`) | 4,096 items | Total event-to-step candidates, including ambiguous matches. Excess discards the whole derived association result and withholds correlation; retained events remain diagnostic. | Fixed. |
| Candidate allocation allowance (`log_candidate_bytes`) | 8,388,608 bytes | Total candidate charge: six times the sum of twice the step-ID byte length plus the path, operation, kind and action byte lengths, plus 1,024 bytes per candidate. Excess reports the `association_bytes` cutoff, discards associations and withholds correlation. | Fixed. |
| Steps admitted to correlation (`log_correlation_steps`) | 256 items | Each of the submitted plan and returned step arrays. Excess withholds log correlation; execution evidence is unchanged. | Fixed. |
| Exec child output per stream (`exec_stream`) | 1,023 bytes | Retained stdout or stderr bytes for each exec child. An overflow marker occupies part of this allowance. Excess output is not retained. | Fixed. |
| Primary worker diagnostic (`worker_diagnostic`) | 4,095 bytes | Retained primary diagnostic bytes. The reply reports retained length and truncation state; this is not a complete transcript. | Fixed. |
| Optional compiled-object capture (`applied_profile`) | 1,048,576 bytes | Raw bytecode bytes in an optional compiled-object receipt, before base64 encoding. Oversized or unsupported objects leave capture unavailable without preventing policy application. | Fixed. |
| Worker observed path (`observed_path`) | 1,023 bytes | Retained bytes in each worker-observed path. Path observation can be absent or bounded; a host-side path diagnostic is a separate observation. | Fixed. |
| Worker attempt error text (`attempt_error`) | 255 bytes | Retained bytes in each worker attempt error message. Error text is bounded; structured result and status fields remain separate. | Fixed. |

## Diagnostic helpers

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| sbpl-check source admission (`helper_source`) | 4,194,304 bytes | Top-level source bytes read by the diagnostic helper; not the runner policy cap. policy_too_large with null compile and import_inventory groups; no compile verdict. | Fixed. |
| sbpl-check import inventory depth (`helper_import_depth`) | 8 levels | Import depth in the helper inventory, starting at 0. Depth 8 is the first depth replaced by a depth-limit diagnostic. The affected branch stops and `import_inventory.truncated` is set. This does not limit compilation of imports. | Fixed. |
| sbpl-check import inventory count (`helper_import_count`) | 64 records | Import-inventory records, including unresolved and error records. Repeated files or names are listed once. Further inventory stops and `import_inventory.truncated` is set. This does not limit compilation of imports. | Fixed. |
| Log observer stream text (`observer_stream_text`) | 1,048,576 bytes | Streaming helper mode only (`--duration` or `--follow`): retained nonempty log lines after the prelude, with one LF per line. Only whole lines that fit are retained. The first overflowing line sets `log_truncated` and ends text retention. Deny-event arrays and JSONL emission continue. The normal CLI log-show path does not use this cap. | Fixed. `--no-log-capture` disables the CLI's log collection, not this helper mode. |

<!-- END GENERATED LIMITS -->

## Interactions that matter

- Budgets nest, and one flag changes one of them. `--timeout-ms` sets
  `client_rpc_wait`, which bounds only the client's wait. The worker polling
  window `worker_sentinel_wait`, the validator deadline `validator_io_wait`,
  the release wait `worker_proceed_wait` and the exec budgets keep their own
  values, so no number here is an end-to-end runtime. The reply records the
  client span in `data.runner_client.started_at_unix_ms` and
  `ended_at_unix_ms`; an expired client wait yields `xpc_timeout`.
- Output budgets mark, they never silently cut. Each receiver reports the
  budget it applied in `capture_limit_bytes` (`controller_output`,
  `policy_helper_output`). Output beyond it is marked truncated, and a
  truncated JSON stream is not parsed as a reply.
- Log limits change evidence only. The byte caps on `log show` and the
  observer (`log_show_stdout`, `log_show_stderr`, `log_observer_output`,
  `log_observer_stderr`) and the event and candidate counts (`log_deny_events`,
  `log_candidate_count`, `log_candidate_bytes`) are fixed; when one is
  exceeded, the capture keeps a bounded prefix and withholds correlation.
  `--log-timeout-ms` changes only the time allowance, `log_collection_timeout`.
  Attempt results and `sandbox_check` verdicts never change because of a log
  limit, and the plan's step count does not bound how much the OS log holds.
- One refusal names the first failing field. When a specimen exceeds several
  admission limits, the order is: top-level metadata (`specimen_id`,
  `request_label`) and `test_override_path` executable overrides, then plan
  and parameter counts (`probe_steps`, `policy_parameters`), then worker strings
  (`policy_source`, `step_id`, `attempt_target`, exec arguments, parameter keys
  and values), then host query
  fields (`query_operation`, `query_filter_value`, `probe_plan_label`). A
  refused value is never echoed shortened: an oversized `specimen_id` is
  replaced by `<admission_refused>`, an oversized `run_kind` is omitted and an
  oversized `policy.format` reads `unknown`.
- The `policy_source`, `parameter_key`, `parameter_value`, `step_id`,
  `attempt_target`, `exec_argument`, `query_operation`, `query_filter_value`
  and `test_override_path` limits also reject embedded NUL. For a string within
  its byte capacity, that refusal reports unit `nul_bytes`, maximum 0 and the
  same field. Metadata and labels (`specimen_id`, `request_label`,
  `probe_plan_label`) permit escaped NUL at this gate; their
  normal meaning rules still apply. Within the capacities above, other control
  characters and valid Unicode survive request transport unchanged.
- Exec steps share a budget and each child has a deadline. `exec_attempt_budget`
  bounds all exec steps of a plan together and `exec_child_wait` bounds each
  child; neither has a flag. A step the exhausted budget refuses reports
  `exec_failed` with `ETIMEDOUT`, no `child_pid` and no sandbox attribution. A
  child cut by its deadline fails the attempt but keeps any exit code that was
  observed. A worker that dies first leaves the step's exec details
  unpublished, which establishes neither that no child spawned nor that cleanup
  succeeded.
- What the deny-log capture covers. The requested window is the runner
  client's own span, rounded outward to whole seconds and padded by
  `log_window_pad` at each end; `window.start`, `window.end` and
  `window.pad_seconds` record it, and reversed wall-clock endpoints prevent the
  scan. Captured records name the worker's process name and PID. Denials inside
  exec children and prediction queries contribute no captured records. A
  missing record never establishes that an operation was allowed.
<!-- END SHARED LIMITS -->

See the [user guide](PolicyWitness.md) for the request and response contracts.
Tables are generated from [limits.json](limits.json).

<!-- BEGIN GENERATED LIMIT COVERAGE -->

## Grounding and coverage

Value checks compare the inventory with compiled constants, constructed defaults or actual returned bytes. Boundary checks exercise a limit and its consequence; path checks cover related behavior without proving the exact boundary. A source reference alone is not a value check. Coverage notes below identify where behavior remains source-inspected.

| Limit ID | Implementation | Permanent checks | Behavioral coverage |
| --- | --- | --- | --- |
| `policy_source` | [`PW_SHM_POLICY_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `probe_steps` | [`PW_SHM_MAX_STEPS`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `policy_parameters` | [`PW_SHM_MAX_PARAMS`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `step_id` | [`PW_SHM_STEP_ID_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `attempt_target` | [`PW_SHM_TARGET_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `exec_arguments` | [`PW_SHM_MAX_ARGV`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `exec_argument` | [`PW_SHM_ARGV_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `parameter_key` | [`PW_SHM_PARAM_KEY_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `parameter_value` | [`PW_SHM_PARAM_VALUE_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py) | At-limit, over-limit and multibyte admission controls through the CLI. |
| `query_operation` | [`sandboxCheckOperationMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`queryAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Host-only: the string goes to the validator line and is echoed per step in the reply; it never enters shared memory. At-limit, over-limit and multibyte admission controls through the CLI; constructed orchestrator controls refuse before any process work and cover every filter kind. |
| `query_filter_value` | [`sandboxCheckFilterValueMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`queryAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | At-limit, over-limit and multibyte admission controls through the CLI; constructed orchestrator controls refuse before any process work and cover every filter kind. |
| `probe_plan_label` | [`probePlanLabelMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`queryAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Exact, over-limit and multibyte boundaries through the CLI; 256-step oversized-label regressions require a small refusal and unchanged write targets. |
| `specimen_id` | [`specimenIdMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`requestAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; the refusal reply never contains the refused string. |
| `request_label` | [`requestLabelMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`requestAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; an at-limit format passes capacity admission and fails meaning validation as bad_request. |
| `test_override_path` | [`testOverridePathMaxBytes`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`requestAdmissionFailure`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift) | Override paths are mirrored in test_overrides and named in dlopen and spawn diagnostics; each invalid path is independently dropped from a refusal mirror. Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; at-limit nonexistent paths pass admission and reach their own seam failures. |
| `worker_policy_transfer` | [`CWorkerInput.defaultPolicyTransferTimeoutMs`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runPolicyTransferTests`](../runner/Tests/PWRunnerCoreTests/PolicyTransferTests.swift) | Real stalled and draining pipes plus deterministic interrupted, partial and zero-progress writes. Readiness wait starts only after successful delivery. The production budget fits within the default client wait; a shorter client override is independent and does not cancel the host. |
| `worker_ready_wait` | [`CWorkerInput`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | runCWorker counts ready-byte polling iterations, then checks shared-memory publication even if the hint was not received. Normal readiness is tested; expiry without aborting is source-inspected. |
| `worker_sentinel_wait` | [`timeoutMsForCWorker`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | runCWorker counts polling iterations until done. Policy transfer precedes polling; synchronous validator work is outside the count, and scheduler delays add time. The worker uses a separate local active-time exec budget, configured below this window without an end-to-end guarantee. Deadline and partial-publication paths use shortened test budgets; the production duration is source-inspected. |
| `worker_exit_grace` | [`CWorkerInput`](../runner/Sources/PWRunnerCore/CWorker.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) | runCWorker counts polling iterations after storing exit_requested, then attempts SIGKILL and reaping. Deadline/cleanup paths use controlled children; the production duration is source-inspected. |
| `worker_proceed_wait` | [`PW_PROCEED_WAIT_MS_DEFAULT`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); path (control): [`main`](../tests/suites/runner_c_worker_harness/harness.c); path (test): [`runOrderingTests`](../runner/Tests/PWRunnerCoreTests/OrderingTests.swift) | wait_for_proceed uses CLOCK_MONOTONIC before acknowledging host release. Failure publishes done, then the exit-request spin can outlive a dead host. Short-budget, delayed-release, clock-failure and delayed-cleanup controls establish fail-closed behavior; production duration is value-checked. |
| `validator_release_margin` | [`validatorReleaseMarginMs`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | validatorReleaseMarginMs allows for host observation, setup, decoding and scheduling. Production defaults satisfy 60000 > 30000 + 1000 + 5000. This configuration guard excludes test overrides and does not bound final blocking reap, host descheduling, prompt replies or eventual orphan cleanup. Short-budget, delayed-release, clock-failure and delayed-cleanup controls establish fail-closed behavior; production duration is value-checked. |
| `validator_io_override_floor` | [`timeoutMsForValidator`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | Short-budget, delayed-release, clock-failure and delayed-cleanup controls establish fail-closed behavior; production duration is value-checked. |
| `validator_io_wait` | [`ValidatorClientInput`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runValidatorEvidenceTests`](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift) | runValidator uses a CLOCK_MONOTONIC deadline for nonblocking probe writes and verdict reads; wall-clock changes cannot extend it. The `_test_overrides.validator_io_timeout_ms` test seam replaces this deadline, floored at 50 ms without a ceiling and mirrored in results; production has no flag. I/O deadline and partial-evidence paths use shortened budgets; the production duration is source-inspected. |
| `validator_exit_grace` | [`ValidatorClientInput`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runValidatorEvidenceTests`](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift) | runValidator closes the validator pipes and counts exit-grace polling iterations before attempting SIGKILL and reaping. Cleanup paths use controlled children; the production duration is source-inspected. |
| `exec_child_wait` | [`PW_EXEC_CHILD_DEADLINE_MS_DEFAULT`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); path (test): [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | The absolute child deadline and local exec plan cutoff are compared without restarting the plan budget after spawn. EOF and child exit are observed separately. Deadline or observation failure requests process-group termination while the leader is still owned, even after leader exit. Live controls close streams while both processes remain alive and exit the leader while a descendant retains streams. Independent socket credentials, OS exit events and file effects establish the behavior. |
| `exec_attempt_budget` | [`PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`attempt_budget_start`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`exec_attempt_budget_remainder`](../tests/suites/runner_c_worker_harness/run.sh) | attempt_budget_start runs before worker setup; attempt_budget_exclude removes only the interval returned by the release barrier. Exec attempts receive an absolute cutoff independent of the host polling clock. Clock failure after spawn triggers cleanup. Blocking spawn and non-exec operations are not preemptible here. The production default sits a nominal 5,000 ms below worker_sentinel_wait; test equipment may shorten it independently and the specimen worker_timeout_ms override does not move it. Compiled values agree with the host configuration. Deterministic native controls vary spawn latency, release exclusion, intervening work, exact exhaustion, clock failures and cleanup. Real short-budget plans preserve completed prefix and trailing file effects through host assembly and serialization. |
| `exec_reap_grace` | [`PW_EXEC_REAP_GRACE_MS`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); boundary (control): [`main`](../tests/fixtures/worker_lifecycle/exec_control.c) | Final reaping uses nonblocking waitpid in a local monotonic observation window. Failed group termination permits only an immediate nonblocking reap. The allowance does not bound native syscall duration or host descheduling. Controlled pending/EINTR waits exhaust the grace; kill, wait and clock failures retain missing status. Every wait is required to be nonblocking. |
| `client_rpc_wait` | [`DEFAULT_TIMEOUT_MS`](../controller/src/run_flow.rs); [`defaultClientTimeoutMs`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`defaultClientTimeoutMs`](../runner/Clients/PWRunnerClient/main.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`documented_controller_limits`](../controller/src/run_flow.rs) | The production wait and timeout response are source-inspected; compiled default agreement is tested. |
| `runner_remove_teardown_wait` | [`TEARDOWN_WAIT_MS`](../controller/src/runner_manager.rs) | value (test): [`documented_removal_limits`](../controller/src/runner_manager.rs); boundary (test): [`bootout_waits_out_launchd_teardown_within_the_budget`](../controller/src/runner_manager.rs) | After its own bootout, runner remove re-reads the service every 50 milliseconds until it is absent or the nominal allowance is spent. Controlled cleanup systems report the job present for two reads and then absent (completion after two waits), present for every read (retention after the whole allowance), and a skipped bootout (nothing awaited). The live removal cases observe real launchd teardown. |
| `byoxpc_throttle_interval` | [`BYOXPC_THROTTLE_INTERVAL_SECONDS`](../controller/src/runner_manager.rs) | value (test): [`documented_throttle_interval`](../controller/src/runner_manager.rs); boundary (test): [`byoxpc_plist_sets_the_respawn_throttle`](../controller/src/runner_manager.rs); boundary (test): [`single_use`](../tests/suites/runner_byoxpc/opt_in/single_use.sh) | Measured on one owned installation (macOS 14.8, user scope) with the plist rewritten per candidate: with no key a run 0.4 s after the previous one took about 10.3 s and a run after the install's own verify about 9.2 s; with the interval at one second those took about 1.3 s and 0.3 s. The single-use live case reads the installed plist's value and waits it out plus a margin before requiring a fresh host. |
| `validator_query_payload` | [`LINE_MAX_BYTES`](../controller/tools/sb_api_validator/sb_api_validator.c); [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); boundary (test): [`query_boundary`](../tests/suites/runner_abi_layout/limits.py); path (test): [`validator_overlong_request`](../tests/suites/failure_boundaries/check.py) | The fixed 65536-byte buffer allows a 65534-byte payload. The reader counts physical bytes, including raw NUL, and drains an overlong line. Admission bounds on operation and filter value keep a fully escaped probe line to a few KiB. Exact payload boundary, over-limit drain/recovery, valid raw and escaped Unicode, malformed escapes/UTF-8/raw controls and raw-NUL physical framing. Every rejected probe is followed by a valid recovery probe. |
| `runner_reply_maximum` | [`maximalReplyEncodedSize`](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift); [`pwRunnerEncodeJSON`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runReplyMaximumTests`](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift); path (test): [`main`](../tests/suites/witness_contract/check_max_target_reply.py) | Encoded size, through the production encoder, of the field-complete reply fixture with 256 steps, 256 validator records and disposition entries, every request- or host-derived string at its documented limit and made of U+0001 (six JSON bytes per byte), the largest worker diagnostic, and the largest slash-heavy compiled-profile receipt. An upper bound for the current response schema: fields that cannot co-occur in one run are all present. Composed host path strings allow 1,535 bytes for a resolved parent plus literal leaf and 1,043 bytes for a realpath plus the supported system firmlink prefix; runner_unit checks both expansions. Not enforced anywhere; it derives the runner client budget. A reply string key added to the fixture without a size classification fails runner_unit, so the number cannot silently fall behind the schema. runner_unit recomputes the number; edit the manifest when the synthesizer's value moves. The synthesizer's value is compared with the manifest; the budget relation is asserted; an injected unclassified key is detected. Live 256-step workloads are measured against this bound. |
| `controller_output` | [`RUNNER_CAPTURE_BYTES`](../controller/src/utils.rs) | value (test): [`documented_controller_limits`](../controller/src/run_flow.rs); path (test): [`valid_oversized_producer_is_receiver_loss_not_malformed_json`](../controller/src/runner_client.rs); path (test): [`main`](../tests/suites/witness_contract/check_max_target_reply.py) | The byte prefix precedes lossy text decoding. This is a per-stream retention budget, not an envelope-wide cap or a process-memory limit. runner_unit asserts the derivation against the compiled Rust constant's documented value. Exact prefix and truncation-boundary controls, including small arbitrary budgets and every cut within multibyte scalars. Collection buffers the entire stream first; this is not a memory limit. Five admitted 256-step CLI workloads at the admitted maxima, including the control-character exec workload with 511-byte targets and queries, 63-byte step IDs, maximal metadata and live profile capture, must each stay under runner_reply_maximum; the budget then holds a complete reply with a threefold margin by construction. |
| `log_observer_output` | [`OBSERVER_STDOUT_BYTES`](../controller/src/log_capture.rs) | value (test): [`documented_controller_limits`](../controller/src/run_flow.rs); boundary (test): [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs); boundary (test): [`inner_byte_limit_with_maximal_json_escaping_fits_outer_serialization_limit`](../controller/src/bin/sandbox-log-observer.rs); boundary (test): [`controlled_256_step_capture_keeps_every_long_target_candidate`](../controller/src/log_replay_tests.rs) | The cap is enforced while reading. One extra byte witnesses overflow; no JSON fragments are recovered from the retained prefix. Sized for bounded inner text, duplicated deny lines and parsed raw lines, six-byte JSON escaping, event metadata and reply metadata. Streaming cap controls cover both pipes. A 256-record corpus with 511-byte targets preserves all records and candidate references through parser, supervised receiver, assembly and consumer recovery under the production default allowance. Exact inner stdout/stderr caps with maximum escaping fit the bounded serializer. Interrupted or failed capture changes log evidence only; live volume has no bound derived from step count. |
| `log_show_stdout` | [`LOG_STDOUT_BYTES`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs) | Raw bytes read from log show stdout, already selected by the OS predicate, before PW decoding, parsing or PID filtering; enforced while reading. One extra byte witnesses overflow; only the budgeted prefix is retained. Both stream boundaries are tested at, below and above a substituted small cap, including concurrent stdout/stderr. Counts describe bytes actually read, never the unavailable remainder. |
| `log_show_stderr` | [`LOG_STDERR_BYTES`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs) | Raw bytes read from log show stderr, before decoding or parsing; enforced while reading. One extra byte witnesses overflow; only the budgeted prefix is retained. Both stream boundaries are tested at, below and above a substituted small cap, including concurrent stdout/stderr. Counts describe bytes actually read, never the unavailable remainder. |
| `log_observer_stderr` | [`OBSERVER_STDERR_BYTES`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs) | Raw bytes read from observer stderr, before decoding or parsing; enforced while reading. One extra byte witnesses overflow; only the budgeted prefix is retained. Both stream boundaries are tested at, below and above a substituted small cap, including concurrent stdout/stderr. Counts describe bytes actually read, never the unavailable remainder. |
| `log_window_pad` | [`LOG_WINDOW_PAD_SECONDS`](../controller/src/sandbox_log.rs) | value (test): [`documented_controller_limits`](../controller/src/run_flow.rs); boundary (test): [`run_span_window_floors_start_ceils_end_and_never_collapses`](../controller/src/sandbox_log.rs); boundary (test): [`requested_intervals_select_independently_timed_events`](../controller/src/sandbox_log.rs); boundary (test): [`padded_records_survive_assembly_and_consumer_recovery`](../controller/src/run_flow.rs) | The pad allows for differences between client wall-clock and archive event timestamps; it guarantees neither delivery nor coverage under every clock condition. Independent timestamp fixtures cover both padding regions, exact and exterior bounds, equal spans and rollback. Complete full, early-only, late-only and empty replies preserve eligible candidates and missing-record diagnostics through assembly, serialization and consumer recovery. |
| `log_collection_timeout` | [`DEFAULT_LOG_TIMEOUT_MS`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`larger_allowance_buys_time_only_and_still_bounds_hangs`](../controller/src/log_capture.rs) | The shared CLOCK_MONOTONIC allowance starts before observer launch and includes inner log show capture. The log child receives the allowance minus the report reserve. Independent slow-success and permanent-hang fixtures prove that a larger finite allowance buys waiting time only; shared absolute deadlines are not restarted by the observer. |
| `log_cleanup_grace` | [`CLEANUP_GRACE_MS`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); path (test): [`cleanup_failures_and_lost_ownership_remain_unconfirmed`](../controller/src/log_capture.rs) | Owned orphan controls cover leader death before reply, pipes open or closed, group absence, failed signalling/probing and lost ownership. The bound concerns supervised waiting, not OS scheduling. |
| `log_report_reserve` | [`LOG_REPORT_RESERVE_MS`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`inner_timeout_preserves_available_record_and_actual_child_wait`](../controller/src/bin/sandbox-log-observer.rs); boundary (test): [`timeout_override_changes_waiting_only_across_both_boundaries`](../controller/src/log_replay_tests.rs) | At the log show boundary the observer stops its log child this long before the controller deadline to allow reaping and report delivery. The controller deadline is unchanged; cleanup and scheduling can consume the reserve. A short inner allowance cuts off the log child while the observer's report, including its inner cutoff, still reaches the controller; a stalled query exhausts the reserved inner allowance and is reported the same way. |
| `log_deny_events` | [`MAX_DENY_EVENTS`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`event_limit_withholds_completion_without_discarding_retained_diagnostics`](../controller/src/bin/sandbox-log-observer.rs); boundary (test): [`maximum_event_volume_correlates_within_the_default_allowance`](../controller/src/sandbox_log.rs) | Exact and over-limit fixtures retain diagnostics and distinguish complete capture from overflow. The maximum event volume correlates against a 256-step plan inside the default collection allowance. |
| `log_candidate_count` | [`MAX_ASSOCIATIONS`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`derived_json_and_candidate_allocations_are_bounded`](../controller/src/sandbox_log.rs) | A 256-record unique-path control preserves all associations; repeated matching attempts exhaust the candidate budget. |
| `log_candidate_bytes` | [`MAX_ASSOCIATION_BYTES`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`derived_json_and_candidate_allocations_are_bounded`](../controller/src/sandbox_log.rs) | The charge is a conservative encoded/allocation allowance, not a measurement of peak process memory. Long repeated paths exercise the allocation allowance independently of the candidate count. This is a derived-data bound, not a peak-process-memory claim. |
| `log_correlation_steps` | [`MAX_CORRELATION_STEPS`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`derived_json_and_candidate_allocations_are_bounded`](../controller/src/sandbox_log.rs) | A 256-step control preserves unique candidates; over-limit arrays reject correlation. |
| `log_reply_structure` | [`MAX_OBSERVER_JSON_TOKENS`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); boundary (test): [`derived_json_and_candidate_allocations_are_bounded`](../controller/src/sandbox_log.rs) | The structural count is checked before allocating a JSON tree. Independent oversized JSON array trips the structural guard before Value allocation. |
| `log_observer_metadata` | [`MAX_OBSERVER_METADATA_BYTES`](../controller/src/log_capture.rs) | value (test): [`documented_collection_limits`](../controller/src/log_capture.rs); path (test): [`supervised_receiver_retains_failed_inner_evidence_and_rejects_bad_shapes`](../controller/src/sandbox_log.rs) | The observer rejects excess metadata before launching log show; the controller also rejects oversized reply metadata. Receiver malformed-shape controls cover excess metadata; direct argument admission is source-inspected. |
| `policy_helper_output` | [`HELPER_CAPTURE_BYTES`](../controller/src/utils.rs) | value (test): [`documented_controller_limits`](../controller/src/run_flow.rs); boundary (test): [`arbitrary_budgets_preserve_counts_at_every_unicode_cut`](../controller/src/utils.rs) | The byte prefix precedes lossy text decoding. This is a per-stream retention budget, not an envelope-wide cap or a process-memory limit. The shared receiver accepts an explicit per-stream retention budget for this producer; exact byte counts, truncation and JSON parse suppression are tested independently of the runner budget. |
| `validator_fault_context` | [`decodeValidatorFrames`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | Exact and over-limit invalid-frame context controls; no rejected bytes become verdicts. |
| `exec_stream` | [`PW_SHM_CHILD_OUTPUT_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runCWorkerTests`](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift) | Each text buffer reserves its terminating NUL outside this payload limit. Additional output is drained even after retention stops. Small stdout/stderr capture is tested. Overflow truncation and the exact retained-prefix/marker split are source-inspected. |
| `worker_diagnostic` | [`PW_SHM_DIAGNOSTIC_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runWorkerEvidenceTests`](../runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift) | The diagnostic buffer reserves its terminating NUL outside the payload limit. Bounded diagnostic/truncation controls in the Swift worker evidence tests. |
| `applied_profile` | [`PW_SHM_CAPTURE_BYTES`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (control): [`main`](../tests/suites/runner_abi_layout/capture.c) | Capture supports nonempty single-profile (type 0) objects; it runs before applying the same object. Failed capture leaves application unchanged. Independently constructed object controls cover exact, excessive and unsupported captures. |
| `observed_path` | [`PW_SHM_OBSERVED_PATH_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | The per-step C path-buffer payload excludes its terminating NUL. Source-inspected buffer use; no exact path-length behavior claim is tested. |
| `attempt_error` | [`PW_SHM_ERROR_MAX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | value (test): [`compare`](../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) | The per-step C error-buffer payload excludes its terminating NUL. Source-inspected bounded formatting; no exact error-text boundary claim is tested. |
| `helper_source` | [`MAX_SBPL_SOURCE_BYTES`](../controller/src/sbpl_imports.rs) | value (test): [`documented_helper_limits`](../controller/src/bin/sbpl-check.rs); path (test): [`source_byte_cap_counts_utf8_bytes_not_characters`](../controller/src/bin/sbpl-check.rs) | Oversized input is tested through the shipped helper and fallback CLI; exact boundary behavior is source-inspected. |
| `helper_import_depth` | [`IMPORT_MAX_DEPTH`](../controller/src/sbpl_imports.rs) | value (test): [`documented_helper_limits`](../controller/src/bin/sbpl-check.rs); path (test): [`resolve_imports_truncates_on_depth_cap`](../controller/src/sbpl_imports.rs) | At depth 8 the helper records a diagnostic instead of reading or expanding that file; libsandbox compilation has its own import resolution. Deep import-chain control in the helper unit tests. |
| `helper_import_count` | [`IMPORT_MAX_COUNT`](../controller/src/sbpl_imports.rs) | value (test): [`documented_helper_limits`](../controller/src/bin/sbpl-check.rs); path (test): [`resolve_imports_truncates_on_count_cap`](../controller/src/sbpl_imports.rs) | The helper traversal deduplicates visited files/names and accumulates at most this many records; libsandbox compilation does not use that inventory as a limit. Import-count exhaustion control in the helper unit tests. |
| `observer_stream_text` | [`MAX_CAPTURE_BYTES`](../controller/src/bin/sandbox-log-observer.rs) | value (test): [`documented_observer_limits`](../controller/src/bin/sandbox-log-observer.rs) | This bound covers streaming text accumulation only, not memory use or total report size. Compiled value agreement is tested. Streaming accumulation and overflow behavior are source-inspected. |

<!-- END GENERATED LIMIT COVERAGE -->

## Premises behind the interactions

The shared text above states only what a reader can observe in a reply. The
mechanisms those statements rest on live here, each beside the symbol that
implements it, so that a premise can be reopened when the platform changes.

- Reply and output budgets. `RUNNER_CAPTURE_BYTES`
  ([utils.rs](../controller/src/utils.rs)) is three times `runner_reply_maximum`
  rounded up to a whole 4 MiB. The maximum is synthesized by
  `maximalReplyEncodedSize`
  ([ReplyMaximumTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift))
  from the field-complete 256-step reply fixture encoded by
  `pwRunnerEncodeJSON`; it places fields that cannot co-occur side by side, so it
  is an upper bound for the schema, and a reply string key added without a size
  classification fails that test. Collection buffers the whole stream before
  applying a budget; the budgets are not memory limits.
- Log collection. `LOG_STDOUT_BYTES`, `LOG_STDERR_BYTES`,
  `OBSERVER_STDOUT_BYTES`, `OBSERVER_STDERR_BYTES`, `DEFAULT_LOG_TIMEOUT_MS`,
  `CLEANUP_GRACE_MS` and `LOG_REPORT_RESERVE_MS`
  ([log_capture.rs](../controller/src/log_capture.rs)) are enforced while
  reading. The outer observer allowance is sized for repeated raw lines, six-byte
  JSON escaping and event metadata over bounded inner output; both supervisors
  share one monotonic deadline and a fixed cleanup grace; the derived structures
  (event array, candidates, JSON delimiter count) have independent guards.
- Admission order and echo. `CWorkerOrchestrator.admissionFailure`
  ([CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift))
  checks decoded requests before semantic validation or child process work.
  Its `requestAdmissionFailure` checks metadata and executable overrides
  before plan/parameter counts, then `workerAdmissionFailure`
  ([CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift)) and the host
  `queryAdmissionFailure` check worker strings and query fields. The service
  ([PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift))
  and direct orchestration share this gate. Each string checks its UTF-8
  capacity before its native-string constraint.
  `AdmissionStringRule.requiresCString` selects the NUL guard:
  native strings reject it, while host-only metadata and labels permit escaped
  NUL before semantic validation. `AdmissionStringRule.safeEcho` sanitizes every
  echoed metadata field independently of which diagnostic was selected.
  Host-only metadata is echoed once per reply. The shared-memory string
  slots ([pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h))
  carry no length, so the host rule is the only NUL guard for them; the worker's
  policy reader refuses a NUL on its own (`PW_FAILURE_SOURCE_NUL`, exit 9, offset
  in detail) rather than compile a prefix. The validator
  ([sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c))
  rejects raw controls, invalid UTF-8, malformed escapes and lone surrogates per
  probe line while preserving the next physical line; admitted specimens cannot
  produce such lines. Decoder failures report a bounded category and path, not
  input-derived prose.
- Exec budget and observation. `PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT`
  ([pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c))
  sits `PW_EXEC_ATTEMPT_BUDGET_MARGIN_MS` below the host polling window; the
  margin is a configuration allowance, not an enforced timer. `attempt_budget_start`
  begins before worker setup, `attempt_budget_exclude` subtracts only the
  measured release wait, the cutoff never restarts after spawn, and a blocking
  spawn is not preemptible. Pipe EOF and leader exit are observed separately:
  `waitid` with `WNOWAIT` retains the unreaped leader so deadline cleanup can
  still target its process group after a leader exit; kill, wait and clock
  errors remain errors; final reaping is a nonblocking window of
  `PW_EXEC_REAP_GRACE_MS`; descendants that leave the group are outside cleanup.
- Deny-log window and selection. `LOG_WINDOW_PAD_SECONDS`
  ([sandbox_log.rs](../controller/src/sandbox_log.rs)) pads the span after
  whole-second rounding, which matches `log show` precision; the pad allows for
  client and archive clock differences and guarantees neither delivery nor
  coverage. `sandbox_predicate`
  ([sandbox-log-observer.rs](../controller/src/bin/sandbox-log-observer.rs))
  matches `Sandbox: <name>(<pid>)` for the worker only. Predictions carry
  `SANDBOX_CHECK_NO_REPORT`
  ([sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c)),
  so the kernel writes no record for them. Archive access has cost seconds for
  short spans; scan cost is not independent of span or log volume.
- Nested timeouts. `DEFAULT_TIMEOUT_MS` ([run_flow.rs](../controller/src/run_flow.rs))
  is the client wait; `timeoutMsForCWorker`
  ([CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift))
  the worker polling window; `ValidatorClientInput`
  ([ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift))
  the validator deadline; `PW_PROCEED_WAIT_MS_DEFAULT` the release wait, with
  `validatorReleaseMarginMs` as the nominal margin (60000 > 30000 + 1000 + 5000).
  Policy transfer precedes polling, synchronous validator work is outside the
  polling budget, and cleanup and reaping add time. `runCWorker`
  ([CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift)) counts polling
  iterations for readiness, publication and exit grace; it does not compare an
  elapsed monotonic clock for those waits. The exit grace in `runValidator`
  ([ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift))
  also counts iterations, while its I/O deadline uses `CLOCK_MONOTONIC`.
  Syscall cost and delayed scheduling can extend the nominal polling waits.
- Transport encoding. The controller's `run`
  ([run_flow.rs](../controller/src/run_flow.rs)) reads the request with
  `std::fs::read_to_string` before calling `parse_request`. Invalid UTF-8 takes
  the read-error path to `tool_error`; it never reaches serde_json or the
  runner's JSONDecoder. This path is source-inspected and checked with a
  non-UTF-8 request through the shipped CLI; there is no permanent encoding
  refusal control. Non-UTF-8 bytes in comments and string literals have compiled
  through `libsandbox` on Darwin 23.6; that compiler observation also has no
  permanent check.

## Maintaining this document

Edit [limits.json](limits.json), then run `python3 docs/generate_limits.py` from
the repository root. The same command copies the marked shared section into
[PolicyWitness.md](PolicyWitness.md); edit its explanations here. The same
command also copies the shared questions from [QUESTIONS.md](QUESTIONS.md) into
the guide's Questions section; edit the questions there, writing links into the
guide as `PolicyWitness.md#anchor`. The JSON is a reviewed description;
production code does not load it.

Two editorial rules keep the shared section honest for its reader, a user of the
guide. First, shared prose states only what that reader can observe with the
shipped app: a reply field, a refusal's name, a count, a marker. Second, the
mechanism a statement rests on goes under "Premises behind the interactions",
beside the symbol that implements it, so that an agent or a maintainer can
reopen the premise. Admission rows carry `refusal_field`, the exact
`admission_failure.field` text measured from a refusal, and every `control`
starts with one of Fixed, Flag, Derived or Not enforced; developer-only remarks
belong in `behavior`, which only this document renders.

`python3 docs/generate_limits.py --check` verifies the manifest's shape, source
and check references, generated text in both documents, the copied questions,
and the guide's internal links. The copied sections must contain every limit and
every shared question and require no companion files or web pages. `--stage-guide PATH` performs the same checks before copying
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

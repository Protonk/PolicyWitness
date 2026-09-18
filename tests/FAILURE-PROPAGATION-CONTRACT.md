# Interim failure evidence contract

This is the implemented step-0 contract for
[FAILURE-PROPAGATION-PLAN.md](FAILURE-PROPAGATION-PLAN.md): host observations,
corrected execution classification, response 5 and independent log correlation.
Worker ABI 5 is unchanged. New worker records, late-publication preservation
and the final missing-prediction representation belong to step 1A.

## Evidence and classification

`normalized_outcome` summarizes PW execution. It does not report a policy access
decision or establish why a signal was delivered. All independently confirmed
worker slots, validator verdicts, process observations, and captured log events
survive regardless of which observation determines the summary.

In the table, A means an acquire observation of `applied`, D an acquire
observation of `done`, and R the legacy `apply_rc` storage. A publishes successful
application; D publishes a terminal worker payload, including pre-apply failure.
R is not a native apply result merely because of its name. Parameter allocation,
parameter setting, the defensive parameter NUL check, and compilation can all
write -1. `apply_errno` is populated only for an actual failed application, but
zero does not distinguish compilation, parameter setup, or application failure.
No library result may be inferred from unpublished storage. The parameter NUL
check follows forced termination of the strings and is not credited as a
reliably reachable specimen failure.

For a published legacy failure, retain R and any nonzero legacy errno in the
runner's `error` diagnostic as published status values, without calling R an
observed apply/compile return. A structured failed-operation record belongs to
1A. The controller retains this diagnostic unchanged; subprocess fields below
separately preserve cleanup observations. For an unpublished payload, neither
the diagnostic nor a structured object may expose its storage as a call result.

Rows describing process status require `waitpid` to return the child's PID.
Neither initialized wait storage nor a successful termination request supplies
that status. A last confirmed publication does not identify the instruction at
which the child stopped.

| Observations | Required account | Step-0 summary |
| --- | --- | --- |
| No worker spawned | Retain the host admission/setup/spawn error; no worker report or subprocess object | Existing applicable host outcome |
| A=false, D=false; arbitrary R/errno storage | No published application or failure result; ignore R/errno | Use independently observed deadline or disposition below; never `sandbox_apply_failed` |
| A=false, D=true, R nonzero | Worker published a legacy preparation/application failure; precise failed operation and native return unavailable | `runner_failed`; describe a published legacy failure, without saying an apply or compile call returned R |
| A=false, D=true, R=0 | Inconsistent terminal publication; not evidence of successful application or a library failure | `runner_failed` |
| A=true, published R nonzero | Inconsistent successful-application marker and status; preserve flags, do not choose a library cause | `runner_failed` |
| No terminal report; pre-apply child reaped with exit 0 | Incomplete reporting and observed clean exit; cause unknown | `runner_failed`, not a timeout |
| No terminal report; pre-apply child reaped with nonzero exit | Incomplete reporting and observed exit code; no invented library result | `runner_failed` |
| No terminal report; pre-apply child reaped with signal | Incomplete reporting and observed signal; no policy attribution | `runner_failed` |
| No terminal report; no successful reap or confirmed deadline | Incomplete reporting, unconfirmed process disposition, and any wait/cleanup errors; no invented exit status or cause | `runner_failed` |
| A=true, D=false; child exits or signals before a deadline is observed | Successful application, any completed slots/verdicts, incomplete report, actual disposition | `runner_failed`; signal is not a sandbox verdict |
| Polling exhausts its sentinel budget, then child voluntarily exits during grace | Observed deadline survives independently of exit 0 and absence of a kill request | `runner_timeout` |
| Polling exhausts its sentinel budget, then host requests termination | Deadline, request, call result, and any reaped status remain distinct | `runner_timeout`, including when kill/reap fails |
| Published legacy failure followed by observed deadline, cleanup kill, or failed kill/reap | Keep the reported failure and every subsequent host observation | `runner_failed`; cleanup does not replace the earlier report |
| A=true, D=true, R=0; exit grace expires and host requests termination | Completed report/slots survive; record cleanup request and result without inventing a sentinel deadline | `runner_failed`, even if the child subsequently exits 0 |
| A=true, D=true, R=0; independently reaped nonzero exit or signal | Completed report/slots survive alongside abnormal disposition | `runner_failed` |
| A=true, D=true, R=0; disposition unconfirmed or unrecovered wait error | Completed report/slots survive; exit/signal absent unless reaped | `runner_failed` |
| A=true, D=true, R=0; reaped exit 0, no unresolved host fault or termination request | Worker completion confirmed; evaluate validator observations | Existing validator mapping, or `ok` when required evidence is complete |

Summary precedence is: host rejection before spawn; inconsistent published
worker state; published legacy worker failure; observed sentinel expiry; other
worker incompletion/abnormal disposition/unresolved host error; validator
failure; `ok`. A recovered EINTR alone is not a failed run. A cleanup request
without an observed sentinel expiry is not a timeout. This ordering selects
the summary only; it does not discard another observer's evidence. Validator
lifecycle and record-association repairs remain step 2; step 0 must not claim
that the current validator mapping proves those properties.

## Host observations implemented in 0B

Use `runner_subprocess` as the authoritative process object. The following
additive JSON locations are defined with producer/validity comments in
[`PWRunnerAPI.swift`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) and
[`CWorker.swift`](../runner/Sources/PWRunnerCore/CWorker.swift).
They are host observations, not a new worker ABI or a fabricated worker failure
record. Internal `CWorkerOutput` carries the same facts to the assembler.

| JSON location under `runner_subprocess` | Producer, type and validity |
| --- | --- |
| `pid` | Existing host-observed spawned PID; JSON integer |
| `exit_code`, `term_signal` | Existing JSON nullable integers, decoded only after successful reaping; both absent/null if no status obtained |
| `partial_steps` | Existing host summary of missing completed slots; does not prove an attempt never started |
| `ready_byte_received` | Host boolean: a byte was actually read; false supplies no compile/apply result |
| `done_observed` | Host boolean from acquire polling; step 1A will also preserve publications observed during cleanup |
| `poll_stop_reason` | Host string: `done`, `child_reaped`, `sentinel_deadline`, or `wait_error`; retains why polling stopped, regardless of subsequent publication/cleanup |
| `exit_requested` | Host boolean: release-store to the exit-request flag occurred; not proof the worker acted on it |
| `termination_request` | Optional host object with `signal` (integer), `rc` (signed syscall return), `errno` (integer only on failed kill, otherwise absent/null); absent/null means no request |
| `reaped` | Host boolean: a wait call actually returned this PID; not inferred from kill success |
| `wait_errors` | Host array of observed wait failures, each with phase, signed return and errno; retain errors even if a later wait succeeds |

`sandboxed_after_apply` remains the public application observation; do not add a
second authoritative applied boolean. `sentSigkill` internally must not stand in
for deadline expiry or successful termination/reaping. New fields decoded from
old stored replies must be optional/unknown rather than synthesized observations.
Optional subprocess objects preserve the existing omitted-or-null convention.

The readiness, sentinel and exit-grace budgets are unchanged. The driver allows
two EINTR retries total across polling, grace and final reaping. A terminal wait
error ends that phase; ECHILD stops all further waits and signals to that PID.
There are at most five failed-call records (two recovered interruptions plus one
terminal error per phase), with no error truncation. `wait_errors[].phase` is
`poll`, `exit_grace`, or `after_termination`; rc/errno and termination numbers
are signed 32-bit syscall values, encoded as JSON integers. Empty errors means
observed none; missing/null means unavailable in an older reply.

A failed kill permits only a nonblocking final reap; if no status arrives, the
result explicitly records `reaped=false` and omits exit/signal. A successful kill
retains the existing blocking final wait, with finite EINTR retries if it fails.
This bounds failed-call handling, not kernel exit latency or the whole lifecycle.
An unreaped child or zombie may remain; no global reaper is introduced. Test
equipment independently cleans up children it owns without changing the driver
result. This contract adds no global lifecycle or policy-transfer deadline.
The policy-write error path's partial-evidence repair belongs to 1C. The current
payload snapshot precedes cleanup; refreshing late publications remains 1A.

## Public compatibility and correlation

Responses use schema 5, distinct from request schema 1, the outer controller
envelope and worker ABI 5. Every new step explicitly encodes `deny_signal: null`;
old signal objects remain decodable as stored legacy evidence. This is a wire
change for typed readers requiring a signal object. Explicit errno/drift nulls
remain required. No signal collection is added.

Current producers do not emit `runner_sandbox_denied`: existing evidence cannot justify
its causal meaning. It remains a recognized legacy string for stored replies,
not an alias to which new unknown terminations are assigned.
`sandbox_apply_failed` is reserved for precise operation/result evidence; the
ambiguous legacy status does not justify it. Both constants and coverage rows
remain as legacy/reserved entries. `runner_failed` covers execution/reporting failure with cause possibly
unknown; it does not mean a proven host defect. `bad_policy` keeps its existing
structural-policy admission meaning. No new outcome string is needed for step 0.

The pre-apply CLI witness asserts excluded claims, not one exact summary;
the table's classifier controls pin the mapping. During step 0, the compatibility
attempt spelling `not_run_worker_died` means no completed attempt result, not
proof that an operation never started. The final spelling and synthetic missing
prediction `rc=0` treatment are decisions for step 1A.

Worker identity comes only from a positive `runner_subprocess.pid`, never a
host/client top-level PID. Capture remains available on successful runs.
`runner_sandbox_diagnostics` describes process disposition and capture status
independently of outcome: disabled, no worker, and observer availability stay
distinct. Correlation status is `not_attempted`, `unavailable`, `no_match`, or
`pid_match`. Abnormal/unconfirmed disposition has `termination_cause="unknown"`.
Application remains separately recorded in `sandboxed_after_apply`.

`first_deny` is an `{event_index}` reference to the first matching worker PID in
the capture array, not a cause or temporal first event. `step_denies` records
`{event_index, candidate_step_ids, association}`. One candidate has association
`candidate`; multiple matching attempts have `ambiguous`. Events are not copied
per step; the original observer reply and parsed `deny_events` array survive,
including unmatched events. This does not identify a unique occurrence.

Step correlation requires both PIDs, an exact operation relevant to the submitted
attempt (kind/action joined by unique step ID), and exact submitted/attempt path
evidence. Queries are independently routed and never supply that provenance.
Unknown/missing operations and unusable duplicate-ID joins stay unmatched. No
wildcard/prefix aliases are used; create accepts both `file-write-create` and
`file-write-data` because it may open an existing file for writing. The complete
[operation mapping](../PolicyWitness.md#denial-log-correlation) is part of the
public contract. An incomplete attempt can still be a candidate: a kernel event
can precede interrupted publication.

`capture.window` records trailing `--last` and explicitly reports no structured
event timestamps, exact run membership, step ordering, or PID-reuse protection.
Raw lines remain available. The observer preserves the full remaining target,
including spaces; it does not shorten a path into a different target. PID
matching alone never establishes a termination cause or exact run membership.

## Coverage audit and acceptance ownership

The entries below distinguish constructed host interpretation, actual C-worker
publication, and the CLI boundary. The host-driver, encoding and classifier
controls establish separate parts of the table; retained execution evidence is linked from the
plan's current execution state.

| Test entry | Production reach and current assertions | Acceptance owner / remaining obligation |
| --- | --- | --- |
| `runner_unit/pwrunner_core_unit_executable`: `HostOutcomeClassifierTests.runHostOutcomeClassifierTests` | Constructed `CWorkerOutput`/validator results; pins publication, deadline, disposition and precedence rows; no OS calls or worker publication | Implemented, independently of driver tests |
| Same catalog case: `EnvelopeInvariantTests.runEnvelopeInvariantTests` | Constructed Codable results; response 5 explicit signal null, legacy response-4 objects, subprocess absence and unknown vs observed false/empty, unfamiliar observation values | Implemented; actual client error replies also checked in smoke/runner_caller_auth |
| Same catalog case: `CWorkerTests`, `postApplyHangMs > sentinelTimeoutMs produces done=false` | Real worker through Swift driver; late voluntary exit with no host kill and exit 0; records `sentinel_deadline`, reaped exit 0, and no termination request through actual subprocess encoding | Driver plus runner_timeout classifier verified; 1A final snapshot must retain late publication |
| Same catalog case: `CWorkerTests`, `postApplyKillSignal terminates worker before done -> runner_failed` | Real C worker self-signals; asserts applied/not-done/no-host-kill/SIGKILL, `child_reaped` and encoded process facts, then calls classifier | Driver plus runner_failed classifier verified; no real sandbox kill is established |
| Same catalog case: `CWorkerValidatorTests`, `postApplied hook does not fire when compile fails` | Real malformed SBPL through Swift driver; asserts no applied marker and zero hook calls | Retain; does not prove diagnostic text reaches CLI; 1B adds that boundary |
| `runner_c_worker_harness/compile_failure` (`run_compile_failure`, `harness.c` scenario) | Real C worker: no ready byte, A=false, D=true, R=-1, no completed slot, exit 0 and no host kill | Retain actual publication/exit protection; not Swift interpretation or CLI forwarding |
| `runner_c_worker_harness` early-exit and success cases; `runner_abi_layout` | Actual C worker's early guards and attempts; independently compiled C layout compared with Swift constants | Complementary ABI/publication protection; keep ABI 5 in step 0 |
| `witness_contract/pre_apply_failure_reports_no_policy_verdict` (`check_pre_apply_failure.py`) | Real CLI, populated allowed/denied plan, pre-ready delay and worker deadline; identical un-overridden positive control | All response-5 assertion groups pass; 0A/0B retain actual earlier failures independently |
| `runner_unit/pwrunner_core_unit_executable`: `CWorkerLifecycleTests.runCWorkerLifecycleTests` | Real host driver with test-only ABI child: completed report then cleanup SIGKILL, independent exit 17 or SIGTERM, published legacy failure then cleanup, failed kill, failed/recovered/interrupted wait, ECHILD ownership loss and poll EIO. Actual subprocess assembler and JSON round-trip preserve reports and missing status. Fixture applies no sandbox. | Driver, assembler, encoding and classifier agree; synthetic payload does not establish a native library result |
| `runner_ready_byte_resilience/slow_compile_ready_byte_survives_sigpipe` | Real CLI with sufficient budget; lost ready byte must not prevent successful application, prediction and attempt | Successful resilience verified; delay follows compilation/capture and has sufficient sentinel budget |
| `runner_outcome_runner_timeout/host_kills_hung_worker`, `witness_contract/worker_post_apply_hang_seam`, `runner_use_c_worker/worker_timeout_ms_honored` | Real CLI post-apply deadlines; empty, mixed and single-write plans, retained evidence and independently checked effects | Success/timeout/partial-evidence checks pass; populated pre-apply witness adds distinct absence coverage |
| `witness_contract/worker_termination_and_log_correlation`; Rust `run_flow::tests`, `sandbox_log::tests`, observer parser tests | CLI ordinary denied writes, repeated attempts, independent read queries, self-signal, capture disabled/enabled and successful-run capture. Constructed captures pin PID, operation, target, ambiguity, window and availability semantics. Parser preserves missing identity and full paths without structured timestamps. | Implemented; optional real logs do not replace deterministic populated-event controls or establish a policy cause |
| `runner_validator_failure/validator_unavailable_reports_degraded`, `runner_validator_failure/validator_decode_failure_reports_degraded` (also witness suite members) | Real worker attempts plus fixture validator, reversed partial IDs, missing verdict and null drift; malformed JSON is distinct from EOF | Retain; 1A distinguishes missing prediction reasons; validator lifecycle/UTF-8/structure/association repairs are step 2 |
| `runner_unit`: `SandboxApplyTests` | Calls the unused Swift apply helper, not the C producer | No production failure-reporting credit; helper/type/test cleanup is outside this effort; preserve live `computePolicyHash` |

Real-worker `CWorkerTests` cases guarded by `workerExists()` require
`<PW_APP_DIR>/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner`.
`CWorkerValidatorTests` live cases use that worker and the diagnostic app-level
`<PW_APP_DIR>/Contents/MacOS/sb_api_validator` (including the compile-failure
case's `bothBinariesExist()` guard). Production CLI orchestration uses the
bundle-local validator in the XPC service. Tests without `PW_APP_DIR` select
`dist/PolicyWitness.app`. Record those actual paths in retained provenance.

`TestKit.run` counts a guarded early return as passed; the shell wrapper checks
only exit status and the summary. Credit live rows only after selecting
`runner_unit` alongside an app-dependent case, inspecting bundle-integrity
evidence and the complete retained `pwrunner_core_tests.log`, and finding actual
case execution without internal `SKIP`. Newly required live controls must fail
when their equipment is missing. Constructed classifier/encoding cases have
separate credit. `source_drift` protects registry/outcome matrices and remains
required at the step-0 gate.

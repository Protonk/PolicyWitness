# Failure evidence contract

This is the implemented contract for steps 0 and 1 of
[FAILURE-PROPAGATION-PLAN.md](FAILURE-PROPAGATION-PLAN.md): host observations,
worker ABI 6 publications, response 6 and independent log correlation.
Worker records, diagnostic text, late publications and policy-transfer partial
outputs preserve independently observed facts through to the CLI.

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
observed apply/compile return. ABI 6 records identify the failed operation and
its native result independently of this legacy storage. The controller retains this diagnostic unchanged; subprocess fields below
separately preserve cleanup observations. For an unpublished payload, neither
the diagnostic nor a structured object may expose its storage as a call result.

Rows describing process status require `waitpid` to return the child's PID.
Neither initialized wait storage nor a successful termination request supplies
that status. A last confirmed publication does not identify the instruction at
which the child stopped.

| Observations | Required account | Summary |
| --- | --- | --- |
| Valid ABI 6 failure publication | Retain operation/code/native result, optional text, and independent host observations | `runner_failed` |
| Incomplete or malformed ABI 6 failure publication | Do not expose unpublished fields or infer a library result | `runner_failed` |
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

Summary precedence is: host rejection before spawn; published ABI 6 failure;
host transfer failure; incomplete/malformed failure publication; inconsistent published
worker state; published legacy worker failure; observed sentinel expiry; other
worker incompletion/abnormal disposition/unresolved host error; validator
failure; `ok`. A recovered EINTR alone is not a failed run. A cleanup request
without an observed sentinel expiry is not a timeout. This ordering selects
the summary only; it does not discard another observer's evidence. The validator
lifecycle and record-association requirements below also apply before `ok`.

## Host observations

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
| `done_observed` | Host boolean from the final acquire snapshot after cleanup |
| `poll_stop_reason` | Host string: `done`, `child_reaped`, `sentinel_deadline`, `wait_error`, or `policy_write_error`; retains why polling stopped, regardless of subsequent publication/cleanup |
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
Policy-write failure retains the child's partial evidence. The final acquired
snapshot follows cleanup, preserving late immutable publications. The write
pipe suppresses SIGPIPE; original descriptors close on exec so only intended
child descriptors survive.

## Public compatibility and correlation

Responses use schema 6, distinct from request schema 1, the outer controller
envelope and worker ABI 6. Every new step explicitly encodes `deny_signal: null`;
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
structural-policy admission meaning. Published ABI 6 failures also use `runner_failed`; the operation/code record
provides the precise account without adding outcome strings.

The pre-apply CLI witness asserts excluded claims, not one exact summary;
the table's classifier controls pin the mapping. The compatibility
attempt spelling `not_run_worker_died` means no completed attempt result, not
proof that an operation never started. Synthetic missing predictions retain
`rc=0` with an explicit result source, missing reason, and null native return.

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
| Same catalog case: `EnvelopeInvariantTests.runEnvelopeInvariantTests` | Constructed Codable results; response 6 explicit signal null, legacy response-4 objects, subprocess absence and unknown vs observed false/empty, unfamiliar observation values | Implemented; actual client error replies also checked in smoke/runner_caller_auth |
| Same catalog case: `CWorkerTests`, `late done during grace preserves sentinel deadline` | Real worker through Swift driver; late voluntary exit with no host kill and exit 0; records `sentinel_deadline`, reaped exit 0, and no termination request through actual subprocess encoding | Driver, final done/slot snapshot and runner_timeout classifier verified |
| Same catalog case: `CWorkerTests`, `postApplyKillSignal terminates worker before done -> runner_failed` | Real C worker self-signals; asserts applied/not-done/no-host-kill/SIGKILL, `child_reaped` and encoded process facts, then calls classifier | Driver plus runner_failed classifier verified; no real sandbox kill is established |
| Same catalog case: `CWorkerValidatorTests`, `postApplied hook does not fire when compile fails` | Real malformed SBPL through Swift driver; asserts no applied marker and zero hook calls | Retain; does not prove diagnostic text reaches CLI; 1B adds that boundary |
| `runner_c_worker_harness/compile_failure` (`run_compile_failure`, `harness.c` scenario) | Real C worker: no ready byte, A=false, D=true, R=-1, no completed slot, exit 0 and no host kill | Retain actual publication/exit protection; not Swift interpretation or CLI forwarding |
| `runner_c_worker_harness` early-exit and success cases; `runner_abi_layout` | Actual C worker's early guards and attempts; independently compiled C layout compared with Swift constants | Complementary ABI/publication protection; ABI 6 layout and exact-version rejection |
| `witness_contract/pre_apply_failure_reports_no_policy_verdict` (`check_pre_apply_failure.py`) | Real CLI, populated allowed/denied plan, pre-ready delay and worker deadline; identical un-overridden positive control | All response-6 assertion groups pass; 0A/0B retain actual earlier failures independently |
| `runner_unit/pwrunner_core_unit_executable`: `CWorkerLifecycleTests.runCWorkerLifecycleTests` | Real host driver with test-only ABI child: completed report then cleanup SIGKILL, independent exit 17 or SIGTERM, published legacy failure then cleanup, failed kill, failed/recovered/interrupted wait, ECHILD ownership loss and poll EIO. Actual subprocess assembler and JSON round-trip preserve reports and missing status. Fixture applies no sandbox. | Driver, assembler, encoding and classifier agree; synthetic payload does not establish a native library result |
| `runner_ready_byte_resilience/slow_compile_ready_byte_survives_sigpipe` | Real CLI with sufficient budget; lost ready byte must not prevent successful application, prediction and attempt | Successful resilience verified; delay follows compilation/capture and has sufficient sentinel budget |
| `runner_outcome_runner_timeout/host_kills_hung_worker`, `witness_contract/worker_post_apply_hang_seam`, `runner_use_c_worker/worker_timeout_ms_honored` | Real CLI post-apply deadlines; empty, mixed and single-write plans, retained evidence and independently checked effects | Success/timeout/partial-evidence checks pass; populated pre-apply witness adds distinct absence coverage |
| `witness_contract/worker_termination_and_log_correlation`; Rust `run_flow::tests`, `sandbox_log::tests`, observer parser tests | CLI ordinary denied writes, repeated attempts, independent read queries, self-signal, capture disabled/enabled and successful-run capture. Constructed captures pin PID, operation, target, ambiguity, window and availability semantics. Parser preserves missing identity and full paths without structured timestamps. | Implemented; optional real logs do not replace deterministic populated-event controls or establish a policy cause |
| `runner_validator_failure/validator_unavailable_reports_degraded`, `runner_validator_failure/validator_decode_failure_reports_degraded` (also witness suite members) | Real worker attempts plus fixture validator, reversed partial IDs, missing verdict and null drift; malformed JSON is distinct from EOF | Missing prediction reasons are distinct; validator lifecycle/UTF-8/structure/association repairs are step 2 |
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

## Step 1 contract (ABI 6 accepted)

The authoritative layout is `pw_probe_runner_abi.h::pw_shm_evidence_t`, appended
following the existing capture bytes. Existing input/output capacities and
budgets do not change. Host and worker require exactly ABI 6; there is no ABI 5
fallback. Response schema 6 supports nullable query PIDs and additive evidence fields; request schema stays 1.
The worker record is `data.runner_result.runner_subprocess.worker_evidence`.
Legacy stored replies may omit it. Its `abi_version` is the host-selected UInt32
layout encoded as a JSON integer, not proof the child reached ABI validation.
An entirely absent publication remains explicit even after a mapping failure.
Host process observations remain independent.

### Progress and state table

One release-stored/acquire-loaded UInt32 is the entire progress snapshot: high
8 bits operation, next 4 bits phase (1 started, 2 returned), low 20 bits item
index plus one (zero means no index). JSON retains `raw`, `operation`, `phase`,
and optional zero-based `index`. Zero raw means no progress publication; unknown
operation/phase values are retained without inferring success. No non-atomic
payload is read through progress. This is the latest milestone, not a history.

Operations: 1 compatible header validation, 2 policy read, 3 parameter allocation,
4 parameter assignment, 5 compilation, 6 optional profile capture, 7 readiness
write, 8 application, 9 indexed attempt, 10 terminal completion. Started means
control reached the call boundary; returned means control returned, regardless
of success. Application is established only by `applied == 1`. Completed attempt
outputs are established only by that slot's `completed == 1`.

| Observation | Meaning / next transition |
| --- | --- |
| compile started; worker dies | No observed return; no invented NULL or errno |
| compile returned; next operation not started | Call returned; success requires subsequent independent evidence; a report may still be unpublished |
| compile NULL | Returned progress, then immutable operation=5 failure with native_kind=2, native_result=0; done may follow |
| param assignment i returns nonzero | Record operation=4 and index=i with the actual integer return; no fabricated apply result |
| assignment i returns and i+1 starts | Atomic progress identifies exactly one boundary; no torn index/phase |
| readiness write fails | Its own immutable rc/errno record remains; execution may proceed to apply and done |
| optional capture omitted | Transition compile → readiness is valid |
| attempt i starts but never completes | Progress may identify the started slot; no completed result or claim that it never ran |
| failure published; diagnostic incomplete; cleanup fails | Failure status, diagnostic availability and host observations survive independently |
| done published during exit grace | Final acquired payload/slots survive; earlier poll stop/deadline stays unchanged |

### Failure, readiness and text fields

Every field below is worker-owned. Host zeroes and pre-touches the full region
before spawn. `failure_published`: UInt32 atomic, 0 absent, 2 being written,
1 valid immutable payload; other values invalid. Only an acquire of 1 permits
payload reads. JSON `failure_state` distinguishes absent/incomplete/published/
invalid; `failure_publication` preserves the raw word. An absent/incomplete
failure omits `failure`. All-zero payload with publication 1 is still a report.

Published payload fields have the same names and integer types in Swift/JSON:
`operation`, `code`, `native_kind`, `detail`: UInt32; `native_result`: Int32;
`errno_val`: Int32 gated by UInt32 `errno_present` (0/1); `item_index`: UInt32
with UINT32_MAX meaning absent. JSON renames the latter two to optional `errno`
and `index`. Native kind 0 means no native return (stored result is padding,
JSON native_result is omitted); 1 is a signed integer return; 2 is a NULL pointer
return represented by zero, never a pointer address. Unfamiliar kinds retain
the raw signed result. Unknown operation/code/detail are transported unchanged;
recognition is not validity. Invalid errno presence or a nonzero result tagged as NULL rejects payload decoding.
Code 1 is native failure, 2 source capacity rejection (detail is maximum source
bytes, excluding NUL), 3 policy read error, 4 step capacity, 5 parameter capacity,
6 defensive parameter encoding rejection, 7 unprepared header. No errno is claimed for libsandbox
allocation/parameter/compile calls, whose return contracts do not establish it.
Failed apply and failed read capture errno immediately; zero remains a value.

`ready_published`: atomic UInt32 0/1; acquire 1 publishes immutable Int32
`ready_rc` (0 success, -1 failure) and `ready_errno` (meaningful only on failure).
JSON `readiness` carries rc and optional errno; it is the worker write result,
independent of host `ready_byte_received`.

`diagnostic_state`: atomic UInt32 0 absent, 3 writing/incomplete, 1 complete,
2 truncated. Only acquire 1/2 permits reading UInt32 `diagnostic_length` and that
many bytes in the fixed 4096-byte text region (at most 4095 payload bytes).
The producer NUL-terminates; length excludes NUL, not characters. Text and length
are immutable once published. JSON `diagnostic` always carries raw `state` and
`status`; valid text also carries `length` and `text` (UTF-8 decoding replaces
invalid sequences). Unknown states retain their raw value with status unknown;
out-of-bounds lengths or missing declared NUL terminators yield invalid, never
an out-of-bounds read. Empty published
text differs from absent text. No text or length is read in state 0/3. Failure
publication precedes text; status never depends on successful text publication.
Post-apply reporting uses only fixed memory and atomics, no new allocation or
I/O. Early stderr emissions remain; this work does not collect that stream.

Swift decodes shared memory and assembles these fields without code allowlists;
runner JSON encodes them. The XPC client forwards reply bytes, and the controller
retains opaque JSON within its existing capture limit. Neither reconstructs a
typed failure. `runner_failed` summarizes any published worker failure, including
observed apply/compile failures; the specific operation remains in the record.
Failure records take precedence over later deadline/cleanup observations, all
of which remain independently visible. Unknown progress alone implies no failure
or success. A malformed/incomplete failure publication cannot yield `ok`.

### Missing step evidence

Both step channels add optional `result_source`, `native_rc`, `missing_reason`.
Legacy decoding preserves absence. Live assembly emits native_rc as explicit
null when unavailable. Existing required rc/outcome fields stay compatible.
Prediction rc=0 with outcome=error remains a synthetic compatibility sentinel:
result_source=synthetic and missing_reason=validator_not_invoked (no validator
process), or validator_no_verdict (process ran without this verdict). Excluded
queries use query_not_requested. Received verdicts use result_source=validator;
native_rc is present only for actual allow/deny/error native call results, not
parse/unsupported/filter rejections. Run-level validator subprocess metadata
remains authoritative; per-step fields do not duplicate PID/disposition.

Attempts retain the compatibility spelling `not_run_worker_died` as the final
missing-result spelling; it means no completed result, never proof of non-start.
They use result_source=synthetic, native_rc=null, and missing_reason=slot_absent
or slot_incomplete. Completed supported slots use result_source=worker. Their rc is PW
attempt status (often 0/1, or aggregated exec disposition), not a native syscall
return such as an open FD. ABI 6 does not carry that raw return: native_rc is
null for attempts, including completed ones. Unsupported/skipped attempts use synthetic and
attempt_not_supported. Step errno/drift/signal absence retains its existing form.

### Acceptance observations fixed before implementation

Real success retains attempts/predictions without a failure; real syntax error
identifies compilation NULL and diagnostic; producer-controlled apply failure
retains native return/errno. Missing/incomplete publication exposes no payload.
Late publication retains slots and deadline. Unknown codes survive fixture →
real host → XPC → CLI. Never-invoked and short-reply validators differ; an
interrupted started attempt remains incomplete. In 1C, worker source rejection
and host EPIPE must coexist, closed-input controls must work without oversized
admission, and mapping failure preserves exit 3 without invented errno/cause.
Failures after completed real probes preserve independently checked effects.

### Policy-transfer failure (1C)

`CWorkerRunResult.failure(error, partial)` carries an optional actual worker
output. No child means no partial; an observed policy write failure after spawn
retains final acquired worker publications, slots, readiness, and cleanup/status.
`runner_subprocess.policy_transfer_error` is host-owned: Int32 `errno` captured
immediately from failed write; nonnegative Swift Int/JSON integers `bytes_written`
and `bytes_expected` count successful host writes and submitted UTF-8 bytes.
Counts are not evidence of bytes consumed by the worker. Object omission means
no observed transfer failure; it does not establish transfer success before spawn.
A zero errno is retained if observed. No worker record is synthesized from it.
The poll stop reason is `policy_write_error`; sentinel polling never began.
The host suppresses SIGPIPE on this pipe's write FD using F_SETNOSIGPIPE before
spawn, checking setup failure. After write failure it closes input, requests exit,
and uses the step-0 grace/termination/reaping contract. All evidence reaches the
same partial-output assembly path. A worker failure summary takes precedence
when published; host transfer error remains independently available and named.
An open, undrained pipe is still a blocking pre-sentinel transfer with no deadline.

## Admission and validator/controller receiver contract

Worker admission limits use `runner_result.admission_failure`, observed by the
runner host before shared-memory setup/spawn. Its fields are `origin=runner_host`,
`field`, `actual`, `maximum`, `unit`, and optional `step_id`, `parameter_key`,
`index`. `utf8_bytes` excludes NUL; `items` counts entries. Limits remain source
262143 bytes, steps 256, parameters 1024, step ID 63 bytes, target 511, parameter
key/value 127/383, supplied exec args 15 of 127 bytes each. `PW_SHM_POLICY_BYTES`
and its Swift mirror include the source NUL. The C reader independently refuses
oversized source when driven directly; normal CLI oversized source is a host
`bad_request` with no subprocess. Policy-write interruption controls use admitted
source sizes and retain their separate host and child observations.

`ValidatorClient.swift` owns the record acceptance rules, stated beside its
byte-frame decoder. `PWRunnerAPI.swift` owns the JSON representation. A complete
allow/deny record requires native integer rc/errno, nonempty step ID/operation/
filter type, kind, schema and outcome. Diagnostic outcomes require string error,
but can omit native results; unfamiliar outcomes and extra raw JSON fields are
preserved. Booleans, strings and fractional values cannot stand in for integers.
Parsing never turns a missing native result into a prediction.

`validator_subprocess` retains all accepted `records` with original `raw_line`,
including explicit null step IDs. Its `expected_step_ids` and `association_issues`
record missing, duplicate, unexpected and unassociated IDs, plus query mismatches.
Only a unique record matching the submitted query enters the step join; duplicate records remain at run scope
and produce no guessed prediction. Existing uniquely associated per-step error
and unsupported-operation semantics remain: their diagnostic alone does not fail
the run. Run-level framing/association gaps do fail it.

The host frames bytes on LF before strict UTF-8 decoding, then checks JSON syntax
and structure. It accepts a final nonempty fragment if valid and stops at the
first rejected frame, retaining preceding records. `decode_fault` has
`origin=runner_host`, `kind=utf8|json|structure`, message, exact `byte_offset` and
`frame_bytes`, and at most 256 context bytes as `context_b64`, with
`retained_bytes` and explicit `context_truncated`. Rejected context never enters
`records`. `stdout_bytes_received` counts all bytes actually drained, not bytes a
child may have attempted to write. `probe_bytes_written`/`probe_bytes_expected`
count host writes and serialized bytes, not consumption. `io_error` and
`decode_fault` can coexist; the I/O failure takes summary precedence.

Both child drivers use `ChildProcessState`/`ChildProcessCalls` in `CWorker.swift`.
Validator `reaped`, `termination_request`, `wait_errors`, `exit_code` and
`term_signal` obey the same successful-reap and finite EINTR contract as the
worker. Legacy absent host fields are unknown. The validator's `.success` driver
variant only means no transport/decoding error; it cannot establish clean
process disposition. `validator_unavailable` includes incomplete ID coverage,
association faults, cleanup requests, non-EINTR wait faults and abnormal or
unconfirmed disposition even with enough records. `validator_decode_failure`
identifies the receiver's UTF-8/JSON/structure boundary; `validator_no_reply`
identifies I/O failure. Worker summary precedence does not discard the validator
subprocess evidence. All original validator pipe descriptors close on exec;
parent writes use FD-scoped SIGPIPE suppression and checked nonblocking setup.

The controller collects full `Command::output()` buffers before retaining a
1 MiB prefix per stream for runner-client, sbpl-check and log-observer replies.
Each capture object's `stdout_bytes_received` and
`stderr_bytes_received` are exact full lengths; `*_bytes_retained` are measured
before lossy text conversion; `capture_limit_bytes` is 1048576. Locally truncated
stdout is not parsed and has `stdout_capture_error`, distinct from
`stdout_parse_error` for malformed JSON/UTF-8 within the cap. Text context may use
replacement characters; accepted JSON is parsed from original untruncated bytes.
Synthetic non-invocations have null received/retained counts. This cap is not a
streaming allocation bound, and inner records cannot be promised when their
outer envelope was lost. Independent `sbpl-check` admission remains
`policy_too_large` in both helper status and missing-reply note prose.

Readiness, blocking policy transfer, the nominal 60s worker polling budget,
synchronous 30s validator I/O and default 240s client timeout remain separate
phases. No end-to-end worker deadline was added. Failed cleanup can leave an
unreaped child; successful termination still uses blocking final wait. No early
stderr capture is added: pre-mapping, direct dependency output and crashes in the
reporting path may leave no diagnostic text. Optional compiled-object capture
(1 MiB) and exec stream text (1023 bytes each, with truncation marker) keep their
existing refusal/truncation semantics. Neither optional capture failure nor an
incomplete post-apply attempt proves a policy cause or instrumentation defect.

## Query and receiver evidence

Response 6 makes `steps[].sandbox_check.pid` nullable: it is the spawned worker
PID, or explicit null when no worker exists. It never substitutes the host PID.
Typed readers must accept null; stored integer-PID replies remain decodable.
The top-level legacy PID convention is unchanged. Request schema 1 and worker
ABI 6 remain separate.

Per-step `native_rc` is authoritative for native returns. A received diagnostic
without a native return retains `result_source="validator"`, `native_rc=null`
and compatibility `rc=-1`; this is not a synthetic validator record or a claimed
native failure. Missing replies use synthetic `rc=0`, `outcome="error"` with a
missing reason. `outcome="error"` alone does not identify a native call failure.

Query planning records each submitted probe or exclusion reason before attempts
run. A later create/unlink cannot change that decision, including when all
queries are excluded and no validator runs. Only unique records matching the
submitted `(operation, filter_type, filter_value)` supply a step prediction.
Mismatch records remain under `validator_subprocess.records`, with
`association_issues.kind="query_mismatch"`, null step drift and a non-ok run.
Diagnostics may omit query metadata; any metadata they supply must agree.
Queries and attempted operations remain independent.

An input write failure stops writes but does not stop stdout collection. The
host drains under the original I/O deadline. `io_error` retains the first write
failure (or read failure when no write failed); `read_error` independently retains
a read/poll/deadline failure. `stdout_collection_stop` is `eof`, `deadline`,
`read_error` or `poll_error`. EOF describes observed collection completion, not
validity of all received frames. Decoding faults coexist with these observations.

All controller JSON receivers (runner client, sbpl-check and log observer) use
the same 1 MiB retained-prefix cap and original-byte JSON parser. Exact stdout
and stderr received/retained byte counts precede lossy context conversion.
`stdout_capture_error` identifies local truncation and precludes parsing the
prefix; `stdout_parse_error` identifies malformed untruncated bytes. Helper
`status="invalid_reply"` means parsed JSON lacks the required compilation
observation; `compiled` remains null and the original envelope is retained.
The observer similarly uses `capture_status="invalid_reply"` when no denial
observation or explicit helper failure is available. This cap is not a streaming
memory bound.

The directional `drift=false` case for a deny prediction plus ambiguous
EPERM/EACCES is unchanged. False does not establish that the sandbox caused the
attempt failure; the separate-query DAC control demonstrates this distinction.

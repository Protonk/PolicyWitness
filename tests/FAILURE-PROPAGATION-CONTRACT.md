# Failure evidence contract

This contract specifies host observations, diagnostic preservation and derived
comparisons: worker ABI publications, the runner reply and independent log correlation.
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
observed apply/compile return. Worker failure records identify the failed operation and
its native result independently of this legacy storage. The controller retains this diagnostic unchanged; subprocess fields below
separately preserve cleanup observations. For an unpublished payload, neither
the diagnostic nor a structured object may expose its storage as a call result.

Rows describing process status require `waitpid` to return the child's PID.
Neither initialized wait storage nor a successful termination request supplies
that status. A last confirmed publication does not identify the instruction at
which the child stopped.

| Observations | Required account | Summary |
| --- | --- | --- |
| Proceed wait expiry (operation 11, code 8) or native clock failure (kind 3) | Preserve budget detail/diagnostic and zero attempts; late release cannot revive | `runner_failed` |
| Death awaiting release | Preserve disposition/progress without inventing a failure record or policy cause | `runner_failed` |
| Valid worker failure publication | Retain operation/code/native result, optional text, and independent host observations | `runner_failed` |
| Incomplete or malformed worker failure publication | Do not expose unpublished fields or infer a library result | `runner_failed` |
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

Summary precedence is: host rejection before spawn; published worker failure;
host transfer failure; incomplete/malformed failure publication; inconsistent published
worker state; published legacy worker failure; observed sentinel expiry; other
worker incompletion/abnormal disposition/unresolved host error; validator
failure; `ok`. A recovered EINTR alone is not a failed run. A cleanup request
without an observed sentinel expiry is not a timeout. This ordering selects
the summary only; it does not discard another observer's evidence. The validator
lifecycle and record-association requirements below also apply before `ok`.

## Reply construction failure

Response 8 distinguishes a host reporting failure from the execution summary.
If the assembled result cannot be encoded, the reply uses
`normalized_outcome: "runner_reporting_failed"`, `rc: 1` and an explanatory
`error`. The controller consequently reports `ok: false`. This supplies no new
worker, validator or policy failure claim.

The `reporting_failure` object has `origin: "runner_host"`, a `diagnostic`,
`original_rc`, `original_normalized_outcome`, optional `original_error`, and
`evidence_retained`. For an invariant rejection, `evidence_retained` is true:
all step IDs, queries, attempts, path diagnostics, application observations,
subprocess objects (including raw validator records and ordering observations),
policy capture and test overrides survive unchanged. Every step's `comparison`
is omitted and `drift` is explicit null. The original summary is diagnostic,
not a second authoritative outcome. Retained ordering fields are diagnostic
observations; no per-step order is certified by this reply.

This is the sole exception to mandatory comparisons and complete
ordering objects. Consumers require the failure outcome, nonempty diagnostic,
original summary and the absence of **all** comparisons and drift claims before
accepting that exception. A failure marker cannot excuse a surviving agreement,
disagreement or `query_first` claim. The ordinary reply invariants still reject
an invalid assembled result when encoded directly; the service reply boundary
alone constructs the degraded response.

If even the evidence-preserving response cannot be serialized, a minimal
reporting-failure reply retains run identity and the original summary, sets
`evidence_retained: false`, and explicitly diagnoses the additional encoding
failure. It contains no steps or subprocess objects. This final path does not
claim evidence preservation and never substitutes `{}`. These are host coding
failure paths tested with constructed results and an internal encoder fault;
there is no specimen override that fabricates them.

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

The response, request, controller envelope and worker ABI are separate
contracts, owned by [docs/contract.json](../docs/CONTRACT.md). Every new step explicitly encodes `deny_signal: null`;
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
structural-policy admission meaning. Published worker failures also use `runner_failed`; the operation/code record
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
`pid_match`; `permission_failures_without_record` names the steps whose attempt
the runner classified as a permission-shaped failure and that no captured event
names as a candidate, so `no_match` never reads as "nothing was denied" (null
when correlation was not reached or the reply has no per-step comparisons).
Abnormal/unconfirmed disposition has `termination_cause="unknown"`.
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
[operation mapping](../docs/PolicyWitness.md#denial-log-correlation) is part of the
public contract. An incomplete attempt can still be a candidate: a kernel event
can precede interrupted publication.

`capture.window` records the scanned interval, the runner client's own span
widened to whole seconds, and explicitly reports no structured event
timestamps, exact run membership, step ordering, or PID-reuse protection. The
observer mirrors the interval it scanned; any other interval is
`window_mismatch`, which retains raw observer evidence but never yields
`step_denies` or `first_deny`; correlation is `unavailable`. Reversed client clock
readings produce `invalid_window`, retaining the raw milliseconds with null
`start`/`end` and no observer invocation. Ordered endpoints do not establish clock
continuity. Validator queries can generate worker-PID denial records before
attempts begin, and some denied attempts have no available log record. Neither
path matching nor interval coverage establishes a record's origin or complete
log delivery.
Raw lines remain available. The observer preserves the full remaining target,
including spaces; it does not shorten a path into a different target. PID
matching alone never establishes a termination cause or exact run membership.

## Coverage audit and acceptance ownership

The entries below distinguish constructed host interpretation, actual C-worker
publication, and the CLI boundary. The host-driver, encoding and classifier
controls establish separate parts of the table. The
[consumer enforcement map](#permanent-consumer-enforcement) identifies the lasting
reporting obligations and registered test owners.

| Test entry | Production reach and current assertions | Acceptance owner / remaining obligation |
| --- | --- | --- |
| `runner_unit/pwrunner_core_unit_executable`: `HostOutcomeClassifierTests.runHostOutcomeClassifierTests` | Constructed `CWorkerOutput`/validator results; pins publication, deadline, disposition and precedence rows; no OS calls or worker publication | Implemented, independently of driver tests |
| Same catalog case: `EnvelopeInvariantTests.runEnvelopeInvariantTests` and `OrderingTests.runOrderingTests` | Constructed Codable results; current ordering/eligibility and explicit signal null, stored response-4/7 objects, subprocess absence and unknown vs observed false/empty, unfamiliar observation values | Implemented; actual client error replies also checked in smoke/runner_caller_auth |
| Same catalog case: `ReplyFailureTests.runReplyFailureTests` | Real service reply serializer with constructed invariant faults and internal encoder failure; every stored field has encoding coverage | Preserves diagnostic evidence and original summary, withholds comparisons; explicitly reports repeated encoding failure |
| Same catalog case: `CWorkerTests`, `late done during grace preserves sentinel deadline` | Real worker through Swift driver; late voluntary exit with no host kill and exit 0; records `sentinel_deadline`, reaped exit 0, and no termination request through actual subprocess encoding | Driver, final done/slot snapshot and runner_timeout classifier verified |
| Same catalog case: `CWorkerTests`, `postApplyKillSignal terminates worker before done -> runner_failed` | Real C worker self-signals; asserts applied/not-done/no-host-kill/SIGKILL, `child_reaped` and encoded process facts, then calls classifier | Driver plus runner_failed classifier verified; no real sandbox kill is established |
| Same catalog case: `CWorkerValidatorTests`, `postApplied hook does not fire when compile fails` | Real malformed SBPL through Swift driver; asserts no applied marker and zero hook calls | Driver control; `witness_contract/worker_progress_and_failure` separately verifies compiler diagnostic text at the CLI boundary |
| `runner_c_worker_harness/compile_failure` (`run_compile_failure`, `harness.c` scenario) | Real C worker: no ready byte, A=false, D=true, R=-1, no completed slot, exit 0 and no host kill | Retain actual publication/exit protection; not Swift interpretation or CLI forwarding |
| `runner_c_worker_harness` early-exit and success cases; `runner_abi_layout` | Actual C worker's early guards and attempts; independently compiled C layout compared with Swift constants | Complementary ABI/publication protection; ABI 7 layout and exact-version rejection |
| `witness_contract/pre_apply_failure_reports_no_policy_verdict` (`check_pre_apply_failure.py`) | Real CLI, populated allowed/denied plan, pre-ready delay and worker deadline; identical un-overridden positive control | Independent attribution, lifecycle, signal and consumer-recovery groups enforce at least response 8; missing channels remain distinct from observed failures |
| `runner_unit/pwrunner_core_unit_executable`: `CWorkerLifecycleTests.runCWorkerLifecycleTests` | Real host driver with test-only ABI child: completed report then cleanup SIGKILL, independent exit 17 or SIGTERM, published legacy failure then cleanup, failed kill, failed/recovered/interrupted wait, ECHILD ownership loss and poll EIO. Actual subprocess assembler and JSON round-trip preserve reports and missing status. Fixture applies no sandbox. | Driver, assembler, encoding and classifier agree; synthetic payload does not establish a native library result |
| `runner_ready_byte_resilience/slow_compile_ready_byte_survives_sigpipe` | Real CLI with sufficient budget; lost ready byte must not prevent successful application, prediction and attempt | Successful resilience verified; delay follows compilation/capture and has sufficient sentinel budget |
| `runner_outcome_runner_timeout/host_kills_hung_worker`, `witness_contract/worker_post_apply_hang_seam`, `runner_use_c_worker/worker_timeout_ms_honored` | Real CLI post-apply deadlines; empty, mixed and single-write plans, retained evidence and independently checked effects | Success/timeout/partial-evidence checks pass; populated pre-apply witness adds distinct absence coverage |
| `witness_contract/worker_termination_and_log_correlation`; Rust `run_flow::tests`, `sandbox_log::tests`, observer parser tests | CLI ordinary denied writes, repeated attempts, independent read queries, self-signal, capture disabled/enabled and successful-run capture. Constructed captures pin PID, operation, target, ambiguity, window and availability semantics. Parser preserves missing identity and full paths without structured timestamps. | Implemented; optional real logs do not replace deterministic populated-event controls or establish a policy cause |
| `runner_validator_failure/validator_unavailable_reports_degraded`, `runner_validator_failure/validator_decode_failure_reports_degraded` (also witness suite members) | Real worker attempts plus fixture validator, reversed partial IDs, missing verdict and null drift; malformed JSON is distinct from EOF | Missing prediction reasons and completed failures are independently recoverable; validator lifecycle/UTF-8/structure/association controls are described below |
| `runner_unit`: `SandboxApplyTests` | Calls the unused Swift apply helper, not the C producer | No production failure-reporting credit; helper/type/test cleanup is outside this effort; preserve live `computePolicyHash` |

Real-worker `CWorkerTests` cases guarded by `workerExists()` require
`<PW_APP_DIR>/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner`.
`CWorkerValidatorTests` live cases use that worker and the diagnostic app-level
`<PW_APP_DIR>/Contents/MacOS/sb_api_validator` (including the compile-failure
case's `bothBinariesExist()` guard). Production CLI orchestration uses the
bundle-local validator in the XPC service. Tests without `PW_APP_DIR` select
`dist/PolicyWitness.app`. Record those actual paths in retained provenance.

`TestKit.run` counts a guarded early return as passed; the shell wrapper rejects
internal `SKIP`/`FAIL`, checks the summary and requires its worker equipment.
Credit live rows only after inspecting bundle-integrity evidence and the retained
`pwrunner_core_tests.log`. Required live controls fail when their equipment is
missing. Constructed classifier/encoding cases have separate credit.
`source_drift` protects registry/outcome matrices.

## Worker evidence contract

The authoritative layout is `pw_probe_runner_abi.h::pw_shm_evidence_t`, appended
following the capture bytes. Host and worker require exactly the same ABI number, with no older fallback. Header offsets 56 and 60 carry proceed and proceed_observed, and the header is 64 bytes. The reply carries the ordering evidence described below; replies before schema 8 have none.
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
write, 8 application, 9 indexed attempt, 10 terminal completion, 11 proceed wait. Started means
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
| proceed wait starts; budget expires | Operation 11/code 8, budget milliseconds in detail, done; no acknowledgement or attempt, even after late release |
| proceed clock fails | Operation 11/code 1/native kind 3, actual return and errno; done, no attempts |
| release acknowledged; worker dies | Lifetime and eligible query order remain established; attempt evidence may be missing |
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
return such as an open FD. The worker ABI does not carry that raw return: native_rc is
null for attempts, including completed ones. Unsupported/skipped attempts use synthetic and
attempt_not_supported. Step errno/drift/signal absence retains its existing form.

### Acceptance observations fixed before implementation

Real success retains attempts/predictions without a failure; real syntax error
identifies compilation NULL and diagnostic; producer-controlled apply failure
retains native return/errno. Missing/incomplete publication exposes no payload.
Late publication retains slots and deadline. Unknown codes survive fixture →
real host → XPC → CLI. Never-invoked and short-reply validators differ; an
interrupted started attempt remains incomplete. Worker source rejection
and host EPIPE must coexist, closed-input controls must work without oversized
admission, and mapping failure preserves exit 3 without invented errno/cause.
Failures after completed real probes preserve independently checked effects.

### Policy-transfer failure

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
and uses the [host observation](#host-observations) grace/termination/reaping contract. All evidence reaches the
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

When validator `posix_spawn` returns nonzero, `validator_spawn_failure` retains
`origin: runner_host`, `operation: posix_spawn`, the exact `executable_path`,
numeric `return_code`, and native `strerror` text as `diagnostic`. The return code
is captured directly, independently of ambient errno, with no recognized-code
allowlist or diagnostic-string classification. Unknown codes remain failures.
No validator PID or subprocess is invented. Collection closes and releases the
worker normally; missing predictions remain unestablished with null drift.
The record survives worker-summary precedence and evidence-preserving reply
degradation. The explicit `evidence_retained: false` backstop may omit it along
with the other observations. This optional field is additive;
absence in older replies is unknown. The controller forwards it unchanged.
The live ENOENT witness checks the native code, path and call context without
requiring English wording. Internal native-call controls exercise unfamiliar
returns through orchestration and reply serialization; they are not policy
evidence and no request override selects them.

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

`steps[].sandbox_check.pid` is the spawned worker PID, or explicit null when no
worker exists. It never substitutes the host PID. Typed readers must accept
null; replies before schema 6 carry an integer PID and remain decodable. The
top-level legacy PID convention is unchanged. Request schema and worker ABI are
separate contracts.

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

Deny plus ambiguous EPERM/EACCES has `drift=null`. A matching submitted scope
can retain directional consistency in `comparison`; a separate query target
prevents that comparison. The direct DAC control remains test-owned evidence,
not a runtime observation used to assign the cause.


## Unfamiliar diagnostic preservation controls

Open values do not require a production code registration. Two distinct worker
payloads are checked against independent fixture inputs through C publication,
Swift decoding and encoding, XPC client forwarding and Rust reception. The worker
producer/domain is the containing worker PID and worker ABI channel; JSON diagnostic
records additionally exercise explicit producer/domain/operation/code/detail.
Known operation/native-result fields survive an unfamiliar diagnostic code. The
fixture supplies these values, including errno; it does not establish that the
named native calls ran. Unknown operation names do not imply a compile/apply or
sandbox cause.

Absent/unpublished payloads remain unavailable; structural failures and an
incompatible version word remain rejected. Truncated or invalid text does not
erase a valid numeric failure. A host EPIPE remains independently visible beside
a worker record. Two valid validator diagnostics survive alongside a known
UTF-8 receiver fault, a fixture-supplied allow record and an independently checked
file change from the real worker. The transcript producer does not call
`sandbox_check`; its allow record tests forwarding of declared native-result
fields, not native verdict attribution. A shared envelope does not establish a
causal relationship between the retained records.
Legitimate per-step diagnostics with clean transport retain the existing run
semantics; an unfamiliar name alone does not create a run failure.

Rust subprocess controls compare complete received JSON for all three capture
paths, including unfamiliar diagnostics beside fixture-supplied failed reports. Local
truncation precludes parsing and cannot be mistaken for diagnostic rejection.
These helper controls test receiver transport; they do not manufacture real
XPC loss, helper compilation failure or kernel log output. The normal worker
success/failure controls continue to establish native attribution separately.

See [fixture documentation](fixtures/diagnostic_transport/README.md) for fixture boundaries and
`witness_contract/unfamiliar_diagnostic_transport` for CLI assertions. Temporary
code-filtering and detail-dropping mutations are test experiments only; source
and the signed app must be restored before acceptance.

## Derived comparisons and evidence joins

### Claim/evidence review

| Join / observation owners | Association and phase guarantee | Counterexample / limit | Supported public conclusion |
| --- | --- | --- | --- |
| Submitted query → validator record; host and validator | Unique step ID plus exact submitted operation/filter tuple; host invokes validator after observing worker application | A correctly associated query for A need not concern attempted B; a late validator can query changed state | The record answers the submitted query, not necessarily the attempt |
| Query → attempt; host request and completed worker slot | Host retains both independently supplied inputs and pairs by unique step ID | Different operations/targets; compound create; broad or unscoped query; same path spelling with different runtime resolution | An explicit relation between submitted operations/targets, separately from an outcome comparison |
| Query time → attempt time; host and two children | Application → closed query collection → host release → worker acknowledgement → attempts; eligible uniquely associated native records acquire query_first | External state can change during the interval; earlier attempts can affect later attempts | Established order for eligible records, without stable state or runtime identity claims |
| Path enrichment → query/attempt; runner host | Host resolves submitted query path after the orchestrator returns | Worker unlinks the path before host resolution; host and sandboxed worker can resolve differently | Later host diagnostic, never an earlier validator/worker observation |
| Denial event → attempt; observer and controller | Exact worker PID, mapped submitted operation and matching path evidence yield candidates | Repeated attempts, PID reuse, whole-second capture bounds and absent timestamps prevent unique occurrence or causal ordering | Candidate association with inspectable matching basis; no termination cause and no negative proof from no match |
| Test control → runtime interpretation; test harness and PW | Controls can establish expected meanings independently of the classifier | Direct unsandboxed execution or a fixture oracle is not an observation available in a normal PW envelope | Credit controlled interpretation separately from native observation; no test knowledge silently becomes runtime attribution |

### Consumer-question baseline and design dispositions

These IDs and their scope precede representation selection. Wording changes must
preserve the original obligation; narrowing, merging or changing a disposition
requires a recorded design reason. Current output omissions do not prove runtime
ignorance. Submitted kind/action describes intent; it does not prove execution.

| ID | Original consumer question | Required disposition under the chosen contract |
| --- | --- | --- |
| C1 | Which steps report established agreement, and what comparison does that claim cover? | Recover supported allow/success agreement for matching submitted scope, separately from directional consistency and unavailable comparison. Disagreement requires evidence excluding material alternative explanations; order alone cannot supply state or runtime identity evidence. Agreement does not certify synchronized state. |
| C2 | Which steps observed a failure whose cause PW could not attribute to the sandbox? | Recover observed permission/other failures with unestablished sandbox attribution separately from missing worker results. Native numbers and errors survive. |
| C3 | What relationship between each query and attempt was established, known to differ, or left unresolved? | Report submitted operation and target relations, with submitted kind/action retained. Runtime object identity, complete check coverage and temporal equivalence remain limited where unobserved. |
| C4 | Which steps produced no comparison, and what known reasons limit it? | Recover all known missing/unusable, scope and attribution limits, allowing simultaneous reasons; retain underlying missing_reason and native observations. |
| C5 | Which path resolutions were later host observations? | Mark path diagnostics with observer and phase; absence in older replies does not invent provenance. |
| C6 | Which denial events are candidates for a step, and what association or capture limits remain? | Keep event references and capture limitations; add per-candidate matched operation/path evidence with provenance from the submitted request or worker reply. Unique occurrence and causal attribution remain unestablished. |

All six require delivered reporting changes; none is closed by a current omission.
The limits above reflect absent synchronization/identity/causal observations.
They do not permit discarding known request relations, native failures or capture
status.

### Accepted consumer answers and their evidence

The six questions retain their original scope. The following judgments separate
what the observations justify from whether the envelope makes that judgment
recoverable. A readable label alone does not justify its claim. Controlled
policies, submitted inputs, direct permission checks, file contents and executable
markers supply the test expectations; none becomes additional runtime evidence
available to a JSON consumer.

| Controlled scenario | Accepted answer / questions | Evidence and assumption | Stronger conclusion excluded |
| --- | --- | --- | --- |
| Same submitted file scope, supplied allow or deny verdict, successful read | Agreement or unavailable respectively; even established query order cannot discharge the state/identity obligations, and scope and state/identity limits survive (C1/C3/C4) | Fixture verdict plus real worker read and independently retained file contents; interpretation control, not native prediction validation | Synchronized enforcement agreement, causal contradiction, or a libsandbox bug |
| Planned path query and worker-reported successful unlink of that submitted target, in any step of the run, with unestablished query order | Retain mutation uncertainty; successful corresponding attempts yield unavailable/null under either prediction (C1/C3/C4) | Completed worker unlink status and submitted target equality, independently of later host resolution | Removal is proved to precede the query, or recreation restores runtime identity |
| Allow or deny verdict, same locked file, failed read | Unavailable or directional consistency respectively; permission failure with unestablished cause (C1/C2/C4) | Direct unsandboxed EACCES control and real worker failure; the test knows DAC prevented access | Runtime proof that DAC or the sandbox caused this particular failure; directional consistency is not agreement |
| Different submitted target or operation, including denied query A and successful spawn B | Preserve the known difference and successful observation; comparison unavailable (C1/C3/C4) | Independently supplied query/attempt inputs and actual worker effects | Host canonicalization repairs the relation, or two different strings prove different runtime objects |
| Compound create or unsupported attempt | Preserve unresolved operation/scope; distinguish completed create from absent supported attempt result (C2/C3/C4) | Submitted action and worker publication/missing reason | A single query covers the compound operation; missing result proves no operation started |
| Absent query path with failed attempt, or with successful attempt at another path | Retain planning exclusion, missing prediction, failure attribution or differing target simultaneously (C2/C3/C4) | Owned absent path, direct file control and independently submitted attempt target | One reason explains away another; later host resolution supplies a missing validator observation |
| Native exec query and same-target successful spawn, including child exit 37 | Agreement about target execution admission; a failed exec result after spawning remains separately recoverable with unestablished cause (C1/C2/C3/C4) | Native `process-exec*` query, positive worker child PID, helper marker and direct exit-code control | Complete spawn prediction, successful child completion, or a known cause for the failed exec result |
| Native exec allowed but fork or interpreter denied | Preserve allow query and failed spawn; comparison unavailable and full-spawn coverage limited (C1/C2/C3/C4) | Independently varied policies, native query, real spawn attempt | Allow target admission promises spawn success; test-controlled policy intervention proves runtime attribution |
| Native target exec denied and permission-shaped spawn failure | Directional consistency with unestablished cause (C1/C2/C4) | Native query and worker failure; no successful spawn observation | Proven target-admission denial from the failure alone |
| Interpreter query against binary spawn; unsupported bare exec query | Different operation and, for the bare query, unusable prediction remain explicit (C3/C4) | Native interpreter counterexample and native bare-query error | Accepted query spelling alone establishes operation correspondence |
| Validator missing while worker completes, or worker has no completed result | Preserve the independent channel, missing reason and every other known limit (C2/C4) | Controlled EOF/deadline and real worker publication/file evidence | Missing worker result is an observed permission failure; missing prediction erases a completed attempt |
| Query planning intentionally excludes sysctl prediction | Report planning exclusion and missing query alongside the observed attempt (C3/C4) | Submitted sysctl query and native attempt; documented unsupported prediction pair | A synthetic status is a native verdict |
| Host path diagnostics after orchestration | Report their host owner and phase, whether resolution succeeds or fails (C5) | Host instrumentation and the controlled unlink/late-resolution scenario | Validator/worker observation, stable runtime identity, or proof both children had been reaped |
| Repeated denied attempts and a captured matching event | Return the event reference, every candidate and its operation/path provenance; preserve capture window limits (C6) | Native CLI/log control plus deterministic correlation controls | Unique occurrence, step ordering, or cause of an unrelated worker signal |
| One candidate, no matching event, unavailable/disabled capture, or no worker | Keep these distinct, including raw unmatched events and capture diagnostics (C6) | Deterministic receiver controls and live disabled/captured observations | One candidate is a unique occurrence; no match or no capture proves no denial |
| Older reply without comparison or provenance | Return not reported for absent distinctions, preserving old drift and raw observations (C1–C5); recover any independently present controller correlation (C6) | Stored legacy replies and version-aware decoding controls | Reclassifying legacy drift under response-7 semantics, inventing provenance, or suppressing controller evidence because the runner is old |

C2 includes failed exec results after successful spawning. The consumer must not
select only `permission_failure` and `other_failure`: `exec_result_failed_after_spawn`
also identifies a failed result while `observation=succeeded` still describes the
spawn. Preserve the native attempt fields in either case. Missing completed
results belong in a separate answer, not in the observed-failure set. This makes
the original failure question explicit; it does not narrow it to one summary field.

C4 distinguishes an unavailable comparison from directional consistency, which
is a useful but limited reported conclusion. Both may project to null drift.
Recover the complete limitations array, the prediction/attempt missing reasons,
and their raw observations without choosing a principal cause. No admitted steps
and no runner reply are run-level absences, not evidence of agreement or an
invented missing step.

C5 and C6 preserve an explicit not-reported state separately from a reported
negative, empty candidate set or disabled capture. Path provenance and denial
correlation are independent channels: even an old runner reply may carry new
controller matching evidence. Candidate event indices resolve within the same
envelope, including unmatched events; they require no external log access.

Intentionally unsettled by these answers are synchronized query/attempt state,
runtime object identity, complete spawn preconditions, the cause of an individual
failed result, and unique or causal log occurrence. The product does not observe
enough to answer those portions. The contract nevertheless requires reporting
every known submitted relation, observation, failure, missing reason and capture
limit; blanket unknown would discard supported information. JSON recovery tests
enforce that reporting obligation, not a general proof of causal correctness.

### Public representation and meaning

`comparison.order` is `query_first` only when the host closed collection before
storing release, the worker acknowledged release after successful application,
worker ownership was retained through acknowledgement, and a unique native
allow/deny record matches the exact planned query tuple with coherent rc/errno.
All other records retain `unestablished`. Death before acknowledgement cannot
certify policy lifetime; death or cleanup failure afterwards does not erase
established order. Queries are never launched against a reaped worker.

`runner_subprocess.ordering` is present exactly when the worker subprocess object
is present. It records `collection_closed_before_proceed`, `proceed_set`,
`proceed_observed`, `worker_lifetime_established`, `validator_disposition` and
`protocol_violations`. The first two observations belong to the host; acknowledgement
is a worker publication acquired by the host. False means not established,
not proof of nonoccurrence. Contradictory observations remain visible, carry
protocol violations, and establish no order.

Validator disposition is `not_invoked`, `not_needed` (empty query plan),
`not_spawned` (setup/spawn failure), `reaped`, or `unconfirmed`. Collection closes
when the synchronous driver returns, even after partial output, decode failure,
I/O expiry or failed cleanup. The host then releases attempts. No later record
can enter predictions; `unconfirmed` does not mean the validator has exited.
Eligible partial records can therefore retain `query_first`. Every emitted step
has order even when predictions are excluded or missing; those steps still obey
the release barrier. Legacy decodes gain neither field.

Queries form an interval before the first attempt, not per-step interleaving or
a shared snapshot. External activity may change targets during that interval;
earlier attempts may affect later attempts. State stability and path identity
remain unestablished. No current producer path can yield `disagreement` or
`drift: true`: the typed evidence model has no established state/identity cases,
and the encoder and consumers reject that unsupported claim even with empty
limitations.

The ordering promise covers PolicyWitness's own actions only. It does not
promise that a target's state is unchanged between a query and its attempt,
that a path spelling names the same runtime object at both times, that a query
was requested for every step (planning exclusions keep their `missing_reason`),
a comparison for attempts whose prediction was excluded or never returned, or
any per-step interleaving. Collection closure, not confirmed validator
termination, is the release condition: a validator that survives cleanup may
keep querying, but none of its later records is collected or used.

#### Ordering evidence states

C/S/O are `collection_closed_before_proceed`, `proceed_set` and
`proceed_observed`. Rows give the final observations for each scenario.

| Scenario | C/S/O | Validator disposition | Per-step order |
| --- | --- | --- | --- |
| No worker spawned | No ordering object | No snapshot | `unestablished` on any emitted step |
| Worker exists, application not confirmed | false/false/false | `not_invoked` | `unestablished` |
| Applied, no planned queries, release acknowledged | true/true/true | `not_needed` | `unestablished`; no prediction exists |
| Setup/spawn failed, release acknowledged | true/true/true | `not_spawned` | `unestablished`; the failure is retained in `validator_spawn_failure` |
| Eligible records, release acknowledged | true/true/true | `reaped` or `unconfirmed` | `query_first` for eligible records only |
| Partial, diagnostic or rejected records, release acknowledged | true/true/true | `reaped` or `unconfirmed` | `query_first` only for eligible associated records; all others `unestablished` |
| Proceed expired or worker died before acknowledgement; hook later returned | true/true/false | actual terminal disposition | `unestablished`; received records survive |
| Worker died or hung after acknowledgement | true/true/true | actual terminal disposition | eligible records retain `query_first`; missing attempts remain unavailable |

Consumers reject `query_first` without every prerequisite, with the order
limitation still present, or on a synthetic or diagnostic record, and reject
`unestablished` for an eligible record whose full chain is established. Release
without collection closure, acknowledgement without release, and release before
successful application are protocol violations: the raw sentinels stay visible,
`protocol_violations` names the contradiction, and no order is derived.

#### Ordering protocol names

| Thing | Name | Where |
| --- | --- | --- |
| Release sentinel | `proceed` | shared-memory header offset 56 |
| Acknowledgement sentinel | `proceed_observed` | shared-memory header offset 60 |
| Worker operation | `PW_OP_PROCEED` = 11 | `pw_probe_runner_abi.h` |
| Worker failure | `PW_FAILURE_PROCEED_TIMEOUT` = 8; clock failure is `PW_FAILURE_NATIVE` with kind `PW_NATIVE_CLOCK` = 3 | `pw_probe_runner_abi.h` |
| Worker budget | `PW_PROCEED_WAIT_MS_DEFAULT`, limit id `worker_proceed_wait` | `pw_probe_runner.c`, `docs/limits.json` |
| Worker argv seam | `--proceed-wait-ms` | C harness only; no request override |
| Request override | `validator_io_timeout_ms` | `PWRunnerTestOverrides` |
| Run-level evidence | `runner_subprocess.ordering` | reply; absent before schema 8 |
| Per-step evidence | `comparison.order` | reply; absent before schema 8 |
| Host reply failure | `runner_reporting_failed`, `reporting_failure` | reply, absent before schema 8; comparisons absent, drift null |
| Failed validator launch | `validator_spawn_failure` | reply; optional and additive |
| Unordered limitations | `attempt_mutation_order_unestablished`, `host_path_resolution_changed` | reply; absent before schema 7 |
| Native gated validator | `tests/fixtures/validator/bridge.m`, suite `validator_bridge` | test equipment |


Each new step contains `comparison` with `scope="submitted_operation_and_target"`,
`prediction` (allow/deny/unavailable), `observation`
(succeeded/permission_failure/other_failure/unavailable), `observation_basis`,
`operation_relation` (matched/different/unresolved), `target_relation`
(same_submitted/different_submitted/unresolved), `conclusion`
(agreement/disagreement/directional_consistency/unavailable), and `limitations`.
The host supplies `attempt.requested_kind` and `requested_action`; existing
`requested_path` is the submitted target. These are input provenance, not native
call observations. `result_source`, native fields, child status and missing reasons
retain their independent meanings.

Only a supported operation mapping, compatible filter and identical submitted target
permit the limited comparison. The reviewed mappings are file open_read/access →
file-read-data, open_write → file-write-data, unlink → file-write-unlink;
exec spawn → process-exec* (target execution admission); mach lookup → mach-lookup;
sysctl read → sysctl-read.
File/exec require path filters; mach lookup requires global_name (local namespace
equivalence is not established); sysctl requires sysctl_name. Other broad query names,
NONE filters and compound create attempts retain unresolved scope, not inferred
equivalence. Different strings establish different submitted targets, not distinct
runtime objects. Later host canonicalization never certifies comparability.

For exec, `process-exec*` is the native query spelling corresponding to target
execution admission; bare `process-exec` is rejected by the native prediction
channel on the tested system. This specific mapping does not generalize from
the presence of a star or from acceptance of an operation name. In particular,
`process-exec-interpreter` can predict deny while a binary spawns successfully.
The exec mapping carries `exec_query_not_full_spawn_prediction`: fork permission,
interpreter admission, executable format and other spawn requirements are outside
the query's promised scope. An allow prediction does not promise spawn success.
A successful spawn supplies the target-execution observation needed for a
comparison; a failed spawn does not establish that this particular gate denied it.

The native `runner_exec_dac` control exercises this distinction through ordinary
CLI runs with real policies, validator calls and worker attempts. Independently
changing exec, fork and interpreter permissions separates their verdicts and
effects. A same-target allow/spawn-success comparison reports agreement, including
a helper that prints its marker then exits 37. A denied query for a different
target retains the successful attempt without reporting disagreement. None of
these test-controlled interventions becomes causal evidence in a user's envelope.
The source-level worker observation remains the successful `posix_spawn` return
that publishes `child_pid`; it is not inferred from the helper's exit code.

`drift=false` projects `comparison.conclusion=agreement`: an allow prediction and
completed successful attempt within that submitted scope, without a supported
unordered target mutation. This agreement does not certify runtime identity or
equal state. `drift=true` projects `disagreement` and is reserved for differing
kernel enforcement with no supported or materially unresolved alternative
explanation. It requires usable native prediction and attempt evidence, query
order and worker policy context, corresponding operation and runtime target,
and sufficient evidence about state, query coverage and other enforcement
mechanisms. Identical submitted paths and absent captured denies are insufficient.
Established query order alone cannot exclude state changes or runtime target ambiguity, so every deny/success difference yields `unavailable`/null. No current producer path yields `drift=true`.
An exec child that ran
and then failed supplies spawn success independently of its later exit outcome.
It also retains `exec_result_failed_after_spawn` and `sandbox_attribution_unestablished`: a
useful spawn comparison cannot erase a failed exec result. That result may
reflect child exit, timeout or collection failure; it does not alone establish
a native child failure or its cause.
`drift=null` covers all other conclusions. Deny plus permission failure can retain
`directional_consistency` when scope matches, but cannot establish agreement.
Permission numbers (including Mach permission failure) do not alone establish a
sandbox cause. Unrecognized sysctl errors never become strong denial evidence.
No current failed-attempt path establishes attributable sandbox denial.

Every comparison reports `state_stability_unestablished`; `query_attempt_order_unestablished` appears exactly when `comparison.order` is not `query_first`. Path comparisons also report
`runtime_target_identity_unestablished`. Additional limits report unresolved or
different operations/targets, unavailable predictions/attempts, unusable verdicts
broad query operations, unsupported filter scope, absent submitted targets
and unestablished failure attribution independently, without suppressing another
known reason. A `query_plan:` limitation retains the host's known exclusion:
`prediction_unavailable_pair`, `unrecognized_filter_kind` or
`path_unresolved_at_planning`. This planning observation remains separate from
`prediction:query_not_requested`, native errors and later host path enrichment.
The documented derivation permits recovery without reimplementing
the classifier. A synthetic record cannot acquire a native observation by its label.

`attempt_mutation_order_unestablished` requires a planned path query and a
worker-reported successful (`rc=0`, `outcome=ok`) file/unlink of that submitted
target in any step of the run whose query order is unestablished. Established query order removes this confound and restores allow/success agreement; it does not establish drift. Step position does not bound it: with order
unestablished the worker can finish every attempt before the first query, so a
later step's unlink can precede an earlier step's query. Unknown order makes
this a material confound for both allow/success agreement and deny/success
disagreement. Other
targets, failed/synthetic unlink results, content writes and create-if-absent
do not supply that observation. Later recreation does not erase it.
`host_path_resolution_changed` separately records planned host resolution
followed by failed host resolution after orchestration. Enrichment appends it
only to an existing comparison with no planning exclusion; it never changes
conclusion or drift and never supplies query-time state.

| Observation basis | Supporting fields and limited meaning |
| --- | --- |
| `completed_worker_status` | Completed worker result: `attempt.outcome` and PW status `rc`; this is not a raw syscall return or a causal explanation |
| `permission_errno` | Worker-reported EPERM/EACCES on a file/access/unlink/sysctl/failed-spawn result; the permission-shaped failure does not identify the enforcing mechanism |
| `bootstrap_permission_result` | The worker's exact `bootstrap_look_up: kr=1100` report; different calls or numbers do not acquire this interpretation, and sandbox attribution remains unestablished |
| `spawned_child` | Positive `attempt.child_pid` in a completed worker result establishes spawning independently of the child's later outcome |
| `no_completed_worker_result` | Missing/synthetic/incomplete result; neither a native return nor proof the attempt never started |


Path diagnostics retain their fields and add `observer="runner_host"` and
`phase="after_orchestration"`. These provenance fields remain absent when decoding
older records. Denial candidates add matching evidence without changing their
candidate-only meaning; optional logs cannot change PW status or `drift`.
Matching evidence identifies submitted operation provenance and every matched
`submitted_attempt.target`, `attempt.requested_path` or `attempt.observed_path`.
An unowned legacy `normalized_path` alone no longer admits a candidate; its raw
value is retained in the runner reply. This controller correlation correction
also applies when consuming older runner replies without rewriting their version.

### Permanent consumer enforcement

The original C1–C6 obligations all retain their scope. Their design justification
and deliberately unanswerable portions are recorded in the accepted-answer table
above; passing a recovery test does not independently prove a causal judgment.
`tests/lib/consumer.py` reads only a single JSON envelope. It groups reported
conclusions and failures, retains raw channel observations and all limitations,
and resolves denial references within that envelope. It reads no specimen,
external log, native errno rules or private classifier. Scenario expectations
remain in the tests that own the controlled inputs and independent observations.

| Question | Permanent registered owners and enforced distinctions | Accepted limit |
| --- | --- | --- |
| C1 | `witness_contract/drift_determination_via_validator_seam`: all four conclusion groups from supplied verdicts and real file controls; `runner_exec_dac/execute_permission_is_not_sandbox_drift`: native admission/spawn comparisons; `blackbox_e2e/checker_controls`: reject blanket unknown that erases supported agreement | Recorded submitted-scope comparison, without synchronized-state or causal proof |
| C2 | Comparison witness: permission/other failures versus absent result; native exec case: failed child result remains beside successful spawn; pre-apply and both validator-failure CLI cases: missing channel never erases the other; `runner_unit/pwrunner_core_unit_executable`: `EnvelopeInvariantTests` retains native fields through Codable | Cause of a failed result remains unestablished, even where the test controls a known cause |
| C3 | Comparison witness and `witness_contract/prediction_target_is_independent_of_attempt_target`: independent target/operation relations and submitted intent; native exec counterexamples; shared checker requires intent fields from response 7 onward | Submitted relation does not establish runtime object identity or full operation coverage |
| C4 | Comparison witness, `witness_contract/pre_apply_failure_reports_no_policy_verdict`, both `runner_validator_failure` CLI cases and `runner_filter_sysctl_name/prediction_unavailable_attempt_observed`: simultaneous limits and distinct missing reasons survive alongside raw observations; Swift encoding retains the whole limitations array including unfamiliar values | Several limits can coexist; no principal cause is inferred |
| C5 | Comparison witness and `runner_unit`'s `DriftClassifierTests`/`EnvelopeInvariantTests`: later host enrichment and old-record absence survive encoding; shared blackbox checker rejects validator ownership or wrong phase on new host diagnostics | No earlier validator/worker observation or reaping guarantee follows from later host resolution |
| C6 | `witness_contract/worker_termination_and_log_correlation`: live repeated candidates and matching provenance; `unit/rust.unit`'s `run_flow`/`sandbox_log` tests: serialized event indices, candidate multiplicity, capture limits and old-runner/new-controller independence; blackbox controls recover populated, unmatched, unavailable and disabled captures | Candidates are not unique occurrences or causes; absent/no-match capture supplies no negative proof |

`unit/rust.unit` also exercises `runner_client` transport with response versions
4–8, preserving complete received JSON, native child failure and unfamiliar limits.
Swift legacy controls preserve original drift and do not invent comparison, intent
or path provenance. `blackbox_e2e/checker_controls` exercises JSON recovery for
versions 4–6, independent newer controller evidence, no admitted steps and no reply.
The shared blackbox checker enforces the comparison shape introduced in response 7 and blanket temporal
limits on legacy replies. From response 8 it checks conditional ordering evidence,
native-record eligibility and the prohibition on disagreement. A validated
`reporting_failure` reply instead requires absent comparisons and explicit null
drift, and retains unvalidated ordering observations for diagnosis. Both versions
require attribution limits, explicit drift projection and host-path ownership;
the checker does not reconstruct the full prediction/attempt decision procedure. Indirect blackbox and
filter consumers, including BYOXPC cases, exercise the same guarantees.

`validate_current_build_evidence` is an explicit producer-conformance check:
it rejects current disagreement claims, unsupported or missing mutation and
resolution-change limitations, and agreement in the presence of a reported
unordered target mutation anywhere in the run. The new unlink witness and supplied-verdict controls use it; offline
checker controls retain accepted and rejected envelopes. It is separate from
`validate_evidence_shape` and `recover_evidence`, which preserve historical
response-7 disagreements without silently applying current-build rules.

Live comparison, native-exec, pre-apply, validator-failure and log-correlation
witnesses require at least response 8 before relying on version-gated checks.
The three live filter callers pass `--minimum-schema-version 8` to their
adapter. Its offline controls accept legacy fixtures without that requirement,
reject older/missing/invalid versions when it is supplied, and reject missing
comparison/intent evidence on current replies. Compatibility with stored replies
cannot substitute for checking the current producer's contract.

The blackbox checker controls reject losses through the actual checker CLI or
the same single-envelope recovery helper used by live cases: missing intent,
temporal/attribution evidence, a single missing concurrent scope limit, failed
exec evidence after spawning, matching provenance, invented exact run membership,
host data presented as validator data and blanket unknown. Each negative control
retains its mutated envelope and rejection evidence; positive controls run beside
it. These are reporting-regression controls, not new native causal experiments.
No permanent test reads an execution plan, audit document or acceptance output.

### Compatibility and acceptance gate

Response schema is **8**, request schema **1**, and worker ABI **7**. Current
responses require per-step order and worker ordering observations. The ABI adds
release and acknowledgement in the two reserved header words; capacities and
other offsets are unchanged. The worker release wait is inventoried in
[Limits](../docs/LIMITS.md).

Stored versions 4–7 preserve their original drift values and absence of new
fields. Historical response-7 disagreement means deny/success despite unresolved
order, state and identity. That legacy projection remains decodable; from response 8 the encoder
rejects disagreement outright because no vocabulary for established state or
runtime identity exists. Dropping limitation strings cannot manufacture evidence.
The Rust controller preserves response versions and unfamiliar order strings.

Acceptance selects every registered canonical case in [the catalog](catalog.json),
including opt-ins and both runner contexts. Required skips/unrun cases prevent
completion.

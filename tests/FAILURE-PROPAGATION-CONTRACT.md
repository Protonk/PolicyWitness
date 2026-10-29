# Failure evidence contract

This contract specifies host observations, diagnostic preservation and derived
comparisons: worker ABI publications and the runner reply.
Worker records, diagnostic text, late publications and policy-transfer partial
outputs preserve independently observed facts through to the CLI.

## Evidence and classification

`normalized_outcome` summarizes PW execution. It does not report a policy access
decision or establish why a signal was delivered. All independently confirmed
worker slots, validator verdicts and process observations
survive regardless of which observation determines the summary.

In the table, A means an acquire observation of `applied`, D an acquire
observation of `done`, and R the `apply_rc` status word. A publishes successful
application; D publishes a terminal worker payload, including pre-apply failure.
The worker erases accepted token storage before publishing D and exits without
waiting for the host's exit request. The host retains its evidence mapping and
observes process disposition independently. Cancellation and early returns do
not add D or other publications absent from those paths.
R is not a native apply result merely because of its name. Parameter allocation,
parameter setting, the defensive parameter NUL check, and compilation can all
write -1. `apply_errno` is populated only for an actual failed application, but
zero does not distinguish compilation, parameter setup, or application failure.
No library result may be inferred from unpublished storage. The parameter NUL
check follows forced termination of the strings and is not credited as a
reliably reachable specimen failure.

For a published status-word failure (no failure record), retain R and any
nonzero `apply_errno` in the runner's `error` diagnostic as published status
values, without calling R an observed apply/compile return. Worker failure
records identify the failed operation and its native result independently of
this storage. The controller retains this diagnostic unchanged; subprocess fields below
separately preserve cleanup observations. For an unpublished payload, neither
the diagnostic nor a structured object may expose its storage as a call result.

Rows describing process status require `waitpid` to return the child's PID.
Neither initialized wait storage nor a successful termination request supplies
that status. A last confirmed publication does not identify the instruction at
which the child stopped.

| Observations | Required account | Summary |
| --- | --- | --- |
| Proceed wait expiry (operation 11, code 8) or local timing refusal (operation 11, code 14) | Preserve budget or reason detail/diagnostic and zero attempts for that phase; late release cannot revive | `runner_failed` |
| Clock setup refusal (operation 12) | Preserve the native Mach return or local reason; A=false, D=false, R untouched, reaped exit 12; no receipt, application or action | `runner_failed` |
| Death awaiting release | Preserve disposition/progress without inventing a failure record or policy cause | `runner_failed` |
| Valid worker failure publication | Retain operation/code/native result, optional text, and independent host observations | `runner_failed` |
| Incomplete or malformed worker failure publication | Do not expose unpublished fields or infer a library result | `runner_failed` |
| No worker spawned | Retain the host admission/setup/spawn error; no worker report or subprocess object | Existing applicable host outcome |
| A=false, D=false; arbitrary R/errno storage | No published application or failure result; ignore R/errno | Use independently observed deadline or disposition below; never an application-failure claim |
| A=false, D=true, R nonzero | Worker published a preparation/application failure through the status word only; precise failed operation and native return unavailable | `runner_failed`; describe a published status-word failure, without saying an apply or compile call returned R |
| A=false, D=true, R=0 | Inconsistent terminal publication; not evidence of successful application or a library failure | `runner_failed` |
| A=true, published R nonzero | Inconsistent successful-application marker and status; preserve flags, do not choose a library cause | `runner_failed` |
| No terminal report; pre-apply child reaped with exit 0 | Incomplete reporting and observed clean exit; cause unknown | `runner_failed`, not a timeout |
| No terminal report; pre-apply child reaped with nonzero exit | Incomplete reporting and observed exit code; no invented library result | `runner_failed` |
| No terminal report; pre-apply child reaped with signal | Incomplete reporting and observed signal; no policy attribution | `runner_failed` |
| No terminal report; no successful reap or confirmed deadline | Incomplete reporting, unconfirmed process disposition, and any wait/cleanup errors; no invented exit status or cause | `runner_failed` |
| A=true, D=false; child exits or signals before a deadline is observed | Successful application, any completed slots/verdicts, incomplete report, actual disposition | `runner_failed`; signal is not a sandbox verdict |
| Polling exhausts its sentinel budget, then child voluntarily exits during grace | Observed deadline survives independently of exit 0 and absence of a kill request | `runner_timeout` |
| Polling exhausts its sentinel budget, then host requests termination | Deadline, request, call result, and any reaped status remain distinct | `runner_timeout`, including when kill/reap fails |
| Published status-word failure followed by observed deadline, cleanup kill, or failed kill/reap | Keep the reported failure and every subsequent host observation | `runner_failed`; cleanup does not replace the earlier report |
| A=true, D=true, R=0; exit grace expires and host requests termination | Completed report/slots survive; record cleanup request and result without inventing a sentinel deadline | `runner_failed`, even if the child subsequently exits 0 |
| A=true, D=true, R=0; independently reaped nonzero exit or signal | Completed report/slots survive alongside abnormal disposition | `runner_failed` |
| A=true, D=true, R=0; disposition unconfirmed or unrecovered wait error | Completed report/slots survive; exit/signal absent unless reaped | `runner_failed` |
| A=true, D=true, R=0; reaped exit 0, no unresolved host fault or termination request | Worker completion confirmed; evaluate validator observations | Existing validator mapping, or `ok` when required evidence is complete |

Summary precedence is: host rejection before spawn; published worker failure;
host transfer failure; incomplete/malformed failure publication; inconsistent published
worker state; published status-word worker failure; observed sentinel expiry; other
worker incompletion/abnormal disposition/unresolved host error; validator
failure; `ok`. A recovered EINTR alone is not a failed run. A cleanup request
without an observed sentinel expiry is not a timeout. This ordering selects
the summary only; it does not discard another observer's evidence. The validator
lifecycle and record-association requirements below also apply before `ok`.

## Reply construction failure

The reply boundary distinguishes a host reporting failure from the execution summary.
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
is omitted. The original summary is diagnostic,
not a second authoritative outcome. Retained ordering fields are diagnostic
observations; no per-step order is certified by this reply.

This is the sole exception to mandatory comparisons and complete
ordering objects. Consumers require the failure outcome, nonempty diagnostic,
original summary and the absence of **all** comparisons before accepting that
exception. A failure marker cannot excuse a surviving `query_first` claim. The ordinary reply invariants still reject
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
[PWRunnerLifecycleEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerLifecycleEvidence.swift) and
[CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift).
They are host observations, not a new worker ABI or a fabricated worker failure
record. Internal `CWorkerOutput` carries the same facts to the assembler.

| JSON location under `runner_subprocess` | Producer, type and validity |
| --- | --- |
| `pid` | Existing host-observed spawned PID; JSON integer |
| `exit_code`, `term_signal` | Existing JSON nullable integers, decoded only after successful reaping; both absent/null if no status obtained |
| `partial_steps` | Existing host summary of missing completed slots; does not prove an attempt never started |
| `ready_byte_received` | Host boolean: a byte was actually read; false supplies no compile/apply result |
| `done_observed` | Host boolean from the final acquire snapshot after cleanup |
| `poll_stop_reason` | Host string: `done`, `child_reaped`, `sentinel_deadline`, `wait_error`, `policy_write_error`, or `policy_transfer_deadline`; retains why polling stopped, regardless of subsequent publication/cleanup |
| `exit_requested` | Host boolean: release-store to the exit-request flag occurred; not proof the worker acted on it |
| `termination_request` | Optional host object with `signal` (integer), `rc` (signed syscall return), `errno` (integer only on failed kill, otherwise absent/null); absent/null means no request |
| `reaped` | Host boolean: a wait call actually returned this PID; not inferred from kill success |
| `ready_wait`, `sentinel_wait`, `exit_grace_wait` | Host wait records, present for each stage that ran: `budget_ms` (the allowance), `elapsed_ms` (monotonic time when the wait stopped, absent when the clock could not supply it), `stop` (why the host moved on: `received`, `eof`, `read_error`, `deadline` or `setup_failed` for readiness; the `poll_stop_reason` value for the sentinel; the `grace_end` value for exit grace), `excluded_ms` (sentinel only: synchronous phase collection time the allowance does not charge), `native_errno` (a readiness setup or read failure) and `clock_fault` (the clock failed or ran backwards and the wait spent only its last remaining allowance in nominal sleeps). The allowance consumed is `elapsed_ms` minus `excluded_ms`; each sleep is bounded by the remaining allowance, and progress or interrupted calls never renew it. A stop says when the host moved on, not when a child ended |
| `wait_errors` | Host array of observed wait failures, each with stage, signed return and errno; retain errors even if a later wait succeeds |

`sandboxed_after_apply` remains the public application observation; do not add a
second authoritative applied boolean. `sentSigkill` internally must not stand in
for deadline expiry or successful termination/reaping. Absent optional fields
are unknown rather than synthesized observations.
Optional subprocess objects preserve the existing omitted-or-null convention.

The readiness, sentinel and exit-grace budgets are unchanged. The driver allows
two EINTR retries total across polling, grace and final reaping. A terminal wait
error ends that stage; ECHILD stops all further waits and signals to that PID.
There are at most five failed-call records (two recovered interruptions plus one
terminal error per stage), with no error truncation. `wait_errors[].stage` is
`poll`, `exit_grace`, or `after_termination`; rc/errno and termination numbers
are signed 32-bit syscall values, encoded as JSON integers. Empty errors means
observed none; missing/null means unavailable.

A failed kill permits only a nonblocking final reap; if no status arrives, the
result explicitly records `reaped=false` and omits exit/signal. A successful kill
retains the existing blocking final wait, with finite EINTR retries if it fails.
This bounds failed-call handling, not kernel exit latency or the whole lifecycle.
An unreaped child or zombie may remain; no global reaper is introduced. Test
equipment independently cleans up children it owns without changing the driver
result. The policy-transfer deadline does not establish a global lifecycle deadline.
Policy-write failure retains the child's partial evidence. The final acquired
snapshot follows cleanup, preserving late immutable publications. The write
pipe suppresses SIGPIPE; original descriptors close on exec so only intended
child descriptors survive.

## Worker disposition record

The host resolves one canonical account of the worker's lifecycle and carries it
in the reply as `runner_subprocess.disposition`. Every lifecycle conclusion
downstream is a projection of that account. The record answers a fixed list of
questions; each answer names the observations that support it, and unresolved,
conflicting and inapplicable questions carry a specific reason. The
observations themselves stay in their existing raw fields, which remain the
authoritative facts; the record references them and never copies them into a
separately mutable form. `tests/lib/lifecycle_contract.py` carries the same
tables and spellings, `tests/lib/lifecycle_adapter.py` reads the record without
deriving answers, and `tests/lib/lifecycle_oracle.py` checks a reply against
the claim tables independently of the production resolver.

A worker reply carries the record whenever it carries `runner_subprocess`;
omission is a contract violation (`disposition_integrity: invalid` with a
`missing_record` issue, claims withheld). No worker means no record. The
record's own version is the response schema; it carries no separate number,
and readers accept exactly the current response schema.

The account indexes every declared phase action in execution order, including
extension consumption and release. `steps` contains ordinary query/attempt pairs;
`extension_events` contains the native interventions. `phases[].action_ids`
partitions their union, preserving each array's relative order. Consumers join
disposition entries by action identity; an index in `steps` alone is not the
worker slot index when interventions are present.

### Native extension evidence

`extensions[]` records target preparation, issuance and worker delivery
independently. It carries a specimen-local `token_ref`, the fixed
`com.apple.app-sandbox.read` class, submitted and resolved targets, preparation
status/errno and the prepared target's device, inode, mode, UID and GID. Resolution
and metadata are host observations before issuance; neither establishes that a
later open reached the same object. Preparation failure retains its status and
withholds the unavailable identity or resolved path. It does not fabricate a
native issuance call.

The nested `issuer` records its executable, PID, authority IDs, pre-call boundary,
result publication, native pointer nonnullness, errno and bounded token length,
plus independent spawn/wait/termination/reap observations. The pointer and token
bytes are not reply fields. `issuance_status: issued` requires a complete bounded
native result and a clean, confirmed issuer reap; abnormal or unconfirmed cleanup
withholds delivery. `issuer_abnormal_exit` retains a published bounded native
token result alongside a confirmed nonzero exit or signal; it does not mean the
publication was missing. Timeout and wait-error statuses retain their independent
cleanup observations. `delivery_status` and `delivered_bytes` describe the worker's
published channel observation separately from issuance. `host_buffer_erased`
records clearing the host's mapping, not proof that every process or native
library has erased every copy.

Ordinary worker departures after channel acceptance erase the full fixed token
buffer. Terminal publication follows that erasure; cancellation and early returns
preserve their existing publication boundaries. Fatal termination or interruption
inside a native call need not reach cleanup. The worker retains its borrowed
mapping until exit. Erasure does not call native extension release, which remains
an explicit specimen action; the host's separate erasure observation cannot prove
worker cleanup.

A worker delivery failure publishes `delivery_status` as `channel_rejected` or
`local_setup_failed` beside a `delivery_failure` account: `stage` names the
first failing preparation stage, `native_rc` and `errno` are that call's return
and the errno saved immediately after it when the stage made a native call,
and `cleanup_stage` with `cleanup_errno` record a `descriptor_close` or `unmap`
failure observed while undoing earlier setup. A cleanup failure never changes
the status. The account is present exactly for those two statuses. Delivery
success still establishes neither consumption nor effective access.

<!-- BEGIN SHARED EXTENSION STATUSES -->

Issuance and delivery are separate observations. Only `issued` makes the token
channel eligible for worker delivery. Other issuance statuses withhold it;
none establishes consumption, effective permission or revocation. Read spawn,
termination, wait and reap fields independently: a status does not substitute
for cleanup evidence.

| Issuance status | Publication and supported meaning |
| --- | --- |
| `not_started` | Issuance did not start, including when target preparation failed. No issuer result is supplied. |
| `issuer_unavailable` | The selected issuer executable was unavailable. Preparation and issuance did not start; capability refusal prevents a worker run. |
| `channel_setup_failed` | Host setup of the transient channel or its descriptor failed before issuer launch. No issuer result is supplied. |
| `spawn_failed` | Spawn setup or `posix_spawn` failed. The issuer record retains the spawn failure; no child PID or native result is inferred. |
| `issuer_timeout` | The issuer wait expired without a more specific publication status. Publication may be present; termination requests and final reap observations remain separate. |
| `issuer_wait_error` | The issuer wait failed without a more specific publication status. Publication may be present; the wait error does not establish child exit. |
| `issuer_result_missing` | The issuer was reaped without result publication. `result_published` is false, with no native result, errno, token length or published authority IDs. A pre-call marker and exit/signal observation may remain. |
| `issuer_abnormal_exit` | A bounded token result was published, but the issuer was reaped with a nonzero exit or signal. Publication is retained and delivery withheld. |
| `native_api_unavailable` | The issuer published that at least one required extension API (issue, consume or release) was unavailable, without a native call. Capability refusal prevents a worker run; cleanup remains independently recorded. |
| `native_refusal` | The issuer published a null native return and its errno. This observation does not establish why issuance was refused or whether cleanup was clean. |
| `token_oversized` | A nonnull native return supplied an empty token or no terminator within the token buffer bound. The issuer published that rejection; no deliverable token length is supplied. |
| `invalid_transport` | Publication was observed, but its header, state/marker relationship or token length failed host validation. Fields from an invalid header are not treated as native results. |
| `issued` | The issuer published a nonnull native result with a bounded token length and was cleanly reaped. The worker still must validate the channel and publish its own delivery observation. |

Published API unavailability, native refusal, token rejection or invalid transport
has its own issuance status even if the host wait also timed out or failed.
For a valid bounded token result, a wait timeout or error withholds delivery and
keeps that wait status; clean and abnormal reaps distinguish `issued` from
`issuer_abnormal_exit`.

| Delivery status | Worker observation and supported meaning |
| --- | --- |
| `not_observed` | No worker delivery publication was collected. This includes no worker or interruption before publication; it does not negate completed issuance. |
| `delivered` | The worker published successful channel validation; `delivered_bytes` matches the issued token length. This does not establish a consume call or result. |
| `token_unavailable` | The worker published that no token descriptor was supplied. No delivered byte count is supplied. |
| `channel_rejected` | The worker inspected the channel and rejected it. `delivery_failure.stage` is `channel_size` (a successful `fstat` reported an object smaller than the channel; `native_rc` 0 and no errno), `channel_header` (magic, completion or status) or `channel_token` (length, terminator or embedded NUL). Format rejections carry no native result. No delivered byte count is supplied. |
| `local_setup_failed` | A local native call before channel validation failed. `delivery_failure.stage` is `core_limit` (`setrlimit`), `descriptor_metadata` (`fstat`), `mapping` (`mmap`) or `descriptor_close` (`close`), with that call's `native_rc` and the errno saved immediately after it. The channel contents were not judged. No delivered byte count is supplied. |
| `native_api_unavailable` | The worker published that consume or release API support was unavailable. No delivered byte count is supplied. |

<!-- END SHARED EXTENSION STATUSES -->

Each `extension_events[]` entry identifies its phase, action, operation and local
handle reference; consumption also identifies its token reference. These events
have no ordinary query or comparison. `call_boundary_observed` is a separately
published pre-call marker, not proof of native entry, return or effect.
`result_published` means the worker completed that action's immutable slot.

| Event status | Supported reading |
| --- | --- |
| `returned` | The call marker and slot publication support `native_result` and `errno`. Consumption retains the full signed native handle; -1 supplies no handle. Release retains its native int result and requires the matching earlier observed consume handle. |
| `unavailable` | The worker published its decision without making the call. The reason is `token_unavailable`, `handle_unavailable`, `native_api_unavailable` or defensive `repeated_action`; native return and errno remain absent. |
| `unresolved` | The action has no published result. A pre-call marker may survive, but no native return, errno or unavailability decision is inferred. |

The event's `lifecycle` copies the corresponding disposition claims. A completed
slot can record an unavailable action; it does not imply native success. A call
whose return was not published remains unresolved even when an independent test
intervention knows that it returned. Issuance, consumption, release, predictions
and access remain independent observations; no field states effective permission
or prediction/enforcement agreement.

The ordinary `file/read_fresh` action opens a fresh descriptor, records `fstat`,
performs one bounded read and closes the descriptor. `attempt.fresh_read` retains
the native results and failure errnos separately, the descriptor identity after
successful stat, and hexadecimal bytes whose length equals the nonnegative read
count. A failed open supplies no read/stat/close evidence. The aggregate attempt
preserves the first failure in syscall order as `read_failed`; missing slot
publication supplies no fresh-read payload. This establishes the recorded bytes,
not EOF or a whole-file read. `open_read` keeps its existing open-only meaning.

`file/write_fresh` and `file/create_fresh` publish `attempt.fresh_write` only
through completed worker slots. Both use a fresh write-only descriptor and
attempt one fixed `x` byte. Existing-file writing explicitly truncates to zero;
creation uses `O_CREAT|O_EXCL` and mode 0600. Their native open, truncate, write
and close return/errno pairs are separate. `preopen_stat` (create-only lstat),
`opened_stat`, `truncated_stat` (existing-write only), and `written_stat` each
retain native rc, failure errno and successful identity/size. The pre-open
observation is diagnostic, including ENOENT, and does not suppress the open.
After failed truncation, write/written metadata are absent but close still
runs. Failed opens have no descriptor operations. Successful native calls have
no failure errno; unattempted calls have no result. The aggregate preserves the
first relevant failure in call order as `write_failed`, excluding pre-open
metadata; short transfer is a failure without an invented errno. Later failures
remain visible. These fields do not themselves prove persistent contents.

Extension records identify the internally selected native read or read-write
class from admitted authority. Default and explicit `read` preserve the native
read class. Native issuance, consumption and release never substitute for
independent read/write effects or post-release observations.

`witness_contract/extensions` establishes native calls and independent file
observations through the public CLI. `blackbox_e2e/checker_controls` mutates its
retained capture to reject fabricated native completion, bad references and
inconsistent read observations. Swift extension evidence controls and Rust
disposition tests check producer encoding and controller withholding separately.

### Raw host facts the record needs

Three host observations join `runner_subprocess` beside the fields in
[Host observations](#host-observations). They are facts, recorded where the host
acts, not conclusions reconstructed from a final status.

| JSON location under `runner_subprocess` | Producer, type and validity |
| --- | --- |
| `cleanup_trigger` | Host string recorded at the exit-request store: `deadline_expiry`, `completion`, `child_reaped`, `poll_wait_error` `policy_transfer_error` or `policy_transfer_timeout`. It names why exit was requested; today it corresponds one-to-one with `poll_stop_reason`, and both are retained. |
| `grace_end` | Host string recorded when the exit-grace wait ends: `not_entered` (the poll loop already reaped the child), `reaped_during_grace`, `exhausted` (the host then requests termination) or `wait_error`. Never inferred from `done` plus a kill. |
| `collection_basis` | Host string recorded at the final shared-memory reads: `after_confirmed_reap` (every relevant read followed a successful reap), `execution_may_continue` (the worker was not confirmed reaped when the reads happened, including after a failed kill) or `unavailable` (no usable mapping). A reap observed after the reads does not upgrade the basis. |

Absence of any of the three is a malformed record, not an observation of
false. The record's per-step entries additionally carry two host facts about
each submitted step: `slot` (`completed`, `incomplete` or `absent`) and
`attempt_support` (`supported` or `unsupported`, from the host's attempt
mapping). They agree with the step channel: `attempt.result_source` is
`worker` exactly when the slot is completed and supported, and
`attempt.missing_reason` is `attempt_not_supported`, `slot_absent` or
`slot_incomplete` accordingly.

### Nesting

```
runner_subprocess.disposition = {
  "questions": { <run question>: <claim>, ... },   // all seven run questions, always present
  "steps": [ { "index": i, "step_id": "...", "slot": "...", "attempt_support": "...",
               "questions": { <step question>: <claim>, ... } }, ... ],   // one per declared action, in phase order
  "issues": [ { "kind": "conflict", "rule": "D1" | "D5", "question": "...",
                "step_index": i?, "observations": [ <reference>, ... ], "detail": "..." }, ... ]
}
<claim> = { "state": "supported", "answer": "...", "value"?: ..., "basis": [ <reference>, ... ] }
        | { "state": "unresolved", "reason": "...", "basis"?: [ ... ] }
        | { "state": "conflicting", "issue": <index into issues> }
        | { "state": "inapplicable", "reason": "..." }
```

The run questions are `final_status`, `stop_reason`, `cleanup_trigger`,
`grace_end`, `kill_request_and_result`, `collection_basis` and
`progress_association`. The step questions are `step_boundary_reached`,
`step_result_published` and `step_requested_operation_applicability`. A
`value` accompanies `final_status` (the exit code or signal number),
`kill_request_and_result` when `requested` (the `termination_request` object),
and `progress_association` when it names an index. Every question is present
in every record; an absent question is malformed, never unresolved.

### Evidence references

A `basis` or `observations` entry is one token from a fixed set. Run-scoped
tokens resolve under `runner_subprocess`; step-scoped tokens resolve inside the
record's own step entry. A token that does not resolve within the same retained
reply invalidates the claim that uses it.

References must be strings and must include a sufficient witness set for the
answer, not merely a nonempty list of existing fields. Values (including all
fields of a termination request) must equal the cited observation. Both exit
and signal representations disqualify either supported status answer. A
terminal collection fact without a successful reap is invalid; a reap alone
never upgrades a live collection fact. The boundary/result copies in
`attempt.lifecycle`, the aggregate publication flag and lifecycle limitations
must agree with the carried record. Conflict issue references must identify
the applicable rule, question, step and observations, not just an existing
array element.

| Token | Resolves to |
| --- | --- |
| `reaped`, `exit_code`, `term_signal` | the same-named `runner_subprocess` fields |
| `poll_stop_reason`, `exit_requested`, `termination_request`, `wait_errors`, `done_observed` | the same-named `runner_subprocess` fields |
| `cleanup_trigger`, `grace_end`, `collection_basis` | the new host facts above |
| `progress`, `worker_failure` | `runner_subprocess.worker_evidence.progress` and `.failure` |
| `plan` | the declared actions across all phases, including native interventions, in execution order |
| `slot`, `attempt_support` | this step entry's own facts (step questions only) |

### Questions, answers and witnesses

The tables below are the claim requirements. Each supported answer lists its
alternative sufficient witness sets and the collection scope they need: `any`
holds under every collection basis; `terminal` requires `collection_basis` to
be `after_confirmed_reap`, so the worker can publish nothing more. Negative
answers (`not_reached`, `unpublished`) need terminal scope because a live
worker can still publish. A conflict is listed apart from the answers it
disqualifies: once its identity and scope are established it disqualifies a
supported answer to that question even when a candidate basis is also present,
and it leaves every other question's answer alone. Unresolved conditions carry
the reason code the record must use. Applicability is explicit: an inapplicable
question is not missing evidence.

Protocol position orders progress words by the worker protocol, not by opcode:
header 1, policy read 2, parameter allocation 3, parameter assignment 4,
compilation 5, capture 6, readiness 7, application 8, then proceed 11 before each phase's action batch, attempt 9
for each action in execution order, and completion 10. Here a disposition
"step" means any declared action, including consumption and release. Indexed
proceed progress names the waiting phase's first action and occupies the position
immediately before that action; an empty final phase can name the total action
count. It does not mean that action began. An attempt word's item
index names the step; a parameter word's names the parameter. An attempt index
that names no submitted step, including any attempt index for an empty plan,
is `invalid`; a mismatch between the encoded word and its decoded fields, or
an item index on a non-indexed operation, is also `invalid`. An ambiguous slot
identity supplies no associated slot, rather than selecting one duplicate.
An unrecognized operation or stage code is `progress_unrecognized`
and its raw word is retained. Progress at or beyond a step's boundary means a
position at or after that step's `started` word.

| Question | Answer | Sufficient witnesses (any one) | Scope | Rules |
| --- | --- | --- | --- | --- |
| Final status | exit code | successful reap with a valid exit-status representation and no signal representation | any | D1 |
| | signal | successful reap with a valid signal representation and no exit-status representation | any | D1 |
| Stop reason | `done`, `sentinel_deadline`, `child_reaped`, `wait_error`, `policy_write_error`, `policy_transfer_deadline` | the host's poll-loop observation | any | D2 |
| Cleanup trigger | deadline expiry; completion; child reaped during polling; poll wait error; policy transfer error or timeout | direct host observation of why exit was requested | any | D2 |
| Grace end | not entered; reap during grace; exhaustion; wait error | direct host observation of how the exit-grace wait ended | any | D2 |
| Kill request and result | none; requested, with `rc` and `errno` | explicit host observation that no request was issued; or direct observation of the request and its return | any | D2 |
| Collection basis | reads after confirmed reap; reads while execution may continue; unavailable | direct host observation at collection time | any | D2 |
| Progress association | valid step index; parameter index; none; invalid | the decoded word validated against the ABI operation table and the submitted plan | any | D3 |
| Per-step boundary reached | reached | valid started or returned attempt progress associated with this step; or a valid completed slot for this supported step, including with absent or unusable progress; or valid attempt progress associated with a later step under the serial attempt order | any | D3 |
| | not reached | a valid known protocol position before this step and no completed slot for this step | terminal | D4 |
| Per-step result published | published | a completed slot for this supported step | any | D3 |
| | unpublished | a valid incomplete slot for this step with no applicable publication conflict | terminal | D3 |
| Per-step requested-operation applicability | supported; unsupported | the host's attempt mapping (`PW_ATTEMPT_NONE` marks unsupported) | any | D3 |

| Question | Conflict (rule; witnesses; scope) | Unresolved when | Applicability | Consuming projections |
| --- | --- | --- | --- | --- |
| Final status | D1; one successful reap represented as both an exit status and a signal; any | no successful reap (a successful kill request is not a reap); or a reap with missing, malformed or unrecognized status representation | whenever a worker was spawned | `process_disposition`, `termination_cause` |
| Stop reason | none | the host recorded no poll-loop stop | whenever polling started | `stop_reason`, lifecycle error clause |
| Cleanup trigger | none | the host recorded no trigger apart from the stop reason | whenever exit was requested | `termination_cause`, lifecycle error clause |
| Grace end | none | the host recorded no grace outcome; never infer exhaustion from `done` plus a kill | whenever exit was requested | `termination_cause`, lifecycle error clause |
| Kill request and result | none | the host recorded no request outcome; absent evidence is not an observed non-request | whenever cleanup ran | `termination_cause`, lifecycle error clause |
| Collection basis | none | the host recorded no basis; a later kill or reap never stabilizes earlier reads | whenever slots were read | the scope of every per-step answer |
| Progress association | none | no progress word; unrecognized operation or stage code, with the raw word retained | whenever a progress word was published | the per-step answers below |
| Per-step boundary reached | D5; a completed slot for this step beside valid terminal progress that never reached it; terminal | no usable progress and no completed slot; a live or unavailable basis for `not reached` | every submitted step | `attempt.lifecycle`, `comparison.limitations` |
| Per-step result published | D5; valid association, an incomplete slot and valid returned progress for this step or a later known protocol position, violating completion-before-return; terminal | an absent or unusable slot; an incomplete slot under a live or unavailable basis, with or without progress beyond it | every supported step | `attempt.lifecycle`, `partial_steps`, `comparison.limitations` |
| Per-step requested-operation applicability | none | the host recorded no mapping | every submitted step | `attempt.lifecycle`, `missing_reason` |

The FIFO case reads off these rows. Attempt 0 has a reached boundary from its
started progress under any scope and, because collection followed the reap with
no progress beyond its incomplete slot, an unpublished result. Attempt 1 is not
reached because the last valid position precedes it under terminal scope and
its slot is incomplete. A completed slot with absent or invalid progress keeps
both its result and its reached boundary. Terminal progress beyond an
incomplete slot is the D5 conflict; returned progress for that same incomplete
slot also violates completion-before-return. These combinations leave the
publication question conflicting, while an independently witnessed reached
boundary stays known. A poll-time reap still leads the host to publish
`exit_requested`; its cleanup trigger is the observed reap and its grace end
is `not entered`. No termination request is implied.

### Cause labels

`runner_sandbox_diagnostics.termination_cause` projects host cleanup that the
account witnesses end to end. A label requires all of: `cleanup_trigger`
supported with the trigger in the table, `grace_end` supported as `exhausted`,
`kill_request_and_result` supported as `requested` with `rc` 0, and
`final_status` supported as `signal` equal to the requested signal. The label
describes that witnessed host sequence. It is not exclusive signal-sender
attribution and never a sandbox cause.

| Witnessed trigger | Label |
| --- | --- |
| `deadline_expiry` | `host_sentinel_deadline` |
| `completion` | `host_exit_grace_exhausted` |
| `poll_wait_error` | `host_cleanup_after_wait_error` |
| `policy_transfer_error` | `host_cleanup_after_transfer_error` |
| `policy_transfer_timeout` | `host_cleanup_after_transfer_timeout` |

Otherwise the cause is null for a supported exit code 0, and `unknown` for a
supported nonzero exit or signal without the full chain, an unresolved or
conflicting final status, an unrecognized final-status answer, and a record
that failed integrity validation. `unknown` is a specific
statement that the account does not attribute the termination; the record's
own reasons say why.

### Projections

Each registered projection is a total function of the record. The controller
validates the record before projecting and never derives a competing lifecycle
answer from raw fields or prose.

| Projection | Rule |
| --- | --- |
| `runner_sandbox_diagnostics.process_disposition` | `final_status` supported: `signal` gives `signaled`; `exit_code` 0 gives `clean_exit`; nonzero gives `nonzero_exit`. Unresolved gives `unconfirmed`. Conflicting gives `conflicting`. A record that fails validation, or a worker subprocess without one, gives `withheld`; an unrecognized answer spelling gives `unrecognized`. No worker gives `no_worker`. |
| `runner_sandbox_diagnostics.termination_cause` | The cause table above. |
| `runner_sandbox_diagnostics.stop_reason` | The `stop_reason` answer when supported; otherwise null. The raw `poll_stop_reason` remains readable. |
| `runner_sandbox_diagnostics.disposition_integrity`, `disposition_issues` | `valid` or `invalid`. Invalid records list their issues with kind `invalid_claim`, `unresolved_reference`, `unrecognized_value`, `missing_record`, `malformed_record`, `extension_evidence` or `phase_collection`; an invalid record withholds disposition and cause as above. A record that faithfully reports a conflict is valid. |
| `runner_subprocess.partial_steps` | True when any step's slot is not completed, including an unsupported no-op slot. It does not say an attempt never began. |
| `steps[].attempt.lifecycle` | `{"summary", "boundary", "result"}` where `boundary` and `result` are the step's two claims and `summary` is: `unsupported` when the requested operation is unsupported; else `completed` when the result is `published`; else `conflicting` when either claim conflicts; else `started_without_result` (reached, unpublished) or `not_reached` (not reached, unpublished); else `unresolved`. |
| `steps[].comparison.limitations` | Beside the existing entries, exactly one lifecycle entry for a summary other than `completed`: `attempt:started_without_result`, `attempt:not_reached`, `attempt:unsupported`, `attempt:lifecycle_unresolved` or `attempt:lifecycle_conflicting`. Lifecycle entries never change the relations, order or sandbox attribution. |
| `steps[].attempt.outcome`, `missing_reason`, `result_source` | `no_completed_result` and `slot_incomplete` mean no completed supported result, which may have started; the lifecycle object carries the distinction. |
| `error` lifecycle clauses | Rendered from the account, text unchanged: a `sentinel_deadline` stop renders `pw-probe-runner sentinel deadline expired` followed by `host requested SIGKILL during cleanup` when a request was made or `no termination requested` otherwise. The `runner_failed` problem list keeps `process disposition unconfirmed`, `reaped with signal N`, `reaped with exit code N`, `reaped without usable exit status` and `host requested termination during cleanup`, each from the corresponding claim. Worker failure, validator and setup diagnostics keep their owners and precedence and are composed with, not generated from, these clauses. |

`normalized_outcome` keeps its values and precedence. A deadline followed by a
voluntary exit stays `runner_timeout`; a published worker failure still takes
precedence over later cleanup.

### Integrity, unknown values and degradation

The encoder rejects an assembled claim that contradicts its basis, such as a
supported final status without a successful reap or a basis token that does
not resolve; the service reply boundary then produces the evidence-preserving
degraded reply, which retains `runner_subprocess` and the record as assembled,
withholds comparisons, and names the invariant in `reporting_failure`. The
degraded encoder does not re-check the invariant, so the conflict being
reported is never lost to a rejection loop. A record that reports an observed
conflict through `issues` is valid and encodes normally. The minimal
reporting-failure reply carries no `runner_subprocess` and therefore no record,
and says `evidence_retained: false`.

Unrecognized answer, reason and summary spellings transport unchanged through
the runner encoder, the XPC client and the controller. Only interpretations
that need recognition become unresolved for the reader: an unrecognized
final-status answer projects `process_disposition: unrecognized` and cause
`unknown`; an unrecognized stop reason projects null; an unrecognized lifecycle
summary keeps its raw value. Consumers never reinterpret a reply of another
version; they report it as unsupported.

### Reader validation responsibilities

The Swift response types establish field types; ordinary encoding also checks
claim, phase, ordering and native-publication invariants. The reporting-failure
path retains conflicting observations and withholds comparisons as described
above. It does not make contradictory raw observations trustworthy.

The Rust controller gates the version and validates the evidence needed for its
disposition projections. `disposition_integrity: valid` certifies those claim
checks, not the shape of the entire response. Present non-null phase containers,
phase records, ordering objects, validator-disposition values and spawn-failure
objects must have their declared types; a mistyped value cannot become optional
absence. The claim checks tolerate absent or null optional evidence without
inventing it. Required phase and ordering fields remain the full response
validator's responsibility. A degraded reporting-failure reply preserves the raw
phase account without using contradictory collection observations to recover
ordinary claims; the controller always forwards the raw reply unchanged.

`tests/lib/consumer.py` combines shape-golden checks with required-field and
semantic checks. `tests/lib/lifecycle_oracle.py` independently checks lifecycle
claims and their supporting observations; it is not a complete response-shape
validator. For example, an empty `validator_spawn_failure: {}` beside
`collected`/`not_spawned` contradicts no presence claim, so Rust and the lifecycle
oracle do not infer a native spawn result from it. The full consumer rejects it
because the required origin, operation, executable path, nonzero return code and
diagnostic are missing. Reader controls pin both responsibilities, including
wrong-type rejection, optional absence and unchanged degraded evidence.

Every semantic reader checks ownership of a phase's validator subprocess the
same way. The block carries `phase_id` and `ordinal`, stamped by the host from
the collection it ran, and both must equal the containing phase's. Its
`expected_step_ids` must name exactly the phase's eligible query plan: the
phase's ordinary steps whose retained query decision is not
`query_not_requested`, read from the reply rather than by resolving paths again,
so a block beside a phase without eligible queries carries an empty plan. Step
order is the partition and step-order checks' question, not ownership's. Its
`association_issues` must be the
issues its retained `records` and that plan imply, recomputed by the reader. A
block copied from another phase, or copied expected IDs, records or identity
fields, therefore fails validation even when every phase queries the same
path under different action IDs, and a block missing these fields withholds
the dependent claims. Unexpected, duplicate and null-ID validator records remain
intentional diagnostic evidence, retained with their association issues. Numeric
PID uniqueness across phases is not a reader invariant: sequential children may
reuse a PID, and the collection identity does not authenticate the validator
executable or prove that it made a native call.

### Versions

The record is mandatory for every worker reply at the current response
schema, and the controller's `termination_cause`, `stop_reason`,
`disposition_integrity` and `process_disposition` projections belong to the
current controller envelope. `tests/lib/contract.py` carries both numbers and
every reader gates on them exactly. Per [docs/CONTRACT.md](../docs/CONTRACT.md)
the manifest moves with the change that produces them; a rebuilt app must never
report a response number without carrying the shape that number names.

## Public compatibility

The response, request and controller envelope are separate public contracts;
[docs/contract.json](../docs/contract.json) owns their version numbers. Semantic
readers accept exactly the current numbers (see [Supported versions](#supported-versions)).
The internal host/worker boundary instead requires the same generated source
identity, as described in [the wire contract](../docs/CONTRACT.md#internal-hostworker-identity).
That identity is independent of the public JSON versions.
Steps carry no signal channel; a null per-step `errno` requires key presence.

No outcome spelling claims a sandbox termination cause or a precise
application failure: signals alone cannot justify the first,
and an imprecise published status cannot justify the second. The pre-apply
witness case forbids both spellings outright. `runner_failed` covers
execution/reporting failure with cause possibly unknown; it does not mean a
proven host defect. `bad_policy` keeps its existing structural-policy admission
meaning. Published worker failures also use `runner_failed`; the operation/code
record provides the precise account without adding outcome strings.

The pre-apply CLI witness asserts excluded claims, not one exact summary;
the table's classifier controls pin the mapping. The attempt
outcome `no_completed_result` means no completed attempt result and makes no
claim about whether an operation started. Synthetic missing predictions retain
`rc=0` with an explicit result source, missing reason, and null native return.

Worker identity comes only from a positive `runner_subprocess.pid`, never a
host/client top-level PID. `runner_sandbox_diagnostics` describes execution
and disposition independently of outcome. Abnormal or unconfirmed disposition
has `termination_cause: unknown` unless the
[worker disposition record](#worker-disposition-record) witnesses host cleanup
end to end. Client timestamps retain the raw execution span, even when the
wall clock moves backwards.

## Coverage audit and acceptance ownership

The entries below distinguish constructed host interpretation, actual C-worker
publication, and the CLI boundary. The host-driver, encoding and classifier
controls establish separate parts of the table. The
[comparison record](#comparison-record) ownership table identifies the lasting
reporting obligations and registered test owners.

| Test entry | Production reach and current assertions | Acceptance owner / remaining obligation |
| --- | --- | --- |
| `runner_unit/pwrunner_core_unit_executable`: `HostOutcomeClassifierTests.runHostOutcomeClassifierTests` | Constructed `CWorkerOutput`/validator results; pins publication, deadline, disposition and precedence rows; no OS calls or worker publication | Implemented, independently of driver tests |
| Same catalog case: `EnvelopeInvariantTests.runEnvelopeInvariantTests` and `OrderingTests.runOrderingTests` | Constructed Codable results; current ordering/eligibility, absence of the removed wire keys, exact-version rejection, subprocess absence and unknown vs observed false/empty, unfamiliar observation values | Implemented; actual client error replies also checked in smoke/runner_caller_auth |
| Same catalog case: `ReplyFailureTests.runReplyFailureTests` | Real service reply serializer with constructed invariant faults and internal encoder failure; every stored field has encoding coverage | Preserves diagnostic evidence and original summary, withholds comparisons; explicitly reports repeated encoding failure |
| Same catalog case: `CWorkerTests`, `late done during grace preserves sentinel deadline` | Real worker through Swift driver; late voluntary exit with no host kill and exit 0; records `sentinel_deadline`, reaped exit 0, and no termination request through actual subprocess encoding | Driver, final done/slot snapshot and runner_timeout classifier verified |
| Same catalog case: `CWorkerTests`, `postApplyKillSignal terminates worker before done -> runner_failed` | Real C worker self-signals; asserts applied/not-done/no-host-kill/SIGKILL, `child_reaped` and encoded process facts, then calls classifier | Driver plus runner_failed classifier verified; no real sandbox kill is established |
| Same catalog case: `CWorkerValidatorTests`, `postApplied hook does not fire when compile fails` | Real malformed SBPL through Swift driver; asserts no applied marker and zero hook calls | Driver control; `witness_contract/worker_progress_and_failure` separately verifies compiler diagnostic text at the CLI boundary |
| `runner_c_worker_harness/compile_failure` (`run_compile_failure`, `harness.c` scenario) | Real C worker: no ready byte, A=false, D=true, R=-1, no completed slot, exit 0 and no host kill | Retain actual publication/exit protection; not Swift interpretation or CLI forwarding |
| `runner_c_worker_harness` early-exit and success cases; `runner_abi_layout` | Actual C worker's early guards and attempts; independently compiled C layout compared with Swift constants | Complementary ABI/publication protection; compiled layout and exact-identity rejection |
| `runner_c_worker_harness/clock_arithmetic`, `proceed_precedence`, `exec_control_states` | Production clock helpers, proceed wait and exec flow with a controlled timebase and raw counter: ceiling allowances, checked arithmetic, sample rejection and provenance, setup publications, precedence, race gates, exact exclusions and every exec timing stage | Deterministic boundaries only; not platform clock behavior, sleep or a sandbox cause |
| Same catalog case as `runner_unit`: `WorkerClockTests.runWorkerClockTests`; Rust `run_flow::tests::worker_clock_driver_replies_cross_assembly_and_consumer` | Production C main with one substituted clock boundary through the real host driver and production orchestration with the shipped validator: setup refusal during and after policy delivery, phase-2 refusal and expiry with retained predictions, sticky provenance with independent child cleanup and local arithmetic refusals; replies cross Rust assembly, the consumer and the lifecycle oracle | Publication, transport and interpretation; companion substitutions are not native clock failures |
| `runner_c_worker_harness/native_clock` (opt-in) | Production clock helpers in fresh processes under the original version-2 policy, bare deny-default and allow-default, beside the old `CLOCK_MONOTONIC` neighbour; retains timebase, counts, PIDs, reaps, installed disassembly and available deny records | Native applicability on the recorded machine only; actual system sleep remains untested |
| `witness_contract/pre_apply_failure_reports_no_policy_verdict` (`check_pre_apply_failure.py`) | Real CLI, populated allowed/denied plan, pre-ready delay and worker deadline; identical un-overridden positive control | Independent attribution, lifecycle and consumer-validation groups require the current response schema; missing channels remain distinct from observed failures |
| `runner_unit/pwrunner_core_unit_executable`: `CWorkerLifecycleTests.runCWorkerLifecycleTests` | Real host driver with test-only ABI child: completed report then cleanup SIGKILL, independent exit 17 or SIGTERM, published status-word failure then cleanup, failed kill, failed/recovered/interrupted wait, ECHILD ownership loss and poll EIO. Gated acknowledgement between samples followed by clean exit with done or fatal termination without done exercises reconciliation after confirmed reap, with a lost-ownership control. Actual subprocess assembler and JSON round-trip preserve reports and missing status. Fixture applies no sandbox. | Driver, assembler, encoding and classifier agree; synthetic payload does not establish a native library result |
| `runner_ready_byte_resilience/slow_compile_ready_byte_survives_sigpipe` | Real CLI with sufficient budget; lost ready byte must not prevent successful application, prediction and attempt | Successful resilience verified; delay follows compilation/capture and has sufficient sentinel budget |
| `runner_outcome_runner_timeout/host_kills_hung_worker`, `witness_contract/worker_post_apply_hang_seam`, `runner_use_c_worker/worker_timeout_ms_honored` | Real CLI post-apply deadlines; empty, mixed and single-write plans, retained evidence and independently checked effects | Success/timeout/partial-evidence checks pass; populated pre-apply witness adds distinct absence coverage |
| `witness_contract/worker_termination`; Rust `run_flow::tests::execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields` | CLI failed writes, repeated attempts, independent read queries, self-signal and ordered phases. Constructed replies cross production assembly with raw execution evidence retained. | Independent worker disposal and execution diagnostics; no sandbox-cause attribution |
| `runner_validator_failure/validator_unavailable_reports_degraded`, `runner_validator_failure/validator_decode_failure_reports_degraded` (also witness suite members) | Real worker attempts plus fixture validator, reversed partial IDs and a missing verdict with its missing reason; malformed JSON is distinct from EOF | Missing prediction reasons and completed failures are independently recoverable; validator lifecycle/UTF-8/structure/association controls are described below |

Real-worker `CWorkerTests` cases guarded by `workerExists()` require
`<PW_APP_DIR>/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner`.
`CWorkerValidatorTests` live cases use that worker and the bundle-local
`<PW_APP_DIR>/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator`
(including the compile-failure case's `bothBinariesExist()` guard), the same
copy production orchestration launches. Tests without `PW_APP_DIR` select
`dist/PolicyWitness.app`. Record those actual paths in retained provenance.

`TestKit.run` counts a guarded early return as passed; the shell wrapper rejects
internal `SKIP`/`FAIL`, checks the summary and requires its worker equipment.
Credit live rows only after inspecting bundle-integrity evidence and the retained
`pwrunner_core_tests.log`. Required live controls fail when their equipment is
missing. Constructed classifier/encoding cases have separate credit.
`source_drift` protects registry/outcome matrices.

## Worker evidence contract

The authoritative layout is `pw_probe_runner_abi.h::pw_shm_evidence_t`, appended
following the capture bytes. Host and worker require exactly the same generated
source identity, with no fallback. The [layout golden](fixtures/contract/abi_layout.txt),
checked against compiled C and Swift, owns offsets and sizes. The header carries
the latest release ordinal, latest observed acknowledgement and fixed per-phase
arrival, acknowledgement and completion records; the magic and identity bootstrap
locations remain fixed. The reply carries the ordering evidence described below.
The worker record is `data.runner_result.runner_subprocess.worker_evidence`.
Its `abi_identity` is the host-selected SHA-256 source identity encoded as a hex
string, not proof the child reached ABI validation.
An entirely absent publication remains explicit even after a mapping failure.
Host process observations remain independent.

### Progress and state table

One release-stored/acquire-loaded UInt32 is the entire progress snapshot: high
8 bits operation, next 4 bits stage (1 started, 2 returned), low 20 bits item
index plus one (zero means no index). JSON retains `raw`, `operation`, `stage`,
and optional zero-based `index`. Zero raw means no progress publication; unknown
operation/stage values are retained without inferring success. No non-atomic
payload is read through progress. This is the latest milestone, not a history.

Operations: 1 compatible header validation, 2 policy read, 3 parameter allocation,
4 parameter assignment, 5 compilation, 6 optional profile capture, 7 readiness
write, 8 application, 9 indexed attempt, 10 terminal completion, 11 proceed wait,
12 clock setup. Temporal order differs from numeric order: clock setup follows
header validation and precedes the policy read; proceed precedes each phase's
attempts.
Started means control reached the call boundary; returned means control returned, regardless
of success. Application is established only by `applied == 1`. Completed attempt
outputs are established only by that slot's `completed == 1`.

| Observation | Meaning / next transition |
| --- | --- |
| compile started; worker dies | No observed return; no invented NULL or errno |
| compile returned; next operation not started | Call returned; success requires subsequent independent evidence; a report may still be unpublished |
| compile NULL | Returned progress, then immutable operation=5 failure with native_kind=2, native_result=0; done may follow |
| param assignment i returns nonzero | Record operation=4 and index=i with the actual integer return; no fabricated apply result |
| assignment i returns and i+1 starts | Atomic progress identifies exactly one boundary; no torn index/stage |
| readiness write fails | Its own immutable rc/errno record remains; execution may proceed to apply and done |
| optional capture omitted | Transition compile → readiness is valid |
| clock setup returned; timebase query failed | Operation 12/code 1/native kind 1 with the actual Mach return, no errno; diagnostic, exit 12, no done |
| clock setup returned; zero factor or unrepresentable allowance | Operation 12/code 14/kind 0, reason in detail; diagnostic, exit 12, no done, even for a plan without exec |
| proceed wait starts; budget expires | Operation 11/code 8, budget milliseconds in detail, done; no acknowledgement or attempt, even after late release |
| proceed sample below the origin or the last accepted sample | Operation 11/code 14/kind 0, reason 3 in detail, the stage in the diagnostic; done, no acknowledgement or attempts |
| proceed after an earlier exec rejected a sample | Operation 11/code 14, reason 6 in detail, no new sample; the diagnostic names the first rejection's reason, stage, phase and slot; done, no acknowledgement |
| release acknowledged; worker dies | Lifetime and eligible query order remain established; an acknowledgement first acquired after confirmed reap also qualifies while ownership remained unbroken, even without done; attempt evidence may be missing |
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
return represented by zero, never a pointer address; 3 is the historical native
clock-call return, which the current worker never publishes. Unfamiliar kinds
retain the raw signed result. Unknown operation/code/detail
are transported unchanged; recognition is not validity. Invalid errno presence
or a nonzero result tagged as NULL rejects payload decoding.
Code 1 is native failure, 2 source capacity rejection (detail is maximum source
bytes, excluding NUL), 3 policy read error, 4 step capacity, 5 parameter capacity,
6 defensive parameter encoding rejection, 7 unprepared header, 8 proceed-wait
expiry, 9 embedded policy NUL, 10 invalid phase partition/publication input,
11 a future release ordinal, 12 an expected policy length the source buffer
cannot hold (header operation 1; detail is the refused expectation; refused
before any policy byte is read; exit 10), 13 a policy whose length at EOF
differs from the host's expectation (operation 2; detail is the received count;
exit 11), and 14 a local timing refusal with no native result or errno, whose
detail is a reason: 1 invalid timebase, 2 invalid or unrepresentable duration,
3 backwards counter (a rejected sample), 4 unrepresentable delta, 5 deadline or
exclusion overflow, 6 prior clock fault. Clock setup (operation 12) refuses
before the policy read with exit 12 and without `done`, like the header and
policy-read refusals; it never claims a status-word result. Code 9's detail is the NUL byte offset; code 10's is the phase
capacity. On the policy read the order is capacity (2, which stops before EOF
and publishes no receipt), then the EOF receipt publication, then length (13),
then NUL (9); codes 12 and 13 precede any libsandbox call, so no prefix or
extension of the submission is compiled. For proceed operation 11, failure index names the zero-based
phase: code 8 carries the wait budget in milliseconds, code 11 the observed release
ordinal and code 14 a timing reason, never milliseconds. Reason 6 records a
refusal caused by an earlier rejected sample, not a new sample failure; only an
actual rejected sample carries reason 3. Human diagnostics interpret those units
only for the known code/kind combination; unknown details remain raw. Exec timing
faults are slot diagnostics, not failure records: a refusal before spawn has rc -1,
no child and no errno; after spawn the PID, captured bytes and any reaped status
survive, cleanup runs while ownership is known, and a native kill or wait errno is
kept beside the local reason. No errno is claimed for libsandbox
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

Both step channels carry `result_source` and optional `missing_reason`; the
query channel also carries `native_rc`, emitted as explicit null when
unavailable. Ordinary attempts have no general `attempt.native_rc` field;
the separate `fresh_read` payload retains its individual syscall returns.
Prediction rc=0 with outcome=error is a synthetic sentinel:
result_source=synthetic and missing_reason=validator_not_invoked (no validator
process), or validator_no_verdict (process ran without this verdict). Excluded
queries use query_not_requested. Received verdicts use result_source=validator;
native_rc is present only for actual allow/deny/error native call results, not
parse/unsupported/filter rejections. The matching phase's validator subprocess metadata remains authoritative;
per-step fields do not duplicate the validator PID/disposition.

Attempts use the outcome `no_completed_result` for a missing result; it means
no completed result and does not say whether the operation started. They use result_source=synthetic
and missing_reason=slot_absent or slot_incomplete. Completed supported slots use
result_source=worker. Their rc is PW attempt status (often 0/1, or aggregated
exec disposition), not a native syscall return such as an open FD. The separate
`fresh_read` payload carries the individual open/stat/read/close native returns;
`attempt.rc` does not substitute for any of them.
Unsupported/skipped attempts use synthetic and attempt_not_supported. A null
step `errno` requires key presence.

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
Counts are host writes, not bytes consumed by the worker; the worker's own
account of what it read is `worker_evidence.policy_read` below. Omission of this
object means no failed write was recorded; it does not establish successful
delivery. No worker record is synthesized from it.

`runner_subprocess.policy_transfer_timeout` independently records expiry of
the host's absolute monotonic delivery deadline. Its integer `budget_ms`,
`elapsed_ms`, `bytes_written` and `bytes_expected` identify the allowance,
observed elapsed time and transfer progress. It carries no errno. The stop
reason is `policy_transfer_deadline`, cleanup trigger `policy_transfer_timeout`,
and the summary is `runner_timeout` unless a published worker failure takes
precedence. A confirmed cleanup signal can project
`host_cleanup_after_transfer_timeout`; neither timeout nor a kill request alone
establishes a successful reap or any sandbox cause.

`runner_subprocess.worker_evidence.policy_read` is the worker's EOF receipt for
the policy pipe. The host writes the submission's UTF-8 byte count into the
region header (`policy_bytes_expected`) before spawn; the worker, once its read
returned at EOF and before comparing, stores the count it read and
release-publishes a flag. The JSON object carries `bytes_expected` (that
immutable host input) and `bytes_received` (the worker's count), both
nonnegative integers within the source capacity. The host exposes only counts
within that capacity after its final snapshot acquired the flag as 1 behind a
validated identity; a
header refusal, read error or overflow publishes none, and absence establishes
nothing about delivery: termination can interrupt the worker before
publication, a failed cleanup can leave publication after collection, and
historical or fixture replies carry no receipt. When a transfer record is also
present its `bytes_expected` agrees with the receipt's; a disagreement is a
reader-detectable fault that neither side corrects. Equal counts establish
length agreement with the submission, not content identity, compilation,
application or kernel effect. A code 13 refusal names the received count while
the counts differ. Unequal counts without that refusal are retained as the
completed read only, because termination can interrupt the worker between the
receipt and the refusal. They cannot coexist in an ordinary reply with known
progress or failure after the length check, readiness, application, completion,
phase arrival/acknowledgement or a worker attempt result. Unknown operation
numbers have no inferred temporal meaning. The Swift reply encoder and decoder
and `tests/lib/consumer.py` enforce these rules; the shape golden only types them.
An evidence-preserving reporting failure retains contradictory receipt values
and withholds every comparison under the existing reply-failure contract. The
receipt's object structure and integer members remain required; its conflicting
values are diagnostics, not an accepted account of delivery.

The production deadline of <!-- span limits.worker_policy_transfer.value_unit -->5,000 milliseconds<!-- /span --> starts immediately after spawn. The
write endpoint is nonblocking and protected by F_SETNOSIGPIPE, with setup
checked before spawning. Partial writes, EINTR and backpressure consume the
same deadline. Zero-progress writes, clock failure or poll failure close
transfer with a host diagnostic and `policy_write_error`; only an actual
failed write supplies `policy_transfer_error.errno`.

On any transfer failure the host closes input, skips ready/sentinel polling,
requests exit and uses the [host observation](#host-observations)
grace/termination/reaping contract. Partial publications and independent
cleanup observations reach the ordinary assembly path. Published worker
failure retains summary precedence; the transfer observation stays available.
If the worker reaches EOF after input closes, it publishes the count it read
and refuses a different length before compiling. The worker can be terminated
before either publication or before its own exit; a refusal publication alone
does not establish voluntary exit or reaping during grace. When the host
observes a worker failure it takes `runner_failed` precedence, with the host's
transfer observation, stop reason and cleanup trigger retained. Without an
observed failure a transfer timeout remains `runner_timeout`. Neither
classification supplies publication, kill or exit evidence the account lacks.
Successful transfer begins the separate readiness wait. The deadline does
not bound final blocking reap, cancel an earlier client timeout, or contain
all descendants. Readers must consider the timeout
object and stop reason as well as the errno-bearing write-error object.

## Admission and validator/controller receiver contract

Capacity limits use `runner_result.admission_failure`, decided by the runner
host from the decoded request before semantic validation and before
shared-memory setup/spawn, so no later diagnostic (empty operation, duplicate
step ID, dlopen or spawn failure) quotes an unbounded string. Its fields are
`origin=runner_host`, `field`, `actual`, `maximum`, `unit`, and optional
`step_id`, `step_index`, `parameter_key`, `index`. `utf8_bytes` counts payload
bytes (excluding the terminating C NUL); `items` counts entries. `nul_bytes`
counts forbidden embedded NULs in native C-string fields against maximum zero. Limits remain source <!-- span limits.policy_source.value_unit -->262,143 UTF-8 bytes<!-- /span -->, steps <!-- span limits.probe_steps.value -->256<!-- /span -->,
parameters <!-- span limits.policy_parameters.value -->1,024<!-- /span -->, step ID <!-- span limits.step_id.value_unit -->63 UTF-8 bytes<!-- /span -->, target <!-- span limits.attempt_target.value -->511<!-- /span -->, parameter key/value <!-- span limits.parameter_key.value -->127<!-- /span -->/<!-- span limits.parameter_value.value -->383<!-- /span -->, supplied exec
args <!-- span limits.exec_arguments.value -->15<!-- /span --> of <!-- span limits.exec_argument.value_unit -->127 UTF-8 bytes<!-- /span --> each, the host-only `sandbox_check.operation` and
`sandbox_check.filter.value` strings 127/511, the filter kind and attempt
kind/action labels 127 each (unrecognized labels included), `specimen_id` 255,
`run_kind` and `policy.format` 63 each, and the worker/validator executable
override paths 1023 each. A refusal never repeats the string it refused: the
reply carries no steps, `step_index` names the position of a refused step ID
and `step_id` is omitted, a refused parameter key is omitted, a refused
`specimen_id` reads `<admission_refused>`, a refused `run_kind` is omitted, a
refused format reads `unknown`, and a refused seam path is dropped from the
mirrored `test_overrides`. Selection of the first violation does not exempt
other metadata: the refusal builder independently sanitizes all echoed fields.
The same gate and builder serve direct orchestration; decoder failures use bounded
category/path text. The worker's reader independently refuses a policy whose
length at EOF differs from the header's `policy_bytes_expected` (operation 2,
code `PW_FAILURE_SOURCE_LENGTH` = 13, exit 11, detail the received count) and an
embedded NUL (operation 2, code `PW_FAILURE_SOURCE_NUL` = 9, exit 9, detail the
byte offset) instead of compiling a prefix, and refuses an expectation the
source buffer cannot hold before reading (operation 1, code
`PW_FAILURE_LENGTH_EXPECTATION` = 12, exit 10). The shared-memory string slots
carry no length, so for them the host rule is the only guard. `PW_SHM_POLICY_BYTES`
and its Swift mirror include the source NUL. The C reader independently refuses
oversized source when driven directly; normal CLI oversized source is a host
`bad_request` with no subprocess. Policy-write interruption controls use admitted
source sizes and retain their separate host and child observations.

`ValidatorClient.swift` owns the record acceptance rules, stated beside its
byte-frame decoder. `PWRunnerPredictionEvidence.swift` owns the JSON representation. A complete
allow/deny record requires native integer rc/errno, nonempty step ID/operation/
filter type, kind, schema and outcome. Diagnostic outcomes require string error,
but can omit native results; unfamiliar outcomes and extra raw JSON fields are
preserved. Booleans, strings and fractional values cannot stand in for integers.
Parsing never turns a missing native result into a prediction.

When validator `posix_spawn` returns nonzero, `phases[].validator_spawn_failure` retains
`origin: runner_host`, `operation: posix_spawn`, the exact `executable_path`,
numeric `return_code`, and native `strerror` text as `diagnostic`. The return code
is captured directly, independently of ambient errno, with no recognized-code
allowlist or diagnostic-string classification. Unknown codes remain failures.
No validator PID or subprocess is invented. Collection closes and releases the
worker normally; missing predictions remain unestablished.
The record survives worker-summary precedence and evidence-preserving reply
degradation. The explicit `evidence_retained: false` backstop may omit it along
with the other observations. This optional field is additive; absence is
unknown. The controller forwards it unchanged.
The live ENOENT witness checks the native code, path and call context without
requiring English wording. Internal native-call controls exercise unfamiliar
returns through orchestration and reply serialization; they are not policy
evidence and no request override selects them.

`phases[].validator_subprocess` names its phase with `phase_id` and `ordinal`
and retains all accepted `records` with original `raw_line`,
including explicit null step IDs. Its `expected_step_ids` and `association_issues`
record missing, duplicate, unexpected and unassociated IDs, plus query mismatches.
Only a unique record matching the submitted query enters the step join;
duplicate records remain in the matching phase's `validator_subprocess.records`
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
worker. Absent optional host fields are unknown. The validator's `.success` driver
variant only means no transport/decoding error; it cannot establish clean
process disposition. `validator_unavailable` includes incomplete ID coverage,
association faults, cleanup requests, non-EINTR wait faults and abnormal or
unconfirmed disposition even with enough records. `validator_decode_failure`
identifies the receiver's UTF-8/JSON/structure boundary; `validator_no_reply`
identifies I/O failure. Worker summary precedence does not discard the validator
subprocess evidence. All original validator pipe descriptors close on exec;
parent writes use FD-scoped SIGPIPE suppression and checked nonblocking setup.

For the runner client and sbpl-check, the controller collects full
`Command::output()` buffers before retaining a <!-- span limits.controller_output.binary -->152 MiB<!-- /span --> prefix per runner-client
stream (three times the synthesized maximal reply in `docs/limits.json`, rounded
up to 4 MiB) and an independent <!-- span limits.policy_helper_output.binary -->8 MiB<!-- /span --> prefix per sbpl-check stream.
Each capture object's `stdout_bytes_received` and
`stderr_bytes_received` are exact full lengths; `*_bytes_retained` are measured
before lossy text conversion; `capture_limit_bytes` reports the selected receiver
budget (<!-- span limits.controller_output.value -->159,383,552<!-- /span --> or <!-- span limits.policy_helper_output.value -->8,388,608<!-- /span --> bytes). Locally truncated
stdout is not parsed and has `stdout_capture_error`, distinct from
`stdout_parse_error` for malformed JSON/UTF-8 within the cap. Text context may use
replacement characters; accepted JSON is parsed from original untruncated bytes.
Synthetic non-invocations have null received/retained counts. This cap is not a
streaming allocation bound, and inner records cannot be promised when their
outer envelope was lost. Independent `sbpl-check` admission remains
`policy_too_large` in both helper status and missing-reply note prose.

Readiness, bounded policy transfer, the nominal 120s worker polling budget,
synchronous 30s validator I/O and default 240s client timeout remain separate
stages. The worker has a separate local exec attempt budget; no end-to-end
worker deadline is implied. Failed cleanup can leave an unreaped child. Exec
attempt reaping is nonblocking and bounded by exec_reap_grace; the host's
worker/validator final reap after successful termination remains blocking. No early
stderr capture is added: pre-mapping, direct dependency output and crashes in the
reporting path may leave no diagnostic text. Optional compiled-object capture
(<!-- span limits.compiled_profile.binary -->1 MiB<!-- /span -->) and exec stream text (<!-- span limits.exec_stream.value_unit -->1,023 bytes<!-- /span --> each, with truncation marker) keep their
existing refusal/truncation semantics. Neither optional capture failure nor an
incomplete post-apply attempt proves a policy cause or instrumentation defect.

## Query and receiver evidence

`steps[].sandbox_check.pid` is the spawned worker PID, or explicit null when no
worker exists. It never substitutes the host PID. Typed readers must accept
null. Request schema and worker ABI are separate contracts.

The query channel's `native_rc` is authoritative for native returns. A received
diagnostic without a native return retains `result_source="validator"`,
`native_rc=null` and `rc=-1`; this is not a synthetic validator record or a
claimed native failure. Missing replies use synthetic `rc=0`, `outcome="error"` with a
missing reason. `outcome="error"` alone does not identify a native call failure.

Query planning records each phase's submitted probes or exclusions before that
phase's actions run. A later create/unlink does not revise the retained decision,
including when all queries were excluded and no validator ran. The next phase
plans afresh and can observe a changed path. Only unique records matching the
submitted `(operation, filter_type, filter_value)` supply a step prediction.
Mismatch records remain under `phases[].validator_subprocess.records`, with
`association_issues.kind="query_mismatch"`, a missing step prediction and a
non-ok run.
Diagnostics may omit query metadata; any metadata they supply must agree.
Queries and attempted operations remain independent.

An input write failure stops writes but does not stop stdout collection. The
host drains under the original I/O deadline. `io_error` retains the first write
failure (or read failure when no write failed); `read_error` independently retains
a read/poll/deadline failure. `stdout_collection_stop` is `eof`, `deadline`,
`read_error` or `poll_error`. EOF describes observed collection completion, not
validity of all received frames. Decoding faults coexist with these observations.

The controller's runner-client and sbpl-check receivers use the same
original-byte JSON parser with explicit retention budgets: <!-- span limits.controller_output.binary -->152 MiB<!-- /span --> per runner-client stream and <!-- span limits.policy_helper_output.binary -->8 MiB<!-- /span --> per sbpl-check stream.
Received/retained byte counts precede lossy context conversion and count fully
collected buffers. These are retention limits, not peak-memory bounds.
`stdout_capture_error` identifies local truncation and precludes parsing the
prefix; `stdout_parse_error` identifies malformed untruncated bytes. Helper
`status="invalid_reply"` means parsed JSON is not a supported helper envelope
(the helper kind, the current controller envelope version and a nonempty
`result.normalized_outcome`); the parsed output is retained unchanged and no
verdict is derived from it.
Deny plus EPERM/EACCES is a `permission_failure` observation beside a deny
answer; the record relates the submitted scopes and never assigns the cause. A
separate query target is `different_submitted`. The direct DAC control remains
test-owned evidence, not a runtime observation used to assign the cause.


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

Rust subprocess controls compare complete received JSON for both capture
paths, including unfamiliar diagnostics beside fixture-supplied failed reports. Local
truncation precludes parsing and cannot be mistaken for diagnostic rejection.
These helper controls test receiver transport; they do not manufacture real
XPC loss, helper compilation failure. The normal worker
success/failure controls continue to establish native attribution separately.

See [fixture documentation](fixtures/diagnostic_transport/README.md) for fixture boundaries and
`witness_contract/unfamiliar_diagnostic_transport` for CLI assertions. Temporary
code-filtering and detail-dropping mutations are test experiments only; source
and the signed app must be restored before acceptance.

## Comparison record

### Claim/evidence review

| Join / observation owners | Association and stage guarantee | Counterexample / limit | What the record states |
| --- | --- | --- | --- |
| Submitted query → validator record; host and validator | Unique step ID plus exact submitted operation/filter tuple; host invokes validator after observing worker application | A correctly associated query for A need not concern attempted B; a late validator can query changed state | The record answers the submitted query, not necessarily the attempt |
| Query → attempt; host request and completed worker slot | Host retains both independently supplied inputs and pairs by unique step ID | Different operations/targets; compound create; broad or unscoped query; same path spelling with different runtime resolution | An explicit relation between submitted operations/targets, separately from any outcome judgment |
| Query time → attempt time; host and two children | Application → closed query collection → host release → worker acknowledgement → attempts; eligible uniquely associated native records acquire query_first | External state can change during the interval; earlier attempts can affect later attempts | Established order for eligible records, without stable state or runtime identity claims |
| Path enrichment → query/attempt; runner host | Host resolves submitted query path after the orchestrator returns | Worker unlinks the path before host resolution; host and sandboxed worker can resolve differently | Later host diagnostic, never an earlier validator/worker observation |
| Test control → runtime interpretation; test harness and PW | Controls can establish expected meanings independently of the classifier | Direct unsandboxed execution or a fixture oracle is not an observation available in a normal PW envelope | Credit controlled interpretation separately from native observation; no test knowledge silently becomes runtime attribution |

### The record

`steps[].comparison` contains `observation`, `observation_basis`,
`operation_relation`, `target_relation`, `order` and `limitations`, and nothing
else. It relates the two channels; it does not say whether they agree, and no
field in a reply does.

```json
"comparison": {
  "observation": "succeeded",
  "observation_basis": "completed_worker_status",
  "operation_relation": "matched",
  "target_relation": "same_submitted",
  "order": "query_first",
  "limitations": []
}
```

| Path | Type | Rule |
| --- | --- | --- |
| `observation` | string | the attempt channel classified: `succeeded`, `permission_failure`, `other_failure` or `unavailable` |
| `observation_basis` | string | the fields the classification rests on: `completed_worker_status` (completed result, `attempt.outcome` and PW status `rc`), `permission_errno` (worker-reported EPERM/EACCES on a file, access, unlink, sysctl or failed-spawn result), `bootstrap_permission_result` (the exact `bootstrap_look_up: kr=1100` report), `spawned_child` (positive `child_pid` in a completed result, independently of the child's later exit) or `no_completed_worker_result`. None identifies the enforcing mechanism. |
| `operation_relation` | string | `matched` when the submitted query operation is the attempt's mapped operation (file `open_read`/`access`/`read_fresh` → `file-read-data`, `open_write`/`write_fresh` → `file-write-data`, `unlink` → `file-write-unlink`, exec `spawn` → `process-exec*`, mach lookup → `mach-lookup`, sysctl read → `sysctl-read`); `different` when it is another operation; `unresolved` for compound `file`/`create` or `file`/`create_fresh`, or an unsupported attempt |
| `target_relation` | string | `same_submitted` or `different_submitted` by comparing the submitted `filter_value` with the submitted attempt target under the attempt's mapped filter kind (`path` for file and exec, `global_name` for mach lookup, `sysctl_name` for sysctl); `unresolved` when the query's `filter_kind` differs from that kind or either side is absent. Different strings establish different submitted targets, not distinct runtime objects. |
| `order` | string | `query_first` only when the host closed collection before storing release, the worker acknowledged release after successful application, worker ownership was retained through acknowledgement, and a unique native allow/deny record matches the exact planned query tuple with coherent rc/errno; `unestablished` otherwise. It names an interval before that phase’s entire action batch, not a state snapshot or per-step interleaving. |
| `limitations` | array of string | may be empty. Vocabulary: `query_plan:path_unresolved_at_planning`, `query_plan:prediction_unavailable_pair`, `query_plan:unrecognized_filter_kind` (the planner's exclusion, one at most) and `attempt:lifecycle_unresolved`, `attempt:lifecycle_conflicting`, `attempt:unsupported`, `attempt:not_reached`, `attempt:started_without_result` (the lifecycle summary when it is not `completed`, one at most). Missing channels, scope differences and failures carry no limitation of their own: their fields already say so. |

The raw query answer stays in `sandbox_check`: it is `outcome` when
`result_source` is `validator` and the outcome is `allow` or `deny`; otherwise
`missing_reason` explains the unavailable answer. These labels classify native
returns. An otherwise eligible answer qualifies as a prediction about a live
specimen only with its phase's established chain, reflected by `query_first` in
an ordinary reply. The chain does not require an attempt, phase or run to succeed.
`phases[].ordering` carries the host's collection, release,
acknowledgement and lifetime observations that `order` is derived from
(`collection_closed_before_proceed`, `proceed_set`, `proceed_observed`,
`worker_lifetime_established`, `validator_disposition`, `protocol_violations`);
contradictory observations stay visible, carry a protocol violation and
establish no order. Validator disposition is `not_invoked`, `not_needed`
(empty query plan), `not_spawned`, `reaped` or `unconfirmed`; collection
closes when the synchronous driver returns, even after partial output or
failed cleanup, and no later record enters predictions.

#### Phase association and partial publication

`phases` is ordered by one-based `ordinal`. Each record carries a unique
`phase_id`, ordered `action_ids`, `arrival_observed`, `completion_observed`,
`collection_status`, and, when a worker exists, `ordering`. Validator process
and spawn-failure evidence belong only to this record. `steps[].phase_id` must
match the unique phase containing its `step_id`. Concatenated phase action IDs
partition ordinary steps and native events: filtering for either kind preserves
that array's order, and every action occurs exactly once. The simple `probe_plan` has one phase,
`main`. Admission refusals have no phases or steps.

Collection status is `not_reached`, `not_needed`, `collected`,
`budget_exhausted` or `clock_unavailable`. `collected` means the synchronous
driver ran and returned, including timeout, decode failure and failed cleanup;
it does not mean every query received a usable answer. Planning is repeated at
each arrival. A path missing then has `prediction_unavailable`,
`query_plan:path_unresolved_at_planning` and `order: unestablished`, while its
attempt can still run. Later path diagnostics cannot replace this observation.

Collection status must agree with the independent validator account:

| Collection status | Compatible validator disposition | Process/spawn evidence |
| --- | --- | --- |
| `not_reached` | `not_invoked`, or no ordering when there is no worker | Neither present |
| `not_needed` | `not_needed` | Neither present |
| `collected` | `not_spawned`, `reaped`, `unconfirmed` | A failed spawn can have its own record; local driver setup can fail before spawning. A child requires its matching reap disposition and excludes a spawn-failure record. |
| `budget_exhausted` | `not_spawned` | Neither present |
| `clock_unavailable` | `not_needed` before planning, or `not_spawned` after a nonempty plan | Neither present |

`collected` does not require successful spawning, complete output, zero exit
status or confirmed cleanup. Contradictory combinations cannot support ordinary
encoding or reader claims; a degraded reporting-failure reply can retain the
conflict without recovering those claims. The hand-reviewed
[collection controls](fixtures/contract/phase_collection.json) exercise the
encoder, Rust disposition reader and both Python reader entry points; live
phase/validator controls establish the corresponding production paths.

A worker publishes arrival, waits for the exact release ordinal, publishes
acknowledgement, performs the phase's actions, then publishes completion.
Earlier ordinals cannot release a later phase; a future ordinal is a protocol
failure. Host release requires collection closure, the expected arrival,
previous phase completion and retained worker ownership. Loss or expiry during
collection withholds release while preserving already collected records.
`query_first` uses only the matching phase's validator records and ordering.
Neither a previous phase's acknowledgement nor another phase's record can
supply the missing chain. The same worker acknowledging after collection closes
establishes that it lived through that collected interval. A later worker death
does not erase an acknowledgement observed while ownership was established.
After confirmed reap, final reconciliation can acquire an acknowledgement missed
between earlier samples, even following fatal termination without `done`; it does
not restore an ownership chain broken before acknowledgement. Reconciliation
does not rewrite the poll stop reason or a previously observed deadline.

If the worker refuses while collection continues, the synchronous collector keeps
its existing deadlines and closure rules. Received allow/deny/error records
remain raw observations; without the phase chain they do not qualify as live
specimen predictions. Missing acknowledgement does not prove the target was dead
during any particular query. No per-query liveness inference is required. A
degraded `runner_reporting_failed` reply retains ordering only as diagnostic
evidence and omits every comparison; consumers must not recover certified order
from that retained chain.

Phase completion and action completion are separate publications. A missing
completion stays missing even if an action result exists; a later boundary
cannot fill in an unpublished result. Progress operation `PW_OP_PROCEED`
identifies the next phase's first action index, which can equal the total
count at an empty final phase. It records a wait, not entry into that action.
The request has one fixed policy application and one worker for every phase.
These publications establish intervals, not stable target identity or effective
kernel permission state. `PhaseProtocolTests`, `OrderingTests` and the barrier
mutation control check independent file effects, stale/future releases,
interrupted collection and retained earlier evidence.

#### Ordering evidence states

C/S/O are `collection_closed_before_proceed`, `proceed_set` and
`proceed_observed`. Rows give the final observations for each scenario.

| Scenario | C/S/O | Validator disposition | Per-step order |
| --- | --- | --- | --- |
| No worker spawned | No ordering object | No snapshot | `unestablished` on any emitted step |
| Worker exists, application not confirmed | false/false/false | `not_invoked` | `unestablished` |
| Applied, no planned queries, release acknowledged | true/true/true | `not_needed` | `unestablished`; no prediction exists |
| Setup/spawn failed, release acknowledged | true/true/true | `not_spawned` | `unestablished`; an observed native spawn failure is retained in `phases[].validator_spawn_failure`; local setup can fail before a spawn record exists |
| Eligible records, release acknowledged | true/true/true | `reaped` or `unconfirmed` | `query_first` for eligible records only |
| Partial, diagnostic or rejected records, release acknowledged | true/true/true | `reaped` or `unconfirmed` | `query_first` only for eligible associated records; all others `unestablished` |
| Proceed expired or worker died during collection; closure later observed | true/false/false | actual terminal disposition | `unestablished`; received records survive |
| Worker died or hung after acknowledgement | true/true/true | actual terminal disposition | eligible records retain `query_first`; missing attempts remain unavailable |

#### Ordering protocol names

| Thing | Name | Where |
| --- | --- | --- |
| Release ordinal | `proceed` = phase index + 1 | shared header; [layout golden](fixtures/contract/abi_layout.txt) |
| Latest acknowledgement ordinal | `proceed_observed`; immutable `phases[i].acknowledged` | shared header; [layout golden](fixtures/contract/abi_layout.txt) |
| Worker operation | `PW_OP_PROCEED` = 11; clock setup `PW_OP_CLOCK_SETUP` = 12 | `pw_probe_runner_abi.h` |
| Worker failure | `PW_FAILURE_PROCEED_TIMEOUT` = 8; local timing refusal `PW_FAILURE_TIME_INVALID` = 14 with a `PW_TIME_REASON_*` detail | `pw_probe_runner_abi.h` |
| Worker budget | `PW_PROCEED_WAIT_MS_DEFAULT`, limit id `worker_proceed_wait` | `pw_probe_runner.c`, `docs/limits.json` |
| Worker argv seam | `--proceed-wait-ms` | C harness only; no request override |
| Request overrides | `validator_io_timeout_ms`, `validator_total_timeout_ms` | `PWRunnerTestOverrides` |
| Per-phase evidence | `phases[].ordering` | reply |
| Per-step evidence | `comparison.order` | reply |
| Host reply failure | `runner_reporting_failed`, `reporting_failure` | reply; comparisons absent |
| Failed validator launch | `phases[].validator_spawn_failure` | reply; optional and additive |
| Native gated validator | `tests/fixtures/validator/bridge.m`, suite `validator_bridge` | test equipment |

### Invariants

- Producer: `PWRunnerStepResult` has no `drift` or `deny_signal` property;
  `PWRunnerComparison` has no `prediction`, `conclusion`, `scope`, `drift` or
  `obligations`; `PWRunnerAttemptResult` has no `exit_code`, `syscall_errno`
  or `native_rc`; `PWRunnerSandboxCheckResult` has no `scope`;
  `PWRunnerRunResult` has no `deny_signal_total` or `comparison_conditions`;
  there is no signal result type. The reply-shape golden
  (`tests/fixtures/contract/response_shape.json`) records every key the
  encoder emits, from the field-complete fixture and the production-shaped
  documents beside it.
- Encoder: rejects `limitations` strings outside the vocabulary above and
  retains the `query_first`, disposition and reply-degradation checks. Swift
  ignores unknown keys after the version gate; no strict unknown-key decoder
  exists.
- Reply degradation: `runner_reporting_failed` omits every `comparison`, even
  when `steps: []`. `evidence_retained: false` still withholds step and
  subprocess evidence.
- Consumer (`tests/lib/consumer.py`): applies the exact envelope and response
  gates and reports another version as `unsupported`; validates every object
  it reads against the shape golden for its path
  (`tests/fixtures/contract/envelope_shape.json` for the envelope's own
  objects, `response_shape.json` for the reply), so a key no current producer
  emits is rejected at the path where it appears and a present key must carry
  the golden's type; rejects any `limitations` string outside the vocabulary;
  validates `observation`, the two relations and `order` against the raw
  channel fields and `ordering`. The goldens are allowlists, not required
  sets: absence is allowed.
- Controller: `validate_disposition` checks the lifecycle
  entries in `comparison.limitations`, and failed validation withholds the
  projected disposition and termination cause. Every semantic projection runs
  behind the response-version gate.
- Host invariance: the XPC host never links, loads or calls libsandbox.
  `source_drift` rejects bindings, calls and dynamic lookups of the sandbox
  SPI under `runner/Sources/`; the artifact inspection fails a shipped
  `PWRunner` whose `nm -u` output names any `_sandbox_*` symbol.

### Reading rules

This list is the one text of the reading rules. `docs/generate_limits.py`
copies it into the guide's
[Reading a comparison record](../docs/PolicyWitness.md#reading-a-comparison-record)
for readers of an envelope, and `source_drift` fails when the copy differs.
Tests assert the evidence each scenario establishes, by field, and never a
label.

<!-- BEGIN SHARED READING RULES -->

1. The raw query answer is `sandbox_check.outcome` when `result_source`
   is `validator` and the outcome is `allow` or `deny`; otherwise
   `sandbox_check.missing_reason` explains the unavailable answer. An otherwise
   eligible answer qualifies as a prediction about a live specimen only with
   its phase's collection/release/acknowledgement chain, reflected by
   `comparison.order: query_first`. Neither successful attempts nor a successful
   run are required. Without that chain, retained native answers do not establish
   whether the target was live during any particular query. A degraded
   `runner_reporting_failed` reply certifies no per-step order, even when raw
   ordering observations survive; every comparison is omitted.
2. `attempt.missing_reason` explains an unavailable attempt channel.
3. A `permission_failure` or `other_failure` observation, or an exec attempt
   whose spawned child exited nonzero, does not attribute the failure to the
   sandbox. The envelope does not establish that sandbox enforcement caused a
   particular attempt's failure.
4. A `path` query, or an attempt whose mapped filter is `path`, never
   establishes that both channels resolved the same object at runtime.
5. No record establishes that the state the query saw is the state the
   attempt met; nothing in a reply discharges this.
6. A worker `unlink` of a submitted path with `outcome: ok` and `rc: 0`
   records removal at that action. For a path query of that same submitted
   spelling in the same phase, `order: query_first` establishes that the query
   preceded the unlink. `order: unestablished` supplies no ordering inference.
   For actions in different phases, use the corresponding completion and arrival
   publications to establish sequencing; the query's `order` applies only to
   its own phase. A later same-path query can follow an earlier unlink and
   recreation. None of these fields establishes stable object identity.
7. A `process-exec*` query predicts target admission only, not every spawn
   prerequisite; the child's result is in `attempt.rc` and
   `attempt.child_exit_code`.
8. A `file`/`create` attempt has no single query operation, so
   `operation_relation` is `unresolved`.
9. A query operation containing `*`, other than `process-exec*`, resolves to
   no single attempt operation.
10. `target_relation: unresolved` means the attempt's mapped filter kind
    differs from the query's `filter_kind`, or `filter_value` or
    `requested_path` is absent; those fields show which.
11. `sandbox_check.path_diagnostics.realpath_resolved` null on a query the
    planner did not exclude means the host could not resolve the submitted
    path after the run.
12. An attempt the worker does not support has `attempt.outcome` and
    `missing_reason` saying so, and both relations `unresolved`.
13. Extension issuance, delivery, consumption and release are independent
    observations. A pre-call marker without result publication supplies no
    native result. A successful consume/release does not establish effective
    access or revocation; read later fresh-descriptor attempts separately.
14. A lifecycle action has no ordinary comparison. `query_first` on an ordinary
    action refers to its phase's collection, including when an earlier consume
    or release in that phase changed what the attempt later encountered.

<!-- END SHARED READING RULES -->

### Scenario matrix

`tests/fixtures/comparison/matrix.json` is the single source of these rows:
each carries the specimen inputs, the raw channel values the Swift reader
feeds to the producer, the raw fields the live reader asserts beside the
record, an independent control and the expected record. S09 is explicitly
constructed-only: its unsupported attempt is refused by public admission,
while the unit reader exercises defensive handling of constructed results.
`docs/generate_limits.py` renders the table below from it, and `source_drift`
fails when the committed table differs from the generator's output. The query column is
`sandbox_check.outcome` when `result_source` is `validator` and the outcome is
`allow` or `deny`, otherwise `unavailable`. Specimen S runs the real
validator; B steers it with `stub_validator.py` through
`_test_overrides.validator_executable_path` (its records are stub output, so
its expectations come from submitted scopes and independent file and
permission controls, never from native verdicts); C fails to compile; T is the
FIFO deadline case. M01–M07 combine native issuance, delivery and lifecycle
faults through the CLI. M08 uses the production phase driver with controlled
validator calls to combine a collection timeout, failed termination, unconfirmed
reap and late output; its validator transcript is controlled fixture output.
The ordinary worker performs a fresh read of independently prepared bytes.
Lifecycle limitations in the table come from the step's summary.

<!-- BEGIN GENERATED SCENARIO MATRIX -->

| Row | Specimen | Scenario | Query | Observation | Basis | Operation | Target | Order | Limitations | Independent control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | S | allow, read succeeds | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | readable bytes unchanged after the run |
| S02 | S | deny, read EPERM | `deny` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | policy denies file-read-data on this literal path; denied bytes unchanged; the failure is read under reading rule 3 (the envelope does not attribute it to the sandbox) |
| S03 | S | allow, mode-000 file EACCES | `allow` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | direct open of locked outside PW fails with EACCES before the run; mode 0000 is a DAC condition, not policy |
| S05 | S | query denied path, attempt other path | `deny` | `succeeded` | `completed_worker_status` | `matched` | `different_submitted` | `query_first` | — | readable and denied bytes unchanged |
| S06 | S | query write, attempt read | `allow` | `succeeded` | `completed_worker_status` | `different` | `same_submitted` | `query_first` | — | readable bytes unchanged |
| S07 | S | absent path, both channels | `unavailable` | `other_failure` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | `query_plan:path_unresolved_at_planning` | absent does not exist before or after the run |
| S08 | S | compound create | `unavailable` | `succeeded` | `completed_worker_status` | `unresolved` | `same_submitted` | `unestablished` | `query_plan:path_unresolved_at_planning` | created is absent before the run and present after it |
| S09 | S | unsupported attempt kind (constructed only) | `allow` | `unavailable` | `no_completed_worker_result` | `unresolved` | `unresolved` | `query_first` | `attempt:unsupported` | constructed channel results exercise the defensive comparison; public admission refuses the request (request-contract unknown_attempt example) |
| S10 | S | sysctl planning exclusion | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | `query_plan:prediction_unavailable_pair` | the planner's prediction_unavailable set lists (sysctl-read, sysctl_name); a direct sysctlbyname of kern.osrelease succeeds |
| S11 | S | bare process-exec query, spawn ok | `unavailable` | `succeeded` | `spawned_child` | `different` | `same_submitted` | `unestablished` | — | direct spawn of helper_true exits 0; the native API rejects the bare spelling |
| S12 | S | file-read* query | `allow` | `succeeded` | `completed_worker_status` | `unresolved` | `same_submitted` | `query_first` | — | readable bytes unchanged |
| S13 | S | mach deny, kr=1100 | `deny` | `permission_failure` | `bootstrap_permission_result` | `matched` | `same_submitted` | `query_first` | — | policy denies mach-lookup of this global name; kr=1100 is BOOTSTRAP_NOT_PRIVILEGED, read under reading rule 3 |
| S14 | S | mach unknown service, kr=1102 | `allow` | `other_failure` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | no service registers this name; kr=1102 is BOOTSTRAP_UNKNOWN_SERVICE, not a permission result |
| S15 | S | process-exec*, spawn ok, exit 0 | `allow` | `succeeded` | `spawned_child` | `matched` | `same_submitted` | `query_first` | — | direct spawn of helper_true (compiled to exit 0) exits 0; helper bytes unchanged |
| S16 | S | spawn ok, child exits 1 | `allow` | `succeeded` | `spawned_child` | `matched` | `same_submitted` | `query_first` | — | direct spawn of helper_false (compiled to exit 1) exits 1; the child's exit is in attempt.rc and child_exit_code (reading rule 7) |
| S17 | S | spawn of mode-000 target, EACCES | `allow` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | direct posix_spawn of helper_locked outside PW fails with EACCES before the run |
| S18 | S | spawn of absent target | `unavailable` | `other_failure` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | `query_plan:path_unresolved_at_planning` | absent_target does not exist before or after the run |
| S19 | S | ordered unlink of queried path | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | unlink_s19 exists before the run and is absent after it (reading rule 6: this step removed it, after its query) |
| S20 | S | process-exec-interpreter query, binary spawn | `allow` | `succeeded` | `spawned_child` | `different` | `same_submitted` | `query_first` | — | direct spawn exits 0; an accepted interpreter query cannot substitute for the exec query |
| S21 | S | local_name query excluded, kr=1100 | `unavailable` | `permission_failure` | `bootstrap_permission_result` | `matched` | `unresolved` | `unestablished` | `query_plan:prediction_unavailable_pair` | (mach-lookup, local_name) is in the prediction-unavailable set, so the host plans no query and records the exclusion; the global-name deny still refuses the native lookup, and the attempt maps to the global_name filter, so the target relation is unresolved (reading rule 10) |
| S22 | S | none filter on a file query | `allow` | `succeeded` | `completed_worker_status` | `matched` | `unresolved` | `query_first` | — | readable bytes unchanged; no filter value was submitted, so the target relation is unresolved (reading rule 10) |
| S23 | S | allow, access succeeds | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | readable bytes unchanged |
| S24 | S | allow, open_write succeeds | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | writable exists before the run with its 20-byte content and holds exactly the worker's one written byte after it |
| S25 | S | read of the path S19 unlinked, ENOENT | `allow` | `other_failure` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | the query ran before release while unlink_s19 existed; S19's unlink preceded this read |
| S26 | S | fresh read returns independently known bytes | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | Returned bytes equal the independently prepared readable file; its bytes remain unchanged after the run. |
| S27 | S | fresh open fails with permission errno | `deny` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | policy denies file-read-data on this literal path; denied bytes unchanged; the failure is read under reading rule 3 (the envelope does not attribute it to the sandbox) |
| B1 | B | steered deny, read succeeds, ordered | `deny` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | stub transcript supplies deny; b_readable bytes unchanged; the real read succeeds under (allow default) |
| B2 | B | verdict omitted, read succeeds | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | — | stub omits b2; b_readable bytes unchanged |
| B3 | B | verdict omitted, unlink of queried path | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | — | stub omits b3; unlink_b3 exists before the run and is absent after it |
| B4 | B | validator error record | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | — | stub emits a diagnostic record (outcome error, string error, matching step and query metadata); the record is associated, not missing |
| B5 | B | verdict omitted, read of a path B6 unlinks | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | — | stub omits b5; unlink_b6 exists at attempt time because b6 runs after b5 in plan order |
| B6 | B | allow, ordered unlink | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | stub supplies allow; unlink_b6 is absent after the run |
| B7 | B | allow, read succeeds (control) | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | stub supplies allow; b_readable bytes unchanged |
| C1 | C | policy fails to compile, nothing runs | `unavailable` | `unavailable` | `no_completed_worker_result` | `matched` | `same_submitted` | `unestablished` | `attempt:not_reached` | the worker publishes a compile failure record (operation 5) and exits before applying; no validator is spawned; readable bytes unchanged |
| T | T | allow policy, FIFO read starts after release, then worker deadline | `allow` | `unavailable` | `no_completed_worker_result` | `matched` | `same_submitted` | `query_first` | `attempt:started_without_result` | a FIFO with no writer blocks the worker's open inside attempt 0 until the host's sentinel deadline; raw progress, the validator record and the release chain are asserted by the owning case before this row is compared |
| M01 | extension_combinations | issuer publishes a token then exits abnormally; consume and release cannot run | `deny` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | witness_contract/extension_combinations: issuer publishes a token then exits abnormally; consume and release cannot run; compile-time native seam receipt, unchanged independently prepared bytes, transient token leak detector, consumer and lifecycle-oracle checks. |
| M02 | extension_combinations | worker dies midway through framing validation, before delivery publication | `unavailable` | `unavailable` | `no_completed_worker_result` | `matched` | `same_submitted` | `unestablished` | `attempt:not_reached` | witness_contract/extension_combinations: worker dies midway through framing validation, before delivery publication; compile-time native seam receipt, unchanged independently prepared bytes, transient token leak detector, consumer and lifecycle-oracle checks. |
| M03 | extension_combinations | same-phase consume fails natively; release is omitted and fresh read still fails | `deny` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | witness_contract/extension_combinations: same-phase consume fails natively; release is omitted and fresh read still fails; compile-time native seam receipt, unchanged independently prepared bytes, transient token leak detector, consumer and lifecycle-oracle checks. |
| M04 | extension_combinations | cross-phase release returns native failure; earlier consume and fresh read survive | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | witness_contract/extension_combinations: cross-phase release returns native failure; earlier consume and fresh read survive; compile-time native seam receipt, unchanged independently prepared bytes, transient token leak detector, consumer and lifecycle-oracle checks. |
| M05 | extension_combinations | same-phase consume returns natively then worker dies before publication; release omitted | `deny` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | witness_contract/extension_combinations: same-phase consume returns natively then worker dies before publication; release omitted; compile-time native seam receipt, unchanged independently prepared bytes, transient token leak detector, consumer and lifecycle-oracle checks. |
| M06 | extension_combinations | cross-phase release is interrupted before its native call; prior phase evidence survives | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | witness_contract/extension_combinations: cross-phase release is interrupted before its native call; prior phase evidence survives; compile-time native seam receipt, unchanged independently prepared bytes, transient token leak detector, consumer and lifecycle-oracle checks. |
| M07 | extension_combinations | published issuer output and abnormal exit survive when both lifecycle actions are omitted | `deny` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | witness_contract/extension_combinations: published issuer output and abnormal exit survive when both lifecycle actions are omitted; compile-time native seam receipt, unchanged independently prepared bytes, transient token leak detector, consumer and lifecycle-oracle checks. |
| M08 | combined_phase_driver | validator timeout, failed termination and unconfirmed reap followed by late output during a fresh next-phase collection | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | runner_unit PhaseProtocolTests M08: native kill substitution returns EPERM; surviving validator observes EPIPE after collection closure; distinct validator PIDs and exact phase-local record IDs; unchanged target bytes; Rust/Python replay of the production-encoded reply. |

<!-- END GENERATED SCENARIO MATRIX -->

### Ownership

| Rows or invariant | Owner | Independent control |
| --- | --- | --- |
| Specimen S rows in the generated matrix (real validator, except constructed-only S09) | `witness_contract/comparison_matrix` (live); `runner_unit` `ComparisonEvidenceTests` (constructed inputs through `comparisonEvidence(...)`) | Direct file reads, mode-000 opens, helper spawns and absence checks recorded in `direct-controls.json`; file bytes compared before decoding and fresh-read prefixes compared with independently prepared contents |
| S09 (unsupported attempt, constructed only) | `runner_unit` `ComparisonEvidenceTests`; public refusal covered by `runner_outcome_bad_request/accepted_input_contract` | Constructed comparison inputs; the live refusal control proves an earlier valid create did not execute. |
| Specimen B rows in the generated matrix (steered validator) | `witness_contract/comparison_matrix`; `runner_unit` `ComparisonEvidenceTests` | Stub transcript plus file effects; the run ends in `validator_no_reply` while B1, B6 and B7 retain `query_first` |
| C1 (compile failure, nothing runs) | `witness_contract/comparison_matrix`; `runner_unit` `ComparisonEvidenceTests` | Files unchanged; `runner_failed` with the validator not invoked |
| T (FIFO in flight at the deadline) | `witness_contract/worker_attempt_in_flight_at_deadline` (live, with the `a1` specimen of `tests/fixtures/disposition/`); `runner_unit` `ComparisonEvidenceTests` | OS-observed deadline, SIGKILL request and reaped signal; the lifecycle oracle |
| M01–M07 (combined extension faults) | `witness_contract/extension_combinations` (live CLI); `runner_unit` `ComparisonEvidenceTests` (constructed comparisons) | Independent native observer records, target bytes and descriptor checks; row-specific placement, raw, comparison and cleanup assertions |
| M08 (combined ordinary-phase faults) | `runner_unit` `PhaseProtocolTests` (production driver), `ComparisonEvidenceTests` (constructed comparison), and Rust assembly/Python consumer and lifecycle-oracle replay | Failed termination call, unconfirmed host reap, surviving validator's late EPIPE, distinct phase-local PIDs/record IDs, independently prepared fresh-read bytes and separate test cleanup |
| Producer invariants and the shape golden | `runner_unit`: `ContractVersionTests`, `EnvelopeInvariantTests`, `OrderingTests`, `ComparisonEvidenceTests`, `ReplyFailureTests`, `DispositionResolverTests` | Constructed results; mutations must be rejected by the encoder |
| Consumer invariants | `blackbox_e2e/checker_controls` (consumer controls, client-output control, mutation-order controls); every live blackbox, menagerie, filter and witness case through `tests/lib/consumer.py` | Mutated envelopes retained beside their rejection |
| Controller invariants (version gate, outcomes, delivery precedence, projections) | `unit/rust.unit` (`run_flow`, `runner_client`, `dossier` tests); `integration/cli.integration` | Constructed replies of other and malformed versions; live refusals |
| Dossier (`data.specimen`) | `witness_contract/dossier_witness`; opt-in `dossier_witness_byoxpc`; `unit/rust.unit` `dossier` tests | Independently read request bytes, hashes, imports, host sysctls and manifest entries |
| Host invariance | `source_drift` (source rule with controls); `preflight` and `dispatcher/artifact_controls` (binary `nm -u` with a sandbox-importing control host) | Compiled control binaries |

### Supported versions

Semantic readers of runner responses and controller envelopes accept exactly
the versions in [docs/contract.json](../docs/CONTRACT.md): the Swift decoder
and encoder, the Rust controller (`unsupported_runner_response`,
`malformed_runner_response`, with the reply retained and no runner-derived
diagnostics; a delivery failure takes precedence as
`tool_error`), and `tests/lib/consumer.py` (`unsupported`). Raw transport
(`pw-runner-client` and the Rust capture) retains received bytes without
interpreting them. Retained test output and release acceptance artifacts keep
their bytes. Request admission and the worker ABI follow their own contracts;
the ABI's equality tripwire is independent.
Every run of these checks selects through `tests/run.sh` by canonical case
identity in [the catalog](catalog.json); required skips or unrun cases prevent
completion. Acceptance of a change selects the owners named above, release
production runs the default battery, and `--all` is the complete registered
population, including opt-ins and both runner contexts, selected explicitly.

## Exec collection and cleanup evidence

`steps[].attempt.exec_observation` is optional additive evidence. Missing/null
means unavailable, including valid old-producer replies; it never supplies a
negative cleanup, EOF or reap observation. A present object requires a published
worker `exec/spawn` result and positive child PID. Pre-spawn failures, synthetic
results, non-exec attempts and unpublished slots supply none. Slot completion
and lifecycle `completed` describe result publication, not process completion.

`collection` freezes the actual stop branch, `waitid(... WNOWAIT)` leader
observation and each stream's read-zero EOF before cleanup. Terminal waitid,
poll and independent stream read errors remain native errors; poll error flags
remain revents, and timing faults remain nonzero local numeric reason codes.
Actual deadline stops name the selected child/plan cutoff. Reap cannot rewrite
this snapshot. `leader_exit_and_eof` requires all three positive observations
and no terminal collection error/fault.

`cleanup` records termination requests only. `not_requested` and
`ownership_unconfirmed` have no call record. `requested` has the actual negative
group target, SIGKILL, native rc and failure errno. Failed group calls other than
`ESRCH` retain their independent positive-target fallback call. Return zero,
`ESRCH`, no call and a successful fallback are distinct facts; none establishes
group absence. Descriptor/handle cleanup is not included.

`reap` records the final nonblocking wait and actual stop branch. Only a return
of the owned leader permits raw status and the corresponding decoded legacy
exit/signal. A zero return has no errno or status. A failed final wait retains
its errno, including EINTR if a later local guard ends the loop. Native wait
ETIMEDOUT and a local deadline are distinct. A reap-clock fault remains visible
beside an immediate successful reap or a native wait error; unfamiliar bounded
nonzero clock reasons stay numeric. Successful signalling with unconfirmed reap
is valid evidence, not grounds to invent status or reject a reply.

Ordinary Swift reply integrity, Rust admitted-reply checks and the independent
Python consumer validate present types/ranges, branches, targets, wait/status
relationships and publication. Malformed present evidence cannot silently become
absence or a clean default. Degraded reporting-failure replies retain diagnostic
evidence under their existing rules, withholding comparisons. The new object
never supplies a comparison, ordering or run-disposition conclusion.

The native source controls use their independent call ledger to check actual
arguments/returns and preserved wait/signal/clock order. Production C-to-Swift
and encoded-reader controls exercise publication and transport; live process
controls use independent peers/exit observations and separately owned fixture
cleanup. See the [field account](../docs/PolicyWitness.md#structured-exec-observations)
and [native controls](suites/runner_c_worker_harness/README.md#worker-timing-controls).

Exec attempt observation distinguishes stream EOF, leader exit, termination
requests and confirmed reaping. A deadline remains an attempt failure even when
the leader exited naturally while another group member retained the pipes;
`child_exit_code` preserves that observed natural status. Cleanup or observation
errors do not manufacture a child exit or sandbox denial. If the worker dies
before the slot is published, incomplete exec fields remain unavailable even
when an independent observer saw a live child. Supporting earlier spawn facts
in the reply requires a separate publication contract.

Ordinary completion requests no termination. Same-group descendants that close
their streams can survive later work and worker exit; worker loss can interrupt
exceptional cleanup or precede child publication. Descendants that leave the
group can escape requests. The host supervises the worker, not these descendants.

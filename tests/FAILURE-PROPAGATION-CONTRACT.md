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
observation of `done`, and R the `apply_rc` status word. A publishes successful
application; D publishes a terminal worker payload, including pre-apply failure.
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
| Proceed wait expiry (operation 11, code 8) or native clock failure (kind 3) | Preserve budget detail/diagnostic and zero attempts; late release cannot revive | `runner_failed` |
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
[PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) and
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
| `wait_errors` | Host array of observed wait failures, each with phase, signed return and errno; retain errors even if a later wait succeeds |

`sandboxed_after_apply` remains the public application observation; do not add a
second authoritative applied boolean. `sentSigkill` internally must not stand in
for deadline expiry or successful termination/reaping. Absent optional fields
are unknown rather than synthesized observations.
Optional subprocess objects preserve the existing omitted-or-null convention.

The readiness, sentinel and exit-grace budgets are unchanged. The driver allows
two EINTR retries total across polling, grace and final reaping. A terminal wait
error ends that phase; ECHILD stops all further waits and signals to that PID.
There are at most five failed-call records (two recovered interruptions plus one
terminal error per phase), with no error truncation. `wait_errors[].phase` is
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
               "questions": { <step question>: <claim>, ... } }, ... ],   // one per submitted step, in plan order
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
| `plan` | the submitted probe plan's step count and order |
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
compilation 5, capture 6, readiness 7, application 8, proceed 11, then attempt
9 for each step in plan order, then completion 10. An attempt word's item
index names the step; a parameter word's names the parameter. An attempt index
that names no submitted step, including any attempt index for an empty plan,
is `invalid`; a mismatch between the encoded word and its decoded fields, or
an item index on a non-indexed operation, is also `invalid`. An ambiguous slot
identity supplies no associated slot, rather than selecting one duplicate.
An unrecognized operation or phase code is `progress_unrecognized`
and its raw word is retained. Progress at or beyond a step's boundary means a
position at or after that step's `started` word.

| Question | Answer | Sufficient witnesses (any one) | Scope | Rules |
| --- | --- | --- | --- | --- |
| Final status | exit code | successful reap with a valid exit-status representation and no signal representation | any | D1 |
| | signal | successful reap with a valid signal representation and no exit-status representation | any | D1 |
| Stop reason | `done`, `sentinel_deadline`, `child_reaped`, `wait_error`, `policy_write_error`, `policy_transfer_deadline` | the host's poll-loop observation | any | D2 |
| Cleanup trigger | deadline expiry; completion; child reaped during polling; poll wait error; policy transfer error | direct host observation of why exit was requested | any | D2 |
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
| Progress association | none | no progress word; unrecognized operation or phase code, with the raw word retained | whenever a progress word was published | the per-step answers below |
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
| `runner_sandbox_diagnostics.disposition_integrity`, `disposition_issues` | `valid` or `invalid`. Invalid records list their issues with kind `invalid_claim`, `unresolved_reference`, `unrecognized_value`, `missing_record` or `malformed_record`; an invalid record withholds disposition and cause as above. A record that faithfully reports a conflict is valid. |
| `runner_subprocess.partial_steps` | True when any step's slot is not completed, including an unsupported no-op slot. It does not say an attempt never began. |
| `steps[].attempt.lifecycle` | `{"summary", "boundary", "result"}` where `boundary` and `result` are the step's two claims and `summary` is: `unsupported` when the requested operation is unsupported; else `completed` when the result is `published`; else `conflicting` when either claim conflicts; else `started_without_result` (reached, unpublished) or `not_reached` (not reached, unpublished); else `unresolved`. |
| `steps[].comparison.limitations` | Beside the existing entries, exactly one lifecycle entry for a summary other than `completed`: `attempt:started_without_result`, `attempt:not_reached`, `attempt:unsupported`, `attempt:lifecycle_unresolved` or `attempt:lifecycle_conflicting`. Lifecycle entries never change the relations, order or sandbox attribution. |
| `steps[].attempt.outcome`, `missing_reason`, `result_source` | `not_run_worker_died` and `slot_incomplete` mean no completed supported result, which may have started; the lifecycle object carries the distinction. |
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

### Versions

The record is mandatory for every worker reply at the current response
schema, and the controller's `termination_cause`, `stop_reason`,
`disposition_integrity` and `process_disposition` projections belong to the
current controller envelope. `tests/lib/contract.py` carries both numbers and
every reader gates on them exactly. Per [docs/CONTRACT.md](../docs/CONTRACT.md)
the manifest moves with the change that produces them; a rebuilt app must never
report a response number without carrying the shape that number names.

## Public compatibility and correlation

The response, request, controller envelope and worker ABI are separate
contracts, owned by [docs/contract.json](../docs/CONTRACT.md). Semantic readers
accept exactly the current numbers (see [Supported versions](#supported-versions)).
Steps carry no signal channel; a null per-step `errno` requires key presence.

No outcome spelling claims a sandbox termination cause or a precise
application failure: signals and PID-matched denials cannot justify the first,
and an imprecise published status cannot justify the second. The pre-apply
witness case forbids both spellings outright. `runner_failed` covers
execution/reporting failure with cause possibly unknown; it does not mean a
proven host defect. `bad_policy` keeps its existing structural-policy admission
meaning. Published worker failures also use `runner_failed`; the operation/code
record provides the precise account without adding outcome strings.

The pre-apply CLI witness asserts excluded claims, not one exact summary;
the table's classifier controls pin the mapping. The attempt
spelling `not_run_worker_died` means no completed attempt result, not
proof that an operation never started. Synthetic missing predictions retain
`rc=0` with an explicit result source, missing reason, and null native return.

Worker identity comes only from a positive `runner_subprocess.pid`, never a
host/client top-level PID. Capture remains available on successful runs.
`runner_sandbox_diagnostics` describes process disposition and denial
correlation independently of outcome; `sandbox_log_capture.capture_status`
keeps disabled (null capture), no worker, and observer availability distinct.
Correlation status is `not_attempted`, `unavailable`, `no_match`, or
`pid_match`; `permission_failures_without_record` names the steps whose attempt
the runner classified as a permission-shaped failure and that no captured event
names as a candidate, so `no_match` never reads as "nothing was denied" (null
when correlation was not reached or the reply has no per-step comparisons).
Abnormal or unconfirmed disposition has `termination_cause` `unknown` unless the
[worker disposition record](#worker-disposition-record) witnesses host cleanup end to end.
Application remains separately recorded in `sandboxed_after_apply`.

`step_denies` records `{event_index, candidate_step_ids, association,
matching_evidence}`; array position is not time order and a match is not a
cause. One candidate has association
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
rounded outward to whole seconds and padded by two seconds at each end:
`floor(client start) - 2 s` through `ceil(client end) + 2 s`. The raw client
milliseconds are unchanged; `pad_seconds: 2` describes the pad. Supported records in either padding region remain eligible
for correlation. This allowance for client/archive clock differences promises no
delivery or exact run membership. The window explicitly reports no structured event
timestamps, exact run membership, step ordering, or PID-reuse protection. The
observer mirrors the interval it scanned; any other interval is
`window_mismatch`, which retains raw observer evidence but never yields
`step_denies`; correlation is `unavailable`. Reversed client clock
readings produce `invalid_window`, retaining the raw milliseconds with null
`start`/`end` and no observer invocation. Ordered endpoints do not establish clock
continuity. Validator queries can generate worker-PID denial records before
attempts begin, and some denied attempts have no available log record. Neither
path matching nor interval coverage establishes a record's origin or complete
log delivery.
Raw lines remain available. The observer preserves the full remaining target,
including spaces; it does not shorten a path into a different target. PID
matching alone never establishes a termination cause or exact run membership.

Collection uses one finite monotonic allowance across the observer and its log
child, with fixed cleanup grace and streaming byte limits at both boundaries.
Failed or incomplete captures retain bounded diagnostics, but all candidate
associations and missing-record diagnostics are null. Execution
result, CLI exit status, native observations, comparisons and disposition remain
independent. The [controller collection contract](../controller/README.md#log-collection-budgets-and-cleanup)
defines cutoff reasons, retained prefixes, ownership and separate child-wait
versus group-absence observations. Complete empty live queries and evidenced
budget exhaustion with confirmed cleanup are admissible live outcomes; archive
selection and supplied-text preservation controls have strict positive oracles.

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
| `witness_contract/pre_apply_failure_reports_no_policy_verdict` (`check_pre_apply_failure.py`) | Real CLI, populated allowed/denied plan, pre-ready delay and worker deadline; identical un-overridden positive control | Independent attribution, lifecycle and consumer-validation groups require the current response schema; missing channels remain distinct from observed failures |
| `runner_unit/pwrunner_core_unit_executable`: `CWorkerLifecycleTests.runCWorkerLifecycleTests` | Real host driver with test-only ABI child: completed report then cleanup SIGKILL, independent exit 17 or SIGTERM, published status-word failure then cleanup, failed kill, failed/recovered/interrupted wait, ECHILD ownership loss and poll EIO. Actual subprocess assembler and JSON round-trip preserve reports and missing status. Fixture applies no sandbox. | Driver, assembler, encoding and classifier agree; synthetic payload does not establish a native library result |
| `runner_ready_byte_resilience/slow_compile_ready_byte_survives_sigpipe` | Real CLI with sufficient budget; lost ready byte must not prevent successful application, prediction and attempt | Successful resilience verified; delay follows compilation/capture and has sufficient sentinel budget |
| `runner_outcome_runner_timeout/host_kills_hung_worker`, `witness_contract/worker_post_apply_hang_seam`, `runner_use_c_worker/worker_timeout_ms_honored` | Real CLI post-apply deadlines; empty, mixed and single-write plans, retained evidence and independently checked effects | Success/timeout/partial-evidence checks pass; populated pre-apply witness adds distinct absence coverage |
| `witness_contract/worker_termination_and_log_correlation`; Rust `run_flow::tests`, `sandbox_log::tests`, observer parser tests | CLI ordinary denied writes, repeated attempts, independent read queries, self-signal, capture disabled/enabled and successful-run capture. Constructed captures pin PID, operation, target, ambiguity, window and availability semantics. Parser preserves missing identity and full paths without structured timestamps. | Implemented; optional real logs do not replace deterministic populated-event controls or establish a policy cause |
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
following the capture bytes. Host and worker require exactly the same generated source identity, with no fallback. Header offsets 56 and 60 carry proceed and proceed_observed; bytes 64 through 95 carry the identity, and the header is 96 bytes. The reply carries the ordering evidence described below.
The worker record is `data.runner_result.runner_subprocess.worker_evidence`.
Its `abi_identity` is the host-selected SHA-256 source identity encoded as a hex string, not proof the child reached ABI validation.
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

Both step channels carry `result_source` and optional `missing_reason`; the
query channel also carries `native_rc`, emitted as explicit null when
unavailable. The attempt channel has no native-return field.
Prediction rc=0 with outcome=error is a synthetic sentinel:
result_source=synthetic and missing_reason=validator_not_invoked (no validator
process), or validator_no_verdict (process ran without this verdict). Excluded
queries use query_not_requested. Received verdicts use result_source=validator;
native_rc is present only for actual allow/deny/error native call results, not
parse/unsupported/filter rejections. Run-level validator subprocess metadata
remains authoritative; per-step fields do not duplicate PID/disposition.

Attempts use the spelling `not_run_worker_died` for a missing result; it means
no completed result, never proof of non-start. They use result_source=synthetic
and missing_reason=slot_absent or slot_incomplete. Completed supported slots use
result_source=worker. Their rc is PW attempt status (often 0/1, or aggregated
exec disposition), not a native syscall return such as an open FD; the worker
ABI does not carry that raw return, so no attempt field presents one.
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
Counts are not evidence of bytes consumed by the worker. Omission of this
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

The five-second production deadline starts immediately after spawn. The
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
Successful transfer begins the separate readiness wait. The deadline does
not bound final blocking reap, cancel an earlier client timeout, or contain
all descendants. Response schema 15 requires readers to consider the timeout
object and stop reason as well as the errno-bearing write-error object.

## Admission and validator/controller receiver contract

Capacity limits use `runner_result.admission_failure`, decided by the runner
host from the decoded request before semantic validation and before
shared-memory setup/spawn, so no later diagnostic (empty operation, duplicate
step ID, dlopen or spawn failure) quotes an unbounded string. Its fields are
`origin=runner_host`, `field`, `actual`, `maximum`, `unit`, and optional
`step_id`, `step_index`, `parameter_key`, `index`. `utf8_bytes` counts payload
bytes (excluding the terminating C NUL); `items` counts entries. `nul_bytes`
counts forbidden embedded NULs in native C-string fields against maximum zero. Limits remain source 262143 bytes, steps 256, parameters
1024, step ID 63 bytes, target 511, parameter key/value 127/383, supplied exec
args 15 of 127 bytes each, the host-only `sandbox_check.operation` and
`sandbox_check.filter.value` strings 127/511, the filter kind and attempt
kind/action labels 127 each (unrecognized labels included), `specimen_id` 255,
`run_kind` and `policy.format` 63 each, and the three `_test_overrides`
executable paths 1023 each. A refusal never repeats the string it refused: the
reply carries no steps, `step_index` names the position of a refused step ID
and `step_id` is omitted, a refused parameter key is omitted, a refused
`specimen_id` reads `<admission_refused>`, a refused `run_kind` is omitted, a
refused format reads `unknown`, and a refused seam path is dropped from the
mirrored `test_overrides`. Selection of the first violation does not exempt
other metadata: the refusal builder independently sanitizes all echoed fields.
The same gate and builder serve direct orchestration; decoder failures use bounded
category/path text. The worker's reader independently refuses an embedded NUL in
the policy (operation 2, code `PW_FAILURE_SOURCE_NUL` = 9, exit 9, detail the byte
offset) instead of compiling a prefix; the shared-memory string slots carry no
length, so for them the host rule is the only guard. `PW_SHM_POLICY_BYTES`
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
worker normally; missing predictions remain unestablished.
The record survives worker-summary precedence and evidence-preserving reply
degradation. The explicit `evidence_retained: false` backstop may omit it along
with the other observations. This optional field is additive; absence is
unknown. The controller forwards it unchanged.
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
`Command::output()` buffers before retaining a 72 MiB prefix per runner-client
stream (three times the synthesized maximal reply in `docs/limits.json`, rounded
up to 4 MiB) and an independent 8 MiB prefix per sbpl-check stream.
Each capture object's `stdout_bytes_received` and
`stderr_bytes_received` are exact full lengths; `*_bytes_retained` are measured
before lossy text conversion; `capture_limit_bytes` reports the selected receiver
budget (75497472 or 8388608). Locally truncated
stdout is not parsed and has `stdout_capture_error`, distinct from
`stdout_parse_error` for malformed JSON/UTF-8 within the cap. Text context may use
replacement characters; accepted JSON is parsed from original untruncated bytes.
Synthetic non-invocations have null received/retained counts. This cap is not a
streaming allocation bound, and inner records cannot be promised when their
outer envelope was lost. Independent `sbpl-check` admission remains
`policy_too_large` in both helper status and missing-reply note prose.

Log collection instead enforces streaming bounds: 32 MiB observer stdout and
128 KiB observer stderr, containing the inner log-show capture of at most 1 MiB
stdout and 128 KiB stderr. The log child stops 1,000 ms before the shared
deadline so the observer's report can be delivered before the controller's own
deadline. Its received counts describe actual reads, including
at most one excess byte that detects a stream overflow, not the total output
the stopped producer might have emitted. No JSON fragment recovery is attempted.
An intact failed reply can retain diagnostic events, without correlation. These
are stream and derived-data bounds, not a peak-process-memory guarantee.

Readiness, bounded policy transfer, the nominal 120s worker polling budget,
synchronous 30s validator I/O and default 240s client timeout remain separate
phases. The worker has a separate local exec attempt budget; no end-to-end
worker deadline is implied. Failed cleanup can leave an unreaped child. Exec
attempt reaping is nonblocking and bounded by exec_reap_grace; the host's
worker/validator final reap after successful termination remains blocking. No early
stderr capture is added: pre-mapping, direct dependency output and crashes in the
reporting path may leave no diagnostic text. Optional compiled-object capture
(1 MiB) and exec stream text (1023 bytes each, with truncation marker) keep their
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

Query planning records each submitted probe or exclusion reason before attempts
run. A later create/unlink cannot change that decision, including when all
queries are excluded and no validator runs. Only unique records matching the
submitted `(operation, filter_type, filter_value)` supply a step prediction.
Mismatch records remain under `validator_subprocess.records`, with
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

All controller JSON receivers (runner client, sbpl-check and log observer) use
the same original-byte JSON parser with explicit retention budgets: 72 MiB
per runner-client stream, 8 MiB per sbpl-check stream, and streaming limits of
32 MiB stdout / 128 KiB stderr for the observer. Received/retained byte counts
precede lossy context conversion; log collection's counts are actual bounded
reads, while the other receivers count fully collected buffers.
`stdout_capture_error` identifies local truncation and precludes parsing the
prefix; `stdout_parse_error` identifies malformed untruncated bytes. Helper
`status="invalid_reply"` means parsed JSON is not a supported helper envelope
(the helper kind, the current controller envelope version and a nonempty
`result.normalized_outcome`); the parsed output is retained unchanged and no
verdict is derived from it.
The observer uses `capture_status="invalid_reply"` when parsed JSON lacks the
required observation, identity, metadata or supervision shape. An interrupted
outer reply keeps only its bounded raw prefix. Receiver completeness does not
imply that the OS delivered every denial, and a stream limit is not a bound on
the process's total memory.

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

## Comparison record

### Claim/evidence review

| Join / observation owners | Association and phase guarantee | Counterexample / limit | What the record states |
| --- | --- | --- | --- |
| Submitted query → validator record; host and validator | Unique step ID plus exact submitted operation/filter tuple; host invokes validator after observing worker application | A correctly associated query for A need not concern attempted B; a late validator can query changed state | The record answers the submitted query, not necessarily the attempt |
| Query → attempt; host request and completed worker slot | Host retains both independently supplied inputs and pairs by unique step ID | Different operations/targets; compound create; broad or unscoped query; same path spelling with different runtime resolution | An explicit relation between submitted operations/targets, separately from any outcome judgment |
| Query time → attempt time; host and two children | Application → closed query collection → host release → worker acknowledgement → attempts; eligible uniquely associated native records acquire query_first | External state can change during the interval; earlier attempts can affect later attempts | Established order for eligible records, without stable state or runtime identity claims |
| Path enrichment → query/attempt; runner host | Host resolves submitted query path after the orchestrator returns | Worker unlinks the path before host resolution; host and sandboxed worker can resolve differently | Later host diagnostic, never an earlier validator/worker observation |
| Denial event → attempt; observer and controller | Exact worker PID, mapped submitted operation and matching path evidence yield candidates; predictions are queried with `SANDBOX_CHECK_NO_REPORT`, so they produce no records | Repeated attempts, PID reuse, whole-second capture bounds and absent timestamps prevent unique occurrence or causal ordering | Candidate association with inspectable matching basis; no termination cause and no negative proof from no match |
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
| `operation_relation` | string | `matched` when the submitted query operation is the attempt's mapped operation (file `open_read`/`access` → `file-read-data`, `open_write` → `file-write-data`, `unlink` → `file-write-unlink`, exec `spawn` → `process-exec*`, mach lookup → `mach-lookup`, sysctl read → `sysctl-read`); `different` when it is another operation; `unresolved` for a compound `file`/`create` attempt or an unsupported attempt |
| `target_relation` | string | `same_submitted` or `different_submitted` by comparing the submitted `filter_value` with the submitted attempt target under the attempt's mapped filter kind (`path` for file and exec, `global_name` for mach lookup, `sysctl_name` for sysctl); `unresolved` when the query's `filter_kind` differs from that kind or either side is absent. Different strings establish different submitted targets, not distinct runtime objects. |
| `order` | string | `query_first` only when the host closed collection before storing release, the worker acknowledged release after successful application, worker ownership was retained through acknowledgement, and a unique native allow/deny record matches the exact planned query tuple with coherent rc/errno; `unestablished` otherwise. It names an interval before the entire attempt batch, not a state snapshot or per-step interleaving. |
| `limitations` | array of string | may be empty. Vocabulary: `query_plan:path_unresolved_at_planning`, `query_plan:prediction_unavailable_pair`, `query_plan:unrecognized_filter_kind` (the planner's exclusion, one at most) and `attempt:lifecycle_unresolved`, `attempt:lifecycle_conflicting`, `attempt:unsupported`, `attempt:not_reached`, `attempt:started_without_result` (the lifecycle summary when it is not `completed`, one at most). Missing channels, scope differences and failures carry no limitation of their own: their fields already say so. |

The query's answer stays in `sandbox_check`: it is `outcome` when
`result_source` is `validator` and the outcome is `allow` or `deny`; otherwise
no prediction was available and `missing_reason` says why.
`runner_subprocess.ordering` carries the host's collection, release,
acknowledgement and lifetime observations that `order` is derived from
(`collection_closed_before_proceed`, `proceed_set`, `proceed_observed`,
`worker_lifetime_established`, `validator_disposition`, `protocol_violations`);
contradictory observations stay visible, carry a protocol violation and
establish no order. Validator disposition is `not_invoked`, `not_needed`
(empty query plan), `not_spawned`, `reaped` or `unconfirmed`; collection
closes when the synchronous driver returns, even after partial output or
failed cleanup, and no later record enters predictions.

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
| Run-level evidence | `runner_subprocess.ordering` | reply |
| Per-step evidence | `comparison.order` | reply |
| Host reply failure | `runner_reporting_failed`, `reporting_failure` | reply; comparisons absent |
| Failed validator launch | `validator_spawn_failure` | reply; optional and additive |
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
- Controller: `permission_failures_without_record` reads
  `comparison.observation`; `validate_disposition` also checks the lifecycle
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

1. The query channel's answer is `sandbox_check.outcome` when `result_source`
   is `validator` and the outcome is `allow` or `deny`; otherwise no prediction
   was available and `sandbox_check.missing_reason` says why.
2. `attempt.missing_reason` explains an unavailable attempt channel.
3. A `permission_failure` or `other_failure` observation, or an exec attempt
   whose spawned child exited nonzero, does not attribute the failure to the
   sandbox; attribution needs a captured denial record, and
   `permission_failures_without_record` lists the steps that have none.
4. A `path` query, or an attempt whose mapped filter is `path`, never
   establishes that both channels resolved the same object at runtime.
5. No record establishes that the state the query saw is the state the
   attempt met; nothing in a reply discharges this.
6. When a query has `filter_kind: path`, a nonnull `filter_value` and no
   `query_plan:*` limitation, and any step's attempt is a worker `unlink` of
   that same submitted path with `outcome: ok` and `rc: 0`, the target was
   removed during the run; `order` says whether the removal followed the
   query, and the unlink attempt's step is the step that removed it.
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
FIFO deadline case. Lifecycle limitations in the table come from the step's
summary.

<!-- BEGIN GENERATED SCENARIO MATRIX -->

| Row | Specimen | Scenario | Query | Observation | Basis | Operation | Target | Order | Limitations | Independent control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | S | allow, read succeeds | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | readable bytes unchanged after the run |
| S02 | S | deny, read EPERM | `deny` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | policy denies file-read-data on this literal path; denied bytes unchanged; the failure is read under reading rule 3 (no attribution without a captured denial record) |
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
| S21 | S | local_name query, kr=1100 | `allow` | `permission_failure` | `bootstrap_permission_result` | `matched` | `unresolved` | `query_first` | — | the global-name deny does not match a local-name query; the attempt maps to the global_name filter, so the target relation is unresolved (reading rule 10) |
| S22 | S | none filter on a file query | `allow` | `succeeded` | `completed_worker_status` | `matched` | `unresolved` | `query_first` | — | readable bytes unchanged; no filter value was submitted, so the target relation is unresolved (reading rule 10) |
| S23 | S | allow, access succeeds | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | readable bytes unchanged |
| S24 | S | allow, open_write succeeds | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | writable exists before the run with its 20-byte content and holds exactly the worker's one written byte after it |
| S25 | S | read of the path S19 unlinked, ENOENT | `allow` | `other_failure` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | the query ran before release while unlink_s19 existed; S19's unlink preceded this read |
| B1 | B | steered deny, read succeeds, ordered | `deny` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | stub transcript supplies deny; b_readable bytes unchanged; the real read succeeds under (allow default) |
| B2 | B | verdict omitted, read succeeds | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | — | stub omits b2; b_readable bytes unchanged |
| B3 | B | verdict omitted, unlink of queried path | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | — | stub omits b3; unlink_b3 exists before the run and is absent after it |
| B4 | B | validator error record | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | — | stub emits a diagnostic record (outcome error, string error, matching step and query metadata); the record is associated, not missing |
| B5 | B | verdict omitted, read of a path B6 unlinks | `unavailable` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | — | stub omits b5; unlink_b6 exists at attempt time because b6 runs after b5 in plan order |
| B6 | B | allow, ordered unlink | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | stub supplies allow; unlink_b6 is absent after the run |
| B7 | B | allow, read succeeds (control) | `allow` | `succeeded` | `completed_worker_status` | `matched` | `same_submitted` | `query_first` | — | stub supplies allow; b_readable bytes unchanged |
| C1 | C | policy fails to compile, nothing runs | `unavailable` | `unavailable` | `no_completed_worker_result` | `matched` | `same_submitted` | `unestablished` | `attempt:not_reached` | the worker publishes a compile failure record (operation 5) and exits before applying; no validator is spawned; readable bytes unchanged |
| T | T | allow policy, FIFO read starts after release, then worker deadline | `allow` | `unavailable` | `no_completed_worker_result` | `matched` | `same_submitted` | `query_first` | `attempt:started_without_result` | a FIFO with no writer blocks the worker's open inside attempt 0 until the host's sentinel deadline; raw progress, the validator record and the release chain are asserted by the owning case before this row is compared |

<!-- END GENERATED SCENARIO MATRIX -->

### Ownership

| Rows or invariant | Owner | Independent control |
| --- | --- | --- |
| S01–S25 with S04 unused and S09 constructed only (specimen S, real validator) | `witness_contract/comparison_matrix` (live); `runner_unit` `ComparisonEvidenceTests` (constructed inputs through `comparisonEvidence(...)`) | Direct file reads, mode-000 opens, helper spawns and absence checks recorded in `direct-controls.json`; file bytes compared before decoding |
| S09 (unsupported attempt, constructed only) | `runner_unit` `ComparisonEvidenceTests`; public refusal covered by `runner_outcome_bad_request/accepted_input_contract` | Constructed comparison inputs; the live refusal control proves an earlier valid create did not execute. |
| B1–B7 (specimen B, steered validator) | `witness_contract/comparison_matrix`; `runner_unit` `ComparisonEvidenceTests` | Stub transcript plus file effects; the run ends in `validator_no_reply` while B1, B6 and B7 retain `query_first` |
| C1 (compile failure, nothing runs) | `witness_contract/comparison_matrix`; `runner_unit` `ComparisonEvidenceTests` | Files unchanged; `runner_failed` with the validator not invoked |
| T (FIFO in flight at the deadline) | `witness_contract/worker_attempt_in_flight_at_deadline` (live, with the `a1` specimen of `tests/fixtures/disposition/`); `runner_unit` `ComparisonEvidenceTests` | OS-observed deadline, SIGKILL request and reaped signal; the lifecycle oracle |
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
diagnostics or log capture; a delivery failure takes precedence as
`tool_error`), and `tests/lib/consumer.py` (`unsupported`). Raw transport
(`pw-runner-client` and the Rust capture) retains received bytes without
interpreting them. Stored evidence under `records/`, retained test output and
release acceptance artifacts keeps its bytes. Request admission and the worker
ABI follow their own contracts; the ABI's equality tripwire is independent.
Acceptance selects every registered canonical case in [the catalog](catalog.json),
including opt-ins and both runner contexts; required skips or unrun cases
prevent completion.

Exec attempt observation distinguishes stream EOF, leader exit, termination
requests and confirmed reaping. A deadline remains an attempt failure even when
the leader exited naturally while another group member retained the pipes;
`child_exit_code` preserves that observed natural status. Cleanup or observation
errors do not manufacture a child exit or sandbox denial. If the worker dies
before the slot is published, incomplete exec fields remain unavailable even
when an independent observer saw a live child. Supporting earlier spawn facts
in the reply requires a separate publication contract.

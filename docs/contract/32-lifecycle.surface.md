# Process and operation observations {lifecycle: surface}

```contract
syntax: 1
artifact: "Process and operation observations"
part: "report"
goldens: ["tests/fixtures/contract/surfaces/lifecycle.json", "tests/fixtures/disposition/current/constructed_deadline.json"]
checks: ["runner_unit"]
```

## Worker subprocess {worker: subject}

```contract
record: "PWRunnerSubprocess"
as: "lc_worker"
```

The host retains one process account for the fresh worker. Actor replies put this account on its actor; single-worker replies put it at run scope.

### pid {pid: field}

PID returned by successful worker spawn and used for host waits and cleanup.

### term_signal {term_signal: field}

Signal decoded from a successful waitpid result for this child. A recorded cleanup request alone supplies no value here.

### exit_code {exit_code: field}

Exit status decoded after waitpid returned this child; zero is an observed exit status. Missing status stays unknown.

### partial_steps {partial_steps: field}

True when the canonical disposition contains any slot other than completed; false means all represented slots completed.

### worker_evidence {worker_evidence: field}

Acquired worker publication snapshot, including independent progress, failure, diagnostic and policy-read observations.

### policy_transfer_timeout {policy_transfer_timeout: field}

Host policy-pipe deadline observation with accepted-write counts.

### policy_transfer_error {policy_transfer_error: field}

Host policy-pipe native write failure with accepted-write counts.

### ready_byte_received {ready_byte_received: field}

Whether the host read the worker's readiness byte. False records the missing hint at that boundary.

### done_observed {done_observed: field}

Final acquire observation of the worker's done flag after cleanup. Earlier polling termination remains in poll_stop_reason.

### poll_stop_reason {poll_stop_reason: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["done", "child_reaped", "sentinel_deadline", "wait_error", "policy_write_error", "policy_transfer_deadline"]
unknown: "The host string is retained; an unfamiliar reason establishes only that recorded reason, and gains no known timeout or cause meaning."
```

Why host publication polling ended. Only sentinel_deadline names exhaustion of that polling allowance; later cleanup preserves this recorded reason.

### exit_requested {exit_requested: field}

Whether the host performed the release store asking the worker to exit. Worker receipt is a separate observation.

### termination_request {termination_request: field}

Host kill call, its requested signal and native return. Absence means no retained request.

### reaped {reaped: field}

True when waitpid returned this child PID; false explicitly records unconfirmed disposition. Absence means the observation is unavailable.

### wait_errors {wait_errors: field}

Failed host waitpid calls, including recovered EINTR. Empty means none observed; absence means unavailable.

### cleanup_trigger {cleanup_trigger: field}

Host fact recorded when it requests exit: deadline_expiry, completion, child_reaped, poll_wait_error, policy_transfer_error or policy_transfer_timeout.

### grace_end {grace_end: field}

How the post-request grace stage ended: not_entered, reaped_during_grace, exhausted or wait_error.

### collection_basis {collection_basis: field}

Whether final reads followed a confirmed reap: after_confirmed_reap, execution_may_continue or unavailable. This controls terminal absence claims.

### ready_wait {ready_wait: field}

Measured monotonic wait for the readiness hint, present when that stage ran. The production allowance is <!-- span limits.worker_ready_wait.value_unit -->1,000 milliseconds<!-- /span --> after successful policy delivery and readiness-pipe setup; actor setup can reduce it to the remaining shared setup allowance. The record carries the allowance actually assigned. Expiry leaves the readiness hint absent and execution continues.

### sentinel_wait {sentinel_wait: field}

Measured publication wait, with synchronous validator collection charged separately through excluded_ms.

### exit_grace_wait {exit_grace_wait: field}

Measured monotonic wait for departure after the host exit request, present when that stage ran. Its production allowance is <!-- span limits.worker_exit_grace.value_unit -->1,000 milliseconds<!-- /span -->; subsequent termination and final reap retain their own observations.

### disposition {disposition: field}

Host-resolved lifecycle questions, step claims and conflicts. Ordinary subprocess reporting supplies this account and derives compatibility fields from it.

## Measured host wait {host_wait: subject}

```contract
record: "PWHostWait"
as: "lc_host_wait"
```

A wait records the host boundary at which it moved on. Budgets and elapsed values use milliseconds on CLOCK_MONOTONIC.

### budget_ms {budget_ms: field}

Allowance assigned to this wait; its owning operation defines the cap and whether other work is excluded.

### elapsed_ms {elapsed_ms: field}

Measured interval at stop. Absence records that the clock could not supply a valid nondecreasing interval.

### stop {stop: field}

Owning operation's reason for ending this wait. clock_unavailable denotes failed or backward time with bounded sleep fallback; setup_failed denotes an unavailable nonblocking prerequisite.

### excluded_ms {excluded_ms: field}

Measured synchronous work excluded from this wait's allowance. For sentinel waiting, consumed allowance is elapsed_ms minus excluded_ms; absence means this exclusion is unreported or inapplicable.

### native_errno {native_errno: field}

Native error captured by the wait's failing prerequisite or observation, when that branch supplies one.

### clock_fault {clock_fault: field}

Whether the monotonic clock failed or moved backward during this wait.

## Host termination request {termination: subject}

```contract
record: "PWRunnerTerminationRequest"
as: "lc_termination"
```

Each record preserves one host kill call. The return establishes whether the request was accepted by that call; the child's ending is reported by reaping.

### signal {signal: field}

Signed 32-bit signal argument passed to kill.

### rc {rc: field}

Signed 32-bit native kill return, retained without a signal-result allowlist.

### errno {errno: field}

Immediately captured errno when rc is -1; absent after another return.

## Failed host wait {wait_error: subject}

```contract
record: "PWRunnerWaitError"
as: "lc_wait_error"
```

The host records each failed waitpid call even if a later retry reaps the child.

### stage {stage: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["poll", "exit_grace", "after_termination"]
unknown: "The recorded stage and native error remain available without an invented known-stage interpretation."
```

Host stage of the call, including poll, exit_grace and after_termination. Unfamiliar stages remain transportable as recorded strings.

### rc {rc: field}

Native waitpid return; producer records this object for -1.

### errno {errno: field}

Error captured before another native call; EINTR may be followed by a recovered wait.

## Policy-pipe timeout {transfer_timeout: subject}

```contract
record: "PWWorkerPolicyTransferTimeout"
as: "lc_transfer_timeout"
```

Host write counts and worker read receipts describe separate ends of the policy pipe.

### budget_ms {budget_ms: field}

Host policy-transfer allowance in milliseconds. Production assigns <!-- span limits.worker_policy_transfer.value_unit -->5,000 milliseconds<!-- /span --> from an absolute monotonic deadline established immediately after spawn; partial writes and interrupted calls keep that deadline. Actor delivery is additionally capped by the remaining shared setup allowance. This field reports the assigned allowance.

### elapsed_ms {elapsed_ms: field}

Measured transfer interval when its deadline expired.

### bytes_written {bytes_written: field}

UTF-8 policy bytes accepted by host write calls before timeout.

### bytes_expected {bytes_expected: field}

Total UTF-8 policy bytes the host attempted to send.

## Policy-pipe write error {transfer_error: subject}

```contract
record: "PWWorkerPolicyTransferError"
as: "lc_transfer_error"
```

This record belongs to the host's transport of the selected source bytes.

### errno {errno: field}

Native errno captured from the failed policy-pipe write.

### bytes_written {bytes_written: field}

Policy bytes accepted by preceding writes before this failure.

### bytes_expected {bytes_expected: field}

Total selected policy bytes the host attempted to send.

## Worker publication snapshot {worker_evidence: subject}

```contract
record: "PWWorkerEvidence"
as: "lc_worker_evidence"
```

The host first checks the shared region's worker identity, then acquire-reads each publication independently. Available publications retain their own scopes.

### abi_identity {abi_identity: field}

Host-selected worker protocol identity copied into the report after the region identity check.

### progress {progress: field}

Last acquired nonzero packed worker progress word, decoded into operation, stage and optional index.

### failure_publication {failure_publication: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: [0, 1, 2]
unknown: "The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions."
```

Raw terminal-failure publication word, including unfamiliar numeric values.

### failure_state {failure_state: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["absent", "incomplete", "published", "invalid"]
```

Host interpretation of the publication and eligible failure payload: absent, incomplete, published or invalid.

### failure {failure: field}

Terminal worker failure payload when its publication and layout guards allow decoding.

### readiness {readiness: field}

Worker publication of the readiness-write native result, independent of the host's receipt of the byte.

### diagnostic {diagnostic: field}

Diagnostic publication state and eligible bounded diagnostic text.

### policy_read {policy_read: field}

Worker EOF receipt, published before comparing received and expected lengths; missing receipt leaves delivery unknown.

## Worker progress {progress: subject}

```contract
record: "PWWorkerProgress"
as: "lc_progress"
```

Progress is an acquired protocol position. Numeric operation and stage codes are open; the lifecycle resolver names an unfamiliar position progress_unrecognized.

### raw {raw: field}

Packed UInt32 progress value: operation in the high byte, stage in the next four bits, and one-based optional item in the low twenty bits.

### operation {operation: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
unknown: "The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions."
```

Numeric worker operation decoded from raw; known protocol order runs header validation, clock setup, policy read, parameter/compile/apply work, activation/release waits, attempts and completion.

### stage {stage: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: [1, 2]
unknown: "The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions."
```

Numeric boundary stage decoded from raw; 1 is entry and 2 is return for recognized lifecycle positions.

### index {index: field}

Zero-based item decoded from the low bits; attempts use the plan slot, parameter setup uses its parameter, and actor waits identify the next visit's first slot.

## Terminal worker failure {failure: subject}

```contract
record: "PWWorkerFailure"
as: "lc_failure"
```

The worker publishes the operation's native observation and a PW failure classification. Numeric codes retain unfamiliar values.

### operation {operation: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: [1, 2, 3, 4, 5, 8, 12]
unknown: "The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions."
```

Worker operation at which the terminal failure was published.

### code {code: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: [1]
unknown: "The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions."
```

PW failure classification within that operation.

### native_kind {native_kind: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: [0, 1, 2]
unknown: "The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions."
```

Discriminator for the retained native observation: 0 has no native result, 1 is an integer return, 2 is a null-pointer result represented by zero; unfamiliar codes retain their number.

### native_result {native_result: field}

Signed native return when native_kind supplies one; a null-pointer result is zero.

### errno {errno: field}

Native errno when the publication marks it present.

### index {index: field}

Operation-specific zero-based item, such as a parameter or attempt; absence represents the worker's no-index sentinel.

### detail {detail: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: [0]
unknown: "The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions."
```

Additional operation-specific numeric classification retained alongside the primary failure code.

## Readiness-write result {readiness: subject}

```contract
record: "PWWorkerReadiness"
as: "lc_readiness"
```

This is the worker's own publication of the readiness helper result. The helper retries EINTR and converts a one-byte write to success.

### rc {rc: field}

Readiness-helper result: zero after one byte was written; -1 after a persistent failure.

### errno {errno: field}

Worker-captured errno accompanying a nonzero helper result; absent for rc zero.

## Worker diagnostic {diagnostic: subject}

```contract
record: "PWWorkerDiagnostic"
as: "lc_diagnostic"
```

The host exposes text only after acquiring a complete or truncated publication with a bounded length and terminating NUL.

### state {state: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: [0, 1, 2, 3]
unknown: "The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions."
```

Raw diagnostic publication word: 0 absent, 1 complete, 2 truncated, 3 incomplete; other values remain numeric.

### status {status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["absent", "incomplete", "unknown", "complete", "truncated", "invalid"]
```

Host interpretation: absent, incomplete, unknown, complete, truncated or invalid. Invalid identifies an eligible publication whose length or terminator failed validation.

### length {length: field}

Retained diagnostic-byte length excluding its terminating NUL, at most <!-- span limits.worker_diagnostic.value_unit -->4,095 bytes<!-- /span --> when validation permits text extraction.

### text {text: field}

Diagnostic bytes decoded as UTF-8 with replacement for invalid sequences. The <!-- span limits.worker_diagnostic.value_unit -->4,095 bytes<!-- /span --> bound applies before replacement decoding. The diagnostic status carries whether the worker truncated its buffer.

## Worker policy receipt {policy_read: subject}

```contract
record: "PWWorkerPolicyRead"
as: "lc_policy_read"
```

At EOF the worker publishes both counts before comparing them. A header refusal, read failure or overflow leaves this receipt unavailable; both counts must fit the <!-- span limits.policy_source.value -->262,143<!-- /span -->-byte source capacity.

### bytes_expected {bytes_expected: field}

Host-selected UTF-8 byte count from the worker's immutable header input.

### bytes_received {bytes_received: field}

Bytes the worker read from the policy pipe when it observed EOF. Equality with bytes_expected establishes length agreement with the submitted bytes.

## Canonical worker disposition {disposition: subject}

```contract
record: "PWDispositionRecord"
as: "lc_disposition"
```

The host resolves this account once from the worker's acquired output and submitted plan. Run questions and per-step questions keep their individual support and conflicts.

### questions {questions: field}

Fixed set of run-level lifecycle claims.

### steps {steps: field}

Plan-ordered lifecycle claims for each requested step, joined only to uniquely identified worker slots.

### issues {issues: field}

Conflicting observations referenced by conflicting claims; indices are zero-based within this array.

### Resolving lifecycle claims {resolve: reports}

```contract
who: "runner host"
where: "final worker output and plan join"
entry: ["single_worker", "actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["ordinary_reply"]
free.condition: Resolve each question from the owning worker's acquired output, unique slot identities and submitted plan. A not_reached or unpublished conclusion requires terminal collection where specified below.
free.effect: Publish the canonical account once and copy its boundary/result claims into per-attempt lifecycle projections. Retain conflicts as issues rather than selecting one conflicting observation.
```

An exit code or signal is supported after a successful reap. Both representations
produce a D1 conflict. A completed supported slot establishes publication and
can establish entry. Recognized progress at or after an attempt's entry also
establishes entry. A final earlier progress position establishes `not_reached`
only after confirmed reaping and with an incomplete slot; beside a completed
slot it produces D5. Returned-or-later terminal progress beside an incomplete
supported slot produces D5 for result publication. Live collection leaves
missing results unresolved. An unsupported attempt has inapplicable result
publication and an `unsupported` lifecycle summary.

## Lifecycle claim {claim: subject}

```contract
record: "PWDispositionClaim"
as: "lc_claim"
```

A supported claim names its answer and observation references. An unresolved or inapplicable claim names its reason; a conflicting claim points to its issue.

### state {state: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["supported", "unresolved", "conflicting", "inapplicable"]
```

supported, unresolved, conflicting or inapplicable, determining which accompanying fields carry the claim.

### answer {answer: field}

Question-specific supported answer, such as signal, exit_code, reached, published or an observed host stop reason.

### value {value: field}

Answer payload: an exit code, signal or item index as an integer, or the observed termination-request object.

### reason {reason: field}

Reason the question is unresolved or inapplicable, preserving missing, unusable, nonterminal and unsupported evidence distinctions.

### issue {issue: field}

Zero-based pointer to the matching conflict in disposition.issues.

### basis {basis: field}

Observation references supporting the answer or explaining uncertainty: raw run fields, progress, worker_failure, plan, slot and attempt_support in their question's scope.

## Lifecycle answer value {claim_value: subject}

```contract
record: "PWDispositionValue"
as: "lc_claim_value"
```

The integer alternative carries a signal, exit code or index according to the question. The request alternative carries the complete host termination request.

## Lifecycle conflict {issue: subject}

```contract
record: "PWDispositionIssue"
as: "lc_issue"
```

The resolver retains both incompatible observations and identifies the claim whose support they conflict over.

### kind {kind: field}

conflict for a resolver-created disagreement among observations.

### rule {rule: field}

D1 for competing terminal status representations; D5 for incompatible terminal progress and slot publication.

### question {question: field}

Lifecycle question affected by this issue.

### step_index {step_index: field}

Zero-based plan step for a step issue; absent for a run-level issue.

### observations {observations: field}

Named observations involved in the conflict, resolved in the same run or step scope.

### detail {detail: field}

Human-readable description of the incompatible observations.

## Run lifecycle questions {run_questions: subject}

```contract
record: "PWDispositionRunQuestions"
as: "lc_run_questions"
```

Ordinary resolution supplies every question; absent slots preserve partial or rejected evidence for readers.

### final_status {final_status: field}

Whether a successful owned reap supplies an exit code or terminating signal; competing representations produce a D1 conflict.

### stop_reason {stop_reason: field}

Host polling-stop observation, or unresolved when it was not recorded.

### cleanup_trigger {cleanup_trigger: field}

Recorded reason for requesting exit; inapplicable when exit_requested is false.

### grace_end {grace_end: field}

Recorded end of the exit-grace stage; inapplicable when exit_requested is false.

### kill_request_and_result {kill_request_and_result: field}

The observed termination request, a supported none after a recorded exit request, or the corresponding unresolved/inapplicable state.

### collection_basis {collection_basis: field}

Host fact stating whether final reads followed confirmed reaping or execution might continue.

### progress_association {progress_association: field}

Association of the packed progress word with no item, a step index or a parameter index; invalid packing is distinguished from an unfamiliar operation/stage.

## Step lifecycle account {step: subject}

```contract
record: "PWDispositionStep"
as: "lc_step"
```

Step positions come from the submitted plan. Duplicate slot identifiers supply no unique slot to the join.

### index {index: field}

Zero-based position of this step in the owning worker's plan.

### step_id {step_id: field}

Submitted step identifier used to join its worker slot and public step.

### slot {slot: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["completed", "incomplete", "absent"]
```

completed, incomplete or absent according to the uniquely associated worker slot and its completion publication.

### attempt_support {attempt_support: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["supported", "unsupported"]
```

supported or unsupported according to whether the requested attempt has an implemented worker mapping.

### questions {questions: field}

Boundary, result-publication and requested-operation applicability claims for this step.

## Step lifecycle questions {step_questions: subject}

```contract
record: "PWDispositionStepQuestions"
as: "lc_step_questions"
```

The result and boundary questions preserve distinct observations: a call can start without publishing a completed result.

### step_boundary_reached {step_boundary_reached: field}

Whether recognized progress or a supported completed slot establishes entry; terminal earlier progress can establish not_reached or conflict with a completed slot.

### step_result_published {step_result_published: field}

Whether a supported completed slot is published; incomplete terminal collection can establish unpublished, while live collection remains unresolved.

### step_requested_operation_applicability {step_requested_operation_applicability: field}

Whether this requested attempt maps to an implemented worker operation, as stated by attempt_support.

## Per-attempt lifecycle projection {attempt: subject}

```contract
record: "PWAttemptLifecycle"
as: "lc_attempt"
```

A step or extension event carries this compact projection of its canonical disposition claims.

### summary {summary: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["completed", "started_without_result", "not_reached", "unsupported", "unresolved", "conflicting"]
unknown: "The controller retains an unfamiliar summary and checks the independently carried boundary and result claims."
```

The current producer derives completed, started_without_result, not_reached, unsupported, unresolved or conflicting from the boundary/result claims and attempt support. The controller retains unfamiliar summary strings; it checks the recognized summaries against their corresponding claims.

### boundary {boundary: field}

Copy of the owning disposition step's step_boundary_reached claim.

### result {result: field}

Copy of the owning disposition step's step_result_published claim.

## Owned child ending {owned_reap: subject}

```contract
record: "PWOwnedReapObservation"
as: "lc_owned_reap"
```

A successful waitpid observation retains the host's ownership and departure-request state at capture. Actor gates refer to this observation by ordinal.

### pid {pid: field}

Owned child PID for which the host obtained terminal wait status.

### native_rc {native_rc: field}

Native waitpid return equal to pid for this captured ending.

### raw_status {raw_status: field}

Raw terminal wait status, from which the corresponding exit code or signal is decoded.

### stage {stage: field}

Host capture stage, including schedule, termination_gate and cleanup stages; the gate admits schedule or termination_gate for natural-departure support.

### observed_ns {observed_ns: field}

Host monotonic capture time in nanoseconds, when available.

### ownership_unbroken {ownership_unbroken: field}

Whether the host retained uninterrupted ownership through this wait observation.

### departure_requested {departure_requested: field}

Whether the host had already requested this child's departure when it captured the ending.

### capture_ordinal {capture_ordinal: field}

Positive ordinal in this child's host-observation sequence, shared with its activations and gate captures.

## Owned-ending reference {reap_reference: subject}

```contract
record: "PWOwnedReapReference"
as: "lc_reap_reference"
```

A gate references the source actor's retained owned_reap instead of copying a second ending.

### capture_ordinal {capture_ordinal: field}

Ordinal of the source actor's owned ending; its association must match that source's owned_reap record.

## Native spawn failure {spawn_failure: subject}

```contract
record: "PWRunnerSpawnFailure"
as: "lc_spawn_failure"
```

The host retains the failed spawn operation as a separate record before a child process exists.

### origin {origin: field}

Component reporting the failure, supplied by the runner host.

### operation {operation: field}

Failed native spawn operation, such as posix_spawn.

### executable_path {executable_path: field}

Executable path passed to the attempted spawn.

### return_code {return_code: field}

Native spawn return code, whose error-code convention is distinct from a child exit status.

### diagnostic {diagnostic: field}

Human-readable native error explanation of the spawn failure.

## Validator subprocess {validator: subject}

```contract
record: "PWRunnerValidatorSubprocess"
as: "lc_validator"
```

The host binds each validator collection to its phase and retains accepted records through later I/O, association or cleanup failure.

For N submitted queries, the collector assigns a record allowance of max(1, N) multiplied by <!-- span limits.validator_records_per_query.value -->2<!-- /span --> and a stdout retention allowance of max(1, N) multiplied by <!-- span limits.validator_reply_bytes_per_query.value_unit -->16,384 bytes<!-- /span -->. The allowances are sized before writing the query batch. On byte overflow the host counts all bytes received, keeps the bounded prefix through its last complete LF frame, closes collection and reports byte_limit. Decoding retains complete accepted records before the first refused frame or record-count excess.

### phase_id {phase_id: field}

Host-stamped phase identifier served by this collection; agrees with the containing phase.

### ordinal {ordinal: field}

Host-stamped one-based phase ordinal for this collection.

### pid {pid: field}

Spawned validator PID used for collection and owned cleanup.

### term_signal {term_signal: field}

Signal decoded only from a successful waitpid result for this validator.

### exit_code {exit_code: field}

Exit status decoded only from a successful waitpid result for this validator.

### reaped {reaped: field}

True for a confirmed owned reap, false for an unconfirmed ending, absent when unreported.

### termination_request {termination_request: field}

Host kill request and native return, if requested during validator cleanup.

### wait_errors {wait_errors: field}

Failed waitpid observations from validator cleanup, including recovered interruptions.

### read_error {read_error: field}

Host diagnostic for stdout-read failure, separate from accepted record contents.

### stdout_collection_stop {stdout_collection_stop: field}

Host reason for stopping stdout collection: eof, clock_error, deadline, poll_error, byte_limit or read_error. This is fixed before the exit-grace stage.

### stdout_bytes_received {stdout_bytes_received: field}

Total stdout bytes received by the host, including bytes later rejected by frame decoding.

### probe_bytes_written {probe_bytes_written: field}

Request bytes accepted by host writes to the validator input pipe.

### probe_bytes_expected {probe_bytes_expected: field}

Serialized request-batch byte count the host intended to write.

### io_error {io_error: field}

Host transport diagnostic for the first request-write or stdout-read failure selected for this collection.

### decode_fault {decode_fault: field}

First rejected stdout frame's receiver-owned diagnostic and bounded byte prefix.

### records {records: field}

Accepted verdict records in received order, including diagnostic, unexpected-ID and null-ID records, within this phase collector's record allowance.

### expected_step_ids {expected_step_ids: field}

Submitted query IDs in the planned collection; used to check missing, duplicate and unexpected associations.

### association_issues {association_issues: field}

Host-computed join problems; an empty array records a complete unambiguous join for the expected queries.

### exit_grace_wait {exit_grace_wait: field}

Measured monotonic host wait after collection closed, with production allowance <!-- span limits.validator_exit_grace.value_unit -->1,000 milliseconds<!-- /span -->, before any further termination/reap work. Those later operations can continue beyond this allowance.

### Joining accepted validator records {associate: reports}

```contract
who: "runner host"
where: "closed phase query collection"
entry: ["single_worker", "actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["ordinary_reply", "retained_reporting_failure"]
effects: retain_records(lc_validator.records)
free.condition: Join each expected ID to exactly one accepted record whose supplied query metadata agrees; allow/deny additionally require the complete submitted query identity.
free.effect: Exclude ambiguous, missing or mismatched records from the per-step join, retain every accepted record in the collection and publish association_issues.
```

Duplicate IDs leave every record of that group at collection scope. Null IDs
remain unassociated. Diagnostic outcomes may omit query metadata; any supplied
metadata must agree. A decoding fault retains the accepted prefix and the
rejected frame's bounded byte context. Transport or later cleanup failure
preserves the already accepted observations.

## Rejected validator frame {decode_fault: subject}

```contract
record: "PWValidatorDecodeFault"
as: "lc_decode_fault"
```

The host retains the first fault and its exact received byte context. Earlier accepted verdicts remain available.

### origin {origin: field}

runner_host, identifying the rejecting receiver.

### kind {kind: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["utf8", "json", "structure"]
```

Receiver category utf8, json or structure for the first rejected frame.

### message {message: field}

Human-readable reason the frame failed structural admission.

### byte_offset {byte_offset: field}

Zero-based offset of the rejected frame's first byte in received stdout.

### frame_bytes {frame_bytes: field}

Length of that frame in bytes, excluding its LF separator.

### retained_bytes {retained_bytes: field}

Number of prefix bytes retained, capped at 256.

### context_b64 {context_b64: field}

Base64 encoding of the retained received-byte prefix. Decoding yields those exact bytes.

### context_truncated {context_truncated: field}

True when frame_bytes exceeds retained_bytes.

## Validator query association {association_issue: subject}

```contract
record: "PWValidatorAssociationIssue"
as: "lc_association_issue"
```

Expected IDs are joined only to one accepted record describing the submitted query. Accepted records remain at collection scope when the join cannot select them.

### origin {origin: field}

runner_host, identifying the component computing the association issue.

### kind {kind: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["missing_id", "duplicate_id", "query_mismatch", "unexpected_id", "unassociated"]
```

missing_id, duplicate_id, query_mismatch, unexpected_id or unassociated.

### step_id {step_id: field}

Expected or unexpected ID concerned by the issue; absent for records whose verdict ID is null.

### count {count: field}

Number of accepted records involved: zero for missing_id, one for query_mismatch, the group size for duplicate/unexpected IDs, or total null-ID records for unassociated.

## Spawned-command observation {exec: subject}

```contract
record: "PWExecObservation"
as: "lc_exec"
```

A completed worker exec slot separates collection, cleanup requests and the owned leader reap. Collection facts are frozen before termination requests.

### collection {collection: field}

Leader-exit and pipe observations up to the collection stop.

### cleanup {cleanup: field}

Requests to terminate the spawned process group and any leader fallback.

### reap {reap: field}

Final bounded wait account for the owned leader after collection and cleanup.

## Exec collection {exec_collection: subject}

```contract
record: "PWExecCollectionObservation"
as: "lc_exec_collection"
```

The collector can observe leader exit and pipe EOF independently; descendants may keep a stream open after the leader exits.

### stop_reason {stop_reason: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["leader_exit_and_eof", "deadline", "observation_error", "clock_fault"]
```

leader_exit_and_eof, deadline, observation_error or clock_fault, recording the branch that stopped collection.

### leader_exit_observed {leader_exit_observed: field}

Whether waitid observed the owned leader's exit during collection.

### stdout {stdout: field}

EOF or native read/poll failure retained for stdout.

### stderr {stderr: field}

EOF or native read/poll failure retained for stderr.

### deadline_kind {deadline_kind: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["child", "plan"]
uses: ["probes.attempt.exec"]
```

child or plan when the selected collection deadline expires; absent on other stop branches. The child allowance and remaining per-worker active-plan allowance are defined by the exec operation.

### waitid_errno {waitid_errno: field}

Native waitid failure which stopped leader observation; recovered EINTR is excluded.

### poll_errno {poll_errno: field}

Native poll failure which stopped stream observation; recovered EINTR is excluded.

### clock_fault {clock_fault: field}

Local numeric clock-fault observation when collection stopped for failed/backward time.

## Exec stream observation {exec_stream: subject}

```contract
record: "PWExecStreamObservation"
as: "lc_exec_stream"
```

A stream carries EOF or a terminal read/poll observation from collection.

### eof {eof: field}

Whether the worker read EOF on this stream before collection stopped.

### read_errno {read_errno: field}

Terminal read errno, excluding recovered EINTR and EAGAIN.

### poll_revents {poll_revents: field}

Terminal error/invalid descriptor poll bits retained when they ended observation; ordinary readable/EOF handling uses its own read observation.

## Exec cleanup {exec_cleanup: subject}

```contract
record: "PWExecCleanupObservation"
as: "lc_exec_cleanup"
```

Cleanup requests follow the frozen collection observation and preserve their native returns.

### state {state: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["not_requested", "ownership_unconfirmed", "requested"]
```

not_requested after leader_exit_and_eof; ownership_unconfirmed when waitid failed; requested when an eligible process-group cleanup was attempted.

### group_request {group_request: field}

SIGKILL request to negative leader PID for the owned process group, when cleanup is requested.

### leader_fallback {leader_fallback: field}

SIGKILL request to the positive leader PID after a failed group request with errno other than ESRCH.

## Exec signal request {exec_signal: subject}

```contract
record: "PWExecSignalRequest"
as: "lc_exec_signal"
```

This is the worker's native kill call for a spawned command, scoped to the target named here.

### target {target: field}

Negative leader PID for a process-group request, or positive leader PID for the fallback request.

### signal {signal: field}

Signal passed to kill; the exec cleanup path uses SIGKILL.

### rc {rc: field}

Native kill return, zero or -1.

### errno {errno: field}

Positive native errno captured for rc -1; absent after success.

## Exec leader reap {exec_reap: subject}

```contract
record: "PWExecReapObservation"
as: "lc_exec_reap"
```

Final wait facts concern the spawned leader owned by the worker. After collection ends, the production reap allowance is <!-- span limits.exec_reap_grace.value_unit -->1,000 milliseconds<!-- /span --> of continuous time. Earlier ownership or group-request failures retain their branch priority; a recorded request and an observed reap remain separate.

### stop_reason {stop_reason: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["reaped", "wait_error", "ownership_unconfirmed", "group_request_failed", "clock_fault", "deadline"]
```

reaped, wait_error, ownership_unconfirmed, group_request_failed, clock_fault or deadline; branch priority preserves earlier ownership/group-request failures.

### last_wait {last_wait: field}

Last native waitpid result, with status only when the owned leader PID returned.

### clock_fault {clock_fault: field}

Local numeric clock fault encountered by the reap wait, when observed.

## Exec leader wait result {exec_wait: subject}

```contract
record: "PWExecWaitObservation"
as: "lc_exec_wait"
```

Pending, failed and reaped waits retain their different native return values.

### rc {rc: field}

Native waitpid return: zero pending, -1 failure, or owned leader PID when reaped.

### errno {errno: field}

Positive captured errno for rc -1, including EINTR; absent otherwise.

### status {status: field}

Raw terminal wait status present exactly when rc is the owned leader PID, agreeing with the attempt's leader exit/signal fields.

## Support for record meanings {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerLifecycleEvidence.swift", "symbol": "PWRunnerSubprocess"}, {"path": "runner/Sources/PWRunnerCore/CWorker.swift", "symbol": "decodeWorkerEvidence"}, {"path": "runner/Sources/PWRunnerCore/CWorkerDisposition.swift", "symbol": "resolveDisposition"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerDisposition.swift", "symbol": "lifecycleSummary"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift", "symbol": "validatorAssociationIssues"}, {"path": "runner/Sources/PWRunnerCore/ValidatorClient.swift", "symbol": "decodeValidatorFrames"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift", "symbol": "execObservationEvidenceProblem"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift", "symbol": "PWOwnedReapObservation"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "write_ready_byte"}, {"path": "runner/Sources/PWRunnerCore/CWorker.swift", "symbol": "CWorkerInput"}, {"path": "runner/Sources/PWRunnerCore/ActorSession.swift", "symbol": "readyBudgetMs"}, {"path": "runner/Sources/PWRunnerCore/ValidatorClient.swift", "symbol": "runValidator"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner_abi.h", "symbol": "PW_SHM_DIAGNOSTIC_BYTES"}, {"path": "controller/tools/pw_probe_runner/pw_worker_timing.h", "symbol": "PW_EXEC_REAP_GRACE_MS"}]
pins: "Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope."
context: "Source and check inspection during contract drafting."
limits: "No execution credit is claimed by this owner."
```

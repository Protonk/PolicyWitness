# Predictions, attempts and comparison {steps: surface}

```contract
syntax: 1
artifact: "Predictions, attempts and comparison"
part: "report"
goldens: ["tests/fixtures/contract/surfaces/steps.json", "tests/fixtures/comparison/matrix.json"]
checks: ["runner_unit", "failure_boundaries", "witness_contract"]
who: ["identity.definitions.host"]
where: "step evidence assembly"
entry: ["xpc_execute"]
recipient: ["controller", "xpc_caller"]
report: ["runner_reply"]
```

## Probe result {step: subject}

```contract
record: "PWRunnerStepResult"
as: "step"
```

### phase_id {phase_id: field}

Identifier of the containing declared phase; normalized flat-step requests use `main`.

### step_id {step_id: field}

Identifier of the declared probe action, associated within its phase and actor.

### sandbox_check {sandbox_check: field}

Query-channel result from the associated validator record or a synthetic unavailable result.

### attempt {attempt: field}

Worker action result, including publication provenance and retained native observations.

### comparison {comparison: field}

Host assessment of observation, submitted scopes and reply.phases[p].ordering.

### actor_id {actor_id: field}

Actor whose process owns this probe in actor form; omitted in ordinary execution.

## Query-channel result {query: subject}

```contract
record: "PWRunnerSandboxCheckResult"
as: "query"
```

### result_source {result_source: field}

`validator` means a uniquely associated accepted record supplied the result; `synthetic` means the host constructed an unavailable result.

### native_rc {native_rc: field}

Native return carried by an associated allow, deny or error record. Synthetic results carry explicit null when result_source is present.

### missing_reason {missing_reason: field}

`query_not_requested` for a planner exclusion, `validator_not_invoked` when collection never ran, or `validator_no_verdict` when it produced no associated record.

### rc {rc: field}

An associated record supplies its carried return, or -1 if that record omits the return. A planner exclusion uses -1. With no associated verdict, the host supplies 0 and an error outcome. Provenance and outcome qualify this number.

### outcome {outcome: field}

`allow` or `deny` is the associated answer; `unsupported_operation` retains that diagnostic. Other accepted diagnostics project as `error`. Planner exclusion yields `prediction_unavailable`.

### pid {pid: field}

PID targeted by this phase's validator collection when worker output supplies it. The ordering assessment states whether the required live-worker interval was established.

### operation {operation: field}

The admitted query operation.

### filter_kind {filter_kind: field}

The normalized query filter name.

### filter_value {filter_value: field}

The supplied request value. A none-filter native query uses no value even when this echoed field is present.

### filter_type_id {filter_type_id: field}

Native filter identifier retained from the associated record when supplied.

### errno {errno: field}

Errno retained from the validator record, belonging to the query channel.

### error {error: field}

The validator diagnostic or host explanation of an unavailable result.

### path_diagnostics {path_diagnostics: field}

Host observations after orchestration for a nonempty path-filter value.

## Accepted validator record {verdict: subject}

```contract
record: "ValidatorVerdict"
as: "verdict"
```

### step_id {step_id: field}

Step identifier carried by the frame, or null when absent. Unknown, duplicate and unassigned records remain retained as received.

### operation {operation: field}

Operation carried by the frame, omitted when absent.

### filter_type {filter_type: field}

Filter spelling carried by the frame, omitted when absent.

### filter_type_id {filter_type_id: field}

Numeric native filter identifier carried by the frame, omitted when absent.

### filter_value {filter_value: field}

Value carried by the frame, omitted when absent; a NONE query has no native filter value.

### rc {rc: field}

Native or diagnostic return carried by the frame, omitted when absent.

### errno {errno: field}

Query errno carried by the frame, omitted when absent.

### outcome {outcome: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["allow", "deny", "error", "unsupported_operation"]
unknown: "Retain an unfamiliar diagnostic outcome with its error string; assign only its recorded diagnostic meaning."
```

The accepted frame's outcome string.

### error {error: field}

The frame diagnostic, omitted when absent.

### raw_line {raw_line: field}

Accepted UTF-8 frame text. A receiver-owned decode-fault record retains rejected frame bytes separately.

## Attempt-channel result {attempt: subject}

```contract
record: "PWRunnerAttemptResult"
as: "attempt"
```

### requested_kind {requested_kind: field}

Declared attempt kind, echoed independently of completion.

### requested_action {requested_action: field}

Declared action, echoed independently of completion.

### result_source {result_source: field}

`worker` means a supported action's slot published completion; `synthetic` means the host supplied an unavailable or unsupported result.

### missing_reason {missing_reason: field}

`attempt_not_supported`, `slot_absent` or `slot_incomplete` identifies the synthetic result's reason.

### lifecycle {lifecycle: field}

Resolved reach, entry, completion and interruption claims under the subprocess disposition's supporting observations.

### fresh_read {fresh_read: field}

Completed read_fresh action's open, descriptor-stat, bounded read and close observations.

### fresh_write {fresh_write: field}

Completed write_fresh or create_fresh action's native sequence and descriptor metadata.

### exec_observation {exec_observation: field}

Worker observations of spawn, child wait, output collection and cleanup.

### rc {rc: field}

Completed worker slot return; zero maps to ok. Synthetic unsupported or incomplete actions use -1. Exec can return nonzero after successful spawning because of the child's result.

### errno {errno: field}

Completed slot's nonzero errno, when retained. Fresh-operation details separately record their own failed calls.

### outcome {outcome: field}

A completed zero return yields `ok`. Nonzero returns map by action to `open_failed`, `read_failed`, `write_failed`, `unlink_failed`, `access_failed`, `lookup_failed`, `sysctl_failed` or `exec_failed`. Synthetic slots yield `no_completed_result` or `unsupported`.

### error {error: field}

Action diagnostic from the completed slot or explanation of a synthetic result.

### requested_path {requested_path: field}

Submitted target string, including service and sysctl names for those kinds.

### path_diagnostics {path_diagnostics: field}

Host observations after orchestration for a nonempty file or exec target.

### observed_path {observed_path: field}

Path observation supplied by the worker slot when available.

### child_pid {child_pid: field}

Completed exec slot's child PID: zero when no child was spawned. A positive value supports the comparison's spawned_child observation.

### child_exit_code {child_exit_code: field}

Completed exec slot's child exit code, using -1 until a normal child exit is observed.

### child_term_signal {child_term_signal: field}

Completed exec slot's terminating signal, using zero until a signaled child termination is observed.

### stdout {stdout: field}

Captured child stdout, omitted when empty. The worker retains at most <!-- span limits.exec_stream.value_unit -->1,023 bytes<!-- /span --> for this stream; an overflow marker occupies part of that allowance.

### stderr {stderr: field}

Captured child stderr, omitted when empty. The worker retains at most <!-- span limits.exec_stream.value_unit -->1,023 bytes<!-- /span --> for this stream; an overflow marker occupies part of that allowance.

## Comparison assessment {comparison: subject}

```contract
record: "PWRunnerComparison"
as: "comparison"
```

### observation {observation: field}

```contract
uses: ["steps.assessment.observe"]
```

`succeeded`, `permission_failure`, `other_failure` or `unavailable`, classified from the attempt channel by the rule below.

### observation_basis {observation_basis: field}

```contract
uses: ["steps.assessment.observe"]
```

Supporting observation: `spawned_child`, `completed_worker_status`, `permission_errno`, `bootstrap_permission_result` or `no_completed_worker_result`.

### operation_relation {operation_relation: field}

```contract
uses: ["steps.assessment.relations"]
```

`matched` means the query equals the action's mapped operation; `different` means those strings differ; `unresolved` means the mapping cannot assign a single operation.

### target_relation {target_relation: field}

```contract
uses: ["steps.assessment.relations"]
```

`same_submitted` or `different_submitted` compares submitted strings when the query filter matches the action's mapped filter and both strings exist; otherwise `unresolved`.

### order {order: field}

```contract
uses: ["steps.assessment.order"]
```

`query_first` places this eligible prediction before this phase's attempt batch with required worker lifetime and setup established. `unestablished` retains the channels without that temporal assessment.

### limitations {limitations: field}

Planner exclusions as `query_plan:path_unresolved_at_planning`, `query_plan:prediction_unavailable_pair` or `query_plan:unrecognized_filter_kind`. Lifecycle summaries add `attempt:started_without_result`, `attempt:not_reached`, `attempt:unsupported`, `attempt:lifecycle_unresolved` or `attempt:lifecycle_conflicting` for their corresponding noncompleted state; completed adds none. Ordinary reporting and controller checks require this closed vocabulary.

## Collection and release observations {ordering: subject}

```contract
record: "PWRunnerOrdering"
as: "ordering"
```

### collection_closed_before_proceed {collection_closed_before_proceed: field}

The host closed this phase's collection before performing its release store.

### proceed_set {proceed_set: field}

The host performed this phase's release store.

### proceed_observed {proceed_observed: field}

The worker published acknowledgement of this phase's release.

### validator_disposition {validator_disposition: field}

`not_invoked` when the hook never ran; `not_needed` when it ran without queries; `not_spawned` when queries existed without validator output; `reaped` for confirmed reap; otherwise `unconfirmed`.

### worker_lifetime_established {worker_lifetime_established: field}

Host-established worker ownership through release acknowledgement. Later cleanup has its own disposition.

### protocol_violations {protocol_violations: field}

Sorted unique driver and assembly findings about the collection/release/acknowledgement protocol.

## Query path observations {query_paths: subject}

```contract
record: "PWRunnerPathDiagnostics"
as: "query_paths"
```

### observer {observer: field}

`runner_host` identifies the observing component.

### stage {stage: field}

`after_orchestration` identifies the observation interval.

### input {input: field}

Nonempty submitted path-filter value.

### realpath_resolved {realpath_resolved: field}

Successful host realpath result, or null when resolution failed after orchestration.

### firmlink_resolved {firmlink_resolved: field}

Firmlink-mapped realpath result, or mapped input after standard /etc, /tmp and /var substitutions when realpath failed. Null means no mapping was available.

### same_as_input {same_as_input: field}

Names of available resolved fields whose UTF-8 bytes equal input; those equal-valued keys are omitted. A differing form is carried as a string; an unavailable form is explicit null.

## Attempt path observations {attempt_paths: subject}

```contract
record: "PWRunnerAttemptPathDiagnostics"
as: "attempt_paths"
```

### observer {observer: field}

`runner_host` identifies the observing component.

### stage {stage: field}

`after_orchestration` identifies the observation interval.

### input {input: field}

Nonempty submitted file or exec target.

### realpath_resolved {realpath_resolved: field}

Successful host realpath result after orchestration, following the leaf, or null when unavailable.

### parent_realpath_resolved {parent_realpath_resolved: field}

Realpath-resolved parent with the literal leaf appended for an eligible absolute path, or null when unavailable. A symlink leaf remains named by this form.

### same_as_input {same_as_input: field}

Names of available resolved fields whose UTF-8 bytes equal input; those equal-valued keys are omitted. A differing form is carried as a string; an unavailable form is explicit null.

## File identity observation {identity: subject}

```contract
record: "PWFileIdentity"
as: "identity"
```

### device {device: field}

The stat observation's device number.

### inode {inode: field}

The stat observation's inode number.

### mode {mode: field}

The stat observation's file type and mode bits.

### uid {uid: field}

The stat observation's owning user identifier.

### gid {gid: field}

The stat observation's owning group identifier.

## File metadata observation {stat: subject}

```contract
record: "PWRunnerFileStat"
as: "stat"
```

### rc {rc: field}

Native lstat or fstat return at this position in the operation sequence.

### errno {errno: field}

Errno from a failed metadata call.

### identity {identity: field}

Device, inode, mode, uid and gid from a successful metadata call.

### size {size: field}

Byte length from a successful metadata call.

## Fresh-descriptor read {fresh_read: subject}

```contract
record: "PWRunnerFreshRead"
as: "fresh_read"
```

### open_rc {open_rc: field}

Descriptor from open with O_RDONLY and O_CLOEXEC, or -1 on failure.

### open_errno {open_errno: field}

Errno from failed open.

### read_rc {read_rc: field}

Byte count from the bounded read, or -1 on failure; absent when open failed.

### read_errno {read_errno: field}

Errno from failed read.

### stat_rc {stat_rc: field}

Return from descriptor fstat, present after successful open.

### stat_errno {stat_errno: field}

Errno from failed descriptor stat.

### identity {identity: field}

Identity from successful descriptor stat.

### close_rc {close_rc: field}

Return from closing the descriptor, present after successful open.

### close_errno {close_errno: field}

Errno from failed close.

### content_hex {content_hex: field}

Bytes actually read as hexadecimal, including the empty string for a zero-byte read. Absent when no valid read result supplied bytes.

## Fresh-descriptor write or creation {fresh_write: subject}

```contract
record: "PWRunnerFreshWrite"
as: "fresh_write"
```

### open_rc {open_rc: field}

Descriptor from open with O_WRONLY and O_CLOEXEC, additionally O_CREAT and O_EXCL with mode 0600 for creation, or -1 on failure.

### open_errno {open_errno: field}

Errno from failed open.

### truncate_rc {truncate_rc: field}

Return from ftruncate(fd, 0) for write_fresh after successful open; absent for creation or failed open.

### truncate_errno {truncate_errno: field}

Errno from failed truncate.

### write_rc {write_rc: field}

Return from writing byte x after creation or successful truncation. One is complete, zero is a short write, -1 is failure; absent when writing was not reached.

### write_errno {write_errno: field}

Errno from a failed write. A short write retains its count without an invented errno.

### close_rc {close_rc: field}

Return from closing an opened descriptor.

### close_errno {close_errno: field}

Errno from failed close.

### preopen_stat {preopen_stat: field}

Creation's pre-open lstat diagnostic, including absence or existing-object metadata.

### opened_stat {opened_stat: field}

Descriptor metadata immediately after successful open.

### truncated_stat {truncated_stat: field}

Descriptor metadata after the write_fresh truncate call, including a failed truncate.

### written_stat {written_stat: field}

Descriptor metadata after the attempted write, including a failed or short write.

## Interpreting the observations {assessment: subject}

```contract
bind.p: reply.phases
bind.s: reply.steps
match.s: reply.steps[s].phase_id == reply.phases[p].phase_id
```

### Assemble the two channels {assembly: reports}

```contract
free.effect: Associate validator records and completed worker slots with the declared probe, retain their separate provenance and native observations, and synthesize an unavailable channel when its required observation is absent.
retained_free: {"effect":{"kind":"native_protocol","reason":"Association uses the planned query and completed native slot before producing the per-step channels; output fields cannot replace missing source observations."}}
```

An excluded query remains synthetic even when an unexpected validator frame
carries its step identifier. A completed slot is used only for a supported
attempt. The native answer is the validator-sourced allow or deny value;
the ordering assessment supplies its live-worker temporal meaning.

#### Assembly support {support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/CWorkerStepResults.swift","symbol":"buildStepResults"}
check: {"path":"runner/Tests/PWRunnerCoreTests/AttemptOutcomeMappingTests.swift","symbol":"runAttemptOutcomeMappingTests","form":"test"}
pins: "Completed, incomplete, absent and unsupported slots map to distinct provenance and outcomes; action mapping preserves exec child observations."
context: "Read complete step assembly and constructed attempt-mapping controls."
limits: "Check reading. Integrated query association has the validator collection's own support."
```

### Establish query order {order: checks}

```contract
each: ["p", "s"]
when: absent(reply.reporting_failure) and present(reply.steps[s].comparison)
who: ["identity.definitions.host"]
where: "per-step ordering assessment"
report: ["runner_reply"]
failure: "first"
```

#### Established order {success: effect}

```contract
on: "success"
effects: set_value(reply.steps[s].comparison.order, "query_first")
```

#### Unestablished order {failure: effect}

```contract
on: "failure"
effects: set_value(reply.steps[s].comparison.order, "unestablished")
```

#### Collection chain {chain: condition}

```contract
test: present(reply.phases[p].ordering) and reply.phases[p].ordering.collection_closed_before_proceed and reply.phases[p].ordering.proceed_set and reply.phases[p].ordering.proceed_observed and reply.phases[p].ordering.worker_lifetime_established and count(reply.phases[p].ordering.protocol_violations) == 0
```



#### Setup {setup: condition}

```contract
free.condition: Ordinary execution has observed successful application; actor execution has established the actor's declared applied or unapplied setup.
retained_free: {"condition":{"kind":"native_protocol","reason":"Ordinary apply observation and actor declared setup are producer inputs; their final summary labels alone do not establish the eligibility observation."}}
```

#### Native answer {native: condition}

```contract
test: reply.steps[s].sandbox_check.result_source == "validator" and present(reply.steps[s].sandbox_check.native_rc) and present(reply.steps[s].sandbox_check.errno) and reply.steps[s].sandbox_check.rc == reply.steps[s].sandbox_check.native_rc and ((reply.steps[s].sandbox_check.outcome == "allow" and reply.steps[s].sandbox_check.native_rc == 0) or (reply.steps[s].sandbox_check.outcome == "deny" and reply.steps[s].sandbox_check.native_rc == 1 and reply.steps[s].sandbox_check.errno == 0))
```

#### Unique association {association: condition}

```contract
test: present(reply.phases[p].validator_subprocess) and present(reply.phases[p].validator_subprocess.records) and matches(v) == 1
match.v: reply.phases[p].validator_subprocess.records[v].step_id == reply.steps[s].step_id
bind.v: reply.phases[p].validator_subprocess.records
free.condition: The query targets the associated live worker PID. For a filter kind outside the known request vocabulary, the native filter type is the uppercase spelling of that kind.
retained_free: {"condition": {"kind": "native_protocol", "reason": "The constructor receives the owned worker PID from live CWorkerOutput; the general reader supplies its associated reported process PID. Future filter names use the source string uppercasing operation."}}
```



##### Exact retained query identity {identity: condition}

```contract
each: ["v"]
test: reply.phases[p].validator_subprocess.records[v].operation == reply.steps[s].sandbox_check.operation and reply.phases[p].validator_subprocess.records[v].outcome == reply.steps[s].sandbox_check.outcome and reply.phases[p].validator_subprocess.records[v].rc == reply.steps[s].sandbox_check.native_rc and reply.phases[p].validator_subprocess.records[v].errno == reply.steps[s].sandbox_check.errno and implies(reply.steps[s].sandbox_check.filter_kind in ['none', 'path', 'global_name', 'local_name', 'iokit_registry_entry_class', 'iokit_user_client_class', 'sysctl_name'], (reply.steps[s].sandbox_check.filter_kind == "none" and reply.phases[p].validator_subprocess.records[v].filter_type == "NONE") or (reply.steps[s].sandbox_check.filter_kind == "path" and reply.phases[p].validator_subprocess.records[v].filter_type == "PATH") or (reply.steps[s].sandbox_check.filter_kind == "global_name" and reply.phases[p].validator_subprocess.records[v].filter_type == "GLOBAL_NAME") or (reply.steps[s].sandbox_check.filter_kind == "local_name" and reply.phases[p].validator_subprocess.records[v].filter_type == "LOCAL_NAME") or (reply.steps[s].sandbox_check.filter_kind == "iokit_registry_entry_class" and reply.phases[p].validator_subprocess.records[v].filter_type == "IOKIT_REGISTRY_ENTRY_CLASS") or (reply.steps[s].sandbox_check.filter_kind == "iokit_user_client_class" and reply.phases[p].validator_subprocess.records[v].filter_type == "IOKIT_USER_CLIENT_CLASS") or (reply.steps[s].sandbox_check.filter_kind == "sysctl_name" and reply.phases[p].validator_subprocess.records[v].filter_type == "SYSCTL_NAME")) and ((reply.steps[s].sandbox_check.filter_kind == "none" and absent(reply.phases[p].validator_subprocess.records[v].filter_value)) or (reply.steps[s].sandbox_check.filter_kind != "none" and reply.phases[p].validator_subprocess.records[v].filter_value == reply.steps[s].sandbox_check.filter_value))
```

#### Order association source {source: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift", "symbol": "eligibleOrderedStep"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerReply.swift", "symbol": "validateForReporting"}]
pins: "Ordering first counts all records for the step ID, then compares the selected record and native value. Production supplies its live worker PID; reporting validation supplies the associated reported worker PID."
```

#### Ordering support {support: owner}

```contract
grade: "check_read"
scope: "subtree"
source: [{"path":"runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift","symbol":"eligibleOrderedStep"},{"path":"runner/Sources/PWRunnerCore/CWorkerComparison.swift","symbol":"buildOrdering"},{"path":"runner/Sources/PWRunnerCore/CWorkerStepResults.swift","symbol":"eligibleOrderedStep"}]
check: {"path":"runner/Tests/PWRunnerCoreTests/OrderingTests.swift","symbol":"runOrderingTests","form":"test"}
pins: "Native answer eligibility and the collection/release/acknowledgement chain are independently required; producer association is exact within the phase."
context: "Read eligibility, ordering construction, phase adaptation and ordering controls."
limits: "Source and check reading; no new execution or mutation-control run is credited."
```

### Temporal meaning {meaning: definition}


Each probe retains its prediction eligibility when another query fails.
A consume, release or other action earlier in the batch can change the
state a later attempt encounters. Submitted-string relations and path
observations retain their respective intervals and identities.

### Classify an observation {observe: checks}

```contract
bind.r: reply.steps
each: ["r"]
when: present(reply.steps[r].comparison)
selection: "first_match"
who: ["identity.definitions.host"]
```


A permission classification records the shape of the native failure.
Attribution to a particular enforcing mechanism requires supporting
evidence.

#### Spawn observed {spawned: outcome}

```contract
test: reply.steps[r].attempt.result_source == "worker" and reply.steps[r].attempt.requested_kind == "exec" and present(reply.steps[r].attempt.child_pid) and reply.steps[r].attempt.child_pid > 0
effects: [set_value(reply.steps[r].comparison.observation, "succeeded"), set_value(reply.steps[r].comparison.observation_basis, "spawned_child")]
```

A positive child PID records spawning even when the child's later status fails.

#### Completed success {completed: outcome}

```contract
test: reply.steps[r].attempt.result_source == "worker" and reply.steps[r].attempt.outcome == "ok" and reply.steps[r].attempt.rc == 0
effects: [set_value(reply.steps[r].comparison.observation, "succeeded"), set_value(reply.steps[r].comparison.observation_basis, "completed_worker_status")]
```

#### Permission errno {permission: outcome}

```contract
test: reply.steps[r].attempt.result_source == "worker" and reply.steps[r].attempt.rc != 0 and reply.steps[r].attempt.outcome in ["open_failed", "read_failed", "write_failed", "unlink_failed", "access_failed", "sysctl_failed", "exec_failed"] and reply.steps[r].attempt.errno in [1, 13]
effects: [set_value(reply.steps[r].comparison.observation, "permission_failure"), set_value(reply.steps[r].comparison.observation_basis, "permission_errno")]
```

Darwin EPERM and EACCES supply the numeric errno alternatives at this boundary.

#### Bootstrap permission result {bootstrap: outcome}

```contract
test: reply.steps[r].attempt.result_source == "worker" and reply.steps[r].attempt.rc != 0 and reply.steps[r].attempt.outcome == "lookup_failed" and reply.steps[r].attempt.error == "bootstrap_look_up: kr=1100"
effects: [set_value(reply.steps[r].comparison.observation, "permission_failure"), set_value(reply.steps[r].comparison.observation_basis, "bootstrap_permission_result")]
```

#### Other completed failure {other: outcome}

```contract
test: reply.steps[r].attempt.result_source == "worker" and reply.steps[r].attempt.rc != 0
effects: [set_value(reply.steps[r].comparison.observation, "other_failure"), set_value(reply.steps[r].comparison.observation_basis, "completed_worker_status")]
```

#### Unavailable observation {unavailable: outcome}

```contract
test: True
effects: [set_value(reply.steps[r].comparison.observation, "unavailable"), set_value(reply.steps[r].comparison.observation_basis, "no_completed_worker_result")]
```

#### Classification support {support: owner}

```contract
grade: "check_read"
scope: "subtree"
source: {"path":"runner/Sources/PWRunnerCore/CWorkerComparison.swift","symbol":"comparisonEvidence"}
check: {"path":"runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift","symbol":"runComparisonEvidenceTests","form":"test"}
pins: "Every scenario-matrix row's constructed attempt result yields its expected observation and basis: a spawned child with either exit status, completed success, permission errno, the bootstrap permission result, another completed failure and a missing result."
context: "Read the producer's branch order and the table-driven reader over the scenario matrix."
limits: "Constructed attempt results were read. Integrated matrix cases own the live rows, without execution credit here."
```

### Submitted operation and target {relations: definition}

| Attempt | Mapped operation | Mapped filter |
| --- | --- | --- |
| file/open_read, file/access, file/read_fresh | file-read-data | path |
| file/open_write, file/write_fresh | file-write-data | path |
| file/unlink | file-write-unlink | path |
| mach_lookup/bootstrap_look_up | mach-lookup | global_name |
| sysctl/read | sysctl-read | sysctl_name |
| exec/spawn | process-exec* | path |
| file/create, file/create_fresh | unresolved compound operation | path |

`process-exec*` predicts target admission; spawn and child observations
record the subsequent operation. Other wildcard query spellings have an
unresolved operation relation. Target equality compares submitted strings;
runtime object identity requires its own observations.

#### Unlink and later observations {unlink: example}

A completed worker unlink with `outcome: ok` and `rc: 0` records removal at
that action. A same-phase query's `query_first` places it before unlink.
Across phases, completion and arrival publications establish sequencing.
A later query can follow unlink and recreation of the same spelling;
these observations belong to their respective objects and times.

#### Comparison support {support: owner}

```contract
grade: "check_read"
scope: "subtree"
source: {"path":"runner/Sources/PWRunnerCore/CWorkerComparison.swift","symbol":"comparisonEvidence"}
check: {"path":"runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift","symbol":"runComparisonEvidenceTests","form":"test"}
pins: "The scenario matrix checks mapped operations, submitted relations, order and limitation values, including spawn and unlink distinctions."
context: "Read the producer, matrix adapter and shared reading rules with their scenario descriptions."
limits: "Constructed controls were read. Corresponding integrated cases own live filesystem scenarios, without execution credit here."
```

### Observe fresh descriptors {fresh: acts}

```contract
uses: ["steps.assessment.fresh_read_aggregate", "steps.assessment.fresh_write_aggregate"]
who: ["identity.definitions.worker"]
where: "released probe action"
free.effect: Open a new descriptor during the released action, perform the action-specific native sequence and publish each reached operation when the slot completes.
retained_free: {"effect": {"kind": "native_protocol", "reason": "Descriptor acquisition, call order and release publication are native events. The adjacent aggregate classifiers express the ordered selection from carried native returns and errno values."}}
```

A successful read records the bytes actually returned.

Unreached operations remain absent.

#### Publication support {support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"PW_ATTEMPT_FILE_READ_FRESH"},{"path":"runner/Sources/PWRunnerCore/CWorker.swift","symbol":"decodeFreshRead"},{"path":"runner/Sources/PWRunnerCore/CWorker.swift","symbol":"decodeFreshWrite"},{"path":"runner/Sources/PWRunnerCore/CWorkerStepResults.swift","symbol":"buildAttemptResult"}]
check: {"path":"runner/Tests/PWRunnerCoreTests/FreshWriteEvidenceTests.swift","symbol":"runFreshWriteEvidenceTests","form":"test"}
pins: "Completed publication gates detailed payloads; fresh-write controls distinguish creation, truncate, short write, metadata precedence and absent operations."
context: "Read native sequences, shared-memory decoding, step construction and fresh-write controls."
limits: "Fresh-read sequencing is source-supported here. Constructed controls establish record consistency; live effects have integrated owners."
```

### Add host path observations {paths: acts}

```contract
each: ["p", "s"]
who: ["identity.definitions.host"]
where: "after orchestration"
free.effect: Resolve qualifying query and attempt paths through the host filesystem after orchestration. Preserve independent realpath, parent-form and firmlink observations and their unavailable results.
retained_free: {"effect": {"kind": "environment_observation", "reason": "Realpath, parent lookup and firmlink resolution are later filesystem observations; channel input eligibility and fixed output provenance are structured below."}}
```

A missing leaf can have
a parent form and a null realpath form. The submitted
comparison operands remain preserved.

#### Path support {support: owner}

```contract
grade: "check_read"
source: [{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"enrichPathDiagnostics"},{"path":"runner/Sources/PWRunnerCore/PathUtils.swift","symbol":"parentRealpathResolved"},{"path":"runner/Sources/PWRunnerCore/PathUtils.swift","symbol":"firmlinkResolved"}]
check: {"path":"runner/Tests/PWRunnerCoreTests/PathDiagnosticsTests.swift","symbol":"runPathDiagnosticsTests","form":"test"}
pins: "Path controls create parents and symlinks, distinguish missing and symlink leaves, skip non-path attempts and preserve separate query observations."
context: "Read enrichment, helpers and path controls, including exact UTF-8 retention."
limits: "Check reading; the observations retain the host's after-orchestration interval."
```

#### Attempt path input {attempt: effect}

```contract
on: "always"
when: reply.steps[s].attempt.requested_kind in ["file", "exec"] and present(reply.steps[s].attempt.requested_path) and reply.steps[s].attempt.requested_path != ""
effects: [set_value(reply.steps[s].attempt.path_diagnostics.input, reply.steps[s].attempt.requested_path), set_value(reply.steps[s].attempt.path_diagnostics.observer, "runner_host"), set_value(reply.steps[s].attempt.path_diagnostics.stage, "after_orchestration")]
```

#### Attempt path input applicability {attempt_presence: condition}

```contract
test: implies(reply.steps[s].attempt.requested_kind in ["file", "exec"] and present(reply.steps[s].attempt.requested_path) and reply.steps[s].attempt.requested_path != "", present(reply.steps[s].attempt.path_diagnostics))
```

#### Query path input {query: effect}

```contract
on: "always"
when: reply.steps[s].sandbox_check.filter_kind == "path" and present(reply.steps[s].sandbox_check.filter_value) and reply.steps[s].sandbox_check.filter_value != ""
effects: [set_value(reply.steps[s].sandbox_check.path_diagnostics.input, reply.steps[s].sandbox_check.filter_value), set_value(reply.steps[s].sandbox_check.path_diagnostics.observer, "runner_host"), set_value(reply.steps[s].sandbox_check.path_diagnostics.stage, "after_orchestration")]
```

#### Query path input applicability {query_presence: condition}

```contract
test: implies(reply.steps[s].sandbox_check.filter_kind == "path" and present(reply.steps[s].sandbox_check.filter_value) and reply.steps[s].sandbox_check.filter_value != "", present(reply.steps[s].sandbox_check.path_diagnostics))
```

### Project the fresh-read aggregate {fresh_read_aggregate: reports}

```contract
who: ["identity.definitions.worker", "identity.definitions.host"]
where: "completed native aggregate projection"
entry: ["xpc_execute"]
recipient: ["controller", "xpc_caller"]
report: ["runner_reply"]
when: reply.steps[s].attempt.requested_kind == "file" and reply.steps[s].attempt.requested_action == "read_fresh" and reply.steps[s].attempt.result_source == "worker" and present(reply.steps[s].attempt.fresh_read)
each: ["p", "s"]
selection: "first_match"
```

#### open failure with errno {open_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_read.open_rc) and reply.steps[s].attempt.fresh_read.open_rc < 0 and present(reply.steps[s].attempt.fresh_read.open_errno) and reply.steps[s].attempt.fresh_read.open_errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "read_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_read.open_errno)]
```

#### open failure without nonzero errno {open_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_read.open_rc) and reply.steps[s].attempt.fresh_read.open_rc < 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "read_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### stat failure with errno {stat_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_read.stat_rc) and reply.steps[s].attempt.fresh_read.stat_rc != 0 and present(reply.steps[s].attempt.fresh_read.stat_errno) and reply.steps[s].attempt.fresh_read.stat_errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "read_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_read.stat_errno)]
```

#### stat failure without nonzero errno {stat_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_read.stat_rc) and reply.steps[s].attempt.fresh_read.stat_rc != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "read_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### read failure with errno {read_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_read.read_rc) and reply.steps[s].attempt.fresh_read.read_rc < 0 and present(reply.steps[s].attempt.fresh_read.read_errno) and reply.steps[s].attempt.fresh_read.read_errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "read_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_read.read_errno)]
```

#### read failure without nonzero errno {read_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_read.read_rc) and reply.steps[s].attempt.fresh_read.read_rc < 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "read_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### close failure with errno {close_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_read.close_rc) and reply.steps[s].attempt.fresh_read.close_rc != 0 and present(reply.steps[s].attempt.fresh_read.close_errno) and reply.steps[s].attempt.fresh_read.close_errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "read_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_read.close_errno)]
```

#### close failure without nonzero errno {close_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_read.close_rc) and reply.steps[s].attempt.fresh_read.close_rc != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "read_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### Successful aggregate {success: outcome}

```contract
test: True
effects: [set_value(reply.steps[s].attempt.rc, 0), set_value(reply.steps[s].attempt.outcome, "ok"), set_value(reply.steps[s].attempt.errno, None)]
```

#### Aggregate source {source: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_file_read_fresh"}, {"path": "runner/Sources/PWRunnerCore/CWorkerStepResults.swift", "symbol": "buildAttemptResult"}]
pins: "Native code preserves the first failed reached descriptor operation; the host maps the completed aggregate rc and converts errno zero to null. Creation pre-open stat stays diagnostic."
```

### Project the fresh-write aggregate {fresh_write_aggregate: reports}

```contract
who: ["identity.definitions.worker", "identity.definitions.host"]
where: "completed native aggregate projection"
entry: ["xpc_execute"]
recipient: ["controller", "xpc_caller"]
report: ["runner_reply"]
when: reply.steps[s].attempt.requested_kind == "file" and reply.steps[s].attempt.requested_action in ["write_fresh", "create_fresh"] and reply.steps[s].attempt.result_source == "worker" and present(reply.steps[s].attempt.fresh_write)
each: ["p", "s"]
selection: "first_match"
```

#### open failure with errno {open_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.open_rc) and reply.steps[s].attempt.fresh_write.open_rc < 0 and present(reply.steps[s].attempt.fresh_write.open_errno) and reply.steps[s].attempt.fresh_write.open_errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_write.open_errno)]
```

#### open failure without nonzero errno {open_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.open_rc) and reply.steps[s].attempt.fresh_write.open_rc < 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### opened stat failure with errno {opened_stat_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.opened_stat) and present(reply.steps[s].attempt.fresh_write.opened_stat.rc) and reply.steps[s].attempt.fresh_write.opened_stat.rc != 0 and present(reply.steps[s].attempt.fresh_write.opened_stat.errno) and reply.steps[s].attempt.fresh_write.opened_stat.errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_write.opened_stat.errno)]
```

#### opened stat failure without nonzero errno {opened_stat_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.opened_stat) and present(reply.steps[s].attempt.fresh_write.opened_stat.rc) and reply.steps[s].attempt.fresh_write.opened_stat.rc != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### truncate failure with errno {truncate_errno: outcome}

```contract
test: reply.steps[s].attempt.requested_action == "write_fresh" and present(reply.steps[s].attempt.fresh_write.truncate_rc) and reply.steps[s].attempt.fresh_write.truncate_rc != 0 and present(reply.steps[s].attempt.fresh_write.truncate_errno) and reply.steps[s].attempt.fresh_write.truncate_errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_write.truncate_errno)]
```

#### truncate failure without nonzero errno {truncate_zero: outcome}

```contract
test: reply.steps[s].attempt.requested_action == "write_fresh" and present(reply.steps[s].attempt.fresh_write.truncate_rc) and reply.steps[s].attempt.fresh_write.truncate_rc != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### truncated stat failure with errno {truncated_stat_errno: outcome}

```contract
test: reply.steps[s].attempt.requested_action == "write_fresh" and present(reply.steps[s].attempt.fresh_write.truncated_stat) and present(reply.steps[s].attempt.fresh_write.truncated_stat.rc) and reply.steps[s].attempt.fresh_write.truncated_stat.rc != 0 and present(reply.steps[s].attempt.fresh_write.truncated_stat.errno) and reply.steps[s].attempt.fresh_write.truncated_stat.errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_write.truncated_stat.errno)]
```

#### truncated stat failure without nonzero errno {truncated_stat_zero: outcome}

```contract
test: reply.steps[s].attempt.requested_action == "write_fresh" and present(reply.steps[s].attempt.fresh_write.truncated_stat) and present(reply.steps[s].attempt.fresh_write.truncated_stat.rc) and reply.steps[s].attempt.fresh_write.truncated_stat.rc != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### write failure with errno {write_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.write_rc) and reply.steps[s].attempt.fresh_write.write_rc != 1 and present(reply.steps[s].attempt.fresh_write.write_errno) and reply.steps[s].attempt.fresh_write.write_errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_write.write_errno)]
```

#### write failure without nonzero errno {write_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.write_rc) and reply.steps[s].attempt.fresh_write.write_rc != 1
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### written stat failure with errno {written_stat_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.written_stat) and present(reply.steps[s].attempt.fresh_write.written_stat.rc) and reply.steps[s].attempt.fresh_write.written_stat.rc != 0 and present(reply.steps[s].attempt.fresh_write.written_stat.errno) and reply.steps[s].attempt.fresh_write.written_stat.errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_write.written_stat.errno)]
```

#### written stat failure without nonzero errno {written_stat_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.written_stat) and present(reply.steps[s].attempt.fresh_write.written_stat.rc) and reply.steps[s].attempt.fresh_write.written_stat.rc != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### close failure with errno {close_errno: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.close_rc) and reply.steps[s].attempt.fresh_write.close_rc != 0 and present(reply.steps[s].attempt.fresh_write.close_errno) and reply.steps[s].attempt.fresh_write.close_errno != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, reply.steps[s].attempt.fresh_write.close_errno)]
```

#### close failure without nonzero errno {close_zero: outcome}

```contract
test: present(reply.steps[s].attempt.fresh_write.close_rc) and reply.steps[s].attempt.fresh_write.close_rc != 0
effects: [set_value(reply.steps[s].attempt.rc, -1), set_value(reply.steps[s].attempt.outcome, "write_failed"), set_value(reply.steps[s].attempt.errno, None)]
```

#### Successful aggregate {success: outcome}

```contract
test: True
effects: [set_value(reply.steps[s].attempt.rc, 0), set_value(reply.steps[s].attempt.outcome, "ok"), set_value(reply.steps[s].attempt.errno, None)]
```

#### Aggregate source {source: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_file_write_fresh"}, {"path": "runner/Sources/PWRunnerCore/CWorkerStepResults.swift", "symbol": "buildAttemptResult"}]
pins: "Native code preserves the first failed reached descriptor operation; the host maps the completed aggregate rc and converts errno zero to null. Creation pre-open stat stays diagnostic."
```

## Record-field support {support: owner}

```contract
grade: "source_read"
scope: "subtree"
source: [{"path":"runner/Sources/PWRunnerCore/CWorkerStepResults.swift","symbol":"buildStepResults"},{"path":"runner/Sources/PWRunnerCore/CWorkerComparison.swift","symbol":"comparisonEvidence"},{"path":"runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift","symbol":"PWRunnerStepResult"},{"path":"runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift","symbol":"ValidatorVerdict"},{"path":"runner/Sources/PWRunnerCore/CWorker.swift","symbol":"decodeFreshRead"},{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"enrichPathDiagnostics"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner_abi.h", "symbol": "PW_SHM_CHILD_OUTPUT_BYTES"}, {"path": "controller/tools/pw_probe_runner/pw_worker_exec.h", "symbol": "stdout_overflow"}]
pins: "Imported fields receive their producer meanings, channel origins and observation boundaries."
context: "Read definitions alongside assembly, native payload decoding and path enrichment."
limits: "Source support; specific rules have separately graded check owners."
```

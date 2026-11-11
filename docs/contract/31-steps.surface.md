# Predictions, attempts and comparison {steps: surface}

```contract
syntax: 1
artifact: "Predictions, attempts and comparison"
part: "report"
goldens: ["tests/fixtures/contract/surfaces/steps.json", "tests/fixtures/comparison/matrix.json"]
checks: ["runner_unit", "failure_boundaries", "witness_contract"]
who: "runner host"
where: "step evidence assembly"
entry: ["cli", "direct_xpc"]
recipient: ["controller", "xpc_caller"]
report: ["ordinary", "actors", "reporting_failure"]
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

Host assessment of observation, submitted scopes and reply.phases[p].ordering. Reporting fallback withholds every comparison.

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

Filter spelling carried by the frame, omitted when absent. Query association compares the projected filter's uppercase spelling.

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

The accepted frame's outcome string. Unfamiliar diagnostic strings remain retained with their recorded diagnostic meaning.

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

`succeeded`, `permission_failure`, `other_failure` or `unavailable`, classified from the attempt channel by the rule below.

### observation_basis {observation_basis: field}

Supporting observation: `spawned_child`, `completed_worker_status`, `permission_errno`, `bootstrap_permission_result` or `no_completed_worker_result`.

### operation_relation {operation_relation: field}

`matched` means the query equals the action's mapped operation; `different` means those strings differ; `unresolved` means the mapping cannot assign a single operation.

### target_relation {target_relation: field}

`same_submitted` or `different_submitted` compares submitted strings when the query filter matches the action's mapped filter and both strings exist; otherwise `unresolved`.

### order {order: field}

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

Sorted unique driver and assembly findings about the collection/release/acknowledgement protocol. An empty array is one prerequisite of the established chain.

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
who: ["identity.definitions.host"]
where: "per-step ordering assessment"
report: ["ordinary", "actors"]
failure: "first"
free.when: A nondegraded report retains this probe's comparison.
free.effect: Set comparison.order to query_first exactly when all eligibility conditions hold; otherwise retain unestablished.
```

#### Collection chain {chain: condition}

```contract
test: present(reply.phases[p].ordering) and reply.phases[p].ordering.collection_closed_before_proceed and reply.phases[p].ordering.proceed_set and reply.phases[p].ordering.proceed_observed and reply.phases[p].ordering.worker_lifetime_established and count(reply.phases[p].ordering.protocol_violations) == 0
```

Collection closed, release and acknowledgement occurred, and worker
ownership was established through acknowledgement.

#### Setup {setup: condition}

```contract
free.condition: Ordinary execution has observed successful application; actor execution has established the actor's declared applied or unapplied setup.
```

#### Native answer {native: condition}

```contract
test: reply.steps[s].sandbox_check.result_source == "validator" and present(reply.steps[s].sandbox_check.native_rc) and present(reply.steps[s].sandbox_check.errno) and reply.steps[s].sandbox_check.rc == reply.steps[s].sandbox_check.native_rc and ((reply.steps[s].sandbox_check.outcome == "allow" and reply.steps[s].sandbox_check.native_rc == 0) or (reply.steps[s].sandbox_check.outcome == "deny" and reply.steps[s].sandbox_check.native_rc == 1 and reply.steps[s].sandbox_check.errno == 0))
```

#### Unique association {association: condition}

```contract
free.condition: The query targets the associated worker PID, and exactly one retained validator record has the step identifier and matches operation, uppercase filter kind, native filter value, outcome, return and errno.
```

The native value for a none filter is absent. Other filters compare the
carried value with the projected query value.

### Temporal meaning {meaning: definition}

`query_first` places this prediction before the phase's attempt batch.
Each probe retains its prediction eligibility when another query fails.
Attempt success and aggregate run success have independent meanings.
A consume, release or other action earlier in the batch can change the
state a later attempt encounters. Submitted-string relations and path
observations retain their respective intervals and identities.

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

### Classify an observation {observe: checks}

```contract
who: ["identity.definitions.host"]
free.effect: Select the first applicable observation below from the attempt channel and retain its stated basis.
```

| Condition in order | Observation | Basis |
| --- | --- | --- |
| Worker source, exec kind, positive child PID | succeeded | spawned_child |
| Worker source, ok outcome, zero return | succeeded | completed_worker_status |
| Worker source, nonzero return, file/sysctl/exec failure carrying EPERM or EACCES | permission_failure | permission_errno |
| Worker source, lookup_failed with exactly `bootstrap_look_up: kr=1100` | permission_failure | bootstrap_permission_result |
| Worker source, nonzero return | other_failure | completed_worker_status |
| Otherwise | unavailable | no_completed_worker_result |

A permission classification records the shape of the native failure.
Attribution to a particular enforcing mechanism requires supporting
evidence. A positive child PID establishes spawning even when the child
subsequently exits nonzero.

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
pins: "The scenario matrix checks channel classification, mapped operations, submitted relations, order and limitation values, including spawn and unlink distinctions."
context: "Read the producer, matrix adapter and shared reading rules with their scenario descriptions."
limits: "Constructed controls were read. Corresponding integrated cases own live filesystem scenarios, without execution credit here."
```

### Observe fresh descriptors {fresh: acts}

```contract
who: "C worker"
where: "released probe action"
free.effect: Open a new descriptor during the action, publish reached native operations and preserve the aggregate's first failed descriptor operation.
```

`read_fresh` performs descriptor stat, bounded read and close after a
successful open. The first stat, read or close failure supplies the
aggregate failure. A successful read records the bytes actually returned.

`write_fresh` opens, records descriptor metadata, truncates to zero,
records metadata again, writes one byte if truncation succeeded, records
metadata after that write and closes. `create_fresh` first records a
path-stat diagnostic, then opens with exclusive creation, records descriptor
metadata, writes one byte, records metadata and closes. Creation's pre-open
stat is diagnostic. Metadata, truncate, write and close failures preserve
the first failed descriptor operation; a short write fails with its
observed count. Unreached operations remain absent.

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
who: "runner host"
where: "after orchestration"
free.effect: Add query and attempt path forms to their separate channel records when their path inputs qualify.
```

Query realpath and firmlink forms describe host observations after
orchestration. The attempt's realpath follows the leaf; its parent form
resolves the parent and appends the literal leaf. A missing leaf can have
a parent form and a null realpath form. For a symlink leaf, the parent form
names the link while realpath can name its destination. The submitted
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

## Record-field support {support: owner}

```contract
grade: "source_read"
scope: "subtree"
source: [{"path":"runner/Sources/PWRunnerCore/CWorkerStepResults.swift","symbol":"buildStepResults"},{"path":"runner/Sources/PWRunnerCore/CWorkerComparison.swift","symbol":"comparisonEvidence"},{"path":"runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift","symbol":"PWRunnerStepResult"},{"path":"runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift","symbol":"ValidatorVerdict"},{"path":"runner/Sources/PWRunnerCore/CWorker.swift","symbol":"decodeFreshRead"},{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"enrichPathDiagnostics"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner_abi.h", "symbol": "PW_SHM_CHILD_OUTPUT_BYTES"}, {"path": "controller/tools/pw_probe_runner/pw_worker_exec.h", "symbol": "stdout_overflow"}]
pins: "Imported fields receive their producer meanings, channel origins and observation boundaries."
context: "Read definitions alongside assembly, native payload decoding and path enrichment."
limits: "Source support; specific rules have separately graded check owners."
```

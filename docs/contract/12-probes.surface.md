# Paired probes and attempted operations {probes: surface}

```contract
syntax: 1
artifact: "Paired probes and attempted operations"
part: "input"
goldens: ["tests/fixtures/contract/surfaces/probes.json"]
checks: ["failure_boundaries"]
```



## Paired probe {step: subject}

```contract
record: "PWRunnerProbeStep"
as: "step"
```

One paired probe contributes one action and at most one eligible validator query. Its prediction is collected at the phase barrier before the attempt is released.

### step_id {step_id: field}

Caller label associating a query with its attempt and result. It is unique across all actions and fits <!-- span limits.step_id.value_unit -->63 UTF-8 bytes<!-- /span --> and is NUL-free. Actor plans require it to be nonempty; ordinary plans currently accept a unique empty value.

### sandbox_check {sandbox_check: field}

Requested prediction operation and filter. Admission validates this request independently from the attempt.

### attempt {attempt: field}

Requested native operation. The caller may intentionally pair a different query target or operation; report readers assess those relations separately.

### Read-hosts pair {read_hosts: example}

This step pairs a path query with an open-read attempt:

```json
{"step_id":"read-hosts","sandbox_check":{"operation":"file-read-data","filter":{"kind":"path","value":"/etc/hosts"}},"attempt":{"kind":"file","action":"open_read","target":"/etc/hosts"}}
```

The open-read operation's success establishes its open boundary. A `read_fresh` attempt supplies the separate read-count, content and close observations described by the step-result surface.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerProbeStep"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "requestMeaningFailure"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent field meanings and operations follow the named implementation."
context: "Current source read for this draft."
limits: "Grammar and uniqueness branches read. The teaching step is a template; no live result is claimed."
```



## Sandbox query {query: subject}

```contract
record: "PWRunnerSandboxCheck"
as: "query"
```



### operation {operation: field}

Nonempty after whitespace trimming for admission, bounded by <!-- span limits.query_operation.value_unit -->127 UTF-8 bytes<!-- /span -->, NUL-free operation string passed unchanged to prediction planning. Accepted strings remain open to native operation support.

### filter {filter: field}

Closed filter kind with its applicable optional value.

### Admission and eligibility {eligibility: acts}

```contract
who: "host"
where: "query admission and planning"
entry: ["ordinary_xpc_execute", "actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Refuse a blank operation, unknown filter or inapplicable/missing filter value as a whole-request error. For an admitted query, withhold native prediction when its path fails host realpath planning or its operation/filter pair is excluded; report prediction_unavailable while leaving the attempt eligible.
```

A path created by the attempt can be unresolved at planning and resolve in later host diagnostics. These observations have separate times and owners.

### Excluded prediction pairs {excluded: definition}

```contract
defines: "condition"
```

These exact pairs are excluded by the planner:

| Operation | Filter |
| --- | --- |
| `iokit-open-service` | `iokit_registry_entry_class` |
| `iokit-open-user-client` | `iokit_user_client_class` |
| `sysctl-read` | `sysctl_name` |
| `mach-lookup` | `local_name` |

The exclusion belongs to the pair. Other operations using the same filter follow their own eligibility and native result.

### Prediction-exclusion evidence scope {exclusion_evidence: definition}

```contract
defines: "value"
```

The IOKit and sysctl exclusions retain the dated 2026-05-29 exploration of filter IDs 1–200. The local Mach mapping remains conservatively unresolved. Each native filter observation belongs to its recorded operation, target and platform; the finite exploration bounds the basis for the current exclusion table.

#### Disposition support {disposition_support: owner}

```contract
grade: "source_read"
source: {"path":"runner/Sources/PWRunnerCore/ProbeRunner.swift","symbol":"predictionUnavailableOpFilters"}
pins: "The table preserves the dated IOKit/sysctl exploration and conservative local-Mach choice."
context: "Static review of the cited production branches."
limits: "This owner reads the recorded basis and current table; it adds no native rerun credit."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "predictionUnavailableOpFilters"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "pathFilterIsUnresolvable"}]
pins: "The adjacent field meanings and operations follow the named implementation."
context: "Current source read for this draft."
limits: "Source inspection supplies the stated branch behavior; this draft credits no execution."
```



## Sandbox filter {filter: subject}

```contract
record: "PWRunnerSandboxFilter"
as: "filter"
```



### kind {kind: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["none", "path", "global_name", "local_name", "iokit_registry_entry_class", "iokit_user_client_class", "sysctl_name"]
```

Filter representation admitted by the host.

### value {value: field}

For `none`, require absence or null. Every other kind requires a string nonempty after whitespace trimming, bounded by <!-- span limits.query_filter_value.value_unit -->511 UTF-8 bytes<!-- /span --> and NUL-free. The original string is retained and passed through unchanged.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "sandboxCheckFailure"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerSandboxFilter"}]
pins: "The adjacent field meanings and operations follow the named implementation."
context: "Current source read for this draft."
limits: "Source inspection supplies the stated branch behavior; this draft credits no execution."
```



## Attempt request {attempt: subject}

```contract
record: "PWRunnerAttempt"
as: "attempt"
```



### kind {kind: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["file", "mach", "sysctl", "exec"]
```

Native operation family selected with action.

### action {action: field}

Closed action within its family, listed in the operation table below. An unsupported pair refuses the complete request before children.

### target {target: field}

Operation target, bounded by <!-- span limits.attempt_target.value_unit -->511 UTF-8 bytes<!-- /span --> and NUL-free. Exec requires an absolute path. Other admitted targets retain their supplied native-operation meaning.

### args {args: field}

```contract
default: []
```

Exec-only argument strings appended after target as argv[0]. Omission and null mean an empty list. A supplied array on another kind, including an empty array, is refused. At most <!-- span limits.exec_arguments.value_unit -->15 items<!-- /span --> are admitted, each NUL-free and bounded by <!-- span limits.exec_argument.value_unit -->127 UTF-8 bytes<!-- /span -->.

### Native operations {operations: definition}

```contract
defines: "action"
```

The worker runs the selected operation after policy application in an apply worker, or after the unapplied actor's setup:

| Kind / action | Native operation and operation-specific consequence |
| --- | --- |
| `file / open_read` | `open(O_RDONLY)`; on an accepted descriptor, request a one-byte read and close. Aggregate success is the successful open; read and close results are discarded. |
| `file / open_write` | `open(O_WRONLY \| O_TRUNC)`; on an accepted descriptor, request a one-byte `x` write and close. Aggregate success is the successful open; write and close results are discarded. |
| `file / create` | `open(O_WRONLY \| O_CREAT, 0600)` then close. Creation mode is subject to umask. An existing file is opened without truncation or exclusive creation. |
| `file / read_fresh` | Fresh `open(O_RDONLY \| O_CLOEXEC)`, `fstat`, one read bounded by <!-- span limits.fresh_read_bytes.value_unit -->64 bytes<!-- /span -->, then close. Record each boundary and read bytes; aggregate failure selects stat, read or close failure after a successful open. |
| `file / write_fresh` | Fresh `open(O_WRONLY \| O_CLOEXEC)` of an existing target, opened `fstat`, `ftruncate(0)`, truncated `fstat`, one-byte `x` write after successful truncation, written `fstat`, then close. Preserve the first failure in the aggregate. |
| `file / create_fresh` | `lstat` before a fresh exclusive `open(O_WRONLY \| O_CLOEXEC \| O_CREAT \| O_EXCL, 0600)`, opened `fstat`, one-byte `x` write, written `fstat`, then close. Pre-open `lstat` is an independent observation. Preserve the first operation failure in the aggregate. |
| `file / unlink` | `unlink(target)` and its return/errno. |
| `file / access` | `access(target, R_OK)` and its return/errno. This is an access-check observation. |
| `mach / lookup` | Obtain the task bootstrap port and call `bootstrap_look_up` for the supplied name; release the returned service port on success. |
| `sysctl / read` | One `sysctlbyname` call with a <!-- span limits.sysctl_read_bytes.value_unit -->4,096 bytes<!-- /span --> buffer acquired after application. Report the call's result and errno; discard value bytes and the returned length. |
| `exec / spawn` | Prepare per-attempt child resources, call `posix_spawn` for the absolute target with the requested argv, then collect child and cleanup observations. |

A short fresh write records its native count and fails the aggregate while retaining zero native errno when the write returned a short nonnegative count. A fresh file descriptor belongs to that attempt and is closed before its result is published.

### Execute a declared operation {execute: acts}

```contract
who: "C worker"
where: "released action slot"
entry: ["ordinary_worker", "actor_worker"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Dispatch only the admitted kind/action pair, record the operation's native observations and publish its slot after the attempt. Preserve operation-specific success meaning alongside the aggregate result.
uses: ["identity.definitions.observation", "identity.definitions.effect"]
```



### Exec setup and child inputs {exec: acts}

```contract
who: "C worker"
where: "released exec action after setup"
entry: ["ordinary_worker", "actor_worker"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: After application or an actor's unapplied declaration, acquire stdout/stderr pipes and spawn actions for this released attempt, release them on setup failure and at completion, and report the failing setup call when spawning was prevented. Spawn with target as argv[0], an empty environment, /dev/null stdin, captured stdout/stderr, close-on-exec descriptor policy and a new process group.
```

A successful spawn supplies a child PID even if the child later exits nonzero. The child collection, termination request and owned reap remain separate observations. The production per-child collection allowance is <!-- span limits.exec_child_wait.value_unit -->10,000 milliseconds<!-- /span --> after successful spawn, capped by the remaining per-worker active-plan allowance of <!-- span limits.exec_attempt_budget.value_unit -->115,000 milliseconds<!-- /span -->. The active-plan clock starts before worker setup, includes setup and intervening work, and excludes acknowledged release waits and accepted actor parked-activation waits. Both allowances use continuous time, including system sleep. Exhausted allowance can refuse a later spawn or stop collection; clock faults retain their own boundary. Blocking native calls can outlast the allowance.

### Extension participant restriction {extension_exec: acts}

```contract
who: "host"
where: "actor admission"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Refuse exec probes in every actor participating in an extension operation, including an actor named only as a transfer recipient. Other actors may declare exec probes.
uses: ["extensions.operation"]
```



### Operation observation scope {operation_evidence: definition}

```contract
defines: "value"
```

Fresh-file records retain the reached descriptor operations and the bytes or object identity observed by those operations. Exec records distinguish child creation, final child status, captured output and cleanup. The legacy open operations keep their open-boundary aggregate meaning. Independent target and process observations supply the evidence for effects claimed by a concrete operation control.

#### Disposition support {disposition_support: owner}

```contract
grade: "source_read"
source: [{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"attempt_file_read_fresh"},{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"attempt_file_write_fresh"},{"path":"runner/Sources/PWRunnerCore/CWorkerStepResults.swift","symbol":"buildAttemptResult"}]
pins: "Native operation details and aggregate return/errno projection have their own report fields."
context: "Static review of the cited production branches."
limits: "This owner is source-read. Selected fresh-file, descriptor, sysctl-buffer and exec-cleanup executions need their exact operation owners."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "mapAttemptKind"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_file_open_read"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_file_write_fresh"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_sysctl_read"}, {"path": "controller/tools/pw_probe_runner/pw_worker_exec.h", "symbol": "attempt_exec_spawn"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}, {"path": "controller/tools/pw_probe_runner/pw_worker_timing.h", "symbol": "PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT"}, {"path": "controller/tools/pw_probe_runner/pw_worker_timing.h", "symbol": "pw_timing_setup"}]
pins: "The adjacent field meanings and operations follow the named implementation."
context: "Current source read for this draft."
limits: "Source inspection supplies the stated branch behavior; this draft credits no execution."
```

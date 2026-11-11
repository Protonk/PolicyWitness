# Existing relationships as model trials {trial: surface}

```contract
syntax: 1
artifact: "Private trials of current contract relationships"
part: "assessment"
goldens: ["tests/fixtures/contract/compiled_profile.json"]
checks: ["source_drift"]
who: "runner host"
where: "typed request or report boundary named by each rule"
entry: ["xpc_execute"]
recipient: ["host", "controller"]
report: ["runner_reply"]
```

These partial record subjects exercise actual imported operands. Their full field
meanings remain in the corresponding production surface subjects.

## Admitted request {request: subject}

```contract
record: "PWRunnerRunSpec"
as: "plan"
at: ["request"]
```

### Total phased actions {capacity: checks}

```contract
where: "phase action capacity admission"
entry: ["xpc_execute"]
when: present(plan.phases)
bind.p: plan.phases
test: sum_over(p, count(plan.phases[p].actions)) <= limit("probe_steps")
```

The whole request's action capacity applies across phases. The value is the
current `probe_steps` capacity, resolved from its owning limits inventory beside
the actual aggregate operand.

### Each phase identifier {identity: checks}

```contract
where: "phase identity admission"
entry: ["xpc_execute"]
when: present(plan.phases)
bind.p: plan.phases
bind.q: plan.phases
match.q: plan.phases[q].phase_id == plan.phases[p].phase_id
each: ["p"]
test: matches(q) == 1 and utf8_length(plan.phases[p].phase_id) > 0 and utf8_length(plan.phases[p].phase_id) <= limit("phase_id") and not contains(plan.phases[p].phase_id, "\u0000")
```

Each phase has one occurrence of its identifier, within its UTF-8 capacity and
without an embedded NUL.

### Each actor phase has a declared owner {owner: checks}

```contract
where: "actor phase ownership admission"
entry: ["xpc_execute"]
when: present(plan.actors) and present(plan.phases)
bind.p: plan.phases
bind.a: plan.actors
match.a: plan.actors[a].actor_id == plan.phases[p].actor_id
each: ["p"]
test: matches(a) == 1
```

The named phase owner resolves to one declared actor.

### Probe action identifiers {probe_identity: checks}

```contract
where: "phase action identity admission"
entry: ["xpc_execute"]
bind.p: plan.phases
bind.a: plan.phases[p].actions
each: ["p", "a"]
when: present(plan.actors) and present(plan.phases) and is_variant(plan.phases[p].actions[a], "probe")
test: variant(plan.phases[p].actions[a], "probe").step_id != ""
```

In the actor form, the predicate names an imported action alternative and the
projection reads its actual step identifier.

### Prediction barrier {barrier: acts}

```contract
where: "phase scheduler"
entry: ["xpc_execute"]
free.effect: Close the active phase's eligible prediction collection before releasing its actions; run those actions in declaration order. Begin the next phase's collection after the previous phase completes.
retained_free: {"effect":{"kind":"native_protocol","reason":"The host's collection closure and release store, followed by worker completion and the next activation, describe the native scheduling protocol rather than a predicate over a final report."}}
```

## Emitted host report {reply: subject}

```contract
record: "PWRunnerRunResult"
as: "host_report"
at: ["reply"]
```

### Pre-execution request refusal {refusal: reports}

```contract
where: "request refusal reply construction"
entry: ["xpc_execute"]
when: host_report.normalized_outcome == "bad_request"
effects: set_value(host_report.steps, [])
```

Request refusal emits an empty probe-result array.

## Captured profile {receipt: subject}

```contract
record: "CompiledProfileCapture"
as: "receipt"
at: ["reply.compiled_profile"]
```

### Captured extent {extent: checks}

```contract
where: "captured receipt definition"
entry: ["xpc_execute"]
when: receipt.status == "captured"
test: byte_length(receipt.bytecode_b64) == receipt.bytecode_length
```

The imported field is bytes projected as base64. Its decoded payload size agrees
with the recorded bytecode length; encoded base64 width is a separate quantity.

## Probe result {step: subject}

```contract
record: "PWRunnerStepResult"
as: "row"
```

### Classify the attempt observation {observation: reports}

```contract
where: "comparisonEvidence attempt-channel classification"
entry: ["xpc_execute"]
selection: "first_match"
```

The observation and its basis are assigned together from the first matching
case. This trial transcribes the current branch order in `comparisonEvidence`.

#### Spawn observed {spawned: outcome}

```contract
test: row.attempt.result_source == "worker" and row.attempt.requested_kind == "exec" and present(row.attempt.child_pid) and row.attempt.child_pid > 0
effects: [set_value(row.comparison.observation, "succeeded"), set_value(row.comparison.observation_basis, "spawned_child")]
```

A positive child PID records spawning even when the child's later status fails.

#### Completed success {completed: outcome}

```contract
test: row.attempt.result_source == "worker" and row.attempt.outcome == "ok" and row.attempt.rc == 0
effects: [set_value(row.comparison.observation, "succeeded"), set_value(row.comparison.observation_basis, "completed_worker_status")]
```

#### Permission errno {permission: outcome}

```contract
test: row.attempt.result_source == "worker" and row.attempt.rc != 0 and row.attempt.outcome in ["open_failed", "read_failed", "write_failed", "unlink_failed", "access_failed", "sysctl_failed", "exec_failed"] and row.attempt.errno in [1, 13]
effects: [set_value(row.comparison.observation, "permission_failure"), set_value(row.comparison.observation_basis, "permission_errno")]
```

Darwin EPERM and EACCES supply the numeric errno alternatives at this boundary.

#### Bootstrap permission result {bootstrap: outcome}

```contract
test: row.attempt.result_source == "worker" and row.attempt.rc != 0 and row.attempt.outcome == "lookup_failed" and row.attempt.error == "bootstrap_look_up: kr=1100"
effects: [set_value(row.comparison.observation, "permission_failure"), set_value(row.comparison.observation_basis, "bootstrap_permission_result")]
```

#### Other completed failure {other: outcome}

```contract
test: row.attempt.result_source == "worker" and row.attempt.rc != 0
effects: [set_value(row.comparison.observation, "other_failure"), set_value(row.comparison.observation_basis, "completed_worker_status")]
```

#### Unavailable observation {unavailable: outcome}

```contract
test: True
effects: [set_value(row.comparison.observation, "unavailable"), set_value(row.comparison.observation_basis, "no_completed_worker_result")]
```

## Trial provenance {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"runner/Sources/PWRunnerCore/ActorPlan.swift","symbol":"normalizeActorPlan"},{"path":"runner/Sources/PWRunnerCore/ProbeRunner.swift","symbol":"requestMeaningFailure"},{"path":"runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift","symbol":"admissionFailure"},{"path":"runner/Sources/PWRunnerCore/CWorkerComparison.swift","symbol":"comparisonEvidence"},{"path":"runner/Sources/PWRunnerCore/ActorScheduler.swift","symbol":"walkSchedule"},{"path":"docs/limits.json","symbol":"\"id\": \"probe_steps\""},{"path":"docs/contract/35-profile.surface.md","symbol":"Bytecode length {bytecode_length: field}"},{"path":"docs/contract/30-reply.surface.md","symbol":"Probe results {steps: field}"}]
pins: "Actual request/report operands and the existing observation branch order demonstrate each proposed model feature."
context: "Private authoring trial over imported types; declarations remain partial so the trial uses preview validation."
limits: "Source reading only. No model control, generated render, native observation or integrated acceptance run is credited."
```

# Controller findings and assessments {diagnostics: surface}

```contract
syntax: 1
artifact: "Controller findings and assessments"
part: "assessment"
goldens: ["tests/fixtures/contract/surfaces/diagnostics.json"]
checks: ["unit", "failure_boundaries"]
```

The controller retains the admitted host reply and publishes its own
assessment under `data.runner_sandbox_diagnostics`. Each finding has the
scope of the check that produced it. The outer result, a worker's ending,
phase order, native operation and reporting-failure form have separate
conditions.

## Execution diagnostics {execution: subject}

```contract
record: "rust.RunnerExecutionDiagnostics"
as: "diagnostics"
at: ["envelope.data.runner_sandbox_diagnostics"]
```

### process_disposition {process_disposition: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["no_worker", "clean_exit", "nonzero_exit", "signaled", "conflicting", "unconfirmed", "unrecognized", "withheld", "per_actor"]
```

The controller's disposition projection. An ordinary worker supplies its
validated lifecycle result.
`no_worker` means this
projection had no worker subprocess record to assess.

### termination_cause {termination_cause: field}

A controller attribution selected from the validated lifecycle chain.
Actor-form top-level diagnostics begin with null because
causes belong to the actor entries.

### stop_reason {stop_reason: field}

Supported ordinary-worker stop observation when its answer is one of
`sentinel_deadline`, `done`, `child_reaped`, `wait_error`,
`policy_write_error` or `policy_transfer_deadline`; otherwise null.
Actor stop reasons belong to their actor entries.

### disposition_integrity {disposition_integrity: field}

`valid` means the applicable controller checks for this projection passed;
`invalid` means they produced a finding. Null means there was no worker
projection to validate. When at least one actor has a worker projection,
actor aggregation is valid when every actor projection is valid or has null
integrity; it becomes invalid when any actor projection is invalid. With no
worker projections, aggregate integrity remains null.
A host's supported conflict can accompany valid integrity: the controller
has checked the conflict's own evidence.

### disposition_issues {disposition_issues: field}

Controller findings at this scope, followed or preceded according to the
producing check order by copied host conflict records where applicable.
Actor-local findings remain in the actor entry.

### actors {actors: field}

Present for `execution_form: "actors"`, in the host's actor order. Each
entry is derived from that actor's subprocess and its actions selected
through the phase plan.

### Decoded response collection bounds {geometry: checks}

```contract
who: ["identity.definitions.controller"]
where: "decoded response-context admission after delivery, capture and public identity admission"
entry: ["cli_run","runner_verify"]
recipient: ["caller","report_reader"]
report: ["run_envelope","runner_verify"]
when: present(reply)
bind.p: reply.phases
bind.a: reply.actors
```

These bounds apply to every structurally decoded reply reaching this gate, including preparation and reporting-failure replies. Counts use the retained rows before semantic association.

#### Phase and action tables {plan: condition}

```contract
test: implies(reply.execution_form == "actors", count(reply.phases) <= limit("actor_phases")) and implies(absent(reply.execution_form) or (present(reply.execution_form) and reply.execution_form != "actors"), count(reply.phases) <= limit("phase_count")) and count(reply.steps) <= limit("probe_steps") and implies(present(reply.extension_events), count(reply.extension_events) <= limit("probe_steps") - count(reply.steps)) and sum_over(p, count(reply.phases[p].action_ids)) <= limit("probe_steps")
```

#### Actor and transfer tables {actors_transfers: condition}

```contract
test: implies(present(reply.actors), count(reply.actors) <= limit("actors")) and implies(present(reply.transfers), count(reply.transfers) <= limit("actor_deliveries"))
```

#### Resource tables {resources: condition}

```contract
when: present(reply.resources)
test: count(reply.resources.tokens) <= limit("actor_issues") and count(reply.resources.deliveries) <= limit("actor_deliveries") and count(reply.resources.handles) <= limit("actor_handles")
```

#### Equal-handle references {equal_handles: condition}

```contract
when: present(reply.resources)
bind.h: reply.resources.handles
each: ["h"]
test: count(reply.resources.handles[h].raw_equal_handles) <= limit("actor_handles") - 1
```

#### Validator collection tables {validator: condition}

```contract
each: ["p"]
when: present(reply.phases[p].validator_subprocess)
bind.s: reply.steps
match.s: reply.steps[s].phase_id == reply.phases[p].phase_id and reply.steps[s].sandbox_check.missing_reason != "query_not_requested"
```

An absent missing_reason is included.

##### Expected identifiers {expected: condition}

```contract
test: implies(present(reply.phases[p].validator_subprocess.expected_step_ids), count(reply.phases[p].validator_subprocess.expected_step_ids) <= limit("probe_steps"))
```

##### Retained validator records {records: condition}

```contract
when: present(reply.phases[p].validator_subprocess.records)
test: implies(matches(s) == 0, count(reply.phases[p].validator_subprocess.records) <= limit("validator_records_per_query")) and implies(matches(s) > 0, count(reply.phases[p].validator_subprocess.records) <= matches(s) * limit("validator_records_per_query"))
```

##### Association issue allowance {issues: condition}

```contract
when: present(reply.phases[p].validator_subprocess.association_issues)
test: implies(present(reply.phases[p].validator_subprocess.records), count(reply.phases[p].validator_subprocess.association_issues) <= matches(s) + count(reply.phases[p].validator_subprocess.records) + 1) and implies(absent(reply.phases[p].validator_subprocess.records), count(reply.phases[p].validator_subprocess.association_issues) <= matches(s) + 1)
```

#### Equipment tables {equipment: condition}

```contract
test: implies(present(reply.equipment_bindings), count(reply.equipment_bindings) <= limit("equipment_static_bindings")) and implies(present(reply.equipment_entitlements), count(reply.equipment_entitlements) <= limit("equipment_entitlement_records"))
```

#### Authority scope tables {authority: condition}

```contract
when: present(reply.authority_setup)
test: count(reply.authority_setup.workers) <= limit("actors") and count(reply.authority_setup.host.regions) <= limit("actors") and count(reply.authority_setup.host.custody) <= limit("actor_issues")
```

#### Host run authority scope {host_scope: condition}

```contract
when: present(reply.authority_setup)
test: count(reply.authority_setup.host.run.operations) <= 4 and count(reply.authority_setup.host.run.ownership) <= 5 and implies(present(reply.authority_setup.host.run.integrity_errors), count(reply.authority_setup.host.run.integrity_errors) <= 16)
```

#### Worker authority scopes {worker_scopes: condition}

```contract
when: present(reply.authority_setup)
bind.w: reply.authority_setup.workers
each: ["w"]
test: count(reply.authority_setup.workers[w].operations) <= limit("authority_setup_cells") and count(reply.authority_setup.workers[w].ownership) <= 5 and implies(present(reply.authority_setup.workers[w].integrity_errors), count(reply.authority_setup.workers[w].integrity_errors) <= 16)
```

#### Host region authority scopes {region_scopes: condition}

```contract
when: present(reply.authority_setup)
bind.r: reply.authority_setup.host.regions
each: ["r"]
test: count(reply.authority_setup.host.regions[r].operations) <= limit("authority_setup_cells") and count(reply.authority_setup.host.regions[r].ownership) <= 5 and implies(present(reply.authority_setup.host.regions[r].integrity_errors), count(reply.authority_setup.host.regions[r].integrity_errors) <= 16)
```

#### Host custody authority scopes {custody_scopes: condition}

```contract
when: present(reply.authority_setup)
bind.c: reply.authority_setup.host.custody
each: ["c"]
test: count(reply.authority_setup.host.custody[c].operations) <= 4 and count(reply.authority_setup.host.custody[c].ownership) <= 5 and implies(present(reply.authority_setup.host.custody[c].integrity_errors), count(reply.authority_setup.host.custody[c].integrity_errors) <= 16)
```

#### Actor visits {visits: condition}

```contract
when: present(reply.actors)
each: ["a"]
test: count(reply.actors[a].visits) <= limit("actor_phases")
```

#### Actor equipment observations {actor_equipment: condition}

```contract
when: present(reply.actors) and present(reply.actors[a].equipment)
each: ["a"]
test: count(reply.actors[a].equipment.required_entitlements) <= limit("actor_required_entitlements") and implies(present(reply.actors[a].equipment.missing_requirements), count(reply.actors[a].equipment.missing_requirements) <= limit("actor_required_entitlements")) and count(reply.actors[a].equipment.execution.native_observations) <= 4
```

#### Ordinary worker disposition {ordinary_lifecycle: condition}

```contract
when: present(reply.runner_subprocess) and present(reply.runner_subprocess.disposition)
bind.d: reply.runner_subprocess.disposition.steps
bind.i: reply.runner_subprocess.disposition.issues
```

##### Disposition rows {rows: condition}

```contract
test: count(reply.runner_subprocess.disposition.steps) <= limit("probe_steps") and count(reply.runner_subprocess.disposition.issues) <= 1 + 2 * limit("probe_steps")
```

##### Run claim references {run_references: condition}

```contract
test: implies(present(reply.runner_subprocess.disposition.questions.final_status), implies(present(reply.runner_subprocess.disposition.questions.final_status.basis), count(reply.runner_subprocess.disposition.questions.final_status.basis) <= 14)) and implies(present(reply.runner_subprocess.disposition.questions.stop_reason), implies(present(reply.runner_subprocess.disposition.questions.stop_reason.basis), count(reply.runner_subprocess.disposition.questions.stop_reason.basis) <= 14)) and implies(present(reply.runner_subprocess.disposition.questions.cleanup_trigger), implies(present(reply.runner_subprocess.disposition.questions.cleanup_trigger.basis), count(reply.runner_subprocess.disposition.questions.cleanup_trigger.basis) <= 14)) and implies(present(reply.runner_subprocess.disposition.questions.grace_end), implies(present(reply.runner_subprocess.disposition.questions.grace_end.basis), count(reply.runner_subprocess.disposition.questions.grace_end.basis) <= 14)) and implies(present(reply.runner_subprocess.disposition.questions.kill_request_and_result), implies(present(reply.runner_subprocess.disposition.questions.kill_request_and_result.basis), count(reply.runner_subprocess.disposition.questions.kill_request_and_result.basis) <= 14)) and implies(present(reply.runner_subprocess.disposition.questions.collection_basis), implies(present(reply.runner_subprocess.disposition.questions.collection_basis.basis), count(reply.runner_subprocess.disposition.questions.collection_basis.basis) <= 14)) and implies(present(reply.runner_subprocess.disposition.questions.progress_association), implies(present(reply.runner_subprocess.disposition.questions.progress_association.basis), count(reply.runner_subprocess.disposition.questions.progress_association.basis) <= 14))
```

##### Step claim references {step_references: condition}

```contract
each: ["d"]
test: implies(present(reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached), implies(present(reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached.basis), count(reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached.basis) <= 16)) and implies(present(reply.runner_subprocess.disposition.steps[d].questions.step_result_published), implies(present(reply.runner_subprocess.disposition.steps[d].questions.step_result_published.basis), count(reply.runner_subprocess.disposition.steps[d].questions.step_result_published.basis) <= 16)) and implies(present(reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability), implies(present(reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis), count(reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis) <= 16))
```

##### Conflict observation references {issue_references: condition}

```contract
each: ["i"]
test: implies(present(reply.runner_subprocess.disposition.issues[i].step_index), count(reply.runner_subprocess.disposition.issues[i].observations) <= 16) and implies(absent(reply.runner_subprocess.disposition.issues[i].step_index), count(reply.runner_subprocess.disposition.issues[i].observations) <= 14)
```

#### Actor worker disposition {actor_lifecycle: condition}

```contract
when: present(reply.actors) and present(reply.actors[a].subprocess) and present(reply.actors[a].subprocess.disposition)
bind.d: reply.actors[a].subprocess.disposition.steps
bind.i: reply.actors[a].subprocess.disposition.issues
each: ["a"]
```

##### Disposition rows {rows: condition}

```contract
test: count(reply.actors[a].subprocess.disposition.steps) <= limit("probe_steps") and count(reply.actors[a].subprocess.disposition.issues) <= 1 + 2 * limit("probe_steps")
```

##### Run claim references {run_references: condition}

```contract
test: implies(present(reply.actors[a].subprocess.disposition.questions.final_status), implies(present(reply.actors[a].subprocess.disposition.questions.final_status.basis), count(reply.actors[a].subprocess.disposition.questions.final_status.basis) <= 14)) and implies(present(reply.actors[a].subprocess.disposition.questions.stop_reason), implies(present(reply.actors[a].subprocess.disposition.questions.stop_reason.basis), count(reply.actors[a].subprocess.disposition.questions.stop_reason.basis) <= 14)) and implies(present(reply.actors[a].subprocess.disposition.questions.cleanup_trigger), implies(present(reply.actors[a].subprocess.disposition.questions.cleanup_trigger.basis), count(reply.actors[a].subprocess.disposition.questions.cleanup_trigger.basis) <= 14)) and implies(present(reply.actors[a].subprocess.disposition.questions.grace_end), implies(present(reply.actors[a].subprocess.disposition.questions.grace_end.basis), count(reply.actors[a].subprocess.disposition.questions.grace_end.basis) <= 14)) and implies(present(reply.actors[a].subprocess.disposition.questions.kill_request_and_result), implies(present(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.basis), count(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.basis) <= 14)) and implies(present(reply.actors[a].subprocess.disposition.questions.collection_basis), implies(present(reply.actors[a].subprocess.disposition.questions.collection_basis.basis), count(reply.actors[a].subprocess.disposition.questions.collection_basis.basis) <= 14)) and implies(present(reply.actors[a].subprocess.disposition.questions.progress_association), implies(present(reply.actors[a].subprocess.disposition.questions.progress_association.basis), count(reply.actors[a].subprocess.disposition.questions.progress_association.basis) <= 14))
```

##### Step claim references {step_references: condition}

```contract
each: ["d"]
test: implies(present(reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached), implies(present(reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached.basis), count(reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached.basis) <= 16)) and implies(present(reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published), implies(present(reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published.basis), count(reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published.basis) <= 16)) and implies(present(reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability), implies(present(reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis), count(reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis) <= 16))
```

##### Conflict observation references {issue_references: condition}

```contract
each: ["i"]
test: implies(present(reply.actors[a].subprocess.disposition.issues[i].step_index), count(reply.actors[a].subprocess.disposition.issues[i].observations) <= 16) and implies(absent(reply.actors[a].subprocess.disposition.issues[i].step_index), count(reply.actors[a].subprocess.disposition.issues[i].observations) <= 14)
```

#### Attempt lifecycle copies {step_copies: condition}

```contract
when: present(reply.steps[s].attempt.lifecycle)
bind.s: reply.steps
each: ["s"]
test: implies(present(reply.steps[s].attempt.lifecycle.boundary.basis), count(reply.steps[s].attempt.lifecycle.boundary.basis) <= 16) and implies(present(reply.steps[s].attempt.lifecycle.result.basis), count(reply.steps[s].attempt.lifecycle.result.basis) <= 16)
```

#### Extension lifecycle copies {extension_copies: condition}

```contract
when: present(reply.extension_events) and present(reply.extension_events[e].lifecycle)
bind.e: reply.extension_events
each: ["e"]
test: implies(present(reply.extension_events[e].lifecycle.boundary.basis), count(reply.extension_events[e].lifecycle.boundary.basis) <= 16) and implies(present(reply.extension_events[e].lifecycle.result.basis), count(reply.extension_events[e].lifecycle.result.basis) <= 16)
```

#### Failed collection bound {failed: effect}

```contract
on: "failure"
effects: [set_value(result.normalized_outcome, "malformed_runner_response"), set_value(result.ok, False), set_value(result.exit_code, 1), retain_records(reply)]
```

#### Run assessment after refusal {run_refusal: effect}

```contract
entry: ["cli_run"]
on: "failure"
effects: set_value(envelope.data.runner_sandbox_diagnostics, None)
```

#### Verification completion after refusal {verify_refusal: effect}

```contract
entry: ["runner_verify"]
on: "failure"
effects: [set_value(runner_verify.normalized_outcome, "malformed_runner_response"), set_value(runner_verify.runner_pid, None)]
```

#### Response-bound support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"claim_geometry"},{"path":"controller/src/porcelain_admission.rs","symbol":"lifecycle_geometry"},{"path":"controller/src/porcelain_admission.rs","symbol":"scope_geometry"},{"path":"controller/src/porcelain_admission.rs","symbol":"reply_geometry"},{"path":"controller/src/porcelain_admission.rs","symbol":"admission_problem"},{"path":"controller/src/run_flow.rs","symbol":"admit_reply"},{"path":"controller/src/runner_commands.rs","symbol":"cmd_runner_verify"}]
check: [{"path":"controller/src/porcelain_admission.rs","symbol":"typed_geometry_refuses_before_projection_and_retains_every_raw_record","form":"test"},{"path":"controller/src/porcelain_admission.rs","symbol":"typed_reference_geometry_is_checked_before_claims_and_admission_contexts","form":"test"}]
pins: "Collection bounds precede semantic joins and profile-context checking on run and verification admission; their refusal retains the decoded reply."
context: "Read every geometry guard, both public call paths and the named constructed-control bodies."
limits: "The controls assert selected excess tables, reference lists, an accepted boundary and unchanged raw records. The remaining enumerated collection bounds and verification-specific projection are supported by their source branches."
```

### Admit the response before assessment {admit: acts}

```contract
who: ["identity.definitions.controller"]
where: "client delivery, public reply identity and bounded response context"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
uses: ["diagnostics.execution.geometry"]
free.effect: Check request-delivery failure and client capture status, then exact reply identity, response geometry and compiled-profile context before execution diagnostics.
retained_free: {"effect":{"kind":"native_protocol","reason":"Execution diagnostics are reached only after preceding delivery/capture/host-context gates, some of which operate before a decoded reply exists."}}
```

A missing or foreign producer identity follows its own transport/identity
refusal. The geometry guard bounds collections before semantic joins.
The compiled-profile guard checks its status and producer/stage context,
including actor captures and reporting-failure replies. These are
preconditions for the execution-assessment path described here.

#### Decoded response-context refusal {context_refusal: outcome}

```contract
free.when: The controller's response geometry or compiled-profile context check rejects a structurally decoded host reply.
effects: [set_value(envelope.result.normalized_outcome, "malformed_runner_response"), set_value(envelope.result.ok, False), set_value(envelope.result.exit_code, 1), set_value(envelope.data.runner_sandbox_diagnostics, None), retain_records(reply)]
retained_free: {"when":{"kind":"native_protocol","reason":"The geometry or compiled-profile context check returns the intermediate admission decision that selects this refusal."}}
```

The controller returns the selected exit status with the decoded host reply
still available in the envelope.

### Project one worker or aggregate actors {project: acts}

```contract
who: ["identity.definitions.controller"]
where: "typed worker lifecycle interpretation after response admission"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
free.effect: Run the worker lifecycle validation against its native records, assigned actions and reporting form. Project a validated ending by the ending-mapping and stop-reason rules, then publish the validated host conflicts at that worker scope.
retained_free: {"effect":{"kind":"native_protocol","reason":"The controller invokes lifecycle validation for the worker, assigned actions and reporting form. Its returned failure list selects the worker projection path; successful validation proceeds to host-conflict copying. The output field assignments are structured below."}}
```

For the actor form, the controller computes each worker's projection
separately. It then sets the top-level disposition to `per_actor` when any
entry differs from `no_worker`, and aggregates the actor integrity values.

Their lifecycle prerequisites are the actual helper
check in each invocation, including retained reporting-failure replies.

### Actor projection rows {actor_rows: reports}

```contract
who: ["identity.definitions.controller"]
where: "worker projection after response admission"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
when: reply.execution_form == "actors"
bind.a: reply.actors
bind.d: envelope.data.runner_sandbox_diagnostics.actors
match.d: d == a
```

#### Positional coverage {coverage: condition}

```contract
test: present(envelope.data.runner_sandbox_diagnostics.actors) and implies(present(reply.actors), count(envelope.data.runner_sandbox_diagnostics.actors) == count(reply.actors)) and implies(absent(reply.actors), count(envelope.data.runner_sandbox_diagnostics.actors) == 0)
```

#### Copied actor identity {identity: condition}

```contract
each: ["a", "d"]
test: envelope.data.runner_sandbox_diagnostics.actors[d].actor_id == reply.actors[a].actor_id
```

Its label is copied even when that actor has no subprocess. Duplicate labels retain their
separate positions and remain subject to the reply-wide association checks.

### Ordinary worker projection {ordinary: subject}

```contract
who: ["identity.definitions.controller"]
where: "worker projection after response admission"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
when: (absent(reply.execution_form) or (present(reply.execution_form) and reply.execution_form != "actors")) and present(reply.runner_subprocess)
```

The source is `reply.runner_subprocess`; the output is the ordinary
execution diagnostic record, before reply-wide findings are appended.

#### Worker lifecycle validation {lifecycle_check: checks}

```contract
who: ["identity.definitions.controller"]
where: "one worker lifecycle validation before projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
free.condition: For reply.runner_subprocess and its assigned actions under the carried reporting form, the controller's lifecycle validation returns no failed-check findings, before validated host conflicts are copied.
retained_free: {"condition":{"kind":"native_protocol","reason":"This prerequisite is the lifecycle validator's intermediate return for the selected worker, assigned actions and reporting form. Successful validation permits host conflicts to be copied into the final disposition_issues array."}}
```



##### Local lifecycle findings {local_failure: effect}

```contract
on: "failure"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.process_disposition, "withheld"), set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "unknown"), set_value(envelope.data.runner_sandbox_diagnostics.disposition_integrity, "invalid"), set_value(envelope.data.runner_sandbox_diagnostics.stop_reason, None)]
```

#### Ending mapping {mapping: reports}

```contract
who: ["identity.definitions.controller"]
where: "validated worker ending projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
requires: ["diagnostics.execution.ordinary.lifecycle_check"]
when: present(reply.runner_subprocess.disposition) and present(reply.runner_subprocess.disposition.questions.final_status)
selection: "first_match"
```

##### Clean exit {clean: outcome}

```contract
test: reply.runner_subprocess.disposition.questions.final_status.state == "supported" and reply.runner_subprocess.disposition.questions.final_status.answer == "exit_code" and present(reply.runner_subprocess.disposition.questions.final_status.value) and is_variant(reply.runner_subprocess.disposition.questions.final_status.value, "Integer") and variant(reply.runner_subprocess.disposition.questions.final_status.value, "Integer") == 0
effects: [set_value(envelope.data.runner_sandbox_diagnostics.process_disposition, "clean_exit"), set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, None)]
```

##### Other exit status {nonzero: outcome}

```contract
test: reply.runner_subprocess.disposition.questions.final_status.state == "supported" and reply.runner_subprocess.disposition.questions.final_status.answer == "exit_code"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.process_disposition, "nonzero_exit"), set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "unknown")]
```

##### Signaled ending {signal: outcome}

```contract
test: reply.runner_subprocess.disposition.questions.final_status.state == "supported" and reply.runner_subprocess.disposition.questions.final_status.answer == "signal"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.process_disposition, "signaled"), set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "unknown")]
```

##### Supported conflict {conflict: outcome}

```contract
test: reply.runner_subprocess.disposition.questions.final_status.state == "conflicting"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.process_disposition, "conflicting"), set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "unknown")]
```

##### Unresolved or inapplicable ending {unconfirmed: outcome}

```contract
test: reply.runner_subprocess.disposition.questions.final_status.state in ["unresolved", "inapplicable"]
effects: [set_value(envelope.data.runner_sandbox_diagnostics.process_disposition, "unconfirmed"), set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "unknown")]
```

##### Other admitted ending {other: outcome}

```contract
test: True
effects: [set_value(envelope.data.runner_sandbox_diagnostics.process_disposition, "unrecognized"), set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "unknown")]
```

Lifecycle validation
has already checked the integer exit value and supported-conflict evidence.

#### Supported stop reason {stop: reports}

```contract
who: ["identity.definitions.controller"]
where: "validated worker ending projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
requires: ["diagnostics.execution.ordinary.lifecycle_check"]
when: present(reply.runner_subprocess.disposition)
selection: "first_match"
after: ["diagnostics.execution.ordinary.cause"]
```

##### Recognized supported stop {recognized: outcome}

```contract
test: present(reply.runner_subprocess.disposition.questions.stop_reason) and reply.runner_subprocess.disposition.questions.stop_reason.state == "supported" and present(reply.runner_subprocess.disposition.questions.stop_reason.answer) and reply.runner_subprocess.disposition.questions.stop_reason.answer in ["sentinel_deadline", "done", "child_reaped", "wait_error", "policy_write_error", "policy_transfer_deadline"]
effects: [set_value(envelope.data.runner_sandbox_diagnostics.stop_reason, reply.runner_subprocess.disposition.questions.stop_reason.answer), set_value(envelope.data.runner_sandbox_diagnostics.disposition_integrity, "valid")]
```

##### No supported recognized stop {absent: outcome}

```contract
test: True
effects: [set_value(envelope.data.runner_sandbox_diagnostics.stop_reason, None), set_value(envelope.data.runner_sandbox_diagnostics.disposition_integrity, "valid")]
```

#### Carried host-cleanup chain {cause_chain: definition}

```contract
defines: "condition"
```

##### Required claims and native request result {facts: condition}

```contract
test: present(reply.runner_subprocess.disposition) and present(reply.runner_subprocess.disposition.questions.final_status) and reply.runner_subprocess.disposition.questions.final_status.state == "supported" and reply.runner_subprocess.disposition.questions.final_status.answer == "signal" and present(reply.runner_subprocess.disposition.questions.final_status.value) and is_variant(reply.runner_subprocess.disposition.questions.final_status.value, "Integer") and present(reply.runner_subprocess.disposition.questions.cleanup_trigger) and reply.runner_subprocess.disposition.questions.cleanup_trigger.state == "supported" and present(reply.runner_subprocess.disposition.questions.grace_end) and reply.runner_subprocess.disposition.questions.grace_end.state == "supported" and reply.runner_subprocess.disposition.questions.grace_end.answer == "exhausted" and present(reply.runner_subprocess.disposition.questions.kill_request_and_result) and reply.runner_subprocess.disposition.questions.kill_request_and_result.state == "supported" and reply.runner_subprocess.disposition.questions.kill_request_and_result.answer == "requested" and present(reply.runner_subprocess.disposition.questions.kill_request_and_result.value) and is_variant(reply.runner_subprocess.disposition.questions.kill_request_and_result.value, "Request") and variant(reply.runner_subprocess.disposition.questions.kill_request_and_result.value, "Request").rc == 0 and variant(reply.runner_subprocess.disposition.questions.kill_request_and_result.value, "Request").signal == variant(reply.runner_subprocess.disposition.questions.final_status.value, "Integer")
```

#### Host-cleanup attribution {cause: acts}

```contract
who: ["identity.definitions.controller"]
where: "validated worker ending projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
requires: ["diagnostics.execution.ordinary.lifecycle_check"]
when: present(reply.runner_subprocess.disposition) and present(reply.runner_subprocess.disposition.questions.final_status) and reply.runner_subprocess.disposition.questions.final_status.state == "supported" and reply.runner_subprocess.disposition.questions.final_status.answer == "signal"
selection: "first_match"
after: ["diagnostics.execution.ordinary.mapping"]
```

##### Deadline expiry {deadline_expiry: outcome}

```contract
test: ref("diagnostics.execution.ordinary.cause_chain.facts") and reply.runner_subprocess.disposition.questions.cleanup_trigger.answer == "deadline_expiry"
effects: set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "host_sentinel_deadline")
```

##### Completion {completion: outcome}

```contract
test: ref("diagnostics.execution.ordinary.cause_chain.facts") and reply.runner_subprocess.disposition.questions.cleanup_trigger.answer == "completion"
effects: set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "host_exit_grace_exhausted")
```

##### Poll wait error {poll_wait_error: outcome}

```contract
test: ref("diagnostics.execution.ordinary.cause_chain.facts") and reply.runner_subprocess.disposition.questions.cleanup_trigger.answer == "poll_wait_error"
effects: set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "host_cleanup_after_wait_error")
```

##### Policy transfer error {policy_transfer_error: outcome}

```contract
test: ref("diagnostics.execution.ordinary.cause_chain.facts") and reply.runner_subprocess.disposition.questions.cleanup_trigger.answer == "policy_transfer_error"
effects: set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "host_cleanup_after_transfer_error")
```

##### Policy transfer timeout {policy_transfer_timeout: outcome}

```contract
test: ref("diagnostics.execution.ordinary.cause_chain.facts") and reply.runner_subprocess.disposition.questions.cleanup_trigger.answer == "policy_transfer_timeout"
effects: set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "host_cleanup_after_transfer_timeout")
```

##### No eligible recognized cleanup cause {unknown: outcome}

```contract
test: True
effects: set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "unknown")
```

The request result, exhausted grace and owned final status are independent
observations in this chain. A successful signal request supplies its own
request result; attribution requires the other carried claims and the
preceding lifecycle validation.

#### Copy validated host conflicts {host_conflicts: reports}

```contract
requires: ["diagnostics.execution.ordinary.lifecycle_check"]
bind.i: reply.runner_subprocess.disposition.issues
bind.j: envelope.data.runner_sandbox_diagnostics.disposition_issues
match.j: j == i
when: present(reply.runner_subprocess.disposition)
after: ["diagnostics.execution.ordinary.stop"]
```

##### Copy cardinality {coverage: condition}

```contract
test: count(envelope.data.runner_sandbox_diagnostics.disposition_issues) == count(reply.runner_subprocess.disposition.issues)
```

##### Copy each conflict's fields {copy: effect}

```contract
on: "always"
each: ["i", "j"]
effects: [set_value(envelope.data.runner_sandbox_diagnostics.disposition_issues[j].kind, reply.runner_subprocess.disposition.issues[i].kind), set_value(envelope.data.runner_sandbox_diagnostics.disposition_issues[j].detail, reply.runner_subprocess.disposition.issues[i].detail), set_value(envelope.data.runner_sandbox_diagnostics.disposition_issues[j].subject_path, None), set_value(envelope.data.runner_sandbox_diagnostics.disposition_issues[j].rule, reply.runner_subprocess.disposition.issues[i].rule), set_value(envelope.data.runner_sandbox_diagnostics.disposition_issues[j].question, reply.runner_subprocess.disposition.issues[i].question), set_value(envelope.data.runner_sandbox_diagnostics.disposition_issues[j].step_index, reply.runner_subprocess.disposition.issues[i].step_index), set_value(envelope.data.runner_sandbox_diagnostics.disposition_issues[j].observations, reply.runner_subprocess.disposition.issues[i].observations)]
```



### Apply reply-wide findings {reply_checks: acts}

```contract
who: ["identity.definitions.controller"]
where: "typed reply relationship checks after worker projections"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics"]
free.condition: One or more applicable reply-wide checks finds an invalid relationship.
effects: [set_value(diagnostics.process_disposition, "withheld"), set_value(diagnostics.termination_cause, "unknown"), set_value(diagnostics.disposition_integrity, "invalid"), retain_records(reply), retain_assessments(diagnostics.actors)]
after: ["diagnostics.execution.project"]
retained_free: {"condition":{"kind":"native_protocol","reason":"The controller uses the reply-wide validation result before appending its findings to the existing top-level issue array."}}
```

The controller appends these findings to top-level `disposition_issues`.
It preserves the actor entries, an ordinary stop reason already derived,
and all host fields including step comparisons and claimed gate outcomes.
Those retained assertions can therefore appear beside the controller's
finding about them.

### Findings beside the completion result {outer_result: definition}

```contract
uses: ["envelope.data.select"]
```

The envelope's result-selection rule governs completion. Individual failed
attempts and controller integrity findings remain visible beside that result.
A reply-wide withheld disposition can therefore accompany an outer successful
result.

### Check families and applicability {families: definition}

```contract
defines: "condition"
uses: ["identity.definitions.reply"]
```

| Check family | Applicability and checked relationship | Finding scope |
| --- | --- | --- |
| Lifecycle claims | Each worker subprocess: required claims, state/basis references, owned final status, cleanup facts, progress association, slot count/order, action identity, lifecycle copies and supported conflicts. | That worker's projection; ordinary projection or one actor entry. |
| Phase and query evidence | Ordinary semantic reply: phase IDs/order, action partition, collection state, validator ownership and raw-record association, protocol violations, comparison vocabulary and the complete `query_first` chain. | Reply-wide. |
| Policy delivery/read evidence | Ordinary semantic reply with a worker policy-read receipt: bounded counts, host expected-count agreement, length-refusal detail and consistency with later worker observations. | Reply-wide. |
| Native operation observations | Ordinary semantic reply: each fresh-read, fresh-write and exec observation's applicable fields and native relationships. | Reply-wide. |
| Actor association | Ordinary semantic actor reply: actor indexes/IDs, launch/subprocess PID, visits, phase owner, event owner and matching transfer source. | Reply-wide. |
| Actor setup, equipment, application, termination and custody | Ordinary semantic reply: execution-form applicability and the actor record relationships defined by those surfaces. | Reply-wide. |
| Reporting-failure form | A reply carrying reporting_failure: degraded outcome/rc/error, origin/diagnostic/original outcome, removed comparisons and the retention-specific record form. | Reply-wide. |

The reporting-failure branch checks its degradation form while retaining the
assembled records. Worker lifecycle projections still run independently,
with their comparison-limitation requirement waived when the comparison
has been removed by degradation. The retained host records remain
available for inspection at their own observation boundaries.

### Closed claim states and open answers {vocabulary: definition}

```contract
defines: "value"
```

Lifecycle claim states are `supported`, `conflicting`, `unresolved` and
`inapplicable`. A supported claim needs an answer and sufficient resolving
basis; unresolved and inapplicable need a reason. A conflicting claim
needs the matching indexed conflict record and native observations.
Another state produces an invalid-claim finding.

Some answers and summaries are open. For example, an unfamiliar
applicability answer or lifecycle summary is retained, while a known
summary is checked against the canonical lifecycle. A supported unfamiliar
final-status answer that passes the other claim checks projects as
`unrecognized`. This differs from an unknown closed claim state, which
withholds the worker projection.

#### Unconfirmed vocabulary {vocabulary_choice: gap}

```contract
kind: "behavior"
```

For ordinary and actor workers, the controller maps both unresolved and inapplicable host final-status claims to unconfirmed while retaining the host claim. Whether to retain that merged controller vocabulary remains a maintainer decision.

### Scope example {scope_example: example}

A typed actor reply can carry a transfer naming an invalid source actor,
while another actor retains a valid clean-exit lifecycle. The controller
then publishes top-level `withheld` and an actor-evidence finding beside
that actor's `clean_exit`. If the admitted host summary is `finished`,
the outer result still reports `ok: true` and exit 0. The three values
answer the reply relationship, individual ending and host completion
questions respectively.

### Controller finding support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"execution_diagnostics"},{"path":"controller/src/porcelain_admission.rs","symbol":"project"},{"path":"controller/src/porcelain_admission.rs","symbol":"validate_lifecycle"},{"path":"controller/src/porcelain_admission.rs","symbol":"admit_reply"},{"path":"controller/src/run_flow.rs","symbol":"reply_contract"},{"path":"controller/src/run_flow.rs","symbol":"complete_execution"},{"path":"controller/src/porcelain_actor.rs","symbol":"pub(super) fn validate"},{"path":"controller/src/porcelain_native.rs","symbol":"pub(super) fn validate"}]
check: [{"path":"controller/src/porcelain_admission.rs","symbol":"typed_invalid_actor_account_keeps_independent_actor_endings","form":"test"},{"path":"controller/src/porcelain_admission.rs","symbol":"typed_degradation_never_certifies_surviving_comparison","form":"test"},{"path":"controller/src/porcelain_admission.rs","symbol":"typed_future_applicability_and_summary_remain_open_without_rewriting","form":"test"},{"path":"controller/src/run_flow.rs","symbol":"malformed_phase_claims_withhold_projection_and_preserve_raw_reply","form":"test"},{"path":"controller/src/run_flow.rs","symbol":"execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields","form":"test"}]
pins: "Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches."
context: "Typed controller implementation and the named constructed tests were read."
limits: "Actor/native family entry points and the complete gate checks were read; their detailed operation predicates have separate source owners. The scope example combines separately inspected projection and outer-result controls."
```

### Reader judgments {reader_evidence: definition}

```contract
uses: ["actor_evidence.actor.reader_scope"]
```

Host reporting validation, controller semantic admission and canonical-JSON
consumption interpret the same typed records at their stated scopes. Worker
lifecycle assessment remains a separate judgment over the retained native
account and its projection. A reporting failure can retain observations that
produce a lifecycle finding while satisfying the degradation form.


#### Corpus support {support: owner}

```contract
grade: "executed"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"execution_diagnostics"},{"path":"tests/lib/consumer.py","symbol":"_validate_reply"},{"path":"tests/lib/lifecycle_oracle.py","symbol":"check_actor_records"}]
check: [{"path":"controller/src/run_flow.rs","symbol":"reader_definition_corpus_cross_readers","form":"test"},{"path":"tests/suites/runner_unit/reader_corpus.py","symbol":"replay","form":"test"}]
pins: "Preparation, identifier, membership, application precedence and degradation cases check their own expected judgments and retained consequences across the actual readers."
context: "Whole canonical runner-unit case passed with zero recorded system sleep. Swift judgments over 142 typed frames were retained before encoding; exact-one Rust replay carried 143 frames including the real writer-cap fallback through envelopes, then independent Python readers completed all rows and seven JSON-only controls."
limits: "The corpus uses constructed records and independently expected interpretations. Eleven application-positive pairs, degradation admission, the exact contradictory-worker D1 finding and retained actor projections have separate assertions. JSON-only normalization has its own domain. Native occurrence of each constructed context has separate observation owners."
run: "20261111T162345Z_3d6c7242"
case: "runner_unit/pwrunner_core_unit_executable"
source_snapshot: "reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)"
```

#### Independent semantic classifiers {classifier_generation: gap}

```contract
kind: "behavior"
```

The host, controller and test readers retain independently written semantic classifiers checked against the stated definitions. Whether to generate those classifiers from one implementation remains a maintainer decision.

## One actor's diagnostics {actor: subject}

```contract
record: "rust.ActorExecutionDiagnostics"
as: "actor_diagnostics"
```

### actor_id {actor_id: field}

The host actor label copied into an actor-form diagnostic entry. The
underlying projection helper begins with null; actor assembly supplies
the label even when that actor has no subprocess record.

### process_disposition {process_disposition: field}

The actor's own worker projection, chosen by the actor-worker mapping below after its
lifecycle checks pass. Local findings yield `withheld`; a missing
subprocess record yields `no_worker`.

### termination_cause {termination_cause: field}

Null for `clean_exit` or `no_worker`, otherwise `unknown` unless the
validated host-cleanup chain supplies a named cause below.

### stop_reason {stop_reason: field}

The actor worker's supported stop reason from the recognized set listed
for execution diagnostics. Null when no supported recognized answer was
projected, including when local lifecycle validation failed.

### disposition_integrity {disposition_integrity: field}

`valid` when this worker's lifecycle checks passed, `invalid` when they
produced a finding, and null when its subprocess record is absent. A
reply-wide finding preserves this actor-local value.

### disposition_issues {disposition_issues: field}

Findings from this actor's lifecycle validation, or copied validated host
conflicts after successful validation. Reply-wide actor-association or
equipment findings appear in the execution-level issue list.

### Actor worker projections {projection: subject}

```contract
who: ["identity.definitions.controller"]
where: "worker projection after response admission"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
bind.a: reply.actors
bind.d: envelope.data.runner_sandbox_diagnostics.actors
match.d: d == a
each: ["a", "d"]
when: reply.execution_form == "actors" and present(reply.actors) and present(reply.actors[a].subprocess)
```

This scope addresses each existing subprocess, including
its degraded reporting form, before later reply-wide findings.

#### Worker lifecycle validation {lifecycle_check: checks}

```contract
who: ["identity.definitions.controller"]
where: "one worker lifecycle validation before projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
free.condition: For reply.actors[a].subprocess and its assigned actions under the carried reporting form, the controller's lifecycle validation returns no failed-check findings, before validated host conflicts are copied.
retained_free: {"condition":{"kind":"native_protocol","reason":"This prerequisite is the lifecycle validator's intermediate return for the selected worker, assigned actions and reporting form. Successful validation permits host conflicts to be copied into the final disposition_issues array."}}
```



##### Local lifecycle findings {local_failure: effect}

```contract
on: "failure"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition, "withheld"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "unknown"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity, "invalid"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason, None)]
```

#### Ending mapping {mapping: reports}

```contract
who: ["identity.definitions.controller"]
where: "validated worker ending projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
requires: ["diagnostics.actor.projection.lifecycle_check"]
when: present(reply.actors[a].subprocess.disposition) and present(reply.actors[a].subprocess.disposition.questions.final_status)
selection: "first_match"
```

##### Clean exit {clean: outcome}

```contract
test: reply.actors[a].subprocess.disposition.questions.final_status.state == "supported" and reply.actors[a].subprocess.disposition.questions.final_status.answer == "exit_code" and present(reply.actors[a].subprocess.disposition.questions.final_status.value) and is_variant(reply.actors[a].subprocess.disposition.questions.final_status.value, "Integer") and variant(reply.actors[a].subprocess.disposition.questions.final_status.value, "Integer") == 0
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition, "clean_exit"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, None)]
```

##### Other exit status {nonzero: outcome}

```contract
test: reply.actors[a].subprocess.disposition.questions.final_status.state == "supported" and reply.actors[a].subprocess.disposition.questions.final_status.answer == "exit_code"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition, "nonzero_exit"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "unknown")]
```

##### Signaled ending {signal: outcome}

```contract
test: reply.actors[a].subprocess.disposition.questions.final_status.state == "supported" and reply.actors[a].subprocess.disposition.questions.final_status.answer == "signal"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition, "signaled"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "unknown")]
```

##### Supported conflict {conflict: outcome}

```contract
test: reply.actors[a].subprocess.disposition.questions.final_status.state == "conflicting"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition, "conflicting"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "unknown")]
```

##### Unresolved or inapplicable ending {unconfirmed: outcome}

```contract
test: reply.actors[a].subprocess.disposition.questions.final_status.state in ["unresolved", "inapplicable"]
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition, "unconfirmed"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "unknown")]
```

##### Other admitted ending {other: outcome}

```contract
test: True
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition, "unrecognized"), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "unknown")]
```

Lifecycle validation
has already checked the integer exit value and supported-conflict evidence.

#### Supported stop reason {stop: reports}

```contract
who: ["identity.definitions.controller"]
where: "validated worker ending projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
requires: ["diagnostics.actor.projection.lifecycle_check"]
when: present(reply.actors[a].subprocess.disposition)
selection: "first_match"
after: ["diagnostics.actor.projection.cause"]
```

##### Recognized supported stop {recognized: outcome}

```contract
test: present(reply.actors[a].subprocess.disposition.questions.stop_reason) and reply.actors[a].subprocess.disposition.questions.stop_reason.state == "supported" and present(reply.actors[a].subprocess.disposition.questions.stop_reason.answer) and reply.actors[a].subprocess.disposition.questions.stop_reason.answer in ["sentinel_deadline", "done", "child_reaped", "wait_error", "policy_write_error", "policy_transfer_deadline"]
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason, reply.actors[a].subprocess.disposition.questions.stop_reason.answer), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity, "valid")]
```

##### No supported recognized stop {absent: outcome}

```contract
test: True
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason, None), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity, "valid")]
```

#### Carried host-cleanup chain {cause_chain: definition}

```contract
defines: "condition"
```

##### Required claims and native request result {facts: condition}

```contract
test: present(reply.actors[a].subprocess.disposition) and present(reply.actors[a].subprocess.disposition.questions.final_status) and reply.actors[a].subprocess.disposition.questions.final_status.state == "supported" and reply.actors[a].subprocess.disposition.questions.final_status.answer == "signal" and present(reply.actors[a].subprocess.disposition.questions.final_status.value) and is_variant(reply.actors[a].subprocess.disposition.questions.final_status.value, "Integer") and present(reply.actors[a].subprocess.disposition.questions.cleanup_trigger) and reply.actors[a].subprocess.disposition.questions.cleanup_trigger.state == "supported" and present(reply.actors[a].subprocess.disposition.questions.grace_end) and reply.actors[a].subprocess.disposition.questions.grace_end.state == "supported" and reply.actors[a].subprocess.disposition.questions.grace_end.answer == "exhausted" and present(reply.actors[a].subprocess.disposition.questions.kill_request_and_result) and reply.actors[a].subprocess.disposition.questions.kill_request_and_result.state == "supported" and reply.actors[a].subprocess.disposition.questions.kill_request_and_result.answer == "requested" and present(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value) and is_variant(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value, "Request") and variant(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value, "Request").rc == 0 and variant(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value, "Request").signal == variant(reply.actors[a].subprocess.disposition.questions.final_status.value, "Integer")
```

#### Host-cleanup attribution {cause: acts}

```contract
who: ["identity.definitions.controller"]
where: "validated worker ending projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
requires: ["diagnostics.actor.projection.lifecycle_check"]
when: present(reply.actors[a].subprocess.disposition) and present(reply.actors[a].subprocess.disposition.questions.final_status) and reply.actors[a].subprocess.disposition.questions.final_status.state == "supported" and reply.actors[a].subprocess.disposition.questions.final_status.answer == "signal"
selection: "first_match"
after: ["diagnostics.actor.projection.mapping"]
```

##### Deadline expiry {deadline_expiry: outcome}

```contract
test: ref("diagnostics.actor.projection.cause_chain.facts") and reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer == "deadline_expiry"
effects: set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "host_sentinel_deadline")
```

##### Completion {completion: outcome}

```contract
test: ref("diagnostics.actor.projection.cause_chain.facts") and reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer == "completion"
effects: set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "host_exit_grace_exhausted")
```

##### Poll wait error {poll_wait_error: outcome}

```contract
test: ref("diagnostics.actor.projection.cause_chain.facts") and reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer == "poll_wait_error"
effects: set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "host_cleanup_after_wait_error")
```

##### Policy transfer error {policy_transfer_error: outcome}

```contract
test: ref("diagnostics.actor.projection.cause_chain.facts") and reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer == "policy_transfer_error"
effects: set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "host_cleanup_after_transfer_error")
```

##### Policy transfer timeout {policy_transfer_timeout: outcome}

```contract
test: ref("diagnostics.actor.projection.cause_chain.facts") and reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer == "policy_transfer_timeout"
effects: set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "host_cleanup_after_transfer_timeout")
```

##### No eligible recognized cleanup cause {unknown: outcome}

```contract
test: True
effects: set_value(envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause, "unknown")
```

The request result, exhausted grace and owned final status are independent
observations in this chain. A successful signal request supplies its own
request result; attribution requires the other carried claims and the
preceding lifecycle validation.

#### Copy validated host conflicts {host_conflicts: reports}

```contract
requires: ["diagnostics.actor.projection.lifecycle_check"]
bind.i: reply.actors[a].subprocess.disposition.issues
bind.j: envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues
match.j: j == i
when: present(reply.actors[a].subprocess.disposition)
after: ["diagnostics.actor.projection.stop"]
```

##### Copy cardinality {coverage: condition}

```contract
test: count(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues) == count(reply.actors[a].subprocess.disposition.issues)
```

##### Copy each conflict's fields {copy: effect}

```contract
on: "always"
each: ["i", "j"]
effects: [set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].kind, reply.actors[a].subprocess.disposition.issues[i].kind), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].detail, reply.actors[a].subprocess.disposition.issues[i].detail), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].subject_path, None), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].rule, reply.actors[a].subprocess.disposition.issues[i].rule), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].question, reply.actors[a].subprocess.disposition.issues[i].question), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].step_index, reply.actors[a].subprocess.disposition.issues[i].step_index), set_value(envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].observations, reply.actors[a].subprocess.disposition.issues[i].observations)]
```



### Actor projection support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"project"},{"path":"controller/src/porcelain_admission.rs","symbol":"validate_lifecycle"},{"path":"controller/src/porcelain_admission.rs","symbol":"check_claim"}]
check: [{"path":"controller/src/porcelain_admission.rs","symbol":"typed_host_cleanup_cause_requires_all_independent_observations","form":"test"},{"path":"controller/src/porcelain_admission.rs","symbol":"typed_invalid_actor_account_keeps_independent_actor_endings","form":"test"}]
pins: "The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain."
context: "Full projection and lifecycle validation read; constructed cleanup and scope controls read."
limits: "The read cleanup test covers completion, deadline, wait-error and future-trigger cases. Transfer-error and transfer-timeout causes were read in source; no execution is credited."
```

## Integrity finding {issue: subject}

```contract
record: "rust.IntegrityIssue"
as: "integrity_issue"
```

### kind {kind: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["missing_record", "malformed_record", "invalid_claim", "unresolved_reference", "phase_collection", "ordering", "policy_read", "fresh_read", "fresh_write", "exec_observation", "actor_evidence", "reporting_failure", "conflict"]
unknown: "An unfamiliar category remains a finding with its carried detail and scope; interpreting its specific condition requires that producer's definition."
```

Category supplied by the controller check or copied from a host conflict.


### detail {detail: field}

Human-readable explanation of the failed relationship or copied host
conflict. Some controller details embed a step label or position; other
actor and gate findings carry a general explanation.

### subject_path {subject_path: field}

Optional location of the inspected assertion within `data.runner_result`.
The path is an ordered list of object keys and canonical zero-based decimal
array positions. An empty path names the whole host result; a present null
value remains an addressable target. For example,
`["phases","2","termination_gate"]` names the third phase's carried gate,
even when phase labels are duplicated or invalid.
The controller supplies this field for owned-reap, phase-activation and
termination-gate findings. Its association identifies the inspected record;
projection and retention effects follow the producing check's scope.
Other controller findings and copied host conflicts omit this field.

### rule {rule: field}

Host conflict rule copied from the retained disposition issue, such as
D1 for a final-status conflict or D5 for the supported step conflicts.
Controller-created findings currently omit this field.

### question {question: field}

Host question associated with a copied conflict. Controller-created
findings currently omit this field even when a detail names the question.

### step_index {step_index: field}

Worker-local step index copied from a host conflict when it has step
scope. A copied run-level conflict and controller-created findings omit it.

### observations {observations: field}

Host observation-reference list copied from a validated conflict.
Controller-created findings currently omit this field.

### Retain observation and finding separately {retain: acts}

```contract
who: ["identity.definitions.controller"]
where: "integrity finding construction"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
effects: retain_records(reply)
free.effect: Construct controller findings from the failed check's kind and detail, attaching subject_path for the owned-reap, phase-activation and termination-gate checks. Publish each finding and copied validated host conflict at its producing validation scope and in the producing order.
retained_free: {"effect":{"kind":"native_protocol","reason":"The native validation procedure constructs findings, formats collection positions as decimal strings in subject paths, and appends records at the producing scope in order. Copied conflict field values and host-reply retention are structured separately."}}
```

### Finding association and effect {subject: definition}

```contract
uses: ["diagnostics.issue.subject_path", "diagnostics.execution.reply_checks", "diagnostics.execution.project"]
```

A subject path associates the finding with the retained assertion that its
check inspected. A gate's source and dependent records remain operands of
that check. Reply-wide findings withhold the aggregate projection and retain
the separately computed actor projections. Worker-local findings affect
that worker's projection.

#### Reply-wide withholding scope {withholding_scope: gap}

```contract
kind: "behavior"
```

A reply-wide finding withholds the aggregate projection and retains separately computed actor projections. Whether that finding should also withhold the actor conclusions remains a maintainer decision.

#### Executed gate finding locations {gate_execution: owner}

```contract
grade: "executed"
source: {"path":"controller/src/porcelain_actor.rs","symbol":"fn gates"}
check: {"path":"controller/src/porcelain_actor.rs","symbol":"gate_findings_locate_each_retained_assertion_by_position","form":"test"}
pins: "The constructed check retains both equal-label gates by positions 2 and 6, then checks owned-reap, activation and dependent-gate subjects with exact finding details/order and unchanged input records."
context: "The named control passed in the completed zero-sleep unit/rust.unit case; its assertions inspect the findings returned by the production gate checker."
limits: "Execution covers the constructed owned-reap, activation and selected gate cases. Remaining predicate-location assignments retain their source support. Reference resolution and action-wide withholding choices have separate owners."
run: "20261111T155411Z_29ef0802"
case: "unit/rust.unit"
source_snapshot: "reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)"
```

#### Executed reference-form controls {reference_execution: owner}

```contract
grade: "executed"
source: [{"path":"tests/lib/consumer.py","symbol":"_subject_path_problem"},{"path":"tests/lib/consumer.py","symbol":"_validate_diagnostic_subjects"}]
check: {"path":"tests/suites/blackbox_e2e/checker_controls.py","symbol":"diagnostic_subject_controls","form":"test"}
pins: "Forty-two retained controls cover optional/root/object/scalar/null targets, canonical array positions, malformed or unresolved paths, aggregate and actor issue locations, version gating and accumulated independent faults; 12 accept and 30 refuse."
context: "The completed blackbox_e2e/checker_controls case passed with zero recorded system sleep. Each constructed input and its exact findings remain in consumer_subject_*.json and *.errors.json."
limits: "These controls establish reference reading and unchanged carried documents. Product predicate-to-subject selection is checked by the gate and full-reply corpus owners; reserved withholding policy remains explicit."
run: "20261111T155411Z_29ef0802"
case: "blackbox_e2e/checker_controls"
source_snapshot: "reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)"
```

### Finding construction support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"IntegrityIssue"},{"path":"controller/src/porcelain_admission.rs","symbol":"fn issue"},{"path":"controller/src/porcelain_admission.rs","symbol":"for i in &sub.disposition"},{"path":"controller/src/porcelain_actor.rs","symbol":"fn require"},{"path":"controller/src/porcelain_actor.rs","symbol":"fn gates"},{"path":"controller/src/porcelain_native.rs","symbol":"pub(super) fn validate"}]
pins: "Gate-family findings carry locations in the retained reply while preserving existing predicates, detail, order and projection scope. Copied host issues preserve their own metadata."
context: "Constructors, projection copy, actor gate checks and native validator dispatch read."
limits: "Locations identify inspected retained records. Existing worker-local and reply-wide projection rules govern the findings independently."
```

# Actor and phase evidence {actor_evidence: surface}

```contract
syntax: 1
artifact: "Actor and phase evidence"
part: "report"
goldens: ["tests/fixtures/contract/surfaces/actor_evidence.json"]
checks: ["runner_unit"]
```

## Actor process account {actor: subject}

```contract
record: "PWRunnerActorResult"
as: "ae_actor"
```

The host emits actors in request order. Each actor owns its launch, worker publications, policy receipt, equipment read-back and lifecycle account.

### actor_id {actor_id: field}

Submitted actor identifier that binds this row to its phases and resources.
Ordinary semantic replies require nonempty, NUL-free actor identifiers within
their admitted UTF-8 capacity, distinct identifiers and request order.

### index {index: field}

Zero-based position in the admitted actor list.

### mode {mode: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["apply", "unapplied"]
```

Submitted sandbox mode, apply or unapplied.

### policy_format {policy_format: field}

Selected policy representation for an apply actor, when provided.

### policy_sha256 {policy_sha256: field}

Host SHA-256 of the selected submitted source bytes after controller augmentation.

### policy_received_sha256 {policy_received_sha256: field}

Worker SHA-256 of the bytes it actually read before compilation, when published.

### setup_status {setup_status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["not_launched", "launch_refused", "transfer_failed", "applied", "unapplied_declared", "setup_failed", "authority_setup_failed", "exited_before_setup", "setup_timeout"]
```

Host setup classification: not_launched, launch_refused, transfer_failed, applied, unapplied_declared, setup_failed, authority_setup_failed, exited_before_setup or setup_timeout.

### applied {applied: field}

Acquired worker applied flag for apply mode when output exists; absent for an unapplied declaration or unavailable output.

### application_count {application_count: field}

Zero or one from the final acquired applied publication, retained even when a setup deadline already ended eligibility.

### launch {launch: field}

Host-arranged launch context once this actor process was spawned.

### subprocess {subprocess: field}

This actor's worker lifecycle and publication account.

### compiled_profile {compiled_profile: field}

Receipt from this actor's requested compiled-profile capture, when the host has a capture result.

### visits {visits: field}

In an ordinary semantic reply, the exact ordered list of one-based global
phase ordinals declared for this actor, including visits whose activation
never occurred. Membership comes from each phase's declared owner.

### equipment {equipment: field}

Requested and resolved worker role, entitlement requirement assessment and live execution observation.

### application {application: field}

Host application-boundary assessment with its evidence basis.

### owned_reap {owned_reap: field}

Host-owned waitpid ending retained for this actor and referenced by dependent termination gates.

### Actor ownership and reporting scope {account: reports}

```contract
when: present(request.actors)
who: ["identity.definitions.host"]
where: "actor reply assembly"
entry: ["xpc_execute"]
recipient: ["xpc_caller", "runner_client", "controller"]
report: ["runner_reply"]
free.condition: Assemble each actor's row from its declaration, launch/driver output and its own shared publications; phases retain their declared actor and action ownership.
free.effect: Retain the actor-indexed account and separately report schedule observations. In an ordinary executed reply, each declared action has its ordered step or extension-event record even when execution evidence is unresolved. Preparation refusals and retained reporting failures carry the distinct contents stated below.
retained_free: {"condition":{"kind":"native_protocol","reason":"Actor assembly binds declarations to actual launch, setup and phase outputs before reporting missing or unresolved observations."},"effect":{"kind":"native_protocol","reason":"Assembly consumes the internal ActorScheduleOutcome, query plans and validator results to construct ordered actor, step and extension-event tables. These intermediate records and the preparation or reporting form determine the native assembly procedure."}}
```

A preparation refusal retains declarations and preparation observations while
its execution tables remain empty. A retained reporting-failure reply carries
the assembled observations and the reporting conflict, with comparison claims
removed. Its applicable guarantee is the degraded report's form: retained
actor, phase and resource associations remain available for inspection as
assembled. Ordinary consistency assessments apply on the ordinary reply path.

### Reader applicability {reader_scope: definition}

```contract
defines: "condition"
uses: ["diagnostics.execution.families", "reply.failure.publish"]
```

The host self-check, controller semantic reader and general canonical-JSON
consumer check ordinary actor relationships when `reporting_failure` is
absent. A preparation refusal belongs to the actor execution form and retains
its admitted declarations: actor order, IDs and visits, phase order and owner,
actor visit numbers and action IDs. It carries no launch, arrival, completion,
proceed publication, step, extension-event, transfer or resource entry. Each
actor has zero successful applications. Its host authority scope is
`not_attempted`, with empty region and custody tables. The actor event table
is present, including when empty.

Phase and actor identifiers are nonempty and NUL-free within their admitted
UTF-8 capacities. Action identifiers use that same capacity and NUL rule;
ordinary-form actions admit an empty identifier, while actor-form actions require a
nonempty one. Declaration uniqueness and exact schedule membership apply
separately from that string grammar.

A reporting-failure reply is checked for its degradation form and applicable
compiled-profile context. Host validation, controller admission and the general consumer apply that
scope. The actor/extension readers check ordinary semantic relationships when
the reporting-failure record is absent. The lifecycle receipt reader separately checks each
retained worker's claims and controller projection; findings from that
assessment describe the retained worker evidence.

#### Reader definition support {support: owner}

```contract
grade: "executed"
source: [{"path":"runner/Sources/PWRunnerCore/ActorOrchestration.swift","symbol":"actorPreparationRefusal"},{"path":"runner/Sources/PWRunnerCore/ActorPlan.swift","symbol":"normalizeActorPlan"},{"path":"runner/Sources/PWRunnerCore/PWRunnerReply.swift","symbol":"actorExtensionEvidenceProblem"},{"path":"runner/Sources/PWRunnerCore/PWRunnerReply.swift","symbol":"validateForReporting"},{"path":"controller/src/porcelain_admission.rs","symbol":"admission_problem"},{"path":"controller/src/porcelain_actor.rs","symbol":"preparation_failure_valid"},{"path":"tests/lib/consumer.py","symbol":"_validate_reply"},{"path":"tests/lib/lifecycle_oracle.py","symbol":"check_actor_records"}]
check: [{"path":"runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift","symbol":"runReaderCorpusTests","form":"test"},{"path":"controller/src/run_flow.rs","symbol":"reader_definition_corpus_cross_readers","form":"test"}]
pins: "Constructed typed preparation, declaration and degradation neighbours retain separate host, controller, general-consumer and worker-lifecycle judgments."
context: "Whole canonical runner-unit case passed with zero recorded system sleep. Swift judgments over 142 typed frames were retained before encoding; exact-one Rust replay carried 143 frames including the real writer-cap fallback through envelopes, then independent Python readers completed all rows and seven JSON-only controls."
limits: "The corpus uses constructed records and independently expected interpretations. Eleven application-positive pairs, degradation admission, the exact contradictory-worker D1 finding and retained actor projections have separate assertions. JSON-only normalization has its own domain. Native occurrence of each constructed context has separate observation owners."
run: "20261111T162345Z_3d6c7242"
case: "runner_unit/pwrunner_core_unit_executable"
source_snapshot: "reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)"
```

## Actor launch context {launch: subject}

```contract
record: "PWRunnerActorLaunch"
as: "ae_launch"
```

The host starts each actor as a fresh process with explicit standard streams and descriptor inheritance.

### pid {pid: field}

PID obtained from this actor's successful spawn.

### parent_pid {parent_pid: field}

PID of the runner host that spawned the actor.

### environment {environment: field}

empty: the host supplies an empty environment to the actor process.

### standard_streams {standard_streams: field}

stdin_policy_pipe_stdout_stderr_null_device: stdin carries policy bytes, while stdout and stderr are attached to the null device.

### inherited_descriptors {inherited_descriptors: field}

Explicit inherited descriptor numbers: 0 policy input, 3 shared evidence, 4 readiness, and 5 only when an authority region is mapped for the actor.

## Application assessment {application: subject}

```contract
record: "PWRunnerActorApplication"
as: "ae_application"
```



### state {state: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["not_requested", "not_attempted", "observed", "unobserved"]
```

not_requested, not_attempted, observed or unobserved. observed identifies evidence of the apply boundary, including a native apply failure; unobserved retains an unresolved result.

### basis {basis: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["unapplied_declaration", "worker_not_launched", "applied_publication", "terminal_authority_setup_refusal", "apply_failure_publication", "terminal_input_refusal", "terminal_parameter_refusal", "terminal_compile_refusal", "terminal_timing_refusal", "apply_call_boundary_without_result", "no_eligible_apply_publication"]
```

The specific declaration, launch state or worker/authority publication supporting state. The eleven permitted state/basis pairs are defined by the application rule below.

### Associated authority rows {authority_association: reports}

```contract
who: ["identity.definitions.host"]
where: "actor reply assembly"
entry: ["xpc_execute"]
recipient: ["xpc_caller", "runner_client", "controller"]
report: ["runner_reply"]
bind.a: reply.actors
bind.w: reply.authority_setup.workers
match.w: w == a and present(reply.authority_setup.workers[w].actor_index) and reply.authority_setup.workers[w].actor_index == a and present(reply.authority_setup.workers[w].actor_id) and reply.authority_setup.workers[w].actor_id == reply.actors[a].actor_id
each: ["a"]
when: present(request.actors) and present(reply.actors) and reply.execution_form == "actors" and absent(reply.reporting_failure)
```

#### One associated entry for each actor {entry: condition}

```contract
test: present(reply.authority_setup) and count(reply.authority_setup.workers) == count(reply.actors) and matches(w) == 1
```



### Application classification {classify: reports}

```contract
who: ["identity.definitions.host"]
where: "actor reply assembly"
entry: ["xpc_execute"]
recipient: ["xpc_caller", "runner_client", "controller"]
report: ["runner_reply"]
selection: "first_match"
bind.a: reply.actors
bind.t: reply.authority_setup.workers
match.t: t == a and present(reply.authority_setup.workers[t].publication) and reply.authority_setup.workers[t].publication == "observed" and present(reply.authority_setup.workers[t].disposition) and reply.authority_setup.workers[t].disposition == "terminal_required_failure" and absent(reply.authority_setup.workers[t].integrity_errors)
each: ["a"]
when: present(request.actors) and present(reply.actors) and reply.execution_form == "actors" and absent(reply.reporting_failure)
```


Preparation refusals classify their
unlaunched rows through the first two branches. An unavailable native
authority observation is reported as an entry with publication `not_observed`.

These are the host's production assignments. Recipient checks separately
validate the carried associations, permitted state/basis pairs and source
precedence. A reporting-failure reply retains the earlier assessment under
its own reporting scope.

#### Unapplied declaration {unapplied: outcome}

```contract
test: reply.actors[a].mode == "unapplied"
effects: [set_value(reply.actors[a].application.state, "not_requested"), set_value(reply.actors[a].application.basis, "unapplied_declaration")]
```



#### Worker absent {unlaunched: outcome}

```contract
test: absent(reply.actors[a].launch)
effects: [set_value(reply.actors[a].application.state, "not_attempted"), set_value(reply.actors[a].application.basis, "worker_not_launched")]
```



#### Applied flag {applied: outcome}

```contract
test: present(reply.actors[a].applied) and reply.actors[a].applied == True
effects: [set_value(reply.actors[a].application.state, "observed"), set_value(reply.actors[a].application.basis, "applied_publication")]
```



#### Authority refusal {authority: outcome}

```contract
test: present(reply.authority_setup) and matches(t) == 1
effects: [set_value(reply.actors[a].application.state, "not_attempted"), set_value(reply.actors[a].application.basis, "terminal_authority_setup_refusal")]
```



#### Native apply failure {apply_failure: outcome}

```contract
test: present(reply.actors[a].subprocess) and present(reply.actors[a].subprocess.worker_evidence) and reply.actors[a].subprocess.worker_evidence.failure_state == "published" and present(reply.actors[a].subprocess.worker_evidence.failure) and reply.actors[a].subprocess.worker_evidence.failure.operation == 8 and reply.actors[a].subprocess.worker_evidence.failure.code == 1 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 1 and present(reply.actors[a].subprocess.worker_evidence.failure.native_result) and reply.actors[a].subprocess.worker_evidence.failure.native_result != 0
effects: [set_value(reply.actors[a].application.state, "observed"), set_value(reply.actors[a].application.basis, "apply_failure_publication")]
```



#### Input refusal {input: outcome}

```contract
test: present(reply.actors[a].subprocess) and present(reply.actors[a].subprocess.worker_evidence) and reply.actors[a].subprocess.worker_evidence.failure_state == "published" and present(reply.actors[a].subprocess.worker_evidence.failure) and ((reply.actors[a].subprocess.worker_evidence.failure.operation == 1 and reply.actors[a].subprocess.worker_evidence.failure.code in [4, 7, 10, 12] and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 0) or (reply.actors[a].subprocess.worker_evidence.failure.operation == 2 and reply.actors[a].subprocess.worker_evidence.failure.code in [2, 3, 9, 13]))
effects: [set_value(reply.actors[a].application.state, "not_attempted"), set_value(reply.actors[a].application.basis, "terminal_input_refusal")]
```



#### Parameter refusal {parameter: outcome}

```contract
test: present(reply.actors[a].subprocess) and present(reply.actors[a].subprocess.worker_evidence) and reply.actors[a].subprocess.worker_evidence.failure_state == "published" and present(reply.actors[a].subprocess.worker_evidence.failure) and ((reply.actors[a].subprocess.worker_evidence.failure.operation == 1 and reply.actors[a].subprocess.worker_evidence.failure.code == 5 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 0) or (reply.actors[a].subprocess.worker_evidence.failure.operation == 3 and reply.actors[a].subprocess.worker_evidence.failure.code == 1 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 2) or (reply.actors[a].subprocess.worker_evidence.failure.operation == 4 and ((reply.actors[a].subprocess.worker_evidence.failure.code == 1 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 1) or (reply.actors[a].subprocess.worker_evidence.failure.code == 6 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 0))))
effects: [set_value(reply.actors[a].application.state, "not_attempted"), set_value(reply.actors[a].application.basis, "terminal_parameter_refusal")]
```



#### Compile refusal {compile: outcome}

```contract
test: present(reply.actors[a].subprocess) and present(reply.actors[a].subprocess.worker_evidence) and reply.actors[a].subprocess.worker_evidence.failure_state == "published" and present(reply.actors[a].subprocess.worker_evidence.failure) and reply.actors[a].subprocess.worker_evidence.failure.operation == 5 and reply.actors[a].subprocess.worker_evidence.failure.code == 1 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 2
effects: [set_value(reply.actors[a].application.state, "not_attempted"), set_value(reply.actors[a].application.basis, "terminal_compile_refusal")]
```



#### Timing refusal {timing: outcome}

```contract
test: present(reply.actors[a].subprocess) and present(reply.actors[a].subprocess.worker_evidence) and reply.actors[a].subprocess.worker_evidence.failure_state == "published" and present(reply.actors[a].subprocess.worker_evidence.failure) and reply.actors[a].subprocess.worker_evidence.failure.operation == 12 and ((reply.actors[a].subprocess.worker_evidence.failure.code == 1 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 1) or (reply.actors[a].subprocess.worker_evidence.failure.code == 14 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 0) or (reply.actors[a].subprocess.worker_evidence.failure.code == 15 and reply.actors[a].subprocess.worker_evidence.failure.detail == 1 and reply.actors[a].subprocess.worker_evidence.failure.native_kind == 0))
effects: [set_value(reply.actors[a].application.state, "not_attempted"), set_value(reply.actors[a].application.basis, "terminal_timing_refusal")]
```



#### Apply boundary without result {boundary: outcome}

```contract
test: present(reply.actors[a].subprocess) and present(reply.actors[a].subprocess.worker_evidence) and present(reply.actors[a].subprocess.worker_evidence.progress) and reply.actors[a].subprocess.worker_evidence.progress.operation == 8 and reply.actors[a].subprocess.worker_evidence.progress.stage in [1, 2]
effects: [set_value(reply.actors[a].application.state, "unobserved"), set_value(reply.actors[a].application.basis, "apply_call_boundary_without_result")]
```



#### Remaining evidence {remaining: outcome}

```contract
test: True
effects: [set_value(reply.actors[a].application.state, "unobserved"), set_value(reply.actors[a].application.basis, "no_eligible_apply_publication")]
```



### Setup deadline and later application {late_application: definition}

```contract
defines: "value"
```

Final collection preserves a later applied publication and derives application_count from it after setup eligibility has ended. A setup_timeout can therefore coexist with applied true, count 1 and application state observed with basis applied_publication. The affected actor remains ineligible for phase activation and query collection.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorScheduler.swift","symbol":"ActorScheduler"}
pins: "Final collection retains application independently of earlier setup eligibility."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift","symbol":"runActorSchedulerTests","form":"test"},{"path":"runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift","symbol":"runActorReplyTests","form":"test"}]
limits: "The read controls use 40 ms setup, 150 ms pre-ready delay and 1000 ms grace, then retain the production reply. Their timing observation is bounded to that schedule."
```

## Phase collection and execution {phase: subject}

```contract
record: "PWRunnerPhaseResult"
as: "ae_phase"
```

The host reports phases in declared schedule order. Observation fields record activation's consequences separately from the declared phase and action identities.

### phase_id {phase_id: field}

Submitted phase identifier used by its action records and validator collection.
Ordinary semantic replies require a nonempty, NUL-free identifier within its
admitted UTF-8 capacity. The declared phase order determines its ordinal.

### ordinal {ordinal: field}

One-based position in the global phase schedule.

### action_ids {action_ids: field}

Declared action identifiers in phase order, retained even when actions produce no execution observations.

### arrival_observed {arrival_observed: field}

Whether the host acquired the active worker's arrival publication for this visit.

### completion_observed {completion_observed: field}

Whether the host acquired completion for this visit.

### collection_status {collection_status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["collected", "not_needed", "budget_exhausted", "clock_unavailable", "not_reached"]
```

collected, not_needed, budget_exhausted, clock_unavailable or not_reached. collected identifies an invoked collection even when validator I/O or decoding later fails.

### ordering {ordering: field}

Collection/release order observations for this phase, including host proceed store and worker acknowledgement.

### validator_subprocess {validator_subprocess: field}

Child-process and accepted-verdict account for this phase's validator collection.

### validator_spawn_failure {validator_spawn_failure: field}

Native validator spawn failure before a validator child existed.

### actor_id {actor_id: field}

Actor owning this phase in actor form; absent for the single-worker form.

### actor_visit {actor_visit: field}

One-based visit number within this actor's declared visits, distinct from global ordinal.

### visit_timing {visit_timing: field}

Host-measured intervals for reached visit boundaries; missing intervals retain unavailable clock/boundary observations.

### termination_gate {termination_gate: field}

Dependency observation for a phase declaring after_termination, including gates left not_reached.

### activation_observation {activation_observation: field}

Host release-store observation which activates this phase, with its actor-local capture ordinal and optional time.

## Host activation observation {activation: subject}

```contract
record: "PWRunnerActorActivation"
as: "ae_activation"
```



### capture_ordinal {capture_ordinal: field}

Positive sequence position of this host activation store among observations of the same child.

### observed_ns {observed_ns: field}

Host monotonic time in nanoseconds after the store, when the clock supplied it.

## Visit intervals {timing: subject}

```contract
record: "PWRunnerVisitTiming"
as: "ae_timing"
```

Each interval measures two host observations in milliseconds; an unavailable or backward clock leaves that interval absent.

### activation_to_arrival_ms {activation_to_arrival_ms: field}

Time between the host activation store and acquired worker arrival.

### collection_ms {collection_ms: field}

Time spent in the phase's synchronous query-collection hook.

### arrival_to_release_ms {arrival_to_release_ms: field}

Time from observed arrival to the host proceed release store.

### release_to_completion_ms {release_to_completion_ms: field}

Time from the release store to acquired worker completion.

## Schedule account {schedule: subject}

```contract
record: "PWRunnerScheduleRecord"
as: "ae_schedule"
```



### setup_wait {setup_wait: field}

Measured shared setup wait for the actor set.

### execution_wait {execution_wait: field}

Measured schedule traversal wait, with collection excluded when separately budgeted.

### lifetime_budget_ms {lifetime_budget_ms: field}

Overall actor-run lifetime allowance, <!-- span limits.actor_lifetime_cutoff.value_unit -->180,000 milliseconds<!-- /span --> in the production plan.

### collection_budget_ms {collection_budget_ms: field}

Recorded production maximum for aggregate query collection across actor phases: <!-- span limits.actor_collection_allowance.value_unit -->30,000 milliseconds<!-- /span -->. The host reports this maximum even when `_test_overrides.validator_total_timeout_ms` reduces the allowance used for collection.

### cancelled {cancelled: field}

Recorded schedule cancellation reason, such as preparation_refused, execution_allowance_exhausted, an equipment failure or termination_dependency followed by its outcome; absent when no cancellation was recorded.

## Termination dependency {gate: subject}

```contract
record: "PWRunnerTerminationGate"
as: "ae_gate"
```

The gate belongs to the dependent phase and observes the named source actor after that source’s final scheduled visit was activated.

### source_actor_id {source_actor_id: field}

Different actor named by the dependent phase's after_termination declaration.

### source_final_phase_id {source_final_phase_id: field}

Source actor's last declared phase, which must precede the dependent phase in the global schedule.

### condition {condition: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["terminated"]
```

terminated, the supported dependency condition.

### outcome {outcome: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["not_reached", "satisfied", "timed_out", "ownership_lost", "clock_unavailable", "source_unavailable", "source_departure_requested", "execution_allowance_exhausted"]
```

not_reached, satisfied, timed_out, ownership_lost, clock_unavailable, source_unavailable, source_departure_requested or execution_allowance_exhausted; each is defined by the gate rule below.

### wait {wait: field}

Host dependency wait, with budget capped at <!-- span limits.actor_termination_wait.value_unit -->5,000 milliseconds<!-- /span --> and charged to remaining execution allowance. Absent for not_reached.

### observation {observation: field}

Reference to the source actor's owned ending captured by the evaluated gate, when available; a late ending can remain beside a failed gate.

### activation_eligible {activation_eligible: field}

True exactly for a satisfied gate, allowing this dependent phase to proceed to activation.

### capture_ordinal {capture_ordinal: field}

Capture of the gate result in the source child's host-observation sequence; absent for not_reached and when no source session supplies a sequence.

### Prepared actor phase and gate records {prepared_association: reports}

```contract
who: ["identity.definitions.host"]
where: "prepared actor reply assembly"
entry: ["xpc_execute"]
recipient: ["xpc_caller", "runner_client", "controller"]
report: ["runner_reply"]
when: present(request.actors) and reply.execution_form == "actors" and absent(reply.preparation_failure) and absent(reply.reporting_failure)
bind.q: request.phases
bind.p: reply.phases
match.p: p == q
```

#### Phase cardinality {cardinality: condition}

```contract
test: present(request.phases) and count(reply.phases) == count(request.phases)
```

#### Each phase and declared gate {rows: condition}

```contract
each: ["q", "p"]
test: reply.phases[p].phase_id == request.phases[q].phase_id and reply.phases[p].ordinal == q + 1 and reply.phases[p].actor_id == request.phases[q].actor_id and implies(present(request.phases[q].after_termination), present(reply.phases[p].termination_gate) and reply.phases[p].termination_gate.source_actor_id == request.phases[q].after_termination.actor_id) and implies(absent(request.phases[q].after_termination), absent(reply.phases[p].termination_gate))
```

The scheduler
installs every declared gate before cancellation, allowance and dependent
availability checks, then assembly copies that gate into the phase row.
Its source final phase
comes from the source actor's last preceding phase in the normalized plan.
Preparation refusals carry their separate before-launch phase account.

### Evaluating and applying the dependency {evaluate: acts}

```contract
who: ["identity.definitions.host"]
where: "serial actor schedule before dependent activation"
entry: ["xpc_execute"]
recipient: ["xpc_caller", "runner_client", "controller"]
report: ["runner_reply"]
bind.q: request.phases
bind.p: reply.phases
match.p: p == q
each: ["q", "p"]
when: present(request.actors) and present(request.phases) and present(request.phases[q].after_termination) and reply.execution_form == "actors" and absent(reply.preparation_failure) and absent(reply.reporting_failure)
requires: ["actor_evidence.gate.prepared_association.cardinality", "actor_evidence.gate.prepared_association.rows"]
free.condition: Evaluate only after the schedule remains uncancelled, its allowance is positive, and the dependent actor session, usable setup, unstopped state and visit are available. Evaluation first checks the source session and final declared phase activation; unavailable source evidence gives source_unavailable.
free.effect: A failed evaluated gate prevents dependent activation, collection and release, and cancels every later scheduled phase regardless of its actor. Cleanup and final collection continue for launched actors.
retained_free: {"condition":{"kind":"native_protocol","reason":"The scheduler consults live cancellation, remaining allowance and dependent-session/setup/visit state before invocation. Evaluation consults the source session and prior final-activation observation."},"effect":{"kind":"native_protocol","reason":"The native cancellation and cleanup procedure acts on the live schedule and owned sessions and formats the cancelled string from its prefix and gate outcome. The activation_eligible assignment is structured below."}}
```

The dependency wait observes the owned source child without requesting its
departure. Its budget is the lesser of <!-- span limits.actor_termination_wait.value_unit -->5,000 milliseconds<!-- /span --> and the remaining
execution allowance in whole milliseconds. Deadline samples and final elapsed
accounting govern satisfaction. These are charged-wait conditions; operating
system scheduling determines when the host next runs.

A failed evaluated gate sets `schedule.cancelled` to
`termination_dependency:<outcome>`. Later phases retain their declarations
with collection `not_reached`, false arrival/completion and absent activation
and visit timing. Their own gates remain `not_reached`. Final cleanup may add
the source's later owned ending while the failed gate keeps the observation
reference captured during its evaluation.

#### Eligibility assigned by evaluation {eligibility_assignment: effect}

```contract
on: "always"
effects: set_value(reply.phases[p].termination_gate.activation_eligible, reply.phases[p].termination_gate.outcome == "satisfied")
```



#### Satisfied {satisfied: outcome}

```contract
value: "satisfied"
free.condition: The source final activation precedes a natural owned reap in its child sequence; both timestamps exist and activation time is at most reap time. Ownership is unbroken, departure_requested is false, budget is positive, deadline samples permit the reap, and final wait has a valid elapsed interval at most budget.
retained_free: {"condition":{"kind":"native_protocol","reason":"Owned reap eligibility includes intermediate deadline samples and final wait observations, beyond the carried ordinal/timestamp comparisons."}}
```

The gate closes after the source's owned ending. A normal exit or signaled
ending can qualify; natural means the host had not requested departure.
Source final-phase completion is a separate observation from activation and
owned termination.

#### Unreached {not_reached: outcome}

```contract
value: "not_reached"
```

Cancellation, exhausted schedule allowance or an unavailable dependent actor
or visit stopped traversal before this gate was evaluated. Its wait,
observation and capture ordinal are absent and eligibility is false. An
unavailable dependent actor can leave this gate unreached while later
otherwise eligible phases remain schedulable.

#### Source unavailable {source_unavailable: outcome}

```contract
value: "source_unavailable"
```

The source session, final activation, or required activation-before-ending
order was unavailable.

#### No remaining gate allowance {execution_allowance_exhausted: outcome}

```contract
value: "execution_allowance_exhausted"
```

Evaluation began with no positive whole-millisecond gate budget.

#### Timing unavailable {clock_unavailable: outcome}

```contract
value: "clock_unavailable"
```

A deadline sample, required activation/reap time or final elapsed accounting
was unavailable or moved backward. Retained fields provide the available
context for this timing failure.

#### Gate timeout {timed_out: outcome}

```contract
value: "timed_out"
```

The deadline or wait expired, including after a reap, or final elapsed time
exceeded budget. A retained reap reference establishes that capture while
this outcome records failure to establish timely satisfaction.

#### Ownership lost {ownership_lost: outcome}

```contract
value: "ownership_lost"
```

The host's uninterrupted source ownership was lost or its source wait failed.

#### Departure requested {source_departure_requested: outcome}

```contract
value: "source_departure_requested"
```

The host had requested the source's departure before the eligible ending.

### Checking a carried gate {check: checks}

```contract
who: ["identity.definitions.controller"]
where: "semantic assessment after reply admission"
entry: ["cli_run"]
recipient: ["cli_caller"]
report: ["runner_reply"]
bind.p: reply.phases
bind.s: reply.actors
bind.f: reply.phases
match.s: reply.actors[s].actor_id == reply.phases[p].termination_gate.source_actor_id
match.f: reply.phases[f].phase_id == reply.phases[p].termination_gate.source_final_phase_id
when: absent(reply.reporting_failure) and reply.execution_form == "actors" and present(reply.phases[p].termination_gate)
failure: "accumulate"
free.condition: Resolve source and final-phase joins before using s or f; missing, nonfinal, same-actor or nonpreceding associations are findings. Check owned PID/native-status agreement, all conditional gate captures, independent actor setup/equipment eligibility and activation timing.
retained_free: {"condition":{"kind":"native_protocol","reason":"Reader findings combine source/final-phase association, native status, conditional captures and independent equipment/setup checks. Their carried gate and resolved records are distinct operands of the complete procedure."}}
```

#### Failed carried-gate requirement {failed: effect}

```contract
on: "failure"
effects: [set_value(envelope.data.runner_sandbox_diagnostics.disposition_integrity, "invalid"), set_value(envelope.data.runner_sandbox_diagnostics.process_disposition, "withheld"), set_value(envelope.data.runner_sandbox_diagnostics.termination_cause, "unknown"), retain_records(reply), retain_assessments(envelope.data.runner_sandbox_diagnostics.actors)]
free.effect: Append the actor_evidence finding for the failed requirement, with subject_path naming this phase's inspected termination_gate.
uses: ["envelope.data.select"]
retained_free: {"effect":{"kind":"native_protocol","reason":"Native finding construction selects details from the failed predicate, formats the phase position in subject_path as a decimal string, and appends the record. Projection assignments and retention are structured separately."}}
```

Run result and exit status continue to follow their result-selection rule.

#### Unreached shape {unreached: condition}

```contract
test: implies(reply.phases[p].termination_gate.outcome == "not_reached", absent(reply.phases[p].termination_gate.wait) and absent(reply.phases[p].termination_gate.observation) and absent(reply.phases[p].termination_gate.capture_ordinal))
```



#### Timely satisfied wait {timely: condition}

```contract
test: implies(reply.phases[p].termination_gate.outcome == "satisfied", present(reply.phases[p].termination_gate.wait) and reply.phases[p].termination_gate.wait.budget_ms > 0 and reply.phases[p].termination_gate.wait.budget_ms <= 5000 and present(reply.phases[p].termination_gate.wait.elapsed_ms) and reply.phases[p].termination_gate.wait.elapsed_ms <= reply.phases[p].termination_gate.wait.budget_ms and reply.phases[p].termination_gate.wait.clock_fault == False and absent(reply.phases[p].termination_gate.wait.native_errno))
```

Every present gate wait has budget 0–5000 and absent excluded time. An
evaluated gate has a wait whose stop matches its outcome.

#### Source sequence {sequence: condition}

```contract
test: implies(reply.phases[p].termination_gate.outcome == "satisfied", present(reply.phases[f].activation_observation) and present(reply.actors[s].owned_reap) and reply.phases[f].activation_observation.capture_ordinal < reply.actors[s].owned_reap.capture_ordinal and reply.actors[s].owned_reap.capture_ordinal < reply.phases[p].termination_gate.capture_ordinal and reply.actors[s].owned_reap.ownership_unbroken == True and reply.actors[s].owned_reap.departure_requested == False)
```

The referenced ending matches the source actor's valid PID/native wait status,
has stage `schedule` or `termination_gate`, and has the reference's positive
ordinal. Final activation and reap timestamps must exist in nondecreasing
order; a timestamped dependent activation is at or after the reap.

#### Eligibility consequence {eligibility: condition}

```contract
bind.d: reply.actors
match.d: present(reply.phases[p].actor_id) and reply.actors[d].actor_id == reply.phases[p].actor_id and reply.actors[d].setup_status in ["applied", "unapplied_declared"] and present(reply.actors[d].equipment) and reply.actors[d].equipment.execution.eligible == True
each: ["p"]
test: implies(reply.phases[p].termination_gate.activation_eligible == True, reply.phases[p].termination_gate.outcome == "satisfied" and present(reply.actors) and matches(d) > 0) and implies(reply.phases[p].termination_gate.activation_eligible == False, absent(reply.phases[p].activation_observation) and absent(reply.phases[p].visit_timing) and reply.phases[p].arrival_observed == False and reply.phases[p].collection_status == "not_reached" and (absent(reply.phases[p].ordering) or (reply.phases[p].ordering.proceed_set == False and reply.phases[p].ordering.proceed_observed == False)))
```

### A timeout followed by cleanup {timeout_example: example}

The source completes its final phase but remains alive when the dependency
times out. The dependent phase receives no activation, collection or release.
Cleanup later reaps the source; the gate remains `timed_out`.

#### Example support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorScheduler.swift","symbol":"observeTermination"}
check: {"path":"runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift","symbol":"runActorSchedulerTests","form":"test"}
pins: "Source phase completion, timeout, withheld dependent activation/collection/release, later source reap and unchanged timeout."
context: "Real fixture child with post-apply hang and 50 ms execution allowance; test source inspected."
limits: "No execution credit; this assertion covers scheduler observations with shortened allowance, not public JSON or an additional later actor."
```

### Termination cancellation reach {cancellation_evidence: gap}

```contract
kind: "behavior"
```

A failed evaluated termination dependency cancels every remaining scheduled phase, including later work owned by another actor. A dependent actor that is ineligible before gate evaluation has a not_reached gate and does not create that dependency failure. Whether cancellation should have narrower reach remains a maintainer decision.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorScheduler.swift","symbol":"ActorScheduler"}
pins: "An evaluated failed gate sets global schedule cancellation; an unreached gate has a different path."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/witness_contract/check_actor_compositions.py","symbol":"assert_gate_schedule","form":"test"}]
limits: "The control distinguishes a three-worker evaluated timeout from an ineligible-dependent neighbour and retains final collection."
```

## Observation sequences {owned_endings: subject}

### Actor-local sequence {sequence: definition}

```contract
defines: "value"
```

The host maintains one observation counter for each owned child. Each activation
of that actor, its owned reap and each evaluated gate waiting for it consumes
the next ordinal. Source final activation, source reap and gate closure are
comparable within that source sequence. The dependent actor's activation has
its own sequence; its timestamp supplies the cross-process temporal comparison.
A `not_reached` gate consumes no gate-capture ordinal.

## Support for record meanings {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerActors.swift", "symbol": "PWRunnerActorResult"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift", "symbol": "actorApplicationAssessment"}, {"path": "runner/Sources/PWRunnerCore/ActorScheduler.swift", "symbol": "ActorScheduler"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "assembleActorReply"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerReply.swift", "symbol": "actorExtensionEvidenceProblem"}, {"path": "controller/src/porcelain_actor.rs", "symbol": "gates"}, {"path": "controller/src/porcelain_admission.rs", "symbol": "execution_diagnostics"}, {"path": "tests/lib/actor_evidence.py", "symbol": "validate_actor_evidence"}, {"path": "tests/lib/lifecycle_oracle.py", "symbol": "check_actor_records"}, {"path": "tests/lib/consumer.py", "symbol": "_validate_actors"}]
pins: "Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope."
limits: "No execution credit is claimed by this owner."
```

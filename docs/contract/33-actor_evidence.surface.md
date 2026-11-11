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

One-based global phase ordinals declared for this actor, including visits whose activation never occurred.

### equipment {equipment: field}

Requested and resolved worker role, entitlement requirement assessment and live execution observation.

### application {application: field}

Host application-boundary assessment with its evidence basis.

### owned_reap {owned_reap: field}

Host-owned waitpid ending retained for this actor and referenced by dependent termination gates.

### Actor ownership and reporting scope {account: reports}

```contract
who: "runner host"
where: "actor reply assembly"
entry: ["actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["ordinary_reply", "preparation_refusal", "retained_reporting_failure"]
free.condition: Assemble each actor's row from its declaration, launch/driver output and its own shared publications; phases retain their declared actor and action ownership.
free.effect: Retain the actor-indexed account and separately report schedule observations. In an ordinary executed reply, each declared action has its ordered step or extension-event record even when execution evidence is unresolved. Preparation refusals and retained reporting failures carry the distinct contents stated below.
```

A preparation refusal retains declarations and preparation observations while
its execution tables remain empty. A retained reporting-failure reply carries
the assembled observations and the reporting conflict, with comparison claims
removed. Its applicable guarantee is the degraded report's form: retained
actor, phase and resource associations remain available for inspection as
assembled. Ordinary consistency assessments apply on the ordinary reply path.

### Reader scope requiring reconciliation {reader_scope: gap}

```contract
kind: "behavior"
```

The host and controller apply actor/equipment/gate assessment on the ordinary
reporting path. The Python lifecycle receipt reader checks those predicates
for actor-form reporting-failure replies too. The general JSON consumer skips
its extension checks there but still checks actor identities, launch and
phase/step associations. Its preparation partition exception requires a valid
preparation-failure shape. The degraded form guarantee and preservation of
assembled observations above govern retained reporting failures. These reader
scopes still need reconciliation and a common corpus; a gate-specific
disagreement remains an unestablished case.

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

The host classifies the apply-call boundary from mode, launch, applied publication, eligible authority failure and terminal worker evidence, in that precedence order.

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

### Application classification {classify: reports}

```contract
who: "runner host"
where: "actor reply assembly"
entry: ["actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["ordinary_reply", "preparation_refusal"]
free.condition: Evaluate the following branches in displayed precedence order. A terminal worker branch requires failure_state published and the specified operation/code/native-kind combination.
free.effect: Publish exactly the state/basis pair of the first matching branch.
```

#### Unapplied declaration {unapplied: outcome}

```contract
value: ["not_requested", "unapplied_declaration"]
```

Mode is `unapplied`.

#### Worker absent {unlaunched: outcome}

```contract
value: ["not_attempted", "worker_not_launched"]
```

Apply mode has no launched worker.

#### Applied flag {applied: outcome}

```contract
value: ["observed", "applied_publication"]
```

The worker's applied publication is true.

#### Authority refusal {authority: outcome}

```contract
value: ["not_attempted", "terminal_authority_setup_refusal"]
```

An observed authority decision is `terminal_required_failure` and carries no
setup integrity error.

#### Native apply failure {apply_failure: outcome}

```contract
value: ["observed", "apply_failure_publication"]
```

Terminal operation 8, code 1, native kind 1 has a nonzero native result.

#### Input refusal {input: outcome}

```contract
value: ["not_attempted", "terminal_input_refusal"]
```

Terminal operation 1 has code 4, 7, 10 or 12 and native kind 0; or operation 2
has code 2, 3, 9 or 13.

#### Parameter refusal {parameter: outcome}

```contract
value: ["not_attempted", "terminal_parameter_refusal"]
```

Terminal operation 1/code 5/kind 0; operation 3/code 1/kind 2; or operation 4
with code 1/kind 1 or code 6/kind 0.

#### Compile refusal {compile: outcome}

```contract
value: ["not_attempted", "terminal_compile_refusal"]
```

Terminal operation 5/code 1/native kind 2.

#### Timing refusal {timing: outcome}

```contract
value: ["not_attempted", "terminal_timing_refusal"]
```

Terminal operation 12 has code 1/kind 1, code 14/kind 0, or code 15/detail 1/kind 0.

#### Apply boundary without result {boundary: outcome}

```contract
value: ["unobserved", "apply_call_boundary_without_result"]
```

Progress identifies operation 8 and stage 1 or 2, after all earlier branches failed.

#### Remaining evidence {remaining: outcome}

```contract
value: ["unobserved", "no_eligible_apply_publication"]
```

The preceding evidence branches did not establish another pair.

### Setup deadline and later application {late_application: gap}

```contract
kind: "evidence"
```

Final actor collection preserves a later applied publication and derives
`application_count` from it even after setup eligibility ended. The exact
combination of `setup_timeout` with an observed applied publication still
needs an owning behavioral check; the current account is supported by source.

## Phase collection and execution {phase: subject}

```contract
record: "PWRunnerPhaseResult"
as: "ae_phase"
```

The host reports phases in declared schedule order. Observation fields record activation's consequences separately from the declared phase and action identities.

### phase_id {phase_id: field}

Submitted phase identifier used by its action records and validator collection.

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

The capture sequence belongs to the actor whose activation was stored. Time may be unavailable while the store and ordinal remain observed.

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

The schedule records aggregate allowances and cancellation alongside individual actor and phase facts.

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

### Evaluating and applying the dependency {evaluate: acts}

```contract
who: "runner host"
where: "serial actor schedule before dependent activation"
entry: ["actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["ordinary_reply"]
bind.p: reply.phases
when: present(reply.phases[p].termination_gate)
free.condition: Evaluate only after the schedule remains uncancelled, its allowance is positive, and the dependent actor session, usable setup, unstopped state and visit are available. Evaluation first checks the source session and final declared phase activation; unavailable source evidence gives source_unavailable.
free.effect: Set activation_eligible from satisfied. A failed evaluated gate prevents dependent activation, collection and release, and cancels every later scheduled phase regardless of its actor. Cleanup and final collection continue for launched actors.
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

#### Satisfied {satisfied: outcome}

```contract
value: "satisfied"
free.condition: The source final activation precedes a natural owned reap in its child sequence; both timestamps exist and activation time is at most reap time. Ownership is unbroken, departure_requested is false, budget is positive, deadline samples permit the reap, and final wait has a valid elapsed interval at most budget.
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

Evaluation began with no positive whole-millisecond gate budget. A schedule
allowance check that stops traversal earlier leaves the gate `not_reached`.

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
entry: ["controller_run"]
recipient: ["cli_caller"]
report: ["ordinary_reply"]
bind.p: reply.phases
bind.s: reply.actors
bind.f: reply.phases
match.s: reply.actors[s].actor_id == reply.phases[p].termination_gate.source_actor_id
match.f: reply.phases[f].phase_id == reply.phases[p].termination_gate.source_final_phase_id
when: absent(reply.reporting_failure) and present(reply.phases[p].termination_gate)
failure: "accumulate"
free.condition: Resolve source and final-phase joins before using s or f; missing, nonfinal, same-actor or nonpreceding associations are findings. Check owned PID/native-status agreement, all conditional gate captures, independent actor setup/equipment eligibility and activation timing.
free.effect: Add actor_evidence issues for failed requirements; set top-level disposition_integrity invalid, process_disposition withheld and termination_cause unknown. Preserve the host reply, each actor's independently projected disposition, run result and exit status.
```

#### Unreached shape {unreached: condition}

```contract
test: implies(reply.phases[p].termination_gate.outcome == "not_reached", absent(reply.phases[p].termination_gate.wait) and absent(reply.phases[p].termination_gate.observation) and absent(reply.phases[p].termination_gate.capture_ordinal))
```

An unreached gate carries its declaration and false eligibility.

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
test: implies(reply.phases[p].termination_gate.activation_eligible == True, reply.phases[p].termination_gate.outcome == "satisfied")
free.condition: True eligibility also requires the dependent actor's applied or unapplied_declared setup and eligible equipment. False eligibility requires absent activation/visit timing, false arrival/proceed flags and collection not_reached.
```

#### Finding subject {finding_subject: gap}

```contract
kind: "behavior"
```

Gate findings carry `actor_evidence` and a detail sentence. They currently
lack a structured actor or phase reference joining the issue to its gate.
The host's gate fields remain present beside the controller's overall finding.

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

### Cancellation-scope evidence {cancellation_evidence: gap}

```contract
kind: "evidence"
```

The scheduler source cancels every phase after a failed evaluated gate. The
read timeout check covers the dependent phase; a focused check still needs
to assert an additional later phase owned by another actor and its public
cancellation account.

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
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerActors.swift", "symbol": "PWRunnerActorResult"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift", "symbol": "actorApplicationAssessment"}, {"path": "runner/Sources/PWRunnerCore/ActorScheduler.swift", "symbol": "ActorScheduler"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "assembleActorReply"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerReply.swift", "symbol": "actorExtensionEvidenceProblem"}, {"path": "controller/src/porcelain_actor.rs", "symbol": "gates"}, {"path": "controller/src/porcelain_admission.rs", "symbol": "execution_diagnostics"}, {"path": "tests/lib/actor_evidence.py", "symbol": "validate_actor_evidence"}, {"path": "tests/lib/lifecycle_oracle.py", "symbol": "check_actor_records"}, {"path": "tests/lib/consumer.py", "symbol": "_validate_actors"}]
pins: "Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope."
context: "Source and check inspection during contract drafting."
limits: "No execution credit is claimed by this owner."
```

# Actors and phases {actors: surface}

```contract
syntax: 1
artifact: "Actors and phases"
part: "input"
goldens: ["tests/fixtures/contract/surfaces/actors.json"]
checks: ["failure_boundaries"]
```



## Actor declaration {actor: subject}

```contract
record: "PWRunnerActor"
as: "actor"
```

A specimen admits at most <!-- span limits.actors.value_unit -->8 items<!-- /span -->.

### actor_id {actor_id: field}

Nonempty specimen-local actor identifier, unique across actors and bounded by <!-- span limits.actor_id.value_unit -->63 UTF-8 bytes<!-- /span -->. Native transport also requires NUL-free bytes.

### sandbox {sandbox: field}

The actor's explicit apply or unapplied declaration; application assessment is reported separately from this request.

### equipment {equipment: field}

```contract
default: "selected"
vocabulary: "closed"
listed: "exhaustive"
values: ["selected", "unentitled"]
```

Equipment role: `selected` uses the selected runner worker; `unentitled` uses the packaged unentitled worker. Omission selects `selected`; present null is refused.

### required_entitlements {required_entitlements: field}

```contract
default: []
```

Static and live read-back demand for boolean-true entitlement keys on this actor's executable. Omission supplies an empty list; present null is refused.

### Normalize actors before launch {normalize: acts}

```contract
when: present(request.actors) and present(request.phases)
bind.a: request.actors
bind.b: request.actors
bind.p: request.phases
match.b: request.actors[b].actor_id == request.actors[a].actor_id
match.p: request.phases[p].actor_id == request.actors[a].actor_id
free.effect: Resolve the admitted actor and resource references once into the plan indexes used for execution.
who: ["identity.definitions.host"]
where: "actor-plan admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
uses: ["equipment.actor", "equipment.binding"]
retained_free: {"effect":{"kind":"native_protocol","reason":"Resolving admitted references into the executable actor/resource index table is a construction procedure, separate from its structured admission conditions."}}
```

#### Actor identity {identity: condition}

```contract
each: ["a"]
test: request.actors[a].actor_id != "" and matches(b) == 1 and utf8_length(request.actors[a].actor_id) <= limit("actor_id") and not contains(request.actors[a].actor_id, "\u0000")
```

#### Known equipment role {role: condition}

```contract
each: ["a"]
test: implies(present(request.actors[a].equipment), request.actors[a].equipment in ["selected", "unentitled"])
```

#### At least one declared visit {visits: condition}

```contract
each: ["a"]
test: matches(p) > 0
```

#### Sandbox declaration {sandbox: condition}

```contract
each: ["a"]
test: request.actors[a].sandbox.mode in ["apply", "unapplied"] and implies(request.actors[a].sandbox.mode == "apply", present(request.actors[a].sandbox.policy)) and implies(request.actors[a].sandbox.mode == "unapplied", absent(request.actors[a].sandbox.policy))
```

#### Entitlement list capacity {entitlement_count: condition}

```contract
each: ["a"]
test: count(request.actors[a].required_entitlements) <= limit("actor_required_entitlements")
```

#### Required entitlement identity {entitlement_identity: condition}

```contract
bind.e: request.actors[a].required_entitlements
bind.f: request.actors[a].required_entitlements
match.f: request.actors[a].required_entitlements[f] == request.actors[a].required_entitlements[e]
each: ["a", "e"]
test: request.actors[a].required_entitlements[e] != "" and matches(f) == 1 and utf8_length(request.actors[a].required_entitlements[e]) <= limit("actor_entitlement_key") and not contains(request.actors[a].required_entitlements[e], "\u0000")
```

#### Refusal consequence {failure: effect}

```contract
on: "failure"
effects: perform(ref("refusals.request.consequence"), request)
```

### Fresh process and retained policy {fresh: acts}

```contract
when: present(request.actors)
who: ["identity.definitions.host", "identity.definitions.worker"]
where: "actor process lifecycle"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Launch one fresh worker for each actor. An apply worker compiles and applies its own declared policy once before its visits; an unapplied worker publishes that declaration and executes under the restrictions already inherited by its process. Keep that worker for its successive visits.
uses: ["actor_evidence.application"]
retained_free: {"effect":{"kind":"native_protocol","reason":"Fresh process creation, one-way application and successive parked visits describe process lifetime and inherited restrictions."}}
```



### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerActors.swift", "symbol": "PWRunnerActor"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "actorApplicationAssessment"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "requestAdmissionFailure"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "actorAdmissionFailure"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
limits: "Normalization concerns admitted declarations; worker setup and application observations have separate owners."
```



## Actor sandbox declaration {sandbox: subject}

```contract
record: "PWRunnerActorSandbox"
as: "sandbox"
```



### mode {mode: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["apply", "unapplied"]
```

`apply` requires a policy and asks the worker to compile/apply it; `unapplied` requires policy absence or null and records the inherited process restrictions as its starting condition.

### policy {policy: field}

```contract
required_when: sandbox.mode == "apply"
present_when: sandbox.mode == "apply"
```

Required non-null policy for `apply`; a non-null policy is refused for `unapplied`. Each apply policy has its own source, parameters, augmentation and capture request.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerActors.swift", "symbol": "PWRunnerActorSandbox"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
```



## Phase declaration {phase: subject}

```contract
record: "PWRunnerPhase"
as: "phase"
```



### phase_id {phase_id: field}

Nonempty identifier unique across the specimen's phases and bounded by <!-- span limits.phase_id.value_unit -->63 UTF-8 bytes<!-- /span --> and NUL-free.

#### Required phase identity {identity: condition}

```contract
test: phase.phase_id != "" and utf8_length(phase.phase_id) <= limit("phase_id") and not contains(phase.phase_id, "\u0000")
```

### actor_id {actor_id: field}

Required known actor owner in the actor form. The ordinary form requires absence or null.

### actions {actions: field}

Actions in declaration order, including an empty array. Ordinary phases contain paired probes. Actor phases may also contain extension actions. Action identifiers are unique across the whole specimen.

### after_termination {after_termination: field}

Optional owned-termination dependency in the actor form. Absence supplies no dependency; present null is refused. The ordinary form refuses a supplied dependency.

### Collect, release and advance {order: acts}

```contract
who: ["identity.definitions.host"]
where: "phase scheduler"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Close the active phase's eligible prediction collection before releasing its actions; run those actions in declaration order. Begin the next phase's collection after the previous phase completes. In the actor form activate one actor at a time while other workers remain parked.
uses: ["identity.definitions.phase", "identity.definitions.prediction"]
retained_free: {"effect":{"kind":"native_protocol","reason":"Collector closure, release-store publication, action completion and parked actors form the live scheduling protocol."}}
```



#### Barrier observation support {disposition_support: owner}

```contract
grade: "source_read"
source: {"path":"runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift","symbol":"eligibleOrderedStep"}
pins: "The ordering claim requires a complete chain and a unique matching native prediction for the owned worker."
limits: "The source owner describes eligibility. Integrated collection/release and mutation observations retain their own execution owners."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerPhase"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "admissionFailure"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "actorAdmissionFailure"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
limits: "Source support here pins decoded grammar and normalized order. Runtime collection/release evidence belongs to the phase and lifecycle producer rules."
```



## Termination dependency {after_termination: subject}

```contract
record: "PWRunnerAfterTermination"
as: "after_termination"
```

The declaration names a source actor, while the gate reports the host's owned observation of its ending.

### actor_id {actor_id: field}

Known actor whose final declared phase occurs earlier than the dependent phase. It must differ from the dependent phase's actor.

### Validate and evaluate the dependency {gate: acts}

```contract
when: present(request.actors)
who: ["identity.definitions.host"]
where: "actor admission and phase activation"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Before activating the dependent actor or collecting its predictions, evaluate the owned natural-reap gate. A failed evaluated gate cancels every remaining scheduled phase.
uses: ["actor_evidence.gate"]
retained_free: {"effect":{"kind":"native_protocol","reason":"Owned natural-reap evaluation occurs between prior activation and dependent collection; cancellation is a live scheduler transition, separate from the declared-visit admission conditions."}}
```



### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerActors.swift", "symbol": "PWRunnerAfterTermination"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
limits: "Admission source read; the referenced actor-evidence rule owns the runtime gate and global cancellation consequence."
```

### Admit the declared dependency {declaration: acts}

```contract
who: ["identity.definitions.host"]
where: "actor plan admission before child launch"
entry: ["xpc_execute"]
recipient: ["report_reader"]
report: ["runner_reply"]
when: present(request.actors) and present(request.phases)
bind.p: request.phases
bind.a: request.actors
bind.q: request.phases
match.a: request.actors[a].actor_id == request.phases[p].after_termination.actor_id
match.q: request.phases[q].actor_id == request.phases[p].after_termination.actor_id
each: ["p"]
```
#### Source actor and visit {source: condition}

```contract
when: present(request.phases[p].after_termination)
test: matches(a) == 1 and request.phases[p].after_termination.actor_id != request.phases[p].actor_id and matches(q) > 0
```
#### Every source visit precedes this phase {earlier: condition}

```contract
each: ["q"]
when: present(request.phases[p].after_termination) and request.phases[q].actor_id == request.phases[p].after_termination.actor_id
test: q < p
```
#### Refusal consequence {failure: effect}

```contract
on: "failure"
effects: perform(ref("refusals.request.consequence"), request)
```
#### Source support {support: owner}

```contract
grade: "source_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorPlan.swift","symbol":"normalizeActorPlan"}
pins: "The dependency names a different declared actor whose final declared phase precedes the dependent phase."
```

## Phase action variants {action: subject}

```contract
record: "PWRunnerPhaseAction"
as: "action"
```

An action is one JSON object in the phase actions array. The decoder chooses an extension action when the `extension` key is present; otherwise it decodes a paired probe. A present null extension therefore selects extension decoding and fails its required object.

### Action identity {identity: acts}

```contract
who: ["identity.definitions.host"]
where: "plan admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
uses: ["probes.step", "extensions.action"]
```

#### Flat probe identities {flat: condition}

```contract
when: absent(request.actors) and present(request.probe_plan)
bind.i: request.probe_plan
bind.j: request.probe_plan
match.j: request.probe_plan[j].step_id == request.probe_plan[i].step_id
each: ["i"]
test: matches(j) == 1
```

#### Phased probe identities {probe: condition}

```contract
when: present(request.phases) and is_variant(request.phases[p].actions[a], "probe")
bind.p: request.phases
bind.a: request.phases[p].actions
bind.q: request.phases
bind.b: request.phases[q].actions
match.b: (is_variant(request.phases[q].actions[b], "probe") and variant(request.phases[q].actions[b], "probe").step_id == variant(request.phases[p].actions[a], "probe").step_id) or (is_variant(request.phases[q].actions[b], "extensionAction") and variant(request.phases[q].actions[b], "extensionAction").step_id == variant(request.phases[p].actions[a], "probe").step_id)
each: ["p", "a"]
test: sum_over(q, matches(b)) == 1 and implies(present(request.actors), variant(request.phases[p].actions[a], "probe").step_id != "")
```

#### Phased extension identities {extension: condition}

```contract
when: present(request.phases) and is_variant(request.phases[p].actions[a], "extensionAction")
bind.p: request.phases
bind.a: request.phases[p].actions
bind.q: request.phases
bind.b: request.phases[q].actions
match.b: (is_variant(request.phases[q].actions[b], "probe") and variant(request.phases[q].actions[b], "probe").step_id == variant(request.phases[p].actions[a], "extensionAction").step_id) or (is_variant(request.phases[q].actions[b], "extensionAction") and variant(request.phases[q].actions[b], "extensionAction").step_id == variant(request.phases[p].actions[a], "extensionAction").step_id)
each: ["p", "a"]
test: sum_over(q, matches(b)) == 1 and implies(present(request.actors), variant(request.phases[p].actions[a], "extensionAction").step_id != "")
```

#### Refusal consequence {failure: effect}

```contract
on: "failure"
effects: perform(ref("refusals.request.consequence"), request)
```

### Form-specific action identifiers {empty_id: definition}

```contract
defines: "value"
```

Ordinary-form action identifiers may be empty. Actor-form action identifiers must be nonempty so declared actions can be resolved in the actor schedule. UTF-8 capacity, NUL exclusion, uniqueness and membership are separate requirements at their owning admission boundary.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: [{"path":"runner/Sources/PWRunnerCore/ActorPlan.swift","symbol":"normalizeActorPlan"},{"path":"runner/Sources/PWRunnerCore/ProbeRunner.swift","symbol":"requestMeaningFailure"}]
pins: "Actor normalization rejects an empty action step_id before constructing its slot map; ordinary meaning admission tests uniqueness without a nonempty condition."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift","symbol":"runReaderCorpusTests","form":"test"}]
limits: "The corpus emits separate ordinary-empty and actor-empty declaration neighbours through reporting admission; it is constructed reader evidence."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerPhaseAction"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "requestMeaningFailure"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
```

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

A specimen admits at most <!-- span limits.actors.value_unit -->8 items<!-- /span -->. Each actor has at least one declared phase. Each required-entitlement list fits <!-- span limits.actor_required_entitlements.value_unit -->64 items<!-- /span -->, with each key bounded by <!-- span limits.actor_entitlement_key.value_unit -->255 UTF-8 bytes<!-- /span -->.

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

Static and live read-back demand for boolean-true entitlement keys on this actor's executable. Omission supplies an empty list; present null is refused. Keys must be nonempty and unique.

### Normalize actors before launch {normalize: acts}

```contract
who: "XPC host"
where: "actor-plan admission"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Require unique nonempty actor IDs, known equipment roles, valid sandbox declarations, valid entitlement demands, and at least one phase per actor. Build one resolved plan whose actor and resource indexes govern execution.
uses: ["equipment.actor", "equipment.binding"]
```



### Fresh process and retained policy {fresh: acts}

```contract
who: "XPC host and actor worker"
where: "actor process lifecycle"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Launch one fresh worker for each actor. An apply worker compiles and applies its own declared policy once before its visits; an unapplied worker publishes that declaration and executes under the restrictions already inherited by its process. Keep that worker for its successive visits.
uses: ["actor_evidence.application"]
```



### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerActors.swift", "symbol": "PWRunnerActor"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "actorApplicationAssessment"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
context: "Source inspection of the current implementation; no execution is credited."
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
context: "Source inspection of the current implementation; no execution is credited."
limits: "Runtime behavior remains subject to integrated acceptance evidence."
```



## Phase declaration {phase: subject}

```contract
record: "PWRunnerPhase"
as: "phase"
```

The actor form admits <!-- span limits.actor_phases.value_unit -->16 items<!-- /span --> and the ordinary form <!-- span limits.phase_count.value_unit -->8 items<!-- /span -->. Across either form, actions share the <!-- span limits.probe_steps.value_unit -->256 items<!-- /span --> total capacity.

### phase_id {phase_id: field}

Nonempty identifier unique across the specimen's phases and bounded by <!-- span limits.phase_id.value_unit -->63 UTF-8 bytes<!-- /span --> and NUL-free.

### actor_id {actor_id: field}

Required known actor owner in the actor form. The ordinary form requires absence or null.

### actions {actions: field}

Actions in declaration order, including an empty array. Ordinary phases contain paired probes. Actor phases may also contain extension actions. Action identifiers are unique across the whole specimen.

### after_termination {after_termination: field}

Optional owned-termination dependency in the actor form. Absence supplies no dependency; present null is refused. The ordinary form refuses a supplied dependency.

### Collect, release and advance {order: acts}

```contract
who: "XPC host"
where: "phase scheduler"
entry: ["ordinary_xpc_execute", "actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Close the active phase's eligible prediction collection before releasing its actions; run those actions in declaration order. Begin the next phase's collection after the previous phase completes. In the actor form activate one actor at a time while other workers remain parked.
uses: ["identity.definitions.phase", "identity.definitions.prediction"]
```



### Barrier observation scope {barrier_evidence: definition}

```contract
defines: "value"
```

Query ordering joins whole-batch collection, host release, worker acknowledgement and the associated attempt. Phase records retain each observation and the established order. Integrated controls and mutation controls assess this sequence at their selected execution boundary; source ordering alone has source-read support.

#### Disposition support {disposition_support: owner}

```contract
grade: "source_read"
source: {"path":"runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift","symbol":"eligibleOrderedStep"}
pins: "The ordering claim requires a complete chain and a unique matching native prediction for the owned worker."
context: "Static review of the cited production branches."
limits: "The source owner describes eligibility. Integrated collection/release and mutation observations retain their own execution owners."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerPhase"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
context: "Source inspection of the current implementation; no execution is credited."
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
who: "XPC host"
where: "actor admission and phase activation"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: At admission require the source's final declared visit before the dependent phase. Before activating the dependent actor or collecting its predictions, evaluate the owned natural-reap gate. A failed evaluated gate cancels every remaining scheduled phase.
uses: ["actor_evidence.gate"]
```



### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerActors.swift", "symbol": "PWRunnerAfterTermination"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
context: "Source inspection of the current implementation; no execution is credited."
limits: "Admission source read; the referenced actor-evidence rule owns the runtime gate and global cancellation consequence."
```



## Phase action variants {action: subject}

```contract
record: "PWRunnerPhaseAction"
as: "action"
```

An action is one JSON object in the phase actions array. The decoder chooses an extension action when the `extension` key is present; otherwise it decodes a paired probe. A present null extension therefore selects extension decoding and fails its required object.

### Paired probe {probe: definition}

```contract
defines: "record"
```

The probe variant is `PWRunnerProbeStep`: a step ID, sandbox query and attempt, as defined by the probes surface.

### Extension action {extension: definition}

```contract
defines: "record"
```

The extension variant is `PWRunnerExtensionAction`: a step ID and closed extension operation, as defined by the extensions surface. It contributes no sandbox query.

### Action identity {identity: acts}

```contract
who: "XPC host"
where: "plan admission"
entry: ["ordinary_xpc_execute", "actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Refuse repeated step IDs across the complete specimen. Actor actions require nonempty IDs. The ordinary form currently accepts an empty step ID when it is unique.
uses: ["probes.step", "extensions.action"]
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
context: "Source inspection of the current implementation; no execution is credited."
limits: "Runtime behavior remains subject to integrated acceptance evidence."
```

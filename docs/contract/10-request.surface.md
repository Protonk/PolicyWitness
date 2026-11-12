# Saved specimens and runner selection {request: surface}

```contract
syntax: 1
artifact: "Saved specimens and runner selection"
part: "input"
goldens: ["tests/fixtures/contract/surfaces/request.json", "tests/fixtures/request_contract/examples.json"]
checks: ["failure_boundaries"]
```


Direct XPC callers supply the host form themselves.

## Specimen {specimen: subject}

```contract
record: "PWRunnerRunSpec"
as: "specimen"
```

The host request objects have closed field sets. Parameter-map keys and caller labels are data within their own bounds.

### contract {contract: field}

```contract
uses: ["identity.public.contract"]
```

Required non-null string asserting the exact public contract identity. The controller checks it before selector parsing and augmentation; the host checks it before other request fields. Obtain the current value from the packaged version envelope. `unbound` is refused.

### specimen_id {specimen_id: field}

Required non-null string caller label, echoed when it fits <!-- span limits.specimen_id.value_unit -->255 UTF-8 bytes<!-- /span -->. It may be empty. Its identity is independent of the worker PID or an actor ID.

### run_kind {run_kind: field}

```contract
default: null
```

Optional caller label, bounded by <!-- span limits.request_label.value_unit -->63 UTF-8 bytes<!-- /span -->. Omission and null have the same meaning; it selects no execution mode.

### policy {policy: field}

Policy for the ordinary form. With no non-null `actors`, the policy object is required. In the actor form a non-null top-level policy is refused; each actor declares its own sandbox mode and policy.

### probe_plan {probe_plan: field}

Ordinary paired probes, including an empty array for apply-only execution. Exactly one of this field and `phases` must be non-null in the ordinary form. The host represents this plan as the `main` phase.

### phases {phases: field}

Ordered phase declarations. The ordinary form requires a nonempty array, forbids actor ownership, termination dependencies and extension actions, and uses one worker across its phases. The actor form requires phases and forbids a non-null `probe_plan`.

### actors {actors: field}

A non-null actor array selects the actor form; an empty array is refused. Each declared actor has its own fresh worker and at least one declared visit. Omission or null selects the ordinary form.

### _test_overrides {_test_overrides: field}

Optional execution controls accepted by the host request decoder. Each declared control retains its stated scope and meaning; unknown override fields are refused.

### Hold and deliver the selected request {hold: acts}

```contract
who: ["identity.definitions.controller"]
where: "saved-file processing"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Read and parse the request file once; gate its contract, parse selection, resolve named augments, strip controller selector fields and serialize once for client delivery. Preserve original and selected policy observations in the specimen dossier.
uses: ["identity.definitions.specimen", "identity.definitions.request"]
retained_free: {"effect":{"kind":"native_protocol","reason":"The read-once, in-memory augmentation and one-serialization guarantee concerns ownership of intermediate request bytes."}}
```



### Admission order and effects {admission: acts}

```contract
uses: ["refusals.request.consequence"]
who: ["identity.definitions.host"]
where: "request decode and whole-request admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Check contract first, decode the selected plan form and closed nested objects, check capacities, then validate policy and plan meaning. On refusal apply the runner request-refusal consequence. A host may already exist to deliver that refusal.
retained_free: {"effect": {"kind": "raw_admission", "reason": "Contract-first decoding and branch traversal consume raw objects before a complete typed request is available."}}
```

Admission accepts or refuses the complete plan; it preserves declared action counts.

### Null and omission {nulls: acts}

```contract
who: ["identity.definitions.host"]
where: "request decoding"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Treat optional null as absent where decodeIfPresent is used. Refuse present null for actor equipment, actor required_entitlements, after_termination and actor_equipment_executable_paths. Retain presence of extension operands so an inapplicable operand is refused even when null.
uses: ["identity.definitions.absent", "identity.definitions.null_value", "extensions.operation"]
retained_free: {"effect":{"kind":"raw_admission","reason":"Key presence, explicit null and failed decoding are distinguished before optional admitted values erase those distinctions."}}
```



### Bounded strings and action counts {capacity: acts}

```contract
free.effect: Preserve complete UTF-8 strings at accepted bounds.
who: ["identity.definitions.host"]
where: "pre-child admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
retained_free: {"effect":{"kind":"serialized_grammar","reason":"Complete string transport and C-string admission describe the original encoded inputs, separate from the structured count requirements."}}
```

Native C-string inputs also refuse embedded NUL. A paired query and attempt consumes one action; an extension action consumes one action and contributes no query. Phase and actor counts do not multiply the total action capacity.

#### Ordinary source bytes {ordinary_source: condition}

```contract
when: absent(specimen.actors) and present(specimen.policy) and present(specimen.policy.sbpl_source)
test: utf8_length(specimen.policy.sbpl_source) <= limit("policy_source")
```

#### Actor source bytes {actor_source: condition}

```contract
bind.a: specimen.actors
each: ["a"]
when: present(specimen.actors) and present(specimen.actors[a].sandbox.policy) and present(specimen.actors[a].sandbox.policy.sbpl_source)
test: utf8_length(specimen.actors[a].sandbox.policy.sbpl_source) <= limit("policy_source")
```

#### Flat action count {flat_actions: condition}

```contract
when: absent(specimen.actors) and present(specimen.probe_plan)
test: count(specimen.probe_plan) <= limit("probe_steps")
```

#### Phased action count {phase_actions: condition}

```contract
when: present(specimen.phases)
bind.p: specimen.phases
test: sum_over(p, count(specimen.phases[p].actions)) <= limit("probe_steps")
```

#### Ordinary phase count {ordinary_phases: condition}

```contract
when: absent(specimen.actors) and present(specimen.phases)
test: count(specimen.phases) <= limit("phase_count")
```

#### Actor phase count {actor_phases: condition}

```contract
when: present(specimen.actors) and present(specimen.phases)
test: count(specimen.phases) <= limit("actor_phases")
```

#### Refusal consequence {failure: effect}

```contract
on: "failure"
effects: perform(ref("refusals.request.consequence"), request)
```

### Apply-only specimen {apply_only: example}

This template applies a policy with no probe actions. Replace the assertion with the packaged version's `build.contract` before submission.

```json
{"contract":"<reported-contract>","specimen_id":"apply-only","policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default)"},"probe_plan":[]}
```

### Repeated members at each entry {duplicate_keys: definition}

```contract
defines: "value"
```

For the paired repeated-member cases, CLI entry keeps the last contract, policy, probe step_id, attempt target, runner selector or runner.mode value, then holds the parsed object’s serialization. Direct host entry keeps the first contract, policy, probe step_id or attempt target value in either tested order. Direct-host runner and runner.mode cases refuse with unknown_field at ["runner"] in either order. These observations concern the listed raw-input pairs, their canonical neighbours and independent file effects on the observed platform.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"controller/src/request_patch.rs","symbol":"parse_request"}
pins: "The controller parses raw JSON before holding its object; the direct-host cases use retained raw request bytes."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/runner_outcome_bad_request/contract.py","symbol":"duplicate_entries","form":"test"}]
limits: "The pinned matrix distinguishes both member orders and canonical neighbours for six fields at CLI and direct host entries. Its selected field/value pairs bound the observation."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerRunSpec"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "admissionFailure"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "admitSpecimen"}, {"path": "controller/src/run_flow.rs", "symbol": "validate_request_contract"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "requestAdmissionFailure"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "actorAdmissionFailure"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
context: "Source inspection of the current implementation; no execution is credited."
limits: "Read the request fixture corpus loop, identity/unknown-field checks and actor parameter-capacity assertions. The apply-only template has source-level support; this owner credits no executed instance of that template."
check: [{"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
```



## Controller selection options {options: subject}

```contract
record: "ControllerSelectionOptions"
as: "options"
```

These fields extend the saved-file root at the controller entry. The controller strips all five before client delivery. A direct XPC request carrying them reaches the host unknown-field refusal.

### runner {runner: field}

```contract
type: "ControllerRunnerSelector"
optional: true
json_null: true
```

Optional nested selector object. Null means absent. Unknown nested keys are refused.

### runner_id {runner_id: field}

```contract
type: "String"
optional: true
json_null: true
```

Legacy registry ID selector. Null means absent; a non-string value refuses even when nested `runner.id` would override it.

### runner_service {runner_service: field}

```contract
type: "String"
optional: true
json_null: true
```

Legacy explicit Mach service selector. Null means absent; a non-string value refuses before nested precedence is applied.

### required_entitlements {required_entitlements: field}

```contract
type: "[String]"
optional: true
json_null: true
```

Legacy list of selected-worker entitlement keys required to be boolean true. Null means absent. Values must be strings.

### runner_mode {runner_mode: field}

```contract
type: "String"
optional: true
json_null: true
vocabulary: "closed"
listed: "exhaustive"
values: ["standard", "byoxpc"]
```

Legacy runner mode. Null means absent. The accepted values are `standard` and `byoxpc`.

### Selector precedence {precedence: acts}

```contract
who: ["identity.definitions.controller"]
where: "runner selector parsing"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Validate every supplied legacy value first, then let each non-null nested value replace its corresponding legacy value. An explicit nested empty entitlement list replaces the legacy list. Refuse standard mode with an external selector and byoxpc mode without an ID or service.
retained_free: {"effect": {"kind": "raw_admission", "reason": "CLI mode injection and per-field precedence construct the effective selector from supplied candidates. Malformed raw values are checked before replacement; an explicit nested empty entitlement list replaces the legacy list."}}
```

CLI `--runner-mode` is parsed before reading the request and is injected into its selector processing. `machme` is refused. Selection resolution and entitlement checks precede client invocation. A resolved target identifies the requested host service; actor equipment roles remain actor declarations.

### Selection and augmentation failure order {failure_order: acts}

```contract
uses: ["refusals.controller.consequence"]
who: ["identity.definitions.controller"]
where: "request preparation"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Retain a target-resolution error while resolving augment dossiers. Select the target-resolution error first; otherwise select an augment refusal when present. Apply the controller pre-invocation consequence to the selected failure.
retained_free: {"effect": {"kind": "native_protocol", "reason": "Target resolution and augmentation return separate intermediate results. Their priority determines which refusal procedure applies."}}
```



### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/runner_select.rs", "symbol": "parse_runner_selector_value"}, {"path": "controller/src/run_flow.rs", "symbol": "strip_runner_selector"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
context: "Source inspection of the current implementation; no execution is credited."
limits: "Read parser and precedence controls; full registry selection and installed-equipment evidence belongs to installation and equipment."
check: [{"path": "controller/src/runner_select.rs", "symbol": "nested_runner_takes_precedence_over_legacy_top_level", "form": "test"}, {"path": "controller/src/runner_select.rs", "symbol": "malformed_selection_never_falls_back_or_discards_entitlements", "form": "test"}, {"path": "controller/src/runner_select.rs", "symbol": "optional_nulls_and_explicit_nested_empty_entitlements_have_defined_meanings", "form": "test"}]
```



## Nested runner selector {selector: subject}

```contract
record: "ControllerRunnerSelector"
as: "selector"
```



### id {id: field}

```contract
type: "String"
optional: true
json_null: true
```

Registry ID for an installed external runner.

### service {service: field}

```contract
type: "String"
optional: true
json_null: true
```

Explicit external Mach service name.

### required_entitlements {required_entitlements: field}

```contract
type: "[String]"
optional: true
json_null: true
```

Selected-worker entitlement keys that must read back as boolean true for selection. This demand is separate from each actor's required_entitlements.

### mode {mode: field}

```contract
type: "String"
optional: true
json_null: true
vocabulary: "closed"
listed: "exhaustive"
values: ["standard", "byoxpc"]
```

Mode constraint applied to selection. With no mode or external selector, selection uses the packaged standard runner.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/runner_select.rs", "symbol": "RunnerSelector"}, {"path": "controller/src/runner_select.rs", "symbol": "parse_runner_selector_value"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
```



## Execution overrides {overrides: subject}

```contract
record: "PWRunnerTestOverrides"
as: "overrides"
```

These controls are admitted as request data in the current implementation, including packaged hosts. Their names identify test use; the parser applies the documented grammar and capacities. Host admission of a positive fixture value can be followed by worker argument refusal before application.

### worker_executable_path {worker_executable_path: field}

Ordinary-worker executable override, bounded by <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. Actor-form admission refuses this singular override.

### worker_timeout_ms {worker_timeout_ms: field}

Ordinary worker sentinel budget override in milliseconds. The host floors the supplied allowance at <!-- span limits.worker_timeout_override_floor.value_unit -->50 milliseconds<!-- /span -->; omission uses <!-- span limits.worker_sentinel_wait.value_unit -->120,000 milliseconds<!-- /span -->. Actor scheduling uses its fixed setup allowance and its fixed <!-- span limits.actor_execution_allowance.value_unit -->120,000 milliseconds<!-- /span --> execution allowance even when this field is supplied.

#### Floor support {floor_support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift","symbol":"timeoutMsForCWorker"}
check: {"path":"runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift","symbol":"runLimitsContractTests","form":"test"}
pins: "Calls the production helper to compare its floor to the limits inventory; independent below/equal/above cases retain the minimum and the uncapped larger override."
context: "Planning helper and newly authored constructed assertions read."
limits: "No test execution is credited; the check establishes the planning value, not elapsed worker time."
```

#### Actor applicability support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorOrchestration.swift","symbol":"runActors"}
pins: "Actor orchestration constructs the scheduler input with its fixed allowances."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/witness_contract/check_actor_compositions.py","symbol":"assert_timeout_applicability","form":"test"}]
limits: "The paired control uses a 200 ms override and a 500 ms delay, checking an ordinary timeout and actor completion with a later dependent file read."
```

### actor_equipment_executable_paths {actor_equipment_executable_paths: field}

Actor equipment role-to-path map. Present maps must be nonempty and use only `selected` and `unentitled` keys; actor admission requires absolute paths. The ordinary form refuses this map.

### validator_executable_path {validator_executable_path: field}

Validator executable override, bounded by <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. The validator remains a separate child and receives query work through its own channel.

### validator_total_timeout_ms {validator_total_timeout_ms: field}

Cumulative validator collection budget override in milliseconds, spanning phases. Both schedulers clamp it to a minimum of <!-- span limits.validator_collection_override_floor.value_unit -->1 millisecond<!-- /span --> and their configured maximum: <!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span --> for the ordinary form and <!-- span limits.actor_collection_allowance.value_unit -->30,000 milliseconds<!-- /span --> for actors. Omission uses that maximum.

### validator_io_timeout_ms {validator_io_timeout_ms: field}

Per-validator I/O timeout override in milliseconds. The host floors the proposed allowance at <!-- span limits.validator_io_override_floor.value_unit -->50 milliseconds<!-- /span -->; omission uses <!-- span limits.validator_io_wait.value_unit -->30,000 milliseconds<!-- /span -->. The remaining aggregate collection allowance can reduce the effective timeout below that floor.

### worker_post_apply_hang_ms {worker_post_apply_hang_ms: field}

Positive fixture delay in milliseconds after all declared visits and actions, before terminal publication. The host forwards positive values; the worker argument parser accepts through <!-- span limits.worker_fixture_delay.value_unit -->60,000 milliseconds<!-- /span -->. A larger forwarded value causes worker argument refusal after launch. Zero and negative values are omitted by the host.

### worker_post_apply_kill_signal {worker_post_apply_kill_signal: field}

Positive fixture signal requested after completed actions and before terminal publication, including an unapplied actor's visits. The host forwards positive values; the worker accepts signal numbers through 31. A larger value causes worker argument refusal after launch. Zero and negative values are omitted. A signal request can return without termination; final process observations decide the ending.

### worker_pre_ready_hang_ms {worker_pre_ready_hang_ms: field}

Positive fixture delay in milliseconds after compilation and optional capture, before an apply worker's readiness byte and policy application. The host forwards positive values; the worker argument parser accepts through <!-- span limits.worker_fixture_delay.value_unit -->60,000 milliseconds<!-- /span -->. A larger value causes worker argument refusal after launch. Zero and negative values are omitted. The unapplied actor branch bypasses this compile/readiness path.

### worker_kill_before_publish_slot {worker_kill_before_publish_slot: field}

Nonnegative zero-based slot in each worker's own plan. After that attempt returns and its result payload is written, the worker raises SIGKILL before publishing completion. Negative values are omitted. The worker argument parser requires an index below <!-- span limits.probe_steps.value_unit -->256 items<!-- /span -->; an index beyond the worker's actual plan has no reached action to trigger it.

### Override admission and equipment ordering {override_authority: definition}

```contract
defines: "condition"
uses: ["equipment.binding"]
```

A caller whose connection passes host authorization can supply these controls. Actor equipment preparation checks the packaged inventory and both packaged role bindings before considering fixture override bindings. It retains the packaged and test_override rows with their respective implementation identities.

### Fixture-value support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorOrchestration.swift","symbol":"runActors"}
pins: "The actor path retains equipment preparation and fixed scheduler applicability separately."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/witness_contract/check_pre_apply_failure.py","symbol":"main","form":"test"}]
limits: "Excessive positive fixture values are sent through the selected CLI and checked at the downstream worker argument boundary."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerTestOverrides"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "timeoutMsForCWorker"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "admitSpecimen"}, {"path": "runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift", "symbol": "collectionRemainingNs"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "collectionRemainingNs"}, {"path": "runner/Sources/PWRunnerCore/ActorSession.swift", "symbol": "postApplyHangMs"}, {"path": "runner/Sources/PWRunnerCore/ActorEquipment.swift", "symbol": "private func prepare"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "kill_before_publish_slot"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
```

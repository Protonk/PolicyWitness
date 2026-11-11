# Request refusals and retained evidence {refusals: surface}

```contract
syntax: 1
artifact: "Request refusals and retained evidence"
part: "report"
goldens: ["tests/fixtures/contract/surfaces/refusals.json", "tests/fixtures/request_contract/examples.json"]
checks: ["failure_boundaries"]
```



A refusal identifies the boundary that stopped the request or a later interpretation. Input refusals carry machine-readable code and location; transport and reporting failures retain the observations supplied by their own channels.

## Runner request refusal {request: subject}

```contract
record: "PWRunnerRequestFailure"
as: "request_failure"
```

The host supplies this record for decoding, meaning and capacity refusal. Its human error string explains the category; readers use the structured fields for machine classification.

### code {code: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["invalid_json", "missing_field", "missing_value", "type_mismatch", "unknown_field", "unsupported_contract", "admission_refused"]
unknown: "An unfamiliar code remains an unclassified refusal category; its producer text and path are retained as evidence."
```

Producer's refusal category. Current categories identify syntax, required values, contract mismatch, closed-field or plan meaning, and capacity failures.

### path {path: field}

Object keys and decimal array indexes locating the rejected input; [] names the root. Retain the entire path only through <!-- span limits.request_failure_path_components.value_unit -->8 items<!-- /span -->, with each component through <!-- span limits.request_failure_path_component.value_unit -->63 UTF-8 bytes<!-- /span -->; otherwise null withholds it.

### expected_contract {expected_contract: field}

Current expected public identity supplied for refusal at `contract`; omitted otherwise. It identifies the receiver's expected assertion.

### Refuse at the first reached boundary {select: acts}

```contract
who: "host"
where: "request decoding and admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Report the first failure reached by the actual decoder or admission branch. Check contract before unknown root fields; at a decoded closed object choose its lexicographically first unknown key before decoding its declared fields. Complete decoded capacity checks before meaning admission.
```

The ordinary and actor plan branches have different required fields and ordered checks. There is one request_failure per refusal. Its code and path locate the selected problem; correcting it may reveal the next problem.

### Stop children and preserve safe metadata {consequence: acts}

```contract
who: "host"
where: "pre-child request refusal"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Return normalized_outcome bad_request, rc 1 and steps []. Start no worker or validator for the refused request. Retain metadata only under its own echo rule, independent of which field won refusal precedence.
uses: ["request.specimen"]
```



### Current refusal families {families: definition}

```contract
defines: "value"
```

| Category | Current code examples and condition |
| --- | --- |
| JSON and required values | `invalid_json`, `invalid_value`, `missing_field`, `missing_value`, `type_mismatch`; decoder structure or required-value failure. |
| Public identity and closed objects | `unsupported_contract`; assertion differs or expected identity is unbound. `unknown_field`; undeclared object key. |
| Plan form and identifiers | `exclusive_plan_forms`, `actors_require_phases`, `empty_phases`, `empty_actors`, `empty_actor_id`, `empty_phase_id`, `empty_step_id`, `duplicate_actor_id`, `duplicate_phase_id`, `duplicate_step_id`, `actor_without_phases`. |
| Policy and query | `unresolved_augments`, `unsupported_policy_format`, `missing_policy_source`, `invalid_capture_nonce`, `empty_operation`, `unknown_filter_kind`, `missing_filter_value`. |
| Attempt and applicability | `unsupported_attempt`, `relative_exec_target`, `inapplicable_field`. Inapplicability includes non-exec args, ordinary actor-only fields, disabled-capture nonce and extraneous extension operands. |
| Actor and equipment | `unsupported_sandbox_mode`, `unsupported_equipment`, `unknown_actor`, `empty_entitlement`, `duplicate_entitlement`, `invalid_termination_dependency`, `empty_equipment_overrides`, `relative_equipment_path`. |
| Extension grammar and ownership | `unsupported_extension_action`, `unsupported_extension_family`, `unsupported_extension_authority`, `relative_extension_target`, `empty_reference`, `duplicate_reference`, `unknown_token_reference`, `unknown_delivery_reference`, `unknown_handle_reference`, `wrong_owner_reference`, `repeated_release` and `extension_exec_unsupported` for reference assignment, ownership, release and exec participation. |
| Capacity | `admission_refused`; exact count, unit and available association are in admission_failure. |

Each code's condition remains attached to its owning input rule. This list supplies current examples for the open code vocabulary.

### Compound-error precedence controls {compound_order: gap}

```contract
kind: "evidence"
```

The source defines deterministic branch-local precedence. Paired controls covering every combination of identity, unknown fields, capacity and semantic errors remain to be assembled; this draft credits only the inspected identity and bounded-path controls.

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerRequestFailure"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerService.swift", "symbol": "requestDecodeFailure"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerCoding.swift", "symbol": "rejectUnknownRequestKeys"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "admitSpecimen"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Read identity-before-unknown, unknown-field and actor parameter-path assertions. The code examples are source-derived, with the reference-family details owned by extensions."
check: [{"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
```



## Controller request refusal {controller: subject}

```contract
record: "rust.RequestFailure"
as: "controller"
```

The controller supplies this shape for its JSON, assertion, selector and augmentation boundaries. Its location has the same bounded whole-path meaning as the runner shape.

### code {code: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["invalid_json", "missing_field", "missing_value", "type_mismatch", "unknown_field", "unsupported_contract", "admission_refused"]
unknown: "An unfamiliar code remains an unclassified refusal category; its producer text and path are retained as evidence."
```

Producer's refusal category. Current categories identify syntax, required values, contract mismatch, closed-field or plan meaning, and capacity failures.

### path {path: field}

Object keys and decimal array indexes locating the rejected input; [] names the root. Retain the entire path only through <!-- span limits.request_failure_path_components.value_unit -->8 items<!-- /span -->, with each component through <!-- span limits.request_failure_path_component.value_unit -->63 UTF-8 bytes<!-- /span -->; otherwise null withholds it.

### expected_contract {expected_contract: field}

Current expected public identity supplied for refusal at `contract`; omitted otherwise. It identifies the receiver's expected assertion.

### Controller pre-invocation refusal {consequence: acts}

```contract
who: "controller"
where: "CLI preparation"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: For malformed JSON, missing/wrong assertion, malformed selector values or augmentation refusal, report bad_request and exit 1 before client invocation. Argument parsing, missing/unreadable input file and target-resolution errors report tool_error and exit 2. Preserve a specimen dossier for the preparation reached.
uses: ["request.options", "policy.augments"]
```

CLI argument parsing precedes reading and gating the file. Target resolution errors take precedence over an augment error after dossier preparation. These results identify local refusal, while the client capture owns whether a later invocation was attempted.

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/request_patch.rs", "symbol": "validate_contract"}, {"path": "controller/src/run_flow.rs", "symbol": "bad_request"}, {"path": "controller/src/run_flow.rs", "symbol": "parse_arguments"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
check: [{"path": "controller/src/request_patch.rs", "symbol": "request_contract_is_exact_and_required", "form": "test"}, {"path": "controller/src/request_patch.rs", "symbol": "request_failure_path_components_use_utf8_bytes_and_withhold_the_whole_path", "form": "test"}, {"path": "controller/src/request_patch.rs", "symbol": "request_failure_path_depth_retains_eight_and_withholds_nine", "form": "test"}]
```



## Projected request refusal {projection: subject}

```contract
record: "rust.RequestFailureProjection"
as: "projection"
```

The controller's run data projects either its own request refusal or the admitted runner reply's request_failure. Serialization emits the selected record directly, preserving its code, path and optional expected_contract.

### Controller variant {controller: definition}

```contract
defines: "record"
```

The `Controller` variant carries `rust.RequestFailure` from local preparation.

### Runner variant {runner: definition}

```contract
defines: "record"
```

The `Runner` variant carries `PWRunnerRequestFailure` from the admitted host reply.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/run_flow.rs", "symbol": "RequestFailureProjection"}, {"path": "controller/src/run_flow.rs", "symbol": "RequestFailureProjection::Runner"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```



## Capacity refusal {admission: subject}

```contract
record: "PWRunnerAdmissionFailure"
as: "admission"
```

Counts describe the complete submitted value. The reply uses the same admission rules to select a refusal and to decide which metadata it can echo.

### origin {origin: field}

Admission authority. Current pre-launch capacity refusals use `runner_host`.

### field {field: field}

The capacity rule's field name, including actor policy ownership where retained.

### actual {actual: field}

Measured submitted count in the named unit.

### maximum {maximum: field}

Maximum accepted count in the same unit; embedded-NUL rules use zero.

### unit {unit: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["utf8_bytes", "items", "nul_bytes"]
```

`utf8_bytes` counts encoded string bytes, `items` counts collection members, and `nul_bytes` counts embedded zero bytes in a native C-string input.

### step_id {step_id: field}

Associated step label when it is independently safe to echo; withheld when the label itself fails its bound.

### step_index {step_index: field}

Flattened probe position when the capacity rule refers to a probe. The host reconstructs phase/action paths from the original plan.

### parameter_key {parameter_key: field}

Affected parameter key only when it can be echoed in full within its own key bound. Key failures withhold the key; value failures may retain a safe key.

### index {index: field}

Associated item position, such as argv or phase position, supplied by the specific capacity rule.

### Sanitize every echoed field {echo: acts}

```contract
who: "host"
where: "capacity-refusal reply assembly"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Independently inspect every echoed metadata value: replace an unsafe specimen_id with <admission_refused>, omit unsafe run_kind, use unknown for unsafe ordinary policy format, drop unsafe override paths, and withhold unsafe step IDs or parameter keys. Preserve the exact capacity counts.
```

A parameter key can fit the parameter capacity yet exceed the smaller path-component bound. Such a refusal may retain admission_failure.parameter_key while request_failure.path is null. The path is withheld as a whole rather than shortened into another input location.

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "admissionRefusalReply"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "requestCapacityFailure"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerAdmissionFailure"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Read actor parameter count, UTF-8 boundary, NUL, safe-key and path-withholding controls. Other capacity fixtures are inherited evidence until release validation."
check: [{"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
```



## Refusal and unavailable-prediction examples {examples: subject}



### Misspelled capture request {misspelling: example}

Given a correctly asserted ordinary specimen, a policy member `capture_compiled_profiel` is an unknown field. The host returns `bad_request`, with code `unknown_field` and path `["policy","capture_compiled_profiel"]`; the controller exits 1. A worker or validator is not launched for this refusal. Correcting the spelling to `capture_compiled_profile: true` also requires a valid `capture_nonce`.

A target-absence check made by a teaching control is separate evidence of the file state. The structured refusal identifies the stopped admission boundary.

### Absent query path and successful creation {absent_path: example}

A paired probe can query `file-write-create` with a path that does not exist at planning time, then attempt `file/create` at that path. The planner reports `prediction_unavailable`; the attempt remains eligible to run. A successful native create/open and an independent newly-created-file check answer different observations. Later realpath diagnostics can resolve a path the earlier query planner could not resolve.

### Example workflow evidence {workflow: gap}

```contract
kind: "evidence"
```

The request example corpus and its decode/admission harness were read. Full CLI/XPC execution, target-before/after observations and guide recovery commands for these examples must be checked at the release boundary; this draft credits no live effect.

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerCoding.swift", "symbol": "rejectUnknownRequestKeys"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "pathFilterIsUnresolvable"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_file_create"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Read the corpus-loop assertions and relevant producer branches. Runtime file-effect assertions were not read or executed in this drafting pass."
check: [{"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
```



## Failures after invocation {later: subject}

Later failures have different consequences from pre-child input refusal. Their owning transport, lifecycle and reporting records preserve the boundary actually observed.

### Distinguish a stopped boundary {boundaries: definition}

```contract
defines: "event"
```

A client `xpc_timeout` records expiry of the client's wait without a host reply. A host `runner_timeout` may arrive in a successfully delivered client reply, with client exit 0 and controller exit 1. The host timeout includes policy-transfer and worker-sentinel paths.

Worker or validator launch failure belongs to the respective child record. A missing completed slot leaves its operation result unresolved. `runner_reporting_failed` carries the reporting failure's explicit retention account and original summary when available. Preserve the records that were actually received while reading each failure at its own scope.

### Late-failure evidence join {evidence: gap}

```contract
kind: "evidence"
```

The full late-outcome catalog, capture retention, reporting fallback and refusal precedence belong to the transport, reply, lifecycle and envelope surfaces. Their runtime source/check owners must support those shared distinctions during integration; this surface supplies the request-refusal account.

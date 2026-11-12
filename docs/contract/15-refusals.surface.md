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

Producer's refusal category.

### path {path: field}

Object keys and decimal array indexes locating the rejected input; [] names the root. Retain the entire path only through <!-- span limits.request_failure_path_components.value_unit -->8 items<!-- /span -->, with each component through <!-- span limits.request_failure_path_component.value_unit -->63 UTF-8 bytes<!-- /span -->; otherwise null withholds it.

### expected_contract {expected_contract: field}

Current expected public identity supplied for refusal at `contract`; omitted otherwise. It identifies the receiver's expected assertion.

### Refuse at the first reached boundary {select: acts}

```contract
who: ["identity.definitions.host"]
where: "request decoding and admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Report the first failure reached by the actual decoder or admission branch. Check contract before unknown root fields; at a decoded closed object choose its lexicographically first unknown key before decoding its declared fields. Complete decoded capacity checks before meaning admission.
retained_free: {"effect":{"kind":"raw_admission","reason":"Branch-local decoder traversal selects an unknown raw key before decoding declared fields; admitted values cannot reproduce that traversal."}}
```

The ordinary and actor plan branches have different required fields and ordered checks. There is one request_failure per refusal. Its code and path locate the selected problem; correcting it may reveal the next problem.

### Stop children and preserve safe metadata {consequence: acts}

```contract
effects: [set_value(reply.normalized_outcome, "bad_request"), set_value(reply.rc, 1), set_value(reply.steps, [])]
free.effect: Start no worker or validator for the refused request. Retain metadata under its independent echo rule.
who: ["identity.definitions.host"]
where: "pre-child request refusal"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
uses: ["request.specimen"]
retained_free: {"effect":{"kind":"native_protocol","reason":"Child noncreation and bounded raw metadata echo are procedural refusal obligations beside the explicit reply assignments."}}
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

### Branch-local refusal precedence {compound_order: definition}

```contract
defines: "value"
```

Each entry reports the first failure reached in its own traversal. CLI parsing, controller identity and selector checks, augmentation, host decoding, capacity and meaning admission remain distinct boundaries.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/src/run_flow.rs","symbol":"fn run(args:"},{"path":"runner/Sources/PWRunnerCore/ProbeRunner.swift","symbol":"sandboxCheckFailure"}]
pins: "Controller preparation and typed host meaning admission have their own ordered branches."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/runner_outcome_bad_request/contract.py","symbol":"refusal_workflows","form":"test"}]
limits: "The matrix checks selected neighbouring failures and their corrections through actual CLI and direct-host entries."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerRequestFailure"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerService.swift", "symbol": "requestDecodeFailure"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerCoding.swift", "symbol": "rejectUnknownRequestKeys"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "admitSpecimen"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Review of the named producer branches."
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

Producer's refusal category.

### path {path: field}

Object keys and decimal array indexes locating the rejected input; [] names the root. Retain the entire path only through <!-- span limits.request_failure_path_components.value_unit -->8 items<!-- /span -->, with each component through <!-- span limits.request_failure_path_component.value_unit -->63 UTF-8 bytes<!-- /span -->; otherwise null withholds it.

### expected_contract {expected_contract: field}

Current expected public identity supplied for refusal at `contract`; omitted otherwise. It identifies the receiver's expected assertion.

### Controller pre-invocation refusal {consequence: acts}

```contract
effects: [set_value(envelope.result.ok, False), set_value(envelope.data.runner_client, None), set_value(envelope.data.runner_result, None), set_value(envelope.data.runner_sandbox_diagnostics, None), retain_records(envelope.data.specimen)]
who: ["identity.definitions.controller"]
where: "CLI preparation"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Select bad_request for malformed JSON, missing or wrong contract assertions, malformed selector values or augmentation refusal. Select tool_error for argument parsing, missing or unreadable input and target resolution. Argument parsing precedes input reading; a retained target-resolution error takes precedence over an augmentation error. Preserve the diagnostic and structured refusal available at that stage.
uses: ["request.options", "policy.augments"]
retained_free: {"effect": {"kind": "raw_admission", "reason": "CLI and preparation failures arise before different typed inputs exist; the selected diagnostic and refusal path depend on those raw branches."}}
```

These results identify local refusal, while the client capture owns whether a later invocation was attempted.

#### Selected request refusal {request_refusal: outcome}

```contract
test: envelope.result.normalized_outcome == "bad_request"
effects: [set_value(envelope.result.exit_code, 1)]
```

#### Selected tool failure {tool_failure: outcome}

```contract
test: envelope.result.normalized_outcome == "tool_error"
effects: [set_value(envelope.result.exit_code, 2)]
```

#### Selected local class {class: condition}

```contract
test: envelope.result.normalized_outcome in ["bad_request", "tool_error"]
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/request_patch.rs", "symbol": "validate_contract"}, {"path": "controller/src/run_flow.rs", "symbol": "bad_request"}, {"path": "controller/src/run_flow.rs", "symbol": "parse_arguments"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Review of the named producer branches."
limits: "The checks cover exact identity admission and UTF-8 path-component and depth withholding."
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
who: ["identity.definitions.host"]
where: "capacity-refusal reply assembly"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Independently inspect every echoed metadata value: replace an unsafe specimen_id with <admission_refused>, omit unsafe run_kind, use unknown for unsafe ordinary policy format, drop unsafe override paths, and withhold unsafe step IDs or parameter keys. Preserve the exact capacity counts.
retained_free: {"effect":{"kind":"raw_admission","reason":"Safe refusal echo inspects malformed raw input values independently of the selected first refusal and typed request construction."}}
```

A parameter key can fit the parameter capacity yet exceed the smaller path-component bound. Such a refusal may retain admission_failure.parameter_key while request_failure.path is null.

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "admissionRefusalReply"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "requestCapacityFailure"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerAdmissionFailure"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Review of the named producer branches."
limits: "The cited controls cover actor parameter count, UTF-8 and NUL boundaries, safe keys and path withholding."
check: [{"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
```



## Refusal and unavailable-prediction examples {examples: subject}



### Misspelled capture request {misspelling: example}

Given a correctly asserted ordinary specimen, a policy member `capture_compiled_profiel` is an unknown field. The host returns `bad_request`, with code `unknown_field` and path `["policy","capture_compiled_profiel"]`; the controller exits 1. A worker or validator is not launched for this refusal. Correcting the spelling to `capture_compiled_profile: true` also requires a valid `capture_nonce`.

A target-absence check made by a teaching control is separate evidence of the file state. The structured refusal identifies the stopped admission boundary.

#### Correction workflow support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"controller/src/run_flow.rs","symbol":"fn run(args:"}
pins: "Controller refusals precede invocation at their own preparation boundaries."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/runner_outcome_bad_request/contract.py","symbol":"refusal_workflows","form":"test"}]
limits: "This owner describes the concrete correction chain; the guide presentation has its own workflow validation."
```

### Absent query path and successful creation {absent_path: example}

A paired probe can query `file-write-create` with a path that does not exist at planning time, then attempt `file/create` at that path. The planner reports `prediction_unavailable`; the attempt remains eligible to run. A successful native create/open and an independent newly-created-file check answer different observations. Later realpath diagnostics can resolve a path the earlier query planner could not resolve.

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerCoding.swift", "symbol": "rejectUnknownRequestKeys"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "pathFilterIsUnresolvable"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_file_create"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Review of the named producer branches."
limits: "The request corpus checks refusal fields; the correction workflow and independent file effects have their own support."
check: [{"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
```



## Failures after invocation {later: subject}

Later failures have different consequences from pre-child input refusal. Their owning transport, lifecycle and reporting records preserve the boundary actually observed.

### Distinguish a stopped boundary {boundaries: definition}

```contract
defines: "event"
```

A client `xpc_timeout` records expiry of the client's wait without a host reply. A host `runner_timeout` may arrive in a successfully delivered client reply, with client exit 0 and controller exit 1.

Worker or validator launch failure belongs to the respective child record. Preserve the records that were actually received while reading each failure at its own scope.

#### Later-outcome support {disposition_support: owner}

```contract
grade: "source_read"
source: [{"path":"controller/src/runner_client.rs","symbol":"parse_runner_client_output"},{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"pwRunnerReportData"},{"path":"controller/src/run_flow.rs","symbol":"admit_reply"}]
pins: "Delivery/capture precedence, successive reporting writers and controller reply admission retain separate consequences."
limits: "Constructed writer and reader controls, source-built child controls and native selected-app outcomes retain their individual evidence grades."
```

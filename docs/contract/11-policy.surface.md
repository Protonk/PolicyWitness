# Policy source, parameters and compilation {policy: surface}

```contract
syntax: 1
artifact: "Policy source, parameters and compilation"
part: "input"
goldens: ["tests/fixtures/contract/surfaces/policy.json"]
checks: ["failure_boundaries"]
```



## Worker policy input {spec: subject}

```contract
record: "PWRunnerPolicySpec"
as: "spec"
```

Each apply actor owns a separate policy. The host bounds the selected source string and parameter map before starting workers or validators.

### format {format: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["sbpl"]
```

The accepted policy representation is `sbpl`; another value is refused before worker launch.

### sbpl_source {sbpl_source: field}

Required string when applying a policy. An empty string reaches native compilation. The final source after augmentation fits <!-- span limits.policy_source.value_unit -->262,143 UTF-8 bytes<!-- /span -->, and embedded NUL is refused before child launch.

### params {params: field}

Optional string-to-string compiler parameter map. Omission, null and an empty map produce no native parameter setup. Supplied names remain open data. At most <!-- span limits.policy_parameters.value_unit -->1,024 items<!-- /span --> fit each policy, with keys bounded by <!-- span limits.parameter_key.value_unit -->127 UTF-8 bytes<!-- /span --> and values by <!-- span limits.parameter_value.value_unit -->383 UTF-8 bytes<!-- /span -->; native strings must be NUL-free.

### capture_compiled_profile {capture_compiled_profile: field}

```contract
default: false
```

When true, request a compiled-profile receipt from the worker before application and require a valid capture_nonce. Omission, null and false leave capture unrequested.

### capture_nonce {capture_nonce: field}

```contract
required_when: spec.capture_compiled_profile == True
present_when: spec.capture_compiled_profile == True
```

Required with enabled capture: exactly 32 lowercase hexadecimal characters encoding the caller's nonce. A non-null nonce with capture disabled is an inapplicable-field refusal. Receipt publication and consistency checks belong to the compiled-profile surface.

### augments {augments: field}

Controller-resolved list of named packaged SBPL fragments. Omission, null and an empty list are no-ops. The controller strips the field before delivery. The host accepts the no-op forms and refuses a nonempty unresolved list.

### Prepare native compiler input {parameters: acts}

```contract
who: ["identity.definitions.host", "identity.definitions.worker"]
where: "policy preparation and compilation"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Sort parameter keys, transport their complete strings, create native parameters only for a nonempty map, and pass each key and value through sandbox_set_param before compiling the selected source. Report setup or compile failure at the observed native stage.
retained_free: {"effect":{"kind":"native_protocol","reason":"Sorted allocation and sandbox_set_param calls define native resource setup and cleanup, not merely the final parameter map."}}
```

A supplied parameter is data for the SBPL compiler. The compiler decides how source expressions use it. Source text, selected parameter values and imported file bytes are distinct inputs.

### Parameter expressions {parameter_example: example}

A source may combine a parameter with a literal suffix:

```scheme
(version 1)
(deny default)
(allow file-read* (literal (string-append (param "ROOT") "/hosts")))
```

`"params":{"ROOT":"/etc"}` supplies the value used by this expression. An unused `OPTIONAL` parameter and a referenced but missing `ROOT` exercise different compiler paths. Inspect the native compile record for the latter's outcome.

### Parameter example observations {parameter_evidence: definition}

```contract
defines: "value"
```

The helper records parameter-map presence and count separately: omission and null decode as absent; an empty map remains present with zero entries. Native compiler examples concern the helper invocation that produced the verdict. Worker examples use the consumed source and parameter values, then observe application and the requested fresh-file effects on concrete targets. Record the selected binaries, policy and platform with each native observation.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"controller/src/bin/sbpl-check.rs","symbol":"check"}
pins: "Helper metadata and native verdict are retained together."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"controller/integration/cli_contract.rs","symbol":"sbpl_check_verdicts_follow_the_native_compiler","form":"test"},{"path":"tests/suites/runner_outcome_bad_request/contract.py","symbol":"composite_parameters","form":"test"}]
limits: "Helper omitted/null/empty neighbours and worker ROOT twins have distinct oracles; worker target bytes and descriptor identity are checked independently."
```

### Worker and helper compile classification {compile_classification: definition}

```contract
defines: "value"
```

The worker treats a null compiled-profile pointer as failure and proceeds to capture and application with a non-null profile. The helper requires a profile and no native diagnostic for success, and frees the returned profile, parameters and diagnostic it owns. A simultaneous profile and diagnostic therefore has different classifications at these two boundaries. The helper branch has an injected native-return control; native occurrence of the worker combination remains unobserved.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"sandbox_compile_string(policy_buf"},{"path":"controller/src/bin/sbpl-check.rs","symbol":"compile_with"}]
pins: "Worker pointer acceptance and helper diagnostic-sensitive classification are separate producer rules."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"controller/src/bin/sbpl-check.rs","symbol":"a_profile_succeeds_alone_and_fails_beside_an_error_buffer","form":"test"}]
limits: "Injected helper returns check verdict and free counts. Worker simultaneous profile/diagnostic occurrence has source support only."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerPolicySpec"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "policyMeaningFailure"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "workerParamsFromPolicy"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "sandbox_set_param"}]
pins: "The adjacent field meanings and operations follow the named implementation."
limits: "Decoder, meaning checks, parameter ordering, worker parameter snapshot/setup and compilation branches read. Native execution is not credited."
```



## Augment resolution {augments: subject}

Augments select packaged source fragments from `Contents/Resources/Augments/<name>.sb`. Names are nonempty ASCII letters, digits or underscore. The resolver treats the fragment contents as source text.

### Resolve and append {resolve: acts}

```contract
who: ["identity.definitions.controller"]
where: "saved-file policy normalization"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: For a nonempty augment list require a string source, validate every name, read the named resources in requested order and append a newline plus each fragment. Replace the policy source only after every requested read succeeds. Remove augments from the held policy before submission.
retained_free: {"effect":{"kind":"native_protocol","reason":"Ordered file reads, newline splicing and replacement after every successful read define atomic in-memory augmentation."}}
```

An empty string source is accepted at this normalization boundary. An unavailable resource produces `augment_unavailable` at the offending list element. Invalid names produce `invalid_augment_name`. A wrong list or element type produces `type_mismatch`. The original file remains unchanged because resolution edits the held JSON value.

### Resolve actor policies in request order {actors: acts}

```contract
who: ["identity.definitions.controller"]
where: "actor policy normalization"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Resolve each actor policy object in actor order and stop after the first augment refusal. Retain each visited actor's original and selected source in its dossier. Mode and policy applicability are judged later by host admission.
retained_free: {"effect":{"kind":"native_protocol","reason":"The first failed actor augmentation controls which later actor policies are never visited; the partial dossier retains visited reads."}}
```



### Packaged exec baseline {exec_baseline: definition}

```contract
defines: "value"
```

`exec_baseline` appends these source rules:

```scheme
(allow process-exec*)
(allow process-fork)
(allow file-read*)
```

The `file-read*` allowance is unconditional. Using this augment changes the selected policy's file-read authority and can mask the denial a file-read experiment intended to observe. Its documented derivation used macOS 14.8.3, build 23J220, and the repository's dynamic exec helper.

### Augment evidence scope {augment_semantics: definition}

```contract
defines: "value"
```

The resolver validates all names before file access, reads fragments in requested order and appends each with a leading newline. Native behavior is scoped to the exact fragment bytes, base policy and macOS build observed. The packaged exec_baseline fragment includes broad file-read allowance; additional prerequisites and SBPL composition on another platform require their own observations.

#### Disposition support {disposition_support: owner}

```contract
grade: "source_read"
source: {"path":"controller/src/augments.rs","symbol":"resolve_policy_augments"}
pins: "Resolver validation, ordered reads and source append define the produced policy text."
context: "Static review of the cited production branches."
limits: "Resolver correctness and selected native fragment observations have distinct scopes."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/augments.rs", "symbol": "resolve_policy_augments"}, {"path": "controller/src/augments.rs", "symbol": "resolve_actor_augments"}, {"path": "runner/augments/exec_baseline.sb", "symbol": "(allow process-exec*)"}]
pins: "The adjacent field meanings and operations follow the named implementation."
context: "Review of the named producer branches."
limits: "Read append/no-partial-replacement and actor-order controls. The packaged baseline source was read; its historical derivation is inherited evidence."
check: [{"path": "controller/src/augments.rs", "symbol": "applies_and_strips_field", "form": "test"}, {"path": "controller/src/augments.rs", "symbol": "unknown_name_is_bad_request_without_partial_apply", "form": "test"}, {"path": "controller/src/augments.rs", "symbol": "actor_policies_resolve_at_their_own_paths_and_stop_at_the_first_refusal", "form": "test"}]
```



## Standalone compiler-helper request {helper_request: subject}

```contract
record: "rust.CheckRequest"
as: "helper_request"
```

`sbpl-check --request <path>` reads a policy request file; `--request -` reads stdin. This decoder selects the policy object and ignores other root fields. It accepts input without a public-contract assertion.

### policy {policy: field}

Required compiler-helper policy object.

### Read helper input {read: acts}

```contract
who: ["identity.definitions.helper"]
where: "standalone argument, read and JSON boundary"
entry: ["standalone_helper", "controller_helper_stdin"]
recipient: ["caller", "report_reader"]
report: ["helper_envelope", "stderr"]
free.effect: Use the helper policy decoder. Usage errors, input-read errors and JSON/decode errors exit 2 and report on stderr. Successfully decoded requests proceed to helper admission and produce an envelope.
retained_free: {"effect":{"kind":"raw_admission","reason":"Usage, byte-read and decode failures occur before the helper envelope and have separate stderr/process-exit paths."}}
```



### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/bin/sbpl-check.rs", "symbol": "CheckRequest"}, {"path": "controller/src/bin/sbpl-check.rs", "symbol": "fn main"}]
pins: "The adjacent field meanings and operations follow the named implementation."
```



## Compiler-helper policy {helper_policy: subject}

```contract
record: "rust.CheckPolicy"
as: "helper_policy"
at: ["helper_request.policy"]
```

The helper decoder ignores policy members outside this record, including capture and augment requests. Controller fallback supplies the already normalized policy source.

### format {format: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["sbpl"]
```

Require `sbpl` at helper admission.

### sbpl_source {sbpl_source: field}

Require a string source at helper admission; allow an empty string for the native compiler. Bound its UTF-8 bytes by <!-- span limits.helper_source.value_unit -->4,194,304 bytes<!-- /span -->, then require a NUL-free C string.

### params {params: field}

Optional string map. Null and absence mean no map; an empty map is present for reporting but needs no native parameter object. Reject embedded NUL in each key and value before inventory or native calls.

### Helper admission order {admit: acts}

```contract
who: ["identity.definitions.helper"]
where: "pre-inventory admission"
entry: ["standalone_helper", "controller_helper_stdin"]
recipient: ["caller", "report_reader"]
report: ["helper_envelope"]
free.effect: Stop at the first admission refusal. After format, source-presence and source-extent checks pass, construct the source C string and then parameter key/value C strings in map order; a failed conversion prevents later conversions and retains its diagnostic.
retained_free: {"effect":{"kind":"native_protocol","reason":"C-string construction and its first diagnostic remain preparation operations; the decoded field refusal predicates and envelope assignments are stated in the ordered cases."}}
selection: "first_match"
bind.k: helper_policy.params
match.k: contains(k, "\u0000") or contains(helper_policy.params[k], "\u0000")
```

#### Unsupported format {format: outcome}

```contract
test: helper_policy.format != "sbpl"
effects: [set_value(helper_envelope.result.ok, False), set_value(helper_envelope.result.exit_code, 1), set_value(helper_envelope.result.normalized_outcome, "bad_request"), set_value(helper_envelope.data.policy_sha256, None), set_value(helper_envelope.data.compile, None), set_value(helper_envelope.data.import_inventory, None)]
```

#### Missing source {source: outcome}

```contract
test: absent(helper_policy.sbpl_source)
effects: [set_value(helper_envelope.result.ok, False), set_value(helper_envelope.result.exit_code, 1), set_value(helper_envelope.result.normalized_outcome, "bad_request"), set_value(helper_envelope.data.policy_sha256, None), set_value(helper_envelope.data.compile, None), set_value(helper_envelope.data.import_inventory, None)]
```

#### Oversized source {extent: outcome}

```contract
test: present(helper_policy.sbpl_source) and utf8_length(helper_policy.sbpl_source) > limit("helper_source")
effects: [set_value(helper_envelope.result.ok, False), set_value(helper_envelope.result.exit_code, 1), set_value(helper_envelope.result.normalized_outcome, "policy_too_large"), set_value(helper_envelope.data.policy_sha256, None), set_value(helper_envelope.data.compile, None), set_value(helper_envelope.data.import_inventory, None)]
```

#### Source NUL {source_nul: outcome}

```contract
test: present(helper_policy.sbpl_source) and contains(helper_policy.sbpl_source, "\u0000")
effects: [set_value(helper_envelope.result.ok, False), set_value(helper_envelope.result.exit_code, 1), set_value(helper_envelope.result.normalized_outcome, "bad_request"), set_value(helper_envelope.data.policy_sha256, None), set_value(helper_envelope.data.compile, None), set_value(helper_envelope.data.import_inventory, None)]
```

#### Parameter NUL {parameter_nul: outcome}

```contract
test: present(helper_policy.params) and matches(k) > 0
effects: [set_value(helper_envelope.result.ok, False), set_value(helper_envelope.result.exit_code, 1), set_value(helper_envelope.result.normalized_outcome, "bad_request"), set_value(helper_envelope.data.policy_sha256, None), set_value(helper_envelope.data.compile, None), set_value(helper_envelope.data.import_inventory, None)]
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/bin/sbpl-check.rs", "symbol": "admit"}, {"path": "controller/src/bin/sbpl-check.rs", "symbol": "CheckPolicy"}]
pins: "The adjacent field meanings and operations follow the named implementation."
```



## Compiler-helper data {check_data: subject}

```contract
record: "rust.CheckData"
as: "check_data"
part: "report"
at: ["helper_envelope.data"]
```



### policy_format {policy_format: field}

The decoded policy format, including a refused format.

### policy_sha256 {policy_sha256: field}

SHA-256 of the admitted source's UTF-8 bytes; null when input admission failed before hashing.

### macos_build_version {macos_build_version: field}

The host macOS build observed by the helper, or null when unavailable.

### params_present {params_present: field}

True when params decoded as a map, including an empty map; false for omission or null.

### params_count {params_count: field}

Number of decoded parameter-map entries.

### compile {compile: field}

The last native stage attempted and its result. Null means the helper refused the input before native setup or compilation.

### import_inventory {import_inventory: field}

The helper's literal-import walk performed before native compilation. Null means admission prevented the walk; an empty records list is a performed walk with no import records.

### Inventory, compile and report {run_compile: acts}

```contract
who: ["identity.definitions.helper"]
where: "admitted diagnostic compilation"
entry: ["standalone_helper", "controller_helper_stdin"]
recipient: ["caller", "report_reader"]
report: ["helper_envelope"]
free.effect: Inventory imports, prepare native parameters when needed, then compile the admitted source. Preserve the inventory even when native compilation fails.
retained_free: {"effect":{"kind":"native_protocol","reason":"The import walk and native parameter/compile calls occur in order; the verdict from the retained last-stage record is defined separately."}}
```

The helper compiles in its own process. The fallback capture reports this independent attempt alongside the transport result and any retained worker evidence.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/bin/sbpl-check.rs", "symbol": "check"}, {"path": "controller/src/bin/sbpl-check.rs", "symbol": "CheckData"}]
pins: "The adjacent field meanings and operations follow the named implementation."
```

### Select the helper verdict {verdict: reports}

```contract
who: ["identity.definitions.helper"]
where: "last native-stage record to helper result"
entry: ["standalone_helper", "controller_helper_stdin"]
recipient: ["report_reader"]
report: ["helper_envelope"]
when: present(helper_envelope.data.compile)
selection: "first_match"
```
#### Successful last stage {ok: outcome}

```contract
test: helper_envelope.data.compile.ok
effects: [set_value(helper_envelope.result.ok, True), set_value(helper_envelope.result.exit_code, 0), set_value(helper_envelope.result.normalized_outcome, "ok"), set_value(helper_envelope.result.error, None)]
```
#### Compile failure with a diagnostic {compile_diagnostic: outcome}

```contract
test: helper_envelope.data.compile.stage == "compile" and present(helper_envelope.data.compile.error)
effects: [set_value(helper_envelope.result.ok, False), set_value(helper_envelope.result.exit_code, 1), set_value(helper_envelope.result.normalized_outcome, "compile_error"), set_value(helper_envelope.result.error, helper_envelope.data.compile.error)]
```
#### Compile failure without a diagnostic {compile_no_diagnostic: outcome}

```contract
test: helper_envelope.data.compile.stage == "compile"
effects: [set_value(helper_envelope.result.ok, False), set_value(helper_envelope.result.exit_code, 1), set_value(helper_envelope.result.normalized_outcome, "compile_error"), set_value(helper_envelope.result.error, "sandbox_compile_string returned NULL without a diagnostic")]
```

The helper supplies its fixed explanatory summary when the native call returned no diagnostic.
#### Native setup failure {setup: outcome}

```contract
test: True
effects: [set_value(helper_envelope.result.ok, False), set_value(helper_envelope.result.exit_code, 1), set_value(helper_envelope.result.normalized_outcome, "setup_error"), set_value(helper_envelope.result.error, helper_envelope.data.compile.error)]
```
#### Source support {support: owner}

```contract
grade: "source_read"
source: {"path":"controller/src/bin/sbpl-check.rs","symbol":"verdict"}
pins: "The helper selects its result from the last native-stage record."
```

### Decoded policy metadata {metadata: reports}

```contract
who: ["identity.definitions.helper"]
where: "decoded helper input to report metadata"
entry: ["standalone_helper", "controller_helper_stdin"]
recipient: ["report_reader"]
report: ["helper_envelope"]
effects: [set_value(check_data.policy_format, helper_request.policy.format), set_value(check_data.params_present, present(helper_request.policy.params))]
```
#### Present parameter map {present: effect}

```contract
on: "always"
when: present(helper_request.policy.params)
effects: set_value(check_data.params_count, count(helper_request.policy.params))
```
#### Absent parameter map {absent: effect}

```contract
on: "always"
when: absent(helper_request.policy.params)
effects: set_value(check_data.params_count, 0)
```
#### Source support {support: owner}

```contract
grade: "source_read"
source: {"path":"controller/src/bin/sbpl-check.rs","symbol":"check"}
pins: "Metadata retains decoded format and optional-map presence/count, including an empty present map."
```

## Last native compile stage {compile: subject}

```contract
record: "rust.CompileRecord"
as: "compile"
part: "report"
at: ["helper_envelope.data.compile"]
```



### stage {stage: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["params_create", "param_set", "compile"]
```

Last native stage attempted: parameter object creation, one parameter assignment, or source compilation. `compile` means required parameter setup completed.

### ok {ok: field}

Whether that last stage supplied the helper's successful native result. Compilation succeeds only when the profile is non-null and the native diagnostic pointer is null.

### error {error: field}

At setup failure, helper text identifies the call and, for parameter assignment, the key. At compile, copy the native diagnostic as lossily decoded UTF-8, preserving an empty diagnostic as an empty string. A null profile with no diagnostic leaves this field null and supplies a separate explanatory summary.

### Release native resources {release: acts}

```contract
who: ["identity.definitions.helper"]
where: "native compile-call completion"
entry: ["standalone_helper", "controller_helper_stdin"]
recipient: ["caller", "report_reader"]
report: ["helper_envelope"]
free.effect: Free every acquired parameter object, returned profile and native error buffer. Treat a non-null diagnostic as compile failure even when a profile was returned. Preserve the native diagnostic separately from the helper summary.
retained_free: {"effect":{"kind":"native_protocol","reason":"Acquired native pointers and diagnostic buffers have ownership and free obligations not represented by final result records."}}
```

#### Retained compile diagnostic {diagnostic: condition}

```contract
test: implies(compile.stage == "compile" and present(compile.error), compile.ok == False)
```

An empty native diagnostic remains present and therefore also rules out helper compile success.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/bin/sbpl-check.rs", "symbol": "compile_with"}, {"path": "controller/src/bin/sbpl-check.rs", "symbol": "CompileRecord"}]
pins: "The adjacent field meanings and operations follow the named implementation."
limits: "Native wrapper branches read. Scripted native-result controls and platform execution still need to be joined as graded owners."
```



## Literal import inventory {imports: subject}

```contract
record: "rust.ImportInventory"
as: "imports"
part: "report"
```

Absolute import names are checked as supplied. Other names are sought first under `/System/Library/Sandbox/Profiles`, then `/usr/share/sandbox`, with the literal name unchanged. The resolver follows literal imports recursively; an unevaluable import argument, unreadable/nonregular file or invalid UTF-8 scan input records an incomplete inventory.

### records {records: field}

Observed import records sorted by resolved path (empty for unresolved), then literal name. Each resolved file is opened once, checked as a regular file, and its held bytes are both hashed and scanned. Canonical resolved files and unresolved names are deduplicated.

### truncated {truncated: field}

True when the walk reached its <!-- span limits.helper_import_depth.value_unit -->8 levels<!-- /span --> depth bound or <!-- span limits.helper_import_count.value_unit -->64 records<!-- /span --> record bound; retained records describe the partial walk.

### cycle {cycle: field}

First cycle found by revisiting a canonical path already in the active traversal chain, reported in literal import-name order. Null means the walk found no cycle.

### policy_closure_sha256 {policy_closure_sha256: field}

SHA-256 of source bytes, byte 0x1F, then newline-joined sorted strings of each successfully hashed resolved path, one space and its SHA-256. The separator is included for an empty inventory. Failed imports remain error records and contribute no path/hash line.

### Separate reads and their identities {holds: acts}

```contract
who: ["identity.definitions.controller", "identity.definitions.helper", "identity.definitions.worker"]
where: "policy preparation and import reads"
entry: ["cli_run", "standalone_helper", "xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["run_envelope", "helper_envelope", "runner_reply"]
free.effect: Bind each digest to the bytes held by its producing read. The controller dossier walk, fallback helper walk and worker native compiler perform their own reads. Preserve import errors and bounds beside each inventory.
retained_free: {"effect":{"kind":"native_protocol","reason":"Each hash belongs to bytes held by a distinct producing read; final equal hashes do not establish read ownership or simultaneity."}}
```

The saved file is held once by the controller, selected source is held after augmentation, and the serialized request is held once for delivery. Files named by imports can change between these independent reads. A literal inventory describes the producer's walk; the worker compiled-profile receipt has its own observation boundary.

### Literal import evidence scope {native_import_agreement: definition}

```contract
defines: "value"
```

The inventory walks literal imports using its documented two-directory search order and records the bytes read during that walk. The directory order is a platform convention. Native compilation examples establish their selected literal imports; collision precedence, macro-generated dependencies and files changing between independent reads retain their own evidence limits.

#### Disposition support {disposition_support: owner}

```contract
grade: "source_read"
source: {"path":"controller/src/sbpl_imports.rs","symbol":"resolve_import_path"}
pins: "The scanner follows IMPORT_SEARCH_PATHS and records each resolved file read."
context: "Static review of the cited production branches."
limits: "The source records that collision precedence was not established by the cited platform exploration."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/sbpl_imports.rs", "symbol": "resolve_imports"}, {"path": "controller/src/sbpl_imports.rs", "symbol": "read_regular_file"}, {"path": "controller/src/sbpl_imports.rs", "symbol": "compute_closure_hash"}, {"path": "controller/src/bin/sbpl-check.rs", "symbol": "ImportInventory"}]
pins: "The adjacent field meanings and operations follow the named implementation."
limits: "Full inventory traversal and hashing implementation read. Native search-order observations are inherited from the source comments, not reproduced here."
```



## Fallback helper capture {fallback: subject}

```contract
record: "rust.PolicyCheckCapture"
as: "fallback"
part: "report"
```



### status {status: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["unavailable", "capture_error", "parse_error", "tool_error", "invalid_reply", "ok", "compile_error", "setup_error", "bad_request", "policy_too_large"]
unknown: "A nonempty unfamiliar helper outcome is copied when kind and public identity are supported; its meaning remains producer-supplied."
```

Capture result, or the exact normalized_outcome from a supported helper envelope. Current capture statuses are unavailable, capture_error, parse_error, tool_error and invalid_reply.

### tool_exit_code {tool_exit_code: field}

Helper process exit code, or the capture's fallback value when unavailable. It remains independent of a supported envelope's declared outcome.

### envelope {envelope: field}

Whole parsed helper envelope retained unchanged when stdout parsed, including unsupported envelopes. Null means no retained parsed object.

### stdout_raw {stdout_raw: field}

Retained textual stdout used for capture diagnosis.

### stdout_parse_error {stdout_parse_error: field}

Parse diagnosis when retained stdout could not be decoded as the helper JSON value.

### stdout_truncated {stdout_truncated: field}

Whether stdout retention truncated the child's output; truncation prevents interpreting a parsed prefix as the complete reply.

### stdout_capture_error {stdout_capture_error: field}

Capture loss diagnosis, which takes precedence over parsing and helper interpretation.

### stdout_bytes_received {stdout_bytes_received: field}

Count of stdout bytes observed by capture.

### stdout_bytes_retained {stdout_bytes_retained: field}

Count of stdout bytes retained within the capture limit.

### stderr_bytes_received {stderr_bytes_received: field}

Count of stderr bytes observed by capture.

### stderr_bytes_retained {stderr_bytes_retained: field}

Count of stderr bytes retained within the capture limit.

### capture_limit_bytes {capture_limit_bytes: field}

Per-stream retention limit, <!-- span limits.policy_helper_output.value_unit -->8,388,608 bytes<!-- /span -->.

### stderr {stderr: field}

Retained stderr text, including diagnostic output when the helper produced no envelope.

### stderr_truncated {stderr_truncated: field}

Whether stderr exceeded its retained capture capacity.

### Fallback eligibility and classification {classify: acts}

```contract
who: ["identity.definitions.controller"]
where: "admitted client capture after xpc_error"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Invoke the fallback helper when client transport admission is accepted, request delivery has no error, and the admitted client capture has terminal xpc_error. Deliver the held request on stdin. Report launch or delivery failure as unavailable; only after successful launch and delivery apply capture_error, parse_error, absent-output tool_error, then raw envelope identity/kind validation. Copy a supported envelope's nonempty outcome into status.
retained_free: {"effect":{"kind":"native_protocol","reason":"Launch/delivery success is an independent event missing from PolicyCheckCapture; the unavailable constructor can also carry a capture error. The parsed envelope remains raw JSON for kind, identity and outcome admission."}}
```

Support requires kind `sbpl_check`, the current non-unbound `build.contract`, and a nonempty string normalized_outcome. The capture preserves the envelope and helper process exit independently; compiler observations retain their own process owner.

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/policy_check.rs", "symbol": "parse_policy_check_output"}, {"path": "controller/src/policy_check.rs", "symbol": "supported_outcome"}, {"path": "controller/src/run_flow.rs", "symbol": "fallback_policy_check"}, {"path": "controller/src/runner_client.rs", "symbol": "pub fn fallback_eligible"}, {"path": "controller/src/run_flow.rs", "symbol": "let actor_policies:"}]
pins: "The adjacent field meanings and operations follow the named implementation."
context: "Review of the named producer branches."
limits: "Capture parsing, fallback eligibility and call sites, supported-outcome control and constructed fallback-selection control read; no execution credited. The malformed actor-mode policy-object path is source-read. Detailed text-byte capture mechanics are shared with the transport surface."
check: [{"path": "controller/src/policy_check.rs", "symbol": "supported_outcomes_are_copied_into_status_without_a_second_verdict", "form": "test"}, {"path": "controller/src/run_flow.rs", "symbol": "fallback_compilation_is_requested_only_for_an_admitted_xpc_error", "form": "test"}]
```

## Per-actor fallback capture {actor_check: subject}

```contract
record: "rust.ActorPolicyCheck"
as: "actor_check"
part: "report"
```

When fallback is eligible, the controller checks each actor carrying a policy object in request order, sending a separate policy-only request. A malformed mode remains a host-admission question; the controller collected these policy objects before host execution.

### actor_id {actor_id: field}

Actor label copied from the policy-bearing actor declaration when it is a string; null otherwise.

### policy_check {policy_check: field}

Independent helper capture for this actor's selected policy object.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/run_flow.rs", "symbol": "actor_fallback_checks"}, {"path": "controller/src/run_flow.rs", "symbol": "actor_policies"}]
pins: "The adjacent field meanings and operations follow the named implementation."
```

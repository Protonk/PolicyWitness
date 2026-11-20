# Compiled-profile receipts {profile: surface}

```contract
syntax: 1
artifact: "Compiled-profile receipts"
goldens: ["tests/fixtures/contract/surfaces/profile.json", "tests/fixtures/contract/compiled_profile.json"]
checks: ["runner_unit", "unit", "failure_boundaries"]
entry: ["cli_run", "runner_verify", "direct_xpc"]
recipient: ["controller", "xpc_caller", "cli_caller"]
report: ["runner_reply"]
```

The host reports the result of an optional capture of the worker's compiled policy before application.

## Receipt {receipt: subject}

```contract
record: "CompiledProfileCapture"
as: "receipt"
bind.a: reply.actors
at: ["reply.compiled_profile", "reply.actors[a].compiled_profile"]
coverage: "complete"
```

The containing reply's producer contract identifies the receipt's contract.

### Status {status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["captured", "unavailable"]
```

`captured` states that the host's capture checks passed. `unavailable` states that a capture condition failed. The host evaluates application and worker completion before it reads any capture record. An `unavailable` receipt therefore does not report whether the worker copied the object, and a completed copy is withheld when application was not observed to succeed or the worker did not complete cleanly.

### Reason {reason: field}

```contract
where: "controller_reply_admission"
vocabulary: "open"
listed: "illustrative"
values: ["successful_application_unconfirmed", "worker_not_complete", "capture_nonce_mismatch"]
unknown: "retained as the host's reason string"
```

The host names the first failing capture condition. The controller's label check accepts the carried reason string. `worker_capture_refused` covers every worker capture status other than captured: an unsupported type or reserved word, an empty or over-limit extent, a null byte pointer, an unreadable object, and malformed consumed input. The receipt does not say which. The host's extent and type condition repeats checks the worker makes before it records captured status.

### Worker process {worker_pid: field}

The process identifier of the worker whose output the host collected.

### Capture producer {producer: field}

`worker` on a captured receipt names the component whose program copies the bytes. The host writes this value on every captured receipt; no worker publication carries it.

### Capture stage {capture_stage: field}

`before_apply` on a captured receipt names the position of the copy in the worker's program, between compilation and application. The host writes this value on every captured receipt; it is not a recorded observation of that order.

### Request nonce {request_nonce: field}

The host returns the request's capture nonce after comparing it with the worker's recorded bytes. A comparison with a separately retained request nonce supplies a consumer's request association; the controller's carried-label check has no request-nonce operand. The nonce enters no compiled byte and no digest; the comparison associates the receipt with the reply that carries it.

### Profile type {profile_type: field}

The supported compiler result representation is `0`.

### Bytecode length {bytecode_length: field}

The number of raw bytes copied from the compiled object, positive and at most <!-- span limits.compiled_profile.value_unit -->1,048,576 bytes<!-- /span -->. It counts the decoded bytes represented by `bytecode_b64`, separately for each opted-in worker.

#### Captured byte extent {captured: condition}

```contract
test: implies(receipt.status == "captured", present(receipt.bytecode_length) and receipt.bytecode_length > 0 and receipt.bytecode_length <= limit("compiled_profile"))
```

### Bytecode digest {bytecode_sha256: field}

The host's SHA-256 digest of the captured bytes, presented as lowercase hexadecimal.

### Bytecode {bytecode_b64: field}

The bytes copied from the compiler object passed to `sandbox_apply`, presented as base64. The worker reads that object through a fixed four-member view (type, reserved word, byte pointer, length) of a private structure. The receipt establishes that the bytes read this way matched their recorded length and digest. It does not establish the structure's layout on the running system, or which bytes application submitted.

#### Captured payload extent {extent: condition}

```contract
when: receipt.status == "captured"
test: byte_length(receipt.bytecode_b64) == receipt.bytecode_length
```

### Source digest {source_sha256: field}

The SHA-256 digest of the UTF-8 C-string source passed to compilation, presented as lowercase hexadecimal. The host compares it with its supplied source bytes; an embedded NUL cannot establish the full source identity.

### Source length {source_length: field}

The supplied source's UTF-8 byte count.

### Parameter digest {params_sha256: field}

The order-independent digest of parameter names and values consumed by the worker, presented as lowercase hexadecimal.

### Parameter count {parameter_count: field}

The count of parameters supplied to the worker.

### Captured input identity {identity: definition}

Each parameter pair digest hashes its little-endian 32-bit key length, key bytes, little-endian 32-bit value length and value bytes. The parameter digest hashes the little-endian 32-bit count followed by sorted pair digests. The identity covers the source string and the parameter strings passed to the compiler. No receipt field identifies a file the compiler reads, so equal source and parameter identities do not imply equal bytecode; [the import inventories](#contract-policy-imports-holds) do not identify those files either.

### Receipt presence {presence: reports}

```contract
who: ["identity.definitions.host"]
where: "worker_collection"
recipient: ["controller", "xpc_caller"]
free.when: Capture was requested for this worker and worker output was collected.
free.effect: Include the optional capture receipt in that worker output.
retained_free: {"when": {"kind": "native_protocol", "reason": "The selected ordinary or actor policy supplies this worker capture request. Collection supplies the worker output consumed before receipt construction."}, "effect": {"kind": "native_protocol", "reason": "Receipt insertion occurs only for collected capture output, which is an intermediate producer object rather than a final admitted report."}}
```

A failure that produces no worker output leaves the receipt absent; absence has several possible causes.

### The host decides capture availability {host: reports}

```contract
failure: "first"
who: ["identity.definitions.host"]
where: "collected worker capture decoding"
recipient: ["controller", "xpc_caller"]
free.when: Capture was requested for this worker and worker output was collected.
retained_free: {"when": {"kind": "native_protocol", "reason": "The selected ordinary or actor policy supplies this worker capture request. Collection supplies the worker output consumed before receipt construction."}}
```

Passing every condition produces `captured` with the capture fields.

#### Application {application: condition}

```contract
free.condition: Application was observed and its return code was zero.
retained_free: {"condition":{"kind":"native_protocol","reason":"The raw application observation and return code are supplied to the capture decoder, separate from the derived capture receipt."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "successful_application_unconfirmed")]
```

#### Worker completion {completion: condition}

```contract
after: ["profile.receipt.host.application"]
free.condition: The worker published done and the collected exit code is zero with no terminating signal.
retained_free: {"condition": {"kind": "native_protocol", "reason": "The decoder receives done, exitCode and termSignal as independent inputs to capture validation."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "worker_not_complete")]
```

#### Capture completion {capture: condition}

```contract
after: ["profile.receipt.host.completion"]
free.condition: The worker published capture completion.
retained_free: {"condition":{"kind":"native_protocol","reason":"Raw capture-completion publication is the decoder input; captured status is its eventual result."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "capture_not_complete")]
```

#### Capture status {status: condition}

```contract
after: ["profile.receipt.host.capture"]
free.condition: The recorded capture status was accepted.
retained_free: {"condition":{"kind":"native_protocol","reason":"The native capture status precedes the receipt's captured/unavailable label and cannot be replaced by that label."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "worker_capture_refused")]
```

#### Process association {pid: condition}

```contract
after: ["profile.receipt.host.status"]
free.condition: The recorded PID equals the worker PID collected by the host.
retained_free: {"condition":{"kind":"native_protocol","reason":"The recorded capture PID and host-collected owned PID are independent inputs whose equality is checked before receipt creation."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "capture_worker_mismatch")]
```

#### Nonce association {nonce: condition}

```contract
after: ["profile.receipt.host.pid"]
free.condition: The recorded nonce bytes equal the valid request nonce.
retained_free: {"condition":{"kind":"native_protocol","reason":"Raw recorded nonce bytes are compared with the validated supplied nonce before the retained request nonce is emitted."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "capture_nonce_mismatch")]
```

#### Extent and type {extent: condition}

```contract
after: ["profile.receipt.host.nonce"]
free.condition: The profile type is zero and its raw byte count is positive and at most <!-- span limits.compiled_profile.value_unit -->1,048,576 bytes<!-- /span -->.
retained_free: {"condition":{"kind":"native_protocol","reason":"Raw profile type and extent are capture-buffer inputs checked before emitting the receipt's validated type/length fields."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "capture_extent_or_type_invalid")]
```

#### Payload digest {digest: condition}

```contract
after: ["profile.receipt.host.extent"]
free.condition: SHA-256 of the captured bytes equals the recorded digest.
retained_free: {"condition":{"kind":"native_protocol","reason":"The host hashes raw captured bytes and compares the raw recorded digest; emitted digest equality cannot substitute for that producing calculation."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "capture_bytecode_digest_mismatch")]
```

#### Consumed input {input: condition}

```contract
after: ["profile.receipt.host.digest"]
free.condition: The recorded source length and digest and parameter count and digest equal the host's supplied inputs.
retained_free: {"condition":{"kind":"native_protocol","reason":"Supplied source/parameter identities and raw consumed-input publications are separate decoder inputs, not duplicate final receipt fields."}}
```

##### First failed guard reason {failure: effect}

```contract
on: "failure"
effects: [set_value(receipt.reason, "capture_consumed_input_mismatch")]
```

#### Capture failure {failure: effect}

```contract
effects: [set_value(receipt.status, "unavailable"), withhold(receipt.producer), withhold(receipt.capture_stage), withhold(receipt.request_nonce), withhold(receipt.profile_type), withhold(receipt.bytecode_length), withhold(receipt.bytecode_sha256), withhold(receipt.bytecode_b64), withhold(receipt.source_sha256), withhold(receipt.source_length), withhold(receipt.params_sha256), withhold(receipt.parameter_count), retain_assessments(reply.normalized_outcome)]
on: "failure"
```

#### Source and constructed capture checks {support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/CWorker.swift","symbol":"decodeProfileCapture"}
check: {"path":"runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift","symbol":"runCompiledProfileCaptureTests","form":"test"}
pins: "The read checks construct worker bytes and corrupt each capture input. Each corruption, an unobserved application, a nonzero application return, an incomplete worker, a signal, a nonzero exit and each invalid extent asserts its reason and a receipt carrying only status, reason and worker PID; together they name all nine reasons. For each pair of adjacent conditions, two faults assert the earlier condition's reason. A known-answer parameter digest for two parameters, one non-ASCII, is asserted, as in the C capture controls."
context: "Constructed shared-memory bytes and injected application/termination arguments."
limits: "This owner credits source and check reading. The shared-memory fixture establishes host checks; the native same-pointer capture is source-supported here. Live receipts after a compile failure and a kill after application, and a live two-parameter capture, are in runner_outcome_bad_request/accepted_input_contract."
```

#### Successful receipt {success: effect}

```contract
on: "success"
effects: [set_value(receipt.status, "captured"), set_value(receipt.producer, "worker"), set_value(receipt.capture_stage, "before_apply"), set_value(receipt.profile_type, 0), withhold(receipt.reason)]
```

### The controller checks carried labels {labels: checks}

```contract
who: ["identity.definitions.controller"]
where: "reply_admission"
entry: ["cli_run", "runner_verify"]
recipient: ["cli_caller"]
when: present(receipt)
```

After public producer admission and reply-capacity checks, the controller applies these conditions to every present receipt, including actor, preparation-failure and reporting-failure records. The retained nonce, bytecode, digests, lengths and counts remain the host's assertions; their production checks belong to the host capture rule. The controller compares no receipt field with the request it delivered, with the reply's worker record or with the receipt's own bytes, and evaluates neither extent condition. A `finished` result beside a `captured` receipt reports the host's capture checks, not a controller comparison.

#### Status vocabulary {status: condition}

```contract
test: receipt.status in ["captured", "unavailable"]
```

#### Captured labels {captured: condition}

```contract
test: implies(receipt.status == "captured", receipt.producer == "worker" and receipt.capture_stage == "before_apply")
```

#### Unavailable labels {unavailable: condition}

```contract
test: implies(receipt.status == "unavailable", absent(receipt.producer) and absent(receipt.capture_stage))
```

#### A failed label check for run {failure: effect}

```contract
entry: ["cli_run"]
on: "failure"
effects: [set_value(envelope.result.normalized_outcome, "malformed_runner_response"), set_value(envelope.result.ok, False), set_value(envelope.result.exit_code, 1), set_value(envelope.data.runner_sandbox_diagnostics, None), retain_records(reply)]
```

For `run`, the controller refuses admission of the containing report, reports a failed result and exits with status 1. The retained report remains the host's account.

##### Constructed run labels {support: owner}

```contract
scope: "subtree"
grade: "executed"
run: "20261119T062523Z_48db4d65; unit/rust.unit"
source_snapshot: "controller/src/run_flow.rs sha256 8c8d42d7cc966d54d9aa60f162704dfdd872e6d367db94c545e303774c217c80; controller/src/porcelain_admission.rs sha256 19f071e85e9887240eff2a6bae7c6dabc671394c1ebca8c32677c40b830c230f; tests/fixtures/contract/compiled_profile.json sha256 7789f717f77ca8cd3c01f6351a385db205d9afd12e3e5757e03a8ade49e17867"
source: {"path":"controller/src/porcelain_admission.rs","symbol":"pub(crate) fn admission_problem"}
check: {"path":"controller/src/run_flow.rs","symbol":"compiled_profile_status_and_labels_alone_decide_run_admission","form":"test"}
pins: "The constructed check follows status and label admission through the public outcome, exit status, result and retained decoded report, and reads the diagnostics key as present with JSON null on every refused row."
context: "Constructed typed replies carried through the run command admission and envelope path with a supplied client result; the named control passed in the completed unit/rust.unit case with zero recorded system sleep."
limits: "The unit case passed on the named source bytes; its development run is disposable. Of the seventeen refused rows, nine are refused by reply admission with the decoded report retained. The other eight carry a non-string or absent status or label and are refused by the test's typed JSON reader, as host bytes that supply no typed record, before label admission. The admitted captured row's nonce, source and parameter fields do not correspond to the test request, which asks for no capture; admission here establishes nothing about request association. Constructed replies establish admission and retention, while native capture is a separate observation."
```

#### A failed label check for runner verify {verify_failure: effect}

```contract
entry: ["runner_verify"]
on: "failure"
effects: [set_value(result.ok, False), set_value(result.exit_code, 1), set_value(result.normalized_outcome, "malformed_runner_response"), set_value(runner_verify.normalized_outcome, "malformed_runner_response"), set_value(runner_verify.runner_pid, None), retain_records(runner_verify.runner_client), retain_records(runner_verify.runner_result)]
```

`runner verify` emits its verification envelope and exits with status 1.

##### Verification refusal source {support: owner}

```contract
grade: "source_read"
source: [{"path":"controller/src/runner_commands.rs","symbol":"cmd_runner_verify"},{"path":"controller/src/run_flow.rs","symbol":"pub(crate) fn admit_reply"},{"path":"controller/src/json_contract.rs","symbol":"impl JsonResult"}]
pins: "A refused verify reply preserves the returned capture and decoded report, leaves runner_pid null, copies the refusal classification into data and result, and returns exit 1."
context: "Read the verify command's Refused branch, payload construction, JsonResult construction and returned exit code."
limits: "The verify consequence is supported by these branches. The executed constructed-label case belongs to the run consequence."
```

#### An unsupported capture producer {example: example}

A current-build reply carries a captured receipt whose producer is `future`. The receipt-label check refuses that reply as `malformed_runner_response`.

#### Shared label admission source {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"pub(crate) fn admission_problem"},{"path":"controller/src/run_flow.rs","symbol":"pub(crate) fn reply_contract"},{"path":"controller/src/run_flow.rs","symbol":"pub(crate) fn admit_reply"},{"path":"controller/src/runner_commands.rs","symbol":"cmd_runner_verify"}]
pins: "Run and runner verify use the same post-version reply admission; it checks each present top-level or actor receipt's status, producer and capture-stage labels before command-specific refusal projection."
context: "Read both command routes into reply admission and the compiled-profile label loop."
limits: "The predicates and command dispatch are source-read. The executed constructed-label control under the run consequence supplies its separate run evidence."
```

### Capture and presence source {source: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"controller/tools/pw_probe_runner/pw_profile_capture.h","symbol":"pw_capture_profile"},{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"pw_capture_profile"},{"path":"runner/Sources/PWRunnerCore/ActorSession.swift","symbol":"profileCapture: input.captureCompiledProfile"},{"path":"runner/Sources/PWRunnerCore/CWorker.swift","symbol":"decodeProfileCapture"}]
pins: "Opt-in capture copies the same compiled object before apply; the collected worker output includes the optional host-checked receipt. The host compares the worker-recorded PID, nonce, source identity and parameter identity with its own values before emitting them; files the compiler reads are outside these identities. Shared-memory and public JSON projections are distinct."
context: "Read C capture, compile/apply call site, Swift output construction and ordered receipt checks."
limits: "Source reading establishes the branch account. The constructed-layout controls (tests/suites/runner_abi_layout/capture.c) exercise the capture over a structure they build themselves. The live captures (witness_contract/max_targets_reply_survives, runner_outcome_bad_request/accepted_input_contract) show that the reading yields captured status on the tested system, and the second checks that the bytes match their recorded length and digest, and for two parameters, one non-ASCII, that the count and parameter digest equal an independent framing. None decodes the bytes, compares them with a reference compilation or observes what application submitted."
```

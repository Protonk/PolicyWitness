# Delivery to the host {transport: surface}

```contract
syntax: 1
artifact: "Reservation, invocation and client capture"
part: "delivery"
goldens: ["tests/fixtures/contract/surfaces/transport.json"]
checks: ["runner_byoxpc", "runner_unit", "unit"]
```

The controller, client and host report different boundaries. A client can hold a reservation without invoking execution, invoke execution without receiving a reply, or receive bytes that its controller refuses to interpret.

## Implementation and evidence {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/runner_client.rs", "symbol": "parse_runner_client_output"}, {"path": "controller/src/runner_client.rs", "symbol": "validate_capture"}, {"path": "controller/src/utils.rs", "symbol": "run_with_stdin"}, {"path": "runner/Clients/PWRunnerClient/PWRunnerClientSession.swift", "symbol": "PWRunnerClientSession"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerReservation.swift", "symbol": "PWRunnerAdmission"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerTransport.swift", "symbol": "PWRunnerClientCapture"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerService.swift", "symbol": "reserveRunner"}]
check: [{"path": "runner/Tests/PWRunnerClientSessionTests/main.swift", "symbol": "runClientSessionControls", "form": "test"}, {"path": "runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift", "symbol": "runReservationAdmissionTests", "form": "test"}, {"path": "controller/src/runner_client.rs", "symbol": "binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence", "form": "test"}, {"path": "controller/src/runner_client.rs", "symbol": "retention_loss_precedes_decode_and_keeps_exact_prefix", "form": "test"}]
pins: "Source defines all imported fields, reservation state transitions, capture gates, preservation and deadline boundaries. Controlled tests establish retry/invocation accounting, connection binding, bound-control admission, byte preservation and delivery-error precedence."
context: "Read the cited producer/receiver declarations and branches; check citations identify the assertions read."
limits: "The Swift session checks inject clock, scheduler and connection boundaries. Rust process controls use controlled child programs. Live XPC, signed foreign-host nonreceipt and large native replies require separate execution evidence."
```

## Caller authorization {authorization: subject}

### Admit a connection {connection: checks}

```contract
who: ["identity.definitions.host"]
where: "NSXPCListener connection acceptance before exporting reservation methods"
entry: ["cli_run", "runner_verify", "direct_xpc"]
recipient: ["xpc_caller"]
report: ["connection_acceptance"]
free.condition: The host reads PWRunnerRequireSignedCaller from its Info.plist as a Boolean; absence or an unavailable Boolean value selects false.
free.effect: When true, obtain caller signing information using the connection PID and the host's own signing information; require both Team IDs to be present and equal. If a nonempty identifier allowlist is configured, also require the caller signing identifier to occur in it. Reject the connection before exporting reservation methods when these checks fail.
retained_free: {"condition":{"kind":"raw_admission","reason":"The Info.plist Boolean read can be absent or of another type; the accepted connection has no field carrying that raw configuration observation."},"effect":{"kind":"environment_observation","reason":"Caller and host signing information are live Security API observations tied to a connection PID and configured identifiers."}}
```

`PWRunnerAllowedIdentifiers` is a string array whose members are trimmed and empty members removed. An unavailable or empty resulting list leaves the identifier unrestricted within the Team ID check. The shipped template enables the signed-caller check and lists `pw-runner-client` and `com.policywitness.policy-witness`. An ad-hoc host has no Team ID and fails the enabled check. With the Boolean false, the listener accepts local connections without these signing comparisons; reservation and specimen admission still follow. These signing comparisons and public contract equality are separate checks.

### Authorization support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"authorizedCaller"},{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"shouldAcceptNewConnection"},{"path":"runner/Services/PWRunner/Info.plist","symbol":"PWRunnerRequireSignedCaller"}]
pins: "The listener applies configured signing-information comparisons before exporting a service; source defaults and shipped settings are distinct."
context: "Read Security lookup, Team ID and identifier comparisons, option decoding, listener call order and shipped template."
limits: "Source reading. The external-auth wrapper was read, but its delegated setup assertions and a signed refusal matrix are not credited by this owner."
```

## Reservation and execution {delivery: subject}

### Acquire an unused host {acquire: acts}

```contract
who: ["identity.definitions.client", "identity.definitions.host"]
where: "reserveRunner control RPC"
entry: ["cli_run", "runner_verify", "direct_xpc"]
recipient: ["runner_host", "runner_client"]
report: ["client_capture", "control_reply"]
uses: ["identity.public.contract"]
free.condition: The client has a positive remaining overall allowance and has already begun fewer than <!-- span limits.reservation_attempts.value -->256<!-- /span --> acquisition attempts.
free.effect: Send only the reservation control; the host may grant its one unused slot to that connection. Occupied or transport-lost acquisition may reconnect within the original allowance.
retained_free: {"condition":{"kind":"native_protocol","reason":"The pre-attempt remaining continuous-clock allowance and attempts-started counter precede the final acquisition report."},"effect":{"kind":"native_protocol","reason":"Grant/reconnect control runs on connection-bound reservation state within an unchanged deadline and never submits specimen bytes during acquisition."}}
```

The requested lease is at most <!-- span limits.reservation_lease.value_unit -->5,000 milliseconds<!-- /span --> and at most the remaining overall allowance. Each reservation RPC waits at most <!-- span limits.reservation_rpc_wait.value_unit -->5,000 milliseconds<!-- /span -->; retries wait up to <!-- span limits.reservation_retry_delay.value_unit -->100 milliseconds<!-- /span -->, shortened by the remaining allowance. The client begins at most <!-- span limits.reservation_attempts.value -->256<!-- /span --> acquisition attempts, including occupied replies and transport failures. Every attempt uses a new UUID. A host shares its one slot across authenticated connections. Grant, execution, expiry and abandonment advance that slot toward retirement; expiry or disconnect does not make it reusable. The client sends specimen bytes at the execution RPC.

### Admit the control {admit_control: checks}

```contract
who: ["identity.definitions.client"]
where: "reservation and submission-control reply admission"
entry: ["cli_run", "runner_verify"]
recipient: ["runner_client"]
report: ["client_capture"]
uses: ["identity.public.contract", "transport.control"]
free.condition: Control bytes arrive before a terminal client decision.
free.effect: Bound the control to <!-- span limits.reservation_control_bytes.value_unit -->65,536 bytes<!-- /span -->, compare the contract before decoding descendants, validate host-instance and credential UUID syntax, and associate the callback with the active phase and attempt. Acquisition accepts granted or occupied and checks the echoed attempt and requested lease; submission accepts reservation_refused. On refusal retain control byte count and SHA-256, withhold decoded fields and end with protocol_error.
retained_free: {"condition": {"kind": "native_protocol", "reason": "Control callback arrival must precede the client terminal decision; the decoded control cannot establish event ordering alone."}, "effect": {"kind": "serialized_grammar", "reason": "Raw control bytes, live callback phase/attempt, requested lease and UUID parsing govern admission. The adjacent typed requirements express the carried status-specific fields."}}
```

A grant requires a positive signed-32-bit host PID, UUID host instance, the current attempt UUID, UUID credential and positive lease no greater than requested. Acquisition replies require reason absent or null; occupied replies also require credential and lease absent or null. Both reservation requests and admitted control replies reject unknown keys after identity admission. Optional control fields accept JSON null as absence. Reservation acceptance establishes control admission and ownership of a slot. Peer PID and host-instance strings are assertions supplied by that peer.

#### Typed control identity {identity: condition}

```contract
test: control.host_pid > 0 and control.host_pid <= 2147483647 and utf8_length(control.host_instance) == 36
```

#### Admitted status forms {status: condition}

```contract
test: control.status in ["granted", "occupied", "reservation_refused"]
```

#### Granted reservation fields {grant: condition}

```contract
test: implies(control.status == "granted", present(control.attempt_id) and absent(control.reason) and present(control.reservation_id) and utf8_length(control.reservation_id) == 36 and present(control.lease_ms) and control.lease_ms > 0 and control.lease_ms <= limit("reservation_lease"))
```

#### Occupied reservation fields {occupied: condition}

```contract
test: implies(control.status == "occupied", present(control.attempt_id) and absent(control.reason) and absent(control.reservation_id) and absent(control.lease_ms))
```

#### Submission refusal fields {refusal: condition}

```contract
test: implies(control.status == "reservation_refused", absent(control.attempt_id) and absent(control.reservation_id) and absent(control.lease_ms) and control.reason in ["wrong", "expired", "absent", "consumed", "clock_error"])
```

### Invoke execution once {invoke: acts}

```contract
effects: set_value(capture.submission.state, "invoked")
who: ["identity.definitions.client"]
where: "runReservedSpecimen invocation on the granting connection"
entry: ["cli_run", "runner_verify"]
recipient: ["runner_host"]
report: ["client_capture"]
free.condition: A grant was admitted and a fresh continuous-clock sample is before the original deadline.
free.effect: Record the sampled invocation elapsed time before acquiring/calling the execution proxy. Make one execution invocation and preserve its observation through later error, timeout or refusal; never replay the specimen.
retained_free: {"condition": {"kind": "native_protocol", "reason": "Invocation eligibility uses a fresh continuous-clock sample after an admitted grant, not the final reported elapsed time."}, "effect": {"kind": "native_protocol", "reason": "The sampled elapsed time, publication-before-proxy ordering and once-only invocation are live session events. The invoked field records this client call boundary."}}
```

A grant handled at or after the overall deadline remains granted with submission `not_invoked`. The host checks the connection-bound credential before interpreting the specimen. Wrong, expired, absent or consumed credentials return a submission control refusal. A transport error after invocation leaves receipt and execution uncertain until independent observations resolve them.

### Apply the original allowance {deadline: acts}

```contract
who: ["identity.definitions.controller", "identity.definitions.client"]
where: "client launch, input delivery, acquisition and execution wait"
entry: ["cli_run", "runner_verify"]
recipient: ["cli_caller"]
report: ["client_capture", "run_envelope", "runner_verify"]
free.condition: The controller invokes its runner client with timeout_ms clamped to at least one millisecond.
free.effect: Create an absolute mach_continuous_time deadline before tool resolution and process spawn and pass it to the client. The client ends on expiry and ignores later callbacks; granting a reservation never resets the deadline.
retained_free: {"condition":{"kind":"raw_admission","reason":"The timeout floor applies to the parsed command option before the effective client allowance is stored."},"effect":{"kind":"native_protocol","reason":"One continuous-clock deadline is created and propagated through acquisition, invocation and callback expiry."}}
```

Continuous time includes machine sleep. Client clock failure ends with `local_error` and `clock_error`, preserves valid earlier readings and any positive invocation, and leaves the final reading absent. The controller drains complete stdout and stderr and waits for the client process; that collection has no independent receiver deadline. Client allowance expiry ends its wait. Host cleanup and worker termination follow their own owners and observations.

### Uncertain invocation example {uncertain: example}

A capture can contain `acquisition_stop: "granted"`, `submission: {"state":"invoked"}` and `terminal: "xpc_error"` while `runner_reply` is absent. The client crossed its execution-call boundary once; the reply was unavailable. Retrying the specimen would be a new caller decision with possible repeated effects. A capture rejected by the controller instead leaves the controller’s `submission` projection `unknown`.

### Transport evidence scope {live_evidence: definition}

```contract
defines: "value"
```

Controlled client connections establish the observed control-identity refusal and once-only submission behavior. Signed reservation and single-use observations concern their selected service and binaries. A foreign signed host’s receiving boundary, unbound-peer branches and native request/reply faults require their own observations. Native outcomes between the <!-- span limits.client_reply_retention.value_unit -->96,468,992 bytes<!-- /span --> client-retention cap and <!-- span limits.porcelain_frame_bytes.value_unit -->134,217,728 bytes<!-- /span --> frame limit remain unobserved in this account.

#### Disposition support {disposition_support: owner}

```contract
grade: "source_read"
source: {"path":"runner/Clients/PWRunnerClient/PWRunnerClientSession.swift","symbol":"reservationReply"}
pins: "Control admission and submission phase changes preserve the once-only client boundary."
context: "Static review of the cited production branches."
limits: "A substituted foreign control is a controlled receive observation. Native cap-interval behavior and a complete native fault matrix remain outside that observation."
```

## Reservation request {reservation: subject}

```contract
record: "PWRunnerReservationRequest"
as: "reservation"
```

### contract {contract: field}

The client’s exact public identity. The host compares it before decoding the rest of this control.

### attempt_id {attempt_id: field}

UUID naming one acquisition attempt, echoed by granted or occupied control responses.

### lease_ms {lease_ms: field}

Positive requested reservation lifetime in milliseconds; the host caps an accepted lease at 5,000.

## Host control reply {control: subject}

```contract
record: "PWRunnerControlReply"
as: "control"
```

### contract {contract: field}

The host’s compiled public identity, checked by the client before reading the control body.

### status {status: field}

The host reports `granted`, `occupied`, `invalid_request`, `unsupported_protocol` or `reservation_refused` at the corresponding boundary. The client admits granted/occupied acquisition replies and reservation_refused submission replies with their required fields.

### attempt_id {attempt_id: field}

Acquisition attempt echoed when available; submission-refusal replies omit it.

### host_pid {host_pid: field}

Host-reported process identifier. A client-admitted control requires a positive value representable as signed 32-bit.

### host_instance {host_instance: field}

Host-generated UUID for its admission owner, reported by that host.

### reservation_id {reservation_id: field}

Single-use UUID credential returned by a grant and supplied only on the granting connection’s execution call. Capture projection omits this credential.

### lease_ms {lease_ms: field}

Lifetime granted in milliseconds. A client accepts a positive value no greater than the requested lease.

### reason {reason: field}

Control refusal diagnostic. Submission refusals use `wrong`, `expired`, `absent`, `consumed` or `clock_error`; invalid/unsupported acquisition controls have their own reason.

## Client capture {capture: subject}

```contract
record: "PWRunnerClientCapture"
as: "capture"
```

### kind {kind: field}

`runner_client_capture` identifies the client observation record.

### contract {contract: field}

Client producer’s public identity. The controller admits it independently of the embedded host reply’s producer.

### client_pid {client_pid: field}

PID reported by the runner-client process; distinct from every host, worker and validator PID.

### clock {clock: field}

`mach_continuous_time_ns` names the capture’s continuous-clock readings.

### clock_available {clock_available: field}

Whether the client retained a usable monotonic continuous clock through its terminal decision. False accompanies a clock_error local failure.

### started_continuous_ns {started_continuous_ns: field}

Client session’s initial valid clock reading in nanoseconds, when available.

### deadline_continuous_ns {deadline_continuous_ns: field}

Absolute deadline in the same clock coordinate, inherited from the controller or derived locally when invoked directly.

### ended_continuous_ns {ended_continuous_ns: field}

Last valid sample at terminal completion; absent after clock failure.

### timeout_ms {timeout_ms: field}

Positive nominal allowance supplied to the client, in milliseconds. The inherited absolute deadline accounts for time already spent before the session starts.

#### Positive effective allowance {positive: condition}

```contract
test: capture.timeout_ms > 0
```

### attempts {attempts: field}

Acquisition attempts in invocation order, with one-based ordinals and unique attempt UUIDs.

#### Bounded acquisition count {bounded: condition}

```contract
test: count(capture.attempts) <= limit("reservation_attempts")
```

### acquisition_stop {acquisition_stop: field}

`granted`, `overall_deadline`, `attempt_limit`, `protocol_error` or `local_error`. Granted remains true even if a later pre-invocation stop prevents submission.

### submission {submission: field}

The client’s irreversible execution-invocation observation.

### terminal {terminal: field}

One of `runner_reply`, `submission_refused`, `xpc_error`, `xpc_timeout`, `acquisition_failed`, `protocol_error` or `local_error`, naming the client’s final event.

### error {error: field}

Bounded client-local or XPC diagnostic associated with a failure terminal.

### runner_reply {runner_reply: field}

Host-result bytes accepted by the client before its deadline. Presence establishes receipt of the result callback; the controller separately admits the frame and evidence.

### submission_refusal {submission_refusal: field}

Count/hash and, after control admission, status and reason of a host submission refusal. Malformed control bytes retain only count/hash.

## Acquisition attempt {acquisition: subject}

```contract
record: "PWRunnerAcquisitionAttempt"
as: "acquisition"
```

### ordinal {ordinal: field}

One-based position in the capture’s acquisition-attempt array.

### attempt_id {attempt_id: field}

UUID generated for this attempt. The client requires matching acquisition replies.

### started_elapsed_ms {started_elapsed_ms: field}

Elapsed whole milliseconds from the client session’s initial continuous-clock sample at attempt start, when available.

### ended_elapsed_ms {ended_elapsed_ms: field}

Elapsed whole milliseconds when this attempt ended, when available; a later clock fault can leave it absent.

### outcome {outcome: field}

`granted`, `occupied`, `transport_error`, `timeout`, `protocol_error` or `local_error`. Only acquisition transport loss, occupied status and an RPC timeout can lead to another acquisition attempt.

### control {control: field}

Received reservation-control count/hash and any admitted peer fields.

### error {error: field}

Failure diagnostic for this attempt. A granted or occupied attempt instead carries its admitted control.

## Retained control observation {control_observation: subject}

```contract
record: "PWRunnerControlObservation"
as: "control_observation"
```

### bytes_received {bytes_received: field}

Byte count of the complete received control data, including a control that fails admission.

### sha256 {sha256: field}

SHA-256 of those complete bytes, projected as lowercase hexadecimal.

### status {status: field}

Control status retained only after the client admits the control.

### host_pid {host_pid: field}

Admitted peer-reported host PID.

### host_instance {host_instance: field}

Admitted peer-reported admission-owner UUID.

### lease_ms {lease_ms: field}

Admitted grant lifetime when the control carries one.

### reason {reason: field}

Admitted submission-refusal reason when present.

## Submission observation {invocation: subject}

```contract
record: "PWRunnerSubmission"
as: "invocation"
```

### state {state: field}

`not_invoked` until the client crosses its execution-call boundary, then permanently `invoked`. This field is authoritative to the controller only in an admitted capture.

### invoked_elapsed_ms {invoked_elapsed_ms: field}

Elapsed whole milliseconds at that boundary. Absent for not_invoked; clock-failure capture retains only a value actually sampled.

## Retained host reply {retained_reply: subject}

```contract
record: "PWRunnerReplyCapture"
as: "retained_reply"
```

### bytes_received {bytes_received: field}

Length of the complete host-result Data received by the client.

### bytes_retained {bytes_retained: field}

Length of its retained prefix, the smaller of bytes_received and <!-- span limits.client_reply_retention.value_unit -->96,468,992 bytes<!-- /span -->.

### truncated {truncated: field}

True exactly when bytes_retained is smaller than bytes_received. The controller refuses a truncated host frame before structural decoding.

#### Retention arithmetic {arithmetic: condition}

```contract
test: retained_reply.truncated == (retained_reply.bytes_retained < retained_reply.bytes_received) and retained_reply.bytes_retained <= retained_reply.bytes_received and retained_reply.bytes_retained <= limit("client_reply_retention") and implies(retained_reply.bytes_received <= limit("client_reply_retention"), retained_reply.bytes_retained == retained_reply.bytes_received) and implies(retained_reply.bytes_received > limit("client_reply_retention"), retained_reply.bytes_retained == limit("client_reply_retention"))
```

### data_base64 {data_base64: field}

Exact retained host bytes, kept as bytes internally and rendered as base64 at public JSON projection.

#### Exact retained byte extent {extent: condition}

```contract
test: byte_length(retained_reply.data_base64) == retained_reply.bytes_retained
```

### Source for these relationships {source: owner}

```contract
scope: "subtree"
grade: "source_read"
source: {"path": "runner/Sources/PWRunnerCore/PWRunnerTransport.swift", "symbol": "struct PWRunnerReplyCapture"}
pins: "The constructor retains the bounded Data prefix, its original and retained lengths, and their inequality flag."
```

## Client error {error: subject}

```contract
record: "PWRunnerTransportError"
as: "error"
```

### stage {stage: field}

Boundary at which the client reported the error: `local`, `acquisition` or `submission`.

### reason {reason: field}

Machine classification for the boundary, including `clock_error`, `encoding_failed`, `input_read_failed`, `xpc_error`, `proxy_type_mismatch`, `rpc_timeout`, `overall_deadline`, `attempt_limit`, `control_too_large`, `unsupported_protocol` and `invalid_control`. The capture reader checks stage/reason/terminal compatibility.

### domain {domain: field}

Native NSError domain when available, bounded to <!-- span limits.client_error_domain.value_unit -->128 UTF-8 bytes<!-- /span --> without splitting a scalar.

### code {code: field}

Native NSError numeric code when available. Its value belongs to that error domain.

### message {message: field}

Native debug diagnostic when available, otherwise localized or supplied client text; bounded to <!-- span limits.client_error_message.value_unit -->1,024 UTF-8 bytes<!-- /span --> without splitting a scalar.

### domain_truncated {domain_truncated: field}

Whether the original native domain exceeded its retained-byte allowance.

### message_truncated {message_truncated: field}

Whether the original message exceeded its retained-byte allowance.

## Controller observation of the client process {client: subject}

```contract
record: "rust.RunnerClientRun"
as: "client"
```

### argv {argv: field}

Controller-selected client executable and arguments, including connection flags, deadline and stdin-request mode.

### started_at_unix_ms {started_at_unix_ms: field}

Controller wall-clock milliseconds immediately before launching and feeding the client.

### ended_at_unix_ms {ended_at_unix_ms: field}

Controller wall-clock milliseconds after child-output collection and request-writer completion. Wall-clock reversals remain visible.

### exit_code {exit_code: field}

Client process exit code, or 1 when process status supplies no numeric exit code. A zero client exit accompanies delivery of host-result bytes and leaves host outcome to its own report.

### request_delivery {request_delivery: field}

Controller’s stdin-writer observation for the one held serialized request.

### transport {transport: field}

Admitted typed client capture or a rejected retained-byte projection; null when no bytes are retained.

### transport_admission {transport_admission: field}

`accepted`, `missing`, `unsupported`, `malformed` or `delivery_failed`, naming the controller’s client-capture admission decision.

### transport_error {transport_error: field}

Diagnostic explaining capture refusal or absence; null for accepted capture.

### submission {submission: field}

Admitted capture’s invoked/not_invoked state, otherwise `unknown`. Raw rejected bytes never supply a recovered invocation assertion.

### runner_reply_error {runner_reply_error: field}

Diagnostic for a truncated, unsupported or malformed embedded host frame. Its exact retained bytes remain in the admitted client capture.

### stdout_parse_error {stdout_parse_error: field}

Binary frame/schema/producer decoding diagnostic when decoding was attempted. Retention loss is recorded independently before decoding.

### stdout_truncated {stdout_truncated: field}

Whether complete client stdout exceeded the retained prefix allowance.

### stdout_capture_error {stdout_capture_error: field}

Retention-loss diagnostic; this blocks capture decoding even if the prefix resembles a valid frame.

### stdout_bytes_received {stdout_bytes_received: field}

Original stdout byte count after complete process-output collection.

### stdout_bytes_retained {stdout_bytes_retained: field}

Retained stdout prefix length, before binary frame admission.

### stderr_bytes_received {stderr_bytes_received: field}

Original stderr byte count after complete process-output collection.

### stderr_bytes_retained {stderr_bytes_retained: field}

Retained stderr prefix length before diagnostic text conversion.

### capture_limit_bytes {capture_limit_bytes: field}

Per-stream prefix-retention allowance, currently <!-- span limits.controller_output.value_unit -->285,212,672 bytes<!-- /span --> for the runner client.

### stderr {stderr: field}

Retained stderr converted to UTF-8 text with replacement for invalid bytes.

### stderr_truncated {stderr_truncated: field}

Whether complete stderr exceeded its retained prefix allowance.

### Admit client and host observations {admit: checks}

```contract
who: ["identity.definitions.controller"]
where: "completed client stdout and nested host frame"
entry: ["cli_run", "runner_verify"]
recipient: ["cli_caller"]
report: ["run_envelope", "runner_verify"]
uses: ["identity.public.contract"]
free.condition: The client process and input writer completed collection.
free.effect: Give request-delivery failure precedence; otherwise refuse retention loss, missing capture, unsupported producer/schema or inconsistent capture. Admit the host frame separately only when its retained bytes are complete. Keep raw received bytes at the boundary that received them.
retained_free: {"condition":{"kind":"native_protocol","reason":"Process collection and stdin-writer completion are independent events whose join determines delivery success."},"effect":{"kind":"serialized_grammar","reason":"Retention, capture decoding and host-frame admission operate on successive byte representations before the decoded host reply is available."}}
```

Delivery failure yields controller `tool_error` and exit 2 while retaining available client bytes. Admitted capture semantics check chronology, UUIDs, terminal combinations, control fields and retained lengths. Unsupported or malformed capture withholds submission knowledge and host interpretation. An admitted capture’s `runner_reply` can still be refused as `runner_reply_truncated`, `unsupported_runner_response` or `malformed_runner_response`. Host semantic admission follows structural decoding.

#### Input delivery takes precedence {delivery: condition}

```contract
test: implies(present(client.request_delivery) and present(client.request_delivery.error), client.transport_admission == "delivery_failed" and client.transport_error == client.request_delivery.error and client.submission == "unknown" and absent(client.stdout_parse_error) and absent(client.runner_reply_error))
```

#### Retention loss precedes decoding {retention: condition}

```contract
test: implies(not (present(client.request_delivery) and present(client.request_delivery.error)) and present(client.stdout_capture_error), client.transport_admission == "malformed" and client.transport_error == client.stdout_capture_error and client.submission == "unknown" and absent(client.stdout_parse_error) and absent(client.runner_reply_error))
```

#### Empty retained capture {missing: condition}

```contract
test: implies(not (present(client.request_delivery) and present(client.request_delivery.error)) and absent(client.stdout_capture_error) and client.stdout_bytes_retained == 0, client.transport_admission == "missing" and client.transport_error == "runner client produced no capture" and client.submission == "unknown" and absent(client.stdout_parse_error) and absent(client.runner_reply_error))
```

#### Capture refusal selection source {selection_source: owner}

```contract
grade: "source_read"
source: {"path": "controller/src/runner_client.rs", "symbol": "parse_runner_client_output"}
pins: "Completed collection first selects input-delivery error, then retained-output loss, then an empty capture. These paths preserve unknown submission and skip both frame decoders."
```

## Request stdin delivery {request_delivery: subject}

```contract
record: "rust.RequestDelivery"
as: "request_delivery"
```

### bytes_written {bytes_written: field}

Number of request bytes accepted by the child’s stdin pipe according to the controller’s writes.

### error {error: field}

First terminal write error, including a zero-length write. Null records successful delivery by the writer; child receipt remains a separate observation.

## Transport alternatives {transport_value: subject}

```contract
record: "rust.TransportCapture"
as: "transport_value"
```

The public object is either the complete admitted PWRunnerClientCapture projection or the Rejected object below. The Rust enum is untagged: JSON contains the chosen alternative’s fields directly. `transport_admission` names which interpretation the controller established.

## Rejected client stdout {rejected: subject}

```contract
record: "rust.TransportCapture.Rejected"
as: "rejected"
```

### format {format: field}

`porcelain` identifies the expected client-output encoding at this collection boundary.

### data_base64 {data_base64: field}

Exact retained stdout prefix, projected as base64. It can contain arbitrary, malformed or foreign bytes.

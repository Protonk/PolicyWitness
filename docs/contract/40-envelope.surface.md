# The controller envelope {envelope: surface}

```contract
syntax: 1
artifact: "The controller envelope"
part: "assessment"
goldens: ["tests/fixtures/contract/surfaces/envelope.json"]
checks: ["unit", "integration", "failure_boundaries"]
who: "controller"
where: "JSON envelope presentation"
entry: ["cli"]
recipient: ["cli_caller"]
report: ["run"]
```

## Run envelope {run: subject}

```contract
record: "rust.RunEnvelope"
as: "run_envelope"
```

### Build {build: field}

The emitting binary's embedded build stamp, separate from nested producers.

### Data {data: field}

Run payload, retaining observations under their admission and collection conditions.

### Generation time {generated_at_unix_ms: field}

Emitter wall-clock time at rendering, in milliseconds since the Unix epoch.
An unavailable pre-epoch duration becomes zero. Child spans and
continuous-clock ordering have separate observations.

### Operation {kind: field}

`run` identifies specimen execution.

### Result {result: field}

The controller operation's result. Nested native and child returns retain
their own scopes.

## Compiler-helper envelope {helper: subject}

```contract
record: "rust.HelperEnvelope"
as: "compiler_envelope"
```

### Build {build: field}

The helper binary's embedded build stamp.

### Data {data: field}

Helper policy metadata, import inventory and compilation result.

### Generation time {generated_at_unix_ms: field}

Helper wall-clock time at rendering, in milliseconds since the Unix epoch.
An unavailable pre-epoch duration becomes zero.

### Operation {kind: field}

`sbpl_check` identifies standalone or captured helper compilation.

### Result {result: field}

The helper operation's result, separate from any worker execution.

## Operation result {result: subject}

```contract
record: "rust.JsonResult"
as: "result"
```

### Success {ok: field}

For an admitted specimen result, true exactly when the host outcome is
`finished`. Evidence findings and failed individual attempts can coexist
with true. Other commands define success for their own operation.

### Return code {rc: field}

Optional native-style result slot. Controller/helper-created results leave
it null; native attempt returns remain in their nested records.

### Process exit {exit_code: field}

Selected controller/helper exit status. For a run: zero for admitted
`finished`, one for an execution/refusal outcome, two for tool or
input-handling errors.

### Outcome {normalized_outcome: field}

Selected operation label. An admitted host outcome is copied; controller
and client admission failures use the classifications below.

### Errno {errno: field}

Optional native errno slot. Controller/helper-created results leave it null;
nested errno values concern their own operations.

### Error {error: field}

Human-readable diagnostic, null on successful controller/helper results.
After execution admission, precedence is host error, client
`stdout_capture_error`, client `stdout_parse_error`, then a generic
unsuccessful-run message.

### Standard error {stderr: field}

Optional captured text slot. Controller/helper-created results leave it null;
client and child capture text stays in its own record.

### Standard output {stdout: field}

Optional captured text slot. Controller/helper-created results leave it null;
typed nested data carries the report.

## Run payload {data: subject}

```contract
record: "rust.RunData"
as: "run_data"
```

### Controller assessments {runner_sandbox_diagnostics: field}

Assessments after client/reply admission. Null for earlier refusals and tool
errors. An admitted execution with no host report can still produce the
controller's no-worker assessment.

### Dossier {specimen: field}

Held-input, equipment and provenance observations, including partial records
on failure.

### Ordinary fallback compilation {policy_check: field}

Independent helper capture after an eligible admitted client-terminal
`xpc_error`. Null when fallback was not invoked.

### Actor fallback compilations {actor_policy_checks: field}

Captures for actor declarations carrying a sandbox.policy object, in request
order, when fallback is eligible. Collection of these policy objects precedes
host admission of sandbox mode. Omitted when fallback is ineligible or the
request contains no actor policy objects.

### Client wait budget {timeout_ms: field}

Selected runner-client wait budget in milliseconds when argument parsing
supplied it; null when no usable configuration was obtained.

### Client invocation {runner_client: field}

Client invocation, capture and delivery account. Null when the client was
not invoked or launch failed before a capture returned.

### Host report {runner_result: field}

Structurally decoded host reply when available, retained even if a later
label gate refuses admission. Null when there is no decodable reply; an
accepted capture can retain its exact bytes separately.

### Request refusal {request_failure: field}

Controller refusal code/path, or the host refusal projected from an admitted
`bad_request` reply. Omitted when the selected result supplies none.

### Select the public result {select: reports}

```contract
where: "run completion after admission"
after: ["diagnostics.execution.reply_checks"]
when: present(envelope.data.runner_result)
free.when: Client capture and host reply admission have succeeded.
effects: [set_value(envelope.result.ok, reply.normalized_outcome == "finished"), set_value(envelope.result.normalized_outcome, reply.normalized_outcome)]
free.effect: Choose exit 0 for finished and exit 1 otherwise. Retain query, attempt and native records, and compute diagnostics independently.
```

`finished` can coexist with a failed file open or an integrity finding.
The observations and supported assessments state what the run establishes.

#### Success and findings {success_findings: gap}

```contract
kind: "behavior"
```

Whether result.ok and process exit should also reflect controller integrity
findings remains open. Present behavior selects success from the admitted
host outcome alone.

### Controller classifications {classification: definition}

| Value or boundary | Result and retained account |
| --- | --- |
| `bad_request` | Decoded request admission refused; exit 1, structured refusal when supplied, dossier retained. |
| `tool_error` | CLI/input/configuration, client launch or request delivery failed; exit 2. A returned client capture remains on delivery refusal. |
| `missing_runner_client` | No retained client capture; exit 1. |
| `unsupported_runner_client` | Client producer/schema admission failed; exit 1, bounded rejected bytes retained. |
| `malformed_runner_client` | Client frame or capture semantics failed; exit 1, bounded rejected bytes retained. |
| `runner_reply_truncated` | Accepted capture says host bytes were truncated; exit 1, prefix retained. |
| `unsupported_runner_response` | Host schema/public identity failed; exit 1, captured bytes retained. |
| `malformed_runner_response` | Host decoding, capacity or label check failed; exit 1. A structurally decoded report remains when the later gate refused it. |
| `xpc_error`, `xpc_timeout` | Admitted client reports that transport failure; exit 1. xpc_error alone can permit fallback compilation. |
| `xpc_acquisition_failed`, `xpc_submission_refused`, `xpc_protocol_error` | Client reports acquisition failure, reservation refusal or protocol error; exit 1. |
| `runner_client_error` | Another admitted client local-terminal failure; exit 1. |
| `runner_response_unavailable` | Completion has no host result to supply an outcome; exit 1. |
| Other admitted host label | Retain the label and select exit 1; only exact `finished` selects run success. |

### Boundary precedence {admit: checks}

```contract
who: ["identity.definitions.controller"]
where: "received run data admission"
failure: "first"
free.condition: Check request delivery error first, then client failure (capture admission, host frame admission and transport terminal), then decoded host producer identity and host capacity/profile-label admission.
free.effect: A delivery failure yields tool_error/exit 2; another refused boundary yields its classification/exit 1. Retain the available capture and structurally decoded reply, with runner_sandbox_diagnostics null. Eligible xpc_error can add independent fallback compilation.
```

Admission precedes evidence interpretation. The same held request supplies
client delivery and eligible ordinary fallback compilation; the helper
result describes its separate compiler invocation.

### A finished run with a failed attempt {failed_attempt: example}

An admitted report says `finished` while a step says `open_failed`, rc -1
and errno 1. The controller emits result.ok true and exit 0, retains the
native failure and computes evidence findings independently.

## Envelope support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path":"controller/src/json_contract.rs","symbol":"render_envelope"},{"path":"controller/src/run_flow.rs","symbol":"complete_execution"},{"path":"controller/src/run_flow.rs","symbol":"admit_reply"},{"path":"controller/src/runner_client.rs","symbol":"pub fn failure"}]
check: [{"path":"controller/src/json_contract.rs","symbol":"renderer_borrows_nonclone_typed_payload_and_serializes_it_once","form":"test"},{"path":"controller/src/run_flow.rs","symbol":"finished_run_preserves_successful_and_failed_attempts","form":"test"},{"path":"controller/src/run_flow.rs","symbol":"typed_completion_preserves_native_failure_beside_finished_summary","form":"test"},{"path":"controller/src/runner_client.rs","symbol":"binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence","form":"test"}]
pins: "Constructed outcomes preserve nested native evidence and select success only for finished. A real fixture child exposes delivery refusal precedence. Rendering serializes the borrowed payload once."
context: "Read completion/admission/frame code and the named constructed or fixture-child checks."
limits: "Check reading. The fixture child is a controlled protocol writer; native kernel execution is separate evidence."
```

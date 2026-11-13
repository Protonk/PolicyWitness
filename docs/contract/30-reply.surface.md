# The host report {reply: surface}

```contract
syntax: 1
artifact: "The host report"
part: "report"
goldens: ["tests/fixtures/contract/surfaces/reply.json"]
checks: ["runner_unit", "failure_boundaries"]
who: ["identity.definitions.host"]
where: "host reply assembly"
entry: ["xpc_execute"]
recipient: ["controller", "xpc_caller"]
report: ["runner_reply"]
```

## Execution record {record: subject}

```contract
record: "PWRunnerRunResult"
as: "host_report"
```

The host produces this record after execution or as a refusal. A received
record's admissibility and supported assessments have their respective
recipient boundaries.

### Producer {producer: field}

The host build context. Its public contract string is checked before a
recipient interprets the body.

### Specimen identifier {specimen_id: field}

The admitted specimen identifier. A JSON-decode refusal uses
`<decode_failed>`; refusal construction sanitizes an unavailable or
over-capacity identifier.

### Run label {run_kind: field}

The caller's optional label, echoed when available and within admitted bounds.
It labels the experiment and does not select an execution algorithm.

### Aggregate code {rc: field}

Zero for `finished`, one for a classified refusal or failure. Native
operations and child exit statuses have separate fields.

### Aggregate outcome {normalized_outcome: field}

The host outcome, with the meanings below.

### Aggregate diagnostic {error: field}

Human-readable diagnostic, omitted on ordinary success. Published failure,
host supervision and collection details can coexist here; their structured
observations retain their own origins.

### Process identifier {pid: field}

For ordinary execution, the collected worker PID when worker output exists,
otherwise the host PID. For actor execution, the host PID. Actor launch and
subprocess records identify each worker.

### Bundle identifier {bundle_id: field}

The host bundle's CFBundleIdentifier when available.

### Policy format {policy_format: field}

The ordinary policy format when available; decode refusal uses `unknown`.
Actor policies carry their formats in actor records.

### Policy source digest {policy_sha256: field}

SHA-256 of the ordinary supplied source's UTF-8 bytes, as lowercase
hexadecimal. It identifies the source observed by the host. Compiled-object
and consumed-parameter identities have separate receipt fields. Actor form
uses per-actor source hashes.

### Compiled-profile receipt {compiled_profile: field}

The ordinary worker's opt-in receipt when collected output supplies it.
Actor receipts belong to their actor records.

### Applied publication {sandboxed_after_apply: field}

The ordinary driver's observed applied publication when worker output exists.
False leaves application unobserved by this flag; native failure publications
and actor application assessments supply their own evidence. Actor form
omits this top-level flag.

### Probe results {steps: field}

Probe rows in declared action order, with query, attempt and comparison
observations. Refusals before worker execution and the minimal reporting
fallback use an empty array.

### Ordinary worker {runner_subprocess: field}

Collected worker supervision, publication and disposition. Absent when no
worker output supplies it; actor subprocess accounts live in actor records.

### Capacity refusal {admission_failure: field}

Capacity or embedded-NUL refusal details when that admission branch is reached.

### Request refusal {request_failure: field}

Structured code/path and, when applicable, expected identity for the refusal
selected by the reached decoding or admission branch.

### Phase results {phases: field}

Declared phases in schedule order, including reached and unreached phases
when orchestration produces that account. Rows separate arrival, collection,
completion and ordering.

### Extension events {extension_events: field}

Extension action observations with actor, phase and action association.
Ordinary probe-only execution can omit this field; actor assembly supplies
its event array.

### Instrumentation {test_overrides: field}

Accepted instrumentation echoed by orchestration, with refusal sanitation
where required. It identifies the selected execution configuration.

### Reporting failure {reporting_failure: field}

Host validation or encoding failure and the fallback's retention state.


### Execution form {execution_form: field}

`actors` identifies actor assembly. The ordinary producer omits the field.
Recipient checks define the consequence of other carried values.

### Actor records {actors: field}

Per-actor declaration, setup, application, launch and subprocess accounts.
Preparation refusal can supply declaration records before launch; their
presence alone does not establish launch.

### Transfers {transfers: field}

Host observations of extension delivery attempts and recipient acknowledgements.

### Resources {resources: field}

Specimen-local token, delivery and handle records with their ownership and
available production/use observations.

### Schedule {schedule: field}

Actor scheduling waits, budgets and cancellation. Cancellation is a scheduling
decision, separate from each actor's collected exit evidence.

### Preparation refusal {preparation_failure: field}

Actor preparation failure selected before scheduler launch. Declarations and
equipment observations from that preparation can remain present.

### Equipment inventory {equipment_inventory: field}

Host read and validation of the sealed worker inventory.

### Equipment bindings {equipment_bindings: field}

Static worker binding observations referenced by actor equipment assignments
and preparation failures.

### Equipment entitlements {equipment_entitlements: field}

Requested and observed entitlements used by preparation and live association.

### Authority setup {authority_setup: field}

Host and worker authority-setup publications, including acquired operation
cells and cleanup evidence under their own publication rules.

### Assemble execution evidence {assemble: reports}

```contract
free.effect: Assemble the aggregate summary and available observations without replacing native operation returns with the summary. Ordinary and actor-owned fields use their respective locations.
retained_free: {"effect":{"kind":"native_protocol","reason":"Ordinary, actor and refusal forms assemble reports from different available outputs; final array presence alone cannot establish all prior publications."}}
```

Ordinary classification examines worker failure, publication and supervision
before validator collection. If the worker side remains successful, the first
unsuccessful phase collection selects the summary; all collection records
remain. Actor orchestration reports each actor and selects an aggregate outcome.

### Host outcomes {outcomes: definition}

| Value | Host commitment |
| --- | --- |
| `finished` | Execution and required collection completed under the classifier's conditions; each attempt retains its own result. |
| `bad_request` | Reached decoding/admission refused the specimen before worker or validator execution. |
| `bad_policy` | The host could not identify the ordinary source under its structural policy check. |
| `worker_spawn_failed` | The driver could not spawn the worker. |
| `runner_timeout` | Host sentinel or policy-transfer deadline expired, subject to higher-precedence published worker failures. |
| `runner_failed` | Worker preparation/application/publication, host apparatus or supervision failed, or required observations are unusable. |
| `validator_spawn_failed` | Worker classification succeeded and validator spawn failed. |
| `validator_no_reply` | Worker classification succeeded and validator query delivery or verdict reading failed. |
| `validator_decode_failure` | Worker classification succeeded and validator parsing or typed decoding failed. |
| `validator_unavailable` | Required collection was not invoked, its budget/clock failed, or validator supervision/association was unusable. |
| `runner_reporting_failed` | The host failed to validate or encode its assembled report and entered reporting fallback. |

### Classification support {classification: owner}

```contract
grade: "check_read"
scope: "subtree"
source: [{"path":"runner/Sources/PWRunnerCore/CWorkerDisposition.swift","symbol":"func classify("},{"path":"runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift","symbol":"let topPid: Int"},{"path":"runner/Sources/PWRunnerCore/ActorOrchestration.swift","symbol":"var reply = PWRunnerRunResult"},{"path":"runner/Sources/PWRunnerCore/SandboxApply.swift","symbol":"computePolicyHash"}]
check: {"path":"runner/Tests/PWRunnerCoreTests/HostOutcomeClassifierTests.swift","symbol":"runHostOutcomeClassifierTests","form":"test"}
pins: "Constructed worker/validator outputs select aggregate outcomes; published native failure and unobserved application retain separate meanings. Assembly source establishes field locations and PID selection."
context: "Read classifier branches, ordinary/actor assembly, source hashing and classifier controls."
limits: "Check reading. PID placement and the actor aggregate ladder have source support here, without new integrated execution credit."
```

## Reporting failure {failure: subject}

```contract
record: "PWRunnerReportingFailure"
as: "failure"
```

### Origin {origin: field}

`runner_host` identifies whose validation or encoding failed.

### Diagnostic {diagnostic: field}

The failed validation/encoding diagnostic. The minimal fallback also includes
the subsequent rich-fallback failure.

### Original aggregate code {original_rc: field}

Code from the original assembled report, retained as diagnostic context.

### Original outcome {original_normalized_outcome: field}

Outcome from the original assembled report, retained as diagnostic context.

### Original diagnostic {original_error: field}

Original aggregate error when present.

### Retention {evidence_retained: field}

True identifies the rich fallback: original fields remain apart from the
producer/summary/reporting-failure metadata and removed step comparisons.
False identifies the independent minimal fallback with scalar context and
empty steps/phases.

### Reporting-failure associations {associations: definition}

```contract
uses: ["reply.failure.publish", "actor_evidence.actor.reader_scope"]
```

Reporting-failure admission checks the degraded form and applicable receiver
context. It does not certify ordinary actor/phase associations in retained
records. Those records may preserve the inconsistency that caused reporting
failure. Worker-local lifecycle checks continue at their stated scope; no
comparison or query-order conclusion is recovered from retained raw records.

### Publish a report or fallback {publish: reports}

```contract
where: "host response encoding"
failure: "first"
free.effect: Validate and encode the assembled report. If either operation fails, copy that report into a rich fallback, replace the producer and aggregate summary, preserve the original summary as reporting-failure diagnostics, and remove step comparisons. Validate and encode the rich fallback. If either operation fails again, use the independent minimal writer with original specimen/run/bundle/policy identity, PID and summary diagnostics. If that writer fails, return empty bytes.
retained_free: {"effect": {"kind": "native_protocol", "reason": "Validation/encoding failures select successive writer attempts. Original-summary copying reads the distinct rejected report; the final fallback carries the selected writer retention state."}}
```

The rich fallback preserves observations that triggered rejection. Empty reply bytes reach the
recipient's decoding failure.

#### Fallback support {support: owner}

```contract
grade: "check_read"
source: [{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"pwRunnerReportData"},{"path":"runner/Sources/PWRunnerCore/PWRunnerReply.swift","symbol":"func validateForReporting()"}]
check: {"path":"runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift","symbol":"runReplyFailureTests","form":"test"}
pins: "Constructed reporting defects trigger rich fallback, preserve other projected fields and remove comparisons; malformed fallback markers refuse. Independent minimal/empty paths are read in source."
context: "Read report validation, fallback writers and constructed binary reply controls."
limits: "No new execution credit. Fallback validation establishes the degraded form, not ordinary association consistency in retained records."
```
#### Fallback summary {summary: effect}

```contract
on: "always"
when: present(reply.reporting_failure)
effects: [set_value(reply.rc, 1), set_value(reply.normalized_outcome, "runner_reporting_failed"), set_value(reply.reporting_failure.origin, "runner_host")]
```

#### Rich fallback comparisons {rich: effect}

```contract
bind.s: reply.steps
on: "always"
when: present(reply.reporting_failure) and reply.reporting_failure.evidence_retained
each: ["s"]
effects: [withhold(reply.steps[s].comparison)]
```

#### Minimal fallback arrays {minimal: effect}

```contract
on: "always"
when: present(reply.reporting_failure) and not reply.reporting_failure.evidence_retained
effects: [set_value(reply.steps, []), set_value(reply.phases, [])]
```

#### Fallback producer identity {producer: effect}

```contract
on: "always"
when: present(reply.reporting_failure)
effects: [set_value(reply.producer.contract, ref("identity.build.contract")), set_value(reply.producer.describe, ref("identity.build.describe")), set_value(reply.producer.commit, ref("identity.build.commit"))]
```

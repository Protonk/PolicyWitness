# Controller findings and assessments {diagnostics: surface}

```contract
syntax: 1
artifact: "Controller findings and assessments"
part: "assessment"
goldens: ["tests/fixtures/contract/surfaces/diagnostics.json"]
checks: ["unit", "failure_boundaries"]
```

The controller retains the admitted host reply and publishes its own
assessment under `data.runner_sandbox_diagnostics`. Each finding has the
scope of the check that produced it. The outer result, a worker's ending,
phase order, native operation and reporting-failure form have separate
conditions.

## Execution diagnostics {execution: subject}

```contract
record: "rust.RunnerExecutionDiagnostics"
as: "diagnostics"
at: ["envelope.data.runner_sandbox_diagnostics"]
```

### process_disposition {process_disposition: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["no_worker", "clean_exit", "nonzero_exit", "signaled", "conflicting", "unconfirmed", "unrecognized", "withheld", "per_actor"]
```

The controller's disposition projection. An ordinary worker supplies its
validated lifecycle result. Actor execution uses `per_actor` when at least
one actor has a worker projection; each actor's entry supplies that ending.
A reply-wide finding sets this field to `withheld`. `no_worker` means this
projection had no worker subprocess record to assess.

### termination_cause {termination_cause: field}

A controller attribution selected from the validated lifecycle chain.
A clean ordinary exit gives null; another ordinary disposition gives
`unknown` until the host-cleanup conditions below establish one of the
named causes. Actor-form top-level diagnostics begin with null because
causes belong to the actor entries. A reply-wide finding sets this field
to `unknown`.

### stop_reason {stop_reason: field}

Supported ordinary-worker stop observation when its answer is one of
`sentinel_deadline`, `done`, `child_reaped`, `wait_error`,
`policy_write_error` or `policy_transfer_deadline`; otherwise null.
Actor stop reasons belong to their actor entries. A later reply-wide
finding preserves an already projected ordinary stop reason.

### disposition_integrity {disposition_integrity: field}

`valid` means the applicable controller checks for this projection passed;
`invalid` means they produced a finding. Null means there was no worker
projection to validate. When at least one actor has a worker projection,
actor aggregation is valid when every actor projection is valid or has null
integrity; it becomes invalid when any actor projection is invalid. With no
worker projections, aggregate integrity remains null. A reply-wide finding
also sets invalid.
A host's supported conflict can accompany valid integrity: the controller
has checked the conflict's own evidence.

### disposition_issues {disposition_issues: field}

Controller findings at this scope, followed or preceded according to the
producing check order by copied host conflict records where applicable.
Copied host conflicts preserve rule, question, step index and observations.
A nonempty list can accompany valid integrity when its records are
validated host conflicts. Actor-local findings remain in the actor entry.

### actors {actors: field}

Present for `execution_form: "actors"`, in the host's actor order. Each
entry is derived from that actor's subprocess and its actions selected
through the phase plan. A reply-wide finding preserves these already
computed actor entries.

### Admit the response before assessment {admit: acts}

```contract
who: "controller"
where: "client delivery, public reply identity and bounded response context"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Check request-delivery failure and client capture status, then exact reply identity, response geometry and compiled-profile context before execution diagnostics. A failed response-context check reports malformed_runner_response and exit 1 with the decoded host reply retained and execution diagnostics omitted.
```

A missing or foreign producer identity follows its own transport/identity
refusal. The geometry guard bounds collections before semantic joins.
The compiled-profile guard checks its status and producer/stage context,
including actor captures and reporting-failure replies. These are
preconditions for the execution-assessment path described here.

### Project one worker or aggregate actors {project: acts}

```contract
who: "controller"
where: "typed worker lifecycle interpretation after response admission"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
free.effect: Validate each worker's lifecycle against its native records and assigned actions. If that worker's validation produces any finding, set its process_disposition to withheld, termination_cause to unknown and disposition_integrity to invalid, with stop_reason null. Otherwise derive the ending from final_status and preserve validated host conflicts.
```

For the actor form, the controller computes each worker's projection
separately. It then sets the top-level disposition to `per_actor` when any
entry differs from `no_worker`, and aggregates the actor integrity values.
This calculation occurs before the reply-wide checks below.

### Apply reply-wide findings {reply_checks: acts}

```contract
who: "controller"
where: "typed reply relationship checks after worker projections"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics"]
free.condition: One or more applicable reply-wide checks finds an invalid relationship.
effects: [set_value(diagnostics.process_disposition, "withheld"), set_value(diagnostics.termination_cause, "unknown"), set_value(diagnostics.disposition_integrity, "invalid"), retain_records(reply), retain_assessments(diagnostics.actors)]
after: ["diagnostics.execution.project"]
```

The controller appends these findings to top-level `disposition_issues`.
It preserves the actor entries, an ordinary stop reason already derived,
and all host fields including step comparisons and claimed gate outcomes.
Those retained assertions can therefore appear beside the controller's
finding about them. The finding's level determines which controller
projection changes.

### Findings beside the completion result {outer_result: definition}

```contract
uses: ["envelope.data.select"]
```

The envelope's result-selection rule governs completion. Individual failed
attempts and controller integrity findings remain visible beside that result.
A reply-wide withheld disposition can therefore accompany an outer successful
result.

### Check families and applicability {families: definition}

```contract
defines: "condition"
```

An ordinary semantic reply is a reply with no reporting_failure record;
this branch includes both single-worker and actor execution forms.

| Check family | Applicability and checked relationship | Finding scope |
| --- | --- | --- |
| Lifecycle claims | Each worker subprocess: required claims, state/basis references, owned final status, cleanup facts, progress association, slot count/order, action identity, lifecycle copies and supported conflicts. | That worker's projection; ordinary projection or one actor entry. |
| Phase and query evidence | Ordinary semantic reply: phase IDs/order, action partition, collection state, validator ownership and raw-record association, protocol violations, comparison vocabulary and the complete `query_first` chain. | Reply-wide. |
| Policy delivery/read evidence | Ordinary semantic reply with a worker policy-read receipt: bounded counts, host expected-count agreement, length-refusal detail and consistency with later worker observations. | Reply-wide. |
| Native operation observations | Ordinary semantic reply: each fresh-read, fresh-write and exec observation's applicable fields and native relationships. | Reply-wide. |
| Actor association | Ordinary semantic actor reply: actor indexes/IDs, launch/subprocess PID, visits, phase owner, event owner and matching transfer source. | Reply-wide. |
| Actor setup, equipment, application, termination and custody | Ordinary semantic reply: execution-form applicability and the actor record relationships defined by those surfaces. | Reply-wide. |
| Reporting-failure form | A reply carrying reporting_failure: degraded outcome/rc/error, origin/diagnostic/original outcome, removed comparisons and the retention-specific record form. | Reply-wide. |

The reporting-failure branch checks its degradation form while retaining the
assembled records. Worker lifecycle projections still run independently,
with their comparison-limitation requirement waived when the comparison
has been removed by degradation. The retained host records remain
available for inspection at their own observation boundaries.

### Closed claim states and open answers {vocabulary: definition}

```contract
defines: "value"
```

Lifecycle claim states are `supported`, `conflicting`, `unresolved` and
`inapplicable`. A supported claim needs an answer and sufficient resolving
basis; unresolved and inapplicable need a reason. A conflicting claim
needs the matching indexed conflict record and native observations.
Another state produces an invalid-claim finding.

Some answers and summaries are open. For example, an unfamiliar
applicability answer or lifecycle summary is retained, while a known
summary is checked against the canonical lifecycle. A supported unfamiliar
final-status answer that passes the other claim checks projects as
`unrecognized`. This differs from an unknown closed claim state, which
withholds the worker projection.

### Scope example {scope_example: example}

A typed actor reply can carry a transfer naming an invalid source actor,
while another actor retains a valid clean-exit lifecycle. The controller
then publishes top-level `withheld` and an actor-evidence finding beside
that actor's `clean_exit`. If the admitted host summary is `finished`,
the outer result still reports `ok: true` and exit 0. The three values
answer the reply relationship, individual ending and host completion
questions respectively.

### Controller finding support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"execution_diagnostics"},{"path":"controller/src/porcelain_admission.rs","symbol":"project"},{"path":"controller/src/porcelain_admission.rs","symbol":"admit_reply"},{"path":"controller/src/run_flow.rs","symbol":"reply_contract"},{"path":"controller/src/run_flow.rs","symbol":"complete_execution"},{"path":"controller/src/porcelain_actor.rs","symbol":"pub(super) fn validate"},{"path":"controller/src/porcelain_native.rs","symbol":"pub(super) fn validate"}]
check: [{"path":"controller/src/porcelain_admission.rs","symbol":"typed_invalid_actor_account_keeps_independent_actor_endings","form":"test"},{"path":"controller/src/porcelain_admission.rs","symbol":"typed_degradation_never_certifies_surviving_comparison","form":"test"},{"path":"controller/src/porcelain_admission.rs","symbol":"typed_future_applicability_and_summary_remain_open_without_rewriting","form":"test"},{"path":"controller/src/run_flow.rs","symbol":"malformed_phase_claims_withhold_projection_and_preserve_raw_reply","form":"test"},{"path":"controller/src/run_flow.rs","symbol":"execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields","form":"test"}]
pins: "Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches."
context: "Typed controller implementation and the named constructed tests were read."
limits: "Actor/native family entry points and the complete gate checks were read; their detailed operation predicates have separate source owners. The scope example combines separately inspected projection and outer-result controls."
```

### Shared reader evidence {reader_evidence: gap}

```contract
kind: "evidence"
```

The host self-check, controller reader and harness reader are separate
implementations of the public relationships. The prior constructed
comparison found divergent judgments. Shared acceptance and refusal
controls still need to be reconciled around each rule's applicability,
including preparation failures and reporting failures. This draft credits
the controller branches and inspected controls above; integrated release
execution remains to be attached.

## One actor's diagnostics {actor: subject}

```contract
record: "rust.ActorExecutionDiagnostics"
as: "actor_diagnostics"
```

### actor_id {actor_id: field}

The host actor label copied into an actor-form diagnostic entry. The
underlying projection helper begins with null; actor assembly supplies
the label even when that actor has no subprocess record.

### process_disposition {process_disposition: field}

The actor's own worker projection, chosen by the mapping below after its
lifecycle checks pass. Local findings yield `withheld`; a missing
subprocess record yields `no_worker`.

### termination_cause {termination_cause: field}

Null for `clean_exit` or `no_worker`, otherwise `unknown` unless the
validated host-cleanup chain supplies a named cause below.

### stop_reason {stop_reason: field}

The actor worker's supported stop reason from the recognized set listed
for execution diagnostics. Null when no supported recognized answer was
projected, including when local lifecycle validation failed.

### disposition_integrity {disposition_integrity: field}

`valid` when this worker's lifecycle checks passed, `invalid` when they
produced a finding, and null when its subprocess record is absent. A
reply-wide finding preserves this actor-local value.

### disposition_issues {disposition_issues: field}

Findings from this actor's lifecycle validation, or copied validated host
conflicts after successful validation. Reply-wide actor-association or
equipment findings appear in the execution-level issue list.

### Ending mapping {mapping: definition}

```contract
defines: "assessment"
```

| Validated host final_status | Controller process_disposition |
| --- | --- |
| supported, answer exit_code, integer value 0 | clean_exit |
| supported, answer exit_code, another integer value | nonzero_exit |
| supported, answer signal | signaled |
| conflicting with a matching supported conflict record | conflicting |
| unresolved with a reason | unconfirmed |
| inapplicable with a reason | unconfirmed |
| another otherwise admitted answer | unrecognized |

The `unconfirmed` value merges the two host states while the retained
host claim preserves which state and reason it supplied.

### Host-cleanup attribution {cause: acts}

```contract
who: "controller"
where: "validated worker ending projection"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
free.condition: The validated ending is signaled; cleanup trigger and exhausted grace are supported; the supported kill claim names a request with rc zero whose signal equals the observed final signal.
free.effect: Select the named host-cleanup cause from its cleanup trigger. Preserve unknown when that complete chain or a recognized trigger is absent.
```

| Cleanup trigger | termination_cause |
| --- | --- |
| deadline_expiry | host_sentinel_deadline |
| completion | host_exit_grace_exhausted |
| poll_wait_error | host_cleanup_after_wait_error |
| policy_transfer_error | host_cleanup_after_transfer_error |
| policy_transfer_timeout | host_cleanup_after_transfer_timeout |

The request result, exhausted grace and owned final status are independent
observations in this chain. A successful signal request alone supplies
its own request result; attribution requires the other observations.

### Actor projection support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"project"},{"path":"controller/src/porcelain_admission.rs","symbol":"validate_lifecycle"},{"path":"controller/src/porcelain_admission.rs","symbol":"check_claim"}]
check: [{"path":"controller/src/porcelain_admission.rs","symbol":"typed_host_cleanup_cause_requires_all_independent_observations","form":"test"},{"path":"controller/src/porcelain_admission.rs","symbol":"typed_invalid_actor_account_keeps_independent_actor_endings","form":"test"}]
pins: "The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain."
context: "Full projection and lifecycle validation read; constructed cleanup and scope controls read."
limits: "The read cleanup test covers completion, deadline, wait-error and future-trigger cases. Transfer-error and transfer-timeout causes were read in source; no execution is credited."
```

## Integrity finding {issue: subject}

```contract
record: "rust.IntegrityIssue"
as: "integrity_issue"
```

### kind {kind: field}

```contract
vocabulary: "open"
listed: "illustrative"
values: ["missing_record", "malformed_record", "invalid_claim", "unresolved_reference", "phase_collection", "ordering", "policy_read", "fresh_read", "fresh_write", "exec_observation", "actor_evidence", "reporting_failure", "conflict"]
unknown: "An unfamiliar category remains a finding with its carried detail and scope; interpreting its specific condition requires that producer's definition."
```

Category supplied by the controller check or copied from a host conflict.
A finding's origin and effect follow the producing scope and the remaining
fields, rather than an exhaustive match over this list.

### detail {detail: field}

Human-readable explanation of the failed relationship or copied host
conflict. Some controller details embed a step label or position; other
actor and gate findings carry a general explanation.

### rule {rule: field}

Host conflict rule copied from the retained disposition issue, such as
D1 for a final-status conflict or D5 for the supported step conflicts.
Controller-created findings currently omit this field.

### question {question: field}

Host question associated with a copied conflict. Controller-created
findings currently omit this field even when a detail names the question.

### step_index {step_index: field}

Worker-local step index copied from a host conflict when it has step
scope. A copied run-level conflict and controller-created findings omit it.

### observations {observations: field}

Host observation-reference list copied from a validated conflict.
Controller-created findings currently omit this field.

### Retain observation and finding separately {retain: acts}

```contract
who: "controller"
where: "integrity finding construction"
entry: ["cli_run"]
recipient: ["report_reader"]
report: ["execution_diagnostics", "actor_execution_diagnostics"]
free.effect: Publish controller findings as kind and detail. Copy validated host conflicts with their rule, question, step index and observation references. Preserve the host reply independently of both forms.
```

### Structured finding subjects {subject_gap: gap}

```contract
kind: "meaning"
```

Controller-generated findings currently identify their affected phase or
actor through surrounding scope and, where supplied, human detail.
A structured reference to the specific phase, actor or assertion remains
unimplemented. Adding that reference must preserve the existing distinction
between worker-local projection findings and reply-wide findings.

### Finding construction support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"controller/src/porcelain_admission.rs","symbol":"IntegrityIssue"},{"path":"controller/src/porcelain_admission.rs","symbol":"fn issue"},{"path":"controller/src/porcelain_admission.rs","symbol":"for i in &sub.disposition"},{"path":"controller/src/porcelain_actor.rs","symbol":"fn require"},{"path":"controller/src/porcelain_actor.rs","symbol":"fn gates"},{"path":"controller/src/porcelain_native.rs","symbol":"pub(super) fn validate"}]
pins: "Generic controller findings omit optional host-conflict metadata; copied host issues preserve it. Gate findings use the generic actor-evidence constructor."
context: "Constructors, projection copy, actor gate checks and native validator dispatch read."
limits: "The proposed structured subject is a visible gap, not a field added by this draft."
```

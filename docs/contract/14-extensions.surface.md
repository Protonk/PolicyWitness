# Extension actions and authority custody {extensions: surface}

```contract
syntax: 1
artifact: "Extension actions and authority custody"
part: "input"
goldens: ["tests/fixtures/contract/surfaces/extensions.json"]
checks: ["failure_boundaries"]
```



The actor form carries explicit issue, transfer, consume and release actions. A reference names a declared resource within this specimen; native results, custody acknowledgements and later file observations each have their own producing boundary.

## Extension action {action: subject}

```contract
record: "PWRunnerExtensionAction"
as: "action"
```



### step_id {step_id: field}

Unique nonempty identifier across all specimen actions, bounded by <!-- span limits.step_id.value_unit -->63 UTF-8 bytes<!-- /span -->.

### extension {extension: field}

Closed extension operation for the active actor. Its presence selects extension-action decoding; a null object is refused.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerExtension.swift", "symbol": "PWRunnerExtensionAction"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```



## Extension operation {operation: subject}

```contract
record: "PWRunnerExtensionOperation"
as: "operation"
```

Every supplied operand is checked for applicability, including null. Required operands must contain strings. References are nonempty, NUL-free and bounded by <!-- span limits.extension_reference.value_unit -->63 UTF-8 bytes<!-- /span -->.

### operation {operation: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["issue", "transfer", "consume", "release"]
```

Select the operation and its exact applicable operands.

### token_ref {token_ref: field}

```contract
required_when: operation.operation in ["issue", "transfer"]
present_when: operation.operation in ["issue", "transfer"]
```

Required new token reference for issue; required previously assigned token owned by the active actor for transfer. Other operations require this field absent.

### handle_ref {handle_ref: field}

```contract
required_when: operation.operation in ["consume", "release"]
present_when: operation.operation in ["consume", "release"]
```

Required new handle reference for consume; required previously assigned handle owned by the active actor for release. Other operations require this field absent.

### family {family: field}

```contract
required_when: operation.operation == "issue"
present_when: operation.operation == "issue"
```

Required `file` for issue. Other operations require this field absent.

### target {target: field}

```contract
required_when: operation.operation == "issue"
present_when: operation.operation == "issue"
```

Required absolute file or directory path for issue, bounded by <!-- span limits.extension_issue_target.value_unit -->1,023 UTF-8 bytes<!-- /span -->. The exact submitted bytes reach native issuance. Other operations require this field absent.

### authority {authority: field}

```contract
required_when: operation.operation == "issue"
present_when: operation.operation == "issue"
```

Required `read` or `read_write` for issue, selecting `com.apple.app-sandbox.read` or `com.apple.app-sandbox.read-write`. Other operations require this field absent.

### recipient {recipient: field}

```contract
required_when: operation.operation == "transfer"
present_when: operation.operation == "transfer"
```

Required known actor ID for transfer; may name the active actor itself. Other operations require this field absent.

### delivery_ref {delivery_ref: field}

```contract
required_when: operation.operation in ["transfer", "consume"]
present_when: operation.operation in ["transfer", "consume"]
```

Required new delivery reference for transfer; required previously assigned delivery owned by the active recipient for consume. Other operations require this field absent.

### Operation grammar {grammar: definition}

```contract
defines: "action"
```

| Operation | Required operands | Producing actor and consequence |
| --- | --- | --- |
| `issue` | `family`, `target`, `authority`, `token_ref` | Active actor calls native file issuance once with class selected by authority, exact target and flags zero; assigns the declared token resource. |
| `transfer` | `token_ref`, `recipient`, `delivery_ref` | Token-owning actor publishes a host request for one assigned recipient slot; assigns the delivery resource. |
| `consume` | `delivery_ref`, `handle_ref` | Recipient actor calls native consume on its usable delivered token; assigns the handle resource. |
| `release` | `handle_ref` | Consuming actor calls native release for its candidate handle. |

Each other operand must be absent. A required null operand is missing for this grammar; an extraneous null operand is inapplicable.

### Resolve references and ownership {references: acts}

```contract
who: "host"
where: "whole actor-plan admission"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Assign each token, delivery and handle reference once across a shared specimen namespace. Require each use after its declared producer and enforce token-owner transfer, recipient-owned delivery consumption and consumer-owned handle release. Permit a handle at most one declared release.
```

The same token may be transferred to multiple recipients or repeatedly to one recipient using distinct delivery references. A delivery may be consumed repeatedly using distinct handle references. Syntactic ordering establishes which resource is requested; the later resource record establishes what was observed.

### Bound the declared resource plan {capacity: acts}

```contract
who: "host"
where: "pre-child admission"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Refuse plans exceeding <!-- span limits.actor_issues.value_unit -->32 items<!-- /span --> issues, <!-- span limits.actor_deliveries.value_unit -->64 items<!-- /span --> deliveries, <!-- span limits.actor_handles.value_unit -->64 items<!-- /span --> handles or <!-- span limits.actor_releases.value_unit -->64 items<!-- /span --> releases. Count every extension action toward the shared <!-- span limits.probe_steps.value_unit -->256 items<!-- /span --> action capacity.
uses: ["request.specimen"]
```



### Exclude exec in participating actors {exec: acts}

```contract
who: "host"
where: "actor-plan admission"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Mark issuers, senders, consumers, releasers and transfer recipients as extension participants. Refuse any exec probe in those actors; retain exec availability in other actors.
uses: ["probes.attempt"]
```



### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerExtension.swift", "symbol": "actorOperands"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "actorAdmissionFailure"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```



## Custody protocol {custody: subject}

Authority payloads occupy bounded native storage assigned to the admitted resource plan. Public records expose references, lengths, framing, status and observations. Token bytes stay in the native custody channels.

### Prepare before use {prepare: acts}

```contract
who: "host and actor worker"
where: "host custody preparation before launch and actor setup before application or unapplied declaration"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: When the admitted resource plan contains a token or delivery, the host attempts to disable core dumps; after that succeeds, it prepares one authority region for every actor and a bounded custody buffer for each token. Failure of this host custody preparation prevents every actor launch. Each actor worker reaching authority setup looks up extension symbols and attempts its own core-dump limit. Required setup publishes ready after mapping and validating its assigned region; a primary failure publishes terminal_required_failure and ends the worker before policy setup. Unneeded authority selects not_required without mapping, including when the core-limit attempt failed. These worker setup operations precede application or the actor's unapplied declaration. A reached extension action reports unavailability for missing required apparatus or symbols.
uses: ["equipment.authority_setup"]
```



### Issue and transfer payload ownership {issue: acts}

```contract
who: "issuing worker and host"
where: "outbound token publication"
entry: ["actor_worker"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Publish a one-shot bounded token only when native issuance returned a non-null payload with length from one through <!-- span limits.extension_token_payload.value_unit -->16,383 bytes<!-- /span -->. Erase the native allocation after copying. Keep the published outbound slot immutable until the host validates, copies or rejects it, erases its payload and acknowledges it.
```

The slot owns one declared issue. A worker timeout or exit leaves its published bytes available for the host's later copy and erasure. Another issue uses another slot. The native return and host custody acceptance are reported independently.

### Acknowledge, compare and settle delivery {deliver: acts}

```contract
who: "host and recipient worker"
where: "explicit transfer exchange"
entry: ["actor_worker"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Require a valid transfer request and held host custody, copy into the assigned recipient slot, obtain recipient framing acknowledgement and compare its complete length and bytes with custody. Set delivered and publish settlement only after accepted acknowledgement and equal bytes. On failure publish the corresponding acknowledgement and withdraw the delivery.
```

A parked recipient validates framing. A self-transfer also services inbound work while waiting. Consumption requires settled, committed and accepted delivery. Each exchange is bounded by <!-- span limits.actor_exchange_allowance.value_unit -->5,000 milliseconds<!-- /span --> and the remaining actor budget; timeout and clock observations retain their own boundary.

### Observe the source answer {source_answer: acts}

```contract
who: "host"
where: "reply assembly after transfer"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Set source_acknowledged only when the source action completed and its published transfer status matches the host's nonzero acknowledgement. Preserve late host answers independently of an unpublished or differently completed source action.
```



### Erase at declared last use and teardown {erase: acts}

```contract
who: "host and workers"
where: "resource retirement"
entry: ["actor_xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Erase host-private custody at the last declared transfer (or after issue when never transferred) and at teardown. Erase worker-owned inbound payloads after their last declared consume and at normal exit once host settlement transfers ownership. At host teardown erase shared regions only for actors whose termination is established; otherwise detach the host mapping.
```

A last transfer retires custody even when the recipient is unavailable. Payload erasure is a memory-lifetime action; a native release request and the later access observation are separate operations.

### Native extension evidence scope {native_library: definition}

```contract
defines: "value"
```

Native extension issuance, consumption and release observations are scoped to the concrete policy, entitlements, resource, token bytes and macOS build. Host custody records describe the controlled publication, copying and erasure protocol. A release return records that native call; subsequent access is established by the corresponding access observation.

#### Disposition support {disposition_support: owner}

```contract
grade: "source_read"
source: {"path":"runner/Sources/PWRunnerCore/AuthorityCustody.swift","symbol":"serviceTransfer"}
pins: "Host transfer observations record custody, copying, recipient acknowledgement and equality separately."
context: "Static review of the cited production branches."
limits: "Private-library allocation and opaque token behavior retain the scope of their native observations."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "var authorityRequired: Bool"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "if !plan.authorityRequired { authority = nil; return }"}, {"path": "runner/Sources/PWRunnerCore/ActorScheduler.swift", "symbol": "if let plan = input.authority"}, {"path": "runner/Sources/PWRunnerCore/AuthorityCustody.swift", "symbol": "init(plan: AuthorityPlan, actorCount: Int, calls: ChildProcessCalls)"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "static void prepare_authority"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "if (hdr->actor_mode == PW_ACTOR_MODE_UNAPPLIED)"}, {"path": "runner/Sources/PWRunnerCore/AuthorityCustody.swift", "symbol": "serviceOutbound"}, {"path": "runner/Sources/PWRunnerCore/AuthorityCustody.swift", "symbol": "serviceTransfer"}, {"path": "runner/Sources/PWRunnerCore/AuthorityCustody.swift", "symbol": "recordSourceAcknowledgements"}, {"path": "runner/Sources/PWRunnerCore/AuthorityCustody.swift", "symbol": "finish"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_extension_issue"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_extension_consume_actor"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "erase_authority"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Conditional host/worker setup, host custody service and worker issue/transfer/consume/release have source-read support here. Collected setup-account meanings are owned by the equipment surface. Native private-library behavior remains environment-specific evidence."
```



## Extension experiments {examples: subject}

These schedules keep declaration, native action, delivered payload and fresh access observations separate.

### Before, during and after consumption {before_during_after: example}

Declare actors `issuer` and `reader`. Choose the issuer's equipment and sandbox policy to exercise issuance authority, and a reader policy whose baseline denies the chosen path. Use an exact absolute target:

| Phase owner | Actions in declaration order |
| --- | --- |
| `reader` | `read_fresh` before receiving authority |
| `issuer` | issue `token_ref: "t"`, family `file`, authority `read`; transfer `t` to `reader` as `delivery_ref: "d"` |
| `reader` | consume `d` as `handle_ref: "h"`; `read_fresh`; release `h`; `read_fresh` again |

The first read supplies the baseline. The middle read supplies access during this handle's lifetime. The last read supplies a later access observation after the native release call. Compare their actual file identity and content observations. A non-null issue result, delivered bytes, consume result and release result each remain visible even when a read fails.

### Three-actor redelegation {redelegation: example}

Declare `A`, `B` and `C` with their own sandbox and equipment choices. Read the target freshly in `B` and `C` to establish their baselines. `A` issues a token and transfers it to `B`; `B` consumes that delivery, performs a fresh read, then issues its own token and transfers that token to `C`. `C` consumes its delivery and reads freshly.

The second issuance is `B`'s own native action under its then-current state. Keep the two issue events, two custody/delivery chains, two candidate handles and the readers' file observations distinct. `read_write` may name an absolute directory target; fresh writes or exclusive creation within that directory expose their own file effects.

### Instantiated extension schedules {execution: definition}

```contract
defines: "value"
```

An executed extension schedule fixes concrete actor roles, policies, entitlements, paths and phase boundaries. Its account distinguishes native issue/consume/release returns, host custody and transfers, and fresh access before and after the operations. Those inputs and retained observations identify the schedule supported by that execution.

#### Disposition support {disposition_support: owner}

```contract
grade: "source_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorOrchestration.swift","symbol":"assembleActorReply"}
pins: "Reply assembly retains extension events, transfer observations and resource accounts by their declared actions."
context: "Static review of the cited production branches."
limits: "Native examples require their concrete input and selected-platform observations."
```

#### Native schedule execution support {execution_support: owner}

```contract
grade: "executed"
source: [{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"attempt_extension_issue"},{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"attempt_file_read_fresh"},{"path":"runner/Sources/PWRunnerCore/ActorOrchestration.swift","symbol":"assembleActorReply"}]
check: [{"path":"tests/suites/witness_contract/check_extensions.py","symbol":"run_targets","form":"test"},{"path":"tests/suites/witness_contract/check_extension_redelegation.py","symbol":"chain","form":"test"},{"path":"tests/suites/witness_contract/check_extension_directory.py","symbol":"run","form":"test"}]
pins: "Concrete before/during/after access, the extracted guide JSON example, credited three-actor redelegation and separate directory authority retain native calls, custody/transfer observations and independently identified file effects."
context: "Passed signed-CLI cases with their recorded policies, equipment, paths and macOS 26.7.1/25G241 arm64 environment; inspected native results, principal credit, file observations and owned cleanup."
limits: "The before/during/after instance splits reader actions across visits. Redelegation includes B/C control-path reads and the retained policies. Directory writes and exclusive creation form a separate experiment. The extracted guide JSON and the guide's full shell workflows have separate execution scopes."
run: "20261111T155411Z_29ef0802; witness_contract/extensions, witness_contract/extension_redelegation and witness_contract/extension_directory"
build: "Signed candidate build 1335, version 0.3.7, b6ce6d266ff281fafdae44c32061ceff018485bb dirty; development:1445cd80509c983c6894339523f9f13ad08f5e003de4cb29ce1c398527c42f28"
```

### Example support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "normalizeActorPlan"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_extension_issue"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_file_read_fresh"}]
pins: "Admission supports these resource chains and native operations."
context: "Admission and native-operation source for the teaching schedules."
limits: "Native examples are scoped to their recorded policies, equipment, targets and platform. Before/during/after access was observed with an unapplied unentitled issuer and an applied selected subject, with reader actions split across visits. Three-actor redelegation was observed with the retained B/C policies and added control-path reads. Directory read-write authority was exercised separately through fresh writes and exclusive creation. Release results and later access observations retain their individual meanings."
```



## Extension event {event: subject}

```contract
record: "PWRunnerExtensionEvent"
as: "event"
part: "report"
```



### phase_id {phase_id: field}

Declared phase containing the action.

### step_id {step_id: field}

Declared action identifier.

### operation {operation: field}

Requested issue, transfer, consume or release operation.

### token_ref {token_ref: field}

Declared token reference for issue and transfer; omitted for consume and release.

### handle_ref {handle_ref: field}

Declared handle reference for consume and release; omitted for issue and transfer.

### call_boundary_observed {call_boundary_observed: field}

Whether the host observed the worker's release-published marker immediately before a native issue, consume or release call. Transfer uses its separate request publication.

### result_published {result_published: field}

Whether the action's result slot was completed and observed. A false value withholds native result fields even if a call boundary was observed.

### status {status: field}

`returned` when a completed native result exists; `unavailable` for a published no-call reason; `unresolved` for missing action publication; `invalid` for a completed inconsistent slot. Transfer uses its acknowledgement status.

### native_result {native_result: field}

Published signed native result: issue uses 1 for non-null or 0 for null; consume and release retain their signed result. Consume -1 supplies no handle; another published consume result is the candidate handle.

### errno {errno: field}

Errno captured immediately after the native call when a native result was published. Its value remains paired with that result, including zero.

### unavailable_reason {unavailable_reason: field}

Published apparatus reason such as token_unavailable, handle_unavailable, native_api_unavailable, repeated_action, authority_channel_unavailable or delivery_unavailable; omitted when no reason was published.

### lifecycle {lifecycle: field}

Assessment of the action's observed boundary/publication from its actor's disposition evidence.

### actor_id {actor_id: field}

Actor owning this action.

### family {family: field}

The implemented extension family, `file`.

### target {target: field}

Exact declared issue target, present for issue.

### extension_class {extension_class: field}

Native issue class selected from read/read_write, present for issue.

### flags {flags: field}

Native issue flags; the implementation supplies zero.

### delivery_ref {delivery_ref: field}

Declared delivery reference for transfer and consume.

### native_nonnull {native_nonnull: field}

Issue result projected as true for published native 1 and false for another published native value; absent without a native result.

### token_length {token_length: field}

Length carried by a completed issue publication, including zero when no bounded token was published. Public payload length excludes the NUL terminator.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerExtension.swift", "symbol": "PWRunnerExtensionEvent"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "assembleActorReply"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_extension_issue"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "attempt_extension_consume_actor"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```



## Host transfer observation {transfer: subject}

```contract
record: "PWRunnerTransferRecord"
as: "transfer"
part: "report"
```

The transfer table reports host servicing observations. A worker can time out before the host's answer; source acknowledgement preserves this difference.

### phase_id {phase_id: field}

Phase in which this transfer action was declared.

### step_id {step_id: field}

Transfer action identifier.

### source_actor_id {source_actor_id: field}

Actor owning the token and requesting the transfer.

### recipient_actor_id {recipient_actor_id: field}

Actor assigned the inbound delivery.

### token_ref {token_ref: field}

Requested source token.

### delivery_ref {delivery_ref: field}

Assigned delivery resource.

### request_published {request_published: field}

Whether the host observed the explicit transfer request publication.

### custody_status {custody_status: field}

`held` when the host found accepted, unerased custody for this request; otherwise `unavailable`.

### copy_status {copy_status: field}

`copied` after the host copied custody into the inbound slot; otherwise `not_copied`.

### equality {equality: field}

`equal` or `unequal` after comparing acknowledged recipient bytes to custody; otherwise `not_compared`.

### recipient_acknowledged {recipient_acknowledged: field}

True when the recipient published either framing acceptance or rejection. Read status to distinguish which.

### source_acknowledged {source_acknowledged: field}

True only when the source published a completed action carrying the matching host acknowledgement.

### status {status: field}

Host acknowledgement name: none, delivered, custody_unavailable, recipient_rejected, recipient_timeout, recipient_unavailable, request_invalid, host_timeout, clock_fault or copy_mismatch. Unrecognized raw acknowledgement values are retained as strings by this producer.

### lifecycle {lifecycle: field}

Source action's lifecycle assessment when available.

### recipient_wait {recipient_wait: field}

Host clock and stop observation for the bounded recipient-acknowledgement wait, when that wait was entered.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/AuthorityCustody.swift", "symbol": "TransferObservation"}, {"path": "runner/Sources/PWRunnerCore/AuthorityCustody.swift", "symbol": "serviceTransfer"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "PWRunnerTransferRecord"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```



## Resource tables {resources: subject}

```contract
record: "PWRunnerResourceTables"
as: "resources"
part: "report"
```

The tables retain admitted resources whose producing action was not reached or remains unresolved. Declaration establishes the reference; the status supplies observed production.

### tokens {tokens: field}

Every admitted issue resource in plan order, with its observed production and custody status.

### deliveries {deliveries: field}

Every admitted transfer resource in plan order, with its observed delivery status.

### handles {handles: field}

Every admitted consume resource in plan order, with its candidate handle and declared release observations.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerActors.swift", "symbol": "PWRunnerResourceTables"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "tokenRecords"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```



## Token resource {token: subject}

```contract
record: "PWRunnerTokenRecord"
as: "token"
part: "report"
```



### token_ref {token_ref: field}

Declared token identifier.

### actor_id {actor_id: field}

Issuing actor.

### step_id {step_id: field}

Issue action identifier.

### family {family: field}

Declared extension family.

### status {status: field}

`issued` requires a completed non-null issue result and accepted host custody; `issued_uncustodied` retains a completed non-null result without accepted custody; `null` records native null; `unavailable` records a no-call reason; `invalid` records an inconsistent completed result. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`.

### token_length {token_length: field}

Length available from the issue slot's extension publication, when present.

### last_use_step_id {last_use_step_id: field}

Final declared transfer using this token, or the issue itself when no transfer is declared.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "tokenRecords"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "unpublishedResourceStatus"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```



## Delivery resource {delivery: subject}

```contract
record: "PWRunnerDeliveryRecord"
as: "delivery"
part: "report"
```



### delivery_ref {delivery_ref: field}

Declared delivery identifier.

### token_ref {token_ref: field}

Token selected for delivery.

### source_actor_id {source_actor_id: field}

Token owner and transfer source.

### recipient_actor_id {recipient_actor_id: field}

Actor assigned the delivery.

### step_id {step_id: field}

Transfer action identifier.

### status {status: field}

Host acknowledgement when a transfer observation exists; otherwise the completed slot's unavailable reason or `unrequested`. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`.

### delivered_length {delivered_length: field}

Host custody length only when the acknowledgement is delivered.

### equality {equality: field}

Host equality comparison when a transfer observation exists.

### last_use_step_id {last_use_step_id: field}

Last declared consume using this delivery, or its transfer action when no consume is declared.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "deliveryRecords"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```



## Handle resource {handle: subject}

```contract
record: "PWRunnerHandleRecord"
as: "handle"
part: "report"
```



### handle_ref {handle_ref: field}

Declared handle identifier.

### delivery_ref {delivery_ref: field}

Delivery consumed to produce this candidate.

### actor_id {actor_id: field}

Consuming actor and handle owner.

### step_id {step_id: field}

Consume action identifier.

### status {status: field}

`produced` requires a completed native result other than -1; `consume_failed` records completed -1; `unavailable` records a no-call reason; `invalid` records inconsistent completed evidence. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`.

### native_handle {native_handle: field}

Candidate signed handle only when status is produced.

### raw_equal_handles {raw_equal_handles: field}

Other declared handle references in the same actor whose slot has an equal raw native result. Equality relates raw numbers; declarations retain distinct reference identity.

### release_step_id {release_step_id: field}

Declared release action for this handle, or null/absence when no release was declared.

### release_attempted {release_attempted: field}

Whether the declared release action has an observed native call-boundary marker.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "handleRecords"}]
pins: "The adjacent meanings follow the named request, producer and observation branches."
context: "Current source read for this draft."
limits: "Source inspection supplies these branch meanings; this draft credits no execution."
```

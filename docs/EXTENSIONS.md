# Sandbox extensions in PolicyWitness

This document is the authored source for what PolicyWitness covers of macOS
sandbox extensions: the two accepted request forms, the native calls each
operation makes, the lifecycle rules for references, how authority moves
between processes, what each observation establishes and where the coverage
stops. The section between the shared markers is copied into the user guide's
sandbox-extension section by `docs/generate_limits.py`; links written as
`PolicyWitness.md#anchor` become internal links in the copy. Repository
citations stay outside the shared region.

Implementation references, in the order a request meets them: request
normalization in [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift);
the schedule in [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift);
host custody and transfer servicing in
[AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift);
the per-actor authority region layout in
[pw_authority_region.h](../controller/tools/pw_probe_runner/pw_authority_region.h);
the worker's issue, transfer, consume, release and parked servicing in
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c);
and reply assembly in
[ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift).
The declaration path keeps [ExtensionIssuer.swift](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift)
and [pw_extension_issuer.c](../controller/tools/pw_probe_runner/pw_extension_issuer.c).
The live tests are the actor authority and actor reply groups of the
[runner unit tests](../runner/Tests/PWRunnerCoreTests), the harness activation
rows in [runner_c_worker_harness](../tests/suites/runner_c_worker_harness/README.md)
and the `witness_contract` extension cases.

<!-- BEGIN SHARED EXTENSION COVERAGE -->

## Two request forms

PolicyWitness accepts two ways to put a sandbox extension into an experiment.
Both are current; neither is deprecated.

| Form | How authority enters | Processes | Fields |
| --- | --- | --- | --- |
| Declaration | A fresh helper outside the specimen sandbox issues one token before the worker exists; the host delivers it to the one worker over a transient channel. | One worker under one policy, plus the issuer. | `policy`, `extensions: [{token_ref, target, authority}]`, explicit `phases` with `consume` and `release` actions. |
| Actors | An actor issues a token itself, after its own setup, and transfers it explicitly to another actor through host custody. | One fresh worker per actor; an actor is `apply` (its own policy) or `unapplied` (the runner's ordinary authority). Every declared actor owns at least one phase. | `actors: [{actor_id, sandbox: {mode, policy}}]`, explicit `phases` each naming an `actor_id`, with `issue`, `transfer`, `consume` and `release` actions. |

The declaration form answers "what does a consumed token do under this
policy". The actor form also answers "can a process that consumed a token
issue another one for the same file, and can a third process use it": the
re-delegation question, which needs issuance to happen inside the sandboxed
process rather than in a helper.

## Supported families and native calls

| Family | `authority` | Native class | Issue | Consume | Release |
| --- | --- | --- | --- | --- | --- |
| `file` | `read` | `com.apple.app-sandbox.read` | `sandbox_extension_issue_file(class, path, 0)` | `sandbox_extension_consume(token)` | `sandbox_extension_release(handle)` |
| `file` | `read_write` | `com.apple.app-sandbox.read-write` | the same call with the read-write class | the same | the same |

The family table is the whole supported set. The issue call receives the
submitted path bytes unchanged and flags zero; the declaration form resolves
its target with `realpath` before issuance and records both paths, the actor
form passes the submitted absolute path. Raw class names, token bytes and
flags are never request fields. No other extension class or kind of token is
issued, transported or consumed, and nothing here promises coverage of other
macOS extension mechanisms.

## Operations and references

| Operation | Who | Operands | Produces |
| --- | --- | --- | --- |
| `issue` | an actor | `family`, `authority`, absolute `target`, new `token_ref` | a token the host takes into custody when the native call returns one |
| `transfer` | the actor that issued the token | `token_ref`, `recipient` actor, new `delivery_ref` | a delivery the recipient accepts while parked or during its own wait |
| `consume` | the recipient of a delivery (actor form) or the one worker (declaration form) | `delivery_ref` or `token_ref`, new `handle_ref` | a candidate handle when the native call returns one |
| `release` | the actor that consumed | `handle_ref` | the native release result |

References are specimen-local names. Each `token_ref`, `delivery_ref` and
`handle_ref` is assigned once, used only after its producer in action order,
and stays with its owner: only the issuer transfers its token, only the
recipient consumes a delivery, only the consumer releases its handle. A
delivery may be consumed more than once with distinct handles, a token may be
transferred to several recipients or back to its issuer, and each handle is
released at most once. An actor that issues, transfers, receives, consumes or
releases cannot also run an `exec` attempt; another actor in the same specimen
can. The capacities are in the [limits](PolicyWitness.md#limits).

## How authority moves

Each actor has its own evidence region and its own authority region; neither
is visible to another actor or to a validator. An issued token is written once
into the issuing actor's outbound slot, copied by the host into a fixed custody
buffer after framing checks, and acknowledged. A transfer is a request the
host answers: it copies the custody bytes into the recipient's assigned inbound
slot, waits for the recipient to validate and acknowledge them, compares the
two copies, and reports the outcome to the sender. The recipient accepts a
delivery while parked between its visits; it consumes only in a later visit of
its own, after that phase's queries were collected and the host released it.
The host erases custody at the token's last declared transfer and at teardown;
each worker erases its slots at its last declared use and on every ordinary
exit. Tokens never enter the request, the reply, logs or diagnostics.

Every actor's worker is launched with an empty environment, null standard
streams and only its policy pipe, evidence region, readiness pipe and authority
region as inherited descriptors. The host disables core dumps before any token
can arrive, and so does each worker before mapping its region.

## What each observation establishes

| Observation | Establishes | Does not establish |
| --- | --- | --- |
| `extension_events[]` with operation `issue`, `status: returned`, `native_nonnull: true` | That actor's process made the native issue call for the recorded class and path and received a nonnull result of the recorded length. | That the token is usable by anyone, or why it was granted. |
| `issue` with `native_nonnull: false` | The native call returned NULL; `errno` is the value saved immediately after it. | A sandbox cause for the refusal. |
| `resources.tokens[].status: issued` | The host accepted the published bytes into custody. | Delivery or consumption. |
| `transfers[].status: delivered` with `equality: equal` | The recipient acknowledged a framed delivery whose bytes equalled the host's custody copy. | Consumption or access. |
| `transfers[]` with any other status | Where the exchange stopped: custody absent, recipient refusal, timeout, mismatch. No native result belongs to a transfer. | A native refusal. |
| `consume` with `status: returned` and `native_result` other than the failure sentinel | That actor received a candidate handle for the delivery it named. | Effective permission for any operation. |
| `release` with `status: returned` | The native release call returned the recorded value. | Revocation of access or undoing of earlier effects. |
| `status: unavailable` with an `unavailable_reason` | The named operation was not called for the recorded reason (no delivery, no handle, missing native symbol, no authority channel, repeated action). | A native result of any kind. |
| `status: unresolved` | The action's result was never published: the actor died, was stopped or never reached it. | That the call did not happen. |
| A fresh read that succeeds after a consume | That process could open and read the file at that moment. | That the consumed extension caused it; compare with the actor's baseline read and its policy. |

Native results, host custody facts, recipient acknowledgements and the
validator's predictions are separate records with separate writers. The
`sandbox_check` query cannot represent an extension class beside a path, so
`file-issue-extension` predictions do not distinguish issuance outcomes and
extension events stay outside the query/attempt comparison.

## What can go wrong, and how it reads

| Situation | Reading |
| --- | --- |
| An actor's policy does not compile or apply | That actor's `setup_status` is `setup_failed`; its visits are `actor_unavailable`; other actors' evidence stands. The run is `runner_failed`. |
| An actor dies during a visit | The visit records how it ended; the scheduler establishes the actor is reaped before activating anyone else; later visits of that actor are unavailable. |
| The shared lifetime cutoff expires | Each affected worker publishes a timing failure and exits; parked actors stop too. |
| The issuing actor publishes a token the host rejects | `resources.tokens[].status` is `issued_uncustodied` and `transfers[]` of that token read `custody_unavailable`. |
| A recipient rejects or does not acknowledge a delivery | The transfer reads `recipient_rejected`, `recipient_timeout` or `recipient_unavailable`; the recipient's later consume is `unavailable` for want of a delivery. |
| Native symbols are missing in the worker | The affected operations are `unavailable` with `native_api_unavailable`; unrelated reads still run. |

<!-- END SHARED EXTENSION COVERAGE -->

## Scope notes for maintainers

The shared region above must stay standalone: no repository links, no
reference definitions, and only internal guide anchors. Repository-specific
detail belongs here below the region or in the implementation references at
the top. The actor timing budgets in the limits inventory are qualified by
`witness_contract/actor_timing_qualification`, which measures finite one-,
three- and eight-actor workloads on the signed candidate and requires at least
a quarter of each allowance to remain; its retained report names the equipment
the measurement describes. A deliberately slow or hung specimen is covered by
the deadline controls, not by that margin.

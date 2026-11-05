# Sandbox extensions in PolicyWitness

<!-- BEGIN SHARED EXTENSION COVERAGE -->

File sandbox extensions carry read or read-write authority for a path from an
issuing process to a consuming process. PolicyWitness records their lifecycle
alongside probes of file access.

PolicyWitness accepts two routes for sandbox extension experiments.

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

Issuance uses flags zero. The declaration form resolves its target with
`realpath` before issuance and records both paths; the actor form passes the
submitted absolute path unchanged.

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
released at most once.

## `exec` limitation

An actor that issues, transfers, receives, consumes or releases cannot also
run an `exec` attempt; another actor in the same specimen can. The capacities
are in the [limits](PolicyWitness.md#limits).

## How authority moves

Each actor has its own evidence region and its own authority region; neither
is visible to another actor or to a validator. Each admitted issue has its own
outbound slot, and each transfer has its own request and answer cell. An issued
token is published once; its bytes remain immutable until the host copies or
rejects them and erases that slot. A timeout cannot reuse the slot or consume
another action's answer. A transfer is a request the
host answers: it copies the custody bytes into the recipient's assigned inbound
slot, waits for the recipient to validate framing and its preassigned source,
action and delivery references and acknowledge them, compares the
two copies, settles the delivery as usable or withdrawn, and reports the outcome
to the sender. Consumption requires the host's usable settlement, so a
self-transfer cannot consume or erase bytes while the host compares them.

The recipient accepts a delivery while parked between its visits; it consumes
only in a later visit of its own, after that phase's queries were collected and
the host released it. The host erases private custody at the token's last
declared transfer and at teardown. The worker erases settled inbound slots at
last use and ordinary exit; the host clears remaining shared slots after
confirmed process exit. If worker termination remains unresolved, the host
records that uncertainty and avoids erasing shared bytes that may still be in
use. Tokens never enter the request, the reply, logs or diagnostics.

Every actor's worker is launched with an empty environment, a policy pipe on
stdin, and stdout and stderr opened on the null device. Its other inherited
endpoints are its evidence region, readiness pipe and, when needed, authority
region. Other host descriptors are closed at exec. The host disables core dumps before any token
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
| Resource status `not_reached` | Terminal lifecycle evidence establishes that the producing action was not reached. | Absence of a result alone is insufficient; interrupted or unknown producers remain `unresolved`. |
| `status: unresolved` | The action's result was never published: the actor died, was stopped or never reached it. | That the call did not happen. |
| A fresh read that succeeds after a consume | That process could open and read the file at that moment. | That the consumed extension caused it; compare with the actor's baseline read and its policy. |

Native results, host custody facts, recipient acknowledgements and the
validator's predictions are separate records with separate writers. A source
acknowledgement requires the source action's published matching answer; a
pending request alone does not establish that the source observed an answer. The
`sandbox_check` query cannot represent an extension class beside a path, so
`file-issue-extension` queries cannot express that full issuance predicate and
extension events stay outside the query/attempt comparison.

## What can go wrong, and how it reads

| Situation | Reading |
| --- | --- |
| Required authority-region or custody setup fails | The host refuses launch, or stops the affected worker before releasing a phase; the run records an apparatus failure. This is distinct from missing native symbols or a native refusal. |
| An actor's policy does not compile or apply | That actor's `setup_status` is `setup_failed`; its visits are `actor_unavailable`; other actors' evidence stands. The run is `runner_failed`. |
| An application is published during cleanup after setup expires | Setup stays `setup_timeout` and its visits remain unavailable; `applied` and `application_count` retain the later observed application. |
| An actor dies during a visit | The visit records how it ended; the scheduler establishes the actor is reaped before activating anyone else; later visits of that actor are unavailable. |
| The shared lifetime cutoff expires | A worker that reaches a checked wait publishes a timing failure and exits. A blocked native call may prevent that check; host cleanup and missing publication remain separate observations. |
| The issuing actor publishes a token the host rejects | `resources.tokens[].status` is `issued_uncustodied` and `transfers[]` of that token read `custody_unavailable`. |
| A recipient rejects or does not acknowledge a delivery | The transfer reads `recipient_rejected`, `recipient_timeout` or `recipient_unavailable`; the recipient's later consume is `unavailable` for want of a delivery. |
| Native symbols are missing in the worker | The affected operations are `unavailable` with `native_api_unavailable`; unrelated reads still run. |

<!-- END SHARED EXTENSION COVERAGE -->

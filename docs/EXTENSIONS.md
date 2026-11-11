# Sandbox extensions in PolicyWitness

<!-- BEGIN SHARED EXTENSION COVERAGE -->

File sandbox extensions carry read or read-write authority for a path from an
issuing process to a consuming process. PolicyWitness records their lifecycle
alongside probes of file access.

Extension specimens use actors: one fresh worker per named process, with explicit `issue`, `transfer`, `consume` and `release` actions. Start with an unapplied, unentitled issuer and an applied, selected subject. Add a third actor when testing whether a subject that consumed a token can issue a new one and transfer it onward. Every actor owns at least one phase; issuance takes place inside that actor after its own setup.

Each actor chooses `equipment: "selected"` (the default) or `"unentitled"`, independently of `sandbox.mode`. Both are signed copies of the same compiled worker. The selected copy carries the runner's supplied entitlements; the unentitled copy has an empty entitlement dictionary. Neither name establishes effective authority: an unapplied actor can inherit restrictions, and signing entitlements are associated code metadata. Optional actor `required_entitlements` require boolean `true` in that actor's selected equipment and live signing readback. The controller's `runner.required_entitlements` remains a separate preflight on the selected runner worker.

The service validates its own seal, its sealed `Contents/Resources/worker-equipment.json`, and both production worker artifacts before launching any actor. The inventory binds roles to relative paths, signed hashes, CDHashes, identifiers, teams, entitlements and the compiled worker ABI/build identity. There is no fallback between roles. After usable setup and before any activation or query collection, the host inspects the owned live process and matches its associated code to the binding. An inspection failure cancels scheduled activations while preserving any application already observed. Setup-failed or unlaunched actors remain unavailable without turning their missing inspection into a failure of healthy actors.

Actor setup automatically records bounded apparatus observations before policy
compilation/application or the unapplied declaration: core-limit handling, authority mapping and framing, descriptor closure and each extension-symbol lookup. Missing extension symbols make the corresponding actions unavailable; required apparatus failure prevents application. Setup publication, application observation and final process disposition remain separate. Missing terminal publication leaves application uncertain rather than proving it did not happen.

A phase may specify `after_termination: {"actor_id": "issuer"}` when that actor's last scheduled visit precedes the phase. The gate requires an owned natural reap after the source's final activation, including a nonzero exit or signal, before dependent activation and query collection. It does not require final phase completion. It does not kill an actor to satisfy the dependency. A failed evaluated gate cancels the remaining schedule, including later unrelated
actors' visits, while final collection and cleanup continue. A gate that was
never evaluated because its dependent actor was unavailable retains that distinct
status; it does not itself impose that cancellation. Earlier published facts
retain their own meanings. The reply retains `actors[].owned_reap` and phase `activation_observation`; the gate references the source reap by `capture_ordinal`. Missing clock timestamps retain facts without establishing gate order.

## Request forms

| Form | Available operations |
| --- | --- |
| Actor specimen | Ordinary probes and explicit issue, transfer, consume and release actions. Equipment and policy application are selected per actor. |
| Ordinary single-worker specimen | Ordinary probes and phases without extension actions. |

## Supported families and native calls

| Family | `authority` | Native class | Issue | Consume | Release |
| --- | --- | --- | --- | --- | --- |
| `file` | `read` | `com.apple.app-sandbox.read` | `sandbox_extension_issue_file(class, path, 0)` | `sandbox_extension_consume(token)` | `sandbox_extension_release(handle)` |
| `file` | `read_write` | `com.apple.app-sandbox.read-write` | the same call with the read-write class | the same | the same |

Issuance uses flags zero and passes the submitted absolute path unchanged.

## Operations and references

| Operation | Who | Operands | Produces |
| --- | --- | --- | --- |
| `issue` | an actor | `family`, `authority`, absolute `target`, new `token_ref` | a token the host takes into custody when the native call returns one |
| `transfer` | the actor that issued the token | `token_ref`, `recipient` actor, new `delivery_ref` | a delivery the recipient accepts while parked or during its own wait |
| `consume` | the recipient of a delivery | `delivery_ref`, new `handle_ref` | a candidate handle when the native call returns one |
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

Each actor has its own evidence region. A plan containing token or delivery
resources also receives a host custody session and one authority region per
actor. Those regions are private to their owning host/worker endpoints. Each admitted issue has its own
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
region. Other host descriptors are closed at exec. When creating a custody session, the host disables core dumps before creating
its actor regions. Every actor worker resolves extension symbols and attempts
its core-limit setup. A required authority region is mapped before policy setup;
a plan with no authority resources records mapping as `not_required`. Applied
actors then enter policy setup, and unapplied actors publish their declaration.

## What each observation establishes

| Observation | Supported reading | Read separately |
| --- | --- | --- |
| `extension_events[]` with operation `issue`, `status: returned`, `native_nonnull: true` | That actor's process made the native issue call for the recorded class and path and received a nonnull result of the recorded length. | Host custody, recipient delivery, consumption and fresh access observations. |
| `issue` with `native_nonnull: false` | The native call returned NULL; `errno` is the value saved immediately after it. | Evidence distinguishing the cause of the native refusal. |
| `resources.tokens[].status: issued` | The host accepted the published bytes into custody. | The delivery and consume records. |
| `transfers[].status: delivered` with `equality: equal` | The recipient acknowledged a framed delivery whose bytes equalled the host's custody copy. | The consume result and later fresh access observations. |
| `transfers[]` with any other status | Where the exchange stopped: custody absent, recipient refusal, timeout, mismatch. No native result belongs to a transfer. | Native issue/consume/release calls belong to their separate event records. |
| `consume` with `status: returned` and `native_result` other than the failure sentinel | That actor received a candidate handle for the delivery it named. | Fresh attempts in that process after the consume. |
| `release` with `status: returned` | The native release call returned the recorded value. | Later fresh attempts and independently observed earlier effects. |
| `status: unavailable` with an `unavailable_reason` | The named operation was not called for the recorded reason (no delivery, no handle, missing native symbol, no authority channel, repeated action). | The exact no-call reason. |
| Resource status `not_reached` | Terminal lifecycle evidence establishes that the producing action was not reached. | Interrupted or unknown producers remain `unresolved`. |
| `status: unresolved` | The action's result was never published: the actor died, was stopped or never reached it. | Published progress and final lifecycle evidence about whether the boundary was reached. |
| A fresh read that succeeds after a consume | That process could open and read the file at that moment. | That actor's baseline read, policy and other authority when investigating the cause. |

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
| Required authority-region or custody setup fails | Host preparation refuses launch, or automatic worker setup records a terminal apparatus failure before policy setup or the unapplied declaration. Missing native symbols instead make the corresponding actions unavailable. |
| An actor's policy does not compile or apply | That actor's `setup_status` is `setup_failed`; its visits are `actor_unavailable`; other actors' evidence stands. The run is `runner_failed`. |
| An application is published during cleanup after setup expires | Setup stays `setup_timeout` and its visits remain unavailable; `applied` and `application_count` retain the later observed application. |
| An actor dies during a visit | The visit records how it ended; the scheduler establishes the actor is reaped before activating anyone else; later visits of that actor are unavailable. |
| The shared lifetime cutoff expires | A worker that reaches a checked wait publishes a timing failure and exits. A blocked native call may prevent that check; host cleanup and missing publication remain separate observations. |
| The issuing actor publishes a token the host rejects | `resources.tokens[].status` is `issued_uncustodied` and `transfers[]` of that token read `custody_unavailable`. |
| A recipient rejects or does not acknowledge a delivery | The transfer reads `recipient_rejected`, `recipient_timeout` or `recipient_unavailable`; the recipient's later consume is `unavailable` for want of a delivery. |
| Native symbols are missing in the worker | The affected operations are `unavailable` with `native_api_unavailable`; unrelated reads still run. |

<!-- END SHARED EXTENSION COVERAGE -->

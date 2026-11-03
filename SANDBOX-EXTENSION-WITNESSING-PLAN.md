# Integrated sandbox-extension witnessing

Status: implementation plan; no implementation or native execution performed
in preparing it. Follow [the planning guidance](CONTRIBUTING.md#planning-a-change)
and the [test discipline](tests/AGENTS.md) when executing this plan.

## Result and stopping boundary

Make extension issuance, transfer, consumption and release ordinary specimen
operations. A specimen can name independently restricted actors, retain their
policies for their entire lifetimes, and order operations across them. The
principal acceptance specimen is three-actor re-delegation: an initial issuer A
supplies authority to B; B consumes it and explicitly attempts file issuance
under an extension-dependent issuance rule; C receives the second
token, attempts consumption and performs a fresh access. B applies its policy
once. C is a different process. No caller intervention between phases is needed.

The deliverable is an integrated production capability through `policy-witness
run`, including admission, supervision, evidence, independent readers, tests and
documentation. A faithfully witnessed native refusal is a valid result. A
missing operation or missing publication is not a substitute for that result.
Neither issuance nor consumption alone establishes access.

Implement the existing file read and read-write authority types and flags zero.
Provide a concrete place to add another native family, without implementing Mach,
IOKit, process-bound tokens, arbitrary classes/flags or arbitrary native signatures.
No library interception, function hooking, replacement in production, implicit
warm-up issuance, retry issuance or calls
made solely to observe another call. PW witnesses operations it instructs its own
actors to perform; it does not observe private issuance inside arbitrary libraries.

Existing retained evidence stays unchanged; production must not import or execute
anything under `reports/`. Completion requires accurate witnessing of the
specified operations, including native refusal. It does not depend on a general
macOS security property or usable re-delegation on every host.

## Grounding and consequential choices

The current implementation is deliberately narrower than the required specimen:

| Boundary | Current owner and constraint | Decision |
| --- | --- | --- |
| Specimen parsing | [PWRunnerRequest.swift](runner/Sources/PWRunnerCore/PWRunnerRequest.swift), [request grammar](docs/REQUEST-GRAMMAR.md): one policy and one worker's phases | Add an exclusive actor form with policies per actor and a single ordered schedule. Keep existing forms. |
| Extension admission | `extensionMeaningFailure` in [ProbeRunner.swift](runner/Sources/PWRunnerCore/ProbeRunner.swift), [PWRunnerExtension.swift](runner/Sources/PWRunnerCore/PWRunnerExtension.swift): one declaration, consume and release | Use typed producer/delivery/handle references and aggregate capacities for the actor form. Keep legacy meanings and bounds. |
| Issuance | [ExtensionIssuer.swift](runner/Sources/PWRunnerCore/ExtensionIssuer.swift), [pw_extension_issuer.c](controller/tools/pw_probe_runner/pw_extension_issuer.c): ordinary-authority helper, before worker creation, clean reap required for delivery | Give the existing C worker explicit issuance capability. Retain the old helper protocol only for old declarations. |
| Lifecycle | [pw_probe_runner.c](controller/tools/pw_probe_runner/pw_probe_runner.c): `prepare_extension`, `attempt_extension`, one static handle | Replace actor execution's singleton with bounded tables and operation slots. Native handles stay local to the actor that consumed. |
| Transport | [pw_extension_channel.h](controller/tools/pw_probe_runner/pw_extension_channel.h): one combined input/result/token mapping | Separate authority custody, recipient delivery and token-free evidence, with immutable identities and independent publications. |
| Supervision/order | [CWorker.swift](runner/Sources/PWRunnerCore/CWorker.swift), [CWorkerOrchestrator.swift](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift): synchronous single-child run, per-phase query/release barrier | Extract an owned child session that the host can service incrementally; schedule several such sessions without concurrent specimen actions. |
| Evidence | [worker account](docs/WORKER.md), [contract](docs/CONTRACT.md), [failure propagation](tests/FAILURE-PROPAGATION-CONTRACT.md) | Retain publication and lifetime distinctions; make associations actor-specific and preserve partial results across actors. |

### Native interface and empirical basis

The existing C issuer calls `sandbox_extension_issue_file` through the signature
`char *(const char *extension_class, const char *path, uint32_t flags)`, maps
`read` to `com.apple.app-sandbox.read` and `read_write` to
`com.apple.app-sandbox.read-write`, and passes flags zero. The existing C worker
resolves `sandbox_extension_consume` as
`int64_t (const char *)` and `sandbox_extension_release` as `int (int64_t)`.
These implementation sources, linked above, own the immediate native interface.

Retained native evidence covers 24 trials: eight arrangements repeated in three
blocks on one apparatus revision, r1, on macOS 26.7.1 arm64. The
[equipment record](reports/sandboxed-extension-issuance/evidence/equipment/r1/equipment.json)
pins the executed source/build and environment; the
[trial accounting](reports/sandboxed-extension-issuance/evidence/state.json)
identifies the complete set. The relevant bounded findings are summarized below;
pairs are raw native `(return, errno)` observations.

| Arrangement and recorded observation | Consequence for this plan |
| --- | --- |
| An already sandboxed issuer had a matching class-and-literal-path issuance allowance. Issuance was nonnull, transfer was accepted with transient byte equality, consume returned `(1,0)`, and a separately sandboxed recipient read 37 matching bytes after its initial fresh open had failed. [Native record](reports/sandboxed-extension-issuance/evidence/trials/b1-p4-C2-r1/trial.json). | Explicit post-apply issuance can be useful under the tested restrictions; it belongs in the worker's native operation vocabulary. |
| Removing the issuance allowance, changing its class, or changing its literal path produced NULL with errno 1; dependent transfer/consume were unavailable, and a later fresh open still ran and failed. [No allowance](reports/sandboxed-extension-issuance/evidence/trials/b1-p6-C3-r1/trial.json), [different class](reports/sandboxed-extension-issuance/evidence/trials/b1-p3-C4-r1/trial.json), [different path](reports/sandboxed-extension-issuance/evidence/trials/b1-p8-C5-r1/trial.json). | Admission, native refusal, dependent unavailability and subsequent access are separate observations. Errno alone does not establish sandbox cause. |
| With successful issuance and accepted transfer, omitting consumption left the later fresh open failing. [Native record](reports/sandboxed-extension-issuance/evidence/trials/b1-p5-C6-r1/trial.json). | Delivery must not be reported as consumption or usable access. |
| With successful issuance, accepted transfer and consume `(1,0)`, omitting the recipient's extension predicate left the later fresh open failing. [Native record](reports/sandboxed-extension-issuance/evidence/trials/b1-p7-C7-r1/trial.json). | A candidate handle does not establish access; resource operations need independent evidence. |

The linked examples are from the first block; each arrangement's pattern repeated
in the other two. These findings are bounded by the recorded policies, operations
and environment. The issuer retained ordinary read access and did not first
consume authority supplied by another issuer. Consequently, these observations
do **not** establish effective three-actor re-delegation or issuance enabled by a
previously consumed extension. Those are outcomes the new specimen must witness.
In particular, these records do not establish that `extension` is an accepted
filter on `file-issue-extension`: that combination was not compiled or applied
in the retained trials. Successful compilation of a literal-path allowance
does not establish successful compilation of the proposed allowance below.

For the matching and changed-allowance arrangements above, both `NONE` and `PATH`
queries for `file-issue-extension` returned `(1,0)`, despite different native
issuance results. The query results did not distinguish those outcomes. For these
query forms, the
[validator implementation](controller/tools/sb_api_validator/sb_api_validator.c)
passes PID, operation, type and either no filter value or one path; it does not
pass an extension class alongside the path. The
[pinned validator source](reports/sandboxed-extension-issuance/pw-context/controller/tools/sb_api_validator/sb_api_validator.c)
preserves the implementation examined with the retained evidence. This is a
representation limit, not a class-specific issuance prediction or a claim of
prediction/enforcement agreement. Extension events therefore remain outside the
ordinary query/attempt comparison channel.

These records support the selected native interface and separation of
observations; they do not verify the proposed actor implementation. Its own
integrated tests must establish the requested policy, process, native-call,
authority-transfer and access connections. Fixed publication slots, transient
byte-equality checks and descriptor observations supply useful equipment methods.

### Actor topology and schedule

Use the existing C worker rather than a second sandboxed issuer implementation:
consumption, issuance and access must occur in B's same process and policy. A
special issuer child would answer a different question. Keep Swift outside all
native sandbox operations. Use fresh sibling workers supervised by the existing
fresh XPC host rather than having B create C: actor creation and reporting must
not depend on B's policy permitting spawn or IPC setup.

Choose a serial schedule of actor phases instead of a general dependency DAG or
concurrent actor language. Re-delegation needs durable independent actors and
explicit cross-process dependencies, not concurrent attempts. A serial schedule makes
admission, capacity accounting and established ordering reviewable. Actors remain
alive between visits. This is a restriction on scheduling, not on the number of
issuances, transfers or handles within the stated capacities.

## Specimen language

Add a non-null `actors` form under the current request schema. It is mutually
exclusive with top-level `policy`, `probe_plan` and legacy `extensions`, and
requires nonempty `phases`. Each phase in this form names exactly one `actor_id`.
The old form still requires its existing policy and exactly one existing plan
form. Optional null retains its existing absent meaning; reject mixed forms.

An actor has a unique `actor_id` and one `sandbox` variant:

- `{"mode":"apply","policy":{...}}` uses the existing policy object, including
  parameters, controller-resolved augments and optional compiled-profile capture.
- `{"mode":"unapplied"}` deliberately makes no PW policy application. It does
  not mean unrestricted: inherited restrictions, credentials and code-signing
  entitlements still matter and are recorded. Policy fields are inapplicable.

All actors use the selected runner's bundle-local worker, with the selected
worker's signing/entitlement context. Selection remains specimen-wide; actor
binary selection, credential switching and different entitlement sets per actor
are outside this change. In particular, a BYOXPC unapplied actor is not silently
replaced with the legacy ordinary-authority issuer. Bundled unapplied A supplies
the ordinary initial issuer in the principal acceptance case.

Keep ordinary query/attempt pairs unchanged. Add these closed `extension` action
variants alongside them; `step_id` remains required and globally unique:

| Operation | Required operands | Meaning |
| --- | --- | --- |
| `issue` | `family: "file"`, `target`, `authority: "read"` or `"read_write"`, `token_ref` | This phase's actor calls the file issuer once. `token_ref` names its possible output, not token bytes. Flags are fixed at zero, recorded in evidence; no request flags or raw class field yet. |
| `transfer` | `token_ref`, `recipient`, `delivery_ref` | Request transport of that actor's previously issued token to the named actor; publish a distinct recipient acceptance. It is an apparatus action, not a native sandbox call. |
| `consume` | `delivery_ref`, `handle_ref` | This phase's actor attempts consumption of its accepted delivery. |
| `release` | `handle_ref` | This phase's actor attempts release of the handle from an earlier consume. |

The actor-form operations above do not use the legacy consume spelling
`token_ref`; accepting both would obscure producer versus delivery identity.
There is no automatic transfer, consume, release, resource attempt or retry.
Transfers to the same actor are allowed and use the same validation path.
Extension actions carry no `sandbox_check` and produce no comparison records.
An ordinary query is still allowed to ask a supported operation/filter question,
but its result must not be promoted to an extension-call prediction.

For file issuance, pass the submitted absolute path bytes to the native call.
Do not host-`realpath` or open the target on the actor's behalf, or gate admission
on target existence. This makes the requested call independent of host access
and permits a native failure for a nonexistent target. Evidence records the
exact native path, mapped class and flags. Path replacement and symlink effects
remain limits of individual observations. Preserve legacy target canonicalization
and preparation separately. File access actions keep their present definitions:
`read_fresh` opens anew, observes descriptor identity, performs a bounded read and
closes; `open_read` remains an open-only operation.

### Reference and lifecycle rules

Admission builds typed, single-assignment reference tables from the whole plan
before any process is launched. All actor, phase and step identifiers are unique
in their respective namespaces; token, delivery and handle references are unique
across the resource namespace. Every use must follow its syntactic producer in
global phase/action order. Reject unknown, forward, duplicate, wrong-kind and
wrong-owner references with bounded field paths. Runtime failure of a producer
does not make the admitted request malformed.

A token belongs to its issuing actor. A transfer refers to that token and creates
a delivery owned by its recipient. A recipient cannot transfer somebody else's
token by guessing its reference; it can explicitly issue its own token, as B does
in the principal specimen. Multiple transfers of a produced token are allowed,
each with a fresh delivery reference. A delivery can be consumed more than once
with distinct handle references; every call has its own result. Release is admitted at most
once per handle reference and only in its consuming actor. Do not accept raw
integer handles. A failed consume leaves its later release unavailable.

Treat native consume `-1` as no candidate handle; preserve every other `int64_t`
value, including zero. Equal native values from different consume calls remain
different logical references with the raw equality visible. Do not infer unique
kernel objects, reference counts, independent authority or general revocation.
After a release attempt, record the result and `release_attempted`; do not claim
all authority disappeared. Releasing one reference does not mutate other logical
references even when their raw integers are equal. An omitted release is legal;
process exit and buffer erasure are separate observations, not invented releases.

Compute last token/delivery use statically. Retain raw bytes only for admitted
future uses, then erase. Earlier failed consumption must not erase a delivery
needed by a later explicit consume. There is no slot reuse within a specimen;
this avoids generation reuse being mistaken for a previous token or handle.

### Principal request shape

This proposed complete JSON example illustrates the interface to implement. It
is not admitted by today's build and is not a claim about the kernel's result.
The test harness creates a fresh owned file and substitutes its absolute path
for `/private/tmp/pw-redelegation/A`; no raw authority comes from the request.
B's exact SBPL still needs the compile/apply qualification described under
[readiness](#readiness-and-reconsideration-triggers). The example is not a
record of successful policy compilation.

```json
{
  "schema_version": 5,
  "specimen_id": "extension_redelegation",
  "actors": [
    {"actor_id": "A", "sandbox": {"mode": "unapplied"}},
    {"actor_id": "B", "sandbox": {"mode": "apply", "policy": {
      "format": "sbpl",
      "sbpl_source": "(version 1) (allow default) (deny file-read-data) (deny file-write*) (deny file-issue-extension) (allow file-read-data (extension \"com.apple.app-sandbox.read\")) (allow file-issue-extension (require-all (extension-class \"com.apple.app-sandbox.read\") (extension \"com.apple.app-sandbox.read\")))"
    }}},
    {"actor_id": "C", "sandbox": {"mode": "apply", "policy": {
      "format": "sbpl",
      "sbpl_source": "(version 1) (allow default) (deny file-read-data) (deny file-write*) (allow file-read-data (extension \"com.apple.app-sandbox.read\"))"
    }}}
  ],
  "phases": [
    {"phase_id": "b_before", "actor_id": "B", "actions": [
      {"step_id": "b_read_before", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/private/tmp/pw-redelegation/A"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "/private/tmp/pw-redelegation/A"}}
    ]},
    {"phase_id": "c_before", "actor_id": "C", "actions": [
      {"step_id": "c_read_before", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/private/tmp/pw-redelegation/A"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "/private/tmp/pw-redelegation/A"}}
    ]},
    {"phase_id": "initial_supply", "actor_id": "A", "actions": [
      {"step_id": "a_issue", "extension": {"operation": "issue", "family": "file", "authority": "read", "target": "/private/tmp/pw-redelegation/A", "token_ref": "ta"}},
      {"step_id": "a_to_b", "extension": {"operation": "transfer", "token_ref": "ta", "recipient": "B", "delivery_ref": "db"}}
    ]},
    {"phase_id": "b_consume", "actor_id": "B", "actions": [
      {"step_id": "b_consume_first", "extension": {"operation": "consume", "delivery_ref": "db", "handle_ref": "hb"}}
    ]},
    {"phase_id": "b_redelegate", "actor_id": "B", "actions": [
      {"step_id": "b_read_after", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/private/tmp/pw-redelegation/A"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "/private/tmp/pw-redelegation/A"}},
      {"step_id": "b_issue", "extension": {"operation": "issue", "family": "file", "authority": "read", "target": "/private/tmp/pw-redelegation/A", "token_ref": "tb"}},
      {"step_id": "b_to_c", "extension": {"operation": "transfer", "token_ref": "tb", "recipient": "C", "delivery_ref": "dc"}}
    ]},
    {"phase_id": "c_consume", "actor_id": "C", "actions": [
      {"step_id": "c_consume_second", "extension": {"operation": "consume", "delivery_ref": "dc", "handle_ref": "hc"}}
    ]},
    {"phase_id": "c_effect", "actor_id": "C", "actions": [
      {"step_id": "c_read_after", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/private/tmp/pw-redelegation/A"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "/private/tmp/pw-redelegation/A"}},
      {"step_id": "c_release", "extension": {"operation": "release", "handle_ref": "hc"}}
    ]},
    {"phase_id": "b_cleanup", "actor_id": "B", "actions": [
      {"step_id": "b_release", "extension": {"operation": "release", "handle_ref": "hb"}}
    ]}
  ]
}
```

The separated consume and access phases give access queries their own collection
after consumption. Putting them in the same phase remains legal, but that phase's
queries precede *all* its actions and cannot describe a post-consume state.

## Execution, transport and publication

### Actor sessions and phase scheduling

Extract launch, polling, evidence acquisition and cleanup from the blocking
`runCWorker` path into an owned session primitive. Retain its single-worker
adapter. The actor scheduler owns all sessions and multiplexes their control
and evidence mappings; do not run eight independent blocking orchestrators or
let validator collection stop supervision of other children.

Allocate all bounded evidence and authority storage before application, launch
fresh workers, deliver each actor's own policy, check bootstrap/source identity,
and apply at most once per `apply` actor. Record unapplied mode explicitly, with
no fabricated apply success. Every actor reports its own PID, parent, credentials,
kernel process-start identity when available, executable/build provenance,
policy receipt/hash, compile/apply results and application count. An unavailable
identity observation stays unavailable; PID alone does not justify reacquiring
ownership after it is lost. Retain existing owned-child/reap safeguards.
For the new form, have the worker hash the policy bytes actually received before
compilation and retain that separately from the host's submitted-source hash;
length equality alone cannot establish their identity. Keep import/capture
provenance distinct from source-byte identity.

Only the actor named by the current phase receives an activation command. It
publishes arrival with global phase ordinal and actor-local visit ordinal. The
host plans that phase's ordinary queries freshly against that owned, live actor,
closes collection on every terminal path, and releases the matching ordinal.
The actor acknowledges release, runs actions sequentially, then publishes phase
completion. No other actor runs specimen actions meanwhile. Parked actors may
service delivery/cancellation commands, but must not consume or access resources
as part of servicing those commands.

Recheck process ownership and the current actor's arrival before releasing.
After a previous actor's failure, the scheduler records why its phase ended and
can advance to another actor; it must not fabricate previous phase completion.
A failed active actor must first be known quiescent (never launched, successfully
reaped, or at a validated terminal protocol state that cannot run further actions).
If it could still execute, stop it and establish that fact before advancing;
unresolved termination cancels the remaining schedule. Do not trade the serial
execution contract for an optimistic timeout-based advance.
A missing phase completion cannot establish successful cross-phase order, even
when the host subsequently activates a different actor. Keep raw later results
and mark the missing edge. Query eligibility remains local to the queried actor
and phase and still needs the full collection/release/acknowledgement chain.
Timestamp order alone, a shared PID value, or another actor's acknowledgement
cannot supply it. Rerun and extend the order-barrier mutation controls.
For an unapplied actor, the explicit declared-mode/setup publication replaces
the apply prerequisite; it does not supply an apply result. An apply actor's
failed or missing application cannot take that route to eligibility.

### Actor wait primitive

Use bounded atomic polling, following the existing worker's `wait_for_proceed`
and `cpu_relax`, for activation, delivery, custody acknowledgement and phase
release waits. A parked actor is inactive in the specimen schedule, not suspended
by the OS. The host release-publishes a command; the actor discovers it on an
acquire load when scheduled. There is no separate wake notification or inherited
wait descriptor.

Each polling iteration validates the continuous clock and applicable absolute
deadline, checks cancellation, then inspects the bounded control/mailbox state.
Preserve expiry-before-acceptance and sticky clock-fault handling. Validate the
expected command identity/ordinal before servicing it, publish acknowledgement
with release semantics, and return to the loop. A delivery serviced while parked
does not activate specimen actions. Bound the amount of mailbox work between
clock/cancellation checks; servicing one command cannot reset the wait deadline.

Between empty polls, use the worker's existing bounded CPU-relax batch (currently
1,000 ARM64 `yield` instructions). This is an instruction hint, not `sched_yield`
or a timed sleep. Measure elapsed time through the existing validated
[`mach_continuous_time` clock machinery](controller/tools/pw_probe_runner/pw_worker_timing.h),
not by counting iterations or assuming a batch's duration. Keep its platform and
sample-validation premises; the clock implementation is not promised to avoid
kernel entry on every system. Do not add `nanosleep`, pipe reads, semaphore waits
or an unbounded hardware wait as an implicit alternative. The unsandboxed host
can continue using its own wait facilities.

This choice avoids adding a post-apply blocking API or authority-bearing wait
resource, at the cost of CPU consumption by parked actors. Record that apparatus
cost in the worker account. Extend the existing deny-default wait and order
controls to delivery, self-transfer, cancellation and expiry, and exercise the
maximum actor count to expose starvation or missed deadlines. Batch tuning is
an implementation detail subject to these checks; replacing polling with a
blocking primitive changes the apparatus and needs an explicit resource,
policy-dependency and failure-evidence account. Do not claim a scheduling or
real-time guarantee from polling.

### Bounded transient authority channels

Use preallocated shared-memory mailboxes plus token-free control/evidence slots;
ordinary pipes or sockets opened after application would add a policy dependency.
Separate each actor's evidence mapping from authority mappings. Each actor gets
only its outbound issuance storage and its designated deliveries, never another
actor's evidence or the host's complete token store. Host custody uses bounded
non-serializable native buffers, not Swift `String`, `Data` diagnostics or JSON.

All authority publications carry checked specimen/session identity, actor index,
operation index, resource index, family tag, bounded length and a release-published
commit word. Check magic, layout identity, size, owner, ordinal, terminator,
nonempty payload and absence of interior NUL before accepting a file token.
The source token, delivery and evidence publication are different objects.

1. `issue` publishes a pre-call boundary, invokes the native function once, saves
   raw nonnull/NULL and errno immediately, and publishes a complete result slot.
   A usable bounded token also gets an outbound publication tied to that result.
   Host validation/copy into custody and its acknowledgement are separate facts.
   Result publication without accepted bytes is still an observed native result.
2. The worker waits for custody acceptance/refusal before reusing its outbound
   scratch, then erases that scratch. The host's accepted token remains immutable
   until its final declared transfer or cleanup. A result publication is required
   to report a native return; a pre-call marker cannot supply it.
3. At an explicit `transfer` action the source actor publishes a transport request
   and waits. The host verifies token ownership and custody, copies to the
   recipient's assigned slot, and asks the recipient to validate and acknowledge
   acceptance. A transient byte equality comparison joins the source copy and
   delivered view before consumption can be released. Retain only the comparison
   result, length and references, never a token or token-derived fingerprint.
4. The host publishes the transfer disposition and acknowledges the source's
   action. Recipient acceptance is not native consumption. A self-transfer uses
   the same servicing loop while the active actor waits. The recipient later
   consumes only the slot named by its `delivery_ref`, after its phase release.
5. Consumption publishes its own call boundary and result. Store the raw handle
   in the actor's local handle table only on a published candidate-producing
   result; its evidence references the exact delivery and consume action. Release
   loads the handle from that table and publishes its own result. Neither native
   call supplies a resource-access observation.

The service loop must handle delivery while waiting for activation or host
acknowledgement, avoiding a sender/recipient wait cycle. Each exchange has a
bounded, non-resetting deadline. A timeout is a transport observation, not an
invented native errno. Test loss after copy, after acceptance, and before sender
ack separately. A published transfer request can finish after source death if
custody was already accepted and ownership/recipient checks still hold. Source
death before that request means the transfer action was not reached; custody
alone does not authorize automatic delivery. Never recover bytes from an
uncommitted or mismatched slot.

### Process resources, termination and cleanup

For the actor launcher, check file-action/attribute initialization, duplication,
descriptor relocation, CLOEXEC settings, mapping/unlinking and every prerequisite
before spawn. Use close-on-exec by default with explicit inherited descriptors;
map channels and close their descriptors before policy application. Give actors
explicit empty environments and defined standard streams, recording that launch
context. Do not inherit target file descriptors from the host. Pre-apply setup
resolves required native symbols without calling them and disables core dumps
before any authority is received. No pre-apply target opens or warm-up consume.
Disable core dumps in the custody-owning host before receiving tokens as well.
Resolve capability per requested native operation: an unavailable release symbol
does not suppress a supported issue or unrelated read. Publish the unavailable
operation explicitly; failure of required local authority-channel setup remains
an apparatus failure rather than a native API result.

Record a bounded descriptor inventory at entry and before application, including
inspection completeness and descriptor identities. It supports the launch account;
an incomplete inventory cannot prove absence. Fresh access records its own open,
fstat/read/write/close observations. Tests separately establish that the target
was not inherited and use an intentionally inherited-target control to reject
false attribution. PW does not automatically label a successful read as caused
by a particular token.

Keep the current extension/exec exclusion in legacy requests. For the new form,
make it per actor: an actor that issues, sends, receives, consumes or releases
extensions cannot also `exec/spawn` in this first delivery. Other actors can use
existing exec operations and descendant supervision. This bounds raw-authority
exposure and inherited-authority interpretation without banning unrelated work
specimen-wide. Supporting extension-participating exec actors would need explicit
inheritance/descendant semantics; it is not needed for three-actor re-delegation.

Keep actors alive through the scheduled work, then request termination and
independently observe exit/reap. On any failure preserve every complete immutable
publication already acquired. A dead actor's not-reached actions are distinct
from a live actor's published dependent-unavailability decision. Continue later
independent actors where ownership and apparatus integrity remain established;
C's fresh access still runs after issuance or consume refusal. If the authority
binding is invalid, withhold dependent consumption, retain the diagnostic, and
allow independent resource actions. A shared integrity or ownership failure
cancels affected execution instead of guessing associations.

Erasure is not revocation. Erase native issuance allocations only to the extent
their inspected bounds permit, free them using the established interface, and
make no claim about the library's private copies or allocation size. Erase full
owned token/delivery buffers at last use and on ordinary exits; host cleanup is
independent of worker cleanup. Final host erasure/read-back must occur after
writers are stopped or their write access is gone. Fatal termination may prevent
worker erasure. Record erasure, descriptor closure, unmap/unlink, signals, wait
results, exit status and any uncertainty independently. Terminal publication is
not successful reap, and successful reap is not successful resource removal.

Use immediately unlinked owned mappings where possible. If unlink/setup fails,
retain exact owned resource metadata for cleanup and do not launch with an
untracked named authority channel. Report pending cleanup if absence cannot be
established; do not retry cleanup using historical PIDs alone. Host death may
lose the reply: client uncertainty still forbids replay. Workers have their own
bounded parked wait and cancellation path; these are not promises that every
native call or descendant can be preempted. No durable raw-token recovery store.

## Limits and timing

Keep one-way application and fresh processes. Change the unit of worker count
from specimen to actor. Keep 256 total actions/ordinary queries across the entire
specimen, rather than multiplying it by actors or phases. Propose these explicit
actor-form capacities, recorded and verified through [limits.json](docs/limits.json):

| Quantity | Actor-form bound | Legacy disposition |
| --- | --- | --- |
| Actors | 8 per specimen | One worker plus the existing optional helper |
| Phases | 16 total, each assigned one actor | Existing 8 |
| Issue outputs | 32 total | One pre-issued declaration |
| Transfers/deliveries | 64 total | Existing one delivery |
| Consume/handle references | 64 total | Existing one consume |
| Releases | At most one per handle, at most 64 total | Existing one release |
| All actions | 256 total including transfers and native extension actions | Unchanged |
| Reference/actor ID | 63 UTF-8 bytes, nonempty, no NUL | Existing reference rules |
| File issue target | 1,023 UTF-8 bytes, absolute, no NUL | Existing target bound/preparation |
| Raw token | 16,384 bytes including terminator per stored copy | Unchanged bound |
| Policy source | 262,143 bytes per apply actor; aggregate at most 8 times that | Existing per-worker bound |
| Policy parameters/capture | Existing per-actor caps; at most 8 times their bounded storage in aggregate | Existing bounds |

The resource caps overlap with, and do not increase, the total action cap.
They are engineering budgets, not native macOS maxima: they cover the three-actor
re-delegation specimen and multiple independent resources without unbounded
scheduling.
Allocate only admitted resources, with checked aggregate arithmetic and explicit
worst-case allocation accounting including outbound scratch, host custody and
recipient copies. Per-actor tables cannot independently multiply global reference
counts. Query retention remains bounded by actual submitted queries (at most
512 retained validator records overall). Fresh-read payload remains 64 bytes.
Keep other ordinary action/scalar bounds, refusal-path limits and output-loss
semantics. Test exact, over-limit, multibyte and combined maximum cases.

Retain the old single-worker timing profile. Introduce a documented actor timing
profile with these defaults, rather than starting the old 60-second phase wait
in every parked actor at spawn:

- One aggregate setup allowance of 10,000 ms from first actor launch, capping
  each existing 5,000 ms policy-delivery and 1,000 ms readiness allowance by the
  remaining setup budget. No actor action begins before setup dispositions are
  known. Setup failure in one actor need not suppress an independent actor.
- One 120,000 ms host execution/publication allowance for the schedule, excluding
  measured validator collection, not one allowance per actor. Validator planning
  and collection share the existing 30,000 ms aggregate allowance across actors.
- A 60,000 ms release wait starts only after the selected actor's phase arrival.
  Delivery/custody exchanges each have a 5,000 ms cap and also spend the global
  execution budget. Waiting actors must service transport without spending a
  fresh full execution budget each time they are activated.
- A fixed 180,000 ms actor-form lifetime cutoff, measured from before the first
  launch on a validated shared continuous clock basis, bounds parked/control
  waits and caps all of the above. It includes sleep and collection; it cannot be
  extended by acknowledgements or heartbeats. Give each actor the same absolute
  cutoff before application. Invalid clock samples/conversions fail explicitly.
- Keep existing owned-child exit/reap grace and exec-child limits, capped by the
  appropriate remaining active budget. Charge non-extension actors' exec work
  to the shared schedule budget; do not restart an exec allowance per visit.

The outer cutoff is an execution/wait policy, not an end-to-end real-time guarantee
over native blocking calls, scheduler delay, termination or reap. Cleanup remains
observable even after expiry. Keep the 240,000 ms default client RPC allowance
and its independent uncertainty semantics; do not claim it guarantees a reply.
Implement deterministic clock, oversleep, regression, exact-exhaustion and combined
budget controls before relying on live timing checks. Production-duration value
checks and shortened controls must remain separately described.

Recompute the maximal encoded response, base64 client capture, controller output
and memory bounds from actual encoders. Actor profiles, policy dossiers,
descriptors, process records, failures and transfer metadata all need explicit
size policies. Adjust their manifest-owned transport capacities together if the
new bound exceeds existing retention; never silently truncate admitted evidence
or multiply today's whole-reply allowance by eight. This calculation is an
implementation check with a deterministic acceptance gate, not a native unknown.

## Evidence and interpretation

Add an explicit `execution_form` discriminator to the reply. For actor-form
replies provide actor-indexed process/policy/setup/disposition records, phases
with actor identity and both ordinals, ordinary steps with actor identity, native
extension events, resource metadata and transfer records. Do not designate one
actor as the specimen's authoritative `runner_subprocess` or `policy_sha256`:
leave legacy singular worker/policy projections absent or null for this form.
The existing top-level host PID retains its meaning. Legacy replies retain their
singular records and extension declaration account.

Each native event contains actor, phase, step, family, exact applicable arguments,
input/output references, pre-call boundary, immutable result-publication state,
raw return/errno when published, and availability/interruption information. Issue
records nonnull/NULL and inspected length, not a pointer address or token. Consume
and release retain native-width results. Transfer records name source issue,
custody acceptance, destination, delivery, framing/equality observations and
recipient acknowledgement; their host/actor provenance is explicit. No fake
native return or errno is attached to a transfer.

Use a closed evidence state vocabulary separating these cases:

| Observation | Permitted interpretation |
| --- | --- |
| Published native result | That actor reported that result for that call's arguments. Preserve failure-shaped results without cause attribution. |
| Pre-call boundary without result | Call boundary reached; native entry/return unresolved. It is not a completed call. |
| Published dependency/API unavailable decision | The named operation was not called for the recorded reason. |
| Actor never launched, policy not established, or action not reached | Host-owned disposition; no fabricated actor publication or native result. |
| Invalid or conflicting publication/association | Retain the fault and usable independent observations; withhold the affected interpretation. |
| Missing sender acknowledgement after recipient acceptance | Preserve recipient acceptance and the unresolved sender action separately. |

Partial payloads do not become results at process reap or phase completion.
Native NULL is not transport refusal; transport refusal is not native NULL;
consume success is not access; release success is not general revocation. Error
numbers do not identify sandbox cause. Keep comparison eligibility limited to
ordinary query/attempt pairs, with the current submission-scope and ordering
rules. The query representation limit above supplies no exception for extension
issuance.

Resolve each actor's disposition from raw evidence using the existing approach
in [CWorkerDisposition.swift](runner/Sources/PWRunnerCore/CWorkerDisposition.swift).
Publish all actor dispositions and all phase validator failures. For the actor
aggregate, admission failure precedes execution; reporting-integrity failure
uses the degraded-report contract; any worker/setup/ownership/cleanup failure
makes the aggregate runner failure; otherwise retain validator failure precedence
in schedule order; otherwise `ok` means apparatus completion, not authority
granted. Expected native refusals and fully published dependency unavailability
do not alone make an apparatus failure. Do not let a clean A hide an interrupted
B, and do not discard C's valid read because B failed.

Reader rules must validate unique associations and the observed causal chain,
not just plausible values in a list. Join request, applied policy, owned process,
phase release, operation slot, custody, transfer, delivery, handle and access by
their explicit identities. Preserve raw query records when eligibility fails.
Diagnostic/degraded serialization must keep bounded evidence where possible and
withhold comparisons; the minimal fallback must still say evidence was not
retained. Tokens and token-derived values must never enter requests, replies,
stderr, arbitrary diagnostic text, dossier hashes or retained test evidence.

## Common substrate and native family boundary

Use closed tagged request/result variants and small internal dispatch functions,
not a dynamic plugin system or a universal variadic native-call adapter.

| Common responsibility | File-family responsibility |
| --- | --- |
| Actor/phase scheduling, typed reference validation, capacities and ownership | The `file` request fields and their admission rules |
| Transient opaque token custody, bounded delivery, acknowledgement and erasure | Mapping `read`/`read_write` to native classes; exact path bytes; flags zero |
| Operation boundaries, complete publication and independent partial-result recovery | Resolving/calling the known issue-file signature and recording its native result |
| Process supervision, identity and cleanup | Native allocation handling and token framing constraints for this interface |
| Result association and generic missing-evidence states | Consume/release signature, handle representation and sentinel conventions for supported file tokens |
| Resource references and actor-local native state storage | Any family-specific recipient, issuer-lifetime or process-binding requirements |

Use a typed union for native handle storage/results even though the first variant
is `int64_t`. Opaque token transport must not require a filesystem target. Move
path, class and flags out of the common channel header into the file operation
variant. Do not infer a future family's lifetime or recipient constraints from
file behavior; common metadata permits an explicit supported recipient binding,
but only implement the current issue-file signature without a recipient argument
now. Unknown variants are refused, not routed through file defaults.

Adding a concrete family later means adding its closed request/result variant,
native argument and lifecycle implementation, relevant binding/admission rules,
ABI representation, family-specific evidence checks and documentation/tests. It
reuses actor supervision, transport, references, ordering and publication. If it
requires a genuinely different native lifecycle, extend that tagged lifecycle
contract explicitly. Adding a family does not inherently require a separate
experimental program. This plan does not invent an interface for mechanisms
whose requirements are unknown.

## Compatibility and implementation owners

Keep the request schema at 5 because the actor form is additive and old valid
requests retain their meanings. Older builds reject the new fields explicitly;
do not silently lower actor specimens to an old host or retry after submission.
The controller must preserve its one held resolved request and no-replay rules.
Retain old one-declaration preparation, clean helper reap, canonicalization,
delivery, one consume/release and timing behavior through a compatibility adapter.
It may share low-level file-native functions and session machinery; it must not
be silently translated into a new unapplied actor with different signing or
lifetime semantics. This adapter is the only retained pre-issuance special case.

Bump response 24 to 25 and envelope 9 to 10 when implementing the actor contract:
readers need new actor associations and policy dossier rules. Use the next values
instead if another accepted change has already advanced the manifest. Keep XPC
runner protocol 2 if its reservation/opaque request and reply transport is
unchanged, as proposed. No version negotiation or implicit historical evidence
upgrade. Old retained envelopes keep their versions and original readers; current
strict readers must reject unsupported versions before interpretation.
Update controller, client/host readers and installed external runners together.
An older installed host's response remains explicitly unsupported by the new
strict reader, including for an old-form request; preserving request semantics
does not promise cross-version reply interoperability. Document the required
external-runner refresh and test the unsupported-response path without replay.

Implementation boundaries and coupled work:

- **Controller:** [request_patch.rs](controller/src/request_patch.rs),
  [run_flow.rs](controller/src/run_flow.rs), [dossier.rs](controller/src/dossier.rs),
  [policy_check.rs](controller/src/policy_check.rs) and runner selection. Resolve
  augments and hashes per apply actor, retain original/resolved sources and import
  dossiers keyed by actor, preserve one specimen-wide selection, and never apply
  one actor's policy to another. Generalize fallback policy checks to individually
  identified apply policies without representing them as runtime application.
  Unapplied actors have no invented policy hash/capture. Direct XPC still refuses
  controller selection and unresolved augments at their new paths.
- **Runner request and planning:** the request/extension types and admission
  functions linked above; `CWorkerRequestPlanning.swift`; service entry-point
  policy hashing and refusals. Keep structural decoding, capacity and meaning
  checks in their established order, before child creation. Share the same
  normalized plan and reference table across public and direct-XPC admission.
- **Host execution:** factor owned sessions from `CWorker.swift`, add actor
  scheduling and authority custody/transfer modules beside the existing
  orchestrator. Keep native operations out of Swift and preserve the one-host,
  one-reservation, one-specimen service lifecycle.
- **Native worker/ABI:** add file issue dispatch, bounded handle/delivery tables,
  unapplied mode, parked servicing and actor/phase identity to the C worker and
  shared headers. Split the file-native implementation into focused C source if
  useful, registering it in Meson. Preserve bootstrap validation before any
  layout-dependent read, policy input, authority use or evidence publication.
- **Evidence/consumers:** extend PWRunner evidence/reply types, step/comparison
  builders, disposition and bounded fallback encoding; controller contracts,
  `tests/lib/consumer.py`, response-shape validators and the independent blackbox
  consumer. Build one coherent actor association account rather than several
  incompatible projections of missing evidence.
- **Generated contracts/build:** edit [contract.json](docs/contract.json),
  [limits.json](docs/limits.json) and [architecture.json](docs/architecture.json),
  run their owning generators, regenerate worker source identity, review emitted
  shape goldens and compiled C/Swift layout. Update bundle source lists and
  provenance/signing inventories if source composition changes. No ABI ordinal
  substitutes for the current exact source-identity contract.

## Delivery stages and verification gates

These stages lead to one capability. Do not close the work after adding an issue
opcode or a handcrafted fixture. Do not advertise actor support before the public
re-delegation path, readers and failure propagation are integrated.
At implementation entry, perform the narrow principal-policy qualification
specified under [readiness](#readiness-and-reconsideration-triggers), before
committing substantial work to the end-to-end acceptance case.

1. **Contract and bounded execution model.** Implement the tagged actor form,
   normalization, reference/lifecycle rules, per-actor policy dossiers, proposed
   bounds and response/envelope changes together. Add shared CLI/direct-XPC
   request corpus cases and encoder/consumer fixtures. Gate: all existing accepted
   requests still have their prior meanings/refusals; invalid actor forms create
   no children; maximal encoded evidence fits derived transport bounds.
2. **Owned actor sessions and schedule.** Factor the worker driver without changing
   legacy execution, then add per-actor preparation, unapplied mode, parking,
   supervision, timing and phase barriers. Gate: two different policies actually
   reach two identified processes, each applies once; repeated visits preserve
   those identities; failed setup, death and validator loss preserve other actors'
   evidence. No extension success is needed to establish these connections.
3. **Explicit file authority path.** Implement native issue, host custody, explicit
   transfer, recipient acceptance, consume/release tables and erasure. Connect
   them to the ordinary schedule and production evidence readers. Gate: public
   specimens exercise multiple resources/handles and re-delegation end to end;
   native refusal and interruptions remain independently legible. Do not wait
   for a second family to ship this stage.
4. **Integrated acceptance and documentation.** Complete the tests below on the
   signed candidate, review retained evidence/provenance, update coverage and
   operator documentation, and only then change the FAQ. Acceptance covers the
   complete capability and compatibility adapter, not the staged code in isolation.

### Principal public-interface acceptance

Add `witness_contract/extension_redelegation` through the public CLI with ordinary
specimens, registered in [catalog.json](tests/catalog.json). Use normal test-owned
fresh resources and record input, source/build identity, exact command, envelope,
independent file identities/known contents and cleanup. The case must establish:

- A, B and C are distinct fresh processes from the selected equipment, B and C
  received the intended different policy bytes and each applied exactly once.
  B's policy includes the consumed-extension issuance predicate; it has no
  ordinary read-data allowance for the target. Record baseline B and C fresh
  reads and an unrelated control file, keeping target descriptors out of actors.
- A's issuance result, custody, delivery to B, B's consumption, B's fresh read,
  B's second issuance, delivery to C, C's consumption, C's fresh read and both
  requested releases have separate observations or specifically justified
  unavailable/unresolved states. B must attempt the second issue even if its
  earlier consume returned failure: a native issue action has no implicit
  dependency on successful consumption. C's read still runs when its consume
  cannot run or returns failure.
- Bind the second native call to B's already-applied process and the second
  delivery to that call, not to A's token. A nonnull second issue alone is never
  credited as usable re-delegation. Credit observed usable access only when the
  complete chain and fresh matching bytes/identity are present; otherwise report
  the actual bounded refusal/unavailability without inventing success.
- Distinguish apparatus completion from kernel behavior. A real published NULL,
  consume failure or denied fresh read can pass the witnessing assertions.
  A skipped native call, missing publication, invalid association, failed process
  setup or missing required test equipment cannot pass as such a refusal.

B's successful compilation and one-way application of the consumed-extension
issuance policy are prerequisites to crediting this principal case. A compiler
rejection or apply failure remains correctly reported actor/runner failure; it
can establish failure-propagation coverage but does not establish re-delegation
coverage. The acceptable native refusal here is a reached issuance or later
operation under the successfully applied policy, with its own published result.
There is no sanctioned fallback to a bare allowance, a literal-path allowance,
or ordinary read authority for B in the principal case. Those arrangements may
calibrate the mechanism, but they remove the dependency this case must express.
Any reformulation must retain that consumed-extension dependency and have its
exact policy bytes, rationale and compile/apply evidence reviewed as part of
the principal case; it cannot be substituted merely to obtain a passing result.

Pair it with a positive-capability calibration specimen using a simple supported
file allowance and separately with native refusal/dependency-unavailability
cases. Require calibration to exercise real issuance, transfer, consumption and
fresh access on the acceptance host; if it cannot, report that coverage missing
rather than accepting an all-unavailable implementation. If the re-delegation
case refuses issuance, this does not block shipping accurate witnessing: retain
the refusal, and establish its unvisited later plumbing with the calibration and controls.
If a required native symbol is absent, the product must report it correctly, but
that host cannot supply complete native acceptance coverage for the feature.
Missing positive calibration blocks acceptance of this capability, the FAQ's
affirmative answer and retirement of this plan. Retain the result as missing
coverage; implementation and other checks may proceed, but neither constructed
successes nor an all-unavailable native run close this gate. Obtain applicable
candidate-build evidence on a supported acceptance environment that supplies
both principal-policy compile/apply coverage and the positive calibration path.
Other environments can separately establish accurate refusal/unavailability;
the capability need not succeed on every host. Record each environment and its
credited cases using the existing evidence-applicability rules.

Use narrow public-specimen contrasts: omit B's consume, remove B's issuance
allowance, change its class/path restriction where applicable, omit C's consume,
and omit C's extension predicate. These are controls on association and claims;
do not force every host to reproduce a particular native return value. The
checker must preserve actual observations and identify which comparisons were
possible.
These are integrated production tests, with their own retained evidence.

### Misleading-pass and failure controls

Extend existing native boundary equipment and independent checker mutations. Test
fixtures may substitute functions at compile time with separate provenance as
today; production must not. Substitutes establish boundary handling, not native
policy effects. Implement publication, transient equality and descriptor controls
in maintained test equipment; preserve attribution if adapting existing code.

| Fault/control | Required rejection or retained distinction |
| --- | --- |
| Skip B's issue; reuse A's token; substitute another resource/delivery/handle | No credited re-delegation or valid association merely from later access; mismatched identity is diagnosed. |
| Stop before call, after boundary, after return before result publication, after result before custody, after copy before acceptance | Distinct unresolved/publication/transport states; no completion synthesized from exit or bytes alone. |
| Lose transfer ack after recipient acceptance | Accepted recipient observation survives; sender completion remains unresolved. |
| Omit consume; consume wrong delivery; release wrong actor's handle; equal raw handles | Correct producer/owner joins; no inferred consumption or handle identity. |
| Stale/future phase release; wrong actor ack; validator queried wrong PID; copied query result from another visit | Withhold `query_first` and affected associations without discarding independent raw evidence. |
| Open target before apply or inherit its descriptor; replace target between observations | Fresh-open provenance and independent identity checks prevent credit for the wrong descriptor/resource. |
| NULL/oversized/empty/interior-NUL token; missing symbols; corrupt length/family/session/index | Native result survives where valid; no delivery/consume from invalid bytes; bounded diagnostic only. |
| Setup/map/close/unlink failures, simultaneous native failure and cleanup failure | Both primary and cleanup facts survive; no created-process or erasure claims from intentions. |
| Actor death during each stage, host cancellation, timeout, missing reap, client loss | Published prefix retained; later independent actions handled explicitly; no replay or false cleanup completion. |
| Erasure shortened, omitted, or before final declared use; raw token accidentally serialized | Transient independent inspection rejects the control; tokens never enter retained fixtures. |
| Maximum actors/references/phases, overflow, combined limits, malformed/mixed forms | Bounded refusal before launch or valid bounded evidence, never partially admitted plans. |

Mutation checkers need passing controls and single/combined rejected controls,
including a mutation derived from an actual integrated re-delegation or calibration
envelope.
Deleting one event must not make another failure disappear; moving an event must
not invent a native result. An independent reader must validate against the
submitted plan and retained native/process evidence rather than merely trusting
the production aggregate status. No checker parses SBPL to invent enforcement.

### Repository verification work

Use [change verification](tests/CHANGE-VERIFICATION.md) and existing suite owners.
At minimum the candidate needs `unit`, `integration`, `source_drift`,
`runner_abi_layout`, `runner_unit`, `runner_c_worker_harness`, `failure_boundaries`,
the shared `runner_outcome_bad_request` corpus, relevant `runner_validator_failure`
and `validator_bridge` cases, extension/phase witnesses, and
`witness_contract/order_barrier_mutations`. Extend C/Swift compiled layout checks
to every new tagged header, slot and resource table, including offset/width and
overflow checks; update exact source-identity rejection controls. Add maximal
reply and degraded-serialization controls with multi-actor failures.

Run existing legacy extension, directory, combinations and interruption controls
to show their semantics survived. Include the independent `blackbox_e2e` reader
and controls for the new contract, plus the BYOXPC extension/phase witness for
the common selected-worker entitlement context and preserved helper distinction.
Run the normal signed candidate battery before acceptance; record canonical case
IDs and dependency provenance for every credited run. Native counterfactuals are
appropriate for changed signatures, allocation assumptions or lifetimes; use the
existing native suites when their change-verification rule applies. Do not make
an unrelated exploratory matrix a prerequisite.

Use fresh managed test output, preserve failure evidence, and respect the shared
checkout lock. Required equipment absence is unrun coverage, not an invented
skip. Record production duration checks separately from shortened deadline
controls and constructed results separately from native observations.

## Documentation and completion

Create `docs/EXTENSIONS.md` during implementation as the durable coverage and
semantics document: accepted old/new forms, actors, operations/families, exact
native calls and limits, lifecycle/reference rules, transient transport, missing
evidence, process/timing/cleanup limits, example re-delegation and refusal
outcomes, and what each observation establishes. The supported-family table
initially contains file read/read-write only. Add future concrete families there when implemented; do not
describe a promise of universal macOS extension coverage.

Update the request grammar, contract, limits, architecture/worker tours, runner
and controller references, user guide, repository orientation and tests' coverage
accounts together. Update the root guidance's one-worker wording to one fresh
worker per actor while preserving one-way application, native C boundaries and
witnessing rules. Explain the per-actor exec restriction and shared runner
entitlement choice as current coverage.

Only after functionality and acceptance warrant it, put this answer in the FAQ:

```text
Yes. See [EXTENSIONS.md](EXTENSIONS.md) for supported extension operations and authority types.
```

That future link is relative to `docs/QUESTIONS.md`, not this plan. Make
`docs/EXTENSIONS.md` the source for the extension coverage prose copied into the
guide's `sandbox-extensions` section. Extend the shared-question generator with
an explicit rebasing rule from `EXTENSIONS.md` to that internal guide anchor,
and update shared-link guidance and generator/staging checks together. Preserve
the failure contract's ownership of its generated status/reading tables. The
standalone guide must contain the coverage defining the answer; do not ship a
broken sibling-file link or edit generated copies by hand.

Completion requires the integrated public re-delegation specimen, calibrated
native path, refusal and interruption handling, independent association controls,
legacy compatibility, ABI/transport bounds, verified process/resource cleanup and
documentation above. Record acceptance and retire this active plan under the
repository's planning/records guidance when the implementation is accepted.

## Readiness and reconsideration triggers

The native interface and bounded empirical findings above support starting the
file-operation substrate. One narrow prerequisite to full acceptance remains
unverified: whether the exact B policy using an `extension` predicate on
`file-issue-extension` compiles and applies in the intended acceptance environment.
Effective re-delegation after successful application is still a result to witness,
not a required positive outcome. Admission must permit the well-formed native
issuance-refusal case without confusing it with failed policy application.

At implementation entry, use the existing supported
[`sbpl-check` helper](controller/src/bin/sbpl-check.rs) to compile B's exact policy,
then the existing single-worker run path with that policy and an ordinary
baseline access to establish application. Retain source bytes/hash, command,
equipment/environment, compiler diagnostics and worker application observations.
These are narrow policy-qualification checks, not a new standalone experiment
or a substitute for the later integrated actor case. A helper compile success
alone does not establish application or extension-dependent issuance.

If compilation or application fails, preserve the failure and keep principal
acceptance open. Diagnose the exact failure before choosing another environment
or considering a demonstrably equivalent policy spelling. If the construction
cannot be established, reconsider the principal acceptance requirement explicitly;
do not silently weaken the predicate or count calibration as the principal case.
That unresolved prerequisite must remain visible even if the rest of the
implementation is ready.

Reconsider only on concrete evidence that affects a chosen boundary: for example,
the proposed fixed mapped delivery protocol cannot be serviced after application
under the intended policies, or a native family requires an unmodeled recipient
binding. For the former, retain the failing native/setup observations and test
that precise transport boundary through the existing harness before changing the
design. For an additional family, establish its exact signature and
binding/lifetime requirements when adding that family. Neither question postpones
the specified file implementation
without such evidence.

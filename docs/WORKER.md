# The Worker: Instrument and Constraints

A worker must keep reporting under the policy it is testing while leaving the
requested operations exposed to that policy. PolicyWitness prepares its report
storage before application, then opens file targets, looks up Mach services and
creates exec resources inside the attempts. Moving a target open across that
boundary changes what the operation tests: a later read would exercise an already held
descriptor, with the authority that acquiring it supplied.

The boundary is policy application inside a running process. The executable,
libraries, memory and process context are already present. A fresh worker
applies its policy once: the one worker of the single-worker form, or one
worker per actor of the actor form, where an unapplied actor applies none. Its
later phases share that process and can observe effects of earlier actions,
and in the actor form an actor can hold authority it issued itself. The unsandboxed host arranges queries, collects
publications and replies. This tour explains the resources and constraints of
that instrument. The [architecture tour](ARCHITECTURE.md) owns orchestration
and ordering; the [build tour](BUILD.md) owns compilation and provenance;
the [evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract)
owns the meaning of its records.

## Capability map

```mermaid
flowchart TB
    subgraph worker["Worker"]
        subgraph before["Before policy application"]
            context["Credentials, restrictions<br/>and runtime state"]
            token["Actor authority region<br/>prepared before setup"]
        end
        policy["Compile policy,<br/>then apply restriction"]
        context -->|starting context| policy
        subgraph after["Under the applied policy"]
            acquire["Attempt acquisitions:<br/>file targets, Mach rights,<br/>exec setup and children"]
            extension["Requested issue, transfer,<br/>consume or release"]
        end
        policy -->|after host release| after
        token -->|explicit custody/delivery| extension
    end
    storage["Reporting storage prepared before apply<br/>Worker and host retain separate views"]
    subgraph outside["Outside the worker"]
        validator["Validator queries<br/>the live worker"]
        host["Host collects publications<br/>and assembles comparisons"]
        controller["Controller associates<br/>external log candidates"]
    end
    acquire -->|publish observations| storage
    extension -->|publish native results| storage
    storage -->|host observes retained view| host
    validator -->|predictions| host
    host -->|run evidence| controller
```

This is a conceptual overview; the [detailed capability inventory](#detailed-capability-inventory)
keeps the individual resources, lifetimes and supporting citations. The diagram
covers ordinary and actor workers. Actor workers use separate authority
regions, one-shot issue/delivery slots and transfer cells, plus per-reference
native handles; an unapplied actor proceeds from setup without applying policy.
The crosswalk below distinguishes these resources. The exec exclusion is per
participating actor, including recipients: another actor in the specimen may
exec. Delivery precedes requested consumption and does not consume a token.

| Form | Resources and acquisition | Lifetime and ownership |
| --- | --- | --- |
| All workers | Evidence object, host/worker mappings, policy and readiness endpoints prepared before setup; fixed request/result storage | The worker retains its evidence descriptor and mapping until exit; the host retains its own view through collection. These setup-held descriptors are reporting apparatus, not fresh target acquisitions. |
| Actor | Host creates one separate authority region per actor and private custody per token before launch; worker maps fd 5, closes that descriptor and snapshots inbound assignments before application | Host and worker hold distinct views. One-shot outbound/inbound slots and transfer cells cannot be reused. Shared teardown erasure requires a reaped or never-launched owner; unresolved termination permits host detachment only. Private custody has independent erasure ownership. |
| Actor actions | Native issue allocation, committed outbound slot, host custody copy, assigned inbound slot, per-reference native handle | Worker erases/frees inspected issue allocation before publication; host copies and erases outbound bytes before answering. Recipient framing acceptance and host equality/settlement precede consume. Last-use consume erases inbound bytes even on native failure; ordinary exit erases other settled inbound bytes. Handles persist separately from token bytes. |
| Requested operations | Fresh file descriptors, Mach rights, exec resources acquired inside the action after setup | These exercise then-current process conditions. Closing a file descriptor, erasing bearer bytes and a native extension release are different operations; later fresh access supplies its own observation. |

The actor resource owners are
[ActorSession](../runner/Sources/PWRunnerCore/ActorSession.swift),
[AuthorityCustody](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) and the
worker's `prepare_authority` and `erase_authority`. The
[actor handoff sequence](ARCHITECTURE.md#actor-handoff-and-schedule-advancement)
explains their completion gates; exact capacities belong to [LIMITS](LIMITS.md).

The host closes validator collection before releasing the worker to attempt a
phase; the worker receives the release ordinal, while predictions stay outside
it. The [ordering account](ARCHITECTURE.md#one-run-in-time) explains that hold
and the evidence needed to establish it.

## What the worker can establish

The worker performs admitted actions and publishes native observations. Its
inputs include attempt kinds and targets, bounded arguments, phase partitions
and time allowances; requested extension actions maintain local handle state.
Prediction belongs to the validator. The host owns disposition, collection and
comparison, and the controller gathers log candidates. Those responsibilities
are a deliberate division of work, not observations the worker failed to make.

The observations themselves have limits. Native return values and local
publications do not establish private kernel extension state, effective
permissions, revocation or the cause of a permission-shaped failure. Nor do they
show whether privacy consent mediation affected an attempt; the
[external-runner guide](PolicyWitness.md#external-runners-byoxpc) gives
target-selection guidance for that limitation. Joining host observations and
log candidates to a result does not automatically justify causal attribution or
a verdict that prediction and enforcement agree. The
[evidence ownership table](ARCHITECTURE.md#evidence-channels-and-ownership)
and [comparison contract](PolicyWitness.md#reading-a-comparison-record)
define those boundaries.

A native effect and a published result are also distinct. A call can create a
file before the worker dies without publishing its result; the host must then
withhold that result even though an independent observer can find the file.
[Native observations and publications](#native-observations-and-publications)
explains the publication boundary and its create-then-kill control.

Other omissions are measurement gaps: a live signal-mask observation and a
complete initial Mach-right census are absent from the launch evidence, not
unknowable.

## Reporting apparatus

The host's [`ActorSession`](../runner/Sources/PWRunnerCore/ActorSession.swift), used by both drivers, creates
an evidence object, requests its immediate unlink, sizes and maps it, initializes
the request and touches its pages. The worker's
[`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c) maps the
received descriptor before compilation. The mapping holds request data,
publication payloads and atomic control fields. The host's mapping remains
available during collection even when worker cleanup is unconfirmed. The
[C harness](../tests/suites/runner_c_worker_harness/README.md) checks publication
under its bare-deny and full-region cases.

The worker retains its evidence descriptor as well as the mapping. Its policy
input and readiness descriptors also stay open until exit. Policy EOF ends
source delivery and the host closes its readiness reader after the wait, while
the worker's references remain. [Launch observation L](#launch-observation-l)
saw those endpoints in both of its recorded launches.

Request, result and token storage have fixed capacities from the
[limits inventory](LIMITS.md). The policy buffer and consumed-parameter snapshot
are static worker storage. Temporary frames hold timing arithmetic, hash state,
argv pointers and diagnostics. Host-side Swift arrays and copied launch strings
remain host allocations; spawn copies argument contents into the new image.
The worker checks the received source length and bounded fields, then passes
the policy and parameter snapshot to libsandbox. Its compiled-object path is
[`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) →
[`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h)
when requested → application. PW explicitly frees the parameter object and a
returned compile-error string on the corresponding paths. The compiled profile
has no explicit PW destruction call; ownership changes inside the private apply
routine remain unobserved.

The optional compiler receipt uses the already mapped evidence region and reads
worker memory before apply. The host
[`decodeProfileCapture`](../runner/Sources/PWRunnerCore/CWorker.swift) validates
and copies the published receipt. Its relation to compiled bytes, application
and effective permissions is defined by the
[receipt contract](PolicyWitness.md#compiled-object-receipt-opt-in).

## Starting authority and ambient context

A worker starts with the authority and restrictions of its credentials, signed
image and inherited context. Built-in workers carry empty entitlements; external
runners supply a separately signed worker, whose read-back entitlements are
checked against the specimen's required keys by
[`enforce_required_entitlements`](../controller/src/runner_select.rs).
The [external-runner guide](PolicyWitness.md#external-runners-byoxpc) and
[signing reference](SIGNING.md#evidence-artifacts) own that selection and identity
account. Explicit [augments](../runner/augments/README.md#exec_baseline-composition-limits)
change the submitted policy and are recorded as such.

Host spawn actions select the policy, evidence and readiness endpoints, plus
the optional authority endpoint. Both routes initialize and pass spawn attributes.
Actor launches select `POSIX_SPAWN_CLOEXEC_DEFAULT` and defined null-device standard
streams; the ordinary route leaves those flags unset and other descriptors to
native close-on-exec inheritance. Its standard
output/error are inherited, and the evidence descriptor can also survive under
its original number if later file actions leave that number intact. The host
passes nil envp. The examined Apple
[spawn wrapper](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
forwards that pointer and the examined
[exec path](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_exec.c)
constructs an empty environment. In its two recorded empty allow-default
launches, [L](#launch-observation-l) found matching plain and
environment-displaying process output, inherited null-device standard
output/error, and the expected protocol endpoints. This observation is separate
from the source account of inheritance. The contaminated-worker control
separately establishes a configuration in which an extra descriptor and
environment value reach the worker.

The worker inherits cwd, umask, limits and signal state. It ignores SIGPIPE
before compilation. Exec-child setup selects descriptor isolation and a new
process group, while leaving ignored-signal inheritance and the signal mask to
native spawn rules. Its empty environment and selected standard descriptors
have independent [inheritance controls](../tests/suites/runner_exec_inheritance/README.md).
The observer used by those controls itself ignores SIGPIPE, so that observation
covers environment and descriptors. Actor authority setup attempts to set both core limits to zero and records the result. Actor normalization excludes exec only in authority-participating actors, including recipients.

Worker launch setup checks file-action initialization, endpoint duplication,
evidence unlink and descriptor flags, and spawn attributes before dispatch in
[`ActorSession`](../runner/Sources/PWRunnerCore/ActorSession.swift). The
[host setup controls](../tests/suites/runner_unit/README.md#host-setup-failures-and-descriptor-collisions)
inject failures in disposable source copies and observe refusal and cleanup.
Copied-argument allocation in
[`withCStringArrayCopy`](../runner/Sources/PWRunnerCore/CWorker.swift) remains
unchecked; failed copies can produce empty or truncated argv. An injected unlink failure
leaves an owned empty shared-memory name for the fixture to remove.

The single-worker form retains its launch arrangement: the low-descriptor
control can allocate evidence at fd 0, which a later policy duplication
overwrites. Actor launches relocate sources above their destinations and use
close-on-exec by default, explicitly open stdout/stderr on `/dev/null`, and
supply an empty environment. A separate kernel descriptor inventory checks actual
parked actors with a deliberately inheritable host descriptor and closed host
stdin; their explicit endpoints survive and the unrequested descriptors do not.

### Launch observation L

The [launch-inventory case](../tests/suites/runner_exec_inheritance/README.md#production-launch-inventory-opt-in)
observed two separate workers with empty allow-default plans, no extensions and
no validator queries. Existing pre-ready and post-apply sleep overrides selected
the two observation windows. Source order, selected controls and elapsed time
locate the observations; the observer did not read publication flags live.
Both captures showed numeric descriptors 0–4, read/write null-device stdout/stderr,
cwd `/`, and identical plain and environment-displaying `ps` output. `vmmap`
returned an inventory; `lsmp` refused task-port inspection. Both workers later
published completion and were reaped; the pre-ready worker reported readiness
`EPIPE` after the host's readiness wait expired.

These are observations of the recorded app and those two launch configurations.
They do not measure a transition within one process, establish an empty Mach-right
set or identify an unnamed mapping as the reporting object. Extension-bearing
workers, deny-policy acquisitions, live signal state, umask and resource limits
were outside the observation.

[L's receipt](worker-launch-observation.json) identifies run
`20261018T223601Z_85d8418b`, executed from revision
`f85c7b094d75bf72931cd4856cb4ad086da20cbe` against the signed app accepted with
runtime implementation `a458b28`. The app's own build stamp remains
`v0.3.1-39-g6380645-dirty`; its inventory matches that accepted app. Worker source
identity is
`4cb19db043606894ace2e978434f8805edf4c79245f3588cc68a33b36deca9e8`.
The receipt retains the command, specimens, source hashes, selected raw captures,
final worker evidence and hashes of the original artifacts. The original complete
raw output and app-inventory comparison record are unavailable in this checkout.
The copied observations and hashes
describe the dated run; they do not establish current-source applicability.

Reuse for another implementation or environment requires an applicability
review or a new observation; matching source hashes establish source identity,
not that the relevant conditions were exercised.

Known gap: L covers two recorded launches, and the actor descriptor controls
cover specified endpoints and injected descriptor contamination. Live signal
masks, resource limits beyond the scoped core-limit controls, a complete
Mach-right census and private runtime state remain unobserved; native inheritance
and loader behavior remain part of the instrument's received substrate, without
a complete isolation or effective-authority census.

## Acquisitions inside attempts

File targets are opened inside their requested actions. The distinctions among
those actions determine what is observed:

| Action | Call and retained observation |
| --- | --- |
| [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens read-only. The open result determines the published attempt status. On successful open, records an available descriptor-path observation, attempts a one-byte read and close, and discards those latter returns. |
| [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_TRUNC`. The open result determines the published attempt status. On successful open, attempts to write `x` and close and discards their returns. |
| [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_CREAT` and mode argument `0600`, subject to inherited umask. Existing targets are opened without truncation; missing targets can be created. Close is attempted and its return discarded. |
| [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens a fresh close-on-exec descriptor and retains open, metadata, bounded read and single-close results, including partial native evidence when a later call fails. |
| `write_fresh` / `create_fresh`, through [`attempt_file_write_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Open a fresh descriptor for an existing target or exclusive creation, then retain separate metadata, write and close observations; `write_fresh` also records truncation. Partial native evidence remains when a later call fails. |

The [existing-file control](../tests/suites/witness_contract/README.md#create-on-an-existing-file)
checks preserved bytes and object identity in its case. The
[fresh-read contract](PolicyWitness.md#extension-and-fresh-read-output) defines
which native observations and bounded bytes reach the reply.

Exec setup is also inside the attempt, after apply.
[`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h)
creates the output pipes and initializes opaque spawn handles, checks setup
results and calls cleanup for initialized resources on failure. The examined Apple
[spawn implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
allocates both handles and can grow action storage. That is a published-source
account; allocation events in the installed libraries were unobserved. PW's
post-apply diagnostics also call libc formatting and error-string routines into
fixed destinations. The examined
[formatting implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/vfprintf.c)
and [error-string implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/string/FreeBSD/strerror.c)
have path-dependent internal behavior, including a retained fallback error
buffer. Runtime allocator, locale and binding behavior remain unobserved at
these call sites.

The [per-attempt resource controls](../tests/suites/runner_c_worker_harness/README.md#exec-resources-are-per-attempt)
exercise a descriptor ceiling and a bare-deny setup path. The ceiling checks
reuse across attempts; the denying case observes setup reaching spawn for its
profile and environment. Source establishes post-apply placement. The child
receives explicit null-device stdin, captured stdout/stderr, an empty environment
and a new process group. PW drains output and observes the leader under the
[execution budgets](LIMITS.md#execution-budgets). A nonzero child exit after
successful spawn still supplies spawn evidence; the
[exec action contract](PolicyWitness.md#attempt-kinds-the-runner-implements)
keeps spawn, child exit and cleanup meanings separate.

[`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_worker_exec.h)
retains leader ownership during observation and targets its process group for
exceptional cleanup. The optional `exec_observation` records the collection
snapshot before cleanup, actual group/fallback call results and the final leader
wait separately, behind slot publication. Pending or failed waits have no status;
clock faults and local deadlines do not fabricate native errno. Missing metadata
establishes no cleanup fact. Worker death can interrupt cleanup; the host
supervises the worker. The [lifecycle controls](../tests/suites/runner_exec_lifecycle/README.md)
observe the exercised leader/descendant paths independently.

Known gap: exec descendants can outlive later steps and worker exit. Ordinary
completion requests no termination, so same-group descendants that close their
streams can survive; worker death can also leave descendants alive. Exceptional
cleanup requests target the owned group, but descendants that leave it escape
those requests. Signal returns, EOF and leader reap do not establish group absence.

Mach lookup acquires a bootstrap send-right reference, then a service right on
successful lookup. [`attempt_mach_lookup`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
attempts to deallocate the service right and leaves the acquired bootstrap
reference until process exit, including after lookup failure and repeated
attempts. This lifetime is source-established; a live right-count measurement
is absent. [`attempt_sysctl_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
uses an attempt-local stack buffer and publishes call status, discarding the
returned sysctl value. The inventory includes that buffer among local working
storage. Unlink and access calls acquire no PW-owned target handle at their
call sites.

## Supplied extension authority

Each actor chooses `equipment: "selected"` (the default) or `"unentitled"`, independently of `sandbox.mode`. Both are signed copies of the same compiled worker. The selected copy carries the runner's supplied entitlements; the unentitled copy has an empty entitlement dictionary. Neither name establishes effective authority: an unapplied actor can inherit restrictions, and signing entitlements are associated code metadata. Optional actor `required_entitlements` require boolean `true` in that actor's selected equipment and live signing readback. The controller's `runner.required_entitlements` remains a separate preflight on the selected runner worker.

The service validates its own seal, its sealed `Contents/Resources/worker-equipment.json`, and both production worker artifacts before launching any actor. The inventory binds roles to relative paths, signed hashes, CDHashes, identifiers, teams, entitlements and the compiled worker ABI/build identity. There is no fallback between roles. After usable setup and before any activation or query collection, the host inspects the owned live process and matches its associated code to the binding. An inspection failure cancels scheduled activations while preserving any application already observed. Setup-failed or unlaunched actors remain unavailable without turning their missing inspection into a failure of healthy actors.

Actor setup automatically records bounded apparatus observations before policy compilation/application: core-limit handling, authority mapping and framing, descriptor closure and each extension-symbol lookup. Missing extension symbols make the corresponding actions unavailable; required apparatus failure prevents application. Setup publication, application observation and final process disposition remain separate. Missing terminal publication leaves application uncertain rather than proving it did not happen.

A phase may specify `after_termination: {"actor_id": "issuer"}` when that actor's last scheduled visit precedes it. Before activation or query collection, the host requires an owned natural reap after source final activation, including abnormal exit; final phase completion is not required. The gate does not kill its source and expiry stays closed after later cleanup. Missing source activation/reap timestamps prevent satisfaction; a missing timestamp after dependent activation was stored retains that activation and its satisfied gate. [CONTRACT](CONTRACT.md#contract-actor_evidence-gate) owns the capture-order, clock and reference rules.

Fresh reads acquire a new descriptor at each requested action. Native consume/release observations are separate from those access effects; release success does not establish revocation.

In the actor form, [`prepare_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
resolves the issue, consume and release entry points, lowers the core limit,
maps the actor's authority region and validates its identity and index before
application. Required channel setup failure prevents the scheduler from
releasing that actor's phases; missing native symbols instead leave individual
operations unavailable. The recipient snapshots each inbound slot's assigned
source, action and delivery before application and checks them on publication. [`attempt_extension_issue`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
calls `sandbox_extension_issue_file` once with the exact submitted bytes,
publishes nonnull or NULL with the saved errno and copies a bounded token into
that issue's assigned outbound slot. It erases the native allocation to its
inspected length and frees it before publishing the slot. Published outbound
bytes belong to the host, which copies or rejects and erases them; timeout and
worker exit do not overwrite bytes a host may still read.
[`attempt_extension_transfer`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
publishes into that transfer's own cell and waits for its answer while servicing
its own inbound slots, so a transfer to itself cannot wait on itself. Actor
consume reads only the inbound slot this actor accepted and the host settled
as usable for the named delivery; the handle table is indexed by the plan's handle references rather
than one static handle. Parked actors accept or reject deliveries in
[`service_inbound_once`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
without consuming. Each servicing pass acknowledges at most one committed,
unacknowledged slot, the lowest-indexed one it visits, after checking its framing
and preassigned source, action and delivery. The pass starts after the leading
slots this worker has itself acknowledged, accepted or rejected: one local
prefix word and one local byte per inbound slot recording its own
acknowledgement stores, both cleared when preparation snapshots the inbound
assignments and never derived from the shared slot words. An uncommitted slot stops the prefix and is visited
on every pass without hiding the slots above it. Ordinary exit erases settled
inbound buffers. The host
erases remaining shared buffers only for reaped or never-launched owners;
unresolved termination permits detaching its own mapping, not clearing bytes
under a potentially live worker. Private host custody has separate
erasure ownership and does not depend on a worker publication.

The actor handle table retains each native consume result. Admission permits at most one release per handle; there is no public release retry or automatic exit-time native release. Erasing token bytes does not release a handle.

Known gap: private extension calls may allocate or retain internal state that PW
cannot inspect. Erasure observations cover PW-owned transient buffers; successful
native results and phase progress do not establish kernel extension state,
stable identity, effective permissions or access revocation.

## Native observations and publications

A native call can complete before the worker publishes the attempt slot.
[`pw_progress`](../controller/tools/pw_probe_runner/pw_worker_evidence.h)
records the latest atomic milestone, while
[`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
releases the completed slot after writing its payload. The host reads completed
payload after observing publication. The
[create-then-kill control](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication)
independently observes the created file while requiring the reply to withhold
the unpublished result. Partially written payload remains outside the evidence
the host is entitled to decode. Native call-boundary flags and result publication
have the meanings in the [worker evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract).

The worker's release wait uses atomic fields, continuous-clock samples and local
arithmetic/text. Refusal publishes `done` and exits; cancellation exits without
adding `done` or acknowledgement. After the phase loop and any selected
post-phase seam,
[`publish_done_and_exit`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
releases `done` and calls `_exit(0)` without waiting for the host.

In actor mode the worker also parks before each visit in an activation wait
built from the same atomic fields, continuous-clock samples and relax batch as
the release wait. It accepts only the global ordinal its next phase record
names and publishes that ordinal back; a greater ordinal is a published
refusal, an expired shared lifetime cutoff is a published timing failure, and
cancellation exits without `done`. A parked actor services inbound transport without running requested native
actions; the apparatus cost is one runnable polling loop per parked actor. A
cutoff already past at clock setup refuses before any policy byte. An
unapplied actor publishes its declared setup after the ready byte and never
sets `applied`, and every actor publishes its own hash of the policy bytes it
read beside the host's hash of the submitted source. Single-worker requests never
enter the activation wait. Public actor requests use this mode, exercised by
[harness activation controls](../tests/suites/runner_c_worker_harness/README.md),
actor driver tests and the
[public request contract](../tests/suites/runner_outcome_bad_request/README.md).
The lifetime cutoff is sampled in checked waits; it does not preempt a blocked
native call or bound final cleanup.
The host retains its evidence mapping after worker exit and independently
observes reaping. Its exit request still cancels a worker waiting for release;
grace and termination remain fallback cleanup. These paths use existing storage
and automatic frames. Explicit PW dynamic acquisitions after
apply are concentrated in the attempted operations; the source-level inventory
ends at native/library call boundaries whose internals remain unobserved.

Earlier actions and external actors can change conditions before a later
attempt, even with an intact release hold. Unqualified raw query records remain
available after a refusal; they do not establish whether each native call
encountered a live target. The [ordering account](ARCHITECTURE.md#one-run-in-time)
and [ordering evidence states](../tests/FAILURE-PROPAGATION-CONTRACT.md#ordering-evidence-states)
define eligibility for `query_first` and what an acknowledged release
establishes after abnormal exit.

## Changes that change what a run establishes

A proposed improvement can move authority or an observation across a boundary.
These examples connect the implementation choice to the question being tested.

| Proposed change | Effect on the question | Current behavior and evidence |
| --- | --- | --- |
| Open a file target before apply or retain a read descriptor across extension phases | Exercises previously acquired authority | Fresh-read source and [extension controls](../tests/suites/witness_contract/README.md#native-extension-boundaries) put each acquisition inside its requested action. |
| Prepare exec pipes and handles before apply | Moves setup outside the specimen's applied conditions | Per-attempt acquisition and [resource controls](../tests/suites/runner_c_worker_harness/README.md#exec-resources-are-per-attempt) retain that exposure. |
| Consume a token during preparation or put its bytes in the evidence region | Moves the authority intervention earlier or gives reporting storage bearer authority | Preparation resolves symbols; the separate channel and requested lifecycle calls are covered by the [native boundary controls](../tests/suites/witness_contract/README.md#native-extension-boundaries). |
| Retry with a changed target, extra authority or a friendlier policy, or reuse a worker for another specimen | Changes the conditions of the run | The driver launches a fresh worker for the submitted specimen. Interrupted I/O and process-observation loops retry within their existing protocols. |
| Insert `exec_baseline` automatically | Changes the tested policy, including its broad file-read allowance | [Augment composition](../runner/augments/README.md#exec_baseline-composition-limits) is explicit and recorded in resolved source. |
| Move reply assembly into the worker | Couples reporting to specimen-controlled communication | The host reads released payload; [death before publication](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication) preserves an independently observed effect with a withheld result. |

Removing the collection hold would also let worker effects change what
supposedly prior queries observe. The
[ordering controls](../tests/suites/witness_contract/README.md#predictions-before-attempts)
observe both the hold and its limited snapshot meaning.

## Detailed capability inventory

The figure and expandable inventory are generated from
[architecture.json](architecture.json). Each S/N node preserves a resource
entry; X nodes represent external evidence. The detailed authority-channel
rows describe actor apparatus and explicit custody; the [crosswalk](#capability-map) relates them to ordinary workers. This is a resource inventory, not a
complete transport sequence. The facts distinguish an object
from its descriptors, mappings and borrowed views. The host and worker can
map the same object while retaining different references and lifetimes.

Blue nodes are reporting apparatus, including exec reporting resources acquired
inside an attempt. Gold nodes represent deliberately supplied authority,
restriction or the API/compiler resources used to exercise them. Green nodes
are acquisitions by attempted operations. Purple nodes hold evidence assembled
outside the worker. White nodes have multiple roles or form the ambient
execution substrate: the fresh worker, inherited state, token mappings that
also carry metadata, extension state acquired during a requested action, and
shared working storage. Starting credentials and policy context remain outside
the supplied-authority cluster because part of that context is ambient.

Blue solid edges prepare resources; blue bold edges publish observations.
Gold bold edges deliver authority-bearing objects; green edges exercise a
resource, including applying a restriction. Purple dotted edges observe and
purple dashed edges join evidence. The application boundary is the applied-policy
node and the acquisition periods in the inventory. The authority region and reporting mapping are separate. Validator predictions join host evidence
outside the worker; the host's release ordinal controls admission to attempts.
The edges select relationships among the inventoried resources. Some nodes,
including ambient state and temporary storage, stand without a drawn
observation path. Open the SVG at its native size to read the complete map.

In the table, H is the host and W the worker. P means reporting apparatus, A supplied authority or restriction,
and O operation acquisitions. Every use of L in the inventory refers to the
[two recorded launch configurations](#launch-observation-l), with their stated
applicability limits; it does not describe every current worker. IC and CLI are
the contaminated-worker and ordinary exec-child controls in the
[inheritance suite](../tests/suites/runner_exec_inheritance/README.md).
Acquisition periods record call-site placement, including outputs acquired on
compilation return. Check citations name the particular assertion supporting a
fact; other implementation details retain source-only support. Policy-specific
outcomes belong to their stated specimens and observation conditions. Call-site
completeness is established by source review, not by citation checks.
[Runner guidance](../runner/AGENTS.md#reviewing-a-new-capability) describes the
review procedure. Process exit reclaims that process's remaining references;
created files and references held by other processes have their own lifetimes.

<!-- BEGIN GENERATED ARCHITECTURE GRAPH worker_capabilities -->
![Worker capabilities](worker-capabilities.svg)

*Figure: worker capabilities. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [worker-capabilities.dot](worker-capabilities.dot). Figure IDs correspond to the table IDs. Sources support the implementation account. Check citations state their assertion scope; remaining facts have source support only. The generator checks source-symbol presence, resolves cited definitions and requires nonempty scope text; the relevance of each assertion is reviewed, not mechanically established.*

<details>
<summary>Worker capabilities: 71 nodes and 45 edges; source-symbol presence and cited definitions checked</summary>

#### Worker capabilities nodes

| Id | Node | Kind | Inventory ID | Acquired by | When | Held across | Release / teardown action | Authority | Reaches exec children | Role | Sources | Checks and assertion scope | Limits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s1a | Evidence shared-memory object | reporting | S1a | H: pw_cworker_shm_open_create, ftruncate | Before compilation | Later phases; last mapping/reference may outlive worker | H requests immediate shm_unlink; injected failure leaves name after teardown | Shared writable input/publication storage | No explicit child reference; see S13b | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| s1b | Host shmFD | reporting | S1b | H: pw_cworker_shm_open_create; checks unlink and descriptor flags (clear in single-worker form, CLOEXEC in actor form) | Before compilation | Through successful worker spawn; host mapping remains through collection | H setup/spawn-failure close, or ownership relinquished and close after transfer deadline starts on successful spawn | Can map/resize the evidence object | Worker receives it; later validators cannot inherit the closed host reference; exec child excludes worker evidence descriptors | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata.; [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) — Independent object, descriptor-number reuse and complete-mapping teardown controls; successful worker reporting and reap remain intact. |  |
| s2 | Host evidence base mapping | reporting | S2 | H: mmap, zero/populate/page-touch | Before compilation | Beyond host descriptor close, through collection including after worker exit or unconfirmed cleanup | H defer munmap | Read worker publications; write input/release/exit request | No: exec replaces address space | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) — Controlled worker publications, ownership, acknowledgement reconciliation and confirmed reap; includes acknowledgement recovered after abnormal exit.; [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) — Independent object, descriptor-number reuse and complete-mapping teardown controls; successful worker reporting and reap remain intact. |  |
| s3a | Host ready-pipe read end | reporting | S3a | H: pipe; FD_CLOEXEC | Before compilation | Readiness wait; after a received ready byte, also polling and exit grace, until session teardown | H at session teardown after a received ready byte; otherwise after the readiness wait (deadline, EOF, read error, setup failure) or a transfer failure that skips it, or on setup/spawn failure | Observe ready byte; after it, observe hangup during the ordinary final-completion wait and worker exit grace | No: close-on-exec | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`readyReadFD`](../runner/Sources/PWRunnerCore/ActorSession.swift); [`waitExitNs`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) — Fixture workers that keep fd 4 open until exit are reaped by the sample after the hangup; a hangup before exit is followed by settle sleeps and the sleeping poll; injected timed-out and unusable waits keep the allowance and its fallback.; [`runCWorkerFinalWaitTests`](../runner/Tests/PWRunnerCoreTests/CWorkerFinalWaitTests.swift) — Ordinary final waiting uses notification only after the last collection; independent controls retain done-before-delayed-exit, owned reap without done, bounded early-hangup fallback, unusable or missing pipes, late-ready EPIPE, interrupted return, deadline and clock-fault behavior.; [`slow_compile_ready_byte_survives_sigpipe`](../tests/suites/runner_ready_byte_resilience/run.sh) — A ready byte held past the readiness deadline meets a closed read end: the wait stops at deadline and the worker's readiness write returns EPIPE.; [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| s3b | Host ready-pipe write end | reporting | S3b | H: pipe; FD_CLOEXEC | Before compilation | Through worker spawn | H immediately after spawn or failure | Supply worker readiness endpoint | Worker fd 4; child excludes it | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| s4a | Host policy-pipe read end | reporting | S4a | H: pipe; FD_CLOEXEC | Before compilation | Through worker spawn | H immediately after spawn or failure | Receive policy bytes | Worker fd 0 replaced in exec child | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| s4b | Host policy-pipe write end | reporting | S4b | H: pipe; F_SETNOSIGPIPE, O_NONBLOCK, FD_CLOEXEC | Before compilation | Through bounded policy transfer | H after transfer or setup/spawn failure | Deliver source and EOF | No: close-on-exec | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| s6 | Worker-spawn file-action handle | reporting | S6 | H: posix_spawn_file_actions_init, adddup2 | Before compilation | Through driver return | H defer destroy | Prescribes worker descriptor table | Handle no; actions determine worker state | P; setup caveat | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| s7 | Fresh worker process | mixed | S7 | H: posix_spawn; single-worker nil attributes/envp; actors explicit endpoints, CLOEXEC_DEFAULT and empty environment | Before compilation | Until exit; unconfirmed cleanup may outlive driver | Terminal publication: erase accepted token, release done, _exit; early return, cancellation, fatal signal or H termination; H waitpid observes reap | Executes specimen with inherited context and signed identity | It parents exec children; not itself inherited | none (ambient execution substrate) | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`publish_done_and_exit`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`ActorSession`](../runner/Sources/PWRunnerCore/ActorSession.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L.; [`terminal_exit_without_request`](../tests/suites/runner_c_worker_harness/run.sh) — Applied worker publishes done and exits cleanly without a host exit request. |  |
| s13a | Worker policy fd 0 | reporting | S13a | H adddup2(policyPipe[0], 0); W default policy fd | Before compilation | Later attempts and phases, until exit | No W close; exit | Read remaining policy stream; normally EOF after source receipt | No: child addopen replaces stdin | P, retained after use | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L. |  |
| s13b | Worker evidence fd 3 | reporting | S13b | H requests adddup2(shmFD, 3); low-fd collision can substitute policy pipe | Before compilation | Later attempts and phases, until exit | No W close; exit | Map backing object separately from existing mapping | No: child CLOEXEC_DEFAULT | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L.; [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| s13c | Worker ready fd 4 | reporting | S13c | H requests adddup2(readyPipe[1], 4); self-dup control leaves fd absent | Before compilation | Later attempts and phases, until exit | No W close; exit | Write readiness pipe; its close at worker exit supplies hangup to the ordinary final-completion wait and worker exit grace | No: child CLOEXEC_DEFAULT | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L.; [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| s14a | Worker inherited stdout/stderr | mixed | S14a | H spawn, without replacement file actions | Before compilation | Until exit | Exit; no explicit W close | Whatever underlying endpoints allow; L saw read/write /dev/null | No: exec-child capture pipes replace 1/2 | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L. |  |
| s14b | Other inheritable ambient host descriptors | mixed | S14b | Single-worker H spawn without CLOEXEC_DEFAULT; actor launch excludes unrequested descriptors | Before compilation | Until exit unless a file action overwrites number | No generic W sweep; exit | Depends on inherited objects | No: exec-child CLOEXEC_DEFAULT; IC/CLI test child isolation | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`POSIX_SPAWN_CLOEXEC_DEFAULT`](../runner/Sources/PWRunnerCore/ActorSession.swift) | [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| s14c | Possible original-number alias of evidence shmFD | reporting | S14c | Single-worker form: H clears FD_CLOEXEC and duplicates to 3 without closing the child source alias; actor form relocates and closes original aliases at exec | Before compilation | Until worker exit if original number survives file actions; closing the host descriptor does not remove this child reference | No generic W sweep; exit | Same evidence object as S13b, not a second object | No: exec-child CLOEXEC_DEFAULT | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | Source only; no assertion cited |  |
| s15 | Worker environment vector | mixed | S15 | H posix_spawn(..., nil) | Before compilation | Until exit | Process teardown | No entries observed; potential environment-dependent behavior is source-scoped | No: explicit {NULL} child env; IC/CLI test this boundary | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L. |  |
| s16a | Credentials and signed worker entitlements, ambient policy context | mixed | S16a | Kernel/loader at spawn; host static/live associated signing inspection | Before compilation | Until exit; SBPL/extension interventions alter effective access | Exit, not a PW reset | Role-specific signed entitlements plus inherited credentials/restrictions; neither establishes effective authority | Credentials/policy inherit subject to exec semantics; child signature supplies own entitlements | Supplied entitlements plus ambient authority/restrictions; mixed starting substrate | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`enforce_required_entitlements`](../controller/src/runner_select.rs); [`ActorEquipmentPreparation`](../runner/Sources/PWRunnerCore/ActorEquipment.swift) | Source only; no assertion cited |  |
| s16g | Working directory | mixed | S16g | Received at H spawn; no PW reset | Before compilation | Later attempts/phases, until exit | Exit | Relative file-target resolution | Yes, no chdir action | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L. |  |
| s16h | File-mode creation mask | mixed | S16h | Received at H spawn; no PW reset | Before compilation | Later attempts/phases, until exit | Exit | Reduces requested creation mode | Yes, no umask action | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | Source only; no assertion cited |  |
| s16c | Inherited resource limits | mixed | S16c | Received at H spawn | Before compilation | Until exit, except extension core-limit intervention | Exit; S20 changes core limit | Caps allocation, files, core, processes etc. | Yes by spawn inheritance; public extension/exec exclusion applies | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | Source only; no assertion cited |  |
| s16i | Inherited signal dispositions | mixed | S16i | Received at H spawn, nil attributes | Before compilation | Until exit except S17 | W changes SIGPIPE only | Affects fatal delivery and ignored signals | Ignored dispositions persist, caught handlers reset by exec | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | Source only; no assertion cited |  |
| s16j | Inherited signal mask | mixed | S16j | Received at H spawn, nil attributes | Before compilation | Until exit | No PW reset | Controls blocked signal delivery | Yes, no SETSIGMASK | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | Source only; no assertion cited |  |
| s16e | Task-self, bootstrap and other initial Mach rights | mixed | S16e | Kernel/runtime initialization at spawn | Before compilation | Until exit or library changes | No PW general release; full live right census unavailable | Task/IPC authority, bootstrap namespace access | Special-port inheritance/native exec rules; exact set unknown | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L. |  |
| s16f | Executable/library mappings, runtime heaps and threads | mixed | S16f | Loader/runtime creates new image at H spawn; later library calls | Before compilation initially; later internal changes unknown | Until exit or library release | Native runtime; no PW census/teardown | Executable code, storage and runtime service access | Not the same mappings/threads: exec loads a new image | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Requires identified worker captures, readiness and reap/absence; specific inventory contents are the separately identified observation L. |  |
| s17 | Worker ignored SIGPIPE disposition | mixed | S17 | W: signal(SIGPIPE, SIG_IGN) | Before compilation | All attempts/phases, until exit | No reset | Survive broken ready-pipe write; also changes exec-child behavior | Yes: no SETSIGDEF; no dedicated live signal control | P + effect on O | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) — Pre-ready hold requires readiness errno EPIPE followed by clean worker completion and confirmed reap. |  |
| s18 | Worker evidence base mapping | reporting | S18 | map_region: fstat, mmap(MAP_SHARED) | Before compilation | Later attempts/phases, until exit | No explicit W unmap; exit | Read requests, publish results, observe release/exit | No: exec replaces mappings and excludes fd 3 | P | [`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| s19 | Static extension function pointers | authority | S19 | prepare_authority: independent dlsym lookups | Actor setup before compilation/application | Later attempts/phases, until exit | Static storage at exit; no dynamic handle acquired here | Callable native issue/consume/release, no automatic invocation | No admitted combination; pointer storage not inherited across exec | A | [`prepare_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`run_case`](../tests/suites/witness_contract/check_extension_boundaries.py) — Missing issue, consume and release lookups yield the respective unavailable operations; consume absence preserves the available release setup cell, without inspecting private loader state. |  |
| s20 | Worker zero soft/hard core limit | mixed | S20 | prepare_authority: setrlimit(RLIMIT_CORE) | Actor setup before compilation/application | All later attempts/phases, until exit if call succeeds | No reset; exit | Core-dump restriction attempt recorded separately from missing symbols | Authority-participating actor cannot exec | P + process context | [`prepare_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`run_case`](../tests/suites/witness_contract/check_extension_boundaries.py) — Native-call controls independently read a zero soft core limit, and injected setrlimit refusal retains its primary result; successful hard-limit readback and later invariance remain source-only.; [`main`](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py) — Production worker main makes no policy read/compile/apply calls after terminal required-setup refusal, while retaining primary and cleanup failures; the continuation mutation violates that assertion. |  |
| s23 | Static policy_buf | reporting | S23 | W static storage; read_all_from_fd fills it | Before compilation | Later attempts/phases, until exit | No wipe or explicit release | Policy input, not a target-file descriptor | No: new exec image | P | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) — The direct C harness observes applied policy, terminal publication and a denied file-open attempt under bare deny-default; host Swift handling is outside this control. |  |
| s24 | Static consumed_params snapshot | reporting | S24 | W: memcpy from bounded shared parameters | Before compilation | Later attempts/phases, until exit | No wipe; static storage teardown | Exact compile/capture inputs; no additional access | No: new exec image | P | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`params_round_trip`](../tests/suites/runner_c_worker_harness/run.sh) — Named TARGET parameter reaches the compiled policy: the configured path attempt returns EPERM after successful apply; allocation/free details remain source-only. |  |
| s25 | params_obj and parameter entries | authority | S25 | W: sandbox_create_params, sandbox_set_param | Before compilation | Until compile return, or parameter refusal | sandbox_free_params on success/failure paths after creation | Supplies named compiler inputs | No: freed before possible child spawn | A | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`params_round_trip`](../tests/suites/runner_c_worker_harness/run.sh) — Named TARGET parameter reaches the compiled policy: the configured path attempt returns EPERM after successful apply; allocation/free details remain source-only. |  |
| s26a | Returned compiled profile and its bytecode | authority | S26a | W: sandbox_compile_string | On compilation return, before apply | Passed to capture/apply; allocation lifetime inside apply unknown | No explicit sandbox_free_profile; exit reclaims remaining process storage | Input to restriction application; not an applied policy by itself | No: new exec image; applied restriction separate S28 | A | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) — The direct C harness observes applied policy, terminal publication and a denied file-open attempt under bare deny-default; host Swift handling is outside this control. |  |
| s26b | Compiler error string compile_err on failure | reporting | S26b | W: sandbox_compile_string out parameter | On compilation return, before apply | Failure reporting only | W free when non-null and profile null | None; diagnostic bytes | No child on failed compile path | P | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`compile_failure`](../tests/suites/runner_c_worker_harness/run.sh) — Malformed source publishes compile refusal without apply or attempts and exits cleanly; native error allocation/free is source-only. |  |
| s27 | Compiled capture bytes/header inside S18 | reporting | S27 | pw_capture_profile / pw_read_memory: mach_vm_read_overwrite, hashes | Between compilation and apply | Later attempts/phases, until exit; host copies accepted receipt | No separate allocation/unmap; S18 teardown | Read own task memory via preexisting task port; publish receipt | No: new image, evidence fd excluded | P | [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h) | [`max_targets_reply_survives`](../tests/suites/witness_contract/max_targets_reply_survives.sh) — The maximal-metadata workload requires a captured compiled-profile receipt with positive bytecode length in the returned reply. |  |
| s28 | Applied sandbox policy | authority | S28 | W: sandbox_apply(profile) | Between compilation and apply closing boundary | All later attempts/phases, until exit on success | One-way, no undo | Restricts starting authority; extension may augment access | Inherited sandbox constraints | A | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) — The direct C harness observes applied policy, terminal publication and a denied file-open attempt under bare deny-default; host Swift handling is outside this control. |  |
| s29 | open_read target fd | operation | S29 | attempt_file_open_read: open(O_RDONLY) | After apply within an attempt | Attempt only on ordinary cleanup path | close after best-effort one-byte read; return ignored | Read opened object | No: closed before later exec, which also excludes it | O | [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) — The direct C harness observes applied policy, terminal publication and a denied file-open attempt under bare deny-default; host Swift handling is outside this control. |  |
| s30 | open_write target fd | operation | S30 | attempt_file_open_write: open(O_WRONLY \| O_TRUNC) | After apply within an attempt | Attempt only on ordinary cleanup path | close after unchecked one-byte write | Write/truncate opened object; actual write result unpublished | No: later exec excludes it | O | [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`file_actions_have_exact_effects`](../tests/suites/run_effects/file_actions_have_exact_effects.sh) — Independent file bytes establish the open-write/truncation effect; the worker does not publish the write return. |  |
| s31a | create target fd | operation | S31a | attempt_file_create: open(O_WRONLY \| O_CREAT, 0600) | After apply within an attempt | Attempt only on ordinary cleanup path | close, return ignored | Write existing object or create missing object | No: later exec excludes it | O | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`create_existing_file_preserves_contents`](../tests/suites/witness_contract/create_existing_file_preserves_contents.sh) — Pre-existing targets retain their bytes after create-open; this does not exercise absent-target creation. |  |
| s31b | Newly created filesystem object, if absent | operation | S31b | attempt_file_create: same open | After apply within an attempt | Later attempts/phases and beyond worker exit | No automatic unlink; later action/external actor may remove | Persistent filesystem effect, mode subject to umask | Child can resolve it by path, not inherited fd | O | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`create_allow`](../tests/suites/runner_c_worker_harness/run.sh) — An initially absent target exists after the successful create attempt under allow-default; the worker also publishes its observed path. |  |
| s32 | Fresh target fd and read observation | operation | S32 | attempt_file_read_fresh: open(O_RDONLY \| O_CLOEXEC), fstat, read | After apply within an attempt | Attempt only on successful close; close failure retained | One close, result published; no retry | Read and identify fresh opened object | No: close-on-exec and child exclusion | O | [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`extensions`](../tests/suites/witness_contract/extensions.sh) — Fresh-read and extension action evidence is compared with independent file bytes and native-call controls; native release is not a revocation assertion. |  |
| s32w | Fresh write fd and observations | operation | S32w | attempt_file_write_fresh: open(O_WRONLY \| O_CLOEXEC), fstat, ftruncate, write | After apply within an attempt | Attempt only on successful close; close failure retained | One close; failure retained; completed bytes may persist | Modify the opened existing object | No: close-on-exec and child exclusion | O | [`attempt_file_write_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`fresh_write`](../tests/suites/runner_c_worker_harness/fresh_write.sh) — Production syscall substitutions assert open/stat/truncate/write/close order, native failures, short writes and combined-failure preservation; no native policy effect is inferred.; [`extension_directory`](../tests/suites/witness_contract/extension_directory.sh) — Owned existing files and initially absent children provide independent contents and entry observations through ordinary CLI phases, with authority controls and publication withholding. |  |
| s32c | Exclusive child creation and fd | operation | S32c | attempt_file_write_fresh: lstat, open(O_WRONLY \| O_CREAT \| O_EXCL \| O_CLOEXEC, 0600), fstat, write | After apply within an attempt | Attempt only on successful close; close failure retained | One close; failure retained; created entry and bytes may persist | Create an absent child and write its opened object | No: close-on-exec and child exclusion | O | [`attempt_file_write_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`fresh_write`](../tests/suites/runner_c_worker_harness/fresh_write.sh) — Production syscall substitutions assert open/stat/truncate/write/close order, native failures, short writes and combined-failure preservation; no native policy effect is inferred.; [`extension_directory`](../tests/suites/witness_contract/extension_directory.sh) — Owned existing files and initially absent children provide independent contents and entry observations through ordinary CLI phases, with authority controls and publication withholding. |  |
| s33a | Bootstrap send-right reference | operation | S33a | attempt_mach_lookup: task_get_special_port | After apply within an attempt | Later attempts/phases, until exit after successful acquisition | No matching mach_port_deallocate, even when lookup fails | Bootstrap namespace request authority | No explicit transfer; special bootstrap port inheritance is separate | O, unintended retention | [`attempt_mach_lookup`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| s33b | Lookup service send right | operation | S33b | attempt_mach_lookup: bootstrap_look_up | After apply within an attempt | Attempt on successful lookup | mach_port_deallocate(mach_task_self, svc), result ignored | Send to looked-up service | No explicit port-transfer action | O | [`attempt_mach_lookup`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| s34a | Exec stdout/stderr read endpoints | reporting | S34a | exec_resources_acquire: two pipe calls | After apply within an attempt | One attempt | exec_resources_release, including partial setup/spawn failure | Read child output | No: explicit addclose and CLOEXEC_DEFAULT | P | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| s34b | Exec stdout/stderr write endpoints | reporting | S34b | exec_resources_acquire: two pipe calls | After apply within an attempt | Until successful spawn in worker; child lifetime may extend | Worker closes after spawn; setup/spawn failure releases; child exit closes own refs | Child output channel | Yes, duplicated as 1/2; originals explicitly closed | P | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| s35a | Exec file-action heap handle | reporting | S35a | exec_resources_acquire: init, addopen/dup2/close | After apply within an attempt | One attempt | exec_resources_release destroys initialized handle | Select child descriptors, including /dev/null | Handle no; action effects yes | P | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | Source only; no assertion cited |  |
| s35b | Exec attribute heap handle | reporting | S35b | exec_resources_acquire: init/setflags/setpgroup | After apply within an attempt | One attempt | exec_resources_release destroys initialized handle | Child fd isolation and process-group choice | Handle no; flags/group effects yes | P | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | Source only; no assertion cited |  |
| s36a | Exec child PID/process | operation | S36a | attempt_exec_spawn: posix_spawn | After apply within an attempt | Attempt normally; unconfirmed reap or worker death can leave child alive | Wait observation, conditional group kill, bounded nonblocking reap | Execute requested target under inherited sandbox | This is the child; it can spawn descendants | O | [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF.; [`closed_streams_leader_exit`](../tests/suites/runner_exec_lifecycle/closed_streams_leader_exit.sh) — Independent peer identity/group observations establish same-group survival after ordinary completion, then fixture cleanup.; [`worker_dies_during_exec`](../tests/suites/runner_exec_lifecycle/run.sh) — Independent child observations establish survival after worker death and retain fixture-owned cleanup.; [`test_production`](../tests/suites/runner_c_worker_harness/test_exec_control_states.py) — Production exec code with controlled native returns checks collection, termination-request and leader-reap separation and native call order. |  |
| s36b | Child process group | reporting | S36b | Exec spawn attributes SETPGROUP, pgroup 0 | After apply within an attempt | As long as members remain, possibly beyond attempt/worker | No request on ordinary completion; exceptional group kill while leader ownership is known; no group-absence claim | Cleanup addressing for members that remain | Yes to descendants unless they leave group | P | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h); [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`closed_streams_leader_exit`](../tests/suites/runner_exec_lifecycle/closed_streams_leader_exit.sh) — Independent peer identity/group observations establish same-group survival after ordinary completion, then fixture cleanup.; [`worker_dies_during_exec`](../tests/suites/runner_exec_lifecycle/run.sh) — Independent child observations establish survival after worker death and retain fixture-owned cleanup.; [`test_production`](../tests/suites/runner_c_worker_harness/test_exec_control_states.py) — Production exec code with controlled native returns checks collection, termination-request and leader-reap separation and native call order. |  |
| s37 | Per-reference native handles | mixed | S37 | attempt_extension_consume_actor: native consume result other than -1 | After actor setup within an explicitly released action | Across attempts/phases; requested release is not proven revocation | One requested release per handle; no automatic exit-time native release; OS teardown | Native extension access represented by handle; exact kernel state unobserved | Authority-participating actor cannot exec | A + O | [`attempt_extension_consume_actor`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`attempt_extension_release_actor`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`main`](../tests/suites/runner_c_worker_harness/actor_operations.py) — Production bodies and run_attempt dispatch bind distinct synthetic consume results to named handles and release the matching handle once; omitted, misrouted and crossed dispatch fail without establishing kernel authority or revocation.; [`main`](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py) — Production-main scenarios count no native release except the explicit-release action; token-byte erasure and process termination do not establish kernel revocation. |  |
| n5 | Host copied launch argument strings | reporting | N5 | withCStringArrayCopy: strdup for H/E invocations | Before compilation | Spawn call only | Helper defer free; Swift array lifetime | Transfer launch arguments, not token bytes | Arguments copied into new images, host pointers not inherited | P; setup caveat | [`withCStringArrayCopy`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| n6 | Host policy byte array and request-population temporary arrays/data | reporting | N6 | H: Array(input.policy.utf8), writeString, captureNonceBytes | Before compilation | Transfer/population scope; input objects may live through run | Swift scope/ARC, not worker teardown | Exact delivered inputs and nonce | No host memory inheritance | P | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | Source only; no assertion cited |  |
| n8 | Worker main-frame arguments, timing state and capture nonce | reporting | N8 | W local declarations, pw_clock_start, nonce memcpy | Before compilation | Main frame until exit; timing changes across phases | Process exit (main never returns after successful apply) | Operate release/timing protocol; no new access handle | No: new exec image | P | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| n9a | Worker temporary pre-compile call frames | reporting | N9a | parse_args, map_region, read_all_from_fd, pw_timing_setup, prepare_authority | Before compilation | Call only | Return or process exit | None beyond existing pointers/rights | No: exec replaces stack | P | [`parse_args`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`read_all_from_fd`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`pw_timing_setup`](../controller/tools/pw_probe_runner/pw_worker_timing.h); [`prepare_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| n9b | Capture hash/view/digest/sorting call frames | reporting | N9b | pw_capture_profile, pw_consumed_params_digest, pw_read_memory | Between compilation and apply | Call only | Return or process exit | Read own memory with existing task right | No: exec replaces stack | P | [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h) | Source only; no assertion cited |  |
| n10 | Attempt-local stack buffers, argv pointers, polls, wait status and metadata | mixed | N10 | run_attempt and each attempt_*, capture_observed_path, drain_one, exec_resources_acquire; attempt_sysctl_read holds a sysctl value-read buffer of 4,096 bytes on the stack | After apply within an attempt | Call/attempt only; selected observations copied into S18; sysctl value bytes and post-call length discarded | Return or process exit | Use already inventoried target/child handles; no separate authority | argv_local strings copied; stack not inherited | O + P (working/observation storage) | [`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`attempt_sysctl_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`check_capacity`](../tests/suites/runner_c_worker_harness/check_sysctl.py) — Independent call receipt requires the fixed supplied sysctl capacity; a shortened-capacity mutant is rejected.; [`check_call_and_result`](../tests/suites/runner_c_worker_harness/check_sysctl.py) — Substituted sysctl success/failure returns preserve rc/errno semantics despite changed out-parameter length. | [`sysctl_read_bytes`](LIMITS.md#execution-budgets) |
| n11 | Post-apply outside-attempt automatic diagnostics and seam timespec | reporting | N11 | wait_for_proceed, proceed_refused, W post-phase seam | After apply outside an attempt | Call, or nonreturning refusal frame until exit | Return/exit; not dynamically allocated by PW | None; diagnostic/control working storage | No child spawned on these paths | P | [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| n12 | Exec child stdin /dev/null fd 0 | reporting | N12 | exec_resources_acquire registers addopen; native spawn executes it | After apply within an attempt | Child lifetime | Child closes it or exits | Read EOF without exposing policy pipe | Yes, explicit child fd 0 | P | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| n13 | Libc diagnostic state reachable after apply | reporting | N13 | fail_from_errno, exec_setup_failed, attempt_exec_spawn, attempt_mach_lookup, run_attempt: snprintf, strerror | After apply within an attempt | Library-dependent; ordinary errno table is static, fallback buffer retained | Library/exit; no PW-owned handle | Diagnostic formatting; hidden allocation/locale behavior bounded only by source studied | Library memory not carried across exec | P | [`fail_from_errno`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`exec_setup_failed`](../controller/tools/pw_probe_runner/pw_worker_exec.h); [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_worker_exec.h); [`attempt_mach_lookup`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| x1 | Validator predictions | external | X1 | planValidatorQueries | Query collection outside worker | Eligible phase and reply | Owning host/controller object lifetime | Live worker PID query through separate validator | No worker-to-child transfer | External evidence | [`planValidatorQueries`](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift) | [`comparison_matrix`](../tests/suites/witness_contract/comparison_matrix.sh) — Independent reader checks query/attempt association and phase-order evidence on the submitted comparison specimens. |  |
| x2 | Host disposition and comparison | external | X2 | comparisonEvidence | After collection/publication | Reply | Owning host/controller object lifetime | Join worker publications, query records and process observations | No worker-to-child transfer | External evidence | [`comparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerComparison.swift) | [`comparison_matrix`](../tests/suites/witness_contract/comparison_matrix.sh) — Independent reader checks query/attempt association and phase-order evidence on the submitted comparison specimens. |  |
| x3 | Host path diagnostics | external | X3 | enrichPathDiagnostics | After attempt collection | Reply | Owning host/controller object lifetime | Later path/metadata observations under host authority | No worker-to-child transfer | External evidence | [`enrichPathDiagnostics`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`path_query_integrated`](../tests/suites/witness_contract/opt_in/path_query_integrated.sh) — Integrated path-query controls check later host path resolution and its separation from the worker observation. |  |
| x5 | Compiler receipt in dossier | external | X5 | decodeProfileCapture | Capture before apply; host decode after publication | Reply and optional dossier | Owning host/controller object lifetime | Copy/hash admitted receipt from shared evidence | No worker-to-child transfer | External evidence | [`decodeProfileCapture`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`max_targets_reply_survives`](../tests/suites/witness_contract/max_targets_reply_survives.sh) — The maximal-metadata workload requires a captured compiled-profile receipt with positive bytecode length in the returned reply. |  |
| a1 | Per-actor authority object and host mapping | mixed | A1 | ActorAuthorityRegion creates, unlinks, maps and frames region | Host preparation before first launch | Setup, visits and owner cleanup | Shared erasure only after owner reaped or never launched; unresolved owner permits host detach only | One-shot outbound/inbound slots and transfer answer cells | No authority-participating actor exec | A | [`ActorAuthorityRegion`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Copied host acquisition paths independently check descriptor/mapping cleanup and preserve an unlink-failure name until fixture cleanup; they do not observe a shipped run at CLI return.; [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) — An independent mapping of seeded slots observes erasure only for declared quiescent owners and preservation across repeated finish for unknown owners; the control does not establish a live reap. |  |
| a7 | Host authority launch duplicate | authority | A7 | ActorSession duplicates the authority-region descriptor with F_DUPFD_CLOEXEC and minimum fd 64 | Host preparation before worker compilation/application | Spawn setup through spawn return or failure cleanup | Host closeAuthorityDuplicate closes the launch duplicate; worker fd 5 closes independently in prepare_authority after mapping | Host-owned reference to the same authority object; spawn dup2 supplies worker fd 5 | Only explicit worker fd 5; high duplicate is close-on-exec and authority-participating actor cannot exec | A | [`F_DUPFD_CLOEXEC`](../runner/Sources/PWRunnerCore/ActorSession.swift); [`closeAuthorityDuplicate`](../runner/Sources/PWRunnerCore/ActorSession.swift); [`prepare_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Requested authority dup2 destinations match child descriptor metadata and owned setup resources close on the exercised paths; metadata does not establish shared backing identity.; [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) — An injected authority-duplication failure prevents launch, and a read-only fixture endpoint remains separate at fd 5 in extension_delivery; this does not establish authority-region backing identity. |  |
| a2 | Worker authority descriptor and mapping | mixed | A2 | ActorSession supplies fd 5; prepare_authority validates, maps, closes descriptor and snapshots assignments | Before compilation/application | Mapping through worker exit | Settled inbound erasure on ordinary departure; rejected mapping unmap separately observed | Read/write assigned custody exchange cells; no other actor mapping | No authority-participating actor exec | A | [`prepare_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`erase_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`authority_binding`](../tests/suites/runner_c_worker_harness/authority_binding.sh) — Production worker setup maps a fixture-created region, including page-rounded maximum geometry, and rejects changed owner/action/delivery assignments; shared observations cover those two fixture views.; [`check_setup_failure`](../tests/suites/witness_contract/check_extension_boundaries.py) — Controlled setup refusals retain exact primary and independent cleanup-cell results, suppress application and later native attempts, and retain observed reap; private runtime allocations remain unobserved.; [`main`](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py) — Seeded full-capacity settled inbound bytes are erased before done on the exercised production-main departures while outbound/unsettled bytes remain; fatal interruption can leave bytes, so exit alone does not establish erasure. |  |
| a3 | Native issued token allocation | authority | A3 | attempt_extension_issue calls native issue | Explicit action after setup | Bounded inspection/copy only | Erase inspected length and free before outbound publication; oversized tail unobserved | Transient bearer bytes | No authority-participating actor exec | A | [`attempt_extension_issue`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`run_case`](../tests/suites/witness_contract/check_extension_boundaries.py) — Controlled native issuance observes returned token bytes and erasure of the inspected allocation; free ordering and the uninspected oversized tail remain source-only. |  |
| a4 | Private host token custody | authority | A4 | TokenCustody maps a private buffer; AuthorityCustody later copies accepted outbound bytes and erases the shared source | Mapping before first actor launch; population after committed issue publication | Mapping until teardown; accepted bytes until last declared transfer or teardown | Private bytes erased at last use/teardown independently of worker publication; mapping unmapped at teardown | Deliberately supplied bearer bytes | No authority-participating actor exec | A | [`AuthorityCustody`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`TokenCustody`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | [`main`](../tests/suites/runner_unit/actor_handoff_mutations.py) — Independent synthetic payload comparisons and outbound erasure observations accept the baseline and reject outbound aliasing and premature erasure; these controls make no native extension calls. |  |
| a5 | Assigned recipient inbound bytes | authority | A5 | Host copies custody to assigned slot; recipient accepts framing; host checks equality and settles | During parked servicing or transfer wait | Until last declared consume or ordinary terminal erasure | Worker erases last-use/settled bytes; host shared teardown requires reaped owner | Consumption requires committed, accepted, usable delivery | No authority-participating actor exec | A | [`service_inbound_once`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`attempt_extension_consume_actor`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`authority_binding`](../tests/suites/runner_c_worker_harness/authority_binding.sh) — Assigned owner/action/delivery mismatches are rejected and consume waits for accepted host settlement; worker cleanup preserves unsettled inbound bytes and clears settled bytes. Counted scan seams assert exact visits and loads per pass: the scan starts at the prefix of slots this worker acknowledged, accepted or rejected, an uncommitted lower slot is visited every pass without blocking higher slots, and re-preparation resets the prefix.; [`main`](../tests/suites/runner_unit/actor_handoff_mutations.py) — Disposable worker copies whose scan starts at slot 0, whose prefix steps over an uncommitted slot or advances over shared acknowledgement words, or whose preparation keeps the previous prefix each fail a designated authority_binding pass observation while the unmodified copy passes.; [`main`](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py) — Seeded full-capacity settled inbound bytes are erased before done on the exercised production-main departures while outbound/unsettled bytes remain; fatal interruption can leave bytes, so exit alone does not establish erasure.; [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) — The live actor schedule checks copied/equal delivery, recipient and matching source acknowledgements, and parked acceptance before the recipient visit; source-acknowledgement controls reject incomplete or mismatched publications. |  |
| a6 | Automatic setup evidence trailer | reporting | A6 | Host creates bounded trailer; worker publishes operation cells and terminal decision | Before compilation/application and terminal cleanup | Host evidence mapping through session collection/teardown; decoded setup values continue into reply | Evidence mapping teardown; no token bytes | Reporting apparatus with separate native and publication facts | No authority-participating actor exec | P | [`prepare_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`decodeAuthoritySetup`](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift); [`finish`](../runner/Sources/PWRunnerCore/ActorScheduler.swift); [`tearDown`](../runner/Sources/PWRunnerCore/ActorSession.swift) | [`check_setup_failure`](../tests/suites/witness_contract/check_extension_boundaries.py) — Controlled setup refusals retain exact primary and independent cleanup-cell results, suppress application and later native attempts, and retain observed reap; private runtime allocations remain unobserved.; [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) — Constructed release-published cleanup cells decode before the terminal setup decision with their native result and cleanup role, while invalid cell flags are rejected; this is receiver eligibility, not a live publication-order measurement.; [`main`](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py) — Production worker main makes no policy read/compile/apply calls after terminal required-setup refusal, while retaining primary and cleanup failures; the continuation mutation violates that assertion. |  |

#### Worker capabilities edges

| Id | From | To | Kind | Edge | Sources | Checks and assertion scope | Limits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | s1b | s2 | prepares | Host maps evidence descriptor | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) — Independent mapping challenges distinguish the true evidence object; worker reporting and final reap remain intact. |  |
| W2 | s1a | s1b | prepares | Host holds backing-object descriptor through worker launch | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) — Independent object, descriptor-number reuse and complete-mapping teardown controls; successful worker reporting and reap remain intact. |  |
| W3 | s1b | s13b | prepares | Spawn action duplicates evidence descriptor | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) — Independent mapping challenges distinguish the true evidence object; worker reporting and final reap remain intact. |  |
| W4 | s13b | s18 | prepares | Worker maps evidence descriptor | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| W5 | s3b | s13c | prepares | Spawn action duplicates readiness endpoint | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| W6 | s4a | s13a | prepares | Spawn action duplicates policy endpoint | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| W7 | s4b | s23 | prepares | Policy delivery fills static source buffer | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | Source only; no assertion cited |  |
| W8 | s6 | s7 | prepares | Worker launch file actions select protocol endpoints | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| W9 | n5 | s7 | prepares | Copied argv supplies worker launch arguments | [`withCStringArrayCopy`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Setup controls compare requested dup2 destinations with child descriptor metadata, check argv counts and instrumented cleanup; shared-object identity is not established by metadata. |  |
| W10 | n6 | s2 | prepares | Host initializes request fields and nonce | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | Source only; no assertion cited |  |
| W11 | s23 | s26a | prepares | Compiler reads source buffer | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) — The direct C harness observes applied policy, terminal publication and a denied file-open attempt under bare deny-default; host Swift handling is outside this control. |  |
| W12 | s24 | s25 | prepares | Snapshot entries populate compiler parameters | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`params_round_trip`](../tests/suites/runner_c_worker_harness/run.sh) — Named TARGET parameter reaches the compiled policy: the configured path attempt returns EPERM after successful apply; allocation/free details remain source-only. |  |
| W13 | s25 | s26a | prepares | Compiler receives parameter object | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`params_round_trip`](../tests/suites/runner_c_worker_harness/run.sh) — Named TARGET parameter reaches the compiled policy: the configured path attempt returns EPERM after successful apply; allocation/free details remain source-only. |  |
| W14 | s26a | s27 | prepares | Capture reads returned compiled object | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h) | [`max_targets_reply_survives`](../tests/suites/witness_contract/max_targets_reply_survives.sh) — The maximal-metadata workload requires a captured compiled-profile receipt with positive bytecode length in the returned reply. |  |
| W15 | s35a | s36a | prepares | Spawn file actions select child descriptors | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| W16 | s35b | s36b | prepares | Spawn attributes select child process group | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`closed_streams_leader_exit`](../tests/suites/runner_exec_lifecycle/closed_streams_leader_exit.sh) — Independent peer identity/group observations establish same-group survival after ordinary leader-plus-EOF completion, then fixture cleanup. |  |
| W32 | s26a | s28 | exercises | Apply receives compiled object and imposes policy | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) — The direct C harness observes applied policy, terminal publication and a denied file-open attempt under bare deny-default; host Swift handling is outside this control. |  |
| W33 | s33a | s33b | exercises | Lookup uses acquired bootstrap reference | [`attempt_mach_lookup`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Source only; no assertion cited |  |
| W34 | s31a | s31b | exercises | Successful create-open can create absent file | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`create_allow`](../tests/suites/runner_c_worker_harness/run.sh) — An initially absent target exists after the successful create attempt under allow-default; the worker also publishes its observed path. |  |
| W35 | s34b | s36a | exercises | Child receives output endpoints as stdout/stderr | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| W36 | n12 | s36a | exercises | Child receives explicit stdin | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| W37 | s37 | s32 | exercises | Fresh read attempts access under current extension state | [`attempt_extension_consume_actor`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`extension_boundaries`](../tests/suites/witness_contract/extension_boundaries.sh) — Controlled issuer/worker native-call boundaries, delivery/refusal metadata and token confinement; private library allocation internals remain source-only. |  |
| W38 | s27 | s18 | publishes | Capture writes receipt into evidence mapping | [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h) | [`max_targets_reply_survives`](../tests/suites/witness_contract/max_targets_reply_survives.sh) — The maximal-metadata workload requires a captured compiled-profile receipt with positive bytecode length in the returned reply. |  |
| W39 | s29 | s18 | publishes | Publishes open status and available observed path | [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) — The direct C harness observes applied policy, terminal publication and a denied file-open attempt under bare deny-default; host Swift handling is outside this control. |  |
| W40 | s30 | s18 | publishes | Publishes open status; write return discarded | [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`file_actions_have_exact_effects`](../tests/suites/run_effects/file_actions_have_exact_effects.sh) — Independent file bytes establish the open-write/truncation effect; the worker does not publish the write return. |  |
| W41 | s31a | s18 | publishes | Publishes file-create attempt status from open result | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`create_existing_file_preserves_contents`](../tests/suites/witness_contract/create_existing_file_preserves_contents.sh) — Pre-existing targets retain their bytes after create-open; this does not exercise absent-target creation. |  |
| W42 | s32 | s18 | publishes | Publishes native open/stat/read/close observations | [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`extensions`](../tests/suites/witness_contract/extensions.sh) — Fresh-read and extension action evidence is compared with independent file bytes and native-call controls; native release is not a revocation assertion. |  |
| W43 | s33b | s18 | publishes | Publishes lookup status, not retained port authority | [`attempt_mach_lookup`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`prediction_unavailable_attempt_observed`](../tests/suites/runner_filter_local_name/run.sh) — The live local-name specimen retains native lookup attempt status; no right-count or deallocation assertion. |  |
| W44 | s36a | s18 | publishes | Publishes spawn, wait and cleanup observations | [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| W45 | s37 | s18 | publishes | Publishes consume/release native result | [`attempt_extension_consume_actor`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`extension_boundaries`](../tests/suites/witness_contract/extension_boundaries.sh) — Controlled issuer/worker native-call boundaries, delivery/refusal metadata and token confinement; private library allocation internals remain source-only. |  |
| W47 | s3a | s13c | observes | Host reads worker readiness byte | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) — Controlled worker readiness, release/acknowledgement and exit/reap observations. |  |
| W48 | s2 | s18 | observes | Host observes publications in its retained evidence mapping, including after worker exit | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) — Controlled worker publications, ownership, acknowledgement reconciliation and confirmed reap; includes acknowledgement recovered after abnormal exit. |  |
| W49 | s34a | s36a | observes | Worker drains child output | [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_worker_exec.h); [`drain_one`](../controller/tools/pw_probe_runner/pw_worker_exec.h) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh) — Repeated successful execs and surrounding reads under a hard descriptor ceiling constrain descriptor accumulation across attempts; call placement remains source-derived.; [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) — Independent observer receives the canary descriptor/environment in the worker adapter and excludes them from exec children; checks child stdio and stdin EOF. |  |
| W51 | s2 | x2 | joins | Host uses admitted publications | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`comparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerComparison.swift); [`observeAcknowledgement`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) — Controlled worker publications, ownership, acknowledgement reconciliation and confirmed reap; includes acknowledgement recovered after abnormal exit. |  |
| W52 | x1 | x2 | joins | Host joins prediction records to attempt evidence | [`planValidatorQueries`](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift) | [`comparison_matrix`](../tests/suites/witness_contract/comparison_matrix.sh) — Independent reader checks query/attempt association and phase-order evidence on the submitted comparison specimens. |  |
| W53 | x3 | x2 | joins | Host attaches later path-resolution results | [`enrichPathDiagnostics`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`path_query_integrated`](../tests/suites/witness_contract/opt_in/path_query_integrated.sh) — Integrated path-query controls check later host path resolution and its separation from the worker observation. |  |
| W54 | s27 | x5 | joins | Host decodes and copies receipt | [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h); [`decodeProfileCapture`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`max_targets_reply_survives`](../tests/suites/witness_contract/max_targets_reply_survives.sh) — The maximal-metadata workload requires a captured compiled-profile receipt with positive bytecode length in the returned reply. |  |
| W55 | s32w | s18 | publishes | Publishes separate write and metadata observations through completed slot | [`attempt_file_write_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`fresh_write`](../tests/suites/runner_c_worker_harness/fresh_write.sh) — Production syscall substitutions assert open/stat/truncate/write/close order, native failures, short writes and combined-failure preservation; no native policy effect is inferred.; [`extension_directory`](../tests/suites/witness_contract/extension_directory.sh) — Owned existing files and initially absent children provide independent contents and entry observations through ordinary CLI phases, with authority controls and publication withholding. |  |
| W56 | s32c | s18 | publishes | Publishes separate write and metadata observations through completed slot | [`attempt_file_write_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`fresh_write`](../tests/suites/runner_c_worker_harness/fresh_write.sh) — Production syscall substitutions assert open/stat/truncate/write/close order, native failures, short writes and combined-failure preservation; no native policy effect is inferred.; [`extension_directory`](../tests/suites/witness_contract/extension_directory.sh) — Owned existing files and initially absent children provide independent contents and entry observations through ordinary CLI phases, with authority controls and publication withholding. |  |
| W57 | a1 | a2 | prepares | Map distinct host and worker views | [`prepare_authority`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Copied host acquisition paths independently check descriptor/mapping cleanup and preserve an unlink-failure name until fixture cleanup; they do not observe a shipped run at CLI return.; [`authority_binding`](../tests/suites/runner_c_worker_harness/authority_binding.sh) — Production worker setup maps a fixture-created region, including page-rounded maximum geometry, and rejects changed owner/action/delivery assignments; shared observations cover those two fixture views. |  |
| W58 | a3 | a4 | supplies_authority | Publish bounded token then copy and erase source | [`AuthorityCustody`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | [`main`](../tests/suites/runner_unit/actor_handoff_mutations.py) — Independent synthetic payload comparisons and outbound erasure observations accept the baseline and reject outbound aliasing and premature erasure; these controls make no native extension calls. |  |
| W59 | a4 | a5 | supplies_authority | Copy, acknowledge, compare and settle delivery | [`serviceTransfer`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) — The live actor schedule checks copied/equal delivery, recipient and matching source acknowledgements, and parked acceptance before the recipient visit; source-acknowledgement controls reject incomplete or mismatched publications.; [`authority_binding`](../tests/suites/runner_c_worker_harness/authority_binding.sh) — Production recipient controls reject changed assignments and prevent consume or erasure before host settlement; synthetic bytes establish channel ownership, not native authority. |  |
| W60 | a5 | s37 | exercises | Requested native consume produces handle | [`attempt_extension_consume_actor`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`main`](../tests/suites/runner_c_worker_harness/actor_operations.py) — Production bodies and run_attempt dispatch bind distinct synthetic consume results to named handles and release the matching handle once; omitted, misrouted and crossed dispatch fail without establishing kernel authority or revocation. |  |
| W61 | a6 | s18 | publishes | Release-published automatic setup facts | [`decodeAuthoritySetup`](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift) | [`check_setup_failure`](../tests/suites/witness_contract/check_extension_boundaries.py) — Controlled setup refusals retain exact primary and independent cleanup-cell results, suppress application and later native attempts, and retain observed reap; private runtime allocations remain unobserved.; [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) — Constructed release-published cleanup cells decode before the terminal setup decision with their native result and cleanup role, while invalid cell flags are rejected; this is receiver eligibility, not a live publication-order measurement.; [`main`](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py) — Production worker main makes no policy read/compile/apply calls after terminal required-setup refusal, while retaining primary and cleanup failures; the continuation mutation violates that assertion. |  |
| W62 | a7 | a2 | prepares | Duplicate to worker fd 5; close host launch reference | [`authority_spawn_dup2`](../runner/Sources/PWRunnerCore/ActorSession.swift); [`closeAuthorityDuplicate`](../runner/Sources/PWRunnerCore/ActorSession.swift) | [`check`](../tests/suites/runner_unit/host_setup_controls.py) — Requested authority dup2 destinations match child descriptor metadata and owned setup resources close on the exercised paths; metadata does not establish shared backing identity.; [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) — An injected authority-duplication failure prevents launch, and a read-only fixture endpoint remains separate at fd 5 in extension_delivery; this does not establish authority-region backing identity. |  |

Notes:

- `s6`: Worker setup controls observe failed file-action initialization/addition refusing spawn without use of an invalid handle.
- `s14a`: L observed read/write null-device stdout and stderr.
- `s14b`: L observed no additional numeric descriptor; the contaminated-worker control separately supplies a positive inheritance case.
- `s14c`: L observed no original-number evidence alias in its endpoint arrangement; source permits other arrangements.
- `s15`: L produced identical plain and environment-displaying ps output; this is scoped to those two launches.
- `s16a`: Selected signing metadata and required-key checks do not measure effective worker authority.
- `s16g`: L observed cwd / in both launches.
- `s16h`: No live umask measurement is credited.
- `s16c`: No live resource-limit census is credited.
- `s16i`: No live inherited-signal census is credited.
- `s16j`: No live signal-mask measurement is credited.
- `s16e`: L port inspection was refused; the exact live right set remains unknown.
- `s16f`: L retained vmmap output; per-allocation origin and policy gating remain unknown.
- `s17`: L pre-ready launch retained readiness errno EPIPE and later clean completion.
- `s19`: Private loader/library internals remain unobserved.
- `s25`: Private parameter-allocation internals remain unobserved.
- `s26a`: Private compiled-object lifetime inside apply remains unknown.
- `s33a`: No independent right-count control is cited for the retained bootstrap reference.
- `s33b`: No independent right-count control is cited for service-right release.
- `s35a`: The examined Apple source uses malloc/realloc; installed allocation behavior is unobserved.
- `s35b`: The examined Apple source uses malloc; installed allocation behavior is unobserved.
- `n5`: Controlled strdup failure can dispatch empty or truncated argv.
- `n6`: Swift allocation internals and temporary-array lifetimes have source support only.
- `n9a`: Native library internals remain unobserved.
- `n9b`: qsort/CommonCrypto internal allocation behavior remains unobserved.
- `n10`: Compiler stack/page behavior remains unobserved; the sysctl checks cover supplied capacity and return handling.
- `n13`: Installed libc allocation and locale internals remain unobserved.
- `x1`: No transfer into worker; release ordinal is separate
- `x2`: Host-owned interpretation under evidence contract
- `x5`: Receipt and applied-policy evidence are distinct
- `W4`: Source identifies the descriptor-to-mapping operation. L does not independently identify the evidence mapping object.
- `W51`: A final acquire after confirmed reap can recover an unseen acknowledgement while ownership remained unbroken; successful completion is not required and broken ownership cannot be repaired.

Claims without a cited check: `s14c`, `s16a`, `s16h`, `s16c`, `s16i`, `s16j`, `s18`, `s33a`, `s33b`, `s35a`, `s35b`, `n6`, `n8`, `n9a`, `n9b`, `n11`, `n13`, `W4`, `W7`, `W10`, `W33`.

</details>
<!-- END GENERATED ARCHITECTURE GRAPH worker_capabilities -->

## Known gaps

- [Starting authority and ambient context](#starting-authority-and-ambient-context): the launch observation is a bounded census of inherited and runtime state.
- [Acquisitions inside attempts](#acquisitions-inside-attempts): exec descendants can survive ordinary completion or worker death; escaped descendants are not contained.
- [Supplied extension authority](#supplied-extension-authority): private native state and allocation extend beyond PW-owned buffer and publication observations.

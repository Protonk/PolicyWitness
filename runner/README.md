# `runner/`

This directory contains the Swift XPC host and client for PolicyWitness.
The host accepts one specimen and stays unsandboxed. When execution proceeds,
a fresh C worker applies the specimen policy to itself. The host collects their
observations and the validator's predictions into one `PWRunnerRunResult`
reply, which the controller wraps in its output envelope.

[AGENTS.md](AGENTS.md) describes how to change and test the runner, including
the native helpers maintained under `controller/tools/`. The
[architecture tour](../docs/ARCHITECTURE.md) describes the process and evidence
boundaries across the application. The
[worker tour](../docs/WORKER.md) explains the instrument's resources, authority
and constraints.

## Key files

Meson compiles the core sources and service entry point into `PWRunner.xpc`.
[Package.swift](Package.swift) exposes the same core and C shim to a test
executable; it does not build the shipped service bundle.

| Area | Sources and responsibility |
| --- | --- |
| Shared wire entry | [PWRunnerAPI.swift](Sources/PWRunnerCore/PWRunnerAPI.swift): XPC protocol, wire constants and versions; [PWRunnerCoding.swift](Sources/PWRunnerCore/PWRunnerCoding.swift): closed-object key checking and JSON encoding/decoding. These and the wire families below compile in host and client. |
| Requests and extensions | [PWRunnerRequest.swift](Sources/PWRunnerCore/PWRunnerRequest.swift): ordinary requests, phases, overrides and refusal records; [PWRunnerExtension.swift](Sources/PWRunnerCore/PWRunnerExtension.swift): actor interventions, native event/fresh-file records and local validity rules. |
| Attempt and path evidence | [PWRunnerAttemptEvidence.swift](Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift): native attempt records and local read/write/exec validity; [PWRunnerPathEvidence.swift](Sources/PWRunnerCore/PWRunnerPathEvidence.swift): identities and path forms. |
| Prediction and step evidence | [PWRunnerPredictionEvidence.swift](Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift): native query and validator records and association; [PWRunnerStepEvidence.swift](Sources/PWRunnerCore/PWRunnerStepEvidence.swift): step/comparison/ordering records and ordered-query eligibility. |
| Lifecycle and disposition evidence | [PWRunnerLifecycleEvidence.swift](Sources/PWRunnerCore/PWRunnerLifecycleEvidence.swift): worker publications, host waits and subprocess records; [PWRunnerDisposition.swift](Sources/PWRunnerCore/PWRunnerDisposition.swift): claims, issues, lifecycle projection and integrity validation. |
| Reply and profile evidence | [PWRunnerReply.swift](Sources/PWRunnerCore/PWRunnerReply.swift): phase/run records and checks joining families; [PWRunnerProfileCapture.swift](Sources/PWRunnerCore/PWRunnerProfileCapture.swift): compiled-profile records and local validity. |
| Service lifecycle | [PWRunnerService.swift](Sources/PWRunnerCore/PWRunnerService.swift): caller authorization, shared single-use admission, request handling, reply degradation and host retirement. |
| Listener and bundle | [PWRunnerListener.swift](Sources/PWRunnerCore/PWRunnerListener.swift): listener selection; [Services/PWRunner/](Services/PWRunner/): entry point, Info.plist and entitlements. |
| Orchestration | [CWorkerOrchestrator.swift](Sources/PWRunnerCore/CWorkerOrchestrator.swift): admission, ordinary worker execution, per-phase collection, driver invocation and final reply sequence; [CWorkerRequestPlanning.swift](Sources/PWRunnerCore/CWorkerRequestPlanning.swift): request translation, capacity checks, refusal assembly and fresh query planning; [ActorPlan.swift](Sources/PWRunnerCore/ActorPlan.swift): the actor form's normalized reference tables; [ActorOrchestration.swift](Sources/PWRunnerCore/ActorOrchestration.swift): per-actor driver inputs, the schedule with per-phase collection, and the actor-indexed reply. |
| Host result construction | [CWorkerStepResults.swift](Sources/PWRunnerCore/CWorkerStepResults.swift): query/attempt step assembly; [CWorkerComparison.swift](Sources/PWRunnerCore/CWorkerComparison.swift): ordering and comparison construction; [CWorkerDisposition.swift](Sources/PWRunnerCore/CWorkerDisposition.swift): unique slot association, disposition, subprocess projection and outcome classification. |
| Child drivers | [ActorSession.swift](Sources/PWRunnerCore/ActorSession.swift): one owned worker process: evidence region, pipes, launch, policy transfer, readiness, polling primitives, cleanup and decoded output; [CWorker.swift](Sources/PWRunnerCore/CWorker.swift): the layout mirror, driver inputs and outputs, the single-worker loop over one session and the shared child lifecycle observer; [ActorScheduler.swift](Sources/PWRunnerCore/ActorScheduler.swift): the actor form's serial schedule over several sessions; [AuthorityCustody.swift](Sources/PWRunnerCore/AuthorityCustody.swift): per-actor authority regions, host custody buffers and transfer servicing, with no sandbox call; [ValidatorClient.swift](Sources/PWRunnerCore/ValidatorClient.swift): concurrent probe writes/verdict reads and partial-evidence collection. |
| Actor equipment and setup | [ActorEquipment.swift](Sources/PWRunnerCore/ActorEquipment.swift): sealed inventory, static bindings and live code inspection; [PWRunnerEquipment.swift](Sources/PWRunnerCore/PWRunnerEquipment.swift): shared evidence/readers; [AuthoritySetupRuntime.swift](Sources/PWRunnerCore/AuthoritySetupRuntime.swift) and [PWRunnerAuthoritySetup.swift](Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift): automatic setup account. |
| Time and native shim | [MonotonicDeadline.swift](Sources/PWRunnerCore/MonotonicDeadline.swift): deadlines and policy-pipe delivery; [PWCWorkerShim/](Sources/PWCWorkerShim/): fixed-argument shared-memory opening and acquire/release helpers. |
| Request and path helpers | [ProbeRunner.swift](Sources/PWRunnerCore/ProbeRunner.swift): request meaning and prediction-exclusion definitions; [SandboxApply.swift](Sources/PWRunnerCore/SandboxApply.swift): policy hashing; [PathUtils.swift](Sources/PWRunnerCore/PathUtils.swift): planning and later host path observations. |
| Client and tests | [Clients/PWRunnerClient/main.swift](Clients/PWRunnerClient/main.swift): JSON request and binary reply XPC client; [Tests/PWRunnerCoreTests/](Tests/PWRunnerCoreTests/): explicitly registered TestKit groups. |

The reply representation is owned by
[docs/porcelain.json](../docs/porcelain.json). Its generator writes stored-field
regions, direct Swift binary writers, owned Rust records/readers and the
structural tables a separately written Python reader uses. `PWPorcelain.swift` implements the closed primitive
format. `validateForReporting` runs the semantic gates before normal writing;
rich degradation retains observations while withholding comparisons, and an
independent minimal writer reports lost evidence. The client relays opaque host
bytes in a binary capture. Lifecycle questions have fixed named fields; missing
answers remain representable in incomplete evidence. Equipment metadata counts
retained UTF-8 text directly. Byte payloads (compiled-profile bytecode, rejected
validator context, fresh-read content) and digests are stored and written as
bytes; the controller spells them as base64 or hexadecimal in public JSON.
The inventory file's hexadecimal digests are decoded where that file is read.
Equipment rows refer to each other by table index. JSON request/control decoding, validator NDJSON
and the equipment inventory file retain their own boundary adapters.

The native [C worker](../controller/tools/pw_probe_runner/pw_probe_runner.c) and
[batch validator](../controller/tools/sb_api_validator/sb_api_validator.c) live outside this directory. The build embeds the worker twice and the validator as `pw-probe-runner`,
`sb_api_validator` and `pw-probe-runner-unentitled` in each service's `Contents/MacOS/`; the host resolves them
relative to its own bundle for both built-in and external runners. Only these
runner children call the sandbox APIs. The host's source and shipped imports
are checked by [source drift](../tests/suites/source_drift/README.md) and
[artifact inspection](../tests/suites/preflight/README.md).

The worker entry source keeps preparation, application, phase waits, attempt
dispatch and terminal publication together. Its private included
[timing owner](../controller/tools/pw_probe_runner/pw_worker_timing.h) supplies
the shared clock, conversions, allowances and fault diagnostics; phase waiting
commits a checked deadline extension immediately before acknowledgement. The
[exec owner](../controller/tools/pw_probe_runner/pw_worker_exec.h) receives a slot
and timing context and owns its pipes, spawn handles, collection and child cleanup
within that attempt. Both compile in the worker's single translation unit, so
native-call controls intercept the same included implementation.

The default validator path is always the service's
`Contents/MacOS/sb_api_validator`; an explicit `validator_executable_path`
override takes precedence. Selection does not check executability or imply
launch. A reached native spawn reports a missing or non-executable helper at
the selected path. An earlier refusal or a phase with no eligible queries
creates no validator spawn failure.

## Run lifecycle

1. Caller authorization gates the connection. All connections share one
   reservation slot. The effect-free reservation binds a single-use identifier
   to its authenticated connection and a fixed expiry. Only that connection can
   consume it for execution, before specimen decoding. Expiry or abandonment
   retires an unused host; an executing host finishes its existing worker
   lifecycle despite client loss. Every callback checks the shared state before
   scheduling exit. The client retries only acquisition; it never replays after
   invoking execution. Reservation credentials remain inside the connection.
2. The service decodes and admits the request and validates meaning before
   creating children. `probe_plan` becomes one phase named `main`; explicit
   phases share one total action capacity. The worker receives policy bytes on
   its input pipe, whose expected byte count the host wrote into the shared
   header before spawn, and shares fixed-layout inputs/publications with the
   host; at EOF it publishes the count it read and refuses a different length
   before compiling, so a delivery cut short is never applied as a shorter policy.
3. The worker applies the policy once, then publishes arrival at each phase.
   After a received ready byte, the ordinary host may resample first arrival
   or done once before sleeping, under its existing clock and sample bounds.
   This observation opportunity does not authorize collection by itself.
   The host checks successful application, identity and worker ownership, plans
   that phase's queries afresh and collects eligible queries with a fresh
   `sb_api_validator --batch` child. No eligible queries means no validator.
4. Collection closes on every terminal path. The host rechecks the live phase
   before publishing its numbered release; the worker acknowledges that release
   before actions, then publishes phase completion before its next arrival.
   Each phase retains immutable publications and its own validator evidence.
   No later record joins a closed collection. Expired waits and worker loss
   stop progression; earlier observations remain. The worker decides expiry
   from validated continuous-clock samples in one tick domain shared with its
   exec allowances; an unusable sample also refuses the phase before
   acknowledgement, and a late release cannot revive it.
5. Every terminal publication erases any accepted token buffer, releases `done`
   and exits without awaiting host permission. Cancellation before acknowledgement
   erases the buffer and exits without adding `done`, acknowledgement or failure.
   The host retains cancellation, grace, termination and reaping. After a confirmed
   reap it reconciles acknowledgements published between samples, including before
   an abnormal exit, only while ownership through acknowledgement is established.
   After the last ordinary collection, it can wait on the retained readiness pipe
   for exit notification while keeping bounded checks of `done`. Notification
   prompts observation; it establishes neither publication nor reap. An early
   hangup is consumed once, with bounded sleeping checks thereafter.
6. The host gathers completed slots, partial evidence and independent child
   lifecycle observations, assembles the reply, then schedules its own exit.

For the actor form the same steps run per actor under one scheduler: every
actor's region and authority region exist before the first launch; actors
launch in order under one setup allowance and each publishes its own setup
(application, or an explicit unapplied setup decision); the schedule activates one actor
per phase, plans and collects that phase's queries against that actor's PID,
releases its visit ordinal and awaits its completion while servicing the
active actor's token publications and transfer requests; a failed actor is
stopped and reaped before another is activated; and every actor is stopped,
reaped and read at the end. The reply carries each actor's own records and no
singular worker or policy projection.

The host evidence descriptor lasts only through worker launch. After successful
spawn, the host starts the existing policy-transfer deadline, relinquishes close
ownership and closes the descriptor before policy delivery. Setup and spawn
refusals retain their original cleanup. The host mapping remains through final
evidence collection and teardown; later validators cannot inherit the closed
host reference. Worker descriptors already installed by spawn, including any
surviving original-number alias, keep their separate lifetime.

Actor authority regions are separate from evidence mappings. Token bytes never enter retained JSON, argv or environment. Worker-owned accepted buffers are erased on ordinary departure; host shared-buffer erasure requires a reaped or never-launched owner. Native release remains an explicit action. Call markers and completed result publication are separate; lifecycle actions create no validator queries.

Each actor chooses `equipment: "selected"` (the default) or `"unentitled"`, independently of `sandbox.mode`. Both are signed copies of the same compiled worker. The selected copy carries the runner's supplied entitlements; the unentitled copy has an empty entitlement dictionary. Neither name establishes effective authority: an unapplied actor can inherit restrictions, and signing entitlements are associated code metadata. Optional actor `required_entitlements` require boolean `true` in that actor's selected equipment and live signing readback. The controller's `runner.required_entitlements` remains a separate preflight on the selected runner worker.

The service validates its own seal, its sealed `Contents/Resources/worker-equipment.json`, and both production worker artifacts before launching any actor. The inventory binds roles to relative paths, signed hashes, CDHashes, identifiers, teams, entitlements and the compiled worker ABI/build identity. There is no fallback between roles. After usable setup and before any activation or query collection, the host inspects the owned live process and matches its associated code to the binding. An inspection failure cancels scheduled activations while preserving any application already observed. Setup-failed or unlaunched actors remain unavailable without turning their missing inspection into a failure of healthy actors.

Actor setup automatically records bounded apparatus observations before policy compilation/application: core-limit handling, authority mapping and framing, descriptor closure and each extension-symbol lookup. Missing extension symbols make the corresponding actions unavailable; required apparatus failure prevents application. Setup publication, application observation and final process disposition remain separate. Missing terminal publication leaves application uncertain rather than proving it did not happen.

A phase's `after_termination` dependency requires an owned natural reap after the source's final activation, before dependent activation and query collection. Abnormal natural exit can satisfy it without final phase completion. Source clock uncertainty prevents satisfaction, while clock loss after dependent activation was stored cannot erase that activation. The gate never requests termination to satisfy itself. [The wire contract](../docs/CONTRACT.md#actor-evidence-ownership) defines source association, clock eligibility and retained evidence.

Every validator query uses `SANDBOX_CHECK_NO_REPORT`, so predictions produce no
denial records. `comparison.order=query_first` requires eligible native records,
that phase's collection/release/acknowledgement chain and worker lifetime evidence.
The same worker acknowledging after collection closes establishes that it lived
through the collected interval; successful attempts or a successful run are not
required. Without that chain, raw validator allow/deny/error records remain
observations but do not qualify as predictions about a live specimen. Refusal
does not cancel the synchronous collector or determine which native calls saw an
exited target. A degraded reporting-failure reply withholds all comparisons and
certifies no per-step order, even when it retains raw ordering observations. The
[ordering contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#ordering-evidence-states)
defines the claims and withheld states.

Policy-transfer, readiness, sentinel, validator and cleanup allowances cover
different stages. A client timeout does not cancel the host, and a successful
termination request does not establish reaping. Some final waits can block;
there is no total lifecycle deadline. The
[limits inventory](../docs/LIMITS.md#execution-budgets) and
[host-observation contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#host-observations)
describe these bounds and remaining cleanup limitations.

## Specimen inputs

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 6, response schema 30, controller envelope 14, runner protocol 4. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

The runner consumes `PWRunnerRunSpec`: the accepted request version, SBPL
source and optional parameters, and exactly one of `probe_plan` or `phases`.
An ordinary action always has a submitted query and attempt. Phase IDs are
unique and nonempty; step IDs are unique across the entire specimen. Codable types and
their `CodingKeys` define acceptance. Unknown fields, wrong types, unsupported
versions, unsupported attempt/filter names and ineffective combinations produce
`bad_request` with a bounded `request_failure`. Capacity admission is shared
between service handling and direct orchestration.

Extension actions are actor-only and use issue, transfer, consume and release with owner-bound local references. An ordinary request containing `extensions` or an extension action is refused. The issuer passes the submitted absolute path unchanged, selecting the native read or read-write class from `authority`. Raw tokens and caller-selected native class strings are not admitted.

The controller resolves `policy.augments` and removes selection fields before
delivery. Direct XPC requests containing nonempty unresolved augments or
controller selection fields are refused. The [request grammar](../docs/REQUEST-GRAMMAR.md)
and [accepted input contract](../docs/CONTRACT.md#accepted-input-contract)
own the full rules; [augments/](augments/README.md) describes the shipped policy
fragment.

The optional `compiled_profile` receipt captures the worker's compiler output
before application and explicitly names its worker producer and `before_apply`
capture stage. The host exposes it only after checking successful application,
completion and the receipt's identity/integrity evidence. The
[receipt contract](../docs/PolicyWitness.md#compiled-object-receipt-opt-in)
defines its contents, sensitive-output handling and unavailable cases.

## Run result highlights

The host joins evidence without attributing every failed operation to the
sandbox or declaring prediction/enforcement agreement. Its principal records are:

| Record | Responsibility and contract |
| --- | --- |
| `runner_subprocess` | Worker publications and independent host observations; [worker evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract) and [disposition](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-disposition-record). Its PID is authoritative for worker correlation. |
| `phases[].validator_subprocess`, `phases[].validator_spawn_failure` | Observed validator execution, accepted records and collection faults, or a failed native launch. A failed launch creates no subprocess record; [receiver contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#admission-and-validatorcontroller-receiver-contract). |
| `phases[]` | Ordered arrival/completion observations, collection status, action membership and phase-local ordering. Missing publications remain missing. |
| `extension_events[]`, `transfers`, `resources` | Actor native results and separate custody/delivery observations; [native evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence). Raw tokens are absent. |
| `steps[].sandbox_check`, `attempt`, `comparison` | Predictions, attempted-operation evidence, and their submitted-scope/order relations; [comparison contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#comparison-record). Later host path resolution is separately attributed. |
| `normalized_outcome`, `reporting_failure` | Classification of available observations and any reply-construction failure; [classification](../tests/FAILURE-PROPAGATION-CONTRACT.md#evidence-and-classification) and [reply failure](../tests/FAILURE-PROPAGATION-CONTRACT.md#reply-construction-failure). |

Native observations remain distinct from summaries: the query's `native_rc`
carries a native return, while attempt `rc` is PolicyWitness status.
`file/read_fresh` retains open/stat/read/close results and descriptor identity
under `attempt.fresh_read`; `open_read` remains open-only.
`file/write_fresh` and `file/create_fresh` retain open, explicit truncation where
applicable, fixed one-byte write, close and metadata observations under
`attempt.fresh_write`. Creation is exclusive and has a diagnostic pre-open
`lstat`; legacy `open_write` and `create` retain their existing meanings.
`no_completed_result` means no completed attempt result; the lifecycle evidence,
not the outcome, says whether an operation began. Missing subprocess records or lifecycle fields establish neither
successful execution nor cleanup.

For a completed `exec/spawn` result after successful spawn,
`attempt.exec_observation` carries the pre-cleanup collection snapshot, actual
group/fallback termination requests and final nonblocking leader wait. The
worker records these in reserved slot storage, sets payload validity only after
assembly, and publishes them through the existing slot completion release/acquire
boundary. The decoder never salvages an unpublished payload. Malformed present
payloads use the reporting-integrity failure path; absent metadata is compatible
and establishes no cleanup fact. Legacy aggregate attempt status and spawned-child
comparison precedence remain separate from this evidence. The
[exec field account](../docs/PolicyWitness.md#structured-exec-observations) defines
all conditional fields and residual descendant lifetime limits.

Readers and reporting validation require the current response version. If
reporting admission or the ordinary binary write fails, the service returns
`runner_reporting_failed`, preserving available observations and withholding
comparisons. If that also fails, `evidence_retained: false` marks the minimal
reply. If even the minimal write fails, the host returns zero bytes, which the
controller reports as `malformed_runner_response` with no host result. Full wire fields and reading
rules belong to the [output reference](../docs/PolicyWitness.md#output-envelope).

## Test seam: `_test_overrides`

The optional request block changes inputs at production boundaries; the real
drivers and classifier determine the result. Supplied controls are mirrored in
`test_overrides` when available, subject to refusal sanitization. An echo does
not establish that a boundary was reached or that its requested effect occurred.
An empty or default-valued control can be inert. Early replies can omit the
echo, so a missing echo cannot establish that no controls were submitted;
retain the request for that fact.

| Key | Request type | Default and effective behavior |
| --- | --- | --- |
| `worker_executable_path` | string | Ordinary requests only: substitutes the worker spawn path. A nonexistent path can exercise `worker_spawn_failed`. |
| `actor_equipment_executable_paths` | closed object | Actor requests only: nonempty `selected`/`unentitled` map of absolute signed fixture paths. Both packaged roles are still verified first. Overrides retain actual identity and `test_override` provenance; valid ad-hoc fixtures are allowed but receive no packaged build/signing credit. Missing or invalid code refuses before launch; an ABI mismatch remains worker setup evidence. |
| `worker_timeout_ms` | integer milliseconds | <!-- span limits.worker_sentinel_wait.value_unit -->120,000 milliseconds<!-- /span -->; changes the host sentinel allowance, leaving the worker's exec budget unchanged. |
| `validator_io_timeout_ms` | integer milliseconds | <!-- span limits.validator_io_wait.value_unit -->30,000 milliseconds<!-- /span -->; sets the proposed per-phase I/O deadline, capped by the remaining aggregate collection allowance. |
| `validator_total_timeout_ms` | integer milliseconds | Reduces the aggregate collection allowance, clamped to 1–<!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span --> across all phases. Later collections can become unavailable while attempts still run. |
| `validator_executable_path` | string | Bundle-local `sb_api_validator`; substitutes the validator spawn path after successful worker application. |
| `worker_post_apply_hang_ms` | integer milliseconds | Disabled when absent or nonpositive. Requests a native sleep after completed slots and before `done`; paired with a shorter sentinel allowance it can exercise timeout handling. |
| `worker_post_apply_kill_signal` | integer signal number | Disabled when absent or nonpositive. Requests self-signalling after completed slots and before `done`; observed fatal delivery can exercise `runner_failed`. |
| `worker_pre_ready_hang_ms` | integer milliseconds | Disabled when absent or nonpositive. Requests a native sleep after compilation/optional capture, before the ready byte; publication depends on the remaining host allowance. |
| `worker_kill_before_publish_slot` | integer slot index | Disabled when absent or negative. If the slot is reached, requests SIGKILL on the worker after dispatch returns and before its `completed` flag is stored. Dispatch can refuse without making a native attempt. Observed started progress with no published result does not recover an unpublished native return or identify a signal's sender or policy cause. |

Decoding accepts representable integers. The host floors deadline overrides in
[`timeoutMsForCWorker`](Sources/PWRunnerCore/CWorkerRequestPlanning.swift) and
[`timeoutMsForValidator`](Sources/PWRunnerCore/CWorkerRequestPlanning.swift).
It forwards only positive delay/signal values and nonnegative slot indexes; the worker's
[`parse_args`](../controller/tools/pw_probe_runner/pw_probe_runner.c) enforces
their upper bounds. A rejected native argument can stop the child before the
intended seam. Failed signal delivery or a nonfatal/ignored signal can return
and allow `done` publication; requesting a signal proves neither termination
nor policy cause.

This is the single override-key reference. The
[drift check](../tests/suites/source_drift/README.md) compares its keys with
`PWRunnerTestOverrides`; it does not verify the table's semantics. Working rules
and assertions are in [AGENTS.md](AGENTS.md#testing-normalized_outcome-failure-paths-via-_test_overrides).

## External runner services

Built-in services use `NSXPCListener.service()`. Launchd starts an external host
with `--mach-service <name>`, selecting `NSXPCListener(machServiceName:)`.
Both use the same protocol, reply schema and single-use admission. The external
host remains unsandboxed; its fresh worker applies the policy.

The shipped Info.plist enables `PWRunnerRequireSignedCaller` and supplies
`PWRunnerAllowedIdentifiers`. When enabled, authorization requires matching
caller/host Team IDs and, if configured, an allowed signing identifier.
Copied service bundles inherit this configuration. The
[BYOXPC guide](../docs/PolicyWitness.md#external-runners-byoxpc) describes signing,
ad-hoc configuration and installation through the
[controller manager](../controller/README.md#runner-external-runner-manager).
Required entitlements are checked against the selected worker's read-back.

## Unit tests (SwiftPM)

The [runner_unit suite](../tests/suites/runner_unit/README.md) builds lifecycle
fixtures and runs `PWRunnerCoreTests`, a TestKit executable that works with
Command Line Tools. The core uses `-enable-testing` for `@testable import`;
production builds go through `build.sh`. From the repository root:

```sh
tests/run.sh --suite runner_unit --suite runner_c_worker_harness
```

These suites require a signed app for their native-driver checks. Test setup,
registration, evidence rules and sandboxed-harness diagnostics are in
[AGENTS.md](AGENTS.md).

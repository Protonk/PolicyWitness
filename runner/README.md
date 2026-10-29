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
and experimental constraints.

## Key files

Meson compiles the core sources and service entry point into `PWRunner.xpc`.
[Package.swift](Package.swift) exposes the same core and C shim to a test
executable; it does not build the shipped service bundle.

| Area | Sources and responsibility |
| --- | --- |
| Wire types and admission | [PWRunnerAPI.swift](Sources/PWRunnerCore/PWRunnerAPI.swift): XPC protocol, Codable request/reply types, closed request objects and evidence validation. |
| Service lifecycle | [PWRunnerService.swift](Sources/PWRunnerCore/PWRunnerService.swift): caller authorization, shared single-use admission, request handling, reply degradation and host retirement. |
| Listener and bundle | [PWRunnerListener.swift](Sources/PWRunnerCore/PWRunnerListener.swift): listener selection; [Services/PWRunner/](Services/PWRunner/): entry point, Info.plist and entitlements. |
| Orchestration | [CWorkerOrchestrator.swift](Sources/PWRunnerCore/CWorkerOrchestrator.swift): query planning, driver invocation, evidence association, disposition, classification and comparisons. |
| Child drivers | [CWorker.swift](Sources/PWRunnerCore/CWorker.swift): worker launch, shared memory, publication polling and the shared child lifecycle observer; [ValidatorClient.swift](Sources/PWRunnerCore/ValidatorClient.swift): concurrent probe writes/verdict reads and partial-evidence collection. |
| Extension preparation | [ExtensionIssuer.swift](Sources/PWRunnerCore/ExtensionIssuer.swift): target resolution/metadata, separate issuer lifetime, bounded transient token delivery and host erasure. |
| Time and native shim | [MonotonicDeadline.swift](Sources/PWRunnerCore/MonotonicDeadline.swift): deadlines and policy-pipe delivery; [PWCWorkerShim/](Sources/PWCWorkerShim/): fixed-argument shared-memory opening and acquire/release helpers. |
| Request and path helpers | [ProbeRunner.swift](Sources/PWRunnerCore/ProbeRunner.swift): request meaning and prediction-exclusion definitions; [SandboxApply.swift](Sources/PWRunnerCore/SandboxApply.swift): policy hashing; [PathUtils.swift](Sources/PWRunnerCore/PathUtils.swift): planning and later host path observations. |
| Client and tests | [Clients/PWRunnerClient/main.swift](Clients/PWRunnerClient/main.swift): JSON-over-Data XPC client; [Tests/PWRunnerCoreTests/](Tests/PWRunnerCoreTests/): explicitly registered TestKit groups. |

The native [C worker](../controller/tools/pw_probe_runner/pw_probe_runner.c) and
[batch validator](../controller/tools/sb_api_validator/sb_api_validator.c) and
[extension issuer](../controller/tools/pw_probe_runner/pw_extension_issuer.c)
live outside this directory. Meson embeds them as `pw-probe-runner`,
`sb_api_validator` and `pw-extension-issuer` in each service's `Contents/MacOS/`; the host resolves them
relative to its own bundle for both built-in and external runners. Only these
runner children call the sandbox APIs. The host's source and shipped imports
are checked by [source drift](../tests/suites/source_drift/README.md) and
[artifact inspection](../tests/suites/preflight/README.md).

The default validator path is always the service's
`Contents/MacOS/sb_api_validator`; an explicit `validator_executable_path`
override takes precedence. Selection does not check executability or imply
launch. A reached native spawn reports a missing or non-executable helper at
the selected path. An earlier refusal or a phase with no eligible queries
creates no validator spawn failure.

## Run lifecycle

1. Caller authorization gates the connection. The host shares one terminal
   request claim across connections; another request receives `already_ran`.
   The claim precedes decoding, so a refused request also consumes the host.
   Only the claim owner schedules exit after its reply.
2. The service decodes and admits the request and validates meaning before
   creating children. `probe_plan` becomes one phase named `main`; explicit
   phases share one total action capacity. The worker receives policy bytes on
   its input pipe, whose expected byte count the host wrote into the shared
   header before spawn, and shares fixed-layout inputs/publications with the
   host; at EOF it publishes the count it read and refuses a different length
   before compiling, so a delivery cut short is never applied as a shorter policy.
   An extension declaration requires explicit phases. Before worker creation,
   the host resolves its target and records metadata, then launches the issuer
   under ordinary authority. Only bounded issuance with a confirmed clean reap
   permits delivery. Missing helper/native issuance capability is a named refusal;
   preparation and other issuance failures remain evidence beside unavailable actions.
3. The worker applies the policy once, then publishes arrival at each phase.
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
6. The host gathers completed slots, partial evidence and independent child
   lifecycle observations, assembles the reply, then schedules its own exit.

The host evidence descriptor lasts only through worker launch. After successful
spawn, the host starts the existing policy-transfer deadline, relinquishes close
ownership and closes the descriptor before policy delivery. Setup and spawn
refusals retain their original cleanup. The host mapping remains through final
evidence collection and teardown; later validators cannot inherit the closed
host reference. Worker descriptors already installed by spawn, including any
surviving original-number alias, keep their separate lifetime.

The issuer's token channel is separate from the worker evidence mapping. The
issuer and worker close inherited channel descriptors after mapping; neither
arguments nor environment carry tokens. The worker erases the full accepted token
buffer after the consumption decision, before the post-phase test seams, and on
ordinary departures after preparation; terminal publication follows that erasure.
Fatal termination or an interrupted native call need not reach worker cleanup.
The host independently clears the mapping before reply assembly. Token erasure
does not invoke native extension release; that remains a submitted action.
Consume/release markers precede calls; immutable result
publication is required before reporting a native return. Lifecycle actions
share the ordered action capacity but do not create validator queries.

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
Current wire contracts: request schema 5, response schema 24, controller envelope 8. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

The runner consumes `PWRunnerRunSpec`: the accepted request version, SBPL
source and optional parameters, and exactly one of `probe_plan` or `phases`.
An ordinary action always has a submitted query and attempt. Phase IDs are
unique and nonempty; step IDs are unique across the entire specimen. Codable types and
their `CodingKeys` define acceptance. Unknown fields, wrong types, unsupported
versions, unsupported attempt/filter names and ineffective combinations produce
`bad_request` with a bounded `request_failure`. Capacity admission is shared
between service handling and direct orchestration.

The optional `extensions` array declares a local token reference, target and
optional `authority` (`read` or `read_write`, defaulting to `read`). The fresh
issuer chooses the corresponding native read or read-write class from that
bounded value in its transient channel; callers cannot supply class strings.
An explicit phase action is either an ordinary pair or a `step_id` plus
`extension` operation. At most one declaration, consume and release are admitted;
release references the earlier consume handle. Actions may be omitted or placed
in separate phases. Token bytes, caller-selected classes, repeated lifecycle
actions and mixing exec with an extension declaration are refused.

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
| `extensions[]`, `extension_events[]` | Preparation/issuer/delivery observations and separately published consume/release results; [native evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence). Raw tokens are absent. |
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

Readers and encoders require the current response version. If ordinary reply
encoding fails, the service returns `runner_reporting_failed`, preserving
available observations and withholding comparisons. If that also fails,
`evidence_retained: false` marks the minimal reply. Full wire fields and reading
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
| `worker_executable_path` | string | Bundle-local `pw-probe-runner`; substitutes the worker spawn path. A nonexistent path can exercise `worker_spawn_failed`. |
| `worker_timeout_ms` | integer milliseconds | <!-- span limits.worker_sentinel_wait.value_unit -->120,000 milliseconds<!-- /span -->; changes the host sentinel allowance, leaving the worker's exec budget unchanged. |
| `validator_io_timeout_ms` | integer milliseconds | <!-- span limits.validator_io_wait.value_unit -->30,000 milliseconds<!-- /span -->; sets the proposed per-phase I/O deadline, capped by the remaining aggregate collection allowance. |
| `validator_total_timeout_ms` | integer milliseconds | Reduces the aggregate collection allowance, clamped to 1–<!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span --> across all phases. Later collections can become unavailable while attempts still run. |
| `issuer_executable_path` | string | Bundle-local `pw-extension-issuer`; substitutes its real launch path for extension experiments. |
| `validator_executable_path` | string | Bundle-local `sb_api_validator`; substitutes the validator spawn path after successful worker application. |
| `worker_post_apply_hang_ms` | integer milliseconds | Disabled when absent or nonpositive. Requests a native sleep after completed slots and before `done`; paired with a shorter sentinel allowance it can exercise timeout handling. |
| `worker_post_apply_kill_signal` | integer signal number | Disabled when absent or nonpositive. Requests self-signalling after completed slots and before `done`; observed fatal delivery can exercise `runner_failed`. |
| `worker_pre_ready_hang_ms` | integer milliseconds | Disabled when absent or nonpositive. Requests a native sleep after compilation/optional capture, before the ready byte; publication depends on the remaining host allowance. |
| `worker_kill_before_publish_slot` | integer slot index | Disabled when absent or negative. If the slot is reached, requests SIGKILL on the worker after dispatch returns and before its `completed` flag is stored. Dispatch can refuse without making a native attempt. Observed started progress with no published result does not recover an unpublished native return or identify a signal's sender or policy cause. |

Decoding accepts representable integers. The host floors deadline overrides in
[`timeoutMsForCWorker`](Sources/PWRunnerCore/CWorkerOrchestrator.swift) and
[`timeoutMsForValidator`](Sources/PWRunnerCore/CWorkerOrchestrator.swift).
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

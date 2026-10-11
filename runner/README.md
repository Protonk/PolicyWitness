# `runner/`

This directory contains the Swift XPC host and client for PolicyWitness.
The host accepts one specimen and stays unsandboxed. When execution proceeds,
a fresh C worker applies the specimen policy to itself. The host collects their
observations and the validator's predictions into one `PWRunnerRunResult`
reply, which the controller wraps in its output envelope.

[AGENTS.md](AGENTS.md) describes how to change and test the runner, including
the native helpers maintained under `controller/tools/`. The
[architecture tour](../docs/ARCHITECTURE.md) describes the process and evidence
boundaries across the application.

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
| Time and native shim | [MonotonicDeadline.swift](Sources/PWRunnerCore/MonotonicDeadline.swift): deadlines and policy-pipe delivery; [PWCWorkerShim/](Sources/PWCWorkerShim/): fixed-argument shared-memory opening and acquire/release helpers. |
| Request and path helpers | [ProbeRunner.swift](Sources/PWRunnerCore/ProbeRunner.swift): request meaning and prediction-exclusion definitions; [SandboxApply.swift](Sources/PWRunnerCore/SandboxApply.swift): policy hashing; [PathUtils.swift](Sources/PWRunnerCore/PathUtils.swift): planning and later host path observations. |
| Client and tests | [Clients/PWRunnerClient/main.swift](Clients/PWRunnerClient/main.swift): JSON-over-Data XPC client; [Tests/PWRunnerCoreTests/](Tests/PWRunnerCoreTests/): explicitly registered TestKit groups. |

The native [C worker](../controller/tools/pw_probe_runner/pw_probe_runner.c) and
[batch validator](../controller/tools/sb_api_validator/sb_api_validator.c) live
outside this directory. Meson embeds them as `pw-probe-runner` and
`sb_api_validator` in each service's `Contents/MacOS/`; the host resolves them
relative to its own bundle for both built-in and external runners. Only these
runner children call the sandbox APIs. The host's source and shipped imports
are checked by [source drift](../tests/suites/source_drift/README.md) and
[artifact inspection](../tests/suites/preflight/README.md).

## Run lifecycle

1. Caller authorization gates the connection. The host shares one terminal
   request claim across connections; another request receives `already_ran`.
   The claim precedes decoding, so a refused request also consumes the host.
   Only the claim owner schedules exit after its reply.
2. The service decodes and admits the request, validates meaning and plans
   queries before creating either child. The worker receives policy bytes on
   its input pipe and shares fixed-layout inputs/publications with the host.
3. The worker compiles and applies the policy, publishes application, then waits.
   After observing successful application and matching worker identity, the host
   collects eligible queries with `sb_api_validator --batch`. No eligible queries
   means no validator; failures before application can also prevent its launch.
4. Collection closes on every validator terminal path. The host releases the
   worker, which acknowledges release before attempting the plan. No later
   validator record joins this run's predictions.
5. The host gathers completed slots, partial evidence and independent child
   lifecycle observations, assembles the reply, then schedules its own exit.

Every validator query uses `SANDBOX_CHECK_NO_REPORT`, so predictions produce no
denial records. `comparison.order=query_first` requires eligible native records,
the full collection/release/acknowledgement chain and worker lifetime evidence;
the presence of a paired query alone is insufficient. The
[ordering contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#ordering-evidence-states)
defines the claims and withheld states.

Policy-transfer, readiness, sentinel, validator and cleanup allowances cover
different phases. A client timeout does not cancel the host, and a successful
termination request does not establish reaping. Some final waits can block;
there is no total lifecycle deadline. The
[limits inventory](../docs/LIMITS.md#execution-budgets) and
[host-observation contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#host-observations)
describe these bounds and remaining cleanup limitations.

## Specimen inputs

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 4, response schema 15, controller envelope 7. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

The runner consumes `PWRunnerRunSpec`: the accepted request version, SBPL
source and optional parameters, and an ordered probe plan. Codable types and
their `CodingKeys` define acceptance. Unknown fields, wrong types, unsupported
versions, unsupported attempt/filter names and ineffective combinations produce
`bad_request` with a bounded `request_failure`. Capacity admission is shared
between service handling and direct orchestration.

The controller resolves `policy.augments` and removes selection fields before
delivery. Direct XPC requests containing nonempty unresolved augments or
controller selection fields are refused. The [request grammar](../docs/REQUEST-GRAMMAR.md)
and [accepted input contract](../docs/CONTRACT.md#accepted-input-contract)
own the full rules; [augments/](augments/README.md) describes the shipped policy
fragment.

An optional compiled-object receipt captures the worker's compiler output before
application. The host exposes it only after checking successful application,
completion and the receipt's identity/integrity evidence. The
[receipt contract](../docs/PolicyWitness.md#compiled-object-receipt-opt-in)
defines its contents, sensitive-output handling and unavailable cases.

## Run result highlights

The host joins evidence without attributing every failed operation to the
sandbox or declaring prediction/enforcement agreement. Its principal records are:

| Record | Responsibility and contract |
| --- | --- |
| `runner_subprocess` | Worker publications and independent host observations; [worker evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract) and [disposition](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-disposition-record). Its PID is authoritative for worker correlation. |
| `validator_subprocess`, `validator_spawn_failure` | Observed validator execution, accepted records and collection faults, or a failed native launch. A failed launch creates no subprocess record; [receiver contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#admission-and-validatorcontroller-receiver-contract). |
| `steps[].sandbox_check`, `attempt`, `comparison` | Predictions, attempted-operation evidence, and their submitted-scope/order relations; [comparison contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#comparison-record). Later host path resolution is separately attributed. |
| `normalized_outcome`, `reporting_failure` | Classification of available observations and any reply-construction failure; [classification](../tests/FAILURE-PROPAGATION-CONTRACT.md#evidence-and-classification) and [reply failure](../tests/FAILURE-PROPAGATION-CONTRACT.md#reply-construction-failure). |

Native observations remain distinct from summaries: the query's `native_rc`
carries a native return, while attempt `rc` is PolicyWitness status.
`not_run_worker_died` means no completed attempt result, not proof an operation
never began. Missing subprocess records or lifecycle fields establish neither
successful execution nor cleanup.

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

| Key | Request type | Default and effective behavior |
| --- | --- | --- |
| `worker_executable_path` | string | Bundle-local `pw-probe-runner`; substitutes the worker spawn path. A nonexistent path can exercise `worker_spawn_failed`. |
| `worker_timeout_ms` | integer milliseconds | <!-- span limits.worker_sentinel_wait.value_unit -->120,000 milliseconds<!-- /span -->; changes the host sentinel allowance, leaving the worker's exec budget unchanged. |
| `validator_io_timeout_ms` | integer milliseconds | <!-- span limits.validator_io_wait.value_unit -->30,000 milliseconds<!-- /span -->; changes the validator I/O deadline and can outlast the worker's release wait. |
| `validator_executable_path` | string | Bundle-local `sb_api_validator`; substitutes the validator spawn path after successful worker application. |
| `worker_post_apply_hang_ms` | integer milliseconds | Disabled when absent or nonpositive. Requests a native sleep after completed slots and before `done`; paired with a shorter sentinel allowance it can exercise timeout handling. |
| `worker_post_apply_kill_signal` | integer signal number | Disabled when absent or nonpositive. Requests self-signalling after completed slots and before `done`; observed fatal delivery can exercise `runner_failed`. |
| `worker_pre_ready_hang_ms` | integer milliseconds | Disabled when absent or nonpositive. Requests a native sleep after compilation/optional capture, before the ready byte; publication depends on the remaining host allowance. |

Decoding accepts representable integers. The host floors deadline overrides in
[`timeoutMsForCWorker`](Sources/PWRunnerCore/CWorkerOrchestrator.swift) and
[`timeoutMsForValidator`](Sources/PWRunnerCore/CWorkerOrchestrator.swift).
It forwards only positive delay/signal values; the worker's
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

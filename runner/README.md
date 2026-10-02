# `runner/` (Swift runner: specimen-first sandbox witness)

This directory contains the Swift implementation of the **ephemeral sandbox runner** shipped inside `dist/PolicyWitness.app`.

PolicyWitness is **specimen-first**:

- The controller (`policy-witness`) starts a fresh XPC runner instance per specimen.
- The XPC host stays unsandboxed and spawns two short-lived children:
  - `pw-probe-runner` — the sandboxed C worker that applies the specimen
    policy (SBPL source + params) exactly once to itself and runs the
    probe plan's attempts.
  - `sb_api_validator --batch` — queries `sandbox_check` for each probe
    against the worker's PID.
- The host joins both children's outputs into a single `PWRunnerRunResult`
  envelope and replies. Because the host never applies the specimen
  policy, default-deny policies can't block the XPC reply path.

## Key files

SBPL policies can opt into a compiled-object receipt with
`capture_applied_profile` and a fresh `capture_nonce`. The worker captures before
apply into a bounded shared-memory region; the host joins successful application,
completion, PID, nonce and checksums before exposing `applied_profile`. The API
type lives in `PWRunnerAPI.swift` so the service and client share its wire shape.
See [Opt-in compiled-object receipt](../docs/PolicyWitness.md#opt-in-compiled-object-receipt)
for the sensitive-output contract and unavailable cases. The ABI layout suite
also constructs independent bounded objects for the C capture helper; Swift unit
controls pair selected-byte/input changes with ignored-padding/order changes.

The Swift driver tests honor `PW_APP_DIR` for separately built candidates;
without it they use the default distribution. Host and worker must implement the
same shared-memory ABI. A successful Swift compilation alone does not establish
that the selected worker binary matches that ABI.

The runner follows SwiftPM-convention layout: the core library sources
compiled into `PWRunner.xpc` live under `runner/Sources/PWRunnerCore/`,
each C shim under its own `runner/Sources/<Shim>/` (with `include/`), the
thin XPC client under `runner/Clients/PWRunnerClient/`, and the service
bundle scaffolding under `runner/Services/PWRunner/`.

- `Sources/PWRunnerCore/PWRunnerAPI.swift`
  - `PWRunnerProtocol` (`runSpecimen(Data) -> Data`)
  - Codable JSON types: `PWRunnerRunSpec`, `PWRunnerPolicySpec`, `PWRunnerProbeStep`, and the returned `PWRunnerRunResult`
- `Sources/PWRunnerCore/SandboxApply.swift`
  - `computePolicyHash`: the host's structural policy check (`bad_policy` for a
    missing source or wrong format) and `policy_sha256`. Compilation and
    application run only in the C worker.
- `Sources/PWRunnerCore/ProbeRunner.swift`
  - Query planning metadata: `knownFilterKinds`, `validateSandboxChecks` and
    `predictionUnavailableOpFilters`, the set of `(operation, filter_kind)`
    pairs the runner never predicts. Adding a pair requires empirical
    verification with `tests/suites/witness_contract/harness/verify_filter_id.sh`;
    the `source_drift` suite checks the set against the pairs listed in the
    user guide. The host never calls `sandbox_check`; the validator does.
- `Sources/PWRunnerCore/PathUtils.swift`
  - Path normalization for query planning and host path diagnostics.
- `Sources/PWCWorkerShim/`
  - The one C shim: the fixed-argument `shm_open` wrapper and the two
    `uint32_t` acquire-load/release-store helpers the host driver calls to
    drive `pw-probe-runner` (`PWCWorkerShim.h`). Spawning is Swift's.
- `Sources/PWRunnerCore/CWorker.swift`
  - Host-side driver for `pw-probe-runner`: shm_open + mmap + posix_spawn,
    sentinel polling, and the post-apply hook.
- `Sources/PWRunnerCore/ValidatorClient.swift`
  - Host-side driver for `sb_api_validator --batch`: concurrent
    stdin/stdout via `poll()` to avoid pipe deadlock, partial-evidence
    failure result.
- `Sources/PWRunnerCore/CWorkerOrchestrator.swift`
  - Joins the C worker and the validator child into a single
    `PWRunnerRunResult`. Owns probe-plan validation,
    `prediction_unavailable` query planning, outcome classification and the
    per-step comparison record.
- `Sources/PWRunnerCore/PWRunnerService.swift`
  - Orchestrates the host flow (decode → validate → drive C worker +
    validator → reply).
  - The host enforces caller authorization and computes `policy_sha256`. It
    never links, loads or calls libsandbox: the worker and the validator are
    the only processes that touch the native API. `source_drift` checks the
    host sources for bindings, calls and dynamic lookups, and the artifact
    inspection fails a shipped `PWRunner` whose undefined symbols include any
    `_sandbox_*` import.
- `Clients/PWRunnerClient/main.swift`
  - Builds `dist/PolicyWitness.app/Contents/MacOS/pw-runner-client`: a
    thin `NSXPCConnection` wrapper that forwards JSON bytes and prints
    the runner's JSON reply.
- `Services/PWRunner/`
  - `Info.plist`, `Entitlements.plist`, `main.swift` for the standard
    runner XPC service bundle. Debug-attach inspection goes through
    BYOXPC.

External to `runner/` but conceptually part of the runner:

- `controller/tools/pw_probe_runner/pw_probe_runner.c` (+ `pw_probe_runner_abi.h`)
  — the C worker that owns the post-apply syscall surface. Built once
  and embedded inside each XPC service bundle as
  `…/Contents/MacOS/pw-probe-runner` (not the app's top-level
  `Contents/MacOS/`) so built-in and BYOXPC runners both resolve the
  binary relative to their own bundle. Driven by `CWorker.swift`; the
  `runner_c_worker_harness` suite exercises it in isolation as a
  regression pin.
- `controller/tools/sb_api_validator/sb_api_validator.c` — the batch
  validator. Same bundle-local embedding story; driven by
  `ValidatorClient.swift`; wire contract pinned by
  `tests/suites/validator_batch_mode/`.

## Unit tests (SwiftPM)

`Package.swift` declares a test-only SwiftPM layout that mirrors the
source set build.sh ships in `PWRunner.xpc`. The `runner_unit` suite
runs the `PWRunnerCoreTests` executable and builds its required lifecycle fixture:

```sh
tests/run.sh --suite runner_unit --suite runner_c_worker_harness
```

The executable hand-rolls a small XCTest-shaped harness so the test
target works on Command Line Tools alone (full Xcode not required).
`PWRunnerCore` is built with `-enable-testing` so tests can
`@testable import` it. Production builds keep going through `build.sh`;
SwiftPM's `.build/` tree is gitignored.

See `runner/AGENTS.md` → "Swift runner unit tests (SwiftPM)" for the
contract, when to reach for a unit test vs an e2e suite, and how to add a new
test file.

## Test seam: `_test_overrides`

The request JSON accepts an optional `_test_overrides` block that
re-routes narrow boundaries through real production code so the test
suite can reach failure outcomes (`worker_spawn_failed`,
`validator_spawn_failed`, `runner_timeout`) without stubbing returns.
Every honored override is mirrored back into
`data.runner_result.test_overrides`; production runs leave that field
unset.

| Key | Type | Default | Re-routed boundary | Outcome it lets you reach |
| --- | --- | --- | --- | --- |
| `worker_executable_path` | string | bundle-local `pw-probe-runner` | `posix_spawn(path, ...)` inside `CWorker.spawn` | `worker_spawn_failed` |
| `worker_timeout_ms` | integer (ms, floored at 50) | 120000 | Host-side sentinel deadline in `CWorker.run`; the C worker's exec attempt budget stays at its production value | `runner_timeout` |
| `validator_io_timeout_ms` | integer (ms, floored at 50; no ceiling) | 30000 | Monotonic I/O deadline in `ValidatorClient.runValidator`; may intentionally exceed the worker release budget | `validator_no_reply` or earlier worker failure |
| `validator_executable_path` | string | bundle-local `sb_api_validator` | `posix_spawn(path, ...)` inside `ValidatorClient.runValidator` | `validator_spawn_failed` |
| `worker_post_apply_hang_ms` | integer (ms, 0..60000) | 0 (disabled) | Passed as `--post-apply-hang-ms` to `pw-probe-runner`; the C worker `nanosleep`s for N ms after slot results are durable but before flipping `done`, pushing the host past its sentinel deadline | `runner_timeout` |
| `worker_post_apply_kill_signal` | integer (signal, 0..31) | 0 (disabled) | Passed as `--post-apply-kill-signal` to `pw-probe-runner`; the C worker `kill(getpid(), N)`s itself after `applied` but before `done`, so the host observes a signal with `done` unset; no policy cause follows | `runner_failed` |
| `worker_pre_ready_hang_ms` | integer (ms, 0..60000) | 0 (disabled) | Passed as `--pre-ready-hang-ms` to `pw-probe-runner`; the C worker sleeps after compilation/optional capture and before the ready byte. A sufficient sentinel budget lets it survive the closed ready pipe; a shorter budget expires before publication | `ok` with sufficient budget; `runner_timeout` with the pre-apply witness budget |

This table is the only documented list of keys. The `source_drift` suite
checks it against the fields of `PWRunnerTestOverrides` in
`Sources/PWRunnerCore/PWRunnerAPI.swift`, so a key added to one without the
other fails the default battery.

See `runner/AGENTS.md` → "Testing `normalized_outcome` failure paths via
`_test_overrides`" for the full contract, the four-assertion test
recipe, and the rules for adding a new override.

## Specimen inputs

The runner consumes a `PWRunnerRunSpec` which contains:

- `policy`: `sbpl` source (with optional `params` and `augments`)
- `probe_plan`: ordered probe steps (sandbox_check + attempt)

`policy.augments` is resolved upstream by the controller (the runner
itself is augment-agnostic — by the time a request reaches
`PWRunnerService.runSpecimen`, the field has been stripped and any
named augment contents have been spliced onto `policy.sbpl_source`).
See docs/PolicyWitness.md → Augments for the wire surface and the
single shipped augment (`exec_baseline` — three allows that let a
libSystem-dynamic helper spawn under `(deny default)`).

## Run result highlights

Top-level fields:

- `pid` names the C worker when `runner_subprocess` exists. Correlation uses
  only `runner_subprocess.pid`, never a fallback host/client PID.
- `runner_subprocess` carries the worker PID, exit/signal status, partial-step
  flag, worker publications and independent host lifecycle observations.
  Outcome precedence is host admission failure, published worker failure,
  host transfer failure, invalid or imprecise publication, observed sentinel
  deadline, other worker/reporting/process failure, validator failure, then `ok`. A recovered EINTR alone is not failure. The authoritative
  table is [the failure contract](../tests/FAILURE-PROPAGATION-CONTRACT.md).
  Imprecise published failures, incomplete reports, abnormal/unconfirmed exits and
  cleanup faults use `runner_failed`; cause may remain unknown. Deadline expiry
  uses `runner_timeout` even after voluntary grace exit. A cleanup request alone
  is not a timeout. `runner_sandbox_denied` and `sandbox_apply_failed` are
  recognized constants that no producer emits; specific native failure
  evidence lives under `runner_failed`.
- `validator_subprocess` carries the validator child's process observations,
  accepted records, expected IDs, association issues, byte counts, and independent
  I/O/decode faults, or is `null` when no validator
  ran (every probe was in the prediction-unavailable set, or
  spawning the validator failed).
- `validator_spawn_failure` retains a failed native validator launch independently
  of the summary: `origin: runner_host`, `operation: posix_spawn`,
  `executable_path`, the numeric `return_code`, and a descriptive `diagnostic`.
  The code is the direct return, not ambient errno. Every nonzero return is a
  failure, including unfamiliar codes; diagnostic wording never selects the
  outcome. There is no validator subprocess on this path. The record is
  optional; absence does not establish successful spawning.

The host also writes `runner_subprocess.ready_byte_received`, `done_observed`,
`poll_stop_reason`, `exit_requested`, `termination_request`, `reaped`, and
`wait_errors`. Polling stops for `done`, `child_reaped`, `sentinel_deadline`, or
`wait_error`, or `policy_write_error`; later cleanup preserves that reason.
`done_observed` and completed slots use the final acquire snapshot after cleanup. A termination request records
the signal and `kill` return, with errno only on failure. Exit code and signal
are populated only after `waitpid` returned the child's PID. If reaping is
unconfirmed, both are absent/null even when the termination request succeeded.
Wait errors retain their phase, return and errno, including recovered EINTR.
Missing booleans mean unknown.

The driver allows two EINTR retries across all wait phases. A terminal wait error
ends that phase; ECHILD stops further waits and signals to that PID. Failed kill
permits only a nonblocking final wait. An unreaped child may remain. Successful
kill retains the blocking final wait, so this is no global lifecycle timeout.
Readiness, sentinel and exit-grace budgets are unchanged. Authoritative field
validity and encoding are documented in `PWRunnerAPI.swift`. Policy-write errors
retain partial subprocess evidence and independent transfer observations.

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 3, response schema 13, worker ABI 7, controller envelope 5. Each number is a separate contract. `docs/contract.json` owns all four, and generated copies carry them into code and documents.
<!-- END GENERATED CONTRACT VERSIONS -->

Readers accept exactly the current response schema; the Swift decoder and
encoder refuse another version with an `unsupported` diagnostic. Optional
subprocess objects are omitted or null when absent.

The reply boundary converts encoding failures to `runner_reporting_failed`
with a `reporting_failure` diagnostic and the original execution summary.
It retains queries, attempts and subprocess observations and omits all
comparisons. If that degraded response also cannot be encoded,
`evidence_retained: false` explicitly marks a minimal reply without child
evidence. The [reply failure contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#reply-construction-failure)
defines this exception; ordinary result encoding still rejects invalid claims.

Per-step fields under `steps[]`:

- `not_run_worker_died` is the attempt-outcome spelling for no completed
  result, not proof that an operation never began. Errno stays null when no
  result supports it. `attempt.lifecycle` distinguishes
  `started_without_result`, `not_reached`, `unsupported`, `unresolved` and
  `conflicting` from `completed`, projecting the per-step claims of
  `runner_subprocess.disposition`, the host's canonical lifecycle account
  (tests/FAILURE-PROPAGATION-CONTRACT.md, "Worker disposition record"). The
  subprocess also records `cleanup_trigger`, `grace_end` and `collection_basis`.

- `sandbox_check` reports the original `filter_value` (the exact string passed
  to the check), `pid`, `operation`, `filter_kind`, `filter_type_id`,
  `result_source`, `native_rc`, and `errno`/`error` when the check call fails;
  `missing_reason` says why no answer exists.
- `attempt` reports `rc` (PW attempt status), `errno`, `outcome`, `error`,
  `result_source`, `missing_reason` when no result exists, and `lifecycle`.
  `requested_path` echoes the attempt target for every attempt kind;
  `observed_path` is the worker's `F_GETPATH` observation of a successful open
  and `null` otherwise; `path_diagnostics` is the host's after-orchestration
  resolution of a file or exec target. The attempt channel carries no native
  return.
- `attempt.requested_kind` and `requested_action` retain submitted intent.
- `comparison.order` reports `query_first` only for eligible native records with a complete collection/release/acknowledgement chain and worker lifetime evidence; all others are `unestablished`.
- `runner_subprocess.ordering` retains host collection/release, worker acknowledgement, `worker_lifetime_established`, validator disposition and protocol violations. Collection closure releases attempts after every validator terminal path, including unconfirmed cleanup. No later record joins predictions.
- `comparison` carries `observation`, `observation_basis`,
  `operation_relation`, `target_relation`, `order` and `limitations`: the
  attempt channel's classification, the submitted-scope relations, the order
  the host established and the planner's exclusion or the attempt's lifecycle
  state. The encoder rejects any limitation outside that vocabulary and any
  `query_first` claim without its full chain. The record never says whether
  the channels agree; the query's own answer stays in `sandbox_check`.
  Exec/spawn maps to the native `process-exec*` query for target execution
  admission only. A spawned child's later failure does not erase the
  successful spawn. See the
  [comparison record](../tests/FAILURE-PROPAGATION-CONTRACT.md#comparison-record).
- `sandbox_check.path_diagnostics` records `observer="runner_host"` and
  `phase="after_orchestration"`; later host resolution is not validator evidence.

## Entitlements and sandboxing (important distinction)

The standard built-in runner ships with minimal entitlements. External
(BYOXPC) runners can carry additional hardened-runtime exceptions for
inspection and controlled extensibility (debug attach / dynamic loading /
dyld env / executable memory). These do **not** make sandbox policy “dynamic”.

## Caller authorization

A runner can require a signed caller before accepting XPC connections. The check
is controlled via Info.plist keys:

- `PWRunnerRequireSignedCaller` (bool)
- `PWRunnerAllowedIdentifiers` (optional array of code signing identifiers)

When enabled, the runner compares the caller’s Team ID to its own Team ID and
optionally enforces the allowlist. The shipped `PWRunner.xpc` sets
`PWRunnerRequireSignedCaller`, so a BYOXPC runner made by copying that template
(the documented recipe) **inherits the check** — it is not built-in-only in
practice. That carries a signing consequence:

- Sign the runner with a **Developer ID whose Team ID matches the caller**
  (`pw-runner-client`). An **ad-hoc** runner has no Team ID, so the Team-ID
  comparison fails and every connection is rejected with `NSXPCConnectionInvalid`
  (surfaced as `xpc_error`).
- For an **ad-hoc / local** runner, remove `PWRunnerRequireSignedCaller` and
  `PWRunnerAllowedIdentifiers` from the copied bundle's Info.plist before signing;
  the runner then accepts any caller (covered by
  `tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh`).

Sandbox policy variation is driven by the specimen itself:

- the controller supplies SBPL,
- `pw-probe-runner` applies it once to itself before running probes,
- the runner's witness pairs the attempt result with the validator's
  `sandbox_check` answer for each probe and records how the two submitted
  scopes relate in `steps[].comparison`.

## External runner services

PolicyWitness can target **external runner services** when entitlements are
required. An external runner is the same PWRunner implementation, but signed
with user-selected entitlements and registered with launchd as a **BYOXPC**
runner: a signed `.xpc` bundle, addressed by `CFBundleIdentifier`.

Invariants:

- The protocol is the built-in runner's (`PWRunnerProtocol` JSON-over-Data).
- One specimen -> one runner process; the runner applies the sandbox once and exits.
- The reply schema is the built-in runner's; the controller records runner provenance in `data.specimen.runner_provenance`.

The controller provides a `policy-witness runner` manager to install/register
these services and to enforce entitlements supersets before dispatch.

## Sandboxed automation harnesses

Some automation and agent harnesses run commands under a macOS sandbox. Inside
one, XPC lookup of the runner can be refused (`NSCocoaErrorDomain` code 4099,
or error 159 “Sandbox restriction”), so no runner launches; the unified log
tool can refuse to run (`log: Cannot run while sandboxed`), so deny evidence
cannot be captured; and `codesign --verify` can report “invalid signature (code
or signature have been modified)” for an unchanged, validly signed app. These
refusals can be environment constraints. Request escalation and rerun the same
command once outside the automation sandbox against unchanged artifact bytes.
Treat a signature failure as environmental only after the unsandboxed check
passes; debug any failure that remains.

The name “nested sandbox” fits: the harness's sandbox sits outside the one the
worker would apply to itself, and it wins first, at XPC lookup, before any code
in this directory runs. In the envelope the refusal is `normalized_outcome:
"xpc_error"` with `error` carrying the domain, code and message, empty `steps`,
and no `runner_subprocess`, because no host ran. The controller then runs
`sbpl-check` as a fallback and records it in `data.policy_check`, so a
`compiled: true` there says only that the policy compiles; it says
nothing about the worker. Nothing here produced that outcome and nothing here
can fix it. The other symptom is the controller's, not the runner's: if the
runner does launch but `sandbox_log_capture.capture_status` is `blocked` with
`blocked_reason: "Cannot run while sandboxed"`, the run's execution status and
cause are unchanged and only log correlation is unavailable. Pass
`--no-log-capture` to take that variable out while you work on the runner.

## Evidence contract pointers

The worker ABI places a pre-touched progress/failure header and a 4,096-byte text
region after the capture bytes. The release/acquire
[field contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract)
defines milestones, native results, open numeric codes, and text availability.
`runner_subprocess.worker_evidence` carries these publications through the normal
reply. Policy-write errors retain partial output and host byte/errno evidence in
`policy_transfer_error`; FD-scoped SIGPIPE suppression and close-on-exec source
pipe descriptors make closed-input failure observable. An undrained open pipe
still blocks before sentinel polling. Early stderr capture is not implemented.

Host admission refusals share `admission_failure` with field, actual/maximum and
`utf8_bytes`, `items` or `nul_bytes` units. Service and direct orchestration use
the same check before semantic validation, path planning or process work. It
covers shared-memory bounds, host query fields, top-level metadata and the
three test-override paths. Native C-string fields forbid embedded NUL; other
valid Unicode and control characters survive transport. The driver retains its
local ABI checks. A shared refusal builder independently sanitizes every echoed
metadata field, including simultaneous violations. Decoder errors carry bounded
category/path diagnostics. Both child drivers share the finite
`ChildProcessState` wait/termination observer; parsed validator records survive
failed cleanup. Validator replies are byte-framed, strictly decoded, structurally
validated, then associated by unique requested ID. Allow/deny records require
native integer results. Null-ID and unfamiliar valid diagnostics remain at run
scope; missing/duplicate/unexpected replies cannot be hidden by record count.
See the [field contract](../tests/FAILURE-PROPAGATION-CONTRACT.md) for capacities, acceptance
rules and remaining observation/liveness limitations.


`steps[].sandbox_check.pid` is the spawned worker PID, or explicit null when no
worker exists. It never substitutes the host PID. Typed readers must accept
null. Request schema and worker ABI are separate contracts.

The query channel's `native_rc` is authoritative for native returns. A received
diagnostic without a native return retains `result_source="validator"`,
`native_rc=null` and `rc=-1`; this is not a synthetic validator record or a
claimed native failure. Missing replies use synthetic `rc=0`, `outcome="error"`
with a missing reason. `outcome="error"` alone does not identify a native call
failure.

See [the query and receiver contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#query-and-receiver-evidence)
for immutable query planning, query association, independent pipe collection,
and exact-byte controller capture semantics.

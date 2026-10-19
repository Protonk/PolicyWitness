# Prepare executables before testing and establish ordering through observations

## Problem and intended result

Fresh executable startup can consume the short allowance that a test uses to
arrange a sequence. In `runner_unit`, the over-budget validator case asks a
fixture worker to expire after 50 ms and gives a separate validator 150 ms to
publish a record and time out. It needs that record to test preservation of
predictions after worker expiry. A validator delayed before publishing can
therefore fail the test without exercising its intended condition.

Make successful executable preparation an explicit prerequisite, then replace
these timing arrangements with observed readiness, test-owned gates and
controlled clock samples. A failed preparation must stop at preparation. An
ordering failure must identify the violated sequence or missing observation.
Neither is repaired by automatically repeating a specimen or a suite.

Implement this in two phases. Phase 1 makes fixture preparation mandatory and
executes the final signed shipped binaries through harmless entry points before
packaging. Phase 2 is an implementation sequence: source inspection establishes
that the selected assertions can use real worker/validator processes and real
transport while controlling when the relevant conditions occur. A separate
open-ended investigation is not required. The first phase-2 checkpoint must
demonstrate that design before converting the remaining selected cases.

The implementation baseline is commit `3271e29`. Review covered source and
contracts, without builds, test execution or measurements of Gatekeeper. The
reported approximately 200 ms startup cost is motivation, not an acceptance
threshold or an established cause for any particular failure.

## Findings and scope

| Location | Finding and consequence |
| --- | --- |
| [Lifecycle builder](tests/fixtures/worker_lifecycle/build.sh), final Python block | Already executes the base fixture and a glob of companions. It prints statuses, including `timeout`, without failing on them. A failed preparation can reach Swift tests. The glob also confuses executable inventory with any adjacent files. |
| [Unit wrapper](tests/suites/runner_unit/run.sh) | Fixture construction precedes `swift run`; `test_build_fixture` propagates builder failure. This is the existing admission point to strengthen. |
| [Ordering tests](runner/Tests/PWRunnerCoreTests/OrderingTests.swift), `validator collection may outlast the worker budget without reviving attempts` | The 150 ms case uses the lifecycle worker and `.validator`, not the shipped worker/validator. Preparing the app alone cannot fix its fixture startup. The adjacent 50 ms partial-prediction case has the same record-before-deadline assumption. |
| [Validator driver](runner/Sources/PWRunnerCore/ValidatorClient.swift), `runValidator` | Starts its I/O deadline after successful spawn, before duplex collection. Startup after spawn can consume that allowance. It retains bytes, closes the collection pipe, then decodes and performs child cleanup. Child `fflush` alone does not establish that this host retained a complete record. |
| [Deadline helper](runner/Sources/PWRunnerCore/MonotonicDeadline.swift) | Already accepts a clock closure. The collector does not expose that closure through its internal driver overload. |
| [Orchestrator](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), internal `run` overload | Already permits native validator spawn and child-process substitutions. Its aggregate collection accounting calls `MonotonicDeadline.now` directly. Narrow internal clock/read substitutions can preserve the actual translation, transport, classification and assembly. |
| [Worker driver](runner/Sources/PWRunnerCore/CWorker.swift), phase callback and guarded release | Calls collection synchronously and rechecks worker completion and ownership before publishing release. Production workers exit after terminal publication; the host reconciles acknowledgements after confirmed reap while preserving ownership requirements. The callback interval can be held until independent fixture observations establish expiry. |
| [Lifecycle worker](tests/fixtures/worker_lifecycle/worker.c) and [validator](tests/fixtures/worker_lifecycle/validator.c) | Already have independent waiting/acknowledgement/attempt/expiry receipts and a late-write gate that observes `EPIPE`. Extend this equipment rather than fabricating a production reply. |
| [Build](build.sh), final signing, verification and packaging | Enforces required executable inventories and thin arm64 macOS outputs, checks the worker's identity before signing and verifies signatures afterward, but does not execute the final signed inventory. Preserve the output checks through packaging when adding preparation; a pre-signing execution is not a receipt for the final signed executable. |
| [Host entry point](runner/Services/PWRunner/main.swift) and [listener selection](runner/Sources/PWRunnerCore/PWRunnerListener.swift) | Direct execution currently constructs a listener; unrecognized arguments fall back to the XPC-service launch path. A blanket no-argument or `--help` invocation is unsafe until a harmless exit path is implemented. |

Phase 2 covers the release-gate control, the two short validator-deadline
ordering cases, collection-closure/late-output controls in `OrderingTests`, and
the aggregate-exhaustion and M08 cases in
[PhaseProtocolTests](runner/Tests/PWRunnerCoreTests/PhaseProtocolTests.swift).
These share the record-before-cutoff issue and the collector being changed.

Keep dedicated timing coverage: `CWorkerClockTests`, native
`runner_c_worker_harness/clock_arithmetic` and `proceed_precedence`, exec deadline
controls, and genuine live deadline observations. This plan does not redesign
production allowances or clock domains, change what startup time is charged to,
or promise that every timing-sensitive test in the repository becomes invariant
under arbitrary machine load. The phase-2 sample controls in
[WorkerClockTests](runner/Tests/PWRunnerCoreTests/WorkerClockTests.swift) and
[clock_failure.c](tests/fixtures/worker_lifecycle/clock_failure.c) already use
`ready`, `collection-open` and `injected` receipts with independent watchdogs.
Their handshake establishes ordering under prompt and delayed authorization.
Preserve these controls outside this conversion.

BYOXPC collisions, installation, host retirement and retries are outside this
plan. Preparation must not install a runner, connect to XPC, apply a specimen,
read unified logs, issue extension tokens or modify OS security settings.

## Phase 1: make preparation a required stage

### 1. Implement one bounded execution-preparation helper

Add `tests/lib/prepare_executables.py`, shared by the lifecycle builder and the
signed build. Give it two explicit inventories: lifecycle outputs selected by
their builder, and shipped outputs selected by the full/partial build variant.
Use named recipes with fixed arguments and expected exit statuses. Do not find
executables with a glob or silently omit an absent declared output.

Reuse the bounded subprocess supervision in
[build_provenance.py](tests/lib/build_provenance.py): `probe`, `terminate_group`
and `group_gone`. Keep the existing provenance probe's success/failure semantics.
The preparation adapter may accept a normally completed `nonzero_exit` result
only when its positive status is the recipe's expected status, and accept an
`empty_output` result only for an explicitly output-free, expected-zero recipe.
It must never reinterpret timeout, overflow, signal termination, launch failure
or uncertain cleanup as successful preparation. No general supervisor rewrite
or provenance schema change is needed.

For each execution:

1. Admit the expected regular executable and record its absolute path, arguments
   and SHA-256. Run that path in a fresh process with stdin at EOF, both output
   streams captured within bounds, and all nonstandard descriptors closed.
2. Allow 30 seconds for preparation, independent of specimen/test allowances.
   Keep the supervisor's bounded termination and reap procedure. Record elapsed
   time diagnostically; there is no fast-enough-to-be-warm assertion.
3. Require the recipe's exit status and any stated output check. Record actual
   status, stream sizes, bounded failure metadata and cleanup observation. Keep
   the supervisor's existing rule against storing raw failed-tool output. Reject
   changed executable bytes between admission and completion.
4. Persist a receipt on success or failure. Stop the caller on failure; do not
   retry execution or continue into the timing-sensitive consumer. A receipt
   states that an execution completed, not that macOS will cache it indefinitely.

Keep preparation receipts outside executable inventories and sealed bundles.
Lifecycle receipts belong beside the fixture under a distinct non-executable
name. Build receipts belong in a fresh `DIST_DIR/preparation/<attempt>/`
directory, bound to the actual final executable hashes. Preserve failed receipts;
do not introduce a cached receipt that authorizes skipping preparation after a
rebuild, copy or re-signing. Build preparation runs once per build invocation.

### 2. Replace the lifecycle builder's advisory warm-up

Have `tests/fixtures/worker_lifecycle/build.sh` accumulate the precise outputs
it actually builds and pass those recipes to the helper. The current recipes
can be settled from source without a benchmark:

| Fixture | Invocation | Expected normal exit |
| --- | --- | --- |
| Base worker and `.identity-mismatch` | No arguments, FD 3 closed | 90, before mapping or reading policy |
| `.validator` | No arguments, stdin at EOF | 90, before any verdict |
| `.issuer` | No arguments, FD 3 closed | 92, before channel mapping or issuance |
| `.worker-limits` | No arguments | 0, with its existing default-value output |
| Production-main companions: apply/parameter failures, map/read failures and every clock companion | `--version` | 0, with the worker identity/version line; this exits before their controlled native failures |

The issuer's setup failure status 90 remains a preparation failure. The builder
must add every new companion to this inventory at its compilation site. Update
the [fixture README](tests/fixtures/worker_lifecycle/README.md), fixture catalog
and [runner_unit README](tests/suites/runner_unit/README.md) to describe the
prerequisite and receipt, removing the claim that warm-up asserts nothing.

Keep `runner_unit/run.sh` using `test_build_fixture`; a failed helper must make
the builder nonzero, preserve its log and receipt, and prevent `swift run` and
reader replay. Verify the same behavior for direct fixture-builder callers,
including the ordering mutation equipment. Do not require a successful fixture
preparation to imply that the fixture's later behavioral scenarios will pass.

### 3. Exercise final signed shipped executables before packaging

Add an exact standalone `PWRunner --help` invocation that prints usage and exits
zero before constructing either listener. Extend the pure listener/entry-mode
selection and its `ListenerConfigTests` coverage together. Preserve existing
no-argument and `--mach-service <name>` behavior, including current fallback
behavior for other argument lists. No specimen field or XPC method is added.
Describe the helper entry point in `runner/README.md`.

After app sealing, deep verification, signer checks and the final standalone
observer signing, add a required preparation banner/helper call before guide
staging and ZIP creation. Preserve the existing output-target checks for Cargo
and native outputs, the assembled app, the standalone observer and packaging.
Use the final destination paths:

| Shipped executable | Harmless invocation | Expected exit |
| --- | --- | --- |
| `Contents/MacOS/policy-witness` | `--version`, validate the version envelope | 0 |
| `Contents/MacOS/pw-runner-client` | `run --help` | 0 |
| Embedded `sandbox-log-observer` | `--help` | 0 |
| Embedded `sbpl-check` | `--help` | 0 |
| Each service's `PWRunner` | New standalone `--help` | 0 |
| Each service's `pw-probe-runner` | `--version`, check generated identity | 0 |
| Each service's `sb_api_validator` | No arguments; usage refusal before querying a PID | 2 |
| Each service's `pw-extension-issuer` | No arguments, FD 3 closed | 92 |
| Standalone observer at `${SANDBOX_LOG_OBSERVER_BIN}` (`controller/target/aarch64-apple-darwin/release/sandbox-log-observer`) | `--help`, after its separate signing | 0 |

In `BUILD_XPC=0`, require only the executables actually shipped in that variant
and the standalone observer. The native worker/validator built as intermediates
are not embedded in that variant. Do not launch a full XPC service as a
substitute for the host's harmless entry point.

Record the app's file inventory before and after preparation and require equal
content hashes, then verify the sealed app again before guide staging. Retain
the final packaging output-target check immediately before ZIP creation,
including its required-output inventory. Do not rewrite embedded evidence to
add a post-seal observation. Preparation receipts are local execution
observations; signatures, notarization and release acceptance keep their separate
meanings. Downloaded/copied/re-signed artifacts can be cold again.

Update these dependencies in the same step:

- `build.sh`, `docs/build.json`, and the build generator's step, invocation and
  refusal controls; run `docs/generate_build.py` to regenerate the account and
  diagrams. The new preparation refusal must be represented in the manifest.
- `docs/BUILD.md` narrative and `README.md` build description; `dist/README.md`
  for the new local receipt directory. Explain that a failed late build may leave
  a valid sealed app but cannot produce this invocation's completed package.
- Build input admission/inventory checks for the new helper. Regenerate worker
  identity before every checkpoint build: `build.sh` and runner sources are
  digest inputs even though this work does not change the ABI layout.
- `tests/suites/preflight` and `tests/suites/source_drift` build controls, described
  below. Review architecture citations for the direct help exit; it does not
  create a new specimen process or channel. Change generated architecture inputs
  only if the account actually needs to describe a changed boundary.

### Phase-1 checks and completion condition

Register `shell_helpers/executable_preparation` as a default, app-independent
case with Python and clang prerequisites. Exercise actual child processes and
the real helper with: expected zero/nonzero exits; unexpected zero/nonzero;
signal exit; missing executable; output overflow; a held child that exceeds the
helper allowance; a descendant retaining a pipe; and a control observing closed
FD 3. Use shorter allowances through the helper's Python test boundary for fault
controls, retaining the production 30-second allowance. Observe eventual child
cleanup independently. A stale adjacent receipt/text file must never be executed.

The wrapper controls must prove a preparation failure prevents the later Swift
command, using a marker from that command, and retains the specific failure.
A positive sibling must reach that marker. Add a rejection control that disables
failure propagation and require the wrapper oracle to catch it.

Extend the existing opt-in `preflight/build_guard_controls` and
`preflight/build_refusal_controls` rather than crediting a helper unit check as
build integration. In a disposable checkout, make one legitimately signed helper
return an unexpected status or hang only on its preparation invocation. Keep
identity/version, required-output inventories, thin arm64 macOS checks and earlier
build guards valid so the intended boundary is reached. Observe that verification
and signing precede preparation, and that preparation failure prevents guide/ZIP
completion. Successful full and partial siblings must prepare exactly their
inventories. A control removing the build's helper call must fail the independent
receipt/inventory oracle. Move the existing packaging fault injections in
[build_refusals.py](tests/suites/preflight/opt_in/build_refusals.py) past preparation
and the final seal verification so they still exercise the packaging output-target
guard. Preserve real signing receipts and app hashes; do not tamper with the
inspected source app.

Phase 1 is complete when both the fixture wrapper and signed build enforce the
prerequisite, final signed paths have successful receipts, failure controls stop
at the intended stage, and generated build/identity checks agree. Existing tests
remain meaningful if they fail after this stage; preparation is not permission
to dismiss or retry their failures.

## Phase 2: replace scheduling assumptions with causal controls

### 4. Add the narrow collector substitutions and prove the main sequence

Expose a small internal collector-call value through the existing
`runValidator` overload: a clock closure and a read closure, defaulting to
`MonotonicDeadline.now` and `Darwin.read`. Route the existing deadline through
that clock and the existing stdout read through that read closure. The test
read closure must delegate to the real syscall unchanged, preserve its return
and errno, and copy only the actual positive-length bytes into bounded test
observation storage. Leave native polling, writes, retained-byte bounds,
decoding, collection closure and cleanup in production code.

Thread per-phase collector calls through `CWorkerOrchestrator`'s existing
internal overload. Also supply an internal aggregate-collection clock closure,
defaulting to `MonotonicDeadline.now`, for its start/planning/end samples. Tests
may share an explicitly controlled clock between those two boundaries; production
continues to use its existing clock and starts/debits budgets at the same points.
Preserve production terminal exit, the guarded release and acknowledgement
reconciliation after confirmed reap. Do not expose these substitutions through
request JSON or add an outcome-forcing override.

Extend the independent lifecycle equipment with a gate-driven expiry mode.
It publishes arrival and a `waiting` receipt, waits for its own `.expire` gate,
then publishes the same fixture expiry evidence and `done`, followed by an
`expired` receipt. Keep this explicitly labelled as a constructed worker
publication for host interpretation, not a measurement of a native 50 ms wait.
Keep the ordinary release/acknowledgement/action path operative until expiry;
the gate controls the expiry condition only. An early host release must still
produce observable early acknowledgement/action, and expiry remains terminal
even if release is stored afterward. The ordinary `proceed_wait` mode supports
the successful sibling. Add a validator mode that can announce readiness and
wait for an `.emit` gate before writing its real complete record and holding
stdout open. Carry unique gate nonces through the existing fixture input tokens
and validator operation token, with short owned paths and no global environment
switch or production resource acquisition.

For the replacement over-budget assertion, establish this sequence:

1. The production host observes worker arrival and starts its real validator
   collection. The worker remains unreleased; the test observes its `waiting`
   receipt. Use a unique absent file target for the worker's possible action.
2. Let the validator write through its actual stdout pipe. The read wrapper
   observes the complete expected NDJSON line across arbitrary read fragments;
   identifying a child-side ready or flush receipt is insufficient. The collector
   retains those real bytes through its unchanged read path.
3. On the next collector clock sample, after that read has returned and retention
   has occurred, open the worker's expiry gate and wait for the independent
   `expired` receipt. Then advance the controlled clock to the collector's
   deadline. The clock stays within budget until the required observations exist.
4. The collector closes through its actual deadline branch, retains the real
   record, and returns to the host. The host's existing completion and ownership
   rechecks must withhold release. Assert no acknowledgement or completed attempt,
   absence of the independent file effect, retained prediction, worker-failure
   precedence, `comparison.order == unestablished`, and successful full reply encoding.
5. A sibling without worker expiry must close collection at the controlled
   deadline, release and acknowledge, create the file, and retain the partial
   prediction and its eligible ordering chain.

Make all gates fail within an independent real monotonic watchdog. Fixture
alarms and watchdog intervention are equipment failures, never evidence of a
PolicyWitness deadline. On every exception, unblock gates as necessary and
terminate/reap only children the case owns. Account for early spawn/read/parse
failures without waiting forever for a receipt that cannot arrive. Keep process
cleanup clocks separate from the frozen collection clock.

Before wider conversion, run a deterministic regression variant delaying the
validator's record by 500 ms after readiness. This delay is a test perturbation,
not the ordering oracle and not an emulation of Gatekeeper internals. The old
150 ms arrangement must fail for its missing record; the new sequence must pass
with actual retained bytes, expiry and absent effect. Also run the new sequence
without the delay. Do not credit a passing case whose record was synthesized.

If this checkpoint cannot retain real bytes and traverse the original closure
and release checks, stop phase-2 expansion and retain its failed evidence.
Reassess the proposed internal boundary; do not widen production deadlines or
replace replies with constructed successes. Phase 1 remains independently useful.

### 5. Convert the related ordering assertions

Use explicit case ownership rather than a global test clock or shared gate.

| Existing assertion | Replacement and preserved observation |
| --- | --- |
| `runOrderingGateControl`: 100 ms delayed semaphore before checking the held receipt | Add a fixture checkpoint request/receipt while the callback is held. The child must perform an acquire observation of release and report it before the callback returns. Wait for either that checkpoint or early acknowledgement/attempt receipts, rejecting the latter immediately. Use the fixture's file-create action and require its actual effect after callback return. This gives the child an observed opportunity to run without assuming it ran during a sleep. |
| `proceed_wait_expire` and the over-budget case | Use the explicit expiry gate and wait for its publication receipt before ending collection. Keep worker failure, withheld release and retained evidence assertions. |
| `validator_io_timeout_ms returns partial prediction...` | Retain the requested override and echo checks. Advance the collector clock only after the real record is retained, then observe release and the file effect. |
| `surviving validator cannot publish after collection closes...` | Retain a record, expire collection through controlled time, keep the real failed-kill observation, and open the late-write gate only after return. Require the child's native `EPIPE` receipt and the worker's effect. |
| EOF-with-live-validator cleanup variants | Use their real EOF and explicit child hold, with a generous ordinary collection allowance. No short I/O deadline is needed to establish EOF or failed cleanup. Retain independent reaping. |
| `aggregate collection exhaustion...` | Use controlled aggregate and collector clocks with an observed first record. Debit the first collection deliberately to exhaustion. Assert later validator spawns never occur, later attempts still execute, and earlier records are not borrowed. |
| `M08: timeout, failed cleanup and late output...` | Use controlled first-phase collection expiry after receipt of its record. Keep phase-two launch as the late-write gate, real `EPIPE`, independent file bytes, phase associations, failed cleanup, matrix comparison and cross-reader replay. |

For cases proving ordering, use generous real watchdog/fixture-lifetime bounds
and existing normal host allowances instead of incidental 100/200 ms sentinel
deadlines. Keep short allowances only where expiry is the behavior being tested.
An absence assertion must follow an observed child checkpoint or terminal
publication; checking immediately after spawn would allow a broken implementation
to pass simply because the child had not run yet.

Update the mutation driver that imports `runOrderingGateControl` together with
its oracle in
[mutations.py](tests/suites/witness_contract/opt_in/mutations.py). Its current
diagnostic/receipt expectations depend on the old held-receipt format. Preserve
the requirement that the early-release mutant is rejected for independent early
publication/effect evidence, not a compilation failure, timeout or identity
mismatch. Preserve the existing real-worker bypass and eligibility controls.

### 6. Keep deadline correctness independently tested

Add focused validator deadline cases using the same narrow clock/read boundary.
They must establish that the original allowance is not renewed by partial input,
partial output or interruptions, that exact expiry closes collection, that an
unavailable clock or sample below its starting value retains the existing
`clock_error` meaning, and that a complete earlier record survives closure while
an incomplete tail does not gain verdict status. Do not expand the deadline
helper's clock-validity rules in this change. Use actual pipe reads for retention
assertions; simple controlled clock tests can cover arithmetic separately.

Retain one native-clock live collector timeout against a fixture that remains
open and does not promise a prefix record. Give it a generous outside watchdog;
assert the driver's deadline stop, observed termination/reaping and no fabricated
verdict. This establishes that production still uses an effective real deadline
without requiring a newly started child to publish within 150 ms. Keep existing
host-clock, native proceed and exec-deadline coverage; the new gate-driven worker
fixture does not establish the production worker's timeout arithmetic.

Use rejected controls to protect the new assertions: advance expiry before a
complete read, drop the complete record, release despite observed worker expiry,
return success without the worker effect, and accept late validator output after
collection closes. Each must fail the corresponding independent assertion.
Exercise the existing host early-release mutation after the checkpoint change.
Do not use a shared production classifier as the test oracle for these facts.

### Phase-2 documentation, verification and completion

Update the lifecycle and runner-unit READMEs, fixture catalog, coverage account
and affected assertions in `tests/FAILURE-PROPAGATION-CONTRACT.md` together.
Describe which observations come from actual children and which clock samples or
worker publications are controlled. Retain M08 and any newly retained main-case
replies through the Swift encoder and the existing Rust/Python replay pattern;
register the replay in the wrapper so it actually runs. Update the mutation
description in `tests/OPT_IN_TESTS.md` and its suite README if receipts change.
No request, reply or envelope version change is intended: meanings and wire
fields stay the same. Regenerate worker identity for changed runner sources;
new native production source files would also require Meson inventory changes.

Run verification through `tests/run.sh`, with a fresh `PW_TEST_OUT_DIR` per
checkpoint and retained inputs/receipts. Use `--list` to inspect selections;
do not use a suite selector that unintentionally includes unrelated opt-ins.

| Checkpoint | Required checks and what they establish |
| --- | --- |
| Phase-1 helper/wrapper | New `shell_helpers/executable_preparation`, existing `shell_helpers/controls` and `script_groups`: real preparation failures stop consumers, positive siblings continue, and receipts/cleanup survive. |
| Phase-1 build | Signed full build and disposable partial-build sibling; `source_drift/build_documentation`, `source_drift/generator_contract`, `source_drift/runner_source_manifests_agree`, and `python3 docs/generate_worker_identity.py --check`; `preflight/build_guard_controls`, `preflight/build_refusal_controls` and `preflight/codesign.preflight`. Prove final-byte execution and packaging refusal through the actual build. |
| Phase-2 main-case checkpoint | `runner_unit/pwrunner_core_unit_executable` including delayed/undelayed variants and rejected controls. Prove the intended sequence with real transport and effects before converting the remaining cases. |
| Phase-2 integrated candidate | Default cases of `runner_unit`, `runner_abi_layout`, `runner_c_worker_harness`, `unit`, `failure_boundaries` and `runner_validator_failure`; `witness_contract/phases`, `witness_contract/attempt_effects_wait_for_collection`, `witness_contract/queries_use_a_pre_attempt_interval`, `witness_contract/validator_subprocess_populated`, and explicit `witness_contract/order_barrier_mutations`. Cover unchanged producer/reader behavior, native timing, per-phase evidence and sensitivity to barrier faults. |
| Final | Full `source_drift` and the default battery against the final signed candidate. Select the stated opt-in build/barrier controls explicitly; the default battery alone does not include them. |

Confirm canonical IDs in the current catalog before execution; add the new
preparation case explicitly. Expand the default-only groups into case selections
where a suite selector would also run an opt-in. The `native_clock` opt-in and
power-state/sleep-wake observations are outside this plan. Preserve existing
checkout locking and evidence ownership. If the automation sandbox blocks required signing, process observation
or XPC, follow `tests/AGENTS.md`'s same-command escalation rule, retaining the
original result. That environmental procedure does not authorize automatic
specimen retries after ordering failures.

Phase 2 is complete when the named ordering cases have no required race between
startup/publication and a short real-time allowance; controlled delay preserves
their result; all required receipts, native effects and retained records are
asserted; the deliberately broken controls are rejected for the intended reason;
and native deadline coverage and integrated readers still pass. Report preparation
failures, equipment watchdogs and behavioral failures distinctly. Leave unrelated
working-tree changes and historical evidence intact.

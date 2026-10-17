# Repair worker timing with continuous Mach time

## Problem and intended result

Replace the C worker's shared `CLOCK_MONOTONIC` dependency with
`mach_continuous_time`, an explicitly initialized and validated Mach timebase,
and checked integer arithmetic. Use that one clock domain for phase-release
waits and all exec accounting. Preserve the worker's sampled-time decision
before release, cancellation and acknowledgement, and preserve the evidence
when any timing check refuses to proceed.

The [investigation](../records/SAFE-WAIT-TIME-INVESTIGATION.md) reproduced
`clock_gettime(CLOCK_MONOTONIC)` returning `-1/EPERM` after successful application
of `(version 2)(deny default)(allow file-read-data)`. Successful earlier reads,
including explicit pre-application warm-up, did not prevent failure. The
installed implementation and published sources support a `gettimeofday`
fallback; worker-PID denial events identify Unix syscall 116. The original
failure and the native loops are separate observations, not a trace of the
original failing call's commpage state.

Continuous Mach time is the selected repair. It includes system sleep and
avoids the reproduced libc clock path in the implementations examined. The
investigation found no candidate failures on its native arm64 machine, but did
not test an integrated replacement, actual sleep/wake, or native Intel. Its
passing baseline suites are not acceptance evidence for this repair.

This change covers the worker clock source, conversion, deadlines, failure
reporting, affected readers, tests and documentation. Keep the current host and
worker responsibilities, polling structures, allowance values and per-phase
release protocol. Host/validator/controller clocks remain independently owned;
no worker timestamp will be compared with them. Host deadline redesign, a total
response-time guarantee, unfinished-cleanup ownership (P4), timed issuance,
token-delivery redesign and changes to specimen permissions are outside scope.

## Preparation findings and implementation map

The relevant code and contracts have these consequences for the repair:

| Location | Consequence |
| --- | --- |
| [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `PW_MONOTONIC_READ`, `attempt_budget_start`, `attempt_budget_exclude`, `wait_for_proceed`, `attempt_exec_spawn` | The clock seam serves worker start, proceed start/observation, exec admission/observation and reap. Wait duration extends the exec deadline. Replacing only proceed would mix clock rates and leave unsafe post-apply exec reads. Current conversion and deadline additions are unchecked. |
| [CWorker.swift](Sources/PWRunnerCore/CWorker.swift): phase boundary and release publication | Collection is synchronous and excluded from the host sentinel allowance. The host checks `done` before release, but those operations are not atomic together; a worker refusal must remain terminal after a late release. |
| [CWorkerOrchestrator.swift](Sources/PWRunnerCore/CWorkerOrchestrator.swift): `buildPhaseOrdering`, `buildOrdering`, `classify` | Proceed failures are phase-indexed. A failure in phase 2 must not invalidate phase 1's established chain. Published worker failure takes summary precedence without discarding native or cleanup observations. |
| [Worker evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract) and [ABI header](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | Failure codes are open integers. Native kind zero omits a native result; errno has its own presence bit. This can represent local timing failures without inventing native returns. |
| [clock_failure.c](../tests/fixtures/worker_lifecycle/clock_failure.c), [exec_control.c](../tests/fixtures/worker_lifecycle/exec_control.c), [OrderingTests.swift](Tests/PWRunnerCoreTests/OrderingTests.swift), [PhaseProtocolTests.swift](Tests/PWRunnerCoreTests/PhaseProtocolTests.swift) | Existing controls include production worker code or drive the real host. Adapt them to native setup results and raw ticks; retaining a fake errno-returning continuous clock would test the wrong contract. |

The investigation's deterministic mode 9 also exposes a separate arithmetic
defect: a successful but backwards clock sample produces acknowledgement, an
action, and a negative wait exclusion. Its retained
[observation](../tests/out/runs/safe-wait-baseline-live-20261016/investigation/orders/order-9.stdout)
was checked during preparation. That link is gitignored local evidence. The
repair must turn this case into a local failure before acknowledgement.

The retained successful `bug_report_returns_verdicts` baseline has an `allow`
prediction, a published `open_failed` attempt with `EPERM`, and `query_first`.
Repair acceptance must require that the attempt ran and was reported, not infer
that the prediction requires a successful open.

Keep the investigation and its equipment as historical evidence. New maintained
fixtures belong under `tests/`; they must not depend on files in `records/`.
The associated plan is the inbound link to the investigation, following
[records guidance](../records/AGENTS.md).

## Chosen clock and arithmetic model

Implement a small worker-local clock context and helpers in the existing C
worker. Do not introduce a general clock framework. The context owns the
timebase numerator/denominator, a raw origin, the last accepted raw sample and
an explicit local fault state. Use `<mach/mach_time.h>` and fixed storage.

Capture the origin at the existing `WORKER_START` position, after argument
parsing and before mapping/setup. A raw read does not require conversion.
After validating the mapping identity and prepared/header inputs, initialize
the timebase once, before policy reading, compilation, readiness or application.
Check `mach_timebase_info`'s `kern_return_t`; only after `KERN_SUCCESS`, inspect
and require nonzero numerator and denominator. Then prepare all configured
worker durations. Setup time after the origin remains charged to the exec
budget. No shared payload may be written
before ABI/header validation; a mapping or identity failure retains its current
refusal behavior.

This initialization obtains unit-conversion metadata only. It grants no file,
socket, token or retained-port authority to an attempt. Do not add permissions,
pre-open probe resources, or call timebase initialization lazily after apply.

Use **relative continuous ticks** for worker time coordinates, deadlines and
phase exclusions. A sample is usable only if its raw value is at least both
the origin and the last accepted raw value; equality and raw zero are valid.
Subtract only after those checks. A regression, including observed wrap, marks
the clock unusable for subsequent timed work. Do not fall back to another clock
or recover by clearing the fault on the next successful-looking sample.

For a positive budget in nanoseconds, compute its tick allowance as:

```text
product = (__uint128_t)budget_ns * timebase.denom
ticks   = product / timebase.numer + (product % timebase.numer != 0)
```

Validate the millisecond-to-nanosecond multiplication, the factors, positivity
and `uint64_t` representability before narrowing. At tick delta `ticks` the
budget is expired; at `ticks - 1` it is not. With the observed 125/3 timebase,
a 1 ms allowance is exactly 24,000 ticks. An exact-integer preparation check
confirmed the ceiling inequality for unit, 125/3, reciprocal and extreme
32-bit ratios; the implementation still needs compiled boundary controls.

Keep exclusions in ticks: three one-tick waits at 125/3 are 125 ns together,
whereas flooring each separately would charge only 123 ns. Never convert each
wait to integer nanoseconds and feed those rounded intervals back into a tick
deadline. Use checked `uint64_t` addition for the plan deadline, child deadline
and accumulated exclusions. This deliberately replaces the current signed
nanosecond deadline representation and its unchecked additions.

Convert only bounded **deltas** when a millisecond polling timeout is needed,
using a 128-bit product and quotient/remainder ceiling, then cap at the existing
poll interval before narrowing. Never multiply the absolute counter in 64 bits,
subtract a larger timestamp from a smaller one, or use saturating arithmetic
that quietly grants more budget. The supported-lifetime assumption is no raw
counter wrap during one worker lifetime and representable finite allowances and
cutoffs; detected violations fail closed. A huge forward sample can establish
expiry without converting an absolute counter to nanoseconds.

## Failure representation and coordinated readers

Implement the following representation before integrating the new wait. Keep
the shared layout and existing public result fields; new meanings are named
numeric codes and existing bounded diagnostics.

| Boundary | Publication and continuation |
| --- | --- |
| Native timebase initialization fails | Add `PW_OP_CLOCK_SETUP` (operation 12). Publish code `PW_FAILURE_NATIVE`, kind `PW_NATIVE_INTEGER`, the actual Mach return, no errno, no item index, detail zero. Publish failure, diagnostic and `done`, then return a nonzero pre-apply exit status. No ready/apply/action result is fabricated. |
| Invalid timebase or unrepresentable configured duration | Under operation 12, publish a new `PW_FAILURE_TIME_INVALID` (code 14), `PW_NATIVE_NONE`, no native result or errno, no index, and a documented reason in `detail`. Publish diagnostic and `done`, then return nonzero before applying any specimen, including plans without exec. |
| Invalid proceed sample or exclusion arithmetic | Operation 11/code 14/kind zero, no native result or errno, phase index, reason in `detail`; diagnostic names the stage. Publish `done`, then use the existing exit-request spin. No acknowledgement or action for that phase. |
| Valid elapsed proceed time reaches its allowance | Retain operation 11/code 8, wait milliseconds in `detail`, phase index and the existing terminal behavior. Future-release code 11 retains its ordinal detail. |
| Exec timing invalid before spawn | Complete that attempt with `rc=-1`, no child, `errno_val=0` for the local fault and an explicit timing-stage/reason diagnostic. Refuse spawn; retain ordinary budget exhaustion's existing `ETIMEDOUT` convention. |
| Exec timing invalid after spawn or during reap | Keep the PID, captured bytes and any independently reaped status. Record the local reason separately from real wait/poll/read/kill failures in the existing slot diagnostic. Enter the existing ownership-aware cleanup path; a local fault alone contributes no errno. |

Define code 14's reason values alongside the ABI enums: invalid timebase,
invalid/unrepresentable duration, backwards counter, unrepresentable delta,
and deadline/exclusion overflow. Do not interpret these details as milliseconds.
For exec, retain separate local-fault state and native-error variables internally;
zero errno must no longer mean that an observation loop has no failure. If a
local fault and native cleanup fault coexist, preserve both in the bounded
diagnostic and retain the actual native errno in the existing errno field.
The exec reason remains diagnostic rather than a new machine-readable record;
classification must not parse its English text or claim sandbox attribution.

Keep `PW_NATIVE_CLOCK` and its documented historical meaning transportable;
do not redefine it as the result of `mach_continuous_time`, which has no native
error-return channel. New native-failure controls target timebase initialization;
post-apply controls supply unusable raw values. Set a stale permission errno in
both controls to prove it is not reported as a timing failure.

Give clock setup its real started/returned progress around initialization, after
header validation and before policy reading. Update the temporal operation order
in [PWRunnerAPI.swift](Sources/PWRunnerCore/PWRunnerAPI.swift),
[disposition.rs](../controller/src/disposition.rs) and
[lifecycle_contract.py](../tests/lib/lifecycle_contract.py), with independent
oracle controls and affected disposition fixtures. Update classifier names and
code/detail handling in `CWorkerOrchestrator.swift`. Preserve the phase-local
operation-11 filtering and all unknown-code transport rules.
Exercise setup refusal while the host is still delivering policy: an independent
pipe failure or early reap must not obscure the published clock-setup failure,
and no policy receipt or completed application may be invented.

Use one additive response-schema increment in
[contract.json](../docs/contract.json) for this coordinated evidence/reader
change. Keep request and envelope versions unchanged: there is no new specimen
input or envelope shape. Regenerate version copies with
`docs/generate_contract.py`, update current-version fixtures and round trips,
and retain historical evidence unchanged. This explicitly versions the new
setup milestone and its disposition interpretation under the
[wire rules](../docs/CONTRACT.md#when-a-number-moves).

## Implementation sequence

### 1. Establish the clock and its failure paths

Add the context, setup, checked duration conversion and semantic raw-read seam.
Replace `PW_MONOTONIC_READ` with separate compile-time seams for the real
timebase call and the raw continuous read. Preserve the existing semantic phase
names; no request override or ambient environment variable selects a fault.
The production raw-read signature returns ticks, not a manufactured rc/errno.

Add compiled controls against these production helpers for setup failure,
zero factors, valid zero samples, non-unit ratios, ceiling edges, large products,
unrepresentable allowances, regressions and addition overflow. Supply expected
answers independently of the helper under test. Update failure transport and
reader controls in the same work unit. This checkpoint must demonstrate correct
native/local distinction and refusal before application, not just compilation.

### 2. Move proceed and exec accounting together

Convert `attempt_budget_start`, `attempt_budget_exclude`, `wait_for_proceed` and
every timed branch of `attempt_exec_spawn` to the shared tick context. There
must be no residual `CLOCK_MONOTONIC` dependency in any of the six worker clock
phases. Preserve the plan's absolute cutoff across spawn/setup delays, select
the smaller of the remaining plan deadline and the post-spawn child deadline,
and use the same source for the reap allowance.

For each phase, publish progress and arrival once, then take its start sample.
Reject an unusable start before entering the polling loop. Each polling
decision must have this order:

1. Obtain and validate the next observation sample. Reject unusable time before
   consulting release; do not restart the phase's allowance on another poll.
2. Reject elapsed ticks at or beyond the phase allowance. With a usable,
   pre-expiry sample, prepare a checked candidate exec deadline extended by
   that sample's wait delta. Overflow is a terminal proceed failure.
3. Acquire-load release; reject a future ordinal. A stale ordinal cannot
   release the new phase.
4. Acquire-load cancellation; if observed, exit without acknowledgement.
5. For the exact ordinal, commit the already checked exclusion once, then
   release-store phase acknowledgement and latest ordinal, publish returned
   progress, and enter the action loop. Repeated polls must not repeatedly
   extend the budget. Remove the unchecked post-return exclusion in `main`.

Checking exclusion before acknowledgement avoids reporting an operation-11
failure after acknowledging the same phase, which current ordering readers
correctly treat as contradictory. The clock fault, expiry, future ordinal and
cancellation precedence remains explicit; a late host release cannot revive
any terminal failure.

Retain the sampled-time limit: a pre-expiry sample can be followed by delayed
scheduling and a late acknowledgement/action. A release stored before expiry
can be refused by an expired next sample. Cancellation observed by its load
wins; cancellation stored after that load can arrive too late. Arrival precedes
the start sample. Neither atomics nor this clock create a timestamp of the
host's release or a hard bound on action start.

Exec cleanup must still distinguish EOF, leader exit, group termination request
and confirmed reap. On invalid observation time, request group cleanup only
while ownership is known. On invalid reap time, still permit the immediate
nonblocking `waitpid` observation; if it returns the child, keep that status.
Otherwise stop timed reaping with an explicit local fault and missing status.
Never substitute a blocking wait or an iteration-count allowance. Preserve
completed prefix and subsequent non-exec effects where the current per-step
exec-failure flow permits them.

### 3. Pin the changed decisions with maintained controls

Adapt the lifecycle fixture builder and `clock_failure.c` companions, add raw
tick/setup cases, and extend `exec_control.c`. Register any new C cases with the
dispatcher and any new Swift test file in `Tests/PWRunnerCoreTests/main.swift`.
Use fixtures outside the signed app. The following are required observations:

| Control group | Required result and distinguishing control |
| --- | --- |
| Original dependency | Compile production worker code with a test-only boundary that refuses direct post-apply `CLOCK_MONOTONIC` calls, including after earlier successes. The old path must fail; the repaired path must complete the ordinary specimen without invoking it. Pair this with real native runs below, because substitution alone does not establish platform safety. |
| Tick arithmetic | Test 1/1, 125/3, reciprocal and extreme ratios; exact edge and one tick below; zero, regression relative to the last sample even when still above the origin, wrap, multiplication/narrowing/addition overflow. Multiple fractional-nanosecond phase waits must extend the plan by their exact tick sum once. An unchecked multiply, floor instead of ceiling, or duplicated exclusion must fail these controls. |
| Proceed precedence | Port the investigation's modes 0–8 to the new seam and native/local distinction; mode 9 must now fail closed. Test unusable start/observation with release already present, expiry with release and cancellation present, valid release, cancellation, future release before cancellation, and stale phase-1 release during phase 2. Observe acknowledgement, action-start progress and completed native action independently. |
| Scheduled races | Add test-only gates immediately after the time decision and after the cancellation load. Hold the first beyond the allowance: the pre-expiry decision can still acknowledge. Store cancellation behind the second: it can be too late. Complement both with before-decision controls; do not require a winner in an unscheduled race. |
| Phase/evidence integration | Gate real host collection; acknowledgement and action start stay absent before release. Fail phase 2 time after phase 1 completes; retain phase 1 publications, native results and any supported `query_first`. Retain partial phase-2 validator records on expiry, while its attempts remain unavailable and its order unestablished. Validate serialized replies through independent readers. |
| Exec accounting and cleanup | Vary spawn latency, intervening non-exec time, multiple exclusions, exact plan exhaustion, child-deadline clamping and every timing stage. Check no spawn on refusal, captured output/status survival after spawn, and combined local clock plus native kill/wait failures. Keep pending/EINTR reaps bounded and independently clean up real children whose driver cannot confirm cleanup. |

Use the existing `runner_c_worker_harness/exec_control_states`, remainder and
sequence cases, `OrderingTests`, `PhaseProtocolTests`, `WorkerEvidenceTests`,
disposition/contract tests and live exec suites wherever they already own these
observations. Extend them instead of duplicating whole harnesses.

Strengthen `witness_contract/bug_report_returns_verdicts`: its current assertion
only checks the prediction's `allow` outcome. For this regression also require
successful application, no worker timing failure, the actual release/ack chain,
native attempt publication and confirmed worker cleanup. Retain and validate
the open's actual rc/errno; a completed permission failure is valid evidence
for this timing check. Validate descriptor-derived path evidence when present,
without making its availability or open success a new requirement of the
specimen. Use the allow-default neighbour for a positive open/path control.
Keep prediction and attempt assertions independent; neither establishes
agreement or universal permission.

Review the exact mutation anchors in
[the ordering mutation equipment](../tests/suites/witness_contract/opt_in/mutations.py)
after changing the wait signature. Its unmodified controls must pass and both
the worker-wait bypass and premature-host-release mutation must still produce
early effects detected while collection is held. A mutation that no longer
applies or merely fails compilation supplies no acceptance credit.

### 4. Establish native applicability and update the account

Add an opt-in native clock control using the production clock helpers under the
original version-2 policy, bare deny-default and allow-default. Use fresh
processes and explicit pre-apply timebase initialization. Exercise both a helper
variant whose first explicit raw read is after application and the production
sequence with its pre-apply worker origin, followed by repeated post-apply
reads. Neither adds policy permission. First explicit use does not establish
that the loader or native libraries made no earlier internal call; inspection
must use separate processes so it does not warm the measured path. Preserve
native setup returns, factors, sample/validation counts, PIDs, process reap and
available denial records. Retain a standalone old-clock neighbour for the intermittent
failure comparison; its failure need not recur in every run. Missing deny logs
are not proof of safety, and the investigation's log timestamp offsets must
not be adjusted into stronger correlation.

Two applicability checks require equipment or events absent from the existing
investigation. They do not block implementing the clock, evidence and
deterministic controls, but their results bound acceptance:

- **Supported native configurations and fallback paths.** Run the candidate
  controls and signed integration selection on native arm64 and native x86_64
  configurations supported by the build. Retain OS/SDK/architecture, timebase
  and applicable installed/source path evidence. Rosetta or a cross-compile
  does not establish native Intel behavior. Inspect a selected fallback
  separately; do not assert the arm64 counter-register fast path was used
  everywhere. A denied or otherwise unusable candidate path blocks acceptance
  on that configuration and requires a revised repair, not a policy allowance
  or a silent fallback to `CLOCK_MONOTONIC`. Missing equipment leaves that
  validation explicitly outstanding, not passed or silently removed from scope.
- **Actual system sleep/wake.** On dedicated, operator-coordinated equipment,
  hold a worker at a test gate after its proceed start sample, establish real
  system sleep and wake independently, then permit the next sample. With sleep
  longer than its short allowance, it must expire before acknowledgement even
  with release visible. A companion exec control must charge sleep outside
  waits and exclude the entire measured wait when that wait is valid. Retain
  raw tick deltas, factors, sleep/wake evidence and a no-sleep neighbour.
  `SIGSTOP`, a process delay or mocked ticks are not system sleep. If actual
  sleep is unobserved, no tested-sleep claim is available; if the check
  contradicts the chosen semantics, stop acceptance and investigate the path.

The exact original commpage fallback condition and the log timestamp offset
remain historical research questions; resolving them is not a repair gate.
The plan does require supported-configuration evidence and an actual sleep
control before claiming complete timing acceptance.

Update [limits.json](../docs/limits.json) for `worker_proceed_wait`,
`exec_attempt_budget`, `exec_child_wait` and `exec_reap_grace`, including the
sampled decision, timebase setup, sleep inclusion, raw tick exclusions and local
failure behavior. Update the authored execution-budget explanation in
[LIMITS.md](../docs/LIMITS.md), then run `docs/generate_limits.py` to refresh the
inventory and shared guide copies. Keep host clock descriptions distinct.
Correct the unconditional commpage comment in the worker and explain the
bounded platform evidence without promising an always-userspace path.

Update the worker-evidence and ordering sections of
[FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md), the
runner lifecycle reference, fixture/suite READMEs, catalog, coverage and opt-in
registry with the tests they actually own. Update relevant setup/evidence
citations in [architecture.json](../docs/architecture.json) and regenerate with
`docs/generate_architecture.py`; this is not a new process or channel. Permanent
documentation describes the resulting behavior and links maintained tests,
not the investigation or a change-history narrative.

Regenerate worker identity with `docs/generate_worker_identity.py` after all
native, host, protocol and build inputs settle. No layout expansion is planned;
run compiled C/Swift layout agreement and review any unexpected layout-golden
delta rather than accepting it automatically. Keep helper code in the existing
worker translation unit; if implementation needs a new native source, update
its Meson target and source-list/build account together. Use owning generators,
never hand-edit generated regions or the signed app's evidence.

## Verification and completion

Build a matching signed candidate through [BUILD.md](../docs/BUILD.md). Run
from the repository root with fresh output directories and assertions enabled.
Inspect selections with `--list` before execution. A concrete core selection is:

```sh
PW_TEST_OUT_DIR=tests/out/runs/safe-wait-repair-core \
  tests/run.sh --suite runner_unit --suite runner_c_worker_harness \
  --suite runner_abi_layout --suite failure_boundaries --suite unit \
  --suite source_drift --suite runner_exec_lifecycle \
  --case witness_contract/bug_report_returns_verdicts \
  --case witness_contract/bug_report_returns_attempts \
  --case witness_contract/order_barrier_mutations
```

Add the newly registered clock/native cases and affected live multi-phase
witness cases to that selection. Then run the complete default battery against
the final candidate in another fresh directory. The default battery does not
replace the opt-in ordering, native-clock or sleep controls. After any further
source change, rerun affected checks under the repository's evidence-reuse
rules; earlier baseline credit cannot certify a new worker identity.

Run app/XPC/log/signing-dependent checks outside restrictive automation
sandboxing. If a harness restriction first appears, rerun the same failing
command once with escalation against unchanged artifacts, as required by
[test guidance](../tests/AGENTS.md#sandboxed-automation-harnesses). Preserve
failures, source/build provenance, raw inputs and cleanup observations. Use the
checkout lock, managed output and retention/pruning helpers; never remove the
lock or protected evidence to obtain a clean run.

The repair is complete when the common tick domain is implemented without the
unsafe worker clock dependency, setup/arithmetic failures have honest evidence,
boundary and race controls reject the original unsafe behaviors, integrated
phase and exec evidence survives correctly, both ordering mutations are caught,
supported-platform and sleep checks are accounted for, and the final signed
candidate passes the required selections and default battery. The handoff must
identify the accepted source/build and run IDs, distinguish deterministic,
native and source-path evidence, and name any outstanding applicability check.
An outstanding required configuration or sleep check means implementation can
be ready for that validation; complete acceptance must not be claimed.

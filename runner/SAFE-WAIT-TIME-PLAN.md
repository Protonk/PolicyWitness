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

PolicyWitness's support target is native arm64 execution on Apple Silicon,
on macOS 26 or later. Intel and translated x86_64 clock behavior are outside
this plan and add no implementation or acceptance gate. The deliverable is a
signed candidate validated on the available native arm64 machine, with actual
sleep/wake validation recorded as pending. Equipment and permission for that
observation have not been established; it does not gate
the local deliverable. The plan does not authorize power-state changes on the
machine running the development session.

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
an immutable first rejected-sample record (the sticky clock fault). Only raw
sample validation may populate that record, when a sample is below the origin
or the last accepted sample. It holds the rejection reason, semantic clock
stage, zero-based specimen phase and action slot when applicable; absent scope
is explicit. Setup and arithmetic refusals never populate or overwrite it.
Use `<mach/mach_time.h>` and fixed storage. Pass this context through the wait
and exec helpers so a sample fault's origin is captured where it occurs, not
reconstructed by a later caller.

Capture the origin at the existing `WORKER_START` position, after argument
parsing and before mapping/setup. A raw read does not require conversion.
After validating the mapping identity and prepared/header inputs, initialize
the timebase once, before policy reading, compilation, readiness or application.
Check `mach_timebase_info`'s `kern_return_t`; only after `KERN_SUCCESS`, inspect
and require nonzero numerator and denominator. Then prepare all configured
worker durations. Setup time after the origin remains charged to the exec
budget. No shared payload may be written before ABI/header validation; a mapping
or identity failure retains its current refusal behavior.

This initialization obtains unit-conversion metadata only. It grants no file,
socket, token or retained-port authority to an attempt. Do not add permissions,
pre-open probe resources, or call timebase initialization lazily after apply.

Use **relative continuous ticks** for worker time coordinates, deadlines and
phase exclusions. A sample is usable only if its raw value is at least both
the origin and the last accepted raw value; equality and raw zero are valid.
Subtract only after those checks. A regression, including observed wrap, marks
the clock unusable for subsequent timed work. Do not fall back to another clock
or recover by clearing the fault on the next successful-looking sample. A later
caller refuses because of that recorded sample fault without taking another
sample; it must not report a fresh backwards counter at its own stage.

Arithmetic refusals are separate, operation-local results: invalid duration,
unrepresentable delta conversion, and deadline/exclusion overflow. Here
"unrepresentable delta" means that converting a valid tick delta cannot fit the
required destination type; it is not a rejected raw sample. Ordered `uint64_t`
samples have a representable tick difference after the ordering checks. Report
an arithmetic refusal where it occurs, with its own stage and scope, leaving
the sticky record unchanged (empty if no sample has been rejected). Keep the
last accepted sample even when subsequent arithmetic fails. Later timed work
can proceed with valid samples and representable arithmetic; if it encounters
a real regression, that rejection
becomes the first sticky fault with its own origin. A terminal proceed arithmetic
refusal still publishes failure/done as specified below; it does not need to
invalidate the clock to stop that phase permanently.

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
whereas flooring each separately would exclude only 123 ns and charge the
budget 2 ns more. Never convert each wait to integer nanoseconds and feed those
rounded intervals back into a tick deadline. Use checked `uint64_t` addition
for the plan deadline, child deadline and accumulated exclusions. This
deliberately replaces the current signed
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
| Native timebase initialization fails | Add `PW_OP_CLOCK_SETUP` (operation 12). Publish code `PW_FAILURE_NATIVE`, kind `PW_NATIVE_INTEGER`, the actual Mach return, no errno, no item index, detail zero. Publish the diagnostic and return the new clock-setup exit status 12, without publishing `done`. No ready/apply/action result is fabricated. |
| Invalid timebase or unrepresentable configured duration | Under operation 12, publish a new `PW_FAILURE_TIME_INVALID` (code 14), `PW_NATIVE_NONE`, no native result or errno, no index, and a documented reason in `detail`. Publish the diagnostic and return exit status 12 without `done`, before applying any specimen, including plans without exec. |
| Invalid proceed sample or exclusion arithmetic | Operation 11/code 14/kind zero, no native result or errno, phase index, reason in `detail`; diagnostic names the stage. Publish `done`, then use the existing exit-request spin. No acknowledgement or action for that phase. |
| Proceed refused because an earlier exec invalidated the clock | Operation 11/code 14/kind zero, current phase index, `prior_clock_fault` reason in `detail`; diagnostic names the original reason, semantic stage, phase and slot. Publish `done` and spin without acknowledgement. This records the current refusal, not a new sample failure. |
| Valid elapsed proceed time reaches its allowance | Retain operation 11/code 8, wait milliseconds in `detail`, phase index and the existing terminal behavior. Future-release code 11 retains its ordinal detail. |
| Exec timing invalid before spawn | Complete that attempt with `rc=-1`, no child, `errno_val=0` for the local fault and an explicit timing-stage/reason diagnostic. Refuse spawn; retain ordinary budget exhaustion's existing `ETIMEDOUT` convention. |
| Exec timing invalid after spawn or during reap | Keep the PID, captured bytes and any independently reaped status. Record the local reason separately from real wait/poll/read/kill failures in the existing slot diagnostic. Enter the existing ownership-aware cleanup path; a local fault alone contributes no errno. |

Setup refusal follows the adjacent header and policy-read convention: failure
publication followed by a distinct nonzero return, with `applied=0`, `done=0`
and no claimed `apply_rc`. Exit status 12 is unused in the current worker.
Leave `apply_rc` storage untouched; do not introduce a second status-word
convention for setup or rely on failure precedence to hide the inconsistent
terminal-publication combination `applied=0, done=1, apply_rc=0`. Keep that
contract row unchanged.

Define code 14's reason values alongside the ABI enums: invalid timebase,
invalid/unrepresentable duration, backwards counter, unrepresentable delta,
deadline/exclusion overflow and prior clock fault. Do not interpret these
details as milliseconds. Only an actual rejected sample gets the backwards
counter reason. `prior_clock_fault` requires an existing rejected-sample record;
it must never be emitted merely because an earlier arithmetic operation failed.
Subsequent exec refusals caused by a sticky sample fault retain that origin
and identify themselves as refusals due to the earlier rejected sample.
For exec, retain separate local-fault state and native-error variables internally;
zero errno must no longer mean that an observation loop has no failure. If a
local fault and native cleanup fault coexist, preserve both in the bounded
diagnostic and retain the actual native errno in the existing errno field.
The precise origin remains in bounded diagnostics rather than a new wire
record. The distinct prior-fault reason makes the later proceed refusal
machine-distinguishable from a new sample failure. Render that reason as
"proceed refused: worker clock already invalid", with the preserved origin
in the diagnostic; never summarize it as a new proceed clock regression.
Classification must not parse English text or claim sandbox attribution.

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
and no policy receipt or completed application may be invented. Assert the
failure payload, `done=0`, `applied=0`, no acknowledgement/actions and independently
reaped exit 12, including after reply serialization. Check the raw publication
combination as well as the summary so precedence cannot conceal a contradiction.

Use one additive response-schema increment in
[contract.json](../docs/contract.json) for this coordinated evidence/reader
change. Keep request and envelope versions unchanged: there is no new specimen
input or envelope shape. Regenerate version copies with
`docs/generate_contract.py`, update current-version fixtures and round trips,
and retain historical evidence unchanged. This explicitly versions the new
setup milestone and its disposition interpretation under the
[wire rules](../docs/CONTRACT.md#when-a-number-moves).

## Implementation sequence

Before the **step-1 signed checkpoint build**, capture the existing baseline
worker's raw `nm -u` receipt and status, hash, embedded source identity and
bundle provenance into retained baseline evidence outside `dist/`. Verify that
the receipt records `_clock_gettime` and that its hash identifies the inspected
worker. This precedes every build in this plan, not just the final candidate:
`build.sh` defaults `DIST_DIR` to `dist/`, so the step-1 build can already replace
the baseline bundle. Do not infer the old worker's identity from a regenerated
checkout or collect a checkpoint worker as though it were the pre-repair baseline.

Before **each** checkpoint build, including steps 1 and 2, regenerate with
`python3 docs/generate_worker_identity.py` after editing any covered input and
run its `--check`. The generator hashes all worker/runner `.c`, `.h` and `.swift`
inputs plus its declared build inputs; `build.sh` refuses stale copies before
compilation and checks again before signing. Regenerate after any intervening
covered edit, even a comment or generated contract-version change in a source.
Each signed checkpoint and its fixtures must use that checkpoint's identity;
do not defer regeneration until final acceptance.

### 1. Establish the clock and its failure paths

Add the context, setup, checked duration conversion and semantic raw-read seam.
Introduce separate compile-time seams for the real timebase call and the raw
continuous read, which replace `PW_MONOTONIC_READ` in step 2. Preserve the
existing semantic phase names; no request override or ambient environment
variable selects a fault.
The production raw-read signature returns ticks, not a manufactured rc/errno.

Add compiled controls against these production helpers for setup failure,
zero factors, valid zero samples, non-unit ratios, ceiling edges, large products,
unrepresentable allowances, regressions and addition overflow. Supply expected
answers independently of the helper under test. Update failure transport and
reader controls in the same work unit. This checkpoint must demonstrate correct
native/local distinction and refusal before application, not just compilation.
For staged development, introduce the continuous-time helpers and their setup
controls alongside the existing clock seam first; switch all production timing
callers together in step 2. This keeps intermediate signed checkpoints buildable
without a mixed-domain proceed/exec implementation. Remove the old seam in that
switch, then enable the worker-import check described below.

### 2. Move proceed and exec accounting together

Convert `attempt_budget_start`, `attempt_budget_exclude`, `wait_for_proceed` and
every timed branch of `attempt_exec_spawn` to the shared tick context. There
must be no residual `CLOCK_MONOTONIC` dependency in any of the six worker clock
phases. Preserve the plan's absolute cutoff across spawn/setup delays, select
the smaller of the remaining plan deadline and the post-spawn child deadline,
and use the same source for the reap allowance.

For each phase, publish progress and arrival once, then inspect the clock state.
If its rejected-sample record is populated, publish the prior-fault refusal
without a new sample. Earlier arithmetic refusals do not satisfy this condition.
Otherwise take its start sample and reject an unusable start before entering
the polling loop. Each polling decision must have this order:

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
| Removed dependency | Extend the shared artifact inspector to reject `_clock_gettime` in the built worker's undefined imports. Retain raw `nm -u` output and command status; inspection failure is not an empty import set. The existing pre-repair worker has this import; the candidate must not. Exercise the checker with independently passing and rejected symbol inputs and a compiled fixture that really imports `clock_gettime`. Pair this structural check with the native and timing-boundary controls; absence of the import alone does not establish usable time or correct ordering. |
| Tick arithmetic | Test 1/1, 125/3, reciprocal and extreme ratios; exact edge and one tick below; zero, regression relative to the last sample even when still above the origin, wrap, multiplication/narrowing/addition overflow. Multiple fractional-nanosecond phase waits must extend the plan by their exact tick sum once. An unchecked multiply, floor instead of ceiling, or duplicated exclusion must fail these controls. |
| Proceed precedence | Port the investigation's modes 0–8 to the new seam and native/local distinction; mode 9 must now fail closed. Test unusable start/observation with release already present, expiry with release and cancellation present, valid release, cancellation, future release before cancellation, and stale phase-1 release during phase 2. Observe acknowledgement, action-start progress and completed native action independently. |
| Scheduled races | Add test-only gates immediately after the time decision and after the cancellation load. Hold the first beyond the allowance: the pre-expiry decision can still acknowledge. Store cancellation behind the second: it can be too late. Complement both with before-decision controls; do not require a winner in an unscheduled race. |
| Phase/evidence integration | Gate real host collection; acknowledgement and action start stay absent before release. Fail phase 2 time after phase 1 completes; retain phase 1 publications, native results and any supported `query_first`. Retain partial phase-2 validator records on expiry, while its attempts remain unavailable and its order unestablished. Validate serialized replies through independent readers. |
| Sticky fault provenance | Inject a backwards sample in phase 1's exec observation or reap stage, then offer valid raw values for phase 2. Preserve the first stage/phase/slot in the completed exec diagnostic; phase 2 must refuse with `prior_clock_fault`, without taking a new sample or attributing a regression to phase 2. Check the serialized summary and diagnostic, missing phase-2 acknowledgement/actions, retained phase-1 publications, and independent child cleanup. Contrast a fault first encountered by phase 2's own read. |
| Arithmetic refusal stays local | With valid raw samples, control phase 1's exec arithmetic operands to cause deadline overflow or an unrepresentable delta conversion. Retain that attempt's local refusal and any child cleanup; assert that the sticky record stays empty and the last accepted sample stays current. Keep phase 2's allowance/exclusion representable and require its normal release, acknowledgement and action. In a companion case, introduce a later genuine regression and require its own stage/phase/slot as the first sticky origin, never the earlier arithmetic refusal's origin. |
| Exec accounting and cleanup | Vary spawn latency, intervening non-exec time, multiple exclusions, exact plan exhaustion, child-deadline clamping and every timing stage. Check no spawn on refusal, captured output/status survival after spawn, and combined local clock plus native kill/wait failures. Keep pending/EINTR reaps bounded and independently clean up real children whose driver cannot confirm cleanup. |

Use the existing `runner_c_worker_harness/exec_control_states`, remainder and
sequence cases, `OrderingTests`, `PhaseProtocolTests`, `WorkerEvidenceTests`,
disposition/contract tests and live exec suites wherever they already own these
observations. Extend them instead of duplicating whole harnesses.

The removed-dependency control belongs in
[artifact.py](../tests/lib/artifact.py) beside the existing host-import check,
with preflight checker controls and documentation. Inspect only the worker for
this prohibition; host and validator clocks remain out of scope. The check
sees direct linked imports, not dynamic lookups or arbitrary library-internal
behavior, so retain source review and native observations. This is the maintained
regression guard. The retained original clock failure and the artifact receipt
captured **before the step-1 build**, as required at the start of the implementation
sequence, supply the one-time baseline. Do not preserve an old production clock
branch, compile historical source on every test run, or depend on
`records/` to make a maintained test fail. There is no new old-clock mutation
in `mutations.py`; its existing ordering mutations keep their separate purpose.

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

### 4. Validate the available native platform and update the account

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

Run the candidate native controls and signed integration selection on the
available native arm64 machine. Preparation observed `uname -m` = `arm64` and
macOS 26.7.1/build 25G241; record the actual equipment again for implementation
runs. Retain OS/SDK/architecture, timebase and applicable installed/source path
evidence. Inspect any selected fallback separately; do not claim an always
userspace path. A denied or unusable candidate path on this machine blocks the
local deliverable and requires investigation, not extra specimen permission or
a silent fallback to `CLOCK_MONOTONIC`.

The existing [build target](../meson.build) derives architecture from the host
CPU and declares a macOS 26 minimum; that expression is not a support matrix.
The support decision is native arm64 on Apple Silicon, not translated x86_64
execution on the same hardware. Record native execution and the candidate
worker's Mach-O architecture when establishing timing-test applicability.
[APPLE-SILICON-PLAN.md](../APPLE-SILICON-PLAN.md) separately owns investigating
and documenting how to enforce that restriction. It adds no build modification
or prerequisite to this clock repair. Do not require Intel equipment, Rosetta
clock tests or an Intel fallback here. Apple Silicon configurations may themselves
select different clock paths; keep observations scoped to the recorded machine
and implementation, and do not claim that a support statement enforces build
architecture.

**Actual system sleep/wake is a follow-up outside the local delivery gate.**
No dedicated test machine, wake arrangement or authorization to interrupt this
development session is established. Do not sleep this Mac, change power settings
or schedule wake events as part of this implementation. First arrange a separate
operator-approved session and machine. The installed `pmset(1)` manual documents
relative wake scheduling and requires root for setting changes; those privileges
are not assumed here. The test owner must choose and authorize a wake method
and retain cleanup of any test-owned wake event without cancelling unrelated
events.

On that equipment, hold a worker after its proceed start sample, independently
establish real system sleep/wake, then allow the next sample. A short-budget
case must expire before acknowledgement even with release visible. In a
separate valid-wait case use the existing 60 s maximum: the **whole measured
wait**, including scheduling, must be below 60 s, with margin supplied by an
arranged timed or operator wake. Do not raise the production cap or credit an
over-budget wake as a successful exclusion. A companion exec observation must
charge sleep outside waits and exclude the measured valid wait in ticks.
Retain raw deltas/factors, sleep/wake evidence, a no-sleep neighbour and process
cleanup. Missing sleep or a missed wake window gives no success credit; a
contradiction with continuous-time accounting requires investigation before
claiming tested sleep behavior.

Required local deterministic controls inject counter advances through these
same wait/exec boundaries, including a valid long wait and an expired one. They
establish accounting, not system sleep. `SIGSTOP` and process delays likewise
cannot establish sleep inclusion. Documentation may state the API's documented
sleep semantics while explicitly distinguishing the absent native sleep test.
Record the sleep follow-up as unperformed, not a skipped passing case. Its
absence permits the locally validated candidate handoff, but not a claim of
experimentally verified sleep/wake acceptance. Intel is outside support scope,
not another pending acceptance item.

The exact original commpage fallback condition and the log timestamp offset
remain historical research questions; resolving them is not a repair gate.

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

Regenerate worker identity again after the final native, host, protocol and build
edits, in addition to every earlier checkpoint regeneration. No layout expansion
is planned; run compiled C/Swift layout agreement and review any unexpected layout-golden
delta rather than accepting it automatically. Keep helper code in the existing
worker translation unit; if implementation needs a new native source, update
its Meson target and source-list/build account together. Use owning generators,
never hand-edit generated regions or the signed app's evidence.

## Verification and completion

Build a matching signed candidate through [BUILD.md](../docs/BUILD.md). Run
from the repository root with fresh output directories and assertions enabled.
Regenerate/check identity before this build as before every checkpoint. Inspect
selections with `--list` before execution. A concrete core selection is:

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
witness cases and the new preflight import-checker controls to that selection.
Then run the complete default battery against the final candidate in another
fresh directory. The default battery does not replace the opt-in ordering and
native-clock controls. Real sleep/wake remains the separately arranged follow-up
above. After any further source change, regenerate identity when covered and
rerun affected checks under the repository's evidence-reuse rules; earlier
baseline credit cannot certify a new worker identity.

Run app/XPC/log/signing-dependent checks outside restrictive automation
sandboxing. If a harness restriction first appears, rerun the same failing
command once with escalation against unchanged artifacts, as required by
[test guidance](../tests/AGENTS.md#sandboxed-automation-harnesses). Preserve
failures, source/build provenance, raw inputs and cleanup observations. Use the
checkout lock, managed output and retention/pruning helpers; never remove the
lock or protected evidence to obtain a clean run.

The local implementation deliverable is complete when the common tick domain
is implemented without the unsafe worker import, setup refusals preserve the
pre-apply publication convention, rejected-sample origins survive later refusals,
arithmetic refusals remain local, race controls reject the unsafe behaviors,
integrated phase and exec evidence survives correctly, both ordering mutations
are caught, and the signed arm64 candidate passes the required local selections
and default battery.
The handoff must identify the accepted source/build, equipment and run IDs and
distinguish deterministic, native and source-path evidence. Its status is
"validated on the recorded Apple Silicon configuration; actual sleep/wake
validation pending" until that follow-up has its own result. State native arm64
applicability; architecture enforcement belongs to the separate Apple Silicon
investigation and there is no pending Intel clock gate.
Future native validation extends or revises the evidence using new observations;
it does not rewrite the local run's original result.

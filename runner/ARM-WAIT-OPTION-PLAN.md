# ARM worker wait option plan

Determine whether an ARM event-wait instruction can make PW's held workers
better neighbors while preserving their ability to witness under restrictive
profiles. First establish native applicability and autonomous progress; only
then consider production integration and resource benefit. This is an
exploration with explicit negative outcomes, not an assumption that Apple
Silicon supplies a usable scheduler sleep.

The [worker wait exploration plan](WORKER-WAIT-EXPLORATION-PLAN.md) addresses
shorter holds and less repeated work without a new waiting dependency. This
plan separately continues [outflow direction 3](../records/FOOTPRINT-OUTFLOW.md#direction-3-pace-the-sandboxed-workers-waits).
Its `nanosleep` and direct `mach_wait_until` trials both failed under the tested
deny-default profiles. Do not retry those calls in a loop, broaden the specimen
profile, or hide pre-application resources to make this alternative pass.

## Coordination with worker wait exploration

The worker exploration's ready builds and native trials have scheduling
priority. Its order is quantitative pilot, branch 2 (host delay), branch 1
(preparation), then branch 3 (scan work and separately selected hint tails).
Read-only ARM contract research, checker design and pinned-source review can
proceed in parallel. ARM disposable-child applicability builds and trials use
time the worker exploration is not using, under the same serialized checkout
execution rule and with separate builds, output directories and acceptance
records. Do not interpret priority as waiting for the other plan to retire.

Branches 1 and 2 must be accepted or rejected, with dispositions recorded in
the outflow, before this plan freezes a production comparison baseline, with
one exception: if branch 1 is blocked solely on a tradeoff decision, the
coordinator may freeze on accepted production source with that candidate
excluded. Record the exclusion in the outflow and ARM acceptance record and
leave branch 1 blocked. Include all accepted changes; if branch 1 later lands,
freeze a new baseline and repeat affected comparisons. The worker plan's
[deferral and exclusion rules](WORKER-WAIT-EXPLORATION-PLAN.md#deferred-work-and-baseline-exclusions)
preserve branch 2's disposition requirement and correctness/ownership gates.

Successful native qualification reserves the corresponding release or activation
tail for this plan's deployment and benefit evaluation. Accepted ARM adoption
supersedes hint tuning there; closing that ARM path without adoption returns
the tail to the worker exploration. Pending qualification does neither by
itself. When qualification awaits an external observation or user availability,
the coordinator may record an explicit deferral for that wait and open hint
tuning. Retain ARM's pending status and outstanding observation in the outflow
and affected acceptance records. Resuming after an accepted hint change needs
a new baseline incorporating it and repeated affected comparisons. Track the
two wait roles separately; release success cannot resolve the question for
parked activation.

Use the shared [pilot record](../records/WORKER-WAIT-PILOT.md) decomposition to
choose the benefit metric and minimum worthwhile improvement. This pilot is measured in an arranged
quiet window with stable power conditions; it is not the later ARM comparison
baseline. Its production-shaped timestamps decompose held time; extended
held-footprint runs supply separately labeled CPU rates, not production hold
durations. Recheck the threshold's rationale against the accepted source at
baseline freeze, before candidate comparisons. A later accepted host, scan or
hint change affecting the comparison requires a new baseline and candidate
comparison on the same source foundation, not reuse across source changes.

## What the primary sources support

These are research leads, not observations of the installed Mac. The XNU links
pin Apple's `xnu-12377.1.9` import at commit
`f6217f891ac0bb64f3d375211650a4c1ff8ca1ea`, reviewed on 2026-11-07. Relate that
source, or a newer pinned revision, to the tested OS before using it as an
implementation premise.

| Source | Supported premise and limit |
| --- | --- |
| [Arm Generic Timer, version 1.3, section 4.7](https://documentation-service.arm.com/static/65fac6957bcc0c1c661b36c0) | A configured timer event stream can bound a WFE low-power interval independently of another process. Configuration is a prerequisite. |
| [Apple XNU machine_routines.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/machine_routines.c), `wfe_timeout_configure`, `wfe_timeout_init`, `_enable_timebase_event_stream` | XNU source configures periodic events with a nominal microsecond target, a boot-argument override and timer-bit rounding. It also contains Apple-specific timer access variants. This is not a public event-period guarantee or proof of the installed binary. |
| [Apple XNU arm_init.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm/arm_init.c), [proc_reg.h](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/proc_reg.h), [start.s](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/start.s) | Initialization/resume paths enable the stream; the default SCTLR setting does not request trapping EL0 WFE. Other builds and higher-level trap controls still need qualification. |
| [Apple XNU cpu_capabilities.h](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm/cpu_capabilities.h) | `kHasEvent` is a clue inside an explicitly Apple-internal interface, not a public feature-detection contract to adopt silently. |
| [Arm feature names, FEAT_WFxT](https://documentation-service.arm.com/static/668bf39069e89f01e39c46dd) | WFET/WFIT add a local timeout based on `CNTVCT_EL0`; the feature is optional from Armv8.6 and mandatory from Armv8.7. This establishes no Apple model's support. |
| [Arm HCR_EL2](https://support.arm.com/documentation/ddi0595/2021-03/AArch64-Registers/HCR-EL2--Hypervisor-Configuration-Register) and [power-efficient locks](https://support.arm.com/documentation/100934/0100/Power-efficient-locks) | Trap controls and event/monitor behavior matter. An instruction returning, or a normal shared-memory store occurring, is insufficient to prove a useful bounded wait. |
| [Apple Silicon performance guidance](https://developer.apple.com/documentation/apple-silicon/tuning-your-code-s-performance-for-apple-silicon) | Active waiting can occupy a core needed by productive work. Measure available execution capacity separately from instruction activity. |

No public Apple WFE period guarantee or WFET availability contract was
established during preparation of this plan. Establishing a usable platform
contract is work in the plan, not a presumption concealed in a fallback.

## 1. Establish the wake and deployment contracts

Investigate **one WFE after an unsuccessful poll** first. The XNU event stream
is a plausible wake source independent of the host. Do not replace a thousand
`yield` hints with a thousand WFEs: that could substantially lengthen the gap
between protocol checks. Do not add SEV broadcasts, exclusive-monitor polling,
worker timers, helper threads or a new wake channel to this first candidate.

Write down the intended intrinsic wake bound, event source, EL0 assumptions,
supported hardware/OS scope and detection method. Distinguish an architectural/
source argument from finite observed timings and the wall-clock interval between
protocol checks: OS descheduling can lengthen that interval.
The wake argument must survive a host that stops publishing or disappears.
The independent parent watchdog contains an experiment; it cannot substitute
for the worker's own cutoff and cancellation progress in production.

Testing may proceed in a disposable child while the deployment contract remains
unresolved. Production enablement requires a defensible capability/configuration
gate covering the event source and its bound, including migration and resume.
A short startup trial or an internal feature bit alone is insufficient.
If no such gate can be established, retain the qualification result and stop
short of production adoption. Observed timings plus model/OS identity and
`kHasEvent` alone yield a test-only result. Adopting a private OS implementation
dependency requires a separate explicit deployment-scope decision. Unknown
configurations retain the existing wait; fallback selection must happen before
entering an instruction that could stall.
Do not build a broad model/OS allowlist from one machine's successful trial.

Investigate **WFET as a separate alternative** if WFE's wake contract or
measured behavior is unsuitable, or if a supported explicit timeout offers a
clearer contract. It need not wait for an API dependency failure. Require a
defensible feature gate, EL0 instruction and counter access, and inspected
instruction encoding. Compiler acceptance and `arm64` naming are insufficient.
Do not add WFIT as another unbounded search branch.

WFET's deadline belongs to `CNTVCT_EL0`. Establish counter frequency, offsets,
access ordering, checked conversion/overflow and sleep/resume behavior; do not
pass a Mach deadline directly. Keep the worker's existing continuous clock as
the authoritative cutoff/allowance source and recheck it after every return.
Bound each timeout by remaining applicable allowances without resetting them.
An inability to relate the clocks safely blocks WFET integration.

## 2. Qualify instructions in disposable native children

Build an opt-in harness through the test dispatcher, separate from the signed
production app. Reuse the independent observation patterns of
[native-pause applicability](../tests/suites/runner_c_worker_harness/README.md#native-pause-applicability),
not its API-return oracle: WFE has no success return value. Record source and
binary hashes, disassembly, toolchain/SDK, macOS/kernel, hardware, power state,
clock calibration and every resource acquired before application. Explain any
test-only signal handler or shared reporting region.

Use fresh children for explicitly unapplied, version-2 allow-default, bare
version-2 deny-default, and version-2 deny-default plus file-read-data profiles.
Execute the first explicit candidate wait after application without a warm-up
that creates a dependency. Retain application facts, entered/returned markers,
native clock samples, parent-observed live generation, signal/exception status,
exit and independently observed reap. Start with three repetitions per profile
and condition; qualification failure stops that candidate before integration.
Retain first-execution observations in qualification. The performance protocol's
excluded initial run does not discard a qualification failure or authorize
warming a wait before applying the policy in a measured child.

Use a supervisor with owned-child cleanup and a declared finite watchdog. It
must survive the loss of the experimental host and retain the child's ending.
Include conditions for:

- Repeated waits with the experimental host silent, no explicit event signal,
  and release withheld until the worker's own cutoff ends the wait.
- Release just before and just after wait entry; already-published release;
  cancellation; invalid/expired clock; future ordinal; spurious/immediate
  returns; a separately controlled interruption; and experimental-host loss.
- A real validator query against the held, successfully applied generation,
  followed by collection closure, release and acknowledgement. Use an
  acknowledged hold established before querying, rather than searching for a
  short-lived PID after launch. Retain deny and allow query observations without
  interpreting them as prediction/enforcement agreement.

Keep silent progress trials free of periodic observer probes, signals and
debugger stops that could supply the very wake being investigated. Obtain
identity before/after the interval and published facts after it; separately
measure observer perturbation. Record traps, stalls and invalid observations
as failures, not successful pauses. A watchdog rescue is a failed progress
trial even when cleanup succeeds. Immediate return is allowed by a polling
protocol but proves no low-power effect or maximum wait bound on other runs.

Actual sleep/wake and migration/resume applicability need explicit evidence
before a deployment claim covering them. Controlled-clock tests establish
arithmetic only. Arrange any real sleep with the user; do not induce it
silently. A pending sleep/resume observation can block adoption while other
research continues.

Add independent valid and rejected checker fixtures for missing application,
wrong generation, no instruction execution, absent progress, rescued timeout,
missing query ordering and missing reap, including combined faults. Use a
no-op candidate to show that successful control flow cannot satisfy a resource
benefit claim. Retain expected and actual effects separately.

Unified logging is supplemental. If access fails, make the prescribed bounded
unsandboxed retry of the same query; persistent unavailability does not block
qualification supported by the direct observations above. State the attribution
limit. Silence establishes no absence, and positive log events establish only
their own event. Do not revive the generic sandbox logger as a required channel.

## 3. Integrate only a qualified, deployable candidate

Begin with `wait_for_proceed` in
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c), at its
unsuccessful tail. Preserve clock/cutoff/allowance/arithmetic checks, future
ordinal refusal before cancellation, exact ordinal acceptance, and existing
release/acquire publications. Do not delay a successful decision before its
acknowledgement or alter sampled-decision semantics. A wait return supplies
neither predicate truth nor memory ordering; run the existing decision again.

Then qualify `wait_for_activation` independently, preserving cancellation and
named/future-ordinal precedence, worker-owned cutoff, one-time excluded wait,
and inbound authority service without consumption. Include a parked recipient,
multiple issuers and self-transfer. Reject parked integration if delivery or
cutoff correctness fails or response exceeds the acceptance bound below.
**Release-only adoption is acceptable** when its own
qualification and benefit pass; a shared dependency failure invalidates both.

Keep `wait_exchange` unchanged in the first integration. It accepts an answer
before its next clock check and has a separate allowance with no phase-wait
exclusion. It needs its own live hold and precedence investigation before a
later change. Never infer correctness there from a held-release measurement.

The initial candidate relies on independent periodic or timed wakeup, not on a
host store emitting an event. If a later design proposes SEV or exclusive
loads, stop for a separate protocol design: prove publication visibility,
notification-before/after-wait races, preemption/migration, monitor clearing
and multiple predicates. Include broadcast interference and acquired authority
in that design. Preserve ordinary acquire loads in this experiment.

## 4. Establish the actual benefit

Use separate records under `records/`: `ARM-WAIT-QUALIFICATION.md` for the
declared native applicability matrix and its results, and
`ARM-WAIT-RELEASE-ACCEPTANCE.md` and `ARM-WAIT-ACTIVATION-ACCEPTANCE.md` as each
production candidate opens. Commit the qualification protocol before native
trials and each acceptance protocol before candidate comparisons. Name the
qualified mechanism, deployment gate, source/build/reader identities, workload
and hold classes, exact durations, five alternating matched pairs, uncertainty
and the primary benefit metric. Select and justify a quantitative minimum
worthwhile improvement from the shared pilot record, beyond mere detectability
given the new platform dependency, and freeze it before candidate comparisons.
Record revisions explicitly, preserving earlier frozen definitions and results;
do not amend one wait's protocol silently to fit the other's later findings.
Use the worker plan's [power, warm-up and pacing protocol](WORKER-WAIT-EXPLORATION-PLAN.md#conditions-and-the-pilot-window)
for performance comparisons: name the power state, retain an excluded initial
execution of each staged artifact, and separate rapid from idle-gap trials.
Do not keep an unreported busy helper active to erase idle behavior. New
workloads and checker fixtures needed for these observations are in scope,
under the existing test registration and fixture-ownership rules.
Isolated prototype measurements may proceed with an unresolved deployment gate;
they cannot authorize adoption. Use the held-footprint controls and generation-qualified samples
described in [change verification](../tests/CHANGE-VERIFICATION.md#footprint-observations).
Freeze a separate baseline for release and parked integration. The current
held-footprint reader requires worker CPU to exceed a matched sleeper; that is
a baseline characterization, not a requirement for a quieter candidate. The
first plan needing quieter-candidate comparisons builds the shared
mechanism-neutral CPU reader before freezing its baseline; this need not be a pilot
deliverable. Reuse it here with independent acceptance/rejection controls for
generation, observer sensitivity, intervals and effects. Response comparisons
also need the separate timestamp reader and the worker plan's
[resolution gate](WORKER-WAIT-EXPLORATION-PLAN.md#instruments-and-response-resolution):
at most 0.5 ms combined timing uncertainty for the 2 ms regression criterion.
Each acceptance record identifies every reader it uses; both sides use the
same versions. A reader change invalidates affected frozen comparisons until
re-frozen with that reader. Candidate-specific benefit criteria remain separate
from measurement validity. Preserve the old busy-worker reader and its evidence.

CPU time, instruction activity, available CPU capacity, energy and wake
coalescing are different claims. A WFE thread may perform less work while
remaining scheduled. Report whole-request and per-generation CPU, completed
workload/held durations, response and host/validator/observer cost. Where
reliable, add instruction/cycle counters, context switches, wake activity and
energy. If claiming more capacity for other work, use one bounded competing
workload and retain its progress; do not saturate all cores. Counter or energy
unavailability stays visible rather than being replaced by an opcode count.

For adoption require the declared worthwhile improvement after accounting for
uncertainty in at least one preselected CPU-demand, peer-progress or energy
metric in every matched pair of the claimed workload. Requiring every pair is
deliberately conservative; an inconclusive result is not proof of no effect and
does not authorize open-ended reruns. Reduced instruction work alone is a useful research
result but does not justify deploying a new platform dependency under this
plan. The earlier sleep proposal's CPU-reduction threshold is not silently
met by executing WFE; any claimed energy benefit must have energy evidence.

For each changed role and applicable release, activation, cancellation, cutoff
and inbound-delivery response, allow at most 2 ms additional worst-observed
latency, comparing candidate upper bounds with baseline lower bounds. Keep
all existing timing allowances and witness checks. This is a finite trial
criterion, not a hard scheduling guarantee. Investigate any resolved worsening
of aggregate CPU, whole-request latency, resource residence, wake activity or
peer progress. An unresolved tradeoff blocks adoption of that branch, not the
recording of its qualification result. Never accept savings caused by reduced
query coverage, delayed observation or work shifted to an unmeasured process.

## Verification, operation and retirement

Run existing release/activation precedence, timing, clock-fault and cutoff
controls plus the new applicability/checker controls. A changed wait requires
`witness_contract/order_barrier_mutations`; failed mutation application/build is
not successful detection. Parked changes additionally require authority-binding,
extension-boundary, actor-composition and actor-timing coverage. Complete the
signed build, worker-identity regeneration, default battery and required
source/ABI checks before accepting production changes. Register new cases with
their actual equipment and keep unsupported applicability results explicit;
do not turn the failed native-pause case into a passing prerequisite.

Follow [runner capability review](AGENTS.md#reviewing-a-new-capability) for any
new instruction/counter dependency and update architecture/worker and footprint
accounts through their owning generators. Retain the support scope and fallback
reason in evidence without inventing specimen-policy conclusions. If the
production evidence shape needs to change, apply the wire/evidence contracts.

The coordinator is whoever is running the plan and owns source integration,
native scheduling and acceptance.
Read-only architecture and checker review may run in parallel; builds and native
trials run serially with compiler concurrency at most two. Start pilots with at
most two busy processes, counting controls and any competitor. Existing actor
footprint/timing cases exceed that pilot cap; inspect and announce their load,
then arrange a bounded quiet window or leave acceptance pending. Do not shrink
required cases while claiming their original coverage. Capture power/sleep
state, never pair across a power transition, and reduce load on contention.
Request a quiet window for sensitive comparisons and announce its start/end.
Arrange actual sleep or a competing-workload trial with the user before use.
Follow [test retention and ownership rules](../tests/AGENTS.md); preserve partial
observations and unfinished cleanup rather than replacing them with a summary.
Exploration runs may remain unpinned, with existing pins left in place. Defer
pruning and decisions about exceeding the normal pin maximum until acceptance.
If required raw evidence disappears, repeat the affected observations and
re-freeze comparisons where necessary; summaries alone cannot retain credit.
Keep raw output under the dispatcher rather than moving it into `records/`.

Close with one of: unsupported equipment; unestablished independent wake or
deployment contract; qualified but no worthwhile measured benefit; release-only
improvement; or independently qualified release and parked improvement. Preserve
the narrow result, contrary trials and apparatus limits in the outflow. Commit
accepted current-behavior documentation and implementation, or the negative
result with production unchanged. Retire this plan and its completed acceptance
records after disposition; preserve needed raw observations through the retention
helpers. Keep the shared pilot while either plan needs it and the outflow while
another associated direction needs it. Once both plans retire, delete the pilot
record after preserving lasting conclusions and evidence references where they
belong; do not create a separate records archive. Raw-evidence retention is
decided at acceptance. Before deleting either plan, remove its
reciprocal links from the remaining plan and retain coordination facts still
needed there. A genuinely pending observation keeps its branch and plan active
unless that scope is explicitly closed; it is not a negative qualification result.

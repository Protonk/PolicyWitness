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

## Status and shared rules

**Deferred**, alongside hint tuning. The worker plan's
[host follow-on round](WORKER-WAIT-EXPLORATION-PLAN.md#host-follow-on-round)
is complete: HOST-04 and HOST-06 are accepted; HOST-05 is closed without
adoption. Deferral remains a priority decision, not an ARM qualification result.
Record explicit resumption before proceeding, then freeze a fresh production
baseline containing HOST-04 and HOST-06 and excluding HOST-05. Historical host
measurements do not substitute for that baseline.

The worker plan owns [resumption, baseline and tail ownership](WORKER-WAIT-EXPLORATION-PLAN.md#resuming-deferred-work),
[measurement resolution](WORKER-WAIT-EXPLORATION-PLAN.md#instruments-and-response-resolution),
[conditions and pacing](WORKER-WAIT-EXPLORATION-PLAN.md#conditions-and-the-pilot-window),
[acceptance](WORKER-WAIT-EXPLORATION-PLAN.md#acceptance),
[verification and operation](WORKER-WAIT-EXPLORATION-PLAN.md#verification-and-execution),
and [retention and closeout](WORKER-WAIT-EXPLORATION-PLAN.md#closeout).
Use those rules here, including role-specific baselines, five alternating
matched pairs, same-version readers and re-freezing affected comparisons.
A qualified ARM role reserves its tail for deployment/benefit evaluation;
adoption supersedes hint tuning there, closure without adoption returns it.
Pending qualification permits hint work only through an explicit deferral
under the resumption rule.

## Primary-source leads

These are research leads, not installed-Mac observations. XNU links pin
`xnu-12377.1.9`, commit `f6217f891ac0bb64f3d375211650a4c1ff8ca1ea`, reviewed
2026-11-07. Relate that source, or a newer pinned revision, to the tested OS.

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

## 1. Establish wake and deployment contracts

Try **one WFE after an unsuccessful poll** first, using an independent periodic
wake source. Do not substitute a thousand WFEs for a thousand yield hints or
add SEV, exclusive-monitor polling, timers, helper threads or another wake
channel. Record the intrinsic wake bound, event source, EL0 assumptions,
hardware/OS scope and detection method. Distinguish architectural/source support,
finite timings and time between protocol checks, which descheduling can extend.

The wake argument must survive a host that stops publishing or disappears.
A parent watchdog contains a trial; it cannot supply production cutoff or
cancellation progress. Disposable-child experiments may proceed while the
deployment gate is unresolved. Production enablement requires a defensible
capability/configuration gate covering the event source and bound, including
migration and resume. Startup trials, model/OS identity and `kHasEvent` alone
support only a test result. A private-OS dependency needs an explicit
deployment-scope decision. Unknown configurations select the existing wait
before entering an instruction that could stall; do not extrapolate an
allowlist from one machine.

Try **WFET as the sole alternative** if WFE's contract/behavior is unsuitable or
a supported explicit timeout offers a clearer contract; API failure is not a
prerequisite. Establish feature detection, EL0 instruction/counter access and
actual instruction encoding. Compiler acceptance and `arm64` naming do not
qualify it; WFIT is outside this exploration.

WFET deadlines use `CNTVCT_EL0`: establish frequency, offsets, access ordering,
checked conversion/overflow and sleep/resume behavior rather than passing a Mach
deadline directly. Keep the continuous clock authoritative, bound each timeout
by remaining applicable allowances without resetting them, and recheck after
every return. An unsafe clock relationship blocks integration.

## 2. Qualify disposable native children

Use a dispatcher-owned opt-in harness and the independent observations of
[native-pause applicability](../tests/suites/runner_c_worker_harness/README.md#native-pause-applicability),
not its return-code oracle: WFE has no success result. Retain equipment,
source/binary identities, disassembly, clock calibration and all pre-application
resources, explaining test-only handlers and reporting memory.

Use fresh children for explicitly unapplied, version-2 allow-default, bare
version-2 deny-default, and version-2 deny-default plus file-read-data profiles.
Execute the first explicit wait after application without dependency-creating
warm-up. Start with **three repetitions per profile and condition**. Retain
application, entered/returned markers, native clock samples, live generation,
signal/exception status, exit and independently observed reap. Qualification
failure stops that candidate before integration. Performance warm-up exclusions
never discard qualification failures or permit pre-apply wait warming.

The supervisor owns cleanup, has a finite declared watchdog, survives loss of
the experimental host and retains the child's ending. Cover:

- Repeated waits with a silent host, no explicit event signal and release
  withheld until the worker's own cutoff ends waiting.
- Release before/after entry and already published; cancellation; invalid or
  expired clock; future ordinal; spurious/immediate returns; controlled
  interruption; and host loss.
- A real validator querying the successfully applied, held generation, followed
  by collection closure, release and acknowledgement. Establish the acknowledged
  hold before querying; retain allow/deny observations without an agreement claim.

Silent-progress trials exclude periodic inspection, signals and debugger stops
that could supply wakes. Establish identity before/after, collect publications
afterward and measure observer perturbation separately. Traps, stalls and invalid
observations fail qualification. Watchdog rescue fails progress even if cleanup
succeeds. Immediate return proves neither low-power behavior nor a wake bound.

Deployment claims covering actual sleep/wake and migration/resume need explicit
evidence; clock controls establish arithmetic only. Arrange real sleep with the
user. A pending observation can block adoption without ending other research.

Independent valid/rejected reader fixtures cover missing application, wrong
generation, unexecuted instruction, absent progress, rescued timeout, missing
query ordering/reap and combined faults. A no-op candidate must not satisfy the
resource-benefit claim. Unified logs remain supplemental: use the prescribed
bounded retry if refused, preserve attribution limits, and do not make silence
or unavailable logging a qualification oracle.

## 3. Integrate qualified, deployable roles separately

Start at the unsuccessful tail of `wait_for_proceed`. Preserve its decision
order, allowances and release/acquire publications; return to the existing
decision after every wait. A wake supplies neither predicate truth nor memory
ordering, and no wait precedes acknowledgement of an already successful decision.

Qualify `wait_for_activation` independently: cancellation/named-ordinal
precedence, worker cutoff, one-time wait exclusion and inbound service without
consumption remain essential. Cover a parked recipient, multiple issuers and
self-transfer. Release-only adoption is acceptable; a shared dependency failure
invalidates both roles. Keep `wait_exchange` unchanged: its acknowledgement
precedes the clock check, it has its own allowance and no phase-wait exclusion.
It needs a separate live hold/precedence investigation.

Retain ordinary acquire loads. SEV or exclusive loads would require a separate
protocol design for publication visibility, notification races, preemption,
migration, monitor clearing, multiple predicates, broadcast interference and
acquired authority.

## 4. Establish worthwhile benefit

Commit and freeze `records/ARM-WAIT-QUALIFICATION.md` before native qualification and
`ARM-WAIT-RELEASE-ACCEPTANCE.md` / `ARM-WAIT-ACTIVATION-ACCEPTANCE.md` before
their comparisons. Record mechanism, deployment gate, workload/hold classes,
durations, readers and the common measurement protocol. Use the
[shared pilot](../records/WORKER-WAIT-PILOT.md) to justify a quantitative minimum
worthwhile gain beyond detectability, then recheck its rationale on the accepted
baseline. Historical pilot timings are not the ARM baseline. Prototype benefit
measurements with an unresolved deployment gate cannot authorize adoption.

Use a mechanism-neutral CPU reader: the old held-footprint requirement that a
worker exceed its sleeping control characterizes busy waiting, not a quieter
candidate. Preserve that reader and evidence; independently control its successor
for generation, sensitivity, interval and effects. Use the common timestamp
reader's complete coverage/publication brackets and
[resolution gate](WORKER-WAIT-EXPLORATION-PLAN.md#instruments-and-response-resolution).

Distinguish CPU time, instruction work, available execution capacity, energy and
wake coalescing. A WFE thread can do less work while remaining scheduled. Report
whole-request/per-generation CPU, completed workload and hold duration, response,
and host/validator/observer cost. Add counters, context switches, wakes or energy
only where reliable. A capacity claim needs one bounded competing workload's
observed progress, arranged with the user; do not saturate all cores. Missing
counters/energy evidence remain missing.

Adoption requires the predeclared worthwhile improvement beyond uncertainty in
at least one selected CPU-demand, peer-progress or energy metric **in every
matched pair** of the claimed workload. Instruction reduction alone is a useful
research result, insufficient for this new platform dependency. Inconclusive
results authorize no open-ended reruns.

For each changed role, apply the common uncertainty-expanded **2 ms response
regression bound** to release, activation, cancellation, cutoff and inbound
delivery where applicable. This is a finite-trial criterion, not a scheduling
guarantee. Investigate resolved worsening of aggregate CPU, whole-request time,
resource residence, wakes or peer progress; unresolved tradeoffs block that
branch's adoption. Savings cannot come from reduced query coverage, delayed
observation or shifting work to an unmeasured process.

## Verification and disposition

Add applicability/reader controls to existing precedence, timing, clock-fault,
cutoff and order-barrier mutation coverage. Parked changes also need authority
binding, extension boundaries, actor composition and timing. Follow the common
[verification](WORKER-WAIT-EXPLORATION-PLAN.md#verification-and-execution) and
[capability review](AGENTS.md#reviewing-a-new-capability) for instruction/counter
dependencies; retain support scope and fallback reason without specimen-policy
attribution. A failed native-pause case is not a passing prerequisite.

Close as unsupported equipment; unestablished independent wake/deployment;
qualified without worthwhile benefit; release-only improvement; or independently
qualified release and parked improvement. Preserve contrary trials and apparatus
limits in the outflow, then follow common
[closeout](WORKER-WAIT-EXPLORATION-PLAN.md#closeout). A genuinely pending
observation remains pending unless explicitly closed; it is not a negative
qualification result.

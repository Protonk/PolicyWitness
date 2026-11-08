# ARM wait qualification

This record belongs to the [ARM option plan](../runner/ARM-WAIT-OPTION-PLAN.md).
The user authorized resumption through disposition and acceptance of ARM and
hint candidates by the coordinator. Production baseline is `1471b02e`, with
native identity `aaa8056c79c242fde5740449049246e3ed88facdc2c8efd143f6344c856da8e5`.
An unrelated planning document is modified; this is not a pristine tree claim.

## Stages and fixed first-use screen

First establish applicability in a small disposable-child screen, then extend
successful candidates to protocol qualification. The screen cannot authorize
production adoption. Freeze its implementation identities before execution.

Try one WFE per unsuccessful pass first. Test three fresh children in each of
unapplied, version-2 allow-default, bare version-2 deny-default and version-2
deny-default with file-read-data. No explicit WFE/WFET warm-up before application.
Each child publishes its applied state, instruction entry and returned-pass
counts into prepared shared storage. Following an initial ownership observation,
the supervisor leaves the child uninspected and unsignalled for the bounded
silent interval. The child must stop on its own continuous-clock cutoff;
the supervisor's watchdog contains a stall but never credits progress. Retain
entry/return timing, live generation at both endpoints, actual signal/exit and
owned reap. Three repetitions per profile are fixed; no sampling extension to
obtain a preferred outcome. Missing observations or native failure withhold
applicability. This first screen does not measure real system sleep or migration.

WFET is the sole alternative if WFE's wake/deployment contract is unestablished
or behavior unsuitable. Its architectural feature and counter access require
separate evidence. Read the virtual counter frequency, use checked conversion
and addition, and preserve the continuous clock as the cutoff authority. Never
pass a Mach tick deadline directly to WFET. The first timed screen uses a
100 microsecond local timeout; an early event return is permitted and is not
credited as a full pause or scheduler sleep.

Before production enablement, independently establish release/cancellation/
cutoff/clock-fault ordering, host-loss progress, generation-qualified live queries,
closure before release, acknowledgement, and no attempt before closure. Parked
activation adds inbound service, multiple issuers and self-transfer. Qualification
of release and activation is separate; `wait_exchange` stays unchanged. Unknown
support must choose the old wait before an unsafe instruction. A private OS
dependency needs an explicit written support-scope decision. An actual
sleep/resume observation is arranged with the user if the candidate reaches
that adoption requirement. No generic log channel is required.

## Research and equipment leads

Read-only hardware queries on Mac17,3, macOS 26.7.1 (25G241), report
`hw.optional.arm.FEAT_WFxT=1` and `FEAT_ECV=1`. The first automation-sandbox
query was refused; the identical unsandboxed query succeeded. Kernel identity
is `xnu-12377.161.15.700.19~2/RELEASE_ARM64_T8142`. These observations nominate
WFET; they do not establish instruction access or a deployment contract.

The plan's pinned XNU source configures an event stream with a boot-argument
override; no fixed user-space WFE wake guarantee has been established. Arm's
architecture supplies the conditional event-stream argument and the optional
WFET local timeout. [Apple's macOS 15 release notes](https://developer.apple.com/documentation/macos-release-notes/macos-15-release-notes)
document a counter-frequency change on newer hardware and SDK-linked behavior,
with virtual-machine exceptions. Therefore frequency, counter relationship and
scope must be observed; model name and a hard-coded frequency are insufficient.

## Measurement and disposition gates

Prepare a mechanism-neutral held-CPU reader without weakening the historical
busy-worker oracle. Independent controls retain generation, effects, clock and
sampling sensitivity while allowing a worker below the sleeping-control count.
Production-shaped timestamps and artificial extended-hold CPU observations stay
separate. Whole-request and host/validator/observer cost remain visible.

Freeze role-specific acceptance records with a worthwhile quantitative benefit
before candidate comparisons, informed by a fresh baseline. Five alternating
matched pairs per claimed workload, no open-ended reruns. The common 2 ms
response-regression and 0.5 ms combined-uncertainty bounds remain unchanged.
Instruction counts alone cannot justify the ARM dependency. Deployment or
benefit failure closes that role without adoption and opens its hint candidate;
pending observations require an explicit deferral rather than an invented failure.

All raw evidence will be dispatcher-owned, gitignored and available only in the
local checkout. Builds/native trials remain serial, compiler concurrency at
most two, initial trials at most two busy processes, with announced bounded
windows and independent owned cleanup.

## First-use screen implementation bounds

The screen uses a 500 ms child-owned cutoff. The supervisor observes the live
generation and CPU before go and after a silent interval of at least 150 ms,
then sleeps another 400 ms without child inspection or publication. Completion
must be recorded by the child within 550 ms of its start, with the second
endpoint before completion. All 64 retained first instruction brackets and
aggregate pass/max-span counters are required. The eight-second supervisor
watchdog plus three-second cleanup reserve fit within a prepared, announced
180-second window for twelve children. The setup can wait at the identity gate
for five minutes; no native child executes before release. These bounds screen
applicability and do not replace the integrated 2 ms response criterion.

Preparation controls `arm-preparation-controls-01`
(`20261108T221623Z_a4537b39`) passed all three cases: the ARM screen oracle,
neutral held-CPU oracle and unchanged historical held-footprint controls.
`arm-wfe-screen-01` failed at compilation before any native trial: the installed
assembler rejects `.arch_extension wfxt`. The isolated WFET helper now uses
fixed-register X17 with encoding `d5031011`, independently specified by
[LLVM's instruction encoding test](https://github.com/llvm/llvm-project/blob/main/llvm/test/MC/AArch64/armv8.7a-wfxt.s).
The screen retains disassembly for an actual-byte review. This compilation
repair is not an instruction applicability observation or a broader ISA change.

## Prepared WFE screen

`arm-wfe-screen-02` is staged from `cc5eeeaf`, with native trials still held
at its gate while this identity is committed. Disassembly shows the WFE helper
executing `wfe; ret`, and the separate WFET helper moving its argument to X17
and executing `wfet x17; ret`; call sites select exactly one helper per pass.

| Input | SHA-256 |
| --- | --- |
| Staged `arm-wait` executable | `c344a7294ca92d6f11b898eaba05b43ab8cdcadb24bcf2bc39525f410793aea8` |
| `opt_in/arm_wait.c` | `09f8e174b5ad0424888fccf324c874e4deaeb8bd5550c864bf21d0b8d774b5d3` |
| `check_arm_wait.py` | `11f9551c246ea04ca001fe7bce957c5cb01729e42c69e836a25fe6239e4b4c97` |
| `arm_wait_driver.py` | `6194808dc9136087ab82b17c1f3c900991c365a12ac3b1667c7954c1479095af` |

Paths are under `tests/suites/runner_c_worker_harness/`, with staged artifacts
under `tests/out/runs/arm-wfe-screen-02/suites/runner_c_worker_harness/arm_wait/artifacts/`.
Power is AC, battery full; an observed Xcode process briefly used about 0.4 of
one core during staging. This is an applicability screen, not a matched resource
comparison. The three-minute maximum window contains one measured child at a time.

## WFE result and alternative trigger

`arm-wfe-screen-02` (`20261108T221744Z_ae4c13b8`) passed both registered cases;
all twelve children passed the screen, with no rescue, unsettled cleanup or
recorded system sleep. Native trials took 7.294 seconds. All profiles executed
WFE and reached their own cutoff. First brackets were 0–83.333 ns at the Mach
clock's resolution, while the repeated loop made approximately 375,000 passes
in 500 ms. A zero first bracket is below resolution, not proof of no instruction.
The largest recorded per-pass bracket was 3.336 ms; descheduling is included.
CPU observations stayed near elapsed time and are diagnostic, not a matched
benefit or response qualification.

WFE deployment remains unestablished: the pinned kernel's configurable event
stream and internal capability flag do not provide a supported user-space
selection rule for an independent maximum wake period across boot configuration,
migration and resume. A finite startup probe cannot supply that contract. Close
the untimed WFE production option on that ground, while preserving its positive
first-use observation. This invokes the plan's sole timed alternative, WFET,
whose local deadline can avoid dependence on the periodic event interval.

The WFET first-use screen is staged as `arm-wfet-screen-01` using the same
source, reader, disassembled helpers and numerical rules. Its exact executable
identity is frozen before gate release below. No integrated role or deployment
credit transfers from WFE.

WFET staged binary SHA-256 is
`c344a7294ca92d6f11b898eaba05b43ab8cdcadb24bcf2bc39525f410793aea8`, identical
to the WFE screen executable; only the selected argument differs. All WFE
children read `CNTFRQ_EL0=24000000`. This observed frequency, not a model-based
expectation of 1 GHz, supplies the timed conversion. Its configuration cause
has not been established.

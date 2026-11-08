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

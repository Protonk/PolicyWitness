# Worker wait qualification

These live opt-in cases exercise candidate worker waits. Their default reader
controls belong to the [direct worker harness](../runner_c_worker_harness/README.md).

## Native pause applicability

`native_pause` is an opt-in qualification gate for a requested 1 ms pause,
not a production-wait or performance acceptance test. It compiles the worker's
timing setup into a standalone probe; every invocation forks a fresh child,
sets up timing before apply, and makes its first explicit pause after apply.
The four configurations are allow-default, bare version-2 deny-default,
version-2 deny-default plus file-read-data, and explicitly unapplied.
There are three repetitions of ordinary and signal-interrupted modes per
configuration. Each ordinary child requests 64 pauses; an unexpected native
failure stops that child after preserving the result. No refused pause is
retried. The interruption mode leaves first use alone, then sends SIGUSR1
from the observing parent. The handler is test equipment installed before
apply. Neither mode restarts a remainder.

Select with `tests/run.sh --case worker_wait_qualification/native_pause`.
`PW_NATIVE_PAUSE_PRIMITIVE=nanosleep` is the default; the only alternative is
`PW_NATIVE_PAUSE_PRIMITIVE=mach_wait_until`. Mach deadlines use absolute ticks
from a fresh `mach_absolute_time` read and checked addition; continuous ticks
measure elapsed time. Actual system sleep/wake is not exercised.
A complete measurement that records a refusal yields an unfavorable enforced
qualification and exits nonzero. A short record without a terminal native
return, a missing child or an unconfirmed reap invalidates the measurement
and withholds the judgment.

Artifacts retain per-call native result/errno and continuous-time brackets,
parent libproc CPU counters and their timebase, bracketing live generations,
application or declared unapplied state, delivered signals, exit and reap,
installed disassembly and platform/power state. A generous independent CPU
margin distinguishes an idle interval from continuous execution in ordinary
controls; it does not establish the integrated 90% reduction or a response
time guarantee. First explicit call does not exclude loader/library use.
The installed libc initialization and fork-child call paths are inspected
separately so inspection cannot warm the measured children.

The bounded unified-log query and a separate denied file-open control are
supplemental. `summary.json` distinguishes unavailable collection, an
unobserved positive control and observed PID events. None supplies general
absence or sandbox-cause attribution. Run in an unsandboxed shell for process
inspection and native policy application. The default `native_pause_controls`
uses independent constructed evidence to accept both primitives, reject missing
or combined required observations despite unavailable logs, and distinguish
log availability from positive-control observation. Live PID queries of an
integrated candidate, barrier ordering and matched response/CPU acceptance
remain separate requirements before changing production waits.

## ARM wait first-use screen

The opt-in `arm_wait` case is a smaller applicability screen for WFE and WFET,
with independent default `arm_wait_controls`. It compiles the production
timing setup into a disposable supervisor/child fixture; it does not alter
production waits. Each primitive has three fresh children per unapplied,
allow-default, bare deny-default and deny-default plus file-read-data profile.
No explicit ARM wait executes before application. The timed alternative reads
`CNTFRQ_EL0`, samples `CNTVCT_EL0` with an instruction barrier and constructs
a checked 100 microsecond deadline in that domain. The feature sysctl is
test equipment's pre-fork admission check, not an adopted deployment policy.

After the ready handshake and same-generation native observation, the supervisor
publishes go and remains silent for at least 150 ms: no PID inspection, waitpid,
signal or publication. It records a second live CPU/generation endpoint, then
leaves the child alone for another 400 ms. The child repeatedly waits until its
own 500 ms continuous-clock cutoff, publishes its ending and waits for leave.
The supervisor's rescue/owned reap are separate observations; rescue fails the
screen. The reader requires the child's recorded ending within 550 ms and
the CPU endpoint before completion. Per-pass brackets include surrounding clock
reads; counters are diagnostic and are not a matched CPU or energy benefit.
The temporary shared report, production-size timing region, fork and observation
calls are declared fixture resources. No child signal handler or post-apply I/O
is introduced. The fixture does not establish host-loss protocol, live validator
queries, sleep/resume, migration or deployability.

Use `PW_ARM_WAIT_PRIMITIVE=wfe` or `wfet` and a fresh `PW_ARM_WAIT_GATE` with
`tests/run.sh --case worker_wait_qualification/arm_wait`. An unset or already
occupied gate path leaves the selected case unrun. After the build and source
and disassembly capture, `prepared.json` identifies the binary and token. The
coordinator releases the gate after freezing identities and announcing the
180-second maximum window. Each owned supervisor has an eight-second watchdog
and three-second cleanup reserve. A forced group containment leaves cleanup
unresolved; do not credit it as child reap. Raw source, receipts, conditions,
window and ownership remain under the dispatcher. Opt-in membership reflects
the hardware/OS-sensitive instruction trial and coordinated window; a failed
screen remains failed. Logging is not a required observable.

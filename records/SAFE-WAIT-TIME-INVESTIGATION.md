# Safe worker wait timing investigation

## Finding and recommendation

The current worker clock dependency is unsafe under the following specimen:

```scheme
(version 2)
(deny default)
(allow file-read-data)
```

The probe requests a `file-read-data` prediction with filter `NONE` and an
`open_read` attempt on `/etc/hosts`.

This investigation reproduced `clock_gettime(CLOCK_MONOTONIC)` returning
`-1/EPERM` after successful sandbox application, with matching worker-PID
`syscall-unix 116` denial events. Successful pre-application reads did not prevent
later failures. The unconditional commpage comment above `wait_for_proceed` is
incorrect on the installed system.

The preferred repair direction is **`mach_continuous_time` with an explicitly
initialized, validated timebase and checked integer arithmetic**, retaining the
worker's time-before-release-before-cancellation-before-acknowledgement sequence.
This is a supported direction for a repair, not an accepted implementation.
Its clock path has source and installed-code support and successful native
controls on the tested arm64 machine. Cross-platform validation, conversion
failure evidence, and the shared exec-accounting decision remain acceptance
work. A warm-up of `CLOCK_MONOTONIC`, an unchecked switch to `mach_absolute_time`,
or moving the release load ahead of the time check would not be justified.

No production code, protocol, generated identity, or shipped app was changed.
The experiments contain native clock probes and deterministic calls to the
existing production wait; there is **no integrated replacement-worker prototype**
and the passing suite below does not certify a replacement. The accounting issue
described below should be settled before building that prototype. P4 cleanup
ownership and timed issuance were not implemented or investigated further.

## Equipment, provenance, and retained evidence

Investigated on 2026-10-16 Pacific time (the new run IDs use 2026-10-17 UTC):

- macOS 26.7.1, build `25G241`; Darwin 25.6.0,
  `xnu-12377.161.15.700.19~2/RELEASE_ARM64_T8142`; native arm64.
- Apple clang 21.0.0, `clang-2100.3.34.2`, through the selected Xcode SDK.
  Native equipment used `-std=c11 -O2 -g -Wall -Wextra` and `-lsandbox`.
- Checkout `f467962de4c051157121c1c90c8d001969252a27`.
  The selected signed app is build 665 from clean commit
  `399de801047d4b0633ac26a8e037346651cd891d`.
  Its worker and the checked generator inputs both report identity
  `fffe4dffeb2815f4c079953f816b73ccd27ef9784b294179ec8ef7f88f734ba7`.
  The commit difference contains only plans, a record, and the retention index;
  production and test sources are unchanged. App inspection and before/after
  inventory checks passed in the live run. This is the applicability basis for
  using the existing signed build, rather than merely assuming it is current.

All run links below are gitignored evidence available only in this local
checkout. `tests/RETAINED.json` protects the two new managed runs as well as the
original. Supplementary native experiments are attached to the completed live
run under `investigation/`; they are not additional dispatcher cases or changes
to its terminal result.

| Evidence | Run ID and result |
| --- | --- |
| [Original preliminary battery](../tests/out/runs/provenance-acceptance-default-20261016/) | `20261016T021725Z_87b7a565`; original failure preserved |
| [Automation-sandbox attempt](../tests/out/runs/safe-wait-baseline-20261016/) | `20261017T052758Z_1b219b8b`; equipment/signature refusal and failed sandboxed unit setup, not runner acceptance |
| [Live baseline and attached investigation](../tests/out/runs/safe-wait-baseline-live-20261016/) | `20261017T052821Z_d7999fb1`; 45/45 dispatcher cases passed, including 439/439 assertions in the runner unit executable |

The sandboxed signature errors were rerun against the unchanged app with
`codesign --verify --strict --deep` outside the automation sandbox; verification
passed. The live selection then passed inspection. No bytes were changed to
make verification pass. Both attempts and their console transcripts are retained.

## Original failure: what it establishes

The original case's [raw envelope](../tests/out/runs/provenance-acceptance-default-20261016/suites/witness_contract/bug_report_returns_verdicts/artifacts/run.json)
identifies worker PID **66685**. The actual policy is version 2,
`(deny default)(allow file-read-data)`, with a `file-read-data/NONE` prediction
and an `/etc/hosts` open attempt. The worker published successful application,
arrival, and operation 11 failure: code 1, native kind 3, native result -1,
errno 1, detail 60000, with `proceed wait: CLOCK_MONOTONIC failed`.

The kernel event is timestamped **2026-10-15 19:27:42.442876-0700**, names
`pw-probe-runner(66685)`, and reports `deny(1) syscall-unix 116`. That timestamp
falls inside the client span, **02:27:42.437–02:27:42.482 UTC**, not merely inside
the two-second padded log search. The [published syscall table](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/syscalls.master)
maps 116 to `gettimeofday`.

There was no release, acknowledgement, completed action, or validator invocation.
The unavailable prediction and attempt are explicitly synthetic; order is
`unestablished`. The host independently recorded a clean reap with exit code 0,
an exit request, and no termination request. Exit zero did not conceal the
published failure. The original envelope uses response schema 21; the current
baseline uses 22. It remains historical evidence, not a current-schema fixture.

That event alone supplies no stack, clock-call ordinal, or commpage state. It
cannot distinguish the first proceed read from a later read or identify which
fallback condition fired. The library explanation below is separate evidence.

## Clock path: source, installed code, and live observations

Apple's [Libc clock implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/gen/clock_gettime.c)
implements `CLOCK_MONOTONIC` using boot-time information and `gettimeofday`;
boot-time lookup itself has a sysctl fallback. Its raw monotonic clock instead
uses `mach_continuous_time` and Mach timebase conversion.
[The gettimeofday wrapper](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/sys/gettimeofday.c)
tries the commpage and falls back to the Unix syscall on failure.
[The commpage implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/__commpage_gettimeofday.c)
can refuse a zero timestamp, an age of at least one second, or an unrepresentable
seconds value. These are runtime checks, not a one-time initialization promise.

The immutable source snapshots and hashes are retained in
`investigation/platform/platform-sources.json`. Public source is not claimed
to be the exact source release of this installed OS. Separately retained LLDB
disassembly confirms the relevant installed branches, including the syscall
fallback, the commpage age/zero checks, and the raw clock's conversion. The
loaded image UUIDs were:

- `libsystem_c.dylib`: `3498CA79-EF40-3587-AD44-75187CEE7D95`.
- `libsystem_kernel.dylib`: `EE805B14-29F2-360D-9A2C-3221A1211833`.

LLDB used separate disposable processes, stopped before `main`, and killed them
after inspection; their exit observations are in the transcripts. It did not
instrument the measured first-use runs.

The [native probe](safe-wait-time/clock_probe.c) launches a fresh parent process
for every condition, then forks one child that compiles and applies the policy
once. The child writes only inherited shared memory during measurement. It
makes no explicit clock read before application in the cold condition; the warm
condition intentionally makes one. Parent timebase reporting occurs after the
child is reaped. Loader or libsandbox internal initialization is not observed,
so “cold” means **first explicit call by this probe**, not a proved empty library
cache. No interposition or extra policy permission was used.

Each cell below represents three processes × five million reads. Every first
post-apply read succeeded. All 72 children finished and were reaped with status
0; native success/failure counts, not that status alone, determine this table.

| Clock | Example policy, cold / warm failures | Bare deny-default, cold / warm failures | Allow-default, cold / warm failures |
| --- | ---: | ---: | ---: |
| `CLOCK_MONOTONIC` | 53 / 10 | 13 / 10 | 0 / 0 |
| `CLOCK_MONOTONIC_RAW` | 0 / 0 | 0 / 0 | 0 / 0 |
| `mach_absolute_time` | 0 / 0 | 0 / 0 | 0 / 0 |
| `mach_continuous_time` | 0 / 0 | 0 / 0 | 0 / 0 |

In total: 360 million reads, **86 failures**, all `-1/EPERM` in the ordinary
monotonic path under the two denying policies. Every one of the 12 denying
monotonic processes encountered a failure after initially succeeding. No
successful read in any condition regressed or returned zero. The 23 captured
log rows include duplicate-report summaries and identify syscall 116 for the
same 12 failed-clock PIDs; they are not 23 independently counted failures.
Raw values, first-failure indices, command times, compiler output, PIDs, reap
observations, and log JSON are retained under `investigation/native/` and
`investigation/orders/`.

Timestamp correlation is weaker for these new log rows than for the original
event: 11 ordinary rows are dated about 15.6–17.8 ms before their parent command
start, while some duplicate summaries arrive after reaping. A strict
within-process-span assertion therefore failed during evidence attachment;
`investigation/log-correlation.json` retains every offset. The PIDs match all
12 failed-clock children, but these log timestamps are not a per-call trace.
The reason for their offset/coalescing was not established. No timestamp was
adjusted to fit the measurements.

Together, these observations support the runtime `gettimeofday` fallback as the
failure mechanism. They rule out “one successful warm-up makes later reads
safe” on this machine. They do not reveal the exact commpage condition in the
original run, and successful candidate loops alone do not prove universal safety.

## Candidate assessment and arithmetic

| Candidate | Assessment |
| --- | --- |
| Keep `CLOCK_MONOTONIC`, prewarm it | Rejected by the warm-condition failures. The production worker also calls the seam before application for its exec budget. |
| `CLOCK_MONOTONIC_RAW` | Promising native observations, but delegates initialization and absolute-value conversion to libc. Installed code calls `mach_timebase_info`, then performs a 64-bit multiply before division. A name change alone does not establish initialization or overflow handling. |
| `mach_absolute_time` | Successful here, but excludes system sleep. Substitution would change deadline semantics; do not silently accept that change. |
| `mach_continuous_time` plus explicit conversion | Preferred direction. Includes system sleep, has no gettimeofday dependency in inspected paths, and permits explicit validation and bounded-delta arithmetic. It has no native error-return channel; do not fabricate a native rc/errno for locally detected invalid arithmetic. |

The SDK's retained `clock_gettime(3)` manual distinguishes raw time from adjusted
monotonic time and says not to compare raw clock values with other clock sources.
Apple's [Mach time header](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/mach/mach_time.h)
specifies that continuous time advances during sleep. No actual system sleep,
wall-clock adjustment, VM migration, or native Intel execution was induced here.

[Continuous-time source](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/mach_continuous_time.c)
selects an arm64 hardware counter plus offset when supported; its other path
combines absolute time with a repeatedly checked continuous-time offset.
In a separate installed-process inspection, the capability bytes were
`USER_TIMEBASE=3`, `CONT_HWCLOCK=1`; the installed branch uses the Apple counter
register and offset without a syscall. This is platform support beyond the
successful loops, not a guarantee for every supported system.

[Absolute-time assembly](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/mach_absolute_time.s)
also contains an arm64 kernel fallback when user timebase access is unavailable;
x86_64 uses the TSC and commpage conversion with generation checks.
[The published arm64 dispatcher](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/sleh.c#L2118-L2172)
handles the special absolute/continuous time traps directly, before ordinary
Mach syscall dispatch. This supports examining the fallback separately rather
than equating every kernel entry with the denied Unix call. That fallback was
not selected by the live candidate measurements.

[Timebase initialization](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/mach_timebase_info.c)
can issue a Mach trap when its cache is empty, which the installed disassembly
also shows. A repair should call it explicitly before application, check the
return and nonzero numerator/denominator, and retain the two integers in
worker-owned storage. This setup obtains unit-conversion metadata, not an open
file, token, socket, or retained port granting specimen authority. It does not
justify pre-opening probe resources. The measured ratio here was **125/3**;
ticks are not nanoseconds.

Suggested arithmetic for the prototype: compare elapsed ticks using a checked
threshold `ceil(budget_ns * denom / numer)`, calculated with a 128-bit
intermediate before applying; or convert a checked elapsed delta with
`(__uint128_t)delta * numer / denom`. Validate representability and positive
budget, reject backwards time explicitly, and use checked addition when
extending a signed exec deadline. Do not multiply the absolute counter in a
64-bit intermediate, treat zero as an API error without a contract, allow a
negative elapsed interval to pass, or rely on signed-overflow behavior.
Conversion failures need honest local-failure evidence distinct from a failed
native call. Counter wrap and impossible intervals should fail closed under an
explicit supported-lifetime assumption, rather than acquire a release.

## Ordering: the actual decision boundary

The [production wait](../controller/tools/pw_probe_runner/pw_probe_runner.c)
publishes progress and phase arrival before its start read. Each iteration then:

1. Reports a previously failed clock read, or obtains the next read.
2. Calculates elapsed time and rejects `elapsed >= budget`.
3. Acquire-loads the release ordinal and rejects a future phase ordinal.
4. Acquire-loads cancellation (`exit_requested`) and exits if nonzero.
5. For the exact current ordinal, release-stores the immutable phase
   acknowledgement and latest ordinal, then returns to the action loop.

The [host driver](../runner/Sources/PWRunnerCore/CWorker.swift) closes collection
after the synchronous hook returns, rechecks child ownership and phase
publications, then release-stores the ordinal. Failure during collection can
leave an independent worker failure before the host sees it. The final `done`
check and release store are not atomic together; the worker's refusal path
must therefore remain terminal even if a late release is written.

After the wait returns, the worker publishes each action's start, runs it,
publishes its result, and finally publishes phase completion. A subsequent phase
has a new start sample and requires its own ordinal. The shared acquire/release
operations establish visibility and ordering, not a common atomic timestamp
across clock, release, cancellation, acknowledgement, and action start.

The [deterministic experiment](safe-wait-time/order_probe.c) includes the actual
worker source and substitutes only its existing semantic clock seam. It does
not apply a sandbox and does not run a validator. Separate acknowledgement and
action-completion publications accompany a real `/etc/hosts` open under ordinary
authority. These are boundary observations, not sandbox or `query_first` claims.

| Mode | Controlled schedule, 1 ms budget | Observed result |
| --- | --- | --- |
| 0, 1 | Start read or observation fails with EIO while release 1 is already visible | Native clock failure, done, no acknowledgement/action |
| 2 | Sample exactly 1,000,000 ns; release made visible before callback returns | Timeout, no acknowledgement/action |
| 3 | Sample 999,999 ns and current release | Acknowledgement and completed native action |
| 4 | Sample below expiry, current release and cancellation visible | Exit without acknowledgement/action; no fabricated clock failure |
| 5 | Expired sample, current release and cancellation visible | Timeout publication precedes cancellation handling |
| 6 | Sample below expiry, delay 10 ms inside callback, then publish release | Acknowledgement/action; returned elapsed is still 999,999 ns |
| 7 | Future release 2 and cancellation visible | Phase-release failure, detail 2; no acknowledgement/action |
| 8 | Two phases; phase 2 initially sees stale release 1, then release 2 | Phase 2 takes two observation reads and acknowledges only its release; both actions complete |
| 9 | Clock reports success but goes backwards by one second; release visible | Current code acknowledges and returns **−1,000,000,000 ns** |

All ten final observations reaped cleanly without forced termination. Mode 9
is a constructed gap, not an observed platform regression: current code checks
the clock's return but does not validate a successful value. A repair should
explicitly strengthen this fail-closed behavior and test its evidence.

The initial experiment driver mistakenly expected failure code 14 for mode 7;
the real enum and publication are 11. Original output and the failed assertion
are preserved. Only this assertion and an orders-only rerun option changed;
the C probes did not. The ten ordering cases were rerun successfully in a fresh
directory. The clock results are credited from the original run: the mistaken
assertion was later and did not alter those commands or measurements. Its driver
snapshot is labelled reconstructed; the final source hashes are also retained.

**Recommended preserved meaning:** expiry is decided by the worker's sampled
elapsed time. A sample at or beyond the edge wins over an already visible
release. Once a pre-expiry sample passes, the following loads can acknowledge
after a scheduling delay. A release stored before the edge can conversely be
refused if the next sample is expired. There is no timestamp of when the host
stored release. Moving or adding a load does not establish a strict wall-time
bound on acknowledgement or action start.

Cancellation likewise wins only when observed by its load. Cancellation stored
after that load can race with acknowledgement/action start; the current protocol
does not atomically arbitrate the two. Arrival precedes the start sample, so a
delay between them is also outside the measured interval. Preserve these limits
explicitly rather than describing the wait as a hard total-response deadline.

The [comparison builder](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
additionally requires phase-local closure/release/acknowledgement, unbroken
worker ownership, no protocol violations, and eligible uniquely associated
native validator records. A clock replacement supplies none of those facts by
itself. Earlier native records survive a later wait failure; later failure must
not retroactively erase earlier phase evidence or manufacture `query_first`.

## Shared seam and the implementation decision still needed

`PW_MONOTONIC_READ` is used by:

| Semantic phase | Purpose and application boundary |
| --- | --- |
| `WORKER_START` | Pre-application exec-budget start, even for a plan without exec |
| `PROCEED_START`, `PROCEED_OBSERVE` | Post-application start/check of every phase wait |
| `EXEC_ADMIT` | Post-application remaining budget before spawn |
| `EXEC_OBSERVE` | Post-spawn checks of child deadline and collection |
| `EXEC_REAP` | Bounded observation during exec cleanup |

`wait_for_proceed` returns elapsed nanoseconds to `attempt_budget_exclude`,
which adds them to the exec budget's deadline. Thus switching only the proceed
clock also changes what duration is subtracted from a budget measured in the
old, adjusted clock. Equal unit names do not establish equal rates. It also
leaves the reproduced unsafe clock dependency in post-apply exec paths.

Recommended next decision: explicitly include the **shared worker clock source
and its arithmetic** in the repair, using one continuous-time domain for budget
start, wait exclusion, exec admission, child observation, and reap observation.
Keep existing lifecycle/orchestration and polling structures. This broadens the
clock-source replacement beyond proceed and must be stated and tested; it is
not authorization for a general timing rewrite. If a proceed-only repair is
required instead, first specify how old-domain exclusion remains truthful when
its clock fails. Do not silently add raw-clock intervals to the old budget.

Moving deadline authority to the host is not recommended by these observations.
The hook runs synchronously and is excluded from the host sentinel allowance;
host scheduling and a blocked collection can delay cancellation. A host-owned
deadline would need independent scheduling, a defined release/cancel race, and
worker-lifetime handling. Neither that redesign nor a safe worker clock bounds
the host's final blocking reap. No total response-time claim follows.

## Repair acceptance and remaining unknowns

The following are the small distinguishing acceptance groups for a subsequent
implementation, beyond compilation:

1. **Native path and setup:** the original deny-default specimen, bare deny,
   and allow-default neighbour, first explicit and repeated reads, without
   added permissions; retain native failures, PID-correlated log evidence and
   cleanup. Observe any platform fallback separately. Verify timebase setup
   failure and zero factors before application without inventing errno.
2. **Arithmetic and sleep:** non-unit ratios including 125/3, exact boundary,
   one tick below it, large multiplication/addition, backwards/unusable time,
   and accumulated phase exclusions. Establish sleep inclusion through a
   controlled suspension/wake observation before making a tested sleep claim.
   Native Intel or other supported configurations need their own path evidence.
3. **Race precedence:** preserve modes 0–8 above; change mode 9 to an explicit
   fail-closed result. Add narrowly placed gates *after* the time sample and
   *after* cancellation load to pin delayed scheduling and cancellation that
   arrives too late. Do not assert that either side must win an unscheduled race.
4. **Phase/evidence integration:** acknowledgement and action start independently
   absent before release; stale/future ordinals; phase 2 time failure preserving
   phase 1; partial validator records retained on expiry; comparisons withheld
   unless the actual phase chain and worker lifetime support them. Exercise the
   existing clock-failure fixture against the revised native/local failure seam.
5. **Shared exec budgets:** same clock domain across initial budget, exclusions,
   admission, child deadlines and reap; failures preserve native observations
   and independent cleanup. Run the existing exec budget and lifecycle cases,
   including remaining-budget refusal and failed cleanup.

For an integrated prototype, use a matching signed build, run `runner_unit`,
`runner_c_worker_harness`, the affected live witness cases, and
`witness_contract/order_barrier_mutations` against that candidate. The current
baseline mutation control passed with its worker and host bypasses detected;
it must be rerun for the changed wait. Production acceptance additionally needs
the applicable failure-boundary suites and full battery. No replacement received
those credits in this investigation.

Unresolved observations are precise: the original fallback condition needs a
trace of the actual failing call and commpage state; a universal candidate claim
needs evidence for configurations not exercised here; tested sleep semantics
needs actual system sleep/wake. These do not rescue `CLOCK_MONOTONIC` or block a
carefully scoped prototype on this machine. Coherent exec accounting and honest
representation of local time failures are the decisions that block selecting
the final production patch.

## Reproduction and artifact map

Run live commands outside a restrictive automation sandbox and keep separate,
fresh output directories. The selected app must match the checkout's sources.
The executed baseline command was:

```sh
PW_TEST_OUT_DIR=tests/out/runs/safe-wait-baseline-live-20261016 \
  tests/run.sh --suite runner_unit --suite runner_c_worker_harness \
  --case witness_contract/bug_report_returns_verdicts \
  --case witness_contract/order_barrier_mutations
```

The durable [probe driver](safe-wait-time/run_probes.py) retains every native
argv, stdout/stderr, wall-time bracket and process reap, plus source hashes.
This equipment requires pre-repair commit `fcc3558`: `order_probe.c` depends on
that worker's `PW_MONOTONIC_READ` seam and wait signature.
For a fresh reproduction (change the output path if it already exists):

```sh
tests/lib/checkout_lock.sh -- python3 records/safe-wait-time/run_probes.py \
  /private/tmp/pw-safe-wait-reproduction
```

It builds and runs 72 clock processes and ten deterministic ordering cases,
then collects kernel log messages naming its clock children. An optional final
`orders` argument runs only the ordering experiment. The historical native and
ordering runs used `/private/tmp/pw-safe-wait-probes-20261016` and
`/private/tmp/pw-safe-wait-orders-20261016` respectively; their data now reside
in the managed run's attachment.

`investigation/platform/installed-disassembly.txt` and `installed-fallbacks.txt`
contain full LLDB command transcripts. They were obtained with `xcrun lldb
--batch`, a `main` breakpoint, `run`, `image list -u -f`, and `disassemble --name`
for the clock/wrapper functions, followed by `process kill`. The second also
reads the two capability bytes at `0xfffffc090`; that private address is
investigation equipment derived from the installed assembly, not a proposed
production API. `platform-sources.json` gives immutable download URLs and
SHA-256 values. `selected-app-source.json`, the app-to-HEAD diffstat, identity
checks and tracked-source hashes retain provenance. `attachment-manifest.json`
hashes the attached files without modifying the dispatcher's original results.

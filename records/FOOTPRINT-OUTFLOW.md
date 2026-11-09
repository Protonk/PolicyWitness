# Footprint reduction outflow

Recorded 2026-11-06. Source revision: `79ad8a447066113474900e29617991cafe5c9cab`.

Status: recorded dispositions and deferred directions, not an execution plan,
acceptance gate or release commitment. The question is which current demands can be reduced while preserving
PW's observations and claims. [FOOTPRINT](../docs/FOOTPRINT.md) establishes scoped
CPU demand, representation coexistence, backing identity and resource-specific
endings; [LIMITS](../docs/LIMITS.md) supplies the corresponding allowances. Row IDs
below refer to FOOTPRINT. Expected assertion reactions remain unverified until a
later experiment.

Each direction below names the present mechanism, the bounded change, the
promises that change must keep, and its evidentiary risks. An evidentiary risk
is a way the present habit may be protecting PW's ability to witness an effect,
or a way it may be obstructing that ability. Neither kind is established here:
each names a mechanism in source and the check that would turn the risk into an
observation. A habit that protects witnessing is not thereby justified, and a
habit that obstructs it is not thereby condemned; the record exists so that a
later change does not discover either role by accident.

| Direction | Rows | Demand mechanism | Possible bounded change |
| --- | --- | --- | --- |
| [2](#direction-2-remove-one-redundant-capture-conversion-copy) | fr6–fr7 | Raw bytes and owned typed records coexist for evidence and presentation. | Schema-owned response representation adopted; further borrowing or streaming remains separate. |
| [3](#direction-3-pace-the-sandboxed-workers-waits) | fw1–fw2 | Active and parked workers continuously poll protocol words. | Introduce a bounded paced wait, separately from serialization changes. |
| [4](#direction-4-right-size-the-evidence-region) | fw4–fw5 | Every worker initializes fixed evidence capacity even for a small request. | Investigate right-sized evidence only in a separate ABI change. |
| [5](#direction-5-authority-region-and-custody-sizing-or-disposal) | fw6–fw7 | Per-actor authority regions and per-token private buffers are allocated before launch; erased bytes can remain allocated. | Investigate tighter admitted-plan capacities or earlier safe disposal separately. |

A small follow-on should change one mechanism at a time and compare matched
workloads against the same signed baseline. No expected gain, changed assertion
or claim of incidental structure is established by this candidate list alone.

## Direction 2: remove one redundant capture conversion copy

Rows: fr6–fr7.

### Disposition: schema-owned response representation

[Typed response transport](../docs/CONTRACT.md#typed-response-transport) owns the
adopted boundary. One schema defines 83 records, their stored fields, binary
representation and public JSON projection. Swift constructs and validates typed
records; the client relays host bytes; Rust admits typed evidence and projects
JSON. Lifecycle questions have named fields. Response-only JSON coders and the
generic response validators are retired.

Named admission covers fresh reads and writes, exec, actor setup/equipment and
application, scheduling and endings, and extension custody. Unsupported claims
remain separate from retained observations. Equipment metadata counts retained
UTF-8 text directly, with native counts bounded separately. Ordinary reporting,
evidence-preserving degradation and independent minimal reporting have distinct
controls.

The accepted benefit is schema ownership and explicit access to evidence, not a
comparative performance result. [FOOTPRINT](../docs/FOOTPRINT.md#response-storage-and-transport)
records current representation lifetimes and descriptive samples. Raw host bytes
and their owned interpretation deliberately coexist. Full pipe collection still
precedes retention limits; no streaming, reception deadline or process-memory
ceiling follows from the frame and decoded-storage budgets.

The smaller capture-copy proposal is superseded by this representation change;
it has no independent performance disposition. Future borrowing or streaming
work needs its own ownership and evidence argument.

## Direction 3: pace the sandboxed worker's waits

Rows: fw1–fw2. The active actor's acknowledgement wait, `wait_exchange`,
also polls continuously, but has different precedence and is not isolated by
the existing held-phase measurements.

### Present mechanism

In [the worker](../controller/tools/pw_probe_runner/pw_probe_runner.c),
`wait_for_proceed` samples continuous time, checks cutoff, proceed allowance
and deadline arithmetic, rejects a future release ordinal, observes cancellation
and then accepts the exact release. It does not service inbound delivery.
`wait_for_activation` checks time, cutoff and arithmetic, observes cancellation,
checks the named activation and services one inbound delivery without consuming
it. It has no separate proceed allowance. `wait_exchange` accepts a nonzero
acknowledgement before its loop's clock sample; otherwise it checks time, cutoff,
exchange allowance and cancellation, then services inbound delivery.

All three end unsuccessful polls with one thousand `cpu_relax` instruction
hints. The instruction is not an OS scheduler yield. The release wait's
no-allocation/sleep/I/O comment describes its present discipline. The
[continuous clock](../controller/tools/pw_probe_runner/pw_worker_timing.h) has
native applicability controls because a previous libc monotonic path failed
after apply. Test-only sleep seams warn of possible policy refusal; those
comments do not establish native applicability or refusal of a replacement.
The unsandboxed host already paces through `HostWaitClock`, with separate
sentinel and exchange-service cadences.

### Qualification result: retain the current waits

The requested 1 ms `nanosleep(&request, NULL)` and the one permitted
alternative, direct `mach_wait_until`, both fail first-use qualification under
bare version-2 deny-default and the historical version-2 deny-default plus
file-read-data profile. In each native run, all twelve children using those
profiles applied successfully, recorded matching live process generations,
returned an unexpected native failure on the first pause, then exited and
were independently reaped. No refused call was retried. `nanosleep` returned
-1 with errno 22 (`EINVAL`); `mach_wait_until` returned 53 (`KERN_DENIED`,
without POSIX errno). Neither return alone assigns a sandbox cause.

Allow-default and explicitly unapplied children completed the requested pauses
and observed interruption in their separate signal mode. Each configuration
has three repetitions of each mode. These controls qualify no production wait:
the dependency failures stop both release and parked pacing before integration.
There is no changed-worker CPU benefit, matched responsiveness result, live
validator-query claim or actual system sleep/wake observation. Removing parked
pacing would not cure a dependency that also fails at release waiting.

The equipment is Mac17,3, native arm64, macOS 26.7.1 (25G241), SDK 27.2,
Apple clang 21.0.0, Mach timebase 125/3. Baseline source is
`d46f1ea646ed1d37c31062ec43669642f5b6c980`; worker identity is
`71deec287a0734104807dd909c56cb506ffbe9e97c58123a1911ae5a64242bd2`.
The signed app and production sources remain unchanged. Power capture initially
reported AC and subsequently battery; native observations record their own
state. No matched CPU/response comparison pairs runs across that transition.

Installed disassembly shows `nanosleep` using `__semwait_signal` (Unix syscall
334), skipping clock-service reads when the remainder pointer is NULL, and
rewriting unexpected errors to EINVAL. The clock port and semaphore are acquired
by libc initialization and refreshed by its fork-child path, before the probe's
application; no explicit pause warm-up was added. Direct `mach_wait_until`
uses Mach trap -90 and acquires neither resource. Its absolute deadline is
constructed from `mach_absolute_time` with checked addition, separately from
continuous elapsed observations. Success or interruption returns to the probe;
no unslept remainder is retried. Neither installed user-space path inspection
nor these runs establish actual system sleep/wake behavior.

A failing nanosleep child had a PID-matched syscall-334 denial event inside its
call's continuous-time bracket. That mechanism-specific observation justified
testing the direct Mach path; it did not establish the alternative's safety.
The alternative independently failed. Bounded supplemental log queries
succeeded, with some nanosleep events and no matching Mach-wait events in the
initial run. The separate file-open positive controls returned -1/EPERM, but
their events were not observed in those queries. Positive evidence establishes
only its own event; silence establishes neither denial absence nor complete
coverage. A corrected final-partial-second log window was rerun diagnostically,
preserving the earlier refusals and their original windows. The final Mach
query retained twelve PID-matched `syscall-mach 90` denial events inside the
failed-call brackets and the known file-open control's own syscall-5 event;
the final nanosleep query retained eight PID-matched syscall-334 events, with
its file-open positive control still unobserved. These events remain separate
from any requested PolicyWitness operation.

The native cases, required-evidence reader and independent rejection controls
are described in the [suite account](../tests/suites/runner_c_worker_harness/README.md#native-pause-applicability).
The initial native runs are `worker-wait-native-02`
(`20261107T151329Z_7d189e62`) and `worker-wait-mach-01`
(`20261107T151443Z_70904b70`); final diagnostic repetitions are
`worker-wait-native-final` (`20261107T151803Z_8759d3a9`) and
`worker-wait-mach-final` (`20261107T151818Z_a72ee735`). Their raw results,
source copies, disassembly, app evidence, power, native positive controls,
log status, exit/reap observations and original run identities are preserved
with a hash index in `worker-wait-evidence/` in the identified copy of
`footprint-opt-targeted-final-02`. Its archive remains inside the preserved
`worker-wait-review-final-01/worker-wait-review/archives/` tree, now in
`host06-main-targeted-01`'s `host-followon/archives/worker-wait-review-final-01.tar.gz`.
That former retained run is itself preserved in
`tests/out/runs/porcelain-adoption-acceptance-b/porcelain-adoption/prior/worker-wait-evidence/archives/host06-main-targeted-01.tar.gz`.
The nested archive indexes and source snapshot of the retired review identify
these copies and file hashes. This evidence is gitignored
and available only in the local checkout. The early `worker-wait-native-01`
hardware-query refusal is preserved separately; its unsandboxed retry passed.
The unchanged app's sandboxed signature-check failure likewise passed the
identical verification outside the automation sandbox.

History identifies the C exit wait's original nanosleep in `c8355d9e` and its
precautionary removal in `ab1d9707`, not an observed refusal in that commit.
No `mach_wait_until` use was found in runner/controller history. The recollection
of a preceding problematic wait remains unresolved and is not equated with the
separately evidenced CLOCK_MONOTONIC failure.

### Dispositions from the worker wait exploration

The completed acceptance review reaffirms the dispositions below
with timestamp reader version 10: uncertainty-expanded response extrema,
complete response coverage, and conservative publication brackets for legacy
inbound commits. All corrected response bounds pass; the largest is 185.541 µs
against 2 ms. It also identifies the retained raw observations and replacement
reader controls. The original summaries remain preserved separately.

The worker wait pilot decomposed held phases on the
production path with continuous-clock stamps in disposable instrumented hosts
and seam-built workers. In every ordinary trial the worker applied, arrived and
spun while the host slept in its 10 ms readiness poll, which lasted 12.5 ms, so
the first arrival was observed 5.6 to 8.1 ms late; worker response to release
and activation was below the 1.3 µs instrument floor throughout; the validator
exit grace never slept in 72 eligible phases and EOF to reap took 2 to 15 µs,
which closes the cleanup-delay question negatively.

HOST-01 (accepted, `fc089ef7`): the readiness wait became a bounded wait for
pipe readability under the same allowance. In sixty matched pairs the arrival
to observation interval and the held total fell beyond the instrument
uncertainty in every pair of every ordinary cell and regime, by 0.4 to 8.1 ms
per pair with medians of 2.9 to 5.3 ms; no resolved actor-form or
whole-request regression; every response bound credited. The remaining first
arrival delay is the 2 ms sentinel poll during the worker's application.

HOST-02 (accepted with HOST-03 on 2026-11-07, `c7648e8e` and `5d1c888d`): the host re-samples a
just-published answer for at most 100 µs before its first sleep after an
activation, release or inbound commit. In every actor-form pair of both regimes
the per-trial detection total fell from 4.9 to 11.1 ms to at most 1.26 ms, the
host's execution sleeps from four to eight to two, and the two actors made
23,568 to 59,493 fewer wait passes per request; a later ordinary phase's
arrival was observed within 4 µs in every rapid pair and in three of five idle
pairs, the other two arriving after the budget. The request as a whole became
slower in the actor form in nine of ten pairs, by 0.1 to 13.9 ms: the host now
reaches the worker exit grace wait before the worker exits and sleeps its 10 ms
poll once per request (12.5 ms slept), where the baseline's final detection
sleep had covered the worker's exit. The owner admitted one further candidate
for that poll rather than accepting the tradeoff.

HOST-03 (accepted with HOST-02 on 2026-11-07, `46e2b578` and `66430db5`): between exit grace
samples the host waits on the readiness pipe's hangup, which the worker's exit
produces, instead of sleeping 10 ms; a hangup that precedes reapability is
followed by at most ten 100 µs settle sleeps, and a pipe that cannot inform
the wait falls back to the former poll. In sixty matched pairs against the
HOST-01 baseline every grace wait ended at the exit with no timeout, the actor
form's detection total fell beyond spread in every pair of both regimes, and
its whole request was faster in all ten pairs (1.5 to 10.2 ms on 58 to 97 ms),
where HOST-02 alone had been slower in nine. The first actor's exit request to
reap grew from 2 to 7 µs to 169 to 362 µs by construction, the host now waiting
for the exit itself rather than finding it done after a longer detection
sleep; terminal publication to reap fell from 1.3 to 2.6 ms to 0.2 to 0.4 ms.
On this machine a pipe hangup and a kqueue `NOTE_EXIT` wake with the same
latency, and the production worker's hangup precedes its reapability more
often than a trivial child's, hence the settle sleep.

SCAN (accepted 2026-11-08, `d7d19a6b` and `d1821df6`): the recipient's inbound
scan starts at a worker-local completed-prefix cursor, the count of leading
slots this worker has itself acknowledged, instead of index 0; 68 bytes of
static state reset at authority preparation, every visited slot checked as
before, lowest-index selection and one acknowledgement per pass preserved. In
seventy matched pairs the subject's scan loads per pass fell below the
full-scan floor in every A2 and A2D pair of both regimes: by 19 to 33 percent
in A2 (two slots, most passes preceding the first commit) and by 41 to 47
percent in the inbound-dense A2D (64 deliveries committed in index order,
13 to 15 million fewer loads per request), with zero-visit passes only on the
candidate; every activation, release and inbound-delivery response bound was
credited, and the only every-pair worsening was the subject's parked pass
count, which rises because shorter passes fit more into the same parked time.
Counts, not CPU: no CPU or energy claim is made.

The pilot and three comparisons measured a pass period of 0.26 to 0.28 µs
with one thousand `cpu_relax` hints. These observations nominated a later
comparison; they were not its baseline. The ARM and hint round below used
fresh accepted source after HOST-04 and HOST-06. The scan mask remains outside
this round: no measurement showed holes defeating the accepted cursor's
savings. Correctness coverage of holes alone does not nominate another mask.

Branch 1, PREPARATION (rejected 2026-11-07 without building, on the plan's cost
clause): the pilot measured the whole frame-serialization interval at 142 to
163 µs for one query, 323 to 364 µs for 64 and 788 to 848 µs for 256, far above
the instrument's uncertainty, so the pre-build rejection rule did not apply;
but the interval is 1.8 to 4.6 percent of the held total, against a derived
cache bound of 1,099,776 encoded bytes retained for the worker's life and a
deferred encoding charge whose precedence against the collection allowance
would need new controlled-clock controls. Reopening it needs a workload where
serialization is a larger share of the held interval or a cheaper accounting
than the plan's.

HOST-04 is accepted (`1451c488`): after the last ordinary collection, the
existing readiness pipe can end the bounded final wait on hangup. Shared-memory
publication checks, actual stop reasons and owned reap remain distinct. An early
hangup is consumed once; unusable or consumed notification falls back to bounded
sleeps. No resource or worker write was added. All fifty ordinary candidate
comparison trials ended that wait on notification, against one plain sleep in
each baseline trial. Terminal detection and reap improved beyond uncertainty in
every ordinary pair, and every response bound was credited. The source account
is FOOTPRINT `fw15`; the retained host archive preserves all 120 comparison
receipts, exact identities and the separate observer-effect comparison.

This is a structural adoption, with no universal request-speed, CPU, energy or
coalescing claim. One O2P idle whole-request pair was 1.970 ms slower and crossed
the any-pair spread flag despite a shorter host session; no group worsened beyond
spread in every pair. Instrumented/unstamped differences were variable, so no
fixed overhead correction is justified. Integrated verification covered all 222
default cases: one compiler-discovery equipment failure was retained and then
passed with an SDK-aware wrapper against unchanged app bytes. The six-case
targeted run also passed ordering mutations and all 24 held measurements.

HOST-05 is closed without adoption. The host-only inspection/Swift `-O`
diagnostic still found about 0.8–0.9 ms of decode for 64 verdicts and
3.0–3.1 ms for 256 under `-O`; shipped inspection settings were unchanged.
Candidate `b433da29` reused each validated native integer within a frame.
Its 40-pair comparison improved decode in all 20 query-dense pairs, saving
135–919 µs, but two held totals grew (21 µs and 1.255 ms), failing the frozen
requirement that every selected pair shorten both decode and hold. Planning
and validator intervals account for the contrary elapsed differences; their
cause is unestablished. No further sampling was added and the source change
was not integrated. The retained host archive preserves exact identities, contrary observations
and incomplete-verification limits. A later less-work
proposal needs a new scope decision; this result is not uniform hold improvement.

HOST-06 is accepted (`7f67e5cd`): after a received readiness byte, the ordinary
host permits one initial resampling opportunity using its existing bounded
helper. Application, phase and ownership checks remain authoritative; missing
readiness gets no new opportunity. On the accepted HOST-04 foundation, every
selected O0/O1 idle pair shortened arrival observation by 2.930–3.010 ms and
held time by 2.827–3.034 ms, beyond uncertainty. The added measured resampling
span was 1.833–8.625 µs and passed the frozen elapsed-cost tradeoff in every
selected pair. This span includes possible descheduling; it is not process CPU.
All response bounds were credited across sixty pairs. One O0 idle whole request
was 1.982 ms slower despite its shorter hold; no whole-request group worsened
beyond spread in every pair. Observer costs remain separately recorded without
a fixed correction. No resource, worker IPC or public evidence field was added.
FOOTPRINT `fw16` describes the mechanism; the retained host archive preserves
exact identities and claim limits. CPU, energy and coalescing gains
remain unmeasured.

The host follow-on round is complete. The integrated signed app passed all
222 default cases, all 597 runner assertions and the six-case targeted selection, including ordering
mutations and 24 held-footprint measurements. Its completion supplied the
production foundation for the separate ARM/hint investigation below.
The roughly 25 percent overshoot of requested host sleeps on this equipment
remains a measured condition, not a separate tuning candidate.

### ARM and hint dispositions

The bounded round on Mac17,3, macOS 26.7.1 (25G241), closes without a worker
wait change. Production native identity is
`aaa8056c79c242fde5740449049246e3ed88facdc2c8efd143f6344c856da8e5`, including
HOST-04/HOST-06 and excluding HOST-05. The signed app is unchanged.

WFE and WFET each passed twelve first-use children: three each under unapplied,
version-2 allow-default, bare deny-default and deny-default with file-read-data.
Applied children executed their first explicit wait only after successful
application; unapplied children were a separate control. Every child published
entry and return and reached its own 500 ms continuous-clock cutoff. Supervisors
observed live generations around a silent interval and reaped every child;
no rescue supplied progress. This establishes native first-use applicability
on this configuration, not integrated protocol or deployment qualification.
WFE's largest repeated instruction bracket was 3.336 ms, including possible
descheduling; these are not the integrated response measurements.

Untimed WFE has no established supported selection rule for an independent
maximum wake interval across configuration, migration and resume. The
[pinned XNU event-stream implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/machine_routines.c)
and its internal capability flag do not supply that contract. Its production option therefore closed without an enablement
rule. The installed public SDK header exposes `hw.optional.arm.caps`, with
stable ABI bit 26 for FEAT_WFxT, a better feature-detection lead for the timed
alternative. It does not by itself qualify all EL0 counter and resume assumptions.
All first-use children read 24 MHz; no model-based 1 GHz assumption was used.

The timed prototype then replaced one unsuccessful tail with one WFET, a
checked CNTVCT deadline limited to 100 microseconds and the last sampled
remaining allowances. It kept ordinary acquire loads and decision order.
These were explicitly labelled signed source substitutions, not production
integration. The CPU screen used fresh held baselines, live queries, effect
guards, generation binding, busy/sleep controls and observed cleanup. The
ordinary cell isolates a release wait. The actor lifecycle cell isolates the
parked, unapplied issuer alongside the applied queried subject and retained
extension custody; it does not qualify a restrictively applied parked actor.

Each row below has five alternating matched pairs in each of rapid and
one-second-idle regimes, with one excluded first request per exact staged app.
All twenty measured holds per row were eligible, on AC with low-power mode 0,
without recorded system sleep. Holds of at least one second measure CPU demand;
they are not production hold durations. Both sides used byte-identical readers,
a 10 ms declared accounting quantum, one quantum of allowance per endpoint and
full elapsed brackets. First baselines were approximately one CPU-second per
second. ARM's added dependency had a frozen 10% minimum beyond those allowances;
the smaller hint change had a 1% minimum. No candidate met its criterion in any
pair, and no extra samples were added.

| Candidate and run | Baseline CPU-seconds/second | Candidate CPU-seconds/second | Pairs meeting criterion |
| --- | --- | --- | --- |
| Release WFET, `arm-cost-wfet-release-01` | 0.9932–1.0017 | 0.9927–1.0033 | 0/10 |
| Parked WFET, `arm-cost-wfet-activation-01` | 0.9946–1.0039 | 0.9965–1.0027 | 0/10 |
| Release 10,000 hints, `hint-cost-release-01` | 0.9966–1.0017 | 0.9936–1.0054 | 0/10 |
| Parked 10,000 hints, `hint-cost-activation-01` | 0.9929–1.0019 | 0.9952–1.0063 | 0/10 |

Both WFET roles and the sole hint alternative per role are closed without
adoption on those CPU criteria. The existing 1,000-hint tails remain. All live
held-generation, query, ordering, effect, custody where applicable and cleanup
checks passed. These negative benefit screens do not label the candidates fully
qualified, prove energy equivalence, or establish native inapplicability.
Whole-request CPU, energy, peer capacity, wake coalescing and integrated response
bounds were not established here. Adoption-only restrictive protocol, host-loss,
migration and actual sleep/resume qualification was not pursued after closure.

The first ARM build failed before trials because Apple's assembler rejected
`.arch_extension wfxt`. The isolated helper instead uses fixed X17 and the
independently specified [LLVM encoding](https://github.com/llvm/llvm-project/blob/main/llvm/test/MC/AArch64/armv8.7a-wfxt.s), `d5031011`; retained disassembly identifies
`wfet x17`. The failure and repaired first-use runs are both preserved. The
mechanism-neutral CPU reader accepts quiet workers without weakening the old
busy-worker oracle. Independent controls reject missing/misbound evidence,
no-op gain claims, contrary pairs, pacing/power mismatches and label changes;
a real alarm exercises watchdog cleanup. Generic logging is not an oracle.

### Retention and reopening

The completed worker and ARM plans and acceptance records are retired. Their
frozen definitions and source identities remain in Git history and the local
evidence snapshot. Current functional acceptance is recorded separately from
these historical wait observations.

The retained porcelain adoption run contains
`porcelain-adoption/prior/worker-wait-evidence/archive-index.json`, which locates
thirteen unchanged historical archives. These include the former
`host06-main-targeted-01` with its twelve host archives and nested pilot/review
evidence, both ARM first-use screens, the pre-trial assembler failure, two fresh
baselines and all four CPU comparisons. Original run IDs, hashes, source copies,
binaries, disassembly, conditions, claims and ownership receipts remain intact.
Copies add no case credits and relocate no cleanup ownership. Evidence is
ignored by Git and local to this checkout.

The four CPU comparisons replayed identically with their frozen readers at
worker-wait closeout. Archive-index SHA-256 is
`3ca6a9f9065344c28acc726eaae0cc5c655236db7d62c09319b6485e9f18143b`;
replay SHA-256 is
`1cfeaf9a44f6d8b912138e6e73843f817c064b6361191c90e7a7b7b62fb54505`.
The preserved public SDK header has SHA-256
`4fc509ff0ba41255900b7fe3efa679590b7f05b7ddfafc113404c440f73d9a5a`.
[tests/RETAINED.json](../tests/RETAINED.json) identifies the current containing
runs. `porcelain-adoption/prior-index.json` verifies the subsequent copy and
preserves the original closeout identity. This relocation changes no measured
result or qualification disposition.

Reopening ARM needs a newly justified benefit observable (for example reliable
energy evidence) or changed-equipment evidence, plus a defensible deployment
contract and the full per-role protocol/response gates. More CPU sampling of
these same candidates is not nominated. Counts alone cannot establish energy
or available execution capacity; a wait may remain scheduled while doing less
instruction work. Reopening hints needs a measured resource or response
opportunity, not an assumption that a shorter or longer batch is better.

`wait_exchange` is closed as outside this round, unchanged: no isolated live
hold was nominated, and its acknowledgement-before-clock precedence prevents
borrowing release or activation measurements. A future exchange proposal needs
its own generation-qualified hold and response controls. The scan mask remains
unopened for lack of measured holes defeating the prefix. These are scope
closures, not pending acceptances or negative native trials. Existing FOOTPRINT
mechanisms and LIMITS allowances remain unchanged by the ARM/hint round.

## Direction 4: right-size the evidence region

Rows: fw4–fw5.

### Present mechanism

[`PWShmLayout.regionBytes`](../runner/Sources/PWRunnerCore/CWorker.swift) is a
compile-time sum: header, 256 slots of 8 KiB, 1,024 params of 512 bytes, the
1 MiB compiled-object capture with its header, the evidence header, the 4 KiB
diagnostic buffer and the 832-byte authority setup trailer, 3,675,920 bytes in
all. The host creates, zeroes and populates the region, touches every page, and
only then spawns. The worker's `map_region` refuses an object smaller than the
constant and addresses every section through compile-time offsets, including
the setup trailer at a fixed distance from the region's end. The layout is
checked C against Swift and bound into the worker identity.

### Proposed direction

Only as a separate ABI change: a region sized to the admitted plan.

### Promises the direction must keep

Published layout, bounds checks, one backing with separate views, profile and
slot coverage, failure evidence with room regardless of plan, and admission that
refuses rather than truncates are promises. Capacity itself is implementation
structure, but changing it crosses ABI, build identity and reader boundaries.
Not a small first perturbation.

### Evidentiary risks

Protective roles the present habit may have:

- Fixed offsets let the worker locate sections after checking the object size
  and bootstrap identity. Variable geometry would need its own validation and
  a stable place to report failures. A proposal must identify which checks run
  before apply and how any later failure can be published without trusting the
  disputed geometry. A geometry failure must never read as a sandbox cause.
- The host zeroes the full region through its mapping before spawn. This may
  move some backing initialization work before apply, but it does not establish
  fault-free access through the worker's separate mapping. Any claimed
  protection of post-apply publication needs observations of that mapping over
  the publication interval. Right-sizing or lazy initialization could change
  when initialization and faults occur; their effects remain to be measured.
- Request-independent geometry supplies a source-derived comparison basis for
  the ABI layout suite, the response checker's
  `evidence_region_bytes_per_backing`, and the held-phase and aftermath checks
  that read worker mapping metadata. These checks retain their own observation
  scopes; the constants alone do not observe a live mapping. With
  variable geometry, readers need an independent basis for comparison, such as
  geometry derived from the admitted plan and independently observed mapping
  lengths. Repeating a reported size is not corroboration of that size.
- The evidence header and diagnostic buffer are where failure evidence lands
  for any plan, including a plan with no slots. Right-sizing must keep them
  whole and at a position the worker can find without the plan.
- Layout changes require worker identity regeneration and review of affected
  fixtures and goldens. Before/after comparisons must account for changed
  geometry and binary identity rather than treating offsets as unchanged.

Ways the present habit may obstruct witnessing:

- The host initializes the full logical region per worker whether or not the
  plan uses it. Initialization work and physical memory demand are possible
  costs, but the footprint measurements establish neither host residency nor
  publication faults. The logical capacity is not a measured resident-set
  increase or a bound on every possible gain. Compare initialization work,
  host and worker memory, and faults over identified intervals before claiming
  a benefit or an obstruction to witnessing. Shared backing must still be
  counted once.

### Before crediting a result

Worker identity regeneration, the ABI layout suite and layout golden review,
the C worker lifecycle tests, the worker harness, the response and held-phase
footprint cases with their readers updated to the published geometry, and the
default battery. A claimed pre-touching benefit also needs independent
observations of faults through the worker's mapping during publication;
claimed physical-memory savings need host and worker memory observations.

## Direction 5: authority region and custody sizing or disposal

Rows: fw6–fw7.

### Present mechanism

[`ActorAuthorityRegion`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
sizes each actor's shared object from the admitted plan: 1,152 bytes plus
16,448 per inbound or outbound slot, so the region is already proportional; a
slotless actor requests 1,152 logical bytes. Page-rounded object and mapping
lengths remain separate from residency. The worker validates the
observed object size between the zero-slot minimum and the page-rounded maximum
and maps the observed size. [`TokenCustody`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
maps one anonymous 16 KiB buffer per admitted token during setup; `erase`
clears the whole buffer at the token's last declared use and keeps the mapping;
`finish` erases again and unmaps. At final actor cleanup, the scheduler permits
`tearDown(quiescent:)` to erase a shared region when its owner was reaped or
never launched; otherwise it records `withheld_not_quiescent` and only detaches
the host mapping. The
authority tests pin that a non-quiescent region keeps its bytes and that a
second `finish` cannot turn unknown into permission to erase.

### Proposed direction

Tighter admitted-plan capacities, or earlier safe disposal, each separately.

### Promises the direction must keep

Custody confinement, source and recipient identity, byte equality, last-use
erasure, and withheld erasure under an unresolved owner are promises. Requested
logical size, padded object size and physical residency must remain distinct. Do
not dispose custody needed by a later transfer, or inbound bytes needed by a
repeated consume.

### Evidentiary risks

Protective roles the present habit may have:

- Withholding shared erasure while a worker could still read prevents one
  possible source of apparatus-induced interference with a consume. It does
  not by itself establish the cause of a failed consume. For final host erasure
  of a launched actor's shared region, the present protocol uses established
  reap as its quiescence gate; a never-launched owner is also eligible. A
  different protocol could use an independently established end to in-flight
  and future reads. That would need its own evidence and failure handling
  before earlier erasure could be credited. Private custody's last-use boundary
  is separate from shared-region quiescence. Failed delivery currently settles
  a flag rather than overwriting bytes a recipient may still read.
- Allocating every custody buffer during setup moves apparatus allocation
  failure before the first activation, where it is reported as a setup
  disposition. Allocating at acceptance would put a possible host allocation
  failure inside the exchange window, between a published native issue result
  and its acknowledgement, which is a new unresolved-transfer shape to classify.
- Fixed-size custody with whole-buffer erasure does not depend on the host's
  own length bookkeeping. A buffer sized to the accepted length erases exactly
  what the host believes it holds, and the evidence that the erasure covered the
  bytes is then the same bookkeeping.
- The worker's size validation and the response checker's padding corroboration
  both encode the present geometry. Reducing a logical size while leaving
  page-rounded object and mapping lengths unchanged does not by itself
  establish lower residency. Observe those lengths and physical memory before
  crediting a saving for a slotless actor.
- The setup observation carries one region row per actor. Dropping regions for
  slotless actors is a reply shape change under the evidence contract, for
  1,152 logical bytes per actor.

Ways the present habit may obstruct witnessing:

- The current aftermath measurements observe process presence after CLI return,
  not erasure or disposal of private and shared token storage. Changing disposal
  timing alone would not establish byte erasure. A claim about that ending
  needs an independent observation tied to the owner and the protocol's
  established quiescence boundary, which need not be reap in a different design.
- Source-established erasure leaves private custody allocated until `finish`.
  Earlier disposal could reduce its lifetime; distinguish logical capacity
  released, observed mapping disposal and any measured physical-memory change.

### Before crediting a result

The actor authority tests including the quiescent and non-quiescent teardown
cases, the worker harness terminal-erasure case, the actor composition and
response footprint cases, and the aftermath footprint case. An earlier shared
erasure gate needs independent evidence that no in-flight or future reads
survive it, including interrupted and failed paths. Claims of erasure or
mapping disposal need their own observations, separate from process exit.

## Assertion owners

Relevant assertion owners include the [controller boundary test](../controller/src/runner_client.rs)
(`independent_binary_records_reach_typed_storage_without_text_conversion`), [native response checker](../tests/suites/witness_contract/check_response_footprint.py),
[held-phase checker](../tests/suites/witness_contract/check_held_phase_footprint.py),
[worker proceed and activation controls](../tests/suites/runner_c_worker_harness/run.sh),
[layout agreement](../tests/suites/runner_abi_layout/run.sh), and
[actor custody controls](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift).
Read their actual assertions before assigning a sensitivity claim. A failure
identifies a row and promise to inspect; a missing FOOTPRINT or LIMITS citation
does not establish incidental behavior.

Every reduction must preserve the [core ideas](../AGENTS.md#core-ideas): fresh
sandboxed processes, host/worker separation, observations supporting effects,
predictions before attempts, honest attribution and simple runner ownership.
Keep token erasure, native release, unmapping, process exit and reap distinct.

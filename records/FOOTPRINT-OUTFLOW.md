# Footprint reduction outflow

Recorded 2026-11-06. Source revision: `79ad8a447066113474900e29617991cafe5c9cab`.

Status: deferred investigation, not an execution plan, acceptance gate or release
commitment. The question is which current demands can be reduced while preserving
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
| [2](#direction-2-remove-one-redundant-capture-conversion-copy) | fr6–fr7 | Generic capture is cloned into a typed capture while raw output and decoded host bytes coexist. | Remove one redundant conversion copy while preserving the generic capture retained for diagnostics. |
| [3](#direction-3-pace-the-sandboxed-workers-waits) | fw1–fw2 | Active and parked workers continuously poll protocol words. | Introduce a bounded paced wait, separately from serialization changes. |
| [4](#direction-4-right-size-the-evidence-region) | fw4–fw5 | Every worker initializes fixed evidence capacity even for a small request. | Investigate right-sized evidence only in a separate ABI change. |
| [5](#direction-5-authority-region-and-custody-sizing-or-disposal) | fw6–fw7 | Per-actor authority regions and per-token private buffers are allocated before launch; erased bytes can remain allocated. | Investigate tighter admitted-plan capacities or earlier safe disposal separately. |

A small follow-on should change one mechanism at a time and compare matched
workloads against the same signed baseline. No expected gain, changed assertion
or claim of incidental structure is established by this candidate list alone.

## Direction 2: remove one redundant capture conversion copy

Rows: fr6–fr7.

### Present mechanism

[`capture_json_output`](../controller/src/utils.rs) makes the lossy retained
text for both streams, counts received and retained bytes from the raw stream
lengths, and parses the generic `Value` from the raw bytes only when stdout
was not truncated. The lossy stdout text is kept only when parsing failed or
retention truncated. [`parse_runner_client_output`](../controller/src/runner_client.rs)
then admits in a fixed order: request-delivery failure, capture or parse error,
missing capture, integer `protocol_version`, version equality, typed capture
(`deny_unknown_fields`), `validate_capture`, strict base64 decoding, retention
truncation, and finally the host JSON parse. The typed capture is produced by
`serde_json::from_value(value.clone())`: `from_value` consumes its argument, and
the clone is what keeps the generic `Value` intact. That generic `Value` lives
on as `run.transport` and is rendered into the envelope on every path.

### Proposed direction

Deserialize the typed capture by reference from the generic `Value`, or
otherwise remove the whole-tree clone, while keeping the generic capture
retained for diagnostics and for the envelope.

### Promises the direction must keep

Capture admission order, exact received and retained counts, receiver-loss
versus malformed-JSON attribution, unrepaired invalid UTF-8, the raw reply
preserved beside its interpretation, and malformed transport evidence are
promises. The present overlap is an implementation fact. Borrowed
deserialization must not silently extend buffer lifetimes or weaken admission.

### Evidentiary risks

Protective roles the present habit may have:

- The generic `Value` is the preserved raw transport record. The clone is the
  only reason it survives typed conversion. An implementation that removes the
  copy by moving the `Value` out of `run.transport` drops the transport record
  from every successful envelope, and no admission test notices, because
  admission still succeeds. The reader of the envelope loses the client's own
  account of acquisition, submission and reply.
- Version gating before typed interpretation requires a generic parse that
  exists separately from the typed one. A single-pass typed parse would report
  an unsupported protocol as malformed, which is a different attribution: the
  controller rules require rejected payloads to be preserved without coercing
  versions.
- Counts are taken from the raw bytes before lossy conversion, and the parse
  reads raw bytes, never the lossy text. Any restructuring that parses from the
  retained `String` repairs invalid UTF-8 into accepted JSON; the existing
  `invalid_utf8_is_not_repaired_into_accepted_json` and
  `multibyte_cut_counts_bytes_before_lossy_conversion` controls are the guards,
  and both must stay in the selected verification.
- Typed fields that borrow from the generic `Value` tie the typed capture's
  lifetime to it and invite holding the raw `Output` longer than fr1 states.
  The ending "raw Output drops on caller return" is a documented fact that
  would then be false.

Ways the present habit may obstruct witnessing:

- Raw streams, lossy text, generic `Value`, typed capture, decoded host bytes
  and the parsed host reply coexist on the largest replies, and the retention
  cap is a retention cap, not a streaming limit. The controller's peak is set by
  what the client emits, not by what PW retains. A memory failure in the
  controller could lose the run's durable envelope. No such failure has been
  observed.
- The opposite habit would be worse for evidence: collecting every byte is what
  makes `stdout_bytes_received` exact and lets the oversized-producer control
  distinguish receiver loss from a malformed reply. A streaming cut that stopped
  reading would block or break the client's pipe and change what the client
  did. That boundary is outside this direction and should stay outside it.

### Before crediting a result

The three receiver controls above, `valid_oversized_producer_is_receiver_loss_not_malformed_json`,
`response_footprint_success_boundaries`, the failure-boundary and blackbox
consumer controls, and the response footprint case.

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
`footprint-opt-targeted-final-02`, now archived under
`tests/out/runs/worker-wait-review-final-01/worker-wait-review/archives/`.
The [acceptance review](WORKER-WAIT-REVIEW.md) identifies the archive and its
file hashes. This evidence is gitignored
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

The [acceptance review](WORKER-WAIT-REVIEW.md) reaffirms the dispositions below
with timestamp reader version 10: uncertainty-expanded response extrema,
complete response coverage, and conservative publication brackets for legacy
inbound commits. All corrected response bounds pass; the largest is 185.541 µs
against 2 ms. It also identifies the retained raw observations and replacement
reader controls. The original summaries remain preserved separately.

The [worker wait pilot](WORKER-WAIT-PILOT.md) decomposed held phases on the
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

HOST-02 (accepted with HOST-03 on 2026-11-07, `c7648e8e` and `5d1c888d`; see its
[acceptance record](WORKER-WAIT-HOST-02-ACCEPTANCE.md)): the host re-samples a
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

HOST-03 (accepted with HOST-02 on 2026-11-07, `46e2b578` and `66430db5`; see its
[acceptance record](WORKER-WAIT-HOST-03-ACCEPTANCE.md)): between exit grace
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

SCAN (accepted 2026-11-08, `d7d19a6b` and `d1821df6`; see its
[acceptance record](WORKER-WAIT-SCAN-ACCEPTANCE.md)): the recipient's inbound
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

Branch 3's hint tails (`HINT-RELEASE`, `HINT-ACTIVATION`) and the
[ARM option plan](../runner/ARM-WAIT-OPTION-PLAN.md) are explicitly deferred
while the host follow-on round below proceeds. This is a priority decision,
not a negative qualification or benefit result. The pilot and three comparisons
measured a pass period of 0.26 to 0.28 µs with one thousand `cpu_relax` hints;
these observations inform a later comparison but do not freeze its baseline.
Hint tuning could reduce repeated work and warrants separate CPU/peer-progress
observations; ARM qualification would establish applicability and progress,
with deployment and resource benefit evaluated separately. The scan mask
alternative remains unopened, conditional on measured savings from skipping
acknowledged slots behind holes.

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

The approved [host follow-on round](../runner/WORKER-WAIT-EXPLORATION-PLAN.md#host-follow-on-round)
nominates ordinary terminal-publication detection outside the held interval
(HOST-04), then decoder work with an explicit inspection/optimized build-flavour
control (HOST-05), then a conditional first-arrival resampling candidate
(HOST-06). Each needs a new comparison on accepted source; the retained timings
nominate the work rather than establish its benefit. The roughly 25 percent
overshoot of requested host sleeps on this equipment remains a measured
condition, not a separate tuning candidate.

### Remaining questions

Release and parked pacing remain unaccepted on this equipment. Reopening either
requires a newly justified dependency or changed-equipment qualification,
followed by live queries of the same held generation, preserved decision order,
error publication, response brackets, the ordering mutation controls, and the
original matched CPU/response acceptance bars. The failed calls above are not
an invitation to add policy exceptions or silently spin on refused sleeps.
Parked delivery acknowledgement, self-transfer, revisits and shortened exchange
allowances still need independent responsiveness observations before parked
pacing can be accepted.

`wait_exchange` remains unchanged and has separate acknowledgement precedence.
It still needs its own isolated hold and acknowledgement experiment before any
optimization. Requested-action quiescence is not CPU idleness; retained footprint
measurements continue to describe the existing polling loops. Their budgets,
mechanism rows and measured values have not changed.

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
(`response_footprint_success_boundaries`), [native response checker](../tests/suites/witness_contract/check_response_footprint.py),
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

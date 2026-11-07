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

### Proposed direction

A bounded requested pause between unsuccessful polls, qualified under the
applied policy. Start with release and parked activation; isolate exchange
waiting separately. Keeping a worker alive for a PID query requires the lifetime
and collection barrier, but does not itself establish a need for continuous CPU
use. Native queries of the paced worker must establish that the proposed
implementation preserves that observation.

### Promises the direction must keep

Collection before release, cancellation precedence as the loads observe it,
continuous-clock accounting including system sleep, each loop's decision order,
named activation, parked delivery service, and one-shot process lifetimes are
promises. CPU ratios and response intervals are observations. A held worker's
CPU exceeding a sleeping control may still hold after pacing; that assertion
is not a detector of every blocking wait.

### Evidentiary risks

Protective roles the present habit may have:

- The instruction-hint batch adds no sleep-call dependency. A replacement's
  native calls, first-use resources, errors and policy applicability need
  inspection and observation. A wait refusal is apparatus evidence; any
  associated log event must not be attributed to a requested action. Repeated
  failed calls could also affect log-based observation, but this record has no
  measurement of their logging rate or coverage. Neither broad syscall safety
  nor one-denial-record-per-call behavior follows from the present source.
- Continuous polling avoids a deliberate pause before the next observation,
  but does not establish memory-latency response. Clock reads, service work,
  instruction batches and scheduling intervene. The ordering controls and the
  [order-barrier mutation control](../tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls)
  anchor on the present loop. `proceed_delayed_observed_quiescence` asserts that
  effects stay absent across a delayed release; a slower worker passes that more
  easily, so it cannot detect a regression in reaction time. The mutation
  control's anchors must be reviewed, not just rerun, because a paced loop can
  make the "worker bypasses the release wait" mutation fail to apply.
- Release and activation decide expiry from validated continuous samples;
  exchange acknowledgement has different precedence. A pause's clock basis
  and behavior across system sleep must not change those decisions or renew
  allowances. Actual sleep/wake remains untested. A bounded requested pause
  does not bound scheduling delay before the next decision.
- A parked actor services inbound delivery between polls. Pacing can delay
  that acknowledgement and spend the active sender's exchange allowance even
  if `wait_exchange` is unchanged. There is no measured microsecond baseline
  here. Transfer timing and shortened-allowance controls must expose the cost.
- The held-phase receipt asserts worker CPU above a matched sleeping control,
  characterizing the current polling behavior. Unit calibration belongs to the
  independent [observer controls](../tests/suites/witness_contract/footprint_observer_controls.py),
  which compare normalized CPU counters with the child's `getrusage` accounting
  and check sensitivity to unconverted ticks when the timebase differs from
  unity. After pacing, the worker-versus-sleep assertion may still pass or may
  fail without indicating a defect. Review its meaning before reusing it;
  preserve the independent unit calibration.
- Requested-action quiescence and CPU idleness remain different claims under
  either implementation. Lower CPU demand needs calibrated observation;
  absent requested effects alone cannot establish it.

Ways the present habit may obstruct witnessing:

- Recorded held intervals show approximately one CPU-second per elapsed second
  per worker. They do not establish core affinity. Competition with host
  collection and validator queries could spend more of their allowances;
  increased `prediction_unavailable` under load has not been measured.
- Pacing may change scheduling conditions for host and validator as well as
  worker response. Compare those roles and response intervals on matched
  equipment instead of treating lower worker CPU as the whole result.
- Battery/AC state is recorded, but heat, energy use and throttling are not
  measured by these CPU receipts. Those consequences remain hypotheses.

### Before crediting a result

The order-barrier mutation control with reviewed anchors, the worker harness
proceed and activation scenarios including the deny-default variants, the
ordering and worker-clock unit tests, a `native_clock`-style control for the
chosen pause under deny-default, live queries of the paced worker generation,
response-interval and parked-delivery observations, the held-phase footprint
case with its receipt's meaning restated, and the response footprint case.

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

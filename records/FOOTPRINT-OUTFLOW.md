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
| [1](#direction-1-rebuild-sorted-envelope-maps-from-owned-entries) | fr8 | Recursive envelope sorting clones complete subtrees while source and destination coexist. | Rebuild sorted maps from owned entries, preserving key order and rendered bytes. |
| [2](#direction-2-remove-one-redundant-capture-conversion-copy) | fr6–fr7 | Generic capture is cloned into a typed capture while raw output and decoded host bytes coexist. | Remove one redundant conversion copy while preserving the generic capture retained for diagnostics. |
| [3](#direction-3-pace-the-sandboxed-workers-waits) | fw1–fw2 | Active and parked workers continuously poll protocol words. | Introduce a bounded paced wait, separately from serialization changes. |
| [4](#direction-4-right-size-the-evidence-region) | fw4–fw5 | Every worker initializes fixed evidence capacity even for a small request. | Investigate right-sized evidence only in a separate ABI change. |
| [5](#direction-5-authority-region-and-custody-sizing-or-disposal) | fw6–fw7 | Per-actor authority regions and per-token private buffers are allocated before launch; erased bytes can remain allocated. | Investigate tighter admitted-plan capacities or earlier safe disposal separately. |

A small follow-on should change one mechanism at a time and compare matched
workloads against the same signed baseline. No expected gain, changed assertion
or claim of incidental structure is established by this candidate list alone.
The [bounded plan](../docs/FOOTPRINT-OPTIMIZATION-PLAN.md) takes direction 1 only.

## Direction 1: rebuild sorted envelope maps from owned entries

Rows: fr8.

### Present mechanism

[`sort_value`](../controller/src/json_contract.rs) visits every object in the
envelope, clones each key and each subtree into a temporary vector, sorts the
copies, recursively sorts each copied subtree, builds a new map and replaces
the old one. By the time it runs, `envelope_value` has already converted the
caller's borrowed `data` into an owned `Value`, so the clone is a second
complete copy of the envelope tree while the first is live. Pretty rendering
then adds the output `String` while the sorted `Value` remains live. The
test-only stage seam records stage order, borrowed input and scalar lengths at
these boundaries; it does not count copies.

### Proposed direction

Take the old map, collect its owned entries, sort them, recursively rebuild and
reinsert. Keep the explicit sort rather than relying on the map's storage
order, so the rendered bytes stay the same if the `serde_json` feature set later
changes.

### Promises the direction must keep

Envelope shape, sorted keys at every object level with array order preserved,
byte-exact rendering for fixed inputs, and the error mapping of a failed encode
are promises. The clone is an implementation fact: the fr8 source wording must
change even if the scalar boundary assertions still pass.

### Evidentiary risks

Protective roles the present habit may have:

- Sorted-key determinism is the property that makes two envelopes comparable
  by bytes. Consumers in the blackbox and shape controls, retained evidence, and
  any custody tooling that hashes an envelope depend on it. The one existing
  ordering test covers a single nested object; it does not establish array
  element order, nested arrays of objects or escaped strings. A rebuild that
  reorders array elements, or sorts only the top level, passes that test and
  silently changes every envelope hash. The protective role belongs to the sort,
  not to the clone; the plan's byte-fixture check is what carries it across.
- The stage seam reports `borrowed_input: true` and lengths only. Passing seam
  assertions after the change is not evidence that copies were removed, and a
  lower native sample is not evidence either, because sampling cannot attribute
  a sample to sorting. The gain is source-established or it is not established.
  The risk is a claim of a measured reduction that the evidence cannot support.

Ways the present habit may obstruct witnessing:

- The duplicate tree raises the controller's peak after the host has replied.
  The envelope is the only durable record of a run, and a lost reply has no
  retrieval or replay. The present copy makes the window in which the controller
  could fail for memory reasons larger than it needs to be. No such failure has
  been observed; the measured peaks (fr9–fr13) are well below any limit on the
  recorded machine.

### Before crediting a result

Exact-byte rendering of a fixed nested fixture with arrays and escaping, the
existing envelope tests, `response_footprint_success_boundaries`, and the
response footprint case against the same signed baseline.

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
  what the client emits, not by what PW retains. This is the same loss-of-record
  exposure as direction 1, and equally unobserved.
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

Rows: fw1–fw2. The same loop shape also serves the active actor's
acknowledgement wait, `wait_exchange`, which the rows do not name.

### Present mechanism

After `sandbox_apply`, [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c),
[`wait_for_activation`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
and `wait_exchange` each loop over: one continuous-clock sample, the shared
cutoff and the phase or exchange allowance, the cancellation word, the protocol
word they are waiting on, and for actors one inbound delivery service; then a
batch of one thousand `yield` instruction hints from `cpu_relax`. The comment on
the release wait states the rule: no allocation, sleep or I/O after apply. The
`yield` hint is an instruction, not a kernel entry. The clock read is
[`mach_continuous_time`](../controller/tools/pw_probe_runner/pw_worker_timing.h),
chosen because the libc monotonic path's fallback was refused under a
deny-default profile; its header promises neither a user-space read nor a kernel
entry, and the `native_clock` control exists to show it produces no deny record
under deny-default on the recorded machine. The only post-apply sleeps in the
worker are test seams, and their comments say that `nanosleep` is a syscall a
sufficiently restrictive policy could deny. The unsandboxed host, by contrast,
already paces: `HostWaitClock` sleeps between polls at 2 ms for the sentinel wait
and 1 ms for exchange servicing.

### Proposed direction

A bounded paced wait between samples, made separately from any serialization
change, with the existing barrier, activation, expiry and cancellation controls.

### Promises the direction must keep

Collection before release, cancellation precedence as the loads observe it,
continuous-clock expiry including system sleep, named activation, parked
delivery service, and one-shot process lifetimes are promises. CPU ratios are
observations. A held worker's CPU exceeding a sleeping control may still hold
after pacing; that assertion is not a detector of every blocking wait.

### Evidentiary risks

Protective roles the present habit may have:

- The wait makes no kernel entry the specimen can refuse. Every post-apply
  syscall the worker makes today belongs to a requested action or to the clock
  read, so a denial recorded against the worker's PID is attributable to one of
  those. A sleep is a kernel entry under the applied profile. If a specimen
  refuses it, the worker must classify a failed wait without inventing a native
  result, and the refusal is logged as a denial that belongs to the apparatus,
  not to a requested action. A loop that retries a refused sleep produces one
  such record per iteration, which also competes with the records a log-based
  observer is trying to read. Whether a given sleep primitive is refusable under
  a given profile is an OS-sensitive fact of the same kind the clock needed its
  own control for; the source comments assert only that it could be.
- The spin keeps reaction to release, cancellation and activation at memory
  latency. The ordering controls, the race-gate and precedence tests, and the
  [order-barrier mutation control](../tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls)
  anchor on the present loop. `proceed_delayed_observed_quiescence` asserts that
  effects stay absent across a delayed release; a slower worker passes that more
  easily, so it cannot detect a regression in reaction time. The mutation
  control's anchors must be reviewed, not just rerun, because a paced loop can
  make the "worker bypasses the release wait" mutation fail to apply.
- Expiry is decided from a validated continuous-time sample before release or
  cancellation is consulted. A sleep primitive has its own clock basis and its
  own behavior across system sleep, which is already untested. Pacing adds a
  second time source to a wait whose correctness argument rests on one.
- The parked actor acknowledges inbound deliveries between polls. Pacing turns
  a microsecond acknowledgement into one or more sleep quanta, bounded by the
  5,000 ms exchange allowance. Transfer timing fields, and any fixture that
  shortens that allowance, observe the difference.
- The held-phase receipt asserts worker CPU above a matched sleeping control to
  validate counter units, not to detect optimization. After pacing it may still
  pass, or it may fail for a reason that is not a defect. Either way its meaning
  must be restated before it is reused; loosening it to pass would remove the
  unit calibration it was written for.
- "Requested-action quiescence is not CPU idleness" is currently an honest
  statement because nothing idles. A paced worker invites an idle-wait claim
  that would need its own observation under the same unit calibration.

Ways the present habit may obstruct witnessing:

- Each waiting worker occupies a core. The host's collection and the validator's
  `sandbox_check` run on the same machine during the same interval, and the
  cumulative collection allowance (30,000 ms) is spent in host time. On a small
  core count, three polling actors compete with the processes that produce the
  predictions; a slower collection makes `prediction_unavailable` more likely
  under load. This is not measured.
- Scheduling latency differs between an idle core and a busy one. The
  apparatus's own polling decides which regime the host and validator run in,
  in a way no footprint row records. Pacing would change that regime for every
  timing observation at once, which is a reason to measure before and after on
  the same machine rather than a reason to prefer either.
- Machine load and power are stated conditions of every footprint row. A spin
  of one to three cores through a held phase on battery is heat and throttling
  that the apparatus brings to its own measurement. Comparisons across holds
  carry that condition without being able to separate it.

### Before crediting a result

The order-barrier mutation control with reviewed anchors, the worker harness
proceed and activation scenarios including the deny-default variants, the
ordering and worker-clock unit tests, a `native_clock`-style control for the
chosen sleep primitive under deny-default, the held-phase footprint case with
its receipt's meaning restated, and the response footprint case.

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

- The sandboxed worker trusts no runtime geometry. For an admitted request,
  region and plan cannot disagree. A right-sized region would make the worker
  read its geometry from the header and bounds-check against it after apply,
  adding an apparatus failure that can only occur after apply, where the
  worker's only publication channel is the region it is disputing. That failure
  would need its own disposition and must never read as a sandbox cause.
- Pre-touching every page before spawn is what keeps post-apply publication free
  of first-touch faults into the shared object. Right-sizing keeps that only if
  the pre-touch still covers the whole smaller region; any lazily grown design
  reintroduces allocation after apply.
- Request-independent geometry is what lets independent readers corroborate the
  worker's mapping from source alone: the ABI layout suite, the response
  checker's `evidence_region_bytes_per_backing` computed from constants, and the
  held-phase and aftermath checks that read worker mapping metadata. With
  variable geometry each run must publish its own geometry and every reader
  must trust the publication it is checking.
- The evidence header and diagnostic buffer are where failure evidence lands
  for any plan, including a plan with no slots. Right-sizing must keep them
  whole and at a position the worker can find without the plan.
- Layout changes change the worker identity. Evidence from before and after the
  change is no longer directly comparable, and every pinned fixture and golden
  moves at once. That is a cost to the record, not just to the build.

Ways the present habit may obstruct witnessing:

- Logical capacity is not residency, but the host touches every page, so the
  host's resident set grows by the full region per worker whether or not the
  plan uses it: about 29 MB of touched shared pages for eight actors, counted
  once. That is the entire measurable cost, and the gain from right-sizing is
  bounded by it. No way in which the fixed region makes an effect harder to
  witness was identified; its mapping size is, if anything, easier to
  corroborate because it is constant.

### Before crediting a result

Worker identity regeneration, the ABI layout suite and layout golden review,
the C worker lifecycle tests, the worker harness, the response and held-phase
footprint cases with their readers updated to the published geometry, and the
default battery.

## Direction 5: authority region and custody sizing or disposal

Rows: fw6–fw7.

### Present mechanism

[`ActorAuthorityRegion`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
sizes each actor's shared object from the admitted plan: 1,152 bytes plus
16,448 per inbound or outbound slot, so the region is already proportional, and
a slotless actor's 1,152 bytes occupy one 16 KiB page. The worker validates the
observed object size between the zero-slot minimum and the page-rounded maximum
and maps the observed size. [`TokenCustody`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
maps one anonymous 16 KiB buffer per admitted token during setup; `erase`
clears the whole buffer at the token's last declared use and keeps the mapping;
`finish` erases again and unmaps. `tearDown(quiescent:)` erases a shared
region only when the host has established that its actor terminated; otherwise
it records `withheld_not_quiescent` and only detaches the host mapping. The
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

- Withheld erasure is what keeps a consume result attributable. If the host
  cleared shared bytes while a worker could still read them, a failed consume
  could be the sandbox's refusal or the apparatus's erasure, and PW could not
  say which. "Earlier safe disposal" can only mean disposal after reap is
  established, which is the present gate; there is no earlier point that
  preserves attribution. The same reasoning is why a failed delivery is settled
  by a flag, not by writing under a reader.
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
  both encode the present geometry. Any region below one page cannot change
  physical residency, so a tighter logical size for a slotless actor changes
  the checks without changing the footprint.
- The setup observation carries one region row per actor. Dropping regions for
  slotless actors is a reply shape change under the evidence contract, for
  1,152 logical bytes per actor.

Ways the present habit may obstruct witnessing:

- At CLI return, fa3 stays unknown: erased-but-mapped custody and withheld shared
  erasure leave token bytes potentially present in mappings PW no longer
  observes. The habit is not the cause; the unresolved reader is. It does mean
  that no change to disposal timing can improve that row. What is missing is an
  independent post-reap observation of erasure, which is evidence work rather
  than footprint work.
- Retained allocations after erase hold 16 KiB per token. There is nothing to
  witness in them.

### Before crediting a result

The actor authority tests including the quiescent and non-quiescent teardown
cases, the worker harness terminal-erasure case, the actor composition and
response footprint cases, and the aftermath footprint case.

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

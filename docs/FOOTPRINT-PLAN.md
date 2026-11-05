# Plan: PolicyWitness resource footprint

## Intended result and scope

Write `docs/FOOTPRINT.md` as a compact account of what PW consumes while
waiting, what it holds while producing and transporting a response, and what
remains after a run. Organize it by resource demand, ownership and observable
ending conditions. Its purpose is to make unnecessary demands discoverable and
reducible; an apparatus-residue category may correctly be zero.

Follow the editorial shape of [LIMITS](LIMITS.md): a short reading guide,
concise conditional tables, small diagrams and a few consequential
interactions. Use [WORKER](WORKER.md) and [ARCHITECTURE](ARCHITECTURE.md) to
investigate mechanisms, without reproducing their tours. The document must
distinguish measured consumption, logical capacity, constructed bounds and
source-supported mechanisms.

This is an execution plan, not a completed footprint investigation. Preparation
used three independent, read-only accounting scouts against clean commit
`2022f3261e7a2c9e59db35d245525443ddd444ad`. Their source and assertion inspection
informs the choices below; no native measurements, new behavioral tests or
version-zero acceptance results are claimed. The full scout accounts were
delivered in conversation but were not preserved as frozen repository records.
The source-findings table is their reconciled summary, not three independently
reviewable accounts. Execution refreshes the baseline and starts at
reconciliation; it does not repeat or claim a new independent-account gate.

Deliver the document, its generated DOT/SVG figures, registered tests and
observer/checker controls, current native observations, and completed cross-review.
An optimization is not required. Findings may confirm behavior, narrow a claim,
identify leakage or support later implementation work. Do not turn this into a
general performance benchmark, a replacement limits inventory, an installation
audit or an unrequested runtime redesign.

## Common cases and accounting boundaries

Every investigation and every review addresses this same trio. A section
assignment determines depth, not permission to omit the other two cases.

| Case | Required scope | Required distinctions |
| --- | --- | --- |
| Waiting | Begin with an identified worker that has arrived at a phase boundary while requested attempts remain paused. Follow worker, host, validator and any parked actors through release, expiry and cancellation. | Elapsed time versus CPU time; requested-action quiescence versus process activity; objects held versus work performed; exit request versus observed exit/reap. |
| Response storage and transport | Follow publications through host collection, reply construction and encoding, XPC, client capture, controller collection and decoding, envelope rendering and disposal. Compare a small admitted workload with a large reachable workload. | Configured capacity, synthesized encoded bound, actual encoded bytes, retained bytes, allocation size/capacity, virtual mappings and live-memory observations. Establish coexistence and backing identity before adding quantities. |
| Aftermath | Compare starting state, CLI return and the relevant resource-specific teardown boundaries for ordinary completion and at least one failed/interrupted path. Observe before harness cleanup. | Requested specimen effects, requested output artifacts, pre-existing installation state, PW apparatus resources and observer resources; presence, confirmed absence and unknown inspection. |

Use each resource's own ending condition. Examples include closing the last
descriptor, unmapping a view, dropping a copied representation, an identified
process exiting, its parent reaping it, and a confirmed registry removal. These
are different events. Neither CLI return nor a fixed settling delay substitutes
for them. A name unlinked at creation can be absent while the unnamed backing
object remains mapped. A surviving process at CLI return may be in expected
teardown; presence beyond its claimed ending boundary needs a different claim.
In particular, a numbered release ends the hold, not the evidence mapping's
lifetime. The host's launch-only evidence descriptor closes after spawn, its
mapping ends at session teardown, and worker references end independently at
process exit. Waiting rows and diagrams must preserve these separate endings.

## Source findings that constrain the proposal

These are starting points for verification, not newly measured consumption.

| Finding | Owning implementation and existing evidence | Consequence for this work |
| --- | --- | --- |
| Release and parked-actor waits poll continuously, including batches of ARM `yield` hints; the host uses separate sleeping/polling loops. | [`wait_for_proceed`, `wait_for_activation`, `cpu_relax`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`ActorScheduler`](../runner/Sources/PWRunnerCore/ActorScheduler.swift); [proceed controls](../tests/suites/runner_c_worker_harness/README.md). | An unchanged target and a held phase establish paused requested actions, not low CPU. Measure CPU over an independently established hold. |
| Each worker gets a fixed evidence region, initialized even for a small plan. Host and worker map one backing object. | [`PWShmLayout`](../runner/Sources/PWRunnerCore/CWorker.swift), [`ActorSession`](../runner/Sources/PWRunnerCore/ActorSession.swift), [ABI golden](../tests/fixtures/contract/abi_layout.txt). | Derive logical geometry from current layout evidence. Do not count aliases as separate backing objects or call logical bytes resident memory. Include authority regions only where used. |
| Collected host values can overlap their source mapping, but sessions tear down before later reply assembly/encoding stages. | [`ActorSession.collectOutput` / `tearDown`](../runner/Sources/PWRunnerCore/ActorSession.swift), [`finish`](../runner/Sources/PWRunnerCore/ActorScheduler.swift), [`CWorkerOrchestrator`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift). | Construct a stage/lifetime account before calculating totals; do not add all representations from the whole run. |
| The controller collects complete child stdout/stderr before applying retention limits. Parsed capture, base64 text, decoded host bytes and parsed host objects overlap at particular stages. | [`run_with_stdin` / `capture_json_output`](../controller/src/utils.rs), [`parse_runner_client_output`](../controller/src/runner_client.rs), [`render_envelope` / `sort_value`](../controller/src/json_contract.rs). | The cap is a retention bound, not a streaming-memory bound. Final envelope construction and pretty-printing need their own accounting. |
| The synthesized maximum is a conservative constructed reply, not a reachable workload or a memory peak. Two live-size receipts call client stdout bytes `runner_reply_bytes`. | [`ReplyMaximumTests`](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift), [`ReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift), [check_max_target_reply.py](../tests/suites/witness_contract/check_max_target_reply.py), [check_max_exec_steps.py](../tests/suites/witness_contract/check_max_exec_steps.py). | Correct the names and comparisons as a prerequisite. Raw host bytes come from `runner_client.transport.runner_reply.bytes_received`; client stdout includes the versioned capture and base64. Keep both. |
| Client timeout after invocation does not cancel submitted host work. Host retirement is scheduled after the reply. | [`PWRunnerClientSession`](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift), [`replyAndExit`](../runner/Sources/PWRunnerCore/PWRunnerService.swift), [reservation controls](../tests/CHANGE-VERIFICATION.md). | Observe continuing work and retirement separately from CLI return. Do not relabel client timeout as worker cancellation. |
| Plain-run installation checks cover registry/plist state; lifecycle controls already establish selected survivors before fixture cleanup. | [check_installs_nothing.py](../tests/suites/run_effects/check_installs_nothing.py), [check_closed_streams_leader_exit.py](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py), [lifecycle suite](../tests/suites/runner_exec_lifecycle/README.md). | Reuse these boundaries and independent identities. Do not extend installation invariance into a claim of zero processes, mappings or residue. |

Inspect assertions before assigning authority to a citation. In particular,
`runner_c_worker_harness/proceed_delayed_observed_quiescence`,
`witness_contract/attempt_effects_wait_for_collection`,
`witness_contract/max_targets_reply_survives`, `unit/rust.unit`,
`runner_unit/pwrunner_core_unit_executable`, `run_effects/run_installs_nothing`
and the exec lifecycle cases answer different questions. A source symbol's
presence, a passing return code or a generated link does not establish the
footprint claim.

## Subagent assignments and coordination

Use subagents within the executing harness's concurrency (up to 32 authorized),
with builds and tests serialized under the checkout lock.

Assign one investigation owner per case and rotate those owners for review;
each case receives one reviewer using a different accounting model. Fresh
agents for another full account reconstruction are unnecessary.

| Case | Investigation model and ownership | Reviewer |
| --- | --- | --- |
| Waiting | Machine demand; owns held-phase observer, case assertions and row/diagram proposal. | Aftermath owner, using objects and lifetimes. |
| Response | Work and amplification; owns representation ledger, controller measurement and internal assertions. | Waiting owner, using machine demand. |
| Aftermath | Objects and lifetimes; owns resource inventory, boundary observations and intervention ledger. | Response owner, using work and amplification. |

The coordinator reconciles findings, integrates tables and diagrams, and checks
acceptance. Review starts after the case's observations and draft are available;
each reviewer reconstructs one consequential claim and checks interactions with
the other two cases. There are no separate diagram or acceptance-agent waves.

The coordinator alone edits shared integration files such as
`tests/catalog.json` and suite-wide documentation, unless explicitly handed to
one owner. Assign diagram-manifest edits to one owner; this plan does not require
generator changes. Agree the common measurement/identity interface and assign
one author before case authors use it. Source edits may proceed in parallel in
disjoint files; builds and test
runs in one checkout remain serialized under the checkout lock. Separate
worktrees are required for genuinely concurrent builds/tests.

## 0. Establish the execution baseline

Read [root guidance](../AGENTS.md), [planning guidance](../CONTRIBUTING.md#planning-a-change),
[documentation guidance](AGENTS.md), [runner guidance](../runner/AGENTS.md),
[controller guidance](../controller/AGENTS.md) and [test guidance](../tests/AGENTS.md).
Record the revision, local changes, relevant source hashes, selected signed
app and its provenance, OS/architecture, toolchain and available observation
facilities. Preserve existing work. Native measurements must identify the
actual inspected binaries and measurement conditions, not merely the source
checkout's revision.

Keep planning/review materials in a task-owned
`records/footprint-<date>/` directory: baseline, reconciliation/questions,
review dispositions and acceptance. This plan is the only inbound documentation
link owner for those records. Permanent FOOTPRINT
content links to source and tests, not to planning records. Keep raw execution
evidence in fresh managed `tests/out/runs/` directories; identify locally
available, gitignored evidence honestly. Do not use scratch as its sole store.

Before collecting footprint receipts, fix the misleading size labels in both
[check_max_target_reply.py](../tests/suites/witness_contract/check_max_target_reply.py)
and [check_max_exec_steps.py](../tests/suites/witness_contract/check_max_exec_steps.py).
Record `host_reply_bytes` from
`runner_client.transport.runner_reply.bytes_received` and
`client_stdout_bytes` from `runner_client.stdout_bytes_received`. Compare the
former with the synthesized host-reply bound and the latter with the controller
allowance. Correct dependent ratios, receipt-allowance arithmetic, printed
labels and receipt consumers/documentation; retain each original boundary's
count. This is a prerequisite correction, not the response measurement cycle.

Choose these concrete workloads before measurement:

- **Small:** one admitted read against an owned fixture with known bytes, no
  exec and no optional compiled-profile receipt. Keep actual outcome and
  prediction evidence, rather than treating admission alone as success.
- **Large:** reuse the reachable 256-action control-character exec/output
  workload from `max_targets_reply_survives`, including its exact child-output
  checks and actual available profile receipt. Separately pair its
  `independent_query` and `eight_phase_maximum` workloads to isolate repeated
  collection with fixed actions, targets and queries; the latter is not a phased
  version of the escaped exec workload. The ordinary/declaration phase cap is
  eight; sixteen phases requires actor form.
  The synthesized maximal reply remains a separate constructed control.
- **Waiting variation:** one worker, followed by a legal multi-actor specimen
  with constant aggregate requested actions and additional parked workers.
  Confirm their actual activation/arrival states before comparison.
- **Aftermath variation:** ordinary small-run completion; a controlled client
  timeout after invocation while collection is held; and the existing known
  descendant-survival/worker-death controls as observer challenges.

Treat installed BYOXPC services, bundles and registry entries as baseline.
If a fixture needs an installation, inventory it before the specimen and keep
fixture installation/removal outside PW-run accounting. Follow existing
session ownership and recovery helpers, including retaining unresolved cleanup.

## 1. Reconcile the existing findings

Start with the source-findings table, checking its claims against the refreshed
baseline and current assertions. Preserve these accounting distinctions without
recommissioning three initial accounts:

| Account | Reconstruction obligation |
| --- | --- |
| O: objects and lifetimes | Identify backing objects, allocations, mappings, descriptors and processes. Follow acquisition, ownership, transfer, overlapping lifetimes and release evidence. |
| W: work and amplification | Follow polling, process checks, repeated collection, encoding, transport, decoding and cleanup. Explain scaling with elapsed time, phases, actions, payload bytes and repeated runs. |
| M: surrounding machine | Identify observable CPU activity, memory occupancy, capacity held and post-run state. Separate PW from observer/test demand and record what inspection can actually establish. |

For each case, retain in the working ledger:

1. A scoped claim naming quantity/unit, interval, owner and process/resource
   boundary, with source and assertion references and their limits.
2. A controlled change expected to alter demand under that model.
3. Two concrete situations that look equivalent under that model but differ
   materially under another. Explain the equivalence and the missing quantity.
4. A consequential unanswered question and the observation needed to answer it.

Useful counterexamples to verify, rather than slogans to repeat, include equal
held object sets over different wait durations; equal retained prefixes after
different full-stream collections; and equal output artifacts with different
surviving process trees. Record assumptions about shared backing and absence
as questions until supported. New investigation is directed at a missing
quantity or consequential disagreement, not at reproducing the preparation.

## 2. Reconcile into questions, rows and relationships

Compare claims before combining prose. Maintain a small working ledger with
case, resource/representation, owner, unit, start/end boundary, conditions,
evidence, uncertainty and proposed distinguishing observation. Resolve apparent
disagreements about different intervals, units, owners or resources by keeping
both useful distinctions. For incompatible claims about the same quantity
under the same conditions, name an observation that could select between them.

Draft three principal tables, using stable row IDs:

> Situation · resource demand or remaining state · quantity or behavior ·
> interval and ending condition · supporting test

The tables are **Waiting and retained resources**, **Response storage and
transport**, and **State remaining after a run**. Add the process, representation
or backing object directly to each row. Keep conditions alongside quantities.
For aftermath, use explicit `present`, `absence confirmed` and `unknown` states
with observation boundaries; zero is valid only for the inventoried category
and observed interval. Retain the expected ending condition even when the
observation does not establish that it occurred.

The initial table is a question map, not publication-ready evidence. Draw its
supported relationships next, with unresolved relationships named in adjacent
prose, before compressing the prose.
Select one material unanswered question per case for the cycles below; refine
the proposed question if account reconciliation identifies a more consequential
uncertainty. Do not spend a cycle rediscovering what source already settles,
such as whether controller retention occurs after full collection.

## 3. Author and inspect the diagrams

Use the existing [architecture manifest](architecture.json) and
[`generate_architecture.py`](generate_architecture.py), which generate DOT,
render with Graphviz `dot -Tsvg`, stamp SVGs with DOT hashes, and maintain
document regions. Do not hand-edit generated DOT/SVG or introduce Mermaid,
ImageGen or a separate drawing pipeline.

Use only the generator's current schema, styles, citation rules and registered
destinations. Keep new figure/citation regions in the already registered
`docs/ARCHITECTURE.md`, embed their SVGs in FOOTPRINT, and link their generated
ID tables. This avoids a new destination or source-only citation mechanism.
Add only the small graphs the principal tables need, using underscore-separated
graph IDs and hyphenated file stems, initially:

- `footprint_waiting` / `footprint-waiting`: worker polling, host/validator work,
  shared backing and views, protocol descriptors, parked actors where applicable,
  and release, expiry and cancellation edges.
- `footprint_response` / `footprint-response`: source mappings and copied host
  values, reply objects, encoded host bytes, XPC, client base64/capture,
  controller raw collection, parsed/decoded forms and final envelope. Split
  host/client from controller if one figure makes overlaps unreadable.
- `footprint_aftermath` / `footprint-aftermath`: baseline objects,
  run-introduced/changed objects, independent completion boundaries, expected
  end events, observed remaining state and separately marked later harness
  interventions. It may extend the other lifetime diagrams where that avoids
  duplication.

Preserve existing Helvetica typography, light process/storage colors, named
clusters, short edge labels, stable IDs and linked citation tables. Identify
shared views, established copies, ownership transfer and lifetime overlap by
explicit labels; a generic arrow must not silently assert a copy. State
unestablished XPC/Foundation backing relationships as unresolved in prose beside
the figure; omit unsupported copy/backing edges. Do not infer
physical allocation from two language-level values or sum per-process RSS as
unique system memory.

Use globally unique diagram IDs and put corresponding IDs in principal rows
and graph facts so a reviewer can trace both directions. Keep generated
supporting tables small and avoid duplicating the principal claim prose. Use
existing graph validation and drift checks. Do not extend the generator or cite
an unrelated passing test to make an unsupported relationship renderable.

Reuse existing limit placeholders in graph facts and link FOOTPRINT prose to
the relevant LIMITS rows; no new span destination is needed. Keep measured
observations distinct from manifest constants. Add the document to the README documentation index and
the architecture document graph with an accurate reader purpose; avoid broad
rewrites of LIMITS, WORKER or ARCHITECTURE.

Generate with `tests/lib/python.sh docs/generate_architecture.py`, inspect every
rendered SVG at readable size, and regenerate after changes. Use a local SVG
viewer/browser or raster preview for visual inspection. Inspect labels,
crossings, clipping, legends and the row/element correspondence. A matching SVG
stamp is mechanical provenance, not visual review. Retain review observations.

## 4. Complete one assess → question → test → update cycle per case

Each cycle records competing accounts, the discriminating observation, observer
and checker sensitivity, exact workload/build/conditions, raw observations,
interpretation and the coupled table/diagram/citation update. Use existing
capture, fixture ownership, dispatcher and retention infrastructure. New case
IDs below are proposed additions, not existing tests.

A case passes only when its deterministic assertions hold, its required receipt
is complete, valid controls are accepted and every rejected control below is
rejected for the intended reason. Missing required observations fail the case;
recording a number is not sufficient. Explicitly allowed `unknown` resource
states preserve limited inspection and cannot support an absence claim.

All receipts use a versioned JSON object with `schema_version`, `case_id`,
`run_id`, `workload_id`, exact request/artifact hashes, inspected binary hashes,
source identity, OS/hardware, observer identity/version, clock and metric units,
measurement configuration, raw native results/errors and assertion outcomes.
Counts, capacities, byte quantities and `*_ns` values are nonnegative integers;
unknown optional quantities are null with a reason, never zero or omitted.
Required quantities cannot be unknown. Retain raw samples and every repetition.
The lists below specify each case's
additional schema and assertion contract; quantities without a universal bound
remain scoped observations rather than invented machine-independent thresholds.

### Waiting: measured demand during an independently held phase

**Question.** How much CPU time accumulates during a validator-gate-acknowledged
hold, and how does adding parked actors change demand? The source establishes
active polling, not a utilization percentage. Compare identified workers with
an independently sleeping control over the same observation window.

Extend the acknowledged gate machinery in
[check_ordering.py](../tests/suites/witness_contract/check_ordering.py) and the
existing validator/exec fixtures. Register
`witness_contract/held_phase_footprint`. The existing gate directly observes
validator acknowledgement and target PID; production control flow connects
collection to worker arrival. Describe that source-qualified connection, not a
direct external read of `phase.arrived`. Actor comparisons additionally need a
host/harness snapshot of acquire-loaded setup, activation, arrival and progress
publications with generation identities; process presence alone is insufficient.

**Deterministic assertions**

- Gate acknowledgement precedes the measured hold; repeated independent target
  reads remain unchanged and the exec rendezvous remains absent until release.
  The expected effects occur afterward. These assertions concern the selected
  actions, not absence of all syscalls.
- Every required start/end CPU sample succeeds and names the same live process
  generation. Per-process user/system counters are nondecreasing. The worker,
  busy-control and sleeping-control samples cover a matched held window, with
  endpoint sampling skew no greater than the declared accounting quantum.
- Declare `hold_min_ns = max(1_000_000_000, 100 * accounting_quantum_ns)` before
  execution. The reported running-process quantum is 10 ms; verify and record
  the meter's resolution rather than treating it as universal. At that quantum
  the minimum measured hold is one second. Use one- and three-second target
  holds, increased before execution if resolution requires it, with three
  repetitions each. Every credited actual interval meets the minimum and has
  no system sleep; do not round a short interval into compliance.
- Over each matched interval, total CPU delta for the busy control exceeds the
  sleeping control's delta. The held production worker's total CPU delta also
  exceeds the sleeping control's delta. These strict directional assertions
  supply a falsifiable production claim without prescribing a CPU percentage.
  Record failures and distinguish invalid measurement from contrary behavior;
  do not silently weaken the comparison or select only favorable repetitions.
- Retain the existing release, expiry and cancellation assertions from proceed/
  activation controls. A shortened expiry control establishes its own allowance,
  not the production timeout's duration; client timeout is not cancellation.

**Measured receipt schema and conditions**

- `hold`: gate/target identity, acknowledgement, before/after target observations,
  release/expiry/cancellation event, requested duration, minimum duration,
  actual continuous-clock interval and per-call sampling brackets, all in ns.
- `processes[]`: role, PID and generation identity at both endpoints,
  `user_cpu_ns` and `system_cpu_ns` before/after, derived deltas, sample times
  and native return/error. Worker and both controls are required; host,
  validator and parked actors have separate records when measured.
- `conditions`: accounting quantum and its calibration evidence, power state,
  system-sleep observation, repetitions, sample cadence and endpoint skew.
  `observer`: its own CPU delta and cadence. Keep sparse/dense sampling checks
  separate so observer work is not attributed to PW.
- `actor_states[]`, when comparing actors: generation, setup/activation/arrival/
  acknowledgement/progress publications and observation boundary. Record the
  internal scope; report aggregate CPU only for the identified processes.

**Controls that must fail**

- Missing gate, early effect/release, changed target, absent rendezvous evidence,
  too-short hold, excessive sample skew or a sleep-overlapped interval.
- Missing/failed CPU samples, an exited worker, changed generation, decreasing
  counters, and busy/sleeping or production/sleeping deltas swapped or equal.
- A receipt presenting process presence as parked-state proof or observer CPU
  as worker CPU. Valid busy/sleeping and held/released fixtures must pass before
  these corrupted observations can establish checker sensitivity.
- The existing premature-effect variants in
  `witness_contract/order_barrier_mutations`, required for the changed hold
  observer by [ordering-control guidance](../tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls).

Use native per-process counters such as `proc_pid_rusage`. Update the waiting
rows and diagram with measured CPU at the stated scope and the independent
resource-ending observations.

### Response: coexistence and amplification, beyond retention size

**Question.** What resident and physical-footprint bytes are observed in a fresh
controller generation handling each small/large admitted response, and which
internal representations coexist despite the retention cap? Restrict the
discriminating native observation to the controller. Host/client framework
allocation, XPC backing and a pipeline-wide peak remain unresolved in version
zero; do not build instrumented Swift binaries or stage rendezvous to resolve them.

The response owner builds the representation/lifetime ledger during account
work, before measurement. Trace the full path in source, including validator
raw/decoded records and final envelope rendering, but do not instrument every
stage. Register `witness_contract/response_footprint` for one external observer
sampling each fresh shipped controller on the named native metrics
`ri_resident_size` and `ri_phys_footprint`, recorded separately in bytes. Retain
the actual interval/cadence and metric accounting limits. Where sampling cannot
name a decoding boundary, leave stage attribution unknown.

A narrow Rust test seam under `unit/rust.unit` asserts internal lengths,
capacities and lifetimes at existing receiver/rendering boundaries. It collects
borrowed scalar summaries without cloning payloads or extending their last use.
This supplies internal assertions, not shipped-process memory measurements.
Keep the native observer external; neither Rust test-runner allocator history
nor internal test instrumentation is credited as production memory.

**Deterministic assertions**

- Both workloads are admitted and contain every expected action, output and
  applicable receipt; retain the existing round-trip/effect checks. Refused or
  truncated output cannot masquerade as a small response.
- Strictly decoded base64 length equals retained host bytes, and its SHA-256
  equals the captured host hash for an untruncated reply. Received and retained
  host counts agree; actual host bytes fit the synthesized host bound. Client
  stdout received/retained counts agree and fit their own allowance; stderr has
  its own count. Final envelope byte count equals the captured output file size.
- The internal success-path boundary sequence is fixed: full client collection,
  capture parsing, typed capture validation/base64 decoding, host parsing,
  envelope construction/sorting, final rendering. The seam checks actual buffer
  lengths against the independent input and `capacity >= length` where exposed,
  and establishes raw/parsed coexistence at the claimed boundaries without
  asserting an allocator-specific capacity or lifetime beyond normal last use.
- The external observer records successful samples from the same fresh controller
  generation, with increasing timestamps, both named metrics present in bytes,
  and at least two samples during its verified lifetime. Required inspection
  errors or missing coverage fail observation rather than yielding zero memory.
  No ordering of small/large memory values or fixed byte threshold is required.

**Measured receipt schema and conditions**

- `sizes`: logical region capacities, actual optional receipt bytes,
  synthesized host bound, host received/retained bytes and hash, base64 character
  count, client stdout/stderr received/retained bytes and allowances, and final
  envelope bytes. Identify each representation; preserve actual wire counts.
- `controller`: PID/generation, executable hash, observed launch/exit and sample
  interval. `samples[]`: bracket timestamps, native return/error,
  `ri_resident_size`, `ri_phys_footprint`. `conditions`: requested/actual cadence,
  observer process and its memory, power/sleep observations, workload/repetition.
- `internal_assertions`: separate unit-case receipt identity, input hash, ordered
  boundary names, lengths/capacities and ownership assertions. Do not align these
  test-process events to a production sample by assumption.
- `summary`: per-metric observed minima/maxima and coverage interval, labeled
  sampled values, not instantaneous peaks. State whether collection/decoding
  boundaries could be located; earlier controller work and exec-child demand
  must not be assigned to an unobserved response stage or added to these metrics.

**Controls that must fail**

- Swapped host/client-stream counters; incorrect retained length/hash; invalid
  base64; missing output/actions/required receipt; truncation; or the synthesized
  bound presented as measured bytes. Valid receipts must first be accepted.
- An omitted/reordered internal boundary, wrong length, capacity below length,
  or a claimed overlap after the source buffer has been dropped. Reuse existing
  receiver rejection controls; do not add another synthetic producer family.
- Missing metric, wrong unit or generation, failed inspection reported as zero,
  out-of-lifetime samples, or missing/reversed timestamps. Exercise the native
  observer against a live touched allocation held through observation and its
  exited generation; detecting brief peaks is outside the claim and this cycle.

Preserve `ReplyMaximumTests`, retention controls and receiver semantics. Do not
sum nonconcurrent maxima, shared views or the two native memory metrics. Update
the response table, diagram and citation together, explicitly leaving host-side
framework storage and unobserved stage attribution unresolved.

### Aftermath: what PW leaves before the harness intervenes

**Question.** Which run-created apparatus resources remain at CLI return after
ordinary completion and after a controlled post-invocation timeout, and what
independent later observations establish their end? Distinguish ordinary
asynchronous retirement, continuing submitted work, surviving descendants,
unresolved cleanup and actual apparatus residue.

Register `run_effects/aftermath_footprint`, reusing
[`RunCapture`](../tests/lib/run_capture.py), fixture process identities/exit
events and the existing lifecycle ownership pattern. Extend
`run_effects/checker_controls` with the new interpretation checks. Use
`runner_exec_lifecycle/closed_streams_leader_exit` and
`runner_exec_lifecycle/worker_dies_during_exec` as live sensitivity controls.

Inventory exact resources before starting PW and observe their independent
ending events, not an arbitrary settling delay. In the timeout path, opening a
gate after CLI return is a harness intervention; record it before observing the
resulting completion. Audit context-manager/finally behavior so `RunCapture.close`,
tree-control release and staging cleanup cannot erase the primary observation.
Use the existing setup/descriptor controls for component facts that public CLI
inspection cannot establish, and label that narrower scope.

**Deterministic assertions**

- Every inventoried object has exactly one state at each required boundary:
  `present`, `absence_confirmed` or `unknown`, with observation/error and owner.
  None is omitted or unclassified. Absence requires identity-qualified evidence;
  failed inspection is unknown, and name absence does not prove unmapped backing.
- Baseline, CLI return and resource-specific ending observations are separately
  identified. Ordinary completion has an identified worker and independent exit
  observation. The timeout path establishes invocation and the held worker before
  timeout, then observes that worker still present at CLI return. Missing these
  required observations fails the case rather than passing an all-unknown ledger.
- The primary pre-intervention snapshot finishes before every post-return harness
  intervention begins, on one declared observer clock. A later snapshot that
  follows gate release, signalling or cleanup is explicitly marked assisted and
  cannot replace the pre-intervention snapshot or prove autonomous teardown.
- The known-survivor control is classified present before fixture cleanup; a
  leader's exit cannot classify its descendant absent. Pre-existing registration,
  requested effects/output and observer artifacts keep their proper categories.
- Choose and record N before execution. Every one of N ordinary runs has its own
  resource identities and boundary counts; distinguish overlapping retirement,
  accumulation and unknowns. Do not require zero residue to obtain a pass, but
  retain failures of subsequent harness cleanup and durable recovery ownership.

**Measured receipt schema and conditions**

- `inventory[]`: stable object ID, type, owner/ownership basis, creation or
  pre-existence evidence, process generation or file/object identity, and category
  (`baseline`, `specimen_effect`, `requested_output`, `apparatus`, `observer`).
- `snapshots[]`: boundary, start/end observer timestamps, CLI-return-relative
  elapsed time, assisted/unassisted status, and one state/evidence/native-error
  entry per inventoried object. Include the expected ending event and whether
  it was observed, still pending, or unestablished.
- `end_events[]`: object identity, event and observation time, independent source
  and outcome. Keep PW's own signal/reap reports separate from observer results;
  erasure, native authority release, exit and reap are different events.
- `interventions[]`: action, target identity, ownership, reason, start/end times,
  native result/error and later observation. `cleanup`: final status and retained
  recovery record. No intervention is silently absorbed into product aftermath.
- `repetitions`: declared N and per-run resource counts. If waiting CPU samples
  are reused after timeout, include their bounded pre-intervention interval and
  conditions separately: unchanged inventory can conceal continuing work.

**Controls that must fail**

- An omitted object/state, missing baseline, unsupported absence, or failed
  inspection relabeled absent. A valid explicit unknown for an optional surface
  is accepted, while unknown cannot replace the required worker observations.
- A reused PID or changed file identity treated as the original object; a live
  descendant classified absent from its leader's exit; the known survivor missed;
  a baseline registration counted as run-created residue.
- Missing snapshot/intervention timestamps, a primary snapshot taken after an
  intervention, or an assisted final clean directory substituted for pre-cleanup
  state. Exercise premature cleanup as well as malformed ledger controls.

Keep requested effects and exec descendants visible even when they are not
apparatus leaks. Shared authority erasure still requires a reaped or
never-launched owner. Update aftermath rows/diagrams/citations with the original
observation and separately recorded intervention outcome.

## 5. Integrate, rotate review and edit

After the three cycles, consolidate supported claims into FOOTPRINT. Its reading
guide defines units, shared backing versus views, conditional quantities and
presence/absence/unknown. Keep the three principal tables and small diagrams
central. Add only interactions that change interpretation, such as:

- Equal wait durations can have different worker/actor CPU demands.
- Equal retained response bytes can conceal different full collection sizes,
  representation overlap and encoding work.
- Identical output artifacts can coexist with different surviving processes;
  CLI timeout and CLI success both need resource-specific end observations.

Each case's designated reviewer receives the full trio, final candidate
graphs/tables, source baseline, assertions and retained observations. The
reviewer reconstructs one consequential claim independently from source and
evidence using the rotated accounting model; another full account is not
required. Require a concrete missing quantity, owner, interval or observation,
or an explanation of why the evidence
supports the claim despite the alternative perspective. Each also checks effects
on the other two cases. Record agreement only at the claim's actual scope.

For each row/diagram pair ask whether the table erased an owner, copy,
overlapping lifetime, activity or release condition, and whether the diagram
asserts more than the evidence. Scrutinize “the reply is bounded,” “the worker
waits,” “the buffer is shared,” and “cleanup completed.” Resolve substantive
disagreement by a distinguishing observation or narrower wording, keeping
unresolved relationships visible. Do not manufacture consensus with broad prose.

Finish with a LIMITS-shaped editorial pass. Remove explanatory tours, repeated
inventories, redundant rows and investigative chronology. Retain distinctions
that change the reader's understanding of demand, ownership or aftermath.
Current tests and scoped observations support the publication; planning history
stays in records. Render again after final edits.

## Verification and evidence handling

Register every added case in [catalog.json](../tests/catalog.json), with actual
equipment, default membership and dependencies, and update owning suite READMEs,
the suite map and relevant coverage/change-verification accounts. Keep cheap
deterministic checker controls in the default battery. The dedicated repeated
resource-measurement cases may be opt-in because of their sampling and workload
cost, but they remain normal dispatcher cases and mandatory for this plan's
acceptance. Missing measurement equipment is not a supported skip.

Only the coordinator runs builds/tests in this checkout. Use a current signed
app from [the build pipeline](BUILD.md), rebuilding if compiled sources change.
Update Meson for native source additions, regenerate worker identity for its
covered inputs, and review ABI/layout/version consequences if those boundaries
change. Preserve the inspected artifact on diagnostic retries. Native XPC,
process-observation and signing work runs in the applicable unsandboxed macOS
environment; follow the repository's diagnostic-and-same-command escalation
procedure for sandbox refusals. Do not attribute them from permission-shaped
errors alone.

Inspect selections with `--list` before execution. A representative final
targeted selection, after registering the new IDs, is:

```sh
PW_TEST_OUT_DIR=tests/out/runs/footprint-targeted-<unique> tests/run.sh \
  --suite unit --suite runner_unit --suite runner_abi_layout \
  --suite runner_c_worker_harness --suite run_effects \
  --suite runner_exec_lifecycle \
  --case witness_contract/held_phase_footprint \
  --case witness_contract/response_footprint \
  --case witness_contract/attempt_effects_wait_for_collection \
  --case witness_contract/max_targets_reply_survives \
  --case witness_contract/order_barrier_mutations \
  --suite source_drift
```

Replace `<unique>` with a fresh valid name; do not redirect a transcript into
the output directory before dispatcher startup. A suite selector includes its
opt-in members; inspect the expanded selection and prerequisites. The above
`run_effects` suite includes the new aftermath case. Add `failure_boundaries`
and applicable validator/consumer suites if admission or receiver behavior
changes; use coordinated selection from [tests/AGENTS.md](../tests/AGENTS.md),
not a narrower memory-only check. Do not treat constructed receiver stress as
evidence of a reachable specimen.

Check generated documents with:

```sh
tests/lib/python.sh docs/generate_architecture.py --check
tests/lib/python.sh docs/generate_limits.py --check
```

Run the current default battery in a separate fresh managed directory for final
acceptance. New source, test or observer changes invalidate affected earlier
credits. Record canonical case IDs, command/configuration, source and binary
snapshots, assertion scope, measurement conditions and result. Reuse evidence
only under the repository's applicability rules; a passing earlier run is not
automatically evidence for a changed observer.

Retain raw counts, samples, gate receipts, process/object identities, before/
after observations, errors and cleanup interventions. Separate deterministic
assertions from machine-dependent measurements. Sleep-overlapped measurements
need a valid replacement run; preserve the original result and its reason.
Keep the accepted default and complementary targeted evidence within the
normal retention policy, preserve unresolved recovery records, and retire
superseded runs only through the helpers. Never unlink `tests/.checkout.lock`.

## Version-zero acceptance

- All three cases have concise claims with conditions, named owners/objects,
  intervals, ending events and support from current tests.
- The preserved summary of the original O/W/M preparation was reconciled against
  the current baseline; the missing frozen scout records are acknowledged, and
  no repeated independent-account gate is claimed.
- Waiting, response and aftermath each completed assessment, question,
  sensitivity-controlled test, native execution and coupled table/diagram update.
- Each new case satisfies its deterministic assertions, complete receipt schema
  and positive/rejected controls; no recorder-only case receives passing credit.
- Response accounting separates capacity, synthesized bounds, actual encoded
  bytes, retained bytes and live-memory observations; coexistence and shared
  backing support any combined quantity.
- Aftermath distinguishes baseline, specimen effects, requested artifacts and
  apparatus state; observations precede harness cleanup, with interventions
  separately retained. Unknown is never promoted to absence. Scoped zero
  apparatus residue is accepted where observed.
- Rendered diagrams preserve owners, copies/shared views, overlaps, activity
  and ending conditions, with bidirectional correspondence to the tables.
- One different-model reviewer per case reconstructed a consequential claim
  and resolved disagreements through evidence or narrower wording.
- Relevant behavioral tests, observer/checker controls, default acceptance and
  documentation checks pass against the credited state. Records identify any
  remaining limited claims without disguising missing required execution.

The final delivery names FOOTPRINT and its figures, states the three material
findings at their measured scope, links the supporting test owners, and reports
verification and unresolved limitations. It does not claim a universal memory
ceiling, idle waiting, or complete teardown where the evidence establishes less.

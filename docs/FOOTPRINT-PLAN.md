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
version-zero acceptance results are claimed. On execution, refresh the source
baseline and preserve the independent accounts as described below.

Deliver the document, its generated DOT/SVG figures, registered tests and
observer/checker controls, current native observations, and completed cross-review.
An optimization is not required. Findings may confirm behavior, narrow a claim,
identify leakage or support later implementation work. Do not turn this into a
general performance benchmark, a replacement limits inventory, an installation
audit or an unrequested runtime redesign.

## Common cases and accounting boundaries

Every initial account and every review addresses this same trio. A section
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
| The synthesized maximum is a conservative constructed reply, not a reachable workload or a memory peak. The existing live-size receipt calls client stdout bytes `runner_reply_bytes`. | [`ReplyMaximumTests`](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift), [`ReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift), [check_max_target_reply.py](../tests/suites/witness_contract/check_max_target_reply.py). | Correct the counter's name and comparisons. Raw host bytes come from `runner_client.transport.runner_reply.bytes_received`; client stdout includes the versioned capture and base64. Keep both. |
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

Up to 32 subagents are authorized. Plan for eleven substantive assignments,
with additional agents reserved for a concrete unresolved disagreement. The
current runtime allows four active agents including the coordinator, so run
at most three delegated tasks concurrently. Do not assume 32 simultaneous
workers. Use fresh contexts (`fork_turns="none"`) for independent accounts and
fresh review assignments; use the inherited model unless separately instructed.

| Wave | Agents and ownership | Handoff gate |
| --- | --- | --- |
| 1: independent reconstruction | O: objects and lifetimes; W: work and amplification; M: demand on the surrounding machine. All three cover all cases, read source and assertions, and write separate accounts. | All three accounts complete and frozen before any account, reconciliation or document draft is shared among them. |
| 2: three investigations | T-Wait applies M's perspective to waiting; T-Response applies W's perspective to response; T-After applies O's perspective to aftermath. Each owns its case-specific test/fixture files and reports a proposed row/diagram update. | Coordinator accepts questions, distinguishes observers from production, assigns shared-file ownership and reviews sensitivity controls before native execution. |
| 3: diagram and document integration | D owns footprint graph entries, generator integration and rendered inspection. Coordinator owns principal tables and prose, incorporating the three test authors' results. | Relationships are drawn and checked before prose is compressed. No final claim outruns its evidence. |
| 4: rotated review | R-O reviews waiting primarily as objects/lifetimes; R-M reviews response primarily as machine demand; R-W reviews aftermath primarily as work/amplification. Each also checks the entire trio for missing interactions. | Each independently reconstructs at least one consequential claim and returns an evidence-based disposition. |
| 5: acceptance | A checks evidence applicability, all three cycles, render/table correspondence, test results and the compact editorial form. Coordinator resolves findings and owns final acceptance. | All version-zero conditions below are met. |

The coordinator alone edits shared integration files such as
`tests/catalog.json` and suite-wide documentation, unless explicitly handed to
one owner. D alone edits `docs/architecture.json` and its generator during its
wave. Avoid simultaneous changes to shared observers: agree the small common
measurement/identity interface first, assign one author, then let case authors
use it. Source edits may proceed in parallel in disjoint files; builds and test
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
`records/footprint-<date>/` directory: baseline, three independent accounts,
reconciliation/questions, review dispositions and acceptance. This plan is the
only inbound documentation link owner for those records. Permanent FOOTPRINT
content links to source and tests, not to planning records. Keep raw execution
evidence in fresh managed `tests/out/runs/` directories; identify locally
available, gitignored evidence honestly. Do not use scratch as its sole store.

Choose these concrete workloads before measurement:

- **Small:** one admitted read against an owned fixture with known bytes, no
  exec and no optional compiled-profile receipt. Keep actual outcome and
  prediction evidence, rather than treating admission alone as success.
- **Large:** reuse the reachable 256-action control-character exec/output
  workload from `max_targets_reply_survives`, including its exact child-output
  checks and actual available profile receipt. Separately pair its
  `independent_query` and `eight_phase_maximum` workloads to isolate repeated
  collection with fixed actions, targets and queries; the latter is not a phased
  version of the escaped exec workload. The
  ordinary/declaration phase cap is eight; sixteen phases requires actor form.
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

## 1. Obtain three independent accounts

Give O, W and M separate initial packets containing only the task scope,
common-case table, baseline/repository access, applicable working rules and
their accounting obligations. Do not include another account, a footprint
draft, preferred conclusions or coordinator-selected answers. Each reads the
relevant documentation, implementation and actual test assertions.

| Account | Reconstruction obligation |
| --- | --- |
| O: objects and lifetimes | Identify backing objects, allocations, mappings, descriptors and processes. Follow acquisition, ownership, transfer, overlapping lifetimes and release evidence. |
| W: work and amplification | Follow polling, process checks, repeated collection, encoding, transport, decoding and cleanup. Explain scaling with elapsed time, phases, actions, payload bytes and repeated runs. |
| M: surrounding machine | Identify observable CPU activity, memory occupancy, capacity held and post-run state. Separate PW from observer/test demand and record what inspection can actually establish. |

For **each** of the three cases, require:

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
as questions until supported. The coordinator may clarify a packet without
exposing another account. Freeze all three reports before reconciliation.

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
relationships next, including unresolved edges, before compressing the prose.
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

Register `docs/FOOTPRINT.md` in the generator's document destinations. Add small
graphs with `document: "docs/FOOTPRINT.md"`, using underscore-separated graph
IDs and hyphenated file stems, initially:

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
explicit labels; a generic arrow must not silently assert a copy. Mark
unestablished XPC/Foundation backing relationships as unresolved. Do not infer
physical allocation from two language-level values or sum per-process RSS as
unique system memory.

Use globally unique diagram IDs and put corresponding IDs in principal rows
and graph facts so a reviewer can trace both directions. Keep generated
supporting tables small and avoid duplicating the principal claim prose.
If an unmeasured relationship needs source-only support, extend the existing
worker-graph scoped-citation/source-only handling narrowly to footprint graphs;
retain explicit unsupported-fact labeling and the existing check requirements
for other graphs. Do not cite an unrelated passing test to satisfy validation.
Extend [architecture generator controls](../tests/suites/source_drift/architecture.py)
for the new destination, scoped support, stale output and input discovery.
Update its owning contract description if that behavior changes.

Reuse limits placeholders/spans for limits quoted in figures/prose; register
FOOTPRINT with the limits span generator if needed. Do not copy numeric limits
into an independently maintained table. Keep measured observations distinct
from manifest constants. Add the document to the README documentation index and
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

### Waiting: measured demand during an independently held phase

**Question.** How much CPU time accumulates in the identified worker during a
validator-gate-acknowledged hold with no observed requested effect, and how does adding parked
actors change that demand? The source establishes active polling; it does not
establish near-zero CPU, one fully occupied core, or the aggregate effect of
several workers. Distinguish these with per-process CPU deltas over known holds.

Extend the acknowledged gate machinery in
[check_ordering.py](../tests/suites/witness_contract/check_ordering.py) and the
existing validator/exec fixtures. Register
`witness_contract/held_phase_footprint`. Retain the original independent target
and helper observations before interpreting the envelope. Credit only their
observed action scope, not absence of all syscalls.

- The existing gate directly observes validator acknowledgement and target PID;
  the production control flow connects that collection to worker phase arrival.
  Describe this as a source-qualified collection gate with independent effects
  and process observations, not a direct external read of `phase.arrived`.
  For actor-state confirmation, add a narrow host/harness snapshot of
  acquire-loaded arrival, acknowledgement and activation publications, paired
  with each process generation. Label its internal observation scope.
- Take CPU samples after gate acknowledgement and just before release, retaining
  the qualified arrival evidence above. Retain sample-call brackets, actual interval,
  user/system CPU counters, process generation, OS/hardware/power conditions,
  sample cadence, system-sleep observations and observer CPU. Measure host,
  validator and parked-worker demand separately where identities are available.
  Use native per-process counters, such as the SDK's `proc_pid_rusage`, rather
  than a displayed instantaneous CPU percentage.
- Compare two sufficiently separated held durations with fixed actions/queries,
  repeat each, and compare one versus several confirmed parked actors. Begin
  with short holds comfortably inside production allowances; increase duration
  only if timer resolution or noise prevents distinguishing the accounts.
  Retain every repetition and the actual distribution, not just the best run.
- Exercise release, expiry and cancellation endings using the existing proceed
  and activation controls. A shortened injected allowance is evidence about
  that control, not the production timeout's duration. Do not change the worker
  wait merely to measure it or identify a client timeout as cancellation.
- Validate the meter with independently active and sleeping children, absent/
  exited/reused-PID cases and failed inspection. Compare sparse/dense sampling
  and a minimally observed hold to expose observer effects. Reject missing or
  too-short intervals and attempts that proceeded early. Keep raw unknowns.
- Run `witness_contract/order_barrier_mutations` for the changed hold observer,
  as required by [ordering-control guidance](../tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls).

Assert deterministic ordering/identity/count facts exactly. Machine-dependent
CPU results are scoped measurements with conditions; avoid an arbitrary
cross-machine utilization threshold. If the meter cannot separate its controls,
repair it before crediting a result. Update waiting rows and diagram together,
including whether multiple parked processes explain aggregate demand.

### Response: coexistence and amplification, beyond retention size

**Question.** At which collection/decoding/rendering stages do the substantial
representations coexist for the small and large admitted workloads, and how
does that coexistence appear in measured live memory? Competing accounts may
place the largest demand in host encoding, client base64/capture encoding, or
controller raw/parsed/final-envelope overlap. Source settles the retention
cap's meaning but not the dominant measured stage or private framework storage.

Extend `witness_contract/max_targets_reply_survives` with correctly named size
receipts, and add `witness_contract/response_footprint` for the paired workloads
and memory observations. Preserve the existing round-trip and effect checks.
Correct `runner_reply_bytes` and dependent comparisons in
`check_max_target_reply.py`: compare raw host bytes to the synthesized host
bound, client stdout to its own retained allowance, and record final envelope
bytes separately. Update receipt consumers/docs with the labels.

- Record logical evidence/authority-region capacity, actual receipt bytes,
  encoded host bytes, retained host bytes, base64 characters, encoded client
  capture stdout/stderr, controller retained counts and final output bytes.
  Decode retained base64 independently and verify exact length/hash against its
  counts. Use actual emitted bytes rather than reserialization to claim exact
  wire size. Keep the synthesized union distinct from reachable native cases.
- Build a stage ledger through host collection/encoding, client capture,
  controller full collection, capture parse, typed validation/base64 decode,
  host parse and final envelope sorting/rendering. Record creation and last-use/
  disposal boundaries. Include validator raw lines/decoded records where they
  materially affect the large workload.
- Establish controller coexistence through a narrow internal test seam around
  the production receiver/rendering functions under `unit/rust.unit`. Observe
  real live vectors/strings/values at named boundaries, including lengths and
  allocation capacities where accessible. A scripted diagram or unrelated
  mock serializer is not evidence of those lifetimes. No new public wire fields
  are needed. Instrumented measurements must retain the exact source delta and
  use the same serialization path. Collect borrowed scalar summaries at existing
  boundaries: do not clone payloads, retain references beyond normal last use,
  or accumulate all stages' snapshots in the measured process. The observer
  must not manufacture the coexistence it reports. Use fresh process generations
  for machine-memory measurements and separate test-runner allocator history
  from the production demand; unit assertions establish internal quantities.
- Use bounded stage rendezvous in disposable native instrumented builds only
  where external sampling cannot otherwise identify the overlap. Pair their
  outputs with uninstrumented admitted runs by stable semantics and declared
  workload/output invariants, not identical whole-wire bytes: identities,
  timestamps and timing records naturally differ. Preserve each run's actual
  byte counts and report the pause's effect. Before measurement select and name
  the native memory metrics, for example resident bytes and physical-footprint
  bytes, recording each separately with its shared-page/accounting limits.
  Distinguish known application allocations, these process metrics,
  allocator-retained pages and unknown XPC/Foundation storage. Bound response
  samples by the named stages; earlier exec-child demand in the large workload
  must not be mislabeled as response memory.
  Sampling alone supplies observed maxima, not proof of an instantaneous peak.
- Extend receiver controls with equal-retained-prefix/different-total-output
  producers, keeping synthetic over-cap cases separate from admitted workloads.
  Challenge swapped host/capture counters, omitted representations, invalid
  base64/counts, truncated responses, missing actions/output, and unavailable
  receipts misclassified as large. A controlled brief allocation tests whether
  the observer misses short peaks; narrow peak wording if it does.

Preserve `ReplyMaximumTests`, client retention controls and receiver rejection
semantics. Do not sum stage maxima from different times or count shared views
twice. Report a supported scoped memory observation even if private framework
copy counts remain unresolved. Update the response table, overlap diagram and
test citation as one change.

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

- Snapshot relevant surfaces before starting PW. Inventory exact owned paths,
  file identity/content where appropriate, known process generations and
  baseline registration. List requested output and fixture artifacts separately.
  Installation fixtures must already be in the baseline before measuring a run.
- Start observation while identities are available, using peer credentials,
  process start/generation information, ancestry and exit events. At CLI return
  record which identified host/worker/validator/issuer/exec processes remain,
  which exits are already independently known, and which could not be inspected.
  Observe again at actual resource-specific end events. Do not wait an arbitrary
  duration and call the resulting snapshot the CLI-return state.
- Record elapsed time from CLI return to every observed ending or harness
  intervention. Keep PW's termination/reap reports separate from independent
  observer results. In the held-timeout path, reuse the CPU observer for one
  bounded pre-intervention interval where available: unchanged inventory can
  conceal continuing worker polling and host collection.
- For the interrupted path, require independent evidence of invocation and a
  held worker before allowing the client's timeout. At CLI return first record
  continuing state. Opening a test gate afterward is a harness intervention:
  record it before observing subsequent completion, never as autonomous cleanup.
  The ordinary path supplies unsteered retirement observations.
- Trace named shared-memory objects, descriptor references and mappings using
  their actual ownership. Name absence is insufficient for backing reclamation.
  Use existing host setup/descriptor controls for a targeted component
  observation where public CLI visibility cannot establish a mapping's lifetime;
  label that scope. Preserve unknown state instead of declaring global absence.
- Take the product-aftermath snapshot before any `RunCapture.close`, tree-control
  release, fixture signal, session removal or staging deletion that could change
  it. Audit context-manager/finally cleanup ordering. Write a separate intervention
  ledger with action, identity, reason, time, result and subsequent observation.
  On failure preserve both the earlier state and durable cleanup ownership.
- Challenge the observer/checker with a known survivor, a PID-generation mismatch,
  failed inspection, an exited leader with a live descendant, an unchanged path
  with replaced object identity, and a pre-existing registration. Include a
  premature-cleanup control: a clean final fixture directory must not pass in
  place of a missing pre-cleanup snapshot.
- Choose and record a small fixed N before execution. For N identified ordinary
  runs, record how many run-created resources remain at each CLI return and
  after their observed ending events. Count baseline objects once. Report
  overlapping retirement, accumulation and unresolved inspection separately;
  a flat count can conceal replacement generations or continuing work.

Keep requested file effects and exec descendants visible even when they are not
apparatus leaks. Keep private token erasure, shared authority erasure, native
extension release, process exit and reap separate. `AuthorityCustody.finish`
cannot safely erase shared storage owned by an unresolved live actor; include
that condition wherever relevant. Update aftermath rows/diagrams/citations with
the pre-cleanup observation and separately recorded harness outcome.

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

R-O, R-M and R-W each receive the full trio, final candidate graphs/tables,
source baseline, test assertions and retained observations. They reconstruct
one consequential claim in their assigned section independently from source
and evidence using the different accounting model. Require a concrete missing
quantity, owner, interval or observation, or an explanation of why the evidence
supports the claim despite the alternative perspective. They also check effects
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
- Initial O/W/M accounts were independent until all three were complete; their
  disagreements became explicit distinctions or discriminating questions.
- Waiting, response and aftermath each completed assessment, question,
  sensitivity-controlled test, native execution and coupled table/diagram update.
- Response accounting separates capacity, synthesized bounds, actual encoded
  bytes, retained bytes and live-memory observations; coexistence and shared
  backing support any combined quantity.
- Aftermath distinguishes baseline, specimen effects, requested artifacts and
  apparatus state; observations precede harness cleanup, with interventions
  separately retained. Unknown is never promoted to absence. Scoped zero
  apparatus residue is accepted where observed.
- Rendered diagrams preserve owners, copies/shared views, overlaps, activity
  and ending conditions, with bidirectional correspondence to the tables.
- Different-model cross-review reconstructed consequential claims and resolved
  disagreements through evidence or narrower wording.
- Relevant behavioral tests, observer/checker controls, default acceptance and
  documentation checks pass against the credited state. Records identify any
  remaining limited claims without disguising missing required execution.

The final delivery names FOOTPRINT and its figures, states the three material
findings at their measured scope, links the supporting test owners, and reports
verification and unresolved limitations. It does not claim a universal memory
ceiling, idle waiting, or complete teardown where the evidence establishes less.

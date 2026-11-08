# JSON as porcelain: representation and ownership experiment

## Question and intended result

Can PolicyWitness express its evidence and the rules for making claims in fixed,
explicit data structures, carry those structures across its response path, and
produce JSON where people and external consumers need it?

Start with that architecture. JSON is a useful public format; internal coherence
need not depend on JSON object shape, string-keyed lookups, or repeated encoding
and parsing. A fixed model means declared records, variants, references and
ownership rules. It can contain variable-length collections and byte buffers;
it does not mean allocating maximum-sized arrays or transmitting language memory
layouts.

This is an exploration with an implemented experiment and a disposition. A
structural improvement can justify the design without beating the existing
implementation on speed or memory. The experiment must demonstrate the claimed
improvement: moving evidence integrity into identifiable model boundaries,
eliminating unnecessary representations, or making ownership and lifetimes
explicit. Merely replacing JSON syntax with a binary codec does not answer the
question.

Schema and protocol changes are available in this pre-1.0 project. Existing key
order, nesting, base64 placement and duplicate representations are design choices,
not acceptance requirements. Preserve the observations, their provenance and
their interpretation limits. State any proposed change to those meanings
explicitly; a version bump alone cannot establish evidentiary equivalence.

Execution delivers a model and ownership account, a working response-path
prototype, independent correctness controls, a resource account, and a decision
to pursue adoption, retain a narrower result, revise a specific assumption, or
close the experiment. Production migration is a subsequent bounded scope; a
successful slice is evidence of feasibility, not coverage of every reply family.

## Starting point

This continues the capture-conversion question in
[FOOTPRINT-OUTFLOW](records/FOOTPRINT-OUTFLOW.md#direction-2-remove-one-redundant-capture-conversion-copy)
and broadens it from copy removal to representation. The current response path is:

```text
worker publications / validator records
  -> Swift result objects
  -> host JSON Data over XPC
  -> base64 inside client-capture JSON on stdout
  -> generic and typed capture in Rust
  -> decoded host JSON bytes and a generic result tree
  -> another envelope tree and rendered JSON String
```

Source establishes several useful premises before experimentation:

- The host already builds typed results. Its
  [reply encoder](runner/Sources/PWRunnerCore/PWRunnerReply.swift) also checks
  disposition, phase partitions, validator ownership, operation evidence and
  ordering. Encoding is an integrity boundary, not only formatting. Decoding
  checks a different subset. Removing Codable must not silently remove either
  set of checks.
- [Reply degradation](runner/Sources/PWRunnerCore/PWRunnerService.swift) preserves
  conflicting observations while withholding comparisons, and has an independent
  minimal reporting-failure path. A model that can represent only coherent
  successes cannot replace it.
- The [XPC interface](runner/Sources/PWRunnerCore/PWRunnerAPI.swift) already carries
  `Data`. The [client session](runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
  owns acquisition and submission observations, but treats result bytes as opaque.
  [Capture construction](runner/Sources/PWRunnerCore/PWRunnerTransport.swift) adds
  base64 and [emission](runner/Clients/PWRunnerClient/main.swift) encodes the wrapper.
- The [Rust receiver](controller/src/runner_client.rs) retains generic transport,
  makes a typed copy, decodes bytes and parses the host result. The
  [run flow](controller/src/run_flow.rs), [disposition reader](controller/src/disposition.rs)
  and [actor reader](controller/src/actor_evidence.rs) derive or check meaning
  through JSON-tree access. [Rendering](controller/src/json_contract.rs) constructs
  another tree, sorts it and creates a complete output string.
- [FOOTPRINT](docs/FOOTPRINT.md#response-storage-and-transport) identifies scoped
  coexistence and observations. Its historical samples are not a fresh comparison
  baseline. A `Data` or borrowed view does not itself prove shared backing or
  zero-copy transport.

The narrower borrowed-base64 change is an alternative independent improvement,
not a prerequisite. This experiment may supersede it on an adopted path; it
need not reproduce its incremental implementation first.

## Boundary of the experiment

Explore the complete **host result -> XPC client -> controller -> public output**
path. The target is a versioned typed result representation, an opaque relay,
controller admission into typed records or validated views, and a JSON projection
from those records. Raw framing around today's host JSON can be a transport
control, but cannot alone establish the model hypothesis.

Keep sandbox application, worker shared-memory publication, live validator
queries, phase release and resource ownership at their existing process
boundaries. Specimen JSON input, reservation-control JSON and validator NDJSON
can remain boundary formats in the first experiment. Inventory their adapters
and identify where they end; retaining them does not require using JSON trees
for result coherence. Do not expand into replacing every JSON use in the repo.

The [host wait round](runner/WORKER-WAIT-EXPLORATION-PLAN.md#host-follow-on-round),
ARM/hint experiments, evidence-region geometry and authority/custody disposal
remain separate work. Freeze the prototype against identified accepted source.
If another accepted change affects its code or comparison equipment, refresh the
baseline and affected observations rather than combining different foundations.

The [core ideas](AGENTS.md#core-ideas), [wire contract](docs/CONTRACT.md) and
[failure evidence contract](tests/FAILURE-PROPAGATION-CONTRACT.md) remain the
semantic foundation: fresh processes, observation before attribution, collection
closure before numbered release, supported ordering claims, partial evidence,
and independently observed cleanup. Changing representation grants no new worker
authority and does not turn an observed return value into a causal explanation.

## 1. Specify the model and the questions that could defeat it

Create `records/JSON-AS-PORCELAIN-EXPERIMENT.md` before prototype implementation.
This plan owns that record. Record the source baseline, scope, proposed model,
unresolved choices and the controls that will decide them. Keep native evidence
in dispatcher-owned output, identified from the record.

Use three distinguishable layers:

1. **Received and observed evidence.** Exact retained transport bytes, native
   observations eligible for publication, partial records, unknown bounded codes,
   conflicts and origin/association information. For each raw capture, keep its
   origin, actual received and retained counts, completeness and admission state.
   A hash or reserialization is not a replacement for the retained original bytes.
   This layer cannot expose unpublished worker fields as observed facts.
2. **Admitted records and supported claims.** Explicit references to actor,
   process generation, phase, action and supporting observations; named validation
   boundaries; claims whose construction requires the appropriate support.
   Structural decoding, evidence integrity and native truth are distinct. A valid
   codec record does not establish a live generation or causal ordering.
3. **Presentation.** JSON field names, nesting, optional/null conventions,
   deterministic ordering and byte encoding. Rendering reports admitted facts,
   rejected captures and diagnostics; it does not repair evidence or classify
   lifecycle events as a side effect of serialization.

Contradictory observations are legitimate data to retain. Make unsupported
claims hard to construct without making conflicting evidence impossible to
record. Avoid a universal `Unknown(JSONValue)` escape hatch: opaque bytes for an
uninterpretable record are different from a mutable generic semantic tree.

Produce a compact mapping from current observations/checks to their proposed
record, owner, validation point and JSON projection. Cover the encoder-only gates
and degraded paths explicitly. Check each field for duplicated ownership,
derived versus observed meaning, absence versus false, integer width/sign, byte
versus text semantics, and associations currently reconstructed from paths or
strings. Per-language storage may differ while the evidence contract agrees.

Before coding, select a small set of falsifiable structural claims. Include:

- One authoritative owner for each retained fact or payload; derived views
  reference it rather than keeping independently mutable copies.
- Named claim constructors/admission functions require their supporting records.
- The chosen admitted internal slices do not require a general-purpose JSON tree.
- JSON export is a projection with explicit failure behavior.
- Rejected and conflicting evidence survives independently of claim construction.

For each, name a concrete counterexample and an observation that would refute the
claim. Lines of code, successful round trips and use of structs are insufficient.

## 2. Choose a transport and output design for the prototype

Choose the model before the codec. Compare suitable existing Swift/Rust codec
support against the actual requirements: native bytes, exact integers, explicit
presence/variants, bounded lengths and nesting, version admission, rejection of
ambiguous encodings, unknown-record handling, build dependencies and independent
inspection. Inspect the chosen specification and implementation behavior. Select
one candidate to implement; record a failed fit before trying an alternative.
There is no requirement to build a custom codec or benchmark a catalog of them.

A schema may own record/tag/field definitions and generate language bindings.
Semantic checks and independent fixtures must still be capable of disagreeing
with a producer using those bindings. Avoid transmitting Swift/Rust object memory
or native pointers as a wire layout. For borrowed binary views, validate lengths,
offsets, alignment and lifetime before access, and preserve the immutable owner.

Design the client framing separately from the result encoding. The relay should
carry its own acquisition/submission facts and opaque host bytes without needing
to understand the host result. Specify magic/version, record kinds, length bounds,
completion, trailing data, duplicate records, unknown tags and short-read behavior.
Keep announced lengths separate from bytes actually received. A successful early
header cannot stand in for a missing payload or terminal observation.

Write a decision table for unsupported versions, malformed metadata, incomplete
payload, receiver retention loss, no reply and client timeout. State which facts
each completed frame establishes and when submission remains unknown. Preserve
single invocation and the prohibition on replay after submission. Retain existing
failure precedence unless a deliberate new reading rule and its evidence justify
changing it; record that rule with the protocol change.

Reception must have bounded retained storage and bounded parser work. If exact
received counts remain part of the contract, drain/count excess bytes without
retaining them. Specify receiver liveness, deadlines and the disposition of a
producer that never closes its streams; the current complete-output collector
does not supply an independent receiver deadline. If reception ends early, count
the bytes actually drained and leave the unobserved producer total unknown.
Drain stderr concurrently where required to avoid pipe deadlock. Closing a pipe
at a retention limit can change producer behavior; it needs an explicit contract,
not an unreported implementation shortcut. Include integer-overflow, allocation
failure, interrupted I/O and producer/consumer death in this design.

Begin with a self-contained JSON stdout export from the new model. It may change
schema, organization and the location of exact raw captures; it need not retain
the old duplicate trees or base64 nesting. Typed direct serialization and
incremental byte encoding can avoid a global tree. Decide how deterministic
output is obtained and how partial output is reported when a writer fails; a
broken stdout cannot be repaired by promising a complete error envelope on it.
The host can still produce one whole XPC `Data` while the later path is streamed;
do not describe that as end-to-end streaming.

A manifest plus binary-artifact bundle is an optional further experiment, not a
prerequisite. If it becomes necessary to the proposal, first specify portability,
paths, permissions, partial writes, publication/completion, missing artifacts and
cleanup ownership. Keep JSON available as an explicit export. Do not silently
replace the user's single-file deliverable with unmanaged sidecar files.

Draw the proposed buffer lifetimes per process: authoritative payload, borrowed
views, decoded records, temporary copies, handoff and earliest release. Separate
source-established ownership from unobserved XPC/Foundation physical copying.

## 3. Implement two complete experimental slices

Use an isolated prototype checkout/build and dispatcher-owned fixtures. Exercise
the real host/client/controller path in a staged signed app; a mock serializer
alone cannot establish integration. Experimental binaries identify their own
source, protocol and provenance and cannot masquerade as the accepted app.

Carry two slices from production observation capture through model construction,
encoding, relay framing, controller admission, independent reading and JSON:

- **Publication and order:** ordinary multi-phase execution and an actor visit,
  including validator collection, closure, numbered release, acknowledgement and
  the support for `query_first`. Include an unavailable query and a later failure.
- **Process ending and partial evidence:** exec or worker completion, termination
  request/native result, owned reap and an incomplete or conflicting outcome.
  Include actor-associated custody/transfer observations sufficient to challenge
  cross-actor references; bearer token bytes remain outside response evidence.

Use actual typed records and raw byte owners across the selected slices. A codec
that merely encloses the old result JSON, or a Rust adapter that reconstructs the
old generic tree to perform all integrity checks, is a useful control but not a
successful model experiment. Mark any unconverted families and temporary adapters
explicitly; the prototype need not migrate every operation to answer feasibility.

Move the selected semantic checks into named model/admission functions before
retiring their encoding-time implementations. Preserve an evidence-bearing
degradation path and a minimal fallback independent of the rich result encoder.
The fallback records which evidence survived and withholds unsupported claims;
it cannot declare retention merely because an error object was emitted.

## 4. Try to falsify the design

Use independently authored records and bytes as well as live runs. Codec
round-trips establish agreement, so add an independent reader or narrow oracle
that does not reuse production semantic validation. Existing
[consumer](tests/lib/consumer.py), [blackbox controls](tests/suites/blackbox_e2e/README.md),
[failure boundaries](tests/suites/failure_boundaries/README.md) and
[lifecycle oracle](tests/lib/lifecycle_oracle.py) are starting points; adapt their
assertions to the new contract rather than teaching every checker the producer's
assumptions.

| Question | Refuting control and required observation |
| --- | --- |
| Does typed coherence have an owner? | Remove closure or acknowledgement, substitute another actor/generation/phase, or introduce a future ordinal. The claim is refused/withdrawn; independently published facts remain. |
| Is collection closure still meaningful? | Add a late validator record. It cannot qualify a closed collection or create `query_first`. |
| Are independent endings preserved? | Supply successful signalling with failed/unconfirmed reap, partial execution, or conflicting status. A requested effect cannot replace an observed ending. |
| Can the model retain failure? | Force integrity rejection and ordinary encoding failure; then failure of evidence-preserving encoding with a successful minimal fallback; then minimal-fallback or emission failure. Check retained facts, original-summary diagnostics, withheld comparisons and loss reporting where output exists. Total reporting failure leaves an outer transport/process failure and whatever bytes survived, not a guaranteed self-report. |
| Is transport admission independent? | Use unsupported versions with plausible bodies; short/truncated frames; inconsistent lengths; duplicate/unknown records; trailing bytes; invalid text; exact/over bounds; EOF and combined faults. No unearned submission or worker claim may survive. |
| Are bytes and types preserved? | Use arbitrary payload bytes, embedded NUL, integer boundaries and wrong scalar kinds. Verify exact retained bytes and distinctions between missing, false, zero, unknown and invalid. |
| Is JSON only a projection? | Render the same admitted model through the JSON exporter and an independent semantic inspector. Neither rendering nor key order can change claim eligibility. |
| Is ownership real? | Observe backing identity or allocation boundaries where claimed; release redundant stage-local storage while retaining each borrowed view's authoritative backing. Check lifetime restrictions, failure cleanup and idempotence. Length equality alone cannot prove borrowing. |
| Are output failures honest? | Interrupt frame emission and JSON output at defined boundaries; retain nonzero/failure status and any partial bytes without claiming a complete artifact. |

Use compile-time rejection tests only for specific construction restrictions
actually promised by the API. Runtime controls remain necessary for received
data and cross-record facts. Combined faults must not hide unrelated observations.

Compare old and new paths by an explicit observation/provenance inventory, not
whole-wire byte equality across different schemas or native runs. Stable authored
fixtures can pin exact bytes of the selected new wire/export formats. Live checks
retain independent file/process effects and identities. The old implementation is
a useful comparator, not the sole oracle for what evidence is correct.

Register prototype cases with their real equipment. Use the coordinated
admission/transport checks in [tests/AGENTS.md](tests/AGENTS.md), including affected
Rust and runner units, framing/failure boundaries and independent consumers. Run
the signed end-to-end slices with witness and lifecycle controls. Collection,
release or eligibility changes require `witness_contract/order_barrier_mutations`;
include that control when claiming the migrated ordering interpretation remains
equivalent. A production adoption proposal also needs full-family coverage and
the default battery, not only the experimental slices.

## 5. Measure cost and judge architectural benefit

Before comparing, record representative small, query-dense, large-byte, actor and
failure workloads; matched build settings; executable/reader identities; and the
questions each instrument answers. Exercise the implemented slices: reuse
applicable footprint workloads and controls, or declare a representative variant
when an existing workload requires unconverted families. Constructed transport-only
inputs can test large payloads but cannot claim live execution coverage. Do not
expand the migration solely to run every historical workload. Whole-controller
samples do not locate parser stages, and they do not measure host/client demand.
Account separately for each changed process and for the observer. Include created
resources, retained bytes/lifetimes, copies or allocations where observable, CPU
and whole-request latency. Leave unavailable metrics unestablished.

The primary acceptance claims are structural. Name which former JSON-dependent
invariants now have explicit owners, which unsupported constructions or admissions
the controls reject, which duplicate mutable stores disappear, and which failure
cases the model can express directly. Record remaining generic representations,
unsafe/unchecked escape routes, code-generation/tooling burden and duplicated
validators. Source review and independently mutated fixtures must support the
account; reduced source size is neither necessary nor sufficient. Give every
structural claim selected before coding an established, refuted or unestablished
disposition; a smaller successful cleanup cannot silently replace a failed model
claim.

Performance superiority is not required. Flat or slower measurements can support
adoption when a demonstrated structural gain warrants their bounded cost. Explain
resolved regressions and proposed tradeoffs; an unexplained cost, lost evidence,
unbounded parser or unresolved ownership failure is not cured by cleaner types.
If claiming a quantitative speed/memory improvement, freeze an appropriate
matched schedule, uncertainty and decision rule before counted comparisons, use
arranged quiet conditions, and retain contrary trials. Do not rerun until a
preferred result appears or import the host-wait plan's every-pair performance
gate as an architectural acceptance requirement.

## Disposition, integration and retirement

After the two slices and their controls, record one of:

- **Pursue adoption:** the model and ownership claims hold, difficult failures are
  represented, and observed costs are acceptable. Specify the remaining families,
  consumers, documentation and migration work as a bounded follow-on.
- **Retain a narrower result:** for example, typed admission or raw relay framing
  helps, while the larger transport/model proposal does not. Name the evidence
  for that boundary and do not claim the full hypothesis succeeded.
- **Revise a named assumption:** a concrete model/codec/ownership failure has a
  plausible bounded alternative. Record what would refute the revision before
  implementing it; avoid an open-ended search through architectures.
- **Close without adoption:** the design needs pervasive generic-tree fallbacks,
  cannot preserve failure evidence, adds unjustified ownership complexity, or has
  unacceptable costs. Preserve the useful negative result and its evidence.

No production compatibility layer is required merely to preserve a retired
pre-1.0 encoding. An adoption scope updates the appropriate versions through
[contract.json](docs/contract.json), producers, readers, fixtures, goldens and
public documentation together. Exact host/worker source identity and compiled
layout agreement remain separate from public schema versions. Update architecture,
build and footprint accounts through their owning manifests when their described
boundaries or mechanisms change. Preserve external-runner list/reconcile/removal
recovery even when execution rejects an older protocol.

Builds and native trials remain serialized under the checkout lock, with compiler
concurrency capped at two. Follow existing test output, staging, signing and
cleanup guidance; parallel read-only review does not authorize overlapping native
comparisons. This plan does not request ARM, sleep/wake or competing-load trials.

The coordinator owns the experiment record, evidence applicability and disposition.
Keep raw receipts under managed test output with source and binary identities.
At closeout retain necessary evidence through the existing helpers, transfer
lasting conclusions into the associated outflow or accepted behavior account,
and retire the temporary record and this plan when no experiment or adoption
dependency remains. A summary cannot replace missing raw observations credited
by the decision.

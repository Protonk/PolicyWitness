# JSON as porcelain: schema-owned evidence records and a JSON projection

## Question and intended result

Can PolicyWitness describe its reply evidence as one owned schema of fixed
records, generate the producer, the admission reader and the public JSON
projection from that schema, and keep JSON only at the public boundary?
Collections and byte buffers remain variable-length; a fixed model means
declared records, references and ownership rules, not maximum-sized arrays or
language memory layouts.

Implement an experiment that tests this architecture. Structural clarity can
justify it without a speed or memory win: identifiable integrity boundaries,
fewer redundant representations, explicit ownership and lifetimes, and one
definition of each record instead of three. Replacing JSON syntax with a binary
codec alone does not answer the question.

Schema and protocol changes are available. Key order, nesting, base64 placement
and duplicate representations are open choices. Preserve evidence meanings or
identify and justify their deliberate revision; a version bump does not establish
equivalence. Deliver the schema and model, a resolved codec decision, a working
prototype, independent controls, a cost and maintenance account and a
disposition. Production migration is a bounded follow-on.

## Starting point

This broadens [capture conversion](records/FOOTPRINT-OUTFLOW.md#direction-2-remove-one-redundant-capture-conversion-copy)
into a representation experiment; borrowed-base64 optimization is no prerequisite.
The source boundaries in scope are the [Swift reply](runner/Sources/PWRunnerCore/PWRunnerReply.swift)
and the evidence records it composes, the [client relay](runner/Clients/PWRunnerClient/PWRunnerClientSession.swift),
[capture encoding](runner/Sources/PWRunnerCore/PWRunnerTransport.swift),
[Rust receiver](controller/src/runner_client.rs), [run assembly](controller/src/run_flow.rs),
[disposition](controller/src/disposition.rs)/[actor](controller/src/actor_evidence.rs)
readers, [JSON renderer](controller/src/json_contract.rs) and the Python
[consumer](tests/lib/consumer.py) that reads the public output.

An inventory of the reply-side Swift sources (2026-11-08, commit `e08ba40c`)
grounds the reorientation. Re-count against the frozen baseline before relying
on these figures:

| Measure | Count |
| --- | --- |
| Codable record types on the reply side (inbound request types excluded) | 89 |
| Stored fields across them | about 700 |
| String and optional String fields | 286 |
| Integer fields of every width and sign, including optionals | 186 |
| Bool and optional Bool fields | 38 |
| Nested record or optional record fields | 87 |
| List-of-record fields | 24 |
| Enumerations with raw values | 2 |
| String-keyed maps | about 6 |
| Untyped property-list values (entitlements) | 1 |
| Raw byte fields in the reply | 0; bytes travel as hex or digest strings |
| Custom `encode(to:)` or `init(from:)` bodies | about 30 |
| Typed Rust structs for the host reply | 0 |
| Generic `.get("...")` reads of the host reply in the Rust readers | about 80 |

The primitive menu the reply needs is bool, integer, string, bytes, optional,
list, record and string-keyed map. Floats, heterogeneous arrays and arbitrary
nesting are unused. The custom coders carry validation and presence rules, not
shape; those rules must be rewritten under any codec. The controller's reading
is entirely generic, so typed admission in Rust is the largest body of work
whatever transport is chosen.

Two premises affect the redesign: Swift reply encoding enforces integrity checks
that decoding only partly repeats; [service degradation](runner/Sources/PWRunnerCore/PWRunnerService.swift)
must preserve conflicting observations while withholding comparisons. Inventory
both sets of checks and their degraded paths before replacing them.

## Boundary of the experiment

Prototype **host result -> XPC client -> controller -> public JSON** from one
schema: generated Swift writers, generated Rust readers and typed records,
generated Python contract tables for the independent consumer, and a JSON
projection from admitted records. Sandbox application, worker publications,
validator queries, release and resource ownership stay at their existing process
boundaries. Specimen JSON, reservation JSON, validator NDJSON and the eleven
inbound request record types remain boundary adapters outside the schema.

Host-wait/ARM work, evidence geometry and custody disposal remain separate.
The approved [host follow-on round](runner/WORKER-WAIT-EXPLORATION-PLAN.md#host-follow-on-round)
changes host wait and validator decoding sources; sequence this experiment
against it explicitly, identify the accepted source baseline, and refresh
affected observations if that baseline changes. The [wire](docs/CONTRACT.md)
and [failure evidence](tests/FAILURE-PROPAGATION-CONTRACT.md) contracts own the
existing meanings; this experiment explores their representation.

A maintenance budget bounds the design: on the order of 150 schema records is
acceptable to maintain if the schema moves slowly. A design that needs
substantially more records, or frequent schema changes to express ordinary
evidence, has failed the budget and must say so.

## 1. Specify the schema, the model and the questions that could defeat them

Before implementation, record the schema draft, model, unresolved choices,
controls and source baseline in `records/JSON-AS-PORCELAIN-EXPERIMENT.md`, owned
by this plan. Map each selected observation/check to its record, authoritative
owner, validation point and JSON projection, including encoder-only gates and
each custom coder's rule. Distinguish three layers:

1. **Received/observed evidence:** exact retained bytes, eligible native facts,
   partial records, unknown bounded codes, conflicts and association information.
   Captures retain origin, actual received/retained counts, completeness and
   admission state. Hashes or reserialization cannot replace original bytes.
2. **Admitted records/claims:** explicit supporting references and named admission
   boundaries. Contradictory observations remain representable even when no claim
   can be constructed. Structural validity does not establish native truth.
3. **Presentation:** JSON structure, presence conventions, ordering and byte
   encoding, projected without repairing evidence or classifying during rendering.

The schema is the owned input: record names, field names, stable field tags,
primitive kinds, optionality, list and map shapes, and a schema version. Decide
integer representation (one signed and one unsigned 64-bit kind, or the native
widths), bytes versus text for each hex and digest field, how the two raw-value
enumerations and the six string-keyed maps are expressed (ordered unique
key-record lists are the default), and how the entitlements property list stays
opaque. State the rule for unknown fields and unknown records on each side.
Avoid a universal `Unknown(JSONValue)` semantic escape hatch.

Freeze a few falsifiable claims: one authoritative owner per fact/payload; claim
construction requires supporting records; admitted slices need no generic JSON
tree; one schema definition produces producer, reader and independent tables that
agree without sharing code; export has explicit failure behavior;
rejected/conflicting evidence survives claim failure. Name a counterexample and
refuting observation for each. Structs, line counts and round trips alone cannot
establish these claims.

## 2. Codec proposal: resolve before implementation

The codec primitives are the small part of this work; the per-record mapping
and the controller's typed reading are the large part. Two candidates fit the
primitive menu. Present both in the experiment record, choose one before section
3, and record what would move the decision. Rejecting both and stopping is a
valid resolution.

**Option A: repository-owned primitives and generator.** A length-prefixed,
tagged encoding of the eight primitive kinds, hand-written once in Swift and
once in Rust. A Python generator under `docs/` or `tests/lib/`, registered under
[generator contracts](tests/suites/source_drift/README.md#generator-contracts),
reads the schema and emits the Swift writers, the Rust readers and typed
records, and the Python contract tables. Generated copies are committed and
drift-checked; nothing third-party enters the Meson source list.

**Option B: SwiftProtobuf with prost.** A `.proto` schema generates Swift and
Rust bindings; generated code is committed and drift-checked. The SwiftProtobuf
runtime is vendored into the Meson source list; prost joins `Cargo.lock`;
`protoc` and both plugins are generation-time tools. The Python consumer reads
the public JSON and needs no binding, but its independent tables must still be
derived from the schema.

| Requirement | Option A | Option B |
| --- | --- | --- |
| Distinct bytes and text, exact 64-bit signed and unsigned integers, explicit presence | Designed in | Supported; presence needs proto3 `optional` on scalars |
| Unknown fields and defaults | Rule owned here; absent means absent | Library rule: unknown fields preserved, scalar defaults implicit; admission must reject what the library accepts |
| Bounded lengths and nesting at the reader | Written into the reader | Message size limit configurable; nesting limit library-defined |
| Build dependencies | None | Vendored Swift runtime, one Rust crate, `protoc` and plugins at generation time |
| Provenance and worker identity | Regenerate once for the protocol change | Same, plus the vendored runtime's identity |
| Independent inspection of wire bytes | A short format note suffices | Public format; third-party tools available |
| Per-record mapping for about 90 to 150 records | Generator emits it | Generator emits it |
| Code the repository must review | Primitives, generator, generated copies | Generator configuration, generated copies, vendored runtime |

The recommendation is Option A, because Option B's dependency cost buys the
part of the problem that is already small and imports an unknown-field and
default policy the plan requires admission to own. Record the observation that
would reverse this: a hand-written primitive layer that grows past a small
bounded size, or a generator that begins to reimplement a general codec, moves
the decision to Option B. A trusted Swift dependency is acceptable in
principle; this proposal stands apart from the rest of the plan so it can be
rejected without disturbing the model or the slices.

## 3. Client framing, reception and output design

Specify client framing separately from the result encoding: magic/version,
record kinds, lengths, completion, duplicates, unknown tags, trailing data and
short reads. The relay carries client observations and opaque host bytes
without host-result interpretation. Decide which completed records establish
submission; an early header cannot establish a missing payload or terminal
event. Map unsupported version, malformed metadata, incomplete payload,
retention loss, no reply and timeout to distinct dispositions. Identify any
deliberate change to failure precedence or reading rules.

Design receiver deadlines and drain behavior explicitly: the present complete
collector has no independent receiver deadline, and [capture conversion](records/FOOTPRINT-OUTFLOW.md#direction-2-remove-one-redundant-capture-conversion-copy)
placed a reception cut outside its direction because it changes client
behavior. The prototype's default keeps complete collection with the retention
cap applied afterwards; a receiver deadline or drain is a recorded design with
its own contract, implemented only by a separate decision. Account for stderr
deadlock, overflow, allocation failure, interrupted I/O and producer/consumer
death in that design.

Begin with self-contained JSON stdout projected from admitted records. The
default projection keeps the present controller envelope shape so the existing
consumer, lifecycle oracle and blackbox controls run unchanged against the
prototype; schema reorganization of the public JSON is a disposition item, not
part of the demonstration. Choose determinism and late-error behavior: once
output is partial, a second error envelope cannot repair it. Whole XPC `Data`
followed by streamed output is not end-to-end streaming. An artifact bundle is
optional and needs its own portability, publication and cleanup decision.

Draw buffer lifetimes per changed process: owners, views, copies, handoffs and
earliest release. Source ownership does not establish Foundation/XPC physical
sharing; ownership controls apply to controller storage and to the host's own
records, not across XPC. [FOOTPRINT](docs/FOOTPRINT.md#response-storage-and-transport)
supplies measurement scopes, not fresh comparison evidence.

## 4. Implement the generator and two experimental slices

Use an isolated prototype worktree and a staged signed app. The prototype build
moves the runner protocol and response schema versions together through
[contract.json](docs/contract.json) and its readers, and regenerates worker
identity, so the build and drift checks admit it. Experimental binaries record
their own source and protocol identity.

Build the generator first and prove it on a small record set before widening.
Then carry real observations through model construction, encoding, relay, typed
admission, independent reading and JSON for:

- **Publication and order:** ordinary multi-phase execution and an actor visit;
  validator collection/closure, numbered release, acknowledgement and `query_first`
  support; an unavailable query and a later failure.
- **Ending and partial evidence:** exec or worker completion, termination request
  and native result, owned reap, and incomplete/conflicting evidence. Include only
  the custody/transfer records needed to challenge cross-actor references,
  without bearer token bytes; equipment inventory, entitlements and authority
  setup stay marked unconverted.

Generate and admit only the record families these slices exercise. Unconverted
families cross as opaque bytes with an explicit marker; a generic tree rebuilt
for coherence checks is a control, not success. Move selected semantic gates into
named model/admission functions before retiring their encoding-time
implementations. Preserve evidence-bearing degradation and an independent
minimal fallback.

## 5. Try to falsify the design

Use independently authored bytes/records and live runs. Adapt the
[consumer](tests/lib/consumer.py), [blackbox controls](tests/suites/blackbox_e2e/README.md),
[failure boundaries](tests/suites/failure_boundaries/README.md) and
[lifecycle oracle](tests/lib/lifecycle_oracle.py), retaining semantic checks
independent of production validation and generated bindings.

| Control | Required observation |
| --- | --- |
| Remove closure/acknowledgement, substitute actor/generation/phase, add a future ordinal or late validator record. | Unsupported claims are withheld; independent facts survive; a closed collection gains no late support. |
| Successful signalling with failed/unconfirmed reap; partial/conflicting execution. | Requested effects do not replace observed endings. |
| Integrity rejection; ordinary encoding failure; evidence-preserving encoding failure; minimal fallback/emission failure. | Preserved facts, original-summary diagnostics and withheld comparisons; total reporting failure leaves outer transport/process failure and surviving bytes, not a guaranteed self-report. |
| Unsupported version with plausible body; malformed/short/oversized frames; duplicates, unknown tags, trailing bytes, invalid text and combined faults. | No unearned submission or worker claim; announced lengths remain distinct from received bytes. |
| Arbitrary payload bytes, NUL, integer limits and wrong scalar kinds. | Exact retention and missing/false/zero/unknown/invalid distinctions survive. |
| Mutate the schema: drop a field, renumber a tag, change a kind, add an unknown record; regenerate one side only. | Producer, reader and independent tables disagree visibly; stale generated copies are refused by the drift check; no side silently accepts the other's change. |
| Export and independently inspect the same admitted model. | JSON formatting cannot change claim eligibility. |
| Release redundant temporaries, retain borrowed-view backing; challenge API lifetime restrictions and cleanup. | Demonstrated ownership/allocation boundaries, not equal lengths or use-after-free trials. |
| Interrupt frame/JSON emission at defined boundaries. | Failure status and partial bytes remain explicit; no complete artifact is claimed. |

Compare observation/provenance inventories, not whole-wire equality across
schemas or live runs. Stable authored fixtures may pin bytes; round trips and the
old implementation are comparators, not sole oracles. Compile-time controls apply
only to construction restrictions the model actually promises.

Register experimental cases and select coordinated checks through
[tests guidance](tests/AGENTS.md#choose-and-run-verification). Exercise the signed
slices with witness/lifecycle controls and `witness_contract/order_barrier_mutations`
when claiming migrated ordering equivalence. Full-family/default-battery
acceptance belongs to production adoption, beyond these slices.

## 6. Measure cost, maintenance and architectural benefit

Record representative small, query-dense, large-byte, actor and failure workloads
within the implemented slices, matched builds and instrument scopes. Adapt
footprint workloads rather than expanding migration to satisfy historical cases;
transport-only inputs establish no live execution coverage. Account for each
changed process and observer: resources, retained bytes/lifetimes, observable
copies/allocations, CPU and whole-request latency. Leave unavailable metrics
unestablished; whole-controller samples do not locate parser stages.

Account for maintenance against the budget: schema record count at the end of
the slices and projected for full coverage, primitive-layer size on each side,
generator size, generated lines per record, the procedure and cost of one schema
change, and which validators remain duplicated across Swift, Rust and Python.

Give every frozen structural claim an established, refuted or unestablished
disposition, supported by source review and independent counterexamples. Identify
new invariant owners, removed mutable duplicates, expressed failure states,
remaining generic representations, unchecked escapes and tooling burden. A
narrower cleanup cannot silently replace a failed model claim.

Performance superiority is not required. A demonstrated structural gain can
justify bounded costs, including slower execution. Explain resolved regressions
and tradeoffs; lost evidence, unbounded parsing, unresolved ownership or a
blown maintenance budget remains disqualifying. Quantitative improvement claims
require a frozen matched schedule, uncertainty and decision rule with retained
contrary trials; do not import the host-wait plan's performance gate as
architectural acceptance.

## Disposition, integration and retirement

After the slices and controls, choose one:

- **Pursue adoption:** supported structural claims, a resolved codec, acceptable
  costs and a maintenance account within budget; define remaining families,
  consumers and bounded migration work.
- **Retain a narrower result:** for example, the schema and generated typed
  admission in Rust over today's JSON transport. Name the supported boundary
  without claiming the larger hypothesis succeeded.
- **Revise a named assumption:** record one bounded alternative and its refuting
  control before continuing; the codec proposal's reversal condition is one
  such revision.
- **Close without adoption:** retain the concrete model, ownership, evidence,
  maintenance or cost finding that defeats the proposal.

Adoption may retire pre-1.0 encodings without compatibility layers, following
[contract evolution](docs/CONTRACT.md#when-a-number-moves) and generated-account
owners, and registers the schema generator under the generator contracts.
External-runner recovery remains independent of execution-version admission.
The coordinator owns applicability and disposition; follow repository build,
signing and evidence-retention guidance, with compiler concurrency capped at
two. This experiment adds no ARM, sleep/wake or competing-load trials.

At closeout preserve credited raw evidence, transfer lasting findings into the
outflow or accepted behavior account, and retire the experiment record and plan
when no experiment/adoption dependency remains.

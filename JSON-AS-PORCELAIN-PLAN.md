# JSON as porcelain: representation and ownership experiment

## Question and intended result

Can PolicyWitness carry evidence and the rules for making claims in explicit
records, variants, references and ownership rules, producing JSON at its public
boundary? Collections and byte buffers may remain variable-length; fixed models
do not mean maximum-sized arrays or language memory layouts.

Implement an experiment that tests this architecture. Structural clarity can
justify it without a speed or memory win: demonstrate identifiable integrity
boundaries, fewer redundant representations, or explicit ownership and lifetimes.
Replacing JSON syntax with a binary codec alone does not answer the question.

Schema and protocol changes are available. Key order, nesting, base64 placement
and duplicate representations are open choices. Preserve observations, provenance
and interpretation limits; identify proposed semantic revisions explicitly. A
version bump does not establish equivalence. Deliver a model, prototype,
independent controls, cost account and disposition. Production migration is a
bounded follow-on.

## Starting point

This broadens [capture conversion](records/FOOTPRINT-OUTFLOW.md#direction-2-remove-one-redundant-capture-conversion-copy)
into a representation experiment; borrowed-base64 optimization is no prerequisite.
The source boundaries to replace are the [Swift reply](runner/Sources/PWRunnerCore/PWRunnerReply.swift),
[opaque client relay](runner/Clients/PWRunnerClient/PWRunnerClientSession.swift),
[capture encoding](runner/Sources/PWRunnerCore/PWRunnerTransport.swift),
[Rust receiver](controller/src/runner_client.rs), [run assembly](controller/src/run_flow.rs),
[disposition](controller/src/disposition.rs)/[actor](controller/src/actor_evidence.rs)
readers and [JSON renderer](controller/src/json_contract.rs).

Two premises affect the redesign: Swift reply encoding enforces integrity checks
that decoding only partly repeats; [service degradation](runner/Sources/PWRunnerCore/PWRunnerService.swift)
must preserve conflicting observations while withholding comparisons. Inventory
both sets of checks and their degraded paths before replacing them.

## Boundary of the experiment

Prototype **host result -> XPC client -> controller -> public JSON** using a typed
result representation, opaque relay and typed admission or validated views.
Sandbox application, worker publications, validator queries, release and resource
ownership stay at their existing process boundaries. Specimen JSON, reservation
JSON and validator NDJSON may remain boundary adapters.

Host-wait/ARM work, evidence geometry and custody disposal remain separate.
Identify the accepted source baseline and refresh affected observations if it
changes. The [wire](docs/CONTRACT.md) and [failure evidence](tests/FAILURE-PROPAGATION-CONTRACT.md)
contracts own the existing meanings; this experiment explores their representation.

## 1. Specify the model and the questions that could defeat it

Before implementation, record the model, unresolved choices, controls and source
baseline in `records/JSON-AS-PORCELAIN-EXPERIMENT.md`, owned by this plan. Map each
selected observation/check to its record, authoritative owner, validation point
and JSON projection, including encoder-only gates. Distinguish three layers:

1. **Received/observed evidence:** exact retained bytes, eligible native facts,
   partial records, unknown bounded codes, conflicts and association information.
   Captures retain origin, actual received/retained counts, completeness and
   admission state. Hashes or reserialization cannot replace original bytes.
2. **Admitted records/claims:** explicit supporting references and named admission
   boundaries. Contradictory observations remain representable even when no claim
   can be constructed. Structural validity does not establish native truth.
3. **Presentation:** JSON structure, presence conventions, ordering and byte
   encoding, projected without repairing evidence or classifying during rendering.

Check integer width/sign, bytes versus text, absence versus false, associations
and duplicate ownership. Avoid a universal `Unknown(JSONValue)` semantic escape
hatch; uninterpretable bytes can remain opaque.

Freeze a few falsifiable claims: one authoritative owner per fact/payload; claim
construction requires supporting records; admitted slices need no generic JSON
tree; export has explicit failure behavior; rejected/conflicting evidence survives
claim failure. Name a counterexample and refuting observation for each. Structs,
line counts and round trips alone cannot establish these claims.

## 2. Choose a transport and output design for the prototype

Choose the model before the codec. Inspect suitable Swift/Rust support for bytes,
exact integers, presence/variants, bounded lengths/nesting, ambiguous encodings,
versions, unknown records, dependencies and independent inspection. Implement one
candidate; record a failed fit before trying another. Generated bindings may own
wire definitions, but independent controls must be able to reject producer errors.
Do not transmit language object memory. Borrowed views require checked bounds,
offsets/alignment and an immutable backing owner.

Specify client framing separately: magic/version, record kinds, lengths,
completion, duplicates, unknown tags, trailing data and short reads. Relay client
observations and opaque host bytes without host-result interpretation. Decide
which completed records establish submission; an early header cannot establish a
missing payload or terminal event. Map unsupported version, malformed metadata,
incomplete payload, retention loss, no reply and timeout to distinct dispositions.
Identify any deliberate change to failure precedence or reading rules.

Choose receiver deadlines and drain behavior explicitly: the present complete
collector has no independent receiver deadline. Bound retained storage and parser
work; drain/count excess without retaining it where exact counts are promised.
If reception stops, report actual drained bytes and leave unseen extent unknown.
Account for stderr deadlock, overflow, allocation failure, interrupted I/O and
producer/consumer death. Closing at a cap changes producer behavior and needs a
declared contract.

Begin with self-contained JSON stdout from the model, using direct serialization
or incremental byte encoding if suitable. Choose determinism and late-error
behavior: once output is partial, a second error envelope cannot repair it.
Whole XPC `Data` followed by streamed output is not end-to-end streaming. An
artifact bundle is optional; opening it requires a separate portability,
publication, partial/missing-artifact and cleanup decision. Keep JSON as an
explicit export; do not silently introduce sidecars.

Draw buffer lifetimes per changed process: owners, views, copies, handoffs and
earliest release. Source ownership does not establish Foundation/XPC physical
sharing; [FOOTPRINT](docs/FOOTPRINT.md#response-storage-and-transport) supplies
measurement scopes, not fresh comparison evidence.

## 3. Implement two complete experimental slices

Use an isolated prototype checkout/build and a staged signed app. Carry real
observations through model construction, encoding, relay, typed admission,
independent reading and JSON for:

- **Publication and order:** ordinary multi-phase execution and an actor visit;
  validator collection/closure, numbered release, acknowledgement and `query_first`
  support; an unavailable query and a later failure.
- **Ending and partial evidence:** exec or worker completion, termination request
  and native result, owned reap, and incomplete/conflicting evidence. Include
  custody/transfer observations sufficient to challenge cross-actor references,
  without bearer token bytes.

Move selected semantic gates into named model/admission functions before retiring
their encoding-time implementations. Preserve evidence-bearing degradation and
an independent minimal fallback. Wrapping old JSON in a codec or rebuilding the
old tree for every coherence check is a control, not success. Mark unconverted
families and adapters; the prototype need not migrate every operation.

## 4. Try to falsify the design

Use independently authored bytes/records and live runs. Adapt the
[consumer](tests/lib/consumer.py), [blackbox controls](tests/suites/blackbox_e2e/README.md),
[failure boundaries](tests/suites/failure_boundaries/README.md) and
[lifecycle oracle](tests/lib/lifecycle_oracle.py), retaining semantic checks
independent of production validation and generated bindings.

| Control | Required observation |
| --- | --- |
| Remove closure/acknowledgement, substitute actor/generation/phase, add a future ordinal or late validator record. | Unsupported claims are withheld; independent facts survive; a closed collection gains no late support. |
| Successful signalling with failed/unconfirmed reap; partial/conflicting execution. | Requested effects do not replace observed endings. |
| Integrity rejection; ordinary encoding failure; evidence-preserving encoding failure; minimal fallback/emission failure. | Check preserved facts, original-summary diagnostics and withheld comparisons. Independent fallback may report loss; total reporting failure leaves outer transport/process failure and surviving bytes, not a guaranteed self-report. |
| Unsupported version with plausible body; malformed/short/oversized frames; duplicates, unknown tags, trailing bytes, invalid text and combined faults. | No unearned submission or worker claim; announced lengths remain distinct from received bytes. |
| Arbitrary payload bytes, NUL, integer limits and wrong scalar kinds. | Exact retention and missing/false/zero/unknown/invalid distinctions survive. |
| Export and independently inspect the same admitted model. | JSON formatting cannot change claim eligibility. |
| Release redundant temporaries, retain borrowed-view backing; challenge API lifetime restrictions and cleanup. | Demonstrated backing identity/allocation boundaries, correct lifetimes, failure cleanup and idempotence. |
| Interrupt frame/JSON emission at defined boundaries. | Failure status and partial bytes remain explicit; no complete artifact is claimed. |

Compare observation/provenance inventories, not whole-wire equality across schemas
or live runs. Stable authored fixtures may pin bytes; round trips and the old
implementation are comparators, not sole oracles. Compile-time controls apply
only to construction restrictions the model actually promises.

Register experimental cases and select coordinated checks through
[tests guidance](tests/AGENTS.md#choose-and-run-verification). Exercise the signed
slices with witness/lifecycle controls and `witness_contract/order_barrier_mutations`
when claiming migrated ordering equivalence. Full-family/default-battery
acceptance belongs to production adoption, beyond these slices.

## 5. Measure cost and judge architectural benefit

Record representative small, query-dense, large-byte, actor and failure workloads
within the implemented slices, matched builds and instrument scopes. Adapt
footprint workloads rather than expanding migration to satisfy historical cases;
transport-only inputs establish no live execution coverage. Account for each
changed process and observer: resources, retained bytes/lifetimes, observable
copies/allocations, CPU and whole-request latency. Leave unavailable metrics
unestablished; whole-controller samples do not locate parser stages.

Give every frozen structural claim an established, refuted or unestablished
disposition, supported by source review and independent counterexamples. Identify
new invariant owners, removed mutable duplicates, expressed failure states,
remaining generic representations, unchecked escapes and tooling/validator burden.
A narrower cleanup cannot silently replace a failed model claim.

Performance superiority is not required. A demonstrated structural gain can
justify bounded costs, including slower execution. Investigate unexplained costs
before adoption and record accepted tradeoffs; lost evidence, unbounded parsing
or unresolved ownership remains disqualifying. Quantitative improvement claims
require a frozen matched schedule, uncertainty and decision rule, arranged quiet
conditions and retained contrary trials. The host-wait plan's performance gate
is not architectural acceptance.

## Disposition, integration and retirement

After the slices and controls, choose one:

- **Pursue adoption:** supported structural claims and acceptable costs; define
  remaining families/consumers and bounded migration work.
- **Retain a narrower result:** name its supported boundary without claiming the
  larger hypothesis succeeded.
- **Revise a named assumption:** record one bounded alternative and its refuting
  control before continuing.
- **Close without adoption:** retain the concrete model, ownership, evidence or
  cost finding that defeats the proposal.

Adoption may retire pre-1.0 encodings without compatibility layers, following
[contract evolution](docs/CONTRACT.md#when-a-number-moves) and generated-account
owners. External-runner recovery remains independent of execution-version
admission. The coordinator owns applicability and disposition; follow repository
build, signing and evidence-retention guidance, with compiler concurrency capped
at two. This experiment adds no ARM, sleep/wake or competing-load trials.

At closeout preserve credited raw evidence, transfer lasting findings into the
outflow or accepted behavior account, and retire the experiment record and plan
when no experiment/adoption dependency remains.

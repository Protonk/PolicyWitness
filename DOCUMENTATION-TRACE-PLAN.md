# Request, response and public-commitment tracing

Status: draft for implementation. No documentation relocation, tree change or
generator change has been made. The preparation and execution notes at the end
distinguish inspection from completed implementation and verification.

## Purpose, readers and authority to proceed

Reorganize the developer documentation around three questions:

1. What request can I supply, and what obligations accompany it?
2. What does the returned evidence establish, including refusals and incomplete
   execution?
3. When implementation, tests or generated interfaces change, which public
   commitments deserve examination, and where are they stated?

`docs/REQUEST.md` will own the first reading path, `docs/RESPONSE.md` the second,
and `docs/CONTRACT.md` the third. ARCHITECTURE carries the complete statements of
a short named list of cross-process protocols. CONTROLLER, WORKER and BUILD keep
their authored accounts and gain generated lists of the commitments that govern
each section. Public meanings remain authored in the contract surface tree;
their rendered location does not determine whether they are public.

**Readers.** These are documents for developers: people changing the
implementation, its tests or its generated interfaces, and people building a
harness against the instrument with its source at hand. REQUEST and RESPONSE
teach, and they teach that reader. They may cite source, checks, fixtures and
component names, and they need not stand alone for someone holding only the
shipped app. The [user guide](docs/PolicyWitness.md) remains the user document
and is [frozen](#the-user-guide-is-frozen) for the duration of this work.

This is a change to how the repository exposes and traces the instrument, not
just a division of a large document. A good result lets a reviewer follow a
consequential operation through its declarations, implementation, observations,
interpretation and public promises without mistaking any one of those for the
others. Passing generators establishes necessary preservation properties. It
does not establish that the new accounts are useful.

**Timing.** This work lands before the `v0.3.8` tag. At the reviewed state all
19 surfaces display `unreleased`, so a change to a public payload alters no
stamp row. Breaking changes to the public representation are authorized, and
expected wherever the reorganization exposes their need: retiring a fact,
splitting, merging or renaming a subject, rewording a title or stamped prose,
changing an anchor, renaming a document. Commit these as deliberate, coherent
conceptual changes, with their payload differences accounted for under
[change classes](#change-classes). Do not preserve a structure only because it
is the current one.

Execute the whole plan without scheduled approval stops. Settle ordinary
editorial and implementation choices locally, record the consequential choices
named under [who decides](#who-decides), and continue. Review checkpoints below
are work for the executor, not requests for the maintainer to supervise each
stage.

The authorized scope includes renaming and writing documents, adapting rendering
and navigation, restructuring the authored tree, correcting a public statement
that misdescribes behavior the source establishes, extending existing controls,
correcting ownership guidance to describe the resulting arrangement, and
updating source comments and other source text that cite the relocated
documentation. That last item edits build inputs: the build identity and the
host/worker identity change during this work, and that is expected.

It does not include changing runtime behavior, changing a JSON shape, rewriting
the help system, editing the user guide, or silently revising a public promise.
Establish from source what the instrument does and correct the statement to
match; that is authoring. Where the correction would instead commit the
instrument to something it does not do today, or withdraw something callers can
rely on, isolate it: state the distinction, why it matters and the commitment
that would change, keep the present meaning, and complete the rest of the work.
Seek a decision only if such an unresolved meaning prevents a coherent result.

Useful rough edges are acceptable: a long reference section, useful repetition,
an explicitly incomplete trace, or a mechanism described in prose. Lost
conditions, conflicting owners, fabricated evidence and misleading claims of
completeness are not acceptable rough edges.

## The user guide is frozen

[docs/PolicyWitness.md](docs/PolicyWitness.md) does not change during this work:
its bytes at completion equal its bytes at the reconciled starting commit. Its
rewrite is an outflow of this plan, not part of it.

Consequences the executor must hold:

- The guide's "Public contract surfaces" section says the release's developer
  contract "defines the fields, applicability and obligations behind these
  surfaces" and links CONTRACT at the release tag. After this work that
  sentence understates where the definitions are. Leave it. Record it in the
  outflow.
- The guide's "Specimen format" and "Output envelope" sections stay the user
  account. Nothing moves between them and REQUEST or RESPONSE in either
  direction. REQUEST and RESPONSE may link to a guide section as the user
  workflow; they must not depend on the guide for a definition. Where the guide
  and the tree disagree, the tree and source govern the developer documents,
  and the disagreement goes in the outflow.
- The guide carries a stamp table and regions copied by
  [generate_limits.py](docs/generate_limits.py). The contract generator must
  reproduce the stamp table byte for byte, so the surface set, surface IDs and
  `artifact` descriptions do not change here. Do not edit the shared regions of
  LIMITS, QUESTIONS, EXTENSIONS or the failure-propagation contract that are
  copied into the guide. A change this work would otherwise make to any of
  those is deferred to the outflow, with its reason.
- Standalone staging must still pass. The guide's executable workflow is
  unchanged, so `witness_contract/guide_workflows` is not rerun to relabel
  existing evidence.

Write the outflow as `records/GUIDE-REWRITE-OUTFLOW.md`, linked from this plan
only, following [records guidance](records/AGENTS.md). It lists what the guide
rewrite should take from this work: stale statements, disagreements found, the
deferred changes above, and which developer statements a user account would
need restated without source citations. It is a record of dispositions, not a
plan for the rewrite.

## Starting evidence and reconciliation

The reviewed state is
[`6fcd2b5f1c84094405e2ce4de035b538a411b7cc`](https://github.com/Protonk/PolicyWitness/commit/6fcd2b5f1c84094405e2ce4de035b538a411b7cc).
At preparation on 2026-11-15, local HEAD was exactly that commit and the working
tree was clean. Commits that add or revise this plan are not implementation
changes.

Before implementation, compare the then-current checkout with that baseline.
Read subsequent changes affecting the owners below, preserve unrelated work,
and record any adjustment to this plan's assumptions. Do not reset the checkout
to the reviewed commit. Obtain the actual starting public snapshot, shape
goldens, stamp tables, guide bytes and relevant interface artifacts from the
reconciled checkout; use the reviewed commit to explain differences, not to
erase them.

Follow [planning and documentation guidance](CONTRIBUTING.md),
[documentation rules](docs/AGENTS.md),
[surface authoring rules](docs/contract/AGENTS.md), and
[test guidance](tests/AGENTS.md). Read the controller or runner working rules
when investigating their respective boundaries. Supporting investigation and
acceptance records may live in `records/documentation-trace/`, linked from this
plan only. Permanent documents must stand without those temporary records.

### Grounding already established

- [REQUEST-GRAMMAR](docs/REQUEST-GRAMMAR.md) is an authored teaching sequence,
  including independent file effects, refusal expectations, phases, actors and
  controller/direct-XPC differences. It already describes itself as a developer
  guide. It is not the complete request definition.
- [CONTRACT](docs/CONTRACT.md) is currently one generated document. The
  [surface tree](docs/contract/README.md) has 19 surfaces, 182 subjects (180
  directly under a surface), 1,004 fields, 129 rules and 151 support owners at
  the reviewed state. Those counts describe the baseline, not targets. The work
  must account for the full tree, not only the input and output fields most
  visible in examples.
- [tree.py](docs/contract/tree.py) routes rendering by the `part` fact:
  `render` groups surfaces, and any descendant carrying its own `part`, under
  the eight `PARTS`. Thirteen sub-surface subjects carry such an override.
  Eleven of them, under `policy` and `extensions`, say `report` inside an
  `input` surface; the other two are `identity.definitions` and
  `identity.version`. `_node_public` includes `part`, titles, prose, context and
  relationship facts in canonical public content.
- Of the 129 rules, 115 name one acting component and 14 name several. Eight of
  the 14 are in four subjects that hold no record: `extensions.custody` (4),
  `transport.delivery` (2), `wire.frame` (1) and `wire.validator` (1). The other
  six sit beside declarations, records or single-component rules:
  `policy.spec.parameters`, `policy.imports.holds`, `actors.actor.fresh`,
  `steps.assessment.fresh_read_aggregate`, `.fresh_write_aggregate` and
  `installation.commands.verify`. Single-component rules are mostly the host's
  (49) and the controller's (50); the host has no tour of its own.
- [runtime.py](docs/contract/runtime.py) uses one `OUTPUTS` tuple for CONTRACT
  and the guide, including assumptions that both contain stamp tables.
  `assemble`, `_claimed_history`, `render` and the history-free branch of
  `check` depend on that arrangement. The
  [entry point](docs/generate_contract_stamps.py) protects only CONTRACT from
  preview overwrite. Several fixture helpers assume positional outputs.
- The `v0.3.7` tag carries a [public snapshot](docs/contract/public.json), read
  by [history_v1.py](docs/contract/history_v1.py) without reparsing authoring
  syntax. Fourteen annotated release tags are reachable. A current-tree change
  to facts or structure does not alter how released snapshots are read.
- [CONTROLLER](docs/CONTROLLER.md) already explains request holding,
  publication, invocation uncertainty, admission, result selection and runner
  cleanup, and has no generated region. [WORKER](docs/WORKER.md) follows
  acquisitions, authority and publication; its capability inventory is
  architecture-generated. [ARCHITECTURE](docs/ARCHITECTURE.md) and WORKER
  receive regions from [architecture.json](docs/architecture.json) through
  [generate_architecture.py](docs/generate_architecture.py).
  [BUILD](docs/BUILD.md) combines authored explanation with regions and spans
  owned by [build.json](docs/build.json) and
  [generate_build.py](docs/generate_build.py). None is a blank destination.
- [generate_limits.py](docs/generate_limits.py) renders scalar spans in its
  `SPAN_DOCUMENTS`, which name REQUEST-GRAMMAR and ARCHITECTURE, and in the
  surface sources. The surfaces carry 78 limit spans; CONTRACT is not a span
  document and carries them through in rendered statements. The generator also
  owns shared content copied into the standalone guide.
- [build_contract.py](docs/build_contract.py) selects build-identity inputs by
  directory and suffix; rendered documentation, the generators other than
  itself, and the JSON and Markdown under `controller/interface/` are not among
  them. [generate_worker_identity.py](docs/generate_worker_identity.py) hashes
  the C, header and Swift sources under `controller/tools/pw_probe_runner` and
  `runner/Sources`, with `build.sh` and the Meson files, into three generated
  copies. `build.sh` already runs every documentation generator's `--check` by
  entry point.
- Two source comments cite `docs/CONTRACT.md`: on the request record in
  [PWRunnerRequest.swift](runner/Sources/PWRunnerCore/PWRunnerRequest.swift)
  and beside the bootstrap identity in
  [pw_probe_runner_abi.h](controller/tools/pw_probe_runner/pw_probe_runner_abi.h).
  Each is both a build-identity input and a host/worker identity input. No
  build input names REQUEST-GRAMMAR. Five source comments cite the user guide
  and several cite the failure-propagation contract, LIMITS, BUILD and
  `runner/README.md`. That search matched document paths; it did not look for
  comments that describe the contract's layout in words.
- The [interface inventory](controller/interface/README.md) already connects
  definitions, cards, corpus cases and recorded mutations. Six contract nodes
  currently cite `interface` identifiers. The
  [join](docs/contract/interface_join.py) checks selected structured facts;
  it explicitly leaves prose, free conditions and the admission-class binding
  outside that comparison. It supplies useful partial traces, not a general
  change-impact classifier.

## Ownership and placement

Separate three kinds of ownership throughout the change: the source defining a
public meaning, the document presenting its complete statement, and the source
or observation supporting it. The surface tree remains the first; routing
changes the second; support owners and existing independent checks retain the
third.

### The placement rule

1. **Route whole subjects.** The routing unit is a subject directly under a
   surface. Its fields, rules, definitions, examples, gaps, owners and nested
   subjects travel with it. No presentation split below that unit.
2. **Direction decides the home.** What a caller declares, and the rules that
   admit or prepare it, go to REQUEST. Records a command returns, and the rules
   that produce, select or assess them, go to RESPONSE. The reviewed tree's
   `part` facts already encode this direction and seed the map.
3. **ARCHITECTURE holds a named list of protocols.** A subject that holds no
   caller-visible record and states an exchange between processes is rendered
   whole in ARCHITECTURE. The list is below; it is not derived from a fact.
4. **CONTRACT holds what tracing needs.** Identity derivation, surface history,
   shared definitions, notation, support grades and details, derived views and
   the trace indexes.
5. **Other tours hold links.** CONTROLLER, WORKER and BUILD receive no complete
   statements. Each section that explains a mechanism behind a commitment gets
   a generated list of those commitments, linked to their statements.

| Surface | Home | Subjects routed elsewhere |
| --- | --- | --- |
| `identity` | CONTRACT | `identity.build`, `.producer`, `.version` → RESPONSE |
| `request` | REQUEST | none |
| `policy` | REQUEST | `policy.check_data`, `.compile`, `.imports`, `.fallback`, `.actor_check` → RESPONSE |
| `probes` | REQUEST | none |
| `actors` | REQUEST | none |
| `extensions` | REQUEST | `extensions.event`, `.transfer`, `.resources`, `.token`, `.delivery`, `.handle` → RESPONSE; `extensions.custody` → ARCHITECTURE |
| `refusals` | RESPONSE | none |
| `transport` | RESPONSE | `transport.authorization`, `.delivery`, `.reservation`, `.control` → ARCHITECTURE |
| `wire` | ARCHITECTURE | `wire.standalone`, `.standalone_status`, `.standalone_result`, `.standalone_error` → RESPONSE |
| `reply`, `steps`, `lifecycle`, `actor_evidence`, `equipment`, `profile` | RESPONSE | none |
| `envelope`, `diagnostics`, `dossier` | RESPONSE | none |
| `installation` | RESPONSE | none |

A surface's introduction and its surface-level owners render at the surface's
home. `transport` and `wire` are divided between documents and each has a
surface-level owner; that owner keeps its original scope and the descendants
rendered elsewhere link to it.

ARCHITECTURE therefore receives seven subjects: caller authorization,
reservation and once-only execution with their two control records, the frame
grammar, the validator line protocol, and extension custody. The six
multi-component rules that sit inside other subjects stay with those subjects.

Entries other than `run` are kept together as labeled sections, not interleaved
with the run account. In RESPONSE: version output (`identity.version`), the
compiler helper (`envelope.helper` with the helper's data records), the direct
validator (the four `wire.standalone*` subjects, kept as one interface), and
runner administration (the whole `installation` surface, including its command
obligations). In REQUEST: the compiler-helper request forms
(`policy.helper_request`, `policy.helper_policy`). Runner administration is the
largest of these and answers neither run question. If it crowds RESPONSE's
reading path, move the whole labeled section to its own document; do not divide
it.

Applied to the reviewed tree's 180 routing units, the table sends 149 to
RESPONSE, 20 to REQUEST, 7 to ARCHITECTURE and 4 to CONTRACT. RESPONSE is most
of the present contract by volume, so its authored path carries the navigation:
the envelope-first account must lead to each evidence family, and the families
must not read as one undivided reference.

Step 1 turns this table into the complete map: every routing unit, its
destination, its order there, and its inbound links. Derive the list from the
tree; do not catalogue a thousand field definitions by hand. No subject is
routed silently by a catch-all.

### When a subject wants two homes

A subject that cannot be read well in one document is evidence about the tree,
not a reason to divide its presentation. Split it in the authored tree as a
deliberate [public change](#change-classes): new subject IDs, each with the
context, bindings and prerequisites its rules had, owners re-scoped without
broadening, references and inbound links updated. Then route the resulting
subjects whole.

The first candidates are the fresh-process, collect/release/advance and
termination-gate rules: `actors.actor.fresh`, `actors.phase.order`,
`actors.after_termination.gate` and `actor_evidence.gate.evaluate`. They state
the ordering protocol and sit inside declaration and evidence records. By
default they stay with those records, and ARCHITECTURE's existing ordering
account links to them. Promote them, by extracting a protocol subject routed to
ARCHITECTURE, only if the [promotion test](#execution-sequence-and-resumption)
shows the promise cannot be read whole from that account and its links.

### Who decides

Accepting this plan is the maintainer decision that
[CONTRIBUTING](CONTRIBUTING.md) requires for a change of ownership: it fixes the
rule, the table and the ARCHITECTURE list.

Moving a whole subject between documents is a one-line map edit that leaves
every public payload unchanged. The executor decides those, and the map file is
the reviewable record. A move that departs from the table needs a sentence of
reason in the execution record.

For the following choices, use one coherent conceptual change per commit and
list its cause and affected surfaces in the execution record. Related title or
prose edits may share a commit; individual sentences do not need separate
commits. Keep placement, `part` retirement and public changes separate:

- a tree split, merge or rename, which changes identities and anchors;
- retirement of a fact, or rewording of a title or stamped prose;
- replacement or deletion of authored tour prose;
- promotion of a subject to ARCHITECTURE beyond the seven named.

## Reading paths to produce

### REQUEST

Rename REQUEST-GRAMMAR, preserving its useful progression from an observable
create, through one-change refusals, to phases, actors and entry-point
differences. Integrate reference material into that progression or into clearly
linked reference sections; do not put the routed definitions ahead of the
teaching sequence.

The introduction should distinguish caller declaration, controller resolution,
host admission and contingent execution. Explain how to obtain the current
build identity without equating an identity match with valid input. Keep
omission/null distinctions, defaults, capacity-before-meaning ordering,
branch-local refusal precedence, shadowed-selector validation and actor-specific
restrictions explicit. Identify `_test_overrides` as test controls, including
the limits of an echoed override. Where a declaration is governed by a protocol
stated in ARCHITECTURE, say what the declaration asks for and link the
statement.

Give the three executable publications distinct roles:

| Command | What this account may promise |
| --- | --- |
| `help` | Selected facts derived from executable interface definitions. Its omissions and unenumerated tails remain visible in the interface account. |
| `example` | Complete build-bound publication plus that build's admission promise. Publication itself does not invoke the host or establish any attempt's success. |
| `test-input` | Build-bound controlled input with positional target binding. The caller/harness arranges target conditions and independent expectations; this publisher carries no general host-admission promise. |

Neither publication command supplies an answer key. Preserve the broader
[request corpus](tests/fixtures/request_contract/examples.json), its independently
authored controller/direct-XPC expectations, and its independent effect checks.
Keep failed-publication guards: complete-looking stdout on publication failure
is not a usable specimen. Link restrictions to the relevant RESPONSE records
without duplicating their complete meanings.

### RESPONSE

Start with an actual envelope shape and process exit, then `result`, then the
run payload and its producers. Lead readers through these distinctions before
the field reference:

- Publication, request admission, execution and evidence collection are separate
  events. Publisher exit statuses and the `run` envelope have different roles.
- A finished experiment can include failed attempts. The current outer result
  mapping can also coexist with controller integrity findings.
- Controller process observations differ from records carried from the client,
  host, worker or validator; carried records differ from controller assessments.
- Missing keys, explicit null, withheld assessments, absent publication and
  incomplete collection do not all mean the same thing.
- An admitted `not_invoked` capture supports a narrower statement than a missing
  capture. Invocation does not prove host receipt or admission. Effects can
  outlive a lost reply; fallback compilation is not worker progress.
- A permission-shaped failure does not establish sandbox cause. `query_first`
  establishes its bounded ordering claim, not prediction/enforcement agreement.

Use a compact reading exercise from the
[example round trip](tests/suites/witness_contract/README.md#the-apps-own-example)
and a controlled-read exercise from the
[test-input work](tests/suites/witness_contract/README.md#controlled-read-input).
Identify the exact input, applicable conditions, observed records, independent
samples and justified conclusion. Prefer extracting existing maintained examples
or presenting explicitly abbreviated excerpts. Never label the
[constructed actor fixture](tests/fixtures/example_round_trip/README.md) as a
captured run. Keep full records accessible through their owners rather than
inventing a polished synthetic success transcript.

Explain build and producer fields at their point of use, linking identity
derivation in CONTRACT. Give refusals, transport records, receipts, equipment,
extensions, lifecycle and dossier an accessible route from the envelope. Keep
the labeled sections for other entries after the run account. Authored
explanation in REQUEST and RESPONSE is allowed; the help-card restriction on
authored text does not apply here.

### ARCHITECTURE and the other tours

Read each ARCHITECTURE section against the protocol subjects it receives before
editing. Replace or consolidate overlap; avoid an unchanged tour followed by a
second full account. A received protocol needs one identifiable complete
statement with its applicable operation, conditions, consequences and
qualifications, and must remain readable as a whole: once-only invocation under
the original allowance, and extension custody from preparation to erasure.

CONTROLLER, WORKER and BUILD keep their organizing subjects: controller
decisions, worker resources and authority, and the build's identity, signing
and provenance responsibilities. Their authored prose changes only where a link
moves or where it contradicts the statement it explains. Each section that
explains the mechanism behind a commitment gets a commitment list.

A commitment list is a small generated region naming subjects or rules and
linking each to its complete statement. The map declares, per tour section,
which node IDs it lists; the executor authors that association by reading the
section against the statements. A list asserts that the section explains those
commitments. It is not a coverage claim, and a section without one makes no
statement about commitments.

A source mechanism is not automatically a promise; a technically detailed
restriction can still be something a caller relies on.

### CONTRACT as a tracing aid

Open with how to investigate a change and how to distinguish four outcomes:
implementation changed while the promise held; supporting evidence changed;
a promise needs deliberate revision; or implementation and promise disagree
and need investigation. Do not compute those judgments from hashes or links.

Provide both entry directions:

- **From a changed item:** an inspectable index grouped by governing declaration,
  source path/symbol, generator/interface artifact, or supporting check, leading
  to candidate commitments and their complete statements. Distinguish a
  declaration owner from a source citation used as evidence. A cited source's
  presence is not proof that every change to that file affects the promise.
- **From a commitment:** its stable surface/subject/rule identity, the document
  holding its statement, applicability and consequence, imported
  fields/declarations, relevant interface projections, and graded support with
  actual assertion scope and known gaps.

The commitment index lists every routing unit with its home. It is how a reader
holding an identity finds the statement; no redirect stub or duplicated anchor
is kept for that purpose.

Reuse tree relationships, record imports, `interface` facts, the inventory,
case joins and mutation records. Generate indexes from those owners where the
relationship exists. Add narrow presentation/support metadata only when it
feeds a useful view or check. Do not infer behavioral reach from staged input
files, infer authority from filenames, or make every promise connect to help,
example and test-input. An absent connection must remain an absent connection.

Begin with subject-level navigation and focused rule-level traces; a giant
field-by-every-source matrix would bury the review. Identity derivation, shared
definitions, notation, surface history, support grades and support details stay
here. Keep inherited conditions and `free.*` qualifications visible at the
statement; support detail links are not a substitute. Retain the applicability,
controller-finding and known-gap views, making their targets destination-aware.

The result is a maintained review aid, not a comprehensive impact-analysis
engine. No new all-purpose dependency language, automatic semantic verdict,
universal coverage score or mandatory connection to every command is required.

## Rendering design and preservation boundaries

Use a presentation map outside canonical public meaning. The default design is
an explicit file under `docs/contract/` mapping routing units to documents,
regions and order, and tour sections to commitment lists, consumed by the
existing contract generator. A separate module is equally reasonable if it is
easier to review. The map is not read by `_node_public` and does not enter any
payload.

### Change classes

Every commit that touches the tree or its rendering belongs to one class, and
each class has its own proof.

| Class | What changes | What must be shown |
| --- | --- | --- |
| Placement | The map, the renderer, links, authored prose around regions | Per-surface canonical payloads, `public.json`, shape goldens, free-text counts and stamp contents are identical before and after. |
| `part` retirement | The `part` fact leaves the tree and its reader | Each payload differs from its predecessor by exactly the removed `part` facts: delete `part` from the earlier payloads and the two are identical. Nothing else moves. |
| Public change | A tree split, merge or rename; a title or stamped-prose rewording; a corrected statement | The payload difference is confined to named nodes. For a restructure, each moved rule's effective context, bindings, quantified scope, prerequisites and case order equal what they were; each owner supports the same subjects with the same scope. The commit names its cause and the surfaces affected. |

Shape goldens, the interface inventory, card bytes and joins are unchanged in
every class unless an explicitly identified owner changed. Compare actual
payloads, not the displayed stamp: every row displays `unreleased` throughout.
Never normalize away a real difference or accept refreshed goldens to make a
check pass.

### Retire `part`

Once the map routes every unit and no renderer path reads `part`, remove it:
the surface and subject fact tables, `PARTS`, `PART_TITLES`, its validation and
its use in `render`, the thirteen overrides and nineteen surface facts, and its
description in the [surface tree reference](docs/contract/README.md). Search
the controls and fixtures for constructed `part` facts. Released snapshots keep
theirs; the release readers do not interpret them. Do not leave `part` in the
tree as a stamped fact that controls nothing.

### Seams the implementation must address

1. **Coverage and inherited scope.** Every public node has exactly one rendered
   home, reached through its routing unit. Surface introductions and
   surface-level owners render at the surface's home and still support the
   descendants rendered elsewhere with their original scope. Keep first-match
   cases together and ordered.
2. **Destination-aware links.** Replace `_link`'s single-document assumption;
   cover field-type links, expressions/references, support paragraphs/details,
   derived views, commitment lists, examples and authored prose links. Keep the
   explicit `contract-*` anchor at each complete statement. Rebase links while
   rendering instead of editing stamped prose to change a URL. Use the
   repository Markdown reader where it can distinguish links from code and
   examples.
3. **Position-dependent wording.** Stamped prose refers to its surroundings by
   position; about nine passages say "below" at the reviewed state, for example
   in `probes`, `reply`, `envelope` and `diagnostics`. Payload checks cannot see
   whether the referent still follows. List these in step 1. After routing and
   after any restructure, confirm each referent renders later in the same
   document, and reword the ones that fail as a public change.
4. **Existing callers.** Update current repository inbound links and their
   descriptions to the statement's new home. Leave intentional
   historical-release links and the frozen guide unchanged. Keep no second
   REQUEST-GRAMMAR account and no forwarding entries. Citations in source are
   callers too; they are updated together as described under
   [source citations](#source-citations-and-the-build-identity).
5. **Output versus history inventory.** Separate rendered document/region
   ownership from stamp-table locations. Stamp tables remain in CONTRACT and
   the guide; no other document gains one. Change runtime assembly,
   claimed-history discovery and both checking paths accordingly. Keep v0/v1
   release readers and released snapshots readable.
6. **Partial document ownership.** REQUEST, RESPONSE and ARCHITECTURE hold
   statement regions beside authored prose; all four tours hold commitment-list
   regions. Declare each region explicitly and preserve the surrounding prose.
   Adapt the entry point, `input_paths`, generator ownership declarations,
   [fixture_inputs](tests/lib/fixture_inputs.py),
   [contract_fixture](tests/lib/contract_fixture.py), and disposable fixtures.
   Remove positional `OUTPUTS[0]`/`OUTPUTS[1]` assumptions where their meaning
   would become ambiguous. Preview must protect every owned output, not only
   CONTRACT, and must validate all selected destinations before writing.
7. **Interacting generators.** Update limits' renamed span document,
   architecture document/edge records, and receiving generator inputs. Keep
   regions disjoint. Statement regions carry limit spans into REQUEST and
   ARCHITECTURE, which the limits generator scans as span documents. Use the
   existing `BEGIN GENERATED ...` / `END GENERATED ...` region convention:
   `authoring_excluded_ranges` and `authored_spans` in
   [generator_common.py](docs/generator_common.py) already exclude those regions
   from scalar rendering. Limits owns the authored surface spans; the contract
   generator owns their rendered copies. Reuse that exclusion and add a focused
   control showing that limits leaves contract-region spans untouched while
   updating authored spans outside them. A separate exclusion mechanism is not
   needed for regions following the existing convention.
   Ensure a complete regeneration reaches a fixed point: a later generator must
   not silently stale an earlier output. Keep copied guide sections unchanged.

### Source citations and the build identity

Source that cites the relocated documentation is updated in this work. Expect
more than the two comments already found: sweep Rust, Swift, C, shell, Python
and fixture text for document paths, `contract-*` anchors, node IDs, `part`
names, and phrases that describe where a rule is stated, such as "the request
contract" or "the wire contract". Read each citation and point it at the
document that holds the statement it relies on. The request record's comment
belongs with REQUEST. The header's comment needs its referent established
first: find which statements cover the bootstrap magic and identity bytes it
describes, and cite their home. Where a comment relies on a statement the tree
does not contain, say so in the execution record; do not leave a general
pointer to CONTRACT in its place.

Leave citations of the user guide as they are; the guide is frozen and their
targets do not move. Leave retained mutation records as historical
observations, including recorded generator refusal text that names the present
outputs, unless the
[interface verification](tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards)
guidance has a check compare them with current output. A citation inside
generated source is changed at its generator input.

These edits change comments and citations, not behavior. If the sweep finds
relocated documentation named in text the app prints, that is an interface
output: treat it under the interface verification guidance, not as a comment.

Make the edits to build inputs together, in one commit, after homes and anchors
have stopped moving (step 8). Documentation, map and generator commits before
it select no build input, so `development:<sha256>` and the worker identity
should hold until then; if either changes earlier, trace the selected file that
caused it. Doing the source edits once means one worker-identity regeneration,
one signed build and one body of live evidence against the final source. A
later build-input edit is allowed, and repeats that verification.

Keep build identity separate from surface identity throughout. A source comment
changes the build identity and no public payload; a tree change does the
reverse.

## Execution sequence and resumption

Use coherent local commits, one change class each. Update the short execution
record at the end of this plan with the last completed step, changed
assumptions, the consequential choices listed under [who decides](#who-decides),
evidence paths and next action. Store bulky comparisons or trace writeups in an
associated record; do not create a parallel permanent progress system. A
resumed agent should read that record and the diff before repeating
investigation or expensive checks.

1. **Reconcile and capture the baseline.** Compare the current checkout to the
   reviewed commit; parse the tree and inventory; capture current per-surface
   canonical payloads, shapes, stamp-table contents, free-text counts, interface
   artifacts and the guide's bytes. Identify available release history. Produce
   the complete map from the placement table, with inbound links per unit, and
   the list of position-dependent passages. Read source and check owners before
   crediting them. Establish the available Developer ID signing identity and
   keychain access, and inspect the toolchain and host prerequisites for the
   final build and selected tests using the [build dependencies](docs/DEPENDENCIES.md)
   and [test equipment guidance](tests/README.md#equipment-checks). Record the
   selected `IDENTITY` and any unavailable prerequisites in the execution
   record. Resolve missing equipment early while continuing independent
   documentation work. Leave the signed build and live verification until the
   final source has settled in steps 8 and 9.
2. **Implement the smallest complete rendering path.** Add the map, region and
   output ownership and link resolution. Exercise a request subject, a response
   subject and `transport.delivery` in ARCHITECTURE with its surface-level
   support rendered in another document. Include the history-free and preview
   paths now. Once that slice preserves its statements and payloads, apply the
   mechanism to the full map; do not build a generic publishing framework.
   These are placement commits.
3. **Retire `part`.** One commit, with its own proof.
4. **Develop REQUEST and RESPONSE together.** Rename the request guide, build
   the envelope-first response explanation, and write the authored paths around
   the routed statements. Read each exercise from supplied input through
   returned evidence and independent observation. Keep references bidirectional
   where useful.
5. **Consolidate ARCHITECTURE, add commitment lists and finish CONTRACT.** Read
   incoming protocols against ARCHITECTURE's sections; associate tour sections
   with their commitments; render trace indexes and retain support grades and
   limits. Add only the relationships the tracing exercises need; report
   unresolved relationships rather than inventing coverage.
6. **Run the tracing exercises and the promotion test.** Carry out the three
   exercises below. Then read three promises whole, each starting from
   ARCHITECTURE: collection before release, once-only invocation, and extension
   custody. If one cannot be stated from ARCHITECTURE's account and its linked
   statements without assembling clauses from several subjects, restructure the
   tree as described under
   [when a subject wants two homes](#when-a-subject-wants-two-homes) and reroute.
   Collection before release is the case most likely to need it. Record the
   reading and the decision either way. Fix other misleading reading paths the
   exercises expose, including statements that misdescribe what the source
   establishes.
7. **Finish navigation and generation.** Update README's documentation index,
   affected root and directory working guidance and READMEs, the architecture
   graph, source references in documentation, inventories and freshness
   controls. Search current uses of `REQUEST-GRAMMAR`, `CONTRACT.md`,
   `contract-*`, generated markers, `OUTPUTS` and `part`; inspect results before
   replacing. Preserve historical fixture spellings and release links where they
   intentionally describe older layouts.
8. **Update source citations.** Carry out the sweep under
   [source citations](#source-citations-and-the-build-identity) in one
   build-input commit. Regenerate the host/worker identity through its
   generator and review the three copies. Record the build identity before and
   after and name the files that moved it. This step follows step 6 because a
   restructure can still rename a node or move a statement, and precedes
   verification so that the signed build and live evidence describe the final
   source.
9. **Verify preservation.** Run the controls below, then the build and live
   verification the build-input commit requires. Fix concrete failures. Do not
   expand into unrelated coverage or rewrite runtime mechanisms to fit the
   prose.
10. **Complete editorial acceptance and handoff.** Answer the three reader
    questions through the resulting documents, write the guide outflow, explain
    remaining difficulties, record maintenance duties added and removed, and
    distinguish new verification from reused evidence. Leave a reviewable set
    of changes and an honest account of anything that prevented completion.

If a routing unit keeps needing exceptions, reconsider its home or restructure
the tree. Do not relax an inherited-scope or payload check to force a placement.

## Verification that establishes preservation

Extend the current controls, principally
[contract_tree_controls.py](tests/suites/source_drift/contract_tree_controls.py),
[build_contracts.py](tests/suites/source_drift/build_contracts.py), and
[generators.py](tests/suites/source_drift/generators.py). Use independent expected
destinations and scoped assertions for representative moves; generating an
expected map from the very routing function under test would not detect a wrong
route. Existing full-tree inventories can establish coverage.

Required observations:

- Each commit meets the proof of its [change class](#change-classes). Check
  both local and imported/shared public nodes.
- The guide's bytes equal the baseline's, by comparing the file against the
  reconciled starting commit. The standalone guide still stages with its own
  usable links and copied content.
- Every public node has exactly one rendered home; every owner retains its
  supported subject and scope. Detect omitted units, duplicate or conflicting
  destinations, unknown IDs, missing regions, and orphaned surface prose or
  support. Each rendered field retains its type/presence meaning and
  subordinate obligations.
- Cross-document links and support links resolve both ways, including compact
  rows, support inherited from a surface rendered in another document, and
  commitment-list entries. Moving a claim cannot drop its applicability,
  antecedent, first-match ordering, outcome scope or native versus constructed
  evidence limits. Include deliberate controls for those losses; a resolving
  link alone is insufficient.
- Stale bytes in every owned output are refused by `--check`, including in a
  no-tags source copy. A check writes nothing. Generation changes only owned
  regions/files; repeat generation is idempotent. Preview cannot overwrite any
  generated destination. A malformed map must not leave partly rewritten
  outputs.
- History-backed generation/checking, pending-release reproduction and retained
  legacy snapshots still work. The history-free check validates all current
  outputs and agreement of the actual stamp-table carriers, while continuing to
  report that historical derivation is unverified. Do not erase inherited
  history claims to make a fixture succeed.
- A map mutation leaves public payloads unchanged; a genuine public-condition
  or example-content mutation still changes the relevant payloads. A stale
  field shape must still fail without an unreviewed refresh. A `part` fact in
  current authoring is refused as unknown.
- Generator order does not overwrite authored explanations or another
  generator's regions, the span owner settled in seam 7 holds, and the build's
  freshness gate sees stale new outputs.

Select through the dispatcher, using a fresh output directory for each separate
execution. Inspect the selection with `--list` first. The expected offline
verification is:

```sh
PW_TEST_OUT_DIR=tests/out/runs/documentation-trace-source-drift tests/run.sh --suite source_drift
```

The relevant cases include `build_contracts`, `generator_contract`,
`architecture_documentation`, `build_documentation`, `limits_documentation` and
`interface_inventory`. Run generator-specific `--check` commands during iteration
as needed; final evidence should include the integrated suite. Explicitly verify
the production history-backed path with
`tests/lib/python.sh docs/generate_contract_stamps.py --check --require-history`
when the required annotated tags are present. Exercise history-free behavior in
the existing disposable fixtures, never by deleting checkout tags. Run the
relevant `preflight/build_entry_controls` when build freshness integration or its
fixtures change; follow its prerequisites instead of turning it into an assumed
offline success.

Select live work by the boundary actually changed:

| Change made during implementation | Additional verification |
| --- | --- |
| Rendering, routing, tree structure, public text and links only | No native rerun for these commits by themselves. They select no build input; confirm the build identity and worker identity are unchanged. |
| Source citations in build inputs (step 8) | Run `tests/lib/python.sh docs/generate_worker_identity.py` and its `--check`; confirm the porcelain and interface generators' checks still pass. Make a signed build from the final source; its identity checks before compilation and before signing must pass. Run the offline suites above with `runner_abi_layout`, `runner_unit` and `unit`; a changed layout golden after a comment-only edit is a finding, not a refresh. Then run the default battery against that build. Evidence from an earlier build describes other bytes; crediting any of it is a reviewed exception under [test guidance](tests/AGENTS.md#evaluate-and-reuse-evidence) that names the comment-only delta. |
| Example publication, admitted document, or its executable teaching/checking workflow | Follow the [example suite account](tests/suites/witness_contract/README.md#the-apps-own-example) and [interface verification](tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards); use `witness_contract/example_round_trip_controls` and `witness_contract/example_round_trip`, with unit/integration/interface checks when their owners change. |
| Test-input publication, target binding or independent observer | Follow [developer read publisher verification](tests/CHANGE-VERIFICATION.md#developer-read-publisher); use `witness_contract/test_input_controls` and `witness_contract/test_input`, adding the specified shared-observer and unit/integration checks. |
| Request corpus loading/admission | Apply the coordinated request/runner routes in [test guidance](tests/AGENTS.md) and [change verification](tests/CHANGE-VERIFICATION.md), including `runner_outcome_bad_request/accepted_input_contract` where applicable. |
| Text the app prints, found by the source sweep to name relocated documentation | Follow [interface verification](tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards) for the affected definitions, cards and corpus cases, in addition to the row above. |
| The user guide or a region copied into it | This breaks the freeze. Revert it and record the wanted change in the outflow. |
| Wait/release/query-eligibility implementation | This exceeds the scope. Isolate the decision and run the required `witness_contract/order_barrier_mutations` if the change is pursued. |

Use a current signed build when a selected workflow needs one. Follow sandboxed
harness diagnostics for signing/XPC/compiler failures and retry the same failing
command once with escalation, without changing the inspected artifact. Never
unlink the checkout lock or bypass evidence/cleanup ownership. Report missing
equipment and unrun work accurately; neither is evidence that a promise holds.

## Three bounded tracing exercises

Record each exercise as a short review: changed item, public commitment(s), full
statement and scope, governing source, relevant projection, independent support,
what the checks actually compare, the plausible review outcome and any gap.
Follow both directions using the new documents. Reuse retained mutations where
their source assumptions still apply; identify them as historical observations,
not newly executed trials. New mutations belong in disposable copies and are
needed only to resolve a concrete doubt about the new tracing machinery.

Node IDs below are those of the reviewed tree. If a restructure renames one,
follow the renamed node and say so in the review.

### 1. Interface vocabulary and result projection

Use `run.option.runner_mode` and `result.admitted_finished` as two small entries
into one interface review. Start with their declarations under
[src/interface](controller/src/interface/) and the
[retained mutations](controller/interface/mutations.json), including
`rename_option`, `acceptance_connected_exit` and
`acceptance_numeric_copy_then_exit`. Follow the inventory and join to
`request.options.precedence` in REQUEST and `envelope.data.select.finished` in
RESPONSE, CONTROLLER's commitment list for result selection, supporting cases
and limits.

The review should distinguish a renamed command spelling, result-field/exit
behavior, a renderer's stale private copy, and a support identifier rename.
Explain the actual promise at risk and why the row's applicability matters.
Retain the join report's uncompared admission class and inherited free
conditions; do not claim the whole rule is machine-verified because a literal
output matched. If a spelling promise lacks a direct public-statement link,
expose that gap or add a justified narrow connection; do not invent coverage.

### 2. Example composition and admission

Start at [EXAMPLE_DOCUMENT](controller/src/example_document.rs) and the retained
`example_field` mutation. Follow its extracted document into
`request.specimen.emit_example`, the public request example, the example help
projection and the independent
[round-trip checker](tests/suites/witness_contract/check_example_round_trip.py).
Inspect the admission path in
[PWRunnerRequest](runner/Sources/PWRunnerCore/PWRunnerRequest.swift) and the
actual associated admission checks, rather than substituting the extraction
check for host grammar admission.

Show which changes affect the specimen's composition, its public snapshot,
the build's admission promise, displayed fragments or the independently authored
workload/target expectations. A displayed target changing does not itself revise
the admission promise. An admitted example does not prove that all three
attempts succeed. Flat and actor derivatives belong to the harness, not to what
`example` publishes. Preserve each form's independent samples and evidence scope.

### 3. Controlled read through worker observation

Start at [test_input.rs](controller/src/test_input.rs), its
[read body](controller/src/test_inputs/README.md), and a controlled read whose
saved input is reused across an in-place change or path replacement. Follow
`request.specimen.emit_test_input`, the request's independent query/attempt
operands, `steps.fresh_read` and `steps.assessment.fresh_read_aggregate` in
RESPONSE, then WORKER's fresh-acquisition/publication account through its
commitment list and the cited implementation in
[pw_probe_runner.c](controller/tools/pw_probe_runner/pw_probe_runner.c).
Then follow the reported data back through the host projection and controller
reader to RESPONSE, and to the independent harness samples and
`distinctions.json` described in the controlled-read suite.

Use at least one instructive limit: a replaced inode with otherwise equal
content/metadata, a suffix change beyond the returned prefix, or the crossed
query/attempt targets. Explain what the worker observed and what only the
independent samples establish. Before/after samples do not prove continuous
stability; a bounded read does not establish the entire file contents. Help and
publisher bytes can remain unchanged while these observations or their governing
worker behavior deserve review. This trace must remain useful without a help
association or a universal change detector.

## Editorial acceptance and acceptable residuals

After mechanical preservation passes, read the result as a developer and
reviewer. Write a short answer to each opening question using the actual reading
path. For each answer, identify a difficult transition or missing relationship,
if one remains. Review the three traces and the three protocol readings for
scope and consequence, not just URLs.

Acceptance requires that:

- REQUEST teaches a developer a usable specimen and its obligations, and
  RESPONSE lets that reader interpret success, refusal and incomplete evidence
  without treating publication, execution and interpretation as
  interchangeable.
- ARCHITECTURE states each received protocol whole, and collection before
  release can be read whole from it. The other tours lead from a mechanism to
  the commitments it serves.
- CONTRACT finds particular commitments implicated by a change, with honest
  implementation/interface/evidence relationships and visible unknowns. It holds
  what tracing needs and no leftover reference material.
- Every payload difference from the baseline belongs to a named commit: the
  `part` retirement or a public change with its cause. Meanings, support
  qualifications and independent expectations survive every placement.
- The guide is byte-identical to the baseline and its outflow is written.
- Source citations name the documents that hold the statements they rely on.
  The build identity and worker identity changes are attributed to named files,
  and the signed build and live evidence describe the final source.
- Maintenance duties are explicit: where to author meaning, where to route it,
  what to regenerate, and which checks or live observations a changed boundary
  requires. The new system adds no second source of public meaning.

Do not set numerical targets for document length, trace coverage or residual
count. Long references and partial source associations can remain if they are
usable and candid. Do not postpone delivery to connect every field to every
test. Conversely, a clean diff of payloads cannot excuse an unreadable
arrangement, and a persuasive reading exercise cannot excuse dropped
qualifications.

Keep acceptance evidence with this plan until review consumes it. Retirement of
the plan and its temporary records is a later acceptance action; the guide
outflow stays for the guide rewrite. Permanent docs must already explain the
resulting maintenance workflow without those records.

## Preparation and execution record

Preparation completed on 2026-11-15:

- Confirmed HEAD equals the reviewed commit and no initial working-tree edits.
- Read repository/planning, documentation, contract, controller, runner and
  records guidance; inspected the current reading paths, surface structure,
  rendering/history code, interface joins, fixture ownership and relevant suites.
- Loaded the current tree through the owning parser. Counted its nodes; listed
  every subject with its effective `part`, record and rules; tabulated each
  rule's acting components; confirmed that every node ID this plan names
  resolves. Inspected the six interface associations and surface-level support
  owners. Found 14 reachable annotated release tags and a public snapshot at
  `v0.3.7`; historical derivation was not run here.
- Read the guide's outline, its contract pointer and its generated regions;
  counted limit spans in the surface sources and rendered documents; searched
  for readers of `part`; searched the build-identity inputs for citations of
  documentation by path, and read the build-identity and worker-identity input
  selections.
- Listed the `source_drift` selection through the dispatcher and confirmed that
  the named cases and linked verification anchors exist. No test suite, live
  specimen, signed build or implementation acceptance was run for this
  planning-only change.
- Follow-up review confirmed that the shared span reader excludes a span inside
  a contract region using the existing generated-region convention, while
  recognizing the same span outside it. This establishes the existing exclusion
  behavior; the integrated ownership control remains implementation work.

Not established by preparation: how each generator treats a foreign region in a
file it owns beyond the shared span exclusion, whether ARCHITECTURE's present
ordering account supports reading collection before release whole, which
statements the header comment relies on, and what source text beyond path
citations describes the contract's layout. Steps 2, 6 and 8 answer these.

Execution began from `2fcf9dbc9f08b1643426b4cf9b9b32e3782c86cc`. Step 1 is complete.
The checkout was clean; the only differences from the reviewed baseline were
three plan commits. [Baseline capture](records/documentation-trace/baseline.md),
[comparison inventory](records/documentation-trace/baseline.json),
[equipment](records/documentation-trace/baseline-equipment.json) and the
[complete initial routing/inbound inventory](records/documentation-trace/baseline-routing.json)
record the reconciled state. The initial map follows the placement table.

Selected `IDENTITY`: `Developer ID Application: Adam Hyland (42D369QV8E)`.
Identity discovery and native-host sysctls succeeded on identical escalated
retries. Required tools and installed pytest are present; compiler/SDK/Rust
versions match the existing toolchain stamp. Private-key signing, timestamp
service access and XPC execution remain to be established by the final build
and live battery. No equipment gap currently prevents implementation.

Independent source reviews are recorded in the
[interface/example trace](records/documentation-trace/interface-example-review.md)
and [controlled-read trace](records/documentation-trace/controlled-read-review.md).
These are source readings and historical-evidence reviews, not newly executed
native observations. The [protocol review](records/documentation-trace/protocol-review.md)
recommends no promotion: ARCHITECTURE can retain its complete ordering account
and link the complete returned-evidence rule. It identifies a source-established
actor advancement wording correction and a cross-document positional reference;
these will be separate public changes after `part` retirement.

Step 2's rendering path is implemented. The explicit map covers every surface
and all 180 whole-subject units; authored teaching paths and tour lists are in
place. [Placement proof](records/documentation-trace/placement-proof.json), made
with the [comparison script](records/documentation-trace/compare_payloads.py),
confirms unchanged public payloads, shapes, counts, stamps, guide, interface
artifacts and build/worker identities. History-backed generator checking passes.
The initial `source_drift/build_contracts` execution at
`tests/out/runs/documentation-trace-placement` failed because a tour list named a
definition where the map admits subjects or rules. That invalid entry was
removed. All six constructed history controls passed; the new presentation
controls still need a clean execution. This run is local, gitignored evidence.
Final integrated verification remains step 9. Next action: retire `part` with
its exact-removal proof, then finish protocol consolidation and navigation.


Step 3 complete: the dedicated retirement removes 32 authored `part` facts and
the parser/renderer fact support. The
[exact-removal proof](records/documentation-trace/part-retirement-proof.json)
compares local and shared payload nodes to placement commit `2500d59e`: its 203
serialized occurrences are the only payload differences. Shapes, stamp contents,
free counts, guide bytes, interface artifacts and build identities remain equal.
Current authoring controls now require `part` to be refused as unknown; released
snapshot readers remain independent of authoring syntax. Next: the two named
public-text corrections and final tour/navigation integration.

Public correction: `actors.phase.order` now distinguishes ordinary completed-phase
advance from serial actor scheduling after failed setup or a failed active visit.
The cited scheduler branches and independently read assertions support the
skip/reap/continue distinction; a new local check-read owner states its limits.
The [actor correction proof](records/documentation-trace/actor-advancement-proof.json)
confines every local/shared public difference to that rule's `free.effect`.
Affected surfaces: `actors`, `request`, `envelope`, `extensions`, `installation`,
`probes`, `refusals` and `reply` (the latter seven import the same public node).
No runtime, shape or ordering-eligibility change.

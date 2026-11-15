# Request, response and public-commitment tracing

Status: first draft for implementation. No documentation relocation or generator
change has been made. The preparation and execution notes at the end distinguish
inspection from completed implementation and verification.

## Purpose and authority to proceed

Reorganize the documentation around three questions:

1. What request can I supply, and what obligations accompany it?
2. What does the returned evidence establish, including refusals and incomplete
   execution?
3. When implementation, tests or generated interfaces change, which public
   commitments deserve examination, and where are they stated?

`docs/REQUEST.md` will own the first reading path, `docs/RESPONSE.md` the second,
and `docs/CONTRACT.md` the third. CONTROLLER, WORKER, ARCHITECTURE and BUILD may
carry complete public commitments where their surrounding explanations make
those commitments clearer. Public meanings remain authored in the contract
surface tree; their rendered location does not determine whether they are public.

This is a change to how the repository exposes and traces the instrument, not
just a division of a large document. A good result lets a reviewer follow a
consequential operation through its declarations, implementation, observations,
interpretation and public promises without mistaking any one of those for the
others. Passing generators establishes necessary preservation properties. It
does not establish that the new accounts are useful.

Execute the whole plan without scheduled approval stops. The placements below
are reasoned defaults, not a demand to force every passage into a predetermined
file. Settle ordinary editorial and implementation choices locally, record the
few consequential choices, and continue. Review checkpoints below are work for
the executor, not requests for the maintainer to supervise each stage.

The authorized scope includes renaming and writing documents, adapting rendering
and navigation, extending existing controls, and correcting ownership guidance
to describe that arrangement. It does not include changing runtime behavior,
designing a new public schema, rewriting the help system, or silently revising a
public promise. When relocation exposes a questionable promise, retain its
present meaning and isolate the proposed correction and its evidence. Complete
the independent reorganization. Seek a decision only if a genuinely unresolved
meaning prevents a coherent result; explain the specific conflict and the
alternatives, rather than asking for general approval to proceed.

Useful rough edges are acceptable: a long reference section, a justified
residual in CONTRACT, useful repetition, an explicitly incomplete trace, or a
mechanism described in prose. Lost conditions, conflicting owners, fabricated
evidence and misleading claims of completeness are not acceptable rough edges.

## Starting evidence and reconciliation

The reviewed state is
[`6fcd2b5f1c84094405e2ce4de035b538a411b7cc`](https://github.com/Protonk/PolicyWitness/commit/6fcd2b5f1c84094405e2ce4de035b538a411b7cc).
At preparation on 2026-11-15, local HEAD was exactly that commit and the working
tree was clean. There were no subsequent changes to reconcile. The commit that
adds this plan is not an implementation change.

Before implementation, compare the then-current checkout with that baseline.
Read subsequent changes affecting the owners below, preserve unrelated work,
and record any adjustment to this plan's assumptions. Do not reset the checkout
to the reviewed commit. Obtain the actual starting public snapshot, shape
goldens, stamp tables and relevant interface artifacts from the reconciled
checkout; use the reviewed commit to explain differences, not to erase them.

Follow [planning and documentation guidance](CONTRIBUTING.md),
[documentation rules](docs/AGENTS.md),
[surface authoring rules](docs/contract/AGENTS.md), and
[test guidance](tests/AGENTS.md). Read the controller or runner working rules
when investigating their respective boundaries. Supporting investigation and
acceptance records may live in `records/documentation-trace/`, linked from this
plan only, following [records guidance](records/AGENTS.md). Permanent documents
must stand without those temporary records.

### Grounding already established

- [REQUEST-GRAMMAR](docs/REQUEST-GRAMMAR.md) is an authored teaching sequence,
  including independent file effects, refusal expectations, phases, actors and
  controller/direct-XPC differences. It is not the complete request definition.
- [CONTRACT](docs/CONTRACT.md) is currently one generated document. The
  [surface tree](docs/contract/README.md) has 19 surfaces, 182 subjects, 1,004
  fields and 151 support owners at the reviewed state. Those counts describe
  the baseline, not targets to freeze forever. The work must account for the
  full tree, not only the input and output fields most visible in examples.
- [tree.py](docs/contract/tree.py) routes rendering by `part`. Its
  `_node_public` includes `part`, titles, prose, context and relationship facts
  in canonical public content. Moving a subject in the authored hierarchy can
  also change identity and inherited meaning. Neither is a safe layout knob.
- [runtime.py](docs/contract/runtime.py) uses one `OUTPUTS` tuple for CONTRACT
  and the guide, including assumptions that both contain stamp tables.
  `assemble`, `_claimed_history`, `render` and the history-free branch of
  `check` depend on that arrangement. The
  [entry point](docs/generate_contract_stamps.py) protects only CONTRACT from
  preview overwrite. Several fixture helpers assume positional outputs.
- [CONTROLLER](docs/CONTROLLER.md) already explains request holding,
  publication, invocation uncertainty, admission, result selection and runner
  cleanup. Its authored account should be consolidated with incoming rules.
  [WORKER](docs/WORKER.md) already follows acquisitions, authority and
  publication; its detailed capability inventory is architecture-generated.
- [ARCHITECTURE](docs/ARCHITECTURE.md) and WORKER receive regions from
  [architecture.json](docs/architecture.json) through
  [generate_architecture.py](docs/generate_architecture.py).
  [BUILD](docs/BUILD.md) combines authored explanation with regions and spans
  owned by [build.json](docs/build.json) and
  [generate_build.py](docs/generate_build.py). None is a blank destination.
- [generate_limits.py](docs/generate_limits.py) names REQUEST-GRAMMAR in
  `SPAN_DOCUMENTS`; it also owns shared content copied into the standalone
  guide. The document graph, generator ownership controls and copied fixture
  inventories must change with rendering.
- The [interface inventory](controller/interface/README.md) already connects
  definitions, cards, corpus cases and recorded mutations. Six contract nodes
  currently cite `interface` identifiers. The
  [join](docs/contract/interface_join.py) checks selected structured facts;
  it explicitly leaves prose, free conditions and the admission-class binding
  outside that comparison. It supplies useful partial traces, not a general
  change-impact classifier.

## Ownership and placement decisions

Separate three kinds of ownership throughout the change: the source defining a
public meaning, the document presenting its complete statement, and the source
or observation supporting it. The surface tree remains the first; destination
routing changes the second; support owners and existing independent checks
retain the third. A technical tour can therefore contain both explanatory prose
and a clearly identifiable generated commitment without becoming another
independently maintained definition.

Start from this subject map. IDs below refer to the existing surface tree, not
new identities to create. Descendants normally travel with their subject.
Where a subject mixes several responsibilities, split its rendered presentation
at an existing coherent rule or definition boundary, keeping the authored tree
and effective scope intact.

| Existing material | Proposed complete-statement home and treatment |
| --- | --- |
| `request.specimen`, `request.options`, `request.selector`, `request.overrides` in [10-request](docs/contract/10-request.surface.md) | REQUEST: forms, defaults, identity obligation, selector precedence, publication promises and explicitly test-only overrides. Explain `request.specimen.hold` with CONTROLLER's held-input account if moving that complete rule improves it. |
| `policy.spec` and the caller-facing parts of `policy.augments` in [11-policy](docs/contract/11-policy.surface.md) | REQUEST: policy source, parameters and augment obligations. CONTROLLER explains resolution and held inputs; WORKER explains native compilation/application. Do not leave parameter admissibility separated from the restrictions that qualify it. |
| `probes.step`, `probes.query`, `probes.filter`, `probes.attempt` in [12-probes](docs/contract/12-probes.surface.md) | REQUEST: paired declarations, supported filters/attempts, applicability and caller inputs. WORKER may carry the complete execution rules `probes.attempt.execute` and `.exec`; REQUEST must still explain what each requested operation means and link to its observations. |
| `actors.actor`, `.sandbox`, `.phase`, `.after_termination`, `.action` in [13-actors](docs/contract/13-actors.surface.md) | REQUEST: actor/phase declaration and dependency admission. ARCHITECTURE is the preferred home for the complete fresh-process, collect/release/advance and termination-gate protocols; keep declaration restrictions discoverable at the request. |
| `extensions.action`, `.operation`, `.examples` in [14-extensions](docs/contract/14-extensions.surface.md) | REQUEST: operands, reference ownership, action ordering, capacities and per-participating-actor exec exclusion. Keep examples with the conditions they teach and distinguish their constructed and native support. |
| `extensions.custody` | ARCHITECTURE for the complete cross-process custody protocol; WORKER explains its native operations and resource lifetime. Avoid scattering issue/delivery/acknowledgement/erasure conditions into disconnected fragments. |
| `extensions.event`, `.transfer`, `.resources`, `.token`, `.delivery`, `.handle` | RESPONSE: event and retained-resource meanings, including the limits of transfer receipts and observations. Link to the full custody protocol and worker operations. |
| `refusals.request`, `.controller`, `.admission`, `.examples` in [15-refusals](docs/contract/15-refusals.surface.md) | REQUEST for admission order, caller restrictions and correction exercises; RESPONSE for returned refusal records and bounded/sanitized evidence. Route complete rules, not individual clauses stripped from their failure trigger. |
| `refusals.projection`, `.later` | RESPONSE: projected diagnostics and the distinction between a known refusal and uncertainty after invocation. CONTROLLER explains the selection mechanism. |
| `transport.authorization`, `.delivery`, `.reservation`, `.control` in [20-transport](docs/contract/20-transport.surface.md) | ARCHITECTURE for authorization, reservation, original deadline and once-only execution as a complete protocol. Control-record definitions can accompany it. CONTROLLER links its delivery decisions into that account. |
| Remaining transport subjects: capture, acquisition, submission, retained reply, client errors/process observations, delivery and rejected stdout | RESPONSE: what the caller can use, what is retained, and what remains unknown. CONTROLLER for the complete capture-admission decision where it fits that tour. |
| `wire.frame`, `wire.validator` in [21-wire](docs/contract/21-wire.surface.md) | ARCHITECTURE for framing and cross-process protocol; RESPONSE explains decoded/carried projections and links exact admission rules. Preserve byte/type distinctions, fallback and producer gates. |
| `reply.record`, `.failure` in [30-reply](docs/contract/30-reply.surface.md) | RESPONSE: host account and reporting fallback; put production mechanics beside ARCHITECTURE's communication account only when the full publication commitment remains intact. |
| All subjects of [31-steps](docs/contract/31-steps.surface.md) | RESPONSE for prediction, attempt, comparison, ordering and fresh-I/O meanings. WORKER can carry complete acquisition/publication rules; ARCHITECTURE can carry the ordering protocol. Keep interpretation conditions next to the records they qualify. |
| All subjects of [32-lifecycle](docs/contract/32-lifecycle.surface.md) and [33-actor_evidence](docs/contract/33-actor_evidence.surface.md) | RESPONSE for process/phase/application/gate evidence, disposition, native references and incomplete collection. ARCHITECTURE or WORKER may explain governing protocols, without breaking a classifier's complete cases or inherited conditions across documents. |
| All subjects of [34-equipment](docs/contract/34-equipment.surface.md) and [35-profile](docs/contract/35-profile.surface.md) | RESPONSE for equipment, authority setup and compiled-profile receipts. BUILD owns identity construction; WORKER explains setup and capture; CONTROLLER explains carried-label admission. Static inventory, live read-back and effective authority remain distinct. |
| `envelope.run`, `.result`, `.data` in [40-envelope](docs/contract/40-envelope.surface.md) | Open RESPONSE here. Explain process exit and the outer result before nested evidence. CONTROLLER can carry `envelope.data.select` and `.admit` with its decision account, linking the complete result relation from RESPONSE. |
| All subjects of [41-diagnostics](docs/contract/41-diagnostics.surface.md) and [42-dossier](docs/contract/42-dossier.surface.md) | RESPONSE for assessment meanings and dossier records; CONTROLLER for complete collection and evaluation commitments. Preserve withheld assessments beside retained records and the distinction between separately sampled files and held inputs. |
| `identity.public`, `.surfaces`, `.other` in [00-identity](docs/contract/00-identity.surface.md) | BUILD for identity derivation, release/development assertions, provenance distinctions and history derivation. CONTRACT retains the surface-history table and explains its review use; link its complete derivation. |
| `identity.build`, `.producer`, `.version` | RESPONSE for build/producer fields where encountered, and a clearly marked version-output reference. Link to BUILD's identity commitments. |
| `identity.definitions` | Keep the complete shared definitions in CONTRACT initially, with short reading keys in REQUEST/RESPONSE derived from or checked against them. Move a definition only when its new home improves all relevant uses. |
| Standalone helper subjects: `policy.helper_request`, `.helper_policy`, `.check_data`, `.compile`, `.imports`, `.fallback`, `.actor_check`; `envelope.helper`; `wire.standalone*` | Give compiler-helper and direct-validator interfaces explicit labeled reference sections: request forms in REQUEST, result forms in RESPONSE, fallback orchestration in CONTROLLER, native/protocol mechanics in WORKER or ARCHITECTURE. Keep each helper's applicable entry and producer distinct from `run`. If splitting an interface impairs comprehension, retain its complete account as a named CONTRACT reference and link both reading paths. |
| All subjects of [50-installation](docs/contract/50-installation.surface.md) | CONTROLLER's equipment-administration account is the default home for command-specific obligations and record definitions. These are machine-state operations, not specimen results. Preserve lock ownership, pending state, verification limits and observed-absence cleanup conditions. Retain the external-runner guide as the operational workflow. |

The implementation inventory should enumerate every subject and any separately
routed descendant, name its canonical destination, and identify inherited
context/support and inbound links. Derive the exhaustive node list from the tree;
do not manually catalogue another thousand field definitions. Group placement
rationales by subject. Account explicitly for surface introductions, examples,
gaps, shared definitions and owners attached above subjects as well as the
subjects themselves. No catch-all silent routing to CONTRACT: residuals get a
named purpose and a reviewed home.

## Reading paths to produce

### REQUEST

Rename REQUEST-GRAMMAR, preserving its useful progression from an observable
create, through one-change refusals, to phases, actors and entry-point
differences. Integrate reference material into that progression or into clearly
linked reference sections; do not put the entire old CONTRACT input part ahead
of the teaching sequence.

The introduction should distinguish caller declaration, controller resolution,
host admission and contingent execution. Explain how to obtain the current
build identity without equating an identity match with valid input. Keep
omission/null distinctions, defaults, capacity-before-meaning ordering,
branch-local refusal precedence, shadowed-selector validation and actor-specific
restrictions explicit. Identify `_test_overrides` as test controls, including
the limits of an echoed override.

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
derivation. Give receipts, equipment, extensions, lifecycle and dossier an
accessible route from the envelope. Keep standalone helper and administration
outputs clearly labeled. Authored explanation in REQUEST and RESPONSE is
allowed; the help-card restriction on authored text does not apply here.

### Receiving technical accounts

Read each existing section against its incoming commitments before editing.
Replace or consolidate overlap; avoid an unchanged tour followed by a second
full account. Preserve the tours' organizing subjects: controller decisions,
worker resources and authority, cross-process boundaries, and the build's
identity/signing/provenance responsibilities.

A moved promise needs one identifiable complete statement with its applicable
operation, conditions, consequences and qualifications. Supporting component
explanations can be elsewhere. Cross-component promises such as collection
before release, once-only invocation and extension custody must remain readable
as a whole. A source mechanism is not automatically a promise; a technically
detailed restriction can still be something a caller relies on.

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
- **From a commitment:** its stable surface/subject/rule identity, canonical
  statement, applicability and consequence, imported fields/declarations,
  relevant interface projections, and graded support with actual assertion
  scope and known gaps.

Reuse tree relationships, record imports, `interface` facts, the inventory,
case joins and mutation records. Generate indexes from those owners where the
relationship exists. Add narrow presentation/support metadata only when it
feeds a useful view or check. Do not infer behavioral reach from staged input
files, infer authority from filenames, or make every promise connect to help,
example and test-input. An absent connection must remain an absent connection.

Begin with subject-level navigation and focused rule-level traces; a giant
field-by-every-source matrix would bury the review. Shared definitions, notation,
surface history and support details may remain here when they serve tracing.
Keep inherited conditions and `free.*` qualifications visible at the statement;
support detail links are not a substitute. Retain applicability, controller
finding and known-gap views where useful, making their targets destination-aware.

The result is a maintained review aid, not a comprehensive impact-analysis
engine. No new all-purpose dependency language, automatic semantic verdict,
universal coverage score or mandatory connection to every command is required.

## Rendering design and preservation boundaries

Use a presentation map outside canonical public meaning. The default design is
an explicit file under `docs/contract/` mapping stable node IDs to document
regions and ordering, consumed by the existing contract generator. A separate
module is equally reasonable if it is easier to review. Do not change `part`,
node IDs, semantic ancestry, rule/case order or public titles to obtain layout.
Do not simply exclude existing `part` facts from hashing: that would itself
change the canonical representation and historical comparison.

Keep authored explanations in the receiving documents around owned generated
regions. The contract generator owns the complete commitment blocks and tracing
views. Architecture/build/limits generators retain their existing distinct
regions or spans. The production route should render one canonical location
for each commitment; secondary presentations can be derived excerpts, links or
checked explanations, visibly tied to that location.

Implementation must address these concrete seams:

1. **Coverage and inherited scope.** Route whole subject/rule units first. A
   split must carry effective context, bindings, quantified scope, prerequisites,
   inherited free conditions, support and public gaps. Keep first-match cases
   together and ordered. A field cannot lose its local obligations or the
   conditions inherited from its subject. Surface-wide owners must still support
   the moved descendants with their original scope, not acquire a broader one.
2. **Destination-aware links.** Replace `_link`'s single-document assumption;
   cover field-type links, expressions/references, support paragraphs/details,
   derived views, examples and authored prose links. Preserve stable explicit
   `contract-*` anchors at the complete statement. Rebase links while rendering
   instead of editing stamped prose only to change a URL. Use the repository
   Markdown reader where it can distinguish links from code and examples.
3. **Existing callers.** Update current repository inbound links and their
   descriptions. Keep intentional historical-release links unchanged. Where
   old CONTRACT fragments plausibly serve published callers, generated forwarding
   entries in the trace index are a reasonable compatibility measure; they
   should identify the canonical destination, not duplicate an obsolete account.
   Avoid retaining a second REQUEST-GRAMMAR account just to preserve its name;
   use a small redirect stub only if concrete inbound use warrants one.
4. **Output versus history inventory.** Separate rendered document/region
   ownership from stamp-table locations. Default stamp tables remain in CONTRACT
   and the standalone guide; REQUEST, RESPONSE and every tour need not gain one.
   Change runtime assembly, claimed-history discovery and both checking paths
   accordingly. Keep v0/v1 release readers and released snapshots readable.
5. **Partial document ownership.** Replace whole-file CONTRACT assumptions as
   needed, declare new regions explicitly, and preserve authored surrounding
   prose. Adapt the entry point, `input_paths`, generator ownership declarations,
   [fixture_inputs](tests/lib/fixture_inputs.py),
   [contract_fixture](tests/lib/contract_fixture.py), and disposable fixtures.
   Remove positional `OUTPUTS[0]`/`OUTPUTS[1]` assumptions where their meaning
   would become ambiguous. Preview must protect every owned output, not only
   CONTRACT, and must validate all selected destinations before writing.
6. **Interacting generators.** Update limits' renamed span document, architecture
   document/edge records, and receiving generator inputs. Keep regions disjoint.
   Ensure a complete regeneration reaches a fixed point: a later generator must
   not silently stale an earlier output. Keep copied guide sections self-contained
   without repository-relative dependencies.
7. **Public versus supporting changes.** Metadata for routes, provenance or
   support must remain outside stamped public meaning. `_node_public` also stamps
   prose and titles, so even equivalent rewording can change a payload. First
   prove exact placement-only preservation; review any later authored public-text
   difference separately, naming its cause and affected surfaces. Never normalize
   away a real difference or accept refreshed goldens to make checks pass.

Keep build identity separate from surface identity. A changed file selected by
the build digest can legitimately change `development:<sha256>` even while
every public surface payload and shape is identical. Clean/tagged state can
also affect the identity form. Trace that cause rather than promising that all
identifiers are invariant under documentation work.

## Execution sequence and resumption

Use coherent local commits to separate infrastructure, relocation, and any
deliberate semantic proposal. Update the short execution record at the end of
this plan with the last completed step, changed assumptions, evidence paths and
next action. Store bulky comparisons or trace writeups in an associated record;
do not create a parallel permanent progress system. A resumed agent should read
that record and the diff before repeating investigation or expensive checks.

1. **Reconcile and capture the baseline.** Compare the current checkout to the
   reviewed commit; parse the tree and inventory; capture current per-surface
   canonical payloads, shapes, stamp-table contents, free-text counts and
   interface artifacts. Identify available release history. Read source/check
   owners needed for proposed moves before crediting them. Produce the complete
   subject/destination inventory described above, including residuals and
   inherited support. This resolves the work's scope before prose relocation.
2. **Implement the smallest complete rendering path.** Add presentation routing,
   region/output ownership and link resolution. Exercise a request subject, a
   response subject and a cross-component rule with inherited support across
   different documents. Include the history-free and preview paths now. Once
   that slice preserves its complete statements and payloads, apply the same
   mechanism to the full inventory; do not build a generic publishing framework.
3. **Develop REQUEST and RESPONSE together.** Rename the request guide, build
   the envelope-first response explanation, and integrate routed definitions.
   Read each exercise from supplied input through returned evidence and
   independent observation. Keep references bidirectional where useful.
4. **Consolidate technical accounts and finish CONTRACT.** Review incoming rules
   against the tours, resolve residual homes, render trace indexes and retain
   support grades/limits. Check that a cross-component promise can still be read
   whole. Add only the relationships needed by the concrete tracing exercises;
   report unresolved relationships rather than inventing coverage.
5. **Finish navigation and generation.** Update README's documentation index,
   affected root/directory working guidance and READMEs, the architecture graph,
   source references, inventories and freshness controls. Search current uses
   of `REQUEST-GRAMMAR`, `CONTRACT.md`, `contract-*`, generated markers and
   `OUTPUTS`; inspect results before replacing. Preserve historical fixture
   spellings and release links where they intentionally describe older layouts.
6. **Verify preservation and exercise tracing.** Run the controls and the three
   reviews below. Fix concrete failures and misleading reading paths. Do not
   expand into unrelated coverage or rewrite runtime mechanisms to fit the prose.
7. **Complete editorial acceptance and handoff.** Answer the three reader
   questions through the resulting documents, explain remaining difficulties,
   record maintenance duties added/removed and distinguish new verification
   from reused evidence. Leave a reviewable set of changes and an honest account
   of anything that prevented completion.

If a route repeatedly needs exceptions, first reconsider the document placement
or move a larger coherent unit. If no better placement emerges, retain that
unit as an explicitly named reference in CONTRACT and continue. Do not relax
inherited-scope or public-payload checks to force dispersal.

## Verification that establishes preservation

Extend the current controls, principally
[contract_tree_controls.py](tests/suites/source_drift/contract_tree_controls.py),
[build_contracts.py](tests/suites/source_drift/build_contracts.py), and
[generators.py](tests/suites/source_drift/generators.py). Use independent expected
destinations and scoped assertions for representative moves; generating an
expected map from the very routing function under test would not detect a wrong
route. Existing full-tree inventories can establish coverage.

Required preservation observations:

- Placement-only rendering leaves canonical per-surface public payloads,
  `public.json`, shape goldens, free-text counts and surface stamp contents
  unchanged. Check both local and imported/shared public nodes. Compare actual
  payloads, not merely the displayed stamp: several different changes can all
  display `unreleased`. Interface inventory, card bytes and joins should also
  remain unchanged unless an explicitly identified owner changed.
- Every public node has a canonical rendered destination or a declared complete
  containing statement; every owner retains its supported subject and scope.
  Detect omitted subjects, duplicate/conflicting destinations, unknown IDs,
  missing regions, and orphaned surface prose or support. Each rendered field
  retains its type/presence meaning and subordinate obligations.
- Cross-document links and support links resolve both ways, including compact
  rows and support inherited from a surface. Moving a claim cannot drop its
  applicability, antecedent, first-match ordering, outcome scope or native versus
  constructed evidence limits. Include deliberate controls for those losses;
  a resolving link alone is insufficient.
- Stale bytes in every new output are refused by `--check`, including in a
  no-tags source copy. A check writes nothing. Generation changes only owned
  regions/files; repeat generation is idempotent. Preview cannot overwrite any
  generated destination. A malformed route must not leave partly rewritten
  public outputs.
- History-backed generation/checking, pending-release reproduction and retained
  legacy snapshots still work. The history-free check validates all current
  outputs and agreement of the actual stamp-table carriers, while continuing to
  report that historical derivation is unverified. Do not erase inherited
  history claims to make a fixture succeed.
- A presentation-route mutation leaves public payloads unchanged; a genuine
  public-condition or example-content mutation still changes the relevant
  payloads. A public `part` edit must not be newly ignored. A stale field shape
  must still fail without an unreviewed refresh.
- The standalone guide still stages with its own usable links and copied
  content. Generator order does not overwrite authored explanations or another
  generator's regions, and the build's freshness gate sees stale new outputs.

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
| Rendering, routing, explanatory text and links only | No native rerun merely to relabel existing evidence. Review reuse against unchanged owners and assertion scope. |
| Example publication, admitted document, or its executable teaching/checking workflow | Follow the [example suite account](tests/suites/witness_contract/README.md#the-apps-own-example) and [interface verification](tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards); use `witness_contract/example_round_trip_controls` and `witness_contract/example_round_trip`, with unit/integration/interface checks when their owners change. |
| Test-input publication, target binding or independent observer | Follow [developer read publisher verification](tests/CHANGE-VERIFICATION.md#developer-read-publisher); use `witness_contract/test_input_controls` and `witness_contract/test_input`, adding the specified shared-observer and unit/integration checks. |
| Request corpus loading/admission | Apply the coordinated request/runner routes in [test guidance](tests/AGENTS.md) and [change verification](tests/CHANGE-VERIFICATION.md), including `runner_outcome_bad_request/accepted_input_contract` where applicable. |
| Ordinary guide acquisition or its executable workflow | Run the whole `witness_contract/guide_workflows` case with its signing, GUI and registry prerequisites; do not excerpt its native sequence. |
| Wait/release/query-eligibility implementation unexpectedly changes | This exceeds relocation scope. Isolate the decision and run the required `witness_contract/order_barrier_mutations` if the change is pursued. |

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

### 1. Interface vocabulary and result projection

Use `run.option.runner_mode` and `result.admitted_finished` as two small entries
into one interface review. Start with their declarations under
[src/interface](controller/src/interface/) and the
[retained mutations](controller/interface/mutations.json), including
`rename_option`, `acceptance_connected_exit` and
`acceptance_numeric_copy_then_exit`. Follow the inventory and join to
`request.options.precedence` and `envelope.data.select.finished`, their new
complete-statement homes, supporting cases and limits.

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
operands, `steps.fresh_read` and `steps.assessment.fresh_read_aggregate` to
WORKER's fresh-acquisition/publication account and the cited implementation in
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

After mechanical preservation passes, read the result as a user and reviewer.
Write a short answer to each opening question using the actual reading path.
For each answer, identify a difficult transition or missing relationship, if
one remains. Review the three traces for scope and consequence, not just URLs.

Acceptance requires that:

- REQUEST teaches a usable specimen and its obligations, and RESPONSE lets a
  reader interpret success, refusal and incomplete evidence without treating
  publication, execution and interpretation as interchangeable.
- The technical accounts improve in context. A reader can find a complete
  cross-component promise without reconstructing it from scattered clauses.
- CONTRACT finds particular commitments implicated by a change, with honest
  implementation/interface/evidence relationships and visible unknowns. It no
  longer gets its purpose from an accumulation of leftover reference material.
- Public identities, meanings, support qualifications and independent
  expectations survive relocation. Any deliberate public-text difference has
  a separately reviewable explanation rather than an indiscriminate refresh.
- Maintenance duties are explicit: where to author meaning, where to route it,
  what to regenerate, and which checks or live observations a changed boundary
  requires. The new system adds no second source of public meaning.

Do not set numerical targets for document length, trace coverage or residual
count. Long references and partial source associations can remain if they are
usable and candid. Do not postpone delivery to connect every field to every
test. Conversely, a clean diff of payloads cannot excuse an unreadable split,
and a persuasive reading exercise cannot excuse dropped qualifications.

Keep acceptance evidence with this plan until review consumes it. Retirement of
the plan and associated records is a later acceptance action; permanent docs
must already explain the resulting maintenance workflow without those records.

## Preparation and execution record

Preparation completed on 2026-11-15:

- Confirmed HEAD equals the reviewed commit and no initial working-tree edits.
- Read repository/planning, documentation, contract, controller, runner and
  records guidance; inspected the current reading paths, surface structure,
  rendering/history code, interface joins, fixture ownership and relevant suites.
- Loaded the current tree successfully through the owning parser and inspected
  the six interface associations and surface-level support owners. Found 14
  reachable annotated release tags; historical derivation was not run here.
- Listed the `source_drift` selection through the dispatcher. No test suite,
  live specimen, signed build or implementation acceptance was run for this
  planning-only change.

Implementation has not started. Next action: reconcile against the current
checkout and capture the baseline and destination inventory in step 1.

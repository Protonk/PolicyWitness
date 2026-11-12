# Controller authority and CONTROLLER.md integration plan

This plan establishes `docs/CONTROLLER.md` as an explanatory peer of
[WORKER.md](../docs/WORKER.md), and uses the authored public contract to examine
the authority assigned to the controller. Its implementation baseline is
**unset**. Set it only after the CLI example work's contractual
changes and reductions are settled, using the entry gate below.

The controller is PolicyWitness's control plane: it admits and prepares work,
selects and directs the execution apparatus, governs invocation, evaluates
received evidence, and accounts for what it can and cannot establish. The
runner is an instrument under that control with responsibilities and behavior
of its own. This framing identifies the subject of investigation; it does not
assign every decision to Rust or imply that directing an operation establishes
its execution or effect.

The intended result is an allocation of authority that is correct, coherent
and supported in the contract, implementation and architectural account. An
obligation may stay, move, split, become more precise or disappear. Missing
distinctions may require new obligations. Neither contraction nor expansion is
a success criterion. Existing mechanisms may be appropriately placed.

## 1. Scope and planning basis

Read the root [CONTRIBUTING.md](../CONTRIBUTING.md) in full, then the [root](../AGENTS.md),
[controller](AGENTS.md), [docs](../docs/AGENTS.md),
[contract](../docs/contract/AGENTS.md) and [tests](../tests/AGENTS.md) guidance.
Read [runner guidance](../runner/AGENTS.md) before inspecting its implementation
or exercising native helpers. Follow additional directory guidance where work
lands. These rules apply to every agent, including evidence retention and
checkout locking.

This plan expects the completed design in the
[CLI example plan](../docs/CONTRACT-EXAMPLE-PLAN.md), as read at `a7b78957`.
That identifies the dependency's design, **not** an implementation baseline or
execution evidence. The coordinator must inspect the actual completed code,
contract and results at the entry gate. The source routes below are starting
points to recheck, not findings about the future implementation.

Useful entry points, without adjudicating their allocation:

| Starting evidence | Why the investigation needs it |
| --- | --- |
| [Contract authoring model](../docs/contract/README.md) | Context is inherited; `who` can name several components; relationships and public prose carry obligations. The generated controller-finding index selects checks and is not a complete controller inventory. |
| [Component definitions](../docs/contract/00-identity.surface.md) and the request, transport, reply, envelope, diagnostics, dossier and installation surfaces | Authority crosses surfaces. Field meanings, definitions and shared rules matter as well as rules explicitly naming the controller. |
| [Run orchestration](src/run_flow.rs), [request preparation](src/request_patch.rs), [selection](src/runner_select.rs) and [augments](src/augments.rs) | Existing seams expose preparation, a held serialization, selection, invocation and fallback compilation. Their assertions need reachability and independence review. |
| [Client admission](src/runner_client.rs), [typed admission and projection](src/porcelain_admission.rs) and [envelope assembly](src/json_contract.rs) | Receiving bytes, admitting a producer, accepting a record and publishing an interpretation are distinct operations. |
| [Runner commands](src/runner_commands.rs) and [registry management](src/runner_manager.rs) | Installation, selection, inspection, ownership and cleanup extend the controller account beyond `run`. |
| [Unit suite](../tests/suites/unit/README.md), [failure boundaries](../tests/suites/failure_boundaries/README.md), [blackbox consumer controls](../tests/suites/blackbox_e2e/README.md) and [BYOXPC controls](../tests/suites/runner_byoxpc/README.md) | Existing tests cover different layers; an assertion on a constructed reply is not a measurement of its producer. |
| [WORKER.md](../docs/WORKER.md) and [ARCHITECTURE.md](../docs/ARCHITECTURE.md) | These connect resources, lifetimes, boundaries, observations and limitations to sources and scoped checks. Their prose is evidence to review, not an oracle for the new account. |

Inspect the actual files and symbols again at execution. For example, the
current contract's questions about success in the presence of integrity
findings, withholding scope, degraded associations and classifier ownership
are investigation inputs, not decisions this plan resolves. Read their
surviving nodes and any settled CLI decisions; do not resurrect deleted
obligations from this planning snapshot. The CLI consumer's new result rule
checks the current outcome mapping. It does not settle whether integrity
findings should change command success; that remains a separate question if
the settled contract still leaves it open.

This work may change controller code, cooperating components, public meanings,
tests and explanatory documentation when justified. It does not authorize a
generic runner factory, a plugin framework, interchangeable-runner protocols,
speculative backends or a general controller framework. Use PolicyWitness's
actual built-in and external-runner arrangements. Tagging, notarization,
publication and unrelated release preparation are outside this plan.

### Expected CLI completion and settled constraints

The completed CLI work is expected to establish the following arrangement.
Treat the CLI plan's settled principles as design constraints; do not reopen
them merely to simplify this investigation.

| Area | Expected arrangement and its limit |
| --- | --- |
| Definition and presentation | `controller/src/example.rs` owns one handwritten `EXAMPLE_DOCUMENT` constant. `request.specimen.example` cites it through the `document` fact; the contract extracts its rendering and parsed public payload. There is no generated Rust example source or path from documentation into shipped code. The contract remains normative for public meanings. |
| Public entrance | `policy-witness example` takes no arguments and originates an input for `run`. Successful emission promises a document the same build admits. Contents, layout and labels have no stability promise between builds; successful native execution is not part of that emission guarantee. |
| Admission | The controller gates identity and prepares controller-owned options; the Swift host owns request grammar admission. `run` remains the way to ask whether a caller's specimen is accepted. Add no admission query, validation mode, dry run or alternative submission route. |
| Publication | The command prepares and gates the document before output, writes it with one framing LF and explicitly flushes. Any emission failure is exit 2 and requires discarding stdout, even when it parses as a complete document. Stderr explains the failure to a person and supplies no classification interface. |
| Testing and interpretation | The live round-trip case gets its specimen from the app, perturbs it before submission, observes the machine beside execution and uses existing readers afterward. It does not author a specimen or add a fourth interpreter. Constructed documents remain legitimate inputs to offline checker controls. |
| Scope | The command is public and currently intended for project verification. Usage and the contract disclose it; user-guide presentation is deferred. `runner verify` retains its separate apply-only purpose. Neither sharing its storage nor introducing named examples is required here. |

The controller therefore originates some inputs as well as admitting caller
inputs. Its self-gate establishes only the checks it performs; host admission
comes from executing `run`. A's inventory should preserve that distinction
without treating the rendered example's particular target or labels as stable
public obligations. The paired/read-only purpose and native expectations belong
to the current test, separately from the narrow public emission promise.

## 2. Entry gate: a settled CLI contract baseline

### Work that can proceed before the gate

The coordinator can prepare role packets, artifact templates, the delegation
ledger, candidate boundary questions and an equipment/test inventory. It can
inspect current code and documentation for navigation, labeling observations
provisional. It can arrange isolated workspaces and determine how evidence
will be retained. Do not finalize obligation IDs, the desired allocation,
refactors, normative text, a controller diagram or an implementation patch
against the unsettled tree. The independent investigations in section 4 begin
after the gate so they examine the same settled subject.

### Evidence required to open the gate

The coordinator writes `records/controller-authority/BASELINE.md` with:

1. The actual CLI work's disposition: the final plan, recorded decisions for
   the distinctions it leaves to confirm before step 1, the maintainer's step 3
   evaluation decision, and the commits settling contractual changes,
   reductions and step 4 support. Do not ask again about its settled principles
   or commitments already confirmed. Inspect the evaluation record and its
   later entries, not just the initial acceptance decision.
   If work was revised, replaced or stopped, record the maintainer's explicit
   disposition and the resulting retained behavior instead of requiring the
   original design to exist.
2. The final authored surfaces, generated public snapshot and relevant output
   artifacts. Inspect `example.rs`, `request.specimen.emit_example`, the example's
   `document` citation, extraction validation, declared generator inputs and
   support. Review deletions and shared/inherited effects elsewhere in the
   contract. Check stale-rendering refusals and the example edit's effects on
   rendering, the request surface and build identity. No open CLI decision may
   still change an inventoried obligation or boundary. Identify unrelated
   release tasks that may remain open.
3. The signed-app evidence from `witness_contract/example_round_trip`: emitted
   and submitted bytes, version and property-list identities, run and perturbed
   `run` captures, target observations and assertion results. Inspect
   `example_round_trip_controls` for independently expected and actual diagnostic
   sets, identifiers that earned coverage and documented exceptions. Include
   cross-build refusals and usage checks. An executed control or generic
   rejection is not verified assertion coverage.
4. The exact preparation and publication controls: the emitted file passes
   through actual `run` preparation under `test:policy-witness` and its document
   without the framing LF equals the captured client callback string. Record
   this scope separately from the signed app's delivery-length observation.
   Read the renderer, gate, short-write, partial-failure and explicit-flush
   controls; do not infer a built-app parse/gate failure from a unit control.
5. The shared consumer's new admitted reply-to-envelope result rule and
   `blackbox_e2e/checker_controls`, including admission applicability, field
   types, missing fields, independent and combined faults and preserved refusal
   boundaries. Review changes to `envelope_skeleton` and its callers: distinguish
   corrected accidental mismatches from deliberate result faults. Inspect the
   complete default battery required before the CLI evaluation, since this rule
   reaches readers outside the two new cases. Re-discover the caller inventory
   rather than assuming the planning-time count remains correct.
6. The bounded ten-run evaluation sample, every failed assertion's disposition
   under the CLI plan's section 4.6, and subsequent corrective/replacement runs.
   Ten identical or consecutive passes are not required. Read candidate-stage
   dispositions appended to the same record if that verification has run; a
   later pass or a new build identity is not itself a disposition. Outstanding
   objections relevant to this baseline keep the gate closed.
7. An exact commit and worktree state for investigation, relevant annotated
   tags, generator checks, public build contract, wire and worker identities,
   and the selected app's provenance if execution is credited. Require a clean
   source snapshot for shared investigation; record later evidence-record
   commits separately. Record environment and unavailable equipment explicitly.

Tie each result to its source, tests, fixtures and selected app; the evaluation's
original build is not automatically the final supported build. Missing
development artifacts are missing evidence. Rerun applicable checks or obtain
an explicit disposition of the unsupported claim; do not recreate successful
historical credit. Use actual case and node names if an accepted implementation
deviation changed them, and record why the deviation fits the settled design.

Check the actual release/stamp state. A prepared, untagged tree may intentionally
refuse ordinary generation or a build. Do not manufacture a tag, bypass history
checks or overwrite the prepared stamp state to force admission. Use the settled
project's supported development-state procedure in an isolated branch/worktree
if needed, record the exact stamp-only transition, and establish that it leaves
the investigated public meanings intact. Preserve the prepared release tree. If the supported
transition is unclear, settle it with the maintainer before dependent builds.

The gate requires settled contractual work and applicable evidence, not release
publication or an unrelated expensive rehearsal. The pre-evaluation default
battery is relevant because the consumer changed; later release-form credit
comes from the CLI plan's candidate rehearsal and is not supplied by a
development run. Do not require candidate completion just to open this gate,
or credit candidate results before they exist. If the CLI project requires
an evaluation decision and none exists, keep the gate closed. The coordinator
may determine readiness from recorded decisions and evidence without asking
for their confirmation again. Record which pending matters are unrelated.

Once open, all investigators receive the same source snapshot. A subsequent
change affecting their inputs closes the affected part of the gate: record the
delta, assess applicability and refresh the affected independent report before
adjudicating it. Do not silently rebase an inventory onto new obligations.

## 3. Coordination, artifacts and independence

One coordinating agent owns the baseline, scheduling, evidence register,
adjudication records, implementation integration and final acceptance package.
It does not supply a preferred allocation to the initial readers. The four
principal assignments below are substantial Astra/Fable-class investigations;
use that capability class for their initial work and returning reviews. Where
available, `gpt-6-astra` is a suitable concrete selection. Record the actual
model and context packet; if the requested class is unavailable, arrange an
equivalent with the maintainer rather than silently reducing the assignment.

Create fresh initial contexts (`fork_turns="none"` where supported), with this
plan, applicable working guidance, the settled baseline identity and each
role's allowed packet. Do not inherit the coordinator's hypotheses or another
role's transcript. Required repository guidance and READMEs remain available;
readers record exposure to their architectural summaries and treat them as
navigation, not established conclusions. The separation below is a reading
protocol, not a claim of filesystem access isolation.

Use `records/controller-authority/` for planning and acceptance records, under
[records guidance](../records/AGENTS.md). Suggested artifacts are:

| Artifact | Owner and purpose |
| --- | --- |
| `BASELINE.md`, `DISPATCH.md`, `EVIDENCE.md` | Coordinator: entry decision, agent packets/budget and evidence with provenance, scope and availability. |
| `A-CONTRACT-INITIAL.md`, `B-IMPLEMENTATION-INITIAL.md`, `C-BOUNDARIES-INITIAL.md` | Original investigators: independently authored findings, counterevidence and unresolved questions. |
| `INITIAL-FREEZE.md` | Coordinator: file hashes, source snapshot, packet/exposure inventory and the commit freezing all three reports. |
| `CROSS-EXAMINATION.md`, `DECISIONS.md` | Questions, responses, competing readings and explicit decisions with their authority. |
| `INTEGRATION.md`, `VERIFICATION.md` | D and coordinator: claim/obligation/code/test crosswalk, implementation slices and results. |
| `A-REVIEW.md`, `B-REVIEW.md`, `C-REVIEW.md`, `ACCEPTANCE.md` | Returning investigators and coordinator: integrated reviews, dispositions and remaining limits. |

These names are destinations to create during execution, not reports produced
by this plan. Raw execution evidence stays in dispatcher-owned run output;
records cite it with its local/disposable availability and reproduction route.
Do not copy protected evidence into records to evade retention. Permanent
documentation links to contract nodes, sources and checks, not these temporary
records. Retire planning records with the plan after acceptance under repository
practice; git retains the decisions.

Run A, B and C independently before starting D. Give each only its own writable
report destination; keep production sources unchanged. They may request narrow
experiments through the coordinator. Do not circulate interim reports, offer
one reader another's question as a finding, or summarize emerging agreement.
Each completes its report and identifies its limits before seeing the others.
Freeze all three in one reviewed commit with hashes. Corrections and subsequent
opinions are appendices/new records; never rewrite the frozen artifacts to
erase a disagreement.

With four concurrent slots, the coordinator plus A/B/C fills the capacity.
Queue minor work or run it while a principal is inactive; run D after their
initial turns finish. Reuse the original investigator contexts for subsequent
tasks. If a context cannot be resumed, give its replacement the original packet
and frozen artifact before the integrated material, record the substitution,
and preserve the initial perspective. Additional minor tasks are centrally
budgeted; principals may request them but may not spawn unrecorded helpers.
For the returning reviews, keep D inactive while A/B/C run, or stagger the
reviews within the available slots. Slot availability changes scheduling, not
the required independence or scope of a role.

## 4. Principal roles and initial assignments

### A. Contractual Authority Reader

**Initial materials:** the settled authored surface tree, its authoring model
and imported record declarations, generated views for navigation, and common
working guidance. Support citations can identify claimed evidence, but do not
open the cited production code or test assertions during this first pass. Do
not use the module map or B's future reconstruction as the inventory outline.

Recover controller obligations across all surfaces, including inherited
context, shared definitions, actor lists, reference relationships, subordinate
conditions/effects and normative prose. Separate acting components from
`owner` support nodes: a support owner/grade does not assign runtime authority.
Follow `who`, `where`, `entry`, `recipient`, `report`, `when`, `requires`,
`uses`, order relationships and failure consequences. A child replacing `who`
is not an additive inheritance. Include obligations expressed as field meanings
or system-wide guarantees; do not limit the search to the controller index or
the literal word "controller".

Produce an inventory with stable local obligation IDs and exact authored node
IDs/paths. For each obligation record effective context and its derivation,
applicability, beneficiary, prerequisite information/authority, action and
failure obligation, shared dependencies and support claimed by the tree.
Distinguish actions, admissions, decisions, observations, interpretations,
preservation and publication; an obligation may span more than one category.
Identify overlaps, ambiguous subjects, inherited promises and absence of an
express assignment.

For the imported example, inventory the normative emission promise separately
from the example's contents and the checks supporting it. The app's authority
over its example does not make every implementation choice a public promise,
or transfer ownership of the host's request grammar to the controller. Identify
the controller's publication obligation even though this command emits a bare
specimen and does not invoke the apparatus. Read its extracted presentation in
the contract; leave source realization to B until cross-examination.

Evaluate whether the declared component could fulfill the obligation given the
contract's stated capabilities and inputs. Mark implementation capability
unverified where it requires code or observation. Keep separate columns for
**current promise**, **unverified factual questions** and **proposed allocation**.
Inventory the whole scope before proposing reductions. State how completeness
was checked and which prose/references resisted a structured reading.

**Later responsibilities:** test B's claimed realization against the exact
promises; answer C's counterexamples; review final authored changes, inherited
effects, removals and new promises, generated views and the normative limits
described in `CONTROLLER.md`.

### B. Implementation Authority Reader

**Initial materials:** production code, build/source inventories, test code,
fixtures and retained execution evidence at the baseline, with component
READMEs for navigation. Do not read the authored contract or generated contract
as an architectural outline before freezing. When a required guide or fixture
exposes contract wording, record it rather than claiming complete blindness.

Trace the real routes from CLI entry through preparation, selection, invocation,
response admission, interpretation and output. Include usage/refusal paths,
actor and ordinary requests, version/example commands that actually exist,
fallback compilation and the separately dispatched registry commands. Follow
calls across Rust, the Swift client, the host, worker and validator where needed
to identify who decides or observes; source directory placement is not ownership.

Include the code-defined example and its path into the contract rendering,
identity inputs and emitted output. Trace rendering/gating before the first
write, completion of short writes, partial failure and explicit flush. Follow
the emitted input through actual preparation, distinguishing the unit test's
client callback capture from signed-app pipe-length evidence and host receipt.
Keep `runner verify`'s existing apply-only request separate; duplication alone
does not warrant unifying the two operations.

For each consequential decision, record inputs and when they are acquired,
mutation/serialization boundaries, resources held, lifetime, call/return and
failure paths, delegation, enforcement mechanism, observations retained and
public projection. Distinguish controller intent, client submission, host
admission, worker progress and externally observed effects. Track independent
compile checks separately from worker execution. Inspect tests for what they
actually exercise, not only their names or README claims.

Trace reply assessment, outer-result assembly and independent consumer reading
as separate operations. Inspect the shared result rule's admission boundary
and callers, including fixture corrections. The controller's clean assessment
of a reply does not independently validate the envelope it assembles afterward.
An independent reader's interpretation evidence likewise does not establish
that a native producer emitted its constructed input.

Produce a decision-and-authority account with source symbols and paths, state
transitions, resource/observation lifetimes and evidence grades. Separate what
the controller decides, directs, enforces, observes, infers and cannot establish.
Record ambient dependencies such as credentials, filesystem state, signing,
launchd, XPC and clocks. Propose questionable placements separately from the
descriptive account. No refactor is required to make this initial account tidy.

**Later responsibilities:** cross-check A's promises against actual paths and
reachability; independently inspect proposed owner changes; review the final
code and document for unsupported enforcement claims and regression in failure
handling, resource ownership or publication.

### C. Boundary Challenger

**Initial materials:** baseline identity, public entry points, test/fixture
catalogs and the following boundary questions. First write a scenario list
from inputs, possible outcomes and required observations. Then consult targeted
contract nodes and implementation to challenge each scenario. Both kinds of
source are allowed, but A/B artifacts and conclusions remain unavailable.

Start with these families; refine their premises against the settled tree:

| Family | Question to make concrete |
| --- | --- |
| Admission/preparation | Can an invalid contract, a shadowed selector, failed augment or changed file reach a later reader? Where does the example's self-gate stop and host admission begin? Which bytes were selected, and what distinguishes callback equality, pipe length and host receipt? |
| Uncertain invocation | Distinguish failure before submission, lost reservation reply, lost execution reply and lost helper capture. Who can prevent replay, and what remains unknown after a successful write or a deadline? |
| Rejected evidence | Can an unsupported producer, malformed/truncated frame or failed request delivery acquire semantic authority through a fallback or partial decoding? What exact bytes and diagnostics survive? |
| Contradictory/degraded reports | What follows from `finished` alongside an integrity finding, conflicting lifecycle evidence, an unassociated retained record or incomplete actor/phase evidence? Which conclusions must be withheld, and at what scope? |
| Result consistency | Can changing a result field disable the rule checking it? Does an admitted reply with an unrelated record error still expose a result mismatch, while a rejected reply's retained bytes supply no outcome mapping? Does a coherent native failure remain consistent despite nonzero process exit? |
| Effects without publications | Can an operation have happened without a usable result? Does the controller report uncertainty without asserting absence or reconstructing a missing worker observation? |
| Equipment and cleanup | Do selected paths, registry assertions, signing/entitlement read-back and observed running identities establish the same thing? Who may remove a service, and what does unknown cleanup permit? |
| Public output and helpers | What survives failed/truncated publication or controller interruption? Can complete-looking example stdout accompany exit 2 after a flush failure, and does the caller discard it? Does independent compilation, a log candidate or other secondary observation get mistaken for execution evidence? |

For each case identify who has the information, who can act, who can enforce,
who can draw the proposed conclusion and who owes the public guarantee. Include
one plausible challenge even where contract and code appear to agree. Seek a
discriminating small experiment or counterexample, not broad recommendations.
Report counterevidence and benign interpretations as well as suspected defects.

Use the CLI plan's failure dispositions, carried into section 10 below, when
interpreting its runs. Distinguish consistent inability to execute from a
defect or unresolved challenge to the native expectation. Do not demand hidden
OS causes where the specified disposition needs only a fresh qualifying run,
or treat later success as an explanation for an earlier discrepancy.

Produce a boundary challenge report with reproducer/fixture, actual boundary
reached, expected distinction, observations, alternative explanations and scope
limits. A constructed case can expose an interpretation defect without proving
native reachability. A source-only question remains a question. Do not install,
remove or perturb unowned external services for an experiment.

**Later responsibilities:** challenge the reconciled allocation, select
regression controls for consequential failures, and review the integrated
result for false certainty, lost evidence or promises its owner cannot enforce.

### D. Integration Editor

Start only after the three initial reports are frozen and their consequential
disagreements have received initial adjudication. Receive the originals,
cross-examination, decisions, evidence register and actual source tree, including
unresolved matters and maintainer dispositions.

Develop the coherent control-plane account, `docs/CONTROLLER.md`, the
claim/obligation/implementation/test crosswalk and proposed implementation
slices. Work jointly with the coordinator on contract and code changes. Every
documentary claim must either have scoped support, identify an admitted limit,
or create a concrete investigation/change task. An implementation mechanism
outside the adjudicated authority creates a candidate refactor, not an automatic
mandate to relocate it.

Keep originating the example, admitting its contract, submitting it for host
admission, interpreting returned evidence and completing public output distinct
in the account. Explain imported example content without turning it into a
second specimen definition or a stability promise. Preserve the evidence scopes
of the CLI work rather than making the narrative imply exact signed-app byte
delivery, successful execution from emission alone, or independent validation
of the outer result by the controller's own reply assessment.

D may resolve organization, wording and duplicate exposition within agreed
meanings. D may not silently choose between disputed owners, strengthen a
promise to make the prose flow, or remove a guarantee because it is difficult
to implement. Return those questions to the decision procedure. D responds to
all three returning reviews and makes the final account reflect their resolved
findings; the coordinator remains responsible for verification and completion.

## 5. Cross-examination and decision authority

After the freeze, release all three reports to A/B/C together. The coordinator
builds a comparison table linking A's obligations, B's decisions and C's cases.
Missing matches are findings, not rows to discard. Throughout the exchange keep
three answers distinct:

1. What does the current contract promise?
2. What does the present implementation establish, with what evidence?
3. What should the controller be responsible for?

Agreement on the first two never decides the third. For each consequential
disagreement, record the exact claim, competing readings, relevant evidence,
external consequence and the smallest observation that would distinguish the
accounts. Each reader responds from its original perspective and states what
would change its view. Prioritize responsibility for uncertain execution,
admission, withholding, preservation, ownership and cleanup over terminology.
Do not settle disagreements by majority vote, agent confidence or prose length.

Use a targeted experiment or a budgeted minor task when it can resolve a factual
question. Record an undecidable or unavailable observation honestly. The
coordinator may settle a factual reading from sources and applicable controls,
deduplicate equivalent inventory rows, select tests, and make routine local
refactors that preserve the adjudicated boundary and public meaning.

Maintainer judgment is required for intentional changes to a public obligation's
actor, scope, meaning or removal, even if output bytes stay the same; for new
public guarantees; and for unresolved choices about such matters as success
status, inference/withholding scope or cleanup authority. Evidence can expose
the choice but cannot supply product intent. Present a concrete decision packet
with proposed wording, affected nodes, current behavior, alternatives, user
consequences and verification. Prior recorded approval remains authorization;
do not ask again. While a decision is pending, continue unaffected work and
keep dependent claims/changes out of the accepted result.

Initial adjudication is complete when each disputed row is resolved with a
reason and decision owner, or explicitly pending with dependent work blocked.
D may integrate settled portions. It cannot present the allocation as complete
while consequential disputes remain unresolved.

## 6. Revising contractual ownership

Create a decision record for each proposed change, including a justified
decision to retain the current allocation. Group truly equivalent obligations
without losing their original node references. Each record contains:

| Field | Required account |
| --- | --- |
| Prior commitment | Exact nodes, effective inherited context, affected field meanings, recipient and applicability. |
| Present realization | Implementing path, information/resource holder, actual enforcement and public evidence; source and test limits. |
| Proposed disposition | Retain, clarify, consolidate, divide, transfer, remove or add; rationale and alternatives. |
| Responsible components | Who acts, who checks, who reports and who preserves failure evidence; required cooperation and ordering. Avoid an undifferentiated shared `who` that leaves no one accountable. |
| Observable consequence | Admission, invocation, effects, reporting, omissions, failure precedence, exit status and recovery before/after; include a contractual transfer even when these bytes are unchanged. |
| Contract edit | Authored nodes/relationships to change, shared-reference and inheritance effects, old-to-new mapping and deleted commitments. Separate runtime responsibility from support metadata. |
| Evidence obligation | Positive observation, negative control, actual owner exercised, interpretation checks and remaining uncertainties. |
| Disposition/authority | Decision, who may settle it, maintainer approval when required, affected implementation slices and reopening condition. |

Assign an obligation only where the component has the necessary information
and an effective mechanism to fulfill it. A delegation needs a cooperating
owner's obligation and an observation available to the delegator; the
controller cannot promise a native effect merely because it requested it.
Conversely, a host observation does not relieve the controller of an assigned
admission or publication responsibility. Preserve the distinction between a
producer's duty and a recipient's checks on the carried record.

Express decisions in the authored tree using its existing component definitions,
contexts, conditions, relationships and effects. Inspect both parent and child
context and all references when moving a node. Consolidation must preserve each
necessary applicability/failure distinction; removal needs a reason the public
commitment is unnecessary or intentionally withdrawn and an account of remaining
behavior. A broader rule is not equivalent merely because it is shorter.

Classify each slice separately as implementation reorganization with unchanged
commitments, correction of an inaccurate account, or intentional public change.
More than one classification can apply. Do not label an ownership transfer
"documentation only" because JSON shape did not change. Record unchanged
behavior through path/effect/preservation checks, not compilation or golden
agreement alone. Keep contract changes and the supporting implementation/test
changes reviewable together while separating unrelated refactors.

Use existing structured authoring forms where they express the distinction.
Do not expand the contract language or raise the `free.*` baseline to force a
preferred allocation through the generator. If required meaning cannot be
expressed, show the concrete missing distinction and obtain a scoped decision
on authoring support. A restraint on free-text growth is not a target to reduce
public obligations. Preserve historical snapshots and readers.

## 7. Minor-agent budget and dispatch strategy

Allow **up to sixteen** smaller assignments, using Sol/Opus-class agents
(for example `gpt-6.1-sol` where available). This is a ceiling, not a target.
Initially allow up to eight before documentary integration and reserve eight
for integration surprises, mutations and returning reviews. The coordinator
may reallocate unused capacity with a recorded reason, without exceeding sixteen.
Principal investigations and their returning reviews are the four principal
roles, not minor assignments. Every additional bounded assignment, including a
replacement minor investigator, consumes a minor slot; clarification within
the same question does not. No uncounted recursive delegation.

`DISPATCH.md` records task number, question, trigger, parent decision, initial
materials, output, slot consumed and independent checker. Dispatch only if a
narrow answer could change a decision or its evidence credit. The coordinator
can answer a trivial question directly. Do not spend slots on broad duplicate
architectural reviews or prescheduled tasks whose uncertainty has disappeared.

The following are opportunities, not sixteen mandatory tasks:

| Dispatch point and trigger | Bounded assignment and required evidence | Independent check/integration |
| --- | --- | --- |
| Initial evidence review: a contractual assertion rests on a generated expectation or shared classifier | **Oracle-independence audit.** Trace one test's expected and actual values through definitions, generators, fixtures, codecs and production functions. Return a dependency sketch, the common failure that could pass, and a discriminating control with independent expected diagnostics. Distinguish valid identity/echo expectations derived from the emitted input from independent claims about its adequacy or native execution. | Coordinator or another principal checks dataflow and control diagnostics. Keep interpretive rules in their existing owners and credit only the asserted relationship, not the entire suite. |
| Initial evidence review: a fixture or mocked seam claims coverage of a production boundary | **Fixture and seam audit.** Trace public entry to the exact exercised symbol, replacements and bypassed gates. Return fixture/source/build identities, boundary reached and a mutation that should break the assertion. For example preparation, distinguish the test-identity callback capture from signed-app delivery-length evidence. | B checks reachability; C verifies the intended assertion/classification fails, rather than compilation, equipment or an earlier gate. A generic consumer rejection cannot stand in for a targeted identity failure. |
| Baseline review: the shared consumer change affects older constructed envelopes | Audit one group of reader callers and their fixture corrections. Identify accidental result incoherence, deliberately faulted results and the assertion preserved by each change; inspect whether the reader normalizes or repairs an input it should reject. | B reviews actual call paths and the coordinator replays valid, invalid and combined controls. Fixture repair cannot narrow rule applicability or erase deliberate fault coverage. |
| A/B cross-examination: a shared or inherited obligation has conflicting readings | Expand one effective context/reference chain and its failure effects; return exact node paths and before/after applicability for a proposed move. | A manually checks the expansion against authored parents and references; the coordinator compares it with the generator's view. |
| Adjudication: one responsibility seems to cross several owners | Trace one obligation through producer, transport, admission, consumer and public projection, including dropped or retained evidence. | A checks the promise, B checks calls/fields and C supplies a missing/contradictory-record control. |
| Adjudication: validators nominally enforce the same rule | Compare one requirement across host, controller and independent consumer. Return a common hand-authored valid/invalid corpus, each result, and legitimate entry/applicability differences. Use constructed inputs to test readers without introducing a public admission query or a second specimen in the live example case. | A decides whether requirements really are identical; B verifies the corpus reaches each validator. Agreement is insufficient if all share their expected values. |
| Before refactoring: invocation uncertainty would change the proposed owner | Reproduce one lost-reply/delivery boundary using an existing seam, independent invocation count/effect and retained bytes. | C checks competing explanations; coordinator reruns the discriminating arrangement and records fixture timing/observability limits. |
| Before refactoring: selection or cleanup evidence is ambiguous | Examine one identity/read-back/ownership transition or one unknown-versus-absent cleanup case. Return exact inputs, durable ownership and native or constructed observations. | B checks the responsible implementation; coordinator verifies cleanup through existing recovery tools. No prefix-based ownership inference. |
| Implementation slice: a source-to-test citation may be decorative | Damage the cited relationship in an isolated copy and show whether its claimed case detects it. Return the minimal diff, passing baseline, expected and actual diagnostic sets, targeted assertion and restoration. | Coordinator confirms the mutation reached the boundary and earned targeted coverage. A wrong-reason rejection is a coverage failure. Revise the claim or test before crediting the slice. |
| D's integration: a diagram/document claim lacks a resource or lifetime owner | Check one resource, state transition or retained observation from acquisition to publication and cleanup. Return source, measurement if available, and explicit unobserved intervals. | B reviews the path; D narrows the prose or adds the justified implementation task. |
| Returning review: a newly combined failure loses a prior guarantee | Supply one combined-fault or reordered-evidence regression, preserving independent expectations for both failures. | Original challenger reviews diagnostics and preservation; coordinator reruns baseline, damaged and restored variants. |

Evaluate oracle independence and fixture reachability early for every decisive
test relied on by the allocation. Prefer the first two delegations when these
remain uncertain; do not treat their names as proof of the whole test system.
During the initial independent phase, minor results go only to the requesting
role and coordinator and are listed in its frozen exposure record. Shared
findings are released at cross-examination. Later assignments may use all
adjudicated materials. Reserve remaining slots for disagreements D actually
discovers.

Cross-role checks in the table happen after the freeze. Before it, the
coordinator checks a returned minor result independently or leaves its credit
pending; it does not break the initial separation to obtain a second opinion.

Every minor report returns a bounded finding, minimal reproducible inputs,
command/configuration, source/build and fixture identity, raw evidence location,
expected/observed result, alternative explanations and limits. It does not make
architectural policy. If the budget is exhausted, the coordinator performs
necessary work itself or stops the dependent decision; exhaustion is not
evidence and does not waive verification.

## 8. What CONTROLLER.md must explain

The destination is `docs/CONTROLLER.md`, alongside `docs/WORKER.md`. Organize it
by meaningful control responsibilities, not Rust modules or envelope nesting.
A competent reader should be able to locate authority, follow a consequential
decision, identify its supporting observation, and understand what happens when
the operation or its result cannot be established.

The following outline is a starting structure for D; change it to fit the
adjudicated account without losing these questions:

1. **Authority and limits.** How caller requests, CLI/configuration, packaged
   identity, selected equipment and operating-system credentials authorize or
   constrain action. Distinguish product responsibility from OS privilege.
2. **Originating, admitting and preparing work.** The code-defined example,
   its narrow same-build admission promise and its extracted contract account;
   refusal order, selected policy and augments, held bytes, dossiers and read
   dependencies. Distinguish the controller gate from the host's grammar and
   retain direct XPC callers' and standalone helpers' separate boundaries.
3. **Selecting and directing the apparatus.** What is selected, checked and
   delegated; how control passes to the client and host; why worker/validator
   responsibilities remain with them. Explain the example/version paths
   without implying that they invoke the apparatus or execute a specimen.
4. **Invocation and uncertainty.** Reservation, submission, deadlines and
   terminal states; acquisition retry versus execution replay; what receipt,
   completion and loss do and do not establish.
5. **Receiving, evaluating, preserving and publishing evidence.** Transport/producer
   admission, native observations versus host claims and controller inference,
   association, contradictory/degraded results, withholding and fallback
   compilation. Separate reply assessment, outer-result assembly and independent
   reading. Explain output completion, partial writes and flush failures;
   complete-looking example stdout is unusable on exit 2. Do not turn stderr
   wording into a machine-readable contract.
6. **Equipment administration and recovery.** Registry authority, lock and
   durable state ownership, signing/read-back, launchd actions, inspection and
   observed absence. Distinguish these commands from per-specimen execution.
7. **Resources, lifetimes and external dependencies.** Request and reply buffers,
   retained opaque bytes, metadata snapshots, client pipes/process ownership,
   clocks, output streams, registry locks and recovery records. Identify what
   remains held across invocation/failure and what persists beyond controller
   exit; do not invent controller ownership of host mappings or worker resources.
8. **Changes that alter what can be promised; known gaps.** Explain consequential
   limits beside their claims and end with an index of admitted gaps, following
   the peer tours. Separate a measurement gap from a fundamental information
   boundary and a product decision still pending.

Use concrete paths through success, early refusal and uncertain/degraded
completion. Include a small state/control diagram if it clarifies when authority
or evidence changes hands, and a resource/observation table when prose obscures
ownership or lifetime. A diagram edge labeled "observe" must not look like a
guarantee of enforcement. State source-only, constructed and native support
separately; copy no evidence credit from WORKER.md without checking applicability.
Explain the controlled preparation test's exact-byte claim and the signed
app's length-only observation at their respective boundaries. Their difference
is a limit of current evidence, not an automatic task to add production capture.

The authored contract remains normative for public meanings. The new tour
explains their realization and dependencies, links to their nodes and supporting
symbols/checks, and avoids becoming a second field dictionary. Keep CLI usage
and the module map in [controller/README.md](README.md), workflows in the user
guide and working rules in AGENTS files. Update inbound navigation in the root
README, controller README and architecture/worker tours where useful; preserve
anchors or update callers. Keep example workflow presentation out of the user
guide while the settled CLI scope defers it. The tour may explain this public
command's control responsibilities without expanding its audience or promises.

For a generated representation, extend [architecture.json](../docs/architecture.json)
and [generate_architecture.py](../docs/generate_architecture.py), rather than
creating a parallel generator. At the planning snapshot `SPAN_DOCUMENTS`
registers only ARCHITECTURE and WORKER; a new generated destination needs
registration, output/input ownership, graph routing and stale-copy controls in
[architecture tests](../tests/suites/source_drift/architecture.py) and the
[generator inventory](../tests/suites/source_drift/generators.py). Extend the
known-gap index's document inventory and controls in the source-drift checker
for the new peer. Review generated SVG/tables as well as source. Citation and
stamp checks establish consistency, not whether an arrow or claim is true.
An authored conceptual diagram may be sufficient; D chooses after the account
is settled and records its verification ownership in either case.

## 9. Implementation sequence

| Stage | Work and exit condition |
| --- | --- |
| 0. Prepare and admit the baseline | Complete section 2. No dependent investigation starts against unsettled CLI meanings. |
| 1. Independent investigation | A/B/C complete bounded but substantial reports and evidence registers. Resolve missing factual inputs with small experiments where useful. Freeze the originals before sharing. |
| 2. Cross-examine and adjudicate | Compare all three questions, run discriminating controls, record disagreements and decisions. Obtain required maintainer judgments on concrete alternatives. Exit with settled rows and explicitly blocked dependencies. |
| 3. Make architectural decisions reviewable | D drafts the authority narrative and crosswalk; coordinator defines implementation slices using section 6 records. Before larger refactors, characterize the affected current behavior through existing seams and independent checks. A failing premise reopens its decision. |
| 4. Implement by obligation/boundary | For each settled slice, establish baseline observations, change actual owner/cooperation, update authored meanings and readers together, and verify the new behavior or preservation claim. Update D's document with the same slice. Avoid a broad module rewrite before its authority decisions. |
| 5. Integrate the account | Complete CONTROLLER.md, navigation, diagrams if justified, support and suite accounts. Review shared/inherited obligations and all affected projections together. Reconcile D's crosswalk against actual final code rather than the proposed design. |
| 6. Return to the investigators | A reviews current promises and transfers; B follows final code and lifetime paths; C repeats the boundary challenges and examines new combined cases. Each receives the full diff, originals, decisions and evidence. Record disagreements separately; fixes reopen affected slices and require focused re-review. |
| 7. Verify and accept | Run final applicable checks on final dependencies/build, close the decision/coverage ledger and present the acceptance packet. No remaining consequential dispute may be hidden as a documentation gap. |

Prefer a small experiment before moving a mechanism when the answer depends on
an uncertain failure boundary. For example, a controlled reply can distinguish
admission from interpretation, while a lost-execution-reply case needs an
independent invocation/effect observation to address replay. Exercise the
existing seam first; add one only if the required boundary cannot otherwise be
reached, and document what that seam substitutes. Experiments can show that a
refactor is unnecessary. Keep that conclusion and its evidence.

Only one agent writes a given production file at a time. Schedule build/test
execution through the checkout lock, or use separate worktrees with distinct
output/intermediates. A shared writable directory is not isolation. Do not
unlink locks or mutate the app under inspection. Use fixture-owned disposable
copies for deliberate damage and retain their exact patches and provenance.

## 10. Verification and public-change accounting

For every accepted obligation maintain a row connecting contract node and
effective scope, responsible implementation, document claim, check/assertion,
independent expected value, rejected control and evidence limit. Removed or
transferred obligations retain a before/after row explaining the decision and
how the new owner is exercised. A coverage count cannot substitute for these
relationships.

Distinguish three evidence classes in every report:

| Class | What it can establish | What it cannot establish alone |
| --- | --- | --- |
| Structural agreement | Authored-tree validity, references, shapes, generated freshness, source inventories, citation existence and identity inputs. | Correct allocation, runtime reachability, effects or behavioral equivalence. |
| Constructed-input checks | Admission, interpretation, failure precedence, association and preservation for supplied inputs; sensitivity to deliberately damaged relationships. | That the native producer emits the input or that its claimed effect occurred. |
| Native execution | The observed execution/effects and evidence flow for a particular build, platform, fixture and prerequisites. | Universal behavior, private kernel state, or an unobserved cause inferred from a return code. |

For a new or changed consequential assertion use an independently authored
expected relationship, a passing control, a one-change violation and restoration.
The damaged case must reach the intended boundary and fail the relevant
assertion. A build error, missing equipment, earlier refusal or unused mutation
is not a negative control. Include combined faults where one error might mask
another and state legitimate masking/precedence explicitly. For an unchanged
claim, review applicability of existing controls before adding duplicates.

For checker controls, independently specify the expected assertion identifiers
and classifications, including necessary consequences of a logical fault.
Match expected and actual sets before crediting a targeted assertion. Carry
forward the CLI plan's specific allowance for the aggregate
`(consumer_validation, consistency)` diagnostic: retain all underlying errors,
require the aggregate in its dedicated propagation control, and earn no coverage
from its incidental presence in another control. It is not permission to ignore
other unexpected diagnostics. Completeness counts identifiers with matched
targeted controls or documented other evidence, not registered tests.
Check combined faults and unevaluated groups explicitly. In particular, failed
emission prevents submission even if stdout parses; it cannot create an
execution-unavailable claim about a run never attempted.

An oracle audit follows expected values to their origin. Sharing a structural
codec or shape inventory may be appropriate; deriving both expected semantics
and actual classification from the same rule cannot independently establish
that rule. Compare hand-authored cases and independent file/process/native
observations where available. Likewise, matching declarations linking a source
and case do not show that the case exercises the source. Confirm this with
reachability evidence and meaningful damage to the asserted relationship.

Apply that audit without creating a second definition of the example or a
fourth interpreter. Identity, digest and echo expectations taken from the
emitted document establish relationships to that input; independently pinned
paired/read-only bounds, refused neighbors and native expectations establish
different things. Ordering, vocabulary and outcome mapping stay with their
existing readers and controls. The live example case supplies no specimen of
its own, while constructed inputs remain appropriate for testing those readers
and the offline checker. A missing interpretive check belongs in its owning
reader, with independent controls, rather than a duplicate rule in the example
checker.

For the shared result rule, establish applicability from version, transport
and reply-admission evidence, independently of the three result fields being
checked. An admitted reply maps its outcome to `result.normalized_outcome`,
`result.ok` (true exactly for `finished`) and `result.exit_code` (0 for
`finished`, 1 otherwise). Missing/null/wrongly typed fields fail; booleans and
integers are distinct. An unrelated record error in an admitted reply must not
hide a result mismatch. A reply refused for compiled-profile context, an absent
reply or a rejected client capture must not acquire this mapping from retained
bytes. Keep process-exit comparison separate: the case observes the actual
exit, while the consumer checks the reported relationship. Review fixture
corrections and deliberate faults without normalizing input in the consumer.

For the example's exact-byte claim, retain the unit-test input and callback
comparison through actual preparation under the test identity. Rendering a
development or release identity does not extend that observation to a signed
binary. On the signed app, `bytes_written` observes bytes accepted by the client
stdin pipe, not their contents or host receipt. Preserve both evidence scopes;
do not require a production capture field merely to make them coincide.

Use the settled catalog, not names assumed from this plan. Inspect selections
with `tests/run.sh --all --list` or the relevant selector plus `--list`, then
run through `tests/run.sh` with fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>`.
The likely verification routes are:

| Changed boundary | Required selection/account |
| --- | --- |
| Controller orchestration, preparation or selection | `unit`, applicable `integration/cli.integration`, and public-run controls establishing held inputs, refusal order and invocation count. Include ordinary and actor paths when both consume the changed mechanism. |
| Example definition, emission or its extracted account | Renderer/gate/write/flush and exact-preparation controls in `unit`, signed usage and cross-build checks in `integration/cli.integration`, `witness_contract/example_round_trip` and `example_round_trip_controls`, plus extraction/stale-output/identity checks in `source_drift`. Preserve the distinction between the controlled and signed boundaries. |
| Admission, evidence interpretation or validator receiver | Follow the coordinated selection in tests/AGENTS: `failure_boundaries`, `runner_unit`, `runner_abi_layout`, `runner_c_worker_harness`, `unit`, plus applicable `runner_validator_failure`, `blackbox_e2e` and `witness_contract` assertions. Trace all readers, not only Rust. |
| Shared consumer result mapping or fixture coherence | `blackbox_e2e/checker_controls`, the affected caller controls and a complete default battery against the applicable app. Inspect the actual callers, incidental fixture corrections and preserved deliberate faults; the example cases alone do not establish the shared rule's reach. |
| Reservation, submission, uncertain invocation or capture | Applicable client/host controls and `runner_byoxpc/reservation_controls`; see [change verification](../tests/CHANGE-VERIFICATION.md#byoxpc-reservation-and-lost-reply-controls). Retain independent invocation/effect observations and raw received bytes. |
| Registry, selection equipment, installation or cleanup | Applicable selection/registry unit controls and BYOXPC recovery, entitlement, ownership and cleanup cases from the settled catalog and change guide. Observe actual owners; unknown inspection is not absence. |
| Public output or interrupted preservation | Relevant CLI, consumer and public-output interruption controls, including failures after execution but before a complete public report. |
| Contract, generated material or documentation | `source_drift`, tree/history/shape checks and generator controls; behavioral checks remain required where a meaning changes. |

Rerun `witness_contract/order_barrier_mutations` if the worker wait, release
store or eligibility rule changes. If untouched, record a reviewed applicability
judgment rather than calling a byte comparison proof. Apply other conditional
checks in [CHANGE-VERIFICATION.md](../tests/CHANGE-VERIFICATION.md), including
build refusal controls when build/generator gates change and limit checks when
limits change. Do not blindly run every opt-in or remove a required case to
obtain a pass.

Edit generator inputs and regenerate with the owning tool. Run contract tree
and history checks in the admitted stamp state, review `public.json` changes,
affected surface histories, relationships and field presence/type joins. Refresh
shape goldens only for intentional shape changes. Regenerate porcelain codecs,
worker identity or layout artifacts when their inputs change, reviewing both
producer and consumer changes and C/Swift agreement. Keep `docs/build.json`
aligned if build behavior changes. Process/channel/boundary changes update
`docs/architecture.json` and its generated account.

Record build contract, worker and wire identities before and after each relevant
slice and explain differences from actual input sets. The handwritten
`controller/src/example.rs` is already a development-digest input through its
path and suffix. Its parsed document enters the request surface's public
payload. A content change can move both accounts after regeneration; a source
formatting change can move the digest without changing that payload. Contract
prose and support do not feed shipped example code or its development digest;
support metadata also stays outside the public payload. Release-form identity
still depends on the tagged source and clean-checkout conditions. Verify these
distinctions from actual input sets, stale-output controls and reviewed diffs;
unchanged shape does not mean unchanged contract. Preserve release history and
never manufacture a release stamp for this work.

When shipped source changes, including behavior-preserving refactors, build
through the signed pipeline and finish with a complete default battery on the
final candidate, plus affected opt-in boundary controls. Compare before/after
behavior with independent expectations where a refactor claims preservation;
normalize only justified nondeterminism,
and account separately for build identity changes. If investigation concludes
that only explanatory documentation changes are justified, use documentation
checks and reviewed applicability of existing behavioral evidence rather than
creating an unrelated binary change or forcing unnecessary native runs.

When crediting CLI example runs, use the CLI plan's section 4.6 dispositions.
Keep consistency separate from native success: an admitted non-finished reply
may pass consistency, and the native group may still fail. A valid recorded
validator spawn failure or timeout with honest ordering can be superseded by
a complete passing run without diagnosing an underlying OS cause. Missing
prerequisites, observed sleep and confirmed automation-sandbox refusals have
their specified exclusions. Unexpected denial, failed reads, sampled target
changes and consistency faults require their stated dispositions; later
success alone does not settle them. Target equality is only a before/after
observation, and difference does not identify a writer. Preserve the bounded
ten-run sample, individual failed assertions and corrective/replacement runs;
never restart it to obtain ten consecutive passes. These rules do not waive a
complete passing default battery or automatically apply to other investigations
with different prerequisites and guarantees.

Every credited run records canonical cases, source/test/fixture snapshots, app
identity, configuration, raw inputs/outputs and limits. Reuse evidence only
after a conservative dependency/applicability review under tests/AGENTS; missing
or stale evidence needs a rerun. Inspect sandbox refusals before attribution and
rerun the identical failing command once outside the automation sandbox when
required by repository guidance. An environmental retry does not retroactively
supply observations to the failed run. Preserve failed evidence and unresolved
resource ownership through the existing cleanup machinery.

## 11. Stopping, reconsideration and completion

Stop the affected dependent work and record the reason when the CLI baseline
is unsettled, source inputs move without an applicability review, a public
decision lacks required maintainer judgment, a credited oracle is circular, a
fixture misses the claimed boundary, or a purported owner lacks the information
or mechanism to fulfill its promise. Resolve these with narrower claims,
appropriate evidence or an explicit architectural decision; do not conceal
them by expanding a generic abstraction or lowering test expectations.

Reconsider a decision when an experiment contradicts its premise, a transfer
requires new authority or changes sandbox exposure, or the implementation would
violate fresh-process, host/worker, ordering or honest-attribution constraints.
Retain the counterexample. Pending machine-resource cleanup blocks completion
of that operation and follows its recovery rules; it is not documentation debt.
Unrelated settled work may continue while the affected question is resolved.

Completion requires all of the following:

- The CLI baseline and evidence applicability are recorded; the original A/B/C
  artifacts, freeze and cross-examination remain distinguishable from later
  conclusions. The baseline reflects the code-defined example, shared-consumer
  changes and accepted failure dispositions, without extending their evidence
  scopes or reopening the settled CLI principles.
- Every identified controller obligation has a disposition and traceable
  realization or explicitly accepted public limit. Every ownership/meaning
  change has the required decision and before/after account. No row disappears
  merely because contract and implementation agreed initially.
- Implemented changes exercise responsibilities at their actual owners and
  preserve intended evidence, including refusals, contradictions, uncertain
  execution and recovery. Justified decisions to leave mechanisms in place have
  evidence too.
- `docs/CONTROLLER.md` enables the reader understanding in section 8, with
  scoped supporting citations, coherent navigation and verified representations.
  It explains current behavior and limits; it contains no planning history and
  does not compete with the contract's normative meanings.
- A, B and C have reviewed the integrated result from their original
  perspectives. All consequential findings are resolved or have an explicit
  maintainer disposition represented faithfully in code/contract/documentation.
- Required structural, constructed and native checks have applicable results;
  negative controls fail for the intended reasons. Remaining evidence gaps and
  availability limits are explicit. No unrun required check is reported as pass.
- The minor-task ledger stays within sixteen and records independently checked
  conclusions; generated artifacts and public-change accounting are complete.

The acceptance packet contains the final diff/commits, baseline and decision
records, the obligation/claim crosswalk, delegated findings, original and
returning reviews, verification receipts with limits, and any accepted residual
gaps. The coordinator presents public decisions needing maintainer judgment as
concrete choices; it may complete already authorized implementation and routine
verification without repeated approval requests. This plan ends with the
grounded controller account and justified changes accepted, not with a release.

# PolicyWitness 0.3.0 sandbox extensions implementation plan

Implement a bounded experiment that observes file sandbox extensions during
one disposable worker's lifetime under one fixed, once-applied SBPL policy.
The result must retain issuance, delivery, consumption, release, phase-specific
predictions, and fresh access attempts as independent observations. Successful
native calls do not establish the worker's effective permissions.

This is the active implementation plan. Update its checkpoint and milestone
status as work proceeds. Current behavior remains defined by the repository's
contracts until each implementation increment changes them.

## Execution mandate

When instructed to execute this plan, implement M0 through M5.6 and complete
their acceptance checks. Milestone gates are evidence checks to evaluate autonomously.
When a gate passes, update the checkpoint, commit a coherent verified increment,
and proceed without requesting routine milestone approval. Observe the
[out-of-band audit handoffs](#out-of-band-audit-handoffs) and
[human review pauses](#human-review): commit the prepared handoff or briefing and
checkpoint, then wait for the auditor or user as specified there. Diagnose and
repair failures before advancing dependent work. Outside those pauses, progress
reports communicate findings and do not end execution while authorized work remains.

Use the shared instructions, preceding evidence and the current milestone as its
execution checklist. Keep implementation, documentation and validation requirements
in the milestone that introduces the behavior; later milestones verify those
deliverables without supplying prerequisites for earlier work.

Choose and revise implementation details within the stated scope and evidence
constraints, including the provisional grammar, helper lifetime, reference
representation, limits, and failure behavior. Schema changes under the wire
contract and an evidence-backed revision of the worker allocation claim are
within scope. When experiments contradict a proposed choice, update the plan
and investigative record with the evidence and rationale, then continue. A
failed test, unexpected native result, or unresolved implementation detail calls
for investigation rather than routine user approval.

Reserve user decisions for the issuer-authority expansion specified in M1,
material scope changes, changes to the evidence requirements, or findings that
make an essential success criterion unattainable within the authorized scope.
Never satisfy a gate by weakening its evidence requirements. Outside explicit
review pauses, continue independent work while a decision or required access is
pending, preserving the evidence and the exact condition blocking dependent work.

Execution authorizes local edits and commits, signed builds using the existing
development signing identity, required live and mutation tests, and installation
and removal of test-owned user-scope BYOXPC fixtures under the repository's
ownership and cleanup rules. Establish and record the signing identity and
required environment early. Tool permissions and macOS authorization remain
separate from this task authorization; follow the repository's harness retry
guidance and report access that cannot be obtained. Release publication remains
outside this plan.

## Current checkpoint

| Milestone | Status | Completion evidence |
| --- | --- | --- |
| Repository investigation | Complete | Baseline and findings below |
| M0 Run-stage vocabulary | Pending | Prose rename only; no wire or source change |
| M1 Native feasibility and independent controls | Pending | Required before settling issuer authority and native integration |
| M2 Ordered phases in the existing worker | Pending | Requires M1 design decisions; phase ordering, interruption, ordinary one-phase controls and the M2 contract increment |
| M3 Minimal extension experiment through PW | Pending | Requires M1 and M2; public ordinary and extension phases, standard and BYOXPC runners, incomplete native results, token confinement controls and the M3 contract increment |
| A1 Middle out-of-band audit | Pending | After M3; committed questions, returned auditor answers and execution dispositions in the shared audit document |
| H1 Prepared human review | Pending | After M3's documentation assessment and A1 closure; prepared assessment, user response permitting continuation, and recorded disposition |
| M4 Failure combinations and adversarial coverage | Pending | Requires M3, A1 and H1 closure; extends the boundary controls already required in M2 and M3, plus the M4 contract increment |
| M5.1 Evidence contract closure | Pending | Requires M4 |
| M5.2 Limits account | Pending | Requires M5.1 |
| M5.3 Build and bundle account | Pending | Requires M4; independent of M5.1 and M5.2 |
| M5.4 Architecture account | Pending | Requires M5.2 and M5.3 |
| M5.5 User-facing documentation | Pending | Requires M5.4 |
| M5.6 Integrated acceptance and record | Pending | Requires all preceding milestones |
| A2 Final out-of-band audit | Pending | After M5.6; returned audit, required corrections and evidence for the final candidate complete before plan closure |

Each implementation gate includes its
[rendered documentation assessment](#rendered-documentation-assessment) waypoint
and the lead agent's disposition of the findings. A1 and A2 use the separate
out-of-band handoff below; H1 uses the prepared human review briefing.

**Execution state:** implementation has not started. The development signing
identity and candidate build have not been selected. This plan has created no
implementation processes or BYOXPC cleanup obligations. Credited investigation
checks and their source baseline are listed below.

**Next action on execution:** complete M0, the run-stage vocabulary rename, as
one commit. Then establish the development signing identity and required
environment, and build the M1 native experiment and its independent controls.
Start with a controlled read-only file extension and an ordinary unprivileged
issuer. Establish the actual signing and entitlement baseline before
interpreting any outcome.

After each increment and before any planned stopping point, update this table and
execution state so another session can resume safely. Record the implementation
commit and any relevant uncommitted source snapshot, candidate build identity,
credited test runs, unresolved findings and decisions, active processes or cleanup
ownership, and the exact next action. Put detailed empirical findings, negative results,
decision rationale, and reproduction instructions in an associated
`records/SANDBOX-EXTENSIONS.md` record when M1 produces evidence.
Follow [record guidance](records/AGENTS.md); link that record from this plan.
Keep permanent documentation focused on current behavior, with history in git.

## Scope and constraints

- Keep a fresh host and worker per specimen, with exactly one policy application
  in that worker. Consumption and release execute in that same worker.
- Keep the XPC host free of native sandbox API calls. Issuance happens outside
  the sandboxed worker under separately recorded authority.
- Establish ordering with observed protocol boundaries. A phase is an ordered
  interval, not a stable state snapshot or proof that a target retained its identity.
- Reserve `phase` for a specimen phase. A stage of one run, from admission
  through reply, is a "stage" in prose and in wire keys. The three existing reply
  keys named `phase` become `stage` under the M2 response bump with no change to
  their values or meaning; M0 renames the prose first.
- Keep native results, missing observations, partial publication, and uncertain
  cleanup visible. Do not add `extension_active`, prediction/enforcement agreement,
  drift verdicts, or unsupported sandbox-cause claims.
- Keep raw tokens out of specimens, command arguments, environment variables,
  ordinary diagnostics, envelopes, logs, and retained artifacts. Use local token
  and handle references; keep authority-bearing bytes in transient channels.
- Use investigator-owned regular files as test discipline for M1 and acceptance
  experiments. Do not add ownership, file-type, or symlink admission restrictions;
  retain path preparation evidence and native outcomes for admitted targets.
  Begin with the smallest demonstrated extension class. Broader classes and
  process-bound issuance remain outside initial scope.
- Limit each specimen to at most one extension declaration and its associated
  token and consume-result handle references. Permit at most one consume action
  and one release action across the entire phase sequence. Refuse additional
  declarations, including sequential ones, and repeated consume or release actions.
- Support extension specimens on both standard and BYOXPC runners in 0.3.0,
  with a bundle-local issuer inside the XPC service bundle.
- Keep ordinary stateless specimens simple. Use one canonical execution model
  with a one-phase path in which query collection closes before any attempt
  begins, including on timeout or failure. Closure does not require a verdict
  for every eligible query. Do not introduce historical request/reply translation.
- Expose a bounded public sequence of phases containing ordinary query/attempt
  pairs and explicit extension lifecycle interventions. Every ordinary entry
  requires both a submitted query and an attempt, preserving existing comparison
  semantics; query-only and attempt-only ordinary entries are outside the 0.3.0
  grammar. Extension lifecycle entries omit that pair and have their own event
  records. Ordinary specimens may use multiple phases without extensions. Exclude
  branches, loops, arbitrary dependency graphs, and user-defined conditions.
  Token/handle references and a release that cannot run after failed consumption
  need fixed operation semantics, not a general dependency engine. Refuse
  unsupported action combinations explicitly.
- Preserve bounded admission and collection, explicit refusals, partial evidence,
  and optional denial logging that cannot change execution results.

PW maintains bounded operational state to route references, coordinate execution,
and identify published observations. Claims about the apparatus still require
observations: a host release request and a worker acknowledgement are separate
facts. This state supplies no model of the kernel's effective permissions. As
the implementation lands, explain this distinction under the existing evidence
and runner principles in the architecture account; do not describe proposed
behavior as already implemented.

## Baseline and findings

The repository investigation used source commit
`8ae8024f60b16dc4918969339c63cc4b11c0ab71`. No product implementation was changed.
The host reports macOS 26.7.1, build 25G241. Dynamic symbol lookup found
`sandbox_extension_issue_file`, `sandbox_extension_consume`, and
`sandbox_extension_release`; this establishes availability only. Issuer authority,
consumption effects, release effects, and query sensitivity remain untested here.

The following findings determine the work:

- [CWorkerOrchestrator.swift](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
  plans queries once and invokes one validator collection. The
  [worker driver](runner/Sources/PWRunnerCore/CWorker.swift) releases all attempts
  through one `proceed` and `proceed_observed` pair. Phases require a new protocol.
- [PWRunnerAPI.swift](runner/Sources/PWRunnerCore/PWRunnerAPI.swift) requires a
  query/attempt pair per step. Lifecycle interventions need their own meaningful
  records, without invented queries. Ordering is currently interpreted at run
  scope by both the producer and [independent consumer](tests/lib/consumer.py).
- The [C worker](controller/tools/pw_probe_runner/pw_probe_runner.c) promises no
  allocation after application. Private extension calls require investigation
  before retaining or revising that promise. Pretouching PW's shared memory does
  not establish the behavior of code inside a native library.
- `attempt_file_open_read` opens a fresh descriptor but discards read and close
  results. Its successful status establishes an open, not verified retrieval of
  known contents. The experiment needs stronger observations if it claims a read.
- Query eligibility currently includes host path resolution before execution.
  Later host diagnostics cannot substitute for the observation used to admit
  a query.
- A prior [project investigation](https://github.com/Protonk/PolicyWitness/issues/1)
  reports release calls without reliable access revocation on Sonoma 14.4.1.
  Treat this as a lead for controls, not a finding about the current host.
- The build checks generated documentation before compiling. Input ownership
  and update rules are listed under
  [Contract increments at each gate](#contract-increments-at-each-gate).
- The reply keys `path_diagnostics.phase`, `wait_errors[].phase` and the worker
  progress field, and the architecture prose, use `phase` for a stage of one
  run. M0 and the M2 response bump resolve that collision.

Three baseline cases passed: `source_drift/contract_versions`,
`source_drift/architecture_documentation`, and `source_drift/generator_contract`.
Their [run summary](tests/out/runs/extensions-brief-review-20261011/run.json) is
gitignored and available only in this local checkout. These checks establish
mechanical agreement and generator controls, not live extension behavior or
general product acceptance.

## Proposed execution design

Use a bounded sequence of phases. At each phase entry the worker publishes its
arrival and waits. The host observes arrival and worker ownership, plans and
collects all eligible queries from that phase's ordinary pairs, and closes
collection before considering release of any attempt or lifecycle intervention.
Every started collection closes on success, timeout, or failure, with
missing predictions retained as unavailable. The host publishes release only
when the phase and worker-ownership checks permit progression. Observed worker
loss, an invalid boundary, or an expired worker wait ends progression with the
available evidence preserved. On normal progression, the worker acknowledges
release before running the phase's declared actions in order, then publishes
arrival at the next boundary or final completion.

Evaluate query eligibility afresh during each phase's planning, preserving the
existing exclusion rules. A path filter requires successful host `realpath`
resolution at that boundary. Retain the planning observation's phase association;
it admits a query only in that collection. A resolution failure skips the native
query and records `prediction_unavailable`, the
`query_plan:path_unresolved_at_planning` limitation, and
`comparison.order: unestablished`, while the paired attempt remains eligible to
run. Issuance-target preparation and later path diagnostics are separate
observations, not substitutes for query planning.

Keep phase progression evidence distinct from a pair's `comparison.order`.
An action's published completion and the observed phase boundaries can establish
that it completed before later planning and execution even when that later phase
has no native query result.
`query_first` still requires an eligible native record and the full collection,
release, and acknowledgement chain for its phase.

Use numbered boundaries and immutable phase/event publications so a previous
release or acknowledgement cannot satisfy a later phase. Distinguish reaching a
native call boundary, the call's return, and publication of its result. A marker
written immediately before a call establishes only that execution reached that
boundary; it cannot prove the call entered or completed. A worker can also die
after a native return but before publishing it. A later phase arrival must not
manufacture a missing earlier call result. Failed predictions can leave an
informative execution history; no phase should wait indefinitely for a usable
verdict.

Consume and release may appear anywhere among the phases' ordered actions.
Consume must name the declared token reference; release must name the handle
reference associated with an earlier declared consume, using phase order and
then action order within each phase. Both actions are optional and may occupy the
same phase or different phases. Issuance and delivery without consumption, and
consumption without release, are legal experiments.
Admission checks declared order and references; it does not predict native
success. All queries still precede the entire action batch within their phase.

The required three-phase acceptance specimen has this conceptual sequence,
independent of final JSON names:

| Phase | Queries while the worker waits | Worker actions after release |
| --- | --- | --- |
| Before consumption | Query access to the controlled file | Fresh access attempt, then consume the referenced token |
| After consumption attempt | Query the same access against the same worker | Fresh access attempt, then release the handle if one was obtained |
| After release attempt | Query the same access against the same worker | Fresh access attempt and terminal publication |

Phase names describe placement in the experiment. Only event records establish
whether consume or release was attempted or returned successfully. Resolve
runtime dependencies explicitly: failed consumption leaves no invented handle;
a dependent release records why it could not run. Keep later observations useful
when safe to continue, and record where a terminal failure stopped execution.

Use a disposable native issuer supervised by the host and resolved inside its
XPC service bundle. Use a dedicated bounded transient channel for tokens,
separate from retained evidence. Choose issuance timing and helper lifetime from
M1 evidence; do not assume the issuer must stay alive or can safely exit before
consumption. Keep the worker's single handle record limited to its routing
reference and observed call outcomes.

Before issuance, the host resolves symlinks in the submitted extension target and
passes the resolved path to the issuer. Retain the submitted path, resolved
issuance path, and observed device, inode, mode, and owner. Resolution or metadata
lookup failure produces a bounded, named preparation failure. Do not silently
rewrite independently submitted query or attempt targets. These host observations
do not establish stable file identity across resolution, issuance, or later
accesses; keep them distinct from identity witnessed by those accesses.

Initially prefer a fresh validator collection per phase, reusing the current
bounded driver. Measure the cost and cleanup behavior before considering a
persistent validator protocol. Each accepted native record must be associated
with its phase, query, and observed worker lifetime; late records cannot migrate
into a subsequent collection.

## Shared verification requirements

Follow [test guidance](tests/AGENTS.md) throughout for output ownership, evidence
provenance and reuse, locking, cleanup, and sandboxed-harness retries. For changed
admission and transport, run `failure_boundaries`, `runner_unit`, `runner_abi_layout`,
`runner_c_worker_harness`, and `unit`, plus affected validator and witness cases.
Select signing, build and maximum-reply controls in the increment that changes
their boundaries. Verify changed aggregate limits and the largest admitted reply
through real transport. Credit reusable evidence only under the test guidance;
record its source/build identity and the checks still owed by the current increment.

Register each new case in the catalog, owning suite README, coverage account and
opt-in registry as applicable, and update the test suite map when its entries
change. Every implementation gate from M2 onward includes a signed build and a
passing `source_drift` suite; neither the prose nor build baseline gains an entry.
Each milestone below names its additional controls and acceptance evidence.

The controls below belong to the earliest indicated milestone. Each case must
establish its intervention independently and assert retained observations as
well as withheld claims. Milestone gates apply these controls to their delivered
boundaries; M4 extends them with combinations and adversarial conditions.

| Boundary | First required | Required controls |
| --- | --- | --- |
| Phase admission | M2 | Duplicate/unknown phase or action identities, ordinary entries missing a query or attempt, unsupported combinations, oversized counts/strings, embedded NUL |
| Phase query eligibility | M2 | Fresh planning observations per phase, unresolved paths excluded despite earlier resolution, unavailable predictions and unestablished query/attempt order alongside retained phase progression, actual later-phase queries on resolvable targets |
| Extension admission | M3 | Additional declarations even if sequential, repeated consume/release actions, duplicate/unknown references, release without or before consume, invalid handle use, unsupported combinations, unavailable helper/API |
| Lifecycle placement | M3 | Same-phase consume/access/release, cross-phase placement, issuance/delivery without consumption, consumption without release, preserved query barrier, omitted actions distinguished from unresolved calls |
| Target preparation | M3, building on M1 target evidence | Symlink resolution, resolution/metadata failures, retained submitted and resolved paths, unchanged query/attempt targets, no owner/type admission rule, replacement between observations without a stable-identity claim |
| Issuance and delivery | M3, building on M1 native refusals | Native refusal, issuer death, timeout, partial/oversized token transfer, delivery without consumption, unknown cleanup |
| BYOXPC integration | M3 | Bundle-local issuer resolution, install signing and read-back, validate/reconcile evidence, older registry records and cleanup, named missing-issuer capability refusal |
| Consumption and release | M3, building on M1 native calls | Rejected token, failed consume without a handle, dependent release unable to run, failed release, missing result publication |
| Phase ordering | M2 | Delayed/missing predictions, validator failure, late/wrong-phase records, stale release/acknowledgement, phase exhaustion, host loss while worker waits |
| Worker lifetime | M2 for phase interruption; M3 for native calls | Death before/inside/after consume or release, death before acknowledgement, failure after a completed earlier phase, unresolved termination/reap |
| Independent readers | M2 for phases; M3 for extensions | Reject fabricated lifecycle success, cross-phase prediction association, unsupported versions, and unsupported ordering claims while retaining raw evidence |
| Optional logs | M3 with multi-phase CLI integration | Repeated target/PID across phases remains ambiguous unless evidence narrows it; log presence, absence, or capture failure cannot change execution |

Observe native-call failures through controlled seams where live reproduction
is unreliable; do not confuse injected return values with kernel behavior.
Do not infer explicit release from worker exit or successful cleanup from EOF.

## Contract increments at each gate

Update these inputs and regenerate their outputs in the milestone that changes
the behavior. Mechanical checks establish agreement within their coverage;
rendered assessment checks the account against implementation evidence.

| Owner | Account and required agreement |
| --- | --- |
| [Contract manifest](docs/contract.json), field-complete fixtures and shape goldens | Versions and reply fields agree with producers and independent readers. Update ABI layout, its static assert and golden, and generated worker identity with protocol changes. |
| [Limits manifest](docs/limits.json) | Each bound has a source symbol, value test in a listed owner file, and boundary or path control. Render values into tables, spans and guide copies. |
| [Build manifest](docs/build.json) | Build and signing steps agree with `build.sh`, Meson targets, `tests/lib/native_sources.py`, artifact inspection, evidence generation and README inventories. |
| [Architecture manifest](docs/architecture.json) | Topology, boundaries, BYOXPC and document graphs agree with implementation and cite existing tests or rules. Durations and sizes use limit placeholders. |
| [Scenario matrix](tests/fixtures/comparison/matrix.json) and [failure contract](tests/FAILURE-PROPAGATION-CONTRACT.md) | Evidence vocabulary and reading rules agree with the encoder, consumer, live cases and Swift comparison tests; regenerate matrix views and shared guide sections. |

Standing rules for these increments:

- A new number in prose is a span rendered from a manifest, never a literal. A
  count with no manifest owner is stated without the number.
- A new build refusal gets a behavioral control in the same increment; the build
  baseline does not grow.
- The `limitations` and lifecycle vocabularies are closed in three places. Change
  the encoder, `tests/lib/consumer.py` and the matrix fixture together.
- The failure contract states header offsets and sizes as prose. When the header
  changes, cite the layout golden instead of restating literals.
- An architecture node or edge is added in the milestone whose tests it cites.
  Update its generated graph and table, the run timeline and evidence-channel
  landing paths, and affected principles and known gaps in the same increment.
- When documentation regions or drift rules change, update the architecture
  document graph and keep its drift-node check list equal to what
  [check.py](tests/suites/source_drift/check.py) runs. Update affected controller
  and runner READMEs and AGENTS files when behavior or working instructions change.
- Regenerate the worker identity in every commit that touches a protocol source.
- Before adding explanatory prose, identify facts that belong in manifests,
  fixtures, shared source sections or generated views. Extend the owning generator
  and its controls where those facts are not represented, regenerate, and then
  write only the remaining explanation. Follow the
  [generator contracts](tests/suites/source_drift/README.md#generator-contracts);
  never patch generated output or expand a baseline to silence a review finding.

## Rendered documentation assessment

At each waypoint below, dispatch a fresh read-only sub-agent, preferably Astra
when available, after the increment's documentation has been regenerated and its
required mechanical checks have run. Give it a bounded brief for that waypoint,
not the implementation conversation or the lead's preferred diagnosis. These
reviews are part of implementation; the lead retains responsibility for gate
decisions and the execution mandate's reserved user decisions.

Provide the source revision and any uncommitted diff, the milestone's implemented
scope, affected rendered documents and diagrams, their owning inputs/generators,
and relevant test evidence. Hold the reviewed files stable or identify an immutable
snapshot. Include surrounding sections and linked copies where needed to read
the changed account coherently. Do not present still-planned behavior as current
behavior or ask the reviewer to treat a passing drift check as semantic proof.

The reviewer reads the generated account as a reader encounters it: rendered
Markdown with its tables, links, copied sections and embedded SVGs, including
the staged guide when that waypoint produces it. Raw manifests, Markdown source,
DOT files or SVG stamps alone do not constitute this inspection. Use an available
local preview for Markdown-only outputs; record the renderer and artifact revision.
If a surface cannot be rendered or inspected, report that coverage gap explicitly.
Trace surprising or missing claims back to their owning inputs, generator,
implementation and cited tests after reading the rendered account.

Return a concise report with the inspected surfaces and omissions, and one entry
per substantive finding: rendered location and claim or omission, why it matters,
source/test evidence, proposed route below, confidence or remaining uncertainty,
owning input/generator, and the smallest corrective action or discriminating check.
Identify generator coverage to add before proposing handwritten prose. A resolved
citation establishes that a test exists; assess whether its observations support
the claim. Record unsupported assertions, stale copies, misleading presentation
and contradictions even when generation and drift checks pass.

| Proposed route | Evidence needed and next step |
| --- | --- |
| Documentation issue | Implemented behavior and its evidence are sufficiently established, but the account is stale, incomplete or misleading. Correct the owning input, generator, copied source or rendering; regenerate and check the affected views. Use handwritten explanation only for what remains. |
| Implementation problem | Evidence supports a concrete defect in product behavior, a reader, or the controls needed to establish the required behavior. Repair the responsible code or test boundary, verify it, then regenerate its account. Do not revise the documented requirement merely to excuse the defect. |
| Investigation blocker | An unresolved fact, conflicting evidence or design assumption prevents a specific gate claim or dependent step. Name that dependency, competing explanations and the smallest investigation that can distinguish them. A surprising sentence alone does not establish a blocker. |

Routes are provisional and may be linked: a misleading paragraph can expose a
code defect or a missing experiment. The lead checks each cited passage, its
owner and the decisive evidence, then accepts, reclassifies or rejects the finding
with a short rationale. This is a bounded assessment of the report, not a second
full audit. For uncertainty affecting a gate, run the narrow discriminating check
before deciding the route. A sub-agent's blocker label does not itself halt work;
a confirmed blocker stops the affected dependent work under the execution mandate
while independent work continues.

Resolve correctness findings for the current increment before closing its gate.
Remaining editorial work or coverage of behavior scheduled for a later milestone
may be assigned there with an explicit owner and reason, provided current claims
remain accurate. After fixes, regenerate and rerun the affected checks, then send
the changed rendered surfaces and finding dispositions for a focused recheck.
Repeat only for unresolved findings or materially changed evidence. Record the
reviewed revision, reviewer/model, render and report locations, lead dispositions
and recheck status in the checkpoint; put detailed reports in the associated
investigative record once it exists. Label local-only artifacts accordingly.
An unperformed inspection remains pending, not passed.

| Waypoint, before gate closure | Bounded assessment focus |
| --- | --- |
| M0 | Rendered architecture and failure-contract vocabulary and their affected copies: run stages remain distinct from specimen phases, and descriptions of unchanged wire keys remain accurate. |
| M1 | Rendered feasibility findings and any affected generated/shared accounts: issuer authority, native results and allocation evidence remain distinct from assumptions and unimplemented product behavior. No production documentation is invented solely for this review. |
| M2 | Generated contract/version views, response shapes and matrix, ordering/progress account and architecture additions: phase association, stage keys, eligibility and incomplete publication agree with reader and control evidence. |
| M3 | Generated build/signing inventories, limits, topology and boundary views, plus the guide and grammar: lifecycle records, public examples, issuer authority, BYOXPC provenance, token handling, placement caps and new refusals have complete owners and supporting controls. |
| M4 | Rendered combined-fault matrix, coverage and architecture citations: partial and unresolved outcomes remain visible; cited controls support each claimed boundary rather than merely existing. |
| M5.1 | Completed evidence account and copied reading rules: lifecycle records, phase ordering, vocabulary and consumer meaning agree across generated and handwritten regions. |
| M5.2 | Limits tables, spans and copied budget explanations: value owners, units and interactions describe the implemented waits and transport bounds without unsupported arithmetic or guarantees. |
| M5.3 | Build graph, inventories, signing/evidence tables and surrounding operating guidance: the issuer and refusal/cleanup paths are represented consistently. This review can proceed independently of M5.1 and M5.2. |
| M5.4 | Rendered architecture graphs and their tables, captions and prose as a whole: process/channel boundaries and operational-state claims are consistent, legible and supported by the cited observations. |
| M5.5 | Rendered user guide and its staged copy, grammar, FAQ and linked operating guidance: public examples, unavailable results and capability refusals read consistently with the implemented contract. |
| M5.6 | Reconcile prior findings with the accepted source/build and rendered artifacts; review changed surfaces since their last assessment and confirm credited reviews still apply to this candidate. |

## Out-of-band audit handoffs

Use [records/SANDBOX-EXTENSIONS-AUDIT.md](records/SANDBOX-EXTENSIONS-AUDIT.md)
as the single committed exchange document for both audits. The executing agent
writes questions at the waypoint from the implemented system, rendered account
and available evidence. The auditor is another agent working out of band and
writes answers and additional findings in that same document. Keep these audits
separate from the implementation's rendered-documentation sub-agent reviews.

| Audit | Handoff point | Resume condition |
| --- | --- | --- |
| A1 Middle | After M3 and its documentation assessment, before H1 and M4. The real CLI lifecycle, public grammar, BYOXPC integration and their contract increments are available to inspect together. | Auditor answers are returned and dispositioned; findings that invalidate M3 or block dependent work are resolved. Then prepare H1. |
| A2 Final | After M5.6 and its documentation assessment, before declaring the plan complete. The complete account and integrated acceptance evidence identify the candidate under review. | Auditor answers are returned and dispositioned, required corrections are verified, and the audit and acceptance evidence apply to the final candidate. |

At each handoff, identify the exact source commit, build identity, rendered
documentation and test evidence, relevant limitations and inaccessible/local-only
artifacts. Write the actual questions then; do not seed them in advance. Commit
the populated document and checkpoint, record the audit as awaiting response,
report the handoff commit, and pause execution. An unanswered handoff is pending.

The auditor answers beside the questions with evidence and may raise findings
beyond them. Preserve the auditor's words and attribution; the executing agent
adds its own dispositions separately, using the documentation/implementation/
investigation distinction above. Resolve disagreements through cited evidence or
the narrow investigation they require. Commit returned answers, dispositions and
correction evidence before closing the audit; carry any agreed later work into
its named milestone without weakening that milestone's gate.

Keep the middle exchange when preparing the final one. Clarifications, repairs
and auditor follow-up stay in the relevant section of this same document. If
repairs change the reviewed candidate, refresh affected checks, generated accounts
and review references, and obtain any needed follow-up there. These are two audit
waypoints in total; follow-up does not create an additional audit milestone.

## Human review

The executing agent owns the API, design, diagnosis and proposed response to
findings. Human review examines the necessity and coherence of the implemented
machinery through the documentation assessments and the agent's reasoning.

**H1 prepared pause:** after M3's documentation assessment and A1 have been
reconciled and closed, prepare a conversation with the user before starting M4.
Use the existing rendered views and recorded findings, including concerns already
resolved by the agent when they expose consequential complexity. Give a short
briefing containing:

- The rendered passage, diagram or omission that prompted the concern.
- The reviewer's finding and the executing agent's assessment of it.
- The disputed mechanism's responsibility and any existing mechanism that could
  serve it, with the relevant implementation evidence.
- The agent's recommendation and the consequences of retaining or changing it.

If the assessments reveal no substantial complexity concern, say so and give
the basis for retaining the implemented design. Prepare a recommendation before
the pause; routine API decisions and unfinished diagnosis remain the agent's work.
Keep the briefing and its evidence references in the checkpoint and associated
investigative record, without creating another review document. Commit that
preparation, mark H1 awaiting the user, present the briefing, and pause execution.
Resume only when the user's response permits continuation. Record any redirection,
update the plan and affected evidence, and close H1 before starting M4. Individual
API decisions do not require separate approval. The final handoff invites user
review without adding a scheduled human approval gate.

**Later review trigger:** pause when a documentation assessment exposes
substantial duplication, competing models of the same behavior, or a new general
mechanism whose necessity remains doubtful after the lead's bounded investigation.
First trace the relevant code, existing mechanisms and evidence, establish the
facts, and prepare a recommended response using the same briefing above. Pause
before expanding the disputed mechanism; record the trigger, affected work and
recommendation in the checkpoint, commit the preparation, and await the user's
response under the same resume rule as H1. Routine documentation repairs, test
failures, API choices and uncertain native behavior do not by themselves trigger
this pause. The issuer-authority and other reserved decisions in the execution
mandate continue to apply.

## M0 Run-stage vocabulary

`phase` belongs to the extension machinery: a specimen phase is the ordered
interval defined under [Scope and constraints](#scope-and-constraints). The
repository uses the same word for stages of one run. Before M1, rename those
prose uses to "stage": the pinned-stage list and the budget sentences in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), the lifetime sentence in
[runner/README.md](runner/README.md), and the sentences of
[the failure contract](tests/FAILURE-PROPAGATION-CONTRACT.md) where "phase"
means a run stage rather than naming a wire key. Leave the three reply keys
named `phase` and the sentences that describe them untouched; they are renamed
to `stage` under the M2 response bump, with no other change to their values or
meaning. Keep the harness-note and core-ideas copies in agreement.

**Completion gate:** no prose outside a wire-key description uses "phase" for a
run stage; `source_drift` passes; the worker identity is unchanged; one commit.

## M1 Native feasibility and independent controls

Build a small native harness independent of PW's result classifier and phase
implementation. Register its controls through the test harness and preserve
source, build commands, OS/SDK facts, signing and entitlement read-backs, native
results, and independent effects. Keep tokens entirely transient.

1. Create an investigator-owned regular file with known contents and controlled
   permissions. Record the submitted and resolved issuance paths, device, inode,
   mode, and owner, and verify access before introducing the experimental policy.
   The sandboxed worker must not inherit an open descriptor to this target.
2. Issue a read-only extension outside the worker. Apply one fixed policy with
   the relevant extension predicate in the worker. Observe access before consume,
   after consume, and after release, using a fresh open/read/close sequence each
   time. Retain native returns and errno with their validity conditions, file
   identity, and bounded content observations sufficient to verify the read.
3. Query the live worker externally at each paused boundary. Record answers even
   when unchanged or unavailable; require neither prediction agreement nor a
   deny/allow/deny pattern for evidence validity.
4. Run separate controls for no consumption, a policy without the extension
   predicate, a different target, unsuccessful issuance/consumption, and retained
   descriptor access after release. Hold other conditions fixed within each
   comparison and distinguish retained access from a fresh open.
5. Test the issuer lifetime and authority relevant to the shipped app. Record its
   credentials, signature, entitlements, and demonstrated authority as experiment
   inputs. Do not infer entitlement requirements from symbol availability or a
   failed call. Distinguish incorrect inputs, signing conditions, and automation
   sandbox restrictions before concluding that ordinary issuance is unavailable.
   Running an ordinary process outside the automation sandbox does not itself
   give the product new privileges.
6. Inspect and, where practical, instrument native allocation/resource behavior
   after application, including first-call behavior. Document what is measured
   and what remains uncertain. Resolve the existing allocation claim explicitly.

**Completion gate:** a reproducible native lifecycle experiment and controls,
with findings supporting the chosen issuer authority, token transport, call
signatures, result widths, and worker invariant. In particular, preserve the
consume API's handle width separately from PW's existing 32-bit status fields.
If evidence indicates that issuance requires elevated privileges, a privileged
service, or an entitlement unavailable to ordinary PW distribution, report the
finding and obtain an explicit user decision before designing or implementing
that authority expansion. Continue independent diagnostics that do not require
it. For other contradicted implementation assumptions, report the evidence and
revise this plan autonomously before building dependent features, provided the
objective and constraints remain intact. If an essential success criterion is
unattainable within those constraints, seek the reserved user decision under the
execution mandate. Retaining access after release or unchanged queries does not
by itself invalidate the witness objective.

## M2 Ordered phases in the existing worker

Introduce phases using existing file operations before adding production
extension calls. Exercise the smallest provisional request and evidence
representation needed for the bounded public phase model, informed by M1.
Internal harnesses may establish the phase protocol before new public syntax is
settled. Use both ordinary action sequences and the native extension experiment
integrated in M3 to settle that syntax; provisional wire formats still require
explicit versioning and coordinated readers.

- Define phase/action identities, legal ordering, reference admission, and the
  ordinary one-phase authoring path. Bump the response contract for the new
  phase records and the `phase`-to-`stage` key rename. Apply
  [the wire contract](docs/CONTRACT.md) to determine request and envelope version
  changes; change the envelope version only if its reading rules require it.
- Implement phase arrival, collection closure, release, acknowledgement, and
  terminal handling in C and Swift. Associate predictions and comparisons with
  the correct phase. Apply the phase-local eligibility rules above and preserve
  unavailable queries separately from access attempts.
- Bound phase count, total actions/queries, publication storage, and total
  collection time as well as individual waits. Specify how phase waits interact
  with worker execution, cleanup, exec budgets, and the client RPC timeout. Add
  limits rows with source and value-test owners and boundary/path controls for
  every new bound. Update the Interactions and Premises in `docs/LIMITS.md`, the
  architecture budget account and their guide copies for per-phase waits against
  worker/sentinel and client windows. Render new values through manifest spans.
- Update producers and independent readers together, including lifecycle
  interpretation, shape fixtures, ABI layout, and generated worker identity.
- Use independently observed file effects and held validator gates to establish
  that actions cannot run early and later queries follow completed interventions.
  Include stale/wrong-phase acknowledgement, interrupted collection, worker death,
  and missing-prediction controls. A missed boundary or premature worker death
  must not produce a fictitious completed phase. Extend and run
  `witness_contract/order_barrier_mutations` whenever its governed code changes.

Contract increment for this gate: regenerate the response contract's copies.
Rename the three reply keys named `phase` to `stage` and update their readers,
fixtures and descriptions. Record every new reply key
in the field-complete fixture and the shape golden. Change the ABI header and
its static assert, the layout golden and the identity together, and replace the
failure contract's literal offsets with a citation of the layout golden. Add
each new `limitations` or lifecycle vocabulary string to the encoder, the
consumer and the matrix fixture in one commit. Extend the test-override table
for new seams and add COVERAGE rows for new outcome values. Fixture directories
are named by response version, so the bump creates the new version's directories
rather than editing retained ones.

Document phase ordering, protocol names, worker evidence operations and progress,
claim ownership, incomplete publication and phase association in the failure
contract and independent-reader rules. Regenerate the matrix and the guide's
shared reading rules. Describe the implemented response shapes and ordinary
one-phase behavior and any authoring syntax exposed by this increment. Keep
the request grammar and corpus current for new public admission refusals;
keep internal-only provisional syntax in the investigative record. Update the
architecture manifest and generated views for phase barriers, validator
collections and worker lifetime, with the timeline, evidence landing paths and
operational-state principle matching them.

Validation for this gate: run the shared admission/transport suites and affected
validator/witness cases, including `witness_contract/order_barrier_mutations`.
Include the independent blackbox checker controls, Swift comparison tests, and
Swift/C limit contract tests for the new phase records and bounds. Establish
aggregate storage and reply bounds through real transport.

**Completion gate:** independently controlled execution through the production
C/Swift phase protocol with multiple real boundaries in one worker, mutation
controls that reject premature execution, and interruption controls that withhold
unsupported phase completion while retaining earlier evidence. A signed CLI
one-phase regression must establish that query collection closes before any
attempt begins on success, timeout, and failure, including missing-verdict cases.
Public CLI experiments with ordinary and extension phases are required in M3;
their exact syntax need not be fixed in M2. The contract increment above is
complete, `source_drift` passes against a signed build, and neither baseline
gained an entry.

## M3 Minimal extension experiment through PW

Integrate the M1 issuer and native calls with the M2 protocol. Implement the
three-phase experiment above using local references and structured lifecycle
events. Record issuance and delivery independently from worker consumption,
including explicit unavailable or skipped dependent actions. Use this integrated
experiment and the ordinary paired-probe specimens below to settle one bounded
public phase syntax, subject to M4's adversarial checks before treating the
interface as final.

Enforce the declaration and lifecycle-action caps and reference-order rules in
admission, and record the caps in the limits manifest. Exercise the shared
lifecycle-placement controls through the public CLI, preserving the distinction
between omitted actions, declared actions that could not run, and calls without
a published result.

Demonstrate ordinary phases without extensions using two controls. The first
establishes eligibility becoming unavailable after a successful unlink:

| Phase | Submitted path query | Paired attempt on the same target |
| --- | --- | --- |
| 1 | `file-write-unlink` | `unlink` |
| 2 | `file-read-data` | `access` |

Independently verify the unlink and failed phase-2 host resolution. Phase 2 must
retain the unavailable prediction and `comparison.order: unestablished`, alongside
evidence of phase progression and the actual access result. Expect `ENOENT` under
the controlled fixture's policy, but preserve whatever the syscall reports. The
second control keeps its target resolvable across ordinary phases
and establishes an actual later-phase validator query with the supporting
collection/release/acknowledgement evidence. Neither control uses ordinary
query-only or attempt-only entries.

Provide the access evidence established in M1. If a new action or changed action
meaning is needed, apply the request-contract rules rather than silently
reinterpreting `open_read`. Preserve native results and local handle association.

Add the bundle-local issuer to Meson, bundle assembly, signing, evidence
inventories, native source checks, and helper resolution. Extend BYOXPC install
signing, read-back, validate, reconcile, and registry records to include it.
Sign the issuer with the selected identity without the worker's entitlement
plist; additional issuer authority remains subject to M1's decision gate.
Preserve management and cleanup of older registry records, treating absent
issuer evidence as unknown. A selected runner lacking the required issuer must
refuse extension specimens with a named capability code. Cover unsupported native
capability explicitly and keep host sandbox-import guards intact.

Test token confinement on success and failure, including malformed transport,
truncation, diagnostics, and cleanup. Compare captured output with token bytes
inside the test process without printing the token or placing it in a retained
fixture. Bound token storage, close inherited channels deliberately, and erase
buffers at the chosen lifecycle boundary. Resolve exec/inheritance interactions
explicitly; refuse unsupported combinations rather than silently expanding scope.

Exercise interruption around consumption and release in this milestone. Include
death after the pre-call marker, during the operation where a controlled seam
can establish that position, and after native return but before result
publication. Use observations to distinguish the test intervention from what PW
can know. No published native result means the result remains unresolved even
when the test knows the call returned.

Contract increment for this gate:

- Add the issuer's Meson target to `tests/lib/native_sources.py`, and its signing
  call to `docs/build.json`, the README inventory, `tests/lib/artifact.py` and
  `tests/build-evidence.py`, then regenerate BUILD.md. Update signing and embedded
  evidence explanations, `docs/SIGNING.md`, distribution and preflight READMEs,
  and build known gaps. Give each new build refusal a behavioral control.
- Add limits rows with source and value-test owners and boundary/path controls
  for the extension declaration/action caps, token size and issuer waits. Update
  the existing phase/budget account for their interactions and regenerate copies.
- Define the lifecycle event shapes, native result validity, missing-publication
  semantics and evidence ownership in the failure contract and consumer rules.
  Coordinate versions, fixtures, vocabulary and matrix entries with the encoder
  and readers, and regenerate shared reading rules. Keep attempt-kind enums in
  agreement and add a COVERAGE row for any new action.
- Document the public phase grammar, ordinary pairs, extension declaration,
  lifecycle placement, response shapes and access-action meaning in the guide
  and request-grammar lesson. Add examples for supported ordinary and extension
  specimens and corpus cases for each new refusal, including the capability
  refusal. Document target resolution and metadata evidence, BYOXPC installation,
  issuer registry fields and older-record recovery. Update the extensions FAQ
  in `docs/QUESTIONS.md` and regenerate its guide copy.
- Add the issuer, token channel, preparation/admission guards and evidence
  boundaries to the architecture manifest, including BYOXPC signing, read-back
  and provenance, with citations to their controls. Regenerate graphs and tables;
  update the issuer rationale, timeline, evidence landing paths, BYOXPC account
  and known gaps. State the production allocation invariant supported by M1 and
  integration evidence and the distinction between operational and sandbox state.

Validation for this gate: run the shared admission/transport suites, independent
reader and Swift comparison controls for lifecycle evidence, and relevant limit
contract tests. Run the public CLI ordinary and extension controls on standard
and BYOXPC runners, with `runner_byoxpc` signing, provenance and registry-recovery
cases, `preflight`, and affected build/signing and maximum-reply controls. Keep
the required ordering mutation control current when its governed code changes.

**Completion gate:** on both standard and BYOXPC runners, the public CLI retains
the native lifecycle and three sets of queries/access attempts for one applied
policy and worker, and passes the lifecycle-placement and both ordinary-phase
controls above.
Independent controls identify the target, worker, issuer and worker signing
baselines, and fresh descriptor use. Target preparation and issuer failures remain
inspectable results with no fabricated consumption or release. Interruption
controls preserve unresolved native outcomes and earlier published observations;
the producer and independent readers reject invented completion. The contract
increment above is complete, `source_drift` and `preflight` pass against a
signed build, and neither baseline gained an entry.

Complete and close A1 under [the out-of-band audit rules](#out-of-band-audit-handoffs),
then complete [H1's prepared human review](#human-review) before advancing to M4.

## M4 Failure combinations and adversarial coverage

Extend the shared boundary controls with combined faults, adversarial timing and
inputs, and failures that are difficult to reproduce naturally. Cover material
interactions such as worker death during partial token delivery and validator
timeout followed by late output and unconfirmed cleanup. Include ordinary phase
sequences without extensions and supported mixtures of ordinary actions and
lifecycle interventions, with aggregate limits and unsupported combinations
checked at admission. Extend same-phase and cross-phase placement controls with
native failures and interruption, including specimens that omit consumption or
release. Exercise BYOXPC provenance and registry recovery failures.
Select additional combinations from the implemented boundaries and record what
each establishes. Revisit the interface if these controls expose an unrepresentable
outcome.

Contract increment for this gate: a scenario-matrix row for each combined fault,
read by the live case and the Swift comparison tests; catalog, coverage and
opt-in registry entries for every new case. Each new claim about delivery,
publication, phase association, child cleanup or registry recovery must name
the control establishing it. Update the corresponding architecture entries,
citations and generated views, and any changed failure or public reading rules.

Validation for this gate: run the registered combined-fault cases, independent
reader and Swift comparison controls using their matrix rows, and affected
`failure_boundaries`, worker, witness and `runner_byoxpc` controls. Apply the
shared validation rules to any implementation or interface repairs made here.

**Completion gate:** combined-fault controls retain each independently supported
failure and earlier observation without one fault masking another. Adversarial
timing cannot admit late records to another phase or invent completion, and
malformed or interrupted token delivery preserves token confinement. Producer
and independent-reader checks agree on the supported evidence and withheld
claims for these cases. The contract increment above is complete, `source_drift`
passes against a signed build, and neither baseline gained an entry.

## M5 Completeness checks and integrated acceptance

Check the delivered implementation and documentation as a whole, then establish
acceptance of the final candidate. Each sub-milestone has its own checkpoint row,
gate and rendered assessment. Correct omissions or contradictions through the owning
inputs and generators, rerun affected controls, and recheck changed rendered
views under the shared rules. Earlier milestones own creation of the behavior,
its account and its controls; these checks verify their completeness and agreement.

### M5.1 Evidence contract closure

Check [the failure contract](tests/FAILURE-PROPAGATION-CONTRACT.md), scenario
matrix and shared guide rules against the delivered encoders, consumers and
controls. Review claim ownership, phase ordering, protocol names, worker progress,
lifecycle records and incomplete publication together. Confirm that rules for
phase association and native outcomes retain their meaning across all views.

**Completion gate:** `generator_contract`, `limits_documentation`, the blackbox
checker controls and the Swift comparison tests pass together; every vocabulary
string appears in the encoder, the consumer and the matrix fixture.

### M5.2 Limits account

Check the limits inventory for complete source/value-test ownership and boundary
or path controls. Read the Interactions and Premises in
[docs/LIMITS.md](docs/LIMITS.md), the budget account in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and the guide copy together. Confirm
that the documented interactions of phase and issuer waits with worker/sentinel
and client budgets match implementation, and that values and units agree across
spans, tables and prose.

**Completion gate:** `limits_documentation`, the Swift and C limit contract
tests and `failure_boundaries` pass; the prose baseline gained no entry.

### M5.3 Build and bundle account

Check the delivered build graph, inventories, signing and embedded-evidence
account against the pipeline and read-back. Read BUILD.md,
[docs/SIGNING.md](docs/SIGNING.md), distribution and preflight READMEs and the
build's known gaps together. Confirm that each new refusal has its control and
that the issuer's treatment agrees across standard and BYOXPC installations.

**Completion gate:** `build_documentation` and `preflight/codesign.preflight`
pass, and the opt-in build guard controls pass when refusals changed; the build
baseline gained no entry.

### M5.4 Architecture account

Check [docs/architecture.json](docs/architecture.json) and its rendered graphs,
tables, captions and surrounding prose against the delivered process/channel
boundaries. Review the phase protocol, issuer, token channel, target preparation,
admission and BYOXPC provenance together. Confirm that the timeline, evidence
landing paths, allocation invariant, operational-state distinction and known
gaps agree with implementation evidence. Check the document graph and drift-node
check list against the actual generators and drift rules.

**Completion gate:** `architecture_documentation` and the known-gap,
evidence-channel and core-ideas rules pass; every node and edge cites a test or
rule that exists.

### M5.5 User-facing documentation

Read the delivered [user guide](docs/PolicyWitness.md) and staged copy,
[request-grammar lesson](docs/REQUEST-GRAMMAR.md), corpus and
[FAQ](docs/QUESTIONS.md) as a user would. Check that examples and reading rules
agree on ordinary pairs, extension references and placement, unavailable results,
target evidence and BYOXPC operation. Check linked controller/runner guidance and
the test suite map, READMEs, opt-in registry and catalog for agreement with that
account. Trace behavioral claims to their establishing cases and verify copied
sections against their owners.

**Completion gate:** the full `source_drift` suite passes and the guide stages;
no claim lacks an establishing case.

### M5.6 Integrated acceptance and record

Apply the shared verification and evidence-reuse rules to the final candidate.
Run the signed default battery against the final candidate, the new lifecycle
and ordinary-phase cases, the required ordering mutation control, and BYOXPC
issuer signing, provenance, lifecycle, and older-record recovery controls.
Include the signing/build/maximum-reply controls selected for the delivered changes.
Verify aggregate limits and the largest admitted reply through real transport.

**Completion gate:** PW demonstrates the controlled experiment on standard and
BYOXPC runners under their supported signing environments, all applicable checks
pass against the accepted source and build, and the investigative record identifies
empirical findings, design decisions, and accepted limitations. Predictions may
remain unavailable or unchanged, and release may leave access observable; those
outcomes must remain informative. Report the implementation commits, evidence
locations, and unresolved findings. Packaging or publishing a release is separate
from this implementation plan.

Then complete A2 against this candidate. The plan is complete only after the final
audit closes under [the out-of-band audit rules](#out-of-band-audit-handoffs).

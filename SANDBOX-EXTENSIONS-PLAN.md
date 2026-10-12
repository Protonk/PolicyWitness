# PolicyWitness 0.3.0 sandbox extensions implementation plan

Implement a bounded experiment that observes file sandbox extensions during
one disposable worker's lifetime under one fixed, once-applied SBPL policy.
The result must retain issuance, delivery, consumption, release, phase-specific
predictions, and fresh access attempts as independent observations. Successful
native calls do not establish the worker's effective permissions.

This is the active implementation plan. Update its checkpoint and milestone
status as work proceeds. It carries the requirements of the initial agent brief;
the brief is retired. Current behavior remains defined by the repository's
contracts until each implementation increment changes them.

## Execution mandate

When instructed to execute this plan, implement M0 through M5.6 and complete
their acceptance checks. Milestone gates are evidence checks to evaluate autonomously.
When a gate passes, update the checkpoint, commit a coherent verified increment,
and proceed without requesting routine milestone approval. Diagnose and repair
failures before advancing dependent work. Progress reports communicate findings
and do not end execution while authorized work remains.

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
Never satisfy a gate by weakening its evidence requirements. Continue independent
work while a decision or required access is pending, preserving the evidence and
the exact condition blocking dependent work.

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
| M4 Failure combinations and adversarial coverage | Pending | Requires M3; extends the boundary controls already required in M2 and M3, plus the M4 contract increment |
| M5.1 Evidence contract closure | Pending | Requires M4 |
| M5.2 Limits account | Pending | Requires M5.1 |
| M5.3 Build and bundle account | Pending | Requires M4; independent of M5.1 and M5.2 |
| M5.4 Architecture account | Pending | Requires M5.2 and M5.3 |
| M5.5 User-facing documentation | Pending | Requires M5.4 |
| M5.6 Integrated acceptance and record | Pending | Requires all preceding milestones |

Each gate includes its [rendered documentation assessment](#rendered-documentation-assessment)
waypoint and the lead agent's disposition of the findings.

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
- Documentation here is generated and checked: five generators, four manifests,
  the comparison scenario matrix, two baselines, two shape goldens and the drift
  rules, with every generator's check run by the build before compiling. Their
  preconditions are listed under
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

The repository's documentation is machinery. Five generators with `--check`,
run by `build.sh` before compiling, render four hand-owned manifests
([architecture](docs/architecture.json), [build](docs/build.json),
[contract](docs/contract.json) and [limits](docs/limits.json)) and the
comparison [scenario matrix](tests/fixtures/comparison/matrix.json) into marked
regions; the prose and build baselines list what those mechanisms do not yet
cover; two shape goldens are the allowlists the independent consumer reads; and
the drift rules in [check.py](tests/suites/source_drift/check.py) compare
handwritten text with sources. Each has a precondition that only code or tests
can satisfy: an architecture node must cite an existing test or rule and may
state a duration only through a limit placeholder; a limit must cite its source
symbol and a value test in a listed owner file; a reply key reaches readers only
through the field-complete fixture that records it; the signing list must agree
with the artifact inspector, the evidence generator and the README inventory at
once; and the native_check build step pins every Meson target by name. A signed
build already refuses a stale copy or a build manifest that disagrees with
`build.sh`.

Every milestone gate from M2 onward therefore includes a signed build and a
passing `source_drift` suite, and neither baseline gains an entry. These checks
establish agreement within their coverage. Rendered documentation assessment at
each gate checks for missing coverage, misleading accounts and evidence gaps;
corrections needed by the increment belong to that gate.

| Gate | Forced by | Increment owed |
| --- | --- | --- |
| M2 | the response bump, the consumer allowlist, the layout golden, the drift rules | the contract manifest and its generated copies; the response shape golden from the field-complete fixture; the ABI header with its static assert, the layout golden and the identity together; every new `limitations` or lifecycle vocabulary string in the encoder, the consumer and the matrix fixture in one commit; the test-override table for new seams; COVERAGE rows for new outcome values; the failure contract's ordering-states, protocol-names and worker-evidence prose |
| M3 | the native_check build step, `build_documentation`, `preflight`, registry read-back | the issuer's Meson target in `tests/lib/native_sources.py`; its `build.sh` signing call with `build.json`, regenerated BUILD.md, the README inventory, `tests/lib/artifact.py` and `tests/build-evidence.py`; limits rows with value owners for every new cap, wait and byte bound; attempt-kind enum agreement and a COVERAGE row for any new action; request-contract corpus examples for each new refusal code; the registry's issuer fields in the guide's BYOXPC section |
| M4 | matrix ownership, architecture citations | a scenario-matrix row for each combined fault, read by the live case and the Swift comparison tests; the tests that M5.4's architecture nodes will cite; catalog, coverage and opt-in registry entries for every new case |

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
  The manifest grows per milestone and is reviewed whole in M5.4.
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
| M3 | Generated build/signing inventories, limits, topology and boundary views, plus their guide copies: issuer authority, BYOXPC provenance, token handling, placement caps and new refusals have complete owners and supporting controls. |
| M4 | Rendered combined-fault matrix, coverage and architecture citations: partial and unresolved outcomes remain visible; cited controls support each claimed boundary rather than merely existing. |
| M5.1 | Completed evidence account and copied reading rules: lifecycle records, phase ordering, vocabulary and consumer meaning agree across generated and handwritten regions. |
| M5.2 | Limits tables, spans and copied budget explanations: value owners, units and interactions describe the implemented waits and transport bounds without unsupported arithmetic or guarantees. |
| M5.3 | Build graph, inventories, signing/evidence tables and surrounding operating guidance: the issuer and refusal/cleanup paths are represented consistently. This review can proceed independently of M5.1 and M5.2. |
| M5.4 | Rendered architecture graphs and their tables, captions and prose as a whole: process/channel boundaries and operational-state claims are consistent, legible and supported by the cited observations. |
| M5.5 | Rendered user guide and its staged copy, grammar, FAQ and linked operating guidance: public examples, unavailable results and capability refusals read consistently with the implemented contract. |
| M5.6 | Reconcile prior findings with the accepted source/build and rendered artifacts; review changed surfaces since their last assessment and confirm credited reviews still apply to this candidate. |

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
  ordinary one-phase authoring path. Decide request and response version changes
  through [the wire contract](docs/CONTRACT.md); change the envelope version only
  if its reading rules require it.
- Implement phase arrival, collection closure, release, acknowledgement, and
  terminal handling in C and Swift. Associate predictions and comparisons with
  the correct phase. Apply the phase-local eligibility rules above and preserve
  unavailable queries separately from access attempts.
- Bound phase count, total actions/queries, publication storage, and total
  collection time as well as individual waits. Specify how phase waits interact
  with worker execution, cleanup, exec budgets, and the client RPC timeout.
- Update producers and independent readers together, including lifecycle
  interpretation, shape fixtures, ABI layout, and generated worker identity.
- Use independently observed file effects and held validator gates to establish
  that actions cannot run early and later queries follow completed interventions.
  Include stale/wrong-phase acknowledgement, interrupted collection, worker death,
  and missing-prediction controls. A missed boundary or premature worker death
  must not produce a fictitious completed phase. Extend and run
  `witness_contract/order_barrier_mutations` whenever its governed code changes.

Contract increment for this gate: bump the response contract and regenerate its
copies. In the same bump rename the three reply keys named `phase` to `stage`
and update their readers, fixtures and descriptions. Record every new reply key
in the field-complete fixture and the shape golden. Change the ABI header and
its static assert, the layout golden and the identity together, and replace the
failure contract's literal offsets with a citation of the layout golden. Add
each new `limitations` or lifecycle vocabulary string to the encoder, the
consumer and the matrix fixture in one commit. Extend the test-override table
for new seams and add COVERAGE rows for new outcome values. Rewrite the
ordering-states and protocol-names tables for phases. Fixture directories are
named by response version, so the bump creates the new version's directories
rather than editing retained ones.

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

Contract increment for this gate: add the issuer's Meson target to
`tests/lib/native_sources.py`, and its signing call to `build.json`, the README
inventory, `tests/lib/artifact.py` and `tests/build-evidence.py`, then
regenerate BUILD.md. Give each new build refusal a behavioral control. Add
limits rows with value owners for the declaration and action caps, the phase
and action bounds, token size and issuer waits. Keep the attempt-kind enums in
agreement and add a COVERAGE row for any new action. Add request-contract corpus
examples for each new refusal code, including the capability refusal. Record the
registry's issuer fields and the capability refusal in the guide's BYOXPC
section. Add the topology, boundary and BYOXPC architecture nodes whose tests
now exist.

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
opt-in registry entries for every new case; and the remaining tests that M5.4's
architecture nodes will cite.

**Completion gate:** combined-fault controls retain each independently supported
failure and earlier observation without one fault masking another. Adversarial
timing cannot admit late records to another phase or invent completion, and
malformed or interrupted token delivery preserves token confinement. Producer
and independent-reader checks agree on the supported evidence and withheld
claims for these cases. The contract increment above is complete, `source_drift`
passes against a signed build, and neither baseline gained an entry.

## M5 Residual account and integrated acceptance

Each preceding increment closes its documentation correctness findings at its
gate. M5 completes the remaining explanations, whole-document views and acceptance
run in six sub-milestones: readers before limits, limits before architecture,
tests before manifests, settled syntax before user prose. Each has its own
checkpoint row, gate and documentation assessment waypoint. Apply the generator
ownership rules before expanding handwritten sections, including any generator
coverage gaps found here. Regenerate through the owning tools and review layout,
identity, diagrams and shape changes at every step. Across the six, cover public
ordinary and extension phases, lifecycle placement and action limits, target
resolution and metadata evidence, and BYOXPC issuer signing, capability refusals
and registry recovery.

### M5.1 Evidence contract closure

Rewrite the handwritten sections of
[the failure contract](tests/FAILURE-PROPAGATION-CONTRACT.md): the claim and
evidence review, the ordering states with the phase dimension, the protocol
names, the worker evidence operations and progress table, a lifecycle event
record section, and the ownership table. Complete the scenario matrix and
regenerate it. State the consumer's rules for phase association and lifecycle
records beside the existing comparison rules, and keep the shared reading rules
that the generator copies into the guide current.

**Completion gate:** `generator_contract`, `limits_documentation`, the blackbox
checker controls and the Swift comparison tests pass together; every vocabulary
string appears in the encoder, the consumer and the matrix fixture.

### M5.2 Limits account

Give every new bound a limits row with a value owner and a boundary or path
check. Rewrite the Interactions and Premises prose in
[docs/LIMITS.md](docs/LIMITS.md) and the budget paragraph in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for per-phase waits against the
sentinel and client windows. Replace every new number in prose with a span and
regenerate the guide's copy.

**Completion gate:** `limits_documentation`, the Swift and C limit contract
tests and `failure_boundaries` pass; the prose baseline gained no entry.

### M5.3 Build and bundle account

Review what the M3 increment forced. Update the BUILD.md prose for the signing
contract and the embedded evidence, [docs/SIGNING.md](docs/SIGNING.md), the
distribution and preflight READMEs, and the build's known gaps. Confirm each new
refusal has its control.

**Completion gate:** `build_documentation` and `preflight/codesign.preflight`
pass, and the opt-in build guard controls pass when refusals changed; the build
baseline gained no entry.

### M5.4 Architecture account

Complete [docs/architecture.json](docs/architecture.json): the issuer and the
token channel in the topology; the token channel record, the target preparation
and extension admission guards and the issuer evidence in the boundaries; issuer
signing, read-back and provenance in the BYOXPC apparatus; any new region or
rule in the document graph, with the drift node's check list equal to what
`check.py` runs. Then the prose: why the issuer exists, the run timeline, the
evidence-channels table with the new landing paths, the principles including the
resolved allocation claim and the operational-state distinction from
[Scope and constraints](#scope-and-constraints), the BYOXPC section and the
known gaps.

**Completion gate:** `architecture_documentation` and the known-gap,
evidence-channel and core-ideas rules pass; every node and edge cites a test or
rule that exists.

### M5.5 User-facing documentation

Update the [user guide](docs/PolicyWitness.md): specimen format with phases and
the extension declaration, per-step and lifecycle shapes, attempt kinds, BYOXPC
install, registry fields and the capability refusal, and the FAQ answer on
extensions in [docs/QUESTIONS.md](docs/QUESTIONS.md) that the generator copies
in. Update the [request-grammar lesson](docs/REQUEST-GRAMMAR.md) and its corpus,
the controller and runner READMEs and AGENTS files, the tests suite map, the
suite READMEs, the opt-in registry and the catalog. Every claim names the case
that establishes it.

**Completion gate:** the full `source_drift` suite passes and the guide stages;
no claim lacks an establishing case.

### M5.6 Integrated acceptance and record

Follow [test guidance](tests/AGENTS.md) throughout for output ownership, evidence
provenance and reuse, locking, cleanup, and sandboxed-harness retries. For changed
admission and transport, run `failure_boundaries`, `runner_unit`, `runner_abi_layout`,
`runner_c_worker_harness`, and `unit`, plus affected validator and witness cases.
Run the signed default battery against the final candidate, the new lifecycle
and ordinary-phase cases, the required ordering mutation control, and BYOXPC
issuer signing, provenance, lifecycle, and older-record recovery controls.
Select signing/build/maximum-reply controls when their boundaries changed.
Verify aggregate limits and the largest admitted reply through real transport.

**Completion gate:** PW demonstrates the controlled experiment on standard and
BYOXPC runners under their supported signing environments, all applicable checks
pass against the accepted source and build, and the investigative record identifies
empirical findings, design decisions, and accepted limitations. Predictions may
remain unavailable or unchanged, and release may leave access observable; those
outcomes must remain informative. Report the implementation commits, evidence
locations, and unresolved findings. Packaging or publishing a release is separate
from this implementation plan.

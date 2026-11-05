# Plan: consolidate sandbox extensions on actors

## Intended result and scope

Make actor operations the sole current request and execution model for sandbox
extensions. Introduce it with an issuer/subject specimen: issue, transfer,
consume, observe fresh access, and release. Re-delegation extends that same
model. Remove the top-level extension declaration form and its separate
issuance machinery after resolving the meaningful authority differences.

This is a production implementation and contract change, including signing,
admission and evidence interpretation. It is not a documentation-only rewrite.
The ordinary single-worker form remains available for specimens without
extensions; converting all ordinary specimens to actors is outside this plan.
Actors without extension operations remain supported.

Maintenance is strictly at the frontier. Once an affected schema advances,
current producers, readers, tests and documentation target that schema alone.
There will be no older-request adapter, compatibility execution branch,
historical semantic reader, maintained converter or version negotiation.
Preserved releases and evidence keep their original bytes and provenance;
cross-version correlation is the user's research problem. The shared answer in
[QUESTIONS](../docs/QUESTIONS.md) and the
[supported-version contract](../docs/CONTRACT.md#supported-versions) express
this policy.

This plan is ready to begin design work. Broad implementation follows the
contract review at the end of Stage 2. The authority configuration below is a
recommendation to make concrete and review, not an already accepted wire shape.
Plan preparation inspected source and test assertions at
`0e3f5e6b20d950691991640376ee575b89590986`; it establishes no new native behavior.
At execution, refresh that baseline rather than assuming the tree is unchanged.

The plan lives in `runner/` because the host orchestration, request/reply types
and worker protocol are its central owners. The
[runner guidance](AGENTS.md) also covers native helpers under `controller/tools/`.

## Decisions and boundaries

The accepted direction is one extension mechanism, expressed through actors,
with explicit authority and evidence. Preserve the ability to study an issuer
without supplied entitlements and a subject with supplied entitlements in the
same specimen. Preserve sandboxed issuance and re-delegation as well. A small
set of actor equipment choices within one model is different from maintaining
separate extension forms and execution engines.

Use the actor schedule and submitted absolute target path as the proposed
canonical behavior. Do not silently reproduce declaration-time target
resolution or the helper's exit-before-subject lifetime. Eager actor setup and
overlapping process lifetimes remain the default, with requested actions in a
serial schedule. Pursue an observed-termination dependency as the narrow
lifetime candidate below: it belongs to host scheduling, not to the extension
operation vocabulary. Deferred subject launch/setup and coordinated issuer
liveness need their own concrete specimen questions before expanding scope.
Historical equivalence alone is not a requirement.

Keep one way to express and execute extension experiments. Setup, evidence
collection and cleanup are PW's responsibility; users should not choose a
transport implementation or a diagnostic mode to obtain complete observations.
An explicit experimental ordering dependency does not select another execution
engine. Expose additional choices only when the witnessing requirement makes
them necessary.

Keep the repository's [core ideas](../AGENTS.md#core-ideas): fresh processes,
sandbox calls outside the host, observations supporting effects, collection
before attempts, and literal attribution. Token bytes remain transient and
absent from requests, replies, logs and diagnostics. Removal of the declaration
path must not weaken actor custody, delivery settlement or cleanup ownership.

New extension families, concurrent actor execution, arbitrary per-actor binary
plugins, changes to the native call flags, footprint optimization, release
publication and general registry redesign are outside this plan. If the
minimal authority design needs one of these, return to review with the concrete
reason and alternatives rather than absorbing it into implementation.

Frontier-only run support does not authorize stranding an already installed
runner or deleting resource-recovery records. Keep list, reconcile and owned
removal usable for unsupported installations, as the wire contract already
requires. This preserves cleanup ownership, not historical execution support.

## Source facts that constrain the design

| Present behavior | Grounding | Consequence |
| --- | --- | --- |
| A declaration prepares its target, issues before worker creation, and requires the issuer's confirmed reap before delivery. | [CWorkerOrchestrator.swift](Sources/PWRunnerCore/CWorkerOrchestrator.swift), [ExtensionIssuer.swift](Sources/PWRunnerCore/ExtensionIssuer.swift), [native issuer](../controller/tools/pw_probe_runner/pw_extension_issuer.c). | Declarations are not merely alternate syntax for an actor schedule. Remove or deliberately replace these observations and failure paths. |
| Declaration preparation resolves the submitted target and records resolved-path metadata. Actor issuance passes the submitted absolute target unchanged. | [ExtensionIssuer.swift](Sources/PWRunnerCore/ExtensionIssuer.swift), [ActorTranslation](Sources/PWRunnerCore/ActorOrchestration.swift), [extension coverage](../docs/EXTENSIONS.md). | Choose the target semantics explicitly; do not add a hidden host resolution step to make old tests pass. |
| Actor translation currently supplies the same selected worker executable to every actor. An unapplied actor skips specimen policy application, not its binary's entitlements. | [ActorOrchestration.swift](Sources/PWRunnerCore/ActorOrchestration.swift), [actor types](Sources/PWRunnerCore/PWRunnerActors.swift), [BYOXPC actor controls](../tests/CHANGE-VERIFICATION.md#byoxpc-actor-controls). | The current actor request cannot express every declaration issuer/subject authority arrangement. |
| BYOXPC signing gives supplied entitlements to the worker and enclosing service, while the validator and declaration issuer receive the signing identity alone. | [signing implementation](../controller/src/runner_manager.rs), [signing account](../docs/SIGNING.md#what-buildsh-signs). | Replacing the helper with another invocation of the selected entitled worker can change the observed authority. Verify actual signed equipment. |
| The scheduler launches actors and resolves setup before walking the serial schedule. Parked actors can receive apparatus deliveries while their requested actions wait. | [ActorScheduler.swift](Sources/PWRunnerCore/ActorScheduler.swift), [ActorSession.swift](Sources/PWRunnerCore/ActorSession.swift), [AuthorityCustody.swift](Sources/PWRunnerCore/AuthorityCustody.swift). | Keep issuance, delivery and consumption distinct. A helper lifetime cannot be inferred from an actor's final scheduled action. |
| Actor references, resource states, budgets and reply ownership differ from declaration records. | [ActorPlan.swift](Sources/PWRunnerCore/ActorPlan.swift), [actor records](Sources/PWRunnerCore/PWRunnerActors.swift), [extension records](Sources/PWRunnerCore/PWRunnerExtension.swift), [limits](../docs/LIMITS.md). | Remove obsolete contracts together with their producers and readers; review surviving shared types before deleting a declaration-named file. |
| Actor authority setup retains status/stage but loses native and cleanup observations that declaration setup records; the actor reply does not expose a complete per-actor setup account. | `prepare_authority` and `prepare_extension` in the [native worker](../controller/tools/pw_probe_runner/pw_probe_runner.c), [ActorSession.swift](Sources/PWRunnerCore/ActorSession.swift), [ActorOrchestration.swift](Sources/PWRunnerCore/ActorOrchestration.swift). | Consolidation needs positive evidence work, not only removal. Use one automatic setup account; no observed macOS requirement calls for alternate user-facing setup modes. |

Source locations identify mechanisms. Test descriptions identify candidate
controls; neither substitutes for inspecting assertions and executing an
applicable control on the candidate.

## Stage 1 — resolve the authority and observation contract

Refresh the current source, build and test baseline. Inventory active callers
of declaration admission, preparation, native operations, reply interpretation
and helper installation. Follow shared symbols rather than deleting by filename
or by a broad search for “extension”. Record the baseline commit, dirty delta
if any, selected app identity and the applicable contracts.

Make the preferred authority design concrete: package narrowly scoped variants
of the same C worker implementation, one without supplied entitlements and one
with the selected runner's entitlements. Both use the actor protocol. Resolve
these questions in the design packet:

- The request spelling, default and admitted choices for actor equipment;
  how equipment selection composes with `apply` and `unapplied`; and what the
  choices mean for the built-in runner, where entitlements may coincide.
- Which signed bundle owns each executable, how the host resolves it, and how
  build and BYOXPC installation sign and validate it. No implicit substitution
  when the selected equipment is missing, stale or cannot be verified.
- How selected equipment, actual executable identity and entitlement read-back
  are associated with each actor in provenance. Distinguish requested equipment,
  inspected bytes and observed process execution; a selector alone proves none
  of them.
- How runner selection and entitlement requirements apply when actors use
  different equipment. A requirement checked against the selected runner's
  usual worker cannot be credited to an actor using the other variant.
- How direct XPC admission obtains and validates the same meaning, and how
  current test overrides select equipment without bypassing the property a
  control claims to establish.

Inspect the applicable
[native lifecycle controls](../tests/CHANGE-VERIFICATION.md#native-sandbox-extensions)
before choosing authority or issuer-lifetime assumptions. Use existing evidence
only under the repository's applicability rules; otherwise run the relevant
controls. Where source inspection cannot settle inherited restrictions or
signing behavior, use an isolated, signed prototype and retain its exact inputs,
native observations and cleanup. Do not credit a constructed reply or a signature
read-back alone as proof of a live authority configuration.

Separately decide which declaration observations remain useful. The proposed
disposition is actor-time issuance on the submitted path, actor lifetime under
the scheduler, actor-native missing-symbol/unavailable records, and actor-indexed
evidence. Evaluate resolved-target identity and issuer-exit observations on
their own merits. Any retained feature needs an explicit actor operation or
evidence rule, or a host scheduling condition for process ordering, with a
bounded implementation; it must not reintroduce a hidden declaration
preparation engine. Process-lifetime dependencies do not become extension
operations.

### Unified setup evidence

The accepted direction is one automatic, bounded account of authority setup
and its cleanup, with the same observation conventions for host and worker
operations. Users choose experiment inputs and equipment; they do not choose
between setup implementations or enable diagnostics to obtain these facts.
This is PW evidence handling. It does not promise that macOS will supply every
native extension operation or that a successful setup establishes authority.

Carry these requirements into the Stage 2 contract packet:

- Identify the producing owner, applicable actor/resource and setup stage.
  Host authority-region creation and worker mapping are separate operations on
  separate references. Keep run-wide host preparation at its actual scope;
  do not manufacture a worker observation or duplicate one as several actors'
  independent results. Preserve each attempted actor's facts even when another
  failure supplies the run's summary disposition.
- Preserve the primary native return and immediately saved errno where that
  call's contract gives errno meaning. Later `close` or `munmap` must not
  overwrite it. A successful `fstat` followed by a size/header rejection is a
  validation rejection, not a failed syscall with fabricated errno. Record
  independent cleanup outcomes alongside the primary observation, retaining
  their native return and immediate errno where applicable, including cleanup
  after successful acquisition; distinguish unattempted or unobserved
  work from success. Retain ownership when cleanup remains unresolved.
- Specify how worker facts become published and eligible for host reading,
  including failure before normal actor setup completion. Fields written into
  a mapping without the required publication are not evidence. Host-produced
  setup facts do not depend on a worker publication that never occurred.
  Early inability to create reporting apparatus must remain representable by
  the surviving host reply path, without pretending the worker reported it.
- Keep observation eligibility separate from scheduling eligibility. Failed,
  incomplete or late setup must not enable a visit, but still permits valid
  setup/cleanup observations. A late application publication can remain a fact
  without changing a host setup timeout. Required authority setup failure takes
  the terminal pre-application path specified below; its published refusal
  establishes that the worker did not attempt specimen policy application.
- Retain independently observed issue, consume and release symbol availability.
  Availability is not a native operation result or proof of effective authority;
  an unavailable operation must not suppress unrelated supported operations.
  Keep these observations separate from mapping/validation outcomes and from
  subsequent issue, transfer, consume and release evidence.
- Define applicability for actors without authority operations: current setup
  still checks symbols and attempts the core-limit change, while an absent
  authority descriptor is tolerated when none was expected. Missing required
  apparatus and apparatus that was never required must remain distinguishable.

Bound the work to authority preparation, its acquired references and their
cleanup, plus the publication and reply paths needed to carry those facts.
Inventory calls in `prepare_authority`, [AuthorityCustody](Sources/PWRunnerCore/AuthorityCustody.swift)
and the relevant [ActorSession](Sources/PWRunnerCore/ActorSession.swift) paths.
Do not expand this into a generic native-call event log or a redesign of every
worker resource. Reuse existing native result, saved-errno and publication
conventions where their meanings fit; the single generic failure record alone
cannot represent a primary failure and independent cleanup failures. Choose
bounded storage and its C/Swift layout, reply shape, limits and reader rules
together. No exact field spelling or new publication mechanism is selected by
this plan.

### Terminal setup boundary and failure meanings

Make failure of required worker authority apparatus terminal immediately after
authority preparation, before policy reading, compilation, capture or
application. Publish the reached setup observations, perform and record the
applicable cleanup, and exit through a path that cannot return to policy
processing or visits. Publication must identify the terminal decision even
when cleanup is incomplete; cleanup completion and process reap retain their
own observations. The host resolves this refusal without waiting for an
applied/unapplied setup publication. This is an automatic worker control-flow
rule, with no additional host permission handshake or user mode.

This changes the current `prepare_authority` path, which returns after recording
failure and permits `main` to continue to application. Keep per-operation symbol
availability separate: a missing issue, consume or release symbol retains its
operation-specific unavailable result. Specify which apparatus is required
for each actor under the applicability rule above. An absent descriptor that
was never required remains an ordinary setup condition.

Tie each failure account to the boundary its observed path establishes. Use
these distinctions in producers, readers, tests and documentation rather than
assigning one meaning to every `setup_failed` summary:

| Observed boundary | Established flow and evidence |
| --- | --- |
| Host authority preparation refuses before actor launch | No actor worker is launched. Preserve the host's native/validation and cleanup facts and the resulting launch refusals. |
| Worker publishes a terminal required-authority refusal | That worker takes the cleanup/exit branch before specimen policy processing. Preserve the setup refusal and independent cleanup outcomes; record application as not attempted, with no native apply result. |
| Worker publishes a terminal header/input, parameter or compilation refusal | The existing terminal branch excludes the later application call. Identify the reached stage and its actual result instead of presenting a synthesized `apply_rc` as a native application result. |
| Host setup deadline expires after launch | The deadline closes visit eligibility. Retain worker facts that become observable later, including application when published, beside that scheduling decision. |
| Ready-byte reporting or optional profile capture fails | The current worker continues toward application. Preserve the failed auxiliary observation and the separately observed application outcome. |
| Application is entered but its result is unpublished | Retain eligible call-entry evidence and classify the result as unobserved. A published native return, successful application publication and process termination each supply their own facts. |

Ground a terminal-refusal claim in the worker publication and the branch that
excludes application, with independent controls at the application call
boundary. An absent application publication instead means application was not
observed. `done` and reap retain their completion/termination meanings; neither
identifies the refusal stage by itself. These statements concern the specimen
policy call in the named worker; inherited restrictions and signed entitlements
remain part of its starting context.

### Lifecycle decision packet

Prepare this compact packet next, before selecting API syntax or simplifying
the architecture documentation. Carry the agreed semantic decisions into the
Stage 2 contract packet. The candidate below is for review, not an implemented
or fully specified request feature.

**Default and retired guarantees.** Resolve launch/setup for the actor
population before walking the serial schedule; resolution includes failure,
and does not promise successful setup of every actor. Parked actors can
service deliveries without running requested native actions. Successful visits
advance after observed phase completion without a prerequisite issuer reap.
Failed visits separately establish quiescence before further activation, or
cancel remaining activation under the existing failure rules. Actors may
publish terminal completion and exit after their own last visit, and resource
cleanup can occur during the schedule. Do not imply survival until final
cleanup. Retire the declaration path's automatic clean issuer reap before
delivery and before subject creation; a new termination dependency does not
restore that creation order.

| Witnessing requirement | Required mechanism | Disposition |
| --- | --- | --- |
| Subject consumes after issuer termination | Confirmed reap of the issuing actor before eligibility of the dependent subject visit. | Pursue as the narrow host-owned dependency candidate. Place the gate before visit activation and query collection so predictions as well as actions follow the observation. |
| Subject starts or applies its policy after issuer termination | Deferred subject launch or setup. | Outside this consolidation unless a concrete specimen question warrants a reviewed scope change. Eager setup plus a visit gate does not establish this observation. |
| Subject consumes while issuer remains alive | Deliberate lifetime coordination with observations supporting liveness during the relevant interval. | Outside this consolidation unless a concrete specimen question warrants a reviewed scope change. Ordinary visit order or absence of a reap is insufficient. |

**Candidate dependency.** Associate a later visit with the host's observed
termination of another actor after that actor's final visit. Admit only a
dependency whose referenced actor has no remaining visits when the gate is
reached; otherwise waiting could require an activation the gate prevents.
Issue, transfer and consume retain their existing meanings. Decide whether
the required condition is termination or clean completion: an observed reap
after an abnormal exit establishes the former, not the latter. Retain exit
status and termination observations separately whichever condition is chosen;
do not add both as user-selectable modes merely to avoid this decision.

**Failure and evidence.** Specify the gate's bounded wait, budget accounting,
ownership requirements and effect on subsequent scheduling. Timeout or lost
ownership leaves the dependent visit ineligible, without its collection or
release. A reap observed later during cleanup cannot retroactively satisfy
that gate. Observe natural termination through the child-observation boundary;
do not call `requestExit`/`finishCleanup` in
[ActorSession.swift](Sources/PWRunnerCore/ActorSession.swift) to make the condition
true, since those paths request departure and may terminate the process. Record the dependency,
the owned child observation, the gate's terminal outcome and its relation to
visit eligibility. A final `reaped` flag or a worker's `done` publication alone
does not establish that relation. Delivery settlement and recipient storage
ownership remain independent prerequisites and observations.

**Specimen question and controls.** Use an issuer/subject specimen asking
whether the subject observes fresh access after the issuing process naturally
terminates: both actors set up eagerly; the subject records baseline access;
the issuer issues and transfers in its final visit; the host gates the
subject's consuming visit on the selected termination condition; a later phase
collects queries before fresh attempts; release and another fresh-access
observation follow. Gate success establishes ordering, not native consumption
success or access persistence. Include natural exit, phase completion and
`done` publication while the process remains alive, an abnormal reaped exit,
and gate timeout followed by successful cleanup. Removing the gate must fail
an independent ordering assertion. The native `issuer_exit` scenario in
[sandbox_extensions_native](../tests/suites/sandbox_extensions_native/README.md#controls)
is supporting evidence for its own arrangement, not proof of this integrated
scheduler guarantee.

### Open design decisions

The following details still require contract review. Setup evidence has the
accepted requirements above; the lifecycle packet fixes the default and
candidate scope. Their representations and remaining choices stay open.
The simplification and test work below does not authorize resolving them
implicitly by deleting evidence or copying
old expectations into actor tests. Include their dispositions in the Stage 2
review packet before implementing dependent changes.

| Decision | Current concern | Required disposition |
| --- | --- | --- |
| Actor authority-setup evidence representation | One automatic account must retain primary native, independent cleanup, per-operation availability and per-actor facts, with host/worker ownership intact. Required worker apparatus failure now has an accepted terminal boundary before policy processing. | Specify the bounded layout, publication boundary, reply landing paths and independent-reader rules implementing those requirements, including host recognition of terminal refusal before normal actor setup completion. Inventory and replace old failure assertions; do not reopen evidence retention or terminal flow by silently deleting them. |
| Normalized execution instructions | `ActorTranslation` reconstructs references from optional strings, substitutes index zero for missing relationships and uses a default release branch. Equipment selection would add another resolved relationship. | Decide how the admitted plan represents operation operands and selected equipment, and how an inconsistent internal plan fails. No new representation or fallback policy is selected by this plan yet. |
| Lifecycle and ownership | Eager setup, overlapping lifetimes and serial visits remain the default. The candidate adds an observed-termination dependency before a later visit, with no new extension operation or deferred subject setup. | Complete the lifecycle packet: choose termination versus clean completion, specify wait/eligibility evidence and failure behavior, and settle actor erasure assertions. Review one run in time in [ARCHITECTURE](../docs/ARCHITECTURE.md) and its [generator input](../docs/architecture.json), showing exit and cleanup during visits as well as remaining cleanup afterward. |

**Exit:** a proposed authority arrangement grounded in the actual signing and
launch paths, a disposition for each meaningful declaration-only observation,
and identified controls capable of distinguishing the proposed arrangements.
If the narrow worker-variant approach cannot establish the required authority,
bring the failed observation and alternatives to the contract review.

## Stage 2 — prepare the contract and removal packet

Produce a packet an executor can implement without reconstructing this
conversation. Include:

1. A complete proposed request and representative reply for the basic
   issuer/subject specimen. Put the subject's baseline read before consumption;
   collect post-consume queries in a later phase before fresh attempts; retain
   release results and a later fresh-access observation without promising
   revocation. Mark draft-only fields as proposals until accepted.
2. The same model under BYOXPC with an unentitled issuer and entitled subject,
   plus a sandboxed issuer/re-delegation example. Explain how the ordinary
   example grows into these cases without choosing another extension form.
3. Field ownership, defaults, invalid combinations, refusal paths and evidence
   eligibility, including missing equipment, unavailable native operations,
   failed setup, incomplete transfer and partial cleanup. Specify the removal
   of the top-level declaration field, including its old null spelling, and
   declaration-only action operands and overrides. Current-schema attempts to
   use removed fields must be refused, not ignored or translated.
4. A contract-version decision using
   [CONTRACT.md](../docs/CONTRACT.md#when-a-number-moves). The request removal
   requires a request bump, and removal of declaration reply fields requires a
   response bump. Decide the envelope version from changed dossier/provenance
   reading rules. Change the runner protocol only if its control/capture
   contract changes. The manifest owns the actual values; internal worker
   changes require regenerated source identity, not a compatibility layer.
5. A disposition ledger for code, tests and documentation: remove, adapt to the
   actor path, or retain with its still-current purpose. For each removed
   behavioral control, identify its replacement assertion or the retired
   behavior that makes it obsolete. List any new controls and their owners.
6. The reviewed lifecycle packet: deliberately retired guarantees, default
   actor ordering, the proposed host termination dependency and its specimen,
   failure/evidence rules and decisive controls. Settle those meanings before
   choosing the dependency's wire syntax or rewriting the temporal account.
7. The unified setup account: bounded primary/cleanup/capability records,
   ownership, publication and eligibility rules, and representative failed-setup
   replies retaining multiple actors' observations. Specify terminal setup
   refusal separately from host timeout, auxiliary reporting failure and native
   application failure. Include a documentation
   claim ledger for the affected WORKER and ARCHITECTURE regions, using the
   execution guidance below; distinguish supported assertions from source-only
   facts and remaining gaps.

Use the following map to start the ledger, then close it over references found
in the current tree:

| Area | Starting owners | Work to account for |
| --- | --- | --- |
| Admission and request preparation | [PWRunnerRequest.swift](Sources/PWRunnerCore/PWRunnerRequest.swift), [ProbeRunner.swift](Sources/PWRunnerCore/ProbeRunner.swift), [CWorkerRequestPlanning.swift](Sources/PWRunnerCore/CWorkerRequestPlanning.swift), [ActorPlan.swift](Sources/PWRunnerCore/ActorPlan.swift), [request_patch.rs](../controller/src/request_patch.rs), [runner_select.rs](../controller/src/runner_select.rs). | Remove declaration admission and add the reviewed actor equipment contract; retain bounded diagnostics and version-first refusal. |
| Orchestration and native operations | [CWorkerOrchestrator.swift](Sources/PWRunnerCore/CWorkerOrchestrator.swift), [ExtensionIssuer.swift](Sources/PWRunnerCore/ExtensionIssuer.swift), [ActorOrchestration.swift](Sources/PWRunnerCore/ActorOrchestration.swift), [ActorSession.swift](Sources/PWRunnerCore/ActorSession.swift), [native worker directory](../controller/tools/pw_probe_runner/). | Remove the separate issuer, transient declaration channel and declaration-specific handle/dispatch paths; preserve shared worker behavior and actor custody. |
| Reply producers and readers | [PWRunnerExtension.swift](Sources/PWRunnerCore/PWRunnerExtension.swift), [PWRunnerActors.swift](Sources/PWRunnerCore/PWRunnerActors.swift), [PWRunnerReply.swift](Sources/PWRunnerCore/PWRunnerReply.swift), [runner_client.rs](../controller/src/runner_client.rs), [disposition.rs](../controller/src/disposition.rs), [dossier.rs](../controller/src/dossier.rs), [consumer.py](../tests/lib/consumer.py), [extension_evidence.py](../tests/lib/extension_evidence.py). | Remove obsolete records and eligibility branches; associate per-actor equipment and evidence consistently in Swift, Rust and independent Python readers. |
| Build, signing and installation | [build.sh](../build.sh), [meson.build](../meson.build), [Package.swift](Package.swift), [app_layout.rs](../controller/src/app_layout.rs), [runner_manager.rs](../controller/src/runner_manager.rs), [build-evidence.py](../tests/build-evidence.py). | Replace the issuer inventory with the accepted worker equipment; update signing, validation, provenance, source lists and artifact controls together. |
| Limits and contracts | [contract.json](../docs/contract.json), [limits.json](../docs/limits.json), [ABI golden](../tests/fixtures/contract/abi_layout.txt), [worker identity generator](../docs/generate_worker_identity.py). | Delete obsolete bounds, ground new ones independently, review reply/transport sizing, and regenerate owning outputs. |
| Tests and fixtures | [test catalog](../tests/catalog.json), [runner tests](Tests/PWRunnerCoreTests/), [controller integration](../controller/integration/), [fixture catalog](../tests/fixtures/README.md), [change-verification guide](../tests/CHANGE-VERIFICATION.md). | Update active specimens and shape fixtures to the frontier, preserve useful assertions, and remove old semantic success expectations. |
| Documentation and generated accounts | [EXTENSIONS](../docs/EXTENSIONS.md), [user guide](../docs/PolicyWitness.md), [request grammar](../docs/REQUEST-GRAMMAR.md), [architecture input](../docs/architecture.json), [build input](../docs/build.json), [documentation guidance](../docs/AGENTS.md). | Present one extension model; update process/resource inventories, signing, limits, examples and shared guide regions. |

### Required simplification and protected shared coverage

Make these entries concrete in the ledger. Retire obsolete mechanisms rather
than preserving their abstractions behind actor-shaped inputs. Keep entries
dependent on an open design decision unresolved until that decision is made.

| Disposition | Code or test work |
| --- | --- |
| Remove the declaration execution path | Delete declaration preparation and `ExtensionSession`, `extensionRequested`/`extensionFD`, the old delivery publications and channel layout, the singleton native handle and its consume/release decision state, and the separate native consume/release implementation. Each extension operation has one dispatch path afterward. Retain the ordinary single-worker scheduling behavior. |
| Collapse declaration admission and interpretation | Remove `extensionMeaningFailure`, declaration-only capacities and the declaration branches in Swift reply validation, Rust disposition interpretation and Python extension validation. Review surviving event fields for required actor ownership. Keep operation-specific optional evidence and genuinely shared limits. |
| Narrow surviving interfaces | Review default Swift `internal` visibility and make implementation helpers private where their callers permit it; `ActorTranslation.extensionSlot` is an initial candidate. Remove unused parameters and duplicate form-specific wrappers. Keep the normalized-instruction design decision separate from this visibility cleanup. |
| Retire obsolete controls | Remove helper-specific reap-before-delivery controls, the old channel ABI tests and declaration-only preparation/status/cardinality expectations. Give each surviving publication, native interruption, reference or cleanup assertion an actor owner. General child cleanup and resource recovery remain covered. |
| Consolidate current workloads | Combine useful `extensions_byoxpc` and `actors_byoxpc` workloads under one owned installation/session, retaining independent signing, live authority, provenance and restoration assertions. Remove the missing-issuer contrast and add missing-selected-equipment coverage. |
| Extract shared test support and assertions | Move generic CLI capture support out of [check_extensions.py](../tests/suites/witness_contract/check_extensions.py). Give ordinary fresh-read/write and validator-ownership checks small non-declaration fixtures; they currently occur in [FreshWriteEvidenceTests](Tests/PWRunnerCoreTests/FreshWriteEvidenceTests.swift) and [blackbox extension controls](../tests/suites/blackbox_e2e/extension_controls.py). Retain live extension-dependent access checks separately. |
| Preserve size accounting and native primitives | [ReplyMaximumTests](Tests/PWRunnerCoreTests/ReplyMaximumTests.swift)'s `extensionReplyAllowance` also counts every ordinary fresh-read payload: extract that allowance before deleting declaration accounting. Trace shared token bounds, erasure primitives, fresh-file observations and actor layout dependencies before removing declaration-named files. |

### Initial test watchlist

These are source-based hypotheses for repair and coverage selection, not
candidate execution results. Inspect the named assertions before treating a
passing case as evidence of the consolidation's intended behavior.

| Attention | Existing control | Hypothesis and required treatment |
| --- | --- | --- |
| Passing with incomplete native coverage | `witness_contract/extension_redelegation` and its BYOXPC reuse | The principal chain may fail while the case passes its apparatus assertions and successful simpler calibration. Preserve that observation coverage, report whether re-delegation was actually credited, and do not count its pass as proof of a successful full chain. |
| Passing despite failed calibration consumption | [ActorAuthorityTests](Tests/PWRunnerCoreTests/ActorAuthorityTests.swift)'s positive-calibration group | It accepts a published consume failure. Distinguish this assertion set from a required successful basic lifecycle calibration; rename or revise its coverage account accordingly. |
| Passing despite broken dispatch | `runner_c_worker_harness/actor_operations` | [operation_control.c](../tests/fixtures/extension_controls/operation_control.c) calls operation bodies directly. Add dispatch coverage below; its current pass alone cannot establish that production routes a slot to the right body. |
| Definite fixture redesign | `runner_c_worker_harness/terminal_erasure` | [terminal_control.c](../tests/fixtures/extension_controls/terminal_control.c) and [its mutations](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py) inspect the declaration channel. Preserve the independent full-capacity and publication-boundary coverage obligation with an actor replacement; settle the exact ownership assertions under the lifecycle decision. |
| Passing with lost setup observations | [ActorReplyTests](Tests/PWRunnerCoreTests/ActorReplyTests.swift)'s host-allocation failure control | Aggregate error and `launch_refused` assertions can pass while native errno, independent cleanup failure or another actor's facts disappear. Retain eligibility assertions and add separate publication and per-actor evidence assertions. Declaration preparation/cleanup controls already assert stronger native and cleanup facts; migrate those assertions onto the surviving setup path. |
| Definite removal or adaptation | `ExtensionEvidenceTests`, the request corpus, extension boundaries/combinations, ABI controls, BYOXPC provenance and reply-size tests | These construct removed requests, records or transport mechanisms. Preserve shared assertions identified above, retire obsolete expectations and update active fixtures to the frontier. |
| Changed semantic expectations | `witness_contract/extensions` symlink, missing-target and replacement cases; `extension_directory` authority/default cases | Host target resolution and pre-worker issuance are proposed for removal; actor issuance currently requires explicit authority. Review each expectation against the accepted contract instead of restoring hidden preparation or old defaults to obtain a pass. |
| Possible timing sensitivity | `witness_contract/actor_timing_qualification` and converted CLI extension workloads | Actor setup and equipment validation can affect margins. Shared CLI capture currently imposes a 40-second timeout, separate from actor allowances. Identify the expired boundary and actual work before changing a timeout or margin; do not treat a larger production allowance as proof that the capture can wait that long. |
| Known independent instability | `runner_unit/host_setup_oracle_sensitivity` | Missing observer receipts have a separately deferred disposition and may recur in the mandatory full-suite selection. Preserve each failure's observations; a passing retry does not close that issue. |

### Additional controls and coverage obligations

Extend existing families where possible; a new public case is needed only when
its equipment, selection or evidence ownership warrants one. Assign exact case
ownership and registration in the Stage 2 packet.

| Control | Intended observation and initial owner |
| --- | --- |
| Production dispatch and targeted mutations | Extend `runner_c_worker_harness/actor_operations` to submit extension slots through `run_attempt`. Independently counted calls and handle observations must reject omitted or misrouted consume/release dispatch, even when the operation bodies remain correct. Compilation failure is not mutation detection. |
| Individually unavailable native symbols | Adapt extension boundary controls to remove issue, consume and release symbols individually. Establish the affected operation's unavailable evidence and continued execution of unrelated supported operations. The old consume/release implementation required both symbols together; the actor implementation checks them separately. Preserve the availability observation through setup publication and independent reply readers. |
| Primary setup failure plus independent cleanup failure | Adapt [check_extension_boundaries.py](../tests/suites/witness_contract/check_extension_boundaries.py)'s core-limit, metadata, mapping, close, combined metadata/cleanup and framing assertions, plus [extension control](../tests/fixtures/extension_controls/README.md) mode 118's missing API plus cleanup failure. Inject different primary/cleanup errors; include successful acquisition followed by failed cleanup, unmap failure and successful metadata followed by format rejection. Host region/private-custody allocation needs corresponding ownership/result checks at its own call boundary. |
| Terminal authority refusal before policy application | Extend native setup controls through production `main`, independently observing entry to policy processing and `sandbox_apply`. Every required-apparatus refusal must retain its setup/cleanup facts with zero application calls and no visit activation. Include a setup-success control that reaches application and a mutation removing the terminal branch that must fail the call-entry assertion. Exercise host recognition before normal actor setup publication, including an interrupted policy transfer caused by the early exit; preserve both the worker refusal and observed transport facts. Keep missing-symbol continuation and host timeout with later application as distinct controls. |
| Setup publication and actor association | Extend actor scheduler/reply and independent Swift, Rust and Python reader controls. Two actors failing at different setup stages must retain both accounts despite one summary disposition. Interrupt publication and require withholding of unpublished fields; retain eligible earlier facts and host observations. Cover valid late observations without restored activation, and substituted actor ownership that readers must reject. |
| Mixed-equipment permutation and provenance substitution | Extend `actor_compositions` and BYOXPC controls with different equipment choices, reordered actor declarations and consistent renaming. Equipment must stay associated with the intended actor. Add constructed reader controls that substitute another actor's equipment evidence and require rejection, alongside live process and signature observations. |
| Exact submitted-path forwarding | Under the proposed submitted-path contract, use an instrumented issue callback and a symlink path to check the exact native argument. Pair it with scheduled target creation/replacement and independent file observations. Do not require a particular kernel return to establish absence of hidden host resolution. Finalize expectations with the path/lifecycle disposition. |
| Actor terminal erasure | Replace the old terminal-erasure fixture with independent observations of full-capacity storage and the terminal publication boundary. Determine settled-inbound and host-owned-storage expectations through the lifecycle decision, retaining mutations that distinguish final cleanup from cleanup at the required boundary. Do not imply native authority from synthetic tokens. |
| Host termination dependency, if accepted | Extend actor scheduler/reply controls and a public issuer/subject specimen. Independent observations must distinguish phase completion, `done`, natural exit, reap, gate eligibility and cleanup; include timeout followed by late cleanup and a removed-gate mutation. Admission must reject a dependency on an actor that still needs a later visit. Keep transfer settlement and recipient ownership assertions active. |

Require successful basic issuance, transfer, consumption and fresh access on
the applicable signed equipment, with release and later fresh-access evidence.
Keep this positive coverage requirement separate from the principal
re-delegation specimen's observation-only success criterion and from native
return values alone. Retain its negative controls and report missing positive
coverage as such.

Removed-field controls must use the current request schema and identify the
intended refusal before execution. Keep unsupported-version controls separate,
so version rejection cannot accidentally satisfy a removed-field assertion.

**Review checkpoint:** return with the concrete examples, authority design,
observation dispositions, remaining design decisions, version decisions,
removal ledger and verification selection before broad implementation. The user is reviewing those choices,
not being asked to approve an unspecified redesign. Record the decision and
revise this plan if its scope changes.

## Stage 3 — implement the accepted frontier and remove declarations

Implement in dependency order: request/equipment contract and signing inventory;
actor launch and provenance; reply producers and readers; declaration removal;
current fixtures and documentation. Intermediate local states can be incomplete,
but the accepted tree must have one extension mechanism. Do not ship a
compatibility wrapper around the old helper to finish this stage.

Preserve ordinary non-extension execution and actor ownership/order rules.
Remove declaration-only preparation, transport, lifecycle records, overrides,
native sources, layout members and capacity checks after tracing shared uses.
If removing a layout field changes geometry, review C/Swift agreement and the
layout golden; do not update a golden without explaining its semantic delta.
All packaged worker variants must pass the current host/worker identity check.
Carry out the ledger's interface cleanup and shared-test extractions as part
of removal; a smaller wire surface must leave a smaller extension execution
and interpretation surface as well.

Update the contract manifest and every active fixture through the owning
generation/update procedures. Remove obsolete historical semantic branches in
current readers and controls. Small deliberately unsupported-version inputs
may remain to prove version-first refusal; they must not require a maintained
old-schema parser or success golden. Historical records, archived releases and
research reports are not bulk rewritten to the new format.

Review maximum reply construction and retention sizing after adding actor
equipment evidence or removing declaration records. Retain honest distinctions
between a constructed bound, reachable encoded output and process memory.
New or changed limits need independently owned value and boundary checks in
each implementing language, with any actual coverage gap stated explicitly.

### Core documentation execution guidance

Update documentation alongside the implemented contract, after tracing its
producers, publications and readers. Do not describe proposed setup fields or
an unsettled termination dependency as current behavior. Use the Stage 2
disposition ledger to track each affected authored region or manifest entry,
its retained/revised/retired claim, producing source, actual supporting
assertion and coverage limits. A documentation-only rename cannot supply the
missing actor observations.

Keep the documents' responsibilities distinct:

| Owner | Account to keep there |
| --- | --- |
| [WORKER](../docs/WORKER.md) | Resources, acquisition relative to setup/application/actions, owned references, native observations, publication and cleanup limits. One actor authority account replaces the declaration account and actor crosswalk. |
| [ARCHITECTURE](../docs/ARCHITECTURE.md) | Process/channel topology, one run in time, handoff/scheduling conditions and evidence ownership/landing paths. Link WORKER for resource mechanics instead of adding another setup inventory. |
| [Evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md), [wire contract](../docs/CONTRACT.md) and [limits](../docs/LIMITS.md) | Exact record meanings and eligibility, version rules, bounded capacities and their qualifications. Reference these from the tours rather than duplicating field specifications. |
| [EXTENSIONS](../docs/EXTENSIONS.md) and its shared guide region | The basic issuer/subject specimen, what its observations establish and advanced issuance/re-delegation. No setup or diagnostic mode choice. Keep implementation citations and maintenance instructions outside shared user prose. |

**WORKER edits and reduction.** Replace the declaration-shaped Mermaid overview
and form crosswalk under `Capability map` with one account that also retains
ordinary single-worker reporting. Rewrite `Supplied extension authority` around
four short subjects: host authority setup, worker authority setup, transport
ownership/settlement and requested native actions. Delete target-resolution,
helper-issuer and static declaration-handle explanations, the comparison of
release behavior by form and obsolete issuer launch caveats. Summarize the
transfer ownership transitions here and link ARCHITECTURE's handoff sequence
for ordering. Remove the declaration-inventory/actor-crosswalk disclaimer and
obsolete E/I owner terminology from `Detailed capability inventory` after its
generated actor replacement is complete.

Keep object, descriptor, mapping, private custody, slot and native handle
lifetimes distinct. Worker erasure of settled inbound bytes, host ownership of
published outbound bytes, quiescence required for shared erasure and independent
private-custody cleanup must survive shortening. Qualify last-use erasure as
following a returned native consume call, including its failure sentinel;
early unavailable/channel/delivery returns do not establish that erasure.
Keep close, unmap, byte erasure, native release, `done` and reap as different
observations, without invented success returns for operations lacking one.

Describe each failure by its observed stage and terminal or continuing flow,
using the failure-meaning table above. Show the new required-authority refusal
before policy processing, auxiliary failures that continue, and host deadlines
that settle eligibility while later worker facts remain collectable. Operations
of an unapplied actor follow setup without applying a policy. Review adjacent
claims against code while rewriting: `ActorSession` currently supplies
spawn attributes in both ordinary and actor execution, contrary to WORKER's
nil-attributes claim. Correct descriptions without changing launch behavior.
Retain the bounded applicability of launch observation L, fresh acquisition
versus reporting apparatus, exec-descendant and native-state gaps, and
publication withholding. Keep the final `Known gaps` links aligned with the
ordered authored `Known gap:` paragraphs. Aim for a modest net reduction by
removing duplicate mechanisms and transport prose; do not meet a word target
by deleting qualifications or merging distinct resource ownership.

**ARCHITECTURE edits.** Organize `One run in time` around admission/equipment,
host authority preparation, actor population setup, serial visits across
overlapping lifetimes, remaining cleanup/final observations and reply. Keep a
short ordinary-worker route. Show the terminal authority-setup refusal branch
before application and separate host setup deadlines from worker refusals.
Show exit and cleanup interleaved with visits;
phase completion, `done`, exit/reap and host cleanup are separate events.
Depict a termination dependency only after review, before dependent activation
and collection, without suggesting deferred subject creation or retrospective
satisfaction by cleanup. Keep the handoff sequence's distinct settlement and
source-acknowledgement conditions.

Remove the separate issuer route/budget and shorten repeated spawn/setup prose
under `Implementation and checking routes`. Replace the declaration row in
`Evidence channels and ownership` with the implemented setup landing paths,
distinguishing host-produced and worker-published observations. Update the
process, verification and BYOXPC accounts for actual selected equipment and
per-actor provenance. Narrow `boundaries.B19`'s current “nothing is credited”
wording: required setup/release governs requested action and authority claims,
not valid setup, native-capability or cleanup observations. Setup deadlines and
failed dependency gates retain their eligibility decisions even when valid
observations arrive later.

**Generated ownership and claim review.** Edit [architecture.json](../docs/architecture.json)
for the inventories. [generate_architecture.py](../docs/generate_architecture.py)
owns WORKER's `worker_capabilities` region; ARCHITECTURE's `topology`,
`boundaries`, `documents` and `byoxpc` regions; their manifest-named DOT/SVG
outputs; and registered architecture scalar spans. Edit authored prose and
WORKER's Mermaid directly, but never generated rows, DOT or SVG. Use this map
as a starting inventory, refreshing IDs against the execution baseline:

| Manifest area | Required review |
| --- | --- |
| `worker_capabilities` | Retire declaration/issuer/target-preparation nodes `s8a`–`s8c`, `s9`, `s10a`–`s10c`, `s11a`–`s11b`, `n1`–`n4`, `n7`; review incident relationships including `W17`–`W25`, `W27`, `W28`, `W46`. Replace, rather than discard, still-needed allocation, bearer storage, descriptor duplicate, endpoint/mapping, symbol, core-limit and handle categories in `s5`, `s12a`–`s12b`, `s13d`, `s19`–`s22`, `s37`. In particular, actor launch still needs the high descriptor duplicate described by `s5`. Review surrounding host setup, launch attributes (`s7`), evidence mapping and cleanup claims. Add actor custody, slot, publication and setup-evidence owners grounded in the implemented paths. |
| `topology` and `boundaries` | Remove issuer/old channel entries and edges `T13`–`T14`, `B13`–`B16`; update host/worker setup and publications (`T5`, `T8`, `T15`), authority region and actor eligibility (`B17`–`B19`), plus `shm_region`, `reply`, `B3`–`B4`. Keep host setup distinct from worker publication; add a narrowly scoped boundary only if existing rows cannot express that ownership clearly. |
| `byoxpc` and `documents` | Remove issuer and `X26`–`X28`; revise installation, signing, validation, provenance and worker inventory for accepted equipment. Preserve recovery for old installed records. Update document-generation/check relationships when their inputs change; consolidation does not require a documentation infrastructure redesign. |

Source citations and valid scoped check citations establish locations and
mapping, not that assertions prove the row. Worker inventory entries may be
explicitly source-only; preserve that honest distinction. For every stronger
claim inspect the native call, publication/read boundary, reply construction,
independent readers and cited assertions before assigning coverage. In
particular, `check_evidence_channel_paths` in
[source_drift/check.py](../tests/suites/source_drift/check.py) only resolves
ARCHITECTURE table paths in shape goldens; it does not establish observation
ownership or semantics. Update those goldens through their owning procedure
when actual fields change, then review the table against the real producers.

Keep new bounds in `limits.json`; use `{limit:id}` in architecture manifest
facts and links to LIMITS in authored WORKER prose. WORKER is not registered
for limits scalar spans, so no new scalar ownership machinery is needed.
If shortening removes a documentation mutation's target, adapt the mutation
to the revised claim and prove it still changes the input and is rejected;
do not restore redundant prose or weaken its coverage to satisfy the fixture.
Search active prose and fixtures for declaration assumptions, not just helper
filenames. Update signing, counts, lifetimes, refusals and test descriptions.

Regenerate with the owning tools for changed inputs. The possible commands,
run from the root, are:

```sh
tests/lib/python.sh docs/generate_contract.py
tests/lib/python.sh docs/generate_worker_identity.py
tests/lib/python.sh docs/generate_limits.py
tests/lib/python.sh docs/generate_architecture.py
tests/lib/python.sh docs/generate_build.py
tests/lib/python.sh docs/generate_limits.py --stage-guide dist/PolicyWitness.md
```

Run the affected generators' `--check` modes after regeneration, including
architecture and limits. Review generated tables, diagrams and the copied
guide in context, checking that one resource/temporal account survives across
prose, graph and inventory without duplicated explanations. The Stage 4 full
`source_drift` selection checks freshness, source/scoped-check citations,
landing paths, links, shared copying and gap indexes; the behavioral controls
separately substantiate meanings. Refresh related
active plans' source assumptions where necessary, including the footprint plan;
do not execute their separate investigations or rewrite historical evidence.

**Exit:** the accepted contract is implemented, the removal ledger has no
unexplained retained declaration path, current readers and specimens agree,
and the candidate is ready for signed integrated verification.

## Stage 4 — verify behavior and deletion on the candidate

Use [tests/AGENTS.md](../tests/AGENTS.md) for selection, evidence and cleanup.
Inspect exact selections with `--list`, use fresh output directories, and run
builds and test executions serially under the checkout lock. Build a normal
signed candidate through [BUILD.md](../docs/BUILD.md). The final battery must
run against the app containing the consolidation, not an earlier passing build.

The mandatory coordinated selection is the full suites below, plus the
affected behavior owners. This covers admission and limit changes; a few
hand-picked drift cases do not substitute for the full suite.

```sh
tests/run.sh --suite unit --suite integration --suite source_drift \
  --suite runner_abi_layout --suite runner_unit \
  --suite runner_c_worker_harness --suite failure_boundaries --list
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-contracts \
  tests/run.sh --suite unit --suite integration --suite source_drift \
  --suite runner_abi_layout --suite runner_unit \
  --suite runner_c_worker_harness --suite failure_boundaries
```

Resolve the rest of the selection against the catalog at Stage 2. These are
behavioral obligations and existing starting controls, not permission to keep
obsolete declaration expectations:

| Obligation | Existing owners and required adaptation |
| --- | --- |
| Basic lifecycle, placement, omission, fresh access and partial failure evidence | [witness_contract](../tests/suites/witness_contract/README.md), [failure_boundaries](../tests/suites/failure_boundaries/README.md), [blackbox_e2e](../tests/suites/blackbox_e2e/README.md), and applicable [runner_validator_failure](../tests/suites/runner_validator_failure/README.md) assertions. Move declaration-only useful checks to actors; pin refused removed fields and unsupported versions separately. |
| Multiple actors/resources, sandboxed issuance, re-delegation and finite budget qualification | `witness_contract/actor_compositions`, `witness_contract/extension_redelegation`, `witness_contract/actor_timing_qualification`, and affected extension boundary/directory/combination controls in the owning suite. Keep calibration and negative controls, not just successful native returns. |
| Authority publication, binding, delivery, native dispatch and terminal erasure | `runner_c_worker_harness/authority_binding`, extended `runner_c_worker_harness/actor_operations`, the actor replacement for `runner_c_worker_harness/terminal_erasure`, and `runner_unit/actor_handoff_mutations`; follow their [change triggers](../tests/CHANGE-VERIFICATION.md#actor-authority-ownership-and-operation-controls). |
| Automatic setup evidence, terminal refusal and independent cleanup | Adapt native extension setup/failure controls; extend actor setup/reply and independent-reader controls assigned in Stage 2. Assert primary/cleanup coexistence, local rejection without invented errno, per-operation availability, host versus worker ownership, all affected actors' facts and withheld incomplete publication. Independently establish no application after terminal apparatus refusal, including the removed-branch mutation. Retain host-timeout ineligibility alongside valid late observations. |
| Unentitled issuer with entitled subject, and inherited restrictions on an unapplied entitled actor | Adapt `witness_contract/actors_byoxpc` and useful assertions from `witness_contract/extensions_byoxpc`; extend `runner_byoxpc/entitlement_readback` and applicable dossier/selection controls. Read back actual signatures, bind equipment to actor processes, and observe live operations with independent file evidence. Remove the obsolete missing-issuer contrast; test missing selected equipment instead. |
| Signed inventory and installation integrity | Applicable [preflight](../tests/suites/preflight/README.md) build/signature controls and [runner_byoxpc](../tests/suites/runner_byoxpc/README.md) installation, verification and recovery controls. Prove the removed helper is absent from the candidate bundle and new equipment is independently validated. |
| Native authority and issuer-lifetime assumptions | `sandbox_extensions_native/feasibility` and `sandbox_extensions_native/directory`, selected according to the [native-control guidance](../tests/CHANGE-VERIFICATION.md#native-sandbox-extensions) during design and again if their dependencies or assumptions change. These supplement integrated PW observations. |

Keep boundary controls independent of production classifiers and generated
limits. For equipment selection, include a control that would fail if the
issuer and subject silently used the same entitled worker. A positive issue
result alone cannot establish that distinction. Signature read-back,
per-process provenance and independent native effects support different claims.
For removed features, assert refusal before execution rather than accepting
silently ignored declaration fields.
Execute the additional controls assigned in Stage 2 and resolve each watchlist
entry in the verification account. Credit the successful basic calibration
separately from apparatus-only re-delegation observations and direct-body
operation checks separately from production dispatch checks.

If worker waits, release publication or query eligibility change, run
`witness_contract/order_barrier_mutations`. Apply the other change-specific
controls when their documented boundaries change. Run the default battery on
the final candidate with a fresh output directory:

```sh
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-battery tests/run.sh
```

After corrections, rebuild when app inputs changed and rerun affected checks;
re-establish final battery applicability using the test evidence rules. Keep
failed runs and their reasons visible. Sleep overlap, missing equipment or
unsettled test resources do not establish product success. The separately
deferred host-setup observer-receipt issue remains separately owned: if a
selected control encounters it, retain the observations and seek an explicit
disposition rather than calling a passing retry a resolution or silently
omitting the control. No separate sleep pause is part of this plan.

**Exit:** complete accounting for required selections on an identified
candidate, independent authority controls establishing the accepted design,
and no unresolved consolidation failure concealed by skips or reruns.

## Acceptance, evidence and closeout

Keep the design decision, removal/coverage ledger, verification selection and
acceptance account together under a new `records/extension-consolidation-<date>/`
directory created at execution. Link those records only from this associated
plan, following [records guidance](../records/AGENTS.md). Do not create an
empty evidence archive as part of plan preparation.

The acceptance account must establish:

- Extension specimens use one actor model; ordinary non-extension execution
  remains usable; removed declarations are explicitly refused.
- The accepted issuer/subject authority arrangements are selectable and
  evidenced, including the BYOXPC distinction. No historical translation or
  secondary extension implementation remains.
- Current producers, independent readers, fixtures and generated documentation
  agree with the selected schemas. A source search's remaining declaration
  references have a current negative-control or historical purpose.
- One automatic bounded setup account preserves primary native, independent
  cleanup and per-operation availability observations with their actual owners;
  summary disposition does not replace per-actor facts. Publication and
  scheduling eligibility remain separate, and no diagnostic mode is required.
- Required authority-apparatus refusal terminates that worker before specimen
  policy processing. Its observed terminal branch establishes application was
  not attempted; timeout, auxiliary failure and unpublished application results
  retain their distinct meanings and supporting controls.
- WORKER and ARCHITECTURE describe the same implemented resource and temporal
  account. The declaration/crosswalk duplication is removed; changed inventory
  claims have reviewed assertion scope or explicit source-only support.
  Mechanical citation/shape agreement is not credited as behavioral proof.
- The signed bundle inventory, worker identities and per-actor provenance match
  the candidate whose integrated and default tests are credited.
- Every meaningful removed test has an explained disposition; every retained
  result has its source/build applicability established. Source inspection,
  mutation controls and live observations receive distinct credit.
- Shared fresh-file, validator-ownership and reply-size coverage survives
  declaration removal. The watchlist and additional controls have explicit
  outcomes, and no open design decision was resolved by silently deleting
  an assertion or weakening its observation requirements.
- Necessary evidence will survive ordinary retention, and external-runner or
  child-resource recovery remains owned until settled.

Retain canonical case IDs, commands/configuration, source snapshots, candidate
app inventory and the raw observations supporting acceptance. Use the normal
retention allocation for current accepted runs, or preserve an identified,
hashed copy of relied-on evidence in the associated records. A list of unpinned
run IDs is insufficient. Copies preserve original identities and do not move
active cleanup ownership. Review retention changes against existing dependencies
before replacing pins or pruning through the supported helpers.

Return for acceptance with the final changes, verification account and any
specific unresolved issue or proposed outflow. A new issue may be deferred by
decision; retirement of the old extension path and proof of the accepted
authority configuration are core completion conditions. Do not retire this
plan until that review is complete. Permanent documentation describes the new
current behavior; the decision history stays with the plan/records and Git.

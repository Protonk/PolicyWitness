# Plan: consolidate sandbox extensions on actors

## Intended result and scope

Make actor operations the sole current request and execution model for sandbox
extensions. Introduce it with an issuer/subject specimen: issue, transfer,
consume, observe fresh access, and release. Re-delegation extends that same
model. Remove the top-level extension declaration form and its separate
issuance machinery while preserving the issuer/subject authority arrangements
specified below.

This changes production implementation, signing, admission and evidence
interpretation together with their contracts and documentation.
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

Stages 1–2 complete the contract and verification packet for review before
implementation. The chosen design is specified below; remaining decisions are
collected at the end of Stage 1. Source and assertion inspection supply the
starting points in this plan; candidate execution supplies behavioral evidence.
Follow [runner guidance](AGENTS.md) for the host and native worker changes.

## Decisions and boundaries

Use one actor extension mechanism with explicit equipment and evidence.
Preserve an issuer without supplied entitlements and a subject with supplied
entitlements in the same specimen, plus sandboxed issuance and re-delegation.
The proposed equipment implementation uses signed variants of the same worker.

Issue on the submitted absolute target path. Set up actors eagerly and execute
requested actions in a serial schedule across overlapping process lifetimes.
The lifecycle packet evaluates a host-observed termination dependency before
a later visit. Automatic issuer reap before subject creation and host target
resolution are retired with declarations.

PW automatically records bounded setup and cleanup observations. Admission
produces one resolved operation plan; equipment binding completes its launch
records before execution. Users select specimen inputs, equipment and any
accepted ordering dependency through this single model.

Keep the repository's [core ideas](../AGENTS.md#core-ideas): fresh processes,
sandbox calls outside the host, observations supporting effects, collection
before attempts, and literal attribution. Token bytes remain transient and
absent from requests, replies, logs and diagnostics. Removal of the declaration
path must not weaken actor custody, delivery settlement or cleanup ownership.

New extension families, concurrent actor execution, deferred actor setup,
coordinated issuer liveness, arbitrary per-actor binary plugins, changes to
native call flags, footprint optimization, release publication and general
registry redesign are outside this plan. A required scope change belongs in
the contract review with its concrete witnessing requirement.

Keep list, reconcile and owned removal usable for unsupported installations,
with resource-recovery records retained until settlement, as the wire contract
requires.

## Source facts that constrain the design

| Present behavior | Grounding | Consequence |
| --- | --- | --- |
| A declaration prepares its target, issues before worker creation, and requires the issuer's confirmed reap before delivery. | [CWorkerOrchestrator.swift](Sources/PWRunnerCore/CWorkerOrchestrator.swift), [ExtensionIssuer.swift](Sources/PWRunnerCore/ExtensionIssuer.swift), [native issuer](../controller/tools/pw_probe_runner/pw_extension_issuer.c). | Remove the separate preparation and lifecycle paths; update their evidence and failure controls for the surviving actor behavior. |
| Declaration preparation resolves the submitted target and records resolved-path metadata. Actor issuance passes the submitted absolute target unchanged. | [ExtensionIssuer.swift](Sources/PWRunnerCore/ExtensionIssuer.swift), [ActorTranslation](Sources/PWRunnerCore/ActorOrchestration.swift), [extension coverage](../docs/EXTENSIONS.md). | Retain exact submitted-path forwarding and replace preparation-specific expectations. |
| Actor translation currently supplies the same selected worker executable to every actor. An unapplied actor skips specimen policy application, not its binary's entitlements. | [ActorOrchestration.swift](Sources/PWRunnerCore/ActorOrchestration.swift), [actor types](Sources/PWRunnerCore/PWRunnerActors.swift), [BYOXPC actor controls](../tests/CHANGE-VERIFICATION.md#byoxpc-actor-controls). | The current actor request cannot express every declaration issuer/subject authority arrangement. |
| BYOXPC signing gives supplied entitlements to the worker and enclosing service, while the validator and declaration issuer receive the signing identity alone. | [signing implementation](../controller/src/runner_manager.rs), [signing account](../docs/SIGNING.md#what-buildsh-signs). | Replacing the helper with another invocation of the selected entitled worker can change the observed authority. Verify actual signed equipment. |
| The scheduler launches actors and resolves setup before walking the serial schedule. Parked actors can receive apparatus deliveries while their requested actions wait. | [ActorScheduler.swift](Sources/PWRunnerCore/ActorScheduler.swift), [ActorSession.swift](Sources/PWRunnerCore/ActorSession.swift), [AuthorityCustody.swift](Sources/PWRunnerCore/AuthorityCustody.swift). | Keep issuance, delivery and consumption distinct. A helper lifetime cannot be inferred from an actor's final scheduled action. |
| Actor references, resource states, budgets and reply ownership differ from declaration records. | [ActorPlan.swift](Sources/PWRunnerCore/ActorPlan.swift), [actor records](Sources/PWRunnerCore/PWRunnerActors.swift), [extension records](Sources/PWRunnerCore/PWRunnerExtension.swift), [limits](../docs/LIMITS.md). | Remove obsolete contracts together with their producers and readers; review surviving shared types before deleting a declaration-named file. |
| Actor authority setup retains status/stage but loses native and cleanup observations that declaration setup records; the actor reply does not expose a complete per-actor setup account. | `prepare_authority` and `prepare_extension` in the [native worker](../controller/tools/pw_probe_runner/pw_probe_runner.c), [ActorSession.swift](Sources/PWRunnerCore/ActorSession.swift), [ActorOrchestration.swift](Sources/PWRunnerCore/ActorOrchestration.swift). | Extend the actor setup account with primary native, independent cleanup and per-actor observations. |

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

### Unified setup evidence

Record authority setup and cleanup automatically in a bounded account using
the same observation conventions for host and worker operations. Setup success,
native symbol availability and effective authority remain separate observations.

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

Scope this account to authority preparation, its acquired references and their
cleanup, plus the necessary publication and reply paths. Inventory calls in
`prepare_authority`, [AuthorityCustody](Sources/PWRunnerCore/AuthorityCustody.swift)
and the relevant [ActorSession](Sources/PWRunnerCore/ActorSession.swift) paths.
Reuse existing native result, saved-errno and publication conventions where
their meanings fit. The single generic failure record cannot represent both
primary and independent cleanup failures. Specify bounded storage, C/Swift
layout, reply shape, limits and reader rules together in the contract packet.

### Terminal setup boundary and failure meanings

Make failure of required worker authority apparatus terminal immediately after
authority preparation, before policy reading, compilation, capture or
application. Publish the reached setup observations, perform and record the
applicable cleanup, and exit through a path that cannot return to policy
processing or visits. Publication must identify the terminal decision even
when cleanup is incomplete; cleanup completion and process reap retain their
own observations. The host resolves this refusal without waiting for an
applied/unapplied setup publication. The worker makes the terminal decision
locally; the host observes its publication.

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

### Lifecycle and termination dependency

**Default behavior.** Resolve launch/setup for the actor
population before walking the serial schedule; resolution includes failure,
and does not promise successful setup of every actor. Parked actors can
service deliveries without running requested native actions. Successful visits
advance after observed phase completion without a prerequisite issuer reap.
Failed visits separately establish quiescence before further activation, or
cancel remaining activation under the existing failure rules. Actors may
publish terminal completion and exit after their own last visit, and resource
cleanup can occur during the schedule. Do not imply survival until final
cleanup.

**Candidate dependency for contract review.** Gate a later visit on the host's
observed termination of another actor after that actor's final visit. Place
the gate before activation and query collection so predictions and actions
follow that observation; the dependent actor has already set up. Admit only a
dependency whose referenced actor has no remaining visits when the gate is
reached; otherwise waiting could require an activation the gate prevents.
Issue, transfer and consume retain their existing meanings. Decide whether
the required condition is termination or clean completion: an observed reap
after an abnormal exit establishes the former, not the latter. Retain exit
status and termination observations separately, and select one condition for
the public contract.

**Failure and evidence.** Specify the gate's bounded wait, budget accounting,
ownership requirements and effect on subsequent scheduling. Timeout or lost
ownership leaves the dependent visit ineligible, without its collection or
release. A reap observed later during cleanup cannot retroactively satisfy
that gate. Observe natural termination through the child-observation boundary;
do not call `requestExit`/`finishCleanup` in
[ActorSession.swift](Sources/PWRunnerCore/ActorSession.swift) to make the condition
true, since those paths request departure and may terminate the process. Record
the dependency, the owned child observation, the gate's terminal outcome and
its relation to visit eligibility. A final `reaped` flag or a worker's `done` publication alone
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

### Resolved launch and operation plan

Resolve operation references and equipment through two preparation steps that
produce one execution plan before any actor launches:

1. **Normalize the specimen's meaning.** Assign stable, distinct internal
   indices to actors, tokens, deliveries and handles. Represent extension
   operations as Swift enum cases with exactly their required operands, such
   as `consume(delivery: DeliveryIndex, handle: HandleIndex)` and
   `release(handle: HandleIndex)`. Resolve ownership, phase placement and
   last-use information during construction, then finalize the plan. Retain
   submitted names as diagnostic/reply metadata. Phase actions must carry
   resolved operations rather than optional request operands that translation
   has to interpret again. These indices identify planned resources; native
   token and handle availability remains an execution observation.
2. **Bind the selected equipment.** Resolve each actor's admitted equipment
   choice against the host's validated executable inventory. Bind the concrete
   executable and inspected identity information needed for validation and
   provenance to that actor's launch record, alongside its application mode,
   policy and resolved operations. Missing or invalid selected equipment yields
   an explicit preparation refusal before launch. Actual process identity and
   native effects remain runtime observations. Keep filesystem/equipment work
   out of pure request normalization.

The scheduler receives the actor launch records, visit schedule and authority
storage assignments derived from the same resolved relationships. Keep one
authoritative resolved model; do not maintain separately mutable request-shaped
actions and resource graphs that can disagree. Complete the actor-local slot
and phase assignments during preparation. Encoding into C worker inputs then
uses exhaustive operation switches, explicit operands and checked index
conversions, with no string-reference lookup, zero-index substitution, default
release operation or silently skipped action. An inconsistent internal plan
produces an explicit preparation error before launch, distinct from malformed
submitted input. Restrict construction and mutation to the preparation owner;
keep these types specific to the admitted operations and equipment.

Authoritative host admission must return its accepted plan and carry it
forward. Currently [requestMeaningFailure](Sources/PWRunnerCore/ProbeRunner.swift)
normalizes to check the actor request, discards that result, and
[CWorkerOrchestrator](Sources/PWRunnerCore/CWorkerOrchestrator.swift) normalizes
again before execution. Remove that duplication and preserve the actual
refusal on failure. Client validation and worker ABI/identity checks retain
their independent boundary purposes. Original request metadata can remain
available for reply construction; execution must obtain its operation and
equipment meaning from the prepared plan.

### Remaining contract decisions

Complete these decisions within the requirements above and present them at
Stage 2 before implementing dependent changes.

| Decision | Required disposition |
| --- | --- |
| Actor equipment contract | Specify public choices/defaults, their composition with application mode and entitlement requirements, signed packaging, host binding and per-actor provenance. Establish the proposed worker variants' authority arrangement on applicable signed equipment. |
| Setup evidence representation | Specify bounded storage, publication, reply landing paths and independent-reader rules, including recognition of terminal refusal before normal actor setup completion. Preserve the required primary, cleanup, availability and per-actor facts. |
| Lifecycle dependency and erasure | Decide whether to include the candidate and choose termination or clean completion. Specify bounded wait/budget accounting, eligibility evidence and failure behavior; settle the actor terminal-erasure assertions against storage ownership. |

**Exit:** a concrete authority arrangement grounded in the signing and launch
paths, bounded setup and lifecycle contracts, and controls capable of
distinguishing the proposed arrangements.
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
6. The [lifecycle contract](#lifecycle-and-termination-dependency), including the
   termination-dependency decision, its specimen and controls, and any accepted
   wire syntax.
7. The [setup evidence representation](#unified-setup-evidence), with
   representative failed-setup replies retaining multiple actors' observations
   and the distinct failure meanings specified above. Include affected WORKER
   and ARCHITECTURE claims in the disposition ledger using the
   [documentation guidance](#core-documentation-execution-guidance).
8. The [resolved plan's](#resolved-launch-and-operation-plan) concrete types,
   ownership and preparation errors, identifying the removed lookups/fallbacks
   and how admission's accepted plan reaches execution.

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
| Resolve execution once | Have host admission retain its normalized plan, finalize typed operations and bind selected equipment before launch. Replace `ActorTranslation`'s semantic reconstruction with mechanical encoding of resolved operands. Remove repeated string lookups, zero-index/default-operation fallbacks and skipped-action paths; keep diagnostic names and runtime resource observations separately owned. |
| Narrow surviving interfaces | Review default Swift `internal` visibility and make implementation helpers private where their callers permit it; the encoder replacing `ActorTranslation.extensionSlot` is an initial candidate. Restrict resolved-plan construction to its owner, and remove unused parameters and duplicate form-specific wrappers. |
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
| Changed semantic expectations | `witness_contract/extensions` symlink, missing-target and replacement cases; `extension_directory` authority/default cases | Host target resolution and pre-worker issuance are removed; actor issuance currently requires explicit authority. Update each expectation for submitted-path forwarding, actor-time issuance and the reviewed authority contract. |
| Possible timing sensitivity | `witness_contract/actor_timing_qualification` and converted CLI extension workloads | Actor setup and equipment validation can affect margins. Shared CLI capture currently imposes a 40-second timeout, separate from actor allowances. Identify the expired boundary and actual work before changing a timeout or margin; do not treat a larger production allowance as proof that the capture can wait that long. |
| Known independent instability | `runner_unit/host_setup_oracle_sensitivity` | Missing observer receipts have a separately deferred disposition and may recur in the mandatory full-suite selection. Preserve each failure's observations; a passing retry does not close that issue. |

### Additional controls and coverage obligations

Extend existing families where possible; a new public case is needed only when
its equipment, selection or evidence ownership warrants one. Assign exact case
ownership and registration in the Stage 2 packet.

| Control | Intended observation and initial owner |
| --- | --- |
| Production dispatch and targeted mutations | Extend `runner_c_worker_harness/actor_operations` to submit extension slots through `run_attempt`. Independently counted calls and handle observations must reject omitted or misrouted consume/release dispatch, even when the operation bodies remain correct. Compilation failure is not mutation detection. |
| Resolved operation and equipment associations | Extend actor planning/translation controls with multiple tokens, deliveries and handles, nonzero resource indices, renamed/reordered actor declarations and empty revisits. Check that worker operands and custody assignments identify the intended resources and actors through the same prepared plan. Exercise remaining fallible preparation boundaries: missing equipment or inconsistent internal assignments must produce their own error before any spawn, without substitution or a fabricated request refusal. Pair these with the mixed-equipment and production-dispatch controls below. |
| Individually unavailable native symbols | Adapt extension boundary controls to remove issue, consume and release symbols individually. Establish the affected operation's unavailable evidence and continued execution of unrelated supported operations. The old consume/release implementation required both symbols together; the actor implementation checks them separately. Preserve the availability observation through setup publication and independent reply readers. |
| Primary setup failure plus independent cleanup failure | Adapt [check_extension_boundaries.py](../tests/suites/witness_contract/check_extension_boundaries.py)'s core-limit, metadata, mapping, close, combined metadata/cleanup and framing assertions, plus [extension control](../tests/fixtures/extension_controls/README.md) mode 118's missing API plus cleanup failure. Inject different primary/cleanup errors; include successful acquisition followed by failed cleanup, unmap failure and successful metadata followed by format rejection. Host region/private-custody allocation needs corresponding ownership/result checks at its own call boundary. |
| Terminal authority refusal before policy application | Extend native setup controls through production `main`, independently observing entry to policy processing and `sandbox_apply`. Every required-apparatus refusal must retain its setup/cleanup facts with zero application calls and no visit activation. Include a setup-success control that reaches application and a mutation removing the terminal branch that must fail the call-entry assertion. Exercise host recognition before normal actor setup publication, including an interrupted policy transfer caused by the early exit; preserve both the worker refusal and observed transport facts. Keep missing-symbol continuation and host timeout with later application as distinct controls. |
| Setup publication and actor association | Extend actor scheduler/reply and independent Swift, Rust and Python reader controls. Two actors failing at different setup stages must retain both accounts despite one summary disposition. Interrupt publication and require withholding of unpublished fields; retain eligible earlier facts and host observations. Cover valid late observations without restored activation, and substituted actor ownership that readers must reject. |
| Mixed-equipment permutation and provenance substitution | Extend `actor_compositions` and BYOXPC controls with different equipment choices, reordered actor declarations and consistent renaming. Equipment must stay associated with the intended actor. Add constructed reader controls that substitute another actor's equipment evidence and require rejection, alongside live process and signature observations. |
| Exact submitted-path forwarding | Use an instrumented issue callback and a symlink path to check the exact native argument. Pair it with scheduled target creation/replacement and independent file observations. Exact forwarding is independent of the kernel's return value. |
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
removal ledger and verification selection before broad implementation. Record
the review decision and revise this plan if its scope changes.

## Stage 3 — implement the accepted frontier and remove declarations

Implement in dependency order: request/equipment contract and signing inventory;
resolved operations and equipment binding; actor launch and provenance;
reply producers and readers; declaration removal; current fixtures and
documentation.

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
current readers and controls. Keep small unsupported-version inputs for
version-first refusal without an old-schema parser or success golden. Preserve
historical records, archived releases and research reports unchanged.

Review maximum reply construction and retention sizing after adding actor
equipment evidence or removing declaration records. Retain honest distinctions
between a constructed bound, reachable encoded output and process memory.
New or changed limits need independently owned value and boundary checks in
each implementing language, with any actual coverage gap stated explicitly.

### Core documentation execution guidance

Update documentation alongside the implemented contract, after tracing its
producers, publications and readers. Use the Stage 2 disposition ledger to
track each affected authored region or manifest entry,
its retained/revised/retired claim, producing source, actual supporting
assertion and coverage limits.

Keep the documents' responsibilities distinct:

| Owner | Account to keep there |
| --- | --- |
| [WORKER](../docs/WORKER.md) | Resources, acquisition relative to setup/application/actions, owned references, native observations, publication and cleanup limits. One actor authority account replaces the declaration account and actor crosswalk. |
| [ARCHITECTURE](../docs/ARCHITECTURE.md) | Process/channel topology, one run in time, handoff/scheduling conditions and evidence ownership/landing paths. Link WORKER for resource mechanics instead of adding another setup inventory. |
| [Evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md), [wire contract](../docs/CONTRACT.md) and [limits](../docs/LIMITS.md) | Exact record meanings and eligibility, version rules, bounded capacities and their qualifications. Reference these from the tours rather than duplicating field specifications. |
| [EXTENSIONS](../docs/EXTENSIONS.md) and its shared guide region | The basic issuer/subject specimen, what its observations establish and advanced issuance/re-delegation. Keep implementation citations and maintenance instructions outside shared user prose. |

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
Describe admission as producing the resolved plan and equipment binding as
finishing launch preparation; keep their planned identities distinct from
subsequent process and native observations.
Show exit and cleanup interleaved with visits; phase completion, `done`,
exit/reap and host cleanup are separate events.
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

Run the full coordinated selection below for admission and limit changes,
plus the affected behavior owners.

```sh
tests/run.sh --suite unit --suite integration --suite source_drift \
  --suite runner_abi_layout --suite runner_unit \
  --suite runner_c_worker_harness --suite failure_boundaries --list
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-contracts \
  tests/run.sh --suite unit --suite integration --suite source_drift \
  --suite runner_abi_layout --suite runner_unit \
  --suite runner_c_worker_harness --suite failure_boundaries
```

Resolve the remaining selection against the catalog at Stage 2. Use these
owners to execute the [additional controls](#additional-controls-and-coverage-obligations)
and close the [test watchlist](#initial-test-watchlist):

| Obligation | Existing owners and required adaptation |
| --- | --- |
| Basic lifecycle, placement, omission, fresh access and partial failure evidence | [witness_contract](../tests/suites/witness_contract/README.md), [failure_boundaries](../tests/suites/failure_boundaries/README.md), [blackbox_e2e](../tests/suites/blackbox_e2e/README.md), and applicable [runner_validator_failure](../tests/suites/runner_validator_failure/README.md) assertions. |
| Multiple actors/resources, sandboxed issuance, re-delegation and finite budget qualification | `witness_contract/actor_compositions`, `witness_contract/extension_redelegation`, `witness_contract/actor_timing_qualification`, and affected extension boundary/directory/combination controls in the owning suite. |
| Authority publication, binding, delivery, native dispatch and terminal erasure | `runner_c_worker_harness/authority_binding`, extended `runner_c_worker_harness/actor_operations`, the actor replacement for `runner_c_worker_harness/terminal_erasure`, and `runner_unit/actor_handoff_mutations`; follow their [change triggers](../tests/CHANGE-VERIFICATION.md#actor-authority-ownership-and-operation-controls). |
| Automatic setup evidence, terminal refusal and independent cleanup | Adapted native extension setup/failure controls and actor setup/reply and independent-reader controls assigned in Stage 2. |
| Unentitled issuer with entitled subject, and inherited restrictions on an unapplied entitled actor | Consolidated `witness_contract/actors_byoxpc` and `witness_contract/extensions_byoxpc` workloads, extended `runner_byoxpc/entitlement_readback`, and applicable dossier/selection controls. |
| Signed inventory and installation integrity | Applicable [preflight](../tests/suites/preflight/README.md) build/signature controls and [runner_byoxpc](../tests/suites/runner_byoxpc/README.md) installation, verification and recovery controls. Establish the removed helper's absence and independent validation of new equipment. |
| Native authority and issuer-lifetime assumptions | `sandbox_extensions_native/feasibility` and `sandbox_extensions_native/directory`, selected according to the [native-control guidance](../tests/CHANGE-VERIFICATION.md#native-sandbox-extensions) during design and again if their dependencies or assumptions change. These supplement integrated PW observations. |

Keep boundary controls independent of production classifiers and generated
limits. For equipment selection, include a control that would fail if the
issuer and subject silently used the same entitled worker. A positive issue
result alone cannot establish that distinction. Signature read-back,
per-process provenance and independent native effects support different claims.
Credit the successful basic calibration separately from apparatus-only
re-delegation observations and direct-body operation checks separately from
production dispatch checks.

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
omitting the control.

**Exit:** complete accounting for required selections on an identified
candidate, independent authority controls establishing the accepted design,
and no unresolved consolidation failure concealed by skips or reruns.

## Acceptance, evidence and closeout

Keep the design decision, removal/coverage ledger, verification selection and
acceptance account together under a new `records/extension-consolidation-<date>/`
directory created at execution. Link those records only from this associated
plan, following [records guidance](../records/AGENTS.md).

The acceptance account must establish:

- Extension specimens use one actor model; ordinary non-extension execution
  remains usable; removed declarations are explicitly refused.
- The accepted issuer/subject authority arrangements are selectable and
  evidenced, including the BYOXPC distinction. No historical translation or
  secondary extension implementation remains.
- Host admission retains one resolved operation plan, and equipment binding
  completes its actor launch records before execution. Scheduler, custody and
  worker encoding consume those relationships without resolving request names
  again or substituting an operation/resource on inconsistency.
- Current producers, independent readers, fixtures and generated documentation
  agree with the selected schemas. A source search's remaining declaration
  references have a current negative-control or historical purpose.
- One automatic bounded setup account preserves primary native, independent
  cleanup and per-operation availability observations with their actual owners;
  summary disposition does not replace per-actor facts. Publication and
  scheduling eligibility remain separate.
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
  outcomes consistent with the reviewed contract and coverage obligations.
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

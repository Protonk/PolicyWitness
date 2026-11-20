# Trace review management plan

**Handoff, November 19.** All fourteen selected remedies are on `main`. The
[product-group checkpoint](#product-group-checkpoint) is complete. It records
the battery, its validator reread and prune preview, and the remaining work,
which begins with the technical-account passes.
The technical-account passes work from two tracked files,
[ACCOUNTS-WORKLIST.md](trace-assessments/ACCOUNTS-WORKLIST.md) and
[ACCOUNTS-ADDENDA.md](trace-assessments/ACCOUNTS-ADDENDA.md).

## Scope and ownership

Assess every claim in [DOCUMENTATION-TRACE-REVIEW.md](DOCUMENTATION-TRACE-REVIEW.md):
DT-01–135, compound subfindings, qualifications and the two unnumbered
import/receipt investigations. Keep that record intact. Maintain the coverage
map and dispositions here, using original DT identifiers.

This plan owns product judgments, implementation authority, the guide freeze,
combined sequencing and closing outflows. [TRACE-ACCEPTANCE-PLAN.md](TRACE-ACCEPTANCE-PLAN.md)
owns documentation change rehearsals. [TEST-OUTCOME-OVERHAUL-PLAN.md](TEST-OUTCOME-OVERHAUL-PLAN.md)
owns test authority/reporting, selected test corrections, two pytest cohorts
and executable seam implementation.

Follow [record guidance](AGENTS.md). Permanent documentation, source and tests
must not link back to investigation records. Check availability and applicability
before reusing local or gitignored evidence; source inspection is not execution.

## Guide freeze and public commitments

Leave `docs/PolicyWitness.md`, its distributed copies and its stamp table
byte-unchanged against `3d3f8e65`. That includes the guide's copies of the
shared explanatory regions and its limit spans. Do not collect guide errata,
draft replacement passages or publish substitute user guidance.

The regions' owners remain current technical accounts: `docs/LIMITS.md`,
`docs/QUESTIONS.md`, `docs/EXTENSIONS.md`, the shared statuses and reading rules
in `tests/FAILURE-PROPAGATION-CONTRACT.md`, and the comparison matrix rows.
Regenerate their tables and spans from current definitions. Where a selected
change makes an authored statement false, correct or remove that claim in its
owner, including the scope and qualifications needed to state the resulting
behavior. Apply the same restriction to authored prose in generator inputs,
including `docs/limits.json` and matrix descriptions. Do not add workflows,
examples or reorganized explanations to these shared regions. The seam migration
requires correcting the limits table's override and refusal names at their
definitions while leaving the guide's copy frozen.

### Handling changes during the transition

Within the trace subjects, selected conversions, two pytest cohorts and seam
scope, the implementing agent may change signed components, contracts,
interfaces, representations, public meanings and technical ownership. Assess
technical merit, evidentiary consequences, user reliance and maintenance cost
before choosing the implementation layer. Retention is a permissible decision.

Guide divergence and signed-app verification cost do not prohibit a remedy.
Sequence verification around those costs. Correct the affected technical accounts
with the behavior. A test reclassification alone cannot repair a product defect
or withdraw a commitment. Seek human input only for genuinely missing authority
or information. No tagged release or publication occurs during this work.

## Working the three plans together

1. Prepare the development/publication checks below. In parallel, map findings,
   perform the planned rehearsals, map cohort equivalence and supply the seam's
   evidence requirements to the reporting design.
2. Establish the reporting capability through the unchanged-app checkpoint.
   Land required build-input changes before its baseline; do not put conversions
   or further build-input changes between its two live batteries.
3. Implement assessed product/test changes, both cohorts and the seam migration.
   Independent work may proceed together. Group signed-app verification as
   specified below.
4. Run final integrated verification once, then finalize the outflows.

For a shared thread, use one trace of statements, producers, readers and tests.
Rehearse before changing that thread's accounts; record the product disposition
here and land its implementation and account changes together. A thread without
an assigned rehearsal does not wait for one. An inconclusive rehearsal adds no
completion obligation.

Where both test authority and product behavior change, exercise the revised test
against existing behavior first. For seam migration, capture the old experiment
before changing entry points; command and callers may then land together with
separately attributable authority changes. Add new controls to a pytest cohort
after establishing that cohort's migration equivalence.

### Development and publication checks

Before the instrument checkpoint, development builds and source-drift checks
compared the guide with the current technical owners. A change to a shared
region or a contract stamp could therefore require changing the guide. The
checkpoint established the following development and publication controls.

- Development generation checks current technical projections, owner regions,
  interface inventory and identities. It checks the guide, including its shared
  regions, limit spans and stamp table, against the bytes at `3d3f8e65`.
  Each technical owner is checked against its current definition.
- Development artifacts and verification receipts record publication withheld.
  The build preserves the frozen guide. Build identity is derived separately
  from the check that establishes publication freshness.
- The checks refuse accidental drift, altered frozen bytes, stale technical
  outputs, wrong identities and inconsistent boundary evidence. When a prose
  guard blocks an authorized change, correct that rule with positive and
  negative controls and retain its other checks.
- Preflight, acceptance, archive and publication each check source freshness
  at the tagged revision. A relabeled development candidate must still pass
  that source check. Signing, source/app agreement, provenance, cleanup
  and historical archive rules also apply. The instrument checkpoint exercised
  the four entry points in constructed fixtures. The normally built candidate's
  extracted-battery case belongs to final integrated verification.

Reporting-reader support and the routed controls for intentional divergence
landed at the instrument checkpoint. The first divergent limits change
subsequently passed with publication-fresh and diverged fixture sources.

## Assess and dispose of findings

Use a claim at a particular boundary as the unit. Split compound entries and
link related claims without renumbering or discarding distinct evidence. Later
entries qualify earlier ones; they do not automatically supersede them. Include
unverified DT-44 leads and temporarily unallocated observations in the map.
A bounded assessment may proceed while the rest are being mapped.

For each assessment, record:

- Observation versus inference; input form, representation, observer and time.
- Original references, inspected revision/build, evidence class and availability.
- The obligation, producer behavior, reader checks and assertions being compared.
- The remaining defect, limitation or uncertainty; the chosen treatment and its
  user/developer consequence.
- A discriminating check, or the reason further evidence would not change the
  decision. Name any missing authority, information or scope needed to proceed.

Distinguish explicit commitments, consequential ambiguities, unsupported
inferences and inaccurate mechanism accounts. An unimplemented promise may
still create reliance; an inference beyond the observations need not become a
product obligation. Agreement among code, tests and prose does not settle the
choice. Use the review's
[acceptance boundary map](DOCUMENTATION-TRACE-REVIEW.md#acceptance-boundary-map-what-each-accepting-boundary-checks-and-over-which-representation)
and [observation-time account](DOCUMENTATION-TRACE-REVIEW.md#observation-time-cross-anchor-account)
where applicable.

Choose behavior, assertion/coverage repair, arrangement change or reasoned
retention on that evidence. Record a present-tense judgment: what is established,
what remains defective or unknown, what treatment is chosen and whether its
consequences are accepted. State accepted limits beside their current technical
claims. A referral or future documentation task does not close an unresolved
product decision; accepted uncertainty does not establish the underlying fact.

Before implementing a selected remedy, identify affected owners/readers,
compatibility consequences, exclusions and the incorrect behavior its checks
must distinguish. Update admission, transport, fixtures and technical accounts
together where affected, using owning generators and the publication boundary.

### Selected assessment threads

| Thread | Work and discriminating evidence |
| --- | --- |
| Transport: DT-31/32/42, DT-113–119 | Start from the [synthesis](DOCUMENTATION-TRACE-REVIEW.md#how-dt-31-dt-32-and-dt-42-relate). Establish reachable submission/capture/host-reply combinations and evidence after the first failure. Decide separately on unreachable states/fixtures, foreign decoding and actor helper invocation. Assess `policy_check` presence/status and whole-request actor failure. Independent compilation does not establish worker progress or explain a lost reply. Pair with the acceptance fallback rehearsal and overhaul run-flow checks. |
| Readers: DT-53/132 and identity relations | Identify selected callers omitting the lifecycle oracle or equivalent assertions and correct credited coverage. Pair with the association rehearsal and overhaul reader contrasts; do not presume a unified validator. |
| Erasure: DT-63/124/125 | Separate host and worker coverage and last-use clearing from final teardown. Use the overhaul's assertion repair and any justified pre-teardown observation. |
| Import/receipts: DT-82/84/85/98/103 and related findings | Distinguish dropped scanner information, missed literal imports, unevaluated forms, receipt input coverage and inference about application. [Source association holds by construction](DOCUMENTATION-TRACE-REVIEW.md#passages-in-the-appended-account-that-need-narrower-wording); compiler-file inputs lack that observation. A source-digest comparison cannot supply it. Decide the instrument's limit separately from scanner repairs. Pair receipt decisions with the capture rehearsal and label-admission checks. |
| Descendant lifetime | Assess remaining truthful-evidence and effect obligations for the overhaul's survivor conversion. Rule by name on the relation that makes `leader_exit_and_eof` valid only with `not_requested`: the [lifecycle surface](../docs/contract/32-lifecycle.surface.md), [controller admission](../controller/src/porcelain_native.rs), the [Swift evidence reader](../runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift) and the [consumer](../tests/lib/consumer.py) enforce it, and the worker signals the group only after a deadline, observation error or local fault. Retained, it is a truthful-evidence commitment: a product that ends the descendant at ordinary completion must change that relation and its readers together, and the reduction account says so. This has no DT identifier and does not join the DT coverage map. |
| DT-55/56 | Decide exec-output representation; preserve embedded-NUL and split-UTF-8 contrasts, retained content and loss indicators. |
| DT-74 | Distinguish absent registry from failed inspection using absent path, inaccessible ancestor and unreadable-file contrasts. |
| DT-89 | Contrast readable and unreadable selected source directories; omission must not masquerade as complete discovery. |
| DT-23/51 | Assess declared-unapplied actor classification with both validator spawn and decode failures beside applied counterparts. |
| DT-09/26/54/58/69/91 | Correct inaccurate accounts through their owners and verify that cited support establishes the revised scope. |

### Bounded test-seam migration

Move these eight controls to `test-input run REQUEST` with explicit control flags:

- Worker: `worker_timeout_ms`, `worker_pre_ready_hang_ms`,
  `worker_post_apply_hang_ms`, `worker_post_apply_kill_signal`,
  `worker_kill_before_publish_slot`.
- Validator: `validator_executable_path`, `validator_io_timeout_ms`,
  `validator_total_timeout_ms`.

Use the overhaul's [caller map](TEST-OUTCOME-OVERHAUL-PLAN.md#selected-seam-callers).
Migrate selected invocations, not entire catalog families. Leave
`worker_executable_path` and `actor_equipment_executable_paths` in the
`_test_overrides` block of an ordinary submission, each on its existing request
form, preserving their coverage and reference account.

Reuse run orchestration. Carry explicit experimental mode outside the ordinary
request through client transport and host admission. Ordinary submissions reject
selected legacy keys, including inert values, before activation. Experimental
submissions take controls only through explicit arguments and reject a nonempty
legacy override block. Internal representations may be reused; they must not
leave an ordinary activation bypass. Flag spelling remains an implementation
choice. This is interface separation, not a new authentication claim.

Of the ten combined oversize pairs in
[failure_boundaries/check.py](../tests/suites/failure_boundaries/check.py), only
`worker_executable_path` with `validator_executable_path` crosses this boundary.
Neither route can carry that pair afterwards. Retire that live pair, retaining
its bounded/sanitized refusal checks in the existing direct-orchestrator pairs
in [QueryAdmissionTests.swift](../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift).
Do not credit those checks as CLI/XPC coverage for the retired combination;
narrow the live case's claim. Its other nine pairs follow their fields' routes.
Source inspection at `4c92ea68` of live request construction, wrappers and
fixtures found no other combination of a selected control with an unselected
substitution. Mixed constructed unit inputs and reply fixtures are not live
submissions; this is source evidence, not executed migration equivalence.

Keep `test-input read` publication-only. Preserve the ordinary sentinel effect
of `worker_timeout_ms` and the separate actor execution allowance; actor
delay/signal/slot controls still reach actor workers. Do not add fault mechanisms,
fabricated outcomes, weaker cleanup or a separate test-only binary.

Capture old positive/rejected experiments before changing entry points. Land
executable/caller changes after the instrument checkpoint on an identified
rebuilt app. The overhaul owns equivalence, per-control activation/refusal checks
and completion before final verification; the acceptance plan rehearses removal
of validator substitution.

## Verification sequence

Use [tests/AGENTS.md](../tests/AGENTS.md) and
[CHANGE-VERIFICATION.md](../tests/CHANGE-VERIFICATION.md), registered selections,
fresh owned output and the checkout lock. Run routed checks at the carrying
commit. With concurrent executors, run broad selections in a worktree pinned to
a commit and reserve quiet windows for the live worker-wait pilot.

Before tests execute for a consequential change, retain the intended verification
selection and rationale in the existing commit or working assessment. If later
broader testing finds a consequential failure outside that selection, record the
failure and establishing evidence, its established or suspected relationship to
the change, whether existing guidance or known dependencies could have predicted
it, and whether it is a product regression, test-infrastructure failure,
environmental problem or unresolved cause. Note broader runs with no unexpected
failures without claiming the selection was sufficient.

These notes, the cost observations below and the overhaul's marginal-value notes
support an out-of-band assessment of the testing regime, potentially including a
later bounded counterfactual experiment. Use existing commits, working assessments,
run identifiers, receipts and retained evidence; no new registry, summary document
or permanent format. They add no implementation requirements, acceptance/completion
conditions or stage dependencies, and require no extra testing or investigation.
Missing cost detail does not block implementation; unexplained surprises remain
findings; uncertain marginal value requires neither retirement nor preservation.
The observations authorize no additional test retirement, reduced verification,
default-membership changes or relaxed guarantees. Guide rewriting and decisions
about unsupported user behavior remain outside this exercise.

| Changed boundary | Evidence when it lands |
| --- | --- |
| Reporting/release readers | Overhaul controls, then the instrument checkpoint. |
| Installation, registry, reconciliation or cleanup | Applicable `runner_byoxpc` opt-ins in a logged-in GUI session; verify owned resources absent before continuing. |
| Worker wait, release store, query eligibility or observers | `witness_contract/order_barrier_mutations` with each change. |
| Wire, layout, schema or identity derivation | Owning regeneration, `source_drift`, `runner_abi_layout`, default build controls and a rebuild before the next change. |
| Documentation | Owning generation and `source_drift`. Check [build-contract inputs](../docs/build_contract.py): Rust test edits under `controller/src` require rebuilding; `runner/Tests` and most of `tests/` do not. |

### Three boundaries for broad runs

At the instrument checkpoint and final integrated verification, retain what
existing timing, command, dependency and execution receipts establish about build
and signing, fixture construction/preparation, experiment/observation duration,
evidence interpretation/reporting, cleanup, serial dependencies, repeated
preparation and substantial waiting. Where evidence permits, distinguish the cost
of executing a case from the additional cost of selecting it with its dependencies,
and costs intrinsic to the observation from supporting apparatus and verification
organization. Mark measured intervals, inferred costs and unknown time separately;
total wall-clock duration does not establish a complete decomposition. Add no
profiling, instrumentation or extra batteries for this account.

**Instrument checkpoint.** Complete development/build publication support, then
run the default battery immediately before reporting capability lands. Land
capability without conversions or build-contract changes and run the default
battery against the same app again. Retain raw inputs and both reporting
revisions; verify the unchanged build-contract digest.

Replay identical retained reports, events, family/control receipts, command
accounts and captured selection/authority context through old and new
`suite_run.reconcile`, `account`, `finish` and battery-validation paths in
isolated outputs. Replay inputs are raw records: case reports, event, phase and
operation streams, the `plan.json` selection and recorded command exits. Derived
fields in a retained `run.json` or `dispatch.json` are comparison targets, never
inputs. The dependency gate is inline in `suite_run.execute`; exercise it
through dispatcher fixture runs instead.

Independently specified counts, decisions and failure reasons must agree for
unchanged authority. Separate new informational/advisory fixtures have explicit
expected deltas or old-reader unsupported-form refusals. Include corruption,
omission, contradictory authority and incomplete accounting beside valid
unfavorable judgments. Reuse existing controls; any feeding adapter must not
invent evidence. Normalize only incidental output locations, never identities,
evidence, authority or failure distinctions.

Explain live differences from observations and replay before crediting the
checkpoint. An explained failed obligation remains a failure. Prefer replay and
affected-case checks to another battery. Later shared-reader changes need the
same deterministic comparison; add a live pair only for changed live collection
or an integration uncertainty existing runs/replay cannot resolve. State that
reason and keep build-input changes out of the comparison.

Read a completed battery with the revised battery validator at this checkpoint
and at the first battery containing a converted case and both migrated families;
these investigations credit no case. Run the read-only prune preview against
retained archives. Replays must not alter original evidence, producer semantics,
outcomes or retention eligibility.

**Signed-app checkpoints.** Group product changes with disjoint routed selections
and run one default battery per group. Locate a failure outside those selections
with an intermediate build. Run each converted or migrated case when it lands.

**Final integrated verification.** Once all selected work is in, run offline and
source-drift controls, a current signed build, the default battery with relevant
opt-ins, then `preflight/build_refusal_controls`. Build before any app-bound
selection that requires the new app. Adapt the long control's existing nested
battery; do not add another broad battery.

Use `control_release_battery`'s one live nested battery on an extracted, normally
built development candidate through the existing extraction, artifact,
command-accounting and battery-validation machinery. Record development identity
and publication withheld; the receipt is not release acceptance. Preserve
signature, source identity, provenance and cleanup checks. Apple-response
stand-ins establish only their stated control behavior.

In that case, strict release preflight/acceptance must reject development
publication boundaries and attempted relabeling/tagging before an expensive
battery or publication. Retain constructed positive/negative controls for genuine
release identity and strict freshness. Do not refresh frozen guide content in
a fixture to manufacture release readiness. Credit candidate execution and
publication refusal separately. A future release follows the
[release procedure](../docs/SIGNING.md#release-procedure) after guide rewriting
and full publication checks.

## Closing outflows and completion

Draft the following after dispositions, rehearsals and reduction accounts are
recorded; finalize them against final integrated evidence. Use a date, source
revision and status. Resolve unsupported entries or mark their uncertainty.

### User-responsibility outflow

Write `records/USER-RESPONSIBILITY-OUTFLOW.md`, one entry per resulting user duty:
condition and responsible role; action or restraint; consequence of omission;
output indicating applicability, or its absence; established/unsettled standing;
and supporting behavior/evidence with scope and limits.

Include obligations left by retained limits, delegated checks or narrowed
claims, including conclusions users must refrain from drawing. Exclude
implementation assumptions, optional practices, hypothetical obligations and
limitations without user consequences. Experimental seam operators and
build/test/release duties belong in working guidance. A substituted component's
behavior does not itself create an ordinary user's duty.

An established responsibility needs evidence and a completed disposition. For
an unsettled candidate, state missing evidence, authority or information and
its consequence. Do not present it as an obligation merely out of caution.

### Judgments for the maintainer

Write `records/MAINTAINER-JUDGMENT-OUTFLOW.md` for consequential choices, reasons
and unresolved matters needed to understand the resulting product. Give the
present responsibility/limit, reason, evidence, current owner and anything still
missing. Reference user duties rather than repeating them. This is not an approval
queue or a mandatory history of every change.

### Material reserved beyond this work

Retain explanation beyond current code and Git only if its absence could cause
a consequential future mistake. This can include irreproducible decisive evidence,
deliberate non-obligations, otherwise undiscoverable design reasons and failed
experiments establishing durable observation limits. Use existing evidence
ownership/retention mechanisms.

Put present limits beside their technical claims; put non-enforcement reasons
in the owning suite and changing commit, and shared testing principles in working
guidance. Use the acceptance analysis where suites may share a premise. Do not
create a permanent disposition registry. Retire plans/outflows once consumed by
the subsequent guide/release work.

Record a brief release account of changed result/evidence semantics, converted
cases, experimental entry points and required release-procedure changes.

Completion requires a disposition for every observation and qualification,
verified selected remedies or reasoned retention, the overhaul's conversions,
cohorts and seam migration, and the final outflows. Check both directions:
each original observation has a disposition and each change has identified
claims and decisions behind it. Unaccepted unresolved decisions remain pending.

## Instrument preparation assessment — 2026-11-17

Status: source mapping and bounded decisions before the instrument checkpoint;
not completion of the trace review. The inspected implementation is `887b485f`.
`git diff --name-only 3d3f8e65 887b485f -- controller runner tests docs` is empty,
so the plans' source references remain applicable at this starting point. No
registered case, live experiment, migration or product change is credited by
this preparation. The original review remains intact. The shared rehearsals
are recorded in the acceptance plan, and the scenario/equipment requirements
in the overhaul plan; they are the same four threads, not additional findings.

Initial environment inventory: one primary worktree, clean `887b485f`, about
160 GiB available. `tests/out` uses 1.2 GiB, all in the newest protected release
acceptance; four protected archives (`v0.3.4`–`v0.3.7`) use 836 MiB. Total
`dist` is 877 MiB, `.tmp` 720 MiB (713 MiB in `contract-trio`), Rust cache
3.2 GiB, `runner/.build` 270 MiB and `builddir` 56 MiB. The scratch root is
`/private/tmp/pw-trace-checkpoint`. The coordinator's read-only prune preview
there, `prune-initial.json`, has no blockers, targets or unmanaged output.
The sandboxed preview's signature/provenance mismatch disappeared when the
same bytes were checked outside the automation sandbox. Likewise `security`
listed no signing identities inside the sandbox and listed
`Developer ID Application: Adam Hyland (42D369QV8E)` outside. These observations
support those environmental diagnoses only; no artifacts were removed.

Verification intent, recorded before the consequential executions: publication
`source_drift` and affected build/preflight controls, then a signed build and
pinned default baseline. Reporting follows with dispatcher and shell-helper
controls including `dispatcher/pytest_controls`, preflight release, publication,
rotation and deadline controls, and the existing exec family. Raw deterministic
replay and the same-app default pair establish the instrument checkpoint;
read the completed battery with the revised validator and preview pruning.
The boundary rationale is generation/publication admission first, then shared
result interpretation, command/phase accounting and release rereading. There
are no conversion, cohort or seam executable changes in this selection.

### Evidence availability and reuse limits

Checked paths on 2026-11-17, before implementation:

| Evidence | Availability and permissible use |
| --- | --- |
| `.tmp/contract-trio/transport/` | Present, including controlled-client app and target directories. Original record distinguishes native, controlled-client, typed and source evidence. Retained capture bytes can inform discriminating inputs; their presence is not a current case pass. |
| `.tmp/contract-trio/observation-time/` | Present. The original `/private/tmp/pw-trio-ot-xVGRMW/target` is absent. Captures can establish what the prior observation recorded; live target identity cannot be reconstructed from current files. |
| `.tmp/contract-trio/acceptance/` | Present, including `reader-case-map.jsonl` and Cargo output. Original rebound frames and placeholder limitations still apply; the old failing seam run is not successful battery evidence. |
| `/private/tmp/pw-failure-trace-elssragi/`, `/private/tmp/pw-authority-trace-3QC3qQ/` | Absent. Use the review's retained descriptions and source reading; rerun an applicable discriminating control before making a new executed claim. |
| Three joint import/receipt outputs under the review's named Claude scratchpad | Absent. `.tmp/82-103-OBSV.md` and `.tmp/SHARED-INTERP-FOLLOW-UP.md` remain, as do their incorporated statements in the review. These are accounts of earlier observations, not raw observations available for replay. |
| The review's CONTRACT-tracing scratch directory, `/private/tmp/claude-501/…/1b7c19fb-c395-4c94-9f87-0906550f66e3/scratchpad/` | Absent when checked on 2026-11-19. Any item in DT-22–44 that the review reproduced there is an account of an earlier observation, not replayable evidence (CL.5). |

All `.tmp` material above is gitignored local development evidence with no
retention guarantee. Availability was checked, not its complete provenance or
hash correspondence. No present directory is adopted as release evidence, and
no original report is rewritten. The app used by those investigations was the
`8b5de2b2` build described there; the checkpoint must identify its own candidate.

### Finding coverage map

This map allocates every DT identifier for subsequent disposition. A row is a
reading/decision boundary, not a claim that its entries have one defect or one
remedy. Compound subfindings and each entry's qualifications remain separate
obligations at their original anchors. These were the open product questions at the preparation checkpoint.
The [disposition index](#dispositions-by-coverage-map-row) records the later
decisions for all 1,036 claims.

| Original entries | Boundary to assess; qualifications to preserve |
| --- | --- |
| DT-01–04 | Contract generation: nested regions, moved destinations, link bytes and condition scope are four different preservation properties. Successful regeneration alone establishes none of their semantic adequacy. |
| DT-05–08 | Authored/imported ownership, changed-item lookup, example provenance and development-input inventory; DT-08 joins DT-91 without dropping its original account. |
| DT-09–10 | Optional log collection and unavailable-clock timeout semantics; separate operator account from observed cancellation. |
| DT-11–14 | Executed evidence availability, historical counts, barrier support and declared check links; unavailable execution remains unavailable. |
| DT-15–21 | Reading routes, commitment placement, changed-file coverage, presence rules, field ownership, known-gap navigation and distinct-rule link labels. DT-18's undefined phrase and 28 missing presence rules need separate dispositions. |
| DT-22/57 | Empty ordinary step identity: eligible and excluded queries exercise different outcomes. Do not infer request refusal from an oracle failure. |
| DT-23/51 | Declared-unapplied actor classification with failed validator spawn and failed decode, each beside applied counterparts. |
| DT-24/30 | Query meanings and response vocabulary; distinguish emitted values, defensive branches and admitted input domains. |
| DT-25/50/131 | Submitted-target canonical equality, validator identifier/metadata association and literal reader equality; only the association proposition participates in the shared equality rehearsal. |
| DT-26–28 | Augment/selector refusal names and publication under broken/closed stdout. Codes, CLI behavior and output completion remain separate. |
| DT-29/81–87 | Import scanner, resolver and helper projection: nonliteral signal, missed literal, unevaluated forms, hash scope and claimed coverage. Join to receipt assessment only at the shared source/file-input question. |
| DT-31/32/42/113–119 | Transport reachability, error precedence, retained bytes, helper selection and held-input provenance; one fallback trace and rehearsal. Typed constructions are not evidence that the shipped caller reaches those states. |
| DT-33–35 | Dossier first-problem/null cases and install ownership/signing/command result forms; do not merge installation evidence with transport fallback. |
| DT-36/43 | Gate reap before ownership-loss classification and lifecycle rendering/resolution. |
| DT-37–41 | Each smaller statement/source difference, support scope, prose account, index spelling and tour commitment list was assessed separately at its original subfinding. |
| DT-44 | Thirteen leads were unverified at preparation; confirmed statement existence does not verify the reported producer. |
| DT-45/47/49/52 | Status-word promise, pre-encoding versus encoded checks, diagnostic null native return and errno-key presence are distinct producer/reader obligations. |
| DT-46/120/121/129 | Cleanup-trigger derivation/time and actor stop-reason mapping, with gate-reaped actor and transfer-phase qualifications. DT-120 narrows DT-46's history claim. |
| DT-48/130 | Native label/return coherence versus order eligibility, and implication versus equivalence in order readers. A valid unfavorable operation is not invalid evidence. |
| DT-53/132/135 | Lifecycle-claim coverage, byte-consistent envelope readers and shared predicates; do not count repeated use of one predicate as independent judgment. |
| DT-54/58 | Collection byte-limit stop and empty-byte fallback beyond the minimal report. |
| DT-55/56 | Exec retained output: embedded NUL and split UTF-8 independently exercise loss and truncation indications. |
| DT-59–61/133 | Self-transfer visit timing, raw setup association, decoder prerequisites and scheduler authority gate; preserve private header versus public record distinctions. |
| DT-62/65/122/123 | Host custody acceptance, publication gating, delivery relationships and discarded worker custody observation; host and worker observers are separate. |
| DT-63/64/124/125/128 | Host last-use/final teardown, oversized native erasure prefix, worker cumulative observer and terminal byte extent. Call counts, flags, scanned bytes and time cannot substitute for one another. |
| DT-66/126 | Equal raw handles and per-release access effects; native return equality does not establish revocation. |
| DT-67 | Redelegation contrasts' assertion authority versus credited negative effects. |
| DT-68/127 | Pre-exit worker resource publications beside host teardown observations; a historical `held` value does not establish present ownership. |
| DT-69–73/75–80 | Reconcile recovery, present/absent/ambiguous classification, candidate discovery and credited coverage; split each listed smaller observation. |
| DT-74 | Absent registry versus failed inspection: absent path, inaccessible ancestor and unreadable file must remain distinguishable. |
| DT-88–94 | Source inventory, traversal refusal, selected suffixes/roots, framing, metadata and support. DT-89's unreadable directory is a completeness question independent of its digest algorithm. |
| DT-95–104/134 | Receipt host binding, publication/application/completion guards, constant labels, input coverage and capture-view limit; one capture rehearsal. Source binding, compiler-file inputs and application input remain distinct. |
| DT-105–112 | Wire fingerprint, variant production, conditional-null projection, path compaction, reader rule order and shape/support coverage; qualify identity sensitivity independently of actual admission discrimination. |
| Both unnumbered import/receipt investigations | Retain both the first synthesis and follow-up narrowing: source join by construction; file join unobserved; divergence observed only by selected contrasts; effects, file opens and bytes applied are different claims. |

DT-44's thirteen leads are allocated separately: host-wait stop vocabulary;
schedule cancellation/setup-timeout vocabulary; ordinary wait progress index;
absent versus incomplete `not_reached` slot; EOF beside collection deadline;
actor schedule versus worker allowance; `actor_unavailable` wording;
capacity-refusal policy format; arrival/completion sampling points;
validation metadata persistence; defensive unsupported vocabulary; adjacent
readiness/count statements; and reporting-failure family applicability. All
thirteen were leads at this preparation boundary. The later disposition of
the EOF case relied on the branch text. The potential closing-stdout/held-stdin
fixture was unnecessary for that decision.

### Bounded shared assessments for capability design

**Descendant lifetime (no DT identifier).** Retain the named
`leader_exit_and_eof`/`not_requested` relation as a truthful-evidence commitment.
Source inspection of `pw_worker_exec.h` shows the group signal is attempted only
after deadline, observation error or local fault; the lifecycle surface,
`porcelain_native.rs`, `PWRunnerAttemptEvidence.swift` and `consumer.py` check
the relation. The existing survivor checker additionally requires a live child
with its original generation/group and ping, before interpreting JSON. That
survival requirement may be withdrawn without withdrawing the truthful account
of the product's calls. The subsequent survivor conversion classified
either that live generation or its independently registered prior exit, retaining
later file effects and separate settlement. A missing ping by itself is not
an observed exit. A product that itself kills the descendant at ordinary
completion is still refused by the retained relation; accepting that product
would require a coordinated product/reader change beyond this conversion.
This decision is based on inspected call conditions and explicit existing
meaning, not a new live descendant experiment.

**Import and receipt association.** Retain the distinction between held-source
association and compiler-file-input association. `run_flow.rs` constructs the
dossier from the resolved value and serializes it once for delivery;
`decodeProfileCapture` checks the worker source/parameter digests against host
inputs. An added dossier/receipt source-digest comparison would not establish
which imported bytes the compiler read. The later dispositions treated the scanner, dropped helper
signal and private capture-view limit separately. R12 changed the scanner.
No new compiler-file observer or authenticity claim is introduced by reporting.

**Reader and erasure claims.** The reporting foundation must allow a checker
to fail an enforced truth/validity obligation while carrying an unfavorable
advisory comparison. It must not silently promote `consumer.validate` to the
lifecycle oracle, or final `erased` flags to last-use observation. The dispositions assign the selected assertions and technical
statements individually, with the independent reader/byte-observer contrasts. No additional observer is justified
merely to make the reporting layer uniform.

The acceptance rehearsals identified dependencies before the product decisions.
R9 selected byte-exact validator association. R10 removed whole-request
fallback for actor requests and kept per-actor capture. The failed-application
capture proposal was declined. The acceptance plan records all four comparisons.

## Instrument implementation and verification

Development/publication support is carried by `bba8bca3`, with generator and
fixture corrections in `f141748e`, `98ef966c` and `2f4d76e4`. The signed build at
`2f4d76e4` uses the declared input identity
`development:b55acb20d6a00395f6a422eafef1a4c18fd64e5140b71a1331cbe3b76744719e`.
Its seven executables and two seals passed Developer ID chain, hardened-runtime,
team and secure-timestamp checks. Source and distributed guide bytes retain
SHA-256 `1e886e4ab5ccaf9aa73fe9c7d6e47e87bcf37d3d3c8caf2e093f38bced97d64d`.

The following are local managed development observations, subject to ordinary
retention, not retained release acceptance. Each directory is under
`tests/out/runs/` and includes its terminal `run.json`, attached `console.txt`
and supplemental `selected-plan.json`; `plan.json` is the actual execution plan.

| Directory / run ID | Result and scope |
| --- | --- |
| `trace-publication-controls` / `20261117T225742Z_635dac19` | At `bba8bca3`, 8 pass / 8 fail, 688424 ms. Provenance and release acceptance controls passed; stale stage citations, missing transitive generator inputs and fixture assumptions failed. |
| `trace-publication-fixes` / `20261117T231313Z_27553dd7` | At `f141748e`, all 11 source-drift cases and build-entry controls passed; release publication/rotation failed because synthetic catalogs omitted required citations. 762421 ms. |
| `trace-publication-release-fixes` / `20261117T232644Z_d901d5f5` | At `98ef966c`, both selected controls failed at later fixture assumptions: exact diagnostic counts and deleted release ancestry. 167745 ms. |
| `trace-publication-release-contracts` / `20261117T233143Z_4702cf5a` | At `2f4d76e4`, publication and rotation both passed, including independent freshness and identity refusals. 255556 ms. |
| `trace-instrument-before` / `20261117T233807Z_b25fa0ec` | At `2f4d76e4`, default battery passed: 233 completed parents, 232 legacy reports, nine exec-family items, no harness errors, app inventory unchanged. 1888317 ms. |

The failed controls establish implementation/fixture defects, not environmental
refusals; their original reports remain failures. Their dependencies were within
the preselected generator/publication routes. The default baseline produced no
unexpected failure. Initial restrictive-harness prune/signing discovery failures
passed on the same bytes when the exact read-only operations ran unsandboxed.
Subsequent signing and test execution used that documented environment.

Reporting followed the planned dispatcher/shell-helper selection, including
`dispatcher/pytest_controls`, plus release, publication, rotation, deadline and
existing exec-family controls. Those owners cover shared accounting, authority,
command ownership, candidate/portable rereading and the existing native sequence.
The completed checkpoint and the reasons for affected-case replacements are
recorded below. No conversion, cohort migration or executable seam change was
included.

Observed durations above are dispatcher wall time, not a full cost decomposition.
Individual construction/command/cleanup receipts retain their measured intervals;
unrecorded decomposition remains unknown. Repeated strict generation in fixture
source trees is supporting verification work. No profiling or extra battery was
added for this account.

At the baseline boundary, managed output occupies about 6.9 GiB, including the
2.7 GiB baseline. Main caches remain about 3.2 GiB Rust, 270 MiB SwiftPM and
56 MiB Meson; `.tmp` remains about 720 MiB. The identifiable investigation root
is under 3 MiB. Volume free space is about 149 GiB. Inspection of relevant
scratch/cache directories and swap did not attribute the remaining volume-level
growth to these repository outputs. Unrelated temporary content was not removed.
No pruning, evidence relocation or additional worktree has been introduced.

### Reporting implementation and checkpoint disposition

Reporting capability is implemented in `c1744aae`, with import/fixture and
literal-argument corrections in `28496e25` and `7f47ed00`. `bd954397` restores
the existing Python file-start convention without weakening its guard.
`5577a4eb` binds new meanings to the captured outer producer contract throughout
reconciliation, family accounting, summaries, display and candidate/release
validation. Opaque legacy fields retain their producing meaning, including in
mixed version-2 runs. These commits change the shared instrument and its controls;
they do not convert selected cases, migrate either cohort or change the executable
test seam. The original native exec sequence remains intact.

Additional managed development runs, with the same local-only availability and
ordinary retention limits as the table above:

| Directory / run ID | Result and scope |
| --- | --- |
| `trace-reporting-controls` / `20261118T001532Z_e5fb5e5e` | At `c1744aae`, 11 parent passes / 9 failures, all 20 accounted; 404407 ms. All four preflight cases, accounting replay and the nine-item native family passed. Isolated helper import and copied-fixture dependency defects failed the other routes. |
| `trace-reporting-import-fixes` / `20261118T002331Z_48c07455` | At `28496e25`, 14 passes / one failure, 256664 ms. Shell and dispatcher controls passed; the new pytest sentinel lacked its executable bit. |
| `trace-reporting-fixture-fixes` / `20261118T003012Z_1172d7c1` | At `7f47ed00`, dispatcher and pytest controls both passed, 136238 ms, including actual dependent/neighbor effects. |
| `trace-instrument-after` / `20261118T003402Z_e6c29e40` | At `7f47ed00`, 232 parent passes / one failure, all 233 completed; 1883865 ms. `source_drift/direct_python_start` rejected `-P` on the new file entry point. The failed report and diagnostic remain unchanged. |
| `trace-reporting-compatibility` / `20261118T010714Z_cc968f17` | At `5577a4eb`, all eight selected parents passed, including nine exec-family items; 198593 ms. Covers the startup guard, finalizers, interpreter boundary, dispatcher/accounting/pytest controls and candidate acceptance. |
| `trace-instrument-after-corrected` / `20261118T011154Z_5cfcec0a` | At `5577a4eb`, default battery passed: 233 parents, 232 legacy reports and nine exec-family items; no harness errors; 1978348 ms. |

The replacement default is necessary verification of the corrected live reporter
startup path, not additional coverage for this account. The initial post-capability
failure is not reclassified. The original independent success expectations remain
at `trace-instrument-before/checkpoint-expected-counts.json`; they were not relaxed
to fit that failure. Both successful defaults have the same selected authority,
prerequisites, command declarations and nested population. No conversion or build
input changed between them, and no app rebuild intervened. Their original producer
contexts and distinct source identities remain intact.

The instrument checkpoint is established. Under
`trace-reporting-compatibility/investigations/reporting-checkpoint/`,
`comparison/checkpoint-replay.json` records 455 passing checks and 65 commands:
13 unchanged-authority constructed histories agree through both readers, two
incomplete-history/ownership inputs receive their specified apparatus refusals,
eight version-2 histories produce the expected new decisions and old-reader
unsupported-contract refusals, and both live datasets agree under both readers.
The readers are the immutable Python source slices for
`2f4d76e49e5b6b4dff25307b2f0e36ffbe10e1e6` and
`5577a4ebc81fd48959ae5bfaba18af22a0ed4f1b`. Apparatus, independent expectations,
raw fixtures, commands, comparisons and outputs remain together. Raw command
observations and captured plans drive interpretation; derived judgments are only
comparison targets. Reader finish time is new; experimental command times,
identities, evidence and authority are not normalized.

`completed-battery-reread.json` records the revised validator's acceptance of both
original completed batteries, unchanged referenced bytes, identical four app
inventories, unchanged build-contract identity and source/distributed guide bytes
equal to `3d3f8e65`. This is interpretation, not renewed native execution, signing,
current resource absence or release acceptance. The replay investigation adds no
case credit to its eight-case owning run.

Decisive controls can be inspected without treating a successful parser as an
independent product observer. All paths below are relative to `tests/out/runs/`:

- `trace-instrument-before/suites/source_drift/limits_documentation/artifacts/limits-receipts.json`
  controls 000–002 establish permitted owner divergence, frozen-guide/stale-owner
  refusals and staging identity checks.
  `trace-instrument-before/suites/source_drift/build_contracts/artifacts/build-contracts-receipts.json`
  control 079 exercises contract projection and strict publication separately.
- `trace-instrument-after-corrected/suites/preflight/release_controls/artifacts/`
  retains missing/inconsistent publication-boundary inspections, the withheld
  archive refusal, `candidate_valid/acceptance.json` and its refused pointer
  downgrade controls. These candidate command/signature responses are constructed;
  they are not a normally built extracted candidate's live battery.
- The same run's `suites/preflight/release_publish_controls/artifacts/publication-freshness/freshness.json`
  and `active-freeze.txt` exercise actual tagged-source freshness and relabeling
  refusal. `archive/acceptance-kind-controls.json`, and the rotation case's
  `artifacts/battery-contract/acceptance-kind-controls.json`, exercise archive and
  portable-release kind boundaries beside historical and valid-release neighbors.
- `trace-reporting-compatibility/suites/dispatcher/controls/artifacts/outcomes/controls.json`
  retains independent shell outcomes, actual dependency/neighbor effects and the
  real pilot reader over constructed raw trials. The pytest case's
  `artifacts/outcome-mechanism-comparison.json` records all eleven mechanism
  contrasts; its mixed runs and legacy-family reread retain exact parent/nested
  scopes, pure/commanded behavior and historical-extension boundaries.

The publication receipt extraction is retained as
`investigations/reporting-checkpoint/publication-verification-final.txt` in the
compatibility run. Its references to earlier passing cases inside a failed run
remain scoped to those cases and their revisions; the successful corrected default
also executes the publication owners with the final implementation.

### Cost and retained state at the instrument checkpoint

The successful live batteries took 1888317 and 1978348 ms; their recorded invocation
intervals sum to 1883932 and 1970235 ms. Both record zero system sleep. The largest
post-capability intervals are build-contract controls (251143 ms), generator
controls (214187 ms), publication controls (212134 ms), extension boundaries
(92646 ms) and held-phase footprint (87886 ms). The largest increases are in
publication and acceptance controls (25599 and 20362 ms); these are measured
interval differences, not a causal or performance conclusion. Replay command
intervals sum to 352.155 s, including copying, hashing and interpretation.

The build console records compatible-cache reuse and 9.73 s of Cargo compilation;
it does not isolate full build, native compilation, signing or packaging duration.
Fixture receipts separately time bounded generation and rejection operations;
candidate fixture battery values are authored responses, not measured execution.
Construction, interpretation, cleanup and waiting cannot be fully separated from
these receipts. No profiling or extra battery was added to obtain cost detail.

One primary implementation checkout remains on `main`; no second worktree or
temporary implementation checkout was created. Initial inspection found about
160 GiB free and 1.2 GiB of managed output. At this boundary `du` reports about
25.5 GiB under `tests/out`, including 10.9 GiB of replay outputs. Free space is
about 131 GiB before the final preview and 129 GiB at the final check. Replay uses
APFS clones; these directory totals are not
an additive measure of unique physical allocation. The existing Rust, SwiftPM
and Meson caches remain near 3.2 GiB, 270 MiB and 56 MiB; `.tmp` remains about
720 MiB and `dist` about 877 MiB. They remain available for the next build stage.
The prior `.tmp/contract-trio` evidence and its availability limitations are
unchanged. Final system-swap inspection reports 2 GiB allocated and about 1.54 GiB
used, compared with zero at the earlier inspection. No particular run is assigned
that growth. Inspected temporary/compiler caches and swap do not fully explain
the volume-level change; the remaining allocation is unattributed. Unrelated
contents were not removed.

The compatibility investigation's `prune-checkpoint.json` is the read-only
preview: all eleven development runs are eligible, with no blockers, failures,
missing acceptance or unmanaged output. It retains archives `v0.3.4`–`v0.3.7`
and `tests/out/release-acceptance/run-9e17e41c6b99440c8359cf2163b7cfa1`. Applying
the uniform sweep would also remove the checkpoint evidence, so it was not
applied. There are no new pins, keep lists or protected copies, and no resource
cleanup obligation was reported by the preview. These development observations
remain gitignored and subject to ordinary retention; they are not release evidence.
The single disposable scratch root `/private/tmp/pw-trace-checkpoint` is removed
after retaining the decisive apparatus, readers, expectations, transcripts and
receipts in the owned runs. No managed evidence is manually removed.

Work paused here after the instrument checkpoint. The subsequent stages
compared both migrated cohorts and the experimental control routes, converted
the selected cases, and landed R1–R14. The survivor conversion retained the
`leader_exit_and_eof`/`not_requested` obligation. The extracted development
candidate and the final clean-stamped build remain on the
[verification schedule](#product-group-checkpoint).

## Integrated implementation — 2026-11-17

This section records what landed after the instrument checkpoint. The
[current handoff](#product-group-checkpoint) identifies the remaining stages
and the evidence for the product group.

### Starting state and environment

The checkout was clean on `main` at `837296af`, eleven commits ahead of the
remote, with one worktree and no stash. The signed app in `dist/` is the
`2f4d76e4` build; `policy-witness --version` and `dist/publication.json` both
report
`development:b55acb20d6a00395f6a422eafef1a4c18fd64e5140b71a1331cbe3b76744719e`
with publication withheld and guide SHA-256 `1e886e4a…d64d`.
`git diff --stat 3d3f8e65 837296af -- controller runner docs build.sh` shows
only the publication-boundary changes of `bba8bca3`–`2f4d76e4` and generated
worker-identity constants in product source. The eleven checkpoint runs under
`tests/out/runs/` were present and untouched.

Inventory at startup: about 26 GiB under `tests/out`, 720 MiB `.tmp`, 877 MiB
`dist`, 3.2 GiB Rust cache, 270 MiB SwiftPM, 56 MiB Meson; 123 GiB free;
2 GiB swap allocated with about 1 GiB used. `/private/tmp/pw-trace-checkpoint`
was absent, as recorded. This stage's one scratch root is
`.tmp/trace-integration/` (gitignored, no retention guarantee). One detached
verification worktree existed during the Markdown cohort's seeded-fault
rounds; its runs were pruned with its own tooling and it was removed. No
pruning has been applied in the primary checkout and no pin was added.

### Assessment method

Thirteen read-only passes at `837296af` assessed every claim in the review, one
pass per group of shared subjects: 1,036 claim rows, counting each DT entry,
lettered subfinding, qualification, DT-44 lead and the two unnumbered
import/receipt investigations. Each pass re-read current source, recorded what
it executed on the `2f4d76e4` app or on retained local runs, and recorded which
of the review's executed evidence is no longer available. No pass modified a
tracked file, built, or ran a registered case. Their per-claim records are in
[trace-assessments/](trace-assessments/README.md). A pass's recommendation is
an input; the decisions are recorded here and govern where the two differ.

Across all passes no product claim in the review had stopped holding. The
passes narrowed or corrected individual review statements; those corrections
are recorded with their rows below. Most of the review's own executed evidence
(its scratch directories, one retained run and the `8b5de2b2` and build-1482
apps) is no longer available, so executed claims rest on the review's record,
on re-execution where a pass could do it without `run`, and on source reading,
as each row says.

### Selected remedies

These are the product and tool behavior changes selected from the
assessments. Each lands with its checks, its regenerated outputs and the
technical accounts that state the changed behavior. Guide divergence is
accepted; `docs/PolicyWitness.md` stays byte-frozen.

| Id | Findings | Decision |
| --- | --- | --- |
| R1 | DT-55/56 | Exec stream text becomes the decoding of every retained byte (NUL as U+0000, invalid sequences as U+FFFD), cut on a scalar boundary before the truncation marker. The per-stream observation gains bytes received, bytes retained, truncated and an exactness indication. Accepted limit: bytes that are not UTF-8 are flagged, not recoverable. |
| R2 | DT-74 | `load_registry` treats only an absent path as an empty registry. Any other inspection failure, and a registry symlink whose target is missing, refuses, naming the path and the OS error. Reconcile stays report-only. |
| R3 | DT-89, with DT-88/90–94 and the DT-08 statement | Development-identity derivation refuses an unlistable directory or uninspectable entry under a selected root instead of omitting it, and the inputs statement names what is actually selected. The identity of the unchanged tree changes with this edit. |
| R4 | DT-23/51 | A declared-unapplied actor's phases are classified through the declared-setup view, so a failed validator spawn, decode or read gives the applied actor's outcome and exit 1. The prefix filter that also drops a validator pipe or serialization failure for applied actors is decided in the same edit. The independent consumer gains the necessary condition for `finished`. |
| R5 | DT-22/57 | The validator receiver accepts an allow/deny record whose `step_id` is an empty string and joins it to the unique empty-ID step. Request admission is unchanged. The lifecycle adapter rejects only a non-string. |
| R6 | DT-28 | Envelope publishers use a checked write: an unwritable stdout is exit 2 with one stderr line, not a panic with status 101. |
| R7 | DT-34 | `runner install` refuses an `--env XPC_SERVICE_PATH` value that differs from the bundle path, before any machine change. |
| R8 | DT-108, DT-110 | A reply frame that carries a conditional dependent without its guard is a malformed reply, refused by both readers with the bytes retained. Generator-side schema validation refuses the rule combinations that would let the readers disagree. |
| R9 | DT-50/131, with DT-25 | Swift validator association and `query_first` eligibility compare identifiers and query metadata as UTF-8 bytes, as the Rust and Python readers do. Request-name uniqueness and submitted-target equality stay canonical and are stated as such. |
| R10 | DT-42/117 | `policy_check` is null for a request with an `actors` array. Per-actor compile captures are unchanged. |
| R11 | DT-113/116 | The fallback calls on the admitted-reply branch, which cannot run for any value, are deleted; statements say a fallback capture never shares an envelope with a host reply. |
| R12 | DT-29/81–85 | `import_inventory` gains a required boolean for import forms seen and not followed. The scanner follows literal spellings with comments or other whitespace and reports the rest as unfollowed. A scanned file containing an unfollowed form gets a record error with its hash kept. |
| R13 | DT-121 | The host maps the actor scheduler's `schedule_complete`, `ended_before_arrival` and `ended_before_completion` stop reasons to `completion`, so a witnessed host kill no longer projects `unknown`. |
| R14 | DT-01/02 | Contract generation refuses nested generated regions and contract regions in unmapped documents. |

Considered and not selected; each is retained with its limit stated in the
owning technical account:

- Capture despite failed application. The rehearsal's premise is corrected:
  after a returned apply failure the worker publishes `done` and exits 0, so
  the completion guard already holds and the application guard alone withholds
  the copy. No observation of a real apply failure exists, so the value of the
  change to a user is unevidenced. `captured` keeps implying observed
  application.
- Controller comparison of receipt fields with the request (DT-95/134). The
  labels rule is stated as comparing nothing else. A comparison would
  establish consistency between the product's own processes, not authenticity.
- Removal of all actor automatic compilation. R10 removes only the call that
  cannot succeed; per-actor captures remain because the envelope publishes no
  resolved policy text a user could compile by hand.
- Clearing an over-length native extension return beyond the inspected prefix
  (DT-64). The Issue rule is narrowed to the inspected length. Whether the
  native issuer can return more than 16,383 bytes is unknown; observed tokens
  are 208–226 bytes.
- A pre-teardown observer for host last-use clearing (DT-63/124/125). No
  public statement credits a check or run for it; the one crediting test
  comment is narrowed.
- A public carrier for accepted host custody under an unpublished issue slot
  (DT-62/122). The "reported independently" sentence is withdrawn.
- Path-form compaction, the hand-written Swift variant writer and fingerprint
  breadth (DT-105–107/109).
- A new cause label for actor allowance-expiry kills (DT-121 remainder). They
  stay `unknown`; no executed actor-timeout observation exists.

Three corrections outside the review land with these threads because their
statements are false in a current technical owner: the `docs/limits.json` row
that says larger native extension results report `token_oversized`, which
nothing emits; stale status-word comments and failure-contract lines beside
DT-45/47; and a suite README that credits a check that does not exist.

### Order of work and verification intent

This was the original sequence. The November 19 handoff records the order
actually completed and the work scheduled after the product-group stop.

Implementation is serial in the one checkout: one writer at a time edits
tracked files, builds or runs tests. Read-only passes ran beside it.
`records/` is outside every drift scan (`docs/repository_tree.py` prunes it).

1. Cohorts: Markdown reader, then worker-wait pilot controls.
2. Seam: an invocation adapter on the old route and the old experiment on the
   `2f4d76e4` app; then the command, transport and host admission; then the
   callers on the new route, the comparison and the old route's retirement.
3. Host changes in `runner/Sources`: R4, R5, R9, R13.
4. Controller changes: R2, R6, R7; then R10, R11 with the selected `run_flow.rs`
   test corrections; then R12.
5. Exec stream R1; wire R8; identity tool R3.
6. Remaining account corrections, R14 and test-side repairs.
7. Conversions: survivor and aftermath dependencies, retirement, pilot,
   bare-assertion paths.
8. The adapted build-refusal control; one default battery for the grouped
   signed-app changes, reread with the revised validator, and a prune preview;
   final integrated verification; outflows.

Each product thread writes or revises its checks first, runs them against the
app as it stands and keeps that run as the pre-change observation, then
edits, regenerates, rebuilds and runs its routed selection. A pre-change
failure that is exactly the behavior being changed is an expected rejection,
recorded as such; it is not a regression and it is not promoted afterwards.

Intended selections, recorded before the executions: for each thread the
routes `tests/CHANGE-VERIFICATION.md` names for its boundary and the cases its
assessment worklist lists; `witness_contract/order_barrier_mutations` for the
seam (its ordering callers) and for R5 and R9, which widen or change the
query-eligibility inputs; `source_drift`, `runner_abi_layout`, default build
controls and a rebuild for R1 and R8 (wire, layout, schema) and for R3
(identity derivation); the applicable `runner_byoxpc` opt-ins for the seam's
BYOXPC callers and for R2 and R7 where Rust-level controls with a redirected
registry do not suffice. The boundary rationale is: request admission and
transport first (seam), then host classification, controller admission and
publication, evidence representation, and identity derivation last because it
changes every later build's contract value.

### Dispositions by coverage-map row

Every claim has a disposition. [DISPOSITIONS.md](trace-assessments/DISPOSITIONS.md)
records, for each row below, what is established and by which evidence
class, the remaining defect or uncertainty, the treatment of each claim
identifier, the discriminating check, the consequence accepted and the
assessment file holding the per-claim record. It ends with the statements
edited for more than one row and a completeness check: 1,036 claims, none
unplaced. This table is the index and the decision at row level. "Accounts"
means corrections in the owning technical statement; "repair" means an
assertion, control or credited-claim correction; "retained" means reasoned
retention with the limit stated in the named owner. These are dispositions.
The progress entries and current handoff record which edits and checks landed;
the three technical-account passes still own the outstanding statements and
assertions.

| Row | Claims | Decision |
| --- | --- | --- |
| DT-01–04 | 10 | R14 refuses nested regions and regions in unmapped documents. Repair: anchor counts across documents on disk; scope phrases must lie inside their own rule. Retained: rebasing's two unsupported link spellings, stated in the contract authoring account. |
| DT-05–08 | 9 | Accounts: the ownership label, the changed-item lookup's stated scope, the example excerpt's provenance. The DT-08 inputs statement is the single edit made under R3. |
| DT-09–10 | 7 | Accounts: optional log collection is corrected in the account that disagrees with the code; `execution_allowance_exhausted` is stated as also selected when the clock cannot supply the remaining allowance, with the clock-fault and elapsed fields named. |
| DT-11–14 | 18 | Accounts: the executed support grade gains its availability and current-file limits; historical counts are labelled as such. Unavailable execution stays unavailable; what the two reviewed-inputs digests covered is unrecorded and stays unknown. |
| DT-15–21 | 27 | Accounts: the failure contract's one wrong row; presence rules written into each field meaning and the notation's undefined phrase defined; known-gap scope stated; BUILD's commitment associations pruned. Retained: the frozen guide's description of CONTRACT; shared link labels. Per-field admission behavior was derived from decoder storage only and is not exercised. |
| DT-22/57 | 9 | R5. Repair: the lifecycle adapter's identifier rule; an actor-form empty-identifier refusal control; a live empty/non-empty pair. |
| DT-23/51 | 9 | R4, with the consumer's necessary condition for `finished`. The actor ladder is stated for both modes. |
| DT-24/30 | 10 | Accounts: emitted values, defensive branches and admitted domains are separated in each vocabulary statement; `cleanup_trigger` wording follows R13. |
| DT-25/50/131 | 24 | R9. Accounts: target equality and identifier uniqueness are stated as canonical equivalence. Worker-slot joins follow the byte rule only where one side is child-supplied. |
| DT-26–28 | 11 | R6. Accounts: `invalid_value`, `conflicting_selector` with its third condition, and the controller's code list. |
| DT-29/81–87 | 68 | R12. Accounts: the closure statement, and the evidence scope: the inventory is a text scan, neither necessary nor sufficient for compiler evaluation, and no field joins import records to compiler inputs. Retained: records for unevaluated forms; no compiler-read observer. The followed set is established only for macOS 26.7.1 and the helper's host-side compiler. |
| DT-31/32/42/113–119 | 104 | R10 and R11. Accounts: `result.error` precedence, the unreachable reply-less row, null projection for a refused foreign producer, the labels-rule effect as explicit null with exit 1, and limits on what eligibility and a helper exit status establish. Repair: the four `run_flow.rs` tests that read call counts as provenance, and a held-input control for the ordinary form. Retained: defensive unreachable branches other than R11's, stated as unreachable through the shipped client. The lost-reply gap stays a tour gap. |
| DT-33–35 | 10 | R7. Accounts: dossier first-problem order and null cases, plist ownership branches, the `ok` label and stderr-only refusal form of runner commands. |
| DT-36/43 | 6 | Accounts: a wait error cancels for lost ownership only after the reap is confirmed; lifecycle rendering details. |
| DT-37–41 | 34 | Accounts in eight surfaces, the presentation map and two `docs/EXTENSIONS.md` sentences, each matched to unchanged behavior. Retained: two inaccurate sentences that exist only in the frozen guide. |
| DT-44 | 22 | Each of the thirteen leads is verified by reading: confirmed ones are corrected in their owners, two are partly refuted and three are not contradictions. Actor schedule-allowance expiry is stated as `runner_failed`. The EOF lead is decided without the closing-stdout fixture because reachability does not change the disposition. |
| DT-45/47/49/52 | 28 | Accounts: the failure contract withdraws the status-word retention promise the producer stopped keeping in v0.3.5, takes RESPONSE's meaning for a diagnostic's carried return, and credits encoded facts only where an assertion reads encoded bytes. Repair: a carried-return control; the consumer's errno-key presence, which the blackbox reader already enforces. |
| DT-46/120/121/129 | 22 | R13. Accounts: the trigger is derived from the stop reason at final collection and is not a second observation. Repair: the oracle checks the derivation. Retained: timeout, violation, withheld-release and failed-setup stops keep an `unknown` cause. |
| DT-48/130 | 22 | Accounts: the order rule is an equivalence owed by the producer, with each reader's direction named; label/return coherence is checked only as an eligibility condition. Retained: host admission of allow/deny labels by type. |
| DT-53/132/135 | 41 | Repair: the lifecycle oracle is invoked in the one caller whose lifecycle credit lacked it; the three reader contrasts are retained in the corpus with per-reader expectations; three independence statements are narrowed. Accounts: the failure contract says the consumer does not check lifecycle claims. No reader is added. About 49 default live cases reach the consumer without the oracle. |
| DT-54/58 | 7 | Accounts: the collection-stop list gains the byte-limit stop and the empty-byte fallback is stated, without crediting the three stop reasons that no assertion exercises. |
| DT-55/56 | 13 | R1. |
| DT-59–61/133 | 15 | Accounts: a self-transfer can be consumed in the same visit (owner of the shared extension region); the equipment rule no longer says validation precedes projection. Repair: the consumer relates `ready` to its prerequisites; a CLI control for same-visit consumption. |
| DT-62/65/122/123 | 25 | Accounts: the "reported independently" sentence is withdrawn and the missing carrier is stated as a limit. Repair: the consumer relates held custody to the token's status. Retained: the worker's discarded custody observation. |
| DT-63/64/124/125/128 | 44 | Accounts: the Issue rule is narrowed to the inspected length; last-use clearing is stated as having no reply field and no registered host check; `performed` means the operation ran. Repair: the test comment that credited last-use clearing; one issuer-erase assertion. The `token_oversized` limits row is corrected. |
| DT-66/126 | 14 | Retained unchanged: existing definitions already state that equal native handle values do not establish revocation. |
| DT-67 | 5 | Repair: the suite account is narrowed to two structural assertions and two recorded credits. |
| DT-68/127 | 16 | Accounts: `ownership` gains its time anchor, the last published operation per scope and not an inventory at reply time. |
| DT-69–73/75–80 | 67 | Accounts: only `runner remove` continues a retained cleanup; a report with no row is not service absence; candidate suppression is by label and scope; placeholders mean not inspected. Repair: reconcile's check-read credit is re-scoped. Reconcile stays report-only. |
| DT-74 | 9 | R2. |
| DT-88–94 | 53 | R3. Accounts: seven roots and twenty files, on-disk discovery regardless of Git, a declared superset not derived from compiler use, order and metadata scope, and the pre-sign comparison's limit. Repair: independent-oracle controls with a literal tree and pinned digest. |
| DT-95–104/134 | 85 | Accounts: what label admission establishes, host-written constants, withheld copy versus failed capture, the one reason covering three worker failures, input identity excluding imported files, the assumed-layout limit of the captured bytes, and nonce association. Repair: the selected Rust label test's claims; Swift, C and Python support corrections. |
| DT-105–112 | 58 | R8. Accounts: the fingerprint is not a compatibility test; compaction applies to public JSON only. Repair: presentation mutations in the fingerprint test, an exact normal-fixture comparison, an identifier requirement in the Python actor reader. |
| Both unnumbered investigations | 134 | Both the first synthesis and the follow-up narrowing are kept: source association holds by construction; file association is unobserved; divergence is observed only by selected contrasts; effects, file opens and applied bytes are different claims. One linked limit sentence in the policy and profile surfaces serves both sides, without restricting it to `import` forms. |


### Progress and interruptions

This subsection is the stage's running account; thread results are added as
they land. Seam and cohort detail is in the overhaul plan.

**Seam migration.** Complete in three stages (`b4e6fee1`, `72617789`,
`1cc5f2fa`, `eeb76c1b`). The eight controls are submitted with
`policy-witness test-input run` flags or the client's controls object; an
ordinary request refuses them in its block; the two worker substitutions
remain request keys. Old and new routes compared on 104 scenarios: 103 equal,
one changed route because a NUL cannot be a command-line argument.

**First owner divergence from the frozen guide.** Correcting the limits rows
that named a control as `_test_overrides.<key>` was the first authorized owner
change whose text is copied into the guide. The generator's development check
accepted it; four controls refused it because each copied the checkout into a
constructed release source and presumed the copy was publication-fresh
(`generator_contract` staging and release-baseline controls, the release
entrypoint control, and the repository builder behind the publish and
rotation controls). Under the rule for a guard that blocks an authorized
change, `11e93191` gives each of those fixtures its own regenerated guide
regions through one helper that refuses the checkout as a target, and adds
the refused neighbours: strict staging of a diverged fixture, tagged-source
freshness of a diverged fixture with its own publication permission, and the
checkout's strict check while its owner differs from the frozen guide. Strict
staging and publication checking of the checkout still refuse. `bd8144ea`
then corrects the texts. Four rows whose value a `test-input run` flag changes
(`worker_sentinel_wait`, `validator_io_wait`, `phase_collection_wait`,
`actor_collection_allowance`) are reclassified from "Fixed" to "Flag", each
naming the flag as a test control and stating that `run` has no flag for the
value: the Control column's reading rule defines "Fixed" as no
`policy-witness` flag changing the value, and the rule was left as written.
`428a2049` adds the actor-form refusal row the seam stage lacked; the actor
form refuses a control in its block exactly as the ordinary form does. None
of the three commits changes a build input; the app is unchanged at
`development:081353c9…948ab695`. Guide, distributed copy and both publication
records are byte-unchanged. Runs of record, all without recorded sleep:
`trace-limits-controls-drift-2` (`20261118T143306Z_4ae3e54d`, 11),
`trace-limits-controls-preflight` (`20261118T144405Z_85b74091`, 5),
`trace-limits-text-drift` (`20261118T145136Z_369f241f`, 11),
`trace-limits-text-preflight` (`20261118T150615Z_ec8bcc6a`, 5),
`trace-limits-text-harness` (`20261118T151334Z_29909577`, 15),
`trace-limits-actor-seam` (`20261118T151845Z_d72920c4`, 2) and
`trace-limits-actor-drift` (`20261118T151932Z_85edf143`, 11), all passing.
`make notarize` reaches its build on a diverged constructed source where
`make release` refuses: the Makefile runs the preflight in report mode for
notarization and the signing guide describes that as a rehearsal. Nothing was
changed there; it is listed for the maintainer.

**Environmental interruption, 2026-11-18.** With the lid closed on battery the
machine slept in cycles of about sixteen minutes from about 01:04 to 06:30
local time. The thread then running stopped itself without committing. Its
interrupted run `trace-limits-controls-drift` (`20261118T081036Z_ee6e56a3`,
9 of 11 cases unrun) and a probe run that overlapped sleep are environmental
and are not runs of record; the selections were repeated. No product or test
defect is attributed to the interruption.

**Cohort and conversions.** The worker-wait pilot controls are a pytest family
(`1acf8884`, `95d05b71`) and the four selected conversions are landed with
their follow-up repairs (`4cb2f91b`, `47b455f1`, `9bcefb24`, `79aa7dde`,
`8a7596b5`, `6bab97ee`, `7b8f1f46`). The overhaul plan carries each account.
None changes a build input; the app is still `development:081353c9…948ab695`.
The default selection is 233 cases and now contains the survivor case.

**Evidence cost of pytest families.** The pilot family's case evidence is
about 133 MB where the script's was under 1 MB, because each item keeps its
own copy of the family's collected sources. A read-only investigation at
`147fc10f` also found a cost that no path in this stage reaches: validating
such a family from a release archive reads members of a gzip tar out of
order, which by a sampled projection adds about half an hour per
verification of one archive. At the maintainer's request the direction is a
plan beside the tests, [PYTEST-EVIDENCE-PLAN.md](../tests/PYTEST-EVIDENCE-PLAN.md)
(`ccba056d`): a one-pass archive reader, one blob store per family, and a
question about what per-item source capture establishes. No shared engine or
reader file changed in this stage for it. Until the reader change lands, the
next release whose battery holds these families meets that cost at archive,
publish and each later prune; this belongs in the release account.

**Retention applied, 2026-11-18.** The maintainer asked whether a selective
sweep exists; the retention tool has none by design, and authorized the
uniform one. At `4994bc3b`, with no writer in the checkout, the preview
reported no blocker, nothing unmanaged, four archives kept (`v0.3.4` to
`v0.3.7`), the newest release's acceptance directory protected and 88 runs
eligible (about 51 GiB). `make prune APPLY=1` then removed those 88 with no
failure in about 28 minutes and left no retention journal. Every development
run named earlier in these three plans, including the instrument checkpoint
batteries, the replay comparison and the seam and cohort comparison
directories, is therefore no longer on disk: their identifiers, results and
recorded conclusions stand as written accounts, and repeating a comparison
means rebuilding the commits named beside it. Evidence produced from here on,
ending with final integrated verification, is what the closing outflows rest
on; no further apply is intended in this stage.

**HOST thread, first half (R4, R5).** `feeeaf7b` and `2cc7e32f`, tests first
in each case.

- R4 (DT-23/51). A declared-unapplied actor's phases are classified through
  the same view as the actor, so a failed validator spawn, decode, read or
  association gives the applied actor's outcome and exit 1. The `validator`
  prefix filter is removed and discards nothing: a failed validator pipe or
  query serialization selects `runner_failed` in both modes, as in the
  ordinary form. A placeholder output that was dead code is removed. One text
  changes with unchanged outcome: an unapplied actor with an exhausted budget
  reports "validator not invoked; expected N query results". The independent
  consumer holds the necessary condition for `finished` without reproducing
  the classifier. Before the product edit, on the old app (`host1-r4-pre`,
  `20261118T190137Z_76b60f89`), both unapplied rows of the new five-specimen
  control gave exit 0, `finished` and `ok: true`, and seven new unit rows
  failed; that is the behavior being changed.
- R5 (DT-22/57). An allow or deny record with `step_id: ""` is accepted and
  joins the one empty-identifier step; where no step has that identifier it
  is retained as an unexpected identifier and the run ends
  `validator_unavailable`. Null, absent and non-string values stay structure
  faults, `operation` and `filter_type` stay nonempty, request admission is
  unchanged and the lifecycle adapter rejects only a non-string. Before the
  edit, on the R4 build (`host1-r5-pre`, `20261118T191214Z_63a065d3`), the
  live empty row exited 1 with a decode failure.
- Build contract: `development:081353c9…948ab695` before;
  `development:72ed55e3…dd80afcb` for the intermediate R4-only build;
  `development:378493f6…01542300` in `dist/` and by derivation at `2cc7e32f`.
  The app's `build.commit` reads `77639e82` with a dirty description because
  it was built before the commits; the bytes of the build inputs are those
  committed.
- Runs of record on the final app, none with recorded sleep:
  `host1-post-routed` (`20261118T191732Z_fa224366`, 92 cases, default members
  of the eight routed suites), `host1-post-witness`
  (`20261118T192138Z_34440819`, 52), `host1-post-order-barrier`
  (`20261118T192651Z_5a1cf31d`: baseline accepted, worker and host bypasses
  rejected, no anchor moved), `host1-post-source-drift`
  (`20261118T192820Z_2e017b4a`, 11) and, run by the coordinator afterwards,
  the four `runner_unit` opt-in mutation controls that anchor in files this
  half edited (`host1-post-unit-mutations`, `20261118T194139Z_541f237d`, 4).
  All pass. The remaining opt-in members of those suites
  (`same_shape_contract`, `native_clock`, `native_pause`, `arm_wait`) were
  not run: none concerns the changed behavior.
- Two failures in the pre-change runs were outside the changed behavior and
  are not product defects: an existing checker control placed a spawn failure
  on a `finished` baseline, a premise the consumer's new condition refuses
  (its summary now reads `validator_spawn_failed`, expectations unchanged),
  and a defect in a new check's passing neighbour, fixed before the runs of
  record.
- Corrections to the assessment's reading of source: the placeholder output
  never reached the validator section; the actor specimens use `open_write`
  to obtain an independent file effect.
- No default battery has run on a build containing R4 or R5. It is owed once,
  for the whole product group.

**R14 (DT-01.a, DT-02.a).** `fc4586fc`: contract generation refuses a
declared region that begins inside another, and refuses region markers in a
Markdown document directly under `docs/` that the presentation map does not
name, in both cases before any write. The controls came first: on the
unchanged generator (`r14-pre`, `20261118T212353Z_c410eb27`) the case failed
on exactly the two new mutations, which generation accepted. No generated
file changed, and the guide is byte-identical; its stamp markers do not match
the region pattern. The constructed-map fixture helper now removes contract
regions from documents its map does not name, because the new scan refused
fixtures that copied the checkout's destinations beside a smaller map. Runs
of record, without recorded sleep: `r14-post-drift`
(`20261118T213406Z_0a2e8a68`, 11 pass) and `r14-post-preflight`
(`20261118T212902Z_6bb1c9b7`, the publish and rotation controls, 2 pass). No
build input changed. Owed to the accounts thread: the build account's list of
what the contract check reads, and an authoring rule for removing regions
when a document leaves the map. `preflight/build_refusal_controls`, which
uses the changed helper, has not run since.

**HOST thread, second half (R9, R13, comments).** `cb00a2bd`, `a887c986`
and `c82a1dd6`, tests first, sharing the final build and routed verification;
the R9 and R13 states were each built and ran their own checks.

- R9 (DT-50/131, T3). Validator association, `query_first` eligibility and
  the reported issue keys compare identifiers and query metadata as UTF-8
  bytes, and unexpected identifiers are listed in byte order. A canonically
  equivalent, byte-different record now gives a missing and an unexpected
  identifier, or a query mismatch, then `validator_unavailable` with exit 1.
  Before the edit (`host2-pre`, `20261118T233145Z_7e071f0b`) the host accepted
  every new corpus row while the Rust reader and the consumer refused the four
  byte-different ones; four new ordering rows failed (`host2-pre2`,
  `20261118T233644Z_2d99a5cf`). The worker-slot identity join has a
  child-supplied side: a completed slot's identifier is read back from the
  shared mapping the worker can write. The byte rule was applied to that join
  and its lookups. One reporting lookup in `dispositionIntegrityProblems` was
  left on `String`; by source reading only, it degrades an actor-form reply
  whose slot identifier was respelled. That is unresolved at this commit and
  is the next thing done.
- R13 (DT-121). `schedule_complete`, `ended_before_arrival` and
  `ended_before_completion` map to `completion`; every other scheduler reason
  passes through and keeps an `unknown` cause. `cleanup_trigger` has an open,
  illustrative vocabulary block beside its derivation text. The oracle's
  derivation check landed first and passed on the old app; the actor
  exit-grace row failed there with `schedule_complete` and `unknown` beside a
  complete kill record. Not in the assessment: a cancelled schedule's actors
  are also assigned `schedule_complete`, so the existing gate row's killed
  source now projects `host_exit_grace_exhausted`, and the row asserts it.
- Comments: the five host-thread worklist entries and the two that named
  `_test_overrides.worker_timeout_ms` are corrected, and the unread
  `custodyNames` table is removed. EXEC corrected the remaining three
  gate comments in `pw_probe_runner.c` in `0cbdb557`.
- Build contract: `development:378493f6…01542300` before;
  `development:55116874…` at the R9 state and `development:e89ef618…` at the
  R13 state; `development:185be8ec…27ce76c2` in `dist/` and at `c82a1dd6`.
- Runs of record on the final build, none with recorded sleep:
  `host2-post-routed` (`20261118T234830Z_80585e49`, 91),
  `host2-post-witness` (`20261118T235317Z_5c2f524d`, 51),
  `host2-post-order-barrier` (`20261119T000027Z_e2e3ce6e`, baseline accepted
  and both bypasses rejected, no anchor moved), `host2-post-unit-mutations`
  (`20261119T000154Z_ad6c6327`, 4) and `host2-post-source-drift-3`
  (`20261119T011716Z_6453bb03`, 11). All pass.
- Environmental, not runs of record: `host2-post-source-drift`
  (`20261119T000515Z_6e4fbb5f`) was interrupted on the coordinator's pause
  message with five of eleven cases done, and `host2-post-source-drift-2`
  (`20261119T001618Z_004e7814`) was suspended across about 56 minutes of
  system sleep and then interrupted. The writing session ended on a network
  error during that sleep and was resumed afterwards; nothing unverified was
  committed.
- A frozen-guide divergence to carry to the guide rewrite: the guide still
  calls `cleanup_trigger` a fact recorded where the host acts.

**R9 follow-up and a unit-test defect.** `43c2896d` applies the byte rule to
the reply-step lookup in `dispositionIntegrityProblems`. The control came
first and confirmed the disagreement as read: for a slot identifier respelled
with U+212A the assembler reported `slot_absent` while reporting validation
refused the reply for disagreeing projections (`host2-follow-pre2`,
`20261119T014056Z_fcb10d66`, one new row failing of 641). Left as they are,
with reasons: the identity term beside the changed lookup, now trivially
false; the event lookup in `actorExtensionEvidenceProblem`, which by reading
refuses under either equality; and the request-against-request checks in
`validateForReporting`.

`host2-follow-routed` (`20261119T014519Z_4bc647a7`) failed `unit/rust.unit`
once. The cause is an implementation defect in test code, not the product and
not this change: parallel `runner_select` tests shared one fixture path. It
reproduced on a test binary built before the change in 6 of 600 repetitions
and in none of 600 after `0be7d3df`, which gives each test its own path. That
run stays a failure. CONTROLLER-A corrected four other modules in `91534b47`.
Together with `runner_select`, five controller modules received per-test paths.

Build contract: `development:185be8ec…27ce76c2` before;
`development:38636ec9…` with the follow-up alone; `development:a31e62f3…e9db53c`
in `dist/` and by derivation at `0be7d3df`. Runs of record, each inspecting
the final build and none with recorded sleep: `host2-follow-routed2`
(`20261119T015253Z_30e3bf7d`, 29), `host2-follow-unit-mutations`
(`20261119T015554Z_381c8d50`, 4), `host2-follow-witness`
(`20261119T015824Z_c1c4ab8a`, 52), `host2-follow-order-barrier`
(`20261119T020323Z_5ea3bed5`, 1) and `host2-follow-source-drift`
(`20261119T020435Z_44451a26`, 11). All pass.

**CONTROLLER-A (R2, R6, R7).** `321bb6c5`, `5906c0ac`, `113e1e49`, with
`334fb604` (the DT-26/27 refusal-code accounts) and `91534b47` (fixture
paths), tests first; one final build and verification serve all five, and
each intermediate tree was checked offline in a worktree.

- R2 (DT-74). `load_registry` inspects with `lstat`: only a path with no entry
  is an empty registry. Another inspection failure refuses with "cannot
  inspect runner registry", and an existing entry is read, so a dangling
  symlink, a directory or an unreadable file refuses with the read error.
  `runner list`, `status`, `verify` and `reconcile` exit 2 with that one
  stderr line and empty stdout (executed in four refusing states); a `run`
  with an external runner is a `tool_error` envelope carrying the text, with
  no client started (executed). `validate` and `remove` under an unsearchable
  directory still refuse at the lock, and `validate` on a dangling symlink
  refuses and keeps the link (executed); `install` and `remove` share that
  locked load (source-read). On the old app both new unit tests failed and 11
  of the then 23 integration rows failed: empty lists, `not_found`, and a
  `validate` that replaced the symlink. Five rows added later have no
  pre-change run. No new BYOXPC case was needed: redirected-registry controls
  reach every reading caller without a launchd change.
- R6 (DT-28). `version`, `run`, `test-input run`, the runner commands and
  `sbpl-check` publish through a checked write: an unwritable stdout is exit 2
  with one "failed to write stdout" line, and an unwritable stderr changes
  nothing. On the old app all 18 reader-less-pipe rows exited 101. The
  helper's own `eprintln!` refusals, which the assessment did not list, also
  exited 101 and are converted.
- R7 (DT-34.a). `runner install` refuses an `--env XPC_SERVICE_PATH` value
  that differs from the bundle path before the property list is read, the
  lock taken or anything signed or written. On the old app the same input
  installed, re-signed the copy and wrote a record its own reconcile then
  reported as unowned.
- Fixture paths (`91534b47`): two `run_flow` tests sharing a tag failed 799 of
  2000 repetitions when run alone and none after; two `evidence` tests shared
  a directory 198 of 2000 times and none after.
- Build contract: `development:a31e62f3…e9db53c` before;
  `development:2292d0b2…5ef2a2853` in `dist/` and at `113e1e49`.
- Runs of record, none with recorded sleep: `ctrl-a-post-routed-2`
  (`20261119T052252Z_6c91b808`, 6), `ctrl-a-post-byoxpc`
  (`20261119T052803Z_93b4d96e`, 3: install, registry recovery, default
  location) and `ctrl-a-post-source-drift-2` (`20261119T054624Z_0753d376`,
  11). External-runner state was empty before and after.
  `ctrl-a-post-source-drift` (`20261119T052847Z_53c6e9b7`) failed
  `generator_contract` on an implementation defect in this thread's own
  account edit, a symbol named beside a file link; it stays a failure and was
  fixed. Reviewed exception: two accounts changed after the routed and BYOXPC
  runs; those cases read neither, and the tree's contract equals the app's.
- Corrections to the assessment: its third `conflicting_selector` case needs a
  service in the file or the root-path refusal comes first; "naming the path
  and the system error" does not hold for schema and parse refusals and is
  scoped accordingly.
- Left for the accounts thread: DT-28.c/e, DT-34.b/c/d, DT-69/78/79, the
  installation surface's checks list and the read rule's entry list.

**CONTROLLER-B (R10, R11, selected test corrections).** `1bba0e37`,
`b3c89046`, with `8ef29ae1` and `560a5a35` (tests) and `6d2d8ebd`
(statements); one rebuild and one routed run, each intermediate tree with its
own unit run and generator checks.

- R10 (DT-42/117). For a request whose `actors` member is an array,
  `data.policy_check` is present and null; `actor_policy_checks` is
  unchanged. With the new assertions on the unchanged product
  (`ctrl-b-r10-pre`, `20261119T062742Z_c4555ecb`) exactly the three actor-form
  tests failed. A by-hand probe on the shipped binaries, with the host killed
  during an actor exec action, gave a `tool_error` helper result ("missing
  field `policy`") before and null after, with the actor's own capture `ok`
  both times; its envelopes are scratch only.
- R11 (DT-113/116). The fallback calls on the admitted-reply branch are
  deleted. A control over every combination of the four members that
  eligibility and the failure classification read shows that all ten
  fallback-eligible results are refused by reply admission, with and without
  a reply; it passed before and after the deletion.
- Tests. The two actor fallback tests now establish input membership from
  independently authored policy objects, per-actor attribution and request
  order from the envelope, and one separate invocation assertion; they no
  longer fix a call count or order. A new ordinary-form control replaces the
  request file inside the client callback and requires the helper's input to
  equal the client's byte for byte, rejecting a reread file and a
  re-serialized request. The test callbacks are not the shipped client or
  helper, and the accounts say so; `runner_byoxpc/reservation_controls` now
  asserts the ordinary fallback capture through the shipped controller and
  client. The label test is renamed
  `compiled_profile_status_and_labels_alone_decide_run_admission` and asserts
  which boundary refused each row; the DT-104.b assertion requires exit 1 and
  the diagnostics key present with JSON null.
- Statements corrected in their owners: `result.error` precedence, the
  reply-less row, the foreign-producer refusal, the fallback rule and the
  sentence that a fallback capture never shares an envelope with a host
  reply. "Does not depend on host admission" is corrected in the limits
  manifest and the architecture account; the guide's copy is unchanged.
- Build contract: `development:2292d0b2…5ef2a2853` before;
  `development:64f2293e…6e76b62` in `dist/` and at `6d2d8ebd`.
- Runs of record, none with recorded sleep: `ctrl-b-post-routed`
  (`20261119T063147Z_6fcb0d5f`, 20), `ctrl-b-post-reservation`
  (`20261119T063248Z_5102edcb`, 1) and `ctrl-b-post-source-drift`
  (`20261119T063511Z_f3fc7395`, 11). External-runner state was empty before
  and after. No failure beyond the designed pre-change one.
- Corrections to the assessment: a `finished` reply without the worker
  subprocess record is withheld, so the no-worker sentence gained "unless an
  integrity finding withholds it"; the parser retains rejected bytes on the
  delivery-failed row, and both rows now model that.
- CONTROLLER-B left the optional DT-44.m and zero-length session controls outside its selection.
  Left for the accounts thread: DT-116.g, the helper-envelope row, the
  oversize limits row, `tool_exit_code` and `stderr`, eligibility and
  `actor_id` limits, transport limits, DT-119.a and four smaller entries.

**CONTROLLER-C (R12).** `227e5fc2` (producer, readers, shape goldens,
checks and statements together) and `b5a941e7` (evidence scope), tests first.

- The `sbpl-check` envelope's `import_inventory` gains a required boolean,
  `unfollowed_imports`; it therefore also appears in the helper envelopes a
  fallback run carries. The dossier gains no field.
- The scanner is now a token scan. It follows an opener, `import`, one
  nonempty string using only the two escapes and the matching closer, with
  whitespace or comments between; every other list headed by `import` is
  reported as unfollowed and scanned inside. Stated limit: a renamed or
  applied `import`, `eval` and `load` produce no such list and are not
  reported, and the followed set is established for one system version.
- A scanned file that holds an unfollowed form gets a record error with its
  hash kept, so a record error no longer means the file was not read; every
  record with a path and a hash contributes a line to the closure.
- The six contrasts are distinguished through the standalone helper
  (`integration`) and through the run dossier with the worker's compiler as
  witness. On the old app (`controller-c-pre`, `20261119T065915Z_40ed32a2`)
  both cases failed as expected: the member was absent in all 47 helper rows,
  a comment between head and string gave no record, and a computed argument
  was reported `complete` in one spelling.
- Found beyond the assessment: square brackets are list delimiters for the
  system reader, so a bracketed import is evaluated and is followed; `#!` at a
  token start is a line comment; a quote inside a symbol desynchronized the
  old scan; a lambda whose parameter list is headed by `import` is now
  flagged, a false alarm the limit statement covers.
- Build contract: `development:64f2293e…6e76b62` before;
  `development:81fac005…3bd09ccb` in `dist/` and at `b5a941e7`.
- Runs of record, none with recorded sleep: `controller-c-post2-routed`
  (`20261119T072343Z_4273eb3d`, 21), `controller-c-post2-source-drift`
  (`20261119T072444Z_c5cd7475`, 11) and, run by the coordinator because the
  consumer now requires the member on a real fallback envelope,
  `controller-c-post-reservation` (`20261119T073749Z_8eade5c0`, 1), with
  external-runner state empty before and after. All pass.
- `controller-c-post-source-drift` (`20261119T071144Z_50e0bfdb`) failed two
  cases and stays a failure: the drift suite's Rust literal reader cannot
  tokenize a quote written as an escaped character literal. The thread
  respelled its own literal and left the reader alone; the reader's limit is
  a defect in test code, listed for the accounts thread. Reviewed exception:
  the drift run of record is on `b5a941e7`'s tree; `227e5fc2`'s own tree
  passed the four generator checks only.
- The guide now lacks: the member in its helper list; that an empty record
  list can accompany unfollowed forms; that a record error can accompany a
  hash.

### EXEC — child output through the signed candidate, 2026-11-19

`0cbdb557` implements R1 (DT-55/56). The worker counts bytes read and
stored on each pipe. The host appends the truncation marker and uses the
stored lookahead to distinguish a cut through a complete scalar from
malformed UTF-8 at the same position. The retained text includes embedded
NULs. The four new count and flag fields are required on each stream.

- `exec-pre` (`20261119T074936Z_68a6776e`) completed 20 cases on the
  previous app. Seven failed at the old behavior and 13 passed.
- `exec-post-routed` (`20261119T145345Z_16015319`) completed all 57 cases,
  with 56 passes and one informational completion. It covers the signed
  command outputs, native publication, reader controls and reply sizes.
  `exec-post-source-drift` (`20261119T150002Z_671662fb`) passed ten of
  eleven cases. The direct-Python check found that the new script launcher
  used the inline-only `-P` option. After removing it, `exec-post-launcher`
  (`20261119T153327Z_10450791`) reran the direct-Python check and all 20 signed worker cases.
  All 21 passed. All three post-change runs recorded zero system sleep.
- On the signed candidate, 256 steps returning malformed UTF-8 used
  4,090,407 of 96,468,992 host reply bytes and 4,091,069 of 285,212,672
  client reply bytes. The ASCII control used 3,042,855 and 3,043,517.
  These are measured replies for the specified workloads.
- The public build contract moved from `development:81fac005…3bd09ccb`
  to `development:9b0db1c3…3ceea1d8`. Worker identity moved from
  `14d41d54…9c5c0ef5` to `217ad94a…a442252b` and the schema fingerprint from
  `80013e5b…a064e224` to `520ca3be…0d3a180`. The first build exposed a reference
  to a host-only layout type in shared validation. The packaged client now
  checks the public retained-byte bound and the signed rebuild completed.

### WIRE — conditional reply fields and schema validation, 2026-11-19

`7b2b030b` implements R8. Before the change, `wire-pre`
(`20261119T153551Z_e929cf95`) completed both selected cases. The Rust
reader accepted a native return without its result source, the Python
reader dropped a carried dependent, and the generator accepted all five
malformed schema fixtures. The guarded and disjoint fixtures passed.

The readers now refuse a carried dependent whose guard is absent. With
the guard present, an absent dependent still projects as null. The
generator rejects overlapping path/presence rules, chained guards,
case types that overlap in JSON, and unknown case keys. All three
conditional records gained a Rust admission check. The shipped schema,
Swift writer, wire fingerprint and worker identity are unchanged.

`wire-post` (`20261119T153807Z_d5bc2204`) passed all 41 selected cases with no system sleep or change to the tested app. The signed app's build contract is
`development:cc96e8ec…ba2b7a06`, following EXEC's
`development:9b0db1c3…3ceea1d8`. The controls cover constructed frames,
generated copies and the signed CLI. They exercise the malformed-reply
route independently of the Swift writer.

### IDENT — development and worker identity derivation, 2026-11-19

`a4d49249` implements R3. Source discovery lists each directory and inspects
each entry beneath the declared roots. It names the path when listing or
inspection fails, including an empty unlistable directory. The inputs
statement now names seven roots, twenty explicit files and the suffixes.
It explains on-disk discovery and which two observations the pre-sign check
compares. The build account includes the new propagated refusal.

- `ident-pre` (`20261119T160501Z_78ce88f1`) completed both cases. The old
  selector omitted unreadable subtrees or gave the wrong reason for refusal.
  Both build fixtures continued to the signing-identity check. The statement
  omitted `controller/interface` and `docs/publication.py`. The readable
  control agreed with the independently pinned digest.
- `ident-post` (`20261119T161611Z_db3c56bd`) completed 98 cases
  with 96 passes and two failures, zero system sleep and an intact app.
  All 24 cases in the thread brief and its native-source route passed.
  Selecting the whole `runner_c_worker_harness` suite also selected its two
  opt-in wait experiments, which the brief did not name.
  Neither failure is a product regression, and both were predictable before
  the run. `native_pause` is a qualification gate that keeps a failure by
  design. It ran twelve children under the two deny-default profiles: bare
  version 2, and the original version 2 with file-read-data. In each, the
  first post-apply 1 ms `nanosleep` returned -1 with errno 22, and the
  supplemental log holds a PID-matched `deny(1) syscall-unix 334` event. The
  allow-default and unapplied children completed their pauses. The
  November 7 qualification, recorded at `7a5f8e80` before R3 existed,
  refused on the same returns, and the production waits were retained then.
  This is a valid unfavorable observation, not an apparatus or environmental
  fault. `arm_wait` refused before building anything, because its suite
  account requires a fresh `PW_ARM_WAIT_GATE` from a coordinator. That is a
  test-selection refusal, and the case recorded no observation. The run
  stays a failure and qualifies neither primitive. The controls exercise
  real directory permissions and the
  build script, Swift context generator and development guide staging in
  disposable source copies. The statement-derived inventory and the literal
  framing check independently exercise the digest.
- The signed candidate's public identity changed from `development:cc96e8ece83a2c1353da049b4dca4036f2077e264c7e4f6d621db622ba2b7a06`
  to `development:0c8497126cab848b4faf781d891010a06f7510dea903d6bea546afb7d09b18b1`. The worker identity changed from
  `217ad94adda003919638e5e7406a2fdb650d9ad17e839f64e87e9d64a442252b` to `3632de9cdadf7dd04e12e29db86dff1b80a30e96a07dff0815bbff8d9df412db`. All three generated copies
  and the built worker agreed at signing. The build account, diagrams and
  public contract were regenerated, and the build checked all eight owners.

### November 18 pause and resumption

Work stopped at a quiet point at the maintainer's request, resumed the same
day for three bounded pieces (R14, the second half of HOST and one R9
follow-up) and stopped again with all three landed. State at this second
stop: `main` at the commit that last changed this note, tree clean, nothing
pushed, no extra worktree, no writer in the checkout. The signed app in
`dist/` is `development:a31e62f3…e9db53c`, equal to the derivation at
`0be7d3df`; it was built before the last commits, so its commit stamp is
older than its contract. `tests/out/runs` holds only this stage's `host1-*`,
`host2-*` and `r14-*` directories. The guide, its copies and both publication
records are byte-unchanged at the freeze. No release was made.

Resumed on 2026-11-18 at 20:34 local from `1fa886c7`, on the maintainer's
instruction to carry the product threads through the grouped default
battery, its reread and a prune preview, and then stop. The
completed product threads and the evidence for that stop are recorded in the
[November 19 checkpoint](#product-group-checkpoint). The earlier pause
preceded the controller threads, EXEC, WIRE and IDENT.

Some working material for the later stages is gitignored scratch under
`.tmp/trace-integration/`. It includes the common and per-thread briefs, the
rulings, the candidate-battery brief and the two outflow drafts. The user-duty
draft dates from November 17 at `837296af`. The maintainer-judgment draft
runs through CONTROLLER-C and has no entries yet for EXEC, WIRE, IDENT or the
product-group checkpoint. The assessments, the disposition record, the
accounts worklist and its addenda are tracked under
[trace-assessments/](trace-assessments/README.md). If the scratch is lost,
those files and the rulings table in "Selected remedies" above are enough to
rewrite the briefs. [PYTEST-EVIDENCE-PLAN.md](../tests/PYTEST-EVIDENCE-PLAN.md)
is later work and is not part of the remaining order.

## Product-group checkpoint

On November 19 the maintainer moved the pause forward to the grouped default battery. The product and
tooling remedies R1–R14 are on `a4d49249`.
The outcome-reporting changes, the two pytest cohorts, the experimental
control migration and the case conversions with their follow-ups preceded
this group. All four acceptance comparisons are recorded. The final two,
fallback and validator association, are in `8ca3e6db`.

The grouped default battery, `product-group-default`
(`20261119T171109Z_bdd0820d`), returned successfully after 44 minutes 48 seconds.
All 242 selected cases completed. The dispatcher recorded 241 passes and one
informational completion, `runner_exec_lifecycle/closed_streams_leader_exit`.
It recorded zero skipped or unrun cases, zero harness errors and zero system
sleep. The signed app passed its initial integrity check and its final inventory
matched the initial inventory.

The independent validator reread and the read-only prune preview ran on
November 19 at `44bc10de`, with no writer in the checkout.

- **Reread.** `reread.py` passed the saved selection's `execution_contract`
  and the run directory to the revised `release_accept.battery_problems`. It
  ran in about three seconds and found no problem:
  - all 242 cases completed, with 241 passes;
  - the survivor's one completion was admitted under its independently
    selected outcome contract;
  - family evidence was read for 9, 66 and 232 items;
  - recorded sleep was zero, and the app was valid before the battery and
    unchanged after.

  `run.json` (SHA-256 `cf04d858…5115a03`) and `independent-selection.json`
  (`89b6c3df…2baf86d`) hashed the same before and after. The reread
  interprets retained evidence. It credits no case and does not re-examine
  the app.
- **Prune preview.** `make prune` without `APPLY` exited 0 after 2 minutes
  39 seconds.
  - It kept archives `v0.3.4`–`v0.3.7` and protected
    `tests/out/release-acceptance/run-9e17e41c6b99440c8359cf2163b7cfa1`.
  - It listed all 61 development runs as eligible, `product-group-default`
    among them.
  - It reported no blocker, unmanaged path, missing acceptance or pending
    journal, and removed nothing.

  An apply would delete this checkpoint's evidence, and none is intended in
  this stage.

The receipts, `reread.json` and `prune-preview.json`, are local gitignored
files beside `reread.py` in `.tmp/trace-integration/product-checkpoint/`.
The product checkpoint is complete.

**Selective removal, 2026-11-19.** After the preview, the maintainer removed
41 of the 61 development runs, about 20 GiB, with `/bin/rm -rf` run under
`tests/lib/checkout_lock.sh`. Each removed run fell into one of three groups:

- it was never a run of record;
- it was a failure followed by a recorded passing rerun;
- every one of its cases ran again on the final tree and app in
  `product-group-default` or `ident-post`.

Twenty runs remain:

- `product-group-default` and `ident-post`;
- the twelve pre-change runs;
- six opt-in runs that no later build repeated: three order-barrier runs, the
  BYOXPC install and recovery run, and two reservation runs.

Where these plans name a removed run, the name now stands only as a written
account. The removed runs' closed pytest owner records stay until the next
`make prune APPLY=1` retires them.

Before and after the battery, the external runner registry and its
pending-cleanup list were empty. Reconciliation found no records,
unregistered candidates or inspection errors.

The signed development app in `dist/` has the same selected-source identity
as `a4d49249`. Its embedded Git description is
`v0.3.7-253-ga02fb459-dirty` because the prescribed signed build preceded
the implementation commit. Both publication records bind that candidate
and withhold publication. The repository and distribution guide match
`3d3f8e65` byte for byte. The run names in this handoff are local gitignored
evidence beneath `tests/out/runs/`. The independent selection and runner inventories are local gitignored
files beneath `.tmp/trace-integration/product-checkpoint/`.

### Remaining checkpoint and later work

1. Done: the product checkpoint's reread and prune preview are recorded
   above.
2. Complete the three technical-account passes in order, working from
   [ACCOUNTS-WORKLIST.md](trace-assessments/ACCOUNTS-WORKLIST.md) and
   [ACCOUNTS-ADDENDA.md](trace-assessments/ACCOUNTS-ADDENDA.md).
   [TRACE-ACCOUNTS-PLAN.md](TRACE-ACCOUNTS-PLAN.md) carries out this step.
   It adds read-only reader probes and ends at a prune apply.
   - Part 1 covers contract statements, presentation and generators.
   - Part 2 covers failure evidence, limits and their supporting
     documentation.
   - Part 3 covers assertions and the tests credited for those statements.

   Check each worklist entry against current text before editing, since a
   product thread may already have made it. The addenda add the entries
   found later, including R14's two remaining corrections. They also settle
   the worklist sections that no pass owns:
   - All the comments in build inputs have landed.
   - The records entries are done.
   - Each outside-the-review note is assigned to Part 1 or to the
     maintainer-judgment outflow.

   R8 and R14 implementation and their generator controls are complete.
3. Adapt the nested build-refusal battery to a development candidate, as
   [final integrated verification](#three-boundaries-for-broad-runs) requires.
   At HEAD, `control_release_battery` in
   `tests/suites/preflight/opt_in/build_refusals.py` still renders release
   outputs and tags a synthetic release, which this plan forbids. The
   prepared design is the scratch `BRIEF-CANDIDATE-BATTERY.md` of November 17,
   written before the conversions and the product threads. Its "Publication
   boundary" pointer now means "Development and publication checks". The
   design replaces `release_battery` with two separately credited sequences:
   - `candidate_battery` makes a normal development build of a snapshot
     commit on the imported release tags, with no release rendering. It runs
     `release_accept.accept` in `development-candidate` mode with no Apple
     stand-ins, and its command boundary fails on `stapler`, `spctl` or
     `notarytool`.
   - `candidate_publication_refusal` runs no battery. Strict acceptance, the
     release preflight on a tagged copy and publication freshness must each
     refuse before any dispatcher or build tool runs.

   The full case runs only once, in step 4.
4. Run final integrated verification with offline and drift controls, a
   clean-stamped signed build and a default battery with the relevant opt-ins.
   Run `preflight/build_refusal_controls` once. Record the extracted candidate's
   actual execution separately from the strict release-preflight and
   release-acceptance refusals for that candidate.
5. Complete the release account, user-responsibility report and
   maintainer-judgment report against that evidence. Start from the two
   scratch drafts named above. Include the coordinator notes the addenda
   assign to the maintainer-judgment outflow and the maintainer items these
   plans record:
   - the `make notarize` report-mode preflight;
   - the pytest-family archive-read cost;
   - the frozen-guide divergences.

   Cleanup of disposable scratch belongs to this later closeout.

## Technical-account passes

[TRACE-ACCOUNTS-PLAN.md](TRACE-ACCOUNTS-PLAN.md) governs this step.
[ACCOUNTS-LEDGER.md](trace-assessments/ACCOUNTS-LEDGER.md) gives each
entry's status.

**Pass 1, 2026-11-19.** Writer W1 settled all 141 worklist entries and the
six Part 1 addenda items in commits `4e7545e9`–`b54a16ba`:

- 110 applied;
- 36 already made by the product threads;
- 1 optional entry not taken, because `DISPOSITIONS.md` selects Pass 3's
  ordinal assertions for DT-38.d.

No entry was contradicted, touched a build input or needed a product change.
In five places, source contradicted the worklist's proposed wording, and the
writer stated the code's behavior instead. Each is recorded in its ledger row.

Reviewer V1 read the diff against source without the writer's report. It
found six statements broader or narrower than their code. One said that a
wait which loses its clock keeps sleeping; in fact, the actor schedule
treats a lost clock as no time left and ends. The coordinator confirmed the
two weightiest findings in source before the writer verified each.
`1638c854` corrects all six. V1's two suspected findings were settled
against source with no edit.

The guide is unchanged, and the development identity is still
`development:0c849712…b18b1`. Runs of record, with no recorded sleep:

- `accounts-p1-drift-review` (`20261120T000019Z_3a581b50`): `source_drift`
  11/11 at `1638c854`.
- `accounts-p1-build-entry` (`20261119T233833Z_076a4f38`):
  `preflight/build_entry_controls` at `b54a16ba`. This is a reviewed
  exception. `1638c854` changes only contract surfaces and their generated
  views. That case's early refusals fire before generation and read none of
  them.

`accounts-p1-drift` and `accounts-p1-drift-final` passed on trees that later
commits superseded, so neither is a run of record. Pass 1 left four owner
texts for Pass 3 to revisit when its test repairs land. They are listed in
the ledger's notes and in the Pass 3 brief.

**Pass 2, 2026-11-20.** Writer W2 settled all 57 worklist entries and both
Part 2 addenda items in commits `2a8a270c`–`a6c2f1a5`. The rows are numbered
142–198 in the ledger.

In eight places, source contradicted the worklist's proposed wording, and the
writer stated the code's behavior instead. No entry touched a build input or
needed a product change.

Reviewer V2 found six statements broader or narrower than their code or
tests:

- B9 left out where actor-form fallback captures are nested;
- one exact boundary was called source-inspected when a unit test covers it;
- `read_error` can accompany the stop `eof`;
- `native_rc` follows the record's own outcome, not the step's;
- a receipt fixture's fields and a lifecycle row's encoded bytes are checked,
  narrowly;
- a removal credit implied that an untested retry after teardown expiry was
  tested.

The coordinator confirmed two of the findings in source before the writer
checked each one. `d172c70e` corrects all six. It also corrects row 190, the
`runner_unit` README's path-diagnostics account. That entry is optional in
`DISPOSITIONS.md`, but its statement was false.

Counts after the review:

- 45 applied;
- 12 already done;
- 1 not applicable;
- 1 optional entry not taken.

Pass 2 left two stale comments in build inputs, in `CWorker.swift` and
`PWRunnerAPI.swift`. They are listed in the ledger for the commit before step
4's build.

The development identity and the guide are unchanged. Runs of record at
`d172c70e`, with no recorded sleep:

- `accounts-p2-drift-review` (`20261120T012305Z_2cd61980`): `source_drift`
  11/11;
- `accounts-p2-unit-review` (`20261120T014109Z_4fb42415`): `unit` and
  `integration`, 5/5.

The earlier runs `accounts-p2-drift` and `accounts-p2-unit` are superseded.

**Reader probes, 2026-11-20.** The answer keys and inputs were committed in
`2bcdfeb8` before any probe ran. Four workflows then ran, each with
read-only `Explore` readers, which do not receive `CLAUDE.md`. Twenty readers
ran in all: Sonnet readers plus an Opus control on the same material in P1,
P2 and P4. Every reader reported staying within its inputs. Records are under
`trace-assessments/probes/` and were committed in `479b43b8`.

- **P1, envelope interpretation.** On ten live envelopes, all four readers
  kept every targeted limit: sandbox cause, `query_first`, agreement,
  fallback meaning, receipts, requested controls, and `cleanup_trigger`.
- **P2, spec-only oracle.** Every reader, the control included, raised three
  gaps where the contract text does not decide an outcome the code
  determines.
- **P3, restatement comparison.** Three rules are consistent across their
  owners. A fourth, the `captured` receipt, has a single owner.
- **P4, test-only reading.** One test's name and comment claim more than its
  corpus shows.

Accepted leads:

- **Four Pass 4 account entries:**
  - the `test_overrides` echo limit, in `30-reply`;
  - when `query_mismatch` is emitted, in `32-lifecycle`;
  - square-bracket lists in the import scan, in `11-policy`;
  - no runner client starting on a registry refusal in `run`, in
    `50-installation`.
- **One test repair in a build input,** the label-admission test in
  `run_flow.rs`, held for the commit before step 4's build.

No lead created or supported a user duty.

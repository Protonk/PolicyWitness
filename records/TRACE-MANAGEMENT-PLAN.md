# Trace review management plan

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

Address the coupling in `build.sh`, `docs/generate_limits.py` and
`docs/contract/runtime.py`: builds check generated copies and stage the guide;
current limits/shared content and contract stamps propagate into it. Default
`source_drift` cases repeat the comparison of the guide with its live owners.
`docs/build_contract.py` distinguishes development and release identities but
does not itself establish publication freshness: a clean annotated tag alone
yields `release:<tag>`.

Before the checkpoint baseline, implement the required development/build support:

- Preserve frozen guide bytes while checking current machine definitions,
  technical projections, owner regions, interface inventory and build identities
  against the development product. Check the guide's region copies, limit spans
  and stamp table against their `3d3f8e65` bytes, and each owner against its
  current definition. Do not hand-edit generated copies or maintain a second
  normative explanation.
- Record publication withheld in development artifacts and verification receipts.
  Do not stage the frozen guide as a freshly verified current manual. Use the
  existing generation/build owners and a bounded revision/region distinction.
- Reject accidental drift, changed frozen bytes, stale technical outputs, wrong
  identities and missing or inconsistent boundary evidence. If a free-text or
  prose guard blocks an authorized change, revise that specific development rule
  with positive and negative controls; do not disable the guard generally.
- Strict publication freshness is enforced today only by `make release`'s
  preflight in `tests/lib/release_preflight.py`. Acceptance, archive and
  publication check identity, tag and hashes but run no freshness check. Extend
  strict freshness so no route from a tagged commit to an accepted, archived or
  published release omits it. Refusal rests on freshness established from source
  at the tagged commit, never on a recorded identity or the absence of a
  publication-withheld record, so a tagged or relabeled development candidate
  is refused. Preserve signing, source/app agreement, provenance, cleanup and
  historical archive rules.

Reporting-reader support lands in the overhaul's capability stage. Land routed
controls exercising intentional divergence beside the listed faults with this
support, before the first divergent change.

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

All `.tmp` material above is gitignored local development evidence with no
retention guarantee. Availability was checked, not its complete provenance or
hash correspondence. No present directory is adopted as release evidence, and
no original report is rewritten. The app used by those investigations was the
`8b5de2b2` build described there; the checkpoint must identify its own candidate.

### Finding coverage map

This map allocates every DT identifier for subsequent disposition. A row is a
reading/decision boundary, not a claim that its entries have one defect or one
remedy. Compound subfindings and each entry's qualifications remain separate
obligations at their original anchors. Except for the bounded decisions below,
product dispositions are pending; the instrument checkpoint does not close them.

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
| DT-37–41 | Each smaller statement/source difference, support scope, prose account, index spelling and tour commitment list remains individually pending at its original subfinding. |
| DT-44 | Thirteen unverified leads remain explicit below; confirmed statement existence does not verify the reported producer. |
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
remain unverified leads at this preparation boundary. In particular, the EOF
lead still needs its closing-stdout/held-stdin fixture if reachability affects
the disposition; absence of that execution is not a failure of the checkpoint.

### Bounded shared assessments for capability design

**Descendant lifetime (no DT identifier).** Retain the named
`leader_exit_and_eof`/`not_requested` relation as a truthful-evidence commitment.
Source inspection of `pw_worker_exec.h` shows the group signal is attempted only
after deadline, observation error or local fault; the lifecycle surface,
`porcelain_native.rs`, `PWRunnerAttemptEvidence.swift` and `consumer.py` check
the relation. The existing survivor checker additionally requires a live child
with its original generation/group and ping, before interpreting JSON. That
survival requirement may be withdrawn without withdrawing the truthful account
of the product's calls. The future informational observation must classify
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
which imported bytes the compiler read. The scanner defects, dropped helper
signal and private capture-view limit remain separate pending product decisions.
No new compiler-file observer or authenticity claim is introduced by reporting.

**Reader and erasure claims.** The reporting foundation must allow a checker
to fail an enforced truth/validity obligation while carrying an unfavorable
advisory comparison. It must not silently promote `consumer.validate` to the
lifecycle oracle, or final `erased` flags to last-use observation. The selected
assertion/account repairs remain after the checkpoint, with their existing
independent reader/byte-observer contrasts. No additional observer is justified
merely to make the reporting layer uniform.

The acceptance rehearsals identify implementation/account dependencies without
selecting their hypothetical product changes. Therefore actor fallback removal,
capture after failed application and byte-exact Swift association remain pending
product decisions. Their shared accounts have not been changed during preparation.

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

### Cost, retained state and next work

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

Work stops here. The selected product/test remedies, both pytest cohort migrations
and executable seam migration remain pending. The prepared source maps and shared
rehearsals identify their owners but establish no execution equivalence. Each
cohort must compare its original and migrated paths; the seam still needs its old
experiment captured before entry-point changes. Retain the named truthful
`leader_exit_and_eof`/`not_requested` relation for the survivor conversion. Other
product dispositions remain as allocated above. Reporting now supplies the required
authority, phase/input and supervised-command support. The later integrated stage
still owns the adapted live extracted-candidate/build-refusal control and signed-app
verification after product/build-input changes. No additional broad verification
is required merely to expand this pause report.

## Integrated implementation — 2026-11-17

Status: in progress. This section records the stage after the instrument
checkpoint: dispositions for every claim, the selected remedies, the two
cohort migrations, the seam migration, final integrated verification and the
outflows. Entries below are added as work lands; a subsection that says
"pending" has no credited result.

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
retention with the limit stated in the named owner.

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

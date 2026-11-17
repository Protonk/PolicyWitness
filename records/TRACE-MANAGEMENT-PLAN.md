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

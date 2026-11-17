# Test outcome overhaul plan

## Scope and sequence

Implement reporting/enforcement distinctions, the selected conversions and trace
corrections, both pytest cohorts and the executable seam migration below.
[TRACE-MANAGEMENT-PLAN.md](TRACE-MANAGEMENT-PLAN.md) owns product dispositions,
authority, the guide freeze, development/publication checks, broad-run sequencing
and outflows. [TRACE-ACCEPTANCE-PLAN.md](TRACE-ACCEPTANCE-PLAN.md) supplies the shared
change rehearsals and maintenance assessment.

Prepare cohort and seam baselines and assess remaining survivor obligations
before capability implementation. Supply all required receipt, pure-item, command
and candidate-evidence support in that stage. Complete management's unchanged-app
checkpoint before conversions, cohort migration or seam executable changes.
Those may then proceed together where independent; preserve separate baselines
when callers overlap. Finish all selected work before final integrated verification.

Machinery/cohort observations use source inspection at `9714e451`; seam/dependency
observations use `3d3f8e65`, not executed equivalence evidence. The
[test-work survey](tests/TEST-WORK-SURVEY-REPORT.md), at `31b81951`, supplies assertion
and reporting leads; it ran no cases and is not a current inventory. Recheck
changed call paths before editing, and verify availability of local trace evidence.

## Prepare the two pytest cohorts

| Cohort | Full migration scope |
| --- | --- |
| `witness_contract/worker_wait_pilot_controls` | All scenarios in [worker_wait_pilot_controls.py](../tests/suites/witness_contract/worker_wait_pilot_controls.py): ordinary/actor/neighbor receipts, decoding and interval arithmetic, historical missing records, grace/scan analysis, faulty formulas, exclusions/pooling, comparisons, disk/Markdown round trips and stager identity controls. |
| `source_drift/markdown_reader` | The complete [markdown.py](../tests/suites/source_drift/markdown.py) population: block/comment/link/heading/table/line interpretation, vendor bytes/import rules and fresh-process guards. Baseline: eight test classes, 38 methods and subcases. |

The first exercises outcome distinctions; the second tests fixture isolation,
parameterized diagnostics and cleanup beyond outcome work. Keep live exec,
BYOXPC and pilot drivers in their existing runners. No other population is part
of this migration. If evidence overturns a cohort's suitability, document the
lost coverage or orchestration problem and explicitly reconsider it; do not
substitute a token test. Completing both ends the mandate.

Before migration, map old scenarios to observations, independent expectations,
accepted/rejected variants, setup/cleanup failures, inputs, commands, receipts
and literal descriptions. Preserve scenario identities and required ordering,
not function counts. Keep hand-authored arithmetic and rejection oracles
independent of the tested reader; reader correctness stays enforced when its
product comparison is advisory.

The stager runs `ditto` and a stand-in worker's `--version` before signing;
the Markdown cohort runs Git and fresh Python processes. Preserve those commands
and controlled environments rather than replacing them with mocks. Neither
cohort needs app admission, native compilation or signing merely to use pytest.

## Establish reporting and enforcement capability

### Outcome meanings

Choose representation and file formats during the bounded mechanism comparison;
retain these distinctions:

| Arrangement | Judgment and acceptance |
| --- | --- |
| Enforced | Evaluate a stated proposition; an unfavorable result blocks acceptance within its authorized scope. |
| Advisory | Evaluate and report an expectation; an unfavorable result does not itself block acceptance. |
| Informational | Record behavior without an expected product value; completion contributes no passing product assertion. |

State each experiment's promised observations. Required prerequisites, identity,
commands, accounting, evidence validity, artifact integrity and resource settlement
remain consequential in all arrangements. Unknown ownership is not absence;
optional unavailable measurements supply no conclusion. Malformed product output
can be valid failure evidence; a truncated harness receipt can invalidate the
observation. A deliberately malformed rejection-control input is not broken
apparatus.

Choose authority before evaluating the result. Bind it through selection or
collected family evidence so deleting/relabeling a judgment cannot make a run
acceptable. Separate product judgments from validity and cleanup checks within
mixed cases. Informational work must not be implemented as skip, `xfail` or an
ignored assertion. Untouched cases keep their enforcement.

A dependent requires its predecessor's valid completion and satisfied enforced
judgments, not a favorable non-gating result. An invalid, incomplete or
unsettled predecessor blocks it, as an enforced failure does now. An unfavorable
advisory judgment or a completed informational observation does not. The gate
is inline in `suite_run.execute` and admits only `pass`; verify the revised
rule through dispatcher fixture runs.

Advisory evidence uses ordinary engineering judgment: it may justify investigation,
a product change, new enforcement or no action. Add no advisory-specific escalation
process. Independent obligations remain enforceable, including when advisory
evidence reveals their violation. Later decisions do not rewrite the original
run's authority or semantics.

### Mechanism and owning boundaries

Compare two arrangements on one enforced judgment, one unfavorable advisory,
one informational completion and one broken observation: extend terminal reports,
or attach a required observation/judgment account to engine phases. Exercise
missing records, contradictions, cleanup failure and release rereading before
choosing. An attached account must participate in acceptance and terminal output.
Record the choice and material tradeoff here. Reuse existing registries, receipts
and ownership machinery; no universal cross-language result protocol is required.

| Owner | Required work |
| --- | --- |
| `test_cli.py`, catalog, `testlib.sh`, `case.sh`, `suite_run.py` | Preserve selection, lifecycle events, reports, interpreter identity, command settlement and independent harness errors. After the checkpoint, since these edits change default cases, repair selected bare-assertion paths in smoke, apply-isolation-v2 and witness-baseline scripts so an assertion does not merely disappear into an unrun case; do not classify arbitrary exceptions as product verdicts. |
| `pytest_engine.py`, `pytest_family.py`, `receipts.py` | Preserve setup/call/teardown and complete command/input accounting. A successful observation phase is not a passing product assertion. Do not blanket-catch `AssertionError`; unexpected exceptions still fail. Reuse input/blob recording and remove replaced unittest scheduling/status duties. |
| `execution_contract.py`, `release_accept.py`, `release_archive.py`, `release_runs.py` | Replace all-parent/all-item-pass assumptions and the requirement for a native command on every item. Revise dispatcher and candidate/release validation together, using independently captured selection/authority expectations. Keep producer-bound historical interpretation. |
| Cargo and Swift TestKit wrappers | Keep batch exit, failure-count, log and summary checks. Correct selected assertions in those runners; an individual observation cannot be made non-gating by relabeling its parent or ignoring execution. |

Pytest owns internal discovery, fixtures and phases; PolicyWitness owns public
selection, prerequisite/artifact admission, command supervision, durable evidence,
cleanup and retention. Keep whole-family public selection and isolated pinned
packages. Collection must not acquire equipment, execute experiments, download
packages or replace evidence.

Generalize the demonstrated exec assumptions in `pytest.ini`, source receipts
naming `exec_domain.py` / `check_exec_evidence.py`, and exec-specific display
artifacts. Keep domain observations with their owner. Pure items need phase/input
evidence and an explicitly empty operation set, not dummy commands or ownership
processes. Actual commands need supervised, complete references and their
controlled environments. Preserve direct-command versus descendant accounting
limits. Check fixtures for hidden acquisition, shared mutation and cleanup errors;
a shared teardown failure must retain its true scope even when attached to the
last item. Preserve the existing exec family's native sequence and fault controls.

### Reports and retained evidence

| Surface | Required account |
| --- | --- |
| Case/family | Promised/completed observations, evidence, evaluated propositions and authority, execution/validity/cleanup failures. Preserve partial evidence after later failure. |
| Run | Exact selection and completion accounting, blocking failures, advisory judgments and informational completions. Keep parent and nested-item scopes separate. |
| Terminal, including quiet mode | Unfavorable non-gating judgments and observation failures remain visible with artifact paths. |
| Candidate/release validation | Required experiments completed validly, resources settled and enforced judgments satisfied; non-gating results explicitly summarized. Preserve signing, identity, unchanged-byte and portable-evidence obligations. |

Current `run.json.counts` / `reports` cover legacy reports, exclude pytest families
and declare `counts_scope`; `case_outcome_counts` includes all parents. Nested
items have a separate account. `completion.completed` counts pass or fail,
not favorable results. Preserve or explicitly revise these scopes. Do not invent
legacy assertion counts, add parent/nested counts, or count informational
completion as a passing product assertion.

Read historical runs under their producing contracts: failures remain failures,
ambiguous evidence remains ambiguous and unsupported formats remain refused.
Choose the necessary version boundary during implementation. Do not rewrite
archives or apply new authority retrospectively. Retention/publication still
reject missing required accounts and unresolved ownership.

### Capability verification and checkpoint

Extend independent fixtures in dispatcher, shell-helper and preflight controls:

| Contrast | Required result |
| --- | --- |
| Valid unfavorable pilot comparison | Correct advisory conclusion visible in case, terminal and run; dispatch and battery validation remain eligible when enforced controls hold. |
| Missing receipt, changed identity, omitted member or corrupt operation reference | Acceptance fails for validity/accounting while earlier valid observations remain readable. |
| Incorrect enforced fact or missing independent effect | Designated blocking assertion failure, not just a crash/missing report; a valid neighbor still runs. |
| Advisory unfavorable plus failed teardown, command settlement or artifact mutation | Advisory remains non-gating; the independent fault rejects acceptance. |
| Pure, commanded and legacy cases together | Exact counts, prerequisite behavior and continuation; no informational passing assertion. A dependent runs after a valid advisory-unfavorable or informational predecessor and is blocked after an invalid or incomplete one. |
| Deleted/relabelled judgment, dropped family reference, contradictory authority or terminal account | Independently captured expectations reject the altered account. |
| Historical/portable evidence | Original semantics preserved; removing required artifacts causes verification/publication/retention refusal. |

Retain cancellation, unavailable-engine, partial-phase, changed-context,
command-settlement and ownership-recovery controls. Use
`--suite dispatcher --suite shell_helpers`, explicitly including
`dispatcher/pytest_controls`, plus `preflight/release_controls`,
`preflight/release_publish_controls` and `preflight/release_rotation_controls`.
Include `preflight/release_deadline_controls` when command supervision changes.
Verify selections with `--list` and use fresh owned output.

Land capability without conversions or build-input changes and execute the
management plan's [live/replay checkpoint](TRACE-MANAGEMENT-PLAN.md#three-boundaries-for-broad-runs).
Finish shared support for cohorts, conversions and seams here. Preserve
inputs listed in [build_contract.py](../docs/build_contract.py). The same
management section owns later-reader verification and the adapted final
`preflight/build_refusal_controls`; do not add another broad battery here.

## Migrate the pytest cohorts

Implement pytest-native functions, fixtures and meaningful parameterized units.
Neither collecting `unittest.TestCase` classes nor wrapping a script's `main`
in one item satisfies the migration. Preserve exact parser structures, vendor
tampering, import contamination and `receipts.TestCase` input/command evidence.

After capability support and the checkpoint, compare old and migrated paths on
the same controlled inputs at identified revisions: observed facts, rejected
faults, command boundaries and available artifacts. Retire old orchestration
once equivalent. Keep subsequent authority changes separately attributable.
Account for retired dispatch/restoration/result duties and added fixtures,
adapters, identity maps and receipt machinery.

## Convert cases and correct trace claims

Obtain trace dispositions and remaining product obligations from management;
return later evidence to that assessment rather than creating another inventory.
A response may correct or narrow an assertion, change its authority, retire an
uninformative test or retain justified enforcement.

With each correction, update assertions, literal success/failure messages,
misleading names, catalog descriptions, suite accounts and affected coverage/
support together. Check `tests/COVERAGE.md`, `tests/FAILURE-PROPAGATION-CONTRACT.md`,
change-verification guidance and contract support where implicated. Preserve
references/selectors/dependencies when IDs change. Trigger changed assertion and
completion paths and compare their actual messages with the claimed scope.

### Descendant lifetime and aftermath dependency

Convert `runner_exec_lifecycle/closed_streams_leader_exit` to a verdict-free
lifetime observation. Its [checker](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py)
currently requires a post-completion ping from the original surviving descendant.
Retain generation/group identity, stream acknowledgments, independently registered
exit events, observed intervals, later file effects, raw CLI output and separate
cleanup. Management assesses remaining truthful-evidence/effect obligations,
including fixed no-request expectations that could reimpose survival.

Register observers before triggering completion. Distinguish a live original
generation with an acknowledged ping from that generation's independently observed
exit before cleanup. Retain timing relative to CLI completion and available
termination evidence; exit alone does not identify its cause. Resolve ping/exit
races with registered events, not missing-PID inference. Unresolved promised
classification is incomplete. Cleanup must handle live and already-exited
processes without losing uncertain ownership.

Replay both histories, then exercise the existing implementation and an identified
disposable control ending the descendant before sampling. The old assertion must
reject the prior-exit history and the new observation complete; missing exit
evidence, changed identity and failed required observations still reject. Keep
process/effect observations ahead of JSON interpretation and cleanup.

The control ends the descendant from outside the product, so the returned exec
account still reports `not_requested` after `leader_exit_and_eof`. It
establishes the instrument's sensitivity to a prior exit, not acceptance of a
product that ends the descendant itself. The checker's own fixed no-request
expectation follows management's ruling on that relation.

Remove both `closed_streams_leader_exit` and `worker_dies_during_exec` from
`run_effects/aftermath_footprint` dependencies. Aftermath's shell, checker and
`HeldWorkload` build their own fixtures, register exits and write local receipts;
they consume neither predecessor's artifacts nor verdict. Retain observer/checker
prerequisites. Keep the worker-death case's independent checks and default
selection; abnormal worker death is outside this authority conversion.

Make the converted survivor explicitly default-selected and remove it from the
catalog's `opt_in.include`, which the dispatcher selection controls tie to
non-default membership. Run aftermath without
either lifecycle predecessor, then mixed selections with the informational
survivor. Follow valid prior-exit evidence through checker, dependency admission,
dispatcher and aggregate battery acceptance; absence of survival must not fail.
Invalid observation and unsettled cleanup must still fail. Update catalog/suite
accounts, FOOTPRINT fa5/fa6 via [footprint.json](../docs/footprint.json), the WORKER
resource claim and COVERAGE with the conversion.

### Retirement and worker-wait pilot

Convert BYOXPC retirement completion to informational reporting. Preserve its
48-request sequence, declared gaps, separate transport/host outcomes,
valid-envelope and generation observations, watchdog, logging and service removal.
It already enforces no favorable success ratio.

Report the worker-wait pilot's matched-pair conclusions as advisory. Keep raw
counts/timings separate from evaluated improvement. Worsening or unestablished
improvement remains non-gating; scheduled receipts, calibration, coverage,
exclusions, executable identity, staged-process lifetime and cleanup retain their
requirements. A dry run gains no measurement credit. These conversions do not
supply the survivor's required reduction in enforcement.

### Selected trace corrections

| Findings | Correction and verification |
| --- | --- |
| DT-53/132 | Follow selected lifecycle-coverage claims through [consumer.py](../tests/lib/consumer.py), [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py) and adapters. Invoke the responsible independent check, add the missing assertion or narrow the credited claim. Do not broaden the consumer automatically. Retain an accepted baseline, missing `final_status`, and a wrong value beside unchanged raw status. Use consistent binary capture for whole-envelope claims; identify the rejecting reader, diagnostic and public-result effect. |
| DT-63/124/125 | Correct `ActorAuthorityTests`' last-transfer comment/support: its final `erased` flag is read after teardown. Retain justified final-state checks. If last-use support is needed, observe nonzero storage before teardown and omit only last-use clearing while retaining final cleanup. Inspect [extension boundary checks](../tests/suites/witness_contract/check_extension_boundaries.py) and [terminal erasure controls](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py) before adding an observer. Distinguish flags, scanned bytes, call counts and timing. DT-125's omitted-call sensitivity was source-read, not executed. |
| Transport | In `run_flow.rs`'s actor fallback tests, distinguish helper invocation policy from independent byte/input provenance and attribution. The shared fallback rehearsal retains submitted form, transport result, actual calls/input bytes, captures, field presence and side effects without requiring a particular call count. Management selects product changes. |
| Receipts: DT-95–104/134 | `compiled_profile_labels_determine_the_public_admission_outcome` enforces labels, not authenticity or request association. Correct stronger credited claims; retain enforcement unless management changes admission. The capture rehearsal must account for both application-success and clean-completion guards in `CWorker.swift`. |

Use affected Swift, C and integrated reader paths for lifecycle/erasure checks.
Rust edits under `controller/src` change build identity: land these after the
instrument checkpoint and rebuild with their thread.

## Migrating executable test seams

Management owns the [eight controls and admission rules](TRACE-MANAGEMENT-PLAN.md#bounded-test-seam-migration).
Capture old positive/rejected experiments before changing entry points. Migrate
each selected invocation and its wrappers/BYOXPC variants after the checkpoint;
leave other scenarios in the same files outside scope.

### Selected seam callers

Caller map from `3d3f8e65`; confirm intervening changes before editing:

| Use | Callers |
| --- | --- |
| Pre-ready/native refusal | `witness_contract/check_pre_apply_failure.py`: pre-ready hang/timeout and invalid delay/signal/slot arguments; separate worker substitution stays outside. |
| Deadline/in-flight/grace | `runner_outcome_runner_timeout/check.py`, its `runner_use_c_worker/worker_timeout_ms_honored` caller, and `witness_contract/check_attempt_in_flight.py`. |
| Publication/termination | `check_killed_before_publication.py`, `check_worker_sparse.py`, `check_worker_termination.py`, `check_extension_directory.py`, including `actors_byoxpc`. |
| Actor applicability | `check_actor_compositions.py`, particularly paired `timeout_applicability_specimens`. |
| Launch/ready/reservation | `runner_exec_inheritance/launch_inventory.py`, `runner_ready_byte_resilience/run.sh`, BYOXPC `single_use.py` and `bad_neighbor_claims.py`, including direct-client submissions. |
| Validator faults/deadlines | `runner_validator_failure/check.py` and `runner_validator_failure/check_signal.py`, `runner_outcome_validator_no_reply/check.py`, `check_phases.py` and its BYOXPC caller. |
| Ordering/comparison | `check_ordering.py`, its shell/mutation callers, and `check_comparison_matrix.py`. Keep matrix expectations independent of observed output; separate controls in the invocation adapter. |
| Identity/strings/paths | `check_dossier.py` and BYOXPC caller, `check_diagnostic_transport.py`, `check_path_queries_integrated.py`, `failure_boundaries/check.py`. Distinct worker substitutions stay outside; management retires the one combined worker/validator oversize pair in `failure_boundaries/check.py` to its unit control. |
| Held workloads | [footprint_workloads.py](../tests/lib/footprint_workloads.py)::HeldWorkload for `check_held_phase_footprint.py` and `check_aftermath_footprint.py`, actor hosts and constructed CPU controls. |
| Request/evidence | `runner_outcome_bad_request/contract.py` live self-signal case; current request examples, shape/generator controls and evidence readers. Preserve historical fixtures' semantics. |
| Internal/lower-level | Swift `RequestContractTests`, `QueryAdmissionTests`, `ServiceAdmissionTests`, `PhaseProtocolTests`, `OrderingTests`, and controller dossier tests. Preserve direct framing, sanitization and driver checks; constructed `ReplyFailureTests` records do not establish ordinary admission. |

Unqualified `check_*.py` names are under `tests/suites/witness_contract/`;
other suite-relative names are under `tests/suites/`. Mixed internal records
may remain through direct construction or revised controls without creating a
mixed public execution route.

### Implement and verify

Reuse CLI/run orchestration, client transport, host admission and native planning.
Use [interface definitions](../controller/interface/README.md) for command/help.
Keep fixture construction, expected effects and cleanup with the harness; exercise
the normally built executable, not a replacement driver or test-only build.

Preserve accepted numeric domains and the native rejection boundary: an
out-of-range native-argument experiment must not become only a CLI usage refusal.
Keep malformed CLI syntax separate. Ordinary `timeoutMsForCWorker` floors its
value; actor inputs use `PWActorLimits.executionMs`. Preserve delay/signal/slot
behavior and the independent ordinary/actor applicability contrast.

Retain actual command, ordinary input, controls, source/app identity, raw output
and applicable timing/exit evidence. Identify experimental intent even on early
refusal or transport failure. Reuse echoes/equipment provenance where sufficient;
preserve safe path handling and distinguish requested from observed intervention.

Compare old/new experiments at identified app revisions for component execution,
intervention, independent effects, fault rejection, identity, command accounting
and cleanup. Retire temporary dual entry points before crediting migration;
keep assertion/authority changes separately attributable.

For each selected control, establish new-route activation and rejection of its
old key through ordinary CLI and lower-level client/host admission. Cover inert,
invalid, combined and mixed inputs, unreached interventions and early refusals,
with valid ordinary neighbors and unchanged unselected substitutions. Verify
`test-input read` still launches nothing and retains publication/refusal behavior.

Run unit, integration and source-drift routes, `witness_contract/test_input_controls`,
`witness_contract/test_input`, affected admission/native-boundary routes and all
mapped experimental callers. Confirm selection/dependencies with `--list`.
Complete migration before final verification; default/selected opt-ins and the
extracted development-candidate battery use the new route. Future release
batteries inherit these callers under strict release admission.

## Acceptance argument: preservation and reduction

Run each conversion/cohort with its controls, the existing exec pytest family,
and management's grouped/final selections. Use native runs for live observation
and cleanup claims. Preserve source/app identity and interrupted ownership;
environment refusals are not product evidence.

For each authority reduction or retired activation path, identify the old
obligation and demonstrate its disappearance through fixtures, dependencies,
dispatcher and the outermost relevant acceptance boundary. Retain independent
oracles and validity/build/release/provenance controls. The survivor conversion
must accept otherwise valid prior-exit behavior; seam migration alone does not
satisfy enforcement reduction. Claim that reduction at the scope management's
ruling on the `leader_exit_and_eof`/`not_requested` relation supports: while the
relation stands, a product that ends the descendant and reports it is still
refused at controller admission, and the account says so.

Complete both pytest cohorts, selected conversions and corrections, reporting
capability and all selected seam callers. Account for preserved observations and
rejection coverage, removed enforcement/orchestration, corrected claims and added
adapter/fixture/reporting duties. Use the acceptance plan's shared rehearsals;
retain separate evidence for migration equivalence and authority revision.

Put each test's present authority and reason in its suite account and changing
commit. Supply resulting user duties and consequential otherwise-unrecoverable
reasons to management's outflows under its retention rule. Do not create a
permanent withdrawn-enforcement registry.

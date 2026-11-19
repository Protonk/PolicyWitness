# Test outcome overhaul plan

**Handoff, November 19.** The reporting capability, both pytest cohorts, the
experimental control migration, and the four case conversions and their
follow-ups have landed. The dated stages below preserve their original
selections and evidence. The [management checkpoint](TRACE-MANAGEMENT-PLAN.md#product-group-checkpoint)
owns the remaining technical statements, test-side assertion repairs and
final verification.

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
| `witness_contract/worker_wait_pilot_controls` | All scenarios of the former `tests/suites/witness_contract/worker_wait_pilot_controls.py`, now [test_worker_wait_pilot_controls.py](../tests/suites/witness_contract/test_worker_wait_pilot_controls.py): ordinary/actor/neighbor receipts, decoding and interval arithmetic, historical missing records, grace/scan analysis, faulty formulas, exclusions/pooling, comparisons, disk/Markdown round trips and stager identity controls. |
| `source_drift/markdown_reader` | The complete population of the former `tests/suites/source_drift/markdown.py`, now [test_markdown_reader.py](../tests/suites/source_drift/test_markdown_reader.py): block/comment/link/heading/table/line interpretation, vendor bytes/import rules and fresh-process guards. Baseline: eight test classes, 38 methods and subcases. |

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

Callers added after the migration, each submitting a validator substitution
through the adapter: `runner_validator_failure/check_actor.py` (scenarios
`actor_validator_failure.{apply,unapplied}-{spawn,decode}`, with rulings R4)
and `failure_boundaries/check.py` (`validator_empty_step_id.*`, with R5).

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

For selected conversions and pytest migrations, preserve marginal-value
observations from the mutation controls and negative contrasts already examined:
where a test supplies a distinct rejection of an incorrect behavior, where another
retained test rejects that same behavior, where apparently independent tests share evidence,
expectations or interpretation machinery, and where meaningful additional detection
cannot be established. Distinguish independent observations from independently
authored assertions over the same observations. Overlapping names, fixtures or
results do not establish redundancy; several failures on one mutation do not
establish independent rejection. Keep these notes in existing working records and
run evidence under management's [observational limits](TRACE-MANAGEMENT-PLAN.md#verification-sequence),
particularly when enforcement is withdrawn or orchestration retired. No new mutation
campaign, complete test inventory or numerical redundancy measure is required.

Complete both pytest cohorts, selected conversions and corrections, reporting
capability and all selected seam callers. Account for preserved observations and
rejection coverage, removed enforcement/orchestration, corrected claims and added
adapter/fixture/reporting duties. Use the acceptance plan's shared rehearsals;
retain separate evidence for migration equivalence and authority revision.

Put each test's present authority and reason in its suite account and changing
commit. Supply resulting user duties and consequential otherwise-unrecoverable
reasons to management's outflows under its retention rule. Do not create a
permanent withdrawn-enforcement registry.

## Capability preparation — 2026-11-17

Inspected revision: `887b485f`; source-only baseline, before reporting changes.
The two cohort files are byte-identical to the planning snapshot. SHA-256:
`markdown.py` is `3ca0606d53648f7f437d198bd316ab87aae9c485e1fc6990e225eb3d27673f6f`;
`worker_wait_pilot_controls.py` is
`85feaa1c661c0714ac5767c8811072f11c16872ffc88996cc39b59881b3b3c0e`.
This inspection preceded both migrations. The later cohort records below
compare the old and new executions for the 66 Markdown reader items and
232 worker-wait pilot control items.

### Cohort scenario and evidence map

The Markdown baseline has eight classes and 38 `test_` methods. Preserve the
original `Class.test_method` identities when assigning stable pytest identities;
split parameterized subcases retain both the method and the concrete input.
The table identifies the full population, including multi-assertion methods.
Its expected parse structures and diagnostics are hand-authored, not obtained
by running the reader to generate expected values.

| Original class (methods) | Observations and independent expectations; setup/cleanup |
| --- | --- |
| `BlockTests` (7) | Same-marker/length fences including comment openers and nested shorter markers; backtick info refusal; list fences; paragraph continuation versus indented code; nested/continued list prose and link bounds; no first paragraph when an item starts with another block; leading code/strong/link. Literal structures, source line bounds and absent links remain exact. Pure in-memory items. |
| `CommentTests` (5) | Block/inline comments versus prose, three double-hyphen refusal inputs, unmatched opener, escaped/entity/code openers, line-start comment paragraph termination. Preserve exact refusal text and hidden heading/link cases; pure items. |
| `LinkTests` (6) | Wrapped labels versus blank-line separation; images/escapes/code/autolinks including route-looking hidden content; decoded destinations; ordered inline pieces; image inside link; reference definitions and undefined references. Exact tuple/piece order is enforced; pure items. |
| `HeadingTests` (6) | ATX/setext and excluded contexts; section end at equal/higher level (four subcases), absent and duplicate section; multiline anchor; underscore/duplicate/Unicode slugs; explicit ID/name anchors including multiline/entity forms; excluded anchor examples in fence/code/comment/escape/script. Pure items. |
| `TableTests` (2) | Inline escaped pipe/link/cell line bounds, and table-like content hidden in comments/fences. Pure items. |
| `LineTests` (1) | Exact paragraph lines and five offset-to-line results. Pure item. |
| `VendorTests` (5) | Wheel RECORD digests and file inventory; simultaneous changed/added/missing file names; rewritten RECORD rejection; Git-discovered Python import rule; three constructed importer files. Temporary declared reader trees are registered before mutation, captured before cleanup, then removed. `git ls-files '*.py'` is a real recorded command in the repository cwd. |
| `ImportGuardTests` (6) | Fresh-process vendored load; missing vendor beside installed stand-in; already imported foreign parser; already imported linkifier; wrong parser version; installed linkifier never imported (independent marker absence). Copy only declared inputs, retain stand-in bytes and environment, run real fresh Python with `-B -S -P`, then capture/remove temporary trees and marker parent. |

`receipts.TestCase` currently records initial inputs, subtest before/after
snapshots, command argv/cwd/selected environment, output, duration and return
or exception, then captures inputs before cleanup. The new fixture adapter
must preserve those duties while retiring unittest discovery/result/subtest
scheduling. Unexpected exceptions and fixture cleanup failures remain failures.
The existing records count direct subprocess calls, not every descendant;
pytest migration must not silently make a stronger command-count claim.

The pilot baseline is a sequential `main`, not unittest discovery. Preserve
the identities in `accepted`, `rejected[].control`, each `fault(name, expected,
...)`, and each named rule-control return value. The table covers every region
of `main` and every delegated control group; no helper wrapper is itself the
intended pytest unit.

| Original scenarios/functions | Observation, oracle and equipment |
| --- | --- |
| Layout/stages and ordinary/actor/neighbor bundles | Hand-packed offsets/stages; O1 intervals/endpoints/uncertainties/pass counts, A2 per-visit waits/exchanges/custody and scan values, neighbor acceptance. Independent integer arithmetic stays separate from reader formulas. Pure inputs. |
| Historical records | O1/A2 without pass/store/stamp/sleep records; O1/A2 without sleep pairs alone. Accept available facts, retain unknown labels and conservative bounds, and compare unchanged intervals only where actually established. Pure inputs. |
| First-positive, done and inversion cases | Register-only single/multi-wait attribution, event-pair attribution, unattributed arrival, first-positive done, absent done register, actor subject done, 20 µs release inversion. Preserve each endpoint/uncertainty/attribution assertion and absence assertion. Pure inputs. |
| Calibration/role limits | No calibration, unbounded alignment, missing endpoint term and role-unknown scan flag. These are valid unavailable measurements, not invented zero durations. Pure inputs. |
| Grace, final-wait and resampling controls | Four ordinary grace outcomes, actor-specific exit intervals/stops, group sums; truncated wait pairs, settle sleep classification, outcome association/reversal; final wait absent/malformed/applicability and teardown intervals; resampling absent/empty/malformed cases and distinct startup points. Preserve every named return label and malformed-input subcase. Pure inputs. |
| Replaced formulas and actor-blind variants | `old_uncertainty_formula`, actor-blind intervals/stops, ignored spread, float scan comparison and ignored scan floor must be rejected by hand-authored expectations. Temporarily replaced reader functions must be restored even on failure; these mutations establish reader sensitivity, not production performance. |
| Order and sleep rule groups | Appended old samples accepted only where program ordering allows; fresh backward/origin faults refused. Sleep truncation past 64 pairs, complete/register-only attribution, no-sleep/unattributed distinction and tiny negative formatting retain exact expectations. Pure inputs. |
| Initial disk round trip | Five ordinary/overlapped/unattributed/actor/neighbor bundles, schedule, constructed identity and clock-pair records go through loader, decomposition/summary JSON and Markdown. Expect four accepted, one excluded, separate groups and exact literal explanatory fragments. Keep actual file inputs/outputs. |
| Calibration disk contrasts | Tampered calibration remains not-established while trial facts survive; endpoint outlier remains established but not credited. Preserve the separate concepts and refusal reasons, not only the final Boolean. Temporary copied trees are removed after observation. |
| Main fault table | All 56 named `fault(...)` entries, including two combined faults, carry their independent expected problem-code sets. Preserve rejected/incomplete/excluded distinctions, unchanged accepted baseline and all asserted codes, not merely nonzero process exit. Pure constructed records until loader-specific variants below. |
| Missing-file loader variants | `missing_stamps`, `missing_started`, `combined_missing_stamps_and_sleep`: expected incomplete status and both faults in the combined input. Keep actual deleted-path input snapshots. |
| Pooling controls | Reject pooling neighbor/instrumented, regime, cell, power source, low-power mode and host flavour; valid split low-power groups each retain one accepted observation. Pure rows. |
| `comparison_controls` / `response_repair_controls` | All named paired-series improvement/worsening/withholding, spread, uncertainty, direction, response bound/gate, unmatched/excluded/condition-changed, identical and uncalibrated variants. The correctness of these advisory-value computations stays enforced; an unfavorable product conclusion is not a failing reader control. |
| `scan_controls` and identical scans | Exact lower-ratio arithmetic including floats rounded equal; floor conditions, absent passes, required pair coverage, inbound count/ack mismatch, zero-visit sums and Markdown. Both full-scan and below-floor identical-scan variants remain. |
| `comparison_round_trip` | Six on-disk trials yield separate baseline/candidate groups, two pairs, excluded/unpaired records, exact combined uncertainty and literal Markdown/no-verdict content. Preserve input and output blobs before removal. |
| `stager_identity_controls` | Missing/malformed/duplicated tree constant, equipment mismatch, worker identity mismatch, and agreeing identities reaching the source record. Real `ditto` and stand-in worker `--version` occur before the intentionally raised `Reached`; no signing or native sandbox evidence. Restore patched stager functions in `finally`, retain controlled bytes and command receipts before deleting fixture trees. |

The current pilot shell message says constructed reader sensitivity, and its
`controls.json` explicitly disclaims live stamps/timings. Preserve this scope.
The migrated pytest suite split meaningful input groups and outcomes while
keeping the stager's real command boundaries and all named faults; collecting
one `main` item would leave its internal completion opaque. No fixture path or
resource lifetime is changed to consolidate storage during preparation.

### Required shared capability from these baselines

- Collection admits explicit module/source dependencies rather than assuming
  `exec_domain.py` and `check_exec_evidence.py`; `pytest.ini` must not limit
  discovery to the exec filename. Collection remains free of experiments and
  acquisition. Whole-family public selection stays with the dispatcher.
- Pure items record source/input and setup/call/teardown evidence plus an
  explicitly empty operation set. Passing execution means the declared
  observation completed; it supplies no invented count of product assertions.
- Commanded items preserve argv, cwd, controlled environment, raw stdout/stderr,
  exits, settlement and complete operation references. The existing
  `Equipment.command` interface has no cwd/environment parameters, so Markdown
  Git/fresh-process controls require that capability before migration.
- Reuse `receipts.Control`'s input/blob capture independently of its unittest
  scheduler. Fixture teardown snapshots precede deletion; a shared finalizer
  records its true family/session scope even if pytest reports it on one item.
- The exec family's baseline and integrity display rules remain with that
  domain. Generic family display must not assume every family has an exec
  baseline artifact, nor hide a non-gating judgment in quiet mode.
- Bind promised observations and judgment authority in the pre-evaluation
  selection/collection evidence. Phase success, failed expectation and failed
  apparatus/cleanup need separate carriers; unexpected exceptions cannot be
  reinterpreted wholesale as product judgments.

### Seam evidence design supplied to reporting

The pre-migration callers and eight controls in this plan remain unchanged.
Source diff from `3d3f8e65` to the inspected revision is empty. A future
invocation adapter can retain ordinary request bytes and explicit controls as
two input blobs, plus exact command argv, requested experimental mode, app/source
identity, output bytes and status/timing. The report must retain experimental
intent even if CLI admission, client transport or host setup prevents activation.
Only raw intervention observations and applicable echoes establish what ran.

Keep valid ordinary neighbors and unselected worker substitutions independent;
an ordinary override containing a selected key must fail even when its value
would be inert. Experimental legacy-block refusal and each native-domain
rejection require distinct scenario identities. The ordinary worker timeout
floor and actor execution allowance remain separate expectations. None of
these requirements needs an executable seam migration before the checkpoint.

At preparation, these maps specified which evidence to retain. The native
exec family and independent dispatcher/preflight controls established generic
capability. The subsequent cohort and seam records give the execution
comparisons and the one documented change of route.

## Reporting mechanism selected; instrument verification

The selected design attaches a required observation/judgment account to pytest
phases and a durable shell journal, with checked terminal projections. Selection
or collection fixes promises, propositions and enforced/advisory authority before
evaluation. Informational completions carry observations without inventing passing
product assertions. Execution, validity, command settlement and cleanup remain
independent requirements.

The [11-contrast mechanism comparison](../tests/out/runs/trace-reporting-compatibility/suites/dispatcher/pytest_controls/artifacts/outcome-mechanism-comparison.json)
gives a test-local extended terminal-account alternative the same authority,
evidence, phase and cleanup obligations. Both complete representations produced
the independently specified decisions on ten contrasts, including unfavorable
judgments, missing observations, contradictory authority, failed phases/cleanup
and damaged or missing evidence. The interruption contrast retains an observed
prefix in the chosen journal without crediting completion; the terminal alternative
needs an additional required journal to preserve that prefix. These controls
establish the choice. Optional annotations, status labels alone and blanket
conversion of exceptions into product judgments were rejected.
The material cost is explicit declarations, durable account/projection duplication
and byte-level rereading; existing lifecycle machinery supplies ordering and
completion instead of adding another test scheduler.

`pw-family-evidence-2` activates new meanings only through the captured outer
producer contract and independently fixed declarations. Version 1 keeps its
original pass/fail/skip and passed/native-item interpretation, including opaque
extension fields and schema metadata its reader ignored. Nested labels cannot
upgrade authority. Ordinary pure or commanded pytest assertions remain enforced
through `pw_commands`; they need no authority conversion. Parent and nested counts
stay separate. Readable judgments can survive an independent validity, execution
or cleanup failure, so counts never establish eligibility. A missing entire shell
terminal leaves its journal readable but the parent unrun, without a fabricated
assessment or completion credit.

At `5577a4eb`, the [eight-case focused verification](../tests/out/runs/trace-reporting-compatibility/run.json)
(`20261118T010714Z_cc968f17`) passed, including compatibility/replay controls,
actual version-2 fixtures, candidate/portable rereading and the unchanged native
exec family. The [baseline default](../tests/out/runs/trace-instrument-before/run.json)
at `2f4d76e4` and [corrected default](../tests/out/runs/trace-instrument-after-corrected/run.json)
at `5577a4eb` each completed 233 parents, 232 legacy reports and nine exec items
against the same signed app and declared build contract. The earlier
[post-capability run](../tests/out/runs/trace-instrument-after/run.json) remains a
failure: its sole failed obligation was the Python file-start convention, corrected
in `bd954397` without relaxing the guard. These failures were implementation
defects. Management retains the detailed run and artifact account.

The final [deterministic comparison](../tests/out/runs/trace-reporting-compatibility/investigations/reporting-checkpoint/comparison/checkpoint-replay.json)
passed 455 checks across 65 reader commands. Old and new readers agreed on full
semantics for all 13 version-1 constructed comparisons and both live datasets.
Two version-1 inputs with missing ownership or unstarted history produced the
expected apparatus refusals;
eight version-2 fixtures produced the independently expected new decisions and
old-reader unsupported-profile refusals. Original evidence bytes remained unchanged.
The [completed-battery reread](../tests/out/runs/trace-reporting-compatibility/investigations/reporting-checkpoint/completed-battery-reread.json)
accepted both original completed runs and confirmed four identical app inventories,
the unchanged development build contract and identical frozen, source and distributed
guide bytes. Replay establishes interpretation, not renewed execution, signing,
resource-absence or release-acceptance credit. Together with the live and focused
controls, this establishes the reporting instrument checkpoint. All `tests/out`
links here are gitignored evidence available in this local checkout.

The shared capability now supports the prepared cohorts and seam evidence:
module-declared source inputs, reusable input/blob recording, explicitly empty
pure-item operation sets, supervised commands with controlled working directories
and environments, and required raw-evidence rereading. Input-recorder finalization
does not order other fixtures' cleanup; each migration must retain its own inputs
before deletion. The subsequent sections record
the completed migrations, executable comparisons and case conversions.
Private development-candidate and release readers share verified evidence machinery,
while receipt kinds and known development markers prevent release credit. Their
controls establish interpretation; no extracted live-candidate acceptance is
claimed at this checkpoint. That execution remains in the specified later
build-refusal control.

## Cohort migration: Markdown reader — 2026-11-17

Status: migrated, compared and retired. `5ab8e530` adds the pytest family and
moves every reference; `116cae5a` deletes the unittest script, which stayed
unreferenced for one commit as the old side of the comparison. No shared
engine or reader file changed. Authority is unchanged: every assertion remains
an enforced pytest assertion.

[test_markdown_reader.py](../tests/suites/source_drift/test_markdown_reader.py)
has 38 functions with the former method names, collected as 66 items. A
`pw_id` is `Class.test_method`, with a label where the function runs once per
input. Seven items declare recorded commands (the Git listing and six fresh
Python processes); 59 are pure with an empty operation set.

| Class | Methods | Old subtests | Items |
| --- | --- | --- | --- |
| `BlockTests` | 7 | 0 | 15 |
| `CommentTests` | 5 | 3 | 8 |
| `LinkTests` | 6 | 0 | 15 |
| `HeadingTests` | 6 | 4 | 14 |
| `TableTests` | 2 | 0 | 2 |
| `LineTests` | 1 | 0 | 1 |
| `VendorTests` | 5 | 0 | 5 |
| `ImportGuardTests` | 6 | 0 | 6 |

Local managed development runs under `tests/out/runs/`, gitignored and subject
to ordinary retention:

| Directory / run ID | Result and scope |
| --- | --- |
| `trace-cohort-markdown-old` / `20261118T030245Z_257f17cd` | Old path at `837296af`: pass. |
| `trace-cohort-markdown-new` / `20261118T033600Z_2644243b` | New family with the migration staged; module bytes equal `5ab8e530`: 66 of 66 items pass. Owns the equivalence investigation. |
| `trace-cohort-markdown-final` / `20261118T033944Z_a2571423` | `--suite source_drift` at `116cae5a`: 11 of 11 pass, no system sleep. |

The equivalence investigation is
`trace-cohort-markdown-new/investigations/cohort-equivalence/`; it credits no
case. Its `comparison/summary.json` records: no identity unmapped in either
direction; all 218 outermost constant expressions of the old methods present
in the same-named functions; all old tests and subtests and all new items
passing on the same inputs; seven commands against seven, the six Python
commands equal in argv, working directory, selected environment, return code
and output after temporary-name replacement, and the Git listing differing
only by the new module's own path; every old tracked tree equal in paths,
modes and content at registration, before the command and before cleanup. The
same comparison against the checkpoint battery's retained old-path record
agrees. Not compared: inherited environment outside the registered settings,
command descendants, durations, and blob bytes of the seeded rounds.
`CORRECTION.txt` records that the disposable checkout differed from the
migration commit by three prose edits in two READMEs that the case does not
read.

Seeded faults ran in one detached worktree with expectations written first;
`rejection.json` records the results. The worktree's ten runs were pruned with
its own tooling and the worktree removed. Four faults in one round (a pure
expectation, a removed version check, a Git-listed importer, a temporary-tree
cleanup failure) were rejected under corresponding identities on both paths;
the cleanup failure fails only the owning item's teardown. One changed
vendored byte fails the same three `VendorTests` on both paths. A reader that
refuses import ends the old script before any test with no receipts; in the
family, collection succeeds, 63 items fail setup and three pass.

Duties retired: unittest discovery, result and subtest scheduling; the
launcher block and `markdown.log`; `markdown-receipts.json` and its shared
blob store. Duties added: a lazy session reader fixture, so collection imports
neither the reader nor the fixture copier; a temporary-directory owner that
captures registered trees before removal and fails teardown on a capture or
removal failure; reader-tree and stand-in factories; a command adapter with
one artifact directory per command; and the identity labels.

Marginal-value observations, recorded without a redundancy claim: the three
vendor-byte items reject the same live-byte change, because two of them copy
the live tree and compare whole lists; all but three items share the
in-process reader import; and the fence, hidden-heading and route shapes
repeat planner scenarios that `source_drift/runner_source_manifests_agree`
also exercises. These are independently authored assertions over shared
evidence, not independent observations.

Observed consequences of the existing capability, none requiring a shared
reader change:

- Any plan selecting this family is captured under `pw-family-evidence-2`,
  including the default battery, where it sits beside the schema-1 exec family.
- `run.json.counts` excludes the family, so the suite's legacy total reads 10
  while `case_outcome_counts` reads 11.
- A recorded-command item that fails before launching its command leaves the
  family unrun with incomplete accounting, not failed, because its observed
  commands differ from its declared scope. Both READMEs state this. It still
  blocks acceptance.
- A collection error refuses the whole selection (by code reading); the lazy
  reader import exists for that reason.
- Case evidence grows from about 0.8 MB to 11.2 MB, from per-item blob stores
  and ten collected sources per item.
- `--suite source_drift` now needs the pinned pytest packages.

## Cohort migration: worker-wait pilot controls — 2026-11-18

Status: migrated, compared and retired. `1acf8884` adds the pytest family and
moves every reference; `95d05b71` deletes the sequential script and its
launcher, which stayed unreferenced for one commit as the old side of the
comparison. No shared engine or reader file changed. Authority is unchanged:
every assertion remains an enforced pytest assertion, and the reader's
correctness stays enforced whatever authority the live pilot's product
comparison is given.

[test_worker_wait_pilot_controls.py](../tests/suites/witness_contract/test_worker_wait_pilot_controls.py)
collects 232 items. The constructed-input builders moved to
[worker_wait_pilot_constructed.py](../tests/suites/witness_contract/worker_wait_pilot_constructed.py),
which imports neither the reader nor the clock-pair module;
`tests/fixtures/dispatcher/pilot_unfavorable.py` imports the builders from
there. Three items declare recorded commands (five commands: the stager's
`ditto` and stand-in `--version` calls); 229 are pure with an empty operation
set.

| Group | Items |
| --- | --- |
| Layout | 2 |
| Receipts | 3 |
| Historical | 4 |
| FirstCheck (first positive, done, inversion) | 8 |
| Limits (calibration) | 4 |
| Grace | 18 |
| FinalWait | 10 |
| Resampling | 14 |
| ReplacedReader (old formula 3, actor-blind 2, spread 4, float 1, floor 2) | 12 |
| OrderRules | 5 |
| SleepRules | 17 |
| DiskRoundTrip | 8 |
| CalibrationContrasts | 2 |
| Faults | 56 |
| MissingFiles | 3 |
| Pooling | 7 |
| Comparison | 15 |
| ResponseRepair | 16 |
| Scan | 17 |
| ComparisonRoundTrip | 3 |
| Stager (5 pure, 3 commanded) | 8 |

A session fixture publishes `controls.json` with the same 71 accepted names and
76 rejected controls the script recorded, a `not_established` list and a map
from each item to the names it establishes. An item records its names as its
last statement, so the names of a failing item land in `not_established`. The
old script wrote no `controls.json` when any scenario failed.

The stager's two commands are routed, not replaced: the stager launches both
through one module-level `command`, and a fixture substitutes an adapter that
calls the dispatcher's recorded-command equipment with the stager's own receipt
directory as the artifact directory. The commands, arguments and controlled
environment are those the stager chose. `bundle.command` itself therefore no
longer runs in this case.

Local managed development runs under `tests/out/runs/`, gitignored and subject
to ordinary retention; no system sleep was recorded in any of them:

| Directory / run ID | Result and scope |
| --- | --- |
| `trace-cohort-pilot-old` / `20261118T153831Z_a80523e9` | Old path at `41d256af`: pass. |
| `trace-cohort-pilot-new` / `20261118T161117Z_9d22dca0` | New family with the migration staged: 232 of 232 items pass. Owns the equivalence investigation. |
| `trace-cohort-pilot-final` / `20261118T161510Z_89280c94` | The family at `95d05b71`: 232 of 232, the same thirteen source digests. |
| `trace-cohort-pilot-final-drift` / `20261118T161537Z_7e5d962c` | `source_drift` and `shell_helpers` at `95d05b71`: 19 of 19 pass. |
| `trace-cohort-pilot-final-dispatcher` / `20261118T162737Z_74536936` | `dispatcher/controls` and `dispatcher/pytest_controls` at `95d05b71`: 2 of 2 pass. |

Four `trace-cohort-pilot-dev-*` directories are development passes on the way
and credit nothing. The live `witness_contract/worker_wait_pilot` case lists
the family as a dependency; the pilot was not run in this thread, so admission
through that dependency is established by the listing only.

The equivalence investigation is
`trace-cohort-pilot-new/investigations/cohort-equivalence/`; it credits no
case. Its `comparison/summary.json` reads `ok` with no unexplained difference:

- **Identity.** Every accepted name, rejected control, fault name and rule
  label maps to items; thirteen items carry no old name and cite the old
  assertion lines they hold; nothing is unmapped in either direction. Two old
  entries shared a name across a rule control and a fault, so names are keyed
  per group.
- **Literals.** Of the 4189 outermost literal expressions of the old script
  outside docstrings, 4164 occur as written and 14 are regrouped into
  parameter rows with every constant present. Eleven are absent and each is
  accounted for: messages of removed wrapper loops, the closing print,
  `__main__`, one directory name and one raise message.
- **Assertions.** Of the old script's 376 assert statements, 342 are identical
  in the new modules and 34 are restated as parameter rows.
- **Facts.** The published scope, names, statuses and code sets agree; list
  order differs.
- **Commands.** Five against five with equal argv, exit status and output. The
  old side came from an in-process probe of the unchanged script, because the
  old run deletes its own receipts.
- **Trees.** Every constructed tree is equal before cleanup. The old copies of
  the tampered and missing-file trees also held three stale output files that
  the family's per-item trees do not.

Not compared: command environment, working directory and standard input;
command descendants; durations; blob bytes of the seeded rounds; the
restoration check under a failing item; and single-item isolation, for which
no public selector exists.

Seeded faults ran in one detached worktree with expectations written first;
`rejection.json` records the results, all as expected. The worktree was
removed with `git worktree remove` and its ten runs went with it.

| Fault | Old path | Family |
| --- | --- | --- |
| A magic check removed from the reader | Stops at `bad_magic` | Fails `bad_magic` and `combined_magic_and_pacing` |
| The 2 ms boundary comparison made strict | Stops in the boundary loop | Fails one exactly-2-ms item |
| The loader misses the clock-pair build record | Fails on the build fragment | Fails one item on the same fragment |
| The stager skips its equipment check | Reports `reached` | One commanded item reports `reached`; accounting complete |

Duties retired: the sequential `main`, accepted/rejected accumulation, five
try/finally restoration wrappers, manual `rmtree`, the launcher and
`assert.log`. Duties added: identity and account decorators with the
`account`/`established` pair; lazy reader, clock-pair and stager fixtures; a
checked `replace` fixture that owns restoration; tree fixtures; the command
adapter; and the family's source-file list.

Departures from the scenario map, each a recorded choice: the pooling rows are
evaluated in memory, where the map called them pure rows over staged files; a
mutation control now requires every check concerned with its fault to fail,
which is stricter than the script's first failure; stager artifacts land under
`artifacts/stager/<identity>/`.

Marginal-value observations, recorded without a redundancy claim: the
old-formula, spread and floor mutations are each rejected by several checks
over one fault; eight round-trip items read identical trees again; every pair
item reruns the every-pair worsening check; 224 items share one reader
import; and the first seeded fault showed two fault rows rejecting one defect.
These are independently authored assertions over shared evidence, not
independent observations.

Observed consequences of the existing capability, none requiring a shared
reader change:

- Case evidence grows from about 0.75 MB to 133 MB. About 115 MB is 232
  per-item copies of the family's thirteen collected sources. One family-level
  blob store in the engine would remove most of it; that is a change to the
  shared engine and is left as a maintainer judgment, with the default
  battery's size stated in the release account.
- `run.json.counts` excludes the family, as for the Markdown cohort.
- The default `witness_contract` selection and the live pilot now need the
  pinned pytest packages.
- No fixture can see an item's outcome, so the published account depends on
  each item recording its names explicitly and on the session's failure count.

## Seam migration, first stage: adapter and old experiment — 2026-11-17

Status: the old experiment is captured; no entry point has changed. `b4e6fee1`
is test-only: 33 files under `tests/`, no product source, no rebuild.

[seam_invocation.py](../tests/lib/seam_invocation.py) is the one invocation
adapter for submissions that use a selected control. A caller gives it the
ordinary request without the selected controls, the controls as a separate
mapping and any `run` arguments. In this stage its one route merges the
controls into the delivered request's `_test_overrides` and submits with
`policy-witness run`, or with `pw-runner-client run` for the direct-client
callers. It serves Python callers (`SeamCapture`, `Submission`) and shell
callers (a file entry point) from one implementation. For each invocation it
writes, under the case's `artifacts/seam-invocations/<scenario>/`, an
`invocation.json` before launch (scenario identity, exact argv, requested
route `legacy_request_block`, app path and reported build contract, then exit
status and monotonic start and end), the ordinary request, the controls, the
delivered bytes and raw stdout and stderr. It interprets nothing:
expectations, independent effects and cleanup stay with each caller, and no
caller's assertion, expected value, message or cleanup changed.

Callers moved, with the number of captured invocations: the thirteen
`witness_contract` checkers in the caller map (29, plus 6 through BYOXPC and
mutation callers); `failure_boundaries/check.py` (18);
`runner_outcome_runner_timeout` and its `runner_use_c_worker` caller (3);
`runner_validator_failure` (3); `runner_outcome_validator_no_reply` (1);
`runner_outcome_bad_request/contract.py` (1);
`runner_exec_inheritance/launch_inventory.py` (2); BYOXPC `single_use.py` (1)
and `bad_neighbor_claims.py` (4, direct client over stdin);
`runner_ready_byte_resilience/run.sh` (1); and `HeldWorkload` (35), which
also brought in the opt-in `witness_contract/worker_wait_cost` as a caller
found from code. `run_capture/controls` gained adapter controls against a
stand-in executable.

Left off the adapter, deliberately:

- The one combined pair of `worker_executable_path` with
  `validator_executable_path` in `failure_boundaries/check.py` (`admission()`,
  combination index 9). Management retires it with the route change.
- The request-corpus example `fractional_override`
  (`worker_timeout_ms: 1.5`), submitted by the corpus loop through the CLI and
  the direct client with a corpus-owned `type_mismatch` expectation. Decision
  for the route change: it stays an ordinary submission and its expectation
  becomes the ordinary refusal of a selected key; a fractional value on the
  experimental route gets its own controls (a CLI usage refusal for the flag,
  a refused controls object at the client).
- Scenarios that use only `worker_executable_path` or
  `actor_equipment_executable_paths`.

Direct constructions that carry a selected control and are not live
submissions remain in `RequestContractTests`, `QueryAdmissionTests`,
`ServiceAdmissionTests`, `PhaseProtocolTests`, `OrderingTests`,
`ReplyFailureTests`, `ReplyMaximumTests` and two `controller/src/dossier.rs`
tests.

The old experiment, as local managed development runs under `tests/out/runs/`
(gitignored, ordinary retention), all against the `2f4d76e4` app with contract
`development:b55acb20…744719e`, all complete, none overlapping system sleep:

| Directory / run ID | Cases | Result | Invocations |
| --- | --- | --- | --- |
| `trace-seam-old-default` / `20261118T042533Z_ef7ca37a` | 48: 29 mapped callers, 13 cases that execute changed shared code, 6 dependencies | pass | 85 |
| `trace-seam-old-optin` / `20261118T042932Z_9c0aa679` | 3 | pass | 5 |
| `trace-seam-old-mutations` / `20261118T043020Z_9cacea3c` | 1 (`witness_contract/order_barrier_mutations`) | pass | 3 |
| `trace-seam-old-byoxpc` / `20261118T043136Z_0ca6cee0` | 4 | pass | 8 |
| `trace-seam-old-waitcost` / `20261118T043513Z_5ca12329` | 2 | pass | 3 |
| `trace-seam-old-drift` / `20261118T043557Z_5a1835a4` | 19 (`source_drift`, `shell_helpers`) | pass | none |

`trace-seam-old-waitcost/investigations/seam-old/index.json` indexes the
experiment: 104 invocations in 36 cases, every case and scenario pair unique,
all eight controls present. The reply echoed the supplied controls in 96;
six were admission refusals with no echo; two had no host reply. Ten stand-in
control records are listed apart. The four BYOXPC sessions installed in scope
`gui/501` were each removed with `cleanup_retained: false`, and service,
plist, staging, bundle and private registry were verified absent; the default
registry was empty before and after. One development run during the work
failed on a wrong constant in a new control and stays a failure; its
replacement passed.

Not run in this stage: `worker_wait_cost`'s activation role and its other
candidates, and the live `worker_wait_pilot`, which imports changed modules
and makes no adapter call. `dossier_witness_byoxpc` passes without an adapter
invocation because its BYOXPC path never reaches the override scenario. For
the route change: `check_extension_provenance.py` derives its expected
validator from the delivered request and must read the controls instead, and
`HeldWorkload` scenario identities derive from their artifact directory path.


## Seam migration, second stage: the experimental route beside the request block — 2026-11-17

Status: `72617789` adds the new route for the eight selected controls. The
request block still carries all ten keys, so every existing caller passes
unchanged; the ordinary refusal of the selected keys, the caller flip and the
old/new comparison belong to the third stage. The signed app is rebuilt:
build contract `development:fe9694b1…a6d14302` (before:
`development:b55acb20…744719e`), publication withheld, guide bytes unchanged.

What exists now:

- `policy-witness test-input run [--timeout-ms N] [--runner-mode KIND]
  [CONTROL VALUE]... REQUEST` reuses `run`'s orchestration, envelope and exit
  statuses. The controls are `--worker-timeout-ms`,
  `--worker-pre-ready-hang-ms`, `--worker-post-apply-hang-ms`,
  `--worker-post-apply-kill-signal`, `--worker-kill-before-publish-slot`,
  `--validator-executable-path`, `--validator-io-timeout-ms` and
  `--validator-total-timeout-ms`. An integer control takes any signed 64-bit
  decimal and is delivered as written. A missing value, a value of another
  form, a repeated control and an unknown flag are `tool_error` refusals with
  exit 2 and no client invocation. `run` admits no control.
- `pw-runner-client run --experimental-controls <JSON object>` calls the XPC
  entry point `runReservedExperiment(_:controls:reservation:withReply:)`;
  without the argument the client calls `runReservedSpecimen` as before.
  `test-input run` always passes the argument (an empty object when no
  control is given).
- The host owns the experimental admission. A request `_test_overrides` block
  holding any member, a null member included, is refused with
  `inapplicable_field` at `["_test_overrides"]`; an absent, null or empty
  block is admitted. The controls object is decoded by the block's decoder
  restricted to the eight members: `unknown_field`, `inapplicable_field` for
  the two unselected keys, `type_mismatch`, `invalid_json` and `missing_value`
  are located under `_test_overrides`. Validator-path capacity remains
  `admission_refused`. Both entry points reach one private submission
  function; capacity admission, the orchestrators, the echo and refusal
  sanitization read the one record either call supplies.
- No wire, layout, porcelain or reply-schema change and no shared-reader
  change. The worker identity is regenerated because runner sources changed.
- The dossier's validator record reads the validator control under the
  request key's rules; its reason names the flag.
- The adapter takes a route per call (`experimental_cli`,
  `experimental_client`); existing callers stay on `legacy_request_block`.

Differences from the design supplied to the stage, as implemented:

- No help card references a form or a control, so the cards are unchanged;
  the interface residue records the forms and controls as referenced by no
  card. The `test-input` usage line names both forms.
- The client capture does not record which XPC call was made; recording it
  would need a porcelain change, which the stage was told not to make. The
  call is identifiable from `--experimental-controls` in
  `data.runner_client.argv` and from the reply's echo, which is a non-null
  object for an experimental submission (empty when no control is given) and
  absent for the ordinary neighbour.

Runs, all local managed development runs under `tests/out/runs/`, none
overlapping system sleep:

| Directory / run ID | Cases | Result |
| --- | --- | --- |
| `trace-seam-b-pre` / `20261118T051021Z_5581a90d` | 3 | The new `witness_contract/test_input` rows against the `2f4d76e4` app: 22 pass, 49 fail, 24 unevaluated, because the command and the client argument did not exist. Intended; the other two cases pass. |
| `trace-seam-b-live` / `20261118T053824Z_472b3a5f` | 2 | pass |
| `trace-seam-b-suites` / `20261118T053900Z_56553011` | 44 | 2 fail |
| `trace-seam-b-suites-2` / `20261118T055500Z_3fd318a7` | 44 | pass |
| `trace-seam-b-bad-request` / `20261118T061025Z_cac6a073` | 4 | pass |
| `trace-seam-b-preflight` / `20261118T061213Z_a8951b45` | 2 | pass |
| `trace-seam-b-old-route` / `20261118T061232Z_567f594e` | 3 | pass: three callers left on the request block |
| `trace-seam-b-reservation` / `20261118T061301Z_693c1da2` | 1 | pass: the opt-in controls that compile the changed protocol |
| `trace-seam-b-live-2` / `20261118T061445Z_f15d39a5` | 2 | pass, final tree |

The two failures in `trace-seam-b-suites` were implementation defects in the
stage's own test material and stay failures: a mutation record in
`source_drift/interface_inventory` named an inventory entry that the
expansion control's fixture removes, and a new
`runner_unit/client_session_controls` control read a capture before the reply
that publishes it. Neither correction changed a build input.
`witness_contract/test_input` now holds 95 live rows and
`witness_contract/test_input_controls` 181 offline controls, one rejecting
control per row of the live checker. Six interface mutation records were
added; they were observed on an unsigned debug build in a disposable
worktree. The ten BYOXPC sessions of the reservation controls each record
removal, their staging is absent, and `runner list` and `runner reconcile`
were empty before and after.

Facts for the validator-substitution trace: the `Control` table in
`controller/src/interface/run_args.rs` decides flag, JSON key and value rule,
and the host's `PWRunnerTestOverrides.experimentalControls` decides membership
of the controls object. The controller's controls object and submission
arguments, the client's experimental submission and the host's submission
decoding only transmit. Added: the flags, the adapter route, the dossier's
control selection and the contract rules `request.overrides.experimental` and
`request.overrides.test_input_run`.

`test-input run` and its usage line are public and absent from the frozen
guide; this is a user duty for the guide rewrite.

## Seam migration, third stage: callers on the new route, old route retired — 2026-11-17

Status: the seam migration is implemented. `1cc5f2fa` (test-only) moves every
caller to `test-input run` or the client's controls object and removes the
legacy route from the adapter; it passed against the second stage's app before
any product edit. `eeb76c1b` makes the host refuse the eight controls in an
ordinary request's block, with lower-level tests, refusal controls, accounts
and regenerated files. The signed app is rebuilt with build contract
`development:081353c9…948ab695`; it was built from the working tree before the
commit, so its recorded commit is `1cc5f2fa` with a dirty mark, and the
committed tree derives the same contract. Publication withheld; guide bytes
unchanged at that revision. The eight limits texts were corrected later
in `bd8144ea`, following the fixture correction in `11e93191`.

Refusals as implemented:

- Ordinary submission: `inapplicable_field` at
  `["_test_overrides", "<control>"]`, decided in
  `PWRunnerTestOverrides.init(from:)` from membership of the raw container,
  after unknown request keys are rejected and before any member is decoded.
  Null, zero, negative and mistyped values are refused. With several controls
  present the first in the host's control order is named; an unknown member,
  the contract and earlier request fields are reported first. The reply is the
  existing decode-failure reply: `bad_request`, no worker or validator, no
  echo.
- Experimental submission with a block holding any member:
  `inapplicable_field` at `["_test_overrides"]`.
- A fractional value: a usage refusal with exit 2 and no client for the flag;
  `type_mismatch` at the member for the client's controls object; the corpus
  example `fractional_override`, an ordinary submission through the CLI and
  the client, is now `inapplicable_field` at the member.
- No new refusal code and no wire, layout, porcelain or reply-schema change.

What rejects the old behavior: 26 hand-written `ordinary.*` blocks in
`witness_contract/test_input` (each control through plain `run` with an acting
and an inert value and through the client's ordinary call, a control beside
`worker_executable_path`, and two controls together); the Swift
`ExperimentalSubmissionTests` group; the corpus example through
`accepted_input_contract` and `RequestContractTests`; `run_capture/controls`,
where the adapter refuses a route argument; and the drift rule that compares
the two key tables of `runner/README.md` with the host record's unselected
members and its control list.

Where source differed from the stage's brief:

- A validator path holding a NUL cannot be a command-line argument. The
  adapter refuses a NUL for the controller, and that one scenario
  (`failure_boundaries/admission`, `admission.nul-9`) goes through the
  client's controls object.
- The controller's `run` also read the request's validator key for the
  dossier. That reading is retired: only `test-input run` selects a validator
  record.
- `ServiceAdmissionTests` submitted an encoded validator override through the
  ordinary call; it now uses the experimental call.

Runs, all local managed development runs under `tests/out/runs/`, none
overlapping system sleep:

| Directory / run ID | App | Cases | Result |
| --- | --- | --- | --- |
| `trace-seam-c-dev-1` / `20261118T062641Z_32c2e84b` | `fe9694b1` | 4 | pass |
| `trace-seam-c-dev-2` / `20261118T063206Z_cef093b0` | `fe9694b1` | 3 | pass |
| `trace-seam-c-flip-default` / `20261118T063431Z_b21261d6` | `fe9694b1` | 48 | pass |
| `trace-seam-c-flip-optin` / `20261118T063852Z_f37ed4eb` | `fe9694b1` | 3 | pass |
| `trace-seam-c-flip-mutations` / `20261118T063937Z_2c328ebf` | `fe9694b1` | 1 | pass |
| `trace-seam-c-flip-byoxpc` / `20261118T064031Z_101b68ac` | `fe9694b1` | 4 | pass |
| `trace-seam-c-flip-waitcost` / `20261118T064309Z_220b09bf` | `fe9694b1` | 2 | pass |
| `trace-seam-c-flip-drift` / `20261118T064322Z_686fbe16` | `fe9694b1` | 19 | pass |
| `trace-seam-c-pre` / `20261118T065511Z_e69c3ad3` | `fe9694b1` | 3 | 2 fail, intended: 44 of 237 `test_input` rows, all `ordinary.*` refusal rows, because every block was still admitted and echoed; `accepted_input_contract` at the corpus example with `type_mismatch` |
| `trace-seam-new-default` / `20261118T065749Z_40eff132` | `081353c9` | 48 | pass |
| `trace-seam-new-optin` / `20261118T070128Z_91f503f5` | `081353c9` | 3 | pass |
| `trace-seam-new-mutations` / `20261118T070213Z_7baeb9b8` | `081353c9` | 1 (`witness_contract/order_barrier_mutations`) | pass |
| `trace-seam-new-byoxpc` / `20261118T070309Z_7276be62` | `081353c9` | 4 | pass |
| `trace-seam-new-waitcost` / `20261118T070549Z_3c01b3c0` | `081353c9` | 2 | pass |
| `trace-seam-new-drift` / `20261118T070602Z_eb457db7` | `081353c9` | 19 | 1 fail |
| `trace-seam-new-controls` / `20261118T071628Z_bc1fc28d` | `081353c9` | 2 | pass |
| `trace-seam-c-suites` / `20261118T071645Z_a03f77ee` | `081353c9` | 88 | pass; not a run of record |
| `trace-seam-new-drift-2` / `20261118T072413Z_322cefa6` | `081353c9` | 19 | pass |
| `trace-seam-c-suites-2` / `20261118T073509Z_9127bbf2` | `081353c9` | 88 | pass |

- `trace-seam-new-drift` stays a failure. `source_drift/generator_contract`
  failed for two reasons, both in the stage's account edits: a backticked
  symbol beside a file link in `runner/AGENTS.md` (an implementation defect,
  corrected), and the limits text edit (below).
- `trace-seam-c-suites` is not a run of record: three documentation files
  were edited while one of its cases was running. It passed and was repeated
  on the quiescent tree as `trace-seam-c-suites-2`.
- Reviewed exception: the six passing `trace-seam-new-*` runs preceded those
  documentation corrections. The delta is one sentence of `runner/AGENTS.md`,
  with `docs/limits.json` and `docs/LIMITS.md` restored to committed bytes;
  the limits readers among those cases read only `id`, `value` and `checks`.
  This is an applicability judgment, not a mechanical fact.
- `trace-seam-c-suites-2` covers `unit`, `integration`, `runner_unit`,
  `runner_abi_layout`, `failure_boundaries` and `runner_outcome_bad_request`
  by suite selector, `run_capture/controls` and the 59 default
  `runner_c_worker_harness` cases. Not run in this stage: the default
  battery, and the opt-in harness members `native_clock`, `native_pause` and
  `arm_wait`.

Old/new comparison, retained at
`trace-seam-new-controls/investigations/seam-equivalence/` with the first
stage's attachment and indexing scripts unchanged; it credits no case. The new
index holds 128 invocations in 37 cases over six runs (echo equal in 114,
empty in 6, absent in 6, no host reply in 2). All 104 scenarios of the old
index are in the new one. 103 are equal in component execution, intervention
observed, independent effects, fault rejection, identity, command accounting
and cleanup. One differs: `admission.nul-9` changed route as described above,
and its host reply is the same in the fields read. The 24 scenarios only in
the new index are all `test_input.*`. Outside the indexes: the retired
combined pair is old-only; `fractional_override` is on both sides with the
changed refusal code; 26 ordinary refusals and 2 unselected-substitution
submissions are new-only. Delivery differs by design: the 104 old records
carry the controls in the request block; 120 new records carry flags and 8
the controls object, each with delivered bytes equal to the ordinary request.

BYOXPC: eight sessions, each recording removal with `cleanup_retained: false`;
each service is absent from `gui/501` and its plist, staging, bundle, durable
state and private registry are absent; `runner list` and `runner reconcile`
were empty before, between and after.

Retained limits of the stage:

- The retired combined oversize pair (`worker_executable_path` with
  `validator_executable_path`) has no CLI/XPC coverage; its bounded,
  sanitized refusal is checked only by the direct-orchestrator pairs in
  `QueryAdmissionTests`.
- A live actor-form request with a control in its ordinary block now has a
  refusal check (`428a2049`). `witness_contract/actor_compositions` owns
  the separate contrast between the ordinary worker-timeout floor and
  the actor execution allowance.

The development generator check accepted the first limits edit. Two
`source_drift/generator_contract` fixtures then refused it because they
expected strict staging or release preflight to succeed with the frozen
guide. `11e93191` supplied publication-fresh fixture sources and a diverged
neighbour. `bd8144ea` corrected eight `docs/limits.json` texts. The `control`
fields belong to `worker_sentinel_wait`, `validator_io_wait`,
`phase_collection_wait` and `actor_collection_allowance`. The `counting`
fields belong to `worker_timeout_override_floor`, `validator_io_override_floor`,
`worker_fixture_delay` and `test_override_path`. The frozen guide retained
its earlier wording.

User duties noticed: the frozen guide documents the eight keys as request
data, lacks `test-input run`, and names `_test_overrides.*` controls in its
limit rows; release notes need the breaking change that `run` refuses those
keys.

## Case conversions — 2026-11-18

Status: the four selected conversions are landed and each was run when it
landed. No product source changed and no build ran; the signed app reported
`development:081353c9…` before and after. No run of record failed and none
recorded system sleep. Local managed development runs are under
`tests/out/runs/`, gitignored and subject to ordinary retention.

| Commit | Conversion |
| --- | --- |
| `4cb2f91b` | Survivor: the same-group descendant's lifetime is recorded without a verdict; `run_effects/aftermath_footprint` loses both lifecycle dependencies. |
| `47b455f1` | `runner_byoxpc/retirement_observations` completes as an informational observation. |
| `9bcefb24` | `witness_contract/worker_wait_pilot` reports the matched-pair improvement as an advisory judgment. |
| `79aa7dde` | Four inline assertion blocks report a failed envelope expectation as a case failure. |

### Survivor

`runner_exec_lifecycle/closed_streams_leader_exit` is default-selected and no
longer listed in `opt_in.include`. Its declared contract: observations
`descendant_lifetime` (informational), `exec_reply` and `later_file_effect`;
enforced judgments `truthful_exec_account` (finished, the worker facts, the
`leader_exit_and_eof` stop with cleanup `not_requested`, the leader's status,
the later step, envelope validity) and `later_step_effect`. The relation
between `leader_exit_and_eof` and `not_requested` stays enforced; the
requirement that the descendant be alive and answer after CLI completion is
gone.

The thread changed test authority only, so the first exercise of the revised
test against existing behavior is the converted case on the unchanged app:
`conv-survivor-b-01` / `20261118T164523Z_b5042bb6`, `complete`, history
`alive_acknowledged`.

Both histories were replayed through the old assertion and the new
observation as constructed inputs: the old assertion accepts the alive history
and rejects the prior-exit history ("descendant already exited"); the new
observation completes on both, as `alive_acknowledged` and
`exited_before_cleanup`.

A disposable control in a worktree made the checker end the descendant from
outside the product after the leader-exit event. That run
(`20261118T164629Z_a9581dea`) completed as `exited_before_cleanup`, with the
exit event 14.8 ms before CLI completion, and the reply still reported
`leader_exit_and_eof` with `not_requested`. This establishes the instrument's
sensitivity to a prior exit. It is not acceptance of a product that ends the
descendant itself: such a product, reporting it, is still refused at
controller admission while the relation stands, and the suite account says so.

The disappearance of the old obligation was followed on that control run
through the checker (completed), the dependency gate (a dependent was
admitted), the dispatcher (exit 0) and battery validation against an
independently captured contract (no problems). On the same route these still
reject, with the dependent blocked and battery problems reported: a stopped
descendant (unresolved, "a missing ping is not an observed exit"), a lost
cleanup observer (staging retained) and a wrong reply expectation
(`truthful_exec_account` unfavorable). Changed identity or group and a late or
missing watch reject in constructed classifier controls only, which each run
retains as `classifier-controls.json`.

`run_effects/aftermath_footprint` ran without either lifecycle predecessor
(`conv-aftermath-alone-01` / `20261118T165030Z_500cd5cd`, 3 pass). Mixed
selections: `conv-survivor-aftermath-01` / `20261118T165113Z_59a50b39` (4) and
`conv-survivor-suite-01` / `20261118T165155Z_50b06139` (5).
`runner_exec_lifecycle/worker_dies_during_exec` is unchanged.

Accounts regenerated through their owners: `docs/FOOTPRINT.md`,
`docs/ARCHITECTURE.md`, `docs/WORKER.md` and the topology files. The
`exec_child` process row has no scope text, so its Lifetime fact was restated
instead. Neither generator refused or touched the guide.

### Retirement and pilot

`runner_byoxpc/retirement_observations`: `conv-retirement-01` /
`20261118T170530Z_b487d082`, `complete` with one informational completion; all
48 requests `host_finished` and no client transport terminal. Runner list and
reconcile were empty before and after; bundle, plist, registry entry and
staging are absent. Only the `pass` credit disappeared, since no ratio was
ever enforced; the outermost boundary is the dispatcher run because the case
is opt-in.

`witness_contract/worker_wait_pilot`: `conv-pilot-live-01` /
`20261118T170914Z_5b935271` (4 cases with dependencies), `complete`: 168
accepted trials, none excluded or skipped, calibration established, none
overlapping sleep, on AC power with a one-minute load between 3.26 and 4.74
and another user's virtual machine holding about one core throughout. The
advisory judgment `candidate_improvement` is unfavorable with the detail
"improvement not established: this run compared no candidate". This was also
the first run through the migrated controls family as a dependency: the
family ran (232 items) and the pilot was admitted. A dry run in comparison
mode with the same app on both sides (`conv-pilot-dry-01` /
`20261118T170755Z_c9d79d1f`) completed with 14 pairs, unfavorable, with no
measurement credit. Matched pairs exist only in comparison mode; the
cataloged pilot has none. No verdict was enforced before, so `pass` became
`complete` and no obligation disappeared. Neither this nor the retirement
conversion supplies the survivor's reduction in enforcement.

### Bare assertions

Repaired paths: `smoke/pw_specimen_smoke.sh`,
`smoke/pw_specimen_smoke_standard.sh`, `runner_apply_isolation_v2/run.sh` and
`witness_contract/happy_path_baseline.sh`. No shared reader changed. In a
worktree with a constructed wrong expectation, the four cases were unrun
before the repair and `fail` after it, naming the expectation and its
`assertions.log`, with a neighbour case passing in each run; an unexpected
exception still leaves the case unrun. In the checkout: `conv-bare-main-01` /
`20261118T171334Z_14d81016` (4 pass) and `conv-bare-byoxpc-01` /
`20261118T171347Z_48a7c0da` (2 pass).

### Verification on the case-conversion tree

| Directory / run ID | Scope and result |
| --- | --- |
| `conv-final-lifecycle-01` / `20261118T171422Z_c9808b2a` | `runner_exec_lifecycle`: 5, ok. |
| `conv-final-run-effects-01` / `20261118T171448Z_2e7d6a06` | `run_effects`: 6, ok. |
| `conv-final-dispatcher-01` / `20261118T171527Z_4d6d867a` | `dispatcher`, `shell_helpers` with `dispatcher/pytest_controls`: 15, ok. |
| `conv-final-preflight-01` / `20261118T172141Z_7e6285e2` | The three release preflight controls: 3, ok. |
| `conv-final-drift-01` / `20261118T172842Z_e51a6c94` | `source_drift`: 11, ok. |

At `79aa7dde` the default selection listed 233 cases including the survivor;
`--all --list` showed aftermath depending only on its two controls. Reviewed exceptions: the
retirement run predates the pilot's catalog entry and the pilot run predates
the bare-assertion scripts; the sources each executed are byte-identical at
`79aa7dde`.

The conversions established the following limits on interpretation.

- The three converted cases report `complete` under `observation_reports` and
  `case_outcome_counts`, not in the legacy `counts`.
- A judgment has two values, so "not established" is recorded as unfavorable
  with its detail, and every pilot run outside comparison mode prints an
  advisory line. A third value would be a shared-reader change and is not
  made.
- Marginal value, without a redundancy claim: `leader_exit_and_eof` with
  `not_requested` is rejected by controller admission, by the independent
  consumer and by one assertion helper shared between the survivor and
  `closed_streams_continue`, so the last two are not independent rejections.
  The survivor's distinct observation is leader exit with a same-group
  descendant. The dispatcher's `pilot_advisory` control and the live pilot
  share the reader but not the conclusion code.

### Follow-up repairs — 2026-11-18

Three points the conversions thread reported were repaired before the product
threads, each in its own commit, with no build-input change.

| Commit | Repair | Run of record |
| --- | --- | --- |
| `8a7596b5` | The pilot driver's advisory conclusion has a permanent constructed control: `tests/fixtures/dispatcher/pilot_conclusion.py`, run in its own process inside `dispatcher/controls`, ten rows with literal expectations (favorable, worsening, no candidate compared, dry run, spread not met, a withheld verdict, an uncovered cell and the reader's real equal-pair output). | `follow-dispatcher-01` / `20261118T175125Z_5925a41b`, 15 pass with `dispatcher/pytest_controls`. |
| `6bab97ee` | The survivor checker's "CLI exit event missing" refusal was an assertion before any sample existed and could not be reached by a classifier input. It is now a classifier refusal with two constructed rows (sixteen in all); the checker still samples and retains the descendant. | `follow-lifecycle-01` / `20261118T174948Z_4d177e6a`, 4 pass and 1 complete. |
| `7b8f1f46` | The retirement summary published an always-zero `host_ok` beside outcomes labelled `host_finished`. The always-present key is now `host_finished`; nothing else read the old key. | `follow-retirement-01` / `20261118T175016Z_29b52e15`, complete, twelve finished hosts in each gap; runner list and reconcile empty before and after. |

The conclusion control is not in the pilot controls family, whose count stays
232: importing the driver inserts the live case's directories into the module
path and loads about twenty-five modules, which the family would have to
declare as sources. A seeded fault in a worktree (the driver reporting
favorable when no candidate was compared) failed `dispatcher/controls` on the
`no_candidate_compared` row. A worktree control that stops the CLI failed the
survivor case with the new message and settled its cleanup.

`follow-drift-01` / `20261118T175652Z_823ae4d3`: `source_drift`, 11 pass. It
is also the first drift run that reads `tests/PYTEST-EVIDENCE-PLAN.md`, a plan
written at the maintainer's request for the storage and reading cost of
pytest family evidence; no diagnostic names it.

Because `6bab97ee` changed the checker's classification code, the survivor's
three disposable live controls were repeated in a worktree at `7b8f1f46`, with
one patch anchor re-fitted to the moved line and no tracked change:

| Control | Run ID | Result |
| --- | --- | --- |
| Descendant ended from outside the product | `20261118T181002Z_a854ac82` | Completes as `exited_before_cleanup` (exit event 16.3 ms before CLI completion); the reply reports `leader_exit_and_eof` with `not_requested`; both enforced judgments favorable; a dependent ran; dispatcher exit 0; battery validation against an independently captured contract reports no problem. |
| Stopped descendant | `20261118T181006Z_3ab52e9a` | Fails unresolved ("a missing ping is not an observed exit"); dependent blocked; battery validation reports problems. |
| Lost cleanup observer | `20261118T181013Z_3f30757d` | Fails with staging retained; dependent blocked; battery validation reports problems. |

The outcomes equal those at `4cb2f91b`. The worktree and its runs are removed;
the receipts are summarized in gitignored scratch.

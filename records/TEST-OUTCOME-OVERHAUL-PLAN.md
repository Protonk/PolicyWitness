# Test outcome overhaul plan

## Purpose and boundaries

PolicyWitness treats tests as part of its documentation. Their assertions,
names, messages and reported outcomes describe what the instrument establishes.
Tests also exercise an authority that ordinary prose does not: they can prevent
a product change from being accepted. That authority needs a justification
beyond the existence of an assertion. An implementation detail, historical
accommodation or mistaken inference can otherwise become an architectural
obligation simply because changing it makes a test fail.

This plan develops a substantial but bounded change to that regime. Separate
three questions wherever the selected work needs them:

- **Observation:** What happened, through which instrument, and what evidence
  supports the account?
- **Judgment:** Which proposition is evaluated against that evidence, under
  which conditions, and with what result?
- **Enforcement:** Why does that judgment have authority to block this change,
  build or release?

A useful test can continue to tell us which processes survived, which helper
invocations occurred, which bytes were retained, or which classification was
produced after it stops requiring that particular behavior. It must still be
possible to distinguish a trustworthy observation from a broken experiment.
Withdrawing product enforcement does not withdraw the obligation to execute,
account for and clean up the promised experiment.

The three companion plans have distinct responsibilities:

| Plan | Responsibility and dependency |
| --- | --- |
| [TRACE-MANAGEMENT-PLAN.md](TRACE-MANAGEMENT-PLAN.md) | Owns assessment and disposition of trace findings, product judgments, compatibility decisions and the guide freeze. This overhaul consumes selected decisions and returns evidence about their implementation. |
| [TRACE-ACCEPTANCE-PLAN.md](TRACE-ACCEPTANCE-PLAN.md) | Supplies the reasoning for evaluating independently maintained judgments and change costs. Its change rehearsals inform the assessment here; they are not another completion gate. |
| This plan | Owns the proposed test-authority and reporting capability, selected assertion and wording corrections, two bounded pytest migration cohorts, executable test-seam implementation and caller migration, and verification of preservation and relinquishment. |

The management plan's
[combined sequence](TRACE-MANAGEMENT-PLAN.md#working-the-three-plans-together)
owns the order in which work shared by the three plans settles and the
boundaries at which broad runs happen. The stages and verification below state
this plan's own obligations within that sequence.

The management plan's
[editorial freeze and implementation authority](TRACE-MANAGEMENT-PLAN.md#guide-freeze-and-public-commitments)
apply here. Leave the guide and its explanatory inputs untouched. Within the
selected subjects, the implementing agent may change signed components,
contracts, representations and product behavior on their merits. A changed
test classification alone cannot repair a defect or withdraw a commitment;
the substantive product decision belongs to management. Describe and verify
the resulting technical responsibilities without creating substitute guidance.

This is a planning handoff, not implementation or a fresh acceptance run. Build,
release, provenance, ownership and cleanup obligations remain independently
enforced. The management plan owns the development/publication distinction;
this plan supplies the necessary reporting and acceptance-reader support.
Seam migration and justified product changes are distinct from relinquishing
test authority and cannot substitute for either pytest cohort.

## Investigation basis

The source inspection for this plan used revision
`9714e451c270ef377d28aa460cdd8e79a9d5f96a`. It traced catalog selection, shell
finalization, dispatcher reconciliation, pytest collection and reporting,
portable release evidence, selected Python checkers, Rust and Swift wrappers,
and the observation cases discussed below. No catalog case, build, native
experiment or release procedure was executed for this plan.

The settled seam and dependency decisions use source inspection at `3d3f8e65`, tracing
`test-input read`, command definitions, ordinary run dispatch, runner override
decoding, caller combinations, aftermath fixture ownership, generation/build
checks and release-battery routing. No native case was executed; the source
traces settle scope and handoff decisions, not runtime equivalence.

The earlier [test-work survey](tests/TEST-WORK-SURVEY-REPORT.md) describes
`31b81951c9c8c4124089aa4dd342b2b63c0a86de`. Its 235 cases and Python group
counts are historical. Its case reading and assertion traces are useful
starting points, not current execution evidence: the survey ran no cases and
did not consult retained results. Its observations about asserted limitations,
batch granularity, independent oracles and failures recorded as harness errors
remain useful questions independently of the trace review.

A current, bounded source inventory found 283 concrete catalog entries and
182 Python files under `tests/suites/`. Only the exec-control module imports
pytest, and only `runner_c_worker_harness/exec_control_states` declares that
engine. Python work includes unittest groups, script-driven scenario tables,
live observers and instrument libraries; file counts are not test counts or
execution coverage. This inventory and the readings below support cohort
selection, without treating the old survey as today's catalog.

The [trace review](DOCUMENTATION-TRACE-REVIEW.md) retains its deliberately broad,
overlapping findings. Its constructed, steered, native and source-supported
claims keep those qualifications. Development artifacts referenced there may
be temporary or gitignored and available only in the originating checkout;
check availability before crediting or reusing them. Source inspection here
does not reproduce those executions.

## How authority works now

The present machinery already separates some responsibilities, but neither
engine success nor a case's `pass` has one uniform evidential meaning.

| Boundary inspected | Present behavior and consequence |
| --- | --- |
| [Shell helpers](../tests/lib/testlib.sh) and [case helpers](../tests/lib/case.sh) | Finalizers write `pass`, `fail` or `skip`, a terminal event and a report. Logged commands and Python checkers turn nonzero exits into failed cases. The final message belongs to the case; it can describe assertions, completed observations or both. |
| [Dispatcher](../tests/lib/suite_run.py) | Reconciles unique selected cases, events, reports, interpreter identity and command exits. Harness errors and artifact integrity can fail a run independently of a reported pass. Missing prerequisites or reports leave unrun selections. Ordinary product assertion failures can also produce `suite_exit`; that diagnostic alone does not classify their cause. |
| [Python control receipts](../tests/lib/receipts.py) | Already distinguish `complete` from `ok` and retain per-control failures, subtests, registered inputs and direct commands. The unittest runner and shell wrapper still turn unsuccessful assertions into gating failures. Registered snapshots do not establish every file read, and command receipts do not count every descendant. |
| [Pytest engine](../tests/lib/pytest_engine.py) and [family adapter](../tests/lib/pytest_family.py) | Preserve setup/call/teardown, incomplete execution, command references and ownership. Any unsuccessful phase makes the item fail; family success requires complete accounting, zero engine exit and all items passed. A native-command timeout, cancellation, failed launch or forced group settlement is consequential. No advisory or verdict-free product result exists at this boundary. |
| [Rust unit wrapper](../tests/suites/unit/run.sh) and [integration wrapper](../tests/suites/integration/run.sh) | Credit whole Cargo batches from their command exits and logs. An individual Rust assertion cannot become non-gating by changing only the parent report. Ignored receipt replays are explicitly invoked elsewhere; ignoring another test would remove execution, not create an observation. |
| [Swift TestKit](../runner/Tests/PWRunnerCoreTests/TestKit.swift) and [runner wrapper](../tests/suites/runner_unit/run.sh) | Thrown failures increment the block failure count. The wrapper rejects nonzero exit, internal `SKIP`/`FAIL` lines and a missing summary, and performs additional reader replays. Missing equipment can therefore appear as a failed block. There is no informational block contract to assume already works. |

The [current output contract](../tests/README.md#output-contract-testsout)
counts legacy reports separately from all parent cases. `run.json.counts` and
`reports` exclude pytest families and say so through `counts_scope`;
`case_outcome_counts` includes all parents. Nested pytest items have their own
account. `completion.completed` currently counts pass or fail reports, not
favorable results; incomplete families contribute to the legacy unrun count
while exposing their more precise execution and accounting states.

The survey's assertion-to-unrun concern is still relevant. For example, current
smoke, apply-isolation-v2 and witness-baseline scripts retain bare Python
assertion blocks under shell `errexit`. An assertion can end the command before
its terminal report. Reconciliation rejects the run, but an aggregate reader
cannot recover an ordinary assertion verdict from that missing report. Correct
the selected paths as part of this work; do not solve this by treating arbitrary
exceptions as product judgments.

Two observational precedents establish different things:

- [BYOXPC retirement](../tests/suites/runner_byoxpc/README.md) makes 48 requests
  at declared gaps, retains host outcomes separately from transport terminals,
  and requires no success ratio. Missing generation exits, invalid envelopes,
  interrupted logging or watchdog intervention make the experiment incomplete;
  owned service removal must also be verified. Its shell still reports `pass`.
- The [worker-wait pilot](../tests/suites/witness_contract/check_worker_wait_pilot.py)
  rejects missing scheduled receipts, blocking reader results, insufficient
  declared coverage, invalid required calibration, changed executables and
  unsettled cleanup. It does not require a favorable comparison verdict.
  Its reader reports improvement, worsening, uncertainty and exclusions, while
  the shell reports a passing case. A dry run establishes mechanics only.

These are useful starting instruments, not existing implementations of the
desired aggregate distinctions. Conversely, the exec survivor characterization
below requires the observed limitation to persist despite describing itself
as observational.

## Meaning before reporting vocabulary

Support three arrangements in the selected work. These are semantic distinctions
to preserve, not a predetermined enumeration or file format:

| Arrangement | What is evaluated | Effect on acceptance |
| --- | --- | --- |
| Enforced judgment | A stated proposition against adequate evidence. | An unfavorable result blocks acceptance for the scope that authorizes it. |
| Advisory judgment | A stated expectation against adequate evidence, retaining favorable, unfavorable or unestablished conclusions as applicable. | An unfavorable product judgment is visible but does not itself block acceptance. Required execution and evidence validity still matter. |
| Informational observation | An account of behavior, with evidence and limits, without an expected product value. | Completing the promised observation contributes no passing product assertion. Failure to obtain valid promised evidence remains consequential. |

Informational work is not `xfail`, a skip, a caught assertion, a warning emitted
after discarding a failure, or an assertion whose expected value follows the
implementation. Remove the selected correctness proposition from the instrument,
while preserving the checks needed to trust what it reports. Advisory work
retains the proposition and its result; informational work has no such verdict.

Separate the instrument's validity from the product facts it records. Malformed
product output can be valid evidence of a product failure; a truncated harness
receipt is a failure to establish the promised observation. A deliberately
malformed input in a rejection control is not broken test equipment. State
which evidence each selected experiment promises so these distinctions are
decidable. The retirement case, for example, currently promises validated
envelopes; changing that promise would be a separate scope decision, not a
consequence of relabeling its result.

Keep required prerequisites, observation identity, command completion,
accounting, bounds, required evidence fields, artifact integrity and resource
settlement consequential. Unknown process ownership is not an observed absence.
An optional measurement may remain explicitly unavailable only where the
experiment declared it optional; it cannot supply the omitted conclusion.
Withheld judgments and incomplete experiments must remain distinguishable.

Apply authority at the proposition's scope. A single existing case may contain
an enforced public guarantee, a characterization of a mechanism and cleanup
checks. Separate those responsibilities in the code and report, or split the
case where that makes the experiment clearer. Do not mark its entire assertion
body advisory. Existing, untouched cases remain enforced under their present
contracts; this plan adds no global switch to ignore their failures.

Choose authority before examining the result. For each conversion, identify the
old assertion, its claimed justification, the narrower observation retained and
the reason for withdrawing or preserving its enforcement. A known bad result
cannot choose its own reporting mode. Selection or collected family evidence
must bind the intended authority sufficiently that deleting a failing judgment
or changing a result field cannot make the run acceptable.

A useful justification identifies the public commitment, evidence-integrity
requirement or explicit product decision the assertion protects. Its scope must
match that justification. Another case may already enforce the same proposition,
but assess whether this test supplies independent scrutiny before treating it
as redundant. Neither duplication nor a long history automatically settles
whether to keep its authority.

Advisory status means only that this judgment does not automatically block
acceptance. Its evidence may justify investigation, a product correction, a new
enforced requirement or no change. Use ordinary substantive engineering judgment
within the authorized scope; do not add advisory-specific escalation, triage or
disposition machinery. Apparent severity or invasiveness does not presumptively
require human review. Ask only when authority or information is genuinely missing.
A separately enforced obligation remains enforceable when an advisory observation
supplies evidence of its violation. Any subsequent enforcement decision applies
to subsequent declared evaluations; preserve the original run and its producing
semantics rather than retroactively changing its status.

## Choose the smallest reporting mechanism through a bounded comparison

Before implementing the adapter, compare two concrete arrangements using the
same small mixed selection: one enforced judgment, one unfavorable advisory
judgment, one completed informational observation, and one broken observation.

One arrangement could extend existing terminal reports with explicit experiment
and judgment information. Another could retain engine phase results and attach
a required, narrowly scoped observation/judgment account that the dispatcher
reconciles. The latter is only viable if the account is part of acceptance and
terminal reporting, not an optional artifact beside a misleading pass. Compare
their behavior under missing records, contradictory evidence, cleanup failure
and release rereading before selecting names and formats.

Prefer reuse of existing selection, reports, receipts and ownership boundaries.
Do not add a second case registry, a generic assertion interpreter or a universal
cross-language result protocol. A shell finalizer and a pytest reporting hook
may express the same distinction differently. Any new adapter must explain what
existing responsibility it replaces and which additional decisions it creates.

Pytest's own successful call phase can mean that an observation function ran
correctly. It cannot by itself mean the product satisfied an expectation.
PolicyWitness's item display and aggregates must make that distinction even if
pytest internally reports a successful phase. Avoid implementing advisory work
by blanket suppression of `AssertionError`: that would also suppress invalid
evidence and existing independent controls. Record the selected judgment
explicitly after validating its inputs; unexpected exceptions still fail.

Native batches need no general conversion in this iteration. Correct selected
Swift and Rust assertions in their current runners. If a later selected native
characterization needs non-gating output, either expose a bounded observation
receipt through its existing driver or add a narrowly tested reporting path.
Do not relax Cargo's exit, TestKit's failure counting, or the wrapper's log
checks for a whole batch to accommodate one observation.

The decision produced by this comparison belongs in this plan's implementation
account, with the rejected alternative and material tradeoff. It is not a new
permanent vocabulary design exercise.

## Aggregation, dependencies and release acceptance

Make these reader questions answerable from terminal output through retained
evidence: Which selected experiments completed? Which judgments were evaluated?
Which judgments were unfavorable? Which had enforcement authority? Which
required evidence or cleanup failed?

| Surface | Required distinction |
| --- | --- |
| Case or family report | Promised and completed observation scope; evidence references; evaluated proposition and authority where one exists; execution, validity and cleanup failures independent of product verdicts. Mixed cases must reveal their separate responsibilities. |
| Run summary | Complete selection accounting, blocking failures, advisory results and informational completions without counting the last two as passing product assertions. Preserve parent versus nested-item scope. Legacy batch passes are case passes, not a known count of assertions. |
| Terminal output, including quiet mode | Non-gating unfavorable judgments and observation failures remain visible, with artifact paths. A run permitted to continue is not described as every product expectation having passed. |
| Retained artifacts | Raw observations, evaluated expectations, authority and producer semantics remain attributable to the run. Partial evidence survives a later assertion, finalizer or publication failure. |
| Release acceptance | Every required experiment completed with valid evidence and settled resources; every authorized enforced judgment satisfied; non-gating results explicitly summarized. Signing, app identity, unchanged bytes and portable evidence obligations remain independent. |

Do not manufacture an assertion count for legacy reports or add parent and
nested-item counts together. If compatibility requires retaining a legacy
count field, define its scope explicitly and keep converted informational work
out of any count represented as passing product judgments. A reader must not
need to inspect an optional log to discover that distinction.

The [release battery validator](../tests/lib/release_accept.py) currently
requires every parent status to be `pass`. The
[execution contract](../tests/lib/execution_contract.py) additionally requires
all family items and phases to pass and every item to reference a native command.
Those rules cannot accept the proposed distinctions or pure Python items
unchanged. Revise them together with the dispatcher, supported by independently
captured source/selection expectations. Evidence validity must not be inferred
solely from a new result's claim to be informational.

Dependency admission currently asks whether a predecessor passed. For a
converted dependency, distinguish needed evidence or equipment from the
predecessor's entire judgment. The aftermath edge is settled by source reading:
[aftermath_footprint.sh](../tests/suites/run_effects/aftermath_footprint.sh) builds
its own bridge, helper and observer; `check_aftermath_footprint.py::main` creates
its own `ActorHostFixture`, and `observe_case` starts its own
[HeldWorkload](../tests/lib/footprint_workloads.py), registers generation-qualified
exit observers and writes local receipts. No survivor artifacts, fixture or
verdict are consumed. Its timeout-worker observations concern its own invoked
client-timeout experiment, not a descendant surviving normal exec completion.

Remove `runner_exec_lifecycle/closed_streams_leader_exit` from the aftermath
case's `depends_on`; do not replace it with a completion-only dependency.
The same trace establishes no dependency on `worker_dies_during_exec`, so remove
that inherited lifecycle edge too without changing that case's independent
checks or default selection. Retain the observer/checker control prerequisites.
Make the converted survivor observation explicitly default-selected: this keeps
its evidence in the default and extracted-app batteries without using aftermath
to force a favorable survival judgment. Update the catalog and suite accounts
with these changes.

Verify selection and execution of aftermath without either lifecycle predecessor,
then mixed selections with the informational survivor. A valid prior-exit
history must complete through checker, dependency admission, dispatcher and
battery acceptance; missing observations and unsettled cleanup still fail.
The worker-death case concerns abnormal worker termination and remains a
separately justified check, not a replacement normal-completion survival rule.

Keep the producer-bound approach to archives in
[release_runs.py](../tests/lib/release_runs.py) and the
[release procedure](../docs/SIGNING.md#portable-test-evidence-and-release-cleanup).
Determine the necessary result/evidence version boundary during implementation;
do not prescribe a new schema number here. Historical failures remain failures
under their producing contract, and assertion failures remain distinguishable
from harness failures to the extent the old evidence permits. Old ambiguous
evidence remains ambiguous. Do not rewrite retained runs, reinterpret them with
today's authority choices, or loosen existing refusals of unsupported archive
formats. New semantics require new evidence. Retention and publication must
still reject missing required accounts and unresolved ownership independently
of any advisory verdict.

## Selected conversions and an instrument for architectural change

### Relinquish the required same-group survivor

The selected primary enforcement reduction is
`runner_exec_lifecycle/closed_streams_leader_exit`. Its
[checker](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py)
observes initial peer identities and process groups, closes both streams, exits
the leader and waits for the CLI. `observe_survivor` then requires the descendant
to remain alive and answer a ping with its original identity and group. Later
cleanup releases it and requires its exit. The final shell message explicitly
credits a surviving descendant. An implementation that stops that descendant
can therefore fail the case even though the suite describes survival as a
current observation limit, not a desired containment rule.

Convert to a verdict-free account of the descendant's post-completion lifetime.
Keep independently registered exit events, generation identity, stream-close
acknowledgments, the later file effect, raw CLI output and separate test cleanup.
Retain justified checks of truthful public evidence and promised later effects
as enforced judgments, visibly separate from the lifetime observation. Examine
fixed expectations such as the no-request record so they do not indirectly
reintroduce the removed architectural requirement; any public-meaning issue
goes through the management plan before changing that expectation.

The assessment of remaining obligations belongs to the management plan,
which takes it early although no trace finding has it as its subject. Give it
the passages that describe descendant lifetime as well as the test. Generated
accounts cite this case as support. FOOTPRINT rows fa5 and fa6 cite the
checker through [footprint.json](../docs/footprint.json) and describe its
`main` as an assertion of the survivor observation. A WORKER resource row
credits the case
with establishing same-group survival, and [COVERAGE](../tests/COVERAGE.md)
describes it. Those support descriptions change with the conversion. Correct
them through their owners in the same change, and inspect the generated
destinations for the freeze.

The revised instrument should distinguish these plausible arrangements:

| Arrangement under examination | What the instrument retains without preferring it |
| --- | --- |
| Leader and streams finish while the descendant continues | Original descendant identity and group, acknowledged post-completion ping, the observed interval, later file bytes, and the distinct release/exit caused during test cleanup. |
| Product completion also ends the descendant | The original generation's independently observed exit before test cleanup, its timing relative to CLI completion, any available termination evidence, later file bytes and the returned exec account. An exit alone does not identify who caused it. |

Register observers before the triggering action. Treat a ping/exit race as a
bounded observation to resolve using those events, not permission to infer
death from a failed ping or a missing PID. If the promised classification cannot
be established, the experiment is incomplete. Cleanup must work for both
already-exited and still-live descendants and preserve uncertain ownership.

First replay constructed histories through the new observer interpretation,
then exercise the existing implementation and a disposable, explicitly
identified control that ends the descendant before the sample. The control
establishes the instrument's sensitivity to the alternative; it is not evidence
that a future production design is implemented. Confirm that the old survival
assertion rejects the latter history and the new informational branch completes,
while a missing exit record, changed identity or failed required observation
still prevents acceptance. Keep process/effect observations ahead of JSON
interpretation and cleanup as in the current case.

This conversion must remove actual blocking authority, including at dependency,
default-battery and acceptance boundaries. The selected lifetime proposition is
observational; management assesses the remaining truthful-evidence and effect
obligations, rather than reopening survival solely because old prose or tests
required it. The adjacent `worker_dies_during_exec` concerns abnormal worker
death and remains outside this authority conversion. Verify that no alternate
fixture or summary reconstructs the normal-completion survival requirement.

### Surface existing observational and advisory work honestly

Convert BYOXPC retirement's experiment completion to informational reporting,
keeping its sequence, valid-envelope requirements, generation observations,
watchdog and session-removal enforcement. This corrects aggregate meaning; it
does not count as relinquishing an existing reliability assertion, since the
case already requires no favorable success ratio.

Use the worker-wait pilot's existing matched-pair conclusions to exercise
advisory reporting. A valid comparison that does not establish improvement, or
establishes worsening, must remain non-gating where it is non-gating today.
Separate raw counts and timings without a preference from evaluated improvement
propositions. Exclusions, missing calibration and insufficient required coverage
retain their own consequences; a dry run cannot gain measurement credit.
Do not quietly convert the pilot's staged-process lifetime or cleanup checks
alongside its performance reporting. Assess any such assertion separately.

These conversions deliberately exercise shell and pytest-facing aggregation
without migrating every live instrument to pytest. They supply useful evidence
about reporting but cannot substitute for the survivor case's real reduction.

## Absorbing trace findings and correcting what tests say

Use the management plan's claim, boundary and consequence assessment. Before
implementation, record the selected finding references there, its present
judgment and the authorized test response. This plan needs only the concrete
handoff and verification references, not another DT inventory or competing
disposition table. Later evidence returns to the same assessment owner.

Possible responses include correcting an expected result; correcting a name,
message or coverage claim; narrowing enforcement; retaining an advisory
expectation; retaining only an observation; retiring an uninformative test; or
retaining its present enforcement with an adequate justification. These are
choices for a particular claim, not compulsory bins for every finding. A
wrong expected value may need correction while its enforcement remains useful.
A genuine public violation calls for a product decision, not a status change.

### DT-53/132: reader acceptance and credited lifecycle coverage

The review distinguishes general consumer acceptance from the lifecycle oracle's
claim checks. DT-53 used constructed JSON edits; DT-132 extends the result to
byte-consistent frames through Rust and Python. It also identifies deliberate
reader responsibility, rather than an unmet promise that the general consumer
must validate every claim. Its counts of affected callers belong to that
snapshot and must be re-established for selected current callers.

Start from [consumer.py](../tests/lib/consumer.py),
[lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py), their adapters and the
[failure contract](../tests/FAILURE-PROPAGATION-CONTRACT.md). Follow callers that
credit lifecycle validation, not every caller that checks an envelope. For
selected claims, either invoke the responsible independent check, add the
specific missing assertion, or narrow what a passing case and its published
description claim. Do not broaden the consumer automatically or count shared
predicates as independent corroboration.

Verification must retain an accepted baseline beside a missing `final_status`
and a wrong value beside unchanged raw status. Use a consistent binary capture
when claiming whole-envelope behavior. Show which reader rejects which
proposition, which diagnostic the test asserts, and whether the public result
changes. A zero process exit or an empty consumer error list cannot receive
credit for checks another reader owns.

### DT-63/124/125: erasure at last use versus teardown

The current [ActorAuthorityTests](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift)
comment credits last-transfer erasure while reading a final post-teardown
`erased` flag. DT-124 supplies a native internal-driver contrast in which that
final flag is identical although the last transfer did not run. DT-125 qualifies
the worker-side coverage: the boundary observer accumulates clearing results,
but a separate synthetic terminal fixture counts erases and would distinguish
an omitted call by source inspection. The review did not execute that mutation.

Correct the literal comment and credited support now within the permitted
scope. Keep any justified final-state check as a final-state check. If the
last-use commitment needs test support, propose an observation before teardown,
using separately prepared nonzero storage and a control that omits only the
last-use clear while retaining final cleanup. Inspect
[extension boundary checks](../tests/suites/witness_contract/check_extension_boundaries.py)
and [terminal erasure checks](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py)
before claiming a gap or adding another observer. Distinguish flags, scanned
bytes, call counts and bounded timing intervals. This is principally an
assertion-scope repair and possibly stronger independent evidence, not a reason
to demote a meaningful erasure guarantee.

### Transport and receipts: investigate enforcement without choosing the product

The transport findings DT-31/32/42 and DT-113–119 challenge reachable states and
fallback meanings. Current [run-flow tests](../controller/src/run_flow.rs),
including `actor_fallback_uses_held_policy_objects_before_host_mode_admission`
and `actor_fallback_preserves_resolved_inputs_order_and_transport_evidence`,
exercise helper invocations and independently authored expected inputs.
Before relaxing them, distinguish byte/input preservation and honest attribution
from the decision to invoke the helper at all.

These Rust tests live in `controller/src`, which is a
[build-contract input](../docs/build_contract.py). Correcting only a test's
name, message or comment there changes the development contract, and the app
must be rebuilt for the tree and the app to agree. Hold such edits until after
the management plan's instrument checkpoint and land them with their thread.
Swift tests under `runner/Tests` are outside those inputs.

Rehearse removing automatic actor fallback while retaining ordinary and
standalone compilation. A useful observation would retain the submitted form,
admitted transport result, actual helper-call sequence and input bytes, captures,
field presence and relevant side effects. It could show invocations disappearing
without requiring either call count. Preserve any independent input-provenance
and transport controls still justified when calls occur. Assess current product responsibilities and compatibility before selecting the
change under management's authority. The rehearsal informs that decision; it
does not make this the mandatory initial enforcement reduction.

For receipts, DT-95–104 and DT-134 distinguish host qualification, constant-label
admission and downstream inference. The run-flow test
`compiled_profile_labels_determine_the_public_admission_outcome` enforces label
admission, not bytecode authenticity or request association. Correct any stronger
credited claim; retain its present enforcement unless a separate product
assessment justifies changing that admission rule. Rehearsing capture despite
failed application must account for both the application's success gate and
clean-completion gate in [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift).
Changing a test outcome cannot settle either commitment.

For every selected correction, update the assertion, literal failure and success
messages, case name where misleading, catalog description, suite README and
affected coverage/support accounts together. Preserve references when an ID
changes and update selectors/dependencies deliberately. Review
`tests/COVERAGE.md`, `tests/FAILURE-PROPAGATION-CONTRACT.md`, change-verification
guidance and authored contract support where the selected claim reaches them.
Use the owning generators and inspect their destinations for the freeze. These
edits are part of behavioral remediation, not later editorial cleanup.

## Migrating executable test seams

The management plan owns the
[settled eight-control boundary](TRACE-MANAGEMENT-PLAN.md#bounded-test-seam-migration),
ordinary/experimental admission and product responsibilities. This plan owns
implementation, caller migration and experimental equivalence. The selection
follows actual co-use rather than whole catalog families; no new inventory or
scope-selection phase is required.

### Selected seam callers

At `3d3f8e65`, the following source paths supply the selected controls. Migrate
the selected invocations and their command/evidence handling, not every scenario
in the containing file. Shell wrappers and BYOXPC variants that invoke the same
checker follow that caller. Confirm these references have not changed before
editing, without reopening the settled scope absent new co-use evidence.

| Experimental use | Caller and combination supporting selection |
| --- | --- |
| Pre-ready and native-argument refusal | [check_pre_apply_failure.py](../tests/suites/witness_contract/check_pre_apply_failure.py): pre-ready hang plus worker timeout; invalid post/pre delay, self-signal and slot controls. Its separate missing-worker substitution stays outside. |
| Worker deadline, in-flight attempt and grace | [runner timeout checker](../tests/suites/runner_outcome_runner_timeout/check.py), also called by `runner_use_c_worker/worker_timeout_ms_honored`; [check_attempt_in_flight.py](../tests/suites/witness_contract/check_attempt_in_flight.py): worker timeout alone or with post-apply hang. |
| Publication and termination | [check_killed_before_publication.py](../tests/suites/witness_contract/check_killed_before_publication.py): slot kill plus worker timeout; `check_worker_sparse.py` and `check_worker_termination.py`: post-apply hang plus self-signal. `check_extension_directory.py` uses slot kill, including its `actors_byoxpc` caller. |
| Actor applicability | [check_actor_compositions.py](../tests/suites/witness_contract/check_actor_compositions.py): post-apply delay and paired ordinary/actor timeout applicability. Keep the actor execution allowance independent. |
| Launch, ready-byte and reservation observations | `runner_exec_inheritance/launch_inventory.py`, `runner_ready_byte_resilience/run.sh`, and BYOXPC `single_use.py` / `bad_neighbor_claims.py`: pre-ready or post-apply delay. Direct-client requests in these callers must use explicit experimental admission too. |
| Validator faults and collection deadlines | `runner_validator_failure/check.py` and `check_signal.py`; [validator no-reply checker](../tests/suites/runner_outcome_validator_no_reply/check.py): replacement plus I/O deadline; [check_phases.py](../tests/suites/witness_contract/check_phases.py): replacement plus total deadline, including `actors_byoxpc`. |
| Ordering and comparison | [check_ordering.py](../tests/suites/witness_contract/check_ordering.py), its shell callers and mutation controls; `check_comparison_matrix.py`: replacement with I/O deadline for the stub and worker timeout for the FIFO experiment. Preserve the independently authored matrix, including frozen guide inputs; the invocation adapter separates its control values from the ordinary request. |
| Identity, strings and path queries | `check_dossier.py` and its BYOXPC caller, `check_diagnostic_transport.py`, `check_path_queries_integrated.py`, and `failure_boundaries/check.py`: selected validator substitution and its admission/failure contrasts. Their distinct worker substitutions stay outside. |
| Held-workload instruments | [footprint_workloads.py](../tests/lib/footprint_workloads.py)::HeldWorkload supplies validator replacement to `check_held_phase_footprint.py` and `check_aftermath_footprint.py`, including disposable actor hosts. Adapt the shared command path and its constructed CPU controls together. |
| Request and evidence controls | `runner_outcome_bad_request/contract.py` has a live self-signal invocation; request examples, current shape/generator controls and evidence readers carry the affected admission/echo claims. Update current claims and controls; keep historical response fixtures under their original semantics. |
| Internal and lower-level controls | `runner/Tests/PWRunnerCoreTests/{RequestContractTests,QueryAdmissionTests,ServiceAdmissionTests,PhaseProtocolTests,OrderingTests}.swift` and controller dossier tests exercise decoding, bounded refusals, service admission or direct orchestration. Update current boundary expectations and experimental context while retaining independent framing, sanitization and driver checks. Constructed full-shape records in `ReplyFailureTests.swift` do not establish ordinary admission. |

The worker controls form one co-use group through timeout, delay, signal and
slot publication; the validator group links replacement with both deadlines.
The initial three fields alone would split these experiments across interfaces.
No inspected live CLI/client invocation combines a selected control with
`worker_executable_path` or `actor_equipment_executable_paths`; separate rows in
one checker do not make such a combination. Constructed decoder/reply records
and direct internal admission tests do contain mixed fields. Preserve their
independent checks through internal construction or revised boundary controls,
without treating those records as evidence that a mixed public execution route
is needed. The eight-field selection is the smallest coherent closure of the
initial live uses, not a mandate to migrate all seams.

### Specify the route and admission

Implement the management plan's `test-input run REQUEST` boundary and eight
explicit control flags. Preserve `test-input read` as publication-only. Trace
[CLI dispatch](../controller/src/cli.rs), [test input handling](../controller/src/test_input.rs),
[run orchestration](../controller/src/run_flow.rs), client transport, host
admission and native planning. Reuse orchestration and pass explicit experimental
intent outside the ordinary request. Ordinary submissions reject selected legacy
keys even through the lower-level client/host; experimental submissions reject
mixed legacy controls. Internal tests may still construct driver inputs directly,
but that does not demonstrate public admission.

Retain absent/default, invalid and unreached control contrasts. Preserve the
accepted numeric domain and the boundary that rejects an out-of-range native
argument; flag parsing must not silently replace that experiment with a CLI
usage refusal. Keep malformed CLI syntax as its own control. In particular,
ordinary `timeoutMsForCWorker` floors the supplied timeout while
`ActorOrchestration` uses `PWActorLimits.executionMs`; delay/signal/slot controls
reach both worker forms. Keep `timeout_applicability_specimens`' independently
expected difference. Requested control presence is not proof of intervention.

Use the [interface definitions](../controller/interface/README.md) and existing
technical owners for command/help and evidence accounts. The management plan's
[development/publication checks](TRACE-MANAGEMENT-PLAN.md#development-and-publication-checks)
handle generator coupling without a guide amendment or substitute user guide.
Do not add a second dispatcher, a result-fabrication mechanism or a test-only
binary in place of exercising the normally built app.

### Preserve the experiment and identify the intervention

Exercise the route in the normally built and released app. A special test-only
binary, external replacement driver or fabricated result cannot substitute for
that coverage. Keep fixture construction, expected effects and resource cleanup
with the existing harness; the executable supplies the selected intervention
through the new entry point.

Retain the actual command, ordinary input, supplied controls, source/app identity
and raw output, including timing and exit evidence where the experiment uses
them. Establish how an experimental invocation remains recognizable in its
retained command/output account, including an early refusal or transport failure.
Reuse existing override echoes and equipment provenance when they suffice;
introduce only the additional indication needed where they do not. Distinguish
an intervention requested from one observed to have taken effect, and preserve
safe path handling. Historical runs retain their original commands and meanings.

Capture the existing positive and rejected experiments before changing entry
points. Compare them with the migrated callers on the identified rebuilt app:
which component ran, which intervention occurred, what evidence survived, and
which independent checks still rejected faults. Preserve failure contrasts,
identity checks, command accounting and cleanup duties. A zero exit from each
command is insufficient experimental equivalence.

Move every selected invocation in the caller mapping and retire the selected
ordinary-request activation paths. Temporary dual entry points may support the comparison but
must be gone before the migration is credited. An internal representation may
remain useful without remaining admissible as an ordinary request. Specify the
settled rejection of mixed old/new inputs, so removing a field neither silently
ignores a promised intervention nor accidentally removes unrelated coverage. Keep any assertion or outcome-authority changes
separately attributable from these interface changes.

### Place verification within the combined sequence

Use the settled caller mapping to supply shared evidence reading requirements
to the reporting capability stage. The executable and
caller changes land after the management plan's unchanged-app instrument
checkpoint, with a rebuilt app and their own routed verification. They may
proceed alongside conversions and cohort migration where the callers are
disjoint; overlapping work first needs an established experiment baseline.

Start from the developer-command route in
[change verification](../tests/CHANGE-VERIFICATION.md): unit, integration and
source-drift checks, plus `witness_contract/test_input_controls` and
`witness_contract/test_input`. Add the actual admission and native-boundary
routes affected, and every mapped experimental caller. Confirm the catalog
selection before executing; the publication-only controls cannot establish
experimental execution. Show that the new route reaches each selected
intervention and that ordinary requests can no longer activate it, while `read`
still launches nothing and retains its publication/refusal behavior. Include
combined controls, invalid values, unreached interventions, early refusals,
equipment identity and cleanup where the selected path uses them.

Complete this work before final integrated verification. The default and
selected opt-in batteries must exercise migrated callers through the new route,
including the extracted development candidate in the adapted acceptance control.
Future release batteries inherit those callers under strict release admission. The closing outflows receive the
implemented boundary, its evidence and retained costs. They do not receive an
undeveloped recommendation for another seam investigation.

## Bounded pytest adoption

### Suitability decision and selected cohorts

The current inventory supports two specific cohorts. Select them before
implementation begins, as this plan does; confirm the boundaries against any
intervening changes before coding. The obligation is to finish both coherent
cohorts, not a percentage of the repository or a target item count.

| Cohort | Complete scope and reason for selection |
| --- | --- |
| Constructed worker-wait pilot analysis controls | All scenarios currently orchestrated by [worker_wait_pilot_controls.py](../tests/suites/witness_contract/worker_wait_pilot_controls.py), under `witness_contract/worker_wait_pilot_controls`: ordinary/actor/neighbor receipts, decoding and interval arithmetic, historical missing-record forms, grace and scan analysis, independent faulty formulas, exclusions and pooling, comparative judgments, disk/Markdown round trips, and constructed stager identity controls. These share one instrument and fixture vocabulary. They exercise valid unfavorable comparisons, withheld conclusions and invalid evidence without needing a live timing experiment. |
| Markdown reader controls | The complete [markdown.py](../tests/suites/source_drift/markdown.py) population under `source_drift/markdown_reader`: block, comment, link, heading, table and line interpretation, vendored bytes/importer rules and fresh-process import guards. The inspected module has eight test-bearing classes and 38 methods, including subcases. This tests pytest's fixture isolation, parameterized diagnostics and cleanup benefits beyond outcome classification, while retaining independently written expectations. |

Cohort one is a sizeable script-driven scenario population, not one trivial
test. Moving its `main` behind a single pytest function would preserve its
opaque first-failure orchestration and would not fulfill the mandate. Expose
meaningful experiment/control units with fixtures and parameterized variants,
preserving dependencies where a rejection control needs an accepted baseline.
Keep its hand-authored arithmetic and rejection expectations independent of the
reader under test. Reader correctness remains enforced even when a reader's
product-comparison conclusion is advisory.

Cohort two must become pytest-native functions/fixtures and useful variants,
not merely unittest classes collected by pytest. Retain exact reader structures,
refusals, tampered vendor controls, ambient-import contamination contrasts and
the per-control input/command evidence already supplied by `receipts.TestCase`.
Parameterization should improve attribution, not inflate the apparent amount
of coverage. Neither cohort's completion is measured by its resulting item
count.

The first cohort is mostly constructed computation, but not command-free: its
stager controls execute `ditto` and a stand-in worker's `--version`, stopping
before signing. The second also invokes Git and fresh Python interpreters.
Preserve those real boundaries and their environment/refusal contrasts; replacing
them with mocks just to simplify migration would lose evidence. Neither cohort
requires app admission, native compilation or a signing identity merely because
it uses pytest.

Other candidates considered remain outside this migration:

- The live exec lifecycle family has valuable lifetime observations, but adding
  XPC-launched resources to pytest's current process-group ownership model is
  a separate orchestration problem. Its selected outcome conversion stays in
  the existing shell/capture path.
- BYOXPC retirement and the live worker-wait pilot have durable session,
  generation, signing and measurement-window responsibilities. Their reporting
  changes do not justify migrating those drivers now.
- The provenance, build-entry and release controls are adversarial infrastructure
  checks. Their custom inputs, locks, child environments and failure sequences
  merit a separate suitability decision; a large unittest count is insufficient.
- Other source-drift modules mix generator transactions, source copies and
  native configuration. Migrating the Markdown reader does not authorize
  converting the whole suite. The small CPU-reader controls remain supporting
  verification, not a token substitute for the pilot cohort.

If current inspection overturns either cohort's suitability, document the
specific lost coverage, orchestration cost or boundary problem and explicitly
reconsider the mandate before implementation. Do not silently substitute a
trivial test or force an unsuitable population into pytest. Completing these
two cohorts ends the migration obligation; it creates no standing requirement
to convert the remainder.

### Fit the subordinate engine to these cohorts

Keep the existing division: pytest discovers internal items, supplies fixtures
and reports phases; PolicyWitness owns public selection, prerequisite and
artifact admission, supervision, durable evidence, cleanup and retention.
Whole-family public selection and isolated pinned packages remain the starting
boundary. Collection must not acquire native equipment, start the experiment,
download packages or replace evidence.

The current engine is specialized in places: `pytest.ini` names the exec
module; collection source receipts name `exec_domain.py` and
`check_exec_evidence.py`; the display knows exec-specific baseline/finalizer
artifacts; release validation requires a command for every item. Generalize only
these demonstrated assumptions, keeping exec-specific observations with their
domain owner. Prefer explicit family inputs at the existing boundary over a
new parallel registry or an inferred complete dependency graph.

Pure computations need no dummy command or command-owner process. Require phase
and input evidence appropriate to them, and account for an empty operation set
as such. Actual commands still need supervision and complete references. A
declared computation must not conceal a promised missing command. Route the
cohorts' real subprocess calls through the selected supervised boundary without
stripping the deliberately controlled child environments used by import tests.
Preserve direct-command versus descendant accounting limits.

Reuse the input/blob recording parts of `receipts.py` where they remain useful;
remove unittest scheduling/status responsibilities from migrated paths instead
of running two result engines. Review fixtures for hidden acquisition, shared
mutable inputs and exceptions during cleanup. Pytest session teardown attached
to the last item must still identify the actual scope of a shared failure.
The existing exec family and its ownership controls must retain their complete
native sequence and independently rejected variants.

### Separate migration equivalence from revised authority

Before changing authority, map the old scenarios to the new observations and
checks, including positive controls, rejected variants, independent effect or
byte observations, setup failures, cleanup, receipts and literal descriptions.
Use stable scenario identities; do not demand a one-to-one mapping of functions
or raw item counts. Preserve intentionally ordered sequences within their
experiment while allowing unrelated controls to report independently.

Run the old and migrated paths against the same controlled inputs at attributable
revisions. Compare established facts, rejected faults, command boundaries and
artifact availability, not only zero exits. Temporarily retaining both paths
for comparison is useful; retire the old orchestration when equivalence is
established. Then identify the intentional assertion/authority deltas separately.
These steps may share a patch series, but their evidence must remain separable.

Measure what migration retires: hand-maintained scenario dispatch, ad hoc
restoration/temporary-directory management, opaque first-failure reporting or
duplicate result accounting. Count added fixture dependencies, identity maps,
adapter conditions and receipt machinery in the same comparison. Moving every
line into fixtures without reducing a maintenance duty is not evidence of an
improvement.

## Implementation stages and dependencies

| Stage | Bounded work and handoff |
| --- | --- |
| 1. Prepare the selected work | Confirm the two cohort boundaries and mapped callers against intervening changes; assess the survivor instrument's remaining product obligations and selected trace claims. Use the settled seam scope and dependency removal. Identify shared evidence requirements and old propositions/controls. Settle the small reporting comparison. Complete necessary development/build publication support before taking the unchanged-app baseline. |
| 2. Establish reporting and enforcement capability | Change shell/dispatcher and pytest boundaries with mixed-outcome controls. Update dependency interpretation, candidate/release evidence validation and producer-bound readers together. Supply deterministic replay through existing reconciliation and aggregate functions. Complete the management plan's live/replay checkpoint before conversions or further build-contract changes. |
| 3. Exercise real conversions and scope repairs | Convert the survivor, retirement and pilot reporting; remove inherited aftermath lifecycle dependencies and select the survivor directly by default. Repair assertion-to-unrun paths and assessment-selected DT-53/132 and DT-63/124/125 claims with their contrasts. Product remedies in transport/receipt threads follow management's substantive decisions, with no implementation-layer presumption. |
| 4. Complete both pytest cohorts | Establish migration equivalence and then any separately justified outcome revisions. Retire the replaced orchestration. This can proceed alongside stage 3 after stage 2 supports the necessary receipts, pure items and real commands. |
| 5. Complete the selected seam migration | After the instrument checkpoint, implement the experimental route and migrate its callers, establish experimental equivalence and retire selected ordinary-request activation paths. This can proceed alongside stages 3 and 4 where independent; preserve attributable baselines when callers overlap. Complete its routed checks on the rebuilt app before final integrated verification. |
| 6. Assess preservation, reduction and maintenance cost | Verify the combined default and selected opt-in behavior, release evidence handling and old-format semantics. Rehearse changed product behavior through the revised tests and accounts. State what authority actually disappeared and what evidence or controls remain, with any residual costs. |

Land stage 2 with no conversion in it, so the capability alone can be shown to
leave existing results as they were. Each conversion then lands separately,
naming its old assertion and the reason for its new authority. Stage 2 need
not change a build-contract input, provided it leaves alone the five
`tests/lib` helpers that list names, `checkout_lock.py` among them. The
management plan's instrument checkpoint depends on that: it compares the
capability alone with a baseline battery of the same app.

The hold on authorized product changes ends at that checkpoint, and stages 3,
4 and 5 then proceed. Finish in stage 2 every change to the shared reading path
that the conversions, cohorts and selected seam evidence will need, including
pure-item, receipt and development-candidate support. A later reader change
follows management's deterministic-replay-first rule, with a further live pair
only for an identified integration uncertainty. Seam command/admission changes
belong after this comparison, not in stage 2.

Implementation owners are existing boundaries, not new organizational layers:
`test_cli.py` and the catalog for selection; `testlib.sh`, `case.sh` and
`suite_run.py` for shell results/reconciliation; `pytest_engine.py` and
`pytest_family.py` for subordinate item evidence; `receipts.py` for existing
control evidence; `execution_contract.py`, `release_accept.py` and
`release_runs.py` for release obligations; each selected suite for its
observations, assertions and descriptions. The seam work uses controller
interface definitions and run orchestration, then the affected runner admission
and request-planning boundaries; it does not create another test dispatcher.
Touch ownership/retention machinery only where the selected reporting change
requires it, preserving its refusal rules. Reconfirm these call paths before
editing if the baseline has moved.

## Discriminating verification

Use independent expected outcomes for controls of the new machinery. A record
writer and its reader agreeing on a new field is insufficient. Inspect commands,
raw evidence, terminal output, reports and aggregate decisions together.

| Contrast | Evidence required |
| --- | --- |
| Deterministic reporting comparison | Replay identical retained inputs through the old and new `suite_run.reconcile`, `account`, `finish` and battery-validation paths, with matching captured context and isolated outputs. Independently expected unchanged decisions must agree; new informational/advisory fixtures have explicit expected deltas or an old-format refusal. Corrupt, omit and contradict evidence and authority; invalid accounting must remain consequential. No archived release is relabeled. |
| Valid but unfavorable advisory judgment | Feed a complete pilot comparison with an unfavorable independent expected conclusion. It appears in the case, terminal and run account; the run remains eligible when all required controls hold. Exercise both ordinary dispatch and the release validator. |
| Same observation missing or invalid | Remove a required receipt, change its identity, omit a scheduled member or corrupt an operation reference. Acceptance fails with the evidence/accounting reason, while valid earlier observations and any evaluated verdict remain readable. |
| Verdict-free lifetime observation | Exercise both survivor and independently observed prior-exit histories, then the live/disposable contrast. Follow the valid prior-exit account through checker, direct default selection, aftermath's removed dependency, dispatcher and aggregate battery acceptance. It must not fail for absence of survival; missing observation and uncertain cleanup still fail. Show the old assertion and every transitive requirement removed. |
| Enforced judgment still authoritative | Intentionally change a retained expected public fact or remove a required independent effect. Require its designated assertion failure and blocking result, not merely a later crash or missing report. Include a valid neighboring case that still runs. |
| Mixed failure | Combine an unfavorable advisory result with failed teardown, missing command settlement or artifact mutation. The advisory judgment stays non-gating, but the run and release remain rejected for the independent fault. |
| Cohort equivalence | Compare accepted and rejected scenario coverage before and after migration, including historical missing-record forms, arithmetic/formula controls, disk round trips, stager refusals, vendor tampering and fresh-process import contamination. An extra pytest item is not extra coverage. |
| Experimental route preserves the instrument | Compare selected old and new callers at identified app revisions, including positive, rejected and unreached interventions. Retain independent effects, equipment identity, failure contrasts, command evidence and cleanup. Keep this equivalence distinct from any simultaneous assertion revision. |
| Experimental and ordinary admission differ deliberately | For each of the eight controls, observe the intended intervention through the new route and rejection of its old ordinary-request key, including inert values, direct client/host submissions and mixed controls. Show a valid ordinary neighbor and unchanged remaining substitutions. Preserve ordinary/actor semantic contrasts, publication-only `read` and recognizable experimental intent before a control is reached. |
| Aggregation and dependencies | Use a mixed selection with pure items, commanded items and legacy cases. Verify exact selection accounting, scope of each count, absence of an informational passing assertion, declared prerequisite failures, continuation after failures and the affected dependency's actual requirement. |
| Authority cannot disappear from results | Remove or relabel an expected judgment, drop a family reference, alter declared authority or supply contradictory terminal evidence. Independently captured expectations must reject the account rather than accept an apparently cleaner run. |
| Development is not publication | A signed, source-matching development candidate with the explicit publication boundary can run and supply valid evidence. Altered frozen bytes, stale technical outputs and missing boundary evidence fail. Strict release/publication readers reject its artifact and candidate receipt, including attempted promotion; constructed current-release controls still pass. |
| Historical and portable evidence | Reread supported old evidence under its original semantics and new evidence under its captured contract. Keep old failures and unsupported-format refusals. Remove required new artifacts from a portable bundle and require rejection by verification/publication/retention readers. |
| Literal claims | Trigger each changed assertion and completion path. Compare its actual message, catalog name/description and coverage statement to the proposition and authority exercised. A successful formatter or grep cannot establish that semantic correspondence. |

The existing [dispatcher controls](../tests/suites/dispatcher/README.md),
[shell-helper controls](../tests/suites/shell_helpers/README.md) and
[preflight release controls](../tests/suites/preflight/README.md) are the starting
verification owners. Extend their independent fixture inputs instead of deriving
every expected summary from the implementation being tested. Retain pytest's
existing cancellation, unavailable-engine, partial-phase, changed-context,
command-settlement and ownership-recovery controls.

Run registered selections through `tests/run.sh` with fresh owned output,
following [tests/AGENTS.md](../tests/AGENTS.md). For the capability, use
`--suite dispatcher --suite shell_helpers`, explicitly including
`--case dispatcher/pytest_controls`, plus `preflight/release_controls`,
`preflight/release_publish_controls` and `preflight/release_rotation_controls`
for acceptance, portable evidence and retention. Include
`preflight/release_deadline_controls` if command supervision changes. Confirm
the selection and dependencies with `--list` before executing. Run both migrated public
cohorts, the existing exec pytest family and the selected converted observation
cases. Use controlled inputs for deterministic reporting contrasts, then native
runs for claims about live observation and cleanup; a constructed report alone
does not verify the latter.

For selected lifecycle/erasure corrections, use their actual Swift, C and
integrated reader paths rather than only the Python aggregation controls.
Changes to the worker wait, release store or eligibility rule still require
`witness_contract/order_barrier_mutations`; measuring or migrating a reader does
not itself establish such a product change. Run source-drift checks for changed
registrations, documentation/support or generated inputs. Run the default
battery against the unchanged app at the instrument checkpoint, each converted
or migrated case when it lands, and the default battery with the relevant
opt-ins in the final integrated verification.
Use the release controls to establish strict acceptance semantics and the
separate development-candidate evidence path. The management plan owns their
[final integrated use](TRACE-MANAGEMENT-PLAN.md#three-boundaries-for-broad-runs).
Changes to `release_accept.py`, `execution_contract.py` or `release_runs.py` route
to `preflight/build_refusal_controls`; run that long case once at the end, with
its existing live battery adapted to an extracted development candidate and
strict publication-refusal contrasts. Do not manufacture release readiness by
retagging the changed product or refreshing frozen guide content in its copy.

Before then, read completed real battery evidence with the revised validator
at the instrument checkpoint and at the first battery containing the converted
cases and migrated cohorts. These direct investigations credit no case. The
checkpoint also replays identical retained inputs through old and new reporting
interpretations, using the same selected context rather than changing source
expectations to obtain agreement. Normalize only identified incidental output
locations when comparing; do not normalize away evidence, identities, authority
or failure distinctions. If an adapter is needed to feed an existing function,
keep it in the controls and demonstrate that it does not invent missing evidence.
Old artifacts stay producer-bound. New-outcome fixtures are separately identified
controls, not rewrites of those artifacts.

Do not count an environment-refused native run as a product result. Preserve
source/app identity, evidence availability and applicability when comparing
old and new runs, and retain interrupted cleanup obligations under the existing
rules. Verification for this plan must not overwrite the historical runs it
uses for comparison.

## Acceptance argument: preservation and reduction

Acceptance needs a reasoned account of both what remains dependable and what
stopped constraining the architecture. Reporting capability, two completed
pytest cohorts, the selected executable seam migration and accurate wording
are necessary parts of this proposal; none alone establishes the intended
overhaul. Moving a seam does not itself count as relinquishing a product
expectation.

Identify at least one previously enforced product expectation that no longer
blocks an otherwise valid alternative. Explain why removing its authority is
justified, how observation still distinguishes the alternatives, and how invalid
evidence and required controls remain consequential. Show this at the outermost
relevant acceptance boundary, including the candidate battery and
strict release-reader controls, not just inside a test function. A mechanically
correct migration that relinquishes no questionable enforcement is incomplete.
For every selected authority reduction or retired activation path, identify the
old obligation and its full path through callers, fixtures, dependencies and
aggregation. Demonstrate its disappearance there while justified independent
scrutiny remains. A label change or a new CLI entry point alone is insufficient.

For preservation, account for the cohorts' observations, independently authored
oracles, rejection contrasts, command evidence and cleanup, together with the
selected seams' experimental equivalence and continued adversarial
build/release/provenance controls. For reduction, name the old survival
requirement or other justified obligation removed, any duplicate test
orchestration retired, and any misleading coverage claim corrected. Account
separately for the ordinary-request entry points retired and the command,
adapter or documentation duties added in their place. Distinguish retirement
of an assertion from retirement of useful evidence.

For each relinquished judgment, explain the test's present observational scope
and reason in its suite account and changing commit. Keep shared testing
principles in working guidance and particular product decisions local. Do not
create a registry of withdrawn enforcement. When a real user responsibility
remains, give the management plan's
[user-responsibility outflow](TRACE-MANAGEMENT-PLAN.md#user-responsibility-outflow)
the present duty, evidence and limits. A withdrawn test requirement that changes
nothing a user may rely on contributes no entry.

The [maintainer outflow](TRACE-MANAGEMENT-PLAN.md#judgments-for-the-maintainer)
collects only consequential reasons or unresolved matters not adequately
recoverable from the product and Git, under management's retention rule. It is
neither mandatory history for every conversion nor a separate approval process.
A maintainer must understand the test's current authority from its current owner.

Apply the acceptance companion's change-sensitivity reasoning locally. Rehearse
the descendant ending at completion, actor fallback disappearing, and a receipt
or identity premise changing, together with the selected seam rehearsal. Where
the acceptance plan rehearses the same change, make the two one trace under one
statement of the hypothetical. Trace which remaining expectations need a
substantive decision, which observations
simply report different facts, which public commitments still constrain the
change, and which descriptions require review. Include hidden adapters, dependency rules and source/provenance
declarations in the cost. Keeping independent scrutiny may properly retain
several checks of a rule; copying the implementation's answer into every oracle
is not economy.

The resulting judgment should name the decisions no longer independently
maintained, the necessary duties retained and any work displaced into reporting,
fixtures or interpretation. It can conclude that a proposed consolidation costs
more than it saves or that a particular observation merits retirement. It cannot
declare success from a larger pytest population or a more expressive list of
statuses. Nor does an inconclusive rehearsal create a permanent reconciliation
obligation among the three plans.

Complete this bounded overhaul when the selected capability and conversions
are verified, both cohorts are genuinely migrated, the selected seam migration
is implemented and verified, selected trace remediations have their
assessment-owned dispositions and accurate test accounts, and the
preservation/reduction argument holds. Remaining trace findings stay with the
management plan. Further migration or product redesign requires its own useful
scope, rather than following automatically from this work.

Keep working evidence and implementation judgments with this associated plan
under the [records guidance](AGENTS.md). Permanent test documentation should
describe the resulting behavior through its normal owners without inbound
links to investigation records. The continuing value of a test is the evidence
and justified scrutiny it supplies, including when that evidence helps explain
why an old architectural obligation can be discarded.

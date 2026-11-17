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
| This plan | Owns the proposed test-authority and reporting capability, selected assertion and wording corrections, two bounded pytest migration cohorts, and verification of preservation and relinquishment. |

The management plan's
[combined sequence](TRACE-MANAGEMENT-PLAN.md#working-the-three-plans-together)
owns the order in which work shared by the three plans settles and the
boundaries at which broad runs happen. The stages and verification below state
this plan's own obligations within that sequence.

The [guide freeze](TRACE-MANAGEMENT-PLAN.md#guide-freeze-and-public-commitments)
remains binding, including shared and generated explanatory content. A new test
classification cannot withdraw a public commitment, resolve a consequential
ambiguity by fiat, or publish a replacement interpretation elsewhere. A known
violation remains a defect even if a particular test ceases to gate changes.
Any permitted acceptance of that cost needs the management plan's substantive
present-tense disposition, not just a green run.

This is an implementation proposal, not an implementation or a fresh acceptance
run. It does not require reviewing every test before useful changes proceed.
Build, release, provenance, ownership and cleanup controls remain adversarial.
Their rejection duties are not candidates for relaxation to make reporting
uniform. Product redesigns used below are investigations, not authorized product
changes.

## Investigation basis

The source inspection for this plan used revision
`9714e451c270ef377d28aa460cdd8e79a9d5f96a`. It traced catalog selection, shell
finalization, dispatcher reconciliation, pytest collection and reporting,
portable release evidence, selected Python checkers, Rust and Swift wrappers,
and the observation cases discussed below. No catalog case, build, native
experiment or release procedure was executed for this plan.

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

Dependency admission also currently asks whether a predecessor passed. For each
converted dependency, establish what its dependent actually needs: completed
evidence, a usable fixture, or a particular enforced proposition. Do not turn
all dependencies into completion-only checks. In particular,
`run_effects/aftermath_footprint` selects the nominally opt-in exec survivor case
as a dependency, bringing it into the default battery. Trace that relationship
and its own assertions so the withdrawn survival requirement is not silently
reimposed elsewhere or retained solely to satisfy dependency machinery.

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

The primary enforcement-reduction candidate is
`runner_exec_lifecycle/closed_streams_leader_exit`. Its
[checker](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py)
observes initial peer identities and process groups, closes both streams, exits
the leader and waits for the CLI. `observe_survivor` then requires the descendant
to remain alive and answer a ping with its original identity and group. Later
cleanup releases it and requires its exit. The final shell message explicitly
credits a surviving descendant. An implementation that stops that descendant
can therefore fail the case even though the suite describes survival as a
current observation limit, not a desired containment rule.

Propose a verdict-free account of the descendant's post-completion lifetime.
Keep independently registered exit events, generation identity, stream-close
acknowledgments, the later file effect, raw CLI output and separate test cleanup.
Retain justified checks of truthful public evidence and promised later effects
as enforced judgments, visibly separate from the lifetime observation. Examine
fixed expectations such as the no-request record so they do not indirectly
reintroduce the removed architectural requirement; any public-meaning issue
goes through the management plan before changing that expectation.

The commitment assessment for this conversion belongs to the management plan,
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

This conversion must remove actual blocking authority, including at dependency
and default-battery aggregation boundaries. If commitment assessment rules it
out, explicitly reconsider the candidate and justify another real reduction;
do not declare the overhaul complete from reporting changes alone. The adjacent
`worker_dies_during_exec` also requires live helpers after worker death, but is
outside the initial conversion unless the first investigation needs it.

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
and transport controls still justified when calls occur. Inspect existing public
commitments and the freeze before approving such a conversion or product change;
this is a rehearsal, not the mandatory initial reduction.

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
| 1. Fix the scope and authority decisions | Confirm the two cohort boundaries and current selected callers; obtain the survivor conversion's commitment assessment from the management plan; map the selected survey reporting gaps and trace claims. Record the old propositions, retained controls and intended reductions. Settle the small reporting comparison before expanding infrastructure. |
| 2. Establish reporting and enforcement capability | Change the existing shell/dispatcher and pytest boundaries only as needed, with mixed-outcome controls. Update dependency interpretation for affected cases, release validation and producer-bound evidence readers in the same stage. A new non-gating result cannot ship while release or summary code silently converts it to a pass. |
| 3. Exercise real conversions and scope repairs | Convert the survivor observation, retirement completion and pilot comparison reporting; repair selected assertion-to-unrun paths. Implement the management-approved DT-53/132 and DT-63/124/125 assertion/wording/support corrections with their contrasts. Keep transport and receipt product decisions bounded by their assessment and freeze. |
| 4. Complete both pytest cohorts | Establish migration equivalence and then any separately justified outcome revisions. Retire the replaced orchestration. This can proceed alongside stage 3 after stage 2 supports the necessary receipts, pure items and real commands. |
| 5. Assess preservation, reduction and maintenance cost | Verify the combined default and selected opt-in behavior, release evidence handling and old-format semantics. Rehearse changed product behavior through the revised tests and accounts. State what authority actually disappeared and what evidence or controls remain, with any residual costs. |

Land stage 2 with no conversion in it, so the capability alone can be shown to
leave existing results as they were. Each conversion then lands separately,
naming its old assertion and the reason for its new authority. Stages 2
through 4 need not change a build-contract input, apart from the run-flow
corrections noted above, provided they leave alone the five `tests/lib`
helpers that list names, `checkout_lock.py` among them. They can then finish
against one unchanged signed app. The management plan's instrument checkpoint
depends on that: it compares the harness-side work with a baseline battery of
the same app before any product change follows.

Implementation owners are existing boundaries, not new organizational layers:
`test_cli.py` and the catalog for selection; `testlib.sh`, `case.sh` and
`suite_run.py` for shell results/reconciliation; `pytest_engine.py` and
`pytest_family.py` for subordinate item evidence; `receipts.py` for existing
control evidence; `execution_contract.py`, `release_accept.py` and
`release_runs.py` for release obligations; each selected suite for its
observations, assertions and descriptions. Touch ownership/retention machinery
only where the selected reporting change requires it, preserving its refusal
rules. Reconfirm these call paths before editing if the baseline has moved.

## Discriminating verification

Use independent expected outcomes for controls of the new machinery. A record
writer and its reader agreeing on a new field is insufficient. Inspect commands,
raw evidence, terminal output, reports and aggregate decisions together.

| Contrast | Evidence required |
| --- | --- |
| Valid but unfavorable advisory judgment | Feed a complete pilot comparison with an unfavorable independent expected conclusion. It appears in the case, terminal and run account; the run remains eligible when all required controls hold. Exercise both ordinary dispatch and the release validator. |
| Same observation missing or invalid | Remove a required receipt, change its identity, omit a scheduled member or corrupt an operation reference. Acceptance fails with the evidence/accounting reason, while valid earlier observations and any evaluated verdict remain readable. |
| Verdict-free lifetime observation | Exercise both survivor and independently observed prior-exit histories, then the live/disposable contrast described above. Neither history is required as product behavior; missing observation and uncertain cleanup remain consequential. Show the exact old assertion that rejected the alternative. |
| Enforced judgment still authoritative | Intentionally change a retained expected public fact or remove a required independent effect. Require its designated assertion failure and blocking result, not merely a later crash or missing report. Include a valid neighboring case that still runs. |
| Mixed failure | Combine an unfavorable advisory result with failed teardown, missing command settlement or artifact mutation. The advisory judgment stays non-gating, but the run and release remain rejected for the independent fault. |
| Cohort equivalence | Compare accepted and rejected scenario coverage before and after migration, including historical missing-record forms, arithmetic/formula controls, disk round trips, stager refusals, vendor tampering and fresh-process import contamination. An extra pytest item is not extra coverage. |
| Aggregation and dependencies | Use a mixed selection with pure items, commanded items and legacy cases. Verify exact selection accounting, scope of each count, absence of an informational passing assertion, declared prerequisite failures, continuation after failures and the affected dependency's actual requirement. |
| Authority cannot disappear from results | Remove or relabel an expected judgment, drop a family reference, alter declared authority or supply contradictory terminal evidence. Independently captured expectations must reject the account rather than accept an apparently cleaner run. |
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
battery against the identified candidate app, with the relevant opt-ins, at
the instrument checkpoint and again in the final integrated verification.
Use the release controls to establish acceptance semantics; any actual archive
acceptance must follow the existing release procedure and is not publication.

Revising `release_accept.py`, `execution_contract.py` or `release_runs.py`
changes release-acceptance orchestration, which
[change verification](../tests/CHANGE-VERIFICATION.md#build-refusal-controls)
routes to the opt-in `preflight/build_refusal_controls`. The constructed
release controls establish the revised semantics. That case's release-battery
sequence is the one catalog path in which real acceptance reads a real
battery, including the migrated families and the converted survivor case. Run
it once, in the final integrated verification, and not after each stage. At
the instrument checkpoint, reading the completed battery with the revised
release battery validator is a direct investigation that credits no case.

Do not count an environment-refused native run as a product result. Preserve
source/app identity, evidence availability and applicability when comparing
old and new runs, and retain interrupted cleanup obligations under the existing
rules. Verification for this plan must not overwrite the historical runs it
uses for comparison.

## Acceptance argument: preservation and reduction

Acceptance needs a reasoned account of both what remains dependable and what
stopped constraining the architecture. Reporting capability, two completed
migrations and accurate wording are necessary parts of this proposal; none
alone establishes the intended overhaul.

Identify at least one previously enforced product expectation that no longer
blocks an otherwise valid alternative. Explain why removing its authority is
justified, how observation still distinguishes the alternatives, and how invalid
evidence and required controls remain consequential. Show this at the relevant
aggregate and release boundaries, not just inside a test function. A mechanically
correct migration that relinquishes no questionable enforcement is incomplete.

For preservation, account for the cohorts' observations, independently authored
oracles, rejection contrasts, command evidence and cleanup, together with the
continued adversarial build/release/provenance controls. For reduction, name the
old survival requirement or other justified obligation removed, any duplicate
test orchestration retired, and any misleading coverage claim corrected.
Distinguish retirement of an assertion from retirement of useful evidence.

For each judgment relinquished or narrowed, state what PolicyWitness no longer
establishes on a user's behalf, and what a user who needs that conclusion must
then do or avoid. Hand those statements, with the conversion and evidence they
rest on, to the management plan's
[user-responsibility outflow](TRACE-MANAGEMENT-PLAN.md#user-responsibility-outflow).
A withdrawn test requirement that changes nothing a user may rely on
contributes no entry.

Apply the acceptance companion's change-sensitivity reasoning locally. Rehearse
the descendant ending at completion, actor fallback disappearing, and a receipt
or identity premise changing. Where the acceptance plan rehearses the same
change, make the two one trace under one statement of the hypothetical. Trace
which remaining expectations need a substantive decision, which observations
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
are verified, both cohorts are genuinely migrated, selected trace remediations
have their assessment-owned dispositions and accurate test accounts, and the
preservation/reduction argument holds. Remaining trace findings stay with the
management plan. Further migration or product redesign requires its own useful
scope, rather than following automatically from this work.

Keep working evidence and implementation judgments with this associated plan
under the [records guidance](AGENTS.md). Permanent test documentation should
describe the resulting behavior through its normal owners without inbound
links to investigation records. The continuing value of a test is the evidence
and justified scrutiny it supplies, including when that evidence helps explain
why an old architectural obligation can be discarded.

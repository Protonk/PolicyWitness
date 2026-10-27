# Historical continuity obligations in tests

Examined `main` at `2d15b1138c973181eef23e38b4a4669d890f9fa2`, with a clean
working tree. This report investigates historical continuity obligations using
`TEST-WORK-SURVEY-REPORT.md` and `TEST-EXPECTATION-AUTHORITY-REPORT.md` as companion
accounts; both are alongside this report in `records/tests/`.
Between their source revision, `31b81951c9c8c4124089aa4dd342b2b63c0a86de`,
and the examined revision, only six files under `records/` changed. The product,
tests and current contracts examined here are unchanged from that source pin.

The four leads support three limited reductions: remove an executable dependency
on an old capture whose contents are rejected before interpretation; stop
requiring a current checker to reproduce its previously demonstrated blind
spots; and retire failure classification tied to completed test promotions.
The author has approved retiring the wrapper machinery described in finding 4,
with its diagnostic tradeoff and preservation requirements.
The comparison baseline supplies provenance without an active requirement to
operate or interpret its earlier producer. The wider screen found a separate,
explicit historical service: current release tools verify and use an older
release-evidence format. The author has decided to retire that older-format
service, accepting the losses and preserving the current-release operations
identified in finding 5. Implementation remains separate work.

## Basis and boundary

The author's intention is to leave historical interpretation and relationships
between releases to the researcher, including releases sharing a wire version.
The subsequent clarifications give this investigation a further constraint:
PW already embodies learned distinctions in its apparatus. A present experiment
can use those distinctions without reconstructing history. Such experiments
still warrant scrutiny; their historical origin neither condemns them nor
settles their continuing value. The account of how users and developers face
macOS through PW must remain clear. Platform history is outside this
investigation, bounded by the current architecture and toolchain restrictions.
Specific machinery and explanations are considered individually; this report
does not propose special documentation categories or general prose restrictions.

The current [wire contract](../../docs/CONTRACT.md#supported-versions) requires
exact-version admission before interpretation, retains unsupported bytes, and
does not translate historical judgments. It also expressly permits comparisons
of current-format runs. An older admissible record remains subject to current
reading rules: age is not a refusal condition. Changing those rules or their
meaning would require the contract/version decision described in
[When a number moves](../../docs/CONTRACT.md#when-a-number-moves). None of the
three narrow proposals below needs such a change. The release-evidence decision
concerns a different, separately promised format service.

Inspection used Git history, source and documentation reads, JSON parsing and
text searches. The initial screen covered 645 tracked textual paths across
controller and runner sources, tests, shared readers and fixtures, generators,
build/release tooling and owning documentation. It excluded `records/`,
`dist/archive/`, `dist/evidence/`, `tests/out/`, vendored libraries, build outputs
and `.tmp/`. The path selection included Markdown, Python, shell, Rust, Swift,
C/header/Objective-C, JSON, TOML, YAML, text and build-description files.
Search terms included `legacy`, `histor*`, `backward*`, `compatib*`, `baseline`,
`version*`, `golden*`, `red`, `migrat*`, `retired`, `previous` and `old`, followed
by substring searches for compatibility/history terms and previous-version or
previous-schema names. Historical-looking hits were read for active consumers;
exact fixture, helper and symbol searches then traced the four leads and the
release-evidence dependency. Dormant plans, names, comments and symlinked guide
copies were not counted as executable obligations.

This was not another complete assertion survey or a compatibility audit. Depth
was limited to those five leads and dependencies affecting their interpretation.
Other hits received the bounded screen recorded below. No tests, builds, native
experiments, archive verification, service operations or cleanup ran. Local
archive metadata was read only after finding its active consumer; those
observations are explicitly local-only. Static inspection cannot establish
whether a future implementation preserves the native experiments.

## 1. The response-12 comparison baseline is provenance, not an active reference

The [baseline account](../../tests/fixtures/comparison/baseline_response12/README.md)
records comparisons against producer `ff2b192`, including two raw envelopes,
specimens and per-row match receipts. Its claim that these describe the then
current producer is qualified by the inventory revision `df333b4`. It does not
make that producer current at the revision examined here.

Exact-path and filename searches found no active reader of the baseline's
`run_a.json`, `run_b.json`, match receipts or specimen files. The operative input
is [matrix.json](../../tests/fixtures/comparison/matrix.json). The current live
reader constructs requests from it, runs the supplied current CLI, validates
the resulting envelopes, compares raw fields and comparison fields, and checks
effects and independent controls. See `check_row` and `main` in
[check_comparison_matrix.py](../../tests/suites/witness_contract/check_comparison_matrix.py),
lines 127–152 and 205–240. The current Swift
[ComparisonEvidenceTests](../../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift),
lines 104–137, supply constructed inputs to `comparisonEvidence` for all 43 rows
and check the six-field record and vocabulary. Extension/phase readers also use
the current matrix. The generator's `load_matrix` and `render_matrix` read that
same file, not old replies or match receipts
([generate_limits.py](../../docs/generate_limits.py), lines 147–185).

Agreement with the old producer is not the only stated authority for these
expectations. The [current fixture account](../../tests/fixtures/comparison/README.md)
requires review against current rules and independent controls. The
[comparison contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md#comparison-record)
defines classification from raw attempt evidence, submitted operations and
targets, and the collection/release/acknowledgement chain. For example, the S03
permission-failure expectation has a direct mode-000 EACCES control outside PW;
it does not acquire sandbox attribution from the earlier producer's answer.
The current live reader preserves that direct observation. These are present
obligations even when their discovery involved an earlier run. This trace does
not independently re-prove every matrix expectation's adequacy.

If the response-12 producer became impossible to run or its output impossible
for current readers to admit, no traced current check or generation step would
fail for that reason. A change to a current comparison rule would instead
require review of the current contract, matrix and readers. No executable
historical responsibility was found to remove here. Retain the historical
receipts. The active fixture README's “Row provenance” explanation is an
individual place to assess explanatory burden, separately from the matrix's
current work; its presence alone does not justify reducing that work.

## 2. The known-loss capture contributes only an unsupported envelope

The sole current code consumer found for
[a1_known_loss.json](../../tests/fixtures/disposition/a1_known_loss.json) is
`expected_fixture_controls` in
[disposition_controls.py](../../tests/suites/blackbox_e2e/disposition_controls.py),
lines 237–263. It is reached through `run_controls` from
`blackbox_e2e/checker_controls`. It loads the old capture and requires rejection
by three entry points: `read_lifecycle`, `lifecycle_oracle.check_record` and
`consumer.validate`.

All three reach the same version gate before claims are read:
[document_versions.py](../../tests/lib/document_versions.py), lines 18–35;
[lifecycle_adapter.py](../../tests/lib/lifecycle_adapter.py), lines 71–72;
[lifecycle_oracle.py](../../tests/lib/lifecycle_oracle.py), lines 457–464; and
[consumer.py](../../tests/lib/consumer.py), lines 808–820. The decisive fact is
the unsupported controller-envelope number. The runner-response number,
deadline, kill request, signal, attempt progress and lost cause are not
interpreted. The file must exist and parse as JSON, but this control does not
authenticate the capture or check the loss it historically illustrated.

The [fixture account](../../tests/fixtures/disposition/README.md) keeps a separate
current-format capture, `response23/a1_expected.json`, as the accepted neighbor.
Copies of that input exercise missing records and semantic losses, including
missing termination requests, conflicting status and lost cause/progress
information. These checks remain downstream of successful admission
(`expected_fixture_controls`, lines 258–305). Refreshing that current acceptance
capture after a version bump is current-contract work, not migration of the
known-loss capture.

**Supported reduction.** Replace the old-capture input in this one control with
a deliberately constructed envelope: integer `schema_version` unequal to the
current controller-envelope version, `kind: run`, `data: {}`, and no `steps`.
An empty body makes rejection before current-shape interpretation observable.
The expected refusal comes from the exact-version rule, independently of any
producer. A concrete precedent already exists in
[checker_controls.py](../../tests/suites/blackbox_e2e/checker_controls.py),
lines 218–224, using the current envelope version minus one. Preserve this
control's three entry-point expectations, accepted neighbor and current-format
semantic mutations; leave the historical file unchanged.

This removes a live dependency on a particular historical artifact and its
explanation. It removes no decoder or historical-interpretation service, and
there is no established burden of repeatedly migrating that artifact to save.
The explicit loss is testing rejection of this particular real captured
envelope. No check of its authentic historical loss is surrendered, because
the current control does not perform one. A future change needs to establish
the same early refusal at all three entry points and preserved acceptance of
the current neighbor; this report has not executed that observation.

## 3. The setup sensitivity case requires a past blind spot to remain present

`runner_unit/host_setup_oracle_sensitivity` copies the **current**
`host_setup_controls.py`, current runner sources and fixture sources, then
imports the copied checker as `legacy`. It does not retrieve an older checker
from Git. For the baseline and three variants, it runs the copied recipe and
independently inspects receipts. The variants change ready-pipe direction,
the shared-memory descriptor argument, and unmapping extent. The decisive
chain is in
[host_setup_oracle_sensitivity.py](../../tests/suites/runner_unit/host_setup_oracle_sensitivity.py):
source substitutions at lines 243–260, copied checker invocation at 371–403,
and success requirements at 333–368 and 408–419.

Success requires all 22 receipts per variant to be accepted by that checker,
alongside 22 completed recipe cases and ten rejected receipt controls.
Independent observations must establish actual child argv, descriptor access
mode and mapping extents; the partial-unmap variant must leave a suffix mapped
and then show successful independent fixture cleanup. Thus the acceptance
requirement is additional to observing and containing the injected faults.
There is a second requirement to preserve the mapping blind spot: line 340
demands that `legacy_maps_before_fixture_cleanup` remain zero, even for the
partial-unmap variant whose independent observer establishes a surviving suffix.

A concrete change exposes the obligation: strengthen the current setup checker
and its receipt observations to reject the wrong ready-pipe direction, while
keeping the correct host and its current guarantees unchanged. This sensitivity
case would fail because the copied checker no longer accepts the counterexample.
That is not just a stale source-substitution anchor. The requirement deliberately
preserves an investigative result about a checker limitation. Its
[suite account](../../tests/suites/runner_unit/README.md#host-setup-oracle-sensitivity-opt-in)
and [control account](../../tests/CHANGE-VERIFICATION.md#worker-resource-challenge-probes) make that continuing experiment
explicit. It supplies useful present information about the checker, but it
also obliges maintenance of a known weakness as a passing result.

**Supported reduction, conditional on changing the experiment's purpose.**
Withdraw the requirement that the current checker accept the three wrong-host
variants, and treat the old mapping counter as an observation rather than
requiring its false zero for partial unmapping. Keep the current checker verdict
as an observation, preserve correct baseline requirements, and retain the
independent observations, receipt
completeness, negative controls, source/input provenance and fixture cleanup.
This would cease guaranteeing that the old blind spots still reproduce while
keeping the route to observe the current host/checker relationship.

This is not a one-line deletion of `all(row["legacy_accepted"] ...)`.
`host_setup_controls.run` calls `check` during collection and stops at its first
rejection
([host_setup_controls.py](../../tests/suites/runner_unit/host_setup_controls.py),
lines 132–164); the sensitivity case also requires `legacy_recipe_completed`.
Collection failure and a checker's rejection of a deliberately wrong variant
would have to become distinguishable. Missing observations, equipment failures
and failed cleanup must continue to fail the experiment. Removing the ten
negative controls would surrender separate checker evidence and is not part
of this proposal. Those controls need admitted baselines so their failures
still establish the intended distinction, rather than merely re-detecting a
deliberate source fault already rejected by a stronger checker.

The loss is the automated claim that all three limitations still exist in the
current setup checker. There is no PW wire-admission change, but the case's
documented experimental promise must change, and accepting that diagnostic
loss remains a decision. Removing the whole case would additionally lose its
native wrong-direction/wrong-argv observations and partial-unmap/cleanup
experiment; the evidence here does not establish that larger reduction as
coverage-neutral. Nearby
[launch_descriptor_controls.py](../../tests/suites/runner_unit/launch_descriptor_controls.py),
lines 57–118 and 176–228, independently checks mapping extent, descriptor
identity/lifetime and rejection of restored defects. It does not replace this
case's full three-variant experiment.

The smallest implementation observation needed is a stronger current checker
rejecting a wrong variant while all required native observations and cleanup
remain available, with missing/contradictory observer receipts still failing.
Static tracing identifies the coupling; it cannot certify such a refactoring.

## 4. Former-red wrappers retain completed-transition diagnostics

`unit/rust.disposition_reds` and `unit/rust.byoxpc_reds` still select four and two
exact Rust tests respectively. Both wrappers require every named test to run,
the exact count, all tests passing and a zero Cargo status. On failure they
classify a test as an expected “red” only when a hard-coded assertion message
appears; otherwise they report an unexpected assertion, build or equipment
failure. See
[disposition_reds.sh](../../tests/suites/unit/disposition_reds.sh), lines 18–57,
and [byoxpc_reds.sh](../../tests/suites/unit/byoxpc_reds.sh), lines 17–54.

The transition is complete. The underlying tests are unignored current
regressions for disposition evidence and false-valued entitlement requirements.
They also remain reachable through `unit/rust.unit`, whose
[run.sh](../../tests/suites/unit/run.sh) invokes Cargo with `--bins`.
Their current assertions are in
[disposition.rs](../../controller/src/disposition.rs), lines 2132–2168 and
2200–2231;
[runner_manager.rs](../../controller/src/runner_manager.rs), lines 1281–1307;
and [runner_select.rs](../../controller/src/runner_select.rs), lines 1218–1249.
This remaining route is not a reason to consolidate execution or remove the
named selections.

Three of the four disposition classifications no longer match their current
Rust assertion messages. `conflicting_status_reports_the_status_rule` now
checks D1 and says “issue must name the status rule D1”, while the wrapper
expects its earlier B1 sentence. The two record tests no longer have the `E1:`
prefix required by the wrapper. Commit `ed0bd3d` changed those assertions;
the original four ignored tests were introduced in `5f6c619`. The first
wrapper message still matches one particular failed disposition value, and
the two BYOXPC messages still match current assertions. Consequently the
classification is not uniformly obsolete, but three entries preserve answers
that the corresponding current assertions no longer emit.

The disposition wrapper's transcript controls do not detect that mismatch.
`rust_wrapper_controls` reads names and messages from the wrapper itself,
constructs all-red and partial-promotion Cargo transcripts from those messages,
and requires promotion-count diagnostics
([disposition_controls.py](../../tests/suites/blackbox_e2e/disposition_controls.py),
lines 134–219). This validates the wrapper's classifier against its own message
table, not against current Rust failure text. Green runs do not need message
matching, and both classified and unclassified failures fail the case. The
finding is stale diagnostic authority, not evidence of a passing regression.

**Author decision: retire promotion machinery.** Remove the tables of former
assertion messages and promotion/red categories from the two wrappers, and the
corresponding diagnostic expectations in `rust_wrapper_controls`. Retain exact
selection and count, per-test success, Cargo status, missing/empty/wrong-test
and equipment-failure guards, raw logs and harness reports. Preserve the six
Rust regression assertions and their existing execution routes. Retiring this
machinery removes a completed transition's message/count obligations; merely
renaming the cases would not.

The accepted loss is the classifier's distinction between designated assertion
failures and other failures, including the still-valid BYOXPC classifications.
Raw Cargo diagnostics remain available. No product contract or admission rule changes;
the wrapper's documented diagnostic purpose and its controlled transcripts
will change. Implementation must show that fully selected passing tests
succeed, while failed tests with arbitrary assertion wording, incomplete or
wrong selection and nonzero Cargo status still fail. These are preservation
requirements, not a claim that this implementation has been made or run.

## 5. Release evidence maintains an explicit older-format service

The wider screen found a responsibility beyond the four initial leads.
[release_runs.py](../../tests/lib/release_runs.py), lines 6–9, promises that
both release-evidence bundle formats verify. Its packer writes only schema 2,
with the battery nested under acceptance. `verify_bundle` still admits schema 1
and its separate battery role (lines 86–105); `verify_release` interprets the
corresponding summaries and provenance (lines 156–234). Commit `7f0b4f6`
introduced the nested format while explicitly preserving the older service.

`preflight/release_rotation_controls` actively enforces this responsibility.
Its `legacy_pack` and `make_legacy_release` construct old-format fixtures using
current machinery; `legacy` requires an old-format archive to verify unchanged
before and after newer-release rotation, and requires rotation driven by an
old-format archive to resume after an interrupted rename
([check_release_rotation.py](../../tests/suites/preflight/check_release_rotation.py),
lines 51–100 and 451–490). The
[suite account](../../tests/suites/preflight/README.md), lines 349–353, promises
these operations. The obligation is compatibility even though no old PW binary
is executed and the fixtures are newly constructed.

This service has current callers. `publish` verifies the archive before
publishing
([release_publish.py](../../tests/lib/release_publish.py), lines 37–41).
`rotate` verifies it before loading or resuming the rotation journal
([release_rotate.py](../../tests/lib/release_rotate.py), lines 226–235).
Removing schema-1 admission would therefore prevent current tools from
verifying or publishing such archives and from starting or resuming rotation
driven by them. These are release integrity and resource-lifecycle operations,
not interpretation of an earlier sandbox observation. The historical-run
disclaimer does not itself withdraw them.

Local-only metadata gives the loss a concrete boundary. The six local archives
under `dist/archive/` for v0.2.7, v0.2.8 and v0.3.0 through v0.3.3 all declare
schema 1 in `evidence/test-runs/manifest.json`. Their `evidence/rotation.json`
records say `complete`; the local `tests/out/.release-rotation/` directory is
empty. No archive hashes, contents or verification result were checked. These
reads establish neither that those archives currently pass verification nor
that no interrupted operation exists in another checkout or copy.

**Author decision: retire superseded-format support.** Current release tools
will cease supporting the schema-1 release-evidence format. This decision
accepts the loss of current-tool verification and publishing of those archives,
and rotation/recovery driven by them. Retained historical bytes remain intact.
Verification of newly prepared releases in the current format remains part of
the release workflow, including verification before publication and before
retiring working evidence.

The smallest complete target is schema-1 admission and battery-summary
interpretation in `release_runs`,
the old-format construction and compatibility expectations in the rotation
controls, and the corresponding promise. Removing only the test leaves the
service in place. Preserving schema-2 verification requires keeping its hash,
inventory, provenance and completed-default-battery checks; preserving current
rotation requires its ownership and interrupted-operation protections.
New-format rotation can still retire older owned local runs using their
retention metadata, without interpreting their old archive bundle.

The accepted loss includes the latest local archived release observed here.
This is a decision to withdraw a release-tool service; it changes no PW
wire-response admission rule. Any unfinished operations depending on the old
service must be settled before removing their recovery route. No pending
rotation was found locally; the metadata inspected does not establish the state
of other checkouts or copies. That transition requirement does not create a
continuing promise to serve completed historical archives. No archive rewriting,
replacement historical reader or replay framework is proposed. Implementation
must preserve current-format verification, old owned-run cleanup and
current-format interrupted recovery, with those operations verified after the
change. This report records the decision; no implementation or execution of
those checks occurred here.

## Wider-screen boundaries and individual follow-up

The following active historical-looking mechanisms did not support additional
reductions within this investigation:

| Mechanism | Present obligation and boundary |
| --- | --- |
| Exact-version refusal and current-format metadata variation | `checker_controls.py`, lines 211–224, admits a current-format input with another producer identity/macOS stamp and rejects an unsupported envelope before its body. These are constructed admission controls, not a promise of agreement between hosts or releases. The current request/response rules cannot be narrowed by declaring old inputs historical. |
| Retired installation-kind spellings | `runner_manager.rs`, lines 31–40 and 1595–1629, reads `machme`/`debuggable` from persisted registry entries as `byoxpc` while rejecting them as new kind input. The wire contract explicitly preserves this recovery route so existing owned jobs remain removable. Its historical dependency protects present cleanup; no reduction is proposed. |
| Pairwise comparison equipment | [envelope_compare.py](../../tests/lib/envelope_compare.py), lines 150–192, validates both supplied sides with the current consumer, permits selected stamp changes only when requested, and keeps explicit identity requirements. Its [controls](../../tests/suites/blackbox_e2e/comparison_controls.py) mutate copies of current captures. It supplies a chosen present comparison, not an automatic requirement that each new release agree with an old one or a decoder for unsupported replies. [native_compare.py](../../tests/lib/native_compare.py) likewise inspects supplied artifacts; its current description reader also serves build receipts. These routes may support historical research without making PW maintain that research's conclusions. |
| Restored descriptor defects | `launch_descriptor_controls.py`, lines 200–213, requires the current checker to reject designated restored defects and separately observes the old-lifetime variant's native facts. That protects present discrimination; it does not require the current checker to retain a blind spot. No whole-case redundancy was established. |
| Old-clock experimental variant | [native_clock.sh](../../tests/suites/runner_c_worker_harness/opt_in/native_clock.sh), lines 75–102, requires fresh-process completion/application and current-clock validity, but records the old-clock failure count without requiring a past failure to recur. This is a current-host experiment. Its platform history and continuing experimental value were not separately audited. |
| Build caches, identities, source goldens and retention | Screened hits concerned current toolchain/output admission, agreement within one build or execution, current shape/source lists, or ownership of retained resources. Names such as baseline, compatibility and old did not establish an earlier release as the required authority. Their complete implementations were not re-audited. |

Two explanatory surfaces can be isolated for later individual work without
first removing useful equipment: the active comparison fixture README's
producer-history account identified in finding 1, and
[native_substitute.py](../../tests/lib/native_substitute.py)'s opening
“Meson migration” framing for a helper that currently copies an app, substitutes
native artifacts, signs and inspects it. The wrappers' stale ignored/red-stage
account is already part of finding 4's concrete machinery. These are bounded
explanation questions, not instructions to recategorize tests or append
historical notices throughout the documentation.

## Decisions and verification limits

The supported work is separable. The known-loss input replacement gives up one
real-capture rejection check. The setup change gives up reproduction of three
checker limitations while preserving the native experiment. The wrapper change
gives up designated-message classification while preserving regressions and
selection guards. Each removes a specific dependency or obligation; none
requires accepting a general reduction in current evidence quality. The specific
replacement for the known-loss capture and the setup-case reduction remain
proposals. The author has approved retiring the wrapper promotion machinery in
finding 4 and withdrawing the older archive-format service in finding 5, with
the stated losses and preservation/transition requirements. Implementation
remains separate work.

The investigation stops at these traced dependencies. It does not establish
repository-wide absence of historical obligations, resolve the value of every
current experiment, or infer kernel behavior from static tests. The remaining
execution questions are the narrow preservation observations identified with
each proposal. Source paths, cited line ranges and commits, canonical case IDs,
Markdown structure, relative links/anchors and documented command routing were
checked statically. Only this report was written; no product, test, fixture,
contract, plan or retained evidence was changed.

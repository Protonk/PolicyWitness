# Potential additions to the drift removal plan

Status: proposals for review; none of these removals is adopted.

The identifiers below are S4 and S6–S9 from the
[second sweep](FIVE-FOLLIES.md#second-sweep). S1–S3 are incorporated directly
in [DRIFT-REMOVAL-PLAN.md](DRIFT-REMOVAL-PLAN.md), with their remaining decisions
recorded there. S5 and the original five entries are outside this document's
selected scope. These IDs are unrelated to the plan's scenario-matrix row IDs.

Each entry records current producers, readers and reading costs, then the
decisions needed before adoption. A task that presently feeds `drift` is a
current use; whether its inputs belong in the replacement is a separate
decision. Validation counts as a reader when its failure affects another
result. Human use of stored output also counts, and source searches cannot
rule out external readers.

Adoption requires a new D6 row in the plan and coordinated changes to its
design, removal inventory, test owners and acceptance criteria. The existing
plan remains controlling until that happens. Stored evidence and release
artifacts keep their bytes.

| Finding | Potential addition | Principal unresolved decision |
| --- | --- | --- |
| S4 | Remove the copied `attempt.lifecycle.boundary` and `.result` claims | Whether an attempt should carry the full local claims or readers should join to disposition evidence |
| S6 | Remove the always-null `attempt.native_rc` | Whether explicit unknown native return belongs in the attempt shape |
| S7 | Remove the observer's duplicate `deny_lines` list | Whether raw-denial extraction convenience warrants a second list, and which observer contract changes |
| S8 | Remove some or all constant log disclaimers | Which limitations must remain explicit in each stored record |
| S9 | Remove or narrow the whole-run target-removal calculation | Which reader task warrants that derivation after the verdict disappears |

## S4. Copied attempt lifecycle claims

**Current structure and readers.**
[`attemptLifecycle`](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
copies the `step_boundary_reached` and `step_result_published` claim objects
from `runner_subprocess.disposition.steps[].questions` into
`steps[].attempt.lifecycle.boundary` and `.result`. These copies include each
claim's basis or reason.

Swift's [`dispositionIntegrityProblems`](runner/Sources/PWRunnerCore/PWRunnerAPI.swift),
Rust's [`validate_disposition`](controller/src/run_flow.rs), and Python's
[`check_record`](tests/lib/lifecycle_oracle.py) compare the copies with the
disposition claims. A Swift mismatch can degrade the reply; a Rust mismatch
causes `project_disposition` to withhold the projected disposition and
termination cause. These checks therefore have observable effects even though
they compare repeated evidence.

The adjacent `lifecycle.summary` has separate uses. The step builder uses it to
append lifecycle limitations, the
[Python adapter](tests/lib/lifecycle_adapter.py) exposes it, and the
[FIFO deadline checker](tests/suites/witness_contract/check_attempt_in_flight.py)
uses it to distinguish started and unreached attempts. Rust also validates the
lifecycle entries in `comparison.limitations`. This candidate covers the two
copied claims; removing the whole lifecycle object or its summary would require
a separate reader analysis.

**Reading cost.** An attempt currently carries its lifecycle support locally.
Removing the copies requires joining the attempt to its corresponding
disposition step. The underlying observations and claims remain available.

**Decisions remaining.**

- Decide whether to retain the local claim objects or make the disposition
  record their sole location. If removing them, specify the remaining
  `attempt.lifecycle` shape and how readers locate the corresponding step.
- Define the current-version rules for absent or malformed lifecycle data,
  including reporting-failure replies. Decide which integrity rules remain
  necessary after there are no copies to compare; removing equality checks
  must not silently remove validation of the original claims or summaries.

**If adopted.** Update D3/D5 and R1–R6 together: Swift types and invariants,
the step builder, Rust validation/projection, Python lifecycle contracts and
adapters, constructed fixtures, the response-shape golden and documentation.
Assign controls for valid lifecycle states, missing/malformed evidence and both
reporting-failure levels. Preserve the independent deadline and failure
scenarios; their expectations must use the chosen representation. The change
belongs to the response contract, with its controller readers coordinated in
the same integration increment.

## S6. The always-null attempt native return

**Current structure and readers.**
[`buildStepResults`](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
sets `attempt.native_rc` to nil: ABI 7 supplies PW's attempt status, not the
attempted syscall's native return. The
[API encoder](runner/Sources/PWRunnerCore/PWRunnerAPI.swift) emits the explicit
null when `result_source` is present. Found tests require that null to prevent
PW status from being presented as a native result; no production branch was
found that reads this attempt field. Nonnull values in constructed log
fixtures are not evidence of a production producer.

`sandbox_check.native_rc` is different: it carries validator results and feeds
`eligibleOrderedPrediction` and `eligibleOrderedStep`. That query field and
its ordering uses are outside this candidate.

**Reading cost.** The null explicitly records an unknown and makes the two
channel shapes more uniform. Without it, the attempt contract must still make
clear that `attempt.rc` is PW status and is not a native syscall return.

**Decisions remaining.**

- Decide whether to retain the explicit null or omit the unsupported field.
  If omitted, define absence as the current attempt shape rather than letting
  readers treat it as a malformed or incomplete result.
- Specify where the distinction between PW status and native return is stated
  for readers. Collecting a real attempt native return would be a different
  feature and ABI decision; it is not implied by either representation choice.

**If adopted.** Add the field to D5/R1's response removals and D3's reader
rules. Update the Swift type, builder and encoder, consumer shape checks,
Swift/Rust/Python fixtures, shape golden, size synthesis and guide. Controls
should continue to prevent PW status being interpreted as a native return and
preserve query-native-return and ordering checks. Removing this host-side null
requires no change to the worker ABI.

## S7. The observer's duplicate denial-line list

**Current structure and readers.** Both show and stream modes of
[`sandbox-log-observer`](controller/src/bin/sandbox-log-observer.rs) append to
`deny_lines` when they append to `deny_events`. The
[parser](controller/src/log_show.rs) stores that same accepted line in each
event's `raw_line`, in the same order, including show mode's event cutoff.
Found references construct or transport the list or assert its count; no
reader was found that recovers additional evidence from it.

The full `log_stdout` is different: it can contain non-denial context. Keeping
`deny_events[].raw_line` also preserves the accepted denial text without
having to reconstruct it from parsed fields. The
[observer-output budget](controller/src/log_capture.rs) explicitly accounts
for text duplicated across these representations.

**Reading cost.** A reader wanting only denial lines would project
`deny_events[].raw_line` instead of reading a ready-made list.

**Decisions remaining.**

- Decide whether to keep that convenience list or remove it. Specify whether
  the change covers both standalone observer modes and every report/error
  path, or only a controller projection. The controller retains the observer
  report, so projection alone does not eliminate the producer's duplication.
- Set the observer's version and reader policy for the chosen change. It has
  its own `observer_schema_version` (currently 1), and
  [`sandbox_log.rs`](controller/src/sandbox_log.rs) explicitly checks that
  version when admitting diagnostic evidence. The plan's response 13/envelope
  5 choices do not settle this nested tool contract.
- Decide whether to keep the existing output budget or revise it after
  measuring the chosen representation. A smaller record alone does not
  establish a new safe limit.

**If adopted.** Extend the plan's contract inventory with the observer
boundary, then update `ShowCapture`, the observer report type and all
constructors, transport/admission readers, replay fixtures and tool/guide
documentation. Verify both show and stream production paths, empty/error
reports, event cutoff and partial/truncated capture behavior. Check that raw
event text, order, membership and the additional context in `log_stdout` are
preserved. Reconcile the budget rationale and change generated limits only if
the budget decision actually changes a published value.

## S8. Constant log disclaimers

**Current structure and readers.**
[`SandboxLogWindow`](controller/src/sandbox_log.rs) emits four booleans that
are always false: `event_timestamps_available`, `exact_run_membership`,
`step_ordering` and `pid_reuse_protection`. Rust tests and
[Python window checks](tests/lib/log_capture_contract.py) require those
values. Correlation does not branch on them.

The [observer](controller/src/bin/sandbox-log-observer.rs) also emits
`layer_attribution: { "seatbelt": "observer_only" }`. Found references
construct the object in reports and fixtures; it does not encode a varying
attribution result. These are two different surfaces: controller capture
metadata and the nested observer report.

**Reading cost.** Each stored record currently includes reminders of limits
on its interpretation. Removing them transfers that explanation to whatever
documentation or remaining record the chosen design identifies; it does not
make the missing guarantees available.

**Decisions remaining.**

- Decide which, if any, of the four false flags should remain in every record.
  Decide the observer's attribution literal separately; the fields need not
  be retained or removed as one group.
- Specify where the omitted limits are communicated, and what absence means
  to a current reader. In particular, absence cannot silently become evidence
  of timestamps, exact membership, ordering, PID-reuse protection or sandbox
  attribution.
- Assign the version boundary for each selected removal. Controller capture
  changes affect the envelope; the observer literal raises the separate
  observer-version decision described in S7, even if S7 is not adopted.

**If adopted.** Amend D5 and the appropriate R1/R3/R4 inventories. Update the
controller and observer constructors, Rust/Python window-contract controls,
fixtures, and the guide and controller descriptions of denial evidence. Keep
controls on actual collection, correlation and attribution limits. Retire
constant-presence assertions only for fields whose removal is selected;
dropping a disclaimer must not broaden the claims of another field.

## S9. The whole-run target-removal calculation

**Current structure and readers.**
[`reportsTargetRemoval` and `comparisonEvidence`](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
look across run attempts for a successful worker `unlink` of a query's
submitted path, with the query-exclusion guard applied. The current conclusion
uses `sameTargetUnordered` to prevent an allow/success pair from becoming
`agreement`; `drift` projects that conclusion. The
[consumer](tests/lib/consumer.py) reconstructs the condition and checks the
corresponding limitation and conclusion. This is a present verdict-producing
use, not merely a self-validation loop.

The drift plan removes the verdict but retains this calculation as
`comparison.obligations.target_mutation.status`, with `none`, `unordered` and
`after_query`. D6.42 has already removed the proposed list of matching step
IDs. This candidate asks about the retained status and its run-wide derivation.

**Reading cost.** Without the derived status, a reader seeking this confound
would compare submitted query paths against the run's reported unlinks and
apply any chosen query-eligibility and ordering rules. Those inputs are
exposed in the reply. The current verdict's need for the calculation does not
settle whether the replacement has a task that warrants it.

**Decisions remaining.**

- Identify the reader task, if any, for a producer-calculated target-removal
  status after the verdict is removed. Decide whether to retain D1's status,
  narrow its derivation, or leave this cross-step interpretation to readers.
- If a derived status remains, specify its applicability: whether the current
  query-exclusion guard and distinction between unordered and after-query
  removals serve that task, and exactly what `none` means. If it is removed,
  specify which obligations and limitation checks disappear with it.
- Assign the surviving expectations of the existing mutation and ordering
  scenarios. Their file effects, validator records and release observations
  can still be evidence even when a verdict-derived assertion is retired.

**If adopted.** Revisit D1/D3, D6.26/42, R2/R4, I2's matrix inputs and ownership
table, the `ComparisonEvidence` plumbing, consumer checks, shape/size fixtures
and explanatory text together. Review the mutation-bearing matrix rows and
kept scenarios against their independent controls rather than deleting them
because a derived field disappears. Preserve the query-before-attempt release
barrier and its evidence. Any change to barrier or eligibility behavior still
requires the opt-in `order_barrier_mutations` control under `AGENTS.md`.

Until this decision is adopted, the plan continues to require the D1 status
and its existing query-exclusion rule. This document does not supersede them.

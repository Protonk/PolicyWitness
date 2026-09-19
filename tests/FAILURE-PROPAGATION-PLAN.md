# Failure evidence through the worker, runner, and controller

## Status: steps 0–4 complete; step 5 planned

Batches 0A–0C, 1A–1C, step 2 and their audit corrections are complete. Worker
ABI 6 retains atomic progress, precise failures and bounded diagnostics. Host
admission, child lifecycles, validator decoding/association and all controller
receivers retain their own observations. Response schema 7 and request schema 1
are separate contracts; capacities and production budgets remain unchanged.
The unfamiliar-code experiment preserves two distinct worker and JSON diagnostic
payloads, rejects structural invalidity, and detects temporary code filtering or
detail loss. It required no production behavior change or code registration.
Step 3's acceptance review and handoff are complete. Fixture-supplied fields,
actual host/receiver/process observations and real-worker effects are now
distinguished explicitly in its coverage claims. The retained executable sources
and signed app match; the [closeout review](out/failure-propagation-3/closeout/README.md)
records the evidence and documentation-only corrections. Step 4 is complete:
response 7 exposes scoped outcome comparisons, submitted attempt provenance,
simultaneous limits and later host path provenance; controller log candidates
retain their matching evidence. All 130 required catalog cases have passing
coverage, including 108 rerun against the final signed build and 22 unchanged
offline controls. The [step-4 handoff](out/failure-propagation-4/README.md) records
compatibility, original consumer-question dispositions, exact provenance and
remaining limits. Step 5 has not begun; its design acceptance, permanent
consumer-recovery review and final closeout remain separate.
[Routing inventory](FAILURE-PROPAGATION-INVENTORY.md) and
[step-3 evidence](out/failure-propagation-3/README.md) identify the accepted routes,
mutation failures, restored signed app and remaining coverage limits.

## Goal and scope

Organize failure evidence around the component that observed it. Worker progress,
reported failures, host actions, and process status are independent observations.
PW execution status and policy evidence are separate axes. A reader should be
able to distinguish a PW rejection, an observed library failure, a supervisor
action, and a missing or unusable reply without reconstructing the implementation
from an outcome string. An honest account of the available observations may leave
the cause unknown, including whether a post-apply gap reflects policy behavior
or an instrumentation defect.

Keep existing input capacities, output capacities, and timeout budgets unchanged.
This work does not decide how large or expensive a specimen PW should support.
Correcting attribution can change diagnostics and normalized outcomes; identify
those contract changes explicitly. Do not search for compiler drift specimens,
redesign the worker lifecycle, or carry out `tests/TEST-EQUIPMENT-PLAN.md`.

The aim is to reuse reporting and preservation paths across different failures.
Local checks will still need to know what they are checking. Transporting their
evidence should not require a new branch in every receiving layer. Sharing a
path is useful where the evidence has the same meaning; do not force unrelated
failures into one category merely to reduce the number of branches.

## Starting points

- `controller/tools/pw_probe_runner/pw_probe_runner.c`: policy reading, parameter
  setup, compilation, application, shared-memory publication, and early exits.
- `controller/tools/pw_probe_runner/pw_probe_runner_abi.h` and
  `runner/Sources/PWRunnerCore/CWorker.swift`: shared layout, publication rules,
  input validation, policy-pipe transfer, deadlines, and child reaping.
- `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift`: `classify`, step-result
  assembly, and the join between worker and validator observations.
- `runner/Sources/PWRunnerCore/ValidatorClient.swift`: batch transport and failure
  returns that already retain partial output and process metadata. Reuse the
  partial-result shape, not its unchecked termination/reaping implementation;
  validator lifecycle repair belongs to step 2.
- `runner/Sources/PWRunnerCore/PWRunnerService.swift` and `PWRunnerAPI.swift`:
  host admission failures and the runner's JSON result types.
- `runner/Clients/PWRunnerClient/main.swift`: reply-byte forwarding and locally
  generated XPC failure results.
- `controller/src/runner_client.rs`, `utils.rs`, and `run_flow.rs`: captured
  output, JSON parsing, the outer envelope, and startup diagnostics.
- `controller/src/sandbox_log.rs` and
  `controller/src/bin/sandbox-log-observer.rs`: captured denial events and their
  correlation with process/step evidence; `run_flow.rs` synthesizes `first_deny`.
- `controller/src/bin/sbpl-check.rs` and `controller/src/policy_check.rs`: fallback
  compilation diagnostics, including the helper's own source-size rejection.
- `runner/Sources/PWRunnerCore/SandboxApply.swift` and
  `runner/Tests/PWRunnerCoreTests/SandboxApplyTests.swift`: a Swift apply helper
  with unit-test callers only; its tests do not establish C-worker coverage.
  `computePolicyHash` in the same source file has a separate, live role.
- `runner/Sources/PWRunnerCore/Signals.swift`: unused signal-observer helpers.
  The live per-step producer is `CWorkerOrchestrator.zeroSignalResult`, which
  supplies zero counts without observing that channel.
- `runner/AGENTS.md`, `tests/README.md`, and `tests/catalog.json`: test boundaries,
  override rules, canonical case registration, and evidence retention.

Useful existing protection lives in `runner_abi_layout`, `runner_c_worker_harness`,
`runner_unit`, `runner_outcome_bad_request`, `runner_outcome_runner_timeout`,
`runner_ready_byte_resilience`, `runner_validator_failure`, `validator_batch_mode`,
`source_drift`, and `witness_contract`. Trace individual assertions before deciding
whether to extend a case or add a complementary one.

The `runner_unit` summary alone does not establish real-worker coverage.
`CWorkerTests` and `CWorkerValidatorTests` can print `SKIP` and return when their
selected binaries are missing; `TestKit.run` then counts that return as a pass.
The catalog requires `swift` and `clang` for this suite; selecting it alone
does not trigger the dispatcher's app-integrity inspection. Apply the live-test
evidence requirements under [Verification and handoff](#verification-and-handoff)
before crediting these cases.

For compilation failure, `runner_c_worker_harness/compile_failure` observes real
C-worker publication and exit. In
`runner/Tests/PWRunnerCoreTests/CWorkerValidatorTests.swift`, the case
`postApplied hook does not fire when compile fails` drives the real worker through
the Swift host driver and checks validator-hook suppression. Neither establishes
compilation diagnostics reaching the CLI; retain both while adding that coverage.

## Proposed observer contract

The first rule is that `normalized_outcome` describes whether and how PW completed
its work. It must not assign an unsupported policy cause or imply an access
decision. Each policy claim needs its own supporting observation. Observer records
can contain predictions, attempt results, or kernel denial events without turning
them into a cause of run termination. A post-apply reporting gap alone establishes
neither sandbox interference nor an instrumentation defect.

The ownership rules below guide acceptance tests; exact public sub-objects and
field names remain open. Preserve existing subprocess blocks as authoritative
where they already serve this purpose. Avoid duplicating facts into several
mutable representations. A layer can summarize another observer's evidence, but
must not rewrite that observer's account or imply an unsupported causal order.

| Observer | Evidence it owns |
| --- | --- |
| Worker | Published progress, failed operation, meaningful native result, and any published diagnostic detail |
| Runner host | Admission decisions, spawn/pipe/readiness observations, deadlines, termination requests and their results, successful reaping, and worker stderr if capture is implemented |
| Validator | Emitted check results and validator diagnostics; the host separately owns transport loss and process observations |
| Sandbox log observer | Captured kernel denial events and capture status; the controller separately owns correlation with run observations |
| Runner client | Received reply bytes or its own XPC error/timeout observations |
| Controller | Client invocation, capture and parsing observations, local rejection or truncation, correlation evidence, and the outer execution summary |
| Fallback `sbpl-check` | Its own admission or compilation result, independent of the missing worker reply |

The rules below apply even when only some observers can report.

- A reported failure carries its producer, operation, diagnostic code/domain,
  and useful detail. Native return values and errno are present only when the
  corresponding call result was observed and the value is meaningful.
- A last confirmed stage is an observation, not proof of the exact instruction
  where a process stopped. Missing publication does not prove a call never ran.
  Progress evidence must remain useful when no failure record was published.
- An absent record differs from a published record containing zero values.
  Incomplete, malformed, or incompatible records must not become library results.
- A supervisor records its own deadline or cleanup action separately from a
  child's reported failure. Both may exist; cleanup must not erase prior evidence.
  Distinguish requesting termination, the system call's result, and a process
  status actually obtained by reaping. Zero-initialized wait status is not evidence.
- A receiver that rejects, truncates, or cannot decode a reply reports that local
  boundary failure. It must not assign an unobserved cause to the sender.
- Size evidence identifies its units and whether a count is exact or a lower
  bound. Reading enough bytes to reject a stream does not reveal its full length.
- A structurally valid diagnostic can survive without its code being recognized
  by the receiver. `normalized_outcome` summarizes evidence; it does not replace it.
  Document summary precedence once, including concurrent failures, without using
  precedence to discard another observer's evidence.
- Each channel's valid evidence survives independently. A completed prediction
  remains evidence when its attempt never finishes; a kernel denial event may
  concern an operation that killed the worker before it published an attempt
  result. Attempt completion alone does not make a permission failure a proven
  policy denial. Missing observations do not establish agreement or disagreement.
  Do not blanket-reset valid step evidence on run failure.
- Diagnostics themselves may be bounded. Specify publication validity and any
  truncation explicitly so a shortened message remains distinguishable from a
  complete one. No design can guarantee delivery after every possible process or
  transport failure; the closest surviving observer must state what it knows.
- A signal after application, without a host kill, does not establish that the
  sandbox sent it. The worker's self-signal test seam produces that same shape.
- A PID-matched denial does not by itself explain termination. Correlation and a
  causal conclusion require distinct criteria. Log capture disabled, unavailable,
  and completed without a match are different observations; none proves that
  policy played no role. Optional log evidence must not change the underlying
  execution status merely by becoming available.
- A fallback compilation result describes that helper's execution. It cannot
  establish how far a missing worker progressed or why its reply was lost.

## Work sequence

### 0. Correct unsupported attribution using the existing ABI

Correct the existing evidence contract before adding new worker fields. This
step spans the host driver, classifier, JSON consumers, and log correlation.
Execute three sequential batches: 0A defines the interim contract and captures
the regression, 0B repairs host observations, and 0C applies the corrected
classification and public evidence semantics. Keep one step-0 acceptance gate:
all required contracts and checks below must be complete before step 1A begins.
Existing worker publications are sufficient for this limited correction; keep
worker ABI version 5 unchanged throughout all three batches.

Outcome-label changes and their dependent correlation changes belong together
in 0C. Publish response version 5 together with the explicit signal null and
corrected outcome semantics in that batch. Neither 0A nor 0B establishes the
accepted step-0 public contract. The new CLI witness remains an explicitly
expected failure through 0B; retain its actual failed result without suppressing
it or marking it passed. Record intermediate results and remaining work in the
current execution state at each handoff.

#### 0A. Define the interim contract and capture the regression

- [x] Write an interim evidence/classification table before changing production
  behavior. Cover absent publication, inconsistent flags, pre-apply exit and
  signal, observed deadline expiry, reported failure plus cleanup trouble, and
  completed reports followed by abnormal or unconfirmed process disposition.
  Specify summary precedence for concurrent failures without discarding their
  independent evidence. Identify the required host observations and proposed
  JSON locations, using authoritative subprocess metadata. Keep this table as
  the specification for 0B's observations and 0C's classifier controls.
- [x] Include the meaning of `runner_sandbox_denied` in this review. Decide and
  document interim outcome semantics and compatibility explicitly. A post-apply
  signal does not prove kernel sandbox attribution, and no progress evidence added
  in later steps changes that. Do not retain the inference merely because an
  existing test expects the label.
- [x] Audit the production reachability of tests credited with protecting these
  decisions. Credit host interpretation with constructed inputs, real C-worker
  publication, and CLI forwarding separately. Assign required live-boundary
  coverage to the witness in 0A, host-driver controls in 0B, and classification
  and public-contract controls in 0C. Keep coverage claims aligned with the
  implementation. Identify which Swift cases require built children and verify
  their actual execution in retained logs; a passing `runner_unit` summary that
  includes an internal `SKIP` does not complete their acceptance rows.
  `SandboxApplyTests` exercises the unused Swift helper only; do not extend that
  helper to imitate the new production reporting model. Removal of the helper,
  its helper-specific error type, and its tests is separate cleanup outside this
  effort. Preserve the live `computePolicyHash` function in the same source file.
- [x] Add one CLI contract case that pins the first observer rule end to end:
  `tests/suites/witness_contract/pre_apply_failure_reports_no_policy_verdict.sh`.
  Use a populated plan under a policy that would deny one probe and allow
  another, with `worker_pre_ready_hang_ms` and `worker_timeout_ms` set so the
  host gives up before application. Both overrides already exist; this case
  requires no new request seam. Choose the delay to exceed the fixed 1s
  ready-byte wait, the overridden sentinel, and the 1s exit grace by a wide
  margin, and run with `--no-log-capture`; log correlation independence belongs
  to the correlation control in 0C. The seam sleeps after successful compilation
  and optional profile capture, before the ready byte and application. It tests
  absence of published application evidence, not that compilation never ran or
  failed; neither the override nor a missing ready byte is a native call result.
  Assert absence rather than a specific outcome name, so the case survives later
  renames: `normalized_outcome` is not
  `ok`, `sandbox_apply_failed`, `bad_policy`, or `runner_sandbox_denied`; the
  summary and any structured failure record state no apply or compile return
  value; `sandboxed_after_apply` is not true; `validator_subprocess` is absent or
  null; every step has no allow/deny prediction, a missing-evidence attempt outcome
  with null errno, and null drift; `runner_sandbox_diagnostics` makes no cause
  claim; `runner_subprocess` and both mirrored overrides are present. Run the
  same specimen without overrides as a positive control and require the deny
  prediction and permission-failure attempt that the failure run must not contain
  (response 7 retains directional consistency with `drift=null`; the step-0
  accepted response-5 baseline pinned `false`), so the absence assertions are not vacuous. Assert that
  neither run claims that the sandbox caused termination, and that every step
  in both runs contains `deny_signal: null`, without measured counts.
  Write the case before the classifier change so it fails on the current
  attribution and passes after. Retain the unsupported-attribution assertion
  failure independently of expected schema/signal-shape mismatches; a version
  assertion alone is not the required before-change evidence.
  Register it in the suite `run.sh`, `tests/catalog.json`,
  `tests/COVERAGE.md`, and the suite README. Record, without asserting, whether
  the per-step prediction shape distinguishes a validator that never ran from
  one that answered short; that decision belongs to step 1A. Currently both use
  `sandbox_check.outcome="error"`, synthetic `rc=0`, and the same missing-verdict
  message for supported queries. This is not an observed sandbox_check return.
- [x] Document in `runner/AGENTS.md` the narrow exception to the exact-outcome
  assertion recipe for this new evidence-focused witness case. Its absence
  assertions supplement classifier tests that pin the chosen outcome mapping;
  keep the artifact, override-mirroring, and structural assertions. Other
  override-driven cases retain their exact-outcome checks.

Exit condition: reviewable interim contract decisions, registered witness and
positive control, and retained baseline evidence showing unsupported attribution
independently of schema/signal-shape mismatches. Retain the positive control's
prediction and attempt evidence even though its new signal-null assertion is
expected to fail before 0C. No production behavior is changed in this batch.

The [interim contract and reachability audit](FAILURE-PROPAGATION-CONTRACT.md)
specify 0B/0C's observations, classification and compatibility. The
[0A evidence index](out/failure-propagation-0a/README.md) links the signed build,
actual failing witness, positive control and executed live Swift cases. This
completes 0A's exit condition only; the step-0 public acceptance gate is pending.

#### 0B. Repair host lifecycle observations

Implement the host observations required by the 0A table before changing the
classifier. Keep the existing outcome vocabulary, response version, and signal
shape until 0C; new observation fields must be additive. Document their producer,
validity, and JSON representation beside the authoritative definitions.

- [x] Repair the host's polling/cleanup observations before changing their
  classification. Record why polling stopped, including sentinel deadline expiry
  separately from any later termination request. Retain termination-call results
  and report exit/signal status only when `waitpid` actually reaped the child;
  zero-initialized wait storage is not a clean exit. Carry these host observations
  through `CWorkerOutput` and the CLI, reusing authoritative subprocess metadata,
  and document their validity and meanings beside the relevant definitions.
  Preserve the existing exit grace duration and specify finite handling of
  failed termination/reaping calls. A failed termination request must not lead
  to a blocking wait on a possibly live child; failed or interrupted reaping
  must not manufacture status. Test that these error paths return with cleanup
  observations and any missing process status stated explicitly. Report any
  unreaped-child limitation; this repair does not add a global lifecycle timeout.
  These repairs require no worker ABI change and belong in this batch. The
  policy-write failure path's evidence preservation remains step 1C work.
- [x] Correct the existing `apply_rc`, `apply_errno`, and `done` comments in
  `pw_probe_runner_abi.h` in this batch: describe their actual producers and
  publication validity, including `done` on pre-apply failure. Correcting these
  descriptions requires no ABI revision. Trace `sandbox_create_params`,
  `sandbox_set_param`, compilation, and the defensive parameter NUL check
  separately; the last follows forced string termination and is not evidence
  of a reliably reachable specimen failure.
- [x] Add host-driver controls for deadline expiry followed by voluntary exit
  during the grace period, a completed report followed by cleanup termination,
  completed reports followed by an independent signal or nonzero exit, and failed
  termination/reaping calls. Exercise lifecycle observations through the host
  driver; use narrow test-only OS-call controls where real failure is unreliable,
  not result-forcing request overrides. Deadline detection must not depend on
  SIGKILL, and failure to obtain wait status must leave process status absent.
  Use driver and JSON encoding controls to establish the observations needed by
  the classifier rows in 0C.

Exit condition: host-driver and encoding controls establish trustworthy polling,
termination, and reaping observations, including explicitly missing process
status. Verify their CLI forwarding through a normal signed build. Preserve
existing budgets and document any unreaped-child limitation. The 0A witness
remains an expected failure because classification and signal semantics are
still pending; this batch does not satisfy the step-0 acceptance gate.

#### 0C. Apply corrected classification and public evidence semantics

Use the 0B observations to implement the 0A table. Change unsupported outcome
attribution together with dependent log correlation, and publish response version
5 together with the signal-null contract. Complete the consumer, documentation,
and coverage updates against this combined public contract.

- [x] Stop treating unpublished `apply_rc`/`apply_errno` storage as a reported
  failure. For legacy pre-apply failures, require the worker's `done` publication.
  Even then, `apply_rc = -1` can describe parameter setup or compilation; the
  interim diagnostic must not claim an observed apply return when it cannot
  distinguish the operation. A published zero or inconsistent flags do not
  establish failure either. Successful application has its own `applied` marker.
- [x] Distinguish pre-apply exit, signal, and host-enforced deadline using the
  confirmed observations. A clean exit without completion does not establish
  a timeout. A published failure followed by cleanup trouble must retain both
  observations; do not unconditionally let a later kill replace an earlier report.
  Include `applied=true, done=true` followed by a nonzero exit, a signal, or
  failure to obtain wait status. The current classifier can fall through to `ok`
  in these states. A completed report must survive, but does not establish clean
  process completion; an abnormal or unconfirmed disposition must not yield `ok`.
- [x] Add classifier rows for absent publication, inconsistent flags, pre-apply
  exit and signal, pre-apply host termination, reported failure plus cleanup
  trouble, and completed reports followed by abnormal or unconfirmed disposition.
  Pin the 0A table with constructed inputs using the observations established in
  0B. Passing these rows does not replace the host-driver acceptance evidence.
  Use the existing pre-ready delay seam for the real CLI deadline case begun in
  0A, and require it and its positive control to pass under the completed contract.
  Add a correlation control with an ordinary denial followed by unrelated
  termination: retain both observations without claiming a sandbox kill. Preserve
  existing successful, post-apply timeout, and partial-result contracts.
- [x] Replace the fabricated per-step `deny_signal` zero record with an explicit
  JSON null: every new `steps[]` entry must contain `"deny_signal": null`.
  The C worker does not observe this channel, so successful and failed runs
  alike must not publish measured signal counts. Make `PWRunnerStepResult`
  support absence and explicitly encode the null; changing only the producer
  is insufficient because the current field is non-optional. Keep decoding of
  legacy signal objects for old stored replies without converting their zeros
  into newly observed evidence. Implementing signal collection or removing the
  unused `Signals.swift` helpers is outside this effort.
- [x] Advance the runner response `schema_version` from 4 to 5 for the changed
  signal shape and corrected outcome semantics. This response version is separate
  from request versions, the outer controller envelope, and worker ABI version 5,
  which step 0 does not change. Update all response emitters, including client
  XPC-error results, public documentation, fixtures, checkers, and exact version
  assertions such as `runner_use_c_worker/run.sh`. Document the outcome mapping
  and reader compatibility; do not claim that old typed readers accept null in a
  required object field. Repository readers should retain support for old stored
  replies where they already have it. External consumers are not inventoried:
  publish the changed contract rather than assume they accept it or defer the
  correctness repair pending an unspecified consumer audit.
  Preserve the existing semantic absence convention for optional subprocess
  objects: omitted and explicit null both mean no value. Tests must accept both
  there. The new per-step signal null and existing per-step errno/drift nulls
  are explicit key-presence contracts, not merely that semantic convention.
- [x] Decouple termination/log correlation from a prior sandbox-cause label in
  the same batch as changing that label. Capture currently uses the top-level
  reply PID when enabled; that PID can belong to the host or client when no worker
  exists. Resolve worker identity from authoritative `runner_subprocess` metadata
  before worker correlation, and never substitute a host/client PID. The current
  outcome gate selects the `first_deny` summary, not observer invocation.
  Use observed process/application facts to report abnormal termination and
  correlated events separately. Preserve capture for successful runs as well.
  Adapt the former `runner_sandbox_diagnostics_on_denied` case (now
  `tests/suites/witness_contract/worker_termination_and_log_correlation.sh`)
  around confirmed termination, the chosen correlation representation, mirrored
  overrides, and observer invocation. Update its registration if renamed or
  split; retain CLI coverage of controller synthesis and capture invocation.
- [x] Define correlation criteria and their limits, including process identity,
  the capture window, and event relevance. A first PID match can be an ordinary
  denied probe followed by an unrelated crash or self-signal. Stronger causal
  attribution requires explicit supporting evidence beyond PID matching. Keep
  capture-disabled, unavailable, and no-match results distinct, with the same
  underlying execution status across those conditions.
  Audit both `first_deny` and `match_step_denies`: the latter currently accepts
  path matches when an event lacks a PID and does not require operation agreement.
  Require a confirmed worker PID for worker correlation; retain unmatched events
  as observer evidence. Define operation relevance before attaching an event to
  a step, including any supported operation aliases. Derive relevant operations
  from the submitted attempt's kind/action, joined to the reply by step ID:
  sandbox_check queries and attempts are independently routed, so the query's
  operation is not authoritative for what was attempted. The current reply's
  attempt object omits kind/action; the controller retains the submitted request
  and can use that provenance without adding duplicate authoritative fields.
  Keep query filter values separate from attempt targets and observed paths.
  The existing `prediction_target_is_independent_of_attempt_target` witness case
  protects this routing distinction; add a correlation control in which query
  and attempt operations differ as well.
  Do not treat a shared path alone as step identity. Even matching worker PID,
  operation, and path cannot distinguish repeated identical attempts without
  further observations. Represent such matches as ambiguous candidate
  associations, not unique step occurrences; retain the event once in observer
  evidence even if several steps reference it. Pin this with repeated-attempt
  controls and document the chosen representation.
  The current observer uses a trailing `--last` window and parsed events have no
  structured timestamp. Report that window and
  its limits; do not claim exact run membership, step ordering, or protection
  against PID reuse without the observations needed to establish them. Test
  missing/mismatched event PIDs, a host/client-only reply, and different operations
  on the same path, as well as capture availability and successful-run capture.
- [x] Correct missing-attempt prose in the builder and public/test documentation.
  An absent or incomplete slot establishes no completed attempt result, not that
  the worker never reached the operation. If `not_run_worker_died` remains as a
  compatibility spelling in step 0, explicitly document that limited meaning;
  settle its final spelling with the step-1A evidence contract. Keep null errno
  and drift when no result supports a comparison.
- [x] Complete the dependency updates below and verify `source_drift` alongside
  the affected unit and CLI cases before handing off step 0. Recheck the listed
  artifacts against the final diff; this inventory is not an exhaustive search.

Exit condition and step-0 acceptance gate: the new CLI witness and positive
control pass, the host-driver and classifier controls agree, and existing
success, timeout, and partial-evidence contracts remain protected. Complete the
dependency checks below, including `source_drift`, and retain signed-build CLI
evidence. Do not begin step 1A until this gate passes.

Step-0 dependency checks (paths below identify existing artifacts):

| Artifacts | Required update or verification |
| --- | --- |
| `runner/Tests/PWRunnerCoreTests/HostOutcomeClassifierTests.swift`, `CWorkerTests.swift`, and `EnvelopeInvariantTests.swift` | Pin the interim classifier table, retain real-worker signal-seam coverage, and update outcome constants/prose while preserving subprocess-presence and process-status assertions. |
| `controller/src/run_flow.rs`, `controller/src/sandbox_log.rs`, and observer tests in `controller/src/bin/sandbox-log-observer.rs` | Exercise worker identity, revised correlation gate, attempt-derived operation relevance, repeated-attempt ambiguity, and capture-window limitations; keep correlation distinct from cause and preserve capture for successful runs. |
| `tests/suites/sbpl_allowdeny_consistency/check.py`, `tests/suites/blackbox_e2e/validate_run.py`, `tests/suites/blackbox_menagerie/checker_controls.py`, and `tests/fixtures/blackbox_e2e/` | Replace assumptions of measured `deny_signal.delta == 0` with the chosen unavailable-channel contract; update fixtures and checker controls while retaining their other evidence assertions. Include the signal record constructed by `EnvelopeInvariantTests`. |
| `PWRunnerAPI.swift::NormalizedOutcome`, `tests/COVERAGE.md`, and `tests/suites/source_drift/check.py` | Keep outcome constants and matrix rows in bidirectional agreement, and retain a matrix row for every `runner_outcome_<name>` suite. Run the existing `source_drift` gate; preserve its checks. |
| `PWRunnerAPI.swift::PWRunnerRunResult` and `PWRunnerStepResult`, `runner/Clients/PWRunnerClient/main.swift`, `EnvelopeInvariantTests.swift`, and schema assertions/fixtures throughout `tests/` | Pin response version 5 and literal signal null, retain legacy reply decoding, and keep optional subprocess absence distinct from explicit per-step null requirements. |
| `PolicyWitness.md`, `controller/README.md`, `runner/README.md`, `runner/AGENTS.md`, and `tests/README.md` | Update outcome, signal-evidence, diagnostics, and override descriptions to the implemented contract. Check the adjacent `runner_failed` description too. Describe the pre-ready delay together with its timeout budget: it already can fail under a short deadline, while the resilience case with sufficient budget must remain `ok`. |
| `tests/suites/runner_ready_byte_resilience/`, `tests/suites/runner_c_worker_harness/`, `tests/suites/runner_use_c_worker/`, and `tests/suites/witness_contract/` | Update affected README prose, shell assertion messages, and harness comments that encode the old attribution. Preserve assertions on successful execution, completed probes, worker publication, and post-apply timeout evidence. |

This step removes claims unsupported by the existing evidence. It does not make
the legacy status fields sufficient to distinguish all failed operations.

### 1. Establish observer-owned progress and failure reporting through to the CLI

#### A. Specify progress and publication, then implement the minimal record

Retain exact-version ABI rejection without dual-version encoding or decoding.
Aim for one coherent ABI revision for step 1: settle the storage and publication
contract for both the minimal record and the diagnostic region here, including
an explicit state for no diagnostic published. Step 1B can implement diagnostic
production and forwarding separately. If the diagnostic contract cannot be
settled responsibly here, a second revision in 1B is acceptable.

A revision under construction can be refined within an unfinished implementation
batch without incrementing the version for each edit. Rebuild host and worker
together and verify their definitions agree; equal version numbers alone do not
establish compatibility between intermediate builds. Record whether the revision
is under construction or accepted in the current execution state. Once the ABI
contract is accepted at batch completion, incompatible changes to its layout,
field meanings, or publication requirements need a new version. Refactoring,
tests, fixes within the contract, and diagnostic codes covered by its
unfamiliar-value rules do not inherently require a bump. The version identifies
a contract, not an edit count.

- [x] Define a small set of useful worker milestones. For each, state whether it
  means an operation started or completed and what an acquire reader can rely on.
  Specify optional transitions and failure exits. Readiness can fail while the
  worker proceeds; `done` is also published following compilation failure. Do not
  infer successful application from a simple ordering of all stage numbers.
- [x] Write a small state table before consolidating progress and failure fields.
  Include death between a completed stage and the next started stage, a returned
  failure, a readiness failure followed by continued execution, and repeated
  parameter calls. Distinguish an operation returning from its succeeding, and
  identify which call failed inside a coarse stage. A generic nonzero-result rule
  is insufficient: compilation fails by returning NULL.
- [x] Settle the minimum failed-operation record and its publication rules,
  independently of diagnostic text. Distinguish no report, a valid report with
  zero values, and an incomplete or incompatible report. Keep native call results
  distinct from PW's own diagnostic codes. An unfamiliar stage value must not be
  interpreted as successful application merely because its number is larger.
  Retain explicit operation/result evidence unless the state table demonstrates
  an equally clear consolidated encoding. Existing `done` may publish a terminal
  payload without an additional validity word, but payload validity, failed
  operation, and terminal success/failure still need unambiguous meanings.
- [x] Before implementing new or changed cross-language fields, record their
  contract beside the authoritative ABI/API definitions or in existing contract
  documentation. For each field specify its producer, publication/validity
  condition, type (including width and signedness), units, Swift interpretation,
  and final JSON path and type. Include absent versus zero (and omitted versus
  null), unfamiliar values, and whether each receiving boundary decodes or forwards
  it unchanged. Reference existing layout definitions rather than copying offsets
  into a second schema. Link the chosen contract locations in the current
  execution state below; keep them current when later batches change fields.
- [x] Implement worker publication in preallocated, pre-touched shared memory.
  Publish payload validity with release/acquire ordering; document its relation
  to progress, `applied`, `done`, and per-slot completion. Keep the post-apply path
  free of new allocation and diagnostic I/O dependencies. Failures before a usable,
  compatible mapping exists still need a supervisor-only fallback.
- [x] Review when the host observes progress and takes its final snapshot around
  reaping. The current driver snapshots flags and slots before requesting exit
  and does not refresh them after cleanup; publications during grace can be lost.
  Account for those publications and preserve confirmed slots. Keep the reason
  polling stopped separate from the final snapshot: a late `done` must not erase
  an already observed deadline. Record readiness already observed by the host.
  Preserve the step-0 distinctions among deadline expiry, termination requests
  and their results, and successfully obtained process status when joining the
  new worker evidence.
  Recheck `decodeProfileCapture` against the confirmed observations while
  preserving its requirement for successful application before exposing a
  capture. Refusal to expose an unconfirmed capture is not itself an observed
  application failure; keep that distinction in its diagnostic wording.
- [x] Carry worker evidence and host observations through `CWorkerOutput`, the
  orchestrator, runner JSON, client forwarding, and controller envelope. Reuse
  the client's byte forwarding and the controller's opaque JSON retention where
  they already work: the client writes received reply bytes without decoding a
  runner result, and the controller retains `serde_json::Value` within its capture
  limit. Test those paths with unfamiliar fields/codes; do not add typed
  reconstruction or diagnostic-specific branches to these receivers merely to
  forward the new record. Focus recognition-dependent preservation checks on
  shared-memory decoding and runner assembly, while still proving client and
  controller forwarding through the CLI. Distinguish failed operations in the
  evidence before deciding which merit separate top-level outcome strings.
- [x] Settle the per-step missing-evidence contract before extending the result
  types. Distinguish a validator that was not invoked from one that ran but did
  not supply this step's verdict, using run/step observations without duplicating
  subprocess authority. The current shared error shape and synthetic `rc=0`
  must not imply an observed sandbox_check return. Specify whether compatibility
  sentinels remain, how they are identified as synthetic, and which fields carry
  observed native results. Settle the final missing-attempt outcome spelling and
  describe an incomplete slot as lacking a completed result, without claiming
  the attempt never started. Add controls for never-invoked and short-reply
  validators, and for an attempt that starts but never publishes completion.
- [x] Apply the ABI rule above and settle JSON compatibility before choosing
  offsets. The header's reserved space is an option, not a specification. Update
  the C/Swift definitions together, extend layout checks, and verify rejection
  of incompatible workers. Include a basic unfamiliar-diagnostic-code
  preservation control for the worker-to-CLI route. A separately built test
  producer selected through the existing `worker_executable_path` override can
  publish a controlled record using the batch's ABI contract, exercising the real
  host driver and forwarding path. Use the step-3 fixture constraints below;
  do not add a result-forcing request key or modify an inspected app to do this.

#### B. Prove reporting with compilation failure and add diagnostic detail

Use an ordinary SBPL syntax error as the central real-worker proving case. It
isolates a deterministic failed operation without requiring a policy-pipe failure.
Sparse-evidence cases remain separate acceptance obligations.

- [x] Show the compilation failure reaching the normal CLI, distinguished from
  parameter setup and an observed apply result. Keep the minimal operation/status
  change reviewable separately from diagnostic-text storage and forwarding.
- [x] Use a preallocated shared-memory text region as the primary route for
  PW-authored diagnostics after a compatible mapping exists. Implement the bounds
  and publication contract settled in 1A, or explicitly settle a further ABI
  revision if needed; make missing, partial, and truncated text explicit.
  Publishing reliable status must not depend on a successful diagnostic write.
- [x] Preserve existing early stderr diagnostics where shared-memory reporting
  is unavailable. The text region cannot recover diagnostics emitted before a
  usable mapping, direct dependency/runtime stderr output, or unpublished details
  lost in a reporting-path crash. A separate stream may retain context when the
  shared-memory mechanism itself fails. Record this coverage gap explicitly;
  preserving an emission does not establish that the CLI can collect it. This
  step does not add stderr capture.
- [x] Preserve and test the restriction on post-apply diagnostic syscalls and
  new allocation dependencies. If the existing stderr sites are routed through a
  helper that is silent after application, that helper must not disable the
  post-apply memory-only result/error publication. Existing per-step
  shared-memory diagnostics remain available after application.
- [x] Verify the compiler diagnostic reaches the CLI. For otherwise identical
  observed failures, controls with rich, missing, and truncated text must retain
  the same justified operation/status classification.

#### C. Retain sparse-evidence and competing-failure cases

Compilation failure is not sufficient acceptance for this step. The worker maps
and validates shared memory before reading source, so oversize-source rejection
can publish a record before exiting. Acceptance must exercise preservation of
that record through a simultaneous pipe failure.

The required interrupted-transfer case is a child that closes its policy-input
end or exits, causing a host write failure. It is distinct from a live child
that keeps the pipe open without consuming input. The current policy write is
blocking and precedes sentinel polling; the latter case has no host transfer
deadline. Adding one would change which phase an existing budget governs, even
if its numeric value stayed the same. Leave that liveness redesign outside this
effort and retain it as an explicit limitation in the step-2 inventory. Do not
describe broken-pipe acceptance or the client timeout as proof of bounded host
transfer. Cleanup after an observed pipe failure must use the step-0 termination
and reaping contract without an unbounded wait after a failed kill.

- [x] Exercise oversized source through the worker guard and account for its
  report, last progress, and process status. Fix the host's policy-write failure
  path to preserve evidence when a child closes its input or exits; do not discard
  its status or lose the report through EPIPE/SIGPIPE handling. Record local pipe
  failure and child evidence independently, retaining bounded cleanup.
- [x] Add a host-driver test for a child that closes its input or exits during
  transfer. Do not make it depend on an oversized specimen reaching the worker,
  so it stays valid if admission later rejects such input upstream. Test report-present and
  report-absent behavior at suitable boundaries, without requiring one
  timing-dependent race.
- [x] Include early failures before publication, unexpected termination, and a
  report followed by cleanup trouble. These remain first-class acceptance cases
  even when ordinary admission prevents a particular specimen from reaching them.
- [x] Cover failed mapping without classifying it as a host bug merely because
  no worker report exists. `map_region` failures in `fstat`, region-size checking,
  and `mmap` share exit code 3; process status cannot recover the missing errno or
  detailed reason. Preserve the actual observations and leave unavailable facts
  absent. Use a deterministic harness boundary for the failure.

Acceptance should cover the following observations, with expected facts written
before implementation. Exact diagnostic prose need not be fixed. The owning batch
first establishes each row; later batches must recheck rows whose evidence changes.
When implemented, replace `Pending` with the actual test file and case/function,
plus the canonical catalog ID for public cases. Where several tests establish a
row, identify which boundary each covers. Use the same test-entry convention for
the step-2 inventory and step-3 controls.

For step-0 rows shared across batches, 0A retains baseline failures and 0B
establishes host observations; 0C establishes classification and the combined
public contract. Row acceptance uses the combined evidence, not only an earlier
batch's checks.

| First owning batch | Case | Boundary to exercise | Evidence that must reach the consumer | Implemented test entry |
| --- | --- | --- | --- | --- |
| 1A | Ordinary successful specimen | Real worker through CLI | Existing attempt/prediction evidence; no fabricated failure record | `witness_contract/worker_progress_and_failure`, `check_worker_evidence.py` success branch (real worker/CLI, independent file bytes). |
| 1C | Source exceeds the existing worker cap at the worker boundary | C worker guard and host policy-transfer handling | Worker rejection and relevant byte limit; last progress and process evidence retained even if the policy pipe also fails | `witness_contract/worker_sparse_failure`, `check_worker_sparse.py` oversize branch; `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` real source guard. Real C source limit 262143 and simultaneous host EPIPE reach the CLI. |
| 1B | Ordinary SBPL syntax error | Real worker through CLI | An actual compilation failure and its diagnostic, distinguished from an observed application result | `witness_contract/worker_progress_and_failure`, `check_worker_evidence.py` real compile and diagnostic fixture branches; `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` text availability and deny-default memory publication. |
| 1A | Observed application failure | C producer and Swift interpretation; deterministic harness if no reliable live specimen reaches it | Operation and meaningful native result retained | `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` production C apply failure; separately compiled real C main with only apply return controlled. |
| 0C (baseline in 0A) | Existing pre-ready delay exceeds the worker budget | Real CLI with existing delay override | The host's deadline/termination observations, with no invented library failure | 0A baseline: `witness_contract/pre_apply_failure_reports_no_policy_verdict`, `check_pre_apply_failure.py::main` / `common_evidence`; retained attribution failure. 0C: all witness groups pass under response 5; `lifecycle_observations` retains the independent deadline/termination facts. |
| 0B (classifier in 0C) | Deadline expiry followed by voluntary exit during grace | Host driver and classifier controls | Observed deadline expiry retained without requiring SIGKILL; separately obtained exit status retained | 0B: `runner_unit/pwrunner_core_unit_executable`, `CWorkerTests` case `postApplyHangMs > sentinelTimeoutMs produces done=false`, including production subprocess encoding. 0C classifier verified in `HostOutcomeClassifierTests` and the corresponding live driver control. |
| 0B (classifier in 0C) | Failed termination/reaping calls | Host driver and classifier controls | Termination request and call result distinguished; exit/signal status absent unless successfully obtained by reaping | 0B: `runner_unit/pwrunner_core_unit_executable`, `CWorkerLifecycleTests` failed-kill, failed-reap, recovered/repeated EINTR, ECHILD and poll-error cases; `EnvelopeInvariantTests` compatibility controls. 0C classifier verified in `HostOutcomeClassifierTests` and the corresponding live driver control. |
| 0B (classifier in 0C) | Completed report followed by nonzero exit, independent signal, or unavailable wait status | Host driver and classifier controls | Published completion and step results survive; process disposition remains independent; run is not `ok` and claims no sandbox cause | 0B: `runner_unit/pwrunner_core_unit_executable`, `CWorkerLifecycleTests` completed-report exit-17, SIGTERM and failed-reap controls retain slots and encode independent disposition. 0C `runner_failed` classifier and preserved report/process JSON verified through the same driver controls. |
| 0C (baseline in 0A) | Failure before application under a policy that would deny a probe | Real CLI with existing delay and deadline overrides, plus an un-overridden positive control | Failure run has no allow/deny prediction, permission-failure attempt, or drift value; control produces the deny prediction and permission-failure attempt from the same specimen (baseline drift=false; response 7 directional consistency with null); neither run claims sandbox-caused termination; failure run retains process evidence and overrides | 0A baseline: `witness_contract/pre_apply_failure_reports_no_policy_verdict`, `check_pre_apply_failure.py::common_evidence` / `no_cause_claim`; 0A/0B retained real attribution failures. 0C: positive control, absence, attribution, lifecycle and signal-null groups all pass. |
| 0C | Unobserved per-step signal channel | Runner JSON encoding/decoding and real CLI failure/success controls, including the pre-apply case above | Response version 5 and literal `deny_signal: null` survive forwarding; legacy reply decoding remains supported and dependent checkers retain their other evidence checks | 0A CLI baseline: `witness_contract/pre_apply_failure_reports_no_policy_verdict`, `check_pre_apply_failure.py::signal_contract` fails separately for both runs; response version recorded as 4. 0C: response-5 literal null and legacy object decoding pass in `EnvelopeInvariantTests`; CLI witness and real client errors in `smoke/runner_caller_auth` pass. |
| 0C | Correlation with incomplete identity, irrelevant events, or repeated attempts | Controller correlation and CLI observer-invocation controls | No worker correlation from host/client PID or missing/mismatched event PID; relevance follows the attempt rather than an independently routed query; same-path unrelated operations do not match; repeated identical attempts retain ambiguity; availability and window limits are explicit | `unit/rust.unit`: `run_flow::tests`, `sandbox_log::tests`, observer parser controls; `witness_contract/worker_termination_and_log_correlation` with repeated denied writes, independent read queries, self-signal, disabled/enabled capture and successful-run capture. Passed; populated-event cases are deterministic unit controls when live capture has no match. |
| 1C | Unexpected worker exit without a report | Controlled child through host driver | Actual process status and absence of a report; unknown underlying cause | `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` early exit with no publication; real driver retains exit 17 and absence. |
| 1C | Failed mapping with no usable worker report | C worker harness and host process-status interpretation | Obtained process status and an incomplete account; no invented errno, detailed cause, or blame | `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` mapping failure; `witness_contract/worker_sparse_failure`, mapping branch. C production main with its mapping FD closed exercises fstat failure; host/CLI retain exit 3 without claiming the unavailable errno or detailed reason. Other map-region failure variants are not claimed as separately exercised. |
| 1C | Child closes policy input or exits during host transfer | Controlled child through host driver, independent of source admission | Host pipe error, available worker evidence, and reaped status or explicit failure to obtain it; this does not cover an open but undrained pipe | `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` closed policy input and pipe failure with failed termination; `witness_contract/worker_sparse_failure` close_report/close_absent. Input closure is independent of source admission. The failed-kill control exposed and now guards duplicate inherited pipe FDs. |
| 0B (classifier in 0C) | Completed report followed by cleanup trouble | Host driver and classifier controls for otherwise unreliable states; step 1C rechecks new worker failure records | Reported completion or failure and subsequent supervisor observations both survive; cleanup termination alone does not establish sentinel deadline expiry | 0B: `runner_unit/pwrunner_core_unit_executable`, `CWorkerLifecycleTests` completed-report cleanup-kill and published-legacy-failure cleanup cases, failed-kill/reap controls and actual subprocess JSON. 0C classifier verified; 1C `WorkerEvidenceTests` pipe failure with failed termination retains the new failure record, EPIPE and unconfirmed disposition independently. |
| 1C | Failure after completed probes | Real worker through CLI, with independent effect checks | Completed step evidence and independently checked effects survive | `witness_contract/worker_sparse_failure`, check_worker_sparse.py after_probes branch; real worker self-signal retains completed write/prediction and independently compared file bytes. |
| 1A | Unpublished or incomplete record | C publication and Swift shared-memory decoding controls | No payload fields treated as confirmed evidence | `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` publication gates and started-attempt poison controls. |
| 1A | Publication during cleanup after sentinel deadline | Host driver with controlled publication timing | Final confirmed records/slots survive; late completion does not erase the observed deadline | `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` cleanup publication and `CWorkerTests` late done during grace. |
| 1A | Missing prediction or incomplete attempt | Step assembly and JSON controls for never-invoked/short-reply validators and an attempt interrupted after starting | Missing evidence does not become a native return or a claim that an operation never started; absence reasons follow the chosen contract | `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` never-invoked/short-reply assembly and started-attempt controls; CLI witness checks native_rc null. |
| 1B | Same observed failure with rich, missing, or truncated text | Worker diagnostic publication, host decoding/classification, and CLI preservation | Identical justified operation/status classification across diagnostic availability | `witness_contract/worker_progress_and_failure`, `check_worker_evidence.py` real compile and diagnostic fixture branches; `runner_unit/pwrunner_core_unit_executable`, `WorkerEvidenceTests` text availability and deny-default memory publication. |

Use real worker failures and existing override boundaries for CLI coverage.
Use the C harness for publication/early-exit behavior and Swift unit tests for
states that cannot be reached reliably through existing seams, following
`runner/AGENTS.md`. A controlled child can establish unexpected termination;
its status is evidence about process handling, not sandbox policy behavior.
Publication claims need review of the synchronization protocol as well as tests.
Do not use a convenient syntax-error case as a substitute for early-exit and
missing-report coverage, or use synthetic transport records to claim production
failure attribution coverage. Record any boundary left untested; a passing
classifier test or unused Swift apply-helper test cannot complete a row that
requires C-worker publication or CLI forwarding.

This step is complete when a real compilation failure and its diagnostic reach
the CLI, progress remains useful without a report, and the pathological cases
retain their independently observed facts. Record changed outcome semantics and
any unresolved coverage gap. Adoption by additional producers follows in step 2.

### 2. Walk the known limits and seams, grouping failures by evidence ownership

Make a reviewable routing inventory before changing the remaining paths. For
each entry record the detecting component, evidence available there, current
loss or reinterpretation, intended reporting location, acceptance case, and
status. Add newly discovered boundaries during this walk. Listing a boundary
does not check it off; mark it complete only with implementation and acceptance
evidence, or record why it is explicitly deferred.

Split the walk into admission and runtime evidence loss. The tables below are a
starting inventory, not a claim of completeness. Recheck constants and execution
paths when implementing. String capacities count UTF-8 payload bytes, excluding
the terminating NUL where applicable.

Admission limits:

| Pending boundary | Current constraint or seam | Candidate route to examine |
| --- | --- | --- |
| Source size | 262,143 bytes (`POLICY_MAX` includes NUL) | Share the existing cap with host admission; retain and test the worker guard |
| Probe count and parameter count | 256 steps; 1,024 parameters | Shared host-admission reporting with field, observed count, and capacity |
| Worker string/argument storage | Step ID 63 bytes; target 511; parameter key 127 and value 383; 15 supplied exec args of 127 bytes each | Same admission route where appropriate, retaining units and offending field/step |
| Fallback `sbpl-check` | 4 MiB source cap; its `policy_too_large` outcome reaches `policy_check_status`, but the startup note prose reports any non-compile as failed | Helper-owned admission rejection; keep the distinction in the note prose as well |

Runtime evidence loss and observation boundaries:

| Pending boundary | Current constraint or seam | Candidate route to examine |
| --- | --- | --- |
| Policy transfer and early exit | Worker closes policy input or exits while host writes | Host pipe observations plus available worker report and process status; retain step-1 protection after admission changes |
| Open but undrained policy pipe | Blocking host writes precede sentinel polling; a live non-reading child need not produce EPIPE | Explicitly deferred liveness limitation under step 1C; no transfer deadline or claim of bounded transfer is added by this plan |
| Validator request framing and result association | 65,536-byte line buffer; overlong input yields a diagnostic with null step ID; classifier counts all records while step assembly drops unassociated ones | Preserve validator-owned diagnostics independently of the step join; record count alone does not establish prediction completeness |
| Validator reply byte decoding | Whole-stream UTF-8 conversion falls back to an empty string on any invalid byte, discarding valid preceding verdicts without a decode diagnostic | Host-owned decode failure with retained valid frames, byte evidence, and process observations; keep distinct from malformed JSON and an empty reply |
| Validator verdict structure | `verdictFromJSONObject` accepts any JSON object and extracts optional fields; assembly substitutes `rc=-1` when absent while retaining an `allow` or `deny` outcome | Receiver-owned structural rejection, distinct from JSON syntax failure and unfamiliar valid diagnostics; missing native results must not become predictions |
| Validator lifecycle | Partial-result return retains evidence, but kill/wait results are unchecked and zero-initialized wait storage is decoded | Apply the step-0 host observation contract to the validator, preserving verdicts alongside cleanup errors |
| Controller reply capture | Full subprocess output is collected before only a 1 MiB prefix is retained/parsed | Receiver-owned loss with exact received-byte count and retained-prefix count, distinct from malformed producer JSON; this is not a streaming memory bound |
| Execution budgets | Worker nominal 60s polling budget, synchronous validator hook with 30s I/O, client default 240s | Observer-owned deadlines with phase, process status, and partial evidence; readiness, policy transfer, and hook time are not one end-to-end worker deadline; `--timeout-ms` does not set all budgets |
| Readiness and child lifecycle | Ready-byte timeout, spawn failure, early exit, post-apply hang/signal, and cleanup grace | Distinguish synchronization hints, actual stops, and unexplained termination |
| Denial-log correlation | Optional capture with worker identity, attempt provenance and ambiguous candidate references | Independent correlation with observed execution facts; a matching denial does not establish termination cause |
| Early or uninstrumented stderr diagnostics | No usable shared-memory report, direct dependency/runtime output, or reporting-path failure | Deferred capture evaluation; process status alone cannot recover diagnostic detail |
| Optional compiled-object capture and exec output | 1 MiB capture region; 1,023 payload bytes per child output stream | Explicit unavailable/truncated evidence; optional capture failure must not become specimen failure |
| Earlier setup and transport | Request decoding, library loading, shared-memory/pipe setup, XPC loss, reply encoding/decoding | Reporting by the component that actually observed failure; fallback where no child report is available |

- [x] Trace each boundary to its final CLI representation, including diagnostics
  that are only emitted on stderr or replaced during cleanup. Use the existing
  validator partial-result behavior as a source of reusable patterns. Its
  `.failure(error, partial)` shape is useful, but is not evidence that its process
  status or result association is already correct.
- [x] Repair validator termination/reaping observations using the step-0 host
  contract. Retain termination-call results and obtain exit/signal status only
  from successful reaping; keep parsed verdicts when cleanup fails. Add driver,
  classifier, and JSON controls for failed kill/reap and abnormal exit after
  verdict production. An adequate verdict count must not conceal a process
  failure or an unconfirmed disposition. Do not infer clean exit merely from the
  driver's `.success` case.
- [x] Preserve validator diagnostics that cannot be joined to a step. The C batch
  reader emits one `parse_error` record with `step_id:null` for an overlong line
  and exits zero at EOF. Today that record can satisfy the classifier's expected
  count while being dropped by the step-ID join, leaving missing predictions
  under an `ok` summary. Retain the diagnostic at validator/run scope without
  inventing a step identity; account for expected step IDs and framing/transport
  failures rather than relying on total record count. Preserve the documented
  semantics of explicitly returned per-step errors or unsupported-operation
  results; distinguish those from missing or unassociated replies. Cover
  duplicate/unexpected IDs without a dictionary-construction crash or
  reassignment of evidence.
  Add a real validator-to-CLI case with an overlong encoded request between valid
  probes, keeping the worker's step IDs and attempt inputs within their caps and
  exceeding framing through an independently routed sandbox_check query field.
  Use a long query operation with a supported, resolvable path filter and short
  valid attempt inputs: current admission rejects an empty operation but does not
  cap its length. Do not rely on an overlong path value; `makeValidatorProbe`
  skips paths rejected by `pathFilterIsUnresolvable`, which can prevent the test
  from reaching the validator. Measure the serialized line including JSON framing
  and show that the middle query reached the batch reader's overlong-line guard.
  The framing diagnostic survives, both valid results keep their IDs,
  the unanswered step has no prediction/drift, completed attempts survive, and
  the run is not `ok`. Keep decoder controls separate from this production case.
- [x] Preserve valid validator frames before an invalid UTF-8 frame. The current
  `String(data: stdoutBytes, encoding: .utf8) ?? ""` conversion erases the whole
  stream on a single invalid byte; it cannot distinguish that boundary failure
  from an empty reply. Frame the bytes before decoding and retain preceding
  valid verdicts with their original step IDs. Report decoding failure as a host
  observation, with received-byte evidence and process metadata, without
  inventing a validator verdict or repairing invalid text into accepted JSON.
  Retain any independently observed I/O failure as well.
  Add direct decoder controls and a validator-fixture-to-CLI case containing valid
  replies followed by invalid UTF-8. Require retained predictions and completed
  attempts, missing prediction/drift for the unanswered step, and a non-`ok`
  summary identifying the decode boundary. Keep malformed-JSON and empty-reply
  controls separate. Include valid multibyte text split across read boundaries
  and an incomplete multibyte tail, so transport chunking is not mistaken for
  invalid encoding. These controls establish receiver behavior, not a claim that
  a normal validator produces invalid UTF-8.
- [x] Validate validator record structure separately from UTF-8 decoding, JSON
  syntax, and step-ID association. `verdictFromJSONObject` currently accepts any
  JSON object, including one with a recognized step ID and `"outcome":"allow"`
  but no `rc`; `buildSandboxCheckResult` then substitutes `rc=-1` while retaining
  the allow prediction. An expected ID or adequate record count cannot make that
  a valid observed verdict. Specify required fields and types for supported
  verdict and diagnostic variants beside the authoritative decoder/types before
  implementing validation. An allow/deny prediction must carry its observed,
  correctly typed native result; a missing, null, or wrongly typed result must
  not be repaired into a prediction. Preserve legitimate diagnostic variants
  that do not report a native call, including `parse_error` with `step_id:null`,
  and the documented semantics of per-step errors and unsupported operations.
  Keep structurally valid unfamiliar diagnostics transportable without a
  known-code-only allowlist; lack of recognition and malformed structure are
  separate conditions.
  Add direct decoder controls for missing/null/wrongly typed required fields,
  and a validator-fixture-to-CLI control with valid replies followed by an
  incomplete allow/deny record for an expected step ID. Retain valid predictions,
  completed attempts, and process observations; the invalid record supplies no
  prediction or drift, and the run is non-`ok` with a host-owned structural
  diagnostic. Contrast this with valid diagnostic records lacking native
  results and unfamiliar valid diagnostics. Retain bounded rejected-frame context
  with any truncation explicit, without presenting it as an accepted validator
  verdict.
- [x] Group changes around a shared reporting path and its evidence contract.
  First examine excess steps and excess parameters: keep their local capacity
  checks, but try to route both through the same host-admission failure record
  and forwarding code. The consumer should not need a case for each field.
- [x] Move the unchanged source cap into the shared contract and reject oversized
  source in host admission with field, actual UTF-8 length, and maximum. Verify
  C/Swift agreement, retain the worker's defensive check, and keep distinct tests
  for admission, the worker guard, and a child interrupting policy transfer.
- [x] Add acceptance cases for every member of a proposed group. Assert origin,
  affected field, actual/allowed values and units, process presence or absence,
  and retained evidence. Where byte boundaries matter, cover exact/over-limit
  and multibyte input; for NDJSON measure encoded framing, not just source text.
- [x] Review the diff for actual reuse. A shared checker alone does not show that
  production routing is shared. Record which inventory entries one change closes
  and why, or explain why distinct handling is needed. Closing several entries
  together is an aspiration, not a quota that justifies a generic framework.
- [x] Preserve distinctions among local admission rejection, child-reported
  failure, supervisor action, and reply loss. Avoid manufacturing worker records
  for host-only failures or relabeling a receiver's truncation as sender corruption.
- [x] Do not close the controller-capture entry merely because a truncation flag
  and parse-error label exist. Use valid producer JSON beyond the existing cap to
  prove the result identifies the controller's own loss of evidence. Contrast that
  with malformed producer output within the cap in an independent control.
  `Command::output()` has already collected the full stdout byte vector before
  `truncate_output` selects the prefix. Record its exact received length and the
  retained byte length before lossy UTF-8 conversion, together with the unchanged
  cap and the local truncation diagnosis. Do not report that known count as only
  a lower bound, call the cap a streaming allocation bound, or increase the parse
  budget. Include a multibyte boundary control so byte counts do not become
  character counts or counts of replacement characters.
- [x] Recheck the correlation path revised in step 0 against the observer records
  adopted in step 1. Preserve independently obtained predictions and kernel events
  when an attempt lacks a completed result. A post-apply gap must not default to
  either policy interference or an instrumentation defect.
- [x] Evaluate capture of early or otherwise uninstrumented stderr diagnostics
  as a bounded, deferred question. Shared-memory text does not close it. Capturing
  stderr adds no worker writes by itself, but its destination, resources,
  draining, and teardown can affect execution, and any proposed capture must
  justify those costs before joining normal runs. Specify pre-mapping coverage,
  direct dependency output, blocking/backpressure, dropped bytes, EOF, and
  cleanup; ignoring SIGPIPE does not prevent a full pipe from blocking. If
  pursued, use a limited capture experiment to assess those obligations first.
  Treat captured text as context without deriving failure classifications from
  it. An explicit decision to omit capture must retain the documented coverage
  gap.
- [x] Keep `sbpl-check` on the missing-reply path as an independent observation.
  Its admission refusal already reaches `policy_check_status` as a distinct
  outcome; keep that distinction in the startup note prose, which reports any
  non-compile as failed. A successful helper compilation does not explain the
  missing worker reply or establish the worker's last stage; no reply does not
  prove the worker never published a record.
- [x] Keep every existing capacity and budget fixed. For the controller's capture
  boundary, make loss explicit; whether parsing should have a separate/larger
  budget is a later decision. Do not promise preservation of a record inside an
  envelope the receiver could not retain or decode.
- [x] Account for affected diagnostic, schema, and outcome documentation and
  existing tests. Preserve complementary contracts rather than replacing useful
  assertions with a single generic failure assertion.

At the end of this step, each reviewed entry should have a reporting owner and
an evidence-based acceptance result or a specific unresolved limitation. Do not
claim that all possible failures have been discovered or can always be reported.

### 3. Experiment with preservation of unfamiliar diagnostic codes

Extend the basic step-1 control to the reporting paths adopted in step 2. Test the
distinction between understanding a diagnostic and transporting it. An integer
field permits unfamiliar values but does not prove that decoding, reconstruction,
or classification-dependent serialization preserves them. Use structurally valid
records in the supported format; malformed records and incompatible ABI versions
still require their defined rejection or fallback behavior.

- [x] Choose a bounded test arrangement after the record format exists: direct
  decoder/forwarding controls and, if practical, a test-only producer exercising
  the worker-to-CLI route. Use at least two unfamiliar codes and distinct payloads
  without registering them in production outcome mappings. Extend the basic
  step-1A control; prefer a separately built fixture selected by the existing
  `worker_executable_path` boundary override. Keep its source and controlled
  payloads in test equipment, its executable outside the inspected app, and the
  override mirrored in the final reply. It must obey the supported ABI's real
  publication protocol; it does not establish production failure attribution.
- [x] Carry each record through the applicable C/Swift decoding, runner encoding,
  client forwarding, and controller parsing boundaries. Check the final record's
  producer, operation, code/domain, and diagnostic detail against the independently
  supplied input. If a layer cannot be exercised, state that coverage gap.
- [x] Require an unsuccessful/incomplete run to remain so. Do not infer a sandbox
  denial or compiler/apply failure merely from an unfamiliar code; preserve any
  independently established operation result. A generic summary is acceptable
  when the original record remains available. A known failure reported alongside
  it must retain its own evidence.
- [x] Include controls for absent, unpublished, malformed, and incompatible
  records. Confirm that structural validation remains effective while an
  unfamiliar but valid code is preserved. Exercise declared diagnostic truncation
  separately from code recognition.
- [x] Demonstrate that a temporary known-code-only forwarding path, or one that
  drops/relabels unfamiliar details, fails the preservation controls. Keep such
  mutations out of production commits and retain their failure evidence.

Synthetic records in this experiment establish transport behavior only. Keep
them in test equipment; do not add a production override that forces a result
or normalized outcome. Real-failure cases from steps 1 and 2 must continue to
establish correct attribution at the producer. If the experiment reveals another
recognition-dependent boundary, fix that boundary and rerun the same controls
instead of adding the unfamiliar code to an allowlist.

The transport controls and the following acceptance review are complete. This
acceptance is limited to diagnostic preservation; interpretation work remains
in step 4.

- [x] Review the step-3 acceptance claims against the retained inputs, outputs
  and mutation failures. Distinguish preservation of supplied diagnostic fields,
  independently observed host/process facts, and producer attribution established
  by real-failure controls. An unfamiliar fixture code does not establish its
  real-world meaning, and co-preserved records do not establish causation between
  them. Qualify any broader claims in the contract, inventory and evidence index.
  Repair a demonstrated transport/structural-validation gap within this step;
  leave comparison, drift and evidence-join semantics to step 4.
- [x] Complete the step-3 handoff with the reviewed scope, remaining coverage
  limits and an exact account of the source changes and tested build. Retain
  the existing successful controls and failed mutations; rerun only checks
  affected by a correction or an unresolved verification concern. Distinguish
  later documentation edits from the source snapshot used for the signed build.
  Report step 3 complete only after these two acceptance items are discharged;
  completion establishes diagnostic transport, not the correctness of every
  derived policy claim.

Acceptance: the transcript producer supplies its allow/native-result record and
never calls `sandbox_check`; worker native-result/errno payloads and Rust helper
failure reports are also supplied test inputs. Documentation now distinguishes
them from observed EPIPE, UTF-8 rejection, reaped child status and the real-worker
file change. Co-preservation establishes no causal relationship. No transport or
structural-validation correction was needed during the closeout review. The
initial worker mutation exposed a crashing Swift assertion; step 3 replaced it
with a normal TestFailure and required the mutation driver to reject crashes.
The closeout records that initial run as superseded by the confirmed repeat,
not as a completed mutation control. It checks the retained 49 passing cases,
258/258 Swift tests, 109 Rust unit tests, 10 CLI integration tests and all three
accepted failed/restored mutations against unchanged executable sources and all
eight signed executables. Fresh `source_drift` and unsandboxed
app-integrity checks pass. [Review, provenance and commit receipt](out/failure-propagation-3/closeout/README.md)
complete the handoff; all seven step-3 requirements are discharged.

### 4. Attempt to reconcile derived claims with their supporting observations

Two valid records can support an unjustified comparison. This step examines the
relationships used to derive claims from independently owned observations, then
attempts bounded corrections to the public contract and its implementation.
Record validity, association with a request, comparability with another
observation, and support for a causal conclusion require separate justification.
A common envelope, step ID or artifact directory does not establish all four.

The response-6 baseline conflated established outcome agreement and consistency
with an unattributed permission failure in `drift=false`. Raw prediction and
attempt evidence survived, but consumers needed classifier knowledge to recover
that interpretation. Response 7 separates those meanings and records their scope
and independent limits. Direct execution controls belong to the test
harness, and denial-log candidates do not automatically resolve attribution.
The retained step-0 baseline pinned deny + permission failure to `drift=false`.
Response 7 uses null and reports directional consistency only within matching
submitted scope. The compatibility decision reconciles that acceptance pin with
the observer principles; it does not treat correct earlier execution as drift
from the plan.

#### Establish what each join supports

- [x] Write a bounded claim/evidence table in the durable failure contract and
  reference it from the routing inventory. For each relationship, identify the observation
  owners, association rule, relevant phase/order guarantees, assumptions,
  counterexample and strongest supported conclusion. Distinguish demonstrated
  defects from source-established limitations and hypotheses needing a control.
  Cover these relationships:

  | Relationship | Question to establish before drawing a stronger conclusion |
  | --- | --- |
  | Submitted query to validator reply | Does the unique record answer the actual query? Preserve step 2's tuple validation; it does not establish comparability with the attempt. |
  | Prediction to attempted operation | What connects their operation, target and relevant conditions? A shared step ID can pair intentionally different queries and attempts. Deny for A plus successful allowed attempt on B must not, by itself, establish sandbox drift. |
  | Query time to attempt time | Application publication precedes host validator invocation, while the worker proceeds with attempts. What ordering or state stability is actually established? Frozen query planning does not freeze filesystem state. |
  | Host path enrichment to validator/worker evidence | Post-run host resolution is a separate observation. Its placement under `sandbox_check` must not imply the validator or worker observed that resolution earlier. |
  | Denial event to attempt or process termination | PID/operation/path matches identify candidates within a limited capture window; repeated attempts and missing temporal identity can prevent a unique association or causal conclusion. |
  | Test control to runtime conclusion | An independent control can test a claim without being an observation available to the running app. Identify the actual runtime evidence supporting any emitted conclusion. |

#### Establish the consumer-question baseline before choosing a representation

- [x] Use the six questions below as the baseline for the claim/evidence review
  and public-contract choice. Preserve their IDs, meaning and scope in the
  durable failure contract before choosing fields; step 5 inherits this baseline.
  Wording may improve, but dropping, merging or narrowing a question, or changing
  its disposition, requires an explicit design reason and an account of the
  affected distinction. Keep the original obligation traceable; fitting the
  chosen representation or making a recovery check pass is not a design reason.

  | ID | Consumer question | Acceptance distinction to preserve |
  | --- | --- | --- |
  | C1 | Which steps report established agreement, and what comparison does that claim cover? | Established agreement must remain distinguishable from directional consistency and an unavailable comparison. |
  | C2 | Which steps observed a failure whose cause PW could not attribute to the sandbox? | An observed failure with uncertain attribution differs from an absent attempt observation. |
  | C3 | What relationship between each query and attempt was established, known to differ, or left unresolved? | A shared step ID or equal target spelling cannot silently certify comparability. |
  | C4 | Which steps produced no comparison, and what known reasons limit it? | Preserve distinct and simultaneous known reasons without inventing explanations for absent evidence. |
  | C5 | Which path resolutions were later host observations? | Host enrichment must remain distinguishable from submitted query values and validator/worker observations. |
  | C6 | Which denial events are candidates for a step, and what association or capture limits remain? | Candidate association, unique occurrence, missing capture and capture without a match remain distinct. |

- [x] Assess each question against the observations and inputs available to PW
  at runtime, their owners and limits, as well as what the current envelope
  exposes. An omitted field does not establish an architectural inability: for
  example, the controller retains the submitted attempt's kind/action even
  though the reply omits them. Submitted kind/action identifies the intended
  operation; it does not by itself prove execution or query/attempt comparability.
  Distinguish unavailable evidence from a reporting choice, without assuming
  that copying raw inputs is the only useful contract.
  Record a proposed disposition and supporting design reason for each question:
  answerable from a single envelope under the proposed public contract;
  deliberately limited, identifying what remains unanswerable and how public
  claims must be constrained; or requiring an added field or changed meaning.
  Carry required additions and semantic changes into the compatibility/dependency
  gate. A deliberately limited answer must rest on the evidence review and a
  substantive scope or design judgment, not merely the current output shape.
  Known uncertainty and several simultaneous limits remain valid answers.

#### Choose a bounded public contract

- [x] State what `drift=true`, `false` and `null` promise before choosing fields.
  Reconcile the observer principles, step-0 positive-control expectations,
  directional DAC control, API comments and public documentation. If false means
  established agreement about sandbox enforcement, ambiguous permission failure
  alone cannot establish it. Retaining directional consistency as useful
  information requires an explicit limited meaning. Avoiding false positives
  does not alone justify false, because null also avoids them.
- [x] Make the derivation and its known limits inspectable in the envelope, so a
  consumer can distinguish the supported meanings without copying the private
  classifier truth table. Choose the smallest useful representation after the
  claim/evidence review; do not preselect `drift_basis` or an exhaustive two-value
  taxonomy. Attribution uncertainty, uncertain comparability, unavailable
  evidence and uncertain event association can coexist. Preserve known reasons
  and supporting observations while allowing unresolved interpretation; a generic
  unknown must not erase a more specific known limit. An `observed` label alone
  cannot establish that two observations are comparable. Consumers may recover
  a documented derived relationship with its supporting provenance and limits;
  they need not reconstruct every derivation from duplicated raw inputs. The
  evidence review must still justify the relationship's promised meaning.

#### Compatibility decision and dependency gate

Complete this gate after choosing the public contract and before changing
production emitters, field meanings or their expected values in tests.
Link each consumer-question disposition to the relevant contract decision and
inventory entries, including required implementation work. A question's needed
change cannot disappear from the inventory because the chosen representation
does not yet support it.

- [x] Record the compatibility decision in the durable contract: old and new
  field meanings/shapes, emitted response version, treatment of older stored
  replies and consequences for existing readers. Decide explicitly whether
  response schema 6 advances. A change to an existing field's promised meaning
  or required shape requires a response-version advance even when its JSON type
  is unchanged. If the change only adds compatible evidence while preserving
  existing meanings, justify retaining the version. Keep request schema and
  worker ABI decisions separate; do not bump either merely because the response
  changes. Apply the decision consistently to every response emitter, including
  client-generated failures, and preserve supported legacy decoding without
  inventing observations absent from stored replies.
- [x] Expand the dependency table below into a concrete inventory before editing
  assertions. Start with references to `drift`, the response version and the
  chosen new fields, then trace shared helpers, fixture readers, wrapper scripts
  and runner contexts. Inspect `tests/run.sh --all --list` and map each executable
  dependency to canonical catalog case IDs, prerequisites and default/opt-in
  status. Record each required update or verification, and the reason for any
  search candidate excluded as unrelated. Plain-text references are discovery
  hints: `tests/lib/artifact.py` uses "drift" for bundle changes, while indirect
  consumers of `tests/lib/blackbox.py` may never name the result field.

The following are required starting points, not an exhaustive or fixed case
count. Extend the inventory when the chosen representation or final diff reveals
another dependency; do not shrink it merely by removing an old assertion.

| Artifacts | Required update or verification |
| --- | --- |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift`, `PWRunnerService.swift`, `runner/Clients/PWRunnerClient/main.swift`; `tests/suites/runner_use_c_worker/run.sh` and stored envelope fixtures | Apply the response-version and field contract to normal and failure emitters, explicit nulls, encoding/decoding and exact-version assertions. Verify supported older replies separately from newly emitted evidence. |
| `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift`; `runner/Tests/PWRunnerCoreTests/DriftClassifierTests.swift`, `AttemptOutcomeMappingTests.swift`, `PredictionUnavailableTests.swift`, `WorkerEvidenceTests.swift`, `CWorkerTests.swift`, `EnvelopeInvariantTests.swift` | Reconcile comparison semantics, missing evidence and Codable guarantees while retaining native observations, process status and partial-result assertions. Run the registered `runner_unit` batch with the required signed-worker equipment. |
| `controller/src/runner_client.rs`, `utils.rs`, `run_flow.rs`, `sandbox_log.rs`, `bin/sandbox-log-observer.rs`; `tests/suites/unit/`, `integration/` | Verify forwarding, any changed JSON interpretation, log associations and host-owned enrichment through their Rust unit/CLI boundaries. Identify affected tests even where the controller forwards the field without naming it. |
| `tests/suites/witness_contract/`, `failure_boundaries/`, `runner_use_c_worker/`, `runner_exec_dac/`, `runner_exec_lifecycle/`, `runner_exec_inheritance/`, `runner_specimen_isolation/`, `runner_filter_sysctl_name/`, `runner_validator_failure/`, `runner_outcome_runner_timeout/` | Map direct drift, absence, version and provenance assertions to all affected catalog cases, including opt-in members and shared validator-failure aliases. Preserve effects, attribution and lifecycle checks while changing summary expectations. |
| `tests/lib/blackbox.py`; `tests/suites/blackbox_e2e/validate_run.py`, `checker_controls.py`; `tests/suites/blackbox_menagerie/validate_run.py`, `checker_controls.py`; `tests/fixtures/blackbox_e2e/`, `blackbox_menagerie/` | Update shared validation and independent checker controls, fixture expectations and legacy examples. Trace all consumers of the helpers and fixtures; a helper change affects callers that do not spell out `drift`. |
| `tests/suites/runner_byoxpc/run.sh`, `tests/suites/smoke/pw_specimen_smoke.sh`, and their smoke/black-box fixtures and checkers | Include affected standard and BYOXPC catalog IDs separately, with installation dependencies, required equipment and cleanup. Standard-context success does not verify BYOXPC wrappers. Explicitly account for `runner_byoxpc/BBX-001` and `runner_byoxpc/BBX-002` when the shared checker or contract changes. |
| `tests/catalog.json`, `tests/suites/source_drift/check.py`, `tests/README.md`, `tests/COVERAGE.md`, `tests/OPT_IN_TESTS.md` | Update case descriptions, registrations and coverage claims. Run `source_drift` as a mandatory step-4 gate; it verifies registry/source consistency and does not substitute for executing affected cases. Check dispatcher/shared-equipment controls when their actual dependencies change. |
| `PolicyWitness.md`, `controller/README.md`, `runner/README.md`, affected suite/fixture READMEs, `tests/FAILURE-PROPAGATION-CONTRACT.md`, `tests/FAILURE-PROPAGATION-INVENTORY.md`, and earlier acceptance pins in this plan | State the accepted meanings, provenance, limitations and compatibility consistently. Preserve the original absence, lifecycle and no-cause obligations when replacing drift expectations. |

#### Implement bounded corrections

- [x] Implement justified corrections at the layer that owns the derivation or
  enrichment. Keep native observations and their provenance independent of the
  summary. Continue accepting independently specified queries and attempts;
  admission or string equality alone cannot certify a meaningful comparison.
  Identify later host path diagnostics as host observations at their actual
  phase, without presenting them as historical validator/worker facts.
- [x] Retain candidate log associations and capture limitations. Stronger joins
  require additional supporting evidence; a log match is not a general remedy
  for ambiguous errno, and no match is not proof of no sandbox involvement.
  Do not infer a total timeline from collection/array order or require a unified
  log stream to complete this step. Optional logs must not change PW execution
  status merely by becoming available. Keep fallback-helper and test-harness
  observations within their own scope.

This is an attempt to improve the contract within the existing architecture.
It does not authorize a lifecycle redesign, global event-ordering system,
per-step synchronization protocol, new logging requirement, larger budgets, or
a search for native compiler drift. Where stronger evidence would require such
work, expose the limitation and constrain the claim. A useful result can leave
interpretation unresolved. Merely documenting an unsupported public claim as
accepted does not discharge it; if no bounded correction is established, leave
that item pending and explain the required follow-up.

#### Establish acceptance and stop at a reviewable boundary

- [x] Add focused controls with an oracle independent of the classifier's
  current outputs. Cover ambiguous permission failures under allow and deny
  predictions, a deny query for A paired with successful allowed attempt B,
  justified comparisons, and missing/unusable observations. Assert both retained
  evidence and the limited conclusion/derivation, not only a revised boolean.
  For temporal or path-enrichment concerns, first establish a deterministic
  control or the precise source-level guarantee; do not depend on a
  nondeterministic race to pass acceptance. Credit constructed
  interpretation tests separately from real-worker and CLI evidence.
- [x] Check the relevant joins with absent, unavailable and candidate log
  evidence, including repeated-attempt ambiguity. A combination of individually
  valid records must not silently gain stronger identity, ordering or causal
  meaning when assembled. Preserve valid observations when a comparison is
  unavailable. Retain step 3's unfamiliar-diagnostic controls and the existing
  success, timeout and partial-evidence protections; exercise changed forwarding
  boundaries through the CLI when public fields change.
- [x] Reconcile the completed compatibility/dependency inventory with the final
  diff and full catalog. Update every affected emitter, reader, fixture, assertion
  and public contract identified by the inventory. Keep each changed expectation
  tied to the chosen semantics; a passing old or mechanically replaced assertion
  cannot settle a conflict with the meaning now promised.
- [x] Execute every affected canonical catalog case identified by that inventory,
  including indirect helper/fixture consumers, applicable opt-ins, both runner
  contexts and their dependencies. Run `source_drift` unconditionally for step 4.
  A convenient selector or the default battery alone is not the acceptance scope.
  Retain the exact required case set, expanded dispatcher selections, commands,
  results and signed-build/source provenance. Reconcile required IDs against
  completed results; missing equipment, skipped or unrun required cases remain
  unverified and prevent acceptance. Use separate output directories for batches.
  Credit results only for the accepted implementation; after a later correction,
  rerun affected cases and explain why any retained results still apply. Include
  Swift/Rust batch results and their internal required controls in this accounting.
- [x] Produce a handoff mapping each reviewed claim to its implemented guarantee,
  acceptance evidence and remaining limits. Account for every original consumer
  question (C1–C6), preserving any explicitly justified changes to its meaning or
  scope. Each must be supported by the delivered single-envelope contract or
  deliberately limited with a substantive design reason and constrained public
  claim. Identify which parts of a limited question remain answerable. Required
  additions or semantic corrections still pending are not completed dispositions.
  Carry these dispositions and their evidence into step 5's design acceptance;
  step-4 closeout does not substitute for that review or its recovery checks.
  Account for unresolved questions in durable documentation and, where relevant
  to interpreting a result, in the envelope. Identify any unfinished correction
  separately from an intentionally unknown answer. Completion requires this
  disposition of every reviewed item,
  not a claim that every pair of streams can be unified or every cause resolved.

Commit the reviewed step-4 implementation, tests and supporting documentation
with their verification and remaining limitations, then pause. Step 3 has its
own closeout commit; the plan/audit planning commit is also separate. This
checkpoint does not dissolve the plan or settle all interpretation questions;
resume step 5 as a separate task and make its final commit separately.

Acceptance: [claim/evidence review and C1–C6 dispositions](FAILURE-PROPAGATION-CONTRACT.md#derived-comparisons-and-evidence-joins-response-7)
are implemented and [reconciled against the final diff and catalog](out/failure-propagation-4/dependencies-final.json).
Response 7 leaves request schema 1 and worker ABI 6 unchanged. The
[acceptance review](out/failure-propagation-4/review.json) credits all 130 required
cases with no skipped or unrun obligations: 108 on the final signed build and
22 unchanged offline controls. Swift passes 262/262, Rust unit 110/110 and CLI
integration 10/10. Ten controlled CLI comparison scenarios and eleven unfamiliar
diagnostic controls pass. Live log captures also verify ambiguous candidate
matching evidence, with no change to PW execution status or causal attribution.
All 51 recorded production-source hashes and eight shipped executables match;
app integrity and owned BYOXPC cleanup pass. The [handoff](out/failure-propagation-4/README.md)
retains earlier failed assertions separately and accounts for every original
question. No required implementation remains pending; temporal equivalence,
runtime identity, full scope for broad/compound operations and causal attribution
remain explicit design limits for step 5 to review.

### 5. Accept the plan and transfer consumer obligations into permanent tests

This step follows the step-4 commit and review. Its primary task is to settle
plan acceptance: which reported distinctions are justified by the observations
and assumptions the product actually has, and which limitations remain part of
the accepted contract. That is a design judgment made for this plan. The lasting
executable obligation is that a consumer can recover the accepted distinctions
from the envelope using the public contract, without reconstructing private
classifier rules. Tests pin the chosen guarantees; they do not establish a
universal theory of policy causation.

#### Settle the design judgments and expected consumer answers

- [ ] Review step 4's claim/evidence table against the observer principles,
  controlled scenarios, retained observations and implemented contract. Resolve
  conflicts between principles and acceptance criteria explicitly. Record the
  conclusions accepted for each scenario, their supporting observations and
  assumptions, prohibited stronger conclusions, and intentionally unresolved
  questions in the durable failure contract. Preserve the distinction between
  test-owned controls and information available to PW at runtime. An unfinished
  correction remains pending; calling it a limitation does not accept an
  unsupported emitted claim.
- [ ] Review the inherited consumer questions C1–C6 and their step-4 dispositions,
  then settle their expected answers before writing recovery checks. Preserve
  the baseline's meaning and scope; wording improvements must not quietly remove
  a distinction. Apply step 4's explicit design-reason requirement to any dropped,
  merged or narrowed question or changed disposition, retaining the original
  obligation and explaining how the review resolves it. Reopen required contract
  or implementation work through step 4's gate when this review exposes a gap;
  do not adapt a question merely to the output already implemented. Answers may
  include "not established" or "not reported" where the review justifies them.
  Do not require certainty unsupported by the evidence, or a single reason where
  several known limits coexist.

- [ ] Associate the expected answers with controlled inputs and observations,
  using applicable existing cases and a small number of focused additions where
  coverage is missing. Record each case's scope: constructed interpretation,
  real-worker observation, CLI forwarding or legacy decoding. Do not derive
  expected answers from the emitted summary labels or copy the classifier into
  the oracle. Changes to an accepted answer require an explicit design reason;
  making a failing filter pass is insufficient. Older stored replies need their
  own version-aware expectations, without retroactively inventing new evidence.

#### Demonstrate recovery and distribute permanent enforcement

- [ ] Implement JSON-only recovery checks using the documented public contract.
  For each question's accepted recoverable distinctions and reportable limits,
  obtain the answer from a single envelope and compare it with the reviewed
  scenario expectation. Keep deliberately unanswerable portions in the design
  accounting; they must not silently remove an accepted recovery obligation.
  Reading public field meanings is
  allowed; consulting the private comparison classifier, applying private errno classifications, or
  inspecting external artifacts to construct the consumer's answer is not.
  External scenario evidence can establish the expected answer for the test,
  but it is not an extra input available to the JSON consumer. Demonstrate
  recovery through actual CLI output for the applicable live controls.
- [ ] Place permanent checks at the boundaries that own the obligation. Extend
  the relevant CLI/witness cases for consumer recovery, Swift tests for encoding
  and absence guarantees, and controller tests for preservation or correlation
  behavior that the controller owns. Put universally shared invariants in shared
  checkers and reuse recovery helpers where appropriate. Reuse step-4 coverage;
  do not copy the full decision procedure into every suite or create a permanent
  plan-specific audit framework. The durable tests and their fixtures must work
  without reading this plan or the audit document.
- [ ] Demonstrate that the permanent checks reject representative losses of
  meaning: dropping a required distinction or provenance, removing one of several
  known limitations, or presenting later host evidence as a validator observation.
  Include a case where blanket unknown would discard a conclusion the reviewed
  evidence supports. Use existing checker controls or bounded temporary mutations
  at the relevant boundary, preserving their failure evidence and restoring the
  source/app afterward. These controls establish enforcement of the accepted
  contract, not independent proof of every causal judgment behind it.

#### Close out the plan and make the final commit

- [ ] Publish an ownership map from each accepted consumer question to its
  durable contract location and permanent registered tests. Account for every
  original baseline ID, including explicitly limited or revised questions and
  their design rationale, so none disappears between design and enforcement.
  Enforce recovery of each accepted distinction and reportable limit; retain
  the rationale for deliberately unanswerable parts as a design decision.
  Keep the rationale and residual limits where future maintainers can find them
  without the plan or audit conversation. Every reviewed promise must have a supported
  guarantee or an explicit accepted limit; unresolved implementation work still
  prevents completion. Readability of an unsupported label cannot substitute for
  the design judgment settled above.
- [ ] Reconcile the final diff with step 4's compatibility and dependency gate.
  Apply that gate to any implementation/contract correction discovered during
  acceptance, and run the new recovery controls plus all affected cases. Keep
  exact build/source and case-result provenance, retaining prior evidence only
  where it still applies. Update registry and coverage documentation and run
  `source_drift`; no required unrun or skipped check receives acceptance credit.
- [ ] Complete the final handoff with the accepted contract, design decisions,
  permanent enforcement map, verification results and remaining limitations.
  Mark the plan complete only when these obligations are satisfied. Make the
  final step-5 commit separately from the step-4 checkpoint; any later archival
  or removal of planning documents must leave the permanent contract and tests
  sufficient on their own.

## Verification and handoff

For each implementation batch, retain focused before/after evidence under a
dedicated `tests/out/` directory. Use separate, non-overlapping `PW_TEST_OUT_DIR`
paths for public test runs; the dispatcher replaces its selected output directory.
Use normal signed builds for changes to the worker, ABI, or runner, and run CLI
cases through `tests/run.sh` so bundle integrity and case results are recorded.
Do not edit binaries inside an already inspected app to create test failures.
SwiftPM unit tests do not rebuild the signed app used by CLI tests. Record the
source revision (and any uncommitted source changes), exact build command, tested
app path (`PW_APP_DIR` if set), and the dispatcher's bundle-integrity evidence so
the next agent can tell which implementation the CLI results establish.

For acceptance that credits real-worker Swift cases, select `runner_unit`
together with an app-dependent case in the same public dispatcher invocation
(for example, `--suite runner_unit --suite runner_c_worker_harness`) so the
selected app is inspected. Record the actual worker and validator paths used by
the credited cases and retain `pwrunner_core_tests.log`. Inspect that log for
internal `SKIP` messages as well as failures. Required live controls throw a
normal TestFailure when equipment is missing, and the wrapper rejects internal
SKIP/FAIL before accepting the summary. A skipped required case remains unverified even if the batch reports
all tests passed. Supply the matching signed build and rerun before accepting
that row; newly added required live controls must fail clearly when their test
equipment is absent. Pure classifier/encoding controls may still be credited
independently. This requirement does not call for a general test-harness redesign.

Select verification according to the changed boundary: C harness and ABI layout,
Swift classifier/envelope tests, validator transport tests, controller parsing
tests, and real CLI cases. Include `source_drift` when outcome constants or
coverage registrations change; it is required for steps 0, 4 and 5. Register new cases and
update `tests/README.md`, `tests/COVERAGE.md`, suite documentation, and public JSON
documentation as needed.
Run relevant existing success, timeout, and partial-evidence cases alongside new
failure cases. Acceptance must check evidence and provenance as well as any
normalized outcome contract. Review the diff and run `git diff --check`.

Each handoff should identify the implemented contract, grouped inventory entries
closed, remaining limitations, exact tests and results, and evidence paths.
Explain any changed outcome semantics without turning current-behavior docs into
a change history. Leave unchecked work visibly pending.

### Current execution state

Update this block in place after each implementation batch and before handing off;
keep the status paragraph and checkboxes consistent with it. Link to retained
evidence and authoritative contracts rather than adding a chronological work log.
A check that was not run remains unverified, with its reason recorded.

| Item | Current state |
| --- | --- |
| Completed implementation batch | 0A–0C, 1A–1C, step 2 and audit corrections, all seven step-3 requirements, and every step-4 requirement. Step 5 has not begun. |
| Next batch | Step 5: review the inherited C1–C6 questions and design dispositions for plan acceptance, distribute permanent consumer-recovery enforcement, then make the final commit. Step 4 has its own implementation/verification checkpoint. |
| ABI revision state | Worker ABI 6; response schema 7 (scoped comparisons, submitted intent and host provenance); request schema 1. No capacity/budget increase. Older replies retain their original version and absent new evidence. |
| Chosen field contract locations | [Failure contract](FAILURE-PROPAGATION-CONTRACT.md), [routing inventory](FAILURE-PROPAGATION-INVENTORY.md), `pw_probe_runner_abi.h`, `PWRunnerAPI.swift`, and `ValidatorClient.swift`. Admission belongs to the host; worker publications/transfer observations to `runner_subprocess`; validator records/receiver/process observations to `validator_subprocess`; controller byte counts/local loss to runner-client, policy-check and log-observer capture objects. |
| Inventory entries closed / remaining limitations | Step-4 claim/evidence and compatibility/dependency inventories are closed; C1–C6 guarantees and deliberate limits are recorded in the failure contract and handoff. Query/attempt order, state stability and runtime target identity remain unestablished; broad/compound scope and sandbox attribution can remain unresolved. Earlier stderr, policy-pipe deadline, blocking reap, buffering and raw log-pathname fidelity limits are unchanged. Step 5 owns final design acceptance and consumer-recovery enforcement. |
| Verified source and signed app | [Final signed build](out/failure-propagation-4/accepted-build.json), [build log](out/failure-propagation-4/build.final.log), [tested source](out/failure-propagation-4/tested-source.json) and [review](out/failure-propagation-4/review.json): all 51 production-source hashes and eight executables match. The accepted dispatcher run reports valid/unchanged app integrity; later Markdown edits are recorded separately. Test fixtures remain outside the inspected app. |
| Checks, results, and evidence paths | [Step-4 handoff](out/failure-propagation-4/README.md): 130/130 required cases credited, no skips/unrun; 108 on the final build plus 22 unchanged offline controls. Swift 262/262; Rust 110/110; CLI integration 10/10; ten comparison scenarios and eleven unfamiliar-diagnostic controls. source_drift passes, all 13 BYOXPC cases pass, and the runner registry matches its initial contents. Earlier failed batches and corrected expectations remain retained without passing credit. |


## Decisions to resolve within implementation batches

- Exact milestone meanings, the state table needed before consolidating fields,
  publication protocol, and final host observation points; then the shared-memory
  layout under the ABI revision rule in step 1A.
- Public representation of observer-owned evidence, reuse of subprocess metadata,
  and compatibility of new evidence fields without duplicated authoritative facts.
  Apply the step-0 response-version, signal-null, and subprocess-absence rules;
  those choices do not require a new consumer survey before execution.
- Minimal failed-operation/status representation and bounds/publication for the
  primary shared-memory text region. Early or uninstrumented stderr capture
  remains a separate deferred coverage question.
- Summary precedence for multiple observations and the compatibility treatment of
  outcomes whose present names or rules imply unsupported causes, particularly
  `sandbox_apply_failed` and `runner_sandbox_denied`.
- Correlation criteria, capture availability, and the evidence needed for any
  stronger policy-cause claim, kept separate from PW's execution summary. Enforce
  step 0's worker-identity and attempt-provenance requirements, specify ambiguous
  associations for repeated attempts, and state the trailing-window limits.
- Per-step missing-prediction and incomplete-attempt representation in step 1A,
  including compatibility sentinels and outcome spellings; these must not imply
  unobserved native returns or prove that an operation never started.
- Validator verdict/diagnostic structural requirements in step 2, including
  legitimate absence of native results and preservation of unfamiliar valid
  diagnostics; syntactically valid JSON and a matching step ID are insufficient.
- Placement of coverage for production C-worker failures; unused Swift apply
  implementation and test removal remain outside this effort.
- The smallest test arrangement that proves unfamiliar-code preservation across
  the full route without introducing result-forcing production seams.
- Where groups genuinely share reporting code, and where separate paths better
  preserve the meaning of the evidence.
- Step 4's supported meanings of drift, representation of derivation and
  simultaneous unresolved limits, justification of cross-observer joins, host
  enrichment provenance, consumer-question dispositions, and the explicit
  response-version/reader compatibility decision and complete affected-case
  inventory required before implementation.
- Step 5's acceptance of design judgments and the inherited consumer-question
  dispositions, scenario-derived expected answers, permanent test ownership and
  residual limits at closeout.

Resolve these questions within the relevant step. This plan does not authorize
raising limits or replacing the existing test-equipment plan.

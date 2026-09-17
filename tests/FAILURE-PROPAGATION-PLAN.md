# Failure evidence through the worker, runner, and controller

## Status: execution plan; implementation pending

This is an execution plan, not an implemented contract or a finished
specification. All implementation work below is pending. Record layouts, public
field names, and exact test placement need to be settled as each step is prepared,
subject to the planned compatibility rules in step 0. A preliminary correction
precedes the three major steps. Each step should produce reviewable changes and
acceptance evidence before the next begins; the preliminary correction and the
first major step are divided into smaller implementation batches.

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

- [ ] Write an interim evidence/classification table before changing production
  behavior. Cover absent publication, inconsistent flags, pre-apply exit and
  signal, observed deadline expiry, reported failure plus cleanup trouble, and
  completed reports followed by abnormal or unconfirmed process disposition.
  Specify summary precedence for concurrent failures without discarding their
  independent evidence. Identify the required host observations and proposed
  JSON locations, using authoritative subprocess metadata. Keep this table as
  the specification for 0B's observations and 0C's classifier controls.
- [ ] Include the meaning of `runner_sandbox_denied` in this review. Decide and
  document interim outcome semantics and compatibility explicitly. A post-apply
  signal does not prove kernel sandbox attribution, and no progress evidence added
  in later steps changes that. Do not retain the inference merely because an
  existing test expects the label.
- [ ] Audit the production reachability of tests credited with protecting these
  decisions. Credit host interpretation with constructed inputs, real C-worker
  publication, and CLI forwarding separately. Assign required live-boundary
  coverage to the witness in 0A, host-driver controls in 0B, and classification
  and public-contract controls in 0C. Keep coverage claims aligned with the
  implementation.
  `SandboxApplyTests` exercises the unused Swift helper only; do not extend that
  helper to imitate the new production reporting model. Removal of the helper,
  its helper-specific error type, and its tests is separate cleanup outside this
  effort. Preserve the live `computePolicyHash` function in the same source file.
- [ ] Add one CLI contract case that pins the first observer rule end to end:
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
  prediction, permission-failure attempt, and `drift=false` that the failure
  run must not contain, so the absence assertions are not vacuous. Assert that
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
- [ ] Document in `runner/AGENTS.md` the narrow exception to the exact-outcome
  assertion recipe for this new evidence-focused witness case. Its absence
  assertions supplement classifier tests that pin the chosen outcome mapping;
  keep the artifact, override-mirroring, and structural assertions. Other
  override-driven cases retain their exact-outcome checks.

Exit condition: reviewable interim contract decisions, registered witness and
positive control, and retained baseline evidence showing unsupported attribution
independently of schema/signal-shape mismatches. Retain the positive control's
prediction and attempt evidence even though its new signal-null assertion is
expected to fail before 0C. No production behavior is changed in this batch.

#### 0B. Repair host lifecycle observations

Implement the host observations required by the 0A table before changing the
classifier. Keep the existing outcome vocabulary, response version, and signal
shape until 0C; new observation fields must be additive. Document their producer,
validity, and JSON representation beside the authoritative definitions.

- [ ] Repair the host's polling/cleanup observations before changing their
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
- [ ] Correct the existing `apply_rc`, `apply_errno`, and `done` comments in
  `pw_probe_runner_abi.h` in this batch: describe their actual producers and
  publication validity, including `done` on pre-apply failure. Correcting these
  descriptions requires no ABI revision. Trace `sandbox_create_params`,
  `sandbox_set_param`, compilation, and the defensive parameter NUL check
  separately; the last follows forced string termination and is not evidence
  of a reliably reachable specimen failure.
- [ ] Add host-driver controls for deadline expiry followed by voluntary exit
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

- [ ] Stop treating unpublished `apply_rc`/`apply_errno` storage as a reported
  failure. For legacy pre-apply failures, require the worker's `done` publication.
  Even then, `apply_rc = -1` can describe parameter setup or compilation; the
  interim diagnostic must not claim an observed apply return when it cannot
  distinguish the operation. A published zero or inconsistent flags do not
  establish failure either. Successful application has its own `applied` marker.
- [ ] Distinguish pre-apply exit, signal, and host-enforced deadline using the
  confirmed observations. A clean exit without completion does not establish
  a timeout. A published failure followed by cleanup trouble must retain both
  observations; do not unconditionally let a later kill replace an earlier report.
  Include `applied=true, done=true` followed by a nonzero exit, a signal, or
  failure to obtain wait status. The current classifier can fall through to `ok`
  in these states. A completed report must survive, but does not establish clean
  process completion; an abnormal or unconfirmed disposition must not yield `ok`.
- [ ] Add classifier rows for absent publication, inconsistent flags, pre-apply
  exit and signal, pre-apply host termination, reported failure plus cleanup
  trouble, and completed reports followed by abnormal or unconfirmed disposition.
  Pin the 0A table with constructed inputs using the observations established in
  0B. Passing these rows does not replace the host-driver acceptance evidence.
  Use the existing pre-ready delay seam for the real CLI deadline case begun in
  0A, and require it and its positive control to pass under the completed contract.
  Add a correlation control with an ordinary denial followed by unrelated
  termination: retain both observations without claiming a sandbox kill. Preserve
  existing successful, post-apply timeout, and partial-result contracts.
- [ ] Replace the fabricated per-step `deny_signal` zero record with an explicit
  JSON null: every new `steps[]` entry must contain `"deny_signal": null`.
  The C worker does not observe this channel, so successful and failed runs
  alike must not publish measured signal counts. Make `PWRunnerStepResult`
  support absence and explicitly encode the null; changing only the producer
  is insufficient because the current field is non-optional. Keep decoding of
  legacy signal objects for old stored replies without converting their zeros
  into newly observed evidence. Implementing signal collection or removing the
  unused `Signals.swift` helpers is outside this effort.
- [ ] Advance the runner response `schema_version` from 4 to 5 for the changed
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
- [ ] Decouple termination/log correlation from a prior sandbox-cause label in
  the same batch as changing that label. Capture currently uses the top-level
  reply PID when enabled; that PID can belong to the host or client when no worker
  exists. Resolve worker identity from authoritative `runner_subprocess` metadata
  before worker correlation, and never substitute a host/client PID. The current
  outcome gate selects the `first_deny` summary, not observer invocation.
  Use observed process/application facts to report abnormal termination and
  correlated events separately. Preserve capture for successful runs as well.
  Adapt `tests/suites/witness_contract/runner_sandbox_diagnostics_on_denied.sh`
  around confirmed termination, the chosen correlation representation, mirrored
  overrides, and observer invocation. Update its registration if renamed or
  split; retain CLI coverage of controller synthesis and capture invocation.
- [ ] Define correlation criteria and their limits, including process identity,
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
- [ ] Correct missing-attempt prose in the builder and public/test documentation.
  An absent or incomplete slot establishes no completed attempt result, not that
  the worker never reached the operation. If `not_run_worker_died` remains as a
  compatibility spelling in step 0, explicitly document that limited meaning;
  settle its final spelling with the step-1A evidence contract. Keep null errno
  and drift when no result supports a comparison.
- [ ] Complete the dependency updates below and verify `source_drift` alongside
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

- [ ] Define a small set of useful worker milestones. For each, state whether it
  means an operation started or completed and what an acquire reader can rely on.
  Specify optional transitions and failure exits. Readiness can fail while the
  worker proceeds; `done` is also published following compilation failure. Do not
  infer successful application from a simple ordering of all stage numbers.
- [ ] Write a small state table before consolidating progress and failure fields.
  Include death between a completed stage and the next started stage, a returned
  failure, a readiness failure followed by continued execution, and repeated
  parameter calls. Distinguish an operation returning from its succeeding, and
  identify which call failed inside a coarse stage. A generic nonzero-result rule
  is insufficient: compilation fails by returning NULL.
- [ ] Settle the minimum failed-operation record and its publication rules,
  independently of diagnostic text. Distinguish no report, a valid report with
  zero values, and an incomplete or incompatible report. Keep native call results
  distinct from PW's own diagnostic codes. An unfamiliar stage value must not be
  interpreted as successful application merely because its number is larger.
  Retain explicit operation/result evidence unless the state table demonstrates
  an equally clear consolidated encoding. Existing `done` may publish a terminal
  payload without an additional validity word, but payload validity, failed
  operation, and terminal success/failure still need unambiguous meanings.
- [ ] Before implementing new or changed cross-language fields, record their
  contract beside the authoritative ABI/API definitions or in existing contract
  documentation. For each field specify its producer, publication/validity
  condition, type (including width and signedness), units, Swift interpretation,
  and final JSON path and type. Include absent versus zero (and omitted versus
  null), unfamiliar values, and whether each receiving boundary decodes or forwards
  it unchanged. Reference existing layout definitions rather than copying offsets
  into a second schema. Link the chosen contract locations in the current
  execution state below; keep them current when later batches change fields.
- [ ] Implement worker publication in preallocated, pre-touched shared memory.
  Publish payload validity with release/acquire ordering; document its relation
  to progress, `applied`, `done`, and per-slot completion. Keep the post-apply path
  free of new allocation and diagnostic I/O dependencies. Failures before a usable,
  compatible mapping exists still need a supervisor-only fallback.
- [ ] Review when the host observes progress and takes its final snapshot around
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
- [ ] Carry worker evidence and host observations through `CWorkerOutput`, the
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
- [ ] Settle the per-step missing-evidence contract before extending the result
  types. Distinguish a validator that was not invoked from one that ran but did
  not supply this step's verdict, using run/step observations without duplicating
  subprocess authority. The current shared error shape and synthetic `rc=0`
  must not imply an observed sandbox_check return. Specify whether compatibility
  sentinels remain, how they are identified as synthetic, and which fields carry
  observed native results. Settle the final missing-attempt outcome spelling and
  describe an incomplete slot as lacking a completed result, without claiming
  the attempt never started. Add controls for never-invoked and short-reply
  validators, and for an attempt that starts but never publishes completion.
- [ ] Apply the ABI rule above and settle JSON compatibility before choosing
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

- [ ] Show the compilation failure reaching the normal CLI, distinguished from
  parameter setup and an observed apply result. Keep the minimal operation/status
  change reviewable separately from diagnostic-text storage and forwarding.
- [ ] Use a preallocated shared-memory text region as the primary route for
  PW-authored diagnostics after a compatible mapping exists. Implement the bounds
  and publication contract settled in 1A, or explicitly settle a further ABI
  revision if needed; make missing, partial, and truncated text explicit.
  Publishing reliable status must not depend on a successful diagnostic write.
- [ ] Preserve existing early stderr diagnostics where shared-memory reporting
  is unavailable. The text region cannot recover diagnostics emitted before a
  usable mapping, direct dependency/runtime stderr output, or unpublished details
  lost in a reporting-path crash. A separate stream may retain context when the
  shared-memory mechanism itself fails. Record this coverage gap explicitly;
  preserving an emission does not establish that the CLI can collect it. This
  step does not add stderr capture.
- [ ] Preserve and test the restriction on post-apply diagnostic syscalls and
  new allocation dependencies. If the existing stderr sites are routed through a
  helper that is silent after application, that helper must not disable the
  post-apply memory-only result/error publication. Existing per-step
  shared-memory diagnostics remain available after application.
- [ ] Verify the compiler diagnostic reaches the CLI. For otherwise identical
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

- [ ] Exercise oversized source through the worker guard and account for its
  report, last progress, and process status. Fix the host's policy-write failure
  path to preserve evidence when a child closes its input or exits; do not discard
  its status or lose the report through EPIPE/SIGPIPE handling. Record local pipe
  failure and child evidence independently, retaining bounded cleanup.
- [ ] Add a host-driver test for a child that closes its input or exits during
  transfer. Do not make it depend on an oversized specimen reaching the worker,
  so it stays valid if admission later rejects such input upstream. Test report-present and
  report-absent behavior at suitable boundaries, without requiring one
  timing-dependent race.
- [ ] Include early failures before publication, unexpected termination, and a
  report followed by cleanup trouble. These remain first-class acceptance cases
  even when ordinary admission prevents a particular specimen from reaching them.
- [ ] Cover failed mapping without classifying it as a host bug merely because
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
establishes host observations; classification and combined public-contract
acceptance remain pending until 0C. Do not mark a row complete using only its
earlier batch's evidence.

| First owning batch | Case | Boundary to exercise | Evidence that must reach the consumer | Implemented test entry |
| --- | --- | --- | --- | --- |
| 1A | Ordinary successful specimen | Real worker through CLI | Existing attempt/prediction evidence; no fabricated failure record | Pending |
| 1C | Source exceeds the existing worker cap at the worker boundary | C worker guard and host policy-transfer handling | Worker rejection and relevant byte limit; last progress and process evidence retained even if the policy pipe also fails | Pending |
| 1B | Ordinary SBPL syntax error | Real worker through CLI | An actual compilation failure and its diagnostic, distinguished from an observed application result | Pending |
| 1A | Observed application failure | C producer and Swift interpretation; deterministic harness if no reliable live specimen reaches it | Operation and meaningful native result retained | Pending |
| 0C (baseline in 0A) | Existing pre-ready delay exceeds the worker budget | Real CLI with existing delay override | The host's deadline/termination observations, with no invented library failure | Pending |
| 0B (classifier in 0C) | Deadline expiry followed by voluntary exit during grace | Host driver and classifier controls | Observed deadline expiry retained without requiring SIGKILL; separately obtained exit status retained | Pending |
| 0B (classifier in 0C) | Failed termination/reaping calls | Host driver and classifier controls | Termination request and call result distinguished; exit/signal status absent unless successfully obtained by reaping | Pending |
| 0B (classifier in 0C) | Completed report followed by nonzero exit, independent signal, or unavailable wait status | Host driver and classifier controls | Published completion and step results survive; process disposition remains independent; run is not `ok` and claims no sandbox cause | Pending |
| 0C (baseline in 0A) | Failure before application under a policy that would deny a probe | Real CLI with existing delay and deadline overrides, plus an un-overridden positive control | Failure run has no allow/deny prediction, permission-failure attempt, or drift value; control produces the deny prediction, permission-failure attempt, and drift=false from the same specimen; neither run claims sandbox-caused termination; failure run retains process evidence and overrides | Pending |
| 0C | Unobserved per-step signal channel | Runner JSON encoding/decoding and real CLI failure/success controls, including the pre-apply case above | Response version 5 and literal `deny_signal: null` survive forwarding; legacy reply decoding remains supported and dependent checkers retain their other evidence checks | Pending |
| 0C | Correlation with incomplete identity, irrelevant events, or repeated attempts | Controller correlation and CLI observer-invocation controls | No worker correlation from host/client PID or missing/mismatched event PID; relevance follows the attempt rather than an independently routed query; same-path unrelated operations do not match; repeated identical attempts retain ambiguity; availability and window limits are explicit | Pending |
| 1C | Unexpected worker exit without a report | Controlled child through host driver | Actual process status and absence of a report; unknown underlying cause | Pending |
| 1C | Failed mapping with no usable worker report | C worker harness and host process-status interpretation | Obtained process status and an incomplete account; no invented errno, detailed cause, or blame | Pending |
| 1C | Child closes policy input or exits during host transfer | Controlled child through host driver, independent of source admission | Host pipe error, available worker evidence, and reaped status or explicit failure to obtain it; this does not cover an open but undrained pipe | Pending |
| 0B (classifier in 0C) | Completed report followed by cleanup trouble | Host driver and classifier controls for otherwise unreliable states; step 1C rechecks new worker failure records | Reported completion or failure and subsequent supervisor observations both survive; cleanup termination alone does not establish sentinel deadline expiry | Pending |
| 1C | Failure after completed probes | Real worker through CLI, with independent effect checks | Completed step evidence and independently checked effects survive | Pending |
| 1A | Unpublished or incomplete record | C publication and Swift shared-memory decoding controls | No payload fields treated as confirmed evidence | Pending |
| 1A | Publication during cleanup after sentinel deadline | Host driver with controlled publication timing | Final confirmed records/slots survive; late completion does not erase the observed deadline | Pending |
| 1A | Missing prediction or incomplete attempt | Step assembly and JSON controls for never-invoked/short-reply validators and an attempt interrupted after starting | Missing evidence does not become a native return or a claim that an operation never started; absence reasons follow the chosen contract | Pending |
| 1B | Same observed failure with rich, missing, or truncated text | Worker diagnostic publication, host decoding/classification, and CLI preservation | Identical justified operation/status classification across diagnostic availability | Pending |

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
| Validator lifecycle | Partial-result return retains evidence, but kill/wait results are unchecked and zero-initialized wait storage is decoded | Apply the step-0 host observation contract to the validator, preserving verdicts alongside cleanup errors |
| Controller reply capture | Full subprocess output is collected before only a 1 MiB prefix is retained/parsed | Receiver-owned loss with exact received-byte count and retained-prefix count, distinct from malformed producer JSON; this is not a streaming memory bound |
| Execution budgets | Worker nominal 60s polling budget, synchronous validator hook with 30s I/O, client default 240s | Observer-owned deadlines with phase, process status, and partial evidence; readiness, policy transfer, and hook time are not one end-to-end worker deadline; `--timeout-ms` does not set all budgets |
| Readiness and child lifecycle | Ready-byte timeout, spawn failure, early exit, post-apply hang/signal, and cleanup grace | Distinguish synchronization hints, actual stops, and unexplained termination |
| Denial-log correlation | Optional capture; `first_deny` summary currently gated by a sandbox-cause outcome | Independent correlation with observed execution facts; a matching denial does not establish termination cause |
| Early or uninstrumented stderr diagnostics | No usable shared-memory report, direct dependency/runtime output, or reporting-path failure | Deferred capture evaluation; process status alone cannot recover diagnostic detail |
| Optional compiled-object capture and exec output | 1 MiB capture region; 1,023 payload bytes per child output stream | Explicit unavailable/truncated evidence; optional capture failure must not become specimen failure |
| Earlier setup and transport | Request decoding, library loading, shared-memory/pipe setup, XPC loss, reply encoding/decoding | Reporting by the component that actually observed failure; fallback where no child report is available |

- [ ] Trace each boundary to its final CLI representation, including diagnostics
  that are only emitted on stderr or replaced during cleanup. Use the existing
  validator partial-result behavior as a source of reusable patterns. Its
  `.failure(error, partial)` shape is useful, but is not evidence that its process
  status or result association is already correct.
- [ ] Repair validator termination/reaping observations using the step-0 host
  contract. Retain termination-call results and obtain exit/signal status only
  from successful reaping; keep parsed verdicts when cleanup fails. Add driver,
  classifier, and JSON controls for failed kill/reap and abnormal exit after
  verdict production. An adequate verdict count must not conceal a process
  failure or an unconfirmed disposition. Do not infer clean exit merely from the
  driver's `.success` case.
- [ ] Preserve validator diagnostics that cannot be joined to a step. The C batch
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
- [ ] Preserve valid validator frames before an invalid UTF-8 frame. The current
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
- [ ] Group changes around a shared reporting path and its evidence contract.
  First examine excess steps and excess parameters: keep their local capacity
  checks, but try to route both through the same host-admission failure record
  and forwarding code. The consumer should not need a case for each field.
- [ ] Move the unchanged source cap into the shared contract and reject oversized
  source in host admission with field, actual UTF-8 length, and maximum. Verify
  C/Swift agreement, retain the worker's defensive check, and keep distinct tests
  for admission, the worker guard, and a child interrupting policy transfer.
- [ ] Add acceptance cases for every member of a proposed group. Assert origin,
  affected field, actual/allowed values and units, process presence or absence,
  and retained evidence. Where byte boundaries matter, cover exact/over-limit
  and multibyte input; for NDJSON measure encoded framing, not just source text.
- [ ] Review the diff for actual reuse. A shared checker alone does not show that
  production routing is shared. Record which inventory entries one change closes
  and why, or explain why distinct handling is needed. Closing several entries
  together is an aspiration, not a quota that justifies a generic framework.
- [ ] Preserve distinctions among local admission rejection, child-reported
  failure, supervisor action, and reply loss. Avoid manufacturing worker records
  for host-only failures or relabeling a receiver's truncation as sender corruption.
- [ ] Do not close the controller-capture entry merely because a truncation flag
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
- [ ] Recheck the correlation path revised in step 0 against the observer records
  adopted in step 1. Preserve independently obtained predictions and kernel events
  when an attempt lacks a completed result. A post-apply gap must not default to
  either policy interference or an instrumentation defect.
- [ ] Evaluate capture of early or otherwise uninstrumented stderr diagnostics
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
- [ ] Keep `sbpl-check` on the missing-reply path as an independent observation.
  Its admission refusal already reaches `policy_check_status` as a distinct
  outcome; keep that distinction in the startup note prose, which reports any
  non-compile as failed. A successful helper compilation does not explain the
  missing worker reply or establish the worker's last stage; no reply does not
  prove the worker never published a record.
- [ ] Keep every existing capacity and budget fixed. For the controller's capture
  boundary, make loss explicit; whether parsing should have a separate/larger
  budget is a later decision. Do not promise preservation of a record inside an
  envelope the receiver could not retain or decode.
- [ ] Account for affected diagnostic, schema, and outcome documentation and
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

- [ ] Choose a bounded test arrangement after the record format exists: direct
  decoder/forwarding controls and, if practical, a test-only producer exercising
  the worker-to-CLI route. Use at least two unfamiliar codes and distinct payloads
  without registering them in production outcome mappings. Extend the basic
  step-1A control; prefer a separately built fixture selected by the existing
  `worker_executable_path` boundary override. Keep its source and controlled
  payloads in test equipment, its executable outside the inspected app, and the
  override mirrored in the final reply. It must obey the supported ABI's real
  publication protocol; it does not establish production failure attribution.
- [ ] Carry each record through the applicable C/Swift decoding, runner encoding,
  client forwarding, and controller parsing boundaries. Check the final record's
  producer, operation, code/domain, and diagnostic detail against the independently
  supplied input. If a layer cannot be exercised, state that coverage gap.
- [ ] Require an unsuccessful/incomplete run to remain so. Do not infer a sandbox
  denial or compiler/apply failure merely from an unfamiliar code; preserve any
  independently established operation result. A generic summary is acceptable
  when the original record remains available. A known failure reported alongside
  it must retain its own evidence.
- [ ] Include controls for absent, unpublished, malformed, and incompatible
  records. Confirm that structural validation remains effective while an
  unfamiliar but valid code is preserved. Exercise declared diagnostic truncation
  separately from code recognition.
- [ ] Demonstrate that a temporary known-code-only forwarding path, or one that
  drops/relabels unfamiliar details, fails the preservation controls. Keep such
  mutations out of production commits and retain their failure evidence.

Synthetic records in this experiment establish transport behavior only. Keep
them in test equipment; do not add a production override that forces a result
or normalized outcome. Real-failure cases from steps 1 and 2 must continue to
establish correct attribution at the producer. If the experiment reveals another
recognition-dependent boundary, fix that boundary and rerun the same controls
instead of adding the unfamiliar code to an allowlist.

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

Select verification according to the changed boundary: C harness and ABI layout,
Swift classifier/envelope tests, validator transport tests, controller parsing
tests, and real CLI cases. Include `source_drift` when outcome constants or
coverage registrations change; it is required for step 0. Register new cases and
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
| Completed implementation batch | None; implementation has not started |
| Next batch | Step 0A: define the interim contract and capture the regression; 0B repairs host observations, then 0C completes the public contract and step-0 acceptance gate |
| ABI revision state | Existing ABI version 5 is the accepted baseline; no new revision is under construction |
| Chosen field contract locations | Step 0 of this plan specifies response version 5, explicit per-step signal null, and semantic absence for optional subprocess objects; implementation and authoritative API documentation are pending. The interim evidence/classification table is pending in 0A, authoritative host observation fields in 0B, and the combined public contract in 0C; new worker fields remain step 1A work. |
| Inventory entries closed / remaining limitations | None closed; implementation and acceptance work remain pending. A transfer deadline for an open but undrained policy pipe is explicitly deferred; stderr capture remains a deferred coverage question. |
| Verified source and signed app | No implementation build verified; record source revision and local changes, build command, app path, and bundle-integrity evidence when available |
| Checks, results, and evidence paths | No implementation checks run; record exact commands, results, and retained evidence for the completed batch |

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
- Placement of coverage for production C-worker failures; unused Swift apply
  implementation and test removal remain outside this effort.
- The smallest test arrangement that proves unfamiliar-code preservation across
  the full route without introducing result-forcing production seams.
- Where groups genuinely share reporting code, and where separate paths better
  preserve the meaning of the evidence.

Resolve these questions within the relevant step. This plan does not authorize
raising limits or replacing the existing test-equipment plan.

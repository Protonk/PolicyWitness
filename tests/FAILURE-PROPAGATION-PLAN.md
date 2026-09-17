# Failure evidence through the worker, runner, and controller

## Status: outline draft

This is a proposed work sequence, not an implemented contract or a finished
specification. All work below is pending. Record layouts, public field names,
compatibility behavior, and exact test placement need to be settled as each step
is prepared. A preliminary correction precedes the three major steps. Each step
should produce reviewable changes and acceptance evidence before the next begins;
the first major step is divided into smaller implementation batches.

## Goal and scope

Organize failure evidence around the component that observed it. Worker progress,
reported failures, host actions, and process status are independent observations.
A reader should be able to distinguish a PW rejection, an observed library
failure, a supervisor action, and a missing or unusable reply without
reconstructing the implementation from an outcome string. An honest account of
the available observations may leave the cause unknown.

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
  returns that already retain partial output and process metadata.
- `runner/Sources/PWRunnerCore/PWRunnerService.swift` and `PWRunnerAPI.swift`:
  host admission failures and the runner's JSON result types.
- `runner/Clients/PWRunnerClient/main.swift`: reply-byte forwarding and locally
  generated XPC failure results.
- `controller/src/runner_client.rs`, `utils.rs`, and `run_flow.rs`: captured
  output, JSON parsing, the outer envelope, and startup diagnostics.
- `controller/src/bin/sbpl-check.rs` and `controller/src/policy_check.rs`: fallback
  compilation diagnostics, including the helper's own source-size rejection.
- `runner/Sources/PWRunnerCore/SandboxApply.swift` and
  `runner/Tests/PWRunnerCoreTests/SandboxApplyTests.swift`: the Swift apply helper
  and tests whose claimed relationship to the production C worker needs review.
  `computePolicyHash` in the same source file has a separate, live role.
- `runner/AGENTS.md`, `tests/README.md`, and `tests/catalog.json`: test boundaries,
  override rules, canonical case registration, and evidence retention.

Useful existing protection lives in `runner_abi_layout`, `runner_c_worker_harness`,
`runner_unit`, `runner_outcome_bad_request`, `runner_outcome_runner_timeout`,
`runner_ready_byte_resilience`, `runner_validator_failure`, `validator_batch_mode`,
and `witness_contract`. Trace individual assertions before deciding whether to
extend a case or add a complementary one.

## Proposed observer contract

These ownership rules guide acceptance tests; exact public sub-objects and field
names remain open. Preserve existing subprocess blocks as authoritative where
they already serve this purpose. Avoid duplicating facts into several mutable
representations. A layer can summarize another observer's evidence, but must not
rewrite that observer's account or imply an unsupported causal order.

| Observer | Evidence it owns |
| --- | --- |
| Worker | Published progress, failed operation, meaningful native result, and any published diagnostic detail |
| Runner host | Admission decisions, spawn/pipe/readiness observations, deadlines, termination requests and their results, successful reaping, and captured worker stderr |
| Validator | Emitted check results and validator diagnostics; the host separately owns transport loss and process observations |
| Runner client | Received reply bytes or its own XPC error/timeout observations |
| Controller | Client invocation, capture and parsing observations, local rejection or truncation, and the outer summary |
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
- Completed attempts, available predictions, and their provenance survive later
  failures when received intact. Missing observations do not establish agreement
  or disagreement. Do not blanket-reset valid step evidence on run failure.
- Diagnostics themselves may be bounded. Specify publication validity and any
  truncation explicitly so a shortened message remains distinguishable from a
  complete one. No design can guarantee delivery after every possible process or
  transport failure; the closest surviving observer must state what it knows.
- A signal after application, without a host kill, does not establish that the
  sandbox sent it. The worker's self-signal test seam produces that same shape.
- A fallback compilation result describes that helper's execution. It cannot
  establish how far a missing worker progressed or why its reply was lost.

## Work sequence

### 0. Correct unsupported attribution using the existing ABI

Make a small, independently reviewable correction before adding new worker
fields. Specify an interim evidence table and its limits rather than merely
reordering the classifier's branches.

- [ ] Stop treating unpublished `apply_rc`/`apply_errno` storage as a reported
  failure. For legacy pre-apply failures, require the worker's `done` publication.
  Even then, `apply_rc = -1` can describe parameter setup or compilation; the
  interim diagnostic must not claim an observed apply return when it cannot
  distinguish the operation. A published zero or inconsistent flags do not
  establish failure either. Successful application has its own `applied` marker.
- [ ] Distinguish pre-apply exit, signal, and host-enforced deadline using the
  evidence already available. A clean exit without completion does not establish
  a timeout. A published failure followed by cleanup trouble must retain both
  observations; do not unconditionally let a later kill replace an earlier report.
- [ ] Include the meaning of `runner_sandbox_denied` in this review. Decide and
  document interim outcome semantics and compatibility explicitly. A stage marker
  cannot make a post-apply signal prove kernel sandbox attribution. Do not retain
  that inference merely because an existing test expects the label.
- [ ] Audit the production reachability of tests credited with protecting these
  decisions. Verify callers of `applySandboxPolicy`; its Swift tests do not by
  themselves exercise C-worker failures. Correct coverage claims and add coverage
  at the live boundary. Removing unused implementation is a separate decision;
  preserve unrelated live helpers in the same file.
- [ ] Add classifier rows for absent publication, inconsistent flags, pre-apply exit and signal,
  pre-apply host termination, and reported failure plus cleanup trouble. Use the
  existing pre-ready delay seam for a real CLI deadline case. Preserve existing
  successful, post-apply timeout, and partial-result contracts.

This step removes claims unsupported by the existing evidence. It does not make
the legacy status fields sufficient to distinguish all failed operations.

### 1. Establish observer-owned progress and failure reporting through to the CLI

#### A. Specify progress and publication, then implement the minimal record

- [ ] Define a small set of useful worker milestones. For each, state whether it
  means an operation started or completed and what an acquire reader can rely on.
  Specify optional transitions and failure exits. Readiness can fail while the
  worker proceeds; `done` is also published following compilation failure. Do not
  infer successful application from a simple ordering of all stage numbers.
- [ ] Settle the minimum failed-operation record and its publication rules,
  independently of diagnostic text. Distinguish no report, a valid report with
  zero values, and an incomplete or incompatible report. Keep native call results
  distinct from PW's own diagnostic codes. An unfamiliar stage value must not be
  interpreted as successful application merely because its number is larger.
- [ ] Implement worker publication in preallocated, pre-touched shared memory.
  Publish payload validity with release/acquire ordering; document its relation
  to progress, `applied`, `done`, and per-slot completion. Keep the post-apply path
  free of new allocation and diagnostic I/O dependencies. Failures before a usable,
  compatible mapping exists still need a supervisor-only fallback.
- [ ] Review when the host observes progress and takes its final snapshot around
  reaping. Account for publication during timeout/cleanup and preserve confirmed
  slots. Record readiness already observed by the host. Inspect ignored signal
  and wait results rather than copying them into fields with stronger meanings.
- [ ] Carry worker evidence and host observations through `CWorkerOutput`, the
  orchestrator, runner JSON, client forwarding, and controller envelope. Reuse
  the client's byte forwarding and the controller's opaque JSON retention where
  they already work. Distinguish failed operations in the evidence before deciding
  which merit separate top-level outcome strings.
- [ ] Settle ABI and JSON compatibility before choosing offsets. The header's
  reserved space is an option, not a specification. Update the C/Swift layout
  and version together as needed, extend layout checks, and specify incompatible
  worker behavior. Include a basic unfamiliar-diagnostic-code preservation control
  now; step 3 will exercise the additional routes introduced later.

#### B. Prove reporting with compilation failure and add diagnostic detail

Use an ordinary SBPL syntax error as the central real-worker proving case. It
isolates a deterministic failed operation without requiring a policy-pipe failure.
Sparse-evidence cases remain separate acceptance obligations.

- [ ] Show the compilation failure reaching the normal CLI, distinguished from
  parameter setup and an observed apply result. Keep the minimal operation/status
  change reviewable separately from diagnostic-text storage and forwarding.
- [ ] Choose bounded diagnostic storage and capture deliberately. Evaluate a
  worker text region and host stderr capture according to the evidence each can
  retain; do not automatically build two copies of the same diagnostic channel.
  Make missing, partial, and truncated text explicit. Publishing reliable status
  must not depend on a successful diagnostic write.
- [ ] If capturing stderr, specify draining during policy transfer and waits,
  buffer exhaustion, dropped bytes, EOF, and cleanup. Ignoring SIGPIPE does not
  prevent a full pipe from blocking. Treat captured bytes as host-observed context;
  do not parse prose into authoritative failure classifications. Preserve and test
  the rule against worker diagnostic writes after successful application, where
  they could create denial evidence attributable to instrumentation.
- [ ] Verify the compiler diagnostic reaches the CLI, while controls with absent
  or incomplete text retain the same justified operation/status attribution.

#### C. Retain sparse-evidence and competing-failure cases

Compilation failure is not sufficient acceptance for this step. The worker maps
and validates shared memory before reading source, so oversize-source rejection
can publish a record before exiting. Acceptance must exercise preservation of
that record through a simultaneous pipe failure.

- [ ] Exercise oversized source through the worker guard and account for its
  report, last progress, and process status. Fix the host's policy-write failure
  path to preserve evidence when a child stops reading; do not kill-and-discard
  its status or lose the report through EPIPE/SIGPIPE handling. Record local pipe
  failure and child evidence independently, retaining bounded cleanup.
- [ ] Keep a host-driver test for a child that stops consuming input even after
  source admission moves upstream in step 2. Test report-present and report-absent
  behavior at suitable boundaries, without requiring one timing-dependent race.
- [ ] Include early failures before publication, unexpected termination, and a
  report followed by cleanup trouble. These remain first-class acceptance cases
  even when ordinary admission prevents a particular specimen from reaching them.

Acceptance should cover the following observations, with expected facts written
before implementation. Exact diagnostic prose need not be fixed.

| Case | Evidence that must reach the consumer |
| --- | --- |
| Ordinary successful specimen | Existing attempt/prediction evidence; no fabricated failure record |
| Source exceeds the existing worker cap at the worker boundary | Worker rejection and relevant byte limit; last progress and process evidence retained even if the policy pipe also fails |
| Ordinary SBPL syntax error | An actual compilation failure and its diagnostic, distinguished from an observed application result |
| Observed application failure | Operation and meaningful native result retained; use a deterministic existing test boundary if no reliable live specimen reaches it |
| Existing pre-ready delay exceeds the worker budget | The host's deadline/termination observations, with no invented library failure |
| Unexpected worker exit without a report | Actual process status and absence of a report; unknown underlying cause |
| Child stops reading during host policy transfer | Host pipe error, available worker evidence, and reaped status or explicit failure to obtain it |
| Failure report followed by cleanup trouble | Original reported failure and subsequent supervisor observations both survive |
| Failure after completed probes | Completed step evidence and independently checked effects survive |
| Unpublished or incomplete record | No payload fields treated as confirmed evidence |
| Valid report with absent/truncated text | Reliable operation/status attribution survives the missing detail |

Use real worker failures and existing override boundaries for CLI coverage.
Use the C harness for publication/early-exit behavior and Swift unit tests for
states that cannot be reached reliably through existing seams, following
`runner/AGENTS.md`. A controlled child can establish unexpected termination;
its status is evidence about process handling, not sandbox policy behavior.
Publication claims need review of the synchronization protocol as well as tests.
Do not use a convenient syntax-error case as a substitute for early-exit and
missing-report coverage, or use synthetic transport records to claim production
failure attribution coverage.

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
| Fallback `sbpl-check` | 4 MiB source cap | Helper-owned admission rejection; distinguish declined compilation from compiler rejection |

Runtime evidence loss and observation boundaries:

| Pending boundary | Current constraint or seam | Candidate route to examine |
| --- | --- | --- |
| Policy transfer and early exit | Worker stops reading while host writes | Host pipe observations plus available worker report and process status; retain step-1 protection after admission changes |
| Validator request framing | 65,536-byte line buffer; newline and JSON encoding affect usable payload | Validator-owned parse/size evidence through batch transport; preserve earlier verdicts and missing step identity honestly |
| Controller reply capture | 1 MiB prefix currently used for JSON parsing | Receiver-owned capture-limit evidence, distinct from malformed producer JSON |
| Execution budgets | Worker nominal 60s polling budget, validator 30s I/O, client default 240s | Observer-owned deadlines with phase, process status, and partial evidence; `--timeout-ms` does not set all budgets |
| Readiness and child lifecycle | Ready-byte timeout, spawn failure, early exit, post-apply hang/signal, and cleanup grace | Distinguish synchronization hints, actual stops, and unexplained termination |
| Optional compiled-object capture and exec output | 1 MiB capture region; 1,023 payload bytes per child output stream | Explicit unavailable/truncated evidence; optional capture failure must not become specimen failure |
| Earlier setup and transport | Request decoding, library loading, shared-memory/pipe setup, XPC loss, reply encoding/decoding | Reporting by the component that actually observed failure; fallback where no child report is available |

- [ ] Trace each boundary to its final CLI representation, including diagnostics
  that are only emitted on stderr or replaced during cleanup. Use the existing
  validator partial-result behavior as a source of reusable patterns.
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
- [ ] Keep `sbpl-check` on the missing-reply path as an independent observation.
  Report its admission refusal separately from compiler rejection. A successful
  helper compilation does not explain the missing worker reply or establish the
  worker's last stage; no reply does not prove the worker never published a record.
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
  without registering them in production outcome mappings.
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

Select verification according to the changed boundary: C harness and ABI layout,
Swift classifier/envelope tests, validator transport tests, controller parsing
tests, and real CLI cases. Register new cases and update `tests/README.md`,
`tests/COVERAGE.md`, suite documentation, and public JSON documentation as needed.
Run relevant existing success, timeout, and partial-evidence cases alongside new
failure cases. Acceptance must check evidence and provenance as well as any
normalized outcome contract. Review the diff and run `git diff --check`.

Each handoff should identify the implemented contract, grouped inventory entries
closed, remaining limitations, exact tests and results, and evidence paths.
Explain any changed outcome semantics without turning current-behavior docs into
a change history. Leave unchecked work visibly pending.

## Decisions still open in this draft

- Exact milestone meanings, optional transitions, publication protocol, and final
  host observation points; then the shared-memory layout and ABI compatibility.
- Public representation of observer-owned evidence, reuse of subprocess metadata,
  and JSON compatibility without duplicated authoritative facts.
- Minimal failed-operation/status representation and the subsequent choice of
  bounded text storage, stderr capture, or distinct justified uses of both.
- Summary precedence for multiple observations and the compatibility treatment of
  outcomes whose present names or rules imply unsupported causes, particularly
  `sandbox_apply_failed` and `runner_sandbox_denied`.
- Placement of coverage for production C-worker failures and the disposition of
  unused Swift apply implementation and its separately scoped tests.
- The smallest test arrangement that proves unfamiliar-code preservation across
  the full route without introducing result-forcing production seams.
- Where groups genuinely share reporting code, and where separate paths better
  preserve the meaning of the evidence.

Resolve these questions within the relevant step. This draft does not authorize
raising limits or replacing the existing test-equipment plan.

# Architecture review implementation plan

This is a daughter of the
[architecture doc buildout plan](ARCH-DOC-BUILDOUT-PLAN.md). It covers the
bounded implementation fixes agreed during review and the tests needed to
establish them. The parent retains the strain register and architecture
closeout; this plan owns implementation and acceptance for the rows below.

| Parent rows | Required behavior | Investigation |
| --- | --- | --- |
| 18 | Admit observer kind and versions before report interpretation | [Observer envelope admission](../records/OBSERVER-ENVELOPE-ADMISSION.md) |
| 13 and 17 | Admit one request per host across connections; only its owner schedules exit | [Single use admission](../records/BYOXPC-SINGLE-USE-ADMISSION.md) |
| 20 | Bound policy delivery and retain truthful transfer and cleanup observations | [Policy transfer deadline](../records/WORKER-POLICY-TRANSFER-DEADLINE.md) |

## Status

Planned; implementation has not started. Writing and committing this plan
does not credit any implementation or acceptance test below.

- [ ] Establish regression controls and record the baseline failures.
- [ ] Implement and validate observer admission.
- [ ] Implement and validate process-wide single-use admission.
- [ ] Implement and validate bounded policy delivery.
- [ ] Reconcile contracts, documentation and plan dispositions; pass the
  final acceptance gates.

## Scope and retained limits

Implement the three changes in the order above as separately reviewable
groups. Each group includes its controls and required reader/documentation
changes. Routine implementation choices belong to this work; record the
reasoning and evidence for material choices in the execution notes below.

Entitlement installation, parent row 19, remains a separate decision. This
plan changes no signing policy for the host, worker or validator. It also
adds no queuing, automatic specimen retries, CLI flags or global cancellation
mechanism. A connection racing with host retirement may still fail before a
refusal arrives. A transfer deadline bounds delivery, not kernel exit latency,
the final blocking reap or the lifetime of every descendant.

Preserve caller authorization, the query-before-attempt release barrier and
the separation of execution and log evidence. Read
[runner/AGENTS.md](../runner/AGENTS.md) before changing runner test machinery.
Internal controls may replace unreliable clock, I/O, kill, wait or scheduling
boundaries; they must not manufacture successful specimen results or summary
outcomes. A fixture that does not apply a sandbox establishes transport and
lifecycle behavior, not a kernel policy cause.

## Establish the regression baseline

Record the starting commit, commands, equipment and artifact paths. Add a
valid positive control alongside each refusal or timeout control. Expected
results must follow the contracts and independently observed effects, rather
than being calculated by the code under test.

Demonstrate that the controls detect the original defects: unsupported
observer frames are interpreted, distinct service objects independently admit
requests, and a stalled policy reader prevents the driver from reaching its
timers. Where a new internal seam prevents directly running a test against the
original source, use a narrowly reverted implementation in a disposable copy
and record which regression it restores. A broad mutation framework is not
required. Keep mutations outside the app used by the acceptance run.

Use explicit gates and receipts to order concurrent operations. Do not rely
on repeatedly racing the host's 50 ms exit delay. Run possible hangs under
an independent watchdog that owns cleanup of the driver and its children.
Watchdog intervention fails the control; it cannot count as a PW timeout.

## Observer admission

### Implementation

In [sandbox_log.rs](../controller/src/sandbox_log.rs), gate bounded JSON
capture by the expected outer kind and exact supported envelope version
before reading report fields. Admit the inner report version before reading
its semantics. Use the generated frame constant and preserve the existing
valid-report, identity, window and supervision checks.

Retain an inadmissible payload as opaque evidence. Produce no body-derived
denial events, blocked reason, step associations or missing-record
conclusions. Keep independent transport timeout, overflow and cleanup
observations with their existing precedence. An intact, completely delivered
but inadmissible report follows the invalid-reply path.

Apply the same interpretation boundary in
[consumer.py](../tests/lib/consumer.py) and
[log_capture_contract.py](../tests/lib/log_capture_contract.py). The capture
wrapper still receives ordinary validation; opacity applies to the rejected
nested payload. Preserve the distinction between a valid envelope carrying
rejected evidence and a test that specifically requires successful capture.

### Tests and acceptance

Extend the receiver tests in `sandbox_log.rs` and the independent controls in
[checker_controls.py](../tests/suites/blackbox_e2e/checker_controls.py) and
[log_capture_controls.py](../tests/suites/witness_contract/log_capture_controls.py).

- A complete report with both current markers retains its events and can
  supply correlation. Repair the existing positive fixture that omits the
  outer version before deriving refusal cases from it.
- Independently exercise missing/wrong kind; missing, malformed, older and
  newer outer versions; and an unsupported inner version under an admitted
  outer frame. Include null, string and Boolean version values.
- Put convincing deny events and malformed or unfamiliar fields in rejected
  bodies. Require unchanged opaque retention and no recovered log claims or
  downstream body-shape errors. Keep controls proving that malformed wrapper
  fields and malformed admitted bodies are still rejected.
- Combine an inadmissible body with independently recorded transport timeout
  and overflow. The body's collection fields cannot supply transport facts.
- Feed actual receiver results through envelope assembly and the consumer.
  Extend `collector_states_preserve_the_serialized_execution_half` in
  [run_flow.rs](../controller/src/run_flow.rs) so serialized execution fields
  remain identical across accepted, rejected and unavailable log evidence.

These controls belong in the default offline batches. They require no live
kernel denial or privileged unified-log access. Acceptance requires both
semantic refusal and preservation of valid capture and independent evidence.

## Process wide single use admission

### Implementation

Give all exported service objects in one host the same synchronized
admission state. Claim it atomically on entry to the first authorized
`runSpecimen`, before decoding or child creation. Merely accepting a
connection does not claim it. Keep the claim terminal through reply and exit,
including when the owning request fails input admission.

In [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift),
separate the owner's reply-and-exit path from subsequent requests' reply-only
`already_ran` refusal. Only the owner may schedule process exit. Retain the
existing normal reply flush delay; it is not a readiness protocol for another
run.

### Service level controls

Add Swift tests through the real request method on distinct service objects,
with narrow internal controls that observe execution entry and scheduled
exit. Record those observations independently of response labels. Register
the tests in [main.swift](../runner/Tests/PWRunnerCoreTests/main.swift).

- Competing requests sharing one host state produce exactly one owner and
  one entry into specimen execution. Include simultaneous claims and
  deterministic cases with the owner held at a gate.
- Refusal schedules no exit while the owner is active or after its reply.
  This must catch the incomplete fix that shares `didRun` but still calls
  `replyAndExit` on rejection.
- An idle connection consumes no admission. A first request that fails
  decoding or input admission consumes the host and schedules only its own
  exit; later requests remain refused.
- A fresh host state accepts a new request. Existing caller-authorization
  controls remain applicable and passing.

### Live BYOXPC control

Add an explicitly selected case under
[runner_byoxpc](../tests/suites/runner_byoxpc/README.md), using its owned
installation/session machinery and a test client signed for the host's
caller-auth requirements. The client opens two connections to the same
installed host. Hold the first request at an observed worker gate before
reply, then send the second. Require its refusal, release the owner, and
require the owner to finish successfully.

Retain host identity, request/reply records and independent worker invocation
or effect receipts. The evidence must establish the same host served the
connections, only the owner entered specimen work, and the rejection did not
terminate it. Use a test-owned fixture or gate at a real boundary; preserve
the inspected app's bytes. After confirmed retirement, a fresh host must be
able to serve a normal request. Transport failure during retirement remains
permitted and does not justify resubmitting a specimen of unknown execution.

The current
[Mach-service liveness test](../tests/suites/runner_mach_service_liveness/README.md)
does not serve connections and cannot substitute for this control. Live
coverage stays outside the default battery because it needs a signed app,
matching signing equipment and a GUI launchd session. It is a required
acceptance gate for this change, alongside the default service-level tests.

## Bounded policy delivery

### Implementation and contract decisions

Make the host's policy write endpoint nonblocking before delivery. In
[CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift), start one
absolute monotonic deadline immediately after successful spawn and before
the first write. Fail into cleanup if nonblocking setup cannot be established.
Account for partial writes; wait for writability using the remaining budget;
check the deadline through interrupted calls, backpressure and progress.
Never restart the deadline. Preserve `SIGPIPE` protection and handle
zero-progress writes explicitly.

On failure or expiry, close the write endpoint, skip normal ready/sentinel
polling and enter the existing exit-request, grace and termination sequence.
Preserve partial worker publications and independent kill/reap observations.
Successful delivery continues through the existing readiness and execution
path.

Before implementing the wire change, choose and record:

- An internal production transfer budget, documented in
  [limits.json](limits.json), with a short setting available to driver tests.
  Explain its relationship to existing phase and client budgets; it does not
  establish end-to-end cancellation.
- An explicit host timeout observation and its disposition/summary mapping.
  Preserve `policy_transfer_error.errno` as an errno actually returned by a
  failed write. Prefer additive evidence that keeps this meaning intact;
  do not synthesize an errno for timer expiry. Counts record bytes accepted
  by writes, not bytes read or interpreted by the child.
- Required reader, shape-golden and contract-version changes under
  [CONTRACT.md](CONTRACT.md#when-a-number-moves). Do not assume a version bump
  is unnecessary merely because one field is added if reading rules change.

Update the producer, disposition interpretation, Rust/Python readers and
contract controls together. No additional public request option is needed
solely to shorten the driver test's budget.

### Real pipe and deterministic controls

Extend the [worker lifecycle fixture](../tests/fixtures/worker_lifecycle/README.md)
with a mode that reads only a short command prefix, then keeps stdin open
without draining the rest. Exercise the real driver and pipe from the
[worker evidence tests](../runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift)
or a dedicated registered Swift group. Use an admitted payload large enough
to cause observable backpressure. The real worker's pre-ready delay occurs
after policy consumption and cannot reproduce this condition.

- Require PW's transfer timeout to initiate cleanup before the independent
  watchdog intervenes. Assert the chosen host timeout record, consistent
  write counts, no fabricated write errno, and no validator or attempts.
- Retain a positive case in which the fixture drains the pipe and confirms
  complete, unmodified policy bytes, including across partial writes.
- Keep existing closed-input/`EPIPE` controls. Exercise interrupted calls,
  slow progress, zero progress and deadline exhaustion with narrow clock/I/O
  controls; these establish that the total delivery budget cannot restart.
- Extend the cleanup-failure cases in
  [CWorkerLifecycleTests.swift](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift).
  A failed kill or unconfirmed reap cannot erase the transfer observation,
  invent an exit code or upgrade the collection basis. The test independently
  cleans up any child it leaves alive.
- Carry real driver results through reply encoding, controller disposition
  projection and the shared consumer. Test the chosen summary and absence of
  unsupported claims, not only the driver's return value.

The real-pipe control establishes production wiring. Clock/I/O controls make
deadline edge cases deterministic without tight wall-clock thresholds. Use
explicit scheduling tolerance in the real test and distinguish entry to
cleanup from eventual process reaping. Keep these controls in the default
runner and reader batches; watchdog or fixture-equipment failure fails them.

## Integration and acceptance gates

Register new cases and prerequisites in [tests/catalog.json](../tests/catalog.json),
the applicable suite documentation and [tests/COVERAGE.md](../tests/COVERAGE.md).
Update [OPT_IN_TESTS.md](../tests/OPT_IN_TESTS.md) for the live BYOXPC control.
Follow the root maintenance checklist for generated contracts and worker
identity; regenerate identity before direct source tests when its inputs
change. Build lifecycle fixtures outside the inspected app.

Run focused controls after each change, then validate the final combined
state. The acceptance record must include:

1. Default Rust receiver/assembly tests, Python checker/log controls and
   Swift `runner_unit` tests covering the cases above.
2. A normal signed build and the applicable worker harness, ordinary runner,
   caller-authorization and live BYOXPC controls. Use the public test
   dispatcher, fresh owned output directories and its app-integrity checks.
   Missing signing/GUI equipment leaves the live gate unfulfilled.
3. Source-drift, generated contract/limits/architecture checks and reviewed
   shape goldens. If the release store, wait or ordering eligibility changes,
   also run `witness_contract/order_barrier_mutations` as required by
   [AGENTS.md](../AGENTS.md).
4. One final default battery against the completed signed artifact. Record
   retained evidence paths, source snapshot and applicable build; keep any
   failed or incomplete run's evidence according to the test retention rules.

Boundaries that need real XPC, signing or logs must follow the repository's
sandboxed-harness escalation procedure if the harness refuses them. A blocked
live gate is not a passing result. Verify removal of every test-owned external
service before deleting its staging and recovery record.

## Documentation and closeout

Update architecture prose and [architecture.json](architecture.json) to
describe only established behavior; regenerate affected copies rather than
editing them. Remove the three resolved Known gap entries only after their
acceptance gates pass. Retain the entitlement gap and residual retirement and
cleanup limits. Correct the remaining timing wording: nominal polling
allowances are not wall-clock lower-bound guarantees; unbounded delivery
precedes host ready/sentinel budgets while the client timeout is already
active; a stalled reader blocks delivery once pipe capacity is exhausted.

Record the completed dispositions of parent rows 13, 17, 18 and 20, update
the investigation records' status without replacing their original evidence,
and leave row 19 separate. The daughter plan does not finish the parent's
remaining architecture integration work. At parent closeout, retire this
completed plan and its parent link together; if work remains deferred, move
its ownership to an independent plan and remove the daughter-to-parent link
before deleting the parent. Permanent documentation must not link either
temporary plan or the investigation records.

## Execution notes

No implementation or acceptance results recorded yet. Add material budget and
wire decisions, baseline regression evidence, test commands/results, retained
artifact paths and any unfulfilled gate as the work proceeds.

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
timers. Write each regression first and record its failure on the starting
commit. Rust reds use the repository's existing pattern: `#[ignore]` with this
plan as the reason, selected by exact name through a wrapper shaped like
[disposition_reds.sh](../tests/suites/unit/disposition_reds.sh) until the fix
promotes them. TestKit has no ignore mechanism, so a Swift red is run once on
the starting commit through a temporary registration, its log retained in the
execution notes, and registered permanently with the fix. Where a new
internal seam makes a red impossible to express against the original source,
and only then, use a narrowly reverted implementation in a disposable copy
and record which regression it restores. Keep mutations outside the app used
by the acceptance run.

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

- Name the `capture_status` an intact but inadmissible frame produces before
  writing the receiver, and check it against the vocabulary
  [log_capture_contract.py](../tests/lib/log_capture_contract.py) and
  [consumer.py](../tests/lib/consumer.py) accept. A new spelling is a reader
  change and is treated as one.
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
admission state: one object created by `PWRunnerSessionDelegate` and handed
to every `PWRunnerService` it exports, guarded by a lock (`NSLock` or
`OSAllocatedUnfairLock`), because NSXPC invokes each exported object on its
own queue. Claim it atomically on entry to the first authorized
`runSpecimen`, before decoding or child creation. Merely accepting a
connection does not claim it. Keep the claim terminal through reply and exit,
including when the owning request fails input admission.

In [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift),
separate the owner's reply-and-exit path from subsequent requests' reply-only
`already_ran` refusal. Only the owner may schedule process exit. Retain the
existing normal reply flush delay; it is not a readiness protocol for another
run.

Two seams do not exist today and this group adds them, with production
defaults: an injected exit scheduler in place of the inline
`DispatchQueue.global().asyncAfter { exit(0) }`, and an injected orchestration
entry in place of the direct `CWorkerOrchestrator.run` call, so a test can
observe the claim, the entry into specimen work and the scheduled exit
without spawning children or ending the test process. No test today
constructs a service object or calls `runSpecimen`. Both seams follow the
rules for injected controls in [runner/AGENTS.md](../runner/AGENTS.md): they
replace a boundary the test cannot otherwise cross and never manufacture a
specimen result.

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
- Parent row 13 closes here: the `already_ran` row of
  [COVERAGE.md](../tests/COVERAGE.md) stops saying out of scope and cites the
  new case, which the source-drift matrix rule then checks.

### Live BYOXPC control

Add an explicitly selected case under
[runner_byoxpc](../tests/suites/runner_byoxpc/README.md), using its owned
installation/session machinery. The shipped pieces suffice: two concurrent
`policy-witness run` invocations selecting the installed service are two
connections from two client processes, and `pw-runner-client` already
satisfies the host's caller-auth requirement. The first request carries
`_test_overrides.worker_post_apply_hang_ms`, which holds the real worker
after apply for up to a minute; send the second while it is held. Require
the second's refusal, let the hang expire, and require the first to finish
successfully.

The receipts are in the replies: both carry the host's `pid`, which
establishes that one host served both connections; the refusal carries a
null `runner_subprocess` and no steps, which establishes that it entered no
specimen work; the owner's reply carries its worker evidence and its file
effects. Preserve the inspected app's bytes. After the owner's host has
retired, wait out launchd's default respawn throttle before the next step:
the generated plist sets no `ThrottleInterval`, so a run issued within about
ten seconds of the previous launch waits for the remainder, and an immediate
one can fail with XPC error 4097, which inside that window is not a
regression. A fresh host must then serve a normal request. Transport failure
during retirement remains permitted and does not justify resubmitting a
specimen of unknown execution.

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
zero-progress writes explicitly. Build the loop on the nonblocking `poll()`
and monotonic-deadline code that
[ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift)
already uses in the same host, extracted into a shared helper, rather than
on a second deadline implementation with its own edge cases.

On failure or expiry, close the write endpoint, skip normal ready/sentinel
polling and enter the existing exit-request, grace and termination sequence.
Preserve partial worker publications and independent kill/reap observations.
Successful delivery continues through the existing readiness and execution
path.

Before implementing the wire change, choose and record:

- An internal production transfer budget as a [limits.json](limits.json) row
  in the execution section. The limits generator accepts a row only with a
  value-kind check owner (`LimitsContractTests` for the host's compiled
  defaults) and a boundary check, so both are part of this decision, with a
  short setting available to driver tests. State its relationship to
  `worker_ready_wait`, which starts only after it, and to the client's wait,
  inside which it must fit; it does not establish end-to-end cancellation.
- An explicit host timeout observation and its disposition/summary mapping.
  Preserve `policy_transfer_error.errno` as an errno actually returned by a
  failed write; do not synthesize an errno for timer expiry. Counts record
  bytes accepted by writes, not bytes read or interpreted by the child. Both
  shapes available change a reading rule: a sibling object changes the
  contract's rule that omission of `policy_transfer_error` means no observed
  transfer failure, and folding the timeout into that object makes `errno`
  optional, a type change. Plan the response-schema bump under
  [CONTRACT.md](CONTRACT.md#when-a-number-moves) from the start, including
  the version-named fixture directories and stored envelopes it renames.
- The poll stop reason vocabulary. A timeout needs its own spelling beside
  `policy_write_error`, which `project_disposition` in
  [disposition.rs](../controller/src/disposition.rs) filters against a closed
  list, [lifecycle_contract.py](../tests/lib/lifecycle_contract.py) spells
  out, and the failure contract's host-observation tables carry. The failure
  contract's policy-transfer section ends with the sentence that states this
  gap; it goes with the fix.

Update the producer, disposition interpretation, Rust/Python readers and
contract controls together. No additional public request option is needed
solely to shorten the driver test's budget.

### Real pipe and deterministic controls

Extend the [worker lifecycle fixture](../tests/fixtures/worker_lifecycle/README.md)
with a `hold_` mode beside its existing `close_*` modes, which already read a
command prefix and act on stdin: it reads the prefix, then keeps stdin open
without draining the rest, with the test-owned watchdog and host-cleanup
ownership that `close_hang_report` established. Exercise the real driver and
pipe from the
[worker evidence tests](../runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift)
or a dedicated registered Swift group. Use an admitted payload larger than
the pipe's capacity, about 64 KiB on macOS against an admitted policy limit
four times that, because a smaller policy lands in the pipe buffer and never
blocks. The real worker's pre-ready delay occurs after policy consumption and
cannot reproduce this condition.

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
   shape goldens. Run `witness_contract/order_barrier_mutations` for the
   policy-delivery group unconditionally: the release store may be
   untouched, but `runCWorker` is restructured around it, and
   [AGENTS.md](../AGENTS.md) requires the control whenever the wait or the
   release code changes.
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
cleanup limits. The three timing-wording corrections found while planning
are the parent's (its Step 4 corrections 16 to 18) and are independent of
this work.

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

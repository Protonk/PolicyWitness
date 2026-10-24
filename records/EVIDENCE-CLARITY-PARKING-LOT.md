# Evidence clarity parking lot

Recorded 2026-10-14 against source
`93f82c86ab84247318618e5bb877a93624890f07`.

Status: parked design questions. These ideas came from inverting the claims
retained during the documentation review: a sentence can be necessary for
current PW while the design that requires it remains improvable. This record
preserves the larger architecture ideas. It does not schedule their
implementation. No new experiment establishes the proposals below.

Each entry names the current burden, a possible improvement, what would justify
returning to it, and the boundary that would remain. Source links locate the
reviewed implementation; subsequent changes may supersede the observation. A
dated drive-by comment under each entry compares it with the tree on that date.

## Larger improvements

### P1 — Give unfinished cleanup an explicit owner

**Current burden.** A nominal timeout can be followed by a blocking final reap.
For example, `ChildProcessState.terminate` in
[CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) uses a blocking wait
after a successful kill request. A finite observation allowance is consequently
not a total response-time bound.

**Possible improvement.** Separate cancellation requested, cancellation
acknowledged and termination observed. After bounded observation, transfer any
unfinished cleanup to an explicit owner with a durable recovery record. Define
how ownership survives host exit and how recovery verifies absence. An unresolved
child must remain visible rather than disappearing when a reply is sent.

**Revisit when.** There is a concrete latency or recovery requirement worth the
additional process and persistence model. First prototype who can reap the child
on macOS, including host death, failed termination, interrupted ownership transfer
and PID reuse. Require controls for recovery and repeated cancellation before
promising a total operational bound. Review the architecture manifest and every
affected lifetime channel.

**Boundary retained.** Sending a signal does not establish termination. PW cannot
promise instantaneous kernel cleanup. Preserve fresh sandbox processes and never
reuse a worker whose execution or cleanup remains unresolved. Converting polling
to elapsed deadlines in the six-item plan does not solve this ownership problem.

**Fable drive-by comment, 2026-10-22, against `9e574fc`.** The burden stands.
The `ChildProcessState` contract in
[CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) still says that
after a successful kill the blocking wait remains, that an unconfirmed
disposition may leave a live child or zombie, and that no global reaper or new
lifecycle timeout exists. The visibility half of the boundary was met on
2026-10-18: `924a6ed` separated exec observation from cleanup evidence, so an
unresolved child now appears as a reap stop reason such as
`ownership_unconfirmed` or `deadline` with a collection basis of
`execution_may_continue`, and [WORKER.md](../docs/WORKER.md) rows s7 and s36a
state that unconfirmed cleanup can outlive the driver. Ownership transfer, a
durable recovery record and a total response bound are untouched. The revisit
trigger has not fired. The nearest signal is finding 2 of the PAWL feedback in
`records/USER-EXPERIENCE-REPORT.md`, where a consumer reconciles worker and
validator termination records itself because PW does not bound completion.
Leave parked; the remaining ask is ownership, not visibility.

### P2 — Preserve more log identity and timing

Historical scope: this entry and its dated review concern the retired observer
in the archive. They do not propose collector work in maintained PolicyWitness.

**Current burden.** The current denial event in
[sandbox_log.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/sandbox_log.rs) has PID, process, operation,
path and raw text, without a structured event timestamp. The observation window
uses rounded, padded wall-clock bounds; repeated operations and PID reuse can
leave several possible associations.

**Possible improvement.** Preserve structured event times and a stronger process
identity when the underlying source supplies them. Retain clock provenance and
uncertainty, and use the added evidence to narrow candidate associations. Do not
infer unavailable identity fields from matching names or neighboring lines.

**Revisit when.** A captured sample demonstrates useful fields and a stable
parsing route. Test repeated identical operations, multiple candidate steps,
reused PIDs, delayed delivery, missing fields and clock discontinuities. Version
the observer/envelope reading rules as needed, preserving raw records and
best-effort capture behavior.

**Boundary retained.** Better association still does not prove complete log
delivery or unique causal attribution. Missing denial lines cannot establish
that no denial occurred, and a nearby event cannot by itself explain a process's
termination.

**Fable drive-by comment, 2026-10-22, against `9e574fc`.** The burden stands
verbatim: `SandboxDenyEvent` in
[sandbox_log.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/sandbox_log.rs) carries PID, process,
operation, path and raw line, and the
[guide](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/docs/PolicyWitness.md#denial-log-correlation) still says structured
event timestamps, step ordering and PID-reuse protection are unavailable. The
revisit condition is met, though. The observer runs `log show --style syslog`,
so every raw line already begins with a timestamp;
[check_deny_capture_window.py](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/tests/suites/witness_contract/check_deny_capture_window.py)
parses it, with a comment that production makes no temporal claim, and a unit
test in [sandbox-log-observer.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/bin/sandbox-log-observer.rs)
asserts the serialized event has no `timestamp` key. The sample and the parsing
route exist; what is missing is the decision to expose the field, and the
controls this entry lists for repeated operations, reused PIDs and delayed
delivery. Since this entry was written, two association defects of a different
kind were found and are the better-evidenced work: the read_fresh operation
admission corrected in `4ec0a52`, and the exec row's `process-exec*` spelling
recorded in `0e253b5` under `records/exec-row/`, whose sketch also names
interpreter execs as an open edge. This is the one entry ready to move into a
plan; that plan would need a reading-rule version decision under
[the wire contract](../docs/CONTRACT.md).

### P3 — Resume notarization from retained submission evidence

**Current burden.** [notarize.py](../notarize.py) retains the archive and submission
ID, submits once and waits once. An unresolved response stops the release flow;
the operator must inspect the retained evidence before continuing.

**Possible improvement.** Add an explicit resume path keyed by the stored
submission ID and archive digest. Reuse the retained `submitted.zip`, verify its
hash, query the existing submission and continue only after a recognized result
for that same submission. Preserve each observation and establish that later
stapling or packaging uses the corresponding artifact.

**Revisit when.** Recovery can be tested independently from new submission.
Cover incomplete receipts, archive changes, mismatched IDs, unavailable service,
unknown status, rejection and acceptance. Demonstrate that resume neither rebuilds
the artifact nor silently submits it again. Integrate with the existing release
attempt and rotation ownership rules before exposing an operator command.

**Boundary retained.** Apple can remain unavailable or return an unrecognized
state. Such a state still stops continuation. An acceptance for one archive does
not authorize publication of different bytes.

**Fable drive-by comment, 2026-10-22, against `9e574fc`.** Unchanged and
untriggered. [notarize.py](../notarize.py) still submits once and waits once,
and has not been edited since 2026-09-28. [SIGNING.md](../docs/SIGNING.md)
states that the code adds no polling loop, retry, resubmission or resume state
machine, and gives the manual recovery procedure: a new evidence directory, the
retained ZIP and its hash, one `notarytool submit --no-wait`, then one bounded
`notarytool wait` on the returned submission ID. The 0.3.2 release reached a
stapled app whose acceptance is pinned in
[tests/RETAINED.json](../tests/RETAINED.json), and no retained evidence records
an unresolved notarization response. The revisit condition, recovery testable
independently of a new submission, has no equipment yet. Leave parked.

### P4 — Clarify admission around host retirement

**Current burden.** The disposable host's admission and retirement path in
[PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)
can meet a new request while the host is retiring. Launch throttling and the
one-request host rule do not eliminate that race.

**Possible improvement.** Define an admission acknowledgement or refusal that
distinguishes an explicitly unexecuted request from one whose execution may have
begun. Permit a bounded retry only when the former is established. Assess whether
the protocol needs a request identity to preserve this distinction across a
connection transition.

**Revisit when.** A controlled retiring-host experiment reproduces the user-visible
failure and establishes the exact loss boundary. Test refusal before admission,
death after admission, execution with a lost reply, reconnection and retry-budget
exhaustion on standard and BYOXPC runners. Keep launchd configuration, admission
and client behavior in one account.

**Boundary retained.** A lost XPC reply can leave execution unknown. Blind retry
of `xpc_error` could repeat side effects. Preserve one specimen per host and
worker, and never claim exactly-once execution from an acknowledgement alone.

**Fable drive-by comment, 2026-10-22, against `9e574fc`.** Substantially
addressed for external runners on 2026-10-17 by `6fd44fb`. The host's
`already_ran` refusal in
[PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)
is the explicit "unexecuted" acknowledgement this entry asked for. The
controller's [runner_acquisition.rs](../controller/src/runner_acquisition.rs)
re-acquires only after an admitted pre-worker `already_ran` with empty steps
and no subprocess report, from a host whose generation it identifies by PID and
executable path and whose retirement it observes, inside the shared RPC wait;
each refused attempt is retained in the envelope's `runner_acquisition`. The
[guide](../docs/PolicyWitness.md) now documents the retirement window beside
the throttle note, which the PAWL feedback had named as the undocumented gap,
and a case in [the catalog](../tests/catalog.json) covers attributed refusals,
bounded waiting and exactly-once effects. Two parts remain parked.
[run_flow.rs](../controller/src/run_flow.rs) supplies the executable path only
for `MachService` targets, so a bundled `XpcService` runner's `already_ran`
never qualifies and gets no retry. And no request identity was added to the
protocol; the "execution may have begun" side of the distinction is still
inferred from reply shape. The retiring-host experiment this entry asked for
exists only on the BYOXPC side.

## Limits that survive these improvements

The useful goal is to remove qualifications caused by avoidable interface and
implementation choices. Several boundaries remain properties of the experiment:
native success and effective access are separate observations; later path
resolution does not recover an earlier target's state; private libraries retain
hidden state; logs can be incomplete; and death can interrupt publication after
an operation has already happened.

Return to a parked idea when it can name an additional observation, a clearer
contract or a failure the apparatus can prevent, together with a control that
establishes that improvement. Move selected work into an associated plan before
implementation. Keep the remaining qualifications attached to their evidence.

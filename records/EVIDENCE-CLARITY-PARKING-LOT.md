# Evidence clarity parking lot

Recorded 2026-10-14 against source
`93f82c86ab84247318618e5bb877a93624890f07`.

Status: parked design questions. These ideas came from inverting the claims
retained during the documentation review: a sentence can be necessary for
current PW while the design that requires it remains improvable. This record
preserves the second group of interface improvements and the larger architecture
ideas. It does not schedule their implementation or add gates to the associated
six-item plan. No new experiment establishes the proposals below.

Each entry names the current burden, a possible improvement, what would justify
returning to it, and the boundary that would remain. Source links locate the
reviewed implementation; subsequent changes may supersede the observation.

## Interface improvements to revisit

### P1 — Name compiled-profile capture for what it captures

**Current burden.** `capture_applied_profile` invites the reader to imagine a
readback of kernel policy state. The [guide](../docs/PolicyWitness.md) must explain
that the receipt captures a userspace compiler object associated with the
application path. Its contents do not establish the kernel's effective policy.

**Possible improvement.** Rename the request and receipt vocabulary around
compiled-profile capture, with `capture_compiled_profile` as a candidate. Record
the capture stage and the separate application result explicitly. Make the
ordinary output understandable without a corrective paragraph about the name.

**Revisit when.** A request/receipt revision can carry a complete migration of
admission, encoders, readers, examples and capture controls. Inventory the capture
paths first so the new name covers their actual timing and ownership. Apply the
[wire contract](../docs/CONTRACT.md); changing accepted input needs its own version
decision, separate from the response change.

**Boundary retained.** Better naming supplies no kernel readback. A compiled
object, a successful apply call and subsequent access observations remain
different evidence.

### P2 — Make independent diagnostics identify their context

**Current burden.** Readers must repeatedly distinguish controller fallback
compilation from worker compilation, a requested interruption from an observed
boundary, and bytes accepted by a pipe from bytes acknowledged by its receiver.
These distinctions appear across the [guide](../docs/PolicyWitness.md),
[architecture account](../docs/ARCHITECTURE.md) and
[extension control fixture](../tests/fixtures/extension_controls/README.md).

**Possible improvement.** Give each diagnostic a clear producer, purpose and
observed stage. Keep fallback compilation in a separately named diagnostic
record. Pair test interventions with independent receipts for the boundary
actually reached. Where a receiver can safely acknowledge a defined event,
record that acknowledgement beside transport write progress.

**Revisit when.** A concrete consumer mistake or missing discriminating control
identifies which record needs improvement. Prototype one channel at a time and
show that the additional observation changes a defensible conclusion. Account
for extra protocol state, publication ordering and failure paths before adding
acknowledgements to the post-sandbox worker.

**Boundary retained.** A fallback result belongs to its own process and context.
A request to interrupt does not establish arrival at the requested point.
Transport acceptance does not establish receiver processing; an acknowledgement
establishes only the event its protocol defines. Do not acquire target resources
before sandbox application merely to make later observations easier.

**Status 2026-10-15.** The third distinction is resolved for the policy pipe.
`runner_c_worker_harness/policy_truncated_prefix` first showed the shipped
worker compiling and applying a 28-byte prefix of a 43-byte submission with no
published failure, indistinguishable from a complete 28-byte submission. Commit
`7ad4c96` (its plan, since removed, recorded the acceptance evidence) gives the
worker the submission's expected byte count through the shared header, has it
publish the count it read at EOF before judging it, and has it refuse any
length that differs before compiling; the reply carries the receipt as
`runner_subprocess.worker_evidence.policy_read` beside the host's write counts.
Host write counts still establish writes accepted by the pipe, and the receipt
establishes only its defined event: the worker reached EOF with the reported
count. The fallback compilation context and the test-seam receipts remain parked.

### P3 — Make build provenance a deliberate artifact

**Current burden.** The [build account](../docs/BUILD.md) relies on build tools'
records to decide whether cached outputs are current. Source identity, selected
paths and signature checks leave questions about the actual compiler, SDK,
effective configuration and inputs behind an artifact.

**Possible improvement.** Emit a bounded provenance record containing actual
tool identities, SDK selection, effective build configuration and relevant source
inputs. Detect reuse of a configured directory under incompatible settings and
define a clean release-build mode. Connect the record to hashes of the produced
artifacts. If certificate class and secure timestamp are intended release
guarantees, verify them on final signed artifacts rather than relying only on
the requested identity, leaf name and runtime flag.

**Revisit when.** A provenance question can be expressed as a field and a check
that would distinguish two materially different builds. Test changed compiler,
SDK and configuration with retained caches, plus missing or inconsistent records.
Keep the recording rules, build guards, embedded evidence and
[signing procedure](../docs/SIGNING.md) aligned. Bound the recorded environment
to avoid collecting unrelated credentials or machine configuration.

**Boundary retained.** The record still trusts the tools reporting or consuming
inputs. It is not proof of reproducibility, compiler correctness, execution of
particular bytes, or exhaustive knowledge of private runtime dependencies.
Closing the six-item plan's build-refusal coverage does not settle these questions.

## Larger improvements

### P4 — Give unfinished cleanup an explicit owner

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

### P5 — Preserve more log identity and timing

**Current burden.** The current denial event in
[sandbox_log.rs](../controller/src/sandbox_log.rs) has PID, process, operation,
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

### P6 — Resume notarization from retained submission evidence

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

### P7 — Clarify admission around host retirement

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

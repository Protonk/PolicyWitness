# Policy transfer acknowledgement plan

Status: complete. Implementation baseline:
`e097c06b008b3482378c27ec600a57e7778026bd`. The plan and its acceptance control
were introduced in `9505f9fc79981d76dd33bcc0b9b46d3ffb23e1c8` and the plan was
revised in `dc7d090fdecad8265ddbf2683cbb10696f17ac4a`. A1, A2 and A3 are
implemented and accepted in the commit that carries this status; the plan is
removed in the commit after it, which also closes the parking lot's P2 status.
The execution record and the deviations from the written instructions are at
the end of this document.

The [parking lot](records/EVIDENCE-CLARITY-PARKING-LOT.md) entry P2 asks, among
other things, that bytes accepted by a pipe be told apart from bytes acknowledged
by the receiver, and that a receiver which can safely acknowledge a defined event
record that acknowledgement beside transport write progress. P2 also sets the
bar for returning to it: a concrete consumer mistake or a missing discriminating
control, prototyped one channel at a time, showing that the added observation
changes a defensible conclusion. The policy pipe meets that bar.

The policy pipe carries no framing. The host writes the SBPL source to the
worker's stdin under one monotonic deadline and records `bytes_written` and
`bytes_expected` only when the transfer fails. The worker reads its stdin to EOF,
compiles whatever arrived, and applies it. It has no expected length to compare
against, so a delivery cut after a complete form is indistinguishable, in every
field the worker publishes, from a complete submission of that shorter policy.
The worker's own NUL guard refuses exactly this outcome for one byte and says
why in its comment: the reply's `policy_sha256` describes the whole submission,
and a prefix of it must not be compiled.

`runner_c_worker_harness/policy_truncated_prefix` establishes the behavior. Its
submission is `(version 1)\n(allow default)\n(deny default)\n`, where each `\n`
denotes one newline byte. It closes the pipe after `(allow default)\n`, delivering
28 of 43 bytes to the shipped worker. The worker sends its ready byte, applies
the prefix with `apply_rc` 0, publishes no failure, runs the
attempt, and exits 0. The `/etc/hosts` open succeeds, where the submitted policy
would have denied it. Three direct runs and dispatcher run
`p2-truncated-prefix-20261014` agree. The harness's `policy_bytes_expected` is the
only field that distinguishes the run from a complete 28-byte submission, and the
production worker has no such field.

In production the host's half of this join is already pinned by
`PolicyTransferTests`: a transfer timeout records a short `bytes_written`, closes
the pipe and enters cleanup. The pipe then delivers EOF to the worker, and the
harness shows what the worker does next. Attempts cannot run, because the host
skips sentinel polling after a transfer failure and never releases a phase. A
worker that reaches apply inside the exit grace still publishes `apply_rc` 0 and
`sandboxed_after_apply` for a policy nobody submitted. The live stall is a
scheduling race and is not reproduced; this plan argues the join from its two
pinned halves and adds a deterministic control that joins them. The harness
releases the attempt; the production host does not after transfer failure. The
verified defect concerns worker input integrity and application evidence, not
production attempts executing under the truncated policy.

This plan gives the worker the expected length, makes it refuse a delivery of any
other length before compiling, and publishes the count it received beside the
host's write progress. The other two distinctions in P2, fallback compilation
context and test-seam receipts, remain parked.

## Checkpoint and order

| Item | Claim to retire or narrow | Status | Completion evidence |
| --- | --- | --- | --- |
| A1 | The worker compiles and applies whatever the policy pipe delivered before EOF | Done | Worker identity `ad6bd925c33aa26d17b3b26efd40ff6a428333de36d06f8ced40e8ee69e125a5`; response schema 21 unchanged. `runner_c_worker_harness` in run `p2-a12-targeted-20261015`: `policy_truncated_prefix` passes with code 13, detail 28, exit 11 and the 28-byte receipt; `policy_overflow_refused` keeps exit 7/code 2 and `policy_nul_refused` exit 9/code 9; the nine new delivery cases pass. Layout golden candidate reviewed (three rows added, none moved) and replaced. |
| A2 | No general pre-compile EOF receipt joins worker reads to host write progress | Done | `runner_unit` run `p2-a12-unit2-20261015`: 436/436 Swift cases including the joined `PolicyTransferTests` control (host timeout 28 of 43 written, receipt 28 of 43, operation 2 code 13 detail 28, exit 11 reaped during grace, no termination request, `runner_failed`) with its rejected fabricated-kill, fabricated-exit and receipt variants; Rust replay of the retained `policy-transfer-refused.json` through assembly, the lifecycle oracle and the consumer with its rejected variants. Shape golden candidate reviewed (the `policy_read` object and its two members) and replaced. |
| A3 | The integrated change still needs final acceptance and evidence review | Done | Signed build of the final increment (identity above). Default battery run `20261015T183151Z_bc3b36df` in `tests/out/runs/p2-a3-battery2-20261015`: 187 pass, 0 fail, 0 skip, artifact inspection clean. `source_drift` passes inside that battery; offline `check.py`, generator `--check`s, prose baseline and link checks pass. Opt-in `witness_contract/order_barrier_mutations`: run `p2-a3-order-barrier-20261015` (`20261015T184234Z_f9f09349`): baseline accepted, both bypasses rejected by the component gate and by independent CLI effects. `cargo test --manifest-path controller/Cargo.toml`: every binary passes (policy-witness 235 and 1, sandbox-log-observer 27, sbpl-check 56, cli_contract 15; the two ignored cases are the receipt-dependent replay, which `runner_unit` runs, and the observer's archive case, which its required archive case selects). |

Implement A1 and A2 as one coherent increment, including the affected readers,
fixtures, contracts, generated documentation and coverage. Regenerate the worker
identity after the implementation edits. The documentation checklist below
belongs to that increment; A3 verifies the result and closes the plan. Do not
leave a partially migrated header, reply or account for a later item to finish.

During execution, update this checkpoint with implementation commits, the worker
identity and response version after each increment, test run identifiers, the
reviewed golden candidates, remaining findings and the next action. The plan
closes when all three gates pass or the user explicitly accepts a documented
change of scope. The parking lot's P2 entry is updated when the plan closes.

## Shared implementation requirements

- Preserve one fresh host and worker per specimen, the host/worker sandbox
  boundary, collection closure before release, and the limited meaning of
  `query_first`. Nothing here touches the wait, the release store or query
  eligibility, so `witness_contract/order_barrier_mutations` is not forced; run
  it anyway in A3, because the worker binary and the shared header change.
- Follow the [wire contract](docs/CONTRACT.md). The decisions recorded below
  classify every change as additive; confirm each before editing and record a
  bump if a reading rule turns out to change. Historical runs keep their bytes.
- The shared header, the C worker, the Swift driver and the API types are
  identity inputs. Regenerate with `python3 docs/generate_worker_identity.py`
  after the last edit of an increment, never by hand. The layout golden produces
  a candidate; review it and replace the golden as the acknowledgement.
- Every producer of the shared header writes the new expectation before
  publishing `prepared` and before spawning the worker: the host in
  [CWorker.swift](runner/Sources/PWRunnerCore/CWorker.swift), the C harness in
  [harness.c](tests/suites/runner_c_worker_harness/harness.c), and any Swift
  unit test that constructs a region for the real worker. The lifecycle fixture
  worker in [worker.c](tests/fixtures/worker_lifecycle/worker.c) reads the header
  and must keep ignoring fields it does not use.
- Do not acquire anything before apply to ease observation, and do not add
  worker I/O after apply. The acknowledgement is a pre-apply read result stored
  into existing fixed memory with release ordering.
- Follow [test guidance](tests/AGENTS.md): fresh output directories, evidence
  provenance, no skips for missing equipment, and controls that establish the
  boundary they claim rather than a plausible string.

## A1 — Refuse a delivery whose length differs from the submission

**Current claim.** `read_all_from_fd` in the
[C worker](controller/tools/pw_probe_runner/pw_probe_runner.c) returns the byte
count at EOF and the worker proceeds to compile it. The only guards are the
fixed-buffer capacity (code 2) and the embedded-NUL scan (code 9). The header in
[pw_probe_runner_abi.h](controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
carries counts, partitions and a nonce as host inputs, but no policy length.

**Change.** Add a `uint32_t` host input `policy_bytes_expected` to
`pw_shm_header_t`, carved from the `reserved[56]` bytes at offset 136 so that no
existing offset moves and the header stays 448 bytes. The host constructs the
submission's UTF-8 byte array
once before header population and uses its count for both this input and the
existing transfer records; that same array supplies the writes. The expectation
remains immutable for the worker's lifetime. After acquiring `prepared`, the
worker snapshots the expectation for validation and comparison. Mirror the
offset in `PWShmLayout`, print it in the layout harvest
[printer.c](tests/suites/runner_abi_layout/printer.c), and keep the remaining
reserved bytes declared.

In the worker, after the existing header checks and before the read: refuse an
expectation larger than `PW_SHM_POLICY_BYTES - 1` as invalid host input, with a
new failure code on operation 1 and its own exit code, so an impossible length
is refused before any policy byte is consumed. The buffer's final byte is
reserved for the terminating NUL. Preserve the existing read-error and overflow
branches for negative returns from `read_all_from_fd`. Only a nonnegative return
establishes EOF and supplies a count: publish the A2 receipt, compare the count
with the expectation, and refuse any difference with a new failure code on
operation 2, detail the received count, and a distinct exit code. The length
check precedes the NUL scan and any sandbox parameter, compile or apply call.
Read overflow retains code 2 because it stops before EOF; it is not a length
mismatch. Define this order in the worker's step comment and the contract's code
list.

Zero is a valid expectation when the host admitted an empty source; the worker
compares, it does not treat zero as unset. Exit codes 2, 3, 4, 5, 6, 7, 8 and 9 are
taken; choose two unused codes and document them beside the others.

The harness prepares the full submission and its expectation before spawn,
including for scenarios that deliver only a prefix. Deliberate malformed-input
controls override the expectation explicitly. In particular, `policy_overflow`
pins it at `PW_SHM_POLICY_BYTES - 1` so read overflow remains reachable and keeps
code 2; an out-of-range expectation with a small valid policy reaches the new
header refusal. Overdelivery within the buffer is a required control for the
other direction of the comparison, even though the production writer does not
send more than its submitted byte array.

**Acceptance gate.** `runner_c_worker_harness/policy_truncated_prefix` passes
with its existing assertions, which require a published operation-2 failure, no
ready byte, no application, no completion, no attempt, and a nonzero exit code;
tighten them to the chosen code and detail 28 once those are fixed. The
`policy_overflow_refused` and `policy_nul_refused` cases keep exit 7 with code 2
and exit 9 with code 9. Required boundary controls also establish:

- A complete delivery of the same 43-byte submission applies successfully and
  denies the `/etc/hosts` open. This pins the contrast with the truncated prefix
  using the exact submitted policy, alongside the existing allow/deny controls.
- A zero expectation with empty EOF passes the length check and reaches ordinary
  compilation handling; this does not require an empty policy to compile.
  Empty EOF with a nonzero expectation and nonempty input with a zero
  expectation both produce the length refusal.
- A valid source containing multibyte UTF-8 is counted in bytes, reaches EOF
  with equal counts and compiles/applies normally.
- A valid source padded to exactly `PW_SHM_POLICY_BYTES - 1` bytes is accepted
  after EOF. An extra byte reaches the existing overflow refusal when the
  expectation remains at capacity.
- An expectation of `PW_SHM_POLICY_BYTES` refuses before reading, with the new
  header-failure code and no EOF receipt. Overdelivery that remains within
  capacity produces the operation-2 length refusal with the actual count.

Every existing harness, unit and live case retains its expected behavior after
its producer supplies the expectation. The layout golden candidate adds the new
offsets and moves none; replace it after review. `runner_abi_layout` compares the
compiled C values with the Swift mirror.

**Retirement.** The worker's step comment and the NUL guard's comment describe
one rule for both guards: a prefix of the source `policy_sha256` describes is
never compiled. The harness README's item for the truncated prefix states the
achieved refusal.

## A2 — Publish what the worker read beside what the host wrote

**Current claim.** `runner_subprocess.policy_transfer_error` and
`policy_transfer_timeout` carry the host's `bytes_written` and `bytes_expected`,
and only on failure. The
[guide](docs/PolicyWitness.md) says written bytes do not prove child receipt; the
[failure evidence contract](tests/FAILURE-PROPAGATION-CONTRACT.md) says the counts
are not evidence of bytes consumed by the worker; the
[architecture account](docs/ARCHITECTURE.md) says counts describe writes accepted
by the pipe. All three are true and none can be replaced by a field.
The opt-in compiled-object capture already records consumed source length and
digest after compilation, but it neither guards compilation nor provides a
general pre-compile EOF receipt.

**Change.** Add `uint32_t policy_bytes_received` and
`_Atomic uint32_t policy_read_published`, also carved from the reserved header
bytes. The host zeroes both before spawn. Only when `read_all_from_fd` returns
`plen >= 0` does the worker store that EOF count and release-store the flag to 1,
before the length comparison and NUL scan. The payload is immutable after
publication. Header refusal, read error and overflow publish no EOF receipt;
their existing or A1 failure records remain independent. The helper's `-1` and
`-2` returns are status sentinels, never byte counts. Counting partial reads on
non-EOF paths would require a richer result and is outside this change.

After validating the worker identity, the host exposes the receipt only if its
final snapshot acquires `policy_read_published == 1`. It reports an optional
`runner_subprocess.worker_evidence.policy_read` object with `bytes_expected`
(the immutable host input specifying the required length) and `bytes_received`
(the worker's EOF count). Zero or an invalid publication flag must not expose payload
bytes. Absence means no valid publication was observed in that snapshot, not
that the worker never read or published. If cleanup failed, the worker may
publish after collection; historical records and fixture workers may also lack
the field. Absence establishes nothing about delivery.

The host's `bytes_expected` remains on the transfer-failure records. When both
records exist, their expectations must agree; a disagreement is a detectable
fault, never something either side corrects. Both members of a present
`policy_read` object are required nonnegative integers bounded by
`PW_SHM_POLICY_BYTES - 1`. The Swift reply checks and independent semantic
readers must enforce these rules, rather than relying only on the shape golden.
When the length-refusal record and receipt are both present, the counts must
differ and the refusal's detail must equal `bytes_received`. Unequal counts alone
do not establish refusal: termination can interrupt the worker between receipt
publication and the comparison or failure publication. Preserve that partial
account without inventing a failure or exit.

Keep existing summary precedence: an observed worker failure takes precedence
over `runner_timeout`. If the worker publishes the A1 refusal after a transfer
timeout and the host observes it, the summary is `runner_failed`; otherwise a
transfer timeout remains `runner_timeout` under the existing rule. In either
case retain `policy_transfer_timeout`, stop reason `policy_transfer_deadline`
and cleanup trigger `policy_transfer_timeout`. A timeout does not guarantee the
worker reaches EOF, publishes a refusal or exits during grace. The disposition
record and Rust projection must use the actual wait and termination observations,
including a kill before publication or an unconfirmed reap.

Thread the existing `PolicyTransferCalls` in
[MonotonicDeadline.swift](runner/Sources/PWRunnerCore/MonotonicDeadline.swift)
through the driver beside `ChildProcessCalls`, so tests can control writes and
the transfer clock/poll boundary without adding a second injection abstraction.
Use the same supplied clock for the deadline and writer. Production defaults
retain the real native calls; no specimen-facing override is added.

**Acceptance gate.** A `PolicyTransferTests` control drives the shipped worker
from `PW_APP_DIR`. Its injected writer uses native writes to deliver exactly the
first 28 bytes of the 43-byte submission, accounting for actual write results,
then returns `-1` with `errno = EAGAIN` until a short transfer deadline expires.
Returning zero is unsuitable: `writePolicy` treats it as an immediate host
diagnostic, not a timeout. Keep the exit grace independently generous so the
real worker can observe EOF and publish its refusal; do not make a scheduling
race the control's success condition. The control establishes the joined
failure-handling path, not a naturally occurring stall of a small policy write.

The encoded reply must carry the host timeout with 28 written and 43 expected,
the worker receipt with 28 received and 43 expected, the operation-2 A1 failure
with detail 28, no application, no worker readiness publication and no attempt.
The host's `ready_byte_received == false` alone is insufficient because it skips
that wait on transfer failure. Require the observed refusal exit, confirmed reap
during grace, no termination request and `runner_failed`, with the timeout and
cleanup trigger retained. Replay this actual reply through the lifecycle oracle,
Rust disposition tests and Python consumer, including rejected variants with a
fabricated kill or exit.

Retain separate controls for timeout/kill before any receipt, and failed cleanup
with unconfirmed reaping; the existing stalled lifecycle fixture supplies host
handling evidence, not a real-worker EOF observation. Add publication-gate
controls for nonzero payload under a zero or invalid flag, valid zero-byte EOF,
and a published receipt without later refusal/application evidence. Read-error
and overflow controls must retain their failure and expose no EOF receipt;
length and NUL refusals after EOF must retain the receipt.

The field-complete reply fixture records the new object so `response_shape.json`
admits it; the maximal reply size test receives a size policy for each new key.
Add semantic-reader controls for missing members, negative or out-of-range
counts, conflicting host/worker expectations and inconsistent length-refusal
details, alongside valid partial observations. The golden permits missing keys
and only checks types, so golden agreement alone is insufficient. Complete
deliveries in the existing live suites report equal counts. Historical and
capture fixtures without the optional object remain valid.

**Retirement.** Retain the three distinctions about host write progress and add
the receipt's reading rule: equal counts in a valid EOF receipt establish length
agreement with the submission, not content identity, compilation, application
or kernel effect. A short count accompanied by the A1 refusal establishes that
the worker refused. Without the refusal record, the receipt establishes only
the completed read.

## Documentation included with A1 and A2

Update together, through the owning generators where a region is generated:
the failure evidence contract's code list and policy-transfer section, and any
affected wire-contract reading rules; the guide's `runner_subprocess` field list
and transfer paragraph; the architecture
prose at the transfer paragraph plus [architecture.json](docs/architecture.json)
edge T5's note and guard B3's label, citing the harness case as a check, then
`python3 docs/generate_architecture.py`; [limits.json](docs/limits.json) entry
`worker_policy_transfer`'s effect and behavior, then
`python3 docs/generate_limits.py`; the authored premise in `docs/LIMITS.md` that
names the NUL guard beside the shared-memory string slots; the `runner_failed`
and `runner_timeout` rows of [COVERAGE.md](tests/COVERAGE.md); the lifecycle
account in [runner/README.md](runner/README.md); the harness README; and the
test catalog and affected suite descriptions. The parking lot's P2 status note
changes on closure, after A3 passes. Do not state a new value or count in scanned
prose outside a span, so the prose baseline does not grow. Describe the EOF-only
receipt, absence and conditional timeout precedence consistently; preserve the
distinction between accepted writes and acknowledged reads.

## A3 — Verify the integrated change and close the plan

**Current claim.** A1 and A2 require integrated acceptance against the signed
build; structural checks alone do not establish behavior.

**Change.** Review the implementation, readers, fixtures and documentation as one
account. Resolve any remaining inconsistencies before crediting acceptance; A3
does not defer documentation or protocol migration from the implementation.

**Acceptance gate.** Against a signed build of the final increment: the default
battery in a fresh output directory; `source_drift` including the generator
checks; the opt-in `witness_contract/order_barrier_mutations`; `cargo test` for
the controller. Record run identifiers, the reviewed layout and shape goldens,
and the worker identity in the checkpoint table.

**Retirement.** Update the parking lot's P2 status with the completed policy-pipe
work and its evidence, leaving its other topics parked. Host write counts alone
still do not establish receipt. The new acknowledgement establishes only its
defined event: the worker reached EOF with the reported byte count.

## Decisions recorded before editing

- **Version effect.** Request schema unchanged. Response schema: additive only,
  one optional object under `worker_evidence` and two new failure codes in an
  open vocabulary whose unknown values readers already transport unchanged. No
  bump. Controller envelope unchanged. The worker identity regenerates.
- **Layout.** New fields come from the header's reserved bytes; no existing
  offset moves and the header size is unchanged. The layout golden grows by the
  new rows.
- **Why a length and not a digest.** This change addresses premature EOF after
  a prefix was delivered. The existing pipe preserves byte order, and a length
  comparison suffices to reject that truncation with little protocol state.
  Read/write errors remain separate observations. The worker already uses
  CommonCrypto to hash consumed source in
  [pw_profile_capture.h](controller/tools/pw_probe_runner/pw_profile_capture.h),
  so dependency avoidance is not a reason to decline hashing. Length agreement
  cannot detect a different buffer of the same length or prove content identity.
  A stronger content-identity contract would justify revisiting a digest; it is
  outside this fix. The reply's `policy_sha256` still describes the submission.
- **Why the header and not framing the pipe.** The header is already the
  host-to-worker input channel with identity and bounds checks, and the harness
  and the fixtures already populate it. A length prefix on the pipe would change
  the transfer deadline's accounting and every producer of policy bytes.
- **Precedence.** An observed worker refusal after a transfer timeout classifies
  as `runner_failed` by the existing rule; the timeout record is retained.
  Without an observed failure the timeout remains `runner_timeout`. Neither
  classification supplies missing publication, kill or exit evidence.

## Out of scope

The fallback compilation context and the test-seam receipts in P2 stay parked.
A live reproduction of the stall that makes the host time out is not attempted.
Framing, content hashing and partial-read counts without EOF are outside this
change. Cleanup ownership after a transfer timeout is P4; retaining independent
cleanup observations in the new controls does not resolve that ownership work.

## Execution record

Choices the plan left open, as implemented:

- Failure codes 12 (`PW_FAILURE_LENGTH_EXPECTATION`, header operation 1,
  detail the refused expectation) and 13 (`PW_FAILURE_SOURCE_LENGTH`, operation
  2, detail the received count); exit codes 10 and 11. Header fields
  `policy_bytes_expected` at offset 136, `policy_bytes_received` at 140 and
  `policy_read_published` at 144; `reserved` shrinks from 56 to 44 bytes;
  `phases` stays at 192 and the header at 448 bytes, pinned by a new static
  assert.
- The reply object is `runner_subprocess.worker_evidence.policy_read` with
  `bytes_expected` and `bytes_received`, decoded behind the validated identity
  and the acquired flag, and omitted for a count outside the source capacity.
- The driver gained a `transferCalls` parameter beside `processCalls`; the
  deadline and the writer share its clock. The joined control injects the
  writer (native writes for the first 28 bytes, then EAGAIN) and the poll
  (sleeping for its allowance), with a short transfer deadline and a generous
  exit grace.
- Nine harness controls beyond the truncated prefix: whole submission, UTF-8
  byte counting, exactly at capacity, capacity plus one with the pinned
  expectation, out-of-range expectation, overdelivery, empty source with a zero
  expectation, empty EOF against a nonzero expectation, nonempty input against
  a zero expectation. Compilation refuses the empty source ("no version
  specified"), as the plan allowed.
- The three qualifications about host write counts are retained and extended
  with the receipt's reading rule in the failure evidence contract, the guide
  and the architecture account; the architecture and limits manifests cite the
  harness case as a check; coverage rows, the runner README, the harness and
  unit suite READMEs, the catalog and the LIMITS premise are updated. The
  prose baseline did not grow.

Deviations from the written instructions, each material enough to record:

- **Capacity bound in the Swift reply rules.** `PWRunnerAPI.swift` is also
  compiled into the runner client without the layout mirror, so the rule cannot
  name `PWShmLayout.policyBytes`. The bound is the mirrored constant
  `policyReceiptCapacityBytes`, which `PolicyTransferTests` pins to
  `PWShmLayout.policyBytes - 1`. The decoder enforces the receipt rules as well
  as the encoder.
- **Attempt kind in the joined control.** The retained reply is assembled with
  the production step builder, which does not attach the host path diagnostics
  that full orchestration adds to file attempts, so the independent consumer
  rejects a file step built that way. The control uses a sysctl attempt; it
  still establishes that no attempt ran and that the reply carries the step as
  a synthetic, unreached result.
- **Where the consumer's refusal-detail control lives.** The blackbox checker
  controls run against a retained envelope that carries no receipt, so they
  construct one for the member, range, partial and conflicting-expectation
  controls. The inconsistent-refusal-detail control and the second
  conflicting-expectation control replay the actual refused reply inside the
  controller's transfer replay test instead.
- **Harness envelope.** `result.json` gained `header_bytes_expected`,
  `policy_read_published` and, behind the flag, `policy_bytes_received`, beyond
  the two counts the plan named, and the controlled-equipment transcript in
  `tests/fixtures/worker_harness/control.py` carries them too.
- **Maximal reply size.** The receipt adds no string key, so no size policy was
  needed; the synthesized maximum grew by 64 bytes and `runner_reply_maximum`
  in `docs/limits.json` records 52,419,188. The client budget is unchanged by
  its 4 MiB rounding.
- **Acceptance equipment the plan did not list.** The first battery
  (`p2-a3-battery-20261015`, 185 of 187) failed `shell_helpers/worker_setup`,
  whose canned happy transcript lacked the new keys, and
  `blackbox_e2e/checker_controls`, which assumed its retained baseline carried
  a receipt. Both are test equipment; the fixes are recorded above and the
  whole battery was rerun.
- **Rust test flake.** In one full `cargo test` run,
  `log_capture::tests::both_raw_streams_are_bounded_at_exact_edges` in the
  `sandbox-log-observer` binary failed with a `pipe_open_after_exit` cutoff at
  the exact 64-byte edge. `controller/src/log_capture.rs` is untouched by this
  work and the test passes on rerun; recorded, not attributed to this change.

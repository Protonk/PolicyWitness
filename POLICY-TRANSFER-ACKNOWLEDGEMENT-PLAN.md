# Policy transfer acknowledgement plan

Status: proposed. Prepared 2026-10-14 against `e097c06b008b3482378c27ec600a57e7778026bd`, the commit that
adds this plan and its acceptance control. Nothing in this plan is implemented;
the control fails by design until item A1 lands.

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

`runner_c_worker_harness/policy_truncated_prefix` establishes the behavior. It
pipes `(version 1)(allow default)(deny default)` to the shipped worker but closes
the pipe after `(allow default)`, delivering 28 of 43 bytes. The worker sends its
ready byte, applies the prefix with `apply_rc` 0, publishes no failure, runs the
attempt, and exits 0. The `/etc/hosts` read succeeds, where the submitted policy
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
pinned halves and adds a deterministic control that joins them.

This plan gives the worker the expected length, makes it refuse a delivery of any
other length before compiling, and publishes the count it received beside the
host's write progress. The other two distinctions in P2, fallback compilation
context and test-seam receipts, remain parked.

## Checkpoint and order

| Item | Claim to retire or narrow | Status | Completion evidence |
| --- | --- | --- | --- |
| A1 | The worker compiles and applies whatever the policy pipe delivered before EOF | Open | |
| A2 | Written bytes do not prove child receipt; no record says what the worker read | Open | |
| A3 | Guide, contracts, manifests and coverage still state the pre-A1 limits | Open | |

Implement A1 and A2 together if the host/worker identity would otherwise
regenerate twice; each committed increment must still have matching producers,
readers, fixtures and documentation. A3 follows once the acceptance battery
passes against a signed build of A2. Do not leave a partially migrated header or
reply for a later item to finish.

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
- Every producer of the shared header writes the new expectation: the host in
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

**Change.** Add a host input `policy_bytes_expected` to `pw_shm_header_t`, carved
from the `reserved[56]` bytes at offset 136 so that no existing offset moves and
the header stays 448 bytes. The host writes the submission's UTF-8 byte count
there during header population, before spawn; it already knows the value it later
reports as `bytes_expected`. Mirror the offset in `PWShmLayout`, print it in the
layout harvest [printer.c](tests/suites/runner_abi_layout/printer.c), and keep
the remaining reserved bytes declared.

In the worker, after the existing header checks and before the read: refuse an
expectation larger than the source capacity as invalid host input, with a new
failure code and its own exit code, so a host that claims a policy the buffer
cannot hold is refused before any byte is consumed. After the read returns:
compare the count with the expectation and refuse any difference with a new
failure code on operation 2, detail the received count, and a distinct exit code,
before the NUL scan and before any libsandbox call. The capacity path (code 2)
stays first, because an oversized delivery overflows before EOF is seen. Define
the order in the worker's step comment and in the contract's code list.

Zero is a valid expectation when the host admitted an empty source; the worker
compares, it does not treat zero as unset. Exit codes 2, 4, 5, 6, 7, 8 and 9 are
taken; choose two unused codes and document them beside the others.

The harness writes the expectation for every scenario from the submission it
pipes. The `policy_overflow` scenario pins its expectation at the capacity so the
read-overflow path stays reachable and keeps code 2; a new scenario sends an
out-of-range expectation with a small valid policy to reach the new header
refusal. A further scenario may deliver more bytes than expected to show the
comparison is symmetric; production cannot produce it, so it is optional.

**Acceptance gate.** `runner_c_worker_harness/policy_truncated_prefix` passes
with its existing assertions, which require a published operation-2 failure, no
ready byte, no application, no completion, no attempt, and a nonzero exit code;
tighten them to the chosen code and detail 28 once those are fixed. The
`policy_overflow_refused` and `policy_nul_refused` cases keep exit 7 with code 2
and exit 9 with code 9. The new out-of-range case refuses before the read with
its own code. Every other harness, unit and live case passes unchanged against a
signed build, since every complete delivery now matches its expectation. The
layout golden candidate adds the new offsets and moves none; replace it after
review. `runner_abi_layout` compares the compiled C values with the Swift mirror.

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

**Change.** The worker publishes `policy_bytes_received` and a release-ordered
`policy_read_published` flag, also carved from the reserved header bytes,
immediately after the read returns and before any comparison, so the count is the
raw EOF count on every path that reaches the read, including the refusals of A1.
The host decodes them in its final snapshot only on an acquire of the flag and
reports them under `runner_subprocess.worker_evidence` as an optional object,
`policy_read` with `bytes_expected` and `bytes_received`, present exactly when the
worker published. Absence means the worker never published a read result; it
establishes nothing about delivery. The host's own `bytes_expected` stays where
it is on the failure records; the two values agree by construction and a
disagreement is a reader-detectable fault, not something either side corrects.

Decide and record the classification of the joined case before editing. Today a
published worker failure takes summary precedence over `runner_timeout`, and the
contract's policy-transfer section says so. After A1 a live transfer timeout is
followed by the worker's length refusal, so the summary becomes `runner_failed`
with `policy_transfer_timeout` retained beside the failure record, the stop
reason `policy_transfer_deadline` and cleanup trigger `policy_transfer_timeout`
unchanged, and the worker reaped during grace by its own exit rather than a kill.
Keep that precedence unless review finds a reason to special-case it, and make
the disposition record and the Rust projection state only what those facts
support.

Add a transfer-write injection point to the driver beside the existing
process-call injection, used only by tests; production keeps the real write.

**Acceptance gate.** A `PolicyTransferTests` control drives the shipped worker
from `PW_APP_DIR` with an injected write that delivers exactly the first 28 bytes
of the 43-byte submission and then reports no progress until a short deadline
expires. The reply must carry `policy_transfer_timeout` with those two counts,
the worker's `policy_read` with the same two counts, the operation-2 failure with
the A1 code and detail 28, no application, no readiness, and the recorded
precedence. The lifecycle oracle and the Rust disposition tests accept the joined
account and reject a fabricated kill or exit. The field-complete reply fixture
records the new object so `response_shape.json` admits it; the maximal reply size
test receives a size policy for each new key; `tests/lib/consumer.py` validates
it through the golden. Complete deliveries in the existing live suites report
equal counts. Existing capture fixtures remain valid without the optional object.

**Retirement.** The three sentences quoted above are replaced by the field and
its reading rule: equal counts establish that the worker read the submission to
EOF intact in length, and nothing more. A short count with the A1 refusal
establishes that the worker refused; compile, application and kernel effect
remain the separate observations they are today.

## A3 — Retire the qualifications and run the acceptance battery

**Current claim.** The documents and manifests describe the pre-A1 behavior.

**Change.** Update together, through the owning generators where a region is
generated: the contract's failure code list and policy-transfer section; the
guide's `runner_subprocess` field list and transfer paragraph; the architecture
prose at the transfer paragraph plus [architecture.json](docs/architecture.json)
edge T5's note and guard B3's label, citing the harness case as a check, then
`python3 docs/generate_architecture.py`; [limits.json](docs/limits.json) entry
`worker_policy_transfer`'s effect and behavior, then
`python3 docs/generate_limits.py`; the authored premise in `docs/LIMITS.md` that
names the NUL guard beside the shared-memory string slots; the `runner_failed`
and `runner_timeout` rows of [COVERAGE.md](tests/COVERAGE.md); the lifecycle
account in [runner/README.md](runner/README.md); the harness README; and the
parking lot's P2 status note. Do not state a new value or count in scanned prose
outside a span, so the prose baseline does not grow.

**Acceptance gate.** Against a signed build of the final increment: the default
battery in a fresh output directory; `source_drift` including the generator
checks; the opt-in `witness_contract/order_barrier_mutations`; `cargo test` for
the controller. Record run identifiers, the reviewed layout and shape goldens,
and the worker identity in the checkpoint table.

**Retirement.** The qualification that the policy pipe's counts say nothing about
the worker is gone. What remains is the boundary P2 states: an acknowledgement
establishes only the event its protocol defines, here the byte count at EOF.

## Decisions recorded before editing

- **Version effect.** Request schema unchanged. Response schema: additive only,
  one optional object under `worker_evidence` and two new failure codes in an
  open vocabulary whose unknown values readers already transport unchanged. No
  bump. Controller envelope unchanged. The worker identity regenerates.
- **Layout.** New fields come from the header's reserved bytes; no existing
  offset moves and the header size is unchanged. The layout golden grows by the
  new rows.
- **Why a length and not a digest.** EOF truncation is the only failure this
  transport can produce; a pipe does not corrupt or reorder. A length is the
  smallest defined event the worker can acknowledge, needs no new dependency in
  the pre-apply worker, and the host already computes the value. A digest would
  add CommonCrypto to the worker for no additional transport failure mode; the
  reply's `policy_sha256` continues to describe the submission.
- **Why the header and not framing the pipe.** The header is already the
  host-to-worker input channel with identity and bounds checks, and the harness
  and the fixtures already populate it. A length prefix on the pipe would change
  the transfer deadline's accounting and every producer of policy bytes.
- **Precedence.** A worker refusal after a transfer timeout classifies as
  `runner_failed` by the existing rule; the timeout record is retained. Revisit
  only if review shows a reader is misled.

## Out of scope

The fallback compilation context and the test-seam receipts in P2 stay parked.
A live reproduction of the stall that makes the host time out is not attempted.
Framing or hashing the policy pipe is declined above. Cleanup ownership after a
transfer timeout is P4.

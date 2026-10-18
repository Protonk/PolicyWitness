# Worker lifecycle fixture

`build.sh <output binary>` builds an ABI-compatible test child outside the app.
`runner_unit` supplies its path to Swift tests as `PW_LIFECYCLE_WORKER_FIXTURE`.
Missing equipment fails the required tests. The fixture does not compile or
apply a sandbox and is not evidence of production failure attribution.

Its stdin text selects completed-report exit 0, exit 17, self-SIGTERM, an ignored
exit request, a published status-word failure that ignores exit, or no publication.
It publishes through the ABI's release/acquire protocol. Completed exit/signal
scenarios wait for the host's exit-request flag, proving that the host observed
the report before the abnormal disposition. The hang cases require cleanup by
the host or the owning test. Swift tests use real spawn/mapping/polling/cleanup;
internal OS-call controls inject only otherwise unreliable kill/wait failures.
They independently clean up their child after a simulated unconfirmed reap.

`reap_ack_clean|<gate>` and `reap_ack_signal|<gate>` publish arrival, then wait
for both host release and a test-owned file gate. The host wait control opens
that gate only after its last acknowledgement/done samples, then observes an
actual native reap before returning to the driver. The first mode completes
its slot and phase, publishes `done` and exits 0; the second acknowledges then
dies by SIGTERM without completing or publishing `done`. Both establish ordering
only through the final confirmed-reap reconciliation. A third control returns
poll EIO before opening the gate in cleanup, so acknowledgement and clean reap
cannot restore broken ownership. The fixture's alarm and the test's bounded
native wait independently fail stalled equipment; the owning test verifies
ECHILD after driver reap and cleans up on failure. Constructed query records
exercise the real comparison builder without claiming native sandbox evidence.

`exec_payload_valid` publishes a constructed complete exec account.
`exec_payload_unpublished` fills the same account and output, then self-kills
before the slot completion store. The host must withhold both new and old
payload fields. `exec_payload_bad_marker` and `exec_payload_bad_enum` publish
malformed present metadata; the ordinary reply must degrade and withhold
comparisons. These modes use a fictional child PID to test ABI interpretation;
production native-call and live-exec controls establish actual observations.

The ready byte is sent after fixture publication for deterministic controls;
real-worker readiness and deadline/grace behavior remain separate tests.

The worker evidence scenarios also publish unfamiliar/zero failure records, late slots,
started-but-unpublished slots, and rich/missing/empty/truncated diagnostics.
`skip_publication` takes a two-step plan and deliberately violates the
completion-before-return rule through the real publication primitives: slot 0
completes with returned progress, slot 1 publishes started and returned progress
without completing, then done; it exits 0 on the exit request. It produces the
D5 publication conflict for the disposition record (plan test C5) and claims no
production reachability.
`diagnostic_after_apply` applies a real deny-default profile before memory-only
publication. `close_report`, `close_absent` and `close_hang_report` read a command
prefix then close stdin; the last has a test-only watchdog and independently
owned host cleanup. They exercise transfer independently of source admission.

The builder emits companion executables alongside its output: `.apply-failure`,
`.params-CREATE`, `.params-SET`, `.map-failure` and `.read-failure`. They compile
production C main with one native boundary substituted or close a descriptor
before entry. The read-failure companion closes stdin: the actual read reports
EBADF, and the worker must retain that failure without publishing an EOF receipt.
Assignment fails on the second call and sets a stale errno to prove it is not
claimed. These are deterministic producer/driver controls, not policy results.

The `.validator` companion flushes an actual valid NDJSON record before clean,
nonzero, signaled or hanging termination. It also provides delayed multibyte
writes and closed-input/invalid-UTF-8 controls. It makes no sandbox calls. Driver
tests select its operation token, control only kill/wait boundaries when needed,
and independently reap any fixture child the driver could not confirm. Its alarm
bounds failures in the test equipment itself.

The validator companion echoes the submitted query. Its closed-input control
closes stdin before emitting over 32 KiB of valid JSON whitespace plus a verdict
and invalid UTF-8 tail, requiring multiple reads after input failure.
`io_hang_late:<uuid>` keeps stdout open until the I/O deadline and failed
cleanup return. The test then creates `/tmp/pw-order-late-<uuid>`; the child attempts another
write and appends its native rc/errno there, proving the collection pipe closed
before that late output. The test owns eventual termination and reaping.

`transport_*` and `close_transport_beta` modes use the separate
[diagnostic transport inputs](../diagnostic_transport/README.md). They publish
controlled unfamiliar records using the supported protocol, retain independent
exit/EPIPE evidence, and provide absent/unpublished/invalid/version/text controls.

Ordering tokens: `proceed_wait` waits for release, acknowledges, then publishes
slots; `proceed_expire:<ms>` expires without acknowledgement or attempts;
`signal_awaiting_proceed` dies before acknowledgement; `ignore_proceed` ignores
release; `signal_after_ack` dies after acknowledgement but before attempts.
`proceed_ack_gate` also requires `<receipt>.ackgate` before acknowledging.
The ownership-loss control returns EIO from polling, then opens this gate in
the subsequent cleanup wait and returns ECHILD after observing the receipt.
This forces a raw acknowledgement after the driver has broken ownership.
An optional `|/tmp/receipt` suffix records waiting/ack/attempt/expiry for the
test-owned collection gate. For the pre-ack signal token, `<receipt>.die` gates
the signal. These unsandboxed fixtures test protocol interpretation, not native
policy enforcement. `.identity-mismatch` refuses a header whose last identity byte differs.

The clock companions compile the production C main from
[clock_failure.c](clock_failure.c) with one continuous-clock boundary
substituted; every seam leaves a stale `EPERM`. `.clock-setup-failure`,
`.clock-zero-factor` and `.clock-unrepresentable` change only the timebase
query and refuse clock setup before the policy read. `.clock-failure` and
`.clock-failure-later` return a value below the origin at the first proceed
start or observation sample. `.clock-phase2` does so at phase 2's own start;
`.clock-expire2` jumps 2^62 ticks forward at its first observation, a valid
expiry. Both wait for explicit collection authorization as described below.
`.clock-sticky` rejects the first exec observation sample.
`.clock-arith` selects a 1/150000000 timebase and jumps the first exec
observation to one millisecond before the default plan cutoff, so the child
deadline overflows while the sample is valid. Jumps persist, keeping later
samples ordered. These establish publication and interpretation of timing
refusals, not native clock behavior.

The two gated companions derive `<executable>.gate` from their executable path
before entering production main. The Swift test creates that directory fresh;
an existing directory is refused. At the selected phase-2 read, the companion
creates `ready` and waits for `collection-open`, which only the second
validator-launch hook creates. It acknowledges selection of the injected
sample with `injected`; the production reply separately establishes failure
publication and missing acknowledgement/actions. A late release remains valid
test scheduling and cannot undo the selected invalid or expired sample.
The fixture uses an independent native continuous clock to bound its gate wait
to five seconds; expiry creates `timed-out` and exits 71 without fabricating
a production timing failure. The host bounds each receipt wait to six seconds.
Prompt and deliberately delayed authorization, a missing receipt, stale gates,
and withheld authorization with confirmed reap are covered in `WorkerClockTests`.
The tests retain `worker-clock-*-gate.json` receipts and remove their owned gate
directories. These controls run under allow-default and add no production seam.

Three standalone controls compile production worker code with a controlled
timebase and counter and run in `runner_c_worker_harness`:
[clock_control.c](clock_control.c) (`clock_arithmetic`),
[proceed_control.c](proceed_control.c) (`proceed_precedence`) and
[exec_control.c](exec_control.c) (`exec_control_states`), each with its own
build script. The exec case additionally runs six disposable bad-payload
producer variants through the unchanged assertions. Its native-call ledger
records actual boundary order, arguments, return values and meaningful
errno/status independently of the slot payload. The reviewed
[exec_call_policy.json](exec_call_policy.json) records the pre-refactor producer
source and fixture/header hashes plus normalized ledger digests/counts. The
candidate must preserve these 58 call sequences; changing the golden requires
an explicit call-policy review. Native fixture calls do not create real children.
The live process, stream and cleanup observations remain in
[runner_exec_lifecycle](../../suites/runner_exec_lifecycle/README.md).

[sysctl_control.c](sysctl_control.c) includes production `attempt_sysctl_read`
with only `sysctlbyname` substituted. It records actual incoming call arguments
and count, changes the length out-parameter on success and failure, and exposes
the resulting slot status. It never applies a sandbox or makes a native sysctl
call. The owning `runner_c_worker_harness/sysctl_read_capacity` case builds the
baseline and a shortened-capacity producer variant and owns the independent
capacity and limits-manifest assertions.

The `.worker-limits` companion compiles the existing C default-value probe. The
Swift budget inequality consumes its output directly; the independent native
inventory check remains in `runner_abi_layout`. A short worker-expiry scenario
paired with longer validator I/O verifies that an over-budget override preserves
received predictions and cannot revive attempts. The nominal budget relation
applies to production defaults; the validator override intentionally has no cap.

`hold_input` consumes only a short prefix, then leaves stdin open and undrained.
An independent five-second alarm ends the fixture if the host fails to bound
delivery; that intervention fails the control. `drain_bytes` checks the prefix,
200,000 following `x` bytes and EOF, returning 24 only for exact delivery.
Neither mode applies a policy.

The builder ends by executing every fixture once with no arguments and stdin at
EOF, so each exits at its first check, and prints the status and elapsed time of
each exec. That absorbs Gatekeeper's first-launch evaluation of a newly linked
executable (about 200 ms on a fresh macOS 26 machine), which would otherwise be
charged to the first driver test that spawns the fixture, such as the 150 ms
over-budget validator case. The warm-up asserts nothing; the tests own every
behavioral check.

The `.issuer` companion builds the production native issuer for Swift host
controls. `ExtensionEvidenceTests` observe the mapped bytes before and after
host erasure and descriptor closure, then inject unavailable wait/kill observations
while independently reaping the real issuer. Published issuance remains visible,
but unknown host cleanup prevents delivery. The test never prints token bytes.

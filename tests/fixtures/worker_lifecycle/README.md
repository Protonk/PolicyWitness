# Worker lifecycle fixture

`build.sh <output binary>` builds an ABI-compatible test child outside the app.
`runner_unit` supplies its path to Swift tests as `PW_LIFECYCLE_WORKER_FIXTURE`.
Missing equipment fails the required tests. The fixture does not compile or
apply a sandbox and is not evidence of production failure attribution.

Its stdin text selects completed-report exit 0, exit 17, self-SIGTERM, an ignored
exit request, a published legacy failure that ignores exit, or no publication.
It publishes through the ABI's release/acquire protocol. Completed exit/signal
scenarios wait for the host's exit-request flag, proving that the host observed
the report before the abnormal disposition. The hang cases require cleanup by
the host or the owning test. Swift tests use real spawn/mapping/polling/cleanup;
internal OS-call controls inject only otherwise unreliable kill/wait failures.
They independently clean up their child after a simulated unconfirmed reap.

The ready byte is sent after fixture publication for deterministic controls;
real-worker readiness and deadline/grace behavior remain separate tests.

The ABI 7 scenarios also publish unfamiliar/zero failure records, late slots,
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
`.params-CREATE`, `.params-SET`, and `.map-failure`. They compile production C main
with one native boundary substituted (or close the mapping FD before entry).
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
[`diagnostic transport inputs`](../diagnostic_transport/README.md). They publish
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
policy enforcement. `.abi6` refuses the new header. `.clock-failure` and
`.clock-failure-later` substitute only the real C producer's clock boundary and
fail closed at the initial and subsequent clock reads.

The `.worker-limits` companion compiles the existing C default-value probe. The
Swift budget inequality consumes its output directly; the independent native
inventory check remains in `runner_abi_layout`. A short worker-expiry scenario
paired with longer validator I/O verifies that an over-budget override preserves
received predictions and cannot revive attempts. The nominal budget relation
applies to production defaults; the validator override intentionally has no cap.

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

The ABI 6 scenarios also publish unfamiliar/zero failure records, late slots,
started-but-unpublished slots, and rich/missing/empty/truncated diagnostics.
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

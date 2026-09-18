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

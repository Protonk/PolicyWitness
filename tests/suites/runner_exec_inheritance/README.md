# runner_exec_inheritance

Exec-child contract: an empty environment, only descriptors 0/1/2, stdin
yielding EOF, and usable stdout/stderr. The shared C fixture emits an explicit
process-state report; missing output cannot stand in for an empty environment.
Run `tests/run.sh --suite runner_exec_inheritance` outside an automation sandbox.
The built app, Python 3, and the macOS C toolchain are required; missing
prerequisites fail. Both cases run in the default test battery.

## CLI

A normal allow-default specimen executes the helper three times. Each report
must be complete, echo its own nonce, identify the reported exec PID, and meet
the contract. Distinct stderr markers must also survive capture. Several exec
steps exercise isolation from sibling steps' resources. This case has no test
overrides, ABI dependencies, or Swift internals.

## Contaminated worker

The existing `runner_c_worker_harness/harness.c` adapter supplies the real
worker with a random environment value and an inheritable descriptor numbered
at least 200, containing 32 random bytes. The shared helper runs first,
records actual launch state, and execs the worker in the same PID without
consuming its policy pipe. The test verifies the upstream value and bytes,
then requires all three exec children to report clean state using the same
`inspection.py` assertions as the direct fixture controls and CLI case.

This supplies a deterministic opportunity for a leak. Setting a variable or
opening a descriptor in the CLI process alone would not establish that it
reached the launchd-managed XPC host. Only the worker adapter depends on the
current ABI; the observer and contract assertions can survive a worker rewrite.
The adapter's helper path must fit the worker's 128-byte argv entry, and it
fails explicitly if the checkout/output path is too long.

Artifacts include specimens/envelopes, raw inspection output, the worker's
launch-state report, parsed observations, and build/assertion logs. Snapshots
are saved before evaluating clean-state assertions, so leaks remain reviewable.
Both entry points build the exec observer and worker harness through their
shared fixture scripts. `build.log` retains observer compilation and
`harness-build.log` retains harness compilation; their short output paths are
kept below the worker's argv bound. Failed builds stop before execution.

## Development mutation controls

Run `tests/suites/runner_exec_inheritance/opt_in/mutations.sh` to compile and
exercise three disposable workers under `tests/out`: unchanged source, inherited
environment, and descriptor isolation disabled. The unchanged worker must pass;
the other two must fail the ordinary assertions with the specific leak
diagnostic. Setup failures, crashes, and malformed reports do not count as
successful detection. Per-variant source, binaries, reports, and a mutation
summary are retained. The app and production source files are not modified.

This development recipe deliberately depends on the C source's spawn details;
it must be reviewed when those details change. It is opt-in so the normal
contract suite continues to exercise the built distributable without requiring
these source transformations. See `tests/OPT_IN_TESTS.md`.

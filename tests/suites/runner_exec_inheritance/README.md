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
The adapter's helper path must fit the worker's 128-byte argv entry; the
harness refuses a longer one, naming the length and the bound, and the check
reports that message.

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

## Production launch inventory (opt-in)

`tests/run.sh --case runner_exec_inheritance/launch_inventory` selects the
contaminated-worker control as a dependency, then observes two shipped workers
running the same empty allow-default plan. Existing pre-ready and post-apply
sleep overrides hold them for external inspection. The observer records worker
and parent identities, `lsof`, plain `ps` and `ps -E`, and attempts `vmmap` and
`lsmp` as the current user. It requires complete mandatory command captures,
matching final worker identity, expected readiness evidence, confirmed reaping
and subsequent process absence. No external runner is installed.

Boundary placement comes from the selected seam, source order and observation
timing; the observer does not read the worker's publication flags live. A
successful command is raw inventory evidence, not a universal isolation claim.
No specific descriptor set or environment count is required. Optional mapping
or port inspection failures are retained as observation boundaries, not empty
inventories. `lsof`'s text mappings are not a complete library census. The
positive control establishes that a parent-supplied descriptor and environment
value can reach a worker; ordinary CLI exec controls cover the child's narrower
contract. Signal state, resource limits and extension-bearing workers remain
outside this observation. See [opt-in guidance](../../OPT_IN_TESTS.md).

Each boundary retains the exact specimen, CLI capture, process listings, each
observer's argv/status/raw streams, and `observations.json`. The case takes
about forty seconds and needs unsandboxed XPC and same-user process inspection.

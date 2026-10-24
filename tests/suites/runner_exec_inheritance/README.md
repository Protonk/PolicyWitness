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

Run `tests/run.sh --case runner_exec_inheritance/mutation_controls` to compile and
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

## Closed worker stderr (opt-in characterization)

`tests/run.sh --case runner_exec_inheritance/closed_worker_stderr` compares two
direct launches of the unchanged shipped worker. Both use the existing C ABI
harness's three-step exec plan. A case-local adapter leaves all standard
descriptors open for the baseline and closes only fd 2 before execing the worker
for the challenge. Its final pre-exec observations require the policy, evidence,
readiness and stdout descriptors to retain their identities, with fd 2 reporting
`EBADF` in the challenge. The adapter closes its rendezvous socket before these
observations and before exec; that socket cannot fill the worker's fd 2.
An additional `fcntl` guard immediately before `execv`, after formatting and
flushing the snapshot, refuses to enter the worker if fd 2 changed state.

Each exec child checks fd 2 with `fcntl` and `fstat`, then records the native
return and errno from a small stderr write. Those measurements precede any
socket or file acquisition by the observer. The child then sends its receipt
through a separate Unix socket, closes that socket, and emits the same receipt
on stdout for collection by the real worker. The parent obtains peer PIDs from
the kernel and watches their OS exit events. Assertions compare the independent
receipts with completed worker slots, require successful application and phase
release, and require the harness's actual `waitpid` reap with a clean worker
exit. The disposable harness copy adds only an explicit field for that reap
observation.

This is a characterization of a failure: a passing baseline requires usable
child stderr and the captured marker, while a passing challenge requires actual
child fd-2 `EBADF` observations and a stderr write returning `-1/EBADF`. Missing
stderr text alone cannot pass. It does not establish that ordinary XPC launches
supply closed stderr, or that every descriptor arrangement has this result.

Artifacts retain the original and adapted harness sources, the ABI headers and
the first-touch probe header the harness includes,
observer source and configuration, compiled equipment, commands and hashes,
worker hashes before/after, raw peer receipts, worker-entry snapshots, worker
publications and cleanup observations. Connected peer ownership and OS exit
events support failure cleanup; the observer also has its own native deadline
after it becomes an exec child. Unconfirmed cleanup retains the temporary
workspace and its `workspace-owner.json` record. This case needs the signed
app, Python 3, the macOS C toolchain and unsandboxed local socket/process access.

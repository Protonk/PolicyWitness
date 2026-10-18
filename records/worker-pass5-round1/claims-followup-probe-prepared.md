# Claims follow-up — closed worker stderr probe prepared

The independent first report remains unchanged. This follow-up implements the
coordinator's requested test preparation for C2, without executing or building
anything.

New files:

- `tests/suites/runner_exec_inheritance/closed_worker_stderr.sh` (executable entry point).
- `tests/suites/runner_exec_inheritance/opt_in/closed_worker_stderr.py`.
- `tests/suites/runner_exec_inheritance/opt_in/closed_worker_stderr_observer.c`.

A new section in the suite README describes the characterization and its limits.
Catalog, opt-in registry, map, records and suite registration belong to the
coordinator and were not edited here. Production sources and existing checkers
were not edited.

The prepared case compiles an exact retained copy of the existing direct C
harness, with one checked source substitution adding a boolean for whether its
actual `waitpid` returned the worker PID. It does not rebuild or change the
shipped worker. A short-lived workspace keeps the observer path within the
worker argv bound; sources, ABI headers, binaries and hashes are copied into
the durable case artifacts before execution.

The paired cases use the existing `exec_inheritance` three-child plan. The
observer's pre-worker adapter closes fd 2 only for the challenge. Its socket is
closed before descriptor snapshots and the close intervention; the final
pre-exec observation must report fd 2 absent and protocol/stdout identities
unchanged. The baseline must retain all standard descriptors.
After formatting/flushing that receipt, a final `fcntl` guard immediately before
`execv` refuses worker entry unless fd 2 still has the required state.

Each child independently observes `fcntl(2, F_GETFD)`, `fstat(2)` and a stderr
write before opening its observation socket. A passing challenge requires all
three children to report native `EBADF` through that socket, not merely empty
captured stderr. The same JSON must survive as stdout in completed worker
slots. The baseline requires successful stderr writes and exact captured
markers. LOCAL_PEERPID, OS exit events, the real worker publications and an
explicit harness reap observation tie these records to their processes.

Failure handling releases connected peers, terminates the owned harness group
when still alive, and cleans up registered processes while keeping kill requests
separate from exit observations. The child observer has a ten-second native
self-deadline for failures before rendezvous. Final process inspection uses the
exact test-owned helper path only as supplementary diagnostics, not as signalling
authority or proof of an unobserved process's exit. Every started case must have
all four expected, validated peer receipts, registered ownership, matching OS
exit events and a reaped harness before staging can be removed. Incomplete peer
ownership or unconfirmed exits retain the workspace even when `ps` finds no
matching helper. The owner record retains the per-case recovery state.
The process-census artifact retains only exact test-helper-path matches, or an
explicit empty list; unrelated process command lines are not saved.

Primary exceptions are recorded and re-raised unchanged; cleanup/persistence
errors are collected separately and cannot replace an existing primary failure.
Cleanup failure becomes the raised error only when no earlier failure exists.

`equipment/inputs.json` is written before compilation and records source/copy
hash equality, the exact copied ABI-header count, individual harness/adapter/
shared-observer/configuration counts, and the single checked harness anchor and
replacement count. The completed equipment manifest repeats the input counts
and hashes all retained equipment. No native shim is introduced by this case.

Status: source prepared and statically reviewed; **no syntax checks, compilation,
test execution or native reproduction has been performed by this reviewer**.
The coordinator should run the new case serially through the public dispatcher
and inspect both native receipts and cleanup before treating C2 as reproduced.

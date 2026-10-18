# runner_exec_lifecycle

Public CLI contract for an exec deadline: terminate the exec process group,
retain output already written, and continue the specimen's remaining steps.
The suite uses the built app and the shared `tests/fixtures/exec` helper,
without `_test_overrides`, worker ABI access, or Swift internals.

An allow-default specimen executes the helper's controlled process tree,
then writes to a file seeded with random bytes. The observer establishes
that both helper processes are alive and share a group led by the exec
child. It obtains PIDs from kernel socket credentials and requires OS exit
events for both processes before releasing or cleaning up the fixture.

The run must finish within a generous outer bound around the public
10-second exec deadline (8–25 seconds), while the fixture itself has a
45-second backstop. JSON must retain stdout and a fresh stderr marker,
report the observed leader as killed by the deadline, and keep that failure
out of sandbox-denial attribution (an `other_failure` observation beside the
allow answer). The next step must appear
as successful and actually change the target's bytes. The whole specimen
must succeed with complete evidence.

Run `tests/run.sh --suite runner_exec_lifecycle` outside an automation
sandbox. Missing app or toolchain fails. Artifacts include the specimen,
envelope, PID/group and exit observations, before/after file bytes, and logs.
The `exec_fixture` suite independently tests the helper and observer,
including the negative control where only the leader is killed.

CLI execution uses `tests/lib/run_capture.py`. The shared capture retains
`specimen.json`, raw `run.json`/`pw.stderr`, and command/exit/timing metadata in
`capture.json`. Its wait observes the CLI without signalling it. The test checks
OS exit events and the later file write before reading JSON or running cleanup;
the public exec-deadline assertion remains here. Direct capture controls live in
`run_capture`.

The shell entry point uses `tests/lib/case.sh` for setup and logged checks.
Case IDs, checker arguments, and artifact paths remain defined by this suite.
The `shell_helpers` controls verify failure propagation and report/log behavior.

Additional cases close both streams while the observed helper processes keep
responding, or exit the leader while its child retains the streams. The former
must finish naturally after test release; the latter must stop the remaining
group member at the deadline while preserving the leader's actual exit code.
`worker_dies_during_exec` terminates the independently identified worker while
both helper processes are live. Earlier file effects survive; unfinished exec
fields remain absent and later effects are absent. The test owns helper cleanup
and observes liveness before performing it. This guards missing-publication
semantics without claiming that current worker death cleans up descendants.

## Same-group descendant after normal completion

The opt-in `closed_streams_leader_exit` case characterizes a current observation
limit. It closes both helper processes' captured streams, asks the leader to
exit without waiting for its child, and waits for the public CLI to finish.
Before reading PW's JSON or releasing the fixture, the test requires the child
to answer a ping with its original process identity and process group. It also
observes the following file write. The reply must retain a cleanly completed
exec attempt, the leader's zero exit status, and the successful later step.
These facts do not establish that the process group is empty.

The fixture then releases the surviving child and requires its kernel exit
event. The same survivor check must reject that exited child. The test watches
the independently identified worker as well, and removes staging only after
helper/worker exits and CLI cleanup are confirmed. An incomplete rendezvous or
unknown cleanup retains staging and a `cleanup.json` account; cleanup failures
do not replace the original assertion or exception. `observations.json`, raw
capture artifacts and before/after bytes keep the characterization distinct
from the later cleanup intervention.

This is characterization of current behavior, not a desired process-tree
containment rule. Pair it with `closed_streams_continue` and
`leader_exit_descendant`: those neighboring cases exercise stream closure and
leader exit separately.

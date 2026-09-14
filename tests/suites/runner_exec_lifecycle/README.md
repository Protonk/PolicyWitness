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
out of sandbox-denial attribution (`drift=null`). The next step must appear
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

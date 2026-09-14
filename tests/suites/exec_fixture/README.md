# exec_fixture

Direct controls for `tests/fixtures/exec`; needs the macOS C toolchain and
Python 3, without an app dependency. Runs in the default test battery.

- Verify default, empty, and oversized stdout, a fresh stderr marker, and
  exit statuses 0 and 37 through direct `subprocess` execution.
- Launch a tree in a new process group. Check the socket leader PID against
  the launched PID and both peers' groups through the OS.
- Require the exit observer to reject a live tree, then accept normal
  release or a group SIGKILL, with one copy of the original output.
- Kill only the leader. Require the exit observer to reject this partial
  cleanup, confirm the child still answers, then release it and require
  both exits. This is a negative control for leaked descendants.
- Hold two trees simultaneously, release B, and require A to remain responsive
  with unchanged libproc identities. Verify PID/parent/path snapshots against
  the direct launches, reject liveness for exited B, and reject a process
  snapshot after B has been reaped.
- Inspect direct launches with empty and populated environments, with a
  readable FD numbered at least 200 deliberately included or excluded, and
  with EOF or data on stdin. Verify exact canary values/bytes and require the
  same clean-state assertions used by PW tests to reject contamination.
- Inspect then exec the fixture again: PID, environment, descriptor access,
  offsets, and unread stdin must survive. Missing, stale, and incomplete
  reports must be rejected.

Run `tests/run.sh --suite exec_fixture` outside an automation sandbox.
Artifacts include the build/assertion logs and PID/group/exit observations
for each lifecycle control. Missing prerequisites fail.

The shell entry point uses `tests/lib/case.sh` for setup and logged checks.
Case IDs, checker arguments, and artifact paths remain defined by this suite.
The `shell_helpers` controls verify failure propagation and report/log behavior.

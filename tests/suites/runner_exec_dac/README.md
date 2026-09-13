# runner_exec_dac

An execute-permission failure is insufficient evidence of sandbox drift.
This test copies `/usr/bin/true` into a private temporary directory and runs
the same `(allow default)` specimen with its execute bits removed and then
restored. It also executes the helper directly outside PW in both modes.

Both controls must complete before the drift assertion:

- With mode 0644, direct execution fails with EACCES; PW predicts allow but
  reports `exec_failed`, errno EACCES, and no spawned child.
- With mode 0755, direct execution and PW both succeed; PW reports a child
  that exited zero and `drift=false`.
- The first run must have `drift=null`: an ordinary filesystem permission
  error cannot substantiate a disagreement about sandbox enforcement.

This is a strict baseline regression test. There is no expected-failure
allowance or skip for incorrect attribution; the raw failure and the
successful permission control remain visible.

Run `tests/run.sh --suite runner_exec_dac` outside an automation sandbox
(request escalation there). No `_test_overrides` or log capture is used.
Missing builds or failed controls fail the test.

Artifacts include the specimen, both envelopes, direct-execution control
results, stderr, and `assert.log`. The temporary helper is removed afterward.

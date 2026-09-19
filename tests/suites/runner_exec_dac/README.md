# runner_exec_dac

An execute-permission failure is insufficient evidence of sandbox drift.
This test copies `/usr/bin/true` into a private temporary directory and runs
the same `(allow default)` specimen with its execute bits removed and then
restored. It also executes the helper directly outside PW in both modes.

All controls must complete before the drift assertion:

- With mode 0644, direct execution fails with EACCES; PW predicts allow but
  reports `exec_failed`, errno EACCES, and no spawned child.
- With mode 0755, direct execution and PW both succeed; PW reports a child
  that exited zero. The broad `process-exec*` query retains unresolved operation
  scope and `drift=null`, separately from observed spawn success.
- A third run denies a separate prediction target while allowing the attempted
  helper under SBPL. Direct and PW execution both observe DAC EACCES; the deny
  prediction and different submitted target remain visible with `drift=null`.
  Neither that pairing nor EACCES establishes sandbox attribution.
- The first run must have `drift=null`: an ordinary filesystem permission
  error cannot substantiate a disagreement about sandbox enforcement.

This is a strict baseline regression test. There is no expected-failure
allowance or skip for incorrect attribution; the raw failure and the
successful permission control remain visible.

Run `tests/run.sh --suite runner_exec_dac` outside an automation sandbox
(request escalation there). No `_test_overrides` or log capture is used.
Missing builds or failed controls fail the test.

`RunCapture` retains `specimen.json`, `run.json`, `pw.stderr`, and `capture.json`
under separate `nonexecutable/`, `executable/` and `deny_prediction_dac/` artifact directories. Direct
execution results and `assert.log` remain at the artifact root. The temporary
helper is removed afterward. Shell setup and checker logging use `case.sh`.

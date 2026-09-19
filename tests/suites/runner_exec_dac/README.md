# runner_exec_dac

An execute-permission failure is insufficient evidence of sandbox drift.
This test copies `/usr/bin/true` into a private temporary directory and runs
the same `(allow default)` specimen with its execute bits removed and then
restored. It also executes the helper directly outside PW in both modes.

All controls must complete before the drift assertion:

- With mode 0644, direct execution fails with EACCES; PW predicts allow but
  reports `exec_failed`, errno EACCES, and no spawned child.
- With mode 0755, direct execution and PW both succeed; PW reports a child
  that exited zero. The native `process-exec*` query and observed spawn agree
  about the submitted target's execution admission (`drift=false`). This does
  not make the query a prediction of every spawn prerequisite.
- A third run denies a separate prediction target while allowing the attempted
  helper under SBPL. Direct and PW execution both observe DAC EACCES; the deny
  prediction and different submitted target remain visible with `drift=null`.
  Neither that pairing nor EACCES establishes sandbox attribution.
- The first run must have `drift=null`: an ordinary filesystem permission
  error cannot substantiate a disagreement about sandbox enforcement.

This is a strict baseline regression test. There is no expected-failure
allowance or skip for incorrect attribution; the raw failure and the
successful permission control remain visible.

`check_query_scope.py` also builds the shared exec fixture, copies it to owned
`/private/tmp` paths, and drives twelve policies through the native CLI. It checks
80 query/attempt pairs and eleven explicit comparison scenarios. No validator
transcript or request override supplies a verdict. Direct helper runs pin its
marker and exit statuses; hashes verify that the executable and script targets
remain unchanged. Each run retains the exact request and raw envelope.
Each also writes `consumer-answers.json` using only that envelope. The consumer
checks retain scoped agreement, directional consistency, unavailable comparisons
and unattributed failure after successful spawning against the independently
specified native controls.

The controls distinguish target exec admission from fork, file access and
interpreter conditions. Denying fork blocks spawn while the exec query still
allows. Denying interpreter execution blocks a script, but a binary still spawns;
an accepted interpreter query therefore cannot substitute for the exec query.
The bare `process-exec` query is rejected even though that spelling is accepted
in an SBPL rule. A denied query for A paired with a successful spawn of B remains
uncomparable. A child exiting 37 retains its failed exec result alongside the
successful spawn comparison. The comparison reports
`exec_query_not_full_spawn_prediction` and the independent timing/identity limits.

Policy interventions establish the test's expected observations on the supported
system; they do not grant runtime attribution to an arbitrary permission failure.
Native operation-set changes fail these controls for review, rather than silently
accepting an unsupported mapping.

Run `tests/run.sh --suite runner_exec_dac` outside an automation sandbox
(request escalation there). No `_test_overrides` or log capture is used.
Missing builds or failed controls fail the test.

`RunCapture` retains `specimen.json`, `run.json`, `pw.stderr`, and `capture.json`
under separate `nonexecutable/`, `executable/` and `deny_prediction_dac/` artifact directories. Direct
execution results and `assert.log` remain at the artifact root. The temporary
helper is removed afterward. Shell setup and checker logging use `case.sh`.

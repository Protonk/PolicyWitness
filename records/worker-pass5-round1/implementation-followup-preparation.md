# Implementation follow-up — focused characterization prepared, not executed

This follow-up implements the coordinator's requested probe preparation for I1. It does not change the independent first report or turn the source-supported finding into reproduced behavior.

Prepared files:

- `tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py`
- `tests/suites/runner_exec_lifecycle/closed_streams_leader_exit.sh`
- New “Same-group descendant after normal completion” section in `tests/suites/runner_exec_lifecycle/README.md`

The shell wrapper names `runner_exec_lifecycle/closed_streams_leader_exit`, builds only the existing exec fixture when eventually invoked, and runs the new driver through the standard logged case helper. No suite registration, catalog/map/registry changes, production edits, build, test execution or commit were performed by this agent. The coordinator owns registration and execution and will select the existing `closed_streams_continue` and `leader_exit_descendant` neighbors in the managed run.

The driver uses the public CLI with an allow-default specimen and no overrides. It receives fixture PIDs from `TreeControl`, verifies the initial process group and helper identities, identifies/registers an exit observer for the live worker through the helper leader's parent, then closes P/C streams and exits P. After CLI completion and before JSON inspection or release, it pings C, checks stable process identity and the original group, and observes the later file's exact `x` byte. It then requires current-format consumer acceptance, successful worker completion/reap and clean exec publication for the observed leader alongside the later successful step. The native observations and publication assertions remain separate.

The fixture release is a later intervention: after those assertions the driver releases peers and requires OS exit events. It then reruns the same survivor observation and requires rejection specifically because the descendant exited. This is an observer negative control; it does not stand in for the neighboring live paths.

Staging uses `mkdtemp`, with a conservative `cleanup_retained: true` record written before launch. A launch attempt is treated as potentially active even if `RunCapture.start()` fails after process creation. Cleanup keeps OS exit observers open while releasing known peers and, if necessary, requesting termination of still-observed fixture peers; a signal request alone cannot establish cleanup. It records helper and worker exit events plus CLI cleanup, removes staging only when both helper roles and worker exit are confirmed (or no launch was attempted), and retains staging on incomplete rendezvous or unknown cleanup. Original exceptions are re-raised; additional cleanup errors remain in the cleanup account/log rather than replacing them. The existing `TreeControl.close()` is not used as final exit proof because it can close its observer after merely requesting a kill.

Source review included the driver, TreeControl, ExitObserver, process_snapshot, RunCapture, case wrapper and neighboring assertions. Static verification only: Python `ast.parse` (without importing/executing the checker), `bash -n` on the wrapper, whitespace inspection, and `git diff --check` on the README change. All succeeded. Runtime and teardown behavior remain untested pending the coordinator's managed execution.

The original report hashes remain unchanged:

- `implementation-initial.md`: `2aa2781fc04bbb36016815f984b1219d18a7f5b24605c81979e61cabd6486a81`
- `implementation.md`: `0c11c9606ab3b6c3262efe199f22d14288793560659806dd28847bb7fa47d72e`

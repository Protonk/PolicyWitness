# shell_helpers

Direct controls for the baseline shell helpers in `tests/lib/case.sh`. Requires
Bash and Python 3, with no PolicyWitness app, compiler, socket, or XPC dependency.
This suite runs in the default battery:

```sh
tests/run.sh --suite shell_helpers
```

## Helper contract

Source `tests/lib/case.sh`, which loads `testlib.sh`, then call `test_begin`.
The case owns its suite/test identity, steps, checker arguments, and final
`test_pass`. The helpers do not decide that a case has passed.

- `test_require_pw` resolves `PW_BIN` from `PW_APP_DIR` or the default bundle,
  honoring an explicit `PW_BIN`. A missing/nonexecutable file fails the case.
  The existing `require_pw_app` still provides its separate optional-app skip
  behavior; callers choose the appropriate prerequisite rule.
- `test_run_logged <log> <failure message> <command> [args...]` executes literal
  argv and retains combined stdout/stderr at the supplied path. A nonzero exit
  prints the log, records failure with the command status and log path, and exits
  the case. Failure to open the log also fails before the command runs.
- `test_build_fixture <build script> <output>` invokes `bash <script> <output>`,
  retains `build.log`, and requires an executable file at the output path.
  Compiler flags and the build recipe stay in the existing fixture build script.
- `test_check_python <log> <failure message> <script> [args...]` runs the checker
  with `/usr/bin/python3` through `test_run_logged`. Missing commands or checker
  arguments fail explicitly. Every nonzero checker status, including 3, fails.

Callers include `runner_validator_failure`, `runner_exec_lifecycle`,
`runner_specimen_isolation`, `runner_exec_dac`, `runner_live_worker_identity`,
`sbpl_allowdeny_consistency`, `exec_fixture`, and `run_capture`. Each supplies
its own `build.log`, `assert.log`, or `assertions.log` artifact paths.

## Controls

The fixture in `tests/fixtures/shell_case/` runs a case without `set -e`.
Separate commands independently record their execution and actual arguments,
emit distinct stdout/stderr markers, and provide a controlled build product or
exit status. The commands import no helper or production code.

Controls cover successful execution, binary overrides, missing/nonexecutable
apps (including a directory in place of the binary), failed builds, missing or
nonexecutable build products, failing checkers, missing commands/checkers,
failure to open a log, and the existing optional-app skip. A command printing
`ok` before exiting nonzero must still fail. Argument controls include spaces,
quotes, newlines, and shell syntax with a canary that must never execute.

The Python observer checks command receipts, exact log bytes, wrapper exit
status, the per-case report, and both local/global event streams. Failure must
prevent later commands and a passing terminal event. Case identity and artifact
paths must survive a suite alias and a working directory outside the repo.
Each control has isolated output/events so intentional failures and skips do
not enter the enclosing suite's report. Its entry point uses `testlib.sh`
directly, independently of the new helpers.

Artifacts retain each fixture configuration, execution journal, raw wrapper
output, exit status, logs, events, report, and the passing control inventory.

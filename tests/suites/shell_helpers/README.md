# shell_helpers

Direct controls for `tests/lib/case.sh`, `tests/lib/scripts.sh`, and the public
result helpers in `tests/lib/testlib.sh`. Requires Bash and Python 3, with no
PolicyWitness app, compiler, socket, or XPC dependency.
This suite runs in the default battery:

```sh
tests/run.sh --suite shell_helpers
```

## Helper contract

Source `tests/lib/case.sh`, which loads `testlib.sh`, then call `test_begin`.
The case owns its suite/test identity, steps, checker arguments, and final
`test_pass`. The helpers do not decide that a case has passed.

Loading `testlib.sh` checks the actual `/usr/bin/python3` assertion mode and
exits 2 with an actionable diagnostic if assertions are disabled. This protects
the dispatcher and direct shell suite entry points before case work or output
initialization. Unset `PYTHONOPTIMIZE` to run tests; empty and `0` values remain
valid because they leave assertions enabled. The check uses an explicit branch
and exits even when sourcing occurs in a conditional with errexit disabled.

- `test_require_pw` resolves `PW_BIN` from `PW_APP_DIR` or the default bundle,
  honoring an explicit `PW_BIN`. A missing/nonexecutable file fails the case.
  The existing `require_pw_app` still provides its separate optional-app skip
  behavior; callers choose the appropriate prerequisite rule.
- `test_run_logged <log> <failure message> <command> [args...]` executes literal
  argv and retains combined stdout/stderr at the supplied path. A nonzero exit
  prints the log, records failure with the command status and log path, and exits
  the case. Failure to open the log also fails before the command runs.
- `test_build_fixture <build script> <output> [log]` invokes `bash <script> <output>`,
  retains the supplied log (default `build.log`), and requires an executable
  file at the output path. Separate logs preserve evidence for multiple builds
  in one case, including when a later build fails.
  Compiler flags and the build recipe stay in the existing fixture build script.
- `test_check_python <log> <failure message> <script> [args...]` runs the checker
  with `/usr/bin/python3` through `test_run_logged`. Missing commands or checker
  arguments fail explicitly. Every nonzero checker status, including 3, fails.

Callers include `runner_validator_failure`, `runner_exec_lifecycle`,
`runner_specimen_isolation`, `runner_exec_dac`, `runner_live_worker_identity`,
`sbpl_allowdeny_consistency`, `runner_c_worker_harness`, `runner_exec_inheritance`,
`exec_fixture`, and `run_capture`. Each supplies
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

## Python startup

The `python_startup` case runs the real dispatcher and a direct suite in fixture
repositories under six optimization settings: unset, empty, `0`, `1`, `2`, and
non-numeric text. Each setting exercises both a passing and a deliberately
failing assertion checker. Rejected startup must exit 2 before any fixture
receipt or report is written and preserve all prior output bytes. Accepted
startup must run the checker with assertions enabled and propagate its outcome.

The control driver uses explicit conditions, with no Python assertions of its
own. The assertion checker imports no test-library implementation. Independent
receipts record its execution and assertion mode, and whether the case continued.
Separate logs and exit metadata retain every subprocess observation.

## Child-script groups

`test_run_scripts <script> [script...]` sources no case state. It invokes each
literal path with Bash, in order, retaining the child's stdout/stderr and
continuing after any nonzero exit or missing script. It returns 1 if any child
failed, otherwise 0; an empty list fails. It does not change the caller's shell
options, synthesize case reports, or interpret a child's explicit skip.
The top-level dispatcher reconciles the reports that the children emit.

`blackbox_e2e`, `witness_contract`, and `opt_in` supply their selected script
lists. `runner_byoxpc` retains its setup gates, environment transitions, and
cleanup trap while using the helper for child execution. The single-child
`smoke` and `sbpl_allowdeny_consistency` wrappers use `exec bash` and forward
the child's exact exit status.

The `script_groups` case runs both direct helper controls and copies of all six
real wrappers in isolated repositories. Independent children record execution,
arguments, and environment; print distinct stream markers; and exit or skip as
configured. Controls cover literal paths, order, failure continuation, missing
and empty inputs, caller/child errexit, single-child status forwarding, and
BYOXPC setup gates, runner-mode propagation, and cleanup after downstream
success or failure. BYOXPC installation and removal use harmless stand-ins.
The witness wrapper must retain its baseline-first ordering and selected cases.

Artifacts retain fixture repositories, child receipts, wrapper streams, exit
statuses, configurations, and the control inventory.

## Result finalization

`test_pass`, `test_pass_note`, `test_fail`, and `test_skip` share a private
writer for duration calculation, the terminal event in both event streams,
and the case report. Each public function owns its default message, console
output, and return/exit behavior. Ordinary pass/skip logging respects quiet
mode; `test_pass_note` always prints. `test_fail` writes its diagnostic to
stderr and exits 1 even when the caller has disabled errexit. Pass and skip
return success so callers can continue with another case.

The `finalizers` case exercises all four public functions with quiet mode on
and off, omitted arguments, empty arguments, and literal messages/JSON data.
The fixture calls `test_begin` and the selected public function, then writes
an independent receipt if execution continues. The Python observer imports
no test-library code. It checks process status, exact stdout/stderr, the
receipt, one start/terminal event pair in each stream, and the matching report.
Suite alias, case identity, message, duration, and artifact path must agree;
nested JSON, quotes, newlines, backslashes, and Unicode must survive. A shell
expression in the message must never create its canary file.

These controls inspect public behavior without replacing the clock or calling
the private writer. Elapsed time is bounded by the enclosing process duration;
the event and report must contain the same nonnegative integer duration.
Artifacts retain inputs, raw streams, exit status, receipts, event/report files,
and the control inventory. Intentional failures remain in isolated outputs.

## Worker-suite setup

The `worker_setup` case runs disposable copies of the actual C-worker suite
with independent builder/harness programs from `fixtures/worker_harness/`.
Controls cover a failed rebuild with an old executable still present, a
successful builder producing no executable, a harness printing valid JSON then
exiting nonzero, malformed output, a failed observation, and failure after an
earlier case passes. Equipment failures must stop before the assertion stage.

Independent receipts check the exact output path, worker/scenario arguments,
and compilation only once across two cases. Case identities, reports, raw
stdout/stderr, and build logs remain distinct. These controls exercise the
real conditional calls where errexit alone cannot enforce build failures.

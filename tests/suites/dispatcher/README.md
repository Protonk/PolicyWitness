# dispatcher

Controls for top-level test execution and report reconciliation. Requires Bash
and Python 3, with no app, compiler, XPC, or socket dependency. In the default
battery; run separately with `tests/run.sh --suite dispatcher`.

## Contract

`tests/run.sh` selects suites and prepares the output directory, then delegates
execution and the final result to `tests/lib/suite_run.py`. The dispatcher writes
`dispatch.json` before starting work and updates it after each requested suite.
Each invocation records its requested name, index, execution state, timestamps,
exit status, observed report paths, report snapshots, and harness errors.

After each suite exits, the dispatcher reconciles newly appended events and
new or changed case reports. Each case needs one start followed by one terminal
event, a readable report with matching path/identity, and agreement between the
terminal event and report status. Case names may differ from the requested suite:
wrappers are associated with the reports emitted during their invocation.

Missing/nonexecutable runners, nonzero suite exits, empty suites, unfinished
cases, invalid events or reports, contradictory statuses, and removed or reused
case evidence are harness failures. Repeating a suite that reuses case paths
fails explicitly; use separate runs to retain independent artifacts. Later
requested suites still execute after a failure. Explicit reported skips remain
skips; a silent exit is not a skip.

`run.json` retains its case `reports`, `counts`, and reported `suites` fields.
It adds `requested_suites`, `invocations`, and `harness_errors`. Counts describe
the structurally valid case reports that were read; they do not invent failed
cases for a dispatcher failure. `ok` requires zero failed reports **and** zero
harness errors. This same decision is the command's exit status (0 or 1).
Reports and raw case artifacts retain their existing paths. Invalid raw files
remain available for diagnosis; harness errors name their invocation and path.

## Independent controls

`check.py` creates small repositories containing copies of the actual entry
point, dispatcher, and testlib, plus the controlled suites under
`tests/fixtures/dispatcher/`. It invokes `tests/run.sh --suite ...` from outside
each repository and inspects the process status, final summary, and dispatch
journal. It neither imports the dispatcher nor supplies precomputed aggregates.

Controls cover passes and explicit skips; aliases; missing/nonexecutable runners;
silent exits; crashes before and after reporting; failed reports with exit zero;
malformed, missing, or wrongly attributed reports; missing and duplicate terminal
events; status disagreement; stale, malformed, unreadable, or rewritten events;
signal termination; repeated case paths; and removal of a prior suite's report.
Failure cases generally request a subsequent passing suite to prove dispatch
continues. Previous run output is seeded and must be replaced.

Artifacts retain the fixture repositories, raw dispatcher stdout/stderr, process
exit status, dispatch journals, summaries, source evidence, and `controls.json`.

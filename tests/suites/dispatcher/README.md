# dispatcher

Offline contracts for public selection, configuration, execution, and evidence
reconciliation. Run `tests/run.sh --suite dispatcher`, or select `controls`,
`accounting_controls`, or `selection_controls` by their full `dispatcher/<case>`
IDs. Each group runs once in its own invocation through the public command, so
a failure in reconciliation does not suppress the accounting group.

## Contract

`tests/run.sh` invokes `tests/lib/test_cli.py`. The CLI expands `tests/catalog.json`,
validates selectors and configuration, and produces a plan before writing output.
No selectors means default membership; explicit selectors form a deduplicated
union in catalog order. Dependencies appear in the plan. `--all` includes opt-ins;
`--list` is a read-only JSON description of exactly the selected plan. Relative
configuration paths resolve from the repository, even when invoked elsewhere.
`selection.suites` records requested suites; `containing_suites` lists membership
of the selected cases. Whole-app symlinks are accepted, but the controller must
resolve within the named bundle. Distinct catalog IDs cannot share a report path;
valid reporting aliases and suite inclusions remain supported.

Execution writes `plan.json` and delegates to `tests/lib/suite_run.py`. Each
ordinary case has a separate command invocation. BYOXPC specimen cases share a
single installation/cleanup lifecycle; the wrapper runs selected specimens in
separate child processes. Independent cases continue after a failing command.
Unavailable requirements or failed dependencies leave explicit unrun selections.

`dispatch.json` journals invocations and evidence. Each observed case needs one
start followed by one terminal event, a readable report with matching identity,
and agreement between terminal event and report status. Reports must belong to
the selected plan. Suite inclusions reuse canonical IDs, while runner contexts
have distinct IDs. Repeating a selector executes once; actual reused evidence
still fails reconciliation.

`run.json` includes the original selectors, plan/configuration, case reports/counts, invocations,
harness errors, and one `case_results` entry per selection. `completion` counts
selected, completed, skipped, and unrun cases. Readable report counts remain
separate from missing-report failures. `ok` and process exit agree: no failed
reports and no harness errors. A case may skip only with a `skip_reason` declared
in its catalog contract. Required equipment missing is a run failure. Planning
errors exit 2 without replacing evidence.

## Independent controls

`check.py` exercises reconciliation against controlled reports/events: aliases,
crashes, silent exits, malformed or missing evidence, contradictory statuses,
rewritten events, reused paths, and removed reports. Failure scenarios generally
include a subsequent passing case. Missing/nonexecutable entrypoints instead
prove rejection happens before any execution or output replacement.

`accounting_controls` runs `check_accounting.py`, which supplies independent
handoff records directly at the accounting/finalization boundary: ambiguous ownership must retain both
selections as unrun, and missing, duplicated, unexpected, or invalid result
records must never produce success. These controls bypass catalog validation
deliberately to check the executor's separate defense. A valid alias and reordered
complete results remain accepted. Inputs, summaries, diagnostics, and return
statuses are retained alongside the other controls.

`check_selection.py` uses an independently authored tiny catalog and fixture
commands that import no test machinery. Their execution receipts record actual
case IDs, literal argv, working directory, and effective artifact configuration.
The observer uses explicit conditionals rather than Python assertions. It checks
union/order/deduplication, distinct contexts, dependencies, default/all membership,
read-only inspection, rejected flags/configuration, symlink output escapes,
artifact aliases, quiet values, required equipment, unexpected evidence, skip
contracts, and complete accounting after failures. Whole-tree byte snapshots
also catch accidental bytecode writes during inspection.
Split bundles and colliding catalog report paths must be rejected without
execution or evidence replacement; whole-app and internal controller symlinks
must preserve the selected bundle in execution receipts.
Two runnable stub bundles also verify default and explicit app selection. The
selected controller records its own path, arguments, and bundle-local marker;
an ignored override must fail even when the fallback app is usable.

`tests/fixtures/dispatcher/repository.py` only copies equipment and writes the
caller-supplied catalog; it contains no expected selections or result oracle.
Fixtures, receipts, raw stdout/stderr, exit status, plans, journals, summaries,
and `controls.json` remain in artifacts for inspection.

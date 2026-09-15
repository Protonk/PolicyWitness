# runner_byoxpc

Runner suite for BYOXPC services. It installs a BYOXPC runner, runs the shared
smoke and blackbox scripts through `runner.mode=byoxpc`, and validates
`runner_kind` in the output.

## Invariants

- Requires launchd bootstrap from a logged-in GUI session.
- Installs a BYOXPC runner under the user scope and removes it after the suite.
- Shared smoke and blackbox scripts receive `PW_TEST_RUNNER_MODE=byoxpc` and the
  installed service name.

## Opt-in tests

- `tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh`

## Artifacts

- `tests/out/suites/runner_byoxpc/<test_id>/artifacts/*`

Run:

```
./tests/run.sh --suite runner_byoxpc
```

The public catalog excludes these cases from the default battery. `--all` includes
them. `--case runner_byoxpc/BBX-001` selects just that specimen and its installation
dependency. Shared offline checker controls run once in their standard suites,
not again for each runner context. The external-auth case has its own invocation;
its failure does not suppress an otherwise usable team-matched runner.

The wrapper installs once for selected specimen cases, continues independent
specimens after failures, and removes the runner on exit. Missing required GUI,
app, or signing equipment fails with explicit unrun selections in the public
summary. `PW_TEST_RUNNER_*` variables are private to this wrapper; select cases
instead of exporting those variables to `tests/run.sh`.

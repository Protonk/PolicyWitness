# runner_byoxpc

Runner suite for BYOXPC services. It installs a BYOXPC runner, runs the shared
smoke and blackbox scripts through `runner.mode=byoxpc`, and validates
`runner_kind` in the output.

## Invariants

- Requires launchd bootstrap from a logged-in GUI session.
- Installs a BYOXPC runner under the user scope and removes it after the suite.
- The team-matched path copies the complete runner to an owned `/private/tmp`
  directory and gives it a unique service identifier. Only that copy is signed;
  source signatures/entitlements and before/after file inventories are retained.
  The caller-auth settings and embedded helper bytes must stay unchanged.
- Shared smoke and blackbox scripts receive `PW_TEST_RUNNER_MODE=byoxpc` and the
  installed service name.

## Opt-in tests

- `tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh`
- `tests/suites/runner_byoxpc/opt_in/registry_recovery.sh`

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/runner_byoxpc/<test_id>/artifacts/*`

Run:

```
./tests/run.sh --suite runner_byoxpc
```

The public catalog excludes these cases from the default battery. `--all` includes
them. `--case runner_byoxpc/BBX-001` selects just that specimen and its installation
dependency. Shared offline checker controls run once in their standard suites,
not again for each runner context. The external-auth case has its own invocation;
its failure does not suppress an otherwise usable team-matched runner.

The external-auth case uses the shared session helper and stages its disposable
ad-hoc runner with a unique `com.policywitness.test.*` service in a unique directory
under `/private/tmp`, so launching it does not depend on Desktop/Documents
privacy consent when the checkout or artifacts live there. Its modified plist,
signing output, and install/verify/remove results stay in the case artifacts.
Exit cleanup removes the service before deleting the temporary bundle; a failed
service removal retains the bundle and fails the case.

The wrapper installs once for selected specimen cases, continues independent
specimens after failures, and removes the runner on exit. Missing required GUI,
app, or signing equipment fails with explicit unrun selections in the public
summary. `PW_TEST_RUNNER_*` variables are private to this wrapper; select cases
instead of exporting those variables to `tests/run.sh`.

Cleanup ownership starts before installation, including failures before a runner
environment or successful install report exists. Removal warnings and lingering
registry/launchd/plist state fail the wrapper and retain staging for inspection.
A partial or uncertain installation with a pending registry record is recovered
through public removal. Uncertain installation without a record retains staging.
The durable session record stays beside the bundle; run-local receipts point to
it, so deleting output does not erase recovery state. The wrapper never pre-cleans the ordinary runner's
identifier. See `tests/fixtures/byoxpc/README.md` for the ownership contract and
`shell_helpers/byoxpc_setup` for offline failure controls.

Shared BBX file targets also use owned `/private/tmp` scratch, with before/after
artifacts and exit cleanup. Existing privacy-database entries are not modified.

`registry_recovery` runs actual CLI controls with registry and HOME paths supplied
only to child processes. It verifies pending/installed transitions, skip-bootstrap,
pending specimen rejection, filesystem write failures, ownership disagreement,
conflicts with pending cleanup, and concurrent modifying commands. Read-only
reconcile checks unregistered candidates and unknown inspection failures. A live
user-scope installation proves skipped bootout retains the running service after
plist removal and that recovery works without original diagnostic output.
Every uniquely owned service and plist must be absent before staging is deleted.

Rust unit controls separately exercise the production removal transaction with
supplied launchd observations: bootout/unlink failures, unknown/unowned state,
process loss after bootout, and failed retirement persistence. These controls
establish state transitions; the opt-in case supplies actual launchd evidence.

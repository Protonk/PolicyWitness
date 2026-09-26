# Cleanup hardening plan

Implement the steps below in order, using separate reviewable commits. Read the
repository `AGENTS.md` and the guidance for each area before editing it. Run
focused checks as each step lands and update its documentation in the same
commit. Delete this plan after final acceptance and documentation are complete.

## 1. Preserve the acceptance record

Preserve `tests/out/ordering-final-all` unchanged. Before implementation, write
`tests/out/ordering-final-all.inventory.json` containing the complete entry set:
relative path, entry type and permission mode; SHA-256 for regular files;
literal target for symlinks; and directories, including empty ones. Walk without
following symlinks. Final verification must detect added, removed and changed
entries.

During implementation, give test runs fresh, explicit `PW_TEST_OUT_DIR` paths
under `tests/out/runs/`. Exercise default-output replacement and `make clean`
only in isolated fixture checkouts until their respective protection steps pass.

## 2. Ignore generated helpers

Add exact root-relative `.gitignore` entries for
`controller/tools/pw_probe_runner/pw-probe-runner` and
`controller/tools/sb_api_validator/sb_api_validator`.

Verify both with `git check-ignore -v` and confirm they remain untracked. During
the signed build in final verification, confirm the expected bundle helpers are
produced and the generated intermediates create no Git changes.

## 3. Share the prediction-unavailable pair set

Read `runner/AGENTS.md` for Swift test requirements. Expose the existing
`predictionUnavailableOpFilters` constant in `ProbeRunner.swift` within its
module. Delete `predictionUnavailableOpFiltersHostMirror` from
`CWorkerOrchestrator.swift` and point `planValidatorQueries` at the shared set.
Preserve the exact pairs, their evidence comments and both callers' behavior.

In `tests/suites/source_drift/check.py`, replace the comparison between the two
Swift sets and documentation with a check of the shared set against
`docs/PolicyWitness.md`. Remove the obsolete mirror parser. Update comments and
coverage descriptions that describe the duplicated set.

`PredictionUnavailableTests.swift` pins the three exclusions through
`runSandboxCheck`. Add independent `planValidatorQueries` cases for those pairs,
an unknown filter kind, and a known filter paired with an operation outside the
set. Preserve the expected exclusion reasons and ordinary query behavior. Run
`source_drift`, `runner_unit` with its required worker equipment, and the live
`runner_filter_*` witnesses against a signed build.

## 4. Protect output and serialize execution

Work in `tests/lib/test_cli.py`, `tests/lib/suite_run.py`,
`tests/lib/release_accept.py` and the dispatcher controls. Deliver retention and
output protection first, followed by the checkout-wide lock.

### Retention and run identity

Create the committed `tests/RETAINED.json` index outside `tests/out`. Each entry
contains `path` relative to `tests/out`, `run_id`, `reason`, `source` (commit hash
or null when unknown), and `app_inventory` (the run-relative evidence reference,
or null when unavailable). Seed it with `ordering-final-all`, run ID
`20260926T170356Z_4addd6eb`, and its existing artifact-integrity reference. Its
158 selected cases completed; record `source` as null because `run.json`
provides no commit hash. Retention metadata stays outside retained directories.

Set the default output to `tests/out/runs/default`. Named disposable runs use
`tests/out/runs/<name>`. Explicit `PW_TEST_OUT_DIR` paths remain bounded within
`tests/out` and separate from the selected app.

Recognize managed run roots through dispatcher-written ownership metadata tied
to their run ID and output path. Write ownership before launching tests. A
completed run has finalized execution and test-process teardown followed by a
valid terminal run record. Completed runs with failed tests are disposable when
unretained. Missing, malformed or inconsistent completion evidence leaves a
managed run interrupted or ambiguous; placement under `runs/` alone does not
establish ownership.

Before replacing output, validate the retention index and target. Refuse a
target equal to, containing, or inside an indexed path, and refuse replacement
of interrupted or ambiguous run output. Report the reason so the caller can
choose a fresh output directory or inspect the existing one. Planning refusals
use exit 2 and leave output unchanged.

Index paths must remain within `tests/out`, with symlink redirects and path
escapes rejected. A missing, malformed or unreadable index prevents destructive
operations. Indexed directories absent from a checkout remain valid entries;
their paths stay protected. Help, `--list` and invalid requests are read-only.

### Checkout-wide lock

Use an OS-held advisory lock on a stable ignored file outside `tests/out`.
After read-only planning succeeds, acquire the lock, revalidate the index and
output eligibility, then hold it through execution. A competing mutating
operation receives a checkout-busy error even when it names a different output
path. Keep the lock file in place between operations. PID/start information is
diagnostic; lock release on process exit leaves completion to the run records.
Help and `--list` remain available while execution holds the lock.

### Integration and verification

Keep release acceptance under `tests/out/release-acceptance/run-*`, with its
nested dispatcher output subject to the same protection checks. A passing
release acceptance prints a suggested index entry. Exercise this through
`preflight/release_controls` and the release invocation path.

Add `dispatcher/retention_controls` using independent fixture checkouts and
execution receipts. Cover retained siblings; targets equal to, containing and
inside retained paths; missing local retained directories; invalid indexes;
symlink/path escapes; completed failed runs; interrupted replacement refusal;
competing operations; independent checkout locks; and owner exit without run
completion. Verify retained inventories and read-only command behavior from
filesystem observations.

Run `dispatcher` and relevant `shell_helpers` controls. Update `tests/README.md`
and `tests/suites/dispatcher/README.md` for the index, run identity, output
replacement and lock. Update root `AGENTS.md`'s testing guidance. Default
execution in the working checkout is available after these checks pass.

## 5. Preserve runner ownership through incomplete cleanup

Work in `controller/src/runner_commands.rs`, `runner_manager.rs`,
`runner_select.rs`, and the BYOXPC session and test wrappers.

### Registry and installation

Serialize modifying commands with a stable lock beside the selected registry.
Hold it across each command's registry read-modify-write sequence and associated
launchd actions. Write registry changes through a temporary file and atomic
rename. Keep schema version 1, using serde defaults for additive fields. Add a
default-empty `pending_cleanup` collection for removal records. Check new
installation identities against both `runners` and `pending_cleanup`.

Add `RunnerRecord.state`, with `pending` and `installed`, defaulting to
`installed` when absent. Save `pending` before writing the plist. Set
`installed` when the requested installation completes: after bootstrap normally,
or after plist creation with `--skip-bootstrap`. Report loaded status through
its own observation. List the state, reject pending records for specimen
selection, and allow their removal. Errors after the pending save leave the
record available for recovery and report it on stderr.

### Removal and reconciliation

Before removal touches launchd or the plist, atomically move the runner record
from `runners` into `pending_cleanup`. A failed save leaves machine state untouched.
Launchd/plist failures preserve the cleanup record and appear in `data.warnings`;
the runner has already left the active collection.

Each cleanup record retains identity, scope/domain, plist and bundle/executable
paths, ownership information and observations sufficient for retry without the
originating test output. Recheck ownership before acting. Retire the record only
after service and plist absence are verified; errors, unknown state or failure
to persist retirement leave a retryable record. `runner remove` accepts cleanup
records through its existing selectors. With `--skip-bootout`, retain recovery
state until service absence is observed.

Add report-only `runner reconcile`. For runner and cleanup records, report
recorded state and observed service/plist presence. Scan user LaunchAgents and
readable system LaunchDaemons for `com.policywitness.*` labels or `PWRunner`
executables, reporting candidates missing from both collections. Classify
ownership as owned, unowned or ambiguous; report inspection failures as unknown.
A label-prefix match identifies a candidate for reporting. Cleanup requires
validated ownership.

Update usage in `controller/src/cli.rs` and `runner_commands.rs`, the CLI and
registry contracts in `controller/README.md`, and the external-runner cleanup
section in `docs/PolicyWitness.md`.

### Test-owned runners and verification

Use `tests/fixtures/byoxpc/session.py` for ownership and staging. Migrate
`tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh` to a session variant
with ad hoc signing, auth keys removed and a unique `com.policywitness.test.`
label. Treat installation failure as a failed case. The helper deletes its
staging only after verified service/plist absence and confirmed cleanup.

Keep live recovery records in the durable registry and test-owned bundles in
staging outside disposable run output. Keep the helper's ownership and recovery
record with its staged bundle until that bundle is removed. These records must
contain everything required for recovery; run-local copies serve as diagnostic
receipts.

Extend `check_byoxpc_setup.py` and registry tests for pending/installed transitions,
`--skip-bootstrap`, pending-selection refusal, partial installation, removal
warnings, uncertain ownership, crashes and repeated cleanup. Cover bootout
failure followed by successful plist removal: reconcile must still find the
service through `pending_cleanup`. Verify recovery after the original test
output is deleted, and concurrent modifying commands against one registry.
Include installation conflicts with pending cleanup and helper recovery after
machine cleanup succeeds but staging deletion is interrupted.

Rust unit tests exercise persistence, transitions and classification over supplied
observations. Filesystem CLI controls use `PW_RUNNER_REGISTRY` and `HOME` in
fixture child processes. Failure controls must demonstrate the boundary reached
and inspect surviving state: initial pending save, plist creation, and the
installed save after observed successful pending persistence and bootstrap.

The production CLI invokes real system commands. Actual bootstrap, launchd
inspection and removal run in opt-in user-scope tests with unique owned services
and verified cleanup. Fixture `HOME` redirects filesystem paths; live tests use
the actual GUI domain and follow repository escalation guidance.

Run `unit`, relevant `shell_helpers` controls and the opt-in `runner_byoxpc`
suite. Update `tests/OPT_IN_TESTS.md` and the affected suite/session documentation.

## 6. Add explicit pruning

Implement pruning in the public `tests/run.sh` interface using the established
ownership, completion and retention checks. Prune candidates are managed run
roots under `tests/out/runs/` that have completed and are unretained. Completed
runs with failed tests are eligible. Preserve interrupted, ambiguous, retained
and unmanaged output, reporting the reason for each disposition. Interrupted
output remains available for deliberate cleanup after inspection.

`tests/run.sh --prune` previews dispositions (`delete`, `keep: retained`,
`keep: interrupted`, `keep: ambiguous`, `keep: unmanaged`).
`tests/run.sh --prune --apply` acquires the checkout lock and evaluates current
eligibility before deletion. Apply reports actual removals and each failure;
its exit status reports failure if a deletion fails. Preview uses the same
classification rules on a read-only snapshot. Reject combinations with case or
suite selection and reject `--apply` without `--prune`.

Keep all pruning inside `tests/out/runs/`. Report output elsewhere under
`tests/out`, including release acceptance, as unmanaged and preserve it. Refuse
symlink redirects, path escapes and deletion of any candidate that overlaps an
indexed path. Make `make clean` delegate to `tests/run.sh --prune --apply`.

Extend retention controls for successful and failed completed runs, interrupted
and ambiguous runs, unmanaged directories, preview/apply state changes, invalid
indexes, retained-path overlap, lock contention, deletion failures and
`make clean`. Enforce an unlink/rmdir failure through fixture directory
permissions and verify both the reported failure and remaining filesystem state.

Run `dispatcher`, relevant `shell_helpers` and release controls. Document the
commands and dispositions in `tests/README.md` and
`tests/suites/dispatcher/README.md`, with the `make clean` behavior in root
`AGENTS.md`. The working checkout's `make clean` is available after these checks
pass.

## 7. Final acceptance

Commit implementation and maintained documentation, then make a fresh signed
build. Confirm generated helper paths are ignored and the shipped bundle
inventory and signatures pass their checks. Run `tests/run.sh --all` with
`PW_TEST_OUT_DIR=tests/out/runs/hardening-final-all`. Account for every selected
case, failure and skip under the repository's acceptance contract.

Run `runner reconcile` and inspect `/private/tmp/pw-byoxpc-*`,
`/private/tmp/pw-runner-noauth.*` and `/private/tmp/pw-release-*`. Resolve every
test-owned leftover or explain its ownership and recovery state. Recompute the
`ordering-final-all` inventory and require an exact match.

Add the passing final run to `tests/RETAINED.json` with its actual tested source
and artifact provenance. Keep its execution receipts with the acceptance output.
Commit the index entry and this plan's deletion together once all acceptance
obligations are satisfied.

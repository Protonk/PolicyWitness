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
entries. `artifact.inventory` in `tests/lib/artifact.py` already meets this
specification (lstat modes, symlink targets, SHA-256 for regular files,
directory entries); use it rather than writing a new walker, and reuse it in
`retention_controls` to prove retained bytes unchanged. The record currently
holds 20 symlinks and 111 empty directories.

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
`tests/out` and separate from the selected app. Direct script invocation falls
back to `tests/out` in `tests/lib/testlib.sh` (line 47) and
`tests/suites/runner_byoxpc/run.sh`; point both at `tests/out/runs/direct`.
Neither path replaces output, but the old fallback would litter
`tests/out/suites/` at the root.

Recognize managed run roots through `owner.json`, written by the dispatcher
before anything else in the run directory, containing the run ID, the resolved
output path and the start time. `plan.json` carries no run ID and
`dispatch.json` is written after execution begins, so neither serves. A
completed run has a valid terminal `run.json` whose run ID matches `owner.json`.
Ctrl-C still writes `run.json` with interrupted invocations, so such a run is
completed; only a missing or invalid terminal record (crash, SIGKILL) leaves a
managed run interrupted. Completed runs with failed or interrupted cases are
disposable when unretained. Malformed or inconsistent completion evidence
leaves a managed run ambiguous; placement under `runs/` alone does not
establish ownership.

Before replacing output, validate the retention index and target. Refuse a
target equal to, containing, or inside an indexed path, and refuse replacement
of interrupted or ambiguous run output. Report the reason so the caller can
choose a fresh output directory or inspect the existing one. Deliberate removal
of interrupted or ambiguous output is `--prune --apply --unfinished <name>`
(step 6); do not document manual `rm -rf`, which bypasses the lock. Planning
refusals use exit 2 and leave output unchanged.

Index paths must remain within `tests/out`, with symlink redirects and path
escapes rejected. A missing, malformed or unreadable index prevents destructive
operations. Indexed directories absent from a checkout remain valid entries;
their paths stay protected. Help, `--list` and invalid requests are read-only.

### Checkout-wide lock

Use an OS-held advisory lock (`fcntl.flock`) on `tests/.checkout.lock`, ignored
through the root `.gitignore` (there is no `tests/.gitignore`). Derive the path
from the repository root the dispatcher runs from, so fixture checkouts lock
independently. Do not place it under `.tmp/`, which is slated for deletion:
unlinking a held lock file silently disables the lock for every later process,
because a new file is a new inode. Document that consequence.

After read-only planning succeeds, acquire the lock, revalidate the index and
output eligibility, then hold it through execution. A competing mutating
operation receives a checkout-busy error even when it names a different output
path. Keep the lock file in place between operations. PID/start information is
diagnostic; lock release on process exit leaves completion to the run records.
Help and `--list` remain available while execution holds the lock.

Document the cost: one checkout runs one execution at a time. A quick smoke run
waits for a long `--all`, and parallel work needs a second worktree.

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
Install, remove and validate take it; list, status, verify and reconcile do not,
and the atomic rename below means they read the old or the new file, never a
torn one. Hold the lock across each command's registry read-modify-write
sequence and associated launchd actions. Implement it with
`std::fs::File::lock` and `try_lock`, stable in the standard library since Rust
1.89 (the checkout builds with 1.91); set `rust-version = "1.89"` in
`controller/Cargo.toml`. Do not add `libc`, `fs2` or any other crate for this.

Write registry changes through a temporary file and atomic rename. Keep schema
version 1, using serde defaults for additive fields. This is safe because
`RunnerRegistry` derives serde without `deny_unknown_fields`, and ordinary
specimen runs never load the registry (only external selectors reach
`load_registry`), so older binaries and release acceptance are unaffected. Add
a default-empty `pending_cleanup` collection for removal records. Check new
installation identities against both `runners` and `pending_cleanup`; a
conflict with a cleanup record reports the same remedy as an active conflict,
`runner remove` for that service name, which retries the cleanup.

Add `RunnerRecord.state`, with `pending` and `installed`, defaulting to
`installed` when absent. Save `pending` before writing the plist. Set
`installed` when the requested installation completes: after bootstrap normally,
or after plist creation with `--skip-bootstrap`. Report loaded status through
its own observation. List the state and allow removal of pending records.
Reject pending records for specimen selection in `find_external_record`
(`runner_select.rs`) with a distinct error text, `external runner is pending
installation`, that tests pin; `status` and `verify` may read pending records
and report the state. Errors after the pending save leave the record available
for recovery and report it on stderr.

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

Envelope changes are additive and named here so the contract documentation and
tests agree: `runner install` reports `state`; `runner list` adds
`pending_cleanup`; `runner remove` adds `cleanup_retained` (boolean) and, when
true, the retained record. Current consumers are the session helper (reads
`runners`), one `run_effects` check (reads the envelope kind) and the auth test
being migrated, so nothing existing breaks.

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
receipts. The run-local receipt records the staging path and the wrapper's
cleanup trap follows it, since the record no longer lives under the run output.
The registry record's `bundle_path` is the recovery pointer a human follows from
`runner reconcile` output to the staging directory.

The `uncertain_install` scenario changes. Today the helper refuses cleanup when
installer completion is uncertain and retains staging for inspection. With a
pending record, the helper reads the registry: if a record for its service
exists, it proceeds through `runner remove`; if none exists, it retains staging
as today. Update the scenario and the helper together.

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
classification rules on a read-only snapshot and does not hold the lock. It
tries the lock non-blocking: when busy, it reports that an execution holds the
checkout and labels runs without a terminal record `keep: active or
interrupted` instead of `keep: interrupted`. Reject combinations with case or
suite selection and reject `--apply` without `--prune`.

`tests/run.sh --prune --apply --unfinished <name>` deletes one named
interrupted or ambiguous managed run under the lock, after the retained-overlap
check. It is the only supported way to remove such output. Reject
`--unfinished` without `--apply`, and reject a name that resolves to a
completed, retained or unmanaged directory.

Keep all pruning inside `tests/out/runs/`. Consider only directories directly
under `runs/`; never touch files anywhere under `tests/out`, including
`ordering-final-all.inventory.json`. Report output elsewhere under `tests/out`,
including release acceptance, as unmanaged and preserve it. Refuse symlink
redirects, path escapes and deletion of any candidate that overlaps an indexed
path. Make `make clean` delegate to `tests/run.sh --prune --apply`; it no
longer removes release acceptance output.

Extend retention controls for successful and failed completed runs, interrupted
and ambiguous runs, unmanaged directories, preview/apply state changes, preview
under a held lock, `--unfinished` against each disposition, invalid indexes,
retained-path overlap, lock contention, deletion failures and `make clean`. Enforce an unlink/rmdir failure through fixture directory
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
and artifact provenance. `source` is the implementation commit the build came
from; the index commit necessarily follows it and is not the source. Keep its
execution receipts with the acceptance output.
Commit the index entry and this plan's deletion together once all acceptance
obligations are satisfied.

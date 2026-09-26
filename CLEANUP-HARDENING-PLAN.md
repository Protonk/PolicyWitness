# Cleanup hardening plan

For an Astra-class implementation agent. Baseline: cleanup commit `3a914e7`.
Scope: the four repairs below, plus three additions that would have prevented
the original accumulation: a per-run lock, a report-only `runner reconcile`,
and a leftover sweep. General scratch/cache management and a
documentation-retirement policy remain outside this work.

**Retirement condition:** delete this plan when the four repairs are implemented,
their checks pass, and maintained documentation describes the resulting behavior.
Durable contracts go to the documents named under "Documentation destinations";
execution receipts stay with the acceptance output.

## Decisions already made

Resolved on 2026-09-26. Do not reopen them.

- Pruning is an explicit command, never a side effect of execution. No age or
  size heuristics.
- The retention record is a committed index at `tests/RETAINED.json`, outside
  `tests/out`. Nothing is written inside a retained directory.
- Controlled failures on the Rust side come from real levers (read-only
  registry directory, read-only LaunchAgents, bad executable path). Do not add a
  launchctl override seam. `tests/fixtures/byoxpc/session.py` records that the
  CLI always uses real commands, and that decision stands.
- The final `--all` run of this work becomes a second indexed acceptance record
  alongside `ordering-final-all`.

## Starting constraints

Read root `AGENTS.md`, `tests/README.md`, `controller/README.md` and
`runner/AGENTS.md` before changing their respective areas.

Preserve the existing `tests/out/ordering-final-all` acceptance record: no file
inside it changes and no file is added to it. It describes the previous build,
not verification of these repairs. Before any other change, write an inventory
(relative path and SHA-256 of every file) to
`tests/out/ordering-final-all.inventory.json` and compare against it at the end.

Until the protection commit in repair 1 lands, never run tests with the default
output directory and never invoke `make clean`. After it lands, both are safe
and this constraint expires.

## 1. Protect evidence, then bound ordinary output retention

Files: `tests/lib/test_cli.py`, `tests/lib/suite_run.py`,
`tests/lib/release_accept.py`, `Makefile`, `tests/suites/dispatcher/`,
`tests/README.md`.

The hazard is exact. `test_cli.py` removes the whole output directory before
executing, the default output directory is `tests/out` itself, and `make clean`
is `rm -rf tests/out/*`. So default execution deletes `ordering-final-all`.

**Protection (first commit of this repair).**

- Create `tests/RETAINED.json`: a list of entries with `path` (relative to
  `tests/out`), `run_id`, `reason`, `source` (a commit hash, or an explicit
  statement that the record carries none) and `app_inventory` (the reference
  into the run's `artifact-integrity/` evidence). Seed it with
  `ordering-final-all`: run id `20260926T170356Z_4addd6eb`, 158 of 158 selected
  cases completed, built from the tree at or before `3a914e7`; `run.json` does
  not record a commit hash, so the entry says so.
- Move the default output directory to `tests/out/runs/default`. Disposable
  runs live under `tests/out/runs/<name>`. `PW_TEST_OUT_DIR` keeps its existing
  contract (inside `tests/out`, not overlapping the app) and may still name any
  path under `tests/out`.
- Before replacing anything, execution loads the index and refuses a target
  that is, contains, or is inside an indexed path. Refusal is a planning error
  (exit 2) with no side effects, like other rejected configurations. Help,
  `--list` and invalid requests stay side-effect free.
- Index paths must resolve inside `tests/out` and must not be symlinks; reject
  `..` escapes the way `resolve_config` already bounds the target.

**Lock (same repair, separate commit).** Execution creates an exclusive lock
file in the run directory holding pid and start time, and holds it for the run.
A live lock refuses execution against that directory. Document that pid
liveness is a heuristic (pid reuse), not proof.

**Prune (lands after repair 2).**

- `tests/run.sh --prune` is dry-run by default: one line per candidate under
  `tests/out/runs/` with its disposition (`delete`, `keep: retained`,
  `keep: live lock`, `keep: interrupted`, `keep: unmanaged`). `--prune --apply`
  deletes only the candidates the preview marked `delete` and prints what was
  actually removed and every deletion failure. `--prune` combined with a
  selection is an error.
- Prune never touches anything outside `tests/out/runs/`. Directories elsewhere
  under `tests/out` (for example `release-acceptance/` and older named runs)
  are reported as unmanaged and preserved.
- A dead-pid lock means an interrupted run: preserved unless that directory is
  named explicitly with `--prune <name>`.
- `make clean` becomes a one-line delegation to `--prune --apply`, so there is
  one implementation.

**Integrations.** `release_accept.py` already writes under
`tests/out/release-acceptance/run-*` and runs the dispatcher nested inside that
directory. Keep the location, make the nested call pass the overlap check, and
have a passing acceptance print the suggested `RETAINED.json` entry. The
`preflight/release_controls` case exercises this path. Update the output
contract, configuration and examples in `tests/README.md` and
`tests/suites/dispatcher/README.md`, and the testing bullet in root `AGENTS.md`
that tells callers to set `PW_TEST_OUT_DIR` to protect evidence.

**Tests.** Add `dispatcher/retention_controls` following the
`check_selection.py` pattern (independent tiny catalog, fixture commands that
import no test machinery, execution receipts). Cover: default execution with an
indexed sibling present; an explicit target equal to, inside, and containing an
indexed path; a live lock and a dead-pid lock; unmanaged directories; prune
preview versus actual deletions; a deletion failure (read-only entry); and
`make clean` through the same code path. Assert filesystem effects and
unchanged retained bytes (inventory before and after), not reported success.
Also assert that `--list`, help and refused configurations leave `tests/out`
byte-identical.

## 2. Make runner ownership survive incomplete cleanup

Files: `controller/src/runner_commands.rs`, `controller/src/runner_manager.rs`,
`controller/src/cli.rs`, `tests/fixtures/byoxpc/session.py`,
`tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh`,
`tests/suites/shell_helpers/check_byoxpc_setup.py`.

Facts established by reading the code. Do not rediscover them.

- Install order is sign, verify, write plist, bootstrap, then save registry. A
  registry save failure after bootstrap leaves a loaded service with no record.
  `runner_auth_external.sh` removes a runner only when it parsed an id from
  install stdout, so that failure leaks. It is the one live install path outside
  the session helper. Its install-failure branch emits a skip the catalog does
  not declare.
- `load_registry` rejects any `schema_version` other than the current one.
  "Additive" therefore means a serde-defaulted field, not a version bump.
- `save_registry` is a plain `fs::write`, not atomic.
- The session helper already records ownership before install, refuses to
  delete staging after a removal with warnings, and verifies launchd, plist and
  registry absence. `check_byoxpc_setup.py` already covers partial install,
  unowned plist, remove failure, remove warning, remove lies, uncertain install
  and registered unowned plist.
- The controller never deletes runner bundles; only the test helper deletes its
  own staging. Bullets about bundle deletion are test-side.

**Product side.**

- Two-phase install: add a `state` field to `RunnerRecord` with values
  `pending` and `installed`, defaulting to `installed` when absent so existing
  registries load unchanged. Save a `pending` record before writing the plist;
  flip it to `installed` after bootstrap succeeds. `runner list` shows the
  state. `runner remove` accepts pending records. The install error path leaves
  the pending record in place and says so on stderr.
- Make `save_registry` write to a temporary file and rename.
- Preserve the documented `runner remove` contract: the registry change always
  persists; launchd and plist failures surface as `data.warnings`.
- Add `runner reconcile`, report only. For each registry record: plist present,
  launchd present, state. Then scan `~/Library/LaunchAgents` (and
  `/Library/LaunchDaemons` when readable) for plists whose label starts with
  `com.policywitness.` or whose program is a `PWRunner` executable, and report
  the ones with no registry record as unowned. Classify owned, unowned and
  ambiguous. Never delete. A permission or inspection failure is reported as
  unknown, not absence; a label prefix alone never authorizes deletion. This is
  a CLI surface change: update the usage text in `cli.rs` and the CLI surface
  section in `controller/README.md` in the same commit.

**Test side.**

- Migrate `runner_auth_external.sh` onto the session helper with a no-auth
  variant (ad hoc signing, auth keys removed). Give it the
  `com.policywitness.test.` label prefix so the sweep can find it. Remove the
  undeclared skip; a failed install is a failure.
- Require verified service and plist absence before deleting an owned staging
  bundle or declaring cleanup complete. Permission and inspection failures mean
  unknown state, not absence. Retries are idempotent.
- Extend `check_byoxpc_setup.py` with only the delta: registry save failure
  after bootstrap, crash between bootstrap and save, repeated cleanup, and the
  migrated no-auth path.
- Rust unit tests for the two-phase install and reconcile drive everything
  through `PW_RUNNER_REGISTRY` and `HOME` pointed at a fixture tree. Real
  failure levers: `PW_RUNNER_REGISTRY` into a read-only directory (save failure
  after bootstrap), `HOME` with a read-only `Library/LaunchAgents` (plist write
  failure), a bad executable path (bootstrap failure). Live user-scope removal
  stays in the opt-in `runner_byoxpc` suite and follows repository escalation
  guidance.

## 3. Ignore the generated helper binaries

Both binaries were deleted in `3a914e7` and are untracked now; `git check-ignore`
reports nothing for them. Add exact root-relative `.gitignore` entries for
`controller/tools/pw_probe_runner/pw-probe-runner` and
`controller/tools/sb_api_validator/sb_api_validator`. Verify with
`git check-ignore -v`, then confirm a normal build produces the signed bundle
helpers and leaves `git status` clean. No new test.

## 4. Share the prediction-unavailable pair set

Both sets are `private let` constants in the same module. Drop `private` from
`predictionUnavailableOpFilters` in `ProbeRunner.swift`, delete
`predictionUnavailableOpFiltersHostMirror` in `CWorkerOrchestrator.swift`, and
point `planValidatorQueries` at the shared set. No new file, so `build.sh` and
`Package.swift` are untouched. Preserve the pairs, their evidence comments and
both callers' behavior. No legacy-runner removal or classification changes.

In `tests/suites/source_drift/check.py`, delete
`parse_orchestrator_prediction_unavailable_pairs` and replace the three-way
comparison with the canonical set against `docs/PolicyWitness.md`, plus a
negative check that the orchestrator contains no literal pair list and
references the shared symbol.

Tests: `PredictionUnavailableTests.swift` already pins the three pairs through
`runSandboxCheck`. Add `planValidatorQueries` tests that pin
`prediction_unavailable_pair` for each pair, `unrecognized_filter_kind` for an
unknown kind, and no exclusion for a known filter kind paired with an operation
outside the set (the filter alone is not the pair). Retain the live
`runner_filter_*` witnesses and existing envelope assertions.

## Delivery

Separate reviewable commits, in this order:

1. Repair 3.
2. Repair 4.
3. Repair 1 protection (index, default directory, refusal), then the lock.
4. Repair 2 product side, then test side.
5. Repair 1 prune and `make clean`.
6. Final verification.

Run focused checks as each lands: `source_drift` and `runner_unit` for repair 4;
`dispatcher` and `shell_helpers` for repair 1; `unit`, `shell_helpers` and the
opt-in `runner_byoxpc` suite for repair 2.

Finish with a fresh signed build and `tests/run.sh --all` into
`tests/out/runs/hardening-final-all`. Account for every failure and skip. Then
run the leftover sweep: `runner reconcile` plus a listing of
`/private/tmp/pw-byoxpc-*`, `/private/tmp/pw-runner-noauth.*` and
`/private/tmp/pw-release-*`; every entry must be explained or removed by its
owner. Confirm `ordering-final-all` matches its pre-work inventory, add the
final run to `tests/RETAINED.json`, and retire this plan.

## Documentation destinations

- `tests/README.md`: output layout, `RETAINED.json`, lock, `--prune`,
  `make clean`.
- `tests/suites/dispatcher/README.md`: retention controls.
- Root `AGENTS.md`: the testing bullet about output replacement.
- `controller/README.md`: CLI surface (`runner reconcile`), registry `state`,
  atomic writes, remove contract unchanged.
- `docs/PolicyWitness.md`: external runner cleanup section, with reconcile
  before the manual recipes.
- `tests/OPT_IN_TESTS.md`: `runner_auth_external` now owned by the session
  helper.

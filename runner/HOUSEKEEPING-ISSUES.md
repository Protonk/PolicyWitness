# Housekeeping issues

Things on this machine and in this tree that accumulated during development and
have no owner. Facts as of 2026-09-26.

## Machine state

- **Five orphaned LaunchAgents.** `~/Library/LaunchAgents` still holds
  `com.policywitness.runner.machme` and four `com.policywitness.runner.runner-<hash>`
  plists. They point at app copies that no longer exist under
  `~/Desktop/PolicyWitness` and `~/Desktop/VM-BRIDGE/PAWL`, `launchctl list` shows
  them with last exit status 78, and `policy-witness runner list` reports an
  empty registry, so no PolicyWitness tool knows about them. Removal needs a
  `launchctl bootout gui/$(id -u)/<label>` per label plus deleting the plist; an
  automation harness declined that action on 2026-09-26.

## Working tree and local state

- **`tests/out` holds 79 named output directories, 925 MB**, dated 2026-09-13 to
  2026-09-26, plus a stray `events.jsonl`. The largest are `failure-propagation-4`
  (126 MB), `control_surface` (88 MB), `testing-audit` (67 MB), `lim1`, `fpc` and
  `fp5` (about 53 MB each). `ordering-final-all` (59 MB) is the current full
  acceptance record; the rest are retained diagnostics from finished work. The
  dispatcher replaces only the directory it is pointed at, so every named
  `PW_TEST_OUT_DIR` persists until someone deletes it, and nothing records which
  ones are still evidence for anything.
- **Two tracked build outputs.** `controller/tools/pw_probe_runner/pw-probe-runner`
  and `controller/tools/sb_api_validator/sb_api_validator` are committed binaries
  that `build.sh` rewrites on every run. The shipped copies are the signed
  bundle-local ones inside `PWRunner.xpc`; the tracked copies only add a binary
  diff to the working tree after each build and a mismatching hash to every
  source snapshot.
- **Three historical planning and audit documents remain in `tests/`.**
  `tests/TESTING-AUDIT.md` (a completed audit prompt with its results),
  `tests/TEST-EQUIPMENT-PLAN.md` and `tests/FAILURE-PROPAGATION-INVENTORY.md` (a
  pre-implementation dependency inventory). They are the same kind of document
  as the retired ordering plan. The inventory is still linked from
  `runner/README.md`, `tests/FAILURE-PROPAGATION-CONTRACT.md`, `tests/COVERAGE.md`
  and `tests/README.md`, so retiring it means moving or dropping four links.
- **`.tmp/` at the repository root is 122 MB of ignored scratch**: an old
  `RUNNER-RESTORE-PLAN.md`, five `opt_in_test_*` directories, `pw_*` specimen and
  result JSON, a `release-v2.3.0` directory, session debug directories and two
  Swift module caches (110 MB between them). None of it is referenced by the
  build or the tests.
- **Build caches are large but ordinary**: `controller/target` is 532 MB and
  `runner/.build` is 100 MB. Both are ignored and safe to delete at any time.
- **One duplicated list.** `predictionUnavailableOpFiltersHostMirror` in
  `CWorkerOrchestrator.swift` mirrors `predictionUnavailableOpFilters` in
  `ProbeRunner.swift`; `source_drift` fails when they disagree, which is the
  only thing keeping them equal.

## A few ideas for not accreting these

- Give `tests/run.sh` a retention rule for `tests/out`: keep the default
  directory and anything named in a committed record, and prune the rest past a
  size or age, printing what it removed.
- Stop tracking the two build outputs and ignore their paths; the signed bundle
  hashes already identify what shipped.
- When a plan or audit document is created, write its retirement condition into
  its first lines and delete it when that condition is met, as was done for the
  ordering plan.
- Have every test-owned launchd install use one reserved label prefix and record
  it in the runner registry, so a single sweep can find what tests left behind.

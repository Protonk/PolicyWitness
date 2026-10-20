# Keep SwiftPM build trees out of test evidence

## Problem and intended result

Seven `runner_unit` cases build a disposable Swift package inside their
`artifacts/` directory, usually a copy of the runner package, with
`swift build` or `swift run --package-path <copy>`. SwiftPM writes its default
`.build` tree beside the package, so every build retains 60 to 120 MB of
compiler state as case evidence for as long as the run exists. The state is
reproducible and nothing reads it after the case ends.

After this change those cases build in a per-case scratch directory that the
case finalizer removes, and the dispatcher reports any completed case that
leaves a SwiftPM build tree or its scratch directory behind. Mutated sources,
snapshots, logs, receipts and results stay where they are now. Retention,
pruning and locking behavior do not change.

This is an implementation plan. Follow the [test working rules](AGENTS.md).

## Observations

On 2026-10-19, `tests/out/runs` held 5.1 GiB in 43 runs, 3.4 GiB of it in
`.build` trees under these cases:

| Case | Default | Package builds per run | `.build` across those runs |
| --- | --- | --- | --- |
| `host_setup_oracle_sensitivity` | opt-in | 4 | 828 MiB |
| `service_admission_controls` | yes | 1 | 730 MiB |
| `launch_descriptor_controls` | yes | 1 | 618 MiB |
| `host_setup_controls` | yes | 1 | 614 MiB |
| `sleep_record_controls` | yes | 1 | 254 MiB |
| `exec_reader_mutations` | opt-in | 1 | 233 MiB |
| `reaped_ack_mutation` | opt-in | 1 | 210 MiB |

`find tests/out/runs -type d -name .build -prune -exec du -sk {} +` remeasures
local output. The default battery `ordering-final-default-20261019` used
669 MiB, 374 MiB of it in `.build`; a `runner_unit` selection used about
1 GiB, nearly all of it `.build`. Built products are about 10 MB of each tree;
the rest is precompiled SDK modules, intermediates and module caches. Without
their build trees, these case directories held at most 5.2 MiB each.

An experiment with Swift 6.4 (`swiftlang-6.4.0.34.1`, arm64, macOS 26) settled
SwiftPM's behavior. A copy of the runner package, prepared as
`service_admission_controls` prepares it, was run with
`swift run --package-path <copy> --scratch-path <dir> PWRunnerCoreTests`:

- The tests passed. All 104 MB of build state was under `<dir>`, and the
  copy's directory listing was unchanged.
- `swift build --package-path <copy> --scratch-path <dir> --show-bin-path`
  printed `<dir>/out/Products/Debug`. Without `--scratch-path` it printed
  `<copy>/.build/out/Products/Debug`, where no product exists, and created an
  8 KB `<copy>/.build` holding `CACHEDIR.TAG` and `.buildSystem_debug`.
- No SwiftPM or build-service process remained after the command returned,
  and nothing recreated `<dir>` after it was removed.
- The build into the fresh scratch directory took about 8 seconds.

`swift build --product` with `--scratch-path` was not exercised separately;
the converted cases' own assertions cover it.

The opt-in `witness_contract/order_barrier_mutations` already builds its copied
package in a temporary directory under `/private/tmp`
([mutations.py](suites/witness_contract/opt_in/mutations.py)) and retains no
build tree.

## Scope

The change covers case setup and finalization in [testlib.sh](lib/testlib.sh),
the seven producers and their wrappers, a reconciliation check in
[suite_run.py](lib/suite_run.py), their controls and their documentation.

It leaves these alone:

- `order_barrier_mutations`, which already complies; changing it would bring
  its own rerun obligations without reducing retained output.
- Other copied inputs. Dispatcher controls copy fixture repositories as
  deliberate inputs, and the planner controls keep a 0.5 MB Meson build
  directory.
- `runner/.build` and `controller/target`, which are build caches in the
  source tree rather than test output.
- Existing runs. Retained runs keep their build trees; ordinary pruning
  removes unretained runs.

## Decisions

### Scratch lives in the case directory

`test_begin` exports `PW_TEST_SCRATCH=${PW_TEST_DIR}/scratch`, beside
`artifacts/`, without creating it. Inside the run, scratch is covered by the
run's ownership record, the checkout lock and pruning: scratch left by an
interrupted case is removed with its run, and no build writes outside
`tests/out`. A `/private/tmp` temporary directory is left behind when its
process is killed, and `.tmp/` is operator scratch under
[its own rules](../.tmp/AGENTS.md), not test output.

A SwiftPM cache shared across runs would avoid cold builds, but it would
couple runs and mutation variants through incremental build state. Cold
builds are short enough not to need it.

### Producers receive scratch as an argument

Each producer takes its scratch directory as a required positional argument,
as it already takes its output directory, and its `.sh` wrapper passes a path
under `${PW_TEST_SCRATCH}`. A direct Python invocation then cannot fall back
to building inside its evidence. Pass `--scratch-path` to every SwiftPM call
for a package, including `--show-bin-path`.

Use one scratch path per package copy, as there is one `.build` per copy now.
Cases that rebuild one copy for successive variants
(`service_admission_controls`, `exec_reader_mutations`, `reaped_ack_mutation`)
keep their current incremental builds. `host_setup_oracle_sensitivity`
prepares a separate source root per variant and runs the preserved
`host_setup_controls` recipe against it, so `host_setup_controls.run` gains a
scratch parameter and each variant passes its own subdirectory.

### Finalization removes scratch for every outcome

`_test_finish`, shared by `test_pass`, `test_pass_note`, `test_fail` and
`test_skip`, removes `${PW_TEST_DIR}/scratch` before writing the terminal
event. Compute the path from `PW_TEST_DIR` instead of reading
`PW_TEST_SCRATCH`, and skip removal when `test_begin` has not established a
case directory, so a finalizer never removes a caller-supplied path. A failed
removal must not prevent the terminal event and report; reconciliation then
records the retained scratch.

Remove scratch after failures too. Compiler diagnostics are already in each
case's build log, mutated sources stay in `artifacts/`, and a failed build
tree costs about 100 MB per case. A case killed before finalization keeps its
scratch inside the run; the dispatcher already reports that case as missing
its report or unrun.

Built executables are not retained. `launch_descriptor_controls` records the
host test executable's SHA-256 in `equipment.json`; that record remains, but
the bytes do not, and a rebuild from the retained sources is not promised to
reproduce them.

### Reconciliation rejects retained build state

In `reconcile()`, for each case with a readable terminal report, inspect its
directory `suites/<suite>/<test_id>/` without following links:

- a directory named `.build` anywhere below it records `build_tree_in_evidence`;
- a remaining `scratch/` records `scratch_retained`.

Both are harness errors. They leave case statuses unchanged and make
`run.json.ok` false, so a regression in a default case also blocks the release
battery until it is fixed. The check sees only SwiftPM's default location; a
build redirected elsewhere under `artifacts/` is caught by the size check in
verification and by review of new producers.

## Changes

Make these in order: the reconciliation check would fail unconverted producers.

1. **Case scratch and finalization.** Export `PW_TEST_SCRATCH` from
   `test_begin` and remove the case scratch in `_test_finish`
   ([testlib.sh](lib/testlib.sh)). Extend the `finalizers` control
   ([check_finalizers.py](suites/shell_helpers/check_finalizers.py) with
   [finalize.sh](fixtures/shell_case/finalize.sh)): for each public finalizer,
   a populated scratch directory is absent afterward, `artifacts/` is
   unchanged, and a directory outside the case named by a reassigned
   `PW_TEST_SCRATCH` survives.
2. **Producers.** Add the scratch argument and `--scratch-path`, and pass the
   argument from each case's `.sh` wrapper:
   - [service_admission_controls.py](suites/runner_unit/service_admission_controls.py): `swift run`.
   - [sleep_record_controls.py](suites/runner_unit/sleep_record_controls.py): `swift run`.
   - [host_setup_controls.py](suites/runner_unit/host_setup_controls.py): `swift build` and `--show-bin-path` in `run`.
   - [launch_descriptor_controls.py](suites/runner_unit/launch_descriptor_controls.py): the `core-build` command and `--show-bin-path`.
   - [host_setup_oracle_sensitivity.py](suites/runner_unit/host_setup_oracle_sensitivity.py): one subdirectory per variant, passed to the preserved recipe.
   - [exec_reader_mutations.py](suites/runner_unit/opt_in/exec_reader_mutations.py): `swift run`.
   - [reaped_ack_mutation.py](suites/runner_unit/opt_in/reaped_ack_mutation.py): `swift run`.
3. **Reconciliation check.** Add both codes to `reconcile()` in
   [suite_run.py](lib/suite_run.py). In [check.py](suites/dispatcher/check.py)
   and the fixture suite [run.sh](fixtures/dispatcher/run.sh), add three
   scenarios, each followed by a passing case like the existing ones:
   - a case that writes into `PW_TEST_SCRATCH` and passes: the run is `ok` and
     no scratch remains;
   - a case that creates `artifacts/<name>/.build` and passes:
     `build_tree_in_evidence`;
   - a case that recreates its scratch after finalization: `scratch_retained`.
4. **Documentation.**
   - [Output contract](README.md#output-contract-testsout): add `scratch/` to
     the case layout as removed at finalization, and add both rejections to
     the reconciliation paragraph. Describe `PW_TEST_SCRATCH` under
     [shell case setup](README.md#shell-case-setup-and-checking).
   - [shell_helpers README](suites/shell_helpers/README.md): the variable in
     the helper contract, removal under result finalization, and the extended
     `finalizers` control.
   - [dispatcher README](suites/dispatcher/README.md): the new reconciliation
     scenarios.
   - [runner_unit README](suites/runner_unit/README.md): the seven cases build
     in scratch and retain sources, logs and receipts, not build products.
   - [Working rules](AGENTS.md#add-or-change-tests): one sentence directing
     build intermediates to `PW_TEST_SCRATCH` while sources, logs and receipts
     stay in `artifacts/`. Reconciliation catches only SwiftPM's default
     location; the rule covers other build state.

## Verification and completion

Use fresh output for each dispatcher run
(`PW_TEST_OUT_DIR=tests/out/runs/<name>`), a signed app for
`launch_descriptor_controls`, and the documented unsandboxed retry for
equipment refusals.

- **Build location.** Run each converted producer's Python script directly
  once, with assertions enabled, an output directory and a scratch directory
  under `.tmp/`. The scratch directory must hold the SwiftPM state
  (`workspace-state.json` and `out/`), and the output directory must contain
  no `.build`. After a dispatcher run the scratch is gone, so this is the only
  observation that builds went to the argument rather than to some path
  outside the case.
- **Controls.** `tests/run.sh --suite shell_helpers --suite dispatcher`. Each
  new scenario must produce exactly its expected codes while the existing
  scenarios keep theirs.
- **Producers.** `tests/run.sh --suite runner_unit`, which includes the three
  opt-ins. The cases' assertions require each mutation's specific failure and
  each fixed variant's pass; a missing `--scratch-path` on `--show-bin-path`
  names a nonexistent executable and fails. Copies and scratch paths are new
  in every run, so no earlier product can stand in for a build. Afterward,
  `find <run> -name .build` and `find <run> -type d -name scratch` return
  nothing, and each converted case directory is under about 6 MiB. A larger
  directory means build state reached evidence by a path that neither
  finalization nor reconciliation detects.
- **Integration.** The default battery, because every case uses `testlib.sh`
  and every invocation passes through `reconcile()`.

The change is complete when these runs pass with no harness errors, none of
their case directories holds a `.build` tree or `scratch/`, and the
documentation describes the scratch layout and both checks.

## Evidence that would require reconsideration

- A `scratch_retained` error after a finalizer ran suggests a process that
  outlived the build and wrote to scratch. Identify that process rather than
  rerunning; the experiment found none.
- A toolchain that writes outside `--scratch-path` would put build state back
  in the package copy. Reconciliation catches the default location; the size
  check catches other locations under the case.
- An investigation that needed a failed case's build tree would argue for
  keeping scratch after failures, at about 100 MB per failed case.

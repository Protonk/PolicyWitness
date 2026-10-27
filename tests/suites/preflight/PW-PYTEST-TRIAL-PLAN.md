# Trial of a subordinate pytest host for build_provenance_controls

## Objective and boundary

Run [check_build_provenance.py](check_build_provenance.py) under pytest beneath
the existing dispatcher, then refactor its record controls, and decide from
measured net benefit whether to keep, defer or revert the arrangement. The
[investigation plan](PW-PYTEST-INTEGRATION-INVESTIGATION-PLAN.md) holds the
research and the invariants that still apply; the
[baseline record](../../../records/tests/pytest/PW-PYTEST-BASELINE-3ec96c1.md)
holds the whole-file inventory (identifiers `BP01` to `BP68`, variant tables for
`BP62`, `BP63` and `BP44`, nine flagged expectations) and the execution
reference. This plan is sufficient to begin; those two documents are optional
background.

Boundary: the dispatcher, the catalog case `preflight/build_provenance_controls`
and its `clang` requirement are unchanged. The case keeps one report path; no
inner parameter becomes a catalog case. The checker's interpreter and its
`-B -S` start are unchanged, and the tested helpers and their children keep
seeing only the interpreter and the tree. Other test migrations are outside
this plan. Every baseline expectation, the nine flagged ones included, is
preserved unchanged through the trial, as the investigation plan requires;
corrections follow the trial's closing decision as separate changes whose rows
carry the `revised` label. During the stages a row carries only `preserved`,
`isolation-improved` or `blocked`.

Decision criteria, judged at the end of each stage from the comparison rows and
run evidence:

1. **Net machinery.** Count the lines added that a maintainer of the checker
   must understand (the launcher, its acceptance rules, the receipt, the
   vendored-package checks, the drift allowlist, the documentation) against
   the organizational lines removed from the checker (ownership and
   temporary-directory boilerplate, hand-written scenario loops, restoration
   code). The one-time verification controls are counted separately and must
   not grow when the checker changes. Stage 1 must remove at least as much as
   stage 0 added outside those controls; otherwise reject and revert.
2. **Identity and preservation.** Every variant in the baseline tables gets a
   stable identity in the receipt; every row is labeled preserved or
   isolation-improved; a blocked row ends the stage, and no row is revised
   before the trial closes.
3. **Maintenance surface.** The launcher's rules and the vendored set need no
   change when the checker changes; updating the set follows the
   [vendoring procedure](../../lib/vendor/README.md).
4. **Cost.** Stage 0 may not lengthen the case materially against the
   reference, and stage 1 should shorten it by sharing the fixture-host
   compile. The measure is the case's whole duration in its `report.json`,
   the same quantity as the reference's 74.7 s; per-test durations from the
   receipt attribute the time, they do not replace that measure.

Deferring is the outcome when stage 0 passes but stage 1 cannot start within
the planned effort; the launcher then stays behind the unchanged checker or is
removed. Rejecting reverts the stages in reverse order, as the stages section
sets out, and only then corrects the flagged expectations in `unittest` form.

## Grounding

The current boundary, from source at `3ec96c1` and unchanged at `c27e859`:
[the preflight case script](run.sh) selects the case, calls `test_begin`, one
`test_step`, then `test_check_python` in [case.sh](../../lib/case.sh), which
starts the checker with the pinned interpreter and `-B -S` and redirects both
streams to `artifacts/assertions.log`; a nonzero exit prints the log and fails
the case before any success event. [suite_run.py](../../lib/suite_run.py)
passes the inherited environment through, minus `PW_TEST_*`, and
[python_start.sh](../../lib/python_start.sh) refuses only `PYTHON*` names. The
checker imports the production helpers in-process, starts children with
`sys.executable -B -S`, and ends in `unittest.main(verbosity=2)`. The reference
run `20261027T134544Z_9ea781a5` in `tests/out/runs/pytest-baseline-reference-20261027`
(gitignored, local) passed the unchanged case at the clean commit `c700b87`
in 74.7 s with the equipment recorded in its `console.log`.

Facts about pytest, read from the revision the investigation pinned
(`41d12cdbb4a35a7877768d93d8dc50a9117a8d8c`); recheck each against the
vendored release before relying on it:

- `unittest.TestCase` subclasses are collected regardless of class name, and a
  file named on the command line is collected regardless of `python_files`
  ([unittest collection](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/unittest.py#L59-L76),
  [explicit paths](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/python.py#L215-L222)).
- `subTest` is supported natively: each variant is a report with its label
  and parameters, and a passing parent with failed subtests is marked failed
  ([addSubTest](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/unittest.py#L423-L461),
  [subtests plugin](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/subtests.py#L367-L412)).
  `setUp`, `tearDown` and `addCleanup` run inside the call phase because
  `TestCase.run` executes them; `setUpClass` becomes a class-scoped fixture.
- Exit codes: 0 passed, 1 failed in any phase, 2 interrupted (including a
  collection error), 4 usage error, 5 nothing collected
  ([ExitCode](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/config/__init__.py#L108-L130),
  [session outcome](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/main.py#L380-L392)).
- The environment is an input: `PYTEST_ADDOPTS` adds command-line arguments,
  `PYTEST_PLUGINS` imports plugins even with autoloading disabled, and
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD`, `PYTEST_DEBUG`, `PYTEST_DEBUG_TEMPROOT`,
  `PYTEST_THEME` and `PYTEST_THEME_MODE` are read; `PYTEST_CURRENT_TEST` and
  `PYTEST_VERSION` are written
  ([addopts](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/config/__init__.py#L1695-L1698),
  [plugins and autoload](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/config/__init__.py#L904-L946),
  [current test](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/runner.py#L204-L216)).
- A config path that is not a regular file means no configuration, and
  `--rootdir` fixes the root; `--noconftest` disables `conftest.py` discovery;
  `-p no:cacheprovider` prevents the cache directory under the root;
  `--collect-only` and `--setup-only` end a run without call phases
  ([config path](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/config/findpaths.py#L423-L470),
  [options](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/main.py#L150-L220),
  [cache directory](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/cacheprovider.py#L136-L142),
  [phases](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/runner.py#L123-L150)).
- The default capture is `fd`, which hides child-process output on pass
  ([capture](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/capture.py#L50-L66)).
- pytest requires Python 3.10 or later and lists 3.14; on this interpreter its
  dependencies are pluggy, iniconfig, packaging and pygments, and the terminal
  writer imports pygments at module level
  ([metadata](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/pyproject.toml#L27-L56),
  [pygments import](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/_io/terminalwriter.py#L13-L17)).

The vendoring precedent is [tests/lib/vendor](../../lib/vendor/README.md):
packages are the wheel's directory byte for byte, each wheel's `RECORD` is
kept beside them, and [markdown.py](../source_drift/markdown.py) compares every
vendored file with its `RECORD` digest and refuses imports of the vendored
packages outside their one reader. [DEPENDENCIES.md](../../../docs/DEPENDENCIES.md)
lists test equipment with its enforcement.

## Design

**Vendored set.** Vendor pytest, pluggy, iniconfig, packaging and pygments
under `tests/lib/vendor/` at exact versions from PyPI wheels whose SHA-256
matches PyPI's, keeping each `RECORD`. Candidates at the time of writing:
pytest 9.1.1, pluggy 1.7.0, iniconfig 2.3.1, packaging 26.3, pygments 2.21.0
(about 1.8 MB of wheels, pygments 1.25 MB of it). Installing into the keg's
site-packages and starting without `-S` is rejected: it changes the host's
import path and the resolver contract.

**Launcher `tests/lib/pytest_host.py`: a parent verifier and a child runner.**
The case starts the launcher through `test_check_python`, so it runs with the
pinned interpreter and `-B -S` and its streams go to `assertions.log`. The
parent imports nothing from the vendored set.

The parent, before starting anything, refuses with exit 2 and a diagnostic
any inherited variable whose name starts with `PYTEST`, as `pw_python_start`
refuses `PYTHON*`; refusal, not filtering, because the dispatcher passes the
inherited environment through. It then starts the child: the same file in
child mode under `sys.executable -B -S -P`, with
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` set explicitly, every other variable passed
through unchanged, the checkout-lock claim's descriptors passed on with
`pass_fds=checkout_lock.inherited_fds()`, and no new session or process
group. Today the checker process holds those descriptors because the case's
shell execs it; Python closes them in children by default, and the
[locking contract](../../README.md#retention-ownership-and-execution-locking)
requires a Python wrapper to pass them on, so the child holds the lock like
the checker does now and dispatcher cancellation reaches it through the
case's process group. The parent forwards nothing and swallows nothing: a
signal ends the child directly, and the parent then fails on the incomplete
receipt. The child inserts the
vendored directory at the front of `sys.path`, imports pytest, and calls
`pytest.main` with the receipt plugin and exactly these arguments: a
non-file config path and an explicit `--rootdir`; `--noconftest`;
`-p no:cacheprovider`; `--import-mode=importlib`; `--capture=no`; a
`--basetemp` under `PW_TEST_SCRATCH`; `-rA`, `-v` and `--durations=0`; and the
test file. No ini file, environment variable or conftest can add arguments.

The receipt plugin writes one JSON line per event to the path the case names
under `PW_TEST_ARTIFACTS`, flushing after each: session start with the pytest
version, its module path, the arguments and the root; the collected node ids;
the deselected count; every report with node id, phase, outcome and duration,
marked as a subtest report with its message and parameters when it is one
(the `SubtestReport` class, serialized with `_report_type` `SubTestReport`),
and as an item report otherwise; and session finish with the exit status.
A method with `subTest` blocks produces one item report per phase plus one
subtest report per block, all under the method's node id, so the two kinds
must be told apart.

The parent accepts only when all of the following hold, computed from the
receipt and the child's exit status, never from terminal text: the child
exited 0 and the finish line reports status 0; the recorded version equals the
pin and the module path lies under the vendored directory; at least one item
was collected, and the count equals the number the case passes as a
cross-check; the deselected count is 0; every collected node id has exactly
three item reports, one each for the setup, call and teardown phases, every
one with outcome passed, and no item report for any other node id; and every
subtest report has outcome passed. pytest emits the setup report for every
item, the call report only when setup passed, and the teardown report always,
so a missing phase report means the item did not complete its protocol.
Collect-only or setup-only runs, an early stop, a body calling `os._exit`, a
killed child, or a hook that suppresses reports all leave items short of
three passed reports and fail. A failed subtest fails the run whatever the
parent item's own report says, so the rule does not depend on the order in
which the subtests plugin and the receipt see the parent report. The parent
exits 1 naming the first violated rule. The rules do not depend on the test
file's contents. The collected-count cross-check, and the subtest-report
count the case may also pass, are updated with each stage; neither is proof
of preservation.

**Case script change.** The one `test_check_python` line for this case starts
the launcher with the receipt path, the expected count and the checker path
instead of the checker. Nothing else in the script, the catalog or the
dispatcher changes.

**Drift checks and documentation.** Extend the vendored-package checks to the
new wheels: every file against its `RECORD`, nothing added or missing. The
import rule has two parts: pluggy, iniconfig, packaging and pygments may be
imported only from inside the vendored directory, and pytest only by the
launcher's child mode and by the test files an explicit allowlist names, which
is the checker from stage 1 onward. The production helpers under `tests/lib`,
which the checker imports in-process, stay off that list. Add a row to
the tests table of `docs/DEPENDENCIES.md` naming the vendored set, its role,
its enforcement (the digest check and the launcher's pin check) and the
versions known to work; add the packages to the vendor README table with
version, wheel digest and license. Describe the launcher under
[shared test infrastructure](../../README.md#shared-test-infrastructure) and
note the changed invocation in [the suite README](README.md).

## Stages

**Stage 0, invocation only.** Vendor the set and its checks, write the launcher
and receipt, add the documentation, switch the one line in the case script, and
run the case into a fresh output directory. Append 68 rows to the baseline's
comparison table, one per method, labeled preserved, each naming the run path.
Record the case's whole duration from its `report.json` beside the reference's,
and the receipt's per-method call durations for `RecordTests` and the
setup-phase duration of the first `OutputTargetTests` item. Under `unittest`
the call phase holds `setUp`, the body and the cleanups together, so the
`RecordTests` figures only bound the fixture-host compile from above; stage 1
isolates it, because a module-scoped fixture's cost appears in the setup-phase
report of the first item that uses it. The difference between the case
duration and the sum of item durations is the launcher's, collection's and
pytest's own overhead. Accepted only when every criterion below holds:

- the five packages are vendored at exact versions with their `RECORD` files;
  the digest check and the two-part import rule pass with the allowlist
  holding only the launcher; the launcher refuses another version or a module
  path outside the vendored directory;
- `docs/DEPENDENCIES.md`, the vendor README and the two test documents above
  are updated;
- the environment and configuration controls pass: an inherited
  `PYTEST_ADDOPTS` or `PYTEST_PLUGINS` is refused before pytest starts; a
  `conftest.py` beside the inner file that writes a marker at import leaves
  no marker; an ini file beside the inner file requesting collection only has
  no effect;
- the execution-receipt controls pass: `--collect-only` and `--setup-only`
  given to the child, a body calling `os._exit(0)`, a child killed from inside
  a test, and an early stop after the first failure each fail the case with
  the rule named in the diagnostic; a receipt without its finish line fails;
- the reporting controls pass: a passing test; a failing body; a `TestCase`
  setup error and a fixture setup error; a teardown error after a passing
  body; a body failure plus a teardown error; an empty file and a deselect-all
  expression; a skip; a bad option; a syntax error in the inner file; each
  inner test writes a marker on body entry so nonexecution after a setup
  failure is a file observation; the outer report status, both event streams,
  the retained log, the receipt and the absence of scratch are checked for
  every control;
- the interruption control passes by the technique of
  [the cancellation controls](../dispatcher/check_cancellation.py): signal the
  dispatcher while an inner test holds a sleeping child and observe descendant
  exit through kernel exit events, never through pytest's interrupt handling;
- the lock-lifetime controls pass: an inner test finds the claim's descriptors
  open in the child and is admitted under the inherited claim, and when the
  launcher's parent is killed while an inner test sleeps, a separate open
  observes the lock held until the child exits, as `lock_free` observes it in
  the checker's own lifetime controls;
- the unchanged checker passes under the launcher with 68 collected, three
  passed item reports each, every subtest report passed, the subtest-report
  count per method compared with the baseline's variant tables as a
  cross-check, the receipt and `assertions.log` retained, and the case
  duration compared with the reference.

**Stage 1, record controls.** Compile the fixture host once as a module-scoped
fixture (the bundle builder copies the host's bytes into each app, so the
compiled host is a read-only input and each test keeps its own bundle).
Parametrize `BP62` and `BP63` with the baseline's variant labels as parameter
ids and authored expected codes, giving `BP62` a fresh record per variant,
which is the isolation improvement that resolves flag F2 and is labeled so.
Replace the ownership and temporary-directory boilerplate with a work-directory
fixture and an owned-checkout fixture that yields the scope and the claimed
environment while publication, mutation and observation stay in the test.
Keep the stamp, fresh-removal, admission and judgment sequences as single
tests with no autouse environment fixtures and no shared mutable state. From
this stage the checker imports pytest and runs only under the launcher: add it
to the import allowlist, and treat the case script's switch and the checker as
one unit. Land the stage as its own commit, separate from stage 0, so it can
be reverted on its own. Append a row per method and variant; judge criteria 1
to 4.

**Stage 2, remaining variants.** Parametrize `BP10`, `BP44`, `BP59` and the
unlabeled loops in `BP23`, `BP24`, `BP29`, `BP30`, `BP40`, `BP57` and `BP61`
so each scenario has an identity. Run the file-order and reverse-order
controls. Leave the lock lifetime and cancellation controls, the probe bounds
and the sequences in their current form; split only an inner loop where it is
cheap (`BP06`, `BP41`), and leave `BP51` as it is. Decide whether to continue
or stop.

Expected across the stages: the process and lock controls persist as sequences
with local helpers, the ownership and temporary-directory boilerplate
disappears, and scenario identity moves from assertion messages into parameter
ids.

**Reverting.** A revert undoes the stages in reverse order, each by reverting
its own commit: stage 2, then stage 1, which restores the `unittest` checker
that needs no launcher, and last stage 0, which restores the one line in the
case script and removes the launcher, the vendored set, their checks, the
allowlist and the documentation rows. Reverting stage 0 alone after stage 1
has landed is not a valid state: the checker would import pytest with no
runner. After the last revert, run the case once more into a fresh output
directory and confirm 68 methods pass under `unittest`, then append rows
naming that run as the trial's closing evidence.

## Verification and completion

The synthetic controls run through the public command in fixture
repositories, as [the dispatcher controls](../dispatcher/check.py) do with
[repository.py](../../fixtures/dispatcher/repository.py), extended to copy the
launcher and the vendored set. Register them as a default case with their
actual requirements, following [the test rules](../../AGENTS.md#add-or-change-tests):
catalog entry, owning suite README, suite map and outcome coverage. A control
passes only on the outer evidence named above; inner totals alone establish
nothing.

Each stage runs the case into a fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>`
with `PYTHONOPTIMIZE` unset, through `tests/run.sh --case preflight/build_provenance_controls`,
and runs the control case and the source-drift suite. Comparison rows cite
those run paths. Method, variant and parameter counts are cross-checks, not
proof of preservation, unconditional collection, absence of skips or
isolation.

Effort, assuming an implementer who knows the dispatcher and basic pytest,
vendoring by the existing precedent, and no CI:

| Stage | Mechanical | Judgment | Verification |
| --- | --- | --- | --- |
| 0 invocation only | 1.5 to 2.5 days | 0.5 to 1 day | 1.5 to 2.5 days |
| 1 record controls | 1 to 2 days | 0.5 to 1 day | 0.5 day |
| 2 remaining variants | 1 to 2 days | 0.5 day | 0.5 to 1 day |

The plan is complete when a stage ends with an explicit keep, defer or revert
decision recorded against the criteria, the baseline's rows and flags are
updated with the commits that corrected them, and the baseline is archived
under `records/archive/tests/` with the investigation plan's closure.

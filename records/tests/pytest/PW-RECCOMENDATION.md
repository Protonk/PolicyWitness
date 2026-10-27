# Recommendation: subordinate pytest integration for build_provenance_controls

The assessment returned for
[the investigation plan](../../../tests/suites/preflight/PW-PYTEST-INTEGRATION-INVESTIGATION-PLAN.md),
revised after the review of `01d5db9`. Its evidence:

- The baseline record
  [PW-PYTEST-BASELINE-3ec96c1.md](PW-PYTEST-BASELINE-3ec96c1.md): the source
  snapshot at `3ec96c1`, with variant tables for BP62, BP63 and BP44.
- The execution reference, run `20261027T134544Z_9ea781a5` in
  `tests/out/runs/pytest-baseline-reference-20261027`, made at the clean commit
  `c700b87` with its equipment recorded in the run's `console.log`. The run
  directory is gitignored and available only in this checkout.
- The document drift checks, which passed in that run and in
  `tests/out/runs/pytest-baseline-drift-20261026` against the plan edits.
- The plan's links to both records, committed in `c700b87`.

External findings are source-derived at the revisions the plan pins. No pytest
prototype was run.

## Recommendation and decision criteria

**Proceed to a bounded trial** of two stages: an invocation-only transition,
then a file-local refactor of the record controls. The plan's criterion for
the proposal is net benefit: less infrastructure that needs PolicyWitness-
specific knowledge, and clearer remaining special cases. Feasibility of the
boundary is a precondition, not the decision. The trial therefore ends in one
of three outcomes against explicit criteria, judged at the end of each stage
from the comparison rows and the run evidence:

1. **Net machinery.** Count the PolicyWitness-specific lines the trial adds
   that the checker's maintainers must understand (the launcher, its
   acceptance rules, the receipt plugin, the vendored-package checks, the
   drift allowlist and the documentation) and the organizational lines it
   removes from the checker (ownership and temporary-directory boilerplate,
   hand-written scenario loops, restoration code). The one-time verification
   controls are counted separately and must not grow when the checker changes.
   Stage 1 must remove at least as much as stage 0 added outside those
   controls. If it cannot, reject: revert the one-line switch and delete the
   launcher and the vendored set.
2. **Identity and preservation.** Every variant in the baseline tables gets a
   stable identity in the receipt, every baseline row is labeled preserved or
   isolation-improved, and no row is blocked. A blocked row ends the stage.
3. **Maintenance surface.** The launcher's acceptance rules and the vendored
   set need no change when the checker changes, and updating the vendored set
   follows the existing `tomli` procedure: replace from a wheel whose digest
   matches PyPI, record version and digest, rerun the checks.
4. **Cost.** Stage 0 may not lengthen the case materially against the
   reference duration of 74.7 s; stage 1 should shorten it by sharing the
   fixture-host compile. Both are measured with per-test durations in the
   receipt.

Deferring is the right outcome if stage 0 passes but stage 1 cannot start
within the planned effort; the launcher then stays as an optional path behind
the unchanged checker, or is removed. Retaining the current arrangement is the
default if criterion 1 fails. The flagged expectations F1 to F4 are corrected
in `unittest` form in that case.

## What the record establishes

| Quantity | Count |
| --- | --- |
| Test classes | 17, one a fixture base with no tests |
| Test methods | 68 |
| `subTest` sites | 35 |
| Labeled variants, counted from source | about 350 |
| Variants enumerated one by one in the record | 78 across BP62, BP63 and BP44, plus 21 BP63 section faults by formula |
| Methods with unlabeled scenario loops | 15 |
| Methods retaining artifacts | 10 |
| Flagged expectations | 9 |

The flags, in short: a tautological assertion in BP34; the record-fault loop in
BP62 regenerates the record inside the `subTest` block, so one failure can
alter later variants; a duplicated `subTest` label in BP20; BP62 accepts either
of two codes where the suite README says both; elapsed-time bounds in BP02,
BP32 and BP33; nine loops without per-scenario identity; an assumption about
closed descriptors in BP06; expectations bound to this machine's keg, Xcode and
SDK; and BP67's dependence on an opt-in module outside the suite. None was
reproduced as a failure.

The execution reference ran the unchanged case at `c700b87`, whose traced
dependencies are byte-identical to `3ec96c1`. It passed in 74.7 s, its log
lists the 68 inventory names, and the equipment is recorded. The earlier
battery run of 2026-10-24 is kept in the record as illustrative only, because
its receipts cannot establish the executed source.

## Integration arrangement

**Interpreter and dependencies.** The checker's interpreter and flags stay
unchanged. A launcher, `tests/lib/pytest_host.py`, is started by the case's
existing Python helper exactly as the checker is today. The pinned pytest
requires Python 3.10 or later and lists 3.14; its runtime dependencies on this
interpreter are pluggy, iniconfig, packaging and pygments, and the terminal
writer imports pygments at module level, so none can be dropped. The set is
vendored under `tests/lib/vendor` by the existing precedent, at exact versions
with each wheel's RECORD kept beside the package.

| Package | Current wheel size |
| --- | --- |
| pytest 9.1.1 | 387 KB |
| pluggy 1.7.0 | 27 KB |
| iniconfig 2.3.1 | 8 KB |
| packaging 26.3 | 130 KB |
| pygments 2.21.0 | 1.25 MB |

Installing into the keg's site-packages and starting without `-S` is not
recommended: it changes the host's import path and contradicts the resolver
contract that helpers see only the interpreter and the tree.

**Launcher: a parent verifier and a child runner.** The launcher runs pytest in
a child process it starts itself and judges the child from a receipt file, so
a child that exits early, is killed, or never runs a body cannot report
success. The design follows Zephyr's outer-runner translation; the rules below
are grounded in the pinned source.

The parent, before starting anything:

- Refuses any inherited variable whose name starts with `PYTEST`, with exit 2
  and a diagnostic, as `pw_python_start` refuses `PYTHON*`. The pinned source
  reads `PYTEST_ADDOPTS` as extra command-line arguments, which could inject
  `--collect-only`; `PYTEST_PLUGINS` as plugin modules to import even with
  autoloading disabled; `PYTEST_DISABLE_PLUGIN_AUTOLOAD`, `PYTEST_DEBUG`,
  `PYTEST_DEBUG_TEMPROOT`, `PYTEST_THEME` and `PYTEST_THEME_MODE`; and it
  writes `PYTEST_CURRENT_TEST` and `PYTEST_VERSION`. The dispatcher passes the
  inherited environment through, so refusal is the only control that keeps
  these out.
- Starts the child with the pinned interpreter and `-B -S -P`, the vendored
  path inserted by the child's own startup, and
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` set explicitly even though no entry
  points exist under `-S`.
- Passes every pytest argument itself: a non-file config path, which the pinned
  source treats as no configuration, with an explicit root directory;
  `--noconftest`, so no `conftest.py` is discovered; `-p no:cacheprovider`;
  `--import-mode=importlib`; `--capture=no`; a base temp directory under the
  case scratch path; `-rA`, `-v` and `--durations=0`; and the checker path.
  No ini file, environment variable or conftest can add arguments.

The child's receipt plugin writes one JSON line per event with a flush after
each: session start with the pytest version, module path, arguments and root;
the collected node ids; the deselected count; every report with node id,
phase, outcome, duration and the subtest context when present; and session
finish with the exit status.

The parent accepts only when all of the following hold, computed from the
receipt and the child's exit status, never from terminal text:

- the child exited 0 and the session-finish line reports status 0;
- the recorded pytest version equals the pin and the module path lies under
  the vendored directory;
- at least one item was collected, and the collected count equals the number
  the case passes as a cross-check when it passes one;
- the deselected count is 0;
- every collected node id has exactly one call-phase report with outcome
  passed, no setup- or teardown-phase report failed or skipped, and no subtest
  report failed or skipped.

A collect-only or setup-only run, an early stop after a failure, a test that
calls `os._exit`, a killed child, or a hook that suppresses reports all leave
items without call reports and fail. The parent exits 1 naming the first
violated rule. These rules do not depend on the checker's contents.

**Facts about running the unchanged file.** `TestCase` subclasses are
collected regardless of class name; an explicitly named file is collected
regardless of the file pattern; `subTest` is supported natively with
per-variant reports and the parent marked failed; class setup becomes a class
fixture; the exit codes are 0, 1, 2, 4 and 5. Differences to record in the
trial: classes run in file order instead of alphabetical order, `setUp`
failures appear in the call phase because `TestCase.run` executes them, fault,
unraisable and thread hooks are installed, and `PYTEST_CURRENT_TEST` is set in
the host environment during each phase. Every byte-exact environment
comparison in the checker starts from an empty or constructed environment, so
the source predicts no effect from that variable; the trial confirms it.

## External patterns and refactor targets

Zephyr's explicit translation under outer authority is the launcher and
receipt; no JUnit is needed, and the exit-based case contract is kept. The
MCUboot prepared-resource shape becomes an owned-checkout fixture replacing the
ownership and temporary-directory boilerplate in nine methods across six
classes, with publication, mutation and observation left in the test.
meson-python supports keeping the stamp, fresh-removal, admission and judgment
sequences as single tests, with no autouse environment fixtures and no shared
mutable state. PyPA build's independent malformed inputs fit parametrization
of BP63, BP62, BP10, BP44 and BP59, and of the unlabeled loops in BP23, BP24,
BP29, BP30, BP40, BP57 and BP61, which would give each scenario an identity.
For BP62, a fresh record per variant is the isolation improvement that resolves
the restoration flag. pytest's own runner tests supply the synthetic-suite
technique for the verification below.

The fixture host compiled per `RecordTests` method is a read-only input: the
bundle builder copies its bytes into each app. A module-scoped host fixture
with per-test bundles is therefore a safe sharing boundary. Its per-method
cost is unmeasured and is the first unresolved question for the trial.

Unpromising targets are the lock lifetime and cancellation controls, the probe
bounds, and the stateful sequences; they keep their local process helpers and
sequence form. Remaining variants are BP51, which combines a `subTest` with an
expected exception, and the loops inside the sequences of BP06 and BP41; split
only the inner loop where it is cheap.

## Trial stages and Stage 0 acceptance criteria

**Stage 0, invocation only.** Vendor the set, add the launcher and receipt,
switch the one helper line in the preflight case script to start the launcher
with the unchanged checker, and append 68 preserved rows with the run path.
Stage 0 is accepted only when every criterion below holds:

- **Enforced exact versions.** pytest, pluggy, iniconfig, packaging and
  pygments are vendored at exact versions with each wheel's RECORD beside the
  package; the drift suite compares every vendored file with its RECORD digest
  and refuses an import of any of them outside the launcher, as it does for
  the Markdown reader's packages; the launcher refuses a recorded pytest
  version other than its pin or a module path outside the vendored directory.
- **Documentation.** `docs/DEPENDENCIES.md` gains a row in its tests table
  naming the vendored set, its role, the enforcement above and the versions
  known to work, and `tests/lib/vendor/README.md` lists each package with its
  version, source wheel digest and license.
- **Environment and configuration controls pass** through the public command
  in fixture repositories: an inherited `PYTEST_ADDOPTS` or `PYTEST_PLUGINS`
  is refused before pytest starts; a `conftest.py` beside the inner file that
  writes a marker at import leaves no marker; an ini file beside the inner
  file requesting collection only has no effect.
- **Execution-receipt controls pass:** `--collect-only` and `--setup-only`
  given to the child, a body calling `os._exit(0)`, a child killed from inside
  a test, and an early stop after the first failure each fail the case with
  the rule named in the launcher's diagnostic; a receipt missing its
  session-finish line fails.
- **Reporting controls pass:** a passing test; a failing body; a `TestCase`
  setup error and a pytest fixture setup error; a teardown error after a
  passing body; a body failure plus a teardown error; an empty file and a
  deselect-all expression; a skip; a bad option; a syntax error in the inner
  file. Each inner test writes a marker on body entry so nonexecution after a
  setup failure is a file observation. The outer report status, both event
  streams, the retained log, the receipt and the absence of scratch are
  checked for every control.
- **Interruption control passes** by the existing cancellation technique:
  signal the dispatcher while an inner test holds a sleeping child and observe
  descendant exit through kernel exit events, not through pytest's interrupt
  handling.
- **The unchanged checker passes under the launcher:** 68 collected, 68 call
  reports passed, no skips, the receipt and `assertions.log` retained, the
  case duration compared with the reference, and no change to the dispatcher
  or catalog beyond the one-line case script switch.

**Stage 1, record controls.** A module-scoped fixture-host compile, parametrized
BP62 and BP63 with the variant labels as parameter ids, the BP62 change labeled
isolation-improved, and the work-directory and owned-checkout fixtures.
Judged by criteria 1 to 4 above.

**Stage 2, remaining variants.** Parametrize BP10, BP44, BP59 and the unlabeled
loops, run the file-order and reverse-order controls, and decide whether to
continue.

Across the stages, the process and lock controls should persist as sequences
with local helpers, the ownership and temporary-directory boilerplate should
disappear, and scenario identity should move from assertion messages into
parameter ids.

## Effort

Assumptions: an implementer who knows the dispatcher and basic pytest,
vendoring by the existing precedent, no CI.

| Stage | Mechanical | Judgment | Verification |
| --- | --- | --- | --- |
| 0 invocation only | 1.5 to 2.5 days | 0.5 to 1 day | 1.5 to 2.5 days |
| 1 record controls | 1 to 2 days | 0.5 to 1 day | 0.5 day |
| 2 remaining variants | 1 to 2 days | 0.5 day | 0.5 to 1 day |

Stage 0 grew by about a day against the first estimate for the parent
verifier, the environment refusal and the added controls.

## Smallest productive first step

Vendor the five packages with digests and the drift check, write the launcher
with its environment refusal, child runner and receipt verifier, add the
dependency documentation, switch the one line in the preflight case script,
and run the case into a fresh output directory:

```sh
PW_TEST_OUT_DIR=tests/out/runs/pytest-stage0-01 tests/run.sh --case preflight/build_provenance_controls
```

If the comparison against the record fails, revert the one line.

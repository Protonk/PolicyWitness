Investigation complete. The baseline record is written at `records/tests/pytest/PW-PYTEST-BASELINE-3ec96c1.md`, the plan links to it, and the `source_drift` suite passed against the plan edit in `tests/out/runs/pytest-baseline-drift-20261026`. Nothing is committed. The working tree holds the modified plan and the new record.

**Recommendation: proceed to a bounded trial.** Stage it as an invocation-only transition first, then one file-local refactor of the record controls. Retaining the current arrangement costs nothing today, but it keeps nine scenario loops that cannot name a failing scenario and one restoration risk inside a `subTest` loop. Rejecting would need evidence that a pytest host cannot sit under the dispatcher without changing tested inputs, and the pinned pytest source shows the boundary can be kept. The invocation-only stage is a one-line switch in the case script and is reversible.

## What the record establishes

The record is a source snapshot at `3ec96c1` with a clean tree. Its inventory gives every method a stable identifier from BP01 to BP68 and names each labeled variant.

| Quantity                              | Count                                |
| ------------------------------------- | ------------------------------------ |
| Test classes                          | 17, one a fixture base with no tests |
| Test methods                          | 68                                   |
| `subTest` sites                       | 35                                   |
| Labeled variants, counted from source | about 350                            |
| Methods with unlabeled scenario loops | 15                                   |
| Methods retaining artifacts           | 10                                   |
| Flagged expectations                  | 9                                    |

The flags, in short: a tautological assertion in BP34; the record-fault loop in BP62 restores the record inside the `subTest` block, so one failure can alter later variants; a duplicated `subTest` label in BP20; BP62 accepts either of two codes where the suite README says both; elapsed-time bounds in BP02, BP32 and BP33; nine loops without per-scenario identity; an assumption about closed descriptors in BP06; expectations bound to this machine's keg, Xcode and SDK; and BP67's dependence on an opt-in module outside the suite. None was reproduced as a failure.

**Execution reference.** Run `unify-review-final-20261024` is applicable. The case passed on the pinned interpreter at version 3.14.9, the retained log lists 68 names identical to the inventory, and the evidence is one log plus ten artifact directories. Mechanically checked: no traced dependency changed between the bracketing commit and HEAD except the catalog, where only two other cases' descriptions moved, and the opt-in `build_refusals.py` module. That module's delta adds one function and one sequence entry, and the three names BP67 reads are untouched, so the record keeps its result as a reviewed exception. Two judgments remain stated as such: the tree at run time is assumed equal to the bracketing commit, and equipment versions were not recorded. No fresh run was needed.

## Proposed arrangement and patterns

**Interpreter and dependencies.** Keep the checker's interpreter and flags unchanged. Add a PolicyWitness launcher, `tests/lib/pytest_host.py`, started by the case's existing Python helper exactly as the checker is today. It inserts a vendored pytest set into the import path and calls pytest in-process with a receipt plugin. Vendoring follows the existing `tests/lib/vendor` precedent with RECORD digests and the drift suite's import-site allowlist. The pinned pytest requires Python 3.10 or later and lists 3.14. Its runtime dependencies on this interpreter are four packages, and the terminal writer imports pygments at module level, so none can be dropped.

| Package         | Current wheel size |
| --------------- | ------------------ |
| pytest 9.1.1    | 387 KB             |
| pluggy 1.7.0    | 27 KB              |
| iniconfig 2.3.1 | 8 KB               |
| packaging 26.3  | 130 KB             |
| pygments 2.21.0 | 1.25 MB            |

Installing into the keg's site-packages and starting the host without `-S` is not recommended. It changes the host's import path and contradicts the resolver contract that helpers see only the interpreter and the tree.

**Launcher settings, each grounded in the pinned source.**

- A non-file config path means no configuration, and an explicit root directory stops the ancestor walk. No config file exists in any ancestor today.
- The cache plugin must be disabled, or it writes a cache directory under the root.
- Import mode `importlib` leaves the import path alone; the checker inserts its own entries.
- Capture must be off, or child-process output the reference log retains is hidden on pass.
- Plugin autoloading is disabled explicitly, although no entry points exist under `-S`.
- Any base temp directory belongs under the case scratch path. The current file uses `/private/tmp` directly.
- The receipt plugin writes one JSON line per report, including subtest reports. The launcher exits nonzero on any nonzero pytest status, on any skipped item, and when the collected count differs from the expected count. That settles the skip and no-test policy as failure.
- pytest sets `PYTEST_CURRENT_TEST` in the host environment during each phase. Every byte-exact comparison in the checker starts from an empty or constructed environment, and the resolver refuses only `PYTHON*` names, so the source predicts no effect. The trial confirms it.

The unchanged file runs under pytest at the pin. `TestCase` subclasses are collected regardless of class name, an explicitly named file is collected regardless of the file pattern, `subTest` is supported natively with per-variant reports and the parent marked failed, class setup becomes a class fixture, and the exit codes are 0, 1, 2, 4 and 5. Differences to record in the trial: classes run in file order instead of alphabetical order, `setUp` failures appear in the call phase because `TestCase.run` executes them, and fault, unraisable and thread hooks are installed.

**Patterns and targets.** Zephyr's explicit translation under outer authority becomes the launcher and receipt, with no JUnit and the exit-based case contract kept. The MCUboot prepared-resource shape becomes an owned-checkout fixture replacing the ownership and temporary-directory boilerplate in nine methods across six classes, with publication, mutation and observation left in the test. meson-python supports keeping the stamp, fresh-removal, admission and judgment sequences as single tests, with no autouse environment fixtures and no shared mutable state. PyPA build's independent malformed inputs fit parametrization of BP63, BP62, BP10, BP44 and BP59, and of the unlabeled loops in BP23, BP24, BP29, BP30, BP40, BP57 and BP61, which would give each scenario an identity. For BP62, a fresh record per variant is the isolation improvement that resolves the restoration flag.

The fixture host compiled per `RecordTests` method is a read-only input: the bundle builder copies its bytes into each app. A module-scoped host fixture with per-test bundles is therefore a safe sharing boundary. Its per-method cost is unmeasured and is the first unresolved question for the trial.

Unpromising targets are the lock lifetime and cancellation controls, the probe bounds, and the stateful sequences. They keep their local process helpers and sequence form. Remaining variants are BP51, which combines a `subTest` with an expected exception, and the loops inside the sequences of BP06 and BP41; split only the inner loop where it is cheap.

## Trial, verification and effort

**Stages.** Stage 0 vendors pytest, adds the launcher and receipt, and switches the one helper line in the preflight case script to start the launcher with the unchanged checker; it appends 68 preserved rows with the run path. Stage 1 refactors `RecordTests` with the shared host fixture and parametrized faults, adds the work-directory and owned-checkout fixtures, and labels the BP62 change as isolation-improved. Stage 2 parametrizes BP10, BP44, BP59 and the unlabeled loops, runs an order control, and decides whether to continue.

**Verification.** Build synthetic inner suites in fixture repositories, as the dispatcher controls already do, and run them through the public command with the launcher. Cases: a passing test; a failing body; a `TestCase` setup error and a pytest fixture setup error; a teardown error after a passing body, which must fail the case; a body failure plus a teardown error with fail-fast, both visible in the receipt; an empty file and a deselect-all expression, both exit 5 and fail; a skip, which fails by policy; a bad option and a syntax error in the inner file. Each inner test writes a marker on body entry so nonexecution after setup failure is a file observation. Check the outer report status, both event streams, the retained log, the receipt and the absence of scratch. For interruption, follow the existing cancellation controls: signal the dispatcher while an inner test holds a sleeping child and observe descendant exit through kernel exit events, not through pytest's interrupt handling. Retain inner sources, launcher streams, receipts and markers; keep base temp and intermediates in scratch. Compare every stage row by row against the record; counts remain cross-checks.

**Effort**, assuming an implementer who knows the dispatcher and basic pytest, vendoring by the existing precedent, and no CI.

| Stage                | Mechanical  | Judgment     | Verification |
| -------------------- | ----------- | ------------ | ------------ |
| 0 invocation only    | 1 to 2 days | 0.5 to 1 day | 1 to 2 days  |
| 1 record controls    | 1 to 2 days | 0.5 to 1 day | 0.5 day      |
| 2 remaining variants | 1 to 2 days | 0.5 day      | 0.5 to 1 day |

Across the stages, the process and lock controls should persist as sequences with local helpers, the ownership and temporary-directory boilerplate should disappear, and scenario identity should move from assertion messages into parameter ids.

**Smallest productive first step.** Vendor the five packages with digests, extend the drift allowlist, write the launcher with its receipt plugin, switch the one line in the preflight case script, and run the case into a fresh output directory:

```sh
PW_TEST_OUT_DIR=tests/out/runs/pytest-stage0-01 tests/run.sh --case preflight/build_provenance_controls
```

If the comparison against the record fails, revert the one line.

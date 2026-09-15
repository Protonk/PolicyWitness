# Testing audit — measure detection of six harness regressions

## Task and required output

Measure which existing controls detect six specified regressions in the test
command. Complete the matrix even if every fault is detected. This is a bounded
measurement task; do not expand it into an open-ended review or implement fixes.

**Write your full results in this file, `tests/TESTING-AUDIT.md`, under
`Audit results`. Preserve this prompt.** Include baseline results, the six-row
matrix, activation evidence, commands, detecting controls and diagnostics,
limitations, and a short conclusion. Your final chat reply should briefly report
completion or blockage and link to this document.

Create all other files under
`tests/out/testing-audit/flag-detection/<your-run-id>/`: disposable source copies,
mutation patches, probe scripts, receipts, raw stdout/stderr, exit metadata, and
a machine-readable `matrix.json`. Link to evidence from each matrix row.
Do not create a permanent mutation framework.

The implementation to measure is commit `eb135ac`, following the runner-staging
fix in `56d7a3d`. Record actual HEAD and working-tree differences before starting.
Use the current checkout as the source and explain relevant differences.
Do not reset it. The prior audit and results are preserved in Git.

## Starting points

Read `tests/README.md` and `tests/suites/dispatcher/README.md`, then inspect:

- `tests/run.sh`, `tests/catalog.json`, `tests/lib/test_cli.py`
- `tests/lib/suite_run.py`
- `tests/suites/dispatcher/check_selection.py`
- `tests/suites/dispatcher/check.py` and `check_accounting.py`
- `tests/fixtures/dispatcher/repository.py`, `selection.sh`, and `selection.py`

Public-command controls use independent fixture catalogs and execution receipts.
Reconciliation controls exercise reports, events, and process failures. Accounting
controls also supply handoff records directly to accounting/finalization. Identify
which observation point detects each fault.

## Work boundary and effort

- Change only this audit document in the original source/documentation tree.
  Mutations are authorized **only in physical copies** under your run directory.
  Do not use hardlinks or symlinks back to mutable original files. Copy needed
  test machinery, scripts, fixtures, and catalog; exclude `tests/out`, `.git`,
  app bundles, and build caches.
- Keep existing checkers, fixtures, expected values, and catalogs unchanged in
  every subject copy. Apply one logical behavior fault per copy, confined to
  `tests/lib/test_cli.py` or `tests/lib/suite_run.py`. Do not combine faults or
  disable unrelated defenses to obtain a green result.
- Establish clean baselines for both drivers below. Then use at most two
  applicable driver invocations per mutant. Allow at most one correction if a
  patch is invalid or fails to activate. Record unresolved rows and move on;
  do not search for additional mutations.
- Everything here can run offline. Do not rebuild the app, run the full suite,
  invoke live PW/XPC/signing/launchd operations, or change privacy settings.
- Give every invocation fresh output. Keep auditor-owned observations outside
  each disposable subject's `tests/out`: the destructive-list mutant may erase
  that directory. Preserve all earlier evidence.
- Retain before/after hashes of original subject files and copied checkers and
  fixtures, plus mutation patches, proving that the original implementation and
  test oracles were unchanged.

## Run unchanged observers outside the mutated dispatcher

Do not use the mutated public dispatcher to select its own audit controls:
a selection fault could otherwise suppress its own detector.

Run these unchanged Python drivers directly from the appropriate physical copy,
with assertions enabled and bytecode writing disabled:

```sh
/usr/bin/python3 -B <copy>/tests/suites/dispatcher/check_selection.py <fresh-results-dir>
/usr/bin/python3 -B <copy>/tests/suites/dispatcher/check.py <fresh-results-dir>
```

Unset `PYTHONOPTIMIZE` and external `PW_*` settings for these invocations.
`check.py` includes the accounting controls. The drivers locate subject
equipment relative to their copied source root; verify that mutations reach
the fixture repositories they execute. Do not accidentally test the original
checkout or an unmodified nested copy.

First retain passing runs of both drivers against an unmodified copy. For each
mutant, run the applicable unchanged driver; use the second only for a distinct
observation. The first meaningful failing control is enough. Do not edit drivers
to continue past assertions or seek every possible detector.

## Six faults, in three pairs

These are behavioral targets. Choose small, generic patches; do not branch on
fixture case names, audit environment variables, or expected results.

| ID | Area | Injected behavior | Likely observer |
| --- | --- | --- | --- |
| S1 | Selection | Omit an explicitly requested case during selection, so a multi-case request loses work. Retain enough work for the subject to execute. | `check_selection.py` |
| S2 | Selection | Execute the same canonical case twice when a suite selector and a case selector overlap. Show two actual executions, not merely a duplicated display entry. | `check_selection.py` |
| C1 | Configuration | Ignore a valid `PW_APP_DIR` override and resolve the default bundle instead. Demonstrate two distinguishable bundle paths. | `check_selection.py` |
| C2 | Inspection | Let `--list` initialize or replace output, altering seeded prior evidence even though no test execution was requested. | `check_selection.py` |
| A1 | Accounting | Stop treating a nonzero child exit as a harness failure. Use a child that emits otherwise valid passing evidence before exiting nonzero, so a missing or failed report does not independently explain rejection. | `check.py` |
| A2 | Accounting | Drop one selected case from `case_results` after execution/accounting, leaving otherwise passing evidence. Keep the independent final-summary guard intact and measure whether it prevents success. | `check.py` and/or `check_selection.py` |

These describe fault injections, not assertions that the current code contains
these bugs. A2 intentionally measures whether a second defense contains an error
introduced into an earlier layer.

## Establish activation separately from detection

For each row, retain an observation demonstrating the intended behavior changed
relative to the clean copy. Existing fixture receipts may suffice. If necessary,
write a separate activation probe with its own tiny catalog, command, and literal
expectations under the run directory. Do not change existing oracles or count a
new probe as an existing test that detected the mutation.

Use observations suited to the fault:

- Selection: literal requested IDs versus independently recorded executions.
  A planner agreeing with its own modified plan is insufficient.
- Configuration: named bundle versus effective configuration or execution path;
  identify whether execution was blocked before launch.
- Inspection: before/after bytes, existence, and mtimes of seeded evidence.
- Accounting: child exit/receipts and evidence versus case identities, completion
  counts, diagnostics, and final success status.

Syntax/import errors, patches that never run, and unrelated equipment failures
are not detected behavioral regressions. If another harness guard contains an
activated fault, retain that diagnostic and distinguish the containment from
the checker assertion observing it. Do not remove the guard.

## Required results

Report one row per fault, using these classifications:

- **Detected:** activation is demonstrated and an unchanged existing control
  rejects the resulting behavior for a relevant reason. Name the first detector,
  its assertion/diagnostic, and any earlier harness guard.
- **Survived:** activation is demonstrated and the applicable unchanged controls
  complete successfully. State exactly which controls ran; this is a bounded
  coverage gap, not proof the entire suite would miss it.
- **Invalid/inactive:** the patch is broken or the intended behavior was not
  reached. Exclude it from any detection-rate denominator.
- **Blocked:** measurement could not be completed within the boundary. Explain
  the specific limitation and retain partial evidence.

The Markdown table and `matrix.json` must identify the fault, patch path, clean
and mutated activation observations, commands, exit statuses, classification,
first relevant detector, containment layer if any, and evidence paths. Put longer
explanations below the table. Report baseline status and valid-mutant totals
separately; six rows is a workload limit, not a comprehensive coverage score.

Conclude with which behaviors have demonstrated regression protection, which
activated faults escaped the sampled controls, and which rows remain unmeasured.
For survivors, propose only the smallest useful contract addition. Do not
implement it.

## Audit results

Run ID `20260915-det01`. Everything except this document is under
`tests/out/testing-audit/flag-detection/20260915-det01/` (28 MB, untracked),
including seven physical source copies, six patches, activation probes, driver
receipts and `matrix.json`.

**Six faults injected, six valid mutants, six detected, zero survivors, zero
blocked.** Both baselines pass. No permanent mutation framework was created: the
three helper scripts (`build_subjects.py`, `probe.py`/`run_probes.py`,
`drive.py`) live only in the run directory.

### Reviewed state and working-tree differences

- Actual HEAD is `eb135ac` ("Enforce coherent test bundles and complete
  selection accounting"), the commit named for measurement, following
  `56d7a3d`. Recorded in `inputs/head.txt`.
- The only working-tree difference is ` M tests/TESTING-AUDIT.md` — this
  document, carrying the new prompt. `git diff eb135ac -- . ':!tests/TESTING-AUDIT.md'`
  is empty (`inputs/worktree-diff-excluding-audit-doc.txt`), so the implementation
  measured is exactly `eb135ac`. The checkout was not reset.
- `56d7a3d..eb135ac` (`inputs/diff-56d7a3d-eb135ac.txt`) is the change under
  measurement: it closed the two findings of the previous audit — the split
  bundle (`test_cli.py:117-138`, "controller must resolve inside the selected app
  bundle") and the shared report path (`test_cli.py:42-47` catalog rejection,
  `suite_run.py:205-218` `ambiguous_case_path`, `suite_run.py:137-150`
  `incomplete_accounting`) — renamed `plan.suites` to `containing_suites`, and
  added `check_accounting.py` plus 20 further `check_selection.py` controls. That
  matters here because three of the six faults (S2, A2, and the blocked half of
  C1) are contained by guards introduced in that commit.

### Baselines

| Driver | Command | Exit | Controls passed | Time | Evidence |
| --- | --- | --- | --- | --- | --- |
| `check_selection.py` | `/usr/bin/python3 -B subjects/clean/tests/suites/dispatcher/check_selection.py <fresh>` | 0 | 87 | 11.4 s | `baseline/clean/check_selection/` |
| `check.py` (incl. `check_accounting`) | `/usr/bin/python3 -B subjects/clean/tests/suites/dispatcher/check.py <fresh>` | 0 | 37 | 15.1 s | `baseline/clean/check/` |

Both were run from the unmodified copy `subjects/clean`, with `PYTHONOPTIMIZE`
and all external `PW_*` settings removed, `PYTHONDONTWRITEBYTECODE=1`, `cwd=/`,
and a fresh results directory. `subjects/clean` is byte-identical to the
checkout (`inputs/mutation-reach.json`).

### Matrix

| ID | Area | Patch | Clean activation observation | Mutated activation observation | Driver command | Exit | Class | First detector / diagnostic | Containment layer | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | Selection | [`patches/S1.diff`] `test_cli.py` `select()`, +2 lines | `--case p/first --case p/second` → receipts `[p/first, p/second]`, `completion {selected 2, completed 2}` | receipts `[p/first]`, `completion {selected 1, completed 1}`, `ok true`, exit 0 | `check_selection.py` | 1 | **Detected** | control `default`: `require([r['id'] for r in records] == list(expected))` → `default: wrong execution receipts: [{'id': 'probe/first', …}]` | none — the plan is truncated with the selection, so `finish()` sees `selected == accounted` and the run self-reports `ok: true` | `probes/S1/`, `runs/S1/check_selection/` |
| S2 | Selection | [`patches/S2.diff`] `test_cli.py` `select()`, +2 lines | `--suite p --case p/first` → 2 executions, pids `[56927, 56929]` | 3 executions `[p/first, p/second, p/first]`, pids `[56936, 56938, 56940]` — three distinct child processes | `check_selection.py` | 1 | **Detected** | control `deduplicate`: `require(result.returncode == code)` → `deduplicate: exit 1, expected 0` | `reused_case` + `incomplete_accounting` (`duplicate_cases`) failed the run first | `probes/S2/`, `runs/S2/check_selection/` |
| C1 | Configuration | [`patches/C1.diff`] `test_cli.py` `resolve_config()`, 1 line | `PW_APP_DIR={repo}/Named.app` → `configuration.app_dir` and the receipt's `PW_APP_DIR` both `…/repo/Named.app` | both `…/repo/dist/PolicyWitness.app`; with `requires: ['app']` the case is **blocked before launch** (0 executions) | `check_selection.py` | 1 | **Detected** | control `all`: `require(result.returncode == code)` → `all: exit 1, expected 0` | `requirements()` blocked `equipment/app`: `not_run: missing prerequisites: ['app']` + `unrun_case` | `probes/C1/`, `runs/C1/check_selection/` |
| C2 | Inspection | [`patches/C2.diff`] `test_cli.py` `main()`, 6 lines (reordered) | `--list` → all three seeded files byte- and mtime-identical | `--list` removed all three (`keep.bin`, `run.json`, `suites/prior/case/report.json`); exit still 0 | `check_selection.py` | 1 | **Detected** | control `list_11`: `require(snapshot(repo) == before)` → `list_11: inspection/invalid command changed files` | none — `--list` exits 0 after destroying the seeded evidence | `probes/C2/`, `runs/C2/check_selection/` |
| A1 | Accounting | [`patches/A1.diff`] `suite_run.py` `execute()`, −2 lines | child writes a passing report then exits 19 → `ok false`, exit 1, `harness_errors ['suite_exit']` | identical report, identical child rc 19 → `ok true`, exit 0, `harness_errors []` | `check.py` | 1 | **Detected** | control `crash`: `assert set(codes) <= actual_codes` (`check.py:100`) → `('crash', ('suite_exit', 'empty_suite'), [empty_suite, unrun_case])` | scenario-local only (see below) | `probes/A1/`, `runs/A1/check/` |
| A2 | Accounting | [`patches/A2.diff`] `suite_run.py` `finish()`, +2 lines | two passing cases → 2 `case_results`, `completion {selected 2, completed 2}`, exit 0 | 1 `case_results` entry, `completion {selected 2, completed 1}`, `ok false`, exit 1 | `check.py`, then `check_selection.py` | 1, 1 | **Detected** | control `pass_and_skip`: `assert result.returncode == (0 if expected_ok else 1)` (`check.py:92`) → `('pass_and_skip', 1, b'HARNESS: [dispatcher] incomplete_accounting: …')` | **`incomplete_accounting` in `finish()` refused a successful summary** — the second defense held | `probes/A2/`, `runs/A2/check/`, `runs/A2/check_selection/` |

Totals: 6 faults, 6 valid mutants, **6 detected**, 0 survived, 0 invalid/inactive,
0 blocked. Machine-readable in `matrix.json`. Six rows is the workload limit set
by the prompt, not a coverage score.

### Method

Seven physical copies of `tests/` were made with `shutil.copytree(..., symlinks=False)`,
excluding `tests/out` and `__pycache__`; no hardlinks or symlinks point back to
the original. Each mutant received exactly one logical fault, confined to
`tests/lib/test_cli.py` or `tests/lib/suite_run.py`, applied by an anchor-unique
string replacement that stops if the anchor is not found exactly once. Every
patched file was byte-compiled before use, so a syntax error could never be
reported as a behavioral regression (`inputs/mutation-manifest.json`: all six
`compiles: true`, 2–6 changed lines each). No patch branches on fixture case
names, audit environment variables, or expected results.

Checkers, fixtures, expected values and catalogs were copied unchanged and
verified: `inputs/subject-copy-hashes.json` shows zero drift across all seven
copies for `check_selection.py`, `check.py`, `check_accounting.py`, all five
`tests/fixtures/dispatcher/` files, `tests/catalog.json`, `tests/run.sh` and
`tests/lib/testlib.sh`. The original checkout's subject and oracle files are
byte-identical before and after
(`inputs/subject-and-oracle-hashes-{before,after}.txt`; "original subject/oracle
files changed during the audit: none"). No unrelated defense was disabled.

Drivers were run directly from the appropriate copy and never through the
mutated dispatcher, so a selection fault could not suppress its own detector.
`inputs/mutation-reach.json` proves each run used the intended subject: for every
mutant the subject file differs from the original checkout **and** the mutated
file's hash matches the copy `install_runner` placed inside the fixture
repositories the driver actually executed (S1 1 repo, S2 4, C1 7, C2 12, A1 7,
A2 1; clean baselines 86 and 28). The clean baselines match the original exactly.

Activation was established separately from detection. `probe.py` writes its own
tiny catalog, its own case command (which imports no test machinery and records
its own executions, including PID), and its own literal expectations; it never
uses `repository.py`, `selection.py` or any reviewed oracle, and it is not
counted as a detector anywhere. Each probe ran against `subjects/clean` and the
matching mutant; all seven probe pairs show `behavior_changed: true`
(`probes/activation.json`). Auditor observations — receipts, snapshots,
stdout/stderr — are written outside every disposable subject's `tests/out`, which
is what let the C2 probe measure a directory the mutant erases.

Budget: two driver invocations were used only for A2 (`check.py` for the
executor boundary, `check_selection.py` for the public-command receipts — a
distinct observation point). Every other mutant used one. One correction was
made and it was to my own harness, not to a patch: `drive.py` initially wrote all
results to `runs/<driver>/`, so the four `check_selection` mutant runs
overwrote each other; the path became `runs/<subject>/<driver>/` and the
baselines and those four runs were repeated. No patch needed correction, and no
driver was edited to continue past an assertion.

### Row notes

**S1** is the only fault with no internal containment at all. Because `select()`
truncates before the plan is built, `plan.json`, `completion.selected`,
`case_results` and `ok` are all internally consistent with the reduced work — the
mutant reports `completion {selected: 1, completed: 1}` and exits 0. Nothing in
the run record reveals that `p/second` was requested. Only the comparison of the
literal requested IDs against independently recorded executions exposes it, which
is exactly the observation `check_selection.py` makes at its very first control.

**S2** produced two real executions, not a duplicated plan entry: three distinct
child PIDs, and `p/first`'s command ran twice in separate processes. Two guards
contained it before the checker spoke — `reconcile`'s `reused_case` and
`finish`'s `incomplete_accounting` with `duplicate_cases` — so the run exited 1;
the control observed that as `deduplicate: exit 1, expected 0`.

**C1** was measured in both directions because the brief asks whether execution
was blocked before launch. With a case that requires nothing, the mutant executes
happily against the wrong bundle: the plan, the run summary and the child's own
`PW_APP_DIR` all agree on `dist/PolicyWitness.app` while the caller named
`Named.app` — a planner agreeing with its own modified configuration. With
`requires: ['app']`, the wrong bundle has no controller, so `requirements()`
blocks the case before launch (0 executions, `not_run` + `unrun_case`). The
driver's `all` control hits the second shape, since its `equipment/app` case
requires `app`.

**C2** destroyed all three seeded artifacts and still exited 0. The clean copy
kept every one byte- and mtime-identical. `check_selection.py`'s whole-tree byte
snapshot caught it at the first `--list` control; note the `--help` and invalid
argument controls stay green because `argparse` exits before `main()` reaches
the reordered block, so the snapshot control is doing the work, not the exit code.

**A1** needs care in how detection is attributed, per the prompt's instruction to
distinguish containment from the checker assertion. The first failing control is
`crash`, whose child exits 23 having written no evidence; there `empty_suite` and
`unrun_case` still fail the run, so the exit status stayed 1 and the control fired
on the *missing* `suite_exit` code rather than on a wrongly successful run. That
is scenario-local containment, not general containment — the activation probe
settles the general case: a child that writes a valid passing report and then
exits 19 yields `ok: true`, exit 0, and an empty `harness_errors` on the mutant,
versus `ok: false`, exit 1, `['suite_exit']` on the clean copy, with a
byte-identical report and the same child return code 19 on both sides. A missing
or failed report therefore does not independently explain the clean copy's
rejection. `check.py`'s decisive fixture for this shape, `pass_then_crash`, never
ran because the driver stops at the first assertion, and I did not edit it to
continue.

**A2** is the row the prompt designed to test a second defense, and the defense
held. Dropping the last `case_results` entry inside `finish()` — after execution
and per-invocation accounting, with the guard left intact immediately below — was
caught by that guard on the same call: `incomplete_accounting` with
`missing_cases`, `ok: false`, exit 1. So the fault never reached a successful
summary. Both observation points reject it: `check.py` at `pass_and_skip`
(`check.py:92`) and `check_selection.py` at `default`, each reporting an
unexpected exit 1 whose stderr carries the `incomplete_accounting` diagnostic.
The `check_accounting.py` controls, which supply handoff records directly to
`account`/`finish` and include a `missing_result` case aimed at exactly this
behavior, were not reached — `check.py` stops at its first fixture assertion —
so their independent rejection of this fault is unmeasured here.

### Limitations

- Six faults is the prompt's workload limit. A 6/6 detection rate on this sample
  is not a coverage score for the dispatcher, and says nothing about faults not
  injected.
- Each driver stops at its first failing control, so every row names the *first*
  detector, not the full set. In particular `pass_then_crash` (A1) and the nine
  `check_accounting` controls (A1, A2) never executed; the `check_accounting`
  controls sit behind 28 fixture scenarios in the same process.
- Detection was measured only against `check_selection.py` and `check.py`. Other
  suites, and the real 111-case catalog under live execution, were not run.
- C1 was measured with a fixture bundle containing only a stub controller; a
  real bundle mismatch could surface differently at, for example, the `worker`
  prerequisite or the Rust consumer's `sbpl-check` path.
- Everything ran offline. No app rebuild, no full suite, no live PW/XPC,
  signing or launchd operation, and no privacy setting was touched.
- Relative timings are from a single run each; they are recorded for
  reproducibility, not as performance measurements.

### Conclusion

Every behavior in the six-fault sample has demonstrated regression protection at
the observation point the prompt predicted, and each was caught by the first or
near-first control in its driver rather than by a distant one. Specifically:
losing an explicitly requested case, duplicating a canonical case across
overlapping selectors, ignoring a named app bundle, letting `--list` replace
evidence, ignoring a nonzero child exit, and losing a `case_results` entry are
all currently protected.

Two results are worth separating from the rest. A2's fault was contained by the
independent `incomplete_accounting` guard in `finish()` before any checker looked
at it, which answers the question that row was built to ask: the second defense
does contain an error introduced into the earlier accounting layer. S1, by
contrast, has no internal containment whatsoever — the run's own summary is fully
self-consistent with the reduced work — so its protection rests entirely on the
independent execution receipts in `check_selection.py`. That single control file
is the only thing standing between a selection-side regression and a silently
smaller test run.

No activated fault escaped the sampled controls, so there is no survivor for
which to propose a contract addition. Rows left unmeasured: whether
`pass_then_crash` and the `check_accounting` controls would independently reject
A1 and A2 (both are unreachable once an earlier assertion in the same driver
process fires), and detection by any control outside these two drivers.

### Retained evidence

```text
tests/out/testing-audit/flag-detection/20260915-det01/
  inputs/      head.txt, status.txt, worktree-diff-excluding-audit-doc.txt,
               diff-56d7a3d-eb135ac.txt, original-tree-hashes.json,
               subject-and-oracle-hashes-{before,after}.txt,
               subject-copy-hashes.json, mutation-manifest.json,
               mutation-reach.json
  build_subjects.py, probe.py, run_probes.py, drive.py   (run-directory only)
  subjects/    clean, S1, S2, C1, C2, A1, A2   (physical copies of tests/)
  patches/     S1.diff S2.diff C1.diff C2.diff A1.diff A2.diff
  baseline/clean/{check_selection,check}/  meta.json, stdout.txt, stderr.txt,
                                           artifacts/ (controls.json + fixtures)
  runs/<ID>/<driver>/                      same layout, per mutant
  probes/<ID>/{clean,<ID>}_<variant>/      observation.json, receipts.jsonl,
                                           stdout.txt, stderr.txt, repo/
  probes/activation.json
  matrix.json
```

Earlier audit evidence under `tests/out/testing-audit/` (`batch-01`, `batch-02`,
`measurement-01`, `measurement-02`, `flag-design`) was not read destructively or
replaced; no command in this turn wrote outside the run directory above.

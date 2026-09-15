# Testing audit — adversarial review of the test command

## Task and required output

Try to falsify the three claims below about the new test-control design. Look
for concrete counterexamples in behavior, not merely missing tests or stylistic
preferences. A convincing finding may concern misleading semantics even when
the implementation follows its own documentation.

**Write your full results into this file, `tests/TESTING-AUDIT.md`, under
`Audit results`. Preserve the prompt.** For each question, report your conclusion,
what you inspected/exercised, and any remaining uncertainty. For each finding,
include severity, source file/line, exact reproduction, expected versus observed
behavior, retained evidence, and the smallest useful remediation or contract
test. Distinguish reproduced failures, code-supported findings, and hypotheses.
If you find no counterexample, describe the bounds of your search; do not claim
exhaustive correctness. Your final chat reply should briefly report completion
or blockage and link to this document.

The reviewed implementation is commit `ed922f7` (test selection/configuration/
accounting), following `2d2283e` (Python assertion startup guard). Record actual
HEAD and working-tree differences; review the current implementation and explain
any relevant changes since those commits. Do not reset the checkout.

## Starting points and work boundary

Read `tests/README.md`, then follow the relevant paths:

- `tests/run.sh`, `tests/catalog.json`, `tests/lib/test_cli.py`
- `tests/lib/suite_run.py`, `tests/lib/testlib.sh`
- `tests/suites/runner_byoxpc/run.sh` and selected suite entrypoints
- `controller/integration/cli_contract.rs` for artifact consumption
- `tests/suites/dispatcher/{check.py,check_selection.py}` and
  `tests/suites/shell_helpers/check_scripts.py` for existing defenses

Edit only this audit document among repository source/documentation files.
Create any reproduction scripts, disposable fixture repositories, and raw
observations under `tests/out/testing-audit/flag-design/<your-run-id>/`.
Use physical copies of the reviewed runner for disposable experiments. You may
supply independent catalogs and fixture commands to exercise runner contracts;
clearly distinguish those experiments from reproductions using the real catalog.
Do not modify the reviewed planner/executor to manufacture a failure.

Prefer a small reproduction over a broad run. Do not run the full test suite.
`--list` and offline controls need no live PolicyWitness execution. If a live
PW/XPC/signing command is necessary, select a single command and request
escalation so an outer sandbox does not masquerade as a product failure. Give
executing test commands their own `PW_TEST_OUT_DIR`; the default output directory
is replaced on execution and may contain other evidence.

## Three adversarial questions

1. **Can a reasonable flag combination run a different set of work from what
   a human or agent would understand it to select?** Challenge no-argument
   defaults, literal `--all`, repeated/mixed `--suite` and `--case`, suite
   inclusions, runner contexts, dependency insertion, and `--list`. Can ordering,
   duplication, opt-in membership, or an unknown identifier silently add or omit
   work? Does a case advertised as selectable actually isolate that case in the
   real entrypoint? Inspect the relationship between catalog membership and
   existing suite/manifest cases: where could registration hide work? Use actual
   execution receipts where possible; a planner agreeing with its own catalog
   is insufficient evidence of correct dispatch.

2. **Can configuration be silently ignored, cause tests to use different
   artifacts, or let inspection/rejection alter existing evidence?** Challenge
   app/controller aliases, helper lookup, caller working directory, relative
   paths, symlinks, output overlap, run labels, quiet values, and private runner
   settings. Trace effective configuration into real shell and Rust consumers.
   Try to demonstrate a meaningful mismatch between the advertised plan and the
   artifact actually exercised, or a filesystem change caused by help, listing,
   or rejected input. Identify any restriction that makes the small interface
   misleading or needlessly inexpressive; explain the concrete use case.

3. **Can selected work disappear while the command exits successfully or
   reports `ok: true`?** Challenge crashes, incomplete/contradictory evidence,
   unexpected reports, skips, unavailable prerequisites, failed dependencies,
   and the BYOXPC shared installation/cleanup lifecycle. Can one failure suppress
   independent cases without accurate accounting? Does deduplication accidentally
   remove the defense against genuinely reused evidence? Are completed, skipped,
   and unrun selections truthful and consistent with the command exit? Examine
   whether existing controls independently observe these facts or merely echo
   the machinery they purport to check.

Concentrate effort on the strongest counterexample for each question. Report
additional material findings if you encounter them, but avoid expanding into
worker implementation review or a speculative feature wishlist.

## Existing verification and known failure

The expanded `--all` run selected 111 cases: 110 passed, one failed, none skipped
or unrun. The failure was `runner_byoxpc/runner_auth_external`: installation
succeeded but verification returned `xpc_timeout`. The unchanged script also
failed when invoked directly outside the new dispatcher and outside the harness
sandbox. Team-matched BYOXPC installation and all its selected specimens passed.
This timeout is known; do not report its existence as a new flag-design finding.
You may investigate whether the new design mishandles its consequences.

Useful existing artifacts, if still present:

- `tests/out/control_surface/all/run.json`: expanded live run (before final
  selector-metadata refinements; use the current code for fresh reproductions).
- `tests/out/control_surface/auth_direct/`: direct external-auth reproduction.
- `tests/out/control_surface/final-offline/`: passing final offline suites,
  including 63 public-command controls and 29 wrapper controls.
- `tests/out/control_surface/reuse-final/`: passing 28 reconciliation controls,
  including distinct selections that try to reuse the same evidence path.
- `tests/out/control_surface/alternate-run/` and
  `tests/out/control_surface/alternate/executed-tools.jsonl`: passing Rust
  integration and shell smoke through alternate app wrappers, with independent
  receipts for nine controller invocations and two bundled `sbpl-check` calls.

These results are starting evidence, not premises you must accept.

## Audit results

Run ID `20260915-flag01`. All reproduction scripts, plans, receipts and raw
observations are under `tests/out/testing-audit/flag-design/20260915-flag01/`
(6.5 MB, untracked). Two findings, both reproduced with execution receipts.
Five further observations are recorded; none of them is a counterexample to the
three claims. This document is the only repository file I changed.

### Reviewed state

- Actual HEAD is `bc7f654` ("Ask adversarial audit questions about the test
  control surface"). `git diff --stat ed922f7..HEAD` touches only
  `tests/TESTING-AUDIT.md` (+111 / -391), so the reviewed selection/
  configuration/accounting implementation (`ed922f7`) and the Python assertion
  guard (`2d2283e`) are byte-identical to what is on disk. There is no relevant
  change since those commits to explain. The checkout was not reset.
- Working tree was clean at the start of the turn and carries only this
  document at the end. Subject digests recorded before the work and re-verified
  with `shasum -c` afterwards (`inputs/subject-hashes.txt`): `test_cli.py`
  `dbca4e3d…`, `suite_run.py` `33d97cb2…`, `testlib.sh` `1ceddac3…`,
  `catalog.json` `0ea38c7f…`, `run.sh` `8362d808…` — all `OK` after the run.
- Host equipment during this turn: a Developer ID identity matching the app
  team and a GUI launchd domain were both available
  (`inputs/identity-probe.txt`), so no result below is an artifact of missing
  prerequisites masquerading as behaviour.

### Method and bounds

Five instruments, in order of authority:

1. `list/list_matrix.py` — 22 `--list` plans from the real catalog, run from
   `/` with every `PW_*` variable stripped (`list/list_matrix.json`).
2. `exec/real-run.*` — one real execution of the public command selecting
   eight offline cases (`requires: []`) drawn from eight different entrypoints,
   four of them multi-case suites, into its own `PW_TEST_OUT_DIR`.
3. `exec/live-out` — one live PolicyWitness execution: a single case selected
   out of the nine-case `blackbox_menagerie` entrypoint.
4. `accounting/accounting.py` — eight scenarios driving a **physical copy** of
   the reviewed runner (via `tests/fixtures/dispatcher/repository.py`) against
   **independent catalogs** and an **independent case command**
   (`accounting/witness.py`, which imports no test library and derives nothing
   from the dispatcher). These are clearly not reproductions with the real
   catalog; they exercise the runner contract.
5. `config/bundle_identity.py` and `inspect/preserve.py` — configuration
   resolution and filesystem-preservation probes against the real repository.

Bounds: no full-suite run, no app rebuild, and exactly one live PW command. The
reviewed planner and executor were never modified — every experiment supplies
inputs to unmodified copies. I did not review worker or controller internals,
`cargo`/`swift` batch cases, or the known `runner_auth_external` timeout. Cases
requiring `cargo`, `swift`, `gui` or `identity` were exercised through `--list`
and through fixture catalogs only, never live. The static entrypoint sweep
(`list/entrypoint_coverage.py`) is a regex cross-check and is reported as such.

---

### Question 1 — can a flag combination run different work than a reader expects?

**Conclusion: no counterexample found.** Selection is order-independent,
repetition-independent, deduplicating across suite membership, and each
advertised case isolates itself in the real entrypoint. One material but
non-counterexample defect in the plan's *presentation* is recorded as O1.

What I exercised:

- **Defaults, `--all`, ordering, duplication** (`list/list_matrix.json`). No
  arguments selects 96 cases (`mode: default`); `--all` selects 111
  (`mode: all`); the 15-case difference is exactly `--suite opt_in`.
  `--all --suite smoke` and `--suite smoke --all` both produce byte-identical
  case lists to `--all`. `--suite smoke --suite shell_helpers` and the reverse
  produce identical ordered lists; `--suite smoke --suite smoke` selects three
  cases; `--case X --case X` selects one. Execution order is catalog order with
  dependencies hoisted, independent of argv order — `--case runner_byoxpc/BBX-002
  --case runner_byoxpc/BBX-001` plans
  `[runner_install, BBX-001, BBX-002]` — while `selection.cases` preserves the
  caller's original order and deduplication for the record.
- **Unknown identifiers and abbreviation.** `--suite no_such_suite`,
  `--case smoke/no_such_case` and the bare leaf `--case specimen_file_read_deny`
  all exit 2 naming the rejected identifiers; `--sui smoke` is rejected as an
  unrecognized argument (`allow_abbrev=False`). Nothing is added or omitted
  silently.
- **Suite inclusions and opt-in membership.** `--suite witness_contract`
  selects 14 cases, two of which are `runner_validator_failure/...` includes;
  `--suite witness_contract --suite runner_validator_failure` selects 15, with
  each shared contract case appearing exactly once. `--suite opt_in` selects
  precisely the 15 non-default cases.
- **Dependency insertion.** `--case runner_byoxpc/BBX-001` plans two cases and
  labels `runner_byoxpc/runner_install` `selection: "dependency"`. With
  `runner_auth_external` added, the plan is
  `[runner_auth_external, runner_install, BBX-001]`, which is exactly the order
  needed for the shared-installation group to form (see Q3).
- **Real dispatch receipts, not planner self-agreement.** Eight offline cases
  selected by exact ID produced eight invocations, eight report directories,
  eight `test_start` and eight `test_end` events, `counts.total = 8`,
  `completion {selected: 8, completed: 8, skipped: 0, unrun: 0}`, `ok: true`,
  exit 0, zero harness errors (`exec/real-run-summary.json`). Four of those
  eight come from multi-case suites; each produced **only** its selected leaf:
  `blackbox_menagerie` 1 of 9, `shell_helpers` 1 of 5, `runner_validator_failure`
  1 of 3, `runner_filter_sysctl_name` 1 of 2.
- **Live isolation receipt.** `--case blackbox_menagerie/core_strict_tmp` ran
  the live nine-case menagerie entrypoint and produced exactly one report
  directory, one terminal event and `completion {selected: 1, completed: 1}` in
  3.05 s (`exec/live-run-summary.json`).
- **Registration versus entrypoint reach** (`list/entrypoint_coverage.json`).
  Every command shared by more than one registered case carries a selection
  guard (literal `test_selected` or a loop variable), and for **every** command
  in the catalog the set of identifiers the script can report is a subset of the
  identifiers the catalog registers — there is no entrypoint that can report
  work nobody selected. The apparent gap on `tests/suites/runner_byoxpc/run.sh`
  is an artifact of the regex: its leaves are routed by the `case "$leaf"`
  statement at `run.sh:67-77`, whose `*)` arm exits 2 on an unknown leaf. The
  menagerie's manifest (`tests/fixtures/blackbox_menagerie/cases/core.json`) and
  its eight catalog leaves match exactly, so no manifest case is unreachable and
  no catalog case is unmanifested.

**Remaining uncertainty.** I confirmed isolation by execution for nine of the
111 cases (eight offline plus one live) and by static reach analysis for the
rest. `unit`, `integration`, `runner_unit` (`cargo`/`swift` batch cases) and all
`gui`/`identity` cases were never dispatched live. A suite that performed
unreported side effects for a deselected case would not appear in any receipt I
collected, because the only signal I used is reports and events.

---

### Question 2 — can configuration be ignored, redirect artifacts, or mutate evidence?

**Conclusion: one finding (F1).** Inspection and rejection provably preserve
evidence; effective configuration reaches children and the Rust consumer intact
in every ordinary case; but a named app bundle whose controller is a symlink is
accepted and then silently split across two bundles.

Preservation held completely (`inspect/preserve.json`): across 11 probes —
`--list`, `--all --list`, `--case … --list`, `--help`, unknown case, unknown
suite, `PW_TEST_QUIET=yes`, `PW_TEST_RUN_ID=../escape`, `PW_TEST_CASES=x`,
standalone `PW_BIN`, and an out-of-tree `PW_TEST_OUT_DIR` — a seeded sentinel
output directory (prior `run.json`, a prior case report, a binary blob) was
byte- and mtime-identical afterwards, the repository worktree was unchanged, the
`tests/lib` mtimes were unchanged, and **no new `.pyc` appeared anywhere under
`tests/`** even though I deliberately removed `PYTHONDONTWRITEBYTECODE` from the
environment first. Rejections all exited 2 before any execution step. The
guards that should fire did fire: disagreeing `PW_BIN`/`PW_BIN_PATH`, a
standalone controller outside a bundle, and `PW_APP_DIR` naming a different
bundle from the controller override are each rejected with a specific message
(`config/bundle_identity.json`).

#### F1 — a symlinked controller splits the tested bundle in two

- **Severity: medium.** Silent, produces `ok: true` and exit 0, and the two
  halves of a split bundle can differ in exactly the components the suite is
  meant to be testing.
- **Source:** `tests/lib/test_cli.py:99-123`. `path()` (`:104`) resolves
  symlinks; `binary` at `:121` is `(app / 'Contents/MacOS/policy-witness').resolve()`,
  so the controller is resolved *through* the bundle the caller named, while
  `app` (`:115`) keeps the caller's bundle. The agreement check at `:122-123`
  compares `bins[0]` to that already-resolved `binary`, so it can never observe
  the split. The inverse path at `:116-118` derives `app` from the *resolved*
  controller, so a `PW_BIN`-only caller loses their bundle entirely.
- **Reproduction** (`config/bundle_identity.py`, `accounting/accounting.py`
  scenario `split_bundle`):

  ```sh
  mkdir -p /tmp/pw-split/Named.app/Contents/MacOS
  ln -s "$PWD/dist/PolicyWitness.app/Contents/MacOS/policy-witness" \
        /tmp/pw-split/Named.app/Contents/MacOS/policy-witness
  PW_APP_DIR=/tmp/pw-split/Named.app ./tests/run.sh --case smoke/specimen_file_read_deny --list
  ```

- **Expected:** either the pair is rejected the way a disagreeing
  `PW_BIN`/`PW_APP_DIR` pair is, or `configuration.pw_bin` stays inside
  `configuration.app_dir`.
- **Observed**, three distinct behaviours, all accepted:
  1. `PW_APP_DIR=Named.app` → `app_dir = …/Named.app`,
     `pw_bin = …/dist/PolicyWitness.app/Contents/MacOS/policy-witness`. The
     controller is **not** inside the named bundle.
  2. `PW_BIN=Named.app/Contents/MacOS/policy-witness` alone (or `PW_BIN_PATH`
     alone) → `app_dir` becomes `…/dist/PolicyWitness.app`. The bundle the
     caller named is discarded with no diagnostic.
  3. Supplying all three variables, all spelled as the wrapper, still yields the
     split: the "all supplied paths must agree after resolution" guard passes
     because both spellings resolve to the same *controller*, while `app_dir`
     remains the wrapper.
- **Why it matters downstream.** Everything except the controller is derived
  from `app_dir`: the `worker` prerequisite probe
  (`tests/lib/suite_run.py:167-169`), `runner_c_worker_harness/run.sh:12`
  (`${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc/…/pw-probe-runner`), the
  `case.sh:7-8` fallback, and — in the Rust consumer —
  `controller/integration/cli_contract.rs:49-54`, where `sbpl_check_bin_path()`
  joins `PW_APP_DIR` while `pw_bin_path()` (`:22-29`) prefers `PW_BIN_PATH`. A
  run can therefore exercise one bundle's controller against another bundle's
  worker and bundled `sbpl-check`. The `split_bundle` scenario shows the harm is
  not theoretical: the probe `Split.app` carries its own `pw-probe-runner`, and
  the plan pairs it with the other bundle's controller.
- **Retained evidence:** `config/bundle_identity.json` (11 probes, including the
  three rejection controls and a copied-binary and exec-wrapper bundle that both
  resolve correctly), `accounting/split_bundle/` — a real execution receipt in
  which the child process recorded
  `app=…/repo/Named.app`, `bin=…/repo/Real.app/Contents/MacOS/policy-witness`,
  with `ok: true`, exit 0 and no harness error.
- **Smallest remediation:** in `resolve_config`, after computing `binary`,
  reject when `app not in binary.parents` — one condition beside the existing
  `:122-123` check. Note this is also what makes case (2) coherent: the inverse
  inference at `:116-118` should be derived from the *unresolved* override so
  the caller's bundle survives, or rejected outright when the two disagree.
- **Smallest contract test:** add to `tests/suites/dispatcher/check_selection.py`
  a `config_error_*` row whose fixture repo contains
  `An app.app/Contents/MacOS/policy-witness` as a symlink into a second bundle,
  expecting exit 2. The existing `symlink_escape` row (`:149-151`) covers only
  `PW_TEST_OUT_DIR`; no existing row makes an app bundle's own controller a
  symlink.

---

### Question 3 — can selected work disappear while the command succeeds?

**Conclusion: one finding (F2).** Every failure mode I could construct with the
real catalog is reported truthfully and fails the command. The single silent
loss requires a catalog that uses `report_suite` — a deliberate, already-tested
catalog field — to point two selected cases at one evidence path inside one
invocation.

The accounting that held, each with an execution receipt from a physical copy of
the runner (`accounting/accounting.json`):

| scenario | result |
|---|---|
| `alias_control` — two cases, two evidence paths | `ok: true`, exit 0, `completion {selected: 2, completed: 2}`, two `case_results` |
| `alias_unwritten` — alias names a path nobody writes | exit 1, `unrun_case` + `unselected_case`, `unrun: 1` |
| `alias_collapse_standard` — same collision across two invocations | exit 1, **`reused_case`** |
| `alias_collapse_extra_report` — grouped collision, evidence on both paths | exit 1, `unselected_case` |
| `byoxpc_partial_group` — shared installation passes, command stops after the first leaf | exit 1, `unrun_case` ×2, `completion {selected: 4, completed: 2, unrun: 2}` |
| `skipped_dependency` — a declared skip of a dependency in its own invocation | exit 1, `not_run` + `unrun_case`; the dependent is `unrun`, the dependency `skipped` |

Deduplication does **not** remove the reuse defence: `alias_collapse_standard`
is exactly the "two distinct selections write one evidence path" case, and
`seen_cases` (`suite_run.py:97-100`) catches it across invocations. The
suppression claim also holds — in `byoxpc_partial_group` the later leaves are
individually accounted rather than folded into the first result, and in the real
eight-case run a per-case process boundary was used for every standard case
(`suite_run.py:215-220` groups only adjacent `byoxpc` cases sharing a command).

#### F2 — two selected cases sharing one aliased evidence path collapse silently

- **Severity: medium.** `run.json.ok` is `true`, the shell exits 0, and a
  selected case is absent from `case_results` entirely — contradicting
  `tests/README.md:236-244` ("one `case_results` entry per selected case",
  "`completion` counts selected, completed …, skipped, and unrun cases") and
  the promise that "unrun selections … fail".
- **Source:** `tests/lib/suite_run.py:189`. `expected = {(c['report_suite'],
  c['test_id']): c for c in item['cases']}` is a dict comprehension over the
  invocation's cases; two cases with the same pair collapse to one entry, and
  the loop at `:196` then emits one `case_results` entry for two selected cases.
  `report_suite` reaches this point unvalidated: `tests/lib/test_cli.py:31-51`
  type-checks `command`, `requires`, `default`, `context`, `skip_reasons` and
  `depends_on`, but `report_suite` is only `setdefault`-ed at `:41` after
  `case.update(entry)` at `:33`, so any catalog entry may set it to anything.
  It is not dead machinery: `tests/suites/dispatcher/check.py:53` sets it
  explicitly for every fixture case and `:114-116` asserts the aliased reporting
  path, and `suite_run.py:3-4` calls wrapper aliases part of the contract.
- **Reproduction** (`accounting/accounting.py`, scenario `alias_collapse`;
  independent catalog, physical copy of the runner, independent case command):

  ```json
  {"schema_version": 1, "suites": {
     "alpha": {"command": ["bash", "tests/suites/shared/run.sh"],
               "context": "byoxpc", "cases": [{"id": "x", "report_suite": "beta"}]},
     "beta":  {"command": ["bash", "tests/suites/shared/run.sh"],
               "context": "byoxpc", "cases": ["x"]}}}
  ```

  The shared command writes one report and one `test_start`/`test_end` pair for
  `beta/x` — the behaviour a wrapper alias is meant to have. Run `tests/run.sh`
  with no selectors.
- **Expected:** two selected cases, therefore two `case_results` entries and
  `completed + skipped + unrun == selected`; a second case with no distinct
  evidence should be `unrun` and fail the run.
- **Observed:** exit 0, `ok: true`, `harness_errors: []`,
  `counts {pass: 1, total: 1}`,
  `completion {selected: 2, completed: 1, skipped: 0, unrun: 0}` — the three
  states sum to 1, not 2 — and `case_results == [("beta/x", "completed",
  "pass")]`. `alpha/x` appears in `plan.cases` and then vanishes from the run
  record with no diagnostic.
- **Boundary, verified:** the collapse needs all three of (a) both cases in one
  invocation, which for this executor means adjacent `byoxpc` cases sharing a
  command (`suite_run.py:215-220`); (b) both resolving to the same
  `(report_suite, test_id)`; (c) evidence written only on the shared path. Relax
  (a) and `reused_case` fires; relax (c) and `unselected_case` fires — though in
  that variant (`alias_collapse_extra_report`) `completion` still silently
  reports 1 of 2, so the under-count is the same defect surfacing behind a
  different diagnostic.
- **Reachability with the shipped catalog: none.** `tests/catalog.json` sets
  `report_suite` nowhere (`grep -n report_suite tests/catalog.json` is empty),
  and without it every case's pair is its own unique `suite/leaf`. The current
  BYOXPC wrapper achieves aliasing at runtime through `PW_TEST_SUITE_OVERRIDE`
  instead. So this is a contract defect in the reviewed runner, not a live
  mis-accounting of today's 111 cases.
- **Retained evidence:** `accounting/accounting.json` plus per-scenario
  `repo/tests/out/{plan,run,dispatch}.json`, `receipts.jsonl`, `stdout.txt` and
  `stderr.txt` under `accounting/alias_collapse/`, `accounting/alias_control/`,
  `accounting/alias_collapse_standard/` and
  `accounting/alias_collapse_extra_report/`.
- **Smallest remediation:** in `account()`, build `expected` as a list and
  detect the collision, e.g. raise `problem(item, 'ambiguous_case_path', …)`
  when two cases in one invocation share a `(report_suite, test_id)` pair; or
  reject it earlier in `catalog()`, where a `report_suite` collision across the
  whole catalog is already computable alongside the existing
  `duplicate catalog case` check at `test_cli.py:29-30`.
- **Smallest contract test:** `tests/suites/dispatcher/check_selection.py`
  already asserts the right invariant at `:102`
  (`[r['id'] for r in case_results] == [c['id'] for c in plan['cases']]`) and
  `:100-101` asserts the completion arithmetic — but none of its fixture
  catalogs sets `report_suite`, and `check.py`'s `alias` control exercises only
  **one** aliased case per invocation. Adding a fixture suite pair that aliases
  two `byoxpc` cases onto one reporting path, expecting exit 1, closes the gap
  without any new assertion.

---

### Additional observations

- **O1 (Q1, low, reproduced) — `plan.suites` names suites that were not
  selected.** `test_cli.py:171-172` emits every catalog suite whose membership
  *intersects* the selection. So `--suite smoke` lists `opt_in`;
  `--case runner_byoxpc/BBX-001` lists `opt_in`; and
  `--case runner_validator_failure/validator_unavailable_reports_degraded`
  lists `witness_contract` alongside a single case. A reader comparing this key
  with `selection.suites` can reasonably read it as "these suites are running".
  The `cases` list is correct in every instance, so no extra work is dispatched;
  the defect is naming. Evidence: `list/list_matrix.json`, rows `suite_ab`,
  `byoxpc_leaf`, `shared_single_case`. Smallest fix: rename the key
  (`containing_suites`) or document it in `tests/README.md:47-49`.
- **O2 (Q2, low, reproduced) — `PW_TEST_QUIET=0` silences a directly-invoked
  suite script.** `testlib.sh:122` suppresses on any *non-empty* value, so `0`,
  `false` and `1` all silence `test_log`, while `tests/README.md:80-81` defines
  `0` as retaining messages. The public command is correct — it normalizes to
  `''`/`'1'` at `test_cli.py:132-139` and `suite_run.py:231`, and a
  `PW_TEST_QUIET=0` run printed all three case lines. The mismatch only bites
  developers running a suite script directly, which the README already carves
  out at `:63-66`. Evidence: `inspect/quiet-semantics.txt`.
- **O3 (Q1/Q3, low, code-supported, not reproduced here) — `--suite smoke`
  drags in an `identity` case.** `smoke/runner_caller_auth` is `default: false`
  but a suite selects all its members, so the documented per-suite invocation at
  `tests/README.md:140` selects a case requiring a matching Developer ID. On a
  host without one, `requirements()` blocks it and the documented rule
  ("Required equipment missing at execution is a failed run … never an implicit
  skip", `README:60-61`) turns that into `not_run` + `unrun_case` and exit 1.
  Both rules are individually documented and the combination is visible in
  `--list`; I record it because a reader of the suite table would not expect a
  smoke invocation to depend on signing equipment. Not reproduced: this host has
  a matching identity (`inputs/identity-probe.txt`).
- **O4 (Q2, informational) — the default output directory is replaced
  wholesale.** `test_cli.py:178-181` `rmtree`s `PW_TEST_OUT_DIR`, whose default
  is `tests/out`, which is also where this repository keeps
  `tests/out/control_surface/`, `tests/out/testing-audit/` and the other
  evidence trees the prompt cites as starting material. This is documented
  (`README:76-78`, `:218`), and it is why every command in this turn was given
  its own directory; noted only so the hazard is on record.
- **O5 (Q3, informational) — where the existing controls stop.** The two
  control files are genuinely independent, not echoes: `check_selection.py`
  builds a disposable repository with its own catalog and a receipt-emitting
  fixture command that imports no test library, then compares execution receipts
  against the plan, the completion arithmetic and the per-case accounting;
  `check.py` drives 27 evidence-corruption scenarios through the real dispatcher
  and asserts `ok` against independently recomputed counts (`check.py:105-109`)
  rather than against the dispatcher's own verdict. The gap F2 exploits is one
  of *coverage*, not of assertion strength: the invariant is asserted
  (`check_selection.py:100-102`) but no fixture catalog reaches the state that
  violates it.

### Retained evidence

```text
tests/out/testing-audit/flag-design/20260915-flag01/
  inputs/          head.txt, status.txt, diff-since-ed922f7.txt,
                   subject-hashes.txt, identity-probe.txt
  list/            list_matrix.py + list_matrix.json (22 real-catalog plans)
                   entrypoint_coverage.py + .json (catalog vs entrypoint reach)
  config/          bundle_identity.py + .json, apps/ (4 probe bundles)
  exec/            real-run.stdout/.stderr/.exit, real-out/ (8 offline cases),
                   real-run-summary.json, live-out/ (1 live case),
                   live-run-summary.json
  accounting/      accounting.py, witness.py, accounting.json,
                   <scenario>/repo/tests/out/{plan,run,dispatch}.json,
                   <scenario>/receipts.jsonl, stdout.txt, stderr.txt
  inspect/         preserve.py + preserve.json (11 probes), sentinel-out/,
                   quiet-semantics.txt, quiet-out/
```

Nothing under `tests/out/control_surface/` or any earlier
`tests/out/testing-audit/` directory was read destructively or replaced; every
executing command in this turn was given a `PW_TEST_OUT_DIR` inside the run
directory above.

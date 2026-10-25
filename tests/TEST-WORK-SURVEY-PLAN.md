# Test work survey: plan

A read-only survey of what PolicyWitness's tests and test-like procedures
do, what a passing result establishes, what a failing result establishes or
fails to establish, and where activities that share the name *test* are doing
materially different jobs or where apparently different activities do the
same job. The deliverable is one report at
`records/tests/TEST-WORK-SURVEY-REPORT.md`. Nothing else in the tree changes.

This plan follows [Planning a change](../CONTRIBUTING.md#planning-a-change)
and the [test working guidance](AGENTS.md). It was prepared on 2026-10-25
against revision `87d5fb2d08d430ffabde6d6a3316257e8190e6c3` (2026-10-24,
"Validate release battery selection and complete acceptance coverage"), the
tip of `main` after the test-execution consolidation recorded in
[its plan](../records/tests/UNIFY-TEST-EXECUTION-PLAN.md). The earlier
[opt-in survey](../records/tests/OPT-IN-REPORT.md) examined `2f23cad`, five
commits earlier; its counts and entry points are historical context here, and
every one the report relies on is re-established at the examined revision.

## Question

For every test and test-like procedure in the current tree, determined from
its implementation and the assertions it actually makes:

- What is exercised, constructed, varied, mutated, observed, compared or
  checked?
- What does a pass establish, stated no more broadly than the executed checks
  support: a PolicyWitness behavior, a property of a test instrument, a build
  or release artifact, an observed property of this host, agreement between
  two texts, or something else?
- What does a failure establish or fail to establish: an asserted product
  regression, missing equipment, invalid setup, an inconclusive observation,
  or a fault in test machinery?
- What makes the activity intelligible: other cases, fixtures, artifacts,
  prior observations, execution context, or a particular implementation
  detail the reader must know?
- Which apparent differences matter, and which apparent similarities hide
  different jobs?

Granularity. The catalog case is the unit of complete accounting: every one
receives a stated inspection level. Inside the batch cases the unit is the
test group (a Rust `mod tests` in one source file, a Swift `run*Tests`
function with its `tk.group` names, a Python `unittest` class, or a checker's
scenario table), and the survey reads the assertions of representatives in
each group and of any member whose name, comment or equipment guard suggests
a job different from its neighbours'. The report says, per group, which
members were read and which were grouped on their names alone. Stage 1 states
the rule, and the promise in the first sentence above is bounded by it: an
account grounded in actual assertions for every case and every group, not an
assertion-by-assertion account of every function.

These are investigative questions. They are not proposed fields, and the
report does not answer them with a schema. The commission that this plan
implements forbids a taxonomy, per-test metadata or labels, release
membership judgments and refactoring proposals. A concrete defect found while
reading may be reported as a finding.

## Grounding and what this preparation did

Executed: two read-only planning invocations of the public command, which
print the selected plan and return before the checkout lock is taken
(`tests/lib/test_cli.py` lines 169 and 210-212; `tests/README.md` lines
71-78 document them as writing nothing). Their output was kept in the
session scratch directory outside the checkout.

```sh
./tests/run.sh --list        # 196 cases, selection mode "default"
./tests/run.sh --all --list  # 235 cases, selection mode "all"
```

Read: `tests/catalog.json`, `tests/run.sh`, `tests/lib/test_cli.py`,
`tests/lib/suite_run.py`, `tests/lib/testlib.sh`, `tests/lib/case.sh`,
`tests/README.md`, `tests/AGENTS.md`, `tests/OPT_IN_TESTS.md`,
`tests/COVERAGE.md`, the ownership sections of
`tests/FAILURE-PROPAGATION-CONTRACT.md`, `tests/fixtures/README.md`,
`records/tests/*`, the suite drivers named below, every suite README's
heading structure and a dozen READMEs in full, `runner/Package.swift`,
`runner/Tests/PWRunnerCoreTests/main.swift` and `TestKit.swift`, the Rust
test attributes, and `tests/suites/source_drift/check.py` lines 173-275 (the
rules a Markdown file under `tests/` must satisfy, which this plan obeys).

Not executed: any catalog case, `cargo`, `swift`, `meson`, a build, or a
prune. The working tree was clean at `87d5fb2` apart from the commission
prompt, which the commit adding this plan removes. The counts below were
taken at that revision and must be re-established by the executor before use
(Stage 0).

## Boundaries made operational

- **Read-only.** No file under the checkout changes except the report.
  Working notes, parsed plans, ledgers and scripts live in the session
  scratch directory, not in `.tmp/` (which is inside the checkout) and not in
  `tests/out/`.
- **Permitted discovery commands.** `tests/run.sh --list` with any selectors
  (verified read-only above); `git show`, `git log`, `git blame`; `grep`,
  `find`, `wc`; and Python run with `-I` against copies of catalog or plan
  JSON. Loading `tests/lib/test_cli.py`'s `catalog()` and `select()` in a
  `-I` interpreter is permitted because they only read the catalog; the
  prior survey did this and it keeps suite-level inheritance of `default`,
  `requires`, `command` and `context` identical to the implementation.
- **Not permitted.** `cargo test -- --list` and `swift run` compile into the
  managed `controller/target/` and `runner/.build` and take the checkout
  lock; they are builds, not discovery. Rust and Swift populations are
  counted statically (attributes and `tk.run(` call sites) and labelled as
  static counts. `tests/run.sh --prune` is not needed and is not run.
- **Runtime questions.** Where a material question needs an execution (for
  example how long a process takes to abort), the report records the
  proposed observation, the case it would inform and why static reading
  cannot settle it. It does not run it.
- **Out of scope as subjects, in scope as population.** The harnesses under
  `records/performance/` are historical investigation equipment that
  `records/performance/README.md` says require a retired application; they
  are accounted for in one paragraph as unregistered procedures and not
  investigated. `tests/build-evidence.py` is a build tool and
  `tests/compare_json_fixture.py` a helper; both are named once as test-adjacent
  files. `tests/accept-release.sh` and `tests/lib/release_accept.py` are a
  test-like procedure (release acceptance runs the default battery and
  requires two named envelopes to report the standard runner) and are
  accounted for and compared with the catalog cases that exercise them
  offline.
- **No execution-route questions.** The consolidation closed direct
  invocation of case scripts (`tests/lib/testlib.sh` `testlib_init` and
  `test_selected`, lines 60 and 178, refuse without the dispatcher's
  context; `shell_helpers/controls` asserts the refusal at
  `tests/suites/shell_helpers/check.py` line 133). The report states this as
  an operational fact and does not reopen it.

## The population at the examined revision

Counts the executor re-derives in Stage 0. Each row names its source.

| Level | At `87d5fb2` | Source |
| --- | --- | --- |
| Public interface | `tests/run.sh`; `make test` forwards with no selectors; `tests/accept-release.sh` runs the default battery against an extracted ZIP | `tests/run.sh`, `Makefile` targets `test`, `notarize`, `release`; `tests/lib/release_accept.py` |
| Suites in the catalog | 42: 41 with their own `cases`, plus the `opt_in` include group of 39 | `tests/catalog.json`; `catalog()` |
| Canonical cases | 235; 196 default; 39 non-default; 19 in the `byoxpc` runner context | `--all --list`, `--list` |
| Distinct case command scripts | 111: 96 cases have a script of their own; 139 cases share 15 multi-case drivers | `command[1]` over the `--all` plan |
| Largest drivers | `runner_c_worker_harness/run.sh` 46 cases; `runner_use_c_worker/run.sh` 14; `preflight/run.sh` 12; `runner_byoxpc/run.sh` 12; `blackbox_menagerie/run.sh` 9; `source_drift/run.sh` 8; `shell_helpers/run.sh` 8; `failure_boundaries/run.sh` 7; `dispatcher/run.sh` 6 | same |
| Suites whose cases all carry their own command | `smoke`, `blackbox_e2e`, `run_effects`, `witness_contract` (no suite-level `command`) | catalog |
| Cases listed in two suites | 2: the `runner_validator_failure` decode and unavailable cases, included by `witness_contract` | catalog `include` |
| Dependencies | 12 `depends_on` edges: 11 `runner_byoxpc` leaves on `runner_install`; `launch_inventory` on `contaminated_worker` | catalog |
| Declared skips | 16 cases, all `annotated_mismatch_absent`: 8 menagerie specimens and their 8 BYOXPC copies | catalog `skip_reasons` |
| Equipment-free cases | 24 (listed below) | `requires == []` in the `--all` plan |
| Case-level equipment that differs from the suite's | 49 cases | compare case `requires` with the suite entry |
| Rust test functions | 223 `#[test]`: 198 in `policy-witness`, 11 in `sbpl-check`, 14 in `controller/integration/cli_contract.rs`; 2 carry `#[ignore]` (`controller/src/run_flow.rs` lines 932 and 1092) and run only through `runner_unit` | `grep -rn '#\[test\]'`; static |
| Swift test blocks | 277 `tk.run(` call sites across 32 registered `run*Tests` functions in `main.swift`; `TestKit` has no skip state | `grep -c 'tk.run('`; static |
| Python `unittest` methods inside cases | 68 in `preflight/check_build_provenance.py`; 137 across the seven `source_drift` modules; most other checkers are assertion scripts, not `unittest` | `grep -c 'def test_'`; static |
| Scenario tables inside cases | `harness.c` scenarios (46 harness cases); `tests/fixtures/comparison/matrix.json` rows; `tests/fixtures/blackbox_menagerie/cases/core.json` (8); the build manifest's refusal list driven by `build_refusals.py`; the shared `tests/fixtures/contract/*.json` corpora read by Swift, Rust and Python | fixtures and suite READMEs |

Equipment over the 235 cases, by exact `requires` set: `app`+`clang` 55;
`app`+`clang`+`worker` 47; `app` alone 45; none 24; `clang` alone 18;
`app`+`gui` 13; `app`+`gui`+`identity` 7; eleven other combinations cover
the remaining 26. The nine recognized equipment names are the set at
`tests/lib/test_cli.py` line 56.

The 24 equipment-free cases: `preflight/release_controls`,
`preflight/release_deadline_controls`, six `source_drift` cases (all but the
two that read `meson.build`), all eight `shell_helpers` cases,
`runner_unit/build_receipt_controls`, `runner_filter_sysctl_name/checker_controls`,
`runner_validator_failure/transcript_controls`, `run_capture/controls`,
`run_effects/checker_controls`, `blackbox_e2e/comparison_controls`,
`blackbox_menagerie/validation_controls` and
`witness_contract/attempt_outcome_matrix_enforced`. Twelve of them live in
suites whose other members need the app; they are the first place to look for
different jobs under one suite name.

How a result is recorded, which the report must describe before interpreting
any outcome: a case ends with `test_pass`, `test_fail` or `test_skip`
(`tests/lib/testlib.sh` lines 269-292), each writing a terminal event and a
`report.json`; `test_fail` exits 1 immediately. The dispatcher
(`tests/lib/suite_run.py`) separately produces `unrun` for missing equipment
or a failed dependency, the harness errors `unexpected_skip`, `unrun_case`,
`missing_report`, `reused_case`, `interpreter_mismatch`,
`build_tree_in_evidence` and `scratch_retained`, an artifact-integrity
failure independent of case statuses, and a `system_sleep_ms` record whose
nonzero value marks a failure as not creditable product evidence without
changing its status (`tests/suites/dispatcher/README.md`, "Contract"). Inside
the two batch cases the mapping is coarser: `unit/rust.unit` passes only when
`cargo test --bins` exits 0 and retains one log;
`runner_unit/pwrunner_core_unit_executable` fails on a nonzero exit, on any
`SKIP` or `FAIL` line in the Swift log, or on a missing summary line
(`tests/suites/runner_unit/run.sh` lines 33-52). These are the implemented
vocabularies for "failure of test machinery" and "inconclusive"; the report
uses them rather than inventing others.

## Method

### Stage 0: establish the state

1. Record `git rev-parse HEAD`, `git log -1 --date=iso`, `git status
   --porcelain` and `ls tests/out/runs` at the start; repeat all four at the
   end. The report's scope section quotes them.
2. Regenerate the two plans and the counts in the table above. Record every
   difference from this plan and from the opt-in survey's B.2 and B.5 tables.
3. Read the five commits since `2f23cad` (`git log --stat dd352cd..HEAD`)
   and note which inventory facts they changed: deleted wrappers, the
   `sbpl_allowdeny_consistency` command path, the refusal in `testlib.sh`,
   acceptance running the battery.

### Stage 1: account for the whole population

Build a working ledger in scratch, one row per canonical case, holding only
observed facts: command script and the function or branch that runs the
case; whether it starts PolicyWitness, a fixture program, a toolchain, or
nothing; what it reads before asserting (CLI envelope, independent file or
process observation, constructed input, a document, a build artifact); the
exact terminal paths (`test_pass`, `test_fail`, `test_skip`, early `exit 0`,
`test_require_pw`); and whether its assertions live in the shell, a Python
checker, Cargo or TestKit. The ledger is an instrument for completeness, not
a classification to publish. The report states, for every case, whether it
was inspected individually, inspected through its driver function, or
accounted for by pointer to a scenario table, and what remains unknown.

For the batch cases (`unit/rust.unit`, `integration/cli.integration`,
`runner_unit/pwrunner_core_unit_executable`) and the large Python checkers
(`preflight/check_build_provenance.py` with 68 methods, the `source_drift`
modules, `preflight/opt_in/build_refusals.py` whose single `def test_` drives
the build manifest's whole refusal list), the rule from the Question section
applies: list the groups (Rust test modules per file with the per-file counts
above; the 32 Swift `run*Tests` functions with their one-line registry
comments in `main.swift` and their `tk.group` names; `unittest` classes per
module; scenario tables), read the assertions of at least one representative
per group, and read every member that its name, comment or guard marks as a
different job. Preparation already saw such members: the two `#[ignore]` Rust
tests that replay Swift driver receipts; the `CWorkerTests` blocks guarded by
`workerExists()` that run the real worker beside constructed-input blocks in
the same executable; `ComparisonEvidenceTests`, driven row by row from
`tests/fixtures/comparison/matrix.json`; and the ownership table in
`tests/FAILURE-PROPAGATION-CONTRACT.md`, which already names Swift functions
as constructed, real-driver or encoder controls and is a map to verify, not
to adopt. Do not write an essay per method; do say which members were read.

Account separately for procedures that are not catalog cases: release
acceptance, the dispatcher's own artifact inspection (a check that runs once
as a gate before app-dependent cases and once more as `preflight/codesign.preflight`
through the shared read-only inspector), the `make` targets, the standalone
`cargo test` and `swift run` commands that `tests/README.md` lines 238-246
describe as local debugging, and the `records/performance/` equipment.

### Stage 2: investigate a varied set in depth

Choose from the observed differences in Stage 1, not from suite names or
default membership. The candidates below were selected during preparation
from facts already verified in source; the executor may substitute, with a
stated reason, but should keep at least ten and keep every counterexample.
For each, read the named files to the assertion lines, state exactly what a
pass supports and what it leaves open, and state what a failure would and
would not establish.

Status of the statements below. Paths, line numbers, equipment, commands and
quoted text were verified during preparation and may be relied on until the
executor's own re-read. Every statement about what a pass "establishes", "is
evidence about" or "asserts", whether written here or quoted from a registry
entry, README or script comment, is a hypothesis: the executor tests it
against the assertions and keeps, narrows or rejects it. A rejected
hypothesis that came from a repository document is a Stage 4 item; one that
came from this plan is simply corrected in the report. Preparation already
found one likely rejection, noted under candidate 5.

1. **One specimen, three claims.** `smoke/specimen_file_read_deny`
   (`tests/suites/smoke/pw_specimen_smoke.sh`), `witness_contract/happy_path_baseline`
   and `runner_use_c_worker/happy_default_allow`. All run one CLI specimen.
   The smoke case additionally compares the envelope's build stamp with the
   app's `Info.plist` and the response schema and worker ABI identity with
   `tests/lib/contract.py`; the baseline requires `attempt.rc == 0` and an
   `observed_path`; the C-worker case requires the comparison record and
   `test_overrides == null`. Determine what each pass establishes about the
   app, the contract documents and the kernel, and which of these the other
   two leave open. Note that the smoke case and the baseline are also the
   envelopes release acceptance reads for `runner_kind` (`release_accept.py`
   `PROVENANCE_ENVELOPES`). Compare `specimen_file_read_deny` with
   `specimen_file_read_deny_standard`, which share a fixture.

2. **The word "controls" and at least three jobs.** 42 case IDs contain
   `control` or `mutation`. Contrast `blackbox_menagerie/validation_controls`
   (drives the two checker CLIs with fabricated envelopes; needs no app;
   `tests/suites/blackbox_menagerie/checker_controls.py`),
   `runner_exec_dac/execute_permission_controls_spawn` (direct OS execution of
   the same helper with and without execute permission beside a PW run; the
   README says it establishes no sandbox attribution), `preflight/release_controls`
   (fake Apple replies and a fixture XPC host stub through the release
   tooling; no PolicyWitness run), `validator_bridge/protocol_controls` (whose
   README calls them "equipment controls, not evidence that the runner obeys
   its barrier") and `dispatcher/controls` (the dispatcher reconciling
   controlled reports). State what each pass is evidence about: a checker's
   sensitivity, an experimental baseline, release machinery, test equipment,
   or the harness.

3. **A documentation check inside a live suite.**
   `witness_contract/attempt_outcome_matrix_enforced`
   (`tests/suites/witness_contract/attempt_outcome_matrix_enforced.sh`)
   needs no equipment. It reads `PWRunnerAPI.swift`, `tests/COVERAGE.md` and
   `tests/suites/source_drift/check.py` with regular expressions, requires
   the string `AttemptOutcome` to occur in the drift checker, and compares
   enum constants with matrix rows. `source_drift/check.py`
   `check_attempt_outcomes_have_matrix_rows` (line 429) performs the same
   comparison mechanically through the Markdown reader. Determine whether
   the two are the same job, what the string-presence check establishes, and
   whether either can pass while the other fails. This is a candidate finding
   and a candidate overlap; report it as whichever the evidence supports.

4. **Batch cases as populations.** `unit/rust.unit` collapses 209 functions
   into one status and one log. `unit/rust.disposition_reds` and
   `unit/rust.byoxpc_reds` re-run 4 and 2 of those functions by exact name
   with `--include-ignored` and classify each outcome as green, expected red
   or unexpected (`tests/suites/unit/disposition_reds.sh` lines 32-57); their
   job is failure classification of tests that `rust.unit` also runs. At
   `87d5fb2` the `disposition_reds.sh` header (lines 7-12) still describes
   the case as non-default and red by design while the catalog makes it
   default and the four functions carry no `#[ignore]`; the opt-in survey
   reported this at `2f23cad` (C.1 item 1) and it is unchanged. Also read
   `tests/suites/unit/run.sh` lines 7-10: the `rust.fmt` branch inside
   `rust.unit`'s command cannot be selected under the dispatcher because
   `rust.fmt` has its own catalog command; confirm by reading how
   `suite_run.py` groups cases by command, and report what that branch is.
   For `runner_unit/pwrunner_core_unit_executable`, resolve a disagreement
   between two documents: `tests/FAILURE-PROPAGATION-CONTRACT.md` ("TestKit.run
   counts a guarded early return as passed", under "Coverage audit and
   acceptance ownership") and the opt-in survey B.5 ("the equipment guards
   throw a failure"). Read `workerExists()`, `bothBinariesExist()` and the
   `PW_LIFECYCLE_WORKER_FIXTURE` guards in `runner/Tests/PWRunnerCoreTests/`
   and state what a Swift block does when its equipment is absent and what
   the wrapper's `SKIP|FAIL` grep then sees. This decides what a passing
   Swift batch establishes about live-worker rows.

5. **Mutation controls: a pass is about a detector.**
   `runner_exec_inheritance/mutation_controls` (patches and rebuilds the C
   worker, then requires the ordinary assertions to fail with specific leak
   evidence), `witness_contract/order_barrier_mutations`,
   `runner_unit/exec_reader_mutations`, `runner_unit/reaped_ack_mutation`,
   `runner_unit/host_setup_oracle_sensitivity`, and the planner controls
   inside `source_drift/runner_source_manifests_agree`
   (`check_planner.py`, which mutates disposable checkouts). Establish from
   the scripts how each distinguishes "the detector missed the mutation" from
   "the mutation did not build" or "equipment failed"; the registry says of
   the barrier control that a build, signing, transport or equipment error
   never counts as detecting a mutation. Test the hypothesis that a pass
   establishes nothing about PolicyWitness directly, only the sensitivity of
   the baseline assertions the case pairs with. The barrier case is a likely
   counterexample: its registry entry requires the unmodified component and
   signed CLI controls to pass before the mutants run, and a passing
   unmodified control is an observation of PolicyWitness made inside a
   mutation case. Read `tests/suites/witness_contract/opt_in/mutations.sh`
   and its checker to see whether that observation is asserted in its own
   right or is only a precondition for the mutant comparisons, and report
   which.

6. **Passing by observing a counterexample.**
   `runner_exec_lifecycle/closed_streams_leader_exit`,
   `runner_exec_inheritance/closed_worker_stderr`,
   `runner_exec_inheritance/launch_inventory`,
   `runner_c_worker_harness/native_clock` (whose registry entry says the
   neighbour's "intermittent failure need not recur in a given run"),
   `witness_contract/path_query_observations`, `path_query_integrated` and
   `sandbox_extensions_native/feasibility`. The registry calls these
   characterizations that assert no product behavior; that is the registry's
   claim, to be tested. Read each checker to find what does fail it. If the
   hypothesis holds, the claim a pass supports is that an observation was
   recorded on this host under these conditions, and the report says which
   claims it does not support; if a checker asserts a product property after
   all, the report says so and treats the registry wording as a Stage 4
   item.

7. **Tests of the instrument.** The `dispatcher` suite (6 cases, no app),
   `shell_helpers` (8), `run_capture/controls`, `exec_fixture/controls`,
   `source_drift` (8), the preflight release and provenance controls,
   `blackbox_e2e/checker_controls`, `runner_unit/build_receipt_controls`.
   None runs PolicyWitness. Select two or three and state what a pass
   establishes about the harness, builder, release tooling or generators, and
   how a failure there changes the reading of every other result in the same
   run. Include `preflight/codesign.preflight` and the dispatcher's gate as
   one check appearing twice.

8. **Prediction unavailable, attempt observed.** The four `runner_filter_*`
   suites share `tests/lib/unavailable_prediction.py`. `runner_filter_local_name`
   plans a `local_name` filter while the worker performs a global bootstrap
   lookup, and its script comment says it does not establish a matched
   local-name enforcement operation; the two IOKit suites use a file-open
   placeholder and their READMEs say they do not establish IOKit enforcement.
   The scripts' own account is that a pass establishes the unavailable-query
   contract and that the named attempt completed; test that against
   `tests/lib/unavailable_prediction.py` and the per-suite expectations, then
   state what the pass establishes and what the near-identical scripts in
   two suites add to each other.

9. **Independent observation before decoding.**
   `run_effects/file_actions_have_exact_effects` and
   `sbpl_allowdeny_consistency/sbpl_allowdeny_v1` read target bytes and
   metadata themselves before opening the envelope;
   `runner_c_worker_harness/unlink_deny` has the harness own the target and
   report `target_exists_after`. Contrast with cases that assert only
   envelope fields. State how the evidence for "the kernel denied" differs
   between an errno in the envelope and a surviving file, and which cases
   rest on which.

10. **A liveness check with a fixed window.**
    `runner_mach_service_liveness/pwrunner_survives_mach_service_launch`
    launches the host with `--mach-service`, sleeps 0.5 s, and reads the
    process state (`tests/suites/runner_mach_service_liveness/run.sh`). It
    names the regression it guards (an abort under `xpc_main`). State what a
    pass establishes and record the runtime observation that would settle
    whether a late abort can pass: a measured abort latency for the broken
    variant. Do not run it.

11. **The one declared skip.** The menagerie's `annotated_mismatch_absent`
    (`tests/suites/blackbox_menagerie/run.sh` maps `run_case.py` exit 3 to
    `test_skip`; the README says the skip is taken only after every evidence
    check passes). Read `run_case.py` and `validate_run.py` to state what a
    skip means about the OS, the fixture annotation and the app, and how the
    dispatcher counts it. The 8 BYOXPC copies share the script under a
    different suite name and runner context.

12. **Same constructed facts, three readers.** The corpora under
    `tests/fixtures/contract/` (`phase_collection.json`,
    `exec_observation.json`, `evidence_types.json`, `path_diagnostics.json`)
    are read by Swift tests, Rust tests and `tests/lib/consumer.py` or the
    lifecycle oracle. State what agreement among readers establishes and what
    it does not (the truth of the constructed facts), and locate the live
    cases that supply the corresponding real observations.

13. **Same script, different input or context.**
    `runner_apply_isolation_v2` and `v3` (SBPL version differs);
    `runner_filter_iokit_registry_entry_class` and `runner_filter_iokit_user_client_class`
    (filter name differs); the 10 `runner_byoxpc` specimens that run the
    smoke, menagerie and BBX scripts under `PW_TEST_SUITE_OVERRIDE` with an
    installed external runner. State what the second copy adds in each pair.

### Stage 3: follow relationships

Record a relationship only where it changes what a result means. Known
pairings to trace, with the files that implement them:

- Positive controls as dependencies: `launch_inventory` on
  `contaminated_worker` (catalog `depends_on`; `tests/suites/runner_exec_inheritance/run.sh`).
- Installation as dependency: eleven `runner_byoxpc` leaves on
  `runner_install`; shared session and cleanup ownership in
  `tests/fixtures/byoxpc/session.py`.
- Mutation controls and the baseline assertions they prove sensitive
  (candidate 5).
- Checker controls and the live cases that use the same checker:
  `blackbox_e2e/checker_controls` and every consumer of `tests/lib/blackbox.py`
  and `tests/lib/consumer.py` (listed in `tests/README.md` "Black-box
  validation"); `run_effects/checker_controls` and `effects.py`;
  `runner_filter_sysctl_name/checker_controls` and the filter suites.
- Ownership tables: `tests/FAILURE-PROPAGATION-CONTRACT.md` "Ownership" and
  "Coverage audit and acceptance ownership", `tests/COVERAGE.md`'s two
  matrices and the drift rule that holds them equal to the Swift enums.
- Change-triggered controls: `tests/AGENTS.md` requires
  `witness_contract/order_barrier_mutations` after wait, release or
  eligibility changes; the registry's "When to run" entries.
- The dispatcher's artifact inspection and `preflight/codesign.preflight`
  (one inspector, two roles); the dispatcher's sleep record and TestKit's
  per-block sleep line (one rule, two implementations).
- Release acceptance and the offline cases that exercise it:
  `preflight/release_controls`, `release_deadline_controls`,
  `release_publish_controls`, `release_rotation_controls` against
  `tests/lib/release_*.py`.

### Stage 4: documentation against implementation

Compare, for the investigated cases and for any case whose description reads
as a broader claim than its script makes:

- Catalog `description` fields (some run to a paragraph, for example
  `preflight/build_provenance_controls`).
- The suite-coverage table in `tests/README.md` and each suite README's
  stated limits; the Tier column is historical and operational, not a
  premise.
- `tests/COVERAGE.md` rows and notes, including "primary coverage" naming.
- The registry `tests/OPT_IN_TESTS.md` entries' purpose and equipment.
- `docs/ARCHITECTURE.md` "How the system verifies itself" and the document
  graph, whose figure caption states that "whether a test asserts the row is
  not verified".
- In-script comments and `test_pass` messages, which are the words a reader
  of `run.json` actually sees (for example `disposition_reds.sh`).

Report each discrepancy with the two texts and the implemented check, and
say whether it changes the interpretation of a pass or a failure. Separate
confirmed observations from unresolved intent.

### Stage 5: consult history selectively

Use `git log -S`, `git blame` and `git show <rev>:<path>` only to settle a
question about current purpose or an apparent discrepancy. Questions already
worth a look: the origin of `runner_mach_service_liveness` and the regression
it names; when `attempt_outcome_matrix_enforced` was added relative to the
drift rule; why the two Rust tests carry `#[ignore]` (the attribute text
explains the mechanism; the commit explains the choice); the prior survey's
D.3 account of the red convention, re-read only as far as `disposition_reds.sh`
needs. Distinguish original intention, present documentation, implemented
checks and inference in every historical statement.

### Stage 6: write the report

Destination `records/tests/TEST-WORK-SURVEY-REPORT.md`, beside the opt-in
survey. `records/README.md` places investigations there, and
`records/AGENTS.md` permits inbound links to a record only from its associated
plan, which is this file; the report may link outward to source, tests and
documentation. Files under `records/` are excluded from the drift suite's
Markdown command rule (`check.py` line 173), but keep every local link
resolvable and use no reference-style links.

Structure, following the commission:

1. Scope and coverage: revision, enumeration method and commands, levels of
   granularity, the population accounted for with the inspected, grouped and
   unknown portions stated, and limits of inspection (static counts, no
   execution, BYOXPC and signing cases read only).
2. Representative investigations: the Stage 2 accounts, each citing paths,
   symbols and lines, with "a pass supports" and "a pass leaves open" stated
   separately, and failure meaning stated with the dispatcher's and the
   case's own vocabulary.
3. Consequential contrasts and overlaps, including cases that resist
   characterization.
4. Relationships from Stage 3.
5. Documentation versus implementation from Stage 4.
6. Open questions, each with the evidence that would settle it and, for
   runtime questions, the proposed observation.

Write descriptively. A sentence that reads as a recommendation ("should",
"ought", "could be merged") is rewritten as an observation or removed. A
finding is a statement about what a check does and does not do, cited to its
line.

## Consequential choices settled here

1. **Report location** is `records/tests/`, following the opt-in survey and
   the records guidance. The report is the only file the survey adds.
2. **Unit of accounting** is the canonical catalog case, with the batch cases
   expanded one level by static count and scenario tables accounted for by
   pointer. Selection flags, suite membership and the `opt_in` group are
   recorded as operational facts of each case, not as the frame.
3. **No compilation for counting.** Rust and Swift populations are static
   counts and are labelled as such; a block inside a loop or helper would not
   be counted, and the opt-in survey's B.8 states the same limit.
4. **Equipment-sensitive cases are read, not run.** Nothing in the report
   claims a case passes on this machine. Retained runs under `tests/out/runs/`
   (local only; the committed index is `tests/RETAINED.json`) may be cited
   for the date of a past execution, never for a present result.
5. **The commission's prohibitions are honoured literally.** The ledger's
   free-text columns are not turned into categories in the report; the report
   groups cases only to say what was inspected.
6. **"Every test" means every case and every group.** Complete accounting is
   at the catalog case; inside batch cases the test group is the unit, with
   representatives and marked members read (Question section and Stage 1).
7. **Meaning statements are hypotheses.** Stage 2's accounts of what a pass
   establishes, including those quoted from repository documents, are tested
   against assertions and may be rejected (Stage 2, "Status of the
   statements").
8. **The footprint claim is narrow.** Tracked content unchanged and no
   mutating command run, as `git status --porcelain` and the command record
   show; not a byte-level inventory of ignored paths (Verification).

Routine for the executor: the ledger's exact columns, the order of
investigations, how many lines of a checker to quote, and the report's
section lengths.

## Verification of the survey

The checks establish that the report is faithful and state exactly what they
show about the survey's footprint, not merely that the report was written.

- **Revision and footprint.** The report quotes `git rev-parse HEAD`, and
  `git status --porcelain` at the end lists only the report. That establishes
  that no tracked file's content and no untracked path under the checkout
  changed. It establishes nothing about ignored paths (`tests/out/`,
  `controller/target/`, `runner/.build/`, `builddir`, `.tmp/`). For those,
  the evidence is the executor's record of commands, which contains only the
  permitted discovery commands, plus one cheap check: `ls tests/out/runs`
  before and after are identical, which detects the forbidden act most likely
  to happen by accident, a case execution. The report words the claim at that
  strength: the survey ran no mutating command and left the tracked tree
  unchanged. It does not claim that no byte under the checkout changed, and
  no fuller inventory is taken.
- **Regenerable counts.** Every count in the report names the command or
  parse that produced it; the executor re-runs each at the end and the
  numbers agree. The two `--list` plans are regenerated last and compared
  with the Stage 0 copies with `diff`.
- **Cited assertions.** Every "a pass establishes" sentence cites a file and
  the line of the assertion or terminal call it rests on, and a reader can
  open the file at the stated revision and find it. Before finishing, the
  executor re-reads each cited line against `git show 87d5fb2:<path>` or the
  then-current head and corrects drift.
- **Separated claims.** Each investigation has operational facts (selection,
  equipment, side effects, artifacts, result handling) in one place and
  interpretive claims in another; a reviewer can find the boundary.
- **Prohibitions.** A final pass removes any bucket, label, template,
  release judgment or refactoring proposal that crept in; findings remain as
  observations.
- **Misleading completion.** A report that accounts for every case by suite
  description alone has not done Stage 1; the coverage section must say,
  per case, which inspection level it received, and a count of cases at each
  level must sum to 235 (or the re-established total).

## What would require reconsidering this plan

- The re-established population differs from 235 cases or 196 defaults, or
  `tests/run.sh --list` is found to write anything; Stage 0 then records the
  difference and the method proceeds against the new facts.
- A material question cannot be answered without executing a case. The
  report records the proposed observation and stops there; this plan does
  not authorize the execution, and a separate plan would.
- Reading reveals a defect that makes a default case's pass meaningless.
  Report it as a finding with its evidence; do not repair it or propose the
  repair.

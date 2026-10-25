# Test work survey: plan

A read-only survey of what PolicyWitness's tests and test-like procedures
do, what a passing result establishes, what a failing result establishes or
fails to establish, and where activities that share the name *test* are doing
materially different jobs or where apparently different activities do the
same job. The deliverable is one report at
`records/tests/TEST-WORK-SURVEY-REPORT.md` in the original checkout. The
survey examines a recorded commit in a detached worktree; later commits to
`main` do not change its subject.

This plan follows [Planning a change](../CONTRIBUTING.md#planning-a-change)
and the [test working guidance](AGENTS.md). The report belongs in
`records/tests/` under `records/README.md` and `records/AGENTS.md`. It may
link outward to source, tests and documentation; repository links to it may
come only from its associated plan. Keep local links resolvable and use no
reference-style links.

## Question

For every test and test-like procedure at the examined revision, determined
from its implementation and the assertions it actually makes:

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

Complete accounting is at the catalog case and, inside batch cases, at the
test group. Stage 1 specifies representative assertion reading within each
group and disclosure of which members were read or grouped on names alone.
The survey does not promise an assertion-by-assertion account of every
function.

Write a descriptive report without a taxonomy, per-test metadata or labels,
release membership judgments or refactoring proposals. Group cases only to
say what was inspected. Concrete defects may be reported as findings with
their evidence, without repairing them or proposing repairs.

## Boundaries made operational

- **Pinned inspection.** Read sources, documentation and catalog entries,
  and run discovery commands, in a detached worktree at the recorded full
  commit. Create it under a session scratch directory outside the original
  checkout. Keep working notes, parsed plans, ledgers and scripts beside the
  worktree, outside both trees. The survey writes only its report in the
  original checkout's working tree.
- **Worktree lifecycle.** Creating and removing this detached worktree with
  `git worktree add --detach` and `git worktree remove` is authorized,
  including the shared Git metadata those commands update. This follows
  the disposable-checkout guidance in `tests/AGENTS.md`. The original
  checkout need not be clean or remain at the same revision; preserve other
  authors' changes.
- **Permitted discovery commands.** `tests/run.sh --list` with any selectors
  prints a plan and returns before taking the checkout lock
  (`tests/lib/test_cli.py` lines 169 and 210-212; `tests/README.md` lines
  71-78). Use read-only Git, file-reading, search and comparison commands,
  and Python with `-I -B` for static parsing. Loading
  `tests/lib/test_cli.py`'s `catalog()` and `select()` is permitted because
  they only read the catalog and preserve suite-level inheritance of
  `default`, `requires`, `command` and `context`.
- **Not permitted.** `cargo test -- --list` and `swift run` compile into the
  managed `controller/target/` and `runner/.build` and take the checkout
  lock; they are builds, not discovery. Rust and Swift populations are
  counted statically (attributes and `tk.run(` call sites) and labelled as
  static counts; dynamic multiplicity from loops or helpers is not measured.
  Do not execute catalog cases, builds or `tests/run.sh --prune`.
- **Runtime questions.** Where a material question needs an execution (for
  example how long a process takes to abort), the report records the
  proposed observation, the case it would inform and why static reading
  cannot settle it. It does not run it. Resolving a runtime question by
  execution requires a separately authorized plan.
- **Retained evidence.** Runs under the original checkout's
  `tests/out/runs/` are local only and are not copied into the detached
  worktree. Read the committed index, `tests/RETAINED.json`, at the examined
  revision. Identify any run dates read from the original checkout by their
  location and the date of inspection, separately from the pinned source
  evidence. Cite them only for the date of a past execution, never as a
  present result. The survey makes no claim that a case passes on this machine.
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

## Reading and evidence standards

### Claims and investigation notes

Treat claims about what a result establishes, whether from this plan, a
registry, a README or a script comment, as hypotheses to keep, narrow or
reject against the assertions. Record a rejected documentation claim with
the text and implemented check that contradict it; correct a rejected plan
hypothesis in the report.

For each investigation, retain paths, symbols and assertion lines at the
examined revision. Keep operational facts (selection, equipment, side
effects, artifacts and result handling) together and separate from the
claims about what a pass supports, what it leaves open, and what a failure
would or would not establish. Use the dispatcher's and case's own outcome
vocabulary. These notes supply the report without a second collection pass.

### Documentation and history

Read the relevant descriptions alongside each case's assertions, so that
discrepancies can inform the investigation and its selection. Sources are:

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

Use `git log -S`, `git blame` and `git show <rev>:<path>` when a question
about current purpose or a discrepancy needs historical evidence. Relevant
leads include the regression named by `runner_mach_service_liveness`, the
relative introduction of `attempt_outcome_matrix_enforced` and the drift
rule, the choice to ignore the two Rust tests, and the red convention
behind `disposition_reds.sh`. Consult only the history needed to answer the
question. Distinguish original intention, present documentation,
implemented checks and inference.

### Overlap findings

Saying that two checks do the same job requires more than finding the same
proposition in both. For each of the two, the report states: the proposition
asserted, cited to the assertion; the inputs read (the same file, fixture or
live run, or different ones); the implementation path (a regular expression
over a source file against the Markdown reader's parse, say, or the CLI
against the direct ABI); the execution facts (suite, default membership, equipment, what else
runs in the same invocation); and the failures each can detect that the
other cannot, found by asking what change to the checked subject would fail
one and pass the other. "Same job" is warranted when the propositions agree
and no such differential failure is found. When one is found, the report
records a contrast with a shared proposition, not an overlap. In either case
the report says whether the second implementation is independence by design,
which this repository documents for several readers (the consumer beside the
Swift encoder, the lifecycle oracle beside the disposition reader, checker
controls that import neither the checker nor production code), or an
undocumented duplicate. An overlap finding describes a relation; it does not
say that either check is redundant or that one should be removed.

### Counterexamples and selection

Choose at least ten investigations from the differences observed while
accounting for the population. Preserve candidates 3, 4 and 5: the
documentation check inside a live suite, guarded Swift block reporting, and
product observations inside mutation cases. Other candidates may be
substituted with a stated reason; suite names and default membership do not
determine the selection.

A counterexample is a case whose assertions contradict a hypothesis about a
kind of work, whether the hypothesis comes from this plan, a repository
document or the investigation. For each distinct contradiction found during
population accounting or in-depth reading, investigate one example and list
the other cases showing it by ID, one line each, in that investigation.
Contradictions are distinct when they contradict different hypotheses, or
the same hypothesis by different mechanisms. Selection is complete when at
least ten investigations are written and every distinct contradiction found
has its investigated example.

### Relationships

Trace these relationships while reading the cases and their shared helpers.
Record a relationship only where it changes what a result means:

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

## Population reference

The reference counts were taken at revision
`87d5fb2d08d430ffabde6d6a3316257e8190e6c3` and re-derived unchanged at
`f1e96a2e63ac8aa6f02c67a63e208a70e7aecfa4` from the two `--list` plans; every
commit between those revisions changed only this plan file. The counts hold
at any later examined revision whose `git diff --stat 87d5fb2..<revision>`
names only this file; if anything else changed, treat them as historical.
Stage 0 re-derives them regardless; each row names its source.

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

### Result recording

Case scripts require the dispatcher's context: `testlib_init` and
`test_selected` in `tests/lib/testlib.sh` refuse direct invocation, and
`shell_helpers/controls` asserts that refusal in
`tests/suites/shell_helpers/check.py` line 133.

Describe result recording before interpreting outcomes. A case ends with
`test_pass`, `test_fail` or `test_skip`
(`tests/lib/testlib.sh` lines 269-292), each writing a terminal event and a
`report.json`; `test_fail` exits 1 immediately. The dispatcher
(`tests/lib/suite_run.py`) separately produces `unrun` for missing equipment
or a failed dependency, the harness errors `unexpected_skip`, `unrun_case`,
`missing_report`, `reused_case`, `interpreter_mismatch`,
`build_tree_in_evidence` and `scratch_retained`, an artifact-integrity
failure independent of case statuses, and a `system_sleep_ms` record whose
nonzero value marks a failure as not creditable product evidence without
changing its status (`tests/suites/dispatcher/README.md`, "Contract"). Batch
cases have coarser mappings: `unit/rust.unit` passes only when
`cargo test --bins` exits 0 and retains one log;
`runner_unit/pwrunner_core_unit_executable` fails on a nonzero exit, on any
`SKIP` or `FAIL` line in the Swift log, or on a missing summary line
(`tests/suites/runner_unit/run.sh` lines 33-52). These are the implemented
vocabularies for "failure of test machinery" and "inconclusive"; the report
uses them rather than inventing others.

## Method

### Stage 0: establish the state

1. Record the original checkout's absolute path and capture its full
   `git rev-parse HEAD` value once as the examined revision. Create a scratch
   directory outside that checkout, reserving `source/` for the detached
   worktree and `notes/` for the command record, parsed plans, count scripts
   and investigation notes. Record commands as they are used.
2. Create the worktree with
   `git -C <original-checkout> worktree add --detach <scratch>/source <full-revision>`.
   Use the captured hash even if the original checkout's `HEAD` has moved.
   In the new worktree, record `git rev-parse HEAD`, `git log -1 --date=iso`
   and `git status --porcelain`; verify the revision matches and status is
   clean. Record the listing of its `tests/out/runs`, or its absence. The
   report's scope section quotes these observations. All subsequent source
   reads, imports, history queries and enumeration use this worktree;
   retained-run dates and the final report destination are the exceptions
   described in Boundaries.
3. Read `tests/README.md`, `tests/AGENTS.md`, `tests/fixtures/README.md` and
   the dispatcher and result-recording code named above before interpreting
   individual cases. Use `runner/AGENTS.md` for runner tests and native helpers.
4. From the detached worktree, save the two selection plans under `notes/`.
   Use an environment without inherited `PW_*` settings or `PYTHONOPTIMIZE`,
   and retain the returned configuration, including its worktree paths:

   ```sh
   ./tests/run.sh --list
   ./tests/run.sh --all --list
   ```

   Re-derive the population reference counts and record each command or
   parse used. Record differences from the reference and proceed with the
   population at the examined revision. Use `catalog()` and `select()` for
   inherited catalog fields and static source counts for batch populations.
5. After establishing that inventory, put older accounts in revision
   context before using their claims. The
   [opt-in survey](../records/tests/OPT-IN-REPORT.md) examined
   `2f23cad3cf5ac10a4d87f75d9bd1a2c2a026bc09`. Review
   `git log --oneline 2f23cad..<examined-revision>` and the intervening diffs
   that affect the claims being compared, including its B.5 claim used in
   candidate 4. Treat older counts and claims as comparison texts to
   re-verify against the pinned implementation, not as inventory inputs.
   Read only the history relevant to those comparisons.

### Stage 1: account for the whole population

Build a working ledger in scratch, one row per canonical case, holding only
observed facts: command script and the function or branch that runs the
case; whether it starts PolicyWitness, a fixture program, a toolchain, or
nothing; what it reads before asserting (CLI envelope, independent file or
process observation, constructed input, a document, a build artifact); the
exact terminal paths (`test_pass`, `test_fail`, `test_skip`, early `exit 0`,
`test_require_pw`); and whether its assertions live in the shell, a Python
checker, Cargo or TestKit. Carry over selection flags, suite membership,
equipment, dependencies and runner context from the catalog plan as
operational facts. Record case-specific side effects and artifacts alongside
them. The ledger is an instrument for completeness, not a classification to
publish. The report states, for every case, whether it was inspected
individually, inspected through its driver function, or
accounted for by pointer to a scenario table, and what remains unknown.

For the batch cases (`unit/rust.unit`, `integration/cli.integration`,
`runner_unit/pwrunner_core_unit_executable`) and the large Python checkers
(`preflight/check_build_provenance.py` with 68 methods, the `source_drift`
modules, `preflight/opt_in/build_refusals.py` whose single `def test_` drives
the build manifest's whole refusal list), enumerate the groups: Rust
`mod tests` modules per source file with static counts; Swift `run*Tests`
functions with their registry comments in `main.swift` and `tk.group` names;
Python `unittest` classes per module; and checker scenario tables. Read the
assertions of at least one representative per group and every member whose
name, comment or equipment guard marks a different job. Record per group
which members were read and which were grouped on names alone.

Members requiring separate attention include the two `#[ignore]` Rust tests
that replay Swift driver receipts; the `CWorkerTests` blocks guarded by
`workerExists()` that run the real worker beside constructed-input blocks in
the same executable; `ComparisonEvidenceTests`, driven row by row from
`tests/fixtures/comparison/matrix.json`; and Swift functions identified as
constructed, real-driver or encoder controls in the ownership table in
`tests/FAILURE-PROPAGATION-CONTRACT.md`. Verify that table's descriptions
against the assertions.

Account separately for procedures that are not catalog cases: release
acceptance, the dispatcher's own artifact inspection (a check that runs once
as a gate before app-dependent cases and once more as `preflight/codesign.preflight`
through the shared read-only inspector), the `make` targets, the standalone
`cargo test` and `swift run` commands that `tests/README.md` lines 238-246
describe as local debugging, and the `records/performance/` equipment.

### Stage 2: investigate a varied set in depth

Apply the selection and evidence standards to these candidates and the
differences found in Stage 1. Read the selected cases to their assertions,
tracing relevant relationships and documentation in the same investigation.

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
   comparison mechanically through the Markdown reader. Determine, under the
   overlap standard, whether the two are the same job: what the
   string-presence check establishes, and what change to the enum, the
   matrix or the checker would fail one and pass the other.

4. **Batch cases as populations.** `unit/rust.unit` collapses 209 functions
   into one status and one log. `unit/rust.disposition_reds` and
   `unit/rust.byoxpc_reds` re-run 4 and 2 of those functions by exact name
   with `--include-ignored` and classify each outcome as green, expected red
   or unexpected (`tests/suites/unit/disposition_reds.sh` lines 32-57); their
   job is failure classification of tests that `rust.unit` also runs. The
   `disposition_reds.sh` header (lines 7-12) describes the case as non-default
   and red by design while the catalog makes it
   default and the four functions carry no `#[ignore]`. Record this
   discrepancy and the unselectable `rust.fmt` branch in
   `tests/suites/unit/run.sh` lines 7-10: the branch inside
   `rust.unit`'s command cannot be selected under the dispatcher because
   `rust.fmt` has its own catalog command and `suite_run.py` gives every
   standard-context case its own invocation. Only consecutive BYOXPC cases
   sharing a command are combined (`execute`, lines 387-393).
   For `runner_unit/pwrunner_core_unit_executable`, resolve a disagreement
   between two documents: `tests/FAILURE-PROPAGATION-CONTRACT.md` ("TestKit.run
   counts a guarded early return as passed", under "Coverage audit and
   acceptance ownership") and the opt-in survey B.5 ("the equipment guards
   throw a failure"). Read `workerExists()`, `bothBinariesExist()`
   and the `PW_LIFECYCLE_WORKER_FIXTURE` guards in `runner/Tests/PWRunnerCoreTests/`
   and state what a Swift block does when its equipment is absent and what
   the wrapper's `SKIP|FAIL` grep then sees. This decides what a passing
   Swift batch establishes about live-worker rows.

5. **Mutation controls and their unmodified baselines.**
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
   never counts as detecting a mutation. The barrier case requires unmodified
   driver, harness and signed CLI controls to pass before the mutants run
   (`tests/suites/witness_contract/opt_in/mutations.py`, `main`,
   `driver`, `harness_control` and `cli_control`). Account separately for
   the product observations required by those baseline assertions and the
   detector sensitivity established by rejecting the mutants. Trace the
   corresponding baseline requirements in the other mutation cases.

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
   claims it does not support. Record any product assertion that contradicts
   the registry wording as a documentation discrepancy.

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
    installed external runner. State what the second copy adds in each pair,
    under the overlap standard.

### Stage 3: write the report

Write `records/tests/TEST-WORK-SURVEY-REPORT.md` in the original checkout
from the collected evidence. Check the destination before writing so that
concurrent report edits are preserved. State the full examined revision and
use repository-relative source paths with citations tied to that revision;
the report describes the pinned tree even if `main` has advanced.

1. Scope and coverage: examined revision, enumeration commands, levels of
   granularity, per-case inspection accounting and per-group members read
   or grouped on names alone, plus unknowns and limits (static counts, no
   execution, BYOXPC and signing cases read only).
2. Representative investigations: paths, symbols and assertion lines, with
   operational facts separate from what a pass supports and leaves open,
   and failure meaning stated in the implemented vocabulary.
3. Consequential contrasts and overlaps, each overlap meeting the evidence
   standard above, including cases that resist characterization.
4. Relationships that affect the meaning of results.
5. Documentation versus implementation, with both texts and the implemented
   check for each discrepancy.
6. Open questions, each with the evidence that would settle it and, for
   runtime questions, the proposed observation.

Write findings as observations cited to their assertions. Remove
recommendations, release judgments and refactoring proposals. The ledger's
exact columns, investigation order, quotation lengths and report section
lengths are routine choices for the executor.

## Verification of the survey

- **Revision and footprint.** Before removing the detached worktree, repeat
  its Stage 0 revision, status and run-directory observations. Its `HEAD`
  must still equal the recorded commit, its status must remain clean, and
  its run-directory listing or absence must agree. These observations
  establish unchanged tracked content, no visible untracked paths and no
  added or removed run directories in that worktree. They do not inventory
  ignored files or establish absence of transient writes. The command
  record accounts for worktree setup and removal, discovery commands,
  scratch writes and the report written to the original checkout. Review
  that report's diff separately from concurrent changes there. Do not
  require the original checkout to remain clean or at the examined revision,
  or attribute another author's changes to the survey.
- **Regenerable counts.** Every count in the report names the command or
  parse that produced it; re-run each in the pinned worktree and require the
  numbers to agree. Regenerate the two `--list` plans there with the same
  environment and compare them with the Stage 0 copies using `diff`.
- **Cited assertions.** Every "a pass establishes" sentence cites a file and
  the line of the assertion or terminal call it rests on, and a reader can
  open the file at the stated revision and find it. Before finishing, the
  executor re-reads each cited line at the examined revision with
  `git show <rev>:<path>` and corrects citation errors.
- **Separated claims.** Each investigation has operational facts (selection,
  equipment, side effects, artifacts, result handling) in one place and
  interpretive claims in another; a reviewer can find the boundary.
- **Prohibitions.** A final pass removes any bucket, label, template,
  release judgment or refactoring proposal that crept in; findings remain as
  observations.
- **Misleading completion.** A report that accounts for every case by suite
  description alone has not done Stage 1; the coverage section must say,
  per case, which inspection level it received, and a count of cases at each
  level must sum to the re-established total. Each batch group states which
  members were read and which were grouped on names alone. At least ten
  investigations are present, including candidates 3, 4 and 5 and one
  example for every distinct contradiction found; any additional cases
  showing the same contradiction are listed by ID.
- **Worktree cleanup.** After verification and preservation of the report
  and notes, remove only the owned detached worktree with
  `git -C <original-checkout> worktree remove <scratch>/source` and record
  the outcome. If unexpected changes or test output exist, retain the
  worktree and follow `tests/AGENTS.md` rather than forcing removal or
  bypassing evidence cleanup rules.

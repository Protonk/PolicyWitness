# Implementation account

Consumer: the reviewer accepting the
[implementation plan](../../tests/suites/source_drift/DOCUMENT-DRIFT-IMPLEMENTATION-PLAN.md).
Links into `tests/out/` are gitignored, local-checkout evidence.

## Baseline

The credited baseline is the plan's fresh dispatcher run
`tests/out/runs/drift-plan-investigation-20261027-02` (ID
`20261027T175448Z_a3635ceb`): eight `source_drift` cases passed, zero
recorded sleep, 349.098 seconds summed from case reports, Python 3.14.9, Meson
1.12.1, Apple clang 21.0.0.

Evidence-reuse decision: the implementation started from commit `6b465f5`,
whose only differences from the baseline revision `1612eb5` are two lines in
`CONTRIBUTING.md` and the plan documents under `tests/suites/source_drift/`.
No executable source, fixture, helper or catalog entry differs, so the
baseline was reused rather than rerun. This is a reviewed exception under the
test working rules: the delta is the four files `git diff --name-status
1612eb5 6b465f5` lists, and none is read by a case other than as a document
in the command-document scope, where the three plan files change the scanned
set by two removals and one addition (the plan documents hold no case command).

Baseline discovery measurements (single read-only helper samples, warm
filesystem, from the baseline run's `investigation/report.json`):

| Observation | Baseline |
| --- | --- |
| Markdown discovery | 7.116 s; 222,124 directory listings, 214,664 under `tests/out`; 101 documents |
| Shell discovery | 6.802 s; 214,946 listings, 214,664 under `tests/out`; 149 scripts |
| Reading/parsing the documents, empty reader cache | 0.328 s |

## Stage 1: shared tree access and pruned discovery

Change: `docs/repository_tree.py` (explicit root, pruned top-down walk, named
scopes `COMMAND_DOCUMENTS` and `TEST_SHELL_SCRIPTS`, typed read failures,
content-keyed parse reuse for one `Tree`, declared-input expansion).
`check.py::markdown_documents(tree)` and `direct_python.py::shell_scripts(root)`
use the scopes; the planner fixture copies the module. Inventory controls:
`check_planner.py::inventory_controls` (scenario `inventory-scopes`) and
`DirectPythonTests.test_inventory_is_a_pruned_walk_of_the_shell_scope`.
The prose/link scope (`generators.py::scanned_documents`) and generator-owned
documents are unchanged; they do not walk the checkout.

Selected-set agreement: the stage-1 Markdown inventory of the real checkout
equals the baseline run's retained inventory except for the three plan
documents that changed after the baseline revision; the shell inventory is
identical (149 scripts). See `comparison` in the measurement report below.

Discovery after stage 1 (read-only helper, three samples each, warm
filesystem, taken under the checkout lock after the credited run on commit
`e2462f9` with a clean working tree; the helper script, selected
inventories and `report.json` are retained in
`tests/out/runs/drift-cost-stage1-04/investigation/`):

| Observation | Baseline | Stage 1 (3 samples) |
| --- | --- | --- |
| Markdown discovery listings | 222,124 (214,664 under `tests/out`) | 177 (0 under `tests/out`) |
| Markdown discovery seconds | 7.116 | 0.003, 0.003, 0.003 |
| Markdown documents selected | 101 | 100 (two plan documents removed, one added since the baseline revision) |
| Shell discovery listings | 214,946 (214,664 under `tests/out`) | 141 (0 under `tests/out`) |
| Shell discovery seconds | 6.802 | 0.003, 0.003, 0.003 |
| Shell scripts selected | 149 | 149, identical set |
| Reading/parsing the selected documents, empty reader cache | 0.328 | 0.340 |

`tests/out` held 413,844 entries at measurement time; the stage-1
walker never lists it, so its population no longer affects discovery time.
These remain helper samples, not case durations or thresholds. An earlier
measurement of the uncommitted stage-1 working tree was superseded by this
one and removed with its run.

Also in this stage, ahead of the stage-2 rule table: the plan's required
missing-rule controls were added to the planner as real-checker scenarios
(`rule_gap_scenarios` and the Baseline-membership registry scenarios). The
`control-map.json` rows with disposition `added` list them. The planner now
runs 225 receipts per case (204 before).

Credited run: `tests/out/runs/drift-cost-stage1-04` (ID `20261027T203111Z_728f49ca`), both cases
passed with zero recorded sleep, on commit `e2462f9` with a clean working
tree. The planner wrote 225 receipts. Case durations are shown
beside the baseline as context only; they are single runs, and the planner's
whole-checker starts dominate the first case.

| Case | Baseline ms | Stage 1 ms | Recorded sleep ms |
| --- | ---: | ---: | ---: |
| `runner_source_manifests_agree` | 188679 | 186350 | 0 |
| `direct_python_start` | 25151 | 11356 | 0 |

Superseded and uncredited runs, removed from `tests/out` on 2026-10-27 after
review, with their run IDs kept here: `drift-cost-stage1-03` (ID
`20261027T201614Z_dc800ffe`, commit `a9f67e0`) passed, but review found two
walker defects in that commit (an unguarded metadata call that aborted
discovery, and suffix-less directory declarations selecting nothing); commit
`e2462f9` fixes both with controls, and the credited run above is on that
commit. `drift-cost-stage1-01` (ID `20261027T200543Z_79b9b4e5`) passed both
cases but the harness refused the run because the inventory fixture placed a
`runner/.build` directory under artifacts; its early discovery measurement of
the uncommitted working tree is superseded by the one above.
`drift-cost-stage1-02` (ID `20261027T201214Z_bf335fca`) failed because
`PW_TEST_SCRATCH` is exported but not created; every scenario before the
inventory control had passed.

Limitations: the listing counts are the walker's `os.scandir` calls as seen by
an instrument installed in the same process; they are not an OS-wide count.
The fixture control establishes the stated prefix, hidden, symlink and
non-file semantics; it is not an audit of every filesystem read the checker
makes. A selected input that cannot be read still terminates the checker with
an exception until stage 2 converts it to a precondition record.

## Stage 2: explicit rules, inputs and complete failure reporting

Change: `tests/lib/drift_rules.py` holds the rule row (`Rule`), the record
(`Problem`), the expected-input failure (`InputFailure`), the flat dispatcher
(`run_rules`), the one gated dispatcher (`run_gated`) and the status and
summary functions. `check.py` declares its 19 rules in `RULES` with inputs
(required and optional files, directory membership, patterns and the
command-document scope) and helper modules; every rule takes a tree and
returns records with a stable key, a path and a line when known. The
thirteen terminating branches are `InputFailure`s raised at the owning parser;
the dispatcher turns each into one precondition record for that rule and
continues. `--root`, `--rule` and `--json` were added. `build_rules.py`
declares its ten rules with `banner_order` as the gate. The host-invariance
snippets moved to the planner. `generator_common.rule_declarations` reads the
table statically for the `rule` citation form; the form table, the graph test
and the README copy follow it. `docs/build.json` cited the planner's
`configured_controls` as a rule; the planner has no table, so those two
citations now carry the `test` form (same path and symbol; the rendered
document did not change).

Planner additions: every scenario runs the checker with `--json` and requires
the reported rule set to equal the declared table; `precondition_scenarios`,
`dispatch_omission_scenario`, `isolation_controls` and
`host_invariance_controls`. The build case gained
`test_rule_table_gates_on_the_banner_rule`.

Behavior that changed on purpose, for review:

- A selected input that cannot be read (a missing `cli.rs` or README, a
  directory or broken symlink named with `.md`) is a precondition record
  (status 2) where it was drift or a traceback before.
- The build rules load the manifest per tree against the fixture's own
  script, so a script mutation that removes a cited symbol is a manifest
  precondition of the gate rather than a banner finding; the gate control
  uses a reordered banner and an accepted knob value, which keep every cited
  symbol present, and asserts the removed-banner case as the precondition.
- Precondition lines print as `<rule>: blocked by input: <message>`; the
  message text of every existing diagnostic is unchanged, and the summary
  lines `rules: ...`, `evaluated: ...`, `input_blocked: ...` precede them.

Credited run: `tests/out/runs/drift-cost-stage2-01` (ID `20261027T220954Z_7adc46fb`), on commit
`386564e`, all six selected cases passed with zero recorded sleep; the
planner wrote 231 receipts. Durations are single runs beside the
baseline, for context only.

| Case | Baseline ms | Stage 2 ms | Recorded sleep ms |
| --- | ---: | ---: | ---: |
| `runner_source_manifests_agree` | 188679 | 213612 | 0 |
| `architecture_documentation` | 13820 | 11538 | 0 |
| `build_documentation` | 36867 | 35136 | 0 |
| `generator_contract` | 32508 | 35811 | 0 |
| `markdown_reader` | 945 | 1096 | 0 |
| `direct_python_start` | 25151 | 13277 | 0 |

Cost: the planner still starts the whole checker per scenario (now with
`--json`), so the manifests case is not expected to be faster in this stage;
stage 3 converts the scenarios to focused in-process calls.

## Stage 3: focused planner and direct-Python controls

Change: `check_planner.py` builds a fresh tree over the disposable checkout
for each scenario and calls only the rules the scenario names, in process,
asserting the complete record set of every named rule (diagnostic keys, or the
exact messages for the seven Meson scenarios, which stay on real file-mode
introspection) plus a diagnostic substring; `records.json` and the mutated
inputs are retained per scenario, and the list runs again in reverse order
and must give the same records. Registry scenarios record every created or
deleted path with its contents. The entry point keeps six subprocess
scenarios: the baseline, three independent faults in different rules (stderr
in table order), a reader refusal beside a host finding, the combined
precondition scenario, the omitted-rule dispatcher and restoration, each with
exact status, summary lines and `results.json`. The configured-native
receipts now record each setup, compile and check launch with its elapsed
time.

Guidance: all 56 policy and restoration scenarios are kept for every document
and route. Of the 73 reader-shape scenarios, 31 stay at the rule layer (nine
body shapes for `AGENTS.md` at level 2 and `tests/AGENTS.md` at level 3, twelve
route shapes for the `runner/AGENTS.md` route, and the refused comment); the
other 42 are literal expectations in `markdown.py`, added to the eight reader
tests the plan names, with the retained scenario as each one's rule-layer
representative. The control map rows with disposition `consolidated` list
each old ID, its reader assertion and its representative.

`direct_python.py` exposes each check on one file's lines (`entry_problems`,
`script_problems`, `resolver_problems`, `wrapper_problems`); the controls hand
every forbidden, malformed and accepted form to its check directly, and one
full scan of a copied checkout establishes discovery-to-check dispatch with
an entry point, a suite script, a wrapper and a newly added script, each
named once. An entry point found by discovery is no longer reported twice.

Record-set review that changed an expectation, for the reviewer:

- `mirror-three` also loses the shared `contains` call, so the planner rule
  reports `planner.local_table` and `planner.missing_contains`; the old
  control asserted only the first by substring.
- `route-makefile-selector` adds a `--suite` line that is also an argument
  line, so the release rule reports `release.selector` and
  `release.arguments`.
- `registry-directory-without-readme` and `-outside-catalog` also make the
  catalog and the coverage table disagree with the suite directories, so
  `index_vs_disk` reports `catalog.suite_mismatch` and `index.missing_row`
  beside the README finding.
- `rule-runner-outcome-suite-row-removed` also removes a normalized outcome's
  row, so both matrix rules report.
- `entry-refusal-with-fault`: the refused `AGENTS.md` is in the
  command-document scope as well as the guidance rule, so both report the
  refusal.
- `meson-duplicate-host-declaration`: the reader drops a target declared
  twice, so the exact records are the duplicate diagnostic and
  `no 'PWRunner' target`.

STAGE3_CREDIT

## Handoff: stages 4 to 6

Stage 4 adds generator input declarations and the shared fixture copier under
`tests/lib/`; `Rule.inputs` and `Rule.helpers` are the inputs it consumes for
the checker, and the planner's `fixture()` list is the account it replaces.
Stage 5 rehomes `configured_controls` (now recording per-launch timings) and
the build entry and native policy controls under `preflight`.

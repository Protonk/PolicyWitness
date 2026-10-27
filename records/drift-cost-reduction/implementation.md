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
filesystem, under the checkout lock after the credited run; retained with the
helper script and selected inventories in the credited run's `investigation/`
directory):

| Observation | Baseline | Stage 1 (3 samples) |
| --- | --- | --- |
| Markdown discovery listings | 222,124 (214,664 under `tests/out`) | 177 (0 under `tests/out`) |
| Markdown discovery seconds | 7.116 | 0.005, 0.003, 0.003 |
| Markdown documents selected | 101 | 100 (two plan documents removed, one added since the baseline revision) |
| Shell discovery listings | 214,946 (214,664 under `tests/out`) | 141 (0 under `tests/out`) |
| Shell discovery seconds | 6.802 | 0.003, 0.003, 0.003 |
| Shell scripts selected | 149 | 149, identical set |
| Reading/parsing the selected documents, empty reader cache | 0.328 | 0.335 |

The retained `tests/out` tree held 1,803 fixture entries inside the inventory
control plus every earlier run at measurement time; the stage-1 walker never
lists it, so its population no longer affects discovery time. These remain
helper samples, not case durations or thresholds.

Also in this stage, ahead of the stage-2 rule table: the plan's required
missing-rule controls were added to the planner as real-checker scenarios
(`rule_gap_scenarios` and the Baseline-membership registry scenarios). The
`control-map.json` rows with disposition `added` list them. The planner now
runs 225 receipts per case (204 before).

STAGE1_CREDIT

Limitations: the listing counts are the walker's `os.scandir` calls as seen by
an instrument installed in the same process; they are not an OS-wide count.
The fixture control establishes the stated prefix, hidden, symlink and
non-file semantics; it is not an audit of every filesystem read the checker
makes. A selected input that cannot be read still terminates the checker with
an exception until stage 2 converts it to a precondition record.

## Handoff: stages 2 to 6

Not started. The next stage converts `check.py` rules to accept a
`repository_tree.Tree`, declares the ordered `RULES` table with inputs,
replaces the thirteen `sys.exit(2)` branches with typed precondition records
(status 2 after all rules run), moves `host_invariance_controls` into the
planner and migrates `generator_common.citation` to read the table. The
scenarios added in stage 1 keep their expectations through that change: the
malformed C enum control expects status 2 and its diagnostic, which the
precondition policy preserves while the other rules continue.

`check_planner.py::inventory_controls` and the new scenarios still start the
whole checker per scenario; stage 3 converts them to focused in-process rule
calls over a fresh tree per scenario. The inventory fixture is built in
`PW_TEST_SCRATCH` (the harness refuses a `runner/.build` directory under
artifacts), and its receipt `inventory-controls.json` lists every created
path, the selected entries and the directories each walk entered.

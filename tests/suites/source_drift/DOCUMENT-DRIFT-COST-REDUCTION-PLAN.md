# Document drift cost reduction plan

## Purpose and authority

A read-only assessment was performed on 2026-10-27 to investigate why the
document drift checks are slow. It inspected source and existing test evidence,
timed read-only helpers, and profiled selected paths in memory. It made no
implementation changes and did not rerun the mutation controls. Three core
repair directions suggested themselves; they are described below with the
evidence and remaining uncertainty that support them.

You are responsible for further investigation and remediation before the 
later document-checking refactor. The warrant for doing this now is that 
the refactor will be better off if it is not trying to enshrine
poor patterns in a different architecture. Make bounded repairs to demonstrated
costs, preserve the checks' guarantees, and give the later refactor a measured,
better-behaved starting point.

Use [the planning guidance](../../../CONTRIBUTING.md#planning-a-change),
[test working rules](../../AGENTS.md), and
[the source_drift reference](README.md).
This plan lives beside the suite it targets; retain execution evidence in
managed test output, following
[the output contract](../../README.md#retention-ownership-and-execution-locking).

## Assessment and its limits

The existing successful
[pytest-trial-closing-01 run](../../out/runs/pytest-trial-closing-01/run.json)
records 399.588 seconds across the eight `source_drift` cases:

| Case | Recorded seconds |
| --- | ---: |
| `runner_source_manifests_agree` | 214.512 |
| `direct_python_start` | 39.249 |
| `build_documentation` | 37.420 |
| `generator_contract` | 34.932 |
| `limits_documentation` | 29.475 |
| `contract_versions` | 29.109 |
| `architecture_documentation` | 13.763 |
| `markdown_reader` | 1.128 |

The [pytest-baseline-drift-20261026 run](../../out/runs/pytest-baseline-drift-20261026/run.json)
records 370.479 seconds for the same cases. Neither run records system sleep
during these cases. These totals are for `source_drift`, not for every case in
the enclosing runs.

The assessment established the following:

- In `pytest-trial-closing-01`, the largest case spent about 9.2 seconds in its
  initial check and 205.3 seconds in its controls. Its retained
  [control receipts](../../out/runs/pytest-trial-closing-01/suites/source_drift/runner_source_manifests_agree/artifacts/planner-controls/controls.json)
  contain 204 scenarios: 197 launch the complete `check.py`, and seven exercise
  configured native-source checks. There are 129 guidance-section/link variants.
- One read-only pass through the retained planner fixture took approximately
  0.70 seconds: 0.42 seconds in Meson introspection and 0.20 seconds in document
  command checking. Each fresh subprocess loses the previous process's parser
  cache. The fixture's `check.py`, `native_sources.py`, `markdown_reader.py`, and
  `meson.build` matched the working files at assessment time; this was not a
  complete dependency or provenance audit of the historical runs.
- Current-checkout Markdown discovery took 6.565 seconds and made 219,650
  directory-listing calls. Of those calls, 212,230 were under `tests/out`.
  Exclusion happens after recursive discovery. The selected corpus was 99
  Markdown files, 1,684,144 bytes and 21,670 lines, including the distributed
  guide copy. Reading and parsing it with an empty parser cache took 0.322 seconds.
- The direct Python invocation check took 8.933 seconds on current sources;
  8.814 seconds was shell-script discovery. That discovery also traverses test
  output before rejecting its matches.
- The five generator `--check` commands passed in 1.274 seconds combined:
  contract 0.034, worker identity 0.032, limits 0.292, architecture 0.626, and
  build 0.290 seconds. These commands do not perform all the suite's obligations.
  The per-generator and shared contract tests additionally copy fixtures,
  mutate inputs, run subprocesses, compare snapshots, and sometimes configure
  or compile native code.

These are historical case timings and local spot measurements using the pinned
Python 3.14.9 interpreter, not performance thresholds or a new credited battery.
Profiler timings include instrumentation overhead; the discovery and parsing
figures above came from separate timing measurements. The full cost of fixture
copying, snapshotting, and individual generator controls was not attributed.
Source and retained-output populations may have changed since assessment.
Establish a current baseline before making performance claims.

Documentation volume is a multiplier when work is repeated. Its one-pass parsing
cost does not explain the observed minutes. The three repairs below address
the work surrounding and repeatedly applied to that corpus.

## Repair 1: prune excluded subtrees before discovery descends into them

Start with `markdown_documents()` in
[check.py](check.py) and `shell_scripts()` in
[direct_python.py](direct_python.py). Both filter
matches from an already-recursive `rglob`; the Markdown exclusions additionally
cover scratch, native and Rust build state, archives, and vendored sources.

Change discovery so excluded directory contents are never enumerated. Preserve
the intended included file set, ordering, and error behavior. Inspect the exact
prefix and hidden-path rules before selecting the traversal implementation;
directory-name approximations can silently broaden an exclusion. The planner
uses a disposable checkout without Git metadata, so a Git-only inventory is not
a drop-in replacement. Included untracked documents must remain discoverable.

Verification must establish both sides of the boundary: nested included files
remain checked, and excluded directories are not entered. Use an independent
expected inventory and a traversal observation or equivalent control; filtering
the final list alone cannot prove that discovery avoided the expensive work.
Cover similarly named paths, hidden paths, and the existing symlink semantics.
Demonstrate that adding an excluded subtree does not add traversal of its
contents. Do not delete retained evidence to obtain a faster result.

## Repair 2: stop replaying unrelated checks for every narrow mutation

Start with the scenario and registry loops in
[check_planner.py](check_planner.py), the aggregation
in `check.py:main`, and the repeated `check(root)` calls in `direct_python.py`.
A guidance mutation currently pays for native-source introspection and all the
other checks, even when only one rule's behavior is being exercised.

Map each existing scenario to the rule and integration behavior it establishes.
Use that map to reduce redundant execution while retaining every distinct
passing and rejected control. Focused rule calls, grouped executions, or reuse
of genuinely invariant work are candidates; the assessment did not select one.
Determine which controls require a fresh process, real command-line invocation,
or actual Meson evaluation before replacing those boundaries.

Keep integrated coverage of the real entry point, rule aggregation, status and
diagnostics. A focused test can pass while its rule is no longer called by the
entry point. Combined faults, malformed Markdown, and reordered controls must
still expose the applicable failures without inventing or suppressing others.
If execution shares a process or parsed state, verify that mutations, restored
files, changed roots, and scenario ordering cannot reuse stale observations.

Success means fewer unrelated rule evaluations and subprocess starts for the
same demonstrated obligations. Preserve per-scenario inputs and diagnostic
evidence. Do not count removal of controls, new skips, or moving work out of
the normal verification path as a cost reduction.

## Repair 3: remove demonstrated duplication in generator-test setup and work

Inspect `GeneratorContractTests.checkout`, `command`, and `snapshot` in
[generators.py](generators.py), the per-generator
tests in the same directory, and their composition in
[run.sh](run.sh). Separate time spent validating
current documents from time spent copying fixtures, starting commands, checking
ownership and refusal behavior, and configuring or compiling native fixtures.

The assessment establishes that these activities are bundled into the reported
cost; it does not establish that each activity is wasteful. Attribute the
expensive portions before choosing repairs. Identify repeated setup, repeated
unchanged validation, and genuinely duplicated assertions. Reduce only work
whose repetition supplies no additional observation. Where reuse is warranted,
make its unchanged inputs and isolation assumptions explicit and test them.

Preserve the generator contracts: freshness and marker validation, citation
checks, ownership, idempotence, refusal before writes, standalone guide behavior,
and build enforcement. Snapshot comparisons that demonstrate no writes on
refusal have a purpose; replacing them with exit-code checks loses that purpose.
Compilation may establish a property textual checks cannot. Retain distinct
integration observations and explain any expensive work that remains justified.

This repair's implementation depends on the timing attribution. If a suspected
duplication is necessary for independence or command-boundary coverage, record
that finding and narrow the repair. Merely splitting or renaming cases would
not reduce their execution cost and is not the objective.

## Execution and verification

1. Record the current source snapshot, interpreter, relevant equipment, and
   output population. Inspect `tests/run.sh --suite source_drift --list`, then
   establish a current baseline through the dispatcher with a fresh
   `PW_TEST_OUT_DIR=tests/out/runs/<unique-name>`. Keep raw timings and profiling
   evidence with the run. Do not treat the earlier read-only measurements as
   proof that current tests pass.
2. Implement and verify early pruning first. Then measure again before repairing
   repeated checker execution and generator setup, so traversal costs are not
   mistakenly attributed to their other work. Keep the changes independently
   reviewable and let new evidence narrow the proposal.
3. Run the affected canonical cases through `tests/run.sh` as each boundary
   changes. Finish with `tests/run.sh --suite source_drift` in fresh managed
   output. Preserve the single-checkout lock and serialize comparable timing
   runs; follow the repository's diagnostic and escalation guidance if the
   automation sandbox obstructs compiler or other required operations.
4. Compare baseline and candidate case times under comparable conditions and
   repeat measurements where variation could change the conclusion. Report
   discovery calls, full-checker/process invocations, and fixture/build work
   alongside elapsed time. Explain changed output populations and cache state;
   a faster filesystem cache is not evidence of an algorithmic improvement.
5. Update affected suite documentation and test registration if their actual
   behavior changes. Preserve generator-owned documentation by editing its
   inputs and regenerating; check affected manifest citations when rule names
   or locations change. Do not broaden this work into the later architecture
   refactor or change the witness protocol or runner behavior.

Completion requires evidence that excluded contents are no longer traversed,
redundant whole-checker execution has been reduced with equivalent coverage,
and the generator-work investigation has produced supported repairs or a
specific explanation of costs that must remain. Deliver the final before/after
measurements, the mapping of preserved control obligations, credited run paths
and source snapshots, and any remaining uncertainties for the later refactor.
No numerical speedup is promised in advance of that work.

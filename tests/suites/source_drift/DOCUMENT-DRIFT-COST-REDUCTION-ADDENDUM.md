# Document drift cost reduction: addendum

## Purpose and authority

A second read-only assessment was performed on 2026-10-27 at `3a555b6`, after
[the document drift cost reduction plan](DOCUMENT-DRIFT-COST-REDUCTION-PLAN.md)
was written. That plan proposes three repairs: pruning excluded subtrees before document discovery
(Repair 1), ending the replay of the whole checker for every narrow mutation
(Repair 2), and removing duplicated setup and work in the generator tests
(Repair 3).
It read every file in `tests/suites/source_drift/`, the shared reader and
generator helpers under `docs/`, `tests/lib/native_sources.py`, the retained
control receipts of the `pytest-trial-closing-01` run, and the suite's git
history. It called four of the suite's own fixture helpers once each to time
them. It made no implementation changes and reran no battery.

The plan asks for bounded repairs. This addendum adds one design decision the
repairs should be built on, four judgements the later refactor will otherwise
have to make from scratch, and one correction to the plan's attribution of
generator-test cost. It lives beside the suite it describes. Keep execution
evidence in managed test output under
[the output contract](../../README.md#retention-ownership-and-execution-locking).

## Evidence and its limits

Facts below were established by reading the named files at `3a555b6` unless a
measurement or receipt is cited. Line counts and scenario counts are exact;
timings are single samples on a warm page cache.

### The checker is bound to its own file location

[check.py](check.py) derives `REPO_ROOT` from
`__file__`, and every rule reads module constants built from it. No rule takes
a root. That is the only reason
[check_planner.py](check_planner.py) must copy the
checker into its fixture and start one process per scenario. In the retained
`controls.json`, 197 of the 204 receipts are whole-checker subprocesses; the
other seven run `native_sources.py` against a configured build directory.
The other checkers in the suite already take a root:
`native_sources.expected(root)`, `direct_python.check(root)`, and the
module functions in `generators.py` default a `root` parameter.

### The rule registry is implicit, in two places

A rule is "a function called from `main()` whose name starts with `check_`".
`test_document_graph_cites_every_drift_rule` in
[generators.py](generators.py) reads that out of
the AST to hold the document graph's `drift_check` node to it. The `rule`
form in [generator_common.py](../../../docs/generator_common.py) reads it again as
"Python function with a call from `main()`", and the README's form table is a
checked copy of that convention. `host_invariance_controls()` runs
constructed-text controls inside `main()` on every invocation, including all
197 planner runs, and escapes the citation requirement only because its name
lacks the prefix. Diagnostic prefixes are ad hoc per rule, and
`check_cli_surface_agreement` returns lines without the two-space prefix the
others use.

### Error policy is inconsistent and one branch has no control

`guarded()` catches only `markdown_reader.Refused`; that is the one failure
kind for which "the other drift checks still run" holds. Thirteen call sites
in `check.py` exit the process with status 2 instead of returning a problem:
`check_meson_source_lists` on introspection failure, `suite_directories`,
`required_section`, `_parse_swift_enum_constants`, `parse_c_attempt_kinds`
(two), `parse_swift_attempt_kinds` (two),
`parse_swift_prediction_unavailable_pairs` (two),
`parse_docs_prediction_unavailable_pairs`, and `parse_test_override_fields`
(two). A missing "Suite coverage" heading in `tests/README.md` therefore
hides every other rule's result and the summary line. The retained receipts
expect only status 0 (66 scenarios) or 1 (138); no scenario expects 2.

### The control budget was allocated by history, not by rule

One rule, `check_harness_guidance_routes`, has 129 planner scenarios. Four
rules have none: `check_baseline_in_catalog_defaults`,
`check_runner_outcome_suites_have_matrix_rows`,
`check_attempt_outcomes_have_matrix_rows` and
`check_attempt_kind_enum_agreement`. This was established by searching the
planner for each rule's diagnostic text; confirm it by reading when the
Repair 2 map is built.

Of the 129 guidance scenarios, this assessment classifies 73 as establishing
how the Markdown reader treats a shape and 56 as establishing what the rule
decides. The classification by scenario kind:

| Group | Kinds | Count |
| --- | --- | ---: |
| Section body, reader shape, per document (4) | fenced-body, comment-body, indented-body, fenced-section, comment-section, short-fence-close, fake-heading-before-real, body-after-peer, body-after-parent | 36 |
| Section body, rule policy, per document (4) | rewritten, rewrapped, reordered, local-prose, heading-missing, heading-duplicate, empty, headings-only | 32 |
| Section restored | per document plus one combined | 5 |
| Route, reader shape, per target (3) | fenced, comment, inline-example, image, code-label, code-label-example, wrapped-label, split-label, indented-continuation, indented-example, indented-after-heading, list-continuation | 36 |
| Route, rule policy, per target (3) | removed, wrong-path, wrong-fragment, relabeled, relative-path, outside-section | 18 |
| Route restored, reader refusal | routes-restored; unrecognized-comment | 2 |

[markdown.py](markdown.py) holds hand-written
expectations for the reader-shape rows: fence closing and nesting, indented
code, list content after a blank line, comments, wrapped and split labels,
images, autolinks, section boundaries and the `--` refusal. The guidance rule
and its scenarios (`f3fc56b`), the vendored reader (`6d1c65a`) and the
checker's migration to the reader (`e043a75`) all landed on 2026-10-19, and
the scenarios were carried across the migration rather than replaced. Each
reader-shape scenario currently costs one whole-checker process.

### Disposable checkouts are built eleven ways

| Location | Inclusion rule |
| --- | --- |
| `check_planner.main` | hand-maintained path list, the native expectation, a walk of `runner/Sources`, the reader's source files, suite `run.sh` and `README.md` globs |
| `direct_python.DirectPythonTests.checkout` | entry, resolver and wrapper lists plus every shell script under `tests/` |
| `markdown.py`, four places | the reader's source files |
| `generators.GeneratorContractTests.checkout` | every tracked and untracked unignored file |
| `limits.LimitsDocumentationTests.checkout` | fixed set plus every path the limits manifest cites |
| `contract.ContractVersionTests.checkout` | generator, manifest, targets and a caller-supplied extra set |
| `contract.ContractVersionTests.build_checkout` | union of the limits, architecture and build references and the identity sources |
| `contract.WorkerIdentityTests.checkout` | identity sources and targets |
| `architecture.ArchitectureDocumentationTests.checkout` | generator inputs, outputs, span documents and every cited file |
| `build.BuildDocumentationTests.checkout` | fixed set plus every cited file |
| `build.py`, two inline copies | tracked files under the native source directories |

Each list restates by hand what some rule or generator reads. The planner's
fixture self-checks ("fixture requires the current PWRunner source list") exist
because that restatement can drift.

### Three cases are dominated by build-gate behavior controls

- `contract_versions`: [contract.py](contract.py)
  starts `build.sh` from 17 call sites, several inside loops, to establish
  the builder check, knob and argument refusals, the plist minimum, SDK
  selection, build-directory admission and the identity refusal, in order.
  One full pass to the identity refusal measured 2.6 seconds (table below).
- `build_documentation`: [build.py](build.py)
  runs 21 Meson setup, configure and compile cycles against the real checkout
  in `test_meson_policy_assertions_refuse_each_option`, one tree copy with a
  full native compile in
  `test_bypassing_one_meson_policy_assertion_fails_its_control`, and two
  setups with one regeneration in
  `test_meson_output_target_assertion_refuses_other_hosts`. These establish
  what `meson.build` asserts.
- `runner_source_manifests_agree`: `configured_controls` in the planner runs
  six setup-and-compile cycles with `xpc=false` plus a copied-checkout check,
  establishing the configured-directory reading and the identity closure that
  `build.sh` relies on.

These controls establish properties text cannot, as the plan says. None of
them checks a document. The catalog's `requires: meson` on two document cases
comes from them. Rehoming them is a manifest change as well as a file move:
`docs/architecture.json` names `contract.py` on 24 lines and `build.py` on
12; `docs/build.json` names `contract.py` on 27, `build.py` on 3 and
`check_planner.py` on 2.

### Obligations with more than one owner

- `build_rules.py` runs from [run.sh](run.sh)
  line 74 and again from `build.py` line 71 in the same case.
- `broken_links(scanned_documents())` is asserted in `generators.py` line 612
  and `limits.py` line 518, in two cases.
- Every generator's `--check` runs in `build.sh` lines 226 to 233, in its own
  case's currency test, and inside every `build.sh` pass the contract case
  starts.
- Each generator invocation re-resolves every citation in its manifest and
  parses every document it owns before reaching the mutation under test.

### Measurements

Each helper was called once from a short script in the session scratchpad,
not retained, under `/opt/homebrew/opt/python@3.14/bin/python3.14` 3.14.9
with `-B -S`. The `build.sh` pass used the contract case's `build_checkout`
and `build` helpers with `IDENTITY` empty; it printed banners through
"Checking the signing identity" and exited 2.

| Measurement | Result |
| --- | ---: |
| `generators.checkout`, whole tree: 1,280 files, 19,177,010 bytes | 0.48 s |
| `generators.snapshot` of that tree | 0.08 s |
| `limits.checkout`, declared inputs: 150 files, 2.7 MB | 0.04 s |
| `architecture.checkout`, cited files: 238 files, 4.8 MB | 0.06 s |
| `contract.build_checkout`, reference union: 278 files, 5.9 MB | 0.08 s |
| one `build.sh` pass to the identity refusal | 2.60 s |

`records/archive` is 9.8 MB of the 19.2 MB whole-tree copy. The receipts in
`controls.json` record argv, status and expectations but no elapsed time.

## The design decision

Build the repairs on this seam, before Repair 2 and before the fixture part of
Repair 3.

**A tree object.** A root, a content-keyed read cache, and one document
inventory with named scopes (every repository document; the prose-scan set;
the generator-owned documents). Repair 1's pruned traversal lives here, once.
The reader's `parse` cache is keyed by text, not path, so observations cannot
be reused across a mutation; preserve that property in the tree's own cache.

**Rules as functions of the tree.** Each rule takes the tree and returns
problem records: rule id, path, line where known, message. A precondition
failure (missing section, unparseable enum, introspection failure) is a record
with a distinct severity, never an exit. The entry point iterates one explicit
table of rules, each with its id, function and declared inputs, computes the
exit status from the records' severities, and prints the summary from the
table. Constructed-text controls leave `main()` for the planner or the reader
case.

**The planner calls rules in process.** For each scenario it builds a fresh
tree over the mutated fixture and calls the rules the scenario names.
Expectations key on rule id and a stable diagnostic key, not on message
wording. A handful of subprocess scenarios remain and are labeled as such:
baseline, one combined fault, one reader refusal, one precondition failure,
and restored, to establish that the real entry point aggregates, orders and
exits correctly.

**Declared inputs feed everything else.** The fixture helpers derive their
inclusion lists from the rules' and generators' declarations instead of
restating them. The binding plan's inventory column "Inputs read" is read from
the same table, and its reverse index starts from it.

Coupled changes the executor must carry: the `rule` form's definition
convention in `FORM_RULES` and the README's checked copy of the form table;
`test_document_graph_cites_every_drift_rule`, which should read the table
rather than the AST; and the `drift_check` citations in
`docs/architecture.json` if any rule function is renamed. The tree object
must be importable by the checker, the planner and the generator-contract
case without a circular import; its location is the executor's choice.

## Four judgements for the refactor

1. **Name fit.** Decide where the build-gate behavior controls live before
   `docs/CHECK.md` is planned, so the document-checking machinery it
   describes is rules plus generator contracts. The `preflight` suite already
   owns `build_refusal_controls` and `build_guard_controls`. Moving them is a
   scope decision, not a cost reduction, and the plan is right to exclude it
   from the accounting.
2. **One owner per obligation.** For each duplicated obligation above, name
   the owner in the catalog description and remove the other assertion, rather
   than deleting whichever is slower.
3. **Receipts carry their cost.** Record elapsed time and process count per
   scenario in `controls.json` and the generator cases' logs. Step 4 of the
   plan then becomes a read of the receipts, and the binding plan's cost
   column stays current without another assessment.
4. **Parser semantics once.** Establish reader behavior in the reader's case
   and let rule controls establish rule policy. For each reader-shape scenario,
   find the expectation in `markdown.py` that covers the same shape; keep the
   scenario only where none exists or add the expectation. Keep one or two
   rule-level scenarios per shape class to show the rule reads through the
   reader rather than through text patterns.

## Correction to Repair 3

Copying is not where the generator-test time goes. Nine whole-tree checkouts
cost under five seconds of a 35-second case, and snapshots are negligible.
The cost is the generator invocations: dozens per case, each re-validating
the whole manifest, at the per-check times the plan recorded. In the contract
case it is the `build.sh` passes at 2.6 seconds each. Pruning
`records/archive` from the copy is harmless and will not show in the case
time. Attribute by counting invocations per case before choosing what to
reuse, and look for mutations that can share one validated manifest load
without sharing a process with the command boundary under test.

## Remaining uncertainties

- The reader-shape classification is this assessment's; the Repair 2 map
  should settle it scenario by scenario.
- The four uncovered rules were established by the absence of their
  diagnostic text in the planner, not by a control inventory.
- Generator-case cost is inferred from invocation counts and the plan's
  per-check timings, not measured per invocation.
- The `build.sh` figure counts call sites; the invocation count is larger and
  not every start reaches the full pass.
- All timings are single samples.

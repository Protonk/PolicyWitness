# Implementing bounded document-checking cost reductions

## Objective and scope

Reduce repeated discovery, unrelated rule execution and unchanged validation
in `source_drift`, while preserving the observations its controls establish.
Give the later document-binding work an explicit inventory of rules, inputs,
owners and measured costs. This is an implementation plan, not a proposal to
run another open-ended assessment.

The investigation used source revision
`1612eb5e0bd503f0185dda9cda0331be0d9a764f`. This document replaces the cost
reduction plan and its addendum at that revision; neither is needed to execute
it. Follow [CONTRIBUTING.md](../../../CONTRIBUTING.md#planning-a-change),
[test working rules](../../AGENTS.md) and the
[suite contract](README.md#generator-contracts).

Included work:

- Prune excluded directories before descent, with separate discovery policies
  for repository Markdown, prose checks and shell scripts.
- Make the existing checker callable against an explicit tree, register its
  rules, aggregate expected input failures, and run focused controls in process.
- Preserve parser coverage while reducing repeated reader-shape controls at the
  rule layer; fill four confirmed gaps in rule controls.
- Give fixture construction declared inputs and receipts measurable costs.
- Remove specific duplicated validation and assertions, preserving generator
  command boundaries and no-write observations.
- Move build execution controls to explicitly default, offline preflight cases,
  with their existing equipment and assertions. Report their cost separately
  from genuine savings.

Do not change witness behavior, request/evidence versions, runner sources,
native compilation policy, build gate ordering, vendored parser semantics or
external dependencies.
Do not add persistent result caching, a new test framework, parallel execution
within one checkout, or a general document-checking application. Do not execute
the separate [binding investigation](BINDING-THRU-REPLAY-PLAN.md), create
`docs/CHECK.md`, or implement its reverse index. The declarations and receipts
below are inputs that later work can consume, not proof of semantic support for
a citation.

### Design preference: clear contracts before additional savings

Choose implementations whose caller can state what is read, what may be
reused, what is returned and when that reuse ends. Prefer a small explicit
parameter or value over a generic framework or implicit cache. If two designs
preserve the same observations, prefer the one a later refactor can replace
without reconstructing hidden dependencies, even if it leaves some measured
cost in place. The contracts for this work are:

| Boundary | Contract |
| --- | --- |
| Tree access | An explicit root and named scope determine discovery; reads observe bytes from that root. Parse reuse is keyed by content and diagnostic identity. Inventory lifetime ends with the scenario. No writes or subprocesses are hidden in a read. |
| Rule | An explicit tree and declared inputs produce problem records. The rule does not exit, print or mutate files; an external-tool rule declares that boundary. The dispatcher alone orders records and selects exit status. |
| Fixture | Expand declared inputs into a separate mutable tree, preserving specified path/symlink semantics. Include infrastructure dependencies separately from the rule's subject files. Evaluators use the supplied root; structural controls establish the tested root/import behavior, not an audit of all filesystem reads. |
| Validated generator invocation | Load and validate inputs for one check/write operation, pass those values explicitly to rendering, then discard them. Validation completes before publication. A later invocation validates again. |
| Control receipt | Record the inputs, observation, expectation and measured work for one named control. State the counting boundary; never equate a receipt count with all descendant processes. |

Core evaluators require their root/context argument; convenience defaults
belong at command entry points. In-process planner controls import the evaluator
once and pass fixture trees, rather than rebinding module globals or swapping
`sys.modules` entries between roots. Keep these contracts documented beside
their implementation and tested at their boundaries.

## Evidence and decisions

### Baseline and the limits of the measurements

The fresh dispatcher baseline is
[drift-plan-investigation-20261027-02](../../out/runs/drift-plan-investigation-20261027-02/run.json),
run ID `20261027T175448Z_a3635ceb`: all eight cases passed, with zero recorded
sleep and 349.098 seconds summed from case reports. It ran on unchanged
`1612eb5`, with Python 3.14.9, Meson 1.12.1 and Apple clang 21.0.0. The command
was `PW_TEST_OUT_DIR=tests/out/runs/drift-plan-investigation-20261027-02
tests/run.sh --suite source_drift`.

The initial restricted run, `drift-plan-investigation-20261027-01` / ID
`20261027T174605Z_08a98a78`, is preserved separately. It failed limits and
contract build controls because `sysctl`/nested sandbox operations were
refused, and Swift policy controls because module-cache writes were denied.
The unchanged suite passed on the unsandboxed retry; the first run is not a
successful performance baseline.

After that baseline, serialized read-only helper experiments recorded:

| Observation | Result |
| --- | --- |
| Markdown discovery | 7.116 seconds; 222,124 directory listings, including 214,664 under `tests/out`; 101 selected documents, 1,711,255 bytes. |
| Shell discovery | 6.802 seconds; 214,946 listings, including the same 214,664 under `tests/out`; 149 selected scripts. |
| Reading/parsing those documents with an empty reader cache | 0.328 seconds. |
| One build-rules pass | 0.783 seconds; ten manifest loads consumed 0.762 seconds, seven script parses 0.016 seconds. |
| One architecture check | 0.498 seconds; two limits loads, taking 0.049 and 0.012 seconds. |
| One generic-generator fixture | 1,282 files / 19,206,995 bytes; copy 0.227 seconds, snapshot 0.040 seconds. |
| Missing suite heading plus a forbidden host binding | Exit 2, only the missing-heading diagnostic; no host diagnostic or summary. |

A small independent filesystem fixture also confirmed the prefix, hidden,
symlink and non-file discovery semantics specified in stage 1. Raw helper
script, selected inventories and results are retained in the baseline run's
`investigation/` directory. These are single helper samples with wrapper
overhead and a warm filesystem, not credited battery cases or thresholds.

The separately dispatched
[generator attribution run](../../out/runs/drift-plan-generator-profile-20261027-01/run.json),
ID `20261027T180108Z_d44f791d`, passed with zero recorded sleep. Temporary
timing wrappers around `checkout`, `snapshot`, `command` and test execution
measured **31 copies (8.629 seconds), 97 snapshots (5.502 seconds) and 67
generator subprocesses (16.755 seconds)** over 21 tests (41.346 seconds
inclusive). The subprocess distribution was architecture 35, limits 26 and
two each for contract, worker identity and build. Counts and per-call records
are in `suites/source_drift/generator_contract/artifacts/helper-costs.json`;
the exact instrumentation is retained beside them. The original source was
restored byte-for-byte (SHA-256
`580e41b3704f6739344c900252a17b274bb83df6a6ecb687058002c79aa92e21`).

This qualifies the addendum's copying-cost claim: nine call sites are not
nine executed copies, and both copying and snapshots have material cost in
this sample. The instrumented total is not interchangeable with the
32.508-second uninstrumented baseline case. Do not add inclusive test time
to its helper subtotals or infer a speedup from differences between runs.

The earlier assessment's `pytest-trial-closing-01` run (since removed; its
numbers are recorded here) reported these case durations, with no recorded sleep:

| Case under `source_drift/` | Historical seconds | Fresh baseline seconds |
| --- | ---: | ---: |
| `runner_source_manifests_agree` | 214.512 | 188.679 |
| `direct_python_start` | 39.249 | 25.151 |
| `build_documentation` | 37.420 | 36.867 |
| `generator_contract` | 34.932 | 32.508 |
| `limits_documentation` | 29.475 | 24.458 |
| `contract_versions` | 29.109 | 26.670 |
| `architecture_documentation` | 13.763 | 13.820 |
| `markdown_reader` | 1.128 | 0.945 |

Its total was 399.588 seconds; `pytest-baseline-drift-20261026` reported 370.479
seconds for the same eight cases. These are historical comparisons, not a
source-applicability audit or acceptance thresholds. Earlier spot measurements
found 219,650 directory listings for Markdown discovery, 212,230 under
`tests/out`, taking 6.565 seconds; parsing the selected 99 documents took
0.322 seconds. Shell discovery took 8.814 seconds of an 8.933-second direct
Python check. Five generator checks together took 1.274 seconds. These
measurements explain the hypothesis; use the new observations above and fresh
candidate measurements to assess the implementation.

### Findings that determine the implementation

1. **Discovery has different policies.** `check.py:markdown_documents` walks
   the entire checkout before filtering. The exclusion `builddir` is a string
   prefix at the root, so it also excludes `builddir-old`; `records/` does not
   exclude `records-old/`. Any hidden Markdown path component is excluded.
   `direct_python.py:shell_scripts` excludes only the first component `out`
   below `tests/`; hidden shell paths and `tests/nested/out/` remain included.
   A universal exclusion list would change coverage.
2. **Whole-checker replay is the main repeated work.** Reading all planner
   scenario builders establishes 197 complete checker invocations and seven
   configured-native receipts. The 197 comprise 14 planner-membership, five
   host, seven file-mode Meson, 129 guidance, nine Markdown-structure, 15 gap,
   11 command-route and seven registry scenarios. Every complete invocation
   performs Meson introspection and document-command discovery. Constructed
   host controls also run inside every invocation.
3. **Four rule controls are absent.** Reading the actual mutations, rather
   than searching diagnostics alone, confirms no dedicated negative control
   for Baseline default membership, runner-outcome suite/matrix membership,
   attempt-outcome matrix agreement or C/Swift attempt-kind agreement. The
   commented normalized-outcome row is `ok`; it does not cover the
   runner-outcome-suite rule.
4. **The error contract is incomplete.** `guarded` catches only reader
   refusals. Thirteen `sys.exit(2)` branches in parsing and introspection can
   terminate the checker before unrelated rules run. None of the existing
   204 receipts expects status 2. Keep status 2 meaningful, but collect
   expected precondition failures and continue independent rules.
5. **Rule citation recognition is coupled to execution syntax.**
   `generator_common.citation` recognizes a rule by a function definition and
   a direct call in `main`; `test_document_graph_cites_every_drift_rule`
   independently extracts `check_*` calls. Both `check.py` and `build_rules.py`
   use this convention. Changing only the checker would break or weaken
   citation checks.
6. **Both fixture work and repeated validation matter.**
   Whole-tree fixture copying includes roughly 9.8 MB of historical archive
   content in the earlier 19.2 MB sample. That assessment measured about
   0.48 seconds per copy and 0.08 per snapshot, versus 2.60 seconds for one
   build-script pass reaching identity admission. It did not measure all
   invocations. Independently, `build_rules.py` loads the same manifest for
   each of ten rules and reparses the same script for seven of them;
   `generate_architecture.check` validates limits in `load_manifest` and
   loads them again for rendering. These are bounded reuse opportunities.
7. **Some apparent duplication is required integration.** A generator's own
   currency check and its invocation from `build.sh` establish different
   boundaries. Configured Meson/Ninja dependency checks establish facts a
   textual source comparison cannot. Preserve them. Exact duplicate owners
   are the extra `build_rules.py` start in `build.py` and the same repository
   link scan in `limits.py` and `generators.py`.

## Implementation sequence

Keep the following stages independently reviewable. Establish the baseline
before changing executable code; after stage 1, measure discovery again so its
savings are not assigned to later work. Keep the old-to-new control map and
implementation account as handoff records for this plan, as specified below,
and retain the inputs and receipts for credited runs in managed output.

### Records used during this plan

During implementation, create `records/drift-cost-reduction/` containing
`README.md`, `control-map.json` and `implementation.md`. Its consumer is the
reviewer accepting the implementation of this plan. The map records how the
old obligations were preserved; it is not a registry that tests consume or
maintain after the transition. The implementation account carries the
before/after measurements, evidence credits and remaining limitations.

The package README states that purpose and consumer, the baseline and candidate
source revisions, the map's field meanings and the retirement condition below.
Map rows identify the old case/scenario or test/subtest, its obligation,
disposition (retained, moved or consolidated), destination case and
file/symbol/scenario, reason, and supporting receipt. Consolidated rows name
both the reader assertion and the retained rule-integration representative.
The implementing agent checks destination existence and receipt applicability
at the recorded candidate revision for acceptance; no permanent test depends
on this historical map. The account includes the useful results needed for
review even when linked raw evidence is unavailable, and labels `tests/out`
links as gitignored, local-checkout evidence.

Follow [records/AGENTS.md](../../../records/AGENTS.md): this plan is the only
repository document allowed to link into that package, which is
[records/drift-cost-reduction/](../../../records/drift-cost-reduction/README.md);
do not link it from suite READMEs, tests, source, indexes or the separate
binding plan. Commit these records with the relevant
implementation stages so work in progress is recoverable.

Retire the package when implementation review is accepted and the current
contracts, control ownership and receipt formats are documented and checked
in their permanent code/test/README locations. Remove the package and this
plan together in the same retirement change; Git retains the transition
record. The later binding inventory consumes the live declarations and
receipts, not this package. Nothing whose operation must outlive this plan
belongs in the package.

### 1. Shared tree access and pruned discovery

Add `docs/repository_tree.py`, importable by the checker, fixture helpers and
generators without importing any suite or generator. Keep it small: explicit
root, file access, content-keyed parse reuse, named inventory scopes and input
specification expansion. Leave Markdown interpretation in `markdown_reader`;
it remains the only importer of the vendored parser.

Use a top-down walk and remove excluded directory entries before descending.
Return sorted lexical paths, including untracked files, without requiring Git.
Preserve the pinned Python's current behavior: do not follow directory
symlinks; matching file symlinks remain candidates. A broken symlink or a
directory named with `.md` must not become a silent success merely because a
new walker filters to regular files. Preserve existing enumeration-error
behavior; convert an actual selected-input read failure to the explicit
precondition result described below.

The named scopes are:

| Scope | Inclusion and pruning |
| --- | --- |
| Repository command documents | Existing `COMMAND_DOCS_EXCLUDED` prefixes, exactly: `records/`, `dist/archive/`, `dist/evidence/`, `tests/out/`, `.tmp/`, `builddir`, `controller/target/`, `tests/lib/vendor/`, `runner/.build/`; exclude hidden path components; retain `dist/PolicyWitness.md` when present. |
| Prose/link documents | Existing `scanned_documents`: `docs/*.md`, root README and AGENTS, controller/runner AGENTS, tests README and AGENTS, plus every Markdown generator target. Do not expand this to all repository Markdown or shrink it to the command-document scope. |
| Generator-owned documents | Union of declared region, span and whole-document outputs; not inferred from changed bytes. |
| Test shell scripts | `tests/**/*.sh`, pruning only `tests/out/`; do not inherit the Markdown hidden or vendor exclusions. |

Keep dynamic directory inputs, such as native source trees and suite
directories, explicit. A fresh tree is created for each checker invocation or
mutated scenario. Never retain a path-only or mtime-only parse/validation
cache across scenarios. Reuse parsed content by bytes/text and diagnostic
identity (the existing reader keys on both text and name). A tree read must
observe current bytes; a changed or missing file cannot reuse its old result.
Inventories last for one immutable scenario; creating, deleting or restoring
files requires a fresh tree. Do not cache Meson introspection across scenarios.

Add independently specified inventory controls under the existing canonical
checker/direct-Python cases. Include nested and untracked files, prefix near
misses, root versus nested `builddir`, hidden files/directories, Markdown and
shell scope differences, regular/file/directory/broken symlinks, an included
unreadable input and selected non-file paths. Instrument directory enumeration
or install a sentinel that fails if an excluded directory is entered. Add a
large excluded subtree and require identical selected files and zero descent
into it. A filtered final list alone is insufficient evidence.

### 2. Explicit rules, inputs and complete failure reporting

Convert `check.py` rules to accept a tree. Default the CLI to its existing
checkout, with an explicit root option for integration fixtures. Replace all
module-global data paths in rule execution, including helpers and summary
counts; import paths may still locate the implementation. Keep current rule
function names to minimize citation churn.

Declare an ordered `RULES` table in `check.py`. Each row names a stable rule
ID, callable and inputs. Use a small, statically recognizable declaration form
also usable by `build_rules.py`; do not implement plugin discovery. This is a
flat table: rows declare no prerequisites or dependencies on other rule
results. Input declarations describe what a rule reads, not scheduling edges.
The checker attempts every selected rule once in table order. Each rule
obtains its own parsed inputs through tree access and content-keyed parse
reuse; it does not require an earlier rule to have populated state. A result
record contains `rule_id`, stable `diagnostic_key`, repository-relative path
when known, one-based line when known, severity and human-readable message.
Diagnostics may evolve in wording while tests assert identity and location.

Initial input and control ownership is below. Names omit the `check_` prefix;
these are the 19 production rules, not the constructed host controls.

| Rule | Declared inputs | Existing controls / required addition |
| --- | --- | --- |
| `meson_source_lists` | `meson.build`, `meson.options`, native expectation source trees and singleton targets | Seven `meson-*`; real file-mode introspection remains. |
| `readmes_present` | Immediate suite directories and their READMEs | Registry missing README. |
| `index_vs_disk` | Suite directories, catalog, tests README | Registry stray suite; commented suite row. |
| `run_scripts_are_catalog_commands` | Recursive suite `run.sh` inventory and catalog | Registry wrapper/nested-wrapper and removal. |
| `no_direct_case_commands_in_docs` | Repository command-document scope | Six document-route forms plus passing/restored forms. |
| `release_production_runs_the_default_battery` | Makefile, acceptance shell, `tests/lib/release_*.py` | Make selector, argument, comment and acceptance selector. |
| `baseline_in_catalog_defaults` | Catalog, tests README | Add a Baseline suite with all its cases nondefault; restore. |
| `runner_outcome_suites_have_matrix_rows` | Suite directories, normalized matrix | Remove a row for an existing `runner_outcome_*` suite; restore. |
| `normalized_outcomes_have_matrix_rows` | `PWRunnerAPI.swift`, normalized matrix | Commented `ok` row; add converse extra-row control. |
| `attempt_outcomes_have_matrix_rows` | `PWRunnerAPI.swift`, attempt matrix | Add missing and extra row controls and restoration. |
| `attempt_kind_enum_agreement` | `CWorker.swift`, `pw_probe_runner_abi.h` | Add missing value on either side, different names for a shared value, C numeric gap, malformed enum precondition and restoration. |
| `prediction_unavailable_agreement` | `ProbeRunner.swift`, wire constants in `PWRunnerAPI.swift`, guide | Commented pair; add converse document-only pair. |
| `prediction_unavailable_planner` | `CWorkerOrchestrator.swift` | Fourteen planner scenarios. |
| `test_overrides_table_agreement` | `PWRunnerAPI.swift`, runner README | Commented property row; add documented non-property. |
| `harness_guidance_routes` | Root/runner/tests AGENTS and BUILD | Guidance map below. |
| `cli_surface_agreement` | `controller/src/cli.rs`, controller README | Commented usage fence; passing baseline. |
| `host_invariance` | Swift/C/header files recursively under `runner/Sources` | Five file mutations plus relocated constructed-text controls. |
| `known_gap_index` | ARCHITECTURE, BUILD, WORKER | Fifteen gap cases; hidden gap and ordered index. |
| `evidence_channel_paths` | ARCHITECTURE, reply/envelope shape goldens | Hidden table, missing landing cell; add unknown landing path. |

Input declarations must distinguish required files, optional files, directory
membership and patterns, rather than freezing the current filenames. They
also name helper/module dependencies for fixture construction. They are an
auditable dependency account, not a claim of complete program reachability.

Replace the thirteen terminating branches with a typed expected-input failure
carrying location and diagnostic key. Handle known JSON/enum/section/read and
Meson-introspection failures at the owning rule boundary. Preserve reader
refusal as status-1 drift for compatibility. In `check.py`, after all rules run,
choose status 2 if any precondition failed, otherwise 1 for drift, otherwise
0. Do not catch arbitrary programming exceptions and turn them into passing
or missing results. If several rules encounter the same invalid input, each
produces its own precondition record carrying its rule ID and the same input
location/key. Stop that rule's comparison without inventing missing-row
diagnostics; continue the remaining rules. Do not deduplicate these records
into one prerequisite-level failure or suppress a rule based on another
rule's result.

The deterministic summary counts and names rules by outcome: `evaluated`
means the call completed without an input-precondition failure, including a
drift or reader-refusal result; `input_blocked` means the call could not make
its comparison. Each selected rule appears in exactly one category. Do not
reparse inputs to print the summary. A combined control removes the suite
coverage heading and adds a forbidden host binding: exactly
`index_vs_disk` and `baseline_in_catalog_defaults` are input-blocked, each with
its own missing-section record; all other 17 rules run, including the host
diagnostic, and status is 2. Restore the heading and require both rules to
evaluate again. This establishes the flat table's behavior with a shared bad
input, not just with one isolated parser failure.

`build_rules.py` is an explicit exception to the flat execution policy, not
a general dependency scheduler. Keep its existing two-stage entry point:
run `check_banner_order` first, and call the remaining nine rows in table order
only if that result is clean. Preserve the gate for all remaining rules, including the
rows that do not themselves use banner mapping; narrowing it is outside this
repair. When the gate fails, name those nine rows as `gate_blocked` with
`blocked_by: check_banner_order`; do not call them or invent comparison
diagnostics for them. A banner input-precondition failure also closes the
gate. If the gate passes, subsequent rules independently report their own
input failures and do not block later rows. Preserve the build-rule CLI's
existing 0/1 status contract (1 for any reported failure); gate-blocked rows
add no new exit severity. Keep the standalone build generator's existing
banner gate and exit behavior as well.

Control this exception with a banner mismatch plus a knob mismatch: the
banner problem appears, the nine suffix rows are gate-blocked and no knob
comparison runs. Repair just the banner and require the knob problem and all
nine suffix calls to appear; repair the knob and require success. Also cover
an unparseable banner input and a later rule's input failure, distinguishing
gate blocking from independent failure after the gate opens. Document the
exception beside the build registry and in the checked rule-form convention;
there is no implicit prerequisite field for a later refactor to discover.

Move `host_invariance_controls` out of production `main` into the planner.
Run its independent accepted/rejected constructed Swift/C cases once per
canonical case. They are tests of the rule, not an additional production rule.

Migrate citation recognition in the same stage. `generator_common` should
statically read the narrow `RULES` declaration, verify each named function is
defined, and recognize the entry point's use of that table. It must not import
and execute arbitrary cited suite code. Reject malformed/duplicate IDs,
undefined functions and an unused table. Migrate `build_rules.py` to the same
declaration convention with its explicitly described two-stage execution.
Update `FORM_RULES`, its checked README table and
`test_document_graph_cites_every_drift_rule` to
consume this declaration. Keep the graph's rule citations complete. Add
controls for a defined-but-unregistered function, an orphan registry, a
removed/duplicated row and a dispatcher that omits a registered rule. The last
control needs execution evidence; static citation recognition alone cannot
establish it.

### 3. Focused planner and direct-Python controls

Build a fresh tree over the restored/mutated fixture for each scenario and
call only its named rules. Assert the complete expected record set, including
absence of unexpected errors; substring membership alone can hide collateral
failures. Multiple applicable rules may be named, such as for a missing
coverage row. Preserve the mutated inputs, structured records and readable
diagnostics. For registry scenarios, retain explicit created/deleted paths
and their contents, not only a command line.

Keep real subprocess entry-point controls for baseline, combined independent
faults, reader refusal with an independent fault, precondition failure with an
independent fault, and restoration. Assert stdout/stderr, summary, stable
order and exact exit status. Use a nonzero fault in a later rule to prove it
actually ran after a precondition failure. Exercise reversed scenario order,
two roots with the same relative path, same-size content rewritten with its
mtime restored, deleted/recreated files and restoration to demonstrate cache
isolation. A test that removes a rule from execution must fail the integrated
controls even when direct calls to that rule still pass.

Keep the seven file-mode Meson scenarios on real introspection, but call only
their source-list rule. Keep all seven configured-native receipts on the real
Meson/native helper boundary when they move in stage 5. They are not candidates
for replacing Meson with expected dictionaries.

For guidance, preserve all 56 policy/restoration scenarios: eight body-policy
variants for each of four documents, four document restorations and a combined
restoration, six route-policy variants for each of three targets, and route
restoration. These exercise independent prose, wrapping/order, local additions,
missing/duplicate/empty/headings-only sections, resolution, labels, fragments
and placement inside the correct section.

The remaining 73 variants establish reader shapes. Map their original IDs to
these independent reader controls before consolidating repetitions:

| Original guidance variants | Reader owner in `markdown.py` |
| --- | --- |
| Fenced body/section, short close, fake heading before real | `BlockTests.test_fences_close_only_on_the_same_marker_at_least_as_long`, `HeadingTests.test_levels_text_and_where_headings_are_not`; add the exact comment opener inside a fence before a real heading. |
| Comment body/section/route | `CommentTests.test_comments_are_not_prose`, heading control. |
| Indented body, route continuation/example/after-heading | `BlockTests.test_indentation_opens_code_only_where_no_paragraph_continues`; extend with links and explicit expected link presence. |
| Body after peer/parent | `HeadingTests.test_sections_end_at_the_same_or_a_higher_level`. |
| Fenced route, inline example, image, code-label example | `LinkTests.test_images_escapes_code_and_autolinks`; add fenced links and the double-backtick code-label example explicitly. |
| Code label, wrapped/split label | `LinkTests.test_labels_may_hold_code_and_wrap_but_not_cross_a_blank_line`; include the original split-code-label shape. |
| List continuation | `BlockTests.test_list_content_after_a_blank_line_is_prose`; add the exact link-bearing list continuation. |
| Unrecognized inline comment | `CommentTests.test_an_inline_comment_containing_two_hyphens_is_refused`. |

Do not infer equivalence from similar test names: use literal expected blocks,
links, section bounds and refusals for the listed additions. At the guidance
rule layer retain all nine body shapes for one level-2 and one level-3 section,
all twelve route shapes for one target, and the refusal control. That keeps
87 guidance scenarios (56 policy, 31 reader-integration) and transfers the
42 repeated document/target combinations to named reader expectations. Record
each old ID's destination in the map. Preserve the nine cross-rule structure
scenarios: they establish that each consumer uses the reader.

In `direct_python.py`, reuse the same root-aware inventory and expose the
existing file/text checks to focused controls. Test every existing forbidden
command and wrapper/resolver variant against its owner, instead of rescanning
all shell files after each edit. Keep full-tree baseline/restored scans,
combined faults and a mutation of a newly discovered shell script to establish
discovery-to-rule dispatch. Avoid reporting the same entrypoint shell defect
twice merely because that file is both an explicit entry and in the inventory.

### 4. Declared fixture inputs and bounded reuse

Add generator input declarations adjacent to their existing target/output
declarations. Reuse worker identity's existing `source_paths` and `TARGETS`
without editing `generate_worker_identity.py`: that generator hashes its own
source, so an otherwise cosmetic new declaration there changes production
identity. Put its fixture adapter in the shared fixture helper instead.
An `input_paths(root)` interface may combine fixed dependencies,
manifest citation paths, span documents, routed figures, comparison fixtures
and identity-source discovery. Derive outputs from existing `TARGETS`, marker,
span and graph declarations rather than duplicating ownership in another list.
Keep discovery separate from validation: a malformed manifest still has to
reach the generator and exercise its actual refusal. The usual fixture is
copied from a valid baseline before applying its mutation.

Use a shared fixture copier under `tests/lib/` to expand those declarations
and rule inputs. Migrate the planner, direct-Python, generic-generator,
limits, contract, identity, architecture and build checkout helpers. The
reader's small vendored-source fixtures continue using `source_files()` through
the copier. Native-only copies use native/identity declarations. Build-entry
fixtures additionally declare admission files, lock/Python/SDK helpers,
entitlements, augment inventory, version/provenance helpers and all generators
reached before the tested gate. Do not assume that manifest citations enumerate
Python imports, link destinations or subprocess dependencies.

Use structural fixture controls; this plan adds no filesystem read audit,
deny-read sandbox profile or OS tracing. Test declarations with an independent
required-path inventory, relocated fixtures without Git, new native helpers,
a new generator citation/target and an omitted helper causing a clear refusal.
For link checks, include local destination closure, not only source Markdown.

Run copied command entry points in fresh interpreters with the fixture as
their working directory and their script path inside the fixture. In fresh
import controls, assert that the named repository helper modules' resolved
`__file__` paths lie in the fixture. The in-process rule implementation may
load from the real checkout, but receives the fixture tree for subject data;
it must not obtain that data through an import-time/default `ROOT`. Use two
fixtures with the same relative input path and different contents, then
remove the required input from one while it still exists in the real checkout.
Require the different expected observations and then a missing-input refusal.
A deliberately weakened evaluator that ignores the supplied tree and uses
the original root must fail this control's expectations.

Put the copied-generator root/import controls in `generator_contract` and
the in-process root controls in `runner_source_manifests_agree`. Add one fresh
import probe per generator (five Python starts per `generator_contract` run),
reuse existing CLI relocation checks for command execution, and use focused
rule calls for the two-root/missing-input controls. Their cost is those starts
and calls plus fixture construction, recorded in the normal receipts; no
read-observation process runs per fixture. They require no new
equipment or sandbox escalation beyond each case's existing execution
boundaries; do not add a sandbox-sensitive audit to every fixture creation.

These observations establish the tested roots, imports and missing-input
behavior. Declarations remain a reviewed input account: they do not prove
that every file read is declared, detect arbitrary absolute-path reads or
observe all subprocess descendants. Review newly introduced reads and imports
against the declarations. A need for exhaustive read observation would require
a separately specified mechanism, equipment and failure controls; it is not
an acceptance claim of this repair.

Use separate mutable copies per scenario; copy reduction never
licenses mutation leakage or a reduced refusal snapshot. Snapshot the entire
constructed fixture, including unrelated sentinel files and directories, not
only the generator's declared outputs. Preserve detection of unexpected new
files and changes outside owned regions while removing unrelated archive
content from copied input sets.

Place Meson/compiler intermediates under `PW_TEST_SCRATCH`, including the
configured-directory copies used for foreign-root controls. Keep input
snapshots or complete mutated files, command output and receipts under
`PW_TEST_ARTIFACTS` before temporary fixtures are cleaned. Preserve the
source/build-directory relationship each control tests when changing its
storage location; cleanup must not remove the only observation of a failure.

Apply these concrete reductions:

1. Keep `run.sh`'s `build_rules.py` execution as the sole grounding-rule CLI
   owner. Remove the second start in
   `BuildDocumentationTests.test_document_and_figure_are_current_and_the_rules_agree`;
   retain currency and fixture assertions there. Construct the build-rule
   manifest and script model once per tree/pass and share them among rules,
   with explicit banner prerequisite handling. Preserve the same comparisons
   in `generate_build.check/write`: they establish the standalone generator's
   script-agreement and refusal-before-write contract, a distinct checkpoint.
2. Keep repository link scanning and its independent link mutations in
   `GeneratorContractTests.test_prose_links_resolve_anchors_and_symbol_links`.
   Remove only `LimitsDocumentationTests.test_links_in_moved_and_routing_documents`
   and its now-unused imports. Keep standalone guide, shared-source link,
   staging and post-source-removal controls in `limits.py`.
3. Pass one freshly validated limits value through an architecture generator
   invocation's validation and rendering. Preserve full standalone validation
   for callers of `load_manifest`; use an explicit invocation context/internal
   helper, not an unchecked public shortcut or persistent manifest cache.
4. Keep each generator's own currency check and all build gate calls. Keep
   command-level malformed/stale/marker controls, full snapshots before and
   after refusal, idempotence including unchanged mtimes where currently
   asserted, last-render failure before writes, and deliberate ownership
   corruption controls. Do not replace these with return-code-only assertions.

Instrument before extending this list. There is no demonstrated reason to
reuse a validated manifest across changed manifests, skip citations in tests,
batch independent malformed-input command controls into one failure, or remove
fresh compilation. If additional invocation costs remain high, report the
specific boundary they establish. Such justified cost is an acceptable result
of this stage; a broad generator rewrite is not required.

### 5. Build-control ownership and honest cost accounting

Rehome execution controls before the later CHECK account is planned. Add these
three cases under `preflight`, each explicitly `default: true` with its own
`requires` override so it inherits neither the suite's app requirement nor
the existing opt-in build cases' signing requirements:

| New canonical case | Move intact | Equipment |
| --- | --- | --- |
| `preflight/build_entry_controls` | `ContractVersionTests` methods from `test_build_refuses_an_identity_of_another_class_as_absent_before_cargo` through `test_build_refuses_stale_contract_copy_before_signing_or_creating_output`, including both Make controls; the limits stale-guide build control | Preserve the current offline requirements (`[]`); uses macOS shell/SDK/keychain queries and nested sandbox controls, no signed app or identity supplied. |
| `preflight/native_policy_controls` | The three `build.py` Meson methods: per-option policy refusal, bypassed assertion, other output host | `requires: ["meson", "clang", "swift"]`; no signed app. |
| `preflight/native_source_controls` | `check_planner.configured_controls`, all six setup/compile/helper scenarios and the copied-checkout refusal | `requires: ["meson", "clang"]`; no XPC/Swift configuration. |

Use `check_build_entry.py`, `check_native_policy.py` and
`check_native_sources.py` under `tests/suites/preflight/`, selected from its
existing `run.sh`. Share fixture infrastructure through `tests/lib/` rather
than importing one suite's test class from another.

Keep stale-copy-to-generator behavior in source_drift; the moved stale-copy
controls specifically establish enforcement through `build.sh`. Keep identity
generation, ABI golden and reply-shape checks in `contract_versions`. Keep
textual build grounding and its parser/mutation controls in `build_documentation`.
The checker still needs Meson for file-mode introspection. After the move,
`build_documentation` no longer needs Meson itself. Do not merge default
controls into `build_guard_controls` or `build_refusal_controls`, which are
opt-in and need substantially more equipment.

The policy controls currently perform 21 setup/configure/compile sequences;
most compiles trigger an expected regeneration refusal before object
compilation. The bypass control does compile. The output-host controls require
setup and regeneration observations. Preserve these distinctions in receipts.
The C-only configuration builds the worker, validator and extension issuer
(three executables; the old planner docstring says two).
Configured source controls preserve substituted-worker rejection, symlinked,
relative and absolute include escapes, restoration and foreign recorded root.
Do not reuse configured directories across these scenarios without separately
establishing isolation; this plan does not require such reuse.

Update catalog commands/descriptions, both suite READMEs, the tests suite map,
applicable change-verification guidance and build troubleshooting case names.
Move cited functions with stable symbols where practical; update every affected
path in `docs/architecture.json`, `docs/build.json`, limits citations and any
other readers found by repository search. Regenerate with owning generators;
do not edit generated tables. When graph dot content changes, regenerate its
SVG as well; `--skip-svg` does not establish a current SVG stamp. Review
citations for the same asserted scope, not merely a path that now exists.
New test-only Python modules should not
alter worker identity; verify the generator's input closure rather than
regenerating unrelated identity copies to mask a mismatch.

Moving work reduces the source_drift subtotal but is not a performance saving.
Compare the old eight-case total with the new source_drift total **plus all
three new preflight cases**. Keep default selection, no-skip behavior and
the one dispatcher interface intact.

### 6. Receipts, verification and handoff

Add monotonic elapsed time and process accounting at the actual scenario and
command wrappers. Version the receipt schema and document the field meanings
in the owning suite README. A receipt identifies scenario/test/subtest, owner rule IDs,
input changes, execution mode (in-process/CLI/Meson/build), expected and actual
records/status, stdout/stderr paths, elapsed time and direct child launches.
For configured controls count setup and compile as well as the helper; the
existing seven receipts conceal those extra starts. Generator logs need
per-command and per-test timings and copy/snapshot counts/bytes. Write partial
receipts on failure. State exactly what is counted: direct launches are not
an OS-wide count of grandchildren spawned by `build.sh`, Meson or compilers.
Report rule evaluations, inventory entries/descent, manifest loads and fixture
work separately, without summing nested inclusive timings as independent cost.

Use the dispatcher throughout, with fresh `PW_TEST_OUT_DIR` values and
assertions enabled. Record source commit plus any working diff, resolved
Python/equipment, sleep, corpus counts/bytes, output population and cache
conditions. Serialize comparable timing runs under the existing checkout
lock. Never delete retained evidence to improve traversal measurements.
Preserve failed runs; inspect diagnostics and retry an obstructed command once
outside the automation sandbox, keeping the artifact unchanged. A blocked
build gate cannot be counted as a fast successful control.

Verification by stage:

| Stage | Canonical checks and required observation |
| --- | --- |
| Pruning | `source_drift/runner_source_manifests_agree`, `source_drift/direct_python_start`: exact included set and zero excluded-subtree descent. |
| Tree/rules/planner/citations | Those two plus `source_drift/markdown_reader` and `source_drift/generator_contract`; current architecture/build generator cases; per-rule shared-input failures, the build banner-gate exception, combined faults, status 2 for the main checker, dispatch omission and cache/root isolation controls. |
| Fixtures/reuse | All eight source_drift cases: structural root/import and missing-input controls (not a read audit), relocated fixtures, changed dependency invalidation, ownership/refusal snapshots, unchanged generated bytes and idempotence. |
| Rehoming | New preflight cases and all source_drift cases together; dispatcher catalog/selection controls, default `--list` and `--all --list`; every old obligation mapped to a still-default owner with actual equipment. |

The final selected run after rehoming is:

```sh
PW_TEST_OUT_DIR=tests/out/runs/drift-cost-candidate-01 tests/run.sh \
  --suite source_drift \
  --case preflight/build_entry_controls \
  --case preflight/native_policy_controls \
  --case preflight/native_source_controls
```

Also run `dispatcher/selection_controls` and `dispatcher/controls` through
`tests/run.sh` when registration changes. Extend selection controls with the
actual catalog's three new default/offline memberships, so a synthetic catalog
passing does not conceal a wrong `default` or inherited `requires` setting.
Run all five generator `--check` commands through `tests/lib/python.sh` after
regeneration. No signed app build or live witness battery is warranted by
these test/documentation-only changes unless implementation expands into their
dependencies; if that happens, reconsider scope and apply their working rules.

Finish `records/drift-cost-reduction/control-map.json` and
`records/drift-cost-reduction/implementation.md` for this plan's acceptance
review, with the consumer and retirement specified above. They contain:

- The complete 204-scenario old-to-new map, constructed host/direct-Python and
  generator obligations, added missing-rule controls and each remaining CLI
  or native boundary's reason. Consolidated shapes name their independent
  reader assertion and retained rule-integration representative.
- Before/after case and obligation totals, separated from case relocation;
  discovery, subprocess, validation and fixture counts; comparable conditions
  and repeated samples wherever timing variation could change the conclusion.
- Credited run IDs/paths and source snapshots, failures/replacements and any
  explicitly reviewed evidence-reuse exceptions. Raw evidence stays under
  the managed output/retention contract.
- The candidate revision and locations of the live registry, declarations
  and receipt contracts, remaining justified costs and unresolved limitations.
  The later binding inventory reads those live interfaces; it has no dependency
  on this record package. Input declarations and citation membership do
  not establish that a check supports a claim.

Completion means unchanged included discovery with proven early pruning,
fewer unrelated rule evaluations and whole-checker starts, preserved and
strengthened failure reporting, no lost generator/build obligations, and
measured bounded reuse. No numerical speedup is promised. Reconsider a reuse
decision if it needs a new unvalidated cache boundary or prevents independent
mutation/refusal observations; retain that work and explain its measured cost.

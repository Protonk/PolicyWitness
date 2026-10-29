# D1 bounded inventory

Current behavior at `cf0136bbb6366d5f787c3547ec69d757772898c0` (2026-10-29).
The source state is fixed even while implementation proceeds elsewhere. This
is source review plus identified historical cost observations, not a new run
of these checks. `inventory-inputs.json` contains all 29 rule declarations and
their expanded paths, five generator input sets, eleven case declarations and
both baseline contents. `collect.py` reproduces that extraction. Declarations
are not observed filesystem reads or complete dependency proofs.

## Rule tables

The following 19 rows all execute through `check.py` in the default case
`source_drift/runner_source_manifests_agree`. Each callable is `check_<ID>`;
the JSON gives its exact input declaration and helper closure. The table below
adds the contract, limits and controls. `check_planner.py` owns their accepted
and rejected source scenarios, full-record comparisons, reversed order,
fixture-root isolation and command-level combined-fault/blocked-input controls.
Rows run once in table order; an input refusal blocks its own row, not the
others. Exit 2 means blocked input; exit 1 means evaluated disagreement.

| Stable ID | Inputs and binding | Detects; does not establish | Control / name fit / known limitation |
| --- | --- | --- | --- |
| meson_source_lists | meson.build/options, discovered core/shim sources and explicit API/service/client/worker/validator/issuer; structure | Exact per-target membership and duplicate target declarations; not compiler behavior | Dropped/extra/substitute/duplicate targets through real file-mode Meson. Name fits. Configured directory is a separate build checkpoint. |
| readmes_present | suite directory members and READMEs; structure | Missing suite README; not useful coverage prose | Created/deleted suite fixtures. Name fits. |
| index_vs_disk | suite members, catalog, tests README; structure | Suite/table/catalog disagreement; not case quality | Registry scenarios. Name fits. |
| run_scripts_are_catalog_commands | suite run.sh paths, catalog; structure | Unowned wrapper; not dispatch behavior | Added script and restoration. Name fits. |
| no_direct_case_commands_in_docs | pruned command-document scope, Markdown reader; structure | Recognized direct-case commands and retired output path; not all natural-language instructions | Code/prose/fence positive and location/comment negatives. Name accurately describes convention. |
| release_production_runs_the_default_battery | Makefile, acceptance and release helpers; structure | Selectors/extra arguments to battery; not actual release execution | Selector and argument mutations. Name broader than source-only evidence; retain source-convention qualification. |
| baseline_in_catalog_defaults | catalog, tests README; structure | Baseline tier without default case; not adequacy of chosen defaults | Default membership mutation/restoration. Name fits. |
| runner_outcome_suites_have_matrix_rows | suite members, COVERAGE; structure | Outcome-suite rows missing; not witnessed outcomes | Added suite/matrix mutations. Name fits. |
| normalized_outcomes_have_matrix_rows | Swift enum, COVERAGE; value/structure | Enum-vocabulary disagreement; not runtime outcomes | Missing/extra matrix values. Name fits. |
| attempt_outcomes_have_matrix_rows | Swift enum, COVERAGE; value/structure | Same for attempt outcomes | Missing/extra values. Name fits. |
| attempt_kind_enum_agreement | C ABI and CWorker Swift; value agreement | Raw values and normalized names disagree; not matching implementations | Enum mutations. Name fits. |
| prediction_unavailable_agreement | ProbeRunner, API wire constants, guide; value/structure | Selected operation/filter pairs disagree; not OS query availability | Added/missing pairs and syntax variations. Name needs the documented selected-pairs qualifier. |
| prediction_unavailable_planner | CWorkerOrchestrator; source structure | Missing shared-set membership, local copies/shadowing; not Swift semantics | Three/four-pair, literal, comment/string and shadow scenarios. Name fits a source convention. |
| test_overrides_table_agreement | API struct, runner README; value/structure | Property/table keys disagree; not actual seam behavior | Missing/extra keys. Name fits. |
| harness_guidance_routes | root/runner/tests AGENTS and BUILD; navigation | Missing/nonunique/empty section or root route; not sound advice | Heading/body/route mutations. Name fits. |
| cli_surface_agreement | cli.rs usage, controller README text block; identity of selected lines | Exact usage lines absent/different; not CLI implementation | Missing/changed usage blocks. Name needs usage-line qualifier. |
| host_invariance | native files under runner/Sources; source structure | Named sandbox APIs, literal library loads and simple bindings; not computed names or complete Swift/C semantics | Constructed accepted/rejected forms. **F1:** extension functions promised by README are absent from the symbol set; controls derive names from that same set. |
| known_gap_index | architecture/build/worker tours, authored regions; navigation | Missing/misordered index and misplaced Known gap paragraph; not completeness/truth of gaps | Section/index mutations. Name fits. |
| evidence_channel_paths | architecture authored table, reply/envelope shape goldens; pointer/structure | Unknown landing keys; not runtime publication or channel ownership | Missing/unknown landing mutations. Name fits. |

The ten `build_rules.py` rows execute in default
`source_drift/build_documentation`. Each callable is `check_<ID>`. All load
`docs/build.json`, its cited files and the declared shared helpers; the JSON
retains exact expansions. `banner_order` is the sole gate: failure or parse
refusal prevents the other nine evaluations and reports them blocked. After
that gate each row's input failure is local; command status remains 0/1.
`build.py` supplies script/manifest mutations, parser refusal, gate-plus-knob
combined faults, corrupt baseline and restoration controls.

| ID | Additional input / precise binding | Detects; does not establish |
| --- | --- | --- |
| banner_order | build.sh; structural/textual agreement | Banners, order, fresh/incremental condition; not execution order for all shell paths |
| refusals | build.sh; textual agreement | Messages, status, step placement; not refusal firing before protected effect |
| meson_assertions | meson.build; textual/value agreement | Option family/order/template and required output host; not configured enforcement |
| propagated_refusals | build.sh; textual agreement | Represented propagated helper refusal mapping and strict-shell premise; not helper behavior |
| knobs | build.sh; value/textual agreement | Knob names/defaults/values; not environmental behavior |
| signing | build.sh; textual agreement | Calls, flags, step placement; not successful signatures |
| invocations | build.sh; textual agreement | Helper command, subcommand, flags and placement; not helper result |
| makefile_entry | Makefile; textual agreement | Build entry/banner/refusal; not general comment truth (B) |
| inventory | build.sh, artifact.py, build-evidence.py, README, root/service plists; value/structure | Selected executable/path inventory; not produced bytes or signatures |
| baseline | build_baseline.json; structure | Exact manifest refusals without behavioral/helper citations; not citations' assertion adequacy |

These names describe their mechanical subjects adequately when the table's
textual boundary accompanies them. The suite name and first case name understate
their grown responsibilities: native manifests now occupy one of nineteen
rules, alongside registry, prose, source conventions and document generators.
This is an ownership/naming input for D2, not a recommendation to split before
an edit-path trace establishes benefit.

## Generators and controls outside the rule tables

All five generators run read-only currency gates in `build.sh` lines 226–233.
Worker identity is checked again before signing (677); limits stages the
already-checked standalone guide (757). Generation is an authoring action,
never implicit build repair. Input counts below are expanded declarations at
the fixed source, including helpers/citations/targets, not measured reads.

| Owner / default case | Declared inputs and output contract | Other controls, limits and equipment |
| --- | --- | --- |
| generate_contract / contract_versions | 9 paths: manifest, generator and targets; version regions in API/ABI, Rust, test reader and CONTRACT | Identity, unique/schema validation, region ownership, malformed/stale rejection, determinism. Compiled equality belongs to ABI/Swift/Rust cases. Python only. |
| generate_worker_identity / build_documentation | 25 paths: generator, build/Meson/package, discovered C/H/Swift; three identity regions in ABI, CWorker and contract.py | Conservative source identity excludes own generated region; symlink refusal; relocation/helper discovery/handshake/layout controls. Identity is not compatibility. Python only. |
| generate_limits / limits_documentation | 140 paths: limits, comparison matrix, authored shared sections, seven span documents, citations and reader; LIMITS/failure matrix/shared guide/registered spans plus staged whole guide | Identity/value formatting, source/check pointers, standalone links and anchors, staging independent of removed checkout, no partial write on refusal. Does not compare compiled constants. Python only. |
| generate_architecture / architecture_documentation | 238 paths: architecture, limits, registered documents, cited files, dot/SVG and helpers; ARCHITECTURE/WORKER regions, scalar spans and four graph figures | Identity and pointers, document routing, marker ownership, stale dot/table/stamp, source/form validation, all renders before writes. SVG currency tests stamp, not rendered pixels. Graphviz for rendering; not --check. |
| generate_build / build_documentation | 167 paths: manifest/baseline/script/Meson/inventories/plists/citations/reader; BUILD regions, spans and build figure | Same ownership/pointer/stamp contracts plus textual grounding above; malformed shell refuses. Not signing/refusal behavioral proof. Graphviz for rendering, Python for currency. |
| generators.py / generator_contract | Union generator fixtures plus independent sentinel paths; prose scope and link closure; docs baselines | G1–G11: ownership, no writes in --check, complete prevalidation, citations, placeholders, markers, spans, local links and prose registration. Independent known inputs, new target/citation/helper, relocated fresh-interpreter imports and omitted-helper refusal. Generic root-ignoring control verifies fixture isolation. Receipt tests exercise subtest/cleanup errors, changed/deleted/symlink inputs and failed/timeout launches. Python only. |
| markdown.py / markdown_reader | markdown_reader.source_files plus pinned vendor RECORD and import sites | Handwritten parse expectations; vendored byte/version/import guard and only reader imports parser. Structure, not meaning. Python only. |
| direct_python.py / direct_python_start | Six main entrypoints, discovered shell scripts, three wrappers and Python resolver | Source-convention invocation/shebang refusals with accepted comments and a single discovery-dispatch control. Not process ancestry census. Python only. |

`generator_common.citation` is a distinct pointer contract: source citations
match a nonempty symbol substring in a non-Markdown file, so a comment can
satisfy it; Markdown uses reader anchors. Check citations additionally apply
file/form rules, Python definitions, Swift/Rust/shell conventions or catalog
case ownership. A `rule` must appear in a statically read RULES table. `scope`
must be nonempty for worker capabilities but its meaning is not checked.
G4 catches a missing referent; modes 2–5 can all pass.

`repository_tree` gives explicit-root, pruned inventories and cached parsed
reads. `drift_rules` dispatches and reports row outcomes. `fixture_inputs`
expands declarations without replacing generator validation; new manifest
citations are discovered on expansion. `markdown_reader` is the sole pinned
CommonMark parser boundary. `receipts` snapshots registered inputs and explicit
command wrappers. None audits every file read or child process. Source review
found no new demonstrated missing declaration in this bounded inventory;
completeness remains reviewed, not mechanically established.

## Distinct checkpoints

| Canonical checkpoint | Contract, controls and equipment |
| --- | --- |
| tests/run.sh --case preflight/build_entry_controls | Default offline behavioral controls drive unchanged build entry into early refusals and assert no protected outputs/lock. Declared build-entry inputs plus script helpers and relevant generator fixtures. Python and shell; wrappers control observed tool effects. |
| tests/run.sh --case preflight/native_policy_controls | Default real Meson configuration poisons every asserted option, removes one assertion, changes output host; before-compilation refusal is witnessed. Meson/clang/Swift, no signed app. |
| tests/run.sh --case preflight/native_source_controls | Default configured C-only Meson tree, substitutions and include/symlink escapes; configured-directory reader checks evaluated source membership. Meson/clang. Not equivalent to file-mode rule. |
| build.sh native_sources.py --builddir | Real compiled configured directory and compiler input inventory; reads actual build output, no fixture inference. Build toolchain required. Membership/provenance, not behavioral equivalence. |
| tests/lib/release_preflight.py | Current committed HEAD vs previous release tag: exact multisets of prose/build baseline entries must not grow or be rewritten. First baseline is explicitly labeled, not a proven ceiling. Controlled temporary git histories in generators.py cover growth/refusal. |
| runner_abi_layout limits.py compare | Compiled C printer/native/channel values versus selected manifest-owned rows (26 at this source); exact equality, independently owned mappings. Altered manifest is rejected. query_boundary independently fixes 65,534/65,535 byte expectations and drain/recovery; it is a separate behavioral witness. Clang/native execution. Swift/Rust comparisons are citation targets outside this detailed boundary. |
| runner_exec_inheritance/launch_inventory | Opt-in signed app/XPC/process inspection; L trace details claims and assertions. No live execution in D1. |

All eight source_drift cases are default members (suite default inherited).
The two docs baselines are nine exact G9 prose literal sites (zero G11 sites)
and zero unbound build refusals. Empty build baseline means the manifest has
citations, not that a reviewer proved every assertion.

## Costs and remaining questions

`cost-facts.json` records raw receipt digests, run IDs, compact measurements,
input snapshot provenance and current-source differences. `costs.md` interprets
them. No per-rule timing was invented from case totals. Runtime behavioral
adequacy of citation targets is outside this bounded inventory except L and
the limits comparison; extending it requires a named consequential claim.
F1 is the one established promise discrepancy and is reserved for user decision.
The global dependency-completeness question cannot be settled by declaring
more paths; a concrete newly discovered read would require tracing its owner.

# Document ownership and discovery

Current behavior at `7562d24ac2334122499ea349010fd67211058ac3`.
`ownership-facts.json` enumerates every selected document, its role, discovery
membership, generated ownership, each generator's declared inputs/regions and
whole outputs, and all actual scalar names. `capture.py` extracts these facts
read-only. It uses historical bytes for the mutable D2 plan's link destinations
so intake links do not silently change the fixed-source population.

## Reconciled population

There are98 command documents,21 prose/link-scan documents and27 distinct
checked-in generator-owned paths. The latter are10 Markdown files,5 code files
and12 dot/SVG files. The distribution guide is one additional staged whole-file
copy under `${DIST_DIR}/PolicyWitness.md`, validated against its source. The
architecture manifest has5 graphs:4 target ARCHITECTURE and1 targets WORKER.
The reciprocal JSON maps each owned output back to its editable input/generator;
no owned output in these declarations lacks an owner or is omitted below.

| Content family / editable input | Transformation and destinations | Authority and limits |
| --- | --- | --- |
| docs/contract.json versions | generate_contract:7 targets; code regions in PWRunnerAPI.swift, controller/src/json_contract.rs and tests/lib/contract.py; prose regions in CONTRACT, PolicyWitness, controller/runner README | This manifest defines version constants used by implementation and consumers. Currency is shared-input identity, not independent behavior evidence. No ABI-header target here. |
| Runtime constants and docs/limits.json | generate_limits:LIMITS tables, comparison matrix region, guide copies and registered `limits.*` scalar spans | Manifest describes values implemented elsewhere; production does not load it. Compiled equality and independent boundary controls are separate. Source references do not make the manifest the runtime authority. |
| LIMITS shared limits prose, QUESTIONS shared questions | generate_limits renders source spans, demotes question headings, rewrites guide-local references and copies into PolicyWitness | Edit shared source, not copied guide region. QUESTIONS is input-only. Guide structure/internal links and standalone restrictions are checked; prose meaning is reviewed. |
| tests/FAILURE-PROPAGATION-CONTRACT.md shared reading rules / extension status tables | generate_limits copies into PolicyWitness; comparison matrix table comes from tests/fixtures/comparison/matrix.json | Authored interpretation rules/status explanations have an explicit owner. Matrix fixture is the table input. Neither copied agreement nor table rendering proves the implementation's classifier. |
| docs/architecture.json graphs | generate_architecture:4 regions in ARCHITECTURE,1 in WORKER, architecture scalars in registered tours,5 dot/SVG pairs | Structured account describes implementation; source/check definitions are pointers. Limit placeholders use limits.json. SVG checks use dot hash stamps, not image equivalence. |
| docs/build.json and build.sh/Meson/inventory files | generate_build:BUILD figure,6 tables,build scalars and one dot/SVG pair | Manifest is a descriptive account grounded by textual comparisons. Actual refusal/signature behavior requires its cited controls; input can be faithfully rendered yet wrong. |
| Protocol/build native source set | generate_worker_identity:ABI header,CWorker.swift,tests/lib/contract.py identity regions | Digest of declared/discovered source bytes, excluding own generated identity regions. Conservative identity, not compatibility or correctness. Contract-generated API changes feed this digest. |
| Authored prose outside owned regions | Edit its containing README, guide, tour, contract or AGENTS; selected documents get source conventions/navigation/G9/G11 checks | No transformation unless a registered span/shared block says otherwise. Link and structural checks do not judge claims. Root/directory CLAUDE aliases edit adjacent AGENTS, not separate copies. |
| docs/worker-launch-observation.json | Manually authored compact observation record cited by WORKER | Dated evidence, not generated current truth. No live applicability comparison. Current pin availability needs refresh; former L pins are absent at this fixed source too. |

The10 generated Markdown destinations are controller/README,runner/README,
ARCHITECTURE,BUILD,CONTRACT,LIMITS,PolicyWitness,REQUEST-GRAMMAR,WORKER and
FAILURE-PROPAGATION-CONTRACT. Other permanent docs (DEPENDENCIES,QUESTIONS,
SIGNING and docs/AGENTS) are authored inputs/accounts; QUESTIONS supplies copied
prose. The root README owns orientation and the documentation index. Working
rules belong to AGENTS; detailed suite/fixture accounts remain beside their
equipment. Plans are transient yet some participate in discovery.

## Separate scopes, not one global document registry

| Selector / checkpoint | Population and exclusions at this source | What author changes need |
| --- | --- | --- |
| repository_tree.COMMAND_DOCUMENTS; check.py no_direct_case_commands_in_docs |98 recursively discovered .md entries; prune records,dist/archive,dist/evidence,tests/out,.tmp,builddir*,controller/target,vendor,runner/.build; omit hidden components; no directory symlink traversal | New ordinary visible Markdown is automatically checked for recognized direct-case command forms. This is not G11 link coverage. File symlink candidates remain visible. |
| generators.scanned_documents; generator_contract G9/G11 |21 docs:all docs/*.md, explicit root/AGENTS/controller+runner AGENTS/tests README+AGENTS, plus Markdown generator region targets | docs/*.md inclusion automatic, including D2 plan. Other READMEs can be command-scanned without G11. New ordinary document outside this population is not silently registered by linking it. |
| generators.prose_inputs | Selected docs plus direct local link destinations, including code/assets/associated records | Fixture closure carries destinations for checking links; it does not recursively add their prose to the G9/G11 scan. D2 plan links make its records fixture inputs without making those records scanned documents. |
| Generator target/span declarations | Explicit7 contract targets,3 identity targets; architecture tours2,limits scalar docs7,build scalar doc1; dynamic manifest graph destinations must be registered | A new span outside registered destinations is refused; no declaration is inferred from prose. Multiple owners may share a file through distinct regions/prefixes, not the same content. |
| Known-gap indexing | Only ARCHITECTURE,BUILD,WORKER | A new ordinary Markdown file gains no gap-index check automatically. This is a scope fact, not a future-tour registration task. |
| Root route/index and suite registry rules | Named guidance sections/routes and suite coverage tables | These separately enforce navigation/membership. No blanket semantic coverage or all-README link guarantee. |
| Release baseline | Committed prose/build baseline vs nearest earlier annotated release | Exact-site additions/rewrites refuse; initial baseline/no prior baseline is labeled. `--report` is diagnostic warning mode. Does not scan every changed sentence. |

Command discovery includes seven transient plans: WORKSET-PLAN,
WORKSET-EXECUTION-PLAN,D2 plan,ATLAS-BUILD-PLAN,SWITCH-CONTROL-CHANGE-PLAN,
HOST-SETUP-ORACLE-PLAN and D1 plan. Only the D2 plan is in the21-document prose
scan. Recording scope does not authorize executing excluded plans. All output,
record and vendor exclusions have an identifiable owner; absence from one
scan is not evidence absence from every declaration or citation closure.

## Evidence ownership

Generator tests own accepted/stale/malformed/restoration assertions; shared
receipt code records those controls' registered inputs and direct launches.
The semantic author/reviewer owns whether source supports a claim. Native cases
own observations under their conditions; retention owns raw availability.
Descriptive manifests may cite a case without that case asserting the statement.
The D33 stale attribution is an actual example, localized in reconciliation.

Source inspection establishes this routing. Historical receipt selections in
`trace-evidence.json` identify prior executions of unchanged relevant control
code, with source differences disclosed; they are not new current-tree passes.

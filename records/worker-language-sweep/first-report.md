# First descriptive inventory — worker language

Frozen source revision: `2d63c983224907b109b4349d216c03471a8b1f0c`.

This is the collector's first classification, frozen before handoff. It inventories limiting language; it does not adjudicate truth, test adequacy, needed wording, or historical origins. It contains no removal, move or rewrite recommendations.

The user narrowed the original assignment before this freeze. The inventory covers **WORKER.md and its owning manifest, generator/map and direct document-verification machinery**. Earlier broader searches were stopped. Other documentation and source comments read during that initial search remain context or excluded coverage; they do not become separate inventory entries merely because they concern the worker.

## Counts and counting units

| Layer | A1 | B1 / C2 | B1 / D2 | Total |
| --- | ---: | ---: | ---: | ---: |
| WORKER authored account | 32 | 24 | 2 | 58 |
| WORKER generated inventory/account | 164 | 94 | 5 | 263 |
| Direct document machinery | 0 | 2 | 0 | 2 |
| **Total** | **196** | **120** | **7** | **323** |

There are 127 primary B1 units. Every B1 has C2 or D2; each unit has exactly one primary A1/B1 classification. The `repository` layer in JSON means the two direct-machinery occurrences, **not a repository-wide sweep**.

These are **inventory units/occurrences, not 323 unique semantic claims or claim families**. Authored units are generally a statement or tightly related paragraph; generated units are usually a resource-specific cell. Several cells contain closely related clauses and retain a secondary-role explanation. Each resource's repeated `Source-only` qualifier remains attached to that resource. Authored summaries and generated cells can state related propositions and are linked by family notes. Copies of generated clauses in the owning manifest are duplicate locations, not additional entries: 262 inventory entries link their exact owning manifest value. The caption also links its repeated summary and generator strings.

## Descriptive pattern

A1 is prominent in the resource inventory: no explicit closes/unmaps/resets, inheritance exclusions, absent entitlement/token/query transfers, restrictions on admitted extension/exec combinations, bounded or single-call behavior, discarded native returns, and exceptional lifetimes. The authored account also describes once-per-specimen application, received process state, cleanup interrupted by worker death, unobserved escaped descendants, and token-erasure paths that earlier exits can bypass. These describe the instrument or its supplied/reporting apparatus, even when the grammatical subject is a descriptor, host setup action, issuer channel or exec child.

B1 repeatedly distinguishes source placement from observed gating, test definitions from asserted coverage, a bounded launch observation from a full isolation/authority census, PW-owned storage from private native state, publication from native effect, spawn from helper outcome, process-group targeting from complete cleanup, extension release from revocation, and query-before-attempt ordering from a snapshot.

The largest B1 family comes from the generated table. Eighty-one C2 assignments use the specific **`Sandbox-gated` column organization beside source/check citations** as the local invitation to overread evidence scope. Their qualifiers are statements such as source-only, observed under a named control, unknown, not rerun, or not measured. This is an organizational interpretation, marked medium confidence; it is not a claim about reader psychology or why the author originally wrote the qualifiers.

Other C2 triggers are more concrete: “A fresh worker / applies one specimen once” for possible isolation overreading; fixed/static worker storage for possible native-allocation overreading; the before-consume/during-use/after-release fresh-read sequence for revocation overreading; completed-slot publication for absent-effect overreading; and collection closure before release for snapshot overreading. Exact independent trigger quotes and individual rationales are in JSON. A shared topic alone was not treated as sufficient: private ownership, entire native allocation erasure, automatic-frame byte erasure and log causality retain several D2 assignments.

The seven D2 units are:

| ID | Location | Guard |
| --- | --- | --- |
| N009 | WORKER.md:261–262 | Private apply ownership changes remain unobserved. |
| N038 | WORKER.md:440–443 | Bounded issuer erasure does not observe allocation beyond the bound. |
| N098 | WORKER.md:89 | Loader/process teardown internals remain unobserved. |
| N191 | WORKER.md:118 | Compiled-profile allocation lifetime inside apply is unknown. |
| N266 | WORKER.md:144 | Temporary precompile frames make no byte-erasure claim. |
| N270 | WORKER.md:145 | Capture/hash frames make no byte-erasure claim. |
| N300 | WORKER.md:221 | Candidate log association is not worker-native cause. |

Their external textual motivation is **unknown**. This neither establishes external origin nor says the guards are unnecessary. Some related cells have C2 because they primarily qualify the table's evidence/gating organization, whereas a separate lifecycle/erasure clause states a narrower epistemic limit with no identified inviting local claim. That difference is intentional and visible rather than forced into uniform classification.

## Machinery and coverage

The complete 536-line WORKER document was read, including all 83 generated nodes, 55 edges, legend, notes and final gap index. Ordinary positive labels and relationships were not converted into invented negative statements. Exact exclusions cover positive introductions, relationship edges, procedural instructions and noncandidate machinery prose.

The `worker_capabilities` graph in `docs/architecture.json` was reviewed through its generated account and owning values, including column declarations, labels, clusters and notes. `docs/generate_architecture.py` was read for validation, routing, graph/tooltip/table rendering, captions, copy/stamp checks and writes. The map account is therefore covered through its owning inputs and generator; rendered DOT/SVG copies are not separately counted, and this was not a visual/geometry audit.

Direct verification review covered `tests/suites/source_drift/architecture.py`, the WORKER Known-gap indexing functions in `check.py`, the generator-contract explanation in the suite README, and relevant citation/definition routines in `docs/generator_common.py`. The latter's definition-versus-assertion comment and the README's G10 caption rule are the two direct-machinery B1 occurrences. Structural rules about routing, marker ownership, files and check-mode writing are contextual machinery rather than worker propositions. This inventory does not infer what a behavioral test establishes merely because its symbol is cited.

Historical plans, investigations, prior records and agents' reports were excluded as classification sources. Build/dist/output/scratch copies, lockfiles, raw fixtures/assertions/enum spellings, and unrelated host/controller/build/test propositions were also excluded. Broader reads made before the scope amendment are disclosed in JSON coverage; they are not claimed as complete or added to the entry population.

## Ambiguities and limits

Resource-cell granularity makes the generated table dominate the counts. These totals should not be read as how many distinct ideas exist, how much prose is necessary, or a measure of documentation quality. Source-only labels and positive placement clauses can coexist in one cell: the evidence limitation is primary B1, while actual resource context is retained as secondary. Conversely, actual missing cleanup/reset behavior is A1 even when it has interpretive consequences.

The generated inventory includes host/issuer apparatus supporting the worker. This first inventory retains those clauses as requested; a strictly process-only reading of A1 could exclude some of them. The records identify each resource and preserve that boundary for review.

C2 is a descriptive judgment about a plausible exact inference invited by local wording or organization, not proof of historical causation. The medium-confidence table/header, fresh-worker and static-storage assignments remain explicit uncertainties. D2 means no sufficiently specific local trigger was identified in this read, not that no possible trigger exists.

Full document reading plus contextual search is not an exhaustive semantic census of repository language. No build, runtime test, generator/check command, source/document edit or commit was performed. Static JSON/schema and frozen-line quote validation passed for all 323 entries and 727 nested quoted references. The first classification remains immutable after handoff; any later correction belongs in a separate follow-up artifact.

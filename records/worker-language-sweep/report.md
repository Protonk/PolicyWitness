# Descriptive sweep of worker limiting language

The sweep is complete against `2d63c983224907b109b4349d216c03471a8b1f0c`.
It covers [WORKER.md](../../docs/WORKER.md) and its owning manifest, generator,
map and direct document-verification machinery. It is a language classification,
not a truth audit, editorial decision, register adjudication or pass 6.

The readable collection is `inventory.md`; `inventory.json` retains the complete
source context, exact quotations, classifications, rationales, triggers,
confidence, secondary roles and associated manifest occurrences. IDs are stable
across collection, review and reconciliation. No underlying claim was rewritten.

## Final primary classifications

| Layer | A1 | B1 | C2 within B1 | D2 within B1 | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| WORKER authored account | 33 | 24 | 18 | 6 | 57 |
| WORKER generated account | 172 | 75 | 24 | 51 | 247 |
| Direct verification machinery | 0 | 2 | 2 | 0 | 2 |
| **Total** | **205** | **101** | **44** | **57** | **306** |

These are statement/paragraph/cell occurrences, not unique claim families or
atomic proposition counts. Manifest copies are associated locations rather than
additional units. Each included occurrence has one primary A1/B1 classification;
C2 and D2 partition primary B1. Secondary roles do not add to these totals.
Twenty-three candidates remain recorded as scope exclusions, with their wording
and reasons preserved in the inventory.

## What the sweep found

**A1 is dominated by resource and interface facts.** Missing explicit closes,
unmaps or resets; discarded returns; inheritance exclusions; bounded inputs;
and exceptional lifetimes describe the instrument. For example, the compiled
profile's missing explicit destruction call (N008), the discarded sysctl value
(N033), and the worker's prediction/publication boundary (N041/N045) remain A1.
An observation of actual behavior does not become B1 merely because it appears
in a column discussing evidence or gating.

**C2 needs an exact invitation.** The query-before-release sequence can invite a
snapshot inference (N044/N052); release followed by fresh reads can invite a
revocation inference (N039/N040/N241); and source/check pairings can invite an
assertion-coverage inference (N057/N305/N306). The word “fresh” did not support a
complete Mach-right or runtime-state census, and a `Sandbox-gated` heading did
not by itself assert that a test ran or a private state was measured. Those
generic triggers accounted for much of the first classification's overuse of C2.

**D2 does not require an invented external source.** The final D2 entries record
external origin as unknown. Their scope is the absence of an identified specific
local trigger, not proof that the wording originated elsewhere, that no reader
could make the inference, or that the qualification is unnecessary. Conversely,
the denial-log guard N300 moved from D2 to C2 because the document explicitly
associates denial-log candidates with run evidence.

**The supporting apparatus requires a scope distinction.** Pure issuer/host
allocation, teardown or internal-state statements were excluded. Statements
about what reaches the worker, its children, or its reporting/authority boundary
were retained. Six issuer “no child” cells remain A1 at medium confidence only
under their table-column meaning: the worker-exec-child transfer boundary.
Their free-standing issuer-only reading would be outside scope. Each carries
that condition explicitly.

**Some occurrences serve more than one role.** N004 combines cleanup-inference
limits with actual reference lifetimes. N040 combines several native-state,
identity and permission guards whose local triggers differ. Its release/state
inferences are primary C2; stable-identity/private-allocation limits retain
secondary D2 treatment. N285/N287/N289/N291/N293 combine an actual outside-worker
boundary with a source-only qualifier. The collection preserves these roles
without presenting one trigger as support for every clause. Nine C2 occurrences
carry explicit partial-trigger flags. This round retains occurrence granularity;
it does not claim an atomic clause census.

## Collection, challenge and reconciliation

The collector read the complete document, its 83 generated nodes and 55 edges,
and its direct machinery. The user clarified the scope before the first
classification froze; earlier broader searches supplied no standalone inventory
entries. The original prompts and `scope-amendment.txt` preserve that boundary.

A second agent read WORKER and its machinery before seeing the frozen collection,
then reviewed all 323 initial IDs and all six coverage additions. The coordinator
reviewed the classifications, replacement triggers, scope exclusions and mixed
roles. The final inventory adopts the review's primary assignments and makes
secondary roles explicit in `coordinator-overrides.json`.

Among retained units, 53 changed C2 to D2, 12 changed B1 to A1, and one changed
D2 to C2. Other corrections replaced weak triggers without changing the bucket.
The six coverage additions came from a separate 243-cell keyword cross-check:
four remain included and two are issuer-only exclusions. This cross-check aids
coverage; it does not establish semantic exhaustiveness.

`first-inventory.json` and `first-report.md` preserve the immutable first result.
`coverage-followup.json` and `coverage-followup.md` preserve the separate coverage
work. `trigger-review.json` and `trigger-review.txt` preserve the independent
review unchanged; its Markdown source is stored as plain text so quoted relative
links do not become broken record links. `reconciliation.json` records the
applied changes. These are descriptive classifications, not decisions to remove,
move or rewrite text.

## Validation and limits

Frozen-source quotation and structure checks passed for the first inventory
(727 references), coverage follow-up (42), independent review (511), and final
inventory (681, including its excluded/context references). Review-ID coverage,
primary count partitions, artifact hashes and record links are checked separately.
`validation.json` and `artifacts.sha256` retain the results and artifact identities.
The one-off `verify_inventory.py`, `reconcile.py` and `render_inventory.py` helpers
operate on these records; they add no repository enforcement rule.

No build, runtime test, generator execution or SVG geometry audit was performed.
The review classifies what the document says and what may invite an inference;
it does not verify the implementation claims. WORKER, its manifest, generator,
production source, tests and register dispositions are unchanged. Only these
records and the associated plan's Status were updated. No push or release;
pass 6 remains reserved for a fresh agent.

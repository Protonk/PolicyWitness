# A-docs-generation-reading — DT-01 through DT-21

Read-only assessment at `main` HEAD `837296af`, 2026-11-17. Review anchors:
`records/DOCUMENTATION-TRACE-REVIEW.md` lines 23–652 (DT-01–10 observed at
`bfc74b6b`, DT-11–21 at `4816b0e4`). 71 claims are assessed below, grouped by the
five coverage-map rows, plus the two unnumbered qualification sections in the
range.

## Method, evidence classes and limits of this pass

- **Unchanged code.** `git diff --stat bfc74b6b HEAD` is empty for
  `docs/contract/presentation.py`, `docs/contract/tree.py`,
  `docs/contract/record_definitions.py`, `docs/markdown_reader.py` and
  `tests/suites/source_drift/contract_tree_controls.py`. The
  `bba8bca3..2f4d76e4` changes to `docs/contract/runtime.py` (lines 247–298) and
  `docs/generate_contract_stamps.py` (lines 78–83, 90, 122, 128, 137) add the
  development/publication switch and the frozen-guide check; they do not touch
  region validation, rebasing, the indexes or the controls. `docs/publication.py`
  is new. So DT-01–04 concern code that is byte-identical to what the review read.
- **In-memory probes (constructed, not live).** Scripts under
  `.tmp/trace-integration/assessments/work-A-docs-generation-reading/`
  (`probe_dt01_04.py`, `probe_dt04.py`, `probe_tree.py`, `probe_dt12.py`,
  `probe_dt17.py`, `probe_dt18.py`, `probe_dt18b.py`, `probe_dt21.py`) import the
  generator modules through `tests/lib/python.sh`, load the tree from the checkout
  and call `presentation.render` / `presentation.rebase` on an overlay object or
  constructed strings. No generator was run in a writing mode and no file outside
  the work directory was written.
- **Retained output read, not treated as the named historical runs.**
  `tests/out/runs/` holds eleven `trace-*` development runs dated 2026-11-17/18;
  `tests/out/release-acceptance/` holds
  `run-9e17e41c6b99440c8359cf2163b7cfa1` (run id `20261111T145311Z_7a4a9f53`);
  `dist/archive/` holds `v0.3.4`–`v0.3.7`. The review's
  `documentation-trace-default`, `-final-controls` and `-fixture-recheck`
  directories are absent. These are gitignored development observations with
  ordinary retention.
- **Not executed.** No build, test case, generator write, `policy-witness run`
  submission or signed-app specimen. The review's signed-app reproduction for
  DT-15 used the `8b5de2b2` app; `dist/PolicyWitness.app` is now build 1519 at
  `2f4d76e4`, and that reproduction was not repeated.
- **One deviation from the brief's command list.** I invoked
  `dist/PolicyWitness.app/Contents/MacOS/policy-witness run --help` once,
  expecting help text. It returned an argument-refusal envelope
  (`request_path: null`, `runner_provenance: null`, `app_provenance: null`), the
  `Arguments::Error` branch at `controller/src/run_flow.rs:523-531`, which returns
  before the manifest load, runner selection and any client call. No request was
  read and no runner was contacted. It was not repeated.
- **Working tree changed by another actor during this pass.** `git status` was
  clean at the start. Near the end it showed `tests/catalog.json` and
  `tests/suites/source_drift/run.sh` modified and
  `tests/suites/source_drift/test_markdown_reader.py` untracked (the
  `source_drift/markdown_reader` case moving to a pytest module). This pass made
  none of those changes and wrote only under
  `.tmp/trace-integration/assessments/`. Every citation below is to HEAD
  `837296af`; none depends on the three changed paths.

Treatment vocabulary used below: *behavior* (product or generator behavior
change), *assertion* (assertion/coverage repair), *account* (correction of the
account in its owner), *arrangement*, *retention*. None of the recommended edits
touches a build-contract input (`docs/build_contract.py:15-27`: the seven source
roots and the listed files); the alternatives that would are marked.

---

## Subject 1 — DT-01–04: contract generation (four preservation properties)

### 1.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-01.a | With one declared region nested inside another, the pre-assembly inventory passes, `render` returns, and the inner region's markers and statements are gone from the returned document. | Input: hand-edited destination markers (policy BEGIN moved before request BEGIN in REQUEST). Representation: in-memory return of `presentation.render`. Observer: the generator's caller. Time: first generation. | **Yes, with one narrower detail.** `docs/contract/presentation.py:167-172` compares marker names and counts; `:119-125` checks each pair's own order; `:176-194` replaces sequentially. Re-run at HEAD: request markers absent, 25 of 115 anchors absent including `<a id="contract-request-specimen">`, 1289→958 lines. The review said the output contains no `contract-request-specimen`; the string still occurs 7 times, in link targets written by other regions, and 6 distinct local contract link targets then have no anchor. | Review: disposable-copy reproduction, not retained. Now: re-read plus constructed in-memory overlay. | Contradicted explicit commitment (`docs/contract/README.md:113-114`). |
| DT-01.b | Qualification: a rendering reproduction, not a CLI write; a later invocation detects the missing marker; committed regions are not nested; the observation limits what pre-write validation establishes. | Same. | **Yes.** A second render over the damaged output refuses with "orphaned or missing region" (probe). Committed REQUEST regions are sequential (`request`, `policy`, `probes`, `actors`, `extensions`, `helper`). The CLI writes `render`'s results with no further destination check (`docs/generate_contract_stamps.py:128-136`; read, not executed). `--check` on such a document already refuses, as stale. | Re-read plus in-memory. | Accurate observation; qualification retained. |
| DT-02.a | Renaming a destination key in the map while the old file remains leaves the old file's generated statements in place and outside `destinations`, `ownership` and the returned outputs. | Input: map edit plus copied file. Representation: in-memory render. Observer: generator and its controls. Time: every generation after the move. | **Yes.** `presentation.py:76-79`, `:163-172`, `:209-217`. Probe: outputs and ownership name `docs/REQUEST-ALT.md` only; the on-disk REQUEST keeps `contract-request-specimen`. | As above. | Contradicted explicit commitment (the stated intent at `presentation.py:161-162`; G1's "exactly one generator" at `tests/suites/source_drift/README.md:356-359`). |
| DT-02.b | The statement-coverage control counts anchors only in the newly rendered mapping; link resolution does not expose a stale duplicate. | Observer: `source_drift/build_contracts`, `source_drift/generator_contract`. | **Yes.** `tests/suites/source_drift/contract_tree_controls.py:1335-1339` sums over `rendered.values()`; `tests/suites/source_drift/generators.py:179-229` resolves targets and never counts duplicates. | Re-read. | Overstated coverage credit. |
| DT-02.c | Qualification: establishes the ownership omission; no complete mutated-checkout test run is claimed; bears on future document moves. | — | **Yes**; this pass also ran no suite on a mutated checkout. | — | Accurate observation. |
| DT-03.a | Rebasing rewrites the destination text of an escaped-bracket literal when a live link to the same target shares its paragraph. | Input: constructed string. Representation: `rebase` return. | **Yes.** `presentation.py:98-109`: the regular expression matches every `](dest` in the inline range. Probe output equals the review's. The literal alone, with no live link, is unchanged. | Constructed in-memory, both passes. | Overstated coverage credit: the control's name says rebasing changes links "only" (`contract_tree_controls.py:1266`); no authored instance. |
| DT-03.b | A percent-encoded live link is not rewritten: the reader decodes the target, the rewrite looks up the raw spelling. | Same. | **Yes, narrower consequence.** `presentation.py:103`. The reader returns `#contract-demo` for both links (probe). In an emitted document the unrewritten link is then reported by `broken_links` as a missing heading when the node's home is another document (`generators.py:192-194`, `:225-227`; read, not executed). The surface-side check accepts the encoded spelling (`generators.py:195-221`). So the miss does not pass `source_drift`; it produces a late refusal that names the generated document, not the surface. | Constructed in-memory plus re-read. | Contradicted explicit commitment in a bounded form (`README.md:96`: "Rendering resolves these links"). |
| DT-03.c | Qualification: verified transformation behaviors, not errors in current authored passages; existing rebasing controls cover inline code and reference forms but not these. | — | **Yes.** No `%`-encoded contract link and no `\[` occurs in `docs/contract/*.surface.md` (grep). Control at `contract_tree_controls.py:1266-1301`. | Re-read. | Accurate observation. |
| DT-04.a | The scope-preservation control looks for required phrases anywhere in a destination and checks the order of one pair of case anchors; a condition moved away from its rule still passes. | Observer: `source_drift/build_contracts`. | **Yes.** `contract_tree_controls.py:1350-1392`. Replayed in memory: the sentence "A grant was admitted and a fresh continuous-clock sample is before the original deadline." (authored at `docs/contract/20-transport.surface.md:125`, rendered once at `docs/ARCHITECTURE.md:106` under `contract-transport-delivery-invoke`) was removed from its rule and appended under a final unrelated heading; every predicate still passed. | Constructed in-memory, both passes. | Overstated coverage credit (`README.md:125-127`, "representative scope preservation"). |
| DT-04.b | Qualification: no detachment in committed output; the controls establish presence and selected ordering only. | — | **Yes** (rendered output equals disk for all six region documents; probe). | In-memory. | Accurate observation. |

### 1.2 Comparison

Stated obligations and their owners:

- `docs/contract/README.md:110-114`: "The generator replaces only declared
  contract regions beside REQUEST, RESPONSE and tour prose; CONTRACT is a
  whole-file output. … The generator validates all destinations before writing,
  and `--check` writes nothing."
- `tests/suites/source_drift/README.md:356-359` (G1): "Every region … and
  whole-file output has exactly one generator, which changes no byte outside
  them. A document holds each marker pair once, in order; a broken pair stops the
  generator before any write."
- `docs/contract/presentation.py:161-162` (comment): "An obsolete marker must not
  keep an old statement alive outside the declared region inventory. Validate
  every destination before assembly."
- `docs/contract/README.md:94-99`: "Rendering resolves these links to the node's
  mapped document. The link checker verifies that the rendered destination
  actually contains the anchor. Other document paths retain their literal
  destinations".
- `docs/contract/README.md:125-127`: the generator controls "check coverage,
  region boundaries, links, history, freshness and representative scope
  preservation; they do not decide whether a statement is accurate or useful."
- `docs/AGENTS.md:19-21`: "Keep inherited conditions, first-match order and owner
  scope with the statement".

Producer (observed): validation inspects only documents the map names, and only
marker names and counts per document; replacement is sequential by string index;
rebasing rewrites by destination text within inline ranges that hold at least one
parsed link.

Checks (observed): `generators.py:1067-1099`
(`test_contract_map_refusals_validate_every_destination_before_writing`) mutates
the map four ways (duplicate, unknown, omitted, missing region) and asserts
refusal with an unchanged snapshot; it has no document-side mutation.
`contract_tree_controls.py:1317-1348` asserts one anchor per node across the
rendered mapping. `:1350-1392` asserts phrase presence per document.

Inference kept apart: none of the four behaviors is present in the committed
tree. Each is a property of future edits (hand-moved markers, a destination
move, an unusual link spelling, a renderer regression).

### 1.3 Plausible treatments

**DT-01.**
(a) *Behavior (generator)*: in `presentation.render`, before assembly, require
that the declared regions of each document are disjoint (each BEGIN is followed
by its own END before any other BEGIN). File: `docs/contract/presentation.py`
near `:167-172`. Not a build-contract input. Consequence: none for well-formed
documents; a nested pair becomes a named refusal from generation and `--check`.
Must reject: a generation that returns or writes a destination lacking any
declared region.
(b) *Retention* with the limit "destination validation checks each region's own
markers; one declared region nested in another is reported only by the next
check, after the first generation has written". Costs nothing now and leaves
`README.md:113-114` false for that input unless reworded.

**DT-02.**
(a) *Behavior (generator)*: refuse, before any write, a
`GENERATED CONTRACT <region>` marker in a Markdown document directly under
`docs/` that the map does not name. Files: `docs/contract/presentation.py`
(validation loop) and `docs/generate_contract_stamps.py:78-83` (`input_paths`
must declare the scanned documents, because fixtures copy declared inputs and
receipts track them). Today such markers occur only in the seven destinations
(grep), so there is no present false refusal. Must reject: a map whose
destination was renamed while the old document still carries regions.
(b) *Assertion*: extend `contract_tree_controls.py:1335-1339` to count each node
anchor across every `docs/*.md` on disk as well as the rendered mapping. Test-only;
also catches a stale copy whose markers were stripped; detects at
`source_drift/build_contracts` time, not at generation or build.
(c) *Retention* with an authoring rule in `docs/contract/AGENTS.md`: "Remove the
statement regions from a document the map no longer names; generation inspects
only mapped destinations."

**DT-03.**
(a) *Retention with a stated authoring limit* in `docs/contract/README.md` beside
lines 94–99.
(b) *Behavior (generator)*: make `rebase` refuse when the destinations it would
rewrite in an inline range are not exactly the links the reader reports (decode
before lookup; compare counts). File: `docs/contract/presentation.py:82-116`.
Machinery cost: the reader exposes only line ranges (`link.inline.lines`), so the
comparison is per inline range and must keep every accepted form in the existing
control (`contract_tree_controls.py:1267-1287`) passing; images and link text
containing `](` are false-refusal risks that need their own controls. Friction:
none today (no instance); a future author with either spelling gets an immediate
named refusal.

**DT-04.**
(a) *Assertion*: make the control positional: each required phrase must lie
between its own rule anchor and the next `<a id="contract-` anchor. File:
`tests/suites/source_drift/contract_tree_controls.py:1350-1392`. Test-only. Must
reject: the phrase present in the document but outside its rule (the in-memory
move in `probe_dt04.py` is the rejecting control).
(b) *Account*: reword `README.md:125-127` to "representative phrase presence and
selected case order".

### 1.4 Recommended dispositions

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-01.a | Treatment (a). | Exact semantics, no false-refusal risk, and it makes `README.md:113-114` and G1 true for this input. Control: add a nested-marker document mutation to `generators.py::test_contract_map_refusals_validate_every_destination_before_writing` (case `source_drift/generator_contract`): both `--check` and generation refuse and the checkout snapshot is unchanged. |
| DT-01.b | Retain the qualification as the recorded boundary: no committed document is affected. | Further evidence would not change it; the committed markers were read. |
| DT-02.a | Treatment (a), with (b) as the backstop for a copy without markers. | The stated intent at `presentation.py:161-162` is otherwise unenforced, and a stale copy keeps resolving inbound links. Control in the same `generators.py` test: (i) rename the key, copy the file, keep the old file → refused, snapshot unchanged; (ii) same with the old file's regions removed → accepted. |
| DT-02.b | Treatment (b). | Makes the credited "one statement home" assertion cover the documents readers can open. Case `source_drift/build_contracts`. |
| DT-02.c | No change. | It is a limit of the observation, and it still applies to this pass. |
| DT-03.a | Retention with the stated limit (treatment a). Accepted limit, to stand in `docs/contract/README.md` after "Rendering resolves these links to the node's mapped document.": "Rebasing matches destination text within a paragraph that holds a link; show literal link syntax in a code span, not behind an escaped bracket." | No authored instance; the only effect is displayed literal text; treatment (b) changes a working rewrite path that every regeneration in this work depends on. If refusal is preferred over the limit, (b) is the alternative and its two rejecting controls are the review's two input strings. |
| DT-03.b | Retention with the stated limit: "Write contract links with unencoded destinations." (same paragraph). | The existing link check already refuses the unrewritten link in the emitted document: `test_prose_links_resolve_anchors_and_symbol_links` requires `broken_links(scanned_documents()) == []` (`generators.py:782-783`, case `source_drift/generator_contract`). The generator's own `--check` and the build's stale-copy check do not detect it. Further evidence would not change the decision. |
| DT-03.c | No change. | Accurate. |
| DT-04.a | Treatment (a). | Small, test-only, and makes "scope preservation" an asserted property for the representative phrases. Case `source_drift/build_contracts`. |
| DT-04.b | No change. | Accurate. |

### 1.5 Resulting user duties

None. These concern authors and maintainers of the documentation generator.

### 1.6 Implementation worklist

Items A.1, A.2, A.4 and A.5 (DT-01, DT-02, DT-04) and B.4 (DT-03) of the
consolidated worklist at the end; verification D.1–D.3.

---

## Subject 2 — DT-05–08: ownership label, changed-item lookup, example provenance, development-input inventory

### 2.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-05.a | The changed-item index labels every `node.record` "imported record declaration", including twelve records the model marks `authored=True`. | Representation: generated index in CONTRACT. Observer: a reviewer reading provenance. | **Yes.** `docs/contract/presentation.py:147-148`; `docs/contract/tree.py:630-665`. Probe lists the same twelve: `VersionData`, `ControllerSelectionOptions`, `ControllerRunnerSelector`, `ValidatorDirectStatus`, `ValidatorDirectResult`, `ValidatorDirectError`, `RunnerReconcileData`, `RunnerReconcileRecord`, `RunnerReconcileCandidate`, `RunnerReconcileInspectionError`, `RunnerCleanupObservation`, `RunnerCleanupWait`. Rows at `docs/CONTRACT.md:706-707`. | Source inspection, both passes; computed from the loaded tree. | Inaccurate mechanism account. |
| DT-05.b | A reader could infer independent source-declaration extraction where the shape is authored beside its meaning. | Inference by the review. | The inference is reasonable: for these twelve, shape and meaning come from one authored file, so a change to the Rust producer is not detected by any import. | Reading. | Consequential ambiguity (follows from DT-05.a). |
| DT-06.a | The index has no row for `controller/src/interface/result.rs`, `controller/interface/inventory.json`, `cards.rs`, `joins.json` or `mutations.json`; it lists the identifier `result.admitted_finished`. | Representation: index rows. | **Yes.** No such path in `docs/CONTRACT.md`; identifier row at `:1301`. | Search. | Accurate observation. |
| DT-06.b | The generator emits each interface identifier without resolving the inventory relationship, although the inventory names the reader and the joins hold case and mutation associations. | — | **Yes.** `presentation.py:149-150`; `controller/interface/inventory.json:730-733` (`reader.path` `controller/src/interface/result.rs`, `pub fn select`); `joins.json` holds one case and five mutation entries for `result.admitted_finished`. Six nodes carry ten identifiers. | Re-read. | Accurate observation. |
| DT-06.c | Qualification: the interface README link permits manual investigation and the introduction calls the associations partial; the observation does not assume a complete impact map. | — | **Yes.** `docs/contract/trace-introduction.md:22-25`, `:27-30`; row label "interface association; see the partial join". | Re-read. | Accurate observation needing no change. |
| DT-07.a | The RESPONSE opening excerpt is authored outside generated regions; changing `EXAMPLE_DOCUMENT` changes the generated REQUEST example and leaves the excerpt. | Representation: authored fence at `docs/RESPONSE.md:125-137`, described at `:121-123` as "the second action's two operands in EXAMPLE_DOCUMENT". First generated region at `:215`. | **Yes.** The fence is outside every region. The overlay probe was not repeated; the mechanism follows from placement. | Review: in-memory source overlay. Now: re-read. | Unsupported inference waiting to happen: the "excerpt of" claim has no check. |
| DT-07.b | Qualification: the current excerpt matches its source; no freshness check ties it to the second action. | — | **Yes.** `controller/src/example_document.rs:6`: the second action of `initial-reads` queries `file-read-metadata` on `/usr/share/dict/propernames` and attempts `read_fresh` on `/usr/share/dict/connectives`. `dict/connectives` occurs in no test or fixture. | Re-read plus search. | Accurate observation. |
| DT-08.a | The development-identity input statement omits the selected directory `controller/interface`. | Statement: `docs/contract/00-identity.surface.md:63-73` (`identity.public.inputs`), rendered at `docs/CONTRACT.md:79-90`. | **Yes, and wider.** `docs/build_contract.py:15-16` selects seven roots; the statement names six. At HEAD it also omits the file `docs/publication.py`, added to `FILES` at `build_contract.py:20` by `bba8bca3`. A set comparison of `DIRECTORIES`/`FILES`/`SUFFIXES` with the paragraph's backticked names gives exactly those two "in code, not in statement" and none the other way. | Source inspection plus a read-only set comparison. | Contradicted explicit commitment (the statement enumerates the inputs). |
| DT-08.b | The omission predates the reorganization and remains in the statement supporting the tracing path. | History. | Not re-derived; DT-91 carries the per-commit history. | — | Accurate observation. |

### 2.2 Comparison

- DT-05: the index introduction (`presentation.py:135-136`) says "Declarations own
  meaning; source and check citations supply the stated support."
  `docs/contract/README.md:72-74` distinguishes the two cases correctly: "Imported
  field types and presence come from `record_definitions.py`. For an authored
  record absent from those imports, each field supplies `type`". The producer
  collapses them into one label. No control reads the label (search of
  `tests/suites`, `tests/lib`).
- DT-06 and the index: `trace-introduction.md:3-4` invites "the changed
  declaration, implementation, generated interface or check"; `:22-25` then says
  "Source and interface associations are partial: an absent association is an
  unknown". Both statements are true together; the index carries identifiers, not
  interface file paths.
- DT-07: `docs/contract/AGENTS.md` says "Change an extracted example at the source
  its `document` fact cites and regenerate; no surface restates that document."
  RESPONSE's authored opening is not a surface, and it does restate part of the
  document. The REQUEST example is covered by
  `test_example_source_edit_is_stale_until_regeneration_and_moves_content_and_identity`
  (`generators.py`); nothing covers the RESPONSE fence.
- DT-08: the only enumeration of the identity roots in the tree is the surface
  paragraph (search for `runner/augments` across docs and manifests).
  `docs/build.json:390` refers to "shipped sources and build inputs through
  docs/build_contract.py" without listing them. **Owner of the statement:**
  `docs/contract/00-identity.surface.md`, definition `identity.public.inputs`; not
  `docs/build.json`. The producer is `docs/build_contract.py:15-27`. Its support
  owner (`00-identity.surface.md:101-108`) credits digest sensitivity to source
  mutations, not agreement between the paragraph and the code.

### 2.3 Plausible treatments

**DT-05.** (a) *Behavior (generator)*: label rows from the record's own flag,
"authored record declaration" when `tree.records[node.record].get('authored')`.
File `docs/contract/presentation.py:147-148`; regenerates `docs/CONTRACT.md` only.
(b) *Retention*: leaves a false provenance label on twelve rows.

**DT-06.** (a) *Retention*, relying on the limit already stated at
`trace-introduction.md:22-25`. (b) *Arrangement*: add a row per interface
association keyed by the inventory's reader `path: symbol`. About ten rows;
generator change; covers `result.rs` and the entry readers, not `inventory.json`,
`joins.json` or `mutations.json`.

**DT-07.** (a) *Assertion*: a drift rule comparing the fenced JSON under
"Read the published example" with the second action of phase `initial-reads` in
`EXAMPLE_DOCUMENT`, minus `step_id`. Files: `tests/suites/source_drift/check.py`
(`RULES`, with declared inputs `docs/RESPONSE.md` and
`controller/src/example_document.rs`) and its planner control in
`check_planner.py`. (b) *Arrangement*: replace the fence with an extracted
`example` node using `document` + `member`; moves teaching text into a generated
region, renders `step_id`, and changes the public payload. (c) *Retention* with a
limit in `docs/AGENTS.md`.

**DT-08.** (a) *Account*: add `controller/interface` to the directory list and
`docs/publication.py` to the file list at `00-identity.surface.md:63-73`;
regenerate. Public definition text changes; `identity` is already `unreleased`
(`docs/CONTRACT.md:498`), so the stamp table does not change. (b) *Assertion*:
a control that compares the paragraph's names with `DIRECTORIES`, `FILES` and
`SUFFIXES` and rejects a statement missing a selected input.

### 2.4 Recommended dispositions

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-05.a | Treatment (a). | The label is false for twelve rows and the model already holds the fact. New control in `ContractPresentationTests` (case `source_drift/build_contracts`): `ControllerSelectionOptions` carries the authored label and `PWRunnerRunSpec` the imported one; it must reject a renderer that labels every record row imported. |
| DT-05.b | Closed by DT-05.a. | — |
| DT-06.a, .b, .c | Retention, no edit. Accepted limit (already present at `docs/contract/trace-introduction.md:22-25`): "Source and interface associations are partial: an absent association is an unknown". | The stated account is accurate and names the interface account as the route. The identifier rows are checked by the interface join (`docs/contract/interface_join.py`). More rows would not change what a reviewer must do with an absent association. |
| DT-07.a, .b | Treatment (a). | The claim "excerpt of EXAMPLE_DOCUMENT" is true today and has no guard, while the same constant already forces regeneration elsewhere. The rule must reject a fence that differs from the second action in any operand. Case `source_drift/runner_source_manifests_agree` (the `check.py` rules). |
| DT-08.a | Treatment (a) now. | The statement enumerates inputs and is false in two members. Verification of the corrected text: the set comparison above returns empty both ways. |
| DT-08.b | No change in this pass. | Executed contrast, history and any standing statement/code agreement control (treatment b) belong to the development-identity pass that owns DT-91; the statement has drifted twice (`b16f32d0`, `bba8bca3`), which is that pass's evidence for the control. |

### 2.5 Resulting user duties

None. A developer relying on the identity statement must, until DT-08.a lands,
read `docs/build_contract.py` for the input set; that is a developer matter, not
an ordinary user's.

### 2.6 Implementation worklist

Items A.3 and A.5 (DT-05), A.6 (DT-07) and C.1 (DT-08) of the consolidated
worklist; DT-06 needs no edit; verification D.1–D.3.

---

## Subject 3 — DT-09–10: optional log collection; unavailable-clock timeout semantics

### 3.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-09.a | The single-worker run sequence in ARCHITECTURE ends with "optional logs;" between "complete execution;" and "print envelope". | Representation: authored text block at `docs/ARCHITECTURE.md:277-304`, the line at `:302`. Outside every generated region (regions end at `:245` and resume at `:342`). | **Yes.** | Re-read. | Inaccurate mechanism account. |
| DT-09.b | CONTROLLER says the run path gathers no external log candidates, and `run`/`complete_execution` contain no log stage. | `docs/CONTROLLER.md:238-240`; `controller/src/run_flow.rs:521-726`, `:728`. | **Yes.** The admitted branch (`run_flow.rs:692-712`) goes `admit_reply` → `complete_execution` → `execution_parts` → `envelope`. No log reader exists under `controller/src`, `runner/Sources`, `runner/Clients` or `runner/Services` (search for `log show`, `OSLog`, `os_log`, `log_capture`). `docs/QUESTIONS.md:65` (a shared-region owner) agrees: "If you collect unified logs separately". | Source inspection, both passes. | Accurate observation: this account matches the code. |
| DT-09.c | The optional-log line was retained from an older tour. | History. | **Yes.** The line first appears with `66d41b5e`, when `controller/src/sandbox_log.rs` and a `sandbox-log-observer` binary existed; `19e580b7` ("Retire the unified-log observer") removed them. | Read-only git. | Accurate observation. |
| DT-10.a | `actors.phase.order` says "Arrival or completion timeout cancels for exhausted execution allowance". | Statement: `docs/contract/13-actors.surface.md:225` (`free.effect`), rendered under `docs/REQUEST.md:1034`. | **Yes.** | Re-read. | — (statement as quoted). |
| DT-10.b | A source path reaches that label when the clock cannot establish remaining allowance: a fault makes `remainingNs()` return nil, the scheduler evaluates `(clock.remainingNs() ?? 0) == 0`, selects `completion_timeout`, and after an established reap selects `execution_allowance_exhausted`. | Observer: host scheduler. Time: after collection, before release. | **Yes.** `runner/Sources/PWRunnerCore/CWorker.swift:924-931`, `:948-951`, `:1033-1038`; `runner/Sources/PWRunnerCore/ActorScheduler.swift:412`, `:425`, `:472-477`. | Source inspection, both passes. | Accurate observation of mechanism. |
| DT-10.c | Qualification: source-established, conditional on reaching collection and later reaping the actor; no clock-fault specimen executed; the raw wait record can retain `clock_fault`. | — | **Yes**, and the condition is narrower than the code requires (see 3.2). The record is built at `CWorker.swift:1040-1045` with `clock_fault: clockFault` and `elapsed_ms` nil after a fault. No scheduler test injects a failing clock (`runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift:303-313` and `:334-362` assert the label under a zero or a measured-exhausted allowance). | Source inspection; unverifiable by execution in this pass. | Accurate observation. |
| DT-10.d | The public wording does not say whether it describes the selected classification or establishes that time was exhausted. | Reader of REQUEST and of `schedule.cancelled`. | **Yes.** `docs/contract/33-actor_evidence.surface.md:544-546` gives `cancelled` as a "Recorded schedule cancellation reason, such as … execution_allowance_exhausted" with no reference to the wait record. | Re-read. | Consequential ambiguity. |

### 3.2 Comparison

**DT-09.** Two authored accounts in two owners: the sequence block in
`docs/ARCHITECTURE.md` ("One run in time"), and the prose in `docs/CONTROLLER.md`
("Receiving and evaluating evidence"). Neither is generated; neither is a shared
region copied into the guide. The code matches CONTROLLER. No control reads the
block (search of `tests/suites/source_drift` and `tests/fixtures/docs`).

**DT-10.** Obligation as stated (owner `docs/contract/13-actors.surface.md:225`):
"Arrival or completion timeout cancels for exhausted execution allowance, and a
wait error cancels for lost ownership."

Producer (observed by reading): the scheduler maps an unavailable remaining
value to zero at three sites, not one:

- `ActorScheduler.swift:320-324`, at the start of each schedule entry: sets
  `cancelled = "execution_allowance_exhausted"` and `stop = "deadline"` directly.
  This site needs neither collection nor a reap.
- `:425`, after collection: `completion_timeout` (the review's path).
- `:442-443`, in the completion loop: `completion_timeout`.

The same mapping feeds the termination gate's budget (`:337`, then `:516`), where
a zero budget gives the gate outcome `execution_allowance_exhausted`.

`HostWaitClock` documents a different discipline for its own waits ("the wait
spends only the last remaining allowance in nominal sleeps", `CWorker.swift:900-902`);
the scheduler's `?? 0` does not use that fallback. The published wait is
`schedule.execution_wait` (`ActorOrchestration.swift:519`), a `PWHostWait` whose
`elapsed_ms` is absent and `clock_fault` true after a fault
(`docs/contract/32-lifecycle.surface.md:284-286`, `:300-302`). So the returned
evidence already separates a measured exhaustion from an unavailable clock; the
operator statement and the `cancelled` meaning do not tell the reader to look.

Reachability (inference, not observation): the production clock is
`clock_gettime(CLOCK_MONOTONIC)` (`MonotonicDeadline.swift:8`); a fault needs
that call to fail or go backwards. The path is reachable by injection through
`ChildProcessCalls.clock` in a unit test.

The limits row `actor_execution_allowance` (`docs/limits.json:884`, effect
"Expiry ends the current visit (`arrival_timeout` or `completion_timeout`) and
cancels the remaining schedule") states what expiry does and is not contradicted.

### 3.3 Plausible treatments

**DT-09.** (a) *Account*: delete the line `optional logs;` at
`docs/ARCHITECTURE.md:302`. Hand-authored; no generator; not a build-contract
input. (b) Changing CONTROLLER instead would make the accurate account false.

**DT-10.**
(a) *Account*, two owners. Request side, `13-actors.surface.md:225`: say that an
arrival or completion wait ending with no remaining allowance, including one
whose clock can no longer supply a remaining value, cancels under the
execution-allowance label. Returned side, `33-actor_evidence.surface.md:546`:
say that `execution_allowance_exhausted` is the scheduler's classification and
that `execution_wait.elapsed_ms` and `execution_wait.clock_fault` show whether
exhaustion was measured. Public prose in two surfaces (`actors`,
`actor_evidence`, both already `unreleased`); free-text counts unchanged; no
build-contract input.
(b) *Behavior*: give the unavailable clock its own cancellation value and stop.
Touches `runner/Sources/PWRunnerCore/ActorScheduler.swift` (build-contract
input, signed rebuild), the Rust and Python readers of `cancelled`, and the
release pre-check at `:425`, which routes
`witness_contract/order_barrier_mutations`. Adds a public vocabulary value for a
state the production clock is not expected to produce.
(c) *Retention* without edit: leaves DT-10.d open.

### 3.4 Recommended dispositions

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-09.a | Treatment (a): correct ARCHITECTURE. | The owner of the false account is the ARCHITECTURE block; the code and two other accounts agree with each other. Support for the revised scope: after removal the block's tail reads decode / admit / complete / print, which is `run_flow.rs:692-712` in order. Further evidence would not change it: there is no log-reading code to exercise. |
| DT-09.b | No change to CONTROLLER. | It matches the code. |
| DT-09.c | No change. | History only. |
| DT-10.a, .d | Treatment (a). | It separates the operator account (how the scheduler classifies) from what an observed cancellation establishes, using records the product already returns. The wording decision rests on the unconditional `?? 0` at three sites; executing a clock-fault trial would not change it. |
| DT-10.b | Recorded as established by source at all three sites; the corrected wording must cover the pre-visit site (`:320-324`), not only the post-collection one. | — |
| DT-10.c | Retained as the evidence limit. If the schedule-support owner (`13-actors.surface.md:241-250`) is to credit the new clause as check-read, add a constructed control to `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift`: `calls.clock` returns nil after the collection hook; expect `cancelled == "execution_allowance_exhausted"`, `executionWait.stop == "deadline"`, `executionWait.clock_fault == true`, `executionWait.elapsed_ms == nil`, beside the existing measured contrast at `:334-362`. Case `runner_unit/pwrunner_core_unit_executable`. Without it the clause stays source-read and the owner must say so. | `runner/Tests` is not a build-contract input. |

### 3.5 Resulting user duties

- DT-09: none.
- DT-10: a user reading `schedule.cancelled: "execution_allowance_exhausted"` must
  not conclude that the allowance was measured as exhausted unless
  `schedule.execution_wait.elapsed_ms` is present and
  `schedule.execution_wait.clock_fault` is false. Standing: established by source
  reading; not exercised.

### 3.6 Implementation worklist

Items B.1 (DT-09), C.2 and C.3 (DT-10) of the consolidated worklist;
verification D.1–D.3, and D.4 only if the optional unit control is added.

---

## Subject 4 — DT-11–14: executed evidence availability, historical counts, barrier support, declared check links

### 4.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-11.a | Nine owners carry `grade: "executed"` and name three runs (`20261111T155411Z_29ef0802` ×5, `20261111T162345Z_3d6c7242` ×3, `20261110T195016Z_0d197151` ×1); this checkout holds none of them. | Observer: a reader following an executed citation from this checkout. | **Yes.** Owners at `14-extensions.surface.md:486`, `21-wire.surface.md:126`, `:140`, `:285`, `33-actor_evidence.surface.md:157`, `35-profile.surface.md:343`, `41-diagnostics.surface.md:761`, `:1154`, `:1168`; `Run:` lines at `docs/CONTRACT.md:2109`, `2291`, `2298`, `2319`, `2473`, `2571`, `2620`, `2634`, `2641`. No `run.json` under `tests/out` or `dist` carries any of the three ids; the only other occurrences are copies of the contract documents inside the release acceptance's generator receipts. | Search of this checkout, both passes. | Overstated coverage credit as presented: executed credit with no stated availability. |
| DT-11.b | Five owners identify their source as `reviewed-inputs sha256:<digest> (b6ce6d26 dirty)`; the tree states neither the input set nor the framing, and the dirty state is unrecorded. | — | **Yes, for six owners, not five.** `source_snapshot` at `21-wire.surface.md:134`, `:148`, `33-actor_evidence.surface.md:165`, `41-diagnostics.surface.md:769`, `:1162`, `:1176`; three read `(b6ce6d26 dirty)` and three `(b6ce6d26 dirty; replay identity correction)`. The surfaces are unchanged since the review's tree, so the count of five was a miscount. `reviewed-inputs` occurs only in three surfaces, `docs/CONTRACT.md` and the review. Git history holds no definition (`git log -S` finds only the introducing commit `eac1482e`). `b6ce6d26` exists. | Search plus read-only git. | Consequential ambiguity; **information genuinely missing**. |
| DT-11.c | By contrast the direct-validator owner lists three per-file SHA-256 values that the current files reproduce. | `21-wire.surface.md:293`. | **Yes**: `shasum -a 256` of `sb_api_validator.c`, `no_report.c` and `validator_batch_mode/run.sh` gives the three recorded values. | Reproduced now. | Accurate observation. |
| DT-11.d | The profile owner says "its development run is disposable"; the other eight state no availability limit; the tree requires only nonempty `run` and one of `source_snapshot`/`build`; the grade says the named run "exercised the stated assertions with its identified source or build". | — | **Yes.** `35-profile.surface.md:350`; `tree.py:789-795`; `tree.py:84`, rendered at `docs/CONTRACT.md:1696`. | Re-read. | Accurate observation; the eight owners omit a limit their authoring rule asks for (`docs/contract/AGENTS.md`: "Preserve specific native, constructed-input, shortened-budget, missing-assertion and retention limits"). |
| DT-11.e | Limit: only this checkout was searched. | — | Still so. | — | Accurate limit. |
| DT-12.a | Two executed owners share "Swift judgments over 142 typed frames … Rust replay carried 143 frames … and seven JSON-only controls", while the cited check symbols link current files whose corpus is ten frames larger. | `33-actor_evidence.surface.md:161`, `41-diagnostics.surface.md:765`; rendered at `docs/RESPONSE.md:1376`, `:3083`. | **Yes.** The review's comparison run is gone; the present development run `trace-instrument-after-corrected` (`20261118T011154Z_5cfcec0a`) holds 152 Swift cases, 153 Rust and 153 Python with 7 JSON-only, and 152 `.pwp` frames. | Retained development output, read now; not the named run. | Accurate observation: the sentence is scoped to its run. |
| DT-12.b | Other quoted counts agree with later local runs: 42 subject controls (12 accept, 30 refuse); a 621-byte fallback with two writer failures at a 134,217,729-byte input. | — | **Partly re-read.** `writer-cap-receipt.json` in the present run: `emitted_bytes` 621, `input_utf8_bytes` 134217729, two writer failures. The 42/12/30 count was not re-read. | Retained development output. | Accurate observation. |
| DT-12.c | Of fourteen cited source and check files examined, nine have one to five later commits and five have none. | — | **Same pattern, different denominator.** Over all 22 files the executed owners cite, 13 have one to five commits after `b6ce6d26` and 9 have none. The review's fourteen are not identified. | Read-only git. | Accurate observation. |
| DT-13.a | The barrier statement's support defers to "execution owners" that no surface owner supplies. | `13-actors.surface.md:239` ("Integrated collection/release and mutation observations retain their own execution owners."), `:250` ("retain their separate owners"); `31-steps.surface.md:656` ("no new execution or mutation-control run is credited"). | **Yes.** No surface and none of CONTRACT, REQUEST, RESPONSE names `order_barrier_mutations` or `opt_in/mutations.sh`. | Search. | Unsupported inference invited by the limits text. |
| DT-13.b | Root, tests and runner guidance name that control as the one to rerun; `architecture.json` cites it for T8 and B4; the statement and its support do not link it. | — | **Yes.** `AGENTS.md:37`, `tests/AGENTS.md:64`, `runner/AGENTS.md:17`; `docs/architecture.json:920-921`, `:1840-1841`; `docs/ARCHITECTURE.md:227`, `:630`; `tests/CHANGE-VERIFICATION.md:663-697`. | Search. | Accurate observation. |
| DT-13.c | The changed-item index has 26 rows for `pw_probe_runner.c` and none for `wait_for_proceed`; the nine `CWorker.swift` rows route only `runCWorker` to this commitment. | — | **Yes.** 26 rows; `wait_for_proceed` (`controller/tools/pw_probe_runner/pw_probe_runner.c:1205`) absent from CONTRACT; `docs/CONTRACT.md:1386-1394`, with `:1393` the only row to this commitment. | Search. | Accurate observation. |
| DT-13.d | Qualification: this concerns missing direct associations, not whether the barrier holds. | — | Still so. | — | Accurate. |
| DT-14.a | Each surface declares `checks`; the tree verifies only that the list is nonempty catalog suite names; the key is excluded from public content and no renderer reads it. | — | **Yes.** `tree.py:927-935`, `:80`; `docs/contract/README.md:80-81`. The review did not cite `tests/suites/source_drift/README.md:406-409`, present at its revision too: "The surface manifest’s `checks` entries name catalog suites that own verification; they are validated as suite names, not G5 assertion citations. Their presence does not establish a defined assertion or coverage of the surface’s behavior." | Re-read. | Accurate observation; the cited sentence's "that own verification" is the overstated part. |
| DT-14.b | The declarations do not match what owners cite: eleven surfaces declare `failure_boundaries` and no owner cites a check under that suite; `10-request` and `13-actors` declare only it; `32-lifecycle` declares `runner_unit` and its owners cite no check. | — | **Yes.** Recomputed per surface (`probe_tree.py`). | Computed from the loaded tree. | Overstated coverage credit in non-public metadata. |
| DT-14.c | Capacity-refusal support cites only the Swift entry point; the suite's `admission` case through the signed CLI has no route from CONTRACT. | `15-refusals.surface.md:112-120`; `docs/RESPONSE.md:617-618`; `tests/suites/failure_boundaries/README.md:3-18`. | **Yes.** | Re-read. | Accurate observation. |
| DT-14.d | The comparison rules cite only `runComparisonEvidenceTests`; the failure contract names `witness_contract/comparison_matrix` as the live owner. | `31-steps.surface.md:734`, `:771`; `tests/FAILURE-PROPAGATION-CONTRACT.md:1537-1540`. | **Yes.** The owners' own limits say so in words ("Integrated matrix cases own the live rows, without execution credit here", `31-steps.surface.md:737`). | Re-read. | Accurate observation. |
| DT-14.e | 152 owners (82 source-read, 61 check-read, 9 executed) cite checks in 16 files under `tests/suites/`; the catalog holds 283 cases in 42 suites; CONTRACT's introduction calls source and interface associations partial and says nothing about check associations. | — | **Yes** on every count. `trace-introduction.md:22-25`. | Computed. | Consequential ambiguity (the introduction's silence). |
| DT-14.f | Limit: whether `failure_boundaries` exercises each of the eleven declaring surfaces was not examined. | — | Lightly read here, not examined case by case: the suite's README never mentions actors or extensions; `tests/suites/failure_boundaries/check.py:117` has one actor-form request (an oversized `equipment` field) and nothing on extension actions. | Reading. | Accurate limit, slightly narrowed. |

### 4.2 Comparison

**Executed grade (DT-11, DT-12).** Stated: `tree.py:84`, "The named run exercised
the stated assertions with its identified source or build." Authoring rule,
`docs/contract/AGENTS.md`: "Execution credit identifies the run and the
source/build exercised; release credit identifies the acceptance case", and
"Preserve specific … retention limits". Retention rule, `tests/AGENTS.md`:
"Development results are disposable once inactive … Cite development observations
with their availability limits; do not describe them as retained release
evidence." Producer: `_owner` accepts any nonempty strings. No owner carries
`release` (probe), so all nine are development credit. Observed: the runs are
not on this machine. Not established: whether they exist anywhere else.

**Barrier (DT-13).** Stated commitment: "Close the active phase's eligible
prediction collection before releasing its actions". Its support is source-read
over `eligibleOrderedStep` and check-read over `runActorSchedulerTests`; both
limits point to owners elsewhere without naming them. The control that exercises
the barrier is routed by guidance and cited by the architecture manifest. The
only missing link is from the commitment's own support and from the worker wait
in the changed-item index.

**`checks` (DT-14).** The declaration is unread metadata. Two descriptions
exist: `docs/contract/README.md:80-81` ("`checks` names catalog suites") and the
`source_drift` README sentence quoted above. No guidance tells anyone to select
verification from `checks`; `tests/AGENTS.md` routes admission changes to
`failure_boundaries` independently.

### 4.3 Plausible treatments

**DT-11 / DT-12.**
(a) *Account at the definition*: extend `SUPPORT_GRADES['executed']`
(`docs/contract/tree.py:84`) so the grade itself states the two limits every
executed entry shares. The text is rendered only at `docs/CONTRACT.md:1696`; it
is not in `public.json` and no test pins it.
(b) *Account per owner*: add a retention sentence to the `limits` of the eight
owners that lack one, and, for the six `reviewed-inputs` owners, a sentence
that the digest cannot be recomputed from the tree. Owner metadata is outside
the public payload.
(c) *Reclassification* of the nine to `check_read`: discards a true historical
statement and changes nine rendered support paragraphs.
(d) *Re-execution* and re-credit with a present run: replaces one disposable
development run with another. Durable credit exists only as release credit
(`release` + `case`), and no release occurs during this work.
(e) For DT-12.a alone, removing the counts from the two `context` strings.

**DT-13.**
(a) *Account*: reword the two `limits` strings (`13-actors.surface.md:239`,
`:250`) to say that this tree credits no integrated collection/release or
mutation execution and to name `witness_contract/order_barrier_mutations` as the
routed control.
(b) *Assertion/coverage*: add the source citation
`controller/tools/pw_probe_runner/pw_probe_runner.c: wait_for_proceed` to the
barrier's source-read owner, and a check citation
`tests/suites/witness_contract/opt_in/mutations.sh: order_barrier_mutations`
(form `test`, grade check-read, the same spelling `architecture.json` uses) after
reading the control. Each adds a changed-item row to this commitment.
(c) *Retention*: the route exists through guidance and ARCHITECTURE.

**DT-14.**
(a) *Account*: one word in `docs/contract/trace-introduction.md:22-23` ("Source,
check and interface associations are partial"), and correct the description of
`checks` in `tests/suites/source_drift/README.md:406-409` and
`docs/contract/README.md:80-81` to what is validated.
(b) *Arrangement*: align the nineteen declarations with the suites their owners
cite and add a tree validation relating them. New machinery for metadata nothing
reads.
(c) *Coverage*: add check citations for `failure_boundaries` `admission` and
`witness_contract/comparison_matrix` to the two owners.

### 4.4 Recommended dispositions

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-11.a, .d, .e | Treatment (a), keeping the grades. Proposed definition text: "**executed:** The named run exercised the stated assertions with its identified source or build. A development run is disposable test output and may no longer be held; source and check links name the current files, which can differ from that source." | One sentence makes all nine entries true for any checkout, which a per-machine search cannot. Searching other machines would change availability on one machine, not the account. Unavailable execution stays unavailable: no present run is substituted. |
| DT-11.b | Treatment (b) for the six owners (`21-wire.surface.md:126`, `:140`; `33-actor_evidence.surface.md:157`; `41-diagnostics.surface.md:761`, `:1154`, `:1168`; they share two digests): add to `limits` "The reviewed-inputs digest names an input set and framing this tree does not record; it cannot be recomputed here." | **Missing information:** what the two digests (`b5298841…`, `af396aad…`) covered. Neither the tree nor history records it; only the author of `eac1482e` could supply it. If supplied, record the input list instead. |
| DT-11.c | No change. | Reproduces. |
| DT-12.a, .c | Covered by the definition sentence; leave the two `context` strings. | The counts are scoped to their run and nothing shows them wrong for it. The definition now says why the linked files can differ. |
| DT-12.b | No change. | Agrees where re-read. |
| DT-13.a | Treatment (a). Proposed limit for `:239`: "The source owner describes eligibility. No owner in this tree credits integrated collection/release or mutation execution; `witness_contract/order_barrier_mutations` is the control routed for changes to the wait, release store or eligibility rule." Matching change at `:250`. | Removes the pointer to owners that do not exist while stating the real route. Existing discriminating control for the behavior itself: `witness_contract/order_barrier_mutations` (non-default). |
| DT-13.b | No change to guidance or the architecture manifest. | Accurate. |
| DT-13.c | Treatment (b), source citation only, in the same edit; the check citation only if its author reads `mutations.sh` and states its context and limits (non-default, no run credited). | The source row is cheap and gives the worker wait a route to the barrier commitment in the advertised index. |
| DT-13.d | Retained. | — |
| DT-14.a, .b, .f | Treatment (a) for the two descriptions; retain the declarations. Accepted limit, for `tests/suites/source_drift/README.md` and `docs/contract/README.md`: "A surface's `checks` list is validated only as catalog suite names; it is not compared with the checks its owners cite and selects no verification for a surface change." | The metadata is unread and non-public; aligning nineteen fences adds work and a new rule without changing what any reader or check does. A case-by-case reading of `failure_boundaries` would not change this. |
| DT-14.c, .d | Retention under the corrected introduction. | Both integrated cases are routed by `tests/AGENTS.md` and the failure contract's ownership table, and the two owners' limits already say that integrated cases own the live rows. |
| DT-14.e | Treatment (a), the one-word correction. | Makes the introduction's partiality statement cover the association kind the review found partial. |

### 4.5 Resulting user duties

None for ordinary users. A developer following an executed citation must not
conclude that the named run can be opened from a checkout.

### 4.6 Implementation worklist

Items A.7 (grade definition, DT-11/12), C.5 (DT-11.b), C.2 (DT-13), B.4 and B.5
(DT-14) of the consolidated worklist; verification D.1–D.3.

---

## Subject 5 — DT-15–21: reading routes, commitment placement, changed-file coverage, presence rules, field ownership, known-gap navigation, link labels

### 5.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-15.a | CONTRACT, REQUEST, RESPONSE, CONTROLLER and the user guide have no direct link to the failure evidence contract; it is reachable through ARCHITECTURE. | Reader starting from the developer statements. | **Yes.** Link counts: 0 in those five; ARCHITECTURE 5, WORKER 3, `tests/README.md` 3, `runner/README.md` 7, `tests/AGENTS.md` 1, `runner/AGENTS.md` 1. | Search. | Accurate observation needing no change. |
| DT-15.b | The failure contract's `operation_relation` row gives `different` "when it is another operation" and omits that a wildcard query other than the exact `process-exec*` match is `unresolved`. | Row at `tests/FAILURE-PROPAGATION-CONTRACT.md:1224`, hand-authored, outside the shared regions (`:270-303`, `:1399-1456`) and the generated matrix (`:1483-1531`). | **Yes.** Producer `runner/Sources/PWRunnerCore/CWorkerComparison.swift:137-145`. The same document contradicts the row twice: shared reading rule 9 (`:1436-1437`) and generated matrix row S12 (`:1497`, from `tests/fixtures/comparison/matrix.json:1247-1294`, `operation_relation: "unresolved"` for `file-read*`). The frozen guide states the rule correctly (`docs/PolicyWitness.md:2272`). | Review: signed-app specimen at `8b5de2b2` (not retained, not repeated). Now: source and fixture reading; `witness_contract/comparison_matrix` passed with 33 live rows in the present development run. | Inaccurate account (false row). |
| DT-15.c | RESPONSE states the case in two places that differ: the rule ("Other wildcard query spellings have an unresolved operation relation") and the field meaning ("`unresolved` means the mapping cannot assign a single operation"). | `docs/contract/31-steps.surface.md:753-754` and `:275`; rendered at `docs/RESPONSE.md:1202`, `:1024`. | **Yes.** For `file-read*` with `open_read` the mapping does assign `file-read-data`; the relation is unresolved because of the query. | Re-read. | Consequential ambiguity (the field meaning is incomplete). |
| DT-15.d | Limit: only this row of the failure contract was compared with source. | — | Still so; this pass compared no other row. | — | Accurate limit. |
| DT-16.a | BUILD's signing section lists `equipment.manifest` and `equipment.binding`, and its evidence section lists `identity.build`, `equipment.inventory` and `equipment.manifest`, under "Commitments explained here"; neither section discusses them. | `docs/contract/presentation.json:517-534`; `docs/BUILD.md:1033-1038`, `:1100-1106`. | **Yes.** | Re-read. | Inaccurate account (the lead-in is false for those entries). |
| DT-16.b | Supporting facts: `worker-equipment` does not occur in BUILD; "equipment" occurs in three generated table rows; "inventory" and "manifest" mean other things in those sections. | — | **Partly; the first fact is mistaken.** `worker-equipment.json` occurs once, in the generated `sign_services` step row (`docs/BUILD.md:170`), and did at `4816b0e4` too. "equipment" otherwise occurs at `:700` and `:1183` plus the two lists and one authored phrase at `:1097`. The section-prose point stands: no prose in either section mentions it. | Search at HEAD and at `4816b0e4`. | Review mistaken on one detail; the rest accurate. |
| DT-16.c | The first list attaches `identity.public.derive` to "Why the build is shaped this way", which does not mention the public build contract. | `presentation.json:509-516`; `docs/BUILD.md:17-92`. | **Yes.** The section describes the host/worker source identity; `build_contract`, `PW_BUILD_CONTRACT` and "public build contract" occur only at `:150`, `:168`, `:701`, `:1191-1192`. | Re-read. | Inaccurate account. |
| DT-16.d | Qualification: the README calls these associations "reviewed navigation, not test coverage"; this entry concerns BUILD only. | `docs/contract/README.md:100-104`. | **Yes.** | — | Accurate. |
| DT-17.a | Thirty product source files under the build-identity directories have no row in the changed-item index. | Representation: 930 index rows. | **Yes**, the same thirty; row counts by kind unchanged (433 / 180 / 162 / 143 / 10 / 2). | Recomputed. | Accurate observation. |
| DT-17.b | Some of those files hold behavior public statements describe; their records are reachable by type name through record rows that carry no path. | — | **Yes** as to the rows (`presentation.py:147-148` emits the bare record name). The per-file behavior descriptions were not re-read. | Partly re-read. | Accurate observation. |
| DT-17.c | The introduction says an absent association is an unknown; imported Rust records carry a `rust.` prefix and sort after every path row. | — | **Partly.** The introduction is as quoted. The sort order is by string: capitalized record names, `controller/`, `docs/`, lower-case identifiers, `runner/`, `rust.`, then `tests/`. `rust.` rows follow the product paths, not every path row. | Recomputed. | Accurate observation; one detail inexact. |
| DT-18.a | "as defined below" is an undefined presence phrase: 64 entries (50 REQUEST, 11 RESPONSE, 3 ARCHITECTURE); the notation does not define it; what it points to is the entry's own meaning on the same line. | Reader of field signatures. | **Yes.** `docs/contract/record_definitions.py:493-498`; `docs/CONTRACT.md:1634-1645` (`tree.py:1412-1423`). The phrase is part of the canonical public snapshot (`docs/contract/public.json` holds it 2,372 times) and is pinned by `tests/suites/source_drift/build_contracts.py:622-623` and `contract_tree_controls.py:244`. | Re-read plus counts. | Consequential ambiguity. |
| DT-18.b | 28 of those entries state no required, optional, omission or null rule (heuristic scan). | Request author; reader of the equipment inventory and reservation request. | **Yes in substance; the count depends on the keyword set.** A scan for required/optional/omit/omission/null/absent/absence/default finds 32, a superset of the review's named examples (list in 5.7). | Heuristic scan of rendered entries and of the loaded tree. | Contradicted explicit commitment (`docs/CONTRACT.md:1645`: "Exceptional omission and input requirements remain explicit"). |
| DT-18.c | The shared rule "Treat optional null as absent where decodeIfPresent is used" identifies fields by a Swift decoding call. | `docs/contract/10-request.surface.md:100`, rendered at `docs/REQUEST.md:421-424`. | **Yes.** | Re-read. | Consequential ambiguity. |
| DT-18.d | Limit: admission behavior for the 28 fields was not exercised. | — | Still so. This pass adds the generator's own import fact per field (5.7), which is decoder storage, not admission. | Source-derived. | Accurate limit. |
| DT-19.a | The user guide says the release's developer contract "defines the fields, applicability and obligations behind these surfaces"; the field entries and rules are now in REQUEST, RESPONSE and ARCHITECTURE; in the staged standalone guide this link is the only route. | `docs/PolicyWitness.md:3233-3236`; frozen. | **Yes.** `dist/PolicyWitness.md` has the same SHA-256 as the source guide (`1e886e4a…d64d`). | Re-read. | Accurate observation about frozen text. |
| DT-19.b | The link names `v0.3.8`; local tags end at `v0.3.7`; the link was not fetched. | — | **Yes** (`git tag --list 'v0.3.*'`); not fetched here either. `dist/publication.json` records `status: "withheld"`, `reason: "frozen_guide"`. | Reproduced; unverifiable as to GitHub. | Accurate observation. |
| DT-20.a | CONTRACT's Known gaps view lists the tree's two gap nodes; the tours state other gaps about public behavior. | `docs/CONTRACT.md:2800-2805`; `docs/ARCHITECTURE.md:154`, `docs/CONTROLLER.md:205`, `docs/WORKER.md:339`. | **Yes.** Gap nodes: `identity.surfaces.release_history`, `actor_evidence.gate.cancellation_evidence`. | Computed plus re-read. | Accurate observation. |
| DT-20.b | The view has no text saying it covers tree gap nodes only or that the tours hold more; whether the tour gaps belong in the tree is not assessed. | — | **Yes.** The view is a heading and a two-column table (`tree.py:1612-1614`). | Re-read. | Consequential ambiguity. |
| DT-21.a | "Termination dependency" labels both `actors.after_termination` and `actor_evidence.gate` in Find a commitment and in the changed-item index. | — | **Yes**, with a boundary: in Find a commitment the Identity column separates the two rows (`presentation.py:133`). | Computed. | Accurate observation. |
| DT-21.b | Six titles each label two rules in Rule applicability and Controller findings; rows are distinguishable only by link target. | `docs/CONTRACT.md:2762-2798`. | **Yes**: five in Rule applicability, and "Worker lifecycle validation" with "Local lifecycle findings" in Controller findings (`:2796-2797`). | Computed. | Accurate observation. |
| DT-21.c | In Evidence support, 36 headings end "— Support", 22 "— Disposition support", 17 "— Source support"; each is unique with its subject title. | — | **Yes** (152 headings, all unique). | Computed. | Accurate observation needing no change. |
| DT-21.d | The sentence introducing Controller findings says each row names the record members a check reads; five of nine rows say "See the linked rule." | `tree.py:1604-1605`; `docs/CONTRACT.md:2786`, rows `:2791`, `:2794`, `:2796-2798`. | **Yes.** | Re-read. | Inaccurate account (generated sentence). |

### 5.2 Comparison

- **DT-15.** The failure contract defers to RESPONSE for definitions and calls its
  table "the working summary for test authors" (`:1205-1207`). Producer: wildcard
  query other than the matched `process-exec*` → `unresolved`. Asserted by the
  matrix fixture row S12 through `witness_contract/comparison_matrix` (live) and
  `runComparisonEvidenceTests` (constructed). The hand-authored row and the
  RESPONSE field meaning are the two accounts that lag the rule.
- **DT-16.** `docs/contract/README.md:100-104`: "These associations say which
  commitments a section explains. They are reviewed navigation, not test
  coverage." `docs/contract/AGENTS.md`: "Author tour commitment associations by
  reading the section against each statement". Producer: `presentation.py:203`
  prefixes every list with "Commitments explained here:". What the build does:
  `build.sh:732-736` writes each service's inventory after the nested signatures
  and before that service's seal. BUILD states that only in the generated step
  row at `:170`.
- **DT-17, DT-21.a–c.** The index and views are navigation whose stated limit is
  `trace-introduction.md:22-25`. Nothing stated is false.
- **DT-18.** Stated: `docs/CONTRACT.md:1645`, "Exceptional omission and input
  requirements remain explicit"; `docs/contract/README.md` ("input and
  serialization exceptions remain explicit"). Producer: for an input record,
  every field without a `required_key` fact renders the phrase
  (`record_definitions.py:494-498`), and the display drops the import's
  optionality (`tree.py:1404-1409`). The importer says why
  (`record_definitions.py:317-318`): "This captures native optional storage, not
  admission or missing/null applicability; those remain tree obligations." So the
  design puts the presence rule in each field's authored meaning, and 28–32
  meanings do not carry one. No check reads meanings for a presence rule.
- **DT-19.** The technical owner of CONTRACT's reading guidance
  (`trace-introduction.md:3-7`, `:14-19`) already routes field statements to
  REQUEST, RESPONSE and ARCHITECTURE, and "Find a commitment" links every routing
  unit. The inexact sentence exists only in the frozen guide.
- **DT-20.** ARCHITECTURE, BUILD, WORKER and CONTROLLER each end with a
  mechanically checked index of their own gap paragraphs
  (`check_known_gap_index`, `tests/suites/source_drift/check.py:1090`). CONTRACT's
  view is derived from tree `gap` nodes. The two mechanisms do not refer to each
  other.

### 5.3 Plausible treatments

**DT-15.** (a) *Account*: correct the row at
`tests/FAILURE-PROPAGATION-CONTRACT.md:1224` (add the wildcard clause to
`unresolved`). Outside the shared regions, so the guide rule does not apply; no
generator. (b) *Account*: complete the field meaning at
`docs/contract/31-steps.surface.md:275`; public prose, `steps` already
`unreleased`. (c) For DT-15.a, adding links from RESPONSE to the failure contract:
an arrangement change with no false statement behind it.

**DT-16.** (a) *Account*: prune the three associations in
`docs/contract/presentation.json` (`equipment.binding` from `commitments_signing`;
`equipment.inventory` and `equipment.manifest` from `commitments_evidence`;
`identity.public.derive` from `commitments_identity`, where it remains under
`commitments_verification`), and add one sentence to the "Order." paragraph of
`docs/BUILD.md:989-994` stating that each service's `worker-equipment.json` is
written from the signed workers after that service's nested signatures and before
its seal, so `equipment.manifest` under signing is explained. (b) *Behavior
(generator)*: weaken the shared lead-in at `presentation.py:203` to "Related
commitments:" for all 21 lists and reword `README.md:100-104`. (c) *Retention* as
loose navigation: leaves the lead-in false.

**DT-17.** (a) *Retention.* (b) *Arrangement*: add the record's source path to
record rows.

**DT-18.** (a) *Account at the notation*: define the phrase in the `NOTATION`
text (`docs/contract/tree.py:1412-1423`): for an input record it means the
entry's meaning states whether the key is required, optional or may be null.
CONTRACT only; no snapshot change. (b) *Behavior (generator)*: rename the phrase
(`record_definitions.py:498`); changes the snapshot text in 2,372 places, 64
rendered entries and two tests. (c) *Account per field*: author the presence rule
in each meaning that lacks one (list in 5.7), after reading that field's decoder
and admission. (d) *Behavior (generator)*: display `required` for every
non-optional decode; contradicts the importer's stated boundary and changes every
input entry's signature. (e) *Account*: restate the null rule at
`10-request.surface.md:100` in terms of the entries.

**DT-19.** Retention only; the guide is frozen.

**DT-20.** (a) *Account*: one sentence in `docs/contract/trace-introduction.md`
saying that the Known gaps view lists the tree's gap nodes and that ARCHITECTURE,
CONTROLLER, WORKER and BUILD each end with an index of the gaps their own
sections state. (b) Putting the sentence in `tree.py` beside the view would
hard-code tour links into a renderer that fixtures also drive. (c) Moving tour
gaps into the tree: a public-payload change that belongs with the subject of each
gap.

**DT-21.** (a) *Account*: correct the generated sentence at `tree.py:1604-1605`.
(b) *Arrangement*: print the node identity beside a link whose title another
linked node shares. (c) *Retention* for the labels.

### 5.4 Recommended dispositions

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-15.a | Retention, no edit. | The developer statements own definitions and the failure contract defers to them; the working guidance that needs the second document links it. Nothing stated is false. |
| DT-15.b | Treatment (a). Row text for `unresolved`: "for compound `file`/`create` or `file`/`create_fresh`, an unsupported attempt, or a query operation containing `*` other than the exact `process-exec*` match". | The row is false for a case the same document's rule 9 and row S12 state correctly. Existing discriminating check: `witness_contract/comparison_matrix` (row S12) and the constructed matrix reader in `runner_unit/pwrunner_core_unit_executable`. |
| DT-15.c | Treatment (b). Field meaning: "`unresolved` means the action has no single mapped operation, or the query is a wildcard spelling other than the matched `process-exec*`." | Brings the field meaning into line with the rule ten lines below it and with the producer. Same existing checks. |
| DT-15.d | Recorded as open coverage: no other row of the failure contract has been compared with source by this pass. | Not a finding; a limit. |
| DT-16.a, .c | Treatment (a). | The smallest change that makes each BUILD list's lead-in true. If the pass that owns DT-41 finds the same defect across WORKER and CONTROLLER lists, treatment (b) is the shared alternative and should be decided once for all four tours. Verification: `source_drift/build_contracts` (regions regenerate) and `source_drift/generator_contract` (prose and link rules for the added sentence). |
| DT-16.b | Record the correction to the review: `worker-equipment.json` does occur in BUILD, at `:170`. | — |
| DT-16.d | Retained. | — |
| DT-17.a, .b, .c | Retention, no edit; accepted limit already at `trace-introduction.md:22-25`. | The index does not claim these files are irrelevant, and records in them are found by type name. A reviewer who changed one of these files knows which declaration changed. |
| DT-18.a | Treatment (a), landed together with DT-18.b. | Defining the phrase is true only once every such entry states its rule. Renaming (b) costs a snapshot-wide text change for no added information. |
| DT-18.b | Treatment (c). | The notation promises explicit input requirements; the design assigns them to the meanings; 28–32 meanings lack them. Control: a ratchet in `ContractTreeTests` (case `source_drift/build_contracts`) that counts input-record fields whose presence renders the phrase and whose meaning has none of the presence words, expected zero; it is a keyword heuristic and must be described as one. **Missing information per field:** the admission behavior. The import fact in 5.7 is a lead, not an observation. |
| DT-18.c | Treatment (e), after (c): name the fields by what their entries say, keeping the listed refusals. | Removes the dependence on reading the decoder. |
| DT-18.d | Retained as the evidence limit on the per-field rules until an admission pass exercises them. | — |
| DT-19.a | Retention under the guide freeze. Accepted limit, for the management plan's disposition and the maintainer-judgment outflow, not for permanent docs: "The frozen guide names CONTRACT as the place that defines the fields; CONTRACT's introduction and commitment index route each field statement to REQUEST, RESPONSE or ARCHITECTURE." | No technical owner is false. No erratum or substitute guidance is proposed. |
| DT-19.b | Retention; unresolved by nature. | The `v0.3.8` tag does not exist and no release occurs during this work; publication is recorded as withheld. Fetching the link would establish only today's state of a URL for an unreleased tag. |
| DT-20.a | No change to the tours. | Their gap statements are accurate and indexed. |
| DT-20.b | Treatment (a). Whether a tour gap should become a tree gap node is not decided here; the lost-reply gap at `docs/ARCHITECTURE.md:154` belongs with the transport thread (DT-31/32/42, DT-113–119). | A reader who takes CONTRACT's two-row view as the list of known gaps in public behavior misses the lost-reply and descendant-lifetime gaps. One sentence states the view's scope. |
| DT-21.a, .b, .c | Retention, no edit. Accepted limit (for the management plan; no document text needed): "Index rows carry node titles; where two nodes share a title the link target, and in Find a commitment the identity column, distinguishes them." | Every link resolves to its own anchor; renaming public titles or adding identities to four views is not justified by a false statement. |
| DT-21.d | Treatment (a). Proposed sentence: "A row names the record members its check's structured conditions read and links each structured consequence with what it reaches; where the rule states these in prose, the row refers to the linked rule." | The present sentence is false for five of nine rows. `contract_tree_controls.py:416-429` pins the row text "See the linked rule.", not the introduction. |

### 5.5 Resulting user duties

- DT-15: a user reading `operation_relation: "unresolved"` for a wildcard query
  must not conclude that the attempt has no mapped operation. The frozen guide
  already says this at `docs/PolicyWitness.md:2272`; no new duty arises.
- DT-18: none once the entries state their rules. Until then a request author
  must not infer from a missing presence rule that a key may be omitted.
  Standing: unsettled per field; the admission behavior has not been exercised.
- DT-16, DT-17, DT-19, DT-20, DT-21: none.

### 5.6 Implementation worklist

Items B.2 and C.4 (DT-15), B.3 and C.6 (DT-16), A.5, A.7 and C.7 (DT-18), B.5
(DT-20) and A.7 (DT-21.d) of the consolidated worklist; DT-17, DT-19 and the
DT-21 labels need no edit; verification D.1–D.3 and D.5.

### 5.7 The entries without a stated presence rule (lead for DT-18.b)

Scan at HEAD (`probe_dt18b.py`): input-record fields whose presence renders
"as defined below" and whose meaning has none of required / optional / omit /
omission / null / absent / absence / default. "Decode" is what the generator's
import recorded (`optional` false means a non-optional `decode` and non-optional
storage). It is not an admission observation.

| Surface file | Field identities | Import fact |
| --- | --- | --- |
| `11-policy.surface.md` | `policy.spec.format`, `policy.helper_policy.format` | non-optional `String` |
| `11-policy.surface.md` | `policy.helper_policy.sbpl_source` | `Option<String>`; meaning says "Require a string source at helper admission" |
| `12-probes.surface.md` | `probes.step.step_id`, `.sandbox_check`, `.attempt`; `probes.query.operation`; `probes.filter.kind`; `probes.attempt.kind`, `.action`, `.target` | non-optional |
| `13-actors.surface.md` | `actors.actor.actor_id`, `.sandbox`; `actors.phase.phase_id`, `.actions`; `actors.after_termination.actor_id` | non-optional |
| `14-extensions.surface.md` | `extensions.action.step_id`; `extensions.operation.operation` | non-optional |
| `20-transport.surface.md` | `transport.reservation.contract`, `.attempt_id`, `.lease_ms` | non-optional |
| `34-equipment.surface.md` | `equipment.manifest.schema_version`, `.contract`, `.worker_identity`, `.unsigned_worker_sha256`, `.workers`; `equipment.manifest_worker.role`, `.relative_path`, `.sha256`, `.cdhash`, `.identifier`, `.entitlements_xml` | non-optional |

The review's count of 28 excludes a few of these (for example
`equipment.manifest.contract`, whose meaning says "must match"). Thirty-two
other entries with the phrase do state a rule (for example
`request.specimen.run_kind`: "Omission and null have the same meaning").

---

## Unnumbered qualification sections in the range

| Id | Claim | Holds at HEAD? | Disposition |
| --- | --- | --- | --- |
| RC.a (lines 258–272) | The evidence review matched three final-run records (232 passes and one failure in the default run; credits 227 / 6 / 4) under three named `tests/out/runs/documentation-trace-*` directories. | **Unverifiable by reading.** Those three directories are absent; the eleven present runs are later development runs. | Retain as a historical observation; no present run is substituted for it and nothing is reused from it. |
| RC.b (lines 274–277) | A baseline comparison found no change in guide bytes, shape goldens, free-text counts, interface inventory/joins, porcelain schema or ABI layout golden. | Guide bytes re-verified against the frozen SHA-256 in `docs/publication.py:14`; the rest not re-derived. | No change. |
| RC.c (lines 277–279) | The review did not exhaust every native failure path or document arrangement. | Still so. | No change. |
| AF.a (lines 281–297) | The second investigation used tree `4816b0e4` and the `8b5de2b2` app (build 1482); each entry says whether it was reproduced, source-inspected or unresolved. | The app in `dist/` is now build 1519 at `2f4d76e4`; the scratch inputs are gone. | Treat signed-app reproductions in DT-11–21 (only DT-15.b here) as historical; the DT-15.b disposition rests on source, fixture and the existing matrix case instead. |

---

## Outside the review

Noticed while re-verifying; not added to the review.

1. **Second omitted identity input.** `docs/publication.py` joined `FILES` in
   `bba8bca3` and is absent from the inputs statement. Folded into DT-08.a's
   correction because it is the same statement and the same edit.
2. **Unavailable clock before any visit.** `ActorScheduler.swift:320-324` selects
   `execution_allowance_exhausted` on a nil remaining value at the start of a
   schedule entry, with no collection and no reap. DT-10.c describes the path as
   conditional on both. The DT-10 wording correction covers this site.
3. **`policy.helper_policy.sbpl_source`** is `Option<String>` in the import while
   its meaning says the helper requires a string. Whether omission, null and a
   wrong type are refused alike is not established here; it belongs with the
   per-field reading under DT-18.b.
4. **`checks` and extensions.** `14-extensions` declares only
   `failure_boundaries`, and that suite's README and checker contain nothing on
   extension actions. This is the clearest instance of DT-14.b; it does not
   change the recommended retention.

---

## Implementation worklist

Ordered so that generator and control changes land before the account edits that
regenerate through them. None of these files is a build-contract input; no signed
rebuild is forced. A build still checks generated copies, so regenerate before
the next build.

**A. Generator and controls**

1. `docs/contract/presentation.py`, `render` validation (near `:167-172`): refuse
   overlapping or nested declared regions in a document (DT-01).
2. Same function: refuse a `GENERATED CONTRACT <region>` marker in a `docs/*.md`
   document the map does not name; add the scanned documents to `input_paths` in
   `docs/generate_contract_stamps.py:78-83` (DT-02.a).
3. `docs/contract/presentation.py:147-148`: label authored records
   "authored record declaration" (DT-05).
4. `tests/suites/source_drift/generators.py`,
   `test_contract_map_refusals_validate_every_destination_before_writing`: add
   the nested-marker mutation and the moved-destination pair (refused with the old
   file's regions kept; accepted with them removed), each asserting an unchanged
   snapshot for `--check` and generation (DT-01, DT-02).
5. `tests/suites/source_drift/contract_tree_controls.py`: count node anchors
   across `docs/*.md` on disk at `:1335-1339` (DT-02.b); make `:1350-1392`
   positional with a moved-phrase rejecting control (DT-04); add the record-label
   assertion (DT-05); add the presence-word ratchet (DT-18.b, after C.7).
6. `tests/suites/source_drift/check.py` (`RULES`) and `check_planner.py`: rule
   comparing RESPONSE's opening fence with the second action of
   `EXAMPLE_DOCUMENT`, with a passing and a rejected planner control (DT-07).
7. `docs/contract/tree.py:84`: extend the executed grade definition (DT-11,
   DT-12). `:1604-1605`: correct the Controller findings sentence (DT-21.d).
   `:1419-1426`: define "as defined below" in the notation (DT-18.a, with C.7).
8. `tests/suites/source_drift/README.md`: describe each new control and rule
   beside the ones it joins, as `tests/AGENTS.md` requires for a changed suite.

**B. Hand-authored documents**

1. `docs/ARCHITECTURE.md:302`: delete `optional logs;` (DT-09).
2. `tests/FAILURE-PROPAGATION-CONTRACT.md:1224`: add the wildcard clause to the
   `operation_relation` row (DT-15.b). Do not touch the shared regions.
3. `docs/BUILD.md:989-994` ("Order."): one sentence on the service-local
   `worker-equipment.json`, written without a literal count and in the citation
   form the prose rules accept (DT-16).
4. `docs/contract/README.md`: after line 96, the two-sentence rebasing limit
   (DT-03); at `:80-81`, the corrected description of `checks` (DT-14).
   `tests/suites/source_drift/README.md:406-409`: the same correction (DT-14).
5. `docs/contract/trace-introduction.md:22-23`: "Source, check and interface
   associations are partial" (DT-14.e); one sentence on the scope of the Known
   gaps view and the tours' own indexes (DT-20.b).

**C. Generator inputs (surface tree and map)**

1. `docs/contract/00-identity.surface.md:63-73`: add `controller/interface` and
   `docs/publication.py` (DT-08.a).
2. `docs/contract/13-actors.surface.md:225`: reword the timeout clause (DT-10);
   `:232-239`: add the `wait_for_proceed` source citation and reword the limit;
   `:250`: reword the limit (DT-13).
3. `docs/contract/33-actor_evidence.surface.md:546`: add the reading of
   `execution_wait` to `cancelled` (DT-10).
4. `docs/contract/31-steps.surface.md:275`: complete the `operation_relation`
   meaning (DT-15.c).
5. The six owners at `docs/contract/21-wire.surface.md:126`, `:140`,
   `33-actor_evidence.surface.md:157`, `41-diagnostics.surface.md:761`, `:1154`,
   `:1168`: add the reviewed-inputs limit to `limits` (DT-11.b).
6. `docs/contract/presentation.json:509-534`: prune the three BUILD associations
   (DT-16).
7. The six surface files in 5.7: author each field's presence rule after
   reading its decoder and admission; then `10-request.surface.md:100` (DT-18.b,
   .c).

**D. Regeneration and verification**

1. `tests/lib/python.sh docs/generate_contract_stamps.py` (development mode; it
   reports "publication withheld" and leaves the guide untouched). No
   `--refresh-shapes`: none of these edits changes a shape. Review the diff of
   `docs/CONTRACT.md`, `docs/REQUEST.md`, `docs/RESPONSE.md`,
   `docs/ARCHITECTURE.md`, `docs/BUILD.md` and `docs/contract/public.json`.
2. Check every owner afterwards, as `docs/contract/README.md:117-119` requires:
   `tests/lib/python.sh docs/generate_limits.py --check`,
   `docs/generate_architecture.py --check`, `docs/generate_build.py --check`,
   `docs/generate_contract_stamps.py --check`.
3. Routed verification (management plan, "Verification sequence": Documentation →
   owning generation and `source_drift`): `tests/run.sh --suite source_drift` with
   a fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>`. The cases that carry the new
   controls are `source_drift/generator_contract` (A.4, prose and link rules),
   `source_drift/build_contracts` (A.5, map and presentation controls) and
   `source_drift/runner_source_manifests_agree` (A.6).
4. Only if the optional DT-10 unit control is added:
   `tests/run.sh --suite runner_unit --suite runner_c_worker_harness` against the
   signed app (`runner/AGENTS.md`). Only if the DT-10 behavior alternative were
   chosen instead of the account correction: a signed rebuild and
   `witness_contract/order_barrier_mutations`
   (`tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls`).
5. The existing behavior checks behind DT-15 need no new run for a documentation
   correction; they are `witness_contract/comparison_matrix` and
   `runner_unit/pwrunner_core_unit_executable`.

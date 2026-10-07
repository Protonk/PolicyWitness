# Generator hardening plan

This is the one document under `docs/` that describes intended behavior
rather than current behavior. It states the relationship between the four
documentation generators and the documents and sources they write, as a set
of numbered invariants; records where each generator stands against them
today, with the measurements that say so; and specifies the test case that
holds the invariants once the work lands. When every step in
[Sequence](#sequence) is done, the invariants move into
[the drift suite's README](../tests/suites/source_drift/README.md#invariants)
and the generators' docstrings, and this file is deleted, so that
[the documentation rule](../AGENTS.md#documentation) holds again.

The scope is the generators and the problems that live in them. Seams that
live in prose, such as counts a paragraph states, budgets named by
description rather than by limit id, or shortfalls stated without the
"Known gap" marker, are listed under
[What this plan leaves for later](#what-this-plan-leaves-for-later). The plan builds the mechanisms that later work needs for them: inline
spans, limit placeholders, a verified prose citation form, and a baseline
that keeps the two coverage invariants honest while conversions are pending.

## Terms

- **Manifest.** A reviewed file that owns facts: [contract.json](contract.json),
  [limits.json](limits.json), [architecture.json](architecture.json), the
  comparison matrix fixture, and, for the identity generator, the protocol
  source set itself. Nothing loads a manifest at run time.
- **Generator.** A script under `docs/` that reads one or more manifests and
  writes copies of their facts: [generate_contract.py](generate_contract.py),
  [generate_worker_identity.py](generate_worker_identity.py),
  [generate_limits.py](generate_limits.py) and
  [generate_architecture.py](generate_architecture.py). Each has a check mode
  that writes nothing.
- **Region.** Text between one BEGIN marker and one END marker, owned entirely
  by one generator. Handwritten text never sits inside a region.
- **Whole-file output.** A file a generator owns outright: the dot and SVG
  figures beside [ARCHITECTURE.md](ARCHITECTURE.md), and the staged guide copy.
- **Copy.** A rendering of a manifest fact inside a region or a whole-file
  output. The limits tables, the version sentence, the identity bytes and the
  figure tables are copies.
- **Citation.** A `path` and `symbol` pair in a manifest. The generator verifies
  that the file exists and that the symbol occurs in it. A citation is a place
  to look, not proof that a test asserts the row.
- **Span.** New in this plan. An inline region holding one scalar, written as
  `<!-- span <generator>.<name> -->value<!-- /span -->`, so that a sentence of
  prose can state a count or a value the generator owns without the paragraph
  becoming a region.
- **Limit placeholder.** New in this plan. The token `{limit:<id>}` inside an
  architecture fact, label or note, which the renderer replaces with the
  value and unit of that row in [limits.json](limits.json), so that the
  manifest carries no duration or size of its own.
- **Baseline.** New in this plan. A committed list of the exact prose sites
  that still state a value, a count or a citation in an unverified form. A
  rule refuses any site that is not listed and any listed site that no longer
  occurs, so the list and the documents agree and growth is one explicit line
  in one file. Whether the list may grow is decided outside the change, by
  the release preflight against the previous release and by review between
  releases; see C9.

## The invariants

Each invariant is numbered so that a test, a README paragraph or a later plan
can cite it.

- **G1. One owner, nothing outside.** Every region and whole-file output has
  exactly one generator. A generator changes no byte outside its regions and
  its declared whole-file outputs. A document holds each marker pair exactly
  once, in order, and a broken pair stops the generator before any write.
- **G2. Idempotence.** A second run of a generator immediately after a first
  writes nothing.
- **G3. Check mode in the build.** Every generator has `--check`, which writes
  nothing and exits nonzero on any stale copy, and the build runs every
  generator's check before compiling. A stale copy of any manifest fact stops
  a build before signing.
- **G4. Citations resolve.** Every citation names a repository-relative file
  that exists and a symbol that occurs in it. The generator refuses the
  manifest otherwise.
- **G5. Check citations have a form and a definition.** Every check citation
  in both manifests carries a `form`. A `test` form names a test that is
  defined in the cited file, in the file's language; a `rule` form names a
  drift rule function; a `control` form names a fixture, golden, helper or
  compiled C control that a test compares against. Every node, edge and limit
  cites at least one `test` or `rule`. A common word that merely occurs in a
  file cannot satisfy a `test` citation. The limits manifest's existing
  `kind`, which says what a check establishes about the value, is a different
  dimension and stays beside `form`.
- **G6. No self-citation.** A manifest does not cite itself, and does not cite
  any region or whole-file output of its own generator as a source, because the
  generator would then verify text it wrote. A generator's constants are the
  right citation for facts about the generator.
- **G7. Declared vocabulary.** A graph declares the fact keys its nodes and its
  edges may use, in column order. An undeclared key, or a declared key no item
  uses, is an error. The rendered table has exactly the declared columns.
- **G8. Durations and sizes are rendered from limits, never written.** A
  fact, label or note in the architecture manifest states a duration or a
  size only through a limit placeholder; a literal duration or size anywhere
  in the manifest is an error. The renderer substitutes the row's value and
  unit with the limits tables' own formatter, so the figure, its table and
  [LIMITS.md](LIMITS.md) cannot disagree, and the rendered row links the
  limit's section. A value with no limits row is either given a row, with a
  value owner as [LIMITS.md](LIMITS.md#grounding-and-coverage) requires, or
  removed from the fact.
- **G9. Counts and values reach prose through spans.** The mechanism: a span
  is owned by one generator, rendered from its manifest, checked for a stale
  value or an unknown name, and never inside a region. The coverage: every
  prose site that states a count of generated content or a limit value
  without a span is listed in the baseline, the rule refuses a site that is
  not listed, and G9 holds in full when the baseline holds no such site.
  Prose does not restate arithmetic over a spanned value.
- **G10. Captions state the verified guarantee.** The caption and summary a
  generator renders beside a figure or table say what the generator verified
  about the citations, which is the presence of each symbol in its file and,
  for a test, its definition there, and nothing stronger. A caption does not
  say that a test exercises, covers or proves a row: that relationship is the
  manifest author's assertion and the reader's to check, and no generator
  verifies it.
- **G11. Prose citations use the rendered form and are verified.** The
  mechanism: a drift rule scans every Markdown document the suite names and,
  for each link whose text is a backticked symbol and whose target is not a
  Markdown file, verifies the symbol in that file; it resolves every
  `#anchor` in a local Markdown link against the target's headings; any
  other local link is checked for file existence, as today. The coverage:
  every citation in prose that pairs a symbol with a file link in any other
  form is listed in the baseline, the rule refuses an unlisted one, and G11
  holds in full when the baseline holds no such citation.

## Where the generators stand

Measured on the manifests as committed for 0.2.7. The measurement functions
move into the test module in [The test case](#the-test-case), so these
numbers can be reproduced and the tests can assert their targets.

| Invariant | contract | identity | limits | architecture |
| --- | --- | --- | --- | --- |
| G1 one owner, nothing outside | holds; tested | holds; tested | holds; tested for the guide and the LIMITS prose | holds; not tested as a property |
| G2 idempotence | tested | tested | tested | tested |
| G3 check in the build | yes | regenerate, then check before signing | yes | **no**; the check runs only in the drift suite |
| G4 citations resolve | copies table tested | not applicable | yes | yes |
| G5 forms and definitions | not applicable | not applicable | partial: a value-owner set, and a `kind` on the value dimension; no `form`; 4 rows cite `main`; 15 checks match a symbol that occurs ten or more times | **missing**: no `form` field |
| G6 no self-citation | holds | holds; regions are excluded from the digest | holds | **2 self-citations** in the document graph |
| G7 declared vocabulary | fixed columns | not applicable | fixed columns | **missing**: fact keys are free text |
| G8 durations and sizes | not applicable | not applicable | it is the owner | **missing**: 7 numeric facts, 2 with no limits row |
| G9 spans | not applicable | not applicable | **missing**: 4 values restated in prose | **missing**: 1 count restated, and wrong |
| G10 captions | version sentence is exact | not applicable | coverage preamble is exact | **overstates** |
| G11 prose citations | — | — | file existence only; anchors only for the guide | file existence only; anchors only for the guide |

The architecture figures, in detail:

- 512 citations, of which 234 are checks. 11 checks are satisfied by a
  symbol that occurs ten or more times in the cited file, such as
  `entitlements` 31 times in the BYOXPC session fixture. 8 check symbols are
  plain English words: `install`, `cleanup`, `main`, `refused`, `admission`.
  22 checks point at fixtures, library helpers, goldens or the build script
  rather than a test. 2 sources are self-citations: the manifest node cites
  `schema_version` in the manifest, and the document node cites its own marker.
- The BYOXPC node table renders 27 fact columns for 19 nodes, almost every
  cell empty; the topology table renders 7 columns, every cell filled.
- Numeric facts: the host "exits 50 ms after replying"; verify "waits five
  seconds by default"; the throttle "one second", three times; teardown "one
  second"; and launchd's "ten seconds" default. The worker's "exit 4" is a
  code, not a duration, and stays with its source citation. The
  throttle, teardown and launchd default have rows in [limits.json](limits.json).
  The 50 ms exit delay and the five-second verify wait have none; each is
  pinned today only by a symbol in [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)
  and [runner_commands.rs](../controller/src/runner_commands.rs).
- The introduction says "the three figures", and the document graph's node
  for the document itself carries "these three figures" as a fact. The
  manifest has four graphs; the check prints that count. The count went stale
  when the fourth graph landed, and nothing noticed because the count is free
  text on both sides of the seam.
- The caption says each row cites "the check that exercises it". The
  generator verifies that a symbol occurs in a file.
- The prose has 50 local links, 20 of them with anchors into seven documents.
  All resolve today. The drift suite checks that the files exist; only the
  shipped guide has its anchors checked. The prose uses the rendered citation
  form nowhere; its citations are pairs of a symbol and a file link, as in
  "`load_manifest` ([generate_architecture.py](generate_architecture.py))",
  that no rule reads. The limits premises use the same unread form.

The limits generator, in detail:

- 222 citations, 144 checks, every check with a `kind` on the value
  dimension, 75 value, 50 boundary and 19 path, and none with a `form`.
  Every row has a value owner from a fixed set of seven test modules, which
  the drift suite enforces. 4 rows cite `main` as a boundary or path check,
  in two C sources and one Python checker; the form rule in G5 accepts
  `main` in a C control as a `control` and refuses it as a `test`.
- The prose outside the generated tables restates four values: a 63-byte step
  id fits and a 64-byte one does not; output rounds up to a whole 4 MiB; the
  reply maximum comes from a 256-step fixture; and the release margin
  inequality `60000 > 30000 + 1000 + 5000`. The generator's own control bumps
  a value and checks the tables; it cannot see these. The step-id example is
  inside the shared section that ships in the guide.

## Changes to the generators

Each change is small enough to land with its test. The architecture manifest's
`schema_version` goes from 1 to 2 with the first change that adds a field, and
the generator refuses version 1 from then on; there is one manifest, so the
bump and the edit are one commit.

### C1. The build runs the architecture check (G3)

Add `generate_architecture.py --check` to the documentation block at the top
of [build.sh](../build.sh), after the contract check. The check needs no
Graphviz: an SVG is verified by the stamp naming its dot text. Add the edge
`build → gen_architecture` to the document graph and drop the unqualified
"runs the generators' checks" from the `build` node's fact in favor of the
edges, which are precise.

### C2. Check citations gain a form, and tests must be defined (G5, G10)

Every `checks` reference in [architecture.json](architecture.json) and in
[limits.json](limits.json) gains `"form": "test" | "rule" | "control"`. The
word is `form`, not `kind`, because both manifests already use `kind` for
something else: the architecture manifest for a node's or edge's style, the
limits manifest for what a check establishes about a value. The generator
applies the rule by form:

| Form | Allowed files | Symbol must match |
| --- | --- | --- |
| `test` | `tests/suites/**`, `runner/Tests/**`, Rust sources with `#[test]` | Python `def {symbol}(`; Rust `fn {symbol}(` within three lines after `#[test]`; Swift `func {symbol}(` or a run label `"{symbol}:`; shell `test_selected {symbol}` or `PW_TEST_ID="{symbol}"`; or a case id in [catalog.json](../tests/catalog.json) whose suite owns the file |
| `rule` | `tests/suites/source_drift/*.py` | Python `def {symbol}(`, and `main()` must call it |
| `control` | `tests/fixtures/**`, `tests/lib/**`, `build.sh`, and C sources under `tests/` | occurs in the file; for Python and C, as a definition: `def {symbol}(`, or `{symbol}(` at the start of a line |

Every node, edge and limit must cite at least one `test` or `rule`. The
initial assignment is mechanical by path: suite, runner-test and Rust-test
files become `test`; drift-rule functions become `rule`; the rest become
`control`. In the architecture manifest the 8 plain-word symbols and the 22
non-test citations are then fixed by hand: a fixture helper such as
`install` in [session.py](../tests/fixtures/byoxpc/session.py) becomes a
`control`, and the row gains the suite case that drives it as its `test`.

In the limits manifest, `kind` is untouched: value, boundary and path keep
their meaning and their rendering, and the value-owner set in
[limits.py](../tests/suites/source_drift/limits.py) keeps its seven modules.
`form` is added beside `kind` on every check. Every value owner is a `test`
by construction, because the owner set holds only test modules, and the
loader asserts it rather than assuming it. The four `main` citations are C
programs under `tests/` and become `control`; each of those rows already
holds a `test`. The coverage table in
[LIMITS.md](LIMITS.md#grounding-and-coverage) renders the form beside the
kind. The limits loader refuses an unexpected field today, so its
`schema_version` goes to 2 with this change, as the architecture manifest's
does.

The caption and the details summary change to state what G4 and G5 verify
and nothing else: each row names the source symbol that implements it and
the test or rule the manifest names for it, and the generator verified that
each cited symbol is present in its file and each test is defined there.
Whether a test asserts the row is verified by nothing in this plan, and the
caption says so in one clause rather than implying the opposite. The
sentence "Every node and edge above cites at least one check" becomes "Every
node and edge above cites at least one test or rule".

### C3. No self-citation (G6)

The generator refuses a source citation whose path is the manifest or any file
the generator writes. The document graph's manifest node cites `MANIFEST_NAME`
in the generator; its document node cites `REGION_START` in the generator;
the figure files are cited through `expected_outputs`. The same rule, applied
to the limits manifest, already holds.

### C4. Declared fact vocabulary (G7)

Each graph gains `"node_facts": [...]` and `"edge_facts": [...]`, ordered.
The renderer takes its columns from the declaration instead of collecting
keys from the items. Topology, boundaries and documents declare the keys they
use today. The BYOXPC graph is re-keyed to at most eight node keys; the
manifest edit changes no citation and no figure, only which column a fact
sits in, and the rendered table becomes readable.

### C5. Limit placeholders (G8)

A fact, label or note may contain `{limit:<id>}`. The generator loads
[limits.json](limits.json) through the limits generator's own loader, so one
validation rule applies, verifies each id, and substitutes the row's value
and unit with the formatter the limits tables use, in the figure's dot text
as well as in the document tables. A literal that matches the
duration-or-size pattern, which is a number followed by `ms`,
`milliseconds`, `s`, `seconds`, `bytes`, `KiB` or `MiB`, or a number word
followed by `second` or `seconds`, is an error anywhere in the manifest: the
manifest never carries a value it could only restate. The rendered tables
gain a "Limits" column listing the ids each row draws on, each linked to its
section in [LIMITS.md](LIMITS.md). Exit codes and descriptor numbers do not
match the pattern; they stay pinned by their source citations.

Verifying a reference beside a literal would not do: a fact reading "7
seconds" could cite a one-second row and pass. Substitution removes the
number from the manifest, so the only way to state the value is to render
it, and a change to the row changes the fact, the table and the figure's
dot hash together. The shared formatter gains the singular for a value of
one, so a placeholder reads "1 second"; the one limits cell that reads "1
seconds" today changes with it, in the limits document and the guide copy.

Two numbers need a decision before C5 can land, because they have no row:

- The host's 50 ms exit delay. Either an execution-budget row, `host_exit_delay`,
  with its value owner in `runner_unit`, or the number leaves the fact and the
  timeline and the principles paragraph say "after a short reply-flush delay"
  with the symbol cited. The row is the better answer: the delay is the window
  in which a second connection meets the terminal claim, and the principles
  section already reasons about it.
- The verify command's five-second default. A row, `runner_verify_wait`, with
  the existing Rust assertion as its value owner. The flag that changes it is
  `--timeout-ms` on `runner verify`, so the Control cell can name it.

The architecture generator reads [limits.json](limits.json) and never writes
it or [LIMITS.md](LIMITS.md); the test holds that as a snapshot.

### C6. Spans (G9)

Both document generators learn one inline region form:

```text
<!-- span architecture.graphs -->4<!-- /span -->
<!-- span limits.step_id.value -->63<!-- /span -->
```

A generator renders the spans whose prefix it owns in every document it
registers for, and its check fails on a stale value or on a name with its
prefix that it does not expose. A span inside a generated region is an error.
The architecture generator exposes `graphs`, `nodes`, `edges`, `unpinned` and,
per graph, `<graph>.nodes` and `<graph>.edges`. The limits generator exposes
`<id>.value` and `<id>.value_unit`, formatted as the tables format them. The
guide's standalone validation accepts span comments, since the shared
section is copied verbatim.

Spans and limit placeholders share the one formatter, so a value reads the
same in a fact, a table and a sentence.

The first span replaces "three" in the introduction of
[ARCHITECTURE.md](ARCHITECTURE.md), and the document node's fact drops the
count. Prose that restates arithmetic over a value, such as the 64-byte
example beside the 63-byte limit, is reworded to use the value alone. The
counts and values that prose still states without a span after this step
are the baseline's first entries under C9.

### C7. The prose citation rule (G11)

The link checker in [limits.py](../tests/suites/source_drift/limits.py)
becomes a function the new module owns and both import. It scans the same
documents as today, plus every document the generators write, and:

- resolves `#anchor` fragments against the headings of the target document,
  using the same anchor rule the guide validation uses;
- for a link whose text is a backticked symbol and whose target is not a
  Markdown file, requires the symbol in the file;
- for every other local link, requires the file, as today.

The rule verifies the rendered form. A citation in any other form, such as
the pair "`load_manifest` ([generate_architecture.py](generate_architecture.py))"
that the timeline bullets and the limits premises use today, is an entry in
the baseline under C9: the rule does not verify it, but it knows the site
exists, and converting the pair to [`load_manifest`](generate_architecture.py)
removes the entry and puts the citation under the rule. The conversions are
prose work and are listed under
[What this plan leaves for later](#what-this-plan-leaves-for-later).

### C8. The outside-regions property (G1)

A uniform control for all four generators: regenerate from a changed
manifest and assert that every target document and source is byte-identical
outside the generator's regions. The contract and limits tests hold this for
some targets already; the uniform test holds it for all of them, including
the architecture document and the three identity targets.

### C9. The prose baseline (G9, G11)

A committed file, `tests/fixtures/docs/prose_baseline.json`, lists by
document and exact text every prose site that the two coverage rules can
find and that is not yet in a verified form:

- a duration or size literal outside every region and span, matched by the
  pattern of C5 extended with the hyphenated forms prose uses, such as
  "63-byte" and "256-step";
- a citation pair, a backticked symbol followed in the same sentence by a
  link to a non-Markdown file, outside every region;
- a count statement about generated content, which no pattern can find:
  these entries are written by hand from the survey, and the rule verifies
  only that each still occurs, so a new count statement is a review matter.

The baseline has three properties, and each has a different guarantor.

- **Consistency.** The sites the patterns find equal the sites the file
  lists. An unlisted site fails, and so does a listed site that no longer
  occurs. The drift test holds this, mechanically.
- **Explicit growth.** Because an unlisted site fails, a new restatement or
  citation can enter a scanned document only together with a new line in
  this one file. Growth is never a side effect of a prose edit; it is a line
  in a diff to a file whose only purpose is to be short. The drift test
  holds this too.
- **No growth.** No check inside a change can establish that the file did
  not grow, because any reference it compares against, a ceiling, a count or
  a copy of the file, can be edited in the same change. Non-growth needs a
  reference the change cannot edit. Between releases that reference is the
  reviewer: a diff that adds a baseline line is a diff that adds unverified
  prose, and is read as such. At a release it is mechanical:
  [release_preflight.py](../tests/lib/release_preflight.py) already requires
  HEAD to sit at an annotated release tag, and it gains a check that reads
  the baseline at the previous release tag and refuses a release whose
  baseline is not a subset of it. When the previous tag predates the
  baseline there is nothing to compare, and the preflight reports that
  rather than refusing. A release can therefore convert sites and never add
  them, and the drift suite keeps every addition explicit until the
  preflight sees it.

This is where the plan's boundary runs. The generators and the drift suite
can make the state of the prose knowable and every change to it explicit;
they cannot decide what prose may say, and this plan does not try to. Adding
a baseline line is a judgment a reviewer makes, and the preflight rule is
the one place that judgment is checked against something the change cannot
edit.

The baseline is what lets G9 and G11 be stated honestly at every point in
the sequence: each holds as a mechanism from the step that lands it, and
holds in full on the day its part of the baseline is empty. The baseline
outlives this plan. The drift suite keeps the consistency rule, the
preflight keeps the subset rule, and the suite README states which
invariants hold in full and which still carry entries.

## The test case

A new case, `generator_contract`, in the `source_drift` suite, with its
module at `tests/suites/source_drift/generators.py`. It joins the existing
per-generator modules rather than replacing them: those keep their
stale-copy, broken-marker, build-refusal and manifest-shape controls, and
their mutation tables grow with the new fields. Registration follows the
drift rules: a block in [run.sh](../tests/suites/source_drift/run.sh), an
entry in [catalog.json](../tests/catalog.json), the sentence in the suite's
row of [tests/README.md](../tests/README.md), and an invariants paragraph in
the [suite README](../tests/suites/source_drift/README.md#invariants). The
module imports each generator by path, as the existing modules do, and runs
commands in a disposable checkout so that no control can write to the tree.

| Test | Holds | Asserts | Controls that must be refused |
| --- | --- | --- | --- |
| `test_build_checks_every_generator_before_signing` | G3 | [build.sh](../build.sh) invokes `--check` for each of the four generators before the codesign block; the identity generator's regenerate-then-check pair counts | a checkout whose build script lacks one check line fails the test, not the build |
| `test_regeneration_changes_nothing_outside_regions` | G1 | for each generator: change the manifest, regenerate, and the text outside every region and whole-file output is unchanged in every target | a generator patched to append one byte after its END marker |
| `test_check_citations_carry_a_form_and_tests_are_defined` | G5, G4 | every check in both manifests has a form; every `test` symbol matches a definition pattern for its file; every node, edge and limit has a `test` or `rule`; every limit's value owner has form `test`; every limits `kind` is unchanged; the measurement functions report zero plain-word `test` symbols and zero `test` citations into fixtures | a check without a form; `install` with form `test`; an item with only `control` checks; a `rule` whose function `main()` does not call; a limits value owner with form `control`; a limits check whose `kind` is missing |
| `test_manifests_do_not_cite_themselves_or_their_outputs` | G6 | no source citation in either manifest names the manifest or a file its generator writes | the document node citing its own marker |
| `test_fact_keys_are_declared_and_columns_follow_the_declaration` | G7 | every fact key is declared; every declared key is used; the rendered table header equals the declaration; the BYOXPC graph declares at most eight node keys | an undeclared key; an unused declared key; a renderer that collects keys from items |
| `test_durations_and_sizes_render_from_limits` | G8 | no fact, label or note in the architecture manifest matches the duration-or-size pattern; every placeholder names an id in [limits.json](limits.json); the rendered text at each placeholder equals the limits table's value cell for that id; bumping a value in a checkout's limits manifest changes the fact, the table and the dot stamp together; the architecture generator leaves [limits.json](limits.json) and [LIMITS.md](LIMITS.md) byte-identical | a literal "7 seconds" in a fact; a placeholder naming an id that does not exist; a renderer that leaves placeholder text in the dot output |
| `test_spans_render_check_and_stay_out_of_regions` | G9, G2 | every span in every registered document is current; `--check` reports a stale span and an unknown name by name; regeneration repairs a stale span and a second run writes nothing | a span with a stale value; a span naming `architecture.no_such_count`; a span placed inside a generated region |
| `test_captions_state_the_verified_guarantee` | G10 | the rendered caption and summary name presence and definition as the verified facts and say that assertion of the row is not verified; neither contains "exercises", "covers" or "proves" | a renderer whose caption omits the unverified clause; a caption containing any of the three words |
| `test_prose_links_resolve_anchors_and_symbol_links` | G11 | the shared link checker reports nothing for the scanned documents, with every anchor resolved and every symbol-form link verified | a link to a heading that does not exist; a symbol-form link whose symbol is absent; a reference-style link |
| `test_prose_baseline_is_consistent_and_growth_is_explicit` | G9, G11 | every site the two patterns find in the scanned documents is listed in the baseline; every listed site still occurs; a new site fails until a line is added to the baseline and to nothing else; the entries are reported per invariant so the README can state which parts are empty | a new "7 seconds" sentence with no baseline line; a new symbol-and-link pair with no baseline line; a baseline entry whose text no longer occurs |
| `test_release_preflight_refuses_a_grown_baseline` | G9, G11 | in a disposable git repository with two annotated release tags, the preflight accepts a candidate whose baseline equals or is a subset of the previous tag's, refuses a superset, and reports rather than refuses when the previous tag has no baseline; `--report` turns the refusal into a warning as it does for every other finding | a candidate with one added baseline line; a candidate with a rewritten entry that matches no previous entry |
| `test_measurements_match_this_plan` | all | the measurement functions, run on the committed manifests, produce the citation, column and numeric-fact counts the tests above assert as targets; this test is the one that is edited as the numbers move, and it is deleted with this plan | — |

Every test that runs a generator does so in a checkout and asserts afterward
that the checkout is byte-identical when the generator refused, matching the
existing refusal controls.

## Sequence

Each step lands with its tests green under
`tests/run.sh --suite source_drift`, the architecture figures regenerated,
and the SVGs re-rendered where the dot text changed.

1. C1 and `test_build_checks_every_generator_before_signing`. One line in the
   build script, one edge in the manifest.
2. C8 and `test_regeneration_changes_nothing_outside_regions`. No generator
   changes; the test documents the property before the generators change.
3. C2 and C3 for the architecture manifest, with their two tests and the
   mutation table in
   [architecture.py](../tests/suites/source_drift/architecture.py). The
   manifest rewrite is mechanical first, then by hand for the 30 citations the
   rule refuses. Schema version 2. The architecture manifest goes first
   because its citations are the weaker ones, so the definition patterns are
   settled against the harder cases.
4. C2 for the limits manifest: `form` beside `kind`, schema version 2, the
   mutation table in [limits.py](../tests/suites/source_drift/limits.py), the
   four `main` citations as controls, the loader's assertion that every value
   owner is a `test`, and the coverage table's new column.
5. C4 and its test. The BYOXPC re-keying is reviewed as a figure change.
6. C5 and its test, after the two row decisions. The limits manifest gains at
   most two rows, each with a value owner and a coverage note, under
   [the maintenance rules](LIMITS.md#maintaining-this-document).
7. C6 and its test, with the first span in the architecture introduction and
   the rewording of the limits prose that does arithmetic on a value.
8. C7 and C9 with their tests, including the preflight subset rule. The
   baseline's first entries are the sites the survey found. From here a
   conversion is a baseline removal, and the test shows it.
9. `test_measurements_match_this_plan`, then the README paragraphs, then this
   document is deleted and the router line in [AGENTS.md](../AGENTS.md)
   points at the drift suite README. An empty baseline is not a condition of
   deletion; the README states which invariants hold in full.

## What this plan leaves for later

These are seams between prose and generation. Each depends on a mechanism
above, named in brackets, and each conversion removes an entry from the
baseline of C9, so progress is visible in the drift suite rather than here.

- Counts the prose states beyond the figure count: three native-API
  processes, seven evidence channels, four records with local versions, six
  core ideas, four manifests and four generators, six source-drift rules. The
  manifest can derive the first three; the others need a rule or a span over
  a list. [C6, C9]
- The budgets paragraph in [ARCHITECTURE.md](ARCHITECTURE.md), which names
  nine budgets by description and no limit id; and the three phrasings of
  "iteration counts, not wall-clock" across the two documents. [C5, C7, C9]
- The timeline bullets and the limits premises, whose citations are
  hand-verified pairs of symbol and file link, and the positional pointers
  into numbered source comments. [C7, C9]
- The "Known gap" convention: a rule that every paragraph opening with the
  marker is listed in the [index](ARCHITECTURE.md#known-gaps) and the index
  lists nothing else, and a decision about the shortfalls the prose states
  without the marker. [a rule]
- The evidence-channels table, whose landing paths the shape goldens could
  verify. [a rule]
- The document graph's drift node, which draws four rule edges where the
  drift script runs thirteen rules. [C2's `rule` form gives the check a
  vocabulary to compare against]

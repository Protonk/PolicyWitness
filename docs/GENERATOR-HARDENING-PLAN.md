# Generator hardening plan

This is the one document under `docs/` that describes intended behavior
rather than current behavior. It states the relationship between the four
documentation generators and the files they write as numbered invariants,
records where each generator stands against them, and specifies the changes
and drift tests needed to satisfy them. Follow [Sequence](#sequence) in
order, using the invariants as acceptance criteria. Change numbers identify
the work each step requires. After completing the sequence, move the invariants into
[the drift suite's README](../tests/suites/source_drift/README.md#invariants)
and the generators' docstrings, then delete this file in accordance with
[the documentation rule](../AGENTS.md#documentation).

The scope is the generators and their verification mechanisms. Prose work
that depends on those mechanisms is listed under
[What this plan leaves for later](#what-this-plan-leaves-for-later).

## Terms

- **Manifest.** A reviewed file that owns facts: [contract.json](contract.json),
  [limits.json](limits.json), [architecture.json](architecture.json), the
  comparison matrix fixture, and, for the identity generator, the protocol
  source set itself. Nothing loads a manifest at run time.
- **Generator.** A script under `docs/` that reads manifests and writes copies
  of their facts, with a `--check` mode that writes nothing:
  [generate_contract.py](generate_contract.py),
  [generate_worker_identity.py](generate_worker_identity.py),
  [generate_limits.py](generate_limits.py) and
  [generate_architecture.py](generate_architecture.py).
- **Region.** Text between one BEGIN and one END marker, owned entirely by one
  generator. A *rendered* region is produced from a manifest; a *copy* region
  reproduces another document's shared text verbatim, as the guide's copied
  limits, questions and reading rules do. Handwritten text never sits inside
  a region.
- **Whole-file output.** A file a generator owns outright: the dot and SVG
  figures beside [ARCHITECTURE.md](ARCHITECTURE.md), and the staged guide.
- **Citation.** A `path` and `symbol` pair in a manifest. The generator
  verifies that the file exists and that the symbol occurs in it. A citation
  is a place to look, not proof that a test asserts the row.
- **Form.** On a check citation, one of `test`, `rule` or `control`: what
  sort of thing the symbol is. The limits manifest's `kind`, one of
  `value`, `boundary` or `path`, says what the check establishes about the
  value and is a different dimension.
- **Limit placeholder.** The token `{limit:<id>}` in an architecture
  fact, label or note, which the renderer replaces with that row's value and
  unit from [limits.json](limits.json).
- **Span.** An inline region holding one scalar,
  `<!-- span <generator>.<name> -->value<!-- /span -->`, authored once,
  outside every region of its document, so a sentence can state a count or a
  value the generator owns.
- **Baseline.** A committed list of the exact prose sites that still
  state a value, a count or a citation in an unverified form. The drift suite
  holds it consistent with the documents; review governs additions between
  releases, and release preflight enforces non-growth against the previous
  release (see C9).

## The invariants

- **G1. One owner, nothing outside.** Every region and whole-file output has
  exactly one generator, which changes no byte outside them. A document holds
  each marker pair once, in order; a broken pair stops the generator before
  any write.
- **G2. Idempotence.** A second run immediately after a first writes nothing.
- **G3. Check mode before signing.** Every generator has `--check`, which
  writes nothing and exits nonzero on any stale copy, and the build runs
  every generator's check before signing.
- **G4. Citations resolve.** Every citation names a repository-relative file
  that exists and a symbol that occurs in it.
- **G5. Check citations have a form and a definition.** Every check citation
  in both manifests carries a form. A `test` is defined in the cited file, in
  that file's language; a `rule` is a drift-rule function; a `control` is a
  fixture, golden, helper or compiled C control a test compares against.
  Every node, edge and limit cites at least one `test` or `rule`. A common
  word that merely occurs in a file cannot satisfy a `test`.
- **G6. No self-citation.** A manifest cites neither itself nor any region or
  whole-file output of its own generator, since the generator would then
  verify text it wrote.
- **G7. Declared vocabulary.** A graph declares the fact keys its nodes and
  edges may use, in column order; an undeclared or unused key is an error.
- **G8. Durations and sizes render from limits.** The architecture manifest
  states a duration or size only through a limit placeholder; a literal one
  anywhere in the manifest is an error.
- **G9. Counts and values reach prose through spans.** A span is owned by one
  generator, rendered from its manifest, checked for a stale value or an
  unknown name, and authored outside every region; a copy region carries it
  as bytes. Prose does not restate arithmetic over a spanned value.
- **G10. Captions state the verified guarantee.** A generated caption or
  summary says what the generator verified about citations, presence and
  definition, and nothing stronger; it never says a test exercises, covers or
  proves a row.
- **G11. Prose citations use the rendered form and are verified.** A drift
  rule verifies, in every Markdown document it scans, the symbol behind each
  link whose text is a backticked symbol and whose target is not Markdown,
  and resolves every `#anchor` against the target's headings.

For G9 and G11, distinguish implementation of the mechanism from its prose
coverage. The baseline records sites outside each mechanism; coverage is
complete when the baseline's entries for that invariant are empty.

## Where the generators stand

Measured on the manifests committed for 0.2.7, by the functions that become
the measurement module of the new test case.

| Invariant | contract | identity | limits | architecture |
| --- | --- | --- | --- | --- |
| G1 | holds; tested | holds; tested | holds; tested for the guide and the LIMITS prose | holds; not tested as a property |
| G2 | tested | tested | tested | tested |
| G3 | yes | regenerate before compiling, check before signing | yes | **no**: the check runs only in the drift suite |
| G4 | copies table tested | not applicable | yes | yes |
| G5 | not applicable | not applicable | partial: a seven-module value-owner set; `kind` only; 4 rows cite `main`; 15 checks match a symbol occurring ten or more times | **missing**: no form |
| G6 | holds | holds; regions are excluded from the digest | holds | **2 self-citations** in the document graph |
| G7 | fixed columns | not applicable | fixed columns | **missing**: keys are free text |
| G8 | not applicable | not applicable | it is the owner | **missing**: 7 duration facts, 2 with no row |
| G9 | not applicable | not applicable | **missing**: 4 values restated in prose | **missing**: 1 count restated, and wrong |
| G10 | exact | not applicable | exact | **overstates** |
| G11 | not applicable | not applicable | file existence only | file existence only; anchors checked for the guide alone |

The specifics behind the bold cells:

- Architecture citations: 512, of which 234 are checks. 11 checks match a
  symbol occurring ten or more times in its file, such as `entitlements` 31
  times in the BYOXPC session fixture; 8 check symbols are plain words:
  `install`, `cleanup`, `main`, `refused`, `admission`; 22 checks point at
  fixtures, library helpers, goldens or the build script. The two
  self-citations are the document graph's manifest node citing
  `schema_version` in the manifest and its document node citing its own
  marker.
- The BYOXPC node table renders 27 fact columns for 19 nodes, almost every
  cell empty; the topology table renders 7, every cell filled.
- Duration facts: the host "exits 50 ms after replying"; verify "waits five
  seconds by default"; the throttle "one second", three times; teardown "one
  second"; launchd's "ten seconds" default. The last three have rows. The
  first two are pinned only by symbols in
  [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)
  and [runner_commands.rs](../controller/src/runner_commands.rs). The
  worker's "exit 4" is a code, not a duration.
- The introduction of [ARCHITECTURE.md](ARCHITECTURE.md) says "the three
  figures" and the document graph's node for the document carries the same
  count as a fact; the manifest has four graphs.
- The figure caption says each row cites "the check that exercises it"; the
  generator verifies that a symbol occurs in a file.
- The architecture prose has 50 local links, 20 with anchors into seven
  documents, all resolving today and none checked beyond file existence. It
  cites symbols as pairs of a backticked symbol and a file link, as in
  "`load_manifest` ([generate_architecture.py](generate_architecture.py))",
  which no rule reads; the limits premises use the same form.
- Limits citations: 222, of which 144 are checks, 75 value, 50 boundary and
  19 path. The four `main` citations are in two C sources and one Python
  checker. The prose outside the tables restates four values: the 63-byte
  step id beside a 64-byte one, the 4 MiB rounding, the 256-step fixture and
  the inequality `60000 > 30000 + 1000 + 5000`; the generator's own control
  bumps a value and checks the tables, and cannot see these. The step-id
  example ships in the guide.

## Changes

Each change names its invariants, the files it touches and the test that
lands with it; the tests are specified in [The test case](#the-test-case).
Each manifest's `schema_version` goes from 1 to 2 with the first change that
adds a field to it, and its loader refuses version 1 from then on.

### C1. The build runs the architecture check (G3)

Files: [build.sh](../build.sh), [architecture.json](architecture.json).
Test: `test_build_checks_every_generator_before_signing`.

Add `generate_architecture.py --check` to the documentation block at the top
of the build script, after the contract check; it needs no Graphviz, since an
SVG is verified by the stamp naming its dot text. Add the edge
`build → gen_architecture` to the document graph and drop the unqualified
"runs the generators' checks" from the `build` node's fact; the edges are
the precise statement.

### C2. Check citations gain a form, and tests must be defined (G5, G10)

Files: [architecture.json](architecture.json), [limits.json](limits.json),
both document generators, [limits.py](../tests/suites/source_drift/limits.py),
the coverage table of [LIMITS.md](LIMITS.md#grounding-and-coverage).
Tests: `test_check_citations_carry_a_form_and_tests_are_defined`,
`test_captions_state_the_verified_guarantee`.

Add `"form"` to every `checks` reference. Preserve `kind` for node and edge
styles in the architecture manifest and for the value dimension in the
limits manifest. The loaders apply the following rules by form:

| Form | Allowed files | Symbol must match |
| --- | --- | --- |
| `test` | `tests/suites/**`, `runner/Tests/**`, Rust sources with `#[test]` | Python `def {symbol}(`; Rust `fn {symbol}(` within three lines after `#[test]`; Swift `func {symbol}(` or a run label `"{symbol}:`; shell `test_selected {symbol}` or `PW_TEST_ID="{symbol}"`; or a case id in [catalog.json](../tests/catalog.json) whose suite owns the file |
| `rule` | `tests/suites/source_drift/*.py` | Python `def {symbol}(`, and `main()` must call it |
| `control` | `tests/fixtures/**`, `tests/lib/**`, `build.sh`, C sources under `tests/` | occurs in the file; for Python and C, as a definition: `def {symbol}(`, or `{symbol}(` at the start of a line |

Every node, edge and limit must cite at least one `test` or `rule`. The
initial assignment is mechanical by path, and whatever the rule then
refuses is fixed by hand: a plain-word symbol under `test` is replaced by the
test that drives it, and an item left with only controls gains one. A fixture
helper such as `install` in [session.py](../tests/fixtures/byoxpc/session.py)
stays as a `control` beside the suite case added as its `test`.

In the limits manifest the value-owner set keeps its seven modules; every
value owner is a `test` because the set holds only test modules, and the
loader asserts it. The four `main` citations are C programs under `tests/`
and become controls; each of those rows already holds a `test`. The coverage
table renders the form beside the kind.

The caption and the details summary of each figure state what G4 and G5
verify and nothing else: each row names the source symbol that implements
it and the test or rule the manifest names for it; the generator verified
that each symbol is present and each test is defined; whether a test asserts
the row is not verified. The closing sentence becomes "Every node and edge
above cites at least one test or rule".

### C3. No self-citation (G6)

Files: [generate_architecture.py](generate_architecture.py),
[architecture.json](architecture.json).
Test: `test_manifests_do_not_cite_themselves_or_their_outputs`.

The generator refuses a source citation whose path is the manifest or any
file the generator writes. The document graph's manifest node cites
`MANIFEST_NAME` in the generator, its document node `REGION_START`, and the
figure files `expected_outputs`. The limits manifest already satisfies the
rule.

### C4. Declared fact vocabulary (G7)

Files: [generate_architecture.py](generate_architecture.py),
[architecture.json](architecture.json).
Test: `test_fact_keys_are_declared_and_columns_follow_the_declaration`.

Each graph gains ordered `"node_facts"` and `"edge_facts"` lists, and the
renderer takes its columns from them. Topology, boundaries and documents
declare the keys they use today. The BYOXPC graph is re-keyed to at most
eight node keys; the edit changes no citation and no figure, only which
column a fact sits in.

### C5. Limit placeholders (G8)

Files: [generate_architecture.py](generate_architecture.py),
[architecture.json](architecture.json), [limits.json](limits.json),
[generate_limits.py](generate_limits.py).
Test: `test_durations_and_sizes_render_from_limits`.

A fact, label or note may contain `{limit:<id>}`. The architecture generator
loads [limits.json](limits.json) through the limits generator's own loader,
verifies each id, and substitutes the row's value and unit with the limits
tables' formatter, in the dot text as well as the document tables, so a row
change moves the fact, the table and the figure's dot hash together. A
literal matching the duration-or-size pattern, a number followed by `ms`,
`milliseconds`, `s`, `seconds`, `bytes`, `KiB` or `MiB`, or a number word
followed by `second` or `seconds`, is an error anywhere in the manifest.
Exit codes and descriptor numbers do not match the pattern and stay with
their source citations. The rendered tables gain a "Limits" column linking
each id to its section of [LIMITS.md](LIMITS.md). The architecture generator
never writes the limits manifest or document.

The shared formatter uses the singular for a value of one, so a placeholder
reads "1 second". Apply this formatting to the limits table and its guide
copy as well.

Add rows for two durations, each with a value owner and a coverage note under
[the maintenance rules](LIMITS.md#maintaining-this-document):

- `host_exit_delay`: the 50 ms reply-flush delay, owned in `runner_unit`. This
  is the window in which a second connection meets the terminal claim.
- `runner_verify_wait`: the verify command's default, owned by the existing
  Rust assertion, with `--timeout-ms` on `runner verify` as its control.

### C6. Spans (G9)

Files: both document generators, the introduction of
[ARCHITECTURE.md](ARCHITECTURE.md), the prose of [LIMITS.md](LIMITS.md).
Test: `test_spans_are_authored_outside_regions_and_copied_as_bytes`.

```text
<!-- span architecture.graphs -->4<!-- /span -->
<!-- span limits.step_id.value -->63<!-- /span -->
```

Each generator declares the documents it scans for its prefix and renders
the spans there; its check fails on a stale value or an unknown name with its
prefix. The architecture generator exposes
`graphs`, `nodes`, `edges`, `unpinned` and, per graph, `<graph>.nodes` and
`<graph>.edges`; the limits generator exposes `<id>.value` and
`<id>.value_unit`. Spans and placeholders share the one formatter. A prefix
no generator owns is caught by the uniform test, which knows every prefix.

The span pass reads and writes only text outside regions. The limits
generator renders spans in [LIMITS.md](LIMITS.md) before copying the shared
section into the guide. Span markers and values inside a copy region are
copied bytes; a difference from the source fails the copy-equality check.
Renderers emit no span markers, so inserting one into a rendered region makes
the region stale. The guide is registered with neither generator for span
processing and receives spans only by copy. Its standalone validation accepts
span comments as inert HTML comments.

Replace "three" in the architecture introduction with the
`architecture.graphs` span and remove the count from the document node's
fact. Reword the 64-byte example beside the 63-byte limit to use the value
alone. Every count or value that prose still states without a span after
this step is a baseline entry.

### C7. The prose citation rule (G11)

Files: [limits.py](../tests/suites/source_drift/limits.py), the new test
module. Test: `test_prose_links_resolve_anchors_and_symbol_links`.

Move the link checker into a function the new module owns and both import.
Retain its scan set and add every document the generators write. It resolves
`#anchor` fragments against the target's headings with the rule the guide
validation uses, requires the symbol in the file for a link whose text is a
backticked symbol and whose target is not Markdown, and requires the file for
every other local link. A citation in any other form, such as the pair
"`load_manifest` ([generate_architecture.py](generate_architecture.py))", is
a baseline entry until it is converted to
[`load_manifest`](generate_architecture.py).

### C8. The outside-regions property (G1)

Files: the new test module only.
Test: `test_regeneration_changes_nothing_outside_regions`.

For each generator: change its manifest, regenerate, and assert every target
is byte-identical outside the generator's regions and whole-file outputs.
Include all targets, including the architecture document and the three
identity targets.

### C9. The prose baseline (G9, G11)

Files: `tests/fixtures/docs/prose_baseline.json`, the new test module,
[release_preflight.py](../tests/lib/release_preflight.py).
Tests: `test_prose_baseline_is_consistent_and_growth_is_explicit`,
`test_release_preflight_refuses_a_grown_baseline`.

The baseline lists, by document and exact text, every prose site that is not
yet in a verified form: a duration or size literal outside every region and
span, matched by the C5 pattern plus the hyphenated forms prose uses, such as
"63-byte" and "256-step"; a citation pair, a backticked symbol followed in the
same sentence by a link to a non-Markdown file; and a count statement about
generated content, which no pattern can find, so those entries are written by
hand from the survey and only their continued presence is checked.

The baseline's checks and review requirements are:

- **Consistency.** The sites the patterns find equal the sites the file
  lists; an unlisted site fails, and so does a listed site that no longer
  occurs. The drift test holds this.
- **Explicit growth.** Because an unlisted site fails, new unverified prose
  can enter a scanned document only with a new line in this one file. The
  drift test holds this too.
- **No growth.** Reviewers assess baseline additions as additions of
  unverified prose between releases. Release preflight requires HEAD at an
  annotated release tag, reads the baseline at the previous release tag, and
  refuses a release whose baseline is not a subset of it. When the previous
  tag predates the baseline, preflight reports that instead of refusing.

Retain the baseline after this plan is deleted, and state in the suite README
which invariants have complete coverage.

## The test case

A new case, `generator_contract`, in the `source_drift` suite, with its module
at `tests/suites/source_drift/generators.py`, which also holds the
measurement functions. The existing per-generator modules keep their
stale-copy, broken-marker, build-refusal and manifest-shape controls, and
their mutation tables grow with each new field. Registration follows the
drift rules: a block in [run.sh](../tests/suites/source_drift/run.sh), an
entry in [catalog.json](../tests/catalog.json), the sentence in the suite's
row of [tests/README.md](../tests/README.md), and an invariants paragraph in
the [suite README](../tests/suites/source_drift/README.md#invariants). The
module imports each generator by path and runs every generator in a
disposable checkout, asserting afterward that a refused run left the checkout
byte-identical.

| Test | Holds | Asserts | Controls that must be refused |
| --- | --- | --- | --- |
| `test_build_checks_every_generator_before_signing` | G3 | the build script invokes `--check` for each of the four generators before the codesign block; the identity generator's regenerate-then-check pair counts | a build script lacking one check line |
| `test_regeneration_changes_nothing_outside_regions` | G1 | for each generator, a changed manifest regenerates with every target unchanged outside regions and whole-file outputs | a generator patched to append one byte after its END marker |
| `test_check_citations_carry_a_form_and_tests_are_defined` | G4, G5 | every check in both manifests has a form; every `test` symbol matches its file's definition pattern; every node, edge and limit has a `test` or `rule`; every limit's value owner has form `test`; every limits `kind` is unchanged; zero plain-word `test` symbols and zero `test` citations into fixtures | a check without a form; `install` with form `test`; an item with only controls; a `rule` that `main()` does not call; a value owner with form `control`; a limits check missing its `kind` |
| `test_manifests_do_not_cite_themselves_or_their_outputs` | G6 | no source citation in either manifest names the manifest or a file its generator writes | the document node citing its own marker |
| `test_fact_keys_are_declared_and_columns_follow_the_declaration` | G7 | every fact key is declared and used; the table header equals the declaration; the BYOXPC graph declares at most eight node keys | an undeclared key; an unused declared key; a renderer that collects keys from items |
| `test_durations_and_sizes_render_from_limits` | G8 | no manifest text matches the duration-or-size pattern; every placeholder names a limit id; the rendered text at each placeholder equals the limits table's value cell; bumping a value in a checkout's limits manifest changes the fact, the table and the dot stamp together; the limits manifest and document are byte-identical after an architecture run | a literal "7 seconds"; a placeholder naming no id; a renderer leaving placeholder text in the dot output |
| `test_spans_are_authored_outside_regions_and_copied_as_bytes` | G2, G9 | every authored span is current; `--check` names a stale span and an unknown name; regeneration repairs a stale span and a second run writes nothing; a span in the shared limits section reaches the guide's copy region with its rendered value; the span pass changes nothing inside any region | a stale authored span; `architecture.no_such_count`; a span inserted into a rendered region, refused as a stale region; a guide copy whose span value differs from its source, refused as a stale copy |
| `test_captions_state_the_verified_guarantee` | G10 | the caption and summary name presence and definition as the verified facts and say that assertion of the row is not verified; neither contains "exercises", "covers" or "proves" | a caption omitting the unverified clause; a caption containing any of the three words |
| `test_prose_links_resolve_anchors_and_symbol_links` | G11 | the shared link checker reports nothing for the scanned documents | a link to a missing heading; a symbol-form link whose symbol is absent; a reference-style link |
| `test_prose_baseline_is_consistent_and_growth_is_explicit` | G9, G11 | every site the patterns find is listed; every listed site occurs; a new site fails until a line is added to the baseline and nothing else; entries are reported per invariant | a new "7 seconds" sentence with no baseline line; a new citation pair with no baseline line; a baseline entry whose text no longer occurs |
| `test_release_preflight_refuses_a_grown_baseline` | G9, G11 | in a disposable git repository with two annotated release tags, the preflight accepts a baseline equal to or a subset of the previous tag's, refuses a superset, reports when the previous tag has no baseline, and turns the refusal into a warning under `--report` | a candidate with one added line; a candidate with a rewritten entry matching no previous entry |
| `test_measurements_match_this_plan` | all | the measurement functions reproduce the counts in [Where the generators stand](#where-the-generators-stand); it is edited as the numbers move and deleted with this plan | none |

## Sequence

Each step lands with `tests/run.sh --suite source_drift` green, the
architecture figures regenerated, and SVGs re-rendered where the dot text
changed.

1. C1.
2. C8. No generator changes; the property is recorded before the generators
   change.
3. C2 and C3 for the architecture manifest, with the mutation table in
   [architecture.py](../tests/suites/source_drift/architecture.py).
4. C2 for the limits manifest, with the mutation table in
   [limits.py](../tests/suites/source_drift/limits.py).
5. C4. The BYOXPC re-keying is reviewed as a figure change.
6. C5, including the two new limits rows.
7. C6, including the architecture introduction's span and the limits rewording.
8. C7 and C9, including the preflight rule. Initialize the baseline from the
   survey and remove an entry with each conversion.
9. `test_measurements_match_this_plan`, the README paragraphs, then delete
   this document and point the router line in [AGENTS.md](../AGENTS.md) at
   the drift suite README. An empty baseline is not a condition of deletion.

## What this plan leaves for later

For deferred prose conversions, remove the corresponding baseline entries
and report progress in the drift suite.

- Counts the prose states beyond the figure count: three native-API
  processes, seven evidence channels, four records with local versions, six
  core ideas, four manifests and four generators, six source-drift rules. The
  manifest can derive the first three; the rest need a rule or a span over a
  list.
- The budgets paragraph of [ARCHITECTURE.md](ARCHITECTURE.md), which names
  nine budgets by description and no limit id, and the three phrasings of
  "iteration counts, not wall-clock" across the two documents.
- The timeline bullets and the limits premises, whose citations are unread
  symbol-and-link pairs, and the positional pointers into numbered source
  comments.
- The "Known gap" convention: a rule that every paragraph opening with the
  marker is in the [index](ARCHITECTURE.md#known-gaps) and the index lists
  nothing else, and a decision about the shortfalls stated without it.
- The evidence-channels table, whose landing paths the shape goldens could
  verify.
- The document graph's drift node, which draws four rule edges where the
  drift script runs thirteen; C2's `rule` form gives a check its vocabulary.

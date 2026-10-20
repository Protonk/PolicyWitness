# Read Markdown through one vendored CommonMark parser

## Problem and intended result

The documentation generators, the `source_drift` checks and a few other tests
read Markdown structure with hand-written regular expressions and substring
tests in dozens of places, and the readers disagree. The
[Markdown read inventory](records/MARKDOWN-READ-INVENTORY.md) lists them.

- Three fence readers. [`document_prose`](tests/suites/source_drift/check.py)
  and [`prose_lines`](docs/generate_limits.py) are copies with a lenient opener
  (`^\s*` before the marker); [`harness_guidance_prose`](tests/suites/source_drift/check.py)
  allows 0-3 spaces, applies the info-string rule and also hides comments and
  indented code blocks. No other reader handles comments or indented code
  blocks, so G11 ([`broken_links`](tests/suites/source_drift/generators.py))
  reads links inside comments and indented examples.
- Four readers treat inline code four different ways; link targets
  are matched with `[^()\s]+`, `[^\s)]+` or `[^)]+`; only the guidance-route
  check excludes images and escaped brackets.
- Sections are bounded by heading level in one place, by the next `## ` in
  others, and by `text.split(heading)` substring splits in several `check.py`
  parsers that do not know about fences at all.
- Three slug functions disagree. [`heading_anchors`](docs/generator_common.py)
  adds duplicate suffixes, `check.py`'s `heading_anchor` does not, and
  [`generate_architecture.anchor`](docs/generate_architecture.py) drops `_`
  and non-ASCII letters, which GitHub keeps.
- Each reader is a partial CommonMark implementation with its own blind spots.
  The guidance reader, for example, treats an indented list nested inside a
  numbered item after a blank line as an indented code block; the nested list
  under step 3 of "Authoring a new augment" in
  [runner/augments/README.md](runner/augments/README.md) has that shape. A fix
  to one reader does not reach the others.
- Some checks test Markdown with plain substring tests that cannot tell a
  table or heading from text in a comment or code example. For example,
  `update_guide_extension_statuses` in [`generate_limits.py`](docs/generate_limits.py)
  accepts both required table headers when they appear only inside a comment.
- Thirty lines in the current documents begin with a span marker in the middle
  of a paragraph or list item. CommonMark starts an HTML block at a line that
  begins with `<!--`, and GitHub renders each of those lines as raw HTML
  outside its paragraph. In [docs/PolicyWitness.md](docs/PolicyWitness.md)
  this also shows a code span's backticks literally and drops its `<n>`
  placeholder. No current reader notices.

The intended result:

- markdown-it-py 3.0.0 and mdurl 0.1.2 are vendored unmodified under
  [`tests/lib/vendor/`](tests/lib/vendor/README.md), as tomli is.
- One module, `docs/markdown_reader.py`, is the only code that imports them. It
  parses a document once with a fixed configuration and reports facts taken
  from the parser's tokens: blocks and their line ranges, headings (level,
  text, line), sections, inline links and images (target, label, containing
  block), inline code, list items, table cells, fenced block content by info
  string and heading anchors.
- Every reader listed under [callers](#callers) uses that module and keeps
  only its policy: which document and section it reads and what it requires.
- The module's own logic is limited to selecting and reshaping tokens, the
  anchor slug and refusals for input the pinned parser reads differently from
  GitHub. It does not re-parse Markdown text with regular expressions, map
  tokens back to character positions or search source text for a token's
  content. [Source positions](#source-positions-and-recorded-text) explains
  what replaces position-based checks.

Follow [CONTRIBUTING.md](CONTRIBUTING.md#planning-a-change) and
[tests/AGENTS.md](tests/AGENTS.md) when executing it.

## Settled decisions

1. **Versions.** The system `/usr/bin/python3` (3.9.6) is a fixed design
   constraint. markdown-it-py 3.0.0 is the last release that supports Python
   3.9; 4.0.0 and later require 3.10. mdurl 0.1.2 is the current release and
   requires 3.7. The PyPI wheel digests are:

   | Wheel | SHA-256 |
   | --- | --- |
   | `markdown_it_py-3.0.0-py3-none-any.whl` | `355216845c60bd96232cd8d8c40e8f9765cc86f46880e43a8fd22dc1a1a8cab1` |
   | `mdurl-0.1.2-py3-none-any.whl` | `84008a41e51615a49fc9966191ff91509e3c40b939176e643fd50a5c2196b8f8` |

   markdown-it-py 3.0.0 implements CommonMark 0.30; 4.x implements 0.31.2. The
   3.x line receives no further releases. The OSV database listed no advisory
   for markdown-it-py 3.0.0 or mdurl 0.1.2 on 2026-10-19.
   [Parser and renderer behavior](#parser-and-renderer-behavior) lists the
   differences that matter here.
2. **Unmodified.** Copy each wheel's package directory byte for byte
   (`markdown_it/` is about 6,900 lines including its unused `cli/`; `mdurl/`
   about 550) and its licenses (`LICENSE` and `LICENSE.markdown-it` for
   markdown-it-py, `LICENSE` for mdurl). Record version, wheel, digest,
   importing module and license in the vendor README's table. If the parser
   misreads input a check depends on, the reader refuses that input with a
   diagnostic, or this plan is reconsidered. Do not patch vendored files or add a hand-written
   reader to compensate.
3. **One vendor directory.** Use `tests/lib/vendor/`; its README already
   describes code the build helpers import. The generators run during
   [`build.sh`](build.sh) (`--check` for each generator, `--stage-guide` at
   packaging), so the parser becomes a build-time dependency as tomli is.
   `docs/markdown_reader.py` resolves the vendor directory relative to its own
   file.
4. **Configuration.**
   `MarkdownIt("commonmark").enable("table").disable("text_join")`. The
   commonmark preset already enables HTML and disables linkify and the
   typographer. Use no plugins; linkify-it-py is not vendored. Tables are
   enabled because checks read their cells. `text_join` is disabled so that
   backslash escapes and entity references stay `text_special` tokens rather
   than merging into the surrounding `text`. The reader joins both kinds when
   it reports text, and the
   [comment refusal](#comments-the-pinned-parser-does-not-recognize) depends
   on telling them apart. In 3.0.0, `rules_inline/escape.py` and
   `rules_inline/entity.py` push `text_special` tokens, and
   `rules_core/text_join.py` converts and merges them. The reader's controls
   confirm this.
5. **Import guard.** Resolve the vendor directory, insert it at
   `sys.path[0]` and import. Refuse unless `markdown_it.__version__ ==
   "3.0.0"` and both `markdown_it.__file__` and `mdurl.__file__` resolve
   inside that directory. The build runs `/usr/bin/python3 -B` without `-I`.
   Without the guard, a disposable checkout that omits the vendored files
   could import a copy from site-packages and pass.

   One optional dependency needs the same treatment. When 3.0.0's
   `markdown_it/main.py` loads, it tries `import linkify_it`, and every
   `MarkdownIt()` constructs `linkify_it.LinkifyIt()` if that import
   succeeded, whatever the configuration
   ([upstream source](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v3.0.0/markdown_it/main.py)).
   An installed linkify-it-py, or anything importable as `linkify_it`, would
   run in every build. Before importing `markdown_it`, set
   `sys.modules["linkify_it"] = None`, which makes that import raise
   `ModuleNotFoundError`, and refuse if `linkify_it` is already imported.
   After the import, require `markdown_it.main.linkify_it is None`. This is
   the wheel's only import outside the standard library and mdurl.
6. **Prose follows the parser.** Fenced and indented code, HTML blocks and
   inline HTML, including comments, are not prose. Token-level facts such as
   links, inline code, headings and table cells exclude them exactly.
   Line-level checks see whole source lines of prose blocks, so inline code on
   a prose line stays part of that line, as it does today; see
   [source positions](#source-positions-and-recorded-text). G11 stops checking
   links inside comments; none exist today.
7. **One anchor slug.** Keep the rule `heading_anchors` applies now: lowercase,
   drop characters other than word characters, spaces and hyphens, replace
   spaces with hyphens, and add `-1`, `-2` for duplicates. Apply it to the
   heading's inline text from the tokens (text and code content, not link
   targets). It replaces `check.py`'s `heading_anchor` and
   `generate_architecture.anchor`. Of 830 headings in tracked Markdown, 54 get
   a different slug under the ASCII rule, mostly through `_` (for example
   "Test seam: `_test_overrides`" in [runner/README.md](runner/README.md)).
   No heading contains a link, image or HTML, so reading the text from tokens
   rather than raw Markdown changes no current anchor.
8. **Independent oracles stay independent.** `guidance_scenarios` and
   `gap_scenarios` in [`check_planner.py`](tests/suites/source_drift/check_planner.py)
   locate sections and links with their own patterns, deliberately
   independent of the checker's reader. The expected heading demotion in
   [`limits.py`](tests/suites/source_drift/limits.py) is likewise
   independent. Do not route them through the reader. Other test assertions
   about documents move; [callers](#callers) gives the rule. The unit tests in
   [`generators.py`](tests/suites/source_drift/generators.py) that call the
   real code are controls of the reader and follow the migration.
9. **Marker protocol stays textual.** `REGION_RE`, `SPAN_RE`, `region_ranges`,
   `authored_spans`, `block_bounds` and `replace_block` are a byte-offset
   protocol for writing generated files, not Markdown structure. Readers
   parse the original text, so markers are HTML tokens and the block
   structure is the one GitHub renders. A reader that excludes generated
   content (`document_prose`, `authored_prose`) drops blocks whose lines fall
   inside a generated or copied region. A line-level check takes each line's
   text from the marker-blanked source, which keeps lengths and newlines, so
   lines still align. Do not parse blanked text: a span blanked to spaces at
   the start of a line could turn that line into an indented code block.

## Source positions and recorded text

markdown-it reports line ranges for blocks. The children of an inline token
carry no position, and a token's content can differ from its source spelling:
`[x](<two words.md>)` yields the href `two%20words.md`. The first occurrence of
a repeated target can also sit inside an ignored code example. So no check maps
a token back to a character offset or finds one by searching the source.

- **Line-level checks** record or match whole source lines of the blocks the
  reader reports. The G9 literal sites in
  [`prose_sites`](tests/suites/source_drift/generators.py) are of this kind.
  A site is a line of a prose block (a paragraph, heading, list-item
  paragraph or table row) with markers blanked. The value pattern is matched
  against that line, and the recorded text is the line. The twelve current
  baseline entries are such lines and must be reproduced byte for byte.
  Inline code on a prose line stays in the line, as it does today, so the
  only possible effect is an extra site, which the baseline refuses; no site
  is hidden. A `count` row's text is matched against these lines joined; no
  `count` row exists today.
- **Token-level checks** use token content. A link target is the parser's href
  decoded with `urllib.parse.unquote`, so `<two words.md>` resolves to
  `two words.md`. G11's current pattern cannot see that form at all, and no
  document uses it today. A backticked label is a link whose only child is a
  `code_inline` token. Headings, cells and fenced content come from their
  tokens.
- **Citation pairs** (G11 `citation_pair` sites) are defined over the inline
  tokens of one container: a `code_inline` identifier, then a link to a
  non-Markdown file that contains the identifier, with no boundary between
  them. The boundaries are today's, expressed over tokens:
  - sentence punctuation followed by whitespace or by the link;
  - a literal `|`;
  - an earlier link;
  - the end of the container, which is a paragraph, heading, list-item
    paragraph or table cell.

  The 240-character limit runs from the start of the code span to the link,
  over rendered content, as the old limit ran over source text. An inline
  comment does not hide a sentence end. The recorded text is built from the tokens as
  `` `identifier` … [label](target) `` with the decoded target. The baseline
  holds no `citation_pair` entry and the current scan finds none, so the new
  form changes no entry. The migrated scan must also find none, or the
  migration stops for review.
- **Diagnostics** cite the document and the containing block's line range.

## Parser and renderer behavior

GitHub renderings below were checked on 2026-10-19 through GitHub's Markdown
API (`gh api markdown -f mode=gfm`) with synthetic snippets.

### Comments the pinned parser does not recognize

Under CommonMark 0.30 an HTML comment inside a paragraph cannot contain `--`.
The vendored pattern in `markdown_it/common/html_re.py` is
`<!---->|<!--(?:-?[^>-])(?:-?[^-])*-->`. Such a comment becomes text, so a link
inside it would count. GitHub hides it, link included, as CommonMark 0.31 does.
A comment that begins a line is an HTML block and is unaffected. Tracked
Markdown has 236 comments, 137 inline, and none is affected.

The reader refuses a `text` token containing `<!--`, including one in image
alt text, and names the document and block lines. Refuse only `text` tokens,
never `text_special` ones. With `text_join` disabled, a backslash escape
(`\<!--`) or an entity reference (`&lt;!--`) puts the `<` in a `text_special`
token, so neither is refused, and GitHub renders both as literal text. Inline
code containing `<!--` is a `code_inline` token and is not refused. This is
the only workaround for a parser difference that the plan expects.

### Span markers at the start of a line

In every CommonMark version and in GitHub's renderer, a line that begins with
`<!--` starts an HTML block, even in the middle of a paragraph. The block ends
on the line that contains `-->`. Thirty lines in the current documents begin
with a span marker, in paragraphs and list items of `controller/README.md`,
`docs/ARCHITECTURE.md`, `docs/BUILD.md`, `docs/LIMITS.md`,
`docs/PolicyWitness.md` and `tests/FAILURE-PROPAGATION-CONTRACT.md`. Three of
them, in the copied-limits region of `docs/PolicyWitness.md`, are copies of
`docs/LIMITS.md` lines; the rest are authored text.

GitHub renders each such line as raw HTML between two paragraphs. Inside it, a
code span keeps its backticks and an `<n>` placeholder disappears. The parser
reads these lines the same way, so the migration would quietly remove them
from prose. Before the migration, rewrap them so that no span marker begins a
line, and regenerate the copies with `docs/generate_limits.py`. Then refuse a
span marker that the reader reports inside an HTML block, in or beside
`span_problems`, naming the document and line. The other lines that begin
with HTML are the deliberate `<details>` and `<summary>` blocks and the
editorial markers in `MARKDOWN-GUIDANCE-PLAN.md`.

### Other differences

- **Other 0.31 and 4.x changes do not affect the facts the checks read.** These
  are Unicode symbols counting as punctuation for emphasis, the `search` and
  `source` HTML block tags, quadratic-time fixes in reference parsing and
  text joining, table cell limits and an unreleased fix for the whitespace
  set. No document uses `<search>`, `<source>` or U+001C–U+001F or U+0085. If
  timing shows quadratic behavior on a real document, report it rather than
  working around it.
- **Not GitHub's renderer.** GitHub's base is CommonMark 0.29 plus extensions
  (cmark-gfm 0.29.0.gfm.13). Bare-URL autolinks, alerts and footnotes are not
  parsed, and no check depends on them. The slug is ours in either case.

## Callers

The [Markdown read inventory](records/MARKDOWN-READ-INVENTORY.md) lists every
place where Python inspected Markdown content at this plan's commit, by file,
function and line. It classifies each as a structural read, a Markdown
rewrite, the marker protocol, plain text or an independent oracle, and gives
an example of a wrong pass or failure. Step 2 of the approach confirms and
updates it. The structural reads and rewrites that move to the reader are:

- **Prose and links.** `prose_lines` and `require_standalone` in
  `generate_limits.py` (two callers pass `require_standalone` raw text with no
  fence filter). `prose_text`, `broken_links`, `authored_prose`,
  `prose_sites` and the `count` rows of `baseline_problems` in
  `generators.py`. `document_prose` and `architecture_prose` in `check.py`.
- **Headings and sections.** `section`, `known_gap_index_problems`,
  `check_core_ideas_agreement`, `harness_guidance_prose` and
  `check_harness_guidance_routes` in `check.py`. Also in `check.py`, the
  section splits in `parse_index_rows`, `_parse_matrix_section`,
  `parse_readme_test_override_rows`, `parse_docs_prediction_unavailable_pairs`
  and `parse_readme_surface_lines`, which match substrings that also occur in
  longer headings, comments and fences. `readme_inventory` in
  `generate_build.py`. `shared_rules`, `shared_questions`, the heading checks
  in `validate_guide` and the heading count in `main` in `generate_limits.py`.
- **Tables and lists.** `check_evidence_channel_paths` and the tier cell in
  `check_baseline_in_catalog_defaults` in `check.py`.
  `update_guide_extension_statuses` and the one-row-per-limit count in
  `validate_guide` in `generate_limits.py`. The nested bullets of
  `readme_inventory` and the Known gap index bullets.
- **Anchors.** `heading_anchors` in `generator_common.py`, `heading_anchor` in
  `check.py` and `anchor` in `generate_architecture.py`, which
  `generate_build.py` also uses.
- **Citations of Markdown files.** `citation` in `generator_common.py`
  accepts a symbol anywhere in the cited file. The manifests cite Markdown
  files 20 times: 10 markers, 9 whole headings and `_test_overrides`, which
  appears in a heading's code span in `runner/README.md`. Check heading
  symbols against the reader's headings and markers against the marker
  protocol. The inventory step decides how to express `_test_overrides`.
- **Other suites.** `check_extensions.py` in `witness_contract` extracts the
  request JSON from `docs/PolicyWitness.md` by splitting on the first line of
  a fenced heredoc. Read it as that fenced block's content.
- **Rewrites.** Heading demotion in `update_guide` and `shared_questions`, and
  the guide-link rewrite in `shared_questions`, also change fenced and code
  text. Take the lines to demote and the links to rewrite from the reader.
- **Test assertions about documents.** These include the matrix, reading-rule,
  extension-status, copied-row and question assertions in `limits.py`; the
  `| id |` presence checks in `architecture.py` and `build.py`; the anchor
  check in `build.py`; the `| node |` presence check in `contract.py`; and the
  form-table and span-prefix tests in `generators.py`.

A test-side reader stays independent of `docs/markdown_reader.py` only when
its purpose is to check how a reader interprets Markdown. Those are
`guidance_scenarios` and `gap_scenarios` in `check_planner.py` and the
expected heading demotion in `limits.py`. Other assertions about authored or
generated documents are structural reads and move; their purpose is the
document's content, and the reader has its own controls. A test of an
emitter's exact output, produced in the same test, compares text and stays.
`check_release.py`'s assertions on the release evidence README are such a
test. Record each classification and its reason.

The three copies of `block_bounds` and `replace_block` in the generators
belong to the marker protocol and stay as they are.

G11 and `require_standalone` refuse reference-style links today with text
patterns. With the parser, a definition appears in the parse environment's
`references` and a resolved reference becomes an ordinary link token. Refuse
any document that defines a reference. An unresolved `[x][y]` is text in
CommonMark and renders as text, so it is no longer refused. Express the
standalone guide's autolink refusal over autolink tokens.

## Approach

1. **Fix the span lines first, in their own commit.** Rewrap the thirty lines
   so that no span marker begins a line, edit `docs/LIMITS.md` rather than its
   copies and regenerate them. This changes rendering, not checks. No
   baseline line is adjacent to one of these lines. The prose-baseline test
   must still pass unchanged, because release preflight refuses a baseline
   that is not a subset of the previous release's (D49).
2. **Inventory every Markdown read.** List every place where Python inspects
   the content of a Markdown document or a region of one. That covers
   substring tests, counts, index and find calls, splits, prefix tests and
   regular expressions. Classify each as one of:
   - a structural read, which moves to the reader;
   - a Markdown rewrite, which takes its targets from the reader, such as
     the heading lines to demote;
   - the marker protocol, which stays;
   - a plain-text search independent of Markdown structure, which stays;
   - an independent oracle or fixture, which stays.

   Record the classification in the verification record. The
   [callers](#callers) section and its inventory record describe the tree as
   of this plan; they are not a substitute for this step.
3. **Vendor and record.** Add the package directories, licenses and README
   rows. Add the reader and vendored files to each disposable-checkout file
   list whose copied modules will import the reader: `LIMITS_FILES`,
   `build_references` and `architecture_references` in
   [`contract.py`](tests/suites/source_drift/contract.py), the lists in
   `architecture.py`, `build.py`, `limits.py` and `check_planner.py`, and any
   other that a failing control names. One helper that lists the vendored
   files is preferable to more hand-written entries.
4. **Write the reader and its controls** before switching any caller (see
   [Verification](#verification)).
5. **Switch callers one group per commit.** Before each switch, run the old
   and new readings side by side over every document the caller reads. Compare
   prose lines and the links, headings, anchors, sections and cells found, and
   review every difference. Record the reviewed differences in the commit
   message and in the
   [verification record](records/MARKDOWN-PARSER-VERIFICATION.md), linked
   only from this plan. Expected differences: region marker lines become non-prose
   (they contain no links), and the augments nested list is prose. After
   step 1, no span marker begins a line, so span lines stay prose. The
   comparison scaffolding calls the old functions as they stand at the
   switch's parent commit; delete it after the last switch.
6. **Remove the replaced functions.** Add a `source_drift` rule that nothing
   other than `docs/markdown_reader.py` imports `markdown_it` or `mdurl`, and
   that each vendored file's SHA-256 matches the per-file digest in its wheel's
   `RECORD`, recorded beside the vendor README. These enforce the boundary and
   the unmodified copy; reintroduced hand parsing is still a review matter.
7. **Update the accounts.** The vendor README; the "Workflow guidance and
   checked routes" paragraph in
   [`source_drift/README.md`](tests/suites/source_drift/README.md), which
   describes the guidance reader's rules; a node for the reader in the
   documents graph of [`docs/architecture.json`](docs/architecture.json),
   beside `gen_common`, with edges to its readers, regenerated with
   `docs/generate_architecture.py`; and [`docs/build.json`](docs/build.json)
   if `generate_build.py --check` or the `build_documentation` case shows that
   a build step's account must name the new input.

## Verification

- **Reader controls** use constructed inputs with expected values written by
  hand. Each rule has a case that should be accepted and one that should be
  rejected:
  - Fences: backtick and tilde markers, a longer closer, a shorter non-closer,
    a backtick in a backtick fence's info string, a fence inside a list item.
  - Indentation: indented code after a blank line or heading; paragraph
    continuation; list-item content after a blank line, in the augments
    shape, read as prose.
  - Comments: block, inline and multi-line comments are not prose. An inline
    comment containing `--` is refused, including inside image alt text.
    `\<!--`, `&lt;!--` and `` `<!--` `` are accepted and reported as text or
    code.
  - Span markers: a span marker that begins a line inside a paragraph or list
    item is refused.
  - Links: a code label, a wrapped label, a label split by a blank line (not a
    link), an image, an escaped bracket, a link inside inline code (not a
    link), an autolink, an angle-bracket destination with a space (resolved to
    the decoded path) and a reference definition (refused).
  - Headings: ATX and setext levels, closing hashes, a heading inside a fence
    or comment (not a heading), section ends at the same or higher level.
  - Anchors: duplicate suffixes, `_` kept, code in a heading.
  - Tables: cell text with code spans and escaped pipes.
  - Line ranges: the lines reported for parsed blocks match the file, and the
    marker-blanked lines a line-level check reads align with them.
  - Import guard: a copy without the vendored files and with a stand-in
    `markdown_it` on `PYTHONPATH` is refused, naming the path; a version
    mismatch is refused. A stand-in `linkify_it` on `PYTHONPATH` that fails
    when imported is never imported, and the reader still works.
- **Structural-check controls.** Each structural read that moves to the reader
  gets a control in which its required construct appears only in a comment,
  a fence or inline code, and the check refuses it. For example,
  `update_guide_extension_statuses` refuses the issuance and delivery headers
  when they appear only in a comment, and accepts them as the header rows of
  two tables. `validate_guide` refuses a limit whose only row is inside a
  comment or fence.
- **Existing controls pass unchanged**, including the `check_planner.py`
  guidance and gap scenarios, the `generators.py` G9 and G11 tests, the
  `limits.py` rejection controls and the architecture, build and contract
  cases. Changing an existing expected result needs the same review as a
  comparison difference.
- **Prose baseline.** [`prose_baseline.json`](tests/fixtures/docs/prose_baseline.json)
  must not grow; release preflight refuses a grown baseline (D49). The twelve
  G9 entries are reproduced byte for byte, and no `citation_pair` site is
  found. A site that disappears because it is no longer prose is a reviewed
  difference. A site that appears stops the migration until it is explained.
- **Generated copies.** Every generator's `--check` passes without
  regeneration. If the slug change alters a generated anchor, regenerate with
  the owning generator and review the result.
- **Misleading passes.**
  - A reader that finds nothing would pass "no broken links". The
    accept-direction controls assert specific links, headings and cells, and
    each comparison shows its counts.
  - A fallback import from site-packages is caught by the guard and its
    control. An installed optional package is kept out by the `linkify_it`
    control.
  - A substring test can be satisfied by a comment or a code example. The
    structural-check controls cover each such check that moves.
  - A position-sensitive check could find the wrong occurrence of a target.
    No check searches the source for a token's content; see
    [source positions](#source-positions-and-recorded-text).
  - Scaffolding that shared code with the reader would compare the reader
    with itself, so it calls the old functions unchanged.
- **Runs.**
  - `tests/run.sh --suite source_drift` after each switch.
  - The `preflight` cases `release_publish_controls` and
    `release_rotation_controls` after `contract.py` or generator changes.
  - `witness_contract/extensions` after `check_extensions.py` changes; it
    needs the app.
  - A signed `make build` and the default battery at the end, because
    `build.sh` runs the generators.

  Record the parse time for all scanned documents under `/usr/bin/python3`.

## Where it stops

- Which documents are scanned and what each check requires do not change,
  with three exceptions. Links in comments stop counting. Unresolved `[x][y]`
  text is no longer refused, and reference links remain impossible because
  definitions are refused. A construct that appears only in a comment or a
  code example no longer satisfies a structural check, including a
  Markdown-heading citation.
- The region and span marker protocol and the Markdown emitters are
  unchanged, apart from targeting heading demotion. Documents change only
  through the span-line rewrap in step 1.
- tomli and `cargo_config.py` are unchanged.
- No Markdown style rules and no rendering to HTML.
- No move to markdown-it-py 4.x while `/usr/bin/python3` is 3.9.

## Questions the work answers

- Whether reading table cells through the parser reproduces the current
  `|` splitting for every table, including escaped pipes and code spans
  containing pipes. The comparison in step 5 answers it. A difference in a
  check's input is reviewed, not smoothed over.
- Whether parsing every scanned document noticeably lengthens the build or
  the drift suite. If so, cache parsed documents per process by path and
  content.

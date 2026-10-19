# Read Markdown through one vendored CommonMark parser

## Problem and intended result

The documentation generators and the `source_drift` checks read Markdown
structure with hand-written regular expressions in about twenty places, and
the readers disagree:

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
  GitHub. It does not re-parse Markdown text with regular expressions.

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
   for markdown-it-py 3.0.0 or mdurl 0.1.2 on 2026-10-19. [Known parser limits](#known-parser-limits)
   lists the differences that matter here.
2. **Unmodified.** Copy each wheel's package directory byte for byte
   (`markdown_it/` is about 6,900 lines including its unused `cli/`; `mdurl/`
   about 550) and its licenses (`LICENSE` and `LICENSE.markdown-it` for
   markdown-it-py, `LICENSE` for mdurl). Record version, wheel, digest,
   importing module and license in the vendor README's table. If the parser misreads input a
   check depends on, the reader refuses that input with a diagnostic, or this
   plan is reconsidered. Do not patch vendored files or add a hand-written
   reader to compensate.
3. **One vendor directory.** Use `tests/lib/vendor/`; its README already
   describes code the build helpers import. The generators run during
   [`build.sh`](build.sh) (`--check` for each generator, `--stage-guide` at
   packaging), so the parser becomes a build-time dependency as tomli is.
   `docs/markdown_reader.py` resolves the vendor directory relative to its own
   file.
4. **Configuration.** `MarkdownIt("commonmark").enable("table")`. The
   commonmark preset already enables HTML and disables linkify and the
   typographer. Use no plugins; linkify-it-py is not vendored. Tables are
   enabled because checks read their cells.
5. **Import guard.** Insert the vendor directory at `sys.path[0]`, import, and
   refuse unless `markdown_it.__version__ == "3.0.0"` and both
   `markdown_it.__file__` and `mdurl.__file__` resolve inside that directory.
   The build runs `/usr/bin/python3 -B` without `-I`. Without the guard, a
   disposable checkout that omits the vendored files could import a copy from
   Python's per-user site-packages and pass. `markdown_it/main.py` also attempts an
   optional `import linkify_it`; with linkify disabled it is unused and the
   guard ignores it.
6. **Prose follows the parser.** Fenced and indented code, HTML blocks and
   inline HTML, including comments, are not prose for any check. G11 therefore
   stops checking links inside comments; none exist today.
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
   independent of the checker's reader. The expected demotion and heading
   counts in [`limits.py`](tests/suites/source_drift/limits.py) are likewise
   independent. Do not route them through the reader. The unit tests in
   [`generators.py`](tests/suites/source_drift/generators.py) that call the
   real code are controls of the reader and follow the migration.
9. **Marker protocol stays textual.** `REGION_RE`, `SPAN_RE`, `region_ranges`,
   `authored_spans`, `block_bounds` and `replace_block` are a byte-offset
   protocol for writing generated files, not Markdown structure. Where a
   reader excludes generated content before reading prose (`document_prose`,
   `authored_prose`), blank the region bytes while keeping newlines and parse
   the result, so line ranges still match the file.

## Known parser limits

- **Inline comments containing `--`.** Under CommonMark 0.30 an HTML comment
  inside a paragraph cannot contain `--`; the vendored pattern in
  `markdown_it/common/html_re.py` is `<!---->|<!--(?:-?[^>-])(?:-?[^-])*-->`.
  Such a comment becomes text, so a link inside it would count. CommonMark
  0.31 and cmark-gfm, the public reference for GitHub's renderer, treat it as a
  comment. Comments that begin a line are HTML blocks and are unaffected.
  Tracked Markdown has 236 comments, 137 inline, and none is affected. The
  reader refuses any text token containing `<!--`, naming the document and
  block lines. This is the only workaround the plan expects.
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

| Reader | Used by | Notes |
| --- | --- | --- |
| `harness_guidance_prose`, `check_harness_guidance_routes` in `check.py` | Harness guidance sections and routes (D22, D23, D29, D62) | A section ends at the next heading of the same or higher level. A route is an inline link, not an image, in the root section. |
| `document_prose`, `architecture_prose`, `section`, `heading_anchor`, `known_gap_index_problems`, `check_evidence_channel_paths`, `check_core_ideas_agreement` in `check.py` | Known gap indexes, evidence-channel table cells, core-idea labels | The `AGENTS.md` side of the core-ideas comparison reads raw text today. |
| `parse_index_rows`, `_parse_matrix_section`, `parse_readme_test_override_rows`, `parse_docs_prediction_unavailable_pairs`, `parse_readme_surface_lines` in `check.py` | Suite coverage, outcome matrices, `_test_overrides` table, prediction-unavailable list, CLI surface | Substring section splits, `\|`-split table rows and a regex for the `text` fence under "CLI surface (contract)". |
| `prose_lines`, `require_standalone`, `validate_guide`, `shared_rules`, `shared_questions` in `generate_limits.py` | Standalone guide refusals, anchors and heading rules | Heading demotion rewrites text for output; rewrite only the lines the reader reports as level-2 headings. |
| `heading_anchors` in `generator_common.py` | G11, `validate_guide`, the DOT URL check in `build.py` | Becomes the single slug. |
| `anchor` in `generate_architecture.py` | DOT node URLs, LIMITS links, `generate_build.py` | Replaced by the single slug. |
| `readme_inventory` in `generate_build.py` | README "Build and bundle" inventory | Section read. |
| `prose_text`, `broken_links`, `authored_prose`, `prose_sites` in `generators.py`, and the span-prefix test's code stripping | G11 links and anchors, G9 literal sites, citation pairs | The prose baseline depends on these. |

G11 and `require_standalone` refuse reference-style links today with text
patterns. With the parser, a definition appears in the parse environment's
`references` and a resolved reference becomes an ordinary link token. Refuse
any document that defines a reference. An unresolved `[x][y]` is text in
CommonMark and renders as text, so it is no longer refused. Express the
standalone guide's autolink refusal over autolink tokens.

## Approach

1. **Vendor and record.** Add the package directories, licenses and README
   rows. Add the reader and vendored files to each disposable-checkout file
   list whose copied modules will import the reader: `LIMITS_FILES`,
   `build_references` and `architecture_references` in
   [`contract.py`](tests/suites/source_drift/contract.py), the lists in
   `architecture.py`, `build.py`, `limits.py` and `check_planner.py`, and any
   other that a failing control names. One helper that lists the vendored
   files is preferable to more hand-written entries.
2. **Write the reader and its controls** before switching any caller (see
   [Verification](#verification)).
3. **Switch callers one group per commit.** Before each switch, run the old
   and new readings side by side over every document the caller reads. Compare
   prose lines and the links, headings, anchors, sections and cells found, and
   review every difference. Record the reviewed differences in the commit
   message and in a verification record under `records/`, linked only from
   this plan. Expected differences: generated-region and span marker lines
   become non-prose (they contain no links), and the augments nested list is
   prose. The comparison scaffolding calls the old functions as they stand at
   the switch's parent commit; delete it after the last switch.
4. **Remove the replaced functions.** Add a `source_drift` rule that nothing
   other than `docs/markdown_reader.py` imports `markdown_it` or `mdurl`, and
   that each vendored file's SHA-256 matches the per-file digest in its wheel's
   `RECORD`, recorded beside the vendor README. These enforce the boundary and
   the unmodified copy; reintroduced hand parsing is still a review matter.
5. **Update the accounts.** The vendor README; the "Workflow guidance and
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
  - Comments: block, inline and multi-line comments; an inline comment
    containing `--` is refused.
  - Links: a code label, a wrapped label, a label split by a blank line (not a
    link), an image, an escaped bracket, a link inside inline code (not a
    link), an autolink, and a reference definition (refused).
  - Headings: ATX and setext levels, closing hashes, a heading inside a fence
    or comment (not a heading), section ends at the same or higher level.
  - Anchors: duplicate suffixes, `_` kept, code in a heading.
  - Tables: cell text with code spans and escaped pipes.
  - Line ranges: reported lines match the file after region blanking.
  - Import guard: a copy without the vendored files and with a stand-in
    `markdown_it` on `PYTHONPATH` is refused, naming the path; a version
    mismatch is refused.
- **Existing controls pass unchanged**, including the `check_planner.py`
  guidance and gap scenarios, the `generators.py` G9 and G11 tests, the
  `limits.py` rejection controls and the architecture, build and contract
  cases. Changing an existing expected result needs the same review as a
  comparison difference.
- **Prose baseline.** [`prose_baseline.json`](tests/fixtures/docs/prose_baseline.json)
  must not grow; release preflight refuses a grown baseline (D49). A site that
  disappears because it is no longer prose is a reviewed difference. A site
  that appears stops the migration until it is explained.
- **Generated copies.** Every generator's `--check` passes without
  regeneration. If the slug change alters a generated anchor, regenerate with
  the owning generator and review the result.
- **Misleading passes.**
  - A reader that finds nothing would pass "no broken links". The
    accept-direction controls assert specific links, headings and cells, and
    each comparison shows its counts.
  - A fallback import from site-packages is caught by the guard and its
    control.
  - Scaffolding that shared code with the reader would compare the reader
    with itself, so it calls the old functions unchanged.
- **Runs.** `tests/run.sh --suite source_drift` after each switch. The
  `preflight` cases `release_publish_controls` and `release_rotation_controls`
  after `contract.py` or generator changes. A signed `make build` and the
  default battery at the end, because `build.sh` runs the generators. Record
  the parse time for all scanned documents under `/usr/bin/python3`.

## Where it stops

- Which documents are scanned and what each check requires do not change,
  except that links in comments stop counting and unresolved `[x][y]` text is
  no longer refused. Reference links remain impossible because definitions are
  refused.
- The region and span marker protocol and the Markdown emitters are
  unchanged, apart from targeting heading demotion.
- tomli and `cargo_config.py` are unchanged.
- No Markdown style rules and no rendering to HTML.
- No move to markdown-it-py 4.x while `/usr/bin/python3` is 3.9.

## Questions the work answers

- Whether reading table cells through the parser reproduces the current
  `|` splitting for every table, including escaped pipes and code spans
  containing pipes. The comparison in step 3 answers it. A difference in a
  check's input is reviewed, not smoothed over.
- Which diagnostics need a link's own line. Inline tokens carry no line map in
  markdown-it; the reader reports the containing block's line range. Where a
  check needs the exact line, it locates the target text within those lines
  without parsing it.
- Whether parsing every scanned document noticeably lengthens the build or
  the drift suite. If so, cache parsed documents per process by path and
  content.

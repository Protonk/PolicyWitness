# Markdown reads in the Python tooling

Background for the Markdown parser migration. The completed
`MARKDOWN-PARSER-PLAN.md` is preserved in commit `1da5aad`; the inventory,
line numbers and measurements here describe commit `f93323c`.

## Method

- Tracked Python files were swept for every operation on the text of a
  Markdown document or a region of one: substring tests, counts, `index` and
  `find`, `split` and `partition`, prefix tests, replacements and regular
  expressions. `tests/out/`, `.tmp/`, `dist/`, `controller/target/`,
  `.scratch/` and `tests/lib/vendor/` were excluded. A sample of entries was
  confirmed by reading the code. The plan's inventory step confirms the rest.
- Measurements ran over `git ls-files '*.md'`.
- Rendering was checked on 2026-10-19 with GitHub's Markdown API
  (`gh api markdown -f mode=gfm`) using the synthetic snippet below.

## Classes

| Class | Meaning |
| --- | --- |
| S | Structural read: depends on headings, sections, tables, lists, links, inline code, fences, comments or paragraphs. |
| W | Markdown rewrite: changes Markdown text for output. |
| M | Marker protocol: `BEGIN`/`END` region markers, span markers and figure stamps, handled by byte offset. |
| P | Plain text: a search that does not depend on Markdown structure. |
| O | Independent oracle or fixture construction. |

Hazards shared by several S and W entries:

- **H1.** A substring or regular expression on raw text also matches inside a
  comment, fence, indented code block or inline code.
- **H2.** `block_bounds` requires each marker to occur exactly once, so a
  marker quoted in prose or code fails the check. This errs toward refusal.
- **H3.** Heading demotion with `re.sub(r"^## ", "### ", ...)` also rewrites
  `## ` lines inside fences.
- **H4.** `heading_anchors` strips comments but not fences unless its caller
  filtered them first. It ignores setext headings and indentation, and its
  pattern can take the line after a lone `#` as heading text. Its comment
  strip also runs from a `<!--` inside inline code to the next `-->`, removing
  any headings in between. Run over `MARKDOWN-PARSER-PLAN.md`, it reports three
  of the plan's valid in-page anchors as missing.
- **H5.** `prose_lines` and `document_prose` handle fences only, accept any
  indentation and accept a closing fence that carries an info string.
- **H6.** Table cells are found with `startswith("| ")` and `split("|")`, so a
  pipe inside inline code shifts the columns.

## Inventory

### `docs/generator_common.py`

| Line | Function | Operation | Class | Wrong result |
| --- | --- | --- | --- | --- |
| 65-67 | `citation` | `symbol not in text` for any cited file | P as written; S for Markdown targets | A cited heading present only in a comment or fence passes. |
| 138-194 | `REGION_RE`, `SPAN_RE`, `region_ranges`, `authored_spans`, `span_problems`, `render_spans` | marker matching and span splicing | M, W for `render_spans` | A marker inside a fence is treated as real. |
| 197-208 | `heading_anchors` | comment strip, ATX heading pattern, slug with duplicate suffixes | S | A heading-shaped line in an unfiltered fence creates an anchor, so a dead link passes (H4). |
| 51-53 | `form_table` | emits the citation-form table | W | |

### `docs/generate_limits.py`

| Line | Function | Operation | Class | Wrong result |
| --- | --- | --- | --- | --- |
| 191 | `shared_rules` | requires a line starting `1. ` and no line starting `#` | S | A `#` comment line in a fenced example fails it. |
| 205 | `update_guide_extension_statuses` | both table headers present as substrings | S | Headers only inside a comment pass. |
| 207, 356-357 | `update_guide_extension_statuses`, `validate_guide` | `require_standalone` on raw text | S | A link example in a fence or code span fails. |
| 248-256 | `block_bounds`, `replace_block` | marker counts and slices | M | H2. |
| 288 | `update_guide` | heading demotion | W | H3. |
| 296 | `shared_questions` | heading pattern over `prose_lines` | S | H5. |
| 301-302 | `shared_questions` | heading demotion; guide-link rewrite with `str.replace` | W | H3; the link rewrite also changes code spans and fences. |
| 315-319 | `require_standalone` | reference-link, definition and autolink patterns; link targets matched with `[^)]+` | S | A `](x)` in inline code fails it; a destination containing `)` or written in angle brackets is misread. |
| 322-334 | `prose_lines` | fence tracking | S | H5. |
| 340-343 | `validate_guide` | each limit's code span counted once in the copied region | S | One row plus a commented or fenced copy fails; a deleted row whose code span appears in prose passes. |
| 347, 352 | `validate_guide` | `### ` heading and `1. ` list presence | S | A heading or item in a fence counts. |
| 361-367 | `validate_guide` | anchors and internal link targets | S | H4; links in inline code count. |
| 405 | `main` | counts `### ` lines without a fence filter | S | A fenced `### ` line counts. |
| 142-245 | `cell`, `render_matrix`, `reference`, `render`, `render_coverage` | emitters | W | |

### `docs/generate_architecture.py` and `docs/generate_build.py`

| Line | Function | Operation | Class | Wrong result |
| --- | --- | --- | --- | --- |
| architecture 237-238 | `anchor` | ASCII-only slug | S/W | Drops `_` and non-ASCII letters, unlike `heading_anchors`. Also used by `generate_build.py`. |
| architecture 325-424 | table, figure and `<details>` emitters | emitters | W | |
| architecture 427-467, 511-539 | `block_bounds`, `render_document`, stamps | markers | M | H2. |
| build 752-769 | `readme_inventory` | `## Build and bundle` section by pattern; bullets by two- or four-space indent and inline code | S | A fenced or commented bullet counts; a fenced `## ` ends the section; a last section without a following `## ` is not found. |
| build 896-1031 | stamps, emitters, `render_document` | | M, W | |

### `tests/suites/source_drift/check.py`

| Line | Function | Operation | Class | Wrong result |
| --- | --- | --- | --- | --- |
| 176-189 | `parse_index_rows` | `split("## Suite coverage")`, next `##`, row pattern | S | The split also matches `### Suite coverage`; a row-shaped line in a comment or fence counts. |
| 266-267 | `check_baseline_in_catalog_defaults` | tier cell compared as text | S | Emphasis in the cell breaks it. |
| 192-212 | `_parse_matrix_section` | same split and row pattern | S | Same as `parse_index_rows`. |
| 547-565 | `parse_docs_prediction_unavailable_pairs` | section pattern not anchored to a line; bullet pattern | S | A `###` heading or a heading in a fence ends the list; a commented bullet counts. |
| 805-820 | `parse_readme_test_override_rows` | split on the heading, row pattern | S | Same as `parse_index_rows`. |
| 857-935 | `harness_guidance_prose`, `check_harness_guidance_routes` | fences, comments, indentation, ATX headings, routes | S | ATX headings with exact titles only; a list item's content after a blank line is read as code. |
| 957-970 | `parse_readme_surface_lines` | heading text then the next `text` fence, by pattern | S | Not anchored to a heading line; only a backtick `text` fence is accepted, and a longer fence is misread. |
| 997-1017 | `architecture_prose`, `document_prose` | generated-region strip, fence tracking | M and S | H5; comments and indented code remain prose. |
| 1020-1026 | `heading_anchor`, `section` | slug without duplicate suffixes; level-2 section pattern | S | A `## ` line in an unfiltered fence or comment ends the section. |
| 1042-1060 | `known_gap_index_problems` | level-2 headings; paragraphs starting `Known gap`; index bullets with fragment links | S | A commented bullet counts; `*` or `+` bullets are missed. |
| 1070-1085 | `check_evidence_channel_paths` | table rows by prefix, cells by `split("\|")`, code spans in the fourth cell | S | H6; a commented row counts. |
| 1090-1099 | `check_core_ideas_agreement` | bold-led bullets; the `AGENTS.md` side read raw | S | A commented bullet on the `AGENTS.md` side counts. |

### `tests/suites/source_drift/generators.py`

| Line | Function | Operation | Class | Wrong result |
| --- | --- | --- | --- | --- |
| 37-91, 695-714 | `ownership`, `outside`, ownership test | marker offsets | M | |
| 116-118 | `prose_text` | `prose_lines` | S | H5. |
| 127-153 | `broken_links` | code-span masking, reference-link refusal, link pattern, anchors, backticked-label symbol search | S, P for the symbol search | Links in comments are checked; images are treated as links; a titled link or an angle-bracket destination is skipped. |
| 158-167 | `authored_prose` | `prose_text`, then markers found on fence-stripped text | M and S | Markers inside fences are invisible here but visible to `authored_spans`. |
| 170-205 | `prose_sites` | G9 line scan; citation pairs over a 240-character window, sentence boundaries and source slices | S | Position-based; see the plan's source-position section. |
| 224 | `baseline_problems` | `count` rows as substrings of authored prose | S/P | No `count` row exists. |
| 525-532 | span-prefix test | `prose_lines`, inline-code masking, `authored_spans` | S/M | |
| 534-588 | link and baseline tests | constructed documents | O | |
| 671-679 | `test_readme_form_table_is_a_copy_of_the_shared_rules` | table block as a substring; each form's row counted once | S | A copy of the table in a fence or comment passes or breaks the count. |

### Other tests

| File and line | Function | Operation | Class | Wrong result |
| --- | --- | --- | --- | --- |
| `source_drift/limits.py` 72-81 | matrix table test | rows by prefix, cells by `split(" \| ")` | S | H6. |
| `source_drift/limits.py` 84-88 | reading rules test | numbered-item count; no `](` | S | |
| `source_drift/limits.py` 128-138 | extension status test | split at the delivery header; first-cell code spans | S | |
| `source_drift/limits.py` 186-207 | copied rows and questions tests | expected demotion (oracle), row counts, link targets, heading counts | O for the demotion, S for the rest | |
| `source_drift/limits.py` other | mutation and generation tests | constructed inputs | O | |
| `source_drift/architecture.py` 133-148 | `test_every_id_is_in_its_generated_region` | `\| id \|` presence in a region | M and S | An id in an edge's From or To cell satisfies a node-table check. |
| `source_drift/build.py` 113-132 | `test_every_id_is_in_its_generated_region` | `\| id \|` presence in regions | M and S | |
| `source_drift/build.py` 163-165 | figure link test | `heading_anchors` on raw `BUILD.md` | S | H4 without a fence filter. |
| `source_drift/contract.py` 394-415 | build refusal tests | `\| node \|` and `\| admission \|` presence, then mutation | S and O | |
| `source_drift/check_planner.py` 159-292 | `guidance_scenarios`, `gap_scenarios`, principle controls | own heading, section and link patterns; mutations | O | Deliberately independent of the checker. |
| `witness_contract/check_extensions.py` 100-101 | `main` | extracts the request JSON from the guide's fenced heredoc by splitting on its first line | S | The first occurrence anywhere counts, including one in a comment or prose. |
| `preflight/check_release.py` 87-96 | `main` | table-row text in a README the test just generated | P | Checks the emitter's output; a commented row would pass. |
| `tests/lib/release_evidence.py` 44-82 | `summarize` | emits that README | W | |

`docs/generate_contract.py` uses its own `block_bounds` and `replace_block`
copies (M) and emits a table and a sentence (W). `generate_worker_identity.py`
marks regions in code files only.

## Rendering check

Input:

````markdown
The verify command waits
<!-- span a.b -->5,000 milliseconds<!-- /span --> timeout; pass `--timeout-ms <n>` for slow
hosts and [a link](x.md).

Second: text <!-- a -- b [hidden](y.md) --> after. Escaped \<!-- not a comment, entity &lt;!-- too.
````

GitHub's output:

```html
<p>The verify command waits</p>
5,000 milliseconds timeout; pass `--timeout-ms ` for slow
<p>hosts and <a href="x.md">a link</a>.</p>
<p>Second: text  after. Escaped &lt;!-- not a comment, entity &lt;!-- too.</p>
```

A line that begins with a span marker leaves its paragraph as raw HTML, an
inline comment containing `--` is hidden with its link, and escaped or
entity-encoded `<!--` is literal text.

## Measurements

- 830 ATX headings. 54 get a different slug from `generate_architecture.anchor`
  than from `heading_anchors`, mostly through `_`. None contains a link, image
  or HTML.
- 236 HTML comments, 137 of them inline. None is rejected by CommonMark 0.30's
  inline comment rule. The 18 documents G9 and G11 scan contain no comment
  other than markers.
- 30 lines begin with a span marker inside a paragraph or list item. 27 are
  authored: `controller/README.md` 62, 153, 205, 344, 348, 376;
  `docs/ARCHITECTURE.md` 552, 556, 776; `docs/BUILD.md` 1032-1035, 1037-1039;
  `docs/LIMITS.md` 23, 179, 190, 435-437; `docs/PolicyWitness.md` 1881, 2304;
  `tests/FAILURE-PROPAGATION-CONTRACT.md` 958, 1059, 1113. Three are in the
  copied-limits region of `docs/PolicyWitness.md` (755, 911, 922). No
  prose-baseline line is adjacent to any of them. The other lines that begin
  with HTML are `<details>` and `<summary>` blocks and editorial markers.
- 20 manifest citations name a Markdown file: 10 name a marker, 9 a whole
  heading, and one, `_test_overrides` in `runner/README.md`, text inside a
  heading's code span.
- The prose baseline holds 12 G9 `literal` entries, each a whole source line
  with spans blanked to spaces. The current scan finds no `citation_pair`
  site.
- No document uses an angle-bracket link destination, and none contains
  U+001C–U+001F or U+0085.

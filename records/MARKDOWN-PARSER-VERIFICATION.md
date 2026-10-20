# Markdown parser migration: verification

Evidence for [MARKDOWN-PARSER-PLAN.md](../MARKDOWN-PARSER-PLAN.md). Each switch
compared the old reading, taken from the parent commit's code, with the new
reading over every document the caller reads. The tables below list every
difference and its review. Test runs are under `tests/out/runs/` and are
gitignored; they are available only in the local checkout.

## Span-line rewrap (`ef79e1c`)

Thirty lines began with a span marker inside a paragraph or list item. Each
now starts with the preceding word, and the four-line arithmetic in
`docs/LIMITS.md` sits on one line, because a line starting with `>` or `+` in a
list item would open a block quote or a bullet. `docs/generate_limits.py`
regenerated the three copies in `docs/PolicyWitness.md`. No tracked Markdown
line begins with a span marker afterwards. GitHub's Markdown API rendered the
repaired `docs/PolicyWitness.md` passage as one paragraph with its code span.
Every generator's `--check` and `source_drift` passed
(`span-line-rewrap-20261019`); the prose baseline was unchanged.

## Vendored parser and reader (`6d1c65a`)

The two wheels matched PyPI's SHA-256 digests. All 78 vendored files match
their `RECORD` digests, with none added or missing. Under `/usr/bin/python3`
3.9.6 the reader parsed all 120 tracked documents in about 750 ms without a
refusal. Removing the `linkify_it` block or the location check made the
corresponding import-guard control fail. `source_drift` passed
(`markdown-reader-foundation-20261019`).

## Anchors, citations, span placement and the README inventory

| Reading | Compared over | Differences | Review |
| --- | --- | --- | --- |
| Heading anchors: `heading_anchors` over `prose_lines` against the reader's anchors | All 120 tracked documents | `MARKDOWN-PARSER-PLAN.md` gains five anchors | The old comment strip ran from a `<!--` in inline code to the next `-->` and removed those headings. The reader's anchors are the ones GitHub renders. |
| Heading anchors for `BUILD.md`'s figure links (`build.py`) | `docs/BUILD.md` | None | |
| `generate_architecture.anchor` against `markdown_reader.slug` | Every generated link fragment | None | Every generator's `--check` passed without regeneration. |
| `readme_inventory` | `README.md` | None | Seven paths and one service bundle in both. |
| Markdown citations | All 20 in the three manifests | None | All name a region marker, a heading or a heading's code span. |
| Span placement | Every span document | None | No authored span marker is in an HTML block after `ef79e1c`. |

Two existing controls inserted a span marker at the start of a line, which the
generators now refuse. One gained a word before the span; the other passed a
constructed string to `authored_spans`, which now starts with a word. Neither
control's purpose changed. New controls: a generator refuses a span marker
that begins a line and leaves the checkout unchanged; a Markdown citation is
refused when its symbol appears only in prose, a comment or a fence.
`source_drift` passed (`markdown-switch-anchors-2-20261019`).

## The limits generator and its tests

| Reading | Compared over | Differences | Review |
| --- | --- | --- | --- |
| `shared_rules`, `shared_questions`, `update_guide`, `update_guide_questions`, `update_guide_rules`, `update_guide_extension_statuses` | The current contract, questions, limits document and guide | None | Each returns the same text as the parent commit's version. |
| `validate_guide` | The current guide | None | Both versions accept it. |
| The copied-question count in `main` | `docs/QUESTIONS.md` | None | 15 in both. |

Heading demotion now rewrites only the lines the parser reports as level-two
headings, and the guide-link rewrite is refused if it changes anything but link
targets. Reference definitions and autolinks are refused through the parser's
tokens; unresolved `[x][y]` text is no longer refused. The `limits.py`
assertions about table rows, numbered items, headings and links now read through
the reader; the expected demotion stays an independent oracle. New controls:
tables, numbered lists and limit rows shown only in a comment, a fence or inline
code satisfy no check; a quoted copy of a limit row beside the real one is not
a second row; link examples in inline code do not count against a standalone
section; fenced `## ` lines are not demoted. `source_drift` passed
(`markdown-switch-limits-20261019`).

## G9 and G11

| Reading | Compared over | Differences | Review |
| --- | --- | --- | --- |
| `prose_sites` | The 18 scanned documents | None | The same 12 G9 entries, byte for byte, and no citation pair. |
| `broken_links` results | The 18 scanned documents | None | No broken link in either version. |
| Links that G11 checks | The 18 scanned documents | 5 more: 2624 before, 2629 after | Three labels wrap across a line (`docs/BUILD.md:60` and `:521`, `docs/SIGNING.md:194`) and two code labels contain `]` (`docs/BUILD.md:119` and `:135`). The old pattern skipped them. All five resolve, and the code labels' symbols are in their targets. |

Citation pairs are now defined over the parser's inline pieces, as
[source positions](../MARKDOWN-PARSER-PLAN.md#source-positions-and-recorded-text)
describes, and recorded as `` `identifier` … [label](target) ``. No baseline
entry has that kind, and the scan still finds none. The span-prefix ownership
test now finds spans as HTML comments in prose, so examples in code do not
count; the form-table copy test also requires one rendered table with the same
cells. `prose_lines` and `prose_text` are gone. New controls: a broken link
with a wrapped label or a code label containing `]` is reported; text in a
comment or inline code is not a link. `source_drift` passed
(`markdown-switch-g9-g11-20261019`).

## The drift checker

| Reading | Compared over | Differences | Review |
| --- | --- | --- | --- |
| Suite-coverage rows, both outcome matrices, the `_test_overrides` rows, the prediction-unavailable pairs, the CLI surface lines | `tests/README.md`, `tests/COVERAGE.md`, `runner/README.md`, `docs/PolicyWitness.md`, `controller/README.md` | None | 42 suites, 16 and 10 outcomes, 10 keys, 4 pairs and 3 usage lines in both. The prediction-unavailable section is level 3; the old pattern found it only because `## ` is a substring of `### `. |
| Evidence-channel landing paths and the core-idea labels | `docs/ARCHITECTURE.md`, `AGENTS.md` | None | 12 paths and 6 labels in both. |
| Known gap paragraphs and index links | The architecture, build and worker tours | None | Indexes of 1, 5 and 3 entries in both. |
| Guidance sections and root routes | The four guidance documents | None | Both pass. |

`harness_guidance_prose`, `document_prose`, `architecture_prose`, `section` and
`heading_anchor` are gone. A document the reader refuses is reported as a
problem, and the other checks still run. The planner copies the reader and the
vendored parser into its disposable checkout; its fixtures still find sections
and links with their own patterns. New planner controls: a route in list
content after a blank line passes, which the old checker reported as missing,
and an inline comment containing `--` is refused. The first version of the
refusal control put the comment at the start of a line, which is an HTML block
that the parser and GitHub both hide, so the checker reported a missing route.
The control now puts a word first. All 182 planner controls passed;
`source_drift` passed (`markdown-switch-check-3-20261019`).

## Test assertions about documents and the document graph

| Reading | Compared over | Differences | Review |
| --- | --- | --- | --- |
| Generated-region ids in `architecture.py` and `build.py` | `docs/ARCHITECTURE.md`, `docs/WORKER.md`, `docs/BUILD.md` | None | Both pass. Node and edge ids must now open rows of their own tables, in manifest order, instead of appearing anywhere in the region; the figure must be an image. |
| The mutation targets in `contract.py`'s stale-copy build controls | `docs/ARCHITECTURE.md`, `docs/BUILD.md` | None | Each id is the first cell of a table row before the control rewrites it. |
| The request JSON `check_extensions.py` runs | `docs/PolicyWitness.md` | None | One `sh` fence holds the heredoc, and the extracted text is identical. |

`docs/architecture.json` gains a `library` node kind and a `markdown_reader`
node in the document graph, with "reads" edges D67-D72 to the generators and
drift checks that use the reader. A citation of the vendor README's table was
refused by the new Markdown citation rule, so the node cites
`markdown_it/__init__.py`'s version instead. The generator wrote the region,
dot file and SVG; every generator's `--check` passed. `source_drift` passed
(`markdown-switch-tests-20261019`).

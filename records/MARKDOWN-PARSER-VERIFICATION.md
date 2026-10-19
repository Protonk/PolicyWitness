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

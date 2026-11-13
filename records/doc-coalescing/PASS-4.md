# Fourth coalescing pass

Pass 4 of [DOC-COALESCING-PLAN](../../docs/DOC-COALESCING-PLAN.md) is implemented
in `7a411d2bee731feb4cdc83a4d2157fae222fa77a`.

The renderer keeps each owner's grade, exact claim/subtree scope, assertion,
context and limits beside its claim. Source/check citations and execution
identifiers move into the existing Evidence support section. Each owner has
its own detail link and exact local backlink, including compact table rows and
multiple owners of one claim. Both presentations use the same authored record;
there is no new schema, selector or maintained evidence copy.

An eight-owner pilot covered example emission, lesson emission, the extracted
example, envelope completion, execution diagnostics, actor diagnostics, report
fallback and executed gate support. Sol reviewed which qualifications must
stay local; Astra accepted a uniform split and reviewed the generated result.
No assertions/scopes justified merging owners. Those reviews support this
presentation decision without upgrading any evidence grade.

## Effect and preservation

All 148 local support paragraphs remain. Using the repository's Markdown
reader to count their visible whitespace-separated words, the total drops
from 8,795 to 7,636 (about 13%). Visible characters drop from 83,289 to 58,179.
The whole Markdown document grows from 716,404 to 762,734 characters because
the appendix adds headings and navigation. This reduces citation clutter in
the claim-reading path; it does not reduce authored support records or total
document length.

Rejoining every local paragraph with its appendix detail reproduces the
original 148 support paragraphs exactly. The original anchors remain, and
explicit anchors have no duplicates. The public snapshot, surface stamps,
authored surfaces, field shapes, free-text baseline and release history are
unchanged. The guide and app implementation are unchanged; no build or native
execution was needed.

## Verification

Regeneration, `--tree-check` and `--check --require-history` passed. The selected
suite was inspected with `--list`, then executed once from clean `7a411d2b`:

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  PW_TEST_OUT_DIR=tests/out/runs/doc-coalescing-pass4 PW_TEST_QUIET=1 \
  tests/run.sh --suite source_drift
```

Run `20261113T173438Z_7210e427` completed in 420,621 ms in an unsandboxed shell,
using Python 3.14.9 and the selected suite's equipment. All ten cases passed:

```text
source_drift/runner_source_manifests_agree
source_drift/limits_documentation
source_drift/build_contracts
source_drift/architecture_documentation
source_drift/build_documentation
source_drift/generator_contract
source_drift/markdown_reader
source_drift/direct_python_start
source_drift/footprint_documentation
source_drift/porcelain_codec
```

There were no skips, unrun cases, harness errors or recorded system sleep.
The new controls cover all grades, optional source-read qualifications, self
and subtree scopes, multiple owners, compact rows, complete execution metadata
and reciprocal routes for every actual owner. History, source-copy freshness
and document-link checks also passed. These are generator and documentation
observations, not new support for native behavior.

One disposable run and no additional worktree were created. After receipt
review, `make prune` preview and `make prune APPLY=1` removed that run without
blockers, preserving the four release archives and protected acceptance. Raw
output is no longer locally available; these remain development observations.
The final plan/record-only delta changes no generator, public contract, app or
test code; its links and diff formatting were checked separately.

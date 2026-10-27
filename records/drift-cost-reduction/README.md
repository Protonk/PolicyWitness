# Drift cost reduction: implementation records

Purpose: the handoff record for the
[document drift implementation plan](../../tests/suites/source_drift/DOCUMENT-DRIFT-IMPLEMENTATION-PLAN.md).
Its consumer is the reviewer accepting that plan's implementation. Nothing here
is consumed or maintained by tests after the transition; the live contracts
are in `docs/repository_tree.py`, the `source_drift` suite and its README.

Revisions:

- Baseline source revision: `1612eb5e0bd503f0185dda9cda0331be0d9a764f`
  (the investigation revision; the executable sources at the plan's commit
  `6b465f5` are byte-identical to it).
- Candidate source revision: recorded per stage in
  [implementation.md](implementation.md); the final candidate is the revision
  the acceptance review reads.

Files:

- [implementation.md](implementation.md): before/after measurements, credited
  runs, evidence-reuse decisions and remaining limitations, by stage.
- [control-map.json](control-map.json): how each old obligation was preserved.

Control map fields (`rows[]`):

| Field | Meaning |
| --- | --- |
| `old` | The old case/scenario or test/subtest, as `case:scenario` or `file::test`. |
| `obligation` | What the old control established, in one sentence. |
| `disposition` | `retained` (same owner, same mechanism), `moved` (same mechanism, new owner), `consolidated` (repetition transferred to a named reader assertion plus one retained rule-integration representative) or `added` (a control the plan found missing; `old` is null and `rule` names the rule). |
| `destination` | The case that now owns the obligation. |
| `where` | File, symbol and scenario name of the new control. |
| `reader_assertion` | For `consolidated` rows: the independent reader assertion in `markdown.py`. |
| `representative` | For `consolidated` rows: the retained rule-integration scenario. |
| `reason` | Why the disposition preserves the observation. |
| `receipt` | The receipt (run ID and path) that credits the destination. |

Evidence under `tests/out/` is gitignored and available only in the local
checkout where the run executed; the implementation account carries the
numbers a reviewer needs even when that directory is absent.

Retirement: remove this package and the plan together, in one change, once the
implementation review is accepted and the current contracts, control ownership
and receipt formats are documented and checked in their permanent locations.

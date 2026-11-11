# Retention control exit correction

The new `guide_ownership` control expects the wrong status for a completed direct prune apply with blocked paths. Change its expected status from 2 to 1. Production behavior and all ownership/retention assertions stay unchanged.

## Source and account

- `tests/lib/test_cli.py:193–201` invokes `retention.prune`, prints its JSON report, and returns 1 when `report["failures"]` is nonempty. ValueError/OSError use `parser.error` (a refusal, status 2).
- `tests/lib/retention.py:514–543` applies eligible targets, then reports blocked paths as `failures` on apply.
- `tests/lib/retention.py:156–180` reads each actual case's `artifacts/session.json`; `removed` other than true or a nonempty `cleanup_error` blocks the owning run.
- `tests/README.md:305–308` states that blocked paths produce a nonzero apply result and distinguishes invalid requests, unreadable inventories and checkout contention as refusals.
- The earlier `pruning` control at `check_retention.py:255` expects 2 through `make=True`. Make reports a failed recipe differently from the directly invoked dispatcher. The direct redirect control at line 230 already expects 1.

## Retained run observation

Run `20261111T175904Z_4ee0cfa5`, command 78, retained a successful JSON apply report with exit 1 and empty stderr. Its `removed` contains only `tests/out/runs/complete`. The report lists `pending` and `cleanup-error` as cleanup blockers, plus the fixture's pre-existing `kept/link` redirect. The read-only filesystem inspection confirms the complete neighbor is absent, both session files still contain their authored ownership progress, and both effect-observation files contain their original literal payload. Exact report and file observations are in `observation.json`.

The case stopped at the exit-status assertion, so the subsequent full-inventory equality assertions were not executed. Their before inventories existed only in the failed process. This diagnosis does not credit those later assertions as passed; the corrected case must execute them in a fresh run.

## Change and validation scope

One literal changes (`code=2` to `code=1`), in `guide_ownership` only. The preview's explicit blocked rows, completed-neighbor deletion and exact unresolved-run inventory comparisons remain byte-for-byte unchanged. Python syntax was parsed privately. No tests, prune operations, builds, generators or shared-tree writes were executed for this diagnosis.

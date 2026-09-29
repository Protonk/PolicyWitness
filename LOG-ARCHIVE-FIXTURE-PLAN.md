# Isolated archive fixture

Status: Complete. The fixture was generated in an isolated macOS 14.8.7
(23J520) VM on a macOS 26.6.2 (25G83) host and accepted by this checkout's
macOS 14.8.3 (23J220) reader. The query-selection prerequisite in
[BEST-EFFORT-LOG-PLAN.md](BEST-EFFORT-LOG-PLAN.md), sections 2 and 4, is resolved.

## Accepted deliverable

The six-file `tests/fixtures/deny_capture/query_predicate.logarchive` is a real,
self-contained archive. Its independent manifest declares all 26 corpus
messages, 11 selected records for worker 42 and 3 for worker 7. Generation
source, recipe, hashes, reduction and reader provenance are recorded in the
[fixture README](tests/fixtures/deny_capture/README.md). No ambient developer
log store was collected. The generation recipe aborts if the rendered corpus
differs from its declaration.

The required `witness_contract/log_query_predicate_archive` case passes on
14.8.3, including the unfiltered inventory, pre-parser selection multiset and
production parser expectations. `FALSEPREDICATE` and the actual former
bare-PID-digit predicate each fail the pre-parser selection oracle (0 and 20
records respectively, instead of 11); restored production passes.

Local review receipts and mutation outputs are retained under
`/private/tmp/pw-log-archive-review-9b09ad9/review-evidence/` and its associated
`tests/out/runs/archive-review-*` directories. The unchanged merged fixture
also passed in [the main-checkout run](tests/out/runs/archive-fixture-merged-main/run.json).
Permanent tests and fixture documentation do not depend on those receipts or
on either plan file.

## Maintenance boundary

Regeneration remains a one-time maintenance operation in an isolated capture
environment, never default-test setup or a response to an assertion failure.
Declare expectations before emission, inspect all retained content, verify
hashes and reader compatibility, and preserve failed generation receipts.
A default test must not collect an archive, emit new logs, download a fixture,
consult the live store to repair it, or revise expectations to a captured subset.
Missing/unreadable data, blocked access, timeout, overflow, nonzero exit and
wrong/empty selection fail the archive case; none is a live-availability skip.

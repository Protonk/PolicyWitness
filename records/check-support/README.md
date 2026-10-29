# Binding through replay — D1 records

This package belongs to the associated BINDING-THRU-REPLAY-PLAN.md, amended by
WORKSET-PLAN.md. Its consumer is the internal D2 investigation, Checks before
CHECK. It does not prepare a future CHECK writer or implement a proposed
mechanism. Package and owning plan retire after their findings have been
accepted, absorbed/disposed within the workset and still-needed material has
transferred to D2's owned records.

Current behavior at `cf0136bbb6366d5f787c3547ec69d757772898c0`:

- `inventory.md`, `inventory-inputs.json`: bounded entry-point reconciliation,
  declarations, helpers, checkpoints, controls and limits.
- `l-trace.md`, `l-facts.json`: claims/assertions/conditions, source identities
  and fixed retention state.
- `costs.md`, `cost-facts.json`: historical measurements and provenance limits.
- `findings.md`, `host-finding.json`: established discrepancy F1, local diagnostic
  and decision boundary, plus applicability/naming findings.
- `collect.py`: read-only extraction from this fixed checkout and the named raw
  evidence, writing only this package. It is investigation equipment, not a
  new production check or catalog case.

The design, replay register, supplied annotations, results, freeze and
acceptance artifacts will be indexed as their phases complete. Inventories
describe current code; the later design will be explicitly proposed. Raw
tests/out evidence is local and gitignored. Historical replay facts will be
read from named git trees, not inferred from local captures.

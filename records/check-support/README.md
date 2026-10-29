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

Proposed at design version B1:

- `design.md`: explicit relationships, applicability states, checkpoint
  assignment, review ownership, exclusions and cost predictions.
- `replays.md`: open register, annotations, predictions and results pointers;
  `replay/open.py` and `replay/open-results.json`: historical extraction and19
  open evaluations.
- `open-review.md`: reason checks, paired negatives and five-event churn account.
- `freeze.md`: frozen design/annotation policy and curator seal.
- `replay/heldback-cases.json`: unchanged sealed curator dataset, finder
  records, exact revisions, facts, supplied annotations and predictions.
- `heldback-predictions.md`: reveal/exposure account and concrete predictions.
- `replay/heldback.py`, `replay/heldback-results.json`: corrected extraction
  and15 reserved revision evaluations; `heldback-review.md`: coverage and limits.
- `replay/heldback-results-initial.json`, `curator-review.md`: preserved initial
  output, two verification gaps and their correction under unchanged B1.
- `acceptance.md`: self-review, acceptance, unresolved F1, D2 transfer and
  retirement conditions.

Inventories describe current code at the stated fixed source. B1 remains a
paper proposal, with hypothetical historical adoption explicitly labeled.
Raw tests/out evidence is local and gitignored; historical replay facts come
from named git trees, not inferred local captures. Replay scripts write only
their output directory and are not wired into any production checkpoint.

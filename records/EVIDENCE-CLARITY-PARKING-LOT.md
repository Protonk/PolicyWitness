# Evidence clarity parking lot

This record holds proposals that have only been inspected, without
implementation or a dedicated experiment. It does not schedule work.

## P3 — Resume notarization from retained submission evidence

**Current burden.** [notarize.py](../notarize.py) retains the archive and submission
ID, submits once and waits once. An unresolved response stops the release flow;
the operator must inspect the retained evidence before continuing. The
[signing guide](../docs/SIGNING.md) describes manual one-shot status queries;
there is no automated resume path.

**Possible improvement.** Add an explicit resume path keyed by the stored
submission ID and archive digest. Reuse the retained `submitted.zip`, verify its
hash, query the existing submission and continue only after a recognized result
for that same submission. Preserve each observation and establish that later
stapling or packaging uses the corresponding artifact.

**Revisit when.** Recovery can be tested independently from new submission.
Cover incomplete receipts, archive changes, mismatched IDs, unavailable service,
unknown status, rejection and acceptance. Demonstrate that resume neither rebuilds
the artifact nor silently submits it again. Integrate with the existing release
attempt and rotation ownership rules before exposing an operator command.

**Boundary retained.** Apple can remain unavailable or return an unrecognized
state. Such a state still stops continuation. An acceptance for one archive does
not authorize publication of different bytes.

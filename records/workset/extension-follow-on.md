# Matched and crossed extension operations

E1 is accepted at `d2f3bbf`, using signed evidence at `b6cac0d`. The original
read arrangement and the directory read-write arrangement are now established.
This bounded E2 follow-on asks which observed file operations follow consumption
of native `com.apple.app-sandbox.read` and `com.apple.app-sandbox.read-write`
authority. The latter name means read-write, not write-only.

Use the directory fixture's fixed policy, identical initial bytes and modes,
per-boundary names, isolated fresh processes and fresh descriptors. Before each
write attempt, a separate read retrieves the existing file's known initial
bytes. Match reads with read authority and writes with read-write authority;
cross writes with read authority and reads with read-write authority. Separate
existing-file modification and exclusive creation. Repeat no-consumption,
no-predicate and different-directory interventions for both classes. This
extends E1's three such controls to read-only issuance; it does not change the
worker policy between matched and crossed operations.

The ordinary pre-policy baseline establishes access under the same credentials;
the applied pre-consume boundary establishes the fixed policy restriction.
Distinct directories have identical controlled preparation, and no retained
descriptor or prior creation supplies authority for a later boundary. Native
call results, query returns and independent effects remain separate. The
experiment can establish an asymmetry in observed operations without claiming
that all extension classes are symmetric or predicting release behavior.

## Findings

Pending the committed extended matrix and signed run. This follow-on adds no
public capability independently of E2's supported read-write integration.

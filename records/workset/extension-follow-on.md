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

Source `8aa74027e78f0b7ab4c859c1ffa85f2b41a8a288` ran with an empty recorded Git
status in `tests/out/runs/workset-native-crossed-01`, run ID
`20261029T213556Z_990dc5c9`, pinned in `tests/RETAINED.json`. Both canonical native
cases passed: eight directory scenarios and the original eighteen read
scenarios; no skips, unrun cases, harness errors or observed sleep. The command
was the same explicit Developer ID configuration as E1 with this fresh output
path and `tests/run.sh --suite sandbox_extensions_native`.

| Consumed native authority, matching directory and predicates | Read existing contents | Modify existing file | Create absent child |
| --- | --- | --- | --- |
| `com.apple.app-sandbox.read` | Known bytes retrieved | Write open failed | Exclusive write open failed |
| `com.apple.app-sandbox.read-write` | Known bytes retrieved | Truncate/write/close and external contents established | Exclusive creation/write/close and external entry/contents established |

For both classes, no-consume, no-predicate and different-directory controls
refused the read and both write opens after application. All ordinary pre-policy
baselines succeeded. Fresh post-release opens failed in these executions;
the checker permits other recorded outcomes. Completed changes persisted after
release and worker exit. The raw pinned artifact preserves every separate
query, native lifecycle return, syscall, path, identity and independent read-back.

The comparison supports an asymmetry between the selected classes: read-only
consumption did not enable writes, while read-write consumption enabled both
tested directions. This is bounded to these predicates, operations, owned
targets, host and signing conditions. It is not a universal extension taxonomy,
a guarantee of revocation, or prediction/enforcement agreement. The follow-on
is accepted by primary-agent self-review; it introduces no separate public
capability. Public integration and the complete experimental-stage seal remain
outstanding.

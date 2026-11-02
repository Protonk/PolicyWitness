# Apparatus source review

This account records source inspection before the initial native build. It is
not execution evidence. Equipment read-backs and the first planned C0/C1
checkpoint establish the parts that require execution.

## Acquisition and application boundary

The driver creates a fresh mode-0700 trial directory and writes its ownership
receipt. The supervisor creates A and B exclusively, resolves their paths,
records identities and known bytes, and closes creation and baseline-read
descriptors before spawning either child. The exact expanded policies are in
the supervisor's token-free evidence. The fixed clause order and C0–C7 changes
are also checked independently by the reader.

`spawn_role` uses `POSIX_SPAWN_CLOEXEC_DEFAULT`. Its explicit child descriptors
are standard streams opened on `/dev/null`, evidence descriptor 3, one token
mapping descriptor 4, and the checkout-lock lifetime descriptors at 32 and
above. Target descriptors are not passed. The entry snapshot is acquired before
mapping or closing those descriptors; its stored observations are published
after the reporting mapping exists. Mapping descriptors are then closed.

Before application, each child observes its own process/executable identity,
disables core dumps, resolves the required libsandbox functions, records loaded
images, and compiles the policy. Neither child opens, stats or resolves A/B,
issues, consumes, releases, or warms an extension before its application
boundary. C0 compiles C1's policy and omits only the issuer's application. The
recipient's first access follows its application. Every successful target open
has a separate fstat, read and close observation before the next access.

The descriptor snapshots are bounded inventories, with failed enumeration or
identity inspection retained. The reader withholds complete delegation when
the snapshots cannot establish the relevant descriptor identities. Source
inspection does not census private initialization, transient resources or Mach
rights.

## Calls, gates and transient authority

Children publish into fixed shared evidence slots. Each publication is emitted
by the supervisor before acknowledgement. The supervisor records both queries
against the waiting issuer before releasing issuance. It separately records
bounded token publication, transfer framing, recipient acceptance and a
transient byte comparison before releasing the consumption decision. Consume
return `-1`, omitted consumption and unavailable delivery still lead to a
second fresh read when recipient application succeeded.

Tokens occupy two distinct, initially empty shared-memory objects, unlinked
before use, and the issuer's native allocation. The serialized evidence contains
lengths, framing/equality results and erasure observations, never tokens or token
hashes. Native diagnostic strings are not serialized. The issued and delivered
buffers are erased after the final read; the supervisor also erases its views.
The native string's inspected prefix is erased before free. Finding its NUL
does not establish the allocation's full extent. Fatal termination can prevent
erasure; missing publications remain unconfirmed.

`sandbox_check` and the exported no-report integer are dynamically resolved.
There is no literal-flag or unflagged fallback. Only `NONE` and `PATH(A)` are
queried. The reader classifies raw query pairs independently of the producer;
labels do not establish issuance, access or prediction/enforcement agreement.

## Ownership and deadlines

The native deadline is established immediately before the first spawn and is
shared by gate waits and normal reaping. Cleanup allows two additional seconds
per child. Child ownership uses direct ancestry/group membership and recorded
kernel start identities. The driver records launches and NDJSON incrementally,
sets a separate 30-second outer deadline and bounds group cleanup to five
seconds. It checks process-group absence independently of supervisor reaping.

Before signaling a surviving group, the driver checks current membership and
recorded identities. Before removing A/B and the directory, it checks the owned
directory receipt and identities. Unconfirmed process absence, changed resource
identity or pending native channel cleanup retains the paths and blocks further
execution. Python launchers explicitly pass checkout-lock descriptors onward.

## Independent reader controls

The final prebuild [constructed-control run](evidence/controls/constructed-02/summary.json)
passed all 26 scenarios through the locked driver. Its source snapshots, inputs and reader
commands/read-backs are retained alongside the summary. They cover broken
application/transfer links, inherited or retained target descriptors, reuse of
a closed descriptor number, unsupported known-byte claims, query classification,
honest native failures, missing dependent observations and cleanup uncertainty.
The earlier [24-control run](evidence/controls/constructed-01/summary.json) is
retained. The final run adds controls for distinct shared-memory creations with
nonunique stat metadata and for repeated creation identities. Channel separation
uses exclusive creation names and explicit descriptors; shared-memory stat
metadata is a consistency observation, not an assumed unique object identifier.
These runs establish reader behavior on constructed inputs only. A control derived
from an accepted real trial is still required if such a sequence is observed.

The source review included independent native and driver/reader reviews. It
found and corrected issues before native execution involving empty descriptor
enumeration, diagnostic-errno equality, allocation-extent wording, wait/reap
ordering, and durable ownership on cleanup failures. No native trial was added
for these corrections.

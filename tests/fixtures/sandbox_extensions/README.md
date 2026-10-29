# Native sandbox extension fixture

`native.c` is standalone test equipment. It uses no production PW request,
shared-memory layout, result classifier or phase implementation. `build.sh`
compiles it; the owning suite signs it and reads back the signature and empty
entitlements before execution. The host, issuer and worker exec that binary as
separate processes.

The host creates distinct unlinked shared-memory objects for evidence and token
bytes. Only mapping descriptors and standard streams opened on `/dev/null` reach
the children. The worker inventories inherited descriptors before opening the
target, and closes each fresh descriptor unless the retained-descriptor control
explicitly holds it. Issuer token storage is erased before freeing, the worker
erases the token channel after the consume decision, and the host erases the
channel on cleanup. A transient host copy checks the serialized report for the
issued token before publication and is then erased. Core dumps are disabled.
This does not claim protection against privileged memory inspection or OS swap.

The worker applies one fixed policy and pauses at fixed test boundaries. The
host calls the native query against its owned worker before releasing each
boundary. The first access is a pre-policy baseline; subsequent accesses follow
their boundary's query. The issuer either remains held through the experiment
or is reaped before the first release. No query-answer pattern is assumed.

Native call errno snapshots follow explicit zeroing. They are diagnostic on
successful calls, not independent failures. An open/read/fstat/close errno is
meaningful only when its own attempted call returns failure. Unattempted call
fields and unsuccessful fstat identity storage have no observational meaning.
The consume result is signed 64-bit; -1 means no obtained handle. A returned
release result is not evidence of access revocation.

Optional malloc and VM loggers count callbacks from any thread while a native
consume/release call is bracketed. Positive allocation controls execute before application and after the experiment. Descriptor counts
sample the boundaries around native calls. Neither zero counters nor unchanged
descriptor counts establish absence of transient resources, uninstrumented
allocation paths or kernel resources. No extension call is made before application to warm it up.

The fixture's bounds live in its C definitions; they are experiment limits, not
new product admission limits. Native failures and cleanup results remain in the
raw report. The suite's checker, not the fixture, decides acceptance.

Directory scenarios issue `com.apple.app-sandbox.read-write` (or the read-only
control) for an owned directory. Distinct existing files and absent child names
serve the four boundaries. Issuance completes before the first attempt; the
issuer, host and worker independently record child absence before issuance,
before releasing the boundary and immediately before exclusive creation.
Existing-file writes use a fresh write-only open followed by explicit truncation,
write and close. Each call and descriptor size is separate. The host snapshots
completed effects, all targets after release while the worker is paused, and
all targets after worker exit. No file descriptor is retained between attempts.
Read and write queries use the existing file; the absent child has an explicit
unavailable prediction. Persistence means observed contents and directory entries,
not crash durability. These operations do not define production file actions.

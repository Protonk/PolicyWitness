# Directory read-write native experiment

E1 begins from `093eba3`, production-identical to intake. The existing native
file-read experiment passed as `sandbox_extensions_native/feasibility` in
`tests/out/runs/workset-native-baseline-01` with the explicit Developer ID
identity recorded in intake. This is local gitignored evidence. It establishes
the existing equipment on this host, not directory write feasibility.

## Proposed apparatus and acceptance

Extend the existing independent signed fixture with directory scenarios. Keep
its separate exec'd host, issuer and worker, transient token transport, child
cleanup, explicit signing read-back and once-applied worker policy. Production
request, ABI and classification code remain outside this experiment.

Use native `com.apple.app-sandbox.read-write`, flags zero, for an owned resolved
directory. The fixed policy denies data reads and file writes, then permits
data reads through the read and read-write extension predicates and writes
through the read-write predicate. The omission control removes these predicates.
Use no-consume, different-directory and native read-only issuance controls.

Four boundaries use distinct existing files and initially absent child names:
ordinary pre-policy access, applied policy before consumption, after consumption,
and after release. Issuance completes before any boundary is released. Record
child absence in the issuer before issuance, in the host before each attempt,
and in the worker immediately before exclusive creation. Separate write-only
open, descriptor identity, explicit truncation, transferred bytes, final size
and close. The child uses exclusive creation; the existing file uses a fresh
nontruncating open followed by explicit truncation. These fixture operations do
not redefine public `open_write` or `create`.

The host reads completed attempts independently and snapshots all files after
release while the worker is paused, then after reaping it. Record bytes and
directory entries, not crash durability. Query the live worker using each
resolvable existing file. The absent child has no ordinary planned prediction;
retain that absence rather than synthesizing deny. Native lifecycle and query
results remain distinct from file effects; post-release access has no required
allow/deny pattern.

The ordinary baseline must establish DAC and apparatus capability. The positive
read-write treatment must establish both modification and new-child creation;
the negative controls must preserve their denied-operation observations and
unchanged external contents/absence. Checker controls must reject lost absence,
identity, truncation, write, close, persistence, ordering, ownership or token
confinement evidence, while accepting observed query and release variations.
If the premise fails, retain that result and investigate; do not substitute a
broader issuer. E2 and the crossed-operation interpretation follow E1 findings.

## Findings

Candidate `3ce5d8f` ran in `workset-native-directory-01`. The original read
feasibility case passed. The directory case failed in the new checker: it
incorrectly required the child file's group to equal the worker's primary group.
The fixture recorded the ordinary UID/GID for both processes, owner-only file
mode, and matching file identity across observations; equating file GID with
process GID is unnecessary for this claim. Preserve the actual file GID and
compare it across observations instead. This is an E1 apparatus correction,
not a change to an existing product promise.

All five raw native rows completed, with the read-write treatment opening both
write targets after consumption and the four controls refusing those opens.
Do not credit this failed run as the completed experiment: Python's final
read-back was placed after assertions and was lost on failure. Reviewer
`review_directory_native` independently identified this retention gap. Move
preparation capture before launch and final filesystem capture into an
unconditional path before validation and cleanup; retain assertion tracebacks.
Rerun the full native selection from the corrected committed candidate.

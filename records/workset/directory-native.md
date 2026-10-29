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

## Accepted E1 result

Tested source: `b6cac0d735f0384fc50d94a6eba6ab18e9323763`, with empty recorded
Git status. Run `workset-native-directory-02`, ID
`20261029T213006Z_421d1954`, completed both canonical native cases, two passes,
no skips, unrun cases, harness errors or observed system sleep. Invocation:

```sh
IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' PW_TEST_OUT_DIR=tests/out/runs/workset-native-directory-02 tests/run.sh --suite sandbox_extensions_native
```

The directory binary SHA-256 is
`5baec48fd76cdb9b4981ecb9c916b6f8a63f36b9dcf4152a6c327d2f037ef651`.
Its signature read-back has TeamIdentifier `42D369QV8E`, hardened runtime,
secure timestamp, no entitlements and strict verification success. All three
roles exec that signed binary. Host macOS is 26.7.1 (`25G241`), arm64, SDK 27.0;
issuer and worker UID/EUID 501, GID/EGID 20. These are ordinary caller credentials.
No production app participates. Exact compiler, native paths, policy, metadata,
commands and sources remain in the pinned local run's artifacts; hashes do not
make those gitignored bytes portable.

| Arrangement | Before consume: existing / child | During: existing / child | Fresh after release: existing / child |
| --- | --- | --- | --- |
| Directory read-write | open failed / open failed | modified / created | open failed / open failed |
| No consumption | open failed / open failed | open failed / open failed | open failed / open failed |
| No extension predicates | open failed / open failed | open failed / open failed | open failed / open failed |
| Other directory | open failed / open failed | open failed / open failed | open failed / open failed |
| Native read-only | open failed / open failed | open failed / open failed | open failed / open failed |

Every pre-policy baseline modified and created successfully. Every credited
creation had ENOENT observations before issuance and immediately before its own
exclusive open, and distinct names prevent reuse. The positive treatment's
existing-file open preserved initial size and identity, explicit truncation
returned zero with size zero, write transferred all 20 bytes of
`PW directory effect\n`, and close returned zero. Its new child was empty at
exclusive open, received the same 20 bytes and closed successfully. The host
read these exact bytes after release and after worker exit; Python independently
confirmed the final identities, bytes and directory entries. Failed attempts
left initial existing contents or an absent child, separately observed.

Issued tokens were nonnull, successful consume handles were 1, release results
were 0; no-consume omitted both calls. Both children were reaped with zero exit
status, one policy application was recorded, inherited target descriptors were
absent, and token erasure/publication checks passed. Native lifecycle success
alone is not the access evidence. Observed existing-file write queries were
`[0,1,0,1]` for the positive treatment and `[0,1,1,1]` for controls. These are
retained query observations, not prediction/enforcement agreement or a required
future pattern. Absent-child predictions stayed unavailable. Data reads were
also recorded; their matched/crossed interpretation belongs to E2's bounded
follow-on.

All 18 original plain/instrumented read scenarios still passed. The new checker
rejected 18 independently perturbed evidence omissions/contradictions and
accepted eight reference/variation controls, including successful fresh access,
partial write, failed truncation/read, unavailable queries and failed release.
Source review by `review_directory_native` found the failed-run retention gap
and missing variation controls; both were corrected before the accepted run.
Final acceptance is the primary agent's self-review against E1's requirements.

`workset-native-structure-01` passed
`source_drift/runner_source_manifests_agree` and
`source_drift/generator_contract`. It started at `b6cac0d`; only this findings
record's prose evolved during execution. Review of that delta found no changed
links, production, fixture, checker or catalog inputs. This is an explicit
applicability judgment, not a claim that Git status stayed empty in that run.
Both the native and structure runs are pinned in `tests/RETAINED.json`.

**Disposition:** directory-scoped read-write feasibility is supported under the
recorded conditions. Proceed to the smallest coherent public addition and the
bounded crossed follow-on. This does not establish privileged issuance, general
revocation guarantees, crash durability, XPC/BYOXPC integration or portable
behavior across hosts. The full experimental stage is not sealed until E2.

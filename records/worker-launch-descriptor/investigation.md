# Launch descriptor lifetime investigation

Baseline: `503156f0693dd8a22acf633efccdc93e300f2ebc` (2026-10-18).
Associated plan: [launch descriptor ownership](../../runner/Sources/PWRunnerCore/LAUNCH-DESCRIPTOR-LIFETIME-PLAN.md).
State: ready for the ownership design decision. Native prototype experiments
and source review are complete. This record recommends a choice; no production
ownership change has been adopted or implemented.

## Source trace and candidate boundary

`runCWorker` [creates and maps the object](../../runner/Sources/PWRunnerCore/CWorker.swift)
with writable access, clears its close-on-exec flag and defers descriptor close
with mapping teardown. The only subsequent descriptor use is the worker spawn
file action delivering fd 3. Every later publication read, release store, final
snapshot and decoder uses the retained mapping. There is no post-spawn remap,
truncate, duplicate or descriptor-based evidence read.

The worker [spawn actions](../../runner/Sources/PWRunnerCore/CWorker.swift)
install policy input at 0, evidence at 3 and readiness at 4. A supplied extension
uses its own high close-on-exec duplicate and fd 5. All worker file actions have
completed before a successful `posix_spawn` return. Parent descriptor closure
therefore cannot undo the child's installed descriptor. The parent mapping has
a separate lifetime from the descriptor.

The phase hook invokes `runValidator` while `runCWorker` still owns the original
host descriptor. [Native validator spawn](../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
uses nil spawn attributes and only standard-input/output file actions. Nothing
in that launch excludes the evidence descriptor. The shipped validator performs
no descriptor sweep. This establishes a route for inheritance; the native
experiment below must distinguish receiving the same object from receiving
merely similar metadata or bytes.

## Proposed narrow choice

Close the host's evidence descriptor immediately after successful worker spawn,
before policy delivery, while retaining its mapping through the current final
snapshot and teardown. Represent descriptor ownership explicitly so that deferred
cleanup cannot close the released descriptor number after reuse. Pre-spawn
failures retain their close/unmap ownership. A native spawn refusal returns
through that cleanup without executing a success-only close.

Retain the current pre-spawn close-on-exec clearing and worker file actions in
this change. Restoring close-on-exec after spawn would prevent this validator
inheritance too, but preserves a descriptor the host no longer needs and adds a
new checked flag-setting failure after child creation. An explicit child
allowlist is a broader inheritance policy affecting ambient references and
other launch endpoints; it is not required to remove this particular reference.

This boundary does not remove original-number aliases already inherited by the
worker. It does not resolve low-number source/destination collisions, change
extension delivery, move native extension erasure/release, or establish that an
ordinary validator ever altered ordering or evidence. Those are separate claims.

## Experiment and evidence

The native experiment supports closing the host descriptor after successful
spawn with explicit close-once ownership. Baseline runs proved writable access
to the same evidence object. Both candidate lifetimes withheld it from the
validator. The close candidate retained the usable host mapping and avoided a
real deferred-close/reused-number error.

The final command was:

```sh
tests/lib/checkout_lock.sh -- python3 records/worker-launch-descriptor/equipment/run.py /private/tmp/pw-launch-descriptor-20261018-r3
```

It ran outside the automation sandbox on Darwin 25.6.0 / arm64. The copied core
uses baseline sources with the explicit transformations in
[native-runs/r3/transformations.json](native-runs/r3/transformations.json).
The shipped worker remained byte-identical before and after (SHA-256
`4fbcb109af574da3966f7a5c0ef2bf4653ae8cbfc0be642de5771b3eb582f6a0`). Its
worker identity is
`4dd8d75126025defa7b9719fb434d265b69f25b9d3bd6d9fd3836d1321f02976`.
The built copied core and observer hashes, kernel description and complete source
hash manifest are retained beside [results.json](native-runs/r3/results.json).
This is a constructed-core/observer experiment, not acceptance of a rebuilt
production refactor.

| Prototype | Arrangements | Native result |
| --- | --- | --- |
| Original lifetime | High fd 16, self-dup fd 3, synthetic extension fd 5 delivery | Validator writes reached the host evidence mapping at original host fds 16, 3 and 17 respectively. |
| Close after successful spawn, invalidate owner | Same three arrangements | No validator challenge reached the evidence mapping; decoy writes succeeded; mapping still supported release, acknowledgement, done and confirmed clean reap. Exact original fd reuse survived driver return. |
| Restore close-on-exec after successful spawn | Same three arrangements | No validator challenge reached the evidence mapping; decoy writes succeeded; worker protocol completed; descriptor closed at ordinary driver teardown. |
| All three lifetimes | Native worker spawn refusal (`ENOENT`) | No worker or validator was reported; one successful original descriptor close; no descriptor remaining. |
| Naive close retaining old deferred owner | High fd 16 | Validator inheritance disappeared, but deferred close closed the independently opened `/dev/null` sentinel that reused fd 16. |
| Omit the original close-on-exec clear | Self-dup fd 3 | Worker-entry observer had no fd 3; the real worker exited 3 without applied/done, was reaped and independently confirmed unavailable to wait. |

These are fourteen native scenarios. Six independent altered-receipt controls
were rejected for missing positive decoy writes, confusing decoy with evidence,
missing write authority, closing the reuse sentinel, failing to establish exact
reuse, and losing worker evidence delivery. The fourteen case labels describe
characterizations: passing the naive-close case means the fault was observed,
not that its ownership is acceptable.

In the baseline, the evidence and decoy had identical access mode, device,
inode, mode and rounded size (`O_RDWR`, device 0, inode 0, mode 0600,
3,686,400 bytes). The original and decoy mappings nevertheless observed only
their own descriptor's challenge. This is the observation that forecloses using
stat/header similarity as an object-identity oracle. The high-fd worker entry
retained both fd 3 and the original-number candidate; the close candidate did
not change that child table. Worker endpoint identity at fd 3 is additionally
supported by its actual publications reaching the host. The original-number
alias identification also relies on the unchanged spawn action/source trace;
this equipment does not write a separate worker-entry alias challenge.

The fd 5 control delivers a distinct read-only descriptor for the observer
executable through the existing high duplicate. `extensionRequested` remains
false. It pins the delivery endpoint separately from the evidence reference;
it is not native token issuance or consumption evidence.

Equipment is retained in [equipment/](equipment/):

- The observer records every incoming fd in its bounded 0–255 scan before
  acquiring an output file, preserving every incoming descriptor. It retains
  access mode, close-on-exec flags and stat metadata. Its worker role then execs
  the unchanged signed worker in the same PID.
- The validator role maps candidate objects read/write and writes a fresh
  per-descriptor challenge into distinct cells in unused slot 255. Every test
  has zero submitted slots; these cells cannot overlap header, used actions,
  parameters, compiled-profile capture or worker diagnostic storage.
- Host instrumentation reads those cells from the original mapping after the
  validator is reaped. That cross-process readback, rather than stat metadata,
  header resemblance, size or descriptor number, identifies the shared object.
- A separate same-sized shared-memory object is copied byte-for-byte from the
  original immediately before validator launch. Its independent mapped readback
  must observe the validator's write, while the original mapping must remain
  unchanged at that cell. Absence of the true reference cannot pass if the
  observer failed to discover or write the decoy.
- The copied production core compares the original lifetime, close with owner
  invalidation, and close-on-exec restoration. A naive close retaining the old
  deferred owner intentionally closes an independently opened sentinel that has
  reused the exact descriptor number; the corrected owner must preserve it.

Native cases use a fresh process group, a durable `child-owner.json`, a bounded
worker watchdog, independently confirmed host reap (`waitpid` returns
`ECHILD`), and a read-only group inventory after the owning host is reaped. Every
final-run inventory was empty; no timeout, signal fallback or recovery was
needed. [independent-review.json](native-runs/r3/independent-review.json)
checks the worker/validator receipt PID chains against actual driver PIDs and
owner records, and confirms the identical decoy metadata in each baseline.

The first attempt stopped at observer compilation because `<stdatomic.h>` was
missing; no scenario launched. The second completed the three baseline launch
arrangements and native spawn refusal, then stopped because the checker expected
an enum case spelling instead of the driver's `posix_spawn:` diagnostic. Its
original facts remain passing observations rather than an overall successful
run. Before the third attempt, post-reap numeric-group signaling was removed
from equipment: group ownership after leader reap was not established. All
recorded earlier inventories were empty and no such group signal actually
occurred. Exact sources, command status, diagnostics and raw receipts for all
three attempts are preserved under [native-runs/](native-runs/). Repeated exact
source snapshots are stored by hash in [snapshots/](snapshots/), with per-attempt
indexes. Large copied Swift packages and binaries remain only in the named
`/private/tmp` directories; they are local and may disappear. The essential
observations and source transformations do not depend on their retention.

The controlled core directly runs the production worker and validator drivers;
it is not a shipped XPC-host inventory. The observer substitutes for the
validator executable and does not invoke `sandbox_check`. These observations
cannot establish a native validator write to an active protocol field or an
actual violation of collection/release ordering.

## Existing constraints and acceptance needed for a refactor

The fresh shared baseline selected by the coordinator includes
`runner_unit/host_setup_controls`: run `20261018T192430Z_884b74f5`,
`tests/out/runs/worker-followup-baseline-20261018` (local, gitignored evidence).
Its receipt snapshots and independent endpoint observations should be retained
as constraints, not relabeled as the new ownership control.

The fresh setup-control receipts confirm the current closed-stdin worker
collision: the policy `dup2` can overwrite an evidence source allocated at fd 0
before the evidence `dup2` runs. They also show unchecked action-add failures
can lead to wrong child endpoints, while the existing high extension duplicate
protects its source from 3/4/5 destination collisions. Closing the parent's
launch descriptor later fixes none of those earlier child-table decisions.
Preserve them as known constraints rather than broadening this ownership repair.

The earliest source branches (`ftruncate`/`mmap` refusals) already close directly;
post-map/pre-spawn pipe, extension-duplication and native-spawn failures use the
deferred close. The prototype changed the success lifetime and verified a real
spawn refusal, but did not inject every earlier setup failure against the new
owner. A selected refactor should do that targeted cleanup review and retain
or strengthen the existing controls. No close-error injection was run; the
prototype retains the production driver's existing close-error handling rather
than claiming new guarantees for a failed native close. Relinquish ownership
before any later code can reuse the number, and do not retry a close through a
stale numeric owner.

A production refactor should retain these distinguishable controls:

1. A positive original-lifetime inheritance control and an independent writable
   decoy; the repaired lifetime must withhold the true object while the decoy
   remains observable.
2. Exact descriptor-number reuse, proving successful-spawn cleanup relinquishes
   ownership before the old deferred cleanup could close a later owner.
3. Native spawn refusal and earlier setup failures, requiring original cleanup
   ownership exactly once and no process fabricated from a failed spawn.
4. Low-number self-duplication, high original-number worker aliases and extension
   fd 5 delivery as separate endpoint checks. Do not silently claim the current
   closed-stdin collision has been repaired by shortening the host lifetime.
5. The existing runner integration, ABI identity, native extension, worker
   terminal/publication and ordering controls after a signed build. The mapping
   must remain usable for collection, release, acknowledgement reconciliation
   and final decoding until existing teardown.

## Primary native references

Apple's [mmap manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/mmap.2.html)
and [posix_spawn manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/posix_spawn.2.html)
provide the mapping lifetime and launch-action model. They are archived API
references; the native controls establish behavior on the tested machine.
Apple's published [POSIX shared-memory implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/posix_shm.c)
zero-initializes stat output and fills only a subset of fields. Its `pshm_stat`
implementation supports rejecting generic inode/device equality as this
object-identity oracle. The fetched `main` source is explanatory evidence, not
an identification of the exact running kernel revision.

## Decision for the coordinator

Adopt the narrow close-after-successful-spawn boundary with explicit close-once
ownership and the existing mapping teardown. This removes an observed writable
reference at its source, including from every later phase validator, without a
new child-descriptor policy. Keep the transfer deadline's existing start point
and sequence the close before later child launches; do not accidentally move
policy transfer or phase waits outside their existing accounting. Keep the
pre-spawn clear because the self-dup observation establishes its current native
purpose. Revisit that clear only together with a separately designed collision-
safe source/destination strategy.

No new wire field or classifier is implicated. A production Swift source change
still requires normal worker-identity regeneration and signed-build validation.
The exec supervisor can proceed on the assumption that the host no longer needs
the evidence descriptor after worker creation if this choice is adopted; the
worker's own inherited descriptors and exec-child allowlist remain its separate
launch contract.

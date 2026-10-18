# Investigate terminal publication, exit and cleanup

[Parent and handoff scope](../../../WORKER-REDESIGN-PLAN.md).
Findings: WA-04 and WA-08 in the
[initial audit](../../../records/worker-pass6/initial-report.md).
State: drafted; investigation unassigned.

## Starting point

In [pw_probe_runner.c](pw_probe_runner.c), `spin_for_exit` waits indefinitely
for `exit_requested` after terminal publication. The host retains its own
mapping and takes a final acquired snapshot after cleanup in
[CWorker.swift](../../../runner/Sources/PWRunnerCore/CWorker.swift).
Its polling logic also assumes that normal completion leaves the worker alive.

Consider `publish terminal result -> exit` as an alternative to the handshake.
At the same boundary, examine a common terminal routine owning ordinary token
cleanup. `prepare_extension` precedes several header, timing and policy
refusals; those returns bypass the final loop erase. `attempt_extension` has
its own erasure site, and [ExtensionIssuer.swift](../../../runner/Sources/PWRunnerCore/ExtensionIssuer.swift)
owns separate host erasure. Register row 14 records the accepted current scope.

The orphan observed by the auditor was a different build. It has since been
terminated, as recorded in the [handoff context](../../../records/worker-pass6/handoff-context.md).
Its exact instruction location and the cause of host loss remain unestablished.

## Questions that distinguish the designs

- What requires the worker to remain alive after terminal publication? Trace
  compilation failure, proceed refusal and normal completion through polling,
  reap, final snapshots and disposition. Examine publication between the host's
  last `done` read and its reap observation. Preserve actual deadline/stop facts
  even when later publications are retained.
- Could a terminal routine preserve each failure's publication and exit meaning
  while erasing a valid accepted channel on ordinary paths? Compare moving
  token preparation later with transferring bytes into worker-private storage.
  Account for changed failure order, extra copies and partial initialization.
- Which guarantees remain dependent on native exit or host supervision? Separate
  post-done waiting from native-call stalls, fatal termination and descendant
  survival. Investigate parent-loss detection or a watchdog only against a
  specific remaining need and its post-apply resource/syscall cost.

[CWorkerLifecycleTests.swift](../../../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift),
[PhaseProtocolTests.swift](../../../runner/Tests/PWRunnerCoreTests/PhaseProtocolTests.swift)
and the [worker evidence contract](../../../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract)
locate relevant races and readers. Extension boundary controls cover delivery
and erasure observations. Any host-loss experiment needs cleanup ownership
independent of the host being removed; reuse existing session records first
when investigating the historical orphan.

## Outcome to bring back

Return the terminal-state model, the assumptions it removes, and the effects on
ordering, failure evidence, token lifetime and disposition. Distinguish changes
that belong together from independently useful cleanup. Name the decisive
remaining experiments and regression controls; a rename of `done` alone does
not resolve the lifecycle question.

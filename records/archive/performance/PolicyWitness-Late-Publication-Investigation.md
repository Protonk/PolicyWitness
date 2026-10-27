# PolicyWitness: Late Publication During Worker Exit Grace

## Question

Determine what PolicyWitness retains when the **host's worker-publication wait expires while a released worker is still performing an attempt**. In particular, establish whether the worker can finish and publish evidence during the host's exit grace, and distinguish that from evidence published before the deadline but read during cleanup.

The preceding phase-barrier investigation exercised the opposite ordering: the *worker's* proceed deadline expired while the host remained in its collection callback. This investigation concerns the *host's* sentinel deadline after a successful phase release. Keep those cases distinct.

This is a bounded runtime investigation, not an optimization or change proposal.

## Preparation and scope

Read the recent phase-barrier report and the existing worker/driver lifecycle controls. Verify the current checkout and the relevant code in `runner/Sources/PWRunnerCore/CWorker.swift` and `controller/tools/pw_probe_runner/pw_probe_runner.c` before constructing the experiment.

Use the shipped worker binary and the existing `runCWorker` internal test seam where practical. Keep production application code, worker instructions, response schema and timeouts unchanged. Local test equipment and narrowly scoped instrumentation are permitted; record exactly what differs from production. Use a harmless, owned specimen and bounded delays. No external runner or log observer is needed.

Avoid a client RPC timeout: the event under investigation is the **host's sentinel expiry**, followed by its exit grace and final evidence snapshot.

## Controlled cases

Establish a small set of runs that separates these cases:

1. **Timely completion.** Release the worker, complete its attempt, publish the slot and `done`, and exit before the host's sentinel deadline.
2. **Late terminal publication, not a late slot.** Complete and publish the attempt slot before the sentinel deadline, but delay `done` until during exit grace. The existing `postApplyHangMs`/`worker_post_apply_hang_ms` seam may serve this purpose: verify that it runs *after* slot completion.
3. **Late attempt publication.** Ensure that the worker has acknowledged release and entered an attempt before the host's sentinel deadline, but that the native attempt finishes and its slot becomes complete **after** sentinel expiry and **before** grace exhaustion. Use a controllable, bounded operation (for example, an owned blocking file operation or an existing controlled exec helper), with independent evidence of when that operation unblocked or finished. Do not assume that a final completed flag alone dates its publication.
4. **Grace exhaustion.** Keep the comparable attempt unfinished past the host's exit grace and observe termination, reaping, any retained partial evidence and cleanup. Avoid or explicitly supervise any descendant processes or blocked helpers; nothing may remain running after the test.

Choose timings with clear margins between the relevant events. A few repetitions per case are enough if ordering is actually observed. Do not add a large timing sweep merely to increase the sample count. If a case cannot be produced reliably, report that fact instead of treating a different execution as the intended case.

## Record

For each run, preserve the request/input, actual hold or attempt timing, process identities, and the raw driver reply. Record, to the extent independently observable:

- Release and acknowledgement, and evidence that the attempt was in progress before host expiry.
- Host sentinel stop reason and elapsed time; the point at which `exit_requested` was stored.
- Native attempt completion or independent external effect; slot `completed` publication; `done` publication.
- Grace entry and stop reason, termination request, worker exit/reap, and final snapshot collection basis.
- Resulting attempt fields, missing reasons, worker failure/progress fields, and overall outcome.

Separate timestamped observations from facts inferred only from final flags. If publication instants cannot be directly observed, state the ordering bounds that the available evidence supports. Preserve the distinction between a native return, a completed slot, a `done` flag, and a host-observed timely completion.

Use existing lifecycle and failure-propagation tests as references, not as substitutes for live observations. Retain raw evidence locally and provide reproducible analysis and bounded cleanup as in the preceding investigation.

## Report

Explain which of the four conditions were actually reached, with the relevant event order and representative raw fields. State whether the host's grace can recover a **newly completed attempt slot**, merely preserve an **already published slot**, both, or neither in the observed cases. Note what the worker's cancellation flag can and cannot interrupt once an attempt is in progress.

Identify any mismatch between the observed behavior and the current lifecycle documentation, and distinguish it from an error in the application.

Stop after this question is answered to the extent the available test seam permits. Do not implement a shorter grace, new cancellation mechanism, synchronization change, or revised output contract. Offer no optimization proposal in the report.

# PolicyWitness: Phase Barrier Under Delayed Collection

## Question

Determine what the sandboxed worker does, and what it costs, between publishing phase arrival and receiving the host's release. Establish separately what happens when the worker's own proceed deadline expires before the host finishes its collection interval.

This investigates the current implementation. Do not replace the spin loop, add a sleeping wait, or propose a synchronization redesign in this pass.

## Scope

Use the current checkout and built artifacts. Verify that the behavior described here still matches the source before proceeding:

- The worker's `wait_for_proceed` loop publishes arrival, checks its continuous-time allowance, polls the release ordinal and exit request, and uses `cpu_relax` while waiting.
- The host's `runCWorker` phase-boundary callback runs after observed arrival and before the release store. The host excludes that callback's synchronous time from its sentinel allowance.
- The worker has its own proceed-wait allowance, distinct from the host's collection and sentinel allowances.

The relevant starting points are `controller/tools/pw_probe_runner/pw_probe_runner.c`, `runner/Sources/PWRunnerCore/CWorker.swift`, and the existing `PhaseProtocolTests` and worker clock controls. Inspect the current implementation rather than trusting historical line numbers.

Do not reopen the log-observer or host-lifetime investigations. Do not change production worker code, the applied policy procedure, the shared-memory protocol, or public output contracts. A small measurement fixture using an existing internal driver seam is acceptable. Keep all new code and raw measurements clearly separate from shipped application code.

## Experiment

1. **Establish a normal control.** Run a simple phase with the current production C worker and its normal compile-and-apply path. Retain the phase publications, attempt and query-related records where applicable, worker/host identities, and child cleanup outcome. Confirm that the phase is acknowledged and completed normally.

2. **Hold the host-side phase boundary deliberately.** Use the existing `phaseBoundary` callback, or another established internal seam with the same ordering, to add bounded holds of different lengths (for example, approximately 200 and 800 ms). The worker must remain unmodified and sandboxed throughout. Confirm that the attempted action cannot begin before the release store and acknowledgement. Do not treat a held callback as an actual validator observation; identify it as a controlled substitute for collection time.

3. **Measure worker resource consumption during the hold.** Obtain worker-specific user/system CPU time, preferably through external kernel process accounting, with a process-generation identity check rather than PID alone. Measure elapsed hold time and, if possible, the CPU-time increment between arrival and release. Account for the possibility that sampling misses short-lived processes or disturbs scheduling. Keep the timing of the measurement itself visible. Do not attribute host or controller CPU use to the worker.

4. **Cross the worker's own proceed deadline once under a bounded control.** Use the supported test-only proceed-wait allowance to make it shorter than a deliberately held host callback (for example, a 250 ms worker allowance and a 400 ms hold). Observe whether the worker publishes a proceed-timeout failure and terminates before release; whether the host still considers collection closed; whether it withholds release when the child is no longer eligible; and which publications and cleanup facts survive. Keep this distinct from a client RPC timeout or the host's sentinel deadline.

5. **Check measurement interference.** Include a small set of equivalent runs without continuous process polling, or with much less polling, so that a measured CPU or timing effect is not silently assigned to the worker when it may arise from the measurement apparatus. If a direct measurement of worker CPU time is not feasible, record the limitation rather than substituting aggregate machine CPU usage as though it were equivalent.

Choose modest repetition counts to establish whether the observations are repeatable. Record each actual hold duration and the order in which conditions ran. Do not use long hangs or unbounded waits to amplify the effect. Use existing bounded cleanup and verify that all owned processes have terminated.

## Record and interpret

For each condition, retain the actual worker identity, timing endpoints and their observers, worker CPU observations and their coverage, phase arrival/release/acknowledgement/completion, worker failure or success, and final reap/disposition. Preserve raw results and failures, including cases where the expected phase transition never occurs.

Distinguish four events explicitly:

- worker publishes **arrival**;
- host finishes the controlled **collection interval**;
- host publishes **release**;
- worker acknowledges release or **refuses/exits** under its own deadline.

Do not infer one event's time merely from a later event's time. In particular, a host's exclusion of callback time from the sentinel budget does not mean the worker's proceed-wait clock excludes it.

Report what fraction of a held interval, if any, appears as worker CPU consumption; whether observations change between ordinary and deliberately held cases; and what happens in the deadline-crossing case. Separate directly observed effects from explanations about scheduling, CPU frequency, and interference with other processes.

The deliverable is a short runtime findings report with source references, measurement definitions, results, limitations, and unresolved questions. **Do not finish with an optimization plan.**

# PolicyWitness Runtime Performance Exploration

## Purpose

Investigate the runtime performance of PolicyWitness in its ordinary work. This is an empirical investigation, not an optimization assignment. The immediate deliverables are a credible account of what was measured, a reproducible measurement procedure, and findings that can support later decisions. Do not change the application's behavior in pursuit of a speedup during this investigation.

The work has two execution settings: interactive exploration with an agent present, followed by measurements launched by the human operator **with no agent sessions active**. This staging is a practical way to limit investigator interference; it is not presumed to be intrinsically more accurate.

A previous source-reading exercise established that PW has several consequential boundaries that need not coincide. In this investigation, determine the boundaries relevant to each measurement from the current implementation. Do not assume that an invocation's return, an experiment's completion, the end of evidence collection, resource retirement, and final output preparation are the same event. Equally, do not assume they should be made the same event.

## Working constraints

- Establish the current repository state and the identity of the actual executable before drawing conclusions. Documentation and prior reports may describe earlier revisions.
- The requirement for a fresh sandboxed worker, sandbox compilation, and sandbox application for each specimen remains in force. Do not treat reuse of that worker or skipping those actions as an optimization candidate.
- Keep measurements of the existing application distinct from measurements of any instrumented or otherwise modified build. Do not modify PW's runtime code, sandbox profiles, execution semantics, or result schema as part of baseline measurement. If additional instrumentation appears necessary, explain what existing evidence cannot establish before pursuing it, and obtain separate approval for an instrumented variant.
- Preserve raw outputs, failure and refusal outcomes, timing provenance, and the conditions under which runs were made. Do not quietly exclude inconvenient runs or relabel missing evidence as a negative observation.
- Treat measurements as descriptions of particular runs under particular conditions. Avoid interpreting differences in final output or elapsed time alone as proof of what changed internally.
- Do not start from a prescribed set of hotspots, performance findings, optimization proposals, or assumed bottlenecks. Select questions from inspection of the current code and the exploratory measurements.

## Stage 1 — Interactive orientation

Read the local project guidance and the portions of the implementation needed to understand how an ordinary invocation is performed. Establish how to invoke the current application, how to select specimens, and where the existing runtime records are produced.

Record enough context to identify the executable and the environment: repository revision and working-tree state; binary/build identity; OS version and architecture; invocation arguments; relevant runtime configuration; and the intended specimen inputs. Distinguish facts established from the running executable from expectations inferred from source code or documentation.

Decide what to measure and why. For each proposed measurement, specify its start and end events, who observes those events, and what the recorded duration or count does *not* establish. Decide on a small initial set of specimens and run conditions. These should permit interpretation, not attempt to cover the application's full behavior at once.

Do not create a large measurement suite at this stage. Prefer a narrow question that can be checked and revised promptly.

## Stage 2 — Interactive pilot and revision

Conduct short, bounded pilot runs while interactive investigation is still permitted. Inspect both the application results and the operation of the measurement procedure itself.

Determine whether each proposed measure is actually observable at the chosen boundary and whether the procedure changes the conditions it is meant to observe. Record surprising outcomes and failed runs instead of repairing them silently. Inspect resource use or process behavior when necessary, but treat those observations as part of the interactive pilot, not as unattended baseline data.

Revise the questions, workloads, or collection method based on what the pilots establish. Discard measures that cannot support the claim they were designed to test. Do not extrapolate a few pilot measurements into a throughput estimate without appropriate qualification.

This stage ends when there is a small, intelligible set of measurements that can be repeated without requiring an agent's judgment during execution.

## Stage 3 — Prepare the operator-run procedure

Create a self-contained, minimally elaborate procedure that the human operator can launch from a normal terminal. It may be a script or a documented sequence of exact commands. Its behavior must not depend on an agent shell, active agent session, transient working directory, or interactive prompt.

The procedure must:

- Identify the binaries, specimens, arguments, configuration, and repetitions it will use; avoid silently rebuilding or changing them during measurement.
- Save raw stdout, stderr, exit status, and application-produced evidence for each invocation, without overwriting previous runs.
- Record run-level start and end times using an appropriate monotonic source for elapsed duration, along with relevant identifying context and measurement settings. Keep durations derived by the harness distinct from timing fields reported by PW.
- Have bounded behavior, an explicit failure policy, and a comprehensible stop condition. Do not mask timeouts, omit failed specimens, or retry them without recording the retry as a separate event.
- Leave enough information to distinguish completed, failed, interrupted, and never-started invocations.
- Terminate and clean up its own measurement machinery appropriately, without requiring an agent to supervise it.

Keep the procedure mechanically predictable. It should run the chosen measurements and preserve what happened, not diagnose anomalies and change its plan while executing.

Test the complete procedure on a small pilot workload. Inspect the resulting files and verify that they can be interpreted independently of the interactive session. Supply the operator with the exact launch command, the expected output location, the approximate scope of work (number of invocations and configured bounds, not a promised completion time), and a way to interrupt it safely.

## Stage 4 — Operator-issued measurements, without active agent sessions

The operator ends the interactive agent sessions and launches the prepared procedure directly. No agent should launch a background job and then poll, inspect, or troubleshoot it. Other independent agent sessions should not be active during the measurement interval.

The ordinary macOS user session may remain logged in. Logging out is **not** part of the requirement. The operator controls the machine's two known background servers and can either hold their state constant or document a deliberate difference between runs. Avoid unnecessary changes to system configuration made solely to create an artificial notion of a quiet machine.

The measurement procedure may supervise its own child processes and enforce its own deadlines. That necessary supervision is different from an investigating agent opportunistically interacting with the workload. Except for safety or an evident malfunction, the operator need not intervene while it runs.

After it exits, preserve the raw results and record any interruption or environmental event noticed during execution. Do not infer successful completion merely from the absence of an active process; use the saved status records.

## Stage 5 — Analysis after execution

Analyze the unattended results only after the procedure has stopped. Reconcile the invocation manifest with the files actually produced. Account for missing records, failures, timeouts, retries, and interrupted sequences before computing summaries.

Report the number and kind of observations supporting each claim, their variability, and the precise events defining the measures. Distinguish measured elapsed time, CPU time, inferred residuals, and timings emitted by different components. If results from the interactive pilots and the operator-run interval disagree, report the disagreement and examine relevant differences in conditions rather than automatically privileging one set.

Separate:

1. **Observed facts:** source behavior that was verified and measurements actually recorded.
2. **Interpretations:** what those observations suggest, with stated uncertainty and alternative explanations where consequential.
3. **Unresolved questions:** what the current evidence cannot distinguish.

Do not rank speculative speedups or propose architectural changes merely to complete the report. The investigation may conclude that a cost is real and necessary, that its purpose remains uncertain, or that the available measurements cannot yet characterize it reliably.

## Deliverables

Before the unattended run, provide a concise measurement brief, the exact operator instructions, the tested standalone procedure, and the file/output convention. Identify what the procedure will and will not establish. Stop active investigation at handoff; do not remain attached to supervise its execution.

After the run, provide an evidence-grounded runtime report with source/build context, measurement definitions, raw-result locations, sample sizes, outcomes, uncertainty, and findings worth further examination. Do not modify PolicyWitness as part of the investigation.

A successful result is a reproducible account of runtime behavior that preserves the distinctions among the events PW actually observes. It need not identify an optimization.

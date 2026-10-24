# PolicyWitness: Host Lifetime Investigation

## Objective

Establish what happens to the XPC host between PolicyWitness invocations, what the single-use admission rule guarantees, and what that process lifetime costs in ordinary execution. Include built-in runner behavior and, where a usable external runner is available, BYOXPC behavior.

This is a **runtime investigation**, not an implementation task. Do not create a persistent-host prototype, propose a replacement topology, or optimize the application as part of this work.

Keep the scope on **client/host identity, admission, retirement, and relaunch**. Observe worker and validator processes only where needed to establish whether their lifetimes overlap host retirement or the next specimen. Do not investigate phase-barrier spinning, sandbox-operation timing, or the retired log observer.

## 1. Establish the current behavior

Read the repository's planning and runtime-investigation guidance. Inspect the current versions of `docs/ARCHITECTURE.md`, `docs/LIMITS.md`, the XPC service and client code, and the runner-acquisition path. Review F3 in `records/performance/PolicyWitness-Boundaries-Findings.md` and the completed first-cycle runtime report as prior findings, not as evidence that the current build behaves identically.

Record the source revision, executable version/build, executable identity, macOS version, selected runner, and relevant launchd configuration. Determine from source how a request is admitted, how `already_ran` arises, when the reply is issued, and how the host schedules exit. Separate the one-use **admission rule** from the host's actual process termination.

Do not use `runner_result.pid` as a host PID. Previous runtime work established that successful replies expose the worker PID there. Establish host identity separately, or report explicitly that it could not be observed reliably.

## 2. Establish a usable observation method

Prepare a small, bounded harness under `records/performance/` or use existing measurement facilities. Prefer external observation and existing application fields. Do not alter PW application source, schemas, timeouts, signing, packaging, or worker behavior.

For each invocation, retain the command and runner selection, controller/client exit status, raw envelope, timestamps, and observed process identities. Where possible, record the host's **PID plus process-generation identity** (such as start time), client identity, worker identity, host start/exit observations, and any admission or XPC errors. A PID without generation evidence is not sufficient to establish that a host was reused or replaced.

Name each timing interval by its actual endpoints and observer. Distinguish a host exit observed by the harness from an exit inferred from the absence of a process or from a reply. Do not assign unexplained residual time to host startup, XPC, signing, or launchd.

Pilot the method until it can identify the host or can state precisely why that observation is unavailable. Preserve the pilot results, including failed identification attempts.

## 3. Measure the built-in runner

Use ordinary, known-good, single-specimen executions on the existing build. Start with:

1. Five separated invocations to establish the normal process lineage and retirement sequence.
2. At least ten rapid sequential invocations to examine whether a retiring host affects the next request.
3. Five pairs of deliberately overlapping invocations, recording whether overlap actually occurred and whether the requests reached the same or distinct host generations.

These are initial counts, not a statistical claim. Extend them only to settle a specific unresolved observation. Keep each command and the full series bounded by explicit deadlines; do not leave an investigator-owned polling process running after the series ends.

Report admitted versus refused requests, `already_ran` and XPC failures, observed host generations, worker generations, reply-to-exit intervals, and any interactions between successive invocations. Do not infer host instancing solely from distinct worker PIDs or successful overlap.

## 4. Examine external-runner behavior if available

If a working, documented BYOXPC runner can be exercised without introducing a new persistent service or changing unrelated machine configuration, run a small rapid-sequential series against it. Record the configured `ThrottleInterval`, actual host launch observations, admission outcomes, re-acquisition behavior, and elapsed intervals between invocations.

Establish whether the alleged one-second relaunch floor is observed **at the host-generation boundary**, rather than merely inferred from overall wall time. Compare the observed admission and retirement sequence with the built-in case without assuming their launchd instancing is identical.

If this requires substantial environment setup or cannot be observed reliably, mark the external case untested and explain the blocker. Do not expand the investigation to implement or redesign BYOXPC deployment.

## 5. Check the lifetime boundary

For the cases actually exercised, determine which child processes and host-owned resources are known to end before the host reply, between reply and host exit, or afterward. Distinguish confirmed cleanup from cleanup inferred only because a process disappeared.

Inspect existing abnormal-exit evidence or run one bounded, already-supported failure control if needed to test a consequential uncertainty. Do not introduce new deliberate hangs, kill unrelated processes, or expand into a general worker-timeout investigation. Record any surviving owned processes and the limits of what can be established about them.

## 6. Report

Write a concise findings report under the performance records. Include:

- Exact application and machine identities, commands, cases, counts, and measurement boundaries.
- A process-lifetime account distinguishing controller, client, host, worker, and relevant descendants.
- Observed admission, reply, retirement, and relaunch behavior for built-in and any tested external runner.
- Timing distributions with their endpoints and sample counts; retain failures and outliers.
- Specific agreements or disagreements between the source-level model and runtime observations.
- Unresolved questions, including any process identities or lifetimes that could not be observed directly.

Keep raw outputs and the measurement procedure available for reproduction. Record cleanup and incomplete runs explicitly. Do not label a missing observation as zero or a source-level expectation as a measured fact.

Conclude with short, direct answers to these questions:

1. Does each observed admitted invocation get a fresh host generation? What evidence establishes that?
2. What exactly does the one-use admission rule prevent, and when does the host actually exit?
3. Does host retirement constrain subsequent built-in or external invocations in the observed cases?
4. What does host termination demonstrably clean up, and what remains unestablished?
5. What cost can be measured at these boundaries without attributing unmeasured internals?

Do not finish with an optimization plan. Preserve the distinction between a costly boundary, an unnecessary boundary, and a boundary whose necessity has not been established.

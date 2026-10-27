# PolicyWitness: Log Observer Runtime Investigation

## Purpose

Investigate the runtime cost and observational behavior of PolicyWitness's supplementary sandbox-log collection. Treat these as related but distinct questions:

1. **Cost:** What does the measured collection interval contain, and how does its duration respond to query characteristics and execution conditions?
2. **Observation:** For a fixed underlying execution, do the retrievable records change according to when and how often they are queried?

This is an empirical investigation, not an instruction to optimize, redesign, or replace the log observer. It need not produce a proposed change. Preserve the distinction between the time taken to *look* and the information that looking makes available.

Continue within the existing runtime-investigation records and repository guidance. Use the current code and artifacts to establish what is actually running before relying on earlier descriptions.

## Established starting point

The first completed operator series measured PolicyWitness 0.3.2, build 841, over 1,452 invocations, including 660 capture-enabled specimens. For five single-step built-in-runner specimen types, median complete wall time was approximately 672 ms with capture and 37–41 ms without. The log-supervision interval `L` had per-cell medians of 630–632 ms. `L′` had per-cell medians of 629–630 ms.

**Neither `L` nor `L′` isolates the execution time of `/usr/bin/log show`.** They include parts of the observer's process setup and supervision; they share a start time. Neither includes all subsequent controller processing. The captured status is evidence of a collection procedure's outcome, not proof that all relevant OS records were available.

Read `records/performance/README.md`, `RUNTIME-MEASUREMENT-BRIEF.md`, and `RUNTIME-INVESTIGATION-REPORT.md` for definitions, provenance, and limits. These paths describe the previous investigation; establish their current locations rather than assuming an unchanged checkout. The previous results are a point of comparison, not a performance target or a claim about the current executable.

## Inquiry A: Where does collection time go?

Reconstruct the actual existing path from the controller's collection request through observer startup, construction of the macOS log query, child execution, output handling, and the controller's return to envelope assembly. Identify which endpoints are already timed and which remain aggregated.

Use fixed historical query windows where the relevant records are still available. Compare appropriately equivalent invocations of the existing observer and the underlying system log tool. Preserve the precise command arguments, window, predicate, output mode, environment, status, output sizes, and timing endpoints. If those differ, state the difference rather than interpreting the elapsed-time difference as pure wrapper overhead.

Examine whether query cost changes with:

- The width and placement of the queried interval.
- Predicate form and selectivity, including deliberately no-match queries.
- The quantity of returned data, considered separately from predicate complexity.
- First versus subsequent queries, and query order.

Do not assume that increasing the window increases cost linearly, or that low output means a cheap query. Alternate or balance comparisons where practical, so that gradual environmental changes and query warming are not automatically mistaken for a treatment effect.

If external measurements do not separate the consequential components, narrowly scoped diagnostic instrumentation is permissible. Keep instrumented and uninstrumented executions identifiable; do not quietly treat an altered observer as the original measurement path. There is no requirement to instrument merely to fill every box in a timing diagram.

## Inquiry B: Does collection timing affect available evidence?

For one or more fresh, well-identified sandbox executions, hold the **original worker identity, execution window, padding convention, predicate, and output format** constant while querying that event interval more than once at different delays. Record the query's actual start and end, not just its nominal delay after execution.

Compare the returned records themselves, not only record counts or the collector's `captured` status. Preserve enough original content to distinguish added, missing, modified, reordered, and duplicate records. If the available format provides no stable record identifier or structured timestamp, explain the matching method and its ambiguity rather than manufacturing certainty.

Repeated queries introduce another variable: an earlier query may affect later queries or the logging system's state. Where feasible, include comparable fresh executions whose *first* query occurs at different delays, alongside the repeated-query observations. This permits a more useful distinction between collection delay and previous-query effects. The experiment need not posit an exhaustive schedule in advance; start small and refine it based on whether the observations can answer the question.

An empty result does not establish that no relevant sandbox event occurred. Stable results across repeated queries do not establish log completeness. Records retrieved later are not necessarily a monotonic superset of records retrieved earlier. Changes in the window or predicate are separate observation conditions, not repetitions of a fixed observation.

Also establish what a successful collection status means for these comparisons, including any encountered timeouts, truncation, observer failures, or empty captures. Retain those outcomes rather than filtering them out as inconvenient.

## Measurement discipline

Keep the application specimen execution distinct from supplementary collection. Cost experiments may reuse fixed windows without rerunning PW. Experiments about delayed availability require controlled fresh events, but should not regenerate a specimen merely to supply another observation of the same event.

Prefer existing binaries, envelopes, and source-supported observer interfaces. Record executable/build identities and any departure from ordinary PW collection semantics. Preserve raw timing observations, exit statuses, missing measures, query arguments, and relevant environmental conditions. Use explicit timeout and cleanup bounds for spawned processes, including failed invocations.

The first runtime cycle revealed timing drift within a single operator-run series. Treat sequence position and elapsed time as relevant observations. Do not infer a causal effect from small differences between an early and late group without examining that drift.

Unified logs can contain incidental sensitive information, including paths and records unrelated to PW. Keep raw output local and appropriately restricted. Do not commit broad raw log extracts by default. Produce inspectable derived evidence and indicate exactly which claims require access to raw files. Respect the existing distinction between retained raw runs and committed evidence summaries; do not claim that a checksum manifest supplies a portable copy of absent data.

Use proportionate runs. A modest, interpretable comparison is preferable to a large matrix whose query conditions cannot be disentangled. There is no required agent-free operator stage: the experiment may run interactively or independently, provided its execution and observation conditions are explicit and the investigator does not introduce unrecorded intervention.

## Deliverable

Add a report to the runtime-investigation records, consistent with their local contribution conventions, that addresses:

1. **Observed collection path:** The actual components, timing endpoints, and unresolved intervals.
2. **Cost characterization:** Distributions and comparisons by query condition, with raw observations and sufficient provenance to reproduce the calculations. Distinguish measured intervals from residual estimates.
3. **Observation characterization:** How the record set for a fixed event interval changed—or did not change—across collection times and repetitions. Distinguish query success, event retrieval, and any claim of completeness.
4. **Controls and exceptions:** Failed, empty, delayed, interrupted, or anomalous observations; environmental drift; and any instrumentation effects.
5. **Open questions:** What remains unestablished, including alternative explanations consistent with the measurements.

Separate observed facts from interpretations. Avoid estimates of prospective speedup and do not turn the report into a proposal for batching, streaming, caching, deferred attachment, or altering the semantics of collected evidence.

The investigation is successful if it yields a defensible account of **what it costs PW to retrieve supplementary records** and **what changes, if anything, when the same underlying events are inspected at different times**. A result that establishes limits on the available evidence is as useful as one that explains most of the elapsed time.

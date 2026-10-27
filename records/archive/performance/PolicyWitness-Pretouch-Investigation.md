# PolicyWitness investigation: Does pre-touching shared memory matter?

## Question

PolicyWitness establishes and pre-touches its shared-memory reporting region before the worker applies the submitted sandbox policy.

**Does pre-touching that memory change whether a worker can successfully publish to it after applying a restrictive sandbox profile?**

Investigate this as an empirical question about macOS on Apple Silicon. The existing implementation is evidence of a design choice, not proof that the precaution is necessary.

## Historical context, not an investigative assignment

In May 2026, PolicyWitness encountered reporting failures while exercising restrictive SBPL version-2/3 specimens. An initial separation of the XPC host from a Swift worker reporting over a Unix socket did not resolve all the failures. The project subsequently adopted a C worker publishing into shared memory established before sandbox application. A controlled experiment under bare `(version 2)(deny default)` demonstrated successful post-application publication through that arrangement.

A later restrictive version-2 experiment exposed a different failure: the worker could publish a post-application clock error through shared memory, but could not proceed to its intended attempt. The test nevertheless passed because its assertions required a successful prediction, not successful completion of the attempt. Subsequent work repaired the clock dependency and strengthened the test.

The historical connection between restrictive higher-version specimens and these engineering changes is well supported. The evidence does **not** isolate the SBPL version number as the cause, establish that shared memory was the only viable reporting mechanism, or demonstrate that every precaution in the resulting design was necessary.

**Treat this history as established background for present purposes, not as a research direction.** Do not reconstruct its chronology, revisit the original design decision, or use historical motivation as evidence of current behavior. No historical account or assessment of that decision is requested.

The example illustrates how an experimental instrument can encounter unexpected dependencies on the substrate, preserve evidence despite those dependencies, and still pass a test that did not establish the intended result. It does not prescribe what the present investigation should discover.

## Investigation

Inspect the current worker's shared-memory setup and publication sequence sufficiently to identify what pre-touching does and when it occurs relative to sandbox application.

Then conduct a bounded live experiment that distinguishes publication into memory touched before application from publication into otherwise equivalent memory not previously touched.

Design the experiment using your judgment of the relevant macOS mechanisms. In particular:

- Establish that the comparison actually varies pre-touching rather than inadvertently varying mapping, inheritance, profile application, or some other consequential condition.
- Include controls adequate to distinguish a successful publication from an attempted publication, an unreadable result, or a worker that never reached the intended store.
- Observe the result independently of the worker's own success report. Preserve relevant native results, process disposition, and the evidence necessary to interpret them.
- Establish which policy, executable, OS build, and experimental conditions produced each observation.

Use a disposable fixture or experimental copy where necessary. Do not alter the production implementation to accommodate the experiment.

**Actually conduct the investigation.** Source inspection and a proposed experiment are not substitutes for observations. If a particular experimental condition cannot be reached, explain the obstacle and distinguish it from a negative result.

Do not assume that a difference establishes sandbox causation, or that the absence of a difference establishes universal equivalence.

## Report

Produce a compact Markdown report addressing:

1. **Experimental distinction.** What exactly differed between the tested conditions, and how was that distinction established?
2. **Observations.** What happened, including the independent evidence and the outcomes of controls?
3. **Interpretation.** What can be concluded about pre-touching under the conditions tested? What plausible explanations remain distinguishable or unresolved?
4. **Limits.** What does the experiment not establish?

Preserve enough information and raw evidence to make the investigation reproducible and its interpretation independently checkable. Report failed or inconclusive experiments rather than silently replacing them.

A useful result may be **yes, no, conditional, or not established**. Do not manufacture a categorical answer.

## One further question

**Only after examining the results**, identify one consequential follow-up question suggested by the evidence.

Explain briefly why it deserves investigation and what observation would distinguish its possible answers.

Do not investigate that follow-up unless doing so is necessary to resolve the initial question. Do not generate a backlog or a decision tree of possible investigations.

The deliverable is an experimental finding and one well-chosen question, not an implementation plan, an architectural recommendation, or a historical review.

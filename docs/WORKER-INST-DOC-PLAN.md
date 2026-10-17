# Plan a developer document on the PolicyWitness worker

Develop a locally grounded implementation plan for a third major PolicyWitness developer document, provisionally titled **"The Worker: Instrument and Constraints"** (`WORKER.md`).

**This is a planning task only.** Do not write the document, implement its diagrams, or change production code. Follow the repository's existing project-planning guidance.

## Purpose

The existing ARCHITECTURE.md and BUILD.md explain, respectively, one run and one build unfolding in time. The new document should take a different approach: explain the C worker as an **experimental instrument**, concentrating on the constraints that make its observations meaningful.

Its central question is:

**What can the worker carry across the sandbox boundary without compromising the experiment?**

The worker must be capable enough to conduct experiments and report observations, but not so insulated from the specimen policy that it ceases to measure the restrictions under examination.

## Proposed treatment

Develop a plan around three subjects:

1. **The worker's endowment.** Distinguish resources prepared to support observation from resources whose acquisition must occur under the specimen policy. Explain how apparently harmless preparation can change what an experiment measures.

2. **The worker's permitted ignorance.** Explain the intentional limits on what the worker knows, interprets, and claims. In particular, distinguish firsthand native observations from external predictions, process disposition, logs, and causal attribution.

3. **The contamination problem.** Examine superficially reasonable engineering improvements that might compromise experimental validity: preacquiring resources, moving setup before policy application, or retrying operations under changed circumstances. Treat these as questions of experimental design.

Consider a **capability map** as the principal illustration, distinguishing prepared apparatus, authority introduced into the worker, capabilities exercised under the specimen policy, and observations supplied from outside it. This should not be another execution timeline.

## Planning expectations

Inspect the current (0.3.1) implementation, documentation, contracts, and relevant tests. Test the proposed account against what the repository actually does, including qualifications and known limitations.

Determine how the new document should relate to existing material without duplicating the architecture tour, implementation references, or normative contracts. Preserve the repository's established expectations for technical claims, source references, diagrams, and verification.

Leave substantial editorial and structural decisions to the planning process. The proposed subjects are a starting point.

Produce a plan grounded in the current checkout, identifying the proposed document's scope, structure, supporting evidence, illustration strategy, integration and verification work, and any unresolved questions.

**The goal is a plan from which a subsequent agent can write a good document—not a preliminary version of the document itself.**
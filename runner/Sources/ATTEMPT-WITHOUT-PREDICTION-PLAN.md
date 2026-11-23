# Can a user ask for just the attempt?

**Release target.** Conclude during the 0.3.8 guide work. Choose the release for any product change with the result.

**Decision goes to.** Handoff finding 3 under [what a colleague can establish](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md#what-can-a-colleague-establish-about-a-run-they-did-not-see), and an entry in the [product-change ledger](../../records/guide/PRODUCT-CHANGES.md), whether or not the behavior changes.

An author who only needed an `exec` step to hold a process had to invent a validator question. A second author deliberately queried metadata on one file and read data from another. What is the smallest request that serves both authors? [Scope study](../../records/guide/work/scope/README.md) · [Handoff finding 3](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md)

1. Put the shipped crossed pair beside the output of `help example`. Sketch a card from the same example that shows each query and attempt with its operand. Can a reader tell which question to edit while keeping the original policy? [Example card](../../controller/interface/cards.rs)
2. Sketch the hold-only step with an explicit `sandbox_check: null`. Compare it with an omitted field, a malformed query, and a valid query whose target is absent. Today the planner can report `query_not_requested` for the last case. Can the reply distinguish an author's choice from a planner decision? Trace both ordinary and actor probe admission. [Request decoder](PWRunnerCore/PWRunnerRequest.swift) · [Actor admission](PWRunnerCore/ActorPlan.swift) · [Step results](PWRunnerCore/CWorkerStepResults.swift)
3. Draw the validator batch, phase release and resulting rows for a mixed phase and for a phase with only attempts. Identify which rows earn `query_first` and what evidence establishes execution in each. [Phase controls](../../records/guide/EXPERIMENTS-TO-PRESERVE.md)

Return the example card and specimen/reply sketches. Say which confusion the card alone resolves and what additional work an explicit opt-out would remove.

# Contributing to PolicyWitness

PolicyWitness is a research and teaching tool. Its code, specimens, tests, and written contracts are parts of the same instrument. Changing what the code does can change what a result means, and changing what a result means can require changes outside the code.

## Investigating and changing

There are two subjects here: the macOS sandbox and the means of observing it. The experimental apparatus can influence what happens. Opening a file before sandbox application, for example, does not test whether the sandbox allows it to be opened afterward. Which process acts, when it acts, and what authority or resources it already holds can be as important as the policy text.

A useful investigation often begins with a narrow question. An existing specimen may provide a starting point; varying one condition and retaining both inputs and observations can make the result comprehensible to another reader. Sometimes the result is a change to the instrument. Sometimes it is a more precise account of its limits, or evidence that a proposed change isn't warranted. Work on the harness itself deserves attention to what its modifications make possible, or impossible, to observe.

## Planning a change

A plan is one way to carry decisions across a boundary: between exploration and implementation, or between people or agents who do not share the same conversation. It is useful when the rationale, dependencies, or verification of a change would otherwise have to be reconstructed. Small changes need not be preceded by a plan; an investigation need not end in a proposed change.

A plan should be usable by someone who knows the repository but not the history of its preparation. It identifies the problem, the intended result, the proposed approach, and where that approach stops. It explains consequential choices and points to the code, contracts, tests, or observations on which they rest. The right amount of detail is what the executor would otherwise have to rediscover or decide, not a transcription of the planning conversation.

How much investigation is needed depends on the uncertainty. Source inspection, reproducing failures, small experiments, and comparison of approaches are useful when they affect the proposal; they are not steps to perform for their own sake. Questions that can be settled beforehand should not become implementation chores. Where a consequential question genuinely depends on work not yet done, the plan should make clear what would answer it and what depends on the answer. Routine implementation choices can remain with the executor.

`records/` is a place for materials committed before and during the planning, implementation, and acceptance of changes. Planning materials there are generally consumed by acceptance review and retired with the plan.

Verification belongs in the proposal. The checks should establish the intended behavior, not just the absence of an error; where a misleading pass is plausible, the plan should account for it. Include tests and documentation when they are needed to preserve or explain the change. A plan is ready when its reader can proceed without reconstructing its rationale, while recognizing evidence that would require reconsideration.

## Improving documentation in four passes

Choose one bounded topic and three concrete reader questions. Work through these
passes to improve the reader's ability to find, understand and apply the contract.
Shorten, expand, repeat or relocate material when that serves those questions;
fewer words or files do not by themselves establish improvement.

1. **Establish ownership.** Map each question to its authoritative definition,
   other presentations and supporting checks. Public meanings belong in the
   authored contract, concrete build-specific specimens in app source,
   mechanisms in implementation tours, user tasks in the guide, and evidence
   in the existing graded support records. Keep unresolved ownership explicit.
2. **Consolidate explanations.** Resolve reading problems using that map.
   Preserve consequential conditions and useful repetition. Compare revised
   explanations with their owners; a citation check establishes that a source
   exists, not that it supports the explanation. Changes to public meanings,
   ownership or interfaces need a concrete maintainer decision within the
   change's agreed scope.
3. **Use app-owned examples.** Extract documents and useful fragments from
   their actual owner where this improves reading or removes alignment duties.
   Keep expected refusals and independent effect observations separately
   authored, and establish admission through the existing execution path.
   Keep teaching material and verification separable from its presentation so
   another interface can reuse them.
4. **Clarify support.** Keep qualifications and evidence limits beside claims.
   Render citations and provenance from existing support records where useful;
   combine owners only when their assertions and scopes coincide. Preserve the
   distinctions between source inspection, constructed checks and native evidence.

Finish by answering the three questions through the resulting reading paths,
stating remaining difficulties and the maintenance duties added or removed.
Retaining the existing arrangement is a valid outcome of any pass. Additional
review should resolve a specific uncertainty. Use owning generators and checks
appropriate to the changed boundary, following [test guidance](tests/AGENTS.md).

## Working guidance

> You should read AGENTS.md, even if you're a human

The root [AGENTS.md](AGENTS.md) and its directory-level counterparts give the working rules for the repository while READMEs describe the components and link to their contracts and deeper accounts. The `CLAUDE.md` files at the root and under `controller/`, `runner/`, and `tests/` are symlinks to adjacent `AGENTS.md` files; working guidance is edited in `AGENTS.md`.

## Writing guidance

Before adding an imperative, identify the concrete failure it prevents and check whether an existing instruction or automated check already covers it. Address imperatives directly to the reader, without distinguishing between human and automated contributors.

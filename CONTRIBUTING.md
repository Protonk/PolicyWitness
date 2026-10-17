# Contributing to PolicyWitness

PolicyWitness is a research and teaching tool. Its code, specimens, tests, and written contracts are parts of the same instrument. Changing what the code does can change what a result means, and changing what a result means can require changes outside the code.

## Investigating and changing

There are two subjects here: the macOS sandbox and the means of observing it. The experimental apparatus can influence what happens. Opening a file before sandbox application, for example, does not test whether the sandbox allows it to be opened afterward. Which process acts, when it acts, and what authority or resources it already holds can be as important as the policy text.

A useful investigation often begins with a narrow question. An existing specimen may provide a starting point; varying one condition and retaining both inputs and observations can make the result comprehensible to another reader. Sometimes the result is a change to the instrument. Sometimes it is a more precise account of its limits, or evidence that a proposed change isn't warranted. Work on the harness itself deserves attention to what its modifications make possible, or impossible, to observe.

## Planning a change

A plan is one way to carry decisions across a boundary: between exploration and implementation, or between people or agents who do not share the same conversation. It is useful when the rationale, dependencies, or verification of a change would otherwise have to be reconstructed. Small changes need not be preceded by a plan; an investigation need not end in a proposed change.

A plan should be usable by someone who knows the repository but not the history of its preparation. It identifies the problem, the intended result, the proposed approach, and where that approach stops. It explains consequential choices and points to the code, contracts, tests, or observations on which they rest. The right amount of detail is what the executor would otherwise have to rediscover or decide, not a transcription of the planning conversation.

How much investigation is needed depends on the uncertainty. Source inspection, reproducing failures, small experiments, and comparison of approaches are useful when they affect the proposal; they are not steps to perform for their own sake. Questions that can be settled beforehand should not become implementation chores. Where a consequential question genuinely depends on work not yet done, the plan should make clear what would answer it and what depends on the answer. Routine implementation choices can remain with the executor.

Verification belongs in the proposal. The checks should establish the intended behavior, not just the absence of an error; where a misleading pass is plausible, the plan should account for it. Include tests and documentation when they are needed to preserve or explain the change. A plan is ready when its reader can proceed without reconstructing its rationale, while recognizing evidence that would require reconsideration.

## Working guidance

> You should read AGENTS.md, even if you're a human

The root [AGENTS.md](AGENTS.md) and its directory-level counterparts give the working rules for the repository while READMEs describe the components and link to their contracts and deeper accounts. The `CLAUDE.md` files at the root and under `controller/`, `runner/`, and `tests/` are symlinks to adjacent `AGENTS.md` files; working guidance is edited in `AGENTS.md`.

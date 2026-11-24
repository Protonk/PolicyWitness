# Designing PolicyWitness

Someone investigating a failed file open can give PolicyWitness a policy, a
pathname and an operation to attempt. PW can ask a validator about the live
worker, let the worker attempt the open and record what each observed. The
investigator can prepare a file with known contents or change one rule and
repeat the trial. This makes a question about a particular process under
particular conditions answerable. Explaining a failure in someone else's
application still requires evidence about the call that application made.

A result should tell its reader who could see a fact and when. A prediction
collected before a phase and a return published by the worker describe
different events. A file can exist after a create whose return the worker
never published. Someone looking at the file can establish its presence. To
attribute its creation, they also need to know its starting state and who
else could write there. Keeping those distinctions visible lets a reader
draw a conclusion, challenge it or say which observation is still missing.

## Five projections

The intended interface gives a person at a terminal and a program reading
stdout five ways to investigate with the same application.

**`run`** admits the caller's specimen and carries out the work it authorizes
under ordinary product commitments. Its answer must make refusals, incomplete
observations and uncertainty as legible as a completed attempt. A finished
run can give a useful account of a failed open. The author can deliberately
ask about metadata on one path and attempt to read data on another. Preserving
both operands lets the recipient tell which question each observation answers.

**`test`** gives investigators explicit ways to vary consequential decisions
PW ordinarily makes for them. It should be the default runtime entry for
tests, sharing the production execution path. With the same specimen and
no intervention, it should give the same
admission decision, execution behavior and result meaning as ordinary
`run`. With a control, the caller needs to distinguish
the request, the setting that took effect and the evidence that the
intervention occurred. A deliberately induced timeout can complete the
promised observation. The application still timed out. A judgment about that
observation, its authority to block acceptance, and a failure to collect
evidence or finish cleanup each answer a different question.

**`help`** should expose the observable interface mechanically. The declaration
that gives an option its spelling and accepted values should also supply its
help. Change that declaration and both the card and the command should respond.
For an option that selects a runner, the consequential question is which
service received the work. Parsing the displayed option answers only the
first part.

**`guide`** gives the reader an independently authored explanation of how to
investigate. The web page, the Markdown delivered by the app and a requested
verb section all draw on one document. The author chooses the question, the
control and where to stop drawing conclusions. A short lesson earns its
place when a reader can reproduce the case and adapt it to a nearby question,
including one that calls for evidence PW cannot collect.

**`example`** should turn the build's contract into complete specimens that a
reader can run unchanged, inspect and vary. The choices that make an example
worth running should be visible in its input. If its lesson depends on a
query and a read naming different files, a specimen that silently gives them
the same path can still run perfectly. Checking that distinction needs the
submitted operands and an independent observation of the file actually read.

## Following a claim

These views overlap because a caller moves between them. A guide reader
can obtain an example, use help to understand a choice, then try it and
examine the result. Agreement among outputs derived from one declaration
shows they describe it consistently. The file observed by another process
and the conclusion a reader can defend after changing a condition each test
something that agreement cannot establish.

From a field, option, control, refusal or outcome, a caller should be able to
find the applicable release contract in normal use. The route must reach the
conditions, defaults, limits, ordering, provenance and consequences that bear
on the decision at hand. Difficulty explaining when to retry a timed-out run
may expose a missing observation in the application, an ambiguous promise in
the contract or a test that accepts two histories as equivalent. Follow the
difficulty to its source. Where the evidence runs out, leave the uncertainty
intact.

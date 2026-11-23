# From the 0.3.8 guide to the next command-line release

“0.4.0” is a working destination. The intended outcomes are a useful division of work among the verbs, the name `test` for today's `test-input`, and a guide that teaches the decisions a user still owns. Changes can land together, be split across releases, or include findings from the work. Choose the tags once the scope is clear. [The command line as an API](CONTRIBUTING.md#the-command-line-as-an-api)

## Finish the 0.3.8 reading

The contract trace connects a changed source, interface or check to the public statements it may affect and records how far their support extends. The executable supplies `help`, `example` and `test-input`. The user requirements identify what the caller supplies, what PW observes and which control checks the distinction. Draft 0 uses those pieces from the first runnable specimen through repair and evidence handoff. [Contract tracing](docs/CONTRACT.md) · [User requirements](docs/REQUIREMENTS.md) · [Guide draft](docs/guide/PolicyWitness.md)

The remaining editorial work is the reader's pass and the maintainer's own read. Use a point where the reader gets stuck to decide whether the draft needs a correction for this release or the executable should change in the next work. The maintainer will decide whether to commission an additional independent trace review. Stamping, accepting the tagged ZIP and publishing follow the release procedure when the guide is ready. [Guide review plan](docs/guide/USER-GUIDE-PLAN.md) · [Release procedure](docs/SIGNING.md#release-procedure)

## Give the executable the work it can do

Start with a task from the guide. Let the reader try it with the installed executable, then compare what they could discover, run or establish with what the guide had to tell them. Use the existing worked cases first.

| Reader's task | What to try | What belongs in the guide |
| --- | --- | --- |
| Find out whether a finished experiment can contain a failed open | Ask `help result` about completion and read a saved result with a failed worker open. Check whether the build makes both answers findable. | Why the worker observation matters for this question |
| Produce a specimen this build can run, then read a file of my choosing | Get the complete specimen from `example`. Use `test-input read` with an absolute target, inspect its query and attempt, and pass it to ordinary `run` against known fixture bytes. Look for any option, field or JSON the reader still has to copy from prose. | How to choose a target and use independently known bytes to judge the read |
| Tell a colleague what changed between two saved runs | Use the four file-open results in the compare study. Identify the operand, published outcome and fields that support each answer. Try a reused step ID with a different operand. | Why the chosen pair is a control and which causal claim remains open |

Move a lookup or recipe when the reader can recover it from the executable and use it successfully. Follow friction back into the app. For example, ask what the reader expects `test read` to do before showing its proposed help. If they expect it to open the file, inspect the name, help and output alongside the form that actually runs a specimen. Record the change that resolves the confusion, or why the distinction deserves to stay. [Interface definitions](controller/interface/README.md) · [Guide review methods](docs/guide/USER-GUIDE-PLAN.md#ways-to-make-progress)

## Decide what to ship

- **Examine `compare` as a verb.** Start offline with the saved envelopes. Settle the question, supported inputs, output, refusals and what a program such as PAWL could consume. A reader should be able to point from a reported difference back to the observation in each file. Record the first useful comparison or the reason to defer it. [Compare investigation](controller/src/COMPARE-PLAN.md)
- **Rename `test-input` to `test` by the release called 0.4.0.** Carry both the specimen-emitting `read` form and the executing `run` form through the public entry point. Inventory current callers and scripted examples before choosing whether to retain the old spelling for a transition or make an announced break. Update dispatch, help, inventory, caller-facing contracts and guide examples together. Exercise emission into ordinary `run` and the experimental-control route, and check the chosen behavior for the old spelling. [Current forms](controller/README.md#cli-surface-contract) · [Interface inventory](controller/interface/README.md)
- **Feed what the reader found back into the contract and guide.** For each changed meaning, identify the authored statement, an observation or refusal that distinguishes it, and the user requirement or passage it affects. Use an existing case when it already makes that distinction. The guide work already recommends a distinct operation to check a repaired specimen before authorizing its effects. Its owner plan carries the prototype results and the production questions into the next scope decision. [Contract owners](docs/contract/README.md) · [Admission study](runner/Sources/ADMISSION-CHECK-PLAN.md)

The pytest archive reader and shared blob store have their own accepted scope. They can proceed independently of release numbering. Keep per-item observations while doing that work. [Pytest evidence plan](tests/PYTEST-EVIDENCE-PLAN.md)

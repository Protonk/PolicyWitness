# Release staging through the command-line transition

## 0.3.8 (published)

The release traced and reorganized the public contract, separated experimental controls from ordinary requests, revised how the harness reports observations and judgments, and shipped the standalone guide with six rerunnable cases. The signed ZIP passed release acceptance. The annotated tag is `v0.3.8`. [Public contract](docs/CONTRACT.md) · [Worked cases](docs/guide/README.md#worked-cases)

## 0.3.9: a runnable extension example from `example`

**The challenge.** Extensions are the one experiment the guide teaches without a specimen the reader can run. An extension trial needs an actor specimen. Two readers each get a worker and a policy, and issuance, transfer, consumption, release and fresh reads happen in a deliberate order. The guide's other cases start from a one-step specimen and change two or three fields. Building an actor specimen with jq would take more shell than every other case together, and the reader would learn more about jq than about the experiment. [EXTENSIONS](docs/EXTENSIONS.md) has no runnable example. The extension controls retain a [two-actor specimen](tests/fixtures/extensions/file-read.json).

**Intended result.** `example` takes a name. `example extension` prints an actor specimen bound to the build, which that build's `run` admits. The guide then teaches the experiment through small edits the reader makes. The verb does not need to compose the whole experiment. It supplies a correct starting point that already runs and shows something. The guide supplies the sequence of changes and what each result shows. For instance, the reader might add baseline reads, then move the grant to the other reader and compare the two runs. Unnamed `example` keeps printing today's specimen.

**Settle these in order.**

1. *What the verb prints and what the reader changes.* Write the guide passage first against a hand-built specimen and run it on a signed build. Each edit should teach one thing. Put an edit that the reader must type but learns nothing from into the printed specimen. Leave an edit that is the lesson with the reader. Use the [saved recipient-swap inputs](docs/guide/USER-GUIDE-PLAN.md#paired-inputs) to work out that edit. Swapping the recipient stays with the reader. Count the edits and the jq each needs before fixing the printed specimen.
2. *Known bytes.* `example` reads no file and names fixed system paths. The lesson depends on fresh reads of bytes the reader chose. Either `example extension` takes a target, as `test-input read --target` does, or the guide retargets the specimen with jq. How many places a target appears in the actor specimen decides which is simpler to teach.
3. *What the build guarantees.* The build guarantees that its own `run` admits what `example` prints. The round-trip case submits the printed example and checks its observations. A named example needs the same guarantee and its own round trip. The guide's edited forms fall outside that guarantee and remain a review item. The printed document carries no stability promise between builds, so the guide's edits should select actors and steps by the IDs the passage names rather than by position. [Example statement](docs/REQUEST.md#contract-request-specimen-emit_example) · [Round trip](tests/suites/witness_contract/check_example_round_trip.py)
4. *The interface.* `example` takes no argument today and exits 2 when given one. A name operand changes the interface definitions and inventory, the `example` help card, which reads the constant's phases and attempts, and the `request.specimen.emit_example` statement. It also changes the controller README and the CLI tests. Decide how `help example` presents the names and what an unknown name does. [Interface definitions](controller/interface/README.md) · [Example source](controller/src/example.rs)
5. *Which names.* Add `extension`. Add another name only where a guide case's jq would otherwise grow past a few lines. The nearest candidate is the create step that three current cases build from a read with three field changes.

**Where this stops.** One named example, `extension`, and the guide passage that uses it. `test-input` keeps its forms. A second name is optional.

**Verification.**

- Run the interface routes: `unit`, `integration` and `source_drift`, and record a mutation when a governing definition changes. [Interface routes](tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards)
- Extend the example round trip to each name.
- Point the extension controls at the printed specimen in place of the fixture. They must still check the actual reads separately from delivery and consumption.
- Run the guide's extension passage in order on the signed build. After consumption only the recipient's fresh read changes, and swapping the recipient swaps which read changes. Add the passage's row to the case table.
- Record the operand and the changed statement for the 0.3.9 release notes.

## 0.3.9 runner help and recovery

A reader has just run `runner remove`. It exited 0. Can they discard the staged bundle? Today `help runner` falls back to the base help card. Invoking `runner` without a subcommand prints its syntax on stderr. The answer depends on `data.cleanup_retained`, which can be true even at exit 0. The 0.3.8 guide gives the recovery procedure at the point of use. [Guide recipe](docs/PolicyWitness.md#use-an-external-runner) · [Registry ownership and recovery](controller/README.md#registry-ownership-and-recovery)

Investigate a `runner` topic discoverable from base help. Draw the subcommand names and accepted selectors from definitions shared with dispatch and argument parsing. Show which commands inspect state and which change it. For a pending cleanup, the reader needs to find the retained record, inspect service and plist ownership with `runner reconcile`, and recognize when to retry `runner remove` using the recorded selector. Displaying help should require no registry or installed service. [Runner dispatch and usage](controller/src/runner_commands.rs) · [Help card renderer](controller/interface/README.md)

Try the card with two saved removal results. Both report `ok` and exit 0. One confirms cleanup and the other retains it. Given only the executable and each result, can the reader decide whether to keep the bundle and name the next command, if one is needed? Use the existing recovery controls for the two outcomes. Defer a fuller worked recovery example until the card supports that decision. [Recovery controls](tests/suites/runner_byoxpc/opt_in/registry_recovery.py)

## 0.3.9 subtractive experiment

Choose one question when the investigation starts. Read the released guide and caller responsibilities, then find a distinction PW currently asks a reader to make, a representation it maintains, or a duty it assigns. Choose one whose value can be tested with a small pair of specimens or saved results. For instance, the single-plan and phased inputs put the same operations on either side of a change to a file. They can challenge a proposal that makes the placement of a query implicit. They are available as controls whichever question is chosen. [User responsibilities](docs/REQUIREMENTS.md) · [Paired inputs](docs/guide/USER-GUIDE-PLAN.md#paired-inputs)

1. Run the pair on the released build or inspect identified baseline captures. State what the caller can vary and conclude today. Name an observation independent of the mechanism under study that distinguishes the cases, and the assertion, if any, that checks it.
2. In a disposable branch or worktree remove or collapse the selected distinction. Let the alternative ask less of PW or its caller, even if a former behavior deliberately changes. Exercise both versions on equivalent fixtures under their own build identities. Keep each version's inputs, outputs and outside observations together.
3. Give a reader the results from each version. Which experiments can they still express? Which conclusions can they still reach, which can they reach only by doing more work, and which histories now look alike? For each relevant test that rejects the alternative, identify the lost observation or caller capability it exposes, or the old arrangement it simply requires. Look also for consequential losses that pass the tests.
4. Count any work that moved into defaults, inference, adapters, caller setup, interpretation or recovery. Decide whether to adopt the alternative, narrow it or keep the existing mechanism. Give the pair and the observation that decided the question. Retaining the distinction because it lets a reader tell two histories apart completes the experiment.

Limit the trial to one mechanism and the callers and checks needed to judge it. Review any adoption and its compatibility costs separately on those results. The 0.3.9 milestone is the investigation and decision. It has no deletion quota.

## The command-line transition (“0.4.0”)

Start with a task from the guide. Let the reader try it with the installed executable, then compare what they could discover, run or establish with what the guide had to tell them. Use the existing worked cases first.

| Reader's task | What to try | What belongs in the guide |
| --- | --- | --- |
| Find out whether a finished experiment can contain a failed open | Ask `help result` about completion and read a saved result with a failed worker open. Check whether the build makes both answers findable. | Why the worker observation matters for this question |
| Produce a specimen this build can run, then read a file of my choosing | Get the complete specimen from `example`. Use `test-input read` with an absolute target, inspect its query and attempt, and pass it to ordinary `run` against known fixture bytes. Look for any option, field or JSON the reader still has to copy from prose. | How to choose a target and use independently known bytes to judge the read |
| Tell a colleague what changed between two saved runs | Use the four file-open results in the compare study. Identify the operand, published outcome and fields that support each answer. Try a reused step ID with a different operand. | Why the chosen pair is a control and which causal claim remains open |

Move a lookup or recipe when the reader can recover it from the executable and use it successfully. Follow friction back into the app. For example, ask what the reader expects `test read` to do before showing its proposed help. If they expect it to open the file, inspect the name, help and output alongside the form that actually runs a specimen. Record the change that resolves the confusion, or why the distinction deserves to stay. [Interface definitions](controller/interface/README.md) · [Guide review methods](docs/guide/USER-GUIDE-PLAN.md#ways-to-make-progress)

- **Examine `compare` as a verb.** Start offline with the saved envelopes. Settle the question, supported inputs, output, refusals and what a program such as PAWL could consume. A reader should be able to point from a reported difference back to the observation in each file. Record the first useful comparison or the reason to defer it. [Compare investigation](controller/src/COMPARE-PLAN.md)
- **Rename `test-input` to `test`.** Carry both the specimen-emitting `read` form and the executing `run` form through the public entry point. Inventory current callers and scripted examples, including the guide's worked cases, before choosing whether to retain the old spelling for a transition or make an announced break. Update dispatch, help, inventory, caller-facing contracts and guide examples together. Exercise emission into ordinary `run` and the experimental-control route, and check the chosen behavior for the old spelling. Named examples and `test read` both print a build-bound specimen for the reader to edit; decide whether they should converge. [Current forms](controller/README.md#cli-surface-contract) · [Interface inventory](controller/interface/README.md)
- **Feed what the reader found back into the contract and guide.** For each changed meaning, identify the authored statement, an observation or refusal that distinguishes it, and the user requirement or passage it affects. Use an existing case when it already makes that distinction. The guide work already recommends a distinct operation to check a repaired specimen before authorizing its effects. Its owner plan carries the prototype results and the production questions into the next scope decision. [Contract owners](docs/contract/README.md) · [Admission study](runner/Sources/ADMISSION-CHECK-PLAN.md)

## 0.4.0 Test Atlas

Construct the initial Atlas alongside the command-line transition. Let the maintainer enter through a question, inspect the underlying observations, and see where an experiment or its checker failed to establish what we credited to it. Pair a demonstrated correction with a limit a reader can still challenge. Use the released build as a dated baseline when CLI spellings or evidence change. [Atlas build plan](tests/atlas/ATLAS-BUILD-PLAN.md)

The accepted pytest work can proceed independently of both releases. Its archive reader and per-family shared blob store keep collection checks and per-item source observations. The Atlas can read existing evidence without either change. [Pytest evidence plan](tests/PYTEST-EVIDENCE-PLAN.md)

# Release staging through the command-line transition

This plan coordinates the move to five main verbs, `run`, `test`, `help`,
`guide` and `example`, around 0.4.0 and through internal 1.0. The
[design philosophy](docs/PHILOSOPHY.md) explains their jobs. The
[controller reference](controller/README.md#cli-surface-contract) describes
what a caller can invoke today.

## 0.3.8 (published)

The release traced and reorganized the public contract, separated experimental controls from ordinary requests, revised how the harness reports observations and judgments, and shipped the standalone guide with six rerunnable cases. The signed ZIP passed release acceptance. The annotated tag is `v0.3.8`. [Public contract](docs/CONTRACT.md) · [Worked cases](docs/guide/README.md#worked-cases)

## 0.3.9: a runnable extension example from `example`

`example extension` prints a build-bound specimen with an issuer and two readers. The fixed target is `/private/etc/hosts`. The [guide passage](docs/PolicyWitness.md#which-reader-received-the-file-grant) uses two jq assignments to retarget a copy to a file the reader prepared. Moving the grant changes the transfer recipient and the actor responsible for consumption and release. The read steps and policies stay fixed. [Worked case](docs/guide/README.md#worked-cases) · [Paired inputs](docs/guide/USER-GUIDE-PLAN.md#paired-inputs)

The [example statement](docs/REQUEST.md#contract-request-specimen-emit_example) covers both invocations. The emitting build's ordinary `run` admits each printed document. `help example` lists the invocation for each specimen with its actors, phases, steps, queries, attempts and extension actions. The interface inventory names every document member the card leaves out. An unknown name or extra operand exits 2. [Release notes](docs/releases/0.3.9.md)

For release verification, run both [unchanged round trips](tests/suites/witness_contract/README.md#the-apps-own-example) and the [extension controls](tests/suites/witness_contract/README.md#native-extension-boundaries). The latter give Alice access before consumption and require the access check to detect her successful baseline read even though issuance and delivery still succeed. Reproduce the guide passage on the signed app and verify that moving the grant switches which reader opens the sampled file. The [interface routes](tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards) cover the help card, operand and refused tails.

## 0.3.9 runner help and recovery

A reader has just run `runner remove`. It exited 0. Can they discard the staged bundle? Today `help runner` falls back to the base help card. Invoking `runner` without a subcommand prints its syntax on stderr. The answer depends on `data.cleanup_retained`, which can be true even at exit 0. The 0.3.8 guide gives the recovery procedure at the point of use. [Guide recipe](docs/PolicyWitness.md#use-an-external-runner) · [Registry ownership and recovery](controller/README.md#registry-ownership-and-recovery)

Add a `runner` topic discoverable from base help. Draw the subcommand names and accepted selectors from definitions shared with dispatch and argument parsing. Distinguish registry inspection, verification with a fixed request and operations that change recorded state. For a pending cleanup, the reader needs to find the retained record, inspect service and plist ownership with `runner reconcile`, and recognize when to retry `runner remove` using the recorded selector. Displaying help should require no registry or installed service. [Runner dispatch and usage](controller/src/runner_commands.rs) · [Help card renderer](controller/interface/README.md)

Take a selector from the card through the existing recovery fixture. Check which recorded installation removal acted on and which service and plist the fixture subsequently observed. Mutate a governing spelling once, leave the card specification alone and inspect what moved in both help and dispatch. Then try the card with two saved removal results. Both report `ok` and exit 0. One confirms cleanup and the other retains it. Can a reader starting with the executable and each result decide whether to keep the bundle and name the next command, if one is needed? Defer a fuller worked recovery example until the card supports that decision. [Recovery controls](tests/suites/runner_byoxpc/opt_in/registry_recovery.py) · [Retained cleanup](docs/RESPONSE.md#contract-installation-commands-recovery)

## 0.3.9 subtractive experiment

Choose one question when the investigation starts. Read the released guide and caller responsibilities, then find a distinction PW currently asks a reader to make, a representation it maintains, or a duty it assigns. Choose one whose value can be tested with a small pair of specimens or saved results. For instance, the single-plan and phased inputs put the same operations on either side of a change to a file. They can challenge a proposal that makes the placement of a query implicit. They are available as controls whichever question is chosen. [User responsibilities](docs/REQUIREMENTS.md) · [Paired inputs](docs/guide/USER-GUIDE-PLAN.md#paired-inputs)

1. Run the pair on the released build or inspect identified baseline captures. State what the caller can vary and conclude today. Name an observation independent of the mechanism under study that distinguishes the cases, and the assertion, if any, that checks it.
2. In a disposable branch or worktree remove or collapse the selected distinction. Let the alternative ask less of PW or its caller, even if a former behavior deliberately changes. Exercise both versions on equivalent fixtures under their own build identities. Keep each version's inputs, outputs and outside observations together.
3. Give a reader the results from each version. Which experiments can they still express? Which conclusions can they still reach, which can they reach only by doing more work, and which histories now look alike? For each relevant test that rejects the alternative, identify the lost observation or caller capability it exposes, or the old arrangement it simply requires. Look also for consequential losses that pass the tests.
4. Count any work that moved into defaults, inference, adapters, caller setup, interpretation or recovery. Decide whether to adopt the alternative, narrow it or keep the existing mechanism. Give the pair and the observation that decided the question. Retaining the distinction because it lets a reader tell two histories apart completes the experiment.

Limit the trial to one mechanism and the callers and checks needed to judge it. Review any adoption and its compatibility costs separately on those results. The 0.3.9 milestone is the investigation and decision. It has no deletion quota.

## 0.3.9 early Test Atlas investigation

Use the four retained file-open runs, then one harder pair, to ask what conclusion can slip past tests of the individual runs. Give the 0.4.0 Atlas the independent observation, what the checker actually established and the remaining limit or repair. The Atlas owns the investigation. [Comparison study and fixture account](tests/atlas/COMPARE-PLAN.md)

## The command-line transition (“0.4.0”)

### Keep ordinary execution as the reference

`run` admits and executes the caller's specimen. Preserve the result of the
instrument alongside each available query and attempt, including the source
of a synthetic result, the scope of a refusal and what remains unknown.
Use three existing cases while changing the entry points.

- Run the emitted example unchanged through ordinary `run`. Observe the
  process exit and `finished` result alongside the worker's failed open.
  [Example workload](tests/suites/witness_contract/README.md#the-apps-own-example)
- Use the crossed-read case with equal bytes on distinct inodes. Read the
  validator's operation and operand separately from the worker's attempted
  path. The outside descriptor samples distinguish which object the worker
  opened. Keep a deliberate mismatch expressible. [Crossed reads](tests/suites/witness_contract/README.md#controlled-read-input)
- Use the interruption before slot publication to expose an effect whose
  return PW cannot report. Compare the absent name before the run and the
  file afterward with the worker's last progress and missing publication.
  Keep the later unreached step distinguishable even if its query ran.
  The intervention needs the test entry and the file needs an outside
  observer. Both establish the limits of ordinary evidence. [Publication case](tests/suites/witness_contract/check_killed_before_publication.py)

### Make `test` the runtime entry for tests

Rename `test-input` to `test`. Keep `test read` as a specimen emitter and
`test run` as execution. Try the names with a reader who wants to open a
file they prepared. Have them inspect the printed target, run the specimen
and check the bytes. If named examples can serve the emitter's callers,
use this trial to decide its eventual home. Inventory scripts, adapters,
guide blocks and contract statements before deciding whether the old spelling
gets a transition alias or an announced refusal. Exercise both spellings
according to that decision. Change dispatch, help, the interface inventory,
authored contracts and the guide's actual commands together. [Current forms](controller/README.md#cli-surface-contract)

Keep one production path for request preparation, admission, orchestration,
reply admission and result selection. `test` owns the declared interventions.
Deliver them beside the held specimen through the existing experimental
submission. Resolve one existing admission difference explicitly. Ordinary
`run` admits two executable substitutions in `_test_overrides`, each on its
own specimen form. The experimental submission refuses a nonempty block even
with no control flags. Identify the callers of each substitution, decide its
declared route under `test` and check both forms' admission or refusal through
both entries. Record any break and the caller's migration. [Admission of controls](docs/REQUEST.md#contract-request-overrides-experimental)

Migrate the shared invocation adapter and its callers, then examine the
remaining runtime calls in the suites. Where a case substitutes equipment or
changes timing to investigate a decision PW made, identify who made the
decision and what could show it taking effect. Expose the needed choice at
`test` when PW owns it. Default specimen execution in tests to `test run`,
including the empty-control form. Keep a different entry where the case can
name the fact it establishes there. The example round trip promises admission
by ordinary `run`. A fractional integer control must reach the host decoder
to test its refusal there, so submit it via the client's controls object.
Either entry can run alongside an independent filesystem or process observer.
Keep that observer with its fixture and retain its raw samples.
[Seam invocations](tests/README.md#seam-invocations)

The controlled-submission and dispatcher cases give the renamed entry three
distinct checks.

- Submit identical ordinary specimen bytes with matching initial conditions
  through `run` and empty-control `test run`. Compare admission, effective
  allowances, query collection, attempted operation, observed bytes and
  application result. Account for the distinct submission and empty control
  echo, and for per-run identities and times. Include a refused specimen to
  catch divergence before execution.
- For `--worker-timeout-ms` below the ordinary worker's floor, inspect the
  submitted value, the host's actual wait budget and the observed deadline
  on the delayed worker.
  Contrast a kill slot that the worker reaches with one outside its plan.
  An echoed value can survive an unreached boundary. Use the adapter's record
  for the request, the host budget for the effective setting and the worker's
  progress and reaped status for what happened at the slot.
  [Submission, echo and intervention cases](tests/suites/witness_contract/README.md#submissions-with-test-input-run)
- Carry a deliberately induced client timeout through harness reporting. Keep
  the application's `xpc_timeout` and the independently observed aftermath.
  Obtaining the promised observation can complete the case with no favorable
  judgment. Exercise enforced and advisory unfavorable judgments and completion
  without a judgment using the existing dispatcher controls. Check which
  blocks acceptance. Withhold required evidence or fail cleanup and check
  that the failure and earlier observations both survive. Decide here which
  facts PW can report about execution and which the harness must supply
  about setup, collection, judgment authority, command failure and
  cleanup. [Timeout observations](tests/suites/run_effects/README.md#aftermath-footprint) · [Outcome accounting](tests/README.md#declared-observations-and-judgments) · [Dispatcher controls](tests/suites/dispatcher/README.md)

### Derive help from the decisions the build makes

Use the governing command, form, option and result declarations for dispatch
and for typed card references. Enumerate the changed forms and consequential
choices, including refused or discarded inputs where applicable. Keep
`help result` addressable from the execution topics. List the five main jobs
in base help and keep discoverable supporting topics for `runner` and build
identity. Keep `runner` as the management entry for installing, inspecting,
verifying and recovering a service. Keep `version` and `--version` as direct
lookups for scripts and callers matching artifacts to a build. A help lookup
for either operation should display its interface without performing it.
[Interface declarations and inventory](controller/interface/README.md)

Apply a spelling or value change to a governing declaration in a disposable
build, keeping the card input fixed. Record which advertised words and
executions change using the existing mutation and literal-expectation cases.
Follow an advertised `--runner-mode` value past argument parsing. With an
admissible specimen and no external selector, `standard` should reach the
built-in service and `byoxpc` should refuse the missing selector before
invocation. With an eligible installed selector, identify the selected service
and worker using the BYOXPC fixture and its independent equipment read-back.
A test that stops at “missing request” would miss a flag discarded after
parsing. [Interface verification](tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards) · [Selector precedence](docs/REQUEST.md#contract-request-options-precedence) · [Equipment read-back](tests/suites/runner_byoxpc/opt_in/entitlement_readback.py)

A card prints only spellings and values taken from definitions, so no card
can yet say what happens to an input the command refuses or discards. The
`example` card is the case to return to. It lists both invocations and what
each specimen does. An unknown name, an extra operand or a non-UTF-8 argument
exits 2 with empty stdout, and `tail.example`, the entry that records that
refusal, appears on no card. Decide how a card states a refusal or a discard
without wording of its own. Then start a reader at `help example` and ask
what `example extensions` will do. Compare the answer with the corpus cases
for those three tails. [Entries no card references](controller/interface/residue.json) · [Refused tails](controller/integration/interface_cases.json)

### Ship the authored guide through the app

Bare `guide` emits the full release Markdown. `guide <verb>` retrieves the
authored section under that verb's heading in the same document. Keep the
web-published guide and release asset usable on their own. Implement the
section boundaries, offline app delivery, signed byte comparison and topic
refusals in the [guide plan](docs/guide/USER-GUIDE-PLAN.md#deliver-one-authored-guide).
Reproduce the release's worked cases, including the extension passage, and
ask a reader to transfer a lesson to a different operand or fixture and
explain their next action. Record delivery and editorial findings separately.
[Teaching trial](docs/guide/USER-GUIDE-PLAN.md#review-the-teaching)

### Investigate a read after release in the extension example

`example extension` ends with the release action. The contract's teaching
schedule continues with a fresh read after release, and the guide says that
testing later access takes another open. The build's specimen makes neither
observation. Before adding those reads, establish what PW can say about
them. The lifecycle control accepts either result after a successful release.
In development runs on macOS 26.7.1 (25G241) the reader's query returned
`deny` and its fresh open failed again. Repeat that with the emitted specimen
for both readers. Vary what could keep access alive: a second handle consumed
from the same delivery, and a descriptor opened before release. Then decide
whether the specimen gains reads after release with a stated result, gains
them as observations with no claimed result, or keeps its present stop. A
change to the specimen also changes its help card, round trip and contract
example. [Before, during and after consumption](docs/REQUEST.md#contract-extensions-examples-before_during_after) · [Lifecycle control](tests/suites/witness_contract/check_extensions.py) · [Guide passage](docs/PolicyWitness.md#which-reader-received-the-file-grant)

### Find the applicable release contract during normal use

The five projections together must make the application's observable contract
details discoverable during normal use, with enough precision to understand
the applicable conditions and limits. Use the spellings a caller sees in an
emitted example, accepted input, option, control, refusal, reported field or
outcome as lookup keys in help. Show the reader how to follow one in a guide
case. Keep public meanings in the authored surface tree.

Use its node IDs, existing interface associations and presentation map to
put links to the tagged release's complete statements beside relevant help
entries. Where an association is missing, select the appropriate authored
node after reading its conditions. A release app can print these references
without a checkout or a live lookup. Keep detailed reference material in the
published contract and interpretive teaching in the guide.
[Contract owners and placement](docs/contract/README.md) · [Interface associations](controller/interface/README.md#joins)

Try these routes with the release app, the supplied result or specimen and
its published material. Start the reader at the observed fact, without a
source path or a contract identifier.

1. From `finished` beside a failed open, use `help result` to find result
   selection and the step's source. Can the reader explain the process exit,
   whose open failed, when the prediction was collected and what would be
   needed to attribute the failure? [Finished run with a failed attempt](docs/RESPONSE.md#contract-envelope-data-failed_attempt) · [Scope of query order](docs/RESPONSE.md#contract-steps-comparison-order)
2. From the requested kill slot, use `help test` to find its default when
   omitted, its per-worker scope and its place relative to result publication.
   Given the one-step run with an out-of-plan slot, can the reader decide
   whether it could have acted, even with the requested value in the reply?
   [Slot applicability](docs/REQUEST.md#contract-request-overrides-worker_kill_before_publish_slot)
3. From `cleanup_retained` at exit 0, use `help runner` to find the conditions
   for retirement. Can the reader use the retained identity, warnings and
   service/plist observations to decide what must be kept and when removal
   can be retried? [Cleanup field](docs/RESPONSE.md#contract-installation-cleanup-cleanup_retained) · [Recovery](docs/RESPONSE.md#contract-installation-commands-recovery)

Review the answer reached, including applicable defaults, limits, order,
provenance, uncertainty and caller consequences. A resolved link checks an
address. If the statement reached leaves the reader guessing, repair the
route or its owner and try the decision again. Removing redundant tracing is
worthwhile where it helps a caller. The acceptance evidence is the decisions
callers can now make. Keep an unresolved product question with its owner,
such as checking a repaired specimen before authorizing its effects. That
study retains its prototype, production costs and scope decision. [Admission study](runner/Sources/ADMISSION-CHECK-PLAN.md)

## 0.4.0 Test Atlas

Construct the initial Atlas alongside the command-line transition. Let the maintainer enter through a question, inspect the underlying observations, and see where an experiment or its checker failed to establish what we credited to it. Pair a demonstrated correction with a limit a reader can still challenge. Use the released build as a dated baseline when CLI spellings or evidence change. [Atlas build plan](tests/atlas/ATLAS-BUILD-PLAN.md)

The accepted pytest work can proceed independently of both releases. Its archive reader and per-family shared blob store keep collection checks and per-item source observations. The Atlas can read existing evidence without either change. [Pytest evidence plan](tests/PYTEST-EVIDENCE-PLAN.md)

## Internal 1.0 completion

Use the 0.4.0 implementation and Atlas findings to finish the transition.
Revisit outstanding cases where a caller could reach the wrong conclusion,
a test needed an undeclared choice or a published contract was hard to
find. Close them at their owners with the distinguishing observation or
reader trial above. Internal 1.0 marks maturity of the instrument, including
its ability to report the limits of an observation.

**Migrate the philosophy into the root README late.** Once the five jobs can
be described from implemented behavior and the preceding verification,
integrate the durable substance of the [philosophy](docs/PHILOSOPHY.md) into
the [root README](README.md). Explain what PW is and how its main interface
fits together.
Replace “The Experiment” framing and remove the word “experiment” throughout
that README. Use settled language and keep the unitary web-published guide
prominent. Retain the limits on attribution, prediction and inference from
missing observations. Review the account against the worked cases, control
observations and release reading paths, including a conclusion PW cannot
establish. Check the README's wording and links, remove transition-only
text, retire the standalone philosophy and update every incoming link to
its new home. Git retains the transition version.

**Hand off maintainer responsibilities.** During that same late review,
refresh the [change responsibilities plan](docs/CHANGE-RESPONSIBILITIES-PLAN.md)
with the implemented interface, actual breaks and preserved uses, release
evidence and caller actions. Its follow-on deliverable is
`docs/CHANGE-RESPONSIBILITIES.md`. Use the rename, named example and
evidence-meaning cases to settle what maintainers and publishers owe before
shipping either kind of change and what users of saved artifacts can expect.
Any stability, notice, migration or deprecation commitment at internal 1.0
must be made explicitly through that work.

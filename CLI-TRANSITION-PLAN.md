# Release staging through the command-line transition

This plan coordinates the move to five main verbs, `run`, `test`, `help`,
`guide` and `example`, around 0.4.0 and through internal 1.0. The
[design philosophy](docs/PHILOSOPHY.md) explains their jobs. The
[controller reference](controller/README.md#cli-surface-contract) describes
what a caller can invoke today.

The [limits review](docs/LIMITS-SURFACING-PLAN.md) groups the full inventory
by caller question. Review the proposed help, guide, example and result
changes together before selecting any for implementation or release staging.
Before releasing 0.3.9, classify the bounds on equipment error domains
and diagnostic messages. Record what survives shortening in each field. Ship one guide section on timing, retire
“How long does a run take?” from QUESTIONS, and verify the clocks and
reported outcomes against the implementation and its tests. [Limits review decisions](docs/LIMITS-SURFACING-PLAN.md#record-the-decisions) · [Guide timing work](docs/guide/USER-GUIDE-PLAN.md#timing-in-039)

## 0.3.8 (published)

The release traced and reorganized the public contract, separated experimental controls from ordinary requests, revised how the harness reports observations and judgments, and shipped the standalone guide with six rerunnable cases. The signed ZIP passed release acceptance. The annotated tag is `v0.3.8`. [Public contract](docs/CONTRACT.md) · [Worked cases](docs/guide/README.md#worked-cases)

## 0.3.9: a runnable extension example from `example`

`example extension` prints a build-bound specimen with an issuer and two readers. The fixed target is `/private/etc/hosts`. The [guide passage](docs/PolicyWitness.md#which-reader-received-the-file-grant) uses two jq assignments to retarget a copy to a file the reader prepared. Moving the grant changes the transfer recipient and the actor responsible for consumption and release. The read steps and policies stay fixed. [Worked case](docs/guide/README.md#worked-cases) · [Paired inputs](docs/guide/USER-GUIDE-PLAN.md#paired-inputs)

The [example statement](docs/REQUEST.md#contract-request-specimen-emit_example) covers both invocations. The emitting build's ordinary `run` admits each printed document. `help example` lists the invocation for each specimen with its actors, phases, steps, queries, attempts and extension actions. The interface inventory lists the scalar paths the card omits from each source template. The emitter adds the build’s `contract` field when it prints the specimen. An unknown name or extra operand exits 2. [Release notes](docs/releases/0.3.9.md)

Include `extension.target` in the 0.3.9 extension-field help review. A 512-byte path in the guide edit fits the issue target and exceeds both the read target and the query filter. Check that a caller can follow the indexed refusal to the applicable bound. [Limits review](docs/LIMITS-SURFACING-PLAN.md#record-the-decisions)

For release verification, run both [unchanged round trips](tests/suites/witness_contract/README.md#the-apps-own-example) and the [extension controls](tests/suites/witness_contract/README.md#native-extension-boundaries). The latter move the grant to Bob and expect the open to move with it. Three controls keep issuance, delivery, consumption and release successful while access does not follow the grant: Alice can already read, Bob's policy has no extension rule, and the grant names another file. Reproduce the guide passage on the signed app and verify that moving the grant switches which reader opens the sampled file. The [interface routes](tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards) cover the help card, operand and refused tails.

## 0.3.9 runner help and recovery

Base help lists `runner`. Its card distinguishes registry inspection, a fixed verification request and commands that change recorded state. The subcommand names and both record selectors come from the declarations dispatch and parsing use. Help works with an unreadable registry and no installed service. [Controller reference](controller/README.md#registry-ownership-and-recovery) · [Interface definitions](controller/interface/README.md)

A successful `runner remove` can leave cleanup pending. On `data.cleanup_retained: true` the reader keeps the bundle and ownership record, finds the pending record with `runner list`, and inspects service and plist ownership with `runner reconcile`. Once the resources are owned or absent they can retry removal with the recorded ID or service name. On `false` the service and plist were observed absent and the cleanup update was saved. The reader can discard staging. [Guide recipe](docs/PolicyWitness.md#use-an-external-runner) · [Removal contract](docs/RESPONSE.md#contract-installation-commands-recovery)

The recovery fixture saves both exit-0 results. It takes the ID invocation from the card, retries the intended record and checks service and plist absence alongside a second installation's surviving record and plist. The spelling mutation checks that changing the ID option moves both the card and the argument that reaches lookup. [Recovery controls](tests/suites/runner_byoxpc/opt_in/registry_recovery.py) · [Mutation observations](controller/interface/mutations.json)

## 0.3.9 subtractive experiment

Keep the two record selectors for `runner status`. The v0.3.8 binary and a signed positional-key trial read the same private registry. When one record's ID was another's service name, `--id` returned the first bundle and `--service-name` returned the second. The trial returned both unique lookups correctly and refused the shared text as ambiguous. The caller could recover either record by listing the registry and filtering the intended column. That moved the selection into caller code. Four integration tests rejected changes to syntax, diagnostics or the paths they exercised. The paired lookup exposed the lost ability to select directly. [Experiment, captures and decision](records/039-status-selector/README.md)

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

Revisit `test_override_path` when moving `test-input` to `test`. Decide whether the current 1,023 UTF-8 byte ceiling and the admission and refusal-echo behavior suit the worker path, each actor equipment role and the validator flag. Compare an oversized path whose echo is withheld with an exact-fit missing executable that reaches spawn or equipment preparation. Use that comparison to decide what to retain or change, then check the agreed `help result` lookup against the resulting refusal fields. [Current override rules](docs/REQUEST.md#contract-request-overrides) · [Path boundary cases](tests/suites/failure_boundaries/check.py)

Review `--worker-pre-ready-hang-ms` and `--worker-post-apply-hang-ms` at the same time. Today the host forwards 60,001 ms and the worker rejects it before setup. Decide whether `test run` should reject it earlier and where the caller would see the evidence. Write one help entry for the two flags after that decision. [Current delay controls](docs/REQUEST.md#contract-request-overrides-worker_pre_ready_hang_ms)

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

During 0.4.0, decide whether the 256-byte prefix retained from a rejected validator frame belongs in the limits inventory or has another role in the result contract. Write `help result byte_limit` alongside that decision. Compare a partial line discarded at the collection cap with a complete malformed line that reaches the decoder, and check the earlier verdict retained in each case. [Limits review](docs/LIMITS-SURFACING-PLAN.md#record-the-decisions)

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

During 0.4.0, compare the four retained file-open runs, then examine when the host cleared its copy of an extension token. For each comparison, identify the independent observation, the assertion the checker made and any conclusion the evidence still leaves open. Use the token comparison in the Atlas custody section. [Comparison study and fixture account](tests/atlas/COMPARE-PLAN.md)

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

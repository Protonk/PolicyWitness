# Plan: The Worker — Instrument and Constraints

## Status

No pass has started. The plan is grounded at `e901fc0`. Worker, host and
helper sources there are those of v0.3.1, since `6fd9f06` and `e901fc0`
changed only this file. The uncommitted BYOXPC investigation files and catalog
additions in the working tree are not evidence for this plan. The seed register
was surveyed from source at `e901fc0`; cited runtime cases were inspected, not
rerun.

At the end of every pass, update this section with the pass reached, the
register rows opened and closed, and the commit holding the pass's work.

## What this plan produces

`docs/WORKER.md`, titled **The Worker: Instrument and Constraints**, is the
third developer tour beside [ARCHITECTURE.md](ARCHITECTURE.md) and
[BUILD.md](BUILD.md). Its organizing question is: **what can the worker carry
across the sandbox boundary without compromising the experiment?** It is
written for a contributor who has read the repository README, needs to judge a
proposed worker change, and does not need PolicyWitness sold to them. It is
organized by resources and the authority they carry, not by time or source
file. A generated capability map is its principal figure.

Writing the document is also an assessment of the worker, as writing the
architecture and build tours assessed the run and the build. An accurate
account of an awkward instrument contains awkward sentences. A sentence that
is hard to write, or a generated row the prose cannot agree with, is how a
defect is found. The precedent is `63927cd`. The architecture plan's account
of the worker before apply had to say that it created exec pipes under a
descriptor budget. The premise behind that was false. Moving the pipes inside
the attempt removed the budget, its limits and seven harness cases.

The work proceeds in passes. Each finding is recorded in the register, decided
by the user, then fixed or accepted, and finally re-proved in the text.
Production changes happen only through adjudicated rows, in their own commits.
The writer never repairs the implementation to make a sentence true.

## How the assessment works

### The scope rule

Every sentence in WORKER.md states what the worker does, at a scope where it
could be wrong: what it holds, when it acquires it, what it publishes. When the
true scope needs an exception, the sentence carries the exception, and the
exception opens a register row. No hard sentence is dropped. None is softened
into a negative ("does not establish …") or moved elsewhere to avoid it.

Negative statements have two homes in the document. A Known gap paragraph
records a guarantee the user has accepted as incomplete. A link to the owning
contract says what a field does not mean. The guarded qualifications in this
plan are working material for the register, not the document's register. A
responsible reader, perhaps superintending their own fork, can tell from
accurate positive claims what PolicyWitness is not.

### Evidence

Keep three kinds of evidence distinct:

- **Mechanical grounding:** a cited symbol exists, a test is defined, a
  generated region is current. It detects drift; it does not establish
  behavior.
- **Assertion coverage:** what a cited check actually asserts, in which
  configurations, and what it leaves untested. A suite's name or a passing run
  is not coverage evidence.
- **Observed behavior:** a recorded probe or case reaches the path and
  observes the effect. It holds for the revision, inputs and environment
  exercised. A cited case is not a freshly executed case.

Mark source-only conclusions as such.

### The register

Each row moves through `open → investigating → awaiting adjudication →
implementing → validating → closed`. The user decides each disposition:

- correct the document, including a source comment;
- fix the worker or host;
- strengthen verification;
- accept a limitation, written as a Known gap;
- intended behavior that needs explaining.

A row can carry more than one disposition. A documentation-only resolution
skips implementation but not validation. Reopen a row when new evidence
contradicts its decision or a change invalidates the evidence it rested on.

Give each investigated row a detail entry under its number, below the register
table:

- the sentence as it first had to be written, and the claim it was reaching for;
- implementing symbols, cited checks and what they assert;
- the hypothesis and the observation that would refute it;
- for any probe, its exact inputs, expected and actual results, and evidence
  path;
- the recommended disposition with its reasoning, the user's adjudication and
  the scope of any authorized change;
- the validation, and the sentence after the change.

The before and after sentences are the re-proof. A row closes when the
document says something accurate about the changed or accepted instrument.

A broad suite passing does not discard a counterexample. Weakening a promise,
adding a prose baseline exception, or narrowing a check merely to make the
document and tests agree is an adjudication, not an edit.

### Changes a row authorizes

A fix keeps a failing reproduction and adds a regression control that
distinguishes the defect from the fix. It lands in its own commit, naming the
row number.

Changing worker or host source means regenerating the worker identity
(`python3 docs/generate_worker_identity.py`) before building, making a signed
build, and running the exact cases that cover the changed path. Changing the
phase wait, the release store or query eligibility also requires
`witness_contract/order_barrier_mutations`. Follow
[the maintenance checklist](../AGENTS.md#maintenance-checklist-when-changing-things)
for request, evidence or layout changes. A change that would alter the wire
contract goes back to the user as separate scope.

## Editorial decisions

Organize the account around three experimental roles: **prepared reporting
apparatus, deliberately supplied authority, and resources acquired by the
attempted operation**. Evidence that arrives from outside the worker forms a
fourth group. The roles describe what a resource is for in the experiment.
They do not claim that reporting apparatus carries no authority or has no
effects. Membership is a finding, not a premise: a resource that fits no role,
or two, is drawn outside the role clusters and opens a row.

- Treat the boundary as policy application inside an already-running process.
  The worker already has executable code, native libraries, memory and process
  context. A fresh worker is not an empty process. Later phases use the same
  applied worker and can observe effects of earlier actions.
- State the post-apply surface at its actual extent. Where PolicyWitness's own
  post-apply calls allocate, open or create something, say so. Where a
  library's internal behavior is unobserved, name the call and say its
  internals are unobserved.
- Use ordinary file access, exec and an explicit extension experiment as the
  principal examples. Include Mach lookup and sysctl in the inventory without
  expanding into a catalogue of sandbox operations.
- Explain ordering as a condition of meaningful comparison. Link to the
  architecture tour for the protocol and the evidence contract for
  eligibility. A release ordinal is not a verdict delivered to the worker.
- Separate intentional ignorance from missing evidence. The worker
  deliberately does not classify prediction/enforcement agreement, while an
  unpublished native result is unavailable evidence. Neither licenses an
  inferred cause.
- Describe current behavior. Source comments are leads, not evidence; a stale
  comment is itself a register row.

## The inventory

Pass 1 builds an inventory of everything the worker holds or acquires. It is
complete over PolicyWitness's own call sites, from the host's spawn
preparation in [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) to
the worker's exit, including the extension issuer's path into the worker.

"Acquires" means creating or receiving any of:

- memory or a mapping;
- a descriptor;
- a Mach port or right;
- a process;
- authority: entitlements, policy, an extension token.

The inventory also covers what the worker receives without asking: inherited
descriptors, spawn attributes, environment and process context.

| Column | Records |
| --- | --- |
| Resource | What is held, named as the source names it |
| Acquired by | Process and call site (symbol) |
| When | Before compilation; between compilation and apply; after apply within an attempt; after apply outside an attempt |
| Held across | The attempt only; later attempts in the phase; later phases; until exit |
| Released | Call site, or at exit |
| Authority | What the resource lets the worker do that it otherwise could not, or none |
| Sandbox-gated | Observed (cite the case), source-only, or unknown |
| Role | One of the three roles or external evidence; none or several opens a row |

Call-site completeness does not reach library internals, such as what
`sandbox_compile_string`, the extension routines or libc formatting allocate.
Record the call and mark its internal behavior unobserved, unless a source or
probe establishes it.

Draft the inventory as a working table in a section of this plan. In pass 2 it
becomes the map's manifest nodes, and then the working table is deleted,
because the manifest owns it.

## Register

The seed rows come from the planning survey. Their evidence is what the survey
saw at `e901fc0`, source-only unless noted, and should be verified before
deciding. None is adjudicated. Later rows are added as passes find them.

| # | Candidate | Survey evidence | State | Disposition |
| --- | --- | --- | --- | --- |
| 1 | The worker's launch is not isolated the way its children's are | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) calls `posix_spawn` with file actions for fds 0, 3, 4 and optionally 5, no spawn attributes and a nil environment. The issuer ([`ExtensionSession`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift)) and exec children ([`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c)) set `POSIX_SPAWN_CLOEXEC_DEFAULT`. Which other host descriptors the worker inherits (stdio included), and what the nil environment yields, is unobserved; the dossier records neither. | open | |
| 2 | Pre-apply descriptors stay open after apply | The worker does not close the policy descriptor, the shared-region descriptor or the ready pipe after use, so all three are held across apply and every attempt. [`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c) closes the token descriptor after mapping. Exec children do not inherit them. Whether any experiment is affected is undecided. | open | |
| 3 | `open_write` truncates and writes | [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) opens with `O_WRONLY \| O_TRUNC`, writes one byte, ignores the write and close results and reports open success. The guide's [attempt kinds](PolicyWitness.md#attempt-kinds-the-runner-implements) entry says only "exercise file ops on `target`"; the survey found no document stating the truncation. | open | |
| 4 | `open_read` reports open success only | [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) reads one byte, "so the kernel observes the read", and discards the result. `read_fresh` is the action that records a read. | open | |
| 5 | `create` opens an existing file without truncating it | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) uses `O_WRONLY \| O_CREAT` without `O_EXCL`; its comment calls this "semantics callers depend on". The [existing-file create](../tests/suites/witness_contract/README.md#create-on-an-existing-file) case checks bytes and identity. | open | |
| 6 | Exec attempts allocate after apply at PolicyWitness call sites | Since `63927cd`, `exec_resources_acquire` initializes spawn file actions and attributes inside the attempt. On Darwin these are opaque handles whose init functions allocate (verify against the SDK's libc before relying on this). `fail_from_errno` formats with `snprintf` and `strerror` after apply. The [Runner simplicity](ARCHITECTURE.md#principles-as-enforced-constraints) principle names request, evidence and token storage as preallocated; the inventory decides whether that sentence holds at its stated scope. | open | |
| 7 | Worker source comments describe retired premises | The header calls reading the policy into a stack buffer "the LAST allocation attempt before sandbox_apply()", yet parameter creation and `sandbox_compile_string` (commented as allocating internally) follow it. The attempt section says "No allocations post-apply" per "R6". The comments cite R5 and R6, which nothing else in the tracked tree defines, and "the Swift worker". | open | |
| 8 | Two documents will state the private-extension limit | ARCHITECTURE has it as a Known gap under its principles; WORKER.md will state it beside its inventory. Decide which document owns the paragraph and which links to it. | open | |
| 9 | Release is not revocation | [check_extensions.py](../tests/suites/witness_contract/check_extensions.py) permits access after a successful release ("A successful release does not itself require access revocation"); nothing checks revocation. | open | |
| 10 | Exec helpers can outlive the worker | ARCHITECTURE's Known gap covers descendants that leave the child's process group. Worker death during exec can leave helpers alive. This has row 8's ownership question, plus whether to accept it. | open | |
| 11 | The worker's ambient resources are uninventoried | No source or control establishes the full set of descriptors, ports, threads and library mappings the worker holds at apply. Row 1 is the part PolicyWitness controls; this row is the rest. A stronger claim would need an independently observed launch inventory or targeted instrumentation with a stated observation boundary. | open | |

## Passes

Each pass ends with a commit of its work and an update to Status. A pass
marked *stop* ends with a review with the user before the next pass starts.

**Pass 1: inventory** (*stop*). Build the inventory. Recheck the seed rows
against source. Take rows that source can decide to "awaiting adjudication",
with a recommended disposition. Design a probe, with a control that could
refute its hypothesis, only where source cannot decide a row and the answer
would change the document. Write no prose. At the stop, the user reviews the
inventory's scope and adjudicates the rows ready for it.

**Pass 2: map.** Add destination support to the generator with its controls,
as described below. Then add manifest nodes and edges from the inventory and
render. Read the SVG at normal size as an assessment, not just a legibility
check. Look for:

- an edge that implies authority flowing where none does;
- a resource drawn inside a role it only partly fits;
- a node with no path to anything the experiment observes.

Each such reading becomes a row. A matching SVG stamp does not establish
legibility.

**Pass 3: prose** (*stop*). Draft from the section briefs against the map,
under the scope rule. Every hard sentence becomes a row that keeps the
sentence as it was written. At the stop, the user reviews the draft with the
register.

**Pass 4: changes.** Implement the adjudicated rows as described under
"Changes a row authorizes", re-prove each in the document and regenerate. This
pass recurs after any later stop that adjudicates new rows.

**Pass 5: challenge.** Read in both directions:

- from each material claim to its implementation, assertions and observations;
- along the worker from spawn to exit, looking for operations, descriptors,
  branches and failure paths the account omits.

Challenge universal words: "every", "only", "before", "after apply", "fixed",
"fresh". Counterexamples go back to the register, not to the editor.

**Pass 6: plan-blind audit** (*stop*). A fresh agent that has not seen this
plan reads WORKER.md, the map and the cited sources. It reports claims it
cannot support and omissions it finds. Commit the audit prompt as its own file
so the auditor sees a clean tree. Keep the report under `.tmp/audits/`, so
that its numbers do not trip the prose baseline. Findings enter the register
for the user to adjudicate, and pass 4 follows.

**Closeout.**

- Complete the integration work.
- Move the register's substance into a record under `records/`, linked only
  from this plan.
- Delete this plan.

The document is ready to publish when every material claim has a supported
account or an accepted limitation, each implemented fix has its validation,
and no open row could change what the document says.

## Proposed document structure

The writer may change heading wording and paragraph balance. A finding that
the structure itself misrepresents the worker is a register row.

### 1. The experimental question

Introduce the tension between surviving the specimen and staying exposed to
what it tests. Establish the host/worker split briefly. The worker applies the
policy and conducts attempts. The unsandboxed host arranges queries, collects
publications and replies. Explain why opening a target beforehand asks a
different question from opening it under the specimen policy. Place the tour
beside the run and build tours as an account of the instrument, not a
normative contract.

### 2. What the worker holds

The map and the generated inventory tables go here. Prose explains each role
through its principal examples and names the resources that fit no role.

- Distinguish the backing mapping from its descriptor. Results are published
  through mapped memory; the token mapping has different authority, ownership
  and erasure rules.
- State where the policy and ready descriptors stand after apply, as row 2's
  disposition decides, without presenting them as result paths.
- Contrast the worker's launch with the explicit descriptor and
  empty-environment contract for exec children, which excludes the worker's
  reporting descriptor. Row 1's disposition decides how.

### 3. What can become an observation

Explain the operational knowledge the worker needs: attempt kinds and targets,
bounded arguments, phase partitions and ordinals, time allowances, extension
handle state, native returns and publication state. It compiles through
libsandbox; it is not a policy interpreter deciding what should happen. Build
the section on three distinctions:

1. **A native call and a published result.** Progress is a latest atomic
   milestone, not a trace. A pre-call marker establishes reaching that
   boundary, while immutable payload becomes readable only through
   publication. Use the create-then-kill-before-publication control: the
   independently observed file exists while the reply withholds the completed
   result. Explain why reading partially written payload would be wrong.
2. **An attempted operation and the effect recorded.** Contrast `open_read`
   with `read_fresh`, then cover `open_write`, `create`, and an exec child's
   nonzero exit after successful spawning. Rows 3 to 5 settle the wording.
   Link to the action reference for the full catalogue.
3. **Firsthand evidence and external observations.** Predictions originate in
   the validator, and disposition and comparison assembly belong to the host.
   Later path enrichment is a host observation; logs and dossier assembly are
   outside the worker. Neither predictions nor logs become the worker's
   explanation of a failure.

Link to the existing ownership and comparison contracts rather than copying
their tables. Validator queries use no-report mode. Eligible `query_first`
records establish order, not a snapshot. An unchanged path spelling does not
establish an unchanged object.

### 4. Changes that would change the experiment

Short design-review cases. Each names the tempting change, the question it
would answer instead, and the current behavior. The current-behavior column is
a set of claims for pass 5 to confirm, each with its evidence; one that does
not hold is a row. Do not present hypothetical changes as discovered bugs.

| Tempting change | Question it would answer instead | Current behavior to confirm |
| --- | --- | --- |
| Open a target before apply, or keep its descriptor across extension phases. | Use of previously acquired authority rather than fresh acquisition under current conditions. | Fresh reads open and close within each action. |
| Prepare all exec pipes and handles before apply, for reliability. | Moves attempt setup outside the specimen; can hide setup restrictions or exhaustion. | Setup happens per attempt, after apply; descriptor-ceiling and bare-deny controls test different aspects. |
| Warm up an extension by consuming before apply, or hide tokens in reporting state. | Introduces authority before the declared intervention. | Symbols are resolved without calling consume or release; a separate channel carries the token; lifecycle results are published at the requested actions. |
| Retry with a changed path, extra authority or a friendlier policy; reuse a sandboxed worker for a new specimen. | Substitutes changed conditions for the submitted experiment. | No such retry exists; interrupted I/O and process-observation loops do retry within their protocols. |
| Add `exec_baseline` automatically so an experiment runs. | Changes the tested policy; its broad file-read allowance can override the denial under investigation. | Augmentation is explicit and accounted for in the resolved source. |
| Move interpretation or reporting into the sandboxed process, or treat success or missing output as self-explanatory. | Makes replies depend on specimen-controlled communication, or imports unsupported conclusions. | Assembly is external, and missing publication is distinguished from a missing effect. |

Explain the ordering risk briefly. Removing the hold until collection closes
would let worker effects change what supposedly prior queries see. The intact
hold does not freeze external actors, and it does not stop earlier actions
within a phase from changing conditions for later ones.

### 5. Where the instrument stops

Explain how a contributor assesses a new capability. Identify its authority,
its acquisition point, its native observation and publication mechanism, and
an independent control that could falsify the claim. Working rules stay in
AGENTS files.

Limits sit beside the promises they limit. A Known gap paragraph comes only
from a row adjudicated as an accepted limitation. Intentional semantic limits
are explained as behavior rather than labeled gaps. The document ends with
**Known gaps**, indexing those paragraphs in document order.

## The capability map

Add a graph to [architecture.json](architecture.json), routed to WORKER.md and
rendered as `docs/worker-capabilities.dot` and `docs/worker-capabilities.svg`.
The map answers "what kind of resource or evidence is this, and which boundary
does it cross?" It is not a timeline, a sequence diagram or a copy of the
process topology.

- One node per inventory resource. Merge entries only where the inventory
  shows them identical in every column.
- The node facts are the inventory columns. The node's first source cites the
  acquisition call site, so the citation sits next to the claim it most needs
  to support.
- Clusters for the three roles and external evidence, labeled in text as well
  as color. The generator allows a node in at most one cluster and permits
  unclustered nodes. A resource with two roles or none stays outside the
  clusters, and the prose names it.
- Edge kinds by role (prepares, supplies authority, exercises, publishes,
  observes, joins), added to the manifest's shared styles. Edge ids use a
  prefix no other graph uses, such as `W`.
- Draw evidence and token mappings as separate nodes. Make the application
  boundary legible without implying it erases preexisting resources.
- Edges among external evidence join collected evidence. None implies a
  prediction or explanation sent into an attempt.
- Include an accessible description in the document. The caption may promise
  that citations resolve and checks are defined, not that they prove the
  behavior. Use limit placeholders for durations and sizes.

The generator currently admits one destination:
[`load_manifest`](generate_architecture.py) requires an exact set of top-level
keys under schema 2, and `SPAN_DOCUMENTS` names only ARCHITECTURE.md. The
change is bounded:

1. Add an optional per-graph document destination, defaulting to the
   top-level one, and advance the manifest schema. This is not a wire-version
   change. Register the destinations, and keep strict rejection of unknown
   fields, escaping paths and duplicate outputs.
2. Route the new graph to WORKER.md, leaving the existing figures in
   ARCHITECTURE.md. Update rendering, SVG links and tooltips, inventories,
   self-citation exclusions and check/write paths for each destination.
   Validate every document and finish rendering before writing any output.
3. Register WORKER.md for architecture spans. ARCHITECTURE's sentence saying
   how many figures it generates renders the `architecture.graphs` span, which
   counts every manifest graph; revise it to count the figures embedded there,
   using per-graph spans where prose needs counts. Register WORKER.md with the
   limits span owner only if a value is essential; prefer links to limits.
4. Update [architecture controls](../tests/suites/source_drift/architecture.py)
   and [generator ownership controls](../tests/suites/source_drift/generators.py).
   Add passing and rejected controls for:
   - routing;
   - stale regions or figures in either document;
   - invalid destinations;
   - duplicate ownership;
   - broken markers in the second document;
   - a render failure that leaves both documents and all figures untouched.

   Keep idempotence, citation-definition and no-self-citation checks.

ARCHITECTURE's document graph gains the new document and its edges.

## Supporting evidence

Use these anchors when reviewing claims against evidence. Source location,
test definition, controlled interpretation and live observation establish
different things.

| Claim area | Implementation and normative anchors | Controls and their limits |
| --- | --- | --- |
| Prepared mapping, delivery and identity | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift), [`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [internal identity](CONTRACT.md#internal-hostworker-identity). | [C harness](../tests/suites/runner_c_worker_harness/README.md): bare-deny/full-region publication, identity mismatch, NUL and truncated-policy refusals; [ABI suite](../tests/suites/runner_abi_layout/README.md). Tested publication is narrower than universal survival. |
| Publication versus effect | [`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`pw_progress`](../controller/tools/pw_probe_runner/pw_worker_evidence.h), [`buildAttemptResult`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [worker evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract). | [Death before publication](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication) and [its checker](../tests/suites/witness_contract/check_killed_before_publication.py) observe the file effect independently and require withholding its unpublished result. |
| File observations | [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [fresh-read semantics](PolicyWitness.md#extension-and-fresh-read-output). | [Existing-file create](../tests/suites/witness_contract/README.md#create-on-an-existing-file) checks bytes and identity; [extension checks](../tests/suites/witness_contract/check_extensions.py) inspect fresh descriptor identity and bytes. Source establishes which older action returns are discarded. |
| Per-attempt exec acquisition | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`exec_resources_release`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c). | [C harness exec controls](../tests/suites/runner_c_worker_harness/README.md#exec-resources-are-per-attempt), [their assertions](../tests/suites/runner_c_worker_harness/run.sh) and [public exec cases](../tests/suites/runner_use_c_worker/README.md). The descriptor ceiling rules out holding all steps' pipes at once; source establishes placement after apply. |
| Exec-child isolation/lifetime | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [execution limits](LIMITS.md#execution-budgets). | [Inheritance](../tests/suites/runner_exec_inheritance/README.md) contaminates the worker and reads explicit child state; [lifecycle](../tests/suites/runner_exec_lifecycle/README.md) observes processes independently. Neither establishes a clean worker environment or general process-tree containment. |
| Timing and ordering | [`pw_timing_setup`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift), [`buildOrdering`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [ordering evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#ordering-evidence-states). | [Timing controls](../tests/suites/runner_c_worker_harness/README.md#worker-timing-controls) test sampled decisions; [gated effects/external mutation](../tests/suites/witness_contract/README.md#predictions-before-attempts) test observed ordering and snapshot limits. The opt-in barrier mutation control tests detection of bypass. |
| Extension authority | [`ExtensionSession`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift), [issuer source](../controller/tools/pw_probe_runner/pw_extension_issuer.c), [`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [extension evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence). | [Extension boundaries](../tests/suites/witness_contract/README.md#native-extension-boundaries), [native fixtures](../tests/fixtures/extension_controls/README.md) and [fresh-read checks](../tests/suites/witness_contract/check_extensions.py). The live checker permits access after successful release; it does not verify revocation. |
| Prediction and comparison | [`planValidatorQueries`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), [`comparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), [validator source](../controller/tools/sb_api_validator/sb_api_validator.c); [claim/evidence review](../tests/FAILURE-PROPAGATION-CONTRACT.md#claimevidence-review). | [Independent targets](../tests/suites/witness_contract/README.md#independent-prediction-and-attempt-targets), [comparison matrix](../tests/suites/witness_contract/README.md#comparison-matrix) and [unit controls](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift). Constructed records test interpretation, not kernel causation. |
| External observations | [`resolveDisposition`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), [`enrichPathDiagnostics`](../runner/Sources/PWRunnerCore/PWRunnerService.swift), [`attach_sandbox_logs`](../controller/src/run_flow.rs); [ownership](ARCHITECTURE.md#evidence-channels-and-ownership). | [Termination/log correlation](../tests/suites/witness_contract/README.md#termination-and-denial-log-correlation) and [controller ownership](../controller/README.md#execution-and-log-evidence-ownership). A log match is a candidate association, not a worker-native explanation or unique causal event. |
| Starting authority/policy | [`enforce_required_entitlements`](../controller/src/runner_select.rs), [augment implementation](../controller/src/augments.rs); [BYOXPC](PolicyWitness.md#external-runners-byoxpc) and [augment limits](../runner/augments/README.md#exec_baseline-composition-limits). | [Selection controls](../controller/src/runner_select.rs), [BYOXPC suite](../tests/suites/runner_byoxpc/README.md), [augment unit tests](../runner/Tests/PWRunnerCoreTests/AugmentTests.swift). Entitlement read-back is not an inventory of every source of authority. |
| Compiler receipt | [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h), [`decodeProfileCapture`](../runner/Sources/PWRunnerCore/CWorker.swift); [receipt contract](PolicyWitness.md#compiled-object-receipt-opt-in). | [Capture controls](../runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift) and [dossier witness](../tests/suites/witness_contract/README.md#specimen-dossier). Compiler bytes, application publication and effective permissions remain distinct. |

## Integration work

| Existing owner | Relationship to the new tour |
| --- | --- |
| [Repository README](../README.md#documentation) | Add the worker tour beside the architecture and build tours, with its experimental-design purpose. |
| [Architecture tour](ARCHITECTURE.md) | Keeps temporal orchestration, topology, ordering and channel ownership. Link from the Runner simplicity principle to the new account. Rows 8 and 10 decide which document owns the private-extension and exec-descendant Known gaps. Update the document graph and the figure-count sentence. |
| [Build tour](BUILD.md) and [signing reference](SIGNING.md) | Keep compilation, identity generation, signing and provenance. Link to them from starting authority; add a reciprocal link near native compilation if useful. |
| [Runner reference](../runner/README.md) | Keeps the source map, lifecycle and test seams. Add a worker-tour link near the architecture link. |
| [Wire contract](CONTRACT.md), [request grammar](REQUEST-GRAMMAR.md), [user guide](PolicyWitness.md), [limits](LIMITS.md), [evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md) | Keep accepted inputs, fields, capacities and claims. Link to existing anchors rather than copying tables or creating a normative vocabulary. A row may correct one of them, as row 3 may for the guide. |

Extend [`check_known_gap_index`](../tests/suites/source_drift/check.py) to the
new tour. Extend the disposable-checkout controls in
[check_planner.py](../tests/suites/source_drift/check_planner.py) and the
document graph's account of that rule. Update the
[source-drift reference](../tests/suites/source_drift/README.md) for the
destination, manifest schema and gap coverage. Existing catalog cases can own
these controls.

The prose and link scan already covers `docs/*.md`. Use backticked-symbol
labels for symbol links and filename labels for file links. Do not add prose
baseline exceptions for unverified citations or copied constants. Edit
generator inputs and authored regions, then regenerate through their owners;
never hand-edit generated tables, DOT or SVG.

## Verification

Documentation passes (2, 3, 5 and the integration) regenerate affected
outputs, require a second generation to change nothing, run the check modes,
and run `source_drift` with fresh output:

```sh
python3 docs/generate_architecture.py
python3 docs/generate_architecture.py
python3 docs/generate_architecture.py --check
python3 docs/generate_build.py --check
python3 docs/generate_contract.py --check
python3 docs/generate_worker_identity.py --check
python3 docs/generate_limits.py --check
tests/run.sh --suite source_drift --list
PW_TEST_OUT_DIR=tests/out/runs/worker-doc-REPLACE_WITH_PASS_AND_NAME \
  tests/run.sh --suite source_drift
```

If another generator's inputs changed, run that generator before its check.
`source_drift` checks generated ownership, links, citations, spans, baseline
and build refusals. It does not establish runtime semantics.

Pass 4 changes to worker or host source need what "Changes a row authorizes"
lists: identity regeneration, a signed build, the row's reproduction and
regression control, and the exact covering cases. Record each case's
canonical ID, the source and build it applied to, and its actual result in the
row's detail entry. A probe in pass 1 or 5 follows the same recording rule.
Follow [test guidance](../tests/AGENTS.md#choose-and-run-verification) for
equipment, locking and sandboxed-harness retries. Never bypass a refusal or
reuse unrelated evidence for a pass.

## Acceptance

- The map and prose distinguish prepared reporting resources, supplied
  authority, acquisitions under the policy and external observations without
  reconstructing a timeline. Resources that fit no role are drawn and named.
- The inventory is complete over PolicyWitness's call sites, as defined above,
  and the manifest owns it.
- Every material claim is supported, or is an adjudicated accepted limitation
  written as a Known gap. No open row could change the account.
- Every closed row has its before and after sentences, its adjudication and,
  for a change, its reproduction, regression control and validation.
- No sentence upgrades a native return, publication flag, hash, log candidate
  or path spelling beyond what its owning contract permits.
- Generated outputs are reproducible and owned. Links, citations, gap indexes
  and source-drift controls pass without new baseline exceptions. Existing
  figure destinations and count meanings remain correct.
- Documentation and its machinery land in documentation commits. Any
  production change lands in its own adjudicated commit.

## Outflow (provisional)

Two things are outflow, not this plan: modularizing the generation machinery
so the architecture, build and worker accounts share it, and migrating prose
into semi-structured output locked to the app's characteristics.

As this plan stands, the first draft leaves the inventory in the manifest as
per-resource facts with citations, and leaves the prose authored. It adds no
rule tying the inventory to the worker's call sites. Such a rule would add a
parser over the C worker and a baseline. Build it only if a pass shows the
inventory drifting from source.

The state the first draft must leave for a later migration agent is to be
settled with the user before pass 2, and this section revised then. That
decision may change how pass 2 shapes the manifest.

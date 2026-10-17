# Plan: The Worker — Instrument and Constraints

## Intended result and scope

Create `docs/WORKER.md`, titled **The Worker: Instrument and Constraints**, as
the third major developer tour beside [ARCHITECTURE.md](ARCHITECTURE.md) and
[BUILD.md](BUILD.md). Its organizing question is: **What can the worker carry
across the sandbox boundary without compromising the experiment?**

Write for a contributor--someone who who understands the repository README and 
needs to judge a proposed worker change and *does not* need to be sold the 
benefits of PolicyWitness. Explain why this apparatus can supply particular
observations, and how changing its preparation, authority or reporting could
change what those observations mean. Organize by constraints and capabilities,
rather than another run timeline or source-file walkthrough. Use a capability
map as the principal illustration in order to enforce this structural difference.

This plan follows [the project-planning guidance](../CONTRIBUTING.md#planning-a-change).
It is grounded in source, contracts and test assertions at commit `6fd9f06`,
on the v0.3.1 implementation. The committed changes after that release affect
the retained-evidence index and this planning file, not worker implementation.
Existing uncommitted BYOXPC investigation files and catalog additions are not
evidence for this proposal. Runtime cases cited below were inspected, not rerun
as part of planning; their presence is not a fresh passing result.

Implementing this plan includes the document, generated illustration,
navigation and documentation-check integration. It does not change production
behavior, wire contracts, limits, native sources or experimental policy. Do not
repair an implementation limitation to make a stronger sentence true--one of the
sentinel benefits of writing WORKER.md will be re-evaluation of the system in
light of the new document. The document exists to expose when a sentence in it 
is hard to write.

## Editorial decisions

Connect the proposed subjects through a concrete distinction: **prepared
reporting apparatus, deliberately supplied authority, and resources acquired by
the attempted operation**. These categories describe experimental roles, not a
claim that reporting apparatus has no authority or no effects.

- Treat the boundary as policy application inside an already running process.
  The worker already has executable code, native libraries, memory and process
  context. A fresh worker is not an empty process. Subsequent phases use the
  same applied worker and can observe effects of earlier actions.
- Explain C and fixed layouts through the small, inspectable post-application
  surface they support. Avoid claiming that C cannot allocate, that all native
  calls are allocation-free, or that all post-apply work is raw syscalls. Exec
  setup and private extension calls require qualifications.
- Use ordinary file access, exec preparation and an explicit extension experiment
  as the principal examples. Include Mach lookup and sysctl in the inventory,
  without expanding into a catalogue of sandbox operations.
- Explain ordering as a condition of meaningful comparison. Link to the
  architecture tour for the protocol and the evidence contract for eligibility;
  a release ordinal is not a verdict delivered to the worker.
- Separate intentional ignorance from missing evidence. The worker deliberately
  does not classify prediction/enforcement agreement; an unpublished native
  result is unavailable evidence. Neither licenses an inferred cause.
- Describe current behavior, not change history or aspirational rules. Source
  comments are leads to inspect, not sufficient evidence: older broad allocation
  and attempt descriptions in the worker need the qualifications below.

## Proposed document structure

These sections establish the argument. The writer may improve heading wording
and paragraph balance without reopening the scope or evidence decisions.

### 1. The experimental question

Introduce the tension between surviving the specimen and remaining exposed to
what it tests. Establish the host/worker split briefly: the worker applies the
policy and conducts attempts; the unsandboxed host arranges queries, collects
publications and replies. Explain why opening a target beforehand asks a
different question from opening it under the specimen policy.

Locate this tour beside the run and build tours. It is an explanatory account
of the instrument, not another normative contract or a proof of the macOS
sandbox's completeness.

### 2. What the worker brings with it

Place the capability map here, followed by a compact inventory using these roles.
Explain purpose and experimental consequence instead of enumerating ABI offsets.

| Group | Material to account for | Required qualification |
| --- | --- | --- |
| Prepared reporting and coordination | Host-created, zeroed/pre-touched evidence mapping; worker mapping before apply; fixed request, slot, phase, diagnostic and optional capture storage; release/acknowledgement words and exit request. | This is an intentionally available reporting resource. Pre-touching does not establish pinned memory or universal survival. Publication and cleanup remain separate facts. |
| Policy and setup inputs | Policy pipe, expected/read byte counts, parameter snapshot, native compilation, optional compiler-object capture, pre-apply ready pipe, timebase/allowance setup and SIGPIPE handling. | Readiness is a pre-apply hint. Compilation and imports are policy preparation, not target-access observations. The receipt is compiler output before apply, not kernel policy readback. |
| Starting authority and context | Selected worker binary's signing entitlements and ordinary process context; supplied policy bytes, including explicit controller-resolved augments. | Entitlements and augments affect the experiment. The worker's environment is unrecorded. Its launch does not have the descriptor and environment isolation contract provided for an exec child. |
| Explicit extension authority | Ordinary-authority issuer, host target preparation, separate transient token mapping, worker delivery validation, pre-resolved consume/release symbols and later lifecycle actions. | A token is an explicit intervention, not ordinary reporting storage. Issuance, delivery, consumption, release and later access are distinct. The issuer does not receive the selected worker's entitlement plist. |
| Acquisitions under the policy | Fresh target opens; unlink/access; bootstrap-port/service lookup; sysctl calls; per-attempt exec pipes, spawn handles and child launch. | Describe acquisition at the actual attempt boundary. Not every setup call is sandbox-gated, and acquiring one resource does not establish all effects of a compound attempt. |

Distinguish the backing mapping from its descriptor: results are published through
mapped memory, not post-apply writes to a reporting pipe. The token mapping has
different authority, ownership and erasure rules. Policy and readiness pipes must
not appear as equivalent post-apply result paths.

Describe deliberately supplied worker descriptors from the launch actions,
without implying a complete inventory of ambient descriptors or Mach rights.
Contrast this with the explicit descriptor and empty-environment contract for
exec children, including exclusion of the worker's reporting descriptor.

### 3. What can become an observation

Explain the operational knowledge the worker needs: attempt kinds and targets,
bounded arguments, phase partitions and ordinals, time allowances, extension
handle state, native returns and publication state. It compiles through libsandbox;
it is not a policy interpreter deciding what should happen.

Build this section around three distinctions:

1. **A native call and a published result.** Progress is a latest atomic milestone,
   not a complete trace. A pre-call marker establishes reaching that boundary;
   immutable payload becomes readable only through publication. Use the existing
   create-then-kill-before-publication control: the independently observed file
   exists while the reply correctly withholds the completed result. Explain why
   reading partially written payload would be wrong.
2. **An attempted operation and the effect recorded.** Contrast `open_read` with
   `read_fresh`: the former attempts a byte read but ignores its result and reports
   open success; the latter retains separate open/stat/read/close observations,
   descriptor identity and a bounded content prefix. Mention that `open_write`
   ignores write/close returns, `create` can open an existing file without
   truncation, and a child's nonzero exit does not negate successful spawning.
   Link to the action reference for the complete catalogue.
3. **Firsthand evidence and external observations.** Predictions originate in the
   validator; disposition and comparison assembly belong to the host; later path
   enrichment is a host observation; logs and dossier assembly are outside the
   worker. Neither predictions nor logs become the worker's explanation of a
   failure. A permission-shaped result is distinct from a sandbox-cause claim.

Link to the existing ownership and comparison contracts rather than copying
their field tables. Explain that validator queries use no-report mode, eligible
`query_first` records establish order rather than a snapshot, and unchanged path
spelling does not establish unchanged object identity.

### 4. Changes that would change the experiment

Use short design-review cases. Identify the tempting change, the question it
would actually answer, the current constraint and its evidence. Do not present
hypothetical changes as discovered bugs.

| Improvement to examine | Experimental consequence and current response |
| --- | --- |
| Open a target before apply, or retain its descriptor across extension phases. | Observes use of previously acquired authority rather than fresh acquisition under current conditions. Fresh reads open and close within each action. |
| Prepare all exec pipes/handles before apply for reliability. | Moves attempt setup outside the specimen and can hide setup restrictions or exhaustion. Current setup is per attempt after apply; descriptor-ceiling and bare-deny controls test different aspects. They do not prove future macOS versions leave setup ungated. |
| Warm up an extension by consuming before apply, or hide tokens in reporting state. | Introduces authority before the declared intervention. Current code resolves symbols without calling consume/release, uses a separate channel and publishes lifecycle results at requested actions. |
| Retry with a changed path, extra authority or friendlier policy; reuse a sandboxed worker for a new specimen. | Substitutes changed conditions for the submitted experiment. Use a separate specimen or explicit action to investigate those conditions. Do not claim there are no retries: interrupted I/O and process-observation loops retry within their protocols. |
| Add `exec_baseline` automatically to make an experiment run. | Changes the tested policy; its broad file-read allowance can override the denial under investigation. Augmentation is explicit and accounted for in resolved source. |
| Move interpretation/reporting into the sandboxed process, or treat success/missing output as self-explanatory. | Makes replies depend on specimen-controlled communication or imports unsupported conclusions. Retain external assembly and distinguish missing publication from a missing effect. |

Explain the analogous ordering risk briefly: removing the hold until collection
closure would let worker effects change what supposedly prior queries see.
Even the intact hold does not freeze external actors or prevent earlier actions
within a phase from changing conditions for later actions.

### 5. Where the instrument stops

Keep qualifications beside the promises they limit. Explain how a contributor
should assess a new capability: identify its authority, acquisition boundary,
native observation, publication mechanism and an independent control that could
falsify the claim. This is explanatory guidance; working rules stay in AGENTS files.

Cover these limits without converting them into repair tasks:

- PW-owned preallocated buffers do not describe private libraries' allocation or
  retained state. Erasure observations concern PW-owned storage; native release
  success does not establish access revocation.
- Query ordering, prepared metadata and later descriptor identity do not establish
  a stable world. Consume/release earlier in the same phase can change authority
  after that phase's query collection.
- Deadlines govern specific waits and observation loops, not the entire lifecycle.
  Blocking operations can outlast allowances. Termination requests, EOF and leader
  exit do not establish descendant cleanup. Worker death during exec can leave
  helpers alive, and descendants can leave the child's process group.
- Source identity, compiled-layout checks and signed provenance answer different
  questions. None proves runtime correctness or authenticates shared-memory
  observations against an adversarial peer. This tour is not a security proof.

Consider this as you think about limits: even though this plan has very guarded 
language, that exists to help us avoid overclaiming. The guardedness does not 
need to be reproduced in the WORKER document itself, which should be guarded 
by only making positive claims about what it is responsible for and allowing the 
responsible reader (a contributor who might be superindending their own fork!)
to draw their own conclusions as to what PolicyWitness is not.  

End with **Known gaps**, indexing only paragraphs introduced as “Known gap” beside
their owning promises, in document order. Intentional semantic limits need not
all be called implementation gaps. Use that label for incomplete guarantees,
such as unobserved private state, unrecorded worker environment and incomplete
descendant containment.

## Supporting evidence

Use these anchors for claim-to-evidence review. Inspect assertions when selecting
citations: source location, test definition, controlled interpretation and live
observation establish different things.

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

## Capability map and generator ownership

Use a generated Graphviz SVG with a nearby generated source/check table, following
the architecture figures. The map should answer “what kind of resource or evidence
is this, and which boundary does it cross?” It should not be a timeline, sequence
diagram or duplicate process topology.

Use four visually distinct groups, with textual labels as well as color:

- **Prepared apparatus:** reporting/coordination memory, policy/parameter inputs,
  compiled object and clock setup. Distinguish optional pre-apply capture from
  post-apply result publication.
- **Authority supplied:** selected worker entitlements and resolved policy; a
  separately drawn issuer/token path. Consumption is an action under the policy,
  not an inevitable consequence of delivery.
- **Actions under the policy:** fresh file acquisition, native lookup/sysctl,
  exec setup/child and extension lifecycle. Group related actions where detail
  would obscure the central distinction.
- **External evidence:** validator predictions, host lifecycle/path observations,
  controller/log evidence. Connections join collected evidence; they must not
  imply predictions or explanations sent into attempts.

Give every node and edge a stable ID. Label edges by role—prepares, supplies
authority, exercises, publishes, observes or joins—rather than chronological
numbers. Evidence and token mappings must be separate nodes. Make the application
boundary legible without implying it erases preexisting resources. Keep labels
compact and place qualifications in the adjacent table/prose. Include an
accessible description in the document.

**Chosen implementation:** extend the existing architecture manifest/generator
to place this graph in `WORKER.md`. Do not introduce another generator or embed
the full map in both tours. This retains the citation, rendering, stale-copy and
build-gate machinery, but requires a bounded documentation-tool change because
the current generator assumes one Markdown destination.

1. Extend [architecture.json](architecture.json) and
   [`load_manifest`](generate_architecture.py) with an optional per-graph document
   destination, defaulting to the existing top-level destination. Advance the
   architecture manifest schema for this shape; this is not a wire-version
   change. Register the intended destinations and retain strict rejection of
   unknown fields, escaping paths and duplicate outputs.
2. Route the new graph to `docs/WORKER.md`, with generated files
   `docs/worker-capabilities.dot` and `docs/worker-capabilities.svg`. Existing
   figures stay in `ARCHITECTURE.md`. Update rendering, SVG links/tooltips,
   inventories, self-citation exclusions and check/write paths to use each
   destination. Validate all documents and finish rendering before publishing
   any changed output.
3. Register the document in architecture span ownership. Preserve global graph
   count semantics; revise the architecture introduction so it no longer equates
   all manifest graphs with figures embedded there. Use existing per-graph spans
   if the new prose needs counts. Prefer links to limits over numerical copies;
   register the document with the limits span owner if a value is essential.
4. Update [architecture controls](../tests/suites/source_drift/architecture.py)
   and [generator ownership controls](../tests/suites/source_drift/generators.py)
   for multiple destinations. Add passing and rejected controls for routing,
   stale regions/figures in either document, invalid destinations, duplicate
   ownership, broken markers in the second document, and render failure leaving
   both documents and all figures untouched. Retain idempotence, citation-definition
   and no-self-citation checks.

Every map element must cite an implementing source and a suitable test or rule
using the manifest's citation forms. Review what each check establishes. The
caption may promise that citations resolve and checks are defined; it must not
say those facts prove the behavior. Use limit placeholders for numerical
durations or sizes in manifest facts.

## Integration work

| Existing owner | Relationship to the new tour |
| --- | --- |
| [Repository README](../README.md#documentation) | Add the worker tour beside architecture and build with its experimental-design purpose. |
| [Architecture tour](ARCHITECTURE.md) | Retain temporal orchestration, topology, ordering and channel ownership. Link from the worker rationale/principles to the new account. Update the generated document graph for the new destination, document and checks. |
| [Build tour](BUILD.md) and [signing reference](SIGNING.md) | Retain compilation, identity generation, signing and provenance. Link to them from starting authority; add a reciprocal worker link near native compilation if useful. |
| [Runner reference](../runner/README.md) | Retain source map, lifecycle and test seams. Add a worker-tour link near the architecture link. |
| [Wire contract](CONTRACT.md), [request grammar](REQUEST-GRAMMAR.md), [user guide](PolicyWitness.md), [limits](LIMITS.md), [evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md) | Retain accepted inputs, fields, capacities and claims. Link to existing anchors; do not copy tables or create a new normative vocabulary. The standalone user guide need not gain this developer tour as a companion. |

Extend [`check_known_gap_index`](../tests/suites/source_drift/check.py) to include
the new tour. Extend disposable-checkout controls in
[check_planner.py](../tests/suites/source_drift/check_planner.py) and the architecture
document graph's account of that rule. Update the
[source-drift reference](../tests/suites/source_drift/README.md) for the destination,
manifest schema and gap coverage. Existing catalog cases can own these controls;
a new suite is unnecessary.

The prose/link scan already includes `docs/*.md`. Use backticked-symbol link
labels for symbols and ordinary filename labels for file links. Do not add prose
baseline exceptions for new unverified citations or copied constants. Edit
generator inputs and authored regions, regenerate through their owners and review
the diff; do not hand-edit generated tables, DOT or SVG. The existing architecture
check in the build should cover the new outputs without changing the production
build sequence.

## Execution and verification

Implement in this order:

1. Recheck the source snapshot and evidence anchors. If production changed, update
   affected claims and controls first. Establish the inventory and map's source/check
   entries before drafting prose.
2. Add the document skeleton and map destination support with its controls.
   Generate the figure/tables and inspect the SVG at normal reading size for
   legibility, grouping, edge direction and misleading authority/evidence flows.
   A matching SVG stamp does not establish visual quality.
3. Write the tour from the section briefs, incorporating the map and publication
   counterexample. Add navigation and gap-check integration.
4. Review each substantive claim against implementation, the owning contract and
   cited assertions. Focus on open-only semantics, private allocation, worker
   versus child inheritance, publication versus effect, and release versus revocation.
5. Regenerate affected outputs, require a second generation to change nothing,
   run generator check modes, then run the public documentation selection below
   with a fresh output directory.

```sh
python3 docs/generate_architecture.py
python3 docs/generate_architecture.py
python3 docs/generate_architecture.py --check
python3 docs/generate_build.py --check
python3 docs/generate_contract.py --check
python3 docs/generate_worker_identity.py --check
python3 docs/generate_limits.py --check
tests/run.sh --suite source_drift --list
PW_TEST_OUT_DIR=tests/out/runs/worker-documentation-REPLACE_WITH_UNIQUE_NAME \
  tests/run.sh --suite source_drift
```

Replace the placeholder run name. If limits span registration or another
generator's inputs changed, run that owning generator before its check too.
Follow [test guidance](../tests/AGENTS.md#choose-and-run-verification) for equipment,
locking and sandboxed compiler-discovery retries. Do not bypass a refusal or
reuse unrelated evidence for a pass. Source drift checks generated ownership,
links, citations, spans, baseline and build refusals; it does not establish
runtime semantics.

No live worker battery or signed rebuild is required merely to add this tour
and its documentation machinery. If writing exposes a disputed runtime claim,
narrow it to inspected evidence or run the exact existing case that can resolve
it, against an applicable signed build with fresh retained output. Record the
canonical ID, source/build applicability and actual result. A cited case is not
a freshly executed case. Production changes belong in separate scope; changes
to the wait, release store or query eligibility still require
`witness_contract/order_barrier_mutations` under repository guidance.

Acceptance requires:

- The map and prose distinguish prepared reporting resources, supplied authority,
  attempted acquisitions and external observations without reconstructing a timeline.
- Design-review examples explain which experimental question would change, with
  implementation/evidence anchors and qualifications.
- No sentence upgrades a native return, publication flag, hash, log candidate
  or path spelling beyond what its owning contract permits.
- Figure and prose are readable; generated outputs are reproducible and owned;
  links, citations, gap indexes and source-drift controls pass without new baseline
  exceptions. Existing figure destinations and count meanings remain correct.
- The diff contains the document and supporting documentation machinery, with
  no production, ABI, wire-version or policy behavior change.

## Remaining questions and decision boundaries

No unresolved scope or structural decision blocks execution. Leave paragraph
balance, final heading wording and exact diagram layout to the writer.

Two empirical questions remain outside the proposed guarantees: the complete
ambient-resource inventory of the worker, and private extension routines'
allocation/state behavior. Current sources and controls establish neither. Say
so in the document. Stronger claims would require an independently observed
worker launch inventory or targeted native instrumentation with a stated
observation boundary; neither is a prerequisite for this account.

If implementation and a normative contract disagree, stop strengthening that
claim and identify the discrepancy. Resolve it through focused inspection or
evidence before publication, or explicitly document the limitation. This plan
authorizes an accurate account of the current instrument, not changes to make
the instrument fit that account.

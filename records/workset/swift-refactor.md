# Swift contract and orchestration refactor design

R2 preparation by `swift_design` examined `29d1c79`; Swift implementation bytes
were unchanged through D2 merge `bb92c21`. It performed no writes, builds or
tests. Primary source review accepts the design below for revalidation against
the completed R1 baseline. Implementation remains sequential after R1. This
record supplies the execution detail for
`records/distribution/SWIFT-MODULARIZATION-PLAN.md`; no driver extraction is
authorized, and F1 remains unresolved.

## Stage 1: immediately used boundaries

| Change | Existing callers | Named Stage 2 use |
| --- | --- | --- |
| Shared `PWRunnerCoding.swift`: move RequestKey, rejectUnknownRequestKeys, pwRunnerEncodeJSON and pwRunnerDecodeJSON; RequestKey has internal visibility | Eleven closed request-object decoders, the phase-action decoder's key discrimination, and host/client JSON boundaries | Common mechanics for separated request, extension and reply families |
| Host-only `CWorkerDisposition.swift`: move uniquelyAssociatedWorkerSlots with internal visibility | buildStepResults and resolveDisposition | Disposition owner, preserving rejection of duplicate-ID association |
| Make only makeWorkerSlot and workerParamsFromPolicy internal | Current run/admission translation | Calls from run into the separate request-planning owner |
| Explicit shared-contract source list in Meson and independently declared expected set in native_sources.py | Shipped client and host | Add each wire-family owner without including host service/listener/processing |

There is no unused layer. RequestKey is internal because both the closed-key
helper and the phase-action decoder use it. This corrects the initial design's
missed caller after the failed Stage 1 build recorded below.
workerSlotsFromProbePlan, mapAttemptKind, pathFilterIsUnresolvable and local
classifier/result helpers remain private beside their eventual callers.
unwrapWorkerOutput and unwrapValidatorOutput stay private with run. Stage 1
does not relocate query eligibility or the attempt decoder. Commit, sign,
verify and accept this complete intermediate stage before Stage 2.

## Stage 2: responsibility owners

All shared files stay in the existing core target. A family keeps its types,
CodingKeys, codecs and local validation together; flat files are not new runtime
modules or packages. Keep generated contract constants in the existing owner.

| Shared file | Responsibility |
| --- | --- |
| PWRunnerAPI.swift | XPC protocol, PWRunnerWire, outcome constants and generated PWContract versions |
| PWRunnerRequest.swift | Request errors/refusals, run/phase/action requests, overrides, policy/probe/query/filter/attempt requests and admission records |
| PWRunnerExtension.swift | Extension declarations, intervention/event/issuer/delivery records and local limits/validity |
| PWRunnerPathEvidence.swift | File identities, both path diagnostics and local path-form codecs |
| PWRunnerAttemptEvidence.swift | Fresh-read/write/stat and exec records, attempt result, codecs and all three local evidence validators |
| PWRunnerPredictionEvidence.swift | Query results, native verdicts, validator decode/association/subprocess records, filter mapping and unique verdict association |
| PWRunnerStepEvidence.swift | Comparison, step and ordering records; eligibleOrderedPrediction and eligibleOrderedStep |
| PWRunnerLifecycleEvidence.swift | Worker progress/failure/readiness, diagnostics, policy receipts, transfer/wait/termination observations and subprocess |
| PWRunnerDisposition.swift | Disposition vocabulary/claims/issues/steps, protocol positions, progress association, lifecycle projection, dispositionIntegrityProblems and private dispositionBasisSufficient |
| PWRunnerProfileCapture.swift | CompiledProfileCapture and local validity |
| PWRunnerReply.swift | Phase/run replies, codecs, reporting/spawn failures and cross-family policyReadProblem, validatorOwnershipProblem and extensionEvidenceProblem |

PWRunnerReply explicitly owns inter-family relationships. Preserve the existing
run-result encoding/decoding asymmetry: decode validates fewer relationships
than encode. Move both bodies intact with their validation order, error paths,
degradation bypasses and evidence retention. Do not unify them during extraction.

| Host file | Responsibility |
| --- | --- |
| CWorkerOrchestrator.swift | Both run overloads, bundle paths, private output unwrapping and visible execution sequence |
| CWorkerRequestPlanning.swift | Slot/parameter translation, action mapping, capacity/refusal helpers/constants, ValidatorQueryDecision, fresh planning and admissionFailure extension |
| CWorkerStepResults.swift | buildStepResults, buildAttemptResult and private sandbox-result/outcome construction |
| CWorkerComparison.swift | ComparisonOrder/Evidence, ordering projection, comparison construction and scope relationships |
| CWorkerDisposition.swift | Stage 1 association helper, resolveDisposition, lifecycle/subprocess/delivery projections, ClassifiedRun, workerTimeReason and classifier/private helpers |

Keep admission before translation/acquisition, ExtensionSession construction
and early erasure, query planning in the existing phase callback, collection
clock samples and mutable budget, synchronous validator invocation and closure,
driver call, partial-output recovery and failure precedence, phase assembly,
delivery projection, erasure and final reply visible in run. No constructor or
new callback hides planning, acquisition, sampling or cleanup.

## Required adaptations and preservation evidence

- Meson uses an explicit `pwrunner_contract = files(...)` list for host/client;
  native_sources has an independent expected list. No PWRunner-name glob that
  would admit host-only files. SwiftPM discovers the new core files normally.
- Source drift separates request-override and query-planning owner paths,
  including RULES declared inputs, parsers and diagnostics. Planner mutations
  follow the moved owner while host-invariance controls retain their own path.
  Preserve missing definition/contains/local exclusion, combined-fault and
  restoration expectations. Do not repair F1 while editing adjacent equipment.
- Retarget override controls to PWRunnerRequest. Add focused source-membership
  controls rejecting a missing shared client file and a host-only client input.
- Move the exec_reader_mutations decoder anchor to PWRunnerAttemptEvidence,
  preserving both rejected mutations, unchanged assertions, hashes and
  restoration. Order-barrier host discovery continues through native_sources;
  the driver mutation remains in CWorker.swift.
- Relocate current architecture/limits citations and README/AGENTS source
  routes through their owners and regenerate. Preserve dated source paths and
  hashes in historical observations. Regenerate worker identity at both stages;
  wire versions, response-shape golden and ABI geometry remain unchanged.

Commit each candidate before the signed build. Stage 1 selects default cases
from source_drift, unit, integration, runner_unit, runner_abi_layout,
runner_c_worker_harness, failure_boundaries and runner_validator_failure, plus
blackbox checker controls/BBX-001/002 and witness cases for query-before-attempt,
killed-before-publication, in-flight deadline, phases, extension combinations
and directory effects. Inspect exact catalog IDs before executing; suite
selectors include opt-ins and are not a shortcut for default membership.

Stage 2 requires the final signed default battery, plus
`witness_contract/order_barrier_mutations` because eligibility moves and
`runner_unit/exec_reader_mutations` because the production decoder moves.
Final combined verification also includes applicable R1 native/inheritance
controls and the BYOXPC witness. Existing request, response-shape, maximum,
disposition-conflict, partial-result, extension and fresh-write expectations
are preservation criteria; no replacement captures or changed outcomes are
justified merely by relocation.

Record each material test adaptation with old/new owners, causal extraction,
preserved refutation and actual implementing/verification commits. Review the
adopted or revised Stage 1 boundaries and effectful sequence before acceptance.
This design is not an implementation or passing-test claim.

## Stage 1 implementation candidate

Implementation starts from clean `46d2c2f392ef552f503693e84796cfb50524c712`,
after R1 acceptance `96d0328e`. Revalidation against the original design source
found no changes in PWRunnerAPI or CWorkerOrchestrator; R1's Swift change is its
generated identity. D2's factual account and repair-command corrections are
already integrated. `swift_design` authored this stage; primary review and
signed execution remain separate.

Initial candidate `721653008e09280ab7ddecbb0088e8a564a5655e` follows the original
Stage 1 design. PWRunnerCoding owns the
private RequestKey, closed-object key check and sorted-key JSON helpers;
existing names and call sites remain. CWorkerDisposition owns unique worker-slot
association, immediately called by step assembly and disposition resolution.
Only makeWorkerSlot and workerParamsFromPolicy gain internal visibility; both
already serve run/admission and enable the named request-planning extraction.
No Stage 2 family extraction, new callback, runtime state or resource acquisition
is introduced. Run-result codecs and their asymmetric validation bodies remain
in PWRunnerAPI unchanged.

| Adaptation | Old arrangement | New arrangement and preserved obligation |
| --- | --- | --- |
| Shared source membership | Client named API plus its entry; host listed API with its other files | Meson's explicit pwrunner_contract contains API and Coding and feeds both targets. native_sources independently names the same required shared sources; the host still independently discovers every core Swift file. CWorkerDisposition is host-only. |
| Source-membership rejection controls | Meson controls covered host/shim membership, duplicate targets and worker substitution | Two independent client controls replace its shared source argument with API alone, or add CWorkerDisposition. Literal expected diagnostics require the missing Coding file and unexpected host file respectively. Existing controls and restoration remain. |
| Current source accounts | Runner/source-drift references described the monolithic coding/association owners and client source set | README and checker/helper accounts name the actual shared and host boundaries. The unresolved F1 paragraph is byte-identical. |
| Encoding citation | runner_reply_maximum cited pwRunnerEncodeJSON in API | limits.json cites Coding; generate_limits regenerated LIMITS. The numeric limit, production encoder and maximum-reply assertions are unchanged. |
| Worker identity | Identity for the completed R1 source arrangement | The owning generator regenerated all three copies after Swift/Meson changes. Candidate identity is a1916bc910c37e2d6393650bac2d06f157f2642505eeca2372b590be2bbee5cb. No wire-version or ABI-geometry edit. |

Local preparation checks passed: Swift frontend syntax parsing of the four
changed/new Swift files, Python AST parsing of the three changed checker/helper
files, limits/build/worker-identity generator checks, and git diff whitespace
checking. An inverse source comparison against the fixed parent establishes
that API differs only by removing the exact three relocated blocks, and the
orchestrator only by removing the exact association helper and the two specified
visibility modifiers. The new files retain those blocks byte-for-byte apart
from the association function's required visibility and its owner comment.
The existing host-source guarantee paragraph was separately compared unchanged.

These are syntax, generator and source-preservation observations, not passing
dispatcher cases or compilation of the linked client/host. No signed build or
dispatcher was run by this implementer. Primary review, signed Stage 1 build,
required verification and acceptance precede Stage 2. The commit containing
this subsection identifies the candidate; subsequent acceptance must identify
its actual build and run sources separately.

## Stage 1 compilation correction

The primary executor's signed build of `72165300` failed before packaging:
both host and client compilation could not find RequestKey in
PWRunnerPhaseAction.init(from:). The design and extraction audit had counted
rejectUnknownRequestKeys callers but missed the phase-action decoder's direct
use of the key type to select the extension representation. Moving that type
with private visibility made an existing caller inaccessible across files.
This is a refactor regression, not a baseline behavioral finding.

The correction changes only RequestKey from private to internal. An explicit
usage audit across runner finds its declaration, its use in the closed-key
helper, and the phase-action decoder's two direct references; no new caller or
operation is added. The current design row above now records that existing
caller and its Stage 2 Request/Coding boundary. The original failed candidate
and its earlier private-visibility design remain recoverable in git.

The three generated identity copies now carry
`6f777628d0b0f233f6e26f99222e8f78cd0920bb94b842b5bf2d0c4b2e29a9a7`.
The initial inverse body comparison remains accurate but establishes only the
stated source transformation. Swift frontend parsing checks syntax and did not
resolve this access-control error; neither check established host/client
compilation. No test or build was run by the correction implementer. The
primary executor will rerun the same signed build command against the corrected
commit and then perform the Stage 1 verification selection.

## Stage 1 acceptance

Primary-agent review accepts corrected source
`9af4d3d14148710a9cb3db33d52c17fdc24f3b93`. The original failed candidate
`72165300` remains failed, with its missed current caller and correction above.
Primary independent inverse comparison confirmed exact relocated helper bodies
and otherwise unchanged API/orchestrator bodies, apart from the named visibility
changes; the explicit RequestKey caller audit supported its additional correction.
Every introduced boundary has current callers and the named Stage 2 use. No
unused preparatory module or new resource acquisition remains.

The same signed build command succeeded on the corrected commit as v0.3.3
build 998, `v0.3.3-145-g9af4d3d1`, with identity
`6f777628d0b0f233f6e26f99222e8f78cd0920bb94b842b5bf2d0c4b2e29a9a7`.
Both shipped host and client compiled the explicit shared source set, source
and native identity closure passed, and all seven executable signatures/two
seals verified with the intended Developer ID, runtime and secure timestamps.
The client contains Coding and API but no host processing file.

Run `workset-r2-stage1-01`, `20261029T225222Z_5ff4f3ef`, passed **87/87** selected preservation
cases at the clean corrected source and matching app. The selection is the
eight default-suite populations and nine explicit blackbox/witness IDs described
in the design above; exact IDs/configuration remain in the run's plan. No skips,
unrun cases, harness errors, observed sleep or app mutation. Elapsed dispatcher
time was 265.699 seconds. It includes all 480 Swift tests, native
controls/layout, actual admission and validator failure boundaries, source
mutation controls (including both client membership rejections), independent
readers and live phase/extension/publication observations. The run is pinned;
raw output remains local/gitignored.

This acceptance is primary-agent self-review of source and execution against
the Stage 1 criteria, following implementation by `swift_design`. It establishes
a complete usable intermediate stage; it is not Stage 2 or full-workset
acceptance. Wire versions, response goldens and ABI geometry remain unchanged.
F1 remains unresolved. Proceed to the named Stage 2 extractions and their final
combined source/build verification.

## Stage 2 implementation candidate

Implementation starts from clean Stage 1 acceptance
`2de5b1c72e32ba5c14cc140f3df2d34e37ea2321`. The responsibility table above is now
implemented: 91 declarations move from API into the ten named shared wire
families, with each family's existing codecs and local validators. API retains
the protocol, constants and generated versions. PWRunnerReply owns the existing
policy-receipt, validator-ownership and extension-evidence cross-family checks,
called from the run-result codecs. Their existing validation order and the
encode/decode asymmetry remain intact.

The four extracted host helpers leave both run overloads, bundle path selection
and private output unwrapping in CWorkerOrchestrator. The complete run bodies
are unchanged: admission precedes translation/acquisition; extension preparation
and early erasure, phase-callback query planning, clock samples and budget,
synchronous collection closure, worker invocation, partial-output recovery,
failure precedence, phase assembly, delivery projection, erasure and reply
construction retain their positions. No new acquisition, callback or runtime
layer is introduced.

All Stage 1 boundaries are adopted without further visibility changes:

| Boundary | Stage 2 callers and ownership |
| --- | --- |
| PWRunnerCoding | Request and Extension decoders call the same closed-key helper. Request's phase-action decoder directly uses internal RequestKey. Service/client JSON boundaries still call the same coding helpers. Coding is byte-identical to the accepted Stage 1 source. |
| Unique slot association | CWorkerStepResults calls the existing CWorkerDisposition helper; resolveDisposition calls it within that owner. Duplicate identifiers still cannot select an arbitrary slot. |
| makeWorkerSlot and workerParamsFromPolicy | Both run and admission retain their existing calls into CWorkerRequestPlanning. Its workerSlotsFromProbePlan, mapAttemptKind and pathFilterIsUnresolvable remain private with their callers. |
| Explicit shared source set | Meson and native_sources independently name API, Coding and ten wire families. The client compiles those twelve sources plus its entry; the host compiles all twenty-six core sources plus its entry. No host service/listener/processing source enters the client. |

The visibility audit also follows every private top-level helper and type:
RetiredProfileKey stays with the run decoder in Reply; dispositionBasisSufficient
stays with shared disposition validation; sandbox-result/outcome helpers stay
with StepResults; anySlotNotCompleted stays with the classifier in host
Disposition; both unwrap helpers stay with run. The private ordinaryPlan
property remains with the complete RunSpec definition. Complete host and
client typechecking resolves these boundaries, including the direct RequestKey
caller missed by the initial Stage 1 syntax-only check.

| Material adaptation | Relocation and preserved refutation |
| --- | --- |
| Override source rule | The parser, missing-definition diagnostic and RULES required input now name PWRunnerRequest. A control renames its real override definition and independently expects struct.missing, then restores it. Existing property/table mismatch expectations remain. |
| Planner source rule | Function/contains lookup now reads CWorkerRequestPlanning. The local-table scan reads all five owners containing the former orchestrator implementation: Planning, Orchestrator, StepResults, Comparison and Disposition. All five are required RULES inputs; unrelated core files are not added to this convention. The lexer and existing rule IDs are unchanged. |
| Planner rejection controls | Existing planner mutations move to Planning, while host-invariance mutations keep the host path. A second-owner table control independently expects planner.local_table; a renamed planner expects planner.missing_function; an unterminated string in Comparison expects planner.unterminated_string. Restoration remains explicit. String parsing still precedes table/function inspection and returns the malformed-source diagnostic; existing combined local-table/missing-contains and entry-point combined-fault expectations remain unchanged. |
| Client membership controls | The missing-Coding mutation now supplies an independent literal list of all eleven other shared sources, so it omits only Coding and retains the exact single missing-file diagnostic. The host-only Disposition addition still requires the exact unexpected-file diagnostic. Neither control derives its expectation from Meson or native_sources. |
| Exec decoder mutation | exec_reader_mutations now changes and captures PWRunnerAttemptEvidence, the actual owner of the unchanged absent-metadata decode anchor. Its publication-bypass mutation remains in CWorker, and its rejection assertions, hashes and restoration are unchanged. Order-barrier discovery continues through native_sources; its driver mutation stays in CWorker. |
| Current citations and accounts | Seventeen architecture and twenty-four limit source paths follow their actual symbols. The owning generators update ARCHITECTURE, WORKER and LIMITS. Runner/override/request/evidence accounts name the resulting owners. CWorker's action-mapping comment points to Planning. Historical observation paths/hashes and excluded plans remain unchanged. |
| Identity | The owning generator updates the Swift, C-header and Python copies to f477a8488d3f96715e987f7014dcd0aa76ba53b70575118e20ef238b600d4094. No contract versions, ABI geometry or response goldens change. |

The exact source comparison uses the fixed Stage 1 acceptance commit above.
It partitions the API body into its 91 top-level declaration chunks, retaining
attached comments/whitespace, and compares each destination's concatenation
byte-for-byte after its import prefix. The retained API prefix also matches.
For the host it compares the original admission, planning, step-builder,
comparison and subprocess/disposition sections with the five resulting files,
allowing only import prefixes, the admission extension wrapper, the original
enum close and trailing-blank-line normalization. Both run overloads and all
helper bodies are exact. Coding and every other core file match the baseline;
CWorker differs only in its generated identity block and the source-citation
comment. The other two identity outputs differ only in their generated blocks.
The F1 symbol set, host-invariance functions and guarantee paragraph were
separately compared unchanged; F1 remains unresolved.

Local preparation passed:

- Full `xcrun swiftc -typecheck -target arm64-apple-macosx26.0` over the 27-file
  host source set and the 13-file client source set, with separate module names
  and a temporary module cache. Both exit zero. Commands/diagnostics remain in
  `/private/tmp/pw-r2-stage2-typecheck-oi9ni0dt`; these are local preparation,
  not durable dispatcher evidence.
- Static Meson/source-list comparison against native_sources' independent
  twelve-file contract expectation and the complete on-disk core inventory.
- Python AST parsing for all four changed helper/control sources.
- Contract, limits, architecture, build and worker-identity generator checks,
  plus whitespace checking. Request/response/envelope versions remain 5/24/8.

No signed build, dispatcher case or live test was run by this implementer.
The commit containing this subsection identifies the candidate. Primary source
review, the signed build, all default cases and the applicable mutation/BYOXPC
controls must establish acceptance separately; these local preparation checks
do not claim behavioral equivalence or final workset completion.

## Stage 2 verification and citation correction

Signed build 1000 at `fd90eee66538cc02dc5d21b7a3fe8eca81a17403` passed
compilation, source/identity closure and all seven executable/two seal checks.
Independent read-only review by `review_public_extension` found no implementation
defect; both run overloads, complete reply codecs and their asymmetry were
compared unchanged. Primary review agreed. The review did identify current
citation omissions, corrected in this commit:

- A separate request source node now owns documents edge D26's override table.
  API retains its actual version/vocabulary ownership.
- Authored admission/timeout links follow RequestPlanning; synthesis follows
  StepResults. Three R1 timing links follow the private timing owner.
- The contract generator's two Swift citation labels now name requestSchema and
  responseSchema, the actual member declarations. Their formerly qualified uses
  moved out of API. No scanner, rejection expectation or version-value check
  changes; the generated contract table follows its owner.

The complete 207-case selection (all 201 defaults plus native_clock,
inheritance mutation_controls, order_barrier_mutations, exec_reader_mutations,
reaped_ack_mutation and extensions_byoxpc) ran at clean `fd90eee` against that
app in `workset-r2-final-01`, run `20261029T231443Z_9c34b030`. It completed
205 passes and two failures in 803.162 seconds, with no skipped/unrun cases,
observed sleep or app changes. The two suite-exit harness errors reflect those
two failed cases. All 480 Swift unit tests and five other opt-in controls passed.

The generator_contract failure was the two qualified citation strings above;
its original failure remains retained, and corrected checks are still required.
The other failure was extensions_byoxpc: consume_only received an XPC error
4097 and no worker reply. An unchanged rerun in `workset-r2-byoxpc-02` passed
that subcase but failed with the same transport error at no_predicate-baseline.
This is not attributed to the refactor, the automation sandbox or launchd
without further evidence. No retry behavior or expectations were changed.
Required BYOXPC verification remains unmet; Stage 2 and the combined refactor
stage are not yet accepted. The separate failure account/checkpoint records
ownership and the discussion boundary.

For the citation-only correction, `swift_design` traced executed dependencies
and recommended all eight source_drift cases plus preflight/build_entry_controls.
The latter imports/copies the contract generator and runs its build gates.
Other preflight, runtime, reader and selected mutation paths do not execute the
changed documentation inputs. Any reuse still requires final diff and app-byte
comparison and retains each original source/result; the BYOXPC failure supplies
no passing credit. No excluded toolchain-switch control is credited here.

## Corrected source checks and current acceptance limit

The nine-case follow-up at `590c5e42f010814b09cfe30b48973e972aa1609b`, run
`workset-r2-docs-01` / `20261029T233058Z_6ae6b3f4`, passed 9/9 in 124.931
seconds with no skips, unrun cases, harness errors or observed sleep. Command:
`tests/run.sh --suite source_drift --case preflight/build_entry_controls` with
that fresh PW_TEST_OUT_DIR. It includes the previously failing generator case.

Primary diff review confirms only the named generator-label/document/citation
corrections, workset/D2 records and retention changed after fd90eee. Production,
tests, contract/limits/build manifests, build inputs, generated constants and
identity remain identical. The final-run before and BYOXPC-rerun after app
inventories are identical. Thus 197 unaffected passing cases from the full run
retain their original credit, while these nine current results replace their
older credits: 206 distinct selected cases have passing evidence. The remaining
BYOXPC case failed twice and has no acceptance credit. This is an explicit
reviewed applicability exception, not a claim that a single 207-case run passed.
The F2 record supplies the observed failure and exact retained-resource state.

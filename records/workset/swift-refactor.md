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

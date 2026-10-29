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
| Shared `PWRunnerCoding.swift`: move private RequestKey, rejectUnknownRequestKeys, pwRunnerEncodeJSON and pwRunnerDecodeJSON unchanged | Eleven request-object decoders plus host/client JSON boundaries | Common mechanics for separated request, extension and reply families |
| Host-only `CWorkerDisposition.swift`: move uniquelyAssociatedWorkerSlots with internal visibility | buildStepResults and resolveDisposition | Disposition owner, preserving rejection of duplicate-ID association |
| Make only makeWorkerSlot and workerParamsFromPolicy internal | Current run/admission translation | Calls from run into the separate request-planning owner |
| Explicit shared-contract source list in Meson and independently declared expected set in native_sources.py | Shipped client and host | Add each wire-family owner without including host service/listener/processing |

There is no unused layer. RequestKey remains private beside its helper.
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

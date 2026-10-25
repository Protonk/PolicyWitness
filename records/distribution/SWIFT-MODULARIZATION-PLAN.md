# Proposal: Swift API and orchestration modularization

Planning baseline: `838b33b2b55546e41808f5d75efb667487a4bbed`

## Objective and scope

Reorganize two files through a bounded, behavior-preserving effort:

- [PWRunnerAPI.swift](../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift)
  owns the XPC protocol, request/reply types, encoding and decoding, and
  evidence validation shared by the host and client.
- [CWorkerOrchestrator.swift](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
  translates requests, plans validator queries, invokes drivers, associates
  observations, and constructs dispositions, classifications and comparisons.

The acceptance criterion for a split is that a reader can understand one
responsibility with fewer unrelated details while keeping the evidence needed
to judge its correctness nearby. File counts and line limits are not targets.
Here, a module means a cohesive source group within the existing Swift build
targets; this proposal does not introduce new packages or runtime components.

Stages 1 and 2 form one complete effort, with separately reviewable checkpoints.
Rust decomposition, C decomposition, and extraction of responsibilities from
`CWorker.swift` are outside scope. Worker phase progression remains unchanged.
A later `CWorker.swift` proposal is independent: no work here exists solely to
prepare it, and completion does not depend on it.

Necessary call-site adjustments, build inventories, generators, tests and
documentation are included. Generated worker-identity updates may touch
`CWorker.swift`, the C ABI header and test constants; these do not authorize
driver or C implementation refactoring.

## Stage 1: establish usable boundaries

Prepare specific extractions from the two files. Make dependencies and helper
ownership explicit, resolve file-scope access where needed, and introduce
small supporting modules only where existing callers can use them immediately.
Leave already self-contained sections for Stage 2.

**Every Stage 1 change must name the Stage 2 extraction it enables.** Record
the affected responsibility, current symbols, callers and intended destination
in the change description. This is the limit on preparatory work.

Stage 1 is accepted when:

- Each introduced boundary has a current caller and a named Stage 2 use;
  there are no unused interfaces or modules awaiting future adoption.
- Inputs, outputs and ownership are explicit enough for the named extraction
  to proceed without redesigning behavior. Visibility changes expose only what
  those callers need.
- Shared contract code compiles in both host and client without depending on
  worker drivers or orchestration. Host-only processing remains host-only.
- The stage builds and passes the applicable checks below as a complete
  implementation, with no dependency on unfinished Stage 2 code.

## Stage 2: extract cohesive responsibilities

Organize the same two files around the established boundaries. The current
source provides these candidate responsibility families:

| Source | Families to organize |
| --- | --- |
| API | XPC/envelope definitions and constants; requests and admission; prediction/attempt/ordering records; lifecycle, extension and compiled-profile evidence. |
| Orchestrator | Request translation and query planning; step/subprocess result construction; evidence association and comparisons; disposition and outcome classification. |

Choose filenames and the number of groups by the acceptance criterion. Keep
each wire family's types, `CodingKeys`, custom encoding/decoding and local
validation together. Checks spanning several families need an explicit owner
and visible callers.

Stage 2 is accepted when:

- The extracted responsibilities have identifiable owners and narrow
  dependencies. Reviewing a wire family does not require assembling its
  definition, codec and local validity rules from unrelated groups.
- The orchestrator retains a readable execution sequence. The placement of
  query planning, collection, driver invocation, evidence assembly and cleanup
  remains apparent; extraction does not hide new side effects in initialization
  or callbacks.
- Stage 1 modules are used by the extractions they enabled. If an extraction
  exposes an unsuitable boundary, revise or remove it and explain the resulting
  ownership; retaining an awkward boundary solely for reuse is not acceptance.
- No unused preparatory layers or duplicate implementations remain. The runner
  source map describes the completed organization.

## Shared acceptance criteria

Both stages preserve accepted and rejected requests, wire shapes and meanings,
encoding/decoding behavior, evidence validation, classifications, and the
retention or withholding of claims on incomplete and failed runs. Wire versions
remain unchanged under the [contract rules](../../docs/CONTRACT.md). Behavioral
repairs discovered during the work are separate changes.

Fresh-process ownership, resource acquisition and cleanup, query eligibility,
collection closure, release/acknowledgement ordering and publication semantics
remain unchanged. A permission-shaped failure still does not establish sandbox
cause, and comparisons still make no prediction/enforcement agreement claim.

The shipped host, client and SwiftPM tests compile the intended source sets.
Today [meson.build](../../meson.build) and
[native_sources.py](../../tests/lib/native_sources.py) explicitly give the
client `PWRunnerAPI.swift` plus its entry point. Update that shared-source
boundary with the extraction, without including host implementation merely to
make client compilation succeed.

Update checks and citations that locate definitions in the original files so
they still inspect the actual owners. Preserve their rejection controls and
independent expectations. Update generator inputs and regenerate owned outputs,
including [worker identity](../../docs/generate_worker_identity.py); source
paths participate in that identity even when runtime behavior is unchanged.

## Verification and completion

Verify each stage through the signed [build pipeline](../../docs/BUILD.md) and
the [test dispatcher](../../tests/README.md), following
[test selection and evidence rules](../../tests/AGENTS.md). Required evidence
covers:

- Source membership, generator ownership/freshness and documentation citations
  through `source_drift`, including controls that reject missing definitions
  or incorrect source membership after relocation.
- Request/reply admission, encoding and evidence interpretation through the
  relevant `runner_unit`, `failure_boundaries`, `unit` and independent consumer
  controls. Preserve rejected-input and incomplete-evidence assertions as well
  as successful cases.
- Integrated ordering, partial results and failure handling through applicable
  `integration`, `witness_contract`, `runner_validator_failure`,
  `runner_abi_layout` and `runner_c_worker_harness` cases against the matching
  signed app. Compilation and source checks alone do not establish these facts.

If query eligibility implementation is moved or reworked, include the opt-in
`witness_contract/order_barrier_mutations` control. The worker wait and release
store are outside this effort's implementation scope.

Completion requires the default battery against the final signed build, plus
applicable change-specific opt-in controls, with fresh output directories and
recorded source/build identities. The final review identifies the responsibility
owners, the Stage 1 boundaries adopted or revised in Stage 2, and the evidence
supporting unchanged behavior. Stages 1 and 2 are then complete without any
pending `CWorker.swift` extraction.

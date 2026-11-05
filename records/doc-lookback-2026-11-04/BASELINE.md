# Documentation lookback baseline and neutral change brief

Baseline ID: `lookback-ea64218b`. Exact revisions and SHA-256 values are in `baseline.json` in this directory. The checkout was clean before review records were created. Review records are the only planned writes during the initial review; the candidate documents and implementation remain at the recorded state.

## Comparison boundary

Compare `990dc322` (parent of the actor integration) with `ea64218b` (current HEAD). The integration is `c686a05f`; include the repairs in `557f98de` and `deb67eff`, not only the first integration. Later commits retain evidence and refine this review plan. The historical `SANDBOX-EXTENSION-WITNESSING-PLAN.md` at `990dc322` describes the starting single-worker/declaration capability and intended integrated actor capability. The integration commit message and `records/RETAINED-RESOURCES.md` identify its squashed branch and acceptance records. These make the boundary sufficiently definite to proceed. Earlier declaration-form extensions are baseline behavior whose explanations may be affected by the actor update.

## Changed mechanisms and paths

- The actor request form adds per-actor apply/unapplied setup and a specimen-wide serial phase schedule. Actor ownership, typed producer/delivery/handle references and aggregate capacities are admitted before launch. Existing single-worker and declaration forms remain supported. Owners include `PWRunnerActors.swift`, `ActorPlan.swift`, `PWRunnerRequest.swift`, `PWRunnerExtension.swift` and `ProbeRunner.swift` under `runner/Sources/PWRunnerCore/`.
- Fresh sibling workers retain state across their visits. Host orchestration, launch/session setup, phase activation, parked servicing, collection/release and cleanup now account for several workers. Primary owners are `ActorOrchestration.swift`, `ActorScheduler.swift`, `ActorSession.swift`, `CWorker.swift`, and the C worker/ABI under `controller/tools/pw_probe_runner/`.
- File issuance occurs in the issuing actor. Transient host custody, per-actor authority mappings, recipient validation/acknowledgement, and one-shot issue/transfer publications join explicit issue, transfer, consume and release actions. Owners include `AuthorityCustody.swift`, `pw_authority_region.h` and `pw_probe_runner.c`. Declaration issuance continues through its ordinary-authority helper. This changes authority lifetime, resource acquisition, channels and erasure questions without moving native sandbox calls into the host.
- Replies, controller interpretation and independent Python readers carry actor-indexed policy/process/phase evidence, extension events, resources, transfers and partial publications. Repairs address launch/evidence associations, handoff settlement, unknown quiescence, empty visits and late setup observations. Owners include `PWRunnerReply.swift`, `PWRunnerTransport.swift`, `controller/src/disposition.rs`, `controller/src/run_flow.rs`, `tests/lib/consumer.py` and `tests/lib/extension_evidence.py`.
- Actor capacities/timing, shared region geometry, publication slots, reply bounds and client retention change. The current contract manifest carries the current version values. Actor-related unit/native/public controls and existing declaration controls supply possible evidence; passing claims in commit messages are navigation aids, not independent verification for this review.

## Documentation and source ownership

Review authored and generated text as one reader account. ARCHITECTURE and WORKER include authored content and generated regions/scalars owned by `docs/architecture.json` and `docs/generate_architecture.py` with related inputs. LIMITS includes authored prose and records owned by `docs/limits.json` / `docs/generate_limits.py`; shared prose is copied into `docs/PolicyWitness.md`. Identify the owning input before any later edit.

The README index describes ARCHITECTURE as one run through boundaries, WORKER as resources/authority/constraints, and LIMITS as limits. Their openings align broadly with the plan's audiences. LIMITS makes the stronger opening claim that it lists every limit of its stated kind; the coverage audit should assess that promise. No audience has been silently changed to fit an opening.

## Evidence availability

Current local verification is under `tests/out/runs/actor-passes-default-02` and `tests/out/runs/actor-passes-final-controls-02`; review/source snapshots are in the former's `review/`. Those are gitignored, checkout-local evidence. Earlier integration evidence is in the separately retained `PolicyWitness-extension-actors` worktree described by `records/RETAINED-RESOURCES.md`. No artifact, signature, native run or behavior has been reverified in establishing this baseline.

## Scope and staging

ARCHITECTURE: inclusion map after a whole-document read. WORKER: conservative exclusions after a whole-document read; retain cross-cutting uncertainty. LIMITS: every entry and surrounding explanation plus a separate missing-limit search. Both scopers receive this same brief. Readers receive only baseline identifiers and bounded materials until their initial document-use result is captured. All substantive findings remain provisional pending coordinator review and appropriate evidence.

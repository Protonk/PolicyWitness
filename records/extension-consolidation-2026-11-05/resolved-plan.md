# Proposed admission and resolved execution contract

Status: Stage 2 proposal, not accepted or implemented. Source baseline:
`4cd1d6c7f14e3ebacfd2dda219dda85967f64680`.

## Source findings

The current public host normalizes actor meaning in
`PWRunnerService.runReservedSpecimen` through `requestMeaningFailure`. Its
orchestration closure passes the request, not that result. `CWorkerOrchestrator.run`
repeats admission and meaning, then calls `normalizeActorPlan` a third time.
The final failure branch substitutes `missing_field` at `actors`. Direct
orchestration repeats the latter two passes. These are source findings, not
an assertion that a current request can make those identical passes disagree.

`ActorPlan` retains mutable resource arrays and request-shaped phase actions.
`ActorTranslation` reconstructs their meaning: names are searched again,
missing actions are skipped, missing references/positions become index zero,
and the default operation switch encodes release. `AuthorityPlan` is then
constructed separately using the same fallbacks. Current public normalization
prevents many such inconsistencies; the change removes their representation
and silent recovery, rather than claiming they are demonstrated public bugs.

The source owners are `ActorPlan.swift`, `ActorOrchestration.swift`,
`AuthorityCustody.swift`, `CWorkerOrchestrator.swift`, `ProbeRunner.swift` and
`PWRunnerService.swift` under `runner/Sources/PWRunnerCore/`.
`ActorPlanTests.swift` already checks reference ownership, repeated consumes,
self-transfers and actor-local positions for empty revisits. It does not make
the current default/fallback branches correct in the presence of an inconsistent
internal plan. The new controls below must exercise that boundary explicitly.

## One authoritative meaning

Use distinct small index wrappers. Their initializers are private to the
preparation owner, and conversion to C integer operands is checked there.
Separate actor, phase, action, actor-local slot, actor-local visit, token,
delivery and handle indices even when their integer values coincide.
No actor index is a PID; no planned token or handle index proves a native
resource exists.

The following Swift sketches specify the representation, not code to copy
without fitting the existing types:

```swift
enum ResolvedExtensionOperation {
    case issue(token: TokenIndex)
    case transfer(token: TokenIndex, delivery: DeliveryIndex,
                  recipient: ActorIndex)
    case consume(delivery: DeliveryIndex, handle: HandleIndex,
                 lastDeliveryUse: Bool)
    case release(handle: HandleIndex)
}

enum ResolvedActionBody {
    case probe(ResolvedProbe) // admitted query and typed attempt
    case authority(ResolvedExtensionOperation)
}

struct ResolvedAction {
    let id: String
    let index: ActionIndex
    let actor: ActorIndex
    let phase: PhaseIndex
    let slot: ActorSlotIndex
    let body: ResolvedActionBody
}

struct ResolvedVisit {
    let id: String
    let index: PhaseIndex
    let actor: ActorIndex
    let actorVisit: ActorVisitIndex
    let slots: Range<Int> // exact contiguous actor-local half-open range
    let actions: [ActionIndex]
    let afterTermination: ActorIndex?
}

struct ResolvedToken {
    let name: String
    let owner: ActorIndex
    let outboundPosition: AuthorityOutboundIndex // local to owner's region
    let producer: ActionIndex
    let producerSlot: ActorSlotIndex
    let target: AbsoluteSubmittedPath
    let authority: FileAuthority // .read or .readWrite; native flags stay zero
    let deliveries: [DeliveryIndex]
    let lastUse: ActionIndex
    let lastUseSlot: ActorSlotIndex
}

struct ResolvedDelivery {
    let name: String
    let token: TokenIndex
    let source: ActorIndex
    let recipient: ActorIndex
    let inboundPosition: AuthorityInboundIndex // local to recipient's region
    let producer: ActionIndex
    let producerSlot: ActorSlotIndex
    let handles: [HandleIndex]
    let lastUse: ActionIndex
}

struct ResolvedHandle {
    let name: String
    let delivery: DeliveryIndex
    let owner: ActorIndex
    let producer: ActionIndex
    let release: ActionIndex?
}
```

`ResolvedActor` owns its application mode/policy, requested equipment and
entitlement requirements, ordered action indices and visit indices, and the
derived `authorityRequired` bit. An actor participates if it issues, transfers,
receives, consumes or releases anywhere; the existing per-actor exec exclusion
remains. An actor with no authority operations remains valid and visits can
be empty. All actors still need at least one visit.

`authorityRequired` means an authority region is assigned, not that the actor
personally has an authority action. Preserve current provisioning: when the
specimen has an authority plan, every actor receives a required region, including
actors with zero authority operations. With no authority plan, no actor receives
a region and descriptor absence is not-required. This is the applicability rule
in `setup-lifecycle.md`; selective region provisioning is outside consolidation.

`ResolvedActorPlan` is immutable after construction. Names remain in metadata
for diagnostics and reply construction. Dictionaries used to resolve submitted
names live only inside its builder. Arrays referenced by this plan are not
duplicated into a separately mutable request graph. Runtime custody/handle
availability is separate state keyed by these indices.

Global resource indices remain the current C protocol's resource identifiers.
Preserve the current compact **actor-local region positions** separately:
`AuthorityCustody.init` currently builds `outboundSlotOfToken` by counting each
issuer's tokens and `inboundSlotOfDelivery` by counting each recipient's
deliveries. Move those deterministic assignments into preparation. Store each
token's outbound region position and each delivery's inbound region position
alongside its global resource index, owner and producer action slot. Region
headers/assignments retain the global resource identity while addressing the
actor-local payload position. Size each region from its actor's inbound/outbound
counts, including a header-only region for a zero-operation actor. The scheduler,
custody owner and encoder consume these assignments without recomputing a second
resource graph. This preserves existing geometry instead of introducing an
unrelated layout optimization.

## Preparation and admission ownership

1. Version-first decoding rejects unknown fields and wrong types. Capacity
   admission runs before semantic construction, preserving bounded diagnostics.
2. `admitSpecimen` returns either the original `PWRunnerRequestFailure` or an
   `AdmittedSpecimen` containing immutable ordinary or actor execution meaning
   and diagnostic metadata. Pure normalization does not inspect the filesystem,
   signatures, process state, or native API availability.
3. `bindEquipment` consumes admitted actor meaning and a freshly validated
   bundle inventory. It creates `PreparedActorExecution` with one launch record
   per actor. Each combines the resolved actor, concrete executable identity,
   application inputs and mechanically encoded C slots/phases. The equipment
   contract is specified separately in `authority-equipment.md`.
4. All checked indices, actor-local partitions, authority assignments and
   equipment bindings are finalized before creating authority regions or
   launching the first actor. No actor starts if any launch record cannot be
   prepared. Host authority-region preparation follows this boundary and has
   its own observations/refusal path.
5. The scheduler, custody owner and reply assembler receive views of this
   same immutable prepared plan. A view may contain mechanically encoded data,
   but cannot reconstruct semantics from submitted names or be independently
   mutated. Runtime records remain separate from the plan.

Change `PWRunnerService`'s orchestration seam to accept `AdmittedSpecimen`.
The live host calls the preparation owner once and passes its actual accepted
result forward. A direct-orchestration convenience entry used by tests first
calls that same owner, then the same admitted entry. There must not be a public
entry that accepts a request plus an unrelated claimed plan. Client-side
validation remains independent of the host; it does not satisfy host admission.
Worker identity/input checks remain independent of both.

The ordinary form retains its policy, `probe_plan`/ordinary `phases`, query
planning and fresh worker lifecycle. Its extension-action branch disappears.
Both ordinary and actor forms use exhaustive admitted action encoders. Ordinary
request decoding refuses any extension action instead of creating an executable
ordinary authority path.

## Mechanical encoding and internal errors

Encoding switches exhaustively on `ResolvedActionBody` and the four authority
cases. Issue obtains its exact submitted path and authority from its token;
transfer writes its already resolved token/delivery/recipient;
consume writes its delivery/handle/last-use flag; release writes its handle.
No default release case, string search, `?? 0`, action skip or fallback target
is permitted. Private encoder functions need no wider visibility unless a
real caller requires it.

Checks cover table membership, resource ownership, action/phase/slot agreement,
per-actor contiguous partitions, last-use ordering, dependency placement and
representable C operands. Factory construction should make most violations
unrepresentable. Any remaining fallible boundary returns `PreparationFailure`
before spawn. Do not turn an internal inconsistency into a malformed submitted
request or silently repair it.

Proposed reply for admitted but unpreparable actor execution:

```json
{
  "schema_version": 26,
  "execution_form": "actors",
  "rc": 1,
  "normalized_outcome": "runner_failed",
  "preparation_failure": {
    "stage": "resolved_plan",
    "code": "inconsistent_assignment",
    "actor_id": "subject"
  },
  "steps": [],
  "extension_events": [],
  "transfers": []
}
```

This is a constructed reply projection. Common envelope/host metadata is
omitted here. `request_failure` is absent. Actor records retain each admitted
actor and `setup_status: "launch_refused"`, without a launch or subprocess.
Host authority setup is `not_attempted`; no native setup success is invented.
The same shape uses `stage: "equipment"` for equipment failures, whose closed
codes and inspected facts belong to the equipment contract. Failures are
bounded structural diagnostics, never token bytes or arbitrary internal dumps.

## Request removals and version decision

Propose request **6**, response **26**, controller envelope **11**, and runner
protocol **3**. The first two bumps follow removal of declarations and their
reply fields; the envelope bump follows per-actor equipment/provenance reading
rules. Reservation RPCs, capture and replay prohibition do not change, so the
runner protocol remains 3. Regenerate the worker identity for implementation
and C/Swift layout changes. No historical semantic reader or adapter is added.
The committed `docs/contract.json` remains unchanged until acceptance.

Remove top-level `extensions` from allowed keys, including the explicit null
spelling: schema-6 `extensions: null` is `unknown_field` at `extensions`.
The same current-version negative control must be exercised at the CLI and
direct XPC boundary. A request carrying schema 5 instead receives unsupported
version refusal first and cannot count as the removed-field control.

`consume` accepts only `delivery_ref` and `handle_ref`; `token_ref` is
inapplicable, including an explicit null key. Likewise, any extra operation
operand is rejected by key presence, not only by a non-null decoded value.
Required operands must be present strings. `issue` continues to require
`family: "file"`, `authority: "read" | "read_write"`, an absolute target,
and `token_ref`. There is no declaration authority default to carry forward.
Transfer keeps `token_ref`, `recipient`, `delivery_ref`; release keeps
`handle_ref`. No user-supplied token bytes/classes/native flags are admitted.

Remove `issuer_executable_path` from `_test_overrides`, including null.
Other obsolete declaration-only controls are removed wherever the ledger
finds their producers or readers. Equipment test substitutions are specified
in the equipment contract; a substituted executable cannot establish the
property of an unmodified packaged variant.

New `equipment`, actor `required_entitlements`, and `after_termination` fields
use omission for their documented default/absence. Explicit null is a type
refusal. Unknown equipment or gate keys are rejected. Existing null semantics
of unrelated request fields are unchanged.

## Refuting controls

Extend `ActorPlanTests` and actor translation/authority tests through their
registered `runner_unit/pwrunner_core_unit_executable` owner. Use multiple
tokens, deliveries and handles with nonzero indices; consistently rename
actors; reorder actor declarations; retain empty revisits. Compare exact C
operands and custody assignments to independently specified owners/resources.
Use a test-only preparation injection to reject inconsistent assignments before
a counted spawn boundary; do not expose an unsafe constructor in production.

At the host service seam, count normalization and require the actual accepted
plan to reach orchestration once. Return a distinctive normalization failure
and assert it survives, rather than the present synthetic `missing_field`.
Capacity/version refusals must still precede normalization, equipment binding
and spawn. Query planning stays fresh per visit, after arrival; resolving
operation meaning once does not pre-collect sandbox queries.

Pair these structural controls with `runner_c_worker_harness/actor_operations`
through production `run_attempt`, the mixed-equipment live permutations,
custody/handoff mutation controls and independent reply reader substitutions.
Each control establishes its own boundary; constructed plans alone do not
prove live authority or process identity.

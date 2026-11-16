# Protocol reading and promotion decision

Source/check review on 2026-11-15 for steps 5 and 6 of
[the documentation trace plan](../../DOCUMENTATION-TRACE-PLAN.md), starting from
`2fcf9dbc9f08b1643426b4cf9b9b32e3782c86cc`. No tests were executed for this
review. The baseline ARCHITECTURE prose and authored statements were read
against the named sources and selected assertion bodies. This is an integration
recommendation; the executor must still read the final generated arrangement.

## Decision

No tree promotion is needed for the three promises. Once-only invocation and
extension custody already have complete protocol subjects among the seven
incoming units. ARCHITECTURE's `One run in time` narrative can state collection
before release whole, including failure and observation qualifications, without
extracting declaration or returned-evidence nodes. Its detailed `query_first`
interpretation can link to the complete `steps.assessment.order` rule, which
already holds the required chain, setup, native-answer and association clauses.

One public rule needs correction regardless of placement:
`actors.phase.order` describes actor schedule advancement more strictly than
the implementation and its existing tests. This is a source-established prose
correction, not a request to change runtime behavior. A separate wording change
is needed for `wire.standalone`'s positional link. Both are detailed below.

## Collection before release

The opening of [One run in time](../../docs/ARCHITECTURE.md#one-run-in-time), its
timeline, the paragraphs after the timeline, and the `The barrier` implementation
route already state a coherent protocol: fresh planning at the arrived phase,
eligible collection against the owned live worker, closure before guarded
numbered release, worker acknowledgement before actions, action order, completed
phase progression, and independent publication/cleanup observations. The actor
handoff section supplies the failed-active-visit/quiescence qualification.

The whole promise can be read as follows. At an eligible arrived phase the host
collects queries while that worker's requested actions wait, closes the
collection, rechecks child ownership and phase state, and only then publishes
that phase's release ordinal. The worker acknowledges the matching ordinal
before actions. Closed collection can retain unavailable predictions and
unconfirmed validator cleanup; neither means the worker was released. A late
release cannot revive a worker's refused wait. Each completed action has its own
publication. Ordinary later phases require previous completion; actor visits
advance under the actor scheduler's separate availability, quiescence and
cancellation rules. These qualifications are part of the reading, not exceptions
to be left behind in another document.

The returned `query_first` claim is narrower than that protocol. It additionally
requires established setup, the complete collection/release/acknowledgement and
worker-ownership chain with no violations, and one matching retained eligible
native answer for that step and owned worker PID. The exact operation, filter,
value, outcome, native rc and errno must agree. That whole interpretation is
`steps.assessment.order`; `steps.assessment.meaning` explains the interval limit.
Earlier actions can change the state encountered by later attempts after their
queries were collected. The claim does not establish prediction/enforcement
agreement. An acknowledgement read after confirmed reap can establish the
earlier interval if ownership remained unbroken, without changing the abnormal
ending or inventing `done`.

Read source and checks:

- [`runCWorker`](../../runner/Sources/PWRunnerCore/CWorker.swift), especially its
  arrived-phase loop, checks application, identity, prior completion, premature
  publication and child ownership before the callback; sets `collectionClosed`
  after the callback; rechecks the child and phase before `releaseVisit`.
- [`walkSchedule`](../../runner/Sources/PWRunnerCore/ActorScheduler.swift)
  checks actor availability, setup, remaining allowance and any explicit
  termination dependency before activation; performs collection before its
  guarded release; services custody before observing phase completion.
- [`ActorSession`](../../runner/Sources/PWRunnerCore/ActorSession.swift)'s
  `checkPrematurePublication`, `releaseVisit`, `observeAcknowledgement` and
  final reconciliation establish the host-side publication/ownership account.
- [`wait_for_proceed`](../../controller/tools/pw_probe_runner/pw_probe_runner.c)
  samples clock validity and remaining wait before accepting the ordinal;
  refuses a future ordinal; checks cancellation before acknowledgement; then
  `main` runs the phase's slots in order and publishes phase completion.
- [`buildOrdering`](../../runner/Sources/PWRunnerCore/CWorkerComparison.swift)
  records closure, release, acknowledgement, worker lifetime and violations;
  validator disposition is separately retained. [`eligibleOrderedStep`](../../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift)
  checks the unique exact native association and setup in addition to the chain.
- [`OrderingTests`](../../runner/Tests/PWRunnerCoreTests/OrderingTests.swift)
  reads a held fixture receipt before permitting release; its surviving
  validator control observes a completed attempt and later `EPIPE` after closed
  collection with unconfirmed reap. Those fixture query answers are controlled
  data. [`PhaseProtocolTests`](../../runner/Tests/PWRunnerCoreTests/PhaseProtocolTests.swift)
  and the [reader replay account](../../tests/suites/runner_unit/README.md)
  separately retain multi-phase collection and reader checks.
- The [order-barrier mutation control](../../tests/suites/witness_contract/README.md#predictions-before-attempts)
  has worker-wait and host-release mutations with independent early-effect
  assertions. Its existing procedure was read; no mutation or historical run is
  newly credited here. Documentation changes alone do not require that native
  mutation rerun; changing the actual wait, release or eligibility would.

For integration, keep a named `Collection before release` explanation within
`One run in time`, consolidate the present opening and post-timeline
qualifications there, and link `actors.phase.order` for the scheduler obligation
and `steps.assessment.order` for the exact returned claim. Do not move their
individual child clauses separately. The current architecture account already
contains the essential mechanism; an extra protocol subject would add identity,
scope and owner migration work without solving a missing reading path.

### Correct the actor advancement statement

The current `actors.phase.order` free effect says, unconditionally, “Begin the
next phase's collection after the previous phase completes.”
[`walkSchedule`](../../runner/Sources/PWRunnerCore/ActorScheduler.swift) instead:

1. Skips an unavailable actor/session/visit before activation and collection.
2. On failed active visit, stops that actor and requires its recorded quiescence
   to be `reaped` before further activation.
3. Cancels on unresolved termination, arrival/completion timeout, or wait error;
   other failures with confirmed reap allow another available actor to continue.
4. Separately cancels after a failed evaluated termination dependency or an
   exhausted schedule allowance. An unevaluated gate on an unavailable actor
   does not independently cancel later actors.

[`runActorSchedulerTests`](../../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift)
contains two direct counterexamples to the old unconditional wording:
`a failed setup leaves the other actor's visits intact` expects
`[actor_unavailable, completed, actor_unavailable, completed]`; `the active
actor's death is established before the next activation; later actors continue`
expects `[died_before_completion, completed, actor_unavailable, completed]`.
The latter uses the real worker's kill-before-publication seam and also checks
the earlier PID is absent at later actor collections, absent completion/done,
confirmed reap and retained SIGKILL. These are assertions read from tests, not
new observations.

Proposed bounded replacement for that rule's `free.effect`:

> Close the active phase's eligible prediction collection before releasing its
> actions; run those actions in declaration order. In ordinary execution begin
> the next phase's collection only after the previous phase completes. In the
> actor form walk the declared schedule serially while it remains uncancelled
> and has execution allowance, activating one actor at a time while others
> remain parked. Skip unavailable actors or visits. After a failed active visit
> establish that actor's reap before any further activation; unresolved
> termination cancels the remaining schedule. Arrival or completion timeout
> cancels for exhausted execution allowance, and a wait error cancels for lost
> ownership. A failed evaluated termination dependency also cancels the remaining
> schedule. Other available actors may continue after the failed actor is reaped.

Leave `who`, `where`, `entry`, `recipient`, `report`, `uses` and support scope
unchanged unless an explicit new source association is added. The existing
`disposition_support` only cites ordering eligibility, and the phase-level
owner explicitly limits itself to admission/normalized order. A separate local
owner for the correction can cite `walkSchedule`, `runCWorker` and
`runActorSchedulerTests`, with grade `check_read`, a pin naming the skip/reap/
continue distinction, and a limit that this review credits no execution.
Do not broaden the existing admission or eligibility owners to claim these
runtime assertions.

This is an `actors` public payload change, confined to `actors.phase.order`'s
prose/fact and any accurately revised retained-free explanation. No shape,
runtime code, declared schedule, per-phase publication, gate condition or
ordering eligibility change is needed. ARCHITECTURE's existing failed-visit
paragraph already agrees with source and should be retained.

## Once-only invocation under the original allowance

`transport.delivery` states the entire promise in one subject: effect-free
reservation, connection-bound one-use slot, bounded acquisition retries, control
admission, one execution invocation after a fresh deadline sample, invocation
recorded before proxy acquisition/call, no replay after any later error, and
one original continuous-time allowance including machine sleep. Client expiry
does not bound controller draining or host/worker cleanup. Peer PID and instance
values remain peer assertions. `transport.reservation` and `transport.control`
provide the adjacent control-record meanings without splitting the protocol.

[`PWRunnerClientSession.reservationReply`](../../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
admits a grant, resamples time, refuses expiry, moves to submitted and records
invocation before `connection.submit`. Terminal guards ignore late callbacks.
[`PWRunnerAdmission`](../../runner/Sources/PWRunnerCore/PWRunnerReservation.swift)
holds one locked slot across connections and moves it toward executing or
retiring; expiry/disconnect cannot make it free again. The source matches the
statement's narrower client-call meaning: a positive invocation observation
does not prove receipt, admission, effects or a delivered reply.

[`runClientSessionControls`](../../runner/Tests/PWRunnerClientSessionTests/main.swift)
checks late grant, original deadline, submission error/timeout/refusal and proxy
failure without replay using injected clock/scheduler/connection boundaries.
[`runReservationAdmissionTests`](../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift)
checks connection ownership, slot retirement and expiry. Preserve the existing
surface-level support and its explicit limits; these checks are not a complete
native XPC or signed foreign-host fault matrix.

Integrate the whole delivery subject near `Why these processes exist`'s present
reservation paragraph, replacing that overlapping summary with a short
orientation to the complete generated statement. Keep `transport.authorization`
immediately before reservation and the two control subjects nearby. Their
surface-level owner remains in RESPONSE with unchanged subtree scope; each
rendered protocol must link to that owner. No promotion or split is warranted.

## Extension custody from preparation to erasure

`extensions.custody` already holds preparation, issue, transfer, source-answer
observation, last-use retirement and teardown in one complete subject. Retain
the following distinctions as it moves into the actor-handoff account:

- Required host custody preparation prevents all actor launch on failure;
  worker setup precedes policy application or unapplied declaration. Missing
  native symbols make reached operations unavailable separately from required
  setup failure.
- Issue publishes only bounded nonempty native token bytes in its assigned
  one-shot slot. Native allocation erasure/free precedes publication; published
  outbound bytes remain immutable for the host even after worker timeout/exit.
- Framing acknowledgement precedes full byte equality and usable settlement.
  Parked and self-transfer servicing does not consume. Consumption requires
  settled, committed, accepted delivery.
- A late host answer is independent of source completion. Source acknowledgement
  requires the completed action's answer to match the host's nonzero answer.
- Last declared transfer retires private custody even for an unavailable
  recipient. Last declared consume and normal exit erase worker-owned settled
  input. Unknown actor termination permits host detachment, not shared erasure.
  Token erasure, native handle release and later access observations differ.

Read [`AuthorityCustody`](../../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
initialization, `serviceOutbound`, `serviceTransfer`, `recordSourceAcknowledgements`
and `finish`, and the worker's `prepare_authority`, `attempt_extension_issue`,
`service_inbound_once`, `attempt_extension_consume_actor`, `erase_authority` and
`publish_done_and_exit`. These show the ownership transfer and refusal/cleanup
branches named above. [`ActorAuthorityTests`](../../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift)
has separate controls for immutable outbound assignments, unknown-quiescence
retention, source-answer matching and the parked-recipient exchange. The
protocol's existing support remains source-read; this review does not convert
the listed controls into execution credit or a general assertion about opaque
private-library or kernel token state.

Replace the overlapping five-item explanation under `Actor handoff and schedule
advancement` with the complete generated custody subject at that point, keeping
the opening schedule sequence and the following failed-visit/quiescence
paragraph. Keep its relevant mechanism/check links as a short route after the
generated statement. Preparation and erasure must remain in the same readable
subject even though the surrounding narrative begins at a scheduled handoff.

## The other incoming subjects and positional wording

Place `wire.frame` and `wire.validator` as complete statement regions near
`Boundaries`, after a short explanation distinguishing typed host/client frames
from validator JSON lines. Neither should be duplicated as a second account
elsewhere. `wire`'s surface introduction and owner stay in ARCHITECTURE; their
links to standalone records in RESPONSE must retain original scope.

`wire.standalone` currently says `--batch PID` “selects the line protocol above.”
After its move to RESPONSE that referent is in ARCHITECTURE. Change only that
phrase to “selects the [validator query and reply line
protocol](../../docs/ARCHITECTURE.md#contract-wire-validator)” in the rendered
reading. In authored source use a destination-independent
`[validator query and reply line protocol](#contract-wire-validator)` so the
renderer chooses the home. This is a named `wire.standalone` public-prose
change, not placement-only rebasing. Keep its argv, leading-mode exclusivity,
native result/exit distinctions and historical execution support untouched.

The `wire` surface introduction's “line protocol below” remains true if
`wire.validator` follows that introduction in ARCHITECTURE. Confirm actual
render order during final acceptance; no public rewording is needed merely to
remove every positional word.

## WORKER commitment lists

These associations were chosen by reading the actual sections and matching
their described mechanisms, not by treating every citation as coverage. The
lists do not replace prose or promote full statements into WORKER.

| Existing section | Proposed node IDs | Reason and limits |
| --- | --- | --- |
| `Capability map` | `actors.actor.fresh`, `actors.phase.order`, `extensions.custody` | Summarizes fresh processes, held actions and the actor token path. Keep generated inventory detail as its existing generator's region. |
| `What the worker can establish` | `steps.assessment.assembly`, `steps.assessment.observe`, `extensions.custody.native_library` | Distinguishes native observation, publication, host assessment and causal limits. The section supplies no complete ambient-authority census. |
| `Reporting apparatus` | `identity.other.worker`, `lifecycle.worker_evidence`, `policy.spec.parameters`, `profile.receipt` | Describes shared report storage/identity, consumed compiler inputs and pre-apply profile capture; receipt admission is the host's separate operation. |
| `Starting authority and ambient context` | `actors.actor.fresh`, `actors.sandbox`, `actor_evidence.launch`, `extensions.operation.exec`, `extensions.custody.prepare` | Connects inherited context, apply/unapplied setup, launch records and participation-based exec exclusion. Launch observation L remains dated and separately qualified. |
| `Acquisitions inside attempts` | `probes.attempt`, `steps.assessment.fresh`, `steps.fresh_read`, `steps.fresh_write`, `steps.assessment.fresh_read_aggregate`, `steps.assessment.fresh_write_aggregate`, `lifecycle.exec` | File, Mach, sysctl and exec acquisition descriptions lead to action/observation definitions; detailed exec collection/cleanup/reap subjects remain reachable from `lifecycle.exec`. |
| `Supplied extension authority` | `equipment.binding.bind`, `equipment.execution.inspect`, `equipment.authority_scope.acquire`, `actor_evidence.gate.evaluate`, `extensions.custody`, `extensions.operation.references` | The present section includes equipment binding, live inspection, authority setup, gate prerequisites and complete resource lifetime mechanisms. Linking custody whole avoids assembling its clauses from scattered links. |
| `Native observations and publications` | `steps.assessment.assembly`, `steps.assessment.fresh`, `actors.phase.order`, `steps.assessment.order`, `lifecycle.worker_evidence`, `extensions.custody.erase` | Covers completed-slot gates, acknowledged release, autonomous terminal exit and settled authority erasure. A `done` publication and host reap retain different meanings. |
| `Changes that change what a run establishes` | `actors.actor.fresh`, `actors.phase.order`, `steps.assessment.fresh`, `extensions.custody.prepare` | Its concrete change examples explain the existing freshness, preparation and ordering obligations. Keep the policy augmentation link as its existing separately owned account. |

The final generated lists may omit a repeated summary entry if the next section
provides the direct route without ambiguity. Do not remove `steps.assessment.fresh`
owner's explicit limit that fresh-read sequencing is source-supported there;
its named constructed controls concern fresh writes. The companion
controlled-read review gives the separate independent correspondence path;
the associated plan is the entry point to that record.

# Worker terminal lifetime: adopted decision

Status: terminal-lifetime refactor and phase qualification rule adopted.
Production code is unchanged. This record belongs to the
[terminal-publication investigation](../../controller/tools/pw_probe_runner/TERMINAL-PUBLICATION-PLAN.md)
and its [implementation plan](../../controller/tools/pw_probe_runner/TERMINAL-EXIT-REFACTOR-PLAN.md).
The source baseline is `51487f74da15de196d44c4ac571c7b322a2fe83b`.

## Adopted design

A worker reaching an existing terminal publication will erase its accepted
token bytes, publish the same terminal evidence, and call `_exit(0)` without
waiting for host permission. Include the
host acknowledgement reconciliation needed for a worker that publishes and
exits between polling observations. Cover ordinary token cleanup in the same
implementation, while preserving the distinct meanings of each departure path.
Retain the existing validator collection behavior and apply the adopted phase
qualification rule below. Active validator cancellation is not a prerequisite
for this refactor.

This removes the intentional, unbounded post-publication wait. It does not
promise that native exit always completes, bound a native call that has not
returned, provide a total host lifecycle deadline, or clean up exec descendants.
Those limitations remain explicit inputs to the later exec investigation.

## Adopted phase qualification rule

Treat otherwise admissible query records as predictions about the live specimen
only when their phase's collection/release/acknowledgement chain is established,
including unbroken worker ownership and the existing protocol checks. Otherwise
retain them as native query observations without that qualification.

Collection closes before release; the same worker subsequently acknowledges.
Under the harness's identity and publication assumptions, that acknowledgement
establishes that the worker survived the preceding collection. No per-query
liveness check or reconstruction of the instant of exit is needed. Missing
acknowledgement does not prove any particular query reached an exited target.
It withholds the qualification for that phase. Later worker failure does not
invalidate an already established chain, and qualification does not require
successful attempts, phase completion, or successful completion of the run.

Use the existing phase evidence as this condition; do not introduce a competing
lifetime classifier. Raw outcomes and native rc/errno remain observations,
including an `allow` label produced from rc zero. An interrupted collection's
raw label alone must not be presented as a qualified live-specimen prediction.
Make that distinction explicit in the account and verify affected readers.

This rule removes two prerequisites that would otherwise enlarge the design:
determining the native API's response for every exited-target case, and
cancelling every remaining query before it can run. Cancellation could reduce
wasted work, but it would still race with execution; it is separate work if a
concrete need warrants it. The deliberate cost is withholding qualification
from potentially valid observations in a phase whose chain was not established.

## Why this is sufficient

The host owns a separate mapping and takes a final acquire snapshot after its
cleanup attempt. Worker exit does not require sacrificing already published
application, failure, phase, slot or compiled-profile evidence. The classifier
already separates terminal publication, actual polling stop, deadline and
observed process status. A cleanly reaped completed worker can be accepted when
the polling stop was `child_reaped`; it need not have been `done`.

The required host adjustment concerns phase acknowledgement. The current grace
path observes acknowledgement again after reaping, but a child reaped directly
in the polling loop bypasses that observation. Reconcile acknowledgement after
a confirmed reap using the existing `ownershipUnbroken && releaseSet && ack == 1`
predicate. This establishes historical ownership through acknowledgement, not
worker liveness after reap. Preserve protocol violations and their separate veto
on the ordering chain. A final raw acknowledgement must never repair previously
lost ownership, invent a release, or promote an unreleased phase.

These conclusions follow from
[the driver](../../runner/Sources/PWRunnerCore/CWorker.swift),
[ordering and classification](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift),
and the [evidence contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md).
An independent source review reached the same conclusion.

## Boundaries to preserve

- Keep the host exit-request flag for cancellation and cleanup. Removing the
  worker's post-`done` wait does not remove the pre-acknowledgement cancellation
  decision or require a new shared-memory layout.
- Keep actual stop/deadline facts even when a later snapshot finds `done`.
  Late evidence is retained; a missed deadline does not become timely success.
  Acknowledgement after the host's cancellation store can still be a valid
  sampled-decision race; do not add a new cancellation violation.
- Keep early refusal return codes and their absent `done` publications.
  Cancellation also must not gain a new `done` publication. A common erase
  primitive need not force every departure through one publication/exit policy;
  existing ordinary returns from main remain returns.
- Retain the borrowed shared token channel and preparation placement. Preserve
  consume-time erasure and the existing erase before hang/signal interventions.
  Erase accepted bytes before ordinary departures, without adding allocation,
  new resource acquisition or native extension release. Extension release
  remains an explicit specimen action; host erasure remains a separate fact.
- Retain host reap/termination fallback for workers that do not finish. No
  watchdog, parent-loss detector, new supervisor, or descendant-containment
  promise is part of this change.

## Observable tradeoff

A worker that refuses a phase during synchronous validator collection may now
exit while queries remain. Those queries may return different native results
than queries against the presently retained, failed worker. Preserve actual
records and close collection through the existing path. Without the phase
chain, these records remain unqualified observations under the adopted rule;
there is no need to determine which individual queries had a live target.
Withhold release/order when the required chain is absent. The existing
[death-during-collection control](../../runner/Tests/PWRunnerCoreTests/OrderingTests.swift)
already avoids assuming a particular native answer for a dead target.

This tradeoff is part of the adopted decision. It should be covered explicitly
in implementation validation, rather than describing the refactor as
observationally identical.

Readiness and cleanup observations can also change: a pre-ready terminal
failure can close the ready pipe sooner, and a promptly exiting worker can be
reaped during polling instead of grace. Preserve those actual observations
alongside the same published failure or completion evidence.

## Alternatives

| Alternative | Assessment |
| --- | --- |
| Retain the handshake and document the limitation | Avoids a lifecycle change but retains dependence on host permission after terminal publication, with no identified evidence-collection need. |
| Add a bounded wait or parent-loss watcher | Introduces another timing or liveness mechanism to a stage that can simply request native exit; it does not solve native-call stalls or arbitrary descendant survival. No separate need for such a mechanism was established. |
| Move token preparation later or copy into private storage | Changes acquisition/failure ordering or introduces another token copy and cleanup lifetime. Neither is needed to remove the terminal wait or cover ordinary erasure. |

## Evidence and implementation gate

Lifecycle and token ownership were reviewed separately, followed by independent
source review. Four bounded controls passed in the investigation experiment
`experiment-20261018T171602.901016Z`, whose equipment and raw receipts are retained
beside this record. The coordinator inspected all four receipts.

| Forced condition | Existing host | Isolated candidate host |
| --- | --- | --- |
| Acknowledgement and terminal publication between the last polling samples and reap | Completed report and clean reap retained; `child_reaped` retained; lifetime credit absent and order `unestablished` | Same publication, stop and reap facts; lifetime credit present and order `query_first` |
| Wait error breaks ownership before later acknowledgement and clean reap | `wait_error` retained; lifetime credit absent and order `unestablished` | Same conservative result; successful later reap does not restore lost ownership |

The candidate added only a final acknowledgement observation after confirmed
reap in a copied host source tree. The child was an ABI fixture that published
controlled data and exited without waiting for the exit-request flag; validator
records were constructed. These controls establish host interpretation of the
scheduled race, not native sandbox behavior, signed-app acceptance, production
token erasure, or host-loss recovery. Every child was reaped, with an independent
native wait subsequently reporting `ECHILD`; no cleanup kill or watchdog fired.
The initial sandboxed build failed on Swift module-cache access. The same command
passed after the prescribed escalated retry; both attempts' logs are retained.

Implementation acceptance needs production-source and signed-app
controls for normal completion, failures, restrictive profiles, final empty
phases, refusal during collection, late publication after deadlines, ownership
loss and ordinary token erasure. Host-loss controls need an independent cleanup
owner. Worker byte-erasure evidence must be distinct from host erasure.
Qualification controls must retain raw responses from interrupted phases without
promoting them to live-specimen predictions, and retain established qualification
when a worker fails after acknowledgement. They must not depend on a particular
native answer for an exited target.
The required `witness_contract/order_barrier_mutations` control applies because
ordering eligibility and the worker wait paths are affected.

Existing wire fields and the ordinary-reply `query_first` predicate already
supply the phase qualification condition. Preserve their meanings and reading
rules; no new field, classifier or version bump is part of the implementation.
On reporting-failure replies, retained ordering remains diagnostic and absent
comparisons must not be reconstructed into qualification. The implementation
plan specifies these producer/reader boundaries and their regression controls.
Regenerate worker identity, update lifecycle/resource documentation through its
owning inputs, and review affected producers and independent readers during
implementation. These are future acceptance requirements, not completed checks.

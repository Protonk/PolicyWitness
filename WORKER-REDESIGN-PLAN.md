# Worker findings: design investigations

## Status and purpose

The terminal-publication investigation is complete, with independent review
and coordinator synthesis. The terminal-exit refactor and phase qualification
rule below are implemented, reviewed and accepted against the signed app; the
[acceptance record](records/worker-terminal-lifetime/implementation-acceptance.md)
retains the build, tests, test-oracle repairs and source snapshots.
The descriptor, exec and sysctl investigations are complete and reviewed against
`503156f`; their daughter plans link the reports and native evidence. Execution
configuration has a reviewed source inventory. The user selected narrow host
descriptor closure and preservation/disclosure of the bounded sysctl read.
The [exec evidence refactor](controller/tools/pw_probe_runner/EXEC-EVIDENCE-REFACTOR-PLAN.md)
is specified for review; it separates observations without changing cleanup
policy. The [coordination record](records/worker-redesign-followups/coordination.md)
retains sequencing, baseline evidence and the coordinator's documentation review.
Execution environment remains staged. No follow-up application refactor has
been implemented.

The question is whether a different design would remove the reason for a
finding, and what that design would cost the instrument. A useful outcome can
be a smaller refactor, a changed experimental contract, or a reason to retain
the existing design and its limitation. Each investigation ends with evidence,
alternatives and a recommendation for a user decision. Implementation follows
that decision as separately scoped work.

## Evidence and relationship to the worker tour

The [initial audit](records/worker-pass6/initial-report.md) examined
`475ac0b7a284b784a4a65e5673f71c7f17941a5b`. Its original text is preserved;
the [handoff context](records/worker-pass6/handoff-context.md) records provenance,
evidence availability, subsequent process cleanup and provisional connections
to existing findings. Audit recommendations are inputs to investigation.

The [worker documentation plan](docs/WORKER-INST-DOC-PLAN.md) retains its register
and adjudications. These handoffs neither close its open rows nor authorize
runtime repairs. Existing findings missed by this audit remain in that register.

## Application investigations

| Finding | Code-local plan | Decision to develop | State |
| --- | --- | --- | --- |
| WA-01 | [Launch descriptor lifetime](runner/Sources/PWRunnerCore/LAUNCH-DESCRIPTOR-LIFETIME-PLAN.md) | Close host descriptor after successful worker spawn, retaining mapping and relinquishing descriptor ownership | Narrow refactor selected; implementation planning pending |
| WA-04, WA-08 | [Terminal investigation](controller/tools/pw_probe_runner/TERMINAL-PUBLICATION-PLAN.md) and [implementation plan](controller/tools/pw_probe_runner/TERMINAL-EXIT-REFACTOR-PLAN.md) | Publication followed by exit, ordinary terminal cleanup and token possession | Implemented; signed acceptance passed |
| WA-03 | [Exec investigation](controller/tools/pw_probe_runner/EXEC-SUPERVISION-PLAN.md) and [evidence refactor](controller/tools/pw_probe_runner/EXEC-EVIDENCE-REFACTOR-PLAN.md) | Separate collection, cleanup-request and reap facts; retain current cleanup policy | Evidence plan ready for review; supervisor undecided |
| WA-07 | [Execution configuration](runner/Sources/PWRunnerCore/EXECUTION-CONFIGURATION-PLAN.md) | How requested controls, resolved configuration and observed interventions should relate | Source inventory reviewed; design staged |
| WA-10 | [Execution environment](controller/src/EXECUTION-ENVIRONMENT-PLAN.md) | Whether an application-level environment account improves the experiment | Staged; not started |
| WA-11 | [Sysctl read contract](controller/tools/pw_probe_runner/SYSCTL-READ-PLAN.md) | Preserve and disclose bounded reading; optional raw length metadata remains a separate choice | Bounded operation selected; implementation planning pending |

The initial three follow-ups ran concurrently, with shared-checkout builds and
process experiments serialized. Configuration source inventory followed as an
agent slot became available. The coordinator reviewed sources, equipment,
receipts and limitations; copied-source prototypes did not alter the app.

Selected directions and remaining decision checkpoints are:

- Descriptor lifetime: close the host's evidence descriptor immediately after
  successful worker spawn, relinquish its cleanup ownership and retain the
  mapping. The user selected this narrow refactor; broader inheritance and
  low-descriptor collisions remain separate.
- Exec: implement separate observation, cleanup-request and reap evidence under
  the new plan, preserving legacy aggregate status and current behavior. Then
  decide whether ordinary leader-plus-EOF completion should end same-group
  background work. A cleanup request before leader reap needs no
  extra owner. An external group owner is feasible for cleanup after worker
  loss, but adds authority and child-visible state and cannot contain escaped
  descendants or establish group absence merely from a signal result.
- Sysctl: the user selected retaining the single non-null 4096-byte value read
  and naming/disclosing its capacity. Decide separately whether to publish
  supplied capacity and raw post-call `oldlen`. That value is neither required
  size nor bytes copied.

Settle descriptor implementation before new supervisor launch wiring. Let the
exec evidence plan supply the fact distinctions before configuration chooses
a shared representation; any supervisor-specific configuration remains staged.
Existing request, envelope and provenance can already support qualified document
observation records. Environment work follows the
requested/resolved/observed distinction and does not need to precede those
records. The exec plan is awaiting review; no supervisor or stronger cleanup
contract is selected.

The user selected terminal lifetime as the first investigation to bring to a
design decision, before detailed exec-supervisor design. That decision is now
recorded in the implementation plan. Worker terminal completion and descendant
cleanup remain separate guarantees.

The [terminal-lifetime decision record](records/worker-terminal-lifetime/decision.md)
records prompt native exit after terminal publication, paired with final
acknowledgement reconciliation and ordinary accepted-token erasure. The initial
bounded fixture controls are supplemented by signed production acceptance and
deterministic erasure/acknowledgement mutation controls. Under the adopted rule,
otherwise admissible query records qualify
as live-specimen predictions only with an established phase collection/release/
acknowledgement chain and unbroken ownership; other records remain native query
observations without that qualification. This avoids per-query liveness
reconstruction and makes active validator cancellation unnecessary for the
terminal-exit decision. Raw observations after refusal may still change.
The implementation plan's production scope is complete. The worker-documentation
register retains its own adjudications; this acceptance does not close unrelated
open findings or select a descendant-supervision design.

Terminal publication and exec supervision share lifecycle evidence, but worker
exit and descendant cleanup are different guarantees. Execution configuration
may affect how observations are described in the retained workstream. Descriptor
ownership and token cleanup may change resource lifetimes in the tour. Record
these consequences when recommending a design; they do not assign one
investigator ownership of another plan.

## Retained documentation workstream

WA-02, WA-05, WA-06 and WA-09 stay together here. Preliminary source review is
recorded in the coordination record; no schema or graph redesign is selected.
Examine:

- Support attached to particular facts, including explicit source-only support
  and relevant assertion citations, in place of mandatory per-row check filling.
- Identifiable observation records and applicability review, including the
  configuration and evidence behind observation L.
- Separation of acquisition placement from policy-specific observations in the
  current "Sandbox-gated" column.
- Resource holders, shared objects and multiple purposes in the map, together
  with correction of source ownership references.

This workstream concerns how WORKER.md and its machinery represent the
instrument. It makes no application redesign decision on behalf of a daughter
investigation. Changes to the manifest's current per-resource model are
proposals to examine, including their authoring and verification costs.

## Return and maintenance

For each investigation, record the source revision and evidence used, which
part of the finding each alternative removes, remaining limitations, changes
to the experimental question, and the smallest useful next decision. Separate
source conclusions, observed results and hypotheses. Name any needed future
regression controls and contract changes without treating them as completed.

Update this outline with report locations and actual user decisions as they
arrive. Preserve the initial audit; subsequent investigation reports and
reconciliation are separate records linked from their associated plans.

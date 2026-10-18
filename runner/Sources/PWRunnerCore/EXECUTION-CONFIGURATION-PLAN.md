# Investigate explicit execution configuration

[Parent and handoff scope](../../../WORKER-REDESIGN-PLAN.md).
Finding: WA-07 in the [initial audit](../../../records/worker-pass6/initial-report.md).
State: source investigation complete and reviewed after the exec, descriptor
and sysctl refactors. The user selected removal of the implicit app-level
validator fallback; the narrow refactor is implemented, reviewed and accepted
against the signed app.

The [source inventory](../../../records/worker-execution-configuration/source-inventory.md)
traces all ten controls, selection/provenance and readers at `503156f`, with
ordinary, effective, inert, unreached and refused examples. These are source
branches, not newly executed runs. Existing retained requests, envelopes and
provenance suffice for qualified observation records; override presence cannot
classify effective instrumentation. That inventory identified structured dynamic
validator allowances, intervention observations and the default-validator
fallback's selected-path account as separate gaps. No mode, request split or
schema is selected.

The [post-refactor review](../../../records/worker-execution-configuration/post-refactor-review.md)
and [reviewed source hashes](../../../records/worker-execution-configuration/reviewed-sources.json)
refresh these conclusions against the accepted implementations. The user
selected removal of the implicit app-level fallback, aligning the default with
the supported bundle-local helper. The
[implementation plan](VALIDATOR-DEFAULT-REFACTOR-PLAN.md) and
[acceptance record](../../../records/worker-validator-default/implementation-acceptance.md)
retain the selected scope, signed build, controls and full default battery.
Manually arranged older layouts no longer receive fallback; explicit overrides
retain precedence. Related comments now distinguish supplied controls, selected
bytes and observed execution. Dynamic validator allowances and native
intervention observations remain optional capabilities with no present
requirement to add them. No mode, request split or schema was added.

## Starting point

[PWRunnerAPI.swift](PWRunnerAPI.swift) admits `_test_overrides` that select
executables, allowances and interventions.
[CWorkerOrchestrator.swift](CWorkerOrchestrator.swift) translates them into
driver inputs; [CWorker.swift](CWorker.swift) passes applicable controls to the
worker. Supplied controls are echoed, but presence alone establishes neither
an effective change nor execution of the selected intervention. An earlier
refusal can prevent the boundary from being reached. The launch observation
called L itself uses sleep overrides.

Consider a resolved execution plan with explicit executable selection and
interventions, potentially reached through separate ordinary and instrumented
request forms. Compare this with a smaller clarification of existing fields.
Compiling controls out of shipped binaries is another alternative, with a cost
to testing the actual distributable.

## Questions that distinguish the designs

- What facts belong to the submitted request, resolved configuration and
  observed execution respectively? Include inert/default controls, early
  refusal, unavailable executables and interventions never reached.
- Which distinctions can existing `test_overrides` and binary provenance already
  express? Trace [run_flow.rs](../../../controller/src/run_flow.rs), the dossier
  and reply readers before proposing another mode flag or parallel metadata.
- Can ordinary and instrumented requests share the same production orchestration
  while making their differences explicit? Identify where separate entry points
  or build variants would cause tests to exercise a different path.
- How would the proposal affect admission, refusal sanitization, wire compatibility
  and observation applicability? Built-in versus BYOXPC selection and test
  intervention are different axes; preserve that distinction.

The [override contract](../../README.md#test-seam-_test_overrides),
[request grammar](../../../docs/REQUEST-GRAMMAR.md) and
[wire contract](../../../docs/CONTRACT.md) are the relevant boundaries.

## Outcome to bring back

Return a small model illustrated by ordinary, effective-override and
unreached-override runs. Explain which scope ambiguities it removes, what can
be derived from current evidence, and what new observations or fields would
be required. Keep application configuration separate from the parent's retained
work on document citations and observation records.

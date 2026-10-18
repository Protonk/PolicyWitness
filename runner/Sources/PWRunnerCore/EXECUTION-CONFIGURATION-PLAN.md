# Investigate explicit execution configuration

[Parent and handoff scope](../../../WORKER-REDESIGN-PLAN.md).
Finding: WA-07 in the [initial audit](../../../records/worker-pass6/initial-report.md).
State: drafted; investigation unassigned.

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

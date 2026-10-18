# Investigate the execution environment as part of an experiment

[Parent and handoff scope](../../WORKER-REDESIGN-PLAN.md).
Finding: WA-10 in the [initial audit](../../records/worker-pass6/initial-report.md).
State: drafted; investigation unassigned.

## Starting point

The [external-runner guide](../../docs/PolicyWitness.md#external-runners-byoxpc)
identifies consent mediation as a possible source of stalls for privacy-mediated
targets. The audit supplied no new TCC observation for this launch chain.
Worker credentials, signing, inherited context and the specimen policy already
affect the experiment. Determine whether an application-level environment
account would add useful information beyond existing provenance.

Start at runner selection and provenance in [runner_select.rs](runner_select.rs)
and dossier/envelope assembly in [run_flow.rs](run_flow.rs). Follow their
providers as needed. Compare explicit environment declarations, independently
observed context, and a controlled-environment profile with retaining the
existing environmental limitation.

## Questions that distinguish the designs

- Which proposed facts can the application actually observe for this launch
  chain? Separate user-declared conditions, measured context and unknown OS
  state. Avoid implying an effective-permissions census from signing metadata.
- Would the information change specimen selection or interpretation? Sketch a
  concrete run for which it helps before adding a general environment schema.
- Would a baseline probe itself prompt for consent, warm state or change the
  later operation? A separate control requires a fresh process and an account
  of those effects. Pre-opening the target changes the acquisition under test.
- What would a controlled environment reproduce, and which native-desktop or
  BYOXPC experiments would it cease to represent? Specify the smallest useful
  scope before considering provisioning or environment-reset machinery.

This investigation can conclude that the external condition should remain an
explicit limitation. A permission-shaped failure or a stalled call supplies
an observation; causal attribution requires additional evidence.

## Outcome to bring back

Recommend either a concrete environment capability with a bounded observation
method, or retention of the existing model with reasons. State the cost in
experimental disturbance, platform dependence and applicability. Identify any
proposed changes to machine consent or system settings for a separate user
decision; existing metadata review is the starting point.

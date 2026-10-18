# Investigate exec completion and supervision

[Parent and handoff scope](../../../WORKER-REDESIGN-PLAN.md).
Finding: WA-03 in the [initial audit](../../../records/worker-pass6/initial-report.md),
overlapping register row 10. State: investigation complete and reviewed;
behavioral decision ready, no supervisor design selected.

The [investigation report](../../../records/worker-exec-supervision/investigation.md)
records current-source behavior, fresh lifecycle controls and a native external
group-owner probe at `503156f`. The next decision is whether ordinary completion
should end same-group background work. A pre-reap cleanup request is the smaller
extension; cleanup after worker loss needs a surviving owner. The probe supports
the latter's limited feasibility while independently demonstrating escape and
an inconclusive signal-zero probe. Neither alternative promises descendant
containment. The report identifies a current documentation correction that is
needed regardless of the behavioral choice.

## Starting point

`attempt_exec_spawn` in [pw_probe_runner.c](pw_probe_runner.c) can finish after
leader exit and both output streams reach EOF. Its group-kill paths are
conditional. A same-group descendant can survive ordinary completion, and
worker death can leave exec processes alive. The
[lifecycle suite](../../../tests/suites/runner_exec_lifecycle/README.md)
characterizes these separately in `closed_streams_leader_exit` and
`worker_dies_during_exec`; both passed during the audit. The fixture owns later
cleanup, which is distinct from product behavior.

The design question is what completion and containment the exec operation
should offer. Compare separate leader/stream/cleanup states, cleanup on ordinary
completion, and supervision by an owner that survives worker death. A narrower
controlled-helper feature is a different capability choice worth making explicit.

## Questions that distinguish the designs

- Which surviving processes may a run legitimately leave, and which can affect
  later steps? State the promised boundary before choosing a supervisor.
- How would an external supervisor learn process identity and cleanup ownership
  without a registration gap if the worker dies? Trace group changes, escaped
  descendants, identifier reuse and loss of the supervisor itself. Group
  signalling and observed process absence are separate evidence.
- Can the worker retain the actual post-apply spawn while supervision changes?
  Moving spawn or acquiring attempt resources before apply changes the
  experiment. Identify any extra channel, authority or process introduced.
- What would the reply say when the leader is reaped but cleanup remains
  incomplete? Which proposed changes merely clarify completion, and which
  actually remove a survivor path?

Use the existing fixture's independent identity, liveness and exit observations
to distinguish these cases. A new experiment must retain an independent cleanup
owner when deliberately removing its worker or supervisor. The
[terminal publication investigation](TERMINAL-PUBLICATION-PLAN.md) concerns the
worker's own exit and cannot by itself establish descendant cleanup.

## Outcome to bring back

Recommend a completion contract and its attainable cleanup boundary, with
alternatives, evidence and capability costs. Identify the smallest experiment
that would discriminate the preferred ownership model. Keep the broader
arbitrary-process containment question explicit if it remains unresolved.

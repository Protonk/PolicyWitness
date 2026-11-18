# runner_exec_lifecycle

Public CLI contract for an exec deadline: terminate the exec process group,
retain output already written, and continue the specimen's remaining steps.
The suite uses the built app and the shared `tests/fixtures/exec` helper,
without `_test_overrides`, worker ABI access, or Swift internals.

An allow-default specimen executes the helper's controlled process tree,
then writes to a file seeded with random bytes. The observer establishes
that both helper processes are alive and share a group led by the exec
child. It obtains PIDs from kernel socket credentials and requires OS exit
events for both processes before releasing or cleaning up the fixture.

The run must finish within a generous outer bound around the public
10-second exec deadline (8–25 seconds), while the fixture itself has a
45-second backstop. JSON must retain stdout and a fresh stderr marker,
report the leader's observed SIGKILL status separately from the group request,
and keep the successful spawn observation beside the allow answer. Neither
the signal number nor a matching request establishes who sent the observed
signal; the later failure does not become sandbox-denial attribution. The next step must appear
as successful and actually change the target's bytes. The whole specimen
must succeed with complete evidence.

Run `tests/run.sh --suite runner_exec_lifecycle` outside an automation
sandbox. Missing app or toolchain fails. Artifacts include the specimen,
envelope, PID/group and exit observations, before/after file bytes, and logs.
The `exec_fixture` suite independently tests the helper and observer,
including the negative control where only the leader is killed.

CLI execution uses `tests/lib/run_capture.py`. The shared capture retains
`specimen.json`, raw `run.json`/`pw.stderr`, and command/exit/timing metadata in
`capture.json`. Its wait observes the CLI without signalling it. The test checks
OS exit events and the later file write before reading JSON or running cleanup;
the public exec-deadline assertion remains here. Direct capture controls live in
`run_capture`.

The shell entry point uses `tests/lib/case.sh` for setup and logged checks.
Case IDs, checker arguments, and artifact paths remain defined by this suite.
The `shell_helpers` controls verify failure propagation and report/log behavior.

Additional cases close both streams while the observed helper processes keep
responding, or exit the leader while its child retains the streams. The former
must finish naturally after test release; the latter must stop the remaining
group member at the deadline while preserving the leader's actual exit code.
`worker_dies_during_exec` terminates the independently identified worker while
both helper processes are live. Earlier file effects survive; unfinished exec
fields remain absent and later effects are absent. The test owns helper cleanup
and observes each original process identity and liveness before performing it.
It retains independent final helper and worker exit events in `cleanup.json`;
staging is removed only after those exits and CLI closure are confirmed. An
incomplete rendezvous or unconfirmed cleanup retains staging. This guards
missing-publication semantics without claiming that current worker death
cleans up descendants.

Each completed live exec reply carries `exec_observation`. The suite checks
collection stop/leader/EOF facts, a separate group request or no-request state,
and the leader's actual final wait/status. A deadline snapshot remains open
streams/leader-not-observed even after cleanup has reaped it; the exited-leader
case retains the observed exit with open streams. Normal completion reports no
request, including the descendant-lifetime case below. The killed worker's unpublished slot
exposes no object. File attempts also omit it. The deadline checker accepts the
live result and rejects six independently altered documents promoting cleanup,
EOF or pending waits into stronger facts; their rejection receipt is retained.
All process/effect observations precede JSON interpretation.

## Same-group descendant after normal completion

The default `closed_streams_leader_exit` case closes both helper processes'
captured streams, asks the leader to exit without waiting for its child, and
waits for the public CLI to finish. It declares its observations and judgments
in the catalog (`outcome_contract`) and ends with `complete`, not `pass`.

**Recorded without a verdict: the descendant's lifetime.** Whether the
same-group descendant is alive after ordinary completion is an informational
observation: PolicyWitness makes no commitment to it, so neither history is
expected and neither fails. Exit watches for the CLI, the leader and the
descendant are registered on one queue before any stream closes. After the
CLI's exit event the checker reads that queue. An exit event for the
descendant classifies `exited_before_cleanup`, with its observation time
relative to the CLI's. Without one, the checker pings the descendant and reads
its process identity and group: an acknowledged ping from the original
generation in the original group classifies `alive_acknowledged`. An
unacknowledged ping or a missing PID is never read as an exit: the checker
then waits a bounded time for the registered event, and a sample no event
settles leaves the observation incomplete, which fails the case. A changed
identity or group, or a watch registered after completion was triggered, also
fails it. Each exit stamp is when the event was observed; it carries no status
for a process that is not the checker's child, so an exit alone does not
identify its cause. `classifier-controls.json` retains constructed samples for
both histories and for each refusal, run through the same classifier before
any launch.

**Enforced: the reply's account of the product's own calls.** Two enforced
judgments are evaluated after the process and effect observations and before
cleanup. `truthful_exec_account` requires a valid `finished` envelope, the
independently identified worker reaped after a clean exit, an exec attempt
that stopped at `leader_exit_and_eof` with both streams at EOF, cleanup
`not_requested` and the leader's zero exit status, and a completed later step.
`later_step_effect` requires the later step's target to hold the byte that
step writes. These facts do not establish that the process group is empty.
The worker requests group termination only after a deadline, an observation
error or a local fault, and controller admission, the host's evidence reader
and the test consumer accept `leader_exit_and_eof` only with `not_requested`.
While that relation stands, a product that ended the descendant at ordinary
completion and reported the request would be refused at controller admission;
this case's `exited_before_cleanup` history covers a descendant that exits
without such a request.

**Required in either history: evidence and cleanup.** The fixture then
releases the helpers and requires kernel exit events for both, whether the
descendant was alive or had already exited. When it was alive, the same
sampler and classifier must report its exit after the release. The test
watches the independently identified worker as well, and removes staging only
after helper/worker exits and CLI cleanup are confirmed. An incomplete
rendezvous or unknown cleanup retains staging and a `cleanup.json` account and
fails the case; cleanup failures do not replace the original exception. A
checker failure, an unsettled cleanup or an unfavorable enforced judgment ends
the case as `fail`. `account.json` holds the published facts and judgments;
`observations.json`, raw capture artifacts and before/after bytes keep the
lifetime sample distinct from the later release.

Pair it with `closed_streams_continue` and `leader_exit_descendant`: those
neighboring cases exercise stream closure and leader exit separately.

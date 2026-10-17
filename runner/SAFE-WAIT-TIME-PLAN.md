# Investigate safe worker wait timing

## Problem and intended result

Determine how the sandboxed C worker can bound its wait for host release without
depending on a clock path that the specimen can deny, and without weakening the
ordering or failure evidence. This is an investigation: establish a defensible
approach and the tests a repair will need before committing to an implementation.

In the retained preliminary battery `20261016T021725Z_87b7a565`, case
`witness_contract/bug_report_returns_verdicts`, the worker reported
`proceed wait: CLOCK_MONOTONIC failed` with errno 1. Its deny capture includes
`syscall-unix 116`, `gettimeofday`, for that worker under
`(deny default)(allow file-read-data)`. The
[run directory](../tests/out/runs/provenance-acceptance-default-20261016/) is
gitignored, local evidence protected by `tests/RETAINED.json`. The worker failed
closed; no prediction or attempt was fabricated. Other successful batteries
do not explain away the observed failure.

The unconditional commpage claim above `wait_for_proceed` in
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c) is too
strong. The API name alone does not establish the path taken by the installed
library, including initialization and fallback paths. A replacement also has
to preserve the race-sensitive relationship among time, release, cancellation
and acknowledgement. Selecting a promising clock API is only part of the work.

This investigation is independent of
[the completed build provenance repairs](../records/BUILD-PROVENANCE-ACCEPTANCE.md#review-corrections). It covers
the proceed wait first. Inventory other uses of `PW_MONOTONIC_READ`, including
exec timing, to understand shared dependencies before changing that seam; do
not silently broaden a proceed-wait experiment into a general timing rewrite.

## Questions to resolve through observation

Read [AGENTS.md](AGENTS.md), [the runner reference](README.md),
[test guidance](../tests/AGENTS.md) and the current ordering tests. Start from
the retained worker result and raw deny event, checking process identity and
timing. Keep a library-path explanation distinct from what that event alone
establishes.

1. **Which paths can the current clock take on supported systems?** Inspect
   the applicable platform implementation and use a small native reproduction
   under the same policy. Observe first use and repeated reads, recording OS,
   architecture, toolchain, native failures and available deny evidence. Failure
   to reproduce an intermittent event leaves its cause open. Instrumentation
   must not warm up or replace the path whose first-use behavior is in question.
2. **Can a suitable clock be read after application with the required bounds?**
   Compare a small number of plausible native paths, including their
   initialization and conversion requirements. Establish monotonicity, units,
   overflow handling and whether sleep counts toward the deadline. Examine
   any proposal for pre-application setup for hidden resources or authority;
   prewarming one successful read does not prove subsequent reads stay safe.
   A candidate must be usable without adding permissions to the specimen.
3. **What ordering can be preserved when clock and control events compete?**
   Trace `wait_for_proceed`, the host's release/cancellation paths and the shared
   acquire/release operations. Work through release near expiry, clock failure
   with release already visible, cancellation, delayed scheduling and successive
   phases. Decide from the evidence where expiry is determined and which event
   wins; do not move a load or acknowledgement merely to make a clock test pass.

Investigate the clock path and the ordering model independently at first. Their
results meet at a small prototype only when a candidate has a plausible safety
argument. The prototype should expose the disputed boundary, not introduce a
new general timing abstraction. If no candidate has adequate support, report
why and what observation is missing; do not select one on API naming or repeated
successful runs alone. A proposal to move deadline authority to the host needs
its own account of host delay, worker lifetime and release races.

## Evidence to seek

Use the existing
[clock-failure fixture](../tests/fixtures/worker_lifecycle/clock_failure.c) and
[OrderingTests.swift](Tests/PWRunnerCoreTests/OrderingTests.swift) for deterministic
boundary observations. Extend only the seams needed to schedule a disputed
interleaving. Keep those constructed failures separate from live evidence that
a clock path survives the applied policy. Retain the original failure alongside
successful controls, raw command output and process-cleanup observations.

For a promising prototype, seek a live deny-default run, an ordinary successful
neighbour, and deterministic cases for failed/unusable time, deadline expiry,
release at the boundary and cancellation. Verify acknowledgement and action
start independently: collection must close before release, the worker must
observe the appropriate release before attempting that phase, and failure must
not manufacture `query_first` or discard already-established native evidence.
An unusable clock currently fails closed even when release is visible; any
proposed change to that behavior must be explicit and justified.

Any prototype changing the worker wait, release store or query eligibility must
run `witness_contract/order_barrier_mutations`, as the repository guidance
requires. Use a matching signed build for integrated runner checks, including
`runner_unit` and `runner_c_worker_harness`; retain the affected live witness
cases. A later production repair will also need the applicable failure-boundary
and full-battery checks. Do not treat compilation or a timing stress loop as
proof that the ordering contract survived.

## Investigation outcome

Write the findings to `records/SAFE-WAIT-TIME-INVESTIGATION.md`, distinguishing
observations, platform-source support, inferred causes and remaining unknowns.
Record reproducible commands, equipment and retained run IDs. Recommend an
approach only as far as its clock-path and race evidence supports it, with the
small set of acceptance cases that would distinguish it from an unsafe repair.
If evidence is insufficient, name the unresolved question, the next resolving
observation and the implementation decision it blocks.

Before turning the prototype into production work, update this plan with the
chosen behavior and the resulting implementation, contract and test scope.
That scope must account for worker identity, any C/Swift shared-layout change
and the ordering mutation gate. Correct the unconditional source comment with
an evidence-supported description. Put lasting timing and ordering guarantees
in the runner reference and owning contracts, and update generated architecture
inputs if process or channel boundaries change. The investigation report holds
the experiment history; it must not become the sole explanation of shipped
behavior.

## Related parking-lot item: P4 (context only)

[P4 — Give unfinished cleanup an explicit owner](../records/EVIDENCE-CLARITY-PARKING-LOT.md#p4--give-unfinished-cleanup-an-explicit-owner)
is related to this investigation. A safe worker clock can bound the proceed
wait, while the host's final reap can still block; a bounded wait does not
establish a total response-time bound. This distinction is especially relevant
when considering moving deadline authority to the host, where cancellation,
worker lifetime and cleanup ownership meet.

This is a suggested connection for the investigating agent. Investigating or
closing P4 is outside this plan's scope, and P4 adds no acceptance gate here.

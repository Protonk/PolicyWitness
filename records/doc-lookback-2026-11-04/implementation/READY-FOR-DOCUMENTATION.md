# Ready to resume documentation, with F1 deferred

The user authorized exhausting two final instrumented runs and deferring the
remaining investigation if the issue recurred. Both executions completed and
failed. F1 in `READER-OUTFLOW-PLAN.md` now owns the deferred work; documentation
can proceed without another fixture investigation or test retry in this tranche.
This is an accepted deferral, not a claim that the failing case is repaired.

## Final bounded observations

Root ran the focused command outside the automation sandbox twice, with
`PYTHONOPTIMIZE` unset and separate output directories:

```sh
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-repairs-06 tests/run.sh --case runner_unit/host_setup_oracle_sensitivity
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-repairs-07 tests/run.sh --case runner_unit/host_setup_oracle_sensitivity
```

Run 06: `20261105T031925Z_7088dee4`, 31,698 ms, one case completed/failed.
Run 07: `20261105T032015Z_f0ccd56a`, 29,590 ms, one case completed/failed.
Neither case overlapped recorded sleep. All twelve prepared/diagnostic source
files stayed unchanged. All 46 copied inputs match instrumented runs 05–07.

| Missing receipt | Ready wait | Sentinel wait | Exit grace | Termination and reap |
| --- | --- | --- | --- | --- |
| Run 06, wrong ready direction | EOF, 0 ms | deadline, 200 ms | exhausted, 201 ms | SIGKILL request rc 0; reaped with signal 9 |
| Run 06, partial unmap | deadline, 100 ms | deadline, 200 ms | exhausted, 202 ms | SIGKILL request rc 0; reaped with signal 9 |
| Run 07, wrong shared-memory argument | deadline, 101 ms | deadline, 200 ms | exhausted, 200 ms | SIGKILL request rc 0; reaped with signal 9 |

Each failure was the variant's first `worker-baseline` scenario. Its observer
receipt was absent; the scenario log was empty. All three retained no wait
errors or clock fault, collection after confirmed reap, closed descriptors,
zero remaining mappings and successful fixture-name cleanup. The other variants
completed their original recipe/checker and independent observation assertions.

The diagnostic addition now distinguishes these executions from a normal
observer exit: the host exhausted its waits, requested termination and reaped
a signal-9 exit. It does not reveal whether the child reached main, where it
was delayed, or why it had not created its receipt. Earlier uninstrumented
failures still lack that telemetry; the observed sequence is not retroactively
assigned to them. No startup mechanism or operating-system cause is claimed.

## Deferred ownership and evidence

F1 is explicitly separate from I1–I3. The three original repairs have passing
direct checks from run 01; ordinary setup plus all sensitivity variants also
have a complete instrumented pass in run 05. These passes do not convert the
original coordinated selection or runs 06/07 to passing historical results.
The user-authorized deferral permits the documentation tranche to proceed with
that qualification.

The original managed runs remain intact. Transcripts were attached under the
checkout lock after terminal run/owner identity checks. The small observation
copies under `implementation/setup-flake-evidence/` preserve terminal run
accounting, failed host/independent receipts, build receipts, input inventories,
variant results and console output. Their manifest retains original paths,
run IDs and hashes; these are observation copies, not relocated ownership or
live process/resource-cleanup authority. `implementation/final-observation.json`
records the source comparison and terminal results. Existing source snapshots
and the diagnostic patch retain reconstruction inputs.

## Next work

No further fixture runs or repairs are pending in this tranche. No documentation
owner has been launched yet. Fifteen specialists have participated and all are
finished. Next, dispatch two fresh documentation owners under the agreed plan:

1. ARCHITECTURE/WORKER and `architecture.json`: public-form corrections, actor
   sequence/resource crosswalk, accurate timing/capture/authority qualifications,
   and justified consolidation. Preserve useful IDs and checking routes.
2. LIMITS/`limits.json` and shared explanations: form/counting/budget scope,
   capture/fallback/receiver bounds and diagnostic-path bounds, with independent
   implementation-value checks and honest coverage. Coordinate shared guide
   regeneration with the first owner; do not edit generated copies directly.

Root owns cross-document review and adjacent controller/qualification README
updates, generator coordination, mechanical validation, and rendered figure/table
fidelity. Return after documentation and validation, before the six fresh final
readers, or sooner for a consequential unresolved question. F1 must remain an
explicit deferred test-reliability item in the final acceptance account.

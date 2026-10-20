# Execution preparation and ordering: verification

Evidence for the sleep record, fixture warm-up check and validator start gate
committed in `98c2781`, `f237590` and `ac359d9`. The plan as executed is
`EXECUTION-PREPARATION-AND-ORDERING-PLAN.md` in `ac359d9`'s tree. Each commit
message records its phase's checks and controls in full. Test runs are under
`tests/out/runs/` and are gitignored; they are available only in the local
checkout. Only `gate-p3-checkpoint` is pinned in `tests/RETAINED.json`, so
ordinary pruning can remove the others.

## Signed build

`make build` with the Developer ID identity, from a clean checkout of
`ac359d9`, produced `dist/PolicyWitness.app`: build 778, `v0.3.1-94-gac359d9`,
`dirty: false`. Its provenance records worker identity
`bf9b04aefccf51568969e6914149c389d6c271da5033f65f39dc73cddaa3372e`, the same
as the build of `390f771` that the phase checks ran against, so no identity
input changed.

## Phase checks

Each ran against the build of `390f771`, on the phase's working tree
immediately before its commit. Every case recorded 0 ms of system sleep.

| Phase | Run | Result |
| --- | --- | --- |
| 1 | `sleep-p1-drift` | `source_drift`: 7 of 7. |
| 1 | `sleep-p1-dispatcher` | `dispatcher`: 6 of 6, including the constructed sleep readings and the idle-sleep helper's lifetime controls. |
| 1 | `sleep-p1-runner-unit` | `runner_unit` with its opt-in mutation controls: 8 of 8; 465 of 465 Swift tests, no sleep lines. |
| 1 | `sleep-p1-pmset` | `dispatcher/controls`: 1 of 1, while `pmset -g assertions` listed the helper's `PreventUserIdleSystemSleep` on behalf of the dispatcher. |
| 2 | `warm-p2-callers` | Default `runner_unit` cases and the three fixture-building `witness_contract` cases: 8 of 8. |
| 2 | `warm-p2-order-mutations` | `witness_contract/order_barrier_mutations`: 1 of 1. |
| 3 | `gate-p3-checkpoint` | The over-budget case at 150 ms. Both ungated runs lost the record. Gated, it was kept with a cold copy (185 ms to the receipt), a warm fixture (1 ms) and a 1,000 ms delay (1,002 ms). The first attempt discriminated, with no void run. |
| 3 | `gate-p3-integrated` | The Phase-2 selections plus the `runner_unit` opt-ins: 12 of 12; 467 of 467 Swift tests. |

All fixture build logs list the nineteen outputs with their expected
statuses. Phase 2's three builder controls ran once in a disposable worktree
and are recorded in `f237590`'s message. `python3
docs/generate_worker_identity.py --check` passed with the identity above.

## Final checks

| Selection | Run | Result |
| --- | --- | --- |
| Default battery | `ordering-final-default-20261019` | 196 of 196, none skipped or unrun, no harness errors, app unchanged. 467 of 467 Swift tests; the never-executed validator copy took 116 ms to its receipt. Four fixture build logs, each with nineteen expected statuses. |
| Full `source_drift` and `dispatcher` | `ordering-final-drift-dispatcher-rerun-20261019` | 13 of 13 (7 and 6), none skipped or unrun, no harness errors. Neither suite uses the app, so the run made no artifact inspection. |

The default battery ran against the new build. In both runs the idle-sleep
helper launched and was still running at the end, and every case recorded 0 ms
of system sleep. Both tested the tree of `280e2f3`, which is `ac359d9` with
`MARKDOWN-GUIDANCE-PLAN.md` deleted. The default battery ran before that
deletion was committed, with the same working tree. The first
`source_drift` and `dispatcher` run, `ordering-final-drift-dispatcher-20261019`,
was stopped during its first case and has no terminal record. It is not
credited, and the rerun replaces it.

No builder failure, gate equipment failure or behavioral failure occurred in
a credited run.

## Not established

No run overlapped a system sleep. The per-case sleep record has been exercised
only with constructed readings, and its comparison with the `Sleep` line of
`pmset -g log` waits for the first real sleep during a run. Production
allowances still count sleep.

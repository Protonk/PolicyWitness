# Candidate review: recovery entry point

Claude, 2026-10-30. Worktree `/private/tmp/pw-candidate-repair-20261030`, branch
`review/pytest-candidate-repair`, starting from `ecd3795d` (tip of
`review/pytest-coherence`, unchanged at `/private/tmp/pw-coherence-20261030`).
The associated plan is `records/CANDIDATE-REPAIR-PLAN.md`.

## Where things are

- Findings, repair commits and run table: [findings.md](findings.md).
- Run identities, sources, pins and hashes: [evidence-index.json](evidence-index.json).
- Ownership records in this worktree and in nested fixtures of its runs:
  [recovery-index.json](recovery-index.json), produced by the read-only
  [holds.py](holds.py). It never recovers, signals or removes anything.

Raw output is gitignored and local to this worktree's `tests/out/`. Every run named
in the evidence index is pinned in this worktree's `tests/RETAINED.json`.

## Ownership and disposal

This worktree's actual registry is `tests/out/pytest-owners/`: 16 records from
`repair-verify-01`'s family, all closed (`recovery-index.json`). A future refusal
here names its run ID; inspect with `tests/run.sh --recover-ownership RUN_ID`
and use `--apply` only when the receipts justify it. Closure still requires a
matching settlement with revoked launch authority (or an affirmative never-launched
receipt), not a state label, direct return, available lock, elapsed time or absent
endpoint.

Each `dispatcher/pytest_controls` run deliberately creates unresolved nested
fixture records (the inherited ambiguous-state and crash-window controls). They
are scoped to their fixture roots and protected by their enclosing pins (eight
each in `repair-controls-01` and `repair-controls-02`). The
unrepaired run `repair-prefix-01` additionally holds records from the old owner's
failure paths (13 unresolved in all: the same eight plus spawn failure, context
refusal, unstarted owner, lost readiness and the integrated launch failure); four
of them left socket directories under `/private/tmp/pwpx-*`, which remain where
the old owner left them. Those failures are affirmatively never-launched: four
`owner.stderr` files end in the refusal, spawn error or `BrokenPipeError`. For the
unstarted owner (empty `owner.stderr`), the evidence is the control's patched spawn
refusal. The old records still carry no settlement, and this review does not
create one after the fact. Keep them with the pin.

One scratch reproduction outside any checkout,
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/ebb544f7-bba4-4de5-a7bf-0eb202dc1033/scratchpad/repro/work/launch-failure/`,
left the same unsettled shape and `/private/tmp/pwpx-4bf411e2ab914fd9b4d14d8e03ee37a4`.
It is session scratch; its owner exited with `FileNotFoundError` before any child
existed.

## Inherited protection

Unchanged and not touched: the coherence worktree's registry (16 closed actual
commands) and the eight unresolved nested records in its pinned `coherence-01`; the
frozen adoption worktree at `/private/tmp/pw-pytest-exec-candidate-20261030` with
its 25 indexed runs and, per its index and the coherence traces (not recounted
here), 176 closed actual records and 95 unresolved nested fixture records; the earlier prototype and unknown-worker resources under that worktree's
`records/pytest-maintenance/resource-recovery.md`; and the accepted checkout and
app. This review signalled no process and recovered, unpinned or pruned nothing
it did not create.

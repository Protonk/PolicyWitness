# Retained evidence and resources outside the main checkout

Claude, 2026-10-30, after integrating the pytest exec-family adoption
(reviewed candidate `f80815fa`, merged as `b3536d1a`). This is the current
recovery entry point for evidence and resources that live outside
`/Users/raccoon/Desktop/Security/PolicyWitness`. The retired plan packages
it replaces remain recoverable at the git objects named below.

## Integration account

The scoped one-family adoption was accepted after the candidate review repaired
four defects: unrecoverable holds from failures before launch, uncredited but
unreported group intervention, a misattributed shared baseline cause, and an
uncollected family crashing the dispatcher when packages appeared late. The
review's account is `f80815fa:records/candidate-repair/findings.md`.
On `main` at `b3536d1a`, the pinned default battery `integration-default-01`
(run `20261030T231522Z_2f76036f`) passed 202/202 against the accepted app with
no harness error and an unchanged app.

Reviewed exceptions:
- `dispatcher/pytest_controls` is credited from `repair-h2-controls-01` at
  `da469993`. The integrated tree's executable files are identical to it; only
  records and a root Markdown file differed, and `pytest_controls` reads neither.
- `preflight/build_refusal_controls` and the other Developer ID rebuild cases
  were not rerun. The admission functions they exercise (`guard`, `inspect`,
  `disposition`, `settled`, `validate`, `recover`, `close_record`) are byte-identical
  to the adoption's tested source. That establishes file identity, not that no
  build path reaches the changed `Command.__init__` or `suite_run` code.
- `witness_contract/order_barrier_mutations`: no worker wait, release store or
  eligibility change.

## Why these stay where they are

Retained runs are bound to their absolute location: `retention.valid_owner`
requires `owner.json`'s `out_dir` to equal the run path, and every nested
ownership record names its absolute fixture root, which
`pytest_resources.validate` checks. No repository procedure relocates a
retained run while keeping either identity, so each worktree below is kept
whole. Closed actual registries carry no obligation. Their receipts also
survive in each run's `ownership.json`.

**Volatility.** Nothing in `/private/tmp` on this machine predated the
2026-10-06 boot when inspected on 2026-10-30, consistent with `/private/tmp`
being cleared at restart. Everything below in `/private/tmp` — six worktrees,
38 socket directories, the prototype lease, the unknown-worker directory and
the F2 controlled-preparation staging — is therefore not durable. The user
decided on 2026-10-30 that the worktrees may be kept but are no longer needed:
they are not archived or relocated, and their loss at restart is accepted.
Keeping them grants no closure; a recorded unresolved item that disappears is
lost, not settled.

## Worktrees kept

| Worktree | Branch / HEAD | Retained content | Detailed index |
| --- | --- | --- | --- |
| `/private/tmp/pw-pytest-exec-candidate-20261030` | `adoption/pytest-exec-family` `809ef178` (in `main`) | 20 pinned runs (pins also in `main`'s index); 95 deliberately unresolved nested fixture records; 176 closed actual records | `809ef178:records/pytest-exec-adoption/recovery-index.json` and `recovery.md` |
| `/private/tmp/pw-pytest-exec-comparison-20261030` | `comparison/pytest-exec-family` `d03cc67f` (**not in `main`**) | 2 pinned runs, pinned only in this branch's index | `809ef178:records/pytest-exec-adoption/evidence-index.json` |
| `/private/tmp/pw-pytest-exec-build-check-20261030` | `verification/pytest-exec-build` `4ff5eee0` (**not in `main`**) | 3 pinned runs (build refusals, 202-case default battery, mutation continuations), pinned only in this branch's index | same |
| `/private/tmp/pw-pytest-boundary-20261030` | `investigation/pytest-boundary` `9e46c7b9` (in `main`) | 12 pinned runs, including `pytest-boundary-demo-01` with the prototype's acquired lease, its `owned` file and socket directory `/private/tmp/pw-py-res-6e703d57e50848888c7d8b19e46202f9` | `5dbcf4d8:records/pytest-maintenance/resource-recovery.md` |
| `/private/tmp/pw-coherence-20261030` | `review/pytest-coherence` `ecd3795d` (in `main`) | pinned `coherence-01` with 8 deliberately unresolved nested records; 16 closed actual records | `ecd3795d:records/coherence/recovery-index.json` |
| `/private/tmp/pw-candidate-repair-20261030` | `review/pytest-candidate-repair` `f80815fa` (in `main`) | 7 pinned runs with 45 deliberately unresolved nested records; 16 closed actual records | `f80815fa:records/candidate-repair/recovery-index.json` (first five runs, 29 records); the two H2 runs hold 8 each |
| `/Users/raccoon/Desktop/Security/PolicyWitness-pytest-trial-evidence` | detached `6304fef5` (in `main`) | 3 unpinned runs cited by path in `records/archive/tests/PW-PYTEST-BASELINE-3ec96c1.md`; its prune tool would delete them, so do not prune there | that archived record |

[Ownership records](retained-resources/records.json) is a current read-only
inventory of these worktrees: every unresolved nested record with its run,
fixture root, state and socket directory, plus each actual registry's size
(208 actual records, all closed). The prototype lease predates that record
format and is described by its own index above.

Keep the two branches not in `main`; their pins and wrappers exist only there.
Every unresolved nested record is a fixture-scoped control, not an actual
command obligation. Recovery for them is read-only inspection from the
fixture root. Historical PIDs, elapsed time, absent endpoints, free locks and
external exit observations do not settle them.

## Resources outside worktrees

- [Socket directories](retained-resources/sockets.json): 37 `/private/tmp/pwpx-*`
  and the prototype's `/private/tmp/pw-py-res-6e703d57e50848888c7d8b19e46202f9`. Each is
  named by exactly one unresolved record listed there. One of them,
  `/private/tmp/pwpx-4bf411e2ab914fd9b4d14d8e03ee37a4`, belongs to a scratch
  reproduction whose record lives in a Claude session scratchpad. Its owner
  exited with `FileNotFoundError` from `Popen` before any command existed;
  the record still has no settlement, and none is created after the fact.
- `/private/tmp/pw-extension-directory-uge3532e`: the BYOXPC extension
  experiment's unknown-worker directory. Its own `ownership.json` identifies the
  `no_predicate-baseline` request with unknown worker spawn/exit; public runner
  list/reconcile were empty on 2026-10-30. Preserve until a worker exit witness exists.
- `/private/tmp/pw-f2-controlled-prep`: F2 controlled fixture preparation;
  accepted equipment is committed under `tests/`. Not a worktree; untouched.

## Removed on 2026-10-30

- `/private/tmp/pw-pytest-adoption-plan-20261030` (`plan/pytest-exec-family`
  `8fd2c825`) and `/private/tmp/pw-pytest-maintenance-20261030`
  (`investigation/pytest-maintenance` `5dbcf4d8`): no runs, registries or
  ignored content; both branch refs deleted, tips are ancestors of `main`.
- `/private/tmp/pw-f2-stage1` (detached `2de5b1c7`, ancestor of `main`): no runs
  or registry. Its Stage-1 app (build 999) was the subject of `main`'s pinned
  `f2-stage1-observe-01` and `f2-stage1-original-01`. Their
  `artifact-integrity/before.json` and `after.json` both equalled the app's full
  inventory immediately before removal (45 entries, digest of the sorted
  inventory JSON `1c52a5e70bdfedf594fe5c0946fa43666b84c9001b391d00b13a783eb421c933`).
  The app bytes are gone; its identity remains in those runs.

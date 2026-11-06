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
On `main` at `b3536d1a`, the then-pinned default battery `integration-default-01`
(run `20261030T231522Z_2f76036f`) passed 202/202 against the accepted app with
no harness error and an unchanged app. Its full main-checkout run is now retired.

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

## Sandbox-extension actor integration (2026-11-03)

The explicit file authority path and the public actor form were accepted on
the `extension-actors` branch and squashed into one commit on `main`. The plan
(`SANDBOX-EXTENSION-WITNESSING-PLAN.md`) and its records
(`records/sandbox-extension-issuance/`: the implementation journal and the
test and documentation scouting reports) were retired with that integration;
they remain recoverable at `4ebb1afc:SANDBOX-EXTENSION-WITNESSING-PLAN.md`
and `4ebb1afc:records/sandbox-extension-issuance/IMPLEMENTATION-JOURNAL.md`.

Acceptance ran on the candidate built at `a6695516` (build 1117, clean tree)
in the worktree `/Users/raccoon/Desktop/Security/PolicyWitness-extension-actors`
(branch `extension-actors`), whose `tests/out/runs/` holds the pinned runs
`stage4-captures-01`, `stage4-acceptance-01` (default battery 213/213) and
`stage4-acceptance-optin-01` (`order_barrier_mutations`, `actors_byoxpc`,
`extensions_byoxpc`, `reservation_controls`), beside unpinned stage
verification runs. Pins are relative to that worktree's `tests/out`; keep it
whole. The main checkout's `tests/out` does not contain these runs.

Resources outside worktrees created by this work:

- `~/Library/Containers/com.policywitness.test.restricted-worker` and
  `~/Library/Containers/com.policywitness.test.restricted-worker.1ef4fe8633cb88c7`:
  App Sandbox containers created by the inherited-restriction control's
  bundled worker copy (the second from the first run, before the control used
  one fixed identifier). They hold nothing of value. The harness cannot remove
  them (`EPERM` without Full Disk Access); delete them from Finder or a
  terminal with Full Disk Access when convenient. The control reports a
  retained container in its pass message each time it runs.
- A crash report `~/Library/Logs/DiagnosticReports/pw-probe-runner-2026-11-03-185426.ips`
  from the first restricted-worker launch (bare executable, no bundle
  identifier); it is the retained diagnosis for the bundle requirement and
  can be deleted.

## Main-checkout retention (2026-11-04)

At the user's direction, superseded main-checkout test runs are retired and
`tests/RETAINED.json` is reduced from 89 entries to two current verification
runs and the existing release-managed acceptance entry. The previous index is
recoverable at `a54da012:tests/RETAINED.json`. Release archives and the foreign
worktrees below are untouched; their own indexes remain authoritative for their
local output. Removing their duplicate main-checkout pins does not settle any
resource obligation.

The current runs are `extension-consolidation-battery-01` and
`extension-consolidation-build-refusals-04`. These are gitignored,
checkout-local materials at their original owned paths. Their exact source
snapshot, verification account and retention receipts remain recoverable from commit `bc3abe2f` under
`records/extension-consolidation-2026-11-05/`. The two superseded actor-passes
runs have identified, hashed historical copies under
`records/doc-lookback-2026-11-04/critique/historical-evidence/`; their original
identities and cleanup qualifications remain preserved. Archive copies do not
relocate active ownership.

Before retiring `workset-r2-byoxpc-02`, seven unchanged recovery files
(20,628 bytes) were copied to
`records/retained-resources/extension-directory-uge3532e/`. Its `manifest.json`
records original paths, hashes, run identity and the prior retention entry.
These are historical recovery observations, not relocated active ownership.

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
| `/private/tmp/pw-pytest-exec-candidate-20261030` | `adoption/pytest-exec-family` `809ef178` (in `main`) | 20 pinned runs in that worktree's index; 95 deliberately unresolved nested fixture records; 176 closed actual records | `809ef178:records/pytest-exec-adoption/recovery-index.json` and `recovery.md` |
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

- `/Users/raccoon/Library/Containers/com.policywitness.test.equipment-5baed78c80dc4eeeb2b95b9f10113600`:
  the consolidation prototype's uniquely created App Sandbox container. Its removal was refused with `Operation not permitted`; no settled
  cleanup is claimed. The original ownership receipt remains
  `/private/tmp/pw-equipment-prototype-20261105-02/container-ownership.json`
  (SHA-256 `7ea19b33c701990fd39040a795e95a002f942ebe9c7a1493a89139b91ebc06ab`).
  The historical recovery account is recoverable at
  `bc3abe2f:records/extension-consolidation-2026-11-05/recovery.json`.
  Retiring the plan records does not transfer this ownership or establish
  removal; retain the original receipt until absence is verified. The separate
  `com.policywitness.test.restricted-worker` container was preexisting and was
  not newly owned by this work.
- [Socket directories](retained-resources/sockets.json): 37 `/private/tmp/pwpx-*`
  and the prototype's `/private/tmp/pw-py-res-6e703d57e50848888c7d8b19e46202f9`. Each is
  named by exactly one unresolved record listed there. One of them,
  `/private/tmp/pwpx-4bf411e2ab914fd9b4d14d8e03ee37a4`, belongs to a scratch
  reproduction whose record lives in a Claude session scratchpad. Its owner
  exited with `FileNotFoundError` from `Popen` before any command existed;
  the record still has no settlement, and none is created after the fact.
- `/private/tmp/pw-extension-directory-uge3532e`: the BYOXPC extension
  experiment's unknown-worker directory. On 2026-11-04 the directory still
  existed but its in-place `ownership.json` was absent. The unchanged historical
  records preserved above identify the `no_predicate-baseline` request with
  unknown worker spawn/exit; public runner list/reconcile were empty on
  2026-10-30. Preserve the directory until a worker exit witness exists. The
  evidence copy and retirement of the old run establish no such witness.
- `/private/tmp/pw-f2-controlled-prep`: F2 controlled fixture preparation;
  accepted equipment is committed under `tests/`. Not a worktree; untouched.

## Removed on 2026-10-30

- `/private/tmp/pw-pytest-adoption-plan-20261030` (`plan/pytest-exec-family`
  `8fd2c825`) and `/private/tmp/pw-pytest-maintenance-20261030`
  (`investigation/pytest-maintenance` `5dbcf4d8`): no runs, registries or
  ignored content; both branch refs deleted, tips are ancestors of `main`.
- `/private/tmp/pw-f2-stage1` (detached `2de5b1c7`, ancestor of `main`): no runs
  or registry. Its Stage-1 app (build 999) was the subject of `main`'s then-pinned
  `f2-stage1-observe-01` and `f2-stage1-original-01`. Their
  `artifact-integrity/before.json` and `after.json` both equalled the app's full
  inventory immediately before removal (45 entries, digest of the sorted
  inventory JSON `1c52a5e70bdfedf594fe5c0946fa43666b84c9001b391d00b13a783eb421c933`).
  The app bytes and those full runs are gone; the inventory digest above remains
  as a historical identity statement.

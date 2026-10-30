# Findings, repairs and verification

Claude, 2026-10-30. Selection is in [selection.md](selection.md); it was committed
(`d5229a58`) before any repair. Raw output is gitignored and local to
`/private/tmp/pw-candidate-repair-20261030/tests/out/runs/`.

## Sequence

| Commit | Content |
| --- | --- |
| `d5229a58` | Plan and selection. |
| `881ad3b1` | Eight receipt controls (`tests/suites/dispatcher/pytest_receipts.py`), stimuli and independent expectations only. |
| `e624b7f9` | Repairs (owner, supervisor, engine, shared baseline), documentation, pin of the unrepaired run. |
| `33104cd1` | Control correction: survivor stimulus ledger read from raw native stdout; per-control exceptions recorded. |
| `7e48461f` | README sentence restated without the duration literal refused by G9; pins. |
| `c8c6b56c` | Review records and recovery index (no executable change). |
| `1713bb06` | H2 availability-transition controls, committed before the correction. |
| `da469993` | H2 correction in `suite_run.py`, documentation, pin of the uncorrected run. |

| Run (`tests/out/runs/`) | Run ID | Source | Result |
| --- | --- | --- | --- |
| `repair-prefix-01` | `20261030T223754Z_4478add4` | `881ad3b1` (unrepaired) | All 44 existing observations pass; all eight new controls fail for their stated reasons. Pinned. |
| `repair-controls-01` | `20261030T224215Z_8d571b63` | `e624b7f9` | Six new controls pass; my integrated-survivor control read a ledger the repaired engine no longer publishes, and its `ValueError` skipped `baseline_cause`. Equipment defect in the new control, not the repair. Pinned. |
| `repair-controls-02` | `20261030T224502Z_f6603edf` | `33104cd1` | `dispatcher/pytest_controls` passes: 52 observations, eight new controls, no failures. Pinned. |
| `repair-verify-01` | `20261030T224720Z_91f1fd36` | `33104cd1` | 19/20 pass: the family against the unchanged accepted app, five dispatcher controls, six preflight build-entry/provenance/release cases, seven drift cases. `generator_contract` refused my README literal (G9). Pinned. |
| `repair-drift-01` | `20261030T225319Z_8314e456` | `7e48461f` | `--suite source_drift`: 8/8 pass. Pinned. |
| `repair-h2-prefix-01` | `20261030T230715Z_92147082` | `1713bb06` (uncorrected) | Receipt controls pass; `provisioned_after_collection` fails with no terminal run record; the reverse transition passes. Pinned. |
| `repair-h2-controls-01` | `20261030T230950Z_7ebb880d` | `da469993` | `dispatcher/pytest_controls` passes: 54 observations, ten review controls. Pinned. |

Reconciliation: `repair-verify-01` and `repair-controls-02` executed `33104cd1`.
Executable changes after them are `pytest_availability.py`/`check_pytest.py`
(covered by `repair-h2-controls-01`) and `suite_run.py` (`da469993`, the dispatcher
of every case). `tests/README.md`, `tests/suites/dispatcher/README.md`, records and
`RETAINED.json` pin entries are documentation or data. Because the dispatcher
changed after the broad branch runs, those runs do not cover the final tree.
Integration verification on `main` reruns the default battery and the owning
control case at the integrated revision.

`generator_contract`: it failed in `repair-verify-01` (G9: the duration literal
"one second" in the new README sentence). `7e48461f` restated the sentence;
`repair-drift-01` passed the whole drift suite. The H2 README addition contains no
literal value, and the integrated battery reruns the drift suite.

## H1 — failure before launch left an unrecoverable checkout hold (repaired)

Mechanism: `pytest_command_owner.main` binds its recovery endpoint, then has no
handling until the start receipt. A spawn error, its own deliberate refusals
(no durable release authorization; changed execution context) or a closed
readiness gate raised out of `main`. No settlement was written, and the socket
file stayed on disk, so `recover` always took the live-peer branch and failed
with `Connection refused`; the offline branch was unreachable. Every later build
and test in the checkout was refused, and no supported tool could clear it. The
supervisor's own failure to start an owner left `owner_launch_authorized` with no
owner, also permanently unresolved.

Unrepaired observation (`repair-prefix-01`): spawn failure, context refusal, unstarted
owner and lost readiness all leave unsettled records (`command_release_authorized`,
`owner_launch_authorized`, `owner_bound`). In the integrated mixed fixture
(`launch-integrated`), the family reported `invalid session finish; incomplete
execution accounting; … command ownership unresolved` — the `FileNotFoundError`
appeared only in `owner.stderr` — and the legacy `sentinel/later` was `unrun` with
`pytest ownership checkout hold`.

Repair (`e624b7f9`): `main` wraps the unchanged body (`own`). If an exception occurs
while no command process exists, the owner removes its endpoint and publishes
`settle_unlaunched` (never-launched, `launch_error`), then exits normally. The
supervisor does the same when `Popen` of the owner raises. A failure after the
command exists is re-raised unchanged (still ambiguous by design). This follows
the adoption plan's recovery table: once the owner or controller can no longer
release, the release invariant establishes that no native command started.
The engine fails the item with `native command was not launched: <error>`.

Repaired observation (`repair-controls-02`): each case settles never-launched and
closes, the endpoint is gone, `inspect` shows no hold, recovery is idempotent.
Lost readiness leaves an output-only hold until public recovery closes it, because
the supervisor had already given up. The integrated family fails with
`SHARED BASELINE: native command was not launched: FileNotFoundError …`, one
command receipt, eight setup-blocked bodies, and the legacy sentinel passes.

Discrimination: independent of receipts, the missing path cannot exec; the refused
and unreleased commands' `touch` markers are absent. A repair that merely labelled
the record closed would fail the endpoint, recovery-idempotence and
integrated-diagnostic checks.

## H2 — mixed pytest/legacy integration (availability disagreement repaired)

See selection H2 for the paths inspected. A family-internal launch failure became
a hold blocking later legacy work (H1). The integrated control now requires the
legacy sentinel to run after that failure.

Second defect, first noted unrepaired and repaired in the closeout: `test_cli.main`
decides pytest availability when it collects the plan, before the checkout lock;
`suite_run.requirements` decides it again for the `pytest` prerequisite. Only one
direction disagreed. When packages appear in between, the second check passed for
a family with no collected engine. `execute` then raised `KeyError` on
`collectors[...]`: no `run.json`, an unfinished run, and every later case lost.
The reverse (collected, then removed) was already blocked as `not_started/unavailable`.

Contract applied: README "that same collected engine waits until ordinary
admission allows it to proceed"; the release reader requires the executed
selection to equal the plan's collected items. A family without a collected
engine therefore lacks its engine equipment for this run, whatever the packages
look like later. Correction (`da469993`): `requirements` reports `pytest` missing
for an engine case whose plan has no `items`. The blocked reason appends the
plan's recorded `engine_unavailable` error, already durable in `plan.json`. No new
availability policy. Non-family reasons, including the exact rosetta reason
`check_selection` asserts, are unchanged.

Controls (`1713bb06`, `pytest_availability.py`) rename a verified target, the
final step provisioning performs, at a fixed point between plan collection and
the lock. Unrepaired (`repair-h2-prefix-01`): the provisioned direction left
`owner.json`, `plan.json` and `dispatch.json` with no `run.json` and a
`KeyError` traceback; the sentinel never ran. Repaired (`repair-h2-controls-01`):
both directions end terminal with the family `unrun`, `not_started/unavailable`,
completion 1 completed / 1 unrun, a `not_run` diagnostic, the sentinel passing,
no registry and a free checkout. The reason reads `missing prerequisites:
['pytest']; no pytest engine was collected with this plan: expected regular
evidence file: …/installed.json`. A later run in the same fixture executes the
family with the provisioned packages.

## H3 — shared baseline cause misattributed (repaired)

Mechanism: `Observation.baseline` cached only `AssertionError`, `OSError` and
`ValueError`. `canonical_ledger` raises `KeyError` on a `close` of a descriptor that
no `pipe` created. The next dependent setup re-entered `build_run('production')`,
failed in `mkdir` with `FileExistsError`, and cached that as the shared cause.

Stimulus: `(void)close(-1);` inserted at the exec assembly boundary of the nested
fixture's production `pw_worker_exec.h`. It compiles, passes every native assertion
(rc 0) and changes the call policy in a way the golden exists to catch.

Unrepaired: `SHARED BASELINE: [Errno 17] File exists: …/artifacts/production`.
Repaired: `SHARED BASELINE: KeyError: -1`, exactly two production commands, eight
setup-blocked bodies, `baseline.json` naming the `KeyError`. The parser's terse
`-1` message is inherited and unchanged.

## H4 — unreported owner kill of group survivors was credited (repaired)

Mechanism: after the leader's ordinary exit, the owner waits one second, then
`SIGKILL`s any remaining group members. It published `returncode 0, timed_out
false, cancelled false, group_absent true` — the same receipt as a clean
completion — and the engine credited it. The inherited production supervisor
(`checkout_lock.Scope.supervise`, `run_standard_command`) never signals on
ordinary completion. The adoption plan requires settlement to identify group
observations and does not credit a control that PW had to stop (`3e93082f`).

Unrepaired observation: a same-group child, identified by its own socket peer
and kernel exit event, exited 1.0 s after the leader with a clean receipt. In the
integrated fixture the leader `exec`s the real native binary (ledger identical to
the golden) while a forked child sleeps; all nine items passed and the run
exited 0.

Repair: the settlement records `group_signalled_after_leader_exit`. The engine
refuses it like a timeout. The one-second timing is unchanged. The repaired
integrated run shows `SHARED BASELINE: PW signalled process-group members that
remained …`, two production commands and the legacy sentinel passing. The raw
native stdout still canonicalizes to the golden, so only the intervention
explains the refusal.

## Verification and applicability

The real family in `repair-verify-01` passes 9/9 with complete accounting, the
58-attempt ledger equal to the golden, 16 closed commands and no receipt carrying
`never_launched`, `timed_out` or `group_signalled_after_leader_exit`. In this run
its clang and native commands left no group survivors, so the new refusal did not
change the ordinary result. The accepted app was valid and unchanged. The test
module, `check_exec_evidence.py`, `exec_control.c`, the golden and the native sources
are unchanged from `ecd3795d`; in `exec_domain.py` only the baseline `except` clause
changed, and its mutation statements, expected assertions and owners are untouched.

Selection followed `tests/CHANGE-VERIFICATION.md` (exec family engine boundary) and
`tests/AGENTS.md`. `pytest_resources.py` is the shared admission module and a
build-entry input, so the dispatcher, build-entry/provenance, release and drift
cases were run. `guard`, `inspect`, `disposition`, `settled`, `validate`, `recover`
and `close_record` are unchanged. The additions are a new function and the
exception path of `Command.__init__`, which admission never calls.

Not rerun (reviewed exception): the opt-in `preflight/build_refusal_controls` and
the other identity/rebuild cases. They exercise build-script refusals through the
unchanged admission functions above and need a Developer ID rebuild. Not rerun:
`witness_contract/order_barrier_mutations` (no barrier change).
Applicability of `33104cd1` results to the tip is recorded in
[evidence-index.json](evidence-index.json): only one README line and pin entries
differ, and drift was rerun. The record drafts were written into `records/` while
`repair-verify-01` ran; `records/` is pruned from every repository-tree scope the
drift checks use (`docs/repository_tree.py`), so they could not affect it.

Direct observation versus reliance: every result above was produced in this
worktree in this review. The coherence and adoption runs, the 229-credit inherited
acceptance, the 202-case battery and 16 build mutations, and the F2 native
evidence are relied on only as described in their own indexes; none was repeated.

## Limits of the sample

Four hypotheses, chosen for consequential claims about recovery authority,
crediting a native receipt, the shared-cause display and legacy continuation.
This is not a whole-tree audit, a fresh default battery or a build-mutation run.
The inherited production path examined was the supervision contract of
`checkout_lock.Scope.supervise` and `run_standard_command`, used as H4's reference.
Worker identity sources, golden provenance, the order-barrier control, include
closure and citation re-pointing were checked briefly and eliminated
(selection.md). No inherited native witness was re-executed.

Not changed, by design: recovery still refuses records whose owner may have
started a command (crash after launch, before settlement). The one-second grace
is still the owner's timing; an alternative that waits for survivors up to the
command deadline was not adopted. Portable/release readers still rely on item
outcomes rather than re-deriving crediting from receipts, as they already did for
timeouts.

## Judgment

No consequential choice remains for the user. Each repair enforces a commitment
already stated in the adoption plan or the existing controls: the never-launched
closure form, settlement identifying group observations, no credit for commands
PW had to stop, and one cached shared baseline. The candidate at the final commit
of this branch is recommended for acceptance as the one-family adoption, subject
to the user's merge decision and the reviewed exceptions above.

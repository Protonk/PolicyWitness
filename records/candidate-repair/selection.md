# Selection, hypotheses and eliminated checks

Claude, 2026-10-30. Formed from the candidate source (`tests/lib/pytest_*.py`,
`execution_contract.py`, `suite_run.py`, `test_cli.py`, `checkout_lock.py`,
`retention.py`, release readers, the family module/domain and dispatcher controls)
before reading the coherence traces; the traces were then used to drop questions
already covered (execution-to-acceptance reader roles, the after-return crash
window, F2, Swift exec-observation consumers, F1 guard).

Working back from consequential claims: *recovery may close an obligation*, *a
native receipt may be credited*, *the shared baseline names the cause of eight
blocked bodies*, and *a later legacy case may proceed after the family*.

## H1 — owner failure before any command process exists

Claim at stake: closure requires settlement; an affirmative never-launched receipt
is an accepted closure form (adoption plan recovery table, rows 1–2). The owner
(`pytest_command_owner.main`) has no handling between readiness and the start
receipt: a spawn error (`FileNotFoundError`, `EAGAIN`), its own deliberate refusals
(missing durable release authorization, changed execution context), or a closed
readiness gate raise out of `main` after the recovery endpoint was bound.

Scratch reproduction (`/does-not-exist/native-tool`): owner traceback
`FileNotFoundError`, record left `command_release_authorized` with no settlement,
`/private/tmp/pwpx-*/recover` left on disk, `inspect` → `blocking: checkout`,
`recover(apply=True)` → `[Errno 61] Connection refused`. The offline path is never
reached while the dead endpoint file exists, so no supported tool can clear the
hold; builds share the guard. The supervisor reports "command ownership unresolved"
instead of the launch error. Immediate sibling: the supervisor's own `Popen` of
the owner raising leaves `owner_launch_authorized` with no owner and no receipt.

Existing controls never construct a real `Command` whose launch fails; the
ambiguous fixtures are hand-written records that never invoke a launcher.

## H2 — mixed pytest/legacy consequence and accounting

Claim at stake: a family failure is reported by the family; independent legacy
work continues unless a real possible-live obligation exists. Examined
`suite_run.execute` grouping (standard cases never merge with the family),
skipped `reconcile` for the family (no `report.json` under the family directory,
so a duplicate legacy execution would still surface as an unexpected report),
interrupt flow (Ctrl-C reaches only the dispatcher; every path ends in `fail` or
`unrun`), dependencies (none involve F), SDK guard (applied at dispatcher start,
inherited by both routes) and per-invocation `guard` placement. No independent
defect found. Through H1, a family-internal launch failure becomes a checkout hold
that blocks the next selected legacy case and every later run. The integrated
control pairs F with the existing legacy sentinel to observe that consequence.

Noted, not repaired: `test_cli.main` decides pytest availability before taking the
lock, and `suite_run.requirements` re-decides it later; if provisioning completes
between the two, `collectors[...]` raises an uncaught `KeyError` and the run ends
without `run.json` (visible as unfinished output, never as success).

## H3 — shared baseline cause

Claim at stake: a failed production baseline is one cached observation whose cause
the summary names before eight setup-blocked bodies (`87b66cb8`; README "A failed
baseline leaves eight dependent bodies unattempted"). `Observation.baseline` caches
only `AssertionError`, `OSError`, `ValueError`. `canonical_ledger` raises `KeyError`
for a `close` of a descriptor no `pipe` created. Scratch check: inserting
`(void)close(-1);` at the exec assembly boundary compiles, passes all native
assertions (rc 0) and makes the parser raise `KeyError: -1`. The next dependent
setup re-enters `build_run('production')`, whose `mkdir` raises `FileExistsError`;
that is cached and displayed as `SHARED BASELINE: [Errno 17] File exists`.

## H4 — inherited supervision contract vs. the owner's ordinary-completion kill

Inherited production path: `checkout_lock.Scope.supervise` (build/test front end)
and `suite_run.run_standard_command` never signal a group on ordinary completion;
survivors keep the inherited lock and stay visible. The adoption plan requires
settlement to "identify the exact command, wait/exit and group observations" and
that a control PW had to stop is not credited (`3e93082f`). The owner instead waits
1 s after the leader's own exit, `SIGKILL`s remaining group members and publishes
`returncode 0, timed_out false, cancelled false, group_absent true`. Scratch
reproduction: a same-group child that would sleep 30 s was gone 1.15 s after a
leader exit, with that clean receipt; the engine would credit it.

## Eliminated without repair

- Worker identity sources: `docs/generate_worker_identity.py` walks whole source
  directories, so extracted `pw_worker_exec.h`/`pw_worker_timing.h` are covered.
- Golden provenance: `exec_control.c` still matches the golden's recorded hash;
  production sources differ as intended.
- Order-barrier mutation control (`witness_contract/order_barrier_mutations`):
  count-checked anchors and required positive early-effect observations; it cannot
  pass vacuously. Not rerun (no barrier change; needs signing identity).
- Include closure: `exec_control.c` reaches the copied closure only through
  quoted includes resolved beside the variant's copies.
- Architecture citations were re-pointed one-for-one from the legacy block to
  `test_production`; any over-breadth is inherited, not introduced.

# Sources and applicability for the one-family adoption plan

Codex, 2026-10-30. These are planning observations, not implementation results.
No adoption code, new environment, native execution or feasibility rerun was
performed. The associated plan owns the proposed design and acceptance work.

## Current state and preserved evidence

The accepted checkout is `/Users/raccoon/Desktop/Security/PolicyWitness`, branch
`main`, at `77eb987554eef10ffa3371ffb21b235097562a78`. Its existing untracked
review prompt, `records/WORKSET-REVIEW-PLAN.md` and `records/workset-review/`
were left in place. The frozen boundary worktree remains at `9e46c7b9`; the
maintenance worktree remains at `5dbcf4d8`. The new plan branch derives from the
latter so both investigations are available without moving their worktrees.

The maintenance preservation checker was run in verify-only mode from
`/private/tmp/pw-pytest-maintenance-20261030`:

```
/private/tmp/pw-pytest-boundary-venv/bin/python -B -I records/pytest-maintenance/snapshot.py --verify
```

It verified twelve material retained runs, the fifty-entry frozen retention
index, original source records, accepted app paths/modes/hashes and protected
path identities. The unresolved early resource remains preserved, with cleanup
not established. The current plan does not reinterpret its recovery description,
the unknown-worker directory, or any earlier resource claim. Verification of
those identities is not a new lifecycle observation.

Starting evidence, all at fixed historical sources:

| Evidence | Reuse in this plan; limit |
| --- | --- |
| `9e46c7b9:records/pytest-boundary/assessment.md` | Credible serial engine/supervisor boundary and explicit limitations. Not proof of production integration. |
| `5dbcf4d8:records/pytest-maintenance/comparison.md` and `decision.md` | Source-owner map, actual local reporting benefits, omitted metadata/artifact/retention obligations and no established whole-harness replacement case. The user's new priority makes a bounded reporting adoption a different decision. |
| `pytest-boundary-demo-06`, source `832e7717` | Eighteen outside groups/eleven accounting inputs: phase preservation, selection barrier, setup/body/teardown failures, interruption/death, lock/capture/environment. Exact old implementation/configuration only. |
| `pytest-boundary-demo-01` at `fa376979`, correction `4211d48b` | Datagram-reset failure bypassed cleanup; keep engine-reaping/finalization invariant and evidence. Old unresolved lease is not an adoption resource. |
| `pytest-boundary-journal-red-01` at `0d3af494`, correction `832e7717` | Malformed tail must preserve previously decoded completed evidence while failing the run. Transfer this rejection control to the integrated reader. |
| `pytest-boundary-replay-old-01` / `-stale-01`, adapter `0085bd54` | Native source `f8f3c24f` gave seven passing items; source `341f9441` gave a passing production baseline and six named formation failures. The outside stale observer passed because it expected those failures. |
| `pytest-boundary-replay-adapted-01`, adapter `fec0e181` | Nine passing items with the same 58 golden attempts, six native assertion rejections and two specific missing-header refusals. Real source-binding work remained. Compiler-tree death and production admission were not exercised by this replay. |
| `pytest-boundary-reference-02`, run ID `20261030T145251Z_0059d39d`, source `e9375310` | Existing dispatcher selection/accounting/cancellation/retention controls passed; retain their stimuli and independent observers at changed boundaries. Earlier sandbox-refused `reference-01` remains failed/pinned. |

Except the reference's generated run ID, names above are also run IDs. Raw
evidence is gitignored under
`/private/tmp/pw-pytest-boundary-20261030/tests/out/runs/`. Full commit/pin/hash
identities are retained in the frozen inventory and maintenance preservation
manifest. C0.2 remains the unchanged historical blob
`0c22d256:records/workset/pytest-first.md`.

## Family selection and observation boundary

`tests/catalog.json` declares `exec_control_states` inside
`runner_c_worker_harness`. Effective inherited requirements are `app`, `clang`,
`worker`; default=true, context=standard, skip_reasons=[], depends_on=[]. No
other suite includes this ID and no current case depends on it. These were
checked from the catalog, not inferred from the standalone compiler command.

`tests/suites/runner_c_worker_harness/run.sh:821` is its current shell wrapper.
`check_exec_evidence.py:main` owns the sequential baseline, missing-header and
mutation checks. `build_run` snapshots the include closure, overwrites the actual
exec owner after copying, records compiler/native output and enforces exact
missing-owner errors. `canonical_ledger` normalizes descriptor identities only,
then retains meaningful call order/arguments/results in canonical digests.
The current script stops before dependent controls when the baseline fails.
The earlier pytest replay did not implement that dependency; the adoption plan
therefore supplies it through a shared baseline fixture/result, not supervisor
item scheduling.

`tests/fixtures/worker_lifecycle/exec_control.c` has SHA-256
`adc11fd2f3e1daf2638c752221b8da97a6a102aaab8fbcc1c42401a93ebb6da5`.
The golden has 58 attempts. Its regeneration metadata points to the existing
`check_exec_evidence.canonical_ledger`, so retaining that helper's import identity
avoids changing a historical expectation record just to move test organization.
The new test module can sit alongside it. The C source's macros intercept
spawn/wait/kill and other native calls before including the worker; controlled
spawn assigns PID 12345. Its README explicitly says the calls create no real
children. Nonetheless clang/linker/control executables are real processes and
need owned lifetimes. Separate live suites continue to establish real process,
stream and sandbox effects.

Complete sequences matter: the native main contains multiple attempts after
shared timing-state transitions and rejected samples. Splitting ledger rows
would change the experiment. Choosing nine full-program/compiler variants is
the bounded unit, with named setup/call/teardown around each variant.

The wider `runner_c_worker_harness` suite mixes shared-memory worker lifecycle,
real sandbox/file observations, timing controls and standalone native controls.
Migrating that entire suite would introduce additional observation/resource
relationships. The selected subfamily is therefore more coherent for this leg
than either the whole suite or a collection of unrelated assertions.

## Actual integration consumers

| Current owner | Finding relevant to implementation |
| --- | --- |
| `test_cli.py:catalog/select/main` | Merges group metadata, requires a command, validates bash entry scripts, applies exact case/suite union and dependencies, prints read-only list, then publishes owner/plan under checkout lock. Engine schema and collection admission require a deliberate branch; a new module cannot simply be put in the old command field. |
| `suite_run.py:execute/reconcile/account/finish` | Runs selected case groups, checks equipment/dependencies, inspects app before/after, records sleep, validates shell events/reports and exact selected accounting. `finish` currently computes success using legacy report counts plus errors. Typed family results must enter success directly, not silently disappear from those counts. |
| `checkout_lock.py:Scope.popen/supervise/group_finished/owned` | Shared descriptor/admission owner and process-group primitives. Supervising ordinary child exit is not itself the new real-command recovery adapter. Orphaned new records need a shared admission guard; core old lock behavior and independent controls remain. |
| `retention.py:disposition/replacement_allowed/prune_rows/prune` | A structurally complete unsuccessful run can be disposable. No knowledge of candidate resource records. Protecting live/unresolved ownership needs explicit new-namespace integration, not the prototype's copied terminal JSON fields. |
| `release_accept.py:battery_problems` | Requires completed passing default selection, no skipped/unrun cases, correct unchanged app and passing case results. Must reject an absent/incomplete declared family summary as well as parent failure. |
| `release_archive.py:battery_record`; `release_runs.py:pack/verify_bundle` | Archive acceptance reads parent counts/completion/default mode/integrity; packer already inventories and copies whole acceptance tree. Validate embedded family references/terminal ownership receipts without rewriting the portable archive design. |
| `release_cleanup.py:cleanup_blocker`; `release_rotate.py` | Current release guards recognize actual suite/case external-runner receipts, not arbitrary recursive resource files. Add the precise new ownership reference; do not mistake nested failure-control fixtures for live claims. |
| `tests/lib/python_start.sh`, `python.sh`; `source_drift/direct_python.py` | Pin direct Homebrew 3.14, reject ambient Python environment, enforce `-B -S`, no site/.pth discovery and interpreter identity. Test-only explicit package target keeps these entry semantics; runtime import/capture checks are still required for this new setup. |
| `source_drift/check.py`, `check_planner.py`, `docs/repository_tree.py` | Catalog/script registration and documented commands have independent negative controls and declared fixture input copies. Update relevant declarations without disabling their guards. |
| `docs/architecture.json` and generator outputs | Six citations name `exec_control_states` in the shell source. The proposed removal needs owner-path/symbol updates in generator inputs and regenerated current accounts, preserving the cited claims. |

The plan's new public selection is deliberately **not** a per-variant CLI. F
continues as one family selector, comparable to existing Rust/Swift batches;
pytest alone owns its item list. This permits reporting/organization adoption
without maintaining equivalent item catalogs on both sides. The implementation
must still reconcile the committed manifest against every observed item.

## Verification and stop boundaries

The plan names exact current canonical test IDs rather than speculative new
commands. It reserves new independent control inputs for changed integration:
baseline gating, mixed engine/legacy results, package startup, real compiler
ownership and retention/release consumers. These are unverified proposed work,
not benefits or guarantees borrowed from the frozen synthetic resource owner.

No new production defect was established. Existing app admission is retained
even though this native subfamily does not execute the app. Any later proposal
to remove that admission, change the golden or alter a product observation is
a separate behavioral decision for the user. A credible bounded plan may still
be rejected at implementation's resource/diagnostic gate; it does not authorize
indefinite expansion to obtain a favorable result.

Planning creates no managed test output or disposable runs. Nothing new needed
pinning/pruning. The associated state file records source identities and unchanged
worktree status at inspection. No permanent document points into these records.
Retire this package with its associated plan after its review/implementation use.

Planning verification checked both associated-plan links, resolved the cited
historical commits, verified all 17 named canonical control IDs in the current
catalog and compared the 94 inspected source-file hashes to the accepted checkout.
The inherited `tests/RETAINED.json` difference from accepted source belongs to
the prior investigations and is byte-identical to the maintenance worktree's
index. This leg adds only its plan and record package. The preservation checker
above passed without executing pytest, native controls or the application.

## Review refinements after the initial plan

The user supported the family, ownership split, intact native sequences, nine
variants and whole-family selection. Their four requested refinements are now
part of the existing integration/acceptance stages, with no additional general
feasibility exercise or implementation in this revision:

- The ownership state machine now distinguishes permission to launch from an
  observed launch and from settlement/closure. The proposed public recovery mode
  remains available during admission refusal. Its evidence/disposition table
  covers both pre-launch and post-completion crash windows, current-identity
  requirements, checkout-wide execution blocks, output-only holds and narrow
  recovery/disposal capabilities. Ordinary record deletion is not recovery.
- Expected family and closure evidence comes from outer invocation and verified
  harness-source/selection provenance, not optional family fields in a result.
  New controls remove the declaration/reference itself, and remove terminal
  ownership evidence while repairing mutable archive checksums. Historical
  interpretation needs affirmative legacy provenance; missing provenance is
  unverified, not evidence that the legacy contract applies.
- A new parent family account exposes execution and accounting states even
  when the existing completion counter uses `unrun`. Positive starts, refusal
  before eligibility and indeterminate starts have different ordinary displays.
- Acceptance must trace actual emitted reports through phase, submitted
  mutation, expected/observed rejection and native evidence. Shared-baseline
  blockage, session-finalizer scope, input-integrity uncertainty and cleanup
  failure after otherwise complete observations receive explicit reader checks.

The relevant inspected existing primitives are `checkout_lock.acquire/owned`
(including owner-metadata replacement when taking a new hold), the kernel peer/
exit and start-identity observations in `tests/fixtures/exec/control.py`, and
`release_runs.pack/verify_bundle`'s archive/inventory hash checks. Those hashes
establish byte consistency; required evidence roles need the separately checked
invocation/source contract. No newly discovered production defect is claimed:
these refinements close gaps in the proposed integration before implementation.
The original planning-state record stays intact; source and preservation checks
are repeated only to verify that this review changed planning material alone.

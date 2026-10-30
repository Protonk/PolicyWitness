# Workset checkpoint

Current state: independent authorized implementation and documentation work is
complete, but Swift Stage 2, the combined refactor seal and whole-workset
completion remain unaccepted. Required BYOXPC verification failed twice (F2).
F1 remains unresolved at the user's explicit request. The bounded F2
investigation is complete. The user accepted reservation, authorized continuation
and allowed schema changes. The concrete mandatory-protocol repair design is
prepared in f2-reservation-design.md; production implementation and verification
are next. No build or dispatcher is running. Neither finding is a waiver.

## Current source and evidence

- Swift Stage 2 implementation: `fd90eee66538cc02dc5d21b7a3fe8eca81a17403`.
  Signed v0.3.3 build 1000, worker identity
  `f477a8488d3f96715e987f7014dcd0aa76ba53b70575118e20ef238b600d4094`.
  Independent review found no implementation defect; exact extracted bodies,
  host/client membership and control reach are recorded in swift-refactor.md.
- Citation corrections: refactor `81f5d260`, D2 follow-up `590c5e42`.
  These do not change production, test sources, generated constants/identity,
  contract/limits/build manifests or app bytes. The latter is the current
  verified documentation source; subsequent F2 commits add investigative
  fixtures and their documentation, without changing production sources.
- `workset-r2-final-01`, `20261029T231443Z_9c34b030`: all 201 defaults plus
  six applicable opt-ins completed, 205 pass / 2 fail. No sleep, skips, unrun
  cases or app changes. Two suite-exit errors correspond to the two failures.
- `workset-r2-byoxpc-02`, `20261029T232845Z_044d37dc`: unchanged diagnostic
  rerun also failed, at a different subcase. No passing BYOXPC credit.
- `workset-r2-docs-01`, `20261029T233058Z_6ae6b3f4`: all eight source_drift
  cases plus preflight/build_entry_controls pass after corrections. The
  original qualified-name citation failure remains preserved. Reviewed reuse
  of 197 unaffected passes plus these nine results establishes 206 distinct
  passing selected cases; it does not make a 207-case passing run.

## Findings and next decision

F1: the documented host-source rejection of extension issue/consume/release
calls is absent from the API set; controls derive that family from the same
set. The recommendation remains missing names plus independent controls. The
user chose to keep this unresolved for later discussion. Do not change the
guarantee or implement the repair. Evidence is in D2's absorbed finding and
original D1 history.

F2: the original two BYOXPC 4097 failures remain unattributed. The new ungated,
instrumented public trace establishes a lost refusal: the prior owner's exit
overtook a request whose admission claim had failed. Separate controls produced
4097 with no execution and with a completed effect. Generic retry is unsafe.
The agreed repair is an effect-free reservation before submission, with bounded
retry only before execution is sent and no replay after submission. The concrete
design requires runner protocol 2 and envelope 9, preserves request 5/response
24, and removes legacy execution fallback while retaining old-installation
cleanup. Implementation and acceptance are next. Observations and limits are in f2-investigation.md;
original failures and cleanup remain in byoxpc-failure.md. Required BYOXPC
verification remains unmet, so do not seal or retire the Swift plan.

Once these decisions are made, complete the affected investigation/authorized
repair and matching verification, reconcile current evidence, seal the refactor
stage if justified, and retire the remaining accepted plans/packages. No pytest
counterfactual evaluation or trial belongs in this workset.

## Resources and retention

The original and new investigative BYOXPC services have verified removal.
Default registry/reconcile are
empty, including pending cleanup and inspection errors. The second directory
fixture remains at `/private/tmp/pw-extension-directory-uge3532e`; its
ownership.json and the pinned rerun's directory cleanup/ownership records
identify the one unwitnessed worker execution. Preserve it until that worker's
absence/exit is established; service removal is not a worker-exit receipt.

All credited native, E2, R1, R2, D2 and retirement runs remain pinned in
tests/RETAINED.json, as do all six F2 investigation runs, both failed R2 runs
and three historical D1 cost
inputs. Their source IDs and purposes are reconciled there. The dirty historical
D1 run keeps null source and its attached source.json/working.diff; never
relabel it as a clean commit. Existing release pins are unchanged. Earlier
unneeded raw output was pruned through supported tools; D2's worktree was
removed after integration. The unrelated pytest-evidence worktree remains
untouched. No cleanup may bypass the checkout lock or retention helpers.

## Recoverable milestones

- Intake `bf7e97f`; execution companion `4b18284`.
- C0 initial account `0c22d2565b42f543bd6334a1d09f95781ef09386`, seal `cf0136b`;
  records/workset/pytest-first.md remains frozen and unevaluated.
- E1 native candidate `b6cac0d`, acceptance `d2f3bbf`, crossed `8aa7402`.
  E2 implementation `7426fc0`, harvest `3ff8bf2`, captures `a7c1408`, adaptation
  `b565c1b`; experimental seal `29d1c79`, records/workset/e2-seal.md.
- D1 original chain `def5de0` through `cd6adaa`, primary `7562d24`; absorption
  into records/checks-before-check, retirement `950c604f`. Three historical
  cost pins and original predictions/replays remain recoverable.
- D2 chain `7e9d677` through `f996212`, merge `bb92c21`, primary `96dffd56`;
  final bounded citation correction `590c5e42`. F1 prevents final disposition.
- R1 design `6e40887`, candidate `341f9441`, acceptance `96d0328e` with
  build 994 and 204/204. Final candidate also passes its native/ABI/mutation
  controls. Its accepted plan retires after record commit `6dab4430`; workset-owned c-refactor.md stays
  with this ongoing package.
- R2 design `f8f3c24f`; Stage 1 candidate `72165300` failed compilation,
  corrected `9af4d3d1`, accepted `2de5b1c7` with build 998 and 87/87.
  Stage 2 and its failed verification are identified above.

C plan retirement `aa3069f3` passed both source/structure and generator/prose-link
checks in pinned `workset-r1-retirement-01`, run `20261029T233533Z_3cf679ab`.
All retained paths and run IDs were reconciled; no credited result or owned
cleanup record was released. The C plan is recoverable at `6dab4430` under
records/distribution/C-RUNNER-MODULARIZATION-PLAN.md.

F2 investigation: fixed harness `edf2c561` ran 48 ordinary requests each on
current build 1000 and Stage 1 build 999, all ok with 47 acquisitions each. The
original BYOXPC workload also passed once on Stage 1. These do not reproduce or
resolve the original failures. Controlled equipment `aa45aa48` failed to compile;
fixture correction `7d3b57a5` completed all four arrangements and reproduced
the lost-refusal mechanism. Its source/registry and generator checks both pass.
All six runs are pinned, preserving the compile failure. Baseline worktree/app
remain at /private/tmp/pw-f2-stage1; its build log and comparison are attached
to the baseline observation run. Controlled fixture preparation remains under
/private/tmp/pw-f2-controlled-prep; accepted equipment is committed in tests/.
Production sources and the inspected app are unchanged. See f2-investigation.md
for exact identities, evidence and proposal. f2-reservation-design.md fixes the
protocol, lifecycle, reader and acceptance boundaries. Next: coordinated repair,
generators and controls, then a normal signed build and required verification.

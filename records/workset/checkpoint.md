# Workset checkpoint

Current state: independent authorized implementation and documentation work is
complete, but Swift Stage 2, the combined refactor seal and whole-workset
completion remain unaccepted. Required BYOXPC verification failed twice (F2).
F1 remains unresolved at the user's explicit request. No build, dispatcher or
agent assignment is running. Do not treat either finding as an accepted waiver.

## Current source and evidence

- Swift Stage 2 implementation: `fd90eee66538cc02dc5d21b7a3fe8eca81a17403`.
  Signed v0.3.3 build 1000, worker identity
  `f477a8488d3f96715e987f7014dcd0aa76ba53b70575118e20ef238b600d4094`.
  Independent review found no implementation defect; exact extracted bodies,
  host/client membership and control reach are recorded in swift-refactor.md.
- Citation corrections: refactor `81f5d260`, D2 follow-up `590c5e42`.
  These do not change production, test sources, generated constants/identity,
  contract/limits/build manifests or app bytes. The latter is the current
  verified documentation source; later commits record results/retirement only.
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

F2: BYOXPC produces intermittent NSCocoaErrorDomain 4097 without a host/worker
receipt. The first failing consume-only subcase passed on rerun; the second
failure used allow-default without extensions. Cause is unassigned. The
unchanged service-retirement/acquisition interval suggests a hypothesis only.
The exact observations, affected case, source and cleanup are in
byoxpc-failure.md. Do not repair by changing retry/expectation policy or call
this an automation-sandbox failure. Further lifecycle investigation and any
behavioral repair belong in the user's defect discussion. Required BYOXPC
verification remains unmet, so do not seal or retire the Swift plan.

Once these decisions are made, complete the affected investigation/authorized
repair and matching verification, reconcile current evidence, seal the refactor
stage if justified, and retire the remaining accepted plans/packages. No pytest
counterfactual evaluation or trial belongs in this workset.

## Resources and retention

Both BYOXPC services have verified removal. Default registry/reconcile are
empty, including pending cleanup and inspection errors. The second directory
fixture remains at `/private/tmp/pw-extension-directory-uge3532e`; its
ownership.json and the pinned rerun's directory cleanup/ownership records
identify the one unwitnessed worker execution. Preserve it until that worker's
absence/exit is established; service removal is not a worker-exit receipt.

All credited native, E2, R1, R2, D2 and retirement runs remain pinned in
tests/RETAINED.json, as do both failed R2 runs and three historical D1 cost
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

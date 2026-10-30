# Workset checkpoint

Current state: F2's authorized reservation repair, Swift Stage 2 and the combined
C/Swift refactor stage are accepted. Final test source is `8500baff`; production
source `4407d0ae` is signed v0.3.3 build 1016. The required 229-case selection
has 212 reviewed unchanged passes and 17 replacement passes, with separate
caller-auth coverage. All 21 BYOXPC cases, all nine reservation arrangements and
the added installation-marker/old-registry cleanup controls pass. No credited
case overlaps sleep; the app remains unchanged. The original four fixture
failures remain preserved, and the original two BYOXPC 4097 failures remain
unattributed. F1 is unresolved at the user's explicit request, so final D2 and
whole-workset disposition remain blocked. No build or dispatcher is running.
The accepted Swift plan is retired; recover it and the acceptance account at
`600a7922`. Check the retirement's affected structure/links next. Keep the workset
records and F1 package live; no pytest counterfactual trial is in scope.

## Current source and evidence

- Production `4407d0aedb84a9f4af7cf133803e05fbdaa174c7`, build 1016, worker
  identity `87c9ac8e3b6dec120ae1c6a5a726fde3ddfc338907bf26a0e91d12efde176336`.
  Test source `8500baff5f10a986657c58792594129d4637ef67` changes only cfg(test)
  Python, suite-local controls and records/documentation; the app is applicable
  under the reviewed exception in f2-reservation-design.md.
- `f2-reservation-final-01`, `20261030T014533Z_3f5dbde2`: 225 pass / four
  constructed-fixture failures, all 229 complete. `f2-reservation-replacements-01`,
  `20261030T020912Z_f6e7fb69`: all 17 pass, replacing the four failed owners,
  registry_recovery, Rust and source checks. Its acceptance-credit.json identifies
  every credited case and source. `f2-native-route-04`,
  `20261030T014440Z_1028993a`, separately passes caller-auth. All are pinned.

The following earlier identities remain historical, not current acceptance:

- Swift Stage 2 implementation: `fd90eee66538cc02dc5d21b7a3fe8eca81a17403`.
  Signed v0.3.3 build 1000, worker identity
  `f477a8488d3f96715e987f7014dcd0aa76ba53b70575118e20ef238b600d4094`.
  Independent review found no implementation defect; exact extracted bodies,
  host/client membership and control reach are recorded in swift-refactor.md.
- Citation corrections: refactor `81f5d260`, D2 follow-up `590c5e42`.
  These do not change production, test sources, generated constants/identity,
  contract/limits/build manifests or app bytes. The latter was the verified
  documentation source before the separately authorized F2 production repair.
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
cleanup. The signed implementation, independent loss controls, public
compatibility controls and combined workload now pass and are accepted.
Observations and limits are in f2-investigation.md and f2-reservation-design.md;
original failures and protected cleanup remain in byoxpc-failure.md. The repair
does not guarantee reply delivery or explain the original failures. Runtime
fixture relocation avoids the denied Desktop requests; no TCC setting changed.

F1 needs later discussion before final D2/workset disposition. Continue only
the accepted-plan retirement here. Do not implement F1, weaken its guarantee or
start a pytest counterfactual evaluation/trial.

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

Historical F2 investigation checkpoint: fixed harness `edf2c561` ran 48 ordinary requests each on
current build 1000 and Stage 1 build 999, all ok with 47 acquisitions each. The
original BYOXPC workload also passed once on Stage 1. These do not reproduce or
resolve the original failures. Controlled equipment `aa45aa48` failed to compile;
fixture correction `7d3b57a5` completed all four arrangements and reproduced
the lost-refusal mechanism. Its source/registry and generator checks both pass.
All six runs are pinned, preserving the compile failure. Baseline worktree/app
remain at /private/tmp/pw-f2-stage1; its build log and comparison are attached
to the baseline observation run. Controlled fixture preparation remains under
/private/tmp/pw-f2-controlled-prep; accepted equipment is committed in tests/.
At that checkpoint production sources and the inspected app were unchanged. See f2-investigation.md
for exact identities, evidence and proposal. f2-reservation-design.md fixes the
protocol, lifecycle, reader and acceptance boundaries. The subsequent repair,
signed build and accepted verification are identified at the top of this record.

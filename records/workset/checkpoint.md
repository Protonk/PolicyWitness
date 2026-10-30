# Workset checkpoint

Current state: all included stages and the authorized F1/F2 repairs are accepted.
Final implementation/test source is `8ceb04ea`; production `4407d0ae` remains
signed v0.3.3 build 1016. The required 229-case selection has 212 reviewed
unchanged full-run passes, 15 F2 replacement passes and two current F1 source
passes, with separate caller-auth coverage. Original failures remain failed.
Both required refactors were completed. D1 and D2 finish in the required order;
no counterfactual evaluation, pytest trial or future-CHECK handoff was done.
No build, dispatcher or delegated write is running. Commit final acceptance,
then retire the remaining D2/workset plans and owned records and run the two
affected source/structure/prose-link checks. Protected evidence and the
unwitnessed-worker directory remain retained through retirement.

## Current source and evidence

- F1 source `8ceb04eaffebf2395c7df839131c1b35d2b23ab2` changes the source
  checker, independent controls and suite account only. `workset-f1-green-01`,
  `20261030T025029Z_6523788d`, passes both affected cases: 14 accepted snippets,
  102 rejected snippets, eleven detected symbol omissions with restoration,
  and six Swift/C file mutations. The preceding independently exposed failure
  is pinned as `workset-f1-red-01`, `20261030T024703Z_892e823d`, source
  `55116788c3d25b782008eb98388e3477284d2461`. Its 21 missing rejections remain
  failed observations, not a production host violation.
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

## Findings and disposition

F1: the user authorized adding the three missing extension APIs and independent
expectations after the original deferral. The guard and its omission controls
now pass at the source above. The documented host boundary is preserved, with
the covered names explicit. Computed names and complete Swift/C analysis remain
outside this source convention. Original D1 evidence and the historical decision
are preserved in D2's inherited package; final acceptance is attributable to
this authorized correction, not a rewrite of the earlier finding.

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

No remaining finding needs a user decision for this engagement. The original
F2 cause and missing worker-exit witness remain explicit limits, not new claims
or additional assignments. Retire only this workset's plans and records, then
stop; the later counterfactual investigator chooses their own work.

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
  final bounded citation correction `590c5e42`. F1 then delayed final disposition;
  its authorized closure is recorded above.
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

## Final workset acceptance

The primary executor accepts the complete bounded engagement. C0 was frozen
before substantive implementation; its current bytes still exactly match
`0c22d2565b42f543bd6334a1d09f95781ef09386`. This integrity check does not
evaluate the counterfactual. E1 and E2 have accepted native observations and
public integration, with matched/crossed authority results and independent
effects. Both C and Swift refactors were carried out, with their design,
adaptation and acceptance records. D1's investigation precedes its absorption
by D2; the proposed B1 machinery is explicitly declined, C1–C5 and the authorized
F1 correction are accepted. F2 is accepted with its attribution and delivery
limits. No required refactor or investigation is omitted, and no included
decision remains unresolved.

Current combined credit is 212 cases from f2-reservation-final-01, 15 from
f2-reservation-replacements-01, and the two source cases from workset-f1-green-01:
229 distinct required cases, not one passing full-battery run. Caller-auth is
separate. The green run's combined-acceptance-credit.json names every case,
actual source and run. The original full-run failures and red F1 observations
remain failed and retained. No credited result overlaps sleep.

Reviewed reuse from `8500baff` to `8ceb04ea`: the executable changes are confined
to check.py and check_planner.py; their owning source case reran. The generator
case reads the rule declarations and documentation sources and also reran.
The suite README adds exact names, control scope and the issuer; it introduces
no new links, generator ownership or runtime promise. Other changed files are
plans, records and retention metadata, including the accepted Swift-plan
retirement. Runtime sources, schemas, limits, build inputs, native identities,
shared test helpers, fixtures and other case wrappers are unchanged. The sole
controller delta since signed source `4407d0ae` remains the previously accepted
cfg(test) embedded Python adaptation, already rerun at `8500baff`. The signed
app inventory still exactly matches the accepted before/after inventory with
SHA-256 `9529b7f22ca49559a3aee9200fd4ac9fe83268351576dc77d1c501e8f13cd4da`.
These comparisons establish identity; retaining the unaffected executed paths
is an explicit applicability judgment. Independent read-only review by
review_public_extension confirms the bounded delta and finds no blocker.

Recoverable stage index (the final acceptance commit contains both remaining
record packages before their ordinary retirement):

| Stage | Earlier fixed acceptance/source | Record path |
| --- | --- | --- |
| C0 | account `0c22d256`; seal `cf0136b` | records/workset/pytest-first.md and c0-seal.md |
| E1/E2 | seal `29d1c79` | records/workset/e2-seal.md and native/integration records |
| R1 | acceptance `96d0328e`; plan recovery `6dab4430` | records/workset/c-refactor.md |
| R2/F2 | acceptance `600a7922`; implementation `4407d0ae` | records/workset/swift-refactor.md and f2-reservation-design.md |
| D1 | original package `cd6adaa`; primary `7562d24`; retirement `950c604f` | records/check-support/ in that history; absorbed records/checks-before-check/inherited/ |
| D2/F1 | C1–C5 `96dffd56`; final citation `590c5e42`; F1 `8ceb04ea` | records/checks-before-check/acceptance.md |

All selected historical and current runs remain pinned; retirement releases
none. Preserve the unknown-worker directory and ownership record, the baseline
comparison worktree and the unrelated pytest-evidence worktree. No claim is made
that service removal established the missing worker exit. Retire only the D2
plan/package and the two root workset plans/package. Then run the affected two
source/structure/prose-link cases, pin their actual source and reconcile output.
Those deletion-only checks do not require another signed build or live battery.
Stop after retirement verification; do not begin the later counterfactual work.

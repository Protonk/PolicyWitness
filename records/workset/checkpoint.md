# Workset checkpoint

Current phase: R1 accepted; R2 Stage 1 is next. Main is clean at R1 acceptance
`96d0328e` before this checkpoint-only update. No build, dispatcher or owned
native/external service is active. C0, E1/E2, R1, D1 and the bounded D2
investigation/corrections have accepted milestones. Swift implementation has
not begun. Final combined verification and the unresolved F1 decision remain.

## Next work

1. Agent `swift_design` revalidates the recorded R2 design against R1, implements
   only Stage 1, commits and stops for primary review/build/verification.
2. After Stage 1 acceptance, implement and verify Stage 2. Preserve shared
   client/host contract ownership, encode/decode asymmetry, query ordering and
   actual moved-code reach through mutation controls. No CWorker driver refactor.
3. Reconcile D2 facts and verification against final source, run the matching
   signed default battery plus applicable C/Swift/BYOXPC controls, and reconcile
   retention/findings. Never credit earlier source without dependency review.
4. Final workset retirement remains pending F1's explicit disposition. Keep the
   finding visible; do not treat its deferral as a repaired or accepted guarantee.

## Recoverable states

- Intake `bf7e97faab75754efe719b0bad20e83b67762c15`; execution companion `4b18284`.
- Initial counterfactual `0c22d2565b42f543bd6334a1d09f95781ef09386`, sealed
  `cf0136b`. It remains frozen; no retrospective evaluation or pytest trial.
- E1 native candidate `b6cac0d`, acceptance `d2f3bbf`; crossed follow-on `8aa7402`.
- E2 public design `ad1c1ca`, implementation/signed build 977 `7426fc0`, harvested
  goldens `3ff8bf2`, genuine response24 captures `a7c1408`, enum-fixture adaptation
  `b565c1b`, full experimental seal `29d1c79`.
- D1 original chain `def5de0` through `cd6adaa`, primary acceptance `7562d24`.
  D2 absorbed twelve exact copies. D1 plan/package retired `950c604f`; pinned
  `workset-d1-retirement-01` passed both source/link cases.
- D2 original chain `7e9d677` through `f996212`, merged `bb92c21`, primary
  acceptance `96dffd56`. Pinned `workset-d2-main-01` passed five source cases at
  `bb92c21`. Its fixed ownership/trace account describes `7562d24`; the E2
  comparison and later correction/acceptance records qualify newer applicability.
- R1 design `6e40887`, implementation `341f9441`, acceptance `96d0328e`.
  Signed v0.3.3 build 994 has worker identity
  `b307fc295883bbcdf4bdd2b2855ce8d6fe969eb93d104e54c7e775075bad6b0f`.
  Pinned run `workset-r1-01`, `20261029T223004Z_941f9f72`, passed all 201 default
  cases plus native-clock, inheritance-mutation and order-barrier controls:
  204/204, no skips/unrun/errors/sleep/app changes. Exact native bodies and old
  ledger remain unchanged; primary and independent reviews accepted the owners.
- R2 read-only preparation is committed in `records/workset/swift-refactor.md`
  at `f8f3c24f`; implementation requires revalidation against the R1 baseline.

## Finding F1

The documented host-source rejection of extension issue/consume/release calls
is absent from the API set, and controls derive that family from the same set.
The recommendation is to preserve the guarantee with the missing names and
independently specified rejection controls. The user explicitly chose to keep
it unresolved for later discussion. No repair or expectation change is
 authorized; this is not a final accepted disposition. Evidence and implications
remain in the absorbed D2 finding and original D1 commits.

D2 implemented only bounded ownership/citation/table-account corrections,
canonical Python repair hints with controls, dated raw-evidence availability,
and the account of both existing release-baseline gates. The B1 registry
proposal was declined for implementation. No future CHECK handoff was prepared.

## Evidence and resources

`tests/RETAINED.json` pins the accepted native/E2/R1/D2 and retirement runs plus
three historical D1 cost inputs. The third D1 pin keeps null source because its
actual dirty bytes require the attached source snapshot and working delta;
never call that a clean commit run. E2 coordinated evidence remains 81 passes
plus one failed obsolete enum anchor; its corrected rerun is separate.

Supported pruning removed thirteen earlier eligible runs and later the shape
harvest/development-write runs. Their compact accounts/harvests remain in git;
raw bytes do not. D2's isolated development output was pruned after the main
five-case pass, and its clean worktree was removed through Git. All D2 commits
remain integrated. The unrelated pytest-evidence worktree, release pins and
`.release-rotation` remain untouched.

The E2 BYOXPC service was removed with verified cleanup; registry/reconcile
were empty afterward. Use exact durable ownership before any later external
runner cleanup. Builds/tests share the checkout lock; never unlink it or bypass
retention/resource cleanup helpers. Stop starting work on a user interruption,
settle active ownership and commit a resumable checkpoint after execution stops.

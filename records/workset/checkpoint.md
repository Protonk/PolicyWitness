# Workset checkpoint

Current phase: E2, public extension addition and crossed follow-on; C0 and E1 complete.

The intake baseline is `bf7e97faab75754efe719b0bad20e83b67762c15`.
Production implementation has not changed. E1 added independent native
directory equipment and its tests/documentation at `3ce5d8f`, corrected at
`b6cac0d735f0384fc50d94a6eba6ab18e9323763` after a failed candidate run.
The execution companion and intake record are committed as `4b18284`.
The initial counterfactual C0.2 is frozen at
`0c22d2565b42f543bd6334a1d09f95781ef09386`; the C0 acceptance record names the
review and its ownership-order clarification. The original account is `6cd868b`.

Next work:

1. Design and implement the smallest supported public directory read-write
   addition, preserving legacy public file-operation meanings; complete the
   matched/crossed follow-on and integrated verification before the E2 seal.
2. Reconcile D1's isolated investigation against its fixed source. D2 cannot
   begin before D1 acceptance.
3. Seal the experimental stage before either core refactor begins.

E1 is accepted by primary-agent self-review with `review_directory_native`
source review. Signed native run `workset-native-directory-02` passed both
native cases at `b6cac0d`, with all five directory scenarios and eighteen read
scenarios complete. `workset-native-structure-01` passed the source/catalog and
generator/link cases. Their pins are committed with the E1 findings; the
directory-native record states provenance and the structural prose-delta limit.

The read-only C0 reviewer is complete. Agent `binding_investigation` owns D1 in
the isolated worktree `/private/tmp/pw-workset-binding`, detached at `cf0136b`.
Its writes are limited to the associated plan and `records/check-support/`;
it stops after a reviewable D1 acceptance package. No D2 work is dispatched.
The worktree creation required the same command outside the automation sandbox
after sandbox refusal of `.git/worktrees` creation.

Temporary D1 evidence pins protect `runs/drift-plan-investigation-20261027-02`
(source `1612eb5e0bd503f0185dda9cda0331be0d9a764f`),
`runs/drift-cost-candidate-01` (source
`22f688d7d4c1aefe890c41db03a897141796f0e9`), and
`runs/drift-acceptance-fixes-03` (source not yet established). Run IDs are in
`tests/RETAINED.json`; these are historical cost inputs, not current behavioral
verification. Their completed ownership was verified and pins written through
the retention helper while holding the checkout lock. Revisit after D1.

No running build/test, workset-owned native child or external runner.
D1 finding F1 remains unresolved by explicit user instruction: the documented host-source rejection of
extension issue/consume/release calls is absent from its API set, and controls
derive that family from the same set. The recommendation is to preserve the
guarantee with the missing names and independently specified rejection controls.
The user chose to keep it unresolved for later discussion. No repair or
expectation change is authorized, and this is not an accepted final disposition.

Supported `make prune` preview/apply removed thirteen eligible unpinned runs
after D1 confirmed that only its three pinned inputs were needed. They were
the eleven old drift/planning runs plus the E1 baseline and failed first
directory candidate. Their compact findings remain committed; no future claim
may imply their raw output remains available. All five workset pins and release
pins survived. The separate pytest-trial worktree, release material and
`.release-rotation` remain untouched; cleanup reported no failures.

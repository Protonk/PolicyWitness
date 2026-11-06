# Candidate evidence retention review

Status: dependency review, index replacement and supported pruning complete. Both retained candidate runs passed in full.

The installed non-release pins are `extension-consolidation-battery-01` and `extension-consolidation-build-refusals-04`. This keeps the current default battery and the larger complementary whole-family run in their original owned locations. Complete consolidated BYOXPC evidence is preserved instead in `evidence/extension-consolidation-actors-03-complete.tar.gz`, SHA-256 `de1dc7f74fda4810d29b7aa995f7306228ded632b9ec7281dc35843cc5b40b10`. The release-managed v0.3.4 entry remains unchanged.

## Existing dependencies

The two superseded actor-passes pins have identified historical copies under `records/doc-lookback-2026-11-04/critique/historical-evidence/`. Independent read-only review verified archive hashes and every unique archived member:

- `evidence.tar.gz`: SHA-256 `8de145d7fee00fb786acab64cfffc952c74d5c9a6a9d4d19fd301380502960b4`, 6,723 unique members.
- `older-complementary.tar.gz`: SHA-256 `666314789e194d19e63bb126d9f2aba80b9a2c15ae67f78a305682bd0ed0ef47`, 2,745 unique members.

The old default extension-directory `ownership.json` was a pre-cleanup snapshot with `removed:false`. Its final `cleanup.json` records removal after all 13 original host reap observations. Both snapshots and those 13 original envelopes are additionally preserved in `evidence/previous-default-cleanup-observations.tar.gz`, with the original paths, run ID and hashes. The review does not infer process settlement from a currently absent path. `retention-readiness.json` records the exact file inventory and distinction.

The documentation critique's separate current-evidence archive is also intact: `records/doc-lookback-2026-11-04/critique/current-evidence/evidence.tar.gz`, SHA-256 `efd5c15b4b16c1ddc76f996e59ee5935a3dfa4a9823591c4d66f7ffa3382f238`. The reviewer verified all 17,200 unique blobs and the three original run records. It preserves complete critique-default-02 and critique-controls-01, plus critique-default-01 metadata/integrity and its failed case; its 215 superseded passing case directories are explicitly omitted. Existing historical/F1 packages cover earlier lookback repairs, audit and documentation observations.

No current pathname reference was found for the other unpinned footprint/documentation-only runs in active source or record documents outside archives. The active FOOTPRINT plan does require current maximum-target and maximum-exec receipts. Both now have passing final-battery results, with separate actual host/client observations and preserved raw inputs/effects. These supersede the two older prerequisite credits in footprint-prereq-01; that older run remains recorded as two passes plus a generator-contract failure. This is a prerequisite replacement, not execution of the separate footprint investigation or a memory claim. Documentation-only verification is likewise superseded by current source-drift/default checks.

## Resource ownership and preservation

The bounded recovery audit found all 208 actual pytest ownership records closed and the release-rotation directory empty. It found eight extension-directory cleanup receipts with removal recorded and no unreaped attempts. Historical unresolved resources outside this checkout retain their original records and are unaffected by replacing pins. The Stage 1 prototype container's original ownership record remains active; copies do not move it or claim removal. The inherited-restriction container is preexisting and not newly owned.

Completed-run root metadata and app-integrity observations are additionally preserved in `evidence/completed-run-metadata-before-br4.tar.gz`, SHA-256 `8ae88d9e54ba1f01cf11833a0ae578e9a1c78e01604fc3154ec6ddbc138d40b8`. Its inventory states that case trees are omitted; this is not a substitute for the separately preserved raw targeted evidence or retained final runs. Complete C4, E1, E2, order/native and failed BR3 runs, plus selected earlier failure observations, have individual immutable archives and per-file manifests.

After the last required result, the coordinator updated `tests/RETAINED.json` through its atomic writer under the existing execution lock and ownership guard. `retention-before.json` preserves the prior index; `retention-change.json` records exact hashes and the unchanged release entry. The normal pruner preview identified 56 eligible completed/unretained runs, the two intended retained runs and three unmanaged areas. Apply removed exactly those 56 runs, with no failures; `prune-preview.json` and `prune-apply.json` retain both receipts. No interrupted, ambiguous, unmanaged, release-managed or still-owned recovery data was manually removed. The record-local helper's first attempt used an unsupported lock-purpose name and refused before mutation; `retention-attempt.json` preserves the correction to the existing execution purpose. No repository locking code changed.

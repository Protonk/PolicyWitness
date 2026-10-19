# Documentation revision and branch-build verification

This record accompanies [the Markdown guidance plan](../MARKDOWN-GUIDANCE-PLAN.md).
The review base is `a7cf758` on `main`; the changes are on `doc-rework`.
The implementation is ready for merge review. Evidence linked below is
gitignored and available only in this local checkout.

## Result and source coverage

The maintained guidance uses direct instructions and preserves technical names,
end-user distinctions and historical observations. Sandbox troubleshooting is
local to each workflow. The replacement check verifies nonempty sections and
diagnostic routes; independent wording passes. The architecture account and
its rendered document graph describe the new rule. The original prompt is
deleted, and the plan contains its requirements.

The signed production candidate is
`2b0be8e1632850aaaa12c657e52882c6b0233d7d`, stamped
`v0.3.1-73-g2b0be8e`, build number `757`, with `dirty: false`.
Both its fresh and cache-reusing builds passed without warnings. The worker
identity is
`bf9b04aefccf51568969e6914149c389d6c271da5033f65f39dc73cddaa3372e`.

The [complete acceptance run](../tests/out/runs/doc-rework-candidate-20261019/run.json)
passed all 66 selected cases with no skips or failures. It covers the six
`source_drift` cases, the Rust unit/formatting and selected regression cases,
the Swift core unit executable, C/Swift ABI agreement, the C worker harness,
independent live worker/host queries and smoke/caller-authorization checks,
plus provenance, real signatures and offline release/publication controls.

After that run, changes were limited to the two test-build warning fixes
described below and this record. The
[corrected focused run](../tests/out/runs/doc-rework-test-build-fixes-2-20261019/run.json)
at `5d6af0a` rebuilt the lifecycle companions and Swift test executable and
passed all 465 Swift tests, including 2,880 finite-model disposition rows.
Its compiler logs contain no warnings. The selected app is still the unchanged
production candidate above.

The other 65 acceptance cases retain their original source attribution. Their
production inputs and executed test code did not change: the later code delta
is confined to `runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift` and
`tests/fixtures/worker_lifecycle/clock_failure.c`, both exercised by the repeated
Swift case. This is a reviewed applicability judgment, not a claim that all
66 cases ran at the final documentation/retention commit. Final source scans,
local-link validation, generator freshness and diff checks cover that closing
documentation change.

## Build issues and resolutions

| Issue | Resolution | Evidence |
| --- | --- | --- |
| Signing discovery reported zero valid identities in the automation sandbox. | The same `security find-identity -v -p codesigning` command outside that sandbox found the configured Developer ID. Use the documented unsandboxed entry point for signing and compiler discovery; no signing rule was relaxed. | Baseline and candidate signed builds, plus real signature controls, passed outside the sandbox. |
| The production controller build warned that `capture_reserving` was unused. | This module is shared with the observer, which calls the helper in production; controller receiver tests also call it. Add a local `allow(dead_code)` annotation identifying those consumers, matching the existing treatment of `CollectionBudget::from_argument`. No behavior changed. | Corrected fresh/reused builds and the Rust test build are warning-free; Rust tests passed. |
| A fresh native build exposed two ambiguous-trailing-closure sites in `PWRunnerAPI.swift` that cache reuse had not recompiled. | Parenthesize the `Optional.map` closure arguments in the signal and exit-code comparisons. Regenerate the conservative host/worker identity through its owning generator. No wire version or ABI layout changed. | Corrected fresh/reused builds are warning-free. Swift disposition controls, ABI checks, worker harness, live identity and smoke cases passed. |
| Eight clock-fixture variants warned that `phase2_start` was unused. | Move the static declaration into the `PW_CLOCK_EXPIRE_SECOND_PHASE` branch, its only consumer. Zero initialization and process lifetime remain unchanged. | The corrected focused run rebuilt every companion without warnings and passed the gated clock controls. |
| The maximum-reply Swift test declared two unmodified values as `var`. | Use `let` for `phases` and `validator` in `maximalReplyEncodedSize`; retain the mutable per-phase copies and all maximum-reply assertions. | The corrected focused run compiled without warnings and passed all 465 tests. |
| The first warning-cleanup commit changed an earlier pair with the same names in `addAbsentOptionalFields`, causing assignment errors in the focused build. | Restore that earlier mutable pair and apply `let` only at the reported warning sites before `var record = try maximalRecord()`. Preserve the failed run and corrective commit. | The failed run has no acceptance credit; the subsequent focused run passed. Both remain available for review. |

The build used Developer ID Application: Adam Hyland (42D369QV8E), the Xcode
macOS 27.0 SDK, Apple clang 21.0.0, Swift 6.4, Cargo 1.99.0, Meson 1.12.1 and
Ninja 1.13.2. Compiler warnings in the source and fixture builds were resolved;
deliberately rejected mutation inputs remain rejected.

## Build and test receipts

| Source | Observation | Receipts |
| --- | --- | --- |
| `df7365c`, clean baseline, build number `751` | Signed build succeeded on `doc-rework`. Provenance and signature cases passed; the Rust warning above was present. | [Build log](../tests/out/runs/doc-rework-baseline-20261019/review/baseline-build.log), [source/provenance](../tests/out/runs/doc-rework-baseline-20261019/review/baseline-provenance.json), [test result](../tests/out/runs/doc-rework-baseline-20261019/run.json). |
| `cb3b3be`, build number `756` | Reused build was warning-free; the fresh build succeeded but exposed the Swift closure warnings. | [Reused build](../tests/out/runs/doc-rework-candidate-20261019/review/candidate-reuse-build.log), [fresh build](../tests/out/runs/doc-rework-candidate-20261019/review/candidate-fresh-build.log). |
| `2b0be8e`, build number `757` | Corrected fresh and reused builds both passed without warnings, followed by the complete 66-case run. | [Fresh build](../tests/out/runs/doc-rework-candidate-20261019/review/resolved-fresh-build.log), [fresh provenance](../tests/out/runs/doc-rework-candidate-20261019/review/resolved-fresh-provenance.json), [reused build](../tests/out/runs/doc-rework-candidate-20261019/review/resolved-reuse-build.log), [reused provenance](../tests/out/runs/doc-rework-candidate-20261019/review/resolved-reuse-provenance.json), [test result](../tests/out/runs/doc-rework-candidate-20261019/run.json). |
| `45bf39f` | Focused test build failed on the misplaced `let` edit; no test acceptance was credited. | [Failed result](../tests/out/runs/doc-rework-test-build-fixes-20261019/run.json), [diagnostics](../tests/out/runs/doc-rework-test-build-fixes-20261019/review/test-build-fixes.log). |
| `5d6af0a` | Corrected focused case passed; Swift and C fixture builds are warning-free. | [Result](../tests/out/runs/doc-rework-test-build-fixes-2-20261019/run.json), [console receipt](../tests/out/runs/doc-rework-test-build-fixes-2-20261019/review/test-build-fixes-2.log). |

The full selection is recorded in the
[candidate plan](../tests/out/runs/doc-rework-candidate-20261019/plan.json).
The two acceptance runs preserve their app inventories and report no changes
to the inspected app. Each run's `review/attachments.json` hashes its additional
original build receipts and identifies the test-source commit; individual
build-provenance files identify their own source revisions.

## Branch-name comparison

The existing release controls now execute the actual stamp fragment from
`build.sh` and the real release preflight in one disposable Git repository.
They compare `main`, `master`, `doc-rework` and newly created then renamed branches
at identical HEAD, tags and checkout path. All 12 comparisons passed across
untagged, annotated-tag and dirty-tree states:
[comparison receipts](../tests/out/runs/doc-rework-candidate-20261019/suites/preflight/release_publish_controls/artifacts/branch-names/comparisons.json).

The untagged release refusal and dirty-tree refusal remain intact. New branch
names required no build or release-policy workaround. This observation covers
the exercised local workflows; it does not establish a remote publication or
notarization result.

## Editorial and mechanical acceptance

The final inventory has 113 canonical Markdown sources. The source-only scan
found no remaining actor-label prose outside the plan's four bounded verbatim
before excerpts, verified against the review base. The remaining whole-word
matches are technical `AGENTS.md` paths. Broader matches are platform/process
names, graph identifiers and the search expression itself.

All four `CLAUDE.md` symlinks retain their targets. The excluded
`CONTRIBUTING.md` is unchanged. No retained output, scratch copy or packaged
documentation was edited to satisfy the editorial search. Builds staged their
normal output through the owning tools.

The entire source inventory has the same 78 pre-existing link findings as the
baseline, including missing historical evidence and stale references in earlier
plans; there are no new findings. Changed-document links pass. Active source
guidance and citations no longer name the retired equality rule or headings.
The [scan receipt](../tests/out/runs/doc-rework-candidate-20261019/review/editorial-verification.json)
records the initial completed source comparison; final validation includes this
completed record.

All five generator freshness checks pass. Repeating architecture generation
writes nothing; the regenerated document graph was visually reviewed. The
[source and guidance controls](../tests/out/runs/doc-rework-candidate-20261019/suites/source_drift/runner_source_manifests_agree/artifacts/planner-controls/controls.json)
contain 157 successful scenarios, including rejected missing/empty/fake sections,
wrong or misplaced diagnostic routes, and accepted independent rewrites.
The full `source_drift` selection also passed the graph-citation, generator,
stale-copy and build-documentation controls.

## Evidence lifetime and review

Four explicit holds in `tests/RETAINED.json` protect the baseline, complete
acceptance, failed cleanup and corrected focused runs for this merge review.
Their reasons identify this record and require retirement once review is
resolved and integrated acceptance supersedes their claims. These are manual
retirement conditions under the current index, not automatic expiry or an
implementation of the separate retention plan.

Review the commit sequence and complete diff with:

```sh
git log --oneline a7cf758..doc-rework
git diff --stat a7cf758..doc-rework
git diff a7cf758..doc-rework
```

The branch is left for review; it has not been merged into `main`.

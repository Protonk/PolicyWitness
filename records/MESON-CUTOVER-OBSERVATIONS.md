# Meson cutover observations

Local cutover checks passed; notarization and final ZIP acceptance not run.

Record, 2026-10-08. The native compile of PolicyWitness (the C worker and
validator, the C shim, the Swift client and host) moved from direct `clang`
and `swiftc` calls in `build.sh` to the root `meson.build`, driven by
`build.sh`. This record states what was observed locally before that change
landed and what remains outstanding. It is an evidence record, not a plan: the
plan that directed the migration was removed from the repository after
execution at the maintainer's request. All linked test and distribution
evidence is gitignored and exists only in the local checkout.

## What was tested

- **Base commit plus diff.** The gate ran against base commit `f69a7e3437f0ee9e9df949302bd4085e309b96ba` plus
  the exact tracked diff recorded at
  `tests/out/runs/meson-cutover-default-2/migration/source/tracked.diff`
  (SHA-256 `0dc85b5a410218dd77d9b2d083d2d97de45b88bfeb693a173220f9b3dee4c984`, no untracked files). The cutover commit carries that
  diff plus this record, the retention index entries below and the plan's
  removal; those additions are not build or test inputs.
- **Build stamp.** `PWBuildDescribe` `v0.2.7-28-gf69a7e3-dirty`, `PWBuildCommit` `f69a7e3437f0ee9e9df949302bd4085e309b96ba`,
  `CFBundleVersion` `488`; worker identity `e2ffb11905ed22af49ad80dcc37fc08664dd067b3b5c5452da2b5b373ce7e4da`.
- **Artifact.** `dist/PolicyWitness.zip` SHA-256 `0af979bfe7cfc1fbc1e071c0547c137758138022b204ed3c6344a46ee6656ba5`; the app
  inventory the dispatcher recorded before the battery is
  `tests/out/runs/meson-cutover-default-2/artifact-integrity/before.json`.
  Meson outputs (SHA-256, from
  `tests/out/runs/meson-cutover-default-2/migration/receipts-final/receipt.json`):
  `sb_api_validator` `2f36580e3440c0b298565265026b9866fde0823244e51502af0d5a0e616e7150`; `pw-probe-runner` `6c521a549a0243b5aae871d1ef7763df5e1372ed7e52b72e802066ffe39451cc`; `libPWCWorkerShim.a` `479b74cd0d1239b0681571d57ae56952b3e6db85e9d87d8ac323a0af487f5ffe`; `pw-runner-client` `84c8b6854094227a4afbbb97995db9d0a0ac073338a1018aebfca59876641290`; `PWRunner` `819f5a0794034887dc9254cff657c93907fbd2b3e1f6262658f34761af69d21e`
- **Toolchain.** Meson 1.12.1, Ninja 1.13.2; Xcode developer directory
  `/Applications/Xcode.app/Contents/Developer`, macOS SDK 27.0; Apple clang `Apple clang version 21.0.0 (clang-2100.3.34.2)`;
  Swift `Apple Swift version 6.4 (swiftlang-6.4.0.34.1 clang-2100.3.34.1)`; `PW_INSPECTION=1`, `BUILD_XPC=1`.

## Local gate results

| Run | Selection | Result |
| --- | --- | --- |
| `tests/out/runs/meson-cutover-default`, `tests/out/runs/meson-cutover-default-2` | default battery | first attempt `meson-cutover-default`: 167 of 168 passed, 0 skipped, 0 unrun, 1 harness errors, app unchanged: True (the one failure is the Rust observer timing test `both_raw_streams_are_bounded_at_exact_edges`, cutoff `pipe_open_after_exit`, in code this change does not touch); full rerun `meson-cutover-default-2`: 168 of 168 passed, 0 skipped, 0 unrun, 0 harness errors, app unchanged: True |
| `tests/out/runs/meson-cutover-optin` | `preflight/signed_artifact_controls`, `witness_contract/order_barrier_mutations`, `smoke/runner_caller_auth` | 3 of 3 passed, 0 skipped, 0 unrun, 0 harness errors, app unchanged: True |
| `tests/out/runs/meson-cutover-byoxpc` | `--suite runner_byoxpc` | 17 of 17 passed, 0 skipped, 0 unrun, 0 harness errors, app unchanged: True |
| `tests/out/runs/meson-cutover-drift` | `--suite source_drift` on the cutover tree | 5 of 5 passed, 0 skipped, 0 unrun, 0 harness errors, app unchanged: n/a |

Each run's `run.json` is the authority for counts, skips, unrun cases, harness
errors and the unchanged-app check. The commands were
`PW_TEST_OUT_DIR=tests/out/runs/<name> tests/run.sh` with the selectors above,
from an unsandboxed, logged-in GUI session.

Build-chain controls through `make build`, with logs under
`tests/out/runs/meson-cutover-default-2/migration/` (`chain.log` and the
numbered step logs): a second build after a source change leaves Meson with
no work; `PW_INSPECTION=0` and back switch the Swift flags between `-O` and
`-Onone -g`; an injected `-Doptimization=2` makes the next build refuse
before bundle assembly with the dist app's inventory unchanged, and a fresh
directory refuses an inherited `CFLAGS` the same way (an existing directory
does not read it, as Meson reads environment flags only at first setup);
`BUILD_XPC=0` into a separate `DIST_DIR` builds only the two C executables,
packages a partial bundle without the service, client or helpers, and the full
artifact inspector rejects it; `BUILD_XPC=1` restores the complete app. In a
disposable source copy, a comment appended to `meson.options` changed the
identity and the regenerated ABI header and Swift copy rebuilt exactly the
worker and the host (`migration/identity-rebuild/`).

## Comparison with the released app

The released 0.2.7 app (`dist/archive/v0.2.7/PolicyWitness-0.2.7.zip`,
SHA-256 `c5dd385d510109c5761856895f1ebc1525f16396ff812e3280b7f7be04c47875`,
built from `50802056dfdf6ef55d36d49c40512603594e65ae`) was extracted under
`/private/tmp` and compared with the candidate by
`tests/lib/native_compare.py app --across-builds`
(`migration/app-compare-released.json`): the evidence-manifest inventory and
entitlements, the exported `_pw_*` markers, and every executable's dynamic
libraries, load-command sequence, segments and sections, platform build
version, imports, `_sandbox_*` imports and Swift module names are equal, and
both Info.plists differ only in the four stamp values. The only layout
difference is the released app's `Contents/CodeResources`, which stapling
adds. Code and data sizes were recorded, not compared, because the sources
differ between 0.2.7 and the candidate.

The five request fixtures under `tests/fixtures/pw_runner/` ran through both
apps (`migration/envelopes-candidate/`, `migration/envelopes-released/`) and
were compared by `tests/lib/envelope_compare.py compare --across-builds
--expect-identity e2ffb11905ed22af49ad80dcc37fc08664dd067b3b5c5452da2b5b373ce7e4da` (`migration/envelope-compare-released.json`):
all five fixtures equal under the declared volatile classes and the four stamp values, with the worker identity equal to the candidate's (attempt 2, `envelope-compare-released.json`). Attempt 1 (`envelope-compare-released-attempt1.json`, `envelopes-candidate-attempt1/`) differed for `specimen_mach_deny`, `specimen_path_diagnostics_strict`: the candidate's log capture saw no kernel deny line in its window while the released app's run did. The candidate's rerun captured them; the difference was unified-log latency, which the log channel documents as early or late availability, not a difference in the apps.

## Earlier chunks

- Baseline: `tests/out/runs/meson-baseline` (default battery against the
  build.sh-compiled app at `14252b0`, 168 of 168, with that app retained under
  `retained/`).
- Pilot: `tests/out/runs/meson-pilot` (default battery against a signed copy of
  the baseline app with the Meson-built executables substituted, 168 of 168;
  structural comparisons equal for all four executables under Xcode and under
  the Command Line Tools; envelope comparison equal under the stated volatile
  classes; configuration-state and no-XPC controls under `migration/`).
- Chunk 2: `tests/out/runs/meson-chunk2-barrier` (order-barrier mutation
  control reading the host list from `meson.build`, baseline accepted and both
  bypasses detected) and `tests/out/runs/meson-chunk2-offline` (source_drift,
  dispatcher and shell_helpers after the reader and equipment changes).

## Outstanding

Release validation is the maintainer's: `make notarize
NOTARY_KEYCHAIN_PROFILE=<profile> IDENTITY=...` on this commit from a clean
checkout, or the next real `make release`. When it runs, link the attempt's
`dist/evidence/<attempt>/` receipts and the final
`tests/out/release-acceptance/<run>/acceptance.json` here and record the
accepted ZIP hash and the source actually used. Local checks do not certify
Apple's acceptance. A migration-caused failure must be fixed and revalidated
or rolled back; reverting the cutover commit restores the direct compiles and
the former readers, after which the identity must be regenerated and the app
rebuilt.

## Deviations from the plan as executed

- **Build recipe.** The plan said `build.sh` reconfigures on every build. It uses `meson setup` for a new directory and `meson configure` afterwards instead, because `meson setup --reconfigure` runs Ninja's `restat` tool after regenerating, which discards the marks swiftc leaves when it does not rewrite unchanged objects, so the build after any source change recompiled the Swift targets once more. `meson configure` regenerates only when a value changed; the policy assertions still run on setup and on every regeneration.
- **dSYM bundles.** The plan did not foresee that the old one-shot `swiftc -g` link ran `dsymutil` implicitly, leaving a `.dSYM` beside each Swift executable in the bundle. Meson links in a separate step, so `build.sh` now runs `dsymutil` itself for inspection builds to keep that layout.
- **Swift discovery module cache.** The plan asked for a writable module cache during compiler discovery. Meson passes no compile arguments to its Swift sanity check, so discovery uses swiftc's default per-user cache; only the targets use `builddir/swift-module-cache`. Documented rather than engineered around.
- **In-tree executable ignores.** The plan said to remove both. The validator's ignore stays because the retained manual debugger helper (`controller/tools/sb_api_validator/build.sh`) still writes its output beside the source; only the worker's ignore was removed.
- **Inherited `CFLAGS`.** The plan's refusal of injected native arguments holds for `-Dc_args=...` and for `CFLAGS` on a fresh directory; an existing directory does not read environment flags at all (Meson reads them only at first setup), so there is nothing to refuse there. Documented.
- **Missing-Swift refusal through `build.sh`.** The plan wanted the pilot's missing-Swift check repeated through `build.sh`'s option mapping. `build.sh` has no toolchain knob that can hide swiftc without also hiding clang, so the refusal was exercised through Meson directly (a native file naming a nonexistent swiftc) and `build.sh`'s propagation of a Meson setup failure was exercised with an injected option instead.
- **Architecture edge direction.** The plan's "edge to `drift_check`" became `drift_check → meson_build` of kind `checks`, matching the graph's convention that a `checks` edge runs from the check to what it checks; the label is the plan's.
- **Timing of the architecture edit.** The `meson_build` node and the new rule citation went in during Chunk 2 rather than Chunk 3, because the generator contract refuses a checker rule the document graph does not cite; Chunks 2 and 3 land together, so the landed state is as planned.
- **`meson` equipment kind.** The plan said to treat failed introspection as an error; in addition the dispatcher learned a `meson` equipment kind, declared on the two cases that read the manifest, so a missing Meson is an unrun case with a named cause rather than a failing case.
- **Chunk 2 documentation.** The intermediate three-way wording was written and validated, then replaced by the final two-way wording in the same uncommitted tree; only the final wording lands.
- **Default battery at the gate.** The first gate battery failed one Rust observer timing test (`both_raw_streams_are_bounded_at_exact_edges`, `pipe_open_after_exit`) in code the migration does not touch; the battery was rerun in full into a second directory rather than crediting the first run. Both runs are kept.
- **Plan removal.** The plan said to link the cutover record from the plan only; the plan was deleted after execution at the maintainer's request, so the record has no inbound link.

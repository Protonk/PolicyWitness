# Apple Silicon output target acceptance

Acceptance record for [APPLE-SILICON-PLAN.md](../APPLE-SILICON-PLAN.md),
executed 2026-10-18 and 2026-10-19. The plan restricts what the build
delivers: every executable is a thin `arm64` Mach-O for macOS. This record
keeps the conclusions, the commits, the decisions taken during execution, the
findings, the runs credited and what remains untested; the product
documentation describes the resulting behavior and does not link here.

Run evidence under `tests/out/runs/` is gitignored and available only in the
local checkout; the credited directories are protected through
[tests/RETAINED.json](../tests/RETAINED.json). Shakedown runs of the opt-in
controls under the session scratchpad and `/private/tmp` were diagnostic,
are not credited and are described, not linked.

## Conclusions

Review subsequently found two gaps in the checks, described under
[Review repairs](#review-repairs). The candidate and runs below remain the
original evidence; they do not establish acceptance of those repairs.

The output target is enforced where the plan asked, and every claim below
rests on a credited run of the final source, `9c6ee31`:

- Target selection. Cargo is given `--target aarch64-apple-darwin`; the
  controller package's build script refuses any other `TARGET`.
  `meson.build` asserts an arm64 macOS host machine on setup and
  regeneration, leaves the build machine unconstrained, and passes
  `-arch arm64` to every C compile and link and `arm64-apple-macosx26.0` as
  the Swift target.
- Output gates. `tests/lib/output_target.py` observes container (header),
  architecture names (`lipo -archs`) and platform (load commands) and decides
  separately. `build.sh` runs it after Cargo, after the native compile and
  before the worker is run, across the assembled bundle by header before the
  first signature, at the standalone observer's signing and before the ZIP.
- Caches. Fresh mode replaces `builddir/` and both Cargo release areas
  (`controller/target/release/` for host units,
  `controller/target/aarch64-apple-darwin/release/` for the shipped
  executables). The toolchain stamp (schema 2) records the configured output
  target from Meson's introspection and refuses another target, or a stamp
  from before the contract, before any compile.
- Artifacts. The inspector checks every required executable regardless of
  the manifest and every other Mach-O found by header, excluding dSYM
  companions. The provenance record (schema 2) carries the fixed output
  target, Meson's host and build machines and each output's architectures and
  container; the inspector and the archive reader compare them with the
  bytes, and archived schema 1 records are read only as schema 1.

The fresh signed candidate built from `9c6ee31` passes inspection and the
default battery (194 of 194), and the four opt-in build controls pass
against that source: the signed artifact controls (28 scenarios), the build
guard controls (21 builds), the toolchain switch, and the refusal controls
(83 controls across both variants and the sequences, and 13 mutation
demonstrations, each failing its control).

Native-build enforcement is not implemented, as the plan directs: nothing
observes or refuses the machine or process that runs the build.

## Implementation commits

| Commit | Content |
| --- | --- |
| `cbefbc1aa3c2162dcd66d1dfe9cd9518690bf8dd` | The output target check and its Mach-O fixture controls (step 1, completed before integration). |
| `e04ec9614648f670333554c970f904a42eafbcab` | Target selection, the five build gates, stamp and record schema 2, the inspector, the generator's output-target Meson row, and their controls. |
| `60b16a3c5b1d76f01c5fee479d16551477c9905f` | Documentation, the build guard faults and the refusal-control adjustments found in shakedown. |
| `06cb69d2edb0f0713aaae37740f94daf63f75e1b` | Replacements in the refusal controls carry the current time; comments no longer claim Cargo hard-links its outputs. |
| `9c6ee314d2081511e1eb7ec1e4277d8e438be967` | The stamp compares the Swift target only while the directory is configured with the XPC pieces; the fresh-mode sequence expects the Swift target in an extended stamp; mutation case directories are named per mutation. |

The candidate's worker identity is
`92ac66e53859d0133fd30ee0203b094d355188b334ac0192f05f75a78f7787a2`; no
identity input changed after `e04ec96`. The follow-on plan,
[NATIVE-BUILD-PLAN.md](../NATIVE-BUILD-PLAN.md), was committed separately as
`c876227` and changes nothing here.

## Equipment

macOS 26.7.1 (25G241), Darwin 25.6.0, arm64, native
(`sysctl.proc_translated` 0 for the build shell); Xcode 27.1 (27A9275),
Apple clang 21.0.0 (clang-2100.3.34.2), Swift 6.4, ld 27037.1, macOS SDK
27.0; rustc and cargo 1.99.0 from the `stable-aarch64-apple-darwin`
toolchain, the only Rust toolchain and target installed; Meson 1.12.1, Ninja
1.13.2; Rosetta present (`arch -x86_64` runs, translation reported as 1);
signing with Developer ID Application: Adam Hyland (42D369QV8E).

## Decisions taken during execution

- No x86_64 Rust target or toolchain was installed (the user's decision).
  The package guard is therefore shown with
  `cargo build --keep-going --target <triple>` for `x86_64-apple-darwin`
  and `aarch64-apple-ios`: the build script runs on the host and its
  message appears, while the standard library each target lacks fails its
  units as well. This establishes that the guard fires on `TARGET`, not that
  it alone stops a target whose library is installed; the guard removed or
  weakened to an `aarch64` prefix or an `apple-darwin` suffix fails the
  control. Flag attribution with a compiler host that differs from the output
  triple is covered by constructed inputs only.
- The x86_64 fixtures come from `xcrun clang`, which still links x86_64
  against SDK 27.0; the platform mismatch is an arm64 Mac Catalyst executable
  (platform 6), which the macOS SDK links.
- Historical records: bumping the record to schema 2 would have stopped
  archive verification of `dist/archive/v0.3.1`, whose record is schema 1.
  `read_zip_record` accepts schema 1 only when the caller asks for historical
  records, which only archive verification does; v0.3.1 verifies and the
  current-schema reader refuses it.
- Meson's output-target assertion is a new refusal row (`meson_target`,
  `requires_host`), modelled by the generator beside the fixed-policy family.
  Two further rows are new: `output_target_mismatch` (status 1, five steps)
  and `builddir_target_mismatch` (status 1). The manifest has 54 refusals and
  an empty baseline.
- Arm64 cross builds: Meson 1.12.1 sets up no Swift target in any cross
  configuration (an internal error naming a missing `swift_COMPILER` rule,
  reproduced with a two-file Swift project). After discussing with the user
  that builds happen on Apple Silicon in practice, the refusal control's
  arm64 cross build runs in the partial variant only and the documentation
  names the limitation; the `source_drift` control builds an arm64 cross
  configuration of the C targets.

## Findings

- Before this work, a thin x86_64 or arm64e output with the right minimum and
  SDK passed every build gate and the inspector; a universal file was refused
  only incidentally, because the SDK check's load-command reader found two
  `LC_BUILD_VERSION` commands; a one-slice fat container of arm64 passed
  everything. The `file -b | grep Mach-O` signing guard and the minimum
  check's first-`minos` read accept a universal file.
- In this checkout, the first incremental build after the change refused the
  existing schema 1 stamp before compiling, naming the fresh remedy; the fresh
  build replaced both release areas and published a schema 2 stamp.
- Cargo here copies each shipped output from its cached unit rather than
  linking it (the fingerprint binding reads "identical bytes", in the v0.3.1
  record as in the candidate's) and copies it again on every build, so a
  replaced output alone is restored by the next build. The reuse control
  therefore replaces the cached unit as well, as a corrupted cache would.
- The new controls replace files with a `replace` action (a new file renamed
  into place). During execution I switched the replaced-cached-output control
  to it on the belief that Cargo hard-linked outputs to their units; the
  v0.3.1 record shows Cargo copied them, so that control's original `copy`
  was sound and the switch changes nothing it establishes. The comments that
  stated the hard-link rationale were corrected in `06cb69d`.
- The linker signs only arm64 output ad hoc; the fixture builder signs its
  x86_64 and universal stand-ins ad hoc so the fixture record's signature
  facts hold. An unsigned stand-in first produced a `provenance_signature`
  fault beside the intended ones (run `apple-silicon-offline-2`).
- The refusal controls' fresh-mode sequence found a defect in this work's
  stamp check: after a partial build, Meson's introspection lists no Swift
  target, and a full build reusing the directory was refused because the
  stamp, scoped for the XPC pieces, records one (`apple-silicon-optin-2`).
  The check now compares the Swift target only while the directory is
  configured with the XPC pieces, and stamp-extend compares it after the
  compile; a provenance control reproduces the state.
- Three mutations guard one refusal, and their case directories collided in
  the mutation phase until each was named by its mutation.
- With the Meson output-target assertion removed, the x86_64 host
  configuration is no longer refused by it; in the full variant Meson then
  stops on its own Swift cross limitation (status 2), and the control fails
  either way. The `source_drift` control shows the x86_64 setup succeeding
  for the C targets.
- Disposable-checkout file lists in two drift controls and the dispatcher
  fixture installer omitted the new helper; `apple-silicon-offline-1` failed
  on them and on a hard-coded figure edge, before the fix.

## Credited runs

| Run | Run ID | Source | Result |
| --- | --- | --- | --- |
| `tests/out/runs/apple-silicon-default-2` | `20261019T020917Z_c7d77733` | `9c6ee31` | Default battery against the fresh candidate: 194 selected, 194 completed, no skips, unrun cases or harness errors; artifact unchanged. |
| `tests/out/runs/apple-silicon-optin-3` | `20261019T022139Z_78df238e` | `9c6ee31` | `signed_artifact_controls` (28 scenarios), `build_guard_controls` (21 builds), `build_toolchain_switch_controls` and `build_refusal_controls` (83 controls and 13 mutation demonstrations) all pass. |

The candidate (`dist/PolicyWitness.app`, `v0.3.1-50-g9c6ee31`, built with
`PW_FRESH_BUILD=1` from a clean tree): ZIP sha256
`43233168a2d1c5b37781ca1b6753dffe69ab060d4bd775f5d60b266625a72731`,
embedded record sha256
`9e7b74c9b7994919aefd0356058a20d973ece5d912d7f718d1da70a020fa89f5`,
controller sha256
`f38a5fc11f51eebf6c7f390a9667f570e465678793d6cbd91a68aa058be105d2`.
Every executable is thin arm64 by `lipo -archs` and by the inspector. The
Mac did not sleep during either run.

Earlier runs, kept as the record of what they found and not credited:

| Run | Run ID | Source | Result |
| --- | --- | --- | --- |
| `tests/out/runs/apple-silicon-optin-1` | `20261019T005102Z_16cbbd3d` | `60b16a3` | The signed artifact, build guard and toolchain switch controls passed. The refusal controls passed every full-variant control and failed in the partial variant: the reuse case of `control_output_target_mismatch` built successfully, because the replacement unit carried its source's older modification time and Cargo compiled the unit again. Fixed in `06cb69d`. |
| `tests/out/runs/apple-silicon-optin-2` | `20261019T011524Z_b18843a7` | `06cb69d` | The toolchain switch passed; the refusal controls passed all 72 variant controls, including the case fixed above, and failed in the fresh-mode sequence on the stamp defect described under the findings. Fixed in `9c6ee31`. |

`apple-silicon-default-1` (`20261019T003636Z_2d9099aa`, the default battery
against the `60b16a3` candidate, 194 of 194) passed and is superseded by
`apple-silicon-default-2`. Runs on intermediate sources
(`apple-silicon-offline-1` to `-3`, `apple-silicon-drift-docs-1`) found the
copy-list, figure-edge and unsigned-stand-in faults above and are superseded
by the default battery; they are not retained. Shakedown runs of the opt-in
controls through their development entry, under the session scratchpad,
found the remaining control faults before each credited run.

## The plan's verification table

| Control | Evidence |
| --- | --- |
| Arm64 success | Fresh full and partial builds pass with every output gate recorded (`passing` in the refusal controls checks every stage, the record and `lipo`); inspection off in the fresh-mode sequence; the candidate passes inspection and the default battery. |
| Cargo selection | `control_cargo_selection_sequence`: an x86_64 default from `CARGO_BUILD_TARGET` and `build.target` is overridden and recorded, nothing rebuilt; target rules apply for the output triple and not for another. `control_cargo_package_target_guard` for direct x86_64 and iOS builds. Differing compiler host: constructed inputs only. |
| Meson selection | `control_meson_target` (x86_64 host refused at setup; arm64 cross build packages, partial variant); `test_meson_output_target_assertion_refuses_other_hosts` (setup refusal, arm64 cross outputs, regeneration refusal, removed assertion). Partial builds avoid Swift discovery as before. |
| Cache transition | `control_builddir_target_mismatch` (a stamp naming another target and a schema 1 stamp refused before compiling; fresh recovery keeps other profiles and triples; reuse checks every cached executable); the checkout's own schema 1 stamp refused before the fresh build. |
| Artifact substitution | `control_output_target_mismatch` (x86_64, truncated, universal, one-slice fat, unlisted and arm64e substitutes at the five boundaries; a corrupted cached unit refused again on reuse); `test_build_guards` (x86_64 and universal substitutes with correct minimum and SDK). |
| Inspector independence | `signed_artifact_controls` (validly signed x86_64 helper and universal library with consistent hashes) and `dispatcher/artifact_controls` (fake-seal fixtures): each fails for architecture, a contradicting record a separate fault. |
| Guard sensitivity | Refusal mutations: Cargo output check removed, assembled check moved past the first signature, predicate reduced to arm64 membership, Meson assertion removed; the predicate weakenings in `build_provenance_controls`; the package guard weakenings. The output target controls assert that the minimum, SDK and identity checks make none of their refusals, and the build guard's minimum and SDK faults assert that the output check makes none of its own. |
| Builder distinction | `control_translated_builder`: with Rosetta present (`sysctl.proc_translated` read as 1 under `arch -x86_64`), the unchanged script run by a translated shell built, signed and packaged arm64 outputs, every output gate recorded. Its Cargo and Meson have no x86_64 slice and ran natively; a translated Meson was not available. |

## Untested and outside this work

- Builder compatibility was observed on one native arm64 machine and under a
  translated shell whose Cargo and Meson ran natively. A translated Meson was
  not available (Meson 1.12.1 needs Python 3.10; the only x86_64-capable
  Python here is 3.9.6), and no Intel builder was available. The build runs
  the built worker for its identity, so a builder that cannot execute arm64
  code cannot complete the signed pipeline; no end-to-end Intel-hosted build
  is claimed.
- Meson's introspection lists no link arguments for Swift targets; the stamp
  records the Swift target from the compile arguments.
- Native-build enforcement, runtime checks and external-runner admission are
  unchanged.

## Review repairs

Commit `c84e2de` repairs two gaps reproduced during review:

- The assembled and packaging checks discovered code only by its header, so
  they skipped a required executable replaced with text or truncated before
  its magic was recognizable. Both now check the variant's required paths
  alongside the scan for additional code. Controls cover every required path
  in both variants, with text, empty, two-byte and missing files; the build
  refusal controls inject these faults before the first signature and after
  signature verification, before the ZIP.
- The scan excluded only thin dSYM files. It now excludes fat dSYM containers
  only when every bounded, nonoverlapping slice has a complete `MH_DSYM`
  header matching its table entry. Real universal, one-slice fat and fat64
  debug fixtures pass; mixed code/debug and malformed containers remain
  subject to rejection. The signed artifact control adds a universal dSYM
  resource to a re-signed app and requires inspection to pass.

`tests/out/runs/apple-silicon-repair-offline-1`
(`20261019T040908Z_3b0d9ae0`) passed all three selected cases:
`preflight/build_provenance_controls` (45 tests),
`source_drift/build_documentation` and `dispatcher/artifact_controls`.
It ran the working tree later committed as `c84e2de`, except for a subsequent
docstring-only clarification in `output_target.header`. Reusing this result
for the repair is a reviewed applicability judgment: that wording changes no
executed behavior. The retention entry leaves `source` null rather than
claiming that this was a clean committed run. Build-generation and
worker-identity checks also passed; no worker-identity input changed.

Integrated acceptance of the repairs is pending. The fresh signed build was
requested twice, but automatic approval review failed with "Selected model
is at capacity" before either command executed. This was an approval-service
failure, not a build failure or an unsafe-action finding. The existing
`9c6ee31` candidate was not replaced. Resume with a fresh signed build, the
default battery, and the `signed_artifact_controls`, `build_guard_controls`
and `build_refusal_controls` opt-ins; record the new candidate and run IDs
before crediting the repairs as fully accepted.

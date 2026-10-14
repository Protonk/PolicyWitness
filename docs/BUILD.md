# The build

This document is the account of one build in time: what each step reads,
writes and refuses; the two knobs and what each governs; what `meson.build`
owns and what `build.sh` owns; the trust placed in the build directories; the
signing contract; the evidence the build embeds; and how the build verifies
itself. The release ships the [user guide](PolicyWitness.md), which states
the supported macOS;
[CONTRACT.md](CONTRACT.md#internal-hostworker-identity) keeps the identity's
definition, and [SIGNING.md](SIGNING.md) keeps evidence, notarization,
release and the archives.

## Why the build is shaped this way

Three ideas shape the script. The app is a coherent signed specimen: one
bundle, assembled from compilers the script drives itself, signed from the
inside out with one explicitly named identity, and carrying a manifest of the
bytes that were signed. The host and the worker share an exact source identity
([`generate_worker_identity.py`](generate_worker_identity.py)), checked before
compiling and again before signing, so the pair that ships carries the
identity of the sources in the tree; that the binaries were compiled from
those sources rests on the build directories' own records, as the last section
says. And every refusal precedes the step it protects: the documentation and
identity checks run before any compile, each compile is followed by its own
checks before anything is copied, every bundle copy precedes every signature, and the
signatures precede the ZIP. A refusal before assembly leaves the previous
distribution outputs untouched, though the build directories change as the
compiles run; a refusal between assembly and the seal leaves an unsealed
partial app and no ZIP; a refusal after the seal leaves a sealed app that
failed verification, the signer check, the observer's signature or packaging,
and no ZIP or a partial one. The test inspector checks the app's signatures,
its inventory and evidence, including signer consistency for the listed
executables ([`inspect`](../tests/lib/artifact.py)). A failure signing the
standalone observer, staging the guide or writing the ZIP can leave an app
that passes inspection.

The build preserves tracked files: a stale generated copy is refused with the
command that regenerates it, so a clean checkout builds with a clean stamp.
Its writes go to the two build directories, to the standalone observer's
signature inside Cargo's, and to the
output directory, which defaults to the ignored `dist/` but can be placed
elsewhere with `DIST_DIR`. The build is a function of the checkout, its two
build directories and the [inputs beyond the tree](#inputs-beyond-the-tree).
It relies on the tools' records to decide whether cached outputs are current,
and refuses a Meson build directory that belongs to another checkout.

`make build` is the documented entry and the first row of the step table. It
calls `build.sh`: the release targets reach the same row through
`$(MAKE) build`, and a direct `./build.sh` skips the Makefile's guard and
meets the script's own.

## One build in time

What the order establishes. The documentation and identity checks precede
every compile, each compile's own checks follow it and precede any copy, the
copies precede every signature, and the signatures precede the ZIP, as the
table shows and the rule compares. The refusals table distinguishes this
textual check from controls that drive the build and observe it stopping.

The partial build. With `BUILD_XPC=0` the script still runs Cargo, builds and
minimum-checks the C executables, checks the signing identity, and signs
and packages a bundle without the client, the service or the embedded helpers;
the `skip_xpc` row stands in for the embed and service-signing rows it skips.
That bundle passes evidence generation and the seal, fails the full inspector,
and cannot run a specimen, because its evidence manifest names no runner.
Use it only for iteration; the script still writes its ZIP under the release name.

Packaging. After the signer check and the standalone observer, the script
stages the checked user guide beside the app and writes the ZIP for
notarization; the staging command checks the guide's sources again before it
writes. A test compares the staged copy itself.

<!-- BEGIN GENERATED BUILD FIGURE -->
![One build in time](build-steps.svg)

*Figure: one build in time, step by step. Generated from [build.json](build.json) by [generate_build.py](generate_build.py); dot source in [build-steps.dot](build-steps.dot). The ids in the figure are the ids in the step table; a blue node and a blue edge belong only to a full build, a dashed node or edge only to a partial build, and the two paths rejoin where both variants run. Symbol presence and test definition are verified, and the banner order, the refusal messages with the script's own statuses and steps, knob values, signing calls with their flags, helper and tool invocations with their listed flags, and the signing inventory are compared with the script by the build_documentation case; whether a test asserts the row, or a refusal fires before the operation it protects, is not verified.*
<!-- END GENERATED BUILD FIGURE -->

<!-- BEGIN GENERATED BUILD STEPS -->
<details>
<summary>30 steps in order, with symbol presence and test definition verified and the banner order compared with the script; whether a test asserts the row is not verified</summary>

| Id | Banner | Variants | Reads | Writes | Refusals | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| make_build | Makefile: [build] build, sign and embed evidence into $(DIST_DIR)/PolicyWitness.app | both | IDENTITY and DIST_DIR from the make command line | nothing; runs build.sh with them | make_identity_unset | [`[build] build, sign and embed evidence into $(DIST_DIR)/PolicyWitness.app`](../Makefile) | [`check_makefile_entry`](../tests/suites/source_drift/build_rules.py); [`test_make_build_refuses_without_an_identity_and_never_runs_the_script`](../tests/suites/source_drift/contract.py) |
| admission | (none) | both | BUILD_XPC, PW_INSPECTION and the argument list; --help prints the usage and exits before any check, after the knobs are validated | nothing | knob_value, unknown_argument | [`must be 0 or 1`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check`](../tests/suites/source_drift/contract.py); [`test_build_refuses_an_unknown_argument_before_any_check`](../tests/suites/source_drift/contract.py) |
| check_limits | Checking limits documentation | both | docs/limits.json and the documents it renders | nothing | stale_limits | [`Checking limits documentation`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| check_contract | Checking contract versions | both | docs/contract.json, docs/architecture.json and their generated copies | nothing | stale_contract, stale_architecture | [`Checking contract versions`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| check_build_doc | Checking build documentation | both | docs/build.json, build.sh, meson.build, the Makefile, the inventories, the baseline and the generated copies | nothing | stale_build_doc | [`Checking build documentation`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| check_identity | Checking host/worker identity | both | the identity inputs and the three generated copies | nothing | stale_identity | [`Checking host/worker identity`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| stamp | Build stamp: ${PW_VERSION} (${PW_BUILD_NUMBER}) ${PW_BUILD_DESCRIBE} | both | git describe, rev-parse and rev-list, or PW_VERSION and PW_BUILD_NUMBER from the environment | the four stamp variables for Cargo and the plists | none | [`Build stamp: ${PW_VERSION} (${PW_BUILD_NUMBER}) ${PW_BUILD_DESCRIBE}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| minimum | Supported macOS (Info.plist LSMinimumSystemVersion): ${PW_MINIMUM_MACOS} | both | LSMinimumSystemVersion in Info.plist | MACOSX_DEPLOYMENT_TARGET for Cargo | plist_minimum_malformed | [`Supported macOS (Info.plist LSMinimumSystemVersion): ${PW_MINIMUM_MACOS}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| sdk | Selecting the macOS SDK (xcrun --sdk macosx) | both | the SDK path xcrun reports under DEVELOPER_DIR | SDKROOT for Cargo and Meson | sdk_unavailable | [`Selecting the macOS SDK (xcrun --sdk macosx)`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| builddir | Checking the native build directory: ${MESON_BUILD_DIR} | both | builddir/meson-info/meson-info.json when the directory is configured | nothing | builddir_unreadable, builddir_other_checkout | [`Checking the native build directory: ${MESON_BUILD_DIR}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| identity | Checking the signing identity | both | IDENTITY and the keychain listing; the two knobs, for Meson's options and RUSTFLAGS | RUSTFLAGS, when inspection is on and it was unset or empty | identity_unset, identity_class, identity_absent | [`Checking the signing identity`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| cargo | Building Rust controller + tools | both | cargo on PATH with its configuration, caches and registries; controller/ sources, the stamp variables, MACOSX_DEPLOYMENT_TARGET, SDKROOT and RUSTFLAGS; the artifact paths Cargo reports | controller/target/release/ under the pinned output directory, and the messages file Cargo reports its artifacts in | missing_controller, missing_observer, missing_sbpl_check, cargo_artifact_elsewhere, minimum_mismatch, cargo_failed | [`Building Rust controller + tools`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| toolchain | Checking the native toolchain (meson, ninja ${NINJA_MINIMUM} or newer) | both | meson and ninja on PATH and ninja's version | nothing | meson_ninja_missing, ninja_old | [`Checking the native toolchain (meson, ninja ${NINJA_MINIMUM} or newer)`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| configure | Configuring native build (meson configure, existing directory): ${MESON_OPTIONS[*]} / Configuring native build (meson setup, fresh directory): ${MESON_BUILD_DIR} ${MESON_OPTIONS[*]} | both | whether builddir/build.ninja exists, meson.build, meson.options and the two knobs as Meson options; a fresh setup also reads CFLAGS and the other flag variables | builddir/ configuration; meson configure records the two options and the policy assertions run at setup or at the regeneration the next compile triggers | meson_optimization, meson_debug, meson_warning_level, meson_werror, meson_strip, meson_unity, meson_b_ndebug, meson_b_lto, meson_b_coverage, meson_b_pgo, meson_b_bitcode, meson_b_pie, meson_b_staticpic, meson_b_lundef, meson_b_sanitize, meson_c_std, meson_c_args, meson_c_link_args, meson_buildtype, meson_swift_args, meson_swift_link_args, meson_failed | [`Configuring native build (meson configure, existing directory): ${MESON_OPTIONS[*]}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| compile | Compiling native executables | both | the native sources through builddir/; a changed option triggers regeneration, which runs the policy assertions first | builddir/ outputs and the Swift module cache under it | meson_optimization, meson_debug, meson_warning_level, meson_werror, meson_strip, meson_unity, meson_b_ndebug, meson_b_lto, meson_b_coverage, meson_b_pgo, meson_b_bitcode, meson_b_pie, meson_b_staticpic, meson_b_lundef, meson_b_sanitize, meson_c_std, meson_c_args, meson_c_link_args, meson_buildtype, meson_swift_args, meson_swift_link_args, meson_failed | [`Compiling native executables`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| native_check | Checking the configured native source lists and the identity closure against the tree | both | Meson's introspection of builddir/, Ninja's dependency log, the identity inputs and the Meson outputs' load commands | nothing | minimum_mismatch, missing_native_output, native_sources_differ, native_sources_unreadable | [`Checking the configured native source lists and the identity closure against the tree`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| assemble | Assembling app bundle: ${APP_BUNDLE} | both | Info.plist, the three Rust outputs, runner/augments/, dist/README.md and dist/AGENTS.md | the two documents under DIST_DIR; removes the previous app, ZIP and guide; the stamped Info.plist, the three Rust executables and the augments under the new app | missing_info_plist, missing_augments_dir | [`Assembling app bundle: ${APP_BUNDLE}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| embed_client | Embedding PW runner client | full | builddir/pw-runner-client | Contents/MacOS/pw-runner-client and its dSYM in inspection builds | missing_client_output | [`Embedding PW runner client`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| embed_services | Embedding PWRunner XPC services | full | each service's Info.plist and builddir/ host, the worker, validator and issuer | each service bundle: its stamped Info.plist, the host with its dSYM in inspection builds, the worker, validator and issuer | missing_service_dir, missing_service_plist, missing_host_output | [`Embedding PWRunner XPC services`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| skip_xpc | Skipping embedded XPC build (BUILD_XPC=0) | partial | nothing | nothing | none | [`Skipping embedded XPC build (BUILD_XPC=0)`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| presign | Checking host/worker identity again, before signing | both | the identity inputs and copies, and whether PolicyWitness.entitlements exists | nothing | missing_entitlements, stale_identity_presign | [`Checking host/worker identity again, before signing`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| sign_tools | Codesigning embedded MacOS tools | both | the copied top-level helpers | signatures on the top-level helpers | sign_target_missing, sign_target_not_macho, codesign_failed | [`Codesigning embedded MacOS tools`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| sign_services | Codesigning embedded XPC services | full | each service's Entitlements.plist and bundle | signatures on the nested helpers, then each service seal | sign_target_missing, sign_target_not_macho, missing_service_bundle, missing_service_entitlements, codesign_failed | [`Codesigning embedded XPC services`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| evidence | Writing evidence manifest (signed BOM) | both | the signed bytes, entitlements and exported symbols of the helpers, services and augments | Contents/Resources/Evidence/manifest.json and symbols.json | evidence_failed | [`Writing evidence manifest (signed BOM)`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| seal | Codesigning app bundle | both | PolicyWitness.entitlements | the app seal over everything under Contents/ | codesign_failed | [`Codesigning app bundle`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| verify | Verifying signature + entitlements | both | the sealed app | nothing | verify_failed | [`Verifying signature + entitlements`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| signer | Checking every executable's signer | both | every regular file under the app's and each service's Contents/MacOS | nothing | signer_mismatch | [`Checking every executable's signer`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| sign_observer | Codesigning observer tool (not embedded) | both | controller/target/release/sandbox-log-observer | that executable's signature, in place | sign_target_missing, sign_target_not_macho, codesign_failed | [`Codesigning observer tool (not embedded)`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| guide | Staging checked user guide | both | docs/PolicyWitness.md and its inputs | PolicyWitness.md under DIST_DIR | stale_guide | [`Staging checked user guide`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| zip | Creating zip (for notarization): ${ZIP_NAME} | both | the sealed app | PolicyWitness.zip under DIST_DIR | none | [`Creating zip (for notarization): ${ZIP_NAME}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |

</details>
<!-- END GENERATED BUILD STEPS -->

How to read the table. A step is a banner the script prints; the rows are in
script order, and the generator refuses a manifest whose banners are not the
script's, in that order, under the same `BUILD_XPC` branches
([`check_banner_order`](../tests/suites/source_drift/build_rules.py)). The
first row is the Makefile's `build` target; the second, `admission`, has no
banner and holds the refusals that fire before any banner prints. A refusal
belongs to the banner that precedes it in the script, and a refusal inside a
function belongs to every step that calls the function; the script is arranged
so that every refusal follows the banner of the step it protects, which is
what makes that rule honest. Variants are `full` (`BUILD_XPC=1`) and `partial`
(`BUILD_XPC=0`); a row marked `both` runs in either. `--help` prints the usage
and exits before any check, once the knobs are validated. The script prints
a warning and continues when the augments directory holds no augment.
The tables cover refusals; their Reads and Writes columns are manually
maintained descriptions of each step.

## Inputs beyond the tree

The build depends on these inputs and working state, in the order it meets them.

- **The git stamp.** `git describe`, `rev-parse` and `rev-list` give the
  version, the commit count, the describe string and the commit
  ([`PW_BUILD_DESCRIBE`](../build.sh)). `PW_VERSION` and `PW_BUILD_NUMBER`
  override the first two for builds outside a checkout; the other two always
  come from git or read `unknown`. The same four values reach the controller
  through Cargo ([build.rs](../controller/build.rs)) and both plists
  ([`stamp_info_plist`](../build.sh)).
- **The supported macOS.** [`LSMinimumSystemVersion`](../Info.plist) is the
  one declaration the script enforces: it becomes `MACOSX_DEPLOYMENT_TARGET`
  for Cargo, and every Cargo and Meson executable is checked against it
  before assembly ([`check_minimum_macos`](../build.sh)). `meson.build` pins
  the same value for the native compile and link
  ([`macos_minimum`](../meson.build)); the two agree because a build in which
  they disagree refuses.
- **The SDK and the developer directory.** `xcrun --sdk macosx` selects the
  SDK once, under whatever `DEVELOPER_DIR` names, and the script exports it
  as `SDKROOT` for Cargo and Meson alike; a failed selection refuses before
  the build directory and the signing identity are checked. Which toolchain
  `xcrun` resolves is the operator's choice.
- **The two build directories.** Meson's is checked: a directory whose
  recorded source is another checkout, or whose record cannot be read, is
  refused before Cargo. Cargo's is pinned with `--target-dir`, and Cargo is
  asked to report the executables it produced, so one placed under another
  directory by a target triple or a Cargo setting is refused before any copy.
- **The signing identity.** `IDENTITY` must name a Developer ID Application
  identity that `security find-identity` lists; any other class is refused before
  Cargo. The first signature checks whether the keychain is unlocked.
- **Cargo's environment.** `cargo` is resolved on `PATH` and brings its own
  configuration, caches and registries. The script adds the four stamp
  variables, `MACOSX_DEPLOYMENT_TARGET`, `SDKROOT`, and `RUSTFLAGS` with
  debug info, frame pointers and opt-level 1 when inspection is on and the
  caller left it unset or empty; a caller's `RUSTFLAGS` wins silently. A
  plain `cargo build` outside the script carries none of this; on the
  toolchain this was observed with, it produced executables for an older
  macOS than the plist declares, which the minimum check would refuse.
- **The output directory.** `DIST_DIR`, `dist/` by default; a custom one
  also receives copies of the tracked `dist/` README and AGENTS files. Its
  trust and that of the build directories are in the table.

<!-- BEGIN GENERATED BUILD DIRECTORIES -->
| Directory | Trusted as | Refused when | Sources | Checks |
| --- | --- | --- | --- | --- |
| builddir/ | Meson's configuration and incremental native outputs for this checkout | its recorded source directory is not this checkout, or its meson-info cannot be read | [`MESON_SOURCE_DIR`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`](../tests/suites/source_drift/contract.py) |
| controller/target/ | Cargo's incremental outputs under the pinned --target-dir | Cargo reports an executable at another path than the pinned one; otherwise a stale output is caught only by the minimum-version check and Cargo's own fingerprints | [`CARGO_TARGET_DIR_PINNED`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| dist/ (DIST_DIR) | the output directory; the previous app, ZIP and guide are removed one after another at assembly and nothing is preserved | never; a failure between the removals leaves a mixture, a refusal before the seal leaves an unsealed partial app, and a later failure can leave a sealed app; inspection checks the app, not completion of observer signing, guide staging or ZIP creation | [`rm -f "${ZIP_NAME}" "${GUIDE_NAME}"`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
<!-- END GENERATED BUILD DIRECTORIES -->

To discard incremental build state, remove `builddir/` and
`controller/target/` from the repository root with
`rm -rf builddir controller/target` while no build or test is running; the
next `make build` recreates them. `make prune` manages test output only and
does not remove either cache or the distribution directory.

The build checks that Meson and Ninja are installed and checks Ninja's version.
The operator selects their toolchain. A compiler or SDK change needs a fresh
build directory because the toolchain is not fingerprinted. Signing needs an
unsandboxed shell with the login keychain and network access for the
timestamp service. A release needs a clean checkout at the release commit,
enforced by release preflight.
The harness constraints below apply to signing and compiler discovery.

### Sandboxed automation harnesses

An automation harness's macOS sandbox can block runner XPC lookup
(`NSCocoaErrorDomain` 4099 or error 159), unified-log access
(`log: Cannot run while sandboxed`), signing-keychain access, and Meson's Swift
discovery when swiftc cannot write its module cache. It can also make
`codesign --verify` report an invalid signature for unchanged bytes. Request
escalation and rerun the same failing command once outside the automation
sandbox, without changing the artifact under investigation. Treat a signature
failure as environmental only if the unsandboxed verification passes;
investigate any failure that remains.

This warning is intentionally repeated for agents entering through different
workflows who may mistake harness restrictions for product defects.
[source_drift](../tests/suites/source_drift/README.md#intentional-guidance-agreement)
compares the first paragraph in all four locations; edit those copies together.
The explanations that follow it are local to each document.

Use an unsandboxed shell for signing and Swift discovery. The harness may
block the login keychain or swiftc's default per-user module cache. Meson uses
that cache for discovery before the targets can use `builddir/`; discovery
and identity prerequisites can fail before copying or signing, and signing
itself can fail later. `BUILD_XPC=0` skips Swift discovery.

Manifest-only source checks use introspection without compiler discovery.
The `source_drift/build_documentation` controls also configure Swift to test
its policy assertions, so they need the unsandboxed shell.

## Refusals

<!-- BEGIN GENERATED BUILD REFUSALS -->
<details>
<summary>65 refusals (28 the script's own, 21 Meson assertions, 15 propagated from a check or a tool, 1 in the Makefile), with symbol presence and test definition verified and the messages, statuses and steps compared with the script; every refusal has a control that produces it and the baseline is empty; whether a test asserts the row is not verified</summary>

| Id | Message | Steps | Status | Kind | Variants | Coverage | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| knob_value | ${knob} must be 0 or 1 (got '${!knob}') | admission | 2 | script | both | a control produces it | [`${knob} must be 0 or 1 (got '${!knob}')`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check`](../tests/suites/source_drift/contract.py) |
| unknown_argument | unknown argument: $1 | admission | 2 | script | both | a control produces it | [`unknown argument: $1`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_an_unknown_argument_before_any_check`](../tests/suites/source_drift/contract.py) |
| plist_minimum_malformed | Info.plist LSMinimumSystemVersion is not a major.minor version: '${PW_MINIMUM_MACOS}' | minimum | 2 | script | both | a control produces it | [`Info.plist LSMinimumSystemVersion is not a major.minor version: '${PW_MINIMUM_MACOS}'`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_malformed_plist_minimum_after_its_banner_and_before_the_sdk`](../tests/suites/source_drift/contract.py) |
| sdk_unavailable | xcrun could not select the macOS SDK (DEVELOPER_DIR=${DEVELOPER_DIR:-unset}) | sdk | 2 | script | both | a control produces it | [`xcrun could not select the macOS SDK (DEVELOPER_DIR=${DEVELOPER_DIR:-unset})`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_sdk_unavailable`](../tests/suites/preflight/opt_in/build_refusals.py) |
| builddir_unreadable | ${MESON_BUILD_DIR} has no readable meson-info; remove it or use a fresh build directory | builddir | 2 | script | both | a control produces it | [`${MESON_BUILD_DIR} has no readable meson-info; remove it or use a fresh build directory`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`](../tests/suites/source_drift/contract.py) |
| builddir_other_checkout | ${MESON_BUILD_DIR} is configured for ${MESON_SOURCE_DIR}, not this checkout (${ROOT_DIR}); remove it or use a fresh build directory | builddir | 2 | script | both | a control produces it | [`${MESON_BUILD_DIR} is configured for ${MESON_SOURCE_DIR}, not this checkout (${ROOT_DIR}); remove it or use a fresh build directory`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`](../tests/suites/source_drift/contract.py) |
| identity_unset | IDENTITY is not set. | identity | 2 | script | both | a control produces it | [`IDENTITY is not set.`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`](../tests/suites/source_drift/contract.py) |
| identity_class | IDENTITY must name a Developer ID Application identity; got: | identity | 2 | script | both | a control produces it | [`IDENTITY must name a Developer ID Application identity; got:`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_non_developer_id_identity_before_cargo`](../tests/suites/source_drift/contract.py) |
| identity_absent | codesigning identity not found in your keychain: | identity | 2 | script | both | a control produces it | [`codesigning identity not found in your keychain:`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_developer_id_identity_the_keychain_lacks_before_cargo`](../tests/suites/source_drift/contract.py) |
| missing_controller | expected policy-witness binary at ${RUNNER_BIN} | cargo | 2 | script | both | a control produces it | [`expected policy-witness binary at ${RUNNER_BIN}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_controller`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_observer | expected sandbox-log-observer binary at ${SANDBOX_LOG_OBSERVER_BIN} | cargo | 2 | script | both | a control produces it | [`expected sandbox-log-observer binary at ${SANDBOX_LOG_OBSERVER_BIN}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_observer`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_sbpl_check | expected sbpl-check binary at ${SBPL_CHECK_BIN} | cargo | 2 | script | both | a control produces it | [`expected sbpl-check binary at ${SBPL_CHECK_BIN}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_sbpl_check`](../tests/suites/preflight/opt_in/build_refusals.py) |
| cargo_artifact_elsewhere | cargo built ${bin_name} at ${bin_path}, not at ${bin_expected}; a target triple or a Cargo setting moved it | cargo | 2 | script | both | a control produces it | [`cargo built ${bin_name} at ${bin_path}, not at ${bin_expected}; a target triple or a Cargo setting moved it`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_cargo_artifact_elsewhere`](../tests/suites/preflight/opt_in/build_refusals.py) |
| minimum_mismatch | ${target} is built for macOS ${minos:-?}; Info.plist declares ${PW_MINIMUM_MACOS} | cargo, native_check | 2 | script | both | a control produces it | [`${target} is built for macOS ${minos:-?}; Info.plist declares ${PW_MINIMUM_MACOS}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_guards`](../tests/suites/preflight/opt_in/build_guards.py) |
| meson_ninja_missing | meson and ninja are required for the native build (brew install meson ninja); see docs/SIGNING.md | toolchain | 2 | script | both | a control produces it | [`meson and ninja are required for the native build (brew install meson ninja); see docs/SIGNING.md`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_meson_ninja_missing`](../tests/suites/preflight/opt_in/build_refusals.py) |
| ninja_old | ninja ${NINJA_VERSION} is older than the ${NINJA_MINIMUM} minimum; see docs/SIGNING.md | toolchain | 2 | script | both | a control produces it | [`ninja ${NINJA_VERSION} is older than the ${NINJA_MINIMUM} minimum; see docs/SIGNING.md`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_ninja_old`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_native_output | expected Meson output at ${native_bin} | native_check | 2 | script | both | a control produces it | [`expected Meson output at ${native_bin}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_native_output`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_info_plist | missing ${INFO_PLIST_TEMPLATE} at repo root | assemble | 2 | script | both | a control produces it | [`missing ${INFO_PLIST_TEMPLATE} at repo root`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_info_plist`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_augments_dir | missing augments source dir at ${XPC_AUGMENTS_DIR} | assemble | 2 | script | both | a control produces it | [`missing augments source dir at ${XPC_AUGMENTS_DIR}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_augments_dir`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_client_output | expected Meson output at ${PW_RUNNER_CLIENT_BIN} | embed_client | 2 | script | full | a control produces it | [`expected Meson output at ${PW_RUNNER_CLIENT_BIN}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_client_output`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_service_dir | missing ${svc_name} service dir at ${svc_dir} | embed_services | 2 | script | full | a control produces it | [`missing ${svc_name} service dir at ${svc_dir}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_service_dir`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_service_plist | ${svc_name} service is missing Info.plist | embed_services | 2 | script | full | a control produces it | [`${svc_name} service is missing Info.plist`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_service_plist`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_host_output | expected Meson output at ${svc_host} | embed_services | 2 | script | full | a control produces it | [`expected Meson output at ${svc_host}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_host_output`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_entitlements | missing entitlements plist: ${ENTITLEMENTS_PLIST} | presign | 2 | script | both | a control produces it | [`missing entitlements plist: ${ENTITLEMENTS_PLIST}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_entitlements`](../tests/suites/preflight/opt_in/build_refusals.py) |
| sign_target_missing | expected a Mach-O to sign at ${target} | sign_tools, sign_services, sign_observer | 2 | script | both | a control produces it | [`expected a Mach-O to sign at ${target}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_sign_target_missing`](../tests/suites/preflight/opt_in/build_refusals.py) |
| sign_target_not_macho | ${target} is not a Mach-O; the signing list names only executables | sign_tools, sign_services, sign_observer | 2 | script | both | a control produces it | [`${target} is not a Mach-O; the signing list names only executables`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_sign_target_not_macho`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_service_bundle | expected XPC service bundle at ${svc_bundle} | sign_services | 2 | script | full | a control produces it | [`expected XPC service bundle at ${svc_bundle}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_service_bundle`](../tests/suites/preflight/opt_in/build_refusals.py) |
| missing_service_entitlements | ${svc_name} service is missing Entitlements.plist at ${svc_entitlements} | sign_services | 2 | script | full | a control produces it | [`${svc_name} service is missing Entitlements.plist at ${svc_entitlements}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`control_missing_service_entitlements`](../tests/suites/preflight/opt_in/build_refusals.py) |
| make_identity_unset | set IDENTITY to your Developer ID Application identity | make_build | 2 | make | both | a control produces it | [`set IDENTITY to your Developer ID Application identity`](../Makefile) | [`check_makefile_entry`](../tests/suites/source_drift/build_rules.py); [`test_make_build_refuses_without_an_identity_and_never_runs_the_script`](../tests/suites/source_drift/contract.py) |
| meson_optimization | fixed native policy: optimization must be 'plain' | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'optimization'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_debug | fixed native policy: debug must be false | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'debug'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_warning_level | fixed native policy: warning_level must be '0' | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'warning_level'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_werror | fixed native policy: werror must be false | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'werror'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_strip | fixed native policy: strip must be false | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'strip'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_unity | fixed native policy: unity must be 'off' | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'unity'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_ndebug | fixed native policy: b_ndebug must be 'false' | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_ndebug'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_lto | fixed native policy: b_lto must be false | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_lto'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_coverage | fixed native policy: b_coverage must be false | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_coverage'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_pgo | fixed native policy: b_pgo must be 'off' | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_pgo'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_bitcode | fixed native policy: b_bitcode must be false | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_bitcode'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_pie | fixed native policy: b_pie must be false | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_pie'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_staticpic | fixed native policy: b_staticpic must be true | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_staticpic'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_lundef | fixed native policy: b_lundef must be true | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_lundef'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_b_sanitize | fixed native policy: b_sanitize must be 'none' | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'b_sanitize'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_c_std | fixed native policy: c_std must be 'none' | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'c_std'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_c_args | fixed native policy: c_args must be [] | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'c_args'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_c_link_args | fixed native policy: c_link_args must be [] | configure, compile | 1 | meson | both | a control produces it in the helper, not through the script | [`'c_link_args'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_buildtype | fixed native policy: buildtype must be 'plain' | configure, compile | 1 | meson | both | a control produces it | [`'buildtype'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`control_meson_buildtype`](../tests/suites/preflight/opt_in/build_refusals.py) |
| meson_swift_args | fixed native policy: swift_args must be [] | configure, compile | 1 | meson | full | a control produces it in the helper, not through the script | [`'swift_args'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| meson_swift_link_args | fixed native policy: swift_link_args must be [] | configure, compile | 1 | meson | full | a control produces it in the helper, not through the script | [`'swift_link_args'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py); [`test_meson_policy_assertions_refuse_each_option`](../tests/suites/source_drift/build.py) |
| stale_limits | stale <copy>; run python3 docs/generate_limits.py | check_limits | 1 | propagated | both | a control produces it | [`generate_limits.py`](../build.sh); [`stale`](../docs/generate_limits.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_stale_guide_before_signing_or_creating_output`](../tests/suites/source_drift/limits.py) |
| stale_contract | stale <copy>; run python3 docs/generate_contract.py | check_contract | 1 | propagated | both | a control produces it | [`generate_contract.py`](../build.sh); [`stale`](../docs/generate_contract.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_stale_contract_copy_before_signing_or_creating_output`](../tests/suites/source_drift/contract.py) |
| stale_architecture | architecture documentation is stale | check_contract | 1 | propagated | both | a control produces it | [`generate_architecture.py`](../build.sh); [`architecture documentation is stale`](../docs/generate_architecture.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_checks_every_generator_before_signing`](../tests/suites/source_drift/generators.py); [`test_build_refuses_a_stale_architecture_copy_before_compiling`](../tests/suites/source_drift/contract.py) |
| stale_build_doc | build documentation is stale | check_build_doc | 1 | propagated | both | a control produces it | [`generate_build.py`](../build.sh); [`build documentation is stale`](../docs/generate_build.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_checks_every_generator_before_signing`](../tests/suites/source_drift/generators.py); [`test_build_refuses_a_stale_build_document_copy_before_compiling`](../tests/suites/source_drift/contract.py) |
| stale_identity | stale <copy>; run python3 docs/generate_worker_identity.py | check_identity | 1 | propagated | both | a control produces it | [`generate_worker_identity.py`](../build.sh); [`stale`](../docs/generate_worker_identity.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_stale_identity_copy_before_compiling_and_writes_nothing`](../tests/suites/source_drift/contract.py) |
| stale_identity_presign | stale <copy>; run python3 docs/generate_worker_identity.py | presign | 1 | propagated | both | a control produces it | [`generate_worker_identity.py`](../build.sh); [`stale`](../docs/generate_worker_identity.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`control_stale_identity_presign`](../tests/suites/preflight/opt_in/build_refusals.py) |
| cargo_failed | Cargo's own diagnostic | cargo | 101 | propagated | both | a control produces it | [`cargo build`](../build.sh) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`control_cargo_failed`](../tests/suites/preflight/opt_in/build_refusals.py) |
| meson_failed | Meson's or Ninja's own diagnostic | configure, compile | 1 | propagated | both | a control produces it | [`meson compile`](../build.sh); [`meson setup`](../build.sh) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`control_meson_failed`](../tests/suites/preflight/opt_in/build_refusals.py) |
| native_sources_differ | native source lists differ from the tree | native_check | 1 | propagated | both | a control produces it in the helper, not through the script | [`native_sources.py`](../build.sh); [`native source lists differ from the tree`](../tests/lib/native_sources.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`configured_controls`](../tests/suites/source_drift/check_planner.py) |
| native_sources_unreadable | native sources: meson introspection failed | native_check | 2 | propagated | both | a control produces it | [`native_sources.py`](../build.sh); [`meson introspection failed`](../tests/lib/native_sources.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`control_native_sources_unreadable`](../tests/suites/preflight/opt_in/build_refusals.py) |
| codesign_failed | codesign's own diagnostic | sign_tools, sign_services, seal, sign_observer | 1 | propagated | both | a control produces it | [`codesign --force`](../build.sh) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`control_codesign_failed`](../tests/suites/preflight/opt_in/build_refusals.py) |
| evidence_failed | missing app bundle Contents | evidence | 2 | propagated | both | a control produces it | [`build-evidence.py`](../build.sh); [`missing app bundle Contents`](../tests/build-evidence.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`control_evidence_failed`](../tests/suites/preflight/opt_in/build_refusals.py) |
| verify_failed | codesign's own diagnostic | verify | 1 | propagated | both | a control produces it | [`codesign --verify`](../build.sh) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`control_verify_failed`](../tests/suites/preflight/opt_in/build_refusals.py) |
| signer_mismatch | executables not signed by <identity> with the hardened runtime | signer | 1 | propagated | both | a control produces it | [`signer_check.py`](../build.sh); [`executables not signed by`](../tests/lib/signer_check.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`signed_artifact_controls`](../tests/suites/preflight/run.sh); [`test_build_guards`](../tests/suites/preflight/opt_in/build_guards.py) |
| stale_guide | stale PolicyWitness.md | guide | 1 | propagated | both | a control produces it in the helper, not through the script | [`--stage-guide`](../build.sh); [`stale`](../docs/generate_limits.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_check_and_staging_refuse_stale_or_incomplete_documents_without_writing`](../tests/suites/source_drift/limits.py) |

</details>
<!-- END GENERATED BUILD REFUSALS -->

Statuses. The script's own refusals exit 2. A refusal that a check or a tool
produces propagates that tool's status: 1 for a stale generated copy or a
source list that differs from the tree, 2 when a check could not read what it
needed, Cargo's 101, and 1 from Meson, Ninja or codesign. Under `set -e` the
script exits with the failing command's status; the message identifies the
step that refused. The propagated statuses in the table are the tools' documented
ones, verified only where a control asserts them.
The table lists the refusals the script declares, Meson's assertions and the
checks and tools the script names; any other failing command also stops the
build with its own status, a plist key PlistBuddy cannot read, a copy or
removal that fails, `dsymutil`, `ditto`, and those stops have no row.

Coverage. Each row's coverage column says what produces the refusal in a test:
a control that drives the build and observes the message and the operation it
prevented; a control that drives the helper that prints it, establishing the
helper's diagnostic; or only the grounding rule that compares the message with
the script. No row has only a grounding rule:
[the baseline](../tests/fixtures/docs/build_baseline.json) of such rows is
empty, and [release_preflight.py](../tests/lib/release_preflight.py) refuses a
release whose baseline grew or rewrote an entry since the previous release, as
it does for the prose baseline.

The opt-in [`test_build_guards`](../tests/suites/preflight/opt_in/build_guards.py)
control drives the unchanged build script with real compilers and signing
tools in a disposable checkout. In both variants, a tool wrapper substitutes
a wrong-minimum Cargo or native output; the build must name it and exit 2
before assembly, leaving previous distribution bytes intact. Another wrapper
signs a helper ad hoc: deep verification must succeed, then the signer check
must name the helper and exit 1 before observer signing, guide staging or ZIP
creation. Successful sibling builds package both variants.

The opt-in [`test_build_refusals`](../tests/suites/preflight/opt_in/build_refusals.py)
control drives the same unchanged script through every refusal the baseline
used to list, in each variant the refusal applies to. One fault at a time is
arranged beside the guarded boundary: an environment in which xcrun selects no
SDK or finds no Meson, a Cargo output removed or placed under a target triple,
a Ninja reporting an old version, a Meson directory whose buildtype label
departs, a source that does not compile, an input or output removed by a `cp`,
`meson` or `codesign` wrapper right after one named call, a Mach-O truncated as
codesign reaches it, a sealed resource changed after the seal. The wrapper runs
the real tool and records a receipt; the script's own check refuses. Each
control asserts the diagnostic and status, the banners before and after the
refusal, the tool calls that did not happen and the output left behind. Copies
of the script with a guard removed or moved past its operation must fail the
matching control, and a successful build in each variant is the neighbour that
shows the checkout and wrappers build.

## What Meson owns and what the script owns

[meson.build](../meson.build) owns the native compile: source lists, module
names and flags, the supported macOS passed at compile and at link, and the
fixed policy for the targets in the [shipped inventory](../README.md#build-and-bundle).
The C shim is linked into the host. Both
`meson.build` and `meson.options` are host/worker identity inputs. The policy is
an enumerated list of options asserted as effective values
([`fixed_options`](../meson.build)), with two more inside
the Swift branch; every option it names is refused at any other value. These
assertions cover the listed options. The two public knobs are the only
configuration the script passes:

<!-- BEGIN GENERATED BUILD KNOBS -->
| Knob | Values | Unset means | Governs | Sources | Checks |
| --- | --- | --- | --- | --- | --- |
| BUILD_XPC | `1`: build and embed the Swift client, the XPC host and the C shim (Meson xpc=true); `0`: skip them; the C executables still build and nothing Meson-built ships (Meson xpc=false) | 1 | Meson's xpc option, the embed and service-signing steps, and which Meson outputs are minimum-checked and signed | [`BUILD_XPC="${BUILD_XPC-1}"`](../build.sh); [`option('xpc'`](../meson.options) | [`check_knobs`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check`](../tests/suites/source_drift/contract.py) |
| PW_INSPECTION | `1`: Swift -Onone -g with a dSYM beside each Swift executable; RUSTFLAGS with debug info, frame pointers and opt-level 1 when RUSTFLAGS was unset or empty (Meson inspection=true); `0`: Swift -O and no dSYM; RUSTFLAGS untouched (Meson inspection=false) | 1 | Meson's inspection option, RUSTFLAGS and the dSYM step; the C executables are -O2 without debug info in both | [`PW_INSPECTION="${PW_INSPECTION-1}"`](../build.sh); [`option('inspection'`](../meson.options) | [`check_knobs`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check`](../tests/suites/source_drift/contract.py) |
<!-- END GENERATED BUILD KNOBS -->

The script maps the knobs onto Meson's `inspection` and `xpc` options on
every build: `meson setup` for a fresh directory and `meson configure`
afterwards, which records the two values and regenerates only when one
changed. A refused value is recorded too: `meson configure` with any other
option exits 0, and the assertion fires at the next regeneration, which the
compile step triggers before anything compiles, or at setup for a fresh
directory. Meson reads `CFLAGS` and the other flag variables only at setup,
so a fresh directory refuses them the same way. Executables are linked with
`b_asneeded=false` declared per target; Meson's own additions to the compile
and link lines (`-headerpad_max_install_names` and `-fdiagnostics-color`)
are accepted and recorded by the comparison tools.
Compilation and linking are separate steps; the script runs `dsymutil` for
inspection builds. Changing the supported macOS requires changing the plist
and Meson's pinned minimum together. Building for an older macOS this way is
possible but unsupported.

The script owns everything around the compile: the plist's declaration and the
per-output minimum check, the build-directory guard, the configured source and
closure check, Cargo's environment, the dSYM step, assembly, signing, evidence
and packaging. Two of its checks look inside the build directory. Before
Cargo, it refuses a directory whose recorded source directory is not this
checkout ([`MESON_SOURCE_DIR`](../build.sh)), because Meson keeps compiling
the directory it was set up for and every later check would pass against that
other tree. After compiling,
[`native_sources.py`](../tests/lib/native_sources.py) reads the targets Meson
actually evaluated and refuses unless every target's sources are exactly the
files the tree holds for it, reads Ninja's dependency log and refuses, for the
worker and the shim, an include of a repository file outside the identity's
inputs or of a file outside the checkout that is not under the selected SDK or
the developer directory, and repeats the checkout comparison. Both are
membership checks; binary provenance relies on the tools' records, as described
under [Known gaps](#known-gaps).

### Native compile with Meson

To compile the native targets alone, without assembly or signing:

```sh
SDKROOT="$(xcrun --sdk macosx --show-sdk-path)" meson setup builddir -Dinspection=true -Dxpc=true
meson compile -C builddir
```

Use separate build directories for different toolchains, and a fresh directory
or `meson setup --wipe` after changing the compiler or SDK. For example:

```sh
DEVELOPER_DIR=/Library/Developer/CommandLineTools \
SDKROOT="$(DEVELOPER_DIR=/Library/Developer/CommandLineTools xcrun --sdk macosx --show-sdk-path)" \
meson setup builddir-clt
```

`build.sh` uses `builddir/`; a separately named directory is for direct Meson
work. Swift discovery uses swiftc's default module cache, while the targets
use `builddir/swift-module-cache`. The [comparison tools](../tests/README.md#comparing-native-builds)
can record effective commands and output metadata after compilation.

## The signing contract

Identity. `IDENTITY` must name a Developer ID Application identity that the
keychain lists; the script requires it for every signature. The
tests resolve their own identity separately: `PW_BYOXPC_IDENTITY`, then
`IDENTITY`, then a keychain identity whose team matches the app's.

Gates before any signature. The generated identity copies must be current,
checked again after assembly so an identity input edited during the build
without regeneration is refused before signing. The build assumes a stable
checkout throughout execution. Every Cargo and Meson executable carried the
plist's minimum, and the configured source lists and closure matched the tree,
before assembly began.

<!-- BEGIN GENERATED BUILD SIGNING -->
<details>
<summary>9 signing calls in order, with symbol presence and test definition verified and the calls, their targets and entitlements compared with the script and the signed inventory with EXECUTABLES, the evidence generator and the README; whether a test asserts the row is not verified</summary>

| # | Target | Kind | Flags | Entitlements | In the service loop | Step | Variants | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ${APP_BUNDLE}/Contents/MacOS/pw-runner-client | signature | --force --options runtime --timestamp | none | no | sign_tools | full | [`${APP_BUNDLE}/Contents/MacOS/pw-runner-client`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 2 | ${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer | signature | --force --options runtime --timestamp | none | no | sign_tools | both | [`${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 3 | ${APP_BUNDLE}/Contents/MacOS/sbpl-check | signature | --force --options runtime --timestamp | none | no | sign_tools | both | [`${APP_BUNDLE}/Contents/MacOS/sbpl-check`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 4 | ${svc_bundle}/Contents/MacOS/pw-probe-runner | signature | --force --options runtime --timestamp | none | XPC_SERVICE_NAMES | sign_services | full | [`${svc_bundle}/Contents/MacOS/pw-probe-runner`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 5 | ${svc_bundle}/Contents/MacOS/sb_api_validator | signature | --force --options runtime --timestamp | none | XPC_SERVICE_NAMES | sign_services | full | [`${svc_bundle}/Contents/MacOS/sb_api_validator`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 6 | ${svc_bundle}/Contents/MacOS/pw-extension-issuer | signature | --force --options runtime --timestamp | none | XPC_SERVICE_NAMES | sign_services | full | [`${svc_bundle}/Contents/MacOS/pw-extension-issuer`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 7 | ${svc_bundle} | seal | --force --options runtime --timestamp | ${svc_entitlements} | XPC_SERVICE_NAMES | sign_services | full | [`-s "${IDENTITY}" "${svc_bundle}"`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 8 | ${APP_BUNDLE} | seal | --force --options runtime --timestamp | ${ENTITLEMENTS_PLIST} | no | seal | both | [`-s "${IDENTITY}" "${APP_BUNDLE}"`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 9 | ${SANDBOX_LOG_OBSERVER_BIN} | signature | --force --options runtime --timestamp | none | no | sign_observer | both | [`sign_macho "${SANDBOX_LOG_OBSERVER_BIN}"`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |

</details>
<!-- END GENERATED BUILD SIGNING -->

Order. Signing is inside-out, in the table's order, every signature and seal
with `--force --options runtime --timestamp`, so the timestamp service must be
reachable; the evidence manifest is written between the service seal and the
app seal, so the app seal covers it. The dSYM bundles beside the Swift
executables, including their DWARF files, are sealed as resources. The
standalone observer under `controller/target/release` is signed in place for
direct use outside the bundle.

The list and the inventory. [`sign_macho`](../build.sh) refuses a missing or
non-Mach-O target: the list names exactly the executables this build
produced. The grounding rule expands the list, through the service loop, into
bundle paths and requires them, plus the bundle mains the seals sign, to
equal [`EXECUTABLES`](../tests/lib/artifact.py), the helper list in
[build-evidence.py](../tests/build-evidence.py) and the README's inventory
([`check_inventory`](../tests/suites/source_drift/build_rules.py)). Do not
add `--deep` to a signing step; it would sign nested code outside the explicit
inventory.

After the seal. `codesign --verify --deep --strict` checks the bundle seal.
Then [signer_check.py](../tests/lib/signer_check.py) examines every regular
file directly inside the app's `Contents/MacOS` directory and the corresponding
directory in each XPC service, including files absent from the signing list.
Each file must be a Mach-O signed by the named identity with the hardened
runtime. The check reads the leaf authority and the runtime flag; it does not
check the certificate's class or the timestamp.

The linker leaves every compiler output ad hoc-signed, and an ad hoc
executable can pass the seal and deep verification. The build's signer check
refuses it before the ZIP. The test inspector separately refuses a listed
helper whose signer differs from the controller's; a test copy signed ad hoc
throughout stays consistent.

The standalone validator build script,
`controller/tools/sb_api_validator/build.sh`, supports local debugging. It
compiles the validator beside its source and signs the result ad hoc with
`debug.ent`. That git-ignored output is for direct local use.

## The evidence the build embeds

After the nested signatures and before the app seal,
[build-evidence.py](../tests/build-evidence.py) writes the manifest and symbols
files in the [evidence inventory](SIGNING.md#evidence-artifacts): the hash of
every helper and of each service's main executable as signed, with each one's
load-command UUID, entitlements and exported marker symbols as far as the
tools can read them (a tool's failure is recorded in the entry),
the hashes of the shipped augments, and the time of writing. The manifest is
then sealed by the app signature, so it describes signed bytes and is itself
signed. It omits the main executable's hash, which the seal records. The
controller reads it at run time to locate its runner, which is why a partial
bundle refuses to run a specimen.

To record a native build receipt or compare native builds, use the test
equipment described under
[comparing native builds](../tests/README.md#comparing-native-builds).

## How the build verifies itself

The figure and the tables are generated from [build.json](build.json) by
[generate_build.py](generate_build.py), which parses the script and refuses
a manifest that disagrees with it. Every row cites the source symbol that
implements it and the test or rule named by the manifest. Review that test or
rule to assess coverage of the row. The build has
<!-- span build.steps -->30<!-- /span --> steps,
<!-- span build.refusals -->65<!-- /span --> refusals, of which
<!-- span build.covered -->65<!-- /span --> have a control that produces
them, <!-- span build.signing -->9<!-- /span --> signing calls and
<!-- span build.knobs -->2<!-- /span --> knobs.

Before compiling, the script runs every generator's check: limits, contract,
architecture, this document, and the identity
([`check_banner_order`](../tests/suites/source_drift/build_rules.py) for the
order, [`build_checks`](../tests/suites/source_drift/generators.py) for the
set). Each writes nothing and exits 1 on a stale copy. This document's check
also parses the script and refuses a manifest that disagrees with it in what
the parser compares: the banner order, the refusal messages with their steps
and the script's own statuses, the knob values, the signing calls with their
flags, the helper and tool invocations with their listed flags, the signing
inventory, and the `set -euo pipefail` opening. Other conditions and arguments
fall outside this comparison.

The helpers and tools the build invokes, with the step each runs in:

<!-- BEGIN GENERATED BUILD INVOCATIONS -->
<details>
<summary>24 helper and tool invocations, with symbol presence and test definition verified and each command's name, step and listed flags compared with the script; whether a test asserts the row is not verified</summary>

| Id | Command | Flags compared | Step | Variants | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| inv_limits_check | docs/generate_limits.py --check | (not compared) | check_limits | both | [`docs/generate_limits.py" --check`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_contract_check | docs/generate_contract.py --check | (not compared) | check_contract | both | [`docs/generate_contract.py" --check`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_architecture_check | docs/generate_architecture.py --check | (not compared) | check_contract | both | [`docs/generate_architecture.py" --check`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py); [`test_build_checks_every_generator_before_signing`](../tests/suites/source_drift/generators.py) |
| inv_build_check | docs/generate_build.py --check | (not compared) | check_build_doc | both | [`docs/generate_build.py" --check`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py); [`test_build_checks_every_generator_before_signing`](../tests/suites/source_drift/generators.py) |
| inv_identity_check | docs/generate_worker_identity.py --check | (not compared) | check_identity | both | [`docs/generate_worker_identity.py" --check`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_cargo | cargo build | --manifest-path --release --target-dir --message-format --bin --bin --bin | cargo | both | [`cargo build`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_cargo_artifacts | tests/lib/cargo_artifacts.py | (not compared) | cargo | both | [`cargo_artifacts.py`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_minimum_cargo | check_minimum_macos | (not compared) | cargo | both | [`check_minimum_macos "${rust_bin}"`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py); [`test_build_guards`](../tests/suites/preflight/opt_in/build_guards.py) |
| inv_meson_configure | meson configure | (not compared) | configure | both | [`meson configure`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_meson_setup | meson setup | (not compared) | configure | both | [`meson setup`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_meson_compile | meson compile | (not compared) | compile | both | [`meson compile`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_native_sources | tests/lib/native_sources.py --builddir | (not compared) | native_check | both | [`native_sources.py`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py); [`configured_controls`](../tests/suites/source_drift/check_planner.py) |
| inv_minimum_native | check_minimum_macos | (not compared) | native_check | both | [`check_minimum_macos "${native_bin}"`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py); [`test_build_guards`](../tests/suites/preflight/opt_in/build_guards.py) |
| inv_stamp_app | stamp_info_plist | (not compared) | assemble | both | [`stamp_info_plist "${APP_BUNDLE}/Contents/Info.plist"`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_dsym_client | embed_dsym | (not compared) | embed_client | full | [`embed_dsym "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_stamp_service | stamp_info_plist | (not compared) | embed_services | full | [`stamp_info_plist "${svc_bundle}/Contents/Info.plist"`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_dsym_host | embed_dsym | (not compared) | embed_services | full | [`embed_dsym "${svc_bundle}/Contents/MacOS/${svc_name}"`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_identity_presign | docs/generate_worker_identity.py --check | (not compared) | presign | both | [`docs/generate_worker_identity.py" --check`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_evidence | tests/build-evidence.py --app-bundle | (not compared) | evidence | both | [`build-evidence.py`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py); [`signed_artifact_controls`](../tests/suites/preflight/run.sh) |
| inv_verify | codesign --verify | (not compared) | verify | both | [`codesign --verify --deep --strict`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_display | codesign --display | (not compared) | verify | both | [`codesign --display --entitlements`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| inv_signer | tests/lib/signer_check.py | (not compared) | signer | both | [`signer_check.py`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py); [`signed_artifact_controls`](../tests/suites/preflight/run.sh); [`test_build_guards`](../tests/suites/preflight/opt_in/build_guards.py) |
| inv_guide | docs/generate_limits.py --stage-guide | (not compared) | guide | both | [`--stage-guide`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py); [`test_check_and_staging_refuse_stale_or_incomplete_documents_without_writing`](../tests/suites/source_drift/limits.py) |
| inv_zip | ditto | (not compared) | zip | both | [`/usr/bin/ditto`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |

</details>
<!-- END GENERATED BUILD INVOCATIONS -->

The `build_documentation` case in the `source_drift` suite grounds the tables:
ten rules compare the manifest with the script's banner order, refusal
messages, statuses and steps, knob values, signing calls and helper
invocations, with the Makefile's entry, with Meson's assertions, with the
three inventories and with the baseline, and mutation controls over a
disposable copy of the script show each rule naming its mutation. The parser
accepts the forms the script uses and refuses the rest, which the generator's
docstring lists.

The behavioral controls the refusals table cites drive the build itself in
disposable checkouts and observe the targeted refusal and the operation it
prevents. Early refusals stop before compilation; the opt-in build guard and
build refusal controls compile and sign to reach later refusals. The helper controls drive
Meson, the configured source check and the signer check directly.

Known gap: the build relies on Cargo, Meson and Ninja to determine whether
cached outputs match the current sources. It does not independently verify
that binaries in `builddir/` or `controller/target/` were produced from those
sources. A clean checkout and a matching source identity do not establish
binary provenance or reproducibility.

## Known gaps

Each gap is stated in full where the promise it limits is stated; this list
only points there, in document order.

- [How the build verifies itself](#how-the-build-verifies-itself): the build
  relies on the tools' records to establish whether cached outputs are current.

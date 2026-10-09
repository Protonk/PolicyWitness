# The build

This document is the account of one build in time: what each step reads,
writes and refuses, the two knobs and what each governs, what `meson.build`
owns and what `build.sh` owns, the trust placed in the build directories, the
signing contract, the evidence the build embeds and how the build verifies
itself. It does not ship. The [user guide](PolicyWitness.md) keeps its one
sentence on the supported macOS, [CONTRACT.md](CONTRACT.md) keeps the
identity's definition, and [SIGNING.md](SIGNING.md) keeps evidence,
notarization, release and the archives.

The generated figure and tables come from [build.json](build.json) through
[generate_build.py](generate_build.py), which parses `build.sh` and refuses
a manifest that disagrees with it. The build has
<!-- span build.steps -->30<!-- /span --> steps,
<!-- span build.refusals -->64<!-- /span --> refusals of which
<!-- span build.uncovered -->53<!-- /span --> have no control that produces
them, <!-- span build.signing -->8<!-- /span --> signing calls and
<!-- span build.knobs -->2<!-- /span --> knobs.

## Why the build is shaped this way

## Inputs beyond the tree

<!-- BEGIN GENERATED BUILD DIRECTORIES -->
| Directory | Trusted as | Refused when | Sources | Checks |
| --- | --- | --- | --- | --- |
| builddir/ | Meson's configuration and incremental native outputs for this checkout | its recorded source directory is not this checkout, or its meson-info cannot be read | [`MESON_SOURCE_DIR`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`](../tests/suites/source_drift/contract.py) |
| controller/target/ | Cargo's incremental outputs, pinned by --target-dir so the environment cannot move them | never as a directory; a stale output is caught only by the minimum-version check and Cargo's own fingerprints | [`CARGO_TARGET_DIR_PINNED`](../build.sh) | [`check_invocations`](../tests/suites/source_drift/build_rules.py) |
| dist/ (DIST_DIR) | the output directory; the previous app, ZIP and guide are removed at assembly and nothing is preserved | never; a refusal after assembly leaves the partial, unsealed bundle this build got to | [`rm -f "${ZIP_NAME}" "${GUIDE_NAME}"`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
<!-- END GENERATED BUILD DIRECTORIES -->

## One build in time

<!-- BEGIN GENERATED BUILD FIGURE -->
![One build in time](build-steps.svg)

*Figure: one build in time, step by step. Generated from [build.json](build.json) by [generate_build.py](generate_build.py); dot source in [build-steps.dot](build-steps.dot). The ids in the figure are the ids in the step table; a filled node runs only in a full build, a dashed one only in a partial build. Symbol presence and test definition are verified, and the banner order, refusal messages, statuses and steps, knob values, signing calls, helper invocations and the signing inventory are compared with the script by the build_documentation case; whether a test asserts the row, or a refusal fires before the operation it protects, is not verified.*
<!-- END GENERATED BUILD FIGURE -->

<!-- BEGIN GENERATED BUILD STEPS -->
<details>
<summary>30 steps in order, with symbol presence and test definition verified and the banner order compared with the script; whether a test asserts the row is not verified</summary>

| Id | Banner | Variants | Reads | Writes | Refusals | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| make_build | Makefile: [build] build, sign and embed evidence into $(DIST_DIR)/PolicyWitness.app | both | IDENTITY and DIST_DIR from the make command line | nothing; runs build.sh with them | make_identity_unset | [`[build] build, sign and embed evidence into $(DIST_DIR)/PolicyWitness.app`](../Makefile) | [`check_makefile_entry`](../tests/suites/source_drift/build_rules.py) |
| admission | (none) | both | BUILD_XPC, PW_INSPECTION and the argument list | nothing | knob_value, unknown_argument | [`must be 0 or 1`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check`](../tests/suites/source_drift/contract.py) |
| check_limits | Checking limits documentation | both | docs/limits.json and the documents it renders | nothing | stale_limits | [`Checking limits documentation`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| check_contract | Checking contract versions | both | docs/contract.json, docs/architecture.json and their generated copies | nothing | stale_contract, stale_architecture | [`Checking contract versions`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| check_build_doc | Checking build documentation | both | docs/build.json, build.sh, meson.build, the Makefile, the inventories, the baseline and the generated copies | nothing | stale_build_doc | [`Checking build documentation`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| check_identity | Checking host/worker identity | both | the identity inputs and the three generated copies | nothing | stale_identity | [`Checking host/worker identity`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| stamp | Build stamp: ${PW_VERSION} (${PW_BUILD_NUMBER}) ${PW_BUILD_DESCRIBE} | both | git describe, rev-parse and rev-list, or PW_VERSION and PW_BUILD_NUMBER from the environment | the four stamp variables for Cargo and the plists | none | [`Build stamp: ${PW_VERSION} (${PW_BUILD_NUMBER}) ${PW_BUILD_DESCRIBE}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| minimum | Supported macOS (Info.plist LSMinimumSystemVersion): ${PW_MINIMUM_MACOS} | both | LSMinimumSystemVersion in Info.plist | MACOSX_DEPLOYMENT_TARGET for Cargo | plist_minimum_malformed | [`Supported macOS (Info.plist LSMinimumSystemVersion): ${PW_MINIMUM_MACOS}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| sdk | Selecting the macOS SDK (xcrun --sdk macosx) | both | the SDK path xcrun reports under DEVELOPER_DIR | SDKROOT for Cargo and Meson | sdk_unavailable | [`Selecting the macOS SDK (xcrun --sdk macosx)`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| builddir | Checking the native build directory: ${MESON_BUILD_DIR} | both | builddir/meson-info/meson-info.json when the directory is configured | nothing | builddir_unreadable, builddir_other_checkout | [`Checking the native build directory: ${MESON_BUILD_DIR}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| identity | Checking the signing identity | both | IDENTITY and the keychain listing; the two knobs, for Meson's options and RUSTFLAGS | RUSTFLAGS, when inspection is on and it was unset or empty | identity_unset, identity_class, identity_absent | [`Checking the signing identity`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| cargo | Building Rust controller + tools | both | controller/ sources, the stamp variables, MACOSX_DEPLOYMENT_TARGET, SDKROOT and RUSTFLAGS | controller/target/release/, the pinned output directory | missing_controller, missing_observer, missing_sbpl_check, minimum_mismatch, cargo_failed | [`Building Rust controller + tools`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| toolchain | Checking the native toolchain (meson, ninja ${NINJA_MINIMUM} or newer) | both | meson and ninja on PATH and ninja's version | nothing | meson_ninja_missing, ninja_old | [`Checking the native toolchain (meson, ninja ${NINJA_MINIMUM} or newer)`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| configure | Configuring native build (meson configure, existing directory): ${MESON_OPTIONS[*]} / Configuring native build (meson setup, fresh directory): ${MESON_BUILD_DIR} ${MESON_OPTIONS[*]} | both | whether builddir/build.ninja exists, meson.build, meson.options and the two knobs as Meson options | builddir/ configuration | meson_optimization, meson_debug, meson_warning_level, meson_werror, meson_strip, meson_unity, meson_b_ndebug, meson_b_lto, meson_b_coverage, meson_b_pgo, meson_b_bitcode, meson_b_pie, meson_b_staticpic, meson_b_lundef, meson_b_sanitize, meson_c_std, meson_c_args, meson_c_link_args, meson_buildtype, meson_swift_args, meson_swift_link_args, meson_failed | [`Configuring native build (meson configure, existing directory): ${MESON_OPTIONS[*]}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| compile | Compiling native executables | both | the native sources through builddir/ | builddir/ outputs and the Swift module cache under it | meson_failed | [`Compiling native executables`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| native_check | Checking the configured native source lists and the identity closure against the tree | both | Meson's introspection of builddir/, Ninja's dependency log, the identity inputs and the Meson outputs' load commands | nothing | minimum_mismatch, missing_native_output, native_sources_differ, native_sources_unreadable | [`Checking the configured native source lists and the identity closure against the tree`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| assemble | Assembling app bundle: ${APP_BUNDLE} | both | Info.plist, the three Rust outputs, runner/augments/, dist/README.md and dist/AGENTS.md | the two documents under DIST_DIR; removes the previous app, ZIP and guide; the stamped Info.plist, the three Rust executables and the augments under the new app | missing_info_plist, missing_augments_dir | [`Assembling app bundle: ${APP_BUNDLE}`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| embed_client | Embedding PW runner client | full | builddir/pw-runner-client | Contents/MacOS/pw-runner-client and its dSYM in inspection builds | missing_client_output | [`Embedding PW runner client`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
| embed_services | Embedding PWRunner XPC services | full | each service's Info.plist and builddir/ host, the worker and the validator | each service bundle: its stamped Info.plist, the host with its dSYM in inspection builds, the worker and the validator | missing_service_dir, missing_service_plist, missing_host_output | [`Embedding PWRunner XPC services`](../build.sh) | [`check_banner_order`](../tests/suites/source_drift/build_rules.py) |
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

## Refusals

<!-- BEGIN GENERATED BUILD REFUSALS -->
<details>
<summary>64 refusals (27 the script's own, 21 Meson assertions, 15 propagated from a check or a tool, 1 in the Makefile), with symbol presence and test definition verified and the messages, statuses and steps compared with the script; 53 have no control that produces them and are listed in the baseline; whether a test asserts the row is not verified</summary>

| Id | Message | Steps | Status | Kind | Variants | Coverage | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| knob_value | ${knob} must be 0 or 1 (got '${!knob}') | admission | 2 | script | both | a control produces it | [`${knob} must be 0 or 1 (got '${!knob}')`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check`](../tests/suites/source_drift/contract.py) |
| unknown_argument | unknown argument: $1 | admission | 2 | script | both | none; listed in the baseline | [`unknown argument: $1`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| plist_minimum_malformed | Info.plist LSMinimumSystemVersion is not a major.minor version: '${PW_MINIMUM_MACOS}' | minimum | 2 | script | both | none; listed in the baseline | [`Info.plist LSMinimumSystemVersion is not a major.minor version: '${PW_MINIMUM_MACOS}'`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| sdk_unavailable | xcrun could not select the macOS SDK (DEVELOPER_DIR=${DEVELOPER_DIR:-unset}) | sdk | 2 | script | both | none; listed in the baseline | [`xcrun could not select the macOS SDK (DEVELOPER_DIR=${DEVELOPER_DIR:-unset})`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| builddir_unreadable | ${MESON_BUILD_DIR} has no readable meson-info; remove it or use a fresh build directory | builddir | 2 | script | both | a control produces it | [`${MESON_BUILD_DIR} has no readable meson-info; remove it or use a fresh build directory`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`](../tests/suites/source_drift/contract.py) |
| builddir_other_checkout | ${MESON_BUILD_DIR} is configured for ${MESON_SOURCE_DIR}, not this checkout (${ROOT_DIR}); remove it or use a fresh build directory | builddir | 2 | script | both | a control produces it | [`${MESON_BUILD_DIR} is configured for ${MESON_SOURCE_DIR}, not this checkout (${ROOT_DIR}); remove it or use a fresh build directory`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`](../tests/suites/source_drift/contract.py) |
| identity_unset | IDENTITY is not set. | identity | 2 | script | both | a control produces it | [`IDENTITY is not set.`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`](../tests/suites/source_drift/contract.py) |
| identity_class | IDENTITY must name a Developer ID Application identity; got: | identity | 2 | script | both | a control produces it | [`IDENTITY must name a Developer ID Application identity; got:`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_non_developer_id_identity_before_cargo`](../tests/suites/source_drift/contract.py) |
| identity_absent | codesigning identity not found in your keychain: | identity | 2 | script | both | none; listed in the baseline | [`codesigning identity not found in your keychain:`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_controller | expected policy-witness binary at ${RUNNER_BIN} | cargo | 2 | script | both | none; listed in the baseline | [`expected policy-witness binary at ${RUNNER_BIN}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_observer | expected sandbox-log-observer binary at ${SANDBOX_LOG_OBSERVER_BIN} | cargo | 2 | script | both | none; listed in the baseline | [`expected sandbox-log-observer binary at ${SANDBOX_LOG_OBSERVER_BIN}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_sbpl_check | expected sbpl-check binary at ${SBPL_CHECK_BIN} | cargo | 2 | script | both | none; listed in the baseline | [`expected sbpl-check binary at ${SBPL_CHECK_BIN}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| minimum_mismatch | ${target} is built for macOS ${minos:-?}; Info.plist declares ${PW_MINIMUM_MACOS} | cargo, native_check | 2 | script | both | none; listed in the baseline | [`${target} is built for macOS ${minos:-?}; Info.plist declares ${PW_MINIMUM_MACOS}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| meson_ninja_missing | meson and ninja are required for the native build (brew install meson ninja); see docs/SIGNING.md | toolchain | 2 | script | both | none; listed in the baseline | [`meson and ninja are required for the native build (brew install meson ninja); see docs/SIGNING.md`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| ninja_old | ninja ${NINJA_VERSION} is older than the ${NINJA_MINIMUM} minimum; see docs/SIGNING.md | toolchain | 2 | script | both | none; listed in the baseline | [`ninja ${NINJA_VERSION} is older than the ${NINJA_MINIMUM} minimum; see docs/SIGNING.md`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_native_output | expected Meson output at ${native_bin} | native_check | 2 | script | both | none; listed in the baseline | [`expected Meson output at ${native_bin}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_info_plist | missing ${INFO_PLIST_TEMPLATE} at repo root | assemble | 2 | script | both | none; listed in the baseline | [`missing ${INFO_PLIST_TEMPLATE} at repo root`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_augments_dir | missing augments source dir at ${XPC_AUGMENTS_DIR} | assemble | 2 | script | both | none; listed in the baseline | [`missing augments source dir at ${XPC_AUGMENTS_DIR}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_client_output | expected Meson output at ${PW_RUNNER_CLIENT_BIN} | embed_client | 2 | script | full | none; listed in the baseline | [`expected Meson output at ${PW_RUNNER_CLIENT_BIN}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_service_dir | missing ${svc_name} service dir at ${svc_dir} | embed_services | 2 | script | full | none; listed in the baseline | [`missing ${svc_name} service dir at ${svc_dir}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_service_plist | ${svc_name} service is missing Info.plist | embed_services | 2 | script | full | none; listed in the baseline | [`${svc_name} service is missing Info.plist`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_host_output | expected Meson output at ${svc_host} | embed_services | 2 | script | full | none; listed in the baseline | [`expected Meson output at ${svc_host}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_entitlements | missing entitlements plist: ${ENTITLEMENTS_PLIST} | presign | 2 | script | both | none; listed in the baseline | [`missing entitlements plist: ${ENTITLEMENTS_PLIST}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| sign_target_missing | expected a Mach-O to sign at ${target} | sign_tools, sign_services, sign_observer | 2 | script | both | none; listed in the baseline | [`expected a Mach-O to sign at ${target}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| sign_target_not_macho | ${target} is not a Mach-O; the signing list names only executables | sign_tools, sign_services, sign_observer | 2 | script | both | none; listed in the baseline | [`${target} is not a Mach-O; the signing list names only executables`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_service_bundle | expected XPC service bundle at ${svc_bundle} | sign_services | 2 | script | full | none; listed in the baseline | [`expected XPC service bundle at ${svc_bundle}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| missing_service_entitlements | ${svc_name} service is missing Entitlements.plist at ${svc_entitlements} | sign_services | 2 | script | full | none; listed in the baseline | [`${svc_name} service is missing Entitlements.plist at ${svc_entitlements}`](../build.sh) | [`check_refusals`](../tests/suites/source_drift/build_rules.py) |
| make_identity_unset | set IDENTITY to your Developer ID Application identity | make_build | 2 | make | both | none; listed in the baseline | [`set IDENTITY to your Developer ID Application identity`](../Makefile) | [`check_makefile_entry`](../tests/suites/source_drift/build_rules.py) |
| meson_optimization | fixed native policy: optimization must be 'plain' | configure | 1 | meson | both | none; listed in the baseline | [`'optimization'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_debug | fixed native policy: debug must be false | configure | 1 | meson | both | none; listed in the baseline | [`'debug'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_warning_level | fixed native policy: warning_level must be '0' | configure | 1 | meson | both | none; listed in the baseline | [`'warning_level'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_werror | fixed native policy: werror must be false | configure | 1 | meson | both | none; listed in the baseline | [`'werror'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_strip | fixed native policy: strip must be false | configure | 1 | meson | both | none; listed in the baseline | [`'strip'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_unity | fixed native policy: unity must be 'off' | configure | 1 | meson | both | none; listed in the baseline | [`'unity'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_ndebug | fixed native policy: b_ndebug must be 'false' | configure | 1 | meson | both | none; listed in the baseline | [`'b_ndebug'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_lto | fixed native policy: b_lto must be false | configure | 1 | meson | both | none; listed in the baseline | [`'b_lto'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_coverage | fixed native policy: b_coverage must be false | configure | 1 | meson | both | none; listed in the baseline | [`'b_coverage'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_pgo | fixed native policy: b_pgo must be 'off' | configure | 1 | meson | both | none; listed in the baseline | [`'b_pgo'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_bitcode | fixed native policy: b_bitcode must be false | configure | 1 | meson | both | none; listed in the baseline | [`'b_bitcode'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_pie | fixed native policy: b_pie must be false | configure | 1 | meson | both | none; listed in the baseline | [`'b_pie'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_staticpic | fixed native policy: b_staticpic must be true | configure | 1 | meson | both | none; listed in the baseline | [`'b_staticpic'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_lundef | fixed native policy: b_lundef must be true | configure | 1 | meson | both | none; listed in the baseline | [`'b_lundef'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_b_sanitize | fixed native policy: b_sanitize must be 'none' | configure | 1 | meson | both | none; listed in the baseline | [`'b_sanitize'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_c_std | fixed native policy: c_std must be 'none' | configure | 1 | meson | both | none; listed in the baseline | [`'c_std'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_c_args | fixed native policy: c_args must be [] | configure | 1 | meson | both | none; listed in the baseline | [`'c_args'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_c_link_args | fixed native policy: c_link_args must be [] | configure | 1 | meson | both | none; listed in the baseline | [`'c_link_args'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_buildtype | fixed native policy: buildtype must be 'plain' | configure | 1 | meson | both | none; listed in the baseline | [`'buildtype'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_swift_args | fixed native policy: swift_args must be [] | configure | 1 | meson | full | none; listed in the baseline | [`'swift_args'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| meson_swift_link_args | fixed native policy: swift_link_args must be [] | configure | 1 | meson | full | none; listed in the baseline | [`'swift_link_args'`](../meson.build) | [`check_meson_assertions`](../tests/suites/source_drift/build_rules.py) |
| stale_limits | stale <copy>; run python3 docs/generate_limits.py | check_limits | 1 | propagated | both | a control produces it | [`generate_limits.py`](../build.sh); [`stale`](../docs/generate_limits.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_stale_guide_before_signing_or_creating_output`](../tests/suites/source_drift/limits.py) |
| stale_contract | stale <copy>; run python3 docs/generate_contract.py | check_contract | 1 | propagated | both | a control produces it | [`generate_contract.py`](../build.sh); [`stale`](../docs/generate_contract.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_stale_contract_copy_before_signing_or_creating_output`](../tests/suites/source_drift/contract.py) |
| stale_architecture | architecture documentation is stale | check_contract | 1 | propagated | both | none; listed in the baseline | [`generate_architecture.py`](../build.sh); [`architecture documentation is stale`](../docs/generate_architecture.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_checks_every_generator_before_signing`](../tests/suites/source_drift/generators.py) |
| stale_build_doc | build documentation is stale | check_build_doc | 1 | propagated | both | none; listed in the baseline | [`generate_build.py`](../build.sh); [`build documentation is stale`](../docs/generate_build.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_checks_every_generator_before_signing`](../tests/suites/source_drift/generators.py) |
| stale_identity | stale <copy>; run python3 docs/generate_worker_identity.py | check_identity | 1 | propagated | both | a control produces it | [`generate_worker_identity.py`](../build.sh); [`stale`](../docs/generate_worker_identity.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_stale_identity_copy_before_compiling_and_writes_nothing`](../tests/suites/source_drift/contract.py) |
| stale_identity_presign | stale <copy>; run python3 docs/generate_worker_identity.py | presign | 1 | propagated | both | none; listed in the baseline | [`generate_worker_identity.py`](../build.sh); [`stale`](../docs/generate_worker_identity.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py) |
| cargo_failed | Cargo's own diagnostic | cargo | 101 | propagated | both | none; listed in the baseline | [`cargo build`](../build.sh) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py) |
| meson_failed | Meson's or Ninja's own diagnostic | configure, compile | 1 | propagated | both | none; listed in the baseline | [`meson compile`](../build.sh); [`meson setup`](../build.sh) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py) |
| native_sources_differ | native source lists differ from the tree | native_check | 1 | propagated | both | a control produces it in the helper, not through the script | [`native_sources.py`](../build.sh); [`native source lists differ from the tree`](../tests/lib/native_sources.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`configured_controls`](../tests/suites/source_drift/check_planner.py) |
| native_sources_unreadable | native sources: meson introspection failed | native_check | 2 | propagated | both | none; listed in the baseline | [`native_sources.py`](../build.sh); [`meson introspection failed`](../tests/lib/native_sources.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py) |
| codesign_failed | codesign's own diagnostic | sign_tools, sign_services, seal, sign_observer | 1 | propagated | both | none; listed in the baseline | [`codesign --force`](../build.sh) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py) |
| evidence_failed | missing app bundle Contents | evidence | 2 | propagated | both | none; listed in the baseline | [`build-evidence.py`](../build.sh); [`missing app bundle Contents`](../tests/build-evidence.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py) |
| verify_failed | codesign's own diagnostic | verify | 1 | propagated | both | none; listed in the baseline | [`codesign --verify`](../build.sh) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py) |
| signer_mismatch | executables not signed by <identity> with the hardened runtime | signer | 1 | propagated | both | a control produces it in the helper, not through the script | [`signer_check.py`](../build.sh); [`executables not signed by`](../tests/lib/signer_check.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`signed_artifact_controls`](../tests/suites/preflight/run.sh) |
| stale_guide | stale PolicyWitness.md | guide | 1 | propagated | both | a control produces it | [`--stage-guide`](../build.sh); [`stale`](../docs/generate_limits.py) | [`check_propagated_refusals`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_stale_guide_before_signing_or_creating_output`](../tests/suites/source_drift/limits.py) |

</details>
<!-- END GENERATED BUILD REFUSALS -->

## What Meson owns and what the script owns

<!-- BEGIN GENERATED BUILD KNOBS -->
| Knob | Values | Unset means | Governs | Sources | Checks |
| --- | --- | --- | --- | --- | --- |
| BUILD_XPC | `1`: build and embed the Swift client, the XPC host and the C shim (Meson xpc=true); `0`: skip them; the two C executables still build and nothing Meson-built ships (Meson xpc=false) | 1 | Meson's xpc option, the embed and service-signing steps, and which Meson outputs are minimum-checked and signed | [`BUILD_XPC="${BUILD_XPC-1}"`](../build.sh); [`option('xpc'`](../meson.options) | [`check_knobs`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check`](../tests/suites/source_drift/contract.py) |
| PW_INSPECTION | `1`: Swift -Onone -g with a dSYM beside each Swift executable; RUSTFLAGS with debug info, frame pointers and opt-level 1 when RUSTFLAGS was unset or empty (Meson inspection=true); `0`: Swift -O and no dSYM; RUSTFLAGS untouched (Meson inspection=false) | 1 | Meson's inspection option, RUSTFLAGS and the dSYM step; the C executables are -O2 without debug info in both | [`PW_INSPECTION="${PW_INSPECTION-1}"`](../build.sh); [`option('inspection'`](../meson.options) | [`check_knobs`](../tests/suites/source_drift/build_rules.py); [`test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check`](../tests/suites/source_drift/contract.py) |
<!-- END GENERATED BUILD KNOBS -->

## The signing contract

<!-- BEGIN GENERATED BUILD SIGNING -->
<details>
<summary>8 signing calls in order, with symbol presence and test definition verified and the calls, their targets and entitlements compared with the script and the signed inventory with EXECUTABLES, the evidence generator and the README; whether a test asserts the row is not verified</summary>

| # | Target | Kind | Entitlements | In the service loop | Step | Variants | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ${APP_BUNDLE}/Contents/MacOS/pw-runner-client | signature | none | no | sign_tools | full | [`${APP_BUNDLE}/Contents/MacOS/pw-runner-client`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 2 | ${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer | signature | none | no | sign_tools | both | [`${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 3 | ${APP_BUNDLE}/Contents/MacOS/sbpl-check | signature | none | no | sign_tools | both | [`${APP_BUNDLE}/Contents/MacOS/sbpl-check`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 4 | ${svc_bundle}/Contents/MacOS/pw-probe-runner | signature | none | XPC_SERVICE_NAMES | sign_services | full | [`${svc_bundle}/Contents/MacOS/pw-probe-runner`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 5 | ${svc_bundle}/Contents/MacOS/sb_api_validator | signature | none | XPC_SERVICE_NAMES | sign_services | full | [`${svc_bundle}/Contents/MacOS/sb_api_validator`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 6 | ${svc_bundle} | seal | ${svc_entitlements} | XPC_SERVICE_NAMES | sign_services | full | [`-s "${IDENTITY}" "${svc_bundle}"`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 7 | ${APP_BUNDLE} | seal | ${ENTITLEMENTS_PLIST} | no | seal | both | [`-s "${IDENTITY}" "${APP_BUNDLE}"`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |
| 8 | ${SANDBOX_LOG_OBSERVER_BIN} | signature | none | no | sign_observer | both | [`sign_macho "${SANDBOX_LOG_OBSERVER_BIN}"`](../build.sh) | [`check_signing`](../tests/suites/source_drift/build_rules.py); [`check_inventory`](../tests/suites/source_drift/build_rules.py) |

</details>
<!-- END GENERATED BUILD SIGNING -->

## The evidence the build embeds

## How the build verifies itself

## Known gaps

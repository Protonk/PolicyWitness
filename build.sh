#!/usr/bin/env bash
set -euo pipefail

# Build and sign PolicyWitness.app with a clear, single-path flow.
#
# Inputs (environment variables):
#   IDENTITY   Developer ID Application identity string in your login keychain;
#              any other identity class is refused and nothing is auto-selected.
#   BUILD_XPC  Set to 0 to skip building/embedding the XPC service and client;
#              mapped to Meson's xpc option. The two C executables still build.
#   PW_INSPECTION=1  Keep debug info and frame pointers (default); mapped to
#              Meson's inspection option (Swift -Onone -g versus -O) and to RUSTFLAGS.
#
# Native compilation (the C worker and validator, the C shim, the Swift client
# and host) runs through Meson into the ignored builddir/; meson.build owns the
# fixed native flags and refuses any other configuration. Cargo builds the Rust
# pieces. This script maps the two knobs above onto Meson's two options, selects
# the macOS SDK the way xcrun --sdk macosx does, and copies Meson's outputs into
# the bundle. Changing the selected compiler or SDK needs a fresh build
# directory (see docs/SIGNING.md).
#
# The build writes nothing into the tree: every generated copy is checked and
# a stale one is refused with the command that regenerates it.
#
# Outputs:
#   dist/PolicyWitness.app
#   dist/PolicyWitness.zip (ready for notarization)
#   dist/PolicyWitness.md (checked standalone user guide)
#   builddir/ (Meson configuration and native outputs: trusted working state,
#              like controller/target/; see docs/SIGNING.md)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="PolicyWitness"
DIST_DIR="${DIST_DIR:-${ROOT_DIR}/dist}"
APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"
ZIP_NAME="${DIST_DIR}/${APP_NAME}.zip"
GUIDE_NAME="${DIST_DIR}/${APP_NAME}.md"

# Repo paths.
RUNNER_MANIFEST="${ROOT_DIR}/controller/Cargo.toml"
ENTITLEMENTS_PLIST="${ROOT_DIR}/PolicyWitness.entitlements"
INFO_PLIST_TEMPLATE="${ROOT_DIR}/Info.plist"

# Runner source layout.
XPC_ROOT="${ROOT_DIR}/runner"
XPC_SERVICES_DIR="${XPC_ROOT}/Services"
XPC_SERVICE_NAMES=("PWRunner")

# Named SBPL augments callers opt into via policy.augments. Copied into
# Contents/Resources/Augments/ at bundle assembly time; the controller
# resolves them before sbpl-check. Non-executable resources — sealed
# by the outer app codesign at the end of the build.
XPC_AUGMENTS_DIR="${XPC_ROOT}/augments"

# Native outputs from Meson (see meson.build). The source lists, flags and
# module names live there; this script only consumes the results.
MESON_BUILD_DIR="${ROOT_DIR}/builddir"

# Host-side sandbox_check cross-check helper.
SB_API_VALIDATOR_BIN="${MESON_BUILD_DIR}/sb_api_validator"

# Sandboxed C worker spawned by the runner host. This binary is
# embedded INSIDE each XPC service bundle (not in the app's top-level
# MacOS dir), so the runner host resolves it relative to its own
# bundle and built-in vs BYOXPC runners both pick up the correct
# copy. The single output is copied into each XPC service.
PW_PROBE_RUNNER_BIN="${MESON_BUILD_DIR}/pw-probe-runner"

# Swift NSXPCConnection client embedded at the app's top level.
PW_RUNNER_CLIENT_BIN="${MESON_BUILD_DIR}/pw-runner-client"

# Build knobs: exactly 0 or 1, and an unset knob means 1. Any other value,
# including an empty one, is refused rather than read as one of them.
BUILD_XPC="${BUILD_XPC-1}"
PW_INSPECTION="${PW_INSPECTION-1}"
for knob in BUILD_XPC PW_INSPECTION; do
  case "${!knob}" in
    0|1) ;;
    *)
      echo "ERROR: ${knob} must be 0 or 1 (got '${!knob}')" 1>&2
      exit 2
      ;;
  esac
done

# The Ninja minimum docs/SIGNING.md states; meson.build states Meson's own.
NINJA_MINIMUM="1.13.2"

usage() {
  cat <<'USAGE'
usage:
  IDENTITY='Developer ID Application: ...' ./build.sh
  PW_INSPECTION=0 IDENTITY='Developer ID Application: ...' ./build.sh
USAGE
}

if [[ $# -gt 0 ]]; then
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" 1>&2
      usage 1>&2
      exit 2
      ;;
  esac
fi

# Check the documentation and the identity copies before any build or signing
# work; the identity is checked again before signing and the guide again when
# it is staged. The build writes nothing into the tree: a stale copy is
# refused, and the generator the refusal names regenerates it.
echo "==> Checking limits documentation"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_limits.py" --check
echo "==> Checking contract versions"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_contract.py" --check
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_architecture.py" --check
echo "==> Checking build documentation"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_build.py" --check
echo "==> Checking host/worker identity"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_worker_identity.py" --check

# ---- Build stamp -------------------------------------------------------------
# The app version is a coordinate derived from git, never edited by hand:
# CFBundleShortVersionString is the nearest v* tag, CFBundleVersion the commit
# count, and PWBuildDescribe/PWBuildCommit the exact source. PW_VERSION and
# PW_BUILD_NUMBER override the git-derived values (for builds outside a checkout).
PW_BUILD_DESCRIBE="$(git -C "${ROOT_DIR}" describe --tags --match 'v[0-9]*' --always --dirty 2>/dev/null || true)"
PW_BUILD_COMMIT="$(git -C "${ROOT_DIR}" rev-parse HEAD 2>/dev/null || true)"
PW_VERSION="${PW_VERSION:-$(printf '%s' "${PW_BUILD_DESCRIBE}" | /usr/bin/sed -nE 's/^v([0-9]+\.[0-9]+\.[0-9]+).*/\1/p')}"
PW_BUILD_NUMBER="${PW_BUILD_NUMBER:-$(git -C "${ROOT_DIR}" rev-list --count HEAD 2>/dev/null || true)}"
: "${PW_VERSION:=0.0.0}"
: "${PW_BUILD_NUMBER:=0}"
: "${PW_BUILD_DESCRIBE:=unknown}"
: "${PW_BUILD_COMMIT:=unknown}"
echo "==> Build stamp: ${PW_VERSION} (${PW_BUILD_NUMBER}) ${PW_BUILD_DESCRIBE}"

stamp_info_plist() {
  local plist="$1"
  /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${PW_VERSION}" "${plist}"
  /usr/libexec/PlistBuddy -c "Set :CFBundleVersion ${PW_BUILD_NUMBER}" "${plist}"
  /usr/libexec/PlistBuddy -c "Add :PWBuildDescribe string ${PW_BUILD_DESCRIBE}" "${plist}"
  /usr/libexec/PlistBuddy -c "Add :PWBuildCommit string ${PW_BUILD_COMMIT}" "${plist}"
}

# The supported macOS: Info.plist declares it, meson.build pins the native
# compile and link to the same value, Cargo's Apple targets read it from this
# variable, and every shipped Mach-O is checked against the plist below.
PW_MINIMUM_MACOS="$(/usr/libexec/PlistBuddy -c 'Print :LSMinimumSystemVersion' "${INFO_PLIST_TEMPLATE}")"
echo "==> Supported macOS (Info.plist LSMinimumSystemVersion): ${PW_MINIMUM_MACOS}"
if [[ ! "${PW_MINIMUM_MACOS}" =~ ^[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: Info.plist LSMinimumSystemVersion is not a major.minor version: '${PW_MINIMUM_MACOS}'" 1>&2
  exit 2
fi
export MACOSX_DEPLOYMENT_TARGET="${PW_MINIMUM_MACOS}"

# Every Cargo and Meson output that can ship must carry that minimum, in both
# variants and before assembly; a stale output, a toolchain default that moved
# or a manifest pinned to another version than the plist refuses here rather
# than shipping a disagreement.
check_minimum_macos() {
  local target="$1" minos
  minos="$(/usr/bin/otool -l "${target}" | /usr/bin/awk '/LC_BUILD_VERSION/{f=1} f&&/minos/{print $2; exit}')"
  if [[ "${minos}" != "${PW_MINIMUM_MACOS}" ]]; then
    echo "ERROR: ${target} is built for macOS ${minos:-?}; Info.plist declares ${PW_MINIMUM_MACOS}" 1>&2
    exit 2
  fi
}

# ---- Toolchain and build-directory admission --------------------------------

# One SDK for Cargo and Meson, selected the way xcrun --sdk macosx does, before
# any compile; DEVELOPER_DIR passes through for the toolchain choice. The
# selection is checked here because set -e would see export's status, not
# xcrun's.
echo "==> Selecting the macOS SDK (xcrun --sdk macosx)"
if ! SDKROOT="$(/usr/bin/xcrun --sdk macosx --show-sdk-path 2>/dev/null)" || [[ ! -d "${SDKROOT}" ]]; then
  echo "ERROR: xcrun could not select the macOS SDK (DEVELOPER_DIR=${DEVELOPER_DIR:-unset})" 1>&2
  exit 2
fi
export SDKROOT
echo "    ${SDKROOT}"

# A build directory is trusted incremental state for this checkout and no
# other. Meson keeps compiling the source directory a build directory was set
# up for, so one configured elsewhere (copied along with a checkout, say)
# would compile that other tree and pass every later check against it. Refuse
# it here, before Cargo; the configured source check repeats the comparison.
echo "==> Checking the native build directory: ${MESON_BUILD_DIR}"
if [[ -f "${MESON_BUILD_DIR}/build.ninja" ]]; then
  if ! MESON_SOURCE_DIR="$(/usr/bin/python3 -c 'import json, os, sys; print(os.path.realpath(json.load(open(sys.argv[1]))["directories"]["source"]))' "${MESON_BUILD_DIR}/meson-info/meson-info.json" 2>/dev/null)"; then
    echo "ERROR: ${MESON_BUILD_DIR} has no readable meson-info; remove it or use a fresh build directory" 1>&2
    exit 2
  fi
  if [[ "${MESON_SOURCE_DIR}" != "$(cd "${ROOT_DIR}" && pwd -P)" ]]; then
    echo "ERROR: ${MESON_BUILD_DIR} is configured for ${MESON_SOURCE_DIR}, not this checkout (${ROOT_DIR}); remove it or use a fresh build directory" 1>&2
    exit 2
  fi
fi

# Select and verify the signing identity: an explicit Developer ID Application
# identity present in the login keychain. Nothing is auto-selected, and any
# other identity class is refused here, before Cargo runs (docs/SIGNING.md).
echo "==> Checking the signing identity"
IDENTITY="${IDENTITY:-}"
if [[ -z "${IDENTITY}" ]]; then
  cat <<'EOM' 1>&2
ERROR: IDENTITY is not set.

Set it to your Developer ID Application identity string, for example:
  IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' ./build.sh

You can find valid identities via:
  security find-identity -v -p codesigning
EOM
  exit 2
fi
if [[ "${IDENTITY}" != "Developer ID Application: "* ]]; then
  cat <<EOM 1>&2
ERROR: IDENTITY must name a Developer ID Application identity; got:
  ${IDENTITY}

Other identity classes (Apple Development, Mac Developer, ad hoc, self-signed)
produce an app the tests and notarization reject; see docs/SIGNING.md.
EOM
  exit 2
fi
if ! /usr/bin/security find-identity -v -p codesigning 2>/dev/null | /usr/bin/grep -Fq "\"${IDENTITY}\""; then
  cat <<EOM 1>&2
ERROR: codesigning identity not found in your keychain:
  ${IDENTITY}

Run:
  security find-identity -v -p codesigning

Then ensure the identity is installed/unlocked (or set IDENTITY to one of the listed identities).
EOM
  exit 2
fi

# Map the two public knobs onto Meson's two options; meson.build fixes every
# other native setting. Both options are passed on every configuration so a
# build directory never retains an earlier variant.
MESON_OPTIONS=("-Dinspection=false" "-Dxpc=false")
if [[ "${PW_INSPECTION}" == "1" ]]; then
  MESON_OPTIONS[0]="-Dinspection=true"
  if [[ -z "${RUSTFLAGS:-}" ]]; then
    export RUSTFLAGS="-C debuginfo=2 -C force-frame-pointers=yes -C opt-level=1"
  fi
fi
if [[ "${BUILD_XPC}" == "1" ]]; then
  MESON_OPTIONS[1]="-Dxpc=true"
fi

# ---- Build binaries --------------------------------------------------------

# The output directory is pinned on the command line, so a CARGO_TARGET_DIR
# or a Cargo configuration value cannot send the outputs elsewhere while the
# copies below read these fixed paths. Cargo is asked to report what it
# produced: a target triple or another setting that placed an executable
# under a different directory refuses here, before a stale file at the pinned
# path could be copied in its place.
CARGO_TARGET_DIR_PINNED="${ROOT_DIR}/controller/target"
CARGO_MESSAGES="${CARGO_TARGET_DIR_PINNED}/pw-build-messages.jsonl"
RUNNER_BIN="${CARGO_TARGET_DIR_PINNED}/release/policy-witness"
SANDBOX_LOG_OBSERVER_BIN="${CARGO_TARGET_DIR_PINNED}/release/sandbox-log-observer"
SBPL_CHECK_BIN="${CARGO_TARGET_DIR_PINNED}/release/sbpl-check"
echo "==> Building Rust controller + tools"
mkdir -p "${CARGO_TARGET_DIR_PINNED}"
rm -f "${CARGO_MESSAGES}"
PW_BUILD_VERSION="${PW_VERSION}" PW_BUILD_NUMBER="${PW_BUILD_NUMBER}" \
  PW_BUILD_DESCRIBE="${PW_BUILD_DESCRIBE}" PW_BUILD_COMMIT="${PW_BUILD_COMMIT}" \
  cargo build --manifest-path "${RUNNER_MANIFEST}" --release \
  --target-dir "${CARGO_TARGET_DIR_PINNED}" \
  --message-format=json-render-diagnostics \
  --bin policy-witness \
  --bin sandbox-log-observer \
  --bin sbpl-check \
  > "${CARGO_MESSAGES}"
CARGO_BUILT="$(/usr/bin/python3 -B "${ROOT_DIR}/tests/lib/cargo_artifacts.py" "${CARGO_MESSAGES}" policy-witness sandbox-log-observer sbpl-check)"
while IFS=$'\t' read -r bin_name bin_path; do
  case "${bin_name}" in
    policy-witness) bin_expected="${RUNNER_BIN}" ;;
    sandbox-log-observer) bin_expected="${SANDBOX_LOG_OBSERVER_BIN}" ;;
    sbpl-check) bin_expected="${SBPL_CHECK_BIN}" ;;
    *) continue ;;
  esac
  if [[ "${bin_path}" != "${bin_expected}" ]]; then
    echo "ERROR: cargo built ${bin_name} at ${bin_path}, not at ${bin_expected}; a target triple or a Cargo setting moved it" 1>&2
    exit 2
  fi
done <<< "${CARGO_BUILT}"

if [[ ! -x "${RUNNER_BIN}" ]]; then
  echo "ERROR: expected policy-witness binary at ${RUNNER_BIN}" 1>&2
  exit 2
fi
if [[ ! -x "${SANDBOX_LOG_OBSERVER_BIN}" ]]; then
  echo "ERROR: expected sandbox-log-observer binary at ${SANDBOX_LOG_OBSERVER_BIN}" 1>&2
  exit 2
fi
if [[ ! -x "${SBPL_CHECK_BIN}" ]]; then
  echo "ERROR: expected sbpl-check binary at ${SBPL_CHECK_BIN}" 1>&2
  exit 2
fi
for rust_bin in "${RUNNER_BIN}" "${SANDBOX_LOG_OBSERVER_BIN}" "${SBPL_CHECK_BIN}"; do
  check_minimum_macos "${rust_bin}"
done
# ---- Native executables (Meson) ---------------------------------------------

# The SDK was selected above. The first build
# sets the directory up; later builds pass the current variants with meson
# configure, which regenerates only when a value changed, so an unchanged
# tree compiles nothing. meson.build's policy assertions run on setup and on
# every regeneration, so an unsupported or injected option refuses here,
# before any output is copied or signed. (Meson reads CFLAGS and friends only
# when a directory is first set up; a fresh directory refuses them.) The
# source directory is named on setup so the build does not depend on the
# caller's working directory. The worker links libsandbox dynamically there
# (sandbox_apply and sandbox_compile_string are SPI in
# /usr/lib/libsandbox.dylib); the validator does not.
echo "==> Checking the native toolchain (meson, ninja ${NINJA_MINIMUM} or newer)"
if ! command -v meson >/dev/null 2>&1 || ! command -v ninja >/dev/null 2>&1; then
  echo "ERROR: meson and ninja are required for the native build (brew install meson ninja); see docs/SIGNING.md" 1>&2
  exit 2
fi
NINJA_VERSION="$(ninja --version)"
if ! /usr/bin/python3 -c 'import sys; v, m = (tuple(int(p) for p in a.split(".")) for a in sys.argv[1:3]); sys.exit(0 if v >= m else 1)' \
    "${NINJA_VERSION}" "${NINJA_MINIMUM}"; then
  echo "ERROR: ninja ${NINJA_VERSION} is older than the ${NINJA_MINIMUM} minimum; see docs/SIGNING.md" 1>&2
  exit 2
fi
if [[ -f "${MESON_BUILD_DIR}/build.ninja" ]]; then
  echo "==> Configuring native build (meson configure, existing directory): ${MESON_OPTIONS[*]}"
  meson configure "${MESON_BUILD_DIR}" "${MESON_OPTIONS[@]}"
else
  echo "==> Configuring native build (meson setup, fresh directory): ${MESON_BUILD_DIR} ${MESON_OPTIONS[*]}"
  meson setup "${MESON_BUILD_DIR}" "${ROOT_DIR}" "${MESON_OPTIONS[@]}"
fi
echo "==> Compiling native executables"
meson compile -C "${MESON_BUILD_DIR}"
# What Meson evaluated must be the tree: every configured target's sources
# are compared with the repository, so a manifest that compiles a substitute
# or a dead declaration standing in for a live one refuses here, before any
# output is copied. The same check reads Ninja's dependency log: every
# repository file the compiler consumed for the worker and the shim must be an
# identity digest input, so an include reaching outside the digest's
# directories refuses too. The check is told which checkout the directory
# must be configured for. The source_drift suite applies the source-list
# expectation to the manifest read without a build directory.
echo "==> Checking the configured native source lists and the identity closure against the tree"
/usr/bin/python3 -B "${ROOT_DIR}/tests/lib/native_sources.py" --builddir "${MESON_BUILD_DIR}" --root "${ROOT_DIR}"
NATIVE_OUTPUTS=("${SB_API_VALIDATOR_BIN}" "${PW_PROBE_RUNNER_BIN}")
if [[ "${BUILD_XPC}" == "1" ]]; then
  NATIVE_OUTPUTS+=("${PW_RUNNER_CLIENT_BIN}")
  for svc_name in "${XPC_SERVICE_NAMES[@]}"; do
    NATIVE_OUTPUTS+=("${MESON_BUILD_DIR}/${svc_name}")
  done
fi
for native_bin in "${NATIVE_OUTPUTS[@]}"; do
  if [[ ! -x "${native_bin}" ]]; then
    echo "ERROR: expected Meson output at ${native_bin}" 1>&2
    exit 2
  fi
  check_minimum_macos "${native_bin}"
done

# ---- Assemble app bundle ---------------------------------------------------

echo "==> Assembling app bundle: ${APP_BUNDLE}"
mkdir -p "${DIST_DIR}"
for document in README.md AGENTS.md; do
  if [[ ! "${ROOT_DIR}/dist/${document}" -ef "${DIST_DIR}/${document}" ]]; then
    cp "${ROOT_DIR}/dist/${document}" "${DIST_DIR}/${document}"
  fi
done
# From here on a refusal leaves only what this build got to: the previous app,
# ZIP and guide at the output path are removed together, and nothing is
# preserved.
rm -rf "${APP_BUNDLE}"
rm -f "${ZIP_NAME}" "${GUIDE_NAME}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS" "${APP_BUNDLE}/Contents/Resources"

if [[ ! -f "${INFO_PLIST_TEMPLATE}" ]]; then
  echo "ERROR: missing ${INFO_PLIST_TEMPLATE} at repo root" 1>&2
  exit 2
fi
cp "${INFO_PLIST_TEMPLATE}" "${APP_BUNDLE}/Contents/Info.plist"
stamp_info_plist "${APP_BUNDLE}/Contents/Info.plist"

cp "${RUNNER_BIN}" "${APP_BUNDLE}/Contents/MacOS/policy-witness"
chmod +x "${APP_BUNDLE}/Contents/MacOS/policy-witness"

cp "${SANDBOX_LOG_OBSERVER_BIN}" "${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer"
chmod +x "${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer"

cp "${SBPL_CHECK_BIN}" "${APP_BUNDLE}/Contents/MacOS/sbpl-check"
chmod +x "${APP_BUNDLE}/Contents/MacOS/sbpl-check"

# sb_api_validator is embedded only INSIDE each XPC service bundle (see
# the XPC build loop below) and resolved relative to that bundle by the
# runner host; test harnesses that drive the validator CLI directly use
# that bundle-local copy.

# Copy named augments under Contents/Resources/Augments/. The
# controller reads from this directory when resolving
# request.policy.augments before sbpl-check. Augments are
# resources, not executables; the outer codesign at the end of the
# build seals them as part of the app bundle.
if [[ -d "${XPC_AUGMENTS_DIR}" ]]; then
  AUGMENTS_OUT_DIR="${APP_BUNDLE}/Contents/Resources/Augments"
  mkdir -p "${AUGMENTS_OUT_DIR}"
  augments_found=0
  for augment_src in "${XPC_AUGMENTS_DIR}"/*.sb; do
    if [[ ! -f "${augment_src}" ]]; then
      continue
    fi
    augments_found=1
    cp "${augment_src}" "${AUGMENTS_OUT_DIR}/"
  done
  if [[ "${augments_found}" == "0" ]]; then
    echo "WARN: no augments found in ${XPC_AUGMENTS_DIR}; Contents/Resources/Augments will be empty" 1>&2
  fi
else
  echo "ERROR: missing augments source dir at ${XPC_AUGMENTS_DIR}" 1>&2
  exit 2
fi

# ---- Build embedded XPC components ----------------------------------------

# Inspection builds keep a .dSYM beside each Swift executable, as the former
# one-shot `swiftc -g` link left behind. The executable's debug map points at
# the objects under builddir/, which still exist at this point.
embed_dsym() {
  local target="$1"
  rm -rf "${target}.dSYM"
  if [[ "${PW_INSPECTION}" == "1" ]]; then
    /usr/bin/xcrun dsymutil "${target}" -o "${target}.dSYM"
  fi
}

if [[ "${BUILD_XPC}" == "1" ]]; then
  echo "==> Embedding PW runner client"
  if [[ ! -x "${PW_RUNNER_CLIENT_BIN}" ]]; then
    echo "ERROR: expected Meson output at ${PW_RUNNER_CLIENT_BIN}" 1>&2
    exit 2
  fi
  cp "${PW_RUNNER_CLIENT_BIN}" "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
  chmod +x "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
  embed_dsym "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"

  echo "==> Embedding PWRunner XPC services"
  for svc_name in "${XPC_SERVICE_NAMES[@]}"; do
    svc_dir="${XPC_SERVICES_DIR}/${svc_name}"
    svc_info="${svc_dir}/Info.plist"
    svc_host="${MESON_BUILD_DIR}/${svc_name}"
    svc_bundle="${APP_BUNDLE}/Contents/XPCServices/${svc_name}.xpc"
    if [[ ! -d "${svc_dir}" ]]; then
      echo "ERROR: missing ${svc_name} service dir at ${svc_dir}" 1>&2
      exit 2
    fi
    if [[ ! -f "${svc_info}" ]]; then
      echo "ERROR: ${svc_name} service is missing Info.plist" 1>&2
      exit 2
    fi
    if [[ ! -x "${svc_host}" ]]; then
      echo "ERROR: expected Meson output at ${svc_host}" 1>&2
      exit 2
    fi
    mkdir -p "${svc_bundle}/Contents/MacOS"
    cp "${svc_info}" "${svc_bundle}/Contents/Info.plist"
    stamp_info_plist "${svc_bundle}/Contents/Info.plist"

    # The host executable: meson.build's PWRunner target, whose source list
    # the source_drift suite compares with the tree.
    cp "${svc_host}" "${svc_bundle}/Contents/MacOS/${svc_name}"
    chmod +x "${svc_bundle}/Contents/MacOS/${svc_name}"
    embed_dsym "${svc_bundle}/Contents/MacOS/${svc_name}"

    # Embed pw-probe-runner inside the XPC service bundle so the host
    # resolves it relative to its own bundle for both built-in and
    # BYOXPC runners.
    cp "${PW_PROBE_RUNNER_BIN}" "${svc_bundle}/Contents/MacOS/pw-probe-runner"
    chmod +x "${svc_bundle}/Contents/MacOS/pw-probe-runner"

    # Embed sb_api_validator alongside pw-probe-runner for the same
    # bundle-local resolution reason — BYOXPC runners live outside any
    # app bundle, so the orchestrator's app-level fallback would miss.
    # The orchestrator checks bundle-local first.
    cp "${SB_API_VALIDATOR_BIN}" "${svc_bundle}/Contents/MacOS/sb_api_validator"
    chmod +x "${svc_bundle}/Contents/MacOS/sb_api_validator"
  done
else
  echo "==> Skipping embedded XPC build (BUILD_XPC=0)"
fi

# ---- Codesign --------------------------------------------------------------

# Refuse an identity input edited during the build without regeneration,
# instead of signing mixed components; the build otherwise trusts the checkout
# not to change under it.
echo "==> Checking host/worker identity again, before signing"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_worker_identity.py" --check

if [[ ! -f "${ENTITLEMENTS_PLIST}" ]]; then
  echo "ERROR: missing entitlements plist: ${ENTITLEMENTS_PLIST}" 1>&2
  exit 2
fi

# Sign one Mach-O named by the signing list. The list names exactly the
# executables this build produced, so a missing or non-Mach-O target is a
# refusal, never a skip.
sign_macho() {
  local target="$1"
  if [[ ! -f "${target}" ]]; then
    echo "ERROR: expected a Mach-O to sign at ${target}" 1>&2
    exit 2
  fi
  if ! /usr/bin/file -b "${target}" | /usr/bin/grep -q "Mach-O"; then
    echo "ERROR: ${target} is not a Mach-O; the signing list names only executables" 1>&2
    exit 2
  fi
  codesign --force --options runtime --timestamp -s "${IDENTITY}" "${target}"
}

echo "==> Codesigning embedded MacOS tools"
if [[ "${BUILD_XPC}" == "1" ]]; then
  sign_macho "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
fi
sign_macho "${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer"
sign_macho "${APP_BUNDLE}/Contents/MacOS/sbpl-check"

if [[ "${BUILD_XPC}" == "1" ]] && [[ -d "${XPC_SERVICES_DIR}" ]]; then
  echo "==> Codesigning embedded XPC services"
  for svc_name in "${XPC_SERVICE_NAMES[@]}"; do
    svc_entitlements="${XPC_SERVICES_DIR}/${svc_name}/Entitlements.plist"
    svc_bundle="${APP_BUNDLE}/Contents/XPCServices/${svc_name}.xpc"
    if [[ ! -d "${svc_bundle}" ]]; then
      echo "ERROR: expected XPC service bundle at ${svc_bundle}" 1>&2
      exit 2
    fi
    if [[ ! -f "${svc_entitlements}" ]]; then
      echo "ERROR: ${svc_name} service is missing Entitlements.plist at ${svc_entitlements}" 1>&2
      exit 2
    fi

    # Sign embedded helpers (e.g. pw-probe-runner, sb_api_validator)
    # BEFORE sealing the bundle, so the bundle codesign records their
    # hashes. Without this, codesign may refuse to validate the
    # sealed bundle because the helpers carry no signature when the
    # seal is computed.
    sign_macho "${svc_bundle}/Contents/MacOS/pw-probe-runner"
    sign_macho "${svc_bundle}/Contents/MacOS/sb_api_validator"

    codesign --force --options runtime --timestamp \
      --entitlements "${svc_entitlements}" \
      -s "${IDENTITY}" "${svc_bundle}"
  done
fi

# Evidence generation must run after the binaries are in place and signed.
echo "==> Writing evidence manifest (signed BOM)"
/usr/bin/python3 "${ROOT_DIR}/tests/build-evidence.py" \
  --app-bundle "${APP_BUNDLE}" \
  --app-entitlements "${ENTITLEMENTS_PLIST}"

# Sign the outer app last so the bundle is coherent.
echo "==> Codesigning app bundle"
codesign --force --options runtime --timestamp \
  --entitlements "${ENTITLEMENTS_PLIST}" \
  -s "${IDENTITY}" "${APP_BUNDLE}"

echo "==> Verifying signature + entitlements"
codesign --verify --deep --strict --verbose=2 "${APP_BUNDLE}"
codesign --display --entitlements - "${APP_BUNDLE}" >/dev/null

# Every executable under the app's and each service's Contents/MacOS must
# carry the named identity with the hardened runtime, whether or not the
# signing list named it. The linker leaves every compiler output ad hoc-signed,
# and an ad hoc executable passes the seal and the verification above and
# fails only at notarization. The dSYM bundles are sealed resources, not
# executables, and are not checked.
echo "==> Checking every executable's signer"
/usr/bin/python3 -B "${ROOT_DIR}/tests/lib/signer_check.py" "${APP_BUNDLE}" "${IDENTITY}"

# Keep the standalone observer tool signed for direct use.
echo "==> Codesigning observer tool (not embedded)"
sign_macho "${SANDBOX_LOG_OBSERVER_BIN}"

# ---- Package ---------------------------------------------------------------

echo "==> Staging checked user guide"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_limits.py" \
  --stage-guide "${GUIDE_NAME}"

echo "==> Creating zip (for notarization): ${ZIP_NAME}"
rm -f "${ZIP_NAME}"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "${APP_BUNDLE}" "${ZIP_NAME}"

cat <<EOF

DONE:
  - ${APP_BUNDLE}
  - ${ZIP_NAME}
  - ${GUIDE_NAME}
  - ${SANDBOX_LOG_OBSERVER_BIN}

Next (see docs/SIGNING.md; make notarize builds again):
  make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: ...'
  # For this existing ZIP, follow the individual steps in docs/SIGNING.md.
  # Keep their receipts in one ${DIST_DIR}/evidence/<attempt>/ directory.
EOF

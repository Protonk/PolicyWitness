#!/usr/bin/env bash
set -euo pipefail

# Build and sign PolicyWitness.app with a clear, single-path flow.
#
# Inputs (environment variables):
#   IDENTITY   Developer ID Application identity string in your login keychain;
#              nothing is auto-selected, and the signatures made with it are
#              verified against the Developer ID chain after the seal.
#   BUILD_XPC  Set to 0 to skip building/embedding the XPC service and client;
#              mapped to Meson's xpc option. The two C executables still build.
#   PW_INSPECTION=1  Keep debug info and frame pointers (default); mapped to
#              Meson's inspection option (Swift -Onone -g versus -O) and to RUSTFLAGS.
#   PW_FRESH_BUILD=1  Replace builddir/, controller/target/release/ and
#              controller/target/aarch64-apple-darwin/release/ after admission
#              and require Cargo to rebuild every shipped target; 0 (the
#              default) reuses them under their recorded toolchain.
#
# Every executable the build delivers is a thin arm64 Mach-O for macOS: Cargo
# is given the one output triple below, meson.build requires an arm64 macOS
# host machine and selects the architecture explicitly, and each output, the
# assembled bundle and the standalone observer are checked against that target
# by their bytes before they are copied, signed or packaged. The target
# describes the products only; which machine or process runs the build is
# not checked.
#
# Native compilation (the C worker and validator, the C shim, the Swift client
# and host) runs through Meson into the ignored builddir/; meson.build owns the
# fixed native flags and refuses any other configuration. Cargo builds the Rust
# pieces. This script maps the knobs above onto Meson's two options, selects
# the macOS SDK the way xcrun --sdk macosx does, and copies Meson's outputs into
# the bundle. A reused build directory carries a stamp of the toolchain it was
# configured with (builddir/pw-toolchain.json); the build compares the stamp
# with the tools selected now and refuses a changed or unknown toolchain
# until fresh mode replaces the directory (docs/BUILD.md).
#
# The build writes nothing into the tree: every generated copy is checked and
# a stale one is refused with the command that regenerates it. It holds
# tests/.checkout.lock from admission through packaging, so a build and a
# managed test execution in one checkout are mutually exclusive.
#
# Outputs:
#   dist/PolicyWitness.app
#   dist/PolicyWitness.zip (ready for notarization)
#   dist/PolicyWitness.md (checked standalone user guide)
#   builddir/ (Meson configuration, its toolchain stamp and native outputs:
#              trusted working state, like controller/target/; see docs/BUILD.md)
#   controller/target/pw-build-session.json (this build's observations, read by
#              the evidence step; replaced by the next build)

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
PW_EXTENSION_ISSUER_BIN="${MESON_BUILD_DIR}/pw-extension-issuer"

# Swift NSXPCConnection client embedded at the app's top level.
PW_RUNNER_CLIENT_BIN="${MESON_BUILD_DIR}/pw-runner-client"

# Cargo's output directory and output target are pinned on the command line, so
# a CARGO_TARGET_DIR, a CARGO_BUILD_TARGET or a Cargo configuration value cannot
# send the outputs elsewhere or build them for another platform while the
# copies below read these fixed paths. With an explicit target, Cargo puts the
# shipped executables under <target-dir>/<triple>/release/ and keeps build
# scripts and procedural macros under <target-dir>/release/. Its intermediate
# release state is admitted under the same directory before Cargo runs. This
# build's session file lives beside Cargo's artifact messages.
CARGO_TARGET_DIR_PINNED="${ROOT_DIR}/controller/target"
CARGO_OUTPUT_TRIPLE="aarch64-apple-darwin"
CARGO_MESSAGES="${CARGO_TARGET_DIR_PINNED}/pw-build-messages.jsonl"
BUILD_SESSION="${CARGO_TARGET_DIR_PINNED}/pw-build-session.json"
RUNNER_BIN="${CARGO_TARGET_DIR_PINNED}/${CARGO_OUTPUT_TRIPLE}/release/policy-witness"
SANDBOX_LOG_OBSERVER_BIN="${CARGO_TARGET_DIR_PINNED}/${CARGO_OUTPUT_TRIPLE}/release/sandbox-log-observer"
SBPL_CHECK_BIN="${CARGO_TARGET_DIR_PINNED}/${CARGO_OUTPUT_TRIPLE}/release/sbpl-check"

# Build knobs: exactly 0 or 1. An unset BUILD_XPC or PW_INSPECTION means 1 and
# an unset PW_FRESH_BUILD means 0. Any other value, including an empty one, is
# refused rather than read as one of them.
BUILD_XPC="${BUILD_XPC-1}"
PW_INSPECTION="${PW_INSPECTION-1}"
PW_FRESH_BUILD="${PW_FRESH_BUILD-0}"
for knob in BUILD_XPC PW_INSPECTION PW_FRESH_BUILD; do
  case "${!knob}" in
    0|1) ;;
    *)
      echo "ERROR: ${knob} must be 0 or 1 (got '${!knob}')" 1>&2
      exit 2
      ;;
  esac
done

# The Ninja minimum docs/BUILD.md states; meson.build states Meson's own.
NINJA_MINIMUM="1.13.2"

usage() {
  cat <<'USAGE'
usage:
  IDENTITY='Developer ID Application: ...' ./build.sh
  PW_INSPECTION=0 IDENTITY='Developer ID Application: ...' ./build.sh
  PW_FRESH_BUILD=1 IDENTITY='Developer ID Application: ...' ./build.sh
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

# Every tracked input the build copies or stamps must be present before any
# check runs; the first absent one is named. The build otherwise assumes a
# stable checkout and lets a copy that finds its input gone fail on its own.
for tree_input in Info.plist PolicyWitness.entitlements runner/augments runner/Services/PWRunner runner/Services/PWRunner/Info.plist runner/Services/PWRunner/Entitlements.plist; do
  if [[ ! -e "${ROOT_DIR}/${tree_input}" ]]; then
    echo "ERROR: missing tracked build input: ${tree_input}" 1>&2
    exit 2
  fi
done

# ---- Checkout lock -----------------------------------------------------------
# A build and a managed test execution in one checkout are mutually exclusive:
# both hold tests/.checkout.lock. Every Python step here starts the developer
# directory's python3 directly, which the resolver finds without running a
# shim: the /usr/bin/python3 shim inserts SDKROOT, CPATH, LIBRARY_PATH and
# MANPATH into everything it starts. Without a claim in the environment, this
# script hands itself to the shell front end before any Python runs: the front
# end witnesses the caller's SDKROOT, CPATH, LIBRARY_PATH, MANPATH and LC_CTYPE
# with shell builtins, and the owner it starts takes the lock or refuses a busy
# one before any cache or distribution mutation, then supervises this script
# again under it. The held descriptor is passed to the script and inherited by
# every compiler and tool it runs, so the hold lasts until the last of them
# exits, even if this script or its owner is killed first. Under a claim, the
# owner's handoff is verified below, never the environment alone. Nothing
# restores a value: session-start compares the witness with the environment
# this script started with, and a nested build that wants other values starts
# through the front end again.
source "${ROOT_DIR}/tests/lib/python_start.sh"
if [[ -z "${PW_CHECKOUT_LOCK_ROOT+set}${PW_CHECKOUT_LOCK_NONCE+set}${PW_CHECKOUT_LOCK_CHANNEL+set}${PW_CHECKOUT_LOCK_FD+set}" ]]; then
  exec /bin/bash "${ROOT_DIR}/tests/lib/checkout_lock.sh" --root "${ROOT_DIR}" -- /bin/bash "${BASH_SOURCE[0]}" "$@"
fi
# Keep the caller's SDK request apart until xcrun resolves it: a git shim
# given an invalid SDKROOT can request a Command Line Tools installation.
SDK_REQUEST_STATE=unset
SDK_REQUEST_VALUE="${SDKROOT-}"
if [[ -n "${SDKROOT+set}" ]]; then
  SDK_REQUEST_STATE=set
fi
unset SDKROOT
echo "==> Verifying the checkout lock: ${ROOT_DIR}/tests/.checkout.lock"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/checkout_lock.py" --verify --root "${ROOT_DIR}"

# Check the documentation and the identity copies before any build or signing
# work; the identity is checked again before signing and the guide again when
# it is staged. The build writes nothing into the tree: a stale copy is
# refused, and the generator the refusal names regenerates it.
echo "==> Checking limits documentation"
"${PW_PYTHON}" -B "${ROOT_DIR}/docs/generate_limits.py" --check
echo "==> Checking contract versions"
"${PW_PYTHON}" -B "${ROOT_DIR}/docs/generate_contract.py" --check
"${PW_PYTHON}" -B "${ROOT_DIR}/docs/generate_architecture.py" --check
echo "==> Checking build documentation"
"${PW_PYTHON}" -B "${ROOT_DIR}/docs/generate_build.py" --check
echo "==> Checking host/worker identity"
"${PW_PYTHON}" -B "${ROOT_DIR}/docs/generate_worker_identity.py" --check

# ---- Build stamp -------------------------------------------------------------
# The app version is a coordinate derived from git, never edited by hand:
# CFBundleShortVersionString is the nearest v* tag, CFBundleVersion the commit
# count, and PWBuildDescribe/PWBuildCommit the exact source. PW_VERSION and
# PW_BUILD_NUMBER override the git-derived values (for builds outside a checkout).
# The build session opens here with the stamp and the knobs; every later
# observation lands in it, and the evidence step assembles the record from it.
PW_BUILD_DESCRIBE="$(git -C "${ROOT_DIR}" describe --tags --match 'v[0-9]*' --always --dirty 2>/dev/null || true)"
PW_BUILD_COMMIT="$(git -C "${ROOT_DIR}" rev-parse HEAD 2>/dev/null || true)"
PW_VERSION="${PW_VERSION:-$(printf '%s' "${PW_BUILD_DESCRIBE}" | /usr/bin/sed -nE 's/^v([0-9]+\.[0-9]+\.[0-9]+).*/\1/p')}"
PW_BUILD_NUMBER="${PW_BUILD_NUMBER:-$(git -C "${ROOT_DIR}" rev-list --count HEAD 2>/dev/null || true)}"
: "${PW_VERSION:=0.0.0}"
: "${PW_BUILD_NUMBER:=0}"
: "${PW_BUILD_DESCRIBE:=unknown}"
: "${PW_BUILD_COMMIT:=unknown}"
echo "==> Build stamp: ${PW_VERSION} (${PW_BUILD_NUMBER}) ${PW_BUILD_DESCRIBE}"
# The session helper admits builddir/, controller/target/, its release/ and the
# session destination before creating anything: each must be a real directory
# of this user inside the checkout, or absent, and a missing controller/target/
# is created only beneath the admitted controller/.
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" session-start --root "${ROOT_DIR}" \
  --sdk-request-state "${SDK_REQUEST_STATE}" --sdk-request-value="${SDK_REQUEST_VALUE}" \
  --knob "BUILD_XPC=${BUILD_XPC}" --knob "PW_INSPECTION=${PW_INSPECTION}" --knob "PW_FRESH_BUILD=${PW_FRESH_BUILD}" \
  --describe "${PW_BUILD_DESCRIBE}" --commit "${PW_BUILD_COMMIT}" --version "${PW_VERSION}" --build-number "${PW_BUILD_NUMBER}"

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
# than shipping a disagreement. The SDK each output was built against is
# compared with the selected SDK separately, before assembly.
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
# any compile; DEVELOPER_DIR passes through for the toolchain choice, and a
# caller's SDKROOT names the SDK xcrun resolves instead of the macosx default
# (a developer directory whose newest SDK its own linker cannot consume is
# usable with an older one this way). The selection is checked here because
# set -e would see export's status, not xcrun's. The SDK's numeric version is
# what every shipped output must agree with; a version xcrun cannot report
# numerically never compares equal.
SDK_REQUEST="${SDK_REQUEST_VALUE:-macosx}"
SDK_SOURCE="default"
if [[ -n "${SDK_REQUEST_VALUE:-}" ]]; then
  SDK_SOURCE="caller"
fi
echo "==> Selecting the macOS SDK (xcrun --sdk ${SDK_REQUEST})"
if ! SDKROOT="$(/usr/bin/xcrun --sdk "${SDK_REQUEST}" --show-sdk-path 2>/dev/null)" || [[ ! -d "${SDKROOT}" ]]; then
  echo "ERROR: xcrun could not select the macOS SDK (DEVELOPER_DIR=${DEVELOPER_DIR:-unset}, requested ${SDK_REQUEST})" 1>&2
  exit 2
fi
export SDKROOT
if ! SDK_VERSION="$(/usr/bin/xcrun --sdk "${SDKROOT}" --show-sdk-version 2>/dev/null)" || [[ ! "${SDK_VERSION}" =~ ^[0-9]+(\.[0-9]+)*$ ]]; then
  echo "ERROR: xcrun did not report a numeric macOS SDK version (got '${SDK_VERSION:-}')" 1>&2
  exit 2
fi
echo "    ${SDKROOT} (SDK ${SDK_VERSION}, ${SDK_SOURCE} selection)"

# A build directory is trusted incremental state for this checkout and no
# other. Meson keeps compiling the source directory a build directory was set
# up for, so one configured elsewhere (copied along with a checkout, say)
# would compile that other tree and pass every later check against it. Refuse
# it here, before Cargo; the configured source check repeats the comparison.
# A configured directory is reused only under the toolchain its stamp
# records: the stamped SDK, developer directory, compiler commands and Rust
# compiler are compared with the ones selected now, and a changed, missing,
# malformed or unobservable field refuses before any compile or
# reconfiguration. Fresh mode replaces the directory instead of validating it.
echo "==> Checking the native build directory: ${MESON_BUILD_DIR}"
if [[ "${PW_FRESH_BUILD}" == "1" ]]; then
  echo "    fresh mode: the directory is replaced after admission; its reuse is not validated"
else
  if [[ -f "${MESON_BUILD_DIR}/build.ninja" ]]; then
    if ! MESON_SOURCE_DIR="$("${PW_PYTHON}" -c 'import json, os, sys; print(os.path.realpath(json.load(open(sys.argv[1]))["directories"]["source"]))' "${MESON_BUILD_DIR}/meson-info/meson-info.json" 2>/dev/null)"; then
      echo "ERROR: ${MESON_BUILD_DIR} has no readable meson-info; remove it or use a fresh build directory" 1>&2
      exit 2
    fi
    if [[ "${MESON_SOURCE_DIR}" != "$(cd "${ROOT_DIR}" && pwd -P)" ]]; then
      echo "ERROR: ${MESON_BUILD_DIR} is configured for ${MESON_SOURCE_DIR}, not this checkout (${ROOT_DIR}); remove it or use a fresh build directory" 1>&2
      exit 2
    fi
  fi
  "${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" stamp-check --root "${ROOT_DIR}" --xpc "${BUILD_XPC}"
fi

# Select and verify the signing identity: an explicit identity present in the
# login keychain. Nothing is auto-selected. The identity's class, chain, team
# and secure timestamp are verified on the signatures it makes, after the seal
# (docs/BUILD.md); the keychain listing is checked here, before Cargo runs,
# because an empty listing is also how a sandboxed harness shows a keychain
# it cannot open.
echo "==> Checking the signing identity"
IDENTITY="${IDENTITY:-}"
if [[ -z "${IDENTITY}" ]]; then
  cat <<'EOM' 1>&2
ERROR: IDENTITY is not set.

Set it to your Developer ID Application identity string, for example:
  make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'

You can find valid identities via:
  security find-identity -v -p codesigning
EOM
  exit 2
fi
# One listing, read twice: whether this identity is in it, and whether it holds any
# identity at all. An empty listing is what a sandboxed harness shows for a keychain
# it cannot open, which is a different problem from a missing identity.
IDENTITY_LISTING="$(/usr/bin/security find-identity -v -p codesigning 2>/dev/null || true)"
if ! /usr/bin/grep -Fq "\"${IDENTITY}\"" <<< "${IDENTITY_LISTING}"; then
  if /usr/bin/grep -Eq '^ *[1-9][0-9]* valid identities found' <<< "${IDENTITY_LISTING}"; then
    IDENTITY_HINT="The keychain lists other codesigning identities; set IDENTITY to one of them or install this one."
  else
    IDENTITY_HINT="The keychain listed no codesigning identities at all. Inside a sandboxed automation harness the login keychain can be unreadable; rerun the same command outside it (AGENTS.md, Sandboxed automation harnesses)."
  fi
  cat <<EOM 1>&2
ERROR: codesigning identity not found in your keychain:
  ${IDENTITY}

${IDENTITY_HINT}

Run:
  security find-identity -v -p codesigning
EOM
  exit 2
fi

# Map the public knobs onto Meson's two options; meson.build fixes every
# other native setting. Both options are passed on every configuration so a
# build directory never retains an earlier variant. RUSTFLAGS is remembered
# with the source that set it: the caller, this script, or nobody.
MESON_OPTIONS=("-Dinspection=false" "-Dxpc=false")
RUSTFLAGS_SOURCE="none"
if [[ -n "${RUSTFLAGS:-}" ]]; then
  RUSTFLAGS_SOURCE="caller"
fi
if [[ "${PW_INSPECTION}" == "1" ]]; then
  MESON_OPTIONS[0]="-Dinspection=true"
  if [[ -z "${RUSTFLAGS:-}" ]]; then
    export RUSTFLAGS="-C debuginfo=2 -C force-frame-pointers=yes -C opt-level=1"
    RUSTFLAGS_SOURCE="script"
  fi
fi
if [[ "${BUILD_XPC}" == "1" ]]; then
  MESON_OPTIONS[1]="-Dxpc=true"
fi

# Cargo keeps its intermediate release state under the pinned target directory
# unless a build-dir setting redirects it. Cargo itself reports the effective
# directory; one outside the admitted area refuses here, before any mutation,
# in incremental and fresh builds alike. Nothing outside the checkout is ever
# removed because a Cargo setting names it.
echo "==> Admitting the Cargo output and intermediate directories: ${CARGO_TARGET_DIR_PINNED}"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" cargo-admit --root "${ROOT_DIR}"

# Fresh mode replaces the three owned cache areas after read-only input, tool
# and identity admission: builddir/, controller/target/release/ and the output
# triple's release/, each a real directory of this user inside the checkout,
# with no symlink on its path. Other profiles, other triples, registry
# downloads, compiler caches elsewhere and the previous distribution outputs
# stay. A path that cannot be admitted or a removal that fails stops the
# build here.
if [[ "${PW_FRESH_BUILD}" == "1" ]]; then
  echo "==> Replacing the build caches (PW_FRESH_BUILD=1): ${MESON_BUILD_DIR} ${CARGO_TARGET_DIR_PINNED}/release ${CARGO_TARGET_DIR_PINNED}/${CARGO_OUTPUT_TRIPLE}/release"
  "${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" fresh-remove --root "${ROOT_DIR}"
fi

# ---- Build binaries --------------------------------------------------------

# Cargo is asked to report what it produced: a setting that placed an
# executable under a different directory refuses here, before a stale file at
# the pinned path could be copied in its place. The output triple is passed
# explicitly, so a lower-precedence target default is overridden, not used,
# and the controller package's build script refuses any other target. Every
# shipped output must then be a thin arm64 Mach-O for macOS, reused or not,
# before its minimum is read. Cargo's per-target reuse judgment is recorded as
# well; in fresh mode every shipped target must report rebuilding.
echo "==> Building Rust controller + tools"
rm -f "${CARGO_MESSAGES}"
PW_BUILD_VERSION="${PW_VERSION}" PW_BUILD_NUMBER="${PW_BUILD_NUMBER}" \
  PW_BUILD_DESCRIBE="${PW_BUILD_DESCRIBE}" PW_BUILD_COMMIT="${PW_BUILD_COMMIT}" \
  cargo build --manifest-path "${RUNNER_MANIFEST}" --release \
  --target "${CARGO_OUTPUT_TRIPLE}" \
  --target-dir "${CARGO_TARGET_DIR_PINNED}" \
  --message-format=json-render-diagnostics \
  --bin policy-witness \
  --bin sandbox-log-observer \
  --bin sbpl-check \
  > "${CARGO_MESSAGES}"
CARGO_BUILT="$("${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/cargo_artifacts.py" "${CARGO_MESSAGES}" policy-witness sandbox-log-observer sbpl-check)"
while IFS=$'\t' read -r bin_name bin_path; do
  case "${bin_name}" in
    policy-witness) bin_expected="${RUNNER_BIN}" ;;
    sandbox-log-observer) bin_expected="${SANDBOX_LOG_OBSERVER_BIN}" ;;
    sbpl-check) bin_expected="${SBPL_CHECK_BIN}" ;;
    *) continue ;;
  esac
  if [[ "${bin_path}" != "${bin_expected}" ]]; then
    echo "ERROR: cargo built ${bin_name} at ${bin_path}, not at ${bin_expected}; a Cargo setting or Cargo's report moved it" 1>&2
    exit 2
  fi
done <<< "${CARGO_BUILT}"

# Every shipped Cargo output must be an executable file at the pinned path:
# Cargo's path report and a parsable Mach-O do not establish the permission
# bit, and a later chmod must not repair an output this build refuses.
for rust_bin in "${RUNNER_BIN}" "${SANDBOX_LOG_OBSERVER_BIN}" "${SBPL_CHECK_BIN}"; do
  if [[ ! -x "${rust_bin}" ]]; then
    echo "ERROR: expected an executable Cargo output at ${rust_bin}" 1>&2
    exit 2
  fi
done
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" output-check --root "${ROOT_DIR}" --stage cargo \
  "${RUNNER_BIN}" "${SANDBOX_LOG_OBSERVER_BIN}" "${SBPL_CHECK_BIN}"
for rust_bin in "${RUNNER_BIN}" "${SANDBOX_LOG_OBSERVER_BIN}" "${SBPL_CHECK_BIN}"; do
  check_minimum_macos "${rust_bin}"
done
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" cargo-judge --root "${ROOT_DIR}" \
  --bin policy-witness --bin sandbox-log-observer --bin sbpl-check \
  --require-rebuilt "${PW_FRESH_BUILD}" --rustflags-source "${RUSTFLAGS_SOURCE}"

# ---- Native executables (Meson) ---------------------------------------------

# The SDK was selected above. The first build
# sets the directory up and publishes its toolchain stamp from the compilers
# Meson actually selected; later builds pass the current variants with meson
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
if ! "${PW_PYTHON}" -c 'import sys; v, m = (tuple(int(p) for p in a.split(".")) for a in sys.argv[1:3]); sys.exit(0 if v >= m else 1)' \
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
  "${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" stamp-publish --root "${ROOT_DIR}"
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
# expectation to the manifest read without a build directory. Every native
# output must then be a thin arm64 Mach-O for macOS before its minimum is read
# and before the worker is run for its identity. The stamp is then kept
# intact, or extended with the Swift compiler a reused directory discovered
# when this build enabled the XPC pieces, and every shipped output must carry
# the selected SDK.
echo "==> Checking the configured native source lists and the identity closure against the tree"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/native_sources.py" --builddir "${MESON_BUILD_DIR}" --root "${ROOT_DIR}"
NATIVE_OUTPUTS=("${SB_API_VALIDATOR_BIN}" "${PW_PROBE_RUNNER_BIN}" "${PW_EXTENSION_ISSUER_BIN}")
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
done
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" output-check --root "${ROOT_DIR}" --stage native "${NATIVE_OUTPUTS[@]}"
for native_bin in "${NATIVE_OUTPUTS[@]}"; do
  check_minimum_macos "${native_bin}"
done
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" stamp-extend --root "${ROOT_DIR}" --xpc "${BUILD_XPC}"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" sdk-check --root "${ROOT_DIR}" --sdk-version "${SDK_VERSION}" \
  "${RUNNER_BIN}" "${SANDBOX_LOG_OBSERVER_BIN}" "${SBPL_CHECK_BIN}" "${NATIVE_OUTPUTS[@]}"

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
# build seals them as part of the app bundle. The directory's presence
# was admitted before the first check.
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

# The native output loop above checked every Meson output this variant ships;
# the copies here read them without a second check, and a copy that finds its
# input gone fails on its own.
if [[ "${BUILD_XPC}" == "1" ]]; then
  echo "==> Embedding PW runner client"
  cp "${PW_RUNNER_CLIENT_BIN}" "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
  chmod +x "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
  embed_dsym "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"

  echo "==> Embedding PWRunner XPC services"
  for svc_name in "${XPC_SERVICE_NAMES[@]}"; do
    svc_dir="${XPC_SERVICES_DIR}/${svc_name}"
    svc_info="${svc_dir}/Info.plist"
    svc_host="${MESON_BUILD_DIR}/${svc_name}"
    svc_bundle="${APP_BUNDLE}/Contents/XPCServices/${svc_name}.xpc"
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
    # bundle-local resolution reason. Built-in and BYOXPC hosts resolve
    # their default validator directly inside their own service bundle.
    cp "${SB_API_VALIDATOR_BIN}" "${svc_bundle}/Contents/MacOS/sb_api_validator"
    chmod +x "${svc_bundle}/Contents/MacOS/sb_api_validator"

    # The issuer has its own ordinary authority and transient token channel.
    cp "${PW_EXTENSION_ISSUER_BIN}" "${svc_bundle}/Contents/MacOS/pw-extension-issuer"
    chmod +x "${svc_bundle}/Contents/MacOS/pw-extension-issuer"
  done
else
  echo "==> Skipping embedded XPC build (BUILD_XPC=0)"
fi

# The bundle as assembled, before any of it is signed: every Mach-O it carries,
# found by header rather than by the list of names copied in, including the
# bundle mains the seals sign, must be a thin arm64 Mach-O for macOS. The
# copies are what gets signed; this covers the interval between checking a
# compiler output and signing its copied bytes.
echo "==> Checking the assembled code against the output target: ${APP_BUNDLE}"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" output-check --root "${ROOT_DIR}" --stage assembled --app "${APP_BUNDLE}"

# ---- Codesign --------------------------------------------------------------

# Refuse an identity input edited during the build without regeneration,
# instead of signing mixed components; the build otherwise trusts the checkout
# not to change under it. The built worker must also report the generated
# identity: a worker compiled from other identity inputs and an unchanged
# generated constant can agree with the tree, so the binary is asked as well.
echo "==> Checking host/worker identity again, before signing"
"${PW_PYTHON}" -B "${ROOT_DIR}/docs/generate_worker_identity.py" --check
GENERATED_WORKER_IDENTITY="$(/usr/bin/sed -nE 's/^WORKER_IDENTITY = "([0-9a-f]{64})"$/\1/p' "${ROOT_DIR}/tests/lib/contract.py")"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" worker-identity --root "${ROOT_DIR}" \
  --worker "${PW_PROBE_RUNNER_BIN}" --expected "${GENERATED_WORKER_IDENTITY}"

# Sign one Mach-O named by the signing list. The list names exactly the
# executables this build produced, so a missing or non-Mach-O target is a
# refusal before codesign runs, never a skip and never a signature stored
# beside a file that is not code.
sign_macho() {
  local target="$1"
  if ! /usr/bin/file -b "${target}" 2>/dev/null | /usr/bin/grep -q "Mach-O"; then
    echo "ERROR: ${target} is missing or not a Mach-O; the signing list names only executables" 1>&2
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

if [[ "${BUILD_XPC}" == "1" ]]; then
  echo "==> Codesigning embedded XPC services"
  for svc_name in "${XPC_SERVICE_NAMES[@]}"; do
    svc_entitlements="${XPC_SERVICES_DIR}/${svc_name}/Entitlements.plist"
    svc_bundle="${APP_BUNDLE}/Contents/XPCServices/${svc_name}.xpc"

    # Sign embedded helpers (e.g. pw-probe-runner, sb_api_validator)
    # BEFORE sealing the bundle, so the bundle codesign records their
    # hashes. Without this, codesign may refuse to validate the
    # sealed bundle because the helpers carry no signature when the
    # seal is computed.
    sign_macho "${svc_bundle}/Contents/MacOS/pw-probe-runner"
    sign_macho "${svc_bundle}/Contents/MacOS/sb_api_validator"
    sign_macho "${svc_bundle}/Contents/MacOS/pw-extension-issuer"

    codesign --force --options runtime --timestamp \
      --entitlements "${svc_entitlements}" \
      -s "${IDENTITY}" "${svc_bundle}"
  done
fi

# Evidence generation must run after the binaries are in place and signed: the
# manifest and the provenance record describe signed bytes, and the app seal
# below covers both. The controller's final hash cannot live inside the record
# that seal covers; the release record carries it.
echo "==> Writing evidence manifest and provenance record"
"${PW_PYTHON}" "${ROOT_DIR}/tests/build-evidence.py" \
  --app-bundle "${APP_BUNDLE}" \
  --app-entitlements "${ENTITLEMENTS_PLIST}" \
  --build-session "${BUILD_SESSION}" --root "${ROOT_DIR}" --identity "${IDENTITY}"

# Sign the outer app last so the bundle is coherent.
echo "==> Codesigning app bundle"
codesign --force --options runtime --timestamp \
  --entitlements "${ENTITLEMENTS_PLIST}" \
  -s "${IDENTITY}" "${APP_BUNDLE}"

echo "==> Verifying signature + entitlements"
codesign --verify --deep --strict --verbose=2 "${APP_BUNDLE}"
codesign --display --entitlements - "${APP_BUNDLE}" >/dev/null

# Every executable under the app's and each service's Contents/MacOS, and both
# seals, must carry the named identity with the hardened runtime, the Developer
# ID chain, its team identifier and a secure timestamp, whether or not the
# signing list named the file. The linker leaves every compiler output ad
# hoc-signed, and an ad hoc executable passes the seal and the verification
# above and fails only at notarization. This check refuses it before
# packaging; the identity's class is established here, on the signatures
# made, not on the identity string. The dSYM bundles are sealed resources,
# not executables, and are not checked.
echo "==> Checking every executable's signer"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/signer_check.py" "${APP_BUNDLE}" "${IDENTITY}"

# Keep the standalone observer tool signed for direct use. Its bytes are checked
# against the output target again at this boundary: the copy in the bundle was
# checked, but this file is signed in place.
echo "==> Codesigning observer tool (not embedded)"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" output-check --root "${ROOT_DIR}" --stage observer "${SANDBOX_LOG_OBSERVER_BIN}"
sign_macho "${SANDBOX_LOG_OBSERVER_BIN}"

# ---- Package ---------------------------------------------------------------

echo "==> Staging checked user guide"
"${PW_PYTHON}" -B "${ROOT_DIR}/docs/generate_limits.py" \
  --stage-guide "${GUIDE_NAME}"

# The sealed bundle's code is checked against the output target once more, as
# packaged; nothing thins or repairs it.
echo "==> Creating zip (for notarization): ${ZIP_NAME}"
"${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/build_provenance.py" output-check --root "${ROOT_DIR}" --stage packaging --app "${APP_BUNDLE}"
rm -f "${ZIP_NAME}"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "${APP_BUNDLE}" "${ZIP_NAME}"

cat <<EOF

DONE:
  - ${APP_BUNDLE}
  - ${ZIP_NAME}
  - ${GUIDE_NAME}
  - ${SANDBOX_LOG_OBSERVER_BIN}

Next (see docs/SIGNING.md; make notarize builds again, fresh):
  make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: ...'
  # For this existing ZIP, follow the individual steps in docs/SIGNING.md.
  # Keep their receipts in one ${DIST_DIR}/evidence/<attempt>/ directory.
EOF

#!/usr/bin/env bash
set -euo pipefail

# Build and sign PolicyWitness.app with a clear, single-path flow.
#
# Inputs (environment variables):
#   IDENTITY   Developer ID Application identity string in your keychain.
#   YOLO=1     Auto-select the first Developer ID Application identity.
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

# Build knobs.
BUILD_XPC="${BUILD_XPC:-1}"
PW_INSPECTION="${PW_INSPECTION:-1}"

usage() {
  cat <<'USAGE'
usage:
  ./build.sh
  IDENTITY='Developer ID Application: ...' ./build.sh
  YOLO=1 ./build.sh
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

# Check documentation before any build/signing work; staging checks again.
echo "==> Checking limits documentation"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_limits.py" --check
echo "==> Checking contract versions"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_contract.py" --check
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_architecture.py" --check
echo "==> Generating host/worker identity"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_worker_identity.py"

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
if [[ ! "${PW_MINIMUM_MACOS}" =~ ^[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: Info.plist LSMinimumSystemVersion is not a major.minor version: '${PW_MINIMUM_MACOS}'" 1>&2
  exit 2
fi
export MACOSX_DEPLOYMENT_TARGET="${PW_MINIMUM_MACOS}"
echo "==> Supported macOS (Info.plist LSMinimumSystemVersion): ${PW_MINIMUM_MACOS}"

# A shipped Mach-O must carry that minimum; a stale output or a toolchain
# default that moved refuses here rather than shipping a disagreement.
check_minimum_macos() {
  local target="$1" minos
  minos="$(/usr/bin/otool -l "${target}" | /usr/bin/awk '/LC_BUILD_VERSION/{f=1} f&&/minos/{print $2; exit}')"
  if [[ "${minos}" != "${PW_MINIMUM_MACOS}" ]]; then
    echo "ERROR: ${target} is built for macOS ${minos:-?}; Info.plist declares ${PW_MINIMUM_MACOS}" 1>&2
    exit 2
  fi
}

# Select and verify the signing identity.
IDENTITY="${IDENTITY:-}"
if [[ -z "${IDENTITY}" ]]; then
  if [[ "${YOLO:-}" == "1" ]]; then
    IDENTITY="$(/usr/bin/security find-identity -v -p codesigning | /usr/bin/awk -F'"' '/Developer ID Application:/{print $2; exit}')"
    if [[ -z "${IDENTITY}" ]]; then
      cat <<'EOM' 1>&2
ERROR: YOLO=1 could not find a Developer ID Application identity.

Run:
  security find-identity -v -p codesigning

Then set IDENTITY explicitly or install/unlock the identity in your keychain.
EOM
      exit 2
    fi
    echo "==> Using codesign identity (YOLO=1): ${IDENTITY}"
  else
    cat <<'EOM' 1>&2
ERROR: IDENTITY is not set.

Set it to your Developer ID Application identity string, for example:
  IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' ./build.sh

Or re-run with YOLO=1 to auto-select the first Developer ID Application identity:
  YOLO=1 ./build.sh

You can find valid identities via:
  security find-identity -v -p codesigning
EOM
    exit 2
  fi
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

echo "==> Building Rust controller + tools"
PW_BUILD_VERSION="${PW_VERSION}" PW_BUILD_NUMBER="${PW_BUILD_NUMBER}" \
  PW_BUILD_DESCRIBE="${PW_BUILD_DESCRIBE}" PW_BUILD_COMMIT="${PW_BUILD_COMMIT}" \
  cargo build --manifest-path "${RUNNER_MANIFEST}" --release \
  --bin policy-witness \
  --bin sandbox-log-observer \
  --bin sbpl-check

RUNNER_BIN="${ROOT_DIR}/controller/target/release/policy-witness"
SANDBOX_LOG_OBSERVER_BIN="${ROOT_DIR}/controller/target/release/sandbox-log-observer"
SBPL_CHECK_BIN="${ROOT_DIR}/controller/target/release/sbpl-check"
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
# ---- Native executables (Meson) ---------------------------------------------

# SDKROOT selects the macOS SDK the way the former xcrun --sdk macosx calls
# did; DEVELOPER_DIR passes through for the toolchain choice. The first build
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
if ! command -v meson >/dev/null 2>&1 || ! command -v ninja >/dev/null 2>&1; then
  echo "ERROR: meson and ninja are required for the native build (brew install meson ninja); see docs/SIGNING.md" 1>&2
  exit 2
fi
export SDKROOT="$(/usr/bin/xcrun --sdk macosx --show-sdk-path)"
if [[ -f "${MESON_BUILD_DIR}/build.ninja" ]]; then
  echo "==> Configuring native build (meson configure, existing directory): ${MESON_OPTIONS[*]}"
  meson configure "${MESON_BUILD_DIR}" "${MESON_OPTIONS[@]}"
else
  echo "==> Configuring native build (meson setup, fresh directory): ${MESON_BUILD_DIR} ${MESON_OPTIONS[*]}"
  meson setup "${MESON_BUILD_DIR}" "${ROOT_DIR}" "${MESON_OPTIONS[@]}"
fi
echo "==> Compiling native executables"
meson compile -C "${MESON_BUILD_DIR}"
for native_bin in "${SB_API_VALIDATOR_BIN}" "${PW_PROBE_RUNNER_BIN}"; do
  if [[ ! -x "${native_bin}" ]]; then
    echo "ERROR: expected Meson output at ${native_bin}" 1>&2
    exit 2
  fi
done

# ---- Assemble app bundle ---------------------------------------------------

echo "==> Assembling app bundle: ${APP_BUNDLE}"
mkdir -p "${DIST_DIR}"
for document in README.md AGENTS.md; do
  if [[ ! "${ROOT_DIR}/dist/${document}" -ef "${DIST_DIR}/${document}" ]]; then
    cp "${ROOT_DIR}/dist/${document}" "${DIST_DIR}/${document}"
  fi
done
rm -rf "${APP_BUNDLE}"
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
for rust_bin in policy-witness sandbox-log-observer sbpl-check; do
  check_minimum_macos "${APP_BUNDLE}/Contents/MacOS/${rust_bin}"
done

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
  if [[ ! -x "${PW_RUNNER_CLIENT_BIN}" ]]; then
    echo "ERROR: expected Meson output at ${PW_RUNNER_CLIENT_BIN}" 1>&2
    exit 2
  fi
  echo "==> Embedding PW runner client"
  cp "${PW_RUNNER_CLIENT_BIN}" "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
  chmod +x "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
  check_minimum_macos "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
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
    for svc_bin in "${svc_name}" pw-probe-runner sb_api_validator; do
      check_minimum_macos "${svc_bundle}/Contents/MacOS/${svc_bin}"
    done
  done
else
  echo "==> Skipping embedded XPC build (BUILD_XPC=0)"
fi

# ---- Codesign --------------------------------------------------------------

# Refuse a source edit during compilation instead of signing mixed components.
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_worker_identity.py" --check

if [[ ! -f "${ENTITLEMENTS_PLIST}" ]]; then
  echo "ERROR: missing entitlements plist: ${ENTITLEMENTS_PLIST}" 1>&2
  exit 2
fi

# Sign a Mach-O binary if it exists; ignore non-binaries.
sign_macho() {
  local target="$1"
  if [[ ! -e "${target}" ]]; then
    return 0
  fi
  if /usr/bin/file -b "${target}" | /usr/bin/grep -q "Mach-O"; then
    codesign --force --options runtime --timestamp -s "${IDENTITY}" "${target}"
  fi
}

echo "==> Codesigning embedded MacOS tools"
sign_macho "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
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

# Keep the standalone observer tool signed for direct use.
echo "==> Codesigning observer tool (not embedded)"
sign_macho "${SANDBOX_LOG_OBSERVER_BIN}"

# ---- Package ---------------------------------------------------------------

echo "==> Staging checked user guide"
/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_limits.py" \
  --stage-guide "${DIST_DIR}/PolicyWitness.md"

echo "==> Creating zip (for notarization): ${ZIP_NAME}"
rm -f "${ZIP_NAME}"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "${APP_BUNDLE}" "${ZIP_NAME}"

cat <<EOF

DONE:
  - ${APP_BUNDLE}
  - ${ZIP_NAME}
  - ${DIST_DIR}/PolicyWitness.md
  - ${SANDBOX_LOG_OBSERVER_BIN}

Next (see docs/SIGNING.md; make notarize builds again):
  make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail YOLO=1
  # For this existing ZIP, follow the individual steps in docs/SIGNING.md.
  # Keep their receipts in one ${DIST_DIR}/evidence/<attempt>/ directory.
EOF

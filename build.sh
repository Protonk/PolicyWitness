#!/usr/bin/env bash
set -euo pipefail

# Build and sign PolicyWitness.app with a clear, single-path flow.
#
# Inputs (environment variables):
#   IDENTITY   Developer ID Application identity string in your keychain.
#   YOLO=1     Auto-select the first Developer ID Application identity.
#   BUILD_XPC  Set to 0 to skip building the embedded XPC service/client.
#   PW_INSPECTION=1  Keep debug info and frame pointers (default).
#   SWIFT_MODULE_CACHE  Writable path for Swift module cache (default: .tmp/swift-module-cache).
#
# Outputs:
#   dist/PolicyWitness.app
#   dist/PolicyWitness.zip (ready for notarization)

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
XPC_RUNNER_API_FILE="${XPC_ROOT}/PWRunnerAPI.swift"
XPC_RUNNER_SANDBOX_LIB_FILE="${XPC_ROOT}/SandboxLib.swift"
XPC_RUNNER_SANDBOX_APPLY_FILE="${XPC_ROOT}/SandboxApply.swift"
XPC_RUNNER_INSTRUMENTATION_FILE="${XPC_ROOT}/Instrumentation.swift"
XPC_RUNNER_PROBE_RUNNER_FILE="${XPC_ROOT}/ProbeRunner.swift"
XPC_RUNNER_PATH_UTILS_FILE="${XPC_ROOT}/PathUtils.swift"
XPC_RUNNER_SIGNALS_FILE="${XPC_ROOT}/Signals.swift"
XPC_RUNNER_SERVICE_FILE="${XPC_ROOT}/PWRunnerService.swift"
XPC_RUNNER_SANDBOX_SHIM="${XPC_ROOT}/PWSandboxCheckShim.c"
XPC_RUNNER_CLIENT_MAIN="${XPC_ROOT}/runner-client/main.swift"
XPC_SERVICES_DIR="${XPC_ROOT}/services"
XPC_SERVICE_NAMES=("PWRunner" "PWRunnerDebug")

# Host-side sandbox_check cross-check helper.
SB_API_VALIDATOR_DIR="${ROOT_DIR}/controller/tools/sb_api_validator"
SB_API_VALIDATOR_SRC="${SB_API_VALIDATOR_DIR}/sb_api_validator.c"
SB_API_VALIDATOR_BIN="${SB_API_VALIDATOR_DIR}/sb_api_validator"

# Build knobs.
BUILD_XPC="${BUILD_XPC:-1}"
PW_INSPECTION="${PW_INSPECTION:-1}"
# Swift module cache must be writable; sandboxed environments often block ~/.cache.
SWIFT_MODULE_CACHE="${SWIFT_MODULE_CACHE:-${ROOT_DIR}/.tmp/swift-module-cache}"

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

# Build flags tuned for inspection vs optimized builds.
SWIFT_FLAGS=()
if [[ "${PW_INSPECTION}" == "1" ]]; then
  SWIFT_FLAGS+=("-Onone" "-g")
  if [[ -z "${RUSTFLAGS:-}" ]]; then
    export RUSTFLAGS="-C debuginfo=2 -C force-frame-pointers=yes -C opt-level=1"
  fi
else
  SWIFT_FLAGS+=("-O")
fi

# ---- Build binaries --------------------------------------------------------

echo "==> Building Rust controller + tools"
cargo build --manifest-path "${RUNNER_MANIFEST}" --release \
  --bin policy-witness \
  --bin sandbox-log-observer \
  --bin sbpl-preflight

RUNNER_BIN="${ROOT_DIR}/controller/target/release/policy-witness"
SANDBOX_LOG_OBSERVER_BIN="${ROOT_DIR}/controller/target/release/sandbox-log-observer"
SBPL_PREFLIGHT_BIN="${ROOT_DIR}/controller/target/release/sbpl-preflight"
if [[ ! -x "${RUNNER_BIN}" ]]; then
  echo "ERROR: expected policy-witness binary at ${RUNNER_BIN}" 1>&2
  exit 2
fi
if [[ ! -x "${SANDBOX_LOG_OBSERVER_BIN}" ]]; then
  echo "ERROR: expected sandbox-log-observer binary at ${SANDBOX_LOG_OBSERVER_BIN}" 1>&2
  exit 2
fi
if [[ ! -x "${SBPL_PREFLIGHT_BIN}" ]]; then
  echo "ERROR: expected sbpl-preflight binary at ${SBPL_PREFLIGHT_BIN}" 1>&2
  exit 2
fi
if [[ ! -f "${SB_API_VALIDATOR_SRC}" ]]; then
  echo "ERROR: missing sb_api_validator source at ${SB_API_VALIDATOR_SRC}" 1>&2
  exit 2
fi

echo "==> Building sb_api_validator"
/usr/bin/xcrun --sdk macosx clang -Wall -Wextra -O2 -std=c11 \
  -o "${SB_API_VALIDATOR_BIN}" "${SB_API_VALIDATOR_SRC}"
if [[ ! -x "${SB_API_VALIDATOR_BIN}" ]]; then
  echo "ERROR: expected sb_api_validator binary at ${SB_API_VALIDATOR_BIN}" 1>&2
  exit 2
fi

# ---- Assemble app bundle ---------------------------------------------------

echo "==> Assembling app bundle: ${APP_BUNDLE}"
mkdir -p "${DIST_DIR}"
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS" "${APP_BUNDLE}/Contents/Resources"

if [[ ! -f "${INFO_PLIST_TEMPLATE}" ]]; then
  echo "ERROR: missing ${INFO_PLIST_TEMPLATE} at repo root" 1>&2
  exit 2
fi
cp "${INFO_PLIST_TEMPLATE}" "${APP_BUNDLE}/Contents/Info.plist"

cp "${RUNNER_BIN}" "${APP_BUNDLE}/Contents/MacOS/policy-witness"
chmod +x "${APP_BUNDLE}/Contents/MacOS/policy-witness"

cp "${SANDBOX_LOG_OBSERVER_BIN}" "${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer"
chmod +x "${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer"

cp "${SBPL_PREFLIGHT_BIN}" "${APP_BUNDLE}/Contents/MacOS/sbpl-preflight"
chmod +x "${APP_BUNDLE}/Contents/MacOS/sbpl-preflight"

cp "${SB_API_VALIDATOR_BIN}" "${APP_BUNDLE}/Contents/MacOS/sb_api_validator"
chmod +x "${APP_BUNDLE}/Contents/MacOS/sb_api_validator"

# ---- Build embedded XPC components ----------------------------------------

if [[ "${BUILD_XPC}" == "1" ]]; then
  SWIFTC_PATH="$(/usr/bin/xcrun --sdk macosx --find swiftc 2>/dev/null || true)"
  if [[ -z "${SWIFTC_PATH}" ]]; then
    echo "ERROR: BUILD_XPC=1 but swiftc was not found (install Xcode Command Line Tools)" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_API_FILE}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_API_FILE}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_SANDBOX_LIB_FILE}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_SANDBOX_LIB_FILE}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_SANDBOX_APPLY_FILE}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_SANDBOX_APPLY_FILE}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_INSTRUMENTATION_FILE}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_INSTRUMENTATION_FILE}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_PROBE_RUNNER_FILE}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_PROBE_RUNNER_FILE}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_PATH_UTILS_FILE}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_PATH_UTILS_FILE}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_SIGNALS_FILE}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_SIGNALS_FILE}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_SERVICE_FILE}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_SERVICE_FILE}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_SANDBOX_SHIM}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_SANDBOX_SHIM}" 1>&2
    exit 2
  fi
  if [[ ! -f "${XPC_RUNNER_CLIENT_MAIN}" ]]; then
    echo "ERROR: missing ${XPC_RUNNER_CLIENT_MAIN}" 1>&2
    exit 2
  fi

  echo "==> Building embedded PW runner client"
  mkdir -p "${SWIFT_MODULE_CACHE}"
  /usr/bin/xcrun --sdk macosx swiftc \
    -module-cache-path "${SWIFT_MODULE_CACHE}" \
    "${SWIFT_FLAGS[@]}" \
    -o "${APP_BUNDLE}/Contents/MacOS/pw-runner-client" \
    "${XPC_RUNNER_API_FILE}" "${XPC_RUNNER_CLIENT_MAIN}"
  chmod +x "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"

  echo "==> Building embedded PWRunner XPC services"
  shim_obj="${SWIFT_MODULE_CACHE}/PWSandboxCheckShim.o"
  /usr/bin/xcrun --sdk macosx clang -c "${XPC_RUNNER_SANDBOX_SHIM}" -o "${shim_obj}"
  for svc_name in "${XPC_SERVICE_NAMES[@]}"; do
    svc_dir="${XPC_SERVICES_DIR}/${svc_name}"
    svc_info="${svc_dir}/Info.plist"
    svc_main="${svc_dir}/main.swift"
    svc_bundle="${APP_BUNDLE}/Contents/XPCServices/${svc_name}.xpc"
    if [[ ! -d "${svc_dir}" ]]; then
      echo "ERROR: missing ${svc_name} service dir at ${svc_dir}" 1>&2
      exit 2
    fi
    if [[ ! -f "${svc_info}" ]] || [[ ! -f "${svc_main}" ]]; then
      echo "ERROR: ${svc_name} service is missing Info.plist or main.swift" 1>&2
      exit 2
    fi
    mkdir -p "${svc_bundle}/Contents/MacOS"
    cp "${svc_info}" "${svc_bundle}/Contents/Info.plist"

    /usr/bin/xcrun --sdk macosx swiftc \
      -module-cache-path "${SWIFT_MODULE_CACHE}" \
      "${SWIFT_FLAGS[@]}" \
      -o "${svc_bundle}/Contents/MacOS/${svc_name}" \
      "${XPC_RUNNER_API_FILE}" \
      "${XPC_RUNNER_SANDBOX_LIB_FILE}" \
      "${XPC_RUNNER_SANDBOX_APPLY_FILE}" \
      "${XPC_RUNNER_INSTRUMENTATION_FILE}" \
      "${XPC_RUNNER_PROBE_RUNNER_FILE}" \
      "${XPC_RUNNER_PATH_UTILS_FILE}" \
      "${XPC_RUNNER_SIGNALS_FILE}" \
      "${XPC_RUNNER_SERVICE_FILE}" \
      "${svc_main}" "${shim_obj}"
    chmod +x "${svc_bundle}/Contents/MacOS/${svc_name}"
  done
else
  echo "==> Skipping embedded XPC build (BUILD_XPC=0)"
fi

# ---- Codesign --------------------------------------------------------------

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
sign_macho "${APP_BUNDLE}/Contents/MacOS/sbpl-preflight"
sign_macho "${APP_BUNDLE}/Contents/MacOS/sb_api_validator"

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

echo "==> Creating zip (for notarization): ${ZIP_NAME}"
rm -f "${ZIP_NAME}"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "${APP_BUNDLE}" "${ZIP_NAME}"

cat <<EOF

DONE:
  - ${APP_BUNDLE}
  - ${ZIP_NAME}
  - ${SANDBOX_LOG_OBSERVER_BIN}

Next (notarize with your saved profile):
  make notarize NOTARY_KEYCHAIN_PROFILE=dev-profile
  # or manually:
  xcrun notarytool submit "${ZIP_NAME}" --keychain-profile "dev-profile" --wait
  xcrun stapler staple "${APP_BUNDLE}"
  xcrun stapler validate -v "${APP_BUNDLE}"
  spctl -a -vv --type execute "${APP_BUNDLE}"
  /usr/bin/ditto -c -k --sequesterRsrc --keepParent "${APP_BUNDLE}" "${ZIP_NAME}"
EOF

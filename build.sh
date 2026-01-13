#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./build.sh
#   IDENTITY='Developer ID Application: ...' ./build.sh
#   PW_INSPECTION=0 IDENTITY='Developer ID Application: ...' ./build.sh
#
# Produces:
#   PolicyWitness.app
#   PolicyWitness.zip  (ready for notarytool submit)

APP_NAME="PolicyWitness"
APP_BUNDLE="${APP_NAME}.app"
ZIP_NAME="${APP_NAME}.zip"

# Paths in this repo
RUNNER_MANIFEST="runner/Cargo.toml"
ENTITLEMENTS_PLIST="PolicyWitness.entitlements"
INHERIT_ENTITLEMENTS_PLIST="PolicyWitness.inherit.entitlements"
BAD_INHERIT_ENTITLEMENTS_PLIST="PolicyWitness.inherit.bad.entitlements"
INSPECTOR_ENTITLEMENTS_PLIST="Inspector.entitlements"
INFO_PLIST_TEMPLATE="Info.plist"

# Optional: embed extra payloads if present
EMBED_FENCERUNNER_PATH="${EMBED_FENCERUNNER_PATH:-}"   # e.g. /path/to/fencerunner
EMBED_PROBES_DIR="${EMBED_PROBES_DIR:-}"               # e.g. /path/to/probes
BUILD_XPC="${BUILD_XPC:-1}"                            # set to 0 to skip building embedded XPC services/client

# XPC source layout (in this repo)
XPC_ROOT="xpc"
XPC_RUNNER_API_FILE="${XPC_ROOT}/PWRunnerAPI.swift"
XPC_RUNNER_SERVICE_HOST_FILE="${XPC_ROOT}/PWRunnerServiceHost.swift"
XPC_RUNNER_CLIENT_MAIN="${XPC_ROOT}/runner-client/main.swift"
XPC_SERVICES_DIR="${XPC_ROOT}/services"
# Swift/Clang module cache must be writable; the harness sandbox often blocks the default path under ~/.cache.
SWIFT_MODULE_CACHE="${SWIFT_MODULE_CACHE:-.tmp/swift-module-cache}"
SWIFT_OPT_LEVEL="${SWIFT_OPT_LEVEL:-}"
SWIFT_DEBUG_FLAGS="${SWIFT_DEBUG_FLAGS:-}"
PW_INSPECTION="${PW_INSPECTION:-1}"

if [[ "${PW_INSPECTION}" == "1" ]]; then
  if [[ -z "${SWIFT_OPT_LEVEL}" ]]; then
    SWIFT_OPT_LEVEL="-Onone"
  fi
  if [[ -z "${SWIFT_DEBUG_FLAGS}" ]]; then
    SWIFT_DEBUG_FLAGS="-g"
  fi
  if [[ -z "${RUSTFLAGS:-}" ]]; then
    export RUSTFLAGS="-C debuginfo=2 -C force-frame-pointers=yes -C opt-level=1"
  fi
fi

if [[ -z "${SWIFT_OPT_LEVEL}" ]]; then
  SWIFT_OPT_LEVEL="-O"
fi

# Signing identity. Prefer env override; otherwise require user to set it.
IDENTITY="${IDENTITY:-}"

if [[ -z "${IDENTITY}" ]]; then
  cat <<'EOF' 1>&2
ERROR: IDENTITY is not set.

Set it to your Developer ID Application identity string, for example:
  IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' ./build.sh

You can find valid identities via:
  security find-identity -v -p codesigning
EOF
  exit 2
fi

if ! /usr/bin/security find-identity -v -p codesigning 2>/dev/null | /usr/bin/grep -Fq "\"${IDENTITY}\""; then
  cat <<EOF 1>&2
ERROR: codesigning identity not found in your keychain:
  ${IDENTITY}

Run:
  security find-identity -v -p codesigning

Then ensure the identity is installed/unlocked (or set IDENTITY to one of the listed identities).
EOF
  exit 2
fi

validate_injectable_overlay() {
  :
}

merge_entitlements() {
  :
}

entitlements_is_empty() {
  local plist_path="$1"
  /usr/bin/python3 - "${plist_path}" <<'PY'
import plistlib
import sys

path = sys.argv[1]
with open(path, "rb") as fh:
    data = plistlib.load(fh)
if not isinstance(data, dict):
    sys.exit(2)
sys.exit(0 if len(data.keys()) == 0 else 1)
PY
}

echo "==> Building Rust runner + tools"
cargo build --manifest-path "${RUNNER_MANIFEST}" --release \
  --bin policy-witness \
  --bin quarantine-observer \
  --bin sandbox-log-observer \
  --bin signpost-log-observer \
  --bin pw-inspector

# Find the built binary. (Assumes standard Cargo layout.)
RUNNER_BIN="runner/target/release/policy-witness"
if [[ ! -x "${RUNNER_BIN}" ]]; then
  echo "ERROR: expected policy-witness binary at ${RUNNER_BIN}" 1>&2
  exit 2
fi
QUARANTINE_OBSERVER_BIN="runner/target/release/quarantine-observer"
if [[ ! -x "${QUARANTINE_OBSERVER_BIN}" ]]; then
  echo "ERROR: expected quarantine-observer binary at ${QUARANTINE_OBSERVER_BIN}" 1>&2
  exit 2
fi
SANDBOX_LOG_OBSERVER_BIN="runner/target/release/sandbox-log-observer"
if [[ ! -x "${SANDBOX_LOG_OBSERVER_BIN}" ]]; then
  echo "ERROR: expected sandbox-log-observer binary at ${SANDBOX_LOG_OBSERVER_BIN}" 1>&2
  exit 2
fi
SIGNPOST_LOG_OBSERVER_BIN="runner/target/release/signpost-log-observer"
if [[ ! -x "${SIGNPOST_LOG_OBSERVER_BIN}" ]]; then
  echo "ERROR: expected signpost-log-observer binary at ${SIGNPOST_LOG_OBSERVER_BIN}" 1>&2
  exit 2
fi
PW_INSPECTOR_BIN="runner/target/release/pw-inspector"
if [[ ! -x "${PW_INSPECTOR_BIN}" ]]; then
  echo "ERROR: expected pw-inspector binary at ${PW_INSPECTOR_BIN}" 1>&2
  exit 2
fi

echo "==> Assembling app bundle: ${APP_BUNDLE}"
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Helpers"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

# Copy Info.plist
if [[ ! -f "${INFO_PLIST_TEMPLATE}" ]]; then
  echo "ERROR: missing ${INFO_PLIST_TEMPLATE} at repo root" 1>&2
  exit 2
fi
cp "${INFO_PLIST_TEMPLATE}" "${APP_BUNDLE}/Contents/Info.plist"

# Install main executable
cp "${RUNNER_BIN}" "${APP_BUNDLE}/Contents/MacOS/policy-witness"
chmod +x "${APP_BUNDLE}/Contents/MacOS/policy-witness"

# Embed observer tooling (runs outside the App Sandbox boundary when launched from Terminal)
cp "${SANDBOX_LOG_OBSERVER_BIN}" "${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer"
chmod +x "${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer"
cp "${SIGNPOST_LOG_OBSERVER_BIN}" "${APP_BUNDLE}/Contents/MacOS/signpost-log-observer"
chmod +x "${APP_BUNDLE}/Contents/MacOS/signpost-log-observer"

# Optional: embed fencerunner
if [[ -n "${EMBED_FENCERUNNER_PATH}" ]]; then
  if [[ ! -x "${EMBED_FENCERUNNER_PATH}" ]]; then
    echo "ERROR: EMBED_FENCERUNNER_PATH is set but not executable: ${EMBED_FENCERUNNER_PATH}" 1>&2
    exit 2
  fi
  echo "==> Embedding fencerunner: ${EMBED_FENCERUNNER_PATH}"
  cp "${EMBED_FENCERUNNER_PATH}" "${APP_BUNDLE}/Contents/Helpers/fencerunner"
  chmod +x "${APP_BUNDLE}/Contents/Helpers/fencerunner"
fi

# Optional: embed probes directory
if [[ -n "${EMBED_PROBES_DIR}" ]]; then
  if [[ ! -d "${EMBED_PROBES_DIR}" ]]; then
    echo "ERROR: EMBED_PROBES_DIR is set but not a directory: ${EMBED_PROBES_DIR}" 1>&2
    exit 2
  fi
  echo "==> Embedding probes dir: ${EMBED_PROBES_DIR}"
  mkdir -p "${APP_BUNDLE}/Contents/Helpers/Probes"
  rsync -a --delete "${EMBED_PROBES_DIR}/" "${APP_BUNDLE}/Contents/Helpers/Probes/"
fi

# Optional: build and embed XPC services + client
if [[ "${BUILD_XPC}" == "1" ]]; then
  SWIFTC_PATH="$(/usr/bin/xcrun --sdk macosx --find swiftc 2>/dev/null || true)"
  if [[ -z "${SWIFTC_PATH}" ]]; then
    echo "ERROR: BUILD_XPC=1 but swiftc was not found (install Xcode Command Line Tools)" 1>&2
    exit 2
  fi
  SWIFTC=(/usr/bin/xcrun --sdk macosx swiftc)
  if [[ ! -f "${XPC_RUNNER_API_FILE}" ]] || [[ ! -f "${XPC_RUNNER_SERVICE_HOST_FILE}" ]] || [[ ! -f "${XPC_RUNNER_CLIENT_MAIN}" ]]; then
    echo "ERROR: BUILD_XPC=1 but XPC sources are missing under ${XPC_ROOT}/" 1>&2
    exit 2
  fi

  echo "==> Building embedded PW runner client"
  mkdir -p "${SWIFT_MODULE_CACHE}"
  SWIFT_FLAGS=("${SWIFT_OPT_LEVEL}")
  if [[ -n "${SWIFT_DEBUG_FLAGS}" ]]; then
    SWIFT_FLAGS+=("${SWIFT_DEBUG_FLAGS}")
  fi
  if [[ "${PW_LAB_BUILD:-}" == "1" ]]; then
    SWIFT_FLAGS+=("-D" "PW_LAB_ENABLED")
  fi
  "${SWIFTC[@]}" -module-cache-path "${SWIFT_MODULE_CACHE}" "${SWIFT_FLAGS[@]}" -o "${APP_BUNDLE}/Contents/MacOS/pw-runner-client" "${XPC_RUNNER_API_FILE}" "${XPC_RUNNER_CLIENT_MAIN}"
  chmod +x "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"

  echo "==> Building embedded PWRunner XPC service"
  svc_dir="${XPC_SERVICES_DIR}/PWRunner"
  svc_info="${svc_dir}/Info.plist"
  svc_main="${svc_dir}/main.swift"
  svc_bundle="${APP_BUNDLE}/Contents/XPCServices/PWRunner.xpc"
  if [[ ! -d "${svc_dir}" ]]; then
    echo "ERROR: missing PWRunner service dir at ${svc_dir}" 1>&2
    exit 2
  fi
  if [[ ! -f "${svc_info}" ]] || [[ ! -f "${svc_main}" ]]; then
    echo "ERROR: PWRunner service is missing Info.plist or main.swift" 1>&2
    exit 2
  fi
  mkdir -p "${svc_bundle}/Contents/MacOS"
  cp "${svc_info}" "${svc_bundle}/Contents/Info.plist"
  "${SWIFTC[@]}" -module-cache-path "${SWIFT_MODULE_CACHE}" "${SWIFT_FLAGS[@]}" -o "${svc_bundle}/Contents/MacOS/PWRunner" "${XPC_RUNNER_API_FILE}" "${XPC_RUNNER_SERVICE_HOST_FILE}" "${svc_main}"
  chmod +x "${svc_bundle}/Contents/MacOS/PWRunner"
fi

# Sanity check entitlements
if [[ ! -f "${ENTITLEMENTS_PLIST}" ]]; then
  echo "ERROR: missing entitlements plist: ${ENTITLEMENTS_PLIST}" 1>&2
  exit 2
fi
if [[ ! -f "${INHERIT_ENTITLEMENTS_PLIST}" ]]; then
  echo "ERROR: missing inherit entitlements plist: ${INHERIT_ENTITLEMENTS_PLIST}" 1>&2
  exit 2
fi
if [[ ! -f "${BAD_INHERIT_ENTITLEMENTS_PLIST}" ]]; then
  echo "ERROR: missing bad inherit entitlements plist: ${BAD_INHERIT_ENTITLEMENTS_PLIST}" 1>&2
  exit 2
fi
if [[ ! -f "${INSPECTOR_ENTITLEMENTS_PLIST}" ]]; then
  echo "ERROR: missing inspector entitlements plist: ${INSPECTOR_ENTITLEMENTS_PLIST}" 1>&2
  exit 2
fi

sign_macho_inherit() {
  local target="$1"
  local identifier="${2:-}"
  if [[ ! -e "${target}" ]]; then
    return 0
  fi
  if /usr/bin/file -b "${target}" | /usr/bin/grep -q "Mach-O"; then
    codesign \
      --force \
      --options runtime \
      --timestamp \
      --entitlements "${INHERIT_ENTITLEMENTS_PLIST}" \
      ${identifier:+--identifier "${identifier}"} \
      -s "${IDENTITY}" \
      "${target}"
  fi
}

sign_macho_inherit_bad() {
  local target="$1"
  local identifier="${2:-}"
  if [[ ! -e "${target}" ]]; then
    return 0
  fi
  if /usr/bin/file -b "${target}" | /usr/bin/grep -q "Mach-O"; then
    codesign \
      --force \
      --options runtime \
      --timestamp \
      --entitlements "${BAD_INHERIT_ENTITLEMENTS_PLIST}" \
      ${identifier:+--identifier "${identifier}"} \
      -s "${IDENTITY}" \
      "${target}"
  fi
}

sign_macho_plain() {
  local target="$1"
  if [[ ! -e "${target}" ]]; then
    return 0
  fi
  if /usr/bin/file -b "${target}" | /usr/bin/grep -q "Mach-O"; then
    codesign \
      --force \
      --options runtime \
      --timestamp \
      -s "${IDENTITY}" \
      "${target}"
  fi
}

sign_macho_entitlements() {
  local target="$1"
  local entitlements="$2"
  if [[ ! -e "${target}" ]]; then
    return 0
  fi
  if /usr/bin/file -b "${target}" | /usr/bin/grep -q "Mach-O"; then
    codesign \
      --force \
      --options runtime \
      --timestamp \
      --entitlements "${entitlements}" \
      -s "${IDENTITY}" \
      "${target}"
  fi
}

echo "==> Codesigning embedded helper tools (plain; unsandboxed host-side)"
if [[ -d "${APP_BUNDLE}/Contents/Helpers" ]]; then
  while IFS= read -r -d '' f; do
    sign_macho_plain "${f}"
  done < <(find "${APP_BUNDLE}/Contents/Helpers" -type f -print0)
fi

echo "==> Codesigning embedded MacOS tools (plain; unsandboxed host-side)"
sign_macho_plain "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"
sign_macho_plain "${APP_BUNDLE}/Contents/MacOS/sandbox-log-observer"
sign_macho_plain "${APP_BUNDLE}/Contents/MacOS/signpost-log-observer"

echo "==> Codesigning embedded XPC services"
if [[ "${BUILD_XPC}" == "1" ]] && [[ -d "${XPC_SERVICES_DIR}" ]]; then
  svc_dir="${XPC_SERVICES_DIR}/PWRunner"
  svc_entitlements="${svc_dir}/Entitlements.plist"
  svc_bundle="${APP_BUNDLE}/Contents/XPCServices/PWRunner.xpc"
  if [[ ! -d "${svc_bundle}" ]]; then
    echo "ERROR: expected XPC service bundle at ${svc_bundle}" 1>&2
    exit 2
  fi
  if [[ ! -f "${svc_entitlements}" ]]; then
    echo "ERROR: PWRunner service is missing Entitlements.plist at ${svc_entitlements}" 1>&2
    exit 2
  fi
  codesign \
    --force \
    --options runtime \
    --timestamp \
    --entitlements "${svc_entitlements}" \
    -s "${IDENTITY}" \
    "${svc_bundle}"
fi

echo "==> Writing evidence manifest (signed BOM)"
/usr/bin/python3 "tests/build-evidence.py" \
  --app-bundle "${APP_BUNDLE}" \
  --app-entitlements "${ENTITLEMENTS_PLIST}"

echo "==> Codesigning (Developer ID + hardened runtime + entitlements)"
# Sign nested code first if you embed anything executable beyond the main binary.
codesign \
  --force \
  --options runtime \
  --timestamp \
  --entitlements "${ENTITLEMENTS_PLIST}" \
  -s "${IDENTITY}" \
  "${APP_BUNDLE}"

echo "==> Verifying signature + entitlements"
codesign --verify --deep --strict --verbose=2 "${APP_BUNDLE}"
codesign --display --entitlements - "${APP_BUNDLE}" >/dev/null

echo "==> Codesigning observer tools (not embedded)"
sign_macho_plain "${QUARANTINE_OBSERVER_BIN}"
sign_macho_plain "${SANDBOX_LOG_OBSERVER_BIN}"
sign_macho_plain "${SIGNPOST_LOG_OBSERVER_BIN}"
sign_macho_entitlements "${PW_INSPECTOR_BIN}" "${INSPECTOR_ENTITLEMENTS_PLIST}"

echo "==> Creating zip (for notarization): ${ZIP_NAME}"
rm -f "${ZIP_NAME}"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "${APP_BUNDLE}" "${ZIP_NAME}"

echo
echo "DONE:"
echo "  - ${APP_BUNDLE}"
echo "  - ${ZIP_NAME}"
echo "  - ${QUARANTINE_OBSERVER_BIN}"
echo "  - ${SANDBOX_LOG_OBSERVER_BIN}"
echo "  - ${SIGNPOST_LOG_OBSERVER_BIN}"
echo "  - ${PW_INSPECTOR_BIN}"
echo
echo "Next (notarize with your saved profile):"
cat <<EOF
  xcrun notarytool submit "${ZIP_NAME}" --keychain-profile "dev-profile" --wait
  xcrun stapler staple "${APP_BUNDLE}"
  xcrun stapler validate -v "${APP_BUNDLE}"
  spctl -a -vv --type execute "${APP_BUNDLE}"
EOF

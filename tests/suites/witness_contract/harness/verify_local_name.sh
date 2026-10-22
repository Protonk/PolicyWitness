#!/usr/bin/env bash
#
# verify_local_name.sh — establish what the SBPL mach-lookup `local-name`
# filter governs on this host, then compare sandbox_check filter IDs with it.
#
# The global-name method in verify_filter_id.sh needs a lookup the kernel
# denies under the policy. local-name has no such lookup until a reachable
# local namespace is found, so this driver first observes native lookups of a
# target and an independently exercised sibling under controlled policies in
# two tested registration/bundle arrangements:
#
#   registered / registered-after   names the process registers itself
#   bundle                           an embedded XPC service looked up from a
#                                    disposable app bundle's own domain
#
# For each namespace it runs allow-default with a local-name deny, a
# global-name deny, and an unfiltered deny, plus deny-default with a
# local-name or global-name allow of the sibling. It then holds a probe under
# the local-name deny and scans sandbox_check IDs 1..<max> for the target and
# the sibling. The output is the evidence; the operator decides the
# disposition and records it in VERIFICATIONS.md. Nothing is a PolicyWitness
# result, and the result describes this host only.
#
# Usage: verify_local_name.sh [--max-id N] [--keep] [--out FRESH_DIRECTORY]
set -euo pipefail
ulimit -c 0  # Unknown RAW filter IDs may crash the standalone validator.

MAX_ID=200
KEEP=0
OUT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --max-id) MAX_ID="$2"; shift 2 ;;
        --keep) KEEP=1; shift ;;
        --out) OUT="$2"; shift 2 ;;
        -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done
if [[ -n "${OUT}" ]]; then mkdir "${OUT}"; else OUT="$(mktemp -d "${TMPDIR:-/tmp}/pw-local-name.XXXXXX")"; fi
OUT="$(cd "${OUT}" && pwd)"
mkdir "${OUT}/raw"
exec > >(tee "${OUT}/transcript.txt") 2>&1
echo "==> evidence: ${OUT}"

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HARNESS_DIR}/../../../.." && pwd)"
APP_DIR="${PW_APP_DIR:-${REPO_ROOT}/dist/PolicyWitness.app}"
SERVICE_BUNDLE="${APP_DIR}/Contents/XPCServices/PWRunner.xpc"
SB_VALIDATOR="${SERVICE_BUNDLE}/Contents/MacOS/sb_api_validator"
PROBE_SRC="${HARNESS_DIR}/local_name_probe.c"
PROBE_BIN="${HARNESS_DIR}/local_name_probe"
BUNDLE="${HARNESS_DIR}/local_name_probe.app"
TARGET="com.policywitness.probe.local-target"
SIBLING="com.policywitness.probe.local-sibling"
SERVICE="com.policywitness.policy-witness.PWRunner"

[[ -x "${SB_VALIDATOR}" ]] || { echo "ERROR: sb_api_validator not found at ${SB_VALIDATOR}" >&2; exit 2; }
[[ -d "${SERVICE_BUNDLE}" ]] || { echo "ERROR: PWRunner.xpc not found at ${SERVICE_BUNDLE}" >&2; exit 2; }

echo "==> host: $(sw_vers -productVersion) ($(sw_vers -buildVersion)) $(uname -m)"
echo "==> app: ${APP_DIR}"
if [[ ! -x "${PROBE_BIN}" || "${PROBE_SRC}" -nt "${PROBE_BIN}" ]]; then
    echo "==> compiling local_name_probe"
    xcrun --sdk macosx clang -Wall -Wextra -Wno-deprecated-declarations -O1 -std=c11 -fobjc-arc \
        -o "${PROBE_BIN}" "${PROBE_SRC}"
fi

# A disposable bundle whose own domain holds a copy of the service. The copy
# may exit when launched outside its app. Its XPC errors do not prove receipt.
rm -rf "${BUNDLE}"
mkdir -p "${BUNDLE}/Contents/MacOS" "${BUNDLE}/Contents/XPCServices"
cp "${PROBE_BIN}" "${BUNDLE}/Contents/MacOS/local_name_probe"
cp -R "${SERVICE_BUNDLE}" "${BUNDLE}/Contents/XPCServices/"
cat > "${BUNDLE}/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>com.policywitness.probe.local-name</string>
<key>CFBundleExecutable</key><string>local_name_probe</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleName</key><string>local_name_probe</string>
<key>CFBundleShortVersionString</key><string>1.0</string>
<key>CFBundleVersion</key><string>1</string>
</dict></plist>
PLIST
BUNDLE_PROBE="${BUNDLE}/Contents/MacOS/local_name_probe"
git -C "${REPO_ROOT}" rev-parse HEAD > "${OUT}/commit.txt"
git -C "${REPO_ROOT}" diff HEAD --binary > "${OUT}/source.diff"
shasum -a 256 "${PROBE_SRC}" "$0" "${PROBE_BIN}" "${SB_VALIDATOR}" \
    "${SERVICE_BUNDLE}/Contents/MacOS/PWRunner" > "${OUT}/sha256.txt"

HELD_PID=""
cleanup() {
    if [[ -n "${HELD_PID}" ]] && kill -0 "${HELD_PID}" 2>/dev/null; then
        kill -KILL "${HELD_PID}" 2>/dev/null || true
        wait "${HELD_PID}" 2>/dev/null || true
    fi
    [[ "${KEEP}" == "1" ]] || rm -rf "${BUNDLE}"
}
trap cleanup EXIT

echo
echo "==> bootstrap subset availability"
"${PROBE_BIN}" subset | sed 's/^/    /'

policies_for() {
    local name="$1" sibling="$2"
    cat <<POLICIES
(version 1)(allow default)(deny mach-lookup (local-name "${name}"))
(version 1)(allow default)(deny mach-lookup (global-name "${name}"))
(version 1)(allow default)(deny mach-lookup)
(version 1)(deny default)(allow mach-lookup (local-name "${sibling}"))
(version 1)(deny default)(allow mach-lookup (global-name "${sibling}"))
POLICIES
}

for mode in registered registered-after; do
    echo
    echo "==> namespace: ${mode} (names this process registers)"
    while IFS= read -r policy; do
        echo "    policy: ${policy}"
        "${PROBE_BIN}" "${mode}" "${policy}" | grep -v '^pid=' | sed 's/^/        /'
    done < <(policies_for "${TARGET}" "${SIBLING}")
done

echo
echo "==> namespace: bundle (embedded XPC service ${SERVICE})"
while IFS= read -r policy; do
    echo "    policy: ${policy}"
    "${BUNDLE_PROBE}" bundle "${policy}" | grep -v '^pid=' | sed 's/^/        /'
done < <(policies_for "${SERVICE}" "com.policywitness.probe.local-other")

probe_id() {
    local pid="$1" type_id="$2" value="$3" out
    local raw="${OUT}/raw/${pid}-${type_id}-${value##*.}"
    set +e
    "${SB_VALIDATOR}" --json "${pid}" mach-lookup "RAW:${type_id}" "${value}" > "${raw}.stdout" 2> "${raw}.stderr"
    local code=$?
    set -e
    printf '%s\n' "${code}" > "${raw}.status"
    out="$(cat "${raw}.stdout")"
    [[ -n "${out}" ]] || { echo "no-output:${code}"; return; }
    "${PW_PYTHON}" -B -S -P -c '
import json, sys
try: d = json.loads(sys.stdin.read())
except Exception: print("parse-err"); sys.exit()
rc = d.get("rc", d.get("error")); errno = d.get("errno", "-")
print("allow" if rc == 0 else "deny" if rc == 1 and errno == 0 else f"err:rc={rc},errno={errno}")' <<< "${out}"
}

scan() {
    local pid="$1" denied="$2" sibling="$3"
    printf "    %-5s %-10s %-10s\n" id "${denied##*.}" "${sibling##*.}"
    local discriminating=()
    for type_id in $(seq 1 "${MAX_ID}"); do
        local d s
        d="$(probe_id "${pid}" "${type_id}" "${denied}")"
        s="$(probe_id "${pid}" "${type_id}" "${sibling}")"
        if [[ "${d}" != "allow" || "${s}" != "allow" ]]; then
            printf "    %-5s %-10s %-10s\n" "${type_id}" "${d}" "${s}"
        fi
        if [[ "${d}" == "deny" && "${s}" == "allow" ]]; then discriminating+=("${type_id}"); fi
        kill -0 "${pid}" 2>/dev/null || { echo "    probe died during the scan" >&2; break; }
    done
    echo "    IDs that deny ${denied} and allow ${sibling}: ${discriminating[*]:-none}"
}

echo
echo "==> sandbox_check scan under (allow default)(deny mach-lookup (local-name target)), registered names"
"${PROBE_BIN}" registered "(version 1)(allow default)(deny mach-lookup (local-name \"${TARGET}\"))" hold > "${HARNESS_DIR}/.local_name_hold" 2>&1 &
HELD_PID=$!
for _ in $(seq 1 200); do grep -q '^pid=' "${HARNESS_DIR}/.local_name_hold" 2>/dev/null && break; sleep 0.01; done
grep -v '^pid=' "${HARNESS_DIR}/.local_name_hold" | sed 's/^/    /'
scan "${HELD_PID}" "${TARGET}" "${SIBLING}"
kill -KILL "${HELD_PID}" 2>/dev/null || true; wait "${HELD_PID}" 2>/dev/null || true; HELD_PID=""

echo
echo "==> sandbox_check scan under (allow default)(deny mach-lookup (global-name target)), registered names (control)"
"${PROBE_BIN}" registered "(version 1)(allow default)(deny mach-lookup (global-name \"${TARGET}\"))" hold > "${HARNESS_DIR}/.local_name_hold" 2>&1 &
HELD_PID=$!
for _ in $(seq 1 200); do grep -q '^pid=' "${HARNESS_DIR}/.local_name_hold" 2>/dev/null && break; sleep 0.01; done
grep -v '^pid=' "${HARNESS_DIR}/.local_name_hold" | sed 's/^/    /'
scan "${HELD_PID}" "${TARGET}" "${SIBLING}"
kill -KILL "${HELD_PID}" 2>/dev/null || true; wait "${HELD_PID}" 2>/dev/null || true; HELD_PID=""
rm -f "${HARNESS_DIR}/.local_name_hold"

cat <<'NOTE'

==> reading the evidence
    A filter ID is a working local-name mapping only if the kernel denied the
    target under the local-name rule and the ID agrees for the target and the
    sibling. If no namespace above showed the local-name rule changing a
    lookup, no ID can agree with enforcement, whatever it answers: record
    prediction unavailability for (mach-lookup, local_name) in
    VERIFICATIONS.md with this output, naming the host and app.
NOTE

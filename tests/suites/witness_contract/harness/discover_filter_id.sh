#!/usr/bin/env bash
#
# discover_filter_id.sh — empirical discovery of libsandbox filter-type
# numeric IDs.
#
# Approach: apply a policy that uses one named filter kind on a
# discriminator value, then query the running process from outside with
# candidate filter IDs against:
#   value_A (mentioned in a deny rule) — should return deny if ID matches
#   value_B (not mentioned)             — should return allow if ID matches
#
# The (deny, allow) pattern identifies the correct numeric ID for the
# filter kind under test.
#
# Usage:
#   discover_filter_id.sh <filter-kind-sbpl-name> <operation>
#
# Example:
#   discover_filter_id.sh iokit-registry-entry-class iokit-open-service
#
# Output (one row per candidate ID):
#   id=<n> rc_A=<n>/<errno> rc_B=<n>/<errno> verdict=<correct|near|wrong>
#
# Followed by a summary line naming the discovered ID (if any).

set -euo pipefail

if [[ $# -ne 4 ]]; then
    echo "usage: $0 <filter-kind-sbpl-name> <operation> <value_A> <value_B>" >&2
    echo "  value_A: the value mentioned in a deny rule (must be a" >&2
    echo "           syntactically-valid argument for this filter kind)" >&2
    echo "  value_B: a sibling value of the same shape that the rule does" >&2
    echo "           NOT mention" >&2
    echo "  example: $0 iokit-registry-entry-class iokit-open-service \\" >&2
    echo "             AppleHIDMouse AppleHIDKeyboard" >&2
    echo "  example: $0 path file-read-data /tmp/pw-discover-a /tmp/pw-discover-b" >&2
    exit 2
fi

FILTER_KIND="$1"
OPERATION="$2"
VALUE_A="$3"
VALUE_B="$4"

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HARNESS_DIR}/../../../.." && pwd)"

TARGET_SRC="${HARNESS_DIR}/discovery_target.c"
TARGET_BIN="${HARNESS_DIR}/discovery_target"
SB_VALIDATOR="${REPO_ROOT}/dist/PolicyWitness.app/Contents/MacOS/sb_api_validator"

if [[ ! -x "${SB_VALIDATOR}" ]]; then
    echo "ERROR: sb_api_validator not found at ${SB_VALIDATOR}" >&2
    echo "  build the app bundle first: IDENTITY=... ./build.sh" >&2
    exit 2
fi

if [[ ! -f "${TARGET_SRC}" ]]; then
    echo "ERROR: discovery_target source missing at ${TARGET_SRC}" >&2
    exit 2
fi

if [[ ! -x "${TARGET_BIN}" || "${TARGET_SRC}" -nt "${TARGET_BIN}" ]]; then
    echo "==> rebuilding discovery_target"
    xcrun --sdk macosx clang -Wall -Wextra -O2 -std=c11 \
        -o "${TARGET_BIN}" "${TARGET_SRC}"
fi

# Build a default-allow policy with one deny rule using the filter
# kind under test on VALUE_A. We intentionally leave VALUE_B
# unmentioned so the correct filter ID yields different verdicts for
# the two values.
POLICY="(version 1)
(allow default)
(deny ${OPERATION} (${FILTER_KIND} \"${VALUE_A}\"))"

echo "==> applying discriminator policy:"
echo "${POLICY}" | sed 's/^/    /'
echo ""

# Spawn the target. It prints "ready_pid=<n>\n" after sandbox_apply.
"${TARGET_BIN}" "${POLICY}" > /tmp/pw-discovery-out 2>&1 &
TARGET_BG_PID=$!

# Cleanup on any exit path.
cleanup() {
    if kill -0 "${TARGET_BG_PID}" 2>/dev/null; then
        kill -KILL "${TARGET_BG_PID}" 2>/dev/null || true
        wait "${TARGET_BG_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Wait for the ready line (max ~2s).
TARGET_PID=""
for i in $(seq 1 200); do
    if grep -q "^ready_pid=" /tmp/pw-discovery-out 2>/dev/null; then
        TARGET_PID="$(awk -F= '/^ready_pid=/{print $2; exit}' /tmp/pw-discovery-out)"
        break
    fi
    sleep 0.01
done

if [[ -z "${TARGET_PID}" ]]; then
    echo "ERROR: discovery_target did not print ready_pid within 2s" >&2
    cat /tmp/pw-discovery-out >&2 || true
    exit 1
fi

echo "==> target pid: ${TARGET_PID}"
echo ""

# Query each candidate type ID. Sandbox_check returns:
#   rc=0  → allow
#   rc=1  → deny (either policy match or kernel rejected unknown filter
#                 with EINVAL or similar)
#   rc=-1 → error
# To distinguish "policy denied" from "kernel rejected filter," we look
# at errno: errno=0 with rc=1 means policy match; non-zero errno
# typically means the kernel didn't understand the filter.
#
# We scan IDs 0..63 — empirically all known filter IDs are well below
# this. Extend the range if no candidate emerges.

# Probe one (pid, op, type_id, value). Returns four fields on one line:
#   rc errno child_exit child_signal
# Where rc/errno are extracted from the JSON envelope when present;
# child_exit is the sb_api_validator exit code; child_signal is the
# signal number if the validator was killed (libsandbox can SEGV when
# the filter ID expects an argument shape different from what we pass).
# All errors are non-fatal — discovery must scan all IDs even if some
# crash the helper.
probe() {
    local pid="$1" op="$2" type_id="$3" value="$4"
    local out rc=0 sig=0
    set +e
    out="$("${SB_VALIDATOR}" --json "${pid}" "${op}" "RAW:${type_id}" "${value}" 2>/dev/null)"
    local code=$?
    set -e
    if [[ ${code} -gt 128 ]]; then
        sig=$((code - 128))
        rc="signal"
        echo "${rc} - - ${sig}"
        return
    fi
    if [[ -z "${out}" ]]; then
        echo "no-output - ${code} 0"
        return
    fi
    local rc_field errno_field
    rc_field="$(echo "${out}" | /usr/bin/python3 -c 'import json,sys
try: d=json.loads(sys.stdin.read())
except Exception: print("parse-err"); sys.exit()
print(d.get("rc", d.get("error","-")))')"
    errno_field="$(echo "${out}" | /usr/bin/python3 -c 'import json,sys
try: d=json.loads(sys.stdin.read())
except Exception: print("-"); sys.exit()
print(d.get("errno","-"))')"
    echo "${rc_field} ${errno_field} ${code} ${sig}"
}

found_id=""
echo "id    rc_A errno_A code_A sig_A    rc_B errno_B code_B sig_B    verdict"
for type_id in $(seq 1 63); do
    read -r rc_a errno_a code_a sig_a <<< "$(probe "${TARGET_PID}" "${OPERATION}" "${type_id}" "${VALUE_A}")"
    read -r rc_b errno_b code_b sig_b <<< "$(probe "${TARGET_PID}" "${OPERATION}" "${type_id}" "${VALUE_B}")"

    verdict="wrong"
    if [[ "${rc_a}" == "1" && "${rc_b}" == "0" && "${errno_a}" == "0" && "${errno_b}" == "0" ]]; then
        verdict="CORRECT"
        if [[ -z "${found_id}" ]]; then
            found_id="${type_id}"
        fi
    elif [[ "${sig_a}" != "0" || "${sig_b}" != "0" ]]; then
        verdict="validator-crashed"
    elif [[ "${rc_a}" == "${rc_b}" && "${errno_a}" == "0" && "${errno_b}" == "0" ]]; then
        verdict="filter-ignored"
    fi

    printf "%-5s %-4s %-7s %-6s %-7s  %-4s %-7s %-6s %-7s  %s\n" \
        "${type_id}" \
        "${rc_a}" "${errno_a}" "${code_a}" "${sig_a}" \
        "${rc_b}" "${errno_b}" "${code_b}" "${sig_b}" \
        "${verdict}"

    # Verify the target is still alive — sandbox_check on the target
    # pid is read-only and shouldn't kill it, but be defensive.
    if ! kill -0 "${TARGET_PID}" 2>/dev/null; then
        echo ""
        echo "ERROR: target pid ${TARGET_PID} died mid-scan; aborting after id=${type_id}" >&2
        break
    fi
done

echo ""
if [[ -n "${found_id}" ]]; then
    echo "==> DISCOVERED: ${FILTER_KIND} → filter_type_id=${found_id}"
    echo "    (rc_A=deny, rc_B=allow, both errno=0 — policy match pattern)"
    exit 0
else
    echo "==> NO CANDIDATE FOUND in range 0..63"
    echo "    Try extending the range, or verify the policy compiles cleanly."
    exit 1
fi

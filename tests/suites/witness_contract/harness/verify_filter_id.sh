#!/usr/bin/env bash
#
# verify_filter_id.sh — cross-check sandbox_check filter IDs against
# actual kernel enforcement.
#
# Where discover_filter_id.sh looks for IDs that produce a discriminator
# pattern in sandbox_check verdicts, this driver does the harder thing:
# it captures the kernel's actual enforcement for the named operation
# (via real syscalls in enforcement_probe), then asks "for each
# candidate filter ID, does sandbox_check agree with the kernel?"
#
# An ID is verified if and only if its sandbox_check verdict matches the
# kernel's actual verdict for the SAME (operation, value) pair. An ID
# that disagrees means either (a) the ID is wrong for this filter kind,
# or (b) sandbox_check has a known unreliability for this op+filter
# combination (the BBX-001 class of anomaly).
#
# Usage:
#   verify_filter_id.sh mach_lookup <sbpl-filter-name> <value>
#
# Example:
#   verify_filter_id.sh mach_lookup global-name com.apple.cfprefsd.xpc.daemon

set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "usage: $0 <probe> <sbpl-filter-name> <value>" >&2
    echo "  probe: mach_lookup" >&2
    echo "  example: $0 mach_lookup global-name com.apple.cfprefsd.xpc.daemon" >&2
    exit 2
fi

PROBE="$1"
SBPL_FILTER="$2"
VALUE="$3"

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HARNESS_DIR}/../../../.." && pwd)"

PROBE_SRC="${HARNESS_DIR}/enforcement_probe.c"
PROBE_BIN="${HARNESS_DIR}/enforcement_probe"
SB_VALIDATOR="${REPO_ROOT}/dist/PolicyWitness.app/Contents/MacOS/sb_api_validator"

if [[ ! -x "${SB_VALIDATOR}" ]]; then
    echo "ERROR: sb_api_validator not found at ${SB_VALIDATOR}" >&2
    exit 2
fi

if [[ ! -x "${PROBE_BIN}" || "${PROBE_SRC}" -nt "${PROBE_BIN}" ]]; then
    echo "==> rebuilding enforcement_probe"
    xcrun --sdk macosx clang -Wall -Wextra -O2 -std=c11 \
        -framework IOKit -framework CoreFoundation \
        -o "${PROBE_BIN}" "${PROBE_SRC}"
fi

# Map our probe name to the SBPL operation name.
case "${PROBE}" in
    mach_lookup) OPERATION="mach-lookup" ;;
    iokit_open)  OPERATION="iokit-open-service" ;;
    *) echo "ERROR: unknown probe: ${PROBE}" >&2; exit 2 ;;
esac

# A default-allow policy with one deny rule on the named filter.
POLICY="(version 1)
(allow default)
(deny ${OPERATION} (${SBPL_FILTER} \"${VALUE}\"))"

echo "==> policy:"
echo "${POLICY}" | sed 's/^/    /'
echo "==> value: ${VALUE}"
echo "==> probe: ${PROBE}"
echo ""

# Spawn the probe.
PROBE_OUT="$(mktemp)"
trap 'rm -f "${PROBE_OUT}"' EXIT
"${PROBE_BIN}" "${PROBE}" "${POLICY}" "${VALUE}" > "${PROBE_OUT}" 2>&1 &
PROBE_BG_PID=$!
cleanup() {
    if kill -0 "${PROBE_BG_PID}" 2>/dev/null; then
        kill -KILL "${PROBE_BG_PID}" 2>/dev/null || true
        wait "${PROBE_BG_PID}" 2>/dev/null || true
    fi
    rm -f "${PROBE_OUT}"
}
trap cleanup EXIT

# Wait for ready_pid line.
TARGET_PID=""
for i in $(seq 1 200); do
    if grep -q "^ready_pid=" "${PROBE_OUT}" 2>/dev/null; then
        TARGET_PID="$(awk -F= '/^ready_pid=/{print $2; exit}' "${PROBE_OUT}")"
        break
    fi
    sleep 0.01
done

if [[ -z "${TARGET_PID}" ]]; then
    echo "ERROR: probe did not signal ready within 2s" >&2
    cat "${PROBE_OUT}" >&2 || true
    exit 1
fi

# Capture the actual kernel verdict and (for probes that produce one)
# the pre-apply baseline.
ACTUAL_OUTCOME="$(awk -F= '/^attempt_outcome=/{print $2; exit}' "${PROBE_OUT}")"
ACTUAL_KR="$(awk -F= '/^attempt_kr=/{print $2; exit}' "${PROBE_OUT}")"
BASELINE_OUTCOME="$(awk -F= '/^baseline_outcome=/{print $2; exit}' "${PROBE_OUT}")"

echo "==> target pid: ${TARGET_PID}"
if [[ -n "${BASELINE_OUTCOME}" ]]; then
    echo "==> pre-apply baseline: ${BASELINE_OUTCOME}"
fi
echo "==> kernel's actual verdict: ${ACTUAL_OUTCOME} (kr=${ACTUAL_KR})"
echo ""

if [[ "${ACTUAL_OUTCOME}" == "missing" || "${BASELINE_OUTCOME}" == "missing" ]]; then
    echo "ERROR: probe target is not present on this host."
    echo "  Verification can't proceed without an observable enforcement target."
    echo "  Pick a different VALUE that exists on this Mac and rerun."
    exit 1
fi

if [[ -n "${BASELINE_OUTCOME}" && "${BASELINE_OUTCOME}" != "allow" ]]; then
    echo "WARNING: pre-apply baseline reported ${BASELINE_OUTCOME} (not allow)."
    echo "  The chosen probe value isn't openable even without a policy, so"
    echo "  the post-apply outcome doesn't isolate the policy's effect."
    echo "  Pick a different VALUE that is openable unsandboxed, then rerun."
    exit 1
fi

if [[ "${ACTUAL_OUTCOME}" != "deny" ]]; then
    echo "WARNING: kernel did not enforce the deny rule (allowed the operation)."
    echo "  This means either (a) the policy isn't matching the value as we"
    echo "  expect, or (b) we're querying a value the policy doesn't actually"
    echo "  cover. Filter-ID verification can't proceed without enforcement."
    exit 1
fi

# Probe candidate IDs and report which agree with the kernel.
probe() {
    local pid="$1" op="$2" type_id="$3" value="$4"
    set +e
    local out
    out="$("${SB_VALIDATOR}" --json "${pid}" "${op}" "RAW:${type_id}" "${value}" 2>/dev/null)"
    local code=$?
    set -e
    if [[ ${code} -gt 128 ]]; then
        echo "signal:$((code-128))"
        return
    fi
    if [[ -z "${out}" ]]; then
        echo "no-output:${code}"
        return
    fi
    /usr/bin/python3 -c '
import json, sys
try: d=json.loads(sys.stdin.read())
except Exception: print("parse-err"); sys.exit()
rc = d.get("rc", d.get("error"))
errno = d.get("errno", "-")
if rc == 0: print("allow")
elif rc == 1 and errno == 0: print("deny")
else: print(f"err:rc={rc},errno={errno}")
' <<< "${out}"
}

echo "id    sandbox_check_verdict    matches_kernel?"
agreeing=()
SCAN_MAX="${SCAN_MAX:-63}"
for type_id in $(seq 1 "${SCAN_MAX}"); do
    verdict="$(probe "${TARGET_PID}" "${OPERATION}" "${type_id}" "${VALUE}")"
    match="-"
    if [[ "${verdict}" == "${ACTUAL_OUTCOME}" ]]; then
        match="YES"
        agreeing+=("${type_id}")
    fi
    printf "%-5s %-24s %s\n" "${type_id}" "${verdict}" "${match}"

    if ! kill -0 "${TARGET_PID}" 2>/dev/null; then
        echo ""
        echo "ERROR: target died mid-scan; aborting after id=${type_id}" >&2
        break
    fi
done

echo ""
if [[ ${#agreeing[@]} -gt 0 ]]; then
    echo "==> IDs whose sandbox_check verdict matches kernel enforcement: ${agreeing[*]}"
    echo "    These are the candidates for the named filter '${SBPL_FILTER}'"
    echo "    on operation '${OPERATION}'. Multiple agreements mean the"
    echo "    discriminator pattern alone can't single out the unique ID;"
    echo "    use a second probe value to break the tie."
    exit 0
else
    echo "==> NO ID's sandbox_check verdict matches kernel enforcement."
    echo "    sandbox_check is unreliable for this op+filter combination."
    echo "    Validator-primary verdicts via cross-check cannot be trusted"
    echo "    for this filter kind."
    exit 1
fi

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
# An ID is a candidate match if its sandbox_check verdict matches the
# kernel's actual verdict for the policy's (operation, filter_value) and
# the probe target it acted on. An ID that disagrees means either
# (a) the ID is wrong for this filter kind, or (b) sandbox_check has a
# known unreliability for this op+filter combination (the BBX-001 class
# of anomaly). Single-side "match" is necessary but not sufficient: a
# fully verified ID also requires a sibling allow case (see PR C; this
# script reports candidate matches and the operator is responsible for
# the cross-check).
#
# Usage:
#   verify_filter_id.sh <probe> <sbpl-filter-name> <value> [--probe-target <STRING>]
#
# The policy is authored with <value> as the filter argument; the
# enforcement_probe attempts <value> by default. For filter kinds where
# the policy filter value and the kernel object being attempted are
# semantically distinct strings (e.g. iokit_user_client_class — the
# policy filters by user-client class name like IOSurfaceRootUserClient
# while the probe opens an IOService registry class like IOSurfaceRoot),
# pass --probe-target <STRING> to decouple them.
#
# Examples:
#   verify_filter_id.sh mach_lookup global-name com.apple.cfprefsd.xpc.daemon
#   verify_filter_id.sh iokit_open iokit-user-client-class \
#       IOSurfaceRootUserClient --probe-target IOSurfaceRoot

set -euo pipefail

usage() {
    cat <<'EOF' >&2
usage: verify_filter_id.sh <probe> <sbpl-filter-name> <value> [options]
  probe: mach_lookup | iokit_open | iokit_open_user_client | sysctl_read | preferences_read
  --probe-target STRING: override the probe target (default: <value>)
  --allowed-value STRING: sibling filter value the policy does NOT
      deny; enables strict mode. A filter ID is reported as confirmed
      when its sandbox_check verdict is deny for the policy's <value>
      AND allow for the sibling. The deny side matches the kernel's
      actual verdict (the probe exercised the syscall); the allow
      side is sandbox_check's own answer for the un-denied sibling,
      NOT a kernel-observed operation. Used to exclude incidental
      deniers (e.g. ID 1 = PATH returns deny for any string), not as
      a proof of kernel agreement on the allowed value.
  --max-id INT: highest filter ID to scan (default 200; overridable via
      SCAN_MAX env var for backwards compatibility).
  examples:
    verify_filter_id.sh mach_lookup global-name com.apple.cfprefsd.xpc.daemon \
        --allowed-value com.apple.unknown.fake.service
    verify_filter_id.sh iokit_open_user_client iokit-user-client-class \
        IOSurfaceRootUserClient --probe-target IOSurfaceRoot \
        --allowed-value SomeOtherUserClient
EOF
}

if [[ $# -lt 3 ]]; then
    usage
    exit 2
fi

PROBE="$1"
SBPL_FILTER="$2"
VALUE="$3"
shift 3

PROBE_TARGET="${VALUE}"
ALLOWED_VALUE=""
SCAN_MAX_OVERRIDE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --probe-target)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --probe-target requires a value" >&2
                exit 2
            fi
            PROBE_TARGET="$2"
            shift 2
            ;;
        --allowed-value)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --allowed-value requires a value" >&2
                exit 2
            fi
            ALLOWED_VALUE="$2"
            shift 2
            ;;
        --max-id)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --max-id requires a value" >&2
                exit 2
            fi
            SCAN_MAX_OVERRIDE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            usage
            exit 2
            ;;
    esac
done

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

# Map our probe name to the SBPL operation name. iokit_open and
# iokit_open_user_client both trigger IOServiceOpen — the same syscall —
# but the kernel observes them as two distinct operations
# (iokit-open-service for the IOService class match and
# iokit-open-user-client for the resulting user-client class). The probe
# kind selects which SBPL operation the policy and sandbox_check
# question are framed against, so an iokit-user-client-class filter is
# correctly paired with iokit_open_user_client, not iokit_open.
case "${PROBE}" in
    mach_lookup)            OPERATION="mach-lookup" ;;
    iokit_open)             OPERATION="iokit-open-service" ;;
    iokit_open_user_client) OPERATION="iokit-open-user-client" ;;
    sysctl_read)            OPERATION="sysctl-read" ;;
    preferences_read)       OPERATION="user-preference-read" ;;
    *) echo "ERROR: unknown probe: ${PROBE}" >&2; exit 2 ;;
esac

# Both iokit probe kinds use the same C probe code path.
case "${PROBE}" in
    iokit_open_user_client) PROBE_BIN_ARG="iokit_open" ;;
    *)                      PROBE_BIN_ARG="${PROBE}" ;;
esac

# A default-allow policy with one deny rule on the named filter.
POLICY="(version 1)
(allow default)
(deny ${OPERATION} (${SBPL_FILTER} \"${VALUE}\"))"

echo "==> policy:"
echo "${POLICY}" | sed 's/^/    /'
echo "==> policy filter value: ${VALUE}"
echo "==> probe target:        ${PROBE_TARGET}"
echo "==> probe:               ${PROBE}"
echo ""

# Spawn the probe.
PROBE_OUT="$(mktemp)"
trap 'rm -f "${PROBE_OUT}"' EXIT
"${PROBE_BIN}" "${PROBE_BIN_ARG}" "${POLICY}" "${PROBE_TARGET}" > "${PROBE_OUT}" 2>&1 &
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

# SCAN_MAX precedence (highest first): --max-id flag, SCAN_MAX env var
# (legacy), built-in default 200.
if [[ -n "${SCAN_MAX_OVERRIDE}" ]]; then
    SCAN_MAX="${SCAN_MAX_OVERRIDE}"
else
    SCAN_MAX="${SCAN_MAX:-200}"
fi

echo "==> scanning filter IDs 1..${SCAN_MAX}"
if [[ -n "${ALLOWED_VALUE}" ]]; then
    echo "==> strict mode: require sandbox_check verdict to match kernel"
    echo "    for BOTH denied value (${VALUE}) and allowed sibling (${ALLOWED_VALUE})"
    printf "id    deny-side             allow-side            both_match?\n"
else
    echo "==> permissive mode: no --allowed-value supplied; matches may"
    echo "    include incidental deniers (e.g. ID 1 / PATH returns deny"
    echo "    for any string)"
    printf "id    sandbox_check_verdict    matches_kernel?\n"
fi

agreeing=()
for type_id in $(seq 1 "${SCAN_MAX}"); do
    deny_verdict="$(probe "${TARGET_PID}" "${OPERATION}" "${type_id}" "${VALUE}")"
    if [[ -n "${ALLOWED_VALUE}" ]]; then
        allow_verdict="$(probe "${TARGET_PID}" "${OPERATION}" "${type_id}" "${ALLOWED_VALUE}")"
        match="-"
        if [[ "${deny_verdict}" == "deny" && "${allow_verdict}" == "allow" ]]; then
            match="YES"
            agreeing+=("${type_id}")
        fi
        printf "%-5s %-21s %-21s %s\n" "${type_id}" "${deny_verdict}" "${allow_verdict}" "${match}"
    else
        match="-"
        if [[ "${deny_verdict}" == "${ACTUAL_OUTCOME}" ]]; then
            match="YES"
            agreeing+=("${type_id}")
        fi
        printf "%-5s %-24s %s\n" "${type_id}" "${deny_verdict}" "${match}"
    fi

    if ! kill -0 "${TARGET_PID}" 2>/dev/null; then
        echo ""
        echo "ERROR: target died mid-scan; aborting after id=${type_id}" >&2
        break
    fi
done

echo ""
if [[ ${#agreeing[@]} -gt 0 ]]; then
    if [[ -n "${ALLOWED_VALUE}" ]]; then
        echo "==> filter IDs passing strict mode (kernel-observed deny on '${VALUE}',"
        echo "    sandbox_check allow on '${ALLOWED_VALUE}'): ${agreeing[*]}"
        echo "    These IDs correctly interpret filter_value as a string-match"
        echo "    against the policy's filter values. Incidental deniers that"
        echo "    return deny for any string are excluded by the allow-side check."
        echo "    The allow-side evidence is sandbox_check's own answer for the"
        echo "    sibling — it is not a kernel observation. To raise confidence"
        echo "    further, exercise the syscall against the allowed sibling out"
        echo "    of band and confirm the kernel allows it."
    else
        echo "==> candidate filter IDs (deny-side only): ${agreeing[*]}"
        echo "    These match the kernel deny but the set may include incidental"
        echo "    deniers (e.g. ID 1 = PATH returns deny for any string). Rerun"
        echo "    with --allowed-value <sibling-string> to disambiguate."
    fi
    exit 0
else
    echo "==> NO ID's sandbox_check verdict matches kernel enforcement."
    if [[ -n "${ALLOWED_VALUE}" ]]; then
        echo "    Across 1..${SCAN_MAX}, no ID produced (deny on '${VALUE}',"
        echo "    allow on '${ALLOWED_VALUE}'). sandbox_check is unreliable for"
        echo "    this op+filter combination — emit prediction_unavailable."
    else
        echo "    sandbox_check is unreliable for this op+filter combination."
        echo "    (Permissive mode — even incidental deniers didn't match,"
        echo "    so the userland predicate is fully off for this op+filter.)"
    fi
    exit 1
fi

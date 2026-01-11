#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "xpc.q1_dlopen_external"

fail() {
  test_fail "${CURRENT_STEP:-q1 dlopen_external failed}"
}

trap fail ERR

step() {
  CURRENT_STEP="$1"
  test_step "$1" "${2:-$1}"
}

PW="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
OUT_DIR="${PW_TEST_ARTIFACTS}"

if [[ ! -x "${PW}" ]]; then
  test_fail "missing or non-executable PolicyWitness launcher at: ${PW}"
fi

mkdir -p "${OUT_DIR}"

CLANG_MODE=""
if command -v clang >/dev/null 2>&1; then
  CLANG_MODE="clang"
elif command -v xcrun >/dev/null 2>&1; then
  CLANG_MODE="xcrun"
else
  test_skip "clang/xcrun not available (install Xcode Command Line Tools)"
  exit 0
fi

step "create_dylib_paths" "create dylib paths (base + injectable)"
BASE_UUID="$(/usr/bin/python3 - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
)"
INJ_UUID="$(/usr/bin/python3 - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
)"

BASE_DYLIB="pw_lvtest_${BASE_UUID}.dylib"
INJ_DYLIB="pw_lvtest_${INJ_UUID}.dylib"
BASE_MARKER="pw_lvtest_${BASE_UUID}_ran.txt"
INJ_MARKER="pw_lvtest_${INJ_UUID}_ran.txt"

BASE_CREATE_JSON="${OUT_DIR}/dlopen-base-create.json"
INJ_CREATE_JSON="${OUT_DIR}/dlopen-inj-create.json"

"${PW}" xpc run --profile minimal fs_op --op create --path-class tmp --target specimen_file --name "${BASE_DYLIB}" --no-cleanup >"${BASE_CREATE_JSON}"
"${PW}" xpc run --profile minimal --variant injectable fs_op --op create --path-class tmp --target specimen_file --name "${INJ_DYLIB}" --no-cleanup >"${INJ_CREATE_JSON}"

BASE_PATH="$(/usr/bin/plutil -extract data.details.file_path raw -o - "${BASE_CREATE_JSON}")"
INJ_PATH="$(/usr/bin/plutil -extract data.details.file_path raw -o - "${INJ_CREATE_JSON}")"

if [[ -z "${BASE_PATH}" || -z "${INJ_PATH}" ]]; then
  test_fail "failed to resolve dylib paths from fs_op output"
fi

BASE_MARKER_PATH="$(dirname "${BASE_PATH}")/${BASE_MARKER}"
INJ_MARKER_PATH="$(dirname "${INJ_PATH}")/${INJ_MARKER}"

cat >"${OUT_DIR}/dlopen_base.c" <<'EOF_BASE'
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

__attribute__((constructor))
static void pw_init(void) {
  int fd = open("__MARKER_PATH__", O_WRONLY|O_CREAT|O_TRUNC, 0644);
  if (fd >= 0) {
    dprintf(fd, "pw_lvtest constructor pid=%d\n", getpid());
    close(fd);
  }
  fprintf(stderr, "pw_lvtest constructor pid=%d\n", getpid());
}
EOF_BASE

cat >"${OUT_DIR}/dlopen_inj.c" <<'EOF_INJ'
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

__attribute__((constructor))
static void pw_init(void) {
  int fd = open("__MARKER_PATH__", O_WRONLY|O_CREAT|O_TRUNC, 0644);
  if (fd >= 0) {
    dprintf(fd, "pw_lvtest constructor pid=%d\n", getpid());
    close(fd);
  }
  fprintf(stderr, "pw_lvtest constructor pid=%d\n", getpid());
}
EOF_INJ

/usr/bin/sed -i '' "s#__MARKER_PATH__#${BASE_MARKER_PATH}#g" "${OUT_DIR}/dlopen_base.c"
/usr/bin/sed -i '' "s#__MARKER_PATH__#${INJ_MARKER_PATH}#g" "${OUT_DIR}/dlopen_inj.c"

step "compile_dylibs" "compile unsigned dylibs"
set +e
if [[ "${CLANG_MODE}" == "clang" ]]; then
  clang -dynamiclib -o "${BASE_PATH}" "${OUT_DIR}/dlopen_base.c" >"${OUT_DIR}/dlopen-base-compile.stdout.txt" 2>"${OUT_DIR}/dlopen-base-compile.stderr.txt"
  BASE_RC=$?
  clang -dynamiclib -o "${INJ_PATH}" "${OUT_DIR}/dlopen_inj.c" >"${OUT_DIR}/dlopen-inj-compile.stdout.txt" 2>"${OUT_DIR}/dlopen-inj-compile.stderr.txt"
  INJ_RC=$?
else
  xcrun clang -dynamiclib -o "${BASE_PATH}" "${OUT_DIR}/dlopen_base.c" >"${OUT_DIR}/dlopen-base-compile.stdout.txt" 2>"${OUT_DIR}/dlopen-base-compile.stderr.txt"
  BASE_RC=$?
  xcrun clang -dynamiclib -o "${INJ_PATH}" "${OUT_DIR}/dlopen_inj.c" >"${OUT_DIR}/dlopen-inj-compile.stdout.txt" 2>"${OUT_DIR}/dlopen-inj-compile.stderr.txt"
  INJ_RC=$?
fi
set -e

if [[ ${BASE_RC} -ne 0 || ${INJ_RC} -ne 0 ]]; then
  test_fail "failed to compile dylib(s); see ${OUT_DIR}/dlopen-*-compile.stderr.txt"
fi

step "dlopen_base" "dlopen_external (base)"
rm -f "${BASE_MARKER_PATH}"
if "${PW}" xpc run --capture-sandbox-logs --profile minimal dlopen_external --path "${BASE_PATH}" >"${OUT_DIR}/dlopen-base.json"; then
  BASE_DLOPEN_RC=0
else
  BASE_DLOPEN_RC=$?
fi
printf '%s\n' "${BASE_DLOPEN_RC}" >"${OUT_DIR}/dlopen-base.exit.txt"
if [[ -f "${BASE_MARKER_PATH}" ]]; then
  printf 'present\n' >"${OUT_DIR}/marker-base.txt"
  cat "${BASE_MARKER_PATH}" >>"${OUT_DIR}/marker-base.txt"
else
  printf 'absent\n' >"${OUT_DIR}/marker-base.txt"
fi

step "dlopen_injectable" "dlopen_external (injectable)"
rm -f "${INJ_MARKER_PATH}"
if "${PW}" xpc run --capture-sandbox-logs --profile minimal --variant injectable dlopen_external --path "${INJ_PATH}" >"${OUT_DIR}/dlopen-inj.json"; then
  INJ_DLOPEN_RC=0
else
  INJ_DLOPEN_RC=$?
fi
printf '%s\n' "${INJ_DLOPEN_RC}" >"${OUT_DIR}/dlopen-inj.exit.txt"
if [[ -f "${INJ_MARKER_PATH}" ]]; then
  printf 'present\n' >"${OUT_DIR}/marker-inj.txt"
  cat "${INJ_MARKER_PATH}" >>"${OUT_DIR}/marker-inj.txt"
else
  printf 'absent\n' >"${OUT_DIR}/marker-inj.txt"
fi

cat >"${OUT_DIR}/paths.txt" <<EOF
BASE_PATH=${BASE_PATH}
BASE_MARKER=${BASE_MARKER_PATH}
INJ_PATH=${INJ_PATH}
INJ_MARKER=${INJ_MARKER_PATH}
EOF

step "validate" "validate dlopen outcomes and evidence"
PY_STATUS=0
/usr/bin/python3 - "${OUT_DIR}/dlopen-base.json" "${OUT_DIR}/dlopen-inj.json" "${OUT_DIR}/marker-base.txt" "${OUT_DIR}/marker-inj.txt" "${OUT_DIR}/summary.json" <<'PY' || PY_STATUS=$?
import json
import sys
from pathlib import Path

base_path, inj_path, marker_base_path, marker_inj_path, summary_path = sys.argv[1:]

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))

def marker_state(path):
    if not Path(path).exists():
        return "absent"
    text = Path(path).read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if not text:
        return "absent"
    return text[0].strip()

def capture_info(obj):
    data = obj.get("data") or {}
    details = data.get("details") or {}
    cap = data.get("host_sandbox_log_capture") or {}
    obs = cap.get("observer_report", {}).get("data", {})
    return {
        "ok": obj.get("result", {}).get("ok"),
        "normalized_outcome": obj.get("result", {}).get("normalized_outcome"),
        "error": obj.get("result", {}).get("error"),
        "has_disable_library_validation": details.get("has_disable_library_validation"),
        "has_allow_dyld_env": details.get("has_allow_dyld_env"),
        "capture_status": cap.get("capture_status"),
        "observed_deny": obs.get("observed_deny"),
    }

def write_summary(status, reason, base_info, inj_info, marker_base, marker_inj):
    summary = {
        "status": status,
        "reason": reason,
        "base": base_info,
        "injectable": inj_info,
        "marker_base": marker_base,
        "marker_inj": marker_inj,
    }
    Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))

base = load_json(base_path)
inj = load_json(inj_path)
base_info = capture_info(base)
inj_info = capture_info(inj)
marker_base = marker_state(marker_base_path)
marker_inj = marker_state(marker_inj_path)

if base_info.get("capture_status") != "captured" or inj_info.get("capture_status") != "captured":
    write_summary("skip", "capture_status not captured", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(2)

if base_info.get("observed_deny") is True:
    write_summary("skip", "base run observed sandbox denies; not a pure library validation gate", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(2)

if base_info.get("normalized_outcome") == "ok" or marker_base == "present":
    write_summary("skip", "base dlopen succeeded (host does not enforce library validation gate)", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(2)

if base_info.get("normalized_outcome") != "dlopen_failed":
    write_summary("fail", "base did not report dlopen_failed", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(1)

if base_info.get("has_disable_library_validation") not in ("false", False):
    write_summary("fail", "base has_disable_library_validation not false", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(1)

if inj_info.get("normalized_outcome") != "ok":
    write_summary("fail", "injectable dlopen_external did not succeed", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(1)

if inj_info.get("has_disable_library_validation") not in ("true", True):
    write_summary("fail", "injectable has_disable_library_validation not true", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(1)

if marker_inj != "present":
    write_summary("fail", "injectable did not run constructor (marker missing)", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(1)

if inj_info.get("observed_deny") is True:
    write_summary("fail", "injectable run observed sandbox denies", base_info, inj_info, marker_base, marker_inj)
    raise SystemExit(1)

write_summary("pass", "ok", base_info, inj_info, marker_base, marker_inj)
PY

if [[ ${PY_STATUS} -eq 2 ]]; then
  test_skip "q1 dlopen_external inconclusive (see artifacts)"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q1 dlopen_external validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q1 dlopen_external ok" "{}"

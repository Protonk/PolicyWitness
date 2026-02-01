#!/usr/bin/env bash
# Opt-in test for the instrumentation dylib_load port.
#
# Purpose:
# - Build a tiny dylib, load it via instrumentation, and verify the symbol runs.
#
# Opt-in reason:
# - Requires a compiler toolchain and dynamic loading under hardened runtime.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-runner_debuggable}"
PW_TEST_ID="runner_instrumentation_dylib"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "preflight" "check toolchain and fixtures"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
render_specimen_with_runner "${SPECIMEN_FIXTURE}" "${SPECIMEN_PATH}"

CLANG_PATH="$(require_clang)" || exit 0
SDKROOT="$(require_macos_sdk)" || exit 0

test_step "build_dylib" "compile dylib for dylib_load port"

SRC_PATH="${PW_TEST_ARTIFACTS}/instrumentation.c"
DYLIB_PATH="${PW_TEST_ARTIFACTS}/libpw_instrumentation.dylib"
MARKER_PATH="${PW_TEST_ARTIFACTS}/dylib_marker.txt"
BUILD_LOG="${PW_TEST_ARTIFACTS}/clang_build.log"

/usr/bin/python3 - "${SRC_PATH}" "${MARKER_PATH}" <<'PY'
import json
import sys

src_path, marker_path = sys.argv[1:3]
path_literal = json.dumps(marker_path)
code = f"""#include <fcntl.h>
#include <unistd.h>
#include <string.h>

__attribute__((visibility("default"))) void pw_instrumentation_init(void) {{
    const char *path = {path_literal};
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd >= 0) {{
        const char *msg = "ok";
        (void)write(fd, msg, 2);
        close(fd);
    }}
}}
"""
with open(src_path, "w", encoding="utf-8") as fh:
    fh.write(code)
PY

set +e
"${CLANG_PATH}" -isysroot "${SDKROOT}" -dynamiclib -o "${DYLIB_PATH}" "${SRC_PATH}" >"${BUILD_LOG}" 2>&1
CLANG_RC=$?
set -e
if [[ ${CLANG_RC} -ne 0 ]]; then
  test_fail "clang failed to build dylib" "{\"log_path\":\"${BUILD_LOG}\"}"
fi

test_step "run" "run specimen with dylib_load instrumentation"

INSTRUMENTATION_JSON="${PW_TEST_ARTIFACTS}/instrumentation.json"
/usr/bin/python3 - "${INSTRUMENTATION_JSON}" "${DYLIB_PATH}" <<'PY'
import json
import sys

path = sys.argv[2]
payload = {
    "version": 1,
    "ports": [
        {"kind": "dylib_load", "path": path, "symbol": "pw_instrumentation_init"}
    ],
}
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=2, sort_keys=True)
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" --instrumentation "${INSTRUMENTATION_JSON}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not True:
    raise SystemExit(f"expected result.ok=true (got {env.get('result', {}).get('ok')!r})")

runner = env.get("data", {}).get("runner_result") or {}
inst = runner.get("instrumentation") or {}
ports = inst.get("ports") or []
if len(ports) != 1:
    raise SystemExit(f"expected 1 instrumentation port (got {len(ports)})")
port = ports[0]
if port.get("kind") != "dylib_load":
    raise SystemExit(f"expected kind=dylib_load (got {port.get('kind')!r})")
if port.get("status") != "ok":
    raise SystemExit(f"expected status=ok (got {port.get('status')!r})")
dylib = port.get("dylib") or {}
if dylib.get("symbol_found") is not True:
    raise SystemExit(f"expected symbol_found=true (got {dylib.get('symbol_found')!r})")
PY

KIND_ERR="$(assert_runner_kind "${RUN_STDOUT}")" || test_fail "${KIND_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"

if [[ ! -f "${MARKER_PATH}" ]]; then
  test_fail "dylib marker was not created" "{\"marker_path\":\"${MARKER_PATH}\"}"
fi

test_pass "dylib_load instrumentation ok" "{}"

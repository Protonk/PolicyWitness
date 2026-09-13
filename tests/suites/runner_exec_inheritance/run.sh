#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
WORKER="${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin runner_exec_inheritance cli
[[ -x "${PW_BIN}" && -x "${WORKER}" ]] || test_fail "built app/worker missing"
# Keep the helper path below the worker argv[0] bound for the direct ABI adapter.
HELPER="${PW_TEST_OUT_DIR}/inheritance/helper"
HARNESS="${PW_TEST_OUT_DIR}/inheritance/worker-harness"
test_step build "compile shared observer and existing worker harness"
if ! bash "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}" \
    >"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/build.log" >&2
  test_fail "inspection fixture build failed"
fi
if ! /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -O2 -std=c11 \
    -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
    "${ROOT_DIR}/tests/suites/runner_c_worker_harness/harness.c" -o "${HARNESS}" \
    >>"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/build.log" >&2
  test_fail "worker harness build failed"
fi
test_step run "inspect environment, descriptors, and stdin in three ordinary CLI exec steps"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_exec_inheritance/check.py" \
    cli "${PW_TEST_ARTIFACTS}" "${PW_BIN}" "${HELPER}" \
    >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "CLI exec inheritance contract failed"
fi
test_pass "three CLI exec children report a complete, clean process state"

test_begin runner_exec_inheritance contaminated_worker
test_step run "verify worker launch contamination, then observe its exec children"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_exec_inheritance/check.py" \
    worker "${PW_TEST_ARTIFACTS}" "${WORKER}" "${HELPER}" "${HARNESS}" \
    >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "worker exec inheritance contract failed"
fi
test_pass "worker received canary environment and descriptor; its exec children inherited neither"

#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
WORKER="${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner"
source "${ROOT_DIR}/tests/lib/case.sh"

inheritance_setup() {
[[ -x "${PW_BIN}" && -x "${WORKER}" ]] || test_fail "built app/worker missing"
# Keep the helper path below the worker argv[0] bound for the direct ABI adapter.
HELPER="${PW_TEST_OUT_DIR}/inheritance/helper"
HARNESS="${PW_TEST_OUT_DIR}/inheritance/worker-harness"
test_step build "compile shared observer and existing worker harness"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}"
test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_harness/build.sh" "${HARNESS}" \
  "${PW_TEST_ARTIFACTS}/harness-build.log"
}

if test_selected cli; then
test_begin runner_exec_inheritance cli
inheritance_setup
test_step run "inspect environment, descriptors, and stdin in three ordinary CLI exec steps"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_exec_inheritance/check.py" \
    cli "${PW_TEST_ARTIFACTS}" "${PW_BIN}" "${HELPER}" \
    >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "CLI exec inheritance contract failed"
fi
test_pass "three CLI exec children report a complete, clean process state"

fi

if test_selected contaminated_worker; then
test_begin runner_exec_inheritance contaminated_worker
inheritance_setup
test_step run "verify worker launch contamination, then observe its exec children"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_exec_inheritance/check.py" \
    worker "${PW_TEST_ARTIFACTS}" "${WORKER}" "${HELPER}" "${HARNESS}" \
    >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "worker exec inheritance contract failed"
fi
test_pass "worker received canary environment and descriptor; its exec children inherited neither"

fi

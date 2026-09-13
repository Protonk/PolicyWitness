#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin runner_exec_lifecycle timeout_preserves_output_and_continues
[[ -x "${PW_BIN}" ]] || test_fail "built policy-witness missing: ${PW_BIN}"
HELPER="${PW_TEST_ARTIFACTS}/helper"
test_step build "compile shared exec fixture"
if ! bash "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}" \
    >"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/build.log" >&2
  test_fail "exec fixture build failed"
fi
test_step run "observe both processes exit at the public deadline; retain output and execute the next write"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_exec_lifecycle/check.py" \
    "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${HELPER}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "exec lifecycle contract failed; see artifacts/assert.log"
fi
test_pass "timed-out process group stopped; output survived and the next write completed"

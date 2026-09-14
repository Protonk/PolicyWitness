#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin runner_exec_lifecycle timeout_preserves_output_and_continues
test_require_pw
HELPER="${PW_TEST_ARTIFACTS}/helper"
test_step build "compile shared exec fixture"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}"
test_step run "observe both processes exit at the public deadline; retain output and execute the next write"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" \
  "exec lifecycle contract failed" \
  "${ROOT_DIR}/tests/suites/runner_exec_lifecycle/check.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${HELPER}"
test_pass "timed-out process group stopped; output survived and the next write completed"

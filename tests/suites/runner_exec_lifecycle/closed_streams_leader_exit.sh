#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_exec_lifecycle closed_streams_leader_exit
test_require_pw
HELPER="${PW_TEST_ARTIFACTS}/helper"
test_step build "compile the existing independently controlled exec fixture"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}"
test_step run "characterize a same-group survivor after stream closure and leader exit"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "same-group descendant characterization failed" \
  "${ROOT_DIR}/tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${HELPER}"
test_pass "current lifetime limit characterized; surviving descendant independently released and observed exiting"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin runner_exec_dac execute_permission_is_not_sandbox_drift
test_require_pw
test_step run "compare direct execution and PW with execute permission absent, then restored"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "exec permission attribution failed" \
  "${ROOT_DIR}/tests/suites/runner_exec_dac/check.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${PW_TEST_ARTIFACTS}/exec-helper"
test_step native_scope "observe native exec queries under independent exec, fork and file-read policies"
test_check_python "${PW_TEST_ARTIFACTS}/scope.log" "native exec scope control failed" \
  "${ROOT_DIR}/tests/suites/runner_exec_dac/check_query_scope.py" "${PW_BIN}" \
  "${PW_TEST_ARTIFACTS}/scope" "${PW_TEST_ARTIFACTS}/exec-helper"
test_pass "execute permission controls spawning; ordinary EACCES yields drift=null"

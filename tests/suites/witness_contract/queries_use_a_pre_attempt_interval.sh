#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract queries_use_a_pre_attempt_interval
test_require_pw
test_step run "observe effects independently before checking ordered evidence"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "ordering witness failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_ordering.py" \
  queries_use_a_pre_attempt_interval "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "ordered evidence and independent observations verified"

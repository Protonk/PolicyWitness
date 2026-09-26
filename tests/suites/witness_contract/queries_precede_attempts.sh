#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin witness_contract queries_precede_attempts
test_require_pw
test_step run "observe target removal before decoding; both native predictions precede read/unlink and retain limited agreement"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "removed-target evidence contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_removed_target.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "ordered read/unlink retain native allow predictions and limited agreement alongside independent absence"

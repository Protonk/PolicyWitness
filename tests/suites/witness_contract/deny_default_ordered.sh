#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract deny_default_ordered
test_require_pw
test_step run "observe effects independently before checking ordered evidence"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "ordering witness failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_ordering.py" \
  deny_default_ordered "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "ordered evidence and independent observations verified"

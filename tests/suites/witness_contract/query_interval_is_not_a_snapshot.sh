#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract query_interval_is_not_a_snapshot
test_require_pw
test_build_fixture "${ROOT_DIR}/tests/fixtures/validator/build_bridge.sh" "${PW_TEST_ARTIFACTS}/bridge-bin" "${PW_TEST_ARTIFACTS}/bridge-build.log"
test_step run "observe effects independently before checking ordered evidence"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "ordering witness failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_ordering.py" \
  query_interval_is_not_a_snapshot "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/bridge-bin"
test_pass "ordered evidence and independent observations verified"

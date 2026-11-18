#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract test_input
test_require_pw
test_step passages "publish a bound read, observe thirteen controlled passages and submit it with test-input run"
test_check_python "${PW_TEST_ARTIFACTS}/check.log" "test-input correspondence failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/test_input.py" "${PW_TEST_ARTIFACTS}/capture" \
  "${PW_BIN}" "${PW_APP_DIR}" "${ROOT_DIR}/docs/contract/public.json"
test_pass "read publication, fixture transitions, refusal, repair, independent query/attempt expectations and test-input run observations hold" "{}"

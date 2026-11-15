#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract test_input
test_require_pw
test_step passages "publish a bound read and observe twelve controlled passages"
test_check_python "${PW_TEST_ARTIFACTS}/check.log" "test-input correspondence failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/test_input.py" "${PW_TEST_ARTIFACTS}/capture" \
  "${PW_BIN}" "${PW_APP_DIR}" "${ROOT_DIR}/docs/contract/public.json"
test_pass "read publication, fixture transitions, refusal, repair and independent query/attempt expectations hold" "{}"

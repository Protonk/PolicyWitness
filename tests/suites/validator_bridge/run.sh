#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin validator_bridge protocol_controls
test_step build "build independent native validator bridge and exec observer"
test_build_fixture "${ROOT_DIR}/tests/fixtures/validator/build_bridge.sh" "${PW_TEST_ARTIFACTS}/bridge"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${PW_TEST_ARTIFACTS}/helper" "${PW_TEST_ARTIFACTS}/helper-build.log"
test_step run "verify real native results and acknowledged query/emission/closure gates"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "validator bridge controls failed" \
  "${ROOT_DIR}/tests/suites/validator_bridge/check.py" "${PW_TEST_ARTIFACTS}/bridge" "${PW_TEST_ARTIFACTS}/helper" "${PW_TEST_ARTIFACTS}"
test_pass "native records and gate behavior independently verified"

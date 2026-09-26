#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_validator_failure validator_killed_mid_stream
test_require_pw
test_step run "real signal after one verdict; observe writes before decoding"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "signaled validator contract failed" \
  "${ROOT_DIR}/tests/suites/runner_validator_failure/check_signal.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "signal, partial verdict, ordered release and independent effects retained"

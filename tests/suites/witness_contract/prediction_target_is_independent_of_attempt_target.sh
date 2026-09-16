#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin witness_contract prediction_target_is_independent_of_attempt_target
test_require_pw
test_step run "swap prediction targets while preserving policy, attempts, and independent file effects"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "prediction/attempt target independence failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_prediction_targets.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "swapping prediction targets reverses verdicts while actual writes stay fixed"

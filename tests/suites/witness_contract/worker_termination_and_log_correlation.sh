#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_termination_and_log_correlation
test_require_pw
test_step run "ordinary denied writes precede self-signal; optional logs retain correlation without a cause claim"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "termination/log contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_termination_correlation.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "process disposition, denied writes, capture availability and candidate associations remain independent" "{}"

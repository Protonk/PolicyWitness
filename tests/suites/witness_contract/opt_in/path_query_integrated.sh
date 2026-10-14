#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract path_query_integrated
test_require_pw
test_step run "independently query planner-excluded paths against the actual PW worker"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "integrated path-query observations failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_path_queries_integrated.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "PW eligibility and independent native queries retained separately"

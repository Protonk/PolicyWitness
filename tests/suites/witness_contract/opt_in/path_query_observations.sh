#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract path_query_observations
test_require_pw
test_step run "observe direct path queries, native operations and independent path state"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "path-query observation controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_path_queries.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "native path-query observations retained with independent state and cleanup"

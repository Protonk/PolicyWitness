#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin dispatcher controls
test_step reconcile "compare real dispatcher exits and summaries against controlled suite evidence"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "dispatcher controls failed" \
  "${ROOT_DIR}/tests/suites/dispatcher/check.py" "${PW_TEST_ARTIFACTS}"
test_pass "requested suite exits, case reports, and lifecycle evidence determine one result"

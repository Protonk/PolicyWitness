#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

if test_selected controls; then
test_begin dispatcher controls
test_step reconcile "compare real dispatcher exits and summaries against controlled suite evidence"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "dispatcher controls failed" \
  "${ROOT_DIR}/tests/suites/dispatcher/check.py" "${PW_TEST_ARTIFACTS}"
test_pass "requested suite exits, case reports, and lifecycle evidence determine one result"
fi

if test_selected selection_controls; then
test_begin dispatcher selection_controls
test_step command "observe selected work, configuration, and preserved evidence through the public command"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "test command controls failed" \
  "${ROOT_DIR}/tests/suites/dispatcher/check_selection.py" "${PW_TEST_ARTIFACTS}"
test_pass "public selection, inspection, configuration, and completion match execution receipts"
fi

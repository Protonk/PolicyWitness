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

if test_selected accounting_controls; then
test_begin dispatcher accounting_controls
test_step accounting "check complete selection accounting independently of reconciliation"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "accounting controls failed" \
  "${ROOT_DIR}/tests/suites/dispatcher/check_accounting.py" "${PW_TEST_ARTIFACTS}"
test_pass "accounting preserves every selection and refuses incomplete or ambiguous results"
fi

if test_selected cancellation_controls; then
test_begin dispatcher cancellation_controls
test_step cancellation "observe interruption, process exits, preserved evidence, and queued work"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "cancellation controls failed" \
  "${ROOT_DIR}/tests/suites/dispatcher/check_cancellation.py" "${PW_TEST_ARTIFACTS}"
test_pass "ordinary case cancellation stops descendants and retains complete run accounting"
fi

if test_selected selection_controls; then
test_begin dispatcher selection_controls
test_step command "observe selected work, configuration, and preserved evidence through the public command"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "test command controls failed" \
  "${ROOT_DIR}/tests/suites/dispatcher/check_selection.py" "${PW_TEST_ARTIFACTS}"
test_pass "public selection, inspection, configuration, and completion match execution receipts"
fi

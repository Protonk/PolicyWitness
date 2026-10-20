#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit build_receipt_controls
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "build receipt controls failed" \
  "${ROOT_DIR}/tests/suites/runner_unit/build_receipt_controls.py" \
  "${PW_TEST_ARTIFACTS}/controls" "${PW_TEST_SCRATCH}/layouts"
test_pass "build receipts require products in case scratch outside retained output"

#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract test_input_controls
test_step controls "pin coherent external-correspondence faults and real preparation boundary"
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "test-input controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/test_input_controls.py" "${PW_TEST_ARTIFACTS}"
test_pass "independent accepted and rejected controls match exact diagnostics" "{}"

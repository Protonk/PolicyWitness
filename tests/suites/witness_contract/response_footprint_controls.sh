#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract response_footprint_controls
test_step check "independent source ownership and binary transport rejection controls"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "response footprint controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/response_footprint_controls.py" "${PW_TEST_ARTIFACTS}/controls.json"
test_pass "valid constructed receipts accepted and mutations rejected" "{}"

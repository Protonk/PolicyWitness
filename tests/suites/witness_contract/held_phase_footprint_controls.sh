#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract held_phase_footprint_controls
test_step run "accept complete constructed receipts and reject independent corrupted fields"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "held footprint checker controls failed" \
 "${ROOT_DIR}/tests/suites/witness_contract/held_phase_footprint_controls.py" "${PW_TEST_ARTIFACTS}"
test_pass "Waiting checker corruption sensitivity verified at constructed scope"

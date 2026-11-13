#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract example_round_trip_controls
test_step controls "hand the example checker constructed captures that violate each assertion"
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "example round-trip controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/example_round_trip_controls.py" "${PW_TEST_ARTIFACTS}"
test_pass "every checker assertion has a rejected control whose diagnostics match its expected identifiers and classifications" "{}"

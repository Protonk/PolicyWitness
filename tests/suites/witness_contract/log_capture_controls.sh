#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract log_capture_controls
test_step controls "require collection and cleanup facts for completed queries and budget cutoffs; reject unsupported excuses"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "log capture acceptance controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/log_capture_controls.py" "${PW_TEST_ARTIFACTS}/controls"
test_pass "live acceptance distinguishes complete, empty, budget-limited and unexpected outcomes" "{}"

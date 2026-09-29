#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract deny_capture_covers_the_run
test_require_pw
test_step run "denied reads around two held exec children; require padded bounds and supported collection facts; records are optional"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "deny capture window contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_deny_capture_window.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "padded scan contract and native attempts verified; returned records and missing-record diagnostics agree" "{}"

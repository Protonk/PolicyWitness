#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract deny_capture_covers_the_run
test_require_pw
test_step run "denied reads around two held exec children; require padded client bounds and a record of the final denial"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "deny capture window contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_deny_capture_window.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "capture window equals the padded runner client span; the final denial is recorded and associated; unrecorded failures are named" "{}"

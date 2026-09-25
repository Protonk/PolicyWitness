#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin run_effects file_actions_have_exact_effects
test_require_pw
test_step run "run each file action under allow and denied policies; snapshot targets before and after"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "file action effect contract failed" \
  "${ROOT_DIR}/tests/suites/run_effects/check_file_actions.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "open_write truncates in place to one byte, create makes an empty 0600 file or leaves an existing one untouched, unlink removes, reads change nothing, denied twins leave targets identical"

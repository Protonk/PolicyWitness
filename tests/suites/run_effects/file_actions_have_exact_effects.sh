#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin run_effects file_actions_have_exact_effects
test_require_pw
test_step run "compare regular-file snapshots and sample the FIFO after open_read"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "file action effect contract failed" \
  "${ROOT_DIR}/tests/suites/run_effects/check_file_actions.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "regular-file actions have their expected effects, denied twins preserve their targets, and open_read consumes exactly one queued FIFO byte"

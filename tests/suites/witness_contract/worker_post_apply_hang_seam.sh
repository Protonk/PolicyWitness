#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin witness_contract worker_post_apply_hang_seam
test_require_pw
test_step run "completed allowed and denied writes retain their evidence after the host kills the hung worker"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "mixed-outcome worker timeout contract failed" \
  "${ROOT_DIR}/tests/suites/runner_outcome_runner_timeout/check.py" \
  mixed "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "host timeout preserves allowed and denied write evidence, file effects, and limited comparison evidence"

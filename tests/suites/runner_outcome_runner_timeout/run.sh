#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin runner_outcome_runner_timeout host_kills_hung_worker
test_require_pw
# An empty plan deliberately exercises the deadline without a validator child.
test_step run "host timeout with an empty plan preserves explicit empty steps and no validator"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "empty-plan worker timeout contract failed" \
  "${ROOT_DIR}/tests/suites/runner_outcome_runner_timeout/check.py" \
  empty "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "host SIGKILL timeout with explicit empty steps, no validator, and both overrides honored"

#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_c_worker_harness arm_wait_controls
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "ARM screen controls failed" \
  "${ROOT_DIR}/tests/suites/runner_c_worker_harness/check_arm_wait.py" --controls "${PW_TEST_ARTIFACTS}"
test_pass "independent ARM screen evidence faults refused"

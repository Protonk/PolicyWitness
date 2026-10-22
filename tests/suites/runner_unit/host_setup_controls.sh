#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit host_setup_controls
test_step controls "observe native setup faults and actual descriptor collisions in disposable host sources"
test_run_logged "${PW_TEST_ARTIFACTS}/controls.log" "host setup controls failed" \
  "${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/suites/runner_unit/host_setup_controls.py" "${PW_TEST_ARTIFACTS}/controls" "${PW_TEST_SCRATCH}/build"
test_pass "host setup observations and rejected checker controls passed"

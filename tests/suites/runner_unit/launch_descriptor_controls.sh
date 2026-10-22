#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit launch_descriptor_controls
test_step controls "observe evidence-object exclusion, exact-number reuse and setup cleanup in disposable host sources"
test_run_logged "${PW_TEST_ARTIFACTS}/controls.log" "launch descriptor controls failed" \
  "${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/suites/runner_unit/launch_descriptor_controls.py" "${PW_TEST_ARTIFACTS}/controls" "${PW_TEST_SCRATCH}/build"
test_pass "launch descriptor ownership and rejected source/checker controls passed"

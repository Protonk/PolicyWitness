#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit service_admission_controls
test_step controls "restore per-connection admission and refusal exit separately in a disposable source copy"
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "service regression controls failed" \
  "${ROOT_DIR}/tests/suites/runner_unit/service_admission_controls.py" "${PW_TEST_ARTIFACTS}/controls"
test_pass "fixed services pass; per-connection admission and refusal exit each restore the expected failure"

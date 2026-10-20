#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit sleep_record_controls
test_step controls "run TestKit against substituted sleep-counting and uptime clock readings in a disposable package"
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "sleep record controls failed" \
  "${ROOT_DIR}/tests/suites/runner_unit/sleep_record_controls.py" "${PW_TEST_ARTIFACTS}/controls"
test_pass "cases that slept carry a separate sleep line and failures are counted without changing any outcome"

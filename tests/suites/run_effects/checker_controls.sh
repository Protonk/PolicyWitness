#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin run_effects checker_controls
test_step controls "feed each effect expectation fabricated right and wrong observations"
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "effect expectation controls failed" \
  "${ROOT_DIR}/tests/suites/run_effects/controls.py" "${PW_TEST_ARTIFACTS}"
test_pass "each effect expectation accepts the right observation and rejects the wrong ones"

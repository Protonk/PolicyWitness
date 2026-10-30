#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit client_session_controls
test_step controls "compile the production client session with controlled clocks and XPC callbacks"
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "client session controls failed" \
  "${ROOT_DIR}/tests/suites/runner_unit/client_session_controls.py" \
  "${PW_TEST_ARTIFACTS}/controls" "${PW_TEST_SCRATCH}/client"
test_pass "client acquisition, deadline and no-replay boundaries observed through production session logic"

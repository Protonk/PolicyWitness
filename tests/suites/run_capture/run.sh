#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin run_capture controls
test_step capture "verify raw artifacts, exit and timeout attribution, overlap, and cleanup"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" \
  "capture controls failed" \
  "${ROOT_DIR}/tests/suites/run_capture/check.py" \
  "${PW_TEST_ARTIFACTS}"
test_pass "capture preserves raw evidence and distinguishes CLI results from harness intervention"

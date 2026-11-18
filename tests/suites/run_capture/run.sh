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
test_step seam "verify the seam invocation adapter's record, refusals and command form against a stand-in"
test_check_python "${PW_TEST_ARTIFACTS}/seam-assertions.log" \
  "seam invocation controls failed" \
  "${ROOT_DIR}/tests/suites/run_capture/check_seam_invocation.py" \
  "${PW_TEST_ARTIFACTS}/seam"
test_pass "capture preserves raw evidence and distinguishes CLI results from harness intervention"

#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin run_capture controls
test_step capture "verify raw artifacts, exit and timeout attribution, overlap, and cleanup"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/run_capture/check.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "capture controls failed; see artifacts/assertions.log"
fi
test_pass "capture preserves raw evidence and distinguishes CLI results from harness intervention"

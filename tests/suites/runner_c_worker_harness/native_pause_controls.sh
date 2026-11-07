#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_c_worker_harness native_pause_controls
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "native pause checker controls failed" \
  "${ROOT_DIR}/tests/suites/runner_c_worker_harness/check_native_pause.py" --controls
test_pass "unavailable supplemental logs do not hide required evidence failures"

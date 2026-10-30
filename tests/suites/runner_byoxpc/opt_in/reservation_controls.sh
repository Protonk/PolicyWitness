#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_byoxpc reservation_controls
test_require_pw
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "$IDENTITY" ]] || test_fail "reservation controls require the app's Developer ID Application identity"
test_step reservation "observe reservation ownership, controlled reply loss, compatibility, and no replay"
test_check_python "${PW_TEST_ARTIFACTS}/reservation-controls.log" "reservation controls failed; inspect retained trace and cleanup ownership" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/reservation_controls.py" \
  "$PW_BIN" "$PW_APP_DIR" "$PW_TEST_ARTIFACTS" "$PW_TEST_SCRATCH" "$IDENTITY"
test_pass "reservation controls retained independent effects, transport observations and verified owned cleanup"

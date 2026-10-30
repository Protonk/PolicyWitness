#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_byoxpc retirement_controls
test_require_pw
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "$IDENTITY" ]] || test_fail "retirement controls require a matching Developer ID Application identity"
test_step investigate "trace ordinary requests and distinguish delivered refusal, lost refusal, and lost execution reply"
test_check_python "${PW_TEST_ARTIFACTS}/investigation.log" "retirement investigation failed; inspect retained observations and cleanup ownership" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/retirement_controls.py" \
  "$PW_BIN" "$PW_APP_DIR" "$PW_TEST_ARTIFACTS" "$PW_TEST_SCRATCH" "$IDENTITY"
test_pass "controlled boundaries and independent effects observed; bounded ordinary sequence and verified cleanup recorded"

#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_outcome_bad_request same_shape_contract
test_require_pw
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "$IDENTITY" ]] || test_fail "same-shape controls require the app's Developer ID Application identity"
test_step builds "build signed truncate and append controls with independent client and worker launch traces"
test_check_python "${PW_TEST_ARTIFACTS}/same-shape.log" "same-shape contract controls failed; inspect retained worktree ownership" \
  "${ROOT_DIR}/tests/suites/runner_outcome_bad_request/opt_in/same_shape_contract.py" \
  "${PW_TEST_ARTIFACTS}" "$IDENTITY"
test_pass "different same-shape builds refuse foreign intent before launch; current assertions establish truncate and append effects"

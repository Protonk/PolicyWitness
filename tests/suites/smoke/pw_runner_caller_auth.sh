#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin "${PW_TEST_SUITE_OVERRIDE:-smoke}" runner_caller_auth
test_require_pw
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${IDENTITY}" ]] || test_fail "caller-auth controls require a matching Developer ID identity"
test_step authorization "compare restricted and relaxed authorization using identical client bytes"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "caller-auth contract failed" \
  "${ROOT_DIR}/tests/suites/smoke/check_caller_auth.py" \
  "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${IDENTITY}"
test_pass "caller authorization enforced; routing, signing, file effects, and rejection controls verified"

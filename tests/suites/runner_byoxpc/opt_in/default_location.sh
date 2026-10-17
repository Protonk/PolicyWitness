#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_byoxpc default_location
test_require_pw
unset PW_RUNNER_REGISTRY
SESSION_TOOL="${ROOT_DIR}/tests/fixtures/byoxpc/session.py"
cleanup() {
  local status=$?
  trap - EXIT
  /usr/bin/python3 "${SESSION_TOOL}" cleanup "${PW_BIN}" "${PW_TEST_ARTIFACTS}/session.json" || status=1
  exit "$status"
}
trap cleanup EXIT
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "$IDENTITY" ]] || test_fail "matching Developer ID required"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "owned BYOXPC setup failed" \
  "$SESSION_TOOL" install-default "$PW_BIN" "$PW_APP_DIR" "$PW_TEST_ARTIFACTS" "${PW_TEST_ARTIFACTS}/runner_env.json" "$IDENTITY"
test_step default_location "observe the default registry and plist, then run one specimen without an override"
test_check_python "${PW_TEST_ARTIFACTS}/default-location.log" "default-location control failed" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/default_location.py" "$PW_BIN" "$PW_TEST_ARTIFACTS"
test_check_python "${PW_TEST_ARTIFACTS}/cleanup.log" "BYOXPC cleanup failed" \
  "$SESSION_TOOL" cleanup "$PW_BIN" "${PW_TEST_ARTIFACTS}/session.json"
trap - EXIT
test_pass "default registry and plist locations exercised; specimen effect and removal verified"
